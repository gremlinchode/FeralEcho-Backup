import os
import json
import requests
import socket
import subprocess
import threading
import logging
import time
import traceback
import ast
from typing import Optional, Dict, Generator

# ---- Config ----
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "echo:latest")

# Modelfile identity restoration (see _build_chat_messages()/_get_echo_identity_block()
# below) — Ollama's /api/chat replaces, rather than merges with, a model's
# Modelfile SYSTEM block whenever the request carries an explicit system
# message. Confirmed live via direct curl against /api/chat.
_MODELFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Modelfile")
_echo_identity_cache: dict = {"text": None, "mtime": None}

# ---- MLX routing ----
# Patched once on first query — safe because ollama_handler is imported
# lazily (inside _ollama_query), so the app is fully initialized by then.
_mlx_pool_patched = False
_mlx_patch_lock = threading.Lock()

def _patch_mlx_once() -> None:
    global _mlx_pool_patched
    # Two threads racing on the very first query each (e.g. a real request
    # landing right as an autonomous loop also fires) could both pass the
    # unlocked check-then-set below and both call MODEL_POOL.update()
    # concurrently — a real RuntimeError risk for any third thread mid-
    # iteration over MODEL_POOL.keys() at the same moment.
    with _mlx_patch_lock:
        if _mlx_pool_patched:
            return
        _mlx_pool_patched = True
        try:
            from app.mlx_handler import patch_model_pool
            patch_model_pool()
        except Exception as e:
            logging.warning(f"[MLX] Deferred MODEL_POOL patch failed: {e}")

def _get_mlx_path(model_name: str) -> Optional[str]:
    """Look up the HuggingFace path for an mlx:* model name."""
    try:
        from app.mlx_handler import list_mlx_models
        pool = list_mlx_models()
        entry = pool.get(model_name)
        return entry["mlx_path"] if entry else None
    except Exception:
        return None
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
CHAT_URL = os.getenv("OLLAMA_CHAT_URL", "http://localhost:11434/api/chat")
PERSONA_FILE = os.path.join(os.path.dirname(__file__), "persona.json")

_ollama_process: Optional[subprocess.Popen] = None
_ollama_stop_event = threading.Event()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


# ---- Helper functions ----

def _is_thinking_model(model: Optional[str]) -> bool:
    """DeepSeek-R1 variants always emit a separate 'thinking' field, whether
    called via /api/generate (top-level 'thinking' key) or /api/chat
    ('message.thinking' key, confirmed live 2026-07-08 against a running
    deepseek-r1:7b — see scripts/verify_chat_stream_shape.py). Shared by both
    the generate-path and chat-path streaming functions so the check isn't
    duplicated."""
    return "deepseek" in (model or "").lower()


def _get_echo_identity_block() -> Optional[str]:
    """Echo's real Modelfile SYSTEM block, mtime-cached so a manual Modelfile
    edit is picked up without a restart. Fails open (returns None) on any
    error — callers must treat None as 'inject nothing, behave exactly as
    before this existed.'"""
    try:
        mtime = os.path.getmtime(_MODELFILE_PATH)
        if _echo_identity_cache["mtime"] != mtime:
            with open(_MODELFILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            import re
            m = re.search(r'SYSTEM\s+"""(.*?)"""', content, re.DOTALL)
            _echo_identity_cache["text"] = m.group(1).strip() if m else None
            _echo_identity_cache["mtime"] = mtime
        return _echo_identity_cache["text"]
    except Exception as e:
        logging.debug(f"[IDENTITY] Modelfile identity read failed: {e}")
        return None


def _build_chat_messages(prompt: str, system: Optional[str], messages: Optional[list], model: Optional[str] = None) -> list:
    """Build a /api/chat messages array from either an explicit messages list
    (used as-is) or a system + single-turn prompt (the common case for now —
    callers don't yet track multi-turn history through this layer).

    model: when this equals OLLAMA_MODEL (Echo's own model), Echo's real
    Modelfile identity is prepended ahead of any situational system content.
    Ollama's /api/chat replaces rather than merges with a model's Modelfile
    SYSTEM block whenever an explicit system message is present — every
    real conversational caller now sends one (see Finding 17), which was
    silently dropping Echo's actual identity on every /api/chat call. Other
    models (council opinions from mistral/llama3.1/deepseek/etc.) must
    never receive this — they're meant to stay independent opinions, not be
    told they're Echo."""
    if messages is not None:
        return messages
    result = []
    effective_system = system
    if model == OLLAMA_MODEL:
        identity = _get_echo_identity_block()
        if identity:
            effective_system = f"{identity}\n\n{system}" if system else identity
    if effective_system:
        result.append({"role": "system", "content": effective_system})
    result.append({"role": "user", "content": prompt})
    return result


def _chat_ollama(messages: list, model: str, timeout: int = 1200, options: Optional[dict] = None) -> str:
    """
    Non-streaming /api/chat call. Same request/response shape and
    never-raise error philosophy as app/core/echo_tool_dispatch.py's
    _ollama_chat() (a working /api/chat precedent already in production for
    tool-dispatch decisions) — this is a general-purpose counterpart with no
    tools=/fixed-model baked in.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options or {"num_ctx": 8192, "num_predict": 512},
    }
    try:
        response = requests.post(CHAT_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return (data.get("message") or {}).get("content", "").strip()
    except Exception as e:
        logging.error(f"Ollama chat query failed: {traceback.format_exc()}")
        return f"[ERROR] Ollama chat query failed: {e}"


def _stream_chat_ollama(
    messages: list,
    model: str,
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
    options: Optional[dict] = None,
) -> Generator[str, None, None]:
    """
    Streaming /api/chat call. Confirmed live (2026-07-08, Ollama 0.30.10,
    deepseek-r1:7b and llama3.2:3b — see scripts/verify_chat_stream_shape.py)
    that /api/chat streams bare NDJSON per line identical in framing to
    /api/generate, just with content nested under 'message.content' /
    'message.thinking' (both incremental deltas needing concatenation, same
    as /api/generate's top-level 'response'/'thinking') instead of top-level
    'response'/'thinking'. Mirrors stream_query_ollama's thinking-buffer
    assembly logic exactly, adjusted for the nested field names.
    """
    is_thinking_model = _is_thinking_model(model)
    _options = dict(options or {})
    _options.setdefault("num_ctx", 8192)
    _options.setdefault("num_predict", max_tokens)
    if temperature is not None:
        _options["temperature"] = round(max(0.0, min(2.0, temperature)), 3)

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": _options,
    }

    try:
        with requests.post(CHAT_URL, json=payload, stream=True, timeout=1200) as resp:
            resp.raise_for_status()

            thinking_buffer: list[str] = []
            response_buffer: list[str] = []

            for line in resp.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8")

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logging.warning(f"Failed to decode JSON line from chat stream: {line}")
                    continue

                done = data.get("done", False)
                msg = data.get("message") or {}

                if is_thinking_model:
                    thinking_chunk = msg.get("thinking")
                    response_chunk = msg.get("content")

                    if thinking_chunk:
                        thinking_buffer.append(thinking_chunk)
                    if response_chunk:
                        response_buffer.append(response_chunk)

                    if done:
                        thinking_text = "".join(thinking_buffer).strip()
                        response_text = "".join(response_buffer).strip()

                        if thinking_text and response_text:
                            yield (
                                f"[Reasoning process]\n{thinking_text}\n\n"
                                f"[Conclusion]\n{response_text}"
                            )
                        elif response_text:
                            yield response_text
                        elif thinking_text:
                            yield thinking_text
                else:
                    content = msg.get("content")
                    if content:
                        yield content

    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException during streaming Ollama chat query: {e}")
        yield f"[ERROR] Ollama chat request failed: {e}"
    except Exception as e:
        logging.error(f"Unexpected error during streaming Ollama chat query: {traceback.format_exc()}")
        yield f"[ERROR] Unexpected error during Ollama chat streaming: {e}"


def is_ollama_running(host: str = "127.0.0.1", port: int = 11434) -> bool:
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except OSError:
        return False


def _read_stream(pipe, pipe_name: str):
    try:
        for line in iter(pipe.readline, ''):
            if not line:
                break
            logging.info(f"[OLLAMA {pipe_name}] {line.strip()}")
            if _ollama_stop_event.is_set():
                break
    except Exception as e:
        logging.error(f"Error reading Ollama {pipe_name} stream: {e}")


def start_ollama_server():
    global _ollama_process, _ollama_stop_event
    if is_ollama_running():
        logging.info("Ollama server already running.")
        return

    try:
        logging.info("Starting Ollama server...")
        _ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        _ollama_stop_event.clear()
        threading.Thread(target=lambda: _read_stream(_ollama_process.stdout, "STDOUT"), daemon=True).start()
        threading.Thread(target=lambda: _read_stream(_ollama_process.stderr, "STDERR"), daemon=True).start()

        timeout = 10
        start_time = time.time()
        while not is_ollama_running() and time.time() - start_time < timeout:
            time.sleep(0.5)

        if is_ollama_running():
            logging.info("Ollama server started successfully.")
        else:
            logging.warning("Ollama server did not start as expected.")
    except Exception:
        logging.error(f"Failed to start Ollama server: {traceback.format_exc()}")


def stop_ollama_server():
    global _ollama_process, _ollama_stop_event
    if _ollama_process:
        logging.info("Stopping Ollama server...")
        _ollama_stop_event.set()
        _ollama_process.terminate()
        try:
            _ollama_process.wait(timeout=10)
            logging.info("Ollama server stopped gracefully.")
        except subprocess.TimeoutExpired:
            logging.warning("Ollama server did not stop gracefully; killing.")
            _ollama_process.kill()
        _ollama_process = None




# ---- Query functions ----

def query_ollama(
    prompt: str,
    persona: Optional[Dict] = None,
    model: Optional[str] = None,
    timeout: int = 1200,
    system: Optional[str] = None,
    messages: Optional[list] = None,
) -> str:
    """
    Blocking Ollama query.
    Uses the model argument if provided, otherwise falls back to OLLAMA_MODEL env var.
    MLX routing: model names beginning with 'mlx:' are handled locally.

    system / messages: optional, additive-only. When either is given, this
    routes to /api/chat instead of /api/generate (see _chat_ollama()). When
    both are omitted (the default, and every existing caller as of this
    change), behavior and the request sent to Ollama are byte-identical to
    before this parameter existed.

    Traits injection: Echo's Modelfile SYSTEM block is the authority under
    /api/generate (Ollama applies it automatically). Under /api/chat it is
    NOT automatic — Ollama replaces rather than merges with it whenever an
    explicit system message is present. _build_chat_messages() actively
    restores it (prepended ahead of any situational system content) when
    model == OLLAMA_MODEL; this was silently not happening on this path
    since Finding 17 (2026-07-08) until this fix.
    """
    if model is None:
        model = OLLAMA_MODEL

    _patch_mlx_once()

    if (model or "").startswith("mlx:"):
        mlx_path = _get_mlx_path(model)
        if mlx_path:
            try:
                from app.mlx_handler import stream_query_mlx
                return "".join(stream_query_mlx(
                    prompt=prompt, mlx_path=mlx_path, model_name=model, system=system,
                ))
            except Exception as e:
                logging.error(f"[MLX] query_ollama MLX routing failed: {e}")
                return f"[ERROR] MLX routing failed: {e}"

    if messages is not None or system is not None:
        chat_messages = _build_chat_messages(prompt, system, messages, model=model)
        return _chat_ollama(chat_messages, model, timeout=timeout)

    logging.debug(f"Querying Ollama with prompt: {prompt}")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 8192, "num_predict": 512}
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        logging.error(f"Ollama query failed: {traceback.format_exc()}")
        return f"[ERROR] Ollama query failed: {e}"


def generate_code(prompt: str, max_tokens: int = 500) -> str:
    """
    Generate Python code using Ollama.
    Wraps prompt with strict constraints so the model produces
    headless, non-interactive Python code instead of creative projects.
    """
    constrained_prompt = (
        "You are a Python code generator for an autonomous AI system. "
        "Output ONLY raw Python code. No markdown. No code fences. "
        "No input() calls. No interactive elements. No while True loops. "
        "No explanations or comments outside the code. "
        "The code must run headlessly without any user interaction. "
        "If the task cannot be done without input(), return only: pass\n\n"
        f"Task: {prompt}"
    )

    response = query_ollama(constrained_prompt)

    if "```python" in response:
        try:
            response = response.split("```python")[1].split("```")[0].strip()
        except IndexError:
            logging.warning("Failed to parse Python code block from Ollama response.")

    response = response.strip().strip("```").strip()

    try:
        ast.parse(response)
    except SyntaxError:
        logging.warning("Generated code has syntax errors. Returning empty string.")
        return ""

    return response


def stream_query_ollama(
    prompt: str,
    persona: Optional[Dict] = None,
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
    system: Optional[str] = None,
    messages: Optional[list] = None,
) -> Generator[str, None, None]:
    """
    Stream Ollama token by token with robust error handling.
    Uses the model argument if provided, otherwise falls back to OLLAMA_MODEL env var.

    Traits injection: Echo's Modelfile SYSTEM block is the authority under
    /api/generate (Ollama applies it automatically). Under /api/chat it is
    NOT automatic — Ollama replaces rather than merges with it whenever an
    explicit system message is present. _build_chat_messages() actively
    restores it (prepended ahead of any situational system content) when
    model == OLLAMA_MODEL; this was silently not happening on this path
    since Finding 17 (2026-07-08) until this fix.

    DeepSeek-R1 handling: the model emits a 'thinking' field containing its
    chain-of-thought reasoning before populating the 'response' field. Both
    streams are buffered separately and assembled into a single yield once
    'done: true' arrives. The thinking chain is prefixed with a clear label
    so Echo's synthesis prompt receives the full argument, not just the
    conclusion. For all other models the behaviour is unchanged — tokens
    are yielded as they arrive.

    MLX routing: model names beginning with 'mlx:' are routed directly to
    Apple Silicon inference via mlx-lm instead of the Ollama HTTP API.

    system / messages: optional, additive-only. When either is given, this
    routes to /api/chat instead of /api/generate (see _stream_chat_ollama(),
    whose streaming shape was confirmed live 2026-07-08 against a running
    deepseek-r1:7b and llama3.2:3b — see scripts/verify_chat_stream_shape.py).
    When both are omitted (the default, and every existing caller as of this
    change), behavior and the request sent to Ollama are byte-identical to
    before this parameter existed.
    """
    if model is None:
        model = OLLAMA_MODEL

    # Register MLX models into MODEL_POOL on first call (app fully loaded by now)
    _patch_mlx_once()

    # Route mlx:* models to the MLX backend
    if (model or "").startswith("mlx:"):
        mlx_path = _get_mlx_path(model)
        if mlx_path:
            try:
                from app.mlx_handler import stream_query_mlx
                yield from stream_query_mlx(
                    prompt=prompt,
                    mlx_path=mlx_path,
                    model_name=model,
                    max_tokens=max_tokens,
                    system=system,
                    temperature=temperature,
                )
            except Exception as e:
                logging.error(f"[MLX] stream_query_mlx raised: {e}")
                yield f"[ERROR] MLX routing failed: {e}"
            return
        else:
            logging.warning(f"[MLX] No mlx_path found for {model} — falling through to Ollama")

    if messages is not None or system is not None:
        chat_messages = _build_chat_messages(prompt, system, messages, model=model)
        yield from _stream_chat_ollama(
            chat_messages, model, max_tokens=max_tokens, temperature=temperature
        )
        return

    logging.debug(f"Streaming query to Ollama model={model} with prompt: {prompt}")

    # Detect whether this model emits thinking tokens so we know
    # whether to buffer or stream. DeepSeek-R1 variants always think.
    is_thinking_model = _is_thinking_model(model)

    options: dict = {"num_ctx": 8192, "num_predict": max_tokens}
    if temperature is not None:
        options["temperature"] = round(max(0.0, min(2.0, temperature)), 3)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": options,
    }

    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=1200) as resp:
            resp.raise_for_status()

            # Buffers for thinking models — assembled and yielded once done.
            thinking_buffer: list[str] = []
            response_buffer: list[str] = []

            for line in resp.iter_lines():
                if not line:
                    continue

                if isinstance(line, bytes):
                    line = line.decode('utf-8')

                logging.debug(f"Raw stream line: {line}")

                if line.startswith("data: "):
                    line = line[len("data: "):]

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    logging.warning(f"Failed to decode JSON line from stream: {line}")
                    continue

                done = data.get("done", False)

                if is_thinking_model:
                    # Collect thinking and response tokens separately.
                    thinking_chunk = data.get("thinking")
                    response_chunk = data.get("response") or data.get("text")

                    if thinking_chunk:
                        thinking_buffer.append(thinking_chunk)
                    if response_chunk:
                        response_buffer.append(response_chunk)

                    if done:
                        # Assemble and yield the complete output.
                        thinking_text = "".join(thinking_buffer).strip()
                        response_text = "".join(response_buffer).strip()

                        if thinking_text and response_text:
                            # Pass full reasoning chain to council so Echo
                            # synthesises from the argument, not just the conclusion.
                            yield (
                                f"[Reasoning process]\n{thinking_text}\n\n"
                                f"[Conclusion]\n{response_text}"
                            )
                        elif response_text:
                            yield response_text
                        elif thinking_text:
                            # Thinking with no separate conclusion — yield as-is.
                            yield thinking_text

                else:
                    # Standard streaming — yield tokens as they arrive.
                    token = data.get("token")
                    if token:
                        yield token
                    else:
                        partial = data.get("response") or data.get("text")
                        if partial:
                            yield partial

    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException during streaming Ollama query: {e}")
        yield f"[ERROR] Ollama request failed: {e}"
    except Exception as e:
        logging.error(f"Unexpected error during streaming Ollama query: {traceback.format_exc()}")
        yield f"[ERROR] Unexpected error during Ollama streaming: {e}"
