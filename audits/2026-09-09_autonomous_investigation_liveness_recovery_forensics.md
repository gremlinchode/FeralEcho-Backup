# Autonomous Investigation Liveness & Recovery Forensics

**Date:** 2026-09-09
**Mission status:** INVESTIGATION ONLY. No production code, configuration, or Git history modified. No fix applied. No manual invocation, no manual success marking, no fabricated retry, no cleanup of the failed project, no log clearing.

---

## 1. Executive Verdict

**VERIFIED LIVENESS FAILURE, with root cause left explicitly UNRESOLVED between a genuine code-level lifecycle defect and a benign environmental (OS-suspend) explanation — both remain live possibilities, and this report does not pick between them without more evidence than is currently available.**

Across a confirmed, uninterrupted, single-process observation window of **8.06 hours** — comfortably exceeding the mission's 6-hour minimum and reaching its preferred 8–12-hour range — `echo_projects_autonomy`'s scheduling loop evaluated `should_run_cycle()` exactly **once**, at process startup, and never again, despite its own `time.sleep(21600)` (6 hours) having clearly elapsed relative to wall-clock time. The host process itself remained fully healthy throughout (heartbeat continuously current); this is not a dead server, it is one specific background thread that stopped producing observable activity. No unhandled-exception log line was ever recorded for this thread, which rules out the single most obvious failure mode (an uncaught Python exception killing it) without ruling out a more subtle threading-level failure, or — a real, evidence-supported alternative surfaced directly by this investigation's own working conditions — an OS-level suspend event during a long, unattended `time.sleep()` call extending its real completion time well past the naive 6-hour mark.

**Separately, and just as important**: this mission's own historical archaeology found that `echo_projects_autonomy` has a **0/61 (0%) lifetime real-world success rate** — every one of its 61 real autonomous attempts since 2026-08-11 failed at either F1 (48/61) or F2 (13/61). This is a materially more severe, independently-confirmed finding than the liveness question alone, and it means that even a fully "recovered," perfectly-scheduled loop would still be demonstrating retry without recovery, not genuine autonomous success, on the evidence gathered to date.

---

## 2. Research Question

> When `echo_projects_autonomy` experiences a real execution failure, does the architecture independently detect it, preserve state, retry or reschedule, and eventually produce another autonomous investigation opportunity without human intervention?

Answered in two parts, precisely, per this mission's own discipline against conflating them:
- **Does the scheduling mechanism retry after a failure, historically?** **Yes, repeatedly** — 11 real "Cycle complete" events over 26 days (2026-08-11 to 2026-09-06), each following a prior failure, confirms the loop has a genuine, demonstrated, multi-week history of resuming after individual cycle failures.
- **Is the scheduling mechanism currently alive and executing on schedule, right now, during this specific 8+ hour observation?** **No** — confirmed by direct, repeated, live querying of the process's own in-memory scheduling record, not inferred.

---

## 3. Competing Hypotheses (as given, plus one added by this investigation)

- **H1 — Genuine autonomous recovery/lifecycle defect.** Not confirmed, not ruled out. No supporting exception evidence found; a subtler thread-level failure (one that wouldn't be caught by the loop's own `try/except Exception`) remains possible and unproven.
- **H2 — Investigation-induced starvation (restart-driven).** **Ruled out as the explanation for the *current* 8+ hour silent period specifically** — this mission confirmed, via direct, repeated process-identity checks, that the exact same server process (PID 50015) ran continuously and without interruption for the entire observation window. H2 remains a real, evidence-supported explanation for the *broader historical pattern* of irregular gaps (see Section 13), just not for this specific window.
- **H3 (new, added by this investigation) — OS-level suspend extending a long single `time.sleep()` call's real completion time.** Directly motivated by this session's own working conditions (the user's laptop is closed and reopened repeatedly during a work shift). Plausible, not provable from currently available evidence, and **not distinguishable from H1 using anything short of adding new instrumentation, which this mission was not authorized to do.**

---

## 4. Last-Failure Reconstruction

```text
scheduler trigger (2026-09-06T10:43:56Z, per memory/echo_projects_autonomy_state.json;
                    log line 2026-09-06 03:43:56 PDT confirms, PDT = UTC-7)
      ↓
task selection: curiosity-garden entry "How can we reconcile our personal narratives
                 with the vast, seemingly random nature of human experience..."
      ↓
investigation start: council-planned 6-file spec (main.py, narratives.py,
                      randomness.py, reconciler.py, visualize.py, storyteller.py)
      ↓
F1 (per-file static scan): OK for all 6 files — CONFIRMED, direct report read
      ↓
F2 (multi-file sandboxed import+execution): FAIL
      ↓
exception: **UNPROVEN — the persisted traceback is itself truncated mid-line**
           ("from narratives import Stor", cutting off before the class name
           is even complete, and before any exception type/message is ever
           shown). Direct inspection of narratives.py confirms it DOES define
           `class Story` — meaning the "broken cross-file import" read this
           mission's own predecessor audit (Mission 21) gave for this failure
           is likely WRONG, or at minimum unconfirmed by the actual evidence.
           **This is an explicit correction to Mission 21's characterization,
           not a silent one** — see Section 12.
      ↓
exception handling path: the outer `except Exception as _epe:` in
           `_echo_projects_autonomy_loop()` (run.py:1490) — CONFIRMED by
           direct source read, this is the only handler between the cycle
           call and the loop's own log line
      ↓
failure classification: logged as "status=f2_failed" to
           memory/echo_projects_autonomy_state.json and
           "[ECHO-PROJECTS-AUTONOMY] Cycle complete: status=f2_failed" to
           memory/echo_watchdog.log — CONFIRMED
      ↓
retry/reschedule decision: unconditional — `time.sleep(21600)` sits AFTER
           and OUTSIDE the try/except, at the bottom of the `while True:`
           body (run.py:1492) — CONFIRMED by direct source read. There is
           no failure-counter, no backoff, no dead-letter state, no
           project-avoidance logic of any kind gating the next attempt.
      ↓
state persistence: memory/echo_projects_autonomy_state.json (last_run_utc,
           last_status, spec_source) — CONFIRMED, a plain 3-field JSON
           write, no retry counter field exists in this schema
      ↓
next scheduler opportunity: ~2026-09-06T16:43:56Z (6h later, IF the same
           process/thread survived that long) — **UNPROVEN whether this
           specific opportunity occurred**, since the server has been
           restarted multiple times since (this session's own history:
           confirmed stopped before Mission 19, confirmed running again
           for Mission 21, confirmed as PID 50015 since 2026-09-09T00:07:34Z)
      ↓
actual retry (during this mission's own observation window,
           2026-09-09T00:07:34Z onward)?: **YES, once** — a real
           `should_run_cycle()` evaluation occurred at 00:14:02Z (~7 min
           after process start, matching the loop's documented 300s
           startup delay almost exactly), correctly gated False on
           `skipped_reason: "conversation_active"` — CONFIRMED live
      ↓
actual investigation (this window)?: **NO** — the gate correctly
           deferred, so no investigation attempt was made
      ↓
success / repeat failure / abandonment (this window)?: **NONE OF THESE
           OCCURRED** — the loop never reached a second `should_run_cycle()`
           evaluation at all during the entire 8.06-hour observation,
           despite one being due ~06:14:02Z. This is the mission's central,
           live finding.
```

---

## 5. Scheduler Architecture

`run.py:1472-1493`, `_echo_projects_autonomy_loop()`, launched via `safe_start_thread(_echo_projects_autonomy_loop, name="EchoProjectsAutonomy")` (a plain `threading.Thread(daemon=True)`, no process/subprocess isolation). Exact structure, confirmed by direct read:

```python
def _echo_projects_autonomy_loop():
    time.sleep(300)                          # one-time startup delay
    while True:
        try:
            if should_run_cycle("echo_projects_autonomy"):
                result = _run_with_soft_timeout(autonomous_generate_project, timeout_s=2700)
                # ... log result ...
            else:
                logger.debug(...)             # skip, logged at DEBUG (not visible
                                               # in a normal WARNING/INFO-level tail)
        except Exception as _epe:
            logger.warning(f"[ECHO-PROJECTS-AUTONOMY] Cycle error: {_epe}")
        time.sleep(21600)                     # UNCONDITIONAL, every path leads here
```

**Key architectural facts, all confirmed:**
- **Interval**: fixed 21600s (6h), no jitter, no backoff, identical after success, failure, timeout, or skip.
- **Initial delay**: 300s.
- **Worker**: a single daemon thread, launched once at process start, never re-launched by anything if it exits.
- **Lifecycle owner**: nothing. `safe_start_thread()` (run.py:201-212) wraps the target in a try/except that logs `[Thread:{name}] Unhandled exception` on a genuine escaped exception — **but performs no restart, no re-launch, no supervision of any kind**. If this thread ever terminates for any reason (an exception escaping even its own internal handler, or any other cause), nothing in this codebase would ever restart it short of a full process restart.
- **State survival across restart**: `memory/echo_projects_autonomy_state.json` (last outcome) persists; the in-memory `_last_cycle` dict backing `get_autonomy_status()` (in `autonomy_coordinator.py`) does **not** — confirmed by direct source read, it's a plain module-level dict, reset to empty on every process start.
- **Missed cycles**: not replayed. A 6-hour fixed sleep with no catch-up logic means any gap (restart, suspend, or genuine stall) simply pushes the next real attempt later — nothing "makes up" for lost time.
- **Concurrent execution**: not possible for this specific loop (single thread, single `while True:`), though `_run_with_soft_timeout()`'s own abandoned-thread-on-timeout behavior (documented in the code's own extensive comment, run.py:1424-1452) means a genuinely stuck underlying call could keep running harmlessly in the background after the loop itself has moved on — a different, already-understood and accepted risk, not the mechanism observed here.
- **Wall-clock vs. process-relative scheduling**: `time.sleep()` — **this is the crux of the H1-vs-H3 ambiguity.** Python's `time.sleep()` on macOS blocks the calling thread for approximately the requested duration of *process-perceived* time; how that interacts with a full OS-level system suspend (the machine going to sleep) was not established by this investigation and would require either documentation research or direct experimentation this mission was not authorized to perform.

---

## 6. Liveness Ledger Semantics

| Signal | What it proves | What it does NOT prove |
|---|---|---|
| Process sentinel heartbeat (`memory/echo_sentinel.json`) | The main Flask process is alive and its top-level loop is executing | Any specific background thread (including this one) is alive or doing anything |
| `/admin/liveness-status`'s `echo_projects_autonomy_activity` check | A staleness threshold (2x the 6h cadence) has or hasn't been exceeded, computed from the *persisted* `last_run_utc` | Whether the loop is currently trying and failing, currently stalled, or genuinely dead — the check cannot distinguish these, by its own design (confirmed via direct source read of its evaluation logic) |
| `get_autonomy_status()`'s `echo_projects_autonomy` in-memory record | Whether `should_run_cycle()` has been invoked since the current process started, and with what result — **this is the single most informative live signal available**, and it is what this mission used to establish the central finding | Nothing about *why* it hasn't been invoked again — that requires the causal reasoning in Section 3/12 |
| `memory/echo_projects_autonomy_state.json` | The outcome of the most recent *completed* cycle, whenever that was | Whether any cycle has been *attempted* since — a completed-cycle record and a currently-running/stalled loop are not distinguishable from this file alone |
| `[ECHO-PROJECTS-AUTONOMY] Cycle complete` log lines | A cycle genuinely ran to completion (success or failure) | Anything about cycles that never reached completion (e.g., a genuinely stuck thread would produce zero log output, indistinguishable at this signal from "hasn't been due yet") |
| `sandbox/echo_projects/` directory count/newest entry | A new project artifact was genuinely produced | Nothing about failed attempts that never reached artifact-writing, or about scheduling health |

**The single clearest example of a "false positive of liveness" this mission found**: the Liveness Ledger's own `echo_projects_autonomy_activity` check, read in isolation, correctly reports the real staleness — it is not a false positive itself. But a naive read of `memory/echo_sentinel.json` alone (process heartbeat) *would* be a false positive of subsystem liveness — exactly the "process alive ≠ subsystem alive" distinction Section 12 of the mission brief anticipated, and exactly what this investigation confirmed is real and currently occurring.

---

## 7. Cross-File Import Failure Reconstruction

**Correction to Mission 21's characterization, stated explicitly per this mission's own discipline.** Mission 21's audit described this as "a real cross-file import inconsistency" based on a truncated log preview. Direct, full inspection this session found:

- `main.py` line 2: `from narratives import Stor` — the persisted traceback text itself is cut off mid-word, before showing any exception type or message.
- `narratives.py` line 27: `class Story:` — **the class genuinely exists**, under the exact name the (truncated) import line appears to be requesting.

**Classification: Type T4 — unknown.** The actual root cause of this specific F2 failure cannot be determined from the evidence the system itself persisted — the capture mechanism truncated the real error before it ever recorded the exception type. This is a **separate, real observability defect** (the error-capture path in the F2 sandboxed-execution pipeline can silently truncate a traceback before the actually-informative part), not the "broken import" defect previously assumed. **POTENTIAL REMEDIATION — NOT APPLIED**: the capture logic should either not truncate, or truncate only after preserving the exception type/message line, which is far more diagnostically valuable than the source-line echo currently being cut off instead.

**Broader pattern check across all 13 historical F2 failures**: this exact truncation pattern was **not** systemic — most other F2 failures show complete, real tracebacks ending in genuine code lines. Two of the 13 (`20260826T042413Z`, `20260902T151058Z`) show a different, distinct failure mode entirely: `"detail: sandbox test timed out"` — a timeout, not a code-level exception at all. A third, now-historical class of failure (matplotlib's config/cache directory attempting to write outside the sandbox's writable scope) was found, already diagnosed, and already fixed via a documented 2026-09-05 change to `sandbox/safe_exec_wrapper.py` (confirmed present in current source, `MPLCONFIGDIR` now redirected into the scratch directory) — this fix predates and is unrelated to the 09-06 failure under investigation, and was not touched or re-verified beyond confirming its presence.

---

## 8. Recovery-Path Analysis

| Mechanism | Classification |
|---|---|
| Retry after failure (via unconditional `time.sleep(21600)` at loop end) | **IMPLEMENTED + OBSERVED** — 11 real historical cycles across 26 days confirm this genuinely executes repeatedly over time |
| Exponential backoff | **ABSENT** — confirmed by direct source read, the sleep duration never varies |
| Failure counter / retry budget | **ABSENT** — `echo_projects_autonomy_state.json`'s schema has no such field |
| Dead-letter / abandonment state | **ABSENT** — no mechanism marks a repeatedly-failing spec as permanently abandoned; the same curiosity-garden question could in principle be re-selected indefinitely (not confirmed either way this session — `spec_source: "garden"` selection logic was not re-traced) |
| Task requeue | **ABSENT** — no queue exists; each cycle independently re-selects from the curiosity garden |
| Persistent retry state across restart | **ABSENT for the in-memory scheduling record** (`get_autonomy_status()` resets on restart); **PRESENT for the last-outcome record** (`echo_projects_autonomy_state.json` persists) |
| Cooldown logic | Present only in the trivial sense of the fixed 6h interval itself — no adaptive cooldown |
| Exception swallowing | **IMPLEMENTED + OBSERVED** — both the loop's own inner `try/except Exception` and `safe_start_thread()`'s outer wrapper exist and would catch a genuine Python exception; **neither was observed to fire during this mission's window**, because no exception occurred (the loop simply never re-entered its check) |
| Worker supervision / thread restart-on-death | **ABSENT** — confirmed, this is the most consequential gap found in this section. `safe_start_thread()` logs an unhandled exception if one occurs but never relaunches the thread |
| Watchdog interaction | The process-level watchdog (`start_echo.sh`) supervises the *entire `run.py` process*, not individual internal threads — confirmed out of scope for this specific failure mode |
| Stale-task recovery | **ABSENT** — nothing detects "this thread should have produced activity by now and hasn't" except the passive Liveness Ledger check, which only reports staleness, takes no corrective action |
| Timeout recovery (within a single cycle) | **IMPLEMENTED + OBSERVED** (indirectly) — `_run_with_soft_timeout()`'s 45-minute soft ceiling is real, documented, and tested code (per its own extensive in-line commentary describing a `ThreadPoolExecutor` approach tried and rejected), but was not directly observed firing this session (no cycle was attempted during the observation window to exercise it) |
| Idempotency / duplicate-task suppression | Not applicable — no concurrent-execution risk exists for this specific single-threaded loop |

---

## 9. Natural Observation-Window Results

**Purely passive, read-only observation, confirmed by design and by review of the monitoring script used**: two sequential background scripts, run outside any production code path, that only ever read `memory/echo_sentinel.json`, `memory/echo_projects_autonomy_state.json`, `sandbox/echo_projects/`'s directory listing, and the read-only `GET /admin/liveness-status` / `GET /admin/autonomy-status` HTTP endpoints — no write, no POST, no invocation of any Echo function, confirmed by direct review of the monitoring scripts' own source before launch.

**Phase 1** (5-minute polling, `m22_observations.jsonl`): baseline captured at process uptime 16834s (4.68h); ran until process uptime reached 22681s (**6.303h**), the mission's minimum target, with **zero state changes** across 8 polls (`projects_count` fixed at 61, `last_run_utc` fixed at `2026-09-06T10:43:56Z` throughout).

**Phase 2** (2-minute tight watch specifically on the live in-memory scheduling record, `m22_tight_watch.jsonl`): ran until process uptime reached **29067s (8.07h)**. **`echo_projects_autonomy`'s `last_check_utc` remained frozen at `2026-09-09T00:14:02.691648Z` across all 15 polls in this phase — never once advancing**, despite the loop's own `time.sleep(21600)` (due to elapse ~06:14:02Z) having been overdue by up to nearly 2 hours by the final poll.

**Process identity confirmed unbroken throughout both phases**: PID 50015, `start_utc: 2026-09-09T00:07:34.147848Z`, unchanged in every single observation. **This rules out H2 (restart-induced starvation) as the explanation for this specific 8+ hour window** — there was no restart to blame.

**Silence is the data, and it is precise**: one real scheduling evaluation occurred, correctly deferred to a live conversation (this investigation's own activity), and then nothing — for over 8 continuous hours on an unbroken process, well past when the very next evaluation was due.

---

## 10. Restart-Recovery Results

**Not performed.** Per this mission's own instruction ("only after the natural-window experiment is complete should you consider a controlled restart-recovery observation... if necessary and safe"), and given the natural-window experiment already produced a clear, decisive result (a confirmed liveness anomaly, not ambiguous silence), a restart was judged unnecessary to add further information at this stage, and — per the mission's own absolute constraint — was not performed. This is flagged in Section 18 as the most valuable next experiment specifically because it was deliberately not run here.

---

## 11. Human-Intervention Contamination Analysis

**Quantified, not assumed.** Reconstructing this session's own history against the loop's real historical firing pattern:

- **Confirmed available autonomous runtime, this specific investigation's window**: 8.07 continuous hours, one unbroken process, zero restarts — a clean, uncontaminated window.
- **Confirmed human-intervention-interrupted runtime, immediately preceding this window**: this session's own record shows `run.py` was live at the start of Mission 15/16, confirmed stopped by the user before Mission 19 began, and confirmed running again (as the current PID 50015, started `2026-09-09T00:07:34Z`) by the start of Mission 21 — at least one genuine, human-confirmed restart occurred within this exact multi-mission investigation period, between Missions 16-18 and Mission 19.
- **A second, longer-run, pre-existing pattern, independent of this session's own missions**: the watchdog log's own restart history (Section 5's git-archaeology cross-reference) shows several `[WATCHDOG] Echo exited with code 0. Restarting in 10s` events on 2026-09-08 alone, hours apart, well before this specific investigation began — confirming the server was already being restarted with some regularity in the days immediately preceding this mission, for reasons outside this session's own visibility (the exit code 0 in each case indicates a clean, intentional shutdown, not a crash).
- **The historical 43-hour gap found between the 2026-09-04T08:15:02 and 2026-09-06T03:43:56 cycles (Section 4)** predates this entire investigation thread and cannot be attributed to this session's own forensic activity — it is independent evidence that irregular, multi-hour-to-multi-day gaps in this loop's real firing pattern are a **recurring, pre-existing characteristic**, not something newly introduced by Missions 19-22's own observation.

**Conclusion, stated as precisely as the evidence allows**: the *current* 65.9+-hour-and-growing silent gap cannot be attributed to restart-starvation for at least the most recent 8+ hours of it (directly disproven by this mission's own clean observation window) — but earlier portions of the same gap, and the broader historical pattern of irregular multi-day silences, remain plausibly explained by a combination of genuine restarts (confirmed, at least one) and the newly-surfaced H3 possibility (OS suspend). **The honest picture is layered, not single-cause**, and this report does not collapse it into one explanation.

---

## 12. Illusion-of-Recovery Analysis

This is the section this mission specifically flagged as mandatory, and the investigation found a real, concrete instance of exactly this failure shape — **in the predecessor audit, not in the running system**:

**Mission 21's own report is itself a mild instance of "heartbeat without work" reasoning, corrected here.** Mission 21 observed the liveness check's evidence string (mentioning "a real cross-file import problem") and treated the truncated log excerpt as sufficient basis for a specific causal claim ("a broken cross-file import") — when the actual underlying evidence, read in full this session, does not support that specific claim (the imported class genuinely exists). This is precisely the "a system logs a failure ... and therefore appears diagnosed — but the diagnosis was never actually confirmed" pattern this mission's Section 13 asks to search for, found not in Echo's own architecture but in this research program's own prior audit output. **Recorded here as a direct, explicit correction, not smoothed over**, consistent with this project's own standing discipline (`research/OPEN_QUESTIONS.md`/`DECISIONS.md`'s "preserve the contradiction" rule).

**Within the running system itself**: no instance of "heartbeat-without-work," "dispatch-without-execution," or "successful-status-without-investigation" was found — if anything, the opposite problem was found (Section 1): the system is honestly, correctly *not* claiming success anywhere (the Liveness Ledger check fails loudly, exactly as designed, and nothing in the codebase papers over the 65.9+-hour gap with a fabricated healthy status).

---

## 13. Historical Git Archaeology

```
93e3456  Add echo_projects: sandboxed multi-file generation with full library access
6dd2229  Add !project: invoke the council to generate echo_projects content
6d98e18  Make echo_projects genuinely autonomous, not just manual-invocation   (2026-07-23)
fe05f93  Raise echo_projects retention cap 20 -> 60
f5d9b33  Finding 91: four cheap, safe fixes from the capability-ceiling research
```

**The scheduler's exact retry architecture (`time.sleep(21600)` unconditionally at the bottom of the loop, no backoff, no failure counter) was introduced at the feature's original creation in commit `6d98e18` (2026-07-23) and has not been modified since** — confirmed via `git log -p -S "_echo_projects_autonomy_loop" -- run.py`, no later commit touches this specific control-flow structure. **This is a longstanding architectural characteristic, not a recent regression.** The one later, relevant change (`f5d9b33`, Finding 91) touched the RiverBrain quality-scoring metric this loop's *generation* step indirectly depends on, not its scheduling/retry logic. No evidence of a reverted fix, renamed function, or abandoned architectural migration specific to this scheduling mechanism was found.

---

## 14. Causal State Machine

```text
THREAD_STARTED
      ↓ (sleep 300s)
SCHEDULED
      ↓
RUNNING (should_run_cycle evaluation)
      ├── SKIPPED (throttle / stillness / conversation_active)
      │        → recorded in-memory (get_autonomy_status) — CONFIRMED, observed live
      │        → falls through to unconditional sleep(21600) — CONFIRMED by source
      │        → SCHEDULED (next iteration)
      │
      ├── DISPATCHED → autonomous_generate_project() (soft-timeout wrapped)
      │        ├── SUCCESS → COMPLETE → state persisted → sleep(21600) → SCHEDULED
      │        │        **0/61 real historical occurrences — never observed**
      │        ├── FAILURE (F1/F2) → state persisted (status=fN_failed) →
      │        │        sleep(21600) → SCHEDULED
      │        │        **13+48 = 61/61 real historical occurrences**
      │        └── TIMEOUT (45min soft ceiling) → result=None → logged →
      │                 sleep(21600) → SCHEDULED
      │                 **not observed this session; documented, untested this pass**
      │
      └── UNHANDLED EXCEPTION (escapes should_run_cycle or the dispatch call)
               → caught by the loop's own try/except → logged as "Cycle error" →
                 sleep(21600) → SCHEDULED
               **zero occurrences found in the full watchdog log history for
               this thread — never observed**

STALLED  (this mission's central live finding — a state the mission's own
          suggested diagram left as "???")
      ↓
   Thread has entered SCHEDULED (mid-sleep) and has not been observed to
   re-enter RUNNING despite the scheduled duration having clearly elapsed.
   No transition out of STALLED was observed during this mission's 8.07h
   window. Whether this state is truly terminal (the thread has silently
   exited or hung, per H1) or merely extended (an OS-suspend-lengthened
   sleep, per H3) is UNPROVEN — this is the one genuinely open transition
   in this entire state machine.
```

**Every transition above is evidence-backed except the single arrow leading out of STALLED, which is explicitly marked UNPROVEN, per the mission's own instruction not to infer an unestablished transition.**

---

## 15. Quantitative Liveness Metrics

| Metric | Value | Basis |
|---|---|---|
| Real historical scheduler executions producing a logged outcome | 11 | Direct `grep` of `memory/echo_watchdog.log`, 2026-08-11 to 2026-09-06 |
| Real autonomous investigation attempts (report artifacts) | 61 | Direct directory count, `sandbox/echo_projects/` |
| Successful completions (both F1 and F2 passed) | **0** | Direct check of all 61 reports — zero contain a passing F2 with no FAIL |
| F1-stage failures | 48 (78.7%) | Direct grep across all 61 reports |
| F2-stage failures | 13 (21.3%), of which 2 were timeouts and 1 (the most recent) has an unrecoverable/truncated root cause | Direct read of all 13 F2-FAIL reports |
| Confirmed uninterrupted observation window, this mission | 8.07 hours | Live sentinel + monitor logs, single unbroken PID |
| Scheduler evaluations observed during that window | 1 (at window start) | Live `get_autonomy_status()` queries, unchanged across 23 total polls spanning both monitoring phases |
| Maximum observed silent period (current, ongoing at report time) | ≥67.7 hours since last completed cycle; ≥2 hours since the *next* cycle was structurally due | Cross-referenced liveness evidence strings + this mission's own direct timestamp math |
| Mean time to next attempt, historically (excluding the current anomalous gap) | Irregular — ranged from ~5.7h to ~43h between consecutive logged cycles across the 26-day history | Direct interval calculation from the 11 log timestamps |
| Percentage of the current gap explainable by confirmed human intervention | **INSUFFICIENT SAMPLE to state a precise percentage** — at least one confirmed restart occurred in the relevant period (Section 11), but the exact cumulative downtime this restart and others account for, versus genuine in-process silence, was not fully reconstructable from available logs |

---

## 16. Evidence Table (summary)

| Signal | Confirms | Does not confirm |
|---|---|---|
| Live `get_autonomy_status()` record, unchanged across 23 polls / 8.07h | The scheduling loop has not re-evaluated its gate since process start + ~7min | Why — see H1/H2/H3 |
| `echo_watchdog.log`'s 11 historical "Cycle complete" lines | The loop has a real, multi-week history of resuming after failure | That it will always do so — this specific window shows it currently is not |
| 0/61 successful reports | The autonomous-investigation capability has never once produced a working artifact | Nothing about the scheduling-liveness question — these are separate, both-confirmed-negative findings |
| Truncated F2 traceback | The system's own error capture is sometimes incomplete | The originally-assumed "broken import" cause — that claim is now unsupported |
| Unbroken PID across the full observation window | H2 does not explain this specific window | H1 or H3 — both remain open |
| Zero `[Thread:EchoProjectsAutonomy] Unhandled exception` log lines, ever | An uncaught Python exception did not kill this thread | That the thread hasn't died some other way, or isn't merely extended-sleeping |

---

## 17. Unresolved Questions

1. Is the thread genuinely stalled/dead, or is it a `time.sleep(21600)` call whose real completion has been extended by OS-level suspend? **Not resolved by this mission** — would require either code instrumentation (out of scope) or a controlled restart-recovery observation (Section 10, deliberately not performed here).
2. What was the true root cause of the 2026-09-06 F2 failure, given the persisted traceback is truncated before showing it? **Not resolved** — the evidence needed no longer exists in a usable form.
3. What fraction of the historical 26-day firing-interval irregularity (Section 15) is attributable to restarts vs. genuine in-process stalls vs. suspend effects? **Not resolved** — insufficient log granularity to reconstruct precisely.
4. Does `_run_with_soft_timeout()`'s 45-minute soft-timeout path actually fire and behave as documented in a live cycle? **Not exercised this session** — no cycle was attempted during the observation window.

---

## 18. Recommended Next Experiment

**The single most valuable next step, precisely because it was deliberately not performed here**: a controlled, disclosed restart, with full before/after state capture (per Section 10's own checklist), specifically to observe whether the very next scheduling evaluation occurs promptly after the standard 300s startup delay. If it does, that is strong, direct evidence the current thread's specific stall (not the underlying capability itself) is the actual defect, and that a plain restart is sufficient recovery — genuinely useful operational knowledge regardless of which of H1/H3 turns out to be true. If it does *not* recur promptly, that would materially strengthen H1. This experiment was intentionally deferred rather than run reflexively, per the mission's own sequencing instruction.

**Second priority**: fix the F2 error-capture truncation (Section 7's POTENTIAL REMEDIATION) — independent of the liveness question, and directly useful for correctly diagnosing the *next* real F2 failure whenever the loop does run again.

**Third priority**: given the 0/61 lifetime success rate is now precisely quantified and is arguably the more severe of this mission's two headline findings, a dedicated follow-up investigating *why* F1 alone accounts for 78.7% of failures (is it one recurring generation pattern, or genuinely diverse causes?) would likely be higher-value than further liveness archaeology on the scheduling question alone.

---

## 19. Production-Modification Audit

```
HEAD (start and end): 525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged)
Tracked modifications (start and end, identical, none touched):
  M app/core/echo_ground_truth.py, claude_relay/from_m5.md,
  M logs/janitor_report.json, sandbox/scripts/temp_self_edit.py
```
**Production-code modification count: 0, as required.** No manual invocation of `autonomous_generate_project()` occurred. No task was manually marked successful. No retry was fabricated. No log was cleared or rewritten. No configuration was changed to force execution. The server was not restarted by this session at any point during this mission (it was already running, independently, when this mission began, and remained running, untouched, throughout). The only files created were this report and two disposable, read-only monitoring scripts + their JSONL output logs, all located outside the repository in the session's own scratch directory — none of which touch any tracked file.

---

## 20. Final Verdict

**VERIFIED LIVENESS FAILURE.**

The subsystem had a real, confirmed, uncontaminated opportunity to execute (a scheduled checkpoint fell squarely inside an 8.07-hour unbroken observation window) and demonstrably did not do so — the live scheduling record never advanced past its single startup-time evaluation. This satisfies the mission's own definition of this verdict category precisely.

This verdict is deliberately **not** upgraded to "VERIFIED AUTONOMOUS RECOVERY, NO RECOVERY" or downgraded to "HUMAN-INTERVENTION-CONFOUNDED," because:
- The historical record (11 real cycles over 26 days, all following prior failures) already establishes that the loop *can and does* resume after failure under ordinary conditions — this mission is not reporting a system that has never recovered, only that it is not currently doing so, right now, during a specific, real, cleanly-observed window.
- H2 (restart-confounding) is directly, specifically ruled out **for this window** by the unbroken-PID evidence — it would be dishonest to claim confounding when the process identity data says otherwise.
- H1 and H3 remain genuinely tied, and this report declines to break that tie without evidence, per its own governing discipline (Section 20 of the mission brief: "do not promote a liveness heartbeat into proof of investigation... do not promote 'the code contains retry logic' into 'Echo autonomously recovers'").

**Separately and independently confirmed, not contingent on resolving H1 vs. H3: the underlying autonomous-investigation capability has a 0/61 real-world success rate across its entire operational history.** Whatever the scheduling-liveness answer turns out to be, this is the more fundamental, already-fully-resolved finding of this mission.

---

## Answers to the Five Required Questions

**Q1 — Did `echo_projects_autonomy` actually execute autonomously after the Mission 21 failure?** No. One scheduling evaluation occurred (correctly gated, correctly skipped); zero actual investigation attempts occurred during this mission's observation window.

**Q2 — If yes, did it recover, or merely run an unrelated cycle?** Not applicable — no cycle occurred to evaluate.

**Q3 — If no, can we distinguish a genuine lifecycle defect from insufficient uninterrupted runtime?** Insufficient runtime is **ruled out** — 8.07 confirmed continuous hours, past the mission's own preferred window, with the next checkpoint structurally overdue. What remains undistinguished is a genuine code-level defect (H1) versus a benign OS-suspend clock effect (H3) — both are real possibilities the available evidence cannot separate.

**Q4 — Does current liveness instrumentation prove subsystem liveness, or merely process/heartbeat liveness?** Merely process/heartbeat liveness, for the sentinel signal specifically — confirmed directly this mission. The Liveness Ledger's dedicated `echo_projects_autonomy_activity` check and the live `get_autonomy_status()` record are both real, working, subsystem-specific signals (not mere heartbeats) — and both correctly, honestly reported the anomaly this entire mission investigated, rather than papering over it. The instrumentation is working as intended; what it revealed is the actual, unresolved finding.

**Q5 — What is the smallest next experiment that would conclusively distinguish the remaining hypotheses?** A single controlled, disclosed restart with full before/after state capture (Section 18) — the cheapest possible experiment that directly tests whether the specific current thread is stuck (recovery on restart) versus something more systemic.
