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
import threading
from typing import Generator

_MLX_AVAILABLE = False
try:
    from mlx_lm import load as _mlx_load, generate as _mlx_generate
    from mlx_lm.sample_utils import make_sampler as _mlx_make_sampler
    import mlx.core as _mx
    _MLX_AVAILABLE = True
    logging.info("[MLX] mlx-lm backend available")
except ImportError:
    logging.warning("[MLX] mlx-lm not installed — MLX backend disabled")

# 2026-07-22 (CLAUDE.md Finding 73/74) — a real, cheap mitigation for the
# native mlx::core::gpu::check_error crash, suggested independently by an
# external AI-council consultation and confirmed available in the
# installed MLX version before adding it (this repo previously set no
# memory limit or cache policy at all). This machine has 24GB total
# unified memory shared with the OS, Ollama's own models, and everything
# else FeralEcho runs; 8GB is a conservative cap for MLX's own Metal
# allocations specifically — generous for these 4-bit-quantized models'
# real footprint, but a real ceiling against the unbounded KV-cache/
# allocator growth the crash reports point at. Set once, lazily, on first
# real use rather than at import time (matches _load_mlx_model()'s own
# lazy-load convention) so importing this module never has a side effect
# on Metal state before MLX is actually used.
_memory_limit_set = False


def _ensure_mlx_memory_limit() -> None:
    global _memory_limit_set
    if _memory_limit_set or not _MLX_AVAILABLE:
        return
    try:
        _mx.set_memory_limit(8 * 1024 ** 3)
        _memory_limit_set = True
        logging.info("[MLX] Set Metal memory limit to 8GB")
    except Exception as e:
        logging.debug(f"[MLX] set_memory_limit failed, continuing without a cap: {e}")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MLX_MODELS_CONFIG = os.path.join(_PROJECT_ROOT, "mlx_models.json")

# 2026-07-22, decided with Gremlin ahead of an extended (month+) unattended
# absence, after a real crash-rate escalation (CLAUDE.md Finding 73) and a
# genuine external-council consultation (ChatGPT/Gemini/Grok/DeepSeek, all
# converging on "don't retire everything, but the cheap reversible fixes
# are worth doing"). mlx:gemma3 (mlx-community/gemma-3-12b-it-4bit) is
# retired here, mirroring _RETIRED_MODELS' exact shape and reasoning in
# echo_model_orchestrator.py — soft, code-level, trivially reversed by
# deleting this one line, not an uninstall. Not a like-for-like swap:
# Ollama's already-pulled gemma3:4b is a smaller 4B variant of the same
# model family, not the identical 12B weights, but it already carries
# real, overlapping tags (creative/story/poetry) and needs zero new
# downloads or setup, which is what made this the obvious first move
# rather than qwen3 (no comparably-close Ollama equivalent already
# pulled). qwen3 stays in rotation; see stream_query_mlx() for the real
# memory-cap mitigation added in the same change instead.
_RETIRED_MLX_MODELS = {"mlx:gemma3"}

# (model, tokenizer) pairs keyed by mlx_path — loading is expensive (~10s)
_model_cache: dict = {}

# Guards both the cache check-and-set below and the generate() call itself.
# Neither was locked before 2026-07-13: two independent HarmonyManager
# instances (see autonomous_harmony_manager.py's get_harmony_manager(),
# fixed the same day) started concurrent Nature Spark sessions that both
# called _mlx_generate() on the same cached model object from different
# threads at once — MLX's Metal-backed generation isn't designed for
# concurrent calls sharing one model instance. This lock is deliberately
# global rather than per-mlx_path: a real council cycle can also select
# an mlx:* model as a councillor while Harmony is separately active, and
# whether two *different* MLX models can safely run concurrently on the
# same Metal device wasn't verified either — serializing all MLX
# inference through one lock is the smaller, more conservative claim.
# MLX calls are single-shot response generations (not long-running), so
# queuing behind this lock is a short wait, not a functional block.
_generate_lock = threading.Lock()

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
        _ensure_mlx_memory_limit()
        with _generate_lock:
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
            # Same Finding 73/74 mitigation as the memory limit above: clear
            # MLX's cached Metal buffers after every real generation call,
            # inside the lock (this is process-wide Metal state, same as
            # the memory limit — clearing it while another thread could be
            # mid-generation would be wrong, not just untidy). Best-effort:
            # a failure here must never lose a real response that already
            # generated successfully.
            try:
                _mx.clear_cache()
            except Exception as e:
                logging.debug(f"[MLX] clear_cache failed (non-fatal): {e}")
        # Strip any residual thinking tags (Qwen3 safety net) — pure string
        # work, done outside the lock so it doesn't hold up the next caller.
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
            if name in _RETIRED_MLX_MODELS:
                continue
            pool[name] = {
                "name": name,
                "type": entry.get("type", "general"),
                "tags": entry.get("tags", ["general"]),
                "mlx_path": entry["mlx_path"],
                "backend": "mlx",
            }

        # "Learned avoidance" (2026-07-21, differential audit follow-up):
        # filter out any model currently under crash-avoidance (recent
        # mlx::core::gpu::check_error cluster, CLAUDE.md Finding 49) at the
        # single source both patch_model_pool() and _get_mlx_path() read
        # from — same exclusion mechanism _RETIRED_MODELS already uses in
        # echo_model_orchestrator.py, just temporary instead of permanent.
        try:
            from app.core.crash_awareness import is_mlx_avoidance_active
            if pool and is_mlx_avoidance_active():
                logging.warning(f"[MLX] Avoidance active — withholding from pool: {list(pool.keys())}")
                pool = {}
        except Exception:
            pass  # avoidance check is best-effort; never blocks normal model listing

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


def generate_with_ollama_fallback(
    prompt: str,
    mlx_model_name: str,
    max_tokens: int = 300,
    ollama_fallback_model: str = "llama3.2:3b",
    system: str = None,
) -> str:
    """
    Try the named MLX model first; if it's unavailable — crash_awareness.py's
    avoidance engaged (2026-07-21), or genuinely unconfigured — fall back to
    a real Ollama model instead of jumping straight to canned/template
    output. Added after avoidance (built the same night) was found to force
    autonomous_harmony_manager.py's Nature Spark, autonomous_awareness.py's
    dream cycle, and reflection_shard.py's real reflections into permanent
    fixed-string/template fallback for the whole avoidance window — none of
    the three had any fallback besides MLX, so "genuine generation
    unavailable" (their own documented trigger for the canned fallback)
    became true for hours at a stretch instead of the rare edge case it was
    designed around.

    Always returns a string (possibly empty on total failure) — a drop-in
    replacement for the "".join(stream_query_mlx(...)).strip() pattern
    every call site already used, so callers' existing empty-string/
    "[ERROR]" handling needs no other change. Never raises.
    """
    try:
        mlx_path = list_mlx_models().get(mlx_model_name, {}).get("mlx_path")
        if mlx_path:
            text = "".join(
                stream_query_mlx(prompt, mlx_path, model_name=mlx_model_name, max_tokens=max_tokens, system=system)
            ).strip()
            if text and "[ERROR]" not in text:
                return text
    except Exception as e:
        logging.debug(f"[MLX] {mlx_model_name} generation failed, trying Ollama fallback: {e}")

    try:
        from app.ollama_handler import stream_query_ollama
        text = "".join(
            stream_query_ollama(prompt, model=ollama_fallback_model, max_tokens=max_tokens, system=system)
        ).strip()
        if text and "[ERROR]" not in text:
            return text
    except Exception as e:
        logging.debug(f"[MLX] Ollama fallback ({ollama_fallback_model}) also failed: {e}")

    return ""
