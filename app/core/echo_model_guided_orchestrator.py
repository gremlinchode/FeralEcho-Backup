# FILE: app/core/echo_model_guided_orchestrator.py

import threading
import time
import logging
import ast
import re


def _extract_dict_literal(text: str) -> str:
    """Extract the first {...} block from free-form model output, tolerating
    markdown fences and conversational preamble/postamble text around it.
    ast.literal_eval() requires the *entire* string to be a valid literal,
    but echo_query() returns Echo's own reflective voice, not raw structured
    output — a full-string literal_eval was near-guaranteed to fail on any
    real response with a preamble sentence or code fence around the dict."""
    if not text:
        return ""
    fence = re.search(r"```(?:json|python)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    candidate = fence.group(1) if fence else text
    brace = re.search(r"\{.*\}", candidate, re.DOTALL)
    return brace.group(0) if brace else ""

from app.autonomous_awareness import awareness_loop, AWARENESS_SLEEP, start_awareness_thread
from app.core.autonomous_loop_with_optuna import autonomous_loop, autonomous_loop_iteration, AUTONOMOUS_SLEEP, OPTUNA_SLEEP, optimizer, try_run_optuna
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
    while True:
        # Shared throttle/stillness gate (CLAUDE.md Finding 28, 2026-07-15):
        # this loop previously had no gate at all, unlike the other three
        # autonomy loops (emergent_loop, autonomous_loop, self_edit_loop),
        # and ran its full fetch+sandbox+Optuna cycle every hour regardless
        # of system load — autonomy_coordinator.py's own docstring names
        # only those three loops it protects; this one was conspicuously
        # absent.
        from app.core.autonomy_coordinator import should_run_cycle
        if not should_run_cycle("model_guided_orchestrator"):
            logger.info("[ModelGuidedOrchestrator] Skipping cycle — throttled or in stillness.")
            time.sleep(120)
            continue

        logger.info("Starting autonomous fetch + model-guided optimization cycle...")
        # Run single iteration of autonomous fetch loop safely
        try:
            autonomous_loop_iteration()
        except Exception as e:
            logger.error(f"Error during autonomous fetch iteration: {e}", exc_info=True)

        # ---------------- OPTUNA SELF-EDIT (hinted) ---------------- #
        # Gated through the shared try_run_optuna() lock in
        # autonomous_loop_with_optuna.py (CLAUDE.md Finding 28), not an
        # independent local timer — autonomous_loop_iteration() above calls
        # the same optimizer singleton through the same gate, and the two
        # used to fire back-to-back with no lock between them because each
        # kept its own OPTUNA_SLEEP timer seeded at 0.
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
                extracted = _extract_dict_literal(param_hints_str)
                if extracted:
                    try:
                        param_hints = ast.literal_eval(extracted)
                        if not isinstance(param_hints, dict):
                            raise ValueError("Parsed hints are not a dict")
                    except Exception:
                        logger.warning("[ParameterHints] Failed to parse model output, using empty hints.")
                        param_hints = {}
                else:
                    logger.warning("[ParameterHints] No dict-like block found in model output, using empty hints.")

            # Run Optuna self-edit with hints, through the shared gate —
            # ran=False here just means the gate wasn't due this cycle
            # (autonomous_loop_iteration() may already have used this
            # pass's turn), not an error.
            log_memory_event(event_type="info", content="Autonomous Optuna self-edit triggered")
            ran, best_params, best_score = try_run_optuna(param_hints=param_hints)
            if ran:
                log_memory_event(event_type="info",
                    content=f"Autonomous self-edit finished: best_params={best_params}, best_score={best_score}")
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

