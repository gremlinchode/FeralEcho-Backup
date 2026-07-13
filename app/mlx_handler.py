"""
MLX-LM backend for FeralEcho.

Provides stream_query_mlx() with the same generator interface as
stream_query_ollama(), so river_deliberation._ollama_query() can
route mlx:* model names to Apple Silicon inference without touching
any protected files.

Models are configured in mlx_models.json at the project root.
"""

import json
import logging
import os
import re
from typing import Generator

_MLX_AVAILABLE = False
try:
    from mlx_lm import load as _mlx_load, generate as _mlx_generate
    from mlx_lm.sample_utils import make_sampler as _mlx_make_sampler
    _MLX_AVAILABLE = True
    logging.info("[MLX] mlx-lm backend available")
except ImportError:
    logging.warning("[MLX] mlx-lm not installed — MLX backend disabled")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MLX_MODELS_CONFIG = os.path.join(_PROJECT_ROOT, "mlx_models.json")

# (model, tokenizer) pairs keyed by mlx_path — loading is expensive (~10s)
_model_cache: dict = {}

# Strip Qwen3 chain-of-thought tags before handing text to the council
_THINK_TAG_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _load_mlx_model(mlx_path: str):
    if mlx_path not in _model_cache:
        logging.info(f"[MLX] Loading {mlx_path} — first load may take ~10-30s")
        _model_cache[mlx_path] = _mlx_load(mlx_path)
        logging.info(f"[MLX] {mlx_path} ready")
    return _model_cache[mlx_path]


def _format_prompt(tokenizer, prompt: str, model_name: str, system: str = None) -> str:
    """
    Apply the model's chat template so instruction-tuned models respond
    in the right format. Disables Qwen3 thinking mode for council use —
    we want the conclusion, not the chain-of-thought.

    system: optional system-role turn, prepended ahead of the user turn.
    The tokenizer's chat template already supports a system role natively —
    this only needed a kwarg to actually use it, so mlx:* councillors don't
    regress to system-content-stuffed-in-the-user-turn once Ollama
    councillors in the same council cycle get real system messages
    (see river_deliberation.py's system= threading).
    """
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        kwargs = {"tokenize": False, "add_generation_prompt": True}
        if "qwen3" in model_name.lower() or "qwen-3" in model_name.lower():
            kwargs["enable_thinking"] = False
        return tokenizer.apply_chat_template(messages, **kwargs)
    except Exception:
        return prompt


def stream_query_mlx(
    prompt: str,
    mlx_path: str,
    model_name: str = "",
    max_tokens: int = 1024,
    system: str = None,
    temperature: float = None,
) -> Generator[str, None, None]:
    """
    Run inference on an MLX model and yield the response as a single chunk.
    Interface mirrors stream_query_ollama() so it drops in anywhere that
    function is called.

    temperature: previously silently dropped entirely — stream_query_ollama's
    MLX routing branch didn't forward it and this function had no parameter
    to receive it. mlx_lm's generate_step() defaults to a greedy/argmax
    sampler when none is given (make_sampler's own temp=0.0 default), so
    MLX councillors were generating fully deterministic output every call
    regardless of what temperature the rest of a council cycle used — worse
    than "same fixed operating point" (the Ollama-side half of this finding),
    genuinely zero sampling diversity. When temperature is given, builds a
    real sampler so MLX councillors match Ollama councillors' behavior in
    the same cycle instead of regressing to greedy decoding.
    """
    if not _MLX_AVAILABLE:
        yield "[ERROR] MLX backend is not available."
        return
    try:
        model, tokenizer = _load_mlx_model(mlx_path)
        formatted = _format_prompt(tokenizer, prompt, model_name or mlx_path, system=system)
        _gen_kwargs = {}
        if temperature is not None:
            _gen_kwargs["sampler"] = _mlx_make_sampler(temp=max(0.0, min(2.0, temperature)))
        response = _mlx_generate(
            model,
            tokenizer,
            prompt=formatted,
            max_tokens=max_tokens,
            verbose=False,
            **_gen_kwargs,
        )
        # Strip any residual thinking tags (Qwen3 safety net)
        response = _THINK_TAG_RE.sub("", response).strip()
        yield response
    except Exception as e:
        logging.error(f"[MLX] Generation failed for {mlx_path}: {e}")
        yield f"[ERROR] MLX generation failed: {e}"


def list_mlx_models() -> dict:
    """
    Read mlx_models.json and return a MODEL_POOL-compatible dict.
    Each entry mirrors the shape built by list_ollama_models() and
    adds 'mlx_path' + 'backend' keys used for routing.
    """
    if not os.path.exists(MLX_MODELS_CONFIG):
        return {}
    try:
        with open(MLX_MODELS_CONFIG) as f:
            configs = json.load(f)
        pool = {}
        for entry in configs:
            name = entry["name"]
            pool[name] = {
                "name": name,
                "type": entry.get("type", "general"),
                "tags": entry.get("tags", ["general"]),
                "mlx_path": entry["mlx_path"],
                "backend": "mlx",
            }
        logging.info(f"[MLX] Config loaded: {list(pool.keys())}")
        return pool
    except Exception as e:
        logging.warning(f"[MLX] Failed to parse mlx_models.json: {e}")
        return {}


def patch_model_pool() -> None:
    """
    Inject MLX models into the orchestrator's MODEL_POOL.
    Called lazily on first use — by that point echo_model_orchestrator
    is fully initialized so the import is safe.
    """
    mlx_pool = list_mlx_models()
    if not mlx_pool:
        return
    try:
        from app.core.echo_model_orchestrator import MODEL_POOL
        MODEL_POOL.update(mlx_pool)
        logging.info(f"[MLX] Registered into MODEL_POOL: {list(mlx_pool.keys())}")
    except Exception as e:
        logging.warning(f"[MLX] MODEL_POOL patch failed: {e}")
