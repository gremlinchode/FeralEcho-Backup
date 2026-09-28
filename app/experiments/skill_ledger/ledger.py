"""The Verified Skill Ledger itself. Schema per the ACCEPTED revision in
audits/2026-09-27_verified_skill_ledger_build_decision.md Section 0/12: a skill is a
verified {precondition, transformation} PATTERN, never a frozen code string.

Persistence follows the exact hash-then-freeze convention already proven three times
in this codebase (persistent_routing/selector.py, VECT's freeze_procedure.py,
strategy_characterization's own protocol hashing) -- duplicated here deliberately
(this package must not import anything from those experiment-specific modules beyond
the shared pure hash/seed helpers), not re-invented.
"""
from __future__ import annotations
import time
from pathlib import Path

from .common import LEDGER_ROOT, sha256_text, write_json_force, write_json_new, read_json

SKILLS_DIR = LEDGER_ROOT / "skills"
PROVENANCE_LOG = LEDGER_ROOT / "provenance.jsonl"
STATS_PATH = LEDGER_ROOT / "skill_stats.json"


class Skill:
    """One ledger entry. `precondition` and `transformation` are the pattern objects
    produced by diff_extract.py -- plain, JSON-serializable dicts (an AST-shaped
    template with instance-specific literals replaced by wildcard markers), never
    natural language and never a literal answer string. `held_out_verdict` starts
    None and is set only by a real held-out test (harness.py's transfer-check phase)
    -- a skill with held_out_verdict is None is NOT eligible for consumption,
    enforced in code (see is_eligible()), not by convention."""

    def __init__(self, feature_key: str, precondition: dict, transformation: dict,
                 provenance: dict, held_out_verdict=None, status: str = "candidate",
                 version: int = 1):
        self.feature_key = feature_key
        self.precondition = precondition
        self.transformation = transformation
        self.provenance = provenance
        self.held_out_verdict = held_out_verdict
        self.status = status  # "candidate" | "validated" | "invalidated"
        self.version = version

    def to_dict(self) -> dict:
        return {
            "feature_key": self.feature_key,
            "precondition": self.precondition,
            "transformation": self.transformation,
            "provenance": self.provenance,
            "held_out_verdict": self.held_out_verdict,
            "status": self.status,
            "version": self.version,
        }

    def content_hash(self) -> str:
        import json
        return sha256_text(json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")))

    def is_eligible(self) -> bool:
        """A skill may only be consumed (applied to a fresh candidate) if it has
        genuinely passed a real held-out test AND is not flagged invalidated. This
        is the one hard gate distinguishing a 'candidate' from a 'validated' skill --
        enforced here, not left to the caller's discretion."""
        return self.status == "validated" and self.held_out_verdict == "PASS"

    @classmethod
    def load(cls, path) -> "Skill":
        d = read_json(path)
        return cls(d["feature_key"], d["precondition"], d["transformation"], d["provenance"],
                    d.get("held_out_verdict"), d.get("status", "candidate"), d.get("version", 1))

    def save_new_version(self) -> str:
        """Write-once, versioned save -- never overwrites an existing version file.
        Returns the content hash. A skill's version increments only when its
        held_out_verdict/status changes (candidate -> validated, or validated ->
        invalidated) -- the file itself is otherwise immutable, matching this
        project's own established provenance discipline (a change is a new, hashed
        version, never a silent in-place edit)."""
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        path = SKILLS_DIR / f"{self.feature_key}.v{self.version}.json"
        write_json_new(path, self.to_dict())
        log_provenance_event("skill_saved", self.feature_key, self.version, self.content_hash())
        return self.content_hash()

    @classmethod
    def load_latest(cls, feature_key: str) -> "Skill | None":
        """Loads the highest-version file for this feature_key, or None if no skill
        exists yet for it. Verifies the loaded file's own recomputed content hash
        against nothing external (there is no separate commitment file for a single
        skill in this MVK) -- integrity here rests on the write-once file contract
        itself (a version file, once written, is never edited), the same posture
        persistent_routing's own S1.json files rely on."""
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        candidates = sorted(SKILLS_DIR.glob(f"{feature_key}.v*.json"),
                             key=lambda p: int(p.stem.rsplit(".v", 1)[1]))
        if not candidates:
            return None
        return cls.load(candidates[-1])


def log_provenance_event(event: str, feature_key: str, version: int, content_hash: str, **extra) -> None:
    from .common import append_jsonl
    row = {"event": event, "feature_key": feature_key, "version": version,
           "content_hash": content_hash, "timestamp": time.time(), **extra}
    append_jsonl(PROVENANCE_LOG, row)


def invalidate(feature_key: str, reason: str) -> "Skill":
    """Loads the latest version, writes a NEW version with status='invalidated' --
    never deletes or edits the prior version file. This is the rollback mechanism:
    a consumer always calls load_latest() and load_latest() will return the
    invalidated version (highest version number), so invalidation is immediately
    effective for all future consumption without touching history."""
    s = Skill.load_latest(feature_key)
    if s is None:
        raise ValueError(f"no skill exists for {feature_key}")
    s.status = "invalidated"
    s.version += 1
    s.provenance = {**s.provenance, "invalidation_reason": reason, "invalidated_at": time.time()}
    s.save_new_version()
    return s


def validate(feature_key: str, held_out_verdict: str) -> "Skill":
    """Loads the latest 'candidate' version, writes a NEW version with the real
    held-out verdict and status='validated' (only if verdict == 'PASS') or stays
    'candidate' otherwise (a real FAIL here does not silently become eligible)."""
    s = Skill.load_latest(feature_key)
    if s is None:
        raise ValueError(f"no skill exists for {feature_key}")
    s.held_out_verdict = held_out_verdict
    s.status = "validated" if held_out_verdict == "PASS" else "candidate"
    s.version += 1
    s.save_new_version()
    return s
