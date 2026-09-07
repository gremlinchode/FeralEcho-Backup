#!/usr/bin/env python3
"""
scripts/verify_functional_quality_signal.py — Phase 1 discrimination test
matrix, per audits/2026-09-06_phase1_functional_quality_signal.md.

Read-only with respect to production state: calls app.core.functional_quality
directly (itself not imported by any live path), runs real code inside the
real F2 kernel sandbox for each test candidate, and never touches
RiverBrain, self_edit_manager.py's live fitness gate, or any persisted
production file. Does not commit or mutate anything.

Run: python3 scripts/verify_functional_quality_signal.py
"""

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "core"))

from app.core.functional_quality import combined_quality_score


# All four cases deliberately take a single `code: str` parameter, matching
# the real domain this tool targets — every one of the 25 real retained
# self-edit backups sampled for this report takes a code/original_code
# string parameter. An earlier draft of this matrix used a generic 2-arg
# add(a,b) for Case A and a numeric classify_number(n) for Case B; both
# produced misleading results (a 2-required-param function is correctly
# skipped rather than tested at all — a documented scope limit, not a bug —
# and passing the fixed synthetic string "test" into a function expecting a
# number raised a real, if false, TypeError). Kept as a documented finding
# in the report rather than silently fixed away: this module's synthetic-
# argument strategy (a single fixed string) is well-matched to this specific
# codebase's actual self-edit-candidate shape, and is a genuine, disclosed
# false-failure risk for any hypothetical non-string-typed candidate.

CASE_A_SIMPLE_CORRECT = (
    "def strip_blank_lines(code: str) -> str:\n"
    "    return \"\\n\".join(line for line in code.split(\"\\n\") if line.strip())\n"
)

CASE_B_COMPLEX_CORRECT = """
def normalize_code(code: str) -> str:
    lines = code.split("\\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        elif stripped.startswith("#"):
            try:
                result.append(stripped)
            except Exception:
                continue
        else:
            result.append(stripped if len(stripped) < 100 else stripped[:100])
    return "\\n".join(result)
"""

CASE_C_SIMPLE_BROKEN = (
    "def broken(code: str) -> str:\n"
    "    return undefined_name_never_defined_anywhere\n"
)

CASE_D_COMPLEX_BROKEN = """
def refactor_code(code: str) -> str:
    lines = []
    for line in code.split("\\n"):
        if line.strip():
            try:
                lines.append(HelperTransformerNeverDefined(line).apply())
            except ValueError:
                continue
        elif line == "":
            lines.append(line)
    return "\\n".join(lines)
"""


def run_case(label, code):
    print(f"\n{'=' * 70}\nCASE: {label}\n{'=' * 70}")
    result = combined_quality_score(code, task_type="coding")
    print(f"  ast_score          = {result['ast_score']}")
    print(f"  functional_outcome = {result['functional_outcome']}")
    tested = result["functional_detail"].get("tested")
    if tested:
        for t in tested:
            print(f"    - {t['kind']} {t['name']}: {t['outcome']}"
                  + (f" ({t['error']})" if t.get("error") else ""))
    print(f"  combined_score      = {result['combined_score']}")
    return result


def main():
    results = {}
    results["A_simple_correct"] = run_case("A — Simple correct", CASE_A_SIMPLE_CORRECT)
    results["B_complex_correct"] = run_case("B — Complex correct", CASE_B_COMPLEX_CORRECT)
    results["C_simple_broken"] = run_case("C — Simple broken", CASE_C_SIMPLE_BROKEN)
    results["D_complex_broken"] = run_case("D — Complex broken", CASE_D_COMPLEX_BROKEN)

    self_edit_generated = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "core", "self_edit_generated.py",
    )
    with open(self_edit_generated, "r", encoding="utf-8") as f:
        real_broken_code = f.read()
    results["E_real_deployed_broken"] = run_case(
        "E — Real currently-deployed self_edit_generated.py (known-bad)", real_broken_code
    )

    print(f"\n{'=' * 70}\nCASE F / BULK — all 25 real retained self-edit backups\n{'=' * 70}")
    backup_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "core", "self_edit_backups",
    )
    backup_files = sorted(glob.glob(os.path.join(backup_dir, "*.py")))
    bulk_results = []
    for path in backup_files:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        r = combined_quality_score(code, task_type="coding")
        bulk_results.append((os.path.basename(path), r))
        print(f"  {os.path.basename(path):45s} ast={r['ast_score']}  functional={r['functional_outcome']:20s}  combined={r['combined_score']}")

    outcomes = [r["functional_outcome"] for _, r in bulk_results]
    print(f"\n  Summary: {len(bulk_results)} files")
    for outcome in ("verified_success", "verified_failure", "not_applicable", "sandbox_infra_failure"):
        print(f"    {outcome:22s}: {outcomes.count(outcome)}")

    print(f"\n{'=' * 70}\nDISCRIMINATION CHECK (Acceptance Criteria 1-3)\n{'=' * 70}")
    a, b, c, d, e = (results["A_simple_correct"], results["B_complex_correct"],
                      results["C_simple_broken"], results["D_complex_broken"],
                      results["E_real_deployed_broken"])
    print(f"  Criterion 1 (known-working -> positive functional result): "
          f"A={a['functional_outcome']}, B={b['functional_outcome']} "
          f"-> {'PASS' if a['functional_outcome']=='verified_success' and b['functional_outcome']=='verified_success' else 'FAIL'}")
    print(f"  Criterion 2 (known-broken -> negative functional result): "
          f"C={c['functional_outcome']}, D={d['functional_outcome']}, E={e['functional_outcome']} "
          f"-> {'PASS' if c['functional_outcome']=='verified_failure' and d['functional_outcome']=='verified_failure' and e['functional_outcome']=='verified_failure' else 'FAIL'}")
    print(f"  Criterion 3 (complex-broken NOT >= verified-correct): "
          f"D.combined={d['combined_score']} vs A.combined={a['combined_score']} "
          f"-> {'PASS' if d['combined_score'] < a['combined_score'] else 'FAIL'}")
    print(f"  Criterion 3b (real E vs A): "
          f"E.combined={e['combined_score']} (ast={e['ast_score']}) vs A.combined={a['combined_score']} "
          f"-> {'PASS' if e['combined_score'] < a['combined_score'] else 'FAIL'}")


if __name__ == "__main__":
    main()
