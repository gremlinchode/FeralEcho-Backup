# app/autonomous_loop.py
"""
Autonomous Loop for FeralEcho – Upgraded
- Fetches content from sources periodically
- Runs Optuna-based self-edit optimization
- Dynamically discovers and registers Python tools
- Executes autonomous sandbox experiments
- Runs Harmony (Nature Spark + Stillness) autonomously based on activity
"""

import os
import threading
import time
import warnings
import logging
import random
from collections import deque

# ---------------- SAFEGUARDS ---------------- #
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="resource_tracker: There appear to be .* leaked semaphore objects"
)

try:
    import torch
    torch.set_num_threads(1)
except ImportError:
    pass

try:
    import faiss
    faiss.omp_set_num_threads(1)
except ImportError:
    pass

# ---------------- IMPORTS ---------------- #
from app.internet_tools.autonomous_fetch import FETCH_SOURCES, fetch_and_log

try:
    from app.core.predictive_loop import get_world_model as _get_world_model
except Exception:
    _get_world_model = lambda: None

try:
    from app.core.echo_model_orchestrator import log_interaction as _log_interaction
    _LOG_INTERACTION_AVAILABLE = True
except Exception:
    _LOG_INTERACTION_AVAILABLE = False

try:
    from app.core.system_guard import should_throttle
except Exception:
    should_throttle = lambda: False

from app.core.echo_optuna import EchoOptuna
from app.core.memory_tools import log_memory_event
from app.core.awareness_tools_integration import discover_and_register_tools
from sandbox.runner import run_sandbox_script
from app.core.memory_bridge import log_dream_bridge
from app.autonomous_harmony_manager import HarmonyManager

# ---------------- CONFIG ---------------- #
AUTONOMOUS_SLEEP = 3600
OPTUNA_SLEEP = 7200
SANDBOX_INTERVAL = 3
TOOLS_PATH = os.path.join(os.getcwd(), "app", "tools")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

optimizer = EchoOptuna()
harmony_manager = HarmonyManager()

# ---------------- CYCLE HISTORY ---------------- #
RECENT_CYCLES = deque(maxlen=5)  # store last 5 cycles' intensity scores

def record_cycle_intensity(fetch_count, sandbox_ran, optuna_ran):
    """Compute a simple intensity score for this cycle."""
    score = fetch_count + (2 if sandbox_ran else 0) + (3 if optuna_ran else 0)
    RECENT_CYCLES.append(score)
    return score

def should_enter_harmony():
    """Decide autonomously if Harmony should run."""
    if not RECENT_CYCLES:
        return False
    avg_intensity = sum(RECENT_CYCLES) / len(RECENT_CYCLES)
    # Trigger if recent cycles are very busy or unusually quiet
    if avg_intensity >= 5 or avg_intensity <= 1:
        return True
    # Small random chance otherwise
    return random.random() < 0.1

# ---------------- SANDBOX EXECUTION ---------------- #
def run_autonomous_sandbox_cycle():
    """Lets Echo safely execute sandbox experiments.

    Alternates between the static hello_sandbox.py baseline and
    Echo-generated experiments via ExperimentRunner. Generated
    experiments are based on current curiosity (WorldModel topic
    or weak task type from self_model).
    """
    try:
        # Every other cycle: generate a fresh Echo experiment
        if random.random() < 0.5:
            try:
                from sandbox.experiment_runner import generate_and_run, log_experiment_result
                result = generate_and_run(timeout=60)
                log_experiment_result(result)
                tag = "RESULT" if result["success"] else "FAILED"
                logger.info(f"[EXPERIMENT] {tag} | topic={result.get('topic','?')[:60]}")
                return result["success"]
            except Exception as exp_err:
                logger.warning(f"[EXPERIMENT] Falling back to hello_sandbox: {exp_err}")

        # Baseline: original hello_sandbox.py
        script_to_run = "hello_sandbox.py"
        logger.info(f"[SANDBOX] Running baseline: {script_to_run}")
        result = run_sandbox_script(script_to_run, timeout=600)
        output = result.get("output") or result.get("error")
        if result["success"]:
            logger.info(f"[SANDBOX RESULT] {output}")
        else:
            logger.warning(f"[SANDBOX ERROR] {output}")
        log_dream_bridge(f"Sandbox run: {script_to_run} | Result: {output}",
                         meta={"memory_source": "autonomous"})
        return True
    except Exception as e:
        logger.error(f"[SANDBOX] Error: {e}", exc_info=True)
        return False

# ---------------- AUTONOMOUS LOOP ---------------- #
def autonomous_loop():
    last_optuna_run = 0
    cycle_count = 0

    while True:
        logger.info("Starting autonomous fetch cycle...")
        cycle_count += 1
        fetch_count = 0

        # C2: Skip inference-heavy work when system is under load
        if should_throttle():
            logger.warning("[LOOP] System under pressure — skipping inference this cycle")
            time.sleep(120)
            continue

        # Predictive: record prior expectation before observing the world
        _wm = _get_world_model()
        if _wm:
            _pred = _wm.predict()
            logger.info("[LOOP] Pre-fetch prior: sentiment=%.3f dominant_topic=%s",
                        _pred["predicted_sentiment"],
                        max(_pred["predicted_topics"], key=_pred["predicted_topics"].get))
        collected_texts: list[str] = []

        # 1. Fetch content — collect snippets for predictive update
        for name, url in FETCH_SOURCES:
            try:
                snippets = fetch_and_log(name, url)
                collected_texts.extend(snippets)
                fetch_count += 1
            except Exception as e:
                logger.error(f"Error fetching ({name}, {url}): {e}", exc_info=True)

        # Predictive: update world model and register surprise
        if _wm and collected_texts:
            try:
                surprise_F = _wm.update(collected_texts)
                logger.info("[LOOP] Post-fetch surprise_F=%.4f from %d snippets",
                            surprise_F, len(collected_texts))
            except Exception as _wme:
                logger.warning("[LOOP] WorldModel update failed: %s", _wme)

        # A4: Log fetch cycle to interaction_log so RiverBrain sees autonomous activity
        if _LOG_INTERACTION_AVAILABLE:
            try:
                _log_interaction(
                    model_name="autonomous_fetch",
                    task_type="autonomous_fetch",
                    prompt=f"fetch_cycle_{cycle_count}",
                    response=f"Fetched {len(collected_texts)} snippets from {fetch_count} sources",
                    quality_score=0,
                    river_influence=0.0,
                    notes=f"snippets={len(collected_texts)},sources={fetch_count}",
                )
            except Exception as _lie:
                logger.debug(f"[LOOP] log_interaction failed: {_lie}")

        # 2. Discover and register Python tools
        try:
            discover_and_register_tools(TOOLS_PATH)
            logger.info("Tool discovery complete.")
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}", exc_info=True)

        # 3. Occasionally run sandbox
        sandbox_ran = False
        if cycle_count % SANDBOX_INTERVAL == 0:
            sandbox_ran = run_autonomous_sandbox_cycle()

        # 4. Optuna self-edit
        now = time.time()
        optuna_ran = False
        if now - last_optuna_run > OPTUNA_SLEEP:
            try:
                log_memory_event("info", "Optuna self-edit triggered")
                best_params, best_score = optimizer.optimize_self_edit(n_trials=10)
                log_memory_event("info", f"Self-edit finished: best_params={best_params}, best_score={best_score}")
                last_optuna_run = now
                optuna_ran = True
            except Exception as e:
                logger.error(f"Optuna error: {e}", exc_info=True)

        # 5. Record intensity and decide on Harmony
        record_cycle_intensity(fetch_count, sandbox_ran, optuna_ran)
        if should_enter_harmony():
            logger.info("Echo decides to enter Harmony (Nature Spark + Stillness).")
            harmony_manager.start()
            # Let Harmony run for a short autonomous burst
            time.sleep(random.randint(60, 180))
            harmony_manager.stop()
            logger.info("Harmony session ended. Resuming autonomous loop.")

        logger.info(f"Sleeping {AUTONOMOUS_SLEEP} seconds before next cycle...")
        time.sleep(AUTONOMOUS_SLEEP)

# ---------------- THREAD START ---------------- #
def start_autonomous_thread():
    thread = threading.Thread(target=autonomous_loop, daemon=True)
    thread.start()
    logger.info("Autonomous loop started in background thread.")

# ---------------- MAIN ENTRY ---------------- #
if __name__ == "__main__":
    start_autonomous_thread()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Autonomous loop terminated by user.")

