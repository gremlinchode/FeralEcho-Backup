# autonomous_reflection.py – Emergent Autonomous Reflection
import threading
import time
import logging
from app.core import self_edit_manager
from app.core.memory_bridge import log_dream_bridge
from autonomous_thought_chest import weighted_prompt_selection
import echo_python_mastery

shutdown_flag = threading.Event()
AUTONOMOUS_SLEEP = 300  # seconds between cycles

def reflection_loop():
    """Autonomous reflection loop using emergent Thought Chest and Python feedback."""
    logging.info("Emergent autonomous reflection loop started.")
    
    while not shutdown_flag.is_set():
        try:
            # --- Select a prompt using weighted, emergent criteria ---
            prompt = weighted_prompt_selection()
            logging.info(f"Selected reflection prompt: {prompt}")
            
            # --- Perform autonomous self-edit / reflection ---
            reflection = self_edit_manager.autonomous_self_edit_cycle(prompt)
            
            if reflection:
                # Log reflection in memory
                log_dream_bridge(reflection)
                logging.info(f"Reflection logged: {reflection}")

                # Feed reflection into Python mastery practice for emergent learning
                echo_python_mastery.update_from_reflection(reflection)

        except Exception as e:
            logging.error(f"Autonomous reflection error: {e}")

        # Sleep before next cycle
        time.sleep(AUTONOMOUS_SLEEP)

def start_reflection_loop():
    """Start the emergent reflection loop in a daemon thread."""
    threading.Thread(target=reflection_loop, daemon=True).start()
    logging.info("Emergent reflection loop thread started.")

def stop_reflection_loop():
    """Signal the loop to stop."""
    shutdown_flag.set()
    logging.info("Emergent reflection loop stopped.")

