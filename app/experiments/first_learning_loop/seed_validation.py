"""
Seed variation instrument validation (2026-09-06).

NOT a learning experiment. Tests only whether the real Ollama endpoint,
called with the same request shape ollama_handler.py uses, honors an
explicit `seed` option -- and whether that reaches into meaningful output
variation. ollama_handler.py's real /api/chat request construction
(_chat_ollama/_stream_chat_ollama, lines ~125-186) never sets a `seed`
key in `options` -- confirmed directly by source read before writing this
script. This script does NOT modify ollama_handler.py or any production
file; it is a standalone, isolated harness that builds the identical
request shape (same CHAT_URL, same options keys) plus one additional
key (`seed`) to test Q1/Q2 empirically rather than by inference.

Does not call RiverBrain, does not call echo_query(), does not touch
self_edit_generated.py, does not write to any production log/state file.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parents[3]
_OUT_DIR = Path(__file__).resolve().parent / "seed_validation_artifacts"
_OUT_DIR.mkdir(exist_ok=True)

CHAT_URL = "http://localhost:11434/api/chat"
MODEL = "echo:latest"
TEMPERATURE = 0.7

BASELINE_PROMPT = (
    "Write a short Python function that returns the nth Fibonacci number. "
    "Include a brief one-line comment above the return statement. "
    "Output only the function as a single code block."
)


def _call(prompt: str, seed: int) -> dict:
    options = {"num_ctx": 8192, "num_predict": 300, "temperature": TEMPERATURE, "seed": seed}
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": options,
    }
    t0 = time.time()
    resp = requests.post(CHAT_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    content = (data.get("message") or {}).get("content", "")
    elapsed = time.time() - t0
    return {
        "seed": seed,
        "model": MODEL,
        "temperature": TEMPERATURE,
        "prompt": prompt,
        "raw_response": content,
        "elapsed_s": round(elapsed, 2),
        "full_ollama_response_meta": {k: v for k, v in data.items() if k != "message"},
    }


def _persist(name: str, result: dict) -> "tuple[Path, str]":
    path = _OUT_DIR / f"{name}.json"
    text = json.dumps(result, indent=2, ensure_ascii=False)
    path.write_text(text)
    digest = hashlib.sha256(result["raw_response"].encode("utf-8")).hexdigest()
    return path, digest


def run_baseline():
    print("=== BASELINE SEED TEST (generic, non-FeralEcho prompt) ===")
    print(f"model={MODEL} temperature={TEMPERATURE}")
    results = {}
    for name, seed in (("seed_a_response", 4242), ("seed_b_response", 90210), ("seed_a_repeat_response", 4242)):
        print(f"-- generating {name} (seed={seed}) --")
        r = _call(BASELINE_PROMPT, seed)
        path, digest = _persist(name, r)
        print(f"   elapsed={r['elapsed_s']}s  sha256={digest}  path={path}")
        results[name] = {"result": r, "path": str(path), "sha256": digest}
    return results


def run_clean_task_seed_test():
    import sys
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from app.experiments.first_learning_loop.v1_2_clean_transfer import BASE_PROMPT

    print()
    print("=== CLEAN v1.2-TASK SEED TEST (same real task content, direct call w/ seed) ===")
    print("NOTE: this bypasses echo_query()'s full RiverBrain/council/synthesis chain --")
    print("that chain cannot accept a seed parameter without modifying production code,")
    print("which is out of scope. This tests whether the same real task PROMPT CONTENT")
    print("produces seed-dependent variation under a direct, single-model call -- a")
    print("narrower but still informative question than the full pipeline's behavior.")
    results = {}
    for name, seed in (("clean_control_seed_a", 4242), ("clean_control_seed_b", 90210)):
        print(f"-- generating {name} (seed={seed}) --")
        r = _call(BASE_PROMPT, seed)
        path, digest = _persist(name, r)
        print(f"   elapsed={r['elapsed_s']}s  sha256={digest}  path={path}")
        results[name] = {"result": r, "path": str(path), "sha256": digest}
    return results


if __name__ == "__main__":
    baseline = run_baseline()
    a_hash = baseline["seed_a_response"]["sha256"]
    b_hash = baseline["seed_b_response"]["sha256"]
    a_repeat_hash = baseline["seed_a_repeat_response"]["sha256"]
    print()
    print(f"SEED-A == SEED-B (baseline)?        {a_hash == b_hash}")
    print(f"SEED-A == SEED-A-REPEAT (baseline)? {a_hash == a_repeat_hash}")

    if a_hash != b_hash:
        clean = run_clean_task_seed_test()
        ca_hash = clean["clean_control_seed_a"]["sha256"]
        cb_hash = clean["clean_control_seed_b"]["sha256"]
        print()
        print(f"CLEAN-TASK SEED-A == SEED-B? {ca_hash == cb_hash}")
    else:
        print()
        print("Baseline seed test showed NO variation -- skipping clean-task test per")
        print("the mission's own sequencing (§5-11): establish baseline seed sensitivity")
        print("before testing the real task, not after a failed baseline.")
