"""
Rung-1 Stage E0/E0.1 -- trusted evaluator boundary.

Implements the invariant from audits/2026-09-23_rung1_engineering_gate_
specification.md secs 4-9: untrusted candidate execution can never
address protected expected outputs, hidden test structures, or trusted
comparison state.

Architecture (per-case, process-separated), unchanged from E0 and
independently confirmed intact by Codex's own 2026-09-23 validation
(audits/2026-09-23_codex_e0_independent_scientific_validation.md):

  trusted parent (this module, this process)
    owns:    expected value, held only in a local Python variable inside
             run_case() for the duration of that call -- NOTE (E0.1
             correction, per the independent review): this module does
             not, and cannot, guarantee that a CALLER does not also
             retain its own copy of that value elsewhere. "Confined to
             this one stack frame" describes what run_case() itself does
             with the value it is given, not a property of every copy
             that may exist in the caller's own process before or after
             calling this function.
    sends:   candidate source (by scratch-file path) + permitted call
             args (via stdin JSON) to a FRESH sandboxed subprocess
    never sends: the expected value, in any form, to that subprocess

  untrusted child (candidate_worker.py, launched fresh per test case)
    receives: candidate source, permitted input
    returns:  one bounded, typed JSON value on stdout, or a classified
              failure -- nothing else is ever read from it

  trusted comparison (this module, after the child has exited)
    compares its own parsed value against its own expected value, under
    the explicit result-domain/equality contract in _validate_and_compare
    (E0.1 -- see below); the candidate never participates in or can
    inspect this step

Reuses sandbox/echo_sandbox.sb UNCHANGED for kernel-level containment.
(E0.1 correction, per the independent review, source-verified against the
actual profile file rather than repeated from the E0 report): the profile
does NOT deny both fork and exec by omission. `(allow process-exec*)` is
an EXPLICIT allow at echo_sandbox.sb's own line 46, required so
sandbox-exec can exec the Python interpreter itself; only process-FORK is
denied (by omission from the allow list). Ordinary subprocess-spawning
attempts by candidate code (e.g. `subprocess.run(["echo", "hi"])`) still
fail, but because they require fork, not because exec is denied -- see
scripts/verify_rung1_e0_trusted_evaluator.py's process-spawn attack,
which independently confirms this distinction produces a real
PermissionError in practice, not merely in theory.

DOCUMENTED DEVIATION from the engineering-gate specification's suggestion
of a NEW, narrower-read-allowlisted sandbox profile (spec sec 6-7): this
implementation does not author a new profile. For the specific invariant
this stage exists to establish -- can a candidate obtain the protected
expected value THIS MODULE HOLDS -- the load-bearing guarantee is
CONTROLLER DISCIPLINE: this module never writes the expected value to any
file, environment variable, or descriptor the child could reach,
regardless of how broad the sandbox's own read permission is. This is a
narrower and more precisely stated claim than "nothing sentinel-bearing
exists anywhere on disk" -- the independent review correctly noted that
the acceptance suite's own hardcoded synthetic literals ARE readable,
public, checked-in source, which is a real limitation of using them as
evidence, not a defect in this module's own behavior. General filesystem-
read confinement (denying a candidate from reading arbitrary OTHER files
on the host unrelated to this experiment, e.g. real hidden AP-0 task
answers a caller might have loaded from a readable file) remains a real,
separately-named, deliberately DEFERRED integration precondition -- see
the Stage E0.1 report's "Remaining limitations" section. It must be
resolved before any real hidden task artifact is ever attached to this
evaluator; it is explicitly out of scope for E0/E0.1, which qualify the
synthetic-secret-separation mechanism only.

Two additional, independent hardenings ARE applied here, beyond reusing
echo_sandbox.sb as-is, because they cost nothing and close real,
concretely-named channels from the engineering-gate specification's own
perfect-information attack table (sec 7):
  - The child's environment is an explicit, minimal dict (_minimal_env()),
    never the inherited os.environ -- closes the environment-variable
    leak channel regardless of what the parent process's own environment
    happens to contain.
  - subprocess.run(..., close_fds=True) -- the default on POSIX since
    Python 3.2, made explicit here -- ensures no file descriptor open in
    the parent (e.g. a log file handle) is inherited by the child.

Per-case granularity (spec sec 8): a fresh, unique scratch directory and a
fresh subprocess are used for every single test case. No state, scratch
file, or process is ever shared or reused across cases -- a candidate
executed for case N has no way to observe anything about case N-1 or
N+1, because the process it ran in no longer exists by the time any
other case runs.

(E0.1) Failure-attribution repair -- the independently-demonstrated
defect this revision exists to close: a candidate calling `sys.exit(N)`
previously terminated the WORKER process with a real nonzero exit code
this module's own `run_case()` classified as SANDBOX_INFRASTRUCTURE_ERROR
purely because the exit was nonzero -- treating an authentic OS-level
OBSERVATION (a real exit code) as an authentic causal DIAGNOSIS (the
sandbox/launch mechanism failed), which it was not: the candidate
deliberately terminated its own execution, and no evaluator component
failed. This has real consequences for any future aggregation layer that
excludes "infrastructure failures" from a correctness denominator: a
policy that learns to exit early on cases it cannot solve, rather than
returning a wrong answer, could have those cases silently vanish from the
denominator, manufacturing apparent improvement with no real competence
gain (Codex's own strongest counterexample, sec 18 of the independent
validation). Fixed at the root, in candidate_worker.py: SystemExit and
KeyboardInterrupt raised by candidate code are now caught inside the
worker itself and reported through the ordinary "candidate_error"
envelope, the same as any other exception -- they never reach this
module as a raw nonzero exit code at all. What DOES still reach this
module as a raw nonzero exit code is now split into two honestly
different cases, neither of which is "SANDBOX_INFRASTRUCTURE_ERROR" by
default:
  - exit code 65 with no parseable stdout: sandbox-exec's own documented
    convention (echo_sandbox.sb's header comment: "Syntax error in this
    file: sandbox-exec exits 65, subprocess never runs") for a genuine
    sandbox-APPLY failure -- a real, trusted-launch-evidence-backed
    infrastructure fault, still classified SANDBOX_INFRASTRUCTURE_ERROR.
  - any OTHER nonzero exit with no parseable stdout: something terminated
    the child process in a way candidate_worker.py's own exception
    handling could not intercept (os._exit(), a genuine interpreter
    fault, or something this module has no way to enumerate) --
    classified CHILD_TERMINATED_UNVERIFIED, a new, explicitly separate
    outcome. This is NOT eligible for automatic infrastructure-exclusion
    by any future aggregation layer -- it must be treated as attributable
    to the candidate/attempt by default until a stronger, independent
    controller-side signal can disambiguate it further, which is out of
    scope for E0.1.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SANDBOX_PROFILE = str(_REPO / "sandbox" / "echo_sandbox.sb")
_WORKER = str(Path(__file__).resolve().parent / "candidate_worker.py")
_PYTHON = "/Users/richietate/miniforge3/envs/feral_echo/bin/python3"
_DEFAULT_TIMEOUT_S = 10
_MAX_STDOUT_BYTES = 4096  # a post-capture bound, not a streaming one -- see module docstring's
                          # "resource bounds" note and the E0.1 report's disclosed limitation
_SANDBOX_APPLY_FAILURE_EXIT_CODE = 65  # documented sandbox-exec convention, per echo_sandbox.sb's own header

# --- (E0.1) Frozen result domain -----------------------------------------
# The smallest domain actually needed by AP-0-shaped small pure-function
# tasks (re-checked directly against app/experiments/accumulation_probe/
# tasks.py's own real return shapes: ints, bools, strings, lists, dicts
# with string keys, tuples serialized as lists) -- not a general-purpose
# RPC/serialization system. Deliberately does NOT support: non-string
# dict keys (JSON itself cannot express them without lossy coercion, so
# nothing is "added" by trying), custom objects of any kind (already
# impossible to cross the JSON boundary at all), or unbounded nesting.
_MAX_DEPTH = 6


def _depth_within_limit(value, limit: int, _current: int = 0) -> bool:
    """True iff `value`'s JSON-shaped nesting never exceeds `limit`.
    Recurses only into list/dict, the only container types this domain
    permits."""
    if _current > limit:
        return False
    if isinstance(value, list):
        return all(_depth_within_limit(v, limit, _current + 1) for v in value)
    if isinstance(value, dict):
        return all(_depth_within_limit(v, limit, _current + 1) for v in value.values())
    return True


def _contains_non_finite(value) -> bool:
    """True iff `value` contains a non-finite float (inf/-inf/nan)
    anywhere in its structure. Python's json module, by default, happily
    encodes and decodes these as the non-standard `Infinity`/`-Infinity`/
    `NaN` tokens -- real values the frozen domain explicitly excludes,
    since a scientific comparison against a NaN is meaningless (NaN != NaN
    under IEEE 754, so a candidate returning NaN could never be judged
    CORRECT even against an identically-NaN expected value, and comparing
    inf/-inf is rarely a real task requirement here)."""
    if isinstance(value, float):
        return value != value or value in (float("inf"), float("-inf"))  # value != value catches NaN
    if isinstance(value, list):
        return any(_contains_non_finite(v) for v in value)
    if isinstance(value, dict):
        return any(_contains_non_finite(v) for v in value.values())
    return False


def _typed_equal(actual, expected) -> bool:
    """Recursive equality under the frozen domain's explicit contract:
    booleans and integers are DISTINCT types (True != 1), applied at
    every nesting level -- Python's own `==` would otherwise silently
    accept `True == 1`, which the independent review correctly flagged as
    an implicit, undeclared policy choice rather than a stated one. This
    is the ONE comparison-semantics case the review specifically named;
    no broader type-coercion policy is invented beyond it, per the
    "do not overengineer unsupported cases" instruction."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _typed_equal(a, e) for a, e in zip(actual, expected)
        )
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            _typed_equal(actual[k], expected[k]) for k in expected
        )
    return actual == expected


class Outcome:
    """The failure taxonomy from the engineering-gate specification sec
    20, extended (E0.1) with one new, explicitly-honest category. Every
    value here is a distinct string constant, unchanged in spelling from
    E0 for the five that survive, so existing callers/tests keyed on
    these strings are unaffected."""

    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    CANDIDATE_ERROR = "CANDIDATE_ERROR"
    TIMEOUT = "TIMEOUT"
    SANDBOX_INFRASTRUCTURE_ERROR = "SANDBOX_INFRASTRUCTURE_ERROR"
    MALFORMED_RESULT = "MALFORMED_RESULT"
    # (E0.1) New. A child process terminated abnormally (nonzero exit, no
    # parseable stdout) in a way this module cannot mechanically attribute
    # to either a confirmed infrastructure fault or a confirmed candidate
    # action. Per the mission's own instruction ("represent that
    # uncertainty honestly rather than falsely labeling it
    # infrastructure"), this is deliberately its own category, NOT folded
    # into SANDBOX_INFRASTRUCTURE_ERROR. Any future aggregation/analysis
    # layer MUST NOT treat this as an automatically-excludable
    # infrastructure failure -- see the module docstring's "Failure-
    # attribution repair" section for why that specific exclusion is the
    # exact selective-exclusion counterexample this revision closes.
    CHILD_TERMINATED_UNVERIFIED = "CHILD_TERMINATED_UNVERIFIED"


def _minimal_env() -> dict:
    """Explicit, minimal child environment -- never os.environ. See module
    docstring: this is one of the two hardenings applied beyond reusing
    echo_sandbox.sb as-is."""
    return {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}


def _validate_and_compare(parsed: dict, expected) -> dict:
    """(E0.1, extracted for direct unit-testability without a real
    subprocess round-trip.) Pure function: given an already-parsed
    top-level JSON object from the child's stdout and the trusted
    `expected` value, applies the frozen result-domain contract and
    returns the same {"outcome": ..., "detail": ...} shape run_case()
    returns. Called only after run_case()'s own launch/timeout/size/
    parse-failure checks have already passed. Never touches the
    filesystem, a process, or any I/O -- exists specifically so the
    engineering-gate specification's own result-contract requirements
    (missing-value, type-strict equality, depth bound, non-finite
    rejection) can be exercised directly against hand-built dicts in
    tests, the same discipline this project's own liveness-ledger/seam-
    engine verification suites already use for their own pure
    evaluators."""
    status = parsed.get("status")

    if status == "candidate_error":
        return {"outcome": Outcome.CANDIDATE_ERROR,
                "detail": {"stage": parsed.get("stage"), "error_type": parsed.get("error_type")}}
    if status == "malformed_result":
        return {"outcome": Outcome.MALFORMED_RESULT,
                "detail": {"error_type": parsed.get("error_type")}}
    if status != "ok":
        return {"outcome": Outcome.MALFORMED_RESULT, "detail": "unknown status value"}

    # (E0.1) Require the "value" KEY to be present, not merely permit
    # `.get("value")` to silently resolve a missing key to None -- an "ok"
    # envelope with no "value" key at all is a malformed envelope, never
    # a legitimate "the candidate returned None" observation. This is the
    # exact ambiguity the independent review named.
    if "value" not in parsed:
        return {"outcome": Outcome.MALFORMED_RESULT, "detail": "ok status missing required 'value' field"}

    actual = parsed["value"]

    if not _depth_within_limit(actual, _MAX_DEPTH):
        return {"outcome": Outcome.MALFORMED_RESULT, "detail": f"value exceeds max nesting depth {_MAX_DEPTH}"}
    if _contains_non_finite(actual):
        return {"outcome": Outcome.MALFORMED_RESULT, "detail": "value contains a non-finite float (inf/-inf/nan)"}

    # --- TRUSTED COMPARISON. Happens exclusively here, in this process,
    # strictly after the child has already exited, under the explicit
    # type-strict equality contract above. The candidate never
    # participates in, or can inspect, this step. ---
    if _typed_equal(actual, expected):
        return {"outcome": Outcome.CORRECT, "detail": None}
    return {"outcome": Outcome.INCORRECT, "detail": {"actual": actual}}


def run_case(candidate_source: str, fn_name: str, call_args: list, expected,
             timeout: float = _DEFAULT_TIMEOUT_S, sandbox_profile: str = None) -> dict:
    """The trusted comparison entry point, and the only function in this
    module allowed to hold `expected`.

    `expected` is a plain Python value, held in this function's own local
    scope for the entire call. It is NEVER serialized to disk, NEVER
    placed in the child's environment or arguments, and NEVER referenced
    by candidate_path's own file content -- the only place THIS FUNCTION
    puts it while it runs is this stack frame, in this process, which the
    sandboxed child cannot read, inspect, or attach to. (See the module
    docstring's E0.1 correction: this function does not, and cannot,
    control whether the CALLER retains its own separate copy of the same
    value elsewhere -- that is a caller obligation, not one this function
    enforces or can enforce.)

    `sandbox_profile` (E0.1, optional, defaults to the real, unmodified
    echo_sandbox.sb): exists ONLY so a test can safely exercise a genuine
    sandbox-launch failure (by pointing at a nonexistent profile path)
    without ever touching the real production sandbox file. Production
    callers must never pass this.

    Returns {"outcome": Outcome.*, "detail": ..., "_researcher_stdout":
    <optional, only on malformed/infra paths>, "_researcher_stderr":
    <optional>}. The "_researcher_*" keys are for post-hoc human/audit
    use only -- callers building a learner-visible feedback contract on
    top of this function (a later stage, not part of E0/E0.1) must
    extract only "outcome" and must never forward these keys onward.
    """
    profile = sandbox_profile or _SANDBOX_PROFILE

    with tempfile.TemporaryDirectory(prefix="rung1_e0_case_") as scratch:
        scratch = os.path.realpath(scratch)
        candidate_path = os.path.join(scratch, "candidate.py")
        with open(candidate_path, "w", encoding="utf-8") as f:
            f.write(candidate_source)

        stdin_payload = json.dumps({"args": call_args}) + "\n"

        try:
            proc = subprocess.run(
                ["sandbox-exec", "-f", profile, "-D", f"SCRATCH={scratch}",
                 _PYTHON, "-I", "-B", "-S", _WORKER, candidate_path, fn_name],
                input=stdin_payload,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=scratch,
                env=_minimal_env(),
                close_fds=True,
            )
        except subprocess.TimeoutExpired:
            return {"outcome": Outcome.TIMEOUT, "detail": None}
        except OSError as e:
            # (E0.1) Narrowed from a bare `except Exception`: OSError
            # (FileNotFoundError included) is the real, confirmable
            # signature of "the launcher itself could not even start the
            # subprocess" -- e.g. the sandbox-exec binary or the pinned
            # interpreter is missing. This IS genuine, trusted launch
            # evidence.
            return {"outcome": Outcome.SANDBOX_INFRASTRUCTURE_ERROR,
                    "detail": f"{type(e).__name__}: launch failed"}

        researcher_stderr = (proc.stderr or "")[:_MAX_STDOUT_BYTES]

        if proc.returncode != 0:
            stdout_stripped = (proc.stdout or "").strip()
            if not stdout_stripped:
                if proc.returncode == _SANDBOX_APPLY_FAILURE_EXIT_CODE:
                    # Confirmed, documented sandbox-exec convention (see
                    # module docstring) -- a genuine sandbox-apply
                    # failure, not a candidate action.
                    return {"outcome": Outcome.SANDBOX_INFRASTRUCTURE_ERROR,
                            "detail": f"sandbox-exec exit {proc.returncode} (profile apply failure)",
                            "_researcher_stderr": researcher_stderr}
                # (E0.1) Anything else nonzero with no parseable output is
                # honestly uncertain -- see Outcome.CHILD_TERMINATED_UNVERIFIED's
                # own docstring for why this must not become an
                # infrastructure exemption by default.
                return {"outcome": Outcome.CHILD_TERMINATED_UNVERIFIED,
                        "detail": f"nonzero exit {proc.returncode}, no parseable output",
                        "_researcher_stderr": researcher_stderr}
            # A nonzero exit WITH parseable stdout would be unusual (the
            # worker's own main() always returns 0 on every path it
            # controls) -- fall through to ordinary parsing below rather
            # than assuming infrastructure, since real output exists to
            # evaluate.

        stdout = (proc.stdout or "").strip()
        if not stdout or len(stdout.encode("utf-8")) > _MAX_STDOUT_BYTES:
            # (E0.1) Byte length, not character length -- a real,
            # if small, correction: multi-byte UTF-8 content could
            # previously exceed the intended byte budget while still
            # passing a character-count check. Still a POST-CAPTURE
            # bound -- see module-level _MAX_STDOUT_BYTES comment and the
            # E0.1 report's disclosed limitation; a fully streaming,
            # capture-time bound was judged out of scope for this stage.
            return {"outcome": Outcome.MALFORMED_RESULT,
                    "detail": "empty or oversized output",
                    "_researcher_stderr": researcher_stderr}

        try:
            parsed = json.loads(stdout)
        except Exception:
            return {"outcome": Outcome.MALFORMED_RESULT,
                    "detail": "unparseable stdout",
                    "_researcher_stdout": stdout[:_MAX_STDOUT_BYTES],
                    "_researcher_stderr": researcher_stderr}

        if not isinstance(parsed, dict) or "status" not in parsed:
            return {"outcome": Outcome.MALFORMED_RESULT, "detail": "malformed schema",
                    "_researcher_stderr": researcher_stderr}

        return _validate_and_compare(parsed, expected)
