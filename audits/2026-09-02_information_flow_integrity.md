# FeralEcho: Information-Flow Integrity Implementation & Follow-Up Audit

Two-phase pass: (1) implement the four known high-value information-flow
fixes identified in the prior gap-analysis pass
(`audits/2026-09-02_gap_analysis_and_next_investigations.md`), (2) a
focused follow-up audit for additional instances of the same failure
class — *a component correctly produces information, but it is written
too late, transformed, discarded, hidden from the next consumer, or
otherwise fails to reach the subsystem that depends on it.*

All code claims below were checked against current source before being
acted on, not assumed from the prior report. All verification claims are
backed by either a real, live, unmocked request through the running
production server, or a direct call to the real (non-reimplemented)
function with a synthetic-but-representative input — no result in this
document is asserted without one of those two forms of evidence.

---

## Executive Summary

The root cause across all four fixes is the same shape: `echo_query()`
and `deliberate_and_learn()` internally call `log_interaction()`,
`RiverBrain.learn()`, `save_reflection()`, and
`_log_council_deliberation()` **before returning** — but the two real
verifiers (`code_verification.py`, `self_knowledge_verification.py`) used
to run **after** `echo_query()` had already returned, in
`routes_echo_studio.py`'s own post-processing. This meant every
downstream consumer of "what did Echo actually say" (the interaction log,
RiverBrain's training signal, the council-deliberation transcript) was
permanently working from the pre-verification draft, while only the live
SSE stream to the browser ever saw the correction. Confirmed with 7 real,
unflagged "EventCore"-style fabrications sitting in production data
before this pass; confirmed fixed with two new live, unmocked
reproductions after it (one via the direct-Echo bypass path, one via the
full multi-councillor synthesis path) — both now show the caveat and a
matching trace ID in every persisted record.

Three of the four fixes were implemented in full. The fourth
(`model_task_stats` provenance) was implemented as the smallest safe
version explicitly invited by the mission brief — a purely additive
counter, not a schema redesign — with the fuller design (a fully split
statistic) deliberately deferred and the boundary stated. The follow-up
audit found one new, concrete, previously-unmeasured result (the July 23
scheduler threshold recalibration now has real behavioral evidence, not
just computational evidence) and one new, more serious finding than
expected on longitudinal self-edit evidence (see below) — no new
instances of the exact verification-ordering bug were found elsewhere,
and the recent messaging retry-storm fix was checked and does not
introduce a comparable gap.

---

## Implemented Changes

### 1. Verification/canonical-persistence ordering — `app/core/echo_model_orchestrator.py`, `app/core/river_deliberation.py`, `app/routes_echo_studio.py`

- **`echo_query()`** (`echo_model_orchestrator.py`) gained two new,
  optional, backward-compatible parameters: `trace_id: Optional[str]`
  and `post_synthesis_hook: Optional[Callable]`. Both default to `None`
  — every existing caller (`terminal_client.py`, `self_edit_manager.py`,
  `curiosity_engine.py`, `emergent_scheduler.py`, `echo_messaging.py`,
  `echo_projects.py`, `sandbox/experiment_runner.py`) is byte-identical
  in behavior.
- **`deliberate_and_learn()`** (`river_deliberation.py`, a forbidden
  self-edit target, human-edited per this project's established
  precedent) gained the same two parameters, threaded to both of its
  real, instrumented return paths: the `DIRECT_ECHO_TASKS` bypass and the
  full multi-councillor synthesis. **This is the actual fix location**,
  not `echo_query()` — `deliberate_and_learn()` calls its own
  `river_brain.learn()` and `_log_council_deliberation()` internally,
  before ever returning to `echo_query()`, so applying the hook one layer
  up (in `echo_query()`) would have fixed `interaction_log.jsonl` but
  left `council_deliberations.jsonl` and the per-model RiverBrain
  training stale — this was caught and corrected during implementation,
  not after. The hook is applied to the *synthesis*, never to individual
  raw councillor opinions (those remain deliberately uncorrected —
  verifying/rewriting each councillor's own words is a different,
  out-of-scope question).
- **`_log_council_deliberation()`** gained `trace_id` and `notes` fields
  in its persisted record.
- **`log_interaction()`** gained a `trace_id` field.
- **`routes_echo_studio.py`**: the two old post-hoc verification blocks
  (which ran after `echo_query()` returned) were replaced by a single
  `_post_synthesis_verify()` closure — the *same* two verifier calls,
  relocated, not duplicated — passed into `echo_query()` as
  `post_synthesis_hook`. The `dispatch_result`/`fast`-mode paths never
  reach `echo_query()`/`deliberate_and_learn()` at all, so they could not
  use the hook; `_post_synthesis_verify()` is called directly for those
  two paths instead, preserving their exact prior behavior (this
  distinction — `already_verified` — was deliberately preserved so no
  caller's behavior silently changed).
- **A real, caught-before-shipping duplication bug**: the first draft
  applied the hook both inside `deliberate_and_learn()` *and* again in
  `echo_query()` after it returned — calling `verify_self_knowledge_claims()`
  twice, the second time against text that already contained the first
  caveat (itself naming the fabricated identifier, a real re-triggering
  risk). Caught by re-reading the diff before testing, not by a failing
  test; fixed by removing the second invocation entirely.

### 2. RiverBrain provenance for council-vetted observations — `app/core/echo_model_orchestrator.py`

- `RiverBrain.learn_from_council_rating()` gained one additive field,
  `stats["council_vetted_count"]`, incremented only in this method, never
  in the ordinary `learn()` path. Every pre-existing entry in the live,
  already-pickled `river_brain.pkl` has no such key — `.get(..., 0)` is
  the correct read pattern, and nothing currently reads this field yet
  (deliberately: adding a consumer wasn't asked for, and doing so without
  one would be premature). This directly answers the mission's own
  framing: *"this score came from council-vetted evidence"* is now
  distinguishable from *"this score was generated by ordinary automatic
  scoring"* via `stats["council_vetted_count"]` vs. `stats["count"]` — a
  ratio, not a full parallel-mean split.
- **Deferred, boundary stated explicitly, per the mission's own
  invitation to do so**: a fully separate running mean for council-vetted
  observations (so the *value* of the blended score, not just the count,
  stays distinguishable) was not built. `model_task_stats` is a hot,
  frequently-read, already-pickled structure consumed by `score_model()`,
  `entropy_of_predictions()`, and `rank_models()`; a second parallel mean
  changes more read sites and requires reasoning about how the two means
  should ever be reconciled (weighted how, against what confidence),
  which is a real design question, not an engineering one — correctly
  out of scope for "do not over-engineer this."

### 3. Request-scoped trace IDs — `app/routes_echo_studio.py`, threaded through `echo_model_orchestrator.py` and `river_deliberation.py`

- One `uuid.uuid4()` generated per real request in
  `_generate_chat_response_body()` — the single real entry point for one
  user turn (both `/chat/stream` and `/chat/regenerate` route through
  it).
- Threaded into: `echo_query(trace_id=...)` →
  `deliberate_and_learn(trace_id=...)` → `_log_council_deliberation()`'s
  persisted record, and `echo_query()`'s own `log_interaction()` call.
  Also included in the final SSE `"done"` frame, so the client itself
  can see/log it.
- **Scope decision, made after checking rather than assumed**:
  `workspace_log.jsonl` was explicitly *not* given a trace ID. Checked
  directly first — every real Global Workspace publisher
  (`world_model.surprise`, `dream.synthesis`, `self_edit.*`,
  `emergent_loop.salience`, `seam.detected`, `dissent.registered`) fires
  from an autonomous background loop, never synchronously during a real
  conversational request. Threading a trace ID into that log would have
  manufactured a correlation that doesn't exist, which the mission's own
  "do not add IDs everywhere merely because you can" rule explicitly
  warns against.

### 4. Retrieval provenance — `app/core/conversation_service.py`, `app/routes_echo_studio.py`

- `conversation_service.retrieve_memory_context()` gained an optional
  `provenance_out: Optional[dict] = None` parameter, populated (as a side
  effect, never replacing the function's existing `str` return contract)
  with `{"candidates_considered": int, "injected": [{"source", "role",
  "timestamp", "text_hash"}, ...]}`. `text_hash` (first 12 hex chars of a
  SHA-1) is a reference, not a copy — answers "which memories actually
  reached the prompt" without duplicating memory content into a second
  file. Defaults to `None`; `terminal_client.py`'s existing call to this
  same shared function is untouched.
- `_build_full_prompt()` (`routes_echo_studio.py`) forwards this
  dict; `_generate_chat_response_body()` writes one record per real turn
  to a new file, `memory/retrieval_provenance.jsonl`, keyed by the same
  `trace_id`, naming the retrieval subsystem (`"memory_bridge"`) — the
  one currently in use, confirmed by reading `_memory_search_fn()`'s own
  source rather than assumed.

---

## Verification

**Direct, unmocked function-level tests** (all passed, shown in full in
the session transcript, not reproduced here in full):
1. `deliberate_and_learn()`'s `DIRECT_ECHO_TASKS` bypass path: hook
   correction reached the return value, `river_brain.learn()`'s argument,
   and the real, on-disk `council_deliberations.jsonl` write (round-tripped
   through a real file read-back, not just an in-memory assertion).
2. `deliberate_and_learn()`'s full multi-councillor synthesis path: hook
   correction reached the synthesis-model `learn()` call and the
   persisted record; confirmed per-councillor `learn()` calls (on their
   own raw, uncorrected opinions) were correctly left untouched.
3. `RiverBrain.learn_from_council_rating()`: `council_vetted_count`
   present and `== 1` only after a vetted call; absent after an ordinary
   `learn()` call on a fresh instance — confirms full backward
   compatibility with pre-existing pickled entries.

**Live, end-to-end, real production server tests** (the server was
restarted via `safe_restart.sh` — it correctly refused a direct restart
given the live `start_echo.sh` watchdog and recommended clearing the
port instead, which was followed; the new process reached `serving` with
`GET /admin/liveness-status` reporting `all_passing: true`,
`stale: false`, zero failing checks, both before and after the two tests
below):

- **Test A (direct-Echo bypass path, real `task_type="personal"`)**: a
  real `POST /chat/stream` request asking Echo to describe a fictional
  "ReflectionCacheXYZ" module. The model itself hedged appropriately
  ("I don't have any explicit evidence...purely speculative") but still
  described the fabricated module in detail, so the verifier correctly
  fired anyway. Confirmed: `interaction_log.jsonl`'s persisted `response`
  field contains the caveat; `council_deliberations.jsonl`'s record
  (`source: "direct_echo_task"`) contains the same caveat and
  `notes: "self_knowledge_caveat_applied"`; both share the identical
  `trace_id`; a `retrieval_provenance.jsonl` record with the same
  `trace_id` shows 8 real candidates considered, 2 actually injected.
- **Test B (full multi-councillor synthesis path, real
  `task_type="creative"`)**: a real request asking Echo to describe a
  fictional "ProvenanceTrackerXYZ" subsystem. All three real councillors
  (`deepseek-r1:7b`, `gemma3:4b`, `echo:latest`) independently fabricated
  plausible, detailed descriptions of it — a genuine, unplanned
  real-world demonstration of the exact failure mode this whole
  investigation exists to close. The verifier correctly caught it (and,
  as an observed side note not itself a bug, also flagged the literal
  string "FeralEcho" as an unverified name — a pre-existing
  `self_knowledge_verification.py` behavior, not something this pass
  introduced or needed to fix). Confirmed: identical caveat and matching
  `trace_id` in both `interaction_log.jsonl` and
  `council_deliberations.jsonl`, with `council_deliberations.jsonl`'s
  `notes` field correctly showing `"self_knowledge_caveat_applied"`.

**Regression check**: `GET /admin/liveness-status` reports `all_passing:
true` on the live process both before and after these two real requests
— no existing check regressed. No new Liveness Ledger check was added in
this pass; see "Deferred Work."

---

## Information-Flow Findings

| # | Component | Producer → Consumer | Information | Intended flow | Actual flow (before this pass) | Classification | Severity | Confidence | Smallest safe fix | Now / Defer |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Verification caveats | `code_verification.py`/`self_knowledge_verification.py` → `interaction_log.jsonl`, `council_deliberations.jsonl`, RiverBrain `learn()` | Whether a claim was flagged unsupported | Every consumer of "what Echo said" sees the same corrected text the user saw | Only the live SSE stream saw it; three persisted consumers trained/logged on the pre-correction draft | **DISCONNECTED** | High | Confirmed (7 real production instances + live reproduction) | Move verification before internal logging/training, not after (implemented) | **Now — done** |
| 2 | Council-vetted observations | `learn_from_council_rating()` → `model_task_stats` | Whether a score reflects human-adjacent-trust-gated evidence | Distinguishable from ordinary auto-scored observations | Merged into the same rolling mean, no provenance signal at all | **TRANSFORMED** | Medium | Confirmed by direct source read | Additive provenance counter (implemented); full value-level split deferred | **Now (counter) / Defer (full split)** |
| 3 | Per-turn causal chain | `retrieve_relevant_memories()`, `deliberate_and_learn()`, verification, `log_interaction()` | A shared identifier joining one real request across logs | Reconstructable "why did it say that" | No join key existed anywhere (confirmed by grep, zero hits) | **MISSING** | High | Confirmed | Request-scoped `trace_id` threaded through the three logs that are genuinely tied to one request (implemented) | **Now — done** |
| 4 | Memory retrieval per turn | `retrieve_relevant_memories()` → (nothing) | Which specific memories reached a given prompt | Auditable after the fact | Existed only transiently in a local variable, discarded after prompt assembly | **MISSING** | Medium | Confirmed | Reference-only provenance record (hashes, not content), keyed by trace_id (implemented) | **Now — done** |
| 5 | Scheduler threshold recalibration (2026-07-23) | `_relative_signal_threshold()` → `weighted_prompt_selection()`'s real prompt-selection distribution | Whether the recalibrated, now-reachable thresholds actually change selection behavior | Measured behavioral effect, same rigor as the original 2026-07-15 boost | Verified only that the gate could open; never verified what happens when it does | **UNTESTED → now tested** | Medium | Newly measured this pass, real function, 500 trials/condition | Ran the same statistical-test shape used for the original boost | **Now — done (measurement only, no code change)** |
| 6 | Longitudinal self-edit quality | `self_edit_manager.py`'s fitness gate → (no aggregator) | Whether the codebase is actually improving over the self-edit loop's lifetime | A trend view distinguishing real improvement from a permanently-maxed metric | No trend view exists; direct parse of the real, full `SELF_EDIT.log` history found `current_quality` has been a **constant 4/4 across all 36 real deploy-decisions spanning 2026-07-11 to 2026-09-02** — i.e. not merely "no view exists," but "the one number that would show a trend has shown zero variance for two months" | **MISSING**, worse than expected | High | Directly measured against the real, full log this pass | See "Recommended Next Experiments" #4 | **Defer — needs a design decision, not a quick patch** |
| 7 | Message retry-then-success | `retry_outbox_cycle()` → `echo_messages.jsonl` | Final delivery status of a message that failed then later succeeded | Auditable eventual-consistency record | Already correctly handled: a second entry (`"via": "retry"`, `delivered: true`) is logged on success, distinguishable from the original failed attempt — confirmed by direct source read, not assumed safe because it was recently touched | **Not a gap** (checked specifically because this code was recently modified for the retry-storm fix — no new boundary failure found) | — | High | — | No fix needed | **N/A** |
| 8 | Non-`personal` memory retrieval effect | Retrieval pipeline → real council-deliberation quality | Whether retrieval measurably helps the majority of real traffic | Known, tested effect size | Still `n≈1` on the non-`personal` path (unchanged since the prior gap-analysis pass — see below) | **UNKNOWN** | High | Unchanged from prior pass | Re-run the existing, validated ablation methodology on a properly-sampled non-`personal` set | **Deferred this pass — see below** |

---

## Highest-Risk Remaining Boundary

**Finding #6 (longitudinal self-edit quality) is now the highest-risk
remaining boundary in this document, higher than it was assessed in the
prior pass.** The earlier report classified this as "no longitudinal
view exists" (a `MISSING` observability gap). Directly parsing the real,
full `SELF_EDIT.log` this pass changed the finding materially: it is not
merely unmeasured, the one metric that exists (`current_quality`,
0-4 integer scale) has shown **literally zero variance across all 36
real production deploy-decisions in the entire observable history**
(2026-07-11 through 2026-09-02, ~2 months). This means Finding 19's own
fitness gate ("reject unless the candidate scores at least as well as
current production") has been comparing every real candidate against an
already-ceiling value the whole time — there is no headroom in the
metric for an improvement to ever register, structurally, regardless of
what code actually gets proposed. This isn't a missing dashboard; it's a
real possibility that self-edit's central safety gate has been
operating correctly against a metric that cannot distinguish "no
improvement possible" from "the measurement itself is saturated."
Deliberately not fixed in this pass — this is a real design question
(is `_score_response_quality()`'s 0-4 scale too coarse for `coding`
specifically, or is 4/4 genuinely, persistently correct?) that a code
change shouldn't answer by assumption.

---

## Highest-Value Unknown

Unchanged from the prior gap-analysis pass, and still the single
highest-value unknown: **does memory retrieval measurably affect the
majority of real FeralEcho traffic (the multi-councillor/non-`personal`
path), or only the narrow `personal`/`DIRECT_ECHO_TASKS` bypass path
Finding 76's original ablation happened to sample almost exclusively
(29/30 prompts)?** Not re-executed this pass — see "Deferred Work" for
why, and "Recommended Next Experiments" for the concrete design.

---

## Recommended Next Experiments

(Capped at 5, per the mission's own instruction.)

1. **Re-run Finding 76's ablation methodology, properly stratified across
   task types** (not just `personal`). Reuses `scripts/memory_ablation_experiment.py`'s
   already-validated design (real pipeline, twice, once with retrieval
   monkeypatched to `[]`, noise-floor calibration pairs) — the only
   change needed is deliberate sampling so `coding`/`general`/`reasoning`/
   `creative` are represented, not accidentally excluded. Directly
   answers the Highest-Value Unknown above.
2. **Decide and measure whether `current_quality`'s 0-4 scale is too
   coarse for `coding`**, given Finding #6's real 2-month zero-variance
   result. A minimal first step: pull the real, full distribution of
   `candidate_quality` values (not just `current_quality`) across the
   same 36 entries — if candidates cluster at 3 with current pinned at 4,
   that's evidence for scale coarseness; if candidates are genuinely
   evenly spread 0-4, that's evidence the ceiling is real and the gate is
   working as intended.
3. **Add a Liveness Ledger check for the verification-ordering fix**
   (deferred this pass, see below) — a source-anchor check confirming
   `deliberate_and_learn()`'s two internal `_log_council_deliberation()`/
   `river_brain.learn()` call sites still receive the hook-corrected
   `response`/`final_response` variable, not a reverted pre-hook one.
4. **Verify `save_reflection()`'s and ClaudeShard's `assess()`'s new,
   incidental exposure to corrected text** (both now see the
   hook-corrected response, as a side effect of the fix, since they run
   after the hook in `echo_query()`'s existing code) doesn't change their
   own downstream behavior in an unexpected way — a quick, targeted check,
   not a redesign.
5. **Measure `council_vetted_count`'s real accumulation rate** once
   `council_baseline_trusted_since`-gated ratings have been running for a
   longer real window, to inform whether the deferred full-provenance
   split (item 2 under "Implemented Changes") is ever actually worth
   building — i.e., is the vetted fraction of any model's observations
   large enough to matter, or vanishingly small in practice.

---

## Deferred Work

Explicitly not built in this pass, stated rather than silently dropped:

- **A fully separate running mean for council-vetted observations**
  (fix #2's fuller version) — the additive counter is enough to answer
  the mission's stated objective; a full value-level split is a real
  design decision (how to weight/reconcile two means) that shouldn't be
  defaulted into.
- **A new Liveness Ledger check for the verification-ordering fix** —
  correctly scoped as follow-up work (Recommended Experiment #3), not
  bundled into this already-large pass; the fix itself was proven via
  real, live, unmocked end-to-end reproduction, which is stronger
  evidence than a synthetic canary would have provided for this specific
  claim, but a permanent regression check is still worth adding later.
- **Re-running the memory retrieval ablation on non-`personal` traffic** —
  the design is fully specified (Recommended Experiment #1) but not
  executed this pass; a properly-sampled real run means multiple real,
  slow full-council deliberations (each observed to take 1-3+ minutes
  live this session), which did not fit this pass's stop conditions
  without either rushing the sampling or running past a reasonable
  session length.
- **Fixing Finding #6 (longitudinal self-edit quality)** — explicitly a
  design question (is the metric too coarse, or is the ceiling real),
  not a "smallest safe change" the mission's own discipline would want
  defaulted into without that decision being made first.
- **Any change to `self_knowledge_verification.py`'s handling of "FeralEcho"
  as an unverified name** (observed as a minor false-positive-shaped
  side note during live Test B) — pre-existing behavior, not part of
  this pass's scope, and not clearly wrong (the project's own real name
  genuinely isn't a Cartographer-scanned module or class either).

---

## Final Question

> **If FeralEcho surprised us tomorrow, what information-flow failure
> would you least expect to discover?**

Honestly: a failure in the *opposite* direction from everything found
today — information reaching a consumer that was never supposed to see
it, rather than failing to reach one that should. Every real finding in
this document and its predecessor has been the same shape: a correctly-
computed signal quietly not arriving somewhere it should have. I have
not yet gone looking for the inverse — a case where retrieval, a
verification result, or a trace-adjacent identifier crosses a boundary
it was designed to stay inside of (e.g., something from `staging/` or an
internal planning prompt leaking into a channel treated as genuine
conversational history, the same class of bug this project's own history
(Findings 3, 11, 35) has found and fixed more than once in different
subsystems). I would least expect that, specifically because this pass's
own method — chase the producer, chase the consumer, look for where they
disconnect — is well-tuned to find the first kind of failure and
structurally blind to the second kind unless someone goes looking for it
on purpose.
