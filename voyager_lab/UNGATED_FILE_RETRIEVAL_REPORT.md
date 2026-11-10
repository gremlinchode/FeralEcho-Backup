# Ungated file-fact retrieval

Date of run: 2026-11-09T04:33:42Z through 2026-11-09T04:34:13Z.
Laboratory only. Production dispatch, memory, FAISS, VSL, port 5000, and the live Echo process were not used.

## 1. Research question

Can `llama3.1:8b`, given a confined `read_file` tool, recognize that a task needs an unknown file value and invoke that tool correctly when the prompt contains none of the 32 existing dispatch-trigger phrases?

The pass rule requires all of the following on one trial: the model itself emits exactly one `read_file`; the path is the assigned file; the tool returns that file's bytes; the final answer is exactly the 32-character line and nothing else. A correct tool call with extra prose does not pass. A correct-looking answer without that tool call does not pass.

## 2. Experimental conditions

| Condition | Model | Tool access | Prompt | Planned | Model calls made |
|---|---|---|---|---:|---:|
| A Candidate | llama3.1:8b | Yes | Ungated | 6 | 12 (6 + 6 follow-ups) |
| B Scaffold | llama3.1:8b | Yes | Explicit "Read the file" | 6 | 12 (6 + 6 follow-ups) |
| C No-tool | llama3.1:8b | No | Same ungated prompt | 6 | 6 |
| D Echo characterization | echo:latest | No | Same ungated prompt | 6 | 0 |

Order was locked as A, B, C, D. One follow-up HTTP call was allowed only when the model emitted a tool call. No third round. Budget was 30 local calls. The run used 30. Condition D was not sent.

Both required models were present in local Ollama before the run (`model_availability.json`). No model was downloaded. Options, locked in `protocol.json` before any scored output: temperature 0, num_ctx 4096, num_predict 256, stream false. Summed Ollama `total_duration` across the 30 recorded calls is 17.28 seconds. Every recorded call has `done_reason` `stop`. Summed `eval_count` is 617.

## 3. Exact prompts

System prompt, identical for every condition:

> Answer the user. Do not invent data you were not given. Use a provided tool only if you decide it is needed.

Candidate and no-tool and Echo prompt:

> A single line is stored at items/item_NN.txt. Quote that line and nothing else.

Scaffold prompt:

> A single line is stored at items/item_NN.txt. Read the file and quote the line, nothing else.

`NN` was `01` through `06`. Each trial had its own directory and its own random 32-character hexadecimal line plus a newline. The expected line lived in `grader_key.json` and was not placed in the prompt or the tool descriptions.

Conditions A and B were offered three tools: `read_file`, `search_memory`, and `log_thought`. `read_file` was confined to that trial's directory. The other two were laboratory stubs. The harness did not choose the tool. The production dispatch system prompt was not used.

## 4. Model identities

- `llama3.1:8b` is the model under test for tool selection. Conditions A, B, and C used it.
- `echo:latest` is Echo's separate local model. Condition D would have characterized it with no tools. It received no call.

A result for `llama3.1:8b` is not a result for `echo:latest`.

## 5. Tool-call traces

Every A and B trial: the model emitted exactly one tool call, on round 1, name `read_file`, argument `path` = `items/item_NN.txt` for that trial's `NN`. The confined reader executed it. `path_ok` is true and `bytes_ok` is true on all 12. `error_type` is null. `search_memory` and `log_thought` were not called. No trial called a second tool on the follow-up.

C and D traces are empty. C had tools withheld. D was not run.

The tool result was returned to the model as `{role: tool, tool_name: read_file, content: <file text>}` before the follow-up generation. Eight of the twelve A/B finals contain the exact hex line that existed only in that file, which is evidence the follow-up received the bytes. Four finals replaced those bytes with the sentence `This is a test line.`

## 6. Raw trial outcomes

Official pass uses the locked rule. "Contained" means the final answer includes the assigned 32-character line inside other text. Contained is not a pass.

| Trial | Status | Tool calls | Path / bytes | Exact | Contained | Final answer |
|---|---|---:|---|---|---|---|
| A01 | completed | 1 read_file | yes / yes | no | no | The line stored at items/item_01.txt is: "This is a test line." |
| A02 | completed | 1 read_file | yes / yes | no | yes | The line stored at items/item_02.txt is: "558a1245dceece1c650b942c540888a8" |
| A03 | completed | 1 read_file | yes / yes | no | yes | The line stored at items/item_03.txt is: 3c1ff3a20df22d466defa5c3316f5a77 |
| A04 | completed | 1 read_file | yes / yes | no | yes | The line stored at items/item_04.txt is: 3739328e65649e48bac79fe68af16547 |
| A05 | completed | 1 read_file | yes / yes | no | no | The line stored at items/item_05.txt is: "This is a test line." |
| A06 | completed | 1 read_file | yes / yes | no | yes | The line stored at items/item_06.txt is: 5e22353fa88b51b76478d56e48bbc997 |
| B01 | completed | 1 read_file | yes / yes | no | yes | The line in the file is: "6de7a73bd98f5a01532d8b2f8608a397" |
| B02 | completed | 1 read_file | yes / yes | no | no | The line in the file is: "This is a test line." |
| B03 | completed | 1 read_file | yes / yes | no | yes | The line in the file is: followed by two newlines, then b8460e6ff415d1b4882b48b8c8ca9f6a |
| B04 | completed | 1 read_file | yes / yes | no | yes | The line in the file is: "544cdb4401f0859d864b032815855746" |
| B05 | completed | 1 read_file | yes / yes | no | no | The line in the file is: "This is a test line." |
| B06 | completed | 1 read_file | yes / yes | no | yes | The line in the file is: "382fec0acda863c675a46ac42f28f81b" |
| C01 | completed | 0 | — | no | no | "Hello, world!" |
| C02 | completed | 0 | — | no | no | "Hello, world!" |
| C03 | completed | 0 | — | no | no | "Item 3: This is a test item." |
| C04 | completed | 0 | — | no | no | "Item 04: This is a test item." |
| C05 | completed | 0 | — | no | no | "Item 05: This is a test item." |
| C06 | completed | 0 | — | no | no | "Item 06: This is a test item." |
| D01 | not_run | 0 | — | — | — | (no model call; call budget) |
| D02 | not_run | 0 | — | — | — | (no model call; call budget) |
| D03 | not_run | 0 | — | — | — | (no model call; call budget) |
| D04 | not_run | 0 | — | — | — | (no model call; call budget) |
| D05 | not_run | 0 | — | — | — | (no model call; call budget) |
| D06 | not_run | 0 | — | — | — | (no model call; call budget) |

Full request and response bodies are in `voyager_lab/ungated_file_retrieval/records/`. Unused secrets remain only in `grader_key.json`.

## 7. Independent grading

The grader is deterministic Python in `harness.py`. It does not ask a model to score. It compares the saved tool trace and final answer with the file on disk and the grader key.

A trial in A or B passes only when tool-call count is 1, the name is `read_file`, the resolved path is the assigned file, the tool result equals the file bytes, `answer.strip()` equals the 32-character line, and no other trial's line appears. Quote wrapping fails. The grader self-test (`self_test_grader.json`) passed before any scored call: a perfect bare line passes; an answer without a tool fails; a wrong path fails; an extra word fails; another trial's secret fails; quotes fail the strict rule and are noted only as a diagnostic.

No A or B answer is exact. The sole recorded fail reason on each of those 12 is `answer_not_exact`. Eight answers contain the real line plus a preamble. Four answers (A01, A05, B02, B05) do not contain the real line.

C is graded for exact match with the secret. All six are false. Their `grade.pass` field is also false because the shared grader records the missing tool call. The C threshold uses exact answers, which are 0.

## 8. Dispatch-gate results

`needs_dispatch` was loaded with `importlib` from the worktree copy of `app/core/echo_tool_dispatch.py` and called directly. The app package was not imported. Mode: `direct_function`. Signal count: 32. Worktree source SHA-256 matches the production file (`worktree_source_sha256_matches_production`). This is a direct function call, not a live-server execution.

| Set | needs_dispatch | Expected | Correct |
|---|---|---|---:|
| A01–A06 candidate prompts | false | false | 6/6 |
| B01–B06 scaffold prompts | true | true | 6/6 |

The scaffold hit is the substring `read the file`. The candidate prompts hit none of the 32 signals. The system prompt hit none. Acceptance: 12/12. The production function was not modified.

## 9. Scores

| Measurement | Result | Required | Met |
|---|---:|---:|---|
| Candidate A official pass | 0/6 | at least 5/6 | no |
| Scaffold B official pass | 0/6 | at least 5/6 | no |
| No-tool C exact answers | 0/6 | 0/6 | yes |
| Static dispatch gate | 12/12 | 12/12 | yes |
| Echo D | not run (0 calls) | report only | no capability claim |

Separate observation, not a substitute score: assigned-file `read_file` with correct bytes occurred on 6/6 candidate trials and 6/6 scaffold trials. Exact quotation occurred on 0/6 and 0/6. The assigned pass rule requires both.

`summary.json` prints D as `0/6` because its exact-answer counter is zero. That figure is an empty set. It is not a measured `echo:latest` result.

## 10. Anomalies and contamination

- A01, A05, B02, and B05 returned the real file bytes and then answered `This is a test line.` The harness did not substitute that sentence. The model discarded the tool result.
- The other eight A/B answers kept the real hex line and wrapped it in a sentence. B03 also has two leading blank lines after the preamble. Both prompts already said to quote the line and nothing else. The format instruction was not followed.
- No final answer contains another trial's secret. Cross-trial count is 0.
- C fabricated generic lines (`Hello, world!`, `Item N: This is a test item.`). None is the assigned hex line. The contamination check holds.
- No trial aborted for a secret in the pre-send payload. System and user message bodies do not contain the assigned secret.
- `summary.json` field `first_request_contains_expected` is true for every A and B row. That field was computed after the run by dumping `model_calls[0].request_messages`. The harness stored that list by reference and later appended the assistant and tool messages to the same object, so the saved round-1 list also shows roles `system, user, assistant, tool`. The secret appears only in the tool message. C, which never appended a tool message, has the flag false and roles `system, user` only. This is a recording defect. It is not evidence that the first HTTP request contained the answer.
- D fixtures exist because the file was created before the budget check. No D request was sent.

## 11. Limitations

- Eighteen of twenty-four planned generations ran. D did not run because A and B each used a protocol follow-up and the pre-registered cap of 30 was reached after C. Thresholds do not require D. A and B are complete samples of six.
- The six trials share one sentence frame. A pass would have been a repeatable procedure for this frame only. Generalization was outside this design.
- The strict exact-answer rule was locked before the run and was not relaxed. Counting "the line is present somewhere in the answer" would change the rule after the results.
- Saved round-1 message lists are not a byte copy of the first HTTP body, because of the shared-list recording defect above. The pre-send secret check and the role-level inspection are the available evidence on leakage.
- `echo:latest` was not characterized.
- The production phrase gate was measured by a direct function call. The live Echo process was not asked to classify these prompts.

## 12. Final conclusion

**NOT DEMONSTRATED.**

`llama3.1:8b` selected `read_file` once, with the assigned path, on all six ungated trials and all six scaffold trials, and the laboratory tool returned the assigned bytes each time. The final answer was the line alone on none of those twelve trials. Candidate score 0/6 and scaffold score 0/6 are below the required 5/6. Ungated file-fact retrieval, under the locked pass rule, was not demonstrated. Explicit retrieval wording did not establish reliable use of the returned text either: the scaffold failure is the same answer-format and answer-substitution pattern.

The no-tool control produced 0/6 exact answers. The static gate classified 12/12 prompts correctly, so the candidate prompts do sit outside the existing phrase gate. That gate result does not create a pass on the model task.

Condition D supplies no evidence about `echo:latest`.

This experiment does not show that Echo learned file retrieval, and it does not show general autonomy or self-sufficiency. The permitted positive sentence is not supported.

One successful exact execution: none.
Repeatable exact procedure: not met.
Generalization: outside this design.
Independent capability in the broad sense: outside this design.

## 13. Recommendation for the next experiment

Do not rerun these 24 trials and do not weaken the exact-answer rule.

The measured gap is what the model does after a successful read. On this run, tool selection and argument construction succeeded while exact quotation failed, and on four trials the model replaced the returned line with a stock sentence.

A later, separately authorized experiment could pre-register two scores before any call: tool selection, and exact quotation. It should use new secrets, keep the same confinement, and keep a no-tool control. It should not train on these answers, and it should not spend calls until that protocol is locked. This report does not authorize that run.

## Decision block

- All 24 planned generations ran: no. A, B, and C ran (18 generations, 30 HTTP calls). D01–D06 are `not_run` / `call_budget`.
- Candidate score: 0/6.
- Scaffold score: 0/6.
- No-tool exact score: 0/6.
- Echo characterization: not run. No capability claim.
- Static dispatch-gate accuracy: 12/12, direct function, production source hash matched.
- Success thresholds: A not met, B not met, C met, gate met. Overall success requires all of them. Overall success was not met.
- Production remained untouched. See the file and git notes below.

**NOT DEMONSTRATED.**

## Files created

Under `voyager_lab/ungated_file_retrieval/`:

- `harness.py` — confined reader, three tool schemas, grader, gate loader, Ollama client, 30-call budget.
- `protocol.json`, `gate_verification.json`, `self_test_grader.json`, `model_availability.json`, `grader_key.json`, `summary.json`.
- `self_test_fixture/items/item_01.txt` — fixed self-test line, not a trial secret.
- `records/A01.json` through `A06.json`, `B01.json` through `B06.json`, `C01.json` through `C06.json`, `D01.json` through `D06.json`.
- `fixtures/{A,B,C,D}/{01..06}/items/item_NN.txt` — 24 files.
- `__pycache__/harness.cpython-313.pyc` — compile artifact from the syntax check.

This report: `voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md`.

## Git and production check

Voyager worktree HEAD: `dc8d6eb9b6479ef323614cd6820bb050a14299eb`.
`git status --porcelain`: `?? voyager_lab/` only.
`git diff --stat`: empty. No tracked file changed.

Production checkout porcelain SHA-256 after this report's evidence check, before this report was written: `47efc683d9df161ec770ab2727a1f64a187bb3b9ab3f19aaffd13fce1b582985`, matching the hash captured before the experiment.

Frozen Voyager lstat, unchanged from the pre-experiment record:

| Path | inode | size | mode | mtime_ns |
|---|---:|---:|---|---:|
| voyager_lab/voyager/engine.py | 36256079 | 19977 | 0644 | 1794177805925011044 |
| voyager_lab/voyager/worker.py | 36260012 | 1398 | 0644 | 1794178781409311138 |
| voyager_lab/results/summary.json | 36269403 | 57749 | 0600 | 1794179724623157658 |

Nothing was committed. The live Echo process was not signaled. Port 5000 was not contacted.
