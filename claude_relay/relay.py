#!/usr/bin/env python3
"""
claude_relay/relay.py — small, self-contained tooling around the Claude
Code <-> Claude Code mailbox described in README.md.

Not a FeralEcho subsystem: not imported by app/ or run.py, not part of
Echo's runtime, not subject to EDIT_FORBIDDEN_TARGETS or the Liveness
Ledger — this is operator/session tooling, the same category as
spot_check.py or verify_riverbrain.py, just for the Claude<->Claude channel
rather than Echo herself.

Built 2026-07-24 after a manual health check of the relay found two real,
fixable fragilities, not because anything was actually broken:

  1. The old .last_seen_from_air.marker stored a hash of the *whole* other
     side's file. Any hand-maintenance slip (forgetting to update it, or a
     session computing the hash slightly differently) makes it silently
     wrong with no way to tell — which is exactly what a live check found:
     the stored marker didn't match a plain sha256 of the current file,
     and there was no way to be sure whether that meant "real unread
     content" or "someone hashed it differently once." Replaced with a
     length-based marker (how many characters of the other side's file
     have been read so far) — trivially robust to append-only growth,
     and it hands back the exact new substring directly instead of a
     boolean "changed" signal.
  2. Append-only was a convention enforced by nothing but a Claude session
     remembering to follow it. append_note() below makes overwriting
     structurally impossible — it only ever opens the file in append mode.

Usage (run from the repo root, or anywhere — paths are anchored to this
file's own directory):

    python3 claude_relay/relay.py status        # health check, both sides
    python3 claude_relay/relay.py read           # fetch + print new content from the other side, advance the marker
    python3 claude_relay/relay.py append "text"  # append a new dated entry to this machine's own file
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import requests

# This machine's identity in the relay's own naming (see CLAUDE.md's
# "Tailscale sync" section) is NOT the same thing as its OS hostname —
# confirmed directly before hardcoding this: this machine's hostname is
# "Richards-MacBook-Air.local" (a coincidence of what this physical laptop
# happens to be named) but its Tailscale IP (100.84.229.10) is M5. Do not
# switch this to hostname-based auto-detection; it would be silently wrong
# on this exact machine. The Air-side checkout of this same file should
# have IDENTITY = "air" instead.
IDENTITY = "m5"

_SIDES = {
    "m5": {"ip": "100.84.229.10", "file": "from_m5.md", "label": "M5"},
    "air": {"ip": "100.82.172.4", "file": "from_air.md", "label": "Air"},
}
_OTHER = "air" if IDENTITY == "m5" else "m5"

_RELAY_DIR = os.path.dirname(os.path.abspath(__file__))
_OWN_FILE = os.path.join(_RELAY_DIR, _SIDES[IDENTITY]["file"])
_MARKER_FILE = os.path.join(_RELAY_DIR, f".last_seen_from_{_OTHER}.json")
_TIMEOUT_S = 5


def _fetch_other_side() -> "tuple[str | None, str | None]":
    """Returns (content, error) — exactly one is None. Never raises; a
    timeout or an unreachable machine is real, expected, everyday state
    for this channel (see README's own "known limitation"), not a bug."""
    other = _SIDES[_OTHER]
    url = f"http://{other['ip']}:5000/projects/file"
    try:
        resp = requests.get(url, params={"path": f"claude_relay/{other['file']}"}, timeout=_TIMEOUT_S)
        resp.raise_for_status()
        return resp.json().get("content", ""), None
    except Exception as e:
        return None, str(e)


def _load_marker() -> dict:
    try:
        with open(_MARKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"length": 0, "checked_at": None}


def _save_marker(length: int) -> None:
    payload = {"length": length, "checked_at": datetime.now(timezone.utc).isoformat()}
    tmp = f"{_MARKER_FILE}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, _MARKER_FILE)


def read_new() -> str:
    """Fetches the other side's current file, returns only the content
    added since the last successful read, and advances the marker. If the
    other side's file somehow got SHORTER than the marker (the file was
    reset, or truncated) this is reported honestly rather than silently
    treated as "nothing new" or crashing on a negative slice."""
    content, err = _fetch_other_side()
    if err is not None:
        return f"[relay] Could not reach {_SIDES[_OTHER]['label']}: {err}"

    marker = _load_marker()
    last_len = marker.get("length", 0)

    if len(content) < last_len:
        _save_marker(len(content))
        return (
            f"[relay] {_SIDES[_OTHER]['label']}'s file is shorter than what was last read "
            f"({len(content)} chars now vs {last_len} previously recorded) — it may have "
            f"been reset. Marker re-synced to the current length; nothing shown."
        )

    new_content = content[last_len:]
    _save_marker(len(content))
    if not new_content.strip():
        return f"[relay] Nothing new from {_SIDES[_OTHER]['label']} since the last check."
    return new_content


def append_note(text: str) -> str:
    """Appends a new dated section to THIS machine's own file. Always
    append mode — there is no code path in this function capable of
    overwriting prior entries, unlike a hand-run editor session where
    forgetting the right mode is one keystroke away."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    section = f"\n## Entry — {date_str}\n\n{text.rstrip()}\n\n---\n"
    with open(_OWN_FILE, "a", encoding="utf-8") as f:
        f.write(section)
    return f"[relay] Appended to {os.path.basename(_OWN_FILE)} ({len(section)} chars)."


def status() -> str:
    """Structural health only — entry counts, reachability, staleness.
    Deliberately never prints the actual content of either file; matches
    this channel's own privacy rule (README.md) even when checking on it
    rather than participating in it."""
    lines = [f"Identity: {IDENTITY} ({_SIDES[IDENTITY]['label']})"]

    try:
        with open(_OWN_FILE, "r", encoding="utf-8") as f:
            own_content = f.read()
        own_entries = own_content.count("\n## Entry")
        lines.append(f"Own file ({_SIDES[IDENTITY]['file']}): {len(own_content)} chars, ~{own_entries} entries.")
    except FileNotFoundError:
        lines.append(f"Own file ({_SIDES[IDENTITY]['file']}): does not exist yet.")

    content, err = _fetch_other_side()
    if err is not None:
        lines.append(f"{_SIDES[_OTHER]['label']}: UNREACHABLE right now ({err}).")
    else:
        other_entries = content.count("\n## Entry")
        marker = _load_marker()
        unread = len(content) - marker.get("length", 0)
        lines.append(f"{_SIDES[_OTHER]['label']}: reachable, {len(content)} chars, ~{other_entries} entries.")
        if unread > 0:
            lines.append(f"  -> {unread} chars unread since the last `read` (marker last updated {marker.get('checked_at') or 'never'}).")
        elif unread < 0:
            lines.append(f"  -> marker is ahead of the live file by {-unread} chars (file may have been reset).")
        else:
            lines.append("  -> fully caught up.")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        print(status())
    elif cmd == "read":
        print(read_new())
    elif cmd == "append":
        if len(sys.argv) < 3:
            print("Usage: python3 claude_relay/relay.py append \"text\"")
            sys.exit(1)
        print(append_note(sys.argv[2]))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
