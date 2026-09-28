# Persistent-Competence Candidate Tournament

**Date:** 2026-09-20 (mission opened 2026-09-19)
**Type:** Read-only candidate discovery + comparative tournament (no implementation)
**Prior documents this mission builds on and re-litigates from zero**: `audits/2026-09-19_persistent_competence_experiment_design.md`, `audits/2026-09-19_persistent_competence_experiment_adversarial_review.md`
**Method**: Five genuinely independent, non-fork investigator agents, each briefed only on current source (told explicitly NOT to read the prior two reports where candidate-discovery neutrality mattered), each producing a full independent report. This document compiles their findings; every claim below is traceable to a specific investigator's direct source citation, not to this compiler's own narrative preference. Where the compiler added synthesis/scoring judgment, it is marked `[COMPILER]`.

---

## 1. Executive Verdict

**No single existing FeralEcho mechanism wins the tournament outright.** Four real, live-wired, independently-investigated candidates (RiverBrain, `self_model_claims.py`, `behavioral_state.py`, `task_type_classifier.py`) each dominate on a different, non-overlapping subset of the fourteen scorecard dimensions, and each fails hard on at least one dimension the central question cannot do without. RiverBrain has the only **VERIFIED** state-mutation→behavior-change chain of the four, but its connected evaluator signal is self-referential (a static heuristic scoring the generator's own text) and its two genuinely independent signals are architecturally disconnected from the consumed statistic — confirmed independently by four separate reads across this project's history, plus a fifth in this mission. `self_model_claims.py` has the cleanest evaluator independence (a real, non-LLM, self-refreshing codebase scan) but is, by its own dedicated deep-dive's unhedged verdict, "a well-verified diary" — zero causal weight over any decision beyond prompt wording, confined to 5 hardcoded subjects, and structurally confounded by in-context reinjection (any observed "persistence" may just be re-telling the model the same fact every relevant turn forever). `behavioral_state.py` has the single best-demonstrated behavioral-consequence result in the entire codebase (a real subprocess-restart test with correct negative controls) but is explicitly, definitionally disqualified from an autonomous-competence claim by its own header comment and its hard human-confirmation gate — and a new finding this mission surfaced shows even its demonstrated effect bypassed the real production reachability gate three of its four real entry points impose. `task_type_classifier.py` is the only candidate structurally capable of genuine novel-transfer generalization (its BagOfWords architecture doesn't hit RiverBrain's exact-key dead ends), but it has the worst accumulation profile of all four: a hard, permanent, non-decaying freeze on model updates after 100 examples per class — independently discovered by two separate investigators via two different reads.

**The cheapest credible experiment is therefore a minimal, explicitly-labeled hybrid**, not a repair of any one candidate: reuse the one already-existing, already-independent, already-high-volume oracle in this codebase (real F2 sandbox execution pass/fail, classification A, 15,939 real historical observations) as the evaluator; do **not** reconnect it into RiverBrain's actual pickle/singleton/writer-thread apparatus (confirmed the most expensive and highest-risk to isolate of every candidate examined); instead give it a small, freshly-built, cheaply-isolatable carrier explicitly modeled on `self_model_claims.py`'s/`behavioral_state.py`'s proven-simple architecture (plain file, no singleton, no background thread, no OS lock); and consume it through a narrow new function that mirrors — but does not literally call — `score_model()`'s already-VERIFIED selection logic. This is the smallest number of new wires that connects an already-independent evaluator to an already-proven causal-consumption pattern without inheriting either RiverBrain's isolation costs or its evaluator-independence failure. See §17.

---

## 2. Candidate Discovery Methodology

One investigator was assigned to rediscover candidates from scratch, explicitly forbidden from reading either prior report, searching current source directly (`grep` for pickle/JSON/SQLite/FAISS persistence, `ls app/core/*.py` read in full, class/function-name searches for `Ledger`/`Tracker`/`learn`/`persist`). A second investigator ran a broader, 17-candidate structured resurvey covering the same shape plus every `app/experiments/*` directory. Both were cross-checked against each other and against the three deep-dive investigators' own incidental discoveries. This produced convergent, independently-derived candidate lists rather than one investigator's search being taken on faith.

---

## 3. Complete Candidate Inventory

Combining both discovery passes, deduplicated. "Chain status" uses the mission's own PRODUCER→EVALUATOR→MUTATION→PERSISTED OBJECT→RELOAD PATH→CONSUMER→DECISION EFFECT→PERFORMANCE CONSEQUENCE spine.

| # | Candidate | Chain status | Note |
|---|---|---|---|
| 1 | **RiverBrain / `model_task_stats`** | COMPLETE (structural), UNKNOWN at PERFORMANCE CONSEQUENCE for the general claim | Primary tournament candidate — §7 |
| 2 | **`self_model_claims.py`** | COMPLETE | Primary tournament candidate — §5 |
| 3 | **`behavioral_state.py`** | COMPLETE mechanically, ABSENT in practice (0 live directives) | Primary tournament candidate — §6 |
| 4 | **`task_type_classifier.py`** | COMPLETE | Primary tournament candidate — §7 (requalified alongside RiverBrain), §9/§10/§11 |
| 5 | FAISS/memory retrieval (`memory_bridge.py`) | COMPLETE, PERFORMANCE CONSEQUENCE **DISPROVEN** by a real prior ablation (null result, indistinguishable from noise floor) | The one candidate with direct negative empirical evidence, not merely untested consequence |
| 6 | `echo_state.py` valence (dim[8]) | COMPLETE, narrow scope (autonomous self-reflection prompt selection only) | Affects selection *probability*, not demonstrated output quality |
| 7 | `seam_engine.py` | COMPLETE, PERFORMANCE CONSEQUENCE UNKNOWN | Real detections exist (83 in the historical corpus per CLAUDE.md), zero measured downstream effect ever checked |
| 8 | `curiosity_engine.py`/`garden_manager.py` | COMPLETE, two independent real consumers | Pure attention-allocation; no outcome validation anywhere |
| 9 | `self_edit_attempt_ledger.py` | COMPLETE mechanically, but its own docstring states it is read by nothing that decides anything | Deliberately neutered by design — a genuine negative-control example |
| 10 | `shadow_model.py` | **BROKEN at CONSUMER** | Deliberately retired 2026-09-13 after measured below-chance accuracy; all 3 call sites removed |
| 11 | `snapshot_manager.py` restore-council-review (uncommitted diff) | COMPLETE mechanically with a real hard decision branch (HTTP 409 refusal) | **Not** an accumulated-experience mechanism — a same-request advisory gate, no reload-from-history step; never fired in production; uncommitted |
| 12 | `provenance_check.py` | **BROKEN at MUTATION** | No persistence exists anywhere in 1,299 lines; zero production callers |
| 13 | Self-edit fitness gate + `apply_to_code` hook | COMPLETE, most extensively self-audited mechanism in the codebase | Its own history is a documented record of repeated failure (broken deployments, one corruption event), not reliable improvement |
| 14 | `council_rater.py` trust gate | COMPLETE, feeds Candidate 1 | Discovered while tracing RiverBrain's `learn_from_council_rating()` path |
| 15 | `self_model_updater.get_weak_task_type()` → self-edit targeting | COMPLETE | Recently reordered per CLAUDE.md Finding 91; inherits Candidate 1's quality-scorer caveats |
| 16 | `liveness_ledger.py` self-report surfacing | Effectively **BROKEN at DECISION EFFECT** | Every downstream path is reporting/prompt-text, never a behavioral branch |
| 17 | `app/experiments/*` (all 12 directories: E5-mini, RAOC, preference_provenance, p3_causal_learning, etc.) | **BROKEN at CONSUMER, categorically** | Zero production imports found for any experiment package — confirmed by repo-wide grep across all of `app/*.py`/`app/core/*.py`/`run.py` |

**[COMPILER]** Candidates 5–17 are surveyed for completeness and to rule things in/out; the formal 14-dimension scorecard (§15) is scoped to the four candidates (1–4) that cleared a COMPLETE chain *and* received full independent deep-dive investigation, per the mission's own emphasis on `self_model_claims.py`, the "second new mechanism" (`behavioral_state.py`), and RiverBrain requalification, extended here to include `task_type_classifier.py` since it was independently found to be the only candidate with a structurally distinct transfer profile.

---

## 4. Producer→Evaluator→State→Consumer Maps

Condensed from the full investigator reports (see the five underlying investigations for exhaustive file:line citations on every claim below).

**RiverBrain**: PRODUCER = real conversational responses + F2 sandbox outcomes + human ratings + peer-council ratings (4 distinct producers). EVALUATOR = mixed — `_score_response_quality()` (C, static AST/keyword heuristic, feeds the dominant-volume `learn()` path) / real sandbox pass-fail (A, `learn_from_sandbox_outcome()`) / real human 1-5 stars (D, `learn_from_rating()`) / another model's rating blended 30/70 with (C) (E, `learn_from_council_rating()`). MUTATION = `model_task_stats[model][task_type] = {count, mean}`, under lock. PERSISTED = `memory/river_brain.pkl` (4.4MB, actively written). RELOAD = `RiverBrain.load()`, called by a process-wide singleton with **two converging resolution paths** (Flask `current_app.config['echo_core'].river_brain` and a module-level fallback cache). CONSUMER = `score_model()` → `rank_models()`/`_select_council()`. DECISION EFFECT = OBSERVED, real sort-key branch. PERFORMANCE CONSEQUENCE = SUPPORTED for selection mechanics (a real prior experiment measured a ranking-predicts-correctness rate of 77.8% overall — but only 38.9%, worse than chance, once a single-model confound is removed); UNKNOWN for any broader competence claim.

**`self_model_claims.py`**: PRODUCER = real introspective `/chat/stream` exchanges. EVALUATOR = `verify_self_knowledge_claims()` against a real, independently-maintained architecture scan (`CartographerDB`) and background-telemetry `self_model.json` — classification **A**, structurally enforced against self-certification via `proposed_by != verified_by` (though this enforcement is a string-inequality convention, not cryptographic/architectural authentication — a real, newly-flagged weakening of the "structural" claim). MUTATION = `record_claim()`, append-only JSONL. PERSISTED = `memory/self_model_claims.jsonl` (23 real records). RELOAD = fresh disk read every call, zero caching — OBSERVED restart-durable. CONSUMER = `_build_self_model_claims()`, reachable from all real production entry points when the prompt is introspective. DECISION EFFECT = OBSERVED but soft — alters prompt text only, probabilistically obeyed (one documented live-reproduction bug where the model still got it wrong despite correct grounding). PERFORMANCE CONSEQUENCE = SUPPORTED narrowly (two live reproductions), confined to a hardcoded 5-subject vocabulary, and confounded by in-context reinjection.

**`behavioral_state.py`**: PRODUCER = a human, typing and confirming a directive by hand. EVALUATOR = none — explicitly not a learning mechanism; `human_confirmed=True` (literal bool, `is not True` check, zero bypass anywhere in the codebase — confirmed by exhaustive grep, zero live production callers of any mutator). MUTATION = atomic JSON replace with pre-mutation backup. PERSISTED = `memory/behavioral_directives.json` (currently 0 directives). RELOAD = fresh disk read, no cache — OBSERVED, and uniquely among all candidates, verified via a **real separate-subprocess restart test**, not just code inspection. CONSUMER = `get_matching_directives()` → `_build_behavioral()`, **but** reachable only through `get_structural_self_facts()`, which 3 of 4 real production entry points gate behind `_is_introspective()` — a keyword check about Echo's own architecture, essentially never satisfied by an ordinary-topic directive. Only the two autonomous self-reflection call sites in `emergent_scheduler.py` call it unconditionally. DECISION EFFECT = OBSERVED and the most rigorously measured in this survey (75% compliance at n=4, correct 0% at baseline, correct nulls on absent-trigger and near-miss controls) — **but measured via a path that bypasses the real gating**, so the measured effect and the real production effect are not currently the same claim. PERFORMANCE CONSEQUENCE = real for the mechanism in isolation; UNKNOWN/likely-never-organic in real production use given the gating gap and the currently-empty store.

**`task_type_classifier.py`**: PRODUCER = real `source=="user_conversation"` prompts. EVALUATOR = the task_type label the classifier is trained toward is itself generated by the keyword-heatmap ladder this classifier exists to supplement — classification **E** (soft circularity: student and teacher signal share a common upstream origin), sharpened by a confirmed self-reinforcement risk (a confident classifier prediction can become the very label it next trains on, when the keyword heatmap is ambiguous). MUTATION = online BagOfWords+MultinomialNB update, gated by a **hard, permanent cap**: `_MAX_MODEL_EXAMPLES_PER_CLASS = 100` — after 100 real examples per class, `learn_one()` is never called again for that class, for the life of the pickle, no decay, no refresh. PERSISTED = `memory/task_type_classifier.pkl`. RELOAD = OBSERVED, with the same "never overwrite richer pkl" guard shape as RiverBrain (and the same blind spot — richness judged only by aggregate observation count). CONSUMER = `detect_task_type()`/`resolve_task_type()`. DECISION EFFECT = OBSERVED, real hard branch (routes council composition, token budget, tool-list injection). PERFORMANCE CONSEQUENCE = UNKNOWN; a real, already-run blinded pilot (n=20) found the question of whether this classifier beats the keyword heuristic **unstable across labelers** — the ranking inverted depending on who labeled the same 20 items.

---

## 5. `self_model_claims.py` Deep Dive

Full 12-question analysis performed independently (see the dedicated investigator report). Headline findings, each OBSERVED unless noted:

- Claim extraction is pure regex/string matching against the full response text — no LLM judges or extracts a claim.
- The evaluator (`self_knowledge_verification.py`) never lets the response text under evaluation feed into what it's checked against — ground truth is always a freshly-read separate file (`self_model.json`) or a live `CartographerDB` scan. Genuinely independent, structurally, not merely by convention at the *check* step.
- Minimum viable record: `{subject, verified, evidence}` — three fields.
- Restart survival: OBSERVED, real — the live file spans 10 days across numerous real server restarts with no evidence of loss (no cache anywhere in the read path).
- **A previously-unflagged reachability gap, independently discovered**: the consumer only ever looks up the 5 hardcoded `KNOWN_SUBJECTS` names. 4 of the real 23 records (the most recent) fall under a generic fallback subject name never checked by any reader — permanently orphaned, write-only, from the moment they're written.
- The one cited "naturally occurring evaluator-produced mutation traced to a behavioral consequence" (a misread "VERIFIED FALSE" line, later fixed) is real and verified, but is the mechanism's own developer catching a self-inflicted rendering bug during construction — not an example of the ledger correcting some *other*, independent capability gap.
- Records are independently removable/addable with zero collateral state change (no cross-record indexing).
- Format is self-contained and plausibly transplantable — no instance-specific identifiers.
- Hidden dependency: the record's `subject` string must exactly match a `KNOWN_SUBJECTS` key (a code constant, not a data file) to ever be read, and the "current status" half of the rendered text is re-derived fresh from `self_model.json` at read time, independent of what the transplanted record itself says.
- **Verdict, unhedged, from the dedicated investigation**: "This is a well-verified diary, not a competence substrate... nothing in the read path alters model selection, routing, task-type classification, council composition, retry behavior, training signal, or any tool/policy decision." Zero of the real 23 records are `verified: true` — everything accumulated so far is "stop repeating this false thing," never "you can now do X."

---

## 6. Second-New-Mechanism (`behavioral_state.py`) Deep Dive

Full 12-question analysis performed independently. Headline findings:

- The `human_confirmed is True` (not merely truthy) gate is absolute — every mutator refuses without it, no internal caller anywhere supplies it, and zero live application code calls any mutator today (only two research/validation scripts do).
- No evaluator of any kind exists — pure storage-and-recall, no compliance-checking loop, and (a genuinely new finding) no Liveness Ledger check exists for this module at all, a real gap relative to this project's own stated standard that every subsystem gets a ground-truth check.
- Restart survival was tested more rigorously than any other candidate: a genuine, separate-subprocess restart, with real recorded compliance results and correct negative controls (0/2 baseline, 2/2 immediate, 1/2 post-restart-paraphrase, 0/2 and 0/1 on two distinct negative controls).
- **The most consequential finding of this deep dive**: the module's own design-intent comment claims its consumer is evaluated "independently" of the introspection gate every other ground-truth slice uses — but tracing the real call sites shows this is only true *inside* the function; 3 of the 4 real human-facing callers (`terminal_client.py`, Echo Studio, `/mirror_echo`) wrap it in an `_is_introspective()` check anyway, which an ordinary-topic directive will essentially never satisfy. The validation script that produced the 75% compliance figure calls the internal function directly, bypassing this gate — meaning that figure does not demonstrate real production reachability for anything but Echo's own autonomous self-reflection.
- Removal is trivial and safe; transplant is high-confidence (zero FAISS/RiverBrain/embedding dependency, confirmed by the module's own adversarial "poisoning" test).
- Self-disclaimer, quoted exactly: *"THIS IS NOT A LEARNING MECHANISM. It is a small, bounded, human-confirmed, deterministically-triggered directive store."* And in the rendered prompt itself: *"human-confirmed instructions, not something Echo learned or recalls."*
- **Verdict**: the human-confirmation gate definitionally disqualifies this from autonomous acquired competence. It remains valuable as infrastructure — its persistence/audit/rollback/restart-test discipline is the strongest engineering template in this survey — and as a comparison point, but not as a candidate substrate.

---

## 7. RiverBrain Requalification

Re-derived from zero, independently, by two separate investigators (behavioral_state.py's deep-dive report, Assignment 2; and the isolation/math investigator's Part C). Both converge:

- `learn()`'s dominant-volume signal is confirmed self-referential — `_score_response_quality()` for coding tasks is a pure `ast.parse()`/structural-node-count transform applied to the candidate's own text, with **no held-out task, no execution, no external oracle anywhere in the path**. One investigator states this precisely: "there is no independent test suite, no held-out answer... solution and grading share one artifact."
- `learn_from_sandbox_outcome()` (real, execution-grounded, classification A) confirmed — independently, a fourth and fifth time across this mission alone — to never write `model_task_stats`. Real historical volume is large (15,939 observations), not theoretical.
- A partially-independent third path, `learn_from_council_rating()`, was newly confirmed **live today** (real, non-zero `council_vetted_count` fields read directly from the current production pickle) — a correction to an earlier audit that had called this path dead. Still only 30%-weighted toward genuine peer judgment; 70% remains the same self-referential heuristic.
- Restart survival: SUPPORTED, not VERIFIED — no investigator across this entire mission (or the prior two reports) found a single controlled before/after equality test across a real process kill-and-restart. The best available evidence is circumstantial: multi-week monotonic observation-count growth across a system with a heavily-documented restart history.
- `score_model()`→`_select_council()`: OBSERVED, unambiguous mechanical fact — a real Python `sorted()` call keyed directly off the mutable statistic.
- The one real controlled experiment against an independent criterion (`tier7_riverbrain_candidate_ranking_forensic.md`, read directly by two investigators) found the signal predicts correctness at 77.8% overall — but this is a Simpson's-paradox artifact of one specific weak model; on the one pairing that excludes that model, the same signal predicts correctness at 38.9%, worse than a coin flip. This finding has **not** been acted on in production code, which still applies the score as a uniform ordinal ranker.

**Narrow claim vs. stronger claims, explicitly separated**: "a state mutation causes a measurably different ranking output" is fully established, mechanical fact — no further evidence needed. "This ranking change reflects genuine competence" is partially, narrowly supported (real but confound-riddled, model-specific, not yet confirmed out-of-sample). "This constitutes learning" is not established and is actively undermined by the self-referentiality of the dominant signal.

**What RiverBrain lacks, and the smallest fix — checked for landmines, not assumed**: the connected signal is self-referential; the one architecturally-independent signal is disconnected from the consumed field; restart survival is unverified; the one real predictive-value test found narrow, confound-riddled value not yet acted on; no experiment anywhere tests `_select_council()` itself against an independent outcome (only a related sibling mechanism sharing the same signal has been tested). The "obvious" fix (reconnect sandbox feedback) is directionally correct and was independently re-derived as the highest-leverage single change — but one investigator found a specific implementation landmine a naive version would hit: `learn_from_sandbox_outcome()` hardcodes `task_type="coding"` internally, while `self_edit_manager.py`'s own call sites, sitting right next to code that already carefully uses `task_type="self_edit_coding"` (per a prior fix, CLAUDE.md Finding 35), would silently dump self-edit-generation pass/fail into the same bucket Tier-7 validated — reintroducing cross-context contamination this codebase already paid once to fix. The correct minimal fix parameterizes the `task_type` argument explicitly, not merely reconnects the wire.

`task_type_classifier.py`'s own requalification (folded in here since two investigators treated it alongside RiverBrain): its label-generation is softly circular (same upstream heuristic feeds both "student" and "teacher"), and its `_MAX_MODEL_EXAMPLES_PER_CLASS=100` hard cap — independently discovered by two separate investigators via two different reads of the same code — means "more experience" produces **literally zero model change** for any class already past 100 real examples, a harder ceiling than RiverBrain's discounting EMA.

---

## 8. Evaluator-Independence Comparison

| Candidate | Source classification | Independence verdict |
|---|---|---|
| RiverBrain | Mixed: C (dominant volume), A (disconnected), D (disconnected), E (live, 30%-weighted) | **Not solid.** The consumed statistic is fed by a static self-scorer or a mostly-self-scorer blend; the two genuinely external signals never reach it. |
| `self_model_claims.py` | A (claim-checking step) | **Solid for the check itself** — real, non-LLM, self-refreshing ground truth. **Weakened at the recording step** — the "structural" `proposed_by != verified_by` guard is a string-inequality convention trusting the caller, not an enforced authentication. Also uniquely susceptible to an in-context-reinjection confound (see §5). |
| `behavioral_state.py` | Not a learning signal by design | **Total and trivial** — a model cannot fabricate `human_confirmed=True`; it must be a literal Python bool from calling code, and no live route supplies it. Independence is real but the category is the wrong one for this mission's central question. |
| `task_type_classifier.py` | E (soft circularity) — real text input (D-adjacent), but the trained-toward label originates one step upstream from the same heuristic ladder this classifier supplements | **Soft, not hard, circularity** — not an exploit, but a real, confirmed self-reinforcement risk when the keyword heatmap is ambiguous and the classifier's own confident prediction becomes the next training label. |

**Mandatory regression check (per the mission's explicit instruction)**: the previously-demonstrated filesystem-leakage exploit against a shared task-pool file was re-checked as a live threat against every candidate here. None of the four candidates reuse that specific task-pool file, so the *exact* exploit does not currently apply — but RiverBrain's coding-path evaluator has the **structurally identical vulnerability class** (grading a candidate against a transform of its own output, with no held-out answer at all) independently re-confirmed this session as "the sharpest finding for this candidate."

---

## 9. Isolation Qualification

Derived independently from RiverBrain's actual singleton/thread/lock code, then applied to every other candidate.

| Candidate | Singleton? | Autonomous background write? | Path hardcoded? | OS-level lock? | Overwrite-guard scope |
|---|---|---|---|---|---|
| RiverBrain | **Yes, two converging resolution paths** (Flask app-config + module-level cache) | **Yes** — daemon writer thread autosaves within ≤60s of construction, unconditionally | Bare module global (patchable, not parameterizable) | `fcntl.flock`, real cross-process coupling risk if unpatched | Only aggregate `observation_counts`, never inspects `model_task_stats` itself — a real, previously-undiscussed integrity gap |
| `task_type_classifier.py` | Yes, lazy module-level, **but with no lock guarding the check** — a real, unaddressed TOCTOU race | No thread, but a save-on-counter side effect (every 20 `learn()` calls) | Bare module global, patchable | `fcntl.flock`, same coupling risk | Same narrow scope as RiverBrain |
| `self_model_claims.py` | **No class/singleton at all** — pure module functions | **Absent** — no thread, no timer anywhere | Bare module global, patchable | None — no `fcntl` anywhere | N/A — pure append, nothing ever overwritten |
| `behavioral_state.py` | **No class/singleton** | **Absent** | Bare module globals, patchable | None — atomic `os.replace()` only | N/A — full-file atomic replace with a pre-mutation backup, structurally safer than a richer/poorer comparison |
| `echo_state.py` | No class | Absent | Patchable | None | Absent — unconditional overwrite each call (consistent with being a cheap, frequently-recomputed vector) |
| `memory_bridge`/FAISS | **Genuinely parameterizable via constructor**, the structurally cleanest of the group | Absent inside the class itself | **Not a module constant at all** — real constructor arguments | None | Absent |

**Required evidence to prove genuine isolation, specified without executing anything against production** (RiverBrain, the hardest case): run the experiment in a genuinely separate OS process; redirect the module-level path constant *before* the first singleton-triggering call, and confirm the redirect took effect; confirm the scratch path (not the real one) changes after a forced save; wait out at least one full 60-second writer-thread cycle and confirm only the scratch path's mtime changed; capture the real production file's sha256 hash and mtime *before* the redirect is even applied, and again after the full experiment including the wait — byte-identical and mtime-unchanged is the only check that directly falsifies "did this touch production," independent of trusting the redirect logic itself.

**Ranking**: `self_model_claims.py` and `behavioral_state.py` are tied cheapest to isolate — no singleton, no thread, no lock, nothing to race. `echo_state.py` is comparably cheap. `memory_bridge`/`VectorMemory` is nearly as cheap and the *best-designed* (genuine constructor parameterization, no monkeypatch required) but carries an import-time eager-construction trap if the wrong module is imported. **RiverBrain and `task_type_classifier.py` are the most expensive and highest-risk to isolate**, RiverBrain more so given its two-layer singleton resolution.

---

## 10. Mathematical-Identifiability Analysis

Independently re-derived by direct formula inspection, not assumed from any prior framing.

**RiverBrain**: `effective_n = min(count, 200); mean += (score - mean) / effective_n`. Proven by induction: the 0.5 seed cancels exactly at the first observation; below count=200 this is a true, exact, order-invariant cumulative mean — staged/interrupted accumulation is **algebraically identical**, not merely hard to distinguish, from one continuous run of the same observations. Above count=200 it becomes a genuine EMA with a ~138-observation half-life (`ln(0.5)/ln(0.995)`), order-sensitive but with no semantic notion of provenance — a synthetic sequence with matched order statistics produces the identical recency-weighting. A **second, independent visibility gate** exists at `count ≥ 5` (`_MIN_MODEL_OBSERVATIONS`), separate from the update-rule degeneracy — any experiment must clear both.

**`task_type_classifier.py`**: **sharper and structurally different** — two independent thresholds, not one soft transition. `_MAX_MODEL_EXAMPLES_PER_CLASS=100` is a **hard, permanent freeze**: past 100 real examples per class, the model literally stops updating, forever — not decay, a total stop. A separate visibility gate (`_MIN_OBSERVATIONS`, 200 for coding/personal, 30 for general/creative/reasoning) parallels RiverBrain's, in the opposite direction: a floor for visibility here, versus a ceiling for learnability there. Any experiment testing "does more experience matter" on this candidate is **structurally void past 100** for the affected class — a harder guarantee than RiverBrain's soft EMA.

**`self_model_claims.py`**: **ABSENT.** Pure append, no aggregation, order-preserving, informative from the very first record (the consumer only ever reads the single most-recent entry per subject — no running statistic exists to degenerate).

**`behavioral_state.py`**: **ABSENT.** No numeric running statistic anywhere in the file; deterministic exact-substring matching, order = creation order.

**`echo_state.py` valence's dry-run component**: a **different** degeneracy shape — a hard 10-event window recomputed fresh from the raw log every call, with zero persistent running-mean object. The 11th-most-recent matching event has exactly zero influence, not exponentially-decayed influence — a much shorter-tailed eviction than RiverBrain's, and a transplanted/injected signal survives exactly 10 subsequent real events before total eviction.

**Precondition for the scorecard**: any experiment on RiverBrain needs `count ≥ 5` for visibility and — if testing staging/order effects specifically — `count ≥ 200` per (model, task_type) to even mathematically matter, though crossing 200 is necessary, not sufficient, for proving genuine causal learning rather than an EMA artifact. Any experiment on `task_type_classifier.py` must stay **under** 100 real examples per class for continued learning to be possible at all. These are opposite-direction constraints — a hybrid touching both mechanisms would need to satisfy both simultaneously, a real design cost worth naming.

---

## 11. A/B/C/D/E Suitability by Candidate

| Candidate | Isolable carrier? | Live alternative explanations for the desired B>A/C→A/D→B/E-wrong-direction pattern |
|---|---|---|
| RiverBrain | Small (`{count, mean}`) but **entangled** — the online classifier component is keyed only by `task_type`, not `model_name` (confirmed directly), so a per-model "D condition" is well-supported for the `model_task_stats` sub-mechanism but **not** for the classifier sub-mechanism, where one model's data unavoidably shapes the shared classifier used to score every other model | (1) `score_model()` is a pure, deterministic function of exactly `{count, mean}` — transplant reproduction is algebraically guaranteed regardless of provenance, testing code correctness, not causal history. (2) The scorer's known "preferential attachment" history (CLAUDE.md Finding 39) means surface/textual features correlated with, not necessarily caused by, competence could drive the pattern. (3) Cross-model classifier contamination (above) is a confound absent from `model_task_stats` alone but present for anything touching `.learn()`'s classifier side-effect. |
| `self_model_claims.py` | Small (3 effective fields) and standalone | (1) `record_claim()` performs zero verification of its own — a B>A effect tests whether the *external* verifier inserted correctly, not whether anything was "learned" through this module. (2) **Critical**: the "CURRENTLY VERIFIED" fact is re-derived fresh from `self_model.json` every call, independent of the transplanted record's own `verified` field — a naive comparison could attribute a large effect to a source shared by both conditions. (3) Confined to 5 hardcoded subjects — no generalization claim beyond them is supported. |
| `behavioral_state.py` | **Smallest and cleanest of all candidates** (`{trigger_keywords, directive_text}`) | **Decisive disqualifier, not merely an alternative explanation**: the "experience" step is a human authoring and approving text, not anything derived autonomously — any B>A/D→B result would misrepresent human-inserted instruction-following as experience-derived causal learning, which the module's own header explicitly forbids reading it as. |
| `task_type_classifier.py` | **Not small** — the causal state is the entire trained NB pipeline (word-counts + per-class counts), not reducible to a handful of scalars | (1) The 100-example freeze (§10) means any comparison touching a class past that count is testing frozen, not adapting, state. (2) The soft label-circularity (§8) means the "independently evaluated experience" going into B may already be partly self-referential. |

---

## 12. Novel-Transfer Suitability

| Candidate | Keying scheme | Which cells are meaningful vs. tautological/inapplicable |
|---|---|---|
| RiverBrain | Exact-string `[model][task_type]` dict keys, zero cross-key sharing (deliberately, per Finding 3's contamination precedent) | Cell 4 (changed identifier) is **structurally guaranteed null** regardless of any real transfer property — and this is precisely the tautology the original Sept-19 report's own worked example (`coding`→`echo_projects_coding`) fell into, independently confirmed by two investigators reading the same two lines of code. Cell 5 (structurally novel task, same key) is the only cell that could inform genuine transfer, and it requires an external instrument (`find_real_task_pairs()`) RiverBrain itself doesn't expose. **Suitable for testing routing adaptation, not reusable competence.** |
| `self_model_claims.py` | Fixed 5-item `subject` vocabulary, no registration mechanism | **Worse than tautological — guaranteed inapplicable.** A genuinely new subject has no path to ever be recorded at all. Every cell except "same subject, asked again" collapses to a vacuous non-test, a distinct and worse failure mode than RiverBrain's forced-null. |
| `behavioral_state.py` | Substring match against live paraphrased prompts | The most transfer-friendly keying scheme of the four by construction — a real paraphrase-survival result exists (the restart test's Phase E). But this is **routing/retrieval generalization** (does a new phrasing still trigger the same fixed, human-authored content), explicitly not competence generalization — the directive text itself never changes or improves. |
| `task_type_classifier.py` | BagOfWords token features, no per-instance key, one shared model per class | **The only candidate structurally capable of genuine cells 2/3/5 transfer** — a statistical bag-of-words model is built to generalize over novel phrasings of the same underlying category, with no dict-key exact-match wall. **New caveat, not previously named**: a worked example against an under-observed class (below its `_MIN_OBSERVATIONS` visibility floor) would itself be a forced-null tautology for a different reason than RiverBrain's — the trust gate, not a key mismatch — so any transfer test here must first confirm the class has cleared its visibility threshold. |

**[COMPILER]**: this is the single sharpest, most consequential finding a fresh investigation added beyond the prior two reports — `task_type_classifier.py` is the only one of the four primary candidates that isn't structurally disqualified from a meaningful novel-transfer test by its own keying scheme, even though it loses badly on accumulation (§13) and has a softer independence profile (§8) than `self_model_claims.py`.

---

## 13. Accumulation Suitability

| Candidate | Saturation | Averaging → lost individual contributions | Overwrite/replace risk | Catastrophic-replacement risk |
|---|---|---|---|---|
| RiverBrain | **Real** — see §10 | **Real** — a single scalar mean; no per-observation ledger exists; a later round's degraded input can silently regress an earlier round's genuine gain while the pooled scalar keeps rising | **A newly-confirmed, previously-undiscussed fragility**: `load()`'s restore for `model_task_stats` is a whole-dict **replace**, not a per-key merge (unlike the neighboring `classifiers` field, which genuinely merges) — a future field added to the live instance but not added to *both* the save-snapshot and the restore-assignment lists would silently vanish on the next restart, indistinguishable from "the effect didn't survive a restart" | Real, matches the prior adversarial review's Scenario 3 exactly, independently re-derived here from the same formula |
| `self_model_claims.py` | **Absent** — pure append, no window | **Absent** — every observation individually recoverable forever | **Absent** | **Structurally impossible in the same sense** — but there is no accumulation of *competence* here at all, only of an audit trail; "safe" and "inapplicable" both apply simultaneously |
| `behavioral_state.py` | **Absent** — hard 20-directive cap, explicit refusal past it (not silent eviction) | **Absent** — every directive a discrete record; atomic backup + rollback support | **Absent** — cleanest accumulation profile of the four | **Absent**, and currently moot — 0 directives exist in production to accumulate |
| `task_type_classifier.py` | **The worst of the four, independently confirmed twice** — a hard, permanent, 100-example-per-class freeze, harder than RiverBrain's discounting EMA (a total stop, not a discount); `observation_counts` keeps rising regardless, creating a real risk of mistaking "more logged" for "more learned" | N/A — not an averaging mechanism | N/A | The frozen-model risk is functionally a permanent, silent form of this — any class past 100 examples cannot acquire "something genuinely new" at all, by construction |

---

## 14. Lizard-Tail Carrier Comparison

| Candidate | Real consumer function | Minimal carrier actually read | Cleanliness |
|---|---|---|---|
| RiverBrain | `score_model()` | `{count, mean}` per (model, task_type) | Numerically tiny, but nested inside a singleton pickle also holding shared per-task classifiers — cannot be exercised cleanly without the full isolation apparatus from §9 |
| `task_type_classifier.py` | `predict()` | The **entire trained pipeline** (word counts + per-class counts) | Not reducible to a handful of scalars — the least minimal carrier examined |
| `self_model_claims.py` | `_build_self_model_claims()` | `{subject, verified, evidence[:200]}` | Small, standalone, but ~50% diluted — the underlying fact is independently re-derived from `self_model.json` regardless of the carrier |
| `behavioral_state.py` | `_build_behavioral()` | `{trigger_keywords, directive_text}` | **Smallest, cleanest, most literally copyable of all candidates examined — 100% of what's read is what's rendered, nothing independently re-derived** |

**Progressive-amputation outlines** (designed, not run, per both candidates' own investigator reports) for the top two by cleanliness — `behavioral_state.py` and `self_model_claims.py` — are specified in full in the underlying isolation/math investigation, covering: complete record → remove auxiliary fields (expect zero change, confirmed unread by the consumer) → remove/alter the gating field (expect the effect to stop firing entirely, since matching is exact-substring, not graded) → truncate/paraphrase the content field (expect a directly-legible, proportional change) → alter identifiers only (expect zero change) → transplant into a fresh state file (expect identical behavior, confirmed via the no-cache read path) → cross a genuine restart (expect identical behavior, for the same reason). For `self_model_claims.py`, step 4 carries a caveat unique to that candidate: the "CURRENTLY VERIFIED" fact line will **not** change under any amputation, since it's independently recomputed from `self_model.json` regardless of what the transplanted record says — any test on this candidate must hold `self_model.json` fixed across conditions or contaminate the comparison. Neither carrier's numeric-quantization step applies the way RiverBrain's `mean` field does, since neither has a numeric field of that kind.

No organism/reproduction/inheritance/instinct/descendant terminology is used anywhere above, per instruction — this is a state-transfer comparison.

---

## 15. Tournament Scorecard

UNKNOWN and ABSENT are kept visually distinct throughout — UNKNOWN means the evidence doesn't resolve the question; ABSENT means the investigation checked and the thing genuinely does not exist.

| Dimension | RiverBrain | `self_model_claims.py` | `behavioral_state.py` | `task_type_classifier.py` |
|---|---|---|---|---|
| Evaluator independence | **Weak** (OBSERVED — dominant signal self-referential; independent signals disconnected) | **Strong** for the check step (OBSERVED); **weakened** at the record step (convention, not enforced) | N/A — not a learning signal by design (OBSERVED) | **Soft/moderate** (OBSERVED circularity risk, not a hard exploit) |
| Real experience input | **Strong** (OBSERVED, real conversational + sandbox + human + peer volume) | **Moderate** (OBSERVED, real but rare — only 23 records, 19 usable) | **ABSENT in current production** (0 directives) | **Strong** (OBSERVED, real conversational volume) |
| Persistent mutation | **Strong** (VERIFIED causal, OBSERVED write path) | **Strong** (OBSERVED) | **Strong** (OBSERVED) | **Strong** (OBSERVED) |
| Restart survival | **SUPPORTED**, never VERIFIED via a controlled restart-and-diff | **OBSERVED**, real (10-day span, no cache) | **VERIFIED**, uniquely — real subprocess-restart test | **SUPPORTED**, code path exists, not live-tested |
| Live consumer | **Strong** (OBSERVED, unconditional) | **Strong** (OBSERVED, reachable from all real entry points when introspective) | **Weak** (OBSERVED gap — 3 of 4 real entry points gate it behind an unrelated check) | **Strong** (OBSERVED, unconditional) |
| Causal behavioral effect | **VERIFIED** mechanically (ranking changes); competence-meaning UNKNOWN | **OBSERVED**, soft (prompt text only, probabilistically obeyed) | **VERIFIED**, the best-measured of the four (real controls) — but measured via a path bypassing real gating | **OBSERVED**, real hard branch |
| Independent competence relevance | **UNKNOWN/weak** — real signal exists but the dominant, connected one is self-scored | **Weak, explicitly** — "a well-verified diary," per its own dedicated investigation's unhedged verdict | **ABSENT by design** — self-disclaimed as not-learning | **UNKNOWN** — closer to routing than task competence, unresolved |
| Transplantability | **Weak** (entangled with singleton/classifier ecosystem) | **Moderate** (self-contained format, functionally limited to 5 subjects) | **Strong** (zero FAISS/RiverBrain dependency, adversarially confirmed) | **Weak** (entire trained pipeline, not a small carrier) |
| Isolation feasibility | **Weak/expensive** (two-layer singleton, background thread, OS lock) | **Strong/cheap** (no singleton, no thread, no lock) | **Strong/cheap** (no singleton, no thread, no lock) | **Weak/moderate** (singleton with a real race, OS lock, save-on-counter side effect) |
| Novel-transfer suitability | **Weak** — coarse keying, tautology risk (confirmed) | **Very weak** — worse than tautological, guaranteed-inapplicable outside its 5-item vocabulary | **Routing-only** — not competence-relevant by construction | **Strongest of the four** — the only candidate not structurally dead-ended |
| Accumulation suitability | **Moderate** — sound but wrongly-fed mechanics, real catastrophic-replacement risk, a newly-found restore-fragility | **Safe but inapplicable** — nothing lost, but nothing genuinely accumulating either | **Cleanest mechanics, currently moot** (nothing to accumulate) | **Worst** — hard, permanent 100-example freeze, independently confirmed twice |
| Minimal-carrier clarity | **Small but entangled** | **Small, ~50% diluted** | **Smallest and cleanest of all candidates** | **Not small at all** — an entire trained model |
| Implementation cost (to reach a defensible experiment) | **Moderate-high** — isolation apparatus + task_type-parameterization fix needed | **Low** — already isolatable, but wrong shape for the question | **N/A** — repurposing would defeat its safety design | **Moderate** — isolation fix needed, accumulation ceiling not fixable without a redesign |
| False-positive risk | **High** — most-attacked candidate in this project's history, multiple independently-confirmed exploit classes | **Moderate** — the in-context-reinjection confound is real and under-disclosed | **Low as a mechanism; high if misread as competence evidence** | **Moderate-high** — soft circularity + confirmed labeler-instability in a real prior pilot |

---

## 16. Winner or Pareto Frontier

**No single winner.** The four candidates form a genuine Pareto frontier, each dominant on a disjoint axis critical to the central question:

- **RiverBrain** dominates on VERIFIED causal-behavioral-effect and sound (if wrongly-fed) accumulation mechanics.
- **`self_model_claims.py`** dominates on evaluator independence and isolation cheapness, but is explicitly self-limited to being descriptive, not competence-bearing.
- **`behavioral_state.py`** dominates on demonstrated-behavioral-consequence rigor and transplantability/isolation cheapness, but is definitionally excluded from an autonomous-competence claim.
- **`task_type_classifier.py`** uniquely dominates on novel-transfer structural suitability, but is worst-in-class on accumulation and carries a soft evaluator circularity.

No existing mechanism spans independent-evaluation + cheap-isolation + genuine-transfer-suitability + sound-accumulation simultaneously. Per the mission's explicit instruction to allow a hybrid: the smallest defensible experiment connects RiverBrain's already-VERIFIED causal-consumption *pattern* (not its actual entangled object) to the one real, already-independent, already-high-volume evaluator this codebase already computes (F2 sandbox execution outcomes), carried in a freshly-built structure explicitly modeled on `self_model_claims.py`'s/`behavioral_state.py`'s proven-cheap isolation profile — see §17.

---

## 17. Cheapest Credible Experiment After Re-Evaluation

**Do not repair RiverBrain's actual object.** Every isolation-cost finding in §9 says the entangled singleton/thread/lock apparatus is the single most expensive part of any RiverBrain-based experiment to make trustworthy, and the EMA-saturation math in §10 imposes a real minimum sample size (≥200 observations per model/task-type pair) before staging effects even become mathematically meaningful. Repairing the actual production object also risks the write-race integrity gap newly found in §9/§13 (the overwrite guard never inspects `model_task_stats` itself).

**Build a small, new, explicitly-labeled carrier instead** — a plain, append-friendly file (JSON or JSONL, matching `self_model_claims.py`'s/`behavioral_state.py`'s architecture exactly: no class, no singleton, no background thread, no `fcntl` lock), keyed `[model][task_type]`, populated **only** by `learn_from_sandbox_outcome()`'s real signal — parameterized by an explicit `task_type` argument (closing the landmine found in §7, so self-edit-generation outcomes and conversational-coding outcomes land in separate, correctly-labeled buckets) — never by `_score_response_quality()`. Consume it through a narrow new function that mirrors `score_model()`'s exact selection logic (same neutral-fallback-below-threshold shape, so the causal-wiring pattern being reused is the one already VERIFIED in §7) but reads the new, isolated file, not the real pickle.

**[COMPILER, per the mission's explicit instruction to separate "existing FeralEcho capability" from "new experimental architecture built from FeralEcho components"]**: this design introduces exactly two new things — a new persisted file and a new, narrow read function — and reuses three things that already exist and already work as claimed: the oracle (`learn_from_sandbox_outcome`'s real signal, classification A, already computed at real volume), the write-pattern (mirroring `learn()`'s existing `stats.setdefault`/incremental-mean shape, already VERIFIED to compile and run), and the causal-consumption logic (`score_model()`'s already-VERIFIED sort-key pattern). It deliberately does **not** claim this as "RiverBrain learning" — it is a new, narrow, purpose-built accumulator that borrows RiverBrain's one proven-good architectural idea while discarding everything about RiverBrain's actual implementation that made it expensive and risky to trust (the singleton, the background thread, the shared classifier, the non-independent dominant signal).

This design, once qualified against the harness threats in §13 of the adversarial review (env inheritance, filesystem-readable answer keys, hash-seed nondeterminism, the sham-transplant provenance gap), is the smallest experiment that could produce a result difficult to explain away by any confound found across three full investigation rounds (the original design, its adversarial review, and this tournament).

---

## 18. What Changed Relative to Both Sept 19 Reports

- **The "RiverBrain is unique" framing is confirmed too strong, independently re-derived a second time** (this mission's own discovery pass, not merely inherited from the adversarial review's finding) — 17 candidates were traced end-to-end, and at least four (RiverBrain, `self_model_claims.py`, `behavioral_state.py`, `task_type_classifier.py`) clear a COMPLETE structural chain.
- **`self_model_claims.py`'s promise, hypothesized by the adversarial review as "may be closer to the desired architecture than RiverBrain," is now directly refuted** by its own dedicated deep dive: it carries zero causal weight over any decision beyond prompt wording, and its accumulated record is entirely corrections-of-false-claims (0 of 23 real records are positive competence gains).
- **`behavioral_state.py`'s best-in-class measured result is now qualified**: the 75% compliance figure was obtained via a path that bypasses a real, previously-unflagged production gating gap (3 of 4 real entry points never reach this mechanism for an ordinary-topic directive).
- **`task_type_classifier.py` enters the tournament as a serious fourth candidate for the first time** — neither Sept 19 report investigated it in this depth; it turns out to be the only candidate structurally capable of genuine novel-transfer, and simultaneously the worst-in-class on accumulation, a genuinely new and consequential trade-off.
- **The mathematical-identifiability finding from the adversarial review is independently reconfirmed by full derivation** (not just cited) and shown to generalize differently across candidates — RiverBrain's is a soft EMA transition, `task_type_classifier.py`'s is a hard permanent freeze, `echo_state.py`'s is a hard short window, and two candidates (`self_model_claims.py`, `behavioral_state.py`) have no such degeneracy at all.
- **RiverBrain's isolation cost is now shown to be worse than previously documented** — a second, converging singleton-resolution path (via Flask's app config) was found in addition to the module-level cache the adversarial review already flagged.
- **A new, previously-undiscussed integrity gap** in RiverBrain's own write-arbitration logic was found: the "never overwrite richer pkl" guard inspects only aggregate observation counts, never the statistic (`model_task_stats`) an experiment would actually care about.
- **The recommended experiment shape changed materially**: both prior reports proposed extending RiverBrain itself (a new parallel field inside the real object). This report recommends a structurally separate, cheaply-isolatable carrier instead, informed by the isolation-cost findings neither prior report had in front of it in this much detail.

---

## 19. Claims That Remain Unsupported

- That any candidate's PERFORMANCE CONSEQUENCE link constitutes demonstrated, general competence improvement — every candidate's evidence here is either UNKNOWN, narrowly SUPPORTED, or (for FAISS retrieval and, in a different sense, `task_type_classifier.py`'s keyword-ladder comparison) directly null/unstable.
- That `task_type_classifier.py`'s soft label-circularity has ever caused a real, observed misclassification cascade — flagged as a structural risk, not caught in the act.
- That RiverBrain's `learn_from_council_rating()` path, now confirmed live, has produced any measurably different downstream outcome versus the path being dead — only its liveness was reconfirmed, not its effect.
- That `self_model_claims.py`'s in-context-reinjection confound has been directly measured (as opposed to architecturally identified) — no experiment isolating "durable knowledge" from "handed-the-answer-every-relevant-turn" has been run on this mechanism.
- That the recommended hybrid design (§17) would actually survive the full harness-qualification battery from the adversarial review — this report designs the connection, it does not build or qualify it.
- That any candidate outside the four primary ones (§3, rows 5–17) has been ruled out with the same depth as the primary four — most of those were surveyed at one pass, not deep-dived.

---

## 20. Exact Questions a Future Codex Review Should Attack

1. Does the recommended hybrid carrier (§17) actually stay immune to RiverBrain's own singleton/thread contamination risk once it's wired into the same process that constructs `RiverBrain`/`EchoCore` — i.e., does merely living in the same Python process reintroduce any of the isolation costs this report claims to avoid by using a separate file?
2. Is `learn_from_sandbox_outcome()`'s real signal (F2 pass/fail) itself free of the answer-key-leakage exploit class the adversarial review found against a *different* proposed oracle reuse — has anyone checked whether the F2 sandbox's own task/test construction shares the same filesystem-read/shared-context vulnerability?
3. Given `task_type_classifier.py`'s hard 100-example freeze, is there any class currently near or past that ceiling in the live production pickle right now, and if so, has "more experience" for that class already gone silently inert without anyone noticing?
4. Does `self_model_claims.py`'s in-context-reinjection confound generalize to *any* other candidate in this survey that renders persisted content back into a system prompt (i.e., is this a systemic property of every "ground-truth slice" mechanism in `echo_ground_truth.py`, not unique to this one module)?
5. RiverBrain's newly-found write-arbitration gap (the "richer pkl" guard never inspects `model_task_stats`) — has this ever caused a real silent regression in production, checkable via any timestamp/observation-count anomaly in the historical pickle's own save log?
6. Is the `council_rating` path's 30%/70% blend (§7) itself vulnerable to the same self-referential-heuristic critique leveled at `learn()`'s dominant path, given that 70% of even the "independent" blend is the same AST-complexity scorer?
7. Has anyone verified `provenance_check.py`'s complete non-integration (§3, Candidate 12) is intentional and not an oversight — i.e., was it built explicitly as a library for future use, or is its zero-caller status itself evidence of an abandoned or incomplete mission?

---

## Integrity Record

```
production changes: NO
files changed: audits/2026-09-19_persistent_competence_candidate_tournament.md (new, this file)
Git HEAD before: 2fba42644c82b9f7096276f4dd338d615cf1bcce
Git HEAD after:  2fba42644c82b9f7096276f4dd338d615cf1bcce
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: none (5 parallel independent investigator subagents launched across two dispatch rounds — the first round's five calls failed on the monthly spend limit before producing any output and were re-dispatched after the limit reset, and two of the second round's five calls failed with a transient connection error and were immediately retried; no FeralEcho/Ollama process touched by this session or by any investigator, per each investigator's own report)
configuration changes: NO
test changes: NO
persistent learning state touched: NO — every isolation/amputation design in this report was specified, not executed, and every investigator was explicitly instructed to design without running anything against real production state
temporary files created: none beyond investigators' own internal working notes (not persisted outside their own agent transcripts)
temporary files cleaned: n/a
orphaned processes: checked, none found
known anomalies: two agent-dispatch failures in the first round (API monthly spend limit, resolved by the user's own limit reset) and two transient connection failures in the second round (immediately retried and completed successfully) — none touched the repository or produced partial/corrupted output; all five investigations that ultimately ran completed cleanly
known deviations from requested methodology: none. All five investigator assignments were covered by genuinely independent (non-fork) agents, each explicitly instructed not to read the prior two reports where candidate-discovery neutrality mattered (Attack-1-equivalent and self_model_claims-hypothesis-equivalent assignments), per the mission's own explicit "do not assume X wins" instruction. This compiling session performed only mechanical synthesis and cross-referencing of the five independent reports into the required 20-section structure and did not substitute its own candidate preference for the evidence produced.
```

---

## Final Question

**"If we were allowed to build exactly one experiment after this review, which existing FeralEcho mechanism or minimal combination of mechanisms gives us the best chance of distinguishing genuine persistent acquired competence from memory, routing, self-description, benchmark exploitation, and statistical artifact — and what observation would kill that claim fastest?"**

The best chance is not any single existing mechanism, but the narrow combination named in §17: the real, already-independent F2 sandbox-execution oracle (the one signal in this entire codebase that clears the evaluator-independence bar without qualification) feeding a small, newly-built, cheaply-isolated carrier that reuses RiverBrain's one proven-good idea — an incrementally-updated, per-(model, task_type) statistic consumed by a real selection decision — without inheriting RiverBrain's singleton, its background thread, its shared classifier, or its self-referential dominant signal. This combination is not itself competence — it is the smallest wiring that would let a real competence signal, if one exists, become visible and testable for the first time in this codebase's history, rather than being either invisible (as in RiverBrain today) or definitionally excluded (as in `behavioral_state.py`) or diary-shaped (as in `self_model_claims.py`) or permanently frozen after 100 examples (as in `task_type_classifier.py`).

The observation that would kill this claim fastest: **a sham-transplant control** — hand-fabricating the exact same `{count, mean}` numbers the real oracle would have produced, injecting them directly without any real sandbox execution ever occurring, and getting an experimentally identical result. Every investigation in this mission converged, independently, on the same underlying mechanical fact — `score_model()`-shaped consumers are pure functions of a tiny numeric carrier with zero built-in notion of provenance — which means this specific control is not optional hardening, it is the single cheapest test that would immediately show whether the whole exercise measured genuine acquired competence or merely proved that a selection algorithm correctly reads two numbers from a file.
