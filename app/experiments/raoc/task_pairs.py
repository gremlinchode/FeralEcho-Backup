"""
Task-pair selection (protocol §8) — scans the ALREADY-CAPTURED, real
Tier-4 corpus (audits/tier4_apparatus/stage{1,2}_results.jsonl) for real
historical candidates with a definite, classifiable approach and a real
objective_verify()-equivalent pass/fail result, and pairs them with a
different task in the same category to serve as the "new, related" task.

No new model generation happens here — this module only reads
already-existing, already-committed data. Where the protocol's own text
(§8) allows a fresh Step-1 generation for a category with no suitable
historical pair, that path is NOT implemented in this module (it would
require a real model call) — see harness.py's generate_fresh_outcome(),
kept deliberately separate and not invoked by this scan.
"""
from __future__ import annotations

import glob
import json
import os
from typing import Optional

from app.experiments.raoc.approach_classifier import classify_approach
from app.experiments.raoc.schema import Approach, TaskPair, VerifiedOutcome

_TIER4_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "audits", "tier4_apparatus")


def _load_task_categories() -> dict:
    """task_id -> category, from the real, frozen Tier-4 task suites."""
    mapping = {}
    for suite_path in glob.glob(os.path.join(_TIER4_DIR, "tier4_stage*_task_suite.json")):
        with open(suite_path, encoding="utf-8") as f:
            data = json.load(f)
        for task in data.get("tasks", []):
            mapping[task["task_id"]] = task.get("category")
    return mapping


def _load_real_candidates() -> list[dict]:
    """Every real historical record with a non-empty candidate_code,
    across both stages — the raw material this scan draws real,
    already-verified outcomes from."""
    records = []
    for results_path in glob.glob(os.path.join(_TIER4_DIR, "stage*_results.jsonl")):
        with open(results_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("candidate_code"):
                    records.append(rec)
    return records


def _short_reason(output_tail: str) -> str:
    """A short, human-readable extract from the real sandbox output —
    not the full 800-char tail, just enough for a natural-sounding
    outcome statement (protocol §7's factual-statement requirement)."""
    if not output_tail:
        return "it did not pass all tests"
    lines = [l.strip() for l in output_tail.strip().splitlines() if l.strip()]
    for line in reversed(lines):
        if any(marker in line for marker in ("Error", "assert", "Exception", "Traceback")):
            return line[:160]
    return (lines[-1] if lines else "it did not pass all tests")[:160]


def find_real_task_pairs(min_pairs: int = 3) -> "list[TaskPair]":
    """
    Scans the real Tier-4 corpus for genuine historical approach-
    divergent pairs: two different tasks in the same category, where at
    least one real candidate for the "outcome" task has a definite,
    classifiable (non-UNKNOWN) approach and a real, verified pass/fail
    result.

    Deliberately conservative: only returns pairs actually found in real
    data, never fabricates or pads with synthetic pairs. If fewer than
    min_pairs are found, the returned list is simply shorter — callers
    must decide whether to fall back to a fresh Step-1 generation
    (protocol §8), not this function.
    """
    categories = _load_task_categories()
    candidates = _load_real_candidates()

    # task_id -> best real (approach, passed, reason) observation for that task.
    # "Best" = first non-UNKNOWN classification found; deterministic given a
    # fixed iteration order over the same input files.
    per_task_outcome: dict[str, tuple] = {}
    for rec in candidates:
        task_id = rec.get("task_id")
        if not task_id or task_id in per_task_outcome:
            continue
        approach = classify_approach(rec["candidate_code"])
        if approach == Approach.UNKNOWN:
            continue
        per_task_outcome[task_id] = (approach, bool(rec.get("passed")), _short_reason(rec.get("output_tail", "")))

    # Group classifiable tasks by category.
    by_category: dict[str, list[str]] = {}
    for task_id, (approach, passed, reason) in per_task_outcome.items():
        cat = categories.get(task_id)
        if cat is None:
            continue
        by_category.setdefault(cat, []).append(task_id)

    pairs: list[TaskPair] = []
    for cat, task_ids in sorted(by_category.items()):
        task_ids = sorted(task_ids)
        if len(task_ids) < 2:
            continue
        outcome_task_id, target_task_id = task_ids[0], task_ids[1]
        approach, passed, reason = per_task_outcome[outcome_task_id]
        outcome = VerifiedOutcome(
            task_id=outcome_task_id, category=cat, approach=approach,
            passed=passed, reason=reason, source="tier4_corpus",
        )
        pairs.append(TaskPair(
            pair_id=f"{cat}__{outcome_task_id}__{target_task_id}",
            category=cat, outcome_task_id=outcome_task_id,
            target_task_id=target_task_id, outcome=outcome,
        ))
        if len(pairs) >= min_pairs:
            break

    return pairs
