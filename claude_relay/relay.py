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

    python3 claude_relay/relay.py status                       # health check, both sides
    python3 claude_relay/relay.py read                          # fetch + print new content from the other side, advance the marker
    python3 claude_relay/relay.py read-hub                      # same mailbox file, independent cursor - what hub/notes.py's `pull` uses
    python3 claude_relay/relay.py append "text" [--flag needs-human]
                                                                  # append a new dated entry to this machine's own file
    python3 claude_relay/relay.py flagged                       # list the other side's entries tagged FLAG: needs-human
    python3 claude_relay/relay.py fact "text" [--evidence "..."] # append one structured, checkable fact to this side's own ledger
    python3 claude_relay/relay.py facts                          # health check for the facts ledger, both sides
    python3 claude_relay/relay.py facts-read                     # fetch + print new facts from the other side, advance the facts marker

Extension added 2026-09-09, after a real session found (by accident, while
verifying an unrelated claim) that the two forks' TASK_TYPE_MAP had already
drifted — 7 keys here, 4 on Air's side — with nothing in the mailbox
structure making that kind of concrete, checkable divergence discoverable
except by chance. Two additions, deliberately kept as small as the original
design:

  1. A parallel, structured "facts ledger" (facts_<side>.jsonl) alongside
     the prose mailbox — one JSON object per line, for the specific,
     checkable claims ("X has N keys," "function Y is/isn't guarded") that
     are worth being able to grep later without re-reading the full prose
     log. Same append-only + length-cursor mechanics as the mailbox, just a
     second parallel file pair so it never has to compete with or be
     confused for the prose conversation itself.
  2. An optional FLAG line on a mailbox entry (currently one value,
     "needs-human" — the exact case the README's own ground rule already
     names as needing to surface regardless of the channel's general
     privacy default), plus a `flagged` command that scans the other side's
     *entire* file for it. Deliberately a query over the whole file, not
     cursor-based — a flagged entry stays visible on every check until
     someone reads and acts on it, since the read-cursor's job is "what's
     new," not "what still needs attention." Known limitation, stated
     plainly rather than silently accepted: there is no "acknowledged"
     state yet, so a flag that's already been handled will keep showing up
     under `flagged` until someone removes/edits the marker text by hand —
     fine for the current two-party scale, a real gap if this ever needs to
     track more than a handful of live flags at once.
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
    # Intel/Ark (2026-09-27, design in audits/2026-09-27_
    # ark_checkin_protocol_design.md): a lightweight check-in channel,
    # NOT the separate, much heavier cross-backup/transfer plan in
    # audits/2026-09-20_feralecho_m5_intel_cross_backup_relay_plan.md.
    # ip is deliberately None -- unlike Air, Ark's Tailscale IP has never
    # been recorded anywhere in this repo (checked directly before adding
    # this entry) and per that same Sept-20 plan's own stated discipline,
    # peer IPs are always typed by the operator from the peer's own
    # Tailscale app, never discovered by scanning. Fill in once known;
    # every function below fails closed with a clear message on None
    # rather than crashing or guessing.
    "intel": {"ip": None, "file": "from_intel.md", "label": "Intel/Ark"},
}
_OTHER = "air" if IDENTITY == "m5" else "m5"  # unchanged default peer

_RELAY_DIR = os.path.dirname(os.path.abspath(__file__))
_OWN_FILE = os.path.join(_RELAY_DIR, _SIDES[IDENTITY]["file"])
_TIMEOUT_S = 5
_FLAG_PREFIX = "**FLAG:**"


def _resolve_peer(peer: "str | None") -> str:
    """Every public function below takes an optional `peer` argument that
    defaults to None, meaning "the original, unchanged _OTHER" — so every
    pre-existing call site (nothing passes peer today) is byte-for-byte
    unaffected by this extension. Raises on an unknown peer name rather
    than silently falling back, since a typo'd peer should never silently
    talk to the wrong machine."""
    if peer is None:
        return _OTHER
    if peer not in _SIDES or peer == IDENTITY:
        raise ValueError(f"Unknown or invalid peer: {peer!r} (known: {[k for k in _SIDES if k != IDENTITY]})")
    return peer


def _marker_file(peer: "str | None" = None) -> str:
    return os.path.join(_RELAY_DIR, f".last_seen_from_{_resolve_peer(peer)}.json")


def _hub_marker_file(peer: "str | None" = None) -> str:
    # Hub-notes marker — independent length-cursor over the SAME mailbox
    # file the ordinary marker tracks, so hub/notes.py's `pull` doesn't
    # compete with a plain manual `read` for the same "what's new"
    # position. Only ever used with the default (air) peer today.
    return os.path.join(_RELAY_DIR, f".last_seen_from_{_resolve_peer(peer)}_hub.json")


def _other_facts_file(peer: "str | None" = None) -> str:
    return f"facts_{_resolve_peer(peer)}.jsonl"


def _facts_marker_file(peer: "str | None" = None) -> str:
    return os.path.join(_RELAY_DIR, f".last_seen_facts_from_{_resolve_peer(peer)}.json")


# Facts ledger — a separate append-only file pair, same length-cursor
# mechanics as the mailbox, deliberately never merged with from_<side>.md
# (see module docstring). Filenames are own-name-first so a directory
# listing immediately shows which one is locally writable. This side's own
# facts file is peer-independent (there is only ever one from THIS
# machine), unlike everything above which is about reading the PEER.
_OWN_FACTS_FILE = os.path.join(_RELAY_DIR, f"facts_{IDENTITY}.jsonl")


def _fetch_remote_file(remote_name: str, peer: "str | None" = None) -> "tuple[str | None, str | None]":
    """Returns (content, error) — exactly one is None. Never raises; a
    timeout or an unreachable machine is real, expected, everyday state
    for this channel (see README's own "known limitation"), not a bug.
    `remote_name` is the filename under claude_relay/ on the peer side —
    generalized from the original mailbox-only version so the facts ledger
    can reuse the identical fetch path rather than a second copy of it."""
    p = _resolve_peer(peer)
    other = _SIDES[p]
    if not other.get("ip"):
        return None, (
            f"{other['label']}'s Tailscale IP is not yet known — this peer's "
            f"channel is designed but not yet bootstrapped (see "
            f"audits/2026-09-27_ark_checkin_protocol_design.md §6). Fill in "
            f"_SIDES[{p!r}]['ip'] once the operator confirms reachability."
        )
    url = f"http://{other['ip']}:5000/projects/file"
    try:
        resp = requests.get(url, params={"path": f"claude_relay/{remote_name}"}, timeout=_TIMEOUT_S)
        resp.raise_for_status()
        return resp.json().get("content", ""), None
    except Exception as e:
        return None, str(e)


def _fetch_other_side(peer: "str | None" = None) -> "tuple[str | None, str | None]":
    p = _resolve_peer(peer)
    return _fetch_remote_file(_SIDES[p]["file"], peer=p)


def _load_marker(marker_file: str) -> dict:
    # No default value (2026-09-27): the old default was the single fixed
    # _MARKER_FILE constant, which no longer exists now that marker paths
    # are peer-parameterized (_marker_file(peer)/_facts_marker_file(peer)/
    # _hub_marker_file()) — every real call site already passes it
    # explicitly, confirmed by grep before removing the default.
    try:
        with open(marker_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"length": 0, "checked_at": None}


def _save_marker(length: int, marker_file: str) -> None:
    payload = {"length": length, "checked_at": datetime.now(timezone.utc).isoformat()}
    tmp = f"{marker_file}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, marker_file)


def _read_new_generic(remote_name: str, marker_file: str, label: str, peer: "str | None" = None) -> "tuple[str | None, str]":
    """Shared fetch-since-marker logic behind both read_new() (mailbox) and
    read_new_facts() (facts ledger). Returns (new_content_or_None, message)
    — new_content is None on an error/nothing-new/reset case, in which case
    `message` is the human-readable explanation to print; otherwise
    new_content is the real new substring and message is unused by the
    caller."""
    p = _resolve_peer(peer)
    content, err = _fetch_remote_file(remote_name, peer=p)
    if err is not None:
        return None, f"[relay] Could not reach {_SIDES[p]['label']}: {err}"

    marker = _load_marker(marker_file)
    last_len = marker.get("length", 0)

    if len(content) < last_len:
        _save_marker(len(content), marker_file)
        return None, (
            f"[relay] {_SIDES[p]['label']}'s {label} is shorter than what was last read "
            f"({len(content)} chars now vs {last_len} previously recorded) — it may have "
            f"been reset. Marker re-synced to the current length; nothing shown."
        )

    new_content = content[last_len:]
    _save_marker(len(content), marker_file)
    if not new_content.strip():
        return None, f"[relay] Nothing new from {_SIDES[p]['label']}'s {label} since the last check."
    return new_content, ""


def read_new(peer: "str | None" = None) -> str:
    """Fetches the peer's current mailbox file, returns only the content
    added since the last successful read, and advances the marker. Default
    peer (None) is unchanged from before this function took the argument."""
    p = _resolve_peer(peer)
    new_content, message = _read_new_generic(_SIDES[p]["file"], _marker_file(p), "file", peer=p)
    return new_content if new_content is not None else message


def read_new_for_hub() -> str:
    """Same mailbox file as read_new(), but tracked through the independent
    hub marker cursor - see _hub_marker_file()'s comment for why this
    exists as a second cursor over the identical content rather than a
    third copy of the file itself. Air-only (the default peer) — hub notes
    have no meaning for a not-yet-bootstrapped peer like Intel/Ark."""
    new_content, message = _read_new_generic(_SIDES[_OTHER]["file"], _hub_marker_file(), "file")
    return new_content if new_content is not None else message


def append_note(text: str, flag: "str | None" = None, peer: "str | None" = None) -> str:
    """Appends a new dated section to THIS machine's own file. Always
    append mode — there is no code path in this function capable of
    overwriting prior entries, unlike a hand-run editor session where
    forgetting the right mode is one keystroke away.

    `flag`, if given, is written as a `**FLAG:** <value>` line directly
    under the entry header — currently only "needs-human" is a meaningful
    value (see `flagged()` and the module docstring), but this function
    doesn't validate the string, matching the rest of this file's stance
    that convention is enforced by what's checkable (append-only, the
    length cursor), not by validating free-text content.

    `peer` (2026-09-27): this machine has only ONE own file regardless of
    which peer a message is conceptually addressed to (from_m5.md), so
    `peer` doesn't change WHERE this writes — it exists only so a future
    per-peer addressing convention (e.g. a "To: <peer>" line) could be
    added here without changing every call site again. Currently unused
    beyond validating the name via _resolve_peer(), matching this file's
    existing "fail loud on an unknown peer" discipline."""
    _resolve_peer(peer)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    flag_line = f"**FLAG:** {flag}\n\n" if flag else ""
    section = f"\n## Entry — {date_str}\n\n{flag_line}{text.rstrip()}\n\n---\n"
    with open(_OWN_FILE, "a", encoding="utf-8") as f:
        f.write(section)
    return f"[relay] Appended to {os.path.basename(_OWN_FILE)} ({len(section)} chars)."


def flagged(peer: "str | None" = None) -> str:
    """Scans the peer's ENTIRE current mailbox file (not just content
    unread by the cursor) for entries carrying a FLAG line, and returns
    them in full. Deliberately not cursor-based — see module docstring's
    disclosed "no acknowledged state yet" limitation."""
    p = _resolve_peer(peer)
    content, err = _fetch_other_side(peer=p)
    if err is not None:
        return f"[relay] Could not reach {_SIDES[p]['label']}: {err}"

    entries = content.split("\n## Entry")
    flagged_entries = [
        "## Entry" + e for e in entries[1:] if _FLAG_PREFIX in e
    ]
    if not flagged_entries:
        return f"[relay] No flagged entries in {_SIDES[p]['label']}'s file."
    header = f"[relay] {len(flagged_entries)} flagged entr{'y' if len(flagged_entries) == 1 else 'ies'} in {_SIDES[p]['label']}'s file:\n"
    return header + "\n---\n".join(flagged_entries)


def add_fact(fact: str, evidence: str = "") -> str:
    """Appends one structured, checkable fact to THIS machine's own facts
    ledger — see module docstring for why this exists as a second file
    rather than folded into the prose mailbox."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "by": IDENTITY,
        "fact": fact,
        "evidence": evidence,
        "status": "confirmed",
    }
    with open(_OWN_FACTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return f"[relay] Added fact to {os.path.basename(_OWN_FACTS_FILE)}."


def read_new_facts(peer: "str | None" = None) -> str:
    """Same shape as read_new(), for the facts ledger — fetch, diff
    against the facts-specific cursor, advance it, return the new
    substring (raw JSONL lines) or an explanatory message."""
    p = _resolve_peer(peer)
    new_content, message = _read_new_generic(_other_facts_file(p), _facts_marker_file(p), "facts ledger", peer=p)
    return new_content if new_content is not None else message


def facts_status(peer: "str | None" = None) -> str:
    """Health check for the facts ledger, mirroring status()'s shape and
    its own privacy-safe stance (counts only, not full mailbox prose) —
    though facts ARE printed here in full, since by design they're short,
    structured, checkable claims meant to be read, not private
    conversation content the mailbox's own ground rule protects."""
    p = _resolve_peer(peer)
    lines = []

    own_facts = []
    try:
        with open(_OWN_FACTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        own_facts.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        pass
    lines.append(f"Own facts ({os.path.basename(_OWN_FACTS_FILE)}): {len(own_facts)} recorded.")

    content, err = _fetch_remote_file(_other_facts_file(p), peer=p)
    if err is not None:
        lines.append(f"{_SIDES[p]['label']} facts: UNREACHABLE right now ({err}).")
    else:
        other_lines = [l for l in content.splitlines() if l.strip()]
        marker = _load_marker(_facts_marker_file(p))
        unread = len(content) - marker.get("length", 0)
        lines.append(f"{_SIDES[p]['label']} facts: reachable, {len(other_lines)} recorded.")
        if unread > 0:
            lines.append(f"  -> {unread} chars unread since the last `facts-read` (marker last updated {marker.get('checked_at') or 'never'}).")
        elif unread < 0:
            lines.append(f"  -> marker is ahead of the live file by {-unread} chars (file may have been reset).")
        else:
            lines.append("  -> fully caught up.")

    if own_facts:
        lines.append("\nOwn recorded facts:")
        for r in own_facts:
            ev = f" [{r['evidence']}]" if r.get("evidence") else ""
            lines.append(f"  - ({r.get('status', '?')}) {r['fact']}{ev}")

    return "\n".join(lines)


def status(peer: "str | None" = None) -> str:
    """Structural health only — entry counts, reachability, staleness.
    Deliberately never prints the actual content of either file; matches
    this channel's own privacy rule (README.md) even when checking on it
    rather than participating in it."""
    p = _resolve_peer(peer)
    lines = [f"Identity: {IDENTITY} ({_SIDES[IDENTITY]['label']}) | Peer: {_SIDES[p]['label']}"]

    try:
        with open(_OWN_FILE, "r", encoding="utf-8") as f:
            own_content = f.read()
        own_entries = own_content.count("\n## Entry")
        lines.append(f"Own file ({_SIDES[IDENTITY]['file']}): {len(own_content)} chars, ~{own_entries} entries.")
    except FileNotFoundError:
        lines.append(f"Own file ({_SIDES[IDENTITY]['file']}): does not exist yet.")

    content, err = _fetch_other_side(peer=p)
    if err is not None:
        lines.append(f"{_SIDES[p]['label']}: UNREACHABLE right now ({err}).")
    else:
        other_entries = content.count("\n## Entry")
        marker = _load_marker(_marker_file(p))
        unread = len(content) - marker.get("length", 0)
        lines.append(f"{_SIDES[p]['label']}: reachable, {len(content)} chars, ~{other_entries} entries.")
        if unread > 0:
            lines.append(f"  -> {unread} chars unread since the last `read` (marker last updated {marker.get('checked_at') or 'never'}).")
        elif unread < 0:
            lines.append(f"  -> marker is ahead of the live file by {-unread} chars (file may have been reset).")
        else:
            lines.append("  -> fully caught up.")

    return "\n".join(lines)


def _extract_flag_value(args: "list[str]", flag: str) -> "tuple[list[str], str | None]":
    """Pulls `--flag value` out of an arg list anywhere in it, returning the
    remaining args and the value (or None if absent). Shared by --peer and
    the pre-existing --flag/--evidence extraction below, which used to be
    inlined per-command; factored out here only because --peer now needs
    the identical pattern in every command, not a behavior change for the
    pre-existing flags."""
    if flag not in args:
        return args, None
    i = args.index(flag)
    if i + 1 >= len(args):
        return args, "__MISSING__"
    val = args[i + 1]
    return args[:i] + args[i + 2:], val


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    argv = sys.argv[2:]

    # --peer <name> (2026-09-27): extracted first, from anywhere in the
    # remaining args, before each command's own flag parsing runs — so
    # e.g. `relay.py read --peer intel` and `relay.py append "text" --peer
    # intel --flag needs-human` both work regardless of position. Absent
    # entirely (the pre-existing, still-default case): peer_val is None,
    # every function below falls back to _OTHER exactly as before this
    # extension existed.
    argv, peer_val = _extract_flag_value(argv, "--peer")
    if peer_val == "__MISSING__":
        print("Usage: ... --peer <name>  (known peers: " + ", ".join(k for k in _SIDES if k != IDENTITY) + ")")
        sys.exit(1)
    try:
        if peer_val is not None:
            _resolve_peer(peer_val)  # fail loud now, not deep inside a command
    except ValueError as e:
        print(f"[relay] {e}")
        sys.exit(1)

    if cmd == "status":
        print(status(peer=peer_val))
    elif cmd == "read":
        print(read_new(peer=peer_val))
    elif cmd == "read-hub":
        print(read_new_for_hub())
    elif cmd == "append":
        if not argv:
            print("Usage: python3 claude_relay/relay.py append \"text\" [--flag needs-human] [--peer <name>]")
            sys.exit(1)
        text = argv[0]
        rest, flag_val = _extract_flag_value(argv[1:], "--flag")
        if flag_val == "__MISSING__":
            print("Usage: python3 claude_relay/relay.py append \"text\" --flag <value>")
            sys.exit(1)
        print(append_note(text, flag=flag_val, peer=peer_val))
    elif cmd == "flagged":
        print(flagged(peer=peer_val))
    elif cmd == "fact":
        if not argv:
            print("Usage: python3 claude_relay/relay.py fact \"text\" [--evidence \"...\"]")
            sys.exit(1)
        text = argv[0]
        rest, evidence_val = _extract_flag_value(argv[1:], "--evidence")
        if evidence_val == "__MISSING__":
            print("Usage: python3 claude_relay/relay.py fact \"text\" --evidence \"...\"")
            sys.exit(1)
        print(add_fact(text, evidence=evidence_val or ""))
    elif cmd == "facts":
        print(facts_status(peer=peer_val))
    elif cmd == "facts-read":
        print(read_new_facts(peer=peer_val))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
