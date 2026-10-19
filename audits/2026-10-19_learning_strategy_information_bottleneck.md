# Learning-strategy information bottleneck

Date: 2026-10-19. Read-only. No production file was edited. No model was called. The previous-outcome selector stays closed.

## Stopping condition

The direction "a coarse routing signature can learn which of these three prompt strategies beats always-DIRECT" is falsified on the completed Stage-1 grid. With every strategy scored, the same held-out split, and the same tie rule, task identity gains 1/6 over always-DIRECT and the selector's own signature gains 0. Choosing the other tied strategy for the five-task pool also gains 0. No further test inside the authorized bounds is justified. This is a localization of where the comparative evidence stops being usable. It is not a live mechanism, and it is not Level 4.

## What stays closed

The previous-outcome replay failed its frozen success rule and is accepted.

| Item | Value |
|---|---|
| Result | `audits/2026-10-19_previous_outcome_replay_result.json` |
| sha256 | `9923d6c8806ef0092c9418835d8d441f62812145eac5103b8a380e7522d236bf` |
| Seed | `20261019` |
| `pass_rule_met` | false |
| `decisions_changed_from_DIRECT` | 0 |
| `always_direct` and `real_labels` | each passed 4, scored 12, unscorable 0 |
| `shuffled_labels` | passed 4, scored 9, unscorable 3 |
| `arm_B_holdout_all_DIRECT` | true |
| `teaching_updates_arm_C` | 18 |

Report: `audits/2026-10-19_previous_outcome_replay.md` (`07f42c98febe1f2832e5f92e12e4d0ea05398c8ea42f22d4ec45dec81ded3fb5`). Script: `audits/2026-10-19_previous_outcome_replay.py` (`fe74af45051883c541e72efeaa916dfba34dfefeb6d6a8719a696f0982ad1d7f`). Baseline left untouched: `audits/2026-10-19_recursive_learning_baseline.md` (`2c6915aa7f285d43a434fcf283b971863be2284589c31bd70e1df3734f4e86d4`). Its line that the replay had not been run is historically true at freeze time and was not rewritten.

The 12-family pilot stays shelved. This census does not retune the selector, add a feature, or wire a consumer.

## Question

How much usable comparative evidence already exists for DIRECT, STEPWISE, and WORKED_EXAMPLE, and which limitation removes a held-out gain: sparse experience, missing strategy coverage, the situation key, the outcome representation, evaluation quality, or something else?

These were competing hypotheses. The smallest discriminating analysis is an offline recount of records that already exist. It uses the Stage-1 split that was frozen before this census, not a new selector.

## Frozen rule

Copied from the Stage-1 analysis before this script's first output.

- Select repeats `{0, 1}`. Validate repeats `{2, 3}`.
- Baseline: always DIRECT.
- Tie: Python `max()` over `("DIRECT", "STEPWISE", "WORKED_EXAMPLE")`, so the earliest tied name wins.
- A group is comparable only when every strategy has a scored select rate and a scored validate rate.
- Delta = validate rate of the chosen strategy minus validate rate of DIRECT.
- Success: grade true, or the string `PASS`, and infra/timeout are not true.
- Failure: grade false, or the string `FAIL`, and infra/timeout are not true.
- Missing: a declared strategy with zero scored rows. Untested is neither success nor failure.
- Incomparable: infra, timeout, or any other grade.

Grains, all on the same rows:

1. Task id, worlds averaged. This is the integrity target. The published ceiling is 1/6.
2. Routing signature `arg_count_bucket|input_shape`. This is the new contrast.
3. `(task, world)`. Secondary.

The split, the tie, and the four buckets were not changed after the numbers were seen.

## Artifacts and commands

Census script, stdlib only, absolute paths, writes only `/tmp/bottleneck_census_result.json`:

`python3 /tmp/bottleneck_census.py`

Durable copies, hashed after the second run:

| Path | Bytes | sha256 |
|---|---:|---|
| `audits/2026-10-19_learning_strategy_information_bottleneck.py` | 19095 | `340739607cb5b7f0399f3524a49cbba3476668d4fff7e6ea3fc6a3f7dc7fe6bd` |
| `audits/2026-10-19_learning_strategy_information_bottleneck_result.json` | 41636 | `93fe2479f37fafa44057dfaa43dc66dab6cd8c790c0568867c3b6b5a37530ae2` |
| `audits/2026-10-19_learning_strategy_information_bottleneck_bool_only.json` | 41588 | `e3eef5e19bc9ec5353d713bb6a82a8df00e29386ed403fef0b49effe4adad227` |

The bool-only JSON is the first execution. A re-run of the current script will not reproduce it. Keep it. The corrected JSON is the second execution, after `PASS`/`FAIL` were accepted for the online log only.

This session's verification recount is separate from that script. It reads the Stage-1 log and the persistent-routing decision and outcome logs, prints counts, and writes nothing. Its results are in the corrections below. It was not folded back into the frozen script.

## Stage-1 factorial grid

Source: `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl`.

VERIFIED FACT. 216 rows. Expected grid `6 tasks × 3 worlds × 3 strategies × 4 repeats = 216`. This session's recount of `(task_id, world_index, strategy, repeat_index)` is 216 unique keys and 0 duplicates. Every `passed` value is a JSON bool. Infra true: 0. Timeout true: 0. Repeats present: 0, 1, 2, 3. Strategies present: DIRECT, STEPWISE, WORKED_EXAMPLE.

The saved field `stage1.unique_grid_keys` is `1`, and `duplicate_grid_keys` is `0`. Those two fields do not count the grid. In `stage1_report`, the grid-key list is built, then the loop `keys = sig_map.get(task, [])` reuses the name. The returned `len(set(keys))` is the length of the last task's signature list (`K2.T6` → `["2|tuple"]`). The script was not patched after this was seen. Use the 216-row recount above.

Row class, all 72 rows per strategy scored, 0 incomparable:

| Strategy | Success | Failure | Incomparable | Rate |
|---|---:|---:|---:|---:|
| DIRECT | 43 | 29 | 0 | 43/72 |
| STEPWISE | 44 | 28 | 0 | 44/72 |
| WORKED_EXAMPLE | 22 | 50 | 0 | 22/72 |

Situations `(task, world)`: 18. Situations with all three strategies scored: 18. Situations missing any strategy: 0. In-sample strict-separable count: 13/18. That 13/18 is descriptive. It is not the held-out result.

Flip rate, pairs of repeats on the same task, world, and strategy:

| Strategy | Disagreements | Pairs | Rate |
|---|---:|---:|---:|
| DIRECT | 13 | 108 | 0.12037037037037036 |
| STEPWISE | 44 | 108 | 0.4074074074074074 |
| WORKED_EXAMPLE | 34 | 108 | 0.3148148148148148 |

Stage-1 block of the corrected JSON is field-identical to the bool-only JSON on rows, the (mislabeled) unique/duplicate fields, row class, the strict-separable count, flip rates, and the three grain summaries excluding decision lists. The `PASS`/`FAIL` mapping did not move Stage-1.

### Held-out task grain

6/6 comparable. Choices changed from DIRECT: 2. Both changed groups beat DIRECT on the validate half. Losses: 0. Ties among changes: 0. `mean_delta_vs_direct` = 0.16666666666666666 = 1/6. `mean_delta_on_changed_only` = 0.5. Integrity target met.

| Task | Chosen | Delta vs DIRECT | Select D / S / W | Validate D / S / W |
|---|---|---:|---|---|
| K2.T1 | DIRECT | 0 | 1 / 5/6 / 1/2 | 5/6 / 1/6 / 1/2 |
| K2.T2 | STEPWISE | 2/3 | 0 / 2/3 / 0 | 0 / 2/3 / 0 |
| K2.T3 | DIRECT | 0 | 1 / 1/2 / 2/3 | 5/6 / 1/2 / 1/6 |
| K2.T4 | DIRECT | 0 | 1 / 2/3 / 1/2 | 5/6 / 5/6 / 1 |
| K2.T5 | STEPWISE | 1/3 | 0 / 1/3 / 0 | 0 / 1/3 / 0 |
| K2.T6 | DIRECT | 0 | 1 / 1 / 0 | 2/3 / 5/6 / 1/3 |

K2.T4's validate half prefers WORKED_EXAMPLE. The select half does not, so the delta versus DIRECT stays 0. K2.T6 ties DIRECT with STEPWISE on the select half. Earliest-wins keeps DIRECT and leaves STEPWISE's validate edge unused. That happens at task grain. It is not a signature-pooling result. The tie was not retuned.

### Held-out signature grain

Routing key, computed by the census from `task["sig"]` and `task["spec"]`: K2.T1–T5 are `1|tuple`. K2.T6 is `2|tuple`.

2/2 comparable. Choices changed from DIRECT: 0. `mean_delta_vs_direct` = 0.0. `mean_delta_on_changed_only` = null.

| Signature | Tasks pooled | Select D / S / W | Validate D / S / W | Chosen | Delta |
|---|---|---|---|---|---:|
| `1\|tuple` | T1–T5 | 0.6 / 0.6 / 1/3 | 0.5 / 0.5 / 1/3 | DIRECT | 0 |
| `2\|tuple` | T6 alone | 1 / 1 / 0 | 2/3 / 5/6 / 1/3 | DIRECT | 0 |

On `1|tuple`, DIRECT and STEPWISE tie on the select half and tie again on the validate half. The earliest-wins rule picks DIRECT. Assigning STEPWISE to the whole pool would also have delta 0, because the validate rates are equal. The task-level gain exists because T2 and T5 can be chosen separately from T1, T3, and T4. One strategy for the signature cannot express that.

`2|tuple` is the same row as task-grain T6, including the same unused validate edge.

Applied back onto the six tasks, the signature policy assigns every task DIRECT. The task-weighted held-out delta is 0. Averaging two signature groups is not what creates the zero.

### Held-out situation grain

Secondary. 18/18 comparable. Choices changed: 4. Validate beats DIRECT: 2. Validate ties DIRECT: 2. Validate loses: 0. `mean_delta_vs_direct` = 0.1111111111111111. Changed-only mean = 0.5.

Changes: `K2.T2|1` STEPWISE delta 1; `K2.T2|2` STEPWISE delta 0; `K2.T5|1` STEPWISE delta 0; `K2.T5|2` STEPWISE delta 1. The in-sample 13/18 count overstates how often a winner stays a winner on the validate half.

### Signature-word caveat, holdout tasks only

`input_shape` checks `dict`, then `tuple`, then `text` or `string`. This session read `memory/experiments/persistent_routing/lineage_0/holdout_tasks.json` and `prospective_tasks.json`.

- K2.S1 spec: `dict` at index 309, `tuple` at index 12. The key returns `1|dict` because `dict` is checked first. Signature stored: `1|dict`.
- K2.S3 signature is `def winner_from_text(text):`. Spec: `tuple` at index 12, `text` at 309, `string` at 356. The key returns `1|tuple` because `tuple` is checked before `text`.
- K2.S2 and K2.S4 are `1|tuple`. K2.T1–T5 have `tuple` in the spec and no `dict`. K2.T6 has two arguments and no `dict`.

OBSERVATION. The word-order rule adds coarseness on holdout tasks S1 and S3. It does not change the Stage-1 signature-grain delta. T1–T6 have no `dict` false positive, and T6's two-argument bucket is real. The key was not redesigned.

## Online persistent-routing log

Source: `memory/experiments/persistent_routing/log_E_experience.jsonl`, `log_D_decision.jsonl`, `log_O_outcome.jsonl`. This family is separate from Stage-1. Arm C did not load the Stage-1 matrix. Arm B is the no-update control. Do not pool B with C, and do not pool either pass rate with Stage-1.

### Encoding correction

First execution, bool-only `row_class`: all 36 experience rows incomparable, comparison cells 0. `oracle_outcome` is the string `PASS` (23) or `FAIL` (13). That zero is an encoding artifact. It is preserved in the bool-only JSON.

Second execution accepts only those two strings plus JSON bools. Any other non-bool stays incomparable. Strategy-name counts were already valid in the first run: DIRECT 35, WORKED_EXAMPLE 1, STEPWISE never used, n=36.

### Teaching cells after the remap

36 rows. Success 23, failure 13, incomparable 0. Comparison cells (two or more strategies scored): 1.

Arm C, 18 rows:

| Lineage | Signature | DIRECT | STEPWISE | WORKED_EXAMPLE | Comparable |
|---|---|---|---|---|---|
| 0_C | `1\|tuple` | 2 success, 2 failure | missing | 1 failure | yes |
| 0_C | `2\|tuple` | 1 success | missing | missing | no |
| 1_C | `1\|tuple` | 3 success, 2 failure | missing | missing | no |
| 1_C | `2\|tuple` | 1 success | missing | missing | no |
| 2_C | `1\|tuple` | 3 success, 2 failure | missing | missing | no |
| 2_C | `2\|tuple` | 1 success | missing | missing | no |

Arm C scored rows: DIRECT success 11, DIRECT failure 6, WORKED_EXAMPLE failure 1. STEPWISE is missing in all six arm-C cells.

Arm B is 18 DIRECT rows across the same six lineage-signature cells, 12 success and 6 failure, and 0 comparison cells. The closed replay already established that arm B does not update selector state.

### Holdouts

`log_O.oracle_pass_fail` is a real bool, so holdouts scored in both executions. The script joins decisions to outcomes on `(lineage_id, arm, holdout_task_id)` with a dict. Duplicate keys keep the last outcome.

Script, row-weighted, 48 decision rows and 48 outcome rows: executed success 16, failure 32, incomparable 0, missing 0. Strategy selected: DIRECT 48, STEPWISE 0, WORKED_EXAMPLE 0. Unexecuted on every row: STEPWISE and WORKED_EXAMPLE. Those are missing, not failures.

This session's unique-key recount, not in the JSON:

- 36 unique `(lineage_id, arm, holdout_task_id)` keys.
- 12 keys appear twice. The two grades agree on every duplicate. Disagreeing duplicates: 0.
- The 12 duplicates are K2.S1–S4 on lineages `0_C_S1_C`, `1_C_S1_C`, and `2_C_S1_C`. Arm C only.
- Unique by arm: B 4 success and 8 failure (12 keys). C 8 success and 16 failure (24 keys).
- The row-weighted 16/32 is B's 4/8 plus C's 8/16 plus a second copy of 4 success and 8 failure from the agreeing C duplicates.
- Unique-key strategy selected: DIRECT on all 36 keys.

Do not publish 16/48 as independent trials. Arm B's unique 4/12 matches the closed replay's always-DIRECT slice. It is not a new selector result. Arm C's 8/16 is the updated arm's holdout grade under a policy that still selected DIRECT every time. Why the C_S1_C rows were written twice is UNKNOWN. The grades agree, so the last-write join does not change the unique-key tally.

## Other recorded families

Counted so they are not silently omitted. They are not the three-strategy comparison.

G3, `memory/experiments/g3_micro_probe/g3_probe_results.jsonl`: 7 rows, `parse_failed` 0, `source_strategy` DIRECT 2, STEPWISE 3, WORKED_EXAMPLE 2. `g3_has_oracle_grade` false. These rows are not executed strategy outcomes.

Accumulation stage 0, `memory/experiments/accumulation_probe/stage0/results/primary/grades.jsonl`: 554 rows, 0 incomparable in every arm.

| Arm | Success | Failure |
|---|---:|---:|
| E | 15 | 39 |
| H | 91 | 21 |
| H2 | 45 | 9 |
| IC | 12 | 42 |
| MISMATCH | 0 | 54 |
| N | 15 | 73 |
| N2 | 0 | 54 |
| NEUTRAL | 21 | 63 |

These arms are not DIRECT, STEPWISE, and WORKED_EXAMPLE. The rates were already seen, so they cannot be a blinded discovery set. `memory/experiments/accumulation_probe` v2 summaries and FREEZE files were not opened. H is not declared a winner.

## Hypotheses

### Situation-key design

Evidence for. On the complete grid, task-grain selection recovers the published 1/6 and changes two holdout choices to STEPWISE, both of which beat DIRECT on the validate half. The same rows under `arg_count_bucket|input_shape` change 0 choices and gain 0. On `1|tuple` the pool is a select tie and a validate tie, so the other legal choice also gains 0. One strategy per signature cannot keep DIRECT on T1, T3, and T4 while taking STEPWISE on T2 and T5.

Evidence against treating every zero as pooling. `2|tuple` is a single task. Its zero is the frozen earliest-wins tie, and the same tie already leaves a validate edge unused at task grain.

INFERENCE. Situation-key pooling is sufficient to remove the only held-out gain this grid has, even with complete strategy coverage.

### Missing strategy coverage

Evidence for, online log only. STEPWISE has zero scored teaching rows. Five of six arm-C cells have only DIRECT. The one comparison cell adds a single WORKED_EXAMPLE failure. Every holdout decision left STEPWISE and WORKED_EXAMPLE unexecuted.

Evidence against it explaining the signature-grain zero. The factorial matrix has zero missing strategies, and that complete matrix under the same key already gains 0.

INFERENCE. Missing coverage is a real property of the online log. It is not required to explain the signature result.

### Sparse experience

Evidence for, online log. Arm C has 18 teaching rows. That is a thin sample, and it is not pooled with arm B.

Evidence against, factorial grid. 216 unique cells, 0 duplicates, every situation scored for every strategy. The complete matrix still ties under the signature.

INFERENCE. Sparsity is rejected for the grid and retained for the online log. Sparsity is not why the complete matrix gains 0 under this key.

### Outcome representation

Evidence for bools being enough to see the task-grain gain. The 1/6 ceiling is recovered from sandbox pass/fail with no diagnostic label. T4 and T6 show that the select half is not always the validate-best strategy.

Evidence against a failure-mode analysis in this session. The Stage-1 mining audit's sections on shape versus ordering errors were already read for the full population. A predictor fit now would be contaminated. It was not run.

INFERENCE. Bool grades are adequate for the contrast that was actually tested. Whether a richer label would beat bools is UNKNOWN, and this session cannot test it cleanly.

### Evaluation quality

Evidence for a noisy but real grade. Flip rates above are measured. Stage-1 has no infra and no timeout. The noise did not erase the task-grain 1/6.

Evidence against it causing the signature zero. The same grades produce 1/6 at task grain and 0 at signature grain.

OBSERVATION. The grade is a sandbox bool, not a separate human judge. That limits what "works best" means. It does not create the signature zero.

### No consumer in the running system

VERIFIED FACT this session. A search of `app/core/` and `run.py` for `strategy_characterization`, `log_stage1`, `persistent_routing`, and `log_E_experience` returned no matches. The offline contrast has no production reader. Wiring one would be a production change and was not done.

## Alternatives beyond strategy selection

Retrieval. The delivered baseline already records that the E5 lesson store reloaded and its application tied the control. That comparison was not re-run. It supplies no new gain to attribute to strategy choice.

Correction and feedback. The testable path would be a diagnostic label on the same grid. It is contaminated for this session, as stated above. No other correction log in the records just counted carries an oracle grade that separates the three prompt strategies.

Evaluation process. The bool-versus-string defect in the first census run was an analysis bug, corrected by the remap and checked by the unchanged Stage-1 block. It is not evidence that the sandbox evaluator is the bottleneck.

Generation of the missing online STEPWISE and WORKED_EXAMPLE calls would re-ask a question the complete factorial matrix already answers for this key: filling the coverage still gains 0 when the key pools T1–T5. Those calls were not generated.

## What this does not claim

- Level 4 is not demonstrated. Nothing in production used a measured strategy outcome to change a later strategy choice.
- The 1/6 is the already-published task-grain ceiling on these six templates. It is not transfer to a new family.
- Arm B's 4/12 and the row-weighted 16/48 are not new selector successes.
- Accumulation arm H is not a winning learning strategy.
- The base model is not declared a ceiling.
- `sham_state` from the closed replay was not reconstructed.

## Unresolved

1. Whether a chooser that is allowed to use task identity would transfer beyond these six templates. Answering that requires a new family and new authorization. The 12-family pilot stays shelved.
2. Why `log_D` and `log_O` contain two agreeing copies of the four `*_C_S1_C` holdout tasks. Counted, not explained.
3. Whether failure-mode labels would beat bools. Not testable in this session without contamination.
4. Whether any unread v2 summary was frozen before the stage-0 rates were known. Not opened. A later session can pre-register against it only if it does not use the stage-0 grades already printed here as the outcome.
5. The offline gain has no live consumer. Connecting one is outside this authorization.
6. The S1/S3 word-order behavior is measured. Its effect on holdout grades was not measured, because that would require generation.

## Next justified action

None inside the authorized bounds. Do not build a new key, start the pilot, generate the missing online calls, open the v2 summaries to mine them, or edit production. Preserve the three census artifacts and this report.
