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
