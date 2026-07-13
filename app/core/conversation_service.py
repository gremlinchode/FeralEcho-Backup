"""Shared conversation-service helpers.

Extracted from terminal_client.py (behavior-preserving — see
Echo Studio Phase 1 plan) so both the terminal client (one global session)
and Echo Studio (one session per conversation tab) can build prompts and
manage session history without duplicating logic. Functions take state as
parameters instead of closing over module globals.

Not on EDIT_FORBIDDEN_TARGETS — freely editable.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import requests

# terminal_client.py runs as a separate process from run.py's Flask server,
# so it needs its own .env load to read GREMLIN_SECRET for save_turn_to_server()
# below — routes_echo_studio.py's in-process callers already have it loaded
# by run.py, but this call is a no-op (setdefault-style via load_dotenv's
# override=False default) in that case, so it's safe either way.
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

SERVER_URL_DEFAULT = "http://127.0.0.1:5000"
HISTORY_TOKEN_BUDGET_DEFAULT = 4000

_DEFAULT_PID_FILE = Path("memory/echo_server.pid")


def server_is_running(pid_file: Path = _DEFAULT_PID_FILE) -> bool:
    """True if the Flask server process wrote a PID file and is still alive."""
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # signal 0: existence check only
        return True
    except (ValueError, OSError):
        return False


def clean_response_text(raw_response: str) -> str:
    """Clean token spacing artifacts (moved from terminal_client.py, unchanged)."""
    return (
        raw_response
        .replace(" .", ".")
        .replace(" ,", ",")
        .replace(" :", ":")
        .replace(" ;", ";")
        .replace(" ?", "?")
        .replace(" !", "!")
        .replace(" (", "(")
        .replace("( ", "(")
        .replace(" )", ")")
        .replace(" _", "_")
        .replace("_ ", "_")
        .replace("  ", " ")
        .strip()
    )


def _parse_ts(ts: str):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError, TypeError):
        return None


def retrieve_memory_context(
    msg: str,
    search_fn: Callable[[str, int], list],
    k: int = 5,
    exclude_recent_minutes: float = 30.0,
) -> str:
    """
    Retrieve semantically relevant memories and format them for prompt injection.

    search_fn(query, k) must return a list of (text, score, meta) tuples, most
    relevant first — callers plug in whatever search backend they already have
    (terminal_client.py's local VectorMemory, or the server's memory_bridge).

    Excludes autonomous-sourced entries when falling back: news/fetch content
    must never be presented to the model as personal history (Finding 14,
    2026-07-02 — the model treats unlabeled retrieved text as first-person memory).

    Excludes anything newer than `exclude_recent_minutes` — session history
    (format_history_block) already covers that window, so re-surfacing a very
    recent turn as "memory" risks the model treating its own last answer as
    settled precedent and repeating it (confirmed live 2026-07-05: a deflected
    answer got retrieved as [past interaction] context on the very next
    attempt at a similar question, reinforcing the same deflection).
    """
    try:
        raw_memories = search_fn(msg, k * 3)
        if not raw_memories:
            return ""

        if exclude_recent_minutes > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=exclude_recent_minutes)
            raw_memories = [
                (text, score, meta) for text, score, meta in raw_memories
                if not ((_parse_ts(meta.get("timestamp", "")) or cutoff) > cutoff)
            ]
            if not raw_memories:
                return ""

        conv_memories = [
            (text, score, meta) for text, score, meta in raw_memories
            if meta.get("memory_source") == "user_conversation"
        ]
        # != "autonomous" trivially passed for any untagged/legacy entry too
        # (missing memory_source -> None -> None != "autonomous" is True),
        # so entries that were never tagged at all bypassed the exclusion
        # this fallback exists to enforce. Require an explicit, real,
        # non-autonomous tag instead of merely "not literally 'autonomous'".
        non_autonomous = [
            (text, score, meta) for text, score, meta in raw_memories
            if meta.get("memory_source") not in (None, "", "autonomous")
        ]
        relevant_memories = (
            conv_memories[:k] if len(conv_memories) >= k else non_autonomous[:k]
        )

        def _source_label(meta: dict) -> str:
            src = meta.get("memory_source", "")
            role = meta.get("role", "")
            if src == "user_conversation" and role in ("user", "echo"):
                return "[past interaction]"
            elif src == "user_conversation":
                return "[reference]"
            else:
                return "[system log]"

        return "\n".join([
            f"- {_source_label(meta)}: {text}"
            for text, score, meta in relevant_memories
        ])
    except Exception:
        return ""


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def history_token_count(conv_history: list, history_summaries: list) -> int:
    turn_tokens = sum(
        est_tokens(t["user"]) + est_tokens(t["echo"]) for t in conv_history
    )
    summary_tokens = sum(est_tokens(s) for s in history_summaries)
    return turn_tokens + summary_tokens + 50  # 50-token overhead for formatting


def format_history_block(conv_history: list, history_summaries: list) -> str:
    """Render session history for prompt injection. Returns '' if no history."""
    if not conv_history and not history_summaries:
        return ""

    parts = []
    n_compressed = len(history_summaries)

    if history_summaries:
        parts.append("[Earlier in this conversation — compressed:]")
        for s in history_summaries:
            parts.append(f"  {s}")

    turn_offset = n_compressed + 1
    for i, turn in enumerate(conv_history):
        turn_num = turn_offset + i
        ts_short = turn["ts"][:19].replace("T", " ")
        parts.append(f"Turn {turn_num} [{ts_short} UTC]:")
        parts.append(f"  You: {turn['user']}")
        parts.append(f"  Echo: {turn['echo']}")

    inner = "\n".join(parts)
    return (
        "[Conversation history — this session]\n"
        + inner
        + "\n[End of conversation history]"
    )


def build_context_system_note(history_block: str, memory_block: str) -> str:
    """Wrap session history + retrieved memory as an explicitly-disclaimed
    system note, instead of splicing them into the user-turn message text.

    Previously both were concatenated directly ahead of the live question
    (full_msg = history_block + "\\n\\n" + full_msg) with no role boundary —
    a raw "Turn N: You: ... Echo: ..." transcript sitting immediately before
    the real question. Confirmed live (2026-07-12, Echo Studio): local
    models under this shape sometimes pattern-match the transcript and
    regurgitate the most recent Echo turn verbatim instead of answering the
    new question — reproduced identically across three separate councillor
    models in one turn. Framing this as a disclaimed system note (same
    pattern as the ground_truth/tool_ctx fix) gives the model an explicit
    instruction not to continue it, and keeps the user turn as just the
    actual question.
    """
    parts = []
    if memory_block:
        parts.append(
            "Retrieved context (past interactions and system logs — not "
            "assertions about identity, not something being said to you "
            "right now):\n" + memory_block
        )
    if history_block:
        parts.append("Prior turns in this conversation, for continuity only:\n" + history_block)
    if not parts:
        return ""
    return (
        "\n\n".join(parts)
        + "\n\nThe above is background only. Do not repeat, continue, or "
        "quote it back verbatim. Respond only to the user's new message below."
    )


def store_turn_in_history(
    conv_history: list,
    history_summaries: list,
    user_msg: str,
    echo_response: str,
    token_budget: int = HISTORY_TOKEN_BUDGET_DEFAULT,
) -> tuple:
    """Add a completed turn. If over budget, compress-and-drop the oldest turn.

    Mutates and returns (conv_history, history_summaries).
    """
    conv_history.append({
        "ts": datetime.utcnow().isoformat(),
        "user": user_msg,
        "echo": echo_response,
    })

    while (
        history_token_count(conv_history, history_summaries) > token_budget
        and len(conv_history) > 1
    ):
        oldest = conv_history.pop(0)
        q = oldest["user"]
        topic = q[:60] + ("..." if len(q) > 60 else "")
        history_summaries.append(f'You asked: "{topic}"')

    return conv_history, history_summaries


def save_turn_to_server(
    user_msg: str,
    echo_response: str,
    task_type: str,
    server_url: str = SERVER_URL_DEFAULT,
    require_server_check: bool = True,
) -> None:
    """POST a conversation turn to the server for FAISS persistence.

    Silent on all errors — never blocks the conversation. require_server_check
    exists because terminal_client.py runs as a separate process and must
    confirm the server is alive before POSTing; callers already running inside
    the Flask process (e.g. routes_echo_studio.py) can skip the check.
    """
    if require_server_check and not server_is_running():
        return
    try:
        requests.post(
            f"{server_url}/memory/conversation",
            json={
                "user_msg": user_msg,
                "echo_response": echo_response,
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat(),
                "secret": os.environ.get("GREMLIN_SECRET"),
            },
            timeout=3,
        )
    except Exception:
        pass
