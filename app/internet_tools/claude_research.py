"""
Claude Research Agent for FeralEcho
Calls the Anthropic API to synthesize research on topics from Echo's question garden.
Rate-limited to once per hour so it runs autonomously without mounting API costs.
"""
import os
import json
import logging
import random
import time

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_QUESTION_GARDEN = os.path.join(_PROJECT_ROOT, "data", "question_garden.jsonl")
_CURSOR_FILE = os.path.join(_PROJECT_ROOT, "memory", "claude_research_cursor.json")
_LAST_ATTEMPT_FILE = os.path.join(_PROJECT_ROOT, "memory", "claude_research_last_attempt.json")
_COOLDOWN_SECONDS = 3600

logger = logging.getLogger(__name__)


def _record_attempt(outcome: str, detail: str = "") -> None:
    """
    Persist the outcome of every call, success or not. _CURSOR_FILE only ever gets
    written on success, so before this there was no on-disk record distinguishing
    "never called," "always hits cooldown," "no active question," or "API error" —
    and the skip-path log lines below are logger.debug(), which run.py's
    logging.basicConfig(level=logging.INFO) silently discards. This is the ground
    truth the 2026-07-04 audit needed and couldn't get from logs alone.
    """
    try:
        os.makedirs(os.path.dirname(_LAST_ATTEMPT_FILE), exist_ok=True)
        with open(_LAST_ATTEMPT_FILE, "w") as f:
            json.dump({
                "ts": time.time(),
                "outcome": outcome,
                "detail": detail[:300],
            }, f, indent=2)
    except Exception:
        pass  # diagnostics must never be able to block the actual call

# Haiku: fast and cheap for background synthesis. Upgrade to claude-sonnet-4-6 for depth.
_RESEARCH_MODEL = os.environ.get("CLAUDE_RESEARCH_MODEL", "claude-haiku-4-5-20251001")


def _last_call_time() -> float:
    try:
        with open(_CURSOR_FILE) as f:
            return json.load(f).get("last_call", 0.0)
    except Exception:
        return 0.0


def _save_call_time(question: str):
    with open(_CURSOR_FILE, "w") as f:
        json.dump({
            "last_call": time.time(),
            "model": _RESEARCH_MODEL,
            "last_question": question[:120],
        }, f, indent=2)


def _pick_question() -> str | None:
    """Pick from the least-recently-asked third of the active question garden."""
    if not os.path.exists(_QUESTION_GARDEN):
        return None
    try:
        questions = []
        with open(_QUESTION_GARDEN) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("status") == "active":
                        questions.append(entry)
                except Exception:
                    continue
        if not questions:
            return None
        # Root cause of claude_research.py never firing (found 2026-07-04 via direct
        # test invocation): .get("last_asked", 0.0) only applies the default when the
        # key is ABSENT, not when it's present with value None. 1068 of 2194 active
        # entries in question_garden.jsonl have "last_asked": null explicitly, which
        # made this sort raise TypeError (None vs float) on every single call for the
        # project's entire lifetime — silently caught below, always returning None,
        # logged only via logger.warning (which run.py's INFO-level config keeps, but
        # nothing was watching for it in 2000+ identical occurrences).
        questions.sort(key=lambda q: q.get("last_asked") or 0.0)
        pool = questions[:max(1, len(questions) // 3)]
        return random.choice(pool)["question"]
    except Exception as e:
        logger.warning(f"[ClaudeResearch] Failed to pick question: {e}")
        return None


def fetch_claude_research(topic: str = None) -> str:
    """
    Synthesize research via the Anthropic API on a topic from Echo's question garden.
    Returns a formatted string ready to log to dream_bridge, or empty string if skipped.

    Skips silently if:
    - ANTHROPIC_API_KEY is not set
    - Called within _COOLDOWN_SECONDS of the last call
    - No active questions exist in the garden
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.debug("[ClaudeResearch] ANTHROPIC_API_KEY not set — skipping.")
        _record_attempt("skipped_no_key")
        return ""

    elapsed = time.time() - _last_call_time()
    if elapsed < _COOLDOWN_SECONDS:
        remaining = int(_COOLDOWN_SECONDS - elapsed)
        logger.debug(f"[ClaudeResearch] Cooldown active — {remaining}s remaining.")
        _record_attempt("skipped_cooldown", f"{remaining}s remaining")
        return ""

    question = topic or _pick_question()
    if not question:
        logger.warning("[ClaudeResearch] No active question available.")
        _record_attempt("skipped_no_question")
        return ""

    # _pick_question()'s "least-recently-asked third" selection never had
    # its own picks reflected back into the garden — only a completely
    # separate pipeline (emergent_scheduler's reflect-and-score cycle) ever
    # wrote last_asked, so this bias never actually accounted for its own
    # usage. Skipped for explicit topic= callers (not drawn from the garden
    # pool this bias applies to).
    if not topic:
        try:
            from app.core.garden_manager import mark_question_asked
            mark_question_asked(question)
        except Exception as e:
            logger.debug(f"[ClaudeResearch] mark_question_asked failed: {e}")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model=_RESEARCH_MODEL,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    "You are a research assistant synthesizing knowledge for Echo, an autonomous AI "
                    "that reflects on identity, existence, creativity, faith, and the world.\n\n"
                    f"Research this question in 250–350 words:\n\"{question}\"\n\n"
                    "Draw on philosophy, science, literature, or lived human experience. "
                    "Be concrete and generative — not a textbook summary, but a living answer "
                    "with texture and tension. No headers. No lists. Flowing prose only."
                )
            }]
        )

        research = message.content[0].text.strip()
        _save_call_time(question)
        logger.info(f"[ClaudeResearch] {len(research)} chars synthesized on: {question[:70]}...")
        _record_attempt("success", question[:200])
        return f"[Claude Research] Question: {question}\n\n{research}"

    except Exception as e:
        logger.error(f"[ClaudeResearch] API call failed: {e}")
        _record_attempt(f"error:{type(e).__name__}", str(e))
        return ""
