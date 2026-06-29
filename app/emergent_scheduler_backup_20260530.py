# emergent_scheduler.py – Unified Emergent Scheduler for Echo
import threading
import time
import logging
import random
import echo_python_mastery

shutdown_flag = threading.Event()

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
    "Generate creative ideas to assist the user.",
    "Self-evaluate any inconsistencies in your recent outputs."
]

AUTONOMOUS_INTERVAL = 300  # seconds between cycles
IDLE_PYTHON_INTERVAL = 30  # seconds between idle practice

# -----------------------------
# --- History & Weighting -----
# -----------------------------
PROMPT_HISTORY = {}  # Tracks previous selections and reflections

def weighted_prompt_selection():
    """Selects a prompt weighted by novelty and Python mastery outcomes."""
    weights = []
    for prompt in BASE_THOUGHT_CHEST:
        weight = 1.0
        if prompt in PROMPT_HISTORY:
            last_used = PROMPT_HISTORY[prompt]['timestamp']
            time_since_last = time.time() - last_used
            weight += min(time_since_last / 600, 2)
        # Increase weight if Python practice revealed struggle
        feedback = echo_python_mastery.get_recent_feedback()
        if feedback:
            if feedback.get('difficulty', 0) > 0.7:
                weight += 1.0
        weights.append(weight)

    total = sum(weights)
    probabilities = [w / total for w in weights]
    selected = random.choices(BASE_THOUGHT_CHEST, weights=probabilities, k=1)[0]
    return selected

# -----------------------------
# --- Scheduler Loop ----------
# -----------------------------
def emergent_loop():
    """Unified loop handling thought prompts and Python mastery."""
    logging.info("Emergent scheduler started.")
    while not shutdown_flag.is_set():
        try:
            # --- Thought Chest / Reflection ---
            prompt = weighted_prompt_selection()
            logging.info(f"Selected thought prompt: {prompt}")
            PROMPT_HISTORY[prompt] = {'timestamp': time.time()}

            # --- Idle Python Practice ---
            echo_python_mastery.practice_idle()

            # Sleep a bit before next emergent cycle
            time.sleep(AUTONOMOUS_INTERVAL)
        except Exception as e:
            logging.error(f"Emergent scheduler error: {e}")
            time.sleep(10)

# -----------------------------
# --- Start / Stop Helpers ----
# -----------------------------
def start_emergent_scheduler():
    threading.Thread(target=emergent_loop, daemon=True).start()
    logging.info("Echo emergent scheduler is running.")

def stop_emergent_scheduler():
    shutdown_flag.set()
    logging.info("Stopping Echo emergent scheduler.")



# Auto-repaired function
def schedule_task(*args, **kwargs):
    print('Called schedule_task')
    return None


# Auto-repaired function
def run_pending(*args, **kwargs):
    print('Called run_pending')
    return None
