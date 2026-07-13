#!/usr/bin/env python3
"""
dmn_guardian.py
================
DMN v4.1 Guardian Spine for FeralEcho.
Startup module-import check, Ollama process watchdog, snapshot alert dispatch,
and crash-sentinel heartbeat. Adaptive regulator and experimental-zone
infrastructure removed 2026-07-01 (phantom metrics, no live readers).
"""

import importlib
import json
import logging
import os
import subprocess
import time
import traceback
import threading

# ------------------------
# Setup Logging
# ------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ------------------------
# Critical Modules Monitored
# ------------------------
CRITICAL_MODULES = [
    "app.core.self_edit_manager",
    "app.emergent_scheduler",
    "app.internet_tools.autonomous_fetch",
    "app.core.memory_bridge"
]

# ------------------------
# Observability and Logging
# ------------------------
def guardian_log(event_type, details):
    """Structured Guardian logging."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_entry = {
        "timestamp": timestamp,
        "event": event_type,
        "details": details
    }
    logging.info(f"[GUARDIAN] {event_type} | {details}")
    return log_entry

# ------------------------
# Integrity & Pipeline Checks
# ------------------------
def verify_integrity():
    results = {}
    for module in CRITICAL_MODULES:
        try:
            importlib.import_module(module)
            results[module] = True
        except Exception as e:
            logging.error(f"[GUARDIAN] Integrity check failed for {module}: {e}")
            results[module] = False
    return results

def verify_pipelines():
    pipelines = ["self_edit_manager", "memory_bridge", "autonomous_fetch"]
    status = {}
    for p in pipelines:
        try:
            importlib.import_module(
                f"app.core.{p}" if p != "autonomous_fetch" else f"app.internet_tools.{p}"
            )
            status[p] = True
        except Exception as e:
            logging.error(f"[GUARDIAN] Pipeline check failed for {p}: {e}")
            status[p] = False
    return status

# ------------------------
# Guardian Continuous Loop
# ------------------------
def start_guardian_loop(echo_core=None, interval=120):
    """Main Guardian thread: startup module check + Ollama watchdog + snapshot alerts + sentinel heartbeat."""

    # One-time import check before the thread starts — module importability doesn't
    # change at runtime, so polling it every cycle was noise.
    _integrity = verify_integrity()
    _pipelines = verify_pipelines()
    _failed = [m for m, ok in {**_integrity, **_pipelines}.items() if not ok]
    if _failed:
        logging.warning("[GUARDIAN] Startup import check FAILED for: %s", _failed)
    else:
        logging.info("[GUARDIAN] Startup import check passed for all critical modules.")

    _ollama_last_restart: dict = {"ts": 0.0}
    _OLLAMA_RESTART_COOLDOWN = 120.0
    _INTROSPECTION_PATH = os.path.join("memory", "introspection_state.json")

    def _check_ollama_alive() -> bool:
        """Read introspection_state.json to check if Ollama process was seen."""
        try:
            with open(_INTROSPECTION_PATH, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            return bool(state.get("ollama_process_alive", True))
        except Exception:
            return True  # Can't read = assume alive, avoid false restarts

    def guardian_loop():
        logging.info("[GUARDIAN] Starting Guardian loop...")
        while True:
            try:
                # Ollama actuation — restart if process not detected
                if not _check_ollama_alive():
                    now = time.time()
                    if now - _ollama_last_restart["ts"] > _OLLAMA_RESTART_COOLDOWN:
                        logging.critical("[GUARDIAN] Ollama process not detected — attempting restart")
                        try:
                            subprocess.Popen(
                                ["ollama", "serve"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            _ollama_last_restart["ts"] = now
                            logging.info("[GUARDIAN] ollama serve launched")
                        except Exception as _oe:
                            logging.error(f"[GUARDIAN] Failed to restart Ollama: {_oe}")
                    else:
                        logging.warning("[GUARDIAN] Ollama down but restart cooldown active")

                # Health-threshold alert check (ground-truth signals only)
                try:
                    from app.core.snapshot_manager import check_and_alert
                    check_and_alert(guardian_interval_s=interval)
                except Exception as _sae:
                    logging.debug("[GUARDIAN] snapshot check_and_alert error: %s", _sae)

                # Self-edit outcome evaluation (Finding 8) — log-only, does not
                # feed dim[6] or self-edit targeting. Cheap no-op unless a
                # pending outcome's window has actually closed.
                try:
                    from app.core.self_edit_outcome_tracker import evaluate_pending_outcomes
                    evaluate_pending_outcomes()
                except Exception as _oee:
                    logging.debug("[GUARDIAN] self-edit outcome evaluation error: %s", _oee)

                # Self-report verification — log-only, does not correct
                # self_model.json or feed any decision path. Same restraint
                # as the self-edit outcome tracker above.
                try:
                    from app.core.self_report_verifier import verify_memory_health
                    verify_memory_health()
                except Exception as _srve:
                    logging.debug("[GUARDIAN] self-report verification error: %s", _srve)

                # Crash sentinel heartbeat — keeps last_heartbeat_utc current
                try:
                    import json as _json_s
                    from pathlib import Path as _Path_s
                    _sp = _Path_s("memory/echo_sentinel.json")
                    if _sp.exists():
                        _sd = _json_s.loads(_sp.read_text())
                        from datetime import datetime as _dt_s
                        _sd["last_heartbeat_utc"] = _dt_s.utcnow().isoformat() + "Z"
                        _start = _sd.get("start_utc", "")
                        if _start:
                            try:
                                _sd["uptime_s"] = round((_dt_s.utcnow() - _dt_s.fromisoformat(_start.rstrip("Z"))).total_seconds())
                            except Exception:
                                pass
                        _tmp = _sp.with_suffix(".tmp")
                        _tmp.write_text(_json_s.dumps(_sd, indent=2))
                        _tmp.replace(_sp)
                except Exception as _hbe:
                    logging.debug("[SENTINEL] heartbeat write failed: %s", _hbe)

                guardian_log("heartbeat", {})

            except Exception as e:
                logging.warning(f"[GUARDIAN] Loop error: {e}")
                logging.debug(traceback.format_exc())

            time.sleep(interval)

    t = threading.Thread(target=guardian_loop, daemon=True)
    t.start()
    logging.info("[GUARDIAN] Guardian loop initialized.")

# ------------------------
# Startup Confirmation
# ------------------------
def confirm_guardian_startup():
    logging.info("[GUARDIAN] DMN Guardian v4.1 active.")
