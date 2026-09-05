#!/usr/bin/env python3
"""Control run for the live validation: identical 5 tasks, identical
pinned model, identical isolation -- but with the new agreement/
completeness mechanisms patched to be permanent no-ops, reproducing
exactly the PRE-refactor behavior. Run on the same day, same real
conditions as verify_synthesis_refactor_live.py, specifically so the
before/after comparison in the refactor report is a real, controlled
measurement rather than an inference from log data alone.
"""
import os
import sys
import time

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_capability_pilot as base_pilot  # noqa: E402
import app.core.river_deliberation as rd  # noqa: E402
from verify_synthesis_refactor_live import VALIDATION_TASKS  # noqa: E402

# Disable the new mechanisms -- reproduces the exact pre-refactor
# behavior (synthesis always invoked, its output always accepted
# as-is) without touching the real file on disk.
rd.detect_full_agreement = lambda valid_opinions: None
rd.find_missing_agreed_definitions = lambda valid_opinions, synthesis_code: set()


def main():
    proxy = base_pilot.install_isolation()
    from app.core.echo_model_orchestrator import MODEL_POOL

    results = []
    for task in VALIDATION_TASKS:
        print(f"\n=== {task['task_id']} (CONTROL -- fix disabled) ===")
        t0 = time.time()
        try:
            response = rd.deliberate_and_learn(
                prompt=task["prompt"], task_type="coding", river_brain=proxy,
                model_pool=MODEL_POOL, max_tokens=2048,
                trace_id=f"control_run_{task['task_id']}",
            )
        except Exception as e:
            print(f"  EXCEPTION: {type(e).__name__}: {e}")
            results.append({"task_id": task["task_id"], "exception": str(e)})
            continue
        gen_time = time.time() - t0
        code = base_pilot.clean_code(response)
        verify = base_pilot.objective_verify(code, task["test_code"])
        print(f"  passed={verify['passed']} gen_time={gen_time:.1f}s response_len={len(response)}")
        if not verify["passed"]:
            print(f"  output_tail: {verify['output_tail'][-300:]}")
        results.append({"task_id": task["task_id"], "passed": verify["passed"]})

    passed = sum(1 for r in results if r.get("passed"))
    print(f"\n{'='*60}")
    print(f"CONTROL (fix disabled) pass rate: {passed}/{len(results)}")


if __name__ == "__main__":
    main()
