#!/usr/bin/env python3
# scrub_garden.py
# ============================================================
# One-time Question Garden cleanup script.
# Run from ~/Desktop/FeralEcho/ with the feral_echo env active.
#
# What it does:
#   - Loads all active garden entries
#   - Composted entries that are clearly not genuine questions:
#       * No question mark
#       * Too short (under 20 chars)
#       * Start with flattery/filler openers
#       * Are statements masquerading as questions
#   - Reports what was kept vs composted
#   - Leaves resolved/already-composted entries untouched
# ============================================================

import json
import time
from pathlib import Path

GARDEN_PATH = Path("data/question_garden.jsonl")

FLATTERY_OPENERS = (
    "i'm delighted",
    "i'm glad",
    "what a ",
    "i'm honored",
    "i'm grateful",
    "certainly",
    "of course",
    "absolutely",
    "i would be",
    "i'd be happy",
    "great question",
    "i'm excited",
    "i'm pleased",
    "wonderful",
    "fantastic",
    "that's a great",
    "i appreciate",
    "thank you for",
    "i'm happy to",
    "as an ai",
    "as echo",
    "the natural flow",
    "i'm looking forward",
    "i'm thrilled",
    "i'm so glad",
    "what an interesting",
    "what an exciting",
    "i love that",
    "i'm overjoyed",
)

STATEMENT_OPENERS = (
    "i believe",
    "i think",
    "i feel",
    "i know",
    "i understand",
    "i realize",
    "i've come to",
    "it's important",
    "it's essential",
    "it seems",
    "this is",
    "these are",
    "there are",
    "there is",
    "we should",
    "we can",
    "we must",
    "you should",
    "you can",
)


def is_genuine_question(entry: dict) -> tuple[bool, str]:
    """
    Returns (keep: bool, reason: str).
    """
    q = entry.get("question", "").strip()
    lower = q.lower()

    # Must have content
    if not q:
        return False, "empty"

    # Must be long enough to be meaningful
    if len(q) < 20:
        return False, f"too short ({len(q)} chars)"

    # Must contain a question mark
    if "?" not in q:
        return False, "no question mark"

    # Must not start with flattery
    for opener in FLATTERY_OPENERS:
        if lower.startswith(opener):
            return False, f"flattery opener: '{opener}'"

    # Must not be a statement with a question mark tacked on
    for opener in STATEMENT_OPENERS:
        if lower.startswith(opener):
            return False, f"statement opener: '{opener}'"

    # Reject if question mark only appears at end of a very long statement
    # (genuine questions tend to have the ? earlier or as the main verb)
    first_sentence_end = min(
        q.find(".") if "." in q else len(q),
        q.find("!") if "!" in q else len(q),
    )
    if first_sentence_end < len(q) - 5 and "?" not in q[:first_sentence_end]:
        # Statement followed by a question — likely contaminated
        pass  # soft signal only, don't reject on this alone

    return True, "ok"


def scrub_garden(dry_run: bool = False):
    if not GARDEN_PATH.exists():
        print(f"[SCRUB] Garden not found at {GARDEN_PATH}")
        return

    with open(GARDEN_PATH, "r") as f:
        raw_lines = f.readlines()

    entries = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception as e:
            print(f"[SCRUB] Skipping malformed line: {e}")

    total = len(entries)
    kept = []
    composted = []

    for entry in entries:
        status = entry.get("status", "active")

        # Don't touch already resolved or composted
        if status in ("resolved", "composted"):
            kept.append(entry)
            continue

        keep, reason = is_genuine_question(entry)

        if keep:
            kept.append(entry)
        else:
            entry["status"] = "composted"
            entry["compost_reason"] = reason
            entry["composted_at"] = time.time()
            composted.append(entry)
            print(f"  [COMPOST] {reason:40s} | {entry['question'][:80]}")

    active_kept = sum(1 for e in kept if e.get("status") == "active")
    print(f"\n[SCRUB] Results:")
    print(f"  Total entries   : {total}")
    print(f"  Kept (active)   : {active_kept}")
    print(f"  Kept (other)    : {len(kept) - active_kept}")
    print(f"  Composted       : {len(composted)}")

    if dry_run:
        print(f"\n[SCRUB] DRY RUN — no changes written.")
        return

    # Write all entries back (kept + composted with updated status)
    all_entries = kept + composted
    GARDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GARDEN_PATH, "w") as f:
        for entry in all_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"\n[SCRUB] Garden scrubbed. {len(composted)} entries composted.")
    print(f"[SCRUB] {active_kept} genuine questions remain active.")


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("[SCRUB] Running in DRY RUN mode — no changes will be written.\n")
    else:
        print("[SCRUB] Running live scrub — garden will be modified.\n")

    scrub_garden(dry_run=dry_run)
