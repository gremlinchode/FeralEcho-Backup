"""Ties builder.py (construction/solving) + oracle.py (trusted scoring)
into full mocked experiment runs.

SCOPE NOTE (honest, not a shortcut taken quietly): this orchestrator
implements the real P/E/Z/N construction cardinality from adjudication
§7.3/§7.5 (P: 1 construction per world; E: 1 per world; Z: 1 per family,
shared across both worlds; N: none) and the real one-generation-multiple-
oracle-references accounting from §7.5/§7.6/§10 (Z/N's related-query
generations are reused across both worlds' scoring, never re-generated).
It does NOT attempt to reproduce the frozen real pilot's exact declared
totals (80/80/40/40 solver calls, 320 scored rows) at full 4-family scale
by default - `run_mock_e5_mini()` below defaults to a smaller
`n_families` for speed, since this mission's own framing is "apparatus
validation," not execution of the real pilot (which remains NO-GO per
adjudication §13 regardless). The MECHANISM is identical at any scale;
`tests/test_e5_mini_g0.py` includes one run at the real n_families=4 to
report the actual resulting counts honestly rather than assume they match
the adjudication's illustrative arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass

from .builder import construct_arm, solve_query
from .ledger import Ledger
from .mock import SolverStrategy, CLEAN_STRATEGY, make_synthetic_families
from .oracle import score_negative, score_related
from .schema import Action, MicroWorldSpec, OracleReference, OracleResult, QueryKind


@dataclass
class ArmStrategies:
    """Which mock solving strategy each arm uses - lets the mocked
    end-to-end demo (qualify.py) produce P>E, P≈E, etc. on demand."""
    p: SolverStrategy = CLEAN_STRATEGY
    e: SolverStrategy = CLEAN_STRATEGY
    z: SolverStrategy = CLEAN_STRATEGY
    n: SolverStrategy = CLEAN_STRATEGY


def run_family(ledger: Ledger, world0: MicroWorldSpec, world1: MicroWorldSpec, strategies: ArmStrategies) -> None:
    """Runs P, E, Z, N for one base family (both paired micro-worlds)."""
    worlds = {world0.world_id: world0, world1.world_id: world1}
    family_id = world0.family_id

    # --- Construction ---------------------------------------------------
    p_construct = {w.world_id: construct_arm(ledger, "P", w, family_id) for w in (world0, world1)}
    e_construct = {w.world_id: construct_arm(ledger, "E", w, family_id) for w in (world0, world1)}
    z_construct = construct_arm(ledger, "Z", world0, family_id)  # one Z per family, world=None recorded internally

    # --- P, E: world-specific solving, 1:1 with oracle scoring ----------
    for arm, constructs, strategy in (("P", p_construct, strategies.p), ("E", e_construct, strategies.e)):
        for world_id, world in worlds.items():
            crec = constructs[world_id]
            memory_text = crec.artifact_text
            all_queries = (
                [(q["query_id"], q["query"], QueryKind.RELATED) for q in world.related_queries]
                + [(q["query_id"], q["query"], QueryKind.NEAR_MATCH) for q in world.near_match_queries]
                + [(q["query_id"], q["query"], QueryKind.UNRELATED) for q in world.unrelated_queries]
            )
            for query_id, query_text, kind in all_queries:
                rec, gen_id = solve_query(
                    ledger, arm, family_id, world_id, query_id, query_text, kind,
                    memory_artifact_id=crec.artifact_id, memory_text=memory_text, strategy=strategy,
                )
                _score_and_record(ledger, world, query_id, kind, rec, gen_id)

    # --- Z: family-level solving, related queries reused across both worlds ---
    _run_shared_arm(ledger, "Z", family_id, worlds, memory_text=z_construct.artifact_text,
                     memory_artifact_id=z_construct.artifact_id, strategy=strategies.z)

    # --- N: no construction, empty memory, same reuse shape as Z --------
    _run_shared_arm(ledger, "N", family_id, worlds, memory_text="", memory_artifact_id=None, strategy=strategies.n)


def _run_shared_arm(ledger: Ledger, arm: str, family_id: str, worlds: "dict[str, MicroWorldSpec]",
                     memory_text: str, memory_artifact_id, strategy: SolverStrategy) -> None:
    any_world = next(iter(worlds.values()))
    # Related queries: query bytes are world-shared (adjudication §7.1),
    # so ONE generation serves both worlds' scoring - this is the exact
    # mechanism §10/§7.5/§7.6 require and the anomaly-18 test attacks.
    for q in any_world.related_queries:
        rec = None
        gen_id = None
        for i, (world_id, world) in enumerate(worlds.items()):
            if i == 0:
                rec, gen_id = solve_query(
                    ledger, arm, family_id, world_id, q["query_id"], q["query"], QueryKind.RELATED,
                    memory_artifact_id=memory_artifact_id, memory_text=memory_text, strategy=strategy,
                )
            else:
                # Reuse: record a SECOND SolverCallRecord row (so both
                # world scorings are visible in the row table) but pass
                # reuse_generation_id so accounting.py can verify it's
                # the same generation, not a fresh one.
                rec, gen_id = solve_query(
                    ledger, arm, family_id, world_id, q["query_id"], q["query"], QueryKind.RELATED,
                    memory_artifact_id=memory_artifact_id, memory_text=memory_text, strategy=strategy,
                    reuse_generation_id=gen_id,
                )
            _score_and_record(ledger, world, q["query_id"], QueryKind.RELATED, rec, gen_id)

    # Negative queries (near_match/unrelated): correctness doesn't depend
    # on which world is asked, so score once per query, not per world.
    for kind, pool in ((QueryKind.NEAR_MATCH, any_world.near_match_queries), (QueryKind.UNRELATED, any_world.unrelated_queries)):
        for q in pool:
            world_id = any_world.world_id
            rec, gen_id = solve_query(
                ledger, arm, family_id, world_id, q["query_id"], q["query"], kind,
                memory_artifact_id=memory_artifact_id, memory_text=memory_text, strategy=strategy,
            )
            _score_and_record(ledger, any_world, q["query_id"], kind, rec, gen_id)


def _score_and_record(ledger: Ledger, world: MicroWorldSpec, query_id: str, kind: QueryKind, rec, generation_id: str) -> None:
    if kind == QueryKind.RELATED:
        result, detail = score_related(world, query_id, rec.response_text)
    else:
        result, detail = score_negative(world, query_id, rec.declared_action, kind)
    ref_id = ledger.next_id("oracleref")
    ledger.record_oracle_reference(OracleReference(
        reference_id=ref_id, generation_id=generation_id, family_id=world.family_id,
        scored_against_world_id=world.world_id, query_id=query_id,
        oracle_result=result, oracle_detail=detail,
    ))


def run_mock_e5_mini(n_families: int = 4, strategies: "ArmStrategies | None" = None) -> Ledger:
    """Runs the full mocked P/E/Z/N experiment across `n_families` base
    families. See module docstring for the honest scope note on why this
    defaults to real-scale (4) but is parameterizable - callers needing a
    fast smoke run may pass a smaller n_families."""
    strategies = strategies or ArmStrategies()
    ledger = Ledger()
    for world0, world1 in make_synthetic_families(n_families):
        run_family(ledger, world0, world1, strategies)
    return ledger
