# Find Echo's Missing "Stomach" — Latent Learning Reservoir Forensic Audit

Read-only. No production code modified, no `run.py`/watchdog started, no RiverBrain mutation, no new
reservoir built. `memory/river_brain.pkl` sha256 and git HEAD confirmed unchanged at the end (see §12).

---

## 1. Executive Verdict

**MANY ORGANS / NO DIGESTION.**

FeralEcho has an unusually large number of real, live, individually-functioning subsystems that each
retain *something* — memory, ratings, self-edit outcomes, seam detections, curiosity questions, council
opinions, convergence trackers. None of them, individually or in combination, implements the specific
capability the "stomach" hypothesis asks about: **taking an experience that was NOT resolved today and
making it causally available to a DIFFERENT, later decision because that later situation is relevant to
it.** Every mechanism checked either (a) never revisits its own stored content at all, or (b) revisits
via pure staleness/novelty weighting with no relevance-matching to what's currently happening. The
closest thing to true revisitation — the curiosity garden's question selection — is a weighted lottery
over *all* active questions, not a targeted "this new information makes that old question relevant now"
trigger. This is a real, precise, previously-uncharacterized-this-way finding, not a repeat of any prior
pass tonight.

---

## 2. The Learning Reservoir Liveness Ledger

| Mechanism | What enters it? | What is retained? | Where stored? | How retrieved? | Retrieval trigger | Who consumes it? | Can it affect a decision? | Can it affect future behavior? | Evidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Memory / FAISS (`memory_bridge.py`) | Every real conversation turn, autonomous reflection | Embedded text + metadata | `memory/memory_meta.json` + `faiss.index` | Top-k cosine similarity | Every real prompt construction | `_build_full_prompt()` → injected into system context | Yes, mechanically (Level 3) | **Unresolved** — Finding 76's own real ablation experiment (this session) found no measurable behavioral effect distinguishable from noise on the personal-task path (Level 4 test, null result) | `[inherited: Finding 76]`, re-confirmed in scope here | **LIVE BUT NON-CONSEQUENTIAL** (on the one path actually tested) |
| Self-edit retry diagnosis/correction | A real sandbox failure + its retry's fix | The corrected code only, inside that one attempt | Nowhere beyond the single `execute_self_edit()` call frame | N/A | N/A | Nothing — `_build_targeted_prompt()` confirmed, this pass, to contain zero references to `reflection_shard`/`SELF_EDIT.log`/`self_edit_outcome_tracker` | No | No | Direct grep, this pass (§ below) | **DEAD** — episode-local, never persists past the retry that produced it |
| Convergence tracker (`self_edit_convergence.json`) | Function-name novelty per family per cycle | `non_convergent_streak`, `all_names_seen` | JSON file | Read once per cycle by `_build_targeted_prompt()` | Every self-edit cycle | The targeting prompt, in principle | Yes, in principle | **No, in practice** — `[inherited: Michelangelo IV]` `non_convergent_streak` sits at 0 for both `prose_stripping` (95 cycles, 32 distinct names) and `response_shortening` (58 cycles, 33 distinct names) | `[inherited]`, re-confirmed | **LIVE BUT NON-CONSEQUENTIAL** — real state, real read, corrective almost never fires because it compares count not identity |
| RiverBrain `model_task_stats` | Every real conversational/self-edit response, scored by AST heuristic | Rolling per-(model,task) mean | `river_brain.pkl` | `score_model()` | Every real model selection | `rank_models()`/`_select_council()` | **Yes** | **Yes** | `[inherited: Phase 0/1.5]`, direct source | **LIVE CONSEQUENTIAL** — the one clear exception, closes on a weak proxy (r=0.206, not significant) |
| RiverBrain `accuracy_trackers` | Every `.learn()` call | Rolling accuracy stat | `river_brain.pkl` | `predict_one()` inside `.learn()` itself | Every `.learn()` call | Itself, and `self_model.json`'s passive display field | No | No | `[inherited: Phase 1.5]`, direct source | **LIVE BUT NON-CONSEQUENTIAL** |
| `learn_from_sandbox_outcome()` / `learn_from_rating()` | Real sandbox pass/fail; real human 1-5 ratings | Classifier/scaler state only | `river_brain.pkl` | Never (no reader of the classifier's predictions outside `.learn()` itself) | N/A | Nobody | No | No | `[inherited: Phase 1.5]`, direct source | **DEAD** — ground-truth signal computed, persisted, never read by a decision |
| Council rating | Peer/human ratings of real responses | `council_ratings.jsonl`; blended into `model_task_stats` for conversational tasks | JSONL + `river_brain.pkl` | `_blend_council_and_quality()` | Every trusted council rating | `model_task_stats` (for conversational tasks only) | Yes, partially | Yes, partially, **except** at score extremes | `[inherited: Michelangelo III]` — 73/73 real disagreement cases, algebraically provable at `quality_score∈{0,4}` | **LIVE BUT STRUCTURALLY LIMITED** |
| `seam_engine` | Statistical contradictions between 9 state dims + 3 salience components | Real detection log; occasionally a garden question | `seam_log.jsonl`; `data/question_garden.jsonl` | `harvest_question()` on first-ever detections | Every emergent-loop cycle | The garden's own selection lottery (see below) | Rarely (2/78) | Almost never (1/78 ever asked) | `[inherited: Michelangelo III]` | **LOG-ONLY**, with a thin, mostly-blocked path to consequence |
| Curiosity garden (`garden_manager.py`) | Questions from curiosity engine, dream cycle, `seam_engine`, dissent | Full entry: status, `resolution_score`, `last_asked`, `times_asked`, category, optional `investigation_plan` | `data/question_garden.jsonl` | `select_from_garden()` — **direct source read this pass**: pure weighted lottery over ALL active entries, weighted by category balance, never-asked bonus, staleness (age since `last_asked`), inverse resolution score, human-source bonus, incomplete-plan bonus | Every autonomous cycle that wants a topic | Emergent scheduler, dream cycle, self-model reflection | Yes, mechanically | Yes, but **relevance-blind** — see §6 | Direct source, this pass | **LIVE BUT MECHANISM IS "RANDOM RECALL," NOT "RELEVANT RECALL"** |
| `apply_to_code` | Every real self-edit deploy transformation | Transform result, logged | `apply_to_code_invocations.jsonl` | Only by the trusted-observer logger itself | N/A (no consumer reads this to decide anything) | Nobody, decision-wise | No | No — `[inherited: this session's own earlier work]`: 6 real weeks of activity, 62% "success," zero correlation with real self-edit quality delta | `[inherited]` | **DEAD**, despite substantial real historical volume |
| Dissent Log | A real, split council review on a protected-file edit proposal | Full entry, deliberately including unanimous cases | `dissent_log.jsonl` | Nothing reads it back | N/A | Nobody | No | No | `[inherited: Michelangelo II]` — exactly 1 entry, ever | **DEAD** (by design, per Finding 9's own explicit non-wiring — not a bug, but not a stomach either) |
| Shadow model | Reflection-derived keyword guesses about weak task type | Guess + real outcome comparison | `shadow_self_model.json`/`shadow_accuracy.jsonl` | `get_weak_task_type()`'s fallback path only, post-Finding-91 | Self-edit targeting | `perform_self_edit()`, last resort only | Rarely | Yes, but the one case of this whole ledger where the *consequence* was to stop trusting it | `[inherited]` | **LIVE, CONSEQUENTIAL, TERMINATING** — see §7 |
| `council_deliberations.jsonl` | Every real per-councillor raw opinion pre-synthesis | Full raw text, per model, per real deliberation | JSONL, 5,110+ real lines confirmed present this session | Nothing — grepped this pass, zero readers outside the logger itself | N/A | Nobody | No | No | Direct file presence + zero-consumer grep, this pass | **LOG-ONLY — a large, entirely unmined hidden reservoir** (see §11) |
| `retrieval_provenance.jsonl` | Which memories were candidates vs. actually injected, per real request | Hashes only, reference-only by design (per Finding 86) | JSONL | Nothing reads it back for a decision | N/A | Nobody (exists for audit/trace purposes only, per its own stated design) | No | No | `[inherited: Finding 86]` | **LOG-ONLY, by explicit design** |
| `self_edit_outcomes.jsonl` | Real pre/post quality deltas for real deploys | Full pre/post/delta per deploy | JSONL | Read by `SelfModelUpdater.get_weak_task_type()` in aggregate (weak-task detection) | Every self-edit cycle | `perform_self_edit()`'s primary targeting signal | Yes | Yes, but only "which family to target," never "what specifically to do differently" | `[inherited]` | **LIVE, CONSEQUENTIAL, BUT COARSE** — targets a family, carries no content-level lesson forward |

---

## 3. Existing Causal Chains (real, Level 4+)

Only two chains in the whole ledger reach a real, observed behavioral consequence:

1. **RiverBrain `model_task_stats`**: real response → AST-heuristic score → rolling mean update →
   next `rank_models()`/`_select_council()` call reads the updated mean → different model is (or isn't)
   selected. Fully closed, mechanically. Weak proxy (§9's counter-evidence).
2. **Shadow model termination**: real historical predictions → measured against real outcomes (16.1%
   accuracy, below the real 58.8% majority-class floor) → `perform_self_edit()`'s arbitration order was
   changed (Finding 91) to check it last, not first. A real behavioral change, caused by a real
   measurement — but a *subtraction* (stop trusting X), not a case of unresolved experience later
   becoming a *positive* input to a different decision.

No other row in §2 reaches Level 4 with a real "A, retained, later B, A becomes relevant to B" chain.

---

## 4. Broken Chains

| Experience | → | → | → Dead end at |
|---|---|---|---|
| Self-edit retry diagnosis | recorded in the retry's own local variables | never persisted anywhere beyond the call frame | **NO STORAGE** |
| `learn_from_sandbox_outcome()`/`learn_from_rating()`'s real signal | persisted to `river_brain.pkl`'s classifier state | classifier is real and trained | **NO CONSEQUENTIAL READER** — nothing ever reads a prediction from it for a decision |
| `seam_engine`'s 76/78 non-surviving detections | logged in `seam_log.jsonl` | `harvest_question()` called, question constructed | **NO CONTEXT MATCHING** at the garden's own dedup step — rejected on template-similarity, not the real `(pair, direction)` uniqueness already computed upstream |
| Curiosity garden's stored, unresolved questions | persisted with real metadata | real `select_from_garden()` call exists | **NO TRIGGER** for relevance — selection is staleness/novelty-weighted, blind to whether anything new and specifically relevant has occurred |
| `council_deliberations.jsonl`'s raw per-councillor disagreement | fully persisted, 5,110+ real lines | — | **NO CONSUMER** at all, confirmed by direct grep this pass |
| `apply_to_code`'s 6 real weeks of transformation history | fully logged, trusted-observer verified | — | **UNMEASURED** against the actual quality outcome it was meant to affect (already checked, found null, `[inherited]`) |

---

## 5. Unresolved Experience Analysis

What currently happens to an experience Echo does not successfully resolve today, concretely:

- If it's a **self-edit failure**: logged once (`SELF_EDIT.log`), the retry's own diagnosis discarded
  after that call frame, contributes only to a family-level, content-blind convergence counter that
  rarely fires.
- If it's a **contradiction between two internal signals** (`seam_engine`): logged every cycle
  regardless of outcome (a real, good practice — "empty result" is logged too), but a genuinely novel
  one has a ~97% chance of never surviving the garden's own dedup filter to become an askable question.
- If it's an **uncertain/low-confidence conversational answer**: no mechanism in this ledger tags or
  retains "uncertain" as a distinct category at all — `echo_ground_truth.py`'s epistemic-note addition
  (Finding 43/45) shapes how uncertainty is *expressed* in the moment, but nothing persists "I wasn't
  sure about X" as a revisitable item.
- If it's a **real sandbox/functional failure** (`functional_quality.py`'s own output, where it's ever
  used): currently has zero live callers at all, so this case doesn't even reach the "logged" stage in
  production.

**There is no FeralEcho concept equivalent to "I don't know what this means yet, but it may matter
later."** The garden comes closest in spirit (a real "pending" concept exists — `status: "active"`) but,
per §2/§6, its revisitation is content-blind.

---

## 6. Temporal Revisitability

**Can Echo encounter A, retain A, encounter B later, and use A to change behavior on B, where A and B
are actually related?** No mechanism checked in this pass demonstrates this. The garden is the only
candidate with a genuine, real temporal gap (real questions sit `active` for real days/weeks — verified
by `age_days` weighting existing in the real selection formula) — but the *reason* an old question gets
picked is never "something relevant to it just happened," it's "it's old and hasn't scored well." This
is temporal revisitation without contextual relevance — a real, meaningful, and precise distinction the
mission asked to be kept explicit. Classify this specific gap as **NO CONTEXT MATCHING**, not "no
revisitation at all" — the revisitation mechanism is real, its relevance-blindness is the actual seam.

---

## 7. Strongest Existing Learning Mechanism

The shadow-model termination (§3, item 2). Not because it's generative — it's a subtraction — but
because it is the **only** mechanism in this entire ledger that demonstrates the full mission-specified
chain without a broken link: real historical predictions → real outcome comparison → real measured
verdict → a real, verified change to production arbitration logic → confirmed still in effect. Every
other candidate breaks at storage, retrieval, context-matching, or consequential-reading.

---

## 8. Strongest Evidence Against the Stomach Hypothesis (mandatory section)

1. **The shadow-model case (§7) proves FeralEcho does not categorically lack the capacity to convert a
   measured, unresolved-at-the-time signal into a later behavioral change** — the capability exists, at
   least for "stop trusting X." A hypothetical stomach's core requirement (measurement → later
   behavioral consequence) has one clean, real precedent already.
2. **RiverBrain's `model_task_stats` loop is a real, continuously-operating example of exactly the
   "experience → retained → later relevant → behavior changes" shape**, even though its proxy is weak.
   If the concern is "does FeralEcho have *any* infrastructure capable of this shape," the honest answer
   is yes — the concern is quality/scope of what closes the loop, not total absence of loop-closing
   machinery.
3. **The garden already has real persistence, real staleness-awareness, and a real
   `investigation_plan` field for genuinely multi-step, revisitable work** — the skeleton the mission's
   own proposed lifecycle (OBSERVED → CANDIDATE → REVISITED → TESTED) describes is closer to already
   existing, in a different name, than a from-scratch design would suggest.

## 9. Strongest Evidence Supporting the Stomach Hypothesis (mandatory section)

1. **`council_deliberations.jsonl`, 5,110+ real lines, zero readers** — a large, rich, already-collected
   dataset of genuine multi-model disagreement, confirmed this pass to have no consumer of any kind.
   This is exactly the shape of raw material a consolidation layer would need and currently goes
   nowhere.
2. **The garden's relevance-blindness (§6) is a precise, structural, not-yet-documented-this-precisely
   gap** — the closest thing to a stomach in this system genuinely cannot do the one thing that would
   make it one: recognize that new information makes an old, unresolved item newly relevant.
3. **The RiverBrain proxy weakness (r=0.206, `[inherited]`) means the one real closed loop in the whole
   system is learning the wrong thing** — even where the "digestive tract" exists, the food entering it
   is a poor representation of what actually matters.
4. **Self-edit retry's complete lack of persistence (§2, §4)** is the cleanest, single starkest example
   in this whole ledger: a real diagnosis is computed, is genuinely useful (it fixed the immediate
   problem), and is discarded completely, every single time, with no code path that could ever surface
   it again even in principle.

---

## 10. Minimal Missing Capability

Not a new reservoir from scratch. The two cheapest, most surgical changes that would close the two
largest identified gaps, in order of leverage:

1. **Garden relevance-matching**: replace or supplement `select_from_garden()`'s pure staleness/novelty
   weighting with a real relevance signal — e.g., boosting a pending question's weight when the current
   cycle's own topic/category overlaps with it, rather than selecting blind to current context. This
   alone would give the garden genuine "B makes A relevant again" behavior for the first time.
2. **Self-edit retry persistence**: the smallest possible version is not a new subsystem — it's writing
   the retry's real diagnosis/correction pair to something already-durable (even `reflection_shard.jsonl`,
   already real and already durable) with enough structure (failure signature, correction summary) that
   a *future* `_build_targeted_prompt()` call could at least optionally read recent entries for the same
   family, rather than the current zero-persistence design.

Neither is implemented in this pass, per the mission's explicit instruction.

---

## 11. Recommended Next Experiment

**One experiment**: instrument `select_from_garden()` (read-only, isolated harness, no production edit)
to log, for the next N real autonomous cycles, whether the *category* of the currently-active autonomous
context (e.g., what topic the emergent_loop's own salience/surprise signal is currently elevated on) ever
overlaps with the category of the question actually selected — and compare that overlap rate to what
pure chance would predict given the real category distribution in the live garden. This directly,
cheaply (no model calls needed — pure log/state analysis against already-running cycles) tests whether
the garden's real selections are *already* incidentally relevance-correlated (in which case §10 item 1
is lower priority than it looks) or genuinely uncorrelated with current context (confirming the gap is
real and worth closing). Success criterion: overlap rate distinguishable from the chance baseline in
either direction, with a clear enough sample (recommend collecting real data over at least 48h of
already-running autonomous cycles, since this needs zero new generation and can passively observe the
live system once it's running again).

---

## 12. Confidence

**MEDIUM-HIGH.** The core inventory (§2) draws on independently-verified, already-reproduced findings
from four separate investigation passes tonight (Phase 1.5, Michelangelo II/III/IV) plus three new,
direct source checks performed in this pass specifically (garden's `select_from_garden()` weighting
logic, self-edit's `_build_targeted_prompt()` zero-reference confirmation, `council_deliberations.jsonl`
zero-consumer grep) — all Level 2-3 evidence (reachable code, live state) with several genuine Level 4
observations inherited from prior real experiments tonight (the shadow model's real termination, the
learning-loop series' real RED result). Confidence is not HIGH because this pass did not itself run new
Level 4-6 behavioral experiments (per its own read-only mandate) — every claim of "no consequence" rests
on tracing reachability and consumption, not on a fresh, direct behavioral test of every row. The two
new findings this pass adds beyond inherited context (garden relevance-blindness; `council_deliberations.
jsonl`'s total zero-consumer status) are both Level 2-3 (confirmed code/data facts), not yet Level 4
behavioral confirmations — a real, disclosed limit on this pass's own certainty, not glossed over.

---

**Environment verification**: `run.py` not started at any point during this pass (no process check ever
returned a match). `memory/river_brain.pkl` sha256 `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` —
unchanged (this pass performed zero write operations to it, made zero model/generation calls of any
kind — pure source/log/state reading throughout). Git HEAD `2cf2d95009943797db5ec41fea9b4021634fd5e6` —
unchanged, no commits made. No file outside this one new report was created or modified.
