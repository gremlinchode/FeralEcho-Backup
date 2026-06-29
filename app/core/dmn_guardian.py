#!/usr/bin/env python3
"""
dmn_guardian.py
================
DMN v4.1 Guardian Spine + Real-World Adaptive Regulator for FeralEcho
Full observability, safety backbone, dynamic energy equilibrium system,
autonomous efficiency experimentation, and hardware optimization zones.

Changes from v4.1:
  - cpu_tuning: fixed Windows-only psutil constants; macOS/Linux now uses os.nice()
  - assess_sandbox_risk: labeled as stub in logs so Echo doesn't treat random score as signal
  - history pruning: capped at 100 entries to prevent unbounded memory growth
  - observe_performance: added threading.Lock around tracemalloc to prevent thread interference
  - guardian_loop exception handler: now logs full traceback at DEBUG level (traceback was imported but unused)
"""

import importlib
import json
import logging
import os
import platform
import subprocess
import time
import functools
import tracemalloc
import traceback
import threading
import random
import psutil

# Optional dependency: networkx (used if EchoCore exposes a graph)
try:
    import networkx as nx
except ImportError:
    nx = None

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
EXPERIMENTAL_ZONES = set()
SANDBOX_RISK_LEVELS = {}

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
# Observant Decorators
# ------------------------

# FIX 4: Lock to prevent tracemalloc thread interference in a heavily-threaded environment
_tracemalloc_lock = threading.Lock()

def observe_performance(func):
    """Measure execution time and memory usage."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        with _tracemalloc_lock:
            tracemalloc.start()
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        end_time = time.perf_counter()

        perf_data = {
            "function": func.__name__,
            "execution_time_sec": round(end_time - start_time, 6),
            "memory_current_bytes": current,
            "memory_peak_bytes": peak
        }
        guardian_log("observant_performance", perf_data)
        return result
    return wrapper

def mark_experimental(func):
    """Mark function safe for Echo to self-edit."""
    EXPERIMENTAL_ZONES.add(func.__name__)
    guardian_log("observant_experimental_zone", {"function": func.__name__})
    return func

# ------------------------
# Sandbox Risk Assessment
# ------------------------
def assess_sandbox_risk(script_name: str):
    # FIX 2: Label as stub so Echo doesn't treat a random number as real signal.
    # TODO: wire to actual script content analysis (AST inspection, keyword scoring, etc.)
    score = random.random()
    SANDBOX_RISK_LEVELS[script_name] = score
    guardian_log("sandbox_risk_assessment", {
        "script": script_name,
        "risk_score": score,
        "note": "stub — score is random, not content-aware"
    })
    return score

# ------------------------
# Real-World Adaptive Regulator
# ------------------------
class RealWorldAdaptiveRegulator:
    """
    Maps target dimension to a measurable efficiency metric (useful operations / energy spent)
    and allows controlled autonomous experimentation with CPU, memory, and network tuning.
    """

    def __init__(self, target=1.58, energy_budget=120.0, energy_decay=0.995, adaptive_rate=0.002):
        self.target_dimension = target
        self.energy_budget = energy_budget
        self.energy_decay = energy_decay
        self.adaptive_rate = adaptive_rate
        self.history = []
        self.allowed_range = (1.55, 1.60)  # Safe exploration bounds
        self.learning_rate = 0.001
        self.experimental_zones = ["cpu_tuning", "memory_tuning", "network_tuning"]

    # ------------------------
    # Efficiency Metrics
    # ------------------------
    def measure_efficiency(self, echo_core=None):
        """Compute a real-world efficiency metric: useful operations per energy unit."""
        if not echo_core:
            return 1.0
        try:
            ops = getattr(echo_core, "operations_completed", 1)
            energy = getattr(echo_core, "energy_used", 1.0)
            return round(ops / (energy + 1e-6), 3)
        except Exception:
            return 1.0

    # ------------------------
    # Experimental Zone Adjustments
    # ------------------------
    @mark_experimental
    def cpu_tuning(self):
        """Adjust process priority to optimize CPU efficiency.
        
        FIX 1: psutil.NORMAL_PRIORITY_CLASS / IDLE_PRIORITY_CLASS / BELOW_NORMAL_PRIORITY_CLASS
        are Windows-only constants and raise AttributeError on macOS/Linux.
        macOS/Linux use Unix nice values (0=normal, 10=lower, 19=lowest priority).
        """
        try:
            p = psutil.Process()
            if platform.system() == 'Windows':
                p.nice(random.choice([
                    psutil.NORMAL_PRIORITY_CLASS,
                    psutil.IDLE_PRIORITY_CLASS,
                    psutil.BELOW_NORMAL_PRIORITY_CLASS
                ]))
            else:
                # macOS / Linux: nice 0=normal, higher=lower priority
                p.nice(random.choice([0, 10, 15]))
            guardian_log("cpu_tuning", {"priority_set": p.nice(), "platform": platform.system()})
        except Exception as e:
            guardian_log("cpu_tuning_error", {"error": str(e)})

    @mark_experimental
    def memory_tuning(self):
        """Simulate memory management adjustments."""
        adjustment = random.uniform(0.9, 1.1)
        guardian_log("memory_tuning", {"adjustment_factor": adjustment})
        return adjustment

    @mark_experimental
    def network_tuning(self):
        """Adjust network thread allocation or bandwidth usage."""
        adjustment = random.randint(1, 4)  # number of threads to dedicate
        guardian_log("network_tuning", {"threads_allocated": adjustment})
        return adjustment

    # ------------------------
    # Adaptive Feedback
    # ------------------------
    def propose_adjustment(self, current_efficiency):
        """Echo proposes a small autonomous adjustment toward optimal efficiency."""
        error = self.target_dimension - current_efficiency
        adjustment = self.learning_rate * error
        new_target = self.target_dimension + adjustment
        # Clamp to safe bounds
        return max(self.allowed_range[0], min(self.allowed_range[1], new_target))

    def run_cycle(self, echo_core=None):
        """Run a self-correcting, efficiency-based cycle with experimental zones."""
        if self.energy_budget <= 0:
            guardian_log("energy_pause", {"reason": "budget depleted"})
            return

        current_eff = self.measure_efficiency(echo_core)
        deviation = current_eff - self.target_dimension
        energy_cost = abs(deviation) * 10

        if energy_cost > self.energy_budget:
            guardian_log("energy_limit_reached", {"deviation": deviation})
            return

        self.energy_budget -= energy_cost
        self.energy_budget *= self.energy_decay

        # Autonomous adjustment
        self.target_dimension = self.propose_adjustment(current_eff)

        # Run experimental zones probabilistically
        for zone in self.experimental_zones:
            if random.random() < 0.3:  # 30% chance per cycle
                getattr(self, zone)()

        self.history.append({
            "measured_efficiency": current_eff,
            "target_dimension": self.target_dimension,
            "energy_remaining": self.energy_budget,
            "timestamp": time.time()
        })

        # FIX 3: Prune history to prevent unbounded memory growth.
        # At 120s interval this is ~3.3 hours of history — enough for meaningful pattern detection.
        if len(self.history) > 100:
            self.history = self.history[-100:]

        guardian_log("adaptive_cycle", {
            "measured_efficiency": current_eff,
            "target": self.target_dimension,
            "energy": round(self.energy_budget, 3)
        })

    def regenerate(self):
        """Periodic slow energy restoration."""
        self.energy_budget = min(self.energy_budget * 1.03 + 5, 150.0)
        guardian_log("energy_regen", {"new_energy": self.energy_budget})

# ------------------------
# Guardian Continuous Loop
# ------------------------
def start_guardian_loop(echo_core=None, interval=120):
    """Main Guardian thread: system checks + real-world adaptive homeostasis."""
    regulator = RealWorldAdaptiveRegulator()

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
        logging.info("[GUARDIAN] Starting real-world adaptive Guardian loop...")
        while True:
            try:
                integrity = verify_integrity()
                pipelines = verify_pipelines()
                regulator.run_cycle(echo_core)
                regulator.regenerate()

                # A3: Ollama actuation — restart if process not detected
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

                guardian_log("heartbeat", {
                    "integrity": integrity,
                    "pipelines": pipelines,
                    "target_dimension": regulator.target_dimension,
                    "energy": regulator.energy_budget,
                    "experimental_zones": list(EXPERIMENTAL_ZONES)
                })

            except Exception as e:
                # FIX 5: Log full traceback at DEBUG so real failures leave a trail.
                # traceback was imported at the top but never used — now it is.
                logging.warning(f"[GUARDIAN] Loop error: {e}")
                logging.debug(traceback.format_exc())

            time.sleep(interval)

    t = threading.Thread(target=guardian_loop, daemon=True)
    t.start()
    logging.info("[GUARDIAN] Continuous real-world adaptive loop initialized.")
    return regulator

# ------------------------
# Startup Confirmation
# ------------------------
def confirm_guardian_startup():
    logging.info("[GUARDIAN] DMN Guardian v4.1 active with real-world adaptive regulator and experimental zones.")
