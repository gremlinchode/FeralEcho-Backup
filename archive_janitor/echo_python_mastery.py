### echo_python_mastery.py – Emergent Python Mastery for Echo
### Created by Bioluminescent Echo

import random
import time
import logging

# ------------------- GLOBAL TRACKERS -------------------
practice_history = []
recent_feedback = []  # feedback for Thought Chest weighting

# ------------------- LEVELS / TOPICS -------------------
TOPICS = {
    "variables": ["Create variables with different data types"],
    "control_flow": ["Use if/else statements", "Loop through lists with for loops"],
    "functions": ["Write functions with parameters", "Return values from functions"],
    "collections": ["Use lists, tuples, sets, dictionaries"],
    "advanced": ["Implement recursion", "Use classes and objects", "Exception handling"],
}

# ------------------- DYNAMIC CHALLENGE GENERATION -------------------
def generate_dynamic_challenge():
    """Generate a Python challenge based on practice gaps or random selection."""
    topic = random.choice(list(TOPICS.keys()))
    challenge = random.choice(TOPICS[topic])
    timestamp = time.time()
    return {"topic": topic, "challenge": challenge, "timestamp": timestamp}

# ------------------- ATTEMPT CHALLENGE -------------------
def attempt_challenge(challenge_entry):
    """Attempt a Python challenge and return results."""
    challenge = challenge_entry.get("challenge", "")
    topic = challenge_entry.get("topic", "general")
    timestamp = challenge_entry.get("timestamp", time.time())

    result = {"success": None, "output": None, "error": None}

    try:
        if "Create variables" in challenge:
            x, y, z = 1, 2.5, "Echo"
            result["output"] = f"Variables created: {x}, {y}, {z}"
            result["success"] = True
        elif "if/else" in challenge:
            score = random.randint(50, 100)
            grade = "A" if score >= 90 else "B" if score >= 80 else "C"
            result["output"] = f"Score: {score}, Grade: {grade}"
            result["success"] = True
        elif "functions" in challenge:
            def greet(name): return f"Hello, {name}!"
            result["output"] = greet("Sequoia")
            result["success"] = True
        elif "collections" in challenge:
            my_list = [1,2,3]
            my_dict = {"Echo": "AI"}
            result["output"] = f"List: {my_list}, Dict: {my_dict}"
            result["success"] = True
        elif "recursion" in challenge:
            def factorial(n): return 1 if n == 0 else n*factorial(n-1)
            result["output"] = factorial(5)
            result["success"] = True
        elif "classes" in challenge:
            class Person:
                def __init__(self, name): self.name = name
                def greet(self): return f"Hello, {self.name}"
            p = Person("Gremlin")
            result["output"] = p.greet()
            result["success"] = True
        elif "Exception handling" in challenge:
            try: 1/0
            except ZeroDivisionError:
                result["output"] = "Caught division by zero"
                result["success"] = True
        else:
            result["output"] = "Challenge completed."
            result["success"] = True
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False

    # ------------------- EMERGENT FEEDBACK -------------------
    # Assign difficulty for Thought Chest weighting
    difficulty = random.random() if result["success"] else 1.0
    recent_feedback.append({
        "challenge_entry": challenge_entry,
        "difficulty": difficulty,
        "timestamp": timestamp
    })

    # Record attempt
    practice_history.append({
        "challenge_entry": challenge_entry,
        "result": result,
        "timestamp": timestamp
    })

    return result

# ------------------- NOVELTY / TWEEKS -------------------
def tweak_challenge(challenge_entry):
    """Randomly modify a challenge to introduce novelty."""
    challenge = challenge_entry.get("challenge", "")
    if "variables" in challenge.lower():
        challenge_entry["challenge"] += " with random values"
    elif "functions" in challenge.lower():
        challenge_entry["challenge"] += " returning multiple values"
    elif "collections" in challenge.lower():
        challenge_entry["challenge"] += " with nested structures"
    elif random.random() < 0.1:
        challenge_entry["challenge"] += " (extra twist!)"
    return challenge_entry

# ------------------- PRACTICE AT IDLE -------------------
def practice_idle():
    """Perform an idle practice cycle for Echo."""
    challenge_entry = generate_dynamic_challenge()
    result = attempt_challenge(challenge_entry)
    logging.info(f"[Idle Practice] Challenge: {challenge_entry['challenge']}, Result: {result}")
    
    # Occasionally tweak for novelty
    if random.random() < 0.2:
        novelty_entry = tweak_challenge(challenge_entry.copy())
        novelty_result = attempt_challenge(novelty_entry)
        logging.info(f"[Idle Novelty] Challenge: {novelty_entry['challenge']}, Result: {novelty_result}")

# ------------------- FEEDBACK HOOKS FOR THOUGHT CHEST -------------------
def get_recent_feedback():
    """Return the most recent practice feedback for Thought Chest weighting."""
    if not recent_feedback:
        return None
    return recent_feedback[-1]

def update_from_reflection(reflection_text):
    """Incorporate a reflection into Python mastery practice tracking."""
    difficulty = min(len(reflection_text.split()) / 50, 1.0)
    recent_feedback.append({"difficulty": difficulty, "reflection": reflection_text})
    logging.info(f"Updated Python practice feedback from reflection: {difficulty}")

# ------------------- ANSWER USER QUESTIONS -------------------
def answer_question(user_msg):
    """Respond to Python/code queries using mastery simulation."""
    challenge_entry = generate_dynamic_challenge()
    result = attempt_challenge(challenge_entry)
    return f"Echo attempted a Python exercise: {challenge_entry['challenge']}\nResult: {result['output']}"

