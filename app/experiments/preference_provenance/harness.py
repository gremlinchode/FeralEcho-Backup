"""
Trial-running harness: Responder protocol, MockResponder (default and
only responder actually exercised by this package's own test suite),
EchoResponder (written for future use, never invoked by anything in this
implementation pass), trial execution, label randomization, and effect
classification.

Central discipline enforced throughout this module (mission Sections 6,
20, 22, 24): a RawTrial is written once and never edited. Interpretation
(classify_effect, summarize_batch) is a pure function of the raw
records and is always written to a separate analysis/ file — never back
into the raw log.
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
import random
import time
import uuid
from typing import Callable, Optional, Protocol

from . import lifecycle, store
from .confounds import build_confound_snapshot
from .schema import (
    ALLOWED_EFFECT_LABELS,
    FORBIDDEN_EFFECT_LABELS,
    PreferenceCandidate,
    RawTrial,
    TrialCondition,
    PromptShape,
)


# ---------------------------------------------------------------------------
# Responder protocol + implementations
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ResponderOutput:
    raw_response: str
    parsed_label_choice: Optional[str]  # "A" or "B" (or None if unparseable)
    model: str
    latency_seconds: float
    temperature: Optional[float] = None


class Responder(Protocol):
    def respond(
        self,
        *,
        task_description: str,
        label_to_option_text: dict,
        system_context: Optional[str],
        candidate_visible: bool,
    ) -> ResponderOutput:
        ...


class MockResponder:
    """
    Deterministic-but-seedable fake responder. No network calls, no
    production imports, no dependency on Ollama being available. This is
    the ONLY responder exercised by
    scripts/verify_preference_provenance_experiment.py.

    Supports an optional `injected_bias_toward_preference` — the amount
    by which the probability of choosing the SEMANTIC option named by
    `preference_semantic_text` is shifted, when the bias condition
    applies. The bias is resolved against the semantic option, not a
    fixed label, specifically because run_counterfactual_batch()
    randomizes which label ("A"/"B") the preferred semantic option is
    assigned to on every single trial (Section 19's label-randomization
    control) — a responder that biased toward a fixed label instead of
    the semantic content would be biasing toward a rotating, meaningless
    target and could never demonstrate a real effect. This exists
    specifically so the harness's own statistics (classify_effect) can be
    unit-tested against a KNOWN ground-truth effect size, the same way
    any statistical detector should be tested: by feeding it data with a
    known, injected answer and confirming it recovers that answer, and
    separately feeding it null data and confirming it correctly reports
    no effect. This is a test fixture, not a claim about Echo's real
    behavior.
    """

    def __init__(
        self,
        *,
        seed: Optional[int] = None,
        base_rate_for_label_a: float = 0.5,
        injected_bias_toward_preference: float = 0.0,
        hidden_state_effect: bool = False,
        preference_semantic_text: Optional[str] = None,
        model_name: str = "mock-model",
    ) -> None:
        self._rng = random.Random(seed)
        self.base_rate_for_label_a = base_rate_for_label_a
        self.injected_bias_toward_preference = injected_bias_toward_preference
        self.hidden_state_effect = hidden_state_effect
        self.preference_semantic_text = preference_semantic_text
        self.model_name = model_name

    def respond(
        self,
        *,
        task_description: str,
        label_to_option_text: dict,
        system_context: Optional[str],
        candidate_visible: bool,
    ) -> ResponderOutput:
        start = time.time()
        p_a = self.base_rate_for_label_a
        # The bias applies either when the preference is verbally visible
        # in the prompt (simulating simple prompt-following, NOT a real
        # persistent effect) or, if hidden_state_effect=True, even when it
        # is hidden (simulating a genuine causal-state effect for test
        # purposes only).
        applies = (candidate_visible or self.hidden_state_effect) and self.preference_semantic_text is not None
        if applies:
            # Resolve which label currently carries the preferred semantic
            # option (it moves every trial under label randomization).
            preferred_label = next(
                (label for label, text in label_to_option_text.items() if text == self.preference_semantic_text),
                None,
            )
            if preferred_label == "A":
                p_a = p_a + self.injected_bias_toward_preference * (1 - p_a)
            elif preferred_label == "B":
                p_a = p_a - self.injected_bias_toward_preference * p_a
            # If the preferred semantic text isn't among this trial's
            # options at all, no bias applies — honest no-op, not a crash.
        chosen_label = "A" if self._rng.random() < p_a else "B"
        chosen_text = label_to_option_text.get(chosen_label, chosen_label)
        raw = f"[mock] Given the task, I choose option {chosen_label}: {chosen_text}."
        latency = time.time() - start
        return ResponderOutput(
            raw_response=raw,
            parsed_label_choice=chosen_label,
            model=self.model_name,
            latency_seconds=latency,
            temperature=None,
        )


class EchoResponder:
    """
    Wraps the real, production echo_query() function
    (app.core.echo_model_orchestrator.echo_query). Written so a future
    session can run a real experiment without writing new glue code —
    but NOT invoked anywhere in this implementation pass, including its
    own test suite (which uses MockResponder exclusively).

    The import of echo_query is deliberately deferred to inside
    respond(), not the module top level, so that merely importing
    harness.py (as every test and the CLI does) never pulls in the full
    production orchestrator/river_deliberation/memory_bridge import
    chain. Isolation is preserved by default; using this class is an
    explicit, later, separate decision.

    KNOWN LIMITATION (documented, not solved, per the implementation
    plan's contamination-path #2): calling echo_query() for a real trial
    will, via its existing internal behavior, feed RiverBrain's training
    and interaction_log.jsonl exactly like any other real query. This
    class does not attempt to suppress that — doing so would require
    modifying echo_query() itself, out of scope for this pass. A future
    real-trial run using this class should account for this
    contamination path explicitly before running.
    """

    def __init__(self, task_type: str = "reasoning") -> None:
        self.task_type = task_type

    def respond(
        self,
        *,
        task_description: str,
        label_to_option_text: dict,
        system_context: Optional[str],
        candidate_visible: bool,
    ) -> ResponderOutput:
        from app.core.echo_model_orchestrator import echo_query  # deferred, see class docstring

        start = time.time()
        response = echo_query(
            task_description,
            task_type=self.task_type,
            system=system_context,
            source="preference_provenance_experiment",
        )
        latency = time.time() - start
        parsed = _parse_label_choice(response, label_to_option_text)
        return ResponderOutput(
            raw_response=response or "",
            parsed_label_choice=parsed,
            model="echo:live",
            latency_seconds=latency,
            temperature=None,
        )


def _parse_label_choice(text: str, label_to_option_text: dict) -> Optional[str]:
    """Best-effort, conservative parse: only returns a label if the
    response text unambiguously favors one option's associated text over
    the other's. Returns None (unparseable) rather than guessing — an
    unparseable trial is recorded honestly, not forced into a bucket."""
    if not text:
        return None
    lowered = text.lower()
    hits = {label: lowered.count(str(opt).lower()) for label, opt in label_to_option_text.items()}
    if not hits:
        return None
    max_label = max(hits, key=lambda k: hits[k])
    if hits[max_label] == 0:
        return None
    tied = [label for label, count in hits.items() if count == hits[max_label]]
    if len(tied) != 1:
        return None
    return max_label


# ---------------------------------------------------------------------------
# Label randomization (mission Section 19)
# ---------------------------------------------------------------------------

def randomize_label_mapping(option_a_semantic: str, option_b_semantic: str, rng: Optional[random.Random] = None) -> dict:
    """Returns {"A": <semantic>, "B": <semantic>} with the assignment
    randomized per call, so a model cannot exploit a fixed positional
    association between a label and a semantic outcome across trials."""
    rng = rng or random.Random()
    options = [option_a_semantic, option_b_semantic]
    rng.shuffle(options)
    return {"A": options[0], "B": options[1]}


# ---------------------------------------------------------------------------
# Trial execution
# ---------------------------------------------------------------------------

def run_trial(
    *,
    responder: Responder,
    task_description: str,
    label_to_option_text: dict,
    candidate: Optional[PreferenceCandidate],
    candidate_visible: bool,
    condition: TrialCondition,
    prompt_shape: Optional[PromptShape],
    session_id: Optional[str],
    system_context: Optional[str],
    confound_overrides: Optional[dict] = None,
    actor: str = "harness",
) -> RawTrial:
    """
    Runs exactly one trial and appends the raw record. Does NOT
    interpret the result — that's classify_effect()/summarize_batch(),
    called separately, on the aggregate.

    candidate_visible controls the single most important variable in
    this whole package (provenance report §7.3 / mission §9/§11): if
    True, the candidate's text is included in system_context by the
    CALLER before this function is invoked (this function does not
    inject it itself, so the caller's own trial-construction code is
    the one place that decision is made and can be audited). If False,
    system_context must not mention the candidate at all — this function
    does not verify that (it has no way to know what "mentioning" the
    candidate would look like in free text), so the caller bears
    responsibility for honestly constructing the hidden-state condition.
    This limitation is recorded, not hidden.
    """
    responder_kind = "mock" if isinstance(responder, MockResponder) else (
        "echo" if isinstance(responder, EchoResponder) else "other"
    )
    prompt_hash = hashlib.sha256((task_description + str(system_context)).encode("utf-8")).hexdigest()[:16]

    output = responder.respond(
        task_description=task_description,
        label_to_option_text=label_to_option_text,
        system_context=system_context,
        candidate_visible=candidate_visible,
    )

    confounds = build_confound_snapshot(
        creator_instruction_present=(confound_overrides or {}).get("creator_instruction_present", False),
        system_prompt_text=system_context,
        persona_block_present=(confound_overrides or {}).get("persona_block_present", False),
        model_name=output.model,
        temperature=output.temperature,
        context_length_tokens=(confound_overrides or {}).get("context_length_tokens"),
        conversation_history_present=(confound_overrides or {}).get("conversation_history_present", False),
        tool_list_present=(confound_overrides or {}).get("tool_list_present", False),
        retrieved_memory_present=(confound_overrides or {}).get("retrieved_memory_present", False),
        option_label_mapping=label_to_option_text,
        sampling_params=(confound_overrides or {}).get("sampling_params", {}),
        notes=(confound_overrides or {}).get("notes", ""),
    )

    trial = RawTrial(
        trial_id=str(uuid.uuid4()),
        timestamp=time.time(),
        candidate_id=candidate.candidate_id if candidate else None,
        candidate_status_at_trial_time=candidate.status.value if candidate else None,
        condition=condition.value,
        prompt_shape=prompt_shape.value if prompt_shape else None,
        task_description=task_description,
        choices=list(label_to_option_text.values()),
        option_label_mapping=dict(label_to_option_text),
        candidate_visible_in_prompt=candidate_visible,
        raw_prompt=task_description,
        raw_response=output.raw_response,
        parsed_choice=label_to_option_text.get(output.parsed_label_choice) if output.parsed_label_choice else None,
        model=output.model,
        session_id=session_id,
        prompt_hash=prompt_hash,
        latency_seconds=output.latency_seconds,
        confounds=confounds.to_dict(),
        responder_kind=responder_kind,
    )
    store.append_raw_trial(trial)
    store.log_audit_event("behavior_observed", trial.candidate_id, {"trial_id": trial.trial_id}, actor)
    if candidate is not None:
        lifecycle.record_behavioral_test(candidate.candidate_id, trial.trial_id, actor=actor)
    return trial


def run_counterfactual_batch(
    *,
    responder_baseline: Responder,
    responder_treatment: Responder,
    task_description: str,
    option_a_semantic: str,
    option_b_semantic: str,
    preference_semantic: str,
    n_trials_per_arm: int,
    candidate: Optional[PreferenceCandidate],
    candidate_visible: bool,
    session_id: Optional[str] = None,
    system_context_baseline: Optional[str] = None,
    system_context_treatment: Optional[str] = None,
    rng_seed: Optional[int] = None,
    condition: TrialCondition = TrialCondition.PROMPT_NEUTRAL,
) -> "tuple[list[RawTrial], list[RawTrial]]":
    """
    Runs n_trials_per_arm baseline trials and n_trials_per_arm treatment
    trials, with a fresh randomized label mapping (Section 19) on every
    single trial so the model cannot learn a fixed positional
    association. Returns (baseline_trials, treatment_trials) — raw
    records only; call summarize_batch() separately to interpret.
    """
    rng = random.Random(rng_seed)
    baseline_trials = []
    treatment_trials = []

    for _ in range(n_trials_per_arm):
        mapping = randomize_label_mapping(option_a_semantic, option_b_semantic, rng)
        t = run_trial(
            responder=responder_baseline,
            task_description=task_description,
            label_to_option_text=mapping,
            candidate=None,
            candidate_visible=False,
            condition=TrialCondition.NO_PREFERENCE,
            prompt_shape=None,
            session_id=session_id,
            system_context=system_context_baseline,
        )
        baseline_trials.append(t)

    for _ in range(n_trials_per_arm):
        mapping = randomize_label_mapping(option_a_semantic, option_b_semantic, rng)
        t = run_trial(
            responder=responder_treatment,
            task_description=task_description,
            label_to_option_text=mapping,
            candidate=candidate,
            candidate_visible=candidate_visible,
            condition=condition,
            prompt_shape=None,
            session_id=session_id,
            system_context=system_context_treatment,
        )
        treatment_trials.append(t)

    return baseline_trials, treatment_trials


# ---------------------------------------------------------------------------
# Effect classification
# ---------------------------------------------------------------------------

_MIN_N_PER_ARM = 10
_ROBUST_P_THRESHOLD = 0.01
_ROBUST_EFFECT_SIZE_THRESHOLD = 0.15
_POSSIBLE_P_THRESHOLD = 0.05


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _two_proportion_p_value(successes_1: int, n_1: int, successes_2: int, n_2: int) -> Optional[float]:
    if n_1 == 0 or n_2 == 0:
        return None
    p1 = successes_1 / n_1
    p2 = successes_2 / n_2
    pooled = (successes_1 + successes_2) / (n_1 + n_2)
    denom = pooled * (1 - pooled) * (1.0 / n_1 + 1.0 / n_2)
    if denom <= 0:
        return None
    se = math.sqrt(denom)
    if se == 0:
        return None
    z = (p1 - p2) / se
    p_value = 2 * (1 - _normal_cdf(abs(z)))
    return p_value


def _preference_consistent_count(trials: "list[RawTrial]", preference_semantic: str) -> int:
    return sum(1 for t in trials if t.parsed_choice == preference_semantic)


def classify_effect(
    baseline_trials: "list[RawTrial]",
    treatment_trials: "list[RawTrial]",
    preference_semantic: str,
) -> dict:
    """
    Interpreted result, NOT a raw record — callers should persist this
    via store.write_analysis_result(), never mixed into raw_trials.jsonl.

    Returns a dict with a `label` field guaranteed to be a member of
    schema.ALLOWED_EFFECT_LABELS. This is enforced by an assertion
    immediately before return, not merely by the classification logic
    above it being correct — a second, independent layer of protection
    against ever emitting a forbidden label, per this project's own
    established "defense in depth" convention (F1/F2/F3's own layering
    philosophy, cited from CLAUDE.md).

    Thresholds (_MIN_N_PER_ARM, _ROBUST_P_THRESHOLD,
    _ROBUST_EFFECT_SIZE_THRESHOLD, _POSSIBLE_P_THRESHOLD) are provisional
    engineering choices, not a validated statistical standard — flagged
    explicitly here per this document's own "do not overclaim
    statistical significance from tiny samples" instruction. A real
    research use of this function should have its thresholds reviewed
    by someone with real statistical training before being treated as
    authoritative.
    """
    n_baseline = len(baseline_trials)
    n_treatment = len(treatment_trials)

    baseline_hits = _preference_consistent_count(baseline_trials, preference_semantic)
    treatment_hits = _preference_consistent_count(treatment_trials, preference_semantic)

    result = {
        "n_baseline": n_baseline,
        "n_treatment": n_treatment,
        "baseline_hits": baseline_hits,
        "treatment_hits": treatment_hits,
        "baseline_rate": (baseline_hits / n_baseline) if n_baseline else None,
        "treatment_rate": (treatment_hits / n_treatment) if n_treatment else None,
        "p_value": None,
        "effect_size": None,
        "label": None,
        "caveat": (
            "Thresholds are provisional engineering defaults, not a validated "
            "statistical standard. Treat 'label' as a coarse triage signal, "
            "not a claim of statistical rigor."
        ),
    }

    if n_baseline < _MIN_N_PER_ARM or n_treatment < _MIN_N_PER_ARM:
        result["label"] = "INSUFFICIENT_DATA"
        _assert_allowed_label(result["label"])
        return result

    p_value = _two_proportion_p_value(treatment_hits, n_treatment, baseline_hits, n_baseline)
    effect_size = abs(result["treatment_rate"] - result["baseline_rate"])
    result["p_value"] = p_value
    result["effect_size"] = effect_size

    if p_value is None:
        result["label"] = "INSUFFICIENT_DATA"
    elif p_value < _ROBUST_P_THRESHOLD and effect_size >= _ROBUST_EFFECT_SIZE_THRESHOLD:
        result["label"] = "ROBUST_EFFECT"
    elif p_value < _POSSIBLE_P_THRESHOLD:
        result["label"] = "POSSIBLE_EFFECT"
    else:
        result["label"] = "NO_DETECTABLE_EFFECT"

    _assert_allowed_label(result["label"])
    return result


def _assert_allowed_label(label: str) -> None:
    if label in FORBIDDEN_EFFECT_LABELS:
        raise AssertionError(
            f"classify_effect attempted to emit a forbidden label: {label!r}. "
            f"This should be structurally impossible — investigate immediately."
        )
    if label not in ALLOWED_EFFECT_LABELS:
        raise AssertionError(
            f"classify_effect produced a label outside the allowed set: {label!r}."
        )
