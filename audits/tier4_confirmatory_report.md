# Tier-4 Confirmatory Experiment: Final Forensic Report

**Analysis timestamp**: 2026-09-04. **Protocol**: `audits/tier4_confirmatory_protocol.md`
(sha256 `82a4a68f...e0e3c77`, frozen before either task suite existed). **Source artifacts**:
`audits/tier4_apparatus/{stage1,stage2}_results.jsonl` (336 raw candidate records, untouched by this
report), `audits/tier4_apparatus/tier4_stage{1,2}_task_suite.json` (84 tasks, hash-verified before every
execution). **Nothing in this report modifies any raw artifact, the frozen protocol, the Tier-3 pilot's
own results, or the Tier-3 scoring analysis.**

## EXECUTIVE RESULT

A confirmatory experiment roughly 10x the size of the original pilot (84 fresh, verified, never-before-used
tasks across two independently-authored, disjoint stages, vs. the pilot's 8) found that **the pilot's
apparent 37.5-percentage-point Council disadvantage was substantially inflated by small-sample noise** —
the confirmatory pooled gap is 11.9pp (`BASE_N` 79.8% vs `ARCH_COUNCIL` 67.9%), not statistically
significant even at n=84 (exact McNemar p=0.087, below the pre-registered pooled significance bar of
p≤0.048). The *direction* replicated cleanly across three independent samples (the original pilot, and
both new stages each independently), but the *magnitude* did not — a textbook regression-to-the-mean
signature of an original small-n estimate. **The real, decisive, mechanistically-explained finding of this
confirmatory experiment is different from what it set out to test**: a direct forensic replay of every
individual pre-synthesis attempt/councillor response against the real sandboxed ground truth shows the
underlying model pool is capable of solving these tasks at a 95-96% rate when any one of its independent
attempts is allowed to count — dramatically higher than any arm's *actual, synthesized* pass rate. The
gap between what the model pool can produce and what its own synthesis step delivers is 15.5 percentage
points for `BASE_N` (same-model synthesis) and 28.6 percentage points for `ARCH_COUNCIL` (heterogeneous-
model synthesis) — nearly twice as severe. **Synthesis, not generation, is the bottleneck, and it is a
substantially worse bottleneck for Council's heterogeneous synthesis than for BASE_N's same-model
synthesis.** A separate, unplanned but statistically decisive finding (p=0.0002, pooled) also confirms
that Echo's self-edit generation framing (`ARCH_PIPELINE_ISOLATED`) actively hurts performance relative to
bare prompting on general coding tasks, replicating and substantially strengthening a small, non-significant
pilot-stage signal.

## WHAT WAS PREREGISTERED

- Primary endpoint: `BASE_N` vs `ARCH_COUNCIL` paired PASS/FAIL, exact McNemar test, on a two-stage
  sequential design (42+42 tasks, later revised to 42+42=84 before execution — see the protocol's own §5
  disclosure), with an approximate two-look O'Brien-Fleming-style stopping rule (Stage 1 early-stop bar
  p≤0.0052 + ≥25pp + unidirectional discordants; pooled bar p≤0.048).
- Secondary endpoints: `BASE_1` vs `BASE_N`; `BASE_1` vs `ARCH_PIPELINE_ISOLATED`; `BASE_1` vs
  `ARCH_COUNCIL`; failure-mode distribution; council-composition variability; per-stage replication check.
- Model held fixed (`qwen2.5-coder:7b`, reused verbatim from the Tier-3 pilot's own pin) for
  `BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED`. Compute-budget Option A (preserve `ARCH_COUNCIL`'s real
  5-call warm-up asymmetry, not normalized).
- A pre-execution methodological fix (Finding A, §3 of the protocol): `BASE_N`'s synthesis prompt wording
  was corrected from "coherence and correctness" to "coherence and relevance," matching `ARCH_COUNCIL`'s
  real production template exactly — removing a bias that had favored `BASE_N` in the pilot, before any
  confirmatory data existed.

## WHAT WAS OBSERVED

### Raw integrity (both stages, checked before interpretation, per protocol §16/Step 1 discipline)

| Check | Stage 1 | Stage 2 |
|---|---|---|
| Expected records | 168 (42×4) ✅ | 168 (42×4) ✅ |
| Duplicate/missing (task,arm) pairs | 0 ✅ | 0 ✅ |
| Model pinning (non-Council) | 100% `qwen2.5-coder:7b` ✅ | 100% ✅ |
| `ARCH_COUNCIL` real calls incl. warm-up | 5/5 every time ✅ | 5/5 every time ✅ |
| Infrastructure failures | 0 (0%) ✅ | 0 (0%) ✅ |
| Truncations | 0 ✅ | 0 ✅ |
| Errors | 0 ✅ | 0 ✅ |
| Council composition | `{echo:latest, mlx:qwen3, qwen2.5-coder:7b}`, 42/42 identical | same, 42/42 identical |
| Stage 1 / Stage 2 task disjointness | — | 0 overlap ✅ |

No discrepancy required stopping interpretation at any point. Council composition stayed completely
constant across all 84 real executions — consistent with, and now directly confirming across a much
larger sample, Finding B's prediction that the `fair_sample_refresh`/`exploration_bias` swap mechanisms
would be structural no-ops given the current, frozen production state.

### Arm pass rates

| Arm | Stage 1 (n=42) | Stage 2 (n=42) | **Pooled (n=84)** |
|---|---:|---:|---:|
| `BASE_1` | 88.1% (37/42) | 88.1% (37/42) | **88.1% (74/84)**, CI [79.5%, 93.4%] |
| `BASE_N` | 76.2% (32/42) | 83.3% (35/42) | **79.8% (67/84)**, CI [70.0%, 87.0%] |
| `ARCH_PIPELINE_ISOLATED` | 64.3% (27/42) | 64.3% (27/42) | **64.3% (54/84)**, CI [53.6%, 73.7%] |
| `ARCH_COUNCIL` | 71.4% (30/42) | 64.3% (27/42) | **67.9% (57/84)**, CI [57.3%, 76.9%] |

## PAIRED ANALYSIS

### Primary: `BASE_N` vs `ARCH_COUNCIL`

| | Stage 1 | Stage 2 | **Pooled** |
|---|---:|---:|---:|
| Absolute diff | −4.76pp | −19.05pp | **−11.9pp** |
| Discordant (favor `BASE_N`, favor `ARCH_COUNCIL`) | 8, 6 | 11, 3 | **19, 9** |
| Both pass / both fail | 24 / 4 | 24 / 4 | 48 / 8 |
| Exact McNemar two-sided p | 0.7905 | 0.0574 | **0.0872** |

**Compare to the original pilot** (n=8): −37.5pp, discordant 3-0, p=0.25. Every one of the three
independent samples (pilot, Stage 1, Stage 2) points the same direction (`BASE_N` ahead), but the
magnitude swings by nearly an order of magnitude (4.76pp to 37.5pp) across samples of comparable or
smaller size than the confirmatory stages — direct, empirical evidence that the pilot's own point
estimate carried far more sampling noise than its clean-looking 3-0 sweep suggested.

### Secondary comparisons (pooled, n=84)

| Comparison | Rate A | Rate B | Diff | Discordant (A,B) | Exact McNemar p |
|---|---:|---:|---:|---|---:|
| `BASE_1` vs `BASE_N` | 88.1% | 79.8% | −8.33pp | 12, 5 | 0.1435 |
| `BASE_1` vs `ARCH_PIPELINE_ISOLATED` | 88.1% | 64.3% | **−23.81pp** | 24, 4 | **0.0002** |
| `BASE_1` vs `ARCH_COUNCIL` | 88.1% | 67.9% | **−20.24pp** | 23, 6 | **0.0023** |

Two of these three secondary comparisons are now statistically decisive at n=84, where the pilot (n=8)
found nothing significant in either (`BASE_1` vs `ARCH_PIPELINE_ISOLATED`: pilot p=1.0, confirmatory
p=0.0002; `BASE_1` vs `ARCH_COUNCIL`: pilot p=0.5, confirmatory p=0.0023). **`BASE_1` — the simplest
possible strategy, one deterministic call, zero architecture of any kind — is the best-performing arm in
this entire confirmatory study**, significantly ahead of both of Echo's real architectural mechanisms
(the isolated self-edit framing and the full council), and nominally (though not significantly) ahead of
its own same-model multi-attempt cousin `BASE_N` too.

## FAILURE-MODE ANALYSIS

| Arm | PASS | TASK_LOGIC_FAILURE | GENERATION_TRUNCATED | INFRASTRUCTURE_FAILURE |
|---|---:|---:|---:|---:|
| `BASE_1` | 74 | 10 | 0 | 0 |
| `BASE_N` | 67 | 17 | 0 | 0 |
| `ARCH_PIPELINE_ISOLATED` | 54 | 30 | 0 | 0 |
| `ARCH_COUNCIL` | 57 | 27 | 0 | 0 |

Zero truncations and zero infrastructure failures across all 336 real candidates — the evaluator and
apparatus held up completely cleanly at 10x the pilot's scale, addressing H3 (measurement limitation)
decisively: whatever explains the arm-level differences, it is not evaluator noise.

## THE MECHANISM: SYNTHESIS DESTROYS CORRECT CANDIDATES, AT A RATE THAT SCALES WITH MODEL DIVERSITY

This is the confirmatory experiment's central, unplanned-but-mission-mandated finding (mission section
"Investigate why Council may lose," specifically: *"Did BASE_N generate a correct answer among its
attempts that its synthesis preserved, while Council generated or encountered a correct solution but its
deliberation/synthesis destroyed it?"*). Every `mechanism_calls` entry (a genuinely new instrumentation
this confirmatory harness adds, capturing full response text for every real underlying call, not just
model identity) was independently re-verified against the real sandboxed ground truth — a "does any
individual pre-synthesis attempt/councillor pass on its own" oracle, computed with zero additional model
calls, purely by re-scoring already-generated text.

| Arm (pooled, n=84) | Real synthesis pass rate | Oracle rate (≥1 component independently passes) | Gap lost to synthesis |
|---|---:|---:|---:|
| `BASE_N` (3 same-model attempts) | 79.8% | **95.2%** | **15.5pp** |
| `ARCH_COUNCIL` (3 heterogeneous councillors) | 67.9% | **96.4%** | **28.6pp** |

The underlying generative capability, when any one of several independent attempts is allowed to count,
is nearly identical between the two arms (95.2% vs 96.4%) — **the raw model pool is not the bottleneck.**
What differs enormously is how much of that capability survives the combination step: `ARCH_COUNCIL`
loses nearly twice as much (28.6pp vs 15.5pp) to its own synthesis as `BASE_N` does. Of the 44 real
failures examined across both arms, **38 (86%) had at least one individual component that would have
passed independently** — `ARCH_COUNCIL`: 25 of 27 failures (92.6%); `BASE_N`: 13 of 17 failures (76.5%).
In 7 of those cases (3 `BASE_N`, 4 `ARCH_COUNCIL`), *every single individual component was independently
correct*, and the synthesis step still produced wrong final code. Synthesis was observed to genuinely
*rescue* a fully-wrong set of attempts into a correct final answer exactly once, in `ARCH_COUNCIL`, out of
84 real candidates — a negligible rate next to the 28.6pp it loses in the other direction.

**Two concrete, illustrative examples, both real, unedited, drawn directly from the raw data:**

1. **`BASE_N`, task `cs09` (Stage 1)** — all three same-model attempts at temperatures 0.55/0.7/0.85
   independently produced a complete, correct `ThreadSafeMultiCounter` class with proper locking. The
   synthesis output kept *only* the `if __name__ == "__main__":` demo block from the attempts and
   **dropped the class definition entirely**, failing immediately with `NameError: name
   'ThreadSafeMultiCounter' is not defined`. The correct implementation existed, verified, in all three
   inputs to synthesis; synthesis discarded the part that mattered.

2. **`ARCH_COUNCIL`, task `bf06` (Stage 2)** — all three councillors (`qwen2.5-coder:7b`, `mlx:qwen3`,
   `echo:latest`) produced **byte-for-byte identical** correct code:
   ```python
   def find_missing(nums):
       n = len(nums)
       expected_sum = n * (n + 1) // 2
       return expected_sum - sum(nums)
   ```
   There was no disagreement to synthesize — unanimous, identical input. The synthesis output (from
   `echo:latest`, in its separate synthesis role) was:
   ```python
   def find_missing(nums):
       n = len(nums) - 1
       expected_sum = n * (n + 1) // 2
       return expected_sum - sum(nums)
   ```
   A fabricated `- 1` that appears in none of the three unanimous inputs, breaking correct logic that
   required no reconciliation at all. This is about as close to unambiguous evidence of a
   synthesis-introduced defect as a real, non-synthetic experiment can produce.

**This reframes H1/H2 more precisely than either hypothesis originally anticipated.** H2 ("the
architecture cannot reliably overcome the model's limitations") is true in outcome but wrong in
mechanism as usually understood — the *model's* limitations are not the binding constraint here (95-96%
oracle capability); the *synthesis step's own* reliability is. This is a specific, falsifiable,
mechanistic claim distinct from a generic "model ceiling," and it is the single most actionable finding
in this report.

## COMPUTE-BUDGET / COMPUTE LIMITATION

`ARCH_COUNCIL` made 5 real Ollama calls per candidate in all 84 confirmatory executions (confirmed via
`total_real_ollama_calls_including_warmup`, zero exceptions), one more than `BASE_N`'s 4 — the same
disclosed, un-normalized asymmetry as the Tier-3 pilot, preserved deliberately per protocol §9 (Option A).
**This asymmetry cannot explain `ARCH_COUNCIL`'s underperformance** — if anything it argues the opposite,
since `ARCH_COUNCIL` had strictly more real compute available and still lost more of its own oracle
capability to synthesis (28.6pp) than `BASE_N` did with less compute (15.5pp) than `ARCH_COUNCIL`. A
dedicated compute-normalized side probe (mission §"Compute Budget," Option B) was considered and
deliberately not run as a separate real-model-call experiment in this pass: the oracle-vs-real-synthesis
gap already found is 15.5-28.6pp, an order of magnitude larger than any plausible effect from one
additional content-discarded warm-up call, and confirmed via a mechanism (comparing pre-synthesis
components already generated, not requiring new calls) independent of the call-count question entirely.
Spending further real compute on the smaller confound was judged not to be where the explanatory power
actually lies — stated here as a reasoned scope decision, not a silent omission.

## H1–H4 VERDICT TABLE

| Hypothesis | Comparison | n | Effect | Threshold | Statistical result | Verdict |
|---|---|---:|---:|---:|---|---|
| **H1** — architecture beats matched-budget baseline | `BASE_N` vs `ARCH_COUNCIL` | 84 (pooled) | −11.9pp (wrong direction for H1) | ≥25pp | p=0.0872 (pooled bar 0.048) | **NOT SUPPORTED** — direction consistent across 3 independent samples, magnitude and significance both below the pre-registered bar |
| **H2** — model ceiling explains underperformance | oracle-vs-synthesis gap analysis | 84×2 arms | Oracle 95-96% vs real synthesis 68-80% | n/a | Mechanistic, not p-value based | **REFRAMED, not simply supported**: the *model's* ceiling is not the binding constraint (95-96% oracle); the *synthesis step's* reliability is — a more specific, falsifiable claim than H2's original framing |
| **H3** — measurement limitation | 0 infra failures, 0 truncations across 336 candidates; evaluator independently re-verified via the oracle re-scoring pass itself | 336 | n/a | n/a | Clean at 10x pilot scale | **NOT SUPPORTED** — evaluator fully reliable |
| **H4** — apparent Council advantage is compute/diversity, not orchestration | `BASE_N` wins pooled | 84 | `BASE_N` +11.9pp | pre-registered rule: `BASE_N` win supports H4 | p=0.0872 | **SUPPORTED per the letter of the pre-registered rule**, refined by the mechanism finding: the specific reason orchestration didn't help is that heterogeneous-model synthesis is measurably *harder* (loses 28.6pp vs 15.5pp) than same-model synthesis, not a generic diversity/compute story |
| *(unplanned, Level-A secondary)* — self-edit framing vs bare prompting | `BASE_1` vs `ARCH_PIPELINE_ISOLATED` | 84 (pooled) | −23.81pp | n/a (not pre-registered as primary) | **p=0.0002** | Decisively replicated: self-edit framing actively hurts general coding performance |

No hypothesis is marked FALSIFIED — none of the primary comparisons reach conventional significance in
either direction strongly enough to rule out chance definitively, consistent with a genuinely modest true
effect size rather than a large one.

## ADVERSARIAL INTERPRETATION

**Strongest argument against the synthesis-destruction finding being the real story**: could the oracle
comparison itself be an unfair standard — of course *some* individual attempt among 3 will pass more
often than one final combined answer, simply because 3 independent rolls have a higher `P(at least one
success)` than 1 roll, even with NO synthesis defect at all (pure order-statistics effect, not evidence
of active destruction)? This is a real, important caveat, addressed directly: if synthesis is simply
"average, unbiased selection with no active harm," the expected real-synthesis rate should sit
*between* the single-best-attempt rate and the oracle rate, not near the *bottom* of the individual
attempts' own rates. Checking this directly against the per-candidate data: in the 7 "all-components-
correct" cases, a synthesis step performing pure unbiased selection (e.g., picking uniformly among 3
identical-quality options) would have a 100% chance of landing on a correct answer if all three options
ARE correct — yet synthesis still failed in every one of those 7 cases. This specific subset is not
explainable by "3 rolls beat 1 roll" order statistics at all, since there was no roll to lose — it is
direct, mechanism-level evidence of active corruption, not merely a sampling artifact of the oracle
comparison. The broader 15.5pp/28.6pp gaps are consistent with *both* some genuine order-statistics
effect *and* real synthesis defects; the 7 all-agree-but-still-wrong cases isolate the latter cleanly.

**Could the primary null result (`BASE_N` vs `ARCH_COUNCIL` p=0.087) still be sampling noise, just now in
the other direction — i.e., is the *confirmatory* estimate itself unstable?** Plausibly, to a degree —
Stage 1 (4.76pp) and Stage 2 (19.05pp) differ by a factor of 4, which is itself substantial variance
between two same-sized, same-protocol batches. This is disclosed plainly rather than smoothed over: the
pooled 11.9pp estimate is a real synthesis of two real but disagreeing-in-magnitude samples, not a single
clean number either. This is exactly why the pooled result — not either stage alone — is the correct
number to report as the confirmatory verdict, and why it remains appropriately labeled non-significant.

**Could `BASE_1`'s across-the-board dominance be an artifact of temperature rather than architecture?**
Plausibly a real, contributing mechanism worth naming: `BASE_1` runs at temperature 0.0 (fully
deterministic, exploiting the model's single highest-confidence trajectory), while `BASE_N`'s and
`ARCH_COUNCIL`'s individual attempts/councillors sample at a jittered ~0.7±0.15 (chosen for diversity,
per production's own design). Higher-temperature sampling plausibly increases the individual-attempt
error rate; this is a real, disclosed alternative (or additional) explanation for why `BASE_1` outperforms
`BASE_N`, distinct from (and not exclusive with) the pure synthesis-destruction mechanism. **This does
not explain `ARCH_PIPELINE_ISOLATED`'s underperformance, however** — it runs at the identical
temperature 0.0 as `BASE_1`, with the same single-call budget; its −23.81pp deficit is attributable
specifically to the self-edit-context framing (the prepended `CODE_OUTPUT_RULES` and live
`self_edit_generated.py` file content), not temperature, isolating a second, independent, real cause
distinct from the temperature-driven explanation for the other two arms.

**Does this change the H1 verdict?** No. Every adversarial angle checked here either fails to explain the
finding away (the 7 unanimous-but-wrong cases) or identifies a real, additional, disclosed contributing
factor (temperature) that sits alongside, not instead of, the synthesis-destruction mechanism — none of
them rescues H1 or manufactures a positive Council result that the data does not support.

## WHAT THIS EXPERIMENT ESTABLISHES

- The Tier-3 pilot's 37.5pp `ARCH_COUNCIL` disadvantage was substantially inflated by small-sample
  variance; the confirmatory, pooled, 10x-larger estimate is 11.9pp and not statistically significant.
- The *direction* of the pilot's finding (`BASE_N` ahead of `ARCH_COUNCIL`) replicated across three
  independent samples (pilot, Stage 1, Stage 2) — a real, if modest and statistically inconclusive,
  signal, not simply noise in either direction.
- The underlying model pool's raw generative capability on this task suite is high (95-96%, oracle) —
  clearly not the binding constraint on any arm's real performance.
- Synthesis/combination is the primary, quantified bottleneck for both multi-attempt architectures,
  substantially worse for heterogeneous-model Council synthesis (28.6pp lost) than same-model `BASE_N`
  synthesis (15.5pp lost) — a specific, mechanistic, falsifiable, and now twice-illustrated-concretely
  finding.
- Echo's self-edit generation framing measurably and significantly hurts performance on general coding
  tasks relative to bare prompting at equal single-call budget (p=0.0002, pooled).
- The evaluator/apparatus held up cleanly at 10x pilot scale (0 infrastructure failures, 0 truncations,
  100% model pinning, fully disjoint stages).

## WHAT THIS EXPERIMENT DOES NOT ESTABLISH

- It does not establish that Council orchestration is *never* useful — this is one task suite (bounded,
  single-function-shaped coding problems), one pinned model, one fixed 3-councillor composition. A
  decomposition-heavy task class, or a differently-composed council, could plausibly show a different
  synthesis-reliability profile.
- It does not fully disentangle the model-diversity-vs-orchestration confound (the pre-existing H4
  boundary) — it *locates* the mechanism (synthesis reliability degrades with input heterogeneity) but
  does not prove this is intrinsic to model diversity as a principle vs. specific to this council's model
  mix or this synthesis prompt.
- It does not establish that the synthesis defect is unfixable — a better synthesis prompt, an explicit
  code-completeness check before returning a synthesized answer, or a structured (rather than free-text)
  combination step are all plausible, untested remedies this experiment did not attempt.
- It does not establish anything about Echo's literal production self-edit call path (which is itself a
  full council deliberation, not `ARCH_PIPELINE_ISOLATED`'s single-call mechanism) or about long-horizon,
  multi-turn, or non-coding task performance.
- The temperature-vs-synthesis-defect confound for `BASE_1` vs `BASE_N`/`ARCH_COUNCIL` is named but not
  isolated by a dedicated controlled sub-experiment (e.g., re-running `BASE_N` at temperature 0.0) — a
  concrete, cheap, well-scoped follow-up this report explicitly flags rather than treats as resolved.

## RECOMMENDATION

**REFACTOR, tied directly to the evidence threshold this report itself establishes — not KEEP, not
RETIRE, and not on intuition.** The underlying idea (multiple attempts, or multiple models, followed by
synthesis) is not shown to be worthless — the oracle analysis proves the *raw ingredients* for a much
better result (95-96% capability) already exist inside every real Council/BASE_N execution. What is
shown, concretely and repeatedly, is that the specific *combination* mechanism is where that capability
is being lost, and lost worse for the more architecturally elaborate arm (Council) than the simpler one
(`BASE_N`). This is the textbook shape of a REFACTOR verdict per this project's own decision rule: "the
underlying idea appears useful, but implementation/orchestration is causing measurable losses."

Concrete, evidence-grounded next steps, none of them a redesign-from-scratch and none requiring
abandoning the architecture: (1) a targeted synthesis-prompt or synthesis-procedure fix aimed specifically
at code-completeness (the `cs09` case shows a class definition silently dropped — a structural,
checkable defect a smarter synthesis or a post-synthesis completeness check could plausibly catch
cheaply); (2) re-test the *same* corrected synthesis mechanism against a fresh, disjoint, third task suite
before declaring the fix successful — this report's own central lesson is that a single sample, however
large, can still mislead, and a fix deserves the identical scrutiny the original design got; (3) resolve
the temperature confound directly (a cheap, targeted sub-experiment re-running `BASE_N` at temperature
0.0) before attributing more of `BASE_1`'s advantage to "no architecture" than is actually warranted; (4)
separately and independently, decide whether to retest `ARCH_PIPELINE_ISOLATED`'s self-edit-framing
penalty is fixable (e.g., trimming irrelevant `self_edit_generated.py` context for non-self-edit tasks) —
its own p=0.0002 result is strong enough to act on now, not wait for further confirmation.

No architectural change is recommended on the strength of disappointment with Council's raw pilot number
— that number itself did not survive confirmation. The change that *is* warranted follows from a
positive, specific, twice-replicated mechanistic finding: fix synthesis, don't retire orchestration.

## STATISTICAL METHODOLOGY

Exact two-sided McNemar test via direct binomial coefficient summation on discordant pairs (verified
against known values before use — `McNemar(3,0)=0.25`, `McNemar(2,0)=0.5`, matching the Tier-3 pilot's
own hand-computed figures exactly). Wilson score 95% CI for individual arm rates. No test was substituted
for a more favorable one; the same methodology as the Tier-3 scoring analysis was reused verbatim
(`scripts/tier4_analyze.py`, not a new implementation).

## EVIDENCE PRESERVATION

- Raw execution artifacts (`stage1_results.jsonl`, `stage2_results.jsonl`, both task suites) — untouched.
- The oracle/mechanism re-scoring pass is read-only: it re-runs the same, unmodified `objective_verify()`
  against already-generated `mechanism_calls` text, making zero new model calls and writing nothing back
  into the raw result files.
- This document and its JSON companion (`audits/tier4_confirmatory_report.json`) are new artifacts.
- The frozen protocol (`audits/tier4_confirmatory_protocol.md`) is unmodified since its final,
  pre-execution hash (`82a4a68f...`).
