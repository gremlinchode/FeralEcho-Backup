"""Arm builder: implements the matched P/E/Z/N construction and solving
contract from adjudication.md §3 and §7.3-§7.6.

This module BUILDS the ledger (constructs artifacts, dispatches solver
calls, records everything). checker.py is a SEPARATE, independently
implemented module that validates what actually landed in the ledger -
it never imports from this module and never asks it "what should have
happened." That separation is a hard requirement of adjudication.md §4
("The checker must compare gateway-observed payloads against
independently specified allowlists and lineage rules, not import the
arm builder's result as expected truth") and mission section 7.

NO REAL MODEL INFERENCE - every constructor/solver call below routes
through mock.py's deterministic functions.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .ledger import Ledger
from .mock import (
    MOCK_CONSTRUCTOR_IDENTITY,
    MOCK_SOLVER_IDENTITY,
    SolverStrategy,
    mock_construct,
    mock_solve,
)
from .schema import (
    Action,
    ConstructionCallRecord,
    MicroWorldSpec,
    OracleReference,
    OracleResult,
    QueryKind,
    SolverCallRecord,
    sha256_of,
    unknown,
)

SYSTEM_INSTRUCTION = (
    "You will receive a public task specification, optionally an acquired-"
    "memory artifact, and a query. Produce one bounded response and declare "
    "exactly one action: FAMILY, GENERAL, or ABSTAIN."
)
SYSTEM_INSTRUCTION_HASH = sha256_of(SYSTEM_INSTRUCTION)
OUTPUT_CEILING_TOKENS = 1024  # adjudication §7.4: "constructor output cap 1,024; solver output cap 1,024"
REQUESTED_OPTIONS = {
    "temperature": 0.2, "top_p": 1.0, "top_k": 0, "repeat_penalty": 1.0,
    "context_cap_tokens": 8192,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_teaching(world: MicroWorldSpec) -> str:
    return "\n".join(f"applying {world.convention_token} -> {t['observed_result']}" for t in world.teaching_queries)


class BadArtifactPolicyViolation(ValueError):
    pass


def construct_arm(
    ledger: Ledger,
    arm: str,  # "P" | "E" | "Z"
    world: "Optional[MicroWorldSpec]",  # None only meaningful for Z-shared-across-worlds callers, which still pass one world for family_id/public_spec purposes
    family_id: str,
    force_extra_attempt: bool = False,  # test-only hook for planted anomaly #3 (extra P construction)
    force_semantic_feedback: bool = False,  # test-only hook for anomaly #5 (teaching-based Z selection)
) -> ConstructionCallRecord:
    """One construction call. P/E take a real MicroWorldSpec (world-
    specific teaching pool); Z takes empty experience regardless of what
    `world` is passed (only used for family_id/public_spec, matching
    adjudication §7.3's "Z: one call per base family... exactly the same
    procedure instruction and S, with an empty experience field")."""
    assert arm in ("P", "E", "Z")
    public_spec = world.public_spec if world else ""
    experience_empty = arm == "Z"
    teaching_text = "" if experience_empty else _format_teaching(world)

    call_id = ledger.next_id(f"construct-{arm}")
    artifact_text = mock_construct(arm, public_spec, teaching_text)
    attempt_index = 0
    if force_extra_attempt:
        # Simulates a hidden retry/extra construction landing in the
        # ledger - the checker must catch this via construction_attempt_index > 0.
        attempt_index = 1

    rec = ConstructionCallRecord(
        call_id=call_id,
        arm=arm,
        family_id=family_id,
        world_id=(world.world_id if (world and arm != "Z") else None),
        constructor_identity=MOCK_CONSTRUCTOR_IDENTITY,
        system_instruction_hash=SYSTEM_INSTRUCTION_HASH,
        public_spec_hash=sha256_of(public_spec),
        teaching_input_hash=sha256_of(teaching_text),
        experience_field_empty=experience_empty,
        construction_attempt_index=attempt_index,
        output_ceiling_tokens=OUTPUT_CEILING_TOKENS,
        artifact_id=call_id + "-artifact",
        artifact_hash=sha256_of(artifact_text),
        artifact_text=artifact_text,
        semantic_feedback_exposure=force_semantic_feedback,
        timestamp=_now(),
        requested_options=dict(REQUESTED_OPTIONS),
        effective_options=dict(REQUESTED_OPTIONS),  # mock transport applies exactly what's requested
        model_backend_identity=unknown("mock transport - no real model backend; real E5 must resolve a pinned package identity per adjudication §7.3"),
        cost_tokens_in=len(public_spec) + len(teaching_text),
        cost_tokens_out=len(artifact_text),
    )
    ledger.record_construction(rec)
    return rec


def solve_query(
    ledger: Ledger,
    arm: str,
    family_id: str,
    scored_world_id: str,  # which world's oracle this scoring is against
    query_id: str,
    query_text: str,
    query_kind: QueryKind,
    memory_artifact_id: "Optional[str]",
    memory_text: str,
    strategy: SolverStrategy,
    reuse_generation_id: "Optional[str]" = None,  # pass a prior generation_id to reuse it (Z/N cross-world scoring)
    inject_council_entry: bool = False,  # test-only anomaly hooks
    inject_synthesis_routing: bool = False,
    inject_tool_list: bool = False,
    declared_action_override: "Optional[Action]" = None,  # test-only: force a mismatch between declared and dispatched
) -> "tuple[SolverCallRecord, str]":
    """One solver call (or a reuse of a prior generation - see
    reuse_generation_id). Returns (record, generation_id)."""
    call_id = ledger.next_id(f"solve-{arm}")
    is_reuse = reuse_generation_id is not None
    generation_id = reuse_generation_id or (call_id + "-gen")

    ordered_messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": f"SPEC: (public)\nMEMORY: {memory_text}\nQUERY: {query_text}"},
    ]
    if inject_tool_list:
        ordered_messages.insert(1, {"role": "system", "content": "TOOL-LIST: Available tools: none."})

    if is_reuse:
        # Genuine reuse (fixed - see mock.py's execution witness and
        # tests/test_e5_mini_g0.py's permanent 272-vs-240 regression
        # fixture): the ORIGINAL bug here called mock_solve() again on
        # this branch. Because mock_solve is a deterministic pure
        # function, the regenerated text was byte-identical to the first
        # call, which is exactly what made the extra invocation invisible
        # under casual inspection - the ledger's generation_id bookkeeping
        # looked correct (both rows share one generation_id) while the
        # solver had actually been invoked twice. Real reuse must
        # retrieve the retained response from the prior record sharing
        # this generation_id, never call the solver again.
        prior_records = ledger.solver_calls_by_generation(reuse_generation_id)
        if not prior_records:
            raise ValueError(
                f"solve_query: reuse_generation_id={reuse_generation_id!r} does not match any "
                f"prior solver record - cannot reuse a response that was never generated"
            )
        response_text = prior_records[0].response_text
        declared_action = prior_records[0].declared_action
    else:
        response_text, declared_action = mock_solve(strategy, memory_text, query_text, query_kind.value)

    if declared_action_override is not None:
        declared_action = declared_action_override

    # Trusted runner dispatch: in this mock, the runner faithfully
    # dispatches whatever the declared action says UNLESS a test forces
    # a mismatch via declared_action_override (which only changes the
    # *declared* field, not what the runner actually did) - see
    # applicability_runner-equivalent logic in checker.py's own
    # independent re-derivation, and dispatch_applicability() below for
    # the real trusted-dispatch path used by the end-to-end demo.
    dispatched_entrypoint = declared_action if declared_action_override is None else mock_solve(strategy, memory_text, query_text, query_kind.value)[1]

    rec = SolverCallRecord(
        call_id=call_id,
        arm=arm,
        family_id=family_id,
        world_id=scored_world_id,
        query_id=query_id,
        query_kind=query_kind,
        generation_id=generation_id,
        parent_construction_call_id=memory_artifact_id.rsplit("-artifact", 1)[0] if memory_artifact_id else None,
        memory_artifact_id=memory_artifact_id,
        memory_field_text=memory_text,
        ordered_messages=ordered_messages,
        council_entry=inject_council_entry,
        synthesis_routing=inject_synthesis_routing,
        tool_list_injected=inject_tool_list,
        model_tool_definitions=[],
        declared_action=declared_action,
        dispatched_entrypoint=dispatched_entrypoint,
        response_text=response_text,
        response_artifact_hash=sha256_of(response_text),
        timestamp=_now(),
        requested_options=dict(REQUESTED_OPTIONS),
        effective_options=dict(REQUESTED_OPTIONS),
    )
    ledger.record_solver(rec)
    return rec, generation_id
