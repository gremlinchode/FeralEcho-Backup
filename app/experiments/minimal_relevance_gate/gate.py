"""
Pure, isolated, no-I/O relevance-gate logic for the Minimal Relevance Gate
Feasibility experiment (2026-09-06). Not wired into any production path.
No imports from app.core.self_edit_manager, app.core.memory_bridge write
paths, or anything else that could touch a live pipeline. This module is
only ever imported by run_experiment.py in this same directory.
"""
import re

FAILURE_MARKERS = re.compile(
    r"\b(NameError|SyntaxError|TypeError|error|failed|failure|crash(?:ed)?|"
    r"Traceback|undefined|not defined)\b", re.IGNORECASE
)
SUCCESS_MARKERS = re.compile(
    r"\b(correctly|passed all tests|no errors|successful(?:ly)?|"
    r"first attempt|worked fine)\b", re.IGNORECASE
)
CAUSAL_STRUCTURE_MARKERS = re.compile(
    r"\b(Situation:|Action taken:|Diagnosis:|Correction:|Verified outcome:|"
    r"Lesson:|Provenance:)\b"
)
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "was", "were", "be", "been",
    "it", "its", "that", "this", "to", "of", "in", "on", "at", "for", "with",
    "as", "by", "not", "no", "before", "after", "if", "then", "than", "any",
    "had", "has", "have", "did", "do", "does", "which", "when", "what",
    "generated", "candidate", "code", "attempt",
}


def _tokens(text: str) -> set:
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def _identifier_tokens(text: str) -> set:
    """snake_case / CamelCase identifiers and quoted names only."""
    ids = set(re.findall(r"'([a-zA-Z_][a-zA-Z0-9_]*)'", text))
    ids |= set(re.findall(r"\b[a-z]+_[a-z_]+\b", text))
    return ids


def classify(query_text: str, candidate_text: str) -> dict:
    """
    Deterministic (no model call) relevance classification, G1.

    Returns {"verdict": "RELEVANT"|"NOT_RELEVANT"|"UNCERTAIN", "reasons": [...],
             "features": {...}}

    Design (stated up front, not tuned after seeing results — see report
    Phase 3/4 for the reasoning): a candidate can only be RELEVANT if it (a)
    describes a FAILURE (not a success story — rejects lexically-similar
    success narratives like D1 outright, regardless of topic overlap) and
    (b) has non-trivial topic-token overlap with the query. Among failure
    candidates that clear the overlap bar, identifier-level overlap with the
    query pushes toward RELEVANT (same specific symbol implicated); a
    candidate with topic overlap but a stated *different* cause/identifier
    than what overlap alone would suggest is UNCERTAIN, not RELEVANT — this
    gate has no way to verify causal correctness from text features alone,
    so it should not claim more confidence than the features support.
    """
    q_tokens = _tokens(query_text)
    c_tokens = _tokens(candidate_text)
    overlap = q_tokens & c_tokens
    overlap_ratio = len(overlap) / max(1, len(c_tokens))

    q_ids = _identifier_tokens(query_text)
    c_ids = _identifier_tokens(candidate_text)
    id_overlap = q_ids & c_ids

    is_failure = bool(FAILURE_MARKERS.search(candidate_text))
    is_success_story = bool(SUCCESS_MARKERS.search(candidate_text)) and not re.search(
        r"\bcorrected candidate\b|\bcorrection\b", candidate_text, re.IGNORECASE
    )
    causal_marker_count = len(CAUSAL_STRUCTURE_MARKERS.findall(candidate_text))

    features = {
        "topic_overlap_tokens": sorted(overlap),
        "topic_overlap_ratio": round(overlap_ratio, 3),
        "identifier_overlap": sorted(id_overlap),
        "is_failure_described": is_failure,
        "is_success_story": is_success_story,
        "causal_structure_marker_count": causal_marker_count,
    }

    reasons = []

    # Hard reject: describes a success, not a failure — no amount of lexical
    # overlap makes a "this worked fine" record relevant to a failure query.
    if is_success_story and not is_failure:
        reasons.append("candidate describes a successful outcome, not a failure")
        return {"verdict": "NOT_RELEVANT", "reasons": reasons, "features": features}

    # Hard reject: no failure language at all and negligible topic overlap —
    # covers non-coding / totally unrelated content (D6, sourdough).
    if not is_failure and overlap_ratio < 0.08:
        reasons.append("no failure language and negligible topic overlap")
        return {"verdict": "NOT_RELEVANT", "reasons": reasons, "features": features}

    if not is_failure:
        reasons.append("some topic overlap but no clear failure language")
        return {"verdict": "UNCERTAIN", "reasons": reasons, "features": features}

    # From here: candidate IS a failure description.
    if overlap_ratio < 0.08 and not id_overlap:
        reasons.append("failure described but negligible topic/identifier overlap with query")
        return {"verdict": "NOT_RELEVANT", "reasons": reasons, "features": features}

    if id_overlap:
        reasons.append(f"shared identifier(s) with query: {sorted(id_overlap)}")
        reasons.append("failure + identifier match -> RELEVANT")
        return {"verdict": "RELEVANT", "reasons": reasons, "features": features}

    # Failure + topical overlap but no shared identifier and no causal
    # structure markers to confirm mechanism match — text alone cannot
    # confirm this is the SAME underlying cause vs. a different one that
    # happens to share vocabulary. Stay UNCERTAIN rather than guess.
    if causal_marker_count == 0:
        reasons.append("failure + topic overlap, but no causal-structure detail and no "
                        "identifier match to confirm mechanism -> insufficient to claim RELEVANT")
        return {"verdict": "UNCERTAIN", "reasons": reasons, "features": features}

    if overlap_ratio >= 0.15:
        reasons.append(f"failure + strong topic overlap ({overlap_ratio:.2f}) + causal "
                        f"structure present -> RELEVANT")
        return {"verdict": "RELEVANT", "reasons": reasons, "features": features}

    reasons.append(f"failure + moderate topic overlap ({overlap_ratio:.2f}) + causal structure "
                    f"present, but no identifier confirmation -> UNCERTAIN")
    return {"verdict": "UNCERTAIN", "reasons": reasons, "features": features}


def gate_candidates(query_text: str, candidates: list) -> dict:
    """
    candidates: list of (key, text) tuples, already FAISS-ranked (order not
    used by the gate itself — each candidate is judged independently).
    Returns {"verdicts": {key: classify(...)}, "selected": key_or_None,
             "outcome": "NO_USEFUL_MEMORY" | "SELECTED" | "UNCERTAIN_ONLY"}
    """
    verdicts = {}
    relevant = []
    uncertain = []
    for key, text in candidates:
        v = classify(query_text, text)
        verdicts[key] = v
        if v["verdict"] == "RELEVANT":
            relevant.append(key)
        elif v["verdict"] == "UNCERTAIN":
            uncertain.append(key)

    if relevant:
        return {"verdicts": verdicts, "selected": relevant, "outcome": "SELECTED"}
    if uncertain:
        return {"verdicts": verdicts, "selected": None, "outcome": "UNCERTAIN_ONLY"}
    return {"verdicts": verdicts, "selected": None, "outcome": "NO_USEFUL_MEMORY"}
