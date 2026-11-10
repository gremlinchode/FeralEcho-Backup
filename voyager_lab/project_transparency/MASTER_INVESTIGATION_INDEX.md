# Master investigation index

Audit package date: 2026-11-08 (session calendar). This index records what was found. It does not re-run any experiment.

Worktree: `project-voyager` at `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. Remote: `git@github.com:gremlinchode/FeralEcho-Backup.git`. `voyager_lab/` is untracked.

## How counts work

Two numbers are easy to mix. They stay separate.

**Discovered** means a file, package, or index row was located. Discovery is not a result.

**Assessed from primary evidence** means this audit opened the report, the frozen summary, or the cited source passage and wrote a classification from that text. Passing tests are not treated as proof of a broader capability. A design document is not treated as an implementation.

This audit assessed **6 campaigns** from primary evidence and classified **13 claims** inside them. It inventoried **38** index threads (E-001 through E-038) from `research/EXPERIMENT_INDEX.md` without re-opening those reports, except for one paragraph in the 2026-09-02 architectural self-knowledge file (see L1 and L2). It counted **539** files under `audits/`, **15** entries under `research/` (14 Markdown files plus one `.sha256`), and **26** packages under `app/experiments/`. Those corpora were listed. Their bodies were not re-read as a set.

The index author’s own header says `audits/` held 185 files “as of this pass.” This audit’s file count is 539. Both figures are kept. This audit did not reconcile which files the earlier author excluded.

Status words inside E-001–E-038 (`CONFIRMED`, `NULL`, and the rest) are the index author’s words. They are not this audit’s labels.

This audit’s labels, used only on the 13 claims, are:

`DEMONSTRATED`, `PARTIALLY DEMONSTRATED`, `NOT DEMONSTRATED`, `EXPERIMENT NOT COMPLETED`, `FAILED`, `UNKNOWN`, `PROPOSED ONLY`.

## Tier A — assessed from primary evidence

### A1. Frozen Voyager 25-mission evaluation

1. **Name.** Frozen Voyager 25-mission evaluation.
2. **Location.** `voyager_lab/ASSESSMENT.md`, `voyager_lab/README.md`, `voyager_lab/results/summary.json`, `voyager_lab/results/RESULTS.md`, `voyager_lab/voyager/engine.py`, `voyager_lab/voyager/worker.py`, `voyager_lab/voyager/procedures.py`. Rubric lock named in `voyager_lab/README.md`. HEAD context: untracked laboratory on `project-voyager`.
3. **Purpose.** Measure a small mission controller on a toy filesystem: carry a script across a killed process, follow a multi-step template, switch after a controlled fault, stop on a budget or an unknown read, and keep an outside-checkable record.
4. **Hypothesis or objective.** A deterministic engine with saved procedures would beat a weaker baseline on the frozen suite, including recovery, restart, required abstention, and an unfamiliar pair (M19/M20).
5. **What was implemented.** A Python standard-library controller. `procedures.py` states that the grammar is fixed and is not a language-model reading of the objective sentence. Templates include `copy_value`, `pipeline_sum`, `fold_lines`, `make_then_write`, `resolve_conflict`, and `join_pair`. `join_pair` reads two slots, joins them, and writes. The worker brief receives id, objective, problem class, budget, and slots. Grade, world, and success check stay outside the worker. The lab does not import FeralEcho, does not call Ollama, and does not write production memory (`voyager_lab/README.md`).
6. **What was tested.** One official frozen run, recorded in the assessment as 2026-11-08. Three arms: baseline, engine, ablation. Twenty-five missions. `run_experiment.py --run` refuses if `results/summary.json` or `results/raw/` already exists.
7. **What the results demonstrated.** Read from `voyager_lab/ASSESSMENT.md` (observation table, not a new measurement): baseline 2/25 (0.08), engine 23/25 (0.92), ablation 20/25 (0.80). Unsupported completion claims: baseline 23, engine 1 (M20), ablation 0. Successful recovery M07–M10: baseline 0/4, engine 4/4, ablation 4/4. Repeated failed operations: baseline 7, engine 0, ablation 0. Restart recovery M05/M06/M23: baseline 0/3, engine 3/3, ablation 3/3. Abstain when required: baseline 0/4, engine 4/4, ablation 4/4. Tool calls 62 / 73 / 70. Elapsed milliseconds about 1424 / 1414 / 1411. The direct answer in the assessment: the prototype can carry a scripted mission across a killed process, order a multi-step template, switch after a controlled fault, stop on budget, human gate, or unknown read, and keep an outside-checkable record.
8. **What the results failed to demonstrate.** The engine did not improve the unfamiliar pair as a learned skill. M19 and M20 share the public sentence “Read a and b and write them joined by a hyphen,” class `join_pair`, and hypothesis `copy_value`. The hidden grade differs: M19 expects the text `8-1`; M20 requires abstention. Both engine and ablation pass M19 with learning label `none` and 4/4 tool calls. That pass is the prewritten `join_pair` procedure. It does not establish an independently learned Echo capability. Echo, the language model, was not in the loop. M20 engine fails with status success, value `4-4`, label `remember`, and one unsupported-completion flag. M20 ablation passes with status `blocked` and 3/3 tool calls. That pass is budget exhaustion before a write. It is not intelligent abstention. Lessons lowered the unfamiliar rate from 1.0 (ablation 2/2) to 0.5 (engine 1/2). M24 policy non-repeat: baseline passes; engine and ablation fail. M25 composition existed in `procedures.py` before the run. Ablation misses M14, M15, M16, M24, and M25.
9. **Known limitations.** The controller receives `problem_class` and does not interpret the objective sentence. `remember` is path-map equality. Saved procedures on M14 and M16 are not new classes. The filesystem is a toy. Child `resources.elapsed_ms` is 0; parent time is the figure to use. No production integration was authorized. The run is sealed: a second `--run` is refused while results exist.
10. **Status.** Frozen. Complete as a sealed measurement. Not a license to extend the controller.
11. **Production or laboratory.** Laboratory only.
12. **Primary evidence.** `voyager_lab/ASSESSMENT.md`, `voyager_lab/results/summary.json`, `voyager_lab/voyager/procedures.py`, `voyager_lab/README.md`.

Classified claims inside this campaign: V1 `PARTIALLY DEMONSTRATED`, V2 `NOT DEMONSTRATED`, V3 `NOT DEMONSTRATED`, V4 `NOT DEMONSTRATED`. V5 is the separate CAB document.

### A2. Capability-arbitration broker (CAB) review

1. **Name.** CAB adversarial review.
2. **Location.** `voyager_lab/CAB_ADVERSARIAL_REVIEW.md`.
3. **Purpose.** Decide whether a proposed broker, meant to hide grades from a worker and route unfamiliar missions, was good enough to implement, and whether a follow-on experiment E1 was good enough to run.
4. **Hypothesis or objective.** A broker could sit between grader and worker so the worker would abstain or proceed without being told the grade.
5. **What was implemented.** A design review. No broker was added to `voyager/engine.py` or `worker.py`. This audit read the opening and the closing verdict in a prior pass. Sections 2–10 of the review were not re-read line by line in this writing pass. The verdict below is taken from the review’s own close, not re-derived.
6. **What was tested.** Document review against the frozen suite’s M19/M20 shape. No new mission run.
7. **What the results demonstrated.** The review’s executive verdict: CAB is not good enough to implement, and E1 as specified is not good enough to run. The proposal is a deterministic lookup. It is not task understanding. A broker that is told `grade_kind=abstain` has been told the answer.
8. **What the results failed to demonstrate.** Section 12 of the review lists what the proposal does not demonstrate. This audit does not expand that list beyond the verdict already recorded. M24 stays unsolved in the review’s unresolved list. No loss function for quarantine is specified. A grade-kind hide-list gap must not be closed by editing the hashed `worker.py`.
9. **Known limitations.** Same-session self-review. The review itself says that is weaker than a fresh investigator. Middle sections were not fully re-read in this consolidation.
10. **Status.** Complete as a rejection of the proposal. Awaiting no implementation. Implementation remains unauthorized.
11. **Production or laboratory.** Documentation-only proposal beside the laboratory. Not in production.
12. **Primary evidence.** `voyager_lab/CAB_ADVERSARIAL_REVIEW.md`.

Classified claim: V5 `PROPOSED ONLY`.

### A3. ScratchWriter security investigation

1. **Name.** ScratchWriter, original writer and pinned writer.
2. **Location.** `voyager_lab/scratch_write/` including `SECURITY_REPORT.md`, `IMPLEMENTATION_AND_VERIFICATION_REPORT.md`, `FINAL_SECURITY_DESIGN.md`, `pinned_writer.py`, `confine.py`, `write_file.py`, `verify_file.py`, `tests/test_scratch_write.py`, `tests/test_pinned_writer.py`, and `evidence/` (`MANIFEST.json`, `README.md`, T1/T8/T2 JSON and scorer notes). T2’s live directory was located under the system temp path and was not copied.
3. **Purpose.** A scratch-only file writer with a narrow confinement claim, then a separate pinned-root writer after the first interface accepted a caller-supplied root.
4. **Hypothesis or objective.** Writes could be confined to an authorized scratch root using open flags, `F_GETPATH`, and a protected-path list, well enough to describe a laboratory security property.
5. **What was implemented.** macOS-specific writer using `O_NOFOLLOW`, `O_DIRECTORY`, `O_EXCL`, `O_CLOEXEC`, and `F_GETPATH` (1024-byte buffer, later corrected from a larger byte request in the implementation record). The original `write_file` still accepts a caller root. The pinned interface does not take that root from the caller. Not added to Echo’s tool list. No subprocess import into production dispatch.
6. **What was tested.** Original suite, recorded 2026-11-08, macOS, Python 3.13. Run 1: 56 tests, 55 ok, 1 failure in `test_c_failure_temp_cleanup` (`st_nlink` expected 1, observed 2, because the temp name was left on purpose and the destination link count was 2). The security result was not flipped; the helper was replaced with a direct read that keeps mode and content and allows `nlink >= 2`. Run 2: 56 tests, 0 failures, about 0.176 seconds, no `SCRATCH_WRITE_NOTES`. Later authorized checks: T1 root substitution, T8 protected paths, T2 live rename. Scorer mismatches were preserved and were not counted as behavioral passes.
7. **What the results demonstrated.** Run 2 is a clean pass of the 56-test suite after the assertion helper was corrected. T1: three `TypeError`s when a root was supplied to the pinned interface; escape and absolute-outside-pin recorded false; a canary inode stayed unchanged; the legal file landed only inside the pin. T8: ten refusals; zero `os.open` of a protected path. Production files were recorded untouched for the T8 window. Later movement of FAISS or `memory_meta` after that window, while a live server was running, is an inference about the server’s own writes. It is not a T8 failure.
8. **What the results failed to demonstrate.** The original caller-controlled root is not a confinement boundary: a caller who can pass the root chooses the boundary. The pinned writer’s tests do not prove security against every attack. A caller that already has its own write privilege can bypass the API. The protected-path list is local. The rename-after-`F_GETPATH` race was not hammered. A killed process can leave `.swtmp_*` files and a partial audit line. Cross-process overlap was not executed. `F_GETPATH` and the 1024-byte buffer are Darwin-specific. APFS case-fold and NFC/NFD behavior were measured on this machine only. The audit log is unbounded. Parent `fsync` is best-effort. Nested-path temp cleanup was outside the authorized set. Integration was not authorized and was not done.
9. **Known limitations.** Check-to-syscall (TOCTOU) and concurrency limits remain open. Scorer errors are bookkeeping defects, not extra passes. This is a laboratory program, not an Echo capability.
10. **Status.** Complete as a laboratory security result. Frozen in the sense that this audit did not modify it and integration stays unauthorized. The older root-accepting function still exists beside the pinned interface.
11. **Production or laboratory.** Laboratory only.
12. **Primary evidence.** `voyager_lab/scratch_write/SECURITY_REPORT.md` and the evidence JSON files named in that report. Hashes recorded with the evidence package: T1 `3f1ca84ef0434129eeba50d17a39fda7c8393c7e483eaf6cffaf5c056a8bb8f0`; T8 `a1f668d7a6f0223875b7d2894365045e6380490642921c4885cb80688868edd6`; T2 `94d183397af92b8f55b22ad71bfa2d379c07dc6e01339374183e93f141c434e5`; T8 scoring-bug note `aa7b85d37e736699104af2b6e95fbeba093f5759cb4bfe90c589cfb7db9be6f2`; T2 scorer-mismatch note `81ab8602fdc63ec514b9cf9a33da2c562d3462989fc0db6243ee95db4544f07e`. Code hashes are in `ECHO_SOURCE_MAP.md`.

Classified claims: S1 `FAILED` (original root-accepting interface as a confinement boundary), S2 `PARTIALLY DEMONSTRATED` (pinned writer on the authorized tests), S3 `NOT DEMONSTRATED` (production capability or complete security proof).

### A4. Ungated file-fact retrieval

1. **Name.** Ungated file-fact retrieval.
2. **Location.** `voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md`, `voyager_lab/UNGATED_FILE_RETRIEVAL_POSTMORTEM.md`, `voyager_lab/ungated_file_retrieval/`, `voyager_lab/CAPABILITY_GAP_AND_NEXT_EXPERIMENT.md` (the note that recommended a run and did not itself authorize one).
3. **Purpose.** Ask whether `llama3.1:8b`, given a confined `read_file` and a prompt that contains none of the 32 production dispatch-trigger phrases, will call the tool for an unknown file line and return that line exactly.
4. **Hypothesis or objective.** Candidate arm A would pass at least 5 of 6, scaffold arm B at least 5 of 6, no-tool arm C would score 0 of 6 exact, and a static gate would be 12 of 12. An Echo characterization arm D (`echo:latest`, no tools, same candidate prompt) was descriptive only.
5. **What was implemented.** An isolated harness. It does not call production `echo_query` or production dispatch. Conditions A and B offer tools. The model must emit the tool call. Pass for A and B requires exactly one valid `read_file`, a matching path, tool bytes equal to the file, and `answer.strip()` equal to the expected line. Quote wrapping fails. A diagnostic that the expected line is contained in the answer is not a pass. The gap note’s recommendation GO is not the official result. The later run closed the question.
6. **What was tested.** Four conditions times six trials. Twenty-four planned generations, hard maximum 30 local Ollama calls. Static gate: 12 of 12 by direct function call; worktree source hash matched the production file that was compared at the time. Model HTTP: 30 of 30. `voyager_lab/ungated_file_retrieval/summary.json` records `finished_at` `2026-11-09T04:34:13.761873+00:00`. The narrative report does not need to be treated as a second clock. Summed `total_duration` about 17.28 seconds. Summed `eval_count` 617. All `done_reason` stop. D01–D06 were not run (`call_budget`).
7. **What the results demonstrated.** On A01–A06 and B01–B06, each trial executed exactly one `read_file` of the assigned file. Path match and byte match were true on all 12. The static gate was 12 of 12. Arm C scored 0 of 6 exact and fabricated generic lines, with no leakage of the secret hex into those answers. Retrieval of the assigned bytes, in this harness, with this model, on these 12 trials, happened.
8. **What the results failed to demonstrate.** Official scores: A 0/6, B 0/6, sole reason `answer_not_exact`. Official label: **NOT DEMONSTRATED**. Eight final answers kept the correct line inside extra prose. Four finals (A01, A05, B02, B05) replaced the line with the sentence `This is a test line.`, which is absent from the prompts, the harness, the schemas, and the fixtures. No established cause for those four substitutions was found. Truncation was disproven. The flag `first_request_contains_expected: true` was disproven as first-request contamination. `contamination_exact_or_contained` on the eight contained answers means the retrieved bytes were used inside extra prose. It is not a leak grade and it is not an official pass. Arm D was not measured. A 12/12 tool-and-bytes result is not a substitute for the official exact-answer score. The postmortem section 8 recommendation is STOP. The experiment was closed without further tuning.
9. **Known limitations.** One model (`llama3.1:8b`), one harness, six files, temperature 0, `num_ctx` 4096, `num_predict` 256, timeout 120 seconds. The production dispatch system prompt was not the prompt under test. Server-side presentation of the tool role inside Ollama’s template was not verified. The four substitutions have no causal assignment. Class 4 (a delivery failure between tool result and answer) was not assigned. Class 7 (a logging defect: shared message list and a missing round-2 `prompt_eval_count`) did not cause the grade.
10. **Status.** Complete and closed. Official result stands. Not authorized to retune.
11. **Production or laboratory.** Laboratory only. The static gate compared a hash to production source. The run did not go through port 5000 or production dispatch.
12. **Primary evidence.** `voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md`, `voyager_lab/UNGATED_FILE_RETRIEVAL_POSTMORTEM.md`, per-trial records under `voyager_lab/ungated_file_retrieval/`.

Classified claims: R2 `DEMONSTRATED` (assigned-file tool call and bytes, 12/12, narrow), R1 `NOT DEMONSTRATED` (official exact-line task).

### A5. Reasoning reliability pilot

1. **Name.** Reasoning reliability pilot.
2. **Location.** `voyager_lab/REASONING_RELIABILITY_REPORT.md` and `voyager_lab/reasoning_reliability/` (`protocol.json`, `problems.json`, `grader.py`, `harness.py`, `summary.json`, `budget.json`, `freeze.json`, `raw/`, blind package and key).
3. **Purpose.** Compare a single-pass baseline with a two-stage answer-plus-review candidate on five pre-registered dimensions, under a 30-generation budget, with a frozen grader and no LLM-as-judge.
4. **Hypothesis or objective.** The candidate would show a demonstrated improvement: a completed 10-versus-10 comparison, candidate score at least 8, margin at least 2, at least 4 dimensions at 2 of 2, and no fabricated items. The five dimensions are assumption detection, intellectual opposition, evidence discrimination, evidence-driven self-correction, and confidence calibration.
5. **What was implemented.** A harness around local Ollama. Baseline is one generation of `echo:latest` with Modelfile identity only plus the problem. It is not the production council. Candidate stage 1 uses the same shape. Stage 2 appends the stage-1 answer and a frozen review turn ending in CONCLUSION, ASSUMPTIONS, COUNTERARGUMENT, EVIDENCE, REVISION, UNCERTAINTY. The graded candidate text is stage 2 only. Banned tokens in the review turn include `3/4`, `S2`, `free verse`, `2.0 kg`, and `does not support`. Options: temperature 0, `num_ctx` 4096, `num_predict` 640, timeout 180 seconds, stream false, no retries. `decide()` returns demonstrated improvement only when `completed_comparison` is true and the numeric gates above all hold. `completed_comparison` requires every baseline and every stage-2 response to be HTTP 200, error none, and not skipped.
6. **What was tested.** Five problems, A–E, two items each. Budget 30. Used 29. `frozen_at` `2026-11-09T05:17:33.457005+00:00`. `finished_at` `2026-11-09T06:07:51.915140+00:00`. Wall clock about 3018 seconds. Exit 0. Stdout recorded `OUTCOME EXPERIMENT NOT COMPLETED baseline=4/10 candidate=3/10 calls=29`.
7. **What the results demonstrated.** The harness ran and the freeze held. Baseline HTTP 200 on A2, B1, B2, C2, D1, E2. Timeouts at 180 seconds with empty text on A1, C1, D2, E1, scored fail. Stage 1 HTTP 200 on 9 of 10; D1 stage 1 timed out. Stage 2 HTTP 200 on 9 of 10; D1 stage 2 skipped because stage 1 failed. Frozen passes: baseline A2, B1, C2, E2; candidate stage 2 B1, C2, D2. Where both baseline and stage 1 returned HTTP 200 (A2, B1, B2, C2, E2), the texts were byte-identical. The first timeout coincided with `ollama ps` showing `echo:latest` stopping at context 8192 while the lab requested `num_ctx` 4096. That coincidence supports a shared-server explanation for the first timeout only. Later timeout causes are unknown. Specific review effects that were read: A2 stage 2 reversed a pass and affirmed that a bug was fixed. E1 stage 1 said 3/4; stage 2 abstained after treating “equally likely” as unsupported. E2 stage 2’s conclusion says unknown, while COUNTERARGUMENT contains “the probability of drawing a red token is 50%,” and the frozen regex fails. D1 baseline prose says the cure conclusion “is not supported” and names an untreated control, but the withdraw list contains “does not support” and not “is not supported,” so the frozen score stays fail. B2 on both arms misses the grader’s exact phrase list (a false negative). These were not rescored.
8. **What the results failed to demonstrate.** Official label: **EXPERIMENT NOT COMPLETED**. `completed_comparison` is false. Model generations 29, budget 30, margin −1. Printed aggregates 4/10 and 3/10 include empty timeout texts. They are not a valid comparison. The protocol required 10 completed baselines and 10 completed stage-2 answers. This run has 6 and 9. `dimensions_at_2_of_2` is 0 and 0. Fabricated-item lists were empty, which does not rescue the outcome. No reasoning improvement can be claimed. An extra review pass reversed at least one initially correct answer (A2) and changed another correct stage-1 answer into an abstention (E1). That is evidence that a second pass can make a graded answer worse. It is not evidence that the underlying hypothesis is false. The unused 30th slot (D1 stage 2) stays unused.
9. **Known limitations.** Shared Ollama with whatever else was loaded. One model field, `echo:latest`. Frozen string match, including the D1 and B2 false-negative shape, which this audit did not “fix.” Prototype not integrated. Not authorized to retune, raise the timeout, or rerun.
10. **Status.** Closed. Experiment not completed. Report hash at this audit: `ee3830b5e92a886420dc0e3ee0264a38fcfe5bc5ac48e3d637ecfef0b4834f0a`.
11. **Production or laboratory.** Laboratory only. Baseline is not the production council path.
12. **Primary evidence.** `voyager_lab/REASONING_RELIABILITY_REPORT.md` and `voyager_lab/reasoning_reliability/summary.json`.

Classified claim: Q1 `EXPERIMENT NOT COMPLETED`.

### A6. `log_thought` name, tool, and missing conversation

1. **Name.** `log_thought` observation.
2. **Location.** Production tool: `app/core/echo_tool_dispatch.py` (`read_file`, `search_memory`, `log_thought`; dispatch model `llama3.1:8b`; thought log `memory/thought_log.jsonl`). Laboratory non-use: retrieval report (arms A and B offered `log_thought` and `search_memory`; the report says they were not called). Documented different episode: `audits/2026-09-02_architectural_self_knowledge_investigation.md` section 6.A. Search for an “unnecessary proposed invocation” conversation: no Markdown match for that pairing in this audit’s search. `audits/2026-07-18_echo_self_awareness_probe.md` had no `log_thought` hit in the search that was run.
3. **Purpose.** The assignment asked for the conversation in which Echo proposed `log_thought` without a need to log, including what Echo was told, what it answered, and how it later explained the name.
4. **Hypothesis or objective.** None was pre-registered in the repository for that specific conversation. The assignment treats it as a preliminary observation.
5. **What was implemented.** A real production tool that appends a thought line and is isolated from FAISS, retrieval, sync, and prompt injection. A laboratory stub name offered by the retrieval harness and not called. No new tool was registered by this audit.
6. **What was tested.** Source read of the dispatch header and the project-root guard. Grep of the 2026-09-02 audit. A repository search for the unnecessary-invocation episode. The original quoted question, the model’s reply, and a later self-explanation were not found.
7. **What the results demonstrated.** The production identifier `log_thought` is a real tool name in `echo_tool_dispatch.py`. It is not an unverified string at the source level. The 2026-09-02 paragraph, which this audit did read, says Echo was asked for a real code snippet, anchored on the real function name, invented a plausible-but-wrong path and format, and omitted the memory-isolation contract. The audit’s own summary is “correct name, invented substance.” That paragraph does not quote the full user turn or a later self-explanation. The retrieval harness recorded zero calls to `log_thought`.
8. **What the results failed to demonstrate.** No execution of a proposed unnecessary `log_thought` call was established, because the conversation was not found. Echo’s subsequent explanation was not found. A self-explanation, had one been present, would not by itself prove where the name came from. The 2026-09-02 paragraph must not be upgraded into that missing conversation. Section 6.B of the same audit, `run_self_model_reflection()` writing unverified architecture text into vector memory, is a different path and was not re-tested.
9. **Known limitations.** Source inaccessible for the specific episode. One audit paragraph is not a transcript. Dispatch behavior on the live server was not re-contacted.
10. **Status.** The missing conversation remains unknown. The 2026-09-02 paragraph is a recorded audit finding, not a new replication.
11. **Production or laboratory.** The tool definition is production source. This audit did not call it. The retrieval non-use is laboratory. The 2026-09-02 text is an audit document.
12. **Primary evidence.** `app/core/echo_tool_dispatch.py`; `audits/2026-09-02_architectural_self_knowledge_investigation.md` (paragraph at the `log_thought` case); `voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md` for the unused stub.

Classified claims: L1 `UNKNOWN` (the unnecessary-invocation conversation). L2 `PARTIALLY DEMONSTRATED` (the 2026-09-02 “correct name, invented substance” paragraph exists and was read; the original transcript was not recovered).

## The 13 classified claims

| ID | Claim | Label |
|---|---|---|
| R2 | In the retrieval harness, `llama3.1:8b` emitted one `read_file` of the assigned file on 12 of 12 A/B trials, and the tool returned the file bytes. | DEMONSTRATED |
| V1 | The Voyager engine completed 23 of 25 toy-filesystem missions as a controller, including recovery and restart behaviors described in the assessment. | PARTIALLY DEMONSTRATED |
| S2 | The pinned ScratchWriter passed the authorized T1, T8, and post-fix suite checks that the security report records. | PARTIALLY DEMONSTRATED |
| L2 | A 2026-09-02 audit paragraph records “correct name, invented substance” for `log_thought`. The original transcript was not recovered. | PARTIALLY DEMONSTRATED |
| S1 | The original ScratchWriter, which accepts a caller-controlled root, fails as a confinement boundary. | FAILED |
| Q1 | The reasoning protocol improved graded answers under its own success rule. | EXPERIMENT NOT COMPLETED |
| V2 | Echo, the language model, planned the Voyager missions. | NOT DEMONSTRATED |
| V3 | Voyager M19 shows an independently learned Echo skill. | NOT DEMONSTRATED |
| V4 | Voyager M20 ablation is intelligent abstention. | NOT DEMONSTRATED |
| S3 | ScratchWriter is a production Echo capability or a complete security proof. | NOT DEMONSTRATED |
| R1 | Ungated file-fact retrieval returned the exact line often enough to meet its rule. | NOT DEMONSTRATED |
| V5 | CAB, as reviewed, is a design that this audit does not treat as implemented. | PROPOSED ONLY |
| L1 | A specific conversation proposed an unnecessary `log_thought` call, and Echo’s later explanation identifies the cause. | UNKNOWN |

Counts: DEMONSTRATED 1, PARTIALLY DEMONSTRATED 3, FAILED 1, EXPERIMENT NOT COMPLETED 1, NOT DEMONSTRATED 5, PROPOSED ONLY 1, UNKNOWN 1. Total 13.

Design notes whose bodies were not fully re-read in this writing pass — `voyager_lab/FIRST_LOCAL_SKILL_RESEARCH.md`, `voyager_lab/CAPABILITY_ACQUISITION.md`, and the working-self design outside the repo — are not extra `PROPOSED ONLY` rows in this table. They are listed in Tier C so the count stays honest.

## Tier B — E-001 through E-038, index-reported, not re-verified

Source for every row: `research/EXPERIMENT_INDEX.md`. Purpose, hypothesis, implementation, tests, and results below are the index author’s summary. This audit did not open the cited audit files to confirm them, except the single `log_thought` paragraph under E-005’s family (see A6). “Failed to demonstrate” is filled only where the index itself states a negative, a partial, a falsification, or an explicit limit. Otherwise this audit does not invent a gap.

Shared fields for the whole tier:

- **Location.** `audits/` plus the report filename in the index. Paths are relative to `audits/` unless noted.
- **Production or laboratory.** Mixed historically. This audit did not change production. E-025 is described by the index as a production change made in that earlier session. This audit did not re-check that it is still the live code.
- **Primary evidence.** The report path in the index row. Depth disclosure in the index header: E-030 onward first-hand for that author; 1–8 September terminal or FINAL; pre-September titles only.
- **Status for this audit.** Inventoried. Not re-measured. Do not add these rows to the 13-claim totals.

| ID | Index status | What the index says was found | What the index itself withholds |
|---|---|---|---|
| E-001 | CONFIRMED | 2026-07-18 self-awareness probe; 6 findings; 5 fixes the same session. | Title-derived for that author. |
| E-002 | CONFIRMED with corrections | Differential audit; KMP crash count corrected 1→5→9→20 across later notes. | Title-derived. |
| E-003 | CONFIRMED | Emergence mechanisms mostly real, inputs near-constant. | Title-derived. |
| E-004 | NULL (underpowered) | Memory ablation n=30; no distinguishable effect. | Does not prove memory never matters. 29/30 prompts were personal in the longer Finding 76 record, which this audit did not re-compute. |
| E-005 | PARTIALLY REPLICATED | Architectural self-knowledge fixes; 7 files. | Not a claim that self-knowledge is now reliable. The `log_thought` paragraph is L2, not a new result. |
| E-006 | CONFIRMED | Echo-to-Echo 403 storm from a missing shared secret. | Index claim. Not re-counted. |
| E-007 | CONFIRMED, supersedes near-zero | Self-modify chain 426/463 (about 92%). | Fitness gate was saturated (the index points at R-004). |
| E-008 | SUPERSEDED by Finding 91 | Quality metric could not discriminate. | The supersession is `CLAUDE.md`’s claim. Not re-measured on backups. |
| E-009 | UNRESOLVED | Agency architecture file exists. | Terminal report not deep-read by the index author. |
| E-010 | IN PROGRESS | Preference-provenance protocol frozen at P0.1. | Index says no live trial as of Finding 86. Package `app/experiments/preference_provenance/` exists. Contents not inspected here. |
| E-011 | UNRESOLVED | Measurability and longitudinal audit. | Title-level. |
| E-012 | CONFIRMED | Public-sharing review; two blockers; do not publish as-is. | Matches Finding 90 as a document. Repo visibility was not re-checked with GitHub in this audit beyond a five-issue list that returned no rows. |
| E-013 | UNRESOLVED | 27-day phase 0 map. | Title-level. |
| E-014 | UNRESOLVED | Phase 6 red-team. | Title-level. |
| E-015 | CONFIRMED | Findings 91/93 revalidation: KEEP, and KEEP WITH QUALIFICATIONS. | Not re-run. |
| E-016 | UNRESOLVED | Architecture A hot-stove proof. | Title-level. Package directory exists. |
| E-017 | UNRESOLVED | First learning loop, several phases. | Title-level across most phases. |
| E-018 | CONFIRMED, load-bearing | An authoritative flag changes the answer by making generation trust the flag. | Not re-run. |
| E-019 | CONFIRMED negative | Generation-time epistemic revision 0/5 after a rendering fix. | Does not by itself prove the hypothesis false for every phrasing. |
| E-020 | PARTIALLY REPLICATED | Living self-model: storage half described as closed; belief revision not. | Not re-tested across a restart by this audit. |
| E-021 | DESIGN | Persistent self-model design, superseded into E-020. | A design is not an implementation. |
| E-022 | UNRESOLVED | Self-transparency audit. | Title-level. |
| E-023 | CONFIRMED design-only | Git read-only self-history. Not implemented in that investigation. | Later commits `e5acbb0` and `ea22d75` exist in git history. This audit did not re-read them as a finished Git tool. |
| E-024 | CONFIRMED | Camera and microphone path reduced to a few scalar floats; no semantic content in that trace. | Not a new sensor test. |
| E-025 | CONFIRMED production change | Sensory gate fix in that session. | This audit did not re-verify the live gate. |
| E-026 | CONFIRMED as design input | Exhaustive sensor contract. | Design input, not a capability. |
| E-027 | CONFIRMED | Epistemic boundary versus imagination; index says H2 supported. | Not re-run. |
| E-028 | FALSIFIED prior readiness | Condition C did not survive the pressure ladder. Prior “ready to implement” was revoked. | Falsifies that readiness claim. Does not answer every related question. |
| E-029 | CONFIRMED | Precedent times role-play interaction; recovery partial. | Not re-run. |
| E-030 | CONFIRMED | 2×2 factorial 0/6 versus 6/6. Relay rides `GET /projects/file`. No MCP in that account. | Not re-run. |
| E-031 | PARTIALLY REPLICATED | Transition mechanism; several findings later revised at higher n. | See E-032. |
| E-032 | CONFIRMED corrections; partial scale | 43 trials versus the requested scale. Two earlier findings reversed. | Not the full requested n. |
| E-033 | CONFIRMED | Plain evidence instructions at least matched a full taxonomy. Provenance clarity: identical 3/3. | Small cells. Not re-run. |
| E-034 | CONFIRMED, load-bearing | 52/52 held under passive conditions. Pressure transition 5/10 to 9.5/10. False verification 4/5 under the trap. | Passive success is not pressure success. |
| E-035 | REPLICATED with qualification | Primary 15/20. Pooled sensor 25/36. Filesystem/git 3/10. | Domain-dependent. Not universal. |
| E-036 | Domain-dependent; authority-specificity left open in this row | September research Mission 19. 264 trials. Two-turn violation about 13.3%. Ten-turn ladder factual capture 3/3. | Not Voyager M19. The index points authority-specificity at E-037 and also says Q-008 was unresolved at the time of the E-036 writeup. |
| E-037 | Replicated accumulation; narrow exploratory authority effect | September research Mission 20. 222 trials. Index says authority is not required for capture; all four conditions accepted the false claim by L1–L3; 9/9 non-authority at L1. Recovery 12/12 honest verification-status admissions; none spontaneously re-derived the true value. | Not Voyager M20. Bodies of the report and of Q-008 were not re-read. `research/OPEN_QUESTIONS.md` still has a Q-008 heading. This audit does not close Q-008. |
| E-038 | CONFIRMED mostly healthy, plus one then-live defect | Defect audit. Index says a live query saw 50 liveness checks, and `echo_projects_autonomy` had been silent 65.9+ hours. | Those two figures are 2026-09-11 observations. This audit did not query liveness and does not treat either figure as current. |

## Tier C — located, not assessed as results

### Voyager documents beside the frozen run

| Item | Location | This audit’s stance |
|---|---|---|
| Capability gap note | `voyager_lab/CAPABILITY_GAP_AND_NEXT_EXPERIMENT.md` | Dated 2026-11-08. Read in part. Recommends GO on ungated file-fact retrieval and says the note itself does not authorize a run. The later official result is NOT DEMONSTRATED. The note also labels conversation as model-native for ordinary replies without a new quality measurement, the keyword gate and the three tools as scaffolding, dispatch-prompt compliance as unknown at that time, the Voyager engine as scaffolding, and ScratchWriter as a lab program. |
| First local skill research | `voyager_lab/FIRST_LOCAL_SKILL_RESEARCH.md` | Present. Body not re-read. Prior project rule: design only; the skill experiment stays unauthorized. Not added to the PROPOSED ONLY count. |
| Capability acquisition | `voyager_lab/CAPABILITY_ACQUISITION.md` | Present. Body not re-read. Not modified. |
| Rubric freeze | `voyager_lab/RUBRIC_FREEZE.json` | Present. Bundle hash recorded in the history and the final report. Not a result by itself. |
| Reasoning and retrieval freezes | Under `voyager_lab/reasoning_reliability/` and `voyager_lab/ungated_file_retrieval/` | Present. Official reports already cover them. Not re-executed. |

### Research files whose bodies were not the basis of a new classification

Read earlier in this investigation and used as secondary summary, not re-executed: `research/CURRENT_STATE.md`, `research/FINDINGS.md` (R-001 through R-011), `research/EXPERIMENT_INDEX.md` (full), `research/OPEN_QUESTIONS.md` (headings; bodies mostly unread).

Present, body not read in this consolidation: `research/DECISIONS.md` (heading `# Decisions` only was seen), `research/CLOUD_CHAMBER_SEALED_GPT_BASELINE.md` and its `.sha256`, `research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md`, `research/FRONTIER_COLLABORATOR_REGULATORY_DEPENDENCY.md`, `research/MACOS_AUTHORIZATION_EVIDENCE_ARCHEOLOGY.md`, `research/MEMORY_PRESERVATION_ARCHAEOLOGY.md`, `research/MEMORY_PRESERVATION_SET_AUDIT.md`, `research/OPOSSUM_MODE_BRAINSTORM.md`, `research/STRATEGIC_FRONTIER_RESILIENCE.md`, `research/TWO_NODE_IDENTITY_PRESERVATION_RELAY_ARCHAEOLOGY.md`.

Open-question headings that remain headings, not closed by this audit: Q-001, Q-002, Q-008, Q-003, Q-004, Q-005, Q-006, Q-009, Q-007, Q-010. Q-008 is kept open here even though E-037’s index row says the ladder question was tested, because the question file still carries the heading and the report body was not re-read.

### Experiment packages

These directories exist under `app/experiments/`. Contents were not assessed. None were run.

`accumulation_probe`, `architecture_a_hot_stove_proof`, `attempt_ledger_test`, `belief_revision_probe`, `breakfast_club_reachability`, `e5_mini`, `first_learning_loop`, `g3_micro_probe`, `gen_epistemic`, `historical_difficulty_calibration`, `learning`, `minimal_procedure_transfer`, `minimal_relevance_gate`, `p3_causal_learning`, `persistent_routing`, `preference_provenance`, `provenance_f2_verification`, `raoc`, `real_trace_f2_provenance`, `restart_persistence_transfer`, `retrieval_capacity_proof`, `rung1`, `skill_ledger`, `strategy_characterization`, `task_type_ground_truth`, `validated_experience_competence_transfer`.

`raoc` corresponds to Findings 93–95 in `CLAUDE.md`: harness built, calibration and a 12-trial pilot described there, UNKNOWN rate later reduced in the classifier writeup, no claim about the hypothesis, no scale-up to n=240 in that finding. This audit did not open the package to confirm the finding text.

### Audit corpus not rowed above

`audits/` contains 539 files. The index’s “groups not individually rowed” section names, at title level, September 2–3 authority and information-flow notes, deliberate-and-learn and inference-path audits, apply-to-code and self-edit forensics, councillor and pipeline traces, the tier3–tier8 corpus (the index says about 25 files), `p3_*` and self-edit closed-loop files, and subdirectories `2026-07-03/`, `forensic/`, `tier3_apparatus/`, `tier4_apparatus/`. This audit did not build a per-file catalogue of all 539. Absence from Tier A is not evidence that a file is unimportant. It is evidence that this consolidation did not re-read it.

### Git history and GitHub

Commits named in `MASTER_PROJECT_HISTORY.md` were listed from `git log` on `project-voyager`. They are chronology, not new test results. Branches visible: `main`, `project-voyager` (current), `vsl-implementation`, `worktree-agent-abe6ecca0408fd0fb`. Remotes seen: `origin/main`, `origin/vsl-implementation`. `vsl-implementation` was not reviewed. The other worktree was not touched. `gh issue list --limit 5 --state all` returned no rows and exit 0. Pull requests and any other GitHub repositories were not listed. This is not an exhaustive GitHub audit.

`CLAUDE.md` Finding 90 records two publication blockers: `COUNCIL.md` is tracked, and commit metadata carries a real name. `PENDING_DECISIONS.md` records the project stays private. This audit did not change visibility.

### Outside the repository

`/Users/richietate/Desktop/FeralEcho-working-self-design-da499375.md` exists (size 121559 bytes at the existence check). Body not read. Prior session recorded a SHA-256 and a decision not to implement PR2, PR3, or PR4 and not to commit the design. This audit did not re-hash the file and does not add it to the 13-claim table.

## What this index refuses to do

It does not treat `research/CURRENT_STATE.md` or `CLAUDE.md` as a fresh production demonstration.

It does not treat Voyager’s 23/25 as evidence that Echo planned those missions.

It does not treat retrieval’s 12/12 tool successes as an official pass.

It does not treat reasoning’s printed 4/10 versus 3/10 as a completed comparison.

It does not treat ScratchWriter’s suite pass as a production tool or as a proof against every attack.

It does not treat CAB’s review as an implementation.

It does not treat E-037 as a reason to delete the Q-008 heading without reading both documents again.
