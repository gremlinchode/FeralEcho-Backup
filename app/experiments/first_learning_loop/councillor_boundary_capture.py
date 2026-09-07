#!/usr/bin/env python3
"""
Direct Councillor Boundary Trace — capture script.

Read-only forensic capture: monkeypatches river_deliberation._ollama_query
to record each councillor's real raw response as it is returned inside a
genuine deliberate_and_learn() call, without altering what that function
does with the value afterward. RiverBrain writes are neutralized (same
proven-safe pattern used by every prior experiment in this series tonight).
Does not touch river_deliberation.py's own source.
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
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

ARTIFACT_DIR = ROOT / "app/experiments/first_learning_loop/councillor_boundary_artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    from app.core.echo_model_orchestrator import RiverBrain, get_river_brain, MODEL_POOL
    # Neutralize RiverBrain writes -- identical pattern to
    # scripts/memory_ablation_experiment.py's neutralize_river_brain_writes(),
    # applied at the class level so every instance is covered.
    RiverBrain.learn = lambda self, *a, **kw: None
    RiverBrain.save = lambda self, *a, **kw: None
    print(f"[{datetime.now(timezone.utc).isoformat()}] RiverBrain.learn/.save neutralized at class level.")

    import app.core.river_deliberation as rd

    real_ollama_query = rd._ollama_query
    captures = []

    def capturing_ollama_query(model, prompt, *args, **kwargs):
        t0 = time.time()
        raw = real_ollama_query(model, prompt, *args, **kwargs)
        t1 = time.time()
        entry = {
            "call_index": len(captures),
            "model": model,
            "prompt_sha256": sha256(prompt),
            "prompt_length": len(prompt),
            "kwargs": {k: v for k, v in kwargs.items() if k in ("temperature", "timeout", "max_tokens", "task_type")},
            "timestamp_start": datetime.fromtimestamp(t0, tz=timezone.utc).isoformat(),
            "timestamp_end": datetime.fromtimestamp(t1, tz=timezone.utc).isoformat(),
            "elapsed_s": round(t1 - t0, 3),
            "raw_response": raw,
            "raw_response_sha256": sha256(raw or ""),
            "raw_response_length": len(raw or ""),
        }
        captures.append(entry)
        # Persist each capture immediately and individually -- unique filename,
        # never overwrites a prior pass's artifacts.
        fname = ARTIFACT_DIR / f"{STAMP}_call{entry['call_index']}_{model.replace(':', '_')}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(entry, f, indent=2)
        print(f"  [capture] call #{entry['call_index']} model={model} "
              f"sha256={entry['raw_response_sha256'][:16]} len={entry['raw_response_length']} "
              f"elapsed={entry['elapsed_s']}s -> {fname.name}")
        return raw

    rd._ollama_query = capturing_ollama_query

    # A fresh, novel, contamination-free coding prompt -- not reused from any
    # prior experiment in this series.
    prompt = (
        "Write a small Python function `merge_sorted_lists(a, b)` that takes "
        "two already-sorted lists of integers and returns a single sorted "
        "list containing all elements from both, without using the built-in "
        "sorted() function."
    )

    print(f"[{datetime.now(timezone.utc).isoformat()}] Calling real deliberate_and_learn() ...")
    t_start = time.time()
    final_response = rd.deliberate_and_learn(
        prompt=prompt,
        task_type="coding",
        river_brain=get_river_brain(),
        model_pool=MODEL_POOL,
        max_tokens=512,
    )
    t_end = time.time()
    print(f"[{datetime.now(timezone.utc).isoformat()}] deliberate_and_learn() returned in {round(t_end - t_start, 2)}s")

    final_entry = {
        "prompt": prompt,
        "prompt_sha256": sha256(prompt),
        "final_response": final_response,
        "final_response_sha256": sha256(final_response or ""),
        "final_response_length": len(final_response or ""),
        "elapsed_s": round(t_end - t_start, 3),
        "num_councillor_calls_captured": len(captures),
        "councillor_call_summary": [
            {"call_index": c["call_index"], "model": c["model"],
             "raw_response_sha256": c["raw_response_sha256"],
             "raw_response_length": c["raw_response_length"]}
            for c in captures
        ],
    }
    final_path = ARTIFACT_DIR / f"{STAMP}_final_response.json"
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(final_entry, f, indent=2)
    print(f"  [final] sha256={final_entry['final_response_sha256'][:16]} len={final_entry['final_response_length']} -> {final_path.name}")

    # Restore original function (harmless in this short-lived process, but
    # documented per the mission's own restoration-proof requirement).
    rd._ollama_query = real_ollama_query
    print("Restored original _ollama_query reference in this process.")

    print("\n=== SUMMARY ===")
    for c in captures:
        print(f"  call#{c['call_index']} model={c['model']} sha256={c['raw_response_sha256'][:16]} len={c['raw_response_length']}")
    hashes = [c["raw_response_sha256"] for c in captures]
    print(f"All distinct hashes: {len(set(hashes))} distinct out of {len(hashes)} calls")
    print(f"Final response sha256: {final_entry['final_response_sha256'][:16]}")


if __name__ == "__main__":
    main()
