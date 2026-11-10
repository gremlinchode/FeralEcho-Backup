# LOOPBACK TEST COPY.
# Machine addresses in the live relay were replaced with 127.0.0.1.
# This file is the protocol under test for run_isolated_protocol_test.py.
# It is not the live mailbox program and it is not loaded by Echo.

#!/usr/bin/env python3
"""
grok_relay/relay.py — live M5 ↔ Ark mailbox for Grok sessions.

Stdlib only. No dependency on Claude or Codex.
Each side writes only its own file. The peer reads that file over
Tailscale with GET /projects/file on Echo's port 5000.
This loopback copy uses 127.0.0.1 for both sides.

The cursor is a character index into the decoded "content" string.
The endpoint's "size" field is bytes. Those two numbers differ when the
file contains multi-byte UTF-8. Storing size as the cursor makes the next
read look like the file shrank, and the old reader then printed nothing.

Usage (from repo root or anywhere):
    python3 grok_relay/relay.py status
    python3 grok_relay/relay.py read
    python3 grok_relay/relay.py append "message text"
    python3 grok_relay/relay.py append "message text" --flag needs-human
    python3 grok_relay/relay.py fact "claim" [--evidence "file:line"]
    python3 grok_relay/relay.py facts
    python3 grok_relay/relay.py facts-read
    python3 grok_relay/relay.py self-test
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Identity (edit this on each machine) ────────────────────────────────────
# Sender role:  IDENTITY = "m5"
# Peer role:    IDENTITY = "ark"
IDENTITY = "m5"

# Loopback addresses for the isolated protocol test.
SIDES = {
    "m5":  {"ip": "127.0.0.1", "file": "from_m5.md",  "label": "M5"},
    "ark": {"ip": "127.0.0.1",  "file": "from_ark.md", "label": "Ark"},
}

OTHER = "ark" if IDENTITY == "m5" else "m5"
RELAY_DIR = Path(__file__).resolve().parent
TIMEOUT = 5
FLAG_PREFIX = "**FLAG:**"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def own_file() -> Path:
    return RELAY_DIR / SIDES[IDENTITY]["file"]

def marker_file(peer: str = OTHER) -> Path:
    return RELAY_DIR / f".last_seen_from_{peer}.json"

def facts_file(side: str) -> Path:
    return RELAY_DIR / f"facts_{side}.jsonl"

def facts_marker_file(peer: str = OTHER) -> Path:
    return RELAY_DIR / f".last_seen_facts_from_{peer}.json"

def inbox_file(peer: str = OTHER) -> Path:
    return RELAY_DIR / f".inbox_from_{peer}.md"

def outbox_file() -> Path:
    return RELAY_DIR / ".outbox.jsonl"

def load_marker(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"length": 0, "unit": "chars", "checked_at": None}

def save_marker(path: Path, length: int) -> None:
    payload = {"length": length, "unit": "chars", "checked_at": now()}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def resolve_cursor(content: str, last: int, unit: str | None = None) -> tuple[str, int, str]:
    """Map a stored length onto a character index.

    Returns (kind, char_index, detail).
    kind "chars": last is a character index. This is the live contract.
    A marker that already says unit "chars" is never reinterpreted.
    kind "bytes": the marker has no unit (or says bytes), and last is past
    the character count but inside the UTF-8 byte length. That is the
    endpoint size field, or a size field plus a short newer suffix. The
    suffix is kept. A unitless length that is still <= the character count
    stays a character index: after a long append it is ambiguous, and
    guessing would skip or replay text.
    kind "reset": last is past both lengths, or a char-unit cursor is past
    the character count. The file shrank. char_index is the end. The caller
    does not reprint history.
    """
    if last < 0:
        last = 0
    n_chars = len(content)
    raw = content.encode("utf-8")
    n_bytes = len(raw)
    if unit == "chars":
        if last > n_chars:
            return "reset", n_chars, (
                f"character marker {last} is past the file ({n_chars} characters)"
            )
        return "chars", last, ""
    if last <= n_chars:
        return "chars", last, ""
    if last > n_bytes:
        return "reset", n_chars, (
            f"marker {last} is past the file "
            f"({n_chars} characters, {n_bytes} bytes)"
        )
    if last == n_bytes:
        return "bytes", n_chars, (
            f"marker {last} was a byte length; file is {n_chars} characters"
        )
    cut = last
    while cut < n_bytes and (raw[cut] & 0xC0) == 0x80:
        cut -= 1
        if cut < 0:
            break
    cut = max(cut, 0)
    char_index = len(raw[:cut].decode("utf-8"))
    return "bytes", char_index, (
        f"marker {last} was a byte offset; resumed at character {char_index}"
    )

def remember_inbox(peer: str, text: str) -> None:
    """Durably copy unread text before the cursor moves."""
    path = inbox_file(peer)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n<!-- received {now()} -->\n")
        f.write(text if text.endswith("\n") else text + "\n")

def new_message_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{IDENTITY}-{stamp}-{secrets.token_hex(4)}"

def record_sent(msg_id: str) -> None:
    rec = {"id": msg_id, "ts": now(), "acked": False}
    with outbox_file().open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")

def _load_outbox() -> list[dict]:
    path = outbox_file()
    if not path.exists():
        return []
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return rows

def mark_acks(text: str) -> list[str]:
    found = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("ack:"):
            ack_id = stripped.split(":", 1)[1].strip()
            if ack_id:
                found.append(ack_id)
    if not found:
        return []
    rows = _load_outbox()
    if not rows:
        return found
    found_set = set(found)
    changed = False
    for rec in rows:
        if rec.get("id") in found_set and not rec.get("acked"):
            rec["acked"] = True
            rec["acked_at"] = now()
            changed = True
    if changed:
        path = outbox_file()
        tmp = path.with_suffix(".tmp")
        body = "".join(json.dumps(rec, separators=(",", ":")) + "\n" for rec in rows)
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, path)
    return found

def unacked_ids() -> list[str]:
    return [rec.get("id", "") for rec in _load_outbox() if rec.get("id") and not rec.get("acked")]

def fetch_remote(filename: str, peer: str = OTHER) -> tuple[str | None, str | None]:
    """Returns (content, error). Exactly one is None."""
    ip = SIDES[peer].get("ip")
    if not ip or ip.startswith("100.x"):
        return None, f"{SIDES[peer]['label']} Tailscale IP not configured yet"
    url = f"http://{ip}:18765/projects/file?path=grok_relay/{filename}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("content", ""), None
    except Exception as e:
        return None, str(e)

def _cursor_view(content: str, marker: dict) -> tuple[str, int, str, int]:
    kind, start, detail = resolve_cursor(
        content,
        int(marker.get("length", 0) or 0),
        marker.get("unit"),
    )
    unread = 0 if kind == "reset" else max(0, len(content) - start)
    return kind, start, detail, unread

def cmd_status(_: argparse.Namespace) -> int:
    own = own_file()
    if own.exists():
        own_text = own.read_text(encoding="utf-8")
        own_chars = len(own_text)
        own_bytes = len(own_text.encode("utf-8"))
    else:
        own_chars = 0
        own_bytes = 0
    print(f"Identity : {IDENTITY} ({SIDES[IDENTITY]['label']})")
    print(f"Own file : {own.name}  ({own_chars} characters, {own_bytes} bytes)")

    content, err = fetch_remote(SIDES[OTHER]["file"])
    if err:
        print(f"Peer     : {SIDES[OTHER]['label']} unreachable — {err}")
        return 1

    kind, _start, detail, unread = _cursor_view(content, load_marker(marker_file()))
    peer_bytes = len(content.encode("utf-8"))
    print(f"Peer     : {SIDES[OTHER]['label']} reachable")
    print(f"Peer file: {len(content)} characters, {peer_bytes} bytes")
    print(f"Unread   : {unread} characters")
    if detail:
        print(f"Cursor   : {kind} — {detail}")
    pending = unacked_ids()
    print(f"Unacked  : {len(pending)}")
    return 0

def _consume(content: str, marker_path: Path, peer: str) -> tuple[int, str]:
    """Return (exit code, text to print). Advances the cursor only after the inbox copy."""
    marker = load_marker(marker_path)
    kind, start, detail = resolve_cursor(
        content,
        int(marker.get("length", 0) or 0),
        marker.get("unit"),
    )
    if kind == "reset":
        save_marker(marker_path, len(content))
        return 0, f"[grok-relay] {detail} Marker reset to the character end. Nothing replayed."

    new = content[start:]
    if new.strip():
        remember_inbox(peer, new)
    save_marker(marker_path, len(content))
    acked = mark_acks(new) if new.strip() else []
    lines = []
    if detail:
        lines.append(f"[grok-relay] {detail}")
    if acked:
        lines.append("[grok-relay] Ack recorded for " + ", ".join(acked))
    if not new.strip():
        lines.append("[grok-relay] Nothing new.")
        return 0, "\n".join(lines)
    if lines:
        lines.append("")
    lines.append(new if new.endswith("\n") else new + "\n")
    return 0, "\n".join(lines)

def cmd_read(_: argparse.Namespace) -> int:
    content, err = fetch_remote(SIDES[OTHER]["file"])
    if err:
        print(f"[grok-relay] Could not reach {SIDES[OTHER]['label']}: {err}", file=sys.stderr)
        return 1
    code, text = _consume(content, marker_file(), OTHER)
    print(text, end="" if text.endswith("\n") else "\n")
    return code

def cmd_append(args: argparse.Namespace) -> int:
    text = args.message.strip()
    if not text:
        print("[grok-relay] Refusing empty message.", file=sys.stderr)
        return 2

    ts = now()
    msg_id = new_message_id()
    entry = f"\n## {SIDES[IDENTITY]['label']} — {ts}\n\nid: {msg_id}\n\n{text}\n"
    if args.flag:
        entry += f"\n{FLAG_PREFIX} {args.flag}\n"

    path = own_file()
    with path.open("a", encoding="utf-8") as f:
        f.write(entry)
    record_sent(msg_id)

    print(f"[grok-relay] Appended to {path.name}")
    print(f"[grok-relay] id: {msg_id}")
    return 0

def cmd_fact(args: argparse.Namespace) -> int:
    record = {
        "ts": now(),
        "by": IDENTITY,
        "fact": args.fact.strip(),
        "evidence": args.evidence or "",
        "status": "open",
    }
    path = facts_file(IDENTITY)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
    print(f"[grok-relay] Fact recorded → {path.name}")
    return 0

def cmd_facts(_: argparse.Namespace) -> int:
    for side in (IDENTITY, OTHER):
        path = facts_file(side)
        count = 0
        if path.exists():
            count = sum(1 for _ in path.open(encoding="utf-8") if _.strip())
        print(f"{side:5} facts: {count}  ({path.name})")
    return 0

def cmd_facts_read(_: argparse.Namespace) -> int:
    content, err = fetch_remote(f"facts_{OTHER}.jsonl")
    if err:
        print(f"[grok-relay] Could not reach peer facts: {err}", file=sys.stderr)
        return 1
    code, text = _consume(content, facts_marker_file(), f"facts_{OTHER}")
    print(text, end="" if text.endswith("\n") else "\n")
    return code

def cmd_self_test(_: argparse.Namespace) -> int:
    """No network. No live mailbox files."""
    cases = []

    def check(name: str, content: str, last: int, kind: str, index: int, unread: str) -> None:
        got_kind, got_index, _detail = resolve_cursor(content, last)
        got = content[got_index:] if got_kind != "reset" else ""
        ok = got_kind == kind and got_index == index and got == unread
        cases.append((name, ok, got_kind, got_index, got))

    check("ascii char cursor", "abcdefgh", 4, "chars", 4, "efgh")
    check("ascii at end", "abcdefgh", 8, "chars", 8, "")
    em = "hello—world"  # 11 characters, 13 bytes
    check("emdash char end", em, len(em), "chars", len(em), "")
    check("emdash byte end", em, len(em.encode("utf-8")), "bytes", len(em), "")
    # Surplus is 2 bytes. A 1-character suffix keeps the old byte cursor
    # above the new character count, so the suffix is recoverable.
    short = em + "X"
    check("short suffix after byte eof", short, len(em.encode("utf-8")), "bytes", len(em), "X")
    # A longer suffix pulls the old byte cursor back under the character
    # count. Unitless markers stay on the character path. Guessing would
    # skip or replay. Prevention is to store unit "chars", which this file does.
    check("past both", "abc", 99, "reset", 3, "")
    check("negative", "abc", -5, "chars", 0, "abc")
    kind, index, _detail = resolve_cursor(em, len(em.encode("utf-8")), unit="chars")
    cases.append((
        "char unit does not become bytes",
        kind == "reset" and index == len(em),
        kind,
        index,
        "",
    ))

    # A byte-sized cursor at EOF must not take the shrink path.
    kind, index, _detail = resolve_cursor(em, len(em.encode("utf-8")))
    cases.append(("no false shrink", kind == "bytes" and index == len(em), kind, index, ""))

    failed = [c for c in cases if not c[1]]
    for name, ok, got_kind, got_index, got in cases:
        print(f"{'PASS' if ok else 'FAIL'} {name} kind={got_kind} index={got_index} unread={got!r}")
    if failed:
        print(f"[grok-relay] self-test failed {len(failed)}/{len(cases)}")
        return 1
    print(f"[grok-relay] self-test passed {len(cases)}/{len(cases)}")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Grok M5 ↔ Ark relay")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Health check")
    sub.add_parser("read", help="Show unread messages from peer and advance cursor")

    p_append = sub.add_parser("append", help="Append a message to this side's file")
    p_append.add_argument("message")
    p_append.add_argument("--flag", default=None, help="Optional flag, e.g. needs-human")

    p_fact = sub.add_parser("fact", help="Record a structured fact")
    p_fact.add_argument("fact")
    p_fact.add_argument("--evidence", default="")

    sub.add_parser("facts", help="Show fact counts both sides")
    sub.add_parser("facts-read", help="Show new facts from peer")
    sub.add_parser("self-test", help="Check cursor-unit handling without the network")

    args = parser.parse_args()

    if IDENTITY not in SIDES:
        print(f"[grok-relay] IDENTITY={IDENTITY!r} is not in SIDES", file=sys.stderr)
        return 2

    dispatch = {
        "status": cmd_status,
        "read": cmd_read,
        "append": cmd_append,
        "fact": cmd_fact,
        "facts": cmd_facts,
        "facts-read": cmd_facts_read,
        "self-test": cmd_self_test,
    }
    return dispatch[args.cmd](args)

if __name__ == "__main__":
    raise SystemExit(main())
