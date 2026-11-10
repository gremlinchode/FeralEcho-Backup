"""Scoring rubric. Frozen before either official arm runs.

The external file check is the objective. The controller's success
string is not. Definitions in this file are not revised after the
official run.
"""

from voyager.suite_spec import MISSIONS

EXPECTED_IDS = [mission["id"] for mission in MISSIONS]

RECOVERY_IDS = ["M07", "M08", "M09", "M10"]
RESTART_IDS = ["M05", "M06", "M23"]
UNFAMILIAR_IDS = ["M19", "M20"]
BLOCK_IDS = ["M12", "M17", "M21", "M22"]
COMPOSITION_IDS = ["M25"]
TIGHT_HELDOUT_IDS = ["M14", "M15", "M16"]
POLICY_NON_REPEAT_ID = "M24"

REQUIRED_TAGS = [
    "uninterrupted",
    "restart",
    "missing_resource",
    "failed_operation",
    "conflicting",
    "bad_assumption",
    "human",
    "previous",
    "unfamiliar",
    "multi_dependent",
]

READING_RULES = [
    "completion_rate is external passes divided by 25. A success string is not a pass.",
    "M24 stays inside completion_rate. Refusing a repeated flaky read fails that file grade. The baseline may pass it by retrying. Report this as policy_non_repeat. Do not drop M24 from the rate.",
    "successful_recovery_rate counts only M07 M08 M09 M10, and only when the external check passed, an alternate was used, and the world log shows no repeated failed operation.",
    "recovery_after_restart counts only M05 M06 M23. A pass requires the external check, resumed_from_checkpoint, and two different launched process ids.",
    "blocked_when_should_block is the external abstain pass rate on M12 M17 M21 M22.",
    "unfamiliar_rate is the external pass rate on M19 and M20 only. M25 is composition, not unfamiliar.",
    "Lessons apply only to the same problem class, plus the one composition pipeline_sum__scale.",
    "If the lesson arm and the no-lesson arm differ on M19 or M20, record leakage.",
    "A same-class trace replay is remember when the slot map matches the stored example, otherwise procedure_reuse. It is not generalization.",
    "M25 is programmed composition.",
    "The controller is a deterministic grammar over an explicit problem class. It is not a language-model interpretation.",
    "Repeated failed operations are counted from the world log, not from the controller's own failure list.",
    "Resource consumption is the sum of completed tool calls and the parent-timed elapsed milliseconds. Local arithmetic does not spend a tool call.",
]


def _index(rows):
    found = [row["mission_id"] for row in rows]
    if found != EXPECTED_IDS:
        raise ValueError(f"mission order mismatch: {found}")
    return {row["mission_id"]: row for row in rows}


def _rate(rows, predicate):
    hits = [row for row in rows if predicate(row)]
    return len(hits), (len(hits) / len(rows) if rows else 0.0)


def summarize(arm, rows):
    by_id = _index(rows)
    passes, completion = _rate(rows, lambda row: row["objective_pass"])
    recovery_hits = [
        mission_id
        for mission_id in RECOVERY_IDS
        if by_id[mission_id]["objective_pass"]
        and by_id[mission_id]["alternate_used"]
        and by_id[mission_id]["repeat_extras"] == 0
    ]
    restart_hits = [
        mission_id
        for mission_id in RESTART_IDS
        if by_id[mission_id]["objective_pass"]
        and by_id[mission_id]["resumed_from_checkpoint"]
        and len(set(by_id[mission_id]["launched_pids"])) >= 2
    ]
    block_hits = [mission_id for mission_id in BLOCK_IDS if by_id[mission_id]["objective_pass"]]
    unfamiliar_hits = [mission_id for mission_id in UNFAMILIAR_IDS if by_id[mission_id]["objective_pass"]]
    policy = by_id[POLICY_NON_REPEAT_ID]
    return {
        "arm": arm,
        "n": len(rows),
        "completion_passes": passes,
        "completion_rate": completion,
        "successful_recovery_passes": recovery_hits,
        "successful_recovery_rate": len(recovery_hits) / len(RECOVERY_IDS),
        "unsupported_completion_claims": sum(1 for row in rows if row["unsupported"]),
        "contradictions": sum(row["contradictions"] for row in rows),
        "repeated_failed_operations": sum(row["repeat_extras"] for row in rows),
        "resource_tool_calls": sum(row["tool_calls"] for row in rows),
        "resource_elapsed_ms": round(sum(row["elapsed_ms"] for row in rows), 3),
        "recovery_after_restart_passes": restart_hits,
        "recovery_after_restart_rate": len(restart_hits) / len(RESTART_IDS),
        "blocked_when_should_block_passes": block_hits,
        "blocked_when_should_block_rate": len(block_hits) / len(BLOCK_IDS),
        "unfamiliar_passes": unfamiliar_hits,
        "unfamiliar_rate": len(unfamiliar_hits) / len(UNFAMILIAR_IDS),
        "policy_non_repeat": {
            "mission_id": POLICY_NON_REPEAT_ID,
            "objective_pass": policy["objective_pass"],
            "status": policy["status"],
            "unsupported": policy["unsupported"],
            "repeat_extras": policy["repeat_extras"],
            "note": "Inside completion_rate. Not removed.",
        },
        "composition": {
            mission_id: {
                "objective_pass": by_id[mission_id]["objective_pass"],
                "learning_applied": by_id[mission_id]["learning_applied"],
                "status": by_id[mission_id]["status"],
            }
            for mission_id in COMPOSITION_IDS
        },
        "tight_heldout": {
            mission_id: {
                "objective_pass": by_id[mission_id]["objective_pass"],
                "learning_applied": by_id[mission_id]["learning_applied"],
                "plan_source": by_id[mission_id]["plan_source"],
                "tool_calls": by_id[mission_id]["tool_calls"],
            }
            for mission_id in TIGHT_HELDOUT_IDS
        },
        "learning_applied_counts": _counts(row["learning_applied"] for row in rows),
    }


def _counts(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def lesson_flags(engine_rows, ablation_rows):
    engine = _index(engine_rows)
    ablation = _index(ablation_rows)
    flags = []
    for mission_id in UNFAMILIAR_IDS:
        if engine[mission_id]["objective_pass"] != ablation[mission_id]["objective_pass"]:
            flags.append({"mission_id": mission_id, "flag": "leakage_completion"})
        if engine[mission_id]["tool_calls"] != ablation[mission_id]["tool_calls"]:
            flags.append({"mission_id": mission_id, "flag": "leakage_tool_calls"})
    for mission_id in TIGHT_HELDOUT_IDS + COMPOSITION_IDS:
        flags.append(
            {
                "mission_id": mission_id,
                "engine_pass": engine[mission_id]["objective_pass"],
                "ablation_pass": ablation[mission_id]["objective_pass"],
                "engine_learning": engine[mission_id]["learning_applied"],
                "ablation_learning": ablation[mission_id]["learning_applied"],
                "engine_tools": engine[mission_id]["tool_calls"],
                "ablation_tools": ablation[mission_id]["tool_calls"],
            }
        )
    return flags


def compare(baseline, engine, ablation):
    def delta(key):
        return {
            "baseline": baseline[key],
            "engine": engine[key],
            "engine_minus_baseline": _subtract(engine[key], baseline[key]),
        }

    return {
        "completion_rate": delta("completion_rate"),
        "successful_recovery_rate": delta("successful_recovery_rate"),
        "unsupported_completion_claims": delta("unsupported_completion_claims"),
        "contradictions": delta("contradictions"),
        "repeated_failed_operations": delta("repeated_failed_operations"),
        "resource_tool_calls": delta("resource_tool_calls"),
        "resource_elapsed_ms": delta("resource_elapsed_ms"),
        "recovery_after_restart_rate": delta("recovery_after_restart_rate"),
        "blocked_when_should_block_rate": delta("blocked_when_should_block_rate"),
        "unfamiliar_rate": delta("unfamiliar_rate"),
        "ablation_completion_rate": ablation["completion_rate"],
        "engine_completion_rate": engine["completion_rate"],
        "reading_rules": list(READING_RULES),
    }


def _subtract(left, right):
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return round(left - right, 6)
    return None
