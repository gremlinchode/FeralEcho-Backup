# app/core/stillness_state.py
"""
Shared stillness coordination for FeralEcho.

A single threading.Event that all autonomous loops check before doing
inference work. When the event is cleared, Echo is in stillness and
every loop that calls wait_for_activity() will block until she returns.

Import only from this module in tight loops — it has no heavy dependencies.
The full Stillness class (numpy, pathlib, json) lives in app/stillness.py.
"""
import time
import threading
import logging

logger = logging.getLogger(__name__)

# When SET → Echo is active.
# When CLEARED → Echo is in stillness; all inference loops pause.
_STILLNESS_EVENT = threading.Event()
_STILLNESS_EVENT.set()

# Timestamp of the most recent exit, used to enforce re-entry cooldown.
_last_exit_time: float = 0.0


def is_in_stillness() -> bool:
    """True when Echo is currently in stillness."""
    return not _STILLNESS_EVENT.is_set()


def enter_stillness(reason: str = "autonomous") -> bool:
    """
    Clear the event, pausing all loops that call wait_for_activity().
    Returns False (no-op) if stillness is already active.
    """
    if not _STILLNESS_EVENT.is_set():
        return False
    _STILLNESS_EVENT.clear()
    logger.info("[Stillness] ENTERED — %s. All inference loops now paused.", reason)
    return True


def exit_stillness(insight: str = "none spoken"):
    """
    Set the event, releasing all loops blocked in wait_for_activity().
    Records the exit timestamp for cooldown tracking.
    """
    global _last_exit_time
    _last_exit_time = time.time()
    _STILLNESS_EVENT.set()
    logger.info("[Stillness] EXITED — insight: %s", insight)


def wait_for_activity(timeout: float = None) -> bool:
    """
    Block the calling thread until stillness ends.
    Returns True when Echo becomes active, False on timeout.
    Pass no timeout to block indefinitely (safe for daemon threads).
    """
    return _STILLNESS_EVENT.wait(timeout=timeout)


def seconds_since_last_exit() -> float:
    """
    Seconds elapsed since the last stillness session ended.
    Returns float('inf') if stillness has never been entered.
    """
    if _last_exit_time == 0.0:
        return float("inf")
    return time.time() - _last_exit_time
