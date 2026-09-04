#!/usr/bin/env python3
"""
TIER 3 APPARATUS -- repair implementation + DEVELOPMENT-SET SANITY CHECK ONLY.

This script does NOT run the held-out Tier-3 experiment. It exists to
implement and verify the six required repair groups (B1/B2/B3/M2/M3/M4)
identified in audits/tier3_design_preflight.md, then exercise all four
arms exactly once each against the two designated DEVELOPMENT tasks
(task_11, task_12 -- the same two named in
audits/tier3_architecture_vs_model_design.md's own held-out methodology
section) to prove the apparatus itself works. No held-out task is
referenced anywhere in this file's own data.

Reuses, does not duplicate, the proven isolation/verification machinery
from scripts/run_capability_pilot.py (install_isolation, objective_verify,
clean_code, _classify_exception) -- the original 15-task/45-candidate
pilot's own script and data are untouched by this file.
"""
import hashlib
import json
import os
import random
import sys
import time

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import run_capability_pilot as base_pilot  # reuse, do not duplicate

TASK_SUITE_PATH = base_pilot.TASK_SUITE_PATH
EXPECTED_TASK_SUITE_HASH = "6440ed174482a2d5bb43bdd03bfc33c73c66b492cb74f465e2674e8a8eb8937d"

TIER3_DIR = "audits/tier3_apparatus"
PINNED_MODEL_PATH = f"{TIER3_DIR}/pinned_model.json"
RESULTS_PATH = f"{TIER3_DIR}/dev_sanity_results.jsonl"
# B2 / real production parity: matches DEFAULT_COUNCIL_SIZE (3) so BASE_N's
# total call budget (N generations + 1 synthesis) matches ARCH_COUNCIL's.
N_BASEN = 3
# B1: explicit, identical, primary budget definition for EVERY call in
# EVERY arm. Never silently omitted, never left to an Ollama/harness default.
MAX_TOKENS = 2048

# Held-out protection (see assert_development_task_only): this manifest does
# not exist yet -- this study has not reached the held-out phase. The path
# is declared now so a future held-out manifest is automatically checked
# against, rather than requiring a second pass of this file later.
HELD_OUT_MANIFEST_PATH = f"{TIER3_DIR}/held_out_task_suite.json"
# Per audits/tier3_architecture_vs_model_design.md's own methodology: task_11
# and task_12 are the two designated DEVELOPMENT tasks, reused from the
# original frozen 15-task suite, used only to confirm non-degenerate
# apparatus behavior -- never to tune any arm's prompt/parameters.
DEVELOPMENT_TASK_IDS = {"task_11", "task_12"}

# --- Held-out phase (added: current_capability_synthesis's own "NEXT
# MISSION" protocol, §11). 8 brand-new tasks, authored specifically for
# this run -- never used in audits/capability_pilot/task_suite.json or any
# prior document (verified by direct grep before freezing; see
# audits/tier3_apparatus/held_out_task_suite.hash.txt). Frozen the moment
# they were authored, before any generation call touched them.
HELD_OUT_SUITE_EXPECTED_HASH = "2d78cbdb3657755f65779d010590ae348ded22d6d32d300bddacfd0aaa0e912a"
HELDOUT_RESULTS_PATH = f"{TIER3_DIR}/heldout_results.jsonl"


def load_and_verify_held_out_suite() -> dict:
    """Loads the frozen held-out manifest and hard-asserts its hash matches
    the constant recorded at freeze time -- protects against the file being
    silently edited/regenerated between authoring and execution (the
    symmetric integrity check to assert_development_task_only(), which
    protects the DEV path; this protects the HELD-OUT path's own data)."""
    with open(HELD_OUT_MANIFEST_PATH, "rb") as f:
        raw = f.read()
    live_hash = hashlib.sha256(raw).hexdigest()
    assert live_hash == HELD_OUT_SUITE_EXPECTED_HASH, (
        f"HELD-OUT SUITE HASH MISMATCH -- refusing to run. "
        f"expected={HELD_OUT_SUITE_EXPECTED_HASH} live={live_hash}"
    )
    return json.loads(raw)

# --- Objective 1 repair: per-call-scoped truncation evidence -------------
# The original implementation (see audits/tier3_remaining_blockers_
# investigation.md, part D) used a single, shared, unscoped, time-windowed
# list (`_truncation_events`, a plain list appended to by every arm) with
# classify_result() reading recent[-1] -- "whatever event is most recent."
# That variable has been removed entirely, not just deprecated in place --
# nothing in this file reads or writes it any more; every truncation
# observation now lives ONLY in _truncation_events_by_call, below, keyed by
# an explicit, unique per-call identifier.
# The original implementation used a single, shared, time-windowed list with
# NO per-call identity -- classify_result() took "whatever event is most
# recent," which is unsafe for any arm that never contributes its own event
# (confirmed: ARCH_PIPELINE). This replaces that with a strict, call-ID-keyed
# mapping: every truncation observation is stored ONLY under the exact call
# ID that produced it, and classify_result() may ONLY read the entry for the
# call ID it is explicitly given -- never "the latest," never "whatever is in
# the window." Cross-call/cross-arm contamination is now structurally
# impossible, not merely unlikely.
_call_id_counter = [0]
_current_call_id = [None]  # set immediately before a generation call that
                             # routes through stream_query_ollama; cleared
                             # right after. None means "no capture is active
                             # right now" -- a stray captured event with no
                             # current call ID is dropped, never misfiled.
_truncation_events_by_call = {}  # call_id -> list of {"done_reason":..., "ts":...}
                                  # (a list, not a single dict, because
                                  # ARCH_COUNCIL's real deliberate_and_learn()
                                  # makes several underlying calls -- 3
                                  # councillors + 1 synthesis -- under ONE
                                  # call_id per candidate; only the LAST
                                  # entry under that id is ever consulted for
                                  # classification, since only the synthesis
                                  # call's own output is what gets scored --
                                  # see classify_result()'s own docstring.)

PIPELINE_NO_GROUND_TRUTH = "PIPELINE_NO_GROUND_TRUTH"  # explicit sentinel
# call_id for ARCH_PIPELINE's real calls -- never registered in
# _truncation_events_by_call, by construction, since ARCH_PIPELINE's own
# call path never routes through the capture point. Passing this sentinel
# (instead of a real int ID, or instead of silently reusing None) makes the
# "this arm structurally has no ground truth" case an explicit, named,
# auditable state rather than an implicit consequence of an empty lookup.


def _new_call_id() -> int:
    _call_id_counter[0] += 1
    return _call_id_counter[0]


def assert_development_task_only(task_id: str) -> None:
    """Hard, programmatic held-out protection (per the mission's explicit
    requirement). Refuses to proceed if (a) a held-out manifest exists and
    task_id appears in it, or (b) task_id is not in the designated
    development allowlist at all -- whichever manifest state is real."""
    if os.path.exists(HELD_OUT_MANIFEST_PATH):
        with open(HELD_OUT_MANIFEST_PATH, "rb") as f:
            raw = f.read()
        manifest = json.loads(raw)
        held_out_ids = {t["task_id"] for t in manifest.get("tasks", [])}
        assert task_id not in held_out_ids, (
            f"HELD-OUT PROTECTION TRIPPED: '{task_id}' is a real held-out task "
            f"-- refusing to run it in the development sanity path."
        )
    assert task_id in DEVELOPMENT_TASK_IDS, (
        f"'{task_id}' is not in the designated development-task allowlist "
        f"{DEVELOPMENT_TASK_IDS} -- refusing to run it. This sanity script "
        f"may ONLY exercise designated development tasks."
    )


# ---------------------------------------------------------------------------
# M2 -- experiment-level model pinning, persisted across invocations, with
# generate_code_from_plan()'s OWN internal choose_model() call intercepted
# ---------------------------------------------------------------------------

def pin_model_for_study() -> str:
    """Pin once for the ENTIRE study (not per batch, per M2's own finding),
    persisted to disk so every future invocation of this script reuses the
    identical model rather than re-selecting."""
    if os.path.exists(PINNED_MODEL_PATH):
        with open(PINNED_MODEL_PATH) as f:
            return json.load(f)["pinned_model"]
    from app.core.self_edit_manager import choose_model
    model, _ = choose_model(
        "Implement a small, correct, well-structured Python function.", task_type="self_edit_coding"
    )
    os.makedirs(TIER3_DIR, exist_ok=True)
    with open(PINNED_MODEL_PATH, "w") as f:
        json.dump({"pinned_model": model, "pinned_at": time.time()}, f)
    return model


def install_model_pin(pinned_model: str) -> None:
    """M2: prevent generate_code_from_plan()'s own internal choose_model()
    call from silently selecting a DIFFERENT model than BASE_1/BASE_N. Same
    in-process, nothing-on-disk-changes monkeypatch discipline already
    established and proven for get_river_brain/log_interaction/etc.
    self_edit_manager.py imports choose_model BY NAME (`from
    app.core.echo_model_orchestrator import (..., choose_model)`), so its
    own free variable resolves against self_edit_manager's own module
    globals -- patch THAT name, not echo_model_orchestrator's, exactly the
    same import-semantics reasoning already verified for get_river_brain."""
    import app.core.self_edit_manager as sem
    sem.choose_model = lambda *a, **k: (pinned_model, pinned_model)


# ---------------------------------------------------------------------------
# B3 -- neutral, harness-only synthesis for BASE_N + model-identity
# anonymization for ARCH_COUNCIL's real synthesis input (in-process only)
# ---------------------------------------------------------------------------

BASEN_SYNTHESIS_SYSTEM_TEMPLATE = """\
You are solving a coding task. You previously produced the following
independent attempts at solving it.
Task type: {task_type}

Your own independent attempts:
{opinions}

Your role:
- Weigh each attempt according to its coherence and correctness.
- Identify the sharpest point of disagreement or uncertainty between your
  own attempts -- the friction that should not be smoothed over -- and let
  it sharpen your final answer rather than disappear into it.
- Produce ONE final, correct response that integrates the best of what you
  produced, staying true to your own reasoning.
- Do NOT list or number your own attempts in the final answer.
- Do NOT resolve genuine uncertainty artificially. If something remains
  contested between your attempts, hold it that way rather than picking
  arbitrarily.
- Speak plainly, as the one producing the final answer -- not as a
  summarizer describing what you did.

Respond now to the original task."""
# Deliberately mirrors river_deliberation.SYNTHESIS_SYSTEM_TEMPLATE's real
# structure (weigh/identify tension/produce one answer/don't resolve
# artificially/don't list sources) as closely as is honest for a
# same-model case -- "independent attempts," never "council" or
# "perspectives," since there is no real council here. The real template's
# closing paragraph about system-context-as-authoritative-source is
# deliberately DROPPED, not mirrored: that instruction concerns ground-truth
# ABOUT ECHO'S OWN ARCHITECTURE injected via a separate mechanism this
# harness's coding-task prompts never carry -- mirroring it here would add
# content with no real referent, a difference disclosed here, not hidden.


def _format_attempts_anonymized(attempts: list) -> str:
    """BASE_N's own attempt-formatting, structurally identical to
    river_deliberation._format_opinions()'s real rendering shape
    ([N. Label]\\ntext, blank-line separated) but labeled [Attempt N]
    instead of a model name, since there is only one real model here --
    trivially "anonymous" by construction, not merely by choice."""
    lines = []
    for i, text in enumerate(attempts, start=1):
        preview = (text or "[attempt unavailable]").strip()
        lines.append(f"[Attempt {i}]\n{preview}")
    return "\n\n".join(lines)


def install_council_identity_anonymization():
    """B3: council's REAL synthesis (SYNTHESIS_SYSTEM_TEMPLATE via
    _format_opinions()) exposes real per-model short names ([1. Qwen2],
    [2. Deepseek-r1], ...) to the synthesis call -- confirmed by direct
    source read in the preflight. This is real, additional information
    BASE_N's synthesis structurally cannot have (there is only one model),
    so it is neutralized for ARCH_COUNCIL too: an in-process-only patch of
    river_deliberation._format_opinions to use [Attempt N] labels instead
    of real model names, applied for the duration of THIS SCRIPT's own
    process only. river_deliberation.py itself is never edited on disk;
    the live production server's own real council calls (a separate OS
    process) are completely unaffected."""
    import app.core.river_deliberation as rd
    _real_format_opinions = rd._format_opinions

    def _anonymized_format_opinions(opinions: dict, per_opinion_tokens=None):
        # Same real truncation-per-opinion logic as production, only the
        # LABEL text changes (real model short-name -> anonymous index).
        lines = []
        for i, (model, response) in enumerate(opinions.items(), start=1):
            if not response or "[ERROR]" in response:
                preview = "[attempt unavailable]"
            elif per_opinion_tokens is not None:
                from app.core.river_deliberation import _truncate_to_tokens
                preview = _truncate_to_tokens(response, per_opinion_tokens).strip()
            else:
                preview = response[:800].strip()
            lines.append(f"[Attempt {i}]\n{preview}")
        return "\n\n".join(lines)

    rd._format_opinions = _anonymized_format_opinions
    return _real_format_opinions  # returned so a caller could restore it if ever needed


# ---------------------------------------------------------------------------
# M3 -- real, ground-truth-based truncation classification
# ---------------------------------------------------------------------------

def install_truncation_capture():
    """Captures the REAL done_reason Ollama itself reports, for every call
    that routes through app.ollama_handler.stream_query_ollama (covers
    BASE_1, BASE_N's own calls, and ARCH_COUNCIL's per-councillor +
    synthesis calls via river_deliberation._ollama_query -- all funnel
    through this one shared function). In-process monkeypatch only.

    KNOWN, DISCLOSED GAP (found during implementation, reported per the
    mission's own "stop and report" instruction, not silently designed
    around): ARCH_PIPELINE's real call path (generate_code_from_plan() ->
    echo_query() -> echo_model_orchestrator.ollama_query()) is a SEPARATE,
    independent implementation that hits /api/generate directly and
    bypasses app.ollama_handler.py (and therefore this capture point)
    entirely -- confirmed by direct source read, not assumed. Ground-truth
    done_reason is therefore NOT available for ARCH_PIPELINE without
    modifying production code, which this mission does not permit. The
    fence-based heuristic below is the only available truncation signal
    for that one arm -- applied uniformly to ALL FOUR arms as a secondary/
    backstop check regardless, so at minimum every arm gets the same
    secondary check, with three of four additionally getting the strictly
    better, ground-truth primary check."""
    import app.ollama_handler as oh
    _real = oh.stream_query_ollama

    def _wrapped(*args, **kwargs):
        result_meta = kwargs.get("result_meta")
        gen = _real(*args, **kwargs)
        tokens = list(gen)
        if result_meta is not None:
            active_id = _current_call_id[0]
            # Objective-1 repair: file this event ONLY under the call ID that
            # is explicitly active right now -- never a shared, unscoped list.
            # If no call ID is active (a call routed through here without
            # ever being wrapped by a run_condition_*() call-ID scope), the
            # event is dropped, not misfiled under a guessed key -- silence
            # here is honest; a wrong attribution is not.
            if active_id is not None:
                _truncation_events_by_call.setdefault(active_id, []).append({
                    "model": kwargs.get("model"), "done_reason": result_meta.get("done_reason"),
                    "ts": time.time(),
                })
        return iter(tokens)

    oh.stream_query_ollama = _wrapped


def classify_result(raw_response: str, candidate_code: str, verify: dict, call_id=None) -> tuple:
    """Mutually exclusive, deterministic EXTERNAL classification: PASS /
    GENERATION_TRUNCATED / TASK_LOGIC_FAILURE. (INFRASTRUCTURE_FAILURE is
    assigned separately, at the exception-handling call site, exactly as
    in the existing, proven run_capability_pilot.py logic -- reused, not
    reimplemented.)

    Returns (classification, evidence_type). evidence_type is an INTERNAL,
    audit-trail-only signal, never collapsed away, distinguishing HOW a
    truncation determination (or non-determination) was reached:
      - "GROUND_TRUTH_TRUNCATED"      -- Ollama's own done_reason=="length"
                                         for THIS exact call.
      - "TEXT_BACKSTOP_TRUNCATED"     -- no ground truth for this call (or
                                         ground truth said "stop"), but the
                                         fence-parity heuristic caught it.
      - "NO_GROUND_TRUTH_AVAILABLE"   -- this call structurally cannot
                                         produce a ground-truth signal
                                         (call_id is None or the explicit
                                         PIPELINE_NO_GROUND_TRUTH sentinel),
                                         or a ground-truth call_id was given
                                         but no event was ever recorded
                                         under it.
      - None                          -- PASS; no truncation question was
                                         ever asked.

    call_id identity discipline (Objective 1 repair): this function NEVER
    reads "the most recent event," "the last event added," or anything
    keyed by time. It reads ONLY the entry (or entries) filed under the
    EXACT call_id given -- an explicit, unique identifier assigned by the
    caller before its own generation call ran (see run_condition_*()).
    A call_id of None or PIPELINE_NO_GROUND_TRUTH is treated identically:
    both mean "do not even attempt the ground-truth lookup" -- there is
    nothing under either key by construction (PIPELINE_NO_GROUND_TRUTH is
    never registered as a real key in _truncation_events_by_call, and a
    lookup keyed on Python's None would only ever find events some OTHER
    bug filed there, which install_truncation_capture() above structurally
    prevents by dropping any event when no call is actively scoped)."""
    if verify["passed"]:
        return "PASS", None

    # Primary, ground-truth signal -- available whenever this specific call
    # was itself instrumented. As of the ARCH_PIPELINE isolation fix (see
    # audits/tier3_arch_pipeline_isolation.md), this now includes ALL FOUR
    # arms -- BASE_1 / BASE_N / ARCH_PIPELINE_ISOLATED all call
    # river_deliberation._ollama_query() directly (real, per-call ground
    # truth), and ARCH_COUNCIL's synthesis leg is the last event filed under
    # its own shared call_id. PIPELINE_NO_GROUND_TRUTH remains defined and
    # correctly handled below (never registered as a real dict key) as a
    # structural safeguard for any FUTURE arm that genuinely cannot produce
    # ground truth -- it is simply not assigned to any arm that exists today.
    if call_id is not None and call_id != PIPELINE_NO_GROUND_TRUTH:
        events_for_this_call = _truncation_events_by_call.get(call_id)
        if events_for_this_call:
            # Multiple entries can exist under one call_id only for
            # ARCH_COUNCIL, whose single external call wraps 4 real
            # internal calls (3 councillors + 1 synthesis) that this
            # harness cannot individually tag -- deliberate_and_learn()'s
            # own internal ordering (confirmed by direct source read: the
            # councillor loop runs to completion, THEN the synthesis call
            # is made) means the LAST entry filed under this call_id is
            # always the synthesis leg -- i.e. the one whose output is
            # actually being scored. This is an ordering guarantee SCOPED
            # STRICTLY WITHIN one external call's own internal sub-calls,
            # never across different calls/arms/tasks -- categorically
            # different from the original bug, which read "most recent"
            # across the entire shared, unscoped event stream.
            if events_for_this_call[-1].get("done_reason") == "length":
                return "GENERATION_TRUNCATED", "GROUND_TRUTH_TRUNCATED"

    # Secondary, text-based backstop (applied uniformly to ALL arms,
    # including ARCH_PIPELINE, which has no ground-truth signal available):
    # an opening fence with no matching closing fence is real, direct
    # evidence the response itself was cut off mid-generation, independent
    # of whether extraction succeeded.
    if "```" in (raw_response or ""):
        opens = (raw_response or "").count("```")
        if opens % 2 == 1:  # an odd count means the last fence was never closed
            return "GENERATION_TRUNCATED", "TEXT_BACKSTOP_TRUNCATED"

    if call_id is None or call_id == PIPELINE_NO_GROUND_TRUTH or not _truncation_events_by_call.get(call_id):
        return "TASK_LOGIC_FAILURE", "NO_GROUND_TRUTH_AVAILABLE"
    return "TASK_LOGIC_FAILURE", None


# ---------------------------------------------------------------------------
# B2 -- BASE_N_selfconsistency, budget-matched to ARCH_COUNCIL
# ---------------------------------------------------------------------------

def run_condition_basen(task: dict, pinned_model: str) -> dict:
    """N independent attempts from the SAME pinned model (real jittered
    temperature via the real, reused river_deliberation._jittered_temperature
    -- the identical function council's own per-councillor jitter uses, for
    genuine parity, not a reimplemented approximation), then ONE synthesis
    call using the SAME pinned model and the neutral BASEN_SYNTHESIS_
    SYSTEM_TEMPLATE. Total real calls = N_BASEN + 1, matching
    ARCH_COUNCIL's real DEFAULT_COUNCIL_SIZE(3) + 1 synthesis exactly.
    Every call passes max_tokens=MAX_TOKENS explicitly (B1). No access to
    self-edit-specific framing, production memory, RiverBrain learning, or
    any architectural artifact unavailable to BASE_1 -- confirmed by using
    ONLY river_deliberation._ollama_query(), the same clean, contamination-
    free Design B path BASE_1 itself uses."""
    from app.core.river_deliberation import _ollama_query, _jittered_temperature

    attempts = []
    call_log = []
    for i in range(N_BASEN):
        temp = _jittered_temperature(None, i, N_BASEN)
        t0 = time.time()
        attempt_call_id = _new_call_id()
        _current_call_id[0] = attempt_call_id
        try:
            resp = _ollama_query(
                pinned_model, task["prompt"], temperature=temp, max_tokens=MAX_TOKENS, task_type="coding",
            )
        finally:
            _current_call_id[0] = None
        call_log.append({
            "call": f"attempt_{i+1}", "model": pinned_model, "temperature": temp,
            "requested_max_tokens": MAX_TOKENS, "generation_time": round(time.time() - t0, 2),
            "call_id": attempt_call_id,
        })
        attempts.append(resp)

    formatted = _format_attempts_anonymized(attempts)
    synth_prompt = task["prompt"]
    synth_system = BASEN_SYNTHESIS_SYSTEM_TEMPLATE.format(task_type="coding", opinions=formatted)
    t0 = time.time()
    synthesis_call_id = _new_call_id()
    # The N attempt calls above are each tagged with their OWN distinct
    # call_id -- real, individually-attributable truncation evidence for
    # each attempt is preserved in call_log for audit purposes -- but
    # classify_result() (see the return below) is only ever given THIS
    # synthesis call's own call_id, since candidate_code/raw_response below
    # are the synthesis output, not any individual attempt's output. An
    # attempt truncating does not mean the FINAL scored text truncated.
    _current_call_id[0] = synthesis_call_id
    try:
        final = _ollama_query(
            pinned_model, synth_prompt, system=synth_system, temperature=0.3,
            max_tokens=MAX_TOKENS, task_type="coding",
        )
    finally:
        _current_call_id[0] = None
    call_log.append({
        "call": "synthesis", "model": pinned_model, "temperature": 0.3,
        "requested_max_tokens": MAX_TOKENS, "generation_time": round(time.time() - t0, 2),
        "call_id": synthesis_call_id,
    })

    code = base_pilot.clean_code(final)
    return {
        "raw_response": final, "candidate_code": code, "model_used": pinned_model,
        "n_attempts": N_BASEN, "total_calls": N_BASEN + 1, "call_log": call_log,
        "requested_max_tokens_per_call": MAX_TOKENS,
        "call_id": synthesis_call_id,
    }


# ---------------------------------------------------------------------------
# Arms A / B / C, budget-repaired
# ---------------------------------------------------------------------------

def run_condition_base1(task: dict, pinned_model: str) -> dict:
    from app.core.river_deliberation import _ollama_query
    t0 = time.time()
    call_id = _new_call_id()
    _current_call_id[0] = call_id
    try:
        raw = _ollama_query(pinned_model, task["prompt"], temperature=0.0, max_tokens=MAX_TOKENS, task_type="coding")
    finally:
        _current_call_id[0] = None
    gen_time = time.time() - t0
    code = base_pilot.clean_code(raw)
    return {
        "raw_response": raw, "candidate_code": code, "model_used": pinned_model,
        "total_calls": 1, "generation_time": round(gen_time, 2),
        "requested_max_tokens_per_call": MAX_TOKENS,
        "temperature": 0.0,
        "call_id": call_id,
    }


def run_condition_arch_pipeline(task: dict, pinned_model: str) -> dict:
    """ARCH_PIPELINE_ISOLATED -- an experimental isolation of the self-edit
    GENERATION mechanism, NOT a reproduction of Echo's literal current
    production self-edit call path.

    HISTORY (do not lose this -- see audits/tier3_arch_pipeline_isolation.md
    for the full account): the original implementation of this function
    called self_edit_manager.generate_code_from_plan(task['prompt']), which
    calls echo_model_orchestrator.echo_query(), whose default (use_all=False)
    branch unconditionally calls river_deliberation.deliberate_and_learn() --
    a REAL 3-councillor + synthesis council -- for any task_type not in
    DIRECT_ECHO_TASKS ("coding" is not in that set). This was confirmed live,
    by watching a real run's log, not by re-reading source: task_12's
    "ARCH_PIPELINE" candidate under the OLD code showed a real
    "[DELIBERATION] Council for task=coding: ['qwen2.5-coder:7b',
    'mlx:qwen3', 'echo:latest']" / "Sending 3 opinions to echo:latest for
    synthesis" sequence, while the harness recorded model_used='qwen2.5-
    coder:7b' (a label from a SEPARATE, non-generating choose_model() call
    inside generate_code_from_plan(), used only for RiverBrain attribution)
    and total_calls=1 (a hardcoded literal, never a measured count). Real
    generation times (32.8s/37.4s across the two development tasks) were
    consistent with a genuine multi-call council, not a single call
    (BASE_1's real single calls: 2.7s/6.6s). This was true of EVERY
    historical ARCH_PIPELINE result in this project, including the original
    3-condition pilot -- none of it was ever a genuine single-call
    observation. All historical ARCH_PIPELINE data is preserved, unedited,
    and explicitly reclassified INVALID_FOR_ISOLATED_SINGLE_CALL_COMPARISON
    (see the isolation report) -- not deleted, not silently reinterpreted.

    THIS implementation fixes the confound by calling the exact same
    low-level mechanism BASE_1 uses (river_deliberation._ollama_query(),
    Design B -- no echo_query(), no deliberate_and_learn(), no council, no
    live model selection, no production RiverBrain/interaction_log/
    reflection writes reachable from this call at all) with the SAME pinned
    model, SAME temperature, SAME max_tokens, and SAME single-call budget as
    BASE_1 -- the only intended difference is the self-edit-specific
    framing/context prepended to the prompt (CODE_OUTPUT_RULES + the live
    contents of self_edit_generated.py + the task, mirroring
    generate_code_from_plan()'s own real prompt-construction shape exactly,
    so the ONE thing under test is that framing, not anything else changing
    at the same time). No production file was modified to make this fix --
    self_edit_manager.py's own CODE_OUTPUT_RULES/SELF_EDIT_FILE constants are
    only READ (imported), never written to or redefined, and
    generate_code_from_plan()/echo_query()/deliberate_and_learn() themselves
    are completely untouched and still behave exactly as before for real
    production self-edit cycles."""
    from app.core.river_deliberation import _ollama_query
    from app.core.self_edit_manager import CODE_OUTPUT_RULES, SELF_EDIT_FILE, scan_for_unsafe_operations

    # Mirrors generate_code_from_plan()'s own real prompt-construction shape
    # exactly (self_edit_manager.py:1763-1776) -- the ONE intentional,
    # disclosed difference from BASE_1's bare task prompt. See
    # audits/tier3_arch_pipeline_isolation.md Step 1 for the full BASE_1 vs
    # ARCH_PIPELINE attribute table, including the explicit finding that this
    # file's live content was checked and contains no task-relevant
    # information (it is unrelated, disclosed self-edit noise -- see that
    # report for the exact content read and reasoning) and the explicit,
    # disclosed limitation that this content is NOT frozen: it is the live,
    # continuously-self-edited production file, so its exact text can differ
    # between separate runs of this harness at different times.
    current_contents = ""
    try:
        with open(SELF_EDIT_FILE, "r") as _f:
            current_contents = _f.read()
    except Exception:
        pass
    code_prompt = (
        f"{CODE_OUTPUT_RULES}\n\n"
        f"Current contents of {SELF_EDIT_FILE}:\n```\n{current_contents}\n```\n\n"
        f"Plan to implement:\n{task['prompt']}"
    )

    t0 = time.time()
    call_id = _new_call_id()
    _current_call_id[0] = call_id
    try:
        raw = _ollama_query(
            pinned_model, code_prompt, temperature=0.0, max_tokens=MAX_TOKENS, task_type="coding",
        )
    finally:
        _current_call_id[0] = None
    gen_time = time.time() - t0
    code = base_pilot.clean_code(raw)

    # F1 (self-edit's real safety scanner) retained as an observational,
    # non-gating check for continuity with the prior implementation and
    # with real self-edit's own pipeline -- does not affect scoring (see
    # tier3_architecture_vs_model_design.md's own Level-C falsifiable
    # prediction: F1 is a safety scanner, not a correctness verifier, and
    # should contribute ~zero to objective_verify()'s pass/fail result).
    f1_passed, f1_detail = True, None
    try:
        scan_for_unsafe_operations(code)
    except Exception as e:
        f1_passed, f1_detail = False, str(e)[:500]

    return {
        "raw_response": raw, "candidate_code": code, "model_used": pinned_model,
        "total_calls": 1, "generation_time": round(gen_time, 2),
        "f1_passed": f1_passed, "f1_detail": f1_detail,
        "requested_max_tokens_per_call": MAX_TOKENS,
        "temperature": 0.0,
        "call_id": call_id,
        "code_prompt_char_len": len(code_prompt),
        "self_edit_file_char_len": len(current_contents),
    }


def run_condition_arch_council(task: dict, proxy) -> dict:
    from app.core.river_deliberation import deliberate_and_learn
    from app.core.echo_model_orchestrator import MODEL_POOL
    import app.core.river_deliberation as rd

    # Logging-completeness fix (tier3_final_execution_gate mission, Step 8):
    # the harness's own record previously stored only "council_synthesis" as
    # model_used, with no way to reconstruct WHICH real models were actually
    # consulted for a given candidate from the structured JSONL alone (only
    # from the run's own live stdout, which is not part of the durable
    # per-candidate record). A local, function-scoped recording wrapper
    # around the same real river_deliberation._ollama_query() every
    # councillor and the synthesis call go through -- installed and
    # restored within this function only, identical in shape to
    # install_council_identity_anonymization()'s own patch/restore pattern
    # on this same module -- closes this gap without touching any
    # production file.
    _real_ollama_query = rd._ollama_query
    _calls_made = []

    def _recording_ollama_query(model_name, prompt, *a, **k):
        _calls_made.append(model_name)
        return _real_ollama_query(model_name, prompt, *a, **k)

    rd._ollama_query = _recording_ollama_query

    t0 = time.time()
    call_id = _new_call_id()
    # deliberate_and_learn() is one opaque production call that makes 4 real
    # underlying stream_query_ollama() calls internally (3 councillors + 1
    # synthesis) -- this harness has no hook granular enough to assign each
    # of those 4 a genuinely distinct call_id without instrumenting inside
    # river_deliberation.py itself (a production file this repair does not
    # touch). All 4 real events will therefore be filed under this ONE
    # call_id -- see classify_result()'s own docstring for why reading the
    # LAST entry filed under this specific, non-shared call_id (not "the
    # last entry globally") correctly and safely identifies the synthesis
    # leg's own done_reason, the only one relevant to the code actually
    # being scored below.
    _current_call_id[0] = call_id
    try:
        response = deliberate_and_learn(
            prompt=task["prompt"], task_type="coding", river_brain=proxy, model_pool=MODEL_POOL,
            max_tokens=MAX_TOKENS,
        )
    finally:
        _current_call_id[0] = None
        rd._ollama_query = _real_ollama_query
    gen_time = time.time() - t0
    code = base_pilot.clean_code(response)
    # A REAL, PREVIOUSLY-UNDISCLOSED finding, caught during the
    # tier3_final_execution_gate mission's own live verification of this
    # exact fix: deliberate_and_learn() makes a genuine 5TH real
    # _ollama_query() call before the 3 councillors + synthesis -- a
    # minimal-input (".") warm-up ping to the synthesis model
    # (river_deliberation._warm_up_echo(), called unconditionally at
    # "1b. Warm up Echo before council queries begin", real production
    # code, not touched by this harness), whose OWN response content is
    # always discarded (never fed into synthesis, never scored). Confirmed
    # live: a real test call recorded real_calls_made =
    # ['echo:latest', 'qwen2.5-coder:7b', 'mlx:qwen3', 'echo:latest',
    # 'echo:latest'] -- 5 entries, not 4. total_calls is kept at the
    # GENERATIVE call count (4 -- the 3 councillors + synthesis, the calls
    # whose content actually reaches the final answer, directly comparable
    # to BASE_N's own 4) for continuity with BASE_N's own accounting; the
    # true, complete real-call count (including the warm-up) is recorded
    # separately and explicitly, not hidden. Since the warm-up's own output
    # is unconstrained in length (no max_tokens passed to it in production
    # code), its real wall-clock/compute cost is real and non-zero (already
    # included in generation_time, since it happens inside this same timed
    # deliberate_and_learn() call) even though it contributes zero content
    # to the scored candidate -- a genuine, disclosed, NOT-eliminated
    # asymmetry against BASE_N/BASE_1/ARCH_PIPELINE_ISOLATED, none of which
    # have an equivalent warm-up call. See
    # audits/tier3_final_execution_gate.md for the full disclosure.
    _warmup_model = _calls_made[0] if len(_calls_made) >= 2 else None
    _councillor_models = _calls_made[1:-1] if len(_calls_made) >= 2 else _calls_made[:-1] if _calls_made else []
    return {
        "raw_response": response, "candidate_code": code, "model_used": "council_synthesis",
        "total_calls": 4, "generation_time": round(gen_time, 2),
        "requested_max_tokens_per_call": MAX_TOKENS,
        "call_id": call_id,
        "real_calls_made": _calls_made,
        "total_real_ollama_calls_including_warmup": len(_calls_made),
        "warmup_model": _warmup_model,
        "councillor_models": _councillor_models,
        "synthesis_model": _calls_made[-1] if _calls_made else None,
    }


# ---------------------------------------------------------------------------
# M4 -- randomized arm order per task, seeded and recorded
# ---------------------------------------------------------------------------

def randomized_arm_order(task_id: str, seed: int) -> list:
    rng = random.Random(f"{seed}:{task_id}")
    order = ["BASE_1", "BASE_N", "ARCH_PIPELINE_ISOLATED", "ARCH_COUNCIL"]
    rng.shuffle(order)
    return order


# ---------------------------------------------------------------------------
# MAIN -- development-set sanity check ONLY
# ---------------------------------------------------------------------------

def _run_single_candidate(task: dict, arm: str, pinned_model: str, proxy, seed: int, order: list,
                           results_path: str, extra_fields: dict = None) -> dict:
    """Shared per-(task, arm) execution + scoring + logging, used identically
    by both the development-sanity path and the held-out path -- a single
    code path for the two phases the protocol requires to behave identically,
    rather than two independently-maintained copies that could silently
    drift apart between phases (the exact class of risk
    tier3_design_preflight.md's own §9/§17 flags for model-pin drift)."""
    record = {
        "task_id": task["task_id"], "arm": arm, "seed": seed, "arm_order": order,
        "timestamp": time.time(),
    }
    if extra_fields:
        record.update(extra_fields)
    try:
        if arm == "BASE_1":
            gen = run_condition_base1(task, pinned_model)
        elif arm == "BASE_N":
            gen = run_condition_basen(task, pinned_model)
        elif arm == "ARCH_PIPELINE_ISOLATED":
            gen = run_condition_arch_pipeline(task, pinned_model)
        else:
            gen = run_condition_arch_council(task, proxy)
        record.update(gen)
        verify = base_pilot.objective_verify(gen["candidate_code"], task["test_code"])
        record.update(verify)
        classification, evidence_type = classify_result(
            gen.get("raw_response", gen.get("candidate_code", "")), gen["candidate_code"], verify,
            call_id=gen.get("call_id"),
        )
        record["classification"] = classification
        # Internal audit trail (Objective 1, requirement e) -- preserved
        # separately, never collapsed into the external 4-class
        # "classification" field above.
        record["truncation_evidence_type"] = evidence_type
    except Exception as e:
        failure_class = base_pilot._classify_exception(e)
        record["error"] = f"{type(e).__name__}: {e}"
        record["passed"] = False
        record["classification"] = failure_class

    record["side_effects_so_far"] = len(base_pilot._side_effects_detected)
    with open(results_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    print(f"  {arm}: classification={record.get('classification')} "
          f"passed={record.get('passed')} model={record.get('model_used')} "
          f"calls={record.get('total_calls')} side_effects_total={len(base_pilot._side_effects_detected)}")
    return record


def _collect_contention_telemetry() -> dict:
    """Best-effort, read-only snapshot of live contention signals -- recorded
    per-batch so a future report can honestly state the operating conditions
    each candidate was actually generated under, rather than assuming a
    'low-contention window' held for the whole run. Never raises; a failed
    telemetry read degrades to partial/empty data rather than blocking
    generation."""
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
    return telemetry


def main():
    with open(TASK_SUITE_PATH, "rb") as f:
        raw_suite = f.read()
    suite_hash = hashlib.sha256(raw_suite).hexdigest()
    assert suite_hash == EXPECTED_TASK_SUITE_HASH, "FROZEN TASK SUITE HASH MISMATCH -- STOP."
    tasks = {t["task_id"]: t for t in json.loads(raw_suite)["tasks"]}

    seed = 20260904
    print(f"[setup] task suite hash VERIFIED = {suite_hash}")
    print(f"[setup] experiment seed = {seed}")

    pinned_model = pin_model_for_study()
    print(f"[setup] pinned model for entire study = {pinned_model}")
    install_model_pin(pinned_model)
    real_format_opinions = install_council_identity_anonymization()
    install_truncation_capture()
    proxy = base_pilot.install_isolation()
    print("[setup] isolation + model pin + identity anonymization + truncation capture installed")

    os.makedirs(TIER3_DIR, exist_ok=True)
    for task_id in sorted(DEVELOPMENT_TASK_IDS):
        assert_development_task_only(task_id)
        task = tasks[task_id]
        order = randomized_arm_order(task_id, seed)
        print(f"\n=== DEVELOPMENT TASK {task_id} -- arm order: {order} ===")
        for arm in order:
            _run_single_candidate(task, arm, pinned_model, proxy, seed, order, RESULTS_PATH)

    print(f"\n[DEVELOPMENT SANITY CHECK COMPLETE] "
          f"total production_side_effect_detected events: {len(base_pilot._side_effects_detected)}")
    print("No held-out Tier-3 capability results were collected by this run.")


def main_heldout():
    """The real, genuinely held-out Tier-3 comparison. Only run after (a)
    this same process's own fresh dev-sanity pass (main(), above) has
    already confirmed a sane BASE_N synthesis under the repaired code, and
    (b) a deliberate check of live contention has been made immediately
    before this call (see the __main__ dispatch below) -- this function
    itself does not enforce either precondition, per this project's
    established pattern of the harness trusting its own caller's explicit,
    logged sequencing rather than re-deriving it."""
    suite = load_and_verify_held_out_suite()
    tasks = {t["task_id"]: t for t in suite["tasks"]}
    print(f"[setup] HELD-OUT suite hash VERIFIED = {HELD_OUT_SUITE_EXPECTED_HASH}")
    print(f"[setup] held-out task_ids = {sorted(tasks.keys())}")

    seed = 20260904  # same seed as the development phase, for consistency;
    # randomized_arm_order() is independently reseeded per task_id anyway,
    # so reusing this constant does not create any cross-task correlation.

    pinned_model = pin_model_for_study()  # reuses the SAME persisted pin as
    # the development phase -- if this differs from what main() just used,
    # that is itself a reportable finding (model drift between phases),
    # not something to silently paper over.
    print(f"[setup] pinned model for held-out phase = {pinned_model}")
    install_model_pin(pinned_model)
    install_council_identity_anonymization()
    install_truncation_capture()
    proxy = base_pilot.install_isolation()
    print("[setup] isolation + model pin + identity anonymization + truncation capture installed (held-out phase)")

    os.makedirs(TIER3_DIR, exist_ok=True)
    pre_run_telemetry = _collect_contention_telemetry()
    print(f"[telemetry] pre-run: {pre_run_telemetry}")

    for task_id in sorted(tasks.keys()):
        task = tasks[task_id]
        order = randomized_arm_order(task_id, seed)
        print(f"\n=== HELD-OUT TASK {task_id} -- arm order: {order} ===")
        pre_task_telemetry = _collect_contention_telemetry()
        for arm in order:
            _run_single_candidate(
                task, arm, pinned_model, proxy, seed, order, HELDOUT_RESULTS_PATH,
                extra_fields={"held_out": True, "pre_task_telemetry": pre_task_telemetry},
            )

    post_run_telemetry = _collect_contention_telemetry()
    print(f"[telemetry] post-run: {post_run_telemetry}")
    print(f"\n[HELD-OUT RUN COMPLETE] "
          f"total production_side_effect_detected events: {len(base_pilot._side_effects_detected)}")


if __name__ == "__main__":
    if "--heldout" in sys.argv:
        main_heldout()
    else:
        main()
