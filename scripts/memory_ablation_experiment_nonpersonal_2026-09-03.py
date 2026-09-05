#!/usr/bin/env python3
"""Memory retrieval ablation experiment, non-personal path (2026-09-03).

Follow-up to scripts/memory_ablation_experiment.py (2026-07-23), whose own
30-prompt sample landed 29/30 on the personal/DIRECT_ECHO_TASKS bypass path
by chance (random shuffling over a personal-dominated interaction_log), per
audits/2026-09-02_gap_analysis_and_next_investigations.md's own "Highest-
Value Unknown" and audits/2026-09-02_information_flow_integrity.md's
Recommended Experiment #1: does memory retrieval measurably affect the
MAJORITY of real traffic -- the multi-councillor deliberation path -- at
all? That path was previously tested at n<=1.

Reuses the original script's real, already-validated machinery wholesale
(RiverBrain neutralization, source tagging, embedding-distance/quality
scoring, noise-floor calibration) via direct import -- only the prompt
SELECTION differs: explicitly stratified across coding/creative/reasoning/
general, excluding personal entirely, capped smaller (N per type) to keep
real wall-clock time tractable for full multi-councillor deliberation calls
(observed 1-3+ minutes each this session).
"""
import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import sys
import json
import shutil
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

sys.path.insert(0, str(ROOT / "scripts"))
import importlib
_base = importlib.import_module("memory_ablation_experiment")

_STAMP = datetime.now().strftime("%Y%m%dT%H%M%SZ")
RESULTS_PATH = ROOT / "scripts" / "memory_ablation_results_nonpersonal_2026-09-03.json"
TEST_SET_PATH = ROOT / "scripts" / "memory_ablation_test_set_nonpersonal_2026-09-03.json"
LOG_PATH = ROOT / "memory" / "interaction_log.jsonl"
RIVER_BRAIN_PATH = ROOT / "memory" / "river_brain.pkl"
BACKUP_PATH = ROOT / "memory" / f"river_brain.pkl.pre_ablation_backup_nonpersonal_{_STAMP}"

N_PER_TASK_TYPE = 3
TARGET_TASK_TYPES = ("coding", "creative", "reasoning", "general")
N_NOISE_FLOOR = 3
SOURCE_TAG = "memory_ablation_experiment_nonpersonal"
# _base.run_once() references the bare name SOURCE_TAG via a global lookup
# in its own module's namespace at call time (not captured at def time) --
# reassigning it here means every call this script makes through
# _base.run_once() is tagged with THIS script's source, not the original
# 2026-07-23 script's, keeping the two runs forensically distinguishable in
# interaction_log.jsonl even though both are safely excluded from real
# training/rating paths either way (neither is source=="user_conversation").
_base.SOURCE_TAG = SOURCE_TAG


def load_candidate_entries():
    entries = []
    with open(LOG_PATH) as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            prompt = e.get("prompt") or ""
            task_type = e.get("task_type", "")
            if not prompt or len(prompt) > _base.MAX_PROMPT_CHARS:
                continue
            if task_type not in TARGET_TASK_TYPES:
                continue
            if "self_edit_generated.py" in prompt or "FeralEcho importable modules" in prompt:
                continue
            entries.append(e)
    return entries


def select_stratified_prompts_with_real_memory_hits(candidates, n_per_type):
    """Same real-hit-required logic as the original script's selector, but
    stratified: keep filling each task_type's own bucket up to n_per_type
    instead of taking the first N overall (which is what let the original
    run land almost entirely on one task type by chance)."""
    from app.routes_echo_studio import _build_full_prompt
    import random
    random.shuffle(candidates)

    buckets = {t: [] for t in TARGET_TASK_TYPES}
    for e in candidates:
        t = e.get("task_type")
        if t not in buckets or len(buckets[t]) >= n_per_type:
            continue
        msg = e["prompt"]
        session = {"conv_history": [], "history_summaries": []}
        try:
            full_msg, system_context = _build_full_prompt(msg, session)
        except Exception as ex:
            print(f"  [skip] _build_full_prompt raised: {ex}")
            continue
        if "Retrieved context" in system_context:
            buckets[t].append({
                "timestamp": e.get("timestamp"),
                "task_type": t,
                "original_model": e.get("model"),
                "original_quality_score": e.get("quality_score"),
                "prompt": msg,
                "control_system_context_preview": system_context[:300],
            })
            print(f"  [hit] task_type={t} ({len(buckets[t])}/{n_per_type}) ts={e.get('timestamp')}")
        if all(len(v) >= n_per_type for v in buckets.values()):
            break

    selected = []
    for t in TARGET_TASK_TYPES:
        selected.extend(buckets[t])
        print(f"  {t}: {len(buckets[t])}/{n_per_type} real memory-hit prompts found")
    return selected


def save_progress(results, noise_floor):
    with open(RESULTS_PATH, "w") as f:
        json.dump({"pairs": results, "noise_floor": noise_floor, "stratified_by": TARGET_TASK_TYPES}, f, indent=2)


def main():
    print(f"[{datetime.now()}] Backing up river_brain.pkl -> {BACKUP_PATH.name} (defense-in-depth)")
    if RIVER_BRAIN_PATH.exists():
        shutil.copy2(RIVER_BRAIN_PATH, BACKUP_PATH)

    _base.neutralize_river_brain_writes()

    log_lines_before = sum(1 for _ in open(LOG_PATH))

    print("Loading non-personal candidate entries from interaction_log.jsonl ...")
    candidates = load_candidate_entries()
    print(f"  {len(candidates)} candidate entries after filtering (task_type in {TARGET_TASK_TYPES})")

    print(f"Selecting up to {N_PER_TASK_TYPE} prompts per task type with real memory-retrieval hits ...")
    test_set = select_stratified_prompts_with_real_memory_hits(candidates, N_PER_TASK_TYPE)
    print(f"  selected {len(test_set)} total")

    with open(TEST_SET_PATH, "w") as f:
        json.dump(test_set, f, indent=2)

    if not test_set:
        print("No eligible prompts found -- nothing to run. Exiting.")
        return

    results = []
    noise_floor = []

    for i, item in enumerate(test_set):
        msg = item["prompt"]
        try:
            print(f"[{i+1}/{len(test_set)}] control run (task_type={item['task_type']}) ...")
            control = _base.run_once(msg, ablate=False)
            print(f"    control done in {control['elapsed_s']}s, memory_present={control['memory_block_present']}")

            print(f"[{i+1}/{len(test_set)}] ablation run ...")
            ablation = _base.run_once(msg, ablate=True)
            print(f"    ablation done in {ablation['elapsed_s']}s, memory_present={ablation['memory_block_present']}")

            dist, cos_sim = _base.embedding_distance(control["response"], ablation["response"])
            q_control = _base.quality_score(control["response"], control["task_type"])
            q_ablation = _base.quality_score(ablation["response"], ablation["task_type"])

            pair_result = {
                "index": i,
                "prompt_meta": item,
                "control": control,
                "ablation": ablation,
                "embedding_distance": dist,
                "cosine_similarity": cos_sim,
                "quality_control": q_control,
                "quality_ablation": q_ablation,
                "quality_delta": (q_ablation - q_control) if (q_control is not None and q_ablation is not None) else None,
            }
            results.append(pair_result)
            print(f"    distance={dist:.4f} quality_delta={pair_result['quality_delta']}")
        except Exception as ex:
            print(f"  [ERROR] pair {i} failed, skipping: {ex}")
            traceback.print_exc()
        finally:
            save_progress(results, noise_floor)

    for i, item in enumerate(test_set[:N_NOISE_FLOOR]):
        msg = item["prompt"]
        try:
            print(f"[noise {i+1}/{N_NOISE_FLOOR}] repeat-control run A (task_type={item['task_type']}) ...")
            run_a = _base.run_once(msg, ablate=False)
            print(f"[noise {i+1}/{N_NOISE_FLOOR}] repeat-control run B ...")
            run_b = _base.run_once(msg, ablate=False)
            dist, cos_sim = _base.embedding_distance(run_a["response"], run_b["response"])
            noise_floor.append({
                "index": i, "prompt_meta": item, "run_a": run_a, "run_b": run_b,
                "embedding_distance": dist, "cosine_similarity": cos_sim,
            })
            print(f"    noise-floor distance={dist:.4f}")
        except Exception as ex:
            print(f"  [ERROR] noise-floor pair {i} failed, skipping: {ex}")
            traceback.print_exc()
        finally:
            save_progress(results, noise_floor)

    log_lines_after = sum(1 for _ in open(LOG_PATH))
    print(f"\nDone. interaction_log.jsonl grew by {log_lines_after - log_lines_before} lines "
          f"(all tagged source={SOURCE_TAG!r}).")
    print(f"river_brain.pkl backup at {BACKUP_PATH} (learn/save were neutralized -- should be unchanged)")
    print(f"Results: {RESULTS_PATH}")
    print(f"Test set: {TEST_SET_PATH}")


if __name__ == "__main__":
    main()
