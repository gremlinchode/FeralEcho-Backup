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


def classify_approach(code: str) -> Approach:
    """
    RECURSIVE: at least one defined function contains a call to itself
    (direct recursion only — mutual recursion between two functions is a
    real, known limitation, not detected, disclosed rather than silently
    claimed as covered).

    ITERATIVE: contains a top-level or nested For/While loop, and is not
    already classified RECURSIVE (recursion takes priority if a
    candidate happens to do both — rare, but a real candidate combining
    both should not be silently miscounted as purely iterative).

    UNKNOWN: neither pattern found (e.g. a solution expressed via a
    single comprehension/generator/built-in with no explicit loop or
    recursion), or the code doesn't parse at all. UNKNOWN is a real,
    expected, and NEVER-discarded outcome (protocol §10) — it is
    reported as its own bucket in analysis, not folded into either side.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return Approach.UNKNOWN

    func_names = _defined_function_names(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _calls_any_of(node, {node.name}):
                return Approach.RECURSIVE

    has_loop = any(isinstance(node, (ast.For, ast.While, ast.AsyncFor)) for node in ast.walk(tree))
    if has_loop:
        return Approach.ITERATIVE

    return Approach.UNKNOWN
