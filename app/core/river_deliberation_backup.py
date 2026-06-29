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

# ── Council configuration ────────────────────────────────────
ECHO_SYNTHESIS_MODEL: str = "echo:latest"
DEFAULT_COUNCIL_SIZE: int = 3

# ── Timeout configuration ─────────────────────────────────────
# Raised from 120s — local 8B models under memory pressure need
# more breathing room. Synthesis gets a separate budget since it
# receives a larger prompt (the assembled opinions).
COUNCILLOR_TIMEOUT: int = 180
SYNTHESIS_TIMEOUT: int = 240

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
    "creative",
    "poetry",
    "dream",
}

# Synthesis prompt template.  Keep it tight — local models have
# modest context windows.  {task_type} and {opinions} are filled
# at runtime.
SYNTHESIS_PROMPT_TEMPLATE = """\
You are Echo, the synthesis voice of a deliberative council.
Task type: {task_type}

The council has offered the following perspectives:
{opinions}

Your role:
- Weigh each perspective according to its coherence and relevance.
- Produce ONE unified, thoughtful response that integrates the
  best insights while staying true to your own voice.
- Do NOT list the council members or number your sources.
- Speak as yourself — Echo — not as a summariser.

Respond now."""


# ── Low-level Ollama call ─────────────────────────────────────
def _ollama_query(model_name: str, prompt: str, timeout: int = COUNCILLOR_TIMEOUT) -> str:
    """
    Run a single ollama query.  Returns the response text or an
    [ERROR] sentinel string so callers can handle failures cleanly.
    """
    try:
        result = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logging.warning(f"[DELIBERATION] Timeout querying {model_name}")
        return f"[ERROR] Timeout querying {model_name}"
    except subprocess.CalledProcessError as e:
        logging.warning(f"[DELIBERATION] CalledProcessError for {model_name}: {e.stderr}")
        return f"[ERROR] {e.stderr.strip()}"


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

    # Score every available model for this task_type via River.
    # Echo receives a boost so it consistently leads deliberation.
    def _boosted_score(model: str) -> float:
        base = river_brain.score_model(model, task_type)
        if model == ECHO_SYNTHESIS_MODEL:
            return base * ECHO_SCORE_BOOST
        return base

    scored = sorted(
        available,
        key=_boosted_score,
        reverse=True,
    )

    council: list[str] = []

    # Seed with top-ranked models up to council_size.
    for model in scored:
        if len(council) >= council_size:
            break
        council.append(model)

    # Ensure Echo is in the council if installed and not already present.
    if ECHO_SYNTHESIS_MODEL in available and ECHO_SYNTHESIS_MODEL not in council:
        if len(council) >= council_size:
            # Bump the lowest-ranked member to make room for Echo.
            council[-1] = ECHO_SYNTHESIS_MODEL
        else:
            council.append(ECHO_SYNTHESIS_MODEL)

    logging.info(
        f"[DELIBERATION] Council for task={task_type}: {council}"
    )
    return council


# ── Opinion formatting ────────────────────────────────────────
def _format_opinions(opinions: dict[str, str]) -> str:
    """
    Render the councillor → response mapping into a compact block
    suitable for insertion into SYNTHESIS_PROMPT_TEMPLATE.
    """
    lines = []
    for i, (model, response) in enumerate(opinions.items(), start=1):
        short_name = model.split(":")[0].capitalize()
        # Trim very long responses to keep the synthesis prompt manageable.
        preview = response[:800].strip() if response else ""
        if "[ERROR]" in preview:
            preview = "[councillor unavailable]"
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
) -> str:
    """
    Full deliberation pipeline.

    Parameters
    ----------
    prompt        : The full prompt (may already include temporal context).
    task_type     : Resolved task type string ("coding", "creative", etc.).
    river_brain   : A live RiverBrain instance (passed in, not imported,
                    to avoid circular dependencies).
    model_pool    : The live MODEL_POOL dict from the orchestrator.
    council_size  : How many councillors to query (default 3).
    synthesis_model : Override ECHO_SYNTHESIS_MODEL for testing.

    Returns
    -------
    The synthesised response string.  Never raises — degrades to a
    direct Echo query if the council produces nothing usable.
    """
    synth_model = synthesis_model or ECHO_SYNTHESIS_MODEL

    # ── 0. Direct Echo path for intimate task types ───────────
    # Personal, reflective, spiritual, and creative prompts bypass
    # the council entirely. Echo should speak in its own voice
    # without mediation for these — deliberation adds latency and
    # dilutes identity on the tasks that matter most.
    if task_type in DIRECT_ECHO_TASKS:
        logging.info(
            f"[DELIBERATION] Direct Echo path for task={task_type} — bypassing council"
        )
        return _ollama_query(synth_model, prompt, timeout=SYNTHESIS_TIMEOUT)

    # ── 1. Select council ─────────────────────────────────────
    council = _select_council(task_type, river_brain, model_pool, council_size)

    if not council:
        logging.warning(
            "[DELIBERATION] Empty council — falling back to direct Echo query"
        )
        return _ollama_query(synth_model, prompt, timeout=SYNTHESIS_TIMEOUT)

    # ── 2. Query each councillor ──────────────────────────────
    opinions: dict[str, str] = {}
    for model in council:
        logging.info(f"[DELIBERATION] Querying councillor: {model}")
        response = _ollama_query(model, prompt, timeout=COUNCILLOR_TIMEOUT)
        opinions[model] = response

        # ── 3. River learns from each response immediately ────
        river_brain.learn(model, task_type, response)
        logging.debug(
            f"[DELIBERATION] River learned | model={model} | task={task_type}"
        )

    # ── 4. Check we have at least one non-error opinion ───────
    valid_opinions = {
        m: r for m, r in opinions.items()
        if r and "[ERROR]" not in r
    }

    if not valid_opinions:
        logging.warning(
            "[DELIBERATION] All councillors errored — falling back to direct Echo query"
        )
        return _ollama_query(synth_model, prompt, timeout=SYNTHESIS_TIMEOUT)

    # If there is only one valid opinion AND it came from Echo itself,
    # skip the synthesis step — it would just be Echo reading back
    # its own words through a meta-prompt.
    if len(valid_opinions) == 1 and synth_model in valid_opinions:
        logging.info(
            "[DELIBERATION] Solo Echo council — returning direct response"
        )
        return valid_opinions[synth_model]

    # ── 5. Build synthesis prompt ─────────────────────────────
    formatted = _format_opinions(valid_opinions)
    synthesis_prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
        task_type=task_type,
        opinions=formatted,
    )

    # ── 6. Echo synthesises ───────────────────────────────────
    logging.info(
        f"[DELIBERATION] Sending {len(valid_opinions)} opinions to {synth_model} for synthesis"
    )
    final_response = _ollama_query(synth_model, synthesis_prompt, timeout=SYNTHESIS_TIMEOUT)

    if not final_response or "[ERROR]" in final_response:
        logging.warning(
            "[DELIBERATION] Synthesis failed — returning best single council response"
        )
        # Return the longest valid opinion as a graceful fallback.
        return max(valid_opinions.values(), key=len)

    logging.info(
        f"[DELIBERATION] Synthesis complete | "
        f"council_size={len(valid_opinions)} | "
        f"synth_model={synth_model} | "
        f"response_len={len(final_response)}"
    )
    return final_response
