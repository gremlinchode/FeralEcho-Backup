#!/usr/bin/env python3
"""
TIER-4 CONFIRMATORY EXPERIMENT RUNNER.

Follows audits/tier4_confirmatory_protocol.md (frozen, hashed). Reuses,
does NOT duplicate, the proven mechanism from scripts/run_tier3_apparatus.py
(itself built on scripts/run_capability_pilot.py) -- isolation, model
pinning, truncation capture, classify_result, the four run_condition_*
functions, randomized_arm_order -- imported as a library, not copy-pasted.

Two things are genuinely new here, both required by the frozen protocol
and not present in the Tier-3 apparatus:

1. Finding A fix: BASEN_SYNTHESIS_SYSTEM_TEMPLATE's "coherence and
   correctness" -> "coherence and relevance", applied via a module-level
   patch on the imported run_tier3_apparatus module (see
   _apply_finding_a_fix()) -- makes BASE_N's synthesis prompt wording
   match ARCH_COUNCIL's real production template exactly, removing a
   bias that previously favored BASE_N. Asserted to actually change the
   string (not a silent no-op if the source ever drifts).

2. Mechanism instrumentation: a capturing wrapper around
   river_deliberation._ollama_query, installed for the duration of each
   candidate's generation only, recording every real underlying call
   (model, prompt length, temperature, FULL response text) -- needed for
   the Phase 9 mechanism analysis (did synthesis destroy a correct
   pre-synthesis candidate?). This composes cleanly with
   run_condition_arch_council()'s own internal model-name-only recording
   wrapper (see the composition reasoning in this file's own comments
   below) and with run_condition_basen()'s per-call fresh
   `from river_deliberation import _ollama_query` re-import (which reads
   the module's current, patched attribute at call time, not a cached
   reference) -- verified directly, not assumed, in Phase 5b.
"""
import hashlib
import json
import os
import sys
import time

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_capability_pilot as base_pilot  # noqa: E402
import run_tier3_apparatus as t3  # noqa: E402

TIER4_DIR = "audits/tier4_apparatus"
PINNED_MODEL_PATH = f"{TIER4_DIR}/pinned_model.json"

STAGE_SUITE_PATHS = {
    1: f"{TIER4_DIR}/tier4_stage1_task_suite.json",
    2: f"{TIER4_DIR}/tier4_stage2_task_suite.json",
}
STAGE_SUITE_HASHES = {
    1: "a0585ad858d83859242ce8ffb1f369bb7802cfb3174b6c931da48e3da551a79a",
    2: "2736c737db0a9c2493a6be6b0adefc19a1d3d76ab6d75d2c4b64674f0243bbca",
}
STAGE_RESULTS_PATHS = {
    1: f"{TIER4_DIR}/stage1_results.jsonl",
    2: f"{TIER4_DIR}/stage2_results.jsonl",
}
DEV_SANITY_RESULTS_PATH = f"{TIER4_DIR}/dev_sanity_results.jsonl"


# ---------------------------------------------------------------------------
# Finding A fix
# ---------------------------------------------------------------------------

def apply_finding_a_fix() -> None:
    before = t3.BASEN_SYNTHESIS_SYSTEM_TEMPLATE
    after = before.replace(
        "Weigh each attempt according to its coherence and correctness.",
        "Weigh each attempt according to its coherence and relevance.",
    )
    assert after != before, (
        "Finding A fix is a no-op -- the expected source string was not found. "
        "BASEN_SYNTHESIS_SYSTEM_TEMPLATE may have changed since this fix was written; "
        "STOP and re-check before proceeding."
    )
    t3.BASEN_SYNTHESIS_SYSTEM_TEMPLATE = after
    print("[setup] Finding A fix applied: BASE_N synthesis template now reads "
          "'coherence and relevance' (matches real production SYNTHESIS_SYSTEM_TEMPLATE wording)")


# ---------------------------------------------------------------------------
# Mechanism instrumentation -- captures every real underlying _ollama_query
# call (model, temperature, prompt length, FULL response text) for the
# duration of one candidate's generation.
# ---------------------------------------------------------------------------

_mechanism_capture_active = [False]
_mechanism_calls_this_candidate = []


def _install_mechanism_capture():
    """Wrap river_deliberation._ollama_query so every real call this
    candidate makes (whether via run_condition_basen's per-call fresh
    import or run_condition_arch_council's own internal recording
    wrapper, which composes on top of this one -- see module docstring)
    is captured with its full response text. Returns the function to
    restore afterward."""
    import app.core.river_deliberation as rd
    _real = rd._ollama_query

    def _capturing_ollama_query(model_name, prompt, *args, **kwargs):
        response = _real(model_name, prompt, *args, **kwargs)
        if _mechanism_capture_active[0]:
            _mechanism_calls_this_candidate.append({
                "model": model_name,
                "prompt_char_len": len(prompt) if prompt else 0,
                "temperature": kwargs.get("temperature"),
                "response_text": response,
            })
        return response

    rd._ollama_query = _capturing_ollama_query
    return _real


def _restore_mechanism_capture(real_fn):
    import app.core.river_deliberation as rd
    rd._ollama_query = real_fn


# ---------------------------------------------------------------------------
# Model pinning -- reuse the IDENTICAL model pinned for the Tier-3 pilot
# (protocol §8), persisted to a NEW, separate file so the Tier-3 artifact
# is never touched.
# ---------------------------------------------------------------------------

def pin_model_for_tier4() -> str:
    if os.path.exists(PINNED_MODEL_PATH):
        with open(PINNED_MODEL_PATH) as f:
            return json.load(f)["pinned_model"]
    with open("audits/tier3_apparatus/pinned_model.json") as f:
        tier3_pin = json.load(f)["pinned_model"]
    os.makedirs(TIER4_DIR, exist_ok=True)
    with open(PINNED_MODEL_PATH, "w") as f:
        json.dump({
            "pinned_model": tier3_pin,
            "pinned_at": time.time(),
            "source": "reused from audits/tier3_apparatus/pinned_model.json, per protocol §8",
        }, f)
    return tier3_pin


# ---------------------------------------------------------------------------
# Shared per-(task, arm) execution -- mirrors
# run_tier3_apparatus._run_single_candidate() exactly (same classification/
# logging shape, reused functions), adding only the mechanism-capture
# wrap/unwrap and the mechanism_calls field on the record.
# ---------------------------------------------------------------------------

def _run_single_candidate(task: dict, arm: str, pinned_model: str, proxy, seed: int, order: list,
                           results_path: str, extra_fields: dict = None) -> dict:
    record = {
        "task_id": task["task_id"], "arm": arm, "seed": seed, "arm_order": order,
        "timestamp": time.time(),
    }
    if extra_fields:
        record.update(extra_fields)

    _mechanism_calls_this_candidate.clear()
    _mechanism_capture_active[0] = True
    try:
        if arm == "BASE_1":
            gen = t3.run_condition_base1(task, pinned_model)
        elif arm == "BASE_N":
            gen = t3.run_condition_basen(task, pinned_model)
        elif arm == "ARCH_PIPELINE_ISOLATED":
            gen = t3.run_condition_arch_pipeline(task, pinned_model)
        else:
            gen = t3.run_condition_arch_council(task, proxy)
        record.update(gen)
        verify = base_pilot.objective_verify(gen["candidate_code"], task["test_code"])
        record.update(verify)
        classification, evidence_type = t3.classify_result(
            gen.get("raw_response", gen.get("candidate_code", "")), gen["candidate_code"], verify,
            call_id=gen.get("call_id"),
        )
        record["classification"] = classification
        record["truncation_evidence_type"] = evidence_type
    except Exception as e:
        failure_class = base_pilot._classify_exception(e)
        record["error"] = f"{type(e).__name__}: {e}"
        record["passed"] = False
        record["classification"] = failure_class
    finally:
        _mechanism_capture_active[0] = False

    # Mechanism instrumentation (new, Tier-4 only): every real underlying
    # call this candidate made, full response text included, for later
    # (Phase 9) analysis of whether synthesis preserved or destroyed a
    # correct pre-synthesis candidate. Never influences scoring above --
    # captured strictly after classify_result() has already run.
    record["mechanism_calls"] = list(_mechanism_calls_this_candidate)

    record["side_effects_so_far"] = len(base_pilot._side_effects_detected)
    with open(results_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    print(f"  {arm}: classification={record.get('classification')} "
          f"passed={record.get('passed')} model={record.get('model_used')} "
          f"calls={record.get('total_calls')} mechanism_calls={len(record['mechanism_calls'])} "
          f"side_effects_total={len(base_pilot._side_effects_detected)}")
    return record


def _collect_contention_telemetry() -> dict:
    telemetry = {"ts": time.time()}
    try:
        import subprocess
        ps_out = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=5).stdout
        telemetry["ollama_ps_lines"] = [l for l in ps_out.strip().splitlines() if l.strip()]
    except Exception as e:
        telemetry["ollama_ps_error"] = str(e)
    try:
        import subprocess
        sw = subprocess.run(["sysctl", "vm.swapusage"], capture_output=True, text=True, timeout=5).stdout
        telemetry["swapusage"] = sw.strip()
    except Exception as e:
        telemetry["swapusage_error"] = str(e)
    try:
        from app.core.crash_awareness import is_mlx_avoidance_active
        telemetry["mlx_avoidance_active"] = is_mlx_avoidance_active()
    except Exception as e:
        telemetry["mlx_avoidance_check_error"] = str(e)
    return telemetry


def _load_and_verify_suite(stage_num: int) -> dict:
    path = STAGE_SUITE_PATHS[stage_num]
    with open(path, "rb") as f:
        raw = f.read()
    live_hash = hashlib.sha256(raw).hexdigest()
    expected = STAGE_SUITE_HASHES[stage_num]
    assert live_hash == expected, (
        f"STAGE {stage_num} SUITE HASH MISMATCH -- refusing to run. "
        f"expected={expected} live={live_hash}"
    )
    return json.loads(raw)


def _setup_common():
    apply_finding_a_fix()
    pinned_model = pin_model_for_tier4()
    print(f"[setup] pinned model for Tier-4 study = {pinned_model} (reused from Tier-3 pilot)")
    t3.install_model_pin(pinned_model)
    t3.install_council_identity_anonymization()
    t3.install_truncation_capture()
    real_ollama_query = _install_mechanism_capture()
    proxy = base_pilot.install_isolation()
    print("[setup] isolation + model pin + identity anonymization + truncation capture + "
          "mechanism capture installed")
    return pinned_model, proxy, real_ollama_query


def run_stage(stage_num: int):
    suite = _load_and_verify_suite(stage_num)
    tasks = {t["task_id"]: t for t in suite["tasks"]}
    print(f"[setup] STAGE {stage_num} suite hash VERIFIED = {STAGE_SUITE_HASHES[stage_num]}")
    print(f"[setup] stage {stage_num} task_ids = {sorted(tasks.keys())} (n={len(tasks)})")

    seed = 20260904100 + stage_num  # distinct, recorded seed per stage
    pinned_model, proxy, real_ollama_query = _setup_common()

    os.makedirs(TIER4_DIR, exist_ok=True)
    results_path = STAGE_RESULTS_PATHS[stage_num]
    pre_run_telemetry = _collect_contention_telemetry()
    print(f"[telemetry] pre-run (stage {stage_num}): {pre_run_telemetry}")

    for task_id in sorted(tasks.keys()):
        task = tasks[task_id]
        order = t3.randomized_arm_order(task_id, seed)
        print(f"\n=== TIER-4 STAGE {stage_num} TASK {task_id} -- arm order: {order} ===")
        pre_task_telemetry = _collect_contention_telemetry()
        for arm in order:
            _run_single_candidate(
                task, arm, pinned_model, proxy, seed, order, results_path,
                extra_fields={"stage": stage_num, "pre_task_telemetry": pre_task_telemetry},
            )

    post_run_telemetry = _collect_contention_telemetry()
    print(f"[telemetry] post-run (stage {stage_num}): {post_run_telemetry}")
    print(f"\n[TIER-4 STAGE {stage_num} COMPLETE] "
          f"total production_side_effect_detected events: {len(base_pilot._side_effects_detected)}")


def run_dev_sanity():
    """Phase 5b: sanity-check this NEW instrumented harness (Finding A fix
    + mechanism capture) against the existing, non-held-out development
    tasks (task_11/task_12) before spending real compute on either frozen
    Tier-4 suite. Reuses t3.assert_development_task_only for the same
    hard, programmatic held-out protection the Tier-3 apparatus enforces."""
    with open(base_pilot.TASK_SUITE_PATH, "rb") as f:
        raw_suite = f.read()
    suite_hash = hashlib.sha256(raw_suite).hexdigest()
    assert suite_hash == t3.EXPECTED_TASK_SUITE_HASH, "FROZEN DEV TASK SUITE HASH MISMATCH -- STOP."
    tasks = {t["task_id"]: t for t in json.loads(raw_suite)["tasks"]}

    seed = 20260904
    pinned_model, proxy, real_ollama_query = _setup_common()
    os.makedirs(TIER4_DIR, exist_ok=True)

    for task_id in sorted(t3.DEVELOPMENT_TASK_IDS):
        t3.assert_development_task_only(task_id)
        task = tasks[task_id]
        order = t3.randomized_arm_order(task_id, seed)
        print(f"\n=== DEV SANITY (Tier-4 harness) TASK {task_id} -- arm order: {order} ===")
        for arm in order:
            _run_single_candidate(task, arm, pinned_model, proxy, seed, order,
                                   DEV_SANITY_RESULTS_PATH)

    print(f"\n[DEV SANITY COMPLETE] total production_side_effect_detected events: "
          f"{len(base_pilot._side_effects_detected)}")


if __name__ == "__main__":
    if "--dev-check" in sys.argv:
        run_dev_sanity()
    elif "--stage1" in sys.argv:
        run_stage(1)
    elif "--stage2" in sys.argv:
        run_stage(2)
    else:
        print("Usage: python3 scripts/run_tier4_confirmatory.py [--dev-check|--stage1|--stage2]")
        sys.exit(1)
