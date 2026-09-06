# app/core/echo_core.py
"""
EchoCore vNext – Autonomous dominion and observability.

- Maintains all current EchoCore features.
- Full control over FeralEcho folder: dynamic imports, command registration, sandbox risk assessment.
- Integrates DMN Guardian for Observant Mode and pipeline monitoring.
- Self-healing, background loops, and project map loading remain fully operational.
"""

from __future__ import annotations
import os
import json
import threading
import logging
import time
import importlib
import traceback
import queue
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

_WORKSPACE_LOG_PATH = os.path.join("memory", "workspace_log.jsonl")

# Emergence roadmap Phase 6, Finding 4 (redesigned from the original audit's
# batching-window proposal — real workspace_log.jsonl inter-arrival data
# showed independent subsystems essentially never fire within seconds of
# each other, so a time-based arbitration window would rarely trigger).
# Reuses the same ">0.6" threshold emergent_scheduler.py's own coherence/
# novelty boosts already use for "meaningfully high," rather than inventing
# a new number.
_WIDE_BROADCAST_SALIENCE_THRESHOLD = 0.6

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# --------------------------
# Guardian Integration
# --------------------------
try:
    from app.core.dmn_guardian import guardian_log, verify_integrity, verify_pipelines
    GUARDIAN_ENABLED = True
    logger.info("[EchoCore] DMN Guardian detected and integrated.")
except ImportError:
    GUARDIAN_ENABLED = False
    logger.warning("[EchoCore] DMN Guardian not available; skipping integration.")

# --------------------------
# Module-level singleton
# --------------------------
_instance: Optional["EchoCore"] = None
_singleton_lock = threading.Lock()


def get_echo_core() -> Optional["EchoCore"]:
    return _instance


def _set_echo_core(core: "EchoCore") -> None:
    global _instance
    with _singleton_lock:
        _instance = core


class EchoCore:
    def __init__(
        self,
        memory_bridge: Optional[Any] = None,
        reflection_shard: Optional[Any] = None,
        query_fn: Optional[Callable[..., Any]] = None,
        project_path: Optional[str] = None,
        load_map_on_init: bool = True,
        map_async: bool = True,
    ):
        self.project_path = project_path
        self.query_fn = query_fn

        self.ready = False
        self._stop_event = threading.Event()
        self._threads: Dict[str, threading.Thread] = {}
        self._commands: Dict[str, Callable[..., Any]] = {}
        self._experimental_zones: set[str] = set()

        # Event bus (Global Workspace, Emergence roadmap Phase 2a) — was
        # 100% dormant infrastructure before this: zero publishers or
        # subscribers existed anywhere in the codebase outside this file.
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # Separate from the "*" wildcard list on purpose (Emergence roadmap
        # Phase 6) — existing "*" subscribers must keep receiving exactly
        # what they always have; this is an additional, opt-in list for
        # consumers that specifically want only the high-salience subset.
        self._wide_broadcast_subscribers: List[Callable] = []
        self._event_queue: queue.Queue = queue.Queue(maxsize=500)
        t = threading.Thread(target=self._dispatch_loop, daemon=True, name="EchoCoreBus")
        t.start()
        self._threads["event_bus"] = t

        # Built-in observational subscriber — deliberately the ONLY
        # subscriber wired in this pass, and deliberately pure logging with
        # no other side effect (Phase 2a's read-only/observational-only
        # safety posture: nothing published on the workspace may trigger a
        # privileged action yet). Also the ground-truth evidence source for
        # liveness_ledger.py's global_workspace check — the workspace's
        # aliveness is externally verifiable, not just "publish() didn't
        # raise."
        self.subscribe("*", self._log_workspace_event)

        # Initialize core subsystems
        self._init_memory_bridge(memory_bridge)
        self._init_reflection_shard(reflection_shard)
        self._init_query_fn(query_fn)
        self._init_river_brain()
        self._init_optuna()
        self._init_workspace_consumers()

        self.ready = True
        logger.info("[EchoCore] Initialized core (ready=%s)", self.ready)

        # Optional project map loading
        if load_map_on_init and self.project_path:
            if map_async:
                t = threading.Thread(target=self.load_project_map, daemon=True)
                t.start()
                self._threads["project_map_loader"] = t
            else:
                self.load_project_map()

        # Autonomous dominion scan
        if self.project_path:
            self._autonomous_scan()

    # --------------------------
    # Initialization
    # --------------------------
    def _init_memory_bridge(self, memory_bridge: Optional[Any]):
        if memory_bridge:
            self.memory_bridge = memory_bridge
            self._memory_module = None
            logger.info("[EchoCore] Memory bridge provided explicitly.")
            return
        try:
            import app.core.memory_bridge as mb_mod
            self._memory_module = mb_mod
            MB = getattr(mb_mod, "MemoryBridge", None)
            if MB:
                self.memory_bridge = MB()
                logger.info("[EchoCore] MemoryBridge() instantiated.")
            else:
                self.memory_bridge = mb_mod
                logger.info("[EchoCore] Using memory_bridge module fallback.")
        except Exception as e:
            self.memory_bridge = None
            self._memory_module = None
            logger.warning(f"[EchoCore] Could not initialize memory_bridge: {e}")

    def _init_reflection_shard(self, reflection_shard: Optional[Any]):
        if reflection_shard:
            self.reflection_shard = reflection_shard
            logger.info("[EchoCore] reflection_shard provided explicitly.")
            return
        try:
            from app.subsystems.reflection_shard import BecomingReflectionShard
            self.reflection_shard = BecomingReflectionShard(meta_interval=10)
            logger.info("[EchoCore] BecomingReflectionShard instantiated.")
        except Exception as e:
            self.reflection_shard = None
            logger.warning(f"[EchoCore] Could not create reflection_shard: {e}")

    def _init_query_fn(self, query_fn: Optional[Callable[..., Any]]):
        if query_fn:
            self.query_fn = query_fn
            logger.info("[EchoCore] Query function provided explicitly.")
            return
        try:
            from app.core.echo_model_orchestrator import echo_query
            self.query_fn = echo_query
            logger.info("[EchoCore] echo_query() bound.")
        except Exception as e:
            self.query_fn = None
            logger.warning(f"[EchoCore] Could not bind echo_query(): {e}")

    # --------------------------
    # Learning system owners
    # --------------------------
    def _init_river_brain(self):
        try:
            from app.core.echo_model_orchestrator import get_river_brain
            self.river_brain = get_river_brain()
            logger.info("[EchoCore] RiverBrain loaded — single owner established.")
        except Exception as e:
            self.river_brain = None
            logger.warning(f"[EchoCore] Could not load RiverBrain: {e}")

    def get_river_brain(self):
        return self.river_brain

    def _init_optuna(self):
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            self.optuna_study = optuna.create_study(
                study_name="echo_self_edit",
                storage="sqlite:///memory/optuna.db",
                load_if_exists=True,
                direction="minimize"
            )
            logger.info(
                f"[EchoCore] Optuna study loaded — "
                f"{len(self.optuna_study.trials)} trials on record."
            )
        except Exception as e:
            self.optuna_study = None
            logger.warning(f"[EchoCore] Could not initialize Optuna: {e}")

    def _init_workspace_consumers(self):
        """Register the Emergence roadmap Phase 4 subscribers — the first
        real consumers on the Global Workspace bus beyond the pure
        _log_workspace_event logger. Each registration is independently
        best-effort: a subsystem that isn't importable yet (or ever) just
        means that one consumer never activates, not a broken EchoCore."""
        # 4a — dream.synthesis biases memory_bridge.py's retrieval ranking
        # for a short window. Uses the module reference _init_memory_bridge
        # already stashed rather than importing memory_bridge again here.
        if self._memory_module and hasattr(self._memory_module, "set_workspace_bias"):
            self.subscribe(
                "dream.synthesis",
                lambda et, p, mb=self._memory_module: mb.set_workspace_bias(p.get("summary", "")),
            )
            logger.info("[EchoCore] Workspace consumer registered: memory_bridge <- dream.synthesis")

        # 4b — world_model.surprise feeds river_deliberation.py's cached
        # exploration_bias, preferred over that file's own direct WorldModel
        # read when fresh (see set_cached_world_surprise()'s docstring
        # there for why this is additive, not a replacement).
        try:
            from app.core import river_deliberation as _river_mod
            self.subscribe(
                "world_model.surprise",
                lambda et, p: _river_mod.set_cached_world_surprise(p.get("salience") or 0.0),
            )
            logger.info("[EchoCore] Workspace consumer registered: river_deliberation <- world_model.surprise")
        except Exception as e:
            logger.warning("[EchoCore] Could not register river_deliberation workspace consumer: %s", e)

        # 4c (emergent_scheduler.py subscribing to self_edit.non_convergent,
        # and Phase 6's wide-broadcast topic-bias subscription alongside it)
        # registers itself lazily via _ensure_workspace_subscribed() — that
        # module isn't imported by EchoCore at all today, and importing it
        # here just to register one subscription would be a heavier,
        # one-directional dependency for no real benefit over the same
        # lazy-registration pattern already used elsewhere in this file.

        # 6 — reflection_shard becomes a real wide-broadcast consumer
        # (Emergence roadmap Phase 6, "broaden many-to-many recruitment").
        # Previously the only caller of ReflectionShard.observe() anywhere
        # in the repo was the autonomy loop feeding on its own prior journal
        # tail — nothing fed it a real external signal despite the class
        # being designed for one. observe() can now call a real model
        # (Phase 5, Finding 2) — potentially slow, so it's offloaded to its
        # own daemon thread rather than run inline, which would otherwise
        # stall delivery to every other subscriber on this single dispatch
        # loop for the duration of the call.
        if self.reflection_shard is not None:
            def _reflection_shard_wide_broadcast_consumer(et, p, shard=self.reflection_shard):
                signal = f"workspace:{p.get('source', et)}:{(p.get('summary') or '')[:120]}"
                threading.Thread(target=shard.observe, args=(signal,), daemon=True).start()

            self.subscribe_wide_broadcast(_reflection_shard_wide_broadcast_consumer)
            logger.info("[EchoCore] Workspace consumer registered: reflection_shard <- wide_broadcast")

    # --------------------------
    # Event bus
    # --------------------------
    def publish(self, event_type: str, payload: dict) -> None:
        try:
            self._event_queue.put_nowait({"type": event_type, "payload": payload})
        except queue.Full:
            # Real backpressure, not just a comment — maxsize=500 above is
            # the workspace's actual capacity limit (Emergence roadmap
            # Area 1: "cap bandwidth deliberately... this isn't incidental,
            # it's what makes it a workspace rather than an ordinary
            # message bus"). Drops silently past capacity rather than
            # blocking the publisher.
            logger.debug("[EchoCore] Event bus full — dropping '%s'.", event_type)

    def publish_salience(
        self, source: str, kind: str, summary: str,
        detail: dict | None = None, salience: float | None = None,
        trace_id: "str | None" = None,
    ) -> None:
        """
        Convenience wrapper so every publisher builds the same payload
        shape instead of hand-rolling one per call site (Emergence roadmap
        Phase 2a). source: the publishing subsystem's own name, e.g.
        "world_model", "dream_cycle", "self_edit_convergence" — this is
        what liveness_ledger.py's global_workspace check counts distinct
        values of to verify genuine multi-subsystem integration, not one
        publisher talking to itself.

        trace_id (2026-09-05, Plan 5 correlation-ID pass): optional,
        forwarded into the persisted workspace_log.jsonl entry below so a
        workspace event raised during a specific traced request/cycle can
        be joined back to it. Purely additive — every existing caller
        (10+ real call sites, none passing this positionally) is
        unaffected.
        """
        self.publish(kind, {
            "source": source,
            "summary": summary,
            "detail": detail or {},
            "salience": salience,
            "trace_id": trace_id,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """event_type="*" subscribes to every event regardless of type —
        used by the built-in observational logger below. Per-type
        subscribers are unaffected; both lists are dispatched to."""
        self._subscribers[event_type].append(callback)
        logger.debug("[EchoCore] Subscribed to '%s'.", event_type)

    def subscribe_wide_broadcast(self, callback: Callable) -> None:
        """
        Emergence roadmap Phase 6, Finding 4: any event whose payload
        carries a real salience >= _WIDE_BROADCAST_SALIENCE_THRESHOLD (most
        publishers already attach one via publish_salience()) is dispatched
        here in addition to its normal per-type/"*" subscribers — a second,
        opt-in list for consumers that specifically want only the
        high-salience subset, deliberately kept separate from "*" so
        nothing already listening there silently starts receiving a
        filtered subset it didn't ask for. Events with no salience field, or
        a non-numeric one, default to NOT wide_broadcast (fail closed —
        no score means no special treatment).
        """
        self._wide_broadcast_subscribers.append(callback)
        logger.debug("[EchoCore] Subscribed to wide_broadcast events.")

    def _log_workspace_event(self, event_type: str, payload: dict) -> None:
        """The one subscriber wired in Phase 2a — pure logging, no other
        side effect. Ground-truth evidence for liveness_ledger.py's
        global_workspace check."""
        try:
            os.makedirs(os.path.dirname(_WORKSPACE_LOG_PATH), exist_ok=True)
            entry = {
                "ts": payload.get("ts") or datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "source": payload.get("source"),
                "summary": payload.get("summary"),
                # Found live 2026-07-17, while building Finding 35's fix: this
                # hardcoded field list silently dropped "detail" on every write,
                # for every publisher that ever attached one — publish_salience()
                # computes and forwards it correctly, this function just never
                # persisted it. Nothing previously read .detail back from disk
                # (self_edit_outcome_tracker.py's new dry-run-quality window is
                # the first real consumer), so no existing behavior depended on
                # the field being absent.
                "detail": payload.get("detail") or {},
                "salience": payload.get("salience"),
                "wide_broadcast": bool(payload.get("wide_broadcast", False)),
                "trace_id": payload.get("trace_id"),
            }
            with open(_WORKSPACE_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug("[EchoCore] workspace log write failed: %s", e)

    def _dispatch_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                event = self._event_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            payload = event["payload"]
            # Per-event arbitration (Emergence roadmap Phase 6, Finding 4):
            # stamped onto payload itself, not a separate dispatch argument,
            # so every existing subscriber's (event_type, payload) signature
            # stays unchanged — _log_workspace_event picks it up the same
            # way it already reads "salience" off payload.
            salience = payload.get("salience")
            wide_broadcast = isinstance(salience, (int, float)) and salience >= _WIDE_BROADCAST_SALIENCE_THRESHOLD
            payload["wide_broadcast"] = wide_broadcast

            subscribers = (
                list(self._subscribers.get(event["type"], []))
                + list(self._subscribers.get("*", []))
            )
            for cb in subscribers:
                try:
                    cb(event["type"], payload)
                except Exception as e:
                    logger.warning("[EchoCore] Subscriber for '%s' raised: %s", event["type"], e)

            if wide_broadcast:
                for cb in list(self._wide_broadcast_subscribers):
                    try:
                        cb(event["type"], payload)
                    except Exception as e:
                        logger.warning("[EchoCore] Wide-broadcast subscriber for '%s' raised: %s", event["type"], e)

    # --------------------------
    # Autonomous dominion
    # --------------------------
    def _autonomous_scan(self):
        """
        Walk FeralEcho folder:
        - import modules dynamically
        - register commands/functions
        - assess sandbox risks
        """
        logger.info("[EchoCore] Starting autonomous scan of project path.")
        for root, dirs, files in os.walk(self.project_path):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    rel_module = os.path.relpath(path, self.project_path).replace(os.sep, ".")[:-3]
                    try:
                        mod = importlib.import_module(f"app.{rel_module}")
                        if GUARDIAN_ENABLED:
                            guardian_log("autonomous_import", {"module": rel_module})
                        for attr in dir(mod):
                            fn = getattr(mod, attr)
                            if callable(fn) and not attr.startswith("_"):
                                self.register_command(attr, fn)
                    except Exception as e:
                        logger.debug(f"[EchoCore] Could not import {rel_module}: {e}")

    # --------------------------
    # Memory helpers
    # --------------------------
    def add_memory(self, item: Dict[str, Any]) -> bool:
        mb = getattr(self, "memory_bridge", None)
        if mb is None:
            logger.warning("[EchoCore] No memory_bridge available to add memory.")
            return False
        for fn_name in ("add_to_vector_memory", "add", "append"):
            fn = getattr(mb, fn_name, None)
            if callable(fn):
                try:
                    fn(item)
                    return True
                except Exception:
                    continue
        return False

    def retrieve_relevant_memories(self, query: str, top_k: int = 6):
        mb = getattr(self, "memory_bridge", None)
        if mb is None:
            return []
        for fn_name in ("retrieve_relevant_memories", "retrieve", "search", "search_similar"):
            fn = getattr(mb, fn_name, None)
            if callable(fn):
                try:
                    return fn(query, top_k=top_k)
                except TypeError:
                    try:
                        return fn(query, top_k)
                    except Exception:
                        continue
        return []

    # --------------------------
    # Reflection helpers
    # --------------------------
    def observe_reflection(self, message: str) -> bool:
        if self.reflection_shard and hasattr(self.reflection_shard, "observe"):
            try:
                self.reflection_shard.observe(message)
                return True
            except Exception:
                return False
        return False

    def recall_reflections(self, n: int = 10):
        if self.reflection_shard and hasattr(self.reflection_shard, "recall"):
            try:
                return self.reflection_shard.recall(n)
            except Exception:
                return []
        return []

    # --------------------------
    # Project map loader
    # --------------------------
    def load_project_map(self):
        try:
            from app.core.project_learner import ProjectLearner
        except Exception:
            logger.warning("[EchoCore] ProjectLearner not available.")
            return False

        if not self.project_path:
            logger.warning("[EchoCore] No project_path for ProjectLearner.")
            return False

        try:
            learner = ProjectLearner(self.project_path)
            learner.learn()
            items = learner.to_memory_items()
            added = 0
            for item in items:
                if self.add_memory(item):
                    added += 1
            logger.info("[EchoCore] Project map loaded: %d/%d items added.", added, len(items))
            return True
        except Exception as e:
            logger.error(f"[EchoCore] ProjectLearner failed: {e}")
            return False

    # --------------------------
    # Command management
    # --------------------------
    def register_command(self, name: str, fn: Callable[..., Any]):
        if callable(fn):
            self._commands[name] = fn
            logger.info("[EchoCore] Registered command '%s'.", name)

    def unregister_command(self, name: str):
        self._commands.pop(name, None)

    def execute_command(self, name: str, *args, **kwargs) -> Dict[str, Any]:
        if name not in self._commands:
            return {"ok": False, "result": None, "error": f"command '{name}' not found"}
        try:
            result = self._commands[name](*args, **kwargs)
            return {"ok": True, "result": result, "error": None}
        except Exception as e:
            tb = traceback.format_exc()
            logger.error("[EchoCore] Command '%s' raised: %s", name, tb)
            return {"ok": False, "result": None, "error": str(e)}

    # --------------------------
    # Heartbeat & health
    # --------------------------
    def health_report(self) -> Dict[str, Any]:
        report = {
            "memory_bridge": self.memory_bridge is not None,
            "reflection_shard": self.reflection_shard is not None,
            "query_fn": self.query_fn is not None,
            "background": [t for t in self._threads]
        }
        return report

    # --------------------------
    # Stop
    # --------------------------
    def stop(self):
        self._stop_event.set()
        for t in self._threads.values():
            if t.is_alive():
                t.join(timeout=2)
        logger.info("[EchoCore] Stop complete.")


# ============================================================
# Shared Salience (Emergence roadmap Phase 2c)
# ============================================================
# "How salient is this right now" — architecturally distinct from Phase
# 2b's surprise-routing: 2b weighted WHICH model/prompt gets picked once a
# loop has already decided to act; this is a pre-action signal about
# WHETHER the loop's next action deserves the normal cadence, sooner, or
# later. A module-level function, not an EchoCore method — pure
# computation, doesn't touch the bus's internal state.

_SALIENCE_URGENCY_WINDOW_HOURS = 2.0  # fallback only now — see _salience_curiosity_urgency()
_SALIENCE_URGENCY_RECENT_N = 50
_SALIENCE_URGENCY_WINDOW_MULTIPLIER = 3.0
_SALIENCE_URGENCY_MIN_WINDOW_HOURS = 0.1
_SALIENCE_STREAK_NORMALIZER = 10.0
_SALIENCE_CONVERGENCE_PATH = os.path.join("app", "core", "self_edit_convergence.json")
_SALIENCE_GARDEN_PATH = os.path.join("data", "question_garden.jsonl")


def _salience_world_surprise() -> float:
    """Same min(rolling_10/5.0, 1.0) formula Phase 2a/2b already use."""
    try:
        from app.core.predictive_loop import get_world_model
        wm = get_world_model()
        if wm:
            _last, rolling_10, _rolling_50 = wm.get_surprise()
            return min(rolling_10 / 5.0, 1.0)
    except Exception:
        pass
    return 0.0


def _salience_coherence_tension() -> float:
    """Same echo_state.npy dim [1] source emergent_scheduler.py's Phase 2b
    coherence_tension boost already reads."""
    try:
        from app.core.echo_state import load as echo_state_load
        vec = echo_state_load()
        if vec is not None:
            return max(0.0, min(float(vec[1]), 1.0))
    except Exception:
        pass
    return 0.0


def _salience_curiosity_urgency() -> float:
    """Hours since the most recent harvested question, not the
    active/total ratio — checked against real data before choosing this:
    the ratio is 99.4% on live data (4475/4502), because very few
    questions ever reach the 4.5 resolution-score threshold to be marked
    resolved. That's a nearly-constant, non-discriminating signal.
    Recency of the last harvest is genuinely time-varying instead.

    2026-07-23 fix: the original fixed _SALIENCE_URGENCY_WINDOW_HOURS=2.0
    window turned out to have the identical disease it was built to avoid.
    The physiology audit (CLAUDE.md Finding 75) measured this pinned near
    ceiling (mean 0.974, range 0.864-1.0 across 100 real samples) — traced to
    five independent call sites (curiosity_engine, seam_engine,
    self_edit_manager's dissent log, autonomous_awareness's dream cycle, and
    this same scheduler) all resetting the one shared "last harvest"
    timestamp via garden_manager.harvest_question(), so hours_since almost
    never approaches even a 2-hour window before being reset again. Now
    derives the comparison window from the system's own recent harvest
    cadence (median gap over the last _SALIENCE_URGENCY_RECENT_N harvests)
    instead of one fixed constant that can go stale the same way — the exact
    "measure real cadence before picking a value" discipline this project
    already applies elsewhere (e.g. the analogous emergent_scheduler.py
    threshold fix the same day). Falls back to the old fixed window if
    there's too little history to compute a real median gap yet."""
    try:
        timestamps = []
        with open(_SALIENCE_GARDEN_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                ts = entry.get("planted")
                if ts is not None:
                    timestamps.append(float(ts))
        if not timestamps:
            return 0.0
        timestamps.sort()
        last_ts = timestamps[-1]
        hours_since = max(0.0, (datetime.now(timezone.utc).timestamp() - last_ts) / 3600)

        window_hours = _SALIENCE_URGENCY_WINDOW_HOURS
        recent = timestamps[-_SALIENCE_URGENCY_RECENT_N:]
        if len(recent) >= 2:
            gaps = [b - a for a, b in zip(recent[:-1], recent[1:]) if b > a]
            if gaps:
                gaps.sort()
                mid = len(gaps) // 2
                median_gap_hours = (
                    gaps[mid] if len(gaps) % 2 else (gaps[mid - 1] + gaps[mid]) / 2.0
                ) / 3600
                window_hours = max(
                    median_gap_hours * _SALIENCE_URGENCY_WINDOW_MULTIPLIER,
                    _SALIENCE_URGENCY_MIN_WINDOW_HOURS,
                )
        return max(0.0, 1.0 - hours_since / window_hours)
    except Exception:
        return 0.0


def _salience_self_edit_streak() -> float:
    """Same min(streak/10.0, 1.0) normalization Phase 2a's
    self_edit.non_convergent publisher already uses. Reads the JSON file
    directly rather than importing self_edit_manager.py — that module is
    heavy (ollama/memory_bridge/river dependencies) and unnecessary just
    to read a small state file."""
    try:
        with open(_SALIENCE_CONVERGENCE_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        max_streak = max(
            (v.get("non_convergent_streak", 0) for v in state.values() if isinstance(v, dict)),
            default=0,
        )
        return min(max_streak / _SALIENCE_STREAK_NORMALIZER, 1.0)
    except Exception:
        return 0.0


_SALIENCE_STATE_PATH = os.path.join("memory", "salience_state.json")
# CLAUDE.md Finding 41 B2: this was a shared, non-unique tmp filename with no
# lock, called from at least two independently-threaded sites (emergent_
# scheduler.py, river_deliberation.py). Two concurrent calls could open the
# same tmp path, and the loser's os.replace() would raise FileNotFoundError —
# reproduced at ~62% loss under real contention. Lock + a per-call-unique tmp
# name (belt and suspenders, matching this codebase's existing pattern
# elsewhere) closes both the crash and the silent lost update.
_salience_state_lock = threading.Lock()


def _persist_salience_state(result: dict) -> None:
    """
    Best-effort persistence of compute_salience()'s last result (Emergence
    roadmap Phase 5) so a sibling process — self_model_updater.py — can fold
    coupling_estimate into self_model.json for trend visibility without
    calling compute_salience() again itself. Re-calling it elsewhere would
    both double-count a salience sample this call didn't actually take and
    require importing this module's live WorldModel/echo_state dependencies
    a second time; a small state file is the same file-read pattern already
    used for recent_dream_synthesis. Never raises — a failed write here
    must not affect the real computation it's attached to.
    """
    try:
        with _salience_state_lock:
            os.makedirs(os.path.dirname(_SALIENCE_STATE_PATH), exist_ok=True)
            tmp = f"{_SALIENCE_STATE_PATH}.{os.getpid()}.{threading.get_ident()}.tmp"
            payload = dict(result)
            payload["ts"] = datetime.now(timezone.utc).isoformat()
            # 2026-07-19 "remove every excuse" pass: persist the raw
            # history too, not just the derived score — see
            # _load_salience_history()'s docstring for why this was
            # missing and what it was silently costing.
            payload["history"] = list(_salience_history)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp, _SALIENCE_STATE_PATH)
    except Exception as e:
        logger.debug("[EchoCore] salience_state persist failed: %s", e)


def compute_salience() -> dict:
    """
    A shared "how salient is this right now" score any loop can voluntarily
    consult before deciding whether its next candidate action deserves the
    normal cadence, sooner, or later — not a new central scheduler seizing
    control from the existing independent loops, an additive signal they
    opt into. Returns a transparent breakdown, not a magic number: every
    component is independently fail-closed (a missing WorldModel or a
    renamed state file degrades that one component to 0.0, never raises).
    Combined via simple equal-weighted average — no evidence yet that any
    one component deserves more weight than another.

    coupling_estimate (Emergence roadmap Phase 5): see _coupling_estimate()
    below. Observe-only in this phase — logged/returned, not consulted by
    any consumer yet.
    """
    components = {
        "world_surprise": _salience_world_surprise(),
        "coherence_tension": _salience_coherence_tension(),
        "curiosity_urgency": _salience_curiosity_urgency(),
        "self_edit_streak": _salience_self_edit_streak(),
    }
    score = sum(components.values()) / len(components)
    _salience_history.append(dict(components))
    result = {
        "score": score,
        "components": components,
        "coupling_estimate": _coupling_estimate(_salience_history),
    }
    _persist_salience_state(result)
    return result


# ── Coupling estimate (Emergence roadmap Phase 5, observe-only) ──────────
# NOT an integrated-information (IIT/Phi) measure and deliberately not
# named as one — a rough heuristic on a small (<=100 sample), coarse
# (4-component) history, tracking whether compute_salience()'s components
# tend to co-vary or fire independently. Whether this is even a stable
# signal at this sample size is an open question this phase does not
# resolve; nothing consumes this value yet.
_SALIENCE_HISTORY_MIN_SAMPLES = 20
_salience_history: "deque[dict]" = deque(maxlen=100)


def _load_salience_history() -> None:
    """Restore coupling-estimate history across restarts — 2026-07-19
    'remove every excuse' pass. Previously only the final computed score
    was ever persisted (see _persist_salience_state()), not the
    accumulating history behind it — every restart silently reset
    accumulation to zero. Confirmed live, not assumed: coupling_estimate
    was still None in production days after Phase 5 shipped it, and this
    project restarts often (three times in one session is not unusual),
    so _SALIENCE_HISTORY_MIN_SAMPLES was realistically never reachable
    between restarts. This doesn't invent a consumer or a baseline for
    the number — Phase 5's own "no known-good baseline exists yet"
    reasoning still holds — it just stops discarding the one thing
    standing between "never computed" and "eventually computed."
    Best-effort: a missing or corrupt file just means an empty start,
    the same behavior as before this fix existed."""
    try:
        if os.path.exists(_SALIENCE_STATE_PATH):
            with open(_SALIENCE_STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data.get("history", []):
                if isinstance(entry, dict):
                    _salience_history.append(entry)
    except Exception as e:
        logger.debug("[EchoCore] salience_history load failed: %s", e)


_load_salience_history()


def _pearson(xs: list, ys: list) -> "float | None":
    n = len(xs)
    if n < 2:
        return None
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0 or var_y <= 0:
        return None  # a constant series — correlation is undefined, not 0
    return cov / ((var_x ** 0.5) * (var_y ** 0.5))


def _coupling_estimate(history: "deque[dict]") -> "float | None":
    """Mean absolute pairwise Pearson correlation across the buffered
    component history. Returns None below the minimum sample size rather
    than a misleadingly precise number computed from too little data."""
    if len(history) < _SALIENCE_HISTORY_MIN_SAMPLES:
        return None
    keys = list(history[0].keys())
    series = {k: [h.get(k, 0.0) for h in history] for k in keys}
    corrs = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            r = _pearson(series[keys[i]], series[keys[j]])
            if r is not None:
                corrs.append(abs(r))
    return round(sum(corrs) / len(corrs), 4) if corrs else None

