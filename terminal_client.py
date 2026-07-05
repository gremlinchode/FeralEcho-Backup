# terminal_client.py – Echo Terminal Client with Stable Semantic Memory
# Optimized for macOS + FAISS + sentence-transformers stability

import os

# ---------------------------------
# --- macOS / OpenMP Stability ----
# ---------------------------------
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# ---------------------------------
# --- Imports ---------------------
# ---------------------------------
from app.core.temporal_environment import get_temporal_environment_context

import sys
import select
import json
import threading
import uuid
import numpy as np
import time
import faiss
import requests
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown

import pyttsx3

from app.lib.vector_memory import VectorMemory, MemoryItem
from app import ollama_handler

from sentence_transformers import SentenceTransformer

# ---------------------------------
# --- Console ---------------------
# ---------------------------------
SERVER_URL = "http://127.0.0.1:5000"
console = Console()

_SERVER_PID_FILE = Path("memory/echo_server.pid")


def _server_is_running() -> bool:
    """True if the Flask server process wrote a PID file and is still alive."""
    if not _SERVER_PID_FILE.exists():
        return False
    try:
        pid = int(_SERVER_PID_FILE.read_text().strip())
        os.kill(pid, 0)  # signal 0: existence check only
        return True
    except (ValueError, OSError):
        return False

# ---------------------------------
# --- FAISS Thread Safety ---------
# ---------------------------------
try:
    faiss.omp_set_num_threads(1)
except Exception:
    pass

# ---------------------------------
# --- Text-to-Speech Setup --------
# ---------------------------------
engine = pyttsx3.init()

engine.setProperty("rate", 160)
engine.setProperty("volume", 1.0)

def speak_async(text: str):
    """Speak text asynchronously."""

    def run_tts():
        try:
            engine.say(text)
            engine.runAndWait()

        except Exception as e:
            console.print(
                f"[bold yellow]TTS Warning:[/bold yellow] {e}"
            )

    threading.Thread(
        target=run_tts,
        daemon=True
    ).start()

# ---------------------------------
# --- Semantic Memory Setup -------
# ---------------------------------
console.print("[dim]Loading semantic embedding model...[/dim]")

embedding_dim = 384
_st_model = None
try:
    _st_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as _e:
    console.print(f"[yellow]Warning: embedding model unavailable ({_e}). Semantic search disabled.[/yellow]")

# ---------------------------------
# --- Vector Memory ---------------
# ---------------------------------
vm = None
try:
    vm = VectorMemory(
        index_path="memory/faiss.index",
        meta_path="memory/memory_meta.json",
        dim=embedding_dim
    )
except Exception as _e:
    console.print(f"[yellow]Warning: FAISS index unavailable ({_e}). Memory search disabled.[/yellow]")

def embedding_fn(text: str) -> np.ndarray:
    """
    Generate FAISS-safe semantic embeddings.

    Returns:
        np.ndarray shape -> (1, 384)
    """

    try:
        vec = _st_model.encode(
            [text],                     # IMPORTANT: LIST INPUT
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        # Force contiguous memory layout
        vec = np.ascontiguousarray(
            vec,
            dtype=np.float32
        )

        return vec

    except Exception as e:
        console.print(
            f"[bold red]Embedding Error:[/bold red] {e}"
        )

        # Safe fallback
        return np.zeros(
            (1, embedding_dim),
            dtype=np.float32
        )

# ---------------------------------
# --- Temporal Context ------------
# ---------------------------------
API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

temporal_context = ""

def refresh_temporal_context(interval=600):
    """
    Background thread for temporal awareness updates.
    """

    global temporal_context

    while True:

        try:
            temporal_context = (
                get_temporal_environment_context(
                    weather_api_key=API_KEY
                )
            )

            first_line = temporal_context.split("\n")[0]
            weather_line = temporal_context.split("\n")[-1]

            console.print(
                f"[dim]🔄 Temporal context updated: "
                f"{first_line}, {weather_line}[/dim]"
            )

        except Exception as e:

            console.print(
                f"[bold yellow]Temporal Warning:[/bold yellow] {e}"
            )

        time.sleep(interval)

# ---------------------------------
# --- Response Cleanup ------------
# ---------------------------------
def clean_response_text(raw_response: str) -> str:
    """
    Clean token spacing artifacts.
    """

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

# ---------------------------------
# --- Semantic Memory Search ------
# ---------------------------------
def retrieve_memory_context(msg: str, k=5) -> str:
    """
    Retrieve semantically relevant memories.
    """
    if vm is None:
        return ""
    try:
        query_emb = embedding_fn(msg)

        # Additional safety enforcement
        query_emb = np.ascontiguousarray(
            query_emb,
            dtype=np.float32
        )

        # Fetch extra candidates so we can prefer user-conversation memories
        raw_memories = vm.search(query_emb, k=k * 3)

        if not raw_memories:
            return ""

        # Prefer user-conversation entries. When falling back (fewer than k match),
        # never include autonomous-sourced entries (news feed, fetch cycle) — they
        # are external observations, not history, and the model treats unlabeled
        # retrieved text as first-person memory (Finding 14, 2026-07-02).
        conv_memories = [
            (text, score, meta) for text, score, meta in raw_memories
            if meta.get("memory_source") == "user_conversation"
        ]
        non_autonomous = [
            (text, score, meta) for text, score, meta in raw_memories
            if meta.get("memory_source") != "autonomous"
        ]
        relevant_memories = (
            conv_memories[:k]
            if len(conv_memories) >= k
            else non_autonomous[:k]
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

        memory_context = "\n".join([
            f"- {_source_label(meta)}: {text}"
            for text, score, meta in relevant_memories
        ])

        return memory_context

    except Exception as e:

        console.print(
            f"[bold yellow]Memory Search Warning:[/bold yellow] {e}"
        )

        return ""

# ---------------------------------
# --- Save Memory -----------------
# ---------------------------------
def save_memory(user_msg: str, response_text: str):
    """
    Save conversation to semantic memory.
    """
    if vm is None:
        return
    if _server_is_running():
        return  # Server owns FAISS index; avoid concurrent writes
    try:
        _conv_meta = {"memory_source": "user_conversation"}
        items_to_add = [
            MemoryItem(
                id=str(uuid.uuid4()),
                text=user_msg,
                meta=_conv_meta,
            ),
            MemoryItem(
                id=str(uuid.uuid4()),
                text=response_text,
                meta=_conv_meta,
            )
        ]

        user_emb = embedding_fn(user_msg)
        response_emb = embedding_fn(response_text)

        embeddings_to_add = np.vstack([
            user_emb,
            response_emb
        ])

        embeddings_to_add = np.ascontiguousarray(
            embeddings_to_add,
            dtype=np.float32
        )

        vm.add(
            items_to_add,
            embeddings_to_add
        )

    except Exception as e:

        console.print(
            f"[bold yellow]Memory Save Warning:[/bold yellow] {e}"
        )

# ---------------------------------
# --- User Rating (A1) ------------
# ---------------------------------
_INTERACTION_LOG = Path("memory/interaction_log.jsonl")

def _save_rating(rating: int, response_text: str) -> None:
    """Write a user rating to the interaction log. Called from the main input loop."""
    try:
        entry = {
            "timestamp":        datetime.utcnow().isoformat(),
            "type":             "user_rating",
            "rating":           rating,
            "response_preview": response_text[:80].replace("\n", " "),
        }
        _INTERACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_INTERACTION_LOG, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass

# ---------------------------------
# --- Session Conversation Buffer -
# ---------------------------------
_conv_history: list = []       # [{ts, user, echo}] — turns in this session
_history_summaries: list = []  # one-line compressed notes for turns that fell off the window
_HISTORY_TOKEN_BUDGET = 4000   # ~4000 tokens; leaves room for response under num_ctx=8192

def _est_tokens(text: str) -> int:
    return max(1, len(text) // 4)

def _history_token_count() -> int:
    turn_tokens = sum(
        _est_tokens(t["user"]) + _est_tokens(t["echo"])
        for t in _conv_history
    )
    summary_tokens = sum(_est_tokens(s) for s in _history_summaries)
    return turn_tokens + summary_tokens + 50  # 50-token overhead for formatting

def _format_history_block() -> str:
    """Render session history for prompt injection. Returns '' if no history."""
    if not _conv_history and not _history_summaries:
        return ""

    parts = []
    n_compressed = len(_history_summaries)

    if _history_summaries:
        parts.append("[Earlier in this conversation — compressed:]")
        for s in _history_summaries:
            parts.append(f"  {s}")

    turn_offset = n_compressed + 1
    for i, turn in enumerate(_conv_history):
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

def _store_turn_in_history(user_msg: str, echo_response: str) -> None:
    """Add a completed turn. If over budget, compress-and-drop the oldest turn."""
    global _conv_history, _history_summaries

    _conv_history.append({
        "ts": datetime.utcnow().isoformat(),
        "user": user_msg,
        "echo": echo_response,
    })

    while _history_token_count() > _HISTORY_TOKEN_BUDGET and len(_conv_history) > 1:
        oldest = _conv_history.pop(0)
        q = oldest["user"]
        topic = q[:60] + ("..." if len(q) > 60 else "")
        _history_summaries.append(f'You asked: "{topic}"')

def _save_turn_to_server(user_msg: str, echo_response: str, task_type: str) -> None:
    """POST conversation turn to the server for FAISS persistence (Piece B).
    Silent on all errors — never blocks the conversation.
    """
    if not _server_is_running():
        return
    try:
        requests.post(
            f"{SERVER_URL}/memory/conversation",
            json={
                "user_msg": user_msg,
                "echo_response": echo_response,
                "task_type": task_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
            timeout=3,
        )
    except Exception:
        pass

# ---------------------------------
# --- Main Communication ----------
# ---------------------------------
def send_message_stream(
    msg: str,
    prepend_context=False
) -> str:
    """
    Send message to Echo and stream response.
    """

    global temporal_context

    # Capture raw user input before any context injection modifies msg
    original_msg = msg

    # ---------------------------------
    # Inject environmental awareness
    # ---------------------------------
    if prepend_context and temporal_context:

        msg = (
            f"Environmental awareness context for Echo:\n"
            f"{temporal_context}\n\n"
            f"User: {msg}"
        )

    elif temporal_context:

        msg = (
            f"[Updated temporal context: "
            f"{temporal_context}]\n\n"
            f"User: {msg}"
        )

    # ---------------------------------
    # Retrieve memory context
    # ---------------------------------
    memory_context = retrieve_memory_context(msg)

    # ---------------------------------
    # Build final prompt
    # ---------------------------------
    if memory_context:

        full_msg = (
            f"Context (past interactions and system logs — not assertions about identity):\n"
            f"{memory_context}\n\n"
            f"User: {msg}"
        )

    else:
        full_msg = msg

    # Prepend this session's conversation history so Echo has within-session continuity
    history_block = _format_history_block()
    if history_block:
        full_msg = history_block + "\n\n" + full_msg

    # ---------------------------------
    # Ground-truth injection (introspective queries only)
    # Mirrors TOOL_AWARE_TASKS gating in echo_model_orchestrator.py:
    # only fires when the prompt is about Echo's own internal state,
    # only injects the slice(s) relevant to what's being asked.
    # ---------------------------------
    try:
        from app.core.echo_ground_truth import _is_introspective, get_structural_self_facts
        if _is_introspective(msg):
            ground_truth = get_structural_self_facts(msg)
            if ground_truth:
                full_msg = ground_truth + "\n" + full_msg
    except Exception as _gt_err:
        pass  # never block a response over a diagnostic read

    # ---------------------------------
    # Tool context injection (file/directory queries only)
    # Pre-executes the tool and injects the result before generation.
    # ---------------------------------
    try:
        from app.core.echo_tool_context import _needs_tool_context, get_tool_context
        if _needs_tool_context(msg):
            tool_ctx = get_tool_context(msg)
            if tool_ctx:
                full_msg = tool_ctx + "\n\n" + full_msg
    except Exception as _tc_err:
        pass  # never block a response over a tool read

    # Resolve task type early — needed by both the echo_query call and memory tagging
    _task_type = "general"
    try:
        from app.core.echo_model_orchestrator import resolve_task_type as _rtt
        _task_type, _ = _rtt(original_msg)
    except Exception:
        pass

    # ---------------------------------
    # Tool dispatch loop
    # Routes tool-eligible prompts through llama3.1:8b (the dispatch
    # model) which has native tool-calling support. All tool decisions
    # and results are logged to memory/tool_dispatch.log with the
    # dispatch model name — never attributed to echo:latest.
    # Falls back to echo_query silently on any import or runtime error.
    # ---------------------------------
    _dispatch_result = None
    try:
        from app.core.echo_tool_dispatch import needs_dispatch, run_tool_dispatch
        if needs_dispatch(msg):
            _dispatch_result = run_tool_dispatch(full_msg, session_id=str(uuid.uuid4())[:8])
    except Exception as _disp_err:
        pass  # dispatch failure must never block a response

    # ---------------------------------
    # Generate response
    # ---------------------------------
    response_text = ""

    if _dispatch_result is not None:
        raw_response = _dispatch_result.get("response", "")
    else:
        try:
            from app.core.echo_model_orchestrator import echo_query
            raw_response = echo_query(full_msg, task_type=_task_type, source="user_conversation")

        except Exception as orch_err:
            import traceback
            console.print(f"[bold yellow]Orchestrator fallback — using Ollama direct:[/bold yellow] {orch_err}")
            console.print(f"[bold red]FULL ERROR:[/bold red] {traceback.format_exc()}")
            try:
                buffer = []
                for token in ollama_handler.stream_query_ollama(full_msg):
                    buffer.append(token)
                raw_response = "".join(buffer).strip()

            except Exception as e:
                console.print(f"[bold red]Streaming Error:[/bold red] {e}")
                raw_response = "Error: could not stream message."

    response_text = clean_response_text(raw_response)

    # Store in session history buffer and persist to server
    _store_turn_in_history(original_msg, response_text)
    _save_turn_to_server(original_msg, response_text, _task_type)

    console.print(f"💬 Echo: {response_text}\n")
    console.print("[dim]  (type 1–5 at the next prompt to rate this response)[/dim]")

    # ---------------------------------
    # Save memory (gated: only fires when server is NOT running)
    # ---------------------------------
    save_memory(msg, response_text)

    return response_text
# ---------------------------------
# --- Self Edit -------------------
# ---------------------------------
def request_self_edit(prompt: str) -> dict:
    """
    Request self-editing code generation via WOLF pipeline.
    Routes through execute_self_edit() — includes mastery review,
    sandbox validation, friction events, and RiverBrain learning.
    """

    try:
        from app.core.self_edit_manager import execute_self_edit
        success, result = execute_self_edit(prompt)

        return {
            "status": "success" if success else "failed",
            "result": result
        }

    except Exception as e:

        console.print(
            f"[bold red]Self Edit Error:[/bold red] {e}"
        )

        return {
            "status": "failed",
            "error": str(e)
        }

# ---------------------------------
# --- Main Loop -------------------
# ---------------------------------
def main():

    console.print(
        "[bold green]Echo Terminal Client Started[/bold green]"
    )

    first_message = True
    last_response: str = ""   # held for rating until replaced by the next response

    # Start temporal awareness updater
    threading.Thread(
        target=refresh_temporal_context,
        args=(600,),
        daemon=True
    ).start()

    try:

        while True:

            msg = console.input(
                "[bold cyan]You:[/bold cyan] "
            ).strip()

            if not msg:
                continue

            # Rating shortcut: bare 1–5 rates the previous response, then loops back.
            if msg in {"1", "2", "3", "4", "5"} and last_response:
                _save_rating(int(msg), last_response)
                console.print(f"[dim]  Rating {msg} saved.[/dim]")
                continue

            # Exit commands
            if msg.lower() in {
                "exit",
                "quit"
            }:

                console.print(
                    "[bold red]Exiting...[/bold red]"
                )

                break

            # -----------------------------
            # Self-edit mode
            # -----------------------------
            if msg.startswith("!edit "):

                prompt = (
                    msg[len("!edit "):]
                    .strip()
                )

                if prompt:

                    result = request_self_edit(
                        prompt
                    )

                    console.print(
                        f"[bold magenta]"
                        f"Self Edit Result:"
                        f"[/bold magenta] "
                        f"{result.get('status', 'unknown')}"
                    )

                    speak_async(
                        f"Self edit result: "
                        f"{result.get('status', 'unknown')}"
                    )

                else:

                    console.print(
                        "[bold yellow]"
                        "Please provide a prompt "
                        "after '!edit'."
                        "[/bold yellow]"
                    )

            # -----------------------------
            # Normal conversation
            # -----------------------------
            else:

                response = send_message_stream(
                    msg,
                    prepend_context=first_message
                )

                speak_async(response)
                last_response = response

                first_message = False

    except KeyboardInterrupt:

        console.print(
            "\n[bold red]"
            "Interrupted by user. Exiting..."
            "[/bold red]"
        )

# ---------------------------------
# --- Entrypoint ------------------
# ---------------------------------
if __name__ == "__main__":
    main()
