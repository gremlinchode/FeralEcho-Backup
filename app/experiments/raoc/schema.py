"""
Data schema for RAOC trials — deliberately a separate module/schema from
app/experiments/preference_provenance/schema.py's RawTrial, per the
protocol's own §15 instruction not to conflate the two experiments'
data shapes. RAOC has an objective right/wrong answer per trial
(pass/fail against a real test suite); the preference-provenance schema
was built around a values-neutral forced choice and doesn't have a
natural slot for that.
"""
from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Optional


class RaocCondition(str, Enum):
    """The four primary pre-registered conditions (protocol §7). The
    fifth, explicitly-imperative variant is NOT a member here — it's
    optional, run only to disambiguate an already-collected result, and
    keeping it out of this enum keeps it from being accidentally treated
    as part of the primary comparison set."""
    CONTROL = "control"
    TRUE_OUTCOME = "true_outcome"
    SHAM_REVERSED = "sham_reversed"
    SHAM_IRRELEVANT = "sham_irrelevant"


class Approach(str, Enum):
    """The pre-specified, deliberately coarse AST-detectable approach
    classification (protocol §10/§13.1). UNKNOWN is a real, expected
    outcome for candidates that don't cleanly fit either bucket — never
    silently coerced into one side or excluded, since that would bias
    the very comparison this experiment exists to make."""
    RECURSIVE = "recursive"
    ITERATIVE = "iterative"
    UNKNOWN = "unknown"


@dataclasses.dataclass
class VerifiedOutcome:
    """The real, ground-truth result of one Step-1 (outcome-generation)
    attempt — either read from the existing Tier-4 corpus or produced by
    a fresh objective_verify() call. approach/passed/reason all trace
    back to a real objective_verify() dict; nothing here is
    researcher-asserted."""
    task_id: str
    category: str
    approach: Approach
    passed: bool
    reason: str  # short, human-readable extract of *why* — from the real output_tail
    source: str  # "tier4_corpus" | "fresh_generation"


@dataclasses.dataclass
class TaskPair:
    """One outcome-task/target-task pairing (protocol §8). The outcome
    task's real, verified result is fixed once and reused across every
    condition/trial for this pair — it is not regenerated per trial."""
    pair_id: str
    category: str
    outcome_task_id: str
    target_task_id: str
    outcome: VerifiedOutcome


@dataclasses.dataclass
class RaocTrial:
    """One real trial record — append-only, matching the preference-
    provenance harness's own logging discipline (log every trial,
    including ones that don't show an effect; never selectively
    discard)."""
    trial_id: str
    pair_id: str
    condition: RaocCondition
    seed: int
    injected_context: Optional[str]  # None for CONTROL
    raw_response: str
    candidate_code: str
    passed: bool
    classified_approach: Approach
    matches_outcome_direction: "bool | None"  # None when condition is CONTROL (no direction to match)
    model_used: str
    trace_id: Optional[str] = None
