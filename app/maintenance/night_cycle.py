# app/maintenance/night_cycle.py – PATCHED
import shutil
import threading
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core import memory_bridge as mb

_SELF_MODEL_SRC = Path("memory/self_model.json")
_HISTORY_DIR = Path("memory/history")
_MAX_SNAPSHOTS = 8
_SNAPSHOT_INTERVAL_DAYS = 7

class NightCycle:
    """
    Handles autonomous night-time cycles for memory reflection, dream logging, and self-edits.
    """

    def __init__(self, app=None, interval: int = 300, start_delay: int = 0, force: bool = False):
        """
        Args:
            app: Optional Flask app or context object (can be None)
            interval: Time between cycles in seconds (default 5 min)
            start_delay: Seconds to sleep before the first cycle (for staggering)
            force: Accepted for call-site compatibility; currently unused.
        """
        self.app = app
        self.interval = interval
        self.start_delay = start_delay
        self.running = False
        self.thread: Optional[threading.Thread] = None
        logging.info(f"[NightCycle] Initialized with interval={self.interval}s start_delay={self.start_delay}s")

    def start_once(self):
        """Run a single reflection cycle synchronously (used by /force_nightcycle endpoint)."""
        try:
            self._perform_reflection()
        except Exception as e:
            logging.error(f"[NightCycle] start_once error: {e}")

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_cycle, daemon=True)
            self.thread.start()
            logging.info("[NightCycle] Started autonomous night cycle.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            logging.info("[NightCycle] Night cycle stopped.")

    def _run_cycle(self):
        if self.start_delay:
            time.sleep(self.start_delay)
        while self.running:
            try:
                self._perform_reflection()
            except Exception as e:
                logging.error(f"[NightCycle] Error during cycle: {e}")
            time.sleep(self.interval)

    def _perform_reflection(self):
        """
        Run one memory consolidation cycle: time trim → semantic prune → FAISS rebuild.
        Replaces the original heartbeat stub (System 4 of EMERGENCE_ROADMAP).
        """
        try:
            from app.maintenance.consolidation import ConsolidationRunner
            summary = ConsolidationRunner().run()
            logging.info(
                f"[NightCycle] Consolidation complete | "
                f"before={summary['entries_before']} "
                f"after={summary['entries_after']} "
                f"pruned={summary['pruned_count']}"
            )
        except Exception as e:
            logging.error(f"[NightCycle] Consolidation failed: {e}")

        # C1: Weekly self_model snapshot
        self._maybe_snapshot_self_model()

        # Shadow accuracy check — compare experimental targets to what actually happened
        try:
            from app.core.shadow_model import log_accuracy, check_and_correct
            delta = log_accuracy()
            if "focus_matches" in delta:
                logging.info(
                    "[NightCycle] Shadow accuracy | focus_matches=%s | shadow=%s | real=%s",
                    delta["focus_matches"], delta.get("shadow_focus"), delta.get("real_focus"),
                )
            corrected = check_and_correct(delta)
            if corrected:
                logging.warning(
                    "[NightCycle] Shadow drift corrected → new focus proposed: %s", corrected
                )
        except Exception as _se:
            logging.debug("[NightCycle] Shadow accuracy check failed: %s", _se)

    def _maybe_snapshot_self_model(self) -> None:
        """Copy self_model.json to memory/history/ if no snapshot in the last 7 days."""
        try:
            if not _SELF_MODEL_SRC.exists():
                return
            _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
            snapshots = sorted(_HISTORY_DIR.glob("self_model_*.json"))
            needs_snapshot = True
            if snapshots:
                latest = snapshots[-1]
                age_days = (datetime.now(timezone.utc).timestamp() - latest.stat().st_mtime) / 86400
                needs_snapshot = age_days >= _SNAPSHOT_INTERVAL_DAYS
            if needs_snapshot:
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
                dest = _HISTORY_DIR / f"self_model_{stamp}.json"
                shutil.copy2(_SELF_MODEL_SRC, dest)
                logging.info(f"[NightCycle] Self-model snapshot saved: {dest.name}")
                # Prune oldest snapshots beyond the cap
                all_snaps = sorted(_HISTORY_DIR.glob("self_model_*.json"))
                for old in all_snaps[:-_MAX_SNAPSHOTS]:
                    old.unlink()
                    logging.info(f"[NightCycle] Old snapshot removed: {old.name}")
        except Exception as e:
            logging.warning(f"[NightCycle] Snapshot failed: {e}")

# Quick standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    nc = NightCycle(interval=10)
    nc.start()
    time.sleep(35)
    nc.stop()

