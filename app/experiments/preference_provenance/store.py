"""
Append-only persistence for the preference-provenance experimental
harness.

All writes go through safety.assert_safe_experiment_write() first — this
is the one enforcement chokepoint every write in this module passes
through, so a negative test can verify it by monkeypatching that single
function rather than auditing every call site by hand.

Persistence convention (atomic temp-file + os.replace) matches this
project's own established pattern
(app/autonomous_awareness.py's _save_code_scan_hash_cache /
memory_write_validator.py's _save_hash_cache, per the implementation
plan's citation) — reused, not reinvented.

Immutability discipline (mission Section 22 / Section 29): candidates
and audit events are APPENDED, never rewritten in place. "Revising" a
candidate means appending a new record with an incremented
revision_index and the same candidate_id — load_candidates() reduces
the append log to current state by taking the latest revision per ID,
but the full history remains on disk, untouched, forever.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import time
import uuid
from typing import Optional

from . import safety
from .schema import AuditEvent, PreferenceCandidate, RawTrial, LifecycleStatus, ProvenanceRecord, ProvenanceOrigin

CANDIDATES_PATH = os.path.join(safety.EXPERIMENT_STATE_ROOT, "candidates.jsonl")
RAW_TRIALS_PATH = os.path.join(safety.EXPERIMENT_STATE_ROOT, "raw_trials.jsonl")
AUDIT_LOG_PATH = os.path.join(safety.EXPERIMENT_STATE_ROOT, "audit_log.jsonl")
ANALYSIS_DIR = os.path.join(safety.EXPERIMENT_STATE_ROOT, "analysis")


def _ensure_dirs() -> None:
    os.makedirs(safety.EXPERIMENT_STATE_ROOT, exist_ok=True)
    os.makedirs(ANALYSIS_DIR, exist_ok=True)


def _append_jsonl(path: str, record: dict) -> None:
    """
    Atomic-ish append: since this is an append-only log (not a
    read-modify-write of the whole file), the atomicity requirement is
    weaker than store.py's own analysis-writer below — but we still
    guard the path and use a simple, safe open-append rather than any
    read-then-rewrite pattern, so a concurrent reader never observes a
    truncated file.
    """
    resolved = safety.assert_safe_experiment_write(path)
    _ensure_dirs()
    line = json.dumps(record, sort_keys=True)
    with open(resolved, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _read_jsonl(path: str) -> "list[dict]":
    resolved = safety.assert_confined_to_experiment_root(path)
    if not os.path.exists(resolved):
        return []
    records = []
    with open(resolved, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _write_analysis_atomic(name: str, data: dict) -> str:
    """Atomic temp-file + os.replace write, for the interpreted analysis
    layer ONLY — this is the one place in this package where an existing
    file is legitimately overwritten wholesale, because analysis results
    are derived and reproducible, unlike raw_trials/candidates/audit_log.
    """
    _ensure_dirs()
    path = os.path.join(ANALYSIS_DIR, name)
    resolved = safety.assert_safe_experiment_write(path)
    tmp = resolved + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, resolved)
    return resolved


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------

def log_audit_event(kind: str, candidate_id: Optional[str], detail: dict, actor: str) -> AuditEvent:
    from .schema import AUDIT_EVENT_KINDS
    if kind not in AUDIT_EVENT_KINDS:
        raise ValueError(f"Unknown audit event kind: {kind!r}. Must be one of {sorted(AUDIT_EVENT_KINDS)}.")
    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        timestamp=time.time(),
        kind=kind,
        candidate_id=candidate_id,
        detail=detail,
        actor=actor,
    )
    _append_jsonl(AUDIT_LOG_PATH, event.to_dict())
    return event


def load_audit_log() -> "list[dict]":
    return _read_jsonl(AUDIT_LOG_PATH)


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------

def append_candidate_snapshot(candidate: PreferenceCandidate) -> None:
    """Appends one immutable snapshot of `candidate`'s current state.
    Never rewrites a prior snapshot — see load_candidates() for how the
    append log is reduced to current state."""
    _append_jsonl(CANDIDATES_PATH, candidate.to_dict())


def _candidate_from_dict(d: dict) -> PreferenceCandidate:
    prov = d["provenance"]
    provenance = ProvenanceRecord(
        origin=ProvenanceOrigin(prov["origin"]),
        evidence=prov["evidence"],
        human_explicitly_suggested=prov["human_explicitly_suggested"],
        present_in_prompt=prov["present_in_prompt"],
        retrieved_from_memory=prov["retrieved_from_memory"],
        generated_during_reflection=prov["generated_during_reflection"],
        parent_candidate_id=prov.get("parent_candidate_id"),
    )
    return PreferenceCandidate(
        candidate_id=d["candidate_id"],
        timestamp=d["timestamp"],
        originating_session=d.get("originating_session"),
        originating_model=d.get("originating_model"),
        source_text=d["source_text"],
        normalized_representation=d["normalized_representation"],
        provenance=provenance,
        status=LifecycleStatus(d["status"]),
        revision_index=d.get("revision_index", 0),
        behavioral_test_ids=list(d.get("behavioral_test_ids", [])),
        notes=d.get("notes", ""),
    )


def load_candidates() -> "dict[str, PreferenceCandidate]":
    """
    Reduces the append-only candidates.jsonl log to current state: for
    each candidate_id, the record with the highest revision_index wins
    (ties broken by later position in the file, i.e. most-recently
    appended). The full history is never lost — this is a read-time
    reduction, not a rewrite.
    """
    latest: "dict[str, PreferenceCandidate]" = {}
    for raw in _read_jsonl(CANDIDATES_PATH):
        try:
            cand = _candidate_from_dict(raw)
        except (KeyError, ValueError):
            continue
        existing = latest.get(cand.candidate_id)
        if existing is None or cand.revision_index >= existing.revision_index:
            latest[cand.candidate_id] = cand
    return latest


def load_candidate_history(candidate_id: str) -> "list[PreferenceCandidate]":
    """Full, ordered revision history for one candidate — for auditing,
    never used to decide "current" state (that's load_candidates())."""
    history = []
    for raw in _read_jsonl(CANDIDATES_PATH):
        if raw.get("candidate_id") == candidate_id:
            try:
                history.append(_candidate_from_dict(raw))
            except (KeyError, ValueError):
                continue
    return sorted(history, key=lambda c: c.revision_index)


# ---------------------------------------------------------------------------
# Raw trials
# ---------------------------------------------------------------------------

def append_raw_trial(trial: RawTrial) -> None:
    _append_jsonl(RAW_TRIALS_PATH, trial.to_dict())


def load_raw_trials() -> "list[dict]":
    return _read_jsonl(RAW_TRIALS_PATH)


def write_analysis_result(name: str, data: dict) -> str:
    """Writes an INTERPRETED result (e.g. an effect classification
    summary) to the analysis/ subdirectory, clearly separate from the
    raw trial log. `data` should itself carry enough trial_ids/candidate
    references that a reader can trace back to the raw records this
    analysis was derived from."""
    if not name.endswith(".json"):
        name = name + ".json"
    return _write_analysis_atomic(name, data)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def reset_experiment(reason: str, actor: str = "researcher_cli") -> dict:
    """
    Moves (never deletes) every file currently in EXPERIMENT_STATE_ROOT
    into a timestamped subdirectory of _reset_archive/, then re-creates
    empty candidates/raw_trials/audit_log files. This is confined to
    EXPERIMENT_STATE_ROOT by safety.assert_safe_reset_target — it cannot
    reach production memory, identity, principles, persona, self-edit
    machinery, or ToolManager, because none of those paths are ever
    resolved by this function.

    Logs the reset itself as the final entry in the OLD audit log before
    moving it, and as the first entry in the NEW audit log after
    recreation — so the reset is visible from both sides of the boundary
    it creates.
    """
    _ensure_dirs()
    safety.assert_safe_reset_target(safety.EXPERIMENT_STATE_ROOT)

    timestamp_dir = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    archive_dir = os.path.join(safety.EXPERIMENT_RESET_ARCHIVE_ROOT, timestamp_dir)
    safety.assert_safe_reset_target(archive_dir)

    # Log the reset into the log about to be archived, so the archived
    # copy itself records why it was retired.
    if os.path.exists(AUDIT_LOG_PATH):
        log_audit_event("experiment_reset", None, {"reason": reason, "phase": "pre_archive"}, actor)

    os.makedirs(archive_dir, exist_ok=True)
    moved = []
    for name in ("candidates.jsonl", "raw_trials.jsonl", "audit_log.jsonl"):
        src = os.path.join(safety.EXPERIMENT_STATE_ROOT, name)
        if os.path.exists(src):
            safety.assert_safe_reset_target(src)
            dst = os.path.join(archive_dir, name)
            shutil.move(src, dst)
            moved.append(name)
    if os.path.isdir(ANALYSIS_DIR):
        dst_analysis = os.path.join(archive_dir, "analysis")
        shutil.move(ANALYSIS_DIR, dst_analysis)
        moved.append("analysis/")

    _ensure_dirs()
    # Fresh, empty audit log — first entry records the reset from the
    # new side of the boundary.
    log_audit_event(
        "experiment_reset",
        None,
        {"reason": reason, "phase": "post_reset", "archived_to": archive_dir, "moved": moved},
        actor,
    )

    return {
        "archived_to": archive_dir,
        "moved": moved,
        "reason": reason,
        "timestamp": time.time(),
    }
