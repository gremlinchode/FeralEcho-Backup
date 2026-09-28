"""Task substrate -- thin reuse wrapper, verbatim re-import of already-proven
generators (accumulation_probe.worlds/tasks_v2, strategy_characterization.tasks'
own discovery/confirmation split). No duplication of task-generation logic."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import worlds, tasks_v2 as T2  # noqa: E402
import app.experiments.accumulation_probe.tasks as T1  # noqa: E402
from .common import SEED_OFFSET, MASTER_SEED, KIND  # noqa: E402


def build_world(world_index: int, taken: set) -> dict:
    """One fresh {K1,K2,K3} realization at this module's own seed offset. world_index
    999 is reserved for smoke/dev use, never a real experiment world."""
    return {k: worlds.make_realization(k, MASTER_SEED + SEED_OFFSET + 10 * i + world_index, taken)
            for i, k in enumerate(("K1", "K2", "K3"))}


def real_procedure_text(world: dict) -> str:
    return T1.procedure_text(world[KIND])


def discovery_tasks(world: dict) -> list:
    """K2's 6 real T-split templates (the 'source experience' pool)."""
    all_tasks = T2.build_tasks_v2(world)
    return [t for t in all_tasks if t["kind"] == KIND and t["split"] == "T"]


def confirmation_tasks(world: dict) -> list:
    """K2's 4 real S-split templates -- structurally distinct held-out pool."""
    all_tasks = T2.build_tasks_v2(world)
    return [t for t in all_tasks if t["kind"] == KIND and t["split"] == "S"]


def make_hidden_tests(task: dict, world: dict, partition: str):
    cases, _equiv = T2.make_cases2(task, world, partition)
    return T2.make_test_code(task["fn"], cases), len(cases)
