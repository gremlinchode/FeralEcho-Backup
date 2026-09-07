# Real Trace → F2 Provenance Liveness

## Final Verdict: **P2 — PARTIAL PLUMBING**

A real, natural, unforced self-edit attempt ran the full production pipeline end to end. The `trace_id` mechanism is genuinely live and durably persisted — but into `interaction_log.jsonl` and `council_deliberations.jsonl`, not into `self_edit_outcomes.jsonl`, because `record_pending_outcome()` (the function that writes that specific record) is gated on a full production deploy succeeding, and this real attempt was correctly rejected one gate short of that by the independent fitness gate. The trace_id ↔ F2-sandbox-outcome pair the mission asked to establish does not yet exist anywhere durable, but the reason is now a precisely characterized architectural gate, not an unknown.

## Safety Invariants

| Check | Before | After | Status |
|---|---|---|---|
| `run.py`/watchdog process | not running | not running | unchanged |
| Port 5000 | unbound | unbound | unchanged |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | **byte-identical** |
| `app/core/self_edit_generated.py` | untracked-clean | untracked-clean (`git status` shows no diff) | unchanged — candidate never reached the write step |
| `app/core/self_edit_backups/` | last file `self_edit_20260903040641.py` | same, no new file | unchanged — `backup_existing_code()` was never called |
| Commits | 0 | 0 | none made |

No production source file was modified. No commit was made. One new experiment directory was created: `app/experiments/real_trace_f2_provenance/`.

**Real, expected production-state side effects of this genuine attempt** (proving it was a real interaction, not a simulation, and confirming nothing beyond the mission's own anticipated scope changed):
- `memory/self_edit_cooldown.json`: `last_any_autonomous_edit` advanced from `1788729168.45` (24,000s stale) to `1788753272.21` — the real global 60-minute storm-prevention cooldown, correctly stamped by `perform_self_edit()`.
- `memory/reflection_shard.jsonl`: gained one real new entry (`timestamp: 2026-09-07T03:54:32.221810`, `result: rejected_not_improvement`).
- `memory/SELF_EDIT.log`: gained one real new journal line (`result: rejected_not_improvement | candidate_quality=3 current_quality=4`).
- `memory/interaction_log.jsonl`: gained 3 real entries (the plan, codegen, and retry `echo_query()` calls).
- `memory/council_deliberations.jsonl`: gained 1 real entry (`source: "real_deliberation"`).
- `memory/self_edit_outcomes.jsonl`: **unchanged**, still 179 lines — this is the one file the mission is specifically about, and it correctly received nothing, because the attempt didn't clear the fitness gate.

## Phase 1 — Existing Plumbing, Traced from Source

```
perform_self_edit(prompt=None)                       self_edit_manager.py:2760
  ├─ is_in_stillness() check                          (False at run time — proceeded)
  ├─ target_task_type resolution                      SelfModelUpdater().get_weak_task_type()
  ├─ 60-min global cooldown check + stamp              _self_edit_deploy_lock, self_edit_cooldown.json
  └─ execute_self_edit(prompt, dry_run=False)          self_edit_manager.py:1854
        │
        ├─ trace_id = str(uuid.uuid4())                self_edit_manager.py:1887  ← ORIGIN, one per attempt
        ├─ reflection_entry = {...}                    self_edit_manager.py:1904  ← NO trace_id field (confirmed by source read)
        ├─ plan = plan_code_logic(..., trace_id=trace_id)      → echo_query(..., trace_id=trace_id)
        ├─ code, model = generate_code_from_plan(..., trace_id=trace_id)
        │       └─ river.learn(model, "self_edit_coding", code)      [neutralized in this run]
        ├─ success, sandbox_error = test_code_in_sandbox(code)       ← REAL F2 EVALUATOR
        │       └─ river.learn_from_sandbox_outcome(...)             [neutralized in this run]
        ├─ [on failure] retry_code = echo_query(retry_prompt, trace_id=trace_id)
        │       retry_success, retry_error = test_code_in_sandbox(retry_code, ...)
        ├─ _stage_and_import_test(code, ...)            (F3-equivalent staging check)
        ├─ [if dry_run] → return early, NEVER reaches record_pending_outcome()
        ├─ FITNESS GATE (self_edit_manager.py:2110-2152, under _self_edit_deploy_lock):
        │       candidate_quality = _score_response_quality(code, "coding")
        │       current_quality  = _score_response_quality(current production code, "coding")
        │       if candidate_quality < current_quality:
        │           reflection_entry["result"] = "rejected_not_improvement"
        │           save_reflection(reflection_entry)     ← durable, but no trace_id in this dict
        │           return False, "Rejected: ..."          ← STOPS HERE, backup/save/load never run
        │       [else, continue below]
        ├─ backup_existing_code() + save_code(code)      ← writes app/core/self_edit_generated.py for real
        ├─ load_self_edit_module()
        └─ record_pending_outcome(task_type, trace_id=trace_id)   self_edit_manager.py:2196
                └─ writes ONE new row to memory/self_edit_outcomes.jsonl, trace_id included
                   (self_edit_outcome_tracker.py:72-95)
```

**Answering Phase 1's specific questions:**
1. `trace_id` originates once per `execute_self_edit()` call, `self_edit_manager.py:1887`, via `uuid.uuid4()`.
2. The candidate is executed in the real kernel-sandboxed subprocess via `test_code_in_sandbox()` (F2), which shells out through `sandbox-exec` + `safe_exec_wrapper.py`.
3. The trusted F2 pass/fail result is produced by `test_code_in_sandbox()`'s own return value — independent of anything the LLM claims.
4. It is currently persisted, if the attempt reaches full deploy, only via `record_pending_outcome()` → `memory/self_edit_outcomes.jsonl`. **Nowhere else stores the F2 verdict durably keyed by trace_id** — `SELF_EDIT.log`'s journal line and `reflection_shard.jsonl`'s `reflection_entry` both record `sandbox_feedback`/`result` but neither dict includes `trace_id` (confirmed directly: `reflection_entry`'s literal keys at `self_edit_manager.py:1904-1911` are `prompt, task_type, generated_code, timestamp, sandbox_feedback, result` — no `trace_id`).
5. The same `trace_id` **does** survive across stages — confirmed live in this run (see Phase 3).
6. The current production path (`perform_self_edit()` → `execute_self_edit()`) **does** call `record_pending_outcome()`, but only on the terminal success branch after backup+save+load all succeed (`self_edit_manager.py:2196`, inside the `try` block that starts at "Step 4: Backup + Step 5: Save to production").
7. Exact fields written by `record_pending_outcome()`: `edit_id, task_type, edit_timestamp, status, trace_id` (`self_edit_outcome_tracker.py:72-95`, matches source exactly, `trace_id` is optional/`None`-default, added 2026-09-05, Plan 5).

## Phase 2 — One Real Controlled Self-Edit

**Judgment applied before running anything** (per this mission's own explicit instruction to reason first): `record_pending_outcome()` is reachable *only* via the real `dry_run=False` production-deploy-success path — confirmed by direct source read (Phase 1 above), not assumed. Dry-run trials structurally cannot exercise it; Architecture A's prior retries never reached it either. A real deploy attempt was therefore the only way to test the actual durable-persistence mechanism, so Phase 2 proceeded.

**RiverBrain neutralization, applied and independently verified before Phase 2 began:**
1. `echo_model_orchestrator.RIVER_BRAIN_PATH` (module-level global, referenced bare inside `_do_save()`/load) was redirected to a scratch copy of the real file **before** `get_river_brain()` was ever called anywhere in the process — closing the exact gap Finding 89/Tier-8 documented (RiverBrain's own `_writer_thread` starts unconditionally in `__init__()` and persists every ~60s regardless of whether `.save()` is called through any proxy; a method-only patch applied after instantiation would not have caught it).
2. `RiverBrain.learn`, `.learn_from_sandbox_outcome`, `.learn_from_council_rating`, `.save`, `._do_save` were all patched to no-ops at the **class** level, before the singleton was ever instantiated.
3. **Verified, not assumed**: a direct probe (`get_river_brain(); river.learn(...); river.learn_from_sandbox_outcome(...); river.save()`) confirmed all three patched methods fired as no-ops (counters moved to exactly 1 each) and the real `memory/river_brain.pkl` hash was unchanged immediately afterward — this check ran and passed *before* Phase 2's real self-edit attempt began, with a hard abort built into the script if it had failed.
4. **Verified again after the real attempt**: 14 real `learn()` calls, 2 `learn_from_sandbox_outcome()` calls, 3 `save()`/3 `_do_save()` calls occurred during the real self-edit attempt (all correctly routed to the neutralized no-ops), and the real `memory/river_brain.pkl` hash remained byte-identical throughout.

**The attempt itself**: `perform_self_edit(prompt=None)` — no prompt, no target task type, no temperature was chosen by this script; every part of what was attempted was selected by the real, unmodified production logic (`SelfModelUpdater().get_weak_task_type()` → `_build_targeted_prompt()`). Ran for 210.15 real seconds, making real Ollama calls throughout (Ollama was reachable directly, `run.py` never started).

**Real, unforced result** (`success=False`):
```
"Rejected: candidate quality (3) does not improve on current production (4)"
```
The generated candidate — a `log_call` decorator, a `HealthMonitor` class, and refactored `generate_and_modify_code`/`run_code_generator` functions targeting `app/core/self_edit_generated.py`'s `response_shortening` family — genuinely failed F2 on its first pass (`TypeError: HealthMonitor.__init__() missing 1 required positional argument: 'average_response_length'`), was retried with real error feedback, **passed** F2 on retry (`temp_self_edit_retry.py: import test passed`), then cleared staging, then was rejected by the independent fitness gate one step later. No retry of the *whole attempt* was performed — the pipeline's own internal one-retry mechanism (a designed, existing feature) is not the same as this mission's own "do not retry repeatedly" instruction, which refers to re-running `perform_self_edit()` itself; that was called exactly once.

This is a completely ordinary, expected result — Finding 48 already established a 0% real-deploy success rate across 71 prior real attempts (mostly F1/staging rejections, "working as intended, not a crisis"). This run adds one more real, natural data point to that same pattern, not an anomaly.

## Phase 3 — Independent Verification of the Record

**The real `trace_id` for this attempt**: `e05cb935-e74e-4ce1-8313-e8d090f0cafa`.

**A real methodological limitation in this script's own instrumentation, disclosed rather than hidden**: to observe the trace_id without altering `self_edit_manager.py`'s behavior, this script wrapped the shared stdlib `uuid.uuid4` globally (pass-through, zero behavior change) rather than scoping the wrap to `self_edit_manager`'s own module namespace. This captured **37 UUIDs** during the 210s run — one real `trace_id`, plus 36 unrelated `uuid4()` calls from elsewhere in the process (model/embedding loading, other subsystem bookkeeping). The observation list alone could not reliably identify which UUID was the real trace_id.

**Recovered independently instead**, via a more trustworthy path — direct inspection of real, already-durable production logs for entries matching this run's real time window (`03:54–03:58 UTC, 2026-09-07`), `task_type="coding"`, `source="autonomous"`:
- `memory/interaction_log.jsonl`: 3 real entries, all carrying `trace_id: "e05cb935-e74e-4ce1-8313-e8d090f0cafa"`, at `03:55:31.774540`, `03:56:51.553379`, `03:57:57.171908` — matching the console's real wall-clock log lines (`[SANDBOX] temp_self_edit.py: import failed` and `temp_self_edit_retry.py: import test passed`) and the 210s total elapsed time.
- `memory/council_deliberations.jsonl`: 1 real entry, same `trace_id`, `source: "real_deliberation"`, timestamp `03:55:31.772561` — confirming the trace_id survives into this second durable log too, independent of the outcome-tracker mechanism.
- **Confirmed the trace_id is genuinely present in both files by direct grep**, not inferred from the console log alone.

**Proving each required link (Phase 3's checklist):**
- The trace_id is real and originated from this run: **yes** — it appears nowhere in either file before this run's timestamps (both files' prior tails, checked in the immediately preceding mission this session, show no such UUID), and its first appearance is in the correct time window, task type, and source tag.
- The F2 verdict came from the trusted evaluator: **yes** — `test_code_in_sandbox()` genuinely ran, genuinely failed once (real `TypeError`), genuinely passed on retry, confirmed via the real subprocess log lines (`[SANDBOX] temp_self_edit.py: import failed`, `[SANDBOX] temp_self_edit_retry.py: import test passed`), not asserted by the model.
- The persisted outcome contains the same trace_id: **only in `interaction_log.jsonl`/`council_deliberations.jsonl`, not in `self_edit_outcomes.jsonl`** — `record_pending_outcome()` was never called (0 new lines in that file, confirmed directly before and after: 179 lines both times).
- The stored pass/fail agrees with the actual F2 result: **not applicable in the outcome-tracker sense** — no durable `self_edit_outcomes.jsonl` row exists to check agreement against. In the two files that *do* carry the trace_id, neither stores a structured pass/fail field at all — they carry the raw `echo_query()`/deliberation text, not an F2 verdict.
- No manual post-hoc editing created the pair: **confirmed** — every artifact cited above was produced by the real pipeline's own write calls during the live 210s run, not edited afterward by this script.
- The record is recoverable by a fresh read/search: **confirmed** — all greps above were run as independent, separate commands against the real files on disk after the process exited.

**Net: the trace_id → F2-evaluator chain is real and durably recoverable through `interaction_log.jsonl`/`council_deliberations.jsonl`. The trace_id → durable-outcome-record chain (`self_edit_outcomes.jsonl`, the file this whole provenance investigation is actually about) is real in its write logic but was not exercised, because this specific, natural, unforced attempt did not clear the fitness gate.**

## Phase 4 — Negative/Failure Path

**Not UNTESTED** — a genuine F2 failure occurred naturally as part of this single real attempt, without any candidate selection or forcing on this script's part: the first-pass candidate genuinely failed `test_code_in_sandbox()` with a real `TypeError`. This exercised:
- `river.learn_from_sandbox_outcome(model_name, success=False, error=...)` — real call, neutralized (counted in the 2 `learn_from_sandbox_outcome` calls logged).
- The real retry path — `retry_prompt` built from `_sanitize_sandbox_error()`'s real, correct diagnosis of the missing argument, fed into a fresh `echo_query()` call (this too carried the same `trace_id`, confirmed via the `interaction_log.jsonl` entries above).

**What durably survives from this real F2 *failure* specifically**: nothing beyond what already survives from the whole attempt overall (the `interaction_log.jsonl`/`council_deliberations.jsonl` trace_id-linked entries). No separate, distinct "F2 attempt #1 failed with error X, trace_id Y" record exists anywhere on disk — the failure and its diagnosis live only in the retry prompt's in-memory text, discarded once the retry either succeeds or the attempt ends. This is a live, independent re-confirmation of the Hot Stove / Credit Assignment audit's original finding (`clean_error`/`retry_prompt` are local variables, never persisted) — observed here on a fresh, real, unforced attempt rather than inferred from source alone.

## Critical Epistemic Rule — Event Verification vs. Diagnosis Truth

This run's real data keeps these cleanly separate, by construction of what actually exists on disk:
- `trace_id` (`e05cb935-e74e-4ce1-8313-e8d090f0cafa`): **event identity** — confirmed real, confirmed to have originated from this specific attempt.
- `f2_outcome`: the real, trusted result was fail-then-pass (`test_code_in_sandbox()`'s own return value) — genuinely computed, independent of narrative.
- `diagnosis_supported`: **not applicable / not established** — nothing in this run's durable artifacts stores a causal diagnosis linked to the trace_id at all (per Phase 1's finding: `reflection_entry` has no `trace_id` field, and `SELF_EDIT.log`'s journal line has none either). There is no record anywhere claiming "trace_id X's failure was caused by Y" that could be mistaken for verified — the gap is total silence, not false confidence. This is a cleaner (if less useful) state than the "confidently wrong narrative" failure mode the two preceding missions found in the relevance-gate experiments — here there's no causal claim at all to over-trust.

## What This Establishes and What It Doesn't

**Establishes**: the `trace_id` correlation-ID mechanism (Plan 5) is genuinely live in production, not just committed-but-dormant — a real attempt, run right now, threaded one real trace_id through 4 real model calls and 2 separate durable logs. The F1/F2/F3 safety pipeline and the independent fitness gate both function exactly as documented, on a completely natural, unforced attempt.

**Does not establish**: a durable `trace_id ↔ F2 outcome` pair inside `self_edit_outcomes.jsonl` specifically — the file this whole line of investigation (Provenance + F2 Verification Feasibility → this mission) was built around remains at 0 real trace_id-carrying rows, not because the write logic is broken, but because reaching it requires clearing a real, independently-functioning quality bar that most real attempts (71/71 historically, and now 72/72 including this one) do not clear.

## Files Changed

Production: none. New: `app/experiments/real_trace_f2_provenance/run_real_self_edit.py`, `app/experiments/real_trace_f2_provenance/phase2_run_report.json`, `app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl` (scratch decoy, not real state), this report. Real, expected production *state* changes (not source changes) are itemized in Safety Invariants above.

## Git HEAD / RiverBrain Verification (repeated, for the record)

- HEAD before: `2cf2d95009943797db5ec41fea9b4021634fd5e6`
- HEAD after: `2cf2d95009943797db5ec41fea9b4021634fd5e6`
- `river_brain.pkl` sha256 before: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`
- `river_brain.pkl` sha256 after: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`
