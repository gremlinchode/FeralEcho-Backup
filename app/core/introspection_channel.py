# app/core/introspection_channel.py
# ============================================================
# INTROSPECTION CHANNEL — System 1 of EMERGENCE_ROADMAP
# ============================================================
# Lightweight observer that collects Echo's internal metrics
# on a background timer and writes a structured JSON snapshot
# to memory/introspection_state.json.
#
# Never modifies Echo's state — reads only.
# All collectors are individually fault-tolerant: a failure in
# one collector does not prevent the others from running.
# ============================================================

import json
import logging
import math
import os
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Resolved at runtime from app.core.config; this is the fallback.
_DEFAULT_MEMORY_DIR = "memory"


class IntrospectionChannel:
    """
    Reads Echo's internal metrics every `interval` seconds and writes
    a structured snapshot to memory/introspection_state.json.

    Designed to be the root data source for the Living Self-Model
    (System 2) and all downstream systems.
    """

    def __init__(self, core=None, interval: int = 120):
        self._core = core
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        try:
            from app.core import config
            self._memory_dir = config.MEMORY_DIR
            self._journal_file = config.MEMORY_JOURNAL_FILE
        except Exception:
            self._memory_dir = _DEFAULT_MEMORY_DIR
            self._journal_file = os.path.join(self._memory_dir, "memory_journal.log")

        self._state_path = os.path.join(self._memory_dir, "introspection_state.json")
        os.makedirs(self._memory_dir, exist_ok=True)

        # One PageHinkley detector per task type.
        # Detects monotonic quality decay (e.g. a model update or data drift)
        # within ~6 samples of the actual drift point.
        # min_instances=30: don't alarm until at least 30 samples seen.
        # threshold=10.0: cumulative sum threshold before declaring drift.
        #
        # Audit finding: this dict was previously rebuilt fresh in every
        # __init__ call with no persistence at all — a plain process restart
        # silently discarded accumulated observations with no log line
        # distinguishing "restarted" from reset_drift_detectors()'s
        # deliberate, logged reset. Given this project's own documented
        # restart-after-every-code-change workflow and min_instances=30
        # before a detector can even alarm, this plausibly prevented these
        # detectors from ever reaching steady state in normal operation.
        # Now tries to load prior pickled state first (_load_drift_detectors);
        # falls back to fresh detectors on any failure — same fail-open
        # posture as every other persistence layer in this codebase
        # (RiverBrain's "never overwrite richer state" guard, etc.).
        self._drift_detectors_path = os.path.join(self._memory_dir, "drift_detectors.pkl")
        self._drift_detectors = self._load_drift_detectors()

        logger.info("[Introspection] Channel initialized (interval=%ds, path=%s).",
                    interval, self._state_path)

    def _load_drift_detectors(self) -> dict:
        try:
            from river.drift import PageHinkley
        except Exception:
            return {}
        fresh = {
            task: PageHinkley(min_instances=30, threshold=10.0)
            for task in ["coding", "creative", "personal", "reasoning", "general"]
        }
        if not os.path.exists(self._drift_detectors_path):
            logger.info("[Introspection] No prior drift-detector state found — starting fresh.")
            return fresh
        try:
            import pickle
            with open(self._drift_detectors_path, "rb") as f:
                loaded = pickle.load(f)
            if not isinstance(loaded, dict) or set(loaded.keys()) != set(fresh.keys()):
                logger.warning("[Introspection] Drift-detector state file shape mismatch — starting fresh.")
                return fresh
            logger.info(
                "[Introspection] Loaded prior drift-detector state for tasks: %s "
                "(restart preserved accumulated observations, not a reset).",
                sorted(loaded.keys()),
            )
            return loaded
        except Exception as e:
            logger.warning("[Introspection] Failed to load drift-detector state (%s) — starting fresh.", e)
            return fresh

    def _save_drift_detectors(self) -> None:
        if not self._drift_detectors:
            return
        try:
            import pickle
            tmp_path = self._drift_detectors_path + ".tmp"
            with open(tmp_path, "wb") as f:
                pickle.dump(self._drift_detectors, f)
            os.replace(tmp_path, self._drift_detectors_path)
        except Exception as e:
            logger.debug("[Introspection] Failed to persist drift-detector state: %s", e)

    # ── Lifecycle ──────────────────────────────────────────────────────

    def start(self) -> "IntrospectionChannel":
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="IntrospectionChannel"
        )
        self._thread.start()
        logger.info("[Introspection] Background loop started.")
        return self

    def stop(self):
        self._stop_event.set()

    def reset_drift_detectors(self) -> list:
        """
        Reset all PageHinkley drift detectors to a clean state.
        Call this after any structural change to River's training signal
        (e.g. removing cross-training contamination) so the detectors
        establish a new baseline from post-fix observations.
        Writes drift_detector_reset_at to memory/snapshot_baseline.json via
        patch_baseline_meta() (locked, atomic temp-then-rename) so post-reset
        observation counts are measurable going forward.
        Returns the list of task types reset.
        """
        reset = []
        for task, det in self._drift_detectors.items():
            try:
                det._reset()
                reset.append(task)
            except Exception as e:
                logger.warning("[Introspection] drift detector reset failed for %s: %s", task, e)
        ts = datetime.now(timezone.utc).isoformat()
        try:
            from app.core.snapshot_manager import patch_baseline_meta
            patch_baseline_meta("drift_detector_reset_at", ts)
            logger.info(
                "[Introspection] Drift detectors reset: %s — drift_detector_reset_at=%s written to snapshot_baseline.json",
                reset, ts,
            )
        except Exception as e:
            logger.warning(
                "[Introspection] reset timestamp write failed: %s — detectors were reset, timestamp not persisted", e
            )
            logger.info("[Introspection] Drift detectors reset: %s", reset)
        return reset

    # ── Public API ─────────────────────────────────────────────────────

    def collect(self) -> dict:
        """
        Run all six collectors, build state dict, write to disk.
        Returns the state dict regardless of write success.
        Safe to call from any thread.
        """
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "river_brain": self._collect_river_brain(),
            "claude_shard": self._collect_friction(),
            "sandbox": self._collect_sandbox(),
            "memory": self._collect_memory(),
            "self_edit": self._collect_self_edit(),
            "optuna": self._collect_optuna(),
            "system_health": self._collect_system_health(),
            "predictive_loops": self._collect_predictive_loops(),
        }
        # Liveness ledger runs last so it can reuse this cycle's own fresh
        # "memory" reading (self_model_drift compares self_model.json against
        # it) instead of taking a second, possibly-inconsistent read. See
        # liveness_ledger.py's module docstring — this is the mechanism named
        # in GREMLIN_ROLE.md's Core Operating Principle, not another audit.
        state["liveness_ledger"] = self._collect_liveness_ledger(state.get("memory", {}))
        self._write(state)
        self._save_drift_detectors()
        try:
            from app.core.echo_state import update as _echo_state_update
            _echo_state_update(state)
        except Exception as _ese:
            logger.debug("[Introspection] EchoState update failed: %s", _ese)
        return state

    # ── Background loop ────────────────────────────────────────────────

    def _loop(self):
        # Collect immediately on start so the file exists before any
        # downstream system tries to read it.
        try:
            self.collect()
        except Exception as e:
            logger.warning("[Introspection] Initial collect failed: %s", e)

        while not self._stop_event.is_set():
            self._stop_event.wait(self._interval)
            if self._stop_event.is_set():
                break
            try:
                self.collect()
            except Exception as e:
                logger.warning("[Introspection] Collect cycle error: %s", e)

    # ── Collector: RiverBrain ──────────────────────────────────────────

    def _collect_river_brain(self) -> dict:
        result = {
            "observation_counts": {},
            "confidence_matrix": {},
            "per_task_accuracy": {},
            "influence_weight": 0.0,
            "drift_alerts": {},
        }
        try:
            rb = self._get_river_brain()
            if rb is None:
                return result

            task_types = ["general", "coding", "creative", "personal", "reasoning"]

            result["observation_counts"] = dict(rb.observation_counts)
            result["influence_weight"] = round(rb.influence_weight, 4)

            # Per-task accuracy from River's accuracy_trackers.
            # Also feed each accuracy value into its PageHinkley detector
            # so drift_alerts reflects the current trend, not just current state.
            for task in task_types:
                tracker = rb.accuracy_trackers.get(task)
                if tracker is not None:
                    try:
                        acc = tracker.get()
                        result["per_task_accuracy"][task] = round(acc, 4)
                        det = self._drift_detectors.get(task)
                        if det is not None:
                            det.update(acc)
                            result["drift_alerts"][task] = bool(det.drift_detected)
                    except Exception:
                        result["per_task_accuracy"][task] = 0.0

            # Confidence score matrix: task_type → model → score
            try:
                from app.core.echo_model_orchestrator import MODEL_POOL
                models = list(MODEL_POOL.keys())
            except Exception:
                models = []

            for task in task_types:
                result["confidence_matrix"][task] = {}
                for model in models:
                    try:
                        score = rb.score_model(model, task)
                        result["confidence_matrix"][task][model] = round(score, 4)
                    except Exception:
                        result["confidence_matrix"][task][model] = 0.5

        except Exception as e:
            logger.warning("[Introspection] river_brain collect failed: %s", e)
        return result

    # ── Collector: ClaudeShard friction ───────────────────────────────

    def _collect_friction(self) -> dict:
        result = {
            "assessment_count_last_50": 0,
            "friction_count_last_50": 0,
            "friction_rate": 0.0,
            "avg_confidence": 0.0,
            "top_friction_questions": [],
        }
        try:
            from app.core.echo_model_orchestrator import _friction_window, _friction_lock
            with _friction_lock:
                window = list(_friction_window)

            result["assessment_count_last_50"] = len(window)
            friction_hits = [e for e in window if e.get("friction")]
            result["friction_count_last_50"] = len(friction_hits)
            result["friction_rate"] = round(
                len(friction_hits) / max(len(window), 1), 4
            )
            if friction_hits:
                result["avg_confidence"] = round(
                    sum(e.get("confidence", 0.0) for e in friction_hits)
                    / len(friction_hits),
                    4,
                )
            # Top 3 most-recent unique friction questions
            seen: list[str] = []
            for e in reversed(friction_hits):
                q = e.get("question", "").strip()
                if q and q not in seen:
                    seen.append(q)
                if len(seen) >= 3:
                    break
            result["top_friction_questions"] = seen

        except ImportError:
            logger.debug("[Introspection] _friction_window not yet available.")
        except Exception as e:
            logger.warning("[Introspection] friction collect failed: %s", e)
        return result

    # ── Collector: Sandbox success/failure ────────────────────────────

    def _collect_sandbox(self) -> dict:
        result = {
            "success_rate_last_50": 0.0,
            "total_attempts": 0,
            "failures_by_model": {},
            "most_common_failure": "",
        }
        try:
            log_path = os.path.join(self._memory_dir, "interaction_log.jsonl")
            if not os.path.exists(log_path):
                return result

            # Read last 200 lines; filter to sandbox entries; take last 50
            raw = _tail_jsonl(log_path, 200)
            sandbox_entries = [
                e for e in raw
                if e.get("sandbox_outcome") in ("success", "failed")
            ][-50:]

            if not sandbox_entries:
                return result

            result["total_attempts"] = len(sandbox_entries)
            successes = sum(
                1 for e in sandbox_entries
                if e.get("sandbox_outcome") == "success"
            )
            result["success_rate_last_50"] = round(
                successes / len(sandbox_entries), 4
            )

            failures = [
                e for e in sandbox_entries
                if e.get("sandbox_outcome") == "failed"
            ]
            by_model: dict[str, int] = defaultdict(int)
            for e in failures:
                by_model[e.get("model", "unknown")] += 1
            result["failures_by_model"] = dict(by_model)

            notes = [e.get("notes", "") for e in failures if e.get("notes")]
            if notes:
                result["most_common_failure"] = Counter(notes).most_common(1)[0][0]

        except Exception as e:
            logger.warning("[Introspection] sandbox collect failed: %s", e)
        return result

    # ── Collector: Memory health ───────────────────────────────────────

    def _collect_memory(self) -> dict:
        result = {
            "faiss_vector_count": 0,
            "journal_line_count": 0,
        }
        try:
            try:
                from app.core.memory_bridge import vector_memory
                idx = getattr(vector_memory, "index", None)
                meta = getattr(vector_memory, "meta", None)
                if idx is not None:
                    result["faiss_vector_count"] = int(idx.ntotal)
                    # Ongoing version of the load-time-only check in
                    # vector_memory.py's _load_or_rebuild_index() — that one
                    # only fires once, at process start. This repeats it on
                    # every introspection cycle so drift during a long-running
                    # process doesn't go unnoticed until the next restart.
                    if meta is not None and int(idx.ntotal) != len(meta):
                        logger.warning(
                            "[Introspection] FAISS/meta divergence: ntotal=%d meta=%d",
                            idx.ntotal, len(meta),
                        )
            except Exception:
                pass

            # Was reading memory_journal_active.log, which memory_bridge.py
            # intentionally truncates to 0 after each consolidation pass —
            # a different mechanism from the actual, ever-growing journal
            # memory_tools.py writes to (config.MEMORY_JOURNAL_FILE). This
            # produced a silently-wrong journal_line_count (confirmed 0 vs.
            # a real count in the thousands) that self_model_updater.py then
            # passed through into self_model.json with no cross-check.
            if os.path.exists(self._journal_file):
                with open(self._journal_file, "r", encoding="utf-8", errors="replace") as f:
                    result["journal_line_count"] = sum(1 for _ in f)

        except Exception as e:
            logger.warning("[Introspection] memory collect failed: %s", e)
        return result

    # ── Collector: Self-edit recency ──────────────────────────────────

    def _collect_self_edit(self) -> dict:
        result = {
            "hours_since_last_success": None,
            "last_success_prompt_preview": "",
            "success_rate": 0.0,
        }
        try:
            shard_path = os.path.join(self._memory_dir, "reflection_shard.jsonl")
            if not os.path.exists(shard_path):
                return result

            lines = _tail_lines(shard_path, 500)
            found_last_success = False
            edit_total = 0
            edit_success = 0

            for raw in reversed(lines):
                try:
                    entry = json.loads(raw)
                except Exception:
                    continue
                if not entry.get("generated_code"):
                    continue
                edit_total += 1
                if entry.get("result") == "success":
                    edit_success += 1
                    if not found_last_success:
                        found_last_success = True
                        ts_str = entry.get("timestamp", "")
                        try:
                            ts = datetime.fromisoformat(ts_str)
                            if ts.tzinfo is None:
                                ts = ts.replace(tzinfo=timezone.utc)
                            age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
                            result["hours_since_last_success"] = round(age_h, 2)
                            result["last_success_prompt_preview"] = entry.get("prompt", "")[:120]
                        except Exception:
                            pass

            if edit_total > 0:
                result["success_rate"] = round(edit_success / edit_total, 4)

        except Exception as e:
            logger.warning("[Introspection] self_edit collect failed: %s", e)
        return result

    # ── Collector: Optuna study health ────────────────────────────────

    def _collect_optuna(self) -> dict:
        result = {
            "total_trials": 0,
            "inf_trial_rate": 0.0,
            "best_value": None,
            "best_params": {},
        }
        try:
            study = None
            if self._core is not None:
                study = getattr(self._core, "optuna_study", None)

            if study is None:
                try:
                    import optuna
                    optuna.logging.set_verbosity(optuna.logging.WARNING)
                    study = optuna.load_study(
                        study_name="echo_self_edit",
                        storage="sqlite:///memory/optuna.db",
                    )
                except Exception:
                    return result

            trials = study.trials
            result["total_trials"] = len(trials)

            if trials:
                # Only scan the last 50 trials to keep this fast on large DBs
                recent = trials[-50:]
                inf_count = sum(
                    1 for t in recent
                    if t.value is None
                    or (isinstance(t.value, float) and math.isinf(t.value))
                )
                result["inf_trial_rate"] = round(inf_count / len(recent), 4)

                try:
                    best = study.best_trial
                    result["best_value"] = (
                        round(best.value, 6) if best.value is not None else None
                    )
                    result["best_params"] = best.params
                except ValueError:
                    # study.best_trial raises ValueError when no trial has finished
                    pass

        except Exception as e:
            logger.warning("[Introspection] optuna collect failed: %s", e)
        return result

    # ── Collector: Predictive loops ──────────────────────────────────────

    def _collect_predictive_loops(self) -> dict:
        """
        Reads the running WorldModel singleton for live surprise metrics.
        Falls back to reading prediction_log.jsonl tail when the model
        isn't initialized yet (e.g. on a slow cold start).
        """
        result = {
            "surprise_last": 0.0,
            "surprise_rolling_10": 0.0,
            "surprise_rolling_50": 0.0,
            "cycles_logged": 0,
            "topic_distribution": {},
        }
        try:
            from app.core.predictive_loop import get_world_model
            wm = get_world_model()
            if wm is not None:
                last, r10, r50 = wm.get_surprise()
                result["surprise_last"] = round(last, 4)
                result["surprise_rolling_10"] = round(r10, 4)
                result["surprise_rolling_50"] = round(r50, 4)
                result["cycles_logged"] = wm.cycles_logged()
                result["topic_distribution"] = wm.get_topic_distribution()
                return result

            # WorldModel not yet initialized — read log tail directly
            log_path = os.path.join(self._memory_dir, "prediction_log.jsonl")
            if not os.path.exists(log_path):
                return result
            with open(log_path, "r", encoding="utf-8") as f:
                lines = [l for l in f.readlines()[-50:] if l.strip()]
            records = []
            for line in lines:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
            if records:
                surprises = [r["surprise_F"] for r in records if "surprise_F" in r]
                result["surprise_last"] = round(surprises[-1], 4) if surprises else 0.0
                result["surprise_rolling_10"] = round(
                    float(sum(surprises[-10:]) / max(len(surprises[-10:]), 1)), 4
                )
                result["surprise_rolling_50"] = round(
                    float(sum(surprises) / max(len(surprises), 1)), 4
                )
                result["cycles_logged"] = len(records)
        except Exception as e:
            logger.warning("[Introspection] predictive_loops collect failed: %s", e)
        return result

    # ── Collector: System health ──────────────────────────────────────

    def _collect_system_health(self) -> dict:
        """
        RAM pressure, Ollama process liveness, and system load.
        These are the causal signals behind council timeout failures and
        empty responses that look like low quality to RiverBrain.
        """
        result = {
            "ram_used_gb": 0.0,
            "ram_available_gb": 0.0,
            "ram_pressure_pct": 0.0,
            "ollama_process_alive": False,
            "load_avg_1m": 0.0,
            "load_avg_5m": 0.0,
            "memory_dir_free_gb": 0.0,
        }
        try:
            import psutil
            mem = psutil.virtual_memory()
            result["ram_used_gb"] = round(mem.used / 1e9, 2)
            result["ram_available_gb"] = round(mem.available / 1e9, 2)
            result["ram_pressure_pct"] = round(mem.percent, 1)
            result["ollama_process_alive"] = any(
                "ollama" in (p.info.get("name") or "").lower()
                for p in psutil.process_iter(["name"])
            )
            load = psutil.getloadavg()
            result["load_avg_1m"] = round(load[0], 2)
            result["load_avg_5m"] = round(load[1], 2)
            result["memory_dir_free_gb"] = round(
                os.statvfs(self._memory_dir).f_bavail
                * os.statvfs(self._memory_dir).f_frsize
                / 1e9,
                1,
            )
        except Exception as e:
            logger.warning("[Introspection] system_health collect failed: %s", e)
            # Total collection failure is a genuinely unknown state, not a
            # healthy one — the pre-initialized 0.0 default above reads
            # identically to a perfectly idle system to any consumer
            # (notably system_guard.py's throttle, the one thing this
            # reading exists to feed), which previously meant a real
            # fail-open on the one signal a safety throttle depends on.
            result["ram_pressure_pct"] = None
        return result

    # ── Collector: Liveness ledger ─────────────────────────────────────

    def _collect_liveness_ledger(self, live_memory: dict) -> dict:
        """
        Runs the nine ground-truth liveness checks (see liveness_ledger.py)
        and writes memory/liveness_ledger.json. Returns a compact summary
        for inclusion in introspection_state.json itself, not the full
        ledger (that would duplicate liveness_ledger.json) — just enough
        that a caller reading only introspection_state.json still sees
        whether anything is failing, without a second file read.
        """
        result = {"all_passing": None, "failing_subsystems": []}
        try:
            from app.core.liveness_ledger import run_liveness_checks
            ledger = run_liveness_checks(live_memory)
            failing = [
                name for name, entry in ledger.items()
                if isinstance(entry, dict) and "pass" in entry and not entry["pass"]
            ]
            result["all_passing"] = not failing
            result["failing_subsystems"] = failing
        except Exception as e:
            logger.warning("[Introspection] liveness_ledger collect failed: %s", e)
        return result

    # ── Internal helpers ───────────────────────────────────────────────

    def _get_river_brain(self):
        if self._core is not None:
            rb = getattr(self._core, "river_brain", None)
            if rb is not None:
                return rb
        try:
            from app.core.echo_model_orchestrator import get_river_brain
            return get_river_brain()
        except Exception:
            return None

    def _write(self, state: dict):
        tmp = self._state_path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
            os.replace(tmp, self._state_path)
            logger.debug("[Introspection] Snapshot written.")
        except Exception as e:
            logger.warning("[Introspection] Write failed: %s", e)
            try:
                os.unlink(tmp)
            except Exception:
                pass


# ── File utilities ─────────────────────────────────────────────────────────


def _tail_lines(path: str, n: int) -> list:
    """Return the last n lines of a text file as a list of stripped strings."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return [ln.rstrip("\n") for ln in f.readlines()[-n:]]
    except Exception:
        return []


def _tail_jsonl(path: str, n: int) -> list:
    """Return up to n valid JSON objects from the tail of a .jsonl file."""
    raw = _tail_lines(path, n * 2)
    result = []
    for line in reversed(raw):
        try:
            result.append(json.loads(line))
        except Exception:
            pass
        if len(result) >= n:
            break
    return list(reversed(result))
