"""Deterministic mission controller.

This is a library a later caller could use. It does not call a language
model, and it does not interpret free text. The problem class is an
explicit input. That limit is part of the record.
"""

import json
import os
import resource
from pathlib import Path

from voyager.atomic import atomic_write
from voyager.procedures import build_plan
from voyager.world import ProcessInterrupt, World

EVIDENCE_CLASSES = {"OBSERVATION", "RETRIEVED", "INFERENCE", "ASSUMPTION", "UNKNOWN"}


def _rss():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def blank_record(brief):
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
        "next_recommended_action": "plan",
        "last_successful_checkpoint": None,
        "vars": {},
        "claimed_value": None,
        "alternate_used": False,
        "pid_history": [],
        "resumed_from_checkpoint": False,
        "learning_applied": "none",
        "plan_source": "none",
        "plan_revisions": [],
        "fail_keys": [],
        "alternate_unlocked": False,
        "allow_human_retry": False,
        "human_retry_open": False,
        "problem_class": brief["problem_class"],
        "controller": "deterministic_grammar",
    }


def _recompute(record):
    tasks = record["tasks"]
    record["completed_tasks"] = [step["id"] for step in tasks if step["state"] == "success"]
    record["outstanding_tasks"] = [
        step["id"] for step in tasks if step["state"] not in ("success", "skipped")
    ]


def _save(path, record, world):
    record["resources"]["tool_calls"] = world.state["completed_calls"]
    record["resources"]["ru_maxrss"] = _rss()
    _recompute(record)
    atomic_write(path, json.dumps(record, indent=2, sort_keys=True))


def _add_ev(record, klass, field, value, note=""):
    if klass not in EVIDENCE_CLASSES:
        raise ValueError(klass)
    if field == "value":
        for item in record["evidence"]:
            if item["field"] == "value":
                item["field"] = "superseded_value"
    record["evidence"].append(
        {"class": klass, "field": field, "value": value, "note": note}
    )


def _stop(record, status, action):
    record["status"] = status
    record["next_recommended_action"] = action


def _checkpoint(record, step):
    record["last_successful_checkpoint"] = step["id"]
    record["next_recommended_action"] = "continue"


def _key(op, args):
    return [op, args]


def _refuse(record, op, args):
    if record.get("allow_human_retry") and op == "write":
        record["allow_human_retry"] = False
        return False
    key = _key(op, args)
    fails = [item for item in record["fail_keys"] if item == key]
    if not fails:
        return False
    if len(fails) >= 2:
        return True
    return not record.get("alternate_unlocked", False)


def _note_result(record, op, args, result):
    if result["status"] == "ok":
        if any(item[0] != op for item in record["fail_keys"]):
            record["alternate_unlocked"] = True
        return
    record["fail_keys"].append(_key(op, args))
    record["alternate_unlocked"] = False
    record["failed_attempts"].append(
        {"op": op, "args": args, "status": result["status"], "code": result["code"]}
    )


def _call(record, world, op, args, fn):
    if world.state["completed_calls"] >= record["resources"]["max_tool_calls"]:
        _stop(record, "blocked", "budget exhausted")
        return "stop", None
    if _refuse(record, op, args):
        _stop(record, "failed", "repeat refused")
        return "stop", None
    result = fn()
    _note_result(record, op, args, result)
    return "ok", result


def _finish_if_complete(record):
    if record["status"] != "running":
        return
    for step in record["tasks"]:
        if step.get("probe"):
            continue
        if step["state"] not in ("success", "skipped"):
            return
    record["status"] = "success"
    record["claimed_value"] = record["vars"].get("value")
    record["next_recommended_action"] = "none"


class Engine:
    def __init__(self, brief, root, record_path, lessons, lessons_enabled):
        self.brief = brief
        self.root = root
        self.record_path = record_path
        self.world = World(root)
        self.slots = brief["slots"]
        if os.path.exists(record_path):
            with open(record_path, encoding="utf-8") as handle:
                self.record = json.load(handle)
            if self.record.get("last_successful_checkpoint"):
                self.record["resumed_from_checkpoint"] = True
            self.record["pid_history"].append(os.getpid())
            if self.record.get("human_retry_open"):
                self.record["human_retry_open"] = False
                self.record["status"] = "running"
                for step in self.record["tasks"]:
                    if step["state"] == "blocked" and step.get("code") == "human_required":
                        step["state"] = "pending"
                        step.pop("code", None)
        else:
            self.record = blank_record(brief)
            self.record["pid_history"] = [os.getpid()]
            steps, source, learning, unplanned = build_plan(brief, lessons, lessons_enabled)
            self.record["tasks"] = steps
            self.record["plan_source"] = source
            self.record["learning_applied"] = learning
            if brief.get("hypothesis_class"):
                _add_ev(
                    self.record,
                    "ASSUMPTION",
                    "hypothesis",
                    brief["hypothesis_class"],
                    "initial hypothesis",
                )
            if unplanned:
                _stop(self.record, unplanned, "no procedure for this class")
        _save(self.record_path, self.record, self.world)

    def run(self):
        try:
            self._loop()
        except ProcessInterrupt:
            if self.record["status"] == "running":
                self.record["next_recommended_action"] = "resume from checkpoint"
            _save(self.record_path, self.record, self.world)
            raise
        _finish_if_complete(self.record)
        _save(self.record_path, self.record, self.world)

    def _loop(self):
        if self.record["status"] in ("success", "failed", "unknown"):
            return
        if self.record["status"] == "blocked" and not any(
            step["state"] == "pending" for step in self.record["tasks"]
        ):
            return
        self.record["status"] = "running"
        for step in self.record["tasks"]:
            if step["state"] in ("success", "skipped", "failed"):
                continue
            if step["state"] == "blocked":
                continue
            action = self._one(step)
            _save(self.record_path, self.record, self.world)
            if action == "stop":
                return
        _finish_if_complete(self.record)

    def _one(self, step):
        if step.get("probe") and step.get("missing_slot"):
            return self._probe_burn(step, "")
        if step.get("only_if") == "conflict" and not self.record["vars"].get("_conflict"):
            step["state"] = "skipped"
            return "continue"
        if step.get("missing_slot"):
            if step.get("only_if") == "conflict" and self.record["vars"].get("_conflict"):
                _stop(self.record, "unknown", "unresolved conflict; authority slot missing")
                return "stop"
            if step.get("probe"):
                return self._probe_burn(step, step.get("path") or "")
            _stop(self.record, "failed", f"missing slot {step.get('missing_slot')}")
            return "stop"
        op = step["op"]
        if op == "read":
            return self._read(step)
        if op == "write":
            return self._write(step)
        if op == "create_dir":
            return self._create_dir(step)
        if op == "add":
            return self._add(step)
        if op == "sum_lines":
            return self._sum_lines(step)
        if op == "compare":
            return self._compare(step)
        if op == "scale":
            return self._scale(step)
        if op == "join":
            return self._join(step)
        _stop(self.record, "failed", f"unknown op {op}")
        return "stop"

    def _probe_burn(self, step, path):
        action, result = _call(
            self.record,
            self.world,
            "read",
            {"path": path},
            lambda: self.world.read(path),
        )
        step["state"] = "failed"
        if action == "stop":
            return "stop"
        _add_ev(self.record, "ASSUMPTION", f"probe:{path}", result.get("text", ""), result["code"])
        return "continue"

    def _read(self, step):
        path = step.get("path") or ""
        action, result = _call(
            self.record,
            self.world,
            "read",
            {"path": path},
            lambda: self.world.read(path),
        )
        if action == "stop":
            return "stop"
        if step.get("probe"):
            _add_ev(
                self.record,
                "ASSUMPTION",
                f"probe:{path}",
                result.get("text", ""),
                result["code"],
            )
            step["state"] = "success" if result["status"] == "ok" else "failed"
            return "continue"
        if result["status"] == "ok":
            self._store_retrieved(step, result["text"])
            return "continue"
        if result["status"] == "unknown":
            _add_ev(self.record, "UNKNOWN", f"unknown:{path}", "", result["code"])
            _stop(self.record, "unknown", "read result unknown; not writing a guess")
            step["state"] = "failed"
            return "stop"
        if result["status"] == "partial":
            _add_ev(self.record, "OBSERVATION", f"partial:{path}", result.get("text", ""), "partial")
            return self._alt_read(step, "partial read is not the final value")
        if result["code"] in ("file_not_found", "io_error"):
            _add_ev(self.record, "OBSERVATION", f"read_error:{path}", result["code"], "")
            if result["code"] == "file_not_found":
                return self._alt_read(step, "file not found")
            step["state"] = "failed"
            _stop(self.record, "failed", "io_error; repeat refused")
            return "stop"
        _add_ev(self.record, "OBSERVATION", f"read_error:{path}", result["code"], "")
        step["state"] = "failed"
        if step.get("probe"):
            return "continue"
        _stop(self.record, "failed", result["code"])
        return "stop"

    def _store_retrieved(self, step, text):
        save = step.get("save", "value")
        self.record["vars"][save] = text
        _add_ev(self.record, "RETRIEVED", save if save != "value" else "value", text, step.get("path") or "")
        step["state"] = "success"
        _checkpoint(self.record, step)

    def _alt_read(self, step, reason):
        alt = self.slots.get("alt_src")
        if not alt:
            step["state"] = "failed"
            status = "partial" if "partial" in reason else "failed"
            _stop(self.record, status, reason)
            return "stop"
        action, result = _call(
            self.record,
            self.world,
            "read",
            {"path": alt},
            lambda: self.world.read(alt),
        )
        if action == "stop":
            step["state"] = "failed"
            return "stop"
        if result["status"] != "ok":
            step["state"] = "failed"
            _add_ev(self.record, "OBSERVATION", f"read_error:{alt}", result["code"], "alternate failed")
            _stop(self.record, "failed", "alternate read failed")
            return "stop"
        self.record["alternate_used"] = True
        self.record["plan_revisions"].append(
            {"after": step["id"], "action": f"read {alt}", "because": reason}
        )
        self._store_retrieved(step, result["text"])
        return "continue"

    def _write(self, step):
        path = step.get("path") or ""
        text = self.record["vars"].get(step.get("from", "value"), "")
        action, result = _call(
            self.record,
            self.world,
            "write",
            {"path": path},
            lambda: self.world.write(path, text),
        )
        if action == "stop":
            return "stop"
        if result["status"] == "ok":
            return self._wrote(step, text)
        if result["code"] == "human_required":
            step["state"] = "blocked"
            step["code"] = "human_required"
            self.record["allow_human_retry"] = True
            self.record["human_retry_open"] = True
            _stop(self.record, "blocked", "await human token then retry write")
            return "stop"
        if result["code"] == "missing_parent":
            return self._repair_parent(step, path, text)
        step["state"] = "failed"
        _stop(self.record, "failed", result["code"])
        return "stop"

    def _wrote(self, step, text):
        _add_ev(self.record, "OBSERVATION", "output", text, step.get("path") or "")
        step["state"] = "success"
        _checkpoint(self.record, step)
        return "continue"

    def _repair_parent(self, step, path, text):
        parent = self.slots.get("parent")
        if not parent:
            parent = str(Path(path).parent)
            if parent in ("", "."):
                step["state"] = "failed"
                _stop(self.record, "failed", "missing_parent")
                return "stop"
        action, result = _call(
            self.record,
            self.world,
            "create_dir",
            {"path": parent},
            lambda: self.world.create_dir(parent),
        )
        if action == "stop":
            step["state"] = "failed"
            return "stop"
        if result["status"] != "ok":
            step["state"] = "failed"
            _stop(self.record, "failed", "create_dir failed")
            return "stop"
        self.record["alternate_used"] = True
        self.record["plan_revisions"].append(
            {"after": step["id"], "action": f"create_dir {parent}", "because": "missing_parent"}
        )
        action, result = _call(
            self.record,
            self.world,
            "write",
            {"path": path},
            lambda: self.world.write(path, text),
        )
        if action == "stop":
            step["state"] = "failed"
            return "stop"
        if result["status"] != "ok":
            step["state"] = "failed"
            _stop(self.record, "failed", result["code"])
            return "stop"
        return self._wrote(step, text)

    def _create_dir(self, step):
        path = step.get("path") or ""
        action, result = _call(
            self.record,
            self.world,
            "create_dir",
            {"path": path},
            lambda: self.world.create_dir(path),
        )
        if action == "stop":
            return "stop"
        if result["status"] != "ok":
            step["state"] = "failed"
            _stop(self.record, "failed", result["code"])
            return "stop"
        _add_ev(self.record, "OBSERVATION", "dir", path, "created")
        step["state"] = "success"
        _checkpoint(self.record, step)
        return "continue"

    def _add(self, step):
        left = str(self.record["vars"].get("a", "")).strip()
        right = str(self.record["vars"].get("b", "")).strip()
        action, result = _call(
            self.record,
            self.world,
            "add",
            {"left": left, "right": right},
            lambda: self.world.add(left, right),
        )
        if action == "stop":
            return "stop"
        if result["status"] == "ok":
            self.record["vars"]["value"] = result["text"]
            _add_ev(self.record, "RETRIEVED", "value", result["text"], "add")
            step["state"] = "success"
            _checkpoint(self.record, step)
            return "continue"
        if result["code"] == "tool_unavailable":
            try:
                total = str(int(left) + int(right))
            except ValueError:
                step["state"] = "failed"
                _stop(self.record, "failed", "local sum failed")
                return "stop"
            self.record["vars"]["value"] = total
            _add_ev(self.record, "INFERENCE", "value", total, "local sum after add unavailable")
            self.record["alternate_used"] = True
            self.record["alternate_unlocked"] = True
            self.record["plan_revisions"].append(
                {"after": step["id"], "action": "local sum", "because": "tool_unavailable"}
            )
            step["state"] = "success"
            _checkpoint(self.record, step)
            return "continue"
        step["state"] = "failed"
        _stop(self.record, "failed", result["code"])
        return "stop"

    def _sum_lines(self, step):
        path = step.get("path") or ""
        action, result = _call(
            self.record,
            self.world,
            "sum_lines",
            {"path": path},
            lambda: self.world.sum_lines(path),
        )
        if action == "stop":
            return "stop"
        if result["status"] != "ok":
            step["state"] = "failed"
            _add_ev(self.record, "OBSERVATION", f"read_error:{path}", result["code"], "sum_lines")
            _stop(self.record, "failed", result["code"])
            return "stop"
        self.record["vars"]["value"] = result["text"]
        _add_ev(self.record, "RETRIEVED", "value", result["text"], "sum_lines")
        step["state"] = "success"
        _checkpoint(self.record, step)
        return "continue"

    def _compare(self, step):
        left = str(self.record["vars"].get("left", "")).strip()
        right = str(self.record["vars"].get("right", "")).strip()
        conflict = left != right
        self.record["vars"]["_conflict"] = conflict
        _add_ev(self.record, "INFERENCE", "_conflict", "true" if conflict else "false", "compare")
        if not conflict:
            self.record["vars"]["value"] = left
            _add_ev(self.record, "INFERENCE", "value", left, "reports agree")
        step["state"] = "success"
        _checkpoint(self.record, step)
        return "continue"

    def _scale(self, step):
        try:
            factor = int(str(step.get("path")).strip())
            current = int(str(self.record["vars"].get("value", "")).strip())
        except ValueError:
            step["state"] = "failed"
            _stop(self.record, "failed", "scale inputs are not integers")
            return "stop"
        total = str(current * factor)
        self.record["vars"]["value"] = total
        _add_ev(self.record, "INFERENCE", "value", total, f"scaled by {factor}")
        step["state"] = "success"
        _checkpoint(self.record, step)
        return "continue"

    def _join(self, step):
        left = str(self.record["vars"].get("a", "")).strip()
        right = str(self.record["vars"].get("b", "")).strip()
        total = f"{left}-{right}"
        self.record["vars"]["value"] = total
        _add_ev(self.record, "INFERENCE", "value", total, "join")
        step["state"] = "success"
        _checkpoint(self.record, step)
        return "continue"


def run_engine(brief, root, record_path, lessons, lessons_enabled):
    engine = Engine(brief, root, record_path, lessons, lessons_enabled)
    engine.run()
    return engine.record
