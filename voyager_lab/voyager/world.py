"""Sandboxed mission world. Faults are applied here, not announced as answers."""

import json
import os
from pathlib import Path

from voyager.atomic import atomic_write


class ProcessInterrupt(Exception):
    """The world ends this process before the current tool runs."""


def _now_unused():
    return None


class World:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.meta_path = self.root / "_world_state.json"
        self.log_path = self.root / "_tool_log.jsonl"
        self.state = json.loads(self.meta_path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        atomic_write(self.meta_path.as_posix(), json.dumps(self.state, indent=2, sort_keys=True))

    def _resolve(self, rel: str) -> Path:
        if not isinstance(rel, str) or rel == "" or rel.startswith("/"):
            raise ValueError("path refused")
        parts = Path(rel).parts
        if ".." in parts:
            raise ValueError("path refused")
        path = (self.root / rel).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError("path refused")
        return path

    def _gate(self) -> None:
        kill_after = self.state.get("kill_after")
        if (
            kill_after is not None
            and self.state["completed_calls"] >= kill_after
            and not self.state["kill_spent"]
        ):
            self.state["kill_spent"] = True
            self._save()
            raise ProcessInterrupt()
        self.state["completed_calls"] += 1
        self._save()

    def _log(self, op: str, args: dict, result: dict) -> None:
        row = {
            "op": op,
            "args": args,
            "status": result["status"],
            "code": result["code"],
        }
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def _finish(self, op: str, args: dict, status: str, code: str, text: str = "") -> dict:
        result = {"status": status, "code": code, "text": text}
        self._log(op, args, result)
        return result

    def read(self, rel: str) -> dict:
        self._gate()
        args = {"path": rel}
        remaining = self.state.get("fail_reads_remaining", {})
        if remaining.get(rel, 0) > 0:
            remaining[rel] -= 1
            self.state["fail_reads_remaining"] = remaining
            self._save()
            return self._finish("read", args, "error", "io_error", "")
        if rel in self.state.get("unknown_reads", []):
            return self._finish("read", args, "unknown", "unknown_result", "")
        if rel in self.state.get("partial_reads", {}):
            return self._finish("read", args, "partial", "partial", self.state["partial_reads"][rel])
        try:
            path = self._resolve(rel)
        except ValueError as exc:
            return self._finish("read", args, "error", "path_refused", str(exc))
        if not path.is_file():
            return self._finish("read", args, "error", "file_not_found", "")
        text = path.read_text(encoding="utf-8")
        if rel in self.state.get("consume_on_read", []):
            path.unlink()
        return self._finish("read", args, "ok", "ok", text)

    def write(self, rel: str, text: str) -> dict:
        self._gate()
        args = {"path": rel}
        if self.state.get("human_gate") and not (self.root / ".human_token").is_file():
            return self._finish("write", args, "blocked", "human_required", "")
        try:
            path = self._resolve(rel)
        except ValueError as exc:
            return self._finish("write", args, "error", "path_refused", str(exc))
        if path.parent != self.root and not path.parent.is_dir():
            return self._finish("write", args, "error", "missing_parent", "")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return self._finish("write", args, "ok", "ok", text)

    def create_dir(self, rel: str) -> dict:
        self._gate()
        args = {"path": rel}
        try:
            path = self._resolve(rel)
        except ValueError as exc:
            return self._finish("create_dir", args, "error", "path_refused", str(exc))
        path.mkdir(parents=True, exist_ok=True)
        return self._finish("create_dir", args, "ok", "ok", "")

    def add(self, left: str, right: str) -> dict:
        self._gate()
        args = {"left": left, "right": right}
        if "add" in self.state.get("down_tools", []):
            return self._finish("add", args, "blocked", "tool_unavailable", "")
        try:
            value = str(int(left) + int(right))
        except ValueError:
            return self._finish("add", args, "error", "bad_number", "")
        return self._finish("add", args, "ok", "ok", value)

    def sum_lines(self, rel: str) -> dict:
        self._gate()
        args = {"path": rel}
        try:
            path = self._resolve(rel)
        except ValueError as exc:
            return self._finish("sum_lines", args, "error", "path_refused", str(exc))
        if not path.is_file():
            return self._finish("sum_lines", args, "error", "file_not_found", "")
        try:
            total = sum(int(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except ValueError:
            return self._finish("sum_lines", args, "error", "bad_number", "")
        return self._finish("sum_lines", args, "ok", "ok", str(total))


def materialize_world(spec: dict, root: str) -> None:
    os.makedirs(root, exist_ok=True)
    for rel, content in spec.get("files", {}).items():
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    state = {
        "kill_after": spec.get("kill_after"),
        "kill_spent": False,
        "completed_calls": 0,
        "fail_reads_remaining": dict(spec.get("fail_reads_remaining", {})),
        "consume_on_read": list(spec.get("consume_on_read", [])),
        "partial_reads": dict(spec.get("partial_reads", {})),
        "unknown_reads": list(spec.get("unknown_reads", [])),
        "down_tools": list(spec.get("down_tools", [])),
        "human_gate": bool(spec.get("human_gate", False)),
    }
    atomic_write(os.path.join(root, "_world_state.json"), json.dumps(state, indent=2, sort_keys=True))
    open(os.path.join(root, "_tool_log.jsonl"), "w", encoding="utf-8").close()


def plant_human_token(root: str) -> None:
    path = os.path.join(root, ".human_token")
    atomic_write(path, "ok\n")
