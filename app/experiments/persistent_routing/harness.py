#!/usr/bin/env python3
"""Multi-phase harness for the persistent-routing-learning PILOT (frozen
design + PREREG_ADDENDUM.md). Each subcommand invocation is meant to be
launched as its own OS subprocess (mirroring qual.py's own multi-phase
CLI shape) -- this is what makes the restart-boundary intervention (§13)
real rather than simulated: `run-arm` and `run-holdout` genuinely start
and exit as separate processes when driven by run_pilot.py's subprocess
launches, not by direct in-process function calls.

Disclosed, deliberate pilot-scope reductions (mirroring QUAL-2's own
disclosed scope reduction for the same reason -- a cheap, bounded,
exploratory pass, not the full statistically-powered confirmatory run):
- Only Arms B (update-disabled twin) and C (adaptive) are run -- Arm A
  (hand-built champion) is deferred to the full run per PREREG_ADDENDUM's
  own note that the pilot's statistical purpose (§17) is specifically the
  C-vs-B gap and its variance.
- Only T and S splits are generated -- NEAR/UNREL (specificity/confound
  controls) are part of the frozen design for the full run, not needed to
  estimate the core effect size this pilot exists to measure.
- No jail.py-style OS-level sandboxing of the generation calls themselves
  (oracle_runner.grade() still runs candidate code under real
  sandbox-exec, per its own existing contract) -- full AP-0-style jailing
  of the harness's own generation step is deferred to the full run.
"""
from __future__ import annotations
import argparse
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import ollama_client as OC, oracle_runner as OR  # noqa: E402
from app.experiments.persistent_routing import tasks as PT, provenance as PROV  # noqa: E402
from app.experiments.persistent_routing.common import (  # noqa: E402
    EXP_ROOT, MODEL, OPTIONS, TASK_TYPE_KEY, sha256_text, write_json_new, read_json,
    read_jsonl, seed_for,
)
from app.experiments.persistent_routing.features import feature_signature  # noqa: E402
from app.experiments.persistent_routing.selector import Selector, extract_sanitized_outcome  # noqa: E402
from app.experiments.persistent_routing.strategies import build_prompt  # noqa: E402

from app.experiments.accumulation_probe.common import OLLAMA_URL as AP0_OLLAMA_URL  # noqa: E402

# BUG FOUND AND FIXED 2026-09-27, before any holdout comparison was trusted:
# the frozen design's §8 "matched-seed convention" requires every stochastic
# call to be seeded per (lineage, task_id) -- but _ollama_query()/
# stream_query_ollama() (river_deliberation.py/ollama_handler.py) have NO
# seed parameter anywhere in their call chain (confirmed by direct grep:
# zero occurrences of "seed" in ollama_handler.py). Using _ollama_query()
# as originally written silently violated the design's own determinism
# requirement -- caught only by noticing that Arm B and Arm C, having both
# selected the identical strategy (DIRECT) for the identical task_ids,
# produced DIFFERENT real pass/fail patterns on the holdout set, which is
# not supposed to be possible if seeding actually held. Switched to AP-0's
# own ollama_client.py (already proven, already used by QUAL-1/QUAL-2
# earlier the same session) instead, which DOES support a real seed in its
# request body -- and, as a genuine bonus rather than a compromise, this
# also *simplifies* the channel-isolation story from PREREG_ADDENDUM's
# 'Blocker 4' section: ollama_client.py has zero interaction with
# production's _cb_state circuit breaker at all (not merely neutralized by
# a dedicated task_type key, but structurally absent), so the two
# separately-tracked risks (determinism, circuit-breaker contamination)
# are both closed by the same one change. All data collected before this
# fix (lineage 0's first pass) was discarded and re-collected, not patched
# around -- per this whole project's own standing discipline that a broken
# control invalidates the comparison, not just the specific numbers.
import app.experiments.accumulation_probe.ollama_client as OC2  # noqa: E402

KIND = "K2"  # the pilot's single convention kind (real, non-trivial structure)


def _lineage_dir(lineage: int) -> Path:
    return EXP_ROOT / f"lineage_{lineage}"


def cmd_build(lineage: int):
    d = _lineage_dir(lineage)
    if d.exists():
        sys.exit(f"STOP: {d} already exists -- refusing to overwrite (delete by hand for a genuine re-build).")
    taken = set()
    world = PT.build_world(KIND, lineage, taken)
    write_json_new(d / "world.json", world)

    t_tasks, s_tasks = PT.split_tasks(world, KIND)
    # DEV: unused by this reduced pilot (no Arm A champion fit) -- kept as
    # an empty, explicit marker so the full run's DEV phase has an obvious
    # slot to fill in later, per the frozen design's own three-partition
    # structure, rather than silently omitted.
    write_json_new(d / "dev_tasks.json", [])
    write_json_new(d / "prospective_tasks.json", t_tasks)   # T split: PROSPECTIVE phase
    write_json_new(d / "holdout_tasks.json", s_tasks)       # S split: HOLDOUT phase (structural transfer)
    print(f"[build] lineage {lineage}: {len(t_tasks)} prospective (T) tasks, {len(s_tasks)} holdout (S) tasks.")


def _real_procedure(world):
    return PT.real_procedure_text(KIND, world)


_SYSTEM_PROMPT = (
    "You are a careful Python programmer. Respond with exactly one fenced "
    "Python code block that defines the requested function. Do not include "
    "explanations, tests, or example calls outside the code block."
)


def _run_one_decision(task, world, strategy, seed):
    """One real, SEEDED generation + grade, for one task under one strategy.
    Uses AP-0's own ollama_client (OC2), not river_deliberation._ollama_query
    -- see the module-level comment above for why. Returns (passed: bool,
    candidate_code_hash: str)."""
    procedure = _real_procedure(world)
    prompt = build_prompt(strategy, task, procedure)
    body = OC2.request_body(MODEL, _SYSTEM_PROMPT, prompt, seed, OPTIONS)
    try:
        resp = OC2.chat(body, AP0_OLLAMA_URL, timeout=180)
        raw = resp["text"]
    except Exception as e:
        return {"passed": False, "ran_ok": False, "infra": True, "timeout": False, "error": str(e)}, sha256_text("")
    code = OR.extract_code(raw, task["fn"])
    test_code, _n = PT.make_hidden_tests(task, world, "VAL")
    grade = OR.grade(code, test_code) if code else {"passed": False, "ran_ok": False, "infra": False, "timeout": False}
    code_hash = sha256_text(code or "")
    return grade, code_hash


def cmd_run_arm(lineage: int, arm: str):
    """Process 2 (§13): a fresh process, no shared memory with any other
    invocation. Loads S0 (fresh, empty selector -- both B and C start
    identical), runs the real PROSPECTIVE phase, saves S1 (or, for arm B,
    a byte-identical copy of S0 since update() is never called), exits."""
    d = _lineage_dir(lineage)
    world = read_json(d / "world.json")
    prospective = read_json(d / "prospective_tasks.json")

    s0 = Selector()  # both B and C start from the byte-identical, empty S0
    s0_hash = s0.content_hash()
    write_json_new(d / f"S0_{arm}.hash", {"hash": s0_hash})

    rng = random.Random(seed_for("PROSPECTIVE", f"lineage{lineage}", 0))
    for task in prospective:
        sig = feature_signature(task["sig"], task["spec"])
        if arm == "C":
            strategy, prob = s0.select(sig, explore=True, rng=rng)
        else:  # arm B: architecture present, but selection is frozen at S0's initial (empty) state
            strategy, prob = s0.select(sig, explore=False, rng=rng)
        grade, _hash = _run_one_decision(task, world, strategy, seed_for("PROSPECTIVE", task["task_id"], 0))
        outcome = extract_sanitized_outcome(grade)
        PROV.log_experience(f"{lineage}_{arm}", task["task_id"], sig, strategy, outcome)
        if arm == "C":
            pre, post = s0.update(sig, strategy, outcome)
            PROV.log_update(f"{lineage}_{arm}", pre, post, sha256_text(Path(__file__).read_text()))
        print(f"[run-arm {arm} L{lineage}] {task['task_id']} strategy={strategy} outcome={'PASS' if outcome else 'FAIL'}")

    final_hash = s0.save(str(d / f"S1_{arm}.json"))
    print(f"[run-arm {arm} L{lineage}] DONE. S1 hash: {final_hash} (S0 was: {s0_hash})")


def cmd_run_holdout(lineage: int, arm: str, state_label: str):
    """Process 3 (§13): fresh process, loads a NAMED state file (S1 for the
    real run, or S0 for the replacement test), runs holdout decisions with
    NO exploration (pure greedy, per §14), grades, logs. state_label names
    which saved state to load -- decoupled from `arm` so the replacement/
    restoration test (§13 steps 4-5) can load S0 under arm C's own code
    path without needing a separate arm identity."""
    d = _lineage_dir(lineage)
    world = read_json(d / "world.json")
    holdout = read_json(d / "holdout_tasks.json")

    state_path = d / f"{state_label}.json"
    s = Selector.load(str(state_path))
    state_hash = s.content_hash()

    results = []
    for task in holdout:
        sig = feature_signature(task["sig"], task["spec"])
        seed = seed_for("HOLDOUT", task["task_id"], 0)
        rng = random.Random(seed)
        strategy, prob = s.select(sig, explore=False, rng=rng)
        PROV.log_decision(f"{lineage}_{arm}_{state_label}", arm, task["task_id"], state_hash, sig, strategy, prob, seed)
        grade, code_hash = _run_one_decision(task, world, strategy, seed)
        PROV.log_execution(f"{lineage}_{arm}_{state_label}", arm, task["task_id"], code_hash, MODEL)
        passed = bool(grade.get("passed"))
        PROV.log_outcome(f"{lineage}_{arm}_{state_label}", arm, task["task_id"], passed,
                          "n/a", sha256_text(Path(__file__).read_text()),
                          infra=grade.get("infra", False), timeout=grade.get("timeout", False))
        results.append({"task_id": task["task_id"], "strategy": strategy, "passed": passed})
        print(f"[holdout {arm}/{state_label} L{lineage}] {task['task_id']} strategy={strategy} passed={passed}")

    write_json_new(d / f"holdout_result_{arm}_{state_label}.json", {"state_hash": state_hash, "results": results,
                    "pass_rate": sum(r["passed"] for r in results) / max(1, len(results))})
    print(f"[holdout {arm}/{state_label} L{lineage}] DONE. pass_rate={sum(r['passed'] for r in results)}/{len(results)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["build", "run-arm", "run-holdout"])
    ap.add_argument("--lineage", type=int, required=True)
    ap.add_argument("--arm", choices=["B", "C"])
    ap.add_argument("--state", default=None, help="state label to load for run-holdout, e.g. S1_C or S0_C")
    a = ap.parse_args()
    if a.phase == "build":
        cmd_build(a.lineage)
    elif a.phase == "run-arm":
        cmd_run_arm(a.lineage, a.arm)
    elif a.phase == "run-holdout":
        cmd_run_holdout(a.lineage, a.arm, a.state)
