"""Shared constants/helpers for the Verified Skill Ledger (VSL) implementation.

Governing documents (read before changing anything here):
  audits/2026-09-27_feralecho_learning_architecture_deep_dive.md
  audits/2026-09-27_verified_skill_ledger_build_decision.md  (REVISE THEN BUILD accepted;
    the schema below reflects the accepted revision: a skill is a verified
    {precondition, transformation} pattern, never a frozen code string.)

Reuses AP-0's proven pure helpers, never anything with production side effects."""
from __future__ import annotations
import json
import os
from pathlib import Path

from app.experiments.accumulation_probe.common import canon, sha256_obj, sha256_text  # noqa: F401

REPO = Path(__file__).resolve().parents[3]
LEDGER_ROOT = Path(os.environ.get("VSL_ROOT", str(REPO / "memory" / "experiments" / "skill_ledger")))
OLLAMA_URL = os.environ.get("VSL_OLLAMA_URL", "http://127.0.0.1:11434")

# This module's own master seed + a fresh, disjoint offset. Disjointness from every
# prior offset in this codebase (0, 100, 5000, 5100, 7000, 40000 [AP-0]; 90000
# [persistent_routing]; 120000 [strategy_characterization]) confirmed empirically
# (direct token-overlap check) before any real call is made, per this project's own
# established discipline -- see verify_disjoint_seed_offset() below.
MASTER_SEED = 20260927
SEED_OFFSET = 150000

MODEL = "qwen2.5-coder:7b"
OPTIONS = {"temperature": 0.2, "top_p": 1.0, "num_predict": 512, "num_ctx": 4096}
KIND = "K2"
N_CANDIDATES_PER_FAILURE = 4  # matches this project's own established repeat-count convention


def seed_for(replicate: str, key: str, sample: int) -> int:
    return int(sha256_text(f"VSL|{MASTER_SEED}|{replicate}|{key}|{sample}")[:8], 16) % (2 ** 31 - 1)


def write_json_new(p, obj) -> None:
    """Refuse-to-overwrite write -- identical contract to every prior experiment
    package's own version in this codebase."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def write_json_force(p, obj) -> None:
    """Overwriting write, used only for the ledger's own versioned skill files where
    an explicit new version is being written under a new path -- never used to
    silently clobber a skill's history."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def append_jsonl(p, row) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(canon(row) + "\n")


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def read_jsonl(p):
    p = Path(p)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
