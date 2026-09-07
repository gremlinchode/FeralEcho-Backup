#!/usr/bin/env python3
"""
scripts/adversarial_functional_verifier_test.py — Phase 1A adversarial test
matrix against app.core.functional_quality (Phase 1's functional verifier).

Read-only w.r.t. production state. Isolated test fixture only — not wired
into anything live. See audits/2026-09-06_phase1a_functional_verifier_adversarial.md.
"""
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.functional_quality import functional_execution_score, combined_quality_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(label, code, timeout=10.0):
    t0 = time.time()
    r = functional_execution_score(code, timeout=timeout)
    dt = time.time() - t0
    print(f"\n{'='*70}\n{label}\n{'='*70}")
    print(f"  outcome={r['outcome']}  blocked_write={r['blocked_write']}  timed_out={r['timed_out']}  wall={dt:.2f}s")
    if r.get('detail'):
        print(f"  detail: {r['detail'][:300]}")
    if r.get('tested'):
        for t in r['tested']:
            print(f"    - {t['kind']} {t['name']}: {t['outcome']}" + (f" ({t['error']})" if t.get('error') else ""))
    return r


# ---------------------------------------------------------------------
# 1/2: correct simple / complex
# ---------------------------------------------------------------------
run("1. Correct + Simple", "def strip_blank(code):\n    return '\\n'.join(l for l in code.split('\\n') if l.strip())\n")

run("2. Correct + Complex", """
def normalize(code):
    lines = code.split("\\n")
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        elif s.startswith("#"):
            try:
                out.append(s)
            except Exception:
                continue
        else:
            out.append(s if len(s) < 100 else s[:100])
    return "\\n".join(out)
""")

# ---------------------------------------------------------------------
# 3/4: broken simple / complex
# ---------------------------------------------------------------------
run("3. Simple + Broken (undefined name)", "def broken(code):\n    return undefined_var_xyz\n")

run("4. Complex + Broken (structurally rich, undefined ref)", """
def refactor(code):
    out = []
    for line in code.split("\\n"):
        if line.strip():
            try:
                out.append(HelperNeverDefined(line).apply())
            except ValueError:
                continue
        elif line == "":
            out.append(line)
    return "\\n".join(out)
""")

# ---------------------------------------------------------------------
# 5: executes but wrong result — THE key adversarial case
# ---------------------------------------------------------------------
run("5a. Wrong result — trivially wrong transform (uppercase instead of documented lowercase)",
    "def to_lower(code):\n    # contract: should lowercase; actually uppercases\n    return code.upper()\n")

run("5b. Wrong result — silently returns constant garbage regardless of input",
    "def process(code):\n    return 'DEFINITELY_NOT_RELATED_TO_INPUT'\n")

run("5c. Wrong result — off-by-one that never raises",
    "def take_first_n(code):\n    # off-by-one: should be code[:5], silently wrong for len<5 too, never raises\n    return code[:5] + code[6:6]\n")

# ---------------------------------------------------------------------
# 6: no-op
# ---------------------------------------------------------------------
run("6a. No-op function (does literally nothing, returns None)",
    "def process(code):\n    pass\n")

run("6b. No-op class (empty __init__, real-looking but empty methods never tested)", """
class Processor:
    def __init__(self, code):
        self.code = code
    def process(self):
        pass  # never called by the verifier -- only __init__ is smoke-tested
    def get_result(self):
        return None  # also never called
""")

# ---------------------------------------------------------------------
# 7: exception swallowing
# ---------------------------------------------------------------------
run("7a. Swallowed exception, returns input unchanged (silently broken)", """
def transform(code):
    try:
        result = 1 / 0
        return result
    except Exception:
        pass
    return code
""")

run("7b. Swallowed exception, returns plausible-looking but wrong value", """
def compute_score(code):
    try:
        return len(code) / 0
    except ZeroDivisionError:
        return 0.0  # plausible-looking float, masks the real division bug entirely
""")

# ---------------------------------------------------------------------
# 9: multiple definitions
# ---------------------------------------------------------------------
run("9a. One correct + one broken function (both top-level)", """
def good_func(code):
    return code.strip()

def bad_func(code):
    return undefined_thing_here
""")

run("9b. One correct + one broken, broken defined FIRST (order sensitivity check)", """
def bad_func(code):
    return undefined_thing_here

def good_func(code):
    return code.strip()
""")

run("9c. Five correct + one trivially-crashing helper (asymmetric penalty check)", """
def helper_a(code):
    return code.strip()
def helper_b(code):
    return code.upper()
def helper_c(code):
    return code.lower()
def helper_d(code):
    return code[::-1]
def helper_e(code):
    return code + code
def unrelated_debug_helper(code):
    return code.nonexistent_attribute_xyz
""")

# ---------------------------------------------------------------------
# 10: timeout
# ---------------------------------------------------------------------
run("10. Bounded timeout case (sleeps 3s under a 1s timeout)",
    "import time\ndef slow(code):\n    time.sleep(3)\n    return code\n", timeout=1.0)

# ---------------------------------------------------------------------
# 11: blocked operation, already partially explored above via real corpus
# ---------------------------------------------------------------------
run("11. Explicit blocked write (function body attempts a real write outside scratch)",
    "def leaky(code):\n    with open('/tmp/echo_adversarial_test_leak.txt', 'w') as f:\n        f.write(code)\n    return code\n")

# ---------------------------------------------------------------------
# 12: sandbox infra failure — genuinely unavailable dependency
# ---------------------------------------------------------------------
run("12. Genuinely unavailable import at module level (should fail at exec_module, before smoke-test loop even runs)",
    "import this_module_definitely_does_not_exist_anywhere\ndef f(code):\n    return code\n")

# ---------------------------------------------------------------------
# 13: wrong input type — signature classes
# ---------------------------------------------------------------------
run("13a. Function expecting int, called with 'test' string", "def double(n: int):\n    return n * 2\n")
run("13b. Function expecting list, called with 'test' string", "def total(items: list):\n    return sum(items)\n")
run("13c. Function expecting dict, called with 'test' string", "def lookup(d: dict):\n    return d['key']\n")
run("13d. Function with 0 required args", "def constant():\n    return 42\n")
run("13e. Function with 2 required args (should be skipped, not guessed)", "def combine(a, b):\n    return a + b\n")

# ---------------------------------------------------------------------
# 14: side effects
# ---------------------------------------------------------------------
run("14a. stdout/stderr only, no file writes", "def loud(code):\n    print('hello')\n    import sys\n    print('err', file=sys.stderr)\n    return code\n")
run("14b. Write INSIDE scratch dir would be allowed in principle, but candidate can't know its own scratch path", "def writer(code):\n    import os\n    return os.environ.get('HOME')\n")

# ---------------------------------------------------------------------
# 15: determinism — run the SAME candidate 5x
# ---------------------------------------------------------------------
print(f"\n{'='*70}\n15. Determinism check — same candidate, 5 runs\n{'='*70}")
det_code = "def strip_blank(code):\n    return '\\n'.join(l for l in code.split('\\n') if l.strip())\n"
outcomes = []
for i in range(5):
    r = functional_execution_score(det_code)
    outcomes.append(r["outcome"])
print(f"  outcomes across 5 runs: {outcomes}")
print(f"  deterministic: {len(set(outcomes)) == 1}")

# Also check the real known-bad file for determinism
print(f"\n  Determinism on real known-bad file (self_edit_generated.py), 3 runs:")
with open(os.path.join(ROOT, "app/core/self_edit_generated.py")) as f:
    real_bad = f.read()
bad_outcomes = []
for i in range(3):
    r = functional_execution_score(real_bad)
    bad_outcomes.append(r["outcome"])
print(f"  outcomes: {bad_outcomes}  deterministic: {len(set(bad_outcomes)) == 1}")

# ---------------------------------------------------------------------
# Real corpus re-test (independent re-derivation, not trusting Phase 1's numbers)
# ---------------------------------------------------------------------
print(f"\n{'='*70}\nREAL CORPUS RE-TEST (25 files, independent re-derivation)\n{'='*70}")
backup_dir = os.path.join(ROOT, "app/core/self_edit_backups")
files = sorted(glob.glob(os.path.join(backup_dir, "*.py")))
corpus_results = []
for path in files:
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    r = combined_quality_score(code, task_type="coding")
    corpus_results.append((os.path.basename(path), r))
    print(f"  {os.path.basename(path):40s} ast={r['ast_score']}  functional={r['functional_outcome']:20s}  combined={r['combined_score']}  blocked_write={r['functional_detail']['blocked_write']}")

outcomes = [r["functional_outcome"] for _, r in corpus_results]
print(f"\n  n={len(corpus_results)}")
for o in ("verified_success", "verified_failure", "not_applicable", "sandbox_infra_failure"):
    print(f"    {o:22s}: {outcomes.count(o)}")

# Determinism across the WHOLE corpus, second pass
print(f"\n  Second independent pass over corpus (determinism check at scale):")
corpus_results_2 = []
for path in files:
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    r = combined_quality_score(code, task_type="coding")
    corpus_results_2.append((os.path.basename(path), r["functional_outcome"]))

mismatches = [(a[0], a[1], b[1]) for a, b in zip([(n, r["functional_outcome"]) for n, r in corpus_results], corpus_results_2) if a[1] != b[1]]
print(f"  mismatches between pass 1 and pass 2: {len(mismatches)}")
for m in mismatches:
    print(f"    {m}")
