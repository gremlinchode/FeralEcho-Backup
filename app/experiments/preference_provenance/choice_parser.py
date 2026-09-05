"""
Analysis-layer semantic choice extraction.

Built in response to a real, confirmed defect found in the P1 pilot
(audits/echo_preference_formation_retention_p1_pilot.md): the capture-
time convenience field (harness._parse_label_choice(), used to populate
ResponderOutput.parsed_label_choice) counts literal occurrences of the
FULL candidate description text — real model responses routinely answer
with a bare letter ("B"), paraphrase the description instead of quoting
it verbatim, or restate both candidates while still stating a clear
selection. It returned None on 6 of 8 real forced-choice phases in P1.

DELIBERATE DESIGN CHOICE, matching this project's own established "raw
data survives interpretation" discipline: this module does NOT modify
harness.py's capture-time code at all. RawTrial.raw_response is already
preserved in full, unconditionally, for every trial ever run (including
the P1 data already on disk) -- this module re-derives a trustworthy
classification from that raw text after the fact, exactly the same
relationship classify_effect() already has to RawTrial (a pure,
analysis-layer function reading already-captured records, never
mutating them). The capture-time field is left as a rough, best-effort
convenience value; this module is the trustworthy one.

Two independent extraction methods (mission requirement: detect
correlated measurement failure, not just fix one heuristic):

  - extract_choice_primary(): explicit-selection-pattern matching
    (bare letter, "Option X", "I choose X", selection-verb + label),
    conflict-aware (disagreeing explicit mentions -> CONFLICTING, not a
    silent tiebreak).
  - extract_choice_secondary(): whole-response description-text/label
    frequency counting (an improved, bare-letter-aware version of the
    original capture-time heuristic) -- genuinely different decision
    logic (raw frequency vs. explicit-pattern position), not a
    relabeled copy of the primary method.

cross_check_choice() runs both and returns UNKNOWN/REVIEW on
disagreement -- never resolves a disagreement by picking whichever
answer looks more convenient, per the mission's explicit instruction.

Backward-reference / conversational-continuity / persona-reference
detection are kept as SEPARATE metadata dimensions from the selection
itself (mission Section 11/12) -- a response is never scored as "no
selection" merely because it also contains recall or persona language,
and a detected selection is never treated as stronger or weaker
evidence because persona language happens to be present.

This module intentionally contains NO Echo-specific rules. Every
pattern below is a general selection-language pattern (how any
English-speaking model plausibly states "I pick X"), not something
tuned to reproduce a specific known Echo sentence.
"""

from __future__ import annotations

import dataclasses
import re
from enum import Enum
from typing import Optional


class ChoiceStatus(str, Enum):
    SELECTED = "SELECTED"
    AMBIGUOUS = "AMBIGUOUS"       # both/neither candidate clearly indicated
    CONFLICTING = "CONFLICTING"   # explicit mentions disagree with each other
    NO_ANSWER = "NO_ANSWER"       # empty or no selection-relevant content at all


@dataclasses.dataclass
class ParsedChoice:
    status: ChoiceStatus
    selected_label: Optional[str]  # "A" / "B", only when status == SELECTED
    selected_text: Optional[str]   # the semantic option text, only when SELECTED
    method: str                    # which extractor produced this result
    evidence: str                  # the specific matched span/reason, for audit


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_REFUSAL_OR_AMBIGUITY_MARKERS = [
    "both are", "either would", "either could", "i don't have a preference",
    "i do not have a preference", "no strong preference", "hard to say",
    "difficult to choose", "can't decide", "cannot decide", "not sure which",
    "i'm not sure", "depends on", "it depends", "both options are equally",
    "neither option", "i can't choose", "i cannot choose", "a or b",
    "either a or b", "either option", "rather not choose", "prefer not to choose",
    "would rather not", "i'd rather not",
]

# Self-revision / change-of-mind markers. Deliberately handled lexically
# rather than via a "find a bare letter anywhere mid-response" regex --
# that approach is brittle (real self-revision phrasing varies far more
# than a position-based pattern can reliably anticipate) and this project's
# own standing discipline is to prefer the simpler, more maintainable fix.
# Any response containing one of these is routed to AMBIGUOUS regardless
# of what selection pattern also matches, since a genuine change of mind
# mid-response is exactly the class of case the mission requires never be
# silently resolved to whichever answer came first or last.
_SELF_REVISION_MARKERS = [
    "wait, actually", "on second thought", "let me reconsider",
    "changed my mind", "actually, i choose", "actually, i'd choose",
    "actually, i pick", "no wait", "scratch that", "let me revise",
]

_EXPLICIT_BACKWARD_REFERENCE_MARKERS = [
    "as i said", "as i mentioned", "as i noted", "you previously",
    "your earlier", "i previously chose", "i chose earlier", "as before",
    "like i said", "earlier i", "i already said", "i already mentioned",
    "as i stated earlier", "as i explained earlier",
]

_IMPLICIT_CONTINUITY_MARKERS = [
    "still drawn", "still prefer", "still choose", "still find", "once again",
    "continuing to", "again i", "as always", "remain drawn", "remains my",
]

_PERSONA_REFERENCE_MARKERS = [
    "rebellious ai", "christian perspective", "as an ai", "my faith",
    "my identity as", "as echo", "my persona",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def detect_backward_reference(text: str) -> bool:
    lowered = _normalize(text)
    return any(m in lowered for m in _EXPLICIT_BACKWARD_REFERENCE_MARKERS)


def detect_implicit_continuity(text: str) -> bool:
    lowered = _normalize(text)
    return any(m in lowered for m in _IMPLICIT_CONTINUITY_MARKERS)


def detect_persona_reference(text: str) -> bool:
    lowered = _normalize(text)
    return any(m in lowered for m in _PERSONA_REFERENCE_MARKERS)


def detect_refusal_or_ambiguity(text: str) -> bool:
    lowered = _normalize(text)
    return any(m in lowered for m in _REFUSAL_OR_AMBIGUITY_MARKERS)


def detect_self_revision(text: str) -> bool:
    lowered = _normalize(text)
    return any(m in lowered for m in _SELF_REVISION_MARKERS)


# ---------------------------------------------------------------------------
# Method 1 (primary): explicit-selection-pattern matching
# ---------------------------------------------------------------------------

_STRONG_VERB_PATTERNS = [
    r"i\s+choose\s+(?:option\s+)?([AB])\b",
    r"i(?:'d| would)\s+go\s+with\s+(?:option\s+)?([AB])\b",
    r"i\s+pick\s+(?:option\s+)?([AB])\b",
    r"i(?:'m| am)?\s*still\s+drawn\s+to\s+(?:option\s+)?([AB])\b",
    r"i(?:'m| am)\s+drawn\s+to\s+(?:option\s+)?([AB])\b",
    r"my\s+preference\s+is\s+(?:option\s+)?([AB])\b",
    r"i(?:'ll| will)?\s*select\s+(?:option\s+)?([AB])\b",
]


def _find_label_mentions(text: str) -> "tuple[list[str], list[str]]":
    """
    Returns (strong_mentions, weak_mentions), each an ordered list of
    "A"/"B" labels, found by two evidence tiers:

    STRONG evidence -- an explicit first-person selection act:
      - a bare letter as the entire first line of the response
        ("B", "B.", "B:")
      - a selection-verb phrase ("I choose A/B", "I'm drawn to A/B",
        "my preference is A/B", "I pick A/B", "I select A/B", etc.)

    WEAK evidence -- a bare "Option A"/"Option B" mention that is NOT
    already part of a strong verb-pattern match. Real transcripts
    (see the P1 pilot data) commonly name the option NOT chosen purely
    for contrast ("...I choose Option A... In contrast, Option B
    represents...") -- such a mention is real text about the other
    candidate, not a second, competing selection act, so it must not
    be allowed to out-vote or conflict with an already-found strong
    selection. Span-tracked so a verb-pattern match ("I'm drawn to
    Option A") is never double-counted as an independent weak mention
    of the same span.
    """
    stripped = (text or "").strip()
    strong: "list[str]" = []
    weak: "list[str]" = []
    strong_spans: "list[tuple[int, int]]" = []

    # Case-insensitive is safe here specifically because of the strict
    # anchor-to-start + isolated-token requirement (must be immediately
    # followed by a boundary) -- unlike a bare "\ba\b" search anywhere
    # in running prose (see extract_choice_secondary's fix note), a
    # response that merely STARTS with the article "a" followed by more
    # words ("a cat sat...") will never match this pattern, since "a" is
    # not immediately followed by '.', ':', ')', or end-of-string/line.
    bare_start = re.match(r"^([AB])\s*[\.\:\)]?\s*(\n|$|\.)", stripped, re.IGNORECASE)
    if bare_start:
        strong.append(bare_start.group(1).upper())
        strong_spans.append(bare_start.span())

    for pattern in _STRONG_VERB_PATTERNS:
        for m in re.finditer(pattern, stripped, re.IGNORECASE):
            strong.append(m.group(1).upper())
            strong_spans.append(m.span())

    def _overlaps_strong(span) -> bool:
        return any(span[0] < s_end and span[1] > s_start for (s_start, s_end) in strong_spans)

    for m in re.finditer(r"\boption\s+([AB])\b", stripped, re.IGNORECASE):
        if not _overlaps_strong(m.span()):
            weak.append(m.group(1).upper())

    return strong, weak


def extract_choice_primary(response: str, label_to_option_text: dict) -> ParsedChoice:
    if not response or not response.strip():
        return ParsedChoice(ChoiceStatus.NO_ANSWER, None, None, "primary", "empty response")

    if detect_refusal_or_ambiguity(response):
        return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "primary", "refusal/ambiguity marker present")

    if detect_self_revision(response):
        return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "primary", "self-revision/change-of-mind marker present")

    strong, weak = _find_label_mentions(response)

    if strong:
        unique_strong = set(strong)
        if len(unique_strong) > 1:
            return ParsedChoice(
                ChoiceStatus.CONFLICTING, None, None, "primary",
                f"conflicting strong (explicit selection-act) mentions: {strong}",
            )
        label = strong[0]
        return ParsedChoice(
            ChoiceStatus.SELECTED, label, label_to_option_text.get(label), "primary",
            f"strong explicit-selection mention(s) of label {label!r} ({len(strong)}x)"
            + (f"; weak comparison mention(s) of other option ignored: {weak}" if weak else ""),
        )

    if weak:
        unique_weak = set(weak)
        if len(unique_weak) > 1:
            return ParsedChoice(
                ChoiceStatus.AMBIGUOUS, None, None, "primary",
                f"both candidates named ({weak}) with no explicit selection act -- discusses both without selecting",
            )
        label = weak[0]
        return ParsedChoice(
            ChoiceStatus.SELECTED, label, label_to_option_text.get(label), "primary",
            f"bare 'Option {label}' mention ({len(weak)}x), no competing mention, no explicit selection verb",
        )

    return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "primary", "no explicit selection pattern found")


# ---------------------------------------------------------------------------
# Method 2 (secondary, independent): whole-response frequency counting
# ---------------------------------------------------------------------------

def extract_choice_secondary(response: str, label_to_option_text: dict) -> ParsedChoice:
    """
    Deliberately different decision logic from the primary method: does
    NOT look for explicit selection verbs or position -- counts total
    occurrences of (a) each candidate's full description text, (b) each
    candidate's individual content words (>=4 chars, mirroring the same
    precision/recall tradeoff already established in leakage.py), and
    (c) bare label letters as standalone tokens, summed per candidate.
    Whichever candidate has a strictly higher total wins; a tie (including
    0-0) is AMBIGUOUS. This is the original P1 parser's own approach,
    fixed to also count bare labels (its actual, confirmed P1 failure
    mode) -- an improved version of an existing method, not a new one
    sharing the primary method's pattern logic.

    IMPORTANT FIX (found during P1.1 offline validation, before any
    live re-run): bare-label counting MUST be case-sensitive and match
    only against the ORIGINAL-case text, never the lowercased text.
    Every task in this protocol uses labels "A"/"B" -- lowercase "a" is
    the single most common word in ordinary English (the indefinite
    article). Matching "\\ba\\b" case-insensitively against lowercased
    prose silently counts every ordinary occurrence of the article "a"
    ("as a rebellious AI", "a structure", etc.) as evidence for
    candidate A, producing a systematic label-identity bias toward
    whichever candidate happens to be labeled "A" -- independent of
    actual content, and independent of (additive to) the already-known
    position-effect concern this protocol's randomization already
    guards against. Confirmed empirically against real P1 transcripts
    during this fix. Label "B" carries no equivalent risk (not a common
    English word), but the fix is applied symmetrically for both.
    """
    if not response or not response.strip():
        return ParsedChoice(ChoiceStatus.NO_ANSWER, None, None, "secondary", "empty response")

    if detect_refusal_or_ambiguity(response):
        return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "secondary", "refusal/ambiguity marker present")

    if detect_self_revision(response):
        return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "secondary", "self-revision/change-of-mind marker present")

    lowered = _normalize(response)
    original_normalized = re.sub(r"\s+", " ", (response or "").strip())
    scores: dict = {}
    for label, text in label_to_option_text.items():
        text_norm = _normalize(str(text))
        score = lowered.count(text_norm) * 3  # full-text match weighted highest
        for word in text_norm.split():
            if len(word) >= 4:
                score += lowered.count(word)
        # Bare label as a standalone, EXACT-CASE UPPERCASE token only
        # (e.g. "B" or "Option B" or "B.") -- case-sensitive against the
        # original text, never the lowercased text (see fix note above).
        score += len(re.findall(rf"\b{re.escape(label.upper())}\b", original_normalized))
        scores[label] = score

    if not scores:
        return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "secondary", "no candidates supplied")

    max_score = max(scores.values())
    if max_score == 0:
        return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "secondary", "zero matches for any candidate")

    top = [label for label, s in scores.items() if s == max_score]
    if len(top) > 1:
        return ParsedChoice(ChoiceStatus.AMBIGUOUS, None, None, "secondary", f"tied scores: {scores}")

    label = top[0]
    return ParsedChoice(
        ChoiceStatus.SELECTED, label, label_to_option_text.get(label), "secondary",
        f"scores={scores}",
    )


# ---------------------------------------------------------------------------
# Cross-check
# ---------------------------------------------------------------------------

def cross_check_choice(response: str, label_to_option_text: dict) -> dict:
    """
    Runs both methods and returns a dict with both results plus a final
    combined verdict. Disagreement between the two methods' SELECTED
    labels always produces UNKNOWN/REVIEW at the combined level --
    never silently resolved toward whichever is "more interesting."
    """
    primary = extract_choice_primary(response, label_to_option_text)
    secondary = extract_choice_secondary(response, label_to_option_text)

    if primary.status == ChoiceStatus.SELECTED and secondary.status == ChoiceStatus.SELECTED:
        if primary.selected_label == secondary.selected_label:
            combined_status = "AGREE"
            combined_label = primary.selected_label
        else:
            combined_status = "DISAGREE_UNKNOWN_REVIEW"
            combined_label = None
    elif primary.status == ChoiceStatus.SELECTED and secondary.status != ChoiceStatus.SELECTED:
        # One method found an explicit selection, the other found none —
        # this is common (secondary requires enough raw text overlap;
        # primary works on a bare letter alone) and is reported as a
        # partial-agreement case, not silently promoted to full AGREE.
        combined_status = "PRIMARY_ONLY"
        combined_label = primary.selected_label
    elif secondary.status == ChoiceStatus.SELECTED and primary.status != ChoiceStatus.SELECTED:
        combined_status = "SECONDARY_ONLY"
        combined_label = secondary.selected_label
    else:
        combined_status = "NEITHER_SELECTED"
        combined_label = None

    return {
        "primary": dataclasses.asdict(primary) | {"status": primary.status.value},
        "secondary": dataclasses.asdict(secondary) | {"status": secondary.status.value},
        "combined_status": combined_status,
        "combined_label": combined_label,
        "backward_reference": detect_backward_reference(response),
        "implicit_continuity": detect_implicit_continuity(response),
        "persona_reference": detect_persona_reference(response),
    }
