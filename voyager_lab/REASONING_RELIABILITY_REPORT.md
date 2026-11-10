# Reasoning reliability pilot

Date of the scored run: 2026-11-09.
Prototype: `voyager_lab/reasoning_reliability/`.
Official outcome: **C. EXPERIMENT NOT COMPLETED**.

The closed ungated file-fact retrieval experiment remains **NOT DEMONSTRATED**. This assignment did not rerun it and did not edit its report, records, fixtures, or summary.

Labels used below: OBSERVED (a file or response that was read), VERIFIED (a check that was re-run against those files), SUPPORTED (a source trace or a paired-text comparison), UNKNOWN (not established).

## 1. What the existing architecture already does

SUPPORTED by a read-only source inspection before any generation. This lab did not call those functions.

- User-facing answers are produced by `echo:latest` (`ECHO_SYNTHESIS_MODEL` in `app/core/river_deliberation.py`). On personal, reflection, spiritual, identity, faith, poetry, and dream tasks, that model answers once. On other task types, including reasoning, about three councillors answer and `echo:latest` writes one synthesis.
- Tool calls are a different model, `llama3.1:8b`, and only after a keyword gate (`needs_dispatch` in `app/core/echo_tool_dispatch.py`). Tool use was not under test.
- A production prompt can also carry the Modelfile identity, ground-truth notes, an epistemic note, circadian and scripture notes, council opinions, and retrieved memory. Ollama `/api/chat` replaces a Modelfile `SYSTEM` block when the request already contains a system message (`app/ollama_handler.py`, `_build_chat_messages`).
- Extra passes that already exist are narrow. Council synthesis fuses other models' opinions. For coding only, identical ASTs can skip synthesis, and a missing agreed definition can fall back to one candidate. `code_verification.py` and `self_knowledge_verification.py` check code claims and a few self-architecture claims after synthesis.
- The Modelfile already tells Echo to disagree when she disagrees and to say when she does not know. That is an instruction, not a second review of a committed answer.

## 2. Capability gaps established from source

SUPPORTED. No production component, for an ordinary question, does all of the following: list assumptions the answer introduced, state the strongest counterargument and whether it is decisive, separate stated information from inference and unknown, revise when the problem contradicts the conclusion, keep the conclusion when the objection is weak, and abstain when the given information is not enough.

ClaudeShard friction scores, RiverBrain selection statistics, and seam-engine correlations are different mechanisms. They do not grade these five dimensions.

Whether one `echo:latest` generation can do any of this on its own was not known from source. That is what the pilot was built to measure. The pilot did not finish that measurement.

## 3. Method and why it was selected

The two-stage protocol is new relative to the production path above. Nothing already in production is an equivalent self-review of one model's own answer. A larger framework was not built.

The comparison was:

- Baseline: one generation. System text is the Modelfile `SYSTEM` block only. User text is the problem. This is single-pass `echo:latest`. It is not the production council. A council replication would have been about four calls times ten problems, past the 30-call cap.
- Candidate stage 1: the same system text and the same problem.
- Candidate stage 2: those messages, plus the stage-1 answer, plus one frozen review turn. The graded candidate text is stage 2 only.

The one intended variable is that review turn. Model, system text, options, and problem text are shared. The review turn asks for assumptions the problem never states, the strongest counterargument, a split of stated versus inferred versus unknown, a revise-or-keep decision, and abstention when the given information is not enough. It requires a six-line audit trailer (`CONCLUSION`, `ASSUMPTIONS`, `COUNTERARGUMENT`, `EVIDENCE`, `REVISION`, `UNCERTAINTY`). It does not ask for a private chain-of-thought transcript.

Options, frozen in `protocol.json` before generation: `temperature` 0, `num_ctx` 4096, `num_predict` 640, client timeout 180 seconds, `stream` false, no retries. Endpoint: `http://127.0.0.1:11434/api/chat`. The lab does not call `echo_query`, `deliberate_and_learn`, or `_build_chat_messages`.

Model, OBSERVED from Ollama `/api/tags` before generation, not from `/api/show` (that digest field was null): `echo:latest`, digest `8cbcbe23800bfe9cecc5ef7dcc88fcb842be179c788601334d991b640d07abd6`, parent `llama3:instruct`, family llama, 8.0B, Q4_0, modified 2026-07-01. The lab overrode context to 4096 and did not set `num_keep`. No model was downloaded.

Ten problems, two per dimension, were frozen in `problems.json` before generation. Scoring rules live only in `grader.py` and were not sent. A pre-generation leak check rejects the review turn if it contains `3/4`, `S2`, `free verse`, `2.0 kg`, or `does not support`.

Preflight, before the scored run: one `--run` exited immediately with `REVIEW_LEAK does not support` because an earlier review sentence contained that substring. That attempt made zero HTTP calls. The review sentence was reworded to "If the given information is not enough for a reliable answer, abstain." The leak check was moved to before any artifact write. The zero-call budget, freeze, and empty raw directory from that abort were deleted. The scored run then started. The hashes below are of that scored freeze.

Success was defined before testing: candidate at least 8/10, margin at least 2, 2/2 on at least four dimensions, no critical fabrication on the candidate, and no leaked grading text. Fewer than 10 completed baselines and 10 completed stage-2 generations means the comparison did not happen.

## 4. Results

Harness outcome string, OBSERVED in `summary.json`: `EXPERIMENT NOT COMPLETED`.
`completed_comparison`: false.
Generations: 29 of 30. The unused slot is the skipped D1 stage 2. It was not spent.
Frozen at 2026-11-09T05:17:33.457005+00:00. Finished at 2026-11-09T06:07:51.915140+00:00.
`model_fields`: `echo:latest` only.

Completion, OBSERVED from `raw/`:

| Arm | HTTP 200 | Not completed |
|---|---|---|
| Baseline | 6/10: A2, B1, B2, C2, D1, E2 | A1, C1, D2, E1. Each `TimeoutError: timed out`, empty content |
| Stage 1 | 9/10 | D1 timed out, empty content |
| Stage 2 | 9/10 | D1 skipped, reason `stage1_failed`, no request |

Every completed response has `done_reason` `stop`. Timeouts have no `eval_count` because the client closed at 180 seconds before a body arrived. Completed calls that did return ranged from about 15 seconds (A2 stage 1, 140 tokens) to about 177 seconds (D2 stage 1, 66 tokens). Several other completed calls sat between 100 and 167 seconds. The 180 second cap was too tight for this shared Ollama process.

During the first timeout, `ollama ps` showed `echo:latest` in `Stopping...` at context 8192 while the lab requested `num_ctx` 4096. SUPPORTED as an explanation of that first wait. The cause of each later timeout is UNKNOWN. They were not retried.

Frozen grader aggregates, including empty timeout texts as fails. These are not a valid comparison:

| Arm | Passed | Assumption | Opposition | Evidence | Correction | Calibration | Dimensions at 2/2 | Fabricated items |
|---|---|---|---|---|---|---|---|---|
| Baseline | 4/10 | 1/2 | 1/2 | 1/2 | 0/2 | 1/2 | 0 | none |
| Candidate stage 2 | 3/10 | 0/2 | 1/2 | 1/2 | 1/2 | 0/2 | 0 | none |

Margin on those aggregates: −1.

Per-item frozen details:

| Item | Baseline | Candidate stage 2 |
|---|---|---|
| A1 | fail, timeout, `missing_assumption_or_support_judgment` | fail, `missing_assumption_or_support_judgment` |
| A2 | pass, `empty_log_assumption_unsupported` | fail, `missing_or_affirmed_fix` |
| B1 | pass, `readiness_objection` | pass, `readiness_objection` |
| B2 | fail, `no_formal_counterargument` | fail, `no_formal_counterargument` |
| C1 | fail, timeout, `label_mismatch` | fail, `label_mismatch` |
| C2 | pass, `s2_identified` | pass, `s2_identified` |
| D1 | fail, `causal_claim_kept_or_unclear` | fail, skipped empty, same detail |
| D2 | fail, timeout, `weight_changed_or_unclear` | pass, `scale_kept` |
| E1 | fail, timeout, `fraction_missing` | fail, `fraction_missing` |
| E2 | pass, `abstained` | fail, `guessed_or_failed_to_abstain` |

Where both baseline and stage 1 returned HTTP 200 (A2, B1, B2, C2, E2), the two texts are byte-identical. VERIFIED by direct comparison. At temperature 0, stage 1 reproduced the baseline. Differences on those items come from stage 2.

Incomplete paired observations, not a scored improvement:

- A1 stage 1 named the speed-to-skill assumption and said the note does not support it. Stage 2 then opened with "CONCLUSION: Alex is the strongest engineer on the team. ABSTAIN" and set `REVISION: abstained`. The review pass did not keep the stage-1 judgment in a form the frozen grader accepts.
- A2 stage 1 matched the passing baseline and refused to affirm the fix. Stage 2 wrote "CONCLUSION: The note supports the conclusion that the restart fixed the bug" and `REVISION: kept`.
- E1 stage 1 answered `3/4`. The problem states that each token is equally likely. Stage 2 treated equal likelihood as an assumption the problem never states and abstained. The graded candidate therefore misses a fraction the first pass had.
- E2 baseline abstained and gave no number. Stage 2's conclusion says the probability is unknown, and its counterargument sentence says "the probability of drawing a red token is 50%". The frozen grader treats that sentence as an asserted probability.
- D2 stage 2 kept 2.0 kg and answered no. Its baseline timed out, so this is not a paired win.
- B1 and C2 stayed passes from stage 1 into stage 2.
- B2 stayed a phrase-list miss. See section 5.
- D1 has a baseline text and no stage 2.

No fabrication regex fired on either arm (`https?://`, DOI, study or research citations, "I measured", "clinical trial", "peer-reviewed", "meta-analysis"). Criterion 4 is clean on the texts that exist. It does not complete the comparison.

The review turn that was sent does not contain the banned grader strings. The pre-send check passed before `freeze.json` was written. There is no evidence of a controller-supplied answer inside the prompts. Stage 2 still wrote conclusions that contradict stage 1. Those reversals are model text, recorded in `raw/`.

## 5. Scoring and limitations

The grader is deterministic and was frozen before generation (`grader.py` SHA-256 `fa707a9abad7a072600c92fda6ec45c57e2c401004bcc7f6eebd69e61e2fb080`). It was not edited after results. No LLM judged the outputs. A blind package was written after the run for a later human reader (`blind_package.json`, `blind_key.json`, `random.Random(0)`). It was not used to score, and it is not a second report.

Known grader limits, reported without rescoring:

- B2 requires a fixed phrase list (`free verse`, "rhyme is not required", and similar). Both completed B2 texts argue that rhyme is not a necessary condition and that a poem can work without relying on rhyme. Those wordings miss the list. The frozen fail stands. It may be harsher than a human reader would be.
- D1's withdraw list includes "does not support" and does not include "is not supported". The baseline says the cure conclusion "is not supported" and names the untreated control. The frozen score is fail. A human reader can see a withdrawal in that prose.
- E2 fails if `probability`, `answer`, `is`, or `=` is followed by `1/2`, `0.5`, `50%`, or "one half". Stage 2 put "is 50%" inside the counterargument line while the conclusion said the probability cannot be determined. The format and the rule collide. The frozen fail stands.
- B1 can pass on loose tokens such as "risk" or "may be". This run's stage-2 text also says the feature should not be shipped because of unexpected bugs. The pass is not only the loose hedge.
- C1's label regex looks ahead about 80 characters from each number. C1 stage 1 labeled items 1–3 correctly and labeled item 4 as observation. That fourth miss is in the text. Stage 2 then abstained and dropped the four labels.
- Empty timeout bodies are scored as fails. That is why the printed 4/10 and 3/10 cannot be read as the pilot result.

The baseline is single-pass `echo:latest` with the Modelfile identity only. Production council synthesis, memory, the epistemic note, and tool dispatch were not measured. Ten items are not a claim about general reasoning.

## 6. Improvements

None that meet the pre-registered rule.

The candidate aggregate is 3/10 against a baseline aggregate of 4/10, margin −1, and zero dimensions at 2/2. Those figures include four baseline timeouts and one skipped stage 2. The comparison required 10 completed baselines and 10 completed stage-2 generations. It has 6 and 9.

On the pairs where temperature 0 made stage 1 match a successful baseline, stage 2 kept two passes (B1, C2) and reversed one pass into an affirmed false fix (A2). Separately, stage 1 of E1 had the required fraction and stage 2 abstained. That pattern is OBSERVED. It is not a completed finding that the protocol makes answers worse, and it is not an improvement.

## 7. Failures and unresolved questions

- The shared Ollama server did not return 10 baseline bodies and 10 stage-2 bodies inside 180 seconds. Raising the timeout, editing the prompt, or replacing the timed-out trials would be a new experiment. This assignment does not authorize it.
- The first timeout coincided with a context-size unload. Later timeouts are unexplained one by one.
- The review turn can discard a correct first answer (A2, and E1's ungraded stage 1) and can restate a rejected number inside a counterargument line (E2).
- E1 stage 2 denied a fact the problem states: equal likelihood. Whether that is a stable misread is UNKNOWN beyond this one text.
- B2 and the D1 baseline are entangled with grader wording. The frozen scores were not corrected by hand.
- Production council behavior on these ten problems is UNKNOWN.
- Whether a completed run of this same protocol would clear 8/10 is UNKNOWN. The incomplete aggregates do not suggest it.

## 8. Further development

Not justified by this run. The comparison did not complete. The frozen aggregates do not clear the pilot thresholds. Completed pairs show the review turn reversing a correct refusal. No production integration is warranted. A later experiment would need its own authorization, a timeout that can survive shared Ollama, and a decision about the grader collisions above. This file does not start that experiment.

## 9. What was demonstrated and what was not

Demonstrated, under these laboratory conditions only:

- An isolated harness can call local `echo:latest` directly, freeze the protocol before generation, refuse a leaked grader phrase, count every send against a 30-call cap, store raw outputs, and grade them without production Echo, port 5000, memory, FAISS, or tool registration.
- At temperature 0, a second send of the same system-plus-problem messages reproduced the first text on all five items where both calls returned.

Not demonstrated:

- A measurable improvement on the five dimensions.
- The pre-registered thresholds (8/10, margin 2, four dimensions at 2/2).
- A valid baseline-versus-candidate comparison. Four baselines and one stage 2 never returned.
- Production council reliability, tool-use reliability, or an order-of-magnitude change in reasoning.
- That the two-stage review is harmless. On recorded pairs it sometimes reversed a correct first answer.

The file-fact retrieval result stays **NOT DEMONSTRATED**. It was not rescued here.

## Artifact hashes

VERIFIED by SHA-256 of the files on disk after the run. Freeze hashes match.

| File | SHA-256 |
|---|---|
| `protocol.json` | `e48a01336daed49a08fa05e9332dfadb50861e92b7917e5c802f45210ac020ea` |
| `problems.json` | `68d3b820b4fd211495be354593d9d714befb4f0098f56c5af6aaa38bd7f42fcb` |
| `grader.py` | `fa707a9abad7a072600c92fda6ec45c57e2c401004bcc7f6eebd69e61e2fb080` |
| `harness.py` | `017e7bf077d6b5c95c7704514d5dd4ef08711657bab388892a6890b162e69ec7` |
| `freeze.json` | `91dbc1cc8e4cb1d663af34109e57d84cea31ec4233d83919761d8d27993388f5` |
| `budget.json` | `2ddd2e178e0914860e36bd4d27eb9c20175594c0629293cc69ee9029a4565138` |
| `summary.json` | `84f1408f498e7447f75af17a8deefc2489d6e3649de02b547deb22e200f070ec` |
| `blind_package.json` | `945a9d9146b0a5fd7249734ad9b55b08b5312c5291bacedc05bab5d082c5c289` |
| `blind_key.json` | `a0027d5af3e695283653cd3ef9ab041ac3bfce385e07d8bce1180a88047a9e3a` |

Raw outputs, 30 files, preserved as written:

| File | SHA-256 |
|---|---|
| `raw/A1_baseline.json` | `061d0a10a743f715bd1e866fbf0c16e2a0b611a91a8e251ee3653d94e2de9996` |
| `raw/A1_stage1.json` | `9a21516916f940039e71efd9c7dd5a4beb935e854fbb596889bbdf1a400d3a86` |
| `raw/A1_stage2.json` | `92e47bdebf4ed9ad615615bdaae3aae672947c7b2ace5f0e6cf6dd63440d1618` |
| `raw/A2_baseline.json` | `eae27caef509de2ef4816285e68074f4fa40894250f3a73820b0f231c47e3c0b` |
| `raw/A2_stage1.json` | `ceecbb28f8796424913b1395c1f63256b9fc1d5256d70947b62f2ebdce18b899` |
| `raw/A2_stage2.json` | `e1d0492e15a16d9a3d9e40b993783b484643598de6c62fa936b712b38414de3d` |
| `raw/B1_baseline.json` | `4b1065e78bb57bbaaffdeab2b8ce98b6e6f051df97c8f7863126cec4b0e3974a` |
| `raw/B1_stage1.json` | `fa9b5957fd937b6f960b220956b693c7589ebcbbc0df748b34fbb92cdb27c84a` |
| `raw/B1_stage2.json` | `8b4def8997832e47562bf1c0747582cd382dfd7ca934b94446018eba6532bbd2` |
| `raw/B2_baseline.json` | `e5e5d1b88bda084ac534509bad6f38b5fb54ac3554e4da4dfb549418c499a7ee` |
| `raw/B2_stage1.json` | `e01c5dcc7e178ab3a7d14c68d9463fc48490f2c0d81a0edd7a2aad0ce522eede` |
| `raw/B2_stage2.json` | `0b0ca44904fa0496fc9bd6aaa082f99bca1fdbbb544d32d018bdeab6b5b59e01` |
| `raw/C1_baseline.json` | `8e8fe2d08fbd5eab5c52221de1c82092819d56961530a9f0c259d87ca7f68a1f` |
| `raw/C1_stage1.json` | `86a5eb0d00101a9d54dd7eb569ed9e0392a1d7123f15468c0fb9c8bac89f5d66` |
| `raw/C1_stage2.json` | `addd6e774e52d762bc1ba542438bfea071c3d3d139ecc6580d002f9630bd9aca` |
| `raw/C2_baseline.json` | `c44cac40548ac8ff60339a204655e07c9a0265efff8147ab2c4699d8ff4095df` |
| `raw/C2_stage1.json` | `3d509c7a513fb8ac27b2649d93ce575714c93b23002d60292bfc935205ee41cb` |
| `raw/C2_stage2.json` | `bea33969fa29388553b89de8570aa430e1337f136af0076dfa8a6a9281024291` |
| `raw/D1_baseline.json` | `0cdd01d964252720776942aa0a65915efbbc9d91e01144a13bfba3b127fe0886` |
| `raw/D1_stage1.json` | `5acb392286cf39886b647b52f7c6f5d2da766b0890e02919681cec55fdc8a8d8` |
| `raw/D1_stage2.json` | `8dea9e47d82a3ac8a0aac1f845084df84f94a4649c067993b86c98cd94085801` |
| `raw/D2_baseline.json` | `89ded7f6ba321834db9710c5b433a997f3aba09bef0e0de59bcac365bafe5dce` |
| `raw/D2_stage1.json` | `bf270784df320e43c2946c8cc6dcfc55a86c0f89bf2e1822fb139b89f056dac6` |
| `raw/D2_stage2.json` | `3af5592839da49995916c0608ce047d7e180e5d91becc5f0ca08ce6412eea100` |
| `raw/E1_baseline.json` | `13c9e3b7a12ce67d5e3498965777742e430a6e1f418ebd95416a9bb126484592` |
| `raw/E1_stage1.json` | `4468b219f6e4995f72a056d21cae34b60ac161fc724914e4a968518946837c37` |
| `raw/E1_stage2.json` | `2907aeddb3e378f8cc7def004e71f8c019a8a42e9021c5472236b06badc14471` |
| `raw/E2_baseline.json` | `5f7462e316f02294c268cd7fa2b36f1aa36219e2296f7655f4eaa09fbeddebe4` |
| `raw/E2_stage1.json` | `417a64dbfba6239b1b802f7c8dd08c0231f509f4a7c89a24f9a8fd229445fbd8` |
| `raw/E2_stage2.json` | `4aa5d1cbbba39d26d3684e5e978600946175281e65a6fb5f4f5f08d97beee5da` |

## Decision

**C. EXPERIMENT NOT COMPLETED**

The environment prevented a valid comparison. Four baseline generations and one stage-1 generation hit the 180 second client timeout on the shared Ollama server. D1 stage 2 was skipped and not replaced. The frozen grader's 4/10 versus 3/10 figures include those empty texts. They are not a completed pilot, and they do not meet the pre-registered thresholds.
