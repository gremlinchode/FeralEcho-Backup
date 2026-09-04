# FeralEcho: Tier-3 Truncation-Attribution Repair — Verification Report

**No held-out task was touched, referenced, or executed** (re-confirmed this session: `audits/tier3_apparatus/held_out_task_suite.json`
does not exist anywhere in the repository; `find . -iname "*held_out*"` returns nothing). **No production file was modified** — the
entire repair lives inside `scripts/run_tier3_apparatus.py`, a harness-only script that has never been committed to git (it is, and
remains, untracked working state). **The frozen development task suite hash is unchanged**
(`6440ed174482a2d5bb43bdd03bfc33c73c66b492cb74f465e2674e8a8eb8937d`, re-verified live). **The existing background sanity process
(PID 52989) was left running, untouched, throughout this repair** — it has continued producing real candidates on its own
already-loaded (pre-repair) copy of the code the entire time; see §8 and §9 for exactly what that means for this report's scope.

## 1. Original Defect

`classify_result()`, as implemented before this repair, determined whether a candidate's generation had been truncated by reading a
single, shared, module-level list (`_truncation_events`) populated by every arm's calls, filtered only by wall-clock recency
(`time.time() - e["ts"] < 300`), and then reading `recent[-1]` — "whichever event was most recently appended, from any arm, from any
task." There was no per-call identifier anywhere in the mechanism. This was first found and synthetically proven in the prior
`tier3_remaining_blockers_investigation` mission (see that document's Part D): a direct test showed a Pipeline-shaped, ordinary-failure
response wrongly classified `GENERATION_TRUNCATED` purely because a *different* arm's real truncation event, from 5 seconds earlier,
was still sitting in the shared window.

## 2. Root Cause

Three of the four arms (`BASE_1`, `BASE_N`, `ARCH_COUNCIL`) call through `app.ollama_handler.stream_query_ollama()`, the one function
`install_truncation_capture()`'s monkeypatch wraps — so each of those arms *does* append at least one real event to the shared list
during its own turn. Because the harness runs arms sequentially within one task and classifies each immediately after it completes,
"most recently appended" and "belongs to the arm currently being classified" happened to coincide for those three arms — a property of
execution order, not of anything the code actually checked. `ARCH_PIPELINE`'s real call path
(`generate_code_from_plan() → echo_query() → echo_model_orchestrator.ollama_query()`) is a separate, independent implementation that
bypasses `app.ollama_handler.py` — and therefore the capture point — entirely (confirmed by direct source read in the prior mission,
re-confirmed unchanged this session). It never appends anything of its own, so whenever it was classified, "most recent event" was
*always* some other arm's leftover. The bug was latent, not theoretical: it was masked only by the one real `ARCH_PIPELINE` candidate
collected so far having happened to run first in its randomized arm order, before any event existed to contaminate it.

## 3. Minimal Repair

Implemented entirely inside `scripts/run_tier3_apparatus.py` (lines ~34–90 for the state/capture machinery, plus one small,
call-site-local change in each of the four `run_condition_*()` functions and in `main()`'s classification call):

- **`_truncation_events` (the shared, unscoped list) was removed entirely** — not deprecated in place, not left importable-but-unread.
  Nothing in the file references it any more.
- **New state**: `_current_call_id = [None]` (a single-slot mutable cell — "which call, if any, is actively being captured right now"),
  `_call_id_counter = [0]` / `_new_call_id()` (a monotonically-increasing, process-local, never-reused integer identifier),
  `_truncation_events_by_call = {}` (a dict keyed by call ID — never a list scanned by time), and an explicit named sentinel,
  `PIPELINE_NO_GROUND_TRUTH`, that is **never registered as a real key** in that dict.
- **`install_truncation_capture()`'s wrapper** now tags every captured event with whatever `_current_call_id[0]` is at capture time.
  If no call ID is active (`None`), the event is **dropped**, not filed under a guessed or default key — silence is the honest outcome
  when no caller has explicitly scoped a capture window; misfiling would not be.
- **Every real generation call in `BASE_1`, both call sites in `BASE_N` (the N attempts *and* the synthesis leg), and the single
  external call in `ARCH_COUNCIL`** now: (a) obtains a fresh call ID via `_new_call_id()`, (b) sets `_current_call_id[0]` to it
  immediately before the call, (c) clears it back to `None` in a `finally` block immediately after, and (d) returns that ID in its
  result dict as `"call_id"`.
- **`ARCH_PIPELINE`'s result dict explicitly sets `"call_id": PIPELINE_NO_GROUND_TRUTH`** — never `None` by omission, never a real
  integer, and never anything derived from another arm's state. This is a structural, load-bearing fact, not a convention: that arm's
  call path cannot reach the capture point at all, so there is no real integer ID that would ever mean anything for it.
- **`classify_result()` gained an explicit, required `call_id` parameter.** It performs an **exact dictionary lookup**
  (`_truncation_events_by_call.get(call_id)`) — never a scan, never a time filter, never "the last one added anywhere." A `call_id` of
  `None` or `PIPELINE_NO_GROUND_TRUTH` causes the ground-truth branch to be skipped entirely, unconditionally, before any dictionary
  read is even attempted.
- **`main()`'s single call site** now threads `gen.get("call_id")` into `classify_result()`, and stores the function's second return
  value as `record["truncation_evidence_type"]` — a new, permanent field in every future result record (see §7's internal-taxonomy
  discussion; not yet present in the 7 real records already collected by the still-running old process, see §8).

No part of this repair required touching `app/ollama_handler.py`, `app/core/river_deliberation.py`,
`app/core/self_edit_manager.py`, or `app/core/echo_model_orchestrator.py`. §8 states explicitly why a harness-level repair was
sufficient and no STOP-and-report was needed.

## 4. Synthetic Tests

All required tests were built and run in `scripts/verify_tier3_truncation_repair.py`, a new, harness-only verification script (no
Ollama call anywhere in it — every "call" is a synthetic event inserted directly into `_truncation_events_by_call`, or, for the
capture-mechanism tests, a fake stand-in generator). **23/23 checks pass.** Full transcript reproduced in the companion JSON's
`synthetic_test_results.raw_stdout` field; summary below.

| Test | Scenario | Result |
|---|---|---|
| Capture mechanism (3 checks) | Event dropped with no active call ID; event filed under the exact active ID; two distinct IDs never merge | **PASS** |
| **A** | call1 `done_reason=length`, call2 normal | call2 correctly **not** truncated |
| **B** | call1 normal, call2 `done_reason=length` | only call2 correctly truncated |
| **C** | Pipeline (no ground truth) + Council (`length`) | Pipeline does **not** inherit Council's event; Council's own event still correctly read |
| **D** | Council `length` registered first, Pipeline classified after | Pipeline stays `TASK_LOGIC_FAILURE`, not fabricated |
| **E** | Same registered state, classify() call order reversed (Pipeline-then-Council vs. Council-then-Pipeline) | identical results either way |
| **F** | 4 call IDs' events interleaved in registration order (including a call ID with 2 events, simulating a retry-shaped case) | each ID's classification reflects only its own last-registered event |
| **G** | 30 real `(seed, task_id)` combinations via the actual production `randomized_arm_order()`, each with a fixed synthetic ground truth per arm, classified in the randomized order itself | classification outcome identical across all 30 combinations |

## 5. Cross-Call Contamination Tests

Tests C, D, and F above are the direct cross-contamination proofs: C and D specifically construct the one scenario the original bug
was found through (a Pipeline-shaped call adjacent to a real Council truncation event) in both possible orderings, and F generalizes
this to four simultaneously-live call IDs with interleaved, out-of-order registration. A dedicated additional check,
`test_invariant_stale_event_cannot_satisfy_another_call`, registers an event with a timestamp of `1.0` (1970-era, maximally "stale" by
the *old* 300-second-window logic) under one call ID, then confirms a **different** call ID with no event of its own is never
satisfied by it — proving recency was removed as part of the identity mechanism, not merely narrowed to a smaller window.

## 6. Random-Order Invariance

Test G reuses the real, unmodified `randomized_arm_order(task_id, seed)` (the exact production randomization function, not a
reimplementation) across 15 seeds × 2 development task IDs = 30 combinations. For each, a fresh call ID (or the Pipeline sentinel) is
assigned to each arm in the randomized order itself, a fixed synthetic ground-truth outcome is registered per arm role, and
`classify_result()` is invoked for each arm in that same randomized order. All 30 combinations produced the identical expected
classification set: `BASE_1→TASK_LOGIC_FAILURE`, `BASE_N→GENERATION_TRUNCATED`, `ARCH_PIPELINE→TASK_LOGIC_FAILURE`,
`ARCH_COUNCIL→TASK_LOGIC_FAILURE`. Test E additionally shows that reversing only the *classification* call order (not the underlying
registration) leaves results byte-identical. Together these directly satisfy the required invariant: "randomized execution order
cannot change classification."

## 7. Pipeline No-Ground-Truth Handling

`ARCH_PIPELINE` never receives a real integer call ID; its result dict always carries the explicit sentinel
`PIPELINE_NO_GROUND_TRUTH`. `classify_result()` treats this sentinel identically to `call_id=None`: the ground-truth branch is skipped
unconditionally, with **no dictionary read attempted at all** (not "attempted and found empty" — structurally bypassed), before
falling through to the uniform, arm-agnostic fence-parity text backstop. The internal audit trail preserves this precisely: the
function returns a `(classification, evidence_type)` tuple, where `evidence_type` is one of `GROUND_TRUTH_TRUNCATED` (this exact call's
own `done_reason == "length"`), `TEXT_BACKSTOP_TRUNCATED` (no usable ground truth for this call, but an unclosed fence caught it),
`NO_GROUND_TRUTH_AVAILABLE` (this call structurally cannot or did not produce ground truth), or `None` (either `PASS`, or ground truth
was genuinely checked and confirmed no truncation). The **external** four-class contract (`PASS` / `TASK_LOGIC_FAILURE` /
`INFRASTRUCTURE_FAILURE` / `GENERATION_TRUNCATED`) is unchanged — `evidence_type` is stored alongside it in every record
(`record["truncation_evidence_type"]`) and never collapses into or overrides it.

## 8. Production-Safety Assessment

**A harness-level repair was sufficient; no production code change was needed or proposed.** The entire defect lived in this
script's own bookkeeping (`_truncation_events`/`classify_result()`), not in any production function's behavior — `stream_query_ollama()`
and `generate_code_from_plan()` themselves were never at fault; the harness was simply attributing their real, correct outputs to the
wrong caller. Every change in §3 is scoped to `scripts/run_tier3_apparatus.py` alone. Per the mission's own instruction, if the *only*
viable repair had required a production change, the correct action was to stop and report rather than implement — that situation did
not arise here.

**One explicit, load-bearing limitation stated plainly, not glossed over**: `ARCH_COUNCIL`'s single external call
(`deliberate_and_learn()`) wraps four real internal `stream_query_ollama()` calls (3 councillors + 1 synthesis) that this harness has
no hook granular enough to assign four independently-distinct call IDs to, without instrumenting inside `river_deliberation.py` itself
— a production file this repair does not touch, consistent with the mission's stated preference. All four of that arm's real events
are therefore filed under **one** shared call ID. Classification correctness for this arm depends on a verified, but external,
ordering fact: `deliberate_and_learn()`'s own internal sequence runs the councillor loop to completion *before* making the synthesis
call (confirmed by direct source read, both in the prior mission and re-confirmed this session) — so the **last** entry filed under
that one call ID is always the synthesis leg, which is the only leg whose output is ever actually scored. This is a real, disclosed
dependency on a source-code fact about `deliberate_and_learn()`'s internal call order, not an assumption papered over as "solved" — if
that internal ordering were ever changed in production, this specific arm's classification could regress. It is fundamentally
different from the original bug in one critical respect: it can **never** read a *different arm's* or a *different task's* event
(each `ARCH_COUNCIL` invocation gets its own fresh call ID, never shared across candidates), so the worst-case failure mode this
dependency exposes is confined entirely within one candidate's own four internal legs — never cross-arm, never cross-task
contamination.

The already-running background sanity process (PID 52989) was **not restarted or otherwise touched at any point during this
repair**. **Update, observed during this mission (not caused by it): the process has since completed and exited on its own** — a
natural, unforced termination (its `main()` loop runs exactly `2 development tasks × 4 arms = 8` iterations, then returns; it was never
a `while True:` daemon). `audits/tier3_apparatus/dev_sanity_results.jsonl` now holds all **8** planned development-sanity records (up
from 3 at the start of this mission, and 7 mid-repair), all produced entirely under the *old, pre-repair* code, since the process ran
from its own already-loaded copy in memory from before this repair began. None of the repairs in §3 retroactively apply to any of these
8 records. This is expected and correct, not an oversight: the mission explicitly forbids restarting the process "merely for
cleanliness" (moot now that it has exited on its own), and every claim in this report is verified against the new, isolated synthetic
test suite (§4–§6), never against this process's output. The full, final 8-record set, for the record (task_id / arm / classification /
passed): `task_11`/`ARCH_PIPELINE`/`TASK_LOGIC_FAILURE`/False; `task_11`/`ARCH_COUNCIL`/`PASS`/True;
`task_11`/`BASE_N`/`TASK_LOGIC_FAILURE`/False; `task_11`/`BASE_1`/`TASK_LOGIC_FAILURE`/False;
`task_12`/`ARCH_COUNCIL`/`GENERATION_TRUNCATED`/False; `task_12`/`BASE_1`/`PASS`/True; `task_12`/`BASE_N`/`PASS`/True;
`task_12`/`ARCH_PIPELINE`/`PASS`/True. Two of these are worth naming precisely: `task_12`/`ARCH_COUNCIL`'s real `GENERATION_TRUNCATED`
result was produced entirely under the *old* code — per the original investigation's own finding, `ARCH_COUNCIL` genuinely does
contribute its own real event under the old, unscoped-list logic (unlike `ARCH_PIPELINE`), so this specific old-code result was not at
elevated risk of cross-arm misattribution the way a Pipeline candidate would have been, but it remains an old-code result, not a
demonstration of anything this repair changed. And `task_12`/`ARCH_PIPELINE`'s real `PASS` result carries no truncation-classification
risk at all regardless of old vs. new code, since `verify["passed"]` short-circuits both versions of `classify_result()` identically
before either one's ground-truth logic is ever reached. **A genuinely useful side effect of this process completing, separate from this
repair**: `BASE_N` has now completed for real, twice (task_11: real logic failure; task_12: real pass) — closing one of the two
concrete gaps the prior `tier3_remaining_blockers_investigation` mission's own verdict named as blocking readiness ("`BASE_N` has still
never completed a real cycle"). This observation is recorded here for completeness only; it is not part of, and does not substitute
for, this mission's own synthetic verification of the repair, and it does not change this report's verdict — a full, fresh sanity run
of the *repaired* script has still not been performed (see §9).

## 9. Remaining Limitations

- The `ARCH_COUNCIL` internal-ordering dependency described in §8 is real, disclosed, and — while structurally safer than the original
  bug — not literally eliminated at the level of "instrument every one of the 4 internal calls independently." Fully closing it would
  require either a small, explicit hook inside `river_deliberation.py` (a production file) or a wrapper capable of distinguishing
  concurrent/nested calls by something other than a single mutable slot — neither was attempted, since the current design is provably
  sufficient for the harness's actual scoring need (only the synthesis leg is ever scored) and does not require a production change.
- This repair was verified entirely with synthetic, in-process event data — it has not yet been exercised against a real, freshly-run
  instance of the *repaired* script end-to-end (doing so would mean starting a second, new sanity process alongside the untouched
  PID 52989, which was judged out of scope for this mission; the mission's own required deliverable is the synthetic proof, not a new
  live run).
- `INFRASTRUCTURE_FAILURE`'s assignment path (at the exception-handling call site in `main()`) was not modified by this repair and was
  not re-verified in this pass — it was already established as correct in the prior mission and this repair does not touch that logic.

## 10. Verdict

**REPAIRED AND VERIFIED, at the harness level, via direct test execution — not code inspection alone.** All 23 synthetic checks
(capture mechanism, Tests A–G, and the explicit stale-event invariant) pass against the repaired code. The five required invariants are
each directly demonstrated: (1) every truncation event is filed under a unique call identity, never an unscoped list (§3, capture
mechanism tests); (2) the classifier queries exactly the call it is given, via exact dictionary lookup, never "recent" or "latest"
(§3–§4); (3) a stale event, however old, cannot satisfy a lookup for a different call ID (§5's dedicated invariant test); (4)
`ARCH_PIPELINE` cannot inherit another arm's event under any tested ordering (Tests C, D, F); (5) randomized execution order does not
change classification outcome across 30 real, production-function-generated orderings (Test G) or under reversed classification-call
order (Test E). No production file was modified. The existing background sanity process was left running, untouched, and its 7
existing (pre-repair) records are explicitly not claimed as evidence of this repair.
