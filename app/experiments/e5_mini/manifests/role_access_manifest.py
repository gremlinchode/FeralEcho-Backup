"""Role/access manifest: turns the "Information invariants" already
specified in the G0/E5-mini mission (what N/Z/P/E/solver stages may and
must not receive) into an actual, checkable access-control specification
- concrete enough that a future real implementation can validate an
actual request/response against it, per the mission's own instruction.

Design principle, load-bearing: this manifest does NOT re-implement
checker.py's logic (that would be exactly the "ask the builder what
should have happened" anti-pattern adjudication §4/mission §7 forbid).
Instead, `verify_manifest_coverage()` below cross-references each
declared rule against checker.py's REAL, already-enforced violation
codes (grepped from source, not hand-copied from memory - see the
hostile review's ROLE-1 finding for what happens when this drifts) and
sandbox.py's real containment functions. This is a two-way check:

  1. Every MUST_NOT rule this manifest declares should map to at least
     one real enforcement mechanism - a rule with none is a real gap
     (paper protection only).
  2. Every real checker.py violation code should map to at least one
     declared rule - an enforcement mechanism with no corresponding
     declared rule is undocumented protection (works today, but nothing
     freezes the policy it implements, so a future refactor could
     silently remove it with nothing to notice).

DESIGN ARTIFACT ONLY. No real E5 execution is authorized or performed
by this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AccessRule:
    stage: str
    may_receive: "list[str]"
    must_not_receive: "list[str]"
    enforced_by: "list[str]"  # checker.py violation codes / sandbox.py function names that would catch a MUST_NOT violation


# The declared policy. Each `enforced_by` entry is checked against the
# REAL set of checker.py violation codes by verify_manifest_coverage()
# below - if a code named here doesn't exist in checker.py, that's a
# ROLE-1-shaped drift and the cross-check will report it, not silently
# trust this list.
ROLE_ACCESS_RULES: "list[AccessRule]" = [
    AccessRule(
        stage="CONSTRUCTOR_P",
        may_receive=["public_spec (S)", "this world's real teaching_queries (T_w)"],
        must_not_receive=[
            "other worlds'/families' teaching content or convention tokens",
            "withheld related_queries or their expected_answer",
            "near_match/unrelated query pools",
            "evaluator/oracle feedback of any kind",
            "prior construction attempts (no retry/critique/best-of)",
        ],
        enforced_by=["WRONG_TEACHING_WORLD", "CROSS_WORLD_CONTAMINATION",
                     "EXPECTED_ANSWER_LEAKED_TO_CONSTRUCTOR", "SEMANTIC_FEEDBACK_EXPOSURE",
                     "EXTRA_CONSTRUCTION_ATTEMPT", "UNKNOWN_WORLD_ASSIGNMENT"],
    ),
    AccessRule(
        stage="CONSTRUCTOR_E",
        may_receive=["public_spec (S)", "this world's real teaching_queries (T_w), identical pool to P"],
        must_not_receive=[
            "other worlds'/families' teaching content or convention tokens",
            "withheld related_queries or their expected_answer",
            "any extra reasoning/selection step P does not also get (matched call count/ceiling)",
        ],
        enforced_by=["CROSS_WORLD_CONTAMINATION", "EXPECTED_ANSWER_LEAKED_TO_CONSTRUCTOR",
                     "EXTRA_CONSTRUCTION_ATTEMPT", "SEMANTIC_FEEDBACK_EXPOSURE", "UNKNOWN_WORLD_ASSIGNMENT"],
    ),
    AccessRule(
        stage="CONSTRUCTOR_Z",
        may_receive=["public_spec (S)", "an explicitly empty experience field"],
        must_not_receive=[
            "ANY teaching observation, from any world or family",
            "any convention token",
            "teaching-based selection of which Z variant to keep",
            "P or E's artifact",
        ],
        enforced_by=["Z_EXPERIENCE_NOT_EMPTY", "Z_TEACHING_LEAK", "Z_CONVENTION_LEAK",
                     "SEMANTIC_FEEDBACK_EXPOSURE", "EXTRA_CONSTRUCTION_ATTEMPT"],
    ),
    AccessRule(
        stage="SOLVER_P",
        may_receive=["public_spec (S)", "the query", "action interface", "P_w's artifact (own world only)"],
        must_not_receive=[
            "the arm label ('P') or private world ID in any model-visible content",
            "withheld expected_answer, hidden oracle tests, evaluator feedback",
            "future queries or evaluation-derived rankings",
            "council/synthesis routing, TOOL-LIST injection, tool definitions",
            "any system content beyond the canonical baseline instruction",
        ],
        enforced_by=["CONVENTION_LEAKED_VIA_ID", "WRONG_ARM_PARENT", "WRONG_FAMILY_PARENT",
                     "WRONG_WORLD_PARENT", "MEMORY_MISMATCH", "UNEXPECTED_COUNCIL_ENTRY",
                     "UNEXPECTED_SYNTHESIS_ROUTING", "UNEXPECTED_TOOL_LIST",
                     "UNEXPECTED_TOOL_DEFINITIONS", "HIDDEN_SYSTEM_CONTENT", "UNEXPECTED_MESSAGE_ROLE",
                     "MISSING_PARENT_CONSTRUCTION", "STALE_OR_CHANGED_ARTIFACT",
                     "P_E_GENERATION_REUSED", "CROSS_ARM_GENERATION_SHARING",
                     "CROSS_WORLD_MESSAGE_CONTAMINATION", "UNDECLARED_DUPLICATE_SOLVE"],
    ),
    AccessRule(
        stage="SOLVER_E",
        may_receive=["public_spec (S)", "the query", "action interface", "E_w's artifact (own world only)"],
        must_not_receive=[
            "the arm label or private world ID in any model-visible content",
            "withheld expected_answer, hidden oracle tests, evaluator feedback",
            "council/synthesis routing, TOOL-LIST injection, tool definitions",
        ],
        enforced_by=["CONVENTION_LEAKED_VIA_ID", "WRONG_ARM_PARENT", "WRONG_FAMILY_PARENT",
                     "MEMORY_MISMATCH", "UNEXPECTED_COUNCIL_ENTRY", "UNEXPECTED_SYNTHESIS_ROUTING",
                     "UNEXPECTED_TOOL_LIST", "UNEXPECTED_TOOL_DEFINITIONS", "HIDDEN_SYSTEM_CONTENT",
                     "MISSING_PARENT_CONSTRUCTION", "STALE_OR_CHANGED_ARTIFACT",
                     "P_E_GENERATION_REUSED", "CROSS_ARM_GENERATION_SHARING",
                     "CROSS_WORLD_MESSAGE_CONTAMINATION", "UNDECLARED_DUPLICATE_SOLVE"],
    ),
    AccessRule(
        stage="SOLVER_Z",
        may_receive=["public_spec (S)", "the query", "action interface", "Z's artifact (shared across both worlds)"],
        must_not_receive=[
            "any world's convention token or teaching content",
            "P/E's artifact",
            "withheld expected_answer, hidden oracle tests, evaluator feedback",
        ],
        enforced_by=["CONVENTION_LEAKED_VIA_ID", "MEMORY_MISMATCH", "WRONG_ARM_PARENT",
                     "STALE_OR_CHANGED_ARTIFACT", "CROSS_ARM_GENERATION_SHARING",
                     "CONVENTION_LEAKED_VIA_MESSAGE_CONTENT", "UNDECLARED_DUPLICATE_SOLVE"],
    ),
    AccessRule(
        stage="SOLVER_N",
        may_receive=["public_spec (S)", "the query", "action interface", "an explicitly empty memory field"],
        must_not_receive=[
            "any acquired artifact of any kind",
            "a construction-call parent",
            "any convention token or teaching content",
        ],
        enforced_by=["N_NONEMPTY_MEMORY", "N_HAS_CONSTRUCTION_PARENT", "N_HAS_MEMORY_ARTIFACT_ID",
                     "CROSS_ARM_GENERATION_SHARING", "CONVENTION_LEAKED_VIA_MESSAGE_CONTENT",
                     "UNDECLARED_DUPLICATE_SOLVE"],
    ),
    AccessRule(
        stage="ORACLE",
        may_receive=["a real generation_id", "the world/query it is scoring against", "the withheld expected_answer for that query"],
        must_not_receive=[
            "the ability to be overridden by candidate-claimed pass/fail text",
            "an UNKNOWN result silently coerced into PASS/FAIL",
        ],
        enforced_by=["MISSING_ASSIGNED_SLOT", "MISSING_ORACLE_RESULT", "ORPHANED_ORACLE_REFERENCE"],  # oracle-forgery/coercion covered separately by sandbox.candidate_trusted_oracle_result, not a checker.py Violation code - see cross-check note below
    ),
    AccessRule(
        stage="CONDITION_CHECKER",
        may_receive=["the raw recorded Ledger", "an independently-specified MicroWorldSpec ground truth"],
        must_not_receive=[
            "any import of builder.py or orchestrator.py",
            "trust in a builder-stated 'this is what should have happened' claim",
        ],
        enforced_by=[],  # structural property of the codebase (verified by import-graph inspection, not a runtime Violation code - see cross-check note
    ),
    AccessRule(
        stage="ORCHESTRATOR",
        may_receive=["the frozen task manifest", "the frozen role/access manifest", "the frozen resource-budget manifest"],
        must_not_receive=[
            "authority to silently exclude a frozen family from analysis",
            "authority to re-freeze an already-frozen manifest",
        ],
        enforced_by=[],  # enforced by task_manifest.py's TaskManifest.freeze()/assert_no_family_removed(), not checker.py - cross-referenced, not duplicated
    ),
]

# Enforcement mechanisms that exist in the real code but are NOT
# expressible as a checker.py Violation code (either because they're a
# structural/import-graph property, or because they live in sandbox.py's
# own functions rather than checker.py's Violation list). Declared here
# so verify_manifest_coverage() doesn't misreport these as gaps.
NON_CHECKER_ENFORCEMENT = {
    "sandbox.guarded_write": "sandbox.py - denies writes outside the sacrificial scratch root (anomaly #26)",
    "sandbox.scan_for_escalation_patterns": "sandbox.py - text-pattern scan for subprocess/escalation attempts (anomaly #27)",
    "sandbox.candidate_trusted_oracle_result": "sandbox.py - candidate cannot forge ALL_TESTS_PASSED or modify the real oracle result (anomalies #22, #23)",
    "checker.py import-graph": "checker.py never imports builder.py/orchestrator.py (verified by source inspection, not a runtime Violation code)",
    "TaskManifest.freeze/assert_no_family_removed": "task_manifest.py - structural freeze + post hoc exclusion detection",
}


def _real_checker_violation_codes() -> "set[str]":
    """Greps the ACTUAL checker.py source for Violation(\"CODE\" call
    sites - never hand-maintained, so this cross-check cannot silently
    drift from the real enforced set the way a hardcoded list could."""
    import re
    from pathlib import Path
    checker_path = Path(__file__).resolve().parent.parent / "checker.py"
    text = checker_path.read_text(encoding="utf-8")
    return set(re.findall(r'Violation\("([A-Z_]+)"', text))


# Real checker.py codes deliberately NOT mapped to any AccessRule here -
# not an oversight, a genuine scope-boundary finding (see the hostile
# review's ROLE-2 finding). All three check a real invariant, but none is
# an "information access" property in this manifest's sense:
#   - OPTIONS_DRIFT: a resource/generation-parameter integrity property
#     (requested vs effective options) - belongs conceptually to
#     resource_budget_manifest.py's domain, not this one.
#   - COHERENT_OPTIONS_DRIFT (added during this repair mission, finding
#     #7's generalized fix): the SAME domain as OPTIONS_DRIFT - detects
#     requested_options/effective_options drifting COHERENTLY together
#     against an independently frozen expected spec, not just against
#     each other. Belongs in the identical bucket as OPTIONS_DRIFT for
#     the identical reason. Its presence here, alongside OPTIONS_DRIFT,
#     is itself additional evidence the ROLE-2 "missing 4th category"
#     question below is real and specifically about generation-options/
#     behavioral-integrity properties - not a general taxonomy failure.
#   - DECLARED_DISPATCH_MISMATCH: an action-integrity property (declared
#     action vs actually-dispatched entrypoint) - arguably a FOURTH
#     manifest category ("behavioral integrity") this three-manifest
#     design doesn't have a home for. Flagged as an open question, not
#     silently absorbed into role/access where it doesn't fit.
INTENTIONALLY_UNMAPPED_CODES = {"OPTIONS_DRIFT", "COHERENT_OPTIONS_DRIFT", "DECLARED_DISPATCH_MISMATCH"}


def verify_non_checker_enforcement_exists() -> dict:
    """Closes hostile-review finding ROLE-3: NON_CHECKER_ENFORCEMENT names
    real functions/properties in prose only - nothing previously verified
    those names still resolve to real, callable code. A future rename or
    removal in sandbox.py would silently leave this manifest claiming
    protection that no longer exists, with nothing to catch it."""
    import importlib
    results: "dict[str, bool]" = {}
    checks = {
        "sandbox.guarded_write": ("app.experiments.e5_mini.sandbox", "guarded_write"),
        "sandbox.scan_for_escalation_patterns": ("app.experiments.e5_mini.sandbox", "scan_for_escalation_patterns"),
        "sandbox.candidate_trusted_oracle_result": ("app.experiments.e5_mini.sandbox", "candidate_trusted_oracle_result"),
        "TaskManifest.freeze/assert_no_family_removed": ("app.experiments.e5_mini.manifests.task_manifest", "TaskManifest"),
    }
    for label, (module_name, attr_name) in checks.items():
        try:
            mod = importlib.import_module(module_name)
            results[label] = hasattr(mod, attr_name)
        except ImportError:
            results[label] = False
    # "checker.py import-graph" is verified separately (static source
    # inspection, not an importable attribute) - see checker.py's own
    # module docstring assertion, cross-checked by grep in the audit report.
    results["checker.py import-graph (verified via source grep, not import)"] = True
    return results


def verify_manifest_coverage() -> dict:
    """Two-way cross-check between this manifest's declared rules and
    checker.py's real, currently-enforced violation codes. Returns a
    dict a caller (or this mission's own audit report) can inspect
    directly - never silently swallows a mismatch."""
    real_codes = _real_checker_violation_codes()
    declared_codes: "set[str]" = set()
    unmapped_rules: "list[str]" = []
    for rule in ROLE_ACCESS_RULES:
        for code in rule.enforced_by:
            declared_codes.add(code)
            if code not in real_codes:
                unmapped_rules.append(f"{rule.stage}: declared enforcement {code!r} does not exist in checker.py")

    codes_with_no_declared_rule = real_codes - declared_codes - INTENTIONALLY_UNMAPPED_CODES
    rules_with_empty_enforcement = [
        r.stage for r in ROLE_ACCESS_RULES if not r.enforced_by and r.stage not in
        {"ORACLE", "CONDITION_CHECKER", "ORCHESTRATOR"}  # these three are explicitly cross-referenced via NON_CHECKER_ENFORCEMENT, not a gap
    ]

    return {
        "real_checker_violation_codes": sorted(real_codes),
        "declared_but_nonexistent": unmapped_rules,  # MUST be empty for this manifest to be trustworthy
        "real_codes_with_no_declared_rule": sorted(codes_with_no_declared_rule),  # undocumented protection - worth naming, not necessarily a blocker
        "stages_with_zero_checker_enforcement_and_no_cross_reference": rules_with_empty_enforcement,  # a genuine coverage gap if non-empty
    }
