#!/usr/bin/env python3
"""
Orchestrates the minimal validated-procedure-transfer pilot.
Standalone: imports nothing from app.* outside this experiment's own
sibling modules (tasks.py, sandbox.py, ollama_client.py). All output is
written under memory/experiments/minimal_procedure_transfer/ -- a fresh
path with no production reader anywhere in the codebase.

Usage:
  python3 -I -B app/experiments/minimal_procedure_transfer/run.py seal
  python3 -I -B app/experiments/minimal_procedure_transfer/run.py baseline
  python3 -I -B app/experiments/minimal_procedure_transfer/run.py experience
  python3 -I -B app/experiments/minimal_procedure_transfer/run.py heldout
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tasks as T
import sandbox as SB
import ollama_client as OC

OUT_DIR = Path(__file__).resolve().parents[3] / "memory" / "experiments" / "minimal_procedure_transfer"

BASELINE_SEEDS = list(range(3000, 3005))   # 5 instances
TRAIN_SEEDS = list(range(1000, 1006))      # 6 instances
HELDOUT_SEEDS = list(range(2000, 2008))    # 8 instances
N_INTERVALS = 5
N_HIDDEN_TESTS = 3

GENERIC_TIP_CONTEXT = (
    "\nGeneral tips (for reference):\n"
    "- Read the problem statement carefully before writing any code.\n"
    "- Consider edge cases, such as an empty input list.\n"
    "- Mentally trace your solution against the given example before finalizing it.\n"
    "- Keep your code clean, simple, and correct.\n"
)


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    tmp.replace(path)


def _append_jsonl(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def cmd_seal():
    """PHASE 3: generate the complete task set BEFORE any teaching, commit
    the held-out set's hash, write baseline/train/heldout task files."""
    if (OUT_DIR / "heldout_commitment.sha256").exists():
        print("Held-out set already sealed -- refusing to regenerate (would defeat sealing). "
              "Delete the experiment output dir by hand first if a genuine re-seal is intended.")
        return

    baseline_tasks = T.build_task_set(BASELINE_SEEDS, "baseline", N_INTERVALS, N_HIDDEN_TESTS)
    train_tasks = T.build_task_set(TRAIN_SEEDS, "train", N_INTERVALS, N_HIDDEN_TESTS)
    heldout_tasks = T.build_task_set(HELDOUT_SEEDS, "heldout", N_INTERVALS, N_HIDDEN_TESTS)

    _write_json(OUT_DIR / "baseline_tasks.json", baseline_tasks)
    _write_json(OUT_DIR / "train_tasks.json", train_tasks)
    _write_json(OUT_DIR / "heldout_tasks.json", heldout_tasks)

    commitment = T.sha256_of(heldout_tasks)
    with open(OUT_DIR / "heldout_commitment.sha256", "w") as f:
        f.write(commitment + "\n")

    print(f"Sealed. baseline={len(baseline_tasks)} train={len(train_tasks)} heldout={len(heldout_tasks)}")
    print(f"heldout_commitment.sha256 = {commitment}")


def _verify_heldout_unchanged():
    with open(OUT_DIR / "heldout_commitment.sha256") as f:
        committed = f.read().strip()
    with open(OUT_DIR / "heldout_tasks.json") as f:
        current = json.load(f)
    live = T.sha256_of(current)
    if live != committed:
        raise SystemExit(f"HELD-OUT SET INTEGRITY FAILURE: committed={committed} live={live}")
    return current


def cmd_baseline():
    """PHASE 4: measure baseline performance, one fresh attempt per
    instance, zero context, before any teaching exists."""
    with open(OUT_DIR / "baseline_tasks.json") as f:
        baseline_tasks = json.load(f)

    log_path = OUT_DIR / "baseline_results.jsonl"
    if log_path.exists():
        print("baseline_results.jsonl already exists -- not overwriting. Delete by hand to re-run.")
        return

    n_pass = 0
    for task in baseline_tasks:
        prompt = OC.build_user_prompt(task, "")
        t0 = time.time()
        resp = OC.generate(prompt)
        latency = time.time() - t0
        code = SB.extract_code(resp.get("content", ""))
        grade = SB.run_candidate(code, task["hidden_tests"])
        record = {
            "task_id": task["task_id"], "seed": task["seed"],
            "raw_response": resp.get("content", ""), "error": resp.get("error"),
            "done_reason": resp.get("done_reason"), "latency_s": round(latency, 2),
            "extracted_code": code, "grade": grade,
        }
        _append_jsonl(log_path, record)
        n_pass += 1 if grade["passed"] else 0
        print(f"[baseline] {task['task_id']}: passed={grade['passed']} category={grade.get('category')} "
              f"latency={latency:.1f}s")

    print(f"Baseline pass rate: {n_pass}/{len(baseline_tasks)}")


def cmd_experience():
    """PHASE 5: the model attempts each TRAIN instance fresh; on failure,
    ONE retry is issued with the real, mechanically-generated F2 failure
    feedback appended -- no human/Claude hint, no general knowledge, only
    the actual observed execution outcome. Every attempt (both the first
    try and any retry) is logged in full for later procedure-extraction
    provenance."""
    with open(OUT_DIR / "train_tasks.json") as f:
        train_tasks = json.load(f)

    log_path = OUT_DIR / "experience_log.jsonl"
    if log_path.exists():
        print("experience_log.jsonl already exists -- not overwriting. Delete by hand to re-run.")
        return

    for task in train_tasks:
        # Attempt 1: fresh, no context, no history.
        prompt1 = OC.build_user_prompt(task, "")
        t0 = time.time()
        resp1 = OC.generate(prompt1)
        lat1 = time.time() - t0
        code1 = SB.extract_code(resp1.get("content", ""))
        grade1 = SB.run_candidate(code1, task["hidden_tests"])
        episode = {
            "task_id": task["task_id"], "seed": task["seed"],
            "attempt_1": {
                "prompt": prompt1, "raw_response": resp1.get("content", ""),
                "error": resp1.get("error"), "latency_s": round(lat1, 2),
                "extracted_code": code1, "grade": grade1,
            },
        }
        print(f"[experience] {task['task_id']} attempt_1: passed={grade1['passed']} "
              f"category={grade1.get('category')} latency={lat1:.1f}s")

        if not grade1["passed"]:
            feedback = SB.format_failure_feedback(grade1)
            retry_context = (
                f"\nYour previous attempt was:\n```python\n{code1 or '(no code found)'}\n```\n"
                f"That attempt failed with real feedback from actually running it:\n{feedback}\n"
                f"Fix the function and write the corrected `solve` now.\n"
            )
            prompt2 = OC.build_user_prompt(task, retry_context)
            t0 = time.time()
            resp2 = OC.generate(prompt2)
            lat2 = time.time() - t0
            code2 = SB.extract_code(resp2.get("content", ""))
            grade2 = SB.run_candidate(code2, task["hidden_tests"])
            episode["attempt_2_retry"] = {
                "prompt": prompt2, "raw_response": resp2.get("content", ""),
                "error": resp2.get("error"), "latency_s": round(lat2, 2),
                "extracted_code": code2, "grade": grade2,
                "real_f2_feedback_supplied": feedback,
            }
            print(f"[experience] {task['task_id']} attempt_2_retry: passed={grade2['passed']} "
                  f"category={grade2.get('category')} latency={lat2:.1f}s")

        _append_jsonl(log_path, episode)


def cmd_heldout(arms: "list[str]"):
    """PHASE 10: run every held-out task under every requested arm, using
    the SAME held-out instances for every arm (paired design). The frozen
    procedure (if the P arm is requested) is loaded from
    procedure_frozen.json, whose hash must match procedure_hash.txt --
    refuses to run if the procedure was edited after freezing."""
    heldout_tasks = _verify_heldout_unchanged()

    context_by_arm = {"Z": ""}
    if "G" in arms:
        context_by_arm["G"] = GENERIC_TIP_CONTEXT
    if "P" in arms:
        with open(OUT_DIR / "procedure_frozen.json") as f:
            frozen = json.load(f)
        with open(OUT_DIR / "procedure_hash.txt") as f:
            committed_hash = f.read().strip()
        live_hash = T.sha256_of(frozen)
        if live_hash != committed_hash:
            raise SystemExit(f"PROCEDURE INTEGRITY FAILURE: committed={committed_hash} live={live_hash}")
        context_by_arm["P"] = "\nWorked procedure from prior validated experience:\n" + frozen["procedure_text"] + "\n"

    log_path = OUT_DIR / "heldout_results.jsonl"

    for task in heldout_tasks:
        for arm in arms:
            context = context_by_arm[arm]
            prompt = OC.build_user_prompt(task, context)
            t0 = time.time()
            resp = OC.generate(prompt)
            latency = time.time() - t0
            code = SB.extract_code(resp.get("content", ""))
            grade = SB.run_candidate(code, task["hidden_tests"])
            record = {
                "task_id": task["task_id"], "seed": task["seed"], "arm": arm,
                "raw_response": resp.get("content", ""), "error": resp.get("error"),
                "done_reason": resp.get("done_reason"), "latency_s": round(latency, 2),
                "extracted_code": code, "grade": grade,
            }
            _append_jsonl(log_path, record)
            print(f"[heldout] {task['task_id']} arm={arm}: passed={grade['passed']} "
                  f"category={grade.get('category')} latency={latency:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["seal", "baseline", "experience", "heldout"])
    parser.add_argument("--arms", default="P,Z,G")
    args = parser.parse_args()
    if args.phase == "seal":
        cmd_seal()
    elif args.phase == "baseline":
        cmd_baseline()
    elif args.phase == "experience":
        cmd_experience()
    elif args.phase == "heldout":
        cmd_heldout(args.arms.split(","))
