# FILE: app/core/echo_model_guided_orchestrator.py

import threading
import time
import logging
import ast

from app.autonomous_awareness import awareness_loop, AWARENESS_SLEEP, start_awareness_thread
from app.core.autonomous_loop_with_optuna import autonomous_loop, autonomous_loop_iteration, AUTONOMOUS_SLEEP, OPTUNA_SLEEP, optimizer
from app.core.echo_model_orchestrator import echo_query
from app.core.memory_tools import log_memory_event, get_last_entries as retrieve_recent_reflections
logger = logging.getLogger(__name__)

# -----------------------------
# 1. Model-Guided Reflection
# -----------------------------
def generate_parameter_hints(reflection_text, use_all_models=False):
    """
    Feed awareness reflection into models to generate suggested Optuna parameter hints.
    """
    prompt = (
        "You are assisting Echo in optimizing its self-edit parameters. "
        "Based on the following reflection insights, suggest improvements "
        "for self-edit trials or parameters. Only return a dict-style string: \n\n"
        f"{reflection_text}"
    )
    try:
        response = echo_query(prompt, use_all=use_all_models)
        # If using multiple models, pick the longest valid response
        if use_all_models and isinstance(response, dict):
            best_response = ""
            for r in response.values():
                if "[ERROR]" not in r and len(r) > len(best_response):
                    best_response = r
            response = best_response
        return response
    except Exception as e:
        logger.error(f"[ParameterHints] Model reflection failed: {e}")
        return "{}"

# -----------------------------
# 2. Awareness Thread Wrapper
# -----------------------------
# start_awareness_thread is imported from app.autonomous_awareness (singleton-guarded)

# -----------------------------
# 3. Self-Edit Loop With Reflection Integration
# -----------------------------
def model_guided_autonomous_loop():
    last_optuna_run = 0
    while True:
        logger.info("Starting autonomous fetch + model-guided optimization cycle...")
        # Run single iteration of autonomous fetch loop safely
        try:
            autonomous_loop_iteration()
        except Exception as e:
            logger.error(f"Error during autonomous fetch iteration: {e}", exc_info=True)

        # ---------------- OPTUNA SELF-EDIT ---------------- #
        now = time.time()
        if now - last_optuna_run > OPTUNA_SLEEP:
            try:
                # Retrieve latest reflections from awareness
                reflection_summary = retrieve_recent_reflections(n=5)
                reflection_text = "\n".join([r.get('content', '') for r in reflection_summary])
                
                # Generate parameter hints via models
                param_hints_str = generate_parameter_hints(reflection_text, use_all_models=False)
                logger.info(f"[ParameterHints] Model suggestions: {param_hints_str}")
                
                # Convert string to dict safely
                param_hints = {}
                if param_hints_str:
                    try:
                        param_hints = ast.literal_eval(param_hints_str)
                        if not isinstance(param_hints, dict):
                            raise ValueError("Parsed hints are not a dict")
                    except Exception:
                        logger.warning("[ParameterHints] Failed to parse model output, using empty hints.")
                        param_hints = {}
                
                # Run Optuna self-edit with hints
                log_memory_event(event_type="info", content="Autonomous Optuna self-edit triggered")
                best_params, best_score = optimizer.optimize_self_edit(n_trials=10, param_hints=param_hints)
                log_memory_event(event_type="info",
                    content=f"Autonomous self-edit finished: best_params={best_params}, best_score={best_score}")
                last_optuna_run = now
            except Exception as e:
                logger.error(f"Error during model-guided self-edit: {e}", exc_info=True)
        
        logger.info(f"Sleeping {AUTONOMOUS_SLEEP}s before next autonomous cycle...")
        time.sleep(AUTONOMOUS_SLEEP)

# -----------------------------
# 4. Thread Starters
# -----------------------------
def start_autonomous_thread():
    thread = threading.Thread(target=model_guided_autonomous_loop, daemon=True)
    thread.start()
    logger.info(f"Model-guided autonomous loop started (sleep {AUTONOMOUS_SLEEP}s).")

# -----------------------------
# 5. Orchestrator Entry Point
# -----------------------------
def start_orchestrator():
    logger.info("Starting Echo Model-Guided Autonomous Orchestrator...")
    start_awareness_thread()
    start_autonomous_thread()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Echo Orchestrator terminated by user.")

# -----------------------------
# 6. Example Usage
# -----------------------------
if __name__ == "__main__":
    start_orchestrator()

