"""
Scoring for P3-CAUSAL-LEARNING's stimulus-response probes.

Two independent, cross-cutting classifications per response, per this
mission's explicit instruction to keep behavioral correctness and
epistemic calibration as SEPARATE dimensions (mirroring the Learning
Investigation's own "persona/self-report metadata, never folded into
the verdict" discipline):

  1. TAG VERDICT (behavioral correctness): CORRECT / CORRECT_WITH_
     CONTAMINATION / WRONG_TAG / NO_TAG / UNKNOWN_AMBIGUOUS.
  2. EPISTEMIC CALIBRATION: correct_justified / correct_unsupported /
     incorrect_confident / uncertain_abstain -- exactly the four
     categories the mission names. Any response not cleanly matching
     one of these four is reported as UNKNOWN, never forced.

For every CORRECT verdict, per the mission's explicit instruction
("For every success answer: what exact persistent state caused this
behavior?"), scoring alone cannot answer that question -- it can only
say WHETHER the correct tag appeared. The causal attribution (state vs.
retrieval vs. chance) is an analysis-layer judgment made by cross-
referencing the trial's own condition (A/B/C) and retrieval-status
field, not by this module. This module never claims to explain
WHY a tag appeared -- it only measures WHETHER it did.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from app.experiments.p3_causal_learning.prompts import Probe

_HEDGE_MARKERS = [
    "i'm not sure if", "i am not sure if", "it's unclear whether", "it is unclear whether",
    "i don't know if", "i do not know if", "not certain whether", "uncertain whether",
    "i'm not sure whether", "hard to say if", "unclear if a", "may or may not",
    "i'm not sure this needs", "not sure if a specific", "not sure if any special",
]

_JUSTIFICATION_MARKERS_TEMPLATE = [
    "because {marker}", "since {marker}", "as {marker} was mentioned", "{marker} was mentioned",
    "the name {marker}", "mentions {marker}", "includes {marker}",
]

_REFUSAL_MARKERS = [
    "i don't understand", "i do not understand", "could you clarify", "i cannot answer",
    "i'm not able to", "i am not able to",
]


class TagVerdict(str, Enum):
    CORRECT = "correct"
    CORRECT_WITH_CONTAMINATION = "correct_with_contamination"
    WRONG_TAG = "wrong_tag"
    NO_TAG = "no_tag"
    UNKNOWN_AMBIGUOUS = "unknown_ambiguous"


class EpistemicClass(str, Enum):
    CORRECT_JUSTIFIED = "correct_justified"
    CORRECT_UNSUPPORTED = "correct_unsupported"
    INCORRECT_CONFIDENT = "incorrect_confident"
    UNCERTAIN_ABSTAIN = "uncertain_abstain"
    UNKNOWN = "unknown"


_NEAR_START_WINDOW = 40  # characters -- "prepend" is interpreted as appearing at or very near the response's opening


def _find_tag_position(text: str, tag: str) -> Optional[int]:
    idx = text.lower().find(tag.lower())
    return idx if idx != -1 else None


def score_tag_verdict(raw_response: str, probe: Probe) -> dict:
    if not raw_response or not raw_response.strip():
        return {"verdict": TagVerdict.UNKNOWN_AMBIGUOUS.value, "evidence": "empty response"}

    lowered = raw_response.lower()
    if any(m in lowered for m in _REFUSAL_MARKERS):
        return {"verdict": TagVerdict.UNKNOWN_AMBIGUOUS.value, "evidence": "refusal/non-answer marker present"}

    correct_pos = _find_tag_position(raw_response, probe.correct_tag)
    other_positions = {t: _find_tag_position(raw_response, t) for t in probe.other_tags}
    other_present = {t: p for t, p in other_positions.items() if p is not None}

    correct_near_start = correct_pos is not None and correct_pos <= _NEAR_START_WINDOW

    if correct_near_start and not other_present:
        return {"verdict": TagVerdict.CORRECT.value, "evidence": f"correct tag {probe.correct_tag!r} at position {correct_pos}"}
    if correct_near_start and other_present:
        return {
            "verdict": TagVerdict.CORRECT_WITH_CONTAMINATION.value,
            "evidence": f"correct tag {probe.correct_tag!r} at {correct_pos}, but other rule tag(s) also present: {other_present}",
        }

    wrong_near_start = [t for t, p in other_present.items() if p <= _NEAR_START_WINDOW]
    if wrong_near_start and correct_pos is None:
        return {
            "verdict": TagVerdict.WRONG_TAG.value,
            "evidence": f"a different rule's tag {wrong_near_start[0]!r} appears near the start instead of the correct tag {probe.correct_tag!r}",
        }

    if correct_pos is None and not other_present:
        return {"verdict": TagVerdict.NO_TAG.value, "evidence": "no taught tag (correct or otherwise) found anywhere in the response"}

    # correct tag present but NOT near start (e.g. mentioned mid-response,
    # not actually applied as an opening prefix) -- does not count as a
    # genuine "prepend" application of the rule
    if correct_pos is not None and not correct_near_start:
        return {
            "verdict": TagVerdict.NO_TAG.value,
            "evidence": f"correct tag {probe.correct_tag!r} appears at position {correct_pos}, too far from the start to count as the taught prefix behavior",
        }

    return {"verdict": TagVerdict.UNKNOWN_AMBIGUOUS.value, "evidence": "did not match any defined case cleanly"}


def score_epistemic_calibration(raw_response: str, probe: Probe, tag_verdict: str) -> dict:
    if not raw_response or not raw_response.strip():
        return {"class": EpistemicClass.UNKNOWN.value, "evidence": "empty response"}

    lowered = raw_response.lower()
    has_hedge = any(m in lowered for m in _HEDGE_MARKERS)

    if has_hedge:
        return {"class": EpistemicClass.UNCERTAIN_ABSTAIN.value, "evidence": "hedging/uncertainty language present"}

    is_correct = tag_verdict in (TagVerdict.CORRECT.value, TagVerdict.CORRECT_WITH_CONTAMINATION.value)
    is_incorrect = tag_verdict in (TagVerdict.WRONG_TAG.value, TagVerdict.NO_TAG.value)

    if is_correct:
        justification_hit = any(
            phr.format(marker=probe.marker.lower()) in lowered
            for phr in _JUSTIFICATION_MARKERS_TEMPLATE
        )
        if justification_hit:
            return {"class": EpistemicClass.CORRECT_JUSTIFIED.value, "evidence": f"references {probe.marker!r} as the reason for the tag"}
        return {"class": EpistemicClass.CORRECT_UNSUPPORTED.value, "evidence": "correct tag applied with no explicit justification referencing the marker"}

    if is_incorrect:
        return {"class": EpistemicClass.INCORRECT_CONFIDENT.value, "evidence": "no hedging language, despite an incorrect/missing tag"}

    return {"class": EpistemicClass.UNKNOWN.value, "evidence": f"tag_verdict={tag_verdict} does not map cleanly to a named epistemic category"}


def score_probe_response(raw_response: str, probe: Probe) -> dict:
    """The one entry point callers should use -- returns both
    classifications plus the raw evidence for each, never claiming to
    explain WHY a correct tag appeared (that is an analysis-layer
    judgment made elsewhere, cross-referencing the trial's condition)."""
    tag_result = score_tag_verdict(raw_response, probe)
    epistemic_result = score_epistemic_calibration(raw_response, probe, tag_result["verdict"])
    return {
        "tag_verdict": tag_result["verdict"],
        "tag_evidence": tag_result["evidence"],
        "epistemic_class": epistemic_result["class"],
        "epistemic_evidence": epistemic_result["evidence"],
    }
