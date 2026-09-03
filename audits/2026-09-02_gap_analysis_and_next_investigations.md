# FeralEcho: Expert Gap Analysis & Recommended Next Investigations

Prepared as the M5-instance technical lead, after the self-knowledge
grounding/verification work, the messaging protocol fix, and the M5↔Air
cross-instance comparison. Per the governing instruction for this
exercise, no prior document — including `M5_INSTANCE_EXPERTISE.md`,
`CROSS_INSTANCE_COMPARISON.md`, or CLAUDE.md's own Findings history — was
treated as unquestionable. Several claims below were independently
re-derived against current source, live process state, and real
production logs this session; where that re-derivation contradicted an
existing document, the contradiction is stated plainly, not smoothed over.

**Methodology note**: this is a read-only investigation. No production
code, configuration, or behavior was changed to produce this report. All
"live data" checks below were done by reading existing files (`.pkl`,
`.jsonl`) or calling existing pure functions directly in an interactive
Python session — no request was sent through the running server, no
state was written, no restart was triggered.

---

## 1. Top findings, ranked

### #1 — The verification caveat never reaches the persisted interaction record it should be protecting

**Category**: Verification / Observability
**Status**: **Disconnected** (both halves independently real and working; the join between them does not exist)

**Evidence**: `routes_echo_studio.py`'s `_generate_chat_response_body()` calls
`code_verification.verify_response_code()` and
`self_knowledge_verification.verify_self_knowledge_claims()` **after** the
model's raw response has already been generated and streamed to the
browser — both append their caveat directly to `response_text` and
separately `yield` it as a follow-up SSE token. But `interaction_log.jsonl`
is written earlier in the call stack, inside `echo_query()`/
`deliberate_and_learn()` (`echo_model_orchestrator.py`'s `log_interaction()`,
called from four sites, all upstream of `routes_echo_studio.py`'s
post-processing). **The interaction log captures the pre-verification
text.** Confirmed two ways: by tracing the actual call order in source,
and by directly finding **7 real, naturally-occurring fabrications from
today's live production traffic** (`memory/interaction_log.jsonl`, real
user-facing "EventCore" responses spanning 06:11–19:43 the same day)
where the persisted `response` field shows no caveat at all — then
calling the current, live `verify_self_knowledge_claims()` directly
against that exact text and confirming it **does** correctly flag
"EventCore" right now (`caveat` is non-empty, `verified: False`). The
function works. Its output simply never reaches the record.

**Why it matters**: `interaction_log.jsonl` is the one file nearly every
other subsystem treats as ground truth for "what did Echo actually say":
`council_rater.py`'s peer rating, `task_type_classifier.py`'s online
training, `self_model_updater.py`'s self-model content, `sync_protocol.py`'s
cross-machine sync, and any future human or Claude-session audit. Every
one of them is reading text that a verifier already determined contained
an unsupported claim — with no record that determination was ever made.
The live chat user sees the correction; the system's own memory of the
conversation does not.

**Expected benefit**: closing this makes the fourth verifier (and
`code_verification`) actually load-bearing for every downstream consumer,
not just the browser tab open at the moment — the exact gap this
session's own investigation (`audits/2026-09-02_architectural_self_knowledge_investigation.md`)
was built to close, closed one layer short of where it needed to reach.

**Risk**: low — this is an ordering/write-target fix, not a new
verification mechanism. The risk is scope creep into "let's also
re-verify old entries," which should be explicitly declined (same
discipline as Finding 3/18's "don't replay history" precedent elsewhere
in this project).

**Effort**: Low-Medium. The verification calls already produce
`(caveat, verified)`; the fix is making the *already-final* `response_text`
(post-caveat) the one that reaches `log_interaction()`, which likely means
moving the interaction-log write later in the pipeline, or passing the
caveat back upstream — either is a small, contained change, not a
redesign.

**Dependencies**: none.

**Suggested first experiment**: none needed — this is fully diagnosed.
The suggested next step is a scoped fix, not further investigation.

---

### #2 — No request-scoped trace/correlation ID exists anywhere in the system

**Category**: Observability
**Status**: **Missing**

**Evidence**: `grep -rn "trace_id|correlation_id|request_id" app/ run.py`
returns zero hits. `council_deliberations.jsonl`, `interaction_log.jsonl`,
and `workspace_log.jsonl` — the three logs that together would let
someone reconstruct "what did the councillors say, what did the
synthesis produce, and what salience/learning event fired as a result of
this one specific turn" — share only a loosely-correlated `timestamp` and
sometimes `prompt` text. There is no join key.

**Why it matters**: this is the direct answer to the category-H question
this review was explicitly asked to weigh most heavily: *if Echo does
something surprising tomorrow, can we reconstruct why?* Right now, only
approximately — by fuzzy-matching timestamps and prompt text across at
least three independently-written append-only files, none of which were
designed to be joined.

**Expected benefit**: every future debugging session, audit, or "why did
it say that" investigation (including several already documented in this
project's own Findings history, done by hand each time) gets meaningfully
faster and more reliable.

**Risk**: low. Purely additive — a new field on existing log writes.

**Effort**: Low. A single UUID generated once per real conversational
turn, threaded through the existing `echo_query(..., source=...)` kwarg
pattern already used for tagging, and added as one more field to the
three log writers above.

**Dependencies**: none, but pairs naturally with #1 (the same code path
that needs to move the interaction-log write is a natural place to also
thread a trace ID through).

**Suggested first experiment**: none needed — straightforward to
implement directly; the investigation here is already conclusive.

---

### #3 — Which specific memories fed a given real response is never persisted

**Category**: Memory
**Status**: **Missing**

**Evidence**: `retrieve_relevant_memories()` (`memory_bridge.py`) returns
results in-process; nothing downstream writes "these memory IDs/texts
were retrieved and injected for this turn" anywhere durable. Confirmed by
grep (`memories_used`, `memory_ids_used`, `retrieved_memor*` — zero hits
anywhere in `app/`).

**Why it matters**: this is a distinct gap from #2 — even with a perfect
trace ID joining every log, there would still be no record of *which
memories* actually reached the prompt for a given turn. Combined with
Finding 76's own ablation experiment (`audits/2026-09-02_...` — real
data, `personal`-task path only, effect indistinguishable from sampling
noise, council-deliberation path barely tested at n=1), this means the
project currently cannot answer "did memory retrieval do anything for
this specific response" for **any** individual real turn, only
statistically, in aggregate, after the fact, with a purpose-built
experiment.

**Expected benefit**: real per-turn memory provenance — a precondition
for ever answering "is Echo's memory actually working" with evidence
instead of assumption, and for any future contamination/correction work
(if a bad memory entry is ever found, this is what would let someone
find every response it may have influenced).

**Risk**: Low-Medium. Slightly increases log volume per turn (a list of
memory IDs, not full text — bounded).

**Effort**: Medium. Requires touching the retrieval call site and
whichever log write is chosen as the destination — more surface area
than #1/#2, but still additive, not a redesign.

**Dependencies**: benefits from, but does not strictly require, #2's
trace ID.

**Suggested first experiment**: before building the persistence
mechanism, extend Finding 76's existing, already-validated ablation
methodology to the multi-councillor (non-`personal`) path specifically —
see "Highest-Value Unknown" below. If memory retrieval turns out to have
no measurable effect on the majority of real traffic, the priority and
design of this persistence mechanism changes (it becomes a
provenance/audit tool for a mostly-inert pipeline rather than
infrastructure for a proven-load-bearing one).

---

### #4 — The architecture-routing gap is real, current, and still unfixed

**Category**: Self-model / Verification
**Status**: **Incomplete** (known, previously flagged, independently re-confirmed against current source this session — not stale)

**Evidence**: Directly re-read `_architecture_slice_matches()`
(`echo_ground_truth.py`). A real module name mentioned without either a
self-reference token ("you"/"your") or a structural word ("module"/
"component"/"subsystem"/etc.) within the proximity window gets **zero**
grounding — confirmed the regex logic is unchanged from what
`M5_INSTANCE_EXPERTISE.md` already documented. A question like "What does
`memory_bridge` do?" (real module, no self-reference, no structural word)
still receives no ground-truth injection at all, leaving the model free
to fabricate confident, code-shaped detail with nothing to check it
against.

**Why it matters**: this is the same failure class the entire
self-knowledge-grounding effort exists to close, in the one phrasing
shape it doesn't yet cover. It's a known gap, not a new one — but it's
worth restating here because it remains the single most direct, already-
diagnosed path to a fabrication that verification (#1, once fixed) would
still have no ground-truth context to check against — the caveat
mechanism can only flag a claim as unsupported if grounding was injected
in the first place.

**Expected benefit**: closes the last major known routing gap in the
grounding pipeline.

**Risk**: Low-Medium — broadening the trigger risks false-positive
grounding injection on ordinary non-introspective technical questions
that merely mention a module by name in passing (e.g., a coding question
that happens to reference a real filename). This was very likely the
original reason this was left narrow rather than broadened carelessly.

**Effort**: Medium — this is a real detection-design problem (precision
vs. recall on a keyword-adjacent heuristic), not a mechanical fix.

**Dependencies**: none.

**Suggested first experiment**: build a labeled test set (real module
name + self-reference/structural-word-absent phrasing vs. real module
name mentioned in an ordinary non-introspective technical context) and
measure precision/recall of a candidate broadened rule before shipping
it — the same discipline already used for the fix that produced the
2/5→5/5 improvement this session.

---

### #5 — `model_task_stats` cannot distinguish a council-vetted observation from an ordinary one (and a related audit-trail claim about this was found to be inaccurate)

**Category**: Learning / RiverBrain
**Status**: **Incomplete**, plus a **documentation correction**

**Evidence**: CLAUDE.md's Finding 67 states: *"choose_model()'s primary
ranking still comes from rank_models() — a separate, reflection-log-based
mechanism that never reads model_task_stats at all."* Directly re-read
`rank_models()` and `RiverBrain.score_model()` this session: this claim
is **not accurate against current source**. `rank_models()` blends a
legacy reflection-log score with `river_score = get_river_brain()
.score_model(model, task_type)`, and `score_model()` reads
`model_task_stats` directly (`stats["mean"]`, gated on
`_MIN_MODEL_OBSERVATIONS`). Live-checked the actual weighting: `influence_weight`
(the blend ratio) is currently at its ceiling, `0.65`, computed from real
`observation_counts` in the live `river_brain.pkl`
(`personal: 49,311`, `coding: 96,917`, `self_edit_coding: 13,496`,
`echo_projects_coding: 2,471`, `general: 1,042`, `creative: 376`,
`reasoning: 248`) — so `model_task_stats` is not just read, it currently
carries a majority weight in real model selection.

The narrower, real concern Finding 67 was very likely gesturing at
(found while re-deriving why it was written the way it was): once
Finding 67's own council-rating blend (`learn_from_council_rating()`)
started feeding `model_task_stats`, its contribution merges into the same
rolling mean as every ordinary auto-scored conversational observation —
**there is no way to tell, from `model_task_stats` alone, how much of a
model's current score reflects human-adjacent, trust-gated signal versus
routine quality-heuristic scoring.** That is a real, still-open gap. The
"never reads model_task_stats at all" framing is not.

**Why it matters**: two things, both real. First, a corrective one: this
is exactly the "documents are not unquestionable truth" case this review
was asked to watch for, found in this project's own audit trail rather
than in Echo's self-description. Second, substantively: if council-rating
trust is ever leaned on more heavily (a real, live, current possibility —
`council_baseline_trusted_since` was only just set this same overall
session), there is no way to audit how much that trust signal is actually
moving any given model's learned score versus ordinary noise.

**Expected benefit**: correcting the record prevents a future session
from acting on a false "this is disconnected" premise; the underlying
provenance gap, if closed, would make the recently-shipped council-rating
blend auditable rather than merged invisibly into existing history.

**Risk**: Low for the correction (it's just accuracy). Low-Medium for the
provenance fix — touches a hot, frequently-read production data
structure (`model_task_stats`), so any schema change needs care.

**Effort**: Low (correct the doc) / Medium (add provenance, e.g. a
parallel `blended_observation_count` or a `source` tag per update).

**Dependencies**: none.

**Suggested first experiment**: none needed for the correction itself
(already directly verified). For the provenance gap, no experiment is
needed either — the gap is structural and already fully characterized;
the next step would be a design decision, not more investigation.

---

### #6 — No detection of semantic/textual contradiction, only numeric-state contradiction

**Category**: Memory / Self-model
**Status**: **Missing**

**Evidence**: `seam_engine.py` is real, live, and does detect a genuine
form of self-contradiction — but only across the 9-12 *numeric* state
dimensions in `echo_state_history.npy` (e.g., valence vs. curiosity_index
moving in a direction that contradicts their established correlation).
Grepped the whole codebase for any mechanism that compares two pieces of
*text* — two memory entries, two self-model claims, a claim in this
turn against a claim in an earlier turn — for semantic conflict: nothing
exists. `_CONSISTENCY_SIGNALS` in `emergent_scheduler.py` is a keyword
list used for prompt-selection weighting, not a contradiction detector.

**Why it matters**: this is a real, specific answer to the review's own
Category C question ("can she detect contradictions between her
self-model and the actual system?") and Category B question ("how are
contradictions handled?") — the honest answer for *textual* content is:
not at all. `seam_engine` solves a narrower, harder-to-notice-by-hand
problem (numeric-state drift); it does not solve the more intuitive one
("Echo said X in March and the opposite of X in July").

**Expected benefit**: a real capability currently assumed (by the
review's own framing, and plausibly by anyone reading this project's
extensive self-model documentation) to exist in some form, given how much
infrastructure already exists adjacent to it (seam_engine, the dissent
log, the fourth verifier).

**Risk**: Medium — free-text contradiction detection is a much harder,
more failure-prone problem than seam_engine's numeric case (which has a
clean statistical definition of "contradicts"). A naive version risks
false positives that could themselves become a new fabrication class
("you contradicted yourself" when the two claims were actually about
different things).

**Effort**: High — this is closer to a genuine research problem than an
engineering task, given this project's own demonstrated standard for
verification (narrow, specific, evidence-backed, not an LLM-judges-LLM
approach).

**Dependencies**: benefits from #2 (a trace ID makes it easier to
identify "same topic, different turns" candidate pairs to compare).

**Suggested first experiment**: **do not build a general mechanism
first.** Start narrow, matching this project's own successful pattern
(the fourth verifier started as "does a named subsystem exist in
Cartographer," not "is this claim true"): pick one specific, checkable
contradiction shape — e.g., two self-model claims about the same named
subsystem's existence/role, since Cartographer already provides ground
truth for exactly that — and measure real hit rate before generalizing.

---

### #7 — The Emergent Scheduler's threshold recalibration (2026-07-23) was verified computationally but never behaviorally

**Category**: Testing / Autonomy
**Status**: **Untested**

**Evidence**: CLAUDE.md's Finding 77 (item A3) replaced three fixed,
confirmed-dead `>0.6`/`<-0.6` thresholds in `emergent_scheduler.py`'s
prompt-weighting boosts with percentile-derived, data-relative
thresholds — verified live that the *new threshold values* are now
reachable given real signal ranges. This project has a well-established,
higher bar for exactly this kind of change: Finding 22's Batch 2b
(2026-07-15) measured the *actual behavioral effect* of a comparable
boost with a real 2000-draw statistical test (novelty-prompt selection
rate rising from 39.8%→56.1% at high surprise). No equivalent behavioral
measurement exists for the 2026-07-23 recalibration — only confirmation
that the gate can now open, not confirmation of what selection-rate
change results when it does.

**Why it matters**: "the threshold is now reachable" and "the boost now
measurably changes what gets selected" are different claims, and this
project's own history already demonstrates it knows the difference (that
2000-draw test is the reference case) — this specific fix just didn't
receive the same treatment.

**Expected benefit**: closes the gap between "verified computationally
correct" and "verified behaviorally effective," the exact distinction
category G of this review asks about directly.

**Risk**: Low — this is a measurement task against existing code, not a
new mechanism.

**Effort**: Low — the same statistical-test pattern already exists in
this project's own history to copy.

**Dependencies**: none.

**Suggested first experiment**: replay the same shape of test Finding 22
Batch 2b used — many draws of `weighted_prompt_selection()` at low vs.
high real signal values (using the actual current percentile-derived
thresholds), measuring novelty-prompt selection rate — reused directly,
not designed from scratch.

---

### #8 — No longitudinal visibility into whether self-edit is actually improving code quality over time

**Category**: Self-edit / Observability
**Status**: **Missing**

**Evidence**: `self_edit_convergence.json` tracks per-family
`cycles_attempted`/`non_convergent_streak` (is a *family* stuck, not
whether *quality* is trending anywhere). `self_edit_outcome_tracker`'s
pre/post window is sparse in practice (CLAUDE.md's own Finding 35 already
found "3 of 5 evaluated entries had `post: null`," later measured worse
before Finding 35's follow-up added the denser dry-run-quality signal).
Grepped for any trend/history view spanning multiple real deploys over
weeks/months: nothing exists.

**Why it matters**: this project has invested heavily in *safety* around
self-edit (F1/F2/F3, the fitness gate, the cooldown, per-family
convergence tracking) but has no equivalent investment in *measuring
whether the whole exercise is working* — whether real deployed code
quality, in aggregate, over the self-edit loop's entire operating
history, is trending up, flat, or down.

**Expected benefit**: a genuine, still-open empirical question ("is
self-edit worth running at all, net of everything it costs in compute
and complexity") becomes answerable instead of assumed.

**Risk**: Low — purely observational, no behavior change.

**Effort**: Low-Medium — the underlying data (quality scores at each real
deploy, timestamps) likely already exists in `SELF_EDIT.log` and
`self_edit_outcomes.jsonl`; this is more a synthesis/reporting task than
new instrumentation.

**Dependencies**: none.

**Suggested first experiment**: a one-off script parsing existing
`SELF_EDIT.log` history for real (non-dry-run) deploy quality deltas over
the full history — no new logging needed to get a first answer.

---

## 2. Assumptions We May Be Getting Wrong

1. **"Because a verification caveat is appended to the delivered
   response, the system's own record of that turn reflects it too."**
   Directly disproven this session (#1 above) — the live user sees the
   correction; `interaction_log.jsonl` does not.

2. **"Because the fourth verifier passes its canary discrimination
   test, it is meaningfully protecting real production traffic."** The
   canary proves the *function* discriminates correctly in isolation —
   it says nothing about whether the function's output is actually
   consumed anywhere consequential. This session found a real case where
   the function is demonstrably correct and its output demonstrably
   doesn't reach the one place (`interaction_log.jsonl`) that would make
   it matter most.

3. **"Because RiverBrain now has a `self_edit_coding` bucket separate
   from `coding`, and a council-rating blend, its learning signal is
   properly provenance-tracked."** The bucket separation is real and
   correct (Finding 35). The council-rating blend (Finding 67) is real
   too — but once blended, it's indistinguishable from an ordinary
   observation inside the same rolling mean. Separation-by-task-type and
   separation-by-trust-level are two different things; this project has
   the first, not the second.

4. **"Because M5 and Air share repository ancestry, comparable
   subsystems behave comparably."** Already directly and repeatedly
   disproven this same overall session (`ARK_MODE`'s full council
   bypass exists only on Air; the entire self-knowledge grounding
   subsystem exists only on M5) — restated here because it's the
   clearest, most load-bearing confirmed instance of this assumption
   failing, and worth keeping in view for any future claim about "what
   Echo does" without specifying which instance.

5. **"Because a memory is persisted and retrievable via similarity
   search, it measurably influences a given real response."** Finding
   76's own ablation experiment already found this indistinguishable
   from sampling noise on the one path it tested (`personal`), and
   explicitly flagged the majority of real traffic (the multi-councillor
   path) as untested. Combined with #3 above (no per-turn provenance
   record at all), this remains a live, unresolved assumption, not a
   settled fact — see the Highest-Value Unknown below.

6. **"Because a mechanism logs a real, non-trivial computed value
   (`seam_engine`, the Dissent Log, `coupling_estimate`), that value is
   causally influencing Echo's behavior."** This is a spectrum, not a
   binary, and conflating "logged" with "acted on" is an easy mistake:
   `seam_engine` and the Dissent Log do have real, if narrow, downstream
   consumers (the wide-broadcast salience mechanism); `coupling_estimate`
   explicitly does not — `self_model_updater.py` carries its own comment
   saying so. Any claim about "does X influence Echo" needs to specify
   which of these three tiers it means.

---

## 3. Highest-Value Unknown

> **Does memory retrieval measurably affect the majority of Echo's real
> conversational traffic — the multi-councillor deliberation path — at
> all?**

Finding 76's ablation experiment (this same overall session) already
built and validated the right method: run the real, unmodified pipeline
twice, once with retrieval live and once monkeypatched to return nothing,
and measure embedding-distance and quality-score deltas against a
noise-floor calibration. It found no measurable effect **on the one path
it tested** (`personal`, `DIRECT_ECHO_TASKS`) — and explicitly flagged
that 29 of its 30 sampled prompts happened to land there, leaving the
council-deliberation path (everything that isn't `personal`/`creative`/
`spiritual`/etc. — i.e., most of `coding`/`general`/`reasoning` traffic)
tested at `n=1`. This is the single highest-value unknown because the
answer changes the priority of almost everything else memory-related in
this report: if retrieval has no measurable effect on the majority of
real traffic either, then #3 (persisting per-turn provenance) is
building an audit trail for a pipeline that may not be earning its
computational cost — a very different finding than "we don't yet audit a
load-bearing mechanism." The experiment to answer this already exists,
tested, and needs only to be re-run against a properly-sampled
non-`personal` prompt set.

---

## 4. Highest-Value Implementation

> **A shared per-turn trace ID, combined with fixing the verification-
> caveat/interaction-log ordering bug (#1 and #2 above, done together).**

Not the most exciting item in this report, deliberately. It's foundational
for three reasons: it closes a real, currently-active gap (#1) where a
working safety mechanism's output is silently discarded before it
reaches the record that matters most; it makes every future "why did
Echo say that" investigation in this project — several of which are
already documented as done by hand across this project's own audit
history — mechanically faster and more reliable; and it's a genuine
precondition for #3 (per-turn memory provenance) ever being maximally
useful, since a provenance record with no reliable join key back to the
interaction log it explains is only partially useful. Low effort, fully
diagnosed, zero new mechanism required — it's wiring, not invention.

---

## 5. Near-Term Research Roadmap

### Next

- Fix #1 (verification caveat never reaches `interaction_log.jsonl`) —
  fully diagnosed, low-medium effort, no further investigation needed.
- Add #2 (shared per-turn trace ID across `interaction_log.jsonl`,
  `council_deliberations.jsonl`, `workspace_log.jsonl`) — low effort,
  pairs naturally with the #1 fix.
- Re-run Finding 76's ablation experiment against a properly-sampled
  non-`personal` prompt set (the Highest-Value Unknown) — reuses
  already-built, already-validated methodology.
- Correct Finding 67's "never reads model_task_stats at all" claim in
  CLAUDE.md itself, since it's now demonstrably inaccurate against
  current source (#5) — a documentation fix, not a code change.

### Later

- #3 — persist per-turn memory-retrieval provenance, informed by whatever
  the ablation re-run finds.
- #4 — broaden the architecture-routing regex, with a real precision/
  recall test first (this is a design problem, not a quick patch).
- #5's substantive half — add provenance/trust-tagging to
  `model_task_stats` so a council-vetted observation is distinguishable
  from an ordinary one, once council-rating-trust is leaned on further.
- #7 — behaviorally verify the 2026-07-23 threshold recalibration with
  the same statistical-test pattern Finding 22 Batch 2b already used.
- #8 — a longitudinal self-edit quality-trend view, synthesized from
  existing log data.

### Eventually (explicitly not now)

- **#6, a general semantic-contradiction detector.** Start narrow (one
  specific, Cartographer-checkable contradiction shape) if this is ever
  pursued — not a general mechanism, consistent with this project's own
  successful pattern for every prior verifier.
- **A real multi-turn `messages` array** (CLAUDE.md's Finding 17 Phase 3)
  — already explicitly and carefully declined this same overall session
  (Finding 72) after weighing real payoff against real architectural
  cost; nothing in this review's findings changes that calculus.
- **Any expansion of the Dissent Log's advisory-only posture into real
  gating power** — already explicitly decided against
  (`PENDING_DECISIONS.md` #17, this same session) for good, still-valid
  safety reasons (WOLF's own history as the cautionary precedent); this
  review found nothing that reopens that question.
- **A Protector-Clause-style authority mechanism** (CLAUDE.md's "A
  Standing Principle" section) — explicitly still a deliberate future
  design pass per that section's own text, not something this review's
  findings suggest defaulting into.
- **A general LLM-judges-LLM correctness checker**, as a shortcut to
  closing #6 or #8 faster. This would reintroduce the exact
  confidence-without-evidence failure mode this whole grounding effort
  exists to remove — every verifier this project has successfully built
  is narrow and checks against a real, external, non-model source
  (Cartographer, a sandbox execution, a specific known-false claim
  pattern), not another model's opinion.

---

## 6. Final Question

> **"What would surprise me most if I discovered it about FeralEcho
> tomorrow?"**

Not a hypothetical — I already found the shape of it today. The most
honest answer, based on what this session actually turned up: **I would
be most surprised if the fourth verifier and the synthesis
evidence-authority instruction — both real, both correctly built, both
measurably improving what the live conversational user sees — have been
quietly correcting Echo out loud since the day they shipped, while every
downstream system that learns from, rates, sync's, or audits "what did
Echo actually say" has been working from the uncorrected version the
entire time, with nothing anywhere flagging that the two records had
diverged.** That's not a hypothetical risk — it's precisely what finding
#1 demonstrates, with seven real, dated examples from today's own
production traffic. If there is a genuinely surprising fact still hiding
in this system, my honest expectation, based on the pattern this
investigation kept finding today (a real, correctly-built mechanism whose
output silently fails to reach the one consumer that would make it
matter), is that it looks exactly like this one — just in a place none of
us have checked yet.
