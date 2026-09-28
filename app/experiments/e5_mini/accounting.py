"""§10 dependency/cost accounting: one generation -> multiple oracle
references (Z/N reuse) must never be miscounted as extra generations,
extra attempts, extra samples, or extra cost.
"""
from __future__ import annotations

from .ledger import Ledger


def reconcile(ledger: Ledger) -> dict:
    distinct_generations = ledger.distinct_generation_ids()
    gen_to_arm = {}
    for rec in ledger.solver_calls.values():
        gen_to_arm.setdefault(rec.generation_id, rec.arm)

    per_arm_generations: "dict[str, int]" = {}
    for gen_id, arm in gen_to_arm.items():
        per_arm_generations[arm] = per_arm_generations.get(arm, 0) + 1

    per_arm_rows: "dict[str, int]" = {}
    for rec in ledger.solver_calls.values():
        per_arm_rows[rec.arm] = per_arm_rows.get(rec.arm, 0) + 1

    # Cost counted once per generation, not once per row/reference.
    seen_for_cost = set()
    total_construction_cost = sum(r.cost_tokens_in + r.cost_tokens_out for r in ledger.construction_calls.values())
    total_solver_generation_cost = 0
    for rec in ledger.solver_calls.values():
        if rec.generation_id in seen_for_cost:
            continue
        seen_for_cost.add(rec.generation_id)
        total_solver_generation_cost += len(rec.memory_field_text) + len(rec.response_text)

    return {
        "distinct_generations_total": len(distinct_generations),
        "distinct_generations_per_arm": per_arm_generations,
        "solver_rows_total": len(ledger.solver_calls),
        "solver_rows_per_arm": per_arm_rows,
        "oracle_references_total": len(ledger.oracle_references),
        "construction_calls_total": len(ledger.construction_calls),
        "total_model_calls": len(ledger.construction_calls) + len(distinct_generations),
        "total_construction_cost_chars": total_construction_cost,
        "total_solver_generation_cost_chars": total_solver_generation_cost,
        "rows_minus_generations": len(ledger.solver_calls) - len(distinct_generations),
    }


def verify_execution_witness(ledger: Ledger, actual_solver_invocations: int) -> dict:
    """Cross-checks the ledger's own generation-id accounting against an
    INDEPENDENT execution-level signal (mock.get_solve_witness_count(),
    captured by the caller around a real run - deliberately not imported
    here, so this function's own correctness doesn't depend on trusting
    mock.py's bookkeeping either, only on being handed the count).

    This is the direct fix for the confirmed 272-vs-240 finding: with
    genuine reuse (builder.py's solve_query() fix), actual_solver_invocations
    must equal distinct_generations_total exactly - one real invocation
    per unique generation_id, reused rows contributing zero additional
    invocations. A mismatch in EITHER direction is a real defect:
      - actual > expected: something invoked the solver without the
        ledger's generation-id bookkeeping reflecting it (the original bug).
      - actual < expected: a generation_id was recorded with no matching
        real invocation at all (a different, also-serious defect - a
        fabricated or duplicated generation_id with no real backing call).
    """
    stats = reconcile(ledger)
    expected = stats["distinct_generations_total"]
    match = actual_solver_invocations == expected
    return {
        "expected_distinct_generations": expected,
        "actual_solver_invocations": actual_solver_invocations,
        "execution_matches_declaration": match,
        "detail": (
            "execution witness matches ledger's declared generation count"
            if match else
            f"MISMATCH: {actual_solver_invocations} real solver invocations occurred but the ledger "
            f"declares {expected} distinct generations - the ledger cannot be trusted to report how "
            f"many times the solver actually ran (this is the generalized form of the confirmed "
            f"272-vs-240 finding, not a point-patch for that exact number)"
        ),
    }
