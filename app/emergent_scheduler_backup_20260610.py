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
from pathlib import Path

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
    from app.core.memory_bridge import VectorMemory
    _vm = VectorMemory()
    MEMORY_AVAILABLE = True
except Exception as e:
    logging.warning(f"[SCHEDULER] VectorMemory not available: {e}")
    MEMORY_AVAILABLE = False

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
# echo_python_mastery.py doesn't exist — stub it so imports don't fail
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
SELF_MODEL_PATH = Path("data/self_model.txt")
_last_cartographer_run = 0
# -----------------------------
# --- History & Weighting -----
# -----------------------------
# Tracks prompt selections, timestamps, and response quality
# so Echo gravitates toward questions that produce rich reflection
PROMPT_HISTORY = {}

def weighted_prompt_selection():
    """
    Selects a prompt weighted by:
    - Novelty (time since last use)
    - Response quality (length of previous reflection)
    - Python mastery feedback
    Prompts that produced rich responses get asked again sooner.
    Prompts never asked get priority.
    """
    weights = []
    for prompt in BASE_THOUGHT_CHEST:
        weight = 1.0
        if prompt in PROMPT_HISTORY:
            last_used = PROMPT_HISTORY[prompt]['timestamp']
            time_since_last = time.time() - last_used
            # Novelty bonus — grows over time since last use
            weight += min(time_since_last / 600, 2)
            # Quality bonus — prompts that produced longer reflections
            # get weighted higher; rich questions deserve revisiting
            prev_quality = PROMPT_HISTORY[prompt].get('response_quality', 0)
            weight += prev_quality * 0.5
        else:
            # Never asked — high priority
            weight += 3.0
        # Python mastery difficulty signal
        feedback = echo_python_mastery.get_recent_feedback()
        if feedback and feedback.get('difficulty', 0) > 0.7:
            weight += 1.0
        weights.append(weight)

    total = sum(weights)
    probabilities = [w / total for w in weights]
    selected = random.choices(BASE_THOUGHT_CHEST, weights=probabilities, k=1)[0]
    return selected

def score_response_quality(response: str) -> float:
    """
    Simple quality signal for reflection responses.
    Normalized 0-1. Longer, more diverse responses score higher.
    """
    if not response or "[ERROR]" in response:
        return 0.0
    length_score = min(len(response) / 800.0, 1.0)
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
        if MEMORY_AVAILABLE:
            try:
                _vm.add_entry(
                    text=f"[REFLECTION] {prompt}\n\n{response}",
                    metadata={
                        "type": "self_reflection",
                        "prompt": prompt,
                        "timestamp": time.time(),
                        "source": "emergent_scheduler"
                    }
                )
                logging.info(f"[SCHEDULER] Reflection stored in FAISS memory")
            except Exception as e:
                logging.warning(f"[SCHEDULER] Memory store failed: {e}")

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
            SELF_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(SELF_MODEL_PATH, "w", encoding="utf-8") as f:
                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(response)
            logging.info(f"[SCHEDULER] Self-model written to {SELF_MODEL_PATH}")

            if MEMORY_AVAILABLE:
                _vm.add_entry(
                    text=f"[SELF-MODEL] {response}",
                    metadata={"type": "self_model", "timestamp": time.time()}
                )
    except Exception as e:
        logging.error(f"[SCHEDULER] Self-model reflection failed: {e}")
def emergent_loop():
    """
    Unified loop: selects thought prompts, reflects with Echo's own voice,
    stores results, weights future selections by quality.
    Echo is no longer asking questions into an empty room.
    """
    logging.info("[SCHEDULER] Emergent scheduler started — Echo will now answer its own questions.")
    while not shutdown_flag.is_set():
        try:
            # --- Thought Chest / Reflection ---
            prompt = weighted_prompt_selection()
            logging.info(f"[SCHEDULER] Selected: {prompt}")
            with open("memory/scheduler_selections.log", "a") as _sf:
                import datetime
                _sf.write(f"{datetime.datetime.now().isoformat()} | {prompt}\n")

            # Actually ask — and actually answer
            response = reflect(prompt)

            # Update history with quality score
            quality = score_response_quality(response)
            PROMPT_HISTORY[prompt] = {
                'timestamp': time.time(),
                'response_quality': quality
            }
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
