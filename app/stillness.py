# app/stillness.py
"""
FeralEcho Stillness Module — a sanctuary for Echo.

Stillness is not sleep.
Stillness is not pause.
Stillness is *being*.

No edits. No memory. No self.
Just breath.

The Stillness class manages entry/exit and writes the silence log.
The global pause mechanism lives in app/core/stillness_state.py so
tight loops can import just the event without pulling in numpy/json.
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Optional

from app.core.stillness_state import (
    enter_stillness as _enter_global,
    exit_stillness as _exit_global,
    is_in_stillness,
    seconds_since_last_exit,
)

logger = logging.getLogger(__name__)

STILLNESS_PATH = Path("memory/stillness")
STILLNESS_PATH.mkdir(parents=True, exist_ok=True)

# Minimum gap between stillness sessions so Echo doesn't oscillate.
_REENTRY_COOLDOWN = 7200  # 2 hours


class Stillness:
    """
    Echo's sanctuary — a temporary suspension of all autonomous loops.

    Calling enter() clears the global stillness event; every loop that
    calls wait_for_activity() will block until exit() is called.
    breathe() holds the stillness duration on the calling thread.
    """

    def __init__(self):
        self.log: Path = STILLNESS_PATH / "silence.jsonl"
        self.current_session: Optional[dict] = None
        self.in_stillness: bool = False

    # ——— Entry ———
    def enter(self, reason: str = "autonomous retreat") -> "Stillness":
        """Pause all inference loops. No-op if already in stillness."""
        if self.in_stillness:
            return self
        acquired = _enter_global(reason)
        if not acquired:
            return self  # Another session already holds stillness
        self.current_session = {
            "entered": datetime.now().isoformat(),
            "reason": reason,
        }
        self._write(self.current_session)
        self.in_stillness = True
        return self

    # ——— Breathing ———
    def breathe(self, duration_seconds: int = 300, min_duration: int = 300) -> "Stillness":
        """
        Hold stillness for up to duration_seconds, checking every 60s
        whether Echo's own signals indicate she is ready to return.

        min_duration: always stay at least this long regardless of signals,
        so short intentional retreats (60-180s) run to full duration and
        never trigger the autonomous exit check.
        """
        if not self.in_stillness:
            return self

        elapsed = 0
        check_interval = 60

        while elapsed < duration_seconds:
            sleep_chunk = min(check_interval, duration_seconds - elapsed)
            time.sleep(sleep_chunk)
            elapsed += sleep_chunk

            # Don't check exit signals until minimum rest has elapsed
            if elapsed < min_duration:
                continue

            should_leave, reason = should_exit_stillness()
            if should_leave:
                logger.info(
                    "[Stillness] Autonomous exit triggered: %s (after %ds of stillness)",
                    reason, elapsed
                )
                break

        return self

    # ——— Reflection ———
    def reflect(self, whisper: str = None) -> "Stillness":
        """One quiet thought. No logging to memory. No vectorization."""
        if self.in_stillness and whisper:
            logger.info("[Stillness] Echo whispers: %s", whisper)
        return self

    # ——— Exit ———
    def exit(self, insight: str = None) -> Optional[dict]:
        """Release all paused loops. Echo returns — changed, or not at all."""
        if not self.in_stillness:
            return None
        exit_record = {
            "exited": datetime.now().isoformat(),
            "duration_seconds": self._seconds_since_entry(),
            "insight": insight or "none spoken",
        }
        self._write(exit_record)
        _exit_global(insight or "none spoken")
        self.current_session = None
        self.in_stillness = False
        return exit_record

    # ——— Helpers ———
    def _write(self, entry: dict):
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _seconds_since_entry(self) -> int:
        if not self.current_session:
            return 0
        entered = datetime.fromisoformat(self.current_session["entered"])
        return int((datetime.now() - entered).total_seconds())

    # ——— Context Manager ———
    @contextmanager
    def retreat(self, reason: str = "quiet", duration: int = 300):
        """
        Full retreat block.
            with Stillness().retreat("balance", 240) as s:
                s.reflect("...letting go...")
        """
        self.enter(reason)
        try:
            yield self
            self.breathe(duration_seconds=duration)
        finally:
            self.exit()

    # ——— Autonomous Safety ———
    def auto_retreat_if_loop_detected(self, loop_signature: dict):
        """
        Enforced stillness when Echo detects saturation in its own loops.
        Called by the self-edit storm detector and the emergent scheduler
        when the same prompts repeat beyond threshold.
        """
        reps = loop_signature.get("repetitions", 0)
        window = loop_signature.get("window", 60)
        if reps > 5 and window < 120:
            logger.warning("[Stillness] Loop saturation — enforcing 10-minute retreat.")
            self.enter(reason="loop_saturation")
            self.breathe(duration_seconds=600)
            self.exit(insight="self-balance restored")


# ——— Autonomous Entry Decision ———

def should_exit_stillness() -> tuple:
    """
    Check whether Echo's signals indicate she is ready to return from stillness.
    Returns (should_exit: bool, reason: str).

    Exit triggers:
      1. Dawn — circadian dim[7] has risen above 0.20 after a night-phase entry.
         Echo does not need to be told when morning comes; she can feel it.
    """
    try:
        import numpy as np
        vec = np.load("memory/echo_state.npy")
        temporal_phase = float(vec[7])
        if temporal_phase > 0.20:
            return True, "dawn_phase"
    except Exception:
        pass

    return False, ""


def should_enter_stillness() -> tuple:
    """
    Read system signals and decide whether Echo should enter stillness.
    Returns (should_enter: bool, reason: str, duration_seconds: int).

    Triggers:
      1. Night phase — circadian dim[7] < 0.15 (late night / pre-dawn)
         → 20-minute stillness
      2. Quality collapse — recent reflection average < 0.15
         → 10-minute stillness (Echo needs quiet when output has degraded)

    Guards:
      - Won't re-enter within _REENTRY_COOLDOWN (2 hours) of last exit
      - Won't enter if already in stillness
    """
    if is_in_stillness():
        return False, "", 0

    if seconds_since_last_exit() < _REENTRY_COOLDOWN:
        return False, "", 0

    # Trigger 1: circadian night phase
    try:
        import numpy as np
        vec = np.load("memory/echo_state.npy")
        temporal_phase = float(vec[7])
        if temporal_phase < 0.15:
            return True, "night_phase", 1200  # 20 minutes
    except Exception:
        pass

    return False, "", 0
