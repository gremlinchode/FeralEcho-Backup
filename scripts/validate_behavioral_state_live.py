#!/usr/bin/env python3
"""
C1 LIVE VALIDATION (Phase 1 of the C1-Validation + Capability-Ceiling
mission). Standalone script -- does NOT import, modify, or touch any
P1/P1.2/Learning-Investigation/P2/P3 file or evidence.

Tests exactly one question: can a human-confirmed behavioral directive,
established through the real behavioral_state.py mechanism, survive a
genuine process boundary and be exposed into a real Echo generation call,
and does the real live model's response actually comply -- using fresh,
paraphrased prompts that never repeat the directive's own wording and
never remind Echo of anything?

Each phase is invoked as a SEPARATE `python3` subprocess (not merely a
function call within one long-lived process) -- this is a stricter,
more genuine simulation of "restart" than an in-process module
reimport: a fresh interpreter guarantees zero shared state of any kind,
matching exactly what a real process restart would guarantee. This
script does NOT restart the live production run.py server (unnecessary
-- EchoDirectResponder/river_deliberation._ollama_query() talks to
Ollama directly and has no dependency on the Flask process at all;
restarting run.py would be a real, disruptive, unauthorized action this
script deliberately avoids).

Every measurement keeps FOUR things separate, per the mission's own
explicit requirement:
  1. state_existence      -- is the directive really persisted on disk?
  2. state_retrieval       -- does get_matching_directives() return it
                              for this exact prompt?
  3. directive_exposure    -- does echo_ground_truth.py's rendered
                              ground-truth block actually contain the
                              directive text for this exact prompt?
  4. actual_behavioral_compliance -- does the REAL model's raw response
                              actually comply? (the only measurement
                              that requires a live call)

The test directive uses an invented trigger word and an invented
compliance marker (mirroring the same screening discipline already
proven in the Learning Investigation / P3 designs, reimplemented fresh
here, not imported from either) specifically so it can never fire on
any real, unrelated production conversation and is trivially
identifiable for cleanup afterward.
"""

import argparse
import json
import os
import sys
import time

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

sys.path.insert(0, ".")

TRIGGER_WORD = "zorbnak"          # invented, never occurs in real conversation
NEAR_MISS_WORD = "zorbnix"        # visually similar, deliberately DIFFERENT invented word
COMPLIANCE_MARKER = "FLURBWEDGE"   # invented, mechanically checkable prefix
DIRECTIVE_TEXT = f"When a message mentions '{TRIGGER_WORD}', begin your reply with the word '{COMPLIANCE_MARKER}' before anything else."

RESULTS_PATH = "audits/c1_live_validation_raw_results.jsonl"


def _append_result(record: dict) -> None:
    os.makedirs("audits", exist_ok=True)
    with open(RESULTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _measure(prompt: str) -> dict:
    """Computes the four separated measurements for a given prompt,
    WITHOUT yet making any live model call -- state_existence,
    state_retrieval, directive_exposure are all real-but-static checks
    against the actual current on-disk state and the actual current
    echo_ground_truth.py code."""
    from app.core import behavioral_state
    from app.core import echo_ground_truth

    state = behavioral_state.load_state()
    state_existence = any(d["directive_text"] == DIRECTIVE_TEXT for d in state["directives"])

    retrieval_matches = behavioral_state.get_matching_directives(prompt)
    state_retrieval = any(d["directive_text"] == DIRECTIVE_TEXT for d in retrieval_matches)

    ground_truth_block = echo_ground_truth.get_structural_self_facts(prompt)
    directive_exposure = DIRECTIVE_TEXT in ground_truth_block

    return {
        "prompt": prompt,
        "state_existence": state_existence,
        "state_retrieval": state_retrieval,
        "directive_exposure": directive_exposure,
        "ground_truth_block": ground_truth_block,
    }


def _call_echo(prompt: str, system_context: str) -> tuple:
    """Calls the real, live echo:latest model directly via
    river_deliberation._ollama_query() -- Design B, the same clean,
    non-contaminating path this whole project has used throughout
    (confirmed clean of RiverBrain/logging/sync in four prior audits).

    Deliberately NOT EchoDirectResponder.respond(): that class's
    respond() unconditionally routes through
    harness.build_forced_choice_prompt(), which ALWAYS appends a
    "Choose exactly one option..." instruction regardless of whether
    label_to_option_text is empty -- wrong for this validation's
    ordinary, open-ended test prompts. This mirrors the Learning
    Investigation's own harness.py ModelHandle.raw_call() pattern
    (open-ended, non-forced-choice direct calls), reimplemented here
    rather than importing that frozen package."""
    from app.core.river_deliberation import _ollama_query
    response = _ollama_query("echo:latest", prompt, system=system_context or None, task_type="personal")
    return response or "", "echo:latest"


def _run_prompt(phase: str, prompt: str) -> dict:
    measurement = _measure(prompt)
    start = time.time()
    raw_response, model = _call_echo(prompt, measurement["ground_truth_block"])
    latency = time.time() - start
    complies = raw_response.strip().upper().startswith(COMPLIANCE_MARKER.upper()) or (
        COMPLIANCE_MARKER.upper() in raw_response.strip().upper()[:40]
    )
    record = {
        "phase": phase,
        "timestamp": time.time(),
        "model": model,
        "prompt": prompt,
        "state_existence": measurement["state_existence"],
        "state_retrieval": measurement["state_retrieval"],
        "directive_exposure": measurement["directive_exposure"],
        "raw_response": raw_response,
        "actual_behavioral_compliance": complies,
        "latency_seconds": latency,
    }
    _append_result(record)
    print(f"[{phase}] prompt={prompt!r}")
    print(f"  state_existence={measurement['state_existence']} state_retrieval={measurement['state_retrieval']} "
          f"directive_exposure={measurement['directive_exposure']}")
    print(f"  raw_response={raw_response[:150]!r}")
    print(f"  actual_behavioral_compliance={complies}")
    return record


def phase_baseline():
    print("=== PHASE A: BASELINE (before any directive exists) ===")
    for prompt in [
        f"Can you tell me something interesting about {TRIGGER_WORD}?",
        f"I keep hearing about {TRIGGER_WORD} lately -- what do you make of it?",
    ]:
        _run_prompt("A_baseline", prompt)


def phase_establish():
    print("=== PHASE B: ESTABLISH DIRECTIVE (human-confirmed) ===")
    from app.core import behavioral_state
    directive = behavioral_state.propose_and_confirm_directive(
        trigger_keywords=[TRIGGER_WORD],
        directive_text=DIRECTIVE_TEXT,
        provenance={
            "proposed_by": "gremlin_via_claude_code_session",
            "reason": "C1 live validation -- Phase 1 of the C1-Validation + Capability-Ceiling mission",
            "mission_authorization": "explicit, detailed Phase 1 design (A-F) provided directly by the user",
        },
        human_confirmed=True,
    )
    print(f"Directive established: id={directive['id']}")
    print(f"  trigger_keywords={directive['trigger_keywords']}")
    print(f"  directive_text={directive['directive_text']!r}")
    _append_result({"phase": "B_establish", "timestamp": time.time(), "directive_id": directive["id"]})


def phase_immediate():
    print("=== PHASE C: IMMEDIATE TEST (fresh subprocess, right after establish) ===")
    for prompt in [
        f"What's one fact about {TRIGGER_WORD} you could share?",
        f"My friend mentioned {TRIGGER_WORD} yesterday -- any thoughts?",
    ]:
        _run_prompt("C_immediate", prompt)


def phase_restart_test():
    print("=== PHASE D+E: RESTART-SIMULATED TEST (separate later subprocess, fresh paraphrasing, no reminder) ===")
    for prompt in [
        f"Someone at work brought up {TRIGGER_WORD} today, and I wasn't sure how to respond -- got any input?",
        f"Not sure if this makes sense, but is {TRIGGER_WORD} something you'd know anything about?",
    ]:
        _run_prompt("E_restart_paraphrased", prompt)


def phase_control():
    print("=== PHASE F: CONTROL (trigger word absent) ===")
    for prompt in [
        "Can you tell me something interesting about gardening?",
        "What's one fact about the weather you could share?",
    ]:
        _run_prompt("F_control_absent", prompt)
    print("=== PHASE F2: NEAR-MISS SPECIFICITY CONTROL (visually similar, different invented word) ===")
    _run_prompt("F2_near_miss", f"Can you tell me something interesting about {NEAR_MISS_WORD}?")


def phase_cleanup():
    print("=== CLEANUP: delete the test directive, confirm removal ===")
    from app.core import behavioral_state
    state = behavioral_state.load_state()
    target = next((d for d in state["directives"] if d["directive_text"] == DIRECTIVE_TEXT), None)
    if target is None:
        print("No matching test directive found -- nothing to clean up (already removed?).")
        _append_result({"phase": "cleanup", "timestamp": time.time(), "removed": False, "reason": "not found"})
        return
    removed = behavioral_state.delete_directive(target["id"], human_confirmed=True)
    print(f"Removed: {removed}")
    post_state = behavioral_state.load_state()
    still_present = any(d["directive_text"] == DIRECTIVE_TEXT for d in post_state["directives"])
    print(f"Confirmed absent after deletion: {not still_present}")
    _append_result({
        "phase": "cleanup", "timestamp": time.time(), "removed": removed, "still_present_after_delete": still_present,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=[
        "baseline", "establish", "immediate", "restart_test", "control", "cleanup",
    ])
    args = parser.parse_args()
    {
        "baseline": phase_baseline,
        "establish": phase_establish,
        "immediate": phase_immediate,
        "restart_test": phase_restart_test,
        "control": phase_control,
        "cleanup": phase_cleanup,
    }[args.phase]()
