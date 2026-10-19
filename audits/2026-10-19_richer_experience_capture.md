# Richer Experience Record: Capture and Prospective Test

Date: 2026-10-19. Clock at verification: 2026-10-19 07:56:29 PDT.
Mission: one isolated capture of the discarded outcome tails, then one prospective test of one tail-conditioned rule against always-DIRECT.
The strategy-routing branch stays closed. This run does not reopen it, retune the closed selector, or start Stage 2.

Evidence labels: OBSERVED, VERIFIED, SUPPORTED, INFERRED, UNKNOWN, DISPROVEN.

## 1. Question, split, and boundary

Question: on a held-out portion that is not a repeat of the templates used to form the rule, does one deterministic rule that may read `output_tail` and `error_tail` change any task outcome relative to always-DIRECT?

Precommitted split, fixed before the held-out tails were inspected:

- Formation templates: K2.T1, K2.T3, K2.T4. These are the three Stage-1 templates whose published select-versus-validate delta was 0. K2.T2 and K2.T5 were kept out of formation so the rule could not memorize the two known STEPWISE template wins.
- Held-out templates: K2.T2, K2.T5, K2.T6. Different task ids from the formation set. This is a within-grid holdout of the six K2 T templates.
- Exclusion sensitivity: drop K2.T2 and K2.T5 and score K2.T6 alone.
- The rule may read tails of formation rows only. It does not read a held-out row's tail before choosing a strategy.

What would count as a measurable improvement: at least one held-out task whose pass count under the rule's chosen strategy is higher than that task's DIRECT pass count, with the unit being the task.

What this run does not settle: unseen-family transfer on the S, NEAR, or UNREL splits. Those grades are not stored in a form that can be scored from existing artifacts without a new model call. Transfer on those families remains UNKNOWN.

Authorized writes: one new root, `memory/experiments/richer_experience_20261019/`, and this audit. No production module, no governance file, no RiverBrain path, no memory-consolidation path, no edit to `app/experiments/persistent_routing/selector.py`, and no edit to `app/core/echo_model_orchestrator.py` or `app/core/river_deliberation.py`.

## 2. Capture method

The Stage-1 grid is already complete: `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl`, 216 rows, the six templates K2.T1–T6, three worlds, three strategies, four repeats. VERIFIED by recount this session (216 rows, those six task ids).

`cmd_stage1()` in `app/experiments/strategy_characterization/harness.py` generates a new model response through `OC2.chat` and then grades it. Re-invoking it would either no-op on completed keys or call the model. New model outputs are outside this authorization. A fresh sandbox re-grade was also not run: `oracle_runner.grade()` puts a fresh evaluator nonce into `output_tail`, so a re-grade would replace the stored tail rather than record it.

The capture transcribes the 216 stored rows through an isolated logger. Each row's `output_tail` and `error_tail` are copied as already stored. `feature_signature` is computed by loading `stage1/world_{0,1,2}.json`, calling `tasks_v2.build_tasks_v2`, and calling `persistent_routing.features.feature_signature` on the rendered signature and spec. `persistent_routing.provenance` was not imported. That module's `log_experience()` appends to the closed log.

Files written inside the new root:

- `logger.py` — isolated `log_experience()`
- `capture_and_compare.py` — transcription plus the frozen comparison
- `log_E_experience_rich.jsonl` — the richer experience file
- `comparison_result.json` — fit and scored delta
- `__pycache__/` — bytecode from the local run

The richer file was written at 2026-10-19 07:56:08 PDT. SHA-256 `547f17b3da8aecfa2b0e1dbeeba36db23990cf9f0dc0e6181e7e60e33aa7f7be`, 76,571 bytes, 216 rows. A directory scan of `memory/experiments/**/log_E_experience*.jsonl` found exactly two files: this new log, and the closed log named below.

## 3. Production artifacts unchanged

Hashes were recorded before the capture and again after it. All six matched. VERIFIED.

| Artifact | SHA-256 | Bytes | mtime (PDT) |
|---|---|---|---|
| `memory/experiments/persistent_routing/log_E_experience.jsonl` | `4f5bb2377035a3ce94a1c21df6aa83e7f000e45a44e32eb296b01fa4968f0241` | 5486 | 2026-09-27 11:22:33 |
| `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl` | `7f9d9533cc05add8171eae632f3c9be7678233c2424ef7810858a64e1b4f826a` | 165572 | unchanged from the pre-capture record |
| `app/experiments/persistent_routing/selector.py` | `71f6f04fa522c78c49ea8eddeb67373335d8f6ea6b574c29220f0379fe0c6127` | 5149 | 2026-09-27, pre-capture mtime 1790510174 |
| `app/experiments/persistent_routing/provenance.py` | `aa672f01c0709514ad0bc1f572323a5f7929e5b29ba41fbd299a05da4a8f94da` | 2828 | pre-capture mtime 1790510188 |
| `app/core/echo_model_orchestrator.py` | `6dcc8b90a33008e889821f1e41058cd6291fca754ee6418fb30444a0e99b0720` | 90538 | 2026-10-18 12:14:30 |
| `app/core/river_deliberation.py` | `c7d68f6e09458007f230bb00138738c1115a70fc919aab1fb3717220724370cc` | 81478 | 2026-10-18 12:20:04 |

The closed experience log remains the six-field file. It was not appended.

## 4. Schema of the richer rows

Path: `memory/experiments/richer_experience_20261019/log_E_experience_rich.jsonl`.

Every one of the 216 rows has these fields. VERIFIED by a full-file key check.

| Field | Content |
|---|---|
| `lineage_id` | `"stage1_grid"` on all 216 rows |
| `task_id` | `K2.T1` through `K2.T6`, 36 rows each |
| `feature_signature` | two-string list from the real `feature_signature()` call |
| `strategy_used` | `DIRECT`, `STEPWISE`, or `WORKED_EXAMPLE`, 72 rows each |
| `oracle_outcome` | `"PASS"` (109) or `"FAIL"` (107), copied from the stored `passed` boolean |
| `timestamp` | capture-time Unix float. Stage-1 rows have no original timestamp |
| `output_tail` | stored stdout tail. String on all 216 rows. Max length 300. Empty on 1 row |
| `error_tail` | stored exception tail, or `""` when there is none. String on all 216 rows. Empty on 215 rows. Nonempty on 1 row. Max length 300 |

Extra fields, present on every row and not required by the minimum contract: `world_index`, `repeat_index`, `seed`.

Computed signatures, identical across the three saved worlds. VERIFIED:

- K2.T1, K2.T2, K2.T3, K2.T4, K2.T5 → `["1", "tuple"]`
- K2.T6 → `["2", "tuple"]`

PASS/FAIL counts match the stored Stage-1 recount (109 / 107). The single nonempty `error_tail` and the single empty `output_tail` are the same row. That preserves the already-known Stage-1 shape (one nonempty `error_tail` in 216 rows).

## 5. The learning rule

Rule id: `tail_nameerror_v1`. Source: `memory/experiments/richer_experience_20261019/capture_and_compare.py`, function `fit_tail_nameerror_v1`. The function receives formation rows only.

1. Recognized exception names, in this order: NameError, TypeError, SyntaxError, IndentationError, AttributeError, KeyError, IndexError, ValueError, ZeroDivisionError.
2. Scan formation rows whose `oracle_outcome` is `FAIL` and whose `error_tail` is nonempty. Count how often each recognized name occurs as a substring.
3. If every count is zero, the decision is DIRECT. Reason code: `no_recognized_exception_on_a_formation_fail`.
4. Otherwise select the name with the highest fail count. Ties break by the order in step 1.
5. Among formation rows whose `error_tail` contains that name, choose the strategy with the highest pass rate. Strategies with no such rows are skipped. Pass-rate ties break DIRECT, then STEPWISE, then WORKED_EXAMPLE.
6. Apply that one strategy to every held-out task. Do not read the held-out task's `output_tail` or `error_tail`.

`output_tail` is recorded on every row. This rule does not branch on its text. The authorized example was an exception pattern in `error_tail`. The formation failures are wrong-answer lines inside `output_tail`, and those lines carry task-specific inputs. Conditioning on that text would memorize a template. That branch was not added.

Fit result on the 108 formation rows (K2.T1, K2.T3, K2.T4). VERIFIED by the comparison script and by a second count of the written log:

- nonempty `error_tail`: 0
- every recognized-name count: 0
- selected exception: none
- decision: DIRECT
- reason: `no_recognized_exception_on_a_formation_fail`

The pass-rate clause in step 5 did not run. An incidental recount of formation pass rates, which the rule did not use, is DIRECT 11/12 on each of T1, T3, and T4, ahead of STEPWISE (6/12, 6/12, 9/12) and WORKED_EXAMPLE (6/12, 5/12, 9/12).

## 6. Prospective comparison

Always-DIRECT and `tail_nameerror_v1` selected the same strategy on every held-out task. The outcome rows are therefore the same rows. Unit is the task. Each cell is 12 graded Stage-1 rows (3 worlds × 4 repeats) for that task and strategy.

| Task | Rule strategy | Rule passes | DIRECT passes | Delta |
|---|---|---|---|---|
| K2.T2 | DIRECT | 0/12 | 0/12 | unchanged |
| K2.T5 | DIRECT | 0/12 | 0/12 | unchanged |
| K2.T6 | DIRECT | 10/12 | 10/12 | unchanged |

All three held-out tasks:

- tasks improved: 0
- tasks degraded: 0
- tasks unchanged: 3

After excluding the two known STEPWISE templates, K2.T2 and K2.T5:

- tasks improved: 0
- tasks degraded: 0
- tasks unchanged: 1 (K2.T6, 10/12 against 10/12)

No gain was present on the three-task holdout, so none remains after the exclusion. The two STEPWISE template wins were not used as evidence of transfer, and this rule did not select STEPWISE.

A measurable improvement on the held-out portion was not observed.

## 7. One tail the rule did not see

After the comparison was written, an integrity scan of the richer file found the single nonempty `error_tail`. It is on held-out K2.T5, strategy WORKED_EXAMPLE, outcome FAIL, world 2, repeat 1, length 300. The only recognized name in that tail is SyntaxError. The same row is the one empty `output_tail`. VERIFIED by a name-list scan. The tail text is not quoted here.

That row was not an input to `fit_tail_nameerror_v1`. Using it to prefer a different strategy on K2.T5 would read the test portion. The scored delta above does not use it.

## 8. What stays closed

The closed selector, its experience log, and the two previously dirty source files are byte-identical to the pre-capture hashes. The rule was not copied into production. No further experiment was run.

Unseen-family transfer remains UNKNOWN. This holdout repeats the same six-template grid under a different train/test cut of those templates. It is not an S-split, NEAR, or UNREL result.

A null result is the outcome of the authorized test.
