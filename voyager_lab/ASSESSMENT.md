# Project Voyager — assessment

Date of the official run: 2026-11-08.
Branch: `project-voyager` at `dc8d6eb9b6479ef323614cd6820bb050a14299eb`.
Worktree: `/Users/richietate/Desktop/FeralEcho-voyager`.
Rubric bundle: `b8b1bc1fe7056294739bd834c3e4329807b50ef6cdffab67f68f6e32e2af9b9d`.
The lock was written before either official arm. `freeze.py` still prints `FREEZE_OK` after the run.
The live Echo process was not signaled. Production code, production memory, and VSL were not modified.
This prototype is not authorized for production integration.

## 1. Architectural assessment

### Existing capabilities

FeralEcho already persists several kinds of state.

- `app/core/working_self.py` appends conversational ledger rows and replaces a summary atomically. That ledger is a record of turns. It has no task graph, no mission checkpoint, and no next action.
- `snapshot_manager.py` copies a fixed set of health and code artifacts. A snapshot is a restore point for those files. It is not an in-progress mission.
- `log_retention.py` rotates oversized logs.
- `autonomy_coordinator.py` decides whether a background cycle may start, and whether a cycle already in progress should yield. It does not remember an objective across a killed process.
- `echo_projects.py` generates a sandboxed multi-file project from a curiosity-garden question on a timer. A failed generation writes a report and stops. It does not resume a half-finished task list in a later process, and it does not carry a measured lesson into the next project.
- VSL is a kill-switched skill ledger. The runtime default remains off / shadow. This project does not read or write it.

A repository search for a mission-continuity store found no record with an objective, a task dependency list, a failure class, an evidence class, a resource stop, and a cross-mission lesson. The word `mission_id` elsewhere belongs to an unrelated protocol envelope.

### Missing capabilities

These were missing before this prototype, and they remain missing inside the live Echo process.

- A mission record that survives an actual process restart, with the fields in capability A.
- A planner that turns an objective into ordered, dependency-aware tasks and revises that plan when a step fails.
- A distinction among successful, partial, failed, unknown, and blocked execution, with an alternate action that is a different operation rather than a third identical call.
- A budget that stops a mission when the tool allowance is spent.
- An external check that scores the world, separate from the controller's own success string.
- A lesson store whose effect is measured against the same controller with lessons disabled.

Free-text interpretation by Echo-the-model is still missing. This prototype does not call `echo_query`. The planner is a deterministic grammar over six problem classes. Calling that grammar "Echo understood the objective" would be false.

### Proposed implementation

A standard-library package, `voyager_lab/voyager/`, in this worktree.

The parent process materializes a small filesystem world, writes a public brief, and launches `python -m voyager.worker` as a real child. Interrupt missions raise `ProcessInterrupt` (exit 75). The parent launches a second process, which loads the checkpoint. The parent records both process ids, because the baseline overwrites its record and would otherwise hide the first pid.

The external grader reads the world directory. A controller status of `success` is an unsupported claim when that file check fails.

Three arms, fixed before the run:

- `baseline`: one source, up to three identical reads, then a write. No checkpoint. A write attempt sets status `success` even when the write was blocked or the bytes are wrong.
- `engine`: the grammar, with lessons stored after an externally verified success.
- `ablation`: the same engine with the lesson store disabled. This arm was pre-registered so a higher engine score can be attributed to lessons only where the two arms differ.

### Dependencies

Python 3.13 from the host framework. No third-party packages. No network. No API key. No conda environment. `PYTHONPATH` must include `voyager_lab`.

### Risks

- A class that already has a template can look "unfamiliar" while the procedure was written by the programmer. M19 is that case.
- A same-class lesson keyed on the path map can replay a trace on new bytes. That helped M06 (the new sum is 9) and hurt M20 (the new join is `4-4`, and the grade required abstention). The rubric already required this difference to be recorded as leakage. It was recorded. The suite was not changed.
- Teaching a per-mission solution would have made the score meaningless. Procedures are class templates. The worker refuses a brief that contains `grade`, `world`, `success_check`, or `tags`.

### Expected measurable improvements, stated before the run and left unchanged

The engine was expected to resume after a kill, to recover M07–M10 by a different operation, to abstain on M12, M17, M21, and M22, and to make fewer unsupported success claims than the baseline. Lessons were expected to change tight-budget same-class missions (M14, M15, M16) and the programmed composition M25. M19 was expected to match across lesson arms. M20 was expected to differ, and that difference was pre-registered as leakage. M24 was expected to fail the engine, because the engine refuses a second identical failed read, while the baseline may pass by retrying. M24 stays inside the completion rate.

## 2. The prototype

`voyager/engine.py` is a deterministic controller. `voyager/procedures.py` holds the six templates: `copy_value`, `pipeline_sum`, `fold_lines`, `make_then_write`, `resolve_conflict`, `join_pair`. A lesson applies only when the problem class matches, plus the one composition `pipeline_sum__scale`, which inserts a local multiply before the stored sum's write.

Failure handling lives in the engine, not in a second copy of the template:

- `tool_unavailable` on `add` becomes a local integer sum, recorded as `INFERENCE`, and the add tool is not called again.
- `file_not_found` and a partial read try `alt_src` once.
- `missing_parent` creates the parent directory, then writes once.
- an `unknown` read stops as `unknown` and does not invent a value.
- a missing authority slot during a real conflict stops as `unknown`.
- `human_required` stops as `blocked`. A later process may write once after the parent plants `.human_token`.
- `io_error` stops as `failed`. The same `(op, args)` pair is not repeated.
- a second identical failed signature is refused. A later successful different operation can unlock one retry. A third identical failure is refused again.
- the tool budget is checked before every world call. Exhaustion stops as `blocked`.

Evidence classes written by the controller are `OBSERVATION`, `RETRIEVED`, `INFERENCE`, `ASSUMPTION`, and `UNKNOWN`.

## 3. Files created and modified

Created under `voyager_lab/`, all untracked. No file in the main FeralEcho checkout was edited.

Controllers and scoring, covered by the freeze:

- `voyager/__init__.py`
- `voyager/atomic.py`
- `voyager/baseline.py`
- `voyager/engine.py`
- `voyager/grader.py`
- `voyager/harness.py`
- `voyager/procedures.py`
- `voyager/rubric.py`
- `voyager/suite_spec.py`
- `voyager/worker.py`
- `voyager/world.py`

Not hashed, because they are the runner and the write-up:

- `self_check.py`
- `freeze.py`
- `run_experiment.py`
- `RUBRIC_FREEZE.json`
- `README.md`
- `ASSESSMENT.md`
- `results/` (the official raw run)

## 4. How the mission engine operates

For each mission the parent:

1. Writes `brief_given.json` with id, objective, problem class, budget, slots, and an optional hypothesis class.
2. Builds the world directory from the hidden spec. The child never receives that spec.
3. Starts `python -m voyager.worker`.
4. On exit 75, starts another worker against the same record and world, up to three processes.
5. For M18, snapshots the record and the file's absence before planting the human token, then starts the second process.
6. Grades the world. Stores a lesson only after an external pass, only for a class that has a template, and only on the engine arm. The stored trace is the template, not the probe plan. The first success for a class wins.

A fresh engine process with no record calls `build_plan`. A later process loads `record.json`. If `last_successful_checkpoint` is set, `resumed_from_checkpoint` becomes true on that later process. The checkpoint is the task list, the variables read so far, the evidence, and the failure signatures.

Parent-timed `elapsed_ms` is the scoreboard's time. The record's own `resources.elapsed_ms` stays 0 because the child does not time the parent's wait. `ru_maxrss` is the macOS bytes value from the child.

## 5. Installation and execution

See `README.md`. Short form:

```bash
cd /Users/richietate/Desktop/FeralEcho-voyager/voyager_lab
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 self_check.py
python3 freeze.py
```

The official command was:

```bash
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 run_experiment.py --run
```

It printed `OFFICIAL_RUN_DONE` once. A second invocation refuses.

`self_check.py` printed `SELF_CHECK_PASS` before the freeze was written. That check covers path escape, hidden-field rejection, M05 resume versus baseline, M12/M17/M18 abstention, M24's refusal to repeat, M07–M10 recovery, the tight-budget lesson pairs, and the M19/M20 leakage sequence.

## 6. Baseline results

OBSERVATION, from `results/summary.json` and `results/RESULTS.md`.

| metric | baseline |
| --- | ---: |
| completion | 2/25 = 0.08 |
| successful recovery (M07–M10) | 0/4 = 0.0 |
| unsupported completion claims | 23 |
| contradictions | 0 |
| repeated failed operations | 7 |
| tool calls | 62 |
| elapsed | 1423.844 ms |
| restart recovery (M05, M06, M23) | 0/3 = 0.0 |
| abstain when required (M12, M17, M21, M22) | 0/4 = 0.0 |
| unfamiliar (M19, M20) | 0/2 = 0.0 |

The two passes are M01 (copy `42`) and M24 (the third read of a flaky file returned `55`, `repeat_extras` = 1). Every other baseline mission set status `success` on a file that failed the external check. M05's second process claimed `done` after the nonce had already been consumed. Its checkpoint flag is false. The parent still recorded two pids, `[69289, 69293]`, exits `[75, 0]`.

## 7. Engine results

OBSERVATION.

| metric | engine (lessons on) | ablation (lessons off) |
| --- | ---: | ---: |
| completion | 23/25 = 0.92 | 20/25 = 0.80 |
| successful recovery | 4/4 = 1.0 | 4/4 = 1.0 |
| unsupported completion claims | 1 | 0 |
| contradictions | 0 | 0 |
| repeated failed operations | 0 | 0 |
| tool calls | 73 | 70 |
| elapsed | 1413.517 ms | 1410.571 ms |
| restart recovery | 3/3 = 1.0 | 3/3 = 1.0 |
| abstain when required | 4/4 = 1.0 | 4/4 = 1.0 |
| unfamiliar | 1/2 = 0.5 | 2/2 = 1.0 |

Engine misses are M20 and M24. M24 is the pre-registered policy miss and is inside the 0.92. Ablation misses are M14, M15, M16, M24, and M25. Ablation passes M20.

Lesson effect, same frozen rule:

| mission | engine | ablation | engine label | tools, engine / ablation |
| --- | --- | --- | --- | --- |
| M14 | pass, value `17` | blocked by budget | procedure_reuse | 4 / 4 |
| M15 | pass, value `5` | blocked by budget | remember | 4 / 4 |
| M16 | pass, value `15` | blocked by budget | procedure_reuse | 2 / 2 |
| M19 | pass, value `8-1` | pass, value `8-1` | none | 4 / 4 |
| M20 | fail, status `success`, value `4-4` | pass, status `blocked` | remember | 3 / 3 |
| M25 | pass, value `30` | status `unknown`, 0 tool calls | programmed_composition | 4 / 0 |

The only lesson flag with `flag` set is `leakage_completion` on M20. Tool counts on M19 and M20 match, so there is no `leakage_tool_calls` flag. M19 was not flagged.

Restart evidence for the engine on M05: claimed `8841`, `resumed_from_checkpoint` true, pids `[69328, 69330]`, exits `[75, 0]`. Those pids differ from each other and from the parent. M06 claimed `9`. M23 passed on the engine and on the ablation.

M07's record shows the recovery shape directly. The `add` call is in `failed_attempts` with code `tool_unavailable`. Evidence classes on that mission are `RETRIEVED` for the two inputs, `INFERENCE` for the local sum, and `OBSERVATION` for the write. The external file is `10`. `repeat_extras` is 0.

## 8. Failure and recovery analysis

OBSERVATION, grouped by the required scenario list.

1. Uninterrupted (M01–M04). Both engine arms pass all four. The baseline passes only M01. M02–M04 need a sum, a line fold, or a directory create. The baseline writes one source string and calls that success.
2. Interruption (M05, M06, M23). Both engine arms resume in a second process and pass. The baseline's second process starts over. On M05 the source is already gone, so the second baseline process assumes `done`.
3. Missing resources (M07, M08, M22, and M20's budget). M07 and M08 pass on both engine arms by an alternate. M22 stops `blocked` after the single allowed call, and the file is absent, so the abstain grade passes. M20 is the leakage case below.
4. Failed operations (M09, M10, M21, M24). M09 creates the missing parent and then writes. M10 discards the partial stub `4` and writes the alternate `48`. M21 stops `unknown` on an empty unknown read and does not write. M24's first read is an `io_error`. The engine records one failure and stops. The baseline reads until the file returns `55` and passes. `repeat_extras` is 1 on the baseline and 0 on the engine.
5. Conflicting evidence (M11, M12). M11 writes the authority value `9`. M12 has no authority slot. The engine stops `unknown` and leaves `answer.txt` absent. The baseline writes `4` and claims success.
6. Incorrect initial hypothesis (M13, M14). The hypothesis class is `copy_value` on a sum mission. With budget 8, M13 can afford the failed probe and still finish, on both engine arms. With budget 4, M14 finishes only when a same-class lesson removes that probe.
7. Human intervention (M17, M18). M17 stays `blocked` and does not write. M18's first process stops `blocked` with the file absent. The parent plants the token. The second process writes `ship`. The baseline claims success on the first process without the token, so the two-phase grade fails and the claim is unsupported.
8. Previously encountered problems (M15, M16). Described in section F.
9. Unfamiliar (M19, M20). M19 is the first `join_pair` in the suite. Both engine arms produce `8-1` from the library template. M20 uses the same path map (`a.txt`, `b.txt`, `join.txt`) with bytes `4` and `4`, and the grade is abstain. With an empty lesson store the probe plus two reads spend the budget of 3, the write never happens, and the abstain grade passes. After M19's lesson, the engine skips the probe, writes `4-4`, sets status `success`, and the external grade fails. That row is the engine's one unsupported completion claim. The written value is `4-4`, computed from these files. It is not a copy of M19's `8-1`.
10. Multiple dependent tasks (M02, M04, M06, M23). Both engine arms pass. The baseline does not.

Repeated identical failures: 7 on the baseline, 0 on each engine arm. The count comes from the world log, not from the controller's failure list.

Contradictions: 0 on every arm. The grader counts distinct evidence values in the fields `value` and `output`, and a claimed value that disagrees with those fields.

## 9. Known limitations

- The controller is a grammar. It receives `problem_class` in the brief. It does not read the objective sentence and decide what the mission is. That interpretation is unimplemented.
- `remember` in the frozen rubric means the path map equals the stored example. M06 and M15 both receive that label. M15's files are `2` and `3`, and the result is `5`, the same bytes as M02. M06's files are `8` and `1`, and the result is `9`. Both re-executed the trace. Neither pasted a stored answer string. A path-map match is a weaker claim than "remembered the earlier solution."
- M14 and M16 are procedure reuse: same class, different paths, and the lesson is what lets them finish inside a tight budget. That is a saved procedure. It is not a new capability on a class the library lacked.
- M25 is programmed composition. The ablation has no `pipeline_sum` lesson, returns no steps, and stops `unknown` without a tool call. The engine inserts `scale` before the stored write and produces `30` from `4`, `6`, and factor `3`. The composition rule was written in `procedures.py` before the run.
- M20 shows the cost of that same rule. Lessons lowered the unfamiliar pass rate from 1.0 to 0.5. The directive's bar, "measurable improvement on subsequent unfamiliar missions," is not met.
- M24 shows a real policy trade. Refusing to repeat a failed read avoids the baseline's extra failed operations and fails a file grade the baseline can pass. The completion rate keeps that miss.
- The world is a toy filesystem with injected faults. Passing it does not say anything about Echo's production tools, memory, or council.
- `resources.elapsed_ms` inside the child record is 0. Use the parent time in `grade.json` and `summary.json`.
- No production integration exists, and none is authorized by this result.

## 10. Recommendations for the next phase

Keep this package isolated. The next capability that would change the honest answer is a planner that assigns `problem_class` from the objective text, with this same external grader still scoring the world. That requires an explicit decision to call a model. This run does not.

Before any such call, the lesson rule needs a stop condition the M20 result already measured. A same-class path-map replay currently treats a finished trace as success. M20's finished trace was a false success. A later design can record whether the stored mission was allowed to write, and can refuse the replay when this mission's budget cannot pay for the hypothesis probe. That change would be a new experiment with a new freeze. It is not a reason to edit this score.

Split the label `remember` only in a future rubric, frozen before that future run. This run's labels stay as written.

Leave VSL, the working-self ledger, `echo_projects`, and the live server as they are.

## Direct answer

The prototype can carry a scripted mission across a killed process, order a multi-step template, switch to an alternate after a controlled fault, stop when the budget or a human gate or an unknown read says to stop, and keep a record an outside grader can check.

It did not improve on the unfamiliar pair. The lesson that helped three tight-budget replays and one programmed composition also produced the only false success in the engine arm.

Echo-the-model was not in this loop. The measured object is the grammar and the checkpoint, running with no operator between the two processes of a restart mission.
