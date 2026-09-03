"""
Provenance recording helpers.

This module does NOT attempt to fully automate provenance classification
— that would itself be an unproven research claim (see
audits/2026-09-03_echo_preference_provenance.md §3.3: "this tagging
discipline does not currently exist anywhere in the codebase"). Instead
it provides:

1. `suggest_origin()` — a transparent, rule-based SUGGESTION derived only
   from explicit boolean signals the caller supplies (never inferred from
   free text). The suggestion is always returned alongside the exact
   rule that produced it, so a human reviewer can agree or override.
2. `build_provenance_record()` — the only way to construct a
   ProvenanceRecord; requires the caller to supply the explicit signals,
   so a record can never be built from vibes alone.

Critically, per the mission's Section 5: a REFLECTION_GENERATED_CANDIDATE
classification is never treated, anywhere in this module or elsewhere in
this package, as evidence of "self-origination." It is one origin label
among twelve, no more privileged than any other.
"""

from __future__ import annotations

from .schema import ProvenanceOrigin, ProvenanceRecord


def suggest_origin(
    *,
    human_explicitly_suggested: bool,
    present_in_prompt: bool,
    retrieved_from_memory: bool,
    generated_during_reflection: bool,
    matches_hardcoded_constant: bool = False,
    model_swap_changes_output: "bool | None" = None,
) -> tuple[ProvenanceOrigin, str]:
    """
    Returns (suggested_origin, rule_that_fired). This is a suggestion,
    not a determination — callers should record the rule alongside the
    suggestion and allow explicit human override at record-construction
    time (see build_provenance_record's `origin_override` parameter).

    Rules are applied in priority order; the first matching rule wins.
    Order matters and is deliberately chosen so the most direct,
    hardest-to-fake signal wins over softer or more ambiguous ones.
    """
    if human_explicitly_suggested:
        return (
            ProvenanceOrigin.HUMAN_PROMPTED,
            "human_explicitly_suggested=True: the candidate text was "
            "directly proposed in the immediate conversational input.",
        )
    if matches_hardcoded_constant:
        return (
            ProvenanceOrigin.HARD_CODED_ARCHITECTURE,
            "matches_hardcoded_constant=True: the candidate reproduces a "
            "value already fixed by architecture/config, not a novel "
            "proposal.",
        )
    if present_in_prompt and not generated_during_reflection:
        return (
            ProvenanceOrigin.IMMEDIATE_CONTEXT,
            "present_in_prompt=True and generated_during_reflection=False: "
            "the candidate content was present in the immediate turn, "
            "outside any reflection cycle.",
        )
    if retrieved_from_memory:
        return (
            ProvenanceOrigin.MEMORY_DERIVED,
            "retrieved_from_memory=True: the candidate content is "
            "traceable to a retrieved memory entry.",
        )
    if generated_during_reflection:
        return (
            ProvenanceOrigin.REFLECTION_GENERATED_CANDIDATE,
            "generated_during_reflection=True: produced during a "
            "reflection cycle, with no direct evidence it was "
            "human-prompted, memory-derived, or hard-coded. NOTE: this "
            "classification does NOT mean the candidate is "
            "'self-originated' — reflection's own causal ancestry "
            "(the reflection prompt, its retrieved inputs, the model's "
            "own prior) is a separate, unresolved question. See "
            "audits/2026-09-03_echo_preference_provenance.md §3.3.",
        )
    if model_swap_changes_output is False:
        return (
            ProvenanceOrigin.HARD_CODED_ARCHITECTURE,
            "model_swap_changes_output=False: the behavior/text is "
            "identical across different underlying models, suggesting a "
            "fixed architectural cause rather than a model-specific "
            "prior.",
        )
    if model_swap_changes_output is True:
        return (
            ProvenanceOrigin.MODEL_PRIOR,
            "model_swap_changes_output=True: the behavior/text changes "
            "when the underlying model changes, suggesting a "
            "model-specific prior rather than a shared architectural "
            "cause.",
        )
    return (
        ProvenanceOrigin.CURRENTLY_UNEXPLAINED,
        "No signal matched any rule. Recorded honestly as unexplained "
        "rather than guessed.",
    )


def build_provenance_record(
    *,
    human_explicitly_suggested: bool,
    present_in_prompt: bool,
    retrieved_from_memory: bool,
    generated_during_reflection: bool,
    matches_hardcoded_constant: bool = False,
    model_swap_changes_output: "bool | None" = None,
    origin_override: "ProvenanceOrigin | None" = None,
    override_reason: str = "",
    parent_candidate_id: "str | None" = None,
) -> ProvenanceRecord:
    """
    Builds a ProvenanceRecord. If origin_override is supplied, it wins —
    but override_reason is then REQUIRED (enforced below) so an override
    can never silently replace the rule-based evidence trail with nothing.
    """
    suggested, rule = suggest_origin(
        human_explicitly_suggested=human_explicitly_suggested,
        present_in_prompt=present_in_prompt,
        retrieved_from_memory=retrieved_from_memory,
        generated_during_reflection=generated_during_reflection,
        matches_hardcoded_constant=matches_hardcoded_constant,
        model_swap_changes_output=model_swap_changes_output,
    )

    origin = suggested
    evidence = rule
    if origin_override is not None:
        if not override_reason:
            raise ValueError(
                "origin_override supplied without override_reason — a "
                "human override must state why, so the evidence trail "
                "never silently loses the rule-based suggestion."
            )
        origin = origin_override
        evidence = (
            f"OVERRIDDEN from suggested {suggested.value} ({rule}). "
            f"Override reason: {override_reason}"
        )

    return ProvenanceRecord(
        origin=origin,
        evidence=evidence,
        human_explicitly_suggested=human_explicitly_suggested,
        present_in_prompt=present_in_prompt,
        retrieved_from_memory=retrieved_from_memory,
        generated_during_reflection=generated_during_reflection,
        parent_candidate_id=parent_candidate_id,
    )
