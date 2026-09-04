#!/usr/bin/env python3
"""Verify every reference_solution in scripts/tier4_task_pool.py actually
passes its own test_code, via the real, unmodified sandbox
(run_capability_pilot.objective_verify -> code_verification.verify_in_sandbox).
Read-only with respect to production; does not touch any Ollama model.
This is ground-truth verification of the TEST ITSELF, not a generation run.
"""
import os
import sys

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_capability_pilot as base_pilot  # noqa: E402
from tier4_task_pool import TASKS  # noqa: E402

failures = []
for t in TASKS:
    verify = base_pilot.objective_verify(t["reference_solution"], t["test_code"])
    status = "PASS" if verify["passed"] else "FAIL"
    print(f"{t['task_id']:6s} {t['category']:28s} {status}"
          f"{'' if verify['passed'] else '  <<< ' + verify['output_tail'][-300:]}")
    if not verify["passed"]:
        failures.append(t["task_id"])

print()
print(f"Total: {len(TASKS)}, passed: {len(TASKS) - len(failures)}, failed: {len(failures)}")
if failures:
    print("FAILING TASK IDS:", failures)
    sys.exit(1)
else:
    print("ALL REFERENCE SOLUTIONS VERIFIED CORRECT")
