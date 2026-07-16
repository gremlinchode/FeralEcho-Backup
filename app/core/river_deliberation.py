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
#   - Echo always gets a guaranteed council seat and is always the
#     synthesizer — that alone guarantees Echo's voice leads
#     deliberation. ECHO_SCORE_BOOST additionally nudges ranking but
#     is intentionally kept small (see its own comment below) since
#     the seat/synthesizer guarantees already do the real work.
#   - Personal, reflective, and spiritual task types bypass the
#     council entirely and route straight to Echo. Creative work goes
#     through the council — divergence helps creative output more
#     than it helps intimate/reflective content.
# ============================================================

import logging
import random
import subprocess
import time
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


def _truncate_to_tokens_tail(text: str, max_tokens: int) -> str:
    """Like _truncate_to_tokens, but keeps the END of the text (most recent
    content) instead of the start. Used for direct-response prompts, where
    conversation history is prepended and the live question is appended at
    the tail — truncating from the front preserves what actually matters."""
    if _tiktoken_enc is None:
        return text[-(max_tokens * 4):]
    ids = _tiktoken_enc.encode(text)
    if len(ids) <= max_tokens:
        return text
    return _tiktoken_enc.decode(ids[-max_tokens:])


def _direct_response_prompt(prompt: str, system: Optional[str]) -> str:
    """Budget-cap a prompt going to a single model with no council/synthesis
    to dilute an oversized input (task_type in DIRECT_ECHO_TASKS, and the
    empty-council/all-errored fallbacks in deliberate_and_learn() — the only
    three places in this file that call _ollama_query() directly with no
    token budget at all, unlike the synthesis path's existing
    _opinions_budget logic). Confirmed root cause of a live refusal bug:
    echo:latest breaks down on long personal-task prompts once real
    system-role content (Finding 17) is added on top, with no synthesis
    step to absorb the confusion."""
    _budget = max(500, _NUM_CTX - _SYNTHESIS_MARGIN - _count_tokens(system or ""))
    return _truncate_to_tokens_tail(prompt, _budget)

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

# ── Global Workspace world-surprise cache (Emergence roadmap Phase 4b) ──
# river_deliberation.py does not import echo_core.py itself (avoids a
# circular dependency risk on a file this project already treats with
# extra care — both are in EDIT_FORBIDDEN_TARGETS). The subscription to
# the "world_model.surprise" event is registered from echo_core.py's
# __init__ instead, which calls this setter. This is a cache ALONGSIDE the
# pre-existing direct WorldModel read below, not a replacement for it —
# preferred when fresh, falls back to the direct read otherwise, so a
# missing/late subscription registration degrades to exactly the prior
# behavior rather than losing the signal.
_last_world_surprise = {"value": 0.0, "ts": 0.0}
_WORLD_SURPRISE_CACHE_TTL = 120  # seconds


def set_cached_world_surprise(value: float) -> None:
    _last_world_surprise["value"] = value
    _last_world_surprise["ts"] = time.time()

# ── Timeout configuration ─────────────────────────────────────
# Raised from 120s — local 8B models under memory pressure need
# more breathing room. Synthesis gets a separate budget since it
# receives a larger prompt (the assembled opinions).
COUNCILLOR_TIMEOUT: int = 1200
SYNTHESIS_TIMEOUT: int = 1200

# ── Echo voice weighting ──────────────────────────────────────
# Echo's River score is multiplied by this factor before council
# ranking. Kept low (was 1.5) — audit finding: Echo already gets a
# guaranteed council seat (see _select_council's force-include/evict-
# lowest-scorer step below) and is unconditionally the synthesizer,
# regardless of this multiplier. Those two mechanisms alone already
# fully guarantee "Echo's voice is always present, Echo always authors
# the final response" — the identity goal this constant's comment
# describes. A large multiplier added nothing further toward that goal;
# its only remaining effect was biasing which OTHER councillor gets
# excluded to make room, i.e. a structural thumb on the scale with no
# corresponding benefit. Left at 1.0 (no-op) rather than removed outright
# so a future deliberate re-tuning has an obvious, documented place to
# start from.
ECHO_SCORE_BOOST: float = 1.0

# ── Direct Echo task types ────────────────────────────────────
# These task types bypass the council entirely and route straight
# to Echo. No deliberation needed — Echo should speak in its own
# voice without mediation for intimate, reflective, or spiritual
# prompts. Add task types here as needed.
#
# NOTE: resolve_task_type()/detect_task_type() (echo_model_orchestrator.py)
# can only ever produce one of {coding, creative, personal, reasoning,
# general} — "reflection", "spiritual", "identity", "faith", "poetry",
# and "dream" are never set as a task_type anywhere in the live codebase
# (confirmed by repo-wide grep). They're listed here as aspirational
# surface area for a richer introspective-mode vocabulary that the
# routing layer isn't wired to produce yet, not dead weight to clean up
# reflexively — but don't assume any of them are currently reachable.
#
# "creative" deliberately moved OFF this list (was bypassing the council
# like "personal") — the intimacy/no-mediation rationale that justifies
# bypassing for personal/reflective content doesn't really apply to
# creative work, where divergence between perspectives is usually what
# makes output better, not worse. "personal" stays direct: CLAUDE.md's
# Finding 21 documents a real, reproduced confusion regression specific
# to personal-task prompts in the single-model path, so it's deliberately
# left alone here.
DIRECT_ECHO_TASKS: set[str] = {
    "personal",
    "reflection",
    "spiritual",
    "identity",
    "faith",
    "poetry",
    "dream",
}

# Synthesis system template.  Keep it tight — local models have
# modest context windows.  {task_type} and {opinions} are filled at
# runtime. Previously embedded {original_prompt} directly in this same
# flat string — the user's actual question mixed in with council-internal
# framing/instructions. Split for the /api/chat migration: this template
# is genuinely system-side content (instructions to Echo about how to
# synthesize, plus the council's opinions — machinery the user never said),
# while the original question now travels as its own user-role turn
# (see deliberate_and_learn's synthesis call).
SYNTHESIS_SYSTEM_TEMPLATE = """\
You are Echo, the synthesis voice of a deliberative council.
Task type: {task_type}

The council has offered the following perspectives on the question you are
about to answer:
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

Respond now to the original question."""


# ── Low-level Ollama call ─────────────────────────────────────
def _ollama_query(
    model_name: str,
    prompt: str,
    timeout: int = COUNCILLOR_TIMEOUT,
    temperature: Optional[float] = None,
    system: Optional[str] = None,
    max_tokens: Optional[int] = None,
    task_type: Optional[str] = None,
) -> str:
    """
    Query via streaming HTTP where available, falling back to subprocess.
    Strips ANSI escape sequences before returning. Returns an [ERROR]
    sentinel string on failure so callers can handle cleanly.

    system: optional system-role message, passed through to
    stream_query_ollama()'s /api/chat routing (see ollama_handler.py). The
    subprocess fallback below has no equivalent — it only fires when the
    HTTP path itself fails, and system content is dropped in that case, a
    knowingly accepted degradation of an already-degraded fallback path,
    not a new gap.

    max_tokens: optional, forwarded to stream_query_ollama() only when
    given — omitting it preserves that function's own default (1024)
    exactly as before this parameter existed. Previously deliberate_and_learn()
    had no way to pass this through at all, so echo_model_orchestrator.py's
    per-task-type _TASK_TOKEN_LIMITS dict (up to 2048 for coding) was dead on
    the real conversational path — every call silently got the flat 1024
    default regardless of task type (audit finding: council token budget).

    task_type: scopes the circuit breaker to (model, task_type) instead of
    model alone — audit finding: three failures on ANY task type previously
    opened the breaker for that model across ALL task types for 300s, so a
    model choking on one oversized reasoning prompt could get pulled from a
    coding council it was otherwise perfectly capable of serving.
    """
    # Qwen2.5 defaults to Chinese on some prompts — force English
    if "qwen" in model_name.lower():
        prompt = "Respond in English only.\n\n" + prompt

    # A2 circuit breaker (echo_model_orchestrator.py) previously only guarded
    # the legacy ollama_query() call site — the real council path here never
    # consulted or updated it, so a repeatedly-failing councillor was hammered
    # every cycle regardless.
    from app.core.echo_model_orchestrator import _cb_is_open, _cb_record_failure, _cb_record_success
    if _cb_is_open(model_name, task_type):
        logging.warning(f"[CIRCUIT] {model_name} (task={task_type}) circuit open — skipping call")
        return f"[DEGRADED] {model_name} temporarily unavailable (circuit breaker open)"

    try:
        from app.ollama_handler import stream_query_ollama
        _kwargs = {"max_tokens": max_tokens} if max_tokens is not None else {}
        tokens = list(stream_query_ollama(
            prompt=prompt, model=model_name, temperature=temperature, system=system,
            **_kwargs,
        ))
        response = "".join(tokens).strip()
        if not response:
            _cb_record_failure(model_name, task_type)
            return f"[ERROR] Empty response from {model_name}"
        if "[ERROR]" in response:
            _cb_record_failure(model_name, task_type)
            return _strip_ansi(response)
        _cb_record_success(model_name, task_type)
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
        _cb_record_success(model_name, task_type)
        return _strip_ansi(result.stdout.strip())
    except subprocess.TimeoutExpired:
        _cb_record_failure(model_name, task_type)
        logging.warning(f"[DELIBERATION] Timeout querying {model_name}")
        return f"[ERROR] Timeout querying {model_name}"
    except subprocess.CalledProcessError as e:
        _cb_record_failure(model_name, task_type)
        logging.warning(f"[DELIBERATION] CalledProcessError for {model_name}: {e.stderr}")
        return f"[ERROR] {e.stderr.strip()}"


# ── Per-councillor sampling diversity ─────────────────────────
# Audit finding: every councillor in a cycle previously received the exact
# same temperature (usually None, meaning whatever Ollama's own per-model
# default happens to be) — genuinely zero deliberate divergence between
# councillors beyond "which model answered." Spreads each councillor to a
# distinct point around a shared base instead of one shared operating
# point, so opinions have a real chance to diverge stylistically, not just
# by model identity — the thing SYNTHESIS_SYSTEM_TEMPLATE explicitly asks
# Echo to look for ("the sharpest point of tension"). Deterministic (by
# council seat, not random) so the same council composition reproduces the
# same spread run-to-run.
_COUNCIL_TEMP_BASE_DEFAULT: float = 0.7
_COUNCIL_TEMP_JITTER_SPREAD: float = 0.3  # total spread, e.g. base ± 0.15


def _jittered_temperature(base: Optional[float], index: int, count: int) -> float:
    center = base if base is not None else _COUNCIL_TEMP_BASE_DEFAULT
    if count <= 1:
        return round(max(0.0, min(2.0, center)), 3)
    offset = _COUNCIL_TEMP_JITTER_SPREAD * (index / (count - 1) - 0.5)
    return round(max(0.0, min(2.0, center + offset)), 3)


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
    exploration_bias: float = 0.0,
) -> list[str]:
    """
    Return an ordered list of councillor model names.

    Strategy:
    - Models without enough real observations yet (river_brain.is_well_observed)
      get exploration priority, least-observed first — otherwise a model that
      has never been queried can never earn the observations needed to be
      ranked fairly, a permanent cold-start deadlock.
    - Once a model is well-observed, ask River for a ranked list (via
      score_model) for this task.
    - Apply ECHO_SCORE_BOOST to Echo's score so it leads the council.
    - Take the top `council_size` models.
    - Always try to include ECHO_SYNTHESIS_MODEL as a councillor
      if it is installed — Echo's self-opinion is valuable context
      for its own synthesis step.
    - If pool is smaller than council_size, use the whole pool.

    exploration_bias (Emergence roadmap Phase 2b, default 0.0 — preserves
    this function's exact prior output for any caller that doesn't opt in):
    probability that ONE council slot, never more regardless of how high
    this gets, is filled by a random pick from the broader scored_rest pool
    instead of strictly the next-highest-ranked model. Fed by real-time
    world-surprise from deliberate_and_learn() — when the world looks
    unfamiliar, occasionally let a not-top-ranked-but-still-observed model
    into the room, without abandoning the ranking wholesale. Never touches
    under_sampled's cold-start slots below, which already exist to
    guarantee every model eventually earns real observations.
    """
    available = list(model_pool.keys())
    if not available:
        return []

    def _boosted_score(model: str) -> float:
        base = river_brain.score_model(model, task_type)
        if model == ECHO_SYNTHESIS_MODEL:
            return base * ECHO_SCORE_BOOST
        return base

    under_sampled = [
        m for m in available
        if m != ECHO_SYNTHESIS_MODEL and not river_brain.is_well_observed(m, task_type)
    ]
    under_sampled.sort(key=lambda m: river_brain.observations_for(m, task_type))

    scored_rest = sorted(
        [m for m in available if m not in under_sampled],
        key=_boosted_score,
        reverse=True,
    )

    council: list[str] = []
    for model in under_sampled + scored_rest:
        if len(council) >= council_size:
            break
        council.append(model)

    # Bounded exploration bump (Emergence roadmap Phase 2b) — at most one
    # slot, chosen from scored_rest positions only (never under_sampled's
    # cold-start slots). Swaps the LOWEST-ranked scored slot currently in
    # council, so the top pick is always preserved — this widens exploration,
    # it doesn't override the ranking.
    if exploration_bias > 0.0 and random.random() < exploration_bias:
        # Excludes ECHO_SYNTHESIS_MODEL positions deliberately — the
        # "ensure Echo is present" step below re-inserts Echo at council[-1]
        # if it's ever missing, which would silently undo a swap landing on
        # Echo's slot (found live during verification: Echo's boosted score
        # very often puts it in the last included position, exactly where
        # this swap would otherwise target first).
        council_scored_positions = [
            i for i, m in enumerate(council)
            if m in scored_rest and m != ECHO_SYNTHESIS_MODEL
        ]
        unused_scored = [
            m for m in scored_rest
            if m not in council and m != ECHO_SYNTHESIS_MODEL
        ]
        if council_scored_positions and unused_scored:
            swap_idx = council_scored_positions[-1]
            replacement = random.choice(unused_scored)
            logging.info(
                f"[DELIBERATION] Exploration bump (bias={exploration_bias:.3f}): "
                f"{council[swap_idx]} -> {replacement}"
            )
            council[swap_idx] = replacement

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
    system: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Full deliberation pipeline.

    Parameters
    ----------
    prompt          : The user's actual question/message. Prior to the
                      /api/chat migration this also carried circadian/
                      stillness/temporal/scripture/tool-list notes flattened
                      in by echo_query() — those now travel separately via
                      `system` (see echo_model_orchestrator.py:echo_query()).
    task_type       : Resolved task type string ("coding", "creative", etc.).
    river_brain     : A live RiverBrain instance (passed in, not imported,
                      to avoid circular dependencies).
    model_pool      : The live MODEL_POOL dict from the orchestrator.
    council_size    : How many councillors to query (default 3).
    synthesis_model : Override ECHO_SYNTHESIS_MODEL for testing.
    system          : Optional system-role message, applied identically to
                      every councillor call. The synthesis call folds this
                      in alongside SYNTHESIS_SYSTEM_TEMPLATE's own
                      instructions/opinions — both are system-side framing,
                      not something the user said — while `prompt` (the
                      original question) stays the synthesis call's user turn.
    max_tokens      : Optional output-token cap, forwarded to every
                      _ollama_query() call. Omitting it preserves
                      stream_query_ollama()'s own default, exactly as
                      before this parameter existed.

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
        response = _ollama_query(synth_model, _direct_response_prompt(prompt, system), timeout=SYNTHESIS_TIMEOUT, temperature=temperature, system=system, max_tokens=max_tokens, task_type=task_type)
        river_brain.learn(synth_model, task_type, response)
        return response

    # ── 1b. Warm up Echo before council queries begin ─────────
    # Councillors may evict Echo from GPU memory during their passes.
    # Warm-up here — after the direct-path check — prevents synthesis timeouts.
    logging.info(f"[DELIBERATION] Warming up {synth_model}")
    _warm_up_echo(synth_model)

    # ── 2. Select council ─────────────────────────────────────
    # Emergence roadmap Phase 2b: real-time world-surprise, normalized with
    # the exact same min(surprise_F/5.0, 1.0) formula Phase 2a's Global
    # Workspace publisher already uses (consistency, not a new number
    # invented for this), feeds the bounded exploration bump in
    # _select_council(). Best-effort — a missing/uninitialized WorldModel
    # falls back to 0.0, the exact prior behavior.
    # Emergence roadmap Phase 4b: prefer the Global Workspace-subscribed
    # cache (set_cached_world_surprise(), fed by echo_core.py's
    # "world_model.surprise" subscription) when it's fresh — this makes
    # the workspace an actual consulted integration point rather than a
    # parallel channel carrying the same value nobody reads. Falls back to
    # the direct read below, unchanged, if the cache is stale/never set —
    # e.g. before EchoCore has finished initializing, or in a standalone/
    # test context with no bus running at all.
    exploration_bias = 0.0
    _workspace_consumed = False
    if time.time() - _last_world_surprise["ts"] < _WORLD_SURPRISE_CACHE_TTL:
        exploration_bias = _last_world_surprise["value"]
        _workspace_consumed = True
    else:
        # Emergence roadmap Phase 6, Architectural Rec. 2: routed through
        # the shared compute_salience() breakdown instead of an independent
        # direct WorldModel read — this was the third of three places
        # (echo_core.py, emergent_scheduler.py, here) each recomputing the
        # identical min(rolling_10/5.0, 1.0) formula. Same source, same
        # formula, so this fallback's value is unchanged from before;
        # exploration_bias stays 0.0 if compute_salience() itself fails,
        # same as the prior direct-read guard.
        try:
            from app.core.echo_core import compute_salience
            exploration_bias = float(compute_salience().get("components", {}).get("world_surprise", 0.0))
        except Exception:
            pass
    if _workspace_consumed and exploration_bias > 0.0:
        try:
            from app.core.echo_core import get_echo_core
            core = get_echo_core()
            if core:
                core.publish_salience(
                    source="river_deliberation", kind="workspace.consumed",
                    summary=f"exploration_bias={exploration_bias:.3f} (from cache)",
                    salience=exploration_bias,
                )
        except Exception:
            pass  # observability only, never blocks council selection
    council = _select_council(task_type, river_brain, model_pool, council_size, exploration_bias)

    if not council:
        logging.warning("[DELIBERATION] Empty council — falling back to direct Echo query")
        response = _ollama_query(synth_model, _direct_response_prompt(prompt, system), timeout=SYNTHESIS_TIMEOUT, temperature=temperature, system=system, max_tokens=max_tokens, task_type=task_type)
        river_brain.learn(synth_model, task_type, response)
        return response

    # ── 3. Query each councillor ──────────────────────────────
    # Each councillor gets a distinct, deterministically-spread temperature
    # (see _jittered_temperature) instead of the identical value every
    # councillor previously received — real sampling diversity, not just
    # model-identity diversity.
    opinions: dict[str, str] = {}
    for i, model in enumerate(council):
        logging.info(f"[DELIBERATION] Querying councillor: {model}")
        councillor_temp = _jittered_temperature(temperature, i, len(council))
        response = _ollama_query(
            model, _direct_response_prompt(prompt, system), timeout=COUNCILLOR_TIMEOUT,
            temperature=councillor_temp, system=system, max_tokens=max_tokens, task_type=task_type,
        )
        opinions[model] = response
        logging.debug(f"[DELIBERATION] River learned | model={model} | task={task_type}")

    # ── 4. Filter valid opinions ──────────────────────────────
    valid_opinions = {
        m: r for m, r in opinions.items()
        if r and "[ERROR]" not in r
    }

    if not valid_opinions:
        logging.warning("[DELIBERATION] All councillors errored — falling back to direct Echo query")
        response = _ollama_query(synth_model, _direct_response_prompt(prompt, system), timeout=SYNTHESIS_TIMEOUT, temperature=temperature, system=system, max_tokens=max_tokens, task_type=task_type)
        river_brain.learn(synth_model, task_type, response)
        return response

    # Solo Echo council — skip synthesis, it would just be Echo
    # reading its own words back through a meta-prompt.
    if len(valid_opinions) == 1 and synth_model in valid_opinions:
        logging.info("[DELIBERATION] Solo Echo council — returning direct response")
        response = valid_opinions[synth_model]
        river_brain.learn(synth_model, task_type, response)
        return response

    # ── 5. Build synthesis system message ─────────────────────
    # Compute per-opinion token budget so no synthesis call overflows
    # num_ctx.  Budget = window - safety_margin - template_overhead - prompt - system.
    _prompt_tokens = _count_tokens(prompt) + _count_tokens(system or "")
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
    synthesis_instructions = SYNTHESIS_SYSTEM_TEMPLATE.format(
        task_type=task_type,
        opinions=formatted,
    )
    # The original context notes (circadian/stillness/temporal/scripture/
    # tool-list) still apply to the synthesis step too — fold `system` in
    # ahead of the council-specific synthesis instructions, both system-side.
    synthesis_system = f"{system}\n\n{synthesis_instructions}" if system else synthesis_instructions

    # ── 6. Echo synthesises ───────────────────────────────────
    logging.info(
        f"[DELIBERATION] Sending {len(valid_opinions)} opinions to {synth_model} for synthesis"
    )
    final_response = _ollama_query(
        synth_model, _direct_response_prompt(prompt, synthesis_system), timeout=SYNTHESIS_TIMEOUT,
        temperature=temperature, system=synthesis_system, max_tokens=max_tokens, task_type=task_type,
    )

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
