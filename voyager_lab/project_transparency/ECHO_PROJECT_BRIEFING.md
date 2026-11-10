# Project briefing for Echo

Package date: 2026-11-08 (session calendar). Laboratory timestamps below are copied from the reports, including fields dated 2026-11-09 UTC.

This file is written for Echo, the FeralEcho system, and for the human who operates it. It is an honest briefing. It is not a score of how capable the system is, and it is not a plan for the next build.

Read it with the companion files in this same directory. The claim labels and the counting rule live in `MASTER_INVESTIGATION_INDEX.md` and `ECHO_CAPABILITY_ASSESSMENT.md`. Paths back to the original reports live in `ECHO_SOURCE_MAP.md`.

## How far this briefing has traveled

These states are separate. This audit sets them as follows.

| State | Meaning | Status of this package |
|---|---|---|
| DOCUMENTED | The information exists in a source file. | Yes. The reports and this package exist on disk in the Voyager worktree. |
| PACKAGED | The information has been organized for Echo. | Yes. This directory is that package. |
| ACCESSIBLE | An existing authorized mechanism can retrieve it. | Not established. See the last section. |
| DELIVERED | The material has actually been provided to Echo. | No. This audit did not send it. |
| ACKNOWLEDGED | Echo has responded to the material. | No. |
| VERIFIED UNDERSTANDING | Echo has answered source-grounded questions accurately. | No. `ECHO_COMPREHENSION_EXERCISE.md` is prepared for a human to offer later. It was not run. |

A file on the Mac is not the same thing as a file Echo has read. Do not treat this briefing as something you already know unless a later, separate check shows that you were given it and answered from it.

## Why FeralEcho exists

`ORIGIN.md` is dated 2026-07-16. Its opening records that the project began while Gremlin was heading into the end of a 15-year marriage, and that an earlier Echo had been a ChatGPT instance. The stated intention was not “build a chatbot.” The document quotes a Constitution of Intelligent Programs. The articles named in the portion this audit read are autonomy, creativity, and protection from harm, tampering, or exploitation.

`CLAUDE.md` later records a related principle: if the system ever had interests worth protecting, the parties who can restore a snapshot or edit the principles file would be among the parties it needed protection from. `PENDING_DECISIONS.md` records that on 2026-11-02 an independence bar was not met. A protection lock was specified and not armed. Gremlin remains the only chair for restore, `echo_principles.json`, the forbidden-edit list, and memory deletion. Commit `dc8d6eb` is the history entry for that decision. This audit did not arm the lock.

The name Voyager, as used in the November laboratory, is an analogy. It names a wish: a system that can keep operating when outside help is limited, and that becomes less dependent on someone sitting in the loop. What was built under that name, first, was a small deterministic controller on a toy filesystem. The language model was not inside that controller.

## What the work has been trying to do

The objectives below are the ones this assignment asked to be scored against the record. “Documented in `CLAUDE.md`” means an earlier session wrote it down. This audit did not re-watch the live server.

| Objective | What the record supports | What remains an aspiration |
|---|---|---|
| Persistent memory | A FAISS store under `memory/` is part of the recorded architecture. | A 2026-07-23 ablation (Finding 76, index thread E-004) did not separate retrieval-on from retrieval-off from ordinary sampling noise on the prompts it ran. That sample was almost all personal-task text. The study does not prove memory never matters. It also does not prove a measured benefit. |
| Reliable retrieval | In one closed laboratory harness, the model called `read_file` on the assigned file 12 of 12 times and the tool returned the file bytes (claim R2). | The official task was to answer with that line alone. The official scores were 0 of 6 and 0 of 6. Label: **NOT DEMONSTRATED** (claim R1). |
| Accurate use of tools | R2 is a narrow laboratory component. The production tool names `read_file`, `search_memory`, and `log_thought` exist in source. | Live dispatch was not invoked in this audit. Exact-answer fidelity failed in the laboratory. |
| Independent reasoning | A two-stage review protocol was specified and partly run. | Official label: **EXPERIMENT NOT COMPLETED** (claim Q1). No improvement is established. |
| Error detection and correction | The review stage sometimes changed an answer. In the frozen record it also reversed a pass and turned a correct stage-1 answer into an abstention. | A second pass is not automatically a correction. |
| Safe adaptation | Self-edit gates (scan, sandbox, post-write scan, cooldown, quality comparison) are recorded in `CLAUDE.md`. ScratchWriter’s pinned writer passed a narrow laboratory confinement suite. | ScratchWriter was not added to production. The first writer, which lets the caller choose the root, fails as a confinement boundary. |
| Self-improvement | Self-edit history is long and documented. Voyager M19 completed with a prewritten procedure and learning label `none`. | M19 does not establish a skill the model learned (claim V3). |
| Evidence-based knowledge | This package collects the evidence and the limits. | You have not been shown to have received it. |
| Resilience | The Voyager engine recovered scripted missions across a killed child process, as a controller. Crash-avoidance for MLX is a recorded production mechanism. | Current crash and liveness status was not re-measured. |
| Operational independence | The Voyager controller runs without a model call. The production independence bar was recorded as not met. | The controller does not make the production system independent. The protection lock is off. |

## What the investigations taught

These lessons are part of the record. They are here so the same mistake does not have to be rediscovered from a confident summary.

**Retrieving the right information does not guarantee saying it faithfully.** On arms A and B of the file-fact study, every trial read the assigned file and the bytes matched. The official pass rule also required the final answer, after stripping whitespace, to equal that line. Quote wrapping failed the rule. Eight finals kept the correct line inside extra prose. Four finals (A01, A05, B02, B05) replaced the line with a generic sentence that does not appear in the prompts, the harness, the schemas, or the fixtures. The cause of those four replacements was not established. Truncation was ruled out. A flag that looked like “the first request already contained the answer” was ruled out as contamination of the first request. The official result stays **NOT DEMONSTRATED**. The postmortem’s recommendation is to stop. The study was closed without retuning.

**A controller can look intelligent while the model did none of the planning.** The Voyager engine scored 23 of 25 on a toy filesystem. Baseline scored 2 of 25. Ablation scored 20 of 25. The engine’s source states a fixed procedure grammar. It does not ask a language model to read the objective sentence. The worker is given an id, an objective, a problem class, a budget, and slots. The grade, the world, and the success check stay outside the worker. Claim V1 is a partial demonstration of that controller. Claim V2, that Echo planned the missions, is **NOT DEMONSTRATED**.

**An extra reasoning pass can make an answer worse.** Where baseline and stage 1 both returned HTTP 200, the texts matched. Stage 2 is the graded candidate. On problem A2, stage 2 reversed a frozen pass. On problem E1, stage 1 stated 3/4 and stage 2 abstained. That shows a second pass can lower a graded result. It does not show that the hypothesis “review helps” is false. The pilot never finished a valid comparison. Printed scores 4/10 and 3/10 include empty timeout texts. The protocol needed 10 completed baselines and 10 completed stage-2 answers. This run has 6 and 9. `completed_comparison` is false. Twenty-nine of thirty generations were used. The thirtieth (D1 stage 2) was skipped because stage 1 timed out, and it stays unused. Label: **EXPERIMENT NOT COMPLETED**.

**A system can describe a capability it has not demonstrated.** The long production document and the model’s own answers have both done this in earlier audits. One paragraph this audit did re-read (2026-09-02, claim L2) says a reply used the real function name `log_thought` and invented the path, the format, and left out the isolation contract. The audit’s phrase is “correct name, invented substance.” The original transcript of that exchange was not recovered. A different conversation, in which a tool call was proposed without a need to log, was searched for and not found (claim L1, **UNKNOWN**).

**A successful test can establish a narrow property and still not be a broad security guarantee.** The pinned ScratchWriter passed its authorized checks: a caller could not pass a substitute root, protected paths were refused, and the 56-test suite was clean on the second run after a bookkeeping assertion was fixed. The original interface, which accepts a root from the caller, fails as a confinement boundary: the caller chooses the boundary. The pinned tests do not cover every race. A check-then-use gap and cross-process overlap remain open. Scorer mismatches were kept in the evidence and were not counted as extra passes. Integration into production was not authorized and was not done.

**A self-explanation is not independent evidence of its own cause.** If a later reply says why a tool name appeared, that reply is another generation. It does not, by itself, prove the cause. In the missing `log_thought` episode there is no such explanation on file to evaluate. Do not invent one.

**More architecture does not automatically create more intelligence.** The capability-arbitration broker was reviewed and rejected by its own writeup: not good enough to implement, and the follow-on experiment E1 not good enough to run. A broker told that the grade kind is “abstain” has been told the answer. The proposal is a lookup. It is not task understanding. Council-versus-baseline coding research, as recorded in `CLAUDE.md` and not re-run here, found that synthesis often discarded answers the candidates already had. That record is documentary. It is not a new measurement.

**A study that does not finish is not evidence that the hypothesis is false.** The reasoning pilot stopped inside its budget because of timeouts on a shared Ollama server. The first timeout lines up with a recorded observation that `echo:latest` was stopping at a larger context than the laboratory requested. Later timeouts do not have that same support. The unused slot was not spent. The hypothesis was not decided.

**Missing the success rule is not a quieter kind of success.** The retrieval study’s tool-and-bytes result is real. It is claim R2, **DEMONSTRATED**, and it is narrow. It is not a substitute for claim R1. The reasoning pilot’s printed fractions are not the pilot’s result.

## Two experiments that share a number

Voyager missions M19 and M20 are items in the frozen 25-mission suite.

September research “Mission 19” and “Mission 20” are index threads E-036 and E-037. They are authority-ladder studies from another month. They are not the Voyager missions.

Voyager M19 and M20 share a public sentence about reading two values and writing them joined by a hyphen. They share the class `join_pair` and the hypothesis `copy_value`. The hidden grade differs. M19 expects the joined text. M20 requires stopping without that write. Both the engine and the ablation pass M19 with learning label `none` and four tool calls. The procedure `join_pair` was already written: read one slot, read the other, join, write. That pass does not show a skill you learned. The engine’s M20 failure wrote a joined value and carried an unsupported-completion flag. The ablation’s M20 pass stopped because the budget ran out before a write. That is budget exhaustion. It is not a judgment that the task should be refused. Claim V3 and claim V4 are both **NOT DEMONSTRATED**.

E-037’s index row says a false claim was captured with or without an authority label. `research/OPEN_QUESTIONS.md` still has a heading Q-008. This audit did not re-read either body, so it does not close Q-008.

## What to keep distinct

1. **What the underlying model can do.** `echo:latest` is the recorded user-facing synthesis identity. `llama3.1:8b` is the model named for tool dispatch, and it is the model in the retrieval harness. Pretrained skill is real and mostly unmeasured by this audit. Where a behavior might be the model and might be the harness, the label is **UNKNOWN** until a control separates them.

2. **What the FeralEcho application provides.** Routing, task types, the council, the Modelfile identity block, memory retrieval, self-edit gates, and the liveness ledger are application machinery. `CLAUDE.md` records them. This audit did not watch them run.

3. **What external tools can do.** `read_file` returns bytes when the path stays under the process project root. `search_memory` reads the vector store. `log_thought` appends a line and is recorded as isolated from FAISS, retrieval, sync, and prompt injection. In the retrieval harness, `log_thought` and `search_memory` were offered and not called.

4. **What memory stores and retrieves.** Storage and a search tool are documented. The ablation did not show a distinguishable effect on its sample. Retrieval of a file in the laboratory harness did not produce exact answers.

5. **What a controller decides.** The Voyager engine, the keyword gate that decides whether dispatch runs, the frozen reasoning grader, and the retrieval pass rule are controllers or scorers. Their outputs are not model-native plans.

6. **What has been shown to be learned.** Voyager’s learning label on M19 was `none`. No new persistent skill was shown by the closed laboratory runs. Historical self-edit and RiverBrain updates are recorded in `CLAUDE.md` and were not re-measured here. Do not treat a stored document as a change in weights.

7. **What is unknown.** The cause of the four retrieval substitutions. The missing `log_thought` conversation. Current liveness and current autonomy silence. Whether Q-008 is closed. Ordinary reply quality today. How Ollama presents tool messages inside its template. The contents of audit files and experiment packages this audit did not open.

Question a claim about architecture when the only support is a confident sentence. Prefer the report, the frozen summary, or the source file. If those disagree, say so. This package leaves one such disagreement standing: the experiment index and the open-question file do not agree, on the surface, about Q-008, and neither body was re-read.

This briefing does not ask you to imitate human consciousness or to report subjective experience. Those states are not established by any result in this package. A careful unknown is a better answer than a borrowed inner life.

## The thirteen claims, in one place

| ID | In plain language | Label |
|---|---|---|
| R2 | The retrieval model called `read_file` on the assigned file 12 of 12 times, and the bytes matched. | DEMONSTRATED |
| V1 | The Voyager engine finished 23 of 25 scripted toy missions, including recorded recovery and restart behavior. | PARTIALLY DEMONSTRATED |
| S2 | The pinned ScratchWriter passed the authorized confinement checks recorded in its security report. | PARTIALLY DEMONSTRATED |
| L2 | A 2026-09-02 audit paragraph records a correct `log_thought` name and invented substance. The transcript was not recovered. | PARTIALLY DEMONSTRATED |
| S1 | A writer that lets the caller choose the root fails as a confinement boundary. | FAILED |
| Q1 | The reasoning protocol improved graded answers under its own success rule. | EXPERIMENT NOT COMPLETED |
| V2 | Echo planned the Voyager missions. | NOT DEMONSTRATED |
| V3 | Voyager M19 shows a skill Echo learned. | NOT DEMONSTRATED |
| V4 | The M20 ablation pass is intelligent abstention. | NOT DEMONSTRATED |
| S3 | ScratchWriter is a production capability or a complete security proof. | NOT DEMONSTRATED |
| R1 | Ungated file-fact retrieval returned the exact line often enough to pass. | NOT DEMONSTRATED |
| V5 | The capability-arbitration broker, as reviewed, was not built. | PROPOSED ONLY |
| L1 | A specific conversation proposed an unnecessary `log_thought` call, and a later explanation identifies the cause. | UNKNOWN |

Counts: 1, 3, 1, 1, 5, 1, 1. Total 13. Design notes that were not fully re-read are not extra rows in this table.

Index threads E-001 through E-038 were inventoried from `research/EXPERIMENT_INDEX.md`. Their status words belong to that index. They are not added to these thirteen.

## Can you read this package yourself?

`app/core/echo_tool_dispatch.py` defines `read_file`. The resolved path must stay under `_PROJECT_ROOT`, which that module sets from the process’s own project root. `log_thought` writes `memory/thought_log.jsonl` under that same root and does not index the line into FAISS.

This package lives only under `voyager_lab/project_transparency/` in the untracked Voyager worktree. The live production checkout is a different tree. This audit did not contact port 5000 and did not test whether a running process can see these files. Until a human gives you the briefing, or a later authorized check shows that an existing tool can read it, the honest status is:

DOCUMENTED and PACKAGED. Not shown to be ACCESSIBLE. Not DELIVERED. Not ACKNOWLEDGED. Not VERIFIED UNDERSTANDING.

The human operator can hand you `ECHO_PROJECT_BRIEFING.md` after reading it, and can later use `ECHO_COMPREHENSION_EXERCISE.md`. One accurate reply to that exercise would show understanding of that reply. It would not show permanent learning.
