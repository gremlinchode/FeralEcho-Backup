#!/usr/bin/env python3
"""
Orchestrates the frozen validated-experience-competence-transfer
experiment, per CONTRACT.md. Standalone: imports only this experiment's
own sibling modules plus the already-verified, FeralEcho-import-free
sandbox.py/ollama_client.py from minimal_procedure_transfer, and
build_calibration_set from historical_difficulty_calibration/tasks.py
(unmodified).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import prompt as P

sys.path.insert(0, str(_HERE.parents[0] / "historical_difficulty_calibration"))
import tasks as T  # extract_code family, bound before any other same-named module

sys.path.insert(0, str(_HERE.parents[0] / "minimal_procedure_transfer"))
import sandbox as SB
import ollama_client as OC

OUT_DIR = _HERE.parents[2] / "memory" / "experiments" / "validated_experience_competence_transfer"
# NOTE (found and fixed live, 2026-09-24): the first version of this line used
# .parents[3], one level too many given _HERE is already resolved to run.py's
# CONTAINING DIRECTORY (app/experiments/validated_experience_competence_transfer),
# not to run.py itself. .parents[3] from there resolves one directory ABOVE the
# repository root. This was caught after the real `seal` and `experience` runs
# had already written their output to /Users/richietate/Desktop/memory/... --
# outside the FeralEcho repo entirely, though never touching any FeralEcho
# production path. The real files were moved into this corrected path
# (byte-for-byte, verified via the held-out commitment hash re-matching after
# the move) rather than regenerated, since the real seal/experience data itself
# was valid -- only its write location was wrong. See the final report's own
# state-integrity section for the full disclosure.

LEVEL = 3
TRAIN_SEEDS = list(range(1000, 1008))     # 8 instances
HELDOUT_SEEDS = list(range(1100, 1110))   # 10 instances
_ALL_PRIOR_SEEDS = set(
    list(range(700, 705)) + list(range(800, 805)) + list(range(810, 815)) +
    list(range(820, 825)) + list(range(830, 835)) + list(range(840, 845)) +
    list(range(850, 855))
)

OC.MODEL = "qwen2.5-coder:7b"


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
    """PHASE 2: generate TRAIN + HELD-OUT, seed-disjointness check, commit
    the held-out set's hash BEFORE any teaching."""
    if (OUT_DIR / "heldout_commitment.sha256").exists():
        print("Already sealed -- refusing to regenerate. Delete the output dir by "
              "hand first for a genuine re-seal.")
        return

    train_set = set(TRAIN_SEEDS)
    heldout_set = set(HELDOUT_SEEDS)
    overlap_prior = (train_set | heldout_set) & _ALL_PRIOR_SEEDS
    overlap_internal = train_set & heldout_set
    if overlap_prior or overlap_internal:
        raise SystemExit(
            f"APPARATUS FAILURE: seed overlap detected. prior={overlap_prior} "
            f"internal={overlap_internal}"
        )

    train_tasks = T.build_calibration_set(TRAIN_SEEDS, LEVEL, "train_")
    heldout_tasks = T.build_calibration_set(HELDOUT_SEEDS, LEVEL, "heldout_")

    _write_json(OUT_DIR / "train_tasks.json", train_tasks)
    _write_json(OUT_DIR / "heldout_tasks.json", heldout_tasks)

    commitment = T.sha256_of(heldout_tasks)
    with open(OUT_DIR / "heldout_commitment.sha256", "w") as f:
        f.write(commitment + "\n")

    print(f"Sealed. train={len(train_tasks)} heldout={len(heldout_tasks)}")
    print(f"heldout_commitment.sha256 = {commitment}")
    print("Seed disjointness verified: no overlap with any calibration/evaluator-"
          "qualification seed, and TRAIN/HELD-OUT are mutually disjoint.")


def _verify_heldout_unchanged():
    with open(OUT_DIR / "heldout_commitment.sha256") as f:
        committed = f.read().strip()
    with open(OUT_DIR / "heldout_tasks.json") as f:
        current = json.load(f)
    live = T.sha256_of(current)
    if live != committed:
        raise SystemExit(f"APPARATUS FAILURE -- HELD-OUT INTEGRITY: committed={committed} live={live}")
    return current


def cmd_experience():
    """PHASE 4: TRAIN episodes -- one attempt, one retry-with-real-F2-feedback
    on failure, per instance. Never touches HELD-OUT."""
    with open(OUT_DIR / "train_tasks.json") as f:
        train_tasks = json.load(f)

    log_path = OUT_DIR / "experience_log.jsonl"
    if log_path.exists():
        print("experience_log.jsonl already exists -- not overwriting.")
        return

    for task in train_tasks:
        prompt1 = P.build_prompt(task, context="")
        t0 = time.time()
        resp1 = OC.generate(prompt1, timeout_s=90)
        lat1 = time.time() - t0
        code1 = SB.extract_code(resp1.get("content", ""))
        hidden = [{"input": task["text"], "expected": task["expected_code"]}]
        grade1 = SB.run_candidate(code1, hidden)
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
            prompt2 = P.build_prompt(task, context=retry_context)
            t0 = time.time()
            resp2 = OC.generate(prompt2, timeout_s=90)
            lat2 = time.time() - t0
            code2 = SB.extract_code(resp2.get("content", ""))
            grade2 = SB.run_candidate(code2, hidden)
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
    """PHASE 11: held-out test, same instances, every requested arm, no
    retries. Refuses to run if the frozen procedure's hash (for arm P) does
    not match, or if the held-out set was tampered with."""
    heldout_tasks = _verify_heldout_unchanged()

    context_by_arm = {"Z": ""}
    if "G" in arms:
        with open(OUT_DIR / "generic_tip_treatment.json") as f:
            g = json.load(f)
        context_by_arm["G"] = g["context_text"]
    if "P" in arms:
        with open(OUT_DIR / "procedure_frozen.json") as f:
            frozen = json.load(f)
        with open(OUT_DIR / "procedure_hash.txt") as f:
            committed_hash = f.read().strip()
        live_hash = T.sha256_of(frozen)
        if live_hash != committed_hash:
            raise SystemExit(f"APPARATUS FAILURE -- PROCEDURE INTEGRITY: committed={committed_hash} live={live_hash}")
        context_by_arm["P"] = frozen["context_text"]

    log_path = OUT_DIR / "heldout_results.jsonl"

    for task in heldout_tasks:
        for arm in arms:  # fixed order P, G, Z, declared in CONTRACT.md before any call
            context = context_by_arm[arm]
            prompt = P.build_prompt(task, context=context)
            t0 = time.time()
            resp = OC.generate(prompt, timeout_s=90)
            latency = time.time() - t0
            code = SB.extract_code(resp.get("content", ""))
            hidden = [{"input": task["text"], "expected": task["expected_code"]}]
            grade = SB.run_candidate(code, hidden)
            record = {
                "task_id": task["task_id"], "seed": task["seed"], "arm": arm,
                "raw_response": resp.get("content", ""), "error": resp.get("error"),
                "latency_s": round(latency, 2), "extracted_code": code, "grade": grade,
            }
            _append_jsonl(log_path, record)
            print(f"[heldout] {task['task_id']} arm={arm}: passed={grade['passed']} "
                  f"category={grade.get('category')} latency={latency:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["seal", "experience", "heldout"])
    parser.add_argument("--arms", default="P,G,Z")
    args = parser.parse_args()
    if args.phase == "seal":
        cmd_seal()
    elif args.phase == "experience":
        cmd_experience()
    elif args.phase == "heldout":
        cmd_heldout(args.arms.split(","))
