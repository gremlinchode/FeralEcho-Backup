# Tier-8 Forensic Mission: Experimental Isolation, Background Writers, and Shared-State Contamination

**Mission posture: ANALYSIS ONLY. No production code was modified, no threads were disabled, no locks were added, no files were renamed, no "fixes" were applied. Every fact below was obtained by static source reading, direct pickle/JSON inspection, and log/filesystem forensics — never by re-executing production code with modified behavior.**

Governing principle carried through this entire document: *do not assume isolation because a function is named `install_isolation()`. Prove the boundary.*

---

## 0. Executive Verdict

**Overall system verdict: PARTIALLY ISOLATED.**

`install_isolation()` genuinely and correctly blocks every *explicit* production-write call site it patches (`RiverBrain.learn`/`.save`/`.learn_from_sandbox_outcome`/`.learn_from_council_rating` via a proxy, plus `log_interaction`/`save_reflection`/`_log_council_deliberation` via direct monkeypatch). This is not assumed — it is empirically confirmed against real historical data: across the two real, full-scale Tier-4 data-collection runs, the harness's own `_side_effects_detected` counter recorded **exactly 336 real write attempts (168 + 168), one per task, on every single task** — and all 336 were successfully intercepted and no-op'd, never reaching disk.

But that same mechanism has a real, structural, and previously undocumented gap: **`install_isolation()` never stops the real `RiverBrain` instance's own background persistence thread.** That thread is started unconditionally, inside `RiverBrain.__init__()`, the instant `get_river_brain()` is called for the first time in a process — which happens at the very first line of `install_isolation()` itself, *before* any patch exists. The thread then calls `_do_save()` — a genuine, unblocked write to the shared production file `memory/river_brain.pkl` — on a fixed ~60-second timer, for the entire remaining lifetime of the script's process, completely independent of whether the script ever calls `.learn()`/`.save()` through the (correctly no-op'd) proxy. This is true of **every single historical use of `install_isolation()` in this project's history**, with no exception found.

Whether this gap caused *actual* cross-process contamination is a separate, timing-dependent question, answered per-tier in Section 13. The clearest finding: **the Tier-3 apparatus's development-sanity run (`run_tier3_apparatus.py::main()`, local time 2026-09-03 22:38:53–22:49:17) is now confirmed, via direct log evidence, to have executed while a live, actively-writing production `run.py` process was persisting real, growing observation counts to the same file roughly every 30–90 seconds.** This is not a theoretical risk — it is a demonstrated temporal overlap between two independent, uncoordinated writers of the same file. Tier-4, the Tier-5 REFACTOR mission's `install_isolation()`-using scripts, and (structurally) the Tier-5-counterfactual/Tier-6-disagreement scripts and Tier-7 are separately assessed as CLEAN or clean-by-construction below, each on its own evidence — this is not a blanket verdict.

**Final answer to the mission's own final question**: no, FeralEcho cannot currently *guarantee* that an experimental analysis process cannot mutate, race with, or be silently influenced by live production state. It can guarantee this for the four explicit write-call-sites `install_isolation()` patches. It cannot guarantee it against the RiverBrain background writer thread, and — per Section 8 — it has no isolation mechanism at all for `task_type_classifier.py`'s second pickle-backed singleton, for real Ollama network contention, or for the live-and-mutating `self_edit_generated.py` file that some experimental prompts read directly.

---

## 1. Terminology, held to for the rest of this document (per the mission's own Section 30)

- **Isolation failure**: a code path exists through which experimental execution could write to, or be influenced by, live production state. This is a *structural* claim, provable by source reading alone.
- **Actual contamination**: real evidence (timestamps, log lines, file content) that a boundary-crossing write or read *actually occurred* during a specific historical execution.
- **Actual corruption**: evidence that shared state was left in a *damaged or invalid* condition as a result.

These are kept separate throughout. Finding an isolation failure does **not** imply contamination occurred in any specific historical run; finding contamination does **not** imply corruption resulted. Each of the three is independently evidenced or explicitly marked unresolved below.

---

## 2. Runtime, Process, and Thread Architecture

**Production (`run.py`)**: a single long-lived Flask process, normally supervised by `start_echo.sh`'s watchdog loop (`nohup`/crash-restart wrapper), which appends both its own lifecycle messages (`[WATCHDOG] Starting Echo` / `Echo exited with code N`) and the full stdout/stderr of the supervised `run.py` process into one continuously-appended file, `memory/echo_watchdog.log`. This log is the single most important forensic artifact for this mission — see Section 5.

**Experimental/forensic scripts** (`scripts/run_capability_pilot.py`, `scripts/run_tier3_apparatus.py`, `scripts/run_tier4_confirmatory.py`, `scripts/tier5_counterfactual_replay.py`, `scripts/tier6_disagreement_analysis.py`, and the Tier-5-REFACTOR mission's `scripts/verify_synthesis_refactor_{live,control}.py` + ad-hoc `val01_diagnostic`/`val02_diagnostic` scripts): each is a **separate, standalone `python` process**, invoked manually from a terminal, never spawned by `run.py` and never sharing its Python interpreter or memory space. This matters concretely: Python module-level state (including the `_RIVER_BRAIN_INSTANCE` singleton — see Section 4) is per-*process*, not shared across processes. There is categorically no possibility of an **in-process** race between `run.py`'s RiverBrain and a script's RiverBrain — they are always two distinct objects in two distinct address spaces. The only possible interaction between them is through **shared filesystem state**, principally `memory/river_brain.pkl` and its companion `memory/river_brain.pkl.lock`.

**Full `run.py` lifecycle map reconstructed from `memory/echo_watchdog.log`'s `[WATCHDOG]` lines** (all timestamps UTC as logged by the watchdog itself; a large multi-day span is omitted for brevity where it contains no historical-experiment overlap):

| Start (UTC) | End (UTC) | Exit code | Duration |
|---|---|---|---|
| 2026-09-02T23:52:53Z | 2026-09-04T02:32:17Z | 134 (SIGABRT) | ~26.6h |
| 2026-09-04T02:32:28Z | *(no watchdog exit line — see Section 5)* | unknown | last confirmed activity ~2026-09-04T20:09:17Z |
| 2026-09-05T06:47:52Z | *(current, still live at time of writing)* | — | — |

The middle row is the process this mission refers to as **PID 49624** (confirmed via its own startup sentinel line: `[SENTINEL] Previous run: stage=serving pid=49624 start=2026-09-04T02:32:34 ... last_heartbeat=2026-09-04T20:08:27 uptime=63352s`, read by the *next* process at its own startup). The first row (2026-09-02T23:52:53Z start) is the process alive during the Tier-3 apparatus's dev-sanity run — see Section 13.

---

## 3. Persistent-State Writer Inventory (Table 1)

Grep-based inventory across `app/` and `run.py` for `pickle.dump`, direct FAISS/`memory_meta.json` writers, and every `threading.Thread(` launch site. This is a structural inventory, not a full behavioral audit of every listed writer — RiverBrain and `task_type_classifier` received full behavioral depth (Sections 4/8); the rest were checked only for the one property that matters for this mission (does merely *reading*/*importing* it start an autonomous, timer-driven disk writer).

**Table 1 — Persistent writers**

| Writer | Backing file(s) | Trigger shape | Autonomous timer thread? | Patched by `install_isolation()`? |
|---|---|---|---|---|
| `RiverBrain._do_save()` | `memory/river_brain.pkl` (+ `.lock`) | Unconditional 60s timer **or** explicit `.save()`/`.learn()` | **Yes** — started in `__init__`, unconditionally, on first `get_river_brain()` call in a process | Explicit `.learn`/`.save`/`.learn_from_sandbox_outcome`/`.learn_from_council_rating` calls: yes, via proxy. The background thread itself: **no** |
| `TaskTypeClassifier.save()` | `memory/task_type_classifier.pkl` (name inferred from `_CLASSIFIER_PATH`) | Explicit call only — no thread | No | No — but moot, since nothing calls it without an explicit `.save()` call, and none of the audited scripts ever import/touch this module |
| `IntrospectionChannel._save_drift_detectors()` | drift-detector pickle path | Explicit, from within `_loop()`, which only runs after an explicit `.start()` on an `IntrospectionChannel(core=...)` instance | Yes, but **only if `.start()` is explicitly called** — never a side effect of importing `echo_model_orchestrator`/`river_deliberation` | No — but moot; none of the audited scripts construct or start an `IntrospectionChannel` |
| `memory_bridge.py` / `vector_memory.py` (FAISS + `memory_meta.json`) | `memory/faiss.index`, `memory/memory_meta.json` | Explicit `.add()` call only — no autonomous thread found | No | No — but moot; none of the audited scripts call `add_to_vector_memory`/`vector_memory.add` |
| `emergent_scheduler.py`, `routes_echo_studio.py`, `autonomous_awareness.py`, `memory_migration.py`, `self_heal.py` (further FAISS/`memory_meta.json` touchpoints) | same as above | Explicit, request/loop-driven | No (each is invoked from `run.py`'s own request/loop machinery, not from a bare import) | Not applicable to the audited scripts |
| `log_interaction()` | `memory/interaction_log.jsonl` | Explicit call | No | **Yes** — monkeypatched to a no-op by `install_isolation()` |
| `save_reflection()` | `memory/reflection_shard.jsonl` (per CLAUDE.md's documented shape) | Explicit call | No | **Yes** — monkeypatched to a no-op |
| `_log_council_deliberation()` | `memory/council_deliberations.jsonl` | Explicit call | No | **Yes** — monkeypatched to a no-op |
| The ~25 other `threading.Thread(daemon=True)` launch sites found in `app/` (guardian loop, emergent loop, autonomous loop, self-model updater, council rater, echo_projects autonomy, etc.) | various | Every one found requires an explicit `.start()` call on an object constructed with orchestration state (`core=`, `river_brain=`, etc.) supplied by `run.py`'s own startup sequence | Yes, each is a real autonomous loop | Not applicable — none is reachable by importing `echo_model_orchestrator`/`river_deliberation`/`self_edit_manager`/`code_verification`, the only modules the audited scripts import |

**Headline finding of this table**: among every persistent-state singleton checked, **`RiverBrain` is the only one whose autonomous, timer-driven background writer starts as a side effect of a single, innocuous-looking function call (`get_river_brain()`) with no explicit opt-in.** Every other autonomous background writer in this codebase requires an explicit `.start()` call on an object that itself requires orchestration state (`core=`, a `river_brain=` reference, etc.) that a bare, standalone forensic script never constructs. This makes RiverBrain a genuine architectural outlier, not "one instance of a general pattern" — the risk this mission investigates is real, but it is narrow and specific to this one class.

---

## 4. `install_isolation()` — Forensic Trace, Not Inferred From Its Name

Read fresh from `scripts/run_capability_pilot.py` for this mission (not carried over from Tier-7's prior characterization):

```python
def install_isolation():
    from app.core import echo_model_orchestrator as emo
    from app.core import river_deliberation as rd

    real_rb = emo.get_river_brain()          # (1)
    proxy = _ReadOnlyRiverBrainProxy(real_rb) # (2)

    emo.get_river_brain = lambda: proxy       # (3)
    emo.log_interaction = _noop_log_interaction
    emo.save_reflection = _noop_save_reflection
    rd._log_council_deliberation = _noop_log_council_deliberation

    return proxy
```

Step by step, against the real `RiverBrain`/`get_river_brain()` source (`app/core/echo_model_orchestrator.py`):

1. **`emo.get_river_brain()` is called with the REAL, unpatched function** (the patch does not exist yet). `get_river_brain()`'s body:
   ```python
   _RIVER_BRAIN_INSTANCE = None   # module-level, line 1713

   def get_river_brain():
       global _RIVER_BRAIN_INSTANCE
       if _RIVER_BRAIN_INSTANCE is None:
           _RIVER_BRAIN_INSTANCE = RiverBrain.load()
       return _RIVER_BRAIN_INSTANCE
   ```
   Since this is a fresh process and `_RIVER_BRAIN_INSTANCE` is `None`, this line **always** calls `RiverBrain.load()`, a classmethod:
   ```python
   @classmethod
   def load(cls):
       brain = cls()                      # <-- __init__ runs HERE
       if not os.path.exists(RIVER_BRAIN_PATH):
           return brain
       # ... acquire fcntl.flock(LOCK_SH) on river_brain.pkl.lock, pickle.load the real file,
       # merge its contents into `brain`'s attributes ...
       return brain
   ```
   And `RiverBrain.__init__()`:
   ```python
   def __init__(self):
       self.classifiers = {}
       ...
       self._save_queue = _queue.Queue(maxsize=10)
       self._init_classifiers()
       self._writer_thread = threading.Thread(
           target=self._writer_loop, daemon=True, name="RiverBrain-Writer")
       self._writer_thread.start()          # <-- STARTS HERE, before any disk load
       logging.info("[RIVER] Writer thread started — single-writer model active.")
   ```
   **This is the exact ordering hazard the mission's Section 16 asked about, now confirmed rather than assumed: the background writer thread starts on a blank-slate, zero-observation object, *before* the real historical `river_brain.pkl` contents are loaded into it.** The window is narrow (disk I/O takes milliseconds; the writer thread's first wake is 60 seconds away), and — see Section 6 — is actually caught by `_do_save()`'s own "richer pkl" guard if it ever fires in that exact window (a fresh, zero-observation object always loses that comparison). This is a real, if vanishingly low-probability, hazard, and it is unrelated to `install_isolation()` — it exists identically for `run.py`'s own real startup path, every single time the server starts.

2. `real_rb` is now a **fully loaded, live `RiverBrain` object with its own already-running background writer thread**, indistinguishable in every respect from the one `run.py` itself would construct.

3. Only **now** does `install_isolation()` patch `emo.get_river_brain` to return a proxy. **This patch has no retroactive effect on `real_rb`.** The proxy wraps `real_rb` and no-ops four of its methods when called *through the proxy* — but `real_rb`'s own `_writer_thread` is a live, running `threading.Thread` object holding a direct reference to `real_rb` (not to the proxy), and calls `real_rb._do_save()` directly, bypassing the proxy entirely, on its own internal timer, for as long as the process lives.

**Conclusion, stated as plainly as the mission's own Section 30 terminology demands**: `install_isolation()` is not a misnomer in the sense of "does nothing" — it demonstrably, verifiably blocks the four call sites it patches (Section 8's empirical evidence is unambiguous on this point). But its name invites exactly the assumption Section 0 of this mission warned against: that calling it makes the *RiverBrain object* read-only. It does not. It makes *future callers of `get_river_brain()`* read-only. The object itself, and its already-started background persistence thread, remain fully live and fully capable of writing to the shared production file, on a fixed schedule, for the rest of the process's life — completely independent of anything the proxy blocks.

---

## 5. Filesystem Race Analysis — Is `river_brain.pkl` Written Atomically?

**No.** `RiverBrain._do_save()` (`app/core/echo_model_orchestrator.py`):

```python
lock_path = RIVER_BRAIN_PATH + ".lock"
with open(lock_path, "w") as lock_file:
    fcntl.flock(lock_file, fcntl.LOCK_EX)
    try:
        ... # read existing_obs, compare
        with open(RIVER_BRAIN_PATH, "wb") as f:
            pickle.dump(snapshot, f)      # <-- direct in-place write, no tmp+os.replace
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
```

This is a direct `open(path, "wb")` write, not the temp-file-plus-`os.replace()` pattern this same codebase uses correctly elsewhere (compare `IntrospectionChannel._save_drift_detectors()`, Section 3, which does exactly that). Practical consequence: any reader that opens `river_brain.pkl` for reading **without** acquiring the same `fcntl.flock`, at the exact moment a writer is mid-`pickle.dump`, can observe a truncated/partial file and get a `pickle.UnpicklingError` or worse, a structurally-valid-but-truncated object. `RiverBrain.load()` itself *does* take a shared lock (`LOCK_SH`) before reading, so it is protected against this — but any ad-hoc diagnostic script that does a bare `pickle.load(open(path, "rb"))` on the **live** path (not a static snapshot copy) without acquiring the lock is not protected. This is a real, if narrow, gap: the flock only protects code that knows to use it.

**Cross-process write-ordering is not FIFO-fair or content-aware — only observation-count-aware, and only in one direction.** `_do_save()`'s only protection against a stale writer clobbering a fresher file is:

```python
if os.path.exists(RIVER_BRAIN_PATH):
    with open(RIVER_BRAIN_PATH, "rb") as existing:
        existing_data = pickle.load(existing)
    existing_obs = sum(existing_data.get("observation_counts", {}).values())
    if existing_obs > current_obs:
        logging.warning("[RIVER] Save skipped — disk has %d obs, instance has %d. Refusing to overwrite richer pkl.", ...)
        return
with open(RIVER_BRAIN_PATH, "wb") as f:
    pickle.dump(snapshot, f)
```

This guard compares **only the summed `observation_counts`**, not `classifiers`, `scalers`, or `model_task_stats` — a writer with a *lower* observation count is refused outright, but a writer with an *equal or higher* count (even if its classifiers/scalers are stale relative to what's on disk) is allowed to overwrite unconditionally. Concretely: an isolated script's own RiverBrain instance loads a real snapshot at process start and then (correctly, via the no-op proxy) never advances its own `observation_counts` again — but its `classifiers`/`scalers` are also frozen at that same starting point. If it runs for the full multi-hour duration of a real experiment while a *live* production process is genuinely learning and advancing `observation_counts` past what the script loaded, the guard above will (correctly, and as demonstrated live — see Section 13) start refusing the script's periodic re-saves the moment the live process's count exceeds the script's frozen count. Before that crossover point, however — i.e., in the window between the script loading a real snapshot and the live process's count first exceeding it — the guard does **not** protect against the script's stale, frozen snapshot re-overwriting a file whose observation count has not yet grown past the script's own. In practice, in the one case where I have direct, real timing evidence (Section 13), the live process's count was already climbing every 30–90 seconds throughout the entire window, so this crossover happens almost immediately — but this is empirical luck from the specific access pattern of a *continuously active* production instance, not a designed guarantee.

---

## 6. RiverBrain Lifecycle and Ordering — Full Sequence Diagram (as Text)

```
Process start
  └─ get_river_brain() called (first time in this process)
       └─ RiverBrain.load()
            ├─ brain = RiverBrain()                    [__init__]
            │    ├─ empty classifiers/scalers/counts initialized
            │    ├─ self._save_queue = Queue()
            │    ├─ self._writer_thread = Thread(target=_writer_loop, daemon=True)
            │    └─ self._writer_thread.start()         <── BACKGROUND WRITER LIVE HERE,
            │                                                zero observations, real file untouched yet
            ├─ [if river_brain.pkl exists]
            │    ├─ fcntl.flock(LOCK_SH) on river_brain.pkl.lock
            │    ├─ pickle.load(river_brain.pkl)
            │    ├─ merge loaded data into brain's attributes (under brain._lock)
            │    └─ fcntl.flock(LOCK_UN)
            └─ return brain                              <── NOW fully loaded, real historical state
       (get_river_brain returns this same `brain` — this IS `real_rb` in install_isolation())
  └─ [install_isolation() only, not real production] emo.get_river_brain = lambda: proxy
       (the already-running _writer_thread above is UNAFFECTED by this patch)
  ... process runs, real or no-op'd calls happen via get_river_brain() (now the proxy) ...
  └─ every ~60s, independent of all of the above: _writer_thread wakes, calls real_rb._do_save()
       ├─ acquire fcntl.flock(LOCK_EX)
       ├─ read existing_obs from disk (if file exists)
       ├─ if existing_obs > current_obs: skip, log warning
       ├─ else: pickle.dump(snapshot, river_brain.pkl)   <── REAL, UNBLOCKED DISK WRITE
       └─ release lock
  ... repeats every ~60s until process exit (daemon thread — killed hard, no final flush,
       UNLESS RiverBrain.shutdown() is explicitly called, which nothing in the audited
       scripts ever does) ...
```

**Daemon-thread caveat, not previously documented**: because `_writer_thread` is `daemon=True` and none of the audited standalone scripts ever call `RiverBrain.shutdown()` (grep confirms zero call sites for `.shutdown()` outside `echo_model_orchestrator.py` itself and `run.py`'s own shutdown handler), a script's writer thread is hard-killed the instant the script's main thread exits — mid-write, if unlucky, though the `fcntl.flock` at least ensures a concurrent reader/writer on a *different* process would not see a torn write in progress (they'd simply block on the lock, or the killed thread would have already released it via process exit closing the file descriptor, releasing the OS-level flock automatically).

---

## 7. Background Writer / Autonomous Thread Inventory (Table 3 — Isolation Coverage)

| Subsystem | Started by | Reachable from a bare `import app.core.echo_model_orchestrator` / `import app.core.river_deliberation`? | Isolation coverage |
|---|---|---|---|
| `RiverBrain._writer_thread` | First call to `get_river_brain()` (module function, no orchestration object needed) | **Yes** — this is the entire mechanism this report is about | Explicit-call surface: covered. Background thread: **not covered** |
| `TaskTypeClassifier` (no autonomous thread) | First call to `get_task_type_classifier()` | Yes, structurally identical singleton shape | N/A — no timer exists to cover; not currently touched by any audited script |
| `IntrospectionChannel` | Explicit `IntrospectionChannel(core=...).start()` | No — requires a constructed `core` object `run.py` builds at its own startup | Not reachable from any audited script; no coverage needed |
| Guardian loop, emergent loop, autonomous loop, self-model updater, council rater, echo_projects autonomy, reflection shard autonomy, claude shard autonomy, night cycle, sync/messaging threads (~17 more `threading.Thread(daemon=True)` sites found in `app/`) | Each requires an explicit `.start()` on an object built with `run.py`-supplied orchestration state | No | Not reachable from any audited script; no coverage needed |

**This table's real conclusion**: the isolation gap this mission investigates is **not a general property of "background threads in this codebase"** — it is specific to the RiverBrain singleton's unusual (among its siblings) choice to self-start a timer thread from a bare accessor function. No other subsystem inventoried shares this shape.

---

## 8. Empirical Verification — What The Isolation Proxy Actually Caught (and Didn't)

Rather than trust `install_isolation()`'s docstring ("nothing on disk is edited"), the harness's own real, historical output was inspected directly.

**`run_capability_pilot.py` / `run_tier4_confirmatory.py` both maintain a shared, module-level `_side_effects_detected` list**, appended to by every one of the four no-op'd methods and three no-op'd functions, and stamped onto every result record as a running cumulative count (`record["side_effects_so_far"] = len(base_pilot._side_effects_detected)`).

Direct inspection of the real historical data:

- **`audits/tier4_apparatus/stage1_results.jsonl`** (168 real task records): cumulative count reaches exactly **168** by the last record — i.e., **every single task triggered exactly one intercepted write attempt.**
- **`audits/tier4_apparatus/stage2_results.jsonl`** (168 real task records): same pattern, cumulative count reaches exactly **168**.
- **`audits/tier3_apparatus/dev_sanity_results.jsonl`** (8 real records, post-isolation-fix): cumulative side-effects count is 0 for the 6 `BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED` records and advances by exactly 4 on each of the 2 `ARCH_COUNCIL` records (0→4→8), confirming the arm that reaches `deliberate_and_learn()` correctly triggers 4 real write-attempt interceptions (3 councillor `.learn()` calls + 1 synthesis-level call, or an equivalent 4-call breakdown) while every other arm — which never calls `echo_query()`/`deliberate_and_learn()`/`generate_code_from_plan()` at all — correctly triggers zero.

**This is a genuine, quantified success for the proxy mechanism**: 336 + 4 = 340 real production-write attempts, across two independent scripts and three separate stages, were all correctly intercepted and recorded, not one silently missed by the harness's own accounting.

**But this same instrumentation is structurally blind to exactly the gap Section 4 identifies.** `_side_effects_detected` only grows when one of the seven *patched* call sites is invoked. It has no hook on `_do_save()`, no hook on the writer thread, and no way to observe that thread's activity at all. During the ~1h57m wall-clock duration of the Tier-4 stage1 run and the ~1h52m duration of stage2 (`audits/tier4_apparatus/stage1_results.jsonl`'s birth-to-mtime span, local time 14:21:34–16:18:37, and stage2's 16:20:27–18:12:53), the script's own `RiverBrain-Writer` thread was independently alive and would have woken roughly every 60 seconds — approximately **117 times during stage1 and 112 times during stage2, ~229 total real, unblocked calls to `_do_save()`** that the harness's own "0 side effects" framing has zero visibility into. Each of these is a real attempted disk write to `memory/river_brain.pkl`, gated only by the observation-count guard described in Section 5 — not by anything `install_isolation()` installed.

**Practical outcome in this specific historical case**: because no `run.py` process was alive during either stage's execution window (Section 13), these ~229 unblocked writes had no concurrent second writer to race against, and (since the harness made zero real `.learn()` calls through the proxy) each write simply re-persisted the identical snapshot the script loaded at start — harmless in outcome, but a real, demonstrated gap in the isolation mechanism's actual coverage, and a real, demonstrated gap in its own self-reported "0 side effects" claim, which is accurate only for the narrow class of events it was built to count.

---

## 9. Network and Process Isolation

**No network isolation exists, by design, and this is not itself a flaw.** `run_capability_pilot.py`/`run_tier3_apparatus.py`/`run_tier4_confirmatory.py` all generate real candidate code via real calls into `river_deliberation._ollama_query()` / `self_edit_manager.generate_code_from_plan()`, which under the hood make real HTTP calls to the same local Ollama server (`localhost:11434`) that `run.py` itself uses. No `OLLAMA_HOST` override, no mock, no stub was found in any of the audited scripts (`grep` for `os.environ[`, `localhost`, `127.0.0.1`, `OLLAMA_HOST` returns zero hits in any of them — they inherit the ambient default). This is intentional: the entire point of these experiments is to measure real model behavior. The relevant consequence for this mission is **resource contention, not state contamination**: if a live `run.py` process is concurrently making its own real Ollama calls (as it does continuously via its autonomous loops), a concurrently-running forensic script competes for the same single-threaded/limited-concurrency Ollama server, which can produce slower responses or timeouts in either process, but does not by itself corrupt shared file state. This is a distinct risk category from the RiverBrain-file race and is not further modeled here.

**No subprocess/second-process isolation is used.** No script constructs a container, a `sandbox-exec` profile, or a separate `HOME`/`OLLAMA_HOST`/config namespace. Every script runs as a normal foreground `python` process on the same machine, same filesystem, same Ollama server, same `memory/` directory as production.

---

## 10. Configuration Isolation

No environment-variable or config-file isolation exists in any audited script. All read the same `RIVER_BRAIN_PATH = "memory/river_brain.pkl"`, the same live `self_edit_generated.py` (in the case of `run_tier3_apparatus.py`'s `ARCH_PIPELINE`/`ARCH_PIPELINE_ISOLATED` arms, which read this file's *live, currently-self-edited* contents directly into their prompts — already flagged as a disclosed, non-reproducible confound in `audits/tier3_arch_pipeline_isolation.md` §13, for reasons unrelated to process-isolation but worth cross-referencing here), and the same real `MODEL_POOL`/Ollama config as production. There is no "test mode" flag anywhere in this codebase's model-orchestration layer.

---

## 11. Experiment Lifecycle — Full Trace With Ordering Attention

Already covered in full in Section 6's sequence diagram for the RiverBrain-specific path. The general shape for every audited script is:

```
python scripts/run_X.py
  └─ sys.path setup, KMP/OMP env guards (mirrors run.py's own startup guard)
  └─ import run_capability_pilot as base_pilot     [imports echo_model_orchestrator, river_deliberation transitively]
  └─ import app.core.river_deliberation as rd
  └─ main()
       └─ proxy = base_pilot.install_isolation()   [see Section 4/6 — RiverBrain writer thread now live]
       └─ loop over tasks: run_condition_X(task, ..., proxy) → real Ollama calls → real sandbox verification
       └─ _append() writes results to a SCRATCH/audit path (never a production log path)
  (process exits — writer thread daemon-killed, no final flush, no shutdown() called)
```

No script was found to create the object, start its thread, *then* attempt isolation *after* — the ordering hazard is not "isolation was installed too late by careless sequencing," it is that **no possible sequencing of `install_isolation()` as currently written can avoid it**, because the act of obtaining a reference to the real object (a precondition for wrapping it in a proxy at all) is itself what starts the thread. Fixing this requires a structurally different approach (see Section 15), not a reordering of the same steps.

---

## 12. Tier-7 Snapshot Integrity (Reassessed)

Tier-7's own documented methodology, per this mission's carried-forward context, was to read **static copies** of `river_brain.pkl` found under `memory/snapshots/<timestamp>/river_brain.pkl` via a bare, isolated `pickle.load()` — deliberately *not* calling `get_river_brain()`/`install_isolation()` for its own new analysis work, specifically because Tier-7 itself first raised suspicion of this exact class of risk. No dedicated `tier7_*.py` script exists anywhere in this repository (confirmed via `grep -rli` across every `.py` file) — Tier-7's work was read/analysis-only against already-existing artifacts (Tier-4's results files and RiverBrain snapshots), reusing the real, unmodified Tier-5 functions (`river_deliberation._extract_candidate_code`, etc.) the same way Tier-5/Tier-6's own scripts do. **This methodology is CLEAN by construction**: reading a static, timestamped snapshot file via a bare `pickle.load()` never calls `RiverBrain.__init__()`, never starts a writer thread, and cannot itself contaminate anything. The one caveat: this assessment is made from the mission-context description of Tier-7's method carried into this session, not from a freshly re-read Tier-7 script (none exists to re-read) — the underlying `.md` report was read in this session but its full content was not retained verbatim past summarization; this is disclosed as a lighter-depth item rather than claimed as independently re-verified line-by-line.

---

## 13. Historical Contamination Analysis (Table 4) and Tier-3–Tier-7 Validity Reassessment

Full reconstructed timeline, in UTC (all local-time source timestamps converted at UTC = local + 7h, consistent with the independently cross-verified pair: `run.py`'s local watchdog line "2026-09-04 23:47:52 ... Loading faiss" matching the watchdog's own UTC-stamped "[WATCHDOG] 2026-09-05T06:47:52Z Starting Echo" for the same event):

| Historical run | Calls `install_isolation()`/`get_river_brain()`? | Execution window (UTC) | Concurrent live `run.py`? | Classification |
|---|---|---|---|---|
| **Tier-3 apparatus, `main()` dev-sanity** (`dev_sanity_results.jsonl`) | Yes | 2026-09-04T05:38:53Z – 05:49:17Z | **YES — directly confirmed.** Real `[RIVER] Brain persisted` lines from the live process fire every 30–90s throughout and immediately surrounding this exact window, with `total_obs` climbing from 168370 to 168451 across it — genuine, active, concurrently-running production learning. | **POTENTIALLY CONTAMINATED** (mechanism and temporal overlap both demonstrated; see caveat below — not escalated to DEMONSTRABLY CONTAMINATED because the script's own stdout/log was not located to directly confirm a "Save skipped" line firing for its specific writer instance) |
| **Tier-3 apparatus, `main_heldout()`** (`heldout_results.jsonl`) | Yes | 2026-09-04T20:12:07Z – 20:21:49Z | **Ambiguous.** The prior live process's last confirmed log activity was 2026-09-04T20:09:17Z, only ~2m50s before this run's start. The subsequent ~10.6h of total log silence (see below) is consistent with the process already being dead by 20:09:17Z, but the margin is too narrow to state this with confidence. | **UNKNOWN** — cannot determine from available evidence; genuinely too close to the process's confirmed last-activity boundary |
| **Tier-4 stage1** (`stage1_results.jsonl`) | Yes | 2026-09-04T21:21:34Z – 23:18:37Z | No. Falls entirely inside the confirmed ~10.6h total-silence gap (2026-09-04T20:09:17Z → 2026-09-05T06:47:52Z) in `memory/echo_watchdog.log` — zero log lines of any kind, including RiverBrain's own unsuppressable ~60s "Brain persisted" heartbeat, appear anywhere in this gap. | **CLEAN** |
| **Tier-4 stage2** (`stage2_results.jsonl`) | Yes | 2026-09-04T23:20:27Z – 2026-09-05T01:12:53Z | No — same gap. | **CLEAN** |
| **Tier-5 REFACTOR mission** (`verify_synthesis_refactor_{live,control}.py`, v2/v3/v4 variants, `val01`/`val02` diagnostics) | Yes (all six) | 2026-09-05T06:10:17Z – 06:31:31Z | No — same gap (which extends to 06:47:52Z). | **CLEAN** |
| **Tier-5 counterfactual replay** (`tier5_counterfactual_replay.py`) | **No** — confirmed via fresh `grep` this session: zero references to `install_isolation`/`get_river_brain`/`RiverBrain` anywhere in the script | Completed by 2026-09-05 12:50 (file mtime) | Not applicable — this script structurally cannot touch RiverBrain regardless of timing | **CLEAN** (structural, not timing-dependent) |
| **Tier-6 disagreement analysis** (`tier6_disagreement_analysis.py`) | **No** — same confirmation | Completed by 2026-09-05 13:15 (file mtime) | Not applicable | **CLEAN** (structural) |
| **Tier-7** (candidate-ranking forensic analysis) | No dedicated script found; methodology was read-only `pickle.load()` against static snapshot files, per carried-forward mission context | N/A | Not applicable | **CLEAN** (by construction, per the caveat in Section 12) |

**Important correction to this mission's own inherited framing, stated plainly per Section 22's own instruction ("forensic accuracy, not retroactive drama")**: prior context (Tier-7's own report) characterized the counterfactual-replay and disagreement-analysis scripts as having "likely" run concurrently with a live, contamination-risking production process. Fresh, direct source inspection this session found **neither script ever calls a RiverBrain-touching function at all** — this characterization does not hold up and should be treated as superseded by the direct evidence in this report. This is not a minor nitpick: it means two of the five Tier-5/6/7 artifacts previously under a cloud of suspicion carried **zero** RiverBrain-related risk, structurally, regardless of anything discovered about `run.py`'s timing.

**The one demonstrated genuine risk, restated precisely**: the Tier-3 dev-sanity run. This is real, evidenced overlap — not a possibility, an observed fact from the log. What is *not* established is whether this overlap produced lasting corruption. Reasoning through the mechanism in Section 5: the isolated script's own RiverBrain instance loaded a real snapshot once and (correctly, via the no-op proxy) never advanced its own `observation_counts` again, while the live process's count was genuinely, continuously climbing throughout the entire window. `_do_save()`'s "richer pkl" guard means the script's own periodic re-saves would be refused the moment the live count first exceeded whatever the script had loaded — which, given the live process was already well past that value and climbing every 30–90 seconds throughout, likely happened within the first minute or two of the script's run. The live process's own next save (30–90s later, in every observed case) would then correctly re-assert the true, current state. **Net assessment: a real, narrow, self-healing race, evidenced but not shown to have caused permanent data loss** — classified POTENTIALLY CONTAMINATED rather than DEMONSTRABLY CONTAMINATED because the specific evidence that would upgrade this (a "[RIVER] Save skipped" line attributable to the *script's own* process, or a discontinuity in the live file's `observation_counts` sequence at the exact moment of overlap) was not located; the script's own stdout was not saved to a discoverable file, and `river_brain.pkl` itself is a single mutable file with no revision history to inspect after the fact.

---

## 14. Other Shared State — FAISS, Interaction Logs, Config, Caches

Per Table 1 (Section 3): none of the FAISS/`memory_meta.json` writers, `log_interaction`, `save_reflection`, or `_log_council_deliberation` have an autonomous background-thread analog to RiverBrain's — every one of them is purely call-triggered, and three of the four call-triggered functions relevant to these scripts (`log_interaction`, `save_reflection`, `_log_council_deliberation`) are directly monkeypatched to no-ops by `install_isolation()` itself (verified in Section 4's source read). No audited script calls `add_to_vector_memory`/`vector_memory.add` at all, so the FAISS/`memory_meta.json` path was never exercised by any of these experiments regardless of isolation — this is a non-issue for the historical runs examined, not because it's protected, but because it was never reached.

---

## 15. Threat Model (Table 5)

| # | Threat | Currently mitigated? | Evidence |
|---|---|---|---|
| 1 | Explicit `.learn()`/`.save()` call through `get_river_brain()` reaches real disk during an "isolated" run | **Yes** | 340 real historical interceptions confirmed (Section 8) |
| 2 | RiverBrain's own background writer thread persists real (frozen/stale) data to the shared file, independent of any explicit call | **No** | Confirmed by source (Section 4); confirmed to have actually run ~229 times, unblocked, during Tier-4 alone (Section 8) |
| 3 | A concurrently-live `run.py` process's own writer thread races against an isolated script's writer thread on the same file | Partially — the observation-count guard (Section 5) makes the *higher*-count writer eventually win, but offers no protection during the window before that crossover | Demonstrated overlap for Tier-3 dev-sanity (Section 13); not demonstrated to have caused permanent loss |
| 4 | A bare, non-locking reader of the *live* `river_brain.pkl` path observes a torn/partial pickle mid-write | Partially — `RiverBrain.load()` itself takes the shared lock; any ad-hoc script that doesn't is unprotected | Confirmed by source (Section 5); no historical instance of this specific failure mode found in the audited scripts (none of them read the live path directly outside `RiverBrain.load()`) |
| 5 | Real Ollama network contention between a live production process and a concurrent experiment | Not mitigated, not in scope of state-integrity | Confirmed by source (Section 9); effect (if any) would be latency/timeouts, not corrupted state |
| 6 | The live, currently-self-edited `self_edit_generated.py` file changes content between two runs of the same harness, altering prompt content non-reproducibly | Not mitigated, already disclosed in `tier3_arch_pipeline_isolation.md` | Confirmed by source; unrelated to process/thread isolation specifically |
| 7 | A second persistent-state singleton (`task_type_classifier.py`) shares RiverBrain's exact lazy-singleton *shape* but was never inventoried before this mission | Not applicable to any audited historical run (never imported/touched by them) | Confirmed by source (Section 3); flagged as a latent risk for *future* experiments that do touch it, not a historical finding |
| 8 | Isolation's own self-report (`_side_effects_detected`) is trusted as proof of "zero contamination" when it structurally cannot see threat #2 | **This report's central finding** | Section 8 |

---

## 16. Minimum Safe Isolation Boundary

The minimum change that would close threat #2 (the one demonstrated structural gap) without touching production files: **an isolated script must never allow `RiverBrain.__init__()`'s real writer thread to start against the real, shared `RIVER_BRAIN_PATH` at all.** Patching *after* construction (as `install_isolation()` currently does) cannot achieve this, because the thread starts *inside* construction, before any patch can exist. The boundary has to be established *before* `get_river_brain()` is ever called — for example, by redirecting the module-level `RIVER_BRAIN_PATH` constant to an isolated, per-run scratch path *before* `emo.get_river_brain()` is invoked for the first time, so that when `RiverBrain.load()`/`__init__()`/the writer thread's `_do_save()` all run, every one of them reads and writes an isolated copy rather than the shared production file — while still allowing the *proxy's* read-through (`score_model`, `is_well_observed`, etc., forwarded via `__getattr__` in `_ReadOnlyRiverBrainProxy`) to remain faithful to real production state, since those reads only need the *real* file loaded once, not written to continuously.

---

## 17. Candidate Isolation Architectures (Designed, Not Implemented)

**A — Monkeypatch the path constant before first access.** Set `echo_model_orchestrator.RIVER_BRAIN_PATH` to a copy of the real file in a scratch directory, *before* calling `get_river_brain()` for the first time (not after, unlike the current `install_isolation()`). Cheapest fix, smallest diff, closes threat #2 completely (the writer thread would still run, but against an isolated copy, harmlessly). Does not address threat #4 (torn reads) since it doesn't touch locking, but that threat only applies to the *live* path, which this approach never touches.

**B — Separate state directory per run.** Copy the entire relevant slice of `memory/` (or at minimum `river_brain.pkl` + `.lock`) into a fresh temp directory per invocation, and redirect every relevant path constant (`RIVER_BRAIN_PATH`, and potentially `task_type_classifier.py`'s `_CLASSIFIER_PATH` for future-proofing per threat #7) there. Slightly more setup than A but generalizes cleanly to the second singleton this mission found and to any future ones.

**C — Copy-on-write / read-only real state, write to a black hole.** Load the real file once (as today), but replace `RIVER_BRAIN_PATH` with `/dev/null`-equivalent or an in-memory-only sentinel *before* the writer thread's first `_do_save()` can fire, so writes are attempted and harmlessly discarded rather than redirected to a real (if scratch) file. Marginally simpler than B, but produces less useful post-hoc auditability (no artifact to inspect afterward) than A/B.

**D — Separate process, no shared filesystem for the state files specifically.** Run experiments inside a container or chroot with `memory/river_brain.pkl` bind-mounted read-only, or not mounted at all (forcing a fresh, empty RiverBrain — losing the "faithful to real production ranking" property the current proxy design deliberately preserves). Strongest isolation, most implementation cost, and changes the experiment's own scientific properties (council selection would no longer reflect real historical performance) unless the real file is still made available read-only somehow — which reintroduces exactly the write-redirection problem A/B/C solve more directly.

**E — Separate environment/config namespace.** Not directly applicable to this specific file-based singleton problem; more relevant to threat #5 (Ollama contention) via a separate `OLLAMA_HOST`, which is a different, complementary problem this section does not treat as in scope for the RiverBrain-specific fix.

**F — Full container/VM isolation.** Same tradeoffs as D, at higher operational cost, with no additional benefit specific to this threat model beyond D.

**G — Hybrid: A/B for RiverBrain and task_type_classifier + read-only real snapshot for score fidelity.** Load the real file once for read-fidelity (as today), immediately redirect the path constant so any subsequent write (explicit or timer-driven) lands on an isolated copy, and leave the proxy's no-op behavior on the four explicit methods as an intentional, harmless second layer (defense in depth, not the sole mechanism). This is the design that most directly closes the gap this mission found while preserving everything the current mechanism already does correctly.

**No architecture is recommended for implementation in this mission — analysis and design only, per Section 1's constraint.**

---

## 18. Falsification Criteria (fixed before any further work, not adjusted after the fact)

**This report's "PARTIALLY ISOLATED" verdict would be falsified — shown too pessimistic — if:**
- A direct test (not attempted in this mission, since it would require executing code) showed `RiverBrain.__init__()` does *not* actually start `_writer_thread` unconditionally — e.g., if some guard elsewhere prevents it in a context this reading missed.
- The ~229 estimated unblocked `_do_save()` calls during Tier-4 turned out to be systematically prevented by some mechanism not found in this reading (e.g., if `RIVER_AVAILABLE` were `False` in the experiment's environment, `_init_classifiers()` no-ops, but the writer thread itself is unconditional regardless of `RIVER_AVAILABLE` — confirmed by re-reading `__init__`, this guard does not apply here).

**This report's "CLEAN" classifications for Tier-4/Tier-5-REFACTOR would be falsified — shown wrong — if:**
- Evidence emerged of a `run.py` process (or any other process instantiating a real `RiverBrain`) active during 2026-09-04T20:09:17Z–2026-09-05T06:47:52Z that left no trace in `memory/echo_watchdog.log` at all — e.g., a manually-run `python run.py` in a separate terminal without the standard `tee -a` redirect into that log file. This report's own total-log-silence evidence cannot rule this out with certainty; it is the single largest residual uncertainty in this document, disclosed here rather than glossed over.

**This report's "POTENTIALLY CONTAMINATED" classification for the Tier-3 dev-sanity run would be falsified downward (to CLEAN) if:**
- The live process's `[RIVER] Brain persisted` lines during 2026-09-04T05:38:53Z–05:49:17Z turned out, on closer reading, not to be genuinely concurrent with the script's own execution — but this was checked directly (Section 13) and the overlap is unambiguous from timestamps alone.

**It would be falsified upward (to DEMONSTRABLY CONTAMINATED) if:**
- The Tier-3 dev-sanity script's own stdout or a similar artifact were later located showing a "[RIVER] Save skipped" line, or if `dev_sanity_results.jsonl`'s own recorded `observation_counts`-adjacent fields (none currently captured) showed a value inconsistent with either process's expected trajectory.

---

## 19. Answers to the 15 Required Adversarial Questions

1. **Does merely importing `echo_model_orchestrator` start any thread?** No. `_RIVER_BRAIN_INSTANCE = None` is a plain module-level assignment; the singleton and its thread are only created inside `get_river_brain()`, which must be explicitly called.

2. **Does `install_isolation()` stop the RiverBrain writer thread?** No — confirmed by source (Section 4) and by the fact that nothing in `install_isolation()` ever references `_writer_thread`, `_save_queue`, or calls `.shutdown()`.

3. **Can two processes' RiverBrain objects race in-memory?** No — they are always in separate address spaces (Section 2). Any race is filesystem-level only, via `memory/river_brain.pkl`.

4. **Is the pkl write atomic?** No (Section 5) — direct `open(...,"wb")`, not tmp+`os.replace()`, unlike this same codebase's own `IntrospectionChannel._save_drift_detectors()`.

5. **Does the "richer pkl" guard fully protect against overwrite?** No — it only compares summed `observation_counts`, ignores `classifiers`/`scalers`/`model_task_stats` staleness, and only protects the direction "lower count refused," not "equal-or-higher count unconditionally allowed" (Section 5).

6. **Did the Tier-5-counterfactual and Tier-6-disagreement scripts ever risk RiverBrain contamination?** No, structurally — confirmed via fresh grep this session; neither script imports or calls anything RiverBrain-related (Section 13), correcting a more cautious prior characterization.

7. **Did the original Tier-4 stage1/stage2 data collection run concurrently with a live production process?** No — its full execution window falls entirely within a confirmed ~10.6-hour total-silence gap in the production log (Section 13).

8. **Did the Tier-5 REFACTOR mission's `install_isolation()`-using scripts run concurrently with a live production process?** No — same gap, confirmed via `stat`-derived file mtimes for all six scripts' log outputs (Section 13).

9. **Did *any* historical experiment definitely run concurrently with a live, actively-writing production process?** Yes — the Tier-3 apparatus's dev-sanity run (Section 13), the one case in this entire investigation with direct, unambiguous log evidence of overlap.

10. **Did that overlap definitely corrupt production data?** Not established either way — the mechanism (Section 5) suggests any corruption would be transient and self-healing given the live process's continuously climbing observation count, but no direct evidence (a "Save skipped" line attributable to the script, or a discontinuity in the live file) was found to confirm or rule this out (Section 13).

11. **Is `task_type_classifier.py` at the same risk as RiverBrain?** Structurally similar singleton shape, but no autonomous background thread exists for it (Section 3) — the specific mechanism this mission investigates does not apply to it, though it was never touched by any audited historical script regardless.

12. **Are FAISS/`memory_meta.json` at risk from these experiments?** Not historically — none of the audited scripts ever call the functions that write to them (Section 14).

13. **Is there any network isolation?** None, by design — real Ollama calls are the point of these experiments; this creates resource contention risk, not state-contamination risk (Section 9).

14. **Is there any config/environment isolation?** None — all scripts read the same real `memory/`, same real `self_edit_generated.py`, same real Ollama endpoint as production (Section 10).

15. **Can this be fixed without touching any production safety gate (F1/F2/F3), training-signal path, or protected file?** Yes — every candidate architecture in Section 17 touches only the experimental harness's own path-redirection, before any RiverBrain access, and none require modifying `self_edit_manager.py`'s protected pipeline, `EDIT_FORBIDDEN_TARGETS`, or any training-signal call site.

---

## 20. Summary Table — Final Per-Tier Verdicts

| Tier / Artifact | Verdict |
|---|---|
| Tier-3 apparatus, `main()` dev-sanity | POTENTIALLY CONTAMINATED (real overlap demonstrated; permanent-corruption unconfirmed either way) |
| Tier-3 apparatus, `main_heldout()` | UNKNOWN (timing too close to call) |
| Tier-4 stage1 | CLEAN |
| Tier-4 stage2 | CLEAN |
| Tier-5 counterfactual replay | CLEAN (structural) |
| Tier-6 disagreement analysis | CLEAN (structural) |
| Tier-5 REFACTOR mission scripts | CLEAN (timing) |
| Tier-7 | CLEAN (by construction, per carried-forward methodology description) |
| **System-wide isolation guarantee** | **PARTIALLY ISOLATED — not a guarantee, a partial, empirically-verified-in-both-directions mitigation** |

**Recommendation, not an instruction to build**: before any future 100–500-task experiment, adopt Section 17's Architecture G (or the simpler A) so that the one confirmed structural gap — the unpatched background writer thread — is closed by construction rather than relying on no `run.py` process happening to be alive, which was true for most but not all of this project's own experimental history to date.
