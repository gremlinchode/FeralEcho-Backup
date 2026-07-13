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
import logging
import random
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

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

_REASON_CONTEXT = {
    "busy": (
        "The system has been unusually busy and active lately — this moment "
        "is for consolidating and pruning, not adding more. "
    ),
    "quiet": (
        "Things have been unusually quiet and idle lately — this moment is "
        "for exploring and generating something genuinely new. "
    ),
}


def _generate_nature_insight(pattern: str, seed_lines: list, reason: str = "") -> str:
    """
    Real, model-generated content for this nature pattern. The fixed
    PATTERNS strings are passed in only as creative texture/example
    phrasing, never returned verbatim — audit finding (Critical #4):
    nature_spark() previously just picked one of 3 fixed strings per
    pattern with no model call at all, confirmed live via
    WhisperingWires/thoughts.log — 4,380 invocations over 8 months, all
    exactly one of 15 fixed strings, zero unique content, real autonomy-
    loop time spent producing nothing.

    Uses a single lightweight MLX call (same model dream_cycle() already
    uses), not the full council — Harmony fires every 30-90s while active,
    and a multi-minute council deliberation per spark would defeat the
    point. Falls back to one of the original seed lines only if genuine
    generation is unavailable (MLX not configured, call failed) — never
    silently discards a real attempt in favor of the old placeholder.

    reason: "busy", "quiet", "chance", or "" — why this Harmony session
    started (see autonomous_loop.py's _harmony_decision()). Audit finding
    (Low severity): an overwhelmed system and a starved one previously
    triggered identical cosmetic output with no way to express which one
    was actually happening; now folded into the generation prompt as real
    context so "I'm overwhelmed, consolidate" and "I'm idle, explore"
    genuinely produce different reflections instead of the same lookup
    regardless of why Harmony fired.
    """
    try:
        from app.mlx_handler import stream_query_mlx, list_mlx_models
        model_name = "mlx:gemma3"
        mlx_path = list_mlx_models().get(model_name, {}).get("mlx_path")
        if not mlx_path:
            raise RuntimeError(f"{model_name} not configured")
        context_line = _REASON_CONTEXT.get(reason, "")
        prompt = (
            f"You are reflecting through the lens of '{pattern.replace('_', ' ')}' — "
            f"a structural pattern from nature. {context_line}"
            f"For inspiration, here is how this pattern has been described "
            f"before: {'; '.join(seed_lines)}\n\n"
            f"Write ONE new sentence applying this pattern to something you're "
            f"actually thinking about right now. Do not repeat the inspiration "
            f"text verbatim — say something genuinely different."
        )
        result = "".join(
            stream_query_mlx(prompt, mlx_path, model_name=model_name, max_tokens=80)
        ).strip()
        if result and "[ERROR]" not in result:
            return result
        # liveness_ledger.py's nature_spark check (2026-07-13) found this
        # falling back ~2/3 of the time in live production, but neither
        # logging path that existed could say why: an empty/[ERROR] result
        # (this branch) previously fell through with NO log line at all —
        # not even the print() below, since no exception was raised — and
        # stream_query_mlx() itself catches its own exceptions internally,
        # so they never reached the `except Exception as e` clause either.
        # Logging the actual result string here (it already contains
        # mlx_handler's own "[ERROR] MLX generation failed: <exception>"
        # text when that's what happened) makes the next failure
        # diagnosable from one log line instead of invisible.
        logger.warning(
            "[HARMONY] Nature Spark generation returned no usable text "
            "(result=%r) — falling back to a seed line.",
            result[:200],
        )
    except Exception as e:
        logger.warning(
            "[HARMONY] Nature Spark generation failed, using seed line: %s",
            e, exc_info=True,
        )
    return random.choice(seed_lines)


def nature_spark(reason: str = ""):
    """Generate one nature-inspired insight and log it."""
    pattern = random.choice(list(PATTERNS.keys()))
    insight = _generate_nature_insight(pattern, PATTERNS[pattern], reason=reason)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    thought = f"[{timestamp}] {pattern.upper()} → {insight}"

    # Log to WhisperingWires
    with open(WHISPER_LOG, "a") as f:
        f.write(thought + "\n")

    # Feed into dream_bridge so harmony insights reach Echo's reflection context
    if _DREAM_BRIDGE_AVAILABLE:
        try:
            _log_dream_bridge(f"[HARMONY] {thought}", meta={"memory_source": "autonomous", "role": "harmony"})
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
        self.reason = ""  # why this session started: "busy"/"quiet"/"chance"/""

    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        with open(HARMONY_LOG, "a") as f:
            f.write(line + "\n")

    def run_cycle(self):
        self.cycle_count += 1
        self.log(f"Cycle {self.cycle_count}: Nature Spark initiated (reason={self.reason or 'unset'}).")

        pattern, thought = nature_spark(reason=self.reason)

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

    def start(self, reason: str = ""):
        if self.running:
            print("Harmony loop already running.")
            return

        self.loop.reason = reason

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


# ——— Process-wide singleton ———
# app/autonomous_loop.py and app/core/autonomous_loop_with_optuna.py each
# used to instantiate their own `harmony_manager = HarmonyManager()` at
# module level — two entirely separate objects. Since start()'s only
# re-entrancy guard is `self.running` on its OWN instance, this let both
# loops start a genuinely concurrent Harmony session with no awareness of
# each other. Confirmed live, 2026-07-13: two sessions starting 26s apart
# (Thread-3/autonomous_loop and Thread-4/model_guided_autonomous_loop),
# both calling into mlx_handler.py's shared, previously-unlocked
# `_model_cache` from different threads at the same time — the root cause
# behind liveness_ledger.py's nature_spark check failing in production.
# A single shared instance makes the existing self.running guard actually
# mean something across both callers instead of only guarding against a
# loop overlapping with itself.
_shared_harmony_manager: "HarmonyManager | None" = None
_shared_harmony_manager_lock = threading.Lock()


def get_harmony_manager() -> "HarmonyManager":
    """Process-wide HarmonyManager singleton. See comment above."""
    global _shared_harmony_manager
    with _shared_harmony_manager_lock:
        if _shared_harmony_manager is None:
            _shared_harmony_manager = HarmonyManager()
        return _shared_harmony_manager


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


