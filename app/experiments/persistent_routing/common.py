"""Shared constants and helpers for the persistent-routing-learning experiment
(audits/2026-09-22_preregistered_persistent_routing_experiment_design.md +
this package's own PREREG_ADDENDUM.md). Reuses AP-0's proven pure helpers
(hashing, seeding, atomic write) rather than duplicating them; never imports
anything AP-0-specific beyond those stdlib-only utilities, per the frozen
design's own "own dedicated files, own jail root" requirement (§20/§19)."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

from app.experiments.accumulation_probe.common import canon, sha256_obj, sha256_text  # pure, stdlib-only, no state

REPO = Path(__file__).resolve().parents[3]
EXP_ROOT = Path(os.environ.get("PR_ROOT", str(REPO / "memory" / "experiments" / "persistent_routing")))
OLLAMA_URL = os.environ.get("PR_OLLAMA_URL", "http://127.0.0.1:11434")
MASTER_SEED = 20260927  # this experiment's own master seed, distinct from AP-0's 20260921

# PREREG_ADDENDUM.md's frozen constants
TASK_TYPE_KEY = "persistent_routing_experiment"
SEED_OFFSET = 90000
EPSILON = 0.2
DEFAULT_STRATEGY = "DIRECT"
MODEL = "qwen2.5-coder:7b"
OPTIONS = {"temperature": 0.2, "top_p": 1.0, "num_predict": 512, "num_ctx": 4096}
STRATEGIES = ("DIRECT", "STEPWISE", "WORKED_EXAMPLE")


def seed_for(replicate: str, task_id: str, sample: int) -> int:
    """Matched-seed convention, identical shape to AP-0's own seed_for()
    (common.py), but under this experiment's own MASTER_SEED namespace so
    the two experiments' seed spaces can never collide even by coincidence."""
    return int(sha256_text(f"PR|{MASTER_SEED}|{replicate}|{task_id}|{sample}")[:8], 16) % (2 ** 31 - 1)


def write_json_new(p, obj) -> None:
    """Refuse-to-overwrite write, identical contract to AP-0's own —
    duplicated (not imported) because AP-0's version is a private module
    detail, not part of its exported pure-helper surface, and this
    experiment must never import anything from AP-0 beyond the explicitly
    pure hash/seed utilities named above."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", encoding="utf-8") as f:
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


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
