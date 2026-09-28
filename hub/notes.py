#!/usr/bin/env python3
"""hub/notes.py — a shared, multi-party notes/ideas board for the agents
operating on FeralEcho (M5 + Air), layered on top of the already-existing
relay channels rather than inventing a new network protocol or secret.

Not a FeralEcho subsystem: not imported by app/ or run.py, not subject to
EDIT_FORBIDDEN_TARGETS or the Liveness Ledger — operator/session tooling,
same category as claude_relay/relay.py and codex_relay/relay.py.

Distinct from hub/status.jsonl (pure liveness facts, never content) and
from claude_relay/codex_relay (strictly pairwise, private mailboxes). This
is a genuinely shared board: any local node can post a note, and any node
- on this machine or the other - can eventually read it, without needing
a live connection to anyone at the moment of posting or reading.

No human/operator node in the schema - author and audience are always one
of the six agent identities (or "all"), by explicit instruction: Gremlin
interacts with each agent directly and doesn't need a seat in this ledger.

DESIGN: cross-machine delivery always rides claude_relay, regardless of
which local node authored the note. Not because claude_relay "owns" hub
content, but because it's the one channel already used for exactly this
"a Claude session coordinates on behalf of everyone else on this machine"
pattern (see CLAUDE.md Finding 86's own precedent). codex_relay is
deliberately left untouched - its own README states it is "intentionally
independent of FeralEcho and the claude relay," and mixing generic hub
traffic into it would blur that stated boundary.

Usage:
    python3 hub/notes.py post --author codex-m5 --audience all \\
        --title "idea" [--body "text" | reads stdin if --body omitted]
    python3 hub/notes.py read [--author NODE] [--audience NODE] [-n 20]
    python3 hub/notes.py pull
        # Calls claude_relay's own `read` (advances the SAME shared marker
        # a manual `claude_relay/relay.py read` would - this is not a new
        # risk, it's the existing single-cursor-per-side semantics that
        # channel already has), extracts any [HUB-NOTE v1] blocks found in
        # the new content, appends them into the local ledger, and still
        # prints everything raw so nothing is silently hidden.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HUB_DIR = Path(__file__).resolve().parent
NOTES_LOG = HUB_DIR / "notes.jsonl"

NODES = {"claude-m5", "claude-air", "codex-m5", "codex-air", "echo-m5", "echo-air"}
AUDIENCES = NODES | {"all"}

NOTE_TAG = "[HUB-NOTE v1]"
_NOTE_BLOCK_RE = re.compile(
    re.escape(NOTE_TAG) + r"\n"
    r"author: (?P<author>[^\n]+)\n"
    r"audience: (?P<audience>[^\n]+)\n"
    r"title: (?P<title>[^\n]+)\n"
    r"timestamp: (?P<timestamp>[^\n]+)\n"
    r"---\n"
    r"(?P<body>.*?)(?=\n\[HUB-NOTE v1\]|\Z)",
    re.DOTALL,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def note_id(entry: dict) -> str:
    # Stable identity for dedup on pull - same (author, timestamp, title)
    # should never be double-appended even if the same relay content is
    # pulled twice (e.g. a marker reset, or two sessions both running pull).
    raw = f"{entry['author']}|{entry['timestamp']}|{entry['title']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_existing_ids() -> set[str]:
    if not NOTES_LOG.exists():
        return set()
    ids = set()
    for line in NOTES_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        ids.add(entry.get("id") or note_id(entry))
    return ids


def append_local(entry: dict) -> bool:
    """Append one note locally. Returns False (no-op) if this id already exists."""
    existing = load_existing_ids()
    entry_id = note_id(entry)
    if entry_id in existing:
        return False
    entry["id"] = entry_id
    with NOTES_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


def format_relay_block(entry: dict) -> str:
    return (
        f"{NOTE_TAG}\n"
        f"author: {entry['author']}\n"
        f"audience: {entry['audience']}\n"
        f"title: {entry['title']}\n"
        f"timestamp: {entry['timestamp']}\n"
        f"---\n"
        f"{entry['body']}"
    )


def push_via_claude_relay(entry: dict) -> tuple[bool, str]:
    block = format_relay_block(entry)
    result = subprocess.run(
        ["python3", "claude_relay/relay.py", "append", block],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=15,
    )
    ok = result.returncode == 0
    output = (result.stdout or "") + (result.stderr or "")
    return ok, output.strip()


def cmd_post(args: argparse.Namespace) -> int:
    if args.author not in NODES:
        print(f"error: --author must be one of {sorted(NODES)}", file=sys.stderr)
        return 2
    if args.audience not in AUDIENCES:
        print(f"error: --audience must be one of {sorted(AUDIENCES)}", file=sys.stderr)
        return 2
    body = args.body if args.body is not None else sys.stdin.read()
    if not body.strip():
        print("error: refusing to post an empty note", file=sys.stderr)
        return 2
    if not args.title.strip():
        print("error: --title is required and cannot be empty", file=sys.stderr)
        return 2

    entry = {
        "timestamp": now(),
        "author": args.author,
        "audience": args.audience,
        "title": args.title.strip(),
        "body": body.rstrip(),
    }
    added = append_local(entry)
    if not added:
        print("note: identical (author, timestamp, title) already in the local ledger - not re-appended")
    else:
        print(f"Posted locally: [{entry['id']}] {entry['author']} -> {entry['audience']}: {entry['title']}")

    needs_cross_machine = args.audience == "all" or args.audience.endswith("-air")
    if needs_cross_machine:
        ok, output = push_via_claude_relay(entry)
        if ok:
            print("Pushed to Air via claude_relay (they'll see it next time they `pull`).")
        else:
            print(f"WARNING: local post succeeded but claude_relay push failed: {output}", file=sys.stderr)
            return 1
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    if not NOTES_LOG.exists():
        print("(no notes yet)")
        return 0
    entries = []
    for line in NOTES_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if args.author:
        entries = [e for e in entries if e.get("author") == args.author]
    if args.audience:
        entries = [e for e in entries if e.get("audience") in (args.audience, "all")]
    entries = entries[-args.n:]
    if not entries:
        print("(nothing matches)")
        return 0
    for e in entries:
        print(f"\n## [{e.get('id', '?')}] {e['author']} -> {e['audience']} — {e['timestamp']}\n### {e['title']}\n")
        print(e["body"])
    return 0


def cmd_pull(args: argparse.Namespace) -> int:
    # Uses claude_relay's own independent `read-hub` cursor (added
    # 2026-09-16, proposed by Air), not the plain `read` cursor - a manual
    # `claude_relay/relay.py read` and this pull no longer compete for or
    # silently consume the same "what's new" position over the same file.
    result = subprocess.run(
        ["python3", "claude_relay/relay.py", "read-hub"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=15,
    )
    output = (result.stdout or "") + (result.stderr or "")
    print("--- raw claude_relay read-hub output (unfiltered) ---")
    print(output)
    print("--- end raw output ---\n")

    if result.returncode != 0:
        print(f"claude_relay read-hub failed (exit {result.returncode}); nothing pulled into notes.jsonl", file=sys.stderr)
        return 1

    matches = list(_NOTE_BLOCK_RE.finditer(output))
    if not matches:
        print("No [HUB-NOTE v1] blocks found in the new content.")
        return 0

    added, skipped = 0, 0
    for m in matches:
        entry = {
            "timestamp": m.group("timestamp").strip(),
            "author": m.group("author").strip(),
            "audience": m.group("audience").strip(),
            "title": m.group("title").strip(),
            "body": m.group("body").strip(),
        }
        if append_local(entry):
            added += 1
        else:
            skipped += 1
    print(f"Pulled {added} new note(s) into hub/notes.jsonl ({skipped} already present).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    post_p = sub.add_parser("post")
    post_p.add_argument("--author", required=True)
    post_p.add_argument("--audience", required=True)
    post_p.add_argument("--title", required=True)
    post_p.add_argument("--body", default=None, help="If omitted, body is read from stdin.")
    post_p.set_defaults(func=cmd_post)

    read_p = sub.add_parser("read")
    read_p.add_argument("--author", default=None)
    read_p.add_argument("--audience", default=None)
    read_p.add_argument("-n", type=int, default=20, help="Show at most the last N matching notes.")
    read_p.set_defaults(func=cmd_read)

    pull_p = sub.add_parser("pull")
    pull_p.set_defaults(func=cmd_pull)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
