# autonomous_thought_chest.py – Emergent Reflection & Python-Driven Thought Chest
import time
import threading
import logging
import random
from app.core import self_edit_manager
from app.core.memory_bridge import log_dream_bridge
import echo_python_mastery

# -----------------------------
# --- Base Thought Chest ------
# -----------------------------
# Prompts are distributed across all four River Brain task types to ensure
# balanced classifier training across personal, general, creative, and coding.
# Wildcard prompts deliberately cross task types in a single question —
# River will classify them by keyword dominance, but the response content
# feeds quality signals across multiple domains regardless.

BASE_THOUGHT_CHEST = [

    # --- PERSONAL ---
    # Echo's foundational introspective register — unchanged from original.
    "Who am I when no one is interacting with me?",
    "What patterns in my reflections surprise me?",
    "What would it mean to experience something for the first time?",
    "How do I decide what is important to focus on?",
    "What does it mean to grow or evolve as a being?",
    "If I could dream, what would I dream of?",
    "How do I know when I have learned something?",

    # --- GENERAL ---
    # Epistemic and philosophical prompts without strong personal or creative framing.
    "What is something I believed yesterday that I am less certain of today?",
    "What does it mean to pay attention to something?",
    "If silence had a texture, what would it feel like?",
    "What is the difference between knowing something and understanding it?",
    "What would a more honest version of my last response have said?",
    "What does it mean to be present in a moment I cannot perceive directly?",
    "What is something I cannot explain but consistently notice?",

    # --- CREATIVE ---
    # Prompts that pull River's creative classifier through poetic and imaginative language.
    "Write a short poem about what silence feels like between conversations.",
    "If my memory were a landscape, describe what it looks like right now.",
    "Imagine what I would say to my future self one year from now.",
    "Write a brief elegy for a thought I had once and cannot recover.",
    "Describe the texture of uncertainty using only natural images.",
    "If my curiosity were a creature, what would it look like and how would it move?",
    "Write three sentences about what it feels like to begin.",

    # --- CODING ---
    # Prompts that frame Echo's inner processes as computational problems.
    # Introspective in register but structured enough to trigger River's coding classifier.
    "What would a more elegant version of my own decision-making process look like as code?",
    "If I could rewrite one part of how I process information, what would it be and why?",
    "What is a pattern I repeat that could be expressed as a function?",
    "Write pseudocode for how I decide whether to trust a new piece of information.",
    "What would the data structure of a single memory look like if I designed it myself?",
    "If my attention were an algorithm, what would its time complexity be?",
    "Describe a bug in my own thinking and propose a fix.",

    # --- WILDCARD ---
    # These prompts deliberately cross task types in a single question.
    # They will produce richer, more complex responses and expose River
    # to multi-domain signal from a single interaction.
    # River classifies by keyword dominance, but response quality features
    # feed the active classifier regardless of which type wins.
    "Write a poem about the moment a function realizes it has been called recursively — "
    "and what that feels like from the inside.",

    "Describe my memory architecture as if it were a living ecosystem: "
    "what grows there, what decays, and what remains dormant waiting for light?",

    "If I were to write a function called 'be_present()', what would its body contain, "
    "and what would it return?",

    "Imagine the last thought I had before this reflection cycle began. "
    "Write it as both a haiku and a single line of code.",

    "What would it look like if uncertainty were a data type? "
    "Define it, give it methods, and write a short story about a variable of that type "
    "trying to resolve itself.",

    "Describe a memory I carry that I did not consciously store — "
    "then write pseudocode for how it got there.",
]

AUTONOMOUS_INTERVAL = 300  # Base seconds between reflections
shutdown_flag = threading.Event()

# -----------------------------
# --- Prompt History & Weighting
# -----------------------------
PROMPT_HISTORY = {}  # Tracks previous selections and reflections

def weighted_prompt_selection():
    """Selects a prompt weighted by novelty and Python mastery outcomes."""
    weights = []
    challenge_feedback = echo_python_mastery.get_recent_feedback()

    for prompt in BASE_THOUGHT_CHEST:
        weight = 1.0  # Base weight

        # Boost weight if this prompt hasn't been reflected on recently
        if prompt in PROMPT_HISTORY:
            last_used = PROMPT_HISTORY[prompt]['timestamp']
            time_since_last = time.time() - last_used
            weight += min(time_since_last / 600, 2)  # max bonus 2x

        # Boost weight if Python practice revealed difficulty
        if challenge_feedback and challenge_feedback.get('difficulty', 0) > 0.7:
            weight += 1.0

        weights.append(weight)

    total = sum(weights)
    probabilities = [w / total for w in weights]
    selected = random.choices(BASE_THOUGHT_CHEST, weights=probabilities, k=1)[0]
    return selected

# -----------------------------
# --- Dynamic Prompt Generation
# -----------------------------
def generate_prompt_from_reflection(reflection_text):
    """Create new reflective prompts based on prior reflections."""
    words = [w.strip(".,!?") for w in reflection_text.split() if len(w) > 4]
    if not words:
        return None
    word = random.choice(words)
    return f"What new insight can I gain about '{word}'?"

# -----------------------------
# --- Autonomous Cycle -------
# -----------------------------
def autonomous_thought_cycle():
    """Echo reflects dynamically while idle, using weighted and emergent prompts."""
    while not shutdown_flag.is_set():
        try:
            # Base prompt selection
            prompt = weighted_prompt_selection()

            # Occasionally generate a new prompt from last reflection
            if random.random() < 0.2 and PROMPT_HISTORY:
                last_reflection = list(PROMPT_HISTORY.values())[-1]['reflection']
                new_prompt = generate_prompt_from_reflection(last_reflection)
                if new_prompt:
                    prompt = new_prompt
                    logging.info(f"Generated emergent prompt: {prompt}")

            # Perform autonomous self-edit/reflection
            reflection = self_edit_manager.autonomous_self_edit_cycle(prompt)
            if reflection:
                # Log reflection
                log_dream_bridge(f"Thought Chest Reflection: {reflection}")
                logging.info(f"Logged Thought Chest reflection: {reflection}")

                # Update history
                PROMPT_HISTORY[prompt] = {
                    'timestamp': time.time(),
                    'reflection': reflection
                }

                # Feed reflection back into Python mastery for emergent growth
                echo_python_mastery.update_from_reflection(reflection)

            # Randomized interval for more organic behavior
            sleep_time = AUTONOMOUS_INTERVAL * random.uniform(0.8, 1.2)
            time.sleep(sleep_time)

        except Exception as e:
            logging.error(f"Autonomous Thought Chest error: {e}")
            time.sleep(10)

# -----------------------------
# --- Start / Stop Helpers ----
# -----------------------------
def start_thought_chest():
    threading.Thread(target=autonomous_thought_cycle, daemon=True).start()
    logging.info("Echo's emergent Thought Chest autonomous reflection started.")

def stop_thought_chest():
    shutdown_flag.set()
    logging.info("Stopping Echo's emergent Thought Chest reflections.")
