# app/core/self_model_claims.py
# ============================================================
# SELF-MODEL CLAIMS LEDGER
#
# 2026-09-08 — built per audits/2026-09-08_persistent_self_model_DESIGN.md
# and audits/2026-09-08_living_self_model_design.md. Closes the exact gap
# both audits found: a conversational architectural correction currently
# has nowhere durable to go. self_model.json (SelfModelUpdater) is rebuilt
# every ~130s from background telemetry ONLY — no code path takes a
# conversational claim as input. self_knowledge_verification.py's
# verify_self_knowledge_claims() correctly evaluates self-referential
# claims in real time but is purely stateless: it appends a caveat to one
# response and persists nothing.
#
# This module is a pure, append-only observation sink for VERIFIED (or
# explicitly contradicted) self-knowledge claims — same shape and same
# discipline as self_edit_attempt_ledger.py's record_attempt(): fail-
# silent, never able to affect the caller's own control flow, read by
# nothing that can turn it into unearned authority.
#
# Critical invariant, enforced structurally, not by convention:
# proposed_by != verified_by. Echo's own text is never the verifier.
# record_claim() takes a `verified` bool that must come from an
# independent check (self_knowledge_verification.py's own ground-truth
# comparisons, or a future equivalent) — never from parsing Echo's stated
# confidence. There is no function here that lets a caller mark a claim
# verified without supplying independent evidence.
# ============================================================
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_LEDGER_PATH = Path("memory/self_model_claims.jsonl")

# Deliberately small and explicit — see the design doc's Phase 5/6
# discussion of why this stays a narrow, curated set rather than an open
# vocabulary. Each key is a canonical subject name; the value is the exact
# dotted path (self_model.json) whose presence/truthiness the claim's
# `verified` bool should already have been checked against by the caller.
# This module does not read self_model.json itself -- it only records
# what a caller (which did the real check) reports. Keeping this dict here
# is documentation, not enforcement; the enforcement is that callers must
# supply `verified` themselves. (See self_knowledge_verification.py's
# Check 5 -- the one real caller as of this writing.)
KNOWN_SUBJECTS = {
    "RiverBrain": "river_brain.total_observations",
    "self_edit_pipeline": "self_edit.total_attempts",
    "liveness_ledger": "verified_capabilities.checks",
    "curiosity_engine": "verified_capabilities.checks.curiosity_engine",
    "world_model": "world_model.accuracy",
}


def record_claim(
    subject: str,
    verified: bool,
    evidence: str,
    proposed_by: str = "echo_response",
    verified_by: str = "self_knowledge_verification",
) -> None:
    """Append one claim record. Best-effort, never raises -- a ledger
    write must never be able to affect response generation. `verified`
    must be supplied by the caller's own independent check; this function
    performs no verification of its own and trusts nothing from Echo's
    text directly."""
    if proposed_by == verified_by:
        # Structural guard: a claim's own proposer can never also be its
        # verifier, even if a future caller passes matching strings by
        # mistake. Refuse silently rather than persist a self-certified
        # "fact" -- same fail-closed posture as the rest of this module.
        logger.debug(
            "[SELF-MODEL-CLAIMS] refused: proposed_by == verified_by (%r)", proposed_by
        )
        return
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subject": subject,
        "verified": bool(verified),
        "evidence": evidence,
        "proposed_by": proposed_by,
        "verified_by": verified_by,
    }
    try:
        with _lock:
            _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.debug("[SELF-MODEL-CLAIMS] record_claim failed: %s", e)


def get_recent_claims(subject: "str | None" = None, limit: int = 5) -> "list[dict]":
    """Most recent claim records, optionally filtered to one subject.
    Fails closed to [] on any error -- a read failure here must never be
    able to affect prompt construction. Ordered oldest-to-newest within
    the returned slice (matches record_attempt's own JSONL append order),
    so a caller display "most recent last" is the natural iteration order."""
    try:
        if not _LEDGER_PATH.exists():
            return []
        out: "list[dict]" = []
        with open(_LEDGER_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not isinstance(entry, dict):
                    continue
                if subject is not None and entry.get("subject") != subject:
                    continue
                out.append(entry)
        return out[-limit:]
    except Exception as e:
        logger.debug("[SELF-MODEL-CLAIMS] get_recent_claims failed: %s", e)
        return []
