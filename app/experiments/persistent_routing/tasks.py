"""Task substrate -- reuses AP-0's worlds.py/tasks_v2.py verbatim (frozen
design §4/§20: 'ALREADY EXISTS'), never edited, never duplicated. A fresh,
disjoint seed range (SEED_OFFSET=90000) is drawn specifically for this
experiment, confirmed disjoint from every prior offset in this codebase."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import worlds, tasks_v2 as T2  # noqa: E402
from .common import SEED_OFFSET, MASTER_SEED


def build_world(kind: str, w: int, taken: set) -> dict:
    """One fresh {K1,K2,K3} realization dict, at this experiment's own
    seed offset -- tasks_v2.build_tasks_v2() needs all three kinds present
    even though a pilot may only exercise one (same reason AP-0's own
    qual2.py generates a full triple; see that module's own comment)."""
    return {k: worlds.make_realization(k, MASTER_SEED + SEED_OFFSET + 10 * i + w, taken)
            for i, k in enumerate(("K1", "K2", "K3"))}


def real_procedure_text(kind: str, realization: dict) -> str:
    """The real, correct convention text -- supplied identically to every
    strategy in every arm (PREREG_ADDENDUM.md 'Blocker 1': this experiment
    tests routing, not induction, so the solving information is given)."""
    import app.experiments.accumulation_probe.tasks as T1
    return T1.procedure_text(realization[kind])


def split_tasks(world: dict, kind: str) -> "tuple[list, list]":
    """Returns (T_tasks, S_tasks) for the given kind -- NEAR/UNREL are not
    used by the pilot (PREREG_ADDENDUM.md's own reduced pilot scope; both
    remain part of the frozen design for the full confirmatory run)."""
    all_tasks = T2.build_tasks_v2(world)
    t = [x for x in all_tasks if x["kind"] == kind and x["split"] == "T"]
    s = [x for x in all_tasks if x["kind"] == kind and x["split"] == "S"]
    return t, s


def make_hidden_tests(task: dict, world: dict, partition: str):
    """Wraps tasks_v2.make_cases2() -- returns (test_code, n_cases)."""
    cases, _equiv = T2.make_cases2(task, world, partition)
    return T2.make_test_code(task["fn"], cases), len(cases)
