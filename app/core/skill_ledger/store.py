"""Persistence primitives for the Verified Skill Ledger core. Generalizes
app/experiments/skill_ledger/common.py's write-once/hash/provenance-log helpers to a
CONFIGURABLE root, so the historical experiment (memory/experiments/skill_ledger/) and
the real production ledger (memory/skill_ledger/) never share a directory or collide --
a production skill and an experimental skill with the same feature_key are, by
construction, different files in different trees, never silently confused.

Hashing/JSON helpers are re-imported from the experiment's own already-proven common.py
rather than reimplemented (same sha256_text/canon lineage this whole codebase already
uses via accumulation_probe.common) -- this module only adds the "which root" concern.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

from app.experiments.skill_ledger.common import sha256_text  # noqa: F401 -- re-exported for callers

_PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Production skills live here -- deliberately NOT under memory/experiments/, which is
# reserved for the scientific harnesses (prospective_transfer.py, accumulation.py) and
# their own Skill A / Skill B evidence. Nothing in this module ever writes there.
PRODUCTION_ROOT = _PROJECT_ROOT / "memory" / "skill_ledger"


def write_json_new(path, obj) -> None:
    """Refuse-to-overwrite write -- identical contract to every write-once file in
    this codebase (accumulation_probe.common.write_json_new, skill_ledger.common's own
    copy). Duplicated rather than imported specifically so this module has zero
    import-time dependency on the experiment package beyond the hash helper above."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_jsonl(path, row) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def log_provenance_event(root: Path, event: str, feature_key: str, version: int,
                          content_hash: str, **extra) -> None:
    row = {"event": event, "feature_key": feature_key, "version": version,
           "content_hash": content_hash, "timestamp": time.time(), **extra}
    append_jsonl(root / "provenance.jsonl", row)
