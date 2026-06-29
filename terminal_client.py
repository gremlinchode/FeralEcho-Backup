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

        # Prefer entries tagged as user conversations; fall back to all if too few
        conv_memories = [
            (text, score, meta) for text, score, meta in raw_memories
            if meta.get("memory_source") == "user_conversation"
        ]
        relevant_memories = conv_memories[:k] if len(conv_memories) >= k else raw_memories[:k]

        memory_context = "\n".join([
            f"- {text}"
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

def _prompt_user_rating(response_text: str) -> None:
    """Non-blocking 4-second window for the user to rate Echo's response 1-5."""
    try:
        console.print("[dim]  Rate this response [1-5] or press Enter to skip:[/dim] ", end="")
        sys.stdout.flush()
        ready, _, _ = select.select([sys.stdin], [], [], 4.0)
        if ready:
            line = sys.stdin.readline().strip()
            if line and line in "12345" and len(line) == 1:
                rating = int(line)
                entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "user_rating",
                    "rating": rating,
                    "response_preview": response_text[:80].replace("\n", " "),
                }
                _INTERACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
                with open(_INTERACTION_LOG, "a") as fh:
                    fh.write(json.dumps(entry) + "\n")
                console.print(f"[dim]Rating {rating} saved.[/dim]")
            else:
                console.print()
        else:
            console.print()
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
            f"Context from past memories:\n"
            f"{memory_context}\n\n"
            f"User: {msg}"
        )

    else:
        full_msg = msg

    # ---------------------------------
    # Generate response
    # ---------------------------------
    response_text = ""

    try:
        from app.core.echo_model_orchestrator import echo_query, resolve_task_type
        task_type, _ = resolve_task_type(msg)
        raw_response = echo_query(full_msg, task_type=task_type)

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

    console.print(f"💬 Echo: {response_text}\n")

    _prompt_user_rating(response_text)

    # ---------------------------------
    # Save memory
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
