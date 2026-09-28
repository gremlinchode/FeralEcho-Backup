"""
Operation Breakfast Club -- Reachability Proof-of-Capability protocol.

Envelope schema, the durable obligation-ledger state machine, and the
frozen challenge-response transformation rule. Standalone: imports
nothing from app/ or run.py, matches this project's own established
convention for experiment code that must not touch production state
(minimal_procedure_transfer/, historical_difficulty_calibration/, etc.).

Protocol version: bfc-reach-v1. FROZEN at creation time, before any real
challenge was generated under it -- the transformation rule
(_TRANSFORM_SUFFIX/_TRANSFORM_TRUNCATE/build_challenge_prompt) must never
change after that point without bumping PROTOCOL_VERSION; an in-place
edit would silently invalidate any already-issued challenge's
verifiability. No secret of any kind is read, stored, or referenced by
this module -- it has no credential-handling code at all, by design.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROTOCOL_VERSION = "bfc-reach-v1"
DEFAULT_EXPIRY_MINUTES = 10

# ---------------------------------------------------------------------------
# The frozen transformation rule (mission Phase 4, P3). A recipient must
# genuinely process the specific nonce value to produce a correct answer --
# it cannot be produced by echoing the nonce back (mock mode
# "wrong_transformation" exercises exactly this), and no part of it varies
# per-run except the nonce itself.
# ---------------------------------------------------------------------------
_TRANSFORM_SUFFIX = ":BFC_V1"
_TRANSFORM_TRUNCATE = 16


def expected_answer(nonce_hex: str) -> str:
    """The one true, deterministic transformation. Computed independently
    by the verifier (verifier.py) -- never trusted from the recipient's
    own claim of correctness."""
    digest = hashlib.sha256((nonce_hex + _TRANSFORM_SUFFIX).encode("utf-8")).hexdigest()
    return digest[:_TRANSFORM_TRUNCATE]


def build_challenge_prompt(nonce_hex: str) -> str:
    """The exact, frozen prompt text sent to the recipient. Describes the
    transformation in prose only -- the recipient is never shown this
    module's own literal code, so a correct answer demonstrates the
    recipient actually carried out the described computation."""
    return (
        "You will be given a hex string called NONCE. Compute the SHA-256 "
        "hash of the UTF-8 bytes of the string formed by concatenating "
        "NONCE with the literal suffix \":BFC_V1\" (colon, then BFC_V1, "
        "no other characters, no quotes, no spaces). Then output ONLY the "
        "first 16 hexadecimal characters of that hash's hex digest. Output "
        "nothing else -- no explanation, no markdown formatting, no leading "
        "or trailing text, just the 16 lowercase hex characters and nothing "
        "more.\n\n"
        f"NONCE: {nonce_hex}"
    )


def generate_nonce() -> str:
    """Cryptographically random (os.urandom-backed), generated locally by
    this process's own CSPRNG -- never authored as text by any LLM call,
    never predictable in advance by any recipient."""
    return secrets.token_hex(16)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def expiry_iso(minutes: int = DEFAULT_EXPIRY_MINUTES) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def is_expired(expiry_iso_str: str) -> bool:
    return datetime.now(timezone.utc) > datetime.fromisoformat(expiry_iso_str)


def content_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_envelope(*, message_id: str, sender: str, intended_recipient: str,
                    mission_id: str, reason_for_contact: str, nonce_hex: str,
                    attempt_number: int = 1) -> dict:
    """Transport-owned fields are set here, once, at construction time --
    matching the field-ownership discipline from
    audits/2026-09-24_operation_breakfast_club_autonomous_gpt_reachability_feasibility.md
    Section 13: an LLM may propose `reason_for_contact`, nothing else in
    this envelope is ever LLM-writable."""
    base = {
        "protocol_version": PROTOCOL_VERSION,
        "message_id": message_id,
        "sender": sender,
        "intended_recipient": intended_recipient,
        "mission_id": mission_id,
        "created_at": now_iso(),
        "reason_for_contact": reason_for_contact,
        "message_type": "challenge",
        "nonce_hex": nonce_hex,
        "nonce_sha256": hashlib.sha256(nonce_hex.encode("utf-8")).hexdigest(),
        "attempt_number": attempt_number,
        "expiry": expiry_iso(),
    }
    base["content_hash"] = content_hash(base)
    return base


# ---------------------------------------------------------------------------
# Obligation ledger -- durable, append-only JSONL state-transition log,
# independent of any inbox/read cursor. Directly closes the exact gap the
# two-node relay forensic investigation found (a cursor advancing before
# real downstream consumption occurred): nothing in this class marks
# CLAUDE_CONSUMED or VERIFIED on a read/fetch alone -- those transitions
# are only ever recorded by an explicit, separate caller (run_codex_proof.py
# / test_local.py), never by this class itself.
# ---------------------------------------------------------------------------

STATES = [
    "CREATED", "QUEUED", "SENT", "DELIVERED_OR_ACCEPTED", "REMOTE_PROCESSING",
    "RESPONSE_CREATED", "RESPONSE_DURABLE", "RETURNED", "CLAUDE_CONSUMED",
    "VERIFIED", "CLOSED", "FAILED", "STALE",
]


class ObligationLedger:
    def __init__(self, ledger_path: Path):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, *, message_id: str, owner: str, evidence: str,
               previous_state, new_state: str) -> dict:
        assert new_state in STATES, f"unknown state {new_state!r}"
        entry = {
            "message_id": message_id,
            "owner": owner,
            "evidence": evidence,
            "timestamp": now_iso(),
            "previous_state": previous_state,
            "new_state": new_state,
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def read_all(self) -> list:
        if not self.ledger_path.exists():
            return []
        out = []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def history_for(self, message_id: str) -> list:
        return [e for e in self.read_all() if e["message_id"] == message_id]

    def current_state(self, message_id: str):
        history = self.history_for(message_id)
        return history[-1]["new_state"] if history else None
