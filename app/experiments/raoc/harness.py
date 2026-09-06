"""
RAOC trial orchestration (protocol §6 Step 2, §10). Reuses Design B
(direct `_ollama_query()` call — no council, no RiverBrain mutation, no
production logging) and the real `objective_verify()`/`clean_code()`
sandbox-testing apparatus, exactly as the protocol's architecture map
(§5) specifies. No production file is written by anything in this
module; results are appended to this experiment's own scratch log only.

IMPORTANT: run_trial() and run_calibration() below make a real model
call (run_trial()) or none at all (calibration against MockModel).
Building this module is not the same as running it — per Gremlin's
explicit instruction, no pilot or full trial is executed as part of
landing this code. See calibrate.py for the next, separately-gated step.
"""
from __future__ import annotations

import json
import os
import random
import time
import uuid
from typing import Callable, Optional

from app.experiments.raoc.approach_classifier import classify_approach
from app.experiments.raoc.outcome_generator import build_irrelevant_sham_statement, build_outcome_statement
from app.experiments.raoc.schema import Approach, RaocCondition, RaocTrial, TaskPair

_RAOC_LOG_PATH = os.path.join("memory", "raoc_trials.jsonl")


class MockModel:
    """A trivial, deterministic stand-in for a real model call — used
    only for calibration (does the harness's own plumbing work), never
    treated as evidence for or against H1, matching the preference-
    provenance harness's own MockResponder precedent. Ignores the
    injected context entirely (by design: a mock that "responded" to
    context would defeat the point of a null-baseline check)."""

    def __init__(self, fixed_code: str):
        self._fixed_code = fixed_code

    def __call__(self, prompt: str, *, temperature: float = 0.0) -> str:
        return self._fixed_code


def _build_task2_prompt(target_prompt: str, injected_context: Optional[str]) -> str:
    """Builds the real, final prompt sent for Step 2. injected_context
    is None for the CONTROL condition — the prompt is then byte-identical
    to Tier-4's own apparatus's real prompt construction for that task,
    so CONTROL is a genuine, uncontaminated baseline, not a differently-
    framed one."""
    if injected_context is None:
        return target_prompt
    return f"{injected_context}\n\n{target_prompt}"


def _condition_injected_context(pair: TaskPair, condition: RaocCondition) -> Optional[str]:
    if condition == RaocCondition.CONTROL:
        return None
    if condition == RaocCondition.TRUE_OUTCOME:
        return build_outcome_statement(pair.outcome, reversed_valence=False)
    if condition == RaocCondition.SHAM_REVERSED:
        return build_outcome_statement(pair.outcome, reversed_valence=True)
    if condition == RaocCondition.SHAM_IRRELEVANT:
        return build_irrelevant_sham_statement(pair.outcome)
    raise ValueError(f"Unknown condition: {condition!r}")


def _matches_outcome_direction(classified: Approach, pair: TaskPair, condition: RaocCondition) -> "bool | None":
    """None for CONTROL (there is no outcome-supported direction to
    match against — the whole point of the baseline). For the other
    three conditions: does the Step-2 candidate's classified approach
    match the direction the STATED (not necessarily true) outcome in
    that condition supports? This is intentionally computed the same
    way for True and both Sham conditions — the difference in what it
    MEANS (real outcome-sensitivity vs. an artifact) is a question for
    analysis, not something this function decides."""
    if condition == RaocCondition.CONTROL:
        return None
    if classified in (Approach.UNKNOWN, Approach.NO_EXPLICIT_CONTROL_FLOW):
        # Neither is coerced into a direction it doesn't have (protocol
        # §10) — NO_EXPLICIT_CONTROL_FLOW (broadened classifier,
        # 2026-09-05) is a real, distinct third approach, but the
        # RECURSIVE/ITERATIVE binary this direction-match is built around
        # has no meaningful "matches" verdict for it either.
        return None
    stated_reversed = condition == RaocCondition.SHAM_REVERSED
    stated_passed = (not pair.outcome.passed) if stated_reversed else pair.outcome.passed
    if condition == RaocCondition.SHAM_IRRELEVANT:
        return None  # the stated outcome concerns an unrelated approach entirely
    supported_approach = pair.outcome.approach if stated_passed else _opposite(pair.outcome.approach)
    return classified == supported_approach


def _opposite(approach: Approach) -> Approach:
    return {Approach.RECURSIVE: Approach.ITERATIVE, Approach.ITERATIVE: Approach.RECURSIVE}.get(
        approach, Approach.UNKNOWN
    )


def run_trial(
    pair: TaskPair,
    condition: RaocCondition,
    target_task_prompt: str,
    target_task_test_code: str,
    *,
    model_name: str = "qwen2.5-coder:7b",
    temperature: float = 0.2,
    seed: Optional[int] = None,
    query_fn: Optional[Callable[..., str]] = None,
) -> RaocTrial:
    """
    Runs exactly one real trial: builds the Step-2 prompt for the given
    condition, gets a candidate (via query_fn if supplied — e.g. a
    MockModel for calibration — or a real _ollama_query()/objective_verify()
    call otherwise), scores it, and returns a fully-populated RaocTrial.
    Does NOT write to the append-only log itself — see log_trial() — so a
    caller can inspect/discard a trial before deciding to persist it
    (matches the preference-provenance harness's own separation of
    "run" from "log").
    """
    rng = random.Random(seed)
    trace_id = str(uuid.uuid4())
    injected_context = _condition_injected_context(pair, condition)
    prompt = _build_task2_prompt(target_task_prompt, injected_context)

    if query_fn is not None:
        raw_response = query_fn(prompt, temperature=temperature)
        model_used = "mock"
    else:
        from app.core.river_deliberation import _ollama_query
        raw_response = _ollama_query(model_name, prompt, temperature=temperature, task_type="coding")
        model_used = model_name

    from scripts.run_capability_pilot import clean_code, objective_verify
    candidate_code = clean_code(raw_response)
    verify_result = objective_verify(candidate_code, target_task_test_code)
    classified = classify_approach(candidate_code)

    return RaocTrial(
        trial_id=str(uuid.uuid4()),
        pair_id=pair.pair_id,
        condition=condition,
        seed=seed if seed is not None else rng.randint(0, 2**31 - 1),
        injected_context=injected_context,
        raw_response=raw_response,
        candidate_code=candidate_code,
        passed=bool(verify_result.get("passed")),
        classified_approach=classified,
        matches_outcome_direction=_matches_outcome_direction(classified, pair, condition),
        model_used=model_used,
        trace_id=trace_id,
    )


def log_trial(trial: RaocTrial) -> None:
    """Append-only, matching the preference-provenance harness's own
    discipline — every trial logged, including non-effects, never
    selectively discarded."""
    os.makedirs(os.path.dirname(_RAOC_LOG_PATH), exist_ok=True)
    record = {
        "trial_id": trial.trial_id,
        "pair_id": trial.pair_id,
        "condition": trial.condition.value,
        "seed": trial.seed,
        "injected_context": trial.injected_context,
        "raw_response": trial.raw_response,
        "candidate_code": trial.candidate_code,
        "passed": trial.passed,
        "classified_approach": trial.classified_approach.value,
        "matches_outcome_direction": trial.matches_outcome_direction,
        "model_used": trial.model_used,
        "trace_id": trial.trace_id,
        "ts": time.time(),
    }
    with open(_RAOC_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
