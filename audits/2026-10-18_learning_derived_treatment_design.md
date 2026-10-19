# Learning-derived treatment — design audit

Date: 2026-10-18. Inspection clock: 2026-10-18 22:10:27 PDT. Machine: M5. Cash cost of this pass: $0. Model calls: 0. Production files written: none.

Status of this document: design and read-only analysis. No selector was created. No test was executed. No new grade exists.

Recommendation: **stop this research branch.**

Labels used below: OBSERVATION, RETRIEVED EVIDENCE, INFERENCE, ASSUMPTION, UNKNOWN. Claim strength is preliminary, supported within tested conditions, contradicted within tested conditions, or unresolved.

This pass did not re-grade the Stage-1 matrix, did not re-run the previous-outcome replay, did not re-run the information-bottleneck census, did not open accumulation-probe grade summaries, and did not import the application package. Closed numerical results are cited from the audits that already published them. One arithmetic recombination of the already-published held-out table is labeled as such. It is a check of an existing candidate, and it is a new experiment in no sense.

Predecessor, left unchanged: `audits/2026-10-18_prospective_generalization_design.md`. Its recommendation stands: no suitable test family was established, because every closed rule chooses DIRECT on every proposed evaluation task. This document asks the follow-up that recommendation named and did not answer: whether any other rule can be derived from the training evidence already in hand.

## Closed findings, preserved

These results stay as reported.

- RETRIEVED EVIDENCE. The task-specific selector gained a mean of 1/6 on held-out repeats of K2.T1–K2.T6. The gain is K2.T2 (STEPWISE 4/6 versus DIRECT 0/6 on both halves, delta 2/3) and K2.T5 (2/6 versus 0/6, delta 1/3). K2.T1, T3, T4, and T6 stay DIRECT, delta 0. The unit is the task, n=6. This is a held-out repeat of known templates. Source: `audits/2026-10-18_evidence_integrity_and_generalization.md` and the held-out table in `audits/2026-10-19_learning_strategy_information_bottleneck.md`.
- RETRIEVED EVIDENCE. The coarse signature `arg_count_bucket|input_shape` changed 0 choices and its mean delta is 0. K2.T1–T5 share `1|tuple`. On that pool, select rates are DIRECT 0.6, STEPWISE 0.6, WORKED_EXAMPLE 1/3, and validate rates are DIRECT 0.5, STEPWISE 0.5, WORKED_EXAMPLE 1/3. Earliest order keeps DIRECT. Assigning STEPWISE to the whole pool is also delta 0. `2|tuple` is K2.T6 alone and stays DIRECT. An unobserved signature falls back to DIRECT.
- RETRIEVED EVIDENCE. The previous-outcome replay scored 4/12, the same as always-DIRECT, with 0 decisions changed. `pass_rule_met` is false. Seed 20261019. Source: `audits/2026-10-19_previous_outcome_replay.md`.
- RETRIEVED EVIDENCE. The frozen Stage-1 statistical result is Outcome E, inconclusive. Template-level Friedman n=6, statistic 4.80, p=0.0907. Source: `audits/2026-09-27_strategy_characterization_stage1_forensic_mining.md`. This pass does not reinterpret that result.
- UNRESOLVED, and left unresolved. Transfer to an unseen task family remains UNKNOWN. The absence of a justified treatment in this document does not convert that unknown into a universal negative.

## 1. What the existing evidence demonstrates

The question in this section is narrow. A relationship counts as demonstrated when a published result, on data already graded, ties a pre-declared input to a strategy outcome under a rule that was fixed before that outcome was used to build the input. A pattern noticed after the winners were known is a hypothesis.

### Demonstrated, and limited to repeated templates

RETRIEVED EVIDENCE. On the six K2.T templates, with repeats {0, 1} choosing and repeats {2, 3} scoring, a lookup by task id that sends only K2.T2 and K2.T5 to STEPWISE beats always-DIRECT by 1/6. Both changed choices beat DIRECT on the validate half in the same direction as the select half. Supported within tested conditions. The information the lookup uses is the task id. The tasks are the same six templates on both halves.

RETRIEVED EVIDENCE. The complete Stage-1 grid scores all three strategies. The mining audit records 216 unique keys, 0 duplicates, and Outcome E unchanged (Friedman n=6, statistic 4.80, p=0.0907). The bottleneck audit records full-grid rates DIRECT 43/72, STEPWISE 44/72, WORKED_EXAMPLE 22/72. That full-grid ordering is descriptive. The held-out task table is the selection result this branch is allowed to use.

The published held-out table, select then validate, rates over equal halves, order DIRECT / STEPWISE / WORKED_EXAMPLE:

| Task | Chosen | Delta | Select | Validate |
|---|---|---:|---|---|
| K2.T1 | DIRECT | 0 | 1 / 5/6 / 1/2 | 5/6 / 1/6 / 1/2 |
| K2.T2 | STEPWISE | 2/3 | 0 / 2/3 / 0 | 0 / 2/3 / 0 |
| K2.T3 | DIRECT | 0 | 1 / 1/2 / 2/3 | 5/6 / 1/2 / 1/6 |
| K2.T4 | DIRECT | 0 | 1 / 2/3 / 1/2 | 5/6 / 5/6 / 1 |
| K2.T5 | STEPWISE | 1/3 | 0 / 1/3 / 0 | 0 / 1/3 / 0 |
| K2.T6 | DIRECT | 0 | 1 / 1 / 0 | 2/3 / 5/6 / 1/3 |

K2.T2 and K2.T5 are the only rows with a strict non-DIRECT win on the select half. K2.T4's validate half prefers WORKED_EXAMPLE, and its select half prefers DIRECT, so the frozen rule leaves the delta at 0. K2.T6's select half ties DIRECT with STEPWISE. Earliest order keeps DIRECT and leaves STEPWISE's validate edge unused.

### Demonstrated, and unavailable to the authorized learner

RETRIEVED EVIDENCE. The mining audit, reading `output_tail`, `error_tail`, and generated code, reports a world-replicated shape: on K2.T2 and K2.T5, DIRECT failures return the wrong output shape, and STEPWISE removes most of that shape error on K2.T5 while K2.T2's remaining STEPWISE failures are ordering errors. K2.T6's WORKED_EXAMPLE collapse is real across three worlds and is more than one bug shape. Supported within tested conditions as a description of those logs.

RETRIEVED EVIDENCE. The learner authorized by the 2026-09-22 design receives exactly `(task_feature_signature, strategy_used, PASS|FAIL)`. `output_tail`, `error_tail`, duration, raw test code, raw candidate code, and expected values are excluded. `selector.py` `extract_sanitized_outcome` keeps `passed` and discards the rest. The diagnostic relationship is in the log. It is outside the information a routing rule in this branch is allowed to use. The mining audit's own classification is R4: further effort on this three-strategy routing question is not well justified by this dataset, and the diagnostic content points at a different primitive, experience then diagnosis then a retained correction. This document records that classification. It does not adopt the primitive as a treatment.

### Demonstrated absences of a transferable policy

RETRIEVED EVIDENCE. The coarse signature pools the two STEPWISE wins with three DIRECT wins. The gain disappears. Contradicted within tested conditions as a policy that carries the 1/6 to a new string.

RETRIEVED EVIDENCE. The previous-outcome replay, the published real-label table, and the live greedy selector state stay on DIRECT. Online arm C has zero STEPWISE teaching rows. One WORKED_EXAMPLE failure sits beside DIRECT. Every holdout decision in the pilot stayed DIRECT. A stored PASS or FAIL that leaves the next choice on DIRECT is an update with no changed decision. Contradicted within tested conditions as an improvement over always-DIRECT.

### Hypotheses

These are recorded so they are not later cited as results.

- HYPOTHESIS. A surface property such as "the required output extracts fewer fields than the raw input entry" separates K2.T2 and K2.T5. The mining audit, section 9, states that this property was not declared before Stage 1, that K2.T2 is `return_type` list and K2.T5 is `return_type` tuple, and that the property is ineligible for the frozen Stage 2 trigger. Read literally, name-only extraction also describes K2.T1, where the select half is DIRECT 6/6. A reading that also covers a ranked sublist describes K2.T4, where the select half prefers DIRECT. The property is hypothesis-generating. It is a treatment in no sense.
- HYPOTHESIS. A disjunction written now, "full ranking, or a (name, score) tuple, chooses STEPWISE," would match the two winners. That sentence is assembled from the outcomes. It is retrospective feature selection on n=6 with two positive tasks.
- HYPOTHESIS. Fitting a predictor now on `output_tail` or `error_tail` would recover a routing rule. The bottleneck audit already refused that fit as contaminated, because the exclusion was written before the data and the tails have since been read. This pass does not open them for a new fit.
- UNKNOWN. Whether any rule, under some future pre-registration written before new grades, would beat always-DIRECT on a genuinely unseen family.

## 2. Why the closed mechanisms are not a transferable learner

### Task identity

The non-DIRECT outputs of the task-id rule are the strings `K2.T2` and `K2.T5`. A new task carries a new id. The lookup has no row for it. The published fallback is DIRECT. The 1/6 measures repetition of the templates the rule names.

INFERENCE. Mapping a new id onto K2.T2 or K2.T5 by shared solution base uses the generator field `base`. K2.N3 shares `k2_rank` with K2.T2. K2.N6 shares `k2_winscore` with K2.T5. That field is hidden test information relative to the rendered task. The 2026-10-18 prospective-generalization audit already refused the mapping. This pass refuses it again.

### Coarse situation signature

OBSERVATION. `app/experiments/persistent_routing/features.py` is the frozen extractor. Its key is `arg_count_bucket|input_shape`, computed from the rendered signature and spec. The 2026-09-22 design, section 6, gives `update()` that key, the strategy name, and PASS or FAIL. Nothing else.

The two tasks with a strict STEPWISE select win, and the three tasks whose select half prefers DIRECT, share one observed key, `1|tuple`. One strategy per key cannot keep DIRECT on K2.T1, K2.T3, and K2.T4 while taking STEPWISE on K2.T2 and K2.T5. The published pool ties, so the rule stays on DIRECT. `2|tuple` is one task and stays on DIRECT. A string the extractor has never counted returns DIRECT.

INFERENCE. On a new task, the extractor either lands in a bucket whose published choice is DIRECT or lands in no bucket and returns DIRECT. The signature implements a learner. The learner's stored experience does not change the action relative to always-DIRECT, on the families already scored and on the candidate strings already signed.

### Previous-outcome replay

The replay adds the preceding outcome to the key and replays the real online labels. The published table chooses DIRECT in every populated cell. STEPWISE has no online teaching attempts, so no cell has a STEPWISE mean that could win. The frozen pass rule failed at 4/12 against 4/12. Retuning thresholds, seeds, or the key on those same labels is the revision this branch already closed.

INFERENCE. Replay demonstrates that a later choice can be a function of an earlier PASS or FAIL. On these labels the function is constant and equal to the baseline. A constant function equal to the baseline is a recorded history. It is an improvement in no sense.

## 3. The pre-declared return_type grouping, examined and rejected

This is the remaining candidate that was frozen before outcomes and has not yet been written down as a treatment decision in this branch. It is rejected here.

OBSERVATION. `app/experiments/strategy_characterization/dimensions.py` declares the Q2 dimensions before any Stage-1 call. The file says `return_type` is the sole eligible dimension. `operation` is ineligible because each level is one task. `arg_count` is ineligible because level 2 is only K2.T6. `output_cardinality` is ineligible for the same near-total confound. The map is a hardcoded dict from task id, and the file says it is not derived from `feature_signature()`:

| Task id | return_type |
|---|---|
| K2.T1 | str |
| K2.T2 | list |
| K2.T3 | str |
| K2.T4 | list |
| K2.T5 | tuple |
| K2.T6 | bool |

`CONFIRMATION_TASK_DIMENSIONS` tags K2.S1 str, K2.S2 list, K2.S3 str, K2.S4 list, and the file says those tags are for Stage 2 only and are not exercised until a Stage 2 is separately authorized.

RETRIEVED EVIDENCE. Protocol section 7 labels Q2 exploratory until a Stage 2 confirmation. Protocol section 9 runs Stage 2 only when Q2 shows one strategy visibly ahead inside a dimension level and reversed or absent in another level. Before any Stage 2 seed, a freeze record must name the `return_type` value, the predicted winner, the comparator, the test, and one-sided α = 0.05. The mining audit, section 10, states that the `return_type` grouping failed adversarial inspection because K2.T2 and K2.T4 disagreed. Stage 2 was not opened. Outcome E stands.

RETRIEVED EVIDENCE, recombined. The following pools use the published held-out rates above. Each task half is 6 trials (2 repeats × 3 worlds). Equal task counts make a 12-trial pool the same quantity as the mean of the two task rates. This recombination was not a census rerun.

Select half, str = K2.T1 + K2.T3 (12 trials): DIRECT 12/12, STEPWISE 8/12, WORKED_EXAMPLE 7/12. DIRECT is strictly ahead. The level stays DIRECT.

Select half, list = K2.T2 + K2.T4 (12 trials): DIRECT 6/12, STEPWISE 8/12, WORKED_EXAMPLE 3/12. The pooled select maximum is STEPWISE, which would assign STEPWISE to both list tasks. K2.T4's own select half is DIRECT 6/6 against STEPWISE 4/6. The two tasks inside the only replicated non-scalar level disagree. That is the disagreement the mining audit already recorded.

Validate half, list, if STEPWISE were assigned anyway: STEPWISE 9/12, DIRECT 5/12, WORKED_EXAMPLE 6/12. K2.T2's own validate delta versus DIRECT is 4/6. K2.T4's own validate rates for STEPWISE and DIRECT are both 5/6, so that task's delta is 0.

tuple is K2.T5 alone. bool is K2.T6 alone. `dimensions.py` marks `operation` and `arg_count` ineligible for this reason: a level that contains one task is the task id under another name. Assigning STEPWISE to tuple is the K2.T5 row of the task-id rule. bool's select half ties DIRECT with STEPWISE at 6/6, and earliest order stays DIRECT.

Per-level select winners, using the same earliest-tie rule as the published table: str → DIRECT, list → STEPWISE, tuple → STEPWISE, bool → DIRECT. Applied to the six tasks, that is the task-id policy plus an extra STEPWISE assignment on K2.T4. K2.T4's validate delta is 0, so the six-task mean remains 1/6. Refusing the single-task levels and changing only list leaves K2.T5 on DIRECT. The six-task mean is then (2/3) / 6 = 1/9, which drops the unreplicated K2.T5 gain and adds a zero-delta change on K2.T4.

INFERENCE. Both readings are coarsenings of the memorized task-id rule. The dict that implements `return_type` has no entry for a new task id, and the file does not parse a new spec. A new task cannot be labeled list, str, tuple, or bool by this table without either a memorized id or a fresh labeling rule written after the winners are known. Writing that labeling rule now would use the outcomes to decide which strings count as list. That is the leakage this mission forbids.

INFERENCE. Sending list → STEPWISE onto K2.S2 and K2.S4 would be the Stage 2 confirmation. The trigger requires a directionally consistent level. The list level is not directionally consistent on the select half. No freeze record of the five Stage 2 items exists, and this document does not write one. K2.S2 and K2.S4 are a confirmation split for a failed exploratory grouping. They are an unseen family in no sense.

RETRIEVED EVIDENCE, cited as a limit on the existing grid and as a power claim in no sense. Protocol section 8: at n=6, no pairwise Wilcoxon can reach Bonferroni α = 0.0167 at any effect size, because the minimum exact two-sided p is 2/2^6 = 0.03125. This pass invents no sample size and no confidence statement for a prospective run.

WORKED_EXAMPLE has no strict select-half win in the published task table, and none in the str pool (7/12 against DIRECT 12/12) or the list pool (3/12 against STEPWISE 8/12). tuple and bool have WORKED_EXAMPLE select rate 0. The authorized select-then-validate rule has no cell in which WORKED_EXAMPLE is the choice.

## 4. Treatment

No treatment is justified.

The information a rule in this branch would be allowed to receive, and the time it would receive it, are fixed by the predecessors:

- When: frozen before any new grade on an evaluation task.
- From the training record: task ids K2.T1–K2.T6, the published held-out rates, the coarse key computed by `features.py`, and PASS/FAIL outcomes already stored for those keys.
- At decision time on a new task: the rendered signature and spec, passed through the already-frozen extractor, and no grade, no solution base, no generator `base` field, no split label, no `output_tail`, no `error_tail`, and no feature defined after inspecting which templates won.

The choice those inputs support:

- On K2.T2 and K2.T5, STEPWISE. That choice is the closed within-template result. It is already scored. It is an evaluation of transfer in no sense.
- On K2.T1, K2.T3, K2.T4, and K2.T6, DIRECT.
- On any other task id, the extractor returns `1|tuple`, `2|tuple`, or a key with no counts. Each of those returns DIRECT under the published tie and the published fallback.

INFERENCE. The allowed rule names STEPWISE only by recognizing the two memorized template ids. It has no principled basis for naming STEPWISE or WORKED_EXAMPLE on a task whose id is new. Where the rule chooses DIRECT on every evaluation task, a comparison with always-DIRECT has decision delta 0 and cannot show an improvement. Assigning a non-DIRECT strategy in order to create a measurable difference would be an arbitrary forcing. This document does not make that assignment.

## 5. Evaluation families, assessed on their own

Family suitability is judged here without assuming a treatment exists. A family is suitable for a transfer test when its solution templates and its success role were outside the fitting set, a pre-registered role allows a positive delta to count as transfer, and the family was not already used to design the rule. "Ungenerated" is not that property. The prospective-generalization audit reached the same family conclusions for the three closed rules. This section repeats the inspection against the broader question, including K2.S, which that audit's pilot scope had withheld from the candidate list.

### K2.T1–K2.T6

RETRIEVED EVIDENCE. This is the fitting set. All three strategies are graded. The 1/6 is a repeat of these ids. The family cannot test transfer.

### K2.S1–K2.S4

RETRIEVED EVIDENCE. The 2026-09-22 design assigns split S the role "narrow structural transfer," and it is the only claim-bearing split in that design. The 2026-09-27 protocol separately assigns these four tasks as the Stage 2 confirmation set for `return_type`, with S2 and S4 tagged list. The persistent-routing pilot already includes S, and the online learner's holdout decisions on S stayed DIRECT. STEPWISE and WORKED_EXAMPLE grades for a `return_type` confirmation on S2 and S4 were not collected, because Stage 2 did not open.

INFERENCE. Generating those missing strategy grades now would reopen an untriggered confirmation on tasks whose dimension tags and DIRECT outcomes are already known. Contamination is the shared generator, the shared kind, the pre-assigned dimension tags, and the observed DIRECT holdouts. K2.S is a real split with a pre-registered role. It is a clean unseen family for a newly invented routing rule in no sense.

### K2 NEAR

RETRIEVED EVIDENCE. `NEARS["K2"]` reuses the six K2.T solution bases under new ids and paraphrased specs, plus an explicit convention mismatch. The 2026-09-22 design, section 4, assigns NEAR the role of specificity control. A win there is a negative finding and is excluded from transfer credit. Strategy-menu grades for K2.N1–K2.N6 do not exist in the persistent-routing artifacts. The closed rules choose DIRECT on all six signed strings, as the predecessor audit recorded.

INFERENCE. K2 NEAR fails the suitability test. Shared bases mean a positive delta can be template memory. The pre-registered role forbids counting that delta as transfer. Absence of a strategy-menu grade does not repair either fact.

### UNREL

RETRIEVED EVIDENCE. U1–U12 are topically separate functions with no K2 solution base. The same 2026-09-22 section assigns UNREL the role of confound control. A positive delta is a red flag and is excluded from evidence for the hypothesis. The predecessor audit signed the coarse key: U4 lands on `1|tuple` because the spec contains the word "tuple," and every other UNREL key is unobserved. Both paths choose DIRECT.

INFERENCE. UNREL fails the suitability test for a transfer claim. The role was frozen before this branch proposed the family. A rule that chose a non-DIRECT strategy here would still be barred from counting the result as transfer, and no such rule is justified.

### K1, K3, and other experiment families

RETRIEVED EVIDENCE. K1 and K3 exist in the generator. They were not signed. No three-strategy Stage-1 grid for this menu exists for them. Substituting them would be a new study. The other experiment directories inventoried in the integrity audit (accumulation probe, belief revision, preference provenance, and the rest) are different constructs. Accumulation-probe summaries were not opened. Their rates are a threshold in no sense.

UNKNOWN. Strategy-menu pass rates on K2 NEAR, UNREL, K1, and K3. Those rates are absent. Creating them is outside this authorization.

No family inspected here is suitable for a prospective transfer test of a learning-derived strategy rule.

## 6. Prospective comparison, frozen as a stop

The comparison is written down before any new grade. Its result is that the comparison is uninformative, so it is not run.

Hypothesis, frozen: an information state produced by the existing training evidence, forbidden from using the evaluation task's outcome, solution base, task id as a memorized lookup, or any other hidden test information, changes at least one later choice among DIRECT, STEPWISE, and WORKED_EXAMPLE on a genuinely unseen task family, and on the task as the unit raises the pass rate above always-DIRECT.

Status of the hypothesis: unresolved in general, because no accepted evaluation family and no accepted treatment exist. Contradicted within tested conditions for the three closed rules at the decision layer, on the strings the predecessor audit already signed, where every choice equals DIRECT.

Treatment under test: none. No rule is frozen for execution.

Task-level scoring, inherited from the predecessor protocol and not refit on any outcome:

- The unit is the task.
- `decision_changed` is true only when the frozen rule names a strategy other than DIRECT.
- A task with `decision_changed` false contributes delta 0 and is not sent to a model.
- A task with `decision_changed` true is the mean of its prespecified repeats under the chosen strategy, minus the mean of the same repeats under DIRECT, same seeds.
- A missing grade is excluded from that task's mean. It is entered as 0 in no calculation. If either arm has no grade, the task delta is unscorable and stays unscorable.
- Success requires all of: at least one `decision_changed` true; the primary mean strictly greater than 0; every unscorable task listed; the family unused in fitting the rule; the family's pre-registered role, where one exists, allowing a positive delta to count as transfer.
- A rule that did change a choice fails when the primary mean is less than or equal to 0 and no task is unscorable.
- The result is inconclusive when a choice changed and a changed task is unscorable, or when the scored mean is positive and a pre-registered role forbids counting it as transfer.
- Design stop, which is the result of this audit: no treatment is justified, and every choice the allowed evidence supports is DIRECT on every task other than the memorized K2.T2 and K2.T5. The success predicate's first clause is false for any accepted evaluation family. The test is not informative. It is not run.

No new numeric margin is added. The AP-0 draft thresholds named in the predecessor (NEAR 18, UNREL 12, and the harm margins) remain a draft for a different arm set. They are this protocol's rule in no sense.

No sample size is frozen, because a run that does not change a decision gains no information from extra tasks or extra repeats. Protocol section 8's n=6 pairwise ceiling is a fact about the existing Stage-1 unit. It is a power analysis for a future experiment in no sense. The 2026-09-22 design already recorded that a confirmatory lineage count was unjustified in the absence of a successful pilot. The pilot that later ran did not beat always-DIRECT.

Seeds are not drawn. If a later, separately authorized study ever used the existing harness, pairing would be the published `seed_for` in `common.py`. This sentence authorizes no such study.

## 7. Resources and cost

This pass spent $0 and made 0 model calls. The only file it adds is this audit.

OBSERVATION, this session, 2026-10-18 22:10:27 PDT. `hw.memsize` is 25769803776 bytes. `memory_pressure` reported pages free 67605, page size 16384 (67605 × 16384 = 1,107,640,320 bytes free), pages purgeable 9724, compressor pages used 304371, swapins 321148721, swapouts 509765276. Historical swap is large. The free-page count at this instant is a snapshot. It is a license to generate in no sense, and it is a statement that memory pressure has ended in no sense.

An informative experiment's call count is UNKNOWN, because no informative treatment exists. A contrast whose every decision equals DIRECT requires 0 model calls. Any experiment that needs new model outputs stays unauthorized until a separate approval.

## 8. Unresolved uncertainties

- UNKNOWN. Transfer of a learning-derived strategy choice to a genuinely unseen task family, in general. This branch stops with that question open.
- UNKNOWN. Whether a different primitive, diagnosis then a retained correction, pre-registered before any new grade, would change a later outcome. The mining audit names the question in its section 15. This document does not convert that question into a routing rule, and it does not authorize the generations the question would require.
- UNKNOWN. The launcher of the second persistent-routing holdout write. The integrity audit closed the duplicate as repeated measurement of one seeded evaluation. This pass does not reopen it.
- UNKNOWN, and to remain unmeasured under this authorization. Strategy-menu pass rates on K2 NEAR, UNREL, K1, and K3.
- UNKNOWN. Whether any stored `world.json` priority token was hand-edited outside the CVCVC generator. This pass did not hash those files. The treatment conclusion does not depend on a new signature string.
- RETRIEVED EVIDENCE, not rechecked. The protocol states that byte-for-byte seed reproducibility was not independently verified.
- The census tie is earliest order over (DIRECT, STEPWISE, WORKED_EXAMPLE). `selector.py` breaks a mean tie by dict insertion order. On the published select ties that determine a choice, both procedures stay on DIRECT. This pass does not open a new tie analysis.

## 9. Authorization required for a next step

No execution is authorized.

The human action this document supports is to stop the strategy-routing branch.

The following remain unauthorized: creating a selector; editing `features.py`, `dimensions.py`, or the persistent-routing harness; fitting a keyword, a `return_type` parser, or any other surface feature on the known winners; reading `output_tail` or `error_tail` to build a router; writing a Stage 2 freeze record; generating STEPWISE or WORKED_EXAMPLE grades on K2.S; generating K2 NEAR or UNREL for this menu; launching the shelved 12-family pilot; calling a model; spending money; opening accumulation-probe summaries to hunt a threshold; modifying production, the two dirty source files `app/core/echo_model_orchestrator.py` and `app/core/river_deliberation.py`, protected files, source logs, or frozen audits.

A future study of a diagnostic correction would need its own authorization and its own pre-registration, written before any new grade, with a success rule of its own. This document does not request that study and does not describe it as the next step of this branch.

## 10. Recommendation

**stop this research branch.**

No defensible learning-derived treatment is currently established. Every rule the existing evidence can justify without leakage, without forcing a strategy, and without an assumption the pre-registration already refused, chooses DIRECT on every task other than the two memorized templates. A prospective comparison against always-DIRECT cannot show an improvement in that setting. Unseen-family transfer remains UNKNOWN. The uncertainty is preserved.
