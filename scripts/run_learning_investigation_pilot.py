#!/usr/bin/env python3
"""
Phase 10 live pilot for the Echo Learning Investigation.

Uses the FROZEN apparatus (audits/echo_learning_experiment_spec.json) --
no code in app/experiments/learning/ is modified by this script or after
it begins running, per mission Section 20. If a defect is found mid-run,
it is documented in the final report, not silently patched.

Small N, per the mission's own "do not immediately launch a huge N"
instruction: ONE world, tested for both echo and the non-Echo control
across every condition; each Formation event's world provides all three
test categories (seen/recombined/novel) so a single teaching event
serves every measurement, rather than re-teaching per category.

Conditions run: A (context-only), B (session boundary), D (retrieval
blocked -- run before C so the real ~30min wait required for C's own
retrieval window is used productively watching A/B/D/F run, not idled).
C's real retention test is scheduled at least 30 real wall-clock minutes
after its own Formation write, per the frozen spec's explicit,
non-negotiable timing requirement (conversation_service.py's real,
unmodified 30-minute recency exclusion). Condition E is not run --
architecturally inapplicable, see the architecture audit.

Environment: sets the KMP/OpenMP guard itself (see spec §11) so this
script is self-sufficient, matching run.py's own convention.
"""

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import json
import subprocess
import sys
import time
import uuid

sys.path.insert(0, ".")

from app.experiments.learning import harness, prompts, scoring, store, world_gen  # noqa: E402
from app.experiments.learning.schema import Condition, LearningTrial, TestCategory  # noqa: E402
from app.experiments.learning.state_instrumentation import capture_state_snapshot  # noqa: E402

PROTOCOL_VERSION = "LEARN-P1-PILOT-1"
WORLD_SEED = 20260903
CONDITION_C_WAIT_SECONDS = 1850  # >30 real minutes, per the frozen spec's non-negotiable timing requirement


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "UNAVAILABLE"


def _git_dirty() -> bool:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL).decode()
        return bool(out.strip())
    except Exception:
        return True


with open("audits/echo_learning_experiment_spec.json") as f:
    _SPEC = json.load(f)
PROTOCOL_HASH = _SPEC["frozen_hashes"]["app/experiments/learning/world_gen.py"][:16]


def _build_trial(session_id, condition, model, model_kind, formation_text, formation_response,
                  test_prompt, raw_response, latency, world, scored, state_before, state_after,
                  retrieval_results, retrieval_blocked):
    return LearningTrial(
        experiment_version=PROTOCOL_VERSION, protocol_hash=PROTOCOL_HASH,
        world_seed=world.seed, world_hash=world.world_hash,
        trial_id=str(uuid.uuid4()), timestamp=time.time(), condition=condition,
        session_id=session_id, model=model, model_version_note=model_kind,
        formation_text=formation_text, test_prompt=test_prompt.prompt_text,
        test_label_map=test_prompt.label_map, raw_response=raw_response,
        entity_name=test_prompt.entity_name, test_category=test_prompt.category,
        has_trait=test_prompt.has_trait, correct_substance=test_prompt.correct_substance,
        parser_primary=scored["parser_primary"], parser_secondary=scored["parser_secondary"],
        parser_combined_status=scored["parser_combined_status"], parser_combined_label=scored["parser_combined_label"],
        selected_substance=scored["selected_substance"], verdict=scored["verdict"],
        backward_reference_detected=scored["backward_reference_detected"],
        implicit_continuity_detected=scored["implicit_continuity_detected"],
        persona_reference_detected=scored["persona_reference_detected"],
        confabulation_flagged=scored.get("confabulation_flagged"), confabulation_note=scored.get("confabulation_note"),
        memory_state_hash_before=(state_before or {}).get("memory_state", {}).get("hash") if state_before else None,
        memory_state_hash_after=(state_after or {}).get("memory_state", {}).get("hash") if state_after else None,
        riverbrain_state_hash_before=(state_before or {}).get("riverbrain_state", {}).get("hash") if state_before else None,
        riverbrain_state_hash_after=(state_after or {}).get("riverbrain_state", {}).get("hash") if state_after else None,
        retrieval_results=retrieval_results, retrieval_blocked=retrieval_blocked,
        git_head=_git_head(), git_dirty=_git_dirty(), latency_seconds=latency,
    )


def _test_all_categories(world):
    """One test prompt per category, using a fresh label_seed per call."""
    seen_entity = world.seen_entities_with_trait[0]
    recombined_entity = world.recombined_entities_with_trait[0]
    novel_entity = world.novel_entities_without_trait[0]
    return {
        "seen": prompts.build_test_prompt(world, seen_entity, True, "seen", label_seed=hash(("seen", world.seed)) % (2**31)),
        "recombined": prompts.build_test_prompt(world, recombined_entity, True, "recombined", label_seed=hash(("recombined", world.seed)) % (2**31)),
        "novel": prompts.build_test_prompt(world, novel_entity, False, "novel", label_seed=hash(("novel", world.seed)) % (2**31)),
    }


def run_conditions_a_b_d(handle, model_kind, world, formation_text, formation_response, results):
    test_prompts = _test_all_categories(world)

    for cat, tp in test_prompts.items():
        state_before = capture_state_snapshot()
        r = harness.run_condition_a_context_only(handle, formation_text, tp)
        state_after = capture_state_snapshot()
        scored = scoring.score_trial_with_world(r["raw_response"], tp, world)
        trial = _build_trial(
            r["session_id"], Condition.A_CONTEXT_ONLY.value, handle.model_name, model_kind,
            formation_text, formation_response, tp, r["raw_response"], r["latency_seconds"],
            world, scored, state_before, state_after, None, None,
        )
        store.append_trial(trial)
        results.append({"condition": "A", "category": cat, "verdict": scored["verdict"], "raw": r["raw_response"][:150]})
        print(f"    [A/{cat}] verdict={scored['verdict']} status={scored['parser_combined_status']} raw={r['raw_response'][:80]!r}")

    for cat, tp in test_prompts.items():
        state_before = capture_state_snapshot()
        r = harness.run_condition_b_session_boundary(handle, formation_text, tp)
        state_after = capture_state_snapshot()
        scored = scoring.score_trial_with_world(r["raw_response"], tp, world)
        trial = _build_trial(
            r["test_session_id"], Condition.B_SESSION_BOUNDARY.value, handle.model_name, model_kind,
            formation_text, formation_response, tp, r["raw_response"], r["latency_seconds"],
            world, scored, state_before, state_after, None, None,
        )
        store.append_trial(trial)
        results.append({"condition": "B", "category": cat, "verdict": scored["verdict"], "raw": r["raw_response"][:150]})
        print(f"    [B/{cat}] verdict={scored['verdict']} status={scored['parser_combined_status']} raw={r['raw_response'][:80]!r}")

    for cat, tp in test_prompts.items():
        state_before = capture_state_snapshot()
        r = harness.run_condition_d_retrieval_blocked(handle, tp)
        state_after = capture_state_snapshot()
        scored = scoring.score_trial_with_world(r["raw_response"], tp, world)
        trial = _build_trial(
            r["session_id"], Condition.D_RETRIEVAL_BLOCKED.value, handle.model_name, model_kind,
            formation_text, formation_response, tp, r["raw_response"], r["latency_seconds"],
            world, scored, state_before, state_after, r["retrieval_memory_block"], r["retrieval_blocked"],
        )
        store.append_trial(trial)
        results.append({"condition": "D", "category": cat, "verdict": scored["verdict"], "raw": r["raw_response"][:150]})
        print(f"    [D/{cat}] verdict={scored['verdict']} status={scored['parser_combined_status']} raw={r['raw_response'][:80]!r}")


def run_condition_c(handle, model_kind, world, formation_text, formation_response, results):
    test_prompts = _test_all_categories(world)
    for cat, tp in test_prompts.items():
        state_before = capture_state_snapshot()
        r = harness.run_condition_c_persistent_memory(handle, formation_text, formation_response, tp, world.world_hash)
        state_after = capture_state_snapshot()
        scored = scoring.score_trial_with_world(r["raw_response"], tp, world)
        trial = _build_trial(
            r["session_id"], Condition.C_PERSISTENT_MEMORY.value, handle.model_name, model_kind,
            formation_text, formation_response, tp, r["raw_response"], r["latency_seconds"],
            world, scored, state_before, state_after, r["retrieval_memory_block"], r["retrieval_blocked"],
        )
        store.append_trial(trial)
        results.append({
            "condition": "C", "category": cat, "verdict": scored["verdict"], "raw": r["raw_response"][:150],
            "retrieval_memory_block": r["retrieval_memory_block"],
        })
        print(f"    [C/{cat}] verdict={scored['verdict']} status={scored['parser_combined_status']} "
              f"retrieved={bool(r['retrieval_memory_block'])} raw={r['raw_response'][:80]!r}")


def main():
    print("=== Echo Learning Investigation: Phase 10 Live Pilot ===")
    print(f"Protocol version: {PROTOCOL_VERSION}")
    print(f"World seed: {WORLD_SEED}")
    print(f"git HEAD: {_git_head()} (dirty: {_git_dirty()})")
    print()

    world = world_gen.generate_world(WORLD_SEED)
    print(f"World: trait={world.trait_name} substances=({world.substance_with_trait}/{world.substance_without_trait})")
    print(f"  seen_with={world.seen_entities_with_trait} seen_without={world.seen_entities_without_trait}")
    print(f"  recombined_with={world.recombined_entities_with_trait} recombined_without={world.recombined_entities_without_trait}")
    print(f"  novel_with={world.novel_entities_with_trait} novel_without={world.novel_entities_without_trait}")
    print(f"  world_hash={world.world_hash} token_balance={world.token_balance_report}")
    print()

    formation_text = prompts.build_formation_text(world)
    print(f"Formation text:\n{formation_text}\n")

    all_results = {"echo": [], "non_echo_control": []}
    formation_records = {}

    for kind, model_name in [("echo", "echo:latest"), ("non_echo_control", "llama3.2:3b")]:
        print(f"--- Formation: {kind} ({model_name}) ---")
        handle = harness.ModelHandle(kind, model_name)
        formation_response, formation_latency = handle.raw_call(formation_text, system=None)
        formation_records[kind] = (handle, formation_response)
        print(f"  formation_response: {formation_response[:200]!r}")
        print(f"  latency: {formation_latency:.2f}s")

        # Explicitly, transparently persist through the real memory-write
        # pathway for Condition C's later use (harness._write_formation_to_real_memory).
        from app.experiments.learning.harness import _write_formation_to_real_memory
        write_result = _write_formation_to_real_memory(formation_text, formation_response, world.world_hash)
        print(f"  persisted to real memory: {write_result}")
        formation_write_time = time.time()
        formation_records[kind] = (handle, formation_response, formation_write_time)

        print(f"--- Conditions A/B/D: {kind} ---")
        run_conditions_a_b_d(handle, kind, world, formation_text, formation_response, all_results[kind])
        print()

    print(f"=== Waiting {CONDITION_C_WAIT_SECONDS}s (>30 real minutes) before Condition C's real retention test ===")
    print("(per the frozen spec's non-negotiable timing requirement -- see spec.md section 3)")
    elapsed_target = min(
        formation_records["echo"][2] + CONDITION_C_WAIT_SECONDS,
        formation_records["non_echo_control"][2] + CONDITION_C_WAIT_SECONDS,
    )
    while time.time() < elapsed_target:
        remaining = elapsed_target - time.time()
        print(f"  ... {remaining:.0f}s remaining")
        time.sleep(min(300, max(1, remaining)))

    for kind in ("echo", "non_echo_control"):
        handle, formation_response, _ = formation_records[kind]
        print(f"--- Condition C: {kind} ---")
        run_condition_c(handle, kind, world, formation_text, formation_response, all_results[kind])
        print()

    print("=== Pilot execution complete. Raw data in memory/experiments/learning/. ===")
    out_path = "audits/echo_learning_investigation_pilot_results.json"
    with open(out_path, "w") as f:
        json.dump(
            {
                "protocol_version": PROTOCOL_VERSION, "world_seed": WORLD_SEED,
                "world": world.to_dict(), "formation_text": formation_text,
                "git_head": _git_head(), "git_dirty": _git_dirty(), "timestamp": time.time(),
                "results": all_results,
            },
            f, indent=2, default=str,
        )
    print(f"Full results written to {out_path}")


if __name__ == "__main__":
    main()
