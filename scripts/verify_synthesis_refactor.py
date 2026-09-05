#!/usr/bin/env python3
"""
Regression tests for the Tier-4-confirmatory-driven synthesis refactor
(app/core/river_deliberation.py) and the self-edit framing guard
(app/core/self_edit_manager.py). Follows this project's own established
verify_*.py convention (plain assert-based checks, a final pass/fail
tally) rather than introducing a new test framework.

Covers the 7 regression tests named in the refactor mission, with one
honest deviation stated where the mission asked for something this
conservative pass does not implement (see Test 5's own note).
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")

import app.core.river_deliberation as rd  # noqa: E402

_results = []


def check(name: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    _results.append((name, condition))
    print(f"[{status}] {name}" + (f" — {detail}" if detail and not condition else ""))


# ---------------------------------------------------------------------------
# Test 1 — Complete candidate preservation
# ---------------------------------------------------------------------------
print("\n=== Test 1: Complete candidate preservation ===")
opinions_t1 = {
    "model_a": (
        "class ThreadSafeCounter:\n"
        "    def __init__(self):\n"
        "        self.value = 0\n"
        "    def increment(self):\n"
        "        self.value += 1\n"
        "if __name__ == '__main__':\n"
        "    c = ThreadSafeCounter()\n"
        "    c.increment()\n"
    ),
    "model_b": (
        "class ThreadSafeCounter:\n"
        "    def __init__(self):\n"
        "        self.value = 0\n\n"
        "    def increment(self):\n"
        "        self.value = self.value + 1\n"
        "if __name__ == '__main__':\n"
        "    c = ThreadSafeCounter()\n"
    ),
}
# A synthesis that drops the class -- the exact real cs09 failure shape.
bad_synthesis_t1 = "if __name__ == '__main__':\n    c = ThreadSafeCounter()\n    c.increment()\n"
missing_t1 = rd.find_missing_agreed_definitions(opinions_t1, bad_synthesis_t1)
check("Test1_detects_dropped_class", missing_t1 == {"ThreadSafeCounter"},
      f"got {missing_t1}")

good_synthesis_t1 = opinions_t1["model_a"]
missing_t1b = rd.find_missing_agreed_definitions(opinions_t1, good_synthesis_t1)
check("Test1_accepts_complete_synthesis", missing_t1b == set(), f"got {missing_t1b}")

# Regression case for a REAL bug found during live validation (2026-09-04):
# a synthesis response with leading prose before its code fence -- the
# single most common real model output shape (confirmed live, task
# val01) -- must NOT be spuriously flagged as missing the definition it
# actually contains, just because the prose makes the raw text fail a
# direct ast.parse(). This is the exact case that produced a 5/5 false-
# positive fallback rate in the first live validation run before the fix.
prose_wrapped_synthesis_t1 = (
    "Here's the final code:\n\n```python\n" + opinions_t1["model_a"] + "\n```\n\n"
    "This solution uses a shared lock to keep increment() thread-safe."
)
missing_t1c = rd.find_missing_agreed_definitions(opinions_t1, prose_wrapped_synthesis_t1)
check("Test1_prose_wrapped_complete_synthesis_not_falsely_flagged",
      missing_t1c == set(), f"got {missing_t1c}")

fallback_t1 = rd.select_best_fallback_candidate(opinions_t1)
fallback_names_t1 = rd._extract_top_level_names(rd._extract_candidate_code(fallback_t1) or "")
check("Test1_fallback_contains_required_definition", "ThreadSafeCounter" in fallback_names_t1)

# ---------------------------------------------------------------------------
# Test 2 — Unanimous candidate preservation
# ---------------------------------------------------------------------------
print("\n=== Test 2: Unanimous candidate preservation ===")
identical_code = "def find_missing(nums):\n    n = len(nums)\n    return n * (n + 1) // 2 - sum(nums)\n"
opinions_t2 = {
    "qwen2.5-coder:7b": identical_code,
    "mlx:qwen3": identical_code,
    "echo:latest": identical_code,
}
agreed_t2 = rd.detect_full_agreement(opinions_t2)
check("Test2_detects_unanimous_agreement", agreed_t2 is not None)
check("Test2_returned_code_matches_candidates",
      agreed_t2 is not None and rd._ast_normalize(agreed_t2) == rd._ast_normalize(identical_code))

# ---------------------------------------------------------------------------
# Test 3 — Unsupported-operation detection (the real bf06 shape: structurally
# identical modulo whitespace/comments, containing no "- 1"; the fix's actual
# guarantee is that no LLM synthesis call — and therefore no possible
# fabricated operation — ever happens in this case, not a general diff
# against arbitrary introduced operations. Stated honestly, not oversold.)
# ---------------------------------------------------------------------------
print("\n=== Test 3: Unsupported-operation detection (via full-agreement short-circuit) ===")
opinions_t3 = {
    "m1": "def find_missing(nums):\n    n = len(nums)\n    return n * (n + 1) // 2 - sum(nums)\n",
    "m2": "def find_missing(nums):\n    n = len(nums)  # count of elements\n\n    return n * (n + 1) // 2 - sum(nums)\n",
    "m3": "def find_missing(nums):\n\n    n = len(nums)\n    return n * (n + 1) // 2 - sum(nums)\n",
}
agreed_t3 = rd.detect_full_agreement(opinions_t3)
check("Test3_agreement_detected_despite_formatting_differences", agreed_t3 is not None)
check("Test3_no_unsupported_operation_present", agreed_t3 is not None and "- 1" not in agreed_t3.replace(" ", ""))

# ---------------------------------------------------------------------------
# Test 4 — Genuine disagreement: the reconciliation mechanism (real LLM
# synthesis) must still be reachable, not bypassed, when candidates
# actually differ in approach.
# ---------------------------------------------------------------------------
print("\n=== Test 4: Genuine disagreement is not short-circuited ===")
opinions_t4 = {
    "m1": "def max_of(a, b):\n    return a if a > b else b\n",
    "m2": "def max_of(a, b):\n    return max(a, b)\n",
}
agreed_t4 = rd.detect_full_agreement(opinions_t4)
check("Test4_genuine_disagreement_not_shortcircuited", agreed_t4 is None)
# Real disagreement should also not falsely trip the completeness check
# against a synthesis that reasonably reconciles them:
reconciled_t4 = "def max_of(a, b):\n    return max(a, b)\n"
missing_t4 = rd.find_missing_agreed_definitions(opinions_t4, reconciled_t4)
check("Test4_reconciled_synthesis_not_falsely_flagged", missing_t4 == set(), f"got {missing_t4}")

# ---------------------------------------------------------------------------
# Test 5 — "Passing candidate preference." HONEST LIMITATION: this
# conservative pass implements syntactic-validity preference (a candidate
# that parses beats one that doesn't), not full execution/test-based
# preference — there is no general-purpose oracle for arbitrary
# conversational coding questions outside the Tier-4 experiment's own
# frozen task suites (unlike self-edit's F2 gate or the Tier-4 harness,
# an ordinary user's coding question has no test to run against). Tested
# as what was actually built, not what the mission's ideal would be —
# see the refactor report's "remaining risks" section for this gap
# stated plainly.
# ---------------------------------------------------------------------------
print("\n=== Test 5: Syntactic-validity preference (documented scope limit vs. full execution evidence) ===")
opinions_t5 = {
    "broken": "def f(x):\n    return x +",  # syntax error
    "valid": "def f(x):\n    return x + 1\n",
}
best_t5 = rd.select_best_fallback_candidate(opinions_t5)
check("Test5_prefers_syntactically_valid_candidate", best_t5 == opinions_t5["valid"])

# ---------------------------------------------------------------------------
# Test 6 — Self-edit isolation: ordinary coding tasks must not inherit
# self-edit-specific framing. Source-anchor style, matching this project's
# own liveness-ledger precedent for structural guarantees.
# ---------------------------------------------------------------------------
print("\n=== Test 6: Self-edit framing isolation ===")
with open("app/core/river_deliberation.py") as f:
    river_source = f.read()
check("Test6_deliberation_never_imports_CODE_OUTPUT_RULES",
      "CODE_OUTPUT_RULES" not in river_source)
check("Test6_deliberation_never_reads_self_edit_generated_file",
      "self_edit_generated" not in river_source)

with open("app/core/self_edit_manager.py") as f:
    sem_lines = f.readlines()
# Exclude comment-only lines before counting -- a bare substring search
# would also match this file's OWN new guard comments mentioning the
# function by name in prose (confirmed live: lines 568/584 do exactly
# this), the same self-referential-comment false-positive class already
# documented elsewhere in this project (e.g. CLAUDE.md Finding 63/84's
# echo_projects_isolation checks). Real call sites are code, not comments.
_code_lines = [ln for ln in sem_lines if not ln.strip().startswith("#")]
_code_text = "".join(_code_lines)
import re as _re
def_count = len(_re.findall(r"^def generate_code_from_plan\(", _code_text, _re.MULTILINE))
all_refs = len(_re.findall(r"generate_code_from_plan\(", _code_text))
real_call_sites = all_refs - def_count
# generate_code_from_plan is defined once and has exactly one real call
# site within this file's own pipeline; a second, unexpected call site
# would be the first sign of scope creep into non-self-edit use.
check("Test6_generate_code_from_plan_has_exactly_one_def_and_one_call_in_self_edit_manager",
      def_count == 1 and real_call_sites == 1,
      f"def_count={def_count}, real_call_sites={real_call_sites}")

# ---------------------------------------------------------------------------
# Test 7 — No regression in self-edit functionality: CODE_OUTPUT_RULES'
# actual string content (what the model receives) must be byte-identical
# to before this refactor — only comments were added, never the real
# instructions.
# ---------------------------------------------------------------------------
print("\n=== Test 7: No self-edit regression (CODE_OUTPUT_RULES content unchanged) ===")
import app.core.self_edit_manager as sem  # noqa: E402
_EXPECTED_RULES_START = "STRICT OUTPUT RULES — violations cause system failure:"
_EXPECTED_RULE_8 = "Do NOT import from app.core.self_edit_generated — you ARE that file."
check("Test7_rules_still_start_correctly", sem.CODE_OUTPUT_RULES.strip().startswith(_EXPECTED_RULES_START))
check("Test7_rule_8_content_unchanged", _EXPECTED_RULE_8 in sem.CODE_OUTPUT_RULES)
check("Test7_apply_to_code_rule_still_present", "apply_to_code(code: str) -> str" in sem.CODE_OUTPUT_RULES)

# ---------------------------------------------------------------------------
# Non-coding task types must be byte-for-byte unaffected (blast-radius check)
# ---------------------------------------------------------------------------
print("\n=== Test 8: Case-insensitive fence language tag (real bug found during live validation) ===")
from app.core.code_verification import extract_python_blocks  # noqa: E402
capitalized_fence_response = (
    "Here's a Python function using a dictionary:\n\n"
    "```Python\ndef remove_duplicates_sorted(nums):\n    return sorted(set(nums))\n```\n"
)
blocks_t8 = extract_python_blocks(capitalized_fence_response)
check("Test8_capitalized_python_fence_extracted", len(blocks_t8) == 1 and "remove_duplicates_sorted" in blocks_t8[0])
extracted_t8 = rd._extract_candidate_code(capitalized_fence_response)
names_t8 = rd._extract_top_level_names(extracted_t8 or "")
check("Test8_names_found_from_capitalized_fence", names_t8 == {"remove_duplicates_sorted"})

print("\n=== Blast-radius check: non-coding synthesis template untouched ===")
check("NonCoding_template_unchanged_word",
      "coherence and relevance" in rd.SYNTHESIS_SYSTEM_TEMPLATE
      and "your role is preservation" not in rd.SYNTHESIS_SYSTEM_TEMPLATE.lower())

print(f"\n{'='*60}")
total = len(_results)
passed = sum(1 for _, ok in _results if ok)
print(f"TOTAL: {passed}/{total} passed")
if passed != total:
    print("FAILING:", [n for n, ok in _results if not ok])
    sys.exit(1)
else:
    print("ALL REGRESSION TESTS PASSED")
