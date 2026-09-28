"""
Minimal, standalone Ollama HTTP client for this experiment. Imports nothing
from app.* -- calls Ollama's own HTTP API directly with a plain `requests`
call, exactly mirroring the frozen persistent-competence protocol's own
[INF-1]/[INF-2]/[INF-3] convention: POST /api/chat, stream=false, a fresh
single-turn [system, user] message pair every call (no history, no shared
Ollama `context`), fixed low-temperature sampling for a low-noise pilot.

This never touches river_deliberation.py, echo_model_orchestrator.py, or
any other FeralEcho inference path -- no council selection, no synthesis,
no RiverBrain observation, no production logging of any kind.
"""
from __future__ import annotations

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:7b"

SYSTEM_PROMPT = (
    "You are a careful Python programmer. Respond with exactly one fenced "
    "Python code block that defines the function `solve` as specified. "
    "Do not include explanations, tests, or example calls outside the "
    "code block."
)

_TEMPERATURE = 0.0
_NUM_PREDICT = 700
_NUM_CTX = 4096
_SEED = 20260923


def build_user_prompt(task: dict, context_block: str) -> str:
    return (
        f"Task:\n{task['description']}\n\n"
        f"Function signature:\ndef solve(intervals: list[list[int]]) -> list[list[int]]\n\n"
        f"Example (illustrative only, not graded):\n"
        f"Input: {task['example_input']}\n"
        f"Output: {task['example_output']}\n"
        f"{context_block}"
        f"Write the function `solve` now."
    )


def generate(user_prompt: str, *, timeout_s: int = 120) -> dict:
    """One fresh, single-turn call. Returns a dict with `content` (the raw
    response text) and `done_reason`, or an `error` key on any failure --
    never raises, so a single infra hiccup doesn't kill a whole batch."""
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": _TEMPERATURE,
            "top_p": 1.0,
            "num_predict": _NUM_PREDICT,
            "num_ctx": _NUM_CTX,
            "seed": _SEED,
        },
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        message = data.get("message", {}) or {}
        return {
            "content": message.get("content", ""),
            "done_reason": data.get("done_reason"),
            "model": data.get("model"),
        }
    except Exception as e:
        return {"content": "", "error": f"{type(e).__name__}: {e}"}
