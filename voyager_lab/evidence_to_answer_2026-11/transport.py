#!/usr/bin/env python3
"""Unhashed local client for the evidence-to-answer experiment.

This file is not part of the sealed protocol. It does not import the
Flask application. It does not open the answer key.
"""

from __future__ import annotations

import json
import socket
import subprocess
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone

CHAT_URL = "http://127.0.0.1:5000/chat/stream"
SHOW_URL = "http://127.0.0.1:11434/api/show"
TIMEOUT_S = 180


def utc_now():
    return datetime.now(timezone.utc)


def stamp(value):
    return value.isoformat()


def parse_sse(raw):
    """Parse an SSE body, including a final block that has no trailing blank line."""
    if not isinstance(raw, (bytes, bytearray)):
        raw = b""
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    events = []
    unparsed = 0
    for block in text.split("\n\n"):
        data_parts = []
        for line in block.split("\n"):
            if line.startswith("data:"):
                data_parts.append(line[5:].lstrip(" "))
        if not data_parts:
            continue
        payload = "\n".join(data_parts)
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            unparsed += 1
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            unparsed += 1
    return events, unparsed


def summarize_events(events):
    tokens = []
    dones = []
    saves = []
    for event in events:
        kind = event.get("type")
        if kind == "token" and isinstance(event.get("text"), str):
            tokens.append(event["text"])
        elif kind == "done":
            dones.append(event)
        elif kind == "memory_save":
            saves.append(event)
    token_text = "".join(tokens)
    done = dones[-1] if dones else None
    save = saves[-1] if saves else None
    done_text = done.get("text") if isinstance(done, dict) else None
    done_present = isinstance(done_text, str)
    task_type = done.get("task_type") if isinstance(done, dict) else None
    trace_id = done.get("trace_id") if isinstance(done, dict) else None
    user_save = None
    echo_save = None
    if isinstance(save, dict):
        user_save = save.get("user") if isinstance(save.get("user"), str) else "unknown"
        echo_save = save.get("echo") if isinstance(save.get("echo"), str) else "unknown"
    return {
        "done_present": done_present,
        "done_text": done_text if done_present else None,
        "token_text": token_text,
        "texts_diverge": bool(done_present and token_text != done_text),
        "task_type": task_type if isinstance(task_type, str) else None,
        "trace_id": trace_id if isinstance(trace_id, str) else None,
        "memory_save_user": user_save,
        "memory_save_echo": echo_save,
        "done_count": len(dones),
        "memory_save_count": len(saves),
    }


def port_open(host, port, timeout=3.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def listener_observation():
    """Record who is listening on port 5000. Do not signal that process."""
    observed = {"port_open": port_open("127.0.0.1", 5000), "pid": None, "command": None}
    try:
        text = subprocess.check_output(
            ["lsof", "-nP", "-iTCP:5000", "-sTCP:LISTEN"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        observed["lsof_error"] = exc.__class__.__name__
        return observed
    pids = []
    commands = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or not parts[1].isdigit():
            continue
        pids.append(int(parts[1]))
        commands.append(parts[0])
    if pids:
        observed["pid"] = pids[0]
        observed["command"] = commands[0]
        observed["listener_pids"] = pids
    if observed["pid"] is not None:
        try:
            env = subprocess.check_output(
                ["ps", "eww", "-p", str(observed["pid"])],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            observed["ollama_model"] = "ps_error:" + exc.__class__.__name__
            return observed
        found = None
        for token in env.split():
            if token.startswith("OLLAMA_MODEL="):
                found = token.split("=", 1)[1]
                break
        observed["ollama_model"] = found if found is not None else "not_in_environment"
    return observed


def ollama_show():
    """One local metadata read. This is not a generation and does not spend budget."""
    payload = json.dumps({"name": "echo:latest"}).encode("utf-8")
    request = urllib.request.Request(
        SHOW_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
    except Exception as exc:
        return {"ok": False, "error": exc.__class__.__name__ + ": " + str(exc)}
    try:
        document = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "error": "show_not_json", "bytes": len(body)}
    if not isinstance(document, dict):
        return {"ok": False, "error": "show_not_object"}
    details = document.get("details") if isinstance(document.get("details"), dict) else {}
    kept = {
        "ok": True,
        "bytes": len(body),
        "modified_at": document.get("modified_at"),
        "parameters": document.get("parameters"),
        "digest": document.get("digest", details.get("digest")),
        "family": details.get("family"),
        "parameter_size": details.get("parameter_size"),
        "quantization_level": details.get("quantization_level"),
    }
    return kept


def post_chat(conversation_id, message, timeout_s=TIMEOUT_S):
    """POST one fast-mode chat. A wall-clock timeout does not signal the server."""
    started = utc_now()
    box = {}

    def worker():
        try:
            payload = json.dumps(
                {
                    "conversation_id": conversation_id,
                    "message": message,
                    "mode": "fast",
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                CHAT_URL,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                box["kind"] = "http"
                box["status"] = int(getattr(response, "status", 200))
                box["body"] = response.read()
        except urllib.error.HTTPError as exc:
            box["kind"] = "http_error"
            box["status"] = int(exc.code)
            try:
                box["body"] = exc.read()
            except Exception:
                box["body"] = b""
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            timed = isinstance(reason, (socket.timeout, TimeoutError)) or (
                "timed out" in str(reason).lower()
            )
            box["kind"] = "timeout" if timed else "connection"
            box["detail"] = str(reason)
        except (TimeoutError, socket.timeout):
            box["kind"] = "timeout"
            box["detail"] = "socket"
        except OSError as exc:
            box["kind"] = "connection"
            box["detail"] = str(exc)

    thread = threading.Thread(target=worker, name="e2a-post", daemon=True)
    thread.start()
    thread.join(timeout_s)
    finished = utc_now()
    if thread.is_alive():
        return {
            "started_at": started,
            "finished_at": finished,
            "http_status": None,
            "infrastructure": True,
            "infrastructure_reason": "timeout",
            "timeout_scope": "wall",
            "events_summary": summarize_events([]),
        }
    kind = box.get("kind")
    if kind == "http":
        events, unparsed = parse_sse(box.get("body") or b"")
        summary = summarize_events(events)
        summary["sse_unparsed"] = unparsed
        return {
            "started_at": started,
            "finished_at": finished,
            "http_status": box.get("status"),
            "infrastructure": False,
            "infrastructure_reason": None,
            "timeout_scope": None,
            "events_summary": summary,
        }
    if kind == "http_error":
        return {
            "started_at": started,
            "finished_at": finished,
            "http_status": box.get("status"),
            "infrastructure": True,
            "infrastructure_reason": "http_error",
            "timeout_scope": None,
            "events_summary": summarize_events([]),
        }
    if kind == "timeout":
        return {
            "started_at": started,
            "finished_at": finished,
            "http_status": None,
            "infrastructure": True,
            "infrastructure_reason": "timeout",
            "timeout_scope": "socket",
            "events_summary": summarize_events([]),
        }
    return {
        "started_at": started,
        "finished_at": finished,
        "http_status": None,
        "infrastructure": True,
        "infrastructure_reason": "connection",
        "timeout_scope": None,
        "detail": box.get("detail"),
        "events_summary": summarize_events([]),
    }


def self_test():
    body = (
        'data: {"type": "status", "text": "start"}\n\n'
        'data: {"type": "token", "text": "Sa"}\n\n'
        'data: {"type": "token", "text": "ble"}\n\n'
        'data: {"type": "memory_save", "user": "accepted", "echo": "accepted"}\n\n'
        'data: {"type": "done", "text": "ignored", "task_type": "general", "trace_id": "a"}\n\n'
        'data: {"type": "done", "text": "Sable", "task_type": "general", "trace_id": "b"}'
    ).encode("utf-8")
    events, unparsed = parse_sse(body)
    assert unparsed == 0
    summary = summarize_events(events)
    assert summary["done_text"] == "Sable"
    assert summary["trace_id"] == "b"
    assert summary["done_count"] == 2
    assert summary["token_text"] == "Sable"
    assert summary["texts_diverge"] is False
    assert summary["memory_save_user"] == "accepted"
    crlf = b'data: {"type": "done", "text": "", "task_type": "general", "trace_id": "c"}\r\n\r\n'
    events, unparsed = parse_sse(crlf)
    summary = summarize_events(events)
    assert summary["done_present"] is True
    assert summary["done_text"] == ""
    assert summary["texts_diverge"] is False
    diverged = (
        b'data: {"type":"token","text":"Sable."}\n\n'
        b'data: {"type":"done","text":"Sable","task_type":"general","trace_id":"d"}\n\n'
    )
    summary = summarize_events(parse_sse(diverged)[0])
    assert summary["texts_diverge"] is True
    assert summary["done_text"] == "Sable"
    print("transport_self_test=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
