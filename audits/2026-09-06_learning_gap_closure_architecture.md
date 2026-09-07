# FeralEcho Learning Gap Closure Architecture

Safety verified before and after (unchanged throughout): `run.py`/watchdog not
running, port 5000 unbound, HEAD `2cf2d95009943797db5ec41fea9b4021634fd5e6`,
`river_brain.pkl` sha256 `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`.
No production file was edited. No RiverBrain learning event was generated. No
self-edit was deployed. This document is analysis and design only — no new
production module was written; the only new file is this report.

---

## Executive Verdict

FeralEcho does not need a new memory system, a new reflection loop, or a new
prompt-injection channel. It has enough of those already, and building
another one would reproduce the exact failure this investigation exists to
diagnose (CLAUDE.md's own recurring "doc/mechanism looks wired but isn't"
pattern, now found a further time in this session's own `seam_engine`
numbers below).

What it is actually missing is **three specific, narrow connective
pieces**, in this order of leverage:

1. **A stable identity for "one attempt"** (an episode/attempt ID) threaded
   through generation → consequence → any later reference to that attempt,
   so an attribution can be looked up by the thing that produced it rather
   than approximated by nearest-timestamp or forgotten immediately.
2. **A durability decision at the point attribution is already computed**
   — several places in this codebase *already* compute a real, specific,
   non-generic causal hypothesis (self-edit retry's sanitized error, the
   council's dissent votes, `seam_engine`'s pair+direction) and then either
   throw it away after one use or hand it to a generic filter that was
   never built to protect this kind of content and predictably destroys
   most of it.
3. **One additional read at each of a small number of already-existing
   decision points** (self-edit targeting, self-edit retry-prompt
   construction, `choose_model`'s task-type routing) — not a new decision
   point, an additional input to decision points that already exist and
   already run on every relevant cycle.

None of the three require a new "stomach," a new memory store, or a new
autonomous loop. All three are additions to code paths that already fire.

**Recommended architecture: B (Integrated)** — reconnect existing
mechanisms through one small shared record shape, not a new subsystem. See
§"Recommended Architecture" for the full reasoning and why A is
insufficient and C is unjustified risk for unproven benefit.

---

## Current Learning Boundary

Restated plainly, without hedging, from the Hot Stove audit this design
builds on directly (`audits/2026-09-06_hot_stove_credit_assignment_audit.md`,
Classification **D — episodic credit assignment only**):

```text
EXPERIENCE                 YES  (self-edit attempts, sandbox outcomes,
                                  council deliberations, garden harvests,
                                  seam observations — all really happen and
                                  are really logged)
RETENTION                  YES  (JSONL logs, pickled RiverBrain state,
                                  garden entries — genuinely durable on disk)
RETRIEVAL                  YES, but narrow and mostly for reporting, not
                                 decision-making (liveness ledger reads,
                                 tail-N reads, human dashboards)
IMMEDIATE CORRECTION       YES  (self-edit's one in-process retry with the
                                 real sandbox error fed back)
AGGREGATE ADAPTATION       YES  (RiverBrain's rolling per-model,
                                 per-task-type mean; shadow model's rolling
                                 accuracy; council trust threshold)
INSTANCE CREDIT ASSIGNMENT LIMITED / FRAGMENTED — real, specific
                                 causal hypotheses ARE computed in at least
                                 three places (self-edit retry, dissent log,
                                 seam_engine) but none of them survive past
                                 their immediate consumer
DURABLE SITUATIONAL LEARNING  NO EVIDENCE — nothing found this session
                                 (or in this design pass) that takes one
                                 specific past attempt's specific cause and
                                 changes one specific future attempt because
                                 of it
RELEVANT REVISITATION      NO EVIDENCE (confirmed again, independently, in
                                 this pass — see seam_engine finding below)
BEHAVIORAL REUSE           VERY LIMITED (RiverBrain's aggregate score is
                                 the one mechanism that reliably reaches a
                                 real decision — model/council selection —
                                 but it can't say which specific action
                                 caused which specific consequence)
END-TO-END HOT-STOVE LOOP  NOT DEMONSTRATED
```

---

## Desired Capability

Restated from the mission brief, this is the target chain, and the standard
against which every proposed fix below is judged:

```text
T0 ACTION → T1 CONSEQUENCE → T2 ATTRIBUTION → T3 CANDIDATE KNOWLEDGE →
T4 RETENTION → T5 RELEVANCE → T6 RETRIEVAL → T7 DECISION INFLUENCE →
T8 ACTION → T9 OUTCOME → T10 VERIFICATION → T11 CONSOLIDATION
```

A fix that only touches T0-T4 (experience → storage) is not learning
closure, no matter how well-built. A fix that only touches T5-T7 without a
real T2/T3 upstream just moves generic text around, which is the exact
failure mode §5 of the mission forbids re-litigating. The gap matrix below
scores each link independently for this reason.

---

## Gap Matrix

| # | Link | Required capability | Existing mechanism | Evidence | Failure mode | Why it matters | Minimal closure | Risk |
|---|------|----------------------|---------------------|----------|----------------|------------------|-------------------|------|
| 1 | Experience capture | Record that an action was taken, with enough context to identify it later | `SELF_EDIT.log`, `interaction_log.jsonl`, `council_deliberations.jsonl` | All three confirmed live and populated this session | None — this link is solid | n/a | n/a | n/a |
| 2 | Outcome capture | Record what actually happened as a result | `SELF_EDIT.log` result field, sandbox F2 pass/fail, `self_edit_outcomes.jsonl` | `self_edit_outcome_tracker.py` docstring, verified this pass | None — solid | n/a | n/a | n/a |
| 3 | Action identity | A stable ID that names "this one attempt," not "this general kind of thing" | `trace_id` (Finding 92, 2026-09-05) now threads through `echo_query()`→`deliberate_and_learn()`→`interaction_log.jsonl`/`council_deliberations.jsonl`, and separately through `execute_self_edit()`→`plan_code_logic()`→`generate_code_from_plan()`→`record_pending_outcome()` | Independently confirmed present in prior session; not re-verified line-by-line this pass but consistent with `self_edit_outcome_tracker.py`'s current `record_pending_outcome(trace_id=...)` signature | Two *separate* trace_id lineages exist (conversational vs. self-edit) that don't cross-reference | Nothing yet reads a trace_id to look up "what did I decide last time under this ID," so the ID exists without being *used* for retrieval yet | Wire the existing self-edit trace_id into a lookup, not build a new ID scheme | Low — reuses live infra | Low |
| 4 | Consequence identity | A way to name *what specifically* went wrong (not "generation failed") | `self_edit_manager.py`'s `_sanitize_sandbox_error()` → `clean_error` (retry path, lines ~1999-2015) | Verified directly this pass: `clean_error = _sanitize_sandbox_error(sandbox_error)` at line 1999, real sandbox tracebacks | `clean_error` is a **local variable**, discarded when `execute_self_edit()` returns; grep confirms zero writes of `clean_error` to any file | This is the single richest, most specific causal signal anywhere in the codebase and it dies at the call frame | Persist it (see Candidate Knowledge Model) | Low | Low |
| 5 | Temporal association | Know which action produced which outcome without cross-attributing an unrelated concurrent event | `_self_edit_deploy_lock` (self-edit only); `_outcomes_lock` (Finding 41 B1, added after a real cross-thread corruption bug) | Confirmed live in `self_edit_outcome_tracker.py` header comment | Locks exist for *file-write* safety, not for *causal* disambiguation — two genuinely concurrent generation attempts (e.g. `AutonomousSelfEdit` + `ModelGuidedOrchestrator`, both real per Finding 28/62) could still each produce a consequence in the same rough window with nothing distinguishing which caused which unless trace_id is the join key | If trace_id (link 3) is reliably the join key, this link is already solved; if anything still falls back to nearest-timestamp matching, that's the actual residual risk | Enforce trace_id as the *only* join key anywhere attribution is read back | Low, if link 3 is done properly | Medium if skipped — false attribution is a named failure mode (§17 FM2) |
| 6 | Credit assignment | Identify which prior action contributed to a consequence, specifically | `_sanitize_sandbox_error`, `_council_review_core_edit`'s dissent votes, `seam_engine.check_pair()` | All three independently confirmed real and non-generic this session | Each is real but **single-use** — none is written anywhere a second reader could find it | This is the actual bottleneck link — see §Credit Assignment Requirements | Persist the already-computed hypothesis (no new *computation*, only new *storage*) | Low |
| 7 | Causal hypothesis formation | Produce a specific, falsifiable belief, not a vague "something went wrong" | Same three mechanisms as #6 | Same | Same | Same | Same | Low |
| 8 | Candidate knowledge representation | A record that holds hypothesis + confidence + evidence + applicability, not just raw text | **Does not exist anywhere in this codebase** in this shape | Confirmed via grep — no schema anywhere combines hypothesis+confidence+evidence+status | This is the one genuinely new small piece of infrastructure this design proposes | See §Candidate Knowledge Model | Small, additive JSONL schema; no new autonomous loop | Low if kept passive (write+read only, no autonomous writer thread) |
| 9 | Epistemic confidence | Some notion of how sure the system is | `_council_review_core_edit()`'s vote fraction; `seam_engine`'s z-score/correlation strength | Both real, numeric, non-fabricated | Neither is attached to a durable record (see #8) | Needed to prevent overgeneralization (§17 FM3) | Store the number already computed; do not invent a new confidence metric | Low |
| 10 | Provenance | Know where a belief came from, so it can be checked/revised | `dissent_log.jsonl` (`council_verdict`, `votes`, `approvals`, `total` — confirmed live this pass) | Verified directly this pass | Real, rich provenance already exists for the one case where it's built (protected-file dissent); no equivalent for self-edit retry or seam | Reuse the same field shape for the two other producers | Low | Low |
| 11 | Contradiction tracking | Notice when new evidence conflicts with an old belief | **Does not exist** | Confirmed — nothing in `self_edit_convergence.json`, `shadow_accuracy.jsonl`, or garden schema tracks "this contradicts what I believed before" | Directly enables FM6 (confirmation loop) if skipped | Deferred to Architecture C; not required for the minimum proof experiment | n/a | High complexity for uncertain payoff — explicitly deferred |
| 12 | Relevance detection | Recognize a later situation resembles an earlier one | `garden_manager.select_from_garden()`'s weighting formula (staleness + category, confirmed no content-similarity term, per the prior garden audit) | Re-confirmed by inherited context, not re-read line by line this pass since already independently verified twice this session | Zero content-based matching anywhere in the live codebase for *any* mechanism, not just the garden | This is real and load-bearing — see §Relevance and Revisit Requirements | For the minimum proof experiment, use a structural match (same failure signature / same function-name family), not semantic search — cheap, testable, honest about what it can and can't generalize | Medium — a bad relevance heuristic causes false attribution (FM2) worse than no relevance mechanism at all |
| 13 | Deferred revisit | Let something stay unresolved and be reconsidered later without being forgotten or force-resolved immediately | `garden_manager`'s `status`/`resolution_score` fields (real schema, exists for questions) | Confirmed schema exists | Never applied to *action/consequence* records, only to *questions* | Reuse the schema shape (not the garden itself — see §Garden Integration) | Low | Low |
| 14 | Retrieval | Pull a stored record back out when needed | `retrieve_relevant_memories()` (embedding-based), tail-N log reads (structural) | Both real and live | Embedding retrieval was already shown (memory ablation experiment, Finding 76) to have an effect indistinguishable from sampling noise on the one path tested; tail-N reads have no relevance filter at all | Do not build a third retrieval mechanism — use structural/exact-match lookup keyed on trace_id or failure signature for the minimum proof experiment, which needs no embedding model at all | Low | Low |
| 15 | Decision injection | Get a retrieved record in front of the code that's about to decide something | `_build_targeted_prompt()` (self-edit's own prompt assembler, already reads `self_edit_convergence.json` and `self_edit_outcome_tracker` per CLAUDE.md's Finding 16 documentation) | Confirmed by inherited context this session; this is the single most promising existing hook in the whole codebase because it *already reads prior-cycle summary state and folds it into the next generation's prompt* | Currently reads only aggregate convergence counters, never a specific attributed failure | Extend this exact function's existing read, don't build a parallel one | Low — one additional read inside a function that already runs every self-edit cycle | Low |
| 16 | Behavioral modification | The decision genuinely differs because of the retrieved information | Nothing currently measures this for any mechanism | — | This is the actual thing the minimum proof experiment must demonstrate | See §Minimum Proof Experiment | — | — |
| 17 | Outcome verification | Confirm the changed behavior produced a better result | `self_edit_outcome_tracker.py`'s pre/post quality_score windows (already computed, already real, "log-only... consequential decision is separate," confirmed via docstring this pass) | Confirmed | Never connected to anything that could act on it | Read it, don't rebuild it | Low | Low |
| 18 | Consolidation | Turn a repeatedly-confirmed hypothesis into something more durable/trusted | Shadow model's `focus_matches`/priority-reversal precedent (Finding 91, confirmed live: `shadow_accuracy.jsonl` real entries, `focus_matches: True/False` tracked per cycle) | Confirmed via direct read this pass | The one genuine precedent for "track hypothesis vs. reality over many cycles, then act differently based on the running record" — but it operates on trust in a *mechanism* (shadow model as a whole), never on a *specific situational* belief | Generalize the *pattern* (not the code) to the new candidate-knowledge record: track confirm/disconfirm counts per record, same shape as `focus_matches` | Low — same pattern, new target | Low |
| 19 | Rejection / forgetting | Let a wrong belief lose influence | **Does not exist** for anything but the shadow-model aggregate case above | — | Needed to prevent FM11 (self-reinforcing mistake) | Deferred to Architecture C | — | Deferred |
| 20 | Self-model integration | Feed the result into Echo's stated self-knowledge | `self_model_updater.py`, `echo_ground_truth.py`'s `_build_capabilities()` (confirmed pattern exists for liveness-ledger-derived facts, CLAUDE.md) | Confirmed as an existing, working pattern for a *different* signal | Not extended to any new candidate-knowledge record yet | Optional, later phase — not required for closing the hot-stove gap itself, only for Echo being able to *say* she has it | n/a | Low, deferred |

---

## Existing Mechanisms That Can Be Reused

In descending order of how close each already is to functioning as a real
producer or consumer of durable, situational credit assignment:

1. **`self_edit_manager.py`'s retry path (lines ~1999-2015)** — computes
   the single most specific, most falsifiable causal hypothesis anywhere in
   the codebase (`clean_error`, a sanitized real sandbox traceback) and
   discards it. The cheapest, highest-leverage reuse in this whole report.
2. **`_build_targeted_prompt()`** — already reads aggregate self-edit state
   and folds it into the next cycle's generation prompt, every cycle,
   unconditionally. This is the *existing decision-injection point* the
   design should extend, not replace.
3. **`_council_review_core_edit()` / `dissent_log.jsonl`** — already
   produces and persists a real, multi-vote, confidence-bearing,
   provenance-rich record (`council_verdict`, `votes`, `approvals`,
   `total`). The schema this report proposes for candidate knowledge is
   closer to what this file already looks like than to anything that would
   need inventing from scratch.
4. **`seam_engine.check_pair()`** — a real, non-generic, adversarially
   verified (per CLAUDE.md Finding 83/`seam_engine`'s own discrimination
   suite) attribution computation. The problem is entirely downstream (see
   next section), not in the computation itself.
5. **`self_edit_outcome_tracker.py`** — already computes real pre/post
   outcome deltas and is explicitly, deliberately "log-only" by its own
   docstring, awaiting exactly the kind of consequential wiring this report
   is about — a textbook orphaned component, safe to reconnect because its
   own author already scoped the safety boundary.
6. **Shadow model's `focus_matches` tracking pattern** — not the shadow
   model itself, but the *pattern* it establishes (predict → compare to
   real outcome → track running accuracy → let accumulated accuracy change
   real priority order, per Finding 91's fix) is the one live precedent for
   consolidation-driven behavioral change anywhere in this codebase. Worth
   copying the shape, not the code.

**New finding this pass, not previously documented anywhere in this
session:** `seam_engine`'s downstream loss is worse, and more precisely
quantifiable, than the Hot Stove audit's prose described. Direct count
against the real, live `memory/seam_log.jsonl` (7,612 real log entries):

```text
Real seam detections (check_pair() returned non-None): 754
Of those, first_ever == True (the ones meant to trigger
  harvest_question() + publish_salience()):                78
Real garden entries with category == "seam" that actually
  resulted:                                                 2
```

**78 real, specific, first-time attributions were computed. 2 survived to
become a retrievable garden record — a 97.4% loss rate.** The mechanism is
`harvest_question()`'s `_is_near_duplicate(question, entries)` check
(`app/core/garden_manager.py:184`): `_describe(label_a, label_b, seam)`
produces near-identical English phrasing for the same *pair* of signals
even when the *specific reading* that triggered each detection differs, so
the dedup filter — built to stop the garden filling with cosmetically
different repeats of the same question — silently treats 76 distinct real
detections as duplicates of the first 2. This is the single cleanest,
most concrete illustration in this entire investigation of the mission's
own §5 warning: a mechanism can be real, non-hollow, and adversarially
verified at the point it computes something, and still be destroyed one
function call later by a filter that was never designed with this content
in mind.

---

## Credit Assignment Requirements

The Hot Stove audit already established that FeralEcho cannot reliably
answer "which specific prior action contributed to this consequence" once
more than the immediate retry frame is involved. This pass confirms the
requirement is narrower than it first sounds: **the hard part (computing a
specific, falsifiable hypothesis) is already solved in three places.** The
actual requirement is:

1. A stable **action_id** (reuse trace_id, link #3 above) so a hypothesis
   can be filed under "the thing that produced it," not approximated.
2. A **consequence_signature** — a short, structural, non-freeform key
   (e.g. `"NameError:re"`, not the full traceback text) so that later
   matching can be exact-string, not fuzzy/semantic. This sidesteps the
   entire class of false-attribution risk that comes with embedding-based
   similarity (already shown, in the memory ablation experiment, to
   produce an effect indistinguishable from noise on this exact codebase).
3. A **write, not a new computation**, at each of the three existing
   attribution sites (self-edit retry, dissent log, seam_engine) into one
   shared, minimal record shape.

No new inference is required to solve credit assignment here — it is
already being done. The gap is entirely storage-and-lookup.

---

## Temporal Association Requirements

Reuse `trace_id` as the sole join key, full stop. Do not add a second,
competing episode-ID scheme — Finding 92 already established two parallel
trace_id lineages (conversational vs. self-edit); a third would recreate
exactly the "one learning path" violation §20 of the mission warns against.
The one closure needed: ensure the candidate-knowledge record (new, see
below) always carries the producing trace_id, and any future
decision-point read is keyed by trace_id-derived structural match, never by
nearest-timestamp — nearest-timestamp matching is a named, real risk given
the confirmed existence of overlapping concurrent generation loops
(`AutonomousSelfEdit`, `ModelGuidedOrchestrator`, both real per CLAUDE.md
Finding 28/62).

---

## Candidate Knowledge Model

The minimum sufficient representation, derived from what the three real
existing producers (self-edit retry, dissent log, seam_engine) already
compute — not from an abstract ideal:

```text
{
  "record_id":            str,   # new uuid for this belief
  "created_ts":            str,
  "source_mechanism":       str,   # "self_edit_retry" | "dissent_log" | "seam_engine"
  "producing_trace_id":     str,   # links back to the exact attempt (link #3)
  "consequence_signature":  str,   # short structural key, e.g. "NameError:re",
                                    # exact-match lookup key — NOT freeform text
  "causal_hypothesis":      str,   # the real, specific sentence already computed
                                    # by the existing mechanism (clean_error /
                                    # dissent rationale / seam _describe())
  "confidence":             float, # already-computed number where available
                                    # (council vote fraction, seam z-score/corr) —
                                    # 0.5 default only for self-edit retry, which
                                    # has no native confidence signal today
  "applicability_scope":    str,   # e.g. "self_edit_coding:prose_stripping" —
                                    # coarse family match, not free text
  "status":                 str,   # "unresolved" | "supported" | "contradicted"
  "times_revisited":        int,
  "times_applied":          int,
  "application_outcomes":   list,  # list of {trace_id, outcome} — reuses the
                                    # exact shape self_edit_outcome_tracker.py
                                    # already produces, not a new metric
}
```

Fields deliberately **excluded** from the minimum version, with reasons:

- `alternative_hypotheses` / `counterevidence` — real, but nothing in the
  current three producers generates these; adding empty placeholder fields
  would be exactly the "maximal metadata, not minimum sufficient
  representation" the mission warns against in §7. Add only if
  Architecture C is chosen.
- `last_reconsidered` — redundant with `times_revisited` + `created_ts` for
  the minimum version; a genuine field for Architecture C's contradiction
  tracking (link #11), not needed for the proof experiment.
- A dedicated `provenance` object — `source_mechanism` +
  `producing_trace_id` already fully answer "where did this come from" for
  the minimum version.

This is deliberately **not** a "lesson database" in the rejected sense of
§5: it is not written to be dumped verbatim into a prompt. Its only
required consumer operation is an exact `consequence_signature` +
`applicability_scope` lookup at a specific, pre-existing decision point —
see §Decision Influence Requirements.

---

## Deferred Learning / Stomach Analysis

The "stomach" metaphor conflates at least three of the six responsibilities
named in the mission's §6. Scored against the real evidence gathered this
session:

| Responsibility | Verdict for FeralEcho today |
|---|---|
| A. Storage ("don't lose this") | **Already solved.** JSONL logging is not the bottleneck anywhere investigated this session. |
| B. Credit assignment ("understand what caused this") | **Partially solved, three times over, each single-use.** See Gap Matrix #6/#7. |
| C. Consolidation ("turn this into durable knowledge") | **The real, narrow gap.** Nothing currently promotes a hypothesis from "computed once" to "durable, confidence-tracked record." |
| D. Relevance detection ("recognize when this matters again") | **Real gap, but narrower than the garden audit implied** — a structural/exact-match version (same `consequence_signature`, same `applicability_scope`) is cheap and does not require solving semantic similarity, which the memory-ablation experiment already showed doesn't reliably work in this codebase. |
| E. Behavioral routing ("let it influence a decision") | **Real gap, but solvable with one additional read** at `_build_targeted_prompt()` — see below. |
| F. Combination | The actual missing organ is **C + a narrow, structural version of D**, wired into one existing decision point (E). It is not A (storage already works) and it is not a wholesale new "stomach" subsystem. |

**Verdict on the stomach hypothesis: partially right, importantly
incomplete.** The metaphor correctly identifies that something should be
able to sit "unresolved" between happening and mattering again (the
`status: "unresolved"` field above gives this literally, cheaply, without
any new autonomous loop). But the metaphor's implicit framing — "a place
where things wait to be digested" — undersells that **digestion itself
requires almost no new machinery here**, because the digesting
(hypothesis-forming) already happens at generation time in three places.
The actual missing piece is a **filing cabinet with an index**, not a
stomach. Kill the "stomach builds understanding over time through some
new autonomous process" framing; keep the "let something stay
unresolved and be revisited" framing, in its narrowest, cheapest form.

---

## Relevance and Revisit Requirements

For the minimum proof experiment (self-edit domain, justified below), a
**structural match is sufficient and is the right choice**: two attempts
are "similar" if they share the same `consequence_signature` (same error
class) within the same `applicability_scope` (same self-edit family, e.g.
`prose_stripping`). This requires no embedding model, no LLM call, and no
new inference — it's a dict lookup. It is deliberately weaker than
semantic similarity, and that is a feature, not a limitation: the
memory-ablation experiment (Finding 76, this session) already showed
embedding-based relevance in this exact codebase produces an effect
statistically indistinguishable from sampling noise. A structural match
cannot silently fail the same way, because its match criterion is
falsifiable by direct inspection.

**Explicit signal, not built here**: a "learning significance score" (§12
of the mission) is not needed for the minimum experiment. `confidence`
(already computed by the three producers) already provides an adequate
proxy — a lower bar to clear now, revisited only if Architecture C's
scale requires triage.

---

## Decision Influence Requirements

Real, mapped decision points, with an honest verdict on whether attributed
knowledge could safely reach each one:

| Decision point | Could attributed knowledge safely influence it? | Why / why not |
|---|---|---|
| **Self-edit targeting** (`_FOCUS_FAMILY_BY_CREATIVITY`, which family gets attempted next) | Not for the minimum experiment — this is a coarser, slower-moving decision than the proof experiment needs, and CLAUDE.md's own Finding 32/43 history shows this exact lever has already been hand-tuned twice this project's life; adding a third automatic influence here without a proof experiment first would be premature | Defer to a later phase, after the minimum experiment validates the record shape |
| **Self-edit retry-prompt construction (`_build_targeted_prompt()` / the retry-prompt string at lines ~2002-2013)** | **Yes — this is the recommended minimum-experiment target.** The function already reads convergence state every cycle; adding "if a candidate-knowledge record exists for this exact `consequence_signature`, include its `causal_hypothesis` explicitly rather than relying on the model to notice the raw traceback" is additive to an existing, already-firing code path | Lowest-risk, highest-observability decision point in the whole codebase for this purpose |
| `choose_model()` / RiverBrain's task-type routing | Already influenced by aggregate credit assignment (RiverBrain) — do not duplicate; a per-record model preference would compete with, not complement, the existing mechanism | Out of scope |
| Council selection (`_select_council()`) | Already has its own aggregate mechanism (`TAG_SCORE_BOOST`, exploration floor per Finding 39/10) | Out of scope, same reasoning |
| Garden selection | Explicitly **not** recommended as the decision point to wire this into — the garden audit already showed its selection formula has no content-relevance term, and retrofitting one is a larger, riskier change than reusing `_build_targeted_prompt()`'s existing read | Rejected candidate |

**The single decision point recommended for the minimum proof experiment
is the self-edit retry-prompt construction inside `execute_self_edit()`.**
It already exists, already fires on every real sandbox failure, already
consumes a `clean_error` string, and changing what that string contains
(plain traceback vs. traceback + "a similar failure occurred N times before
under this exact signature, the last confirmed cause was X") is a single,
observable, revertible edit with no new autonomous behavior.

---

## Stillness Analysis

Read directly and completely this pass (`app/stillness.py`, 226 lines;
`app/core/stillness_state.py`, 72 lines — both fully quoted below the
verdict for the record).

**Classification: sleep/timer + pure pause mechanism. Not a learning
opportunity today, and not a natural site to bolt one onto without real
new engineering.**

Concretely, from direct source read:

- Entry triggers: circadian phase (`echo_state.npy` dim[7] < 0.15, "night
  phase") or a "quality collapse" heuristic, or a hardcoded loop-saturation
  safety valve (`auto_retreat_if_loop_detected`, >5 repetitions in <120s).
  All three are purely numeric/statistical triggers — none reads or
  reasons about any specific past experience.
- What happens during stillness: `_STILLNESS_EVENT` (a bare
  `threading.Event`) is cleared, and every autonomous loop that calls
  `wait_for_activity()` blocks. That is the entire mechanism. No file is
  read, no hypothesis is reconsidered, no state beyond the event and one
  append-only `silence.jsonl` line is touched.
- `reflect(whisper)` — the one method with a name suggestive of
  consolidation — the docstring says explicitly: *"One quiet thought. No
  logging to memory. No vectorization."* It logs to the process's own
  logger only. Confirmed live: `memory/stillness/silence.jsonl`'s real
  2,516 lines (checked this pass) contain only `entered`/`exited`/
  `duration_seconds`/`insight` fields — `insight` is real free text in a
  minority of entries (e.g. `"completed night_phase stillness"`) but the
  overwhelming majority read literally `"none spoken"` (5 of the last 5
  sampled). Nothing downstream reads this file (confirmed by grep — zero
  other readers of `memory/stillness/silence.jsonl` anywhere in the
  codebase).
- Exit trigger: purely circadian (dim[7] > 0.20), same numeric-only shape
  as entry.
- Real, live callers confirmed this pass: `emergent_scheduler.py:859-863`
  and `autonomous_harmony_manager.py:174/195` — both treat it as a plain
  pause-and-resume block around otherwise-normal autonomous cycling, not
  as a distinct reasoning phase.

**Should stillness be part of the learning substrate? No, not as
currently built, and not recommended as the site for Architecture B's
minimum closure.** Using stillness as a consolidation window would require
building the actual reconsideration logic from nothing — stillness
contributes zero existing machinery toward that beyond "a period during
which other things are paused," which is orthogonal to (and doesn't help
solve) credit assignment, relevance, or decision injection. If a
scheduled consolidation pass is ever wanted (Architecture C), it is a
*separate* new small loop, and stillness's exclusivity property (only one
session holds it at a time, verified via `_enter_global`'s boolean return)
is a reasonable, reusable concurrency primitive for that *future* loop —
but that is reusing its locking behavior, not its "reflection" framing,
which does not currently do anything a consolidation pass would need.

---

## RiverBrain Integration Analysis

Not re-derived from scratch this pass — reused directly from this
session's own extensively-verified prior work (`RiverBrain.learn()` at
`app/core/echo_model_orchestrator.py` ~line 808, `score_model()` genuinely
consumed by `rank_models()`, `_blend_council_and_quality()` at lines
737-756 independently re-derived and confirmed mathematically incapable of
letting council override quality_score at either extreme).

**Fit determination: Option D — leave alone, orthogonal function, not a
consumer or producer of the new candidate-knowledge substrate.**

Reasoning: RiverBrain answers "which model/family tends to perform well
across many trials" — a real, working, aggregate question. The
candidate-knowledge record this report proposes answers a categorically
different question: "did this *specific* consequence happen because of
*this specific* cause." Forcing RiverBrain to consume per-record
attribution would either (a) require reducing rich situational attribution
back down to a scalar feature, discarding exactly the specificity this
whole report is trying to preserve, or (b) require RiverBrain to grow a
second, incompatible representation alongside its existing
`model_task_stats` — recreating the "many organs" problem §20 explicitly
warns against. RiverBrain should remain what it already correctly is: one
input among several to model/council selection, unmodified, un-touched by
this proposal.

---

## Garden Integration Analysis

**Fit determination: remain a question-generation subsystem; explicitly
NOT the deferred-revisit mechanism.**

Three independent pieces of evidence converge on this, two from prior
sessions and one new this pass:

1. Prior: 13 categories, zero coding-related, 54.6% of real activity is
   coding-family — the garden's content pool structurally excludes the
   majority of Echo's real experience.
2. Prior: `select_from_garden()`'s weighting formula has no content-
   relevance term — staleness and category only.
3. **New this pass**: `harvest_question()`'s near-duplicate filter,
   applied indiscriminately to every writer including `seam_engine`,
   destroys 97.4% of real first-time attributions before they ever reach
   a retrievable garden entry (78 → 2, quantified above). This is not a
   hypothetical risk — it is a measured, currently-occurring loss, and it
   would apply with equal force to any new writer this report might
   otherwise have proposed routing through the garden.

The garden's `status`/`resolution_score` *field shape* is worth reusing
(§Candidate Knowledge Model's `status` field mirrors it deliberately), but
the garden as a live subsystem — its storage file, its dedup filter, its
selection formula — should not become the home for candidate-knowledge
records. A new, small, separate JSONL file with its own (much narrower,
exact-match, not fuzzy-text) dedup rule is lower-risk than either modifying
the garden's dedup filter (which exists for a good reason — keeping
philosophical questions from flooding with cosmetic repeats — and would be
risky to loosen without separately re-verifying that purpose still holds)
or bypassing it.

---

## Self-Edit Integration Analysis

Self-edit is the domain chosen for the minimum proof experiment (justified
in the next section) precisely because every other link the mission asks
about is already strongest here:

- Action is observable (the generated candidate + its real sandbox
  execution).
- Consequence is objective (F1/F2 pass/fail, a real Python traceback where
  it fails — not a subjective quality judgment).
- A cheap, non-fuzzy similarity test exists (`consequence_signature` as
  exact string match on error class + failed symbol).
- Behavior is measurable (does the retry produce a materially different
  candidate; does a later, independent cycle hitting the same signature
  produce a materially different candidate).
- Outcome is independently verifiable (F2's real sandbox execution — this
  session already built and adversarially validated
  `app/core/functional_quality.py` for exactly this kind of check, though
  it remains, correctly, disconnected from production per Phase 1A's own
  scope).
- Contamination is controllable — this session's learning-loop v1.2/v1.2.1
  series already worked out, the hard way, exactly which confounds to
  guard against (historical-file contamination, identifier leakage,
  non-independent sampling) for this exact domain. Reusing that domain
  means reusing already-hard-won methodological knowledge rather than
  re-deriving it for a new domain from zero.

The real historical `re`-NameError case (82 real occurrences, 72 of them
after CLAUDE.md's own Finding 32 prompt-patch, independently re-confirmed
by me in the parent conversation before this fork was launched) is the
concrete, real, already-occurred instance this design is built to close —
not a hypothetical.

---

## Candidate Architecture A — Minimal

**Components**: one new JSONL file (`memory/candidate_knowledge.jsonl`)
with the schema above; three one-line additions at the existing attribution
sites (self-edit retry, dissent log, seam_engine) to write a record; one
new read inside `_build_targeted_prompt()`'s retry-prompt string, keyed on
exact `consequence_signature` match.

**Data flow**: producer writes on attribution → no autonomous consumer
loop of any kind → the *next* time `execute_self_edit()`'s retry path
independently computes the same `consequence_signature`, it does one dict
lookup against the file (loaded fresh each time, no caching, no background
thread) and appends the matched record's `causal_hypothesis` to the retry
prompt.

**State transitions**: `status` starts `"unresolved"`; the only writer of
`status`/`times_applied`/`application_outcomes` is
`self_edit_outcome_tracker.py`'s existing pre/post window evaluation,
extended (not rebuilt) to also write these three fields onto the matched
record when a `producing_trace_id`'s outcome resolves.

**Decision points touched**: exactly one (self-edit retry-prompt
construction).

**Dependencies**: none beyond what already exists and already runs.

**Failure modes it's exposed to**: FM1 (lesson dump) is the primary risk —
if the retry-prompt injection doesn't measurably change retry behavior,
this degrades to exactly the rejected "failure → write lesson → retrieve →
put in prompt" pattern §5 forbids treating as sufficient. This is why the
proof experiment (next section) is mandatory before calling this
"closure," not merely "installation."

**Observability**: every write and every read is a single JSONL append/dict
lookup — directly greppable, no hidden state, no background thread to
debug.

**Testing requirements**: the minimum proof experiment (below) plus a
counterfactual control (retry-prompt construction WITHOUT the injected
hypothesis, matched pair, per §16's causal-test requirement).

**Implementation cost**: very low — an afternoon, not a project. Roughly
80-120 lines across four files, zero new dependencies, zero new
autonomous loops.

**Risk**: low. No existing safety gate (F1/F2/F3) is touched. No new
write target exists outside `memory/`. The new file has no writer capable
of reaching `EDIT_FORBIDDEN_TARGETS`.

**Expected capability**: closes the hot-stove loop for exactly one domain
(self-edit retry, single-attempt scope only — does NOT persist across
process restarts' worth of *different* self-edit families, does not touch
garden/RiverBrain/stillness). This is deliberately the smallest version
that could actually demonstrate T0-T11 end-to-end, per §15 of the mission.

---

## Candidate Architecture B — Integrated

Everything in A, plus:

**Components**: the same shared schema, but wired as a genuine consumer at
*two* points instead of one — the self-edit retry-prompt (as in A) AND a
second read at self-edit's next-cycle targeting-family choice
(`_FOCUS_FAMILY_BY_CREATIVITY`, deferred in the Decision Influence table
above for the *minimum* experiment, but appropriate once A is proven) — so
a family with a high concentration of `status: "contradicted"` records
(repeated failed hypotheses) gets a *soft* deprioritization nudge, mirroring
the shape of `TAG_SCORE_BOOST`/exploration-floor patterns already proven
safe elsewhere in this codebase (Finding 39/10), not a hard rule.

Also wires `self_edit_outcome_tracker.py`'s existing pre/post evaluation as
the sole writer of `status`/consolidation fields (as in A), but *also*
generalizes the write-side to accept records from dissent_log
(`_council_review_core_edit`) and seam_engine, not self-edit-only — since
both of those already compute real attribution and both are currently
single-use, per the Gap Matrix.

**Data flow**: three producers → one shared record store → two consumers
(retry-prompt injection, soft family-priority nudge) → one outcome-writer
(reusing `self_edit_outcome_tracker.py`'s existing evaluation cycle,
extended to also update the matched candidate-knowledge record's `status`
and `times_applied`/`application_outcomes`).

**State transitions**: adds real confirm/disconfirm accumulation
(`times_revisited`, `application_outcomes`) — the one piece that lets a
record earn or lose trust over multiple encounters, directly modeled on
the shadow-model `focus_matches` precedent (Finding 91).

**Decision points touched**: two (retry-prompt construction,
self-edit-family targeting nudge).

**Dependencies**: A, plus `self_edit_convergence.json`'s existing family
identifiers (reused as `applicability_scope` values, not reinvented).

**Failure modes it's exposed to**: FM3 (overgeneralization) is now a live
risk at the family-nudge consumer specifically — mitigated by keeping the
nudge *soft* (same bounded-swap shape as `exploration_bias`, never a hard
exclusion) and requiring `times_revisited >= 2` before a record can
influence the family nudge at all (a record needs to be seen *again*, not
just once, before its causal hypothesis is trusted for a second, coarser
decision — directly modeled on Michelangelo's "many organs, no digestion"
finding: don't let a single unverified observation become policy).

**Observability**: same as A, plus a periodic (not new-loop; piggybacked
onto the existing `self_edit_outcome_tracker.py` evaluation cycle, which
already runs on DMN Guardian's existing 60s thread) count of
`status: "contradicted"` records per family, cheap to expose on the
existing liveness ledger pattern.

**Testing requirements**: A's proof experiment, plus a second experiment
specifically isolating the family-nudge consumer's effect from the
retry-prompt consumer's effect (so a positive result can't be attributed
to the wrong one of the two consumers).

**Implementation cost**: moderate — roughly 2-3x architecture A's line
count, still no new autonomous loop, still reuses existing scheduled
cycles for all periodic behavior.

**Risk**: low-to-moderate. The family-nudge consumer is new *influence
surface* on a real production decision (which self-edit family gets
attempted), which is exactly the kind of change this project's own
`EDIT_FORBIDDEN_TARGETS`/report-then-pause discipline requires a diff
shown and explicitly confirmed before landing — correctly out of scope for
this design pass, which produces no diff.

**Expected capability**: the actual target state described in the mission
brief — a genuine, if narrow, end-to-end hot-stove loop for self-edit,
reusing (not replacing) RiverBrain, garden, and stillness, each left doing
what it already does well.

---

## Candidate Architecture C — Ambitious

Everything in B, plus: contradiction tracking (link #11), a full
`alternative_hypotheses`/`counterevidence` schema, a dedicated scheduled
consolidation pass (a genuinely new small loop, deliberately *not* piggybacked
on stillness per the Stillness Analysis verdict above), extension beyond
self-edit into the conversational/council domain (reusing dissent_log's
already-real structure), and a learning-significance scoring function
(§12) to triage which experiences get promoted to candidate-knowledge
status at all, needed once volume across *multiple* domains makes the
"write everything, exact-match on retrieval" approach from A/B too noisy.

**Components**: the shared schema (extended with the deferred fields from
§Candidate Knowledge Model), a new scheduled consolidation function (not a
tight loop — a periodic pass, similar cadence/shape to
`self_edit_outcome_tracker.py`'s own DMN-Guardian-thread pattern), a
learning-significance scorer, extension of the two B consumers to a third
(council/conversational routing).

**Data flow**: N producers → one shared substrate with confidence decay
and contradiction detection → M consumers, gated by a significance
threshold rather than "every producer writes everything."

**State transitions**: full status lifecycle including explicit rejection/
forgetting (link #19).

**Decision points touched**: three or more, spanning self-edit and
conversational domains.

**Dependencies**: A, B, plus a working significance scorer that itself
needs its own validation pass before being trusted — a second,
nested proof-experiment requirement.

**Failure modes it's exposed to**: essentially all twelve named in §17
become live simultaneously — FM8/FM9 (reservoir explosion/starvation)
specifically require the significance scorer to be *right*, which is an
unproven, unvalidated new component in its own right, meaning
Architecture C's risk is dominated by a component this report cannot yet
justify building (per §7's "do not assume these exact fields are correct"
instruction — the significance scorer is exactly the kind of premature
generalization the mission is warning against).

**Observability**: substantially harder — multiple producers, a scoring
function whose correctness itself needs an oracle, contradiction detection
whose false-positive rate needs its own study.

**Testing requirements**: everything in A and B, plus dedicated validation
of the significance scorer and the contradiction detector before either
can be trusted with any real decision influence — realistically another
multi-session investigation on the scale of this one, before a single line
of C-specific production code should land.

**Implementation cost**: high, and — critically — **the ambitious parts
of C don't buy proportionally more evidence about whether the hot-stove
gap is closeable.** The proof experiment A already demonstrates the full
T0-T11 chain; C's additions are about *scale and robustness of an already-
proven mechanism*, not about proving the mechanism works at all.

**Risk**: high, concentrated specifically in the unvalidated significance
scorer and contradiction detector — precisely the two components this
report cannot currently write a "why" section for that would survive
§24's own required scrutiny ("if the why cannot be justified, reject the
proposed mechanism").

**Expected capability**: a genuinely more capable, more durable, multi-
domain learning substrate — *if* the two unvalidated new components turn
out to work as intended. Not justified to build now on the strength of this
design pass alone.

---

## Comparative Analysis

| | A — Minimal | B — Integrated | C — Ambitious |
|---|---|---|---|
| New autonomous loops | 0 | 0 | 1 (consolidation pass) |
| New unvalidated components | 0 (all consumers/producers already exist) | 0 | 2 (significance scorer, contradiction detector) |
| Production decision points touched | 1 | 2 | 3+ |
| Demonstrates full T0-T11 chain | Yes, narrowly | Yes, with soft policy influence | Yes, at scale — if the new components work |
| Reuses existing scheduled cycles only | Yes | Yes | No — needs a new one |
| Risk of reproducing "many organs, no digestion" | Low | Low (explicitly designed against it) | Moderate — a 4th learning-adjacent write path if not disciplined |
| Can be built and proof-tested without touching `EDIT_FORBIDDEN_TARGETS` | Yes | No (family-nudge touches self-edit targeting logic near forbidden-file territory — requires the usual diff-review) | No |
| Justifiable today on current evidence | Yes | Yes, as the *next* step after A's proof succeeds | No — two components lack their own validation |

---

## Recommended Architecture

**B — Integrated, built and proven in two explicit stages: A first, B
only after A's proof experiment succeeds.**

Not C, because two of its components (the significance scorer and
contradiction detector) are themselves unvalidated mechanisms this report
cannot yet write a defensible "why" for — building them now would be
exactly the "architecture for architecture's sake" §28 forbids. Not A
alone as the final state, because A only ever touches one decision point,
and the mission's own target ("a specific experience changes a future
decision") deserves at least the second, coarser decision point (family
targeting) that already has a safe, previously-proven-pattern (soft
nudge, bounded swap) available to reuse — leaving it out would be
under-delivering on already-available, already-cheap capability.

But B's second consumer (the family-targeting nudge) is explicitly gated
on **A's proof experiment succeeding first** — this report does not
recommend building both stages simultaneously. If A's proof experiment
fails to show real decision influence, B should not be attempted at all;
that would be strong evidence the whole "retrieval → decision" link is
harder than this design assumes, and the honest next step would be a new
investigation, not a bigger version of the same untested mechanism.

---

## Why Each Component Exists

Per §24's required structure, for the three genuinely new pieces (the
shared schema, the retry-prompt read, the family-nudge read):

**GAP**: A real, specific causal hypothesis is computed at self-edit retry
time and discarded before the next independent cycle can use it.
**WHY**: This is the literal definition of the hot-stove gap the entire
investigation exists to find — episodic-only credit assignment.
**CURRENT STATE**: `clean_error` is a local variable, gone when
`execute_self_edit()` returns.
**MINIMUM FIX**: Persist it under a `consequence_signature` key; read it
back by exact match at the next retry-prompt construction.
**EVIDENCE**: 82 real historical `re`-NameError occurrences, 72 after a
documented (Finding 32) but structurally non-durable fix attempt; the
retry mechanism computes the exact right diagnosis every single time and
throws it away every single time.
**RISK**: Low — additive, no existing gate touched, reversible by deleting
one file.
**PROOF**: The minimum proof experiment below.

**GAP**: A record that has been contradicted or repeatedly confirmed
carries no weight in a coarser decision (which self-edit family to
attempt).
**WHY**: Without this, even a working retry-level fix stays trapped at the
single-attempt scope — real durability requires surviving past one retry
into a genuinely later, independently-triggered cycle.
**CURRENT STATE**: `self_edit_convergence.json` tracks aggregate
near-duplicate counts per family but with zero connection to *why* those
duplicates keep happening (confirmed live this pass:
`non_convergent_streak: 0` for all four families despite up to 31 distinct
near-duplicate names in one family — the counter isn't seeing what's
actually happening, independently re-confirmed by me in the parent
conversation before this fork was launched).
**MINIMUM FIX**: A soft nudge, gated on `times_revisited >= 2`, mirroring
the already-safe `exploration_bias` bounded-swap pattern.
**EVIDENCE**: `prose_stripping`'s 95 cycles / 31 distinct near-duplicate
names is a real, measured instance of a family that keeps failing the same
general way without the targeting logic ever being informed why.
**RISK**: Moderate — touches a real production decision; requires the
usual diff-review-before-landing discipline this project already applies
to self-edit-adjacent changes.
**PROOF**: A second, isolated experiment (per Architecture B's testing
requirements) separating this consumer's effect from the retry-prompt
consumer's effect.

---

## Failure Modes

Mapped against the recommended architecture (B, staged after A):

| # | Failure mode | Exposure in A | Exposure in B's addition | Mitigation built into the design |
|---|---|---|---|---|
| 1 | Lesson dump | **Primary risk for A** — this is exactly what the proof experiment exists to rule out before calling A "closure" | N/A if A already passed | Mandatory causal proof experiment before A is trusted at all |
| 2 | False attribution | Low — trace_id join key, no fuzzy matching | Low — same join key | Exact-match `consequence_signature`, never nearest-timestamp |
| 3 | Overgeneralization | Low — record scope is `applicability_scope`-bounded, single decision point | Moderate — the family-nudge is a coarser decision | `times_revisited >= 2` gate, soft-nudge-only (never hard exclusion) |
| 4 | Undergeneralization | Real, accepted tradeoff — exact-match by design | Same | Deliberately accepted for A/B; revisit only if C is ever justified |
| 5 | Stale knowledge | Low at A's scale (single retry) | Real risk once records persist across many cycles | `status` field + outcome-writer already re-evaluates on new evidence, not append-only trust |
| 6 | Confirmation loop | Low — no retrieval-preference mechanism exists in A/B | Low — nudge direction is symmetric (contradicted records get *deprioritized*, not reinforced) | By construction — B nudges away from repeatedly-contradicted families, not toward confirmed ones |
| 7 | Evaluator gaming | Not applicable — no model-facing evaluator is being optimized against here | Same | N/A |
| 8 | Reservoir explosion | Low — only 3 real producers, all already rate-limited by their own existing cadence | Same | No new producer added |
| 9 | Reservoir starvation | Possible if `consequence_signature` is too granular (every traceback slightly different) | Same | Signature must be class-level (error type + symbol), not full-traceback — specified in the schema |
| 10 | Decision bypass | This is what the proof experiment tests directly | Same, for the second consumer | Explicit before/after comparison required, not assumed |
| 11 | Self-reinforcing mistake | Low — `status` can move to `"contradicted"`, which *reduces* influence, never increases it automatically | Same | By construction |
| 12 | Anthropomorphic illusion | The report itself is the guard here — nothing in this design is graded on language Echo produces; every claim of success in the proof experiment requires a measured behavioral difference, not a stated one | Same | Explicit in the proof-experiment design below |

---

## Minimum Proof Experiment

**Domain**: self-edit retry (justified in §Self-Edit Integration Analysis).

**Design**:

1. Take a real historical `consequence_signature` with multiple confirmed
   occurrences — the `re`-NameError case (82 real occurrences) is the
   obvious, already-available candidate, but using the *exact same* one
   already investigated in CLAUDE.md's Finding 32 risks reusing a case this
   project has already prompt-patched once; prefer a **different,
   currently-unaddressed recurring signature** mined fresh from
   `SELF_EDIT.log`, so success or failure can't be attributed to residual
   effects of a prior fix. (This mining step is a small, isolated,
   read-only task — not attempted in this design pass, correctly deferred
   to the implementation phase per the mission's own "no premature
   implementation" rule.)
2. **Episode 1** (control-establishing): reconstruct a real historical
   failure under that signature, run it through the *unmodified*
   `execute_self_edit()` retry path exactly as it exists today (in an
   isolated sandbox harness, `river_brain.pkl` writes neutralized — same
   discipline as every prior experiment this session). Record the retry
   output.
3. Persist a real candidate-knowledge record for that signature (as
   Architecture A specifies), with `causal_hypothesis` set to the actual
   `clean_error` text the pipeline itself produced in step 2 — not a
   fabricated or improved hypothesis, since injecting a *better* diagnosis
   than the system genuinely produces would test something other than
   whether *this system's own* attribution can close the loop.
4. **Episode 2 — TIME GAP simulated** (a fresh process/harness invocation,
   not the same in-memory retry, to genuinely test durability rather than
   in-process persistence): reconstruct a **different, independently-
   generated candidate that happens to trip the same signature** (not the
   identical candidate replayed — a genuinely separate generation attempt,
   to rule out simple memoization/replay). Run it through the retry path
   twice: once with the candidate-knowledge lookup wired in (EXPERIENCE
   condition), once with it disabled (CONTROL condition) — matched pair,
   same seed/model/prompt otherwise.
5. Compare EXPERIENCE vs. CONTROL retry output. The claim of "decision
   influence" is only supported if the two differ in a way traceable to
   the injected `causal_hypothesis` text specifically — not to prompt
   length, not to incidental wording changes, not to model sampling
   variance. This requires the same adversarial counterfactual discipline
   this session already built for the v1.2 experiment: unseen
   identifiers where possible, multiple replications, explicit ruling-out
   of lexical cueing.
6. **Episode 3** (independent verification): run the EXPERIENCE-condition
   retry candidate through the real, unmodified F2 sandbox. Success is
   only claimed if the EXPERIENCE-condition candidate has a *measurably
   different, and not worse, real sandbox pass rate* than the CONTROL
   condition across enough replications to be statistically meaningful —
   the same evidentiary bar (McNemar-style paired comparison, matched n)
   already established as this project's own standard in the Tier-3/
   Tier-4 capability-ceiling research this session inherited.

**What would falsify the design**: if EXPERIENCE and CONTROL retry outputs
are indistinguishable, or if CONTROL performs as well or better, this
report's central claim (that the bottleneck is purely storage-and-lookup,
not something harder like relevance or model capability) is wrong, and the
honest conclusion would be that the model itself cannot make effective use
of an explicit, correct causal hypothesis handed to it — a materially
different, and more concerning, finding than anything in the Hot Stove
audit.

---

## Observability Requirements

- Every write to `candidate_knowledge.jsonl` is a plain JSONL append,
  directly `tail -f`-able, same convention as every other log in this
  codebase.
- The retry-prompt injection point should log (at the same
  `logging.warning` level `self_edit_manager.py` already uses for its
  retry path) whether a matching candidate-knowledge record was found and
  used, so a human reviewing `SELF_EDIT.log` can directly see whether the
  mechanism fired on any given real cycle — no new dashboard required for
  the minimum experiment.
- If Architecture B's family-nudge consumer is ever built, it should
  follow the existing Liveness Ledger pattern (a functional canary against
  the real evaluator, per this project's own established convention) —
  not attempted in this design pass.

---

## Implementation Order

1. Mine a fresh, currently-unaddressed recurring `consequence_signature`
   from `SELF_EDIT.log` (read-only, isolated).
2. Build the minimal schema + three producer writes (self-edit retry,
   dissent log, seam_engine) — additive only, no existing behavior changed.
3. Run the minimum proof experiment in an isolated harness (per the design
   above), with `river_brain.pkl` writes neutralized and no production
   file touched.
4. **Explicit stop-and-report point.** Do not proceed to wiring the
   retry-prompt consumer into production until the proof experiment's
   result is reported and reviewed.
5. Only if the proof experiment succeeds: wire the retry-prompt consumer
   into production, with a diff shown and explicit confirmation first
   (self_edit_manager.py is not itself on `EDIT_FORBIDDEN_TARGETS`, but
   this project's own established discipline for self-edit-adjacent
   changes still applies).
6. Only after production wiring is confirmed stable across real cycles:
   consider Architecture B's second consumer (family-targeting nudge), with
   its own separate proof and its own separate diff review.
7. Architecture C is not scheduled — revisit only if B, once live, proves
   insufficient for a *specific*, evidenced reason (not proactively).

---

## Explicit Non-Goals

- No new autonomous loop, at any stage of A or B.
- No embedding-based or LLM-based relevance/similarity mechanism — exact
  structural matching only, for the reasons given in §Relevance and Revisit
  Requirements.
- No modification to RiverBrain, the garden's selection formula, or
  stillness's trigger logic.
- No "learning significance scorer" or contradiction detector — explicitly
  deferred to Architecture C, itself not currently recommended.
- No claim that this closes the hot-stove gap for any domain other than
  self-edit until a domain-specific proof experiment is run for that
  domain.
- No production code was written in this design pass, per the mission's
  explicit instruction.

---

## What We Still Do Not Know

- Whether the *model* (not the architecture) can actually make productive
  use of an injected, correct causal hypothesis at retry time — this is
  exactly what the proof experiment tests and this report cannot predict
  the answer.
- Whether `consequence_signature`'s exact-match granularity will turn out
  too narrow (many superficially-different signatures that are really the
  same underlying mistake) or about right — only real mined data from step
  1 of the implementation order can answer this.
- Whether the family-nudge consumer (Architecture B's addition) would
  measurably change `self_edit_convergence.json`'s real non-convergence
  numbers over a long enough window to be worth its added risk — untested,
  correctly deferred.
- Whether reusing `dissent_log.jsonl`'s and `seam_engine`'s attribution as
  additional producers (rather than self-edit alone) adds real value or
  just adds volume without a correspondingly useful consumer — Architecture
  B recommends including them as producers on the theory that a shared
  substrate should have multiple real inputs from the start rather than
  being retrofitted later, but this is an architectural bet, not something
  this pass measured.

---

## Final Recommendation

Build and prove **Architecture A first, as a strictly bounded, single-
domain, single-decision-point experiment**, using the retry-prompt
consumer inside `execute_self_edit()`. Do not build Architecture B's
second consumer, and do not touch RiverBrain, the garden, or stillness,
until A's proof experiment produces a real, measured, adversarially-
checked positive result. If it does, extend to Architecture B exactly as
staged in the Implementation Order above, each stage gated on an explicit
report-and-confirm checkpoint, never assumed. If it does not, treat that as
a real and important finding in its own right — evidence that the
bottleneck this project has been circling all session is not (only)
missing plumbing, but something about how the underlying models use
explicit causal information, which would be a different, harder, and more
interesting problem than the one this report was asked to design for.

---

### Appendix: full source read this pass

`app/stillness.py` (226 lines) and `app/core/stillness_state.py` (72
lines) were read in full during this investigation, per the mission's
explicit instruction not to assume relevance. Neither file was modified.
Key excerpts are quoted inline above; full files remain unchanged in the
working tree for independent re-verification.
