"""Production consumption API: the ONE place a real Echo path should ever call to
consult, apply, and record outcomes for verified skills. Gated by two independent
controls (Phase 14): `VSL_ENABLED` (a hard kill switch) and `VSL_MODE`
(disabled/shadow/active, Phase 15/16).

THE LEDGER MUST NOT BE ITS OWN VERIFIER: nothing here ever treats a precondition
match, a skill's own metadata, or a model's claim as proof of correctness.
`record_outcome()` only ever RECORDS a verdict some external verifier already
produced (an F1/F2 pass, a real test-suite result) -- it never computes one itself.
Deciding whether accumulated outcome evidence should degrade/quarantine a skill is a
SEPARATE, explicitly-invoked step (`evaluate_degradation()`), never triggered
automatically inline by `record_outcome()` -- this project's own established
discipline around consequential auto-triggers (do not wire one in by default or
momentum; see CLAUDE.md's mark_baseline_trusted()/council_rater() history) applies
here too.
"""
from __future__ import annotations
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from . import matcher
from .schemas import Skill, SKILLS_DIR, _DEGRADE_MIN_APPLICATIONS, _DEGRADE_FAILURE_RATE
from .store import PRODUCTION_ROOT, append_jsonl, sha256_text

APPLICATIONS_LOG = PRODUCTION_ROOT / "applications.jsonl"

_VALID_MODES = ("disabled", "shadow", "active")


def is_enabled() -> bool:
    """The hard kill switch (Phase 14). Fails closed: any value other than the
    literal string 'true' (case-insensitive) is treated as disabled, including an
    unset/malformed env var -- consistent with this codebase's own established
    fail-closed convention (system_guard.py's None-sentinel handling, F1/F2's own
    refuse-don't-guess posture)."""
    return os.environ.get("VSL_ENABLED", "false").strip().lower() == "true"


def get_mode() -> str:
    """Returns 'disabled' unconditionally if is_enabled() is False, regardless of
    VSL_MODE's own value -- the kill switch always wins. Otherwise returns VSL_MODE
    (default 'shadow', the safer of the two real modes) if it's one of the three
    valid values, else 'disabled' (fail closed on a malformed/unknown mode value,
    never silently falling through to 'active')."""
    if not is_enabled():
        return "disabled"
    mode = os.environ.get("VSL_MODE", "shadow").strip().lower()
    return mode if mode in _VALID_MODES else "disabled"


def _pattern_for(skill: Skill) -> dict:
    return {"precondition": skill.precondition, "transformation": skill.transformation,
            "node_type": skill.provenance.get("node_type"),
            "enclosing_call": skill.provenance.get("enclosing_call")}


@dataclass
class ConsultResult:
    """What consult() decided, and why -- always fully populated regardless of mode,
    so a caller (or a human reading applications.jsonl) can always answer 'what
    would VSL have done here, and did it actually do it.'"""
    mode: str
    matched_feature_key: Optional[str] = None
    matched_skill_version: Optional[int] = None
    proposed_code: Optional[str] = None
    applied: bool = False
    candidates_checked: list = field(default_factory=list)  # feature_keys inspected, in order


def _list_active_feature_keys() -> list:
    """Every feature_key with at least one skill version on disk whose
    effective_lifecycle() is ACTIVE, using each key's LATEST version only (an older,
    superseded version of an ACTIVE key is never separately considered)."""
    if not SKILLS_DIR.exists():
        return []
    keys = sorted({p.name.rsplit(".v", 1)[0] for p in SKILLS_DIR.glob("*.v*.json")})
    return [k for k in keys if (Skill.load_latest(k) or Skill("", "", "", {})).effective_lifecycle() == "ACTIVE"]


def consult(code: str, fn_name: str, feature_keys: "list | None" = None) -> ConsultResult:
    """The one entry point a real Echo path calls. Returns a ConsultResult
    regardless of mode -- callers that want the "what would have happened" signal
    even when disabled should call this directly rather than checking get_mode()
    themselves first (though get_mode()=='disabled' short-circuits before any real
    matching work, for cheapness).

    Only ACTIVE-lifecycle skills are ever considered, in BOTH shadow and active mode
    -- shadow mode is a true preview of what enabling active mode would do, not a
    broader "what if every qualified skill were trusted" simulation (Phase 15's own
    stated purpose: "production-distribution evidence... integration safety", not a
    second research probe).

    CONFLICT POLICY (Phase 7), stated explicitly rather than left implicit in the
    iteration order below: candidates are tried in a fixed, deterministic order
    (sorted feature_key), and the FIRST skill whose precondition matches wins --
    this single call NEVER composes two skills' transformations together, and never
    picks a "better" of two matching skills by any notion of specificity, success
    rate, or recency. With exactly one real ACTIVE skill in production today this
    policy is inherently conflict-free; it is written down now, before a second
    ACTIVE skill ever exists, specifically so the behavior at that point is already
    decided rather than improvised. Known, accepted limitations of this simple
    policy, left as explicit future work rather than solved here: no
    specificity-based tiebreak (a narrower precondition does not win over a broader
    one that also matches), no outcome-stat-based ranking (a skill with a better
    real track record is not preferred over one with a worse one), no composition
    within one function (echo_adapter.py's consult_file() *does* allow different
    skills to apply to *different* functions within the same file across repeated
    consult() calls -- composition across files/functions, never within one).
    Echo declines to apply any skill whenever no candidate's precondition matches,
    or whenever mode is "disabled" -- there is no other decline condition today
    (e.g. "ambiguous match" is not a distinct state; the first deterministic match
    is always taken).
    """
    mode = get_mode()
    if mode == "disabled":
        return ConsultResult(mode="disabled")

    candidates = feature_keys if feature_keys is not None else _list_active_feature_keys()
    checked = []
    for fk in candidates:
        checked.append(fk)
        skill = Skill.load_latest(fk)
        if skill is None or skill.effective_lifecycle() != "ACTIVE":
            continue  # a key that WAS active at listing time but changed since -- re-checked live, not cached
        pattern = _pattern_for(skill)
        try:
            proposed = matcher.apply_skill(code, fn_name, pattern)
        except Exception:
            proposed = None  # fail closed: a matcher exception is treated as "no match", never propagated
        if proposed is not None:
            return ConsultResult(mode=mode, matched_feature_key=fk, matched_skill_version=skill.version,
                                  proposed_code=proposed, applied=(mode == "active"), candidates_checked=checked)
    return ConsultResult(mode=mode, candidates_checked=checked)


def record_outcome(task_id: str, result: ConsultResult, code_before: str,
                    verifier_result: "dict | None", verifier_strength: str,
                    code_after: "str | None" = None, applications_log=None) -> None:
    """Appends one real application/consultation record. Never raises (best-effort,
    matching this codebase's own "instrumentation never blocks the real computation
    it's attached to" convention) and never itself decides pass/fail -- `verifier_result`
    must already be a real, external verdict (e.g. {"f1_passed": True, "f2_passed":
    True} from echo_projects.py's own pipeline, or a real oracle's {"passed": bool}).

    `verifier_strength` is a required, explicit label naming how strong the verdict
    actually is -- e.g. "f1_f2_safety_only" (no correctness check, just "didn't get
    blocked and didn't crash") vs "full_oracle" (a real hidden-test pass/fail, the
    K2 harness's own standard). This is recorded precisely so outcome stats are never
    silently conflated across verifiers of very different strength -- exactly the
    kind of inflation Phase 18 warns against.

    `applications_log` (optional): write to a different path than the real production
    APPLICATIONS_LOG -- for tests only, so a test run never pollutes real production
    outcome history (a real mistake caught and fixed during this integration pass
    itself: an early manual test of evaluate_degradation() below wrote synthetic
    failure records against the real store before this parameter existed -- see
    audits/2026-09-28_vsl_integration_readiness.md).
    """
    log_path = applications_log if applications_log is not None else APPLICATIONS_LOG
    row = {
        "timestamp": time.time(), "task_id": task_id, "mode": result.mode,
        "matched_feature_key": result.matched_feature_key,
        "matched_skill_version": result.matched_skill_version, "applied": result.applied,
        "code_before_hash": sha256_text(code_before) if code_before else None,
        "code_after_hash": sha256_text(code_after) if code_after else None,
        "verifier_result": verifier_result, "verifier_strength": verifier_strength,
        "candidates_checked": result.candidates_checked,
    }
    try:
        append_jsonl(log_path, row)
    except Exception:
        pass  # observability must never block the real generation path it's attached to


def evaluate_degradation(feature_key: str, min_applications: int = _DEGRADE_MIN_APPLICATIONS,
                          failure_rate_threshold: float = _DEGRADE_FAILURE_RATE,
                          applications_log=None, skills_root=None) -> "dict | None":
    """Reads the REAL application log (not a self-report) for this feature_key's
    real, applied (result.applied==True), *full_oracle*-strength outcomes only
    (f1_f2_safety_only outcomes are deliberately excluded here -- they cannot
    distinguish a genuine correctness regression from a skill that simply never
    reaches a code path exercised by F1/F2, so they are not strong enough evidence
    to degrade a skill on their own). Returns a dict describing the real stats and,
    if the threshold is crossed, calls skill.mark_degraded() with the real evidence
    -- an explicit, separately-invoked check, never run automatically inside
    record_outcome() itself.
    """
    log_path = applications_log if applications_log is not None else APPLICATIONS_LOG
    if not log_path.exists():
        return None
    applied_full_oracle = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            import json
            try:
                row = json.loads(line)
            except Exception:
                continue
            if (row.get("matched_feature_key") == feature_key and row.get("applied")
                    and row.get("verifier_strength") == "full_oracle" and row.get("verifier_result")):
                applied_full_oracle.append(row)

    n = len(applied_full_oracle)
    if n < min_applications:
        return {"feature_key": feature_key, "n_full_oracle_applications": n,
                "min_required": min_applications, "action": "none", "reason": "insufficient real evidence"}

    failures = sum(1 for r in applied_full_oracle if not r["verifier_result"].get("passed", False))
    rate = failures / n
    stats = {"feature_key": feature_key, "n_full_oracle_applications": n, "failures": failures,
             "failure_rate": rate, "threshold": failure_rate_threshold}
    if rate >= failure_rate_threshold:
        skill = Skill.load_latest(feature_key, root=skills_root)
        if skill is not None and skill.effective_lifecycle() == "ACTIVE":
            skill.mark_degraded(
                evidence=f"real application log: {failures}/{n} full-oracle applications failed "
                         f"(rate={rate:.2f} >= threshold {failure_rate_threshold})",
                root=skills_root)
            stats["action"] = "degraded"
        else:
            stats["action"] = "none"
            stats["reason"] = "skill already not ACTIVE"
    else:
        stats["action"] = "none"
        stats["reason"] = "below threshold"
    return stats
