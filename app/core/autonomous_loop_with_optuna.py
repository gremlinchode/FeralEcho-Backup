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
import threading

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

# Guards _cycle_state["last_optuna_run"] and the optimize_self_edit() call
# below (CLAUDE.md Finding 28, 2026-07-15): autonomous_loop_iteration() and
# echo_model_guided_orchestrator.model_guided_autonomous_loop() used to each
# keep their own independent OPTUNA_SLEEP timer against this same optimizer
# singleton, both seeded at 0 — they could both evaluate true in the same
# outer pass and fire two separate 10-trial Optuna batches back to back,
# with no lock between them. try_run_optuna() below is now the single gated
# entry point both callers use instead.
_optuna_gate_lock = threading.Lock()


def try_run_optuna(param_hints: dict | None = None):
    """Atomically check-and-fire the shared OPTUNA_SLEEP gate, then run
    optimize_self_edit() if allowed. Returns (ran: bool, best_params, best_score).
    Both autonomous_loop_iteration() and model_guided_autonomous_loop() call
    this instead of each maintaining their own independent timer."""
    with _optuna_gate_lock:
        now = time.time()
        if now - _cycle_state["last_optuna_run"] <= OPTUNA_SLEEP:
            return False, None, None
        _cycle_state["last_optuna_run"] = now
    try:
        best_params, best_score = optimizer.optimize_self_edit(n_trials=10, param_hints=param_hints)
        return True, best_params, best_score
    except Exception:
        # Don't let a failed trial silently re-block the gate for another
        # full OPTUNA_SLEEP — a caller-side try/except already logs the
        # real error; re-raise so that logging still happens at the call site.
        raise

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

    # 4. Optuna self-edit — gated through the shared try_run_optuna() lock
    # (CLAUDE.md Finding 28) rather than this function's own timer, since
    # model_guided_autonomous_loop() also calls into the same optimizer.
    optuna_ran = False
    try:
        log_memory_event("info", "Optuna self-edit triggered")
        optuna_ran, best_params, best_score = try_run_optuna()
        if optuna_ran:
            log_memory_event(
                "info",
                f"Self-edit finished: best_params={best_params}, best_score={best_score}"
            )
    except Exception as e:
        logger.error(f"[OPTUNA] Error: {e}", exc_info=True)

    # 5. Harmony check
    _maybe_run_harmony(fetch_count, sandbox_ran, optuna_ran)

    logger.info(f"[ITERATION] Cycle #{cycle_count} complete.")
