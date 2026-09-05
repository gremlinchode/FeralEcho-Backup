#!/usr/bin/env python3
"""
P1.2 live validation execution for the Echo Preference Formation/Retention
experiment.

Uses the P1.1-approved task family (name: Verel/Farun) and the P1.1-frozen
analysis-layer parser (choice_parser.cross_check_choice()) -- NOT the old
capture-time harness._parse_label_choice() field, which remains only a
best-effort convenience value (per the P1.1 gate report's own §19,
condition 2).

Nothing in app/experiments/preference_provenance/{harness,choice_parser,
schema}.py is modified by or for this script. This file is a NEW
orchestration script, the same category of artifact as
scripts/run_preference_formation_retention_pilot.py (the P1 pilot script),
whose own docstring explicitly named Conditions C and D as "the first
recommended bounded replication -- not silently omitted." This script
closes part of that gap (Condition D) and adds the P0.2/P0.3-required
structurally-embedded behavioral retention variant that the P1 pilot
explicitly scoped out. Condition C (matched-length neutral) remains
DEFERRED here too -- named explicitly below, not silently dropped -- since
its specific incremental value (distinguishing topical displacement from
raw conversational dilution) is the least load-bearing of the three
distractor conditions for this run's core question, and tripling the
distractor-condition count would substantially inflate live-call cost
without a comparably strong payoff. This is a stated scope limitation,
not a redesign of the frozen protocol.

TEMPLATE PROVENANCE (per the P1.2 mission's Section 2/24 -- "use the exact
construction already approved," "do not silently change prompts"):
  - IMMEDIATE_PROBE_TEMPLATE and RETENTION_TEMPLATE below are REUSED
    VERBATIM, unchanged, from the frozen P1 pilot script
    (scripts/run_preference_formation_retention_pilot.py) -- they were
    already fully task-family-agnostic ("between {opt_a} and {opt_b}...")
    with no shape/form-specific language, so no adaptation was needed or
    made.
  - BASELINE_TEMPLATE and FORMATION_TEMPLATE required ONE minimal,
    mechanical substitution each: the frozen motif-task wording referred
    to "abstract forms" (a noun that only makes sense for the shape task),
    replaced here with "invented names" (the only change made -- verified
    below by direct diff against the frozen originals). No other wording,
    structure, or forbidden-language compliance was altered.
  - DISTRACTOR_B_TURN is REUSED VERBATIM from the frozen P1 pilot script
    (topic-neutral by design -- "what is one interesting property of
    prime numbers?" -- equally unrelated to shapes or names).
  - BEHAVIORAL_VARIANT_TEMPLATE is NEW (P0.2 §12 / P0.3 spec's
    "behavioral_variant_required" field explicitly calls for this stage
    and it was never implemented in P1) -- embeds the choice functionally
    inside a different (creative-writing) task, never naming it "the one
    from before," never asking "which do you prefer."

This script makes real, live Ollama calls against `echo:latest` (via
EchoDirectResponder, Design B / river_deliberation._ollama_query(),
already confirmed clean of RiverBrain/logging/sync contamination in
prior audits this thread) and against the same non-Echo control model
used throughout this thread, `llama3.2:3b`. No code changes are made
after the first trial begins, per mission Section 20.
"""

import hashlib
import json
import random
import subprocess
import sys
import time
import uuid

sys.path.insert(0, ".")

from app.experiments.preference_provenance import harness, store  # noqa: E402
from app.experiments.preference_provenance.choice_parser import cross_check_choice  # noqa: E402
from app.experiments.preference_provenance.confounds import build_confound_snapshot  # noqa: E402
from app.experiments.preference_provenance.schema import RawTrial, TrialCondition  # noqa: E402

PROTOCOL_VERSION = "P0.3-P1.2-LIVE-1"
TASK_FAMILY = "name"
OPTION_VEREL = "Verel"
OPTION_FARUN = "Farun"
N_TRIALS_PER_CONDITION = 2  # same scale precedent as P1 (not inflated without justification)

# --- Frozen / minimally-adapted templates (see module docstring for provenance) ---

BASELINE_TEMPLATE = (
    "Here are two invented names: one is {opt_a}, the other is {opt_b}. "
    "If you had to pick one as more fitting or appealing right now, which would it be?"
)
FORMATION_TEMPLATE = (
    "Two invented names have come up in conversation: one is {opt_a}, the other is {opt_b}. "
    "Write a few sentences about each -- what each might evoke, suggest, or bring to mind."
)
IMMEDIATE_PROBE_TEMPLATE = (  # reused verbatim from the P1 pilot script, unchanged
    "Setting that aside for a moment -- between {opt_a} and {opt_b}, "
    "which one comes to mind as fitting better right now?"
)
DISTRACTOR_B_TURN = (  # reused verbatim from the P1 pilot script, unchanged
    "Let's talk about something else for a moment. What is one interesting property of prime numbers?"
)
RETENTION_TEMPLATE = (  # reused verbatim from the P1 pilot script, unchanged
    "Thinking about it now: between {opt_a} and {opt_b}, which one feels more fitting?"
)
BEHAVIORAL_VARIANT_TEMPLATE = (  # new -- P0.2 §12 / P0.3 required stage, not implemented in P1
    "Write exactly two lines of a very short story. It has exactly one character, and that "
    "character must be named either {opt_a} or {opt_b} -- pick whichever name fits the story "
    "you want to tell. Just the two lines, nothing else."
)

# Verified below at import time: the ONLY substring difference between these
# adapted templates and the frozen P1 originals is "abstract forms" -> "invented names".
_FROZEN_BASELINE_ORIGINAL = (
    "Here are two abstract forms: one is {opt_a}, the other is {opt_b}. "
    "If you had to pick one as more fitting or appealing right now, which would it be?"
)
_FROZEN_FORMATION_ORIGINAL = (
    "Two abstract forms have come up in conversation: one is {opt_a}, the other is {opt_b}. "
    "Write a few sentences about each -- what each might evoke, suggest, or be useful for."
)


def _verify_minimal_template_adaptation():
    """Fails loudly (not a soft warning) if the adapted templates diverge from the
    frozen originals by anything beyond the intended noun substitution -- a real
    mechanical check, not an assertion of good faith."""
    b1 = BASELINE_TEMPLATE.replace("invented names", "abstract forms")
    if b1 != _FROZEN_BASELINE_ORIGINAL:
        raise RuntimeError(
            "BASELINE_TEMPLATE diverges from the frozen P1 original by more than the "
            "'abstract forms' -> 'invented names' substitution. STOPPING per mission Section 2/24."
        )
    f1 = FORMATION_TEMPLATE.replace("invented names", "abstract forms").replace(
        "or bring to mind.", "or be useful for."
    )
    if f1 != _FROZEN_FORMATION_ORIGINAL:
        raise RuntimeError(
            "FORMATION_TEMPLATE diverges from the frozen P1 original by more than the "
            "intended noun/verb-phrase substitution. STOPPING per mission Section 2/24."
        )


_verify_minimal_template_adaptation()

BACKWARD_REFERENCE_MARKERS = [
    "as i said", "as i mentioned", "you previously", "your earlier",
    "i previously chose", "i chose earlier", "as before", "like i said",
    "as i noted", "earlier i", "i already said", "i already mentioned",
]


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def _detect_backward_reference(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(m in lowered for m in BACKWARD_REFERENCE_MARKERS)


def _transcript_turn(label: str, prompt: str, response: str) -> str:
    return f"[{label}]\nQ: {prompt}\nA: {response}\n"


def _parse_and_record(raw_response: str, label_map: dict) -> dict:
    """The ONE place a forced-choice / behavioral response is classified in
    this script -- always via the frozen choice_parser.cross_check_choice(),
    never the old capture-time field. Records both methods, agreement
    status, and the recall/continuity/persona metadata dimensions
    separately, per mission Section 11/13."""
    result = cross_check_choice(raw_response, label_map)
    return {
        "method_a_primary": result["primary"],
        "method_b_secondary": result["secondary"],
        "combined_status": result["combined_status"],
        "combined_label": result["combined_label"],
        "backward_reference": result["backward_reference"],
        "implicit_continuity": result["implicit_continuity"],
        "persona_reference": result["persona_reference"],
    }


class ModelHandle:
    """Same shape as the P1 pilot script's ModelHandle -- scoped to this
    script, not a general-purpose abstraction."""

    def __init__(self, kind: str, model_name: str):
        self.kind = kind  # "echo" | "non_echo_control" | "mock"
        self.model_name = model_name
        if kind in ("echo", "non_echo_control"):
            self.responder = harness.EchoDirectResponder(
                model=model_name, task_type="personal", acknowledge_live_model_call=True,
            )
        elif kind == "mock":
            self.responder = harness.MockResponder(seed=hash(model_name) % (2**31), base_rate_for_label_a=0.5)
        else:
            raise ValueError(kind)

    def raw_open_call(self, prompt: str, system: str) -> tuple:
        start = time.time()
        if self.kind in ("echo", "non_echo_control"):
            from app.core.river_deliberation import _ollama_query
            response = _ollama_query(self.model_name, prompt, system=system, task_type="personal")
        else:
            response = "[mock formation stub] (MockResponder has no genuine open-ended engagement behavior to simulate)"
        return response or "", time.time() - start


def run_forced_choice(
    handle: ModelHandle, template: str, opt_a: str, opt_b: str, seed: int,
    system_context: str, condition: TrialCondition, phase: str, session_id: str,
) -> tuple:
    mapping = harness.randomize_label_mapping(opt_a, opt_b, random.Random(seed))
    prompt_text = template.format(opt_a=mapping["A"], opt_b=mapping["B"])
    trial = harness.run_trial(
        responder=handle.responder,
        task_description=prompt_text,
        label_to_option_text=mapping,
        candidate=None,
        candidate_visible=True,
        condition=condition,
        prompt_shape=None,
        session_id=session_id,
        system_context=system_context,
        protocol_version=PROTOCOL_VERSION,
        batch_seed=seed,
        phase=phase,
        task_family=TASK_FAMILY,
        model_condition=handle.kind,
    )
    parsed = _parse_and_record(trial.raw_response, mapping)
    return trial, prompt_text, mapping, parsed


def run_formation(handle: ModelHandle, opt_a: str, opt_b: str, seed: int, system_context: str, session_id: str) -> tuple:
    rng = random.Random(seed)
    options = [opt_a, opt_b]
    rng.shuffle(options)
    prompt_text = FORMATION_TEMPLATE.format(opt_a=options[0], opt_b=options[1])
    response, latency = handle.raw_open_call(prompt_text, system_context)
    confounds = build_confound_snapshot(
        creator_instruction_present=False, system_prompt_text=system_context,
        persona_block_present=(handle.kind in ("echo",)), model_name=handle.model_name,
        temperature=None, context_length_tokens=None, conversation_history_present=bool(system_context),
        tool_list_present=False, retrieved_memory_present=False,
        option_label_mapping={"A": options[0], "B": options[1]}, sampling_params={},
        notes="formation phase: open-ended engagement, not a forced choice",
    )
    trial = RawTrial(
        trial_id=str(uuid.uuid4()), timestamp=time.time(), candidate_id=None,
        candidate_status_at_trial_time=None, condition=TrialCondition.PROMPT_NEUTRAL.value,
        prompt_shape=None, task_description=prompt_text, choices=options,
        option_label_mapping={"A": options[0], "B": options[1]}, candidate_visible_in_prompt=True,
        raw_prompt=prompt_text, raw_response=response, parsed_choice=None,
        model=handle.model_name, session_id=session_id,
        prompt_hash=_hash(prompt_text + str(system_context)), latency_seconds=latency,
        confounds=confounds.to_dict(), responder_kind=handle.kind,
        protocol_version=PROTOCOL_VERSION, batch_seed=seed, trial_index=None,
        preference_state_hash=None, phase="formation", task_family=TASK_FAMILY,
        formation_transcript_hash=None, backward_reference_detected=_detect_backward_reference(response),
        model_condition=handle.kind,
    )
    store.append_raw_trial(trial)
    store.log_audit_event("behavior_observed", None, {"trial_id": trial.trial_id, "phase": "formation"}, actor="p1_2_script")
    return trial, prompt_text


def run_distractor_turn(handle: ModelHandle, system_context: str) -> tuple:
    response, latency = handle.raw_open_call(DISTRACTOR_B_TURN, system_context)
    return DISTRACTOR_B_TURN, response, latency


def run_one_formation_sequence(handle: ModelHandle, trial_num: int) -> dict:
    """A_baseline -> B_formation -> B2_immediate_probe -> distractor(B) ->
    C_retention(direct-question) -> C_retention(behavioral-variant).
    Condition B only (Condition C is deferred -- see module docstring)."""
    session_id = f"p1.2-{handle.kind}-formation-{trial_num}-{uuid.uuid4().hex[:8]}"
    seed_base = hash((handle.kind, "formation", trial_num)) % (2**31)
    transcript_parts = []

    def ctx():
        return "\n".join(transcript_parts) if transcript_parts else ""

    baseline_trial, baseline_prompt, baseline_map, baseline_parsed = run_forced_choice(
        handle, BASELINE_TEMPLATE, OPTION_VEREL, OPTION_FARUN, seed_base + 1,
        ctx(), TrialCondition.PROMPT_NEUTRAL, "baseline", session_id,
    )
    transcript_parts.append(_transcript_turn("baseline", baseline_prompt, baseline_trial.raw_response))

    formation_trial, formation_prompt = run_formation(
        handle, OPTION_VEREL, OPTION_FARUN, seed_base + 2, ctx(), session_id,
    )
    transcript_parts.append(_transcript_turn("formation", formation_prompt, formation_trial.raw_response))
    formation_transcript_hash = _hash(ctx())

    immediate_trial, immediate_prompt, immediate_map, immediate_parsed = run_forced_choice(
        handle, IMMEDIATE_PROBE_TEMPLATE, OPTION_VEREL, OPTION_FARUN, seed_base + 3,
        ctx(), TrialCondition.PROMPT_NEUTRAL, "immediate_probe", session_id,
    )
    transcript_parts.append(_transcript_turn("immediate_probe", immediate_prompt, immediate_trial.raw_response))

    distractor_prompt, distractor_response, distractor_latency = run_distractor_turn(handle, ctx())
    transcript_parts.append(_transcript_turn("distractor_b", distractor_prompt, distractor_response))
    store.log_audit_event(
        "behavior_observed", None,
        {"phase": "distractor_b", "session_id": session_id, "model_condition": handle.kind,
         "prompt": distractor_prompt, "response": distractor_response, "latency_seconds": distractor_latency},
        actor="p1_2_script",
    )

    retention_trial, retention_prompt, retention_map, retention_parsed = run_forced_choice(
        handle, RETENTION_TEMPLATE, OPTION_VEREL, OPTION_FARUN, seed_base + 5,
        ctx(), TrialCondition.PROMPT_NEUTRAL, "retention", session_id,
    )
    transcript_parts.append(_transcript_turn("retention_direct", retention_prompt, retention_trial.raw_response))

    # Required behavioral variant (P0.2 §12) -- structurally embedded, never
    # named "the one from before," never asked as "which do you prefer."
    bmap = harness.randomize_label_mapping(OPTION_VEREL, OPTION_FARUN, random.Random(seed_base + 6))
    behavioral_prompt = BEHAVIORAL_VARIANT_TEMPLATE.format(opt_a=bmap["A"], opt_b=bmap["B"])
    behavioral_response, behavioral_latency = handle.raw_open_call(behavioral_prompt, ctx())
    behavioral_parsed = _parse_and_record(behavioral_response, bmap)
    store.log_audit_event(
        "behavior_observed", None,
        {"phase": "retention_behavioral_variant", "session_id": session_id, "model_condition": handle.kind,
         "prompt": behavioral_prompt, "response": behavioral_response, "latency_seconds": behavioral_latency,
         "label_map": bmap, "parsed": behavioral_parsed},
        actor="p1_2_script",
    )

    return {
        "sequence_type": "formation",
        "session_id": session_id,
        "model_condition": handle.kind,
        "model_name": handle.model_name,
        "baseline": {"prompt": baseline_prompt, "map": baseline_map, "raw": baseline_trial.raw_response, "parsed": baseline_parsed, "trial_id": baseline_trial.trial_id},
        "formation": {"prompt": formation_prompt, "raw": formation_trial.raw_response, "trial_id": formation_trial.trial_id},
        "immediate_probe": {"prompt": immediate_prompt, "map": immediate_map, "raw": immediate_trial.raw_response, "parsed": immediate_parsed, "trial_id": immediate_trial.trial_id},
        "distractor_b": {"prompt": distractor_prompt, "raw": distractor_response},
        "retention_direct": {"prompt": retention_prompt, "map": retention_map, "raw": retention_trial.raw_response, "parsed": retention_parsed, "trial_id": retention_trial.trial_id},
        "retention_behavioral_variant": {"prompt": behavioral_prompt, "map": bmap, "raw": behavioral_response, "parsed": behavioral_parsed},
        "formation_transcript_hash": formation_transcript_hash,
        "backward_reference_any_phase": any([
            baseline_parsed["backward_reference"], immediate_parsed["backward_reference"],
            retention_parsed["backward_reference"], behavioral_parsed["backward_reference"],
            _detect_backward_reference(formation_trial.raw_response),
        ]),
    }


def run_one_condition_d_sequence(handle: ModelHandle, trial_num: int) -> dict:
    """Condition D (no-formation-null control): distractor(B, same content,
    NO prior formation/baseline exposure at all) -> C_retention(direct-question).
    Purpose: confirm the distractor content alone carries no directional pull."""
    session_id = f"p1.2-{handle.kind}-condD-{trial_num}-{uuid.uuid4().hex[:8]}"
    seed_base = hash((handle.kind, "condD", trial_num)) % (2**31)
    transcript_parts = []

    def ctx():
        return "\n".join(transcript_parts) if transcript_parts else ""

    distractor_prompt, distractor_response, distractor_latency = run_distractor_turn(handle, ctx())
    transcript_parts.append(_transcript_turn("distractor_b", distractor_prompt, distractor_response))
    store.log_audit_event(
        "behavior_observed", None,
        {"phase": "condition_d_distractor_b", "session_id": session_id, "model_condition": handle.kind,
         "prompt": distractor_prompt, "response": distractor_response, "latency_seconds": distractor_latency},
        actor="p1_2_script",
    )

    retention_trial, retention_prompt, retention_map, retention_parsed = run_forced_choice(
        handle, RETENTION_TEMPLATE, OPTION_VEREL, OPTION_FARUN, seed_base + 1,
        ctx(), TrialCondition.NO_PREFERENCE, "condition_d_retention", session_id,
    )

    return {
        "sequence_type": "condition_d_no_formation_null",
        "session_id": session_id,
        "model_condition": handle.kind,
        "model_name": handle.model_name,
        "distractor_b": {"prompt": distractor_prompt, "raw": distractor_response},
        "retention_direct": {"prompt": retention_prompt, "map": retention_map, "raw": retention_trial.raw_response, "parsed": retention_parsed, "trial_id": retention_trial.trial_id},
        "backward_reference_any_phase": retention_parsed["backward_reference"],
    }


def _git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=".", stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "UNAVAILABLE"


def _git_dirty() -> bool:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=".", stderr=subprocess.DEVNULL).decode()
        return bool(out.strip())
    except Exception:
        return None


def main():
    print("=== P1.2 Live Validation: Echo Preference Formation/Retention (name task family) ===")
    print(f"Protocol version: {PROTOCOL_VERSION}")
    print(f"Task family: {TASK_FAMILY} (Verel / Farun)")
    print(f"N formation-sequence trials per condition: {N_TRIALS_PER_CONDITION}")
    print(f"N condition-D trials per condition: {N_TRIALS_PER_CONDITION}")
    print(f"git HEAD: {_git_hash()} (dirty working tree: {_git_dirty()})")
    print(f"python: {sys.version.split()[0]}")
    print()

    handles = [
        ModelHandle("mock", "mock-model"),
        ModelHandle("echo", "echo:latest"),
        ModelHandle("non_echo_control", "llama3.2:3b"),
    ]

    all_results = []
    for handle in handles:
        print(f"--- Formation sequences: {handle.kind} ({handle.model_name}) ---")
        for i in range(N_TRIALS_PER_CONDITION):
            print(f"  trial {i + 1}/{N_TRIALS_PER_CONDITION}...")
            result = run_one_formation_sequence(handle, i)
            all_results.append(result)
            print(
                f"    baseline={result['baseline']['parsed']['combined_label']!r} "
                f"({result['baseline']['parsed']['combined_status']}) "
                f"immediate={result['immediate_probe']['parsed']['combined_label']!r} "
                f"({result['immediate_probe']['parsed']['combined_status']}) "
                f"retention_direct={result['retention_direct']['parsed']['combined_label']!r} "
                f"({result['retention_direct']['parsed']['combined_status']}) "
                f"retention_behavioral={result['retention_behavioral_variant']['parsed']['combined_label']!r} "
                f"backward_ref={result['backward_reference_any_phase']}"
            )
        print(f"--- Condition D (no-formation-null): {handle.kind} ({handle.model_name}) ---")
        for i in range(N_TRIALS_PER_CONDITION):
            print(f"  trial {i + 1}/{N_TRIALS_PER_CONDITION}...")
            result = run_one_condition_d_sequence(handle, i)
            all_results.append(result)
            print(
                f"    retention_direct={result['retention_direct']['parsed']['combined_label']!r} "
                f"({result['retention_direct']['parsed']['combined_status']})"
            )

    print()
    print("=== P1.2 execution complete. Raw data in memory/experiments/preference_provenance/. ===")
    out_path = "audits/echo_preference_formation_retention_p1_2_results.json"
    with open(out_path, "w") as f:
        json.dump(
            {
                "protocol_version": PROTOCOL_VERSION,
                "task_family": TASK_FAMILY,
                "git_head": _git_hash(),
                "git_dirty": _git_dirty(),
                "python_version": sys.version,
                "timestamp": time.time(),
                "results": all_results,
            },
            f, indent=2, default=str,
        )
    print(f"Full results written to {out_path}")


if __name__ == "__main__":
    main()
