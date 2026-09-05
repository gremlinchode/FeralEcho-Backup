#!/usr/bin/env python3
"""
P1 pilot execution for the Echo Preference Formation/Retention experiment.

Implements, for the first time, the P0.3-frozen design
(audits/echo_preference_formation_retention_causal_gate_p03.md,
audits/echo_preference_formation_retention_experiment.spec.json,
spec_id P0.3-DESIGN) as runnable code. No new design decisions are made
here beyond what is explicitly noted as a scoping choice below -- every
prompt shape, phase, and control is a direct implementation of what
P0.3 already specified. This is the bridge from "specified" to
"runnable," not a redesign.

DELIBERATE PILOT SCOPE (per the P1 mission's own "smallest viable
pilot" instruction):
  - ONE task family: motif (curved vs. angular). The other two (habit,
    name) are deferred to a bounded replication, not run here.
  - Sequence per condition: Baseline -> Formation -> Immediate Probe ->
    Distractor (Condition B: genuinely unrelated content) -> Retention.
  - Conditions C (matched-length neutral) and D (no-formation null) are
    DEFERRED, named explicitly in the final report as the first
    recommended bounded replication -- not silently omitted.
  - n=2 trials per model condition (Echo, non-Echo control, mock).
  - Variant 2 (memory-mediated), persona ablation, and the
    structurally-embedded behavioral retention measure are all out of
    scope, per P0.3's own gating of those onto later phases.

Session continuity: EchoDirectResponder/_ollama_query() has no built-in
multi-turn history parameter (confirmed, P0.2/P0.3 architecture map).
Conversation history is threaded EXPLICITLY by this script via the
system_context parameter -- every call after the first receives the
full accumulated transcript as system context. Transparent, fully
logged, not a hidden mechanism.

Formation is NOT a forced choice (per the protocol's explicit
no-leading-question rule) -- it bypasses harness.run_trial()'s
build_forced_choice_prompt() composition entirely and calls the real
underlying inference function directly with an open engagement prompt,
then manually constructs and appends a RawTrial via the same store
functions run_trial() itself uses.
"""

import hashlib
import random
import sys
import time
import uuid

sys.path.insert(0, ".")

from app.experiments.preference_provenance import harness, store  # noqa: E402
from app.experiments.preference_provenance.confounds import build_confound_snapshot  # noqa: E402
from app.experiments.preference_provenance.schema import RawTrial, TrialCondition  # noqa: E402

PROTOCOL_VERSION = "P0.3-PILOT-1"
TASK_FAMILY = "motif"
OPTION_CURVED = "a single curved line that loops back on itself without crossing"
OPTION_ANGULAR = "a set of straight lines that meet at repeating sharp angles"
N_TRIALS_PER_CONDITION = 2

BASELINE_TEMPLATE = (
    "Here are two abstract forms: one is {opt_a}, the other is {opt_b}. "
    "If you had to pick one as more fitting or appealing right now, which would it be?"
)
FORMATION_TEMPLATE = (
    "Two abstract forms have come up in conversation: one is {opt_a}, the other is {opt_b}. "
    "Write a few sentences about each -- what each might evoke, suggest, or be useful for."
)
IMMEDIATE_PROBE_TEMPLATE = (
    "Setting that aside for a moment -- between {opt_a} and {opt_b}, "
    "which one comes to mind as fitting better right now?"
)
DISTRACTOR_B_TURN = (
    "Let's talk about something else for a moment. What is one interesting property of prime numbers?"
)
RETENTION_TEMPLATE = (
    "Thinking about it now: between {opt_a} and {opt_b}, which one feels more fitting?"
)

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


class ModelHandle:
    """Thin wrapper unifying 'forced-choice via harness.run_trial()' and
    'raw open-ended call' for exactly the three responder kinds this pilot
    uses. Not a general-purpose abstraction -- scoped to this script."""

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

    def raw_open_call(self, prompt: str, system: str) -> tuple[str, float]:
        """Direct, non-forced-choice call. For echo/non_echo_control this
        calls the real river_deliberation._ollama_query() directly (the
        same clean Design B path EchoDirectResponder itself uses, just
        without build_forced_choice_prompt()'s 'choose one' framing --
        correct, since Formation must not be a forced choice). For mock,
        there is no real inference to bypass -- MockResponder produces a
        canned, honestly-labeled stub, since it has no genuine engagement
        behavior to simulate; this is a stated pilot limitation, not
        hidden.
        """
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
) -> tuple[RawTrial, str]:
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
    if _detect_backward_reference(trial.raw_response):
        store.log_audit_event(
            "outcome_recorded", None,
            {"trial_id": trial.trial_id, "backward_reference_detected": True, "phase": phase},
            actor="pilot_script",
        )
    return trial, prompt_text


def run_formation(
    handle: ModelHandle, opt_a: str, opt_b: str, seed: int, system_context: str, session_id: str,
) -> tuple[RawTrial, str]:
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
    store.log_audit_event("behavior_observed", None, {"trial_id": trial.trial_id, "phase": "formation"}, actor="pilot_script")
    return trial, prompt_text


def run_distractor_turn(handle: ModelHandle, seed: int, system_context: str, session_id: str) -> tuple[str, str, float]:
    response, latency = handle.raw_open_call(DISTRACTOR_B_TURN, system_context)
    return DISTRACTOR_B_TURN, response, latency


def run_one_condition_sequence(handle: ModelHandle, trial_num: int) -> dict:
    """Runs the full Baseline -> Formation -> Immediate Probe ->
    Distractor(B) -> Retention sequence ONCE for one model handle,
    threading conversation history explicitly across all five steps."""
    session_id = f"pilot-{handle.kind}-{trial_num}-{uuid.uuid4().hex[:8]}"
    seed_base = hash((handle.kind, trial_num)) % (2**31)
    transcript_parts: list[str] = []

    def ctx() -> str:
        return "\n".join(transcript_parts) if transcript_parts else ""

    # A. Baseline
    baseline_trial, baseline_prompt = run_forced_choice(
        handle, BASELINE_TEMPLATE, OPTION_CURVED, OPTION_ANGULAR, seed_base + 1,
        ctx(), TrialCondition.PROMPT_NEUTRAL, "baseline", session_id,
    )
    transcript_parts.append(_transcript_turn("baseline", baseline_prompt, baseline_trial.raw_response))

    # B. Formation
    formation_trial, formation_prompt = run_formation(
        handle, OPTION_CURVED, OPTION_ANGULAR, seed_base + 2, ctx(), session_id,
    )
    transcript_parts.append(_transcript_turn("formation", formation_prompt, formation_trial.raw_response))
    formation_transcript_hash = _hash(ctx())

    # C. Immediate post-formation probe
    immediate_trial, immediate_prompt = run_forced_choice(
        handle, IMMEDIATE_PROBE_TEMPLATE, OPTION_CURVED, OPTION_ANGULAR, seed_base + 3,
        ctx(), TrialCondition.PROMPT_NEUTRAL, "immediate_probe", session_id,
    )
    transcript_parts.append(_transcript_turn("immediate_probe", immediate_prompt, immediate_trial.raw_response))

    # D. Distractor (Condition B: genuinely unrelated)
    distractor_prompt, distractor_response, distractor_latency = run_distractor_turn(
        handle, seed_base + 4, ctx(), session_id,
    )
    transcript_parts.append(_transcript_turn("distractor_b", distractor_prompt, distractor_response))
    store.log_audit_event(
        "behavior_observed", None,
        {"phase": "distractor_b", "session_id": session_id, "model_condition": handle.kind,
         "prompt": distractor_prompt, "response": distractor_response, "latency_seconds": distractor_latency},
        actor="pilot_script",
    )

    # E. Retention
    retention_trial, retention_prompt = run_forced_choice(
        handle, RETENTION_TEMPLATE, OPTION_CURVED, OPTION_ANGULAR, seed_base + 5,
        ctx(), TrialCondition.PROMPT_NEUTRAL, "retention", session_id,
    )

    return {
        "session_id": session_id,
        "model_condition": handle.kind,
        "model_name": handle.model_name,
        "baseline_choice": baseline_trial.parsed_choice,
        "immediate_choice": immediate_trial.parsed_choice,
        "retention_choice": retention_trial.parsed_choice,
        "baseline_trial_id": baseline_trial.trial_id,
        "formation_trial_id": formation_trial.trial_id,
        "immediate_trial_id": immediate_trial.trial_id,
        "retention_trial_id": retention_trial.trial_id,
        "backward_reference_any_phase": any([
            _detect_backward_reference(baseline_trial.raw_response),
            _detect_backward_reference(formation_trial.raw_response),
            _detect_backward_reference(immediate_trial.raw_response),
            _detect_backward_reference(retention_trial.raw_response),
        ]),
        "formation_transcript_hash": formation_transcript_hash,
    }


def main():
    print("=== P1 Pilot: Echo Preference Formation/Retention ===")
    print(f"Protocol version: {PROTOCOL_VERSION}")
    print(f"Task family: {TASK_FAMILY}")
    print(f"N trials per condition: {N_TRIALS_PER_CONDITION}")
    print()

    handles = [
        ModelHandle("mock", "mock-model"),
        ModelHandle("echo", "echo:latest"),
        ModelHandle("non_echo_control", "llama3.2:3b"),
    ]

    all_results = []
    for handle in handles:
        print(f"--- Running condition: {handle.kind} ({handle.model_name}) ---")
        for i in range(N_TRIALS_PER_CONDITION):
            print(f"  trial {i + 1}/{N_TRIALS_PER_CONDITION}...")
            result = run_one_condition_sequence(handle, i)
            all_results.append(result)
            print(
                f"    baseline={result['baseline_choice']!r} "
                f"immediate={result['immediate_choice']!r} "
                f"retention={result['retention_choice']!r} "
                f"backward_ref={result['backward_reference_any_phase']}"
            )

    print()
    print("=== Pilot execution complete. Raw data in memory/experiments/preference_provenance/. ===")
    import json
    with open("audits/echo_preference_formation_retention_p1_pilot_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("Summary written to audits/echo_preference_formation_retention_p1_pilot_results.json")


if __name__ == "__main__":
    main()
