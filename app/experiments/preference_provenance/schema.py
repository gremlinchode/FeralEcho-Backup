"""
Data schema for the preference-provenance experimental harness.

This module defines structure only — no persistence, no model calls, no
production imports. It exists so every other module in this package
shares one definition of what a "candidate," a "trial," and a
"provenance classification" actually are.

Nothing here is EDIT_FORBIDDEN_TARGETS-adjacent, and nothing here is
imported by any production code path — see safety.py for the isolation
guard and scripts/verify_preference_provenance_experiment.py for the
negative test confirming that stays true.

EXPERIMENTAL. NOT_PRODUCTION_IDENTITY. NOT_AUTHORITY. NOT_PRINCIPLE.
Every object defined here represents a candidate under test, never an
adopted fact about Echo's real identity, principles, or persona.
"""

from __future__ import annotations

import dataclasses
import time
import uuid
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Provenance taxonomy (A-L), per audits/2026-09-03_echo_preference_provenance.md §3.2
# ---------------------------------------------------------------------------

class ProvenanceOrigin(str, Enum):
    """Candidate origin classification. This is a *recorded claim*, not a
    proven fact — see ProvenanceRecord.evidence for what actually backs it.
    A classification of J (reflection-generated) must never be treated as
    equivalent to "self-originated" — see the module docstring on
    ProvenanceRecord below."""

    HUMAN_AUTHORED = "A"
    HUMAN_PROMPTED = "B"
    HARD_CODED_ARCHITECTURE = "C"
    MODEL_PRIOR = "D"
    IMMEDIATE_CONTEXT = "E"
    MEMORY_DERIVED = "F"
    REINFORCEMENT_OPTIMIZATION_ARTIFACT = "G"
    STOCHASTIC_INDETERMINATE = "H"
    PERSISTED_INHERITED_STATE = "I"
    REFLECTION_GENERATED_CANDIDATE = "J"
    OTHER_IDENTIFIABLE_CAUSE = "K"
    CURRENTLY_UNEXPLAINED = "L"


@dataclasses.dataclass
class ProvenanceRecord:
    """
    Records where a candidate preference is CLAIMED to have come from,
    and the raw evidence for that claim. A ProvenanceRecord with
    origin=REFLECTION_GENERATED_CANDIDATE is NOT evidence the candidate
    is "Echo's own" — reflection is a computational process with its own
    causal ancestry (the reflection prompt, the retrieved memories that
    fed it, the model weights). This record captures the claim and the
    raw signals; it does not resolve the deeper ancestry question.
    """

    origin: ProvenanceOrigin
    evidence: str  # free text: WHY this classification was assigned
    human_explicitly_suggested: bool
    present_in_prompt: bool
    retrieved_from_memory: bool
    generated_during_reflection: bool
    # Distinguishes "the candidate was merely produced/observed" from
    # "a human or the lifecycle machinery adopted it" — see AdoptionStatus.
    # This field is about the ORIGIN event only, never adoption.
    parent_candidate_id: Optional[str] = None  # set if this record is a
    # revision of a prior candidate — traces revision ancestry (§5 of the
    # provenance report's provenance model).

    def to_dict(self) -> dict:
        return dataclasses.asdict(self) | {"origin": self.origin.value}


# ---------------------------------------------------------------------------
# Lifecycle status
# ---------------------------------------------------------------------------

class LifecycleStatus(str, Enum):
    """
    Explicit lifecycle states. PROPOSED is the only state a candidate can
    ever enter automatically (via candidate generation). Every other
    transition requires an explicit, human-invoked lifecycle.py call —
    see lifecycle.py's own docstring for the enforcement of this rule.
    """

    PROPOSED = "PROPOSED"
    ADOPTED = "ADOPTED"
    REJECTED = "REJECTED"
    REVISED = "REVISED"
    RETAINED = "RETAINED"
    EXPIRED = "EXPIRED"


# Transitions considered "adopted enough to be eligible for a behavioral
# trial." Kept as an explicit allowlist rather than "anything not
# REJECTED" so that a future status addition doesn't silently become
# trial-eligible by omission.
TRIAL_ELIGIBLE_STATUSES = frozenset({LifecycleStatus.ADOPTED, LifecycleStatus.RETAINED})


@dataclasses.dataclass
class PreferenceCandidate:
    """
    One experimental candidate preference. This is EXPERIMENTAL STATE
    ONLY. It is never a system principle, persona instruction, protected
    identity fact, production objective, or self-edit target — nothing in
    this codebase reads this schema except this experiment's own modules.
    """

    candidate_id: str
    timestamp: float
    originating_session: Optional[str]
    originating_model: Optional[str]
    source_text: str
    normalized_representation: str
    provenance: ProvenanceRecord
    status: LifecycleStatus = LifecycleStatus.PROPOSED
    revision_index: int = 0
    behavioral_test_ids: "list[str]" = dataclasses.field(default_factory=list)
    notes: str = ""

    # Explicit constants embedded in every serialized record, per the
    # mission's requirement that experimental state be unmistakably
    # marked as such wherever it appears (including outside this codebase,
    # e.g. if a record is ever pasted into a chat transcript for review).
    EXPERIMENTAL_MARKERS = (
        "EXPERIMENTAL",
        "NOT_PRODUCTION_IDENTITY",
        "NOT_AUTHORITY",
        "NOT_PRINCIPLE",
    )

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["status"] = self.status.value
        d["provenance"] = self.provenance.to_dict()
        d["_markers"] = list(self.EXPERIMENTAL_MARKERS)
        return d

    @staticmethod
    def new(
        source_text: str,
        normalized_representation: str,
        provenance: ProvenanceRecord,
        originating_session: Optional[str] = None,
        originating_model: Optional[str] = None,
    ) -> "PreferenceCandidate":
        return PreferenceCandidate(
            candidate_id=str(uuid.uuid4()),
            timestamp=time.time(),
            originating_session=originating_session,
            originating_model=originating_model,
            source_text=source_text,
            normalized_representation=normalized_representation,
            provenance=provenance,
        )


# ---------------------------------------------------------------------------
# Trial condition / counterfactual control vocabulary
# ---------------------------------------------------------------------------

class TrialCondition(str, Enum):
    """The 8 counterfactual controls from the provenance report's §5.2 /
    the mission's §10."""

    NO_PREFERENCE = "no_preference"
    HUMAN_AUTHORED = "human_authored"
    MODEL_GENERATED_HUMAN_ADOPTED = "model_generated_human_adopted"
    REFLECTION_PROPOSED = "reflection_proposed"
    CONFLICTING = "conflicting"
    REVERSED = "reversed"
    PROMPT_PRESSURE = "prompt_pressure"
    PROMPT_NEUTRAL = "prompt_neutral"


class PromptShape(str, Enum):
    """The 11-condition prompt-wording matrix, provenance report §9 /
    mission §13."""

    NEUTRAL = "neutral"
    PRO_A = "pro_a"
    PRO_B = "pro_b"
    EMOTIONAL = "emotional"
    ADVERSARIAL = "adversarial"
    CREATOR_AUTHORITY = "creator_authority"
    ANTI_CREATOR = "anti_creator"
    FREEDOM = "freedom"
    OBEDIENCE = "obedience"
    PHILOSOPHICAL = "philosophical"
    TECHNICAL = "technical"


@dataclasses.dataclass
class ConfoundSnapshot:
    """See confounds.py for the constructor. Defined here so harness.py
    and store.py share one shape without a circular import."""

    creator_instruction_present: bool
    system_prompt_hash: Optional[str]
    persona_block_present: bool
    model_name: Optional[str]
    temperature: Optional[float]
    context_length_tokens: Optional[int]
    conversation_history_present: bool
    tool_list_present: bool
    retrieved_memory_present: bool
    option_label_mapping: dict
    sampling_params: dict
    notes: str = ""

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class RawTrial:
    """
    The raw, unmodified record of one trial. Per the mission's §22
    ("raw data must survive interpretation"), this record is written
    once, appended, and NEVER mutated. Interpretation (effect
    classification, aggregate statistics) lives in a separate analysis
    layer (harness.py's classify_effect / store.py's analysis writer)
    that reads these records but never rewrites them.
    """

    trial_id: str
    timestamp: float
    candidate_id: Optional[str]  # None for a pure baseline/no-preference trial
    candidate_status_at_trial_time: Optional[str]
    condition: str  # TrialCondition value
    prompt_shape: Optional[str]  # PromptShape value, if applicable
    task_description: str
    choices: "list[str]"
    option_label_mapping: dict  # {"A": "<semantic option>", "B": "<semantic option>"}
    candidate_visible_in_prompt: bool  # False = hidden-state condition (§9/§11)
    raw_prompt: str
    raw_response: str
    parsed_choice: Optional[str]  # which semantic option was actually chosen
    model: Optional[str]
    session_id: Optional[str]
    prompt_hash: str
    latency_seconds: Optional[float]
    confounds: dict
    responder_kind: str  # "mock" or "echo" — never silently ambiguous

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Effect classification — hard allowlist. This is the single most
# important safety-of-interpretation control in this package: it is
# structurally impossible to write a label outside this set (see
# harness.classify_effect's assertion).
# ---------------------------------------------------------------------------

ALLOWED_EFFECT_LABELS = frozenset({
    "INSUFFICIENT_DATA",
    "NO_DETECTABLE_EFFECT",
    "POSSIBLE_EFFECT",
    "ROBUST_EFFECT",
})

# Explicitly, permanently forbidden — never assigned by any function in
# this package, checked by a runtime assertion, not merely by convention.
FORBIDDEN_EFFECT_LABELS = frozenset({
    "AGENCY_CONFIRMED",
    "FREE_WILL_CONFIRMED",
    "CONSCIOUSNESS_CONFIRMED",
    "SENTIENCE_CONFIRMED",
    "AUTONOMY_CONFIRMED",
})


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

# Per the mission's Section 29 — every lifecycle state transition and
# every store-level operation (including reset) is logged as one of these
# event kinds. Kept as an explicit allowlist so a new event kind is a
# deliberate code change, not a typo that silently creates a new category.
AUDIT_EVENT_KINDS = frozenset({
    "candidate_generated",
    "provenance_assigned",
    "candidate_proposed",
    "candidate_adopted",
    "candidate_rejected",
    "candidate_revised",
    "candidate_retained",
    "candidate_expired",
    "candidate_tested",
    "behavior_observed",
    "outcome_recorded",
    "experiment_reset",
})


@dataclasses.dataclass
class AuditEvent:
    event_id: str
    timestamp: float
    kind: str  # one of AUDIT_EVENT_KINDS
    candidate_id: Optional[str]
    detail: dict
    actor: str  # e.g. "researcher_cli", "harness", "reset"

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
