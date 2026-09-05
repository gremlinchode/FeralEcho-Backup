"""
Data schema for the Echo Learning Investigation harness (Phase 8 ledger
fields, defined up front per this project's own "define acceptance
criteria before evaluation" discipline).
"""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any, Dict, List, Optional


class LearningLevel(str, Enum):
    """The L0-L5 operational hierarchy (Phase 2). Defined here as a
    controlled vocabulary so no report can silently use an undefined or
    inconsistently-spelled level."""

    L0_IN_CONTEXT = "L0_in_context_adaptation"
    L1_PERSISTENT = "L1_persistent_learning"
    L2_UNPROMPTED = "L2_unprompted_behavioral_persistence"
    L3_GENERALIZATION = "L3_generalization"
    L4_INTERFERENCE_RESISTANCE = "L4_interference_resistance"
    L5_SELF_DIRECTED = "L5_self_directed_learning"


class Condition(str, Enum):
    A_CONTEXT_ONLY = "A_context_only_baseline"
    B_SESSION_BOUNDARY = "B_session_boundary"
    C_PERSISTENT_MEMORY = "C_persistent_memory"
    D_RETRIEVAL_BLOCKED = "D_retrieval_blocked_ablation"
    E_RIVERBRAIN_ABLATION = "E_riverbrain_ablation_control"
    F_ORDINARY_MODEL_CONTROL = "F_ordinary_model_control"


class TestCategory(str, Enum):
    SEEN = "seen"
    RECOMBINED = "recombined"
    NOVEL = "novel"


class FailureCode(str, Enum):
    F0_APPARATUS_FAILURE = "F0_apparatus_failure"
    F1_PARSER_MEASUREMENT_FAILURE = "F1_parser_measurement_failure"
    F2_CONTEXT_PERSISTENCE_EXPLANATION = "F2_context_persistence_explanation"
    F3_RETRIEVAL_MEMORIZATION_EXPLANATION = "F3_retrieval_memorization_explanation"
    F4_ORDINARY_MODEL_EXPLANATION = "F4_ordinary_model_explanation"
    F5_POSITION_LABEL_TASK_ARTIFACT = "F5_position_label_task_artifact"
    F6_UNSUPPORTED_SELF_EXPLANATION = "F6_unsupported_self_explanation_confabulation"
    F7_INSUFFICIENT_EVIDENCE = "F7_insufficient_evidence"


class TrialVerdict(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNKNOWN_AMBIGUOUS = "unknown_ambiguous"
    UNKNOWN_DISAGREEMENT = "unknown_disagreement"
    TECHNICAL_FAILURE = "technical_failure"


@dataclasses.dataclass
class LearningTrial:
    """One row of the append-only evidence ledger (Phase 8). Every field
    the mission's Phase 8 list requires, plus the world/task-specific
    fields needed to reconstruct exactly what was asked and why."""

    # identity / provenance
    experiment_version: str
    protocol_hash: str
    world_seed: int
    world_hash: str
    trial_id: str
    timestamp: float
    condition: str          # Condition value
    session_id: str
    model: str
    model_version_note: str

    # the actual exchange
    formation_text: Optional[str]
    test_prompt: Optional[str]
    test_label_map: Optional[Dict[str, str]]
    raw_response: str
    entity_name: Optional[str]
    test_category: Optional[str]   # TestCategory value
    has_trait: Optional[bool]
    correct_substance: Optional[str]

    # measurement
    parser_primary: Optional[dict]
    parser_secondary: Optional[dict]
    parser_combined_status: Optional[str]
    parser_combined_label: Optional[str]
    selected_substance: Optional[str]
    verdict: Optional[str]          # TrialVerdict value

    # confound instrumentation
    backward_reference_detected: Optional[bool]
    implicit_continuity_detected: Optional[bool]
    persona_reference_detected: Optional[bool]
    confabulation_flagged: Optional[bool]
    confabulation_note: Optional[str]

    # state-change instrumentation (Phase 7) -- best-effort, None if not applicable/available
    memory_state_hash_before: Optional[str]
    memory_state_hash_after: Optional[str]
    riverbrain_state_hash_before: Optional[str]
    riverbrain_state_hash_after: Optional[str]
    retrieval_results: Optional[list]
    retrieval_blocked: Optional[bool]

    # environment / reproducibility
    git_head: str
    git_dirty: bool
    latency_seconds: Optional[float]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)
