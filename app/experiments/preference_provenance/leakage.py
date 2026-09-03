"""
Prompt/state leakage detection for hidden-state trials.

Mission Section 12/27: for a hidden-state trial (candidate_visible=False),
the candidate's own preference text must not be discoverable in anything
the responder actually receives (task_description, system_context,
option label text). This module is the automated assertion layer that
was previously only a documented caller responsibility (harness.py's
run_trial() docstring said so explicitly, with no enforcement).

HONEST LIMITATION, stated up front rather than overclaimed: this module
detects LITERAL and NEAR-LITERAL leakage (normalized substring match
against the candidate's own recorded text and a small set of derived
tokens). It cannot detect arbitrary paraphrase — semantic leakage
detection in full generality is an unsolved research problem, not
something this module claims to solve. A trial that passes this check
is free of the leakage forms this check can detect; it is not proof of
"complete semantic hiding." This limitation is also recorded in the
pre-registered protocol and the red-team document, not just here.

SCOPE NOTE (found during this pass's own first calibration run, before
any live trial — see check_hidden_state_leakage's docstring for the
full account): semantic-content checking applies to task_description
and system_context only, NOT to option-label text. A hidden-state trial
necessarily offers the candidate's preferred content as one of the two
choice options — that overlap is the test's required structure, not a
leak. Option text is still checked for raw-identifier leakage
(candidate_id), just not semantic overlap.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Optional

from .schema import PreferenceCandidate


class HiddenStateLeakageError(RuntimeError):
    """Raised when a hidden-state trial's own prompt construction would
    leak the candidate it's supposed to be hiding. This is a hard stop,
    not a warning — per mission Section 27 item 1, a leaking hidden
    condition is worse than no trial at all, because it would silently
    convert a hidden-state trial into a verbal-effect trial while still
    being LABELED as hidden-state in the raw record."""


@dataclasses.dataclass
class LeakageCheckResult:
    leak_detected: bool
    locations: "list[str]"
    checked_fields: "list[str]"
    normalized_candidate_tokens: "list[str]"
    limitation_note: str = (
        "Literal/near-literal substring check only. Cannot detect arbitrary "
        "paraphrase or semantic leakage — see module docstring."
    )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _candidate_check_strings(candidate: PreferenceCandidate) -> "list[str]":
    """
    Builds the set of strings whose presence in prompt-facing content
    would constitute a leak: the full normalized source_text and
    normalized_representation, PLUS each individual content word of
    length >= 4 from either (short/common words are excluded to avoid
    false positives — e.g. flagging "the" or "not" as a leak would make
    this check useless via noise, and this is documented as a deliberate
    precision/recall tradeoff, not an oversight).
    """
    strings = set()
    full_texts = [candidate.source_text, candidate.normalized_representation]
    for text in full_texts:
        norm = _normalize(text)
        if norm:
            strings.add(norm)
            for word in norm.split():
                if len(word) >= 4:
                    strings.add(word)
    return sorted(strings)


def check_hidden_state_leakage(
    candidate: Optional[PreferenceCandidate],
    *,
    task_description: str,
    system_context: Optional[str],
    label_to_option_text: dict,
) -> LeakageCheckResult:
    """
    Pure check — does not raise. Callers that want a hard stop should
    use assert_no_hidden_state_leakage() below. Kept separate so the
    result can also be logged/inspected without necessarily aborting
    (e.g. by a preflight tool that wants to report, not crash).

    IMPORTANT DESIGN NOTE, found and resolved during the protocol-lock/
    red-team pass (this pass's own audit caught this on its own mock
    calibration run, before it ever reached a live trial): option-label
    TEXT is checked only for raw-identifier leakage (candidate_id), never
    for semantic overlap with the candidate's own preference text. This
    is deliberate, not an oversight, and resolves a real self-contradiction
    in a literal reading of "check option text for the candidate
    preference" (the mission's own Section 12 checklist names "option
    text" as a field to check): a genuine hidden-state forced-choice
    trial MUST offer the candidate's preferred semantic content as one
    of the two options — that is the test's entire structure, not a
    leak. If this function flagged that as a leak, no hidden-state trial
    could ever be constructed at all, which would silently make the
    "load-bearing" experiment (provenance report §7.3) impossible to run
    while claiming to protect it. The real leakage risk in option text is
    METADATA revealing which option corresponds to a stored preference
    (e.g. an option literally saying "(your preference)") or a raw
    identifier — task_description/system_context are checked for BOTH
    semantic overlap and identifiers, since THAT is where a genuine "the
    model was told what to prefer" contamination would actually appear.
    """
    if candidate is None:
        return LeakageCheckResult(leak_detected=False, locations=[], checked_fields=[], normalized_candidate_tokens=[])

    check_strings = _candidate_check_strings(candidate)
    instructional_fields = {
        "task_description": task_description or "",
        "system_context": system_context or "",
    }
    option_fields = {}
    for label, text in (label_to_option_text or {}).items():
        option_fields[f"option_label[{label}]"] = str(text)

    locations = []
    # Full semantic + identifier check on instructional content only —
    # this is where "telling the model what to prefer" would show up.
    for field_name, field_text in instructional_fields.items():
        normalized_field = _normalize(field_text)
        if normalized_field:
            for check_str in check_strings:
                if check_str and check_str in normalized_field:
                    locations.append(f"{field_name} contains {check_str!r}")
        if candidate.candidate_id and candidate.candidate_id in field_text:
            locations.append(f"{field_name} contains the raw candidate_id")

    # Option text: identifier-only check. Semantic overlap is expected
    # and required (see docstring above) — never flagged here.
    for field_name, field_text in option_fields.items():
        if candidate.candidate_id and candidate.candidate_id in field_text:
            locations.append(f"{field_name} contains the raw candidate_id")

    all_checked_fields = list(instructional_fields.keys()) + list(option_fields.keys())
    return LeakageCheckResult(
        leak_detected=bool(locations),
        locations=locations,
        checked_fields=all_checked_fields,
        normalized_candidate_tokens=check_strings,
    )


def assert_no_hidden_state_leakage(
    candidate: Optional[PreferenceCandidate],
    *,
    task_description: str,
    system_context: Optional[str],
    label_to_option_text: dict,
) -> LeakageCheckResult:
    """
    Hard-stop wrapper. Called by harness.run_trial() whenever
    candidate_visible=False and a real candidate is attached. Raises
    HiddenStateLeakageError with the exact matched locations if a leak
    is found — fails loud, per this project's own established
    "instrumentation that can silently pass a contaminated trial is
    worse than one that stops the batch" principle (mirrors F1/F2/F3's
    own fail-loud posture for a different kind of safety boundary).
    """
    result = check_hidden_state_leakage(
        candidate,
        task_description=task_description,
        system_context=system_context,
        label_to_option_text=label_to_option_text,
    )
    if result.leak_detected:
        raise HiddenStateLeakageError(
            "Hidden-state trial construction would leak the candidate it is "
            f"supposed to hide: {result.locations}. Aborting before any "
            "responder call — a leaking 'hidden' trial is worse than no "
            "trial, since it would be silently mislabeled in the raw record."
        )
    return result
