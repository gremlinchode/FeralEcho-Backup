# Self-Heal Event Bus Integration Plan

## Current State Summary

`app/core/self_heal.py` is a vestigial API-signature patcher. Its three functions
(`repair_append_to_journal`, `repair_memory_bridge`, `repair_vector_memory_index`)
stub missing Python object attributes — a bootstrapping concern from early development
that no longer applies to the mature codebase. Nothing in the live system imports or
starts it. `run_self_healing_background` is defined but never called. The only caller,
`archive_janitor/feralecho_continuity_master.py`, calls `self_heal.attempt_repairs()`
which doesn't exist in the file — it would crash on first use.

The EchoCore event bus (`publish` / `subscribe` / `_dispatch_loop`) is live and ready.
The missing half is the publishing side: errors across the system are logged but never
emitted as events.

---

## Phase 1 — Define the Event Taxonomy

Establish these event type strings as constants in a new file
`app/core/health_events.py`. Centralising them prevents string-literal drift and
makes the subscription list in SelfHealMonitor self-documenting.

```
deliberation.councillor_timeout       model timed out during council query
deliberation.councillor_error         model returned an error string
deliberation.all_councillors_failed   every councillor in a council errored
deliberation.synthesis_failed         echo synthesis returned empty/error

river_brain.save_failed               pkl write raised an exception
river_brain.writer_error              writer loop caught an unexpected exception
river_brain.lock_stale                .lock file is older than 60s (stuck lock)

ollama.model_list_failed              `ollama list` subprocess call failed
ollama.probe_failed                   test query to Ollama daemon got no response

memory.journal_write_failed           append_to_journal raised an exception
memory.embedding_failed               SentenceTransformers encode() failed
memory.faiss_mismatch                 FAISS vector count != metadata entry count
memory.retrieval_failed               retrieve_memories raised an exception

echo_core.thread_died                 a monitored background thread is no longer alive
echo_core.subsystem_init_failed       a subsystem failed to initialize on startup
```

Each payload is a plain dict. Shape for each:

```python
"deliberation.councillor_timeout"  → {"model": str, "task_type": str}
"deliberation.councillor_error"    → {"model": str, "task_type": str, "error": str}
"deliberation.all_councillors_failed" → {"task_type": str, "council_size": int}
"deliberation.synthesis_failed"    → {"task_type": str, "council_size": int}
"river_brain.save_failed"          → {"error": str}
"river_brain.writer_error"         → {"error": str}
"river_brain.lock_stale"           → {"lock_path": str, "age_seconds": float}
"ollama.model_list_failed"         → {"error": str}
"ollama.probe_failed"              → {"error": str}
"memory.journal_write_failed"      → {"file_path": str, "error": str}
"memory.embedding_failed"          → {"error": str}
"memory.faiss_mismatch"            → {"vector_count": int, "meta_count": int}
"memory.retrieval_failed"          → {"error": str}
"echo_core.thread_died"            → {"thread_name": str}
"echo_core.subsystem_init_failed"  → {"subsystem": str, "error": str}
```

---

## Phase 2 — Wire publish() at Error Sites

All publish calls follow the same pattern:

```python
from app.core.health_events import EVT_<NAME>   # the constant string
from app.core.echo_core import get_echo_core
if core := get_echo_core():
    core.publish(EVT_<NAME>, {...})
```

`get_echo_core()` returns None before Flask is up, so publish calls are safe to
add unconditionally — they are no-ops during import and unit tests.

### app/core/river_deliberation.py

**Line 123** — empty response sentinel
```python
# after: return f"[ERROR] Empty response from {model_name}"
if core := get_echo_core():
    core.publish(EVT_COUNCILLOR_ERROR, {"model": model_name, "task_type": "unknown", "error": "empty_response"})
```

**Lines 139–140** — councillor timeout
```python
# after: logging.warning(f"[DELIBERATION] Timeout querying {model_name}")
if core := get_echo_core():
    core.publish(EVT_COUNCILLOR_TIMEOUT, {"model": model_name, "task_type": "unknown"})
```
(task_type isn't in scope at `_ollama_query` — pass it as an optional arg added to the
`_ollama_query` signature, defaulting to `"unknown"`, filled in by `deliberate_and_learn`.)

**Lines 142–143** — CalledProcessError
```python
if core := get_echo_core():
    core.publish(EVT_COUNCILLOR_ERROR, {"model": model_name, "task_type": "unknown", "error": e.stderr.strip()})
```

**Lines 292–294** — all councillors failed fallback
```python
# after: logging.warning("[DELIBERATION] All councillors errored — falling back to direct Echo query")
if core := get_echo_core():
    core.publish(EVT_ALL_COUNCILLORS_FAILED, {"task_type": task_type, "council_size": len(council)})
```

**Lines 319–320** — synthesis failed fallback
```python
# after: logging.warning("[DELIBERATION] Synthesis failed — returning best single council response")
if core := get_echo_core():
    core.publish(EVT_SYNTHESIS_FAILED, {"task_type": task_type, "council_size": len(valid_opinions)})
```

### app/core/echo_model_orchestrator.py (RiverBrain)

**Lines 547–549** — writer loop exception (`_writer_loop`)
```python
# after: logging.warning(f"[RIVER-WRITER] Writer loop error: {e}")
if core := get_echo_core():
    core.publish(EVT_RIVER_WRITER_ERROR, {"error": str(e)})
```

**Lines 573–574** — stale lock detection is implicit here; add an explicit stale-lock
check before the `fcntl.LOCK_EX` acquire in `_do_save`:
```python
lock_age = time.time() - os.path.getmtime(lock_path) if os.path.exists(lock_path) else 0
if lock_age > 60:
    if core := get_echo_core():
        core.publish(EVT_RIVER_LOCK_STALE, {"lock_path": lock_path, "age_seconds": lock_age})
```

**Lines 587–588** — brain save failed
```python
# after: logging.warning(f"[RIVER] Brain save failed: {e}")
if core := get_echo_core():
    core.publish(EVT_RIVER_SAVE_FAILED, {"error": str(e)})
```

**Lines 382–384** — `list_ollama_models` subprocess failure
```python
# after: print(f"[ERROR] Could not list Ollama models: {e.stderr}")
if core := get_echo_core():
    core.publish(EVT_OLLAMA_LIST_FAILED, {"error": e.stderr.strip()})
```

### app/core/memory_bridge.py

**Lines 119–120** — journal write failure
```python
# after: logging.error(f"Failed to append to journal {file_path}: {e}")
if core := get_echo_core():
    core.publish(EVT_JOURNAL_WRITE_FAILED, {"file_path": file_path, "error": str(e)})
```

**Lines 173–174** — embedding generation failure
```python
# after: logging.error(f"Embedding generation failed: {e}")
if core := get_echo_core():
    core.publish(EVT_EMBEDDING_FAILED, {"error": str(e)})
```

**Line 216** — FAISS embedding count mismatch (first occurrence)
```python
# after: logging.warning("Embedding count mismatch; skipping vector memory add.")
if core := get_echo_core():
    core.publish(EVT_FAISS_MISMATCH, {"vector_count": -1, "meta_count": -1})
    # fill in actual counts from local context when adding the publish call
```

**Lines 296–297** — retrieval failure
```python
# after: logging.error(f"Failed to retrieve memories: {e}")
if core := get_echo_core():
    core.publish(EVT_RETRIEVAL_FAILED, {"error": str(e)})
```

### app/core/echo_core.py

**EchoCore init failures (lines 134, 147, 160, 172, 193, 202)** — each `logger.warning`
for a failed subsystem init should also publish. Since `publish` requires a running core
and we're inside `__init__`, use a deferred list:

```python
# In __init__, after all _init_* calls:
for subsystem, error in self._init_failures:   # populated by each _init_* on except
    self.publish(EVT_SUBSYSTEM_INIT_FAILED, {"subsystem": subsystem, "error": error})
```

Each `_init_*` method appends to `self._init_failures = []` in its except block before
the existing `logger.warning`.

---

## Phase 3 — Thread Watchdog in EchoCore

Add a `_thread_watchdog_loop` method that runs every 30 seconds and publishes
`echo_core.thread_died` for any thread in `self._threads` that is no longer alive.
This is the only way to detect silent thread death without polling from outside.

```python
def _thread_watchdog_loop(self):
    while not self._stop_event.is_set():
        for name, t in list(self._threads.items()):
            if not t.is_alive():
                logger.warning("[EchoCore] Thread '%s' is dead.", name)
                self.publish(EVT_THREAD_DIED, {"thread_name": name})
        time.sleep(30)
```

Register it in `__init__` after the heartbeat thread:
```python
t = threading.Thread(target=self._thread_watchdog_loop, daemon=True, name="EchoCoreWatchdog")
t.start()
self._threads["thread_watchdog"] = t
# Note: thread_watchdog must NOT be in self._threads before the loop starts,
# or it will immediately report itself dead on the first tick. Add it after start().
```

---

## Phase 4 — Rewrite self_heal.py as SelfHealMonitor

Replace the existing file entirely. Keep `repair_vector_memory_index` — it is the one
repair function that is genuinely still useful. Drop `repair_append_to_journal` and
`repair_memory_bridge` — both patch stubs for API mismatches that no longer exist.

```python
# app/core/self_heal.py

import logging
import shutil
import os
import json
import time
import subprocess
import threading
from collections import defaultdict

from app.core.health_events import (
    EVT_COUNCILLOR_TIMEOUT, EVT_COUNCILLOR_ERROR,
    EVT_ALL_COUNCILLORS_FAILED, EVT_SYNTHESIS_FAILED,
    EVT_RIVER_SAVE_FAILED, EVT_RIVER_WRITER_ERROR, EVT_RIVER_LOCK_STALE,
    EVT_OLLAMA_LIST_FAILED, EVT_OLLAMA_PROBE_FAILED,
    EVT_JOURNAL_WRITE_FAILED, EVT_EMBEDDING_FAILED,
    EVT_FAISS_MISMATCH, EVT_RETRIEVAL_FAILED,
    EVT_THREAD_DIED, EVT_SUBSYSTEM_INIT_FAILED,
)


class SelfHealMonitor:
    """
    Event-driven health monitor for FeralEcho.
    Subscribes to failure events from the EchoCore bus and responds
    with targeted repairs — no blind polling loops.
    """

    # Number of councillor timeouts for the same model within TIMEOUT_WINDOW
    # seconds before escalating to an Ollama probe.
    TIMEOUT_THRESHOLD = 3
    TIMEOUT_WINDOW = 300   # seconds

    def __init__(self, core):
        self._core = core
        self._lock = threading.Lock()
        self._timeout_log: dict[str, list[float]] = defaultdict(list)

        subscriptions = {
            EVT_COUNCILLOR_TIMEOUT:       self._on_councillor_timeout,
            EVT_COUNCILLOR_ERROR:         self._on_councillor_error,
            EVT_ALL_COUNCILLORS_FAILED:   self._on_all_councillors_failed,
            EVT_SYNTHESIS_FAILED:         self._on_synthesis_failed,
            EVT_RIVER_SAVE_FAILED:        self._on_river_save_failed,
            EVT_RIVER_WRITER_ERROR:       self._on_river_writer_error,
            EVT_RIVER_LOCK_STALE:         self._on_river_lock_stale,
            EVT_OLLAMA_LIST_FAILED:       self._on_ollama_failed,
            EVT_OLLAMA_PROBE_FAILED:      self._on_ollama_failed,
            EVT_JOURNAL_WRITE_FAILED:     self._on_journal_write_failed,
            EVT_EMBEDDING_FAILED:         self._on_embedding_failed,
            EVT_FAISS_MISMATCH:           self._on_faiss_mismatch,
            EVT_RETRIEVAL_FAILED:         self._on_retrieval_failed,
            EVT_THREAD_DIED:              self._on_thread_died,
            EVT_SUBSYSTEM_INIT_FAILED:    self._on_subsystem_init_failed,
        }
        for event_type, handler in subscriptions.items():
            core.subscribe(event_type, handler)

        logging.info("[SelfHeal] Monitor active — subscribed to %d event types.", len(subscriptions))

    # ── Handlers ──────────────────────────────────────────────────────────

    def _on_councillor_timeout(self, payload):
        model = payload.get("model", "unknown")
        now = time.time()
        with self._lock:
            self._timeout_log[model] = [
                t for t in self._timeout_log[model]
                if now - t < self.TIMEOUT_WINDOW
            ]
            self._timeout_log[model].append(now)
            count = len(self._timeout_log[model])
        logging.warning("[SelfHeal] Councillor timeout: model=%s count_in_window=%d", model, count)
        if count >= self.TIMEOUT_THRESHOLD:
            self._probe_ollama(trigger=f"repeated_timeout:{model}")

    def _on_councillor_error(self, payload):
        # Single errors are noise; log and move on.
        logging.info("[SelfHeal] Councillor error: model=%s error=%s",
                     payload.get("model"), payload.get("error"))

    def _on_all_councillors_failed(self, payload):
        logging.warning("[SelfHeal] All councillors failed for task=%s — probing Ollama.",
                        payload.get("task_type"))
        self._probe_ollama(trigger="all_councillors_failed")

    def _on_synthesis_failed(self, payload):
        logging.warning("[SelfHeal] Synthesis failed for task=%s — probing Ollama.",
                        payload.get("task_type"))
        self._probe_ollama(trigger="synthesis_failed")

    def _on_river_save_failed(self, payload):
        logging.warning("[SelfHeal] RiverBrain save failed: %s — checking lock file.", payload.get("error"))
        self._clear_stale_river_lock()

    def _on_river_writer_error(self, payload):
        logging.warning("[SelfHeal] RiverBrain writer error: %s", payload.get("error"))
        # The writer thread is a daemon; if it died, thread_watchdog will publish
        # EVT_THREAD_DIED for "RiverBrain-Writer" and _on_thread_died will handle restart.

    def _on_river_lock_stale(self, payload):
        lock_path = payload.get("lock_path", "memory/river_brain.pkl.lock")
        age = payload.get("age_seconds", 0)
        logging.warning("[SelfHeal] Stale RiverBrain lock detected (%.0fs old) — removing.", age)
        self._clear_stale_river_lock(lock_path=lock_path)

    def _on_ollama_failed(self, payload):
        logging.warning("[SelfHeal] Ollama failure event: %s", payload.get("error"))
        self._probe_ollama(trigger="ollama_event")

    def _on_journal_write_failed(self, payload):
        file_path = payload.get("file_path", "memory/reflection_shard.jsonl")
        logging.warning("[SelfHeal] Journal write failed for %s — ensuring directory.", file_path)
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        except Exception as e:
            logging.error("[SelfHeal] Could not create journal directory: %s", e)

    def _on_embedding_failed(self, payload):
        # Embedding failures are usually transient (model loading race).
        # Log; don't act unless they become persistent (future: add rate tracking).
        logging.warning("[SelfHeal] Embedding failure: %s", payload.get("error"))

    def _on_faiss_mismatch(self, payload):
        logging.warning("[SelfHeal] FAISS mismatch detected — triggering vector index repair.")
        try:
            import app.lib.vector_memory as vm_mod
            repair_vector_memory_index(vm_mod)
        except Exception as e:
            logging.error("[SelfHeal] Vector index repair failed: %s", e)

    def _on_retrieval_failed(self, payload):
        logging.warning("[SelfHeal] Memory retrieval failed: %s — will attempt FAISS repair.", payload.get("error"))
        self._on_faiss_mismatch({})

    def _on_thread_died(self, payload):
        name = payload.get("thread_name", "unknown")
        logging.warning("[SelfHeal] Thread '%s' died — checking restart registry.", name)
        restart_map = self._core._thread_restart_registry if hasattr(self._core, "_thread_restart_registry") else {}
        factory = restart_map.get(name)
        if factory:
            try:
                t = factory()
                self._core._threads[name] = t
                logging.info("[SelfHeal] Thread '%s' restarted.", name)
            except Exception as e:
                logging.error("[SelfHeal] Could not restart thread '%s': %s", name, e)
        else:
            logging.warning("[SelfHeal] No restart factory for thread '%s' — manual intervention needed.", name)

    def _on_subsystem_init_failed(self, payload):
        logging.warning("[SelfHeal] Subsystem init failure: %s — %s",
                        payload.get("subsystem"), payload.get("error"))
        # Subsystem init failures during startup are logged here for observability.
        # Retry logic is not appropriate (init already tried); this is a human alert.

    # ── Repair utilities ──────────────────────────────────────────────────

    def _probe_ollama(self, trigger: str = "") -> bool:
        """Send a minimal test call to Ollama. Publishes EVT_OLLAMA_PROBE_FAILED if unreachable."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logging.info("[SelfHeal] Ollama probe OK (trigger=%s).", trigger)
                return True
            raise RuntimeError(result.stderr.strip())
        except Exception as e:
            logging.error("[SelfHeal] Ollama probe FAILED (trigger=%s): %s", trigger, e)
            self._core.publish(EVT_OLLAMA_PROBE_FAILED, {"error": str(e)})
            return False

    def _clear_stale_river_lock(self, lock_path: str = "memory/river_brain.pkl.lock") -> None:
        try:
            if os.path.exists(lock_path):
                age = time.time() - os.path.getmtime(lock_path)
                if age > 60:
                    os.remove(lock_path)
                    logging.info("[SelfHeal] Stale RiverBrain lock removed (%.0fs old).", age)
                else:
                    logging.debug("[SelfHeal] Lock file is fresh (%.0fs) — not removing.", age)
        except Exception as e:
            logging.error("[SelfHeal] Failed to remove lock file: %s", e)


# ── Preserved repair utility ───────────────────────────────────────────────

def repair_vector_memory_index(vector_memory_module) -> bool:
    """
    Rebuild or back up a corrupted/missing VectorMemory index.
    Called by SelfHealMonitor._on_faiss_mismatch and directly if needed.
    """
    index_path = getattr(vector_memory_module, "VECTOR_INDEX_PATH", "data/faiss.index")
    meta_path  = getattr(vector_memory_module, "VECTOR_META_PATH",  "data/memory_meta.json")

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    os.makedirs(os.path.dirname(meta_path),  exist_ok=True)

    if not os.path.exists(meta_path):
        logging.warning("[SelfHeal] Memory metadata missing — creating empty metadata file.")
        with open(meta_path, "w") as f:
            json.dump({}, f)

    try:
        vm = vector_memory_module.VectorMemory(
            dim=vector_memory_module.VectorMemory.DEFAULT_DIM,
            index_path=index_path,
            meta_path=meta_path,
        )
        logging.info("[SelfHeal] VectorMemory re-initialized successfully.")
        return True
    except Exception as e:
        logging.error("[SelfHeal] VectorMemory init failed: %s", e)
        if os.path.exists(index_path):
            backup = index_path + ".bak"
            shutil.move(index_path, backup)
            logging.info("[SelfHeal] Corrupted index backed up to %s.", backup)
        try:
            vector_memory_module.VectorMemory(
                dim=vector_memory_module.VectorMemory.DEFAULT_DIM,
                index_path=index_path,
                meta_path=meta_path,
            )
            logging.info("[SelfHeal] VectorMemory re-initialized after backup.")
            return True
        except Exception as e2:
            logging.error("[SelfHeal] VectorMemory re-init after backup failed: %s", e2)
            return False
```

---

## Phase 5 — Thread Restart Registry in EchoCore

To support `_on_thread_died` restarting threads cleanly, add a restart registry
to EchoCore. Each entry is a zero-argument factory that starts and returns a new
daemon thread. Populate it alongside thread creation in `__init__`.

```python
# In EchoCore.__init__, after starting the heartbeat thread:
self._thread_restart_registry: dict[str, Callable[[], threading.Thread]] = {
    "heartbeat": lambda: self._start_daemon(self._heartbeat_loop, "EchoCoreHeartbeat"),
    "EchoCoreBus": lambda: self._start_daemon(self._dispatch_loop, "EchoCoreBus"),
    # emergent_scheduler, night_cycle, etc. added when those threads are registered
}

def _start_daemon(self, target, name):
    t = threading.Thread(target=target, daemon=True, name=name)
    t.start()
    return t
```

---

## Phase 6 — Startup Wiring in run.py / echo_core.py

After `EchoCore` is constructed in `run.py`, instantiate `SelfHealMonitor`:

```python
from app.core.self_heal import SelfHealMonitor
self_heal_monitor = SelfHealMonitor(core)
# Store on app config so it's not GC'd
app.config["self_heal"] = self_heal_monitor
```

`SelfHealMonitor.__init__` does all the subscribing. No timers, no further
wiring needed.

---

## What Stays, What Goes

| Existing function | Disposition |
|---|---|
| `repair_vector_memory_index` | Keep — moved to bottom of file as standalone utility |
| `run_self_healing` | Delete — calls patchers that are no longer relevant |
| `run_self_healing_background` | Delete — replaced by event subscriptions |
| `repair_append_to_journal` | Delete — patches an API mismatch that no longer exists |
| `repair_memory_bridge` | Delete — same; memory_bridge methods are stable |

---

## Implementation Order

1. `app/core/health_events.py` — create with all event type constants (no deps, zero risk)
2. `app/core/echo_core.py` — add `_thread_watchdog_loop`, `_thread_restart_registry`, `_init_failures` deferred publish
3. `app/core/self_heal.py` — rewrite as `SelfHealMonitor` + `repair_vector_memory_index`
4. `app/core/river_deliberation.py` — add 5 publish calls at the error sites listed above
5. `app/core/echo_model_orchestrator.py` — add 4 publish calls (writer error, stale lock, save failed, list failed)
6. `app/core/memory_bridge.py` — add 4 publish calls (journal, embedding, faiss mismatch, retrieval)
7. `run.py` — instantiate `SelfHealMonitor(core)` after EchoCore construction

Each phase is independently testable. Phases 1–3 can be done and verified before any
publish calls are wired, because `SelfHealMonitor` will simply receive no events until
the publishers are in place.
