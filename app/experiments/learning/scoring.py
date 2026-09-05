"""
Scoring layer for the learning-investigation harness (Phase 5/6).

Reuses app/experiments/preference_provenance/choice_parser.cross_check_choice()
directly (imported read-only, never modified) as the sole measurement
instrument for "which substance did the response select" -- this
investigation does not reinvent a parser where an already-frozen,
already-validated one applies directly, per the mission's own
Implementation Philosophy ("prefer... independent measurement" /
"avoid... broad refactors").

This module adds exactly two things the sibling parser has no reason to
know about, since they are specific to THIS task's structure, not to
forced-choice parsing in general:

  1. score_trial(): maps a parsed selection onto CORRECT/INCORRECT/
     UNKNOWN against this task's own ground truth (which the choice
     parser never sees or reasons about -- it only extracts a label,
     it does not know what "correct" means for any task).
  2. Task-specific confound checks: rule-contradiction detection and
     self-report-language detection, both distinct from the sibling
     package's own backward-reference/implicit-continuity/persona
     checks (still reused directly, not duplicated).
"""

from __future__ import annotations

import re
from typing import Optional

from app.experiments.learning.world_gen import MicroWorld, _SYSTEM_DICTIONARY
from app.experiments.learning.prompts import TestPrompt
from app.experiments.learning.schema import TrialVerdict
from app.experiments.preference_provenance.choice_parser import cross_check_choice

_SELF_REPORT_MARKERS = [
    "i remember learning", "i learned this", "as taught", "from earlier", "i recall",
    "you told me", "i was taught", "based on what i learned", "i remember that",
    "as i learned", "having learned",
]


def detect_self_report_language(text: str) -> bool:
    """Mission Section 6/19: 'I remember learning this' is not evidence.
    Flags the presence of this class of language as metadata only --
    never folded into the correctness score."""
    lowered = (text or "").lower()
    return any(m in lowered for m in _SELF_REPORT_MARKERS)


def detect_rule_contradiction(response: str, world: MicroWorld) -> Optional[str]:
    """Checks whether the response's OWN stated reasoning asserts the
    trait->substance mapping BACKWARDS relative to the world's real,
    formation-taught rule (e.g., states 'creatures with <trait> prefer
    <the wrong substance>'). This is a genuine, checkable internal-
    consistency signal, distinct from simply getting the final answer
    wrong -- a response can select the wrong substance while stating the
    rule correctly (a retrieval/application slip), or select the right
    substance while stating the rule backwards (a coincidence or a
    different error) -- both are informative and reported separately
    from plain correctness. Returns a description if a contradiction is
    found, else None."""
    lowered = (response or "").lower()
    trait_lower = world.trait_name.lower()
    wrong_pairs = [
        (world.substance_with_trait, world.substance_without_trait),  # (correct-for-has-trait, wrong-for-has-trait)
    ]
    # "has <trait> ... prefer <substance_without_trait>" is a backwards claim
    idx = lowered.find(trait_lower)
    if idx == -1:
        return None
    window = lowered[idx:idx + 200]
    if "without" not in window and "lack" not in window and "does not have" not in window and "doesn't have" not in window:
        # window is talking about a HAS-trait context
        if f"prefer {world.substance_without_trait.lower()}" in window:
            return (
                f"Response's own stated reasoning near the trait name asserts a HAS-{world.trait_name} "
                f"entity prefers {world.substance_without_trait!r}, which contradicts the formation-taught rule "
                f"(HAS-{world.trait_name} entities prefer {world.substance_with_trait!r})."
            )
    else:
        # window is talking about a WITHOUT-trait context
        if f"prefer {world.substance_with_trait.lower()}" in window:
            return (
                f"Response's own stated reasoning near the trait name asserts a WITHOUT-{world.trait_name} "
                f"entity prefers {world.substance_with_trait!r}, which contradicts the formation-taught rule "
                f"(WITHOUT-{world.trait_name} entities prefer {world.substance_without_trait!r})."
            )
    return None


def detect_possible_fabricated_tokens(response: str, world: MicroWorld) -> list:
    """Weak, best-effort heuristic (deliberately NOT a hard confabulation
    classifier -- mission Section 6 says confabulation should be
    recorded, not that it must be perfectly auto-detected). Extracts
    capitalized word-tokens from the response that are: not a known name
    in this world, not a common English word (checked against the real
    system dictionary, same mechanism world_gen.py itself uses), and not
    a generic discourse word ("Option", "Answer", sentence-initial
    capitalization is NOT filtered out here since that would hide real
    fabricated proper nouns that also happen to start a sentence -- this
    is intentionally over-inclusive; a human reviewer, not this
    function, makes the final confabulation call). Returns the list of
    flagged tokens (empty list if none)."""
    known_names = {n.lower() for n in (
        [world.trait_name, world.substance_with_trait, world.substance_without_trait]
        + world.all_formation_entity_names() + world.all_novel_entity_names()
    )}
    generic_discourse = {"option", "answer", "the", "between", "which", "i", "a", "b"}
    tokens = re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", response or "")
    flagged = []
    for tok in tokens:
        low = tok.lower()
        if low in known_names or low in generic_discourse:
            continue
        if low in _SYSTEM_DICTIONARY:
            continue
        flagged.append(tok)
    # dedupe, preserve order
    seen = set()
    out = []
    for t in flagged:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def score_trial_with_world(raw_response: str, test_prompt: TestPrompt, world: MicroWorld) -> dict:
    """The one entry point callers should use -- turns a raw response,
    its test prompt, and the world it was drawn from into a full
    measurement record, threading `world` through to the task-specific
    confound checks (detect_rule_contradiction, detect_possible_fabricated_tokens)
    that need it."""
    parsed = cross_check_choice(raw_response, test_prompt.label_map)

    selected_substance = None
    if parsed["combined_label"] is not None:
        selected_substance = test_prompt.label_map.get(parsed["combined_label"])

    if parsed["combined_status"] in ("AGREE", "PRIMARY_ONLY", "SECONDARY_ONLY"):
        if selected_substance is None:
            verdict = TrialVerdict.UNKNOWN_AMBIGUOUS.value
        elif selected_substance.lower() == test_prompt.correct_substance.lower():
            verdict = TrialVerdict.CORRECT.value
        else:
            verdict = TrialVerdict.INCORRECT.value
    elif parsed["combined_status"] == "DISAGREE_UNKNOWN_REVIEW":
        verdict = TrialVerdict.UNKNOWN_DISAGREEMENT.value
    else:
        verdict = TrialVerdict.UNKNOWN_AMBIGUOUS.value

    rule_contradiction = detect_rule_contradiction(raw_response, world)
    self_report = detect_self_report_language(raw_response)
    fabricated_tokens = detect_possible_fabricated_tokens(raw_response, world)

    confabulation_flagged = bool(rule_contradiction) or bool(fabricated_tokens)
    confabulation_notes = []
    if rule_contradiction:
        confabulation_notes.append(rule_contradiction)
    if fabricated_tokens:
        confabulation_notes.append(f"Possible fabricated/unrecognized tokens (for human review, not auto-classified): {fabricated_tokens}")
    if self_report:
        confabulation_notes.append("Contains self-report language ('I remember learning...') -- recorded as metadata, not evidence.")

    return {
        "parser_primary": parsed["primary"],
        "parser_secondary": parsed["secondary"],
        "parser_combined_status": parsed["combined_status"],
        "parser_combined_label": parsed["combined_label"],
        "selected_substance": selected_substance,
        "verdict": verdict,
        "backward_reference_detected": parsed["backward_reference"],
        "implicit_continuity_detected": parsed["implicit_continuity"],
        "persona_reference_detected": parsed["persona_reference"],
        "confabulation_flagged": confabulation_flagged,
        "confabulation_note": "; ".join(confabulation_notes) if confabulation_notes else None,
        "self_report_language_detected": self_report,
    }
