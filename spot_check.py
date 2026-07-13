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

import ast
import json
import sys
from pathlib import Path

COUNCIL_LOG       = Path("memory/council_ratings.jsonl")
INTERACTION_LOG   = Path("memory/interaction_log.jsonl")
CONVERGENCE_STATE = Path("app/core/self_edit_convergence.json")


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


def _write_back(line_index: int, rating: int, expected_source_ts: str) -> bool:
    """Atomically rewrite council_ratings.jsonl with one entry updated.

    Verifies the line at line_index still matches the entry the user was
    actually looking at (by source_timestamp) before writing — the raw
    index was captured once at the start of the run, and nothing
    previously re-checked it against the current file state. Today's real
    writers (the background rating thread only appends; fill_spot_check()
    mutates one line in place without reordering) happen to keep indices
    stable, but a future writer that inserts or reorders lines would
    otherwise silently write the rating onto the wrong record. Falls back
    to a full scan by source_timestamp if the index has drifted. Returns
    False (and writes nothing) if the entry can't be found at all.
    """
    with open(COUNCIL_LOG, encoding="utf-8") as f:
        lines = f.readlines()

    target_idx = line_index
    if not (0 <= target_idx < len(lines)):
        target_idx = -1
    else:
        try:
            candidate = json.loads(lines[target_idx])
        except json.JSONDecodeError:
            candidate = {}
        if candidate.get("source_timestamp") != expected_source_ts:
            target_idx = -1

    if target_idx == -1:
        for i, raw in enumerate(lines):
            try:
                if json.loads(raw).get("source_timestamp") == expected_source_ts:
                    target_idx = i
                    break
            except json.JSONDecodeError:
                continue

    if target_idx == -1:
        return False

    entry = json.loads(lines[target_idx])
    if entry.get("human_spot_check_rating") is not None:
        # Already rated by someone/something else since this run's pending
        # list was computed (e.g. the admin API) — unlike
        # council_rater.py's own fill_spot_check(), which already guards
        # this, this call site previously had no such check and would
        # silently overwrite a real concurrent rating.
        return False
    entry["human_spot_check_rating"] = rating
    lines[target_idx] = json.dumps(entry) + "\n"
    tmp = COUNCIL_LOG.with_suffix(".tmp")
    tmp.write_text("".join(lines), encoding="utf-8")
    tmp.replace(COUNCIL_LOG)
    return True


# ── coding-task plain-English review ────────────────────────────────────────
# Rating self-edit code candidates by eye requires reading Python — not
# something every human rater can do. These helpers turn a code snippet into
# things a non-programmer can actually judge: does it even parse, has this
# exact idea already been tried dozens of times before, and what does it
# claim to do in plain language.

def _ast_check(code: str) -> tuple[bool, str]:
    """Does this parse as valid Python at all? Deterministic, no model needed."""
    try:
        ast.parse(code)
        return True, "Parses as valid Python."
    except SyntaxError as e:
        return False, f"Does NOT parse as valid Python — {e}"


def _extract_def_names(code: str) -> list[str]:
    """Function/method/class names defined in this candidate, via AST walk."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
    return names


def _convergence_context(def_names: list[str]) -> str:
    """How many times has this specific idea already been attempted?

    Cross-references the self-edit convergence tracker's per-family
    all_names_seen list — the same repetition pattern a technical reviewer
    would use to judge "is this actually new" without reading the code.
    """
    if not def_names or not CONVERGENCE_STATE.exists():
        return ""
    try:
        state = json.loads(CONVERGENCE_STATE.read_text(encoding="utf-8"))
    except Exception:
        return ""
    hits = []
    for family, data in state.items():
        seen = set(data.get("all_names_seen") or [])
        matched = [n for n in def_names if n in seen]
        if matched:
            hits.append((family, matched, data.get("cycles_attempted", "?")))
    if not hits:
        return "  Novelty check: none of these names appear in prior self-edit history — looks like a new idea."
    lines = ["  Novelty check:"]
    for family, matched, attempted in hits:
        lines.append(
            f"    - {', '.join(matched)} already appears in the '{family}' family's history "
            f"({attempted} cycles attempted on this family so far)."
        )
    return "\n".join(lines)


def _plain_english_summary(code: str, prompt_hint: str) -> str | None:
    """Ask a local model to explain the code in plain English, no code-reading required.

    Returns None on any failure — callers must fall back to showing raw text,
    never block the rating flow on this.
    """
    try:
        from app.ollama_handler import query_ollama
    except Exception:
        return None

    ask = (
        "Explain what this Python code does in 2-3 plain-English sentences. "
        "Assume the reader cannot read Python at all — do not quote or reference "
        "any code syntax, variable names, or function names in your answer. "
        "Just describe the behavior in everyday language. "
        "If the code looks incomplete or cut off, say so explicitly.\n\n"
    )
    if prompt_hint and prompt_hint.strip() not in ("[SANDBOX]", ""):
        ask += f"Context for what it was supposed to do: {prompt_hint.strip()[:300]}\n\n"
    ask += f"Code:\n{code[:3000]}"

    try:
        result = query_ollama(ask, timeout=90)
    except Exception:
        return None
    if not result or result.startswith("[ERROR]"):
        return None
    return result.strip()


def _review_coding_candidate(code: str, prompt_hint: str) -> None:
    """Print the plain-English review block for a coding-task spot-check entry."""
    valid, ast_msg = _ast_check(code)
    print(f"  {ast_msg}")
    if valid:
        names = _extract_def_names(code)
        conv = _convergence_context(names)
        if conv:
            print(conv)
        print("  Generating plain-English summary...")
        summary = _plain_english_summary(code, prompt_hint)
        if summary:
            print("  What this code does (plain English):")
            for line in summary.splitlines():
                print(f"    {line}")
        else:
            print("  [Could not generate a plain-English summary — Ollama unavailable or errored.")
            print("   Rate based on the novelty check above, or skip this entry.]")
    print()


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

            if task == "coding" and response_text:
                _divider("plain-English review")
                _review_coding_candidate(response_text, prompt_text)
                _divider()

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
                ok = _write_back(line_idx, int(raw), src_ts)
                if not ok:
                    print("  Not saved — entry was already rated or could not be found (log may have changed).\n")
                    break
                suffix = f"{remaining_after} remaining after this." if remaining_after else "All done."
                print(f"  Rating {raw} saved. {suffix}\n")
                break
            print("  Enter 1–5, press Enter to skip, or 'q' to quit.")

    _divider()
    print("All pending spot-checks reviewed.")


if __name__ == "__main__":
    main()
