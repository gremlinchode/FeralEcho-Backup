#!/usr/bin/env python3
"""
Tier-5 correctness retest driver -- executes the exact experiment specified
in audits/tier5_refactor_report.md's own "NEXT EXPERIMENT" section: for
each task in the fresh, hash-frozen tier5_retest_task_pool.py suite, run
TWO real, paired conditions against the SAME task:

  TREATMENT: the real, unmodified, live production synthesis path
             (detect_full_agreement / find_missing_agreed_definitions
             active exactly as shipped in app/core/river_deliberation.py).
  CONTROL:   the identical real deliberate_and_learn() call, with those
             same two functions monkeypatched to permanent no-ops --
             reproducing exact pre-Tier-5-refactor behavior -- using the
             IDENTICAL monkeypatch already established by
             scripts/verify_synthesis_refactor_control.py (reused
             verbatim, not reinvented).

Reuses run_capability_pilot.py's install_isolation() / clean_code() /
objective_verify() unmodified. No production source file is imported for
mutation -- river_deliberation.py's module-level function attributes are
monkeypatched in-process, per-condition, never written to disk.

Results are appended to results JSONL files immediately after each
condition completes, so a partial run (if stopped early) preserves real,
usable paired data rather than losing it.
"""
import json
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
from tier5_retest_task_pool import TASKS  # noqa: E402

RESULTS_PATH = "audits/tier5_retest/tier5_retest_results.jsonl"
PROGRESS_PATH = "audits/tier5_retest/tier5_retest_progress.txt"

_REAL_detect_full_agreement = rd.detect_full_agreement
_REAL_find_missing_agreed_definitions = rd.find_missing_agreed_definitions


def _set_treatment():
    rd.detect_full_agreement = _REAL_detect_full_agreement
    rd.find_missing_agreed_definitions = _REAL_find_missing_agreed_definitions


def _set_control():
    rd.detect_full_agreement = lambda valid_opinions: None
    rd.find_missing_agreed_definitions = lambda valid_opinions, synthesis_code: set()


def _append_result(record):
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()


def _progress(msg):
    print(msg, flush=True)
    with open(PROGRESS_PATH, "a") as f:
        f.write(msg + "\n")
        f.flush()


def run_one_condition(task, condition_name, proxy):
    from app.core.echo_model_orchestrator import MODEL_POOL

    trace_id = f"tier5_retest_{condition_name}_{task['task_id']}"
    t0 = time.time()
    try:
        response = rd.deliberate_and_learn(
            prompt=task["prompt"], task_type="coding", river_brain=proxy,
            model_pool=MODEL_POOL, max_tokens=2048, trace_id=trace_id,
        )
    except Exception as e:
        gen_time = time.time() - t0
        record = {
            "task_id": task["task_id"], "category": task["category"],
            "condition": condition_name, "trace_id": trace_id,
            "exception": f"{type(e).__name__}: {e}",
            "passed": False, "generation_time": round(gen_time, 2),
        }
        _append_result(record)
        return record

    gen_time = time.time() - t0
    code = base_pilot.clean_code(response)
    verify = base_pilot.objective_verify(code, task["test_code"])
    record = {
        "task_id": task["task_id"], "category": task["category"],
        "condition": condition_name, "trace_id": trace_id,
        "raw_response": response, "candidate_code": code,
        "passed": verify["passed"], "ran_ok": verify["ran_ok"],
        "output_tail": verify["output_tail"],
        "generation_time": round(gen_time, 2),
        "verification_time": verify["verification_time"],
    }
    _append_result(record)
    return record


def main():
    _progress(f"=== Tier-5 retest run starting, {len(TASKS)} tasks, PID={os.getpid()} ===")
    proxy = base_pilot.install_isolation()

    for i, task in enumerate(TASKS):
        _progress(f"\n[{i+1}/{len(TASKS)}] {task['task_id']} ({task['category']})")

        _set_treatment()
        t_result = run_one_condition(task, "treatment", proxy)
        _progress(f"  TREATMENT passed={t_result.get('passed')} "
                   f"gen_time={t_result.get('generation_time')}s "
                   f"exc={t_result.get('exception')}")

        _set_control()
        c_result = run_one_condition(task, "control", proxy)
        _progress(f"  CONTROL   passed={c_result.get('passed')} "
                   f"gen_time={c_result.get('generation_time')}s "
                   f"exc={c_result.get('exception')}")

    _progress("\n=== Tier-5 retest run COMPLETE ===")


if __name__ == "__main__":
    main()
