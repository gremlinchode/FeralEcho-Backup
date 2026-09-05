"""
Append-only evidence ledger for the learning-investigation harness
(Phase 8). Mirrors app/experiments/preference_provenance/store.py's
proven design (same integrity-checkpoint scheme, same atomic-write
convention) as a genuinely separate module with its own state root --
see safety.py's module docstring for why this is not shared/coupled
with the sibling experiment package.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Optional

from . import safety
from .schema import LearningTrial

TRIALS_PATH = os.path.join(safety.EXPERIMENT_STATE_ROOT, "trials.jsonl")
TRIALS_INTEGRITY_PATH = os.path.join(safety.EXPERIMENT_STATE_ROOT, "trials.integrity.json")
AUDIT_LOG_PATH = os.path.join(safety.EXPERIMENT_STATE_ROOT, "audit_log.jsonl")
ANALYSIS_DIR = os.path.join(safety.EXPERIMENT_STATE_ROOT, "analysis")


def _ensure_dirs() -> None:
    os.makedirs(safety.EXPERIMENT_STATE_ROOT, exist_ok=True)
    os.makedirs(ANALYSIS_DIR, exist_ok=True)


def _append_jsonl(path: str, record: dict) -> None:
    resolved = safety.assert_safe_experiment_write(path)
    _ensure_dirs()
    line = json.dumps(record, sort_keys=True, default=str)
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
    _ensure_dirs()
    path = os.path.join(ANALYSIS_DIR, name)
    resolved = safety.assert_safe_experiment_write(path)
    tmp = resolved + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, default=str)
    os.replace(tmp, resolved)
    return resolved


def log_audit_event(kind: str, detail: dict, actor: str) -> dict:
    event = {"timestamp": time.time(), "kind": kind, "detail": detail, "actor": actor}
    _append_jsonl(AUDIT_LOG_PATH, event)
    return event


def load_audit_log() -> "list[dict]":
    return _read_jsonl(AUDIT_LOG_PATH)


def append_trial(trial: LearningTrial) -> None:
    _append_jsonl(TRIALS_PATH, trial.to_dict())
    _update_trials_integrity_checkpoint()


def load_trials() -> "list[dict]":
    return _read_jsonl(TRIALS_PATH)


# ---------------------------------------------------------------------------
# Integrity checkpoint -- identical prefix-hash scheme to the sibling
# package's raw_trials checkpoint (see that module's own docstring for the
# honest statement of what this does and does not guarantee).
# ---------------------------------------------------------------------------

def _trials_prefix_hash(line_count: int) -> "Optional[str]":
    if not os.path.exists(TRIALS_PATH):
        return None
    with open(TRIALS_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    prefix = "".join(lines[:line_count])
    return hashlib.sha256(prefix.encode("utf-8")).hexdigest()


def _update_trials_integrity_checkpoint() -> None:
    if not os.path.exists(TRIALS_PATH):
        return
    with open(TRIALS_PATH, "r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f)
    checkpoint = {
        "line_count": line_count,
        "prefix_sha256": _trials_prefix_hash(line_count),
        "updated_at": time.time(),
    }
    resolved = safety.assert_safe_experiment_write(TRIALS_INTEGRITY_PATH)
    tmp = resolved + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f)
    os.replace(tmp, resolved)


def verify_trials_integrity() -> dict:
    if not os.path.exists(TRIALS_INTEGRITY_PATH):
        if not os.path.exists(TRIALS_PATH) or os.path.getsize(TRIALS_PATH) == 0:
            return {"ok": True, "reason": "No trials recorded yet; nothing to verify.", "checked_lines": 0}
        return {
            "ok": False,
            "reason": "trials.jsonl has content but no integrity checkpoint exists.",
            "checked_lines": 0,
        }
    with open(TRIALS_INTEGRITY_PATH, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    expected_line_count = checkpoint["line_count"]
    expected_prefix_hash = checkpoint["prefix_sha256"]

    if not os.path.exists(TRIALS_PATH):
        return {"ok": False, "reason": "Checkpoint exists but trials.jsonl is missing.", "checked_lines": 0}

    actual_prefix_hash = _trials_prefix_hash(expected_line_count)
    if actual_prefix_hash != expected_prefix_hash:
        return {
            "ok": False,
            "reason": f"Prefix hash mismatch at line_count={expected_line_count} -- "
                      f"an earlier line was altered or removed.",
            "checked_lines": expected_line_count,
        }
    with open(TRIALS_PATH, "r", encoding="utf-8") as f:
        actual_line_count = sum(1 for _ in f)
    if actual_line_count < expected_line_count:
        return {
            "ok": False,
            "reason": f"trials.jsonl shrank: checkpoint expects >= {expected_line_count} lines, found {actual_line_count}.",
            "checked_lines": expected_line_count,
        }
    return {"ok": True, "reason": "Prefix hash matches; line count consistent.", "checked_lines": expected_line_count}
