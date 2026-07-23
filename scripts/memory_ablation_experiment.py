#!/usr/bin/env python3
"""Memory retrieval ablation experiment (2026-07-23).

Measures whether FAISS-retrieved memory context
(app.core.memory_bridge.retrieve_relevant_memories) has a measurable effect
on real LLM output, beyond the two confirmed scheduling gates
(emergent_scheduler repeat-avoidance, curiosity_engine match-reuse)
established in audits/2026-07-23_systems_physiology_audit.md Part 7.

Method: reuses the real, unmodified production pipeline --
app.routes_echo_studio._build_full_prompt() + app.core.echo_model_orchestrator
.echo_query() -- exactly what /chat/stream (mode: full) calls. Ablation is a
pure in-process monkeypatch of memory_bridge.retrieve_relevant_memories -> []
for the duration of one call; no source file is edited.

Side-effect handling (checked before writing this script, not assumed):
  - echo_query() never commits to FAISS vector memory on this path (that only
    happens via run.py's /mirror_echo route and emergent_scheduler.py's
    autonomous loop -- confirmed by grep, not this script).
  - echo_query() DOES unconditionally call RiverBrain.learn()/.save() on
    every real generation. That's irrelevant to what this experiment measures
    (LLM output content, not training), so RiverBrain's learn/save are
    monkeypatched to no-ops for this script's whole process lifetime --
    production river_brain.pkl is never touched. A backup is still taken as
    defense-in-depth.
  - interaction_log.jsonl DOES gain one real line per generation (unavoidable
    -- it's the shared flat journal, not gated). Tagged
    source="memory_ablation_experiment" (distinct from "user_conversation")
    so it stays forensically distinguishable and is excluded from the
    task-type-classifier online-learning hook and the user-rating attribution
    path, both of which are gated on source=="user_conversation" exactly
    (echo_model_orchestrator.py:236,333).
"""
import os

# Must precede any faiss/numpy/torch import -- mirrors run.py's own startup
# guard (CLAUDE.md "OpenMP / KMP startup guard" section).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import sys
import json
import shutil
import random
import time
import traceback
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

_STAMP = datetime.now().strftime("%Y%m%dT%H%M%SZ")
RESULTS_PATH = ROOT / "scripts" / "memory_ablation_results_2026-07-23.json"
TEST_SET_PATH = ROOT / "scripts" / "memory_ablation_test_set_2026-07-23.json"
LOG_PATH = ROOT / "memory" / "interaction_log.jsonl"
RIVER_BRAIN_PATH = ROOT / "memory" / "river_brain.pkl"
BACKUP_PATH = ROOT / "memory" / f"river_brain.pkl.pre_ablation_backup_{_STAMP}"

N_PROMPTS = 30
N_NOISE_FLOOR = 5
MAX_PROMPT_CHARS = 2000  # exclude giant self-edit meta-prompts
SOURCE_TAG = "memory_ablation_experiment"


def neutralize_river_brain_writes():
    """No-op RiverBrain.learn()/.save() for this process only -- production
    river_brain.pkl must never be touched by a measurement script. Read-side
    methods (score_model, influence_weight, etc.) are untouched.

    Patched at the CLASS level, not on one instance grabbed via
    get_river_brain() -- a smoke test found that patching only the singleton
    instance this script happened to load did NOT intercept the real
    .save() call inside echo_query()'s own code path (the real .save() still
    ran and printed its own internal staleness-guard warning, "Save skipped
    -- disk has more obs than instance, refusing to overwrite richer pkl" --
    reassuring evidence that guard is real and already protects against
    multi-process clobbering, but not something to rely on incidentally).
    Patching RiverBrain.learn/.save at the class level guarantees every
    instance, however it's obtained, uses the no-op."""
    from app.core.echo_model_orchestrator import RiverBrain
    RiverBrain.learn = lambda self, *a, **kw: None
    RiverBrain.save = lambda self, *a, **kw: None
    # .save() only enqueues onto a background writer thread that calls the
    # real ._do_save() on its own periodic timer, independent of .save()
    # itself -- confirmed live: patching .save() alone still left repeated
    # real "[RIVER] Save skipped -- disk has more obs, refusing to overwrite"
    # warnings firing from that thread. Harmless either way (with .learn()
    # neutralized, the in-memory snapshot never changes, and the pre-existing
    # richer-pkl guard was blocking every one of those writes regardless) --
    # patched directly too so there is no ambiguity and the logs stay quiet.
    RiverBrain._do_save = lambda self, *a, **kw: None
    print(f"[{datetime.now()}] RiverBrain.learn()/.save()/._do_save() neutralized at the class level for this process.")


def load_candidate_entries():
    """Real, recent, conversational-shaped interaction_log.jsonl entries."""
    entries = []
    with open(LOG_PATH) as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            prompt = e.get("prompt") or ""
            task_type = e.get("task_type", "")
            if not prompt or len(prompt) > MAX_PROMPT_CHARS:
                continue
            if task_type not in ("coding", "personal", "creative", "reasoning", "general"):
                continue
            if "self_edit_generated.py" in prompt or "FeralEcho importable modules" in prompt:
                continue
            entries.append(e)
    return entries


def select_prompts_with_real_memory_hits(candidates, n):
    """Call the real (unablated) retrieval pipeline against each candidate
    and keep only those where it actually returns a non-empty memory block --
    otherwise this experiment would just compare a prompt to itself."""
    from app.routes_echo_studio import _build_full_prompt

    random.shuffle(candidates)
    selected = []
    for e in candidates:
        if len(selected) >= n:
            break
        msg = e["prompt"]
        session = {"conv_history": [], "history_summaries": []}
        try:
            full_msg, system_context = _build_full_prompt(msg, session)
        except Exception as ex:
            print(f"  [skip] _build_full_prompt raised: {ex}")
            continue
        if "Retrieved context" in system_context:
            selected.append({
                "timestamp": e.get("timestamp"),
                "task_type": e.get("task_type"),
                "original_model": e.get("model"),
                "original_quality_score": e.get("quality_score"),
                "prompt": msg,
                "control_system_context_preview": system_context[:300],
            })
            print(f"  [hit {len(selected)}/{n}] task_type={e.get('task_type')} ts={e.get('timestamp')}")
    return selected


def run_once(msg, ablate: bool):
    """One real generation through the exact production pipeline."""
    from app.routes_echo_studio import _build_full_prompt, _resolve_task_type
    from app.core.echo_model_orchestrator import echo_query

    session = {"conv_history": [], "history_summaries": []}

    if ablate:
        with patch("app.core.memory_bridge.retrieve_relevant_memories", return_value=[]):
            full_msg, system_context = _build_full_prompt(msg, session)
    else:
        full_msg, system_context = _build_full_prompt(msg, session)

    task_type = _resolve_task_type(msg)
    t0 = time.time()
    response = echo_query(
        full_msg, task_type=task_type, source=SOURCE_TAG, system=system_context,
    )
    elapsed = time.time() - t0
    return {
        "task_type": task_type,
        "system_context": system_context,
        "memory_block_present": "Retrieved context" in system_context,
        "response": response,
        "elapsed_s": round(elapsed, 2),
    }


def embedding_distance(text_a, text_b):
    from app.core.memory_bridge import embed_text
    import numpy as np
    vecs = embed_text([text_a, text_b])
    a, b = vecs[0], vecs[1]
    cos_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
    return 1.0 - cos_sim, cos_sim


def quality_score(text, task_type):
    from echo_quality_scorer import _score_response_quality
    try:
        return _score_response_quality(text, task_type)
    except Exception as ex:
        print(f"  [warn] quality scoring failed: {ex}")
        return None


def save_progress(results, noise_floor):
    with open(RESULTS_PATH, "w") as f:
        json.dump({"pairs": results, "noise_floor": noise_floor}, f, indent=2)


def main():
    print(f"[{datetime.now()}] Backing up river_brain.pkl -> {BACKUP_PATH.name} (defense-in-depth)")
    if RIVER_BRAIN_PATH.exists():
        shutil.copy2(RIVER_BRAIN_PATH, BACKUP_PATH)

    neutralize_river_brain_writes()

    log_lines_before = sum(1 for _ in open(LOG_PATH))

    print("Loading candidate entries from interaction_log.jsonl ...")
    candidates = load_candidate_entries()
    print(f"  {len(candidates)} candidate entries after filtering")

    print(f"Selecting {N_PROMPTS} prompts with real memory-retrieval hits ...")
    test_set = select_prompts_with_real_memory_hits(candidates, N_PROMPTS)
    print(f"  selected {len(test_set)}/{N_PROMPTS}")

    with open(TEST_SET_PATH, "w") as f:
        json.dump(test_set, f, indent=2)

    results = []
    noise_floor = []

    for i, item in enumerate(test_set):
        msg = item["prompt"]
        try:
            print(f"[{i+1}/{len(test_set)}] control run (task_type={item['task_type']}) ...")
            control = run_once(msg, ablate=False)
            print(f"    control done in {control['elapsed_s']}s, memory_present={control['memory_block_present']}")

            print(f"[{i+1}/{len(test_set)}] ablation run ...")
            ablation = run_once(msg, ablate=True)
            print(f"    ablation done in {ablation['elapsed_s']}s, memory_present={ablation['memory_block_present']}")

            dist, cos_sim = embedding_distance(control["response"], ablation["response"])
            q_control = quality_score(control["response"], control["task_type"])
            q_ablation = quality_score(ablation["response"], ablation["task_type"])

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

    # Noise-floor calibration: repeat CONTROL mode twice on a subset, to
    # measure pure sampling-noise distance independent of any ablation.
    for i, item in enumerate(test_set[:N_NOISE_FLOOR]):
        msg = item["prompt"]
        try:
            print(f"[noise {i+1}/{N_NOISE_FLOOR}] repeat-control run A ...")
            run_a = run_once(msg, ablate=False)
            print(f"[noise {i+1}/{N_NOISE_FLOOR}] repeat-control run B ...")
            run_b = run_once(msg, ablate=False)
            dist, cos_sim = embedding_distance(run_a["response"], run_b["response"])
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
