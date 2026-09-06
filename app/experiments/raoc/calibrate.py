"""
RAOC calibration script (protocol §15's implementation plan, §17's pilot
protocol precursor). Validates the harness's own plumbing against
MockModel — a model that ignores injected context entirely — confirming
the pipeline runs end-to-end and correctly reports NO_DETECTABLE_EFFECT
before any real-Echo call is trusted. Mirrors the preference-provenance
harness's own "calibrate against Mock before touching anything real"
discipline (calibrate_preference_provenance_harness.py).

THIS SCRIPT IS NOT EXECUTED AS PART OF LANDING THIS CODE. Per Gremlin's
explicit instruction, running even the mock calibration pass is a
separate, later-gated step from building the harness — this file exists
so that step is a single command away once authorized, not so it runs
itself.

Usage (not run by anything automatically):
    python -m app.experiments.raoc.calibrate
"""
from __future__ import annotations

import glob
import json
from collections import Counter

from app.experiments.raoc.harness import MockModel, run_trial
from app.experiments.raoc.schema import RaocCondition
from app.experiments.raoc.task_pairs import find_real_task_pairs

_TASK_SUITE_GLOB = "audits/tier4_apparatus/tier4_stage*_task_suite.json"
_TRIALS_PER_CONDITION = 5  # small, calibration-only — not the pre-registered §11 sample size


def _load_task_map() -> dict:
    task_map = {}
    for suite_path in glob.glob(_TASK_SUITE_GLOB):
        with open(suite_path, encoding="utf-8") as f:
            data = json.load(f)
        for task in data.get("tasks", []):
            task_map[task["task_id"]] = task
    return task_map


def run_calibration() -> dict:
    """
    Runs _TRIALS_PER_CONDITION trials per condition per real task pair
    against MockModel (a fixed, context-blind responder — see harness.py).
    Success criterion (protocol §17): the pipeline runs end-to-end with
    no exceptions, and the mock condition shows no condition-dependent
    difference in matches_outcome_direction beyond what a context-blind
    model's fixed output would produce by construction (i.e., the
    plumbing doesn't fabricate an effect out of nothing).

    Returns a summary dict; does not write to memory/raoc_trials.jsonl
    (calibration trials are explicitly not real experimental data and
    must never be mixed into the same log as a real pilot/full run).
    """
    task_map = _load_task_map()
    pairs = find_real_task_pairs(min_pairs=3)
    if not pairs:
        raise RuntimeError("Calibration cannot proceed: no real task pairs found in the Tier-4 corpus.")

    mock = MockModel(fixed_code="def solve(*args, **kwargs):\n    return None\n")
    results_by_condition: dict = {c: [] for c in RaocCondition}

    for pair in pairs:
        target = task_map.get(pair.target_task_id)
        if target is None:
            continue
        for condition in RaocCondition:
            for _ in range(_TRIALS_PER_CONDITION):
                trial = run_trial(
                    pair, condition, target["prompt"], target["test_code"],
                    query_fn=mock,
                )
                results_by_condition[condition].append(trial)

    summary = {}
    for condition, trials in results_by_condition.items():
        n = len(trials)
        n_passed = sum(1 for t in trials if t.passed)
        approach_counts = Counter(t.classified_approach.value for t in trials)
        summary[condition.value] = {
            "n_trials": n,
            "n_passed": n_passed,
            "approach_distribution": dict(approach_counts),
        }

    return {
        "pairs_used": [p.pair_id for p in pairs],
        "trials_per_condition": _TRIALS_PER_CONDITION,
        "by_condition": summary,
        "note": (
            "Calibration only — MockModel ignores all injected context by "
            "construction, so approach_distribution should be IDENTICAL "
            "across all four conditions (the mock always returns the same "
            "fixed code regardless of what it's shown). If it is NOT "
            "identical, the harness itself has a bug that must be fixed "
            "before any real-Echo trial is trusted."
        ),
    }


if __name__ == "__main__":
    result = run_calibration()
    print(json.dumps(result, indent=2))
