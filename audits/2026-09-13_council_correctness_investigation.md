# Does Council Systematically Harm Correctness? An Investigation

**Type:** Read-only investigation. No production code modified. No commit made.
**HEAD:** `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` (unchanged throughout).

---

## 1. Executive conclusion

**Coding/objective tasks: Council's free-text synthesis step demonstrably and specifically loses correctness that already existed in the candidate set. This is established at a mechanistic level with strong, direct evidence — including cases immune to sampling-artifact explanations — but the top-line pass-rate comparison (Council vs. single-model sampling) is NOT statistically significant at n=84 (p=0.087, pre-registered bar p≤0.048). The mechanism finding and the aggregate-comparison finding are two different claims with two different confidence levels; conflating them overstates the evidence.**

**Non-coding tasks (creative, reasoning, general — the task types that actually reach Council's synthesis step; personal/reflective/faith/poetry/dream bypass Council entirely by design): UNKNOWN. No experiment anywhere in this repository's research corpus tests Council's effect on correctness, quality, or any other outcome for these task types.** This is a genuine, unfilled gap, not evidence of no effect.

**Echo globally: NOT established, and the evidence does not support a global claim in either direction.** The strong coding evidence is specific to one bounded task suite (short, single-function-shaped coding problems), a since-partially-fixed synthesis mechanism, and zero cross-domain testing. Extrapolating "Council harms correctness" to Echo as a whole would be exactly the kind of unsupported generalization this mission was designed to prevent.

---

## 2. Current architecture

Traced directly from `app/core/river_deliberation.py` (`deliberate_and_learn()`) and `app/core/echo_model_orchestrator.py`, both `EDIT_FORBIDDEN_TARGETS` (read, not modified). This is the **current, live production pipeline**, already reflecting fixes made after the Tier-4 confirmatory experiment — a fact that matters directly for how historical evidence should be read (§4).

1. **Task-type routing.** `DIRECT_ECHO_TASKS = {personal, reflection, spiritual, identity, faith, poetry, dream}` bypasses Council entirely — a single direct call to `echo:latest`, no councillors, no synthesis. Every other task type (`coding`, `creative`, `reasoning`, `general`, and others) goes through the full Council pipeline below.
2. **Candidate generation.** `council_size` defaults to `DEFAULT_COUNCIL_SIZE = 3` (confirmed: `river_deliberation.py:137`, also referenced directly in `scripts/run_tier3_apparatus.py` and `scripts/verify_tier3_apparatus_readiness_audit.py` as matching real production parity). `_select_council()` picks 3 models; each is queried once at a distinct, jittered temperature (`_jittered_temperature()`) — real per-model sampling diversity, not identical prompts at identical settings.
3. **Candidate storage.** Raw per-councillor responses held in an in-memory `opinions: dict[model -> text]` for the duration of one `deliberate_and_learn()` call; persisted afterward to `memory/council_deliberations.jsonl` via `_log_council_deliberation()` (raw + truncated text, per-model temperature, synthesis output) — not silently discarded after the call returns.
4. **Fallback behavior, pre-synthesis.** Empty council → direct Echo query, bypassing synthesis and candidates entirely. All councillors errored → same direct-query fallback. Exactly one valid opinion and it's Echo's own → returned directly, no synthesis (avoids Echo "synthesizing" its own single voice through a meta-prompt).
5. **Agreement shortcut (`detect_full_agreement()`), coding only.** If every candidate's extracted code is AST-identical (whitespace/comment/quote-style independent), the LLM synthesis call is **skipped entirely** and the agreed code returned verbatim. This is a post-Tier-4 fix (Tier-5 refactor, 2026-09-04) — it did not exist during the Tier-4 confirmatory experiment itself.
6. **Synthesis.** For every task type reaching this stage, one call to `ECHO_SYNTHESIS_MODEL = "echo:latest"` combines the candidate opinions into one final response. Two distinct system prompts exist: `SYNTHESIS_SYSTEM_TEMPLATE` (all non-coding task types — "integrate the best insights while staying true to your own voice," explicitly licenses rewriting) and `SYNTHESIS_SYSTEM_TEMPLATE_CODING` (coding only, since the Tier-5 refactor — explicitly a preservation contract: "Your role is preservation, not authorship... Do not paraphrase or rewrite code that is already correct"). **The non-coding template has never been changed in response to any of this evidence** and is the same free-text, rewrite-licensing template the whole synthesis-loss finding was discovered against.
7. **Post-synthesis completeness check (`find_missing_agreed_definitions()`), coding only.** If every parseable candidate agreed on defining some function/class and the synthesis output's own top-level definitions don't include it, the synthesis is **rejected outright** (not repaired) and replaced by `select_best_fallback_candidate()`'s choice. Also a post-Tier-4 fix.
8. **Fallback candidate selection (`select_best_fallback_candidate()`).** Three-stage rule: (1) majority AST-structural agreement, ties broken by length; (2) an explicitly-not-implemented RiverBrain-tiebreak stage (Tier-7 found this signal performs worse than chance once isolated from model-identity confound — deliberately never shipped); (3) shortest parseable candidate. Verified against the real 168+168-event Tier-4 corpus at 96.1% correct-pick on real production council shape — a real, measured, already-hardened mechanism, not a naive heuristic.
9. **No verification step exists for non-coding synthesis output at all** — no agreement shortcut, no completeness check, no fallback-candidate selection. A creative/reasoning/general synthesis call's output is returned unconditionally once non-empty and error-free, identical to the pre-Tier-5-refactor coding behavior that produced the documented `cs09`/`bf06` failures.
10. **Post-synthesis learning.** Each councillor's own opinion trains `RiverBrain` under its own identity; only the synthesis model learns from the final synthesized text — this was already true before Tier-5 and is unchanged.

---

## 3. Evidence inventory

| Study | Source report | N | Metric | Comparator | Task class | Oracle/verification |
|---|---|---:|---|---|---|---|
| Tier-3 pilot | `audits/tier3_heldout_scoring_analysis.md` (cited via Tier-4's own report, which restates and supersedes the number) | 8 | `ARCH_COUNCIL` vs `BASE_N` pass rate | Single-model N-sample vs. heterogeneous council | Coding | Real sandboxed execution |
| Tier-4 confirmatory, primary | `audits/tier4_confirmatory_report.md` | 84 (pooled, two 42-task disjoint stages) | Paired PASS/FAIL, exact McNemar | `BASE_N` (79.8%) vs `ARCH_COUNCIL` (67.9%) | Coding | Real sandboxed execution, hash-frozen frozen task suite |
| Tier-4 confirmatory, mechanism | Same report | 84×2 arms (336 total records) | Oracle rate (≥1 component independently correct) vs. real delivered synthesis rate | `BASE_N`: 95.2% oracle / 79.8% delivered (15.5pp lost). `ARCH_COUNCIL`: 96.4% oracle / 67.9% delivered (28.6pp lost) | Coding | Zero new model calls — re-scoring of already-generated `mechanism_calls` text against the same real sandbox |
| Tier-4 confirmatory, secondary | Same report | 84 | `BASE_1` (88.1%) vs `ARCH_PIPELINE_ISOLATED` (64.3%) | Bare single-call prompting vs. Echo's own self-edit generation framing | Coding (general, not literal self-edit path) | Real sandboxed execution, p=0.0002 |
| Tier-5 refactor validation | `audits/tier5_refactor_report.md` | 5 fresh tasks (small, explicitly disclosed as underpowered for a pass-rate delta) + direct replay of the 2 known historical failures (`cs09`, `bf06`) | Pass/fail + selection-mechanism trigger rate | Refactored pipeline vs. itself with mechanisms patched to no-ops | Coding | Real end-to-end `deliberate_and_learn()` calls, real sandbox |
| Tier-6 disagreement forensic | `audits/tier6_disagreement_resolution_forensic.md` | 168+168 real Tier-4 events (re-analysis, zero new model calls) | Fallback-candidate correct-pick rate | Length-based heuristic vs. structural-agreement heuristic | Coding | Real sandboxed correctness, replayed from stored Tier-4 text |
| Tier-7 RiverBrain forensic | `audits/tier7_riverbrain_candidate_ranking_forensic.md` | Real Tier-4 corpus (re-analysis) | RiverBrain-score tiebreak accuracy, isolated from model-identity confound | 38.9% (worse than chance) on the isolating pair | Coding | Real historical data, re-scored |
| Tier-8 isolation forensic | `audits/tier8_experimental_isolation_forensic.md` | N/A (forensic audit of the apparatus itself, not a capability result) | Contamination classification per historical run | — | Meta (apparatus integrity) | Log-timestamp cross-referencing |

**Non-coding evidence: no rows exist.** A targeted repository-wide search for any experiment comparing Council's effect on creative, reasoning, general, planning, or reflective task correctness/quality found nothing. This absence is itself recorded as a finding, not filled with inference.

**Every number above traces to a primary source read directly in this mission** (`audits/tier4_confirmatory_report.md`, `audits/tier5_refactor_report.md`) or to production source code read directly (`river_deliberation.py`) — none are repeated from a secondhand summary without independent confirmation. One number is explicitly *not* independently re-derived: the Tier-3 pilot's 8-task, 37.5pp figure is restated exactly as Tier-4's own report cites it (Tier-4's report itself frames the pilot as context for its own confirmatory result, and re-deriving the pilot's raw scoring was out of this mission's scope — flagged as a secondhand citation, not a primary one).

---

## 4. Causal analysis

**The evidence establishes a real causal mechanism for two specific, replicated failure cases — stronger than mere correlation — but does not establish that synthesis is the dominant cause of the aggregate pass-rate gap, because that aggregate gap is not itself statistically significant.**

Two things must be kept separate, because Tier-4's own report keeps them separate and later summaries (including this session's own earlier capability-benchmark-harness report) sometimes compress them into one headline:

1. **The mechanism claim (candidate correctness → synthesis → loss) is directly, causally demonstrated**, not merely correlated, via the "7 all-correct-components, still-wrong-synthesis" subset. Tier-4's own adversarial-interpretation section makes this argument explicitly and correctly: if synthesis were unbiased selection among options that are *all* correct, the expected outcome is 100% correct, every time — there is no "roll" to lose in that subset, so an order-statistics explanation (three attempts beat one by pure chance) cannot apply. Synthesis still failed in all 7 of these cases. This is genuine causal evidence, not correlational — it isolates the synthesis step as the active agent of failure in a subset where nothing else could explain the result.
2. **The aggregate pass-rate gap (`BASE_N` 79.8% vs `ARCH_COUNCIL` 67.9%, −11.9pp) is NOT statistically significant** (exact McNemar p=0.087, below the pre-registered bar of p≤0.048) **and swung by nearly an order of magnitude between the pilot (37.5pp) and the two confirmatory stages (4.76pp, 19.05pp) that were themselves pooled from the same protocol.** Tier-4's own report treats this candidly: the *direction* replicated across three independent samples, the *magnitude* did not, "a textbook regression-to-the-mean signature of an original small-n estimate."

**Alternative explanations checked, per the mission's Phase 2C requirement:**
- *Candidate generation differences*: ruled out as a confound for the mechanism finding — the oracle rate (95.2%/96.4%) is computed from the exact same generated text the real synthesis call also received; there is no separate generation step being compared.
- *Unequal model counts / compute budget*: `ARCH_COUNCIL` made 5 real calls vs. `BASE_N`'s 4 (disclosed, unnormalized asymmetry) — Tier-4's own report argues this cannot explain the result, since more compute should help, not hurt, and `ARCH_COUNCIL` still lost more (28.6pp) than `BASE_N` (15.5pp) despite having more calls available.
- *Temperature*: a real, disclosed, partially-overlapping confound — `BASE_1` runs at temperature 0.0 while `BASE_N`/`ARCH_COUNCIL` sample at ~0.7±0.15. This plausibly explains part of why `BASE_1` beats `BASE_N`, but Tier-4's report notes it does *not* explain `ARCH_PIPELINE_ISOLATED`'s underperformance (same temperature 0.0 as `BASE_1`, still −23.81pp) — a second, independent, temperature-unrelated cause. This confound was **named but never isolated by a dedicated controlled experiment** (e.g., re-running `BASE_N` at temperature 0.0) — an explicit, acknowledged gap in Tier-4's own report.
- *Evaluation leakage, verifier differences, scoring artifacts*: Tier-4's own H3 check (0 infrastructure failures, 0 truncations across all 336 real candidates, evaluator independently re-verified via the same oracle re-scoring pass) argues against a measurement-artifact explanation.
- *Implementation changes since the data was collected*: **this is a real, live confound for anyone reading the historical numbers today.** The agreement shortcut and completeness check (§2) did not exist when Tier-4's 84-task data was collected. The historical `ARCH_COUNCIL` pass rate (67.9%) describes a synthesis mechanism strictly worse than the one currently in production for coding tasks — the current mechanism has real, structural protections the tested mechanism did not. This does not invalidate the mechanism finding (both documented failure examples, `cs09` and `bf06`, were directly replayed against the fixed code and correctly handled — see §5), but it does mean **the 67.9%/11.9pp numbers should not be read as describing today's coding Council's current pass rate.**

**Conclusion**: candidate correctness → synthesis-caused loss is established as a real, causal mechanism, demonstrated concretely and replicated in two independent failure examples. Whether that mechanism explains the *majority* of the aggregate gap, versus other contributing factors (temperature, order statistics in the non-immune cases), is not established — the aggregate gap itself did not clear its own pre-registered significance bar.

---

## 5. Synthesis-loss mechanisms

**Observed, directly documented examples (not hypotheses):**

1. **Correct-information deletion** (`cs09`, `BASE_N`, Stage 1): all three same-model attempts independently produced a complete, correct `ThreadSafeMultiCounter` class with proper locking. Synthesis retained only the `if __name__ == "__main__":` demo block and dropped the class definition entirely — immediate `NameError`. The correct implementation existed, verified, in all three inputs; synthesis discarded the part that mattered.
2. **Fabrication into unanimous-correct input** (`bf06`, `ARCH_COUNCIL`, Stage 2): all three heterogeneous councillors produced byte-for-byte identical correct code (`find_missing`). There was no disagreement to synthesize. The synthesis output introduced an unsupported `n = len(nums) - 1` — a fabricated `-1` present in none of the three inputs — breaking correct logic that required zero reconciliation.
3. **Aggregate scale of the phenomenon**: of 44 real failures examined across both arms in the confirmatory experiment, 38 (86%) had at least one individual component that would have passed independently if it alone had been delivered (`ARCH_COUNCIL`: 25/27 failures, 92.6%; `BASE_N`: 13/17, 76.5%). In 7 of those, *every* individual component was independently correct and synthesis still produced a wrong final answer.
4. **Rare, real counterexample**: synthesis was observed to genuinely rescue a fully-wrong candidate set into a correct final answer exactly once, in `ARCH_COUNCIL`, out of 84 real candidates — real, but negligible next to the 28.6pp it loses in the opposite direction.

**Hypothesized, not directly observed in this repository's evidence:** whether the same "own voice, integrate, rewrite" licensing that `SYNTHESIS_SYSTEM_TEMPLATE` grants (unchanged, still live for every non-coding task) produces analogous fact-dropping or fabrication for non-coding content. No documented example of this exists in the corpus searched. This is a plausible mechanistic extension, explicitly flagged here as **speculation, not evidence** — the template's wording is structurally identical in spirit to the pre-fix coding template that caused the two documented failures, which is a reasonable basis for suspicion but not itself a measurement.

---

## 6. Cross-domain assessment

| Task class | Evidence | Council effect | Confidence | What remains unknown |
|---|---|---|---|---|
| Objective/checkable (coding) | Tier-3/4/5/6/7/8, n=84 confirmatory + 2 direct replicated failure examples | HARMFUL at the mechanism level (established); aggregate pass-rate effect PARTIALLY SUPPORTED (real direction, not significant magnitude) | High for mechanism, Moderate for aggregate magnitude | Whether the post-Tier-5-refactor mechanism still loses correctness at a similar rate — no fresh, powered re-test exists (§10) |
| Factual reasoning | None found | **UNKNOWN — no experiment establishes Council's effect in this task class.** | None | Everything — no baseline, no comparator, no oracle definition attempted |
| Planning/decision | None found | **UNKNOWN — no experiment establishes Council's effect in this task class.** | None | Everything |
| Creative | None found (creative task type reaches Council's plain synthesis template in production; zero dedicated research) | **UNKNOWN — no experiment establishes Council's effect in this task class.** | None | Whether "integrate in your own voice" causes fact-loss or quality-loss for creative content the way it did for code; no objective oracle even exists for this domain to measure against |
| Reflective/personal | `DIRECT_ECHO_TASKS` structurally bypasses Council entirely for this category (personal, reflection, spiritual, identity, faith, poetry, dream) | **N/A — Council is not invoked for this task class in production**, confirmed directly from source, not inferred | High (for the routing fact only) | Whether this routing choice was itself evidence-driven or a design default — not investigated by this mission |
| Other ("general" task type) | None found | **UNKNOWN — no experiment establishes Council's effect in this task class.** | None | Everything |

---

## 7. Counterevidence

Per Phase 9's explicit requirement, evidence weakening or complicating the harm hypothesis, found rather than manufactured:

1. **The primary aggregate comparison did not reach statistical significance** (p=0.087 vs. a pre-registered p≤0.048 bar) — the single strongest piece of counterevidence against a strong "Council materially harms coding correctness" claim, and it comes from the same experiment cited as the headline evidence for harm. Any summary that omits this is overstating the finding.
2. **The pilot's estimate (37.5pp) was substantially inflated by small-sample noise** — a real, measured instance of exactly the effect a skeptic would predict before trusting a small-n pilot result, self-identified by the confirmatory experiment's own authors rather than by an external critic.
3. **A real rescue case exists**: synthesis corrected a fully-wrong candidate set into a correct answer once in 84 trials — proof the mechanism is not unconditionally destructive.
4. **The current production system already has real, structural fixes** (agreement shortcut, completeness check) that eliminate the exact two documented failure classes by construction/detection, verified via direct replay against the real historical failure cases — the harm finding is partially self-correcting, not a static, still-fully-live defect.
5. **`select_best_fallback_candidate()`'s hardened, measured 96.1% correct-pick rate** on real production council-disagreement shape is itself evidence that *this specific piece* of the Council pipeline performs well — the finding is not "everything about Council fails," it's specifically the free-text synthesis step for coding.
6. **`BASE_1` (a single deterministic call, zero architecture at all) beat every other arm, including `BASE_N` (same-model sampling)** — this weakens any framing that positions "single-model sampling" as an obviously superior alternative architecture; the strongest performer in this experiment was not multi-sample-and-select, it was the simplest possible strategy. This complicates Architecture B (§8) more than it complicates Council specifically.
7. **No evidence anywhere in the corpus supports Claim 4 (generalizes beyond coding) or Claim 5 (should be removed globally)** — the complete absence of contrary evidence is itself worth stating plainly as a limit on how far the coding finding can be legitimately extended, not just an absence to be silently worked around.

---

## 8. Architectural comparison

| Architecture | Information preservation | Corruption opportunity | Requires oracle? | Suitability by task class | Known evidence | Unknowns |
|---|---|---|---|---|---|---|
| **A — Current Council** (N candidates → free-text synthesis → answer) | Low for coding pre-fix (demonstrated); currently partially improved for coding via post-hoc checks; unmeasured elsewhere | High — an LLM rewrite step with no verification, still the default path for every non-coding task type | No (which is itself the problem for objective domains) | Demonstrated poor fit for coding without the Tier-5 additions; unknown fit elsewhere | Tier-3/4/5/6/7/8 (coding only) | Everything outside coding |
| **B — Single model, N samples, select/verify** | Depends entirely on the select/verify step's quality — `BASE_N`'s own oracle-vs-delivered gap (15.5pp) shows this architecture is *not* automatically safe either | Moderate — no synthesis rewrite risk, but a weak selection mechanism still loses information (demonstrated: `BASE_N` lost real correctness too, just less than `ARCH_COUNCIL`) | Ideally yes, for the select step to be trustworthy | Best-demonstrated performer among "no free-text synthesis" architectures in this one coding suite (`BASE_1`, degenerate N=1 case, was the strongest arm overall) | Tier-4 (coding only) | Whether the diversity `BASE_N`/`ARCH_COUNCIL` are meant to provide has value anywhere this experiment didn't test |
| **C — Candidate preservation + deterministic verification** (agreement shortcut / tests / structural checks, minimal formatting only) | High — this is structurally what the Tier-5 refactor already partially built for coding | Low, by design — no free-text rewrite step when a deterministic check can resolve the case | Yes, requires a real oracle (tests, AST structure) — this is exactly why it's coding-only today | Directly demonstrated effective for the two known coding failure classes; **fundamentally inapplicable, as currently designed, to any task type lacking a deterministic checker** (creative, personal, most reasoning) | Tier-5 refactor (2 replicated fixes, small live-validation batch) | Whether a non-coding equivalent of "deterministic verification" can even be defined; no fresh, powered re-test of the coding version exists either |
| **D — Council as verifier, not author** (independent evaluation → select an existing candidate → no free-text rewriting) | Highest in principle — no generative step touches already-produced content | Lowest in principle, if the verifier itself is reliable | Not necessarily a hard oracle — could be model-judgment-based, but then inherits whatever unreliability model-judgment carries | Never built or tested anywhere in this codebase for Council specifically | **None** — this is architecturally plausible and mentioned by the mission, but zero evidence, positive or negative, exists for it in this repository | Everything — untested speculation, not a supported conclusion |

No architecture is recommended for implementation on the strength of this comparison alone — Architecture D in particular "sounds elegant" (avoids the demonstrated risk by construction) but has zero empirical support in this codebase; recommending it would repeat the exact mistake this investigation was designed to catch.

---

## 9. Claims ladder

| Claim | Verdict | Evidence |
|---|---|---|
| **1. Council can harm correctness** | **SUPPORTED** | The 7 all-components-correct-but-synthesis-wrong cases are direct, mechanism-immune-to-order-statistics evidence. `cs09`/`bf06` are concrete, replicated, disclosed examples. |
| **2. Council materially harms coding correctness** (in aggregate, at production scale) | **PARTIALLY SUPPORTED** | Real, consistent-direction effect across 3 independent samples (pilot + 2 confirmatory stages), but the pooled magnitude (11.9pp) did not clear the pre-registered significance bar (p=0.087 vs. ≤0.048). "Materially" is doing real work in this claim that the data does not fully discharge. |
| **3. The free-text synthesis step is the mechanism responsible** | **SUPPORTED**, for the specific documented cases; **PARTIALLY SUPPORTED** as the dominant explanation for the full aggregate gap | The 7-case subset directly isolates synthesis as causal, immune to alternative explanation. Temperature and order-statistics effects are real, disclosed, only-partially-isolated contributing factors to the *broader* 15.5pp/28.6pp gaps, not fully separated from the pure-synthesis-defect contribution. |
| **4. This mechanism generalizes beyond coding** | **UNKNOWN** | Zero experiments exist testing any non-coding task class. The structural similarity between the pre-fix coding template and the still-live non-coding template is a reasonable basis for suspicion, explicitly labeled as speculation in §5 — not evidence. |
| **5. Council harms non-coding tasks** | **UNKNOWN** | Same as above — no data exists in either direction. |
| **6. Council is globally harmful** | **UNKNOWN, and the available evidence argues against extending the coding finding this far without new data** | The coding evidence is scoped to one bounded task suite and a since-partially-fixed mechanism; personal/reflective/faith/poetry/dream never reach Council at all; three of five real task-type categories have zero evidence in either direction. |
| **7. Council should be removed from Echo globally** | **CONTRADICTED, as a conclusion this evidence would support** | No mission finding anywhere in this corpus argues for global removal; Tier-4's own explicit, evidence-grounded verdict is REFACTOR, not RETIRE, even for coding specifically — "the underlying idea... is not shown to be worthless." Extending that to "remove globally" would be a strictly stronger claim than the strongest available source makes for even the one domain with real data. |

---

## 10. Smallest next experiment

**Two candidate experiments answer two different open questions; neither has been run.** Per Phase 7's instruction to identify the smallest one, not the most comprehensive:

**Experiment 1 (highest priority — already explicitly recommended by Tier-5 itself, never executed): does the current, post-refactor coding Council still lose correctness at a similar rate?**
- **Hypothesis**: the Tier-5 refactor (agreement shortcut + completeness check) measurably reduces, but does not eliminate, the synthesis-loss gap found in Tier-4.
- **Task strata**: a fresh, disjoint, hash-frozen 20-30 task coding suite (mirroring Tier-4's own discipline — never reused from the pilot, the 84-task confirmatory suite, or the 5-task validation batch).
- **Comparison groups**: the same tasks run twice under identical real conditions — once with the Tier-5 mechanisms active, once with `detect_full_agreement`/`find_missing_agreed_definitions` patched to no-ops (Tier-5's own control-run pattern, already built in `scripts/verify_synthesis_refactor_control.py`, reusable rather than reinvented).
- **Sample size rationale**: 20-30 tasks is Tier-5's own stated recommendation, sized to detect whether the refactor's benefit holds at a scale beyond the 5-task validation batch (explicitly too small to show a pass-rate delta) without re-running the full 84-task Tier-4 protocol.
- **Metrics**: primary — paired McNemar on pass/fail per task per condition; secondary — real `completeness_fallback`/`full_agreement_shortcut` trigger rate on a larger, more diverse sample than the 5-task pass achieved.
- **Raw candidate + synthesis preservation**: reuse the existing `mechanism_calls`-style full-text capture already built for Tier-4/Tier-5.
- **Deterministic oracle**: real sandboxed test execution, as every coding tier before it used.
- **Contamination controls**: reuse Tier-8's now-fixed `install_isolation()` (the RiverBrain background-writer-thread gap it found is closed per this session's own prior mission), and confirm CLEAN status the same way Tier-8 did for Tier-4/5. **Additionally, and not covered by Tier-8's own isolation fix**: this experiment's correctness oracle is real sandboxed test execution — the exact execution path the separately-closed F2 stdin/fd0 lineage (`research/FINDINGS.md` R-010, Missions 24-30) found could silently corrupt a result rather than just fail loudly. Before this experiment's real candidate/task runs begin, confirm the sandbox invocation used for scoring inherits the current, hardened `safe_exec_wrapper.py` (`_BlockedStdin` + closed fd 0) rather than an older or bypassed invocation path — a hung or falsely-short-circuited sandboxed test run would directly corrupt the one deterministic oracle this whole experiment's causal claim depends on, the same class of contamination risk Tier-8's `install_isolation()` closed for RiverBrain state, applied here to the test-execution oracle instead.
- **Stopping criteria**: fixed sample size (not sequential/early-stop, given the small scale) — 20-30 tasks run to completion, both conditions, no interim peeking.

**Experiment 2 (the genuinely novel question this mission's brief foregrounds): does Council's synthesis step cause any measurable effect — positive, negative, or none — on a non-coding task class?**
- **Hypothesis**: none pre-specified in this report (this would be the *first* experiment in this domain — appropriately exploratory, not confirmatory).
- **Task strata**: pick exactly one non-coding class with the best-available oracle proxy — "creative" is the most tractable starting point, since `DIRECT_ECHO_TASKS` already excludes personal/reflective content from Council, and "reasoning"/"general" tasks could plausibly borrow a checkable-fact-based design (e.g., structured word/logic puzzles with a single correct answer) rather than needing a fully subjective creative-quality judgment on the first pass.
- **Comparison groups**: Council synthesis vs. `BASE_N` (same-model, N-sample) vs. `BASE_1`, mirroring Tier-4's own arm structure for direct comparability.
- **Sample size rationale**: given zero prior data exists in this domain, a small pilot (8-12 tasks, matching Tier-3's own original pilot scale) is the appropriate first step — Tier-3/4's own history is a direct, in-repository cautionary tale against over-trusting a small pilot's magnitude, but an appropriately small, cheap first look is still the correct sequencing before committing Tier-4-scale resources to an unexplored domain.
- **Metrics**: explicitly separate correctness (only where a real checkable answer exists), factual accuracy (for any verifiable claims embedded in output), usefulness/coherence/preference (rated, explicitly labeled as subjective, never conflated with the objective metrics above).
- **Deterministic oracle where available; subjective evaluation where not** — and the report from this pilot should state plainly which of its own conclusions rest on which kind of evidence, per this mission's own standard.
- **Contamination controls**: same isolation discipline as Experiment 1.
- **Stopping criteria**: fixed small sample (this is explicitly a pilot, not a confirmatory run) — report the result honestly as preliminary regardless of direction, exactly as Tier-3's own pilot should have been treated before Tier-4 confirmed or disconfirmed it.

Neither experiment was run, built, or scaffolded by this mission, per its explicit scope boundary.

---

## 11. Recommended immediate action

**Justified by the evidence actually established in this investigation:**

1. **For coding specifically**, the existing Tier-5 refactor's own unexecuted recommendation — a fresh, powered re-test (Experiment 1, §10) — remains the single highest-value, lowest-cost next step, and it was already designed and partially scaffolded by the team that built the fix. This is not a new recommendation; it is flagging that a previously-recommended, cheap, well-specified experiment has gone unexecuted since 2026-09-04.
2. **Do not extend any Council restriction, redesign, or removal to non-coding task types** on the strength of the coding evidence — no experiment supports this, and the personal/reflective/faith/poetry/dream categories already structurally bypass Council, so there is no live gap to close there in the first place.
3. **Do not recommend Architecture D ("Council as verifier")** for implementation despite its principled appeal (§8) — it has zero empirical support in this codebase, and recommending untested architecture because it "sounds like it would avoid the problem" is precisely the kind of reasoning this investigation's own integrity requirements warn against.
4. **If any single, cheap documentation action is worth taking outside this report**: the fact that Tier-4's headline numbers (67.9% `ARCH_COUNCIL`, 11.9pp gap) describe a synthesis mechanism that no longer exists in production (the Tier-5 refactor changed it) is a real, live risk of future misreading — any future summary of "the Council finding" should cite the mechanism evidence (§5) as the load-bearing claim and treat the raw aggregate percentages as historical, pre-fix numbers, not current production behavior. This report itself follows that discipline throughout.

**Not recommended, because the evidence does not justify it**: any global Council redesign, removal, or restriction; any change to the non-coding synthesis template; any new taxonomy or labeling mechanism layered onto Council's output (out of scope for this mission and, per this session's separate research thread on evidence taxonomies, carries its own documented risk — `research/DECISIONS.md` D-001 — not investigated here but worth flagging as a reason not to reach for a labeling-based fix by default).
