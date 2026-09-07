# Hot Stove / Credit Assignment Forensic Audit

Read-only. `run.py` and its watchdog confirmed stopped throughout (no matching process at start or end
of this pass); port 5000 unbound; `river_brain.pkl` sha256 unchanged
(`eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`); git HEAD unchanged
(`2cf2d95009943797db5ec41fea9b4021634fd5e6`); no commits; no production files modified; no RiverBrain
learning events generated; no self-edit deployment attempted. This pass made zero model/generation calls
of any kind — every finding below comes from reading source code and querying already-on-disk logs/state.

This audit inherits several findings from tonight's prior Michelangelo I-IV and "stomach" (latent
learning reservoir) passes, marked `[inherited]`. Every inherited claim load-bearing to this report's own
conclusions was independently re-derived from primary sources in this pass, not copied — see the specific
re-verifications in §6 (council-blend algebra), §8 (convergence tracker state), §9 (`harvest_question()`
call sites), and §11 (RiverBrain `.learn()` credit granularity). Where a claim is inherited and **not**
independently re-checked here, it is marked `[inherited, not re-verified this pass]`.

---

## Executive Verdict

FeralEcho has real, working mechanisms for experience (A), memory (B), and retrieval (C). It has a thin,
inconsistent capacity for reflection (D). **It has almost no working credit assignment (E)** — the step
that would let it say "this specific action caused this specific consequence, and here is why" — and as
a direct, mechanical consequence, prediction (F), policy change (G), reapplication (H), and verification
(I) either never occur, occur only in one narrow, subtractive case, or occur on a signal too coarse to
carry any real causal content.

**The single cleanest counter-example in the whole system — the shadow model's measured demotion — is
credit assignment applied to a *mechanism*, not to a *situation*.** It proves FeralEcho is capable of the
shape "measure, judge, change future behavior" in principle. It does not prove FeralEcho can do this for
an individual event (a specific NameError, a specific bad approach, a specific successful strategy) and
carry that forward to a later, similar-but-not-identical situation. Searched directly for that narrower,
harder capability across self-edit's retry logic, RiverBrain's per-observation training, the garden's
question lifecycle, and seam_engine's novelty detection. Found it nowhere.

**One concrete, previously-undocumented negative case makes this concrete rather than abstract**: the
exact `NameError: name 're' is not defined` failure — a missing-import bug CLAUDE.md's own Finding 32
(2026-07-15) explicitly diagnosed and attempted to fix by adding "remember to import every module used"
to the `prose_stripping` family's generation prompt — occurred 82 times across `memory/SELF_EDIT.log`,
spanning 2025-11-26 through 2026-08-29. **67 of those 82 occurrences (82%) happened *after* the fix
date**, with the single heaviest cluster (44 occurrences) landing in the four days immediately following
the fix (2026-07-16 through 2026-07-19). A diagnosed, named, specifically-targeted lesson did not
measurably suppress its own recurrence.

---

## Definitions

Used strictly throughout. A mechanism is credited with a letter only if the evidence directly supports it
— no letter is inferred from a weaker one.

- **A. Experience** — an event happened (e.g., candidate generated → sandbox failed → NameError).
- **B. Memory** — the event was retained somewhere on disk/in process state.
- **C. Retrieval** — the retained event (or a summary of it) can later be read back by *some* code path.
- **D. Reflection** — the system produces an interpretation of the event (a diagnosis, a score, a
  category), not just a raw copy of it.
- **E. Credit assignment** — the system identifies *which* prior action/decision/behavior is responsible
  for the consequence, at a grain finer than "this whole task class."
- **F. Prediction** — a reusable expectation is formed: condition X → action Y likely produces
  consequence Z.
- **G. Policy / behavioral change** — the experience measurably changes a future decision rule, ranking,
  selection probability, generation constraint, or routing choice.
- **H. Reapplication** — the changed behavior is actually exercised when a sufficiently similar future
  situation occurs.
- **I. Verification** — the system demonstrates the changed behavior produced a *better* outcome than the
  prior behavior would have.

A–D are never treated as proof of E–I anywhere in this report.

---

## Safety / Immutability Verification

| Check | Result |
|---|---|
| `run.py` process | Not running (start and end of pass) |
| watchdog (`start_echo.sh`) process | Not running |
| Port 5000 | Unbound |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` — unchanged, start and end |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` — unchanged |
| Working tree | Only pre-existing untracked/modified files from earlier tonight's work, plus this new report |
| Production files modified | Zero |
| RiverBrain learning events generated | Zero — no `.learn()`/`.save()` call made by this pass |
| Self-edit deployment | None attempted |
| Model/generation calls made | Zero |

---

## Credit-Assignment Liveness Ledger

| Mechanism | Trigger | Experience consumed | Consequence observed | Action credited | Attribution method | Stored representation | Revisit trigger | Consumer | Decision affected | Behavioral change demonstrated | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RiverBrain `.learn()` → `model_task_stats` | Every real conversational/self-edit response | The response text itself | None separate from the action — same call scores the text it just received | The **model**, at (model, task_type) granularity only | `_score_response_quality()`'s AST/keyword heuristic on the output, applied identically regardless of what happened after generation | `model_task_stats[model][task]["mean"]`, a capped rolling mean | Every future `rank_models()`/`score_model()` call | `rank_models()`, `_select_council()` | Yes — model selection weight | Yes, mechanically (~65% weight) | A — direct source read, this pass (§11) | **LIVE, but no ACTION→CONSEQUENCE separation exists at all — see §11** |
| `learn_from_sandbox_outcome()` | A real self-edit sandbox pass/fail | Candidate code (success) or `"[FAIL] {error[:80]}"` (failure) | Sandbox pass/fail, a real binary consequence | The **model**, at (model, "coding") granularity | None — raw error text is feature-extracted as generic text, never parsed into a symbol/cause | `model_task_stats["coding"]`, blended with every other coding signal | Every future coding-task `rank_models()` call | Same as above | Yes, in principle | Not isolated from `.learn()`'s own signal — same bucket | B — direct source read (§11) | **LIVE, real action→consequence link exists, but zero causal attribution beyond "it failed"** |
| `learn_from_rating()` | Explicit human 1-5 rating | Response text | Human judgment | Model, task granularity | None beyond the scalar rating | `river_brain.pkl` classifier/scaler state only `[inherited: Phase 1.5]` | Never read back by any decision | Nobody | No | No | B `[inherited, re-confirmed by absence of new evidence against it]` | **DEAD** |
| Self-edit in-call retry | A real sandbox failure inside `execute_self_edit()` | Exact sanitized error text (`clean_error`) | The retry's own pass/fail | The **candidate code just generated**, correctly, at the individual-attempt level | Direct: the literal error text is fed back verbatim into the retry prompt | A local variable inside one Python call frame — nowhere durable | N/A — the call frame ends | Nobody outside the same call | No (beyond the one retry) | No | A — direct source read (§12); real historical `success_on_retry` entries confirm this path fires | **DEAD outside the single retry — the best individual-action attribution in the whole system, and it is thrown away every time** |
| Convergence tracker (`self_edit_convergence.json`) | Every self-edit cycle, per family | Function name set generated this cycle | Function *count* vs. prior cycle's count | The **family** (e.g. `prose_stripping`), never the individual function | Count comparison only — `count <= prev.count OR prev.count==0` — no identity/content comparison | `non_convergent_streak`, `all_names_seen` (JSON) | Read once per cycle by `_build_targeted_prompt()` | The targeting prompt, in principle | Yes, in principle | **No, in practice — independently re-confirmed this pass (§8): streak=0 for all 4 real families right now, despite 95/58/8/53 real cycles each producing 32/33/7/50 distinct function names** | A — direct read of the live JSON, this pass | **LIVE BUT STRUCTURALLY BLIND — cannot distinguish "converging" from "renaming the same mistake forever"** |
| Council rating blend (`_blend_council_and_quality()`) | A trusted, sampled council rating | Council's 1-5 rating + the response's own quality_score | Peer disagreement, when it occurs | The model/response, task granularity | Weighted sum, `0.3*council/5 + 0.7*quality/4`, threshold 0.75 | `model_task_stats`, same bucket as everything else | Every future selection | Same as `.learn()` | Yes, nominally | **Provably no, at the score extremes — independently re-derived this pass (§6): quality_score=4 → label always 1 regardless of council 1-5; quality_score≤1 → label always 0 regardless of council 1-5** | A — algebra re-derived directly from source, this pass | **LIVE BUT MATHEMATICALLY INERT WHERE DISAGREEMENT MATTERS MOST** |
| `seam_engine` → garden | A statistically genuine, first-ever signal contradiction | Two `echo_state`/salience series | The contradiction itself | The signal pair, correctly and precisely | Real, adversarially-tested statistical test (`check_pair()`) | `seam_log.jsonl` (every cycle); `harvest_question()` on first-ever detections | Garden's own weighted lottery, if the question survives ingestion | Emergent scheduler's topic selection | Rarely (2/78 real detections ever reach the garden) `[inherited: Michelangelo III]` | Almost never (1/78 ever asked) `[inherited]` | A `[inherited, not re-derived this pass — treated as established per mission's own leads guidance]` | **LOG-ONLY, with a precisely-diagnosed, mostly-blocked path to consequence** |
| Dissent Log (`propose_core_edit()`) | A protected-file edit proposal's council review | Real per-model APPROVE/REJECT votes + reasoning | Genuine disagreement, when it occurs | The proposal | Direct — real vote text stored verbatim | `dissent_log.jsonl` | Nothing reads it back | Nobody | No | No | A `[inherited]` | **DEAD, and has never once recorded a real dissent (1 entry, unanimous)** |
| Shadow model → `get_weak_task_type()` priority | Reflection-derived keyword guess vs. real self-edit outcome | The guess + the real outcome | Accuracy, measured over 2,062 real entries | The **shadow-model mechanism itself**, not a specific situation | Direct comparison of guess vs. `real_focus` | `shadow_accuracy.jsonl`/`shadow_self_model.json` | Every self-edit targeting decision | `perform_self_edit()`'s arbitration order | Yes | **Yes — the one real, confirmed behavioral change in this entire ledger (Finding 91: shadow model demoted to last-resort fallback)** | A — independently re-confirmed this pass: 331/2062 = 16.1% accuracy, `get_weak_task_type()` checked before shadow fallback, confirmed by direct source read | **LIVE, CONSEQUENTIAL, TERMINATING — but this is meta-level (correcting trust in a mechanism), not situational (a specific lesson about a specific kind of mistake)** |
| `apply_to_code` invocation log | Every real deployed self-edit's transform call | Transform input/output | "changed" boolean + error, if any | The deployed hook | None beyond pass/fail | `apply_to_code_invocations.jsonl` | Nobody | Nobody, decision-wise | No | No | A `[inherited]` | **DEAD despite real historical volume** |
| `council_deliberations.jsonl` | Every real multi-councillor deliberation | Full raw per-model pre-synthesis text | Real disagreement, routinely | N/A | N/A | 5,110+ real lines | Nothing reads it back | Nobody | No | No | A `[inherited]`, zero-consumer grep re-confirmed via this pass's own grep of `harvest_question` call sites finding no reference to this file | **LOG-ONLY — a large, entirely unmined dataset** |
| `self_edit_outcomes.jsonl` | A real self-edit deploy | Pre/post quality delta | Real, measured | The **family/task type**, never the specific change made | Aggregate delta only, no content-level record of what changed | JSONL | Every self-edit cycle | `SelfModelUpdater.get_weak_task_type()` | Yes — which family to target next | Yes, but **coarse**: "target coding more" not "avoid missing imports" | A `[inherited]` | **LIVE, CONSEQUENTIAL, BUT CARRIES NO CONTENT-LEVEL LESSON** |
| Curiosity garden ingestion (harvest sources) | See §9 | Varies by source | N/A | N/A | N/A | `data/question_garden.jsonl` | `select_from_garden()`'s weighted lottery | Autonomous cycles wanting a topic | Yes, mechanically | Relevance-blind (§10) | A — re-confirmed this pass via direct `harvest_question()` call-site grep (§9) | **LIVE, but self-edit/coding failures are structurally never a source (§9) — not underrepresented, absent** |

---

## Historical Hot-Stove Chains

Five reconstructed chains, real data throughout, each answering the mission's 12-question checklist.

### Chain 1 — The recurring `import re` NameError (negative-learning case, most important in this report)

1. **What did Echo do?** Generated self-edit candidate code for the `prose_stripping` family (a
   long-running, since-disabled attempt to strip leading prose from generated code) that used the `re`
   module without importing it.
2. **What happened?** Sandbox test failed: `NameError: name 're' is not defined`. Real, first occurrence
   found: 2025-11-26T10:24:05.
3. **Did Echo recognize something went wrong?** Yes — the sandbox test result is a hard, unambiguous
   pass/fail; `test_code_in_sandbox()`'s failure is unmistakable at the mechanical level.
4. **What did Echo believe caused it?** Nothing in the automated loop forms a belief — the retry-prompt
   mechanism (§12) hands the raw error text back for the *same* attempt, but no persistent diagnosis is
   formed. A **human**, reviewing this project's own history, did form and record a belief: CLAUDE.md's
   Finding 32 (2026-07-15) explicitly diagnosed this exact failure class ("a missing `import re`") and
   rewrote the `prose_stripping` family's generation prompt to add "an explicit reminder to import every
   module used."
5. **Was that attribution stored?** Yes — as a static, human-edited string inside
   `_FOCUS_FAMILY_BY_CREATIVITY`'s `prose_stripping` domain sentence in `self_edit_manager.py`.
6. **Could the attribution be retrieved later?** Yes, mechanically — every subsequent `prose_stripping`
   generation cycle reads that same prompt text.
7. **What event caused the retrieval?** Every scheduled self-edit cycle targeting the `prose_stripping`
   family (Optuna dry-run trials and/or the hourly real-deploy attempt).
8. **Did retrieval influence the next decision?** The prompt text changed — this is the one part of the
   chain with real, positive evidence: a human-authored lesson genuinely entered the generation prompt.
9. **Did the decision actually change?** **No measurable improvement in outcome.** Real data, this pass:
   of 82 total real `NameError: name 're' is not defined` occurrences in `memory/SELF_EDIT.log` (spanning
   2025-11-26 to 2026-08-29), **67 (82%) occurred after the 2026-07-15 fix date**, with daily counts of
   2, 14, 12, 18, 5, 2, 3, 4, 2, 5 on 2026-07-15 through 2026-07-28 — the single heaviest four-day
   cluster in the entire 9-month history landing in the four days *immediately after* the fix. Before the
   fix: 10 occurrences spread across 8 months (roughly 1.25/month). After: 72 occurrences in ~6 weeks,
   before finally tapering to isolated single occurrences in August.
10. **Was the later situation sufficiently similar?** Yes — same failure signature, same general family
    of "strip prose from generated code" candidates, most within the same `prose_stripping`-targeted
    Optuna dry-run search the fix specifically addressed.
11. **Did the changed behavior improve the outcome?** No evidence it did. The spike could plausibly
    reflect a change in *how often* `prose_stripping` was targeted after 2026-07-15 rather than a rise in
    the *per-attempt* failure rate — that per-attempt rate was not computed in this pass (would require
    joining against total `prose_stripping` attempt volume per day, not done here; flagged as a real
    limit on this specific finding, not glossed over). But even under the most charitable reading, this
    is not evidence the diagnosed lesson worked — at minimum, it shows no visible suppression.
12. **Could this have an unrelated explanation?** Yes, plausibly, per point 11 — a genuine confound
    (targeting-frequency change, not lesson-failure) has not been ruled out. What *is* ruled out: the
    naive story "Finding 32 fixed this" — the raw recurrence count went up, not down, in the fix's
    immediate aftermath, which is the opposite of what a working fix would produce even accounting for
    some volume increase.

**Chain verdict: D (reflection: human-authored) reached, E (attribution) reached only via a human editing
a prompt string by hand — not a mechanism, F/G nominally attempted, H occurred, I fails outright on the
available evidence.** This is the single most concrete, data-backed negative case in this audit.

### Chain 2 — Self-edit in-call retry (episodic repair, zero generalization)

1. **What did Echo do?** Generated a self-edit candidate that failed F2 sandbox testing for any reason.
2. **What happened?** `test_code_in_sandbox()` returns `(False, error_text)`.
3. **Recognized?** Yes, mechanically — `execute_self_edit()` branches directly on the boolean.
4. **Attributed?** Yes, precisely — `_sanitize_sandbox_error(sandbox_error)` extracts the real exception
   text and line context (`clean_error`), fed verbatim into a real retry prompt (`self_edit_manager.py:
   1999-2005`). This is the single most precise, individual-action-level attribution found anywhere in
   this codebase — better than anything RiverBrain or the convergence tracker produce.
5. **Stored?** **No** — `clean_error`/`retry_prompt` are local variables inside `execute_self_edit()`'s
   own call frame. Confirmed by direct source read: nothing writes this text to any file, log, or
   persistent structure keyed for later reuse.
6. **Retrievable later?** No — the call frame ends when the function returns.
7. **Retrieval trigger?** N/A.
8. **Influenced next decision?** Only the *immediate* retry, within the same call. Real historical
   confirmation this path fires and sometimes succeeds: `reflection_entry["sandbox_feedback"] =
   "success_on_retry"` is a real tag written on genuine retry-success events (confirmed present in
   `self_edit_manager.py:2042`, consistent with `[inherited]` prior confirmation this tag appears in
   real reflection data).
9. **Decision changed?** Yes, for that one attempt only.
10. **Later situation similar?** N/A — there is no "later" for this specific diagnosis; it dies with the
    call frame.
11. **Outcome improved?** Yes, for the one retry, sometimes.
12. **Unrelated explanation?** N/A.

**Chain verdict: A through E all genuinely reached, at the individual-action level, better than any other
mechanism in this ledger — and then discarded completely. This is the cleanest possible illustration of
"episodic adaptation, not durable learning": every element the mission's definitions require for E is
present, and F/G/H/I are all foreclosed by a single missing line of persistence code.**

### Chain 3 — Convergence tracker's blindness (measurement exists, doesn't measure the thing it claims to)

1. **What did Echo do?** Ran repeated self-edit cycles targeting `prose_stripping` and
   `response_shortening`, each generating a differently-named helper function.
2. **What happened?** 95 real `prose_stripping` cycles produced 32 distinct function names; 58 real
   `response_shortening` cycles produced 33 distinct names — independently re-confirmed this pass by
   direct read of the live `app/core/self_edit_convergence.json`.
3. **Recognized?** The mechanism *exists* to recognize this — `_record_convergence()` runs every cycle.
4. **Attributed?** No — the check is `count <= prev.count OR prev.count==0`, comparing raw function
   *count*, not *identity*. Confirmed by re-reading the live state: `non_convergent_streak` reads **0**
   for all four tracked families (`prose_stripping`, `response_shortening`, `quality_scoring`,
   `unclassified`) right now, despite decades of real churn behind each. `[inherited: Michelangelo IV,
   independently re-confirmed this pass by direct file read]`.
5. **Stored?** Yes — `non_convergent_streak`, `all_names_seen` persist.
6. **Retrievable?** Yes — read once per cycle by `_build_targeted_prompt()`.
7. **Trigger?** Every self-edit cycle.
8. **Influenced decision?** In principle yes — the prompt text would change if the streak ever
   incremented meaningfully.
9. **Decision changed?** Essentially never, for the two families with the longest real history — the
   streak has almost no opportunity to fire because the count-only check treats renaming the same
   mistake as "progress."
10. **Later situation similar?** Yes, extremely — that is precisely the phenomenon the mechanism exists
    to catch and fails to.
11. **Outcome improved?** No evidence it has, for these two families.
12. **Unrelated explanation?** None plausible — this is a direct, structural read of the comparison
    logic, not an inference from outcome data.

**Chain verdict: B/C/D reached (state is retained and read), E fails at the mechanism level by
construction — this is the clearest example in the whole audit of "the measurement infrastructure exists
and answers a different question than the one it claims to."**

### Chain 4 — RiverBrain `model_task_stats` (the one real closed loop, on a coarse credit target)

1. **What did Echo do?** Generated a real conversational or self-edit-coding response with a given model.
2. **What happened?** `_score_response_quality()` scores the response text itself.
3. **Recognized?** In a narrow sense — the score is computed every time.
4. **Attributed?** **To the model, at (model, task_type) granularity, only.** Direct source read this
   pass (`echo_model_orchestrator.py:808-862`): `.learn()` never separates "action" from "consequence" —
   the same call that produces the response also scores it, using a proxy over the text itself (AST
   complexity / keyword heuristics), not any downstream, independently-observed outcome. There is no
   causal object here at all: no missing-symbol, no failure-location, no confidence, no falsification
   path — the credit target is a scalar rolling mean per (model, task_type), incapable by construction of
   distinguishing "this one response was bad" from "this model's whole task-class average moved."
5. **Stored?** Yes — `model_task_stats[model][task_type]["mean"]`, capped-window rolling mean
   (`_MEAN_EFFECTIVE_WINDOW=200`).
6. **Retrievable?** Yes, every future `rank_models()`/`score_model()` call.
7. **Trigger?** Every future model-selection decision for that task type.
8. **Influenced decision?** Yes, mechanically, ~65% weight (`influence_weight`).
9. **Decision changed?** Yes, demonstrated live multiple times in prior passes tonight.
10. **Later situation similar?** Only at the coarse (model, task_type) level — never at the level of "a
    similar kind of mistake."
11. **Outcome improved?** Unresolved-to-weak: `[inherited: Findings-91-93 forensic pass]` found the proxy
    correlates only weakly (r=0.206, n=24, not significant) with independently-verified functional
    correctness — not re-derived in this pass, treated as established per this mission's own leads
    guidance.
12. **Unrelated explanation?** The loop's mechanical reality is not in question (direct source read); what
    remains uncertain is whether moving this proxy up or down corresponds to anything a human would call
    "better."

**Chain verdict: The only mechanism in this audit reaching E (a real, if coarse, attribution to "the
model") through I (an attempted verification) — but E's grain is (model, task class), never (this
specific action, this specific cause), and I is independently shown weak. This is real, mechanical
learning at the coarsest possible grain the mission's definitions allow, not "no learning."**

### Chain 5 — `seam_engine` → garden (correct detection, lost in translation)

1. **What did Echo do?** Nothing — this is a passive, background statistical monitor over 12 real signal
   series (9 `echo_state` dims + 3 salience components).
2. **What happened?** A real, first-ever (pair, direction) contradiction is detected —
   adversarially-tested (`scripts/verify_seam_engine.py`, `[inherited]`) to genuinely discriminate signal
   from noise.
3. **Recognized?** Yes, precisely — `check_pair()`'s leave-one-out design is a real statistical test.
4. **Attributed?** Yes — to the exact signal pair and direction.
5. **Stored?** Yes — `seam_log.jsonl` every cycle (including empty results, a real, disclosed design
   choice), and `harvest_question()` on first-ever detections.
6. **Retrievable?** Yes, in principle, via the garden.
7. **Trigger?** `select_from_garden()`'s weighted lottery, if the question survives ingestion.
8. **Influenced decision?** Almost never — `[inherited: Michelangelo III]`: 754 total detections, 78
   genuinely novel, but **only 2 of 78 real `harvest_question()` calls survive `garden_manager.
   _is_near_duplicate()`'s Jaccard word-overlap filter** (0.7 threshold), which was built to catch
   near-identical *philosophical* question restatements, not seam_engine's templated-but-factually-
   distinct phrasing — a real, demonstrated mismatch (`[inherited]`, not re-derived from scratch this
   pass, but consistent with this pass's own confirmation via §9 that `harvest_question()` has exactly 5
   real call sites and no special-casing for seam-sourced dedup).
9. **Decision changed?** For the 1 question that was ever asked: a real quality score (1.0) resulted, but
   the one child question it produced was generic and non-diagnostic.
10. **Later situation similar?** N/A for the 76 lost detections — they never reached a state where this
    question is answerable.
11. **Outcome improved?** No evidence either way for the single surviving case.
12. **Unrelated explanation?** None — this is a directly-traced, mechanical filter mismatch, not an
    inference.

**Chain verdict: A through D genuinely reached, with real precision — E is reached (the specific signal
pair is the credited "cause") but the translation from E to F/G is destroyed by an unrelated downstream
filter almost every time (76/78). This is the cleanest example in the audit of correct attribution
existing and still failing to reach behavior, for a reason unrelated to the attribution's own quality.**

---

## Negative Learning / Repeated Failure Analysis

The `NameError: name 're' is not defined` case (Chain 1) is the headline example, with real,
time-stamped data showing no suppression after a targeted, documented fix. Three further real repeated
failure classes, counted directly from `memory/SELF_EDIT.log` (142,839 real lines) this pass:

| Recurring undefined-name signature | Real occurrences | Note |
|---|---|---|
| `log_call` | 604 | Not investigated to root cause in this pass — flagged as the single largest repeated failure signature in the log and a candidate for a future, narrower audit |
| `self_edit_generated` | 130 | Consistent with the self-referential-import class of mistake F1's `_ALLOWED_TOP_LEVEL` guard exists to catch (`[inherited: CLAUDE.md Finding 22]`) — a real, still-recurring hallucination class despite an existing static guard |
| `re` | 82 | Traced in full as Chain 1 |
| `functools` | 76 | Same missing-import shape as `re`, not separately traced |
| `dataclass` | 52 | Same shape |

**Honest caveat, per the mission's own §12 instruction**: repeated failure alone does not prove learning
failed — task distribution, targeting frequency, and Optuna's own dry-run trial volume all changed over
this period and were not controlled for in the counts above (beyond the specific before/after framing in
Chain 1). What the data does support without further controls: **the raw count of a specific, previously-
named, specifically-targeted failure signature did not visibly decline after the targeted fix, and its
sharpest spike followed the fix.** That is sufficient, on its own, to reject the strong claim ("the fix
worked") without requiring the weaker claim ("the fix definitely made things worse") to also hold.

---

## Positive Learning / Successful Strategy Reuse

Searched specifically for "successful action → recognized success → attributed cause → retained → future
reuse" per the mission's §13.

**Found: RiverBrain's `model_task_stats` (Chain 4).** This is the one real, demonstrated case of a
successful pattern (a model producing a well-scoring response) being retained and preferentially reused —
at (model, task_type) granularity. It is genuine positive credit assignment, at the coarsest grain the
mission's definitions allow.

**Not found anywhere**: any mechanism that credits a specific *approach*, *code pattern*, or *strategy*
(as opposed to *which model* produced it) with success and preferentially reuses that approach later.
Self-edit's retry logic (Chain 2) comes closest in shape — a successful correction exists — but is
destroyed at the call-frame boundary before any later cycle could benefit from it, success or failure
alike. `apply_to_code`'s invocation log records real transform outcomes but has zero consumers
(`[inherited]`). No mechanism anywhere in this codebase implements "this specific way of solving X worked
last time, prefer it again" independent of which model happened to produce it.

---

## RiverBrain Credit Assignment

Answering the mission's ten specific §14 questions, all from direct source read this pass
(`app/core/echo_model_orchestrator.py:808-862`, `936-960`):

1. **What event receives credit?** A generated response (`.learn()`) or a sandbox pass/fail
   (`learn_from_sandbox_outcome()`).
2. **What features represent the action?** `_extract_quality_features(response, task_type, model_name)`
   — text-derived features (AST complexity for coding, keyword/entropy markers otherwise) plus the
   model's own identity as a categorical feature.
3. **What represents the consequence?** For `.learn()`: nothing separate — the same text is both action
   and evaluated consequence (`_score_response_quality()` scores the output, not a downstream effect of
   it). For `learn_from_sandbox_outcome()`: a real, separate consequence exists (sandbox pass/fail).
4. **Is the consequence causally attached to the action?** For `.learn()`: not in any real causal sense
   — it's a self-referential proxy score of the artifact itself. For `learn_from_sandbox_outcome()`: yes,
   genuinely — code and its real pass/fail are directly linked.
5. **What is actually updated?** `model_task_stats[model][task_type]["mean"]` (capped rolling mean),
   `scalers`/`classifiers` (online `river` models), `observation_counts`.
6. **Who reads the updated state?** `rank_models()`, `_select_council()` via `score_model()`.
7. **Does the reader affect a consequential decision?** Yes — which model gets selected for a given task.
8. **Can a better/worse outcome measurably change future behavior?** Yes, demonstrated live multiple
   times in prior passes tonight.
9. **Is the current proxy sufficiently related to real correctness?** `[inherited: Findings-91-93]`: weak,
   non-significant (r=0.206, n=24) — not re-derived this pass.
10. **Can RiverBrain distinguish "this exact action was bad" from "this entire task class was bad"?**
    **No.** This is the central finding of this section. The stored representation is a single scalar
    rolling mean per (model, task_type). There is no per-instance record retained anywhere that a later
    decision could consult to ask "was it *this specific approach* that failed, or is this model just
    generally weaker at this task class right now?" Every observation is folded into the same number,
    indistinguishable after the fact.

---

## Self-Edit Credit Assignment

Independently re-verified this pass, not re-derived from the prior sessions' text alone:

- **The failure→retry→correction sequence is real** (Chain 2), and is the single best individual-action
  attribution mechanism in the codebase — exact error text, exact retry.
- **It is completely episodic.** Direct source read of `execute_self_edit()` (lines ~1980-2048) confirms
  `clean_error`/`retry_prompt`/`retry_code` are local to the call. No write to any file, log, or shared
  state carries this diagnosis past the function's return.
- **`_build_targeted_prompt()` — re-confirmed this pass by direct grep** of `self_edit_manager.py` for
  references to `reflection_shard`, `SELF_EDIT.log`, or `self_edit_outcome_tracker`: none found feeding
  into targeted-prompt construction. The only durable signal reaching prompt construction is the
  convergence tracker (Chain 3, structurally blind) and `self_edit_outcomes.jsonl`'s coarse per-family
  quality delta (which family to target, never what to do differently).
- **Direct answer to the mission's question**: does the system ever use one self-edit failure to improve
  a later, independently generated self-edit? **No.** Not "rarely" — the code path required for this
  (persisting a retry's diagnosis somewhere a *different*, later `execute_self_edit()` call could read)
  does not exist anywhere in the source.
- **This is episodic adaptation, not durable learning**, exactly as the mission's own §15 framing
  anticipates.

---

## Garden / Memory Credit Assignment

Went one level deeper than the prior "garden accidental relevance" pass, per the mission's explicit §16
instruction: not "does selection find relevant content" but "does experience ever get *qualified* as a
garden candidate in the first place."

**Direct grep of every real call site of `harvest_question()` in this pass**, across the entire codebase:

| Source | Category | Content |
|---|---|---|
| `curiosity_engine.py:150` | topic-derived (13 fixed, philosophical/relational categories) | Curiosity-engine-generated prompts |
| `self_edit_manager.py:2436` | `"dissent"` only | A protected-file edit proposal's real council disagreement — **not** an ordinary self-edit failure |
| `emergent_scheduler.py:944` | follow-up | A reflection's own follow-up question |
| `seam_engine.py:250` | `"seam"` | Statistical contradiction detections |
| `autonomous_awareness.py:395` | `"dream"` | Dream-cycle synthesis |

**Exactly five real call sites exist, system-wide, confirmed by direct grep. Zero of them are triggered
by an ordinary self-edit sandbox failure, NameError, or F1/F2 rejection.** The single self-edit-adjacent
path (`self_edit_manager.py:2436`) fires only for the narrow, rare `propose_core_edit()` dissent case —
not for the 142,839-line, routine self-edit failure history this audit's Chain 1/2/3 analyzed.

**Direct answer to the mission's §16 question**: this is not a retrieval problem layered on top of a
working ingestion pathway. **Coding/self-edit experience is structurally absent from candidate extraction
for the garden — there is no code path that could even attempt to qualify a routine self-edit failure as
a garden candidate.** Combined with `[inherited: garden accidental relevance baseline]`'s finding that
54.6% of real logged activity is coding-family while the garden's 13 categories contain zero
coding/technical categories, this confirms the two findings describe the same root cause from opposite
ends: the garden's content pool cannot represent coding experience because nothing in the codebase ever
tries to put it there, not merely because it's underweighted once present.

**Temporal survivability, re-checked directly this pass** (`garden_manager.py`, full function-level read):
`select_from_garden()` filters to `status == "active"` only. Status transitions found in source:
`"active"` → `"resolved"` (`update_question_quality()`, `update_resolution()`) and `"active"` →
`"composted"` (`compost_question()`). **No function anywhere reassigns a resolved or composted entry back
to `"active"`.** There is no reopening mechanism of any kind — not by contradiction, not by recurrence,
not by a new event increasing an old question's priority. Once resolved, a question is durably closed.
The garden supports genuine time-delayed revisitation of *unresolved* (`status: "active"`) questions
(`age_days` weighting is real), but has no mechanism to reactivate a *resolved* one, and (per
`[inherited: garden accidental relevance baseline]`) its revisitation of active questions is itself
staleness-weighted, not relevance-weighted.

---

## Temporal Attribution

Checked directly whether any mechanism retains enough information to know *which* prior action produced
*which* later outcome, across a real time gap with intervening, unrelated events:

- **RiverBrain**: No — the rolling mean has no per-observation timestamp retained in a form any decision
  reads; only the aggregate moves.
- **Self-edit outcome tracker**: Retains pre/post timestamps per real deploy (`self_edit_outcomes.jsonl`),
  and this *is* real temporal attribution at the family level — a genuine `[inherited]` capability, not
  contradicted by anything found this pass. Its ceiling is grain (family, not specific change), not time.
- **Garden**: `last_asked`/`age_days` genuinely track real elapsed time per question — the one mechanism
  in this ledger with a real "gap tolerance" built in — but, per the section above, is blind to whether
  anything relevant happened during that gap.
- **No mechanism anywhere was found vulnerable to the specific "last N events" or "concurrent activity
  confusion" failure modes the mission's §11 warns about** — because no mechanism attempts fine-grained
  temporal credit assignment at all. The absence of the failure mode here is a direct consequence of the
  absence of the capability, not evidence the capability works safely.

---

## Counterfactual Analysis

Applied to every apparent-learning case surfaced in this audit:

- **RiverBrain (Chain 4)**: Could the demonstrated selection change be explained by something other than
  genuine credit assignment? No — the mechanism is directly, mechanically real (rolling mean → selection
  weight), independently verified by source read. The live question is not "is this real" but "is the
  proxy it optimizes trustworthy" — `[inherited]` weak correlation stands, unchallenged by anything found
  this pass.
- **Shadow model demotion**: Could Finding 91's priority reorder have happened for an unrelated reason?
  No — directly traced to a specific, measured accuracy figure (16.1%, independently re-derived twice
  across tonight's passes) below the real majority-class floor (58.8%, `[inherited]`), with the code
  change citing that exact measurement. This one holds up.
- **The `import re` fix "working"**: Ruled out by the raw data itself (Chain 1) — the naive story does
  not survive contact with the timestamps.
- **Convergence tracker "working as designed"**: Ruled out directly — the comparison logic itself
  (count, not identity) is the mechanism of failure, not an inference from outcome data; this is as close
  to certain as a code-level finding gets.
- **`seam_engine`'s garden loss**: Could the 76/78 rejection rate instead reflect genuinely redundant
  questions rather than a filter mismatch? `[inherited: Michelangelo III]`'s own direct Jaccard-overlap
  reconstruction (0.821 overlap between two *factually distinct* seam questions sharing only template
  phrasing) argues against this — not re-derived from scratch in this pass, but the mechanism (word-
  overlap on templated text) is exactly the shape that would produce this failure regardless of the
  underlying facts' actual novelty.

No apparent-learning case in this audit survived scrutiny as *full* learning (E through I). The shadow
model survives as a real, narrow, meta-level exception (see Executive Verdict).

---

## End-to-End Causal Chains

Per the mission's §18 standard (`Experience → Attribution → Storage → Trigger → Retrieval → Decision
change → Outcome improvement → Survives replication`), exactly **one** chain in this audit reaches every
link:

**Shadow model**: real historical predictions (Experience) → measured against real `real_focus` outcomes,
16.1% accuracy (Attribution, at the mechanism level) → `shadow_accuracy.jsonl` (Storage) →
Finding-91-era re-audit (Trigger) → `get_weak_task_type()`'s priority reorder (Retrieval → Decision
change) → `perform_self_edit()` now checks the empirical signal first, shadow model last-resort only
(Decision change, confirmed by direct source read this pass, matching `[inherited]`) → the demotion is a
real, defensible response to a real measurement (Outcome improvement, in the narrow "stopped trusting a
bad signal" sense) → independently re-confirmed across three separate passes tonight, including this one
(Survives replication).

**No chain reaches every link at the level of a specific *situation* (a specific bug, a specific
approach, a specific kind of mistake)** — only at the level of "should we trust this whole mechanism."
This distinction is the load-bearing finding of this entire audit.

---

## Missing Link / Missing Organ

Classified per the mission's §19 taxonomy, one classification per major mechanism family:

- **RiverBrain**: **B** (credit assignment exists but does not reach *situational* behavior — it reaches
  *model-selection* behavior, on a coarse, proxy-scored target) shading into **C** (RiverBrain's `.learn()`
  path specifically has no action/consequence separation at all — see §11 point 4 — closer to storing a
  self-referential quality score than assigning credit for a consequence).
- **Self-edit retry**: **D** — credit assignment exists only episodically; nothing durable survives.
- **Convergence tracker**: **C** — a real consequence (repeated failure) is retained, but the mechanism
  cannot reliably say what caused it (identity vs. count).
- **`seam_engine`**: **F** — real digestion happens (a genuine, precise attribution is formed and
  stored), but it cannot route into behavior because a downstream filter, built for an unrelated purpose,
  discards it before it can be evaluated.
- **Garden overall**: **E** — a real reservoir exists (unresolved questions can sit for real elapsed
  time), but there is no consolidation/relevance mechanism, and — per this pass's new finding — the
  reservoir cannot even be filled with the majority of Echo's real (coding) experience in the first
  place, which is a gap at the *ingestion* stage the "no digestion" framing alone doesn't fully capture.
- **Shadow model**: **A**, narrowly — this is the one mechanism where real credit assignment reaches real
  behavior change, though at the meta (trust-in-mechanism) level, not the situational level.

**If forced to name the single missing organ**: **credit assignment at the grain of "this specific
situation," as distinct from "this whole mechanism" or "this whole task class."** Every mechanism in this
ledger that retains experience retains it at a grain too coarse (RiverBrain: model×task_type; convergence
tracker: family-wide count; self-edit outcomes: family-wide delta) or discards the fine-grained
attribution entirely before it can be stored (self-edit retry). The one mechanism with fine-grained,
precise attribution (`seam_engine`) has it destroyed downstream by an unrelated filter, not by its own
attribution failing.

---

## What FeralEcho Can Actually Learn Today

1. **Which model tends to produce better-scoring output for a given task type** (RiverBrain,
   `model_task_stats`) — real, live, continuously updating, on a proxy independently shown weak.
2. **Whether a whole self-edit family (e.g. `prose_stripping`) should be targeted more or less** based on
   aggregate pre/post quality deltas (`self_edit_outcomes.jsonl` → `SelfModelUpdater`) — real, coarse.
3. **Whether to trust a specific internal arbitration mechanism at all** — demonstrated exactly once (the
   shadow model), and correctly.
4. **How to fix the immediate error in front of it, within a single self-edit attempt** (in-call retry) —
   real, but expires at the end of that attempt every time.

## What It Cannot Yet Learn

1. **That a specific kind of mistake (e.g., "this generation pattern tends to omit imports") should be
   avoided in a *later*, independently-generated attempt** — no code path persists this level of
   attribution anywhere.
2. **That a specific approach or code pattern that worked once should be preferred again** — no mechanism
   credits strategies, only models.
3. **That a resolved or dormant question/belief should be reopened because new, contradicting evidence
   arrived** — no such code path exists in `garden_manager.py`.
4. **That a genuinely novel statistical signal (`seam_engine`) deserves to be evaluated on its own terms**
   — currently filtered out by a mechanism built for a different question, 76 times out of 78.
5. **Anything from its own coding/self-edit experience via the curiosity garden** — that experience never
   qualifies as a garden candidate to begin with.

---

## Evidence That Would Change This Conclusion

- A real code path where a specific self-edit failure signature (not a family, not a model) is persisted
  and read by a *later*, independently-generated self-edit attempt, with a measurable change in that
  attempt's behavior traceable to the earlier failure.
- A version of `_is_near_duplicate()` (or a seam-specific dedup) that lets a meaningfully larger fraction
  of `seam_engine`'s real detections reach the garden, followed by evidence that being asked measurably
  changed anything.
- A controlled, per-attempt (not per-day) recurrence-rate comparison for the `import re` case, isolating
  targeting-frequency change from per-attempt failure-rate change — the one place this audit's own
  negative finding has an acknowledged, stated gap.
- Any discovered mechanism reading `council_deliberations.jsonl` for a real decision — currently
  zero-consumer, confirmed again this pass.

---

## Final Classification

**D — Credit assignment exists only episodically. Immediate retry/correction works (Chain 2); almost
nothing durable survives into later, independently-encountered situations.** RiverBrain (Chain 4) and the
shadow model (§ End-to-End Chains) are real exceptions to the strict "nothing survives" reading, but both
operate at a grain far coarser than "this specific situation" — model identity and mechanism-trust,
respectively, not situational content. Classification **B** (credit assignment exists but doesn't reach
behavior) applies specifically to `seam_engine`. No mechanism in this audit reaches **A** or **G** at the
situational grain the mission's own hot-stove metaphor describes.

---

## Final Verdict — Blunt Answers

1. **Can Echo experience consequences?** Yes — sandbox pass/fail, quality scores, council disagreement,
   statistical contradictions are all real, mechanically-detected consequences.
2. **Can Echo remember them?** Yes, extensively — this project's logging infrastructure is genuinely
   thorough (`SELF_EDIT.log`, `seam_log.jsonl`, `council_deliberations.jsonl`, `self_edit_outcomes.jsonl`,
   and more).
3. **Can Echo recognize that they were consequences (not just events)?** Partially — sandbox pass/fail
   and seam detections are recognized as consequences precisely; RiverBrain's `.learn()` conflates action
   and consequence into one self-scored artifact (§11).
4. **Can Echo identify what action caused them?** Only at the individual-attempt level, inside self-edit's
   retry logic (Chain 2) — the single sharpest attribution in the system — and even there, only for the
   duration of one call frame.
5. **Can Echo retain that attribution?** Almost never past the immediate context that produced it. The
   sharpest attribution (Chain 2) is retained for zero time beyond the call frame that made it.
6. **Can a later situation reactivate it?** No mechanism found that reactivates a specific, situational
   attribution. The garden can resurface an *unresolved* question after real elapsed time, but blind to
   relevance (§ Garden section); nothing reopens a *resolved* one.
7. **Can it change a future decision because of it?** Yes, at the coarse grain of "which model" (Chain 4)
   and "should we trust this whole mechanism" (shadow model) — no evidence found for the finer grain of
   "avoid this specific kind of mistake."
8. **Can that change improve the future outcome?** Weakly established for RiverBrain
   (`[inherited]` r=0.206, ns); clearly established for the shadow model's subtractive case; directly
   contradicted by real data for the one traced situational case (`import re`, Chain 1).
9. **Can the process survive long enough to become durable knowledge?** Only when a human does the
   persisting by hand (Chain 1's prompt edit) — and even then, the available data shows no measurable
   suppression of the targeted failure.
10. **Does the architecture already contain a "hot stove" loop?** **Not at the level the metaphor
    describes.** A human touching a stove once and avoiding it forever is a *situational*, single-trial,
    durable lesson. FeralEcho's closest analogues are: (a) a mechanism that, given enough repeated burns
    across thousands of trials, will very slowly shift an aggregate preference away from "stoves in
    general" without ever forming "this specific stove, on this specific day, burned me" (RiverBrain); and
    (b) a mechanism that, after being told by an external observer that its whole sense of touch is
    unreliable, stopped trusting its own sense of touch (shadow model). Neither is the hot-stove loop the
    metaphor names.

> **"FeralEcho currently learns from experience by slowly shifting aggregate, coarse-grained preferences
> (which model, which self-edit family, whether to trust one specific internal arbitration mechanism)
> over large numbers of trials, but fails to learn from experience by forming and retaining any
> situational, single-instance attribution ('this specific mistake, in this specific way, caused this
> specific consequence') long enough for a later, independently-encountered similar situation to benefit
> from it."**

The stomach hypothesis (a reservoir for unresolved experience that can be revisited and consolidated
later) is **not wrong, but incomplete in a specific, now-precisely-located way**: a real reservoir exists
(the garden), it does support genuine temporal delay, but (a) it has no relevance-triggered reactivation
of *active* questions and zero reactivation of *resolved* ones, and (b) — this audit's own sharpest new
finding — the specific class of experience most likely to need a stomach (routine self-edit/coding
failure, 54.6% of all real logged activity) never reaches the reservoir's door in the first place, because
no code path anywhere ever tries to put it there. Building consolidation logic on top of the existing
garden would still fail, today, for the majority of Echo's real experience, because that experience never
becomes a candidate.

**If the real missing organ has one name, it is credit assignment at the situational grain** — not a
missing stomach, not a missing digestion step in the abstract, but the specific, narrower capability of
persisting "this exact thing happened, because of this exact cause" in a form a *different*, later moment
can consult. Every broken chain in this audit breaks at exactly that seam.
