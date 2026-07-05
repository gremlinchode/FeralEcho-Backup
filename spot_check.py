#!/usr/bin/env python3
"""
spot_check.py — Human spot-check ratings for council-flagged responses.

Reads memory/council_ratings.jsonl, presents every entry with
spot_check_required=true and no human_spot_check_rating yet, asks for a
1-5 rating via plain blocking input(), and writes the result back in
place atomically.  Cross-references memory/interaction_log.jsonl to show
the full response text when available.

Run from the project root:
    python spot_check.py
"""

import json
import sys
from pathlib import Path

COUNCIL_LOG     = Path("memory/council_ratings.jsonl")
INTERACTION_LOG = Path("memory/interaction_log.jsonl")


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_council() -> list[tuple[int, dict]]:
    if not COUNCIL_LOG.exists():
        return []
    with open(COUNCIL_LOG, encoding="utf-8") as f:
        raw = f.readlines()
    result = []
    for i, line in enumerate(raw):
        line = line.strip()
        if not line:
            continue
        try:
            result.append((i, json.loads(line)))
        except json.JSONDecodeError:
            pass
    return result


def _pending(entries: list[tuple[int, dict]]) -> list[tuple[int, dict]]:
    return [
        (i, e) for i, e in entries
        if e.get("spot_check_required") and e.get("human_spot_check_rating") is None
    ]


def _lookup_interaction(source_ts: str) -> dict | None:
    """Find the original interaction_log entry by source_timestamp.

    Returns the entry dict.  Prefers 'prompt'/'response' (full text) over
    'prompt_preview'/'response_preview' when both are present — full fields
    are written once log_interaction() is updated to store them.
    """
    if not INTERACTION_LOG.exists() or not source_ts:
        return None
    try:
        with open(INTERACTION_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    if e.get("timestamp", "") == source_ts:
                        return e
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return None


def _page_text(label: str, text: str, width: int = 72, page_lines: int = 40) -> None:
    """Print text with optional pagination when it's long."""
    lines = text.splitlines() if "\n" in text else [text]
    if len(lines) <= page_lines:
        print(f"  {label}:")
        for ln in lines:
            print(f"    {ln}")
        return
    # Long: paginate
    print(f"  {label}: ({len(lines)} lines — press Enter to page through, 'q' to skip)")
    i = 0
    while i < len(lines):
        chunk = lines[i : i + page_lines]
        for ln in chunk:
            print(f"    {ln}")
        i += page_lines
        if i < len(lines):
            try:
                key = input(f"  [{i}/{len(lines)} lines shown — Enter for more, 'q' to stop] ").strip()
            except (EOFError, KeyboardInterrupt):
                return
            if key == "q":
                return


def _write_back(line_index: int, rating: int) -> None:
    """Atomically rewrite council_ratings.jsonl with one entry updated."""
    with open(COUNCIL_LOG, encoding="utf-8") as f:
        lines = f.readlines()
    entry = json.loads(lines[line_index])
    entry["human_spot_check_rating"] = rating
    lines[line_index] = json.dumps(entry) + "\n"
    tmp = COUNCIL_LOG.with_suffix(".tmp")
    tmp.write_text("".join(lines), encoding="utf-8")
    tmp.replace(COUNCIL_LOG)


def _divider(label: str = "") -> None:
    width = 72
    if label:
        pad = (width - len(label) - 2) // 2
        print("─" * pad + f" {label} " + "─" * (width - pad - len(label) - 2))
    else:
        print("─" * width)


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    all_entries = _load_council()
    pending     = _pending(all_entries)

    if not pending:
        if not COUNCIL_LOG.exists():
            print("memory/council_ratings.jsonl does not exist yet.")
            print("The council rater thread needs to produce entries before spot-checks are available.")
        else:
            print(f"No pending spot-checks in {COUNCIL_LOG}.")
        return

    total = len(pending)
    print(f"\n{total} spot-check{'s' if total != 1 else ''} pending.\n")

    for done, (line_idx, entry) in enumerate(pending):
        remaining_after = total - done - 1
        _divider(f"{done + 1} of {total}")

        ts        = entry.get("timestamp_utc", "")[:19]
        src_ts    = entry.get("source_timestamp", "")
        task      = entry.get("task_type", "?")
        model     = entry.get("model_used", "?")
        auto_r    = entry.get("council_rating", "?")
        auto_m    = entry.get("council_rating_model", "?")
        reason    = entry.get("council_rationale_preview", "")
        q_score   = entry.get("quality_score", "?")

        print(f"  Rated at:     {ts} UTC")
        print(f"  Task type:    {task}")
        print(f"  Model:        {model}")
        print(f"  Qual score:   {q_score} / 5  (system metric)")
        print(f"  Peer rating:  {auto_r} / 5  (by {auto_m})")
        print(f"  Peer reason:  {reason}")
        print()

        # Show prompt and response — prefer full fields over *_preview if stored.
        # NOTE: log_interaction() currently stores only 120/200-char previews.
        # Once it is updated to also write 'prompt' and 'response' full fields,
        # this block will automatically use them without further changes.
        interaction = _lookup_interaction(src_ts)
        if interaction:
            prompt_text   = interaction.get("prompt")   or interaction.get("prompt_preview",   "")
            response_text = interaction.get("response") or interaction.get("response_preview", "")
            if prompt_text:
                _page_text("Prompt", prompt_text)
            if response_text:
                _page_text("Response", response_text)
            if not interaction.get("prompt") and not interaction.get("response"):
                print("  [NOTE: interaction log stores 120/200-char previews only —")
                print("   authorize log_interaction() fix to see full text here]")
        else:
            print("  [Full text not available — entry not found in interaction_log]")

        print()

        while True:
            try:
                raw = input(f"  Your rating [1-5], Enter to skip, 'q' to quit: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInterrupted. Remaining spot-checks preserved.")
                return

            if raw == "q":
                print("Exiting. Remaining spot-checks preserved.")
                return
            if raw == "":
                print("  Skipped.\n")
                break
            if raw in {"1", "2", "3", "4", "5"}:
                _write_back(line_idx, int(raw))
                suffix = f"{remaining_after} remaining after this." if remaining_after else "All done."
                print(f"  Rating {raw} saved. {suffix}\n")
                break
            print("  Enter 1–5, press Enter to skip, or 'q' to quit.")

    _divider()
    print("All pending spot-checks reviewed.")


if __name__ == "__main__":
    main()
