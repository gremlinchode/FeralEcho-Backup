"""Task substrate -- reuses AP-0's worlds.py/tasks_v2.py verbatim, never edited, never
duplicated (frozen protocol Section 2: "reuse K2's existing, already-frozen task
registry unmodified"). Discovery = K2's 6 real T-split templates; Confirmation (Stage 2,
not run by Stage 1) = K2's 4 real S-split templates, held out and untouched here."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import worlds, tasks_v2 as T2  # noqa: E402
import app.experiments.accumulation_probe.tasks as T1  # noqa: E402
from .common import SEED_OFFSET, MASTER_SEED, KIND  # noqa: E402


def build_world(world_index: int, taken: set) -> dict:
    """One fresh {K1,K2,K3} realization dict at this experiment's own seed offset --
    tasks_v2.build_tasks_v2() needs all three kinds present even though only K2 is
    exercised (same reason every prior experiment package in this codebase does this).
    world_index=999 is reserved for the Phase-0 smoke test only, never used as a real
    Discovery/Confirmation world."""
    return {k: worlds.make_realization(k, MASTER_SEED + SEED_OFFSET + 10 * i + world_index, taken)
            for i, k in enumerate(("K1", "K2", "K3"))}


def real_procedure_text(world: dict) -> str:
    """The real, correct convention text -- supplied identically to every strategy
    (frozen protocol Section 2/Blocker-1 inheritance: this study tests routing, not
    induction, so the solving information is given)."""
    return T1.procedure_text(world[KIND])


def discovery_tasks(world: dict) -> list:
    """K2's 6 real T-split templates (tasks_v2.py's KT["K2"])."""
    all_tasks = T2.build_tasks_v2(world)
    return [t for t in all_tasks if t["kind"] == KIND and t["split"] == "T"]


def confirmation_tasks(world: dict) -> list:
    """K2's 4 real S-split templates (tasks_v2.py's KS["K2"]) -- held out, not touched
    by Stage 1; reserved for a possible, separately-authorized Stage 2."""
    all_tasks = T2.build_tasks_v2(world)
    return [t for t in all_tasks if t["kind"] == KIND and t["split"] == "S"]


def make_hidden_tests(task: dict, world: dict, partition: str):
    """Wraps tasks_v2.make_cases2() -- returns (test_code, n_cases). partition="VAL",
    matching the persistent-routing pilot's own established, safe convention."""
    cases, _equiv = T2.make_cases2(task, world, partition)
    return T2.make_test_code(task["fn"], cases), len(cases)
