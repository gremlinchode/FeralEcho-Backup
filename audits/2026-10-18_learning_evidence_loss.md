# Learning-evidence loss investigation

**Date:** 2026-10-18
**Mode:** read-only source and artifact inspection. No model calls. No new experiment. No selector. No production edit.
**Question:** Where does outcome evidence become a coarse signature, a strategy name, and PASS/FAIL, and does any existing artifact show that a richer representation changed a later decision?

## 0. What would settle this

Three readings were open before the files were re-checked.

1. The richer grade is still stored beside the learner's inputs, and a later routing decision reads it.
2. The reduction is finished before the online record is written, and later routing decisions read only that coarse record.
3. A side store keeps the richer grade, and some later non-routing step consumes it, while the routing decision does not.

The reading that would change the conclusion below is a paired record already on disk: the same signature and strategy decided once from PASS/FAIL and once from a richer grade, with a different strategy chosen. That record is absent. The two held-out STEPWISE template results from the closed Stage-1 grid are outside this question. This report does not treat them as generalizable learning.

Scope is the closed strategy-routing path, plus the four named production paths: self-edit outcomes, RiverBrain scoring, memory consolidation, and Liveness Ledger checks. This report does not reopen the strategy-routing branch, does not retune it, and does not propose a replacement, a Stage 2 trigger, a diagnostic-channel router, or new model outputs.

Evidence labels: OBSERVED means a direct read of current source or of an on-disk record during this pass. SUPPORTED means a current source path whose live firing was not re-executed here. A prior audit is cited as a prior claim, then marked CONFIRMED only where this pass re-read the same functions or files.

## 1. The routing reduction

The richer grade is cut down in four successive functions. The first three still hold diagnostic text in memory or in the Stage-1 log. The fourth, the online learner's own write, keeps the coarse form only.

### 1.1 The grader already keeps a tail

`app/experiments/accumulation_probe/oracle_runner.py` `run_script()` (lines 22–39) returns the full stripped stdout and an error string already sliced to 1500 characters. `grade()` (lines 41–48) then builds the dict the rest of the pipeline sees:

- `passed` (bool)
- `ran_ok`
- `output_tail` = the last 300 characters of stdout
- `error_tail` = the last 300 characters of the error string
- `infra`, `timeout`, `duration`

The full sandbox stdout and the unsliced error exist only inside `run_script()`'s return value. `grade()` does not return them. **OBSERVED.**

### 1.2 The task is reduced to two buckets before any outcome exists

`app/experiments/persistent_routing/features.py`:

- `arg_count_bucket()` (lines 13–27) parses the rendered signature and returns `"1"`, `"2"`, or `"3+"`.
- `input_shape()` (lines 30–43) returns `"dict"`, `"tuple"`, `"string"`, or `"other"` from keyword presence in the rendered spec.
- `feature_signature()` (lines 46–50) returns that pair.

The selector indexes the string `f"{arg}|{shape}"` (`selector.py` `_key`, lines 23–25). Task id, world, spec text, and split label are not part of the key. **OBSERVED.**

### 1.3 The one function that turns a grade into a learner input

`app/experiments/persistent_routing/selector.py` `extract_sanitized_outcome()` (lines 105–112) returns `bool(grade_result["passed"])`. Its docstring names `output_tail`, `error_tail`, and `duration` as discarded. `Selector.update()` (lines 81–102) accepts only a plain bool. Any other type raises `TypeError`. The stored cell is `{count, mean}`, with the bool mapped to `1.0` or `0.0` and folded into an incremental mean that starts at `0.5`. `save()` (lines 45–55) writes that state dict and nothing else.

`select()` (lines 57–79), when `explore=False`, returns the strategy with the highest mean and the probability `1.0`. The cell's `count` is used as a presence filter (`count > 0`) and is then absent from the returned probability. **OBSERVED.**

### 1.4 The call that drops the grade, and the records that persist

`app/experiments/persistent_routing/harness.py` `cmd_run_arm()` (lines 142–154):

1. `sig = feature_signature(task["sig"], task["spec"])`
2. `strategy, prob = select(...)`
3. `grade, _hash = _run_one_decision(...)`
4. `outcome = extract_sanitized_outcome(grade)`
5. `PROV.log_experience(...)` then, on arm C, `update(sig, strategy, outcome)`

At line 149 the local `grade` dict still holds whatever `grade()` returned, including tails, for a sandbox grade. `_run_one_decision()` (lines 108–125) can also return a thinner dict: the exception path has `passed`, `ran_ok`, `infra`, `timeout`, and `error`, and the empty-code path has `passed`, `ran_ok`, `infra`, and `timeout`. Neither thin dict is written out. After `extract_sanitized_outcome()`, `log_experience()` serializes six fields (`provenance.py` lines 10–18):

| Field | Value |
|---|---|
| `lineage_id` | lineage and arm |
| `task_id` | task id |
| `feature_signature` | the two-bucket pair, as a list |
| `strategy_used` | strategy name |
| `oracle_outcome` | `"PASS"` or `"FAIL"` |
| `timestamp` | epoch seconds |

`log_update()` stores pre/post state hashes and a selector-source hash. It does not store the outcome. The holdout path (`cmd_run_holdout`, lines 176–192) writes `log_decision` (signature, strategy, selection probability, seed, state hash), `log_execution` (code hash and model name), and `log_outcome` (`oracle_pass_fail` bool, evaluator nonce hardcoded `"n/a"`, harness source hash, `infra`, `timeout`). The holdout result JSON stores `task_id`, `strategy`, `passed`, and `pass_rate`. **OBSERVED.**

### 1.5 What is still present at the moment of reduction

Two stores have to stay separate.

**Online path.** At `extract_sanitized_outcome(grade)` the tails, when the sandbox grade produced them, are in the unsaved local dict. They are absent from `log_E_experience.jsonl`, from the selector JSON, and from the holdout outcome record. Once the loop iteration ends, that local dict is gone. **OBSERVED** in source. **OBSERVED** on disk at 2026-10-18 22:31 PDT: `memory/experiments/persistent_routing/log_E_experience.jsonl` has 36 rows. Every row's keys are the six fields above. Outcomes are PASS 23 and FAIL 13. No row has `output_tail`, `error_tail`, `duration`, `raw_response`, or `code_hash`.

**Stage-1 path.** `app/experiments/strategy_characterization/harness.py` `cmd_stage1()` (lines 135–142) writes a different file, `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl`. Each row keeps `task_id`, `world_index`, `strategy`, `repeat_index`, `seed`, `passed`, `ran_ok`, `infra`, `timeout`, `code_hash`, `raw_response`, `output_tail`, and `error_tail`. The selector never reads this file. **OBSERVED** on disk the same minute: 216 rows, those 13 keys, `passed` true on 109 and false on 107. `output_tail` is nonempty on 215 rows and contains the substring `FAIL` on 91. `error_tail` is nonempty on 1 row. `Error` or `Traceback` appears in either tail on 5 rows. The diagnostic text that survives in this log is mostly the grader's `FAIL` line inside `output_tail`. The model text is in `raw_response`. The full sandbox stdout was already discarded inside `grade()`.

The mining audit (`audits/2026-09-27_strategy_characterization_stage1_forensic_mining.md`, section 11) already stated that `extract_sanitized_outcome()` keeps `passed` and that nothing downstream consumes the tails. This pass **CONFIRMS** that claim against current source and against the two logs. The mining audit used the tails as a description of the grid. That description is a human reading. It is not an update of `Selector.update()`.

The 2026-09-22 persistent-routing design, section 6, is the contract this code implements: `update()` receives the feature signature, the strategy, and an outcome in `{PASS, FAIL}`. The excluded list in that section includes `output_tail`, `error_tail`, duration, raw tests, raw candidate code, and expected values. The loss is located, and it is the contract the closed branch ran under.

## 2. Do later decisions consume anything richer than a score?

### 2.1 Strategy routing

The later routing choice is `Selector.select()`. It reads `count` and `mean`. On a holdout call it returns one strategy and the probability `1.0`. No existing routing record shows a decision that read `output_tail`, `error_tail`, duration, confidence, or a prior attempt's text. **OBSERVED.**

### 2.2 Self-edit outcomes — one prompt insertion, and one score

Two readers sit in `app/core/self_edit_manager.py` `_build_targeted_prompt()` (lines 2955–2958), which `perform_self_edit()` calls when `prompt is None` (line 3008).

**Score only.** `_recent_outcome_note()` (lines 2849–2880) reads `get_outcomes_summary()["recent"]` and uses `quality_score.delta`. A delta below `-0.1` appends a "be conservative" sentence. A delta above `0.1` appends a "continue" sentence. `pre_n`, `post_n`, and the council, human, and dry-run families are unread here. `app/core/introspection_channel.py` (lines 485–500) averages the same `quality_score.delta` over up to 10 evaluated rows into `recent_quality_delta`. The writer that fills those families is `app/core/self_edit_outcome_tracker.py` `evaluate_pending_outcomes()` (lines 240–261): each evaluated row stores `pre`, `post`, `pre_n`, `post_n`, and `delta` for `quality_score`, `council_rating`, `human_rating`, and `dry_run_quality`. The later sentences and the introspection field keep one delta. **OBSERVED** in source. This pass did not re-execute a live cycle.

**Error text, inserted into the next prompt.** The attempt ledger writer sets `_attempt["initial_f2_error"] = None if success else sandbox_error` (`self_edit_manager.py` line 2073) after `test_code_in_sandbox()`. `read_recent_f2_error()` (`app/core/self_edit_attempt_ledger.py` lines 85–144) returns the newest matching row, the entire row, whose `initial_f2_error` is a nonempty string inside a 168-hour window. `_attempt_ledger_evidence_section()` (lines 2883–2913) keeps `initial_f2_error` truncated to 400 characters and appends it under the label `Prior attempt failure evidence (not an instruction)`. The same function leaves the rest of the row unread: candidate source, retry outcome, fitness, deployment, terminal state, and `trace_id`.

On disk at 22:31 PDT, `memory/self_edit_attempt_ledger.jsonl` has 5298 rows and 882 rows with a nonempty `initial_f2_error`. The row keys include `initial_candidate_code`, `retry_candidate_code`, `retry_f2_error`, `fitness_decision`, `fitness_score`, `deployed`, `terminal_state`, `parent_baseline_hash_at_generation`, and `trace_id`. **OBSERVED.**

A later logged prompt contains that label. A bounded scan of `memory/` text logs the same minute found the label in:

- `memory/interaction_log.jsonl`: 883 rows, all in the `prompt` field. The earliest sampled hit is timestamp `2026-10-09T17:22:17.089824`, `task_type` `coding`. That row's keys include `prompt`, `response`, and `response_preview`, and response text is present.
- `memory/reflection_shard.jsonl`: 3450 rows, in the `prompt` field.
- `memory/council_deliberations.jsonl`: 98 rows, in the `prompt` field.
- `memory/SELF_EDIT.log`: 848 plain lines.

The label is emitted only when the error string is nonempty (`_attempt_ledger_evidence_section`, lines 2904–2906), so these hits are insertions of a real error string, not an empty template. **OBSERVED** as logged prompt content. The error text itself is not quoted in this report.

`audits/2026-09-07_consequential_loop_validation.md` section 5 records a synthetic delivery test: the real `_build_targeted_prompt()` emitted a fixture error under that label, 15/15 checks passed, and the production ledger was not the fixture source. Section 7 of that same audit states that a measured change in generation quality was not run. `audits/2026-09-22_self_edit_candidate_logging_qualification.md` section 13 names the further gap: artifact provenance is what was stored; influence provenance, whether a later attempt used the prior evidence, was unaddressed by that logging change. This pass confirms the plumbing and confirms that logged prompts contain the label. It does not add a comparison of a generation with the sentence against a generation without it. The subsequent prompt contains the error text. A changed generation choice is not demonstrated.

### 2.3 RiverBrain scoring

`app/core/council_rater.py` `rate_one_entry()` (lines 268–303) writes `council_rating` and `council_rationale_preview` (`reason[:120]`) into the council log, then calls `learn_from_council_rating(model_used, task_type, response_preview, score, quality_score)`. The rationale is not an argument of that call.

`RiverBrain.learn_from_council_rating()` (`app/core/echo_model_orchestrator.py` lines 1121–1164) blends the integer rating with `quality_score`, trains on features of `response_preview`, and updates `model_task_stats[model][task]` `count` and `mean`. The comment at lines 1149–1163 states that once the observation is inside `mean`, it is indistinguishable there from an auto-scored observation. `council_vetted_count` is a separate ratio counter. It is not a second mean.

`learn_from_sandbox_outcome()` (lines 1000–1049) builds a training string `code` on success, or `"[FAIL] " + error[:80]` on failure, extracts features, and persists `verified_count` and `verified_mean`. The appended verified-learning row stores those counts and means, `success`, and source. The docstring at lines 1009–1010 says the row carries counts and averages, not the code or the error text.

`score_model()` (lines 1180–1209) returns `mean`, or for verified task types the mean plus `_score_with_verified_nudge(heuristic, verified_count, verified_mean)`. It does not read rationale text or error text. `app/core/river_deliberation.py` `_select_council()` (lines 588–606) ranks models with `_boosted_score`, which calls `score_model()`. Observation count is also used there as a cold-start order (`observations_for`, lines 596–600). The ranking float is the score. **OBSERVED** in source. The orchestrator and deliberation files were read and not modified. This pass did not unpickle `river_brain.pkl` and did not call `score_model()`.

### 2.4 Memory retrieval and consolidation

`retrieve_relevant_memories()` (`app/core/memory_bridge.py` lines 410–474) returns `{text, score, meta}`. Two readers then drop different halves:

- `echo_ground_truth._build_memory()` (lines 560–601) keeps `user_conversation` text truncated to 120 characters, role, and a date-only timestamp. The similarity `score` is not rendered.
- `emergent_scheduler._prompt_recently_reflected()` (lines 342–354) uses `score > 0.85` and a timestamp inside 7200 seconds as a boolean skip. It does not pass the memory text into that boolean.

`autonomous_prune_journal()` (lines 483–548), called from `app/maintenance/consolidation.py` `run()` (lines 125–131), keeps a fraction of journal lines by facility-location selection on their embeddings, with a centroid-similarity fallback. The keep/drop choice uses embedding geometry of the journal line. It does not read a PASS/FAIL grade, an error string, a quality delta, or a provenance field from the strategy-routing logs. This pass did not run a prune, so no single live line is shown being kept because of a named outcome field. **OBSERVED** in source.

`audits/2026-07-23_memory_ablation_experiment.md` (Finding 76) reports that ablating retrieval was statistically indistinguishable from sampling noise on the prompts it ran (Mann-Whitney p=0.48). That prior result is cited, not re-run. Prompt insertion of memory text is in the current source. A decision change beyond sampling noise is the prior experiment's reported result, and this pass adds nothing to it.

### 2.5 Liveness Ledger text in prompts

`echo_ground_truth._build_capabilities()` (lines 623–648) reads `verified_capabilities.checks` and renders names whose `status` is `verified_live` or `verified_failing`, plus a stale flag. Per-check evidence strings are not in the rendered lines.

`_build_self_model_claims()` (lines 691–712) does append `evidence` truncated to 200 characters, together with a freshly resolved current fact and a matched/incorrect history note. That is one prompt surface that keeps a short evidence string. It is a claim-history renderer. It does not read strategy-routing grades. **OBSERVED** in source.

## 3. Provenance or uncertainty written, then read without it

| Write | What is stored | Later read | What the read uses |
|---|---|---|---|
| `Selector.update()` → state JSON | `count` and `mean` | `select(explore=False)` | highest `mean`; returned probability is `1.0` |
| `rate_one_entry()` → council log | rating, `council_rationale_preview` (120 chars), prompt hash, quality score | `learn_from_council_rating()` then `score_model()` | blended score inside `mean`; rationale absent from the call |
| `learn_from_council_rating()` | `council_vetted_count` beside `mean` | `_select_council()` via `score_model()` | the blended `mean` (and verified nudge on coding-family types) |
| `evaluate_pending_outcomes()` | four signal families, each with `pre_n` / `post_n` | `_recent_outcome_note()`, introspection `recent_quality_delta` | `quality_score.delta` |
| `read_recent_f2_error()` | the whole ledger row, including candidate source and `trace_id` | `_attempt_ledger_evidence_section()` | `initial_f2_error[:400]` |
| `retrieve_relevant_memories()` | `text`, similarity `score`, `meta` | `_build_memory()` | text preview, role, date |
| Liveness check dicts folded into `verified_capabilities.checks` | status plus whatever else the check dict carries | `_build_capabilities()` | check name and live/failing status |

`_build_self_model_claims()` is the row that still carries `evidence[:200]` into the prompt. The routing holdout probability does not carry `count`. **OBSERVED** in source.

## 4. Is there already a test that a richer representation would change a decision?

No uncontaminated artifact does that for strategy routing.

`log_stage1.jsonl` has the raw material for a description: `output_tail`, `error_tail`, `raw_response`, `code_hash`, `passed`, `strategy`, `task_id`, `world_index`, `repeat_index`, `seed`. The mining audit already described those tails. The bottleneck audit refused a predictor fit on that grid as contaminated. The treatment-design audit (`audits/2026-10-18_learning_derived_treatment_design.md`) concluded that no defensible learning-derived routing treatment is established from the closed rules, and that using the mined tails to build another router was outside that stop. Re-reading the same 216 rows would be another description of a grid that has already been mined. It would not be a prospective test.

The online experience log never stored the discarded grade next to the signature and strategy that `update()` consumed. A replay of those 36 rows can recover PASS/FAIL, the two-bucket signature, and the strategy name. It cannot recover the diagnostic tail, because the tail was never written.

The self-edit prompt hits show that error text can reach a later prompt. They are not a routing A/B. The 2026-09-07 validation already recorded that the generation-quality comparison for that insertion was not run.

**The single missing measurement**, named from that gap and not authorized by naming it: the diagnostic tail that `grade()` already returns (`output_tail`, which is where 91 of the 216 Stage-1 failures leave a `FAIL` line, and `error_tail` when the failure is an exception), written onto the experience row inside `log_experience()` at the moment `extract_sanitized_outcome()` runs, beside the `feature_signature` and `strategy_used` already in that row. The capture site is `app/experiments/persistent_routing/harness.py` `cmd_run_arm()`, between the grade return and `log_experience()`, in a new experiment root. The closed logs do not contain this field. This report does not add it, does not fit a rule on it, and does not treat the instruction to name it as permission to capture it.

## 5. Conclusion

The closed learner's online record is the coarse record by the time it is durable. Richer tails exist in process memory at `extract_sanitized_outcome()`, and they exist afterward in the separate Stage-1 log, which the selector does not read. Later routing choices read `count` and `mean`. One production prompt step, `_attempt_ledger_evidence_section()`, inserts a truncated sandbox error into a later self-edit prompt, and logged prompts contain that label. No artifact shows that insertion, or any richer routing field, changing a later strategy choice.

The current artifacts locate the reduction. They lack a paired, uncontaminated measurement of whether keeping the richer grade would change a decision. More evidence is required before any design change can be justified.

## 6. Strategy-routing branch

The strategy-routing branch was not reopened. No file under `app/experiments/persistent_routing/` was edited. No selector was constructed. No holdout was launched. No model was called. `app/core/echo_model_orchestrator.py` and `app/core/river_deliberation.py` were read and left unmodified. The recommendation of `audits/2026-10-18_learning_derived_treatment_design.md` stands: stop this research branch.

## 7. Integrity

- Clock at the filename check and the log recount: 2026-10-18 22:31:30 PDT.
- This path was absent before the write.
- On-disk counts in sections 1.5, 2.2, and 4 are from a stdlib read that printed keys, counts, and one timestamp. Response bodies, tails, and error strings were not printed.
- Investigation only. No independent implementation review applies. No follow-up experiment is authorized by this document.
