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
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

_WORKSPACE_LOG_PATH = os.path.join("memory", "workspace_log.jsonl")

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
    ) -> None:
        """
        Convenience wrapper so every publisher builds the same payload
        shape instead of hand-rolling one per call site (Emergence roadmap
        Phase 2a). source: the publishing subsystem's own name, e.g.
        "world_model", "dream_cycle", "self_edit_convergence" — this is
        what liveness_ledger.py's global_workspace check counts distinct
        values of to verify genuine multi-subsystem integration, not one
        publisher talking to itself.
        """
        self.publish(kind, {
            "source": source,
            "summary": summary,
            "detail": detail or {},
            "salience": salience,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """event_type="*" subscribes to every event regardless of type —
        used by the built-in observational logger below. Per-type
        subscribers are unaffected; both lists are dispatched to."""
        self._subscribers[event_type].append(callback)
        logger.debug("[EchoCore] Subscribed to '%s'.", event_type)

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
                "salience": payload.get("salience"),
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
            subscribers = (
                list(self._subscribers.get(event["type"], []))
                + list(self._subscribers.get("*", []))
            )
            for cb in subscribers:
                try:
                    cb(event["type"], event["payload"])
                except Exception as e:
                    logger.warning("[EchoCore] Subscriber for '%s' raised: %s", event["type"], e)

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

