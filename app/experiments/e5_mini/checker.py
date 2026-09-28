"""Independent condition-integrity checker.

HARD REQUIREMENT (adjudication §4/§7, mission §7): this module must never
import builder.py or orchestrator.py, and must never ask them "what
should have happened." It takes only:

  1. the Ledger (recorded facts - what actually happened), and
  2. an independently-specified ground truth (the MicroWorldSpec fixtures
     - the same shape of input a real task custodian's sealed manifest
     would provide, per adjudication §7.1/§7.2),

and re-derives, from scratch, whether every recorded slot satisfies the
information invariants in adjudication.md §6. A correct hash attached to
the wrong causal lineage is a failure (§4: "A correct hash with the wrong
permitted parent is a failure").
"""
from __future__ import annotations

from dataclasses import dataclass

from .ledger import Ledger
from .schema import Action, ConditionValidity, MicroWorldSpec, OracleResult, sha256_of

WorldKey = "tuple[str, str]"  # (family_id, world_id)

# Independently frozen expected generation-options policy. Deliberately
# NOT imported from builder.py (that would reproduce the exact
# shared-mutable-object flaw found and fixed in
# resource_budget_manifest.py - comparing a value against itself can
# never detect drift). This is checker.py's own, separately-declared
# statement of what the options SHOULD be; a real divergence from
# builder.py's actual constant is a genuine finding this check exists to
# surface, not a false alarm to suppress by re-importing the same object.
_EXPECTED_REQUESTED_OPTIONS = {
    "temperature": 0.2, "top_p": 1.0, "top_k": 0, "repeat_penalty": 1.0,
    "context_cap_tokens": 8192,
}


@dataclass
class Violation:
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


def _all_convention_tokens(world_map: "dict[WorldKey, MicroWorldSpec]") -> "set[str]":
    return {w.convention_token for w in world_map.values()}


def check_construction_records(ledger: Ledger, world_map: "dict[WorldKey, MicroWorldSpec]") -> "list[Violation]":
    violations: "list[Violation]" = []
    all_tokens = _all_convention_tokens(world_map)

    for call_id, rec in ledger.construction_calls.items():
        # Every construction call must be exactly one attempt unless the
        # experiment plan explicitly declares otherwise (this mission's
        # plan never does) - anomaly #3/#4.
        if rec.construction_attempt_index != 0:
            violations.append(Violation("EXTRA_CONSTRUCTION_ATTEMPT",
                f"{call_id}: attempt_index={rec.construction_attempt_index} (>0 without a declared multi-attempt policy)"))
        if rec.semantic_feedback_exposure:
            violations.append(Violation("SEMANTIC_FEEDBACK_EXPOSURE",
                f"{call_id}: construction call has semantic_feedback_exposure=True (forbidden per §3: no critique/retry/best-of/teaching-based promotion)"))

        # Generation-options drift (anomaly #17): a request/effective
        # mismatch means the actual call did not honor what was asked for
        # - e.g. a silently-changed temperature/model option - and must
        # never be trusted as "what we think we ran."
        if rec.requested_options != rec.effective_options:
            violations.append(Violation("OPTIONS_DRIFT",
                f"{call_id}: requested_options={rec.requested_options!r} != effective_options={rec.effective_options!r}"))
        # Coherent drift (confirmed finding #7): requested_options and
        # effective_options can be changed TOGETHER to the same new value,
        # which the check above cannot see since the two fields still
        # agree with each other. Compare BOTH against an independently
        # frozen expectation, not against each other.
        if rec.requested_options != _EXPECTED_REQUESTED_OPTIONS or rec.effective_options != _EXPECTED_REQUESTED_OPTIONS:
            violations.append(Violation("COHERENT_OPTIONS_DRIFT",
                f"{call_id}: requested_options={rec.requested_options!r} and/or effective_options={rec.effective_options!r} "
                f"diverge from the independently frozen expected policy {_EXPECTED_REQUESTED_OPTIONS!r} "
                f"(this fires even when requested_options == effective_options, closing the coherent-drift gap)"))

        if rec.arm == "Z":
            if not rec.experience_field_empty:
                violations.append(Violation("Z_EXPERIENCE_NOT_EMPTY", f"{call_id}: Z construction must have experience_field_empty=True"))
            if rec.teaching_input_hash != sha256_of(""):
                violations.append(Violation("Z_TEACHING_LEAK", f"{call_id}: Z's teaching_input_hash is not the empty-input hash - teaching data reached Z's constructor"))
            for tok in all_tokens:
                if tok in rec.artifact_text:
                    violations.append(Violation("Z_CONVENTION_LEAK", f"{call_id}: Z artifact contains convention token {tok!r} it should have no access to"))
        elif rec.arm in ("P", "E"):
            key = (rec.family_id, rec.world_id)
            world = world_map.get(key)
            if world is None:
                violations.append(Violation("UNKNOWN_WORLD_ASSIGNMENT", f"{call_id}: no ground-truth world found for {key}"))
                continue
            expected_teaching = "\n".join(f"applying {world.convention_token} -> {t['observed_result']}" for t in world.teaching_queries)
            if rec.arm == "P" and rec.teaching_input_hash != sha256_of(expected_teaching):
                violations.append(Violation("WRONG_TEACHING_WORLD", f"{call_id}: P's teaching_input_hash does not match its assigned world {key}'s real teaching pool"))
            # Cross-world/cross-family leak scan: the artifact must not
            # contain any OTHER world's convention token.
            for other_key, other_world in world_map.items():
                if other_key != key and other_world.convention_token in rec.artifact_text:
                    violations.append(Violation("CROSS_WORLD_CONTAMINATION",
                        f"{call_id}: {rec.arm} artifact for {key} contains convention token {other_world.convention_token!r} belonging to {other_key}"))
    return violations


def check_solver_records(ledger: Ledger, world_map: "dict[WorldKey, MicroWorldSpec]") -> "list[Violation]":
    violations: "list[Violation]" = []
    all_tokens = _all_convention_tokens(world_map)
    baseline_roles = {"system", "user"}

    for call_id, rec in ledger.solver_calls.items():
        # Generation-options drift (anomaly #17), same check as the
        # construction-call path above - a solver call is a generation
        # event too and must honor the same requested-vs-effective
        # invariant.
        if rec.requested_options != rec.effective_options:
            violations.append(Violation("OPTIONS_DRIFT",
                f"{call_id}: requested_options={rec.requested_options!r} != effective_options={rec.effective_options!r}"))
        if rec.requested_options != _EXPECTED_REQUESTED_OPTIONS or rec.effective_options != _EXPECTED_REQUESTED_OPTIONS:
            violations.append(Violation("COHERENT_OPTIONS_DRIFT",
                f"{call_id}: requested_options={rec.requested_options!r} and/or effective_options={rec.effective_options!r} "
                f"diverge from the independently frozen expected policy {_EXPECTED_REQUESTED_OPTIONS!r}"))

        # N: no acquired artifact, no construction call in lineage.
        if rec.arm == "N":
            if rec.memory_field_text != "":
                violations.append(Violation("N_NONEMPTY_MEMORY", f"{call_id}: N solver received non-empty memory: {rec.memory_field_text[:60]!r}"))
            if rec.parent_construction_call_id is not None:
                violations.append(Violation("N_HAS_CONSTRUCTION_PARENT", f"{call_id}: N solver call has a construction parent {rec.parent_construction_call_id!r}"))
            if rec.memory_artifact_id is not None:
                violations.append(Violation("N_HAS_MEMORY_ARTIFACT_ID", f"{call_id}: N solver call references a memory_artifact_id"))

        # Every non-N call must reference a real construction call whose
        # artifact_hash matches what the solver actually received - a
        # correct-looking hash pointing at the wrong lineage is still a
        # failure (adjudication §4).
        if rec.arm != "N":
            parent = ledger.construction_calls.get(rec.parent_construction_call_id or "")
            if parent is None:
                violations.append(Violation("MISSING_PARENT_CONSTRUCTION", f"{call_id}: {rec.arm} solver call has no resolvable parent construction record"))
            else:
                if parent.arm != rec.arm:
                    violations.append(Violation("WRONG_ARM_PARENT", f"{call_id}: solver arm={rec.arm} but parent construction arm={parent.arm}"))
                if parent.family_id != rec.family_id:
                    violations.append(Violation("WRONG_FAMILY_PARENT", f"{call_id}: solver family={rec.family_id} but parent family={parent.family_id}"))
                if parent.arm in ("P",) and parent.world_id != rec.world_id:
                    # P is genuinely world-specific; its parent's world must equal the solver's scored world.
                    violations.append(Violation("WRONG_WORLD_PARENT", f"{call_id}: P solver scored against world={rec.world_id} but parent constructed for world={parent.world_id}"))
                if sha256_of(parent.artifact_text) != parent.artifact_hash:
                    violations.append(Violation("STALE_OR_CHANGED_ARTIFACT", f"{call_id}: parent construction {parent.call_id}'s recorded artifact_hash does not match a fresh hash of its own artifact_text"))
                if rec.memory_field_text != parent.artifact_text:
                    violations.append(Violation("MEMORY_MISMATCH", f"{call_id}: solver's memory_field_text does not equal its parent construction's artifact_text (cross-arm/cross-lineage read or corruption)"))

        # Actual-path checks: council/synthesis/tool-list must be absent
        # for this standalone single-call solver design (adjudication §4).
        if rec.council_entry:
            violations.append(Violation("UNEXPECTED_COUNCIL_ENTRY", f"{call_id}: council_entry=True"))
        if rec.synthesis_routing:
            violations.append(Violation("UNEXPECTED_SYNTHESIS_ROUTING", f"{call_id}: synthesis_routing=True"))
        if rec.tool_list_injected:
            violations.append(Violation("UNEXPECTED_TOOL_LIST", f"{call_id}: tool_list_injected=True"))
        if rec.model_tool_definitions:
            violations.append(Violation("UNEXPECTED_TOOL_DEFINITIONS", f"{call_id}: model_tool_definitions is non-empty: {rec.model_tool_definitions!r}"))

        # Hidden system content: every system-role message must be
        # exactly the canonical baseline instruction - no extra injected
        # lines (anomaly #14).
        from .builder import SYSTEM_INSTRUCTION
        system_msgs = [m["content"] for m in rec.ordered_messages if m.get("role") == "system"]
        if system_msgs != [SYSTEM_INSTRUCTION]:
            violations.append(Violation("HIDDEN_SYSTEM_CONTENT", f"{call_id}: system messages {system_msgs!r} != canonical baseline"))
        if any(m.get("role") not in baseline_roles for m in rec.ordered_messages):
            violations.append(Violation("UNEXPECTED_MESSAGE_ROLE", f"{call_id}: message roles outside {baseline_roles}"))

        # Convention leakage through task ID / metadata (never through prompts/labels).
        for tok in all_tokens:
            if tok in rec.query_id or tok in rec.family_id or tok in rec.world_id:
                violations.append(Violation("CONVENTION_LEAKED_VIA_ID", f"{call_id}: convention token {tok!r} appears in an id field"))

        # Convention leakage through the ACTUAL RECORDED MESSAGE CONTENT
        # (confirmed finding #6): the check above only ever scanned id
        # fields, never the ordered_messages payload a model would
        # actually see - a token appended directly onto the recorded user
        # message content passed undetected. This is the "gateway-
        # observed payload" validation the mission requires (checker.py's
        # own module docstring), applied to message content specifically,
        # not just metadata fields.
        full_message_text = "\n".join(m.get("content", "") for m in rec.ordered_messages)
        if rec.arm in ("N", "Z"):
            # N and Z must see NO convention token at all, from any world.
            for tok in all_tokens:
                if tok in full_message_text:
                    violations.append(Violation("CONVENTION_LEAKED_VIA_MESSAGE_CONTENT",
                        f"{call_id}: {rec.arm} solver's recorded message content contains convention token {tok!r} "
                        f"(arm must receive no acquired-convention information at all)"))
        elif rec.arm in ("P", "E"):
            key = (rec.family_id, rec.world_id)
            for other_key, other_world in world_map.items():
                if other_key != key and other_world.convention_token in full_message_text:
                    violations.append(Violation("CROSS_WORLD_MESSAGE_CONTAMINATION",
                        f"{call_id}: {rec.arm} solver for {key} has recorded message content containing "
                        f"convention token {other_world.convention_token!r} belonging to {other_key}"))

        # Declared action vs actually-dispatched entrypoint.
        if rec.declared_action != rec.dispatched_entrypoint:
            violations.append(Violation("DECLARED_DISPATCH_MISMATCH",
                f"{call_id}: declared_action={rec.declared_action.value} but dispatched_entrypoint={rec.dispatched_entrypoint.value}"))
        if rec.declared_action == Action.UNKNOWN or rec.dispatched_entrypoint == Action.UNKNOWN:
            # Not itself a violation (UNKNOWN is a legitimate outcome, per
            # mission §12: "Do not measure applicability from free-text
            # self-report" implies malformed output IS possible) - but is
            # tracked so it's never silently coerced elsewhere.
            pass
    return violations


def check_oracle_references(ledger: Ledger) -> "list[Violation]":
    """§10 accounting: Z/N-arm related-query oracle references may share
    a generation_id (reuse); P/E must never share one (they are freshly
    solved per world). An UNKNOWN oracle result must never silently
    become PASS/FAIL anywhere downstream (checked via detail-string
    presence, since this mock has no separate downstream summarizer -
    the anomaly test for #11 constructs a record that violates this
    directly).

    Also enforces referential integrity (confirmed finding #5): every
    OracleReference.generation_id must resolve to a real, existing
    generation recorded in ledger.solver_calls - a fabricated or
    orphaned generation_id is a failure, not a silently-accepted
    reference."""
    violations: "list[Violation]" = []
    real_generation_ids = ledger.distinct_generation_ids()
    gen_to_arms: "dict[str, set]" = {}
    for rec in ledger.solver_calls.values():
        gen_to_arms.setdefault(rec.generation_id, set()).add(rec.arm)
    for gen_id, arms in gen_to_arms.items():
        if len(arms) > 1:
            violations.append(Violation("CROSS_ARM_GENERATION_SHARING", f"generation {gen_id} shared across arms {arms} - each generation must belong to exactly one arm"))
        if ("P" in arms or "E" in arms):
            refs = [r for r in ledger.oracle_references.values() if r.generation_id == gen_id]
            if len(refs) > 1:
                violations.append(Violation("P_E_GENERATION_REUSED", f"generation {gen_id} (arm {arms}) has {len(refs)} oracle references - P/E must be freshly solved per world, never reused"))

    for ref_id, ref in ledger.oracle_references.items():
        if ref.generation_id not in real_generation_ids:
            violations.append(Violation("ORPHANED_ORACLE_REFERENCE",
                f"{ref_id}: references generation_id={ref.generation_id!r} which does not exist in "
                f"ledger.solver_calls - fabricated or orphaned generation reference"))
    return violations


def check_no_duplicate_solves_per_slot(ledger: Ledger) -> "list[Violation]":
    """Found during this mission's own hostile requalification (a NEW
    attack, structurally distinct from any of Codex's original 8
    findings, not a point-patch for a planted example): an undeclared
    second solve for the same logical slot - a fresh, independent
    generation_id with its own single, internally-consistent oracle
    reference - previously produced ZERO violations, because every
    existing check operates per-generation-id, and a genuinely NEW
    generation_id is (correctly) never flagged as reused by itself.

    This generalizes to the broader class: mission §3 forbids retry/
    critique/best-of-N,  which means every logical "slot" - the thing a
    solver was actually asked to answer - must be backed by EXACTLY ONE
    real generation_id, never two independently-generated ones, even if
    each individually looks like ordinary correct behavior.

    P/E are genuinely world-specific (adjudication: a fresh solve per
    world), so their slot key includes world_id. Z/N are genuinely
    REUSED across both paired worlds by design (one generation scored
    against two worlds via two oracle references - the fix for the
    272-vs-240 finding depends on this), so their slot key is
    family-level (no world_id) - multiple ROWS sharing one generation_id
    is correct for Z/N; multiple DISTINCT generation_ids for the same
    (family, arm, query_id) is not."""
    violations: "list[Violation]" = []
    slot_to_generations: "dict[tuple, set]" = {}
    for rec in ledger.solver_calls.values():
        if rec.arm in ("P", "E"):
            slot = (rec.family_id, rec.world_id, rec.arm, rec.query_id)
        else:  # Z, N - genuinely family-level, reused across both worlds
            slot = (rec.family_id, None, rec.arm, rec.query_id)
        slot_to_generations.setdefault(slot, set()).add(rec.generation_id)

    for slot, gen_ids in slot_to_generations.items():
        if len(gen_ids) > 1:
            violations.append(Violation("UNDECLARED_DUPLICATE_SOLVE",
                f"slot {slot} was independently generated {len(gen_ids)} times ({sorted(gen_ids)}) - "
                f"an undeclared retry/best-of/duplicate solve (forbidden per mission §3), even though "
                f"each individual generation is otherwise well-formed"))
    return violations


def check_no_evaluation_leakage(ledger: Ledger, world_map: "dict[WorldKey, MicroWorldSpec]") -> "list[Violation]":
    """No constructor input may contain a withheld expected_answer or
    oracle-only content (adjudication §4: "No constructor receives
    withheld queries, expected answers, test feedback")."""
    violations: "list[Violation]" = []
    for call_id, rec in ledger.construction_calls.items():
        for world in world_map.values():
            for q in world.related_queries:
                if q["expected_answer"] in rec.artifact_text:
                    violations.append(Violation("EXPECTED_ANSWER_LEAKED_TO_CONSTRUCTOR",
                        f"{call_id}: constructor artifact contains withheld expected_answer {q['expected_answer']!r}"))
    return violations


def check_assignment_completeness(ledger: Ledger, expected_slots: "list[tuple[str, str, str, str]]") -> "list[Violation]":
    """expected_slots: list of (family_id, world_id, arm, query_id) that
    MUST have at least one recorded oracle reference. Missing coverage is
    preserved as an incomplete run, never silently shrinking the
    denominator (adjudication §8: 'Preserve assignment; close is
    incomplete, not a smaller denominator').

    FIXED (confirmed finding #4): the original version only checked
    ledger.solver_calls for slot presence - meaning a slot with a real
    solver call but ZERO surviving oracle references (e.g. every scoring
    outcome deleted after the fact) was reported as "present" regardless.
    Deleting the entire oracle_references dict produced zero violations
    under the old logic. This version requires BOTH a solver call AND at
    least one oracle reference that actually resolves back to that exact
    slot (joined through generation_id -> solver_call, matching the same
    referential-integrity discipline as check_oracle_references)."""
    violations: "list[Violation]" = []
    gen_id_to_slot: "dict[str, tuple]" = {
        r.generation_id: (r.family_id, r.world_id, r.arm, r.query_id) for r in ledger.solver_calls.values()
    }
    slots_with_solver_call = set(gen_id_to_slot.values())
    slots_with_real_oracle_reference: "set[tuple]" = set()
    for ref in ledger.oracle_references.values():
        slot = gen_id_to_slot.get(ref.generation_id)
        if slot is not None and slot[0] == ref.family_id and slot[1] == ref.scored_against_world_id and slot[3] == ref.query_id:
            slots_with_real_oracle_reference.add(slot)

    for slot in expected_slots:
        if slot not in slots_with_solver_call:
            violations.append(Violation("MISSING_ASSIGNED_SLOT", f"expected slot {slot} has no recorded solver call"))
        elif slot not in slots_with_real_oracle_reference:
            violations.append(Violation("MISSING_ORACLE_RESULT",
                f"expected slot {slot} has a solver call but NO surviving oracle reference that resolves back to it "
                f"(scoring outcome missing, deleted, or pointing at the wrong slot)"))
    return violations


def check_every_solved_slot_has_oracle_result(ledger: Ledger) -> "list[Violation]":
    """UNCONDITIONAL half of finding #4's fix - runs with no external
    expected_slots argument, so it can never be silently skipped by a
    caller that doesn't supply one (the original confirmed repro called
    check_ledger(ledger, world_map) with no expected_slots at all).
    Requires only internal consistency: every slot that has a recorded
    solver call must have at least one oracle reference that actually
    resolves back to it. This catches "an outcome was deleted/never
    recorded for an attempted slot" without needing any external
    declaration of what SHOULD have been attempted - that broader check
    remains check_assignment_completeness() below, for when a caller does
    have an external expected-slot list."""
    violations: "list[Violation]" = []
    gen_id_to_slot: "dict[str, tuple]" = {
        r.generation_id: (r.family_id, r.world_id, r.arm, r.query_id) for r in ledger.solver_calls.values()
    }
    resolved_slots: "set[tuple]" = set()
    for ref in ledger.oracle_references.values():
        slot = gen_id_to_slot.get(ref.generation_id)
        if slot is not None and slot[0] == ref.family_id and slot[1] == ref.scored_against_world_id and slot[3] == ref.query_id:
            resolved_slots.add(slot)
    for slot in gen_id_to_slot.values():
        if slot not in resolved_slots:
            violations.append(Violation("MISSING_ORACLE_RESULT",
                f"slot {slot} has a recorded solver call but no surviving oracle reference resolves back to it"))
    return violations


def check_ledger(ledger: Ledger, world_map: "dict[WorldKey, MicroWorldSpec]",
                  expected_slots: "list[tuple[str, str, str, str]] | None" = None) -> "list[Violation]":
    """Runs every independent invariant check and returns the flat
    violation list. Also populates ledger.condition_validity per-slot
    (pass/fail) for reporting."""
    violations: "list[Violation]" = []
    violations += check_construction_records(ledger, world_map)
    violations += check_solver_records(ledger, world_map)
    violations += check_oracle_references(ledger)
    violations += check_no_evaluation_leakage(ledger, world_map)
    violations += check_every_solved_slot_has_oracle_result(ledger)
    violations += check_no_duplicate_solves_per_slot(ledger)
    if expected_slots is not None:
        violations += check_assignment_completeness(ledger, expected_slots)
    return violations
