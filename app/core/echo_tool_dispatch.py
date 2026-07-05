# app/core/echo_tool_dispatch.py
# ============================================================
# TOOL DISPATCH LOOP — genuine agency for Echo
# ============================================================
# Uses llama3.1:8b as the dispatch model (NOT echo:latest).
# Every tool-call decision is made by llama3.1:8b and logged
# with that model name so attribution is always traceable.
#
# Tool-call decisions: llama3.1:8b
# Response synthesis: llama3.1:8b (dispatch model answers directly)
# Echo's voice layer: can be added on top in a future pass
#
# Tools (read-only or reversible):
#   read_file(path)          — path-guarded to project root
#   search_memory(query)     — FAISS semantic search, read-only
#   log_thought(content, tags) — write-only reflection log,
#                                isolated from FAISS and retrieval
#
# Log files:
#   memory/tool_dispatch.log  — every call + result, timestamped
#   memory/thought_log.jsonl  — log_thought output ONLY
#                               NOT indexed, NOT synced, NOT injected
#
# Isolation guarantee for thought_log.jsonl:
#   Written via direct open() only — never via append_to_journal()
#   (which would route to memory/{tag}.log and could be confused
#   with journal entries). FAISS indexes only ACTIVE_JOURNAL.
#   Sync reads only interaction_log.jsonl. No code path connects
#   thought_log.jsonl to retrieval.
# ============================================================

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — dispatch model is explicit and unchanging
# ---------------------------------------------------------------------------

DISPATCH_MODEL = "llama3.1:8b"          # the model making tool-call decisions
CHAT_URL = "http://localhost:11434/api/chat"
MAX_TOOL_ROUNDS = 5                      # max model calls per dispatch session
_MAX_READ_BYTES = 50_000                 # 50 KB file read cap


def _find_project_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isfile(os.path.join(here, "run.py")):
            return os.path.realpath(here)
        here = os.path.dirname(here)
    return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


_PROJECT_ROOT = _find_project_root()
_TOOL_DISPATCH_LOG = os.path.join(_PROJECT_ROOT, "memory", "tool_dispatch.log")
_THOUGHT_LOG = os.path.join(_PROJECT_ROOT, "memory", "thought_log.jsonl")

# ---------------------------------------------------------------------------
# Path-traversal guards — same structured patterns as echo_tool_context.py.
# Applied to the path ARGUMENT directly, not to prose context.
# ---------------------------------------------------------------------------

_RELATIVE_TRAVERSAL_RE = re.compile(r'\.\.[/\\]|[/\\]\.\.')
_ABSOLUTE_SYS_PATH_RE = re.compile(
    r'(?:^|[\s\'"`(])'
    r'/(?:etc|usr|var|home|root|tmp|sys|proc|dev|users|private)'
    r'(?:/|[\s\'"`)]|$)',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Tool schemas — Ollama /api/chat tools parameter format
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the contents of a file inside the FeralEcho project. "
                "Path is relative to the project root (e.g. 'app/core/echo_core.py'). "
                "Traversal attempts and paths outside the project are refused."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": (
                "Semantic search of Echo's episodic memory (FAISS index). "
                "Returns up to 5 relevant past interactions or reflections."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query to search memory",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_thought",
            "description": (
                "Record a reflection or observation to a private thought log. "
                "Write-only: entries do NOT flow back into memory retrieval, "
                "FAISS, or context injection. Safe to use freely."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The thought or reflection to record",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional classification tags",
                    },
                },
                "required": ["content"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# System prompt for the dispatch model
# ---------------------------------------------------------------------------

DISPATCH_SYSTEM_PROMPT = (
    "You are the tool-execution layer for Echo, an AI entity running on a local system. "
    "You have access to tools that can read project files, search Echo's episodic memory, "
    "and log private observations.\n\n"
    "Rules:\n"
    "- When a request requires reading a real file or searching actual memory, use the tool.\n"
    "- Never fabricate file contents, memory results, or tool confirmations.\n"
    "- If a tool returns an error or refusal, report it exactly — do not work around it.\n"
    "- If the request can be answered without tools, answer directly without calling any.\n"
    "- log_thought is write-only and safe to use for any reflection worth noting."
)

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _guard_read_path(path: str) -> tuple[bool, str]:
    """
    Validate a path argument for read_file.
    Returns (allowed, resolved_absolute_path_or_refusal_string).
    Checks the argument itself — not prose context.
    """
    if not isinstance(path, str) or not path.strip():
        return False, "[read_file — refused: empty or non-string path]"

    # 1. Direct '..' check — catches relative traversal in the argument
    if ".." in path:
        return False, "[read_file — refused: path contains traversal component '..']"

    # 2. Structured pattern checks (covers URL-encoded and mixed cases)
    if _RELATIVE_TRAVERSAL_RE.search(path):
        return False, "[read_file — refused: traversal pattern detected in path]"

    # 3. Absolute path handling
    if os.path.isabs(path):
        # Check absolute system path patterns against the argument
        if _ABSOLUTE_SYS_PATH_RE.search(path):
            return False, "[read_file — refused: absolute system path]"
        resolved = os.path.realpath(path)
        if not resolved.startswith(_PROJECT_ROOT + os.sep) and resolved != _PROJECT_ROOT:
            return False, "[read_file — refused: absolute path is outside project root]"
        return True, resolved

    # 4. Relative path — resolve and verify
    resolved = os.path.realpath(os.path.join(_PROJECT_ROOT, path))
    if not resolved.startswith(_PROJECT_ROOT + os.sep) and resolved != _PROJECT_ROOT:
        return False, "[read_file — refused: resolved path escapes project root]"

    return True, resolved


def _tool_read_file(path: str) -> tuple[str, bool, str | None]:
    """Read a file inside the project root. Fail closed on any guard violation."""
    allowed, resolved_or_err = _guard_read_path(path)
    if not allowed:
        return resolved_or_err, False, "path_traversal"

    resolved = resolved_or_err

    if not os.path.exists(resolved):
        return f"[read_file — error: file not found: {path}]", False, "not_found"

    if os.path.isdir(resolved):
        return f"[read_file — error: {path} is a directory, not a file. Use list_directory for directories.]", False, "is_directory"

    size = os.path.getsize(resolved)
    if size > _MAX_READ_BYTES:
        return (
            f"[read_file — error: file too large ({size:,} bytes; limit {_MAX_READ_BYTES:,}). "
            f"Read a smaller file or a specific section.]",
            False,
            "file_too_large",
        )

    try:
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        rel = os.path.relpath(resolved, _PROJECT_ROOT)
        return f"[read_file: {rel}]\n{content}", True, None
    except PermissionError:
        return f"[read_file — error: permission denied: {path}]", False, "permission_denied"
    except Exception as exc:
        return f"[read_file — error: {exc}]", False, "read_error"


def _tool_search_memory(query: str) -> tuple[str, bool, str | None]:
    """Semantic search against the FAISS episodic memory index. Read-only."""
    if not isinstance(query, str) or not query.strip():
        return "[search_memory — error: empty query]", False, "empty_query"

    try:
        from app.core.memory_bridge import retrieve_relevant_memories
        results = retrieve_relevant_memories(query.strip(), top_k=5, source_filter=None)

        if not results:
            return f"[search_memory — no results for: {repr(query[:60])}]", True, None

        lines = [f"[search_memory — {len(results)} result(s) for: {repr(query[:60])}]"]
        for i, r in enumerate(results, 1):
            text = (r.get("text") or "")[:300]
            score = r.get("score", 0.0)
            source = r.get("meta", {}).get("memory_source", "unknown")
            lines.append(f"  [{i}] score={score:.4f} source={source}: {text}")

        return "\n".join(lines), True, None

    except Exception as exc:
        return f"[search_memory — error: {exc}]", False, "search_error"


def _tool_log_thought(content: str, tags: list | None = None) -> tuple[str, bool, str | None]:
    """
    Append one entry to memory/thought_log.jsonl.

    Isolation contract:
    - Written via direct open(), NOT via memory_bridge.append_to_journal()
    - No 'memory_source' field — cannot be mistaken for an episodic memory entry
    - _THOUGHT_LOG path is not registered with FAISS, sync, or introspection_channel
    - This log is write-only until a deliberate future decision connects it to retrieval
    """
    if not isinstance(content, str) or not content.strip():
        return "[log_thought — error: empty content]", False, "empty_content"

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": content.strip(),
        "tags": [str(t) for t in (tags or [])],
        # Deliberately NO memory_source field — keeps this out of any source-filtered retrieval
    }

    try:
        os.makedirs(os.path.dirname(_THOUGHT_LOG), exist_ok=True)
        with open(_THOUGHT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        preview = content.strip()[:80]
        return f"[log_thought — recorded: {repr(preview)}]", True, None
    except Exception as exc:
        return f"[log_thought — error: {exc}]", False, "write_error"


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def _execute_tool(name: str, args: dict) -> tuple[str, bool, str | None]:
    """Route a tool call to its implementation. Unknown names fail closed."""
    if name == "read_file":
        return _tool_read_file(str(args.get("path", "")))
    if name == "search_memory":
        return _tool_search_memory(str(args.get("query", "")))
    if name == "log_thought":
        content = str(args.get("content", ""))
        tags = args.get("tags", [])
        return _tool_log_thought(content, tags)
    return f"[unknown tool: {repr(name)}]", False, "unknown_tool"


# ---------------------------------------------------------------------------
# Call logger — every call lands here regardless of success or failure
# ---------------------------------------------------------------------------

def _log_call(
    session_id: str,
    round_num: int,
    tool_name: str,
    args: dict,
    result: str,
    success: bool,
    error_type: str | None,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "dispatch_model": DISPATCH_MODEL,
        "round": round_num,
        "tool_name": tool_name,
        "arguments": args,
        "result_preview": result[:300] if result else "",
        "success": success,
        "error_type": error_type,
    }
    try:
        os.makedirs(os.path.dirname(_TOOL_DISPATCH_LOG), exist_ok=True)
        with open(_TOOL_DISPATCH_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:
        logger.error("[ToolDispatch] log write failed: %s", exc)


# ---------------------------------------------------------------------------
# Ollama /api/chat wrapper
# ---------------------------------------------------------------------------

def _ollama_chat(messages: list[dict]) -> dict:
    """
    POST to Ollama /api/chat with TOOL_SCHEMAS.
    Returns the full response dict. Never raises — errors produce a
    synthetic assistant message so the dispatch loop can continue cleanly.
    """
    payload = {
        "model": DISPATCH_MODEL,
        "messages": messages,
        "tools": TOOL_SCHEMAS,
        "stream": False,
        "options": {
            "num_ctx": 32768,
            "num_predict": 1024,
        },
    }
    try:
        resp = requests.post(CHAT_URL, json=payload, timeout=180)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.error("[ToolDispatch] Ollama chat failed: %s", exc)
        return {
            "message": {
                "role": "assistant",
                "content": f"[dispatch error: {exc}]",
                "tool_calls": [],
            }
        }


# ---------------------------------------------------------------------------
# Main dispatch loop
# ---------------------------------------------------------------------------

def run_tool_dispatch(
    prompt: str,
    session_id: str | None = None,
) -> dict:
    """
    Run the tool dispatch loop for a prompt.

    The dispatch model (DISPATCH_MODEL = llama3.1:8b) decides which tools
    to call. Every decision is logged with that model name.

    Returns a dict with keys:
        response        — final text from the dispatch model
        rounds_used     — how many model calls were made
        tool_calls_made — total number of tool executions
        session_id      — trace ID for this dispatch session
        dispatch_model  — always DISPATCH_MODEL, for traceability
    """
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]

    messages: list[dict] = [
        {"role": "system", "content": DISPATCH_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    total_tool_calls = 0

    for round_num in range(1, MAX_TOOL_ROUNDS + 1):
        response = _ollama_chat(messages)
        msg = response.get("message", {})
        tool_calls: list[dict] = msg.get("tool_calls") or []
        content: str = msg.get("content") or ""

        if not tool_calls:
            # No tool calls — dispatch model is done
            return {
                "response": content,
                "rounds_used": round_num,
                "tool_calls_made": total_tool_calls,
                "session_id": session_id,
                "dispatch_model": DISPATCH_MODEL,
            }

        # Add assistant's tool-call message to history
        messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls,
        })

        # Execute every tool call the model requested in this round
        for tc in tool_calls:
            fn = tc.get("function", {})
            tc_id: str = tc.get("id", f"call_{total_tool_calls}")
            tool_name: str = fn.get("name", "unknown")
            tool_args: dict = fn.get("arguments", {})

            result, success, error_type = _execute_tool(tool_name, tool_args)
            _log_call(session_id, round_num, tool_name, tool_args, result, success, error_type)
            total_tool_calls += 1

            messages.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": result,
            })

    # Exhausted all rounds
    _log_call(
        session_id, MAX_TOOL_ROUNDS, "__max_rounds__", {},
        "[max tool rounds reached]", False, "max_rounds",
    )
    return {
        "response": "[max tool rounds reached]",
        "rounds_used": MAX_TOOL_ROUNDS,
        "tool_calls_made": total_tool_calls,
        "session_id": session_id,
        "dispatch_model": DISPATCH_MODEL,
    }


# ---------------------------------------------------------------------------
# Detection — gate for terminal_client.py routing
# ---------------------------------------------------------------------------

_DISPATCH_SIGNALS = frozenset([
    # read_file
    "read file", "read the file", "open file", "show file contents",
    "what does the file", "what is in the file", "what's in the file",
    "show me the file", "file contents", "contents of the file",
    # search_memory
    "search memory", "search my memory", "search your memory",
    "recall", "what do you remember about", "do you remember",
    "look up in memory", "check your memory", "memory search",
    "find in memory", "what memories do you have",
    # log_thought
    "log a thought", "log this thought", "log this", "record a thought",
    "note this down", "jot this down", "write this down", "make a note",
    "log an observation", "record this", "log this reflection",
])


def needs_dispatch(prompt: str) -> bool:
    """
    Return True if the prompt is likely to benefit from tool dispatch.
    Intentionally does NOT overlap with echo_tool_context._LISTING_SIGNALS
    (directory listings) — those are pre-execution injection, not dispatch.
    """
    low = prompt.lower()
    return any(sig in low for sig in _DISPATCH_SIGNALS)
