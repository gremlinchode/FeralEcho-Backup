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
from app.core import conversation_service

from sentence_transformers import SentenceTransformer

# ---------------------------------
# --- Console ---------------------
# ---------------------------------
SERVER_URL = "http://127.0.0.1:5000"
console = Console()

_SERVER_PID_FILE = Path("memory/echo_server.pid")


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
# --- Semantic Memory Search ------
# ---------------------------------
def _vm_search(query: str, k: int) -> list:
    """Adapter passed to conversation_service.retrieve_memory_context — searches
    this process's local VectorMemory instance."""
    if vm is None:
        return []
    try:
        query_emb = embedding_fn(query)
        query_emb = np.ascontiguousarray(query_emb, dtype=np.float32)
        return vm.search(query_emb, k=k)
    except Exception as e:
        console.print(
            f"[bold yellow]Memory Search Warning:[/bold yellow] {e}"
        )
        return []


def retrieve_memory_context(msg: str, k=5) -> str:
    """Retrieve semantically relevant memories (delegates to conversation_service)."""
    return conversation_service.retrieve_memory_context(msg, _vm_search, k=k)

# ---------------------------------
# --- Save Memory -----------------
# ---------------------------------
def save_memory(user_msg: str, response_text: str):
    """
    Save conversation to semantic memory.
    """
    if vm is None:
        return
    if conversation_service.server_is_running():
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

# Audit finding: this buffer was purely in-memory — a client restart lost
# it entirely, and retrieve_memory_context()'s own exclude_recent_minutes=30
# deliberately excludes anything from the last 30 minutes from the memory
# fallback (so session history doesn't double up with retrieval). The two
# compose badly: the most recent ~30 minutes of a conversation could vanish
# from context entirely across a restart, with no signal that it happened.
# Persisted to a single-session file (this client is one CLI process, one
# user, no multi-session concept) and reloaded at startup — but only if
# recent enough to plausibly still be "the same conversation"; older state
# is deliberately left unloaded rather than resuming a stale, confusing
# context the user has long since moved on from.
_SESSION_STATE_PATH = Path("memory/terminal_session.json")
_SESSION_CONTINUITY_WINDOW = 4 * 3600  # 4 hours


def _load_session_state() -> None:
    global _conv_history, _history_summaries
    try:
        if not _SESSION_STATE_PATH.exists():
            return
        data = json.loads(_SESSION_STATE_PATH.read_text())
        turns = data.get("conv_history", [])
        if not turns:
            return
        last_ts = turns[-1].get("ts", "")
        last_epoch = datetime.fromisoformat(str(last_ts).replace("Z", "+00:00")).timestamp()
        if time.time() - last_epoch > _SESSION_CONTINUITY_WINDOW:
            return  # too stale — start fresh rather than resuming old context
        _conv_history = turns
        _history_summaries = data.get("history_summaries", [])
        console.print(
            f"[dim]  (resumed {len(_conv_history)} turn(s) from before restart)[/dim]"
        )
    except Exception:
        pass  # never block startup over a missing/corrupt session file


def _save_session_state() -> None:
    try:
        _SESSION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = _SESSION_STATE_PATH.with_suffix(".tmp")
        tmp_path.write_text(json.dumps({
            "conv_history": _conv_history,
            "history_summaries": _history_summaries,
        }))
        tmp_path.replace(_SESSION_STATE_PATH)
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

    global temporal_context, _conv_history, _history_summaries

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
    # Retrieve memory context + session history — both are system-side
    # context (not something the user said). Previously prepended directly
    # into full_msg as a raw "Turn N: You: ... Echo: ..." transcript ahead
    # of the real question, with no role boundary; confirmed live
    # (2026-07-12, via Echo Studio, same code path) to cause local models
    # to regurgitate the prior turn verbatim instead of answering the new
    # one. See conversation_service.build_context_system_note()'s docstring.
    # ---------------------------------
    memory_context = retrieve_memory_context(msg)
    history_block = conversation_service.format_history_block(_conv_history, _history_summaries)
    context_note = conversation_service.build_context_system_note(history_block, memory_context)

    full_msg = msg

    # ---------------------------------
    # Ground-truth / tool-context injection, assembled consistently via
    # prompt_workspace.assemble() rather than each block's own ad-hoc
    # "+ \"\\n\" +" / "+ \"\\n\\n\" +" concatenation (previously inconsistent
    # between this file and routes_echo_studio.py's mirrored version).
    # ---------------------------------
    ground_truth = ""
    try:
        from app.core.echo_ground_truth import _is_introspective, get_structural_self_facts
        if _is_introspective(msg):
            ground_truth = get_structural_self_facts(msg) or ""
    except Exception as _gt_err:
        pass  # never block a response over a diagnostic read

    tool_ctx = ""
    try:
        from app.core.echo_tool_context import _needs_tool_context, get_tool_context
        if _needs_tool_context(msg):
            tool_ctx = get_tool_context(msg) or ""
    except Exception as _tc_err:
        pass  # never block a response over a tool read

    # tool_ctx/ground_truth are system-side context (not something the user
    # said) — passed separately as echo_query()'s `system` param instead of
    # flattened into full_msg, so they travel as a real system-role message
    # once echo_query()/deliberate_and_learn() reach /api/chat, rather than
    # string-concatenated prose ahead of the user's actual message.
    _system_context = "\n\n".join(s for s in (tool_ctx, ground_truth, context_note) if s)

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
            raw_response = echo_query(
                full_msg, task_type=_task_type, source="user_conversation", system=_system_context,
            )

        except Exception as orch_err:
            import traceback
            console.print(f"[bold yellow]Orchestrator fallback — using Ollama direct:[/bold yellow] {orch_err}")
            console.print(f"[bold red]FULL ERROR:[/bold red] {traceback.format_exc()}")
            try:
                buffer = []
                for token in ollama_handler.stream_query_ollama(full_msg, system=_system_context):
                    buffer.append(token)
                raw_response = "".join(buffer).strip()

            except Exception as e:
                console.print(f"[bold red]Streaming Error:[/bold red] {e}")
                raw_response = "Error: could not stream message."

    response_text = conversation_service.clean_response_text(raw_response)

    # Store in session history buffer and persist to server
    _conv_history, _history_summaries = conversation_service.store_turn_in_history(
        _conv_history, _history_summaries, original_msg, response_text
    )
    _save_session_state()
    conversation_service.save_turn_to_server(original_msg, response_text, _task_type, server_url=SERVER_URL)

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
    Request self-editing code generation via the manual !edit command.
    Routes through perform_self_edit() (not execute_self_edit() directly)
    so a manual edit respects the same 60-minute cooldown as autonomous
    edits — the real corruption risk this closes is two real production
    writes racing (this manual command landing while the hourly
    AutonomousSelfEdit loop's own real apply is in progress), not just
    "should a human wait." Still includes mastery review, sandbox
    validation, and RiverBrain learning — perform_self_edit() calls
    execute_self_edit() internally once past the cooldown gate.
    """

    try:
        from app.core.self_edit_manager import perform_self_edit
        success, result = perform_self_edit(prompt=prompt)

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

    _load_session_state()

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
