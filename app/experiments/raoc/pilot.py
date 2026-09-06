"""
RAOC real-Echo pilot — Stage B of the protocol's own §16 Pilot Protocol
(added retroactively, closing the real gap this docstring used to flag
plainly: the document originally had no numbered pilot section the way
the P0.2 reference protocol's §17 does. See CLAUDE.md Finding 95 and
§16 of the protocol document for the full pilot design and success
criteria this module is required to satisfy.

Deliberately small and NOT the pre-registered §11 sample size (which
requires 20 trials per condition per pair, 240 total). Called with
min_pairs=3 below, this pilot runs exactly 1 real trial per condition
per real task pair (3 pairs x 4 conditions = 12 real _ollama_query()
calls) — enough to catch real implementation bugs (does a real Echo
response actually parse/verify correctly end-to-end) without collecting
anything resembling a statistically interpretable sample. NOTE: the
classifier broadening in Finding 95 means find_real_task_pairs() can
now return up to 6 real pairs, not 3 — this module was deliberately
left at min_pairs=3 rather than silently widened, since re-running the
pilot at the new scale is its own separately-gated next step (§16), not
assumed into this pilot's own completion.

RESULTS FROM THIS PILOT ARE NOT EVIDENCE FOR OR AGAINST H1. Logged to a
separate file (memory/raoc_pilot_trials.jsonl) from where real,
pre-registered trial data would go (memory/raoc_trials.jsonl), so pilot
runs can never be accidentally pooled into a real analysis.
"""
from __future__ import annotations

import glob
import json
import os

from app.experiments.raoc.harness import run_trial
from app.experiments.raoc.schema import RaocCondition
from app.experiments.raoc.task_pairs import find_real_task_pairs

_TASK_SUITE_GLOB = "audits/tier4_apparatus/tier4_stage*_task_suite.json"
_PILOT_LOG_PATH = os.path.join("memory", "raoc_pilot_trials.jsonl")
_PILOT_MODEL = "qwen2.5-coder:7b"  # same model the real Tier-4 corpus's own task pairs were generated/verified against


def _load_task_map() -> dict:
    task_map = {}
    for suite_path in glob.glob(_TASK_SUITE_GLOB):
        with open(suite_path, encoding="utf-8") as f:
            data = json.load(f)
        for task in data.get("tasks", []):
            task_map[task["task_id"]] = task
    return task_map


def _log_pilot_trial(trial, pair) -> None:
    os.makedirs(os.path.dirname(_PILOT_LOG_PATH), exist_ok=True)
    record = {
        "trial_id": trial.trial_id,
        "pair_id": trial.pair_id,
        "pair_category": pair.category,
        "outcome_task_id": pair.outcome.task_id,
        "target_task_id": pair.target_task_id,
        "outcome_approach": pair.outcome.approach.value,
        "outcome_passed": pair.outcome.passed,
        "condition": trial.condition.value,
        "injected_context": trial.injected_context,
        "raw_response": trial.raw_response,
        "candidate_code": trial.candidate_code,
        "passed": trial.passed,
        "classified_approach": trial.classified_approach.value,
        "matches_outcome_direction": trial.matches_outcome_direction,
        "model_used": trial.model_used,
        "trace_id": trial.trace_id,
    }
    with open(_PILOT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_pilot() -> list:
    """
    Runs exactly one real trial per condition per real task pair.
    Returns the list of (pair, condition, trial) tuples actually run.
    Every trial is logged to memory/raoc_pilot_trials.jsonl regardless of
    outcome — no selective discarding, matching this thread's own
    established discipline.
    """
    task_map = _load_task_map()
    pairs = find_real_task_pairs(min_pairs=3)
    if not pairs:
        raise RuntimeError("Pilot cannot proceed: no real task pairs found in the Tier-4 corpus.")

    results = []
    for pair in pairs:
        target = task_map.get(pair.target_task_id)
        if target is None:
            print(f"[RAOC-PILOT] Skipping pair {pair.pair_id}: target task {pair.target_task_id} not found in task suites.")
            continue
        for condition in RaocCondition:
            print(f"[RAOC-PILOT] Running pair={pair.pair_id} condition={condition.value} ...")
            trial = run_trial(
                pair, condition, target["prompt"], target["test_code"],
                model_name=_PILOT_MODEL, temperature=0.2,
            )
            _log_pilot_trial(trial, pair)
            results.append((pair, condition, trial))
            print(
                f"[RAOC-PILOT]   passed={trial.passed} "
                f"classified_approach={trial.classified_approach.value} "
                f"matches_outcome_direction={trial.matches_outcome_direction}"
            )

    return results


if __name__ == "__main__":
    run_pilot()
    print(f"\n[RAOC-PILOT] Done. Results logged to {_PILOT_LOG_PATH} (pilot data -- not pre-registered trial data).")
