# Tier-5 Council Correctness Retest — Execution Results

**Date:** 2026-09-13/14 (interrupted attempt 2026-09-13, clean rerun completed 2026-09-14 after reconnection)
**Type:** Experiment-execution mission (not archaeology, not implementation)
**Status:** Complete. HEAD unchanged. No production code modified.

---

## 1. Executive conclusion

In a fresh, disjoint, 20-task coding retest, **the current, Tier-5-fixed Council did not lose paired correctness relative to the control** — it was numerically ahead (90% vs. 85%, +1 net task), the opposite direction from Tier-4's original ~12-point Council-behind finding. This result is **not statistically resolvable at this sample size** (McNemar exact p=1.0 on only 5 discordant pairs) and must not be read as proof the architecture is now safe or equivalent. What the retest *does* establish, concretely: **none of the 5 discordant cases in this batch show the "synthesis destroyed an already-unanimous-correct candidate set" mechanism** that was Tier-4's strongest evidence, and one Council-win case is a direct, on-point mechanistic confirmation that Tier-5's completeness-check fix (`find_missing_agreed_definitions`) prevents exactly the failure class it was built for — visible via its *absence* causing the control condition to fail that exact way on a task the treatment condition passed cleanly. This is real, positive, disclosed evidence — not proof the coding-synthesis problem is solved, but a genuine update away from "the fixed Council still measurably loses correctness" toward "the fixed Council's known failure mechanism was not observed, and the fix's own mechanism was directly seen working, in a small fresh sample."

## 2. Research question

Verbatim, from `audits/tier5_refactor_report.md`'s own unexecuted next-experiment recommendation and `audits/2026-09-13_council_correctness_investigation.md` §10 Experiment 1: **after the Tier-5 Council changes — the agreement-shortcut (`detect_full_agreement`) and completeness-check (`find_missing_agreed_definitions`) fixes — does Council still lose coding correctness relative to a single-model/sampling control?**

## 3. Pre-registered methodology

Fixed before any outcome was inspected, per Tier-4/Tier-5's own established discipline:

- **Treatment**: the real, unmodified, live production synthesis path — `river_deliberation.deliberate_and_learn()` with `detect_full_agreement`/`find_missing_agreed_definitions` active exactly as shipped.
- **Control**: the identical real `deliberate_and_learn()` call, with those same two functions monkeypatched to permanent no-ops in-process — reproducing exact pre-Tier-5-refactor behavior, using the identical monkeypatch already established by `scripts/verify_synthesis_refactor_control.py` (reused verbatim).
- **Task set**: 20 fresh, disjoint coding tasks (`r-bf01..04`, `r-ae01..04`, `r-rf01..04`, `r-iv01..04`, `r-dt01..04`, spanning `bug_fixing`/`algorithmic_edge_case`/`refactoring`/`input_validation_defensive`/`data_transformation_parsing`), authored in `tier4_task_pool.py`'s exact `_t(task_id, category, prompt, test_code, reference_solution)` convention, checked for zero overlap with Tier-4's 84-task pool, the 5-task `VALIDATION_TASKS` batch, and `held_out_task_suite.json`. Frozen and hashed before execution: `audits/tier5_retest/tier5_retest_task_pool_FROZEN.py`, SHA256 `595bb18abf1b8c6ca6c34e23687b909551c6dd610eb860961b3714b82bc7b8ac`.
- **Oracle**: real, deterministic sandboxed test execution (`run_capability_pilot.py`'s `objective_verify()`, unmodified), same isolation apparatus as every prior coding tier.
- **Primary test**: McNemar's exact test on the paired 2×2 discordant-pair table, as specified by Tier-5.
- **Stopping rule**: fixed N=20, run to completion, no interim peeking, no task exclusion after seeing outcomes.

**Prior interrupted attempt, disclosed as part of this record, not hidden**: a first execution attempt (same task pool, same driver) was interrupted mid-run when the host machine's lid was closed for a train departure. Direct evidence, not inference: task `r-rf03` recorded an 18,024-second (~5-hour) generation time for treatment and 16,440 seconds (~4.6 hours) for control in that attempt — an unmistakable sleep-spanning-the-measurement artifact — and the run died entirely before completing task 20/20, killed by a 600-second stall watchdog. That entire partial dataset was judged contaminated and discarded — not resumed, not partially trusted — and archived rather than deleted, at `audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_{results.jsonl,progress.txt,stdout.log}`, disclosed here as historical evidence rather than silently dropped. The clean rerun documented in this report used the identical, unmodified task pool and driver script.

## 4. Environment and Git provenance

| | |
|---|---|
| Starting Git HEAD | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` |
| Ending Git HEAD | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` (unchanged) |
| Working-tree status | 125 changed lines in `git status --short` before and after this mission (pre-existing from earlier sessions; this mission's own additions are entirely new/untracked files under `audits/tier5_retest/` and two `scripts/` files, collapsed into the same untracked-directory line git already showed) |
| Production code | Confirmed unmodified. `app/core/river_deliberation.py` shows as modified in `git status`, but this predates this mission entirely (confirmed by the immediately-prior investigation mission in this same session, which independently verified it never called Edit/Write on that file either) — this mission's driver script monkeypatches `rd.detect_full_agreement`/`rd.find_missing_agreed_definitions` as in-process function-attribute reassignment only, never writing to the file on disk, confirmed by direct code read. |
| Council implementation under test | `app/core/river_deliberation.py:845` (`detect_full_agreement`) and `:901` (`find_missing_agreed_definitions`) — both confirmed present and live in the current file via direct grep immediately before this run, not assumed from documentation. |

## 5. Contamination controls

- **F2 stdin/fd0 protection**: `sandbox/safe_exec_wrapper.py`'s `_install_patches()` installs `_BlockedStdin` and closes fd 0 before any candidate code runs, per the already-closed F2/R-010 lineage — the same sandboxed execution path every prior coding tier and this retest both route through via `objective_verify()`. Not independently re-verified line-by-line in this pass (out of this mission's scope per its own hard boundary), but confirmed structurally unchanged: `git status` shows no modification to `sandbox/safe_exec_wrapper.py`.
- **Sandbox execution / oracle integrity**: real, kernel-sandboxed test execution for both conditions, unmodified from `run_capability_pilot.py`'s established `install_isolation()`/`objective_verify()` pair — identical apparatus Tier-3 through Tier-8 already used and verified.
- **The sleep-interruption finding itself, as a contamination control lesson applied**: this mission is a direct, concrete, second reproduction of the general class of risk `research/FINDINGS.md` R-010 (Missions 22/23) first documented for a different subsystem (a real OS clamshell-sleep event extending a long-running process's measured duration) — now independently observed corrupting a *different* long-running process's timing data via the identical mechanism. The clean rerun avoided it simply by not being interrupted, not by any new code-level defense; this remains a real, standing environmental risk for any future long-running experiment on this hardware, not something this mission closed.
- **Isolation from RiverBrain contamination (Tier-8's finding)**: `run_capability_pilot.install_isolation()` was called at the top of the driver script's `main()`, the same mechanism Tier-8 verified redirects `RIVER_BRAIN_PATH` before any `get_river_brain()` call — not independently re-verified with a fresh forensic pass in this mission (that would exceed this mission's narrow scope), but the mechanism itself was not touched or bypassed.

## 6. Dataset

20 tasks, 2 conditions each = 40 total records, confirmed complete: `audits/tier5_retest/tier5_retest_results.jsonl` contains exactly 40 lines, 20 unique task IDs each with exactly one `treatment` and one `control` record, zero records with a captured `exception`. Task selection: authored fresh (not pulled from any existing pool) using Tier-4's own established task-content convention — 4 tasks in each of 5 categories already used by Tier-4's own 6-category structure (a subset, not the full 6), each with a real prompt, a real sandboxed `test_code` oracle, and a reference solution.

## 7. Results

| | Control (fixes disabled) | Treatment (Council, Tier-5 fixes live) |
|---|---:|---:|
| Correct | 17/20 | 18/20 |
| Accuracy | 85.0% | 90.0% |

**Council − Control = +5.0 percentage points (+1 task, net).**

Paired 2×2 contingency table (N=20):

| | Control correct | Control wrong |
|---|---:|---:|
| **Treatment correct** | 15 | 3 |
| **Treatment wrong** | 2 | 0 |

- Both correct: 15
- Both wrong: 0
- Council wins (treatment right, control wrong): **3** — `r-dt03`, `r-iv04`, `r-rf01`
- Council losses (treatment wrong, control right): **2** — `r-ae03`, `r-bf04`
- Discordant pairs: 5

## 8. Statistical analysis

McNemar's exact test (binomial on the 5 discordant pairs, 3 vs. 2): **p = 1.0000** (two-sided). This is about as uninformative as a significance test can be — with only 5 discordant observations, the test has essentially no power to distinguish "true improvement," "no real effect," or even a small true Council disadvantage from pure sampling noise. **This must not be read as evidence of equivalence, and the +5pp point estimate must not be read as a precise or reliable effect size** — both cautions the pre-registered methodology explicitly required stating.

## 9. Discordant-case analysis

**Council losses (treatment wrong, control right):**

- **`r-ae03`**: Treatment's underlying code (`is_clean_palindrome`, stripping non-alnum characters and comparing to its reverse) was **logically correct** — it failed only because the raw model response began with the prose line `"Here is the final code:\n\n"` ahead of the fenced block, and `clean_code()`'s extraction left that line in the executed script, producing a `SyntaxError` before the real logic ever ran. **This is a prose-leak/extraction-robustness failure, not the Tier-4 "synthesis destroyed correct content" mechanism** — the content was never destroyed, it was never successfully extracted from otherwise-correct output.
- **`r-bf04`**: Treatment's `dedupe_preserve_order` used a genuinely broken idiom (`seen.add(item)` always returns `None`, making the filter condition always false, so the result is always empty) — a real logic defect. **This dataset cannot determine whether this defect originated in a pre-synthesis candidate or was introduced by synthesis itself**: unlike Tier-4's `mechanism_calls`-style full per-councillor capture, this retest's driver only records the final treatment/control output, not each raw candidate opinion — a real, disclosed methodological limitation of this smaller retest, not an oversight to be silently smoothed over.

**Council wins (treatment right, control wrong):**

- **`r-iv04` — the most mechanistically important result in this dataset.** Control's response contained *only* three `print(clamp(...))` calls referencing a `clamp` function that was never defined anywhere in the returned code — the exact "dropped the real definition, kept only a demo/usage block that references it" failure shape Tier-4's `cs09` case documented as one of its two headline synthesis-corruption examples. Treatment's response, from the identical task and prompt, contained a complete, correct `clamp` definition. Since the *only* mechanical difference between these two conditions is whether `find_missing_agreed_definitions()` is active, **this is direct, positive, on-point evidence that the completeness-check fix catches and prevents exactly the failure class it was built for**, observed live on a task neither Tier-4 nor Tier-5's original 5-task validation batch ever tested.
- **`r-dt03`**: control's nested-flatten helper had a genuine logic gap (an `AssertionError` on the real test); treatment's recursive implementation was correct. A plausible, ordinary case of one sample succeeding where another didn't — no distinguishing synthesis-specific mechanism identified.
- **`r-rf01`**: control's response also leaked leading prose ("Here's a cleaner version of your function:") into the extracted script, causing a `SyntaxError` — the same prose-leak failure class as `r-ae03` above, but this time hurting the *control* condition. Confirms the prose-leak issue is **not Council-specific** — it recurred symmetrically in both conditions across this small sample (once favoring, once disfavoring treatment), consistent with ordinary per-call stochastic variation in response formatting rather than anything mechanistically tied to synthesis.

**Net mechanistic read**: zero of the 5 discordant cases in this batch reproduce Tier-4's strongest evidence (synthesis actively corrupting an already-unanimous-correct candidate set). One case (`r-iv04`) is a genuine, positive, mechanistically clean demonstration that a specific Tier-5 fix works as designed. Two of the five discordant cases (one loss, one win) share a *different*, Council-independent failure mode (leading-prose extraction robustness) that this retest was not designed to measure but happened to surface.

## 10. Comparison with Tier-4

Tier-4 confirmatory finding (n=84, pooled): control (`BASE_N`) 79.8%, Council (`ARCH_COUNCIL`) 67.9%, an 11.9-point gap that did not clear its own pre-registered significance bar (p=0.087 vs. ≤0.048), with 7 cases where every candidate was independently verified correct and synthesis still produced a wrong answer.

This retest (n=20): control 85.0%, treatment/Council 90.0%, a +5.0-point gap **in Council's favor**, with zero cases reproducing Tier-4's headline mechanism.

Classification, per the mission's own required options: **directionally reversed relative to Tier-4's aggregate finding, but genuinely inconclusive as to whether the underlying problem was "materially improved" or "eliminated" versus "not detected in a small sample."** N=20 with 5 discordant pairs is not remotely powered to distinguish these possibilities from each other, and this retest used a different (smaller, disjoint) task pool than Tier-4's, so composition differences cannot be ruled out as a contributing factor to the directional shift. What *can* be said with more confidence, because it rests on mechanistic observation rather than the aggregate statistic: the specific corruption mechanism Tier-4 documented did not recur here, and the specific fix built to prevent a related failure class (dropped definitions) was directly observed doing its job.

## 11. Falsification / limitations

Actively attempting to falsify "the repaired Council is now fine," per this mission's own required discipline:

- **Sample size is the dominant limitation.** 5 discordant pairs cannot distinguish a genuine, meaningful improvement from pure noise around a null effect, or even from a small residual Council disadvantage. p=1.0 is not evidence of equivalence.
- **Task composition differs from Tier-4's 84-task pool** — a fresh, smaller, independently-authored 20-task set could plausibly happen to be easier for Council or harder for solo sampling by chance; nothing in this retest rules that out.
- **No per-candidate capture** — this retest cannot confirm whether `r-bf04`'s logic bug originated pre- or post-synthesis, unlike Tier-4's fuller instrumentation. The claim "no case reproduced Tier-4's mechanism" is well-supported for 4 of 5 discordant cases (clear extraction-leak or clear pre-existing-logic-bug shape) but not fully verifiable for the fifth.
- **No direct log evidence that `detect_full_agreement`'s shortcut actually fired** in this run — grepped the full stdout log for any activation signal and found none; the fix's presence in source and its demonstrated effect in one case (`r-iv04`) is confirmed, but how often the agreement-shortcut path specifically executed (versus full synthesis running and simply agreeing with the control by chance) was not instrumented and cannot be recovered from this dataset.
- **The prose-leak failure mode recurring in this batch is a real, disclosed, un-investigated finding of its own** — it affected both conditions, contributed to 2 of the 5 discordant outcomes, and represents a `clean_code()`/extraction-robustness gap independent of the Council-vs-single-model question this mission was scoped to answer. Not investigated further here — flagged, not fixed, per this mission's own hard scope boundary.
- **This remains coding-only evidence.** Nothing here bears on non-coding task classes, which remain exactly as unknown as the prior investigation report already established.

## 12. Architectural implication (coding-only)

**Recommendation: B — Retain with existing fixes, evidence still limited.**

Not A ("retain unchanged"), because this experiment specifically tested the *already-fixed* architecture — "unchanged" doesn't cleanly apply, and the evidence is too thin to declare confident superiority or safety. Not C ("further repair required"), because no clear, repairable Council-specific defect surfaced in this batch — the two loss cases are either a shared, Council-independent extraction bug or mechanistically unattributable. Not D ("redesign toward deterministic selection"), because the evidence this retest actually gathered argues against urgency, not for it — Tier-4's original justification for considering D was the repeated, clean demonstration of synthesis destroying unanimous-correct candidates, and that specific evidence did not recur here. Not E ("inconclusive, no responsible conclusion possible"), because this retest did produce one clean, positive, mechanistically-grounded finding (`r-iv04`) worth keeping, even though the aggregate statistic alone is uninformative — "inconclusive on the aggregate, but with one real positive mechanistic data point" is a more precise, more honest classification than a blanket "inconclusive."

## 13. What remains unknown

Everything the prior investigation report already flagged as unknown remains unknown — this retest was scoped to coding only, per its own hard boundary, and does not touch:

- Non-coding domains (factual reasoning, planning/decision, creative generation) — zero experiments exist in any of these.
- Reflective/personal conversation — structurally bypasses Council already (`DIRECT_ECHO_TASKS`), no gap to close.
- Whether Council's broader architecture has value outside deterministic, oracle-checkable coding tasks — genuinely untested in either direction.

Additionally, newly surfaced by this retest specifically and now also unknown: whether the fresh +5pp directional result would hold, reverse, or wash out at a properly-powered sample size (Tier-4's own 84-task scale, or larger); and whether the prose-leak extraction issue found here is a meaningful, recurring drag on both conditions' real-world accuracy that a separate, small hardening pass could cheaply close.
