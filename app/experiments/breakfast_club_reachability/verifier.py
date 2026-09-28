"""
Deterministic, non-LLM verifier for the Breakfast Club reachability proof
(mission Phase 4, P6 / Phase 5's "Only demonstrated downstream use plus
deterministic verification may support VERIFIED"). Never calls any model,
never makes a network call. Given a nonce, an envelope, and a claimed
answer, independently recomputes the frozen transformation and checks
message-identity/freshness -- this module is the ONLY code path in this
experiment permitted to declare a match.
"""
from __future__ import annotations

from . import protocol


def verify(*, envelope: dict, response_message_id: str, claimed_answer: "str | None") -> dict:
    """Returns a result dict with an explicit `outcome` in
    {"VERIFIED", "REJECTED_MISMATCH", "REJECTED_WRONG_MESSAGE_ID",
     "REJECTED_STALE", "REJECTED_EMPTY_OR_MALFORMED"} -- never a bare bool,
    so a caller can never accidentally collapse "wrong for a structural
    reason" and "wrong because the math didn't match" into one signal."""
    nonce_hex = envelope["nonce_hex"]
    message_id = envelope["message_id"]

    if response_message_id != message_id:
        return {"outcome": "REJECTED_WRONG_MESSAGE_ID", "message_id": message_id,
                "response_message_id": response_message_id}

    if protocol.is_expired(envelope["expiry"]):
        return {"outcome": "REJECTED_STALE", "message_id": message_id,
                "expiry": envelope["expiry"]}

    if not claimed_answer or not claimed_answer.strip():
        return {"outcome": "REJECTED_EMPTY_OR_MALFORMED", "message_id": message_id,
                "claimed_answer_raw": claimed_answer}

    cleaned = claimed_answer.strip().lower()
    # Strict shape check first (16 lowercase hex chars) -- a response that
    # merely LOOKS plausible but isn't well-formed is a distinct failure
    # class from "well-formed but wrong," per the mission's own Phase 7
    # requirement to distinguish malformed from incorrect.
    if len(cleaned) != 16 or any(c not in "0123456789abcdef" for c in cleaned):
        return {"outcome": "REJECTED_EMPTY_OR_MALFORMED", "message_id": message_id,
                "claimed_answer_raw": claimed_answer, "claimed_answer_cleaned": cleaned}

    expected = protocol.expected_answer(nonce_hex)
    if cleaned != expected:
        return {"outcome": "REJECTED_MISMATCH", "message_id": message_id,
                "expected_answer": expected, "claimed_answer_cleaned": cleaned}

    return {"outcome": "VERIFIED", "message_id": message_id,
            "expected_answer": expected, "claimed_answer_cleaned": cleaned}
