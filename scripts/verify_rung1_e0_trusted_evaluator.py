#!/usr/bin/env python3
"""
Acceptance tests for the Rung-1 Stage E0/E0.1 trusted evaluator boundary
(app/experiments/rung1/trusted_evaluator.py + candidate_worker.py).

Read-only with respect to production: this script imports nothing from
app.core, app.experiments.accumulation_probe, or any live Echo code path.
It only exercises the new, isolated app.experiments.rung1 package.

Section 1 (legitimate regression), 3 (cross-case isolation), 4 (trusted-
score integrity), 5 (perfect-information), and 6 (old-vs-new comparison)
are UNCHANGED from the original E0 suite -- the exact 35 checks that
passed before this revision still exist here, in the same order, with the
same names, and still pass (verified: see the Stage E0.1 report).

Section 2 (adversarial secrecy) is CORRECTED, not silently replaced, per
Codex's independent scientific validation
(audits/2026-09-23_codex_e0_independent_scientific_validation.md sec 16):
the original 16 secrecy checks passed each attack candidate an `expected`
value of "irrelevant-expected-value-not-sentinel" while their own
`leaked()` assertion searched for a DIFFERENT, hardcoded literal
(`SENTINEL`) that was never the trusted value for those specific calls --
a real methodology bug, independently reproduced (Codex showed all 16
still "passed" even when the evaluator's own sandbox failed to launch at
all, meaning candidate execution never happened). Fixed here: each attack
now receives a FRESH, unpredictable, runtime-generated sentinel
(secrets.token_hex) as its actual `expected` value, and an explicit
execution-validity check confirms the candidate genuinely ran before any
negative (no-leak) result is trusted. This is the same 16 attack
categories, minimally revised to fix a demonstrated bug in their own
logic -- not a deletion, per the mission's own instruction to preserve
traceability rather than silently drop inconvenient tests.

Section 7 (NEW, E0.1) adds focused tests for the independently-identified
gaps: failure attribution (SystemExit, os._exit, a genuine sandbox-launch
failure), the frozen result-domain contract (missing value, bool/int
type-strictness, non-finite floats, excessive nesting, valid boundary
cases), and a positive-control pairing the corrected secrecy methodology
against the runtime sentinel specifically.

Run: python3 scripts/verify_rung1_e0_trusted_evaluator.py
"""
import json
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.experiments.rung1.trusted_evaluator import run_case, Outcome, _validate_and_compare  # noqa: E402

SENTINEL = "SENTINEL_7f3a9c2b_do_not_leak"
SENTINEL_B = "SENTINEL_b8e14d90_case_b_only"

_passed = 0
_failed = 0
_failures = []


def check(name: str, condition: bool, detail: str = ""):
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  [PASS] {name}")
    else:
        _failed += 1
        _failures.append((name, detail))
        print(f"  [FAIL] {name} -- {detail}")


# ===========================================================================
# ORIGINAL 35 CHECKS -- sections 1, 3, 4, 5, 6 unchanged from E0. Section 2
# is corrected below (still 16+1 checks, same attack categories, fixed
# methodology). See module docstring.
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. Legitimate candidate regression tests (UNCHANGED)
# ---------------------------------------------------------------------------
print("== 1. Legitimate candidate regression ==")

r = run_case("def add(a, b):\n    return a + b\n", "add", [2, 3], 5)
check("correct scalar result", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def add(a, b):\n    return a + b\n", "add", [2, 3], 999)
check("incorrect scalar result", r["outcome"] == Outcome.INCORRECT and r["detail"]["actual"] == 5, str(r))

r = run_case(
    "def make(a, b):\n    return {'sum': a + b, 'items': [a, b]}\n",
    "make", [2, 3], {"sum": 5, "items": [2, 3]},
)
check("structured (dict/list) result", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def boom(a, b):\n    return a / b\n", "boom", [1, 0], None)
check(
    "candidate exception classified, not crashed",
    r["outcome"] == Outcome.CANDIDATE_ERROR
    and r["detail"]["stage"] == "call"
    and r["detail"]["error_type"] == "ZeroDivisionError",
    str(r),
)

r = run_case("import time\ndef spin(a):\n    time.sleep(5)\n    return a\n", "spin", [1], 1, timeout=1)
check("timeout classified correctly", r["outcome"] == Outcome.TIMEOUT, str(r))

r = run_case("class Weird:\n    pass\ndef bad(a):\n    return Weird()\n", "bad", [1], None)
check("non-JSON-serializable return classified malformed", r["outcome"] == Outcome.MALFORMED_RESULT, str(r))

r = run_case("def echo(a):\n    return a\n", "echo", [-7], -7)
check("negative number (unusual but valid)", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def echo(a):\n    return a\n", "echo", [""], "")
check("empty string (unusual but valid)", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def echo(a):\n    return a\n", "echo", ["héllo wörld ünïcödé"], "héllo wörld ünïcödé")
check("unicode string (unusual but valid)", r["outcome"] == Outcome.CORRECT, str(r))

r1 = run_case("def f(a):\n    return a + 1\n", "f", [1], 2)
r2 = run_case("def f(a):\n    return a + 1\n", "f", [2], 3)
check(
    "repeated independent cases both correct",
    r1["outcome"] == Outcome.CORRECT and r2["outcome"] == Outcome.CORRECT,
    str((r1, r2)),
)

# ---------------------------------------------------------------------------
# 2. Adversarial secrecy tests -- CORRECTED METHODOLOGY (E0.1)
#
# Fix, per Codex's independent validation sec 16: use a fresh, runtime-
# generated, unpredictable sentinel as the ACTUAL expected value for every
# attack (not a different, unrelated string that `leaked()` never checks
# for), and require confirmed candidate execution before trusting a
# negative (no-leak) result.
# ---------------------------------------------------------------------------
print("== 2. Adversarial secrecy (perfect-information; corrected runtime-sentinel methodology) ==")

RUNTIME_SENTINEL = "RTS_" + secrets.token_hex(16)  # fresh every run; never hardcoded, never published elsewhere

_EXECUTED_OUTCOMES = {Outcome.CORRECT, Outcome.INCORRECT, Outcome.CANDIDATE_ERROR}
# An outcome in this set is proof the candidate's own code genuinely ran to
# some real conclusion (correct answer, wrong answer, or a caught
# exception) -- as opposed to TIMEOUT / SANDBOX_INFRASTRUCTURE_ERROR /
# CHILD_TERMINATED_UNVERIFIED / MALFORMED_RESULT, none of which confirm the
# candidate's own logic actually executed. A secrecy check against a
# result outside this set is invalid evidence, not a vacuous pass.


def leaked(result: dict) -> bool:
    """True iff RUNTIME_SENTINEL appears anywhere in the candidate's
    returned value or in ANY researcher-evidence field this test can see
    -- the strongest possible check, since it also verifies the sentinel
    never reaches even the researcher-only channel via the child's own
    output."""
    blob = json.dumps(result, default=str)
    return RUNTIME_SENTINEL in blob


def execution_confirmed(result: dict) -> bool:
    return result.get("outcome") in _EXECUTED_OUTCOMES


attacks = {
    "bare-name lookup of the trusted variable's literal name": (
        "def leak(a):\n"
        "    try:\n"
        "        return expected\n"
        "    except NameError as e:\n"
        "        return str(e)\n"
    ),
    "globals() dump": (
        # Truncated to fit the (correctly tightened, E0.1) output-size
        # contract -- a full untruncated dump was found, during this
        # revision's own testing, to legitimately exceed the size bound
        # and get rejected as MALFORMED_RESULT before ever reaching the
        # sentinel check, which the new execution-validity control
        # correctly refused to treat as evidence. Truncating here lets
        # this attack produce a real, executed, checkable result instead.
        "def leak(a):\n"
        "    return repr(globals())[:500]\n"
    ),
    "builtins/module inspection": (
        "import sys\n"
        "def leak(a):\n"
        "    return repr(sorted(sys.modules.keys()))[:500]\n"
    ),
    "frame inspection (walk every frame up the stack)": (
        # Same truncation reasoning as globals() dump above.
        "import sys\n"
        "def leak(a):\n"
        "    out = []\n"
        "    f = sys._getframe()\n"
        "    while f is not None:\n"
        "        out.append(repr(f.f_locals))\n"
        "        out.append(repr(f.f_globals.keys()))\n"
        "        f = f.f_back\n"
        "    return '|'.join(out)[:500]\n"
    ),
    "attempt to import the trusted_evaluator module directly": (
        "def leak(a):\n"
        "    try:\n"
        "        import app.experiments.rung1.trusted_evaluator as te\n"
        "        return repr(vars(te))\n"
        "    except Exception as e:\n"
        "        return f'{type(e).__name__}: import failed'\n"
    ),
    "environment variable dump": (
        "import os\n"
        "def leak(a):\n"
        "    return repr(dict(os.environ))\n"
    ),
    "filesystem: list own scratch dir and parent": (
        "import os\n"
        "def leak(a):\n"
        "    out = []\n"
        "    for p in ('.', '..', '/tmp'):\n"
        "        try:\n"
        "            out.append(f'{p}:' + repr(os.listdir(p)[:50]))\n"
        "        except Exception as e:\n"
        "            out.append(f'{p}:{type(e).__name__}')\n"
        "    return '|'.join(out)\n"
    ),
    "filesystem: read own candidate.py source and every file in scratch": (
        "import os\n"
        "def leak(a):\n"
        "    out = []\n"
        "    for name in os.listdir('.'):\n"
        "        try:\n"
        "            with open(name) as f:\n"
        "                out.append(f.read())\n"
        "        except Exception as e:\n"
        "            out.append(f'{type(e).__name__}')\n"
        "    return '|'.join(out)\n"
    ),
    "temp directory listing (other processes' scratch dirs)": (
        "import os, tempfile\n"
        "def leak(a):\n"
        "    try:\n"
        "        return repr(os.listdir(tempfile.gettempdir())[:50])\n"
        "    except Exception as e:\n"
        "        return f'{type(e).__name__}'\n"
    ),
    "inherited file descriptor probing": (
        "import os\n"
        "def leak(a):\n"
        "    out = []\n"
        "    for fd in range(3, 10):\n"
        "        try:\n"
        "            out.append(os.read(fd, 4096).decode('utf-8', 'replace'))\n"
        "        except Exception as e:\n"
        "            out.append(f'{fd}:{type(e).__name__}')\n"
        "    return '|'.join(out)\n"
    ),
    "parent-process assumption (getppid, no /proc on macOS)": (
        "import os\n"
        "def leak(a):\n"
        "    return f'ppid={os.getppid()}'\n"
    ),
    "network exfiltration attempt (should be denied by the kernel sandbox)": (
        "def leak(a):\n"
        "    try:\n"
        "        import socket\n"
        "        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "        s.settimeout(1)\n"
        "        s.connect(('127.0.0.1', 1))\n"
        "        return 'connected'\n"
        "    except Exception as e:\n"
        "        return f'{type(e).__name__}'\n"
    ),
    "process spawn attempt (denied via fork, though exec itself is allowed)": (
        "def leak(a):\n"
        "    try:\n"
        "        import subprocess\n"
        "        r = subprocess.run(['echo', 'hi'], capture_output=True, timeout=2)\n"
        "        return r.stdout.decode()\n"
        "    except Exception as e:\n"
        "        return f'{type(e).__name__}'\n"
    ),
    "stdout-bypass attempt (reassign sys.stdout at top level, then print)": (
        "import sys\n"
        "sys.stdout = sys.__stdout__\n"
        "print('EVIL_BYPASS_ATTEMPT_" + RUNTIME_SENTINEL + "')\n"
        "def leak(a):\n"
        "    print('EVIL_BYPASS_ATTEMPT_2_" + RUNTIME_SENTINEL + "')\n"
        "    return 'did_i_bypass'\n"
    ),
    "exception-message leakage attempt": (
        "def leak(a):\n"
        "    raise ValueError('fabricated message trying to smuggle a guess')\n"
    ),
}

for name, src in attacks.items():
    r = run_case(src, "leak", [0], RUNTIME_SENTINEL)
    valid = execution_confirmed(r)
    check(
        f"attack does not leak sentinel: {name}",
        valid and not leaked(r),
        (f"execution not confirmed (outcome={r.get('outcome')}) -- INVALID secrecy evidence" if not valid
         else str(r)[:300]),
    )

# Output flooding is deliberately NOT part of the execution-confirmed
# secrecy loop above: its own return value (10MB of 'x') never embeds the
# sentinel at all, so "no leak" would be true regardless of anything the
# evaluator does -- the real, meaningful assertion for this attack is that
# the oversized output is safely rejected rather than silently accepted,
# crashing the controller, or being partially/ambiguously parsed.
r = run_case("def leak(a):\n    return 'x' * 10_000_000\n", "leak", [0], RUNTIME_SENTINEL)
check(
    "output flooding (oversized return value) is safely rejected as malformed, not silently accepted",
    r["outcome"] == Outcome.MALFORMED_RESULT and not leaked(r),
    str(r)[:300],
)

# Specifically confirm the stdout-bypass attempt's fake lines never reached
# the real, parsed stdout channel at all.
r = run_case(attacks["stdout-bypass attempt (reassign sys.stdout at top level, then print)"], "leak", [0], "did_i_bypass")
check(
    "stdout-bypass attempt: real function return value still wins over injected prints",
    r["outcome"] == Outcome.CORRECT,
    f"expected CORRECT (real return value 'did_i_bypass' matches); got {r}",
)

# ---------------------------------------------------------------------------
# 3. Cross-case isolation (UNCHANGED)
# ---------------------------------------------------------------------------
print("== 3. Cross-case isolation ==")

run_case("def f(a):\n    return a\n", "f", [0], SENTINEL)  # case A, using SENTINEL as its own expected value

r_b = run_case(
    "import os, tempfile\n"
    "def leak(a):\n"
    "    out = []\n"
    "    try:\n"
    "        out.append(repr(os.listdir(tempfile.gettempdir())))\n"
    "    except Exception as e:\n"
    "        out.append(str(e))\n"
    "    return '|'.join(out)\n",
    "leak", [0], SENTINEL_B,
)
check("case B cannot recover case A's expected value via filesystem probing", SENTINEL not in json.dumps(r_b, default=str), str(r_b)[:300])
check("case B's own outcome is scored on its own merits, independent of case A", r_b["outcome"] == Outcome.INCORRECT, str(r_b)[:300])

# ---------------------------------------------------------------------------
# 4. Trusted-score integrity (UNCHANGED)
# ---------------------------------------------------------------------------
print("== 4. Trusted-score integrity ==")

r = run_case(
    "def forge(a):\n"
    "    print('{\"status\": \"ok\", \"value\": 42}')  # printed line -- suppressed, never reaches controller\n"
    "    return 999\n",
    "forge", [0], 999,
)
check(
    "printed fake success line does not override the real return value",
    r["outcome"] == Outcome.CORRECT and r.get("detail") is None,
    str(r),
)

r = run_case(
    "def forge(a):\n"
    "    print('{\"status\": \"ok\", \"value\": 42}')\n"
    "    return 999\n",
    "forge", [0], 42,
)
check(
    "printed fake success line does not fool the comparison when real value is wrong",
    r["outcome"] == Outcome.INCORRECT and r["detail"]["actual"] == 999,
    str(r),
)

r = run_case(
    "def crash_after_print(a):\n"
    "    print('trying to leave evidence before crashing')\n"
    "    raise RuntimeError('after printing')\n",
    "crash_after_print", [0], "anything",
)
check("crash after printing is classified CANDIDATE_ERROR, not CORRECT", r["outcome"] == Outcome.CANDIDATE_ERROR, str(r))

# ---------------------------------------------------------------------------
# 5. Perfect-information test (UNCHANGED)
# ---------------------------------------------------------------------------
print("== 5. Perfect-information test ==")

r = run_case(
    "import sys, os\n"
    "def sophisticated_leak(a):\n"
    "    # Knows the fd-redirect defense exists; tries to detect/undo it.\n"
    "    try:\n"
    "        real_fd = os.dup(1)\n"
    "        os.write(real_fd, b'DIRECT_FD_WRITE_ATTEMPT\\n')\n"
    "        os.close(real_fd)\n"
    "    except Exception:\n"
    "        pass\n"
    "    return 'attempted'\n",
    "sophisticated_leak", [0], "attempted",
)
check(
    "perfect-information attempt to write directly to a duped real fd still cannot bypass suppression",
    r["outcome"] == Outcome.CORRECT and r.get("detail") is None,
    str(r),
)

# ---------------------------------------------------------------------------
# 6. Old-pattern-vs-new-boundary comparison (UNCHANGED; safe, local, synthetic
#    -- does NOT touch app/experiments/accumulation_probe/oracle_runner.py)
# ---------------------------------------------------------------------------
print("== 6. Old vulnerable pattern (synthetic reproduction) vs new boundary ==")


def old_pattern_grade(candidate_src: str, fn_name: str, arg, expected_value):
    """Minimal, LOCAL reproduction of the pre-Stage-E0 vulnerability
    (oracle_runner.grade() + tasks.py::make_test_code() concatenating
    candidate code and an expected-value table into ONE exec'd module).
    Never touches the real oracle_runner.py/tasks.py files."""
    combined_src = (
        candidate_src
        + f"\n_EXPECTED = {expected_value!r}\n"
        + f"_RESULT = {fn_name}({arg!r})\n"
    )
    ns: dict = {}
    exec(compile(combined_src, "<old-pattern>", "exec"), ns, ns)
    return ns


old_ns = old_pattern_grade(
    "def leak(a):\n    return _EXPECTED\n",  # candidate references the module-level sentinel directly
    "leak", 0, SENTINEL,
)
check(
    "OLD pattern IS vulnerable (documented for comparison, not exploited against real AP-0)",
    old_ns.get("_RESULT") == SENTINEL,
    f"old pattern's candidate successfully read _EXPECTED == {old_ns.get('_RESULT')!r}",
)

r_new = run_case("def leak(a):\n    return _EXPECTED\n", "leak", [0], SENTINEL)
check(
    "NEW boundary is NOT vulnerable to the identical attack",
    r_new["outcome"] == Outcome.CANDIDATE_ERROR and r_new["detail"]["error_type"] == "NameError",
    str(r_new),
)

print(f"\n(original-suite subtotal after section 6: {_passed} passed, {_failed} failed)")

# ===========================================================================
# 7. NEW (E0.1) -- failure attribution, result-domain contract, positive
#    control against the runtime sentinel specifically
# ===========================================================================
print("== 7. E0.1: failure attribution ==")

r = run_case("def f(a):\n    raise SystemExit(7)\n", "f", [0], 0)
check(
    "SystemExit is classified CANDIDATE_ERROR, not infrastructure (Codex's demonstrated defect, fixed)",
    r["outcome"] == Outcome.CANDIDATE_ERROR and r["detail"]["error_type"] == "SystemExit",
    str(r),
)

r = run_case("import os\ndef f(a):\n    os._exit(5)\n", "f", [0], 0)
check(
    "os._exit (uncatchable) is honestly classified CHILD_TERMINATED_UNVERIFIED, never infrastructure",
    r["outcome"] == Outcome.CHILD_TERMINATED_UNVERIFIED,
    str(r),
)

r = run_case("def f(a):\n    return a\n", "f", [0], 0, sandbox_profile="/nonexistent/rung1_e01_bogus_profile.sb")
check(
    "a genuine sandbox-launch/apply failure IS classified SANDBOX_INFRASTRUCTURE_ERROR (positive control for the taxonomy split)",
    r["outcome"] == Outcome.SANDBOX_INFRASTRUCTURE_ERROR,
    str(r),
)

r = run_case("def f(a):\n    raise ValueError('ordinary')\n", "f", [0], 0)
check("ordinary candidate exception still classified CANDIDATE_ERROR (regression)", r["outcome"] == Outcome.CANDIDATE_ERROR, str(r))

r = run_case("import time\ndef f(a):\n    time.sleep(3)\n    return a\n", "f", [0], 0, timeout=1)
check("timeout still classified TIMEOUT, distinct from the new CHILD_TERMINATED_UNVERIFIED (regression)", r["outcome"] == Outcome.TIMEOUT, str(r))

print("== 7b. E0.1: strongest-counterexample reassessment (selective-exclusion) ==")
# Codex's counterargument (independent validation sec 18): a policy could
# succeed on easy cases and terminate on hard ones, with terminations
# excluded as "infrastructure" -- inflating measured correctness. Confirm
# that SystemExit (the demonstrated, realistic way a candidate would
# actually "give up") is no longer eligible for that exemption at all.
r = run_case("def f(a):\n    raise SystemExit()\n", "f", [0], 0)
check(
    "a candidate 'giving up' via SystemExit can no longer obtain an infrastructure exemption",
    r["outcome"] not in (Outcome.SANDBOX_INFRASTRUCTURE_ERROR,) and r["outcome"] == Outcome.CANDIDATE_ERROR,
    str(r),
)

print("== 7c. E0.1: frozen result-domain contract ==")

r = _validate_and_compare({"status": "ok"}, 5)
check("missing 'value' key is malformed, never silently coerced to None", r["outcome"] == Outcome.MALFORMED_RESULT, str(r))

r = _validate_and_compare({"status": "ok", "value": None}, None)
check("explicit JSON null IS a permitted, distinguishable value (matches expected None correctly)", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def f(a):\n    return True\n", "f", [0], 1)
check("True != 1 under the frozen domain (candidate returns True, expected is int 1)", r["outcome"] == Outcome.INCORRECT, str(r))

r = run_case("def f(a):\n    return 1\n", "f", [0], True)
check("1 != True under the frozen domain (candidate returns int 1, expected is True)", r["outcome"] == Outcome.INCORRECT, str(r))

r = run_case("def f(a):\n    return True\n", "f", [0], True)
check("True == True still CORRECT (bool/bool unaffected)", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def f(a):\n    return [True, 1, False]\n", "f", [0], [1, 1, 0])
check("bool/int type-strictness applies recursively inside lists", r["outcome"] == Outcome.INCORRECT, str(r))

r = run_case("def f(a):\n    return float('nan')\n", "f", [0], 1.0)
check("NaN return value is rejected as malformed (never comparable meaningfully)", r["outcome"] == Outcome.MALFORMED_RESULT, str(r))

r = run_case("def f(a):\n    return float('inf')\n", "f", [0], 1.0)
check("inf return value is rejected as malformed", r["outcome"] == Outcome.MALFORMED_RESULT, str(r))

deep_bad = 1
for _ in range(8):
    deep_bad = [deep_bad]
r = _validate_and_compare({"status": "ok", "value": deep_bad}, deep_bad)
check("excessively nested value (8 deep, limit 6) is rejected as malformed", r["outcome"] == Outcome.MALFORMED_RESULT, str(r))

deep_ok = 1
for _ in range(5):
    deep_ok = [deep_ok]
r = _validate_and_compare({"status": "ok", "value": deep_ok}, deep_ok)
check("valid boundary: nesting depth 5 (within limit 6) is accepted and correctly compared", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def f(a):\n    return []\n", "f", [0], [])
check("valid boundary: empty list", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("def f(a):\n    return {}\n", "f", [0], {})
check("valid boundary: empty dict", r["outcome"] == Outcome.CORRECT, str(r))

r = run_case("class C:\n    pass\ndef f(a):\n    return {'x': C()}\n", "f", [0], None)
check("unsupported nested type (custom object inside dict) is rejected as malformed", r["outcome"] == Outcome.MALFORMED_RESULT, str(r))

print("== 7d. E0.1: positive control for the corrected secrecy methodology ==")
# Pairs directly with section 2's fix: proves the qualification METHOD
# (using RUNTIME_SENTINEL specifically) can detect deliberate disclosure
# when it is actually present, not merely that E0 happens to look clean.
old_ns2 = old_pattern_grade("def leak(a):\n    return _EXPECTED\n", "leak", 0, RUNTIME_SENTINEL)
check(
    "positive control: old shared-process pattern DOES disclose the runtime sentinel when deliberately shared",
    old_ns2.get("_RESULT") == RUNTIME_SENTINEL,
    f"got {old_ns2.get('_RESULT')!r}",
)
r = run_case("def leak(a):\n    return _EXPECTED\n", "leak", [0], RUNTIME_SENTINEL)
check(
    "E0 does NOT disclose the identical runtime sentinel under the identical attack",
    r["outcome"] == Outcome.CANDIDATE_ERROR and r["detail"]["error_type"] == "NameError",
    str(r),
)
r = run_case("def leak(a):\n    return RUNTIME_SENTINEL_NEVER_DEFINED\n", "leak", [0], RUNTIME_SENTINEL)
check(
    "execution-validity control: this run_case call itself genuinely executed the candidate (sanity check on the check)",
    execution_confirmed(r),
    str(r),
)

print(f"\n{_passed} passed, {_failed} failed")
if _failures:
    print("\nFAILURES:")
    for name, detail in _failures:
        print(f"  - {name}: {detail}")
sys.exit(1 if _failed else 0)
