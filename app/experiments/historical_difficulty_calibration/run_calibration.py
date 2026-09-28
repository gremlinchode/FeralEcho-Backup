#!/usr/bin/env python3
"""
PHASE 6/7 -- zero-teaching baseline across the pre-declared 4-level
"extract_code" calibration ladder. CALIBRATION ONLY: no TRAIN/HELD-OUT
sets are created here, no procedure is derived, no retries are issued.
One fresh, single-turn, temperature-0 attempt per instance.

Reuses ollama_client.py unmodified from the sibling minimal_procedure_
transfer package (already verified safe -- no FeralEcho imports at all).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tasks as T  # local extract_code family -- bound before the sibling
                    # package's own same-named tasks.py enters sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "minimal_procedure_transfer"))
import sandbox as SB
import ollama_client as OC

OUT_DIR = Path(__file__).resolve().parents[3] / "memory" / "experiments" / "historical_difficulty_calibration"

# Calibration-only seed ranges. Deliberately distinct from any range that
# would later be used for a sealed TRAIN or HELD-OUT set in a follow-on
# transfer experiment, and never reused across this run.
SEEDS_BY_LEVEL = {
    1: list(range(800, 805)),
    2: list(range(810, 815)),
    3: list(range(820, 825)),
    4: list(range(830, 835)),
}

SYSTEM_PROMPT_OVERRIDE = (
    "You are a careful Python programmer. Respond with exactly one fenced "
    "Python code block that defines the function `solve` as specified. "
    "Do not include explanations, tests, or example calls outside the "
    "code block."
)


_EXAMPLE_TEXT = "Sure, here's what I came up with!\n\ndef add(a, b):\n    return a + b"
_EXAMPLE_OUTPUT = "def add(a, b):\n    return a + b"


def build_prompt(task: dict) -> str:
    return (
        f"Task:\n{task['description']}\n\n"
        f"You must write a general-purpose function with this exact signature:\n"
        f"def solve(text: str) -> str\n\n"
        f"`solve` will be called by an automated test harness on DIFFERENT input "
        f"strings it has never seen before -- it must work by actually inspecting "
        f"its `text` argument at runtime (for example, by parsing or searching it), "
        f"not by returning a fixed value copied from any example.\n\n"
        f"Example (illustrative only, not one of the real graded inputs):\n"
        f"If `text` were exactly:\n"
        f"-----BEGIN EXAMPLE INPUT-----\n{_EXAMPLE_TEXT}\n-----END EXAMPLE INPUT-----\n"
        f"then solve(text) should return exactly:\n"
        f"-----BEGIN EXAMPLE OUTPUT-----\n{_EXAMPLE_OUTPUT}\n-----END EXAMPLE OUTPUT-----\n\n"
        f"Now here is the REAL input string that `solve` will actually be tested "
        f"on for this task (between the markers below -- it is not the example "
        f"above):\n"
        f"-----BEGIN REAL INPUT-----\n{task['text']}\n-----END REAL INPUT-----\n\n"
        f"Write the function `solve` now. Respond with only the function "
        f"definition in a fenced Python code block."
    )


def classify_failure(grade: dict, raw_response: str) -> str:
    cat = grade.get("category")
    if grade["passed"]:
        return "pass"
    if cat == "malformed_no_code_block":
        return "FORMAT_FAILURE"
    if cat in ("timeout", "subprocess_launch_failed", "no_output_produced"):
        return "EXECUTION_FAILURE"
    if cat == "runtime_error":
        return "EXECUTION_FAILURE"
    if cat == "wrong_output":
        return "LOGIC_SEMANTIC_FAILURE"
    return "OTHER"


def run_model(model_name: str) -> dict:
    OC.MODEL = model_name
    summary = {}
    log_path = OUT_DIR / f"calibration_results_{model_name.replace(':', '_')}.jsonl"
    if log_path.exists():
        print(f"{log_path} already exists -- not overwriting. Delete by hand to re-run.")
        return {}

    for level in (1, 2, 3, 4):
        seeds = SEEDS_BY_LEVEL[level]
        tasks_at_level = T.build_calibration_set(seeds, level, "calib_")
        n_pass = 0
        n_by_class = {}
        for task in tasks_at_level:
            prompt = build_prompt(task)
            t0 = time.time()
            resp = OC.generate(prompt, timeout_s=90)
            latency = time.time() - t0
            code = SB.extract_code(resp.get("content", ""))
            hidden = [{"input": task["text"], "expected": task["expected_code"]}]
            grade = SB.run_candidate(code, hidden)
            failure_class = classify_failure(grade, resp.get("content", ""))
            record = {
                "model": model_name, "task_id": task["task_id"], "level": level,
                "seed": task["seed"], "raw_response": resp.get("content", ""),
                "error": resp.get("error"), "latency_s": round(latency, 2),
                "extracted_code": code, "grade": grade, "failure_class": failure_class,
            }
            with open(log_path, "a") as f:
                f.write(json.dumps(record) + "\n")
            n_pass += 1 if grade["passed"] else 0
            n_by_class[failure_class] = n_by_class.get(failure_class, 0) + 1
            print(f"[{model_name}] level={level} {task['task_id']}: "
                  f"passed={grade['passed']} class={failure_class} latency={latency:.1f}s")
        summary[level] = {"n": len(tasks_at_level), "n_pass": n_pass, "by_class": n_by_class}
    return summary


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-coder:7b"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = run_model(model)
    print(json.dumps(summary, indent=2))
