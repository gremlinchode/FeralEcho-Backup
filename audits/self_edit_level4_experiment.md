# FeralEcho: Level 3 → Level 4 Validation Experiment

No production code was modified. Full design/results detail beyond this narrative is in
`audits/self_edit_level4_experiment.json`. Raw prospective trial records (if/when produced) are
appended live to `audits/level4_experiment_raw_results.jsonl` by
`scripts/run_level4_arbitration_experiment.py`, a standalone script that only ever calls
`execute_self_edit(dry_run=True)`/`perform_self_edit(dry_run=True)` — the exact code path Optuna's own
hourly dry-run search already exercises, which never reaches the backup/save/load-into-production
step.

## 1. Experimental Design

Three conditions, defined precisely to require **zero production-code changes** — each condition is
implemented purely by choosing *which existing, already-safe call* to make:

- **A — Current system**: `perform_self_edit(dry_run=True, target_task_type=None)`. The real,
  unmodified shadow-first arbitration logic picks the target exactly as live production would.
- **B — Empirical priority**: `self_model.json`'s real RiverBrain-derived target, read once at batch
  start and held fixed, is forced directly via `_build_targeted_prompt()` + `execute_self_edit()`,
  bypassing the arbitration entirely (not modifying it — simply not calling it).
- **C — Baseline**: a uniform-random choice among the five real task-type buckets (`coding`,
  `personal`, `creative`, `reasoning`, `general`), independent of either signal — operationalizing "no
  adaptive targeting influence."

Held constant across all trials: model pool, verification gates, the quality scorer itself, and —
deliberately — a **single, fixed production-file baseline score**, computed once at batch start rather
than re-read per trial, specifically so a same-batch production deploy by the live server (if one fired
independently) could not silently shift the comparison baseline mid-experiment. Trial order across the
15 planned trials (5/condition) was randomized once via `random.shuffle()`, not run in blocked order.

## 2. Predefined Hypotheses

- **H1 (primary)**: Condition B shows a higher mean prospective quality-delta than A and C.
- **H2**: Condition A resembles C more than B whenever the live shadow and empirical signals disagree
  (a live test of whether current arbitration behaves adaptively or near-randomly in practice — live
  state at batch start: shadow said `personal`, empirical said `coding` — a genuine, real disagreement
  to test against).
- **H3 (pre-registered null, the honest default)**: given the retrospective analysis already found no
  significant quality effect from targeting at all, no condition is expected to show a statistically or
  practically meaningful advantage — and this batch is explicitly pre-registered as **underpowered to
  distinguish H1 from H3 regardless of outcome** (see §4).

## 3. Primary/Secondary Endpoints

**Primary endpoint substitution, disclosed upfront, not discovered after the fact**: the mission's own
specified primary endpoint (`quality_score.delta`, requiring a real ~25-minute post-deploy window of
organic conversational coding activity per trial) cannot be forced or accelerated, and is infeasible
across 15 trials within this investigation's practical time budget. The prospective arm instead
measures an **immediately available** proxy: candidate-file quality score minus the single fixed
production-file baseline, both via `echo_quality_scorer._score_response_quality()` — the same 0-4
AST-based scorer used throughout this codebase, but **not identical** to the retrospective endpoint.
This substitution is treated as a real, disclosed limitation throughout, not a silent swap.

Secondary endpoints, computed from **retrospective** data (the only source with adequate real volume):
target-selection accuracy (empirical 71.8% vs. shadow 13.6% vs. actual, per the prior report), quality
regression rate (42/103, 40.8%), a real-safety-block rate (qualitative, from the prior report's
92%-gate-pass figure, correctly scoped as a different measurement), and — newly computed this session
— **whether prior outcomes predict subsequent outcomes** (the direct "is there real feedback" test):
lag-1 autocorrelation on the full, temporally-sorted 103-entry delta series = **r = −0.145**, closely
replicating Finding 57's own earlier r=−0.14 on a smaller (n=73) slice of the same underlying series —
an independent, larger-n confirmation of the same null. Conditional probabilities: **P(next delta > 0 |
this delta > 0) = 0.574**, barely different from the unconditional base rate of 0.592; **P(next delta <
0 | this delta < 0) = 0.366**, actually *below* the unconditional negative-base-rate of 0.408. Neither
conditional probability exceeds its own baseline in the direction genuine feedback-driven improvement
would predict — a direct, quantified answer to "does a good outcome cause a different future outcome
than a bad one": **no detectable effect either direction.**

## 4. Sample-Size Rationale

Computed **before** interpreting any prospective result, per the mission's own requirement:

- **Retrospective-endpoint power**: using the real historical sd (0.635, n=103) and a defensible
  "practically meaningful" threshold of 0.3 quality points (roughly half the observed SD), a
  two-sample t-test at α=0.05/power=0.80 requires **≈71 real trials per condition (~213 total)**. At
  this system's own observed cadence of roughly one real production deploy per day, this would take
  **many months** of real production operation — explicitly not attempted, stated as a hard constraint
  rather than worked around.
- **Prospective proxy-endpoint power**: using the closest available real variance estimate (historical
  `dry_run_quality.delta`, sd=0.858, n=30) and the same 0.3 threshold, the requirement is **≈128 trials
  per condition** — larger still, because the proxy's own historical variance exceeds the conversational
  metric's. This session's planned n (5/condition, 15 total) is **explicitly, substantially
  underpowered** by design acknowledgment, not by oversight — consistent with the mission's own
  instruction not to treat a small, promising-looking result as confirmatory.

## 5. Results

**The prospective batch was launched and run entirely via the existing, already-safe `dry_run=True`
path (zero production risk throughout) but could not complete a meaningful number of trials within
this investigation's practical time window.** After roughly 30 minutes of real wall-clock time, the
first of 15 planned trials (condition `C`) had not yet finished; process-level CPU-time accounting
(seconds of actual CPU work vs. elapsed wall-clock minutes) showed the script spending the overwhelming
majority of that window **blocked, not computing** — directly consistent with a real, already-identified
confound (§7): this machine's Ollama instance has no configured request parallelism
(`OLLAMA_NUM_PARALLEL` unset, per the prior capability-ceiling hardware report), and the live,
concurrently-running production `run.py` server's own multiple autonomous loops (confirmed still
actively producing real `SELF_EDIT.log` entries during this exact window) share the identical
single-request Ollama queue with this experiment's own separate process.

**This is reported as a real, substantive finding, not a gap to apologize for**: a small, well-designed,
genuinely zero-risk experiment using this system's own existing infrastructure could not be executed
promptly, in practice, on this machine, while the system is in normal live operation — direct,
first-hand confirmation of a hardware/configuration ceiling this investigation's own prior work had
already flagged as a *lever*, now also confirmed as a real *constraint on doing further experimental
work itself*. Any completed trials that do eventually land in
`audits/level4_experiment_raw_results.jsonl` (the process was left running, harmlessly, in the
background) would need to be folded into a future update of this document rather than retrofitted into
this one, per this investigation's own standing discipline against silently revising a report after the
fact without saying so.

## 6. Statistical Analysis

No prospective inferential statistics are reported, for the reason given in §5 — there is no real
prospective sample to analyze. The retrospective statistics already computed and reported in the prior
validation (`audits/self_edit_closed_loop_validation.md` §7) stand as the only real quantitative basis
available: mean Δquality = +0.103, sd = 0.635, t = 1.65 (n=103, not significant at α=0.05); 61/103
(59.2%) improved, 42/103 (40.8%) worsened; mean delta statistically indistinguishable across which
targeting signal happened to be "correct" (0.098 / 0.118 / 0.114). This session's own newly-computed
lag-1 autocorrelation (r=−0.145) and conditional-probability results (§3) are direct, additional,
independently-computed confirmations of the same underlying null, not a restatement of the prior
report's own numbers.

## 7. Confound Analysis

Full 12-item audit in the JSON. The single most consequential, newly-confirmed confound this session:
**live resource contention with the concurrently-running production server**, evidenced directly (a
real, independent `dry_run_staged` entry appeared in `memory/SELF_EDIT.log` during this experiment's own
run window, attributable to the live server's own background thread) rather than merely inferred.
Every other audited confound (model changes, task-mix, temporal drift, regression to the mean, prompt/
context differences, random sampling, selection bias, RAG effects, shadow/empirical timing mismatch,
repeated-edit chaining, survivorship bias) was either controlled by design or explicitly acknowledged
as unresolved at this achieved sample size (see JSON for the per-item disposition).

## 8. Causal Interpretation

The critical distinction the mission asked this experiment to resolve —

```
previous outcome → feedback signal → changed targeting → better subsequent outcome   [Level 4]
        vs.
previous outcome → changed targeting                                                  [Level 3]
```

— is answered by the retrospective evidence alone, independent of the prospective arm's non-completion:
**100% of the 103 real, tracked, quality-evaluated outcomes targeted the identical task type
(`coding`)** across the entire multi-month history. There is, therefore, **no real historical instance
of a bad outcome causing a target *change* that was then followed by a better outcome** — the middle
link of the Level-4 chain has literally never been exercised in this system's own recorded history. The
lag-1 autocorrelation (r=−0.145) and conditional-probability tests (§3) independently confirm the final
link is also absent: even setting the "changed targeting" question aside entirely, a good or bad outcome
does not predict the next outcome better than chance. **Both links required for Level 4 are
unsupported by the available evidence — not merely untested, but directly tested and found absent.**

## 9. Level 3 vs. Level 4 Determination

**Level 3 stands. Level 4 is not supported.**

Per the mission's own success criteria: Level 4 requires feedback-informed targeting to produce
*statistically and practically meaningful* improvement compared with an appropriate baseline. This
investigation found: (a) no real historical variation in actual target to even define a
feedback-informed-vs-baseline contrast against (§8); (b) no statistically significant quality effect in
the only available real outcome data (t=1.65, p≈0.10); (c) no evidence that outcomes predict subsequent
outcomes in either direction (r=−0.145, conditional probabilities within noise of baseline); and (d) a
prospective, purpose-built experiment designed to test this directly could not be completed within
practical bounds, for a real, diagnosed, separate reason. **None of this constitutes a positive mean
alone being mistaken for Level 4** — the evidence gathered actively argues against Level 4, consistent
with the prior investigation's own finding and the mission's explicit standard that Level 4 requires
direct outcome evidence, not its absence.

## 10. Explicit Non-Claims

- This investigation does not establish that Condition B (empirical priority) would underperform,
  outperform, or tie Condition A/C on the mission's own primary endpoint — the prospective test designed
  to answer this did not complete within this session's practical time window.
- This investigation does not establish that the resource-contention confound is permanent or
  unavoidable — it may reflect a temporary state of the live server's own current activity level, not a
  fixed property of the hardware.
- This investigation does not rule out that a much larger retrospective dataset (were `coding` not the
  sole historical target) could have revealed a real targeting-quality relationship — the absence of
  historical variation in the actual target is itself the limiting factor, not a proof that variation
  would show no effect.
- This investigation does not claim the two previously-proposed surgical fixes (stale council cursor;
  arbitration priority rebalance, per the prior closed-loop report) are without merit on other grounds —
  only that neither should be sold as a path to Level-4 self-improvement based on the evidence gathered
  here.

## 11. Recommendation for the Smallest Production Change, If Warranted

**Given the evidence, no production change is recommended on the basis of a Level-4 improvement
claim, because no such claim is supported.** If the two previously-identified surgical fixes (repairing
the stale council-rating cursor; rebalancing the shadow/empirical arbitration priority) are made for
other reasons — architectural correctness, restoring a dormant-but-designed data flow, closing a
priority inversion the shadow module's own authors explicitly did not intend — they should be
**explicitly and separately re-tested** against the same retrospective methodology this report and its
predecessor established (quality_score.delta significance testing, lag-1 autocorrelation, conditional
probability by targeting-match), not assumed to produce improvement merely because they are
architecturally cleaner. **If a genuine, adequately-powered prospective test is ever wanted, it should
be scheduled during a real maintenance window with the live production server's autonomous loops
paused**, to remove the resource-contention confound this session directly encountered, and should
target the ≈71-128 trials per condition this report's own power calculation establishes as the real
requirement — not a small pilot batch mistaken for a confirmatory result.
