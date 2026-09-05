# FeralEcho: Adversarial Validation of the Discovered Closed Self-Edit Loop

No fixes were implemented. Every claim below traces to a direct source read, a live data read, or a
purpose-built correlation script joining three real log files by timestamp — not to documentation or
inference alone. Full machine-readable detail is in
`audits/self_edit_closed_loop_validation.json`.

## 1. Executive Finding

**The self-edit targeting loop is real, closes, and demonstrably persists — but it operates
exclusively at the level of target selection (which task type gets attempted next), and this
investigation finds no statistically defensible evidence that it produces measurable quality
improvement.** Among 103 real, quality-tracked self-edit outcomes, the mean quality delta (+0.103) is
not distinguishable from zero at conventional significance (t=1.65, p≈0.10, n=103); 42 of 103 (40.8%)
actually worsened quality; and the mean delta is nearly identical regardless of which targeting signal
happened to be "correct" at decision time (0.098 vs 0.118 vs 0.114) — the signature of noise around a
near-zero baseline, not directed improvement. Separately, and more surprisingly: across this entire
multi-month, 103-entry tracked history, **100% of real, quality-evaluated self-edit deploys targeted
`coding`**, regardless of what either the empirical (RiverBrain) or shadow (keyword-heuristic) signal
said — meaning the "shadow overrides the stronger signal" defect, while real and directly demonstrated
to affect at least one live, untracked cycle this session, has left **no detectable trace on the
historically-tracked, quality-evaluated production record**. This is reported as **Level 3**
(persistent behavioral adaptation of targeting) — not Level 4 (measurable iterative improvement), per
the mission's own explicit standard that Level 4 requires direct outcome evidence, and the direct
evidence gathered here argues against it rather than merely failing to support it.

## 2. Exact Causal Graph

```
execute_self_edit()'s terminal branches (app/core/self_edit_manager.py)
  ↓  [result: dry_run_staged / rejected_not_improvement / staging_import_failed / safety_blocked / success]
save_reflection() — same file, called at each terminal branch
  ↓  writes a STRUCTURED entry (result, model_used, generated_code) to memory/reflection_shard.jsonl
  ↓  [NOTE: distinct from reflection_shard.py's own separate generative reflection loop —
  ↓   that loop reads only a signal string + past-reflection embeddings, zero access to this data]
self_model_updater._compute_self_edit_stats()  →  _compute_targets()
  ↓  reads generated_code-bearing entries from reflection_shard.jsonl + RiverBrain observation_counts
  ↓  writes memory/self_model.json's targets.next_self_edit_focus
  ↓  LIVE VALUE CONFIRMED: {"next_self_edit_focus": "coding", "reason": "avg_quality=2.37
  ↓   (threshold=2.5), obs=99027"}
perform_self_edit()'s target-selection block (app/core/self_edit_manager.py)
  ↓  checks memory/shadow_self_model.json FIRST ("highest-trust signals", per its own code comment)
  ↓  falls back to SelfModelUpdater().get_weak_task_type() [reads the value above] only if the
  ↓   shadow file is absent or has no focus set
target_task_type  →  _build_targeted_prompt()  →  next self-edit cycle
  ↓
(loops back to execute_self_edit() at the top)
```

Every arrow above was traced to an exact file/function this session, not assumed from documentation.
Full per-edge exists/executes/reader-confirmed/behavioral-effect/persistence detail is in the JSON's
`causal_graph_exact` array.

## 3. RiverBrain Signal Analysis (Signal A — empirical)

- **Source data**: `RiverBrain.model_task_stats`, a real, EMA-windowed (past 200 observations,
  Finding 39) running quality mean per (model, task_type). Live unpickle confirms `coding`'s combined
  observation count (across `coding`/`self_edit_coding`/`echo_projects_coding` sub-buckets) dwarfs
  every other bucket by 2-3 orders of magnitude (coding ≈99,027 vs. reasoning ≈248, creative ≈384).
- **Aggregation**: `self_model_updater._compute_task_performance()` computes a recent-window average
  and sample count per task type; `_compute_targets()` requires BOTH a real all-time observation count
  above threshold AND a real recent sample (a deliberate fix, per the source's own comment, against an
  earlier bug where a zero-recent-sample task type could trivially "win" via a default-0.0 average).
- **Update frequency**: `SelfModelUpdater._loop()` runs on a fixed 130s timer, unconditionally.
- **Selection algorithm**: lowest avg_quality_score among qualifying (well-observed, recently-sampled,
  below-threshold) task types; falls back to worst-quality-among-observed, then to a hardcoded
  `"coding"` default.
- **Persistence**: `memory/self_model.json`, plain JSON, overwritten each cycle — no built-in history.
- **Entry into `perform_self_edit()`**: **only as a fallback** — reached solely when the shadow file
  (Signal B, below) is absent or empty.

## 4. Shadow Signal Analysis (Signal B)

- **Source data**: whatever text `reflection_shard.py`'s generative free-association loop most
  recently produced — real MLX-model output, but about **whatever Echo happened to reflect on**, with
  no connection to self-edit performance data of any kind (confirmed by direct source read of
  `_generate_reflection()`).
- **Reflection extraction / keyword heuristic**: `shadow_model.propose_from_reflection()` — a pure,
  non-LLM keyword-count match against 4 fixed task types (reasoning/coding/creative/personal), 5-6
  keywords each; fires only above a `best_count >= 2` threshold; called unconditionally from
  `app/emergent_scheduler.py:723-724` on every real reflection cycle, regardless of topic relevance.
- **Persistence**: `memory/shadow_self_model.json` — merges the *current real* `self_model.json` as a
  baseline, then overwrites only `targets`.
- **Update frequency**: fires whenever a reflection happens to contain ≥2 keyword hits for some task
  type — live data (`shadow_accuracy.jsonl`, 2,028 total rows) shows this is frequent, roughly hourly.
- **Entry into `perform_self_edit()`**: checked **first**, unconditionally wins if present.

## 5. Arbitration Analysis

**Why is the weaker shadow signal allowed to override the empirically grounded one?** The source
code's own comment calls shadow the "highest-trust signal" with no further justification in that
function. Directly reading `shadow_model.py`'s own module docstring and `check_and_correct()` function
reveals this arbitration appears to **contradict the shadow module's own stated design intent**:
`shadow_model.py` frames itself explicitly as "an experimental copy... Echo can freely overwrite" and
its own `check_and_correct()` function *withholds* auto-applying a correction specifically because
"both sides of the shadow comparison trace to Echo's own outputs... no external anchor" — i.e., the
module that *produces* Signal B explicitly disclaims giving it unvalidated authority, while the
consumer (`perform_self_edit()`) treats it as authoritative by default. **"Highest trust" in this
codebase's own comment does not appear to mean "highest empirical reliability" — it more closely
describes "most recently and specifically proposed," a recency heuristic mistaken for a confidence
ranking.**

## 6. Historical Disagreement Table

Built by joining 103 real `self_edit_outcomes.jsonl` entries (every one with a computed quality
delta) to their nearest-preceding `shadow_accuracy.jsonl` reading. Representative rows (full 103-row
output was generated by this session's own correlation script; every row is available on request —
condensed here for readability):

| Timestamp | Shadow | Empirical | Actual | Pre | Post | Δ Quality | Winner |
|---|---|---|---|---:|---:|---:|---|
| 2026-07-06T09:58 | coding | coding | coding | 2.14 | 1.50 | −0.643 | shadow |
| 2026-07-07T06:24 | personal | reasoning | coding | 2.50 | 1.67 | −0.833 | neither |
| 2026-07-12T20:59 | personal | coding | coding | 2.29 | 4.00 | +1.714 | empirical |
| 2026-08-01T02:40 | creative | coding | coding | 2.50 | 4.00 | +1.500 | empirical |
| 2026-08-27T21:11 | personal | coding | coding | 2.50 | 4.00 | +1.500 | empirical |
| 2026-09-01T23:06 | reasoning | coding | coding | 2.29 | 2.43 | +0.135 | empirical |
| 2026-09-02T19:43 | coding | coding | coding | 2.47 | 1.00 | −1.471 | shadow |

**The single most important structural finding in this table**: the `Actual` column reads `coding`
in **all 103 of 103 rows**, with zero exceptions, spanning 2026-07-05 through 2026-09-02. This means:

- The **empirical** signal independently predicted the real actual target in **74/103 (71.8%)** of
  matched readings.
- The **shadow** signal predicted it in only **14/103 (13.6%)**.
- **Neither** matched in 15/103 (14.6%) — both signals said something else (reasoning/creative/general)
  while the real, tracked deploy still targeted `coding` regardless.

**This directly answers Part III's question ("is shadow actually wrong")**: yes, empirically, by a
wide margin — the empirical signal is the far better predictor of what a real, quality-tracked deploy
actually targets. But it also reveals a genuine, important nuance: **the shadow-override defect's
demonstrated real-world effect (the 2026-09-03T21:38:26 `'personal'`-targeted cycle found in the prior
investigation) never reached this tracked-outcome table at all** — that cycle resulted in
`staging_import_failed`, which does not appear to reach `self_edit_outcomes.jsonl`'s tracking. The
defect is real and demonstrated to alter what gets *attempted*; this table finds no evidence it has
ever altered what gets *quality-tracked as deployed*.

## 7. Quality/Outcome Analysis

Per the mission's Part V, "improvement" was **defined before looking at results**, using the
already-existing, already-computed signal (`self_edit_outcomes.jsonl`'s `quality_score.delta`, a
pre/post-window average of real `_score_response_quality()` scores on real subsequent `coding`-task
interactions) rather than an invented metric:

- **n = 103** real evaluated outcomes with a computed delta (of 179 total tracked entries).
- **Improved: 61 (59.2%). Worsened: 42 (40.8%). Neutral: 0.**
- **Mean delta: +0.103. Stdev: 0.635. t-statistic: 1.65 (n=103).** This does **not** clear the
  conventional 95%-confidence bar (roughly p≈0.10, two-tailed) — the mean is not statistically
  distinguishable from zero given the real variance in individual outcomes.
- **Mean delta by which signal matched the actual target**: empirical-matched = 0.098 (n=74),
  shadow-matched = 0.118 (n=14), neither-matched = 0.114 (n=15). **These are statistically
  indistinguishable from one another** — whichever signal happened to be "right" about the target
  carries no detectable relationship to the resulting quality change.

**Separating the categories the mission's Part V explicitly required, rather than blending them**:
Safety success (F1/F2/F3 gates holding, no destructive change reaching production unreviewed) is
robustly supported by this and the prior investigation's live evidence. Execution success (candidate
applies and passes the sandboxed import test) is real and quantifiable via the safety-blocked/
staging-import-failed/dry-run-staged distribution already documented in the prior investigation.
Quality improvement (this section) is **weak, not statistically significant, and roughly a coin
flip weighted slightly positive**. Targeting improvement (did the system choose a better subsystem)
could not be tested at all — see §6, there is no historical variation in actual target to test against.
Iterative improvement (did later attempts get more successful because of earlier information) is
addressed in §9 below.

## 8. Temporal Feedback Analysis

- **Temporal precedence**: confirmed real — `self_model.json`'s target is computed from
  `reflection_shard.jsonl` entries that necessarily predate it, and `perform_self_edit()`'s target
  read necessarily follows both. The causal ordering is genuine, not a coincidence of timestamps.
- **Persistence**: confirmed real — both `self_model.json` and `shadow_self_model.json` are plain
  disk files, re-read fresh on every relevant call, with no in-process cache found in either
  `self_model_updater.py` or `self_edit_manager.py`'s target-selection code path. This mirrors the
  restart-survival testing methodology already validated for the C1 mechanism in the prior phase of
  this project's work.
- **Causal isolation**: the specific edge tested here (self-model target → target_task_type) is not
  plausibly explained by original prompt context, retrieved text, or model choice — it is a direct,
  traced code read of a specific file field. It **could** plausibly be explained partly by scheduling
  (the 130s `SelfModelUpdater` timer and the reflection cycle's own cadence interact to determine which
  signal is "freshest" at any given `perform_self_edit()` call) rather than by any genuine
  quality-driven reasoning on shadow's part — consistent with §5's finding that shadow is a pure
  keyword-count artifact, not inference.
- **Outcome dependence**: **not demonstrated.** §7 found no relationship between which signal was
  "correct" and the resulting quality delta — a good historical outcome does not appear to produce
  different future targeting behavior than a bad one, at least not detectably in this data.

## 9. Error-Correction Analysis

**A real, narrow, within-cycle error-correction mechanism exists and was confirmed by direct source
read** (`app/core/self_edit_manager.py`, ~lines 1930-1990): on a first sandbox-test failure, the code
builds a retry prompt that **explicitly includes the real error/exception text**, generates a second
candidate, tests it, and separately records the retry's own success/failure via
`river.learn_from_sandbox_outcome()`. This is a genuine, if scoped, `attempt → failure → diagnosis
(real error fed back) → retry → re-verify` loop — real positive evidence for Part VII, distinct from
and smaller in scope than the target-selection loop this report is centrally about. It is explicitly
**single-retry, within one cycle** — not indefinite iteration, and not connected to the
25-minutes-later quality-delta measurement (§7), which arrives long after any retry window has closed.

**The larger, cross-cycle mechanism (`self_edit_convergence.json`'s `non_convergent_streak`) is real
in schema but currently reads 0 for all 4 live families** (`prose_stripping`, `response_shortening`,
`quality_scoring`, `unclassified`) despite this session's own live `SELF_EDIT.log` tail showing
several consecutive real failures. This investigation could not fully resolve whether the reset
condition (most likely: any candidate reaching `dry_run_staged` resets the streak, even without a real
production deploy) is working exactly as designed or is quietly inert in current practice — **flagged
as genuinely unresolved, not concluded either way.**

## 10. Revised Interpretation of the 426/463 Result

**The 92% figure and this session's 59.2%/40.8% figure measure two different things and must not be
combined into one narrative.** 426/463 (92%) — cited from a prior forensic index, not independently
re-derived this session — measures **passing the safety/import/fitness gate** (F1/F2/F3 plus an
AST-complexity comparison confirmed saturated at a perfect ceiling for all 25 currently-retained
deploys). This session's own independently-computed **59.2% improved / 40.8% worsened** (n=103) measures
**whether real subsequent production coding-task quality actually moved after a deploy** — a
completely different, later-stage, outcome-based measurement. Reclassifying the historical population
per the mission's Part VIII categories:

- **Safely blocked**: the large majority of the 463 historical attempts (per the prior forensic
  index's own framing; not independently re-tallied here).
- **Syntactically valid / passed the fitness gate**: 426/463 (92%), the correctly-scoped meaning of
  the original headline.
- **Quality improved** (of the 103 tracked, evaluated subset): 61 (59.2%).
- **Quality worsened**: 42 (40.8%).
- **Neutral**: 0.
- **Unknown/untracked**: 463 − 179 = 284 historical attempts never reached `self_edit_outcomes.jsonl`
  tracking at all (this figure blends across two different source documents with different population
  definitions and is presented as an approximate bound, not an exact reconciled count).

`P(quality improvement | accepted edit)` = 0.592. `P(quality regression | accepted edit)` = 0.408.
The mission's requested `P(quality improvement | feedback-informed target)` vs. `P(quality improvement
| baseline target)` split **cannot be computed**: 100% of the 103 tracked outcomes share the identical
actual target (`coding`), so there is no real historical contrast to condition on. This is stated
plainly rather than forcing an invented comparison.

## 11. Council-Rating Forensic Analysis

- **Exact mechanism**: `memory/council_cursor.json` = `{"position": 33471, "updated_utc":
  "2026-07-26T14:15:33Z"}`; `interaction_log.jsonl` currently holds 11,671 real lines.
  `_poll_and_rate()`'s `lines[cursor:]` on a shorter list silently returns `[]` — no exception raised,
  no log line emitted, a permanent, silent no-op.
- **Confirmed real rotation event**: `memory/interaction_log.jsonl.1.gz` exists, dated **2026-08-22**
  — direct physical proof the file was rotated (gzip+truncate) by `night_cycle.py`'s log-retention
  mechanism (a real 100MB cap, confirmed present in its `_LOG_RETENTION_TARGETS` list).
- **Timeline tension, stated honestly, not smoothed over**: the cursor's own `updated_utc` (July 26)
  predates the confirmed rotation (Aug 22) by roughly a month. If the cursor had kept advancing
  normally through that window, it would only have become invalid *at* the rotation, not a month
  before it. This suggests `_poll_and_rate()` itself may have stopped meaningfully executing around
  July 26 for a separate, not-yet-identified reason, with the later rotation compounding (or simply
  preserving) an already-stalled state rather than being the sole original trigger. **This was not
  resolved in this pass** — logs from that period have themselves already been rotated out by the same
  retention mechanism, so the original triggering event could not be directly recovered.
- **Why no liveness check caught it**: the existing `council_river_blend` check is a **static,
  source-anchor** check — it confirms `rate_one_entry()`'s source still calls
  `learn_from_council_rating()` gated by `is_council_trusted()`, which it genuinely does. It has no
  functional/data-freshness component (e.g., "has `council_ratings.jsonl` grown recently"), so a
  structurally-intact-but-starved mechanism reads as fully passing. This is the same class of gap this
  project's own history has already named once before for a different mechanism (`apply_to_code`).
- **Would repair produce a meaningful change**: plausibly yes — `is_council_trusted()` is confirmed
  `True` live, so a newly-sampled rating would immediately flow through the already-verified blend
  logic (0.3 council / 0.7 quality_score). Whether the resulting magnitude is large enough to matter is
  **not confirmed**, only structurally plausible.
- **Routing or content**: routing only — this feeds the same `model_task_stats` structure Signal A
  already populates; it is not a content-level channel.
- **Minimal regression test proposed** (not implemented): a check computing
  `interaction_log_line_count − cursor_position`, alerting if negative (cursor beyond file end) **or**
  if `council_ratings.jsonl`'s most recent timestamp is >48h old while `interaction_log.jsonl` has
  demonstrably grown in the same window — the second condition specifically catches a
  numerically-valid-but-stuck cursor the first condition alone would miss.

## 12. Minimum Safe Fixes (proposed, NOT implemented)

**Fix A — rebalance shadow-vs-empirical priority.** File: `app/core/self_edit_manager.py`,
`perform_self_edit()`'s target-selection block. ~5-20 LOC. Behavior changed: which of the two signals
wins when both are present. Expected causal edge: self-model target → actual targeting decision
(currently demoted). Safety: high — changes targeting, not any safety gate. Rollback: trivial
(priority-order revert). Test required: a controlled before/after agreement-rate comparison (§13).
Metric required: real target_task_type agreement rate against `self_model.json`'s own value over a
comparable window. Confounds: shadow's real-world effect on tracked outcomes is currently
undetectable (§6/§10), so this fix's realistic expected benefit should be stated modestly, not assumed
large.

**Fix B — repair the stale council cursor.** File: `app/core/council_rater.py`. ~5-15 LOC. Behavior
changed: whether new interaction_log entries get sampled and rated at all. Expected causal edge:
council rating → `RiverBrain.learn_from_council_rating()` → `model_task_stats`. Safety: very high — no
gate touched, purely restores an already-designed, already-trust-gated data flow. Rollback: trivial
(cursor file is small and easily reset/restored). Test required: confirm `council_ratings.jsonl`
resumes growing within one real polling cycle post-fix, and directly measure one real rating's effect
on `model_task_stats` (mirroring the existing before/after methodology already proven in this
project's own Finding 44). Metric required: real rating count growth + a measured `model_task_stats`
delta. Confounds: the blend weight (0.3/0.7) means even a full repair may only modestly shift an
already quality-score-dominated signal — a real measurement, not an assumption, is needed to confirm
magnitude.

## 13. Required Experiments

1. **Fix-B validation** (council cursor): post-fix, confirm real growth in `council_ratings.jsonl`
   within one cycle; directly measure a real rating's effect on `model_task_stats`.
2. **Fix-A validation** (arbitration priority): a pre-registered, restart-tested, control-tested
   before/after window comparing real `target_task_type` selections against `self_model.json`'s own
   value, confirming agreement rate rises — and confirming the shadow signal still applies when it
   *agrees* with the empirical one, so the fix doesn't silently disable Signal B entirely.
3. **`self_edit_convergence.json` zero-streak instrumentation**: log-only (no behavior change) tracing
   of exactly which condition resets `non_convergent_streak` on each real cycle, to resolve the §9
   ambiguity, falsifiable against the mechanism's own documented reset condition.
4. **Independent replication of the quality-delta significance test** at a larger n (this dataset,
   n=103, is not large relative to its own variance) — if the true effect is genuinely near-zero, a
   larger sample should keep the t-statistic near its current value or shrink it further; if a real
   positive effect exists, a larger sample should push the t-statistic higher.
5. **A controlled A/B/C/D arbitration experiment**, as the mission's Part IV specifies: Condition A
   (current arbitration), B (empirical-priority), C (shadow-only), D (no adaptive targeting/baseline),
   holding constant model pool, prompts, verification gates, and starting repo state where possible,
   with ordering randomized. **Not run in this pass** — proposed only, per the mission's explicit
   do-not-implement constraint; this is the most direct possible test of whether Fix A produces any
   real downstream difference at all, and should precede, not follow, applying Fix A in production.

## 14. Falsification Evidence

Reported prominently, per the mission's explicit instruction:

- Signal A's own real effect is demonstrably a **routing** effect (Finding 39's tag-boost, re-confirmed
  live) — the most defensible real consequence of this whole apparatus is on *which model answers*, not
  on self-edit quality specifically.
- **100% of tracked outcomes targeting `coding`, combined with a non-significant mean quality delta**,
  is jointly consistent with the null hypothesis that self-edit targeting has **no measurable effect
  on quality at all** — the system may simply always be doing the same thing (targeting coding) with
  a roughly flat, noisy outcome, regardless of any "adaptive" framing.
- Shadow's disagreement with the empirical signal (12/15 recent hourly readings) is more parsimoniously
  explained by "this is a keyword-count artifact with no semantic task-performance understanding" than
  by "shadow is doing inference and getting it wrong" — this investigation found direct evidence for
  the former, not merely failed to rule it out.
- **Regression-to-the-mean cannot be excluded** for the +0.103 mean delta: t=1.65 is below the
  conventional significance threshold, and the near-identical mean deltas across the
  empirical/shadow/neither-matched subgroups are exactly what pure noise around a shared baseline would
  produce.
- `reflection_shard.py`'s generative reflections (the actual text Signal B keyword-scans) were directly
  confirmed to be free-association, not outcome-grounded introspection — "reflection" in this specific
  mechanism describes what Echo mused about, not what happened in a self-edit cycle.
- The large n≈99,027 RiverBrain coding-bucket size gives a precisely-estimated *baseline*, but this
  investigation's separate, smaller (n=103) outcome-delta measurement shows the actual causal
  intervention (deploying a new file) has a weak, statistically marginal, possibly-zero effect — a
  large sample size for the baseline does not imply a large or reliable effect size for the
  intervention.
- The loop is real but **operates only at the level of target selection** — this investigation found
  no evidence it operates at any higher level, and found direct evidence (the significance test)
  arguing against a higher level, not merely an absence of evidence for one.

## 15. Final Level 0–5 Classification

**LEVEL 3 — Feedback causes persistent behavioral adaptation.**

Not Level 2, because the adaptation genuinely persists across restart (both `self_model.json` and
`shadow_self_model.json` are re-read fresh from disk, with a real, directly-observed instance of this
persistence causing an actual targeting deviation). Not Level 4, because no statistically defensible
evidence of measurable iterative improvement was found — the direct evidence gathered (t=1.65, p≈0.10,
40.8% worsened, no cross-subgroup difference) argues against Level 4 rather than merely falling short
of it. This is explicitly a classification of **targeting-level** adaptation, not content-level
learning, per Hard Rules 6/7/9/10.

## 16. Explicit Non-Claims

- This investigation does not establish why `council_rater.py`'s polling specifically stalled around
  2026-07-26 — only that it did, with a later, confirmed rotation event compounding the resulting
  staleness. The original trigger could not be recovered.
- `P(quality improvement | feedback-informed target)` vs. `P(quality improvement | baseline target)`
  could not be computed — 100% of tracked outcomes share the same actual target.
- This investigation does not establish that repairing the council-cursor bug would produce any
  measurable quality benefit — only that it is structurally ready to and would flow through an
  already-verified blend mechanism.
- This investigation does not resolve whether `self_edit_convergence.json`'s zero-streak state
  reflects correct design behavior or quiet inertness.
- This investigation does not establish whether RiverBrain's overwhelming coding-task-type sample
  dominance reflects a genuinely well-calibrated targeting choice or a self-reinforcing artifact of
  self-edit mechanically only ever generating code in the first place.
- This investigation does not claim the self-edit loop's Level-3 targeting adaptation constitutes
  learning, self-improvement, or any content-level change — it is reported strictly as persistent
  targeting adaptation, and the evidence gathered here argues specifically against a stronger claim,
  not merely for a weaker one.
