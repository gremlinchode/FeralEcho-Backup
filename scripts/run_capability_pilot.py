#!/usr/bin/env python3
"""
HIGHEST-INFORMATION-GAIN PILOT: 15-task RAW vs PIPELINE vs COUNCIL
capability benchmark. Standalone script. Does NOT modify production code,
does NOT repair any known bug (council cursor, arbitration priority),
does NOT deploy anything, and is built specifically to avoid contaminating
production RiverBrain/interaction_log/reflection_shard/council_deliberations
state -- see the isolation layer below.

Every production-writing function this pilot's own call paths would
otherwise reach is monkeypatched to a safe no-op FOR THE DURATION OF THIS
PROCESS ONLY (nothing on disk is edited; this is the same "poison the
function to test/redirect it" pattern this project's own test suites
already use, e.g. scripts/verify_behavioral_state.py). A production_side
_effect_detected flag records whether any patched function was ever
actually called, so isolation is verified empirically, not just assumed.
"""
import argparse
import hashlib
import json
import os
import random
import shutil
import socket
import sys
import tempfile
import time

# Infrastructure-failure signatures -- connection/timeout errors that mean
# "Ollama/the queue/the process misbehaved," not "the model produced wrong
# code." Checked by substring against the stringified exception/response,
# since the underlying HTTP client raises several different exception
# types depending on which stage fails (connect vs. read vs. timeout).
_INFRA_FAILURE_SIGNATURES = (
    "connectionerror", "connection refused", "connection reset",
    "read timed out", "readtimeout", "timeout", "timed out",
    "max retries exceeded", "remotedisconnected", "connectionreseterror",
    "httpconnectionpool", "failed to establish a new connection",
)


def _classify_exception(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(sig in text for sig in _INFRA_FAILURE_SIGNATURES):
        return "INFRASTRUCTURE_FAILURE"
    return "GENERATION_EXCEPTION"

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")

TASK_SUITE_PATH = "audits/capability_pilot/task_suite.json"
RESULTS_PATH = "audits/capability_pilot/raw_results.jsonl"
MAPPING_PATH = "audits/capability_pilot/blind_mapping.json"  # private until unblinding
SANDBOX_TIMEOUT = 30

_side_effects_detected = []


def _append(record: dict) -> None:
    os.makedirs("audits/capability_pilot", exist_ok=True)
    with open(RESULTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


# ---------------------------------------------------------------------------
# ISOLATION LAYER -- read-through / write-blocked proxy + monkeypatches
# ---------------------------------------------------------------------------

class _ReadOnlyRiverBrainProxy:
    """Wraps the REAL, already-loaded production RiverBrain instance.
    Every read (score_model, is_well_observed, influence_weight,
    observation_counts, model_task_stats, ...) delegates to the real
    object so council selection / model ranking is genuinely faithful
    to current production state. Every write (learn, save,
    learn_from_sandbox_outcome, learn_from_council_rating) is a no-op
    that records the attempt instead of touching memory/river_brain.pkl."""

    def __init__(self, real_instance):
        object.__setattr__(self, "_real", real_instance)

    def learn(self, *a, **k):
        _side_effects_detected.append({"fn": "RiverBrain.learn", "args_preview": str(a)[:80]})

    def save(self, *a, **k):
        _side_effects_detected.append({"fn": "RiverBrain.save"})

    def learn_from_sandbox_outcome(self, *a, **k):
        _side_effects_detected.append({"fn": "RiverBrain.learn_from_sandbox_outcome"})

    def learn_from_council_rating(self, *a, **k):
        _side_effects_detected.append({"fn": "RiverBrain.learn_from_council_rating"})

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)


def _noop_log_interaction(*a, **k):
    _side_effects_detected.append({"fn": "log_interaction", "args_preview": str(a)[:80]})


def _noop_save_reflection(*a, **k):
    _side_effects_detected.append({"fn": "save_reflection", "args_preview": str(a)[:80]})


def _noop_log_council_deliberation(*a, **k):
    _side_effects_detected.append({"fn": "_log_council_deliberation", "args_preview": str(a)[:80]})


_isolation_metadata = {}  # set by install_isolation() -- real_path/scratch_path,
                          # kept separate from _side_effects_detected so a real
                          # redirect never gets miscounted as a detected breach


def install_isolation():
    """Patch every known production-write call site this pilot's own call
    paths could reach. Nothing on disk is edited -- these are in-process
    module-attribute patches, scoped to this script's own process only.

    Tier-8 forensic finding (2026-09-05, audits/tier8_experimental_isolation
    _forensic.md): the proxy below blocks explicit .learn()/.save() calls
    reached THROUGH get_river_brain(), but it does NOT stop RiverBrain's own
    background _writer_thread -- that thread is started unconditionally
    inside RiverBrain.__init__(), which runs (via RiverBrain.load()) the
    moment get_river_brain() is first called, i.e. BEFORE this function's
    proxy patch can exist to block anything. That thread independently
    calls _do_save() every ~60s for the life of the process, writing
    directly to the real, shared memory/river_brain.pkl -- confirmed to
    have fired ~229 times, unblocked and invisible to
    _side_effects_detected, during the real Tier-4 stage1/stage2 runs
    alone. Patching AFTER construction (as this function used to) cannot
    close this, because the act of obtaining a real object to wrap is
    itself what starts the thread.

    Fix (Architecture A from the Tier-8 report): redirect the module-level
    RIVER_BRAIN_PATH constant to an isolated scratch copy of the real file
    BEFORE the first get_river_brain() call, not after. RIVER_BRAIN_PATH is
    referenced as a bare global inside RiverBrain.load()/_do_save() (never
    captured into a local/default-argument anywhere -- confirmed by direct
    grep before this fix was written), so every subsequent read AND every
    subsequent write -- including the background thread's, which this
    proxy can never otherwise reach -- resolves against the redirected
    path for the rest of this process's life. The real production file is
    never opened for writing by this process at any point. Read-fidelity
    is unaffected: the scratch copy is byte-identical to the real file at
    the moment of copy, so the proxy's read-through methods (score_model,
    is_well_observed, model_task_stats, ...) still reflect real historical
    production state exactly as before this fix.
    """
    from app.core import echo_model_orchestrator as emo
    from app.core import river_deliberation as rd

    real_path = emo.RIVER_BRAIN_PATH
    scratch_dir = tempfile.mkdtemp(prefix="river_brain_isolated_")
    scratch_path = os.path.join(scratch_dir, os.path.basename(real_path))
    if os.path.exists(real_path):
        shutil.copy2(real_path, scratch_path)
    emo.RIVER_BRAIN_PATH = scratch_path
    _isolation_metadata["real_river_brain_path"] = real_path
    _isolation_metadata["scratch_river_brain_path"] = scratch_path
    print(f"[ISOLATION] RiverBrain state redirected: real={real_path} -> "
          f"scratch={scratch_path} (production file will not be written by "
          f"this process, including by its background writer thread)")

    real_rb = emo.get_river_brain()  # now loads from AND persists to scratch_path only
    proxy = _ReadOnlyRiverBrainProxy(real_rb)

    emo.get_river_brain = lambda: proxy
    emo.log_interaction = _noop_log_interaction
    emo.save_reflection = _noop_save_reflection
    rd._log_council_deliberation = _noop_log_council_deliberation

    return proxy


# ---------------------------------------------------------------------------
# OBJECTIVE VERIFICATION -- reuses code_verification.py's real function
# ---------------------------------------------------------------------------

def objective_verify(candidate_code: str, test_code: str) -> dict:
    from app.core.code_verification import verify_in_sandbox
    combined = candidate_code + "\n\n" + test_code
    t0 = time.time()
    ran_ok, output = verify_in_sandbox(combined, timeout=SANDBOX_TIMEOUT)
    duration = time.time() - t0
    passed = ran_ok and ("ALL_TESTS_PASSED" in output)
    return {
        "ran_ok": ran_ok, "output_tail": (output or "")[-800:],
        "passed": passed, "verification_time": round(duration, 2),
    }


def clean_code(raw_text: str) -> str:
    """Cleanup path. Starts with self-edit's own real production helpers
    (_strip_markdown_fences/_looks_like_python/_extract_code_block), then
    adds ONE disclosed, harness-only fallback discovered necessary during
    this pilot's own real execution (see run notes): those three helpers
    assume code appears at the END of a response with no trailing prose --
    true for self-edit's own normal (non-reasoning-model) generation
    style, but FALSE for deepseek-r1:7b's real output shape (a long
    reasoning trace, an inline unfenced code draft mid-reasoning, THEN a
    final fenced ```python ... ``` block, followed by MORE prose
    explaining it). _extract_code_block()'s first-match-wins scan finds
    the inline mid-reasoning draft first and returns everything after it
    (trailing prose included), which never parses. This fallback -- a
    well-known, standard convention (take the LAST fenced code block, the
    model's final/settled answer) -- is applied identically across ALL
    THREE conditions for fairness, is a fix to THIS HARNESS's own
    pre-processing step only, and does not touch or replace F1/F2/the
    verification pipeline/self_edit_manager.py itself in any way."""
    import re
    from app.core.self_edit_manager import _strip_markdown_fences, _looks_like_python, _extract_code_block

    raw_text = raw_text or ""
    code = _strip_markdown_fences(raw_text)
    if _looks_like_python(code):
        return code

    code = _extract_code_block(raw_text)
    if _looks_like_python(code):
        return code

    # Harness-only fallback: last fenced code block wins.
    fences = re.findall(r"```(?:python)?\s*\n(.*?)```", raw_text, re.DOTALL)
    if fences:
        last = fences[-1].strip()
        if _looks_like_python(last):
            return last
        return last  # return even if it doesn't pass the check -- record the real attempt, don't silently substitute

    return code  # nothing better found; return whatever _extract_code_block gave, honestly


# ---------------------------------------------------------------------------
# CONDITIONS
# ---------------------------------------------------------------------------

def run_condition_a_raw(task: dict, model_name: str) -> dict:
    """RAW: direct Design B call. No pipeline, no council, no retries,
    no production side effects by construction (does not call echo_query
    or generate_code_from_plan at all)."""
    from app.core.river_deliberation import _ollama_query
    t0 = time.time()
    raw = _ollama_query(model_name, task["prompt"], temperature=0.0, task_type="coding")
    gen_time = time.time() - t0
    code = clean_code(raw)
    return {"raw_response": raw, "candidate_code": code, "generation_time": round(gen_time, 2),
            "model_used": model_name}


def run_condition_b_pipeline(task: dict) -> dict:
    """PIPELINE: the real self-edit generation function
    (generate_code_from_plan), fed this task's OWN text as the 'plan'
    argument (unmodified real function, real CODE_OUTPUT_RULES framing,
    real current-self_edit_generated.py-file context, real choose_model()
    selection) -- then the real F1 static scanner
    (scan_for_unsafe_operations). Isolation (install_isolation()) must
    already be active before this is called. NOTE (disclosed limitation):
    this exercises generate_code_from_plan() + F1 directly, not the higher
    -level execute_self_edit() wrapper, so self-edit's own intrinsic
    single-retry-on-sandbox-failure mechanism is NOT exercised here --
    stated plainly, not silently omitted."""
    from app.core.self_edit_manager import generate_code_from_plan, scan_for_unsafe_operations
    t0 = time.time()
    code, model_name = generate_code_from_plan(task["prompt"], temperature=0.0)
    gen_time = time.time() - t0

    f1_passed = True
    f1_detail = None
    try:
        scan_for_unsafe_operations(code)
    except Exception as e:
        f1_passed = False
        f1_detail = str(e)[:500]

    return {"candidate_code": code, "generation_time": round(gen_time, 2),
            "model_used": model_name, "f1_passed": f1_passed, "f1_detail": f1_detail}


def run_condition_c_council(task: dict, proxy) -> dict:
    """COUNCIL: the real deliberate_and_learn() -- real council selection
    (_select_council, live-read-through to the real RiverBrain via the
    proxy), real per-councillor generation, real synthesis. river_brain=
    proxy ensures no production RiverBrain write; _log_council_deliberation
    is monkeypatched module-wide (see install_isolation()). Isolation
    must already be active before this is called."""
    from app.core.river_deliberation import deliberate_and_learn
    from app.core.echo_model_orchestrator import MODEL_POOL
    t0 = time.time()
    response = deliberate_and_learn(
        prompt=task["prompt"], task_type="coding", river_brain=proxy, model_pool=MODEL_POOL,
    )
    gen_time = time.time() - t0
    code = clean_code(response)
    return {"raw_response": response, "candidate_code": code, "generation_time": round(gen_time, 2),
            "model_used": "council_synthesis"}


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def _load_completed_pairs_and_max_id():
    """Resumability: read whatever raw_results.jsonl already has (from a
    prior, possibly-uncontrolled run) and return the set of (task_id,
    condition) pairs that already have a REAL completed record (has a
    'passed' key -- i.e. reached objective scoring, not just an exception),
    plus the highest candidate_NNN number already used, so a controlled
    continuation never re-runs or renumbers a real prior candidate."""
    completed = set()
    max_id = 0
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if "candidate_id" in rec and "passed" in rec:
                    completed.add((rec["task_id"], rec["condition"]))
                    try:
                        n = int(rec["candidate_id"].split("_")[-1])
                        max_id = max(max_id, n)
                    except Exception:
                        pass
    return completed, max_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-candidates", type=int, default=None,
                         help="Stop after generating this many NEW candidates this invocation "
                              "(controlled-batch execution, per the mission's explicit request).")
    args = parser.parse_args()

    with open(TASK_SUITE_PATH, "rb") as f:
        raw_suite = f.read()
    suite_hash = hashlib.sha256(raw_suite).hexdigest()
    assert suite_hash == "6440ed174482a2d5bb43bdd03bfc33c73c66b492cb74f465e2674e8a8eb8937d", (
        "FROZEN TASK SUITE HASH MISMATCH -- STOP. Do not silently continue; the frozen suite must be "
        "restored or the protocol explicitly re-baselined before generation."
    )
    tasks = json.loads(raw_suite)["tasks"]
    print(f"[setup] task suite hash VERIFIED = {suite_hash}, {len(tasks)} tasks")
    _append({"phase": "setup", "task_suite_hash": suite_hash, "n_tasks": len(tasks), "resumed": True})

    completed_pairs, max_id = _load_completed_pairs_and_max_id()
    print(f"[setup] resuming -- {len(completed_pairs)} (task,condition) pairs already completed, "
          f"highest existing candidate_id = {max_id:03d}")

    proxy = install_isolation()
    print("[setup] isolation installed (get_river_brain/log_interaction/save_reflection/"
          "_log_council_deliberation monkeypatched in-process)")

    from app.core.self_edit_manager import choose_model
    fixed_model, _ = choose_model(
        "Implement a small, correct, well-structured Python function.", task_type="self_edit_coding"
    )
    print(f"[setup] fixed model for conditions A/B this batch (via choose_model("
          f"task_type='self_edit_coding')) = {fixed_model}")
    _append({"phase": "setup", "fixed_model_a_b": fixed_model})

    # Remaining (task, condition) pairs, in frozen-suite declaration order --
    # deterministic and resumable, a disclosed, minor deviation from the
    # first run's pure random.shuffle() for the tail of the study, justified
    # by needing safe resumability under real, repeated infrastructure
    # interruptions (see report).
    pending = []
    for task in tasks:
        for cond in ["A", "B", "C"]:
            if (task["task_id"], cond) not in completed_pairs:
                pending.append((task, cond))

    print(f"[setup] {len(pending)} candidates remaining out of 45")
    if args.max_candidates:
        print(f"[setup] CONTROLLED BATCH: capping this invocation at {args.max_candidates} new candidates")
        pending = pending[: args.max_candidates]

    candidate_counter = max_id

    for task, cond in pending:
        candidate_counter += 1
        candidate_id = f"candidate_{candidate_counter:03d}"
        print(f"\n=== {candidate_id} :: task={task['task_id']} (tier {task['tier']}) cond={cond} ===")

        record = {
            "candidate_id": candidate_id, "task_id": task["task_id"], "tier": task["tier"],
            "condition": cond, "timestamp": time.time(),
        }
        t_start = time.time()
        try:
            if cond == "A":
                gen = run_condition_a_raw(task, fixed_model)
            elif cond == "B":
                gen = run_condition_b_pipeline(task)
            else:
                gen = run_condition_c_council(task, proxy)
            record.update(gen)
            verify = objective_verify(gen["candidate_code"], task["test_code"])
            record.update(verify)
            record["failure_class"] = None if verify["passed"] else "TASK_LOGIC_FAILURE"
        except Exception as e:
            failure_class = _classify_exception(e)
            record["error"] = f"{type(e).__name__}: {e}"
            record["passed"] = False
            record["failure_class"] = failure_class
            print(f"  !! {failure_class} !! {record['error'][:200]}")

        record["total_wall_clock_time"] = round(time.time() - t_start, 2)
        record["side_effects_so_far"] = len(_side_effects_detected)
        _append(record)
        print(f"  passed={record.get('passed')} failure_class={record.get('failure_class')} "
              f"gen_time={record.get('generation_time')}s verify_time={record.get('verification_time')}s "
              f"wall_clock={record['total_wall_clock_time']}s side_effects_total={len(_side_effects_detected)}")

    remaining_after = 45 - (len(completed_pairs) + len(pending))
    print(f"\n[batch done] {len(pending)} new candidates this invocation. "
          f"{remaining_after} still pending overall.")

    if remaining_after <= 0:
        # Full study complete -- write the blind mapping now, not before.
        completed_pairs2, _ = _load_completed_pairs_and_max_id()
        blind_mapping = {}
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if "candidate_id" in rec and "passed" in rec:
                    blind_mapping[rec["candidate_id"]] = {
                        "task_id": rec["task_id"], "condition": rec["condition"],
                    }
        with open(MAPPING_PATH, "w", encoding="utf-8") as f:
            json.dump(blind_mapping, f, indent=2)
        _append({"phase": "final", "total_side_effects_detected": len(_side_effects_detected),
                  "side_effects_detail": _side_effects_detected})
        print(f"\n[STUDY COMPLETE] total production_side_effect_detected events: "
              f"{len(_side_effects_detected)}")
        if _side_effects_detected:
            print("  !! ISOLATION BREACH DETECTED !!", _side_effects_detected[:5])


if __name__ == "__main__":
    main()
