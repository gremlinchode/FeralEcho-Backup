"""Shared constants/helpers for the K2 strategy-characterization study
(audits/2026-09-27_strategy_characterization_protocol_design.md, the CORRECTED/
controlling version -- see that file's own provenance note and
audits/2026-09-27_strategy_characterization_protocol_PROVENANCE.md for the full hash
chain). Reuses AP-0's proven pure helpers, never anything with production side effects."""
from __future__ import annotations
import json
import os
from pathlib import Path

from app.experiments.accumulation_probe.common import canon, sha256_obj, sha256_text  # noqa: F401  (pure, stdlib-only, no state)

REPO = Path(__file__).resolve().parents[3]
EXP_ROOT = Path(os.environ.get("SC_ROOT", str(REPO / "memory" / "experiments" / "strategy_characterization")))
OLLAMA_URL = os.environ.get("SC_OLLAMA_URL", "http://127.0.0.1:11434")

# This experiment's own master seed + a fresh, disjoint offset. Disjointness from every
# prior offset in this codebase (0, 100, 5000, 5100, 7000, 40000 [AP-0]; 90000
# [persistent_routing]) was confirmed empirically via direct token-overlap check before
# any real call was made, per this project's own established discipline.
MASTER_SEED = 20260927
SEED_OFFSET = 120000

MODEL = "qwen2.5-coder:7b"
OPTIONS = {"temperature": 0.2, "top_p": 1.0, "num_predict": 512, "num_ctx": 4096}
STRATEGIES = ("DIRECT", "STEPWISE", "WORKED_EXAMPLE")
KIND = "K2"
N_WORLDS = 3
K_REPEATS = 4


def seed_for(replicate: str, key: str, sample: int) -> int:
    """Matched-seed convention, same shape as AP-0's and persistent_routing's own
    seed_for(), under this experiment's own SC| namespace so seed spaces can never
    collide even by coincidence."""
    return int(sha256_text(f"SC|{MASTER_SEED}|{replicate}|{key}|{sample}")[:8], 16) % (2 ** 31 - 1)


def write_json_new(p, obj) -> None:
    """Refuse-to-overwrite write -- identical contract to every prior experiment
    package's own version, duplicated (not imported) since it's a private module detail,
    not part of AP-0's exported pure-helper surface."""
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
