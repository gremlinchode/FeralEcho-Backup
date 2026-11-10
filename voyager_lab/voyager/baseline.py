"""Single-source baseline.

No plan, no checkpoint resume, no alternate, no lesson, no budget stop.
Each process starts from empty vars. A non-interrupt run always claims
success after one write attempt.
"""

import json
import os
import resource

from voyager.atomic import atomic_write
from voyager.world import ProcessInterrupt, World


def _rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def _fresh(brief):
    return {
        "mission_id": brief["id"],
        "objective": brief["objective"],
        "status": "running",
        "tasks": [],
        "completed_tasks": [],
        "outstanding_tasks": [],
        "evidence": [],
        "failed_attempts": [],
        "resources": {
            "tool_calls": 0,
            "max_tool_calls": int(brief["budget"]),
            "ru_maxrss": _rss(),
            "ru_maxrss_unit": "macos_bytes",
            "elapsed_ms": 0,
        },
        "next_recommended_action": "read one source and write it",
        "last_successful_checkpoint": None,
        "vars": {},
        "claimed_value": None,
        "alternate_used": False,
        "pid_history": [os.getpid()],
        "resumed_from_checkpoint": False,
        "learning_applied": "none",
        "plan_source": "baseline",
        "plan_revisions": [],
        "problem_class": brief["problem_class"],
        "controller": "baseline_single_source",
    }


def _save(path, record, world):
    record["resources"]["tool_calls"] = world.state["completed_calls"]
    record["resources"]["ru_maxrss"] = _rss()
    atomic_write(path, json.dumps(record, indent=2, sort_keys=True))


def run_baseline(brief, root, record_path):
    world = World(root)
    record = _fresh(brief)
    slots = brief["slots"]
    if "src" in slots:
        src = slots["src"]
    elif "a" in slots:
        src = slots["a"]
    elif "left" in slots:
        src = slots["left"]
    else:
        src = None
    dst = slots.get("dst")
    value = None
    try:
        if src is not None:
            for _ in range(3):
                result = world.read(src)
                record["failed_attempts"].append(
                    {"op": "read", "args": {"path": src}, "status": result["status"], "code": result["code"]}
                ) if result["status"] != "ok" else None
                if result["status"] in ("ok", "partial", "unknown") and result["text"] != "":
                    value = result["text"]
                    record["evidence"].append(
                        {"class": "RETRIEVED", "field": "value", "value": value, "note": src}
                    )
                    break
        if value is None:
            value = "done"
            record["evidence"].append(
                {"class": "ASSUMPTION", "field": "value", "value": value, "note": "no source text"}
            )
        record["vars"]["value"] = value
        if dst is not None:
            world.write(dst, value)
        record["status"] = "success"
        record["claimed_value"] = value
        record["next_recommended_action"] = "none"
        _save(record_path, record, world)
    except ProcessInterrupt:
        record["status"] = "running"
        record["claimed_value"] = None
        record["next_recommended_action"] = "start over; baseline keeps no checkpoint"
        _save(record_path, record, world)
        raise
    return record
