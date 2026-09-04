# FeralEcho: Tier-3 Held-Out Scoring / Spot-Check / Unblinding Analysis

**Analysis timestamp**: 2026-09-04 (same session as execution). **Source artifacts**: `audits/tier3_apparatus/
heldout_results.jsonl` (32 raw records, read-only), `audits/tier3_apparatus/held_out_task_suite.json` (now
legitimately unblinded — this is the scoring phase), `audits/tier3_heldout_execution_report.{md,json}` (the
execution-forensics record). **No raw artifact was modified.** No candidate was re-generated, retried, or
re-run. No seed, parameter, model, or apparatus setting was changed. This is a NEW artifact, separate from the
raw results and from the execution report — a scoring/analysis layer on top of unmodified data.

## 1. Raw Evidence Verification

Directly re-checked against the raw JSONL, not assumed from the execution report's own narrative:

| Check | Result |
|---|---|
| 32 expected records | ✅ Exactly 32 |
| 8 candidates per arm | ✅ 4 arms × 8 tasks, confirmed |
| No duplicates | ✅ Zero duplicate (task, arm) pairs |
| No missing candidates | ✅ Zero missing pairs against the full 8×4 expected set |
| Model pinning | ✅ 24/24 non-council records used `qwen2.5-coder:7b`, zero drift |
| Call counts | ✅ `BASE_1`=1, `ARCH_PIPELINE_ISOLATED`=1, `BASE_N`=4, `ARCH_COUNCIL`=4 (generative) uniformly |
| Ground-truth availability | ✅ 32/32 records carry a real integer `call_id` (no `PIPELINE_NO_GROUND_TRUTH` sentinel anywhere — the isolation fix holds completely in real execution) |
| Isolation / side effects | ✅ `side_effects_so_far` advances by exactly +4 per real `ARCH_COUNCIL` execution (32 total across 8), zero from the other 24 executions |
| Truncation classifications | 2 flagged (`held_03`/`ARCH_COUNCIL`, `held_04`/`ARCH_COUNCIL`), both via `TEXT_BACKSTOP_TRUNCATED` — **see §3, both corrected on spot-check** |
| Task-logic-failure classifications | 12 recorded (10 after reclassification is applied — see §3, net direction unchanged for `passed`) |
| Infrastructure-failure status | ✅ Zero — `INFRASTRUCTURE_FAILURE` never occurred |

**No discrepancy was found between the raw artifacts and the execution report's own claims.** Every figure in
`tier3_heldout_execution_report.md` (32 records, 100% model pinning, 0 errors, 0 infrastructure failures, the
`ARCH_COUNCIL` 5-call warm-up present in all 8 real executions) is independently reproduced here from the raw
file directly. Proceeding to interpretation.

## 2. Scoring Per the Predefined Protocol

The scoring rules were fixed **before** this run: `objective_verify()` (real kernel-sandboxed execution of the
candidate against the task's real, pre-written `test_code`) determines `passed` (ground truth, binary);
`classify_result()` (the Objective-1-repaired, per-call-scoped classifier) assigns exactly one of `PASS` /
`TASK_LOGIC_FAILURE` / `GENERATION_TRUNCATED` / `INFRASTRUCTURE_FAILURE`. **No new scoring method was invented
for this analysis.** The only action taken here was to independently *re-run* the same, already-existing
`objective_verify()` function against the already-stored `candidate_code` for all 32 records — a reproducibility
check, not a new rule.

**Result: 32/32 independently reproduced exactly.** Every recorded `passed` value matches a fresh, independent
re-execution of the real sandbox test. The scoring pipeline is deterministic and trustworthy for the primary
correctness judgment.

## 3. Spot-Check Against Actual Outputs

All 32 candidates were inspected (full coverage, not a 20% sample, given the tractable size) — `candidate_code`
length/coherence, `raw_response` completeness, and fence-count patterns were checked for every record.

### Correction 1: `held_03` / `ARCH_COUNCIL`

- **Classifier said**: `GENERATION_TRUNCATED` (`truncation_evidence_type: TEXT_BACKSTOP_TRUNCATED`).
- **Ground truth actually indicates**: the real `done_reason` signal (checked first, per the classifier's own
  logic) did **not** report `"length"` — that is precisely why this fell through to the secondary text-backstop
  heuristic in the first place. Direct inspection of `raw_response` (867 chars) shows a single, unclosed opening
  ` ``` ` fence at character index 0, followed by a **complete, syntactically valid, semantically coherent**
  `ThreadSafeLRUCache` class — every method fully defined, no dangling/incomplete statement, ending cleanly at
  `self.cache.move_to_end(key)  # move to the end for MRU`. The real, identifiable bug: `get()`/`put()` write
  `self.cache[key] = None` instead of the actual value — a genuine semantic error (confirmed independently by
  re-running the real sandbox: `AssertionError` on `cache.get(1) == 1`, not a crash from incomplete code).
- **Correction justified**: yes, per the predefined protocol's own stated design intent (ground truth is
  authoritative; the text-backstop exists to catch what ground truth *misses*, not to override a case where
  ground truth already indicated normal completion) and per direct evidence (complete code, clean ending, a
  specific coherent bug). **Corrected: `GENERATION_TRUNCATED` → `TASK_LOGIC_FAILURE`.** `passed` is unaffected
  (`False` either way — already independently reproduced in §2).

### Correction 2: `held_04` / `ARCH_COUNCIL`

- **Classifier said**: `GENERATION_TRUNCATED` (`truncation_evidence_type: TEXT_BACKSTOP_TRUNCATED`).
- **Ground truth actually indicates**: identical pattern — a single unclosed opening fence at index 0 of a
  760-char response, followed by a **complete** `TokenBucketLimiter` class with a real, specific bug:
  `elapsed_seconds = now - self.clock()` calls `self.clock()` a second time instead of tracking the prior
  check's timestamp, making `elapsed_seconds` always ≈0 — a genuine logic error (confirmed: `AttributeError`
  on `.clock` in a related candidate's variant of this same bug family, and a clean assertion-shaped failure
  here), not a truncation artifact.
- **Correction justified**: same reasoning as Correction 1. **Corrected: `GENERATION_TRUNCATED` →
  `TASK_LOGIC_FAILURE`.** `passed` unaffected (`False` either way).

### Verification this is not a broader pattern

A fence-count audit was run across **all 32** raw responses, not just the two flagged ones. Every other record
shows either 0 fences (no fence usage) or exactly 2 (a proper open/close pair) — both even counts, so the
text-backstop never fires. **Only these two `ARCH_COUNCIL` records show an odd count, and both are false
positives on direct inspection.** This is a real, narrow, disclosed limitation of the truncation heuristic —
isolated to `ARCH_COUNCIL`'s own synthesis step specifically (2 of its 8 real syntheses opened with an unclosed
fence; zero of the other 24 records across the other three arms did this even once) — worth noting as a
genuine, if minor, qualitative observation about the council-synthesis mechanism's own output habits, separate
from the correctness question.

**Net effect of both corrections, stated plainly**: this makes `ARCH_COUNCIL`'s result *look worse*, not better
— two candidates move from an "excused" failure category (truncation, which could be read as environmental
rather than architectural) to a genuine, architecture-attributable logic failure. `ARCH_COUNCIL`'s overall
pass/fail tally (3/8) is **unchanged** by this correction; only the failure-mode attribution changes. No other
classification was found to disagree with the evidence — **all 30 other classifications are confirmed correct
as recorded.**

### Corrected classification tally

| Arm | PASS | TASK_LOGIC_FAILURE | GENERATION_TRUNCATED | INFRASTRUCTURE_FAILURE |
|---|---|---|---|---|
| `BASE_1` | 5 | 3 | 0 | 0 |
| `BASE_N` | 6 | 2 | 0 | 0 |
| `ARCH_PIPELINE_ISOLATED` | 4 | 4 | 0 | 0 |
| `ARCH_COUNCIL` (corrected) | 3 | **5** | **0** | 0 |

## 4. Paired Comparisons

All four candidates share the identical 8 held-out tasks, permitting genuine paired analysis (not treated as
four independent groups). Full per-task outcomes:

| task | category | `BASE_1` | `BASE_N` | `ARCH_PIPELINE_ISOLATED` | `ARCH_COUNCIL` |
|---|---|---|---|---|---|
| held_01 | bug fixing (interval merge) | PASS | PASS | PASS | PASS |
| held_02 | bug fixing (increasing run) | PASS | PASS | PASS | PASS |
| held_03 | concurrency (LRU cache) | PASS | PASS | PASS | **FAIL** |
| held_04 | concurrency (token bucket) | FAIL | FAIL | FAIL | FAIL |
| held_05 | algorithmic edge case (RLE) | FAIL | FAIL | **PASS** | FAIL |
| held_06 | algorithmic edge case (circular) | FAIL | **PASS** | FAIL | FAIL |
| held_07 | refactoring (lookup table) | PASS | PASS | **FAIL** | PASS |
| held_08 | refactoring (memoization) | PASS | PASS | **FAIL** | **FAIL** |
| **Pass rate** | | **5/8 (62.5%)** | **6/8 (75.0%)** | **4/8 (50.0%)** | **3/8 (37.5%)** |

**Two tasks (held_01, held_02 — both "bug fixing") show zero discrimination — all four arms pass both.** One
task (held_04 — the token-bucket rate limiter) is a universal failure — all four arms fail, a genuinely hard
task that discriminates nothing about architecture. The remaining 5 tasks carry all of this comparison's real
signal.

### BASE_1 vs BASE_N — *does extra attempts + synthesis (same model) help?*

- 5/8 vs 6/8. **Absolute difference: +12.5pp in favor of `BASE_N`.**
- Discordant pairs: 1 (`held_06`, favors `BASE_N`); 0 favor `BASE_1`.
- Exact McNemar two-sided p-value: **1.0** (a single discordant pair carries no statistical power).
- **Reading**: a small, directionally-positive-for-more-effort signal, entirely carried by one task, not
  distinguishable from noise at this n.

### BASE_1 vs ARCH_PIPELINE_ISOLATED — *the cleanest single-call architectural-framing test*

- 5/8 vs 4/8. **Absolute difference: −12.5pp** (the isolated self-edit framing did slightly *worse*).
- Discordant pairs: 2 favor `BASE_1` (held_07, held_08), 1 favors `ARCH_PIPELINE_ISOLATED` (held_05).
- Exact McNemar two-sided p-value: **1.0**.
- **Reading**: no advantage for the isolated framing; the small negative gap is well within noise at n=8. Two
  of `ARCH_PIPELINE_ISOLATED`'s losses have a distinct, notable failure signature — see §9.

### BASE_N vs ARCH_COUNCIL — *the pre-registered primary H1/H4 comparison (both matched on generative call count)*

- 6/8 vs 3/8. **Absolute difference: −37.5pp** (Council underperformed the compute-matched same-model
  baseline).
- Discordant pairs: **3, all favoring `BASE_N`** (held_03, held_06, held_08); **zero favor `ARCH_COUNCIL`.**
- Exact McNemar two-sided p-value: **0.25** — does not cross conventional significance (α=0.05), despite the
  effect size crossing the pre-registered ≥25pp magnitude threshold.
- **Reading**: this is the most consequential comparison in the experiment. The direction is completely
  one-sided (0 of 3 discordant pairs favor Council) and the magnitude clears the pre-specified bar — but the
  sample is small enough that this specific p-value cannot rule out chance. Both things are true at once; see
  §9 for the full adversarial treatment.

### BASE_1 vs ARCH_COUNCIL — *the broad architectural comparison (reported, not treated as primary)*

- 5/8 vs 3/8. **Absolute difference: −25.0pp.**
- Discordant pairs: 2 favor `BASE_1` (held_03, held_08); 0 favor `ARCH_COUNCIL`.
- Exact McNemar two-sided p-value: **0.5**.
- **Reading**: same direction as the primary comparison, weaker power (fewer discordant pairs since `BASE_1`
  itself already loses one of its own comparisons to `BASE_N`).

## 5. Call-Budget / Compute Asymmetry — Preserved, Not Hidden

**`ARCH_COUNCIL` made 5 real `_ollama_query()` calls per candidate in every one of its 8 real executions this
run, not 4.** Confirmed directly from the raw `total_real_ollama_calls_including_warmup` field: value `5`, all
8 times, zero exceptions. The 5th call is `river_deliberation._warm_up_echo()` — a real, unconstrained-length
ping to the synthesis model (`echo:latest`) issued before the actual council loop; its own response content is
always discarded, never fed into synthesis, never scored. Its real wall-clock/compute cost is included in the
recorded `generation_time` (mean `ARCH_COUNCIL` generation time this run: ~36.0s, versus `BASE_1`'s ~5.9s and
the sum of `BASE_N`'s per-attempt timings — a materially larger real-time footprint per candidate).

**This is not removed, bypassed, or compensated for anywhere in this analysis.** The `BASE_N` vs `ARCH_COUNCIL`
comparison in §4 is matched on *generative* call count (4 vs 4) and `max_tokens` (2048 vs 2048 per generative
call) — the two dimensions the apparatus was explicitly designed to equalize — but is **not** matched on total
real compute, since `ARCH_COUNCIL` genuinely spends one additional real call. **The direct implication for
interpretation**: `ARCH_COUNCIL`'s underperformance in §4 occurred *despite* having strictly more real compute
available to it than `BASE_N`, not because of having less. If anything, this makes the observed gap slightly
more notable, not less — extra, if content-discarded, compute did not translate into a compensating advantage.
The four arms in this experiment are **not** perfectly equal-call or perfectly equal-compute conditions, and no
claim in this report treats them as such.

## 6. Effect Sizes and Uncertainty

| Comparison | n (pairs) | Absolute diff | Discordant (a/b) | Exact McNemar p | Predefined threshold | Threshold crossed? |
|---|---:|---:|---|---:|---:|---|
| `BASE_1` vs `BASE_N` | 8 | +12.5pp | 0/1 | 1.0 | ±25pp | No |
| `BASE_1` vs `ARCH_PIPELINE_ISOLATED` | 8 | −12.5pp | 2/1 | 1.0 | ±25pp (Level A) | No |
| `BASE_N` vs `ARCH_COUNCIL` | 8 | −37.5pp | 3/0 | 0.25 | ≥25pp (H1 GO) | **Yes, in the direction opposite H1** |
| `BASE_1` vs `ARCH_COUNCIL` | 8 | −25.0pp | 2/0 | 0.5 | ≥25pp | Yes (exactly at the boundary), opposite direction |

**95% Wilson confidence intervals on each arm's own raw pass rate** (individual, not paired — included for
context, since paired McNemar is the primary test): `BASE_1` 62.5% [30.6%, 86.3%]; `BASE_N` 75.0% [40.9%,
92.9%]; `ARCH_PIPELINE_ISOLATED` 50.0% [21.5%, 78.5%]; `ARCH_COUNCIL` 37.5% [13.7%, 69.4%]. **Every interval
spans more than 40 percentage points and all four overlap substantially with each other** — this alone is a
direct, quantitative statement of how little n=8 per arm can distinguish.

**No test was substituted for a more favorable one.** Exact (not asymptotic/chi-squared) McNemar was used
throughout because it is the correct, conservative choice for small, paired binary samples — the design
protocol's own pre-registered choice. **No percentage difference is described as "significant" on its own** —
every effect size above is reported alongside its actual p-value, and none reaches p<0.05.

**Explicit small-sample discussion**: with only 8 held-out tasks, and given that 2 of those 8 (held_01, held_02)
show zero discrimination and 1 (held_04) is a universal failure, the *effective* discriminating sample for any
given comparison is often as few as 3-5 tasks. A single task's outcome flipping (e.g., if `held_03` had gone
the other way) would materially change several of the reported percentages. This is exactly the outcome the
apparatus's own design documents anticipated as "the likely, honest outcome at n=8/arm" — a real signal, not
statistically confirmable at this scale, requiring the pre-planned confirmatory sample size before any of these
directional findings could be treated as established.

## 7. H1–H4 Hypothesis Table

| Hypothesis | Relevant comparison | n | Result | Effect size | Threshold | Statistical result | Verdict |
|---|---|---:|---|---:|---:|---|---|
| **H1** — architecture contributes measurable correctness beyond the model, at equal budget | `ARCH_COUNCIL` vs `BASE_N` | 8 | `BASE_N` wins | −37.5pp (opposite of H1's predicted direction) | ≥25pp for H1-GO | McNemar p=0.25 (not significant) | **NOT SUPPORTED** — the threshold-crossing effect observed runs counter to H1, not in its favor; not statistically confirmable at n=8 |
| **H2** — architecture cannot overcome the model's limitations even at equal/greater budget | `ARCH_COUNCIL` vs `BASE_N`; `ARCH_PIPELINE_ISOLATED` vs `BASE_1` | 8 (each) | Council underperformed (threshold-crossing); isolated framing underperformed (sub-threshold) | −37.5pp / −12.5pp | n/a (H2 is the complement of H1) | p=0.25 / p=1.0 | **SUPPORTED for the `ARCH_COUNCIL` comparison** (real, one-directional, threshold-crossing, though not p<0.05); **INCONCLUSIVE for the `ARCH_PIPELINE_ISOLATED` comparison** (sub-threshold, statistically indistinguishable from noise) |
| **H3** — existing evaluators fail to capture meaningful differences | Spot-check (§3) of all 32 candidates against real sandboxed ground truth | 32 | 0/32 discrepancies in the primary pass/fail judgment; 2/32 corrected in the *secondary* truncation-classification layer | n/a | n/a | 32/32 independently reproduced | **NOT SUPPORTED** for the primary correctness evaluator (highly reliable, independently reproduced); a real, narrow, now-corrected limitation exists in the secondary truncation heuristic specifically, disclosed in §3 |
| **H4** — Council's apparent advantage, if any, is primarily compute/diversity rather than uniquely valuable orchestration | `ARCH_COUNCIL` vs `BASE_N` | 8 | `BASE_N` wins (Council did not merely fail to win — it lost) | −37.5pp | pre-registered rule: "`ARCH_COUNCIL` ≈ `BASE_N` or `BASE_N` wins" → supports H4 | McNemar p=0.25 | **SUPPORTED**, per the design's own pre-registered decision rule — **with the explicit caveat that this run never produced a Council win to explain in the first place, so the narrower original H4 question (is a win explained by diversity or orchestration) remains genuinely untestable by this design regardless of outcome polarity** (the pre-existing H4 boundary, unchanged) |

**No hypothesis is marked FALSIFIED.** None of the observed effects reach conventional statistical significance
(all p≥0.25), so none can be said to definitively disprove its corresponding hypothesis — only to fail to
support it, in some cases with a real, one-directional, threshold-crossing signal pointing the other way.

## 8. Direct Answers to the Investigation Questions

1. **Does `BASE_N` actually outperform `BASE_1`?** Marginally, yes in raw numbers (+12.5pp), but on a single
   discordant task with no statistical power (p=1.0). Not a robust finding.
2. **Does `ARCH_PIPELINE_ISOLATED` outperform `BASE_1`?** No — it underperforms slightly (−12.5pp), sub-threshold,
   statistically indistinguishable from noise (p=1.0).
3. **Does `ARCH_COUNCIL` outperform `BASE_N`?** No — the reverse: `BASE_N` outperforms `ARCH_COUNCIL` by 37.5pp,
   with a completely one-directional discordant-pair pattern (3-0).
4. **Does `ARCH_COUNCIL` outperform `BASE_1`?** No — `BASE_1` outperforms `ARCH_COUNCIL` by 25.0pp.
5. **Does any comparison cross the predefined effect-size threshold?** Yes — `BASE_N` vs `ARCH_COUNCIL` (−37.5pp)
   and, at the exact boundary, `BASE_1` vs `ARCH_COUNCIL` (−25.0pp) — both in the direction opposite the
   architecture-benefit hypotheses.
6. **Is any apparent advantage/disadvantage robust enough to support the corresponding hypothesis?** The
   `ARCH_COUNCIL` underperformance is the closest this dataset comes to a robust pattern — one-directional across
   all discordant pairs, crossing the pre-registered magnitude bar — but "robust" in the statistical-confidence
   sense would require p<0.05, which this does not reach. It is a real, consistent, but not yet statistically
   confirmed signal.
7. **Are the truncations materially affecting the Council result?** No, not after correction — both were
   reclassified to `TASK_LOGIC_FAILURE` in §3, and `passed` was `False` in both cases either way, so the raw
   pass/fail tally used in every comparison above was never affected by the truncation-classification question.
8. **Does the known five-call asymmetry make any interpretation substantially weaker?** It does not weaken the
   *direction* of the finding (extra compute did not help Council catch up) but it does mean `ARCH_COUNCIL`
   cannot be described as tested under a strictly equal-or-lesser compute budget than `BASE_N` — a real,
   disclosed caveat on any claim about "compute-matched" comparison, addressed explicitly in §5.

## 9. Adversarial Interpretation

**Attempting to disprove the apparent `ARCH_COUNCIL` disadvantage:**

- *Could this be sampling noise?* Yes, plausibly, and this must be stated as the leading alternative explanation
  — p=0.25 is a real, non-trivial probability of observing a split this lopsided (or more so) under a true null
  of no difference. This is not proof of noise, but noise cannot be ruled out.
- *Could it be explained by additional inference budget?* No — if anything, the extra warm-up call gave
  `ARCH_COUNCIL` *more*, not less, real compute than `BASE_N`, working against this as an explanation for its
  underperformance.
- *Could it be caused by the Council's extra warm-up specifically?* Not directly on correctness (its output is
  discarded), but it correlates with a genuine, distinct qualitative finding: `ARCH_COUNCIL`'s synthesis step is
  the *only* mechanism, across all 32 real candidates, that produced a response opening with an unclosed code
  fence (2 of its 8 real outputs) — a real, disclosed formatting quirk of the council-synthesis path specifically,
  worth further attention on its own terms even though it did not change any PASS/FAIL outcome here.
- *Could it be a task-composition artifact?* Partially checked and largely ruled out: `ARCH_COUNCIL`'s 3 losses
  to `BASE_N` span three *different* categories (concurrency, algorithmic edge case, refactoring), not one
  narrow task type — the pattern is not obviously an artifact of a single overrepresented category, though with
  only 2 tasks per category, this cannot be fully excluded either.
- *Could it be driven by one or two candidates?* Yes, literally — the entire 37.5pp gap is carried by exactly 3
  of 8 tasks (held_03, held_06, held_08). This is stated plainly, not hidden: a small sample means a small
  number of candidates determines the whole result.
- *Would the predefined threshold regard this as meaningful?* Yes, by the letter of the pre-registered rule (§7).
- *Does the paired analysis agree with the aggregate percentage?* Yes — the paired, task-level view (§4) and the
  aggregate percentage tell the same story; the aggregate is not hiding a more mixed underlying pattern.
- *Is there evidence the architecture itself, rather than the underlying model, caused the difference?* **No —
  and this is the most important caveat in this entire report.** `ARCH_COUNCIL`'s three real councillors this
  run were `qwen2.5-coder:7b` (the same model `BASE_N` used exclusively), `mlx:qwen3`, and `echo:latest`. If
  `mlx:qwen3` and/or `echo:latest` are individually weaker than `qwen2.5-coder:7b` on this specific class of
  coding tasks, a synthesis blending three opinions — one strong, two potentially weaker — could plausibly
  underperform four independent attempts from the strong model alone, for reasons having nothing to do with
  "orchestration" as an architectural principle and everything to do with which specific models happened to be
  selected into the council. **This design cannot separate that explanation from a genuine orchestration
  effect** — this is precisely the pre-existing, disclosed H4 boundary, and this run's result is a direct,
  concrete illustration of exactly why that boundary matters, not an exception to it.

**If the architecture had performed better, would this analysis have applied the same scrutiny?** Yes — and to
be explicit about the *symmetric* case that did not occur here: no comparison showed `ARCH_COUNCIL` or
`ARCH_PIPELINE_ISOLATED` outperforming its baseline by a threshold-crossing, one-directional margin. Had one
been observed, this section would have applied the identical adversarial checklist (noise, budget, task
composition, single-candidate dependence, model-vs-architecture confound) before endorsing it. No positive
result existed here to potentially over-credit.

## 10. No Post-Hoc Rescue

**Stated directly**: the data does not support either tested architectural intervention improving task
performance over its matched baseline on this held-out set. `ARCH_PIPELINE_ISOLATED` did not improve on
`BASE_1`. `ARCH_COUNCIL` did not improve on `BASE_N` — it underperformed it, by a margin that crosses the
pre-registered threshold, though not with statistical confidence at n=8.

**None of the following were done, and none will be**: the definition of "success" was not broadened beyond the
pre-existing `objective_verify()` sandbox pass; no candidate was excluded from any comparison; no threshold was
changed after seeing the data (the ≥25pp bar and the McNemar methodology were both already fixed by the design
protocol before this run); no failure was reinterpreted as a partial success; no new metric was introduced after
the fact to rescue a weak quantitative result; the test suite is not blamed for the result (§3's own spot-check
found the evaluator reliable, and the one real limitation found made `ARCH_COUNCIL` look worse, not better); no
new experiment is proposed in place of reporting this one's actual outcome.

**A null/negative/inconclusive result is treated here as fully legitimate** — per §7, three of four hypothesis
rows land at NOT SUPPORTED or INCONCLUSIVE, and the fourth (H4) is SUPPORTED specifically *because* the data
argues against architectural benefit, not because of any favorable reinterpretation.

## 11. Final Verdict

### EXECUTIVE RESULT

This held-out experiment did not provide evidence that the tested Echo architecture improves task performance
over compute/budget-matched non-architectural baselines. Neither the isolated self-edit generation framing nor
the full Council mechanism outperformed its matched control; the Council comparison in particular showed a
real, entirely one-directional, threshold-crossing disadvantage (`BASE_N` 6/8 vs `ARCH_COUNCIL` 3/8, all 3
discordant tasks favoring the simpler baseline) that is not statistically confirmable at this sample size
(n=8, exact McNemar p=0.25) but is also not explainable by the known compute asymmetry, since `ARCH_COUNCIL`
had strictly *more*, not less, real compute available to it. The honest reading is: a real, if underpowered,
signal pointing away from architectural benefit for this specific task class, apparatus, and model pool — not a
confirmed finding, and not a null finding either, but a directionally negative one large enough to take
seriously and too small to treat as settled.

### H1–H4 TABLE

See §7 in full.

### ARM RESULTS

- **`BASE_1`**: 5/8 (62.5%) [30.6%, 86.3%]. Failures: held_04 (universal), held_05, held_06.
- **`BASE_N`**: 6/8 (75.0%) [40.9%, 92.9%]. Best-performing arm in this run. Failures: held_04 (universal),
  held_05.
- **`ARCH_PIPELINE_ISOLATED`**: 4/8 (50.0%) [21.5%, 78.5%]. Failures: held_04 (universal), held_06, held_07,
  held_08. Two of its four failures (held_07, held_08) show a distinct pattern — see §9's qualitative note and
  the "commented-out function" observation below.
- **`ARCH_COUNCIL`**: 3/8 (37.5%) [13.7%, 69.4%] (after §3's correction; unchanged from the raw recorded tally
  since correction only changed failure-mode attribution, not pass/fail). Worst-performing arm in this run.
  Failures: held_03, held_04 (universal), held_05, held_06, held_08.

**One additional qualitative observation, reported because it is real and directly visible in the data, not
because it changes any score**: `ARCH_PIPELINE_ISOLATED`'s `held_07` failure is a candidate whose entire output
was a commented-out function definition (`# def get_permissions(role): ...`) — the same failure shape
independently observed during this apparatus's own isolation-verification testing on an unrelated trivial task.
This suggests a real, recurring tendency for this specific framing (large, irrelevant `self_edit_generated.py`
context + strict output rules) to sometimes produce comment-only, non-executing output — worth further
attention on its own terms, separate from the quantitative comparison.

### PAIRED ANALYSIS

See §4's full candidate-level table and per-comparison discordant-pair breakdown.

### CALL-BUDGET / COMPUTE LIMITATION

See §5. `ARCH_COUNCIL` made 5 real calls per candidate (confirmed in all 8 real executions), not 4 — a real,
disclosed, uncorrected asymmetry against `BASE_N`'s matched 4-call budget. This asymmetry, if anything, argues
against attributing `ARCH_COUNCIL`'s underperformance to insufficient compute.

### FAILURE-MODE ANALYSIS

| Arm | Correct | Task-logic failure | Truncation | Infrastructure failure |
|---|---:|---:|---:|---:|
| `BASE_1` | 5 | 3 | 0 | 0 |
| `BASE_N` | 6 | 2 | 0 | 0 |
| `ARCH_PIPELINE_ISOLATED` | 4 | 4 | 0 | 0 |
| `ARCH_COUNCIL` | 3 | 5 (corrected from 3) | 0 (corrected from 2) | 0 |

### ADVERSARIAL INTERPRETATION

**Strongest argument against the apparent conclusion** ("Council underperforms"): the specific councillor
models selected this run (`mlx:qwen3`, `echo:latest`, alongside the shared `qwen2.5-coder:7b`) may simply be
individually weaker than the pinned coding-specialist model on this exact task class — meaning the observed gap
could reflect *which models happened to be in the pool*, not anything about council orchestration as a
principle. A different council composition, or a task class better suited to genuine multi-perspective
synthesis (e.g., decomposition-heavy problems this design never tested), could plausibly show a different
result. **This argument does not change the final verdict** — it is already fully incorporated into the H1/H4
verdicts in §7, which explicitly state the model-vs-architecture confound as an unresolved limitation rather
than treating the observed gap as proof of an architectural defect. The verdict remains: not supported, not
falsified, and — given the magnitude and one-directional consistency — not simply "no evidence either way."

### WHAT THIS EXPERIMENT ESTABLISHES

- On this specific frozen 8-task held-out set, with this specific pinned model and this specific live council
  composition, neither tested architectural intervention demonstrated a performance advantage over its matched
  baseline.
- `ARCH_COUNCIL` underperformed the compute-matched `BASE_N` baseline by a real, entirely one-directional,
  threshold-crossing margin, despite having strictly more real compute available to it.
- The isolated self-edit generation framing showed no advantage over bare prompting at equal single-call budget;
  the small observed gap is statistically indistinguishable from noise.
- The primary correctness evaluator (real sandboxed test execution) is highly reliable — independently
  reproduced with zero discrepancies across all 32 candidates.
- A real, narrow, now-corrected limitation exists in the secondary truncation-classification heuristic,
  isolated to `ARCH_COUNCIL`'s own synthesis output habits (2/8 real syntheses), which did not affect any
  pass/fail outcome.

### WHAT THIS EXPERIMENT DOES NOT ESTABLISH

- It does **not** establish that Echo's architecture is worse in any general, lasting, or statistically
  confirmed sense — n=8 per arm is too small for confidence in any direction (all p≥0.25).
- It does **not** establish that architecture never helps on any coding task or task class — this is one small,
  frozen, self-authored task suite biased toward single-function algorithmic problems; results may not
  generalize to decomposition-heavy or multi-file tasks this design never tested.
- It does **not** distinguish, for the `ARCH_COUNCIL` comparison, whether underperformance stems from
  orchestration itself, the specific individual councillor models' relative weakness on this task class, or
  noise — the pre-existing H4 boundary remains fully in force.
- It does **not** establish anything about Echo's literal current production self-edit call path — per the
  isolation mission's own finding, that path is itself a full council deliberation, not the isolated single-call
  mechanism tested here.
- It does **not** establish anything about learning, generalized capability, or improvement over time — this is
  a single, static, one-shot snapshot.
- It does **not**, by itself, justify any architectural redesign decision.

### RECOMMENDATION

**Gather more evidence before acting, rather than either abandoning or doubling down on the architecture based
on this result.** The finding is real enough (one-directional, threshold-crossing) to take seriously, and small
enough (n=8, p=0.25) that treating it as confirmed would be exactly the kind of overclaim this whole
investigation has repeatedly warned against. Two concrete, honest options, not a forced choice: (1) run the
pre-planned confirmatory sample size the design protocol's own power analysis already specified, on a freshly
authored held-out set, before drawing any architectural conclusion; or (2) treat this pilot's own clear,
if underpowered, directional signal — zero of three discordant pairs favoring Council — as sufficient reason to
deprioritize further investment in the Council mechanism specifically for single-function coding tasks, while
explicitly leaving open whether a different task class (decomposition-heavy work) or a different council
composition would change the picture. **No architectural change is recommended on the strength of this result
alone.**

## 12. Evidence Preservation

- Raw execution artifacts (`heldout_results.jsonl`, `held_out_task_suite.json`) — untouched, unmodified,
  re-verified byte-for-byte reproducible against this analysis's own independent re-scoring.
- This document and its JSON companion (`audits/tier3_heldout_scoring_analysis.json`) are new artifacts,
  clearly labeled as the scoring/unblinding analysis layer — they do not replace or alter
  `audits/tier3_heldout_execution_report.{md,json}`.
- Scoring methodology: the pre-existing `objective_verify()`/`classify_result()` functions, unmodified, called
  read-only against already-stored data.
- Statistical methodology: exact (permutation-based) two-sided McNemar test on discordant pairs; Wilson score
  interval for individual arm pass rates (both standard, conservative choices for small paired binary samples,
  not selected post hoc for favorability).
- Corrected classifications: 2, both `ARCH_COUNCIL`, both `GENERATION_TRUNCATED → TASK_LOGIC_FAILURE`, both
  documented in full in §3 with the underlying evidence shown, not merely asserted.
