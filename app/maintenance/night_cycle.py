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

# "A metabolism" (2026-07-21, differential audit follow-up) — no file here
# was previously capped at all; confirmed live during the audit that these
# ten grow unbounded (echo_watchdog.log alone was 160MB). memory/SELF_EDIT.log
# is deliberately NOT in this list: backfill_convergence_from_log() does a
# genuine full-file replay of it on every process start (Finding 16) to
# reconstruct real self-edit history, and rotating it would silently shrink
# that reconstruction every time this fires.
_LOG_RETENTION_TARGETS = (
    (Path("memory/echo_watchdog.log"), 100 * 1024 * 1024),
    (Path("memory/reflection_shard.jsonl"), 100 * 1024 * 1024),
    (Path("memory/interaction_log.jsonl"), 100 * 1024 * 1024),
    (Path("memory/dream_bridge.log"), 100 * 1024 * 1024),
    (Path("memory/SELF_EDIT_MASTERY_.log"), 100 * 1024 * 1024),
    (Path("memory/reflection_journal.jsonl"), 100 * 1024 * 1024),
    (Path("memory/quarantine_journal.jsonl"), 50 * 1024 * 1024),
    (Path("memory/validator_audit.log"), 50 * 1024 * 1024),
    (Path("memory/council_deliberations.jsonl"), 50 * 1024 * 1024),
)
_LOG_RETENTION_STATE = Path("memory/log_retention_state.json")
_LOG_RETENTION_CHECK_INTERVAL_HOURS = 24
# Confirmed live on the very first real run (2026-07-21): two overlapping
# _perform_reflection() calls both read _LOG_RETENTION_STATE, both saw the
# gate as due, and both proceeded — reflection_shard.jsonl was rotated
# twice within one second. Same check-then-act-with-no-lock shape as
# Finding 41 B1/B2/B4/B5; same fix.
_log_retention_lock = threading.Lock()

# echo_janitor.py (root) — resolved 2026-07-21. Fully built, functionally
# safe (verified live via --dry-run: only ever auto-archives from a narrow,
# reversible KNOWN_CLUTTER/duplicate/old_log set; ambiguous "not_imported"
# candidates are always flag-only, never moved), but had zero real wiring —
# its own docstring describes two integration points that don't exist:
# emergent_scheduler.schedule_task() is a hollow "auto-repaired stub"
# (prints a line, returns None), and nothing anywhere reads
# logs/janitor_report.json ("surfaced to terminal on next session" never
# implemented). Wired into the same real, already-scheduled cycle
# log_retention uses instead, at the weekly cadence the module's own
# docstring already specified. Lock added preemptively (not discovered
# live this time) given the identical shape already found for log
# retention on its first real run.
_JANITOR_STATE = Path("memory/janitor_state.json")
_JANITOR_INTERVAL_DAYS = 7
_janitor_lock = threading.Lock()

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
            # Shared throttle/stillness gate (autonomy_coordinator) — every
            # other autonomous loop already checks this; NightCycle's own
            # tick was the one that didn't, so it kept running full
            # consolidation cycles regardless of RAM pressure or stillness.
            from app.core.autonomy_coordinator import should_run_cycle
            if should_run_cycle("night_cycle"):
                try:
                    self._perform_reflection()
                except Exception as e:
                    logging.error(f"[NightCycle] Error during cycle: {e}")
            else:
                logging.info("[NightCycle] Skipping cycle — system under pressure or in stillness")
            time.sleep(self.interval)

    def _perform_reflection(self):
        """
        Run one memory consolidation cycle: time trim → semantic prune → FAISS rebuild.
        Replaces the original heartbeat stub (System 4 of EMERGENCE_ROADMAP).
        """
        try:
            from app.maintenance.consolidation import ConsolidationRunner
            summary = ConsolidationRunner().run()
            if summary.get("skipped"):
                logging.debug(
                    "[NightCycle] Consolidation skipped (%s).", summary.get("reason")
                )
            else:
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

        # "A metabolism" — daily-gated log retention check
        self._maybe_rotate_large_logs()

        # echo_janitor.py — weekly-gated project-root hygiene scan
        self._maybe_run_janitor()

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

    def _maybe_rotate_large_logs(self) -> None:
        """Check memory/*.log and memory/*.jsonl growth once every
        _LOG_RETENTION_CHECK_INTERVAL_HOURS, rotating (gzip + truncate) any
        target file over its cap via log_retention.rotate_if_oversized().
        Lock-guarded end to end (check-then-act on shared state, same shape
        Finding 41 B1/B2/B4/B5 already fixed elsewhere) — a non-blocking
        try_lock so a second overlapping caller simply skips this cycle
        rather than waiting to redundantly redo the same rotation."""
        if not _log_retention_lock.acquire(blocking=False):
            logging.debug("[NightCycle] Log retention check already in progress — skipping.")
            return
        try:
            last_checked = 0.0
            if _LOG_RETENTION_STATE.exists():
                import json
                last_checked = json.loads(_LOG_RETENTION_STATE.read_text()).get("last_checked", 0.0)
            age_hours = (datetime.now(timezone.utc).timestamp() - last_checked) / 3600
            if age_hours < _LOG_RETENTION_CHECK_INTERVAL_HOURS:
                return

            # Commit the gate before doing the (slower) real rotation work,
            # not after — closes the exact window that let two overlapping
            # callers both pass the "is it due" check above.
            import json
            _LOG_RETENTION_STATE.write_text(
                json.dumps({"last_checked": datetime.now(timezone.utc).timestamp()})
            )

            from app.core.log_retention import rotate_if_oversized
            rotated = []
            for path, max_bytes in _LOG_RETENTION_TARGETS:
                if rotate_if_oversized(path, max_bytes):
                    rotated.append(path.name)
            if rotated:
                logging.info(f"[NightCycle] Log retention rotated: {rotated}")
            else:
                logging.debug("[NightCycle] Log retention check — nothing over threshold.")
        except Exception as e:
            logging.warning(f"[NightCycle] Log retention check failed: {e}")
        finally:
            _log_retention_lock.release()

    def _maybe_run_janitor(self) -> None:
        """Run echo_janitor.py's real scan+review+execute pipeline once every
        _JANITOR_INTERVAL_DAYS. dry_run=False, but this is safe by the
        janitor's own design: echo_review() only ever sets decision="archive"
        for known_clutter/duplicate/old_log matches (all reversible — files
        land in archive_janitor/, never deleted); everything else (including
        every real candidate found in this repo as of 2026-07-21 — three
        standalone CLI scripts, all "not_imported" false positives) is
        flag-only and never touched."""
        if not _janitor_lock.acquire(blocking=False):
            logging.debug("[NightCycle] Janitor scan already in progress — skipping.")
            return
        try:
            last_run = 0.0
            if _JANITOR_STATE.exists():
                import json
                last_run = json.loads(_JANITOR_STATE.read_text()).get("last_run", 0.0)
            age_days = (datetime.now(timezone.utc).timestamp() - last_run) / 86400
            if age_days < _JANITOR_INTERVAL_DAYS:
                return

            import json
            _JANITOR_STATE.write_text(
                json.dumps({"last_run": datetime.now(timezone.utc).timestamp()})
            )

            import sys
            root = str(Path(__file__).resolve().parent.parent.parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            from echo_janitor import run_janitor
            run_janitor(dry_run=False)
            logging.info("[NightCycle] Janitor scan complete — see logs/janitor_report.json for detail.")
        except Exception as e:
            logging.warning(f"[NightCycle] Janitor scan failed: {e}")
        finally:
            _janitor_lock.release()

# Quick standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    nc = NightCycle(interval=10)
    nc.start()
    time.sleep(35)
    nc.stop()

