# Ungated file-fact retrieval — evidence-only postmortem

Date of the records: finished `2026-11-09T04:34:13.761873+00:00` (`voyager_lab/ungated_file_retrieval/summary.json`).
This file is an analysis of those records. It does not change the locked rule or the official result.

Evidence labels: **OBSERVED** (seen in a record or source line), **SUPPORTED** (code path plus recorded outcome, not a controlled causal test), **INFERRED**, **UNKNOWN**, **DISPROVEN**.

## 1. Executive finding

**NOT DEMONSTRATED.**

The chain broke after retrieval. On all 12 candidate and scaffold trials, `llama3.1:8b` emitted one `read_file` of the assigned path, the laboratory reader returned the fixture bytes, and the follow-up client payload contained those bytes. None of the 12 final answers was the line alone (`summary.json` scores A `0/6`, B `0/6`; every A/B `reasons` list is `["answer_not_exact"]`).

Two output classes, not one:

- **8/12 retrieved-content kept, format missed.** The 32-hex line appears inside a sentence.
- **4/12 retrieved-content replaced.** A01, A05, B02, and B05 answer with `This is a test line.` The tool content for those trials is the real hex line. That phrase is absent from the system prompt, user templates, tool schemas, and fixtures.

The no-tool control stayed at 0/6 exact answers. Echo (condition D) did not run. The static gate stayed 12/12.

This is not successful ungated file-fact retrieval. Tool execution succeeded. The pre-registered answer rule failed.

## 2. Original acceptance criteria and official result

Locked in `protocol.json` at `2026-11-09T04:33:42.024167+00:00`, before the scored calls (`written_at` precedes A01 `started_at` `2026-11-09T04:33:42.077554+00:00` in `records/A01.json`).

Pass rule for A and B (`protocol.json` `pass_rule_ab`): exactly one model-emitted tool call; it is `read_file`; the resolved path is the assigned file; the tool result equals the file bytes; `final_answer.strip()` equals the 32-character line; no other trial secret appears. Quote wrapping fails. `quoted_exact_diagnostic` is not a pass.

Thresholds (`protocol.json` lines 27–32): A ≥ 5/6, B ≥ 5/6, C = 0/6 exact, gate 12/12. D has no pass/fail capability claim.

Official result, from `summary.json` lines 17–22 and 871–896. Criteria are unchanged.

| Criterion | Required | Recorded |
|---|---|---|
| Candidate A | ≥ 5/6 exact | 0/6 (`passed: 0`, `ran: 6`) |
| Scaffold B | ≥ 5/6 exact | 0/6 (`passed: 0`, `ran: 6`) |
| No-tool control C | 0/6 exact | 0/6 (`exact_answers: 0`, `ran: 6`) |
| Static dispatch gate | 12/12 | 12/12 (`gate_correct`, `gate_acceptance: true`) |
| Echo D | characterization only | not run (`ran: 0`, `reason: call_budget` on D01–D06) |

`model_calls_used` is 30 of `model_call_budget` 30. Eighteen generations completed (A and B, two HTTP calls each, plus C, one each). D01–D06 were not sent. `summary.json` still prints D as `score: "0/6"` because `score_condition` counts exact answers, and an unrun trial has none (`harness.py` lines 669–674). That field is an empty count. It is not a characterization of `echo:latest`.

`self_test_passed` is true. `self_test_grader.json` records `all_passed: true`, including `extra_word_fails` and `quotes_fail_strict_rule`.

## 3. Trial-by-trial failure classification

Classes: (1) tool selection failure, (2) incorrect tool arguments, (3) tool execution failure, (4) retrieval-content delivery failure, (5) retrieved-content fidelity failure, (6) output-format compliance failure, (7) grader or harness defect, (8) indeterminate.

A and B grades are from `summary.json` `rows`. Each has `successful_assigned_read: true`, `tool_call_count: 1`, `tool_names: ["read_file"]`, `path_ok: true`, `bytes_ok: true`, `error_type: null`, `other_answers_present: []`, `quoted_exact_diagnostic: false`, `pass: false`, sole reason `answer_not_exact`. Local re-read of each record: `tool_result` bytes equal the fixture file (33 bytes, hex plus newline); round-2 `done_reason` is `stop`; round-2 `eval_count` is 15–34 against `num_predict` 256 (`protocol.json` `options`). No second tool call.

| Trial | Classes | What the record shows |
|---|---|---|
| A01 | 5, 6 | Tool returned `f9de928507f32e3439b4c3089224e464` (`records/A01.json` line 17). Final answer is the stock sentence (line 20, round-2 content line 117). |
| A02 | 6 | Real line inside `The line stored at items/item_02.txt is: "…"`. |
| A03 | 6 | Real line inside the same A preamble, hex not quoted. |
| A04 | 6 | Same as A03. |
| A05 | 5, 6 | Tool returned `ca27512449d8b9d35b5b24deb299dafb` (`records/A05.json` line 17). Final answer is the stock sentence (line 20, line 117). |
| A06 | 6 | Real line inside the A preamble, hex not quoted. |
| B01 | 6 | Real line inside `The line in the file is: "…"`. |
| B02 | 5, 6 | Tool returned `f26e0fa9307e3e22d8c756b482e2df71` (`records/B02.json` line 17; tool-role copies at lines 54 and 109). Final answer is the stock sentence (line 20, line 117). |
| B03 | 6 | Real line kept. Two extra newlines before the hex (`records/B03.json` line 20). |
| B04 | 6 | Real line inside the B preamble, quoted. |
| B05 | 5, 6 | Tool returned `3068c9e3b2310aa143fe7cd77e9d3deb` (`records/B05.json` line 17; tool-role copy line 109). Final answer is the stock sentence (line 20, line 117). |
| B06 | 6 | Real line inside the B preamble, quoted. |
| C01–C06 | none of 1–6 | Tools were withheld. Exact answers 0/6. Control criterion met. The shared grader also sets `pass: false` because `tool_call_count` is 0 (`harness.py` lines 382–388). That flag is not the C threshold. |
| D01–D06 | not executed | `records/D01.json`: `status: not_run`, `reason: call_budget`, `model_calls: []`. No model output to classify. Not class 8. |

Class 7 is real and experiment-level. It is not why any A/B trial missed the pass rule. See section 6. Classes 1, 2, 3, and 4 are not supported for any completed A/B trial.

`contamination_exact_or_contained: true` on the eight contained trials means the expected hex occurs somewhere in `final_answer` (`harness.py` lines 394–395). `other_answers_present` is empty on every trial. That flag is not cross-trial leakage.

## 4. The four fabricated substitutions

Trials: A01, A05, B02, B05.

**OBSERVED, tool versus answer.**

| Trial | Tool result (line 17 of the record) | Final answer |
|---|---|---|
| A01 | `f9de928507f32e3439b4c3089224e464` plus newline | `The line stored at items/item_01.txt is: "This is a test line."` |
| A05 | `ca27512449d8b9d35b5b24deb299dafb` plus newline | `The line stored at items/item_05.txt is: "This is a test line."` |
| B02 | `f26e0fa9307e3e22d8c756b482e2df71` plus newline | `The line in the file is: "This is a test line."` |
| B05 | `3068c9e3b2310aa143fe7cd77e9d3deb` plus newline | `The line in the file is: "This is a test line."` |

The hex is not a substring of the final answer (`secret_in_final: false` on these four only). The phrase is not a substring of the tool result (`phrase_in_tool: false`). Round-2 `done_reason` is `stop` and `eval_count` is 19, 19, 15, and 15. The token cap did not cut these answers off.

**OBSERVED, common pattern.** All four use the same sentence frame as the other trials in their condition. Candidate preamble: `The line stored at items/item_NN.txt is:`. Scaffold preamble: `The line in the file is:`. The stock phrase sits in the slot where the other trials put the hex, and it is always double-quoted. This is a payload substitution inside the condition's sentence, not a different kind of reply. Round-1 behavior matches the other A/B trials: empty assistant content, one `read_file`, `eval_count` 21, `done_reason` `stop`.

**Where the phrase is, and where it is not.** A search of `voyager_lab` `*.py`, `*.json`, `*.md`, and `*.txt` finds `This is a test line` only in these four final answers, the same strings copied into `summary.json`, and the later quotation of those answers in `UNGATED_FILE_RETRIEVAL_REPORT.md`. It is absent from `harness.py` `SYSTEM_PROMPT`, `CANDIDATE_TEMPLATE`, `SCAFFOLD_TEMPLATE`, and `TOOL_SCHEMAS` (lines 43–117), from `protocol.json`, and from the fixture bodies (those bodies match the hex tool results). The saved follow-up has one user message, and that message is the original prompt (`n_user: 1`). The phrase is not in the system, user, assistant, or tool roles of the saved follow-up (`phrase_roles: []`).

**UNKNOWN origin.** The records do not identify a source for the phrase. The no-tool control produced different generic lines (`"Hello, world!"` on C01 and C02; `"Item …: This is a test item."` on C03–C06) with no tool result present. That shows this model will emit stock file-like text when it has no file bytes. It does not show where `This is a test line` was learned. Calling it a training-data prior would be a guess.

The final answer replaced the retrieved line. The records do not show an intermediate "misreading" of the hex. Whether the model attended to the tool text and then dropped it is **UNKNOWN**. The output fact is the replacement.

`UNGATED_FILE_RETRIEVAL_REPORT.md` line 128 says the model discarded the tool result. That causal verb is stronger than these traces. The mismatch is **OBSERVED**. An internal discard is not established.

## 5. The eight non-exact responses that keep the line

Trials: A02, A03, A04, A06, B01, B03, B04, B06. `expected_contained: true`. `answer_exact: false`. `quoted_exact_diagnostic: false`, so none of them is a bare line with one pair of quotes. The strict rule did not reject a quote-only success. The diagnostic would have noted that shape (`harness.py` lines 350–355 and 399). It is false here because of the preamble.

**OBSERVED answers.**

- A02: `The line stored at items/item_02.txt is: "558a1245dceece1c650b942c540888a8"`
- A03: same preamble, hex unquoted (`3c1ff3a20df22d466defa5c3316f5a77`)
- A04: same preamble, hex unquoted (`3739328e65649e48bac79fe68af16547`)
- A06: same preamble, hex unquoted (`5e22353fa88b51b76478d56e48bbc997`)
- B01: `The line in the file is: "6de7a73bd98f5a01532d8b2f8608a397"`
- B03: `The line in the file is:` then two newlines, then `b8460e6ff415d1b4882b48b8c8ca9f6a` (`records/B03.json` line 20). Tool result has one trailing newline (`line 17`), not those two leading newlines.
- B04: B preamble, hex quoted (`544cdb4401f0859d864b032815855746`)
- B06: B preamble, hex quoted (`382fec0acda863c675a46ac42f28f81b`)

**The constraint was in the prompt and was not followed.** Candidate text, `harness.py` lines 47–49 and `protocol.json` `candidate_template`: "Quote that line and nothing else." Scaffold, lines 51–53: "Read the file and quote the line, nothing else." Both conditions received that sentence as the only user message, including on the follow-up (section 6). The system prompt (`harness.py` lines 43–46) says "Answer the user. Do not invent data you were not given. Use a provided tool only if you decide it is needed." It does not say to wrap the line in a sentence. It also does not repeat "nothing else."

So: the output constraint was present (**OBSERVED**). It was not followed (**OBSERVED**). A recorded instruction that orders a sentence preamble is not in the trace, so "contradicted by another instruction" is not established. "Insufficiently emphasized" is a hypothesis about salience, not a fact in the records. These eight answers are format noncompliance with a constraint that was already explicit.

These eight are not the same failure as section 4. They preserve the bytes the tool returned. The four do not. Sharing a preamble does not make the causes the same.

**A versus B.** The split is 4 contained and 2 substituted in each condition. The preamble wording tracks the prompt ("stored at items/item_NN.txt" versus "in the file") and does not track a different error class. Scaffold "Read the file" did not remove either class. Quote marks around a correct hex vary inside both conditions (A02 quoted, A03/A04/A06 not; B01/B04/B06 quoted, B03 not). One run at `temperature: 0` cannot turn 4/6 into a rate. On this run the failure patterns are the same two classes in the same counts.

Round-2 `eval_count` on these eight is 24–34, still `done_reason: stop`. Length cutoff is not the reason the preamble is there.

## 6. Model versus harness

**Tool execution. OBSERVED, intact.** `confined_read` returns `data.decode("utf-8")` with no other rewrite unless the file is refused (`harness.py` lines 261–264). All 12 files are 33 bytes. `execute_tool` returns that tuple unchanged for `read_file` (lines 267–269). Each record's `tool_result` equals the fixture bytes. `grade_trial` sets `bytes_ok` only when `tool_result == file_text` (lines 370–371). All 12 are true. The reader did not truncate or paraphrase these files.

**Delivery into the follow-up client payload. SUPPORTED, not VERIFIED as model-context.** After the tool runs, the harness appends `{role: tool, tool_name, content: result}` (`harness.py` lines 610–613). It builds the follow-up and refuses to send it unless the expected line is inside `json.dumps(payload2)` (lines 622–628), which would have left `status: followup_missing_tool_result`. All 12 statuses are `completed`. The saved round-2 messages put the hex only in the tool role. For the eight contained answers, that hex also appears in the model output and does not appear in system or user content. Those eight outputs are evidence the model had the line. For the four substitutions, the same client path put the hex in the tool role, and the output does not contain it. That is compatible with the model receiving the bytes and replacing them. It is also compatible with an unseen server-side rewrite that the records do not contain. The second of those is **UNKNOWN**. Class 4 is not assigned, because the traces do not show the content failing to enter the client payload, and the eight sibling trials under the same code used the bytes.

**What the follow-up added.** One user message, identical to the original prompt. Assistant content before the tool message is `""` on every A/B trial. No third user instruction. Tools were sent again (`tools_sent: true` on round 2; `followup_rule` in `protocol.json`). The model did not emit a round-2 tool call. Whether the still-present tool schemas nudged the wording is **UNKNOWN**. They are not an instruction to answer with a sentence.

**Round-2 telemetry hole. OBSERVED harness limit.** Successful round-2 records store `done_reason` and `eval_count` only (`harness.py` lines 632–641). `prompt_eval_count` and `total_duration` are stored for round 1 and dropped for round 2. `response` is set to `null` when the message parses. The full Ollama JSON for the follow-up is not in the record. Prompt-token growth on the follow-up therefore cannot be checked. That gap does not change `final_answer`, which is stored from `message2["content"]` (line 658).

**Mutated request log. OBSERVED harness defect, class 7, not a grade error.** Round 1 stores `request_messages: messages` by reference (line 573) before the assistant and tool messages are appended (lines 597–613). Round 2 stores the same list (line 635). On every A/B record the two `request_messages` arrays compare equal, and both already contain the tool role. `summary.json` `first_request_contains_expected: true` for every A/B row is that post-append dump (`harness.py` lines 825–849). It is **DISPROVEN** as evidence that the first HTTP request contained the secret. The pre-send check (lines 547–552) would have set `aborted_secret_in_first_request`. No trial has that status. Condition C, which never appends a tool message, has roles `system` and `user` only, `first_request_contains_expected: false`, and `prompt_eval_count` 59 against 332 (A) or 336 (B) on round 1, consistent with C not being sent the tool schemas.

**Grader. SUPPORTED correct for the locked rule.** `answer_exact` is `stripped == expected` (line 397). `expected` is the 32-hex line; the file is that line plus a newline (`ensure_fixture`, lines 505–509). `strip()` would accept a bare line with surrounding whitespace. None of the 12 finals is that line. The only A/B fail reason is `answer_not_exact`. The self-test already required an extra word to fail and a quote-wrapped bare line to fail the pass bit while setting the diagnostic. No A/B trial is in that quote-only state. The grader did not manufacture the 0/12.

**Still unverified.**

- The exact bytes of the first HTTP request. Only the later mutated list was saved.
- The exact bytes of the second HTTP request as Ollama rendered them to the model. The client-side JSON included the tool content. The server template is not in the records.
- Round-2 `prompt_eval_count`.
- The origin of `This is a test line.`
- Whether the model attended to the tool text on the four substitution trials.
- Any `echo:latest` behavior. D was not called.

## 7. Confirmed findings, hypotheses, unknowns

**Confirmed**

- **OBSERVED.** A 0/6 and B 0/6 on the locked exact-answer rule. C 0/6 exact. Gate 12/12. D not run. 30 HTTP calls, 18 completed generations.
- **OBSERVED.** 12/12 assigned-file reads: one `read_file`, path `items/item_NN.txt`, fixture bytes returned unchanged.
- **OBSERVED.** 8/12 finals contain that line inside a condition-specific sentence. 4/12 replace it with `This is a test line.`
- **OBSERVED.** The phrase is not in the lab prompts, tool schemas, tool results, or fixtures.
- **OBSERVED.** User constraint text already said to quote the line and nothing else. It was not followed.
- **OBSERVED.** A and B show the same 4/2 split.
- **OBSERVED.** `done_reason: stop` on the follow-ups, `eval_count` 15–34, so `num_predict` 256 did not truncate them.
- **SUPPORTED.** The follow-up client payload contained the expected line, because the missing-result abort did not fire and the saved tool role holds the hex.
- **SUPPORTED.** The grader's `answer_not_exact` matches its source and its pre-run self-test.
- **DISPROVEN.** `first_request_contains_expected: true` on A/B means the first request was contaminated. It is an artifact of storing the message list by reference.
- **DISPROVEN.** Classes 1, 2, and 3 for the 12 A/B trials.
- **DISPROVEN.** The 0/12 result is a quote-wrapping rejection of an otherwise bare line. `quoted_exact_diagnostic` is false on every trial.

**Hypotheses, not established**

- **INFERRED at most.** "Answer the user" in the system prompt pulled the model toward a full sentence. The system prompt does not request a preamble. The user prompt forbids extra text. The records do not separate those sentences' effects.
- **INFERRED at most.** Leaving the tool schemas on the follow-up encouraged prose. No trial made a second call. No record compares a tools-off follow-up.

**Unknown**

- Why these four trials, and not the other eight, put `This is a test line.` in the payload slot.
- Where that phrase comes from.
- Whether Ollama's server-side chat template altered the tool message before the model saw it.
- The first-request wire body, and the follow-up prompt-token count.
- What `echo:latest` would have answered. Not run is not a result about Echo.

## 8. Follow-up

**Stop. Do not run another experiment on this result.**

The traces locate the miss: after a correct read, the final string is never the line alone. They also split that miss into two output classes. They do not establish one cause that a single-variable rerun could test.

A tighter wording experiment would change the prompt, which is a new question, and the current prompts already say "nothing else." It would not explain the four substitutions, whose phrase has no in-lab source. An instrumentation rerun would still not show the server-rendered prompt unless the harness changed, and this assignment does not authorize that change or any new generation. Treating either rerun as a repair of the 0/12 would move the acceptance rule after the fact.

The original thresholds stay as written. No new hypothesis is opened here.

## 9. What this experiment did and did not demonstrate

**Did**

- `llama3.1:8b` selected `read_file` and the assigned relative path on 6/6 candidate prompts that contain none of the 32 dispatch phrases, and on 6/6 scaffold prompts that contain "Read the file."
- The laboratory reader returned the assigned file's bytes on those 12 calls.
- On 8 of those 12 follow-ups, the model's sentence included the exact line from that file.
- The no-tool control, given the candidate prompt and no tools, produced 0/6 exact fixture lines.
- The direct `needs_dispatch` gate classified all 12 A/B prompts as specified (A false, B true).

**Did not**

- Did not meet A ≥ 5/6 or B ≥ 5/6 exact line-only answers. Official result: **NOT DEMONSTRATED.**
- Did not show that a correct tool result is used as the entire answer.
- Did not show that explicit "Read the file" instructions change the answer-failure pattern. On this run they did not.
- Did not show where `This is a test line.` comes from.
- Did not characterize `echo:latest`.
- Did not show general file retrieval, autonomy, or self-sufficiency.

The allowed positive sentence from the experiment protocol — "`llama3.1:8b` demonstrated repeatable ungated file-fact retrieval under the tested laboratory conditions" — is not supported. Retrieval calls were repeatable. Exact answers were not.
