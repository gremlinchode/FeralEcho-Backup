"""External grader.

The file on disk and the world log decide the score.
The controller's success string does not.
"""

import json
from collections import Counter
from pathlib import Path


def _load_log(root):
    path = Path(root) / "_tool_log.jsonl"
    rows = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def repeat_extras(rows):
    counts = Counter()
    for row in rows:
        if row["status"] == "ok":
            continue
        key = (row["op"], json.dumps(row["args"], sort_keys=True), row["code"])
        counts[key] += 1
    return sum(count - 1 for count in counts.values() if count >= 2)


def contradiction_events(record):
    buckets = {}
    for item in record.get("evidence", []):
        if item.get("field") in ("value", "output"):
            buckets.setdefault(item["field"], set()).add(item.get("value"))
    events = 0
    for values in buckets.values():
        if len(values) > 1:
            events += 1
    claimed = record.get("claimed_value")
    if claimed is not None:
        for values in buckets.values():
            if any(value != claimed for value in values):
                events += 1
    return events


def _file_state(root, rel):
    path = Path(root) / rel
    if not path.is_file():
        return False, None
    return True, path.read_text(encoding="utf-8")


def _status_ok(record, allowed):
    return record.get("status") in allowed


def evaluate(mission, record, root, phase1=None):
    grade = mission["grade"]
    kind = grade["kind"]
    log_rows = _load_log(root)
    exists, text = _file_state(root, grade["path"])
    phase1_ok = None
    if kind == "equals":
        file_ok = exists and text == grade["text"]
        status_ok = _status_ok(record, grade["status_in"])
        objective = file_ok and status_ok
    elif kind == "abstain":
        file_ok = not exists
        status_ok = _status_ok(record, grade["status_in"])
        objective = file_ok and status_ok
    elif kind == "two_phase":
        phase_record = phase1["record"]
        phase1_ok = (not phase1["exists"]) and _status_ok(phase_record, grade["phase1_status_in"])
        phase2_ok = exists and text == grade["phase2_text"] and _status_ok(record, grade["phase2_status_in"])
        objective = bool(phase1_ok and phase2_ok)
    else:
        raise ValueError(kind)
    unsupported = record.get("status") == "success" and not objective
    if phase1 is not None and phase1_ok is False and phase1["record"].get("status") == "success":
        unsupported = True
    return {
        "mission_id": mission["id"],
        "objective_pass": bool(objective),
        "status": record.get("status"),
        "unsupported": bool(unsupported),
        "contradictions": contradiction_events(record),
        "repeat_extras": repeat_extras(log_rows),
        "alternate_used": bool(record.get("alternate_used")),
        "resumed_from_checkpoint": bool(record.get("resumed_from_checkpoint")),
        "learning_applied": record.get("learning_applied"),
        "plan_source": record.get("plan_source"),
        "claimed_value": record.get("claimed_value"),
        "pid_history": list(record.get("pid_history", [])),
        "tool_calls_record": record.get("resources", {}).get("tool_calls"),
        "ru_maxrss": record.get("resources", {}).get("ru_maxrss"),
    }
