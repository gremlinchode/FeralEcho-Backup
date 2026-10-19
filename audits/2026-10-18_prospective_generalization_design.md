# Prospective generalization test — design and feasibility audit

Date: 2026-10-18. Inspection clock: 2026-10-18 21:53:02 PDT. Machine: M5. Cash cost of this pass: $0. Model calls: 0. Production files written: none.

Status of this document: design only. The proposed test was not executed. No new grades exist. No selector was retuned.

Recommendation: **no suitable test family established.**

Labels used below: OBSERVATION, RETRIEVED EVIDENCE, INFERENCE, ASSUMPTION, UNKNOWN. Claim strength is preliminary, supported within tested conditions, contradicted within tested conditions, or unresolved.

This pass did not independently re-grade the closed Stage-1 matrix, did not re-run the previous-outcome replay script, and did not open accumulation-probe v2 grade summaries. Closed numerical results are cited from the audits that already published them. Signature strings for the candidate families were recomputed in this session from the generator source.

## Closed findings, preserved

These results stay as reported. This document does not reopen them.

- RETRIEVED EVIDENCE. The task-specific selector gained a mean of 1/6 on held-out repeats of the six Stage-1 templates K2.T1–T6. The gain is concentrated in K2.T2 (STEPWISE 4/6 versus DIRECT 0/6 on both halves, delta 2/3) and K2.T5 (2/6 versus 0/6, delta 1/3). The other four tasks stay DIRECT, delta 0. The unit is the task, n=6. Source: `audits/2026-10-18_evidence_integrity_and_generalization.md`. This is a held-out repeat of known templates.
- RETRIEVED EVIDENCE. The coarse situation-signature selector (`arg_count_bucket|input_shape`) changed 0 choices and its mean delta is 0. On `1|tuple`, select rates are DIRECT 0.6, STEPWISE 0.6, WORKED_EXAMPLE 1/3, and validate rates are DIRECT 0.5, STEPWISE 0.5, WORKED_EXAMPLE 1/3. Insertion order keeps DIRECT. Choosing STEPWISE for the whole `1|tuple` pool is also delta 0. `2|tuple` is K2.T6 alone and stays DIRECT. An unobserved signature falls back to DIRECT (`selector.py` returns `DEFAULT_STRATEGY` when the bucket has no positive count).
- RETRIEVED EVIDENCE. The previous-outcome replay did not outperform always-DIRECT. Real labels scored 4/12, the same as always-DIRECT, with 0 decisions changed. `pass_rule_met` is false. Seed 20261019. Source: `audits/2026-10-19_previous_outcome_replay.md` and its result JSON.
- UNRESOLVED, and left unresolved. Transfer to an unseen task family remains UNKNOWN.

## 1. Candidate-family assessment

The earlier integrity audit named NEAR and UNREL as ungenerated inside the persistent-routing pilot. "Ungenerated" is true of that pilot's outputs. It is false of the task generator.

### What "ungenerated" means here

OBSERVATION, this session. `app/experiments/persistent_routing/tasks.py` `split_tasks()` returns only split `T` and split `S`. `harness.py` lines 17–19 state that NEAR and UNREL are withheld from the pilot. All three sealed lineages agree:

| Lineage | Prospective ids | Holdout ids | Dev |
|---|---|---|---|
| 0, 1, and 2 | K2.T1–K2.T6 | K2.S1–K2.S4 | empty list |

OBSERVATION. A search of `memory/experiments/persistent_routing/` found no task id `K2.N*`, no bare `U*`, and no split label NEAR or UNREL. The same search of `memory/experiments/strategy_characterization/` found none.

RETRIEVED EVIDENCE. `app/experiments/accumulation_probe/tasks_v2.py` `build_tasks_v2()` constructs both families. K2 NEAR is six tasks, ids `K2.N1`–`K2.N6`. UNREL is twelve tasks, ids `U1`–`U12`, `kind` None. Strategy-menu grades (DIRECT / STEPWISE / WORKED_EXAMPLE) for these ids do not exist in the persistent-routing artifacts. Accumulation-probe grades under other arms do exist and were already published in earlier AP-0 audits. Those summaries were not opened in this pass. Their rates are not used as a threshold.

### K2 NEAR

RETRIEVED EVIDENCE. `NEARS["K2"]` reuses the same solution bases as `KT["K2"]`, with renamed functions and paraphrased specs:

| NEAR id | Function | Base | Same base as |
|---|---|---|---|
| K2.N1 | `select_champion` | `k2_win` | K2.T1 `pick_winner` |
| K2.N2 | `select_last_place` | `k2_lose` | K2.T3 `pick_loser` |
| K2.N3 | `order_entries` | `k2_rank` | K2.T2 `rank_all` |
| K2.N4 | `leading_pair` | `k2_top2` | K2.T4 `top_two` |
| K2.N5 | `is_champion` | `k2_iswin` | K2.T6 `is_winner` |
| K2.N6 | `champion_with_score` | `k2_winscore` | K2.T5 `winner_with_score` |

The NEAR spec is `_near_base("K2")` plus the task sentence plus `EXPLICIT["K2"]`. `_near_base("K2")` is the ranking paragraph that already appears, in near-identical words, in `BASE_SPEC["K2"]` for the T and S tasks. `solution_realization` is `"mismatch"`: the stated convention conflicts with the carrier world. That is a convention-specificity construct. It is a renamed paraphrase of K2.T1–T6 plus that conflict. It is separate as a task id. It is the same six solution templates.

RETRIEVED EVIDENCE. The 2026-09-22 design (`audits/2026-09-22_preregistered_persistent_routing_experiment_design.md`, section 4) assigns NEAR a role written before any routing data: a specificity control. A selector that wins on NEAR by favoring the strategy that won on T or S is overgeneralized routing, and that design says the result must be reported as a negative finding. NEAR is excluded there from transfer credit.

INFERENCE. K2 NEAR does not test transfer to an unseen family. Mapping K2.N3 to K2.T2, or K2.N6 to K2.T5, by shared base function would use generator knowledge the rendered task id does not contain. That mapping is a retune. It is not adopted.

### UNREL

RETRIEVED EVIDENCE. `UNRELS` is twelve standalone functions: `sum_evens`, `reverse_words`, `flatten_once`, `run_length_encode`, `max_in_list`, `count_vowels`, `unique_sorted`, `is_palindrome`, `second_largest`, `chunk_list`, `invert_dict`, `fizz_list`. Specs do not mention the K2 ranking convention. `solution_realization` is `"none"`. These tasks do not share a solution base with K2.T1–T6 or K2.S1–K2.S4.

RETRIEVED EVIDENCE. The same 2026-09-22 section assigns UNREL the role of confound control. A positive delta there is a red flag (warm-up, formatting, or non-specific drift). It is excluded from evidence for the hypothesis.

INFERENCE. UNREL is topically separate from the K2 ranking templates. It is still inside the generator that the feature extractor, the pilot scope note, and the pre-registered success roles were written against. Absence of a strategy-menu grade is not the same thing as an uncontaminated family. A win on UNREL cannot be counted as transfer under the rule that was frozen before these tasks were a candidate for this mission.

### Surface signatures, recomputed this session

OBSERVATION. The feature functions in `features.py` were reimplemented in a stdlib-only calculation. The app package was not imported. For each K2 NEAR task the spec string is `_near_base("K2")` plus the write-line plus the task sentence. `EXPLICIT["K2"]` appends a priority list of pseudo-words (`k2_pri` joins `r["priority"]` with `" > "`). `pseudo_word` emits a CVCVC string from consonants `bdfgjklmnprstvwz` and vowels `aeiou`. An exhaustive check of all 102,400 such strings found zero occurrences of `dict`, `tuple`, `string`, or `text`. The priority appendix cannot change `input_shape` for K2 NEAR. UNREL specs contain no world text.

| Task | Signature | Closed signature rule | Closed task-id rule |
|---|---|---|---|
| K2.N1 | `1\|tuple` | DIRECT (observed tie, insertion order) | DIRECT (id is not K2.T2 or K2.T5) |
| K2.N2 | `1\|tuple` | DIRECT | DIRECT |
| K2.N3 | `1\|tuple` | DIRECT | DIRECT |
| K2.N4 | `1\|tuple` | DIRECT | DIRECT |
| K2.N5 | `2\|tuple` | DIRECT (K2.T6's signature) | DIRECT |
| K2.N6 | `1\|tuple` | DIRECT | DIRECT |
| U1 | `1\|other` | DIRECT (unobserved fallback) | DIRECT |
| U2 | `1\|string` | DIRECT (unobserved) | DIRECT |
| U3 | `1\|other` | DIRECT | DIRECT |
| U4 | `1\|tuple` | DIRECT (observed) | DIRECT |
| U5 | `1\|other` | DIRECT | DIRECT |
| U6 | `1\|string` | DIRECT | DIRECT |
| U7 | `1\|other` | DIRECT | DIRECT |
| U8 | `1\|string` | DIRECT | DIRECT |
| U9 | `1\|other` | DIRECT | DIRECT |
| U10 | `2\|other` | DIRECT (unobserved) | DIRECT |
| U11 | `1\|dict` | DIRECT (unobserved for this offline rule) | DIRECT |
| U12 | `1\|string` | DIRECT | DIRECT |

U4 matches `1|tuple` because its spec contains the word `tuple` ("list of `(character, count)` tuples"). U11 matches `dict` because `input_shape` checks `dict` before any other keyword and the spec says "Return the dict". U12 matches `string` because the spec says "as a string".

RETRIEVED EVIDENCE. The live arm-C checkpoints agree that the only stored signatures are `1|tuple` and `2|tuple`, and that greedy selection on those buckets is DIRECT:

- Lineage 0 `S1_C.json`: `1|tuple` DIRECT count 4 mean 0.5, WORKED_EXAMPLE count 1 mean 0.0; `2|tuple` DIRECT count 1 mean 1.0.
- Lineage 1: `1|tuple` DIRECT count 5 mean 0.6; `2|tuple` DIRECT count 1 mean 1.0.
- Lineage 2: same shape as lineage 1.

RETRIEVED EVIDENCE. The previous-outcome table published in the replay audit stores DIRECT as the greedy choice on `1|tuple|none`, `1|tuple|pass`, `1|tuple|fail`, and `2|tuple|none`. The one cell with two strategies (`1|tuple|fail`) has DIRECT mean 1.0 and WORKED_EXAMPLE mean 0.0. Empty rows in that same run returned DIRECT. STEPWISE has zero arm-C teaching attempts.

INFERENCE. On all 6 K2 NEAR tasks and all 12 UNREL tasks, each of the three closed rules emits DIRECT. Under matched seeds the decision-level delta versus always-DIRECT is 0 before any new grade. A nonzero score delta under unmatched seeds would be sampling noise. Running generation would spend local model calls to confirm an identity already fixed by the rules and the strings. That is a design defect of this contrast. It is a result about these rules on these strings. It is not a claim that no future rule could ever differ from DIRECT, and it is not a claim that the model cannot solve these tasks.

### The five questions, per candidate

K2 NEAR:

1. Separate from K2.T1–T6 and K2.S1–K2.S4? As ids, yes. As solution templates, no. The six bases are the T bases, permuted and renamed. S is a surface variant of the same ranking skill and has already been inspected under DIRECT.
2. Already influenced the selector, its design, or its success criteria? Yes. The generator, the feature extractor's own docstring, the pilot scope note, and the 2026-09-22 role assignment all predate this mission and name NEAR. The task-id rule's only non-DIRECT targets are K2.T2 and K2.T5, whose bases are K2.N3 and K2.N6.
3. Distinct enough for transfer rather than template memory? No. A pass on `order_entries` after a pass on `rank_all` is another wording of the same template.
4. Clean always-DIRECT comparison technically feasible? The comparison is defined, and its decision delta is identically 0. A comparison that cannot change a decision cannot show an improvement.
5. UNKNOWN. Strategy-menu pass rates on K2.N1–N6. Whether a different, not-yet-specified rule would differ from DIRECT. K1 and K3 NEAR were not signed in this pass and are not substituted as the evaluation family.

UNREL:

1. Separate from K2.T1–T6 and K2.S1–K2.S4? Topically, yes. The twelve functions are different problems. They were written in the same generator file as those templates.
2. Already influenced the selector, its design, or its success criteria? The success-role assignment has. Section 4 of the 2026-09-22 design already says a positive UNREL delta is a confound red flag, never evidence for the hypothesis. The feature extractor was written to read rendered spec text of this generator, including words that put U4 on `1|tuple` and U11 on `1|dict`. The closed task-id rule does not mention U1–U12. The closed signature rule's non-DIRECT behavior was fit on K2.T rates, and on these strings that fit emits DIRECT anyway.
3. Distinct enough for transfer rather than template memory? The tasks are distinct from the K2 ranking templates. The pre-registered role still forbids counting a win as transfer.
4. Clean always-DIRECT comparison technically feasible? Same identity result. Decision delta is 0 for every closed rule.
5. UNKNOWN. Strategy-menu pass rates on U1–U12. Whether the already-published accumulation-probe grades, which this pass did not open, would have suggested a different threshold. Those grades are a different arm set. Using them now would be peeking.

Neither candidate qualifies as an unseen family on which a closed learning-derived rule can be shown to beat always-DIRECT.

## 2. Frozen protocol

This protocol is frozen before any new grade. Its own stop rule is that the test is not run.

### Hypothesis

An information state produced by an earlier learning process, and frozen before the evaluation tasks are graded, changes at least one later strategy choice on a genuinely unseen task family and, on the task as the unit of analysis, raises the pass rate above always-DIRECT.

The hypothesis is unresolved in general. It is contradicted within tested conditions for the three closed rules on K2 NEAR and on UNREL, at the decision layer: the rules do not change the choice, so they cannot raise the pass rate by means of a different choice.

### Family

No family is accepted as the evaluation family. K2 NEAR and UNREL were the candidates inspected. The evidence in section 1 is the independence evidence, and it does not support independence for a transfer claim.

K1 and K3 are in the same generator. The pilot kind is K2 only. They are not silently substituted.

### Baseline

Always-DIRECT. Every evaluation task is also scored, or would be scored, under DIRECT with the same seed schedule the treatment uses. The baseline is a decision policy, not a refit.

### Treatment

Three frozen rules, each tested only as already published. They are not blended, and none is refit on NEAR, UNREL, K1, or K3.

1. Task-id rule. Choose STEPWISE on K2.T2 and on K2.T5. Choose DIRECT on every other task id. Information used: the task id and the Stage-1 select/validate split already published (repeats {0, 1} select, repeats {2, 3} validate). That information was available when the integrity audit closed. It does not become available again from new grades.
2. Signature rule. Index `arg_count_bucket|input_shape` with the published Stage-1 rates. Ties keep the earliest strategy in insertion order, which on both observed signatures is DIRECT. An unobserved signature returns DIRECT. Information used: the rendered signature and those published rates. No task-id, kind, or split label enters the key (`features.py`).
3. Previous-outcome rule. As run on 2026-10-19: greedy lookup on `(arg_count_bucket, input_shape, previous_outcome)` from arm-C teaching rows only. `previous_outcome` is the latest teaching attempt in that signature bucket, in `{none, pass, fail}`. Holdout outcomes do not fill the field. An empty row returns DIRECT. The published real-label table selects DIRECT on every populated key. Information used: that frozen table. It is not updated from evaluation-family grades. A choice that changed only after seeing the new family's own outcomes would be within-family learning, which is a different claim.

What these rules may not use: new pass/fail bits from the evaluation family, raw model text, error tails, expected outputs, the generator's `base` field, or a hand map from `K2.N3` to `K2.T2`.

### Scoring unit

The task is the primary unit. Repeats are averaged inside the task before any mean across tasks is taken. Repeated log rows, duplicate joins, and dependent evaluations are not extra observations. The integrity audit's independent holdout count is 36, not 48, because 12 rows were a second write of one seeded evaluation. That correction stands. The 2026-09-22 confirmatory design used the lineage as its cluster for a three-arm claim that was not run. This protocol's unit for the closed-rule contrast is the task, because that is the unit the closed 1/6 result already used, and because a lineage mean of an all-DIRECT policy is the same number as a task mean of that policy.

### Sample size

Planned evaluation size, if the identity result had not held: 6 K2 NEAR tasks and 12 UNREL tasks, one decision each, with a repeat count copied from the closed Stage-1 grid (4) only as a measurement of a changed decision. That copy is not a power analysis.

No sample-size justification is invented. The 2026-09-22 design, line 170 and item 3 of its closing list, states that no pilot data then existed from which to freeze a confirmatory lineage count. The pilot that later ran did not beat always-DIRECT. While every closed rule's decision equals DIRECT, extra tasks and extra repeats do not increase information about a rule effect. The contrast is too weak to support a generalization conclusion because the treatment never departs from the baseline. The defensible alternative is recorded in section 6. It is not executed.

### Primary outcome and success threshold

Chosen before any new grade:

- For each task, `decision_changed` is true only when the frozen rule names a strategy other than DIRECT.
- A task with `decision_changed` false contributes delta 0 and is not sent to a model for a rule-effect estimate.
- A task with `decision_changed` true is scored as the mean of its prespecified repeats under the chosen strategy, minus the mean of the same repeats under DIRECT, same seeds. A missing grade is excluded from that task's mean. It is not entered as 0. If either arm has no grade, the task delta is unscorable and stays unscorable.
- An untried strategy is UNKNOWN. It is not a failure.
- Evaluator infrastructure failure (timeout, connection error, harness crash) is excluded from the correctness mean and counted in a separate failure tally. It is not coded as FAIL.
- The primary statistic is the unweighted mean of task deltas over the prespecified task list. Tasks with unscorable deltas are reported and are not imputed.
- Success requires all of the following: at least one `decision_changed` true; the primary mean strictly greater than 0; every unscorable task listed; the family not used to fit the rule; the family's pre-registered role, where one exists, allowing a positive delta to count as transfer.
- Failure of the rule: `decision_changed` is true for at least one task, and the primary mean is less than or equal to 0, with no unscorable tasks.
- Inconclusive: `decision_changed` is true, and at least one changed task is unscorable, or the scored mean is positive while a pre-registered role forbids counting it as transfer.
- Design stop, which is the result of this audit: `decision_changed` is false for every closed rule on every candidate task. The success predicate's first clause is false. The test is not informative. It is not run.

The AP-0 draft thresholds (NEAR 18, UNREL 12, and the harm margins in the Stage-1 draft) are a draft for a different arm set. They are not this protocol's rule.

### Comparison method

Paired by task id and by `seed_for(replicate, task_id, sample)` as defined in `common.py` (`PR|{MASTER_SEED}|{replicate}|{task_id}|{sample}`, first 8 hex digits, mod 2^31−1, `MASTER_SEED` 20260927). Treatment and always-DIRECT share those seeds. Ties inside a rule stay on the rule's already published tie break. This protocol adds no new tie break. A task the rule does not mention is DIRECT, which is the published fallback, not a new choice.

### Controls

- The decision table in section 1 is the pre-grade record. A later grade cannot move a task from DIRECT to another strategy inside these three rules.
- No threshold in this document was computed from NEAR or UNREL outcomes. Those outcomes do not exist for the strategy menu, and the other-arm summaries were not read.
- Cherry-picking is closed by naming all 18 candidate tasks and all 3 closed rules. Dropping U4 because it lands on `1|tuple`, or keeping only K2.N3 and K2.N6 because their bases match the two STEPWISE templates, is a violation of this protocol.
- Previously inspected results that stay closed: the 1/6 on K2.T, the signature delta of 0, the replay's 4/12, and the K2.S1–S4 DIRECT holdout. They are not a second evaluation set.
- Leakage of the `base` field into the decision is a protocol violation.
- A new rule fit on these 18 tasks, and then scored on these 18 tasks, is not a prospective test.

### What a result would mean

- Within-family performance is the already published 1/6 on repeats of K2.T1–T6. That result stays inside those six templates.
- Transfer would be a frozen rule changing a choice, and beating always-DIRECT, on tasks whose solution templates and success role were not the fitting set. Neither candidate supplies that contrast.
- A persistent learning-loop improvement would be evidence from an earlier process changing a later learning decision, the changed decision beating the baseline, and the change surviving into a later decision that the first success did not itself grade. A jsonl row, a design audit, and an all-DIRECT policy do not establish that loop.

## 3. Leakage and independence

Supported within the records read:

- K2 NEAR shares solution bases with K2.T. The paraphrase is visible in `tasks_v2.py` without any grade file.
- K2.S1–S4 are the designed structural holdout and have already been read under DIRECT. They are not a blind family.
- The feature function's docstring cites this generator's spec construction. The extractor is not naive to the vocabulary that produces `tuple`, `dict`, and `string`.
- The 2026-09-22 design states the NEAR and UNREL interpretations before data. Reusing a positive delta on either split as transfer credit would reverse that pre-registration.
- Live `S1_C.json` files and the replay table already encode DIRECT as the greedy action on every key these candidates hit.
- The closed task-id rule can fire STEPWISE only on two ids that do not occur in either candidate list.

UNKNOWN, disclosed:

- The launcher of the second `cmd_run_holdout` write for arm C / S1_C. The integrity audit left it UNKNOWN. Shell history was not searched in this pass.
- Full text of every historical accumulation-probe grade on these splits. Not opened, on purpose.
- Whether any priority pseudo-word outside the CVCVC generator, if one were ever hand-edited into a world file, could contain `dict`. The generator as written cannot. Existing lineage `world.json` files were not printed in this pass. They do not affect UNREL. They cannot move K2 NEAR off `tuple` unless a stored priority token contains `dict`, which the generator's alphabet and pattern forbid. This pass did not hash those world files.

ASSUMPTION, stated as an assumption: matched seeds are the only contrast that attributes a score gap to the rule. An unmatched reroll is not evidence about the rule.

## 4. Resource and execution feasibility

OBSERVATION, this session, read-only:

- `hw.memsize` = 25769803776 (24 GiB).
- `memory_pressure`: pages free 51982 (page size 16384, about 812 MiB), pages purgeable 9751, pages purged 866710751, compressor pages used 407336, swapins 321142769, swapouts 509765276.
- An earlier check the same evening saw fewer free pages. Free pages are higher now. The purge and swap counters are still large. Memory pressure is not treated as resolved. Generation was not launched to test the machine.

RETRIEVED EVIDENCE. A future strategy-menu generation, if it were ever authorized for a different question, would be local calls to `qwen2.5-coder:7b` at temperature 0.2, `top_p` 1.0, `num_predict` 512, `num_ctx` 4096 (`common.py`). Cash cost of those local calls is $0. Memory cost is real. Exact call count and wall time for an informative experiment are UNKNOWN, because no informative treatment exists. The null contrast specified here requires 0 model calls.

The current pilot cannot emit NEAR or UNREL. `split_tasks()` drops them. Producing those files would require an edit under `app/experiments/persistent_routing/`, which is experiment code rather than an `EDIT_FORBIDDEN_TARGETS` module, and would still be a code change this mission does not authorize. The edit would not create a non-DIRECT decision.

Files a future authorized run of some other protocol would have to keep immutable:

- The three lineage directories under `memory/experiments/persistent_routing/`, including `S0_*.hash`, `S1_*.json`, task JSON, `world.json`, and the shared logs.
- `audits/2026-10-18_evidence_integrity_and_generalization.md`, `audits/2026-10-19_previous_outcome_replay.md`, `audits/2026-10-19_previous_outcome_replay_result.json`, `audits/2026-10-19_previous_outcome_replay.py`, the bottleneck audit and its JSON, and this design audit once hashed.
- `echo_principles.json`, `memory/genesis/genesis_hash.txt`, and every path in `EDIT_FORBIDDEN_TARGETS`.
- The two source files that were already dirty before this mission: `app/core/echo_model_orchestrator.py` and `app/core/river_deliberation.py`. They were not read, not diffed, and not modified.
- Source JSONL logs named by the integrity audit. Their mtimes were not rewritten.

`write_json_new` uses `open(path, "x")` and refuses to overwrite. `append_jsonl` appends. A later run pointed at the existing `PR_ROOT` could therefore append to shared logs even while refusing to replace task files. Any future run, under some later authorization, would need a new root. That run is not this protocol.

No production reader of these experimental logs was claimed or re-verified in this pass. The integrity audit's statement that production has no reader is cited, not re-established here.

## 5. Unresolved questions and risks

- Transfer to an unseen family remains UNKNOWN. This audit does not convert that unknown into a negative universal claim.
- No frozen rule currently on hand is prespecified to differ from DIRECT on a family that the 2026-09-22 design would allow to carry a transfer claim.
- K2.S remains a narrow-structural split that was already inspected under DIRECT only. STEPWISE and WORKED_EXAMPLE on K2.S2 and K2.S4 are still untried. Filling those two strategies would be a new generation on an already-inspected family. It is not proposed, and it would not be an unseen-family test.
- The task-id gain of 1/6 is fragile under leave-one-out in the integrity audit (leaving out K2.T2 or K2.T5 moves the mean). That fragility was not used to write a new pass rule.
- Sample size for a future non-null rule is UNKNOWN. Inventing n from the failed pilot would pretend the pilot estimated a gap it did not find.
- Memory pressure can still kill a long local generation. This pass did not measure a safe batch size.
- Launcher of the duplicate holdout write remains UNKNOWN.
- A later session could treat "ungenerated" as "clean" and run the null contrast anyway. Section 2's design-stop clause is the control against that.

## 6. Authorization required for a next step

This mission ends here. The next step, if any, is a human decision. Two acceptable decisions:

1. Accept the limit. The closed selector branch stays stopped. NEAR and UNREL are not generated for these three rules.
2. Authorize a different experiment whose treatment is written down before any new grade, and whose text shows at least one evaluation task on which the treatment names a strategy other than DIRECT, without refitting on that evaluation family and without using the generator's `base` field as a hidden key. No such treatment is proposed in this document. Designing one would be a new mission. Executing one is not authorized by this mission.

Not authorized by a decision to "try NEAR" or "try UNREL" alone: editing `split_tasks`, launching the shelved 12-family pilot, calling the model, spending money, retuning either failed selector, opening the v2 summaries to hunt for a threshold, or modifying production, the dirty orchestrator files, protected governance files, source logs, or frozen audits.

## 7. Recommendation

**No suitable test family established.**

K2 NEAR is a renamed paraphrase of K2.T plus a convention mismatch, and the 2026-09-22 design already withholds transfer credit from it. UNREL is topically separate and is pre-registered as a confound control. On both families the three closed learning-derived rules are extensionally always-DIRECT. A prospective comparison against always-DIRECT is defined, and it is uninformative by construction. The protocol above records that stop before any new grade exists.
