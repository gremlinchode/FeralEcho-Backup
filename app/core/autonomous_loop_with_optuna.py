# app/core/autonomous_loop_with_optuna.py
"""
Extracted single-iteration loop for use by echo_model_guided_orchestrator.
Wraps app/autonomous_loop.py logic into a callable iteration function
so the guided orchestrator can run one cycle without spawning a while True.

This file was the missing link causing autonomous_loop_iteration() to throw
a NameError on every guided orchestrator cycle, silently disabling all
model routing and ML learning.
"""

import time
import logging
import random

# Re-export autonomous_loop so echo_model_guided_orchestrator can import it
from app.autonomous_loop import autonomous_loop

from app.internet_tools.autonomous_fetch import FETCH_SOURCES, fetch_and_log
from app.core.echo_optuna import EchoOptuna
from app.core.memory_tools import log_memory_event
from app.core.awareness_tools_integration import discover_and_register_tools
from app.core.memory_bridge import log_dream_bridge
from app.autonomous_harmony_manager import get_harmony_manager
from sandbox.run_script import run_sandbox_script_isolated as run_sandbox_script

import os

# ---------------- CONFIG ---------------- #
# Exported so echo_model_guided_orchestrator can import them
AUTONOMOUS_SLEEP = 3600
OPTUNA_SLEEP = 7200
SANDBOX_INTERVAL = 3
TOOLS_PATH = os.path.join(os.getcwd(), "app", "tools")

logger = logging.getLogger(__name__)

# ---------------- SHARED STATE ---------------- #
# Single instances shared across iteration calls
optimizer = EchoOptuna()
# Process-wide singleton, shared with app/autonomous_loop.py — see
# get_harmony_manager()'s docstring in autonomous_harmony_manager.py.
harmony_manager = get_harmony_manager()

# Cycle counter persists across iteration calls
_cycle_state = {
    "count": 0,
    "last_optuna_run": 0,
}

# ---------------- SANDBOX ---------------- #
def _run_sandbox_cycle():
    """Run a single sandbox experiment. Returns True on success."""
    try:
        sandbox_scripts = ["hello_sandbox.py"]
        script_to_run = random.choice(sandbox_scripts)
        script_path = os.path.join("sandbox", "scripts", script_to_run)
        logger.info(f"[SANDBOX] Running sandbox: {script_to_run}")
        result = run_sandbox_script(script_path, timeout=600)
        output = result.get("output") or result.get("error")
        if result["success"]:
            logger.info(f"[SANDBOX RESULT] {output}")
        else:
            logger.warning(f"[SANDBOX ERROR] {output}")
        log_dream_bridge(f"Sandbox run: {script_to_run} | Result: {output}",
                         meta={"role": "sandbox_run", "memory_source": "autonomous"})
        return True
    except Exception as e:
        logger.error(f"[SANDBOX] Error: {e}", exc_info=True)
        return False

# ---------------- HARMONY ---------------- #
def _maybe_run_harmony(fetch_count, sandbox_ran, optuna_ran):
    """
    Decide autonomously whether to enter Harmony based on cycle intensity.
    Mirrors the logic in autonomous_loop.py.
    """
    score = fetch_count + (2 if sandbox_ran else 0) + (3 if optuna_ran else 0)
    # Simple threshold: busy or quiet cycles trigger harmony
    should_run = score >= 5 or score <= 1 or random.random() < 0.1
    if should_run:
        logger.info("Echo decides to enter Harmony (Nature Spark + Stillness).")
        harmony_manager.start()
        time.sleep(random.randint(60, 180))
        harmony_manager.stop()
        logger.info("Harmony session ended.")

# ---------------- SINGLE ITERATION ---------------- #
def autonomous_loop_iteration():
    """
    Execute one full autonomous cycle without looping or sleeping.
    Called by echo_model_guided_orchestrator on each pass of its own loop.

    Steps:
        1. Fetch content from all registered sources
        2. Discover and register Python tools
        3. Occasionally run a sandbox experiment
        4. Run Optuna self-edit if enough time has elapsed
        5. Evaluate cycle intensity and optionally enter Harmony
    """
    _cycle_state["count"] += 1
    cycle_count = _cycle_state["count"]
    fetch_count = 0

    logger.info(f"[ITERATION] Starting autonomous cycle #{cycle_count}")

    # 1. Fetch content
    for name, url in FETCH_SOURCES:
        try:
            fetch_and_log(name, url)
            fetch_count += 1
        except Exception as e:
            logger.error(f"[FETCH] Error fetching ({name}, {url}): {e}", exc_info=True)

    # 2. Tool discovery
    try:
        discover_and_register_tools(TOOLS_PATH)
        logger.info("[TOOLS] Tool discovery complete.")
    except Exception as e:
        logger.error(f"[TOOLS] Discovery failed: {e}", exc_info=True)

    # 3. Sandbox (every SANDBOX_INTERVAL cycles)
    sandbox_ran = False
    if cycle_count % SANDBOX_INTERVAL == 0:
        sandbox_ran = _run_sandbox_cycle()

    # 4. Optuna self-edit (rate limited by OPTUNA_SLEEP)
    now = time.time()
    optuna_ran = False
    if now - _cycle_state["last_optuna_run"] > OPTUNA_SLEEP:
        try:
            log_memory_event("info", "Optuna self-edit triggered")
            best_params, best_score = optimizer.optimize_self_edit(n_trials=10)
            log_memory_event(
                "info",
                f"Self-edit finished: best_params={best_params}, best_score={best_score}"
            )
            _cycle_state["last_optuna_run"] = now
            optuna_ran = True
        except Exception as e:
            logger.error(f"[OPTUNA] Error: {e}", exc_info=True)

    # 5. Harmony check
    _maybe_run_harmony(fetch_count, sandbox_ran, optuna_ran)

    logger.info(f"[ITERATION] Cycle #{cycle_count} complete.")
