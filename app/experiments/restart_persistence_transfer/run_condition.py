#!/usr/bin/env python3
"""
PROTOCOL.md Sections 3-4 -- runs exactly one of R+ or R- as a genuinely
fresh, standalone OS process. Each invocation of this script (via
`python3 run_condition.py --condition=...`) is its own new Python
interpreter with no state shared with any other invocation, the VECT
process(es) that created P, or the investigating session. Imports only
VECT's own unmodified prompt.py (for the qualified prompt shape) and
minimal_procedure_transfer's unmodified sandbox.py/ollama_client.py (for
the qualified execution/grading and Ollama call shape) -- the same reuse
pattern VECT's own run.py already established. Never imports or executes
anything from validated_experience_competence_transfer/run.py itself.

R+ reads and hash-verifies procedure_frozen.json from disk at runtime.
R- never references that file anywhere in this module -- verifiable by
reading this source directly.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[0] / "validated_experience_competence_transfer"))
import prompt as P  # noqa: E402 -- VECT's own unmodified prompt.py

sys.path.insert(0, str(_HERE.parents[0] / "historical_difficulty_calibration"))
import tasks as T  # noqa: E402 -- for T.sha256_of only

sys.path.insert(0, str(_HERE.parents[0] / "minimal_procedure_transfer"))
import sandbox as SB  # noqa: E402
import ollama_client as OC  # noqa: E402

OC.MODEL = "qwen2.5-coder:7b"

OUT_DIR = _HERE.parents[2] / "memory" / "experiments" / "restart_persistence_transfer"
VECT_DIR = _HERE.parents[2] / "memory" / "experiments" / "validated_experience_competence_transfer"


def _append_jsonl(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def _load_heldout_tasks() -> "list[dict]":
    with open(OUT_DIR / "restart_heldout_commitment.sha256") as f:
        committed = f.read().strip()
    with open(OUT_DIR / "restart_heldout_tasks.json") as f:
        current = json.load(f)
    live = T.sha256_of(current)
    if live != committed:
        raise SystemExit(
            f"APPARATUS FAILURE -- RESTART HELD-OUT INTEGRITY: committed={committed} live={live}"
        )
    return current


def _get_r_plus_context() -> str:
    """R+ only. Reads procedure_hash.txt, independently recomputes the hash
    of procedure_frozen.json, and STOPS immediately on any mismatch. Never
    proceeds past a hash mismatch, per PROTOCOL.md Section 4 step 2."""
    with open(VECT_DIR / "procedure_frozen.json") as f:
        frozen = json.load(f)
    with open(VECT_DIR / "procedure_hash.txt") as f:
        committed_hash = f.read().strip()
    live_hash = T.sha256_of(frozen)
    if live_hash != committed_hash:
        raise SystemExit(
            f"ABORT PER PROTOCOL -- P HASH MISMATCH: committed={committed_hash} "
            f"live={live_hash}. STOP. Do not proceed."
        )
    print(f"[r_plus] P hash independently verified: {live_hash}")
    return frozen["context_text"]


def run(condition: str) -> None:
    pid = os.getpid()
    start_wall = time.time()
    start_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_wall))
    print(f"[{condition}] fresh process started: pid={pid} start={start_iso} "
          f"id(sys.modules)={id(sys.modules)}")

    if condition == "r_plus":
        context = _get_r_plus_context()
        result_path = OUT_DIR / "r_plus_results.jsonl"
    elif condition == "r_minus":
        # Deliberately never reads procedure_frozen.json anywhere in this
        # branch or anywhere else in this file (verifiable by grep).
        context = ""
        result_path = OUT_DIR / "r_minus_results.jsonl"
    else:
        raise SystemExit(f"unknown condition: {condition}")

    if result_path.exists():
        raise SystemExit(f"{result_path} already exists -- refusing to overwrite. "
                          f"Delete it by hand first for a genuine re-run.")

    heldout_tasks = _load_heldout_tasks()

    for task in heldout_tasks:
        prompt_text = P.build_prompt(task, context=context)
        t0 = time.time()
        resp = OC.generate(prompt_text, timeout_s=90)
        latency = time.time() - t0
        code = SB.extract_code(resp.get("content", ""))
        hidden = [{"input": task["text"], "expected": task["expected_code"]}]
        grade = SB.run_candidate(code, hidden)
        record = {
            "task_id": task["task_id"], "seed": task["seed"], "condition": condition,
            "prompt": prompt_text, "raw_response": resp.get("content", ""),
            "error": resp.get("error"), "latency_s": round(latency, 2),
            "extracted_code": code, "grade": grade,
        }
        _append_jsonl(result_path, record)
        print(f"[{condition}] {task['task_id']}: passed={grade['passed']} "
              f"category={grade.get('category')} latency={latency:.1f}s")

    end_wall = time.time()
    end_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_wall))
    evidence = {
        "condition": condition, "pid": pid,
        "start_iso": start_iso, "end_iso": end_iso,
        "duration_s": round(end_wall - start_wall, 2),
        "argv": sys.argv, "executable": sys.executable,
    }
    _append_jsonl(OUT_DIR / "process_evidence.jsonl", evidence)
    print(f"[{condition}] DONE. pid={pid} duration={evidence['duration_s']}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", required=True, choices=["r_plus", "r_minus"])
    args = parser.parse_args()
    run(args.condition)
