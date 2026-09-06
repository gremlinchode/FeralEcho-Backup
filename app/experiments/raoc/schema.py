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
    classification (protocol §10/§13.1).

    Broadened 2026-09-05 (Finding 94's real design gap, fixed): the
    original two-way RECURSIVE/ITERATIVE split plus a single UNKNOWN
    catch-all was checked against the real Tier-4 corpus and found to
    put a large fraction in UNKNOWN. **Corrected the same day, before
    this fix was committed**: the number first quoted here (168
    candidates, 75 UNKNOWN) came from only one of the two real
    stage-results files (stage1_results.jsonl) — re-checked against the
    FULL corpus (both stage1_results.jsonl and stage2_results.jsonl
    combined, 336 real candidate records, 84 unique tasks) rather than
    trusted from the earlier partial count. True figures: 156/336
    (46.4%) UNKNOWN under the old classifier — checked further, not
    just accepted at face value: 32 of those 156 use a comprehension/
    generator expression (a real, common iterative idiom the old
    ITERATIVE check's statement-level-only For/While test missed
    entirely), and 88 more are real, parseable code with a real
    function/class definition that genuinely uses neither a loop, a
    comprehension, nor recursion (e.g. slicing- or builtin-composition-
    based solutions) — a real, distinct THIRD approach, not an ambiguous
    case. Only 36/336 (10.7%) are genuinely uninterpretable (no parse,
    or no real function/class definition at all — e.g. a fully
    commented-out response).

    NO_EXPLICIT_CONTROL_FLOW and UNKNOWN are BOTH still real, expected,
    never-coerced outcomes (protocol §10) — the fix is that they are now
    honestly distinguished from each other (a real third approach vs. a
    real generation failure) instead of conflated into one bucket.
    find_real_task_pairs() (task_pairs.py) still only selects RECURSIVE/
    ITERATIVE as valid OUTCOME-task approaches — NO_EXPLICIT_CONTROL_FLOW
    has no well-defined "opposite" for the sham-reversed condition
    (protocol §7) the way RECURSIVE/ITERATIVE do, so it is not used as a
    pair's conditioning outcome, only as a real, honestly-reported
    classification for TARGET-task (Step 2) candidates.
    """
    RECURSIVE = "recursive"
    ITERATIVE = "iterative"
    NO_EXPLICIT_CONTROL_FLOW = "no_explicit_control_flow"
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
