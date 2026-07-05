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

# ---- MLX routing ----
# Patched once on first query — safe because ollama_handler is imported
# lazily (inside _ollama_query), so the app is fully initialized by then.
_mlx_pool_patched = False

def _patch_mlx_once() -> None:
    global _mlx_pool_patched
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
PERSONA_FILE = os.path.join(os.path.dirname(__file__), "persona.json")

_ollama_process: Optional[subprocess.Popen] = None
_ollama_stop_event = threading.Event()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


# ---- Helper functions ----

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

def query_ollama(prompt: str, persona: Optional[Dict] = None, model: Optional[str] = None, timeout: int = 1200) -> str:
    """
    Blocking Ollama query.
    Uses the model argument if provided, otherwise falls back to OLLAMA_MODEL env var.
    No traits injection — Echo's Modelfile identity is the authority.
    MLX routing: model names beginning with 'mlx:' are handled locally.
    """
    if model is None:
        model = OLLAMA_MODEL

    _patch_mlx_once()

    if (model or "").startswith("mlx:"):
        mlx_path = _get_mlx_path(model)
        if mlx_path:
            try:
                from app.mlx_handler import stream_query_mlx
                return "".join(stream_query_mlx(prompt=prompt, mlx_path=mlx_path, model_name=model))
            except Exception as e:
                logging.error(f"[MLX] query_ollama MLX routing failed: {e}")
                return "I'm having trouble thinking right now. Please try again later."

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
    except Exception:
        logging.error(f"Ollama query failed: {traceback.format_exc()}")
        return "I'm having trouble thinking right now. Please try again later."


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
) -> Generator[str, None, None]:
    """
    Stream Ollama token by token with robust error handling.
    Uses the model argument if provided, otherwise falls back to OLLAMA_MODEL env var.
    No traits injection — Echo's Modelfile identity is the authority.

    DeepSeek-R1 handling: the model emits a 'thinking' field containing its
    chain-of-thought reasoning before populating the 'response' field. Both
    streams are buffered separately and assembled into a single yield once
    'done: true' arrives. The thinking chain is prefixed with a clear label
    so Echo's synthesis prompt receives the full argument, not just the
    conclusion. For all other models the behaviour is unchanged — tokens
    are yielded as they arrive.

    MLX routing: model names beginning with 'mlx:' are routed directly to
    Apple Silicon inference via mlx-lm instead of the Ollama HTTP API.
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
                )
            except Exception as e:
                logging.error(f"[MLX] stream_query_mlx raised: {e}")
                yield "I'm having trouble thinking right now. Please try again later."
            return
        else:
            logging.warning(f"[MLX] No mlx_path found for {model} — falling through to Ollama")

    logging.debug(f"Streaming query to Ollama model={model} with prompt: {prompt}")

    # Detect whether this model emits thinking tokens so we know
    # whether to buffer or stream. DeepSeek-R1 variants always think.
    is_thinking_model = "deepseek" in (model or "").lower()

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
        yield "I'm having trouble thinking right now. Please try again later."
    except Exception:
        logging.error(f"Unexpected error during streaming Ollama query: {traceback.format_exc()}")
        yield "I'm having trouble thinking right now. Please try again later."
