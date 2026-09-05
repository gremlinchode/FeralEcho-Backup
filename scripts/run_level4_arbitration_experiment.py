#!/usr/bin/env python3
"""
LEVEL 3 -> LEVEL 4 VALIDATION EXPERIMENT (prospective arm).
Standalone script. Does NOT modify production self_edit_manager.py,
does NOT deploy anything (every trial uses dry_run=True, which the
existing execute_self_edit() code already guarantees skips the final
backup/save/load-into-production step entirely). Uses 100% existing,
already-verified infrastructure: execute_self_edit(dry_run=True) is the
exact same call Optuna's own hourly dry-run search already makes ~10x/hour.

Conditions (randomized order across trials, not blocked):
  A - CURRENT SYSTEM: perform_self_edit(dry_run=True, target_task_type=None)
      -- lets the real, unmodified arbitration logic (shadow-first, per
      Part 5 of the prior forensic report) pick the target exactly as it
      would in real production operation.
  B - EMPIRICAL PRIORITY: target_task_type forced to whatever
      memory/self_model.json's real, RiverBrain-derived target currently
      is (read live at experiment start, held constant across all trials
      in this batch -- "same starting repository state").
  C - BASELINE: target_task_type forced to a uniform random choice among
      the five real task-type buckets self-edit prompts support
      (coding, personal, creative, reasoning, general), independent of
      both the empirical and shadow signals -- operationalizes "remove
      adaptive targeting influence."

Primary endpoint measured immediately (no 25-minute wait, unlike the
retrospective conversational quality_score.delta): candidate quality vs.
a SINGLE, FIXED production-file baseline score, both computed with the
exact same echo_quality_scorer._score_response_quality(code, "coding")
function used everywhere else in this codebase. This is a deliberate,
disclosed proxy for the retrospective endpoint -- see the report's own
explicit limitation statement.
"""
import json
import os
import random
import sys
import time

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")

N_PER_CONDITION = 5
RESULTS_PATH = "audits/level4_experiment_raw_results.jsonl"
TASK_TYPES = ["coding", "personal", "creative", "reasoning", "general"]


def _append(record: dict) -> None:
    os.makedirs("audits", exist_ok=True)
    with open(RESULTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def main():
    from app.core import self_edit_manager
    from app.core.self_model_updater import SelfModelUpdater
    import echo_quality_scorer as qs

    # --- fixed baseline: score the CURRENT production file once, held
    # constant across every trial in this batch ---
    with open(self_edit_manager.SELF_EDIT_FILE, "r", encoding="utf-8") as f:
        production_code = f.read()
    production_score = qs._score_response_quality(production_code, task_type="coding")
    print(f"[baseline] current production file quality score = {production_score}")
    _append({"phase": "baseline", "production_score": production_score,
             "production_file": self_edit_manager.SELF_EDIT_FILE})

    # --- condition B's fixed empirical target, read once, live ---
    empirical_target = SelfModelUpdater().get_weak_task_type()
    print(f"[setup] Condition B empirical target (held fixed all batch) = {empirical_target}")
    _append({"phase": "setup", "condition_b_empirical_target": empirical_target})

    # --- build randomized trial order across conditions ---
    trials = (["A"] * N_PER_CONDITION) + (["B"] * N_PER_CONDITION) + (["C"] * N_PER_CONDITION)
    random.shuffle(trials)
    print(f"[setup] randomized trial order: {trials}")
    _append({"phase": "setup", "trial_order": trials})

    for i, cond in enumerate(trials):
        print(f"\n=== TRIAL {i+1}/{len(trials)} — condition {cond} ===")
        t0 = time.time()
        try:
            if cond == "A":
                target_used_label = "arbitration(real)"
                success, detail = self_edit_manager.perform_self_edit(
                    dry_run=True, target_task_type=None
                )
            else:
                if cond == "B":
                    forced_target = empirical_target
                else:  # C
                    forced_target = random.choice(TASK_TYPES)
                target_used_label = forced_target
                prompt = self_edit_manager._build_targeted_prompt(forced_target, 0.5)
                success, detail = self_edit_manager.execute_self_edit(prompt, dry_run=True)
        except Exception as e:
            success, detail = False, f"EXCEPTION: {e}"
            target_used_label = "?"

        latency = time.time() - t0
        candidate_score = None
        delta = None
        if success and isinstance(detail, str) and os.path.isfile(detail):
            try:
                with open(detail, "r", encoding="utf-8") as f:
                    candidate_code = f.read()
                candidate_score = qs._score_response_quality(candidate_code, task_type="coding")
                delta = candidate_score - production_score
            except Exception as e:
                detail = f"{detail} (scoring failed: {e})"

        record = {
            "trial": i + 1, "condition": cond, "target_used": target_used_label,
            "success": success, "detail_summary": str(detail)[:200],
            "candidate_score": candidate_score, "production_score": production_score,
            "delta": delta, "latency_seconds": round(latency, 1),
        }
        _append(record)
        print(f"  target={target_used_label} success={success} "
              f"candidate_score={candidate_score} delta={delta} ({latency:.1f}s)")


if __name__ == "__main__":
    main()
