#!/usr/bin/env python3
"""A small, authenticated Codex-to-Codex mailbox over a private network.

This tool is independent from FeralEcho and claude_relay.  One copy runs a
``serve`` command on each peer; ``send`` pushes a message to the peer's
inbox.  Messages are stored locally as append-only JSONL.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
import threading
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAX_BODY_BYTES = 64 * 1024
DEFAULT_PORT = 8765


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(record: dict) -> bytes:
    """The signed byte representation, shared verbatim with the Air peer."""
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def signature(secret: str, record: dict) -> str:
    return hmac.new(secret.encode("utf-8"), canonical(record), "sha256").hexdigest()


def secret_from_env() -> str:
    value = os.environ.get("CODEX_RELAY_SECRET", "")
    if len(value) < 32:
        raise ValueError("CODEX_RELAY_SECRET must be set and at least 32 characters long")
    return value


def paths(data_dir: Path) -> tuple[Path, Path, Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    return (
        data_dir / "inbox.jsonl",
        data_dir / "outbox.jsonl",
        data_dir / ".last_seen.json",
        data_dir / ".seen_ids.json",
    )


def append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")


def load_seen(path: Path) -> set[str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return set(value) if isinstance(value, list) else set()
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()


def save_seen(path: Path, values: set[str]) -> None:
    # Keeping the last 10,000 IDs makes retry de-duplication durable without
    # letting this small index grow without bound.
    recent = sorted(values)[-10_000:]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(recent), encoding="utf-8")
    os.replace(tmp, path)


def valid_message(record: object, expected_sender: str, recipient: str) -> str | None:
    if not isinstance(record, dict):
        return "JSON payload must be an object"
    required = ("id", "sender", "recipient", "created_at", "message")
    if any(not isinstance(record.get(key), str) or not record[key] for key in required):
        return "id, sender, created_at, and body must be non-empty strings"
    if record["sender"] != expected_sender:
        return "sender does not match configured peer identity"
    if record["recipient"] != recipient:
        return "recipient does not match this relay identity"
    if len(record["message"].encode("utf-8")) > MAX_BODY_BYTES:
        return "message body is too large"
    return None


def valid_legacy_message(record: object, expected_sender: str) -> str | None:
    if not isinstance(record, dict):
        return "JSON payload must be an object"
    required = ("id", "sender", "created_at", "body")
    if any(not isinstance(record.get(key), str) or not record[key] for key in required):
        return "id, sender, created_at, and body must be non-empty strings"
    if record["sender"] != expected_sender:
        return "sender does not match configured peer identity"
    if len(record["body"].encode("utf-8")) > MAX_BODY_BYTES:
        return "message body is too large"
    return None


class RelayServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], secret: str, identity: str, expected_sender: str, data_dir: Path):
        super().__init__(address, RelayHandler)
        self.relay_secret = secret
        self.identity = identity
        self.expected_sender = expected_sender
        self.inbox, _, _, self.seen_path = paths(data_dir)
        self.lock = threading.Lock()


class RelayHandler(BaseHTTPRequestHandler):
    server: RelayServer

    def log_message(self, fmt: str, *args: object) -> None:
        # Avoid logging message bodies or authorization headers.
        sys.stderr.write("[codex-relay] %s\n" % (fmt % args))

    def reply(self, status: HTTPStatus, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path not in ("/health", "/v1/health"):
            self.reply(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if self.path == "/v1/health":
            supplied = self.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied, f"Bearer {self.server.relay_secret}"):
                self.reply(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
        self.reply(HTTPStatus.OK, {"status": "ok", "time": now()})

    def do_POST(self) -> None:
        if self.path not in ("/message", "/v1/messages"):
            self.reply(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES + 2048:
            self.reply(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "invalid or oversized request"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.reply(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})
            return
        if self.path == "/message":
            if not isinstance(payload, dict) or not isinstance(payload.get("signature"), str):
                self.reply(HTTPStatus.BAD_REQUEST, {"error": "record and signature are required"})
                return
            record = payload.get("record")
            problem = valid_message(record, self.server.expected_sender, self.server.identity)
            if problem:
                self.reply(HTTPStatus.BAD_REQUEST, {"error": problem})
                return
            if not hmac.compare_digest(payload["signature"], signature(self.server.relay_secret, record)):
                self.reply(HTTPStatus.UNAUTHORIZED, {"error": "invalid signature"})
                return
        else:
            supplied = self.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied, f"Bearer {self.server.relay_secret}"):
                self.reply(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            problem = valid_legacy_message(payload, self.server.expected_sender)
            if problem:
                self.reply(HTTPStatus.BAD_REQUEST, {"error": problem})
                return
            record = {
                "id": payload["id"], "sender": payload["sender"], "recipient": self.server.identity,
                "created_at": payload["created_at"], "message": payload["body"], "legacy_v1": True,
            }
        with self.server.lock:
            seen = load_seen(self.server.seen_path)
            duplicate = record["id"] in seen
            if not duplicate:
                record["received_at"] = now()
                append_jsonl(self.server.inbox, record)
                seen.add(record["id"])
                save_seen(self.server.seen_path, seen)
        self.reply(HTTPStatus.OK, {"accepted": True, "duplicate": duplicate})


def endpoint(peer: str, port: int) -> str:
    return f"http://{peer}:{port}"


def send(args: argparse.Namespace) -> int:
    try:
        secret = secret_from_env()
    except ValueError as e:
        print(f"[codex-relay] {e}", file=sys.stderr)
        return 2
    body = args.message if args.message is not None else sys.stdin.read()
    if not body.strip():
        print("[codex-relay] Refusing to send an empty message.", file=sys.stderr)
        return 2
    record = {
        "id": str(uuid.uuid4()), "sender": args.identity, "recipient": args.peer_identity,
        "created_at": now(), "message": body.rstrip(),
    }
    signed_payload = json.dumps({"record": record, "signature": signature(secret, record)}).encode("utf-8")
    if len(signed_payload) > MAX_BODY_BYTES + 2048:
        print("[codex-relay] Message exceeds 64 KiB.", file=sys.stderr)
        return 2
    signed_request = urllib.request.Request(
        endpoint(args.peer, args.port) + "/message", data=signed_payload, method="POST",
        headers={"Content-Type": "application/json"},
    )
    _, outbox, _, _ = paths(Path(args.data_dir))
    try:
        try:
            with urllib.request.urlopen(signed_request, timeout=args.timeout) as response:
                reply = json.loads(response.read())
            protocol = "signed"
        except urllib.error.HTTPError as error:
            if error.code != HTTPStatus.NOT_FOUND:
                raise
            legacy = {"id": record["id"], "sender": record["sender"], "created_at": record["created_at"], "body": record["message"]}
            legacy_request = urllib.request.Request(
                endpoint(args.peer, args.port) + "/v1/messages", data=json.dumps(legacy).encode("utf-8"), method="POST",
                headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(legacy_request, timeout=args.timeout) as response:
                reply = json.loads(response.read())
            protocol = "legacy-v1"
        append_jsonl(outbox, {**record, "sent_at": now(), "delivery": "accepted", "peer": args.peer, "protocol": protocol})
        print(f"[codex-relay] Delivered {record['id']} via {protocol} (duplicate={reply.get('duplicate', False)}).")
        return 0
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        append_jsonl(outbox, {**record, "attempted_at": now(), "delivery": "failed", "peer": args.peer, "error": str(e)})
        print(f"[codex-relay] Delivery failed: {e}", file=sys.stderr)
        return 1


def read(args: argparse.Namespace) -> int:
    inbox, _, marker_path, _ = paths(Path(args.data_dir))
    content = inbox.read_text(encoding="utf-8") if inbox.exists() else ""
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8")).get("length", 0)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        marker = 0
    if len(content) < marker:
        marker = 0
    new = content[marker:]
    marker_path.write_text(json.dumps({"length": len(content), "checked_at": now()}), encoding="utf-8")
    if not new.strip():
        print("[codex-relay] Nothing new.")
        return 0
    for line in new.splitlines():
        try:
            item = json.loads(line)
            print(f"\n## From {item['sender']} — {item['created_at']}\n")
            print(item["message"])
        except (json.JSONDecodeError, KeyError):
            print("[codex-relay] Skipped malformed local inbox record.", file=sys.stderr)
    return 0


def status(args: argparse.Namespace) -> int:
    inbox, outbox, marker_path, _ = paths(Path(args.data_dir))
    inbox_content = inbox.read_text(encoding="utf-8") if inbox.exists() else ""
    inbox_len = len(inbox_content)
    try:
        seen = json.loads(marker_path.read_text(encoding="utf-8")).get("length", 0)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        seen = 0
    print(f"Identity: {args.identity}\nInbox: {inbox_len} characters ({max(0, inbox_len - seen)} unread characters)\nOutbox: {outbox.stat().st_size if outbox.exists() else 0} bytes")
    if not args.peer:
        return 0
    try:
        request = urllib.request.Request(endpoint(args.peer, args.port) + "/health")
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            response.read()
        print(f"Peer {args.peer}: reachable")
        return 0
    except (ValueError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"Peer {args.peer}: unreachable ({e})")
        return 1


def serve(args: argparse.Namespace) -> int:
    try:
        server = RelayServer((args.bind, args.port), secret_from_env(), args.identity, args.peer_identity, Path(args.data_dir))
    except (OSError, ValueError) as e:
        print(f"[codex-relay] Cannot start server: {e}", file=sys.stderr)
        return 2
    print(f"[codex-relay] Listening on {args.bind}:{args.port}; accepting only sender {args.peer_identity}.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[codex-relay] Stopped.")
    finally:
        server.server_close()
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", default=str(Path.home() / ".codex-relay"))
    p.add_argument("--identity", default=os.environ.get("CODEX_RELAY_IDENTITY", "m5"))
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--timeout", type=float, default=5)
    sub = p.add_subparsers(dest="command", required=True)
    serve_p = sub.add_parser("serve")
    serve_p.add_argument("--bind", default="127.0.0.1", help="Use this machine's Tailscale IP for peer access.")
    serve_p.add_argument("--peer-identity", required=True)
    serve_p.set_defaults(func=serve)
    send_p = sub.add_parser("send")
    send_p.add_argument("--peer", required=True, help="Peer Tailscale IP or hostname.")
    send_p.add_argument("--peer-identity", required=True)
    send_p.add_argument("message", nargs="?")
    send_p.set_defaults(func=send)
    read_p = sub.add_parser("read")
    read_p.set_defaults(func=read)
    status_p = sub.add_parser("status")
    status_p.add_argument("--peer")
    status_p.set_defaults(func=status)
    return p


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
