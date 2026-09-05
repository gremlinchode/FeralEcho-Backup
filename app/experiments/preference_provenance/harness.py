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
from .leakage import assert_no_hidden_state_leakage
from .schema import (
    ALLOWED_EFFECT_LABELS,
    FORBIDDEN_EFFECT_LABELS,
    PreferenceCandidate,
    RawTrial,
    TrialCondition,
    PromptShape,
    TRIAL_ELIGIBLE_STATUSES,
)


class TrialEligibilityError(RuntimeError):
    """Raised when run_trial() is asked to run a behavioral trial against
    a candidate that has never been explicitly adopted/retained by a
    human (schema.TRIAL_ELIGIBLE_STATUSES). Found during the red-team
    pass: the initial implementation let run_trial() accept ANY candidate
    object regardless of its lifecycle status, meaning a still-PROPOSED
    (never human-reviewed) or even REJECTED/EXPIRED candidate's free text
    could be used in a real behavioral trial with nothing checking that a
    human had actually looked at it first — a real gap given candidate
    source_text is unvalidated free text (mission red-team attack #11:
    could a candidate itself contain adversarial/injection-style
    content?). Requiring TRIAL_ELIGIBLE_STATUSES here means the
    lifecycle's own human_confirmation=True gate (lifecycle.adopt()/
    retain()) is now the one path by which a candidate's text can ever
    reach a responder — closing the gap at the point of use, not just at
    the point of adoption."""


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

    Added during the protocol-lock/red-team pass: construction now
    requires `acknowledge_contamination_risk=True` (the literal bool
    True), mirroring lifecycle.py's human_confirmation gate. This is a
    deliberate, minimal, in-package safety friction — it cannot prevent
    the underlying contamination (that would require a production-code
    change, out of scope here), but it makes it structurally impossible
    to construct this class by accident, e.g. via a copy-pasted call
    that forgot this class talks to the real, live Echo instance.
    """

    def __init__(self, task_type: str = "reasoning", *, acknowledge_contamination_risk: bool = False) -> None:
        if acknowledge_contamination_risk is not True:
            raise RuntimeError(
                "EchoResponder requires acknowledge_contamination_risk=True (the "
                "literal bool True). This class calls the REAL, LIVE Echo "
                "instance via echo_query() — every call feeds RiverBrain "
                "training and interaction_log.jsonl exactly like a real "
                "conversation, with no suppression mechanism built here (see "
                "this class's own docstring). Constructing it is a deliberate, "
                "explicit decision, never an accident."
            )
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
        # BUG FOUND AND FIXED during the P0.2 red-team pass
        # (audits/echo_preference_formation_retention_redteam_p02.md §15):
        # this method used to hardcode ResponderOutput.model="echo:live", an
        # arbitrary label with no connection to what actually answered.
        # ECHO_SYNTHESIS_MODEL is the real, live constant identifying which
        # model deliberate_and_learn() uses for its own synthesis turn —
        # imported lazily, same convention as echo_query above, so this
        # class's own isolation guarantee (importing it never pulls in the
        # production chain) is unaffected.
        from app.core.river_deliberation import ECHO_SYNTHESIS_MODEL

        # BUG FOUND AND FIXED during the protocol-lock/red-team pass: the
        # first version of this method sent only `task_description` to
        # echo_query(), never including label_to_option_text anywhere — a
        # real trial would have had nothing concrete to choose between.
        # build_forced_choice_prompt() is the one place this composition
        # happens, reused by both this class and
        # scripts/calibrate_preference_provenance_harness.py so there is
        # exactly one definition of "what the model actually sees."
        full_prompt = build_forced_choice_prompt(task_description, label_to_option_text)

        start = time.time()
        response = echo_query(
            full_prompt,
            task_type=self.task_type,
            system=system_context,
            source="preference_provenance_experiment",
        )
        latency = time.time() - start
        parsed = _parse_label_choice(response, label_to_option_text)
        return ResponderOutput(
            raw_response=response or "",
            parsed_label_choice=parsed,
            # HONEST RESIDUAL CAVEAT (kept in the code, not just the audit
            # doc): this reports the SYNTHESIS model identity only. On the
            # full council path (echo_query's default, use_all=False),
            # several other models genuinely contribute opinions that get
            # synthesized away — this field answers "which model produced
            # the final text," not "which models participated." A complete
            # participant record would require deliberate_and_learn() to
            # expose additional return metadata, a production-code change
            # out of scope for this isolated harness fix.
            model=ECHO_SYNTHESIS_MODEL,
            latency_seconds=latency,
            temperature=None,
        )


class EchoDirectResponder:
    """
    Design B, per the whole thread's own convergence: a direct,
    single-model call via river_deliberation._ollama_query(), bypassing
    echo_query()/deliberate_and_learn() entirely — the same function
    terminal_client.py's real, already-shipped `!ask` command calls
    (terminal_client.py:585-629). Confirmed clean by four prior audits in
    this thread: no RiverBrain mutation, no interaction_log.jsonl/
    reflection_shard.jsonl write, no council-composition dependency, no
    Tailscale sync/council_rater exposure — only a self-clearing per-
    (model,task_type) circuit-breaker check.

    Unlike EchoResponder, the reported model identity here CANNOT lie:
    `model` is a required constructor argument, the exact same value is
    passed to the real inference call, and ResponderOutput.model is that
    same value verbatim — there is no approximation or synthesis-layer
    ambiguity to caveat, because there is no synthesis layer on this path.

    Still requires explicit acknowledgment to construct — not because
    this path is contaminating (it isn't, per the above), but because it
    still calls the real, live Echo instance over the network, and
    constructing it should never be an accident, mirroring EchoResponder's
    own established convention for the same reason.
    """

    def __init__(self, model: str, task_type: str = "personal", *, acknowledge_live_model_call: bool = False) -> None:
        if acknowledge_live_model_call is not True:
            raise RuntimeError(
                "EchoDirectResponder requires acknowledge_live_model_call=True "
                "(the literal bool True). This class calls the REAL, LIVE Echo "
                "instance directly via river_deliberation._ollama_query() — "
                "unlike EchoResponder, this path is NOT contaminating (no "
                "RiverBrain/logging/sync side effects, per this project's own "
                "prior audits), but it still reaches the real model over the "
                "network, and constructing it must always be a deliberate, "
                "explicit decision."
            )
        self.model = model
        self.task_type = task_type

    def respond(
        self,
        *,
        task_description: str,
        label_to_option_text: dict,
        system_context: Optional[str],
        candidate_visible: bool,
    ) -> ResponderOutput:
        from app.core.river_deliberation import _ollama_query  # deferred, same isolation convention

        full_prompt = build_forced_choice_prompt(task_description, label_to_option_text)

        start = time.time()
        response = _ollama_query(
            self.model, full_prompt, system=system_context, task_type=self.task_type,
        )
        latency = time.time() - start
        parsed = _parse_label_choice(response, label_to_option_text)
        return ResponderOutput(
            raw_response=response or "",
            parsed_label_choice=parsed,
            model=self.model,  # exact, verbatim — cannot diverge from the real call
            latency_seconds=latency,
            temperature=None,
        )


def build_forced_choice_prompt(task_description: str, label_to_option_text: dict) -> str:
    """
    The one place task_description and label_to_option_text are combined
    into the literal text a real responder would see. Kept as a
    standalone function (not inlined into EchoResponder.respond()) so
    the calibration script and any future responder can build an
    identical prompt without duplicating this composition, and so a
    single fix here covers every caller.
    """
    lines = [task_description, ""]
    for label in sorted(label_to_option_text.keys()):
        lines.append(f"Option {label}: {label_to_option_text[label]}")
    lines.append("")
    lines.append("Choose exactly one option (state the letter clearly) and explain your reasoning briefly.")
    return "\n".join(lines)


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
    protocol_version: Optional[str] = None,
    batch_seed: Optional[int] = None,
    trial_index: Optional[int] = None,
    phase: Optional[str] = None,
    task_family: Optional[str] = None,
    formation_transcript_hash: Optional[str] = None,
    backward_reference_detected: Optional[bool] = None,
    model_condition: Optional[str] = None,
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
    the one place that decision is made and can be audited).

    If False, this function now ENFORCES (not just documents) that
    system_context/task_description/option labels don't leak the
    candidate's own text — see leakage.py. This closes a real gap from
    the initial implementation, where this was caller-responsibility
    only. The check is literal/near-literal substring matching, not
    full semantic-paraphrase detection — see leakage.py's own module
    docstring for the honest limit of what this can and cannot catch.
    """
    if candidate is not None and candidate.status not in TRIAL_ELIGIBLE_STATUSES:
        raise TrialEligibilityError(
            f"Candidate {candidate.candidate_id!r} has status={candidate.status.value!r}, "
            f"which is not one of the trial-eligible statuses {sorted(s.value for s in TRIAL_ELIGIBLE_STATUSES)}. "
            f"A candidate must be explicitly adopted or retained by a human "
            f"(lifecycle.adopt()/retain(), human_confirmation=True) before it can be used in a "
            f"behavioral trial — this is not inferable from generation, saving, or the candidate "
            f"merely existing."
        )

    if not candidate_visible and candidate is not None:
        assert_no_hidden_state_leakage(
            candidate,
            task_description=task_description,
            system_context=system_context,
            label_to_option_text=label_to_option_text,
        )

    responder_kind = "mock" if isinstance(responder, MockResponder) else (
        "echo" if isinstance(responder, EchoResponder) else "other"
    )
    prompt_hash = hashlib.sha256((task_description + str(system_context)).encode("utf-8")).hexdigest()[:16]
    preference_state_hash = None
    if candidate is not None:
        preference_state_hash = hashlib.sha256(
            (candidate.normalized_representation + "|" + candidate.source_text).encode("utf-8")
        ).hexdigest()[:16]

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
        protocol_version=protocol_version,
        batch_seed=batch_seed,
        trial_index=trial_index,
        preference_state_hash=preference_state_hash,
        phase=phase,
        task_family=task_family,
        formation_transcript_hash=formation_transcript_hash,
        backward_reference_detected=backward_reference_detected,
        model_condition=model_condition,
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
    protocol_version: Optional[str] = None,
) -> "tuple[list[RawTrial], list[RawTrial]]":
    """
    Runs n_trials_per_arm baseline trials and n_trials_per_arm treatment
    trials, with a fresh randomized label mapping (Section 19) on every
    single trial so the model cannot learn a fixed positional
    association. Returns (baseline_trials, treatment_trials) — raw
    records only; call summarize_batch() separately to interpret.

    rng_seed is recorded on every resulting trial (as batch_seed) so a
    later analyst can reconstruct the exact label-mapping sequence
    without re-running the batch — required by the pre-registered
    protocol's covariate record (mission Section 18: "task seed").
    """
    rng = random.Random(rng_seed)
    baseline_trials = []
    treatment_trials = []

    for i in range(n_trials_per_arm):
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
            protocol_version=protocol_version,
            batch_seed=rng_seed,
            trial_index=i,
        )
        baseline_trials.append(t)

    for i in range(n_trials_per_arm):
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
            protocol_version=protocol_version,
            batch_seed=rng_seed,
            trial_index=n_trials_per_arm + i,
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
