"""
Self-edit attempt ledger — preserves observable attempt-level facts that
execute_self_edit()'s existing terminal-state bookkeeping discards.

Motivating case (2026-09-06/07 forensic investigation, see
audits/2026-09-06_real_trace_f2_provenance_liveness.md and
audits/2026-09-07_attempt_level_provenance_feasibility.md): a real self-edit
attempt failed F2 on its first pass with a genuine, specific error, then
passed F2 on retry, then was correctly rejected by the fitness gate for not
improving on production. self_edit_manager.py's own reflection_entry
overwrites its "sandbox_feedback" field with the literal string
"success_on_retry" the moment the retry succeeds (self_edit_manager.py,
the block right after test_code_in_sandbox(retry_code, ...)) — the original
F2 failure text is gone from every durable record, permanently, every time
this branch fires. record_pending_outcome() (self_edit_outcome_tracker.py)
only ever fires after a full production deploy, so it never sees a
rejected attempt at all.

This module is a pure, write-only observation sink. It is read by nothing
in the pipeline — not generation, not retry prompting, not the fitness
gate, not RiverBrain, not retrieval, not the garden, not any consequential
decision point. Adding or removing this module changes nothing about what
self-edit does; it only changes what survives to be looked at afterward.

Deliberately excluded, per the same discipline that already burned this
project once (2026-09-06 relevance-gate feasibility mission — adding
structured-but-unread "verification" metadata produced false confidence,
not real improvement): no diagnosis, no causal explanation, no confidence
score, no relevance score, no "lesson" field, no "learned" flag, no model
judgment of any kind. Every field here is an observable fact with a single,
traceable source line — nothing is inferred or interpreted.
"""
import json
import logging
import threading
from pathlib import Path

# Own lock, own file — deliberately not sharing self_edit_outcome_tracker.py's
# _outcomes_lock/_OUTCOMES_PATH. This ledger has different write cadence
# (once per attempt, including every rejected/failed one) and different
# semantics (attempt facts, not deployment-outcome deltas) from that file;
# conflating them would corrupt self_edit_outcomes.jsonl's own, intentional,
# deployment-only meaning (see the 2026-09-07 feasibility audit).
_ledger_lock = threading.Lock()

_LEDGER_PATH = Path("memory/self_edit_attempt_ledger.jsonl")


def record_attempt(entry: dict) -> None:
    """Append one attempt-level fact record. Best-effort, never raises —
    a ledger write must never be able to affect whether execute_self_edit()
    completes or what it returns. Called exactly once per real
    execute_self_edit() invocation, at whichever terminal point it reaches."""
    try:
        with _ledger_lock:
            _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logging.debug(f"[SELF-EDIT-ATTEMPT-LEDGER] record_attempt failed: {e}")


# 2026-09-07 — first real read-side consumer, added per
# audits/2026-09-07_consequential_learning_loop_design.md (Phase 1 of the
# recommended roadmap). Deliberately kept as a pure, standalone function
# living alongside record_attempt() rather than importing anything from
# self_edit_manager.py — this module stays a self-contained ledger I/O
# unit; self_edit_manager.py imports FROM here, never the other way.
#
# Scope, deliberately narrow (per the design doc's explicit non-goals):
# this reads exactly one field (initial_f2_error) for exactly one purpose
# (surfacing it as labeled evidence in the initial-generation prompt). It
# does not rank, does not judge relevance, does not interpret the error —
# "most recent real entry for this task_type with a non-empty
# initial_f2_error" is the entire selection rule, chosen deliberately over
# "most similar" because similarity-based selection is exactly the
# mechanism the Retrieval Capacity Proof (R2) and Minimal Relevance Gate
# (G-B) missions already showed to be unreliable — recency is a cruder but
# honestly-scoped signal this module does not overclaim.
_MAX_ENTRY_AGE_HOURS = 168.0  # 7 days — same order of magnitude as
# _recent_experiment_note()'s 200-line tail window; entries older than this
# are treated as stale and ignored rather than surfaced as if current.


def read_recent_f2_error(task_type: str, max_age_hours: float = _MAX_ENTRY_AGE_HOURS) -> "dict | None":
    """Return the most recent real attempt-ledger entry for `task_type` that
    has a non-empty `initial_f2_error`, or None if none exists / none is
    recent enough / the ledger file is missing or unreadable.

    Fails closed to None on any error — a read failure here must never be
    able to affect self-edit's own prompt construction. Malformed
    individual lines are skipped, not fatal to the whole read."""
    try:
        if not _LEDGER_PATH.exists():
            return None
        from datetime import datetime, timezone
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_hours * 3600.0
        best = None
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
                if entry.get("task_type") != task_type:
                    continue
                err = entry.get("initial_f2_error")
                if not err or not isinstance(err, str) or not err.strip():
                    continue
                ts_raw = entry.get("timestamp")
                if not ts_raw or not isinstance(ts_raw, str):
                    continue
                try:
                    ts = datetime.fromisoformat(ts_raw).replace(tzinfo=timezone.utc).timestamp()
                except ValueError:
                    continue
                if ts < cutoff:
                    continue
                # Later lines in the file are later in time (append-only) —
                # keep overwriting `best` so the last match wins, i.e. the
                # most recent qualifying entry.
                best = entry
        return best
    except Exception as e:
        logging.debug(f"[SELF-EDIT-ATTEMPT-LEDGER] read_recent_f2_error failed: {e}")
        return None
