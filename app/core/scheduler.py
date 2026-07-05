"""
app/core/scheduler.py

Shared tick registry — one dispatcher thread instead of N independent
`while True: ...; time.sleep(N)` loops. Implements roadmap.txt RULE 6
(scheduler.count == 1) and the forensic audit's observation that at least
three subsystems (self-edit loop, autonomous_loop's main cycle, NightCycle)
each wake up on their own uncoordinated hourly timer.

This module is additive and standalone: registering with it is opt-in.
Existing loops keep working exactly as before until they're deliberately
migrated to call register() instead of spawning their own thread — that
migration is a separate, reviewed step per subsystem, not automatic.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)


class SharedScheduler:
    def __init__(self, poll_interval_s: float = 5.0):
        self._poll_interval_s = poll_interval_s
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._thread: "threading.Thread | None" = None
        self._running = False

    def register(self, name: str, interval_s: float, callback, initial_delay_s: float = 0.0) -> None:
        """Register a job. Raises ValueError on duplicate name — callers must
        unregister() first if they intend to replace a job."""
        with self._lock:
            if name in self._jobs:
                raise ValueError(f"[Scheduler] Job '{name}' is already registered")
            self._jobs[name] = {
                "interval_s": interval_s,
                "callback": callback,
                "next_due": time.time() + initial_delay_s,
            }
        logger.info(
            "[Scheduler] Registered '%s' (interval=%ss, initial_delay=%ss)",
            name, interval_s, initial_delay_s,
        )

    def unregister(self, name: str) -> None:
        with self._lock:
            self._jobs.pop(name, None)

    def status(self) -> dict:
        """Snapshot of every registered job's interval and time until next fire —
        the observable state this module exists to provide."""
        now = time.time()
        with self._lock:
            return {
                name: {
                    "interval_s": job["interval_s"],
                    "next_due_in_s": round(job["next_due"] - now, 1),
                }
                for name, job in self._jobs.items()
            }

    def _run_job(self, name: str, callback) -> None:
        try:
            callback()
        except Exception as e:
            logger.warning("[Scheduler] Job '%s' raised: %s", name, e)

    def _dispatch_loop(self) -> None:
        while self._running:
            now = time.time()
            due = []
            with self._lock:
                for name, job in self._jobs.items():
                    if now >= job["next_due"]:
                        due.append((name, job["callback"]))
                        job["next_due"] = now + job["interval_s"]
            # Each due job runs in its own thread so one slow/blocking job
            # (e.g. an hourly self-edit cycle) can't delay another job's timing.
            for name, callback in due:
                threading.Thread(
                    target=self._run_job, args=(name, callback),
                    name=f"SchedJob-{name}", daemon=True,
                ).start()
            time.sleep(self._poll_interval_s)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.debug("[Scheduler] Already running.")
            return
        self._running = True
        self._thread = threading.Thread(target=self._dispatch_loop, name="SharedScheduler", daemon=True)
        self._thread.start()
        logger.info("[Scheduler] Dispatcher started (poll_interval=%ss).", self._poll_interval_s)

    def stop(self) -> None:
        self._running = False


_scheduler: "SharedScheduler | None" = None


def get_scheduler() -> SharedScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = SharedScheduler()
    return _scheduler
