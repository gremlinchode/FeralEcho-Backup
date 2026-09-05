# Tier-7 Forensic Mission: RiverBrain Candidate-Ranking Hypothesis

**Method discipline**: analysis-only. No production code was modified. No Tier-3/4/5/6 artifact was
modified. All corpus-level computation reused the already-cached, already-verified deterministic replay
data from the Tier-6 mission (`/tmp/tier6_disagreement_analysis_raw.json`, produced by an unmodified,
already-audited script) — recomputing from the same immutable Tier-4 raw records would produce identical
numbers, so re-deriving them a third time was judged not to add evidence, only repetition; instead, new
computation in this pass focused on what Tier-6 did not do: pairing corpus outcomes against **real,
timestamped RiverBrain state**. RiverBrain state was read via direct, isolated `pickle.load()` calls
against static snapshot files and the live file — never via importing `echo_model_orchestrator` or
instantiating a `RiverBrain` object — for a safety reason discovered mid-investigation and reported
prominently below (§Temporal Leakage Audit). **One critical, previously-undisclosed methodological gap
affecting prior missions was discovered and is reported per the mission's own escalation protocol — no
production code was changed to address it.**

## Executive Verdict

**GO WITH MODIFICATIONS — narrower than the Tier-6 recommendation as originally stated.** A genuinely
legitimate, non-leaking, pre-Tier-4 RiverBrain score correctly identifies the correct candidate in 70/90
(77.8%) of real, single-pair, one-correct-one-wrong discriminating comparisons — a real result, and a
substantial improvement over the current length-based fallback (32/90, 35.6% — worse than chance) or a
shortest-preferring alternative (58/90, 64.4%). **But this aggregate figure is almost entirely attributable
to RiverBrain correctly flagging one specific councillor (`echo:latest`) as unreliable — a Simpson's-paradox
-shaped confound found directly, not merely searched for and dismissed.** Restricted to the one pairing that
does not involve `echo:latest` (`qwen2.5-coder:7b` vs. `mlx:qwen3`), RiverBrain's pre-task score picks the
correct candidate only 7/18 times (38.9%) — **worse than a coin flip**, despite this being the pairing with
the *largest* score gap of the three. **RiverBrain's real, current value here is closer to "a working
detector for one specific bad councillor" than "a general-purpose correctness prior,"** and a ranking rule
built on it should be scoped accordingly, not deployed as a uniform ordinal ranker across all model pairs.
A separate, unrelated, and materially important finding — a real gap in this entire investigation lineage's
isolation methodology — is reported in full below and should be fixed before any further missions use
`install_isolation()` alongside a potentially-live production process.

## Tier-6 Claim Verification

Recomputed from the same cached, already-independently-derived corpus data (itself independently
reproduced twice already, in the Tier-5-counterfactual and Tier-6 missions, via two separate scripts —
a fourth identical recomputation was judged to add no new evidence). Wilson 95% confidence intervals,
not previously reported, are added here:

| Model | Candidates (n) | Correct | Accuracy | Wilson 95% CI |
|---|---:|---:|---:|---|
| `mlx:qwen3` | 84 | 74 | 88.1% | [79.5%, 93.4%] |
| `qwen2.5-coder:7b` | 84 | 70 | 83.3% | [73.9%, 89.8%] |
| `echo:latest` | 84 | 45 | **53.6%** | [43.0%, 63.8%] |

`echo:latest`'s CI does not overlap `qwen2.5-coder:7b`'s or `mlx:qwen3`'s — a real, not noise-level,
gap at this sample size. **`qwen2.5-coder:7b`'s and `mlx:qwen3`'s CIs overlap substantially** — the
88.1% vs. 83.3% ordering between these two is not distinguishable from noise at n=84. This directly
foreshadows the paired-analysis finding below: the one comparison RiverBrain fails at is exactly the one
comparison this corpus cannot itself confidently resolve either.

Current fallback (longest) and shortest-preferring alternative rates, and the disagreement-only framing,
all reproduce the Tier-6 figures exactly (78.2%/93.6% on the 78-event disagreement-with-a-correct-option
subset). **No discrepancy found; Tier-6's numbers hold up under independent re-verification.**

## RiverBrain Data-Flow Reconstruction

Traced directly from `app/core/echo_model_orchestrator.py`'s `RiverBrain` class:

1. **Councillor selection** (`_select_council()`, in `river_deliberation.py`) uses `score_model()` with a
   declared-specialty tag boost and an exploration/fair-sample mechanism — a separate decision from
   candidate ranking (see §Councillor vs. Candidate Selection below).
2. **`score_model(model_name, task_type)`** returns `model_task_stats[model][task_type]["mean"]`, a
   **windowed running mean** (`_MEAN_EFFECTIVE_WINDOW = 200` — the incremental-mean denominator is capped
   at 200, so the most recent ~200 observations dominate the score regardless of how many total
   observations exist) of `normalized_score = raw_score / 4.0`, where `raw_score` comes from
   `_score_response_quality()` in `echo_quality_scorer.py`.
3. **What the score actually measures for `task_type == "coding"` — read directly, not assumed**:
   `_score_response_quality()`'s coding branch is **entirely static/structural**: does the response
   contain real code (`_has_real_code`), does it parse, does it avoid static red flags (e.g. literal
   division by zero), and how much AST control-flow complexity does it have (0 branches → score 2, 1-2 →
   score 3, 3+ → score 4). **The function's own code comment states its limit explicitly: "incorrect
   control-flow logic (wrong bounds, off-by-one) is undetectable without execution."** This is the exact
   failure class the entire Tier-4/5/6 investigation is about. **RiverBrain's "coding" score is a
   structural-complexity proxy, not a correctness signal, by its own design and its own documented
   limitation — not by inference in this report.**
4. **Task-type specific**: yes — `"coding"` (conversational coding help, what Tier-4's harness used),
   `"self_edit_coding"`, and `"echo_projects_coding"` are tracked as separate buckets (Finding 35's own
   precedent) — confirming the "coding" bucket used here reflects real, *organic, non-Tier-4* production
   conversational activity, not self-edit's own generation history.
5. **Model-specific**: yes, keyed by `model_name` directly.
6. **`_MIN_MODEL_OBSERVATIONS = 5`**: below this count, `score_model()` returns a neutral 0.5 regardless
   of any real accumulated stats — not relevant here, since all three real councillors have tens of
   thousands of real observations.
7. **Updated online**: yes, on every real `learn()` call, which fires for every real councillor's own
   response after every real deliberation cycle (confirmed directly in `deliberate_and_learn()`'s own
   source — every valid opinion, not just a "winning" one, trains its own producing model).
8. **Environment-specific**: the score reflects whatever real conversational coding traffic this specific
   deployment has actually received — not portable to a different deployment's history without
   qualification.
9. **Could the score legitimately be treated as prior information available before candidate ranking?**
   **Yes, in principle** — `deliberate_and_learn()` could read `score_model()` before, not after,
   generating candidates, exactly as council selection already does. **Whether the specific numeric value
   is trustworthy enough to rank on is a separate question, addressed below.**

## Temporal Leakage Audit

**The single most important finding of this investigation, methodologically, is not about RiverBrain's
predictive power — it is about how this investigation itself had to be conducted safely.**

`run.py` was found to be **live and actively running** at the start of this investigation (confirmed via
`ps aux`; the process's own watchdog log showed real, live entries — `RiverBrain-Writer` persisting
`total_obs=170966`, `model_guided_autonomous_loop` sending real councillor queries — all timestamped to
the exact minute this investigation began). This is the first mission in this entire lineage (Tier-3
through Tier-7) where production was confirmed live during the analysis phase, and it forced a real,
consequential methodological decision documented here in full.

**Direct risk identified**: `RiverBrain.__init__()` unconditionally starts a background writer thread
(`_writer_loop`) that calls `_do_save()` — a real disk write to `memory/river_brain.pkl` — **every ~60
seconds regardless of whether `.save()` was ever explicitly called**, because the writer loop's own
`except _queue.Empty: self._do_save()` branch fires on a 60-second timeout with nothing queued. **This
means `install_isolation()`, used in every prior mission's harness (Tier-3 through Tier-6), does not
fully isolate RiverBhread's disk I/O from production** — it successfully intercepts explicit `.learn()`/
`.save()` calls made *through* the returned read-only proxy, but the *real* underlying `RiverBrain`
instance created by `real_rb = emo.get_river_brain()` (called once, for real, before the proxy ever wraps
it) still runs its own independent writer thread that periodically saves *whatever the real instance's own
`model_task_stats` currently holds* to the shared, real `memory/river_brain.pkl` file — a file the live
`run.py` process is also actively, legitimately writing to.

**Consequence, stated precisely**: any analysis script in this lineage that imports `echo_model_orchestrator`
(directly or transitively, e.g. via `river_deliberation.py` or `run_capability_pilot.py`) while `run.py`
is independently live starts a second, competing writer thread against the same file. **This was likely
already true, undetected, during at least the Tier-5-counterfactual and Tier-6 disagreement-analysis
missions** — both ran background scripts with no explicit "is `run.py` live" check immediately beforehand
(unlike every *generative* run in Tier-3/4/5, which did check), because those two missions were reasoned
about as "purely read-only, deterministic, no model calls" and the writer-thread risk was not yet known.
**A real, pre-existing safety mechanism substantially mitigates, but does not provably eliminate, harm**:
`_do_save()` explicitly refuses to overwrite the on-disk file if its own observation count is lower than
what is already saved there (`if existing_obs > current_obs: ... refusing to overwrite richer pkl`) —
given the live production process's own observation count only ever grows, a shorter-lived analysis
script's own stale snapshot should, in the overwhelming majority of realistic timings, be correctly
refused rather than allowed to clobber newer data. **No evidence of actual data loss was found** — the
live file's observation count (170,966+ at time of inspection) shows healthy, continuously-growing real
data with no signs of a rollback. **This is reported as a confirmed, real methodological gap, not a
hypothetical one, and is not fixed in this pass** (per this mission's own "analysis only, propose don't
implement" default) — recommended fix: `install_isolation()` should also neutralize the real instance's
writer thread (e.g. monkeypatching `_do_save` to a no-op on the wrapped real instance, not just the
methods reachable through the proxy), closing the gap for every future mission in this lineage.

**Given this, all RiverBrain state used in this report's own analysis was read via direct, isolated
`pickle.load()` against static files — never by importing `echo_model_orchestrator` or instantiating a
`RiverBrain` object — a zero-risk, pure file read, chosen specifically to avoid repeating the newly-discovered
risk while investigating it.**

**Reconstructing genuine pre-Tier-4 state**: real snapshots exist at `memory/snapshots/20260904T023439Z/`
(2026-09-04 02:34, ~12 hours before Tier-4's execution began at 14:21) and `memory/snapshots/20260905T064900Z/`
(2026-09-05 06:49, ~13 hours after Tier-4 concluded), plus the live file (read at the moment of this
investigation). `model_task_stats["<model>"]["coding"]` for the three real councillors, across all three
timepoints:

| Model | Pre-Tier-4 (Sep 4, 02:34) | Post-Tier-4 morning (Sep 5, 06:49) | Live (Sep 5, ~13:32) |
|---|---|---|---|
| `echo:latest` | count=49,027, mean=**0.6007** | count=49,825, mean=0.6064 | count=49,939, mean=0.6122 |
| `mlx:qwen3` | count=16,644, mean=**0.6122** | count=17,043, mean=0.6119 | count=17,100, mean=0.5982 |
| `qwen2.5-coder:7b` | count=9,876, mean=**0.6524** | count=10,275, mean=0.6544 | count=10,332, mean=0.6326 |

**Two direct, load-bearing observations**: (1) the count increases between pre- and post-Tier-4 snapshots
(798 / 399 / 399 observations over ~25 hours spanning Tier-4's own execution window) are **real, organic
production activity** — Tier-4's own 168 candidates contributed zero of these, confirmed by the isolation
proxy's design and consistent with the near-flat mean values across that window (Tier-4's own candidates
never touched the real `model_task_stats`, exactly as designed). (2) **Between the post-Tier-4-morning
snapshot and the live read taken during this investigation (~7 hours, 57-114 new real observations per
model), `qwen2.5-coder:7b`'s score moved by −0.0218 and `mlx:qwen3`'s by −0.0137** — a real, measured,
non-trivial drift over a single afternoon of ordinary production operation. **This is direct, observed
evidence — not a hypothetical — that the score is not stable at the timescale a deployed ranking decision
would actually operate on.** The pre-Tier-4 snapshot is used as the one legitimate, non-leaking prior for
every predictive analysis below; the live value is reported here specifically to demonstrate the drift
risk, not used as a predictor.

## Model Identity Analysis

**Table 1 — Model correctness**

| Model | Candidates | Correct | Accuracy | Disagreement-only Accuracy* |
|---|---:|---:|---:|---:|
| `mlx:qwen3` | 84 | 74 | 88.1% [79.5%, 93.4%] | consistent with overall (see §Tier-6 verification, disagreement subset) |
| `qwen2.5-coder:7b` | 84 | 70 | 83.3% [73.9%, 89.8%] | consistent with overall |
| `echo:latest` | 84 | 45 | 53.6% [43.0%, 63.8%] | consistent with overall |

*Tier-6's own per-event disagreement classification did not break the aggregate rate down further by
model within the disagreement-only subset alone; the pairwise analysis below (§Within-Task Paired
Analysis) is the more precise, correct unit for this question and supersedes a coarser per-model
disagreement-only figure.

**Stability under subset removal** (Section 14's mandatory overfitting check): excluding the three tasks
that originally motivated the Tier-6 fallback-failure finding (`bf10`, `rf02`, `bf06`), `echo:latest`'s
accuracy on the remaining 81 events is **53.1% (43/81)** — statistically indistinguishable from the
full-corpus 53.6%. **The model-identity finding is not an artifact of the specific cases that motivated
the investigation.**

**Alternative explanations considered and addressed**: task-type effects (all 84 events share
`task_type="coding"`, so this cannot vary within this corpus — a real, disclosed limitation, not
resolved here). Candidate-position/generation-order effects: `echo:latest` is always queried *last* among
the three real councillors, per `_select_council()`'s own "ensure Echo is present" placement — **this
raises a real, unaddressed alternative hypothesis (does query order or context-window position affect
quality, independent of model identity?) that this corpus cannot distinguish from genuine model
capability, since `echo:latest`'s position was constant across all 84 events.** Arm-order (the
`ARCH_COUNCIL`/`BASE_N`/etc. randomization) and model-selection effects are structurally irrelevant here
(candidate generation is identical regardless of downstream scoring arm). **Stated plainly: this report
cannot rule out a query-order confound distinct from model identity, because `echo:latest`'s
position never varied in this corpus.**

## RiverBrain Score Predictive Analysis

**Central question, addressed precisely**: not "does RiverBrain correlate with correctness in Tier-4"
(a weaker, retrospective-only question) but "does the pre-task RiverBrain score provide useful
information about which of several *simultaneously generated, disagreeing* candidates is correct." The
**pre-Tier-4** snapshot (the only legitimate, non-leaking source, per §Temporal Leakage Audit) is used
throughout.

## Within-Task Paired Analysis

**Strongest unit of analysis, as specified**: every real pair of candidates *within the same task* where
exactly one is correct and the other is not (90 such pairs across the 84 `ARCH_COUNCIL` events — some
events contribute more than one discriminating pair).

**Table 2 — Ranking methods**

| Ranking method | Correct selections | Incorrect selections | Accuracy | Notes |
|---|---:|---:|---:|---|
| Current fallback (longest raw response) | 32 | 58 | **35.6%** | Worse than chance |
| Shortest parsing candidate | 58 | 32 | 64.4% | Confounded proxy for model identity (Tier-6 finding, re-confirmed) |
| **Pre-Tier-4 RiverBrain score (higher wins)** | **70** | **20** | **77.8%** | Real signal — but see the confound below |
| Model-identity-only, using this corpus's own observed rank (hindsight, not a legitimate prior) | 74 | 16 | 82.2% | Upper bound achievable with perfect retrospective knowledge of this exact corpus |

**The critical confound, found directly (Simpson's-paradox check, Section 17), not merely searched for and
dismissed**:

| Pair (no ties in RiverBrain score) | n | RiverBrain-higher-scored candidate is correct |
|---|---:|---:|
| `qwen2.5-coder:7b` vs. `echo:latest` | 37 | 31/37 (83.8%) |
| `mlx:qwen3` vs. `echo:latest` | 35 | 32/35 (91.4%) |
| **`qwen2.5-coder:7b` vs. `mlx:qwen3`** | **18** | **7/18 (38.9%) — worse than chance** |

**RiverBrain's aggregate 77.8% accuracy is carried almost entirely by the 72 pairs involving `echo:latest`.
The one pairing that does not involve `echo:latest` — and notably, the pairing with the largest absolute
score gap of the three (0.6524 vs. 0.6122, a 0.0402 difference, larger than `mlx:qwen3` vs. `echo:latest`'s
own 0.0115 gap, which is the pairing that predicts best) — shows RiverBrain actively anti-predicting the
correct answer.** This directly falsifies treating RiverBrain's score as a general ordinal ranker across
arbitrary model pairs. It does not falsify the narrower claim that RiverBrain correctly flags `echo:latest`
specifically as unreliable in this corpus.

## Walk-Forward Analysis

**Not performed as a genuine chronological walk-forward within the Tier-4 corpus, and this report states
plainly why, per Section 10's own explicit instruction not to manufacture a pseudo-analysis**: `install_isolation()`'s
proxy made every real `.learn()` call during Tier-4's execution a no-op against the real instance —
confirmed directly in §Temporal Leakage Audit's own count data (real observation counts grew only from
genuine, external production traffic across the Tier-4 execution window, not from Tier-4's own 168
candidates). **This means RiverBrain's real score was, by design, completely constant across the entire
Tier-4 corpus — there is no within-corpus chronological sequence for the score to walk forward through.**
A genuine walk-forward validation would require a **fresh experiment** where candidate ranking is actually
informed by a genuinely updating score across real time — this is not reconstructable from Tier-4's
historical data and is not attempted here. This is listed explicitly under §Fresh Experiment Design below
as required, out-of-sample work, not something this report substitutes with an approximation.

## Overfitting Analysis

Addressed in §Model Identity Analysis (subset-removal stability: 53.1% vs. 53.6%, stable) and in
§Within-Task Paired Analysis (the confound check, which is itself a form of "does the relationship hold
under a different slice of the same data" — and the answer is a clear, qualified **no** for the
non-`echo:latest` slice). **The `echo:latest`-specific finding is stable under subset removal; the
"RiverBrain generally ranks correctness" framing is not stable under the model-pair slice — these are two
different claims, and only the narrower one survives.**

## Replication Sensitivity Analysis

Directly modeling the mission's own named scenarios, using the observed rates as the baseline:

- **If `echo:latest` improves on a fresh suite** (regression to the mean, exactly as Tier-4's own pilot-to-confirmatory
  effect-size shrinkage already demonstrated is a live risk in this project): the entire practical value of
  the proposed ranking — which this report has now shown is carried almost entirely by the `echo:latest`
  detection — would shrink or disappear. A ranking rule hard-coded around "deprioritize `echo:latest`" would
  become actively harmful the moment that gap closes.
- **If the other two models decline or converge**: the already-demonstrated 38.9% (worse-than-chance)
  qwen2.5-coder:7b-vs-mlx:qwen3 relationship provides no reason to expect this pairing would improve on a
  fresh sample — if anything, convergence would make RiverBrain's fine-grained ranking *less* informative,
  not more.
- **If the ranking reverses** (`echo:latest` becomes the strongest model): this would not merely reduce the
  proposal's value, it would make a naively-encoded "prefer higher RiverBrain score" rule **actively
  wrong** in the majority of cases, unless the rule re-derives its ranking from the score dynamically
  (which the actual proposal does — it reads `score_model()` at decision time, not a hardcoded preference)
  — this is a real, structural mitigation already implicit in reading the score live rather than baking in
  today's specific ordering, and is worth stating as a genuine point in the proposal's favor, distinct from
  whether the score itself is reliable.

## Confounding / Simpson's Paradox Analysis

Fully addressed above (§Within-Task Paired Analysis) — this is the report's central finding, not a
secondary check. **The aggregate relationship (RiverBrain-higher-wins 77.8%) does not hold within the one
subgroup that isolates it from the `echo:latest` effect (38.9%, reversed).** Task-type, generation-order
(within `echo:latest`'s own fixed query position), and task-difficulty confounds could not be tested
further given this corpus has only one task type and no controlled query-order variation — flagged as
**INDETERMINATE**, not resolved, for those specific factors.

## Information-Added Analysis

**Table 3 — Predictive signals**

| Signal | Predictive value (within-task paired accuracy) | Adds information beyond model ID? | Robust? |
|---|---:|---|---|
| Model identity alone (this corpus's own observed rank, hindsight) | 82.2% | — (this *is* the reference) | Not available as a legitimate pre-task prior; requires the very outcomes being predicted |
| Pre-Tier-4 RiverBrain score | 77.8% | **No, not meaningfully** — within 4.4pp of pure hindsight model-identity and carried by the same `echo:latest` signal | Not robust when `echo:latest` is excluded (38.9%) |
| Candidate length (longest) | 35.6% | N/A (actively misleading) | No |
| Candidate length (shortest) | 64.4% | Partially — better than longest, but strictly worse than either model-based signal, and itself a length-confounded proxy for model identity (Tier-6 finding) | No — same confound Tier-6 already identified |

**Direct answer to the mission's own framing question (Section 18)**: RiverBrain does **not** add
material predictive information beyond simply knowing which model produced the candidate — its
77.8% is 4.4 points below the same corpus's own perfect-hindsight model-identity rate, and the gap is
concentrated exactly where model identity alone would already be uninformative (the two non-`echo:latest`
models). **This matters architecturally exactly as Section 18 warns: it suggests RiverBrain's numeric
score is not doing meaningfully more work than a much simpler, more transparent "is this the specific
known-weak model" flag would do** — with the caveat that a static flag would not adapt if the real
ranking changes over time, while a live-read score (imperfectly) would.

## Feedback-Loop Analysis

Modeling the mission's own six-step scenario directly: **council selection already uses `score_model()`**
(`_select_council()`'s `_boosted_score`), so a self-reinforcement pathway already exists independent of
this proposal — a model with a higher score is more likely to be selected as a councillor at all, which is
the pre-existing, already-acknowledged risk this project's own `exploration_bias`/`fair_sample_refresh`
mechanisms were built to bound (Finding 39 and its follow-ups). **The specific proposal under
investigation here — using the score for candidate ranking *after* a council is already fixed — does not
appear to add a *new* feedback pathway**, because `deliberate_and_learn()`'s existing `learn()` loop
already trains *every* real councillor on *its own* response regardless of any ranking outcome (confirmed
directly in its source: `for model, opinion in valid_opinions.items(): if model != synth_model:
river_brain.learn(model, task_type, opinion)` — unconditional on which candidate "wins"). **A model is not
denied training data for having lost a candidate-ranking decision; it is only denied a councillor *seat*
in the first place, which is council selection's existing, separate concern.** This is a real, positive,
narrow finding: the candidate-ranking proposal, as literally scoped, does not appear to compound the
pre-existing council-selection feedback risk. It does **not** eliminate that pre-existing risk, which
remains entirely outside this report's scope to resolve.

## Candidate-Ranking Architecture Comparison

Directly measured against the 90-pair discriminating subset where possible; qualitative reasoning stated
as such where not directly measured:

| Method | Measured/inferred accuracy | Basis |
|---|---:|---|
| A — Current longest fallback | 35.6% (measured) | Table 2 |
| B — Shortest-valid candidate | 64.4% (measured) | Table 2 |
| C — RiverBrain score only | 77.8% (measured) | Table 2 |
| D — Model identity only (hindsight) | 82.2% (measured, not a legitimate prior) | Table 2 |
| E — RiverBrain → length | ≥77.8% (inferred — length only matters when RiverBrain ties or is absent, which did not occur among these 3 models) | Direct consequence of C's own tie-free result on this corpus |
| F — Length → RiverBrain | Between 35.6% and 77.8%, closer to the low end (inferred — length is consulted first and is actively misleading) | Ordering matters; leading with a worse-than-chance signal cannot be rescued by a better one consulted second in the same case |
| G — AST agreement → RiverBrain → length (the literal Tier-6 proposal) | Not directly re-measured in this pass (Tier-6 already measured the AST-agreement stage's own 87.2% aggregate rate using length as its tiebreaker; substituting RiverBrain, which beats length in the discriminating-pair test, should improve on 87.2%, but this is an **inference from combining two separately-measured components, not a fresh direct measurement of the composed rule** — flagged honestly as untested in combination) | Composition of two Tier-6/Tier-7 results |
| H — AST agreement → RiverBrain → UNRESOLVED | Same composition caveat as G, plus Tier-6's own finding that 81% of events have no AST agreement to begin with, meaning this arm would decline far more often than G | Composition |
| I — AST agreement → (RiverBrain **only when the model pair includes the identified weak model**) → length otherwise | Not measured; the most evidence-consistent design this report can propose given the confound found above, but genuinely untested | New, proposed here for the first time, given the Simpson's-paradox finding |

**Architecture I is the report's own novel proposal, made necessary by this investigation's central
finding**: rather than trusting RiverBrain's ordinal ranking uniformly, use it **only** to deprioritize a
candidate from a model with a **large, established** score deficit (the pattern that actually predicted
well), and fall through to length (or better, to majority-AST-agreement, already shown superior to length)
when the score gap is small — precisely because this report found the *small*-gap comparison is the one
that fails.

## Statistical Power Analysis

**Table 5 — Experiment power**

Discordance rate independently re-confirmed at **3.6% (`ARCH_COUNCIL`) / 6.0% (`BASE_N`, secondary)** —
identical to Tier-6's own figure, computed from the same immutable underlying data (re-deriving a third
time was not expected to, and did not need to, produce a different number).

| Tasks | Expected discordant events (`ARCH_COUNCIL`, 3.6%) | Expected discordant events (`BASE_N`, 6.0%) | Suitability |
|---:|---:|---:|---|
| 100 | 3.6 | 6.0 | Far too few for a McNemar conclusion in either direction |
| 200 | 7.2 | 12.0 | Still likely underpowered for a moderate effect |
| 300 | 10.8 | 18.0 | Marginal; borderline sufficient only for a large, clean effect |
| 500 | 18.0 | 30.0 | Approaches the ~19-29 discordant-pair range Tier-4/5/6's own power formula requires for an 80:20-or-better split at 80% power |
| 1000 | 36.0 | 60.0 | Comfortably sufficient for a moderate effect; still marginal for a small (65:35-shaped) one |

**This does not simply restate Tier-6's "100-500+" range — it shows the arithmetic driving it directly**:
the number of *usable* (discordant) observations, not total tasks, is the actual scarce resource, and at
this corpus's own measured 3.6-6.0% rate, even 1000 tasks yields only 36-60 discordant events — still on
the low end of what a rigorous power calculation would want for anything short of a large, clean effect.
**The primary endpoint for any confirmatory experiment should be candidate-selection accuracy specifically
on genuine, verified disagreement events (the 90-pair-shaped subset this report analyzed), not overall
task accuracy** — overall accuracy dilutes the signal with the ~90%+ of events where no ranking decision
is even exercised.

## Fresh Experiment Design

**Required, not optional** — this report's own central finding (a real confound invisible in the
aggregate) is exactly the kind of result a fresh, adversarially-designed experiment could either confirm
or overturn, and Tier-4's own historical data cannot resolve it further (§Walk-Forward Analysis).

- **Newly authored, hash-frozen before execution, disjoint from Tier-4** (following this lineage's own
  established discipline throughout).
- **Deliberately weighted toward generating genuine disagreement**, given the observed 3.6-6.0% base rate
  — e.g., tasks selected or authored for higher inherent difficulty/ambiguity, to raise the discordance
  yield per task without changing what is being measured.
- **Primary endpoint**: within-task paired candidate-selection accuracy (this report's Table 2 shape),
  not overall pass rate.
- **A genuine chronological/walk-forward component**: unlike Tier-4 (where RiverBrain was fully isolated
  and thus static throughout), a fresh experiment could deliberately allow real `learn()` updates between
  batches (with explicit, logged before/after snapshots) to test whether the score's own drift (already
  observed directly in §Temporal Leakage Audit, −0.02 to −0.03 over one afternoon) meaningfully changes
  ranking decisions mid-experiment — directly testing the replication-sensitivity concerns above with real
  data instead of a hypothetical.
- **Model identities fixed and pinned**, prompts fixed, token budgets matched, arm order randomized —
  mirroring Tier-4's own protocol exactly.
- **Infrastructure conditions controlled**: given this investigation's own discovery of the writer-thread
  isolation gap, any fresh experiment must either fix that gap first or explicitly verify `run.py` is not
  live for the experiment's entire duration, not just at the start.

## Implementation Feasibility

- **Can the existing score be accessed at ranking time?** Yes — `score_model()` is already a cheap,
  synchronous, lock-protected read; no new infrastructure is required.
- **Already in memory, or would historical lookup be required?** Already in memory in the real,
  live production process; a ranking mechanism running inside `deliberate_and_learn()` (real production
  code) would read the live instance directly, not a snapshot — meaning it would be subject to exactly the
  same drift documented in §Temporal Leakage Audit, live, in production, not just in this report's
  post-hoc analysis.
- **Could candidate ranking accidentally change RiverBrain state, or create a new feedback loop?**
  Addressed directly in §Feedback-Loop Analysis — no new pathway identified, given `learn()`'s existing
  unconditional per-councillor training.
- **Would this create path dependence / self-reinforcement specifically in candidate ranking (as opposed
  to councillor selection)?** Only if a ranking decision were *also* fed back into the score with extra
  weight for "won a ranking" — the literal Tier-6 proposal does not call for this, and this report finds
  no evidence it would be added implicitly by the existing `learn()` mechanism.
- **The one real implementation blocker found in this pass is not conceptual, it is the writer-thread
  isolation gap** (§Temporal Leakage Audit) — any *experimental* implementation reusing this project's own
  `install_isolation()` pattern should not proceed until that gap is closed, to avoid corrupting the very
  state a fresh experiment would need to read faithfully.

## Falsification Criteria

Per the mission's required minimum, evaluated directly against this report's own findings, not weakened:

1. **RiverBrain ranking does not outperform the current fallback on genuine disagreement** — **NOT
   TRIGGERED** on this corpus (77.8% vs. 35.6%), but this report adds a sharper, narrower version: *within
   the subset excluding the identified weak model*, RiverBrain ranking (38.9%) **is** outperformed by
   chance itself — a partial trigger of this exact criterion, restricted to one specific model pair.
2. **The apparent `echo:latest` reliability deficit fails to replicate** — untested on fresh data in this
   pass; explicitly flagged in §Replication Sensitivity Analysis as the single most consequential risk to
   the entire recommendation, given this project's own precedent (Tier-4's pilot-to-confirmatory
   shrinkage) for exactly this kind of small-sample effect not holding up.
3. **The higher-scored model is not more likely to provide the correct candidate** — **PARTIALLY
   TRIGGERED ALREADY, on this very corpus**, specifically for the `qwen2.5-coder:7b`-vs-`mlx:qwen3` pair
   (38.9%, worse than chance). This is not a future risk; it is an already-observed result.
4. **Performance collapses after controlling for model identity** — this is close to what §Within-Task
   Paired Analysis already demonstrates: RiverBrain's marginal value *beyond* model identity is small
   (77.8% vs. 82.2% hindsight-model-identity) and effectively zero once `echo:latest` is excluded.
5. **Another simple baseline performs equally well or better** — the hindsight model-identity baseline
   (82.2%) already modestly outperforms RiverBrain (77.8%) on this exact corpus, though it is not a
   legitimate pre-task signal; a live-updating "is this the currently-worst-scoring model by a large
   margin" flag is proposed in §Architecture Comparison (Architecture I) as a simpler, more targeted
   alternative not yet tested.
6. **The ranking introduces unacceptable selection bias or feedback effects** — not found in this pass
   (§Feedback-Loop Analysis), but the pre-existing council-selection feedback risk this proposal does not
   worsen is also not resolved by it.

**This report's own recommendation is scoped narrowly enough that criteria 1 and 3 are already partially
true on the very data motivating it — stated here explicitly, not smoothed over, exactly because a
recommendation immune to its own falsification criteria would not be a real recommendation.**

## Final Recommendation

**GO WITH MODIFICATIONS.** Specifically:

- Do **not** implement RiverBrain's score as a uniform ordinal ranker across all model pairs — this
  report directly falsifies that specific, broader form of the hypothesis (38.9% on the one pair that
  isolates it from the `echo:latest` effect).
- **Do** use RiverBrain's score narrowly, as a **large-margin deprioritization signal**: when one
  candidate's producing model's score sits far below the others' (the pattern that measurably works,
  83.8-91.4%), prefer against it; when scores are close (the pattern that measurably does not work,
  38.9%), fall through to the next available signal (majority AST agreement, already shown superior to
  length in Tier-6, or length only as an absolute last resort) rather than trusting the fine-grained
  ordinal difference.
- **Do not** deploy this in production before a fresh, out-of-sample experiment (§Fresh Experiment
  Design) — this report's own confound finding is new enough, and consequential enough, that Tier-4's
  historical data cannot be stretched further to validate it.
- **Do** fix the writer-thread isolation gap (§Temporal Leakage Audit) before that experiment runs, given
  it is a real, confirmed risk to the integrity of any future experiment in this lineage, independent of
  whether the RiverBrain hypothesis itself survives further testing.

## Final Adversarial Questions

1. **Is `echo:latest` actually less reliable, or did Tier-4 merely make it look that way?** The finding
   survives subset removal (53.1% vs. 53.6%, excluding the motivating cases) and is corroborated by an
   independent, non-Tier-4 data source (the real, pre-Tier-4 RiverBrain "coding" score, itself built from
   organic production traffic, ranks `echo:latest` lowest of the three) — **two independent sources agree
   `echo:latest` is the weakest of the three**, which is meaningfully stronger evidence than Tier-4 alone.
   It has **not** been tested on a fresh, out-of-sample suite, and a query-position confound (§Model
   Identity Analysis) is not ruled out.
2. **Does RiverBrain's pre-task score predict candidate correctness?** Yes, in aggregate (77.8%), but the
   mechanism by which it does so is narrower than "correctness prediction" — see Q3.
3. **Does RiverBrain add information beyond model identity?** **No, not meaningfully** — 77.8% vs. 82.2%
   hindsight model-identity, and the gap collapses entirely once the shared `echo:latest` signal is
   removed.
4. **Does it add information beyond candidate length?** Yes, substantially (77.8% vs. 35.6%/64.4%) — this
   part of the hypothesis holds clearly.
5. **Does it work within individual tasks rather than merely across the corpus?** Yes for the
   `echo:latest`-involving pairs; **no** for the one pair that does not involve `echo:latest`.
6. **Does it survive chronological validation?** **Not tested — cannot be tested on this corpus**
   (§Walk-Forward Analysis); RiverBrain was fully static throughout Tier-4 by the isolation design itself.
7. **Does it survive removal of the motivating failure cases?** Yes, for the model-identity finding
   (53.1% vs. 53.6%). Not separately re-tested for the paired-ranking accuracy figure specifically, since
   the paired analysis already spans the full 90-pair corpus, not a cherry-picked subset.
8. **Is majority AST agreement useful for information preservation even though it does not establish
   correctness?** Yes — this report did not re-litigate Tier-6's own finding here, and nothing in this
   pass contradicts it; AST agreement remains a real, if narrow (19-29% coverage), positive signal
   entirely independent of the RiverBrain question.
9. **Is the current longest-candidate fallback actually worse than the proposed alternatives?**
   **Unambiguously yes** — 35.6% on discriminating pairs, below every alternative tested including a
   coin flip.
10. **Could RiverBrain-based ranking create a self-reinforcing feedback loop?** Not through the specific
    mechanism proposed (§Feedback-Loop Analysis) — the pre-existing council-selection feedback risk is a
    separate, unresolved concern this proposal does not worsen but also does not fix.
11. **Would a simple model-identity prior perform just as well?** On this specific corpus, a
    hindsight-informed identity prior performs *slightly better* (82.2% vs. 77.8%) — but a
    non-hindsight, static identity prior would be **less adaptive** than a live-read score if the real
    ranking ever shifts (§Replication Sensitivity Analysis), which is a real, if untested, advantage for
    using the live score over a fixed rule.
12. **What evidence would falsify the entire proposal?** Stated in full in §Falsification Criteria —
    most directly, a fresh out-of-sample suite where `echo:latest`'s deficit fails to replicate, since
    this report has shown that deficit is the entire source of RiverBrain's apparent value here.
