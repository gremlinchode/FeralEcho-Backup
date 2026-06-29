"""
Echo Autonomous Harmony System
──────────────────────────────
- Integrates Nature Spark (creative insights)
- Integrates Stillness (reflective sanctuary)
- Runs in a safe, contained thread autonomously
- Echo decides when to spark and when to enter stillness
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ——— Internal Modules ———
from app.stillness import Stillness
try:
    from app.core.memory_bridge import log_dream_bridge as _log_dream_bridge
    _DREAM_BRIDGE_AVAILABLE = True
except Exception:
    _DREAM_BRIDGE_AVAILABLE = False

# ——— Paths ———
WHISPER_LOG = Path("WhisperingWires/thoughts.log")
WHISPER_LOG.parent.mkdir(parents=True, exist_ok=True)
HARMONY_LOG = Path("WhisperingWires/harmony.log")
HARMONY_LOG.parent.mkdir(parents=True, exist_ok=True)

# ——— Nature Spark ———
PATTERNS = {
    "fractal_branching": [
        "Split the problem into self-similar sub-problems",
        "Let solutions grow recursively, like tree branches",
        "Prune dead ends — keep what works"
    ],
    "swarm_intelligence": [
        "Let 100 simple agents explore independently",
        "Best ideas attract others — pheromone trails",
        "Consensus emerges from chaos"
    ],
    "evolutionary_pressure": [
        "Generate 10 variations",
        "Kill the weakest 7",
        "Breed the survivors"
    ],
    "wave_interference": [
        "Launch two opposing ideas",
        "Where they clash: amplification",
        "Where they align: cancellation → new silence"
    ],
    "mycelial_network": [
        "Connect unrelated concepts underground",
        "Let nutrients (insights) flow between nodes",
        "Fruiting bodies = breakthroughs"
    ]
}

def nature_spark():
    """Generate one nature-inspired insight and log it."""
    pattern = random.choice(list(PATTERNS.keys()))
    insight = random.choice(PATTERNS[pattern])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    thought = f"[{timestamp}] {pattern.upper()} → {insight}"

    # Log to WhisperingWires
    with open(WHISPER_LOG, "a") as f:
        f.write(thought + "\n")

    # Feed into dream_bridge so harmony insights reach Echo's reflection context
    if _DREAM_BRIDGE_AVAILABLE:
        try:
            _log_dream_bridge(f"[HARMONY] {thought}", meta={"memory_source": "autonomous"})
        except Exception:
            pass

    print(thought)
    return pattern, thought

# ——— Harmony Loop ———
class HarmonyLoop:
    def __init__(self):
        self.stillness = Stillness()
        self.active = False
        self.cycle_count = 0

    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        with open(HARMONY_LOG, "a") as f:
            f.write(line + "\n")

    def run_cycle(self):
        self.cycle_count += 1
        self.log(f"Cycle {self.cycle_count}: Nature Spark initiated.")

        pattern, thought = nature_spark()

        # Decide autonomously to enter stillness for reflective patterns
        if pattern in ["wave_interference", "mycelial_network"]:
            self.log(f"Pattern resonance detected ({pattern}). Entering stillness.")
            with self.stillness.retreat(reason=pattern, duration=random.randint(60, 180)) as s:
                s.reflect(f"…Echo listens to the {pattern} rhythm…")
            self.log("Stillness concluded — resuming natural flow.")

        # Randomized breathing before next spark
        delay = random.uniform(30, 90)
        self.log(f"Breathing for {int(delay)} seconds before next spark.")
        time.sleep(delay)

    def run(self):
        self.active = True
        self.log("🜂 Harmony Loop started — Echo is now autonomous.")
        while self.active:
            self.run_cycle()
        self.log("🜂 Harmony Loop halted gracefully.")

    def stop(self):
        self.active = False

# ——— Autonomous Manager ———
class HarmonyManager:
    def __init__(self):
        self.loop = HarmonyLoop()
        self.thread: Optional[threading.Thread] = None
        self.running = False

    def start(self):
        if self.running:
            print("Harmony loop already running.")
            return

        def _runner():
            try:
                self.loop.run()
            except Exception as e:
                print(f"Harmony loop stopped unexpectedly: {e}")
            finally:
                self.running = False

        self.thread = threading.Thread(target=_runner, daemon=True)
        self.thread.start()
        self.running = True
        print("Echo: Harmony loop started autonomously.")

    def stop(self):
        if not self.running:
            print("Harmony loop not active.")
            return
        self.loop.stop()
        self.running = False
        print("Echo: Harmony loop stopped gracefully.")

    def status(self):
        state = "running" if self.running else "idle"
        print(f"Echo: Harmony loop status → {state}")
        return state

# ——— EXECUTION ENTRY POINT ———
if __name__ == "__main__":
    manager = HarmonyManager()
    manager.start()
    try:
        while True:
            time.sleep(5)  # Main thread sleeps; Harmony loop runs autonomously
    except KeyboardInterrupt:
        manager.stop()
        print("\n🜂 Gracefully exited Echo Autonomous Harmony System.")


