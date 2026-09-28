"""
Mission 34 — schema for the blinded task-type gold-label experiment
(app/experiments/task_type_ground_truth/).

Isolated experiment module, mirroring this codebase's established pattern
(app/experiments/raoc/, app/experiments/preference_provenance/) — not
imported by any production path, never touches the real persisted
classifier (memory/task_type_classifier.pkl) in write mode.

Deliberately a plain dataclass file with no logic, per those siblings'
own separation of schema from harness/dataset construction.
"""
from dataclasses import dataclass, field
from typing import Optional

TASK_TYPES = ("coding", "personal", "general", "creative", "reasoning")
# Mission 33, Section 10/11: the labeler must be allowed to say "none of
# these fit" or "genuinely ambiguous" rather than being forced into one of
# the five buckets — forcing a fit is itself a way lexical/taxonomic
# assumptions get silently smuggled back in.
LABEL_CHOICES = TASK_TYPES + ("ambiguous", "none_of_these")


@dataclass
class CandidateExample:
    """One item in the pool before it has been labeled. `provenance` is
    mandatory and must be tracked honestly (Mission 33, Section 10) —
    'constructed' vs 'organic' are different evidentiary classes and must
    never be silently merged."""
    example_id: str
    prompt: str
    provenance: str          # "constructed_ordinary" | "constructed_adversarial"
    constructor_note: Optional[str] = None  # why this example was built this
    # way — NOT a suggested "correct" label. Recorded for audit trail only;
    # the blind labeler never sees this field (see blind_label.py).


@dataclass
class GoldLabel:
    """One human (or, if explicitly used as the secondary/weaker channel,
    LLM-judge) blinded judgment, recorded before Conditions A/B are ever
    computed for this example."""
    example_id: str
    label: str                # one of LABEL_CHOICES
    labeler: str               # "gremlin" | "llm_judge:<model>" — never "claude_session"
    labeled_at: str            # ISO timestamp
    saw_heuristic_output: bool = False   # must be False for every real record;
    # kept as an explicit, checkable field rather than an assumption, so a
    # violation of the blinding discipline is a data anomaly, not a silent one.
    saw_classifier_output: bool = False
    free_text_note: Optional[str] = None  # optional, e.g. an LLM judge's
    # free-text reasoning before being mapped onto LABEL_CHOICES


@dataclass
class ConditionResult:
    """One condition's (A/B/C) prediction for one example, plus the
    Section 13 comparison against the gold label."""
    example_id: str
    condition: str             # "A_heuristic" | "B_classifier" | "C_independent"
    prediction: Optional[str]
    confidence: Optional[float]
    matches_gold: Optional[bool] = None  # filled in once gold label exists
