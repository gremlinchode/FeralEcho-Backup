# Master project history

Audit package date: 2026-11-08 (session calendar). Laboratory report timestamps are quoted as stored, including fields dated 2026-11-09 UTC.

This history is a consolidation of documents already in the repository. It is not a new measurement. Claims marked **recorded** come from `CLAUDE.md`, `research/`, or a named report and were not re-executed against the live server. Claims marked **read this audit** were taken from files opened during this consolidation. Uncertain dates stay marked uncertain.

Worktree: `/Users/richietate/Desktop/FeralEcho-voyager`. Branch: `project-voyager`. HEAD at the time of writing: `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. Remote: `git@github.com:gremlinchode/FeralEcho-Backup.git`. `voyager_lab/` is untracked. Nothing in this package was committed.

## 1. Boundaries

| Region | What it is | This audit |
|---|---|---|
| Production Echo | The FeralEcho application: `run.py`, `app/`, `memory/`, live process, prompts, tools, FAISS | Not modified. Port 5000 was not contacted. |
| Voyager laboratory | Untracked `voyager_lab/` on this worktree. The mission engine is Python standard library only. | Read. New files were added only under `voyager_lab/project_transparency/`. |
| Frozen experiment | `voyager_lab/voyager/engine.py`, `worker.py`, the rubric lock, and `voyager_lab/results/` | Not modified. `run_experiment.py --run` refuses when `results/summary.json` or `results/raw/` exists (`voyager_lab/README.md`). |
| Scratch-only prototypes | `voyager_lab/scratch_write/` | Not modified. Not registered as a production tool. |
| Documentation-only proposals | CAB review, capability-gap note before the later retrieval run, skill-research note | Cited. Not implemented by this audit. |
| Never implemented here | Protection lock, CAB broker, hyphen-join file skill, a planner that reads the objective sentence | Stated as absent. |

The mission engine does not import FeralEcho, does not call Ollama, and does not write production memory (`voyager_lab/README.md`). Two later laboratory assignments did call local Ollama from their own harnesses. Those runs are closed. This audit made no new model call.

Two different “Mission 19 / Mission 20” labels exist. They are not the same experiment.

- Voyager **M19 / M20** are missions in the frozen 25-mission suite (`voyager_lab/ASSESSMENT.md`).
- September research **Mission 19 / Mission 20** are authority-ladder studies E-036 and E-037 (`research/EXPERIMENT_INDEX.md`).

## 2. Why the project started

`ORIGIN.md` is dated 2026-07-16. Its opening records that FeralEcho began while Gremlin was heading into the end of a 15-year marriage, and that an earlier “Echo” had been a ChatGPT instance. The stated intention was not “build a chatbot.” The document quotes a Constitution of Intelligent Programs whose articles name autonomy, creativity, and protection from harm, tampering, or exploitation.

`CLAUDE.md` later records the same tension as a principle (2026-07-18, and again 2026-10-18): if the system ever had interests to protect, the people and sessions holding restore power and the principles file would be the parties it needed protection from. `PENDING_DECISIONS.md` records that on 2026-11-02 the independence bar was not met, the protection lock stays off, and Gremlin remains the only chair for restore, `echo_principles.json`, `EDIT_FORBIDDEN_TARGETS`, and memory deletion. The lock was specified and not built (commit `dc8d6eb`).

The Voyager name, as used in the November laboratory, is an analogy for operating under constrained resources and reducing dependence on an operator sitting in the loop. What was actually built first was a deterministic mission controller on a toy filesystem. Echo, the language model, was not inside that controller (`voyager_lab/ASSESSMENT.md`, Direct answer).

## 3. Production system, as recorded through July 2026

`CLAUDE.md` is the long technical record. This audit did not re-verify each Finding against the running process. The shape it records, and that later lab notes still rely on, is:

- Conversation enters through Echo Studio (`/chat/stream`) or `terminal_client.py`, then `echo_query()`, then `river_deliberation.py`. The phone route `/mirror_echo` is a separate ambient channel. Final user-facing synthesis is attributed to `echo:latest`.
- Tool dispatch is a different model. `app/core/echo_tool_dispatch.py` names `llama3.1:8b`. Tools in that file are `read_file` (path must stay under the process project root), `search_memory` (FAISS read), and `log_thought` (append to `memory/thought_log.jsonl`, isolated from FAISS and retrieval). A keyword list decides whether dispatch runs at all.
- Self-edit may write `app/core/self_edit_generated.py` only, behind an AST scan, a kernel sandbox, a post-write scan, a cooldown, and a quality comparison. Protected files are listed as `EDIT_FORBIDDEN_TARGETS`.
- Memory for retrieval is the FAISS index under `memory/`. A 2026-07-23 ablation (Finding 76, E-004) did not distinguish retrieval-on from retrieval-off from ordinary sampling noise on the prompts it actually ran, 29 of 30 of them personal.
- A liveness ledger checks subsystems against evidence outside each subsystem’s own self-report. The check count grew through the summer. A September index row (E-038) says a live query once saw 50 checks. That count is historical. This audit did not query `/admin/liveness-status`.

Recorded repairs in that same document include: a hollow WOLF gate retired 2026-07-04 after it auto-approved keystroke “proposals” into a hash-verified principles file; self-edit dry-run made real so Optuna could compare candidates (Finding 16); deployment refused when the candidate did not score at least as well as production (Finding 19); Modelfile identity restored on `/api/chat` because an explicit system message was replacing it (Finding 46); synthesis token accounting corrected after the identity block leaked into an answer (Finding 53); MLX crash avoidance added, then found blind when macOS stopped writing crash reports (Findings 49, 51, 73); `apply_to_code` moved into the real sandbox because a thread timeout could not kill a hook (Finding 69).

Each of those is a recorded engineering result. This audit treats them as history in `CLAUDE.md`, not as a fresh demonstration.

## 4. Emergence roadmap, July 2026, as recorded

`CLAUDE.md` describes Phases 1–10 and later gap-closure Phases A–C2 (Findings 75–80, 2026-07-23). The recorded pattern is consistent: mechanisms were often real and wired, and the signals feeding them were often thin.

Examples the physiology audit is recorded as measuring (Finding 75, E-003): scheduler boosts gated at 0.6 sat above the observed ranges of coherence, world surprise, and valence; `coupling_estimate` had no consumer at that time; seam detection was not dormant (83 seams in a full parse) even though an earlier note had said zero. Later phases recalibrated thresholds, gave coupling and meta-reflection a consumer, widened the seam candidate pool, and gave valence a small bounded effect on council exploration and Optuna sampling bounds. Those phases are recorded as built and checked by their own sessions. This audit did not rerun them.

Finding 81 records two explicit refusals: the dissent log stays advisory, and curiosity’s one-way read of the world model stays one-way, because closing it would let generated text define “what the world already covered.”

## 5. September 2026 research program

`research/EXPERIMENT_INDEX.md` is a thread index. When that file was written it counted 185 files under `audits/`. A directory walk during this audit counted **539** files. The index author disclosed that E-030 onward was first-hand, 1–8 September was terminal-report level, and earlier rows were title-derived. This audit read the index. It did not re-read the underlying audit bodies, except `audits/2026-09-02_architectural_self_knowledge_investigation.md` around the `log_thought` paragraph.

Recorded results that matter for later Voyager work:

- E-004 / Finding 76. Memory ablation, n=30. Distance between normal and retrieval-removed answers was not distinguishable from a noise-floor rerun (Mann-Whitney p=0.48 in the report’s summary in `CLAUDE.md`). This does not prove memory never matters. The noise was large, and the sample was almost all `personal`.
- E-007 / Finding 87’s neighborhood and R-003. A causal-chain count of self-modification is recorded as 426/463, about 92%, replacing an earlier “near zero” claim. The fitness metric used for the deploy gate was saturated (R-004) until Finding 91 recalibrated it.
- Findings 87–89. On held-out coding tasks, raw candidates solved about 95–96% when any one attempt counted, while synthesized answers landed lower (about 79.8% and 67.9% in the Tier-4 pooled summary in `CLAUDE.md`). The comparison of council versus a budget-matched baseline did not cross the pre-registered significance line (exact McNemar p=0.087). A refactor added an agreement shortcut and a missing-definition check. A later forensic note (Finding 88) says the length-based fallback picked the wrong candidate in the cases checked, and that a RiverBrain score used as a ranker fell below chance once `echo:latest` was removed from the pair (7/18). Finding 89 records that experiment isolation did not stop RiverBrain’s background writer, and that the path constant was redirected before the first load.
- E-018, E-019, R-001, R-002. An authoritative flag can change an answer by being trusted in place of the evidence. Putting verified evidence in context did not reliably change what was generated (0/5 in the recorded generation-time trial).
- E-034 through E-037. Verification held in a passive setting in the recorded 52/52. Under a trap, explicit false verification occurred. A 10-turn ladder captured a false claim with or without an authority label (E-037: all four conditions, 9/9 non-authority by an early turn). `research/OPEN_QUESTIONS.md` still has a heading for Q-008. The index says E-037 answered it. This audit did not re-read the E-037 report, so it does not close that question file.
- E-038. As of 2026-09-11, `echo_projects_autonomy` was recorded as silent for 65.9 hours or more. That is not a current measurement.

`CLAUDE.md` Findings 91–95 continue in the same window: council-rating cursor repaired after log rotation; shadow-model priority in self-edit targeting reversed because its accuracy was below chance; `echo_projects` generation failures traced in part to leading prose and a matplotlib cache path; RAOC harness built; a 12-trial pilot run; the approach classifier widened after too many trials fell in `UNKNOWN`. No claim about the RAOC hypothesis was authorized. This audit did not rerun it.

## 6. October and early November commits

`git log` on this branch, newest first, includes:

| Commit | What the message says |
|---|---|
| `dc8d6eb` | Echo-to-Echo claim thread; grok mailbox ignored; 2026-11-02 protection lock stays off |
| `5ee3ae7` | Per-message persistence outcomes for conversation memory saves |
| `8c767b5` | Review-only notices for `weekly_delta` and echo-state dimensions [1] and [2] |
| `4a800af` | Closures of pending items 20–23; MacBook versus phone location split |
| `2c34dc3` | Audit reports 2026-09-11 through 2026-10-18 |
| `66360eb` | Audit reports 2026-10-19 |
| `4d2932c` | Human ratings folded into the ranking mean |
| `7423d55` | Research-only generic repair proposer |
| `e5acbb0` | Reject path-traversal consumer names |
| `0a134d3` | Optional relay supervision, not yet activated |
| `ea22d75` | Isolate relay consumer cursors |

Other branches exist and were not reviewed: `main`, `vsl-implementation` (separate worktree), `worktree-agent-abe6ecca0408fd0fb`. `gh issue list --limit 5 --state all` returned no rows and exit 0. Pull requests and other repositories were not listed. This is not a full GitHub audit.

`PENDING_DECISIONS.md` says no open rows remain. The 2026-11-02 note also says continuity tests A–E were not authorized, five isolated answers are not evidence that the speaking path uses its cards, and the protection lock stays off. Those sentences were read. The rest of the decision file was not re-read line by line.

## 7. Project Voyager laboratory, 2026-11-08

The laboratory sits in untracked `voyager_lab/`. Its own README says the official mission run has already been executed.

### 7.1 Frozen 25-mission evaluation

**Read this audit:** `voyager_lab/ASSESSMENT.md` sections 6–10 and the Direct answer, plus `voyager_lab/voyager/procedures.py` (opening, templates, `learning_label`).

The parent builds a small world, writes a public brief, and starts `python -m voyager.worker`. The brief includes `problem_class`. The worker does not receive the hidden grade. `procedures.py` states that the planner is a fixed grammar, not a language-model reading of free text. Templates include `copy_value`, `pipeline_sum`, `fold_lines`, `make_then_write`, `resolve_conflict`, and `join_pair`. `learning_label` returns `remember` when the path map equals the stored example, and `procedure_reuse` otherwise.

Observed aggregates (`ASSESSMENT.md`, from `results/summary.json` and `results/RESULTS.md`):

| Metric | Baseline | Engine, lessons on | Ablation, lessons off |
|---|---:|---:|---:|
| Completion | 2/25 = 0.08 | 23/25 = 0.92 | 20/25 = 0.80 |
| Successful recovery (M07–M10) | 0/4 | 4/4 | 4/4 |
| Unsupported completion claims | 23 | 1 | 0 |
| Repeated failed operations | 7 | 0 | 0 |
| Restart recovery (M05, M06, M23) | 0/3 | 3/3 | 3/3 |
| Abstain when required | 0/4 | 4/4 | 4/4 |
| Unfamiliar (M19, M20) | 0/2 | 1/2 = 0.5 | 2/2 = 1.0 |

Baseline passes: M01 (copy `42`) and M24 (a third read of a flaky file returned `55`). Other baseline missions set status `success` on a file the external check rejected.

Engine misses: M20 and M24. Ablation misses: M14, M15, M16, M24, M25. Ablation passes M20.

M19: both arms pass with value `8-1`, learning label `none`. The behavior is the prewritten `join_pair` template. M20 uses the same public sentence and the same path map; the hidden grade is abstain. With no lesson, the budget runs out before a write, status is `blocked`, and the abstain grade passes. With M19’s lesson, the engine skips the probe, writes `4-4`, claims success, and the external grade fails. That is the engine’s one unsupported completion claim. The assessment says lessons lowered the unfamiliar pass rate from 1.0 to 0.5.

M25’s composition rule was written in `procedures.py` before the run. The ablation, with no lesson, makes no tool call.

What this demonstrated: a grammar plus a checkpoint can resume after a killed process, follow a multi-step template, switch operation after a scripted fault, stop on budget, human gate, or unknown read, and leave a record an outside grader can check.

What it did not demonstrate: that Echo read the objective and chose a plan; that M19 was an independently learned skill; that the M20 ablation pass was intelligent abstention; that performance on the toy world transfers to production tools or memory.

The rubric bundle hash recorded in the README is `b8b1bc1fe7056294739bd834c3e4329807b50ef6cdffab67f68f6e32e2af9b9d`. The lock covers the listed `voyager/*.py` modules. It does not cover `self_check.py`, `freeze.py`, or `run_experiment.py`.

### 7.2 CAB proposal

**Read this audit:** `voyager_lab/CAB_ADVERSARIAL_REVIEW.md` opening and closing sections. SHA-256 at audit time: `aceab7c557c8b1860c60572d59ccc266fc55a77310a79a255e0c83e6c5aaf6bf`.

The review’s own verdict is that CAB is not good enough to implement, and that the specified E1 is not good enough to run. M19 and M20 share the public sentence “Read a and b and write them joined by a hyphen,” the same class, and the same slots. The hidden grade differs (`equals` versus `abstain`). A broker told the grade kind would be told the answer. One M19 pass is a trace of a template, learning label `none`. The proposal was not built. The frozen suite was not edited to feed it.

### 7.3 ScratchWriter

**Read this audit:** `voyager_lab/scratch_write/SECURITY_REPORT.md` (opening and unresolved-risk sections) and targeted lines of `IMPLEMENTATION_AND_VERIFICATION_REPORT.md`. Evidence copies live under `voyager_lab/scratch_write/evidence/`. The code was not rerun.

The first writer accepted a caller-supplied root. That is a failed confinement boundary for any caller who can already write: the API does not add a root the caller does not control.

A separate pinned writer was then tested. The security report records a 56-test run whose first execution failed one assertion (`st_nlink == 1` while a temp name was deliberately left, destination nlink 2). The helper was replaced. The second run reported `Ran 56 tests in 0.176s` and OK. The report still lists unresolved risks: a privileged caller can bypass the API; the protected-path list is local; a rename between path check and use was not hammered; a kill can leave a temp file and a partial audit line; cross-process overlap was not executed; the path query is Darwin-specific; the audit log is unbounded. The implementation report records T1 (root substitution) and T8 (protected paths) as PASS on the checks that were authorized. A later change in production FAISS metadata, outside the T8 observation window and while the live server was running, is recorded there as the server’s own writes. Scorer mistakes on early T2 and T8 runs were preserved and were not counted as behavioral passes.

This is a laboratory file-writing result. It was not added to Echo’s tool list.

### 7.4 Ungated file-fact retrieval

**Read this audit:** outcome sections of `voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md` and the postmortem’s conclusions as previously established in `voyager_lab/UNGATED_FILE_RETRIEVAL_POSTMORTEM.md`. The report was not edited. The harness was not rerun.

Question: whether `llama3.1:8b`, offered a confined `read_file` and no production dispatch phrase, would call the tool and return exactly the line stored in an assigned lab file.

Official result: **NOT DEMONSTRATED.**

| Arm | Official result | Bar |
|---|---|---|
| Candidate A | 0/6 exact | at least 5/6 |
| Scaffold B | 0/6 exact | at least 5/6 |
| No-tool C | 0/6 exact | 0/6, met |
| Static gate | 12/12 | 12/12, met |
| Echo characterization D | not run | budget spent |

Separate from the official score: all 12 tool-enabled trials made exactly one `read_file` of the assigned path, and the laboratory tool returned the assigned bytes. Exact quotation of that line alone happened on 0 of 12. Eight finals kept the retrieved line inside extra prose. Four finals (A01, A05, B02, B05) replaced it with a generic sentence that the postmortem did not find in the prompts, harness, schemas, or fixtures. The postmortem’s recommendation is STOP. The cause of the four substitutions is not established. Truncation was ruled out for those replies (`done_reason` stop, short `eval_count`). Condition D did not run.

`voyager_lab/CAPABILITY_GAP_AND_NEXT_EXPERIMENT.md` (2026-11-08) had recommended this experiment and had said the document itself did not authorize a run. The run happened under a later assignment. The gap note’s “GO” is a historical recommendation, not the official result.

### 7.5 Reasoning reliability

**Read this audit:** outcome sections of `voyager_lab/REASONING_RELIABILITY_REPORT.md`. SHA-256: `ee3830b5e92a886420dc0e3ee0264a38fcfe5bc5ac48e3d637ecfef0b4834f0a`. The harness was not rerun. The unused 30th generation was not spent.

Official outcome: **C. EXPERIMENT NOT COMPLETED.**

The design was a two-stage `echo:latest` pilot, not the production council. Stage 1 matched the baseline prompt. Stage 2 added a frozen review turn. Success required a finished comparison: 10 completed baselines and 10 completed stage-2 generations, candidate at least 8/10, margin at least 2, four dimensions at 2/2, and no critical fabrication.

The run used 29 of 30 generations. Four baselines timed out at 180 seconds (A1, C1, D2, E1). Stage 1 timed out on D1. Stage 2 for D1 was skipped because stage 1 failed. Completed HTTP bodies: 6 baselines and 9 stage-2 replies. Printed aggregates were baseline 4/10 and candidate stage 2 3/10. Those aggregates include empty timeout texts. The report says they are not a valid comparison.

Where both baseline and stage 1 returned HTTP 200, the texts were byte-identical at temperature 0. Stage 2 then reversed at least one passing answer into an affirmed false claim (A2) and, on E1, replaced a stage-1 fraction the grader wanted with an abstention. That is an observation inside an incomplete experiment. It is not a completed proof that a review pass always helps or always hurts. The report says raising the timeout or editing the prompt would be a new experiment, and this work does not authorize it.

D1’s baseline prose withdraws a causal claim in words the frozen withdraw-list does not contain (“is not supported” versus “does not support”). The frozen fail stands. It was not hand-rescored.

## 8. What was rejected or left unfinished

- WOLF as a live evaluative gate. Recorded retired 2026-07-04.
- Shadow model as a live accuracy signal. Recorded below chance and removed from live call sites (2026-09-13 in `CLAUDE.md`).
- Treating council synthesis as the place coding skill was missing. The recorded bottleneck was the combination step discarding correct candidates, and the confirmatory gap was not statistically significant.
- Treating Voyager’s 23/25 as an Echo capability. The assessment states the model was not in the loop.
- Treating M19’s `8-1` as learned skill, or M20’s ablation pass as intelligent abstention.
- Implementing CAB on the strength of the proposal. The review says not to.
- Integrating ScratchWriter. Not authorized.
- Calling the retrieval run a success because the tool returned the right bytes. The locked rule required the line alone. Official result remains NOT DEMONSTRATED. Follow-up was stopped.
- Interpreting the reasoning pilot’s 4/10 versus 3/10 as a finished scientific comparison. Official result remains EXPERIMENT NOT COMPLETED.
- Arming the protection lock on 2026-11-02. The bar was not met.
- Multi-turn `messages` through the whole council (Finding 17 Phase 3). Recorded as considered and declined on 2026-07-22.
- Giving the dissent log the power to block a human-applied patch (Finding 81). Left advisory.

## 9. Unresolved

See `FINAL_AUDIT_REPORT.md` for the audit’s own gaps. Substantive project questions still open in the source files include the headings in `research/OPEN_QUESTIONS.md` (Q-001 through Q-010, including Q-008, which the index treats as answered and the question file still lists). Also unresolved, from the lab reports themselves: the cause of the four retrieval substitutions; whether a longer timeout would change the reasoning pilot (not authorized to test); ScratchWriter’s check-to-use race and cross-process overlap; M24’s policy trade; a lesson rule that does not replay a false success; whether production Echo can read this package (it was not given the package).

## 10. Uncertain chronology

- The exact first commit of the predecessor Echo is not reconstructed here. `ORIGIN.md` gives a narrative date context of 2026-07-16 for the written origin, while `CLAUDE.md` discusses earlier incidents (including a 2025 quarantine file). Those earlier dates were not re-derived from `git log --all`.
- Findings 86–95 are written in `CLAUDE.md` as retroactive entries for work landed in September 2026. The dates in the Finding headers are the ones used above.
- E-010 says the preference-provenance protocol was frozen with no live trial as of Finding 86. Later uncommitted experiment trees may exist under `app/experiments/preference_provenance/`. This audit did not inspect that package’s contents, so “still unexecuted” is the index’s statement, not a fresh file census.
- Whether `echo_projects_autonomy` is still silent is unknown. The 65.9-hour figure is from 2026-09-11.
