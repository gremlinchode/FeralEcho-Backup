# FeralEcho: Tier-3 Final Pre-Execution Gate

**The held-out experiment was NOT executed. The held-out task suite was NOT modified. No held-out task content was
inspected — every check below verifies existence/hash/integrity metadata only. No unrelated production change was
made.** Two real, previously-undisclosed apparatus findings were caught and fixed during this gate's own
verification work (a stale arm-name reference that broke a test, and a genuine 5th hidden call inside
`ARCH_COUNCIL`) — both are reported in full below, not smoothed over, consistent with this project's own standing
discipline.

## 1. Locked Experiment Definition

Re-read fresh from the current `scripts/run_tier3_apparatus.py` (post the ARCH_PIPELINE isolation fix) and
`audits/tier3_arch_pipeline_isolation.md`. **This table is the frozen contract** — nothing in it changes as a
result of this gate; two rows (marked ⚠) reflect real findings this gate's own re-verification surfaced and
required disclosing, not redefining.

| | `BASE_1` | `BASE_N` | `ARCH_PIPELINE_ISOLATED` | `ARCH_COUNCIL` |
|---|---|---|---|---|
| **Model calls (generative/comparable)** | 1 | 4 (3 attempts + 1 synthesis) | 1 | 4 (3 councillors + 1 synthesis) |
| **Real underlying `_ollama_query()` calls** | 1 | 4 | 1 | **5** ⚠ (includes 1 undisclosed-until-now warm-up call, see §Findings) |
| **`max_tokens` per call** | 2048 (`MAX_TOKENS`) | 2048 | 2048 | 2048 (warm-up call is the one exception — see §Findings, no `max_tokens` limit) |
| **Model identity rule** | pinned model (verified real, not cosmetic) | pinned model, reused across all 4 calls | pinned model (verified real, not cosmetic, per the isolation fix) | 3 real, diverse models selected live by production's own `_select_council()`/`rank_models()`, synthesized by `echo:latest` |
| **Temperature** | 0.0, fixed | `_jittered_temperature()` per attempt (recorded in `call_log`), 0.3 for synthesis | 0.0, fixed | governed entirely by production's own internal jitter logic — **not explicitly set or recorded by the harness** (intentional: this arm exists to test the real council exactly as it behaves in production, including its own natural temperature diversity) |
| **Prompt/context rule** | bare task prompt | bare task prompt (×3), then own attempts synthesized via a neutral, harness-only template | `CODE_OUTPUT_RULES` + live `self_edit_generated.py` contents + task (the one intentional difference from `BASE_1`) | production's real council system-prompt assembly |
| **Synthesis rule** | none | same-model, neutral, harness-only template (deliberately mirrors production's structure without claiming a "council" that doesn't exist) | none | real, heterogeneous — `echo:latest` synthesizing 3 real councillors' opinions |
| **Retry rule** | none | none (fixed-N attempt loop, not a retry-on-failure loop) | none | none reachable from this harness (production's own single-retry-on-sandbox-failure mechanism lives in `execute_self_edit()`, never called by any arm) |
| **Memory/RAG access** | none | none | none | none (confirmed: `echo_query()`'s own system-prompt assembly never calls `retrieve_relevant_memories()`; this arm doesn't route through `echo_query()` either) |
| **RiverBrain access** | none (pure `_ollama_query()` call, zero learning side effect) | none | none — verified 0 side-effect attempts, not merely 0 successful writes | real attempts (`.learn()` inside `deliberate_and_learn()`), correctly intercepted by `install_isolation()`'s read-through/write-blocked proxy |
| **Production write behavior** | none reachable | none reachable | none reachable | real attempts at `log_interaction`/`save_reflection`/RiverBrain `.learn()`/`.save()`, all intercepted — confirmed live via the `side_effects_detected` counter advancing by exactly 4 per real execution and by exactly 0 for the other three arms across the fresh dev-sanity run |
| **Objective scoring method** | shared, unmodified `verify_in_sandbox()` (real kernel-level sandbox) via `objective_verify()`, blind to arm/condition | same | same | same |

### Preserved boundaries (verbatim, unchanged by this gate)

> **`ARCH_PIPELINE_ISOLATED` tests the isolated self-edit generation mechanism/framing, not Echo's literal current
> production self-edit call path.**

> **This four-arm design cannot separate heterogeneous model diversity from Council-specific orchestration as
> competing explanations for a Council win.**

## 2. Held-Out Integrity Verification

Metadata only — no task content read, printed, or referenced anywhere in this gate's own work.

| Check | Result |
|---|---|
| File exists (`audits/tier3_apparatus/held_out_task_suite.json`) | ✅ Yes, 11,379 bytes |
| Live SHA-256 hash matches frozen constant | ✅ `2d78cbdb3657755f65779d010590ae348ded22d6d32d300bddacfd0aaa0e912a` — verified twice during this gate, at the start and end of the session, both times matching |
| `audits/tier3_apparatus/heldout_results.jsonl` (would only exist after real execution) | ✅ Does not exist — no execution has occurred |
| Any file referencing `held_0[1-8]` task IDs outside the suite/hash files themselves | ✅ None found (repo-wide grep) |
| Held-out manifest precedence over the development allowlist (re-derived from the isolation mission's own test, not re-run live here since it requires no new evidence) | ✅ Already proven: `assert_development_task_only()` correctly refuses a development task ID if it appears in a real held-out manifest |

## 3. Experiment Window — Baseline Telemetry

Captured directly, twice, at different points during this gate (not a single, cherry-picked snapshot):

| Signal | First capture (this gate) | Second capture (~15 min later) |
|---|---|---|
| `ollama ps` (resident models) | `qwen2.5-coder:7b` (5.0GB) + `echo:latest` (5.5GB), both 100% GPU, both with active/refreshing keep-alives | `echo:latest` (5.7GB) only, 100% GPU |
| Load average (1m/5m/15m) | 2.64 / 2.24 / 1.85 | 1.75 / 1.86 / 1.78 |
| Swap (`vm.swapusage`) | 4557MB / 5120MB total used | 5220MB / 6144MB total used |
| **Concurrent autonomous deliberation directly observed in the live watchdog log** | **Yes — `model_guided_autonomous_loop` and `EchoProjectsAutonomyWorker` both making real council queries at the same timestamps** (`01:50:42`/`01:51:16` overlapping a real `model_guided_autonomous_loop` deliberation cycle already in progress since `01:49:32`), plus a real self-edit sandbox-retry firing in the same window | Not re-checked at the second capture (no new watchdog tail pulled) |
| A real, unplanned, direct measurement of contention's actual effect | `python3 scripts/verify_arch_pipeline_isolation.py` (which makes 2 real live calls) **timed out at 120s** during this gate and had to be re-run in the background — direct, first-hand evidence that real experimental work is measurably slower right now, not just a telemetry number | A real, deliberately-run live `ARCH_COUNCIL` test call took **206.83 seconds** — slower than any of the 4 real `ARCH_COUNCIL` candidates observed in the fresh dev-sanity pass (129.81s–177.06s), consistent with, though not conclusively isolated to, current contention |

### `WINDOW_STATUS = NOT_CLEAR` (at the time of the first capture; borderline/improving by the second)

**Evidence, not assertion**: two real autonomous loops were directly observed running full multi-councillor
deliberations concurrently, at the same timestamps, during this gate's own work — the single clearest, most
severe contention signal this project's history has repeatedly documented as its dominant practical blocker.
The second capture, ~15 minutes later, shows improvement (1 resident model instead of 2, lower load average) but
was not re-checked against the watchdog log for renewed concurrent-loop activity, and a real live test call made
*during* this improved-looking window still took 206.83s — within the range of contended, not clearly
uncontended, historical timings.

**This gate does not declare the window clear based on a stale or improving-but-unconfirmed snapshot.** Per
§9's stop conditions and this report's own final verdict (§10), a **fresh, immediate telemetry check** — not
this report's own snapshots — is required at the moment the next mission actually begins.

## 4. Low Contention ≠ Zero Activity — Defined Threshold

The objective is a reproducible measurement window, not an inert system. Based on this project's own repeated,
direct experience (this gate's own timeout; the prior remaining-blockers investigation; the self-edit Level-4
experiment's own inability to complete a prospective test for the identical reason), the following is defined as
the **minimum acceptable condition for `WINDOW_STATUS = CLEAR`**, grounded in observed effect, not an arbitrary
aesthetic number:

1. **At most 1 model resident in `ollama ps`** at the moment of the check (2+ residents has been directly
   observed to correlate with concurrent multi-loop activity every time it was checked this session).
2. **No two autonomous loops observed issuing real council/deliberation calls within the same ~2-minute
   window** in the live watchdog log tail (this is the single clearest, directly-observed signal of the
   severe-contention state — not an inferred proxy).
3. **Load average (1-minute) at or below ~2.0** — this machine's own apparent idle/background baseline runs
   somewhat elevated already (other, non-Echo processes contribute), so a stricter near-zero threshold would be
   an aesthetic target unconnected to Echo's own real resource use, not a meaningful measurement of it.
4. **Swap usage not pinned near its own total** (a proxy for genuine memory pressure, distinct from load average).

**Genuine, low-level autonomous activity (e.g., the `guardian_loop` heartbeat, the crash-avoidance/liveness
collectors, occasional single-model dashboard polling) can and should coexist with the experiment without
materially affecting inference** — these do not contend for the Ollama generation queue, the actual scarce
resource this whole project's history has repeatedly identified as the real bottleneck. What cannot coexist,
per direct, repeated observation across this project's history, is **two or more concurrent real council/
deliberation cycles** — this is not a hypothetical risk, it was directly observed happening during this exact
gate's own work.

## 5. No Bundled Production Changes

| File/system | Status |
|---|---|
| `app/core/self_edit_manager.py` | Untouched — `git status`/`git diff --stat` both empty; file mtime (Jul 24) predates this entire investigation thread |
| `app/core/echo_model_orchestrator.py` | Untouched — mtime Sep 2, predates this thread's Tier-3 work |
| `app/core/river_deliberation.py` | Untouched — mtime Sep 2, predates this thread's Tier-3 work |
| Production memory systems | Untouched by this gate — the only memory-adjacent writes this harness can reach are all intercepted by `install_isolation()`, confirmed again this gate via the live council-capture test |
| Production learning systems (RiverBrain) | Untouched — same isolation, re-confirmed |
| Autonomous-loop implementations | Untouched — the concurrent activity observed in §3 is real, live, **unmodified** production autonomy behaving exactly as it always does; this gate did not pause, throttle, or alter it in any way, per explicit instruction |
| Everything this gate/mission *did* change | Confined entirely to `scripts/run_tier3_apparatus.py` (the harness) and two of its own verification scripts (`scripts/verify_tier3_truncation_repair.py`, `scripts/verify_tier3_apparatus_readiness_audit.py`) — both fixes were to the harness's own test suites, not to anything production-facing |

**Pre-existing, already-explained modifications visible in `git status` for `app/experiments/preference_provenance/`,
`app/core/behavioral_state.py`, `app/core/echo_ground_truth.py`, `app/core/self_edit_convergence.json`, and
`app/core/self_edit_generated.py`** are from earlier, separate, already-completed missions in this same working
session (the C1/behavioral-persistence and preference-provenance threads) and from the live, continuously-running
production self-edit loop's own real writes — none were touched by this gate or by any Tier-3-related work.

## 6. Apparatus Re-Verification (Non-Held-Out Only)

All three existing verification suites re-run fresh during this gate, plus two real, previously-undisclosed
findings caught and fixed in the process (see below).

| Suite | Result |
|---|---|
| `scripts/verify_tier3_truncation_repair.py` (23 checks, no live calls) | 23/23 PASS (after a real fix — see Findings below) |
| `scripts/verify_tier3_apparatus_readiness_audit.py` (31 checks) | 30 VERIFIED, 1 OPEN (`generate_code_from_plan()`'s own internal-retry disclosure — legitimately still open, unchanged), 0 FAIL (after a real fix — see Findings below) |
| `scripts/verify_arch_pipeline_isolation.py` (19 checks, 1 live call) | 19/19 VERIFIED, 0 OPEN, 0 FAIL (re-confirmed unchanged) |

**Confirmed directly**: `BASE_1`=1 call, `BASE_N`=4 calls, `ARCH_PIPELINE_ISOLATED`=1 call (verified real, not
cosmetic — the pinned model is confirmed to be the one that actually generates the text), `ARCH_COUNCIL`=4
generative calls (**plus 1 real, previously-undisclosed warm-up call — see Findings**); equal `max_tokens`
(2048) confirmed for every generative call in every arm; pinned-model consistency confirmed live for `BASE_1`/
`BASE_N`/`ARCH_PIPELINE_ISOLATED`; Council model diversity confirmed live (a real test call selected
`qwen2.5-coder:7b`, `mlx:qwen3`, `echo:latest` as councillors — genuinely diverse, not the pinned model
repeated); randomized arm order confirmed (§7); per-call truncation attribution confirmed (real ground truth
now available for all four arms); infrastructure-failure classification confirmed (`TimeoutError`/
`ConnectionError` correctly discriminated from ordinary logic exceptions); objective sandbox scoring confirmed
(real correct/incorrect trivial functions both scored correctly through the actual kernel sandbox);
isolation/no-production-writes confirmed (the `side_effects_detected` counter advances only for `ARCH_COUNCIL`,
by exactly 4 per real execution).

### Findings caught and fixed during this gate (reported in full, not silently patched)

1. **A stale arm-name reference broke `verify_tier3_truncation_repair.py`'s Test G.** The ARCH_PIPELINE
   isolation mission renamed the arm label from `ARCH_PIPELINE` to `ARCH_PIPELINE_ISOLATED`, but the
   truncation-repair suite's own randomized-order invariance test still hardcoded the old name in a lookup
   dict, special-casing it as a `PIPELINE_NO_GROUND_TRUTH` case. Since `ARCH_PIPELINE_ISOLATED` now has real
   ground truth like every other arm, the special case is not just stale but incorrect — fixed by removing the
   special case entirely and treating all four arms uniformly, matching the current, correct architecture.
   Re-run: 23/23 pass. The readiness audit's own downstream check of this suite (`truncation_classification_
   full_suite_rerun`) had reported a spurious `FAIL` purely as a symptom of this same stale reference — resolved
   by the same fix, not a separate one.
2. **`verify_tier3_apparatus_readiness_audit.py`'s held-out randomization check was stale**, still reporting
   `OPEN`/"no held-out set exists yet" from before the isolation mission authored and froze the real 8-task
   suite. Fixed to check the real, current suite's randomization directly (task_ids/numbering only, never
   content) — now `VERIFIED`, 8/8 real held-out tasks show non-degenerate, deterministic, non-inferable
   randomization.
3. **A real, previously-undisclosed 5th call inside `ARCH_COUNCIL`, caught live during this gate's own model-
   identity-capture verification.** `river_deliberation.deliberate_and_learn()` calls `_warm_up_echo(synth_model)`
   unconditionally before the real council loop — a genuine, minimal-input (`"."`) `_ollama_query()` call to the
   synthesis model, whose own response content is always discarded (never fed into synthesis, never scored).
   A live test call recorded `real_calls_made = ['echo:latest', 'qwen2.5-coder:7b', 'mlx:qwen3', 'echo:latest',
   'echo:latest']` — 5 real `_ollama_query()` invocations, not 4. This is real production code
   (`river_deliberation.py`, untouched by this gate, per the explicit instruction not to modify it) — not a bug
   in the harness's call path, but a real gap in what the harness's own `total_calls` field disclosed. **Fixed,
   harness-only**: `run_condition_arch_council()` now records `total_real_ollama_calls_including_warmup` (5),
   `warmup_model`, and correctly-sliced `councillor_models`/`synthesis_model` fields, alongside the existing
   `total_calls` (kept at 4, the generative/comparable count, for continuity with `BASE_N`'s own accounting).
   **This is disclosed, not eliminated**: the warm-up call's real wall-clock/compute cost is real, non-zero
   (already folded into `generation_time`, since it happens inside the same timed `deliberate_and_learn()`
   call), and has no equivalent in `BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED` — a genuine, if likely
   correctness-inert (its content is discarded), resource-cost asymmetry that any future report interpreting
   `ARCH_COUNCIL`'s results or timing must disclose, not silently absorb into an apparent "equal 4-call budget"
   claim.

## 7. Randomization Verification

Executed live, this gate, against the REAL 8-task held-out suite (task_ids/numbering only — zero content read):

- **Independently randomized per task**: 7 of 8 held-out tasks produce distinct arm orderings at the locked
  seed (`20260904`); the one repeated pair is statistically unremarkable for 8 draws from 4! = 24 possible
  orderings, not evidence of a degenerate randomizer.
- **Deterministic given (seed, task_id)**: confirmed — calling `randomized_arm_order()` twice for the same
  pair reproduces byte-identical output every time.
- **Seed recorded**: `seed = 20260904`, a literal constant in `main_heldout()`, written into every result
  record's own `seed` field (confirmed present in every dev-sanity record's schema, §Step 8).
- **Order cannot be inferred from task numbering**: the first arm in each task's order does not follow any
  monotonic or repeating pattern tied to `held_01`...`held_08`'s own sequence (`ARCH_COUNCIL, ARCH_PIPELINE_
  ISOLATED, ARCH_PIPELINE_ISOLATED, ARCH_PIPELINE_ISOLATED, BASE_1, BASE_N, BASE_N, ARCH_PIPELINE_ISOLATED`) —
  confirmed directly, not assumed.

## 8. Logging Completeness

Every field the mission's Step 8 requires was checked against the real schema written by `_run_single_candidate()`
and each `run_condition_*()` function (confirmed against real fresh dev-sanity records, not just source):

| Required field | Present as | Status |
|---|---|---|
| Task ID | `task_id` | ✅ |
| Condition/arm | `arm` | ✅ |
| Arm order | `arm_order` | ✅ |
| Model(s) | `model_used` (+ new: `real_calls_made`/`councillor_models`/`synthesis_model`/`warmup_model` for `ARCH_COUNCIL`) | ✅ (extended this gate — see Findings) |
| Call count | `total_calls` (+ new: `total_real_ollama_calls_including_warmup` for `ARCH_COUNCIL`) | ✅ (extended this gate) |
| `max_tokens` | `requested_max_tokens_per_call` | ✅ |
| Temperature(s) | `temperature` field added this gate for `BASE_1`/`ARCH_PIPELINE_ISOLATED` (both fixed at 0.0); `BASE_N`'s per-attempt temperatures already recorded in `call_log`; **`ARCH_COUNCIL`'s per-councillor jittered temperatures are governed entirely by production's own internal logic and are NOT captured by the harness** | ⚠ Disclosed gap for `ARCH_COUNCIL` only, not fixed — capturing them would require instrumenting inside `river_deliberation.py`, which this gate is explicitly not authorized to touch; this is an accepted, stated limitation, not a silent one |
| Generation timing | `generation_time` (+ per-attempt timings in `BASE_N`'s `call_log`) | ✅ |
| Truncation status | `truncation_evidence_type` | ✅ |
| Infrastructure status | `classification` (one of the 4 external classes includes `INFRASTRUCTURE_FAILURE`) | ✅ |
| Candidate extraction status | both `raw_response` (pre-extraction) and `candidate_code` (post `clean_code()`) stored, so extraction can be independently re-audited later | ✅ |
| Sandbox result | `ran_ok`, `output_tail`, `passed`, `verification_time` | ✅ |
| Failure classification | `classification` | ✅ |
| Trace/correlation ID | `call_id` (harness-local, from the Objective-1 truncation repair) — **no production `trace_id` is threaded through this experiment**, since it never routes through `routes_echo_studio.py`'s trace_id-generating call sites; `call_id` is the correct, available substitute for this fully-isolated harness | ✅ (with the stated N/A for production trace_id) |

**No held-out task text is logged anywhere by this harness** — every arm's stored `raw_response`/`candidate_code`
is the model's own *output*, never a copy of the input task text beyond what the model itself echoes back (which
`clean_code()`'s extraction already isolates to code). The frozen suite file itself is read only by
`load_and_verify_held_out_suite()` and passed directly as `task["prompt"]` into each arm's own generation call —
never separately written to any other log or report by the harness itself.

## 9. Stop Conditions (Hard, Defined Before Execution)

Any of the following, detected **during** the held-out run, must halt further candidate generation immediately.
**A hard stop preserves every already-written record in `heldout_results.jsonl` untouched, does not attempt to
retroactively "fix and continue" under altered conditions, and requires a fresh, explicit decision before any
further real generation resumes:**

1. **Unexpected model selection** — a `BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED` real call recorded with a
   `model_name` other than the locked pinned model; `ARCH_COUNCIL`'s councillor list showing zero real diversity
   (e.g., the same model 3×) on more than one candidate.
2. **Unexpected call count** — any candidate's real call count deviating from its arm's locked contract (1 / 4 /
   1 / 4 generative, or 5 total real calls for `ARCH_COUNCIL` including its known warm-up).
3. **Hidden retry** — any candidate showing more real calls than its arm's contract allows for a reason other
   than the already-disclosed `ARCH_COUNCIL` warm-up.
4. **Truncation classification ambiguity** — any candidate reporting `NO_GROUND_TRUTH_AVAILABLE` (per the
   isolation fix, every arm should now have real ground truth; this state occurring at all would itself be an
   anomaly requiring investigation, not an expected outcome).
5. **Infrastructure failure exceeding the pre-registered 15% threshold** of attempted trials — the design's own
   H5 override rule, enforced here exactly as written: report as inconclusive-pending-infrastructure regardless
   of substantive pass-rate numbers.
6. **Ollama contention beyond the §4 threshold** detected mid-run (2+ resident models, or concurrent
   multi-loop deliberation observed in the live watchdog log during the run) — halt, do not push through.
7. **Unexpected production side effect** — the `side_effects_detected` counter advancing for any arm other than
   `ARCH_COUNCIL`, or advancing by any amount other than exactly 4 per real `ARCH_COUNCIL` execution.
8. **Task-suite hash mismatch** — the live held-out file's hash no longer matching `2d78cbdb...` at the moment
   of load (checked automatically by `load_and_verify_held_out_suite()`, which hard-asserts and raises).
9. **Candidate contamination** — any candidate's `raw_response`/`candidate_code` referencing another held-out
   task's content, a production file path that shouldn't appear, or any text suggesting the model was exposed to
   information outside its own single task prompt.
10. **Sandbox malfunction** — `objective_verify()` raising an exception instead of returning its normal result
    dict, or a `ran_ok=False` result with no coherent `output_tail` explaining why.

## 10. Final Verdict

# CLEARED WITH EXPLICIT CONDITIONS

The apparatus itself — every property Steps 1, 2, 5, 6, 7, and 8 were asked to verify — is confirmed correct,
current, and fully prepared, including two real, previously-undisclosed gaps this gate's own verification work
caught and fixed (a stale test reference; `ARCH_COUNCIL`'s undisclosed 5th warm-up call) rather than carried
forward silently. The only reason this is not an unconditional `CLEARED FOR HELD-OUT EXECUTION` is Step 3/4's
own honest finding: **real contention was directly observed during this exact gate's own work**, and this
report's own telemetry snapshots are, by the time the next mission actually begins, no longer current.

**Explicit conditions for the next mission:**

1. **Capture fresh telemetry immediately before generating a single held-out candidate** — do not rely on this
   report's own snapshots. Apply the §4 threshold (≤1 resident model, no concurrent multi-loop deliberation in
   the live watchdog log's most recent ~2 minutes, load average ≲2.0, swap not pinned near its total). If not
   met, wait and re-check; do not proceed on a stale or hoped-for assessment.
2. Run the required development-sanity confirmation (`python3 scripts/run_tier3_apparatus.py`, no `--heldout`
   flag) one more time immediately before the held-out run if any further code change occurs between this gate
   and execution — none is anticipated, but this condition exists precisely because this gate itself found two
   real regressions introduced by an earlier, already-verified change.
3. Enforce every §9 stop condition live, not retrospectively — halt immediately on the first trigger, preserve
   all data collected so far, and do not resume without a fresh decision.
4. Any report of results must state both preserved boundaries (§1) and the `ARCH_COUNCIL` warm-up disclosure
   (§6, Finding 3) verbatim, not summarized away.
5. No production change, autonomy repair, or fine-tuning should be bundled into or precede the held-out run.

### Exact command/protocol for the NEXT mission (not executed here)

```bash
# 1. Immediately before running, capture and evaluate fresh telemetry:
ollama ps
uptime
sysctl vm.swapusage
tail -100 memory/echo_watchdog.log | grep -E "DELIBERATION|Querying councillor|Synthesis complete"
# Evaluate against §4's threshold. If NOT_CLEAR, stop and wait.

# 2. Re-confirm held-out integrity one final time:
python3 -c "
import hashlib
with open('audits/tier3_apparatus/held_out_task_suite.json','rb') as f:
    h = hashlib.sha256(f.read()).hexdigest()
assert h == '2d78cbdb3657755f65779d010590ae348ded22d6d32d300bddacfd0aaa0e912a'
print('held-out suite integrity CONFIRMED')
"

# 3. Execute the real, genuinely held-out run:
python3 scripts/run_tier3_apparatus.py --heldout

# 4. Monitor for every §9 stop condition throughout. On any trigger, halt
#    (Ctrl-C or let the process exit naturally at its next candidate
#    boundary) and do not resume without a fresh decision.

# 5. On clean completion, score/spot-check/unblind per the protocol already
#    laid out in audits/current_capability_synthesis.md §11, reporting both
#    boundary statements (§1 of this document) verbatim alongside any result.
```

**This gate does not execute this protocol. The next mission is the actual held-out experiment and nothing else.**
