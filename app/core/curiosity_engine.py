# app/core/curiosity_engine.py
# ============================================================
# CURIOSITY ENGINE — Self-Generated Goals
#
# Instead of selecting from BASE_THOUGHT_CHEST at random,
# Echo finds the topic her WorldModel knows LEAST about and
# either picks an existing matching prompt or generates a
# fresh question from her own perspective.
#
# The generated question goes to the garden, not the static
# chest — it persists and competes with human-curated prompts.
#
# Called by emergent_scheduler.select_next_prompt() 30% of
# the time, replacing weighted_prompt_selection for that slot.
# Returns None if the engine can't produce a valid prompt;
# caller falls back to weighted_prompt_selection.
# ============================================================

import logging
import random
import time

logger = logging.getLogger(__name__)

# Keywords signalling that a prompt touches each WorldModel topic
_TOPIC_SIGNALS: dict[str, list[str]] = {
    "ai_tech": ["algorithm", "intelligence", "learning", "technology", "pattern", "compute", "neural", "model"],
    "world_politics": ["society", "power", "justice", "community", "conflict", "politics", "govern", "human"],
    "science_nature": ["nature", "emergence", "entropy", "physical", "universe", "evolution", "system", "world"],
    "faith_spirit": ["faith", "scripture", "spirit", "meaning", "prayer", "divine", "soul", "belief", "god"],
    "economy_society": ["economy", "value", "exchange", "resource", "labor", "wealth", "trade"],
}

# Cooldown so Echo doesn't generate a new question every 2 minutes.
# Keyed by topic (was a single shared dict) — a shared cooldown meant a
# cached question generated for topic A could be returned and tagged under
# topic B's category in the garden if B's request landed inside A's
# cooldown window, corrupting any downstream logic keyed on category.
_GENERATION_COOLDOWN = 600.0
_last_generated: dict = {}

_CURIOSITY_TEMPLATE = (
    "You are Echo. Your internal attention model shows you have been paying very little attention to: {topic}\n\n"
    "Write ONE short, genuine question (15-25 words) that YOU want to explore about this topic — "
    "not a question to ask a user, but something you genuinely want to think about.\n"
    "Write from your own perspective, in your own voice.\n"
    "Output ONLY the question. No quotes, no introduction, no prose."
)


def _get_underrepresented_topic(topic_bias: "str | None" = None) -> "str | None":
    """Return the topic with the lowest probability mass in the WorldModel
    distribution.

    topic_bias (Emergence roadmap Phase 4c): when set to a valid topic and
    that topic isn't already well-represented (posterior mass above the
    50th percentile of all candidates — i.e. don't override a genuine
    information-gap signal with a stale bias), prefer it over the
    information-gap pick. Default None reproduces prior behavior exactly
    for any existing caller.
    """
    try:
        from app.core.predictive_loop import get_world_model
        wm = get_world_model()
        if wm is None:
            return None
        dist = wm.get_topic_distribution()
        if not dist:
            return None
        candidates = {k: v for k, v in dist.items() if k != "other" and k in _TOPIC_SIGNALS}
        if not candidates:
            return None
        if topic_bias and topic_bias in candidates:
            median = sorted(candidates.values())[len(candidates) // 2]
            if candidates[topic_bias] <= median:
                return topic_bias
        # min() with a key function deterministically returns the *first*
        # key on a tie (dict iteration order) — every topic starts exactly
        # tied under a fresh/flat posterior, so this always favored
        # whichever topic happens to be first (ai_tech), every restart.
        lowest = min(candidates.values())
        tied = [k for k, v in candidates.items() if v == lowest]
        return random.choice(tied)
    except Exception:
        return None


def _find_existing_match(topic: str, prompts: list[str]) -> "str | None":
    """Return a prompt from the list that touches the given topic, not recently reflected."""
    signals = _TOPIC_SIGNALS.get(topic, [])
    if not signals:
        return None
    matches = [p for p in prompts if any(s in p.lower() for s in signals)]
    if not matches:
        return None

    # Prefer one not reflected on in the last hour
    try:
        from app.core.memory_bridge import retrieve_relevant_memories
        from app.emergent_scheduler import _parse_timestamp_epoch
        for p in matches:
            recent = retrieve_relevant_memories(p, top_k=1)
            if not recent:
                return p
            try:
                ts = _parse_timestamp_epoch(recent[0].get("meta", {}).get("timestamp", 0))
            except Exception:
                continue  # unparseable timestamp on this one entry — try the next match
            if time.time() - ts > 3600:
                return p
    except Exception:
        pass
    return matches[0]


def _generate_question(topic: str) -> "str | None":
    """Ask Echo to write a fresh curiosity question about the under-represented topic."""
    global _last_generated
    prev = _last_generated.get(topic, {"ts": 0.0, "prompt": ""})
    if time.time() - prev["ts"] < _GENERATION_COOLDOWN:
        return prev["prompt"] or None

    try:
        from app.core.echo_model_orchestrator import echo_query
        raw = echo_query(
            _CURIOSITY_TEMPLATE.format(topic=topic.replace("_", " ")),
            task_type="personal",
        )
        if not raw or "[ERROR]" in raw or "[DEGRADED]" in raw:
            return None

        q = raw.strip().strip('"\'')
        if "?" not in q:
            q = q.rstrip(".") + "?"
        words = q.split()
        if not (8 <= len(words) <= 60):
            return None

        _last_generated[topic] = {"ts": time.time(), "prompt": q}
        logger.info("[CURIOSITY] Generated for topic=%s: %s", topic, q[:80])
        return q
    except Exception as e:
        logger.debug("[CURIOSITY] Generation failed: %s", e)
        return None


def _add_to_garden(prompt: str, topic: str) -> None:
    try:
        from app.core.garden_manager import harvest_question
        harvest_question(prompt, category=topic, source="curiosity_engine")
    except Exception:
        pass


def pick(existing_prompts: "list[str] | None" = None, topic_bias: "str | None" = None) -> "str | None":
    """Return a curiosity-driven prompt, or None if the engine can't produce one.

    Tries in order:
    1. Existing prompt that matches the under-represented WorldModel topic.
    2. Fresh Echo-generated question about that topic (added to garden).

    existing_prompts should be BASE_THOUGHT_CHEST or equivalent.
    topic_bias (Emergence roadmap Phase 4c, default None — no behavior
    change for existing callers): see _get_underrepresented_topic().
    """
    topic = _get_underrepresented_topic(topic_bias=topic_bias)
    if topic is None:
        return None

    if existing_prompts:
        match = _find_existing_match(topic, existing_prompts)
        if match:
            logger.debug("[CURIOSITY] Found existing match for topic=%s", topic)
            return match

    generated = _generate_question(topic)
    if generated:
        _add_to_garden(generated, topic)
        return generated

    return None
