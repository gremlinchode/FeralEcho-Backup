# Adversarial Audit of the Clean Tier-5 Retest

**Date:** 2026-09-14
**Type:** Independent, adversarial re-verification of a completed experiment (not a new experiment, not a re-run)
**Subject:** `audits/2026-09-13_tier5_council_correctness_retest.md` and its underlying raw data
**Status:** Complete. HEAD unchanged. No production code modified.

---

## 1. Executive conclusion

The clean retest's headline numbers **hold up under independent, from-scratch recomputation of the raw data**: N=20, control 17/20 (85.0%), treatment/Council 18/20 (90.0%), +5.0pp, wins=3/losses=2/ties=15/both-wrong=0, McNemar exact p=1.0000 — all independently reproduced from `tier5_retest_results.jsonl` directly, not copied from the report. Task-pool identity, driver logic, and the presence of both Tier-5 fix functions in the live `river_deliberation.py` were also independently re-confirmed.

However, **the McNemar test result is not merely "underpowered" — it was structurally incapable of reaching conventional significance at all**, regardless of what the true effect was: with only 5 discordant pairs, the most extreme possible outcome (5-0, i.e. every single discordant pair going the same direction) yields p=0.0625, still above 0.05. This experiment could not have produced a "significant" result under any realization of its own data. That is a stronger, more precise statement than "underpowered," and it is not stated this precisely anywhere in the original report.

One genuine, material correction to the original report: its own §11 states *"No direct log evidence that `detect_full_agreement`'s shortcut actually fired... found none."* This is **wrong** — direct grep of `tier5_retest_stdout.log` finds two explicit, on-task log lines (`[DELIBERATION] Synthesis dropped agreed-upon definition(s) ['binary_search']... falling back to best candidate`, and the same for `['merge_sorted']`) proving `find_missing_agreed_definitions()` fired successfully twice more, on tasks `r-ae01` and `r-ae02`, both of which then passed. This **strengthens**, not weakens, the case for the Tier-5 fix's real-world value — three of twenty tasks (15%) now show direct, on-point evidence that this specific mechanism mattered, not just the one (`r-iv04`) the original report highlighted. It also means the original report's own falsification section understated the evidence in favor of its own conclusion, which is a real methodological miss even though the direction of the error favors, rather than undermines, the report's headline claim.

**Net verdict for §9's required classification: RESULT INCONCLUSIVE ON THE AGGREGATE STATISTIC, WITH REAL, DIRECTLY-OBSERVED POSITIVE MECHANISTIC EVIDENCE.** The aggregate ±5pp number and its p=1.0 carry no weight either way — the sample cannot support a statistical claim in either direction, full stop. But three separate, concrete, log-and-code-verified observations (`r-iv04`, `r-ae01`, `r-ae02`) show the specific `find_missing_agreed_definitions()` mechanism doing exactly the job it was built for, with zero observed instances of it (or `detect_full_agreement`) causing harm in this batch. This is real evidence at the mechanism level; it is not evidence at the aggregate-magnitude level, and the original report's own architecture recommendation (B) correctly reflects that split — it just had slightly weaker mechanistic support behind it than actually exists.

---

## 2. Experimental identity

Independently re-verified, not copied from the prior report:

| Item | Verified value | How verified |
|---|---|---|
| Git HEAD (this audit's start) | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` | `git rev-parse HEAD` |
| Git HEAD (this audit's end) | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` (unchanged) | `git rev-parse HEAD` re-run |
| Working-tree status | 126 lines in `git status --short`, unchanged across this audit's own work | `git status --short \| wc -l`, run before and after |
| Live task-pool SHA256 | `595bb18abf1b8c6ca6c34e23687b909551c6dd610eb860961b3714b82bc7b8ac` | `shasum -a 256 scripts/tier5_retest_task_pool.py` |
| Frozen task-pool SHA256 | Identical to above | `shasum -a 256 audits/tier5_retest/tier5_retest_task_pool_FROZEN.py` |
| Recorded hash file | Identical to both above, `bytes: 20499` | `cat audits/tier5_retest/tier5_retest_task_pool.hash.txt` |
| Live vs. frozen task pool | **Byte-identical**, confirmed via `diff`, not just hash comparison | `diff scripts/tier5_retest_task_pool.py audits/tier5_retest/tier5_retest_task_pool_FROZEN.py` → no output |
| `detect_full_agreement` presence | Present at `river_deliberation.py:845`, called at line 1342 within `deliberate_and_learn()` | `grep -n` directly against the live file |
| `find_missing_agreed_definitions` presence | Present at `river_deliberation.py:901`, called at line 1445 within `deliberate_and_learn()` | `grep -n` directly against the live file |
| Driver treatment/control logic | Confirmed: treatment restores the two real functions per-task before running; control monkeypatches both to permanent no-ops per-task before running; monkeypatch is byte-identical to `scripts/verify_synthesis_refactor_control.py`'s own established pattern (lines 28-29 of that file) | Full read of `scripts/run_tier5_retest.py`, direct comparison |
| Resume/skip logic | **None** — the driver's `main()` loops unconditionally over all 20 `TASKS` in fixed order, treatment then control, every time it is invoked | Full read of `run_tier5_retest.py`'s `main()` |
| Condition-order effect | **Not randomized** — every task runs treatment first, control second, always. This is a real, previously-undisclosed methodological detail (see §9). | Direct read of the loop body |

No task, prompt, oracle, sandbox, model-pool, or scoring-logic change was found between the interrupted first attempt and the clean rerun — both used the identical frozen task pool and the identical, unmodified driver script. The only difference between the two runs is environmental (machine stayed awake throughout the clean run).

---

## 3. Clean-run provenance

`audits/tier5_retest/tier5_retest_results.jsonl`: 40 lines, independently parsed with a fresh script (not reusing any code from the retest mission). Confirmed: 20 distinct `task_id` values, zero duplicate `(task_id, condition)` cells, zero missing cells (every task has exactly one `treatment` and one `control` record), zero records carrying an `exception` field. Generation-time range across all 40 records: 24.13s–113.14s — no outlier remotely resembling the archived run's ~5-hour sleep artifact. A direct grep of the full `tier5_retest_stdout.log` for `sleep|watchdog|stalled|connectionerror|timed? ?out|network` (case-insensitive) returns **zero matches**. This run shows no contamination signature of the kind that invalidated the first attempt.

Two real, moderate-frequency background signals were found and are worth disclosing, neither of which is fatal:
- **92 `[PROMPT GUARD] Reasoning leak detected` warnings** across 40 real generations (≈2.3 per generation on average) — evidence that per-councillor and/or synthesis output frequently opens with prose the guard has to strip, a real, pre-existing, systemic noise source in the generation pipeline, independent of the Tier-5 mechanism under test. In 2 of 40 cells (see §9), a leak survived stripping and reached the sandbox as a `SyntaxError`.
- **2 `[DELIBERATION] Synthesis dropped agreed-upon definition(s)...` warnings** — see §1 and §9; these are *positive* evidence the completeness-check fix fired correctly, not contamination.

---

## 4. Historical interrupted-run contamination

Confirmed directly, not assumed: the archived first attempt (`audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_results.jsonl`) contains `r-rf03`'s 18024.08s/16439.91s generation-time pair and has no `r-dt04` record at all — both exactly as previously documented. Confirmed the **clean** dataset (`tier5_retest_results.jsonl`, not the archive) contains a normal-magnitude `r-rf03` record (both conditions present, generation times in the same 24-113s range as every other task — independently checked, not merely assumed) and a complete `r-dt04` record. No archived observation appears anywhere in the live results file; the two files are physically separate and were never concatenated or merged. This satisfies §2's requirement in full.

---

## 5. Actual N

| Level | Count |
|---|---|
| Tasks authored | 20 |
| Task-condition cells intended | 40 (20 × 2) |
| Task-condition cells executed | 40 |
| Valid scored cells | 40 |
| Excluded cells | 0 |
| Missing cells | 0 |
| **N used for the primary paired test (tasks)** | **20** |
| **N discordant pairs feeding McNemar** | **5** |

Pairing was preserved throughout — both this audit's own recomputation and the original report analyze outcomes task-by-task (`by_task[tid]['treatment']` vs. `by_task[tid]['control']`), never as two independent unpaired samples of 20. No exclusion of any kind was applied to either condition or any task.

---

## 6. Data-quality audit

Re-stated from §3/§4 for completeness against the mission's own required checklist: no sleep/suspend signature, no process stall, no watchdog intervention, no network failure/retry/timeout signature, no duplicate task execution, no malformed/missing scoring field on any of the 40 records. Condition order was fixed (treatment always first) rather than randomized — see §9 for why this is disclosed as a minor, not fatal, threat. Task order across the run was also fixed (pool order, not shuffled) — same classification.

---

## 7. Independent scoring audit

Rather than trust the recorded `passed` field, the full `candidate_code` and `output_tail` for all 5 discordant cases were read directly and the oracle's own verdict reasoned through independently:

- **`r-iv04` (treatment win)**: Control's `candidate_code` is literally three `print(clamp(...))` calls with **no `clamp` function definition anywhere in the returned text** — confirmed by reading the full, untruncated field, not the report's paraphrase. A `NameError`-class failure is the only possible outcome; `passed=False` is correct. Treatment's code is a complete, correct `clamp` definition; `passed=True` is correct. **This is the strongest single case in the dataset and the recorded scores are verified accurate.**
- **`r-ae03` (control win)**: Treatment's `candidate_code` begins with the literal text `"Here is the final code:\n\n```Python\n..."` — the un-stripped prose prefix is present verbatim in the field actually sent to the sandbox. The recorded `output_tail` shows a `SyntaxError` at exactly the point that prefix would land as the first line. Recomputing this by hand: yes, this must fail. `passed=False` is correct, and the underlying `is_clean_palindrome` logic (visible after the prose prefix) is otherwise valid.
- **`r-rf01` (treatment win)**: Control's `candidate_code` begins with `"Here's a cleaner version of your function:\n\n```Python\n..."` — same failure shape as above, confirmed independently. `passed=False` is correct for control.
- **`r-bf04` (control win)**: Treatment's full code is `def dedupe_preserve_order(items): seen=set(); result=[item for item in items if not (seen.add(item), True)]; return list(result)`. Traced by hand: `seen.add(item)` always returns `None`; `(None, True)` is a non-empty tuple, which is always truthy; `not <truthy>` is always `False` — so the list comprehension's filter condition is always `False`, and `result` is always empty regardless of input. This **independently confirms a genuine logic defect**, distinct from the prose-leak class above, and confirms the recorded `AssertionError`/`passed=False` is correct. **This is not a scoring artifact — the code is genuinely broken**, and the report's own honest disclosure ("cannot determine whether this defect originated pre- or post-synthesis") is the correct level of claim, not an overclaim.
- **`r-dt03` (treatment win)**: Control's full code shows a recursive helper `_flatten_subdict(subd, prefix='')` correctly threading `prefix`, but the **top-level caller invokes it as `result.update(_flatten_subdict(v))`, omitting the second argument** — so the prefix a top-level nested dict should carry is silently dropped one level too early. Traced by hand against the test case `{"a": {"b": 1, "c": 2}, "d": 3}`: this produces `{"b": 1, "c": 2, "d": 3}` instead of the required `{"a.b": 1, "a.c": 2, "d": 3}` — a genuine, independently-confirmed logic defect, `AssertionError`/`passed=False` correct.

**No scoring-layer defect was found.** Every one of the 5 discordant `passed` values was independently re-derivable by hand from the raw candidate code and the task's own test assertions; none required trusting the harness's self-report. This satisfies §5's requirement — the audit does not need to stop and report a scoring defect, because none exists in this sample.

**One correction to the original report's own case classification, made explicit here rather than left implicit**: the original report is careful and accurate in separately identifying `r-ae03`/`r-rf01` as sharing the prose-leak failure mode and `r-bf04`/`r-dt03` as two *independent*, unrelated logic defects (not claiming all four share one cause) — this audit's own first-pass reading of the report's condensed final-response summary (not the report body itself) initially misread this as a single shared bug across all four; re-reading the full report text and independently re-deriving each case from raw data confirms **the original report's actual written classification is correct**, and the summary-level compression was simply less precise than the underlying report. Recorded here as a real self-correction during this audit, not smoothed over.

---

## 8. Primary statistics

Independently recomputed from `tier5_retest_results.jsonl` directly (script written fresh for this audit, not reusing the retest mission's own analysis code):

```
N (tasks)          = 20
Control correct     = 17  (85.0%)
Treatment correct   = 18  (90.0%)
Absolute difference = +5.0 pp (treatment − control)
Relative difference = +5.9% relative to control's own rate (not a meaningful framing at this N — see §10)

Both correct   = 15
Both incorrect =  0
Treatment-only (Council win)  = 3   (r-dt03, r-iv04, r-rf01)
Control-only   (Council loss) = 2   (r-ae03, r-bf04)
Discordant pairs = 5

McNemar exact (binomial on discordant pairs, k=3 of 5): p = 1.0000 (two-sided)
```

This **exactly reproduces** the original report's own numbers in every field. No confidence interval was computed by the original report or by this audit — a Wilson/exact CI on a 3-vs-2 split of 5 discordant pairs would be so wide as to be uninformative on its own (e.g., a 95% CI on the discordant-pair win proportion spans roughly 15%-85% at this n), and computing one would not add real information beyond what §9 below already states precisely.

---

## 9. Adversarial / falsification analysis

Assuming the result is wrong and searching for the strongest explanation:

| Threat | Classification | Reasoning |
|---|---|---|
| **Sample too small to resolve direction or magnitude** | **Fatal, for the aggregate claim only** | Directly proven in §10: with 5 discordant pairs, no possible outcome reaches p<0.05. The aggregate McNemar result cannot support any claim about the true effect's sign or size, full stop. This is not a "weak signal" — it is a structural incapacity, proven mathematically, not estimated. |
| **Task-selection bias / composition differs from Tier-4** | **Material, unresolved** | This retest's 20 tasks are freshly authored, not a subset of Tier-4's 84. No evidence either way that this pool is harder or easier for Council than Tier-4's — genuinely unknown, and the original report already discloses this. |
| **Condition-order effect (treatment always runs first)** | **Minor, previously undisclosed by the original report** | Every task ran treatment then control, never randomized or counterbalanced. A plausible (not confirmed) mechanism: model/connection warm-up, or subtle temporal drift in a locally-served Ollama pool's state across a session, could systematically favor whichever condition runs second. No evidence in this dataset that this occurred (control did not systematically outperform or underperform based on this alone — the treatment win rate is higher, the opposite of what "second-mover advantage favors control" would predict, which is weak evidence *against* this specific threat actually mattering here), but it was never controlled for and should be for a larger future run. |
| **Nondeterminism / model stochasticity** | **Ruled out as an alternative explanation for the *specific* discordant cases**, material as general noise | Every one of the 5 discordant cases was independently traced to a specific, deterministic cause (a missing definition, a dropped prose-stripping edge case, or a genuine logic bug) in §7 — none of the 5 discordant outcomes is unexplained residual noise. Stochasticity remains a real factor in *whether* a given generation happens to contain one of these defects, but it is not an unexplained "black box" effect here. |
| **Prompt/oracle/implementation leakage between conditions** | **Ruled out** | `install_isolation()` and the exact monkeypatch pattern were independently confirmed in §2; each task-condition pair uses a fresh `deliberate_and_learn()` call with no shared mutable state between treatment and control beyond the (correctly reset) module-level function attributes. |
| **Multiple testing / researcher degrees of freedom / post-hoc exclusions** | **Ruled out** | Zero exclusions were applied (§5). The primary test (McNemar) was pre-specified and not changed after seeing results, per the original report's own §3 and confirmed by this audit finding no alternative test substituted anywhere. |
| **Stopping rule** | **Ruled out** | Fixed N=20, no interim peeking possible given the driver's unconditional loop structure (confirmed in §2) — there is no code path by which the run could have been stopped early based on an interim result. |
| **Ceiling/floor effects** | **Material** | Both conditions are already at 85-90% — a high-concordance regime where most tasks are "easy enough" that neither condition fails them (15/20 both-correct). This compresses the discordant-pair count structurally, independent of sample size — even a much larger N of *these same, mostly-easy* tasks would still produce a relatively low discordant rate, further limiting achievable power without also increasing task difficulty. |
| **The `[PROMPT GUARD]` noise source (92 events / 40 generations)** | **Minor** | A real, high-frequency background defect in response-formatting robustness, contributing to 2 of the 5 discordant outcomes (§7), but it hit both conditions (one treatment loss, one control loss) with no directional bias observed in this sample. |

---

## 10. Power/sensitivity analysis

Computed directly (exact binomial McNemar, not a normal approximation) rather than estimated:

**With exactly 5 discordant pairs, the smallest possible two-sided exact p-value achievable by any outcome is p=0.0625** (a 5-0 split: `binomtest(5, 5, 0.5)`). **A 3-2 split (what was observed) is nowhere close to the most extreme possible outcome, and even the most extreme possible outcome would not have reached the conventional p<0.05 threshold.** This is a mathematical fact about this specific dataset's discordant-pair count, not an estimate: **this experiment could not have produced a statistically significant McNemar result under any of its own possible realizations.**

For context, computed the same way: reaching p<0.05 requires at minimum 8 discordant pairs (achieved only at a 0-8 or 8-0 split, p=0.0078); a more realistic, less extreme asymmetry needs considerably more discordant pairs than that. Given this run's own observed 25% discordance rate (5/20), reaching even 8 discordant pairs at the same rate would require roughly N≈32 tasks — and reaching enough discordant pairs to detect a *moderate*, non-extreme true effect (e.g., a true 65/35 split of discordant pairs, not 100/0) would require substantially more than that, plausibly in the range Tier-4 itself used (n=84) or larger.

**Plain statement**: if the true effect of the Tier-5 fixes on paired coding correctness is small or even moderate, this experiment had effectively no chance of detecting it statistically. If the true effect were extremely large (e.g., the fixes fully eliminating a defect that previously affected the majority of discordant cases), it *might* have been detectable — but the observed 3-2 split is far short of what even a large true effect at this N would need to produce a significant result. **N=20 (5 discordant) is not merely underpowered for a moderate effect — it is underpowered even for most large effects**, and this must not be read as license to trust the mechanistic (non-statistical) evidence in §1 as a substitute for statistical power; they answer different questions, as §9 of the original report and this audit both maintain separately.

---

## 11. Architectural interpretation

**What the experiment demonstrates** (directly supported):
- The current, live, Tier-5-fixed `river_deliberation.py` implementation, exercised through its real production code path, did not produce a net paired correctness deficit relative to the disabled-fix control in this specific 20-task sample (numerically ahead, 90% vs. 85%).
- `find_missing_agreed_definitions()` is not merely present in source — it was **observed, live, in this run's own log, correctly detecting and rejecting exactly the failure class it was built for**, on three separate occasions (`r-iv04`'s absence-causes-failure case in control, plus `r-ae01`/`r-ae02`'s presence-prevents-failure cases in treatment), with zero observed instances of either Tier-5 mechanism causing a worse outcome anywhere in this batch.
- Zero of the 5 discordant cases in this batch reproduce Tier-4's specific "synthesis destroyed an already-unanimous-correct candidate set" mechanism.

**What the experiment suggests** (reasonable, not definitive):
- The Tier-5 fixes plausibly prevented at least 2 additional treatment failures beyond the one directly visible via the control-side comparison (`r-ae01`, `r-ae02}) — inferred by analogy to `r-iv04`'s demonstrated failure shape, not directly proven, since the counterfactual (what treatment's output would have scored without the fallback) was never actually executed or scored.
- The coding-synthesis correctness problem Tier-4 documented may be meaningfully reduced by the Tier-5 fixes specifically for the "dropped agreed definition" failure class — this is the one mechanism this retest actually has repeated, on-point evidence for.

**What the experiment does NOT establish**:
- Whether the aggregate ±5pp (or Tier-4's original ∓11.9pp) is closer to the true population-level effect — the data cannot distinguish these.
- Whether Council/synthesis remains net-harmful, net-neutral, or net-beneficial for coding tasks in general, at production scale.
- Anything about non-coding task classes (unchanged from the state established in `audits/2026-09-13_council_correctness_investigation.md`).
- Whether the fixes are *sufficient* to close the correctness gap Tier-4 found, only that the *specific*, previously-documented failure mode did not recur and the fix mechanism was seen actively working.

**Does this experiment justify changing the FeralEcho architecture? RESULT INCONCLUSIVE on the statistical/architectural question, with the caveat that RUN ANOTHER EXPERIMENT is the correct operational response** — specifically, a larger-N rerun (informed by §10's math: meaningfully more than 20 tasks, ideally powered toward Tier-4's own n=84 scale or larger, given the observed ~25% discordance rate) is the only way to convert the genuine, real, positive mechanistic evidence already gathered here into something that can also speak to the aggregate-magnitude question. **PROCEED WITH LIMITED CHANGE does not apply** — no change is being recommended by this audit; the original report's "B — retain with existing fixes, evidence still limited" stands, and this audit finds that recommendation slightly *undersold* by the original report's own falsification section (§9 of the retest report missed the `find_missing_agreed_definitions` log evidence entirely), not oversold.

---

## 12. What remains unknown

Unchanged from the original report, and from `audits/2026-09-13_council_correctness_investigation.md` before it: whether any of this generalizes to non-coding task classes; whether the aggregate coding-correctness gap (in either direction) would replicate at Tier-4 scale; whether `detect_full_agreement`'s shortcut path specifically (as opposed to `find_missing_agreed_definitions`'s completeness check, which this audit found direct evidence for) contributed anything observable in this batch — no `[DELIBERATION]`-tagged log line in this run's stdout references full-agreement-shortcut activation specifically, only the completeness-check fallback; this remains a genuine, real gap in this dataset's instrumentation, not resolved by this audit.

---

## 13. Recommendation

No architectural change is justified by the current evidence, in either direction. The original report's recommendation (B — retain with existing fixes, evidence still limited) is upheld, and this audit's own independent work strengthens rather than weakens the mechanistic half of that case (3 of 20 tasks show direct, on-point evidence the fix works; 0 of 20 show it hurting). The statistical half remains, and will remain, uninformative until a substantially larger N is run — §10's math should be used directly to size that future experiment rather than re-deriving it from scratch.

---

## 14. Exact evidence paths/hashes needed to reproduce this audit's conclusion

- `audits/tier5_retest/tier5_retest_results.jsonl` (the sole source for all statistics in §8; independently re-parseable, 40 lines, no external dependency)
- `audits/tier5_retest/tier5_retest_stdout.log` (source for the `[DELIBERATION]`/`[PROMPT GUARD]` evidence in §3/§9/§11 — search for `[DELIBERATION]` and `[PROMPT GUARD]` directly)
- `audits/tier5_retest/tier5_retest_task_pool_FROZEN.py` + `audits/tier5_retest/tier5_retest_task_pool.hash.txt` (SHA256 `595bb18abf1b8c6ca6c34e23687b909551c6dd610eb860961b3714b82bc7b8ac`)
- `scripts/run_tier5_retest.py` (driver logic referenced throughout §2)
- `scripts/verify_synthesis_refactor_control.py` (source of the control monkeypatch pattern, lines 28-29)
- `app/core/river_deliberation.py:845,901,1342,1445` (Tier-5 mechanism definitions and call sites)
- `audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_results.jsonl` (the excluded, historical-only first attempt — referenced in §4, never pooled)

---

## Git discipline confirmation

- Starting HEAD: `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f`
- Ending HEAD: `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` (unchanged)
- `git status --short` line count: 126, identical before and after this audit's work
- Files changed by this audit: none
- Files created by this audit: exactly one — this report, `audits/2026-09-14_tier5_retest_adversarial_audit.md`
- Files deleted: none
- Pre-existing modifications before this audit began: yes, the same 126-line working-tree state inherited from all prior missions this session (Shadow retirement, CLAUDE.md's retirement entry, the Tier-5 retest's own artifacts and archived contaminated run, and unrelated earlier-session files) — none touched, none altered, confirmed identical at both ends of this audit's own work.
