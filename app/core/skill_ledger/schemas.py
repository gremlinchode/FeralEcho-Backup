"""The Skill record -- identity, provenance, and lifecycle.

Moved from app/experiments/skill_ledger/ledger.py's Skill class during the 2026-09-28
integration-readiness pass. The ORIGINAL contract (feature_key/precondition/
transformation/provenance/held_out_verdict/status/version, to_dict(), content_hash(),
is_eligible(), load(), save_new_version(), load_latest()) is preserved byte-for-byte:
every existing serialized skill file (K2.T5.tag_priority_direction.v1..v5,
K2.T2.discovered_via_accumulation_test.v1) continues to load and re-hash identically --
`lifecycle_state` and `outcome_stats` are additive fields, only included in to_dict()
when actually set/non-empty, so a legacy skill's own content_hash() is unaffected by
this move (verified directly, not assumed -- see the integration test suite).

Schema (unchanged core):
  {
    "feature_key": "...", "precondition": "...", "transformation": "...",
    "provenance": {...}, "held_out_verdict": null|"PASS"|"FAIL",
    "status": "candidate"|"validated"|"invalidated", "version": N
  }

Additive production lifecycle (Phase 6 of the integration-readiness mission), a strict
superset of the legacy status vocabulary -- CANDIDATE/VERIFIED/QUALIFIED/ACTIVE/
DEGRADED/QUARANTINED/RETIRED/SUPERSEDED. `effective_lifecycle()` derives one of these
for ANY skill, legacy or new, without requiring every old file to be rewritten:

  legacy status="candidate", held_out_verdict=None      -> CANDIDATE
  legacy status="candidate", held_out_verdict="FAIL"     -> VERIFIED
    (cleared F1/F2-equivalent verification on its source pair, but its own held-out
    gate did not pass -- matches this project's real historical Skill A v1-v4 states)
  legacy status="validated", held_out_verdict="PASS"     -> QUALIFIED
    (matches is_eligible()==True -- a real causal-transfer PASS is on record, but a
    skill only reaches ACTIVE via an explicit, evidenced promotion -- see below)
  legacy status="invalidated"                            -> RETIRED
  `lifecycle_state` explicitly set (new production skills)  -> returned directly

THE LEDGER MUST NOT BE ITS OWN VERIFIER: every transition function below requires an
explicit `evidence` string naming the real, external fact that justifies it (an oracle
result, a real outcome-stat threshold, a human decision) -- there is no transition that
a skill (or a model asked to describe its own skill) can trigger unassisted.
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import Optional

from .store import sha256_text, write_json_new, read_json, log_provenance_event, PRODUCTION_ROOT

SKILLS_DIR = PRODUCTION_ROOT / "skills"

# Additive lifecycle vocabulary (Phase 6). Legacy status values ("candidate",
# "validated", "invalidated") remain valid `status` values forever -- this is a
# SEPARATE field, not a replacement, specifically so effective_lifecycle() can derive
# a value for old files with no `lifecycle_state` key at all.
LIFECYCLE_STATES = ("CANDIDATE", "VERIFIED", "QUALIFIED", "ACTIVE", "DEGRADED",
                    "QUARANTINED", "RETIRED", "SUPERSEDED")

# A skill is DEGRADED once its own recorded outcome stats (real production
# applications, not synthetic tests) show a failure rate at or above this over at
# least this many real applications -- both numbers are deliberately conservative
# (small N, low bar) since this is the first production skill this threshold will
# ever gate; revisit once real application volume exists to calibrate against.
_DEGRADE_MIN_APPLICATIONS = 5
_DEGRADE_FAILURE_RATE = 0.5


class Skill:
    """One ledger entry. See module docstring for the schema. `precondition` and
    `transformation` are the pattern objects produced by matcher.py -- plain,
    JSON-serializable strings (an ast.dump()-shaped template with instance-specific
    literals replaced by wildcard markers), never natural language and never a
    literal answer string."""

    def __init__(self, feature_key: str, precondition, transformation,
                 provenance: dict, held_out_verdict=None, status: str = "candidate",
                 version: int = 1, lifecycle_state: Optional[str] = None,
                 outcome_stats: Optional[dict] = None):
        self.feature_key = feature_key
        self.precondition = precondition
        self.transformation = transformation
        self.provenance = provenance
        self.held_out_verdict = held_out_verdict
        self.status = status  # "candidate" | "validated" | "invalidated" (legacy, permanent)
        self.version = version
        self.lifecycle_state = lifecycle_state  # None until a production transition sets it
        self.outcome_stats = outcome_stats or {}  # {"applications": N, "successes": N, "failures": N}

    def to_dict(self) -> dict:
        d = {
            "feature_key": self.feature_key,
            "precondition": self.precondition,
            "transformation": self.transformation,
            "provenance": self.provenance,
            "held_out_verdict": self.held_out_verdict,
            "status": self.status,
            "version": self.version,
        }
        # Additive only -- omitted entirely when unset/empty so a legacy skill's own
        # to_dict()/content_hash() is byte-for-byte unaffected by this schema's move.
        if self.lifecycle_state is not None:
            d["lifecycle_state"] = self.lifecycle_state
        if self.outcome_stats:
            d["outcome_stats"] = self.outcome_stats
        return d

    def content_hash(self) -> str:
        import json
        return sha256_text(json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")))

    def is_eligible(self) -> bool:
        """Legacy gate, UNCHANGED: a skill may only be consumed if it has genuinely
        passed a real held-out test AND is not flagged invalidated. Kept exactly as
        the experiment defined it -- production code should prefer
        effective_lifecycle() == "ACTIVE" for the fuller state machine, but this
        method's own behavior is not altered by that addition."""
        return self.status == "validated" and self.held_out_verdict == "PASS"

    def effective_lifecycle(self) -> str:
        """Derives one of LIFECYCLE_STATES for ANY skill, legacy or new. See module
        docstring for the exact mapping. Never requires rewriting an old file."""
        if self.lifecycle_state is not None:
            return self.lifecycle_state
        if self.status == "invalidated":
            return "RETIRED"
        if self.status == "validated" and self.held_out_verdict == "PASS":
            return "QUALIFIED"
        if self.status == "candidate" and self.held_out_verdict == "FAIL":
            return "VERIFIED"
        return "CANDIDATE"

    @classmethod
    def load(cls, path) -> "Skill":
        d = read_json(path)
        return cls(d["feature_key"], d["precondition"], d["transformation"], d["provenance"],
                    d.get("held_out_verdict"), d.get("status", "candidate"), d.get("version", 1),
                    d.get("lifecycle_state"), d.get("outcome_stats"))

    def save_new_version(self, root: "Path | None" = None) -> str:
        """Write-once, versioned save -- never overwrites an existing version file.
        `root` defaults to the real production SKILLS_DIR; parameterized (same
        reasoning as this codebase's other write-once stores gaining optional roots
        for testing -- e.g. self_edit_manager.py's _prune_self_edit_plans()) so tests
        can exercise this against a scratch directory."""
        skills_dir = root if root is not None else SKILLS_DIR
        skills_dir.mkdir(parents=True, exist_ok=True)
        path = skills_dir / f"{self.feature_key}.v{self.version}.json"
        write_json_new(path, self.to_dict())
        log_provenance_event(skills_dir.parent, "skill_saved", self.feature_key, self.version,
                              self.content_hash(), lifecycle_state=self.effective_lifecycle())
        return self.content_hash()

    @classmethod
    def load_latest(cls, feature_key: str, root: "Path | None" = None) -> "Skill | None":
        """Loads the highest-version file for this feature_key, or None if no skill
        exists yet for it in the given root (production SKILLS_DIR by default)."""
        skills_dir = root if root is not None else SKILLS_DIR
        skills_dir.mkdir(parents=True, exist_ok=True)
        candidates = sorted(skills_dir.glob(f"{feature_key}.v*.json"),
                             key=lambda p: int(p.stem.rsplit(".v", 1)[1]))
        if not candidates:
            return None
        return cls.load(candidates[-1])

    # ---- Production lifecycle transitions (Phase 6). Each is write-once/versioned,
    # each requires real, named evidence -- never a model's own self-report. ----

    def _transition(self, new_state: str, evidence: str, root: "Path | None" = None,
                     extra_provenance: "dict | None" = None) -> "Skill":
        if new_state not in LIFECYCLE_STATES:
            raise ValueError(f"unknown lifecycle state: {new_state!r}")
        prov = {**self.provenance, **(extra_provenance or {}),
                f"lifecycle_transition_to_{new_state.lower()}": {
                    "at": time.time(), "evidence": evidence, "from": self.effective_lifecycle(),
                }}
        next_skill = Skill(self.feature_key, self.precondition, self.transformation, prov,
                            self.held_out_verdict, self.status, self.version + 1,
                            lifecycle_state=new_state, outcome_stats=dict(self.outcome_stats))
        next_skill.save_new_version(root)
        return next_skill

    def promote_to_verified(self, evidence: str, root=None) -> "Skill":
        """CANDIDATE -> VERIFIED: an independent oracle (F1-equivalent static check,
        or a real test-suite pass) confirmed the skill's source acquisition was
        genuine, without yet demonstrating held-out generalization.

        State-guarded since 2026-09-28 (adversarial integration review finding): the
        chain's own documented sequencing was previously enforced at exactly one step
        (promote_to_active()) and nowhere else, so this and promote_to_qualified()
        below were callable from any state at all, including RETIRED/QUARANTINED --
        demonstrated live during that review (a RETIRED skill could be silently
        re-qualified and re-activated with a trivial evidence string). Every forward
        step now requires the skill to genuinely be in the state immediately prior."""
        if self.effective_lifecycle() != "CANDIDATE":
            raise ValueError(f"cannot promote to VERIFIED from {self.effective_lifecycle()} "
                              f"-- a skill must be CANDIDATE first")
        return self._transition("VERIFIED", evidence, root)

    def promote_to_qualified(self, evidence: str, root=None) -> "Skill":
        """VERIFIED -> QUALIFIED: a real, outcome-blind, TRUE-vs-SUBSTITUTION
        held-out transfer test passed (matches is_eligible()'s own legacy PASS
        semantic) -- the skill has demonstrated a genuine causal advantage on
        fresh, previously-unseen instances. State-guarded, see promote_to_verified()'s
        docstring for why."""
        if self.effective_lifecycle() != "VERIFIED":
            raise ValueError(f"cannot promote to QUALIFIED from {self.effective_lifecycle()} "
                              f"-- a skill must be VERIFIED first")
        return self._transition("QUALIFIED", evidence, root)

    def promote_to_active(self, evidence: str, root=None) -> "Skill":
        """QUALIFIED -> ACTIVE: an explicit decision (human or an evidenced,
        threshold-based automated process -- never the skill's own claim) that this
        skill may now be consumed on real, unreviewed production tasks, not just
        experimental holdout instances."""
        if self.effective_lifecycle() not in ("QUALIFIED",):
            raise ValueError(f"cannot promote to ACTIVE from {self.effective_lifecycle()} "
                              f"-- a skill must be QUALIFIED (a real held-out PASS on record) first")
        return self._transition("ACTIVE", evidence, root)

    def mark_degraded(self, evidence: str, root=None) -> "Skill":
        """ACTIVE -> DEGRADED: real production outcome stats crossed the degrade
        threshold (see record_outcome() in runtime.py, which is what actually
        computes and calls this -- never a self-referential claim). State-guarded,
        same reasoning as promote_to_verified()/promote_to_qualified() above --
        degradation is only a meaningful signal relative to a skill that was actually
        live and consumed; degrading a non-ACTIVE skill would be a category error."""
        if self.effective_lifecycle() != "ACTIVE":
            raise ValueError(f"cannot mark_degraded from {self.effective_lifecycle()} "
                              f"-- a skill must be ACTIVE first")
        return self._transition("DEGRADED", evidence, root)

    def quarantine(self, evidence: str, root=None) -> "Skill":
        """Any state -> QUARANTINED: a safety-relevant concern (a bad application
        outside its original domain, a suspicious precondition, a human decision)
        immediately removes a skill from consumption pending review. Reversible --
        a quarantined skill can be re-promoted with fresh evidence, or retired."""
        return self._transition("QUARANTINED", evidence, root)

    def retire(self, evidence: str, root=None) -> "Skill":
        """Any state -> RETIRED: permanent (in the sense that consumption code
        should never re-promote a RETIRED skill automatically -- a human creating a
        fresh version from scratch is a new decision, not a reversal)."""
        return self._transition("RETIRED", evidence, root)

    def supersede(self, by_feature_key: str, evidence: str, root=None) -> "Skill":
        """Any state -> SUPERSEDED: a different, better-verified skill now covers
        this one's domain. `by_feature_key` is recorded in provenance so the
        replacement is traceable, never silent."""
        return self._transition("SUPERSEDED", evidence, root,
                                 extra_provenance={"superseded_by": by_feature_key})
