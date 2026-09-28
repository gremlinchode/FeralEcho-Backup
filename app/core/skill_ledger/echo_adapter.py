"""The ONE narrow integration point between real Echo code and the Verified Skill
Ledger (Phase 13 of the integration-readiness mission). Everything upstream
(app/core/echo_projects.py) and downstream (the real F1/F2 gates) is completely
unaware of and unaffected by this module's presence when VSL is disabled --
`consult_file()` degrades to a pure pass-through the instant `VSL_ENABLED` is not
`"true"`, restoring pre-VSL behavior exactly (Phase 14's own requirement).

Deliberately generalizes runtime.consult() (which operates on one named function) to
"try every top-level function defined in this file" -- a real generated file can
define several functions, and this codebase has no way to know in advance which one
(if any) a skill's precondition might match.
"""
from __future__ import annotations
import ast
from typing import Optional

from . import runtime


def _top_level_function_names(code: str) -> list:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def consult_file(code: str, task_id: str) -> dict:
    """Tries every top-level function name in `code` against every ACTIVE skill.
    Returns {"code": <possibly transformed>, "applications": [ConsultResult, ...]}
    -- `applications` includes EVERY consultation attempted (matched or not, shadow
    or active), for full observability, not just the ones that fired. If VSL is
    disabled, returns {"code": code, "applications": []} immediately -- zero
    matcher/AST work done, true pass-through.

    Each real consultation is also recorded via runtime.record_outcome() with
    verifier_strength="not_yet_verified" (the caller -- echo_projects.py -- has not
    run F1/F2 yet at the point this is called; a second, corrected record is
    expected from the caller once the real F1/F2 verdict is known -- see the call
    site in echo_projects.py for how the two records are distinguished).
    """
    if runtime.get_mode() == "disabled":
        return {"code": code, "applications": []}

    fn_names = _top_level_function_names(code)
    applications = []
    current_code = code
    for fn_name in fn_names:
        result = runtime.consult(current_code, fn_name)
        applications.append(result)
        runtime.record_outcome(task_id, result, current_code, verifier_result=None,
                                verifier_strength="not_yet_verified")
        if result.applied and result.proposed_code is not None:
            current_code = result.proposed_code

    return {"code": current_code, "applications": applications}


def record_final_verdict(task_id: str, applications: list, code_before: str,
                          code_after: "str | None", f1_passed: bool, f2_result: "dict | None") -> None:
    """Called by echo_projects.py once the real F1/F2 verdict is known, for every
    application that actually fired (result.applied == True) during consult_file()
    -- records the strongest verifier signal this integration point can currently
    produce ("f1_f2_safety_only": echo_projects.py has no correctness oracle of its
    own, only F1 static safety + F2 "does it run without crashing"). Explicitly NOT
    "full_oracle" -- evaluate_degradation() deliberately excludes this strength
    level from its own threshold math, since it cannot distinguish a genuine
    correctness regression from code that simply never exercises the patched path."""
    verifier_result = {"f1_passed": f1_passed,
                        "f2_passed": bool(f2_result and f2_result.get("passed"))}
    for result in applications:
        if result.applied:
            runtime.record_outcome(task_id, result, code_before, verifier_result,
                                    verifier_strength="f1_f2_safety_only", code_after=code_after)
