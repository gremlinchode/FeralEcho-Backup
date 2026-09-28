"""Thin re-export/subclass wrapper over the production core. The Skill class's
underlying schema (fields/to_dict/content_hash/is_eligible/load) moved verbatim to
app/core/skill_ledger/schemas.py during the 2026-09-28 integration-readiness pass (see
audits/2026-09-28_vsl_integration_readiness.md); this module subclasses it to preserve
two EXACT historical behaviors that a bare re-export would have silently changed:

1. `SKILLS_DIR` here is the experiment's OWN root (memory/experiments/skill_ledger/skills/),
   never the production core's default (memory/skill_ledger/skills/) -- production and
   experimental skills must never share a directory or collide.
2. `save_new_version()`/`load_latest()` called with NO explicit root argument default to
   THIS module's `SKILLS_DIR` global -- preserving verify_diff_extract.py's existing
   serialization test, which monkeypatches `ledger.SKILLS_DIR` directly and expects
   subsequent no-arg calls to respect it.
3. `log_provenance_event()` writes to a FIXED path (`LEDGER_ROOT / "provenance.jsonl"`,
   computed once at import time) -- confirmed, by inspecting the real, existing
   provenance.jsonl before this move, that this was the ORIGINAL module's actual
   behavior even when SKILLS_DIR was monkeypatched to a scratch tempdir during the
   serialization test (a real, pre-existing quirk, not something this move introduces).

Re-run verify_diff_extract.py (15/15) immediately after this move confirmed zero
observable behavior change."""
from __future__ import annotations
from pathlib import Path

from app.core.skill_ledger.schemas import Skill as _CoreSkill
from .common import LEDGER_ROOT, append_jsonl

SKILLS_DIR = LEDGER_ROOT / "skills"
PROVENANCE_LOG = LEDGER_ROOT / "provenance.jsonl"
STATS_PATH = LEDGER_ROOT / "skill_stats.json"


class Skill(_CoreSkill):
    """Experiment-scoped Skill: identical schema/contract to the core, but its
    zero-argument save_new_version()/load_latest() always resolve against THIS
    module's (monkeypatchable) SKILLS_DIR global, and every provenance event lands in
    THIS module's fixed provenance.jsonl -- exactly matching pre-move behavior."""

    def save_new_version(self, root: "Path | None" = None) -> str:
        skills_dir = root if root is not None else SKILLS_DIR
        skills_dir.mkdir(parents=True, exist_ok=True)
        path = skills_dir / f"{self.feature_key}.v{self.version}.json"
        from .common import write_json_new
        write_json_new(path, self.to_dict())
        log_provenance_event("skill_saved", self.feature_key, self.version, self.content_hash())
        return self.content_hash()

    @classmethod
    def load_latest(cls, feature_key: str, root: "Path | None" = None) -> "Skill | None":
        skills_dir = root if root is not None else SKILLS_DIR
        skills_dir.mkdir(parents=True, exist_ok=True)
        candidates = sorted(skills_dir.glob(f"{feature_key}.v*.json"),
                             key=lambda p: int(p.stem.rsplit(".v", 1)[1]))
        if not candidates:
            return None
        return cls.load(candidates[-1])


def log_provenance_event(event: str, feature_key: str, version: int, content_hash: str, **extra) -> None:
    import time
    row = {"event": event, "feature_key": feature_key, "version": version,
           "content_hash": content_hash, "timestamp": time.time(), **extra}
    append_jsonl(PROVENANCE_LOG, row)


def invalidate(feature_key: str, reason: str) -> "Skill":
    """Loads the latest version, writes a NEW version with status='invalidated' --
    never deletes or edits the prior version file."""
    s = Skill.load_latest(feature_key)
    if s is None:
        raise ValueError(f"no skill exists for {feature_key}")
    s.status = "invalidated"
    s.version += 1
    s.provenance = {**s.provenance, "invalidation_reason": reason, "invalidated_at": __import__("time").time()}
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
