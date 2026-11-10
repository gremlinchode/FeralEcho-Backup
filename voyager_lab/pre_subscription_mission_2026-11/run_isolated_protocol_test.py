#!/usr/bin/env python3
"""Isolated two-party grok_relay protocol test. Does not touch the live mailbox."""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path("/tmp/fe-relay-phase2")
PORT = 18765
SRC = Path(__file__).resolve().parent / "relay_protocol_under_test.py"
TOKEN = "fe-pre-sub-isolated-20261109"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact(text: str) -> str:
    return re.sub(r"\d{1,3}(?:\.\d{1,3}){3}", "[addr]", text)


def write_relay(directory: Path, identity: str) -> None:
    source = SRC.read_text(encoding="utf-8")
    source = re.sub(r"\d{1,3}(?:\.\d{1,3}){3}", "127.0.0.1", source)
    source = source.replace('IDENTITY = "m5"', f'IDENTITY = "{identity}"')
    source = source.replace(":5000/projects/file", f":{PORT}/projects/file")
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "relay.py").write_text(source, encoding="utf-8")
    if re.search(r"100\.\d", source):
        raise SystemExit("sanitized relay still contains a tailnet literal")


class Handler(BaseHTTPRequestHandler):
    files: dict[str, Path] = {}
    mode: str = "ok"

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        if self.mode == "drop":
            self.close_connection = True
            return
        if self.mode == "down":
            self._send(503, {"error": "unavailable"})
            return
        parsed = urlparse(self.path)
        if parsed.path != "/projects/file":
            self._send(404, {"error": "not found"})
            return
        name = parse_qs(parsed.query).get("path", [""])[0]
        name = name.rsplit("/", 1)[-1]
        path = self.files.get(name)
        if path is None or not path.is_file():
            self._send(400, {"error": "invalid path"})
            return
        content = path.read_text(encoding="utf-8")
        self._send(200, {"path": f"grok_relay/{name}", "content": content, "size": path.stat().st_size})

    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve() -> ThreadingHTTPServer:
    Handler.files = {
        "from_m5.md": ROOT / "m5" / "from_m5.md",
        "from_ark.md": ROOT / "ark" / "from_ark.md",
    }
    Handler.mode = "ok"
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def run(identity: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / identity / "relay.py"), *args],
        cwd=ROOT / identity,
        text=True,
        capture_output=True,
        check=False,
    )


def relay_id(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("[grok-relay] id:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("append did not print an id")


def outbox(identity: str) -> list[dict]:
    path = ROOT / identity / ".outbox.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def inbox_text(identity: str) -> str:
    path = ROOT / identity / ".inbox_from_ark.md" if identity == "m5" else ROOT / identity / ".inbox_from_m5.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def marker_length(identity: str, peer: str) -> int | None:
    path = ROOT / identity / f".last_seen_from_{peer}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("length")


def main() -> int:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    write_relay(ROOT / "m5", "m5")
    write_relay(ROOT / "ark", "ark")
    server = serve()
    report: dict = {"started_at": now(), "cases": []}

    def add(name: str, ok: bool, **detail) -> None:
        case = {"name": name, "result": "PASS" if ok else "FAIL", **detail}
        report["cases"].append(case)
        extra = {k: v for k, v in case.items() if k not in {"name", "result"}}
        print(f"{case['result']} {name} {extra}", flush=True)

    self_test = run("m5", "self-test")
    add("copy self-test", self_test.returncode == 0 and "passed 9/9" in self_test.stdout, exit=self_test.returncode)

    sent = run("m5", "append", f"{TOKEN} ping from A. No personal content.")
    sent_id = relay_id(sent.stdout)
    add("A send records unacked id", sent.returncode == 0 and outbox("m5")[-1]["id"] == sent_id and outbox("m5")[-1]["acked"] is False, id=sent_id)

    first = run("ark", "read")
    received = TOKEN in first.stdout and sent_id in first.stdout and "Nothing new" not in first.stdout
    add("B receives A's message", first.returncode == 0 and received)
    inbox_after_first = inbox_text("ark")
    add("B inbox keeps the message before any ack", sent_id in inbox_after_first and TOKEN in inbox_after_first)

    reply = run("ark", "append", f"ack: {sent_id}\n{TOKEN} reply from B.")
    reply_id = relay_id(reply.stdout)
    add("B reply has its own id", reply.returncode == 0 and reply_id != sent_id and reply_id.startswith("ark-"), id=reply_id)

    back = run("m5", "read")
    m5_row = next(row for row in outbox("m5") if row["id"] == sent_id)
    add(
        "A receives reply and records B's ack",
        back.returncode == 0 and TOKEN in back.stdout and reply_id in back.stdout and m5_row.get("acked") is True and "acked_at" in m5_row,
    )

    ack_reply = run("m5", "append", f"ack: {reply_id}")
    add("A ack of reply appends", ack_reply.returncode == 0)
    b_again = run("ark", "read")
    ark_row = next(row for row in outbox("ark") if row["id"] == reply_id)
    add("B records A's ack", b_again.returncode == 0 and ark_row.get("acked") is True)

    inbox_before_dup = inbox_text("ark")
    marker_before_dup = marker_length("ark", "m5")
    dup = run("ark", "read")
    add(
        "second read does not deliver the message again",
        dup.returncode == 0 and "Nothing new" in dup.stdout and inbox_text("ark") == inbox_before_dup and marker_length("ark", "m5") == marker_before_dup,
    )

    # Lost cursor: rewind only the isolated marker, then read again.
    marker_path = ROOT / "ark" / ".last_seen_from_m5.json"
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["length"] = 0
    marker_path.write_text(json.dumps(marker), encoding="utf-8")
    replay = run("ark", "read")
    add(
        "lost cursor replays the same id",
        replay.returncode == 0 and sent_id in replay.stdout and inbox_text("ark").count(sent_id) >= 2,
    )

    two = run("m5", "append", f"{TOKEN} order-first")
    three = run("m5", "append", f"{TOKEN} order-second")
    two_id = relay_id(two.stdout)
    three_id = relay_id(three.stdout)
    ordered = run("ark", "read")
    pos_two = ordered.stdout.find(two_id)
    pos_three = ordered.stdout.find(three_id)
    add("appended messages stay in file order", pos_two >= 0 and pos_three > pos_two, first=two_id, second=three_id)

    before_down = [row.get("acked") for row in outbox("m5")]
    Handler.mode = "drop"
    down = run("m5", "status")
    add(
        "dropped endpoint is unreachable and does not invent acks",
        down.returncode == 1 and "unreachable" in down.stdout and [row.get("acked") for row in outbox("m5")] == before_down,
        exit=down.returncode,
    )
    Handler.mode = "down"
    refused = run("m5", "status")
    add(
        "HTTP 503 is unreachable and does not invent acks",
        refused.returncode == 1 and "unreachable" in refused.stdout and [row.get("acked") for row in outbox("m5")] == before_down,
        exit=refused.returncode,
    )
    closed_src = (ROOT / "m5" / "relay.py").read_text(encoding="utf-8").replace(f":{PORT}/projects/file", ":18766/projects/file")
    (ROOT / "m5" / "relay_closed.py").write_text(closed_src, encoding="utf-8")
    closed = subprocess.run(
        [sys.executable, str(ROOT / "m5" / "relay_closed.py"), "status"],
        cwd=ROOT / "m5",
        text=True,
        capture_output=True,
        check=False,
    )
    add(
        "closed port is unreachable and does not invent acks",
        closed.returncode == 1 and "unreachable" in closed.stdout and [row.get("acked") for row in outbox("m5")] == before_down,
        exit=closed.returncode,
    )
    Handler.mode = "ok"
    up = run("m5", "status")
    add("status recovers when the endpoint returns", up.returncode == 0 and "reachable" in up.stdout and "Unread" in up.stdout)

    # New process, same directory: cursor and outbox survive.
    restarted = run("ark", "status")
    add(
        "new process keeps the character cursor",
        restarted.returncode == 0 and "Unread   : 0 characters" in restarted.stdout,
    )

    # False ack reporting: an ack line whose id is absent from the outbox.
    false_ack = run("m5", "append", "ack: not-a-real-id")
    consumed = run("ark", "read")
    said_recorded = "Ack recorded for not-a-real-id" in consumed.stdout
    ark_ids = {row["id"] for row in outbox("ark")}
    add(
        "ack print matches an outbox change",
        said_recorded is False or "not-a-real-id" in ark_ids,
        print_says_recorded=said_recorded,
        outbox_has_id="not-a-real-id" in ark_ids,
    )

    server.shutdown()
    report["finished_at"] = now()
    report["pass"] = sum(1 for case in report["cases"] if case["result"] == "PASS")
    report["fail"] = sum(1 for case in report["cases"] if case["result"] == "FAIL")
    out = ROOT / "result.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "fail": report["fail"], "result": str(out)}, indent=2))
    for case in report["cases"]:
        extra = {k: v for k, v in case.items() if k not in {"name", "result"}}
        print(f"{case['result']} {case['name']} {extra}")
    return 0 if report["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
