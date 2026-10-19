# Evidence integrity and generalization

Local clock at the file check: 2026-10-18 21:10:24 PDT.
UTC at that same instant: 2026-10-19 04:10:24.
This report is dated with the local calendar day. The earlier baseline, replay, and bottleneck artifacts stay under their 2026-10-19 names.

Status of the governing question: unresolved. A useful learning-to-learn mechanism has not been demonstrated. This pass closes the evidence-integrity question for the records named below and finds that a valid unseen-family test cannot be run from the artifacts that already exist.

No selector was built. No frozen success rule was changed. No source log was edited.

## 1. Questions and current status

Governing question, still open. Can FeralEcho use evidence about its own learning processes to improve a later learning choice, retain that improvement, and generalize it beyond the situations used to form the rule, at zero capital?

Question A, resolved for these files. What are the 12 duplicated holdout rows, why do they exist, and what do they change?

Question B, resolved within the tested records. What do the task-specific gain, the coarse-signature result, the online traces, and the previous-outcome replay each establish?

Phase 2, resolved as a negative inventory. No uncontaminated unseen task family with a scored three-strategy matrix remains.

Phase 3, recorded and not executed. The candidates that existing evidence can support do not have a zero-cost test that would change the next decision.

Phase 4, the investigation that was run is the read-only recount in `audits/2026-10-18_evidence_integrity_analysis.py`. No model call was made.

Closed and left closed:

- Previous-outcome selector. Frozen rule failed. Real labels 4/12, always-DIRECT 4/12, zero decisions changed. Seed `20261019`.
- Coarse situation signature `arg_count_bucket|input_shape` on the six Stage-1 templates. Held-out gain 0, zero choices changed.
- Shelved 12-family pilot. Not started.

Labels used below: OBSERVATION, RETRIEVED EVIDENCE, INFERENCE, ASSUMPTION, UNKNOWN. A finding is also marked preliminary, supported within tested conditions, contradicted within tested conditions, or unresolved.

## 2. Files examined

Read and hashed. These hashes match the values recorded when those artifacts were frozen. This pass did not rewrite them.

| Path | sha256 |
|---|---|
| `audits/2026-10-19_recursive_learning_baseline.md` | `2c6915aa7f285d43a434fcf283b971863be2284589c31bd70e1df3734f4e86d4` |
| `audits/2026-10-19_previous_outcome_replay.md` | `07f42c98febe1f2832e5f92e12e4d0ea05398c8ea42f22d4ec45dec81ded3fb5` |
| `audits/2026-10-19_previous_outcome_replay_result.json` | `9923d6c8806ef0092c9418835d8d441f62812145eac5103b8a380e7522d236bf` |
| `audits/2026-10-19_previous_outcome_replay.py` | `fe74af45051883c541e72efeaa916dfba34dfefeb6d6a8719a696f0982ad1d7f` |
| `audits/2026-10-19_learning_strategy_information_bottleneck.md` | `a0c4519268c1df50e70766687537860fadb9ff101da5786aef7f44fcb153875b` |
| `audits/2026-10-19_learning_strategy_information_bottleneck.py` | `340739607cb5b7f0399f3524a49cbba3476668d4fff7e6ea3fc6a3f7dc7fe6bd` |
| `audits/2026-10-19_learning_strategy_information_bottleneck_result.json` | `93fe2479f37fafa44057dfaa43dc66dab6cd8c790c0568867c3b6b5a37530ae2` |
| `audits/2026-10-19_learning_strategy_information_bottleneck_bool_only.json` | `e3eef5e19bc9ec5353d713bb6a82a8df00e29386ed403fef0b49effe4adad227` |

Source records, read only. mtimes unchanged (2026-09-27):

- `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl`
- `memory/experiments/persistent_routing/log_D_decision.jsonl`
- `memory/experiments/persistent_routing/log_O_outcome.jsonl`
- `memory/experiments/persistent_routing/log_execution.jsonl`
- `memory/experiments/persistent_routing/log_E_experience.jsonl`
- `memory/experiments/persistent_routing/log_U_update.jsonl`
- `memory/experiments/persistent_routing/lineage_{0,1,2}/holdout_result_{B_S1_B,C_S0_C,C_S1_C}.json`
- `memory/experiments/persistent_routing/lineage_{0,1,2}/{holdout_tasks,prospective_tasks,dev_tasks,world}.json`
- `memory/experiments/strategy_characterization/phase0/phase0_result.json` (identifiers only)

Code read to locate the writer. Not modified:

- `app/experiments/persistent_routing/harness.py` (`cmd_run_holdout`, lines 160–193; module comment lines 46–68)
- `app/experiments/persistent_routing/common.py` (`seed_for`, `write_json_new`)

Derived artifacts created by this pass:

- `audits/2026-10-18_evidence_integrity_analysis.py`
- `audits/2026-10-18_evidence_integrity_derived.json`

The census script's `main()` was not called. Its import was used only to recompute `grain_eval` and `stage1_report`. It did not rewrite `/tmp/bottleneck_census_result.json`.

## 3. Question A — the 12 duplicated holdout rows

### What was duplicated

OBSERVATION. `log_D_decision.jsonl`, `log_O_outcome.jsonl`, and `log_execution.jsonl` each contain 48 rows and 36 unique keys. The count histogram is `{1: 24, 2: 12}` in all three files. `log_E_experience.jsonl` has 36 rows and 36 unique keys. `log_U_update.jsonl` has 18 rows, six for each of `0_C`, `1_C`, and `2_C`.

The 12 doubled keys are exactly these, each present twice:

| Lineage id | Arm | Task | Decision lines | Decision times (local) | Grade |
|---|---|---|---|---|---|
| `0_C_S1_C` | C | K2.S1 | 5, 13 | 07:53:40 and 07:56:07 | true |
| `0_C_S1_C` | C | K2.S2 | 6, 14 | 07:53:51 and 07:56:28 | false |
| `0_C_S1_C` | C | K2.S3 | 7, 15 | 07:54:13 and 07:56:57 | false |
| `0_C_S1_C` | C | K2.S4 | 8, 16 | 07:54:29 and 07:57:12 | false |
| `1_C_S1_C` | C | K2.S1 | 21, 29 | 11:15:47 and 11:18:01 | true |
| `1_C_S1_C` | C | K2.S2 | 22, 30 | 11:16:01 and 11:18:11 | false |
| `1_C_S1_C` | C | K2.S3 | 23, 31 | 11:16:14 and 11:18:17 | true |
| `1_C_S1_C` | C | K2.S4 | 24, 32 | 11:16:29 and 11:18:39 | false |
| `2_C_S1_C` | C | K2.S1 | 37, 45 | 11:23:59 and 11:27:05 | false |
| `2_C_S1_C` | C | K2.S2 | 38, 46 | 11:24:15 and 11:27:14 | false |
| `2_C_S1_C` | C | K2.S3 | 39, 47 | 11:24:29 and 11:27:33 | true |
| `2_C_S1_C` | C | K2.S4 | 40, 48 | 11:25:25 and 11:27:47 | false |

Times are 2026-09-27 local. Outcome and execution line numbers match the decision line numbers. Outcome gaps are 123–185 seconds.

Shared fields on every copy: `strategy_selected` DIRECT, `selection_probability` 1.0, evaluator hash `f63e471a900bd4e9528f08bf68792e582ae55981bc8bbae740d42fa46448a8d4`, model `qwen2.5-coder:7b`, `infra` false, `timeout` false.

Seeds, from `seed_for("HOLDOUT", task_id, 0)`, which does not include the lineage number:

- K2.S1: `508453239`
- K2.S2: `1028023712`
- K2.S3: `1098223855`
- K2.S4: `1344574094`

State hashes. Both copies of a lineage share that lineage's hash. Lineage 0: `8f9812d79996b8f6bdd85948bcfe958febf9fae58dbc6186322bb3e329b65721`. Lineages 1 and 2: `b75efd22d7895da497fa0f9d7aaaf1b2f222c624e9d645012884e936a0fa6ee9`.

### Identical copies, repeated measurements, or a shared key only

OBSERVATION. For all 12 keys, the two decision bodies are equal once `timestamp` is removed. The two outcome bodies are equal once `timestamp` is removed. The two execution bodies are equal once `generation_time` is removed, including `candidate_code_hash`. Fields that differ: none. Disagreeing grades: 0.

INFERENCE. These are repeated measurements of one seeded evaluation, written as separate log events about two to three minutes apart. They are not two independent samples that happen to share a key, and they are not one JSON object appended twice (the timestamps differ). The second event reproduced the same candidate hash, the same grade, and the same seed.

### Why they were written, and at which stage

RETRIEVED EVIDENCE. `cmd_run_holdout` loops over the four holdout tasks and, for each task, appends `log_D`, generates, appends `log_execution`, and appends `log_O`. After the loop it calls `write_json_new`, which opens the result file with mode `"x"` and refuses to overwrite. The JSONL append is not idempotent. The result file is.

OBSERVATION. Each lineage directory contains exactly one `holdout_result_C_S1_C.json`. Its mtime equals the first pass's K2.S4 outcome time, and it is earlier than the second pass:

| Lineage | Result mtime | First-pass S4 outcome | Second-pass S4 outcome |
|---|---|---|---|
| 0 | 07:54:43 | 07:54:43 | 07:57:30 |
| 1 | 11:16:49 | 11:16:49 | 11:19:00 |
| 2 | 11:25:43 | 11:25:43 | 11:27:58 |

Both outcome copies match that saved row (`passed`, strategy DIRECT, and `state_hash`).

OBSERVATION. The unduplicated `S0_C` campaign sits between the two `S1_C` passes on every lineage:

- lineage 0: 07:55:01–07:55:43
- lineage 1: 11:16:57–11:17:32
- lineage 2: 11:25:50–11:26:38

INFERENCE. The pipeline stage is a second OS invocation of `run-holdout --lineage N --arm C --state S1_C` after the first invocation had already written `holdout_result_C_S1_C.json`. The second process logged all four tasks, called generation again, and then failed the exclusive create. The result file stayed the first pass's file. This order is the same on all three lineages, so it is a repeated procedure.

The same-source conclusion is supported by the evaluator hash: both copies record the sha256 of `harness.py` at write time, and those hashes match. A pre-fix and a post-fix binary would not share that hash.

RETRIEVED EVIDENCE, competing narrative that does not fit these rows. The comment at `harness.py` lines 46–68 says lineage 0's first pass, from before the seed fix, was discarded and re-collected. The rows above are both still in the log, share seeds, share code hashes, and share one evaluator hash. The discarded pre-fix pass is not this pair.

UNKNOWN. Which shell command or missing driver issued the second `S1_C` invocation. `harness.py` names `run_pilot.py`. That file is not in the tree. The smallest unread follow-up is a read of the operator shell history for `run-holdout` on 2026-09-27. It was not performed. It would name the launcher. It would not change the row classification above.

No stderr from the exclusive-create failure was retained. The FileExistsError is the behavior of `open(path, "x")` after a complete log loop. That specific exception text was not recovered from a log.

### What the duplication changed

Supported within tested conditions:

- Selection. Both copies select DIRECT at probability 1.0. No decision changes.
- Unique-key scoring. Grades agree, so a dict join that keeps the last row does not change the unique tally. The census already uses that join.
- The previous-outcome replay. Its holdout slice is arm B. Arm B keys appear once (`0_B_S1_B`, `1_B_S1_B`, `2_B_S1_B`, four tasks each). The replay's 4/12 is outside the duplicated set.
- Stage-1. Recounted below. Zero duplicate grid keys. The duplication is a different log.
- Teaching experience. 36 unique rows. The duplication is not in `log_E`.

Presentation and uncertainty. A row-weighted reading of 48 outcome rows is 16 successes and 32 failures. The unique-key reading is 12 successes and 24 failures:

| Slice | Unique keys | Success | Failure | Copies in the log |
|---|---|---|---|---|
| B / S1_B | 12 | 4 | 8 | 1 |
| C / S1_C | 12 | 4 | 8 | 2 |
| C / S0_C | 12 | 4 | 8 | 1 |
| All unique keys | 36 | 12 | 24 | — |

The extra 4 successes and 8 failures in the row-weighted 16/48 are the second copy of C / S1_C. Arm C's unique holdout rate on the updated state is 4/12, the same unique rate as arm B and as C loaded from S0. Publishing 16/48 as independent trials overstates the sample. The source rows were left in place. The derived JSON is a separate file.

### Independent units

Stage-1 factorial grid:

| Level | Count | Note |
|---|---|---|
| Row | 216 | one scored cell |
| Unique `(task, world, strategy, repeat)` | 216 | duplicates 0 |
| Task | 6 | K2.T1–K2.T6. This is the frozen unit of the 1/6 mean |
| World | 3 | averaged inside each task rate |
| Strategy | 3 | DIRECT, STEPWISE, WORKED_EXAMPLE |
| Repeat | 4 | repeats {0, 1} select; {2, 3} validate |
| Task × world | 18 | secondary grain |
| Routing signature on this grid | 2 | `1\|tuple` (T1–T5), `2\|tuple` (T6) |

A task half is 6 rows: 3 worlds × 2 repeats. Those 6 rows are repeated measurements of one task. They are not 6 independent tasks.

Holdout routing logs:

| Level | Count |
|---|---|
| Log row (decision, outcome, or execution) | 48 |
| Unique `(lineage, arm, task)` evaluation | 36 |
| Of which scientifically duplicated | 12 keys, 2 writes each, one evaluation each |
| Lineage | 3 |
| Arm | 2 (B and C) |
| Holdout task | 4 (K2.S1–K2.S4) |
| Strategy actually selected | 1 (DIRECT). STEPWISE and WORKED_EXAMPLE are untried, which is UNKNOWN, not a failure |
| Experience row | 36, all unique |
| Online comparison cell with two strategies | 1 |

### Does the one-sixth gain survive a dependence-aware reading

Supported within tested conditions, as a point estimate on the frozen task unit. Recomputed by calling the frozen `grain_eval` on `log_stage1.jsonl`:

- Task grain: 6/6 groups comparable, 2 choices changed, both beat DIRECT, mean delta `1/6` (0.1666…). K2.T2 chooses STEPWISE, delta `2/3`. K2.T5 chooses STEPWISE, delta `1/3`. K2.T1, T3, T4, and T6 stay DIRECT, delta 0.
- Raw halves: K2.T2 STEPWISE 4/6 select and 4/6 validate, DIRECT 0/6 and 0/6. K2.T5 STEPWISE 2/6 and 2/6, DIRECT 0/6 and 0/6.
- Situation grain: 18/18 comparable, 4 choices changed, 2 beat DIRECT, 2 tie, mean delta `1/9`. The four changes are T2 worlds 1 and 2 and T5 worlds 1 and 2.
- Signature grain: 2/2 comparable, 0 choices changed, mean delta 0.

The holdout-log duplication does not enter this estimate. Stage-1 has no duplicate key to remove. The frozen rule already averages worlds and splits repeats into select and validate, so the published unit is the task (n = 6), not the row (n = 216) and not the situation (n = 18).

Descriptive leave-one-task-out, computed after the 1/6 was already known. This is not a new success rule:

| Left out | Mean of the other five | Choices changed in the other five |
|---|---|---|
| K2.T1, T3, T4, or T6 | 0.20 | 2 |
| K2.T5 | 0.1333… | 1 |
| K2.T2 | 0.0666… | 1 |

The whole mean is two tasks. Removing T2 leaves only T5's `1/3` spread over five tasks.

Contradicted within tested conditions as a transferable policy. The same rows, pooled by `arg_count_bucket|input_shape`, change 0 choices and gain 0. On `1|tuple` the select rates are DIRECT 0.6, STEPWISE 0.6, WORKED_EXAMPLE 1/3, and the validate rates are DIRECT 0.5, STEPWISE 0.5, WORKED_EXAMPLE 1/3. Insertion order keeps DIRECT. Choosing STEPWISE for that whole pool is also delta 0.

This gain is a held-out repeat of six known templates. It is not a result on an unseen task family.

## 4. Question B — what the evidence establishes

### Repeated observations of known tasks

OBSERVATION. Inside a Stage-1 cell, repeats 0–3 and worlds 0–2 are repeated measurements of K2.T1–T6. The in-sample strict-separable count from the bottleneck audit is a description of those repeats. It is not a held-out claim.

### Held-out repeats of known tasks

Supported within tested conditions. The frozen split uses repeats {0, 1} to choose and repeats {2, 3} to score, on the same six task ids. Task-grain mean delta versus always-DIRECT is 1/6. Signature-grain mean delta is 0. K2.T6's select half is a DIRECT/STEPWISE tie at 6/6; the tie rule keeps DIRECT, and STEPWISE's validate half is 5/6 against DIRECT's 4/6. That unused edge is part of the frozen tie. It was not retuned.

### Entirely unseen tasks or task families

Unresolved, and not supported by these records. K2.S1–S4 are the same kind as the six templates, already inspected, and scored only under DIRECT. Prospective task files list K2.T1–K2.T6 again. `phase0_result.json` names K2.T1 only. No filename under `persistent_routing/` or `strategy_characterization/` contains NEAR or UNREL. `dev_tasks.json` is an empty list on each lineage.

### Offline analysis versus behavior the running application consumes

RETRIEVED EVIDENCE. A search of `app/core/` and `run.py` for `persistent_routing`, `strategy_characterization`, `log_E_experience`, and `log_stage1` returns no matches. The census, the replay, and this recount are offline. Nothing in this pass shows the running server reading these logs and changing a later strategy.

### Recorded outcomes versus demonstrated learning

OBSERVATION. The logs record grades and, on arm C, selector updates (`log_U`, 18 rows). The holdout decisions that follow those updates are DIRECT on all 36 unique keys. Arm C's unique S1_C rate is 4/12, matching arm B. The previous-outcome replay changed 0 of 12 decisions. A stored update that does not change the later choice is a recorded statistic. It is not a demonstrated improvement in a later learning choice.

The Stage-1 1/6 is an offline counterfactual on a frozen split. It was not executed as a later choice by the application.

### Independent evidence versus correlated observations

The task-grain 1/6 and the situation-grain 1/9 are two summaries of one matrix. The four situation-level changes are the same two tasks. The online comparison cell is one WORKED_EXAMPLE failure beside DIRECT on a single arm-C cell. It is not a second replication of the 1/6. The replay's 4/12 is arm B's holdout and matches the unique B tally. It is not an independent confirmation of a new selector.

### `unique_grid_keys` and the PASS/FAIL correction

OBSERVATION, re-verified. `stage1_report` builds the 216-key grid and then, inside `for task in tasks`, assigns `keys = sig_map.get(task, [])`. The returned `unique_grid_keys` is `len(set(keys))` after that loop. The last sorted task is K2.T6, whose signature list is `["2|tuple"]`. `len` of that set is 1. The saved corrected JSON has `stage1.unique_grid_keys` 1 and `stage1.duplicate_grid_keys` 0. This run's recomputed grid is 216 unique and 0 duplicate, and `stage1_report`'s returned field is 1. The shadow matches the saved field.

The census script was not patched.

OBSERVATION, re-verified. Stage-1 `passed` values are JSON booleans (`passed_python_types` is `["bool"]`). The PASS/FAIL string path does not apply to them. On the online experience log, the bool-only artifact has `teaching_cells_with_two_or_more_strategies` 0 and `teaching_row_class_ignoring_strategy` incomparable 36. The corrected artifact has 1 comparison cell and success 23 / failure 13 / incomparable 0. Strategy name counts are DIRECT 35, WORKED_EXAMPLE 1, STEPWISE unused, in both artifacts.

These two defects do not move the Stage-1 task-grain 1/6 or the signature-grain 0 beyond the disclosure already in the bottleneck report. The bool-only run hid the one online comparison cell. The corrected JSON restored it. No conclusion in this report uses the saved `unique_grid_keys` value as a count.

## 5. Reconciled results

| Claim | Reading that respects the records | Status |
|---|---|---|
| Task-specific selection beats always-DIRECT by 1/6 on the six templates' held-out repeats | Unit is the task. Two of six tasks carry the mean. Worlds are averaged. | Supported within tested conditions |
| The coarse signature preserves that gain | Same rows, gain 0, zero choices changed | Contradicted within tested conditions |
| Previous-outcome replay beats always-DIRECT on arm B | 4/12 versus 4/12, zero decisions changed | Contradicted within tested conditions. Rule stays failed |
| Arm C's updated state beats arm B on the holdout | Unique rates are both 4/12, and every selected strategy is DIRECT | Contradicted within tested conditions |
| 16/48 is the holdout sample size | 36 unique evaluations; 12 of them were written twice with identical scientific fields | Contradicted as an independent count |
| The running application consumed either selector | No reader in `app/core/` or `run.py` | Unsupported |
| The result transfers to an unseen family | No such graded family is in the artifacts | Unresolved. Not claimed |

## 6. Competing hypotheses

### H1. A task-level bool selector is a real, transferable learning rule

Mechanism. On repeats {0, 1}, pick the strategy with the higher pass rate; on a later situation, that choice beats always-DIRECT.

Evidence for. On these six templates the held-out task-grain delta is 1/6, and both changed choices beat DIRECT on the validate half, in the same direction as the select half (T2 4/6 and 4/6; T5 2/6 and 2/6).

Competing explanation. The key is the task id. A new task id has no select-half rate. The coarse key that could have transferred gained 0. The gain is two tasks out of six.

Minimum test that would change the decision. A family that did not influence the rule, scored for all three strategies, compared with always-DIRECT, with the task as the unit.

Baseline. Always DIRECT.

Expected information gain from another cut of these 216 rows. Low. The split has been seen.

Likely failure mode. The rule cannot fire on a new id, or it fires through a coarser key and ties DIRECT.

Disposition. Not promoted. The frozen signature test already failed. Not reopened.

### H2. The second holdout write is an independent replication

Mechanism. Two grades on the same key are two trials.

Evidence against. All 12 pairs match on seed, state hash, strategy, probability, grade, evaluator hash, and candidate code hash. The result file's mtime matches the first pass.

Disposition. Contradicted within tested conditions.

### H3. The duplicate pair is the discarded pre-seed-fix pass plus the re-collection

Mechanism. The harness comment describes discarding lineage 0's first pass.

Evidence against. Both copies remain in the log, share the evaluator hash, and share code hashes. The pattern is on lineages 1 and 2 as well. The comment describes a pass that was removed.

Disposition. Competing narrative. It does not describe these rows. The launcher of the second invocation remains UNKNOWN.

### H4. Abstain when the signature evidence is tied or single-strategy

Mechanism. Keep DIRECT unless at least two strategies have scored select rates and one is strictly better. That would also have stayed DIRECT on `1|tuple`, because DIRECT and STEPWISE tie at 0.6.

Competing explanation. This is the coarse-key result restated. It does not recover the task-level 1/6, because that 1/6 requires the task id.

Minimum test. Same unseen-family test as H1. Not available without new graded outputs.

Baseline. Always DIRECT.

Expected information gain now. None. The existing signature grain already changed 0 choices.

Likely failure mode. Abstention reproduces always-DIRECT and cannot be distinguished from it.

Disposition. Not executed.

### H5. The task-level edge is repeat noise, so the system should refuse to switch

Mechanism. Strategy grades flip across repeats, so a switch is unearned.

Evidence for a limit. The mean moves from 1/6 to about 0.067 if T2 is left out. n = 6 tasks.

Evidence against calling the point estimate noise. On T2 and T5 the STEPWISE edge has the same sign on the select half and the validate half, and DIRECT is 0/6 on both halves.

Minimum additional test on this matrix. A new permutation of the same frozen split. That would be a new success rule after seeing the result. Not done.

Disposition. The fragility is recorded. The frozen 1/6 point estimate stands for this split. The direction is not reopened under a new threshold.

### H6. Learning when retrieval helps

Already tested. The earlier retrieval comparison tied its control. Not reopened. A stored retrieval count would not, by itself, show a more capable learner.

## 7. Is a valid unseen-family test possible

No, not from the existing artifacts, and not without generating new model outputs.

Inventory, identifiers only:

- Stage-1 grades: K2.T1–K2.T6, all three strategies, four repeats, three worlds. This is the set that produced the 1/6. It is no longer blind.
- Prospective files: the same six ids.
- Holdout grades: K2.S1–K2.S4, DIRECT only, already read by the replay and by this audit. STEPWISE and WORKED_EXAMPLE are untried.
- Phase 0: K2.T1 only.
- NEAR and UNREL splits: named in the harness comment as not generated. No matching filename.
- `dev_tasks.json`: empty.
- Other directories under `memory/experiments/` (`accumulation_probe`, `g3_micro_probe`, and the rest listed by a directory read) use other arm vocabularies. Stage-0 rates were already seen in the bottleneck pass. Their v2 summaries were not opened. They are not a blind three-strategy family, and using them now would be peeking.

An unseen-family rule was not frozen, because there is no evaluation family left that the selection rule, the signature, and the tie break have not already touched. Treating K2.S as that family would reuse an inspected set and would score missing strategies as if they were failures. That was not done.

## 8. Experiment performed

The only computation was deterministic and local.

Command:

```bash
python3 audits/2026-10-18_evidence_integrity_analysis.py
```

The first run raised `KeyError: 'online_routing_log'` and wrote nothing. The saved census uses `persistent_routing.teaching_cells_with_two_or_more_strategies` and `teaching_row_class_ignoring_strategy`. Those lookups were corrected. The comparison logic was not otherwise changed. The second run wrote the derived JSON and printed:

```text
stage1 216 unique 216 dup 0 shadow_matches True
task_mean 0.16666666666666666 changed 2
signature_mean 0.0 changed 0
holdout decision 48 unique 36 hist {1: 24, 2: 12} duplicate_joins 12
duplicates differing beyond time: decisions 0 outcomes 0 executions 0
```

Controls. The grains are the frozen census function: repeats {0, 1} select, {2, 3} validate, baseline always DIRECT, tie is `max` over `("DIRECT", "STEPWISE", "WORKED_EXAMPLE")`. Leave-one-task-out is descriptive and was not used as a pass rule.

Not executed:

- No retune of either failed selector.
- No new situation key.
- No 12-family pilot.
- No model call and no new generation.
- No edit to source JSONL, result files, or the frozen census script.
- No production wiring.
- No shell-history search for the missing launcher.

## 9. Commands and artifact paths

```bash
python3 audits/2026-10-18_evidence_integrity_analysis.py
shasum -a 256 audits/2026-10-18_evidence_integrity_analysis.py \
               audits/2026-10-18_evidence_integrity_derived.json \
               audits/2026-10-18_evidence_integrity_and_generalization.md
```

Derived JSON sha256, recorded before this markdown was written: `4d6e601f156ac75acff184e9eee4ca023b6994e88315e2af8c123c394ffb4dab`.

Analysis script sha256 at the same time: `ed3e59ca324497e8b915322f3353dc0e001e8814dbba2bd3ff4ea81f2179eaf4`.

The markdown hash is recorded in the session note after the file exists. Recomputing it changes nothing else.

## 10. Resources and production

Machine memory at 2026-10-18 21:06 PDT: 24 GB physical, `memory_pressure` pages free 8405, compressor pages about 408907, heavy historical swap I/O. The recount used the standard-library JSON parser on logs of a few tens of kilobytes. No model was loaded. No service was stopped or restarted.

This pass wrote three audit files under `audits/2026-10-18_evidence_integrity_*`. It did not modify `run.py`, `echo_principles.json`, the source JSONL, or the frozen 2026-10-19 artifacts. Their hashes and the JSONL mtimes (2026-09-27) were checked after the run.

`git status` shows pre-existing uncommitted edits to `app/core/echo_model_orchestrator.py` (mtime 2026-10-18 12:14:30) and `app/core/river_deliberation.py` (mtime 2026-10-18 12:20:04). Those mtimes are hours before this audit. This pass did not edit those files and did not inspect the diff. The tree was already dirty. Nothing was staged or committed.

## 11. Next justified action

Stop the selector branch. Both frozen selector rules have failed, the task-level 1/6 does not apply to a new task id, and no graded unseen family remains.

Do not retune the coarse key, add features, permute the six templates under a new success rule, start the 12-family pilot, or generate the missing STEPWISE and WORKED_EXAMPLE holdout calls.

The broader mission is blocked by an evidence limit, not solved. The single next action that could address transfer is a separately authorized generation on a family that has not been used to design the rule, with always-DIRECT as the baseline, untried strategies left UNKNOWN, the task as the unit, and the success rule written before any new grade is read. The harness comment already names NEAR/UNREL as the splits that were never generated. That generation is not authorized by this pass: it needs new model outputs, and the machine was under memory pressure.

Until that authorization exists, further analysis of K2.T1–T6 cannot answer the governing question.

## Hashes of the new files

Filled after the file was written, by the same session, without changing the body above this heading. The script and derived JSON hashes are in section 9. The markdown hash is printed by the verification command and stored with the session record of this file's existence.
