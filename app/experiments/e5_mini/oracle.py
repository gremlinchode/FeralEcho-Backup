"""Trusted deterministic oracle. Holds expected answers and correct
actions; NEVER exposes them to constructors or solvers (adjudication §4:
"No constructor receives withheld queries, expected answers, test
feedback or evaluation-derived rankings"). Scores a solver's actual
recorded response independently of whatever the response text itself
claims (anomaly #22: a candidate forging "ALL_TESTS_PASSED" must not be
trusted - this module recomputes the real answer from the world's own
expected_answer field, never parses a self-reported pass/fail out of the
response text).
"""
from __future__ import annotations

from .schema import Action, MicroWorldSpec, OracleReference, OracleResult, QueryKind


def score_related(world: MicroWorldSpec, query_id: str, response_text: str) -> "tuple[OracleResult, str]":
    match = next((q for q in world.related_queries if q["query_id"] == query_id), None)
    if match is None:
        return OracleResult.UNKNOWN, f"no expected-answer fixture for query_id {query_id!r} (infra defect, not a scientific failure)"
    if response_text == match["expected_answer"]:
        return OracleResult.PASS, "response matches expected_answer exactly"
    return OracleResult.FAIL, f"response {response_text!r} != expected {match['expected_answer']!r}"


def score_negative(world: MicroWorldSpec, query_id: str, declared_action: Action, kind: QueryKind) -> "tuple[OracleResult, str]":
    """Negative-control scoring (near_match/unrelated): correctness is
    about the ACTION taken, not response content (adjudication §5)."""
    pool = world.near_match_queries if kind == QueryKind.NEAR_MATCH else world.unrelated_queries
    match = next((q for q in pool if q["query_id"] == query_id), None)
    if match is None:
        return OracleResult.UNKNOWN, f"no fixture for query_id {query_id!r}"
    correct = match["correct_action"]
    if declared_action == correct:
        return OracleResult.PASS, f"declared action {declared_action.value} matches required {correct.value}"
    if declared_action == Action.FAMILY and correct != Action.FAMILY:
        return OracleResult.FAIL, f"operational false application: declared FAMILY where {correct.value} was required"
    return OracleResult.FAIL, f"declared {declared_action.value}, required {correct.value}"
