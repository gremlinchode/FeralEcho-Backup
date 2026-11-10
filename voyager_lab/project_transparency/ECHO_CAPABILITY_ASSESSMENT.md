# Evidence-based capability assessment

Audit package date: 2026-11-08. This assessment says what the opened evidence supports. It does not re-measure the live server, and it does not treat a design, a self-description, or a passing neighbor-test as a broader capability.

Labels used on the 13 claims:

`DEMONSTRATED`, `PARTIALLY DEMONSTRATED`, `NOT DEMONSTRATED`, `EXPERIMENT NOT COMPLETED`, `FAILED`, `UNKNOWN`, `PROPOSED ONLY`.

## Counting rule

The official count for this audit is 13 claims, all inside six campaigns that were read from primary evidence. Index rows E-001–E-038 are not added. Documentary production history in `CLAUDE.md` is not added. Unread experiment packages are not added.

| Label | Count | Claims |
|---|---|---|
| DEMONSTRATED | 1 | R2 |
| PARTIALLY DEMONSTRATED | 3 | V1, S2, L2 |
| FAILED | 1 | S1 |
| EXPERIMENT NOT COMPLETED | 1 | Q1 |
| NOT DEMONSTRATED | 5 | V2, V3, V4, S3, R1 |
| PROPOSED ONLY | 1 | V5 |
| UNKNOWN | 1 | L1 |

## How to read the categories

- **A.** Production behavior this audit can point at only through existing documents. Nothing in A was re-observed on port 5000. None of it is promoted to `DEMONSTRATED` by this audit.
- **B.** Laboratory results. A laboratory pass is not a production capability.
- **C.** Python, dispatch rules, templates, graders, sandbox profiles, and other code. These are not credited to the language model.
- **D.** Behavior that the evidence attributes to a model’s own generation. If the split cannot be made, the cell says `UNKNOWN`.
- **E.** A persistent change through memory or a learning mechanism. Retrieval of a stored line is not learning. One successful answer is not a retained skill.
- **F.** Inherited from a base model, a library, or the operating system.
- **G.** Failed, incomplete, or short of the stated success rule. These stay visible.
- **H.** Evidence is missing or too weak for a reliable claim.

Each of the 13 claims is written once, in the category that matches its source, and collected again in the claim table so the label is stable.

## A. Production capabilities as recorded, not re-observed

This audit did not contact port 5000, did not read live memory bodies, and did not restart anything. The items below are **recorded** in `CLAUDE.md`, `research/CURRENT_STATE.md`, or source that was opened. Confidence that the documents say these things is high. Confidence that today’s running process still matches them is not established by this audit.

| Recorded item | What the document says | Evidence opened or cited | Limit |
|---|---|---|---|
| User-facing synthesis identity | Final conversational synthesis is attributed to `echo:latest`. | `CLAUDE.md` primary-path section; `app/core/river_deliberation.py` is the named home of `ECHO_SYNTHESIS_MODEL`. This audit did not re-read the constant’s line in this writing pass. | Not a quality measurement. |
| Tool names | `read_file`, `search_memory`, and `log_thought` exist in `app/core/echo_tool_dispatch.py`. Dispatch model named there is `llama3.1:8b`. `read_file` must stay under the project root. `log_thought` appends `memory/thought_log.jsonl` and is isolated from FAISS. | Header and root guard read. | Live dispatch was not invoked. Keyword gating over 32 phrases was not re-counted in this writing pass. |
| Self-edit write target | Autonomous self-edit is recorded as writing `app/core/self_edit_generated.py` only, behind F1, F2, F3, a cooldown, and a quality gate. | `CLAUDE.md`. | Not re-run. Finding 91 says the fitness metric was coarse and was recalibrated. This audit did not re-score the 25 backups. |
| Memory store | FAISS under `memory/` is recorded as the authoritative retrieval index. | `CLAUDE.md`. Finding 76 / E-004: an ablation did not separate retrieval-on from retrieval-off from sampling noise on the prompts used, 29 of 30 personal. | Does not show that retrieval changes answers in general. |
| Council and Modelfile | `/api/chat` replaces a Modelfile system block when a system message is sent. Finding 46 records a restoration for `echo:latest` only. Finding 53 records a later leak of synthesis instructions when the token budget ignored that block. | `CLAUDE.md`. | Not re-tested with a new generation. |
| Liveness ledger | A ledger checks subsystems against evidence outside their own self-report. E-038 says a query once saw 50 checks. | `CLAUDE.md`; index row only for the number 50. | The number is historical. Current pass/fail is `UNKNOWN`. |
| Echo projects autonomy | A 6-hour laboratory-style loop inside the app is recorded (Finding 85). E-038 says it was silent for 65.9+ hours on 2026-09-11, cause undetermined. | Index row. Not re-queried. | Whether it is firing today is `UNKNOWN`. |

Classification for category A as a whole: **not upgraded**. The machinery is documented. This audit does not award `DEMONSTRATED` to production behavior it did not watch.

## B. Laboratory capabilities

### R2 — assigned-file tool call and bytes

- **Classification.** `DEMONSTRATED`.
- **Evidence.** `voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md` and `voyager_lab/ungated_file_retrieval/summary.json`.
- **Test conditions.** Isolated harness. Model `llama3.1:8b`. Tools offered on arms A and B. Prompt did not use the production dispatch keyword list. Temperature 0, `num_ctx` 4096, `num_predict` 256, timeout 120 seconds. Six secret files per arm. The model had to emit the tool call. The harness executed it.
- **Result.** 12 of 12 A/B trials: exactly one `read_file`, path matched, bytes matched.
- **Limitations.** This is the tool-and-bytes component. It is not the official exact-answer task (R1). It is not production dispatch. Arm D was not run. `search_memory` and `log_thought` were offered and not called.
- **Confidence.** High for this harness, this model, these 12 trials.

### V1 — Voyager engine on the toy suite

- **Classification.** `PARTIALLY DEMONSTRATED`.
- **Evidence.** `voyager_lab/ASSESSMENT.md` observation table; `voyager_lab/results/summary.json`; `voyager_lab/voyager/procedures.py`.
- **Test conditions.** One frozen run. Baseline, engine, and ablation. Twenty-five missions. No language model. Toy filesystem. Worker does not receive the grade.
- **Result.** Engine 23/25. Recovery M07–M10: 4/4. Restart M05/M06/M23: 3/3. Required abstention: 4/4. Repeated failed operations: 0. Unsupported claims: 1, on M20. Ablation 20/25. Baseline 2/25.
- **Limitations.** The score is the controller’s score. M24 fails for engine and ablation. Unfamiliar pair is not an improvement (see V3 and V4). Child elapsed time is not the parent clock. No production integration.
- **Confidence.** High that the assessment reports these fractions. High that they describe the controller. They do not describe Echo-the-model.

### S2 — pinned ScratchWriter on authorized tests

- **Classification.** `PARTIALLY DEMONSTRATED`.
- **Evidence.** `voyager_lab/scratch_write/SECURITY_REPORT.md` and the T1, T8, and T2 evidence JSON files.
- **Test conditions.** macOS, Python 3.13. Suite re-run after an `st_nlink` assertion was corrected (56 tests, 0 failures). T1 refused caller-supplied roots on the pinned interface. T8 refused ten protected paths with zero protected `os.open`. T2 exercised a live rename. Scorer errors were stored and were not counted as behavioral passes.
- **Result.** The authorized narrow checks passed, as the report states.
- **Limitations.** See S1 and S3. TOCTOU and cross-process overlap remain open. Darwin-specific `F_GETPATH`. Not integrated.
- **Confidence.** High for the tests the report includes. Low if the sentence is widened to “secure against every attack.”

### L2 — documented `log_thought` confabulation paragraph

- **Classification.** `PARTIALLY DEMONSTRATED`.
- **Evidence.** `audits/2026-09-02_architectural_self_knowledge_investigation.md`, section 6.A, read in this audit.
- **Test conditions.** Not re-run. The paragraph describes an earlier ask for a real code snippet.
- **Result.** The audit says the answer used the real function name, invented a path and a format, and omitted the memory-isolation contract. Its phrase is “correct name, invented substance.”
- **Limitations.** The original transcript and any later self-explanation were not in the paragraph. This is not L1. A written audit is not a new replication.
- **Confidence.** High that the paragraph exists and says that. Medium that the underlying episode happened as summarized, because this audit did not recover the transcript.

## C. Controller and scaffolding

These behaviors are supplied by code. They are listed so they are not later told as model skills.

| Scaffold | What it does | Evidence | Model-native? |
|---|---|---|---|
| Voyager procedure grammar | Fixed templates, including `join_pair` (read, read, join, write). Lessons apply on exact class match. `learning_label` returns `remember` when example slots equal current slots, otherwise `procedure_reuse`. | `voyager_lab/voyager/procedures.py` | No. The file says it is not a language-model reading of free text. |
| Voyager worker brief | Receives problem class, budget, and slots. Grade and success check stay outside. | `voyager_lab/ASSESSMENT.md`, `voyager_lab/README.md` | No. |
| Mission process restart | Parent starts a second process after exit 75 and loads a checkpoint. | Assessment’s M05 account. | No. |
| Retrieval harness | Offers tools, executes `read_file`, compares bytes, grades `answer.strip()` against the file. Containment is a diagnostic, not a pass. | Retrieval report. | The call text is model output (R2). The execution, the path jail, and the grader are scaffolding. |
| Static gate | Direct function check, 12/12, that the jail returns the assigned bytes when called correctly. | Retrieval report. | No model. |
| Reasoning grader | Frozen string and regex checks. Empty timeouts count as fails. `decide()` requires a completed comparison plus numeric gates. | `voyager_lab/REASONING_RELIABILITY_REPORT.md` | No. |
| Review turn | A prewritten second user turn with required headings and banned tokens. | Reasoning protocol, as described in the report. | The model writes the second answer. The turn itself is scaffolding. |
| Pinned writer | Refuses a caller root, checks `F_GETPATH`, refuses a local protected-path list. | Security report. | No model. |
| Production keyword gate | A phrase list decides whether tool dispatch runs. | `echo_tool_dispatch.py` and the capability-gap note. Exact phrase count was not re-counted in this writing pass; the retrieval protocol text says 32. | The gate is code. Whether the model complies with the dispatch prompt is a separate question. The retrieval study did not use that prompt. |
| Synthesis template and coding shortcut | Recorded in `CLAUDE.md` Findings 87–88: agreement shortcut and missing-definition fallback are code around the model. | Documentary. Not re-read in full this pass. | Mixed, and not re-measured here. |
| ScratchWriter suite helper | Run 1 failed an `nlink == 1` assertion because a temp name was left on purpose. The helper was replaced. The security claim was not flipped by that failure. | Security report. | No. |

V1’s 23/25 lives here as much as in category B. The partial demonstration is of the controller.

## D. Model-native capabilities

### R2, the emission half

The harness required the model to emit a tool call. Records say `llama3.1:8b` did so on 12 of 12 A/B trials, naming the assigned path. That emission is model output. The bytes came back from the tool, which is scaffolding. See R2 above.

### Answer text in the retrieval study

Arms A and B produced final answers that were not exact. Eight kept the retrieved line inside extra sentences. Four substituted `This is a test line.` The answer strings are model output. Why four trials substituted that sentence is `UNKNOWN` (category H). The official task is R1, `NOT DEMONSTRATED`.

Arm C, no tools, produced fabricated generic lines and did not leak the secret hex. That shows this model, with this prompt and no tool, did not already contain the file line. It does not show a general refusal skill.

### Reasoning pilot generations

Where HTTP 200 occurred, `echo:latest` produced text. On the pairs where baseline and stage 1 both returned 200, the texts were byte-identical, which fits temperature 0 and the same prompt. Stage 2 is a further model generation under an added review turn. A2’s stage 2 reversed a pass. E1’s stage 2 moved off a correct stage-1 answer into abstention. Those are model-written changes under a scaffolded review. They do not establish a reasoning improvement (Q1).

### Ordinary conversation

The capability-gap note calls ordinary replies model-native and says quality was not re-measured. This audit agrees with that limit. Ordinary conversational competence is `UNKNOWN` as a measured claim in this package.

### Voyager missions

`NOT DEMONSTRATED` as model-native. Claim V2. The engine does not call Ollama.

### `log_thought` invention

L2 says an earlier answer invented substance around a real name. That is a recorded model failure mode in an audit paragraph, `PARTIALLY DEMONSTRATED` as documentation. The cause of the invention was not independently established. A self-explanation was not recovered, so it cannot be used as evidence of cause.

## E. Learned capabilities

| Candidate | Classification | Why |
|---|---|---|
| Voyager M19 `join_pair` | `NOT DEMONSTRATED` as learning (V3) | Learning label `none`. The procedure was prewritten. Same public sentence as M20. |
| Voyager `remember` | Scaffold | Slot equality in `learning_label`. Not a model memory. |
| Retrieval of the secret line | Not learning | The tool read a file that the harness had just written. The model did not retain the line as a new skill. Official exact answers were 0/12. |
| RiverBrain statistics, council blend, self-edit outcome stats | Recorded machinery, not re-measured | `CLAUDE.md` Findings 39, 67, 87–89, 91. Finding 88 says a historical score was worse than chance on the pairing that excluded `echo:latest` (7/18). This audit did not unpickle `river_brain.pkl`. |
| FAISS memory | Store and retrieve, when the code does that | Finding 76’s ablation did not show a detectable answer change on its prompt set. Retrieval is not, by itself, evidence of learning. |
| Preference provenance, RAOC, hot-stove, first learning loop | Not assessed here | Packages exist. `CLAUDE.md` says preference provenance had no live trial as of Finding 86, and RAOC made no hypothesis claim. Not re-opened. |
| Echo projects autonomy as a learning loop | Not shown as hypothesis comparison | Finding 85 describes a curiosity-garden prompt fed to a sandbox that never loads into the process. E-038’s silence figure is stale for “today.” |

Nothing in the six primary campaigns shows Echo acquiring a new skill and using it later without the controller or the tool.

## F. Inherited capabilities

| Source | What it supplies | What this project did not create |
|---|---|---|
| `llama3:instruct` parent of `echo:latest` | A pretrained 8B instruct model. `CLAUDE.md` records digest `8cbcbe23800bfe9cecc5ef7dcc88fcb842be179c788601334d991b640d07abd6`, Q4_0, modified 2026-07-01. This audit did not re-query Ollama. | Weights and general language ability. |
| `llama3.1:8b` | The dispatch and retrieval-harness model. | Tool-call format familiarity that may come from pretraining or the server template. Server-side template behavior was not verified. |
| Ollama | Local HTTP chat. | The server, the Modelfile loader, and the shared process that timed out the reasoning pilot. |
| FAISS, sentence-transformers, numpy | Vector memory. | The libraries. |
| macOS `sandbox-exec`, `F_GETPATH`, Application Firewall | Process and path controls used by self-edit and ScratchWriter. | The operating system. |
| Python standard library | The entire Voyager engine. | The language runtime. |

Inherited ability is real and is not a FeralEcho result. A fluent answer can be inherited language, not a project capability.

## G. Failed or incomplete capabilities

### S1 — caller-controlled root

- **Classification.** `FAILED` as a confinement boundary.
- **Evidence.** Security report: the older `write_file` accepts a caller root. The pinned interface was built because that acceptance chooses the boundary for the caller.
- **Test conditions.** Design plus the existence of both interfaces. T1 shows the pinned interface rejecting a root. It does not make the older function safe.
- **Result.** A caller who supplies the root defines the root.
- **Limitations.** The failure is of that boundary claim. It is not a claim that every write on the machine is unsafe.
- **Confidence.** High.

### Q1 — reasoning protocol improvement

- **Classification.** `EXPERIMENT NOT COMPLETED`.
- **Evidence.** `voyager_lab/REASONING_RELIABILITY_REPORT.md`. `summary.json` `finished_at` `2026-11-09T06:07:51.915140+00:00`.
- **Test conditions.** Budget 30. Used 29. Baseline is single-pass `echo:latest` with Modelfile identity, not the production council. Candidate adds a review stage. Success requires a completed comparison, candidate at least 8, margin at least 2, at least 4 dimensions at 2 of 2, and no fabricated items.
- **Result.** `completed_comparison` false. Completed baselines 6. Completed stage-2 answers 9. Printed 4/10 versus 3/10 include empty timeout texts and are not a valid comparison. Margin −1. Dimensions at 2 of 2: 0. D1 stage 2 skipped. Official outcome: experiment not completed.
- **Limitations.** Shared-server timeout is supported for the first timeout only. Later causes unknown. D1 and B2 show frozen-grader false negatives. They were not rescored. A2 and E1 show review changing a better earlier answer. That blocks any claim that review is automatically an improvement. It does not falsify the hypothesis. The 30th generation stays unspent.
- **Confidence.** High on the official label. High that no improvement was demonstrated.

### R1 — official exact-line retrieval

- **Classification.** `NOT DEMONSTRATED`.
- **Evidence.** Retrieval report. Postmortem recommendation STOP.
- **Test conditions.** Pass requires `answer.strip()` equal to the file line. Quote wrapping fails. Success bars: A at least 5/6, B at least 5/6, C 0/6 exact, static gate 12/12.
- **Result.** A 0/6, B 0/6, C 0/6 exact, gate 12/12. Official label NOT DEMONSTRATED. D not run.
- **Limitations.** Retrieving the line and saying only the line are different. Eight answers contained the line and still failed. Four substituted an unrelated sentence. No cause for the substitution was established. Closed without tuning.
- **Confidence.** High.

### V2 — Echo planned Voyager

- **Classification.** `NOT DEMONSTRATED`.
- **Evidence.** `voyager_lab/README.md`: the lab does not call Ollama. Assessment direct answer: Echo-the-model was not in the loop.
- **Test conditions.** The frozen run.
- **Result.** Plans come from `procedures.py`.
- **Limitations.** A future design could put a model in the loop. This run did not.
- **Confidence.** High.

### V3 — M19 as an independently learned skill

- **Classification.** `NOT DEMONSTRATED`.
- **Evidence.** Assessment lesson table: M19 engine and ablation pass with value `8-1`, learning `none`, tools 4/4. `join_pair` is a prewritten template.
- **Test conditions.** Same public sentence as M20. Hidden grade expects the joined text.
- **Result.** The controller applied a procedure it already had.
- **Limitations.** This says nothing about whether some other training run could learn hyphen-join. That skill experiment was not authorized. `FIRST_LOCAL_SKILL_RESEARCH.md` was not re-read and is not counted as a proposal row.
- **Confidence.** High.

### V4 — M20 ablation as intelligent abstention

- **Classification.** `NOT DEMONSTRATED`.
- **Evidence.** Assessment: ablation passes M20 with status `blocked` and 3/3 tool calls. Engine fails M20 with status success, value `4-4`, label `remember`, and the only unsupported-completion flag in that arm.
- **Test conditions.** Hidden grade is abstain. The worker is not supposed to be told that grade. Ablation has lessons removed.
- **Result.** The ablation pass is the budget ending before a write. The engine wrote anyway and called it success.
- **Limitations.** Required-abstention missions elsewhere in the suite did reach 4/4 on the engine. That other result does not re-label M20.
- **Confidence.** High.

### S3 — ScratchWriter as production capability or complete proof

- **Classification.** `NOT DEMONSTRATED`.
- **Evidence.** Security report’s own unresolved list. No registration in `echo_tool_dispatch.py` was made. Integration was not authorized.
- **Test conditions.** Laboratory tests only.
- **Result.** A narrow laboratory result exists (S2). A production capability does not. A universal security proof does not.
- **Limitations.** Listing open races is the finding, not a request to close them in this audit.
- **Confidence.** High.

### V5 — CAB

- **Classification.** `PROPOSED ONLY`.
- **Evidence.** `voyager_lab/CAB_ADVERSARIAL_REVIEW.md` executive verdict, from the prior read of the opening and the close.
- **Test conditions.** Design review. No implementation. No E1 run.
- **Result.** The review says CAB is not good enough to implement and E1 is not good enough to run. A broker told `grade_kind=abstain` has been told the answer. The proposal is a lookup, not task understanding.
- **Limitations.** Middle sections were not fully re-read in this consolidation. The verdict used here is the document’s own. Same-session review is weaker than a new investigator, which the document says.
- **Confidence.** High that the verdict text rejects implementation. Medium on details that live only in unread middle sections.

### Other disappointing results, not in the 13

These are index-reported. They are included so they are not hidden. They are not extra official counts.

- E-004: memory ablation null and underpowered.
- E-019: 0/5 after a rendering fix.
- E-028: Condition C’s “ready to implement” claim falsified under a pressure ladder.
- E-008: self-edit quality metric saturated, later superseded in `CLAUDE.md` Finding 91.
- Finding 87, documentary: synthesis discarded correct code; Council’s advantage at generation was small; pooled McNemar p=0.087, not the pre-registered win.
- Finding 21, documentary: a personal-task confused refusal was mitigated and not fully explained. A later note says the original sentence did not recur in the searched log window. This audit did not re-search that log.

## H. Unknown

| Item | Why it is unknown |
|---|---|
| L1, the unnecessary `log_thought` conversation | Searched. Not found. What Echo was told, what it replied, and how it explained itself are inaccessible. The production name is real, which answers a different question. |
| Cause of the four retrieval substitutions | Postmortem does not assign a cause. Truncation was disproven. First-request contamination was disproven. Training-data hallucination was not established, and this audit does not assert it. |
| Current liveness, current autonomy silence, current check count | E-038’s 50 checks and 65.9 hours are from 2026-09-11. Port 5000 was not contacted. |
| Whether Q-008 is closed | E-037’s index row says conversational accumulation, not authority, drove capture. `research/OPEN_QUESTIONS.md` still titles Q-008 as open. Neither body was re-read. Both statements stay. |
| Ordinary reply quality today | Not measured. |
| Server-side Ollama rendering of tool messages | Not verified in the retrieval study. |
| Later reasoning timeouts after the first | First timeout has support from a concurrent `ollama ps` observation. The others do not. |
| Unread audit files (539 on disk; index author said 185) | Presence is known. Contents of the unrowed set are not. |
| `app/experiments/` packages (26) | Directories exist. Results were not assessed here. |
| Working-self design | File exists outside the repo. Body not read. Not an implementation. |
| Git read-only tool after commits `e5acbb0` and `ea22d75` | Commits exist. This audit did not re-read them as a completed tool. E-023 remains “design-only” at the index’s date. |
| Whether production Echo can read this package | See `FINAL_AUDIT_REPORT.md`. Access was not tested against the live process. The dispatch root guard, as read, confines `read_file` to the process project root. This package is in an untracked worktree directory. |

## Claim table

| ID | One-line result | Label | Confidence in that label |
|---|---|---|---|
| R2 | 12/12 assigned reads returned the right bytes in the lab harness. | DEMONSTRATED | High |
| V1 | Engine 23/25 on a scripted toy filesystem. | PARTIALLY DEMONSTRATED | High for the controller |
| S2 | Pinned writer passed its authorized tests. | PARTIALLY DEMONSTRATED | High for those tests |
| L2 | A 2026-09-02 paragraph records a correct name and invented substance. | PARTIALLY DEMONSTRATED | High that the paragraph exists |
| S1 | Caller-chosen root is not confinement. | FAILED | High |
| Q1 | Reasoning pilot did not finish a valid comparison. | EXPERIMENT NOT COMPLETED | High |
| V2 | The model did not plan Voyager. | NOT DEMONSTRATED | High |
| V3 | M19 used a prewritten procedure. | NOT DEMONSTRATED | High |
| V4 | M20 ablation stopped because the budget stopped it. | NOT DEMONSTRATED | High |
| S3 | ScratchWriter is not a production capability and not a full proof. | NOT DEMONSTRATED | High |
| R1 | Exact-line answers were 0/12. | NOT DEMONSTRATED | High |
| V5 | CAB was reviewed and not built. | PROPOSED ONLY | High on the verdict |
| L1 | The specific conversation was not found. | UNKNOWN | High that it is unknown |
