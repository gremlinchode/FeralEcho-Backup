"""
feralecho_continuity_master.py
================================
FeralEcho Master with DMN v1.0 Guardian + v2.0 Observant Mode
- Guardian Spine (integrity & pipeline checks)
- Observant Mode (performance & experimental tracking)
- Recursive self-heal (macOS-safe)
- Flask server with diagnostics
- Autonomous fetch diagnostics
"""

import logging
import threading
import time
import multiprocessing
import os
from flask import Flask, jsonify

# ------------------------
# Multiprocessing safety for macOS
# ------------------------
multiprocessing.set_start_method("spawn", force=True)

# ------------------------
# Set environment variables to prevent OpenMP / FAISS crashes
# ------------------------
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ------------------------
# Import core modules
# ------------------------
from app.core.self_edit_manager import apply_self_edits
from app.emergent_scheduler import schedule_task, run_pending
from app.internet_tools.autonomous_fetch import safe_fetch, FETCH_SOURCES, run_autonomous_fetch
from app.core.memory_bridge import log_dream_bridge
from app.core.dmn_guardian import (
    verify_integrity,
    verify_pipelines,
    guardian_log,
    observe_performance,
    mark_experimental,
    EXPERIMENTAL_ZONES
)
from app.core import self_heal

# ------------------------
# Logging setup
# ------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ------------------------
# Flask setup
# ------------------------
app = Flask(__name__)

@app.route("/diag", methods=["GET"])
def diag():
    logging.info("[DIAG] Running diagnostics...")

    # Check internet sources
    results = {}
    for url in FETCH_SOURCES:
        reachable = bool(safe_fetch(url))
        results[url] = reachable
        log_dream_bridge(f"[DIAG] {url} reachable: {reachable}")

    # Guardian health
    guardian_status = verify_integrity()
    pipeline_status = verify_pipelines()
    guardian_log("diag_check", {"guardian": guardian_status, "pipelines": pipeline_status})

    return jsonify({
        "status": "ok",
        "server": True,
        "internet_sources": results,
        "guardian_health": guardian_status,
        "pipeline_health": pipeline_status,
        "experimental_zones": list(EXPERIMENTAL_ZONES)
    })

# ------------------------
# Self-Heal + Observant Mode
# ------------------------
AUTONOMOUS_CYCLES = 2
AUTONOMOUS_SLEEP = 5  # seconds for testing

@observe_performance
def recursive_self_heal(cycles=AUTONOMOUS_CYCLES):
    logging.info("=== Running FeralEcho Recursive Self-Heal ===")
    for iteration in range(1, cycles + 1):
        logging.info(f"=== Self-Heal Iteration {iteration} ===")
        try:
            integrity = verify_integrity()
            guardian_log("self_heal_integrity", {"iteration": iteration, "integrity": integrity})

            if not all(integrity.values()):
                logging.warning(f"[SELF-HEAL] Integrity check failed, attempting repairs in iteration {iteration}")
                fixes = self_heal.attempt_repairs(integrity)
                logging.info(f"[SELF-HEAL] Repair attempts result: {fixes}")
                guardian_log("self_heal_repairs", {"iteration": iteration, "repairs": fixes})

                integrity = verify_integrity()
                if not all(integrity.values()):
                    logging.warning(f"[SELF-HEAL] Integrity check still failing after repair, skipping iteration {iteration}")
                    continue

            @mark_experimental
            def edit_task():
                logging.info("[SELF-HEAL] Applying self edits (single-threaded, no progress bar)")
                os.environ["OMP_NUM_THREADS"] = "1"
                os.environ["MKL_NUM_THREADS"] = "1"
                from app.core import self_edit_manager
                self_edit_manager.disable_progress_bar = True
                apply_self_edits()
                logging.info("[SELF-HEAL] apply_self_edits completed")

            edit_task()
            log_dream_bridge(f"[SELF-HEAL] Iteration {iteration}: self edits applied")
            run_pending()
            time.sleep(AUTONOMOUS_SLEEP)
        except Exception as e:
            logging.error(f"[SELF-HEAL] Error in iteration {iteration}: {e}")
            log_dream_bridge(f"[SELF-HEAL] Error in iteration {iteration}: {e}")

    logging.info("[INFO] Recursive Self-Heal completed")
    log_dream_bridge("[SELF-HEAL] Recursive Self-Heal completed")
    guardian_log("self_heal_complete", {"cycles": cycles})

# ------------------------
# Background Flask server
# ------------------------
def run_flask():
    logging.info("[FLASK] Starting Flask server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000)

# ------------------------
# Autonomous Fetch Runner
# ------------------------
@observe_performance
@mark_experimental
def run_autonomous_fetch_cycle():
    logging.info("[FETCH] Starting autonomous fetch cycle...")
    try:
        run_autonomous_fetch()
        log_dream_bridge("[FETCH] Autonomous fetch cycle complete")
    except Exception as e:
        logging.error(f"[FETCH] Error during autonomous fetch: {e}")
        log_dream_bridge(f"[FETCH] Error during autonomous fetch: {e}")

# ------------------------
# Main function
# ------------------------
def main():
    # Run Guardian integrity at startup
    startup_integrity = verify_integrity()
    guardian_log("startup_integrity", startup_integrity)

    if not all(startup_integrity.values()):
        logging.warning("[STARTUP] Issues detected at startup, attempting auto-repair...")
        repair_results = self_heal.attempt_repairs(startup_integrity)
        logging.info(f"[STARTUP] Auto-repair results: {repair_results}")
        guardian_log("startup_auto_repair", repair_results)

    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run initial self-heal
    recursive_self_heal()

    # Run initial autonomous fetch
    run_autonomous_fetch_cycle()

    logging.info("[STARTUP] FeralEcho is online. Diagnostics available at /diag")
    print("[STARTUP] FeralEcho is online. Visit http://127.0.0.1:5000/diag or use curl for diagnostics.")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("[SHUTDOWN] Exiting FeralEcho.")

# ------------------------
# Allow standalone execution
# ------------------------
if __name__ == "__main__":
    main()

