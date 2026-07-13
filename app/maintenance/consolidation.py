# app/maintenance/consolidation.py
# ============================================================
# FORGETTING MODULE — System 4 of EMERGENCE_ROADMAP
# ============================================================
# Wraps memory_bridge's prune/rebuild pipeline as a single
# callable and writes a structured event record.
#
# Called from:
#   - NightCycle._perform_reflection() on a 300s timer
#   - Flask route /api/maintenance/consolidate (future)
#
# Does NOT call Ollama — pure signal processing.
# ============================================================

import gzip
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConsolidationRunner:
    """
    Runs one full memory consolidation cycle:
      1. Time-based trim (entries older than cutoff_days)
      2. Semantic prune (keep top N% by cosine similarity to centroid)
      3. FAISS rebuild from the pruned journal
      4. Append a structured event to consolidation_log.jsonl
      5. Update self_model.json memory_health.last_consolidation
    """

    def __init__(
        self,
        memory_dir: str | None = None,
        top_keep: float = 0.2,
        cutoff_days: int = 180,
        min_interval_hours: float = 1.0,
    ):
        try:
            from app.core import config
            self._memory_dir = memory_dir or config.MEMORY_DIR
        except Exception:
            self._memory_dir = memory_dir or "memory"

        self._top_keep = top_keep
        self._cutoff_days = cutoff_days
        self._min_interval_hours = min_interval_hours
        self._log_path = os.path.join(self._memory_dir, "consolidation_log.jsonl")
        self._model_path = os.path.join(self._memory_dir, "self_model.json")

    # ── Public API ──────────────────────────────────────────────────────

    def _should_run(self) -> bool:
        """No frequency gate previously existed here at all — this class is
        invoked every 300s by NightCycle, so every tick ran a full trim +
        semantic prune (apricot facility-location selection over the whole
        journal) + FAISS rebuild, unconditionally, forever."""
        try:
            with open(self._model_path, "r", encoding="utf-8") as f:
                model = json.load(f)
            last = model.get("memory_health", {}).get("last_consolidation")
            if not last:
                return True
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            elapsed_hours = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600.0
            return elapsed_hours >= self._min_interval_hours
        except Exception:
            return True

    def run(self) -> dict:
        """
        Execute a full consolidation cycle.
        Returns a summary dict of what happened (pruned, kept, etc.).
        Never raises — logs errors and returns partial result.
        """
        if not self._should_run():
            logger.debug("[Consolidation] Skipped — last cycle within %.1fh window.", self._min_interval_hours)
            # Same key shape as a real run's summary (below) — night_cycle.py's
            # caller does summary['entries_before'] etc. as a direct subscript,
            # not .get(), so a skip-only dict missing those keys raised
            # KeyError here on every skipped tick (i.e. most ticks, since this
            # gate now allows a real run only once an hour against NightCycle's
            # 300s cadence) — caught by the caller's own try/except, but logged
            # a misleading "Consolidation failed" every time.
            return {
                "skipped": True,
                "reason": "min_interval_not_elapsed",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "entries_before": 0,
                "entries_after": 0,
                "pruned_count": 0,
                "faiss_vectors_after": 0,
                "error": None,
            }

        started_at = datetime.now(timezone.utc).isoformat()
        summary = {
            "started_at": started_at,
            "entries_before": 0,
            "entries_after": 0,
            "pruned_count": 0,
            "faiss_vectors_after": 0,
            "error": None,
        }

        try:
            from app.core import memory_bridge as mb

            # Count entries before
            summary["entries_before"] = self._count_journal_lines(mb.ACTIVE_JOURNAL)

            # Step 1: Time-based trim
            try:
                mb.trim_memory_journal(cutoff_days=self._cutoff_days)
                logger.info("[Consolidation] Time-based trim complete.")
            except Exception as e:
                logger.warning("[Consolidation] trim_memory_journal failed: %s", e)

            after_trim = self._count_journal_lines(mb.ACTIVE_JOURNAL)

            # Step 2: Semantic prune — only if journal has meaningful content
            if after_trim >= 10:
                try:
                    mb.autonomous_prune_journal(
                        top_percent_to_keep=self._top_keep,
                        chunk_size=100,
                    )
                    logger.info("[Consolidation] Semantic prune complete.")
                except Exception as e:
                    logger.warning("[Consolidation] autonomous_prune_journal failed: %s", e)
            else:
                logger.info(
                    "[Consolidation] Journal too small to prune (%d lines) — skipping.",
                    after_trim,
                )

            after_prune = self._count_journal_lines(mb.ACTIVE_JOURNAL)

            # Step 3: Rebuild FAISS index
            try:
                mb.rebuild_vector_memory()
                idx = getattr(getattr(mb, "vector_memory", None), "index", None)
                if idx is not None:
                    summary["faiss_vectors_after"] = int(idx.ntotal)
                logger.info(
                    "[Consolidation] FAISS rebuilt (%d vectors).",
                    summary["faiss_vectors_after"],
                )
            except Exception as e:
                logger.warning("[Consolidation] rebuild_vector_memory failed: %s", e)

            summary["entries_after"] = after_prune
            summary["pruned_count"] = max(0, summary["entries_before"] - after_prune)

        except Exception as e:
            summary["error"] = str(e)
            logger.error("[Consolidation] Cycle failed: %s", e)

        # Step 4: Log the event
        self._append_log(summary)

        # Step 5: Update self_model.json
        self._update_self_model(summary)

        logger.info(
            "[Consolidation] Done | before=%d after=%d pruned=%d faiss=%d",
            summary["entries_before"],
            summary["entries_after"],
            summary["pruned_count"],
            summary["faiss_vectors_after"],
        )
        return summary

    # ── I/O helpers ────────────────────────────────────────────────────

    def _count_journal_lines(self, path: str) -> int:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _append_log(self, summary: dict):
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(summary, default=str) + "\n")
        except Exception as e:
            logger.warning("[Consolidation] Failed to write log: %s", e)

    def _update_self_model(self, summary: dict):
        try:
            model: dict = {}
            try:
                with open(self._model_path, "r", encoding="utf-8") as f:
                    model = json.load(f)
            except Exception:
                pass

            health = model.setdefault("memory_health", {})
            health["last_consolidation"] = summary["started_at"]
            health["last_pruned_count"] = summary["pruned_count"]
            health["faiss_vector_count"] = summary["faiss_vectors_after"]

            tmp = self._model_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(model, f, indent=2, default=str)
            os.replace(tmp, self._model_path)
        except Exception as e:
            logger.warning("[Consolidation] Failed to update self_model: %s", e)
