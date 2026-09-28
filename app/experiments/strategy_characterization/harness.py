#!/usr/bin/env python3
"""Harness for the K2 strategy-characterization study, executed under the CORRECTED,
controlling frozen protocol:
audits/2026-09-27_strategy_characterization_protocol_design.md
(provenance/hash chain: audits/2026-09-27_strategy_characterization_protocol_PROVENANCE.md)

No persistent learning of any kind: no selector, no state file, no epsilon-greedy, no
reward update, no cross-trial memory. Every replicate is a fresh, independent,
stateless generation. Strategies are imported unmodified from
app.experiments.persistent_routing.strategies (Decision A, frozen design Section 1) --
never redefined here.

Two commands:
  phase0    -- mandatory seed-determinism smoke test (2 calls). Must PASS before stage1.
  stage1    -- the 216-generation Discovery characterization.
"""
from __future__ import annotations
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.accumulation_probe import oracle_runner as OR  # noqa: E402
import app.experiments.accumulation_probe.ollama_client as OC2  # noqa: E402
from app.experiments.accumulation_probe.common import OLLAMA_URL as AP0_OLLAMA_URL  # noqa: E402
from app.experiments.persistent_routing.strategies import build_prompt  # noqa: E402  (Decision A: exact existing strategies, unmodified)

from . import tasks as SCT  # noqa: E402
from .common import (  # noqa: E402
    EXP_ROOT, MODEL, OPTIONS, STRATEGIES, N_WORLDS, K_REPEATS,
    sha256_text, write_json_new, append_jsonl, seed_for,
)

_SYSTEM_PROMPT = (
    "You are a careful Python programmer. Respond with exactly one fenced "
    "Python code block that defines the requested function. Do not include "
    "explanations, tests, or example calls outside the code block."
)


def _generate_and_grade(task, world, strategy, seed):
    """One real, seeded generation + real sandboxed grade. Returns (grade_dict, raw_text, code_hash)."""
    procedure = SCT.real_procedure_text(world)
    prompt = build_prompt(strategy, task, procedure)
    body = OC2.request_body(MODEL, _SYSTEM_PROMPT, prompt, seed, OPTIONS)
    try:
        resp = OC2.chat(body, AP0_OLLAMA_URL, timeout=180)
        raw = resp["text"]
    except Exception as e:
        return {"passed": False, "ran_ok": False, "infra": True, "timeout": False, "error": str(e)}, "", sha256_text("")
    code = OR.extract_code(raw, task["fn"])
    test_code, _n = SCT.make_hidden_tests(task, world, "VAL")
    grade = OR.grade(code, test_code) if code else {"passed": False, "ran_ok": False, "infra": False, "timeout": False}
    return grade, raw, sha256_text(code or "")


def cmd_phase0():
    """Mandatory pre-flight: 2 real calls, IDENTICAL seed and prompt, compare output.
    Frozen protocol Section 6/13: if this fails, STOP -- do not repair around it."""
    d = EXP_ROOT / "phase0"
    d.mkdir(parents=True, exist_ok=True)
    taken: set = set()
    world = SCT.build_world(world_index=999, taken=taken)  # reserved smoke-test world index, never reused
    task = SCT.discovery_tasks(world)[0]  # K2.T1, pick_winner
    procedure = SCT.real_procedure_text(world)
    prompt = build_prompt("DIRECT", task, procedure)
    seed = seed_for("SMOKE", "phase0_determinism_check", 0)
    body = OC2.request_body(MODEL, _SYSTEM_PROMPT, prompt, seed, OPTIONS)

    resp1 = OC2.chat(body, AP0_OLLAMA_URL, timeout=180)
    resp2 = OC2.chat(body, AP0_OLLAMA_URL, timeout=180)
    identical = resp1["text"] == resp2["text"]

    result = {
        "identical": identical, "seed": seed, "task_id": task["task_id"], "strategy": "DIRECT",
        "len1": len(resp1["text"]), "len2": len(resp2["text"]),
        "text1": resp1["text"], "text2": resp2["text"],
        "prompt": prompt, "system": _SYSTEM_PROMPT,
    }
    write_json_new(d / "phase0_result.json", result)
    print(f"[PHASE0] task={task['task_id']} strategy=DIRECT seed={seed}")
    print(f"[PHASE0] len1={len(resp1['text'])} len2={len(resp2['text'])} identical={identical}")
    if not identical:
        print("[PHASE0] FAIL -- seed-determinism claim is NOT confirmed by this Ollama server.")
        print("[PHASE0] STOP per frozen protocol Section 6/13. Do not proceed to stage1.")
        sys.exit(1)
    print("[PHASE0] PASS -- identical output confirmed for identical seed+prompt. Stage 1 may proceed.")


def _build_call_grid():
    """Full factorial: 6 discovery tasks x 3 worlds x 3 strategies x 4 repeats = 216.
    Returns (worlds_by_index, call_list) where call_list is a list of
    (task_id, world_index, strategy, repeat_index, task_dict) tuples, in the
    pre-registered RANDOMIZED order (frozen protocol Section 3 -- not blocked by
    strategy, order seeded independently of the generation seeds)."""
    worlds_by_index = {}
    for w in range(N_WORLDS):
        taken: set = set()
        worlds_by_index[w] = SCT.build_world(world_index=w, taken=taken)

    call_list = []
    for w, world in worlds_by_index.items():
        for task in SCT.discovery_tasks(world):
            for strategy in STRATEGIES:
                for rep in range(K_REPEATS):
                    call_list.append((task["task_id"], w, strategy, rep, task))

    order_rng = random.Random(seed_for("ORDER", "stage1_call_order", 0))
    order_rng.shuffle(call_list)
    return worlds_by_index, call_list


def cmd_stage1():
    d = EXP_ROOT / "stage1"
    d.mkdir(parents=True, exist_ok=True)
    worlds_by_index, call_list = _build_call_grid()

    for w, world in worlds_by_index.items():
        world_path = d / f"world_{w}.json"
        if not world_path.exists():
            write_json_new(world_path, world)

    log_path = d / "log_stage1.jsonl"
    done_keys = {(r["task_id"], r["world_index"], r["strategy"], r["repeat_index"]) for r in _read_existing(log_path)}

    total = len(call_list)
    for i, (task_id, w, strategy, rep, task) in enumerate(call_list, 1):
        key = (task_id, w, strategy, rep)
        if key in done_keys:
            continue  # resume-safe: skip already-completed replicates on a re-run
        world = worlds_by_index[w]
        seed = seed_for("CHAR", f"{task_id}|{w}|{strategy}", rep)
        grade, raw, code_hash = _generate_and_grade(task, world, strategy, seed)
        row = {
            "task_id": task_id, "world_index": w, "strategy": strategy, "repeat_index": rep,
            "seed": seed, "passed": bool(grade.get("passed")), "ran_ok": bool(grade.get("ran_ok")),
            "infra": bool(grade.get("infra", False)), "timeout": bool(grade.get("timeout", False)),
            "code_hash": code_hash, "raw_response": raw,
            "output_tail": grade.get("output_tail", ""), "error_tail": grade.get("error_tail", ""),
        }
        append_jsonl(log_path, row)
        print(f"[stage1 {i}/{total}] {task_id} world={w} strategy={strategy} rep={rep} "
              f"passed={row['passed']} infra={row['infra']}")

    print(f"[stage1] DONE. {total} replicates logged to {log_path}")


def _read_existing(log_path):
    from .common import read_jsonl
    return read_jsonl(log_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["phase0", "stage1"])
    a = ap.parse_args()
    if a.phase == "phase0":
        cmd_phase0()
    elif a.phase == "stage1":
        cmd_stage1()
