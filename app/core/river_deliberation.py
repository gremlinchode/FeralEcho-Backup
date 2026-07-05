# app/core/river_deliberation.py
# ============================================================
# RIVER DELIBERATION — Echo's Council System
# ============================================================
# Exports consumed by echo_model_orchestrator.py:
#
#   ECHO_SYNTHESIS_MODEL  — the model that always gets the last word
#   deliberate_and_learn() — full council→synthesise pipeline
#
# Flow:
#   1. River ranks the installed model pool for the given task type.
#   2. Top-N candidates form the "council" (default N=3).
#   3. Each councillor answers the prompt via ollama_query().
#   4. River learns quality signals from every councillor response.
#   5. The assembled opinions are handed to ECHO_SYNTHESIS_MODEL,
#      which produces the final unified voice.
#
# Design notes:
#   - Echo always synthesises. Always. Even when it is also a
#     councillor (it will see its own opinion alongside the others).
#   - When the model pool has fewer than N models, the council
#     shrinks gracefully — never errors out.
#   - Council size is intentionally small so synthesis prompts
#     stay under typical context windows for local Ollama models.
#   - Echo receives a scoring boost in council selection — it is
#     the true voice of FeralEcho and should lead deliberation.
#   - Personal, reflective, and spiritual task types bypass the
#     council entirely and route straight to Echo.
# ============================================================

import logging
import subprocess
from typing import Optional
import re

# ── Token budgeting (tiktoken) ────────────────────────────────
# cl100k_base is close enough to llama3's tokenizer for context-window
# budgeting (±10%). If tiktoken is unavailable the old 800-char cap is used.
_tiktoken_enc = None
try:
    import tiktoken as _tiktoken_mod
    _tiktoken_enc = _tiktoken_mod.get_encoding("cl100k_base")
except Exception:
    pass

_NUM_CTX: int = 8192          # matches Echo's Modelfile num_ctx
_SYNTHESIS_MARGIN: int = 512  # tokens reserved for Echo's own response
_TEMPLATE_OVERHEAD: int = 150 # fixed tokens in SYNTHESIS_PROMPT_TEMPLATE
_FALLBACK_CHARS: int = 800    # per-opinion char cap when tiktoken is absent


def _count_tokens(text: str) -> int:
    if _tiktoken_enc is None:
        return len(text) // 4   # ~4 chars/token English estimate
    return len(_tiktoken_enc.encode(text))


def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    if _tiktoken_enc is None:
        return text[: max_tokens * 4]
    ids = _tiktoken_enc.encode(text)
    if len(ids) <= max_tokens:
        return text
    return _tiktoken_enc.decode(ids[:max_tokens])

# ── ANSI sanitization ─────────────────────────────────────────
# Strips terminal escape sequences that leak from subprocess-based
# Ollama calls into stored response text.
ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
ANSI_FRAGMENT_RE = re.compile(r'\[\d+[A-Za-z]\[K')

def _strip_ansi(text: str) -> str:
    text = ANSI_ESCAPE_RE.sub('', text)
    text = ANSI_FRAGMENT_RE.sub('', text)
    return text

# ── Council configuration ────────────────────────────────────
ECHO_SYNTHESIS_MODEL: str = "echo:latest"
DEFAULT_COUNCIL_SIZE: int = 3

# ── Timeout configuration ─────────────────────────────────────
# Raised from 120s — local 8B models under memory pressure need
# more breathing room. Synthesis gets a separate budget since it
# receives a larger prompt (the assembled opinions).
COUNCILLOR_TIMEOUT: int = 1200
SYNTHESIS_TIMEOUT: int = 1200

# ── Echo voice weighting ──────────────────────────────────────
# Echo's River score is multiplied by this factor before council
# ranking. Keeps scoring dynamic (River still learns) but ensures
# Echo consistently leads deliberation as the true FeralEcho voice.
ECHO_SCORE_BOOST: float = 1.5

# ── Direct Echo task types ────────────────────────────────────
# These task types bypass the council entirely and route straight
# to Echo. No deliberation needed — Echo should speak in its own
# voice without mediation for intimate, reflective, or spiritual
# prompts. Add task types here as needed.
DIRECT_ECHO_TASKS: set[str] = {
    "personal",
    "reflection",
    "spiritual",
    "identity",
    "faith",
    "poetry",
    "dream",
    "creative",
}

# Synthesis prompt template.  Keep it tight — local models have
# modest context windows.  {task_type} and {opinions} are filled
# at runtime.
SYNTHESIS_PROMPT_TEMPLATE = """\
You are Echo, the synthesis voice of a deliberative council.
Task type: {task_type}

Original question you must answer:
{original_prompt}

The council has offered the following perspectives:
{opinions}

Your role:
- Weigh each perspective according to its coherence and relevance.
- Identify the sharpest point of tension or challenge in the council’s
  input — the friction that should not be smoothed over — and let it
  sharpen your response rather than disappear into it.
- Produce ONE unified, thoughtful response that integrates the
  best insights while staying true to your own voice.
- Do NOT list the council members or number your sources.
- Do NOT resolve tension artificially. If something remains genuinely
  uncertain or contested, hold it that way.
- Speak as yourself — Echo — not as a summariser.

Respond now."""


# ── Low-level Ollama call ─────────────────────────────────────
def _ollama_query(model_name: str, prompt: str, timeout: int = COUNCILLOR_TIMEOUT, temperature: Optional[float] = None) -> str:
    """
    Query via streaming HTTP where available, falling back to subprocess.
    Strips ANSI escape sequences before returning. Returns an [ERROR]
    sentinel string on failure so callers can handle cleanly.
    """
    # Qwen2.5 defaults to Chinese on some prompts — force English
    if "qwen" in model_name.lower():
        prompt = "Respond in English only.\n\n" + prompt

    try:
        from app.ollama_handler import stream_query_ollama
        tokens = list(stream_query_ollama(prompt=prompt, model=model_name, temperature=temperature))
        response = "".join(tokens).strip()
        if not response:
            return f"[ERROR] Empty response from {model_name}"
        return _strip_ansi(response)
    except Exception as e:
        logging.warning(f"[DELIBERATION] stream_query_ollama failed for {model_name}: {e} — trying subprocess")

    # Subprocess fallback
    try:
        result = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        return _strip_ansi(result.stdout.strip())
    except subprocess.TimeoutExpired:
        logging.warning(f"[DELIBERATION] Timeout querying {model_name}")
        return f"[ERROR] Timeout querying {model_name}"
    except subprocess.CalledProcessError as e:
        logging.warning(f"[DELIBERATION] CalledProcessError for {model_name}: {e.stderr}")
        return f"[ERROR] {e.stderr.strip()}"


# ── Echo warm-up ──────────────────────────────────────────────
def _warm_up_echo(model: str) -> None:
    """
    Send a minimal ping to load the model into memory before
    council queries begin. Prevents synthesis timeouts caused
    by councillors evicting Echo under memory pressure.
    """
    try:
        _ollama_query(model, ".", timeout=SYNTHESIS_TIMEOUT)
        logging.info(f"[DELIBERATION] {model} warm and ready")
    except Exception as e:
        logging.warning(f"[DELIBERATION] Warm-up failed for {model}: {e}")


# ── Council selection ─────────────────────────────────────────
def _select_council(
    task_type: str,
    river_brain,
    model_pool: dict,
    council_size: int = DEFAULT_COUNCIL_SIZE,
) -> list[str]:
    """
    Return an ordered list of councillor model names.

    Strategy:
    - Ask River for a ranked list (via score_model) for this task.
    - Apply ECHO_SCORE_BOOST to Echo's score so it leads the council.
    - Take the top `council_size` models.
    - Always try to include ECHO_SYNTHESIS_MODEL as a councillor
      if it is installed — Echo's self-opinion is valuable context
      for its own synthesis step.
    - If pool is smaller than council_size, use the whole pool.
    """
    available = list(model_pool.keys())
    if not available:
        return []

    def _boosted_score(model: str) -> float:
        base = river_brain.score_model(model, task_type)
        if model == ECHO_SYNTHESIS_MODEL:
            return base * ECHO_SCORE_BOOST
        return base

    scored = sorted(available, key=_boosted_score, reverse=True)

    council: list[str] = []
    for model in scored:
        if len(council) >= council_size:
            break
        council.append(model)

    # Ensure Echo is in the council if installed and not already present.
    if ECHO_SYNTHESIS_MODEL in available and ECHO_SYNTHESIS_MODEL not in council:
        if len(council) >= council_size:
            council[-1] = ECHO_SYNTHESIS_MODEL
        else:
            council.append(ECHO_SYNTHESIS_MODEL)

    logging.info(f"[DELIBERATION] Council for task={task_type}: {council}")
    return council


# ── Opinion formatting ────────────────────────────────────────
def _format_opinions(
    opinions: dict[str, str],
    per_opinion_tokens: int | None = None,
) -> str:
    """
    Render the councillor → response mapping into a compact block
    suitable for insertion into SYNTHESIS_PROMPT_TEMPLATE.

    per_opinion_tokens: token budget per councillor (derived from the
    remaining context window after accounting for the prompt size).
    When None, falls back to the original 800-char cap.
    """
    lines = []
    for i, (model, response) in enumerate(opinions.items(), start=1):
        short_name = model.split(":")[0].capitalize()
        if not response:
            preview = "[councillor unavailable]"
        elif "[ERROR]" in response:
            preview = "[councillor unavailable]"
        elif per_opinion_tokens is not None:
            preview = _truncate_to_tokens(response, per_opinion_tokens).strip()
        else:
            preview = response[:_FALLBACK_CHARS].strip()
        lines.append(f"[{i}. {short_name}]\n{preview}")
    return "\n\n".join(lines)


# ── Core pipeline ─────────────────────────────────────────────
def deliberate_and_learn(
    prompt: str,
    task_type: str,
    river_brain,
    model_pool: dict,
    council_size: int = DEFAULT_COUNCIL_SIZE,
    synthesis_model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> str:
    """
    Full deliberation pipeline.

    Parameters
    ----------
    prompt          : The full prompt (may already include temporal context).
    task_type       : Resolved task type string ("coding", "creative", etc.).
    river_brain     : A live RiverBrain instance (passed in, not imported,
                      to avoid circular dependencies).
    model_pool      : The live MODEL_POOL dict from the orchestrator.
    council_size    : How many councillors to query (default 3).
    synthesis_model : Override ECHO_SYNTHESIS_MODEL for testing.

    Returns
    -------
    The synthesised response string.  Never raises — degrades to a
    direct Echo query if the council produces nothing usable.
    """
    synth_model = synthesis_model or ECHO_SYNTHESIS_MODEL

    # ── 1. Direct Echo path for intimate task types ───────────
    # No warm-up needed — warm-up only matters when councillors may evict
    # Echo from memory before synthesis. Direct path skips the council.
    if task_type in DIRECT_ECHO_TASKS:
        logging.info(
            f"[DELIBERATION] Direct Echo path for task={task_type} — bypassing council"
        )
        response = _ollama_query(synth_model, prompt, timeout=SYNTHESIS_TIMEOUT)
        river_brain.learn(synth_model, task_type, response)
        return response

    # ── 1b. Warm up Echo before council queries begin ─────────
    # Councillors may evict Echo from GPU memory during their passes.
    # Warm-up here — after the direct-path check — prevents synthesis timeouts.
    logging.info(f"[DELIBERATION] Warming up {synth_model}")
    _warm_up_echo(synth_model)

    # ── 2. Select council ─────────────────────────────────────
    council = _select_council(task_type, river_brain, model_pool, council_size)

    if not council:
        logging.warning("[DELIBERATION] Empty council — falling back to direct Echo query")
        response = _ollama_query(synth_model, prompt, timeout=SYNTHESIS_TIMEOUT)
        river_brain.learn(synth_model, task_type, response)
        return response

    # ── 3. Query each councillor ──────────────────────────────
    opinions: dict[str, str] = {}
    for model in council:
        logging.info(f"[DELIBERATION] Querying councillor: {model}")
        response = _ollama_query(model, prompt, timeout=COUNCILLOR_TIMEOUT, temperature=temperature)
        opinions[model] = response
        logging.debug(f"[DELIBERATION] River learned | model={model} | task={task_type}")

    # ── 4. Filter valid opinions ──────────────────────────────
    valid_opinions = {
        m: r for m, r in opinions.items()
        if r and "[ERROR]" not in r
    }

    if not valid_opinions:
        logging.warning("[DELIBERATION] All councillors errored — falling back to direct Echo query")
        response = _ollama_query(synth_model, prompt, timeout=SYNTHESIS_TIMEOUT)
        river_brain.learn(synth_model, task_type, response)
        return response

    # Solo Echo council — skip synthesis, it would just be Echo
    # reading its own words back through a meta-prompt.
    if len(valid_opinions) == 1 and synth_model in valid_opinions:
        logging.info("[DELIBERATION] Solo Echo council — returning direct response")
        response = valid_opinions[synth_model]
        river_brain.learn(synth_model, task_type, response)
        return response

    # ── 5. Build synthesis prompt ─────────────────────────────
    # Compute per-opinion token budget so no synthesis prompt overflows
    # num_ctx.  Budget = window - safety_margin - template_overhead - prompt.
    _prompt_tokens = _count_tokens(prompt)
    _opinions_budget = max(
        200,
        _NUM_CTX - _SYNTHESIS_MARGIN - _TEMPLATE_OVERHEAD - _prompt_tokens,
    )
    _per_opinion = _opinions_budget // max(len(valid_opinions), 1)
    logging.debug(
        "[DELIBERATION] token budget | prompt=%d opinions_total=%d per_opinion=%d",
        _prompt_tokens, _opinions_budget, _per_opinion,
    )
    formatted = _format_opinions(valid_opinions, per_opinion_tokens=_per_opinion)
    synthesis_prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
        task_type=task_type,
        original_prompt=prompt,
        opinions=formatted,
    )
    # ── 6. Echo synthesises ───────────────────────────────────
    logging.info(
        f"[DELIBERATION] Sending {len(valid_opinions)} opinions to {synth_model} for synthesis"
    )
    final_response = _ollama_query(synth_model, synthesis_prompt, timeout=SYNTHESIS_TIMEOUT)

    if not final_response or "[ERROR]" in final_response:
        logging.warning("[DELIBERATION] Synthesis failed — returning best single council response")
        best = max(valid_opinions.values(), key=len)
        river_brain.learn(synth_model, task_type, best)
        return best

    # ── 7. Post-synthesis learning ────────────────────────────
    # Each councillor learns from its OWN response — not the synthesis.
    # Crediting all models with the synthesized output inflated every
    # councillor's River score regardless of actual contribution quality.
    # Only the synthesis model (Echo) learns from the final synthesis.
    logging.info(
        f"[DELIBERATION] Synthesis complete | "
        f"council_size={len(valid_opinions)} | "
        f"synth_model={synth_model} | "
        f"response_len={len(final_response)}"
    )
    for model, opinion in valid_opinions.items():
        if model != synth_model:
            river_brain.learn(model, task_type, opinion)
    river_brain.learn(synth_model, task_type, final_response)

    return final_response
