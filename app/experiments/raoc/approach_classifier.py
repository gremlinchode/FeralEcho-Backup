"""
Pre-specified, deliberately coarse AST-based approach classifier
(protocol §10, §13.1). Distinguishes "uses recursion" from "uses an
explicit loop" as the primary approach axis for this experiment — chosen
because it's the example already named in the protocol document and
because Tier-4's real task pool contains genuine, real historical
candidates on both sides of this exact split (confirmed in
task_pairs.py).

Deliberately NOT a general code-similarity or intent classifier — a
structural, mechanical check only, disclosed as coarse in the protocol's
own adversarial-analysis section (§13.1: "a real, genuine shift in
strategy that doesn't happen to match the pre-specified AST pattern
gets missed entirely"). This module does not try to fix that; it
implements the check as specified, honestly, not as something smarter.
"""
from __future__ import annotations

import ast

from app.experiments.raoc.schema import Approach


def _defined_function_names(tree: ast.AST) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _calls_any_of(node: ast.AST, names: set[str]) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in names:
            return True
    return False


_COMPREHENSION_NODES = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def classify_approach(code: str) -> Approach:
    """
    RECURSIVE: at least one defined function contains a call to itself
    (direct recursion only — mutual recursion between two functions is a
    real, known limitation, not detected, disclosed rather than silently
    claimed as covered). Checked first — recursion takes priority if a
    candidate happens to combine it with a loop or comprehension, rather
    than silently miscounting a mixed candidate as purely iterative.

    ITERATIVE: contains a top-level or nested For/While/AsyncFor loop,
    OR a list/set/dict comprehension or generator expression (broadened
    2026-09-05 — a real, common Python idiom for iteration, e.g.
    `all(x in y for x in z)`, that a statement-level-only loop check
    misses entirely; confirmed against real Tier-4 data, see schema.py's
    Approach docstring for the measured before/after).

    NO_EXPLICIT_CONTROL_FLOW: the code parses and defines at least one
    real function or class, but uses none of the above (e.g. a solution
    expressed via slicing or built-in composition alone) — a real,
    distinct third approach, not an ambiguous case, and never coerced
    into RECURSIVE or ITERATIVE.

    UNKNOWN: the code doesn't parse, or parses but defines no real
    function or class at all (e.g. a fully commented-out response, or a
    genuinely empty candidate) — there is no approach to classify here,
    honestly reported as such rather than guessed at.

    NO_EXPLICIT_CONTROL_FLOW and UNKNOWN are both real, expected, and
    NEVER-discarded outcomes (protocol §10) — each is its own bucket in
    analysis, never folded into RECURSIVE or ITERATIVE.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return Approach.UNKNOWN

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _calls_any_of(node, {node.name}):
                return Approach.RECURSIVE

    has_loop = any(isinstance(node, (ast.For, ast.While, ast.AsyncFor)) for node in ast.walk(tree))
    has_comprehension = any(isinstance(node, _COMPREHENSION_NODES) for node in ast.walk(tree))
    if has_loop or has_comprehension:
        return Approach.ITERATIVE

    has_real_definition = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        for node in ast.walk(tree)
    )
    if has_real_definition:
        return Approach.NO_EXPLICIT_CONTROL_FLOW

    return Approach.UNKNOWN
