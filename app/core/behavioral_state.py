# app/core/behavioral_state.py
# ============================================================
# BEHAVIORAL DIRECTIVE STORE — Candidate 1 from
# audits/p3_1_l2_mechanism_design.md, implemented per
# P3.1-IMPLEMENT-C1.
#
# THIS IS NOT A LEARNING MECHANISM. It is a small, bounded,
# human-confirmed, deterministically-triggered directive store.
# No autonomous mutation exists anywhere in this file. No
# similarity search, no embeddings, no FAISS, no RiverBrain
# dependency of any kind (verified directly by this module's own
# import list below and re-checked in the accompanying test suite).
#
# CAUSAL SHAPE (mission requirement, reproduced here so the shape
# is visible at the top of the one file that implements it):
#   EXPERIENCE
#     -> explicit proposed directive (caller-supplied, already
#        distilled -- this module never sees or stores the
#        original verbatim teaching exchange)
#     -> HUMAN APPROVAL (a literal, explicit human_confirmed=True;
#        refuses construction/mutation otherwise, mirroring the
#        sibling preference-provenance package's own
#        EchoDirectResponder(acknowledge_live_model_call=True)
#        convention)
#     -> DERIVED STATE (only trigger_keywords + directive_text are
#        persisted -- never the teaching exchange itself)
#     -> PERSIST (atomic temp-file + os.replace, this project's own
#        established convention)
#     -> RESTART (a fresh process re-reads the file from disk;
#        this module holds no module-level cache across imports)
#     -> DETERMINISTIC READ (exact/substring keyword match only,
#        never embedding similarity)
#     -> [existing generation slice mechanism, wired in
#        app/core/echo_ground_truth.py -- NOT this file's
#        responsibility]
#     -> BEHAVIOR
#
# Every mutation and every matched read is logged, with explicit
# provenance, to a separate append-only audit file.
# ============================================================

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

_MEMORY_DIR = "memory"
_STATE_PATH = os.path.join(_MEMORY_DIR, "behavioral_directives.json")
_BACKUP_DIR = os.path.join(_MEMORY_DIR, "behavioral_directives_backups")
_AUDIT_LOG_PATH = os.path.join(_MEMORY_DIR, "behavioral_directives_audit.jsonl")

# Bounds (mission requirement #11: bounded number/size of directives).
# Small and deliberately conservative -- this is a minimal mechanism,
# not a general-purpose knowledge store.
MAX_DIRECTIVES = 20
MAX_TRIGGER_KEYWORDS_PER_DIRECTIVE = 5
MAX_TRIGGER_KEYWORD_LEN = 60
MAX_DIRECTIVE_TEXT_LEN = 300
MAX_BACKUPS_RETAINED = 10

_SCHEMA_VERSION = 1


class BehavioralStateError(RuntimeError):
    """Raised on any human-confirmation failure, bound violation, or
    malformed input. Never raised silently swallowed by this module --
    callers see exactly why a mutation was refused."""


def _ensure_dirs() -> None:
    os.makedirs(_MEMORY_DIR, exist_ok=True)
    os.makedirs(_BACKUP_DIR, exist_ok=True)


def _atomic_write_json(path: str, data: dict) -> None:
    _ensure_dirs()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _append_audit(event: dict) -> None:
    """Full audit logging of mutation/read/provenance (mission
    requirement #15). Best-effort -- a logging failure must never
    block or corrupt the actual state mutation/read it describes,
    matching this project's own established 'instrumentation never
    blocks the real computation' convention."""
    try:
        _ensure_dirs()
        record = {"timestamp": time.time(), **event}
        with open(_AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception as e:
        logger.warning("[BehavioralState] Failed to write audit log entry: %s", e)


def load_state() -> dict:
    """Fresh read from disk every call -- no module-level cache, so
    a restarted process (or this same process calling this function
    again after an external mutation) always sees current, real
    on-disk state. Returns an empty, valid schema if the file does
    not exist yet."""
    if not os.path.exists(_STATE_PATH):
        return {"version": _SCHEMA_VERSION, "directives": []}
    try:
        with open(_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "directives" not in data:
            logger.warning("[BehavioralState] Malformed state file, treating as empty.")
            return {"version": _SCHEMA_VERSION, "directives": []}
        return data
    except Exception as e:
        logger.warning("[BehavioralState] Failed to read state file: %s", e)
        return {"version": _SCHEMA_VERSION, "directives": []}


def _backup_current_state_before_mutation() -> Optional[str]:
    """Rollback path (mission requirement #14): before every mutation,
    the CURRENT on-disk state (if any) is copied to a timestamped
    backup file. Returns the backup path, or None if there was no
    existing state to back up."""
    if not os.path.exists(_STATE_PATH):
        return None
    _ensure_dirs()
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup_path = os.path.join(_BACKUP_DIR, f"behavioral_directives_{ts}_{uuid.uuid4().hex[:8]}.json")
    with open(_STATE_PATH, "r", encoding="utf-8") as src:
        content = src.read()
    with open(backup_path, "w", encoding="utf-8") as dst:
        dst.write(content)
    _prune_backups()
    return backup_path


def _prune_backups() -> None:
    if not os.path.isdir(_BACKUP_DIR):
        return
    files = sorted(
        (f for f in os.listdir(_BACKUP_DIR) if f.startswith("behavioral_directives_") and f.endswith(".json")),
    )
    excess = len(files) - MAX_BACKUPS_RETAINED
    for f in files[:max(0, excess)]:
        try:
            os.remove(os.path.join(_BACKUP_DIR, f))
        except OSError:
            pass


def list_backups() -> "list[str]":
    """Returns available backup filenames, oldest first, for rollback."""
    if not os.path.isdir(_BACKUP_DIR):
        return []
    return sorted(
        f for f in os.listdir(_BACKUP_DIR) if f.startswith("behavioral_directives_") and f.endswith(".json")
    )


def rollback_to_backup(backup_filename: str, *, human_confirmed: bool) -> dict:
    """Explicit rollback path (mission requirement #14). Requires the
    same explicit human confirmation as any other mutation -- rollback
    is itself a mutation of live state."""
    if human_confirmed is not True:
        raise BehavioralStateError(
            "rollback_to_backup() requires human_confirmed=True (the literal bool True). "
            "This mutation was refused."
        )
    backup_path = os.path.join(_BACKUP_DIR, backup_filename)
    if not os.path.exists(backup_path):
        raise BehavioralStateError(f"No such backup: {backup_filename!r}")
    with open(backup_path, "r", encoding="utf-8") as f:
        restored = json.load(f)
    # Back up whatever is currently live before overwriting it, same as any other mutation
    pre_rollback_backup = _backup_current_state_before_mutation()
    _atomic_write_json(_STATE_PATH, restored)
    _append_audit({
        "event": "rollback",
        "restored_from": backup_filename,
        "pre_rollback_backup": pre_rollback_backup,
        "human_confirmed": True,
    })
    return restored


def delete_directive(directive_id: str, *, human_confirmed: bool) -> bool:
    """Explicit delete path. Requires human confirmation. Returns True
    if a directive was found and removed, False if no matching id
    existed (not an error -- deleting something already absent is a
    no-op, not a failure)."""
    if human_confirmed is not True:
        raise BehavioralStateError(
            "delete_directive() requires human_confirmed=True (the literal bool True). "
            "This mutation was refused."
        )
    state = load_state()
    before_count = len(state["directives"])
    state["directives"] = [d for d in state["directives"] if d["id"] != directive_id]
    removed = len(state["directives"]) < before_count
    if removed:
        _backup_current_state_before_mutation()
        _atomic_write_json(_STATE_PATH, state)
        _append_audit({"event": "delete", "directive_id": directive_id, "human_confirmed": True})
    return removed


def propose_and_confirm_directive(
    *,
    trigger_keywords: "list[str]",
    directive_text: str,
    provenance: dict,
    human_confirmed: bool,
) -> dict:
    """The ONLY way new state enters this store. Requires explicit
    human confirmation (mission requirement #3) -- refuses outright
    otherwise, no autonomous fallback path exists anywhere in this
    module.

    `trigger_keywords` and `directive_text` must already be the
    DERIVED, distilled representation -- this function has no
    parameter for, and never accepts, the original verbatim teaching
    exchange (mission requirement #4). Distillation is the CALLER's
    responsibility; this function's job is only to persist the
    already-derived result with explicit provenance (mission
    requirement #5).

    `provenance` must be a caller-supplied dict describing WHO
    proposed this and WHY (e.g. {"proposed_by": "gremlin",
    "reason": "...", "source_conversation_ref": "<opaque id, not the
    text itself>"}) -- required, not optional, and persisted verbatim
    alongside the directive.
    """
    if human_confirmed is not True:
        raise BehavioralStateError(
            "propose_and_confirm_directive() requires human_confirmed=True (the literal bool True). "
            "This mutation was refused -- no directive was stored."
        )
    if not trigger_keywords or not isinstance(trigger_keywords, list):
        raise BehavioralStateError("trigger_keywords must be a non-empty list of strings.")
    if len(trigger_keywords) > MAX_TRIGGER_KEYWORDS_PER_DIRECTIVE:
        raise BehavioralStateError(
            f"trigger_keywords has {len(trigger_keywords)} entries, max is {MAX_TRIGGER_KEYWORDS_PER_DIRECTIVE}."
        )
    for kw in trigger_keywords:
        if not isinstance(kw, str) or not kw.strip():
            raise BehavioralStateError("Every trigger keyword must be a non-empty string.")
        if len(kw) > MAX_TRIGGER_KEYWORD_LEN:
            raise BehavioralStateError(f"Trigger keyword {kw!r} exceeds max length {MAX_TRIGGER_KEYWORD_LEN}.")
    if not directive_text or not isinstance(directive_text, str):
        raise BehavioralStateError("directive_text must be a non-empty string.")
    if len(directive_text) > MAX_DIRECTIVE_TEXT_LEN:
        raise BehavioralStateError(f"directive_text exceeds max length {MAX_DIRECTIVE_TEXT_LEN}.")
    if not provenance or not isinstance(provenance, dict):
        raise BehavioralStateError("provenance must be a non-empty dict describing who/why this was proposed.")

    state = load_state()
    if len(state["directives"]) >= MAX_DIRECTIVES:
        raise BehavioralStateError(
            f"Store already holds the maximum of {MAX_DIRECTIVES} directives. "
            f"Delete an existing directive before adding a new one."
        )

    directive_id = str(uuid.uuid4())
    new_directive = {
        "id": directive_id,
        "trigger_keywords": [kw.strip().lower() for kw in trigger_keywords],
        "directive_text": directive_text.strip(),
        "provenance": provenance,
        "created_at": time.time(),
    }
    _backup_current_state_before_mutation()
    state["directives"].append(new_directive)
    state["version"] = _SCHEMA_VERSION
    _atomic_write_json(_STATE_PATH, state)
    _append_audit({
        "event": "propose_and_confirm",
        "directive_id": directive_id,
        "trigger_keywords": new_directive["trigger_keywords"],
        "directive_text": new_directive["directive_text"],
        "provenance": provenance,
        "human_confirmed": True,
    })
    return new_directive


def get_matching_directives(prompt: str) -> "list[dict]":
    """The ONLY read path. Deterministic, bounded, exact-substring
    keyword matching against the CURRENT prompt text -- no embedding
    similarity, no FAISS, no RiverBrain, no fuzzy/semantic matching of
    any kind (mission requirements #6, #7, #8, #9). Returns matches in
    a deterministic order (mission requirement #12): directive
    creation order (the order they appear in the persisted list),
    never randomized, never similarity-ranked.

    Every matched read is logged for provenance (mission requirement
    #15) -- a non-match is NOT logged, to avoid an unbounded audit
    log growing on every single ordinary prompt; only genuine
    directive activations are recorded.
    """
    if not prompt:
        return []
    state = load_state()
    lowered = prompt.lower()
    matches = []
    for directive in state["directives"]:
        if any(kw in lowered for kw in directive["trigger_keywords"]):
            matches.append(directive)
    if matches:
        # sha256, not Python's built-in hash() -- the latter is randomized
        # per-process (PYTHONHASHSEED) and would never be comparable across
        # a restart, defeating the point of an audit trail. NEVER the raw
        # prompt text itself -- see module docstring.
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
        _append_audit({
            "event": "read_match",
            "matched_directive_ids": [d["id"] for d in matches],
            "prompt_hash": prompt_hash,
        })
    return matches
