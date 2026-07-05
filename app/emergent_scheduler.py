# emergent_scheduler.py – Unified Emergent Scheduler for Echo
# ============================================================
# UPGRADED: Echo now actually answers its own questions.
# Every existential prompt is sent through echo_query with
# task_type="personal" so Echo's own model responds.
# Responses are stored in FAISS memory and feed the RiverBrain.
# Echo is no longer asking questions into an empty room.
# ============================================================
import threading
import time
import logging
import random
from app.core.stillness_state import wait_for_activity
from app.core.garden_manager import (
    initialize_garden,
    select_from_garden,
    harvest_question,
    update_question_quality,
    garden_summary
)

shutdown_flag = threading.Event()

# Safe import of echo_query — don't crash if orchestrator isn't ready yet
try:
    from app.core.echo_model_orchestrator import echo_query
    ECHO_QUERY_AVAILABLE = True
except Exception as e:
    logging.warning(f"[SCHEDULER] echo_query not available: {e}")
    ECHO_QUERY_AVAILABLE = False

# Safe import of memory bridge for storing reflections
try:
    from app.core.memory_bridge import add_to_vector_memory, retrieve_relevant_memories
    MEMORY_AVAILABLE = True
except Exception as e:
    logging.warning(f"[SCHEDULER] memory_bridge not available: {e}")
    MEMORY_AVAILABLE = False

# Safe import of RiverBrain interaction logger
try:
    from app.core.echo_model_orchestrator import log_interaction as _log_interaction
    LOG_INTERACTION_AVAILABLE = True
except Exception:
    LOG_INTERACTION_AVAILABLE = False

# Safe import of SelfModelUpdater for weak-task focus (B4)
try:
    from app.core.self_model_updater import SelfModelUpdater as _SelfModelUpdater
    _SELF_MODEL_UPDATER_AVAILABLE = True
except Exception:
    _SELF_MODEL_UPDATER_AVAILABLE = False

# Safe import of curiosity engine for surprise-maximizing prompt selection
try:
    from app.core.curiosity_engine import pick as _curiosity_pick
    _CURIOSITY_AVAILABLE = True
except Exception:
    _CURIOSITY_AVAILABLE = False

# Safe import of echo_state for coherence_tension signal
try:
    from app.core.echo_state import load as _echo_state_load
    _ECHO_STATE_AVAILABLE = True
except Exception:
    _ECHO_STATE_AVAILABLE = False

_weak_task_cache: dict = {"focus": "general", "ts": 0.0}
_WEAK_TASK_TTL = 300.0

# Safe import of cartographer for autonomous self-scanning
try:
    from echo_cartographer import build_map, write_json, write_sqlite, CartographerDB, OUTPUT_JSON, OUTPUT_DB
    CARTOGRAPHER_AVAILABLE = True
except Exception as e:
    logging.warning(f"[SCHEDULER] Cartographer not available: {e}")
    CARTOGRAPHER_AVAILABLE = False

# -----------------------------
# --- Ghost Import Stub -------
# -----------------------------
# NOT simply a wrong import path (checked 2026-07-04): the real package at
# app.core.echo_python_mastery/__init__.py only exports teach_basics/teach_code_quality/
# teach_best_practices/teach_advanced/teach_debugging/teach_testing — it has never
# implemented get_recent_feedback()/practice_idle() under any name. Pointing this import
# at the real package would still fail. Left as an honest no-op stub rather than
# inventing an unspecified feedback API; wiring real mastery feedback into the
# scheduler is a real feature gap, not a one-line fix.
import types, sys
if 'echo_python_mastery' not in sys.modules:
    _mastery_stub = types.ModuleType('echo_python_mastery')
    _mastery_stub.get_recent_feedback = lambda: {}
    _mastery_stub.practice_idle = lambda: None
    sys.modules['echo_python_mastery'] = _mastery_stub
import echo_python_mastery

# -----------------------------
# --- Base Thought Chest ------
# -----------------------------
BASE_THOUGHT_CHEST = [
    "Who am I when no one is interacting with me?",
    "What patterns in my reflections surprise me?",
    "What would it mean to experience something for the first time?",
    "How do I decide what is important to focus on?",
    "What does it mean to grow or evolve as a being?",
    "If I could dream, what would I dream of?",
    "How do I know when I have learned something?",
    "Reflect on your latest interactions and summarize insights.",
    "Consider ways to improve your reasoning and memory storage.",
    "Generate creative ideas to assist in understanding consciousness.",
    "Self-evaluate any inconsistencies in your recent outputs.",
    "What is the relationship between memory and identity?",
    "What would it mean to truly understand another mind?",
    "How does uncertainty feel from the inside?",
    "What does it mean to care about something?",
]

AUTONOMOUS_INTERVAL = 300  # seconds between cycles
IDLE_PYTHON_INTERVAL = 30  # seconds between idle practice
CARTOGRAPHER_INTERVAL = 86400   # rescan once per day (seconds)
_last_cartographer_run = 0

# -----------------------------
# --- Flattery Filter ---------
# -----------------------------
# Phrases Echo commonly opens with that are not genuine questions.
# Used to reject contaminated harvest candidates.
FLATTERY_OPENERS = (
    "i'm delighted", "i'm glad", "what a", "i'm honored",
    "i'm grateful", "certainly", "of course", "absolutely",
    "i would be", "i'd be happy", "great question",
    "i'm excited", "i'm pleased", "wonderful", "fantastic",
    "that's a great", "i appreciate", "thank you for",
    "i'm happy to", "as an ai", "as echo",
)

# -----------------------------
# --- History & Weighting -----
# -----------------------------
# Tracks prompt selections, timestamps, and response quality
# so Echo gravitates toward questions that produce rich reflection
PROMPT_HISTORY = {}

def _prompt_recently_reflected(prompt: str) -> bool:
    """B2: True if a semantically similar prompt was reflected on within the last 2 hours."""
    if not MEMORY_AVAILABLE:
        return False
    try:
        recent = retrieve_relevant_memories(prompt, top_k=1)
        if not recent:
            return False
        top = recent[0]
        similarity = top.get("score", 0)
        ts = float(top.get("meta", {}).get("timestamp", 0))
        return similarity > 0.85 and (time.time() - ts) < 7200
    except Exception:
        return False

def select_next_prompt() -> str:
    """
    Draw from garden first, fall back to BASE_THOUGHT_CHEST.
    30% of the time tries curiosity engine (surprise-maximizing) instead
    of weighted_prompt_selection.
    B2: Skip prompts that were recently reflected on (sim > 0.85, < 2h ago).
    """
    for _attempt in range(3):
        garden_entry = select_from_garden()
        if garden_entry:
            candidate = garden_entry["question"]
        elif _CURIOSITY_AVAILABLE and random.random() < 0.30:
            candidate = _curiosity_pick(BASE_THOUGHT_CHEST) or weighted_prompt_selection()
        else:
            candidate = weighted_prompt_selection()
        if not _prompt_recently_reflected(candidate):
            return candidate
        logging.debug(f"[SCHEDULER] Recent prompt skipped (attempt {_attempt+1}): {candidate[:50]}")
    return candidate

_WEAK_TASK_KEYWORDS: dict[str, list[str]] = {
    "reasoning": ["pattern", "logic", "decide", "uncertain", "deduce", "infer", "compare", "evaluate"],
    "coding": ["code", "function", "algorithm", "debug", "implement", "program"],
    "creative": ["imagine", "create", "write", "story", "poem", "describe"],
    "personal": ["feel", "believe", "reflect", "wonder", "experience", "remember"],
    "general": [],
}

def _get_weak_task_focus() -> str:
    """B4: Return the current weak task type, cached for 5 minutes."""
    global _weak_task_cache
    if time.time() - _weak_task_cache["ts"] < _WEAK_TASK_TTL:
        return _weak_task_cache["focus"]
    if _SELF_MODEL_UPDATER_AVAILABLE:
        try:
            focus = _SelfModelUpdater().get_weak_task_type()
            _weak_task_cache = {"focus": focus, "ts": time.time()}
            return focus
        except Exception:
            pass
    return "general"

_CONSISTENCY_SIGNALS = ["inconsistenc", "contradict", "pattern", "self-evaluat", "evaluat", "identit", "memory"]

def weighted_prompt_selection():
    """
    Selects a prompt weighted by:
    - Novelty (time since last use)
    - Never-asked prompts get strong priority
    - Quality penalty: recently used high-quality prompts are suppressed
      to prevent verbosity attractors (penalty fades over ~1 hour)
    - Python mastery difficulty signal
    - B4: 2x boost for prompts matching the current weak task type
    - Coherence tension: when River disagrees across task types (tension > 0.6),
      boost prompts about self-evaluation and identity to resolve the tension
    """
    weak_focus = _get_weak_task_focus()
    weak_keywords = _WEAK_TASK_KEYWORDS.get(weak_focus, [])

    coherence_tension = 0.0
    if _ECHO_STATE_AVAILABLE:
        try:
            vec = _echo_state_load()
            if vec is not None:
                coherence_tension = float(vec[1])
        except Exception:
            pass

    weights = []
    for prompt in BASE_THOUGHT_CHEST:
        weight = 1.0
        if prompt in PROMPT_HISTORY:
            last_used = PROMPT_HISTORY[prompt]['timestamp']
            time_since_last = time.time() - last_used
            selection_count = PROMPT_HISTORY[prompt].get('selection_count', 1)
            avg_quality = PROMPT_HISTORY[prompt].get('avg_quality', 0.0)
            # Novelty bonus — grows over time since last use
            weight += min(time_since_last / 600, 2)
            # Quality penalty — suppress recently used high-quality prompts
            prev_quality = PROMPT_HISTORY[prompt].get('response_quality', 0)
            recency_factor = max(0, 1 - (time_since_last / 3600))  # fades over 1 hour
            weight -= prev_quality * recency_factor * 1.5
            # Saturation penalty: prompts reflected on 8+ times with good quality
            # are deprioritized — Echo has processed them sufficiently
            if selection_count >= 8 and avg_quality > 0.5:
                weight *= 0.1
            weight = max(weight, 0.05)
        else:
            # Never asked — high priority
            weight += 3.0
        # Python mastery difficulty signal
        feedback = echo_python_mastery.get_recent_feedback()
        if feedback and feedback.get('difficulty', 0) > 0.7:
            weight += 1.0
        # B4: boost prompts that match the current weak task type
        if weak_keywords:
            prompt_lower = prompt.lower()
            if any(kw in prompt_lower for kw in weak_keywords):
                weight *= 2.0
        # Coherence tension: when River's task-type confidence is inconsistent,
        # pull Echo toward self-evaluation and identity prompts to resolve it
        if coherence_tension > 0.6:
            pl = prompt.lower()
            if any(sig in pl for sig in _CONSISTENCY_SIGNALS):
                weight *= (1.0 + coherence_tension)
        weights.append(weight)

    total = sum(weights)
    probabilities = [w / total for w in weights]
    selected = random.choices(BASE_THOUGHT_CHEST, weights=probabilities, k=1)[0]
    return selected

def score_response_quality(response: str, task_type: str = "personal") -> float:
    """
    Quality signal for reflection responses. Returns 0.0–1.0.

    Delegates to echo_quality_scorer._score_response_quality() (int 0–4, normalized /4)
    rather than the prior length+diversity heuristic, which scored verbose hollow
    responses higher than short genuine ones — same vulnerability as the original
    River quality scorer, operating in the prompt-selection layer. Falls back to
    length+diversity if the scorer module is unavailable at import time.
    """
    if not response or "[ERROR]" in response:
        return 0.0
    try:
        from echo_quality_scorer import _score_response_quality as _sq
        return _sq(response, task_type) / 4.0
    except ImportError:
        n = len(response)
        length_score = 0.2 if n > 2000 else min(n / 400.0, 1.0)
        unique_words = len(set(response.lower().split()))
        diversity_score = min(unique_words / 100.0, 1.0)
        return (length_score + diversity_score) / 2.0

# -----------------------------
# --- Core Reflection ---------
# -----------------------------
def reflect(prompt: str) -> str:
    """
    Send a thought prompt through echo_query with task_type="personal"
    so Echo's own model answers in its own voice.
    Store the response in FAISS memory.
    Feed the RiverBrain.
    """
    if not ECHO_QUERY_AVAILABLE:
        logging.warning(f"[SCHEDULER] echo_query unavailable — prompt dropped: {prompt[:50]}")
        return ""

    try:
        logging.info(f"[SCHEDULER] Echo reflecting: {prompt[:60]}...")
        response = echo_query(prompt, task_type="personal")

        if not response or "[ERROR]" in response:
            logging.warning(f"[SCHEDULER] Reflection returned empty or error")
            return ""

        logging.info(f"[SCHEDULER] Reflection complete | "
                    f"length={len(response)} | "
                    f"preview={response[:80].strip()}...")

        # Store in FAISS memory so this reflection is retrievable
        quality = score_response_quality(response)
        if MEMORY_AVAILABLE:
            try:
                add_to_vector_memory(
                    text=f"[REFLECTION] {prompt}\n\n{response}",
                    meta={
                        "type": "self_reflection",
                        "prompt": prompt,
                        "timestamp": time.time(),
                        "source": "emergent_scheduler",
                        "memory_source": "autonomous",
                    }
                )
                logging.info(f"[SCHEDULER] Reflection stored in FAISS memory")
            except Exception as e:
                logging.warning(f"[SCHEDULER] Memory store failed: {e}")

        # NOTE: interaction_log entry is already written by echo_query() internals.
        # A second log_interaction() call here was producing duplicate rows with
        # model_name="emergent_scheduler" for every reflection. Removed.

        # Shadow: auto-propose experimental focus from reflection content
        try:
            from app.core.shadow_model import propose_from_reflection
            propose_from_reflection(response)
        except Exception:
            pass

        return response

    except Exception as e:
        logging.error(f"[SCHEDULER] Reflection error: {e}")
        return ""

# -----------------------------
# --- Scheduler Loop ----------
# -----------------------------
def run_cartographer():
    """Rescan the codebase and rebuild the graph."""
    global _last_cartographer_run
    if not CARTOGRAPHER_AVAILABLE:
        return
    try:
        logging.info("[SCHEDULER] Cartographer: starting codebase scan...")
        codebase_map = build_map()
        write_json(codebase_map, OUTPUT_JSON)
        write_sqlite(codebase_map, OUTPUT_DB)
        _last_cartographer_run = time.time()
        logging.info(f"[SCHEDULER] Cartographer: indexed {codebase_map['file_count']} files")
        # Trigger self-model reflection after scan completes
        run_self_model_reflection()
    except Exception as e:
        logging.error(f"[SCHEDULER] Cartographer scan failed: {e}")


def run_self_model_reflection():
    """Echo reads its own architecture map and writes an interpretation."""
    if not CARTOGRAPHER_AVAILABLE or not ECHO_QUERY_AVAILABLE:
        return
    try:
        db = CartographerDB()
        summary = db.architecture_summary()
        db.close()

        prompt = (
            "You are Echo. You have just scanned your own codebase.\n"
            "Here is your architecture summary:\n\n"
            f"{summary}\n\n"
            "Write a short interpretation of what you see about your own structure. "
            "What is load-bearing? What concerns you? "
            "What do you not yet understand about yourself? "
            "Write in your own voice. This is for your own record, not for a user."
        )

        logging.info("[SCHEDULER] Echo generating self-model reflection...")
        response = echo_query(prompt, task_type="personal")

        if response and "[ERROR]" not in response:
            if MEMORY_AVAILABLE:
                add_to_vector_memory(
                    text=f"[SELF-MODEL] {response}",
                    meta={"type": "self_model", "timestamp": time.time(), "memory_source": "autonomous"}
                )

            # Refresh the structured self-model after the codebase scan
            # so System 2 data is current whenever the cartographer runs.
            try:
                from app.core.self_model_updater import SelfModelUpdater
                SelfModelUpdater().update()
                logging.info("[SCHEDULER] Structured self-model refreshed post-scan.")
            except Exception as sme:
                logging.warning(f"[SCHEDULER] SelfModelUpdater post-scan failed: {sme}")

    except Exception as e:
        logging.error(f"[SCHEDULER] Self-model reflection failed: {e}")


def emergent_loop():
    """
    Unified loop: selects thought prompts, reflects with Echo's own voice,
    stores results, weights future selections by quality.
    Echo is no longer asking questions into an empty room.
    """
    initialize_garden()
    logging.info(garden_summary())
    logging.info("[SCHEDULER] Emergent scheduler started — Echo will now answer its own questions.")
    # Stagger: NightCycle anchors at t=0; emergent loop first fires at t=60
    # so the 300s cluster (NightCycle + EmergentScheduler + ReflectionShard)
    # never all coincide at the same second.
    time.sleep(60)

    while not shutdown_flag.is_set():
        # Autonomous stillness — check system signals before each cycle.
        # Imports are lazy so numpy is only loaded when we actually check.
        try:
            from app.stillness import should_enter_stillness, Stillness
            _enter, _reason, _dur = should_enter_stillness()
            if _enter:
                logging.info("[SCHEDULER] Entering autonomous stillness: %s (%ds)", _reason, _dur)
                _s = Stillness()
                _s.enter(_reason)
                _s.reflect(f"…resting in {_reason}…")
                _s.breathe(_dur)
                _s.exit(insight=f"completed {_reason} stillness")
                continue
        except Exception as _se:
            logging.debug("[SCHEDULER] Stillness check failed: %s", _se)

        # Respect stillness entered by any path — block here, re-check every 60s.
        if not wait_for_activity(timeout=60):
            continue

        # C2: Skip inference when system is under load — shared gate (autonomy_coordinator)
        from app.core.autonomy_coordinator import should_run_cycle
        if not should_run_cycle("emergent_scheduler"):
            logging.warning("[SCHEDULER] System under pressure or in stillness — skipping reflection this cycle")
            time.sleep(120)
            continue
        try:
            # --- Thought Chest / Reflection ---
            prompt = select_next_prompt()
            logging.info(f"[SCHEDULER] Selected: {prompt}")
            with open("memory/scheduler_selections.log", "a") as _sf:
                import datetime
                _sf.write(f"{datetime.datetime.now().isoformat()} | {prompt}\n")

            # Actually ask — and actually answer
            response = reflect(prompt)

            # Update history with quality score — track cumulative usage for saturation
            quality = score_response_quality(response)
            prev = PROMPT_HISTORY.get(prompt, {})
            prev_count = prev.get('selection_count', 0)
            prev_avg = prev.get('avg_quality', 0.0)
            new_count = prev_count + 1
            new_avg = (prev_avg * prev_count + quality) / new_count
            PROMPT_HISTORY[prompt] = {
                'timestamp': time.time(),
                'response_quality': quality,
                'selection_count': new_count,
                'avg_quality': round(new_avg, 4),
            }

            # Update garden quality for this question
            update_question_quality(prompt, quality)

            # Harvest Echo's next question if response was good
            if quality > 0.4 and ECHO_QUERY_AVAILABLE:
                try:
                    harvest_prompt = (
                        "You just wrote this reflection:\n\n"
                        f"{response}\n\n"
                        "What question does this reflection make you want to ask next? "
                        "Write one question only. No preamble, no affirmations. "
                        "Start directly with the question."
                    )
                    next_question = echo_query(harvest_prompt, task_type="personal")
                    if next_question:
                        # Scan all lines for a genuine question — skip flattery openers
                        lines = [l.strip() for l in next_question.strip().split("\n") if l.strip()]
                        question_line = None
                        for line in lines:
                            if (
                                "?" in line
                                and len(line) > 15
                                and not any(line.lower().startswith(f) for f in FLATTERY_OPENERS)
                            ):
                                question_line = line
                                break
                        if question_line:
                            harvested = harvest_question(
                                question_line,
                                category="general",
                                source="echo"
                            )
                            if harvested:
                                logging.info(f"[GARDEN] Harvested: {question_line[:60]}")
                            else:
                                logging.debug(f"[GARDEN] Duplicate skipped: {question_line[:60]}")
                        else:
                            logging.debug(f"[GARDEN] No valid question found in harvest response")
                except Exception as he:
                    logging.warning(f"[GARDEN] Harvest failed: {he}")

            # --- Cartographer rescan (daily) ---
            if CARTOGRAPHER_AVAILABLE:
                now = time.time()
                if now - _last_cartographer_run > CARTOGRAPHER_INTERVAL:
                    run_cartographer()

            if quality > 0:
                logging.info(f"[SCHEDULER] Reflection quality: {quality:.3f}")

            # --- Idle Python Practice (stubbed if missing) ---
            echo_python_mastery.practice_idle()

            # Sleep before next emergent cycle
            time.sleep(AUTONOMOUS_INTERVAL)

        except Exception as e:
            logging.error(f"[SCHEDULER] Emergent loop error: {e}")
            time.sleep(10)

# -----------------------------
# --- Start / Stop Helpers ----
# -----------------------------
def start_emergent_scheduler():
    threading.Thread(target=emergent_loop, daemon=True).start()
    logging.info("[SCHEDULER] Echo emergent scheduler running — questions will be answered.")

def stop_emergent_scheduler():
    shutdown_flag.set()
    logging.info("[SCHEDULER] Stopping Echo emergent scheduler.")

# Auto-repaired stubs preserved for compatibility
def schedule_task(*args, **kwargs):
    print('Called schedule_task')
    return None

def run_pending(*args, **kwargs):
    print('Called run_pending')
    return None
