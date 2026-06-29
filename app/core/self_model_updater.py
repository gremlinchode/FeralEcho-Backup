# app/core/self_model_updater.py
# ============================================================
# LIVING SELF-MODEL — System 2 of EMERGENCE_ROADMAP
# ============================================================
# Reads introspection_state.json (System 1) plus raw logs and
# produces a structured performance snapshot at
# memory/self_model.json.
#
# This file is the ground truth for what Echo knows about her
# own performance. It is the input for:
#   - System 3 (self-edit Optuna targeting)
#   - System 4 (forgetting module — memory_health field)
#   - System 5 (Modelfile proposer — performance + sandbox fields)
#
# No LLM calls. Pure signal aggregation from existing data.
# ============================================================

import json
import logging
import math
import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Quality score threshold below which a task type is considered "weak".
# Scores are 0–4 integers from echo_quality_scorer.
_WEAK_QUALITY_THRESHOLD = 2.5

# Minimum River observations before a task type is considered reliably scored.
_MIN_OBS_FOR_TARGETING = 20


class SelfModelUpdater:
    """
    Computes memory/self_model.json from introspection_state.json and raw logs.

    Runs on its own daemon thread at `interval` seconds (default 130s —
    10s after IntrospectionChannel's 120s cycle, so fresh data is always
    available before update runs).

    Can also be called directly: SelfModelUpdater().update()
    """

    def __init__(self, memory_dir: str | None = None, interval: int = 130):
        try:
            from app.core import config
            self._memory_dir = memory_dir or config.MEMORY_DIR
        except Exception:
            self._memory_dir = memory_dir or "memory"

        self._introspection_path = os.path.join(
            self._memory_dir, "introspection_state.json"
        )
        self._model_path = os.path.join(self._memory_dir, "self_model.json")
        self._interaction_log = os.path.join(
            self._memory_dir, "interaction_log.jsonl"
        )
        self._shard_path = os.path.join(
            self._memory_dir, "reflection_shard.jsonl"
        )
        self._principles_path = os.path.join(
            os.path.dirname(self._memory_dir), "echo_principles.json"
        )

        self._interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────

    def start(self) -> "SelfModelUpdater":
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="SelfModelUpdater"
        )
        self._thread.start()
        logger.info("[SelfModel] Updater started (interval=%ds).", self._interval)
        return self

    def stop(self):
        self._stop_event.set()

    # ── Public API ─────────────────────────────────────────────────────

    def update(self) -> dict:
        """
        Build and write self_model.json. Returns the written dict.
        Safe to call from any thread.
        """
        introspection = self._read_introspection()
        interactions = self._read_interactions(last_n=500)
        shard_entries = self._read_shard(last_n=200)
        generation = self._read_generation()

        performance = self._compute_task_performance(introspection, interactions)
        self_edit = self._compute_self_edit_stats(introspection, shard_entries)
        targets = self._compute_targets(performance, self_edit, introspection)

        model = {
            "schema_version": 1,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "generation": generation + 1,
            "performance": {"by_task_type": performance},
            "self_edit": self_edit,
            "memory_health": {
                "faiss_vector_count": (
                    introspection.get("memory", {}).get("faiss_vector_count", 0)
                ),
                "journal_line_count": (
                    introspection.get("memory", {}).get("journal_line_count", 0)
                ),
                "last_consolidation": None,
            },
            "friction": {
                "rate_last_50": (
                    introspection.get("claude_shard", {}).get("friction_rate", 0.0)
                ),
                "recurring_questions": (
                    introspection.get("claude_shard", {}).get(
                        "top_friction_questions", []
                    )
                ),
            },
            "river_brain": self._summarize_river(introspection),
            "world_model": self._compute_world_model(introspection),
            "weekly_delta": self._compute_weekly_delta(performance),
            "targets": targets,
        }

        self._write(model)
        logger.info(
            "[SelfModel] Updated | gen=%d | focus=%s | reason=%s",
            model["generation"],
            targets.get("next_self_edit_focus", "?"),
            targets.get("reason", "?"),
        )
        return model

    def get_targets(self) -> dict:
        """Return the targets block from the current self_model.json."""
        m = self._read_model()
        return m.get("targets", {})

    def get_weak_task_type(self) -> str:
        """Return the task type Optuna should focus on next."""
        return self.get_targets().get("next_self_edit_focus", "general")

    # ── Background loop ────────────────────────────────────────────────

    def _loop(self):
        self._stop_event.wait(10)  # Let IntrospectionChannel complete its first write
        if self._stop_event.is_set():
            return
        try:
            self.update()
        except Exception as e:
            logger.warning("[SelfModel] Initial update failed: %s", e)

        while not self._stop_event.is_set():
            self._stop_event.wait(self._interval)
            if self._stop_event.is_set():
                break
            try:
                self.update()
            except Exception as e:
                logger.warning("[SelfModel] Update cycle error: %s", e)

    # ── Computation ────────────────────────────────────────────────────

    def _compute_task_performance(
        self, introspection: dict, interactions: list
    ) -> dict:
        """
        Per-task-type performance metrics derived from interaction_log and
        the introspection confidence matrix.
        """
        task_types = ["coding", "creative", "personal", "reasoning", "general"]
        performance: dict[str, dict] = {}

        # Group interactions by task type
        by_task: dict[str, list] = defaultdict(list)
        for e in interactions:
            tt = e.get("task_type", "general")
            by_task[tt].append(e)

        conf_matrix = (
            introspection.get("river_brain", {}).get("confidence_matrix", {})
        )

        for task in task_types:
            entries = by_task.get(task, [])
            scores = [
                e["quality_score"]
                for e in entries
                if isinstance(e.get("quality_score"), (int, float))
            ]
            avg_quality = round(sum(scores) / len(scores), 3) if scores else 0.0

            # Best model: highest confidence score for this task
            task_conf = conf_matrix.get(task, {})
            best_model = (
                max(task_conf, key=task_conf.get) if task_conf else "unknown"
            )

            # Sandbox success rate for this task
            sandbox_entries = [
                e for e in entries
                if e.get("sandbox_outcome") in ("success", "failed")
            ]
            if sandbox_entries:
                sandbox_rate = round(
                    sum(1 for e in sandbox_entries if e.get("sandbox_outcome") == "success")
                    / len(sandbox_entries),
                    4,
                )
            else:
                sandbox_rate = None

            performance[task] = {
                "avg_quality_score": avg_quality,
                "sample_count": len(scores),
                "best_model": best_model,
                "sandbox_success_rate": sandbox_rate,
            }

        return performance

    def _compute_self_edit_stats(
        self, introspection: dict, shard_entries: list
    ) -> dict:
        """
        Self-edit performance from reflection_shard.jsonl entries that
        contain generated_code (i.e. are self-edit reflections, not
        regular echo_query reflections).
        """
        edit_entries = [
            e for e in shard_entries if "generated_code" in e
        ]
        total = len(edit_entries)
        successes = sum(1 for e in edit_entries if e.get("result") == "success")
        failures = [e for e in edit_entries if e.get("result") == "failed"]

        success_rate = round(successes / total, 4) if total else 0.0

        # Common weak areas from failure sandbox_feedback strings
        weak_areas: list[str] = []
        feedback_counter: dict[str, int] = defaultdict(int)
        for e in failures:
            fb = e.get("sandbox_feedback", "") or ""
            if "prose_detected" in fb:
                feedback_counter["prose_detected_in_code"] += 1
            if "retry" in fb.lower() and "fail" in fb.lower():
                feedback_counter["retry_also_fails"] += 1
            if "syntax" in fb.lower():
                feedback_counter["syntax_error"] += 1
        weak_areas = sorted(
            feedback_counter, key=feedback_counter.get, reverse=True  # type: ignore[arg-type]
        )[:3]

        # Best params from Optuna (if any trials have completed)
        best_intensity: float | None = None
        best_creativity: float | None = None
        best_optuna_value: float | None = None
        opt = introspection.get("optuna", {})
        if opt.get("best_params"):
            best_intensity = opt["best_params"].get("intensity")
            best_creativity = opt["best_params"].get("creativity")
            best_optuna_value = opt.get("best_value")

        hours_since = introspection.get("self_edit", {}).get(
            "hours_since_last_success"
        )

        return {
            "total_attempts": total,
            "success_rate": success_rate,
            "hours_since_last_success": hours_since,
            "weak_areas": weak_areas,
            "best_intensity": best_intensity,
            "best_creativity": best_creativity,
            "optuna_best_value": best_optuna_value,
        }

    def _compute_targets(
        self,
        performance: dict,
        self_edit: dict,
        introspection: dict,
    ) -> dict:
        """
        Identify the task type Optuna should target next.

        Rules (in priority order):
        1. Any task type with avg_quality_score < threshold AND
           River observation_count > MIN_OBS_FOR_TARGETING.
        2. Among qualifying types, pick the lowest avg_quality_score.
        3. If no task type qualifies (all under-observed or all strong),
           fall back to "coding" — the most observable task type and
           the one with the worst sandbox rate in the live data.
        """
        obs_counts = (
            introspection.get("river_brain", {}).get("observation_counts", {})
        )

        candidates: list[tuple[float, str]] = []
        for task, perf in performance.items():
            obs = obs_counts.get(task, 0)
            avg = perf.get("avg_quality_score", 0.0)
            if obs >= _MIN_OBS_FOR_TARGETING and avg < _WEAK_QUALITY_THRESHOLD:
                candidates.append((avg, task))

        if candidates:
            candidates.sort()
            chosen_score, chosen_task = candidates[0]
            obs = obs_counts.get(chosen_task, 0)
            reason = (
                f"avg_quality={chosen_score:.2f} (threshold={_WEAK_QUALITY_THRESHOLD}), "
                f"obs={obs}"
            )
        else:
            # Fall back: pick the task with most observations and worst quality
            # among all task types (even under-observed ones)
            scored = [
                (perf.get("avg_quality_score", 2.5), task)
                for task, perf in performance.items()
                if obs_counts.get(task, 0) > 0
            ]
            if scored:
                scored.sort()
                chosen_score, chosen_task = scored[0]
                reason = (
                    f"fallback (no task met obs threshold); "
                    f"worst avg_quality={chosen_score:.2f}"
                )
            else:
                chosen_task = "coding"
                reason = "no observation data yet; defaulting to coding"

        return {
            "next_self_edit_focus": chosen_task,
            "reason": reason,
        }

    def _summarize_river(self, introspection: dict) -> dict:
        rb = introspection.get("river_brain", {})
        obs = rb.get("observation_counts", {})
        conf = rb.get("confidence_matrix", {})

        # Weakest / strongest task by average confidence score across models
        task_avg: dict[str, float] = {}
        for task, models in conf.items():
            vals = [v for v in models.values() if isinstance(v, (int, float))]
            if vals:
                task_avg[task] = sum(vals) / len(vals)

        weakest = min(task_avg, key=task_avg.get) if task_avg else "unknown"  # type: ignore[arg-type]
        strongest = max(task_avg, key=task_avg.get) if task_avg else "unknown"  # type: ignore[arg-type]

        return {
            "influence_weight": rb.get("influence_weight", 0.0),
            "total_observations": sum(obs.values()),
            "weakest_task_type": weakest,
            "strongest_task_type": strongest,
        }

    # ── I/O helpers ────────────────────────────────────────────────────

    def _read_introspection(self) -> dict:
        try:
            with open(self._introspection_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(
                "[SelfModel] introspection_state.json not found — "
                "IntrospectionChannel may not have run yet."
            )
            return {}
        except Exception as e:
            logger.warning("[SelfModel] Failed to read introspection state: %s", e)
            return {}

    def _read_interactions(self, last_n: int = 500) -> list:
        entries = []
        if not os.path.exists(self._interaction_log):
            return entries
        try:
            with open(self._interaction_log, "r", encoding="utf-8") as f:
                lines = f.readlines()[-last_n * 2:]
            for line in lines:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
            return entries[-last_n:]
        except Exception as e:
            logger.warning("[SelfModel] Failed to read interaction log: %s", e)
            return []

    def _read_shard(self, last_n: int = 200) -> list:
        entries = []
        if not os.path.exists(self._shard_path):
            return entries
        try:
            with open(self._shard_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-last_n * 2:]
            for line in lines:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
            return entries[-last_n:]
        except Exception as e:
            logger.warning("[SelfModel] Failed to read reflection shard: %s", e)
            return []

    def _read_model(self) -> dict:
        try:
            with open(self._model_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _read_generation(self) -> int:
        """
        Read the generation counter. Checks self_model.json first
        (authoritative once it exists), then falls back to
        echo_principles.json to preserve continuity on first run.
        """
        m = self._read_model()
        if "generation" in m:
            return int(m["generation"])
        try:
            with open(self._principles_path, "r", encoding="utf-8") as f:
                p = json.load(f)
            return int(p.get("generation", 0))
        except Exception:
            return 0

    def _compute_world_model(self, introspection: dict) -> dict:
        """
        Derives world_model block from the predictive_loops snapshot in
        introspection_state.json.  Also reads world_model_diagnostics.json
        (written by the PyMC slow path) if available.
        """
        pl = introspection.get("predictive_loops", {})
        surprise_last = pl.get("surprise_last", 0.0)
        surprise_r10 = pl.get("surprise_rolling_10", 0.0)
        surprise_r50 = pl.get("surprise_rolling_50", 0.0)
        cycles = pl.get("cycles_logged", 0)

        if cycles == 0:
            accuracy = None
            trend = "no_data"
        else:
            # Accuracy: inverse-normalized surprise.
            # Empirically, surprise_F < 1.0 is well-calibrated, > 5.0 is very wrong.
            accuracy = round(max(0.0, 1.0 - min(surprise_r50 / 5.0, 1.0)), 4)

            if surprise_r10 > surprise_r50 * 1.2:
                trend = "increasing"
            elif surprise_r10 < surprise_r50 * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"

        result = {
            "accuracy": accuracy,
            "trend": trend,
            "surprise_last": surprise_last,
            "surprise_rolling_avg": surprise_r50,
            "cycles_logged": cycles,
            "topic_distribution": pl.get("topic_distribution", {}),
            "pymc_diagnostics": None,
        }

        # Attach latest PyMC diagnostics if available
        diag_path = os.path.join(self._memory_dir, "world_model_diagnostics.json")
        if os.path.exists(diag_path):
            try:
                with open(diag_path, "r", encoding="utf-8") as f:
                    diag = json.load(f)
                result["pymc_diagnostics"] = {
                    "model_calibrated": diag.get("model_calibrated"),
                    "r_hat_max": diag.get("r_hat_max"),
                    "ess_bulk_min": diag.get("ess_bulk_min"),
                    "posterior_sentiment": diag.get("posterior_sentiment_mean"),
                    "timestamp": diag.get("timestamp"),
                }
            except Exception:
                pass

        return result

    def _compute_weekly_delta(self, current_performance: dict) -> dict:
        """C1: Compare current quality scores to the oldest available snapshot."""
        try:
            from pathlib import Path
            history_dir = Path(self._memory_dir) / "history"
            snapshots = sorted(history_dir.glob("self_model_*.json"))
            if not snapshots:
                return {"status": "no_snapshots_yet"}
            with open(snapshots[0], "r", encoding="utf-8") as fh:
                old = json.load(fh)
            old_perf = old.get("performance", {}).get("by_task_type", {})
            delta: dict = {}
            for task, cur in current_performance.items():
                cur_q = cur.get("avg_quality_score", 0)
                old_q = old_perf.get(task, {}).get("avg_quality_score", 0)
                delta[task] = round(cur_q - old_q, 4)
            return {
                "compared_to": snapshots[0].name,
                "quality_delta_by_task": delta,
            }
        except Exception as e:
            logger.debug("[SelfModel] weekly_delta failed: %s", e)
            return {"status": "error", "reason": str(e)}

    def _write(self, model: dict):
        tmp = self._model_path + ".tmp"
        try:
            os.makedirs(os.path.dirname(self._model_path), exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(model, f, indent=2, default=str)
            os.replace(tmp, self._model_path)
        except Exception as e:
            logger.warning("[SelfModel] Write failed: %s", e)
            try:
                os.unlink(tmp)
            except Exception:
                pass
