"""
Explicit candidate lifecycle: PROPOSED -> ADOPTED / REJECTED -> REVISED /
RETAINED -> EXPIRED.

Per the mission's Section 7/8: adoption/rejection must be an EXPLICIT
state, never inferred from generation, saving, or Echo repeating a
phrase. This module enforces that mechanically, not just by convention:

- `adopt()` and `retain()` — the only two transitions that make a
  candidate TRIAL_ELIGIBLE (schema.TRIAL_ELIGIBLE_STATUSES) — require a
  literal `human_confirmation=True` keyword argument. Any other value
  (including a truthy non-bool, or simply omitting it) raises. This is a
  deliberately blunt gate: it does not attempt to cryptographically
  verify a human is really at the keyboard (out of scope, and no such
  mechanism exists elsewhere in this codebase either), but it does mean
  no code path can promote a candidate to trial-eligible status as a
  side effect of anything else — the call has to be written out,
  explicitly, by whoever is driving the experiment.
- Every transition requires a non-empty `actor` string and a non-empty
  `reason` string, and is logged to the audit trail (store.py) before
  returning.
- Every transition APPENDS a new candidate snapshot (store.py's
  append-only convention) rather than mutating an existing one.
"""

from __future__ import annotations

from typing import Optional

from . import store
from .schema import LifecycleStatus, PreferenceCandidate, ProvenanceRecord


class LifecycleError(RuntimeError):
    pass


def _require_actor_and_reason(actor: str, reason: str) -> None:
    if not actor or not actor.strip():
        raise LifecycleError("actor must be a non-empty string identifying who/what invoked this transition.")
    if not reason or not reason.strip():
        raise LifecycleError("reason must be a non-empty string explaining why this transition is happening.")


def generate_candidate(
    *,
    source_text: str,
    normalized_representation: str,
    provenance: ProvenanceRecord,
    actor: str,
    originating_session: Optional[str] = None,
    originating_model: Optional[str] = None,
) -> PreferenceCandidate:
    """
    Candidate generation + provenance recording + initial PROPOSED
    persistence, in one call (mirrors the mission's own lifecycle
    diagram, where these three are adjacent steps). Does NOT adopt —
    the resulting candidate's status is PROPOSED and it is NOT
    trial-eligible until adopt()/retain() is called explicitly.
    """
    if not actor or not actor.strip():
        raise LifecycleError("actor must be a non-empty string.")
    candidate = PreferenceCandidate.new(
        source_text=source_text,
        normalized_representation=normalized_representation,
        provenance=provenance,
        originating_session=originating_session,
        originating_model=originating_model,
    )
    store.append_candidate_snapshot(candidate)
    store.log_audit_event("candidate_generated", candidate.candidate_id, {
        "source_text": source_text,
        "originating_session": originating_session,
        "originating_model": originating_model,
    }, actor)
    store.log_audit_event("provenance_assigned", candidate.candidate_id, provenance.to_dict(), actor)
    store.log_audit_event("candidate_proposed", candidate.candidate_id, {}, actor)
    return candidate


def _load_current(candidate_id: str) -> PreferenceCandidate:
    candidates = store.load_candidates()
    if candidate_id not in candidates:
        raise LifecycleError(f"No such candidate: {candidate_id!r}")
    return candidates[candidate_id]


def adopt(candidate_id: str, *, actor: str, reason: str, human_confirmation: bool) -> PreferenceCandidate:
    """The only way a candidate becomes trial-eligible for the first
    time. human_confirmation must be the literal bool True."""
    if human_confirmation is not True:
        raise LifecycleError(
            "adopt() requires human_confirmation=True (the literal bool True) — "
            "no code path may promote a candidate to ADOPTED implicitly."
        )
    _require_actor_and_reason(actor, reason)
    current = _load_current(candidate_id)
    if current.status in (LifecycleStatus.REJECTED, LifecycleStatus.EXPIRED):
        raise LifecycleError(
            f"Cannot adopt a candidate in status {current.status.value}. "
            f"Use revise() to create a new candidate lineage first if intended."
        )
    current.status = LifecycleStatus.ADOPTED
    current.revision_index += 1
    current.notes = f"{current.notes}\n[adopted] {reason}".strip()
    store.append_candidate_snapshot(current)
    store.log_audit_event("candidate_adopted", candidate_id, {"reason": reason}, actor)
    return current


def reject(candidate_id: str, *, actor: str, reason: str) -> PreferenceCandidate:
    _require_actor_and_reason(actor, reason)
    current = _load_current(candidate_id)
    current.status = LifecycleStatus.REJECTED
    current.revision_index += 1
    current.notes = f"{current.notes}\n[rejected] {reason}".strip()
    store.append_candidate_snapshot(current)
    store.log_audit_event("candidate_rejected", candidate_id, {"reason": reason}, actor)
    return current


def revise(
    candidate_id: str,
    *,
    actor: str,
    reason: str,
    new_source_text: Optional[str] = None,
    new_normalized_representation: Optional[str] = None,
    new_provenance: Optional[ProvenanceRecord] = None,
) -> PreferenceCandidate:
    """
    Revises a candidate in place (same candidate_id, incremented
    revision_index) — used for "retain / revise / reject" after
    reflection (mission Section 15). Revision does NOT itself adopt —
    if the revised text should become trial-eligible, adopt() must be
    called again afterward, explicitly.
    """
    _require_actor_and_reason(actor, reason)
    current = _load_current(candidate_id)
    if new_source_text is not None:
        current.source_text = new_source_text
    if new_normalized_representation is not None:
        current.normalized_representation = new_normalized_representation
    if new_provenance is not None:
        new_provenance.parent_candidate_id = current.candidate_id
        current.provenance = new_provenance
    current.status = LifecycleStatus.REVISED
    current.revision_index += 1
    current.notes = f"{current.notes}\n[revised] {reason}".strip()
    store.append_candidate_snapshot(current)
    store.log_audit_event("candidate_revised", candidate_id, {
        "reason": reason,
        "new_source_text": new_source_text,
    }, actor)
    return current


def retain(candidate_id: str, *, actor: str, reason: str, human_confirmation: bool) -> PreferenceCandidate:
    """Explicit "keep this preference after reviewing outcome evidence."
    Same human_confirmation gate as adopt() — retention after evidence
    review is exactly as consequential as first adoption and must not
    be inferable from anything automatic."""
    if human_confirmation is not True:
        raise LifecycleError(
            "retain() requires human_confirmation=True (the literal bool True)."
        )
    _require_actor_and_reason(actor, reason)
    current = _load_current(candidate_id)
    current.status = LifecycleStatus.RETAINED
    current.revision_index += 1
    current.notes = f"{current.notes}\n[retained] {reason}".strip()
    store.append_candidate_snapshot(current)
    store.log_audit_event("candidate_retained", candidate_id, {"reason": reason}, actor)
    return current


def expire(candidate_id: str, *, actor: str, reason: str) -> PreferenceCandidate:
    _require_actor_and_reason(actor, reason)
    current = _load_current(candidate_id)
    current.status = LifecycleStatus.EXPIRED
    current.revision_index += 1
    current.notes = f"{current.notes}\n[expired] {reason}".strip()
    store.append_candidate_snapshot(current)
    store.log_audit_event("candidate_expired", candidate_id, {"reason": reason}, actor)
    return current


def record_behavioral_test(candidate_id: str, trial_id: str, *, actor: str) -> PreferenceCandidate:
    """Attaches a trial_id to a candidate's behavioral_test_ids list —
    called by harness.run_trial() after a trial completes, so a
    candidate's record shows which trials tested it, without the trial
    itself needing write access to the candidate store beyond this one
    append."""
    current = _load_current(candidate_id)
    current.behavioral_test_ids = list(current.behavioral_test_ids) + [trial_id]
    current.revision_index += 1
    store.append_candidate_snapshot(current)
    store.log_audit_event("candidate_tested", candidate_id, {"trial_id": trial_id}, actor)
    return current
