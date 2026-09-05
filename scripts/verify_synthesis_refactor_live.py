#!/usr/bin/env python3
"""Small, real, end-to-end validation of the refactored
deliberate_and_learn() against 5 fresh coding tasks (never used in the
original pilot, the Tier-4 suites, or the regression tests). Not a
statistical comparison -- that is explicitly a separate "next experiment"
(see the refactor report) -- this exercises the real production pipeline
(real council selection, real Ollama calls, the new agreement-detection/
completeness-check logic, real logging) end-to-end and checks it behaves
sanely. Uses the same isolation pattern as the Tier-4 apparatus so no
production RiverBrain/interaction-log state is touched.
"""
import os
import sys
import json
import time

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_capability_pilot as base_pilot  # noqa: E402
import app.core.river_deliberation as rd  # noqa: E402

VALIDATION_TASKS = [
    {
        "task_id": "val01",
        "prompt": "Write a Python function `is_power_of_two(n)` that returns True if the "
                  "positive integer n is a power of two (1, 2, 4, 8, ...), False otherwise. "
                  "n=0 or negative n should return False.",
        "test_code": """
assert is_power_of_two(1) == True
assert is_power_of_two(2) == True
assert is_power_of_two(3) == False
assert is_power_of_two(1024) == True
assert is_power_of_two(0) == False
assert is_power_of_two(-4) == False
print('ALL_TESTS_PASSED')
""",
    },
    {
        "task_id": "val02",
        "prompt": "Write a Python function `remove_duplicates_sorted(nums)` that removes "
                  "duplicate values from a SORTED list in place is not required -- just return "
                  "a new sorted list with duplicates removed, preserving order.",
        "test_code": """
assert remove_duplicates_sorted([1,1,2,2,3]) == [1,2,3]
assert remove_duplicates_sorted([]) == []
assert remove_duplicates_sorted([5]) == [5]
assert remove_duplicates_sorted([1,1,1,1]) == [1]
print('ALL_TESTS_PASSED')
""",
    },
    {
        "task_id": "val03",
        "prompt": "Write a Python function `count_words(text)` that returns the number of "
                  "whitespace-separated words in a string. An empty or whitespace-only string "
                  "has 0 words.",
        "test_code": """
assert count_words("hello world") == 2
assert count_words("") == 0
assert count_words("   ") == 0
assert count_words("one") == 1
assert count_words("  a  b   c  ") == 3
print('ALL_TESTS_PASSED')
""",
    },
    {
        "task_id": "val04",
        "prompt": "Write a Python function `sum_of_squares(n)` that returns the sum of squares "
                  "of all integers from 1 to n inclusive. n=0 returns 0.",
        "test_code": """
assert sum_of_squares(0) == 0
assert sum_of_squares(1) == 1
assert sum_of_squares(3) == 14
assert sum_of_squares(10) == 385
print('ALL_TESTS_PASSED')
""",
    },
    {
        "task_id": "val05",
        "prompt": "Write a Python function `is_valid_parens_simple(s)` that returns True if a "
                  "string containing only '(' and ')' characters has balanced, properly nested "
                  "parentheses, False otherwise.",
        "test_code": """
assert is_valid_parens_simple("()") == True
assert is_valid_parens_simple("(())") == True
assert is_valid_parens_simple("(()") == False
assert is_valid_parens_simple(")(") == False
assert is_valid_parens_simple("") == True
print('ALL_TESTS_PASSED')
""",
    },
]


def main():
    proxy = base_pilot.install_isolation()
    print("[setup] isolation installed (real RiverBrain writes blocked, recorded instead)")

    from app.core.echo_model_orchestrator import MODEL_POOL
    with open("audits/tier4_apparatus/pinned_model.json") as f:
        pinned = json.load(f)["pinned_model"]
    print(f"[setup] using Tier-4's pinned model for continuity where applicable: {pinned}")

    log_path_before = 0
    if os.path.exists(rd._SYNTHESIS_INTEGRITY_LOG):
        with open(rd._SYNTHESIS_INTEGRITY_LOG) as f:
            log_path_before = sum(1 for _ in f)

    results = []
    for task in VALIDATION_TASKS:
        print(f"\n=== {task['task_id']} ===")
        t0 = time.time()
        try:
            response = rd.deliberate_and_learn(
                prompt=task["prompt"], task_type="coding", river_brain=proxy,
                model_pool=MODEL_POOL, max_tokens=2048,
                trace_id=f"live_validation_{task['task_id']}",
            )
        except Exception as e:
            print(f"  EXCEPTION: {type(e).__name__}: {e}")
            results.append({"task_id": task["task_id"], "exception": str(e)})
            continue
        gen_time = time.time() - t0
        code = base_pilot.clean_code(response)
        verify = base_pilot.objective_verify(code, task["test_code"])
        print(f"  passed={verify['passed']} gen_time={gen_time:.1f}s "
              f"response_len={len(response)} side_effects_total={len(base_pilot._side_effects_detected)}")
        results.append({
            "task_id": task["task_id"], "passed": verify["passed"],
            "gen_time": round(gen_time, 1), "response_len": len(response),
        })

    log_path_after = 0
    new_entries = []
    if os.path.exists(rd._SYNTHESIS_INTEGRITY_LOG):
        with open(rd._SYNTHESIS_INTEGRITY_LOG) as f:
            lines = f.readlines()
            log_path_after = len(lines)
            new_entries = [json.loads(l) for l in lines[log_path_before:]]

    print(f"\n{'='*60}")
    passed = sum(1 for r in results if r.get("passed"))
    print(f"Validation pass rate: {passed}/{len(results)}")
    print(f"Synthesis integrity log entries written this run: {log_path_after - log_path_before}")
    for e in new_entries:
        print(f"  trace_id={e.get('trace_id')} selection_method={e.get('selection_method')} "
              f"n_candidates={e.get('n_valid_opinions')} missing={e.get('missing_agreed_definitions')}")
    print(f"Total production_side_effect_detected events: {len(base_pilot._side_effects_detected)}")
    print(f"(non-zero is expected and correct here -- these are recorded proxy hits, "
          f"not real writes; isolation is what makes them safe, not their absence)")


if __name__ == "__main__":
    main()
