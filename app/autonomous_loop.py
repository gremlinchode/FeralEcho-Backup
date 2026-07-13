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
from concurrent.futures import ThreadPoolExecutor, as_completed

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
from app.internet_tools.autonomous_fetch import _fetch_hackernews
from app.core.temporal_environment import get_temporal_environment_context

try:
    from app.internet_tools.claude_research import fetch_claude_research
    _CLAUDE_RESEARCH_AVAILABLE = True
except Exception as _cr_import_err:
    _CLAUDE_RESEARCH_AVAILABLE = False
    logging.warning(f"[LOOP] Claude research unavailable: {_cr_import_err}")

try:
    from app.core.predictive_loop import get_world_model as _get_world_model
except Exception:
    _get_world_model = lambda: None

try:
    from app.core.echo_model_orchestrator import log_interaction as _log_interaction
    _LOG_INTERACTION_AVAILABLE = True
except Exception:
    _LOG_INTERACTION_AVAILABLE = False

from app.core.awareness_tools_integration import discover_and_register_tools
from sandbox.run_script import run_sandbox_script_isolated as run_sandbox_script
from app.core.memory_bridge import log_dream_bridge
from app.core.stillness_state import wait_for_activity
from app.autonomous_harmony_manager import HarmonyManager

# ---------------- CONFIG ---------------- #
AUTONOMOUS_SLEEP = 3600
SANDBOX_INTERVAL = 3
TOOLS_PATH = os.path.join(os.getcwd(), "app", "tools")

logger = logging.getLogger(__name__)

# Bounds for surprise-modulated sleep — see _compute_next_sleep below.
_SLEEP_MODULATION_MIN: float = 0.5
_SLEEP_MODULATION_MAX: float = 1.5


def _compute_next_sleep(wm, base_sleep: int) -> int:
    """
    Modulate the next cycle's sleep by how surprising the world model found
    what it just observed, relative to its own recent baseline — audit
    finding: WorldModel.update() computes a real KL-divergence surprise_F
    every cycle, but nothing downstream ever consumed it; every loop
    cadence in this codebase was a flat constant regardless. More surprising
    than the recent baseline (ratio > 1) shortens the wait, so a genuinely
    novel stretch of content gets followed up on sooner; less surprising
    lengthens it. Bounded to [0.5x, 1.5x] of base_sleep so this can never
    produce a runaway fast-loop or an excessively long silent gap — a
    modulation, not a replacement, of the fixed interval.
    """
    if wm is None:
        return base_sleep
    try:
        last, r10, r50 = wm.get_surprise()
    except Exception:
        return base_sleep
    baseline = r50 if r50 > 1e-6 else (r10 if r10 > 1e-6 else 0.0)
    if baseline <= 1e-6:
        return base_sleep
    ratio = last / baseline
    multiplier = max(_SLEEP_MODULATION_MIN, min(_SLEEP_MODULATION_MAX, 1.0 / ratio))
    return int(base_sleep * multiplier)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

harmony_manager = HarmonyManager()

# ---------------- CYCLE HISTORY ---------------- #
# Audit finding: this was purely in-memory — a restart silently discarded
# whatever "momentum" had accumulated, with should_enter_harmony() starting
# blind again every time (mirrors the same pattern already fixed for the
# self-edit cooldown and, this pass, drift detectors/terminal session).
# Only 5 small floats, so persisting on every update is cheap.
_MOMENTUM_STATE_PATH = "memory/autonomous_loop_momentum.json"


def _load_recent_cycles() -> deque:
    try:
        import json
        with open(_MOMENTUM_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return deque(data.get("recent_cycles", []), maxlen=5)
    except Exception:
        return deque(maxlen=5)


def _save_recent_cycles() -> None:
    try:
        import json
        os.makedirs(os.path.dirname(_MOMENTUM_STATE_PATH), exist_ok=True)
        tmp = _MOMENTUM_STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"recent_cycles": list(RECENT_CYCLES)}, f)
        os.replace(tmp, _MOMENTUM_STATE_PATH)
    except Exception:
        pass


RECENT_CYCLES = _load_recent_cycles()  # store last 5 cycles' intensity scores

def record_cycle_intensity(fetch_count, sandbox_ran, optuna_ran):
    """Compute a simple intensity score for this cycle."""
    score = fetch_count + (2 if sandbox_ran else 0) + (3 if optuna_ran else 0)
    RECENT_CYCLES.append(score)
    _save_recent_cycles()
    return score

def _harmony_decision() -> tuple:
    """Returns (should_enter, reason) — reason is "busy", "quiet", or
    "chance". Split out from should_enter_harmony() (which stays a thin
    wrapper, unchanged signature/behavior for any other caller) so the
    actual trigger reason can be threaded into HarmonyManager.start() —
    audit finding: an overwhelmed system and a starved one previously
    triggered identical cosmetic output with no way to express which one
    was actually happening."""
    if not RECENT_CYCLES:
        return False, ""
    avg_intensity = sum(RECENT_CYCLES) / len(RECENT_CYCLES)
    # Trigger if recent cycles are very busy or unusually quiet
    if avg_intensity >= 5:
        return True, "busy"
    if avg_intensity <= 1:
        return True, "quiet"
    # Small random chance otherwise
    if random.random() < 0.1:
        return True, "chance"
    return False, ""


def should_enter_harmony():
    """Decide autonomously if Harmony should run."""
    return _harmony_decision()[0]

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
        script_path = os.path.join("sandbox", "scripts", script_to_run)
        logger.info(f"[SANDBOX] Running baseline: {script_to_run}")
        result = run_sandbox_script(script_path, timeout=600)
        output = result.get("output") or result.get("error")
        if result["success"]:
            logger.info(f"[SANDBOX RESULT] {output}")
        else:
            logger.warning(f"[SANDBOX ERROR] {output}")
            # Only write failures to dream_bridge — baseline success
            # ("Computation result = 285") has no semantic retrieval value
            # and was writing a low-signal FAISS entry on every run.
            log_dream_bridge(f"[SandboxFailure] {script_to_run} | {output}",
                             meta={"memory_source": "autonomous", "role": "sandbox_failure"})
        return True
    except Exception as e:
        logger.error(f"[SANDBOX] Error: {e}", exc_info=True)
        return False

# ---------------- AUTONOMOUS LOOP ---------------- #
def autonomous_loop():
    cycle_count = 0

    while True:
        # Pause during stillness — block here until Echo returns to activity.
        wait_for_activity()

        logger.info("Starting autonomous fetch cycle...")
        cycle_count += 1
        fetch_count = 0

        # C2: Skip inference-heavy work when system is under load — shared gate (autonomy_coordinator)
        from app.core.autonomy_coordinator import should_run_cycle
        if not should_run_cycle("autonomous_loop"):
            logger.warning("[LOOP] System under pressure or in stillness — skipping inference this cycle")
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
        # FIX #3: build temporal context once per cycle, reuse across all sources
        try:
            _cycle_ctx = get_temporal_environment_context(
                weather_api_key=os.environ.get("OPENWEATHER_API_KEY")
            )
        except Exception as _ctx_err:
            logger.warning(f"[LOOP] Temporal context failed: {_ctx_err}")
            _cycle_ctx = None

        # FIX #4: parallel fetching — 3 concurrent workers, capped to avoid
        # hammering sources or overwhelming FAISS with concurrent writes
        def _fetch_one(args):
            n, u = args
            return n, fetch_and_log(n, u, temporal_context=_cycle_ctx)

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(_fetch_one, (name, url)): name for name, url in FETCH_SOURCES}
            for future in as_completed(futures):
                try:
                    src_name, snippets = future.result()
                    collected_texts.extend(snippets)
                    fetch_count += 1
                except Exception as e:
                    logger.error(f"Error fetching {futures[future]}: {e}", exc_info=True)

        # Hacker News (two-step fetch, runs after parallel pool closes)
        try:
            hn_snippets = _fetch_hackernews(temporal_context=_cycle_ctx)
            collected_texts.extend(hn_snippets)
            if hn_snippets:
                fetch_count += 1
        except Exception as e:
            logger.error(f"[LOOP] Hacker News fetch failed: {e}", exc_info=True)

        # Claude research synthesis — rate-limited internally to 1/hour
        if _CLAUDE_RESEARCH_AVAILABLE:
            try:
                research = fetch_claude_research()
                if research:
                    log_dream_bridge(research, meta={"memory_source": "claude_research", "role": "research"})
                    collected_texts.append(research)
                    logger.info("[LOOP] Claude research synthesized and stored.")
            except Exception as e:
                logger.warning(f"[LOOP] Claude research failed: {e}")

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

        # 4. Optuna self-edit — removed (Finding B). This ran its own EchoOptuna()
        # instance against the same sqlite:///memory/optuna.db study that
        # run.py's self_edit_loop uses, on an independent ~2hr timer, but never
        # deployed a result via perform_self_edit(). run.py's loop is the single
        # authoritative self-edit path; this was redundant trial computation
        # sharing storage with it. optuna_ran kept (always False) — only feeds
        # the cosmetic Harmony intensity score below.
        optuna_ran = False

        # 5. Record intensity and decide on Harmony
        # Unlike every other step in this loop, this section had no try/
        # except at all — an uncaught exception here (or from time.sleep
        # itself being interrupted in a way that re-raises) would propagate
        # out of the `while True:` and permanently kill this daemon thread,
        # with no supervisor to restart it and no visible symptom beyond
        # certain log lines quietly stopping.
        try:
            record_cycle_intensity(fetch_count, sandbox_ran, optuna_ran)
            enter_harmony, harmony_reason = _harmony_decision()
            if enter_harmony:
                logger.info(f"Echo decides to enter Harmony (reason={harmony_reason}).")
                harmony_manager.start(reason=harmony_reason)
                # Let Harmony run for a short autonomous burst
                time.sleep(random.randint(60, 180))
                harmony_manager.stop()
                logger.info("Harmony session ended. Resuming autonomous loop.")
        except Exception as _harmony_err:
            logger.error(f"[LOOP] Harmony/intensity step failed: {_harmony_err}", exc_info=True)

        _next_sleep = _compute_next_sleep(_wm, AUTONOMOUS_SLEEP)
        logger.info(
            f"Sleeping {_next_sleep} seconds before next cycle "
            f"(base={AUTONOMOUS_SLEEP}, surprise-modulated)..."
        )
        time.sleep(_next_sleep)

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

