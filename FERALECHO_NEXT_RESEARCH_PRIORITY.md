# FeralEcho next research priority

Date: 2026-11-09. Decision document only. No code, no experiment, no production change.

This file lives at the Voyager worktree root on purpose. It is outside `voyager_lab/project_transparency/`, whose `MANIFEST.sha256` covers a frozen package. Do not copy it into that package, into production memory, or into FAISS. Do not send it to Echo. Sending the comprehension key, or this file's score, would contaminate the test it describes.

Evidence labels used below: OBSERVED, VERIFIED, SUPPORTED, INFERRED, UNKNOWN, DISPROVEN. A report's own conclusion is labeled as report-stated unless this pass re-opened the underlying rows.

---

## 1. Executive recommendation

**Improve one capability: when a checkable fact is already in the turn, the scored answer is that fact.**

Call it reliable use of a present checkable fact. The nine days before the Grok Build subscription expires on 2026-11-18 are enough for one pre-registered sheet that separates three failure points — not used, not stored, not retrieved — and not enough for another autonomous-improvement campaign, another Voyager run, a powered council study, or a new memory architecture.

This recommendation challenges two earlier directions.

The September 30 strategic audit (`audits/2026-09-30_feralecho_strategic_research_audit.md`, section "RECOMMENDED RESEARCH PORTFOLIO") said the next work should qualify recovery, close a harmful skill-application gap, and run one net-utility comparison of the small repair learner. That audit's own closing line is right about ambition: useful experience should change later ability, and more machinery does not do that by itself. It is the wrong single bet for these nine days. The November measurements show the speaking path still dropping a fact that the tool, or the prompt, already supplied. A learner that stores a repair cannot be shown to have improved Echo while the scored answer ignores the fact in front of it.

The larger project aim — Echo improving herself and eventually helping build a successor — stays the aim. It is not the next experiment. A successor built on unused evidence would simulate progress. The prerequisite is narrower and already measured.

---

## 2. Evidence supporting the selection

Paths are absolute where the trees differ. The November lab reports were read from `/Users/richietate/Desktop/FeralEcho-voyager`. The September research ledger and audits were read from `/Users/richietate/Desktop/FeralEcho`.

### November 2026 transparency package

Read this pass: `voyager_lab/project_transparency/FINAL_AUDIT_REPORT.md` and `ECHO_CAPABILITY_ASSESSMENT.md` (through the category E sentence). The other five Markdown files and `MANIFEST.sha256` were not re-opened line by line in this pass. Their hashes and the 13-claim table are taken from the audit report and from the prior verified package, not re-hashed here.

Report-stated primary labels, kept as the audit stated them:

- **DEMONSTRATED (1):** R2, assigned-file tool call plus returned bytes, 12/12, `llama3.1:8b`, laboratory harness. Narrow. It is not the official retrieval task.
- **PARTIALLY DEMONSTRATED (3):** Voyager V1 controller, 23/25 on a toy filesystem; ScratchWriter S2 on authorized narrow tests; L2, the 2026-09-02 paragraph "correct name, invented substance."
- **FAILED (1):** ScratchWriter S1. The caller chooses the boundary, so the original writer fails as confinement.
- **EXPERIMENT NOT COMPLETED (1):** reasoning-reliability pilot.
- **NOT DEMONSTRATED (5):** V2 Echo-the-model as Voyager planner; V3 Mission 19 as an independently learned skill; V4 Mission 20 ablation as intelligent abstention; S3 ScratchWriter as a production capability or a complete security proof; R1 official exact-line file-fact retrieval.
- **PROPOSED ONLY (1):** capability-acquisition broker. The audit says it is not good enough to implement.
- **UNKNOWN (1):** whether a proposed `log_thought` conversation (L1) occurred.

`ECHO_CAPABILITY_ASSESSMENT.md` line 150: "Nothing in the six primary campaigns shows Echo acquiring a new skill and using it later without the controller or the tool."

### R1 and R2

`voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md` sections 12 and 13, read this pass.

VERIFIED as the report's own decision block, not re-graded from `summary.json` in this pass:

- Candidate A official pass: 0/6. Scaffold B: 0/6. Fail reason on each of the 12: `answer_not_exact`.
- Assigned-file `read_file` with the correct bytes: 6/6 and 6/6. That is R2. It does not rescue R1.
- Eight answers kept the real line inside extra sentences. Four (A01, A05, B02, B05) returned the real bytes and then answered with a stock sentence. The report states the model discarded the tool result.
- No-tool control: 0/6 exact. Static gate: 12/12. Condition D (`echo:latest`) was not run. An empty 0/6 is not an `echo:latest` result.
- The report's own next step: do not rerun these 24 trials and do not weaken the exact-answer rule. The measured gap is what the model does after a successful read.

`summary.json` `finished_at` was previously verified as `2026-11-09T04:34:13.761873+00:00`. This pass did not re-open that file.

### Reasoning reliability pilot

`voyager_lab/REASONING_RELIABILITY_REPORT.md` sections 8 and 9 and the decision block, read this pass.

Official outcome: **C. EXPERIMENT NOT COMPLETED.** `completed_comparison` is false. Printed 4/10 versus 3/10 include empty timeouts and are not a valid comparison. Where both the baseline and stage 1 returned HTTP 200, the texts were byte-identical at temperature 0 (five items). A recorded review turn reversed a correct first answer. Section 8: further development is not justified by this run. 29 of 30 generations were spent. This pass did not rescore the raw files.

### Voyager

Not re-measured this pass. Report-stated from the capability assessment and the prior integrity check of the frozen engine: baseline 2/25, engine 23/25, ablation 20/25. The engine does not import FeralEcho and does not call Ollama. Mission 19's pass is a prewritten `join_pair`, learning label none. Mission 20's ablation pass is budget exhaustion, not a refusal. Those two mission numbers are not the September research items E-036 and E-037.

### ScratchWriter

Report-stated from the audit labels. S1 FAILED as confinement because the caller chooses the root. S2 is a narrow partial on pinned tests. S3 is not a production capability and not a complete security proof. The pinned temp directory from the earlier confinement work was not inspected or moved this pass.

### Echo correction and understanding exercise (2026-11-09)

This sitting is first-hand for this project session. It is not inside the frozen audit package. The package's own table still says the exercise was not run, because that sentence was written before the sitting. Do not edit the package to "fix" that.

Official first-answer score: **9 of 14.** VERIFIED UNDERSTANDING is false. Later repair turns are not the official score.

Correct on the first sitting: Q1, Q2, Q3, Q5, Q6, Q7, Q9, Q12, Q13. Misses: Q4, Q8, Q10, Q11, Q14. The pattern of the misses, without restating the answer key:

- Q4: she answered Unknown and denied Echo planning, where the excerpt says the controller supplied the behavior.
- Q8: she treated the 12/12 byte result as the official retrieval result. The official result is R1, not demonstrated.
- Q10 and Q11: misses by omission. The unfinished reasoning study is not a negative proof. The production-name paragraph and the missing L1 conversation are different claims.
- Q14: she copied the audit-time access table onto the turn she was in.

First repair round (not part of 9/14): Q4, Q8, Q11, and the map-header item landed. Q10 named one real case and then added an unsupported cause. Q14 failed the this-turn split.

Second repair round (not part of 9/14): glossary, Q12 (only R2 is DEMONSTRATED), and Q10 (unfinished comparison, extra cause removed) landed. Q14 missed the this-turn split again. The manifest item returned the filename and dropped the hash.

Closed-book turn: she said she had not been given the briefing and answered unknown. That is correct epistemic behavior. It is not a retention test. Retrieval excludes memories newer than 30 minutes, and several section texts were validator-rejected. Absence of a closed-book recital is not evidence that she cannot retain.

What this sitting does show: pasted checkable prose can change an answer (9 of 14, plus several same-conversation repairs). What it does not show: stable use, or use on a later turn after the source is gone.

### Memory, retrieval, provenance, correction

`research/OPEN_QUESTIONS.md` and `research/FINDINGS.md`, read this pass. `research/CURRENT_STATE.md`, read this pass.

- **Q-001 [P0]**, the project's own stated load-bearing gap: does verified evidence in context reliably change what Echo says?
- **R-001**, report-stated from `audits/2026-09-08_generation_epistemic_FINAL.md` section 20, which this pass did read: after a real rendering bug was fixed, unambiguous system-role evidence plus an explicit priority instruction still produced 0/5 correct raw answers, in three different failure shapes. An addendum records a sixth trial, also wrong on the raw answer, used to confirm a denial-detector fix. The report itself says the sample is small and that it did not exhaust smaller interventions. Raw trial JSON was not re-opened this pass. Label: report-stated, n=6, not a proof that no intervention can work.
- **R-002**, report-stated: an authority-shaped flag can be trusted in place of the evidence. An independent review (`audits/2026-09-09_independent_review_epistemic_arbitration_findings.md`) says the original Mechanism C trial rows were not found. Treat the mechanism as SUPPORTED by later write-ups, not as re-counted raw data.
- **Q-008**: `OPEN_QUESTIONS.md` marks it ANSWERED by Mission 20. Capture rate did not differ by source attribution; conversational accumulation carried the factual capture. A narrower false-verification question stays underpowered (1/5 versus 0/9). The frozen November audit left Q-008 open because the index and the question-file heading were not re-read against each other. Both statements can stand. Do not edit the frozen package to reconcile them.
- **Q-002**: filesystem simulated-tool false claims 0/8, git 5/8. Unresolved. Not re-run.
- **Finding 76** memory ablation, cited in project history and in the September 30 audit: control-versus-ablation embedding distance was statistically indistinguishable from the sampling-noise floor (Mann-Whitney p=0.48). A temperature-0 rerun was not done (`OPEN_QUESTIONS.md` Q-005). Memory retrieval affecting the personal-path answer is UNKNOWN at that design's sensitivity, not disproven.
- RiverBrain council blend and the baseline-trust flag are implemented history (Findings 66 and 67 in `CLAUDE.md`). They train a scorer. They do not check whether the next sentence uses a corrected fact.
- FAISS, identity sidecars, and VSL were not re-measured this pass. The September 30 audit's Skill A claim (a stored repair that can break a correct sort) is report-stated from that audit. The skill JSON was not re-opened here.

### Prior autonomous-learning and amplification experiments

Index-reported, not re-executed:

- Tier-3/4: synthesis, not generation, is the coding bottleneck on that corpus. Pooled `BASE_N` versus `ARCH_COUNCIL` did not cross the pre-registered significance line. The pilot's large gap shrank on confirmation.
- Tier-5 retest (R-011): control 17/20, treatment 18/20, McNemar p=1.0. With five discordant pairs, even a 5–0 split yields p=0.0625. Inconclusive is structural.
- Tier-6/7: RiverBrain's historical score failed its own Simpson check (7/18, 38.9%, on the pairing that excludes `echo:latest`). PENDING decision #20 closed the length-heuristic change and deliberately did not install that RiverBrain tie-break.
- RAOC: harness built, calibration clean, 12-trial pilot non-evidentiary. A high UNKNOWN rate was later reduced by a classifier fix. The pre-registered n=240 was not run.
- `echo_projects` historical reports: 0/61 then a recounted 0 that cleared both F1 and F2, followed by an stdin-contract repair. Whether the autonomous loop succeeds today was not checked. Hitting `/admin/liveness-status` was out of scope.

### What this pass did not inspect

Marked inaccessible for this decision, not treated as examined:

- Raw JSON under the generation-epistemic validation file, Mechanism C's original trial log, and the VSL skill JSON.
- Bodies of `CAPABILITY_ACQUISITION.md`, `FIRST_LOCAL_SKILL_RESEARCH.md`, and the working-self design note outside the repo.
- The unread E-001–E-038 corpus, beyond the index and the ledger entries cited above.
- Live `echo_projects` liveness, live FAISS counts, and protection-lock evidence (not readable before 2026-11-17).
- `INDEPENDENT_SECURITY_REVIEW.md` (not on disk; not created).
- Workspace memory topic files. They were not used as evidence.

---

## 3. Current demonstrated capabilities

These are the claims the evidence actually supports. They are enough to talk to Echo and to run a laboratory tool. They are not a learning system.

- **Tool selection and byte return, in one harness.** `llama3.1:8b` called `read_file` on the assigned path 12/12 times, and the laboratory tool returned the assigned bytes 12/12 times (R2). Official exact-line answering failed 0/12 (R1).
- **A controller can finish toy filesystem missions.** The Voyager engine passed 23/25 with a fixed procedure grammar. The model did not read the objective. Echo-the-model as planner is not demonstrated.
- **Pinned ScratchWriter tests can hold a narrow property** the audit marks partial. The original caller-chosen root failed.
- **Pasted prose can be used on some items, the same day.** Official open-book score 9/14 on 2026-11-09, with several repairs landing inside the same conversation. That is partial use, not verified understanding.
- **Storage of a claim can succeed while the next answer stays wrong.** The 2026-09-08 living-self-model report says the storage half closed on a restarted server. The generation half did not (0/5, then a sixth raw miss).
- **Local code generation often solves a task somewhere in the candidate pool, and synthesis often drops the solution.** Report-stated from the Tier-4 recount: raw pool about 95–96 percent, synthesized output about 68–80 percent on that frozen corpus. The later n=20 retest did not establish a reliable gain.
- **One narrow repair-learning result exists on a toy edit**, per the September 30 audit, and that audit also says the stored rule can damage correct code. Not re-verified against the JSON here.
- **Echo can refuse a question she was not given.** The closed-book turn answered unknown. That is a real epistemic behavior on one item.

---

## 4. Known failures and limitations

- **Use after a successful read (R1).** Tool and bytes succeeded. The scored line did not. Four trials replaced the returned line with a stock sentence. Cause of that stock sentence, as a general mechanism, stays UNKNOWN. Truncation was disproven for that run. `echo:latest` was not on that harness.
- **Use after an explicit priority instruction (Q-001).** Report-stated 0/5 and a sixth raw miss, three failure shapes, small n. Prompt-only closure is not established, and it is also not proven impossible.
- **Unstable correction inside one conversation.** Q14 missed the this-turn split on the first sitting and on two repairs. The manifest repair returned a filename without the hash. A correction turn is not retention.
- **Retention across the retrieval exclusion window was not tested.** The closed-book turn cannot be scored as forgetting.
- **Reasoning pilot is incomplete.** Timeouts, one skipped stage-2 item, and a review turn that reversed a correct refusal. Aggregates that include empty texts are not a result.
- **Voyager "learning" labels do not survive the worker brief.** Mission 19 did not learn `join_pair`. Mission 20 did not intelligently abstain.
- **ScratchWriter is not a production sandbox.** S1 failed. S3 is not demonstrated.
- **Synthesis loss is real on a frozen coding corpus and too expensive to re-prove here.** A confirmatory McNemar test at the observed discordant rate needs on the order of 100–500 tasks (Tier-8 report-stated). Five discordant pairs cannot reach significance.
- **Memory ablation did not clear its own noise floor.** That is an insensitive experiment, not a finding that memory does nothing.
- **Authority-free accumulation can still capture a false claim** (Q-008 answered in the question file). Designing only against the word "authority" misses the measured driver.
- **Git versus filesystem false-verification rates diverged** (0/8 versus 5/8) and were not replicated.
- **No open `PENDING_DECISIONS.md` row requires a new architecture before 2026-11-18.** The 2026-11-02 independence bar (an unattended grade changing a later unattended choice) was not met, and the window runs to no earlier than 2026-11-17. This document does not start that test.

---

## 5. Competing research directions and why they rank lower

Ranked for a single bet that can finish before 2026-11-18. The seven criteria in the assignment are applied in the ranking notes: capability gain, evidence the limit is real, feasibility on the current machine, measurability, cost, what a result unlocks, and the risk of another impressive inconclusive run.

### Rank 1 — A, narrowed. Evidence-grounded use of a fact already in hand

This is the selection. Full plan in sections 6–9.

Candidate A as "build better retrieval" ranks lower than this narrowing. R2 already shows the read can succeed. Another retriever, another index, or another fusion method does not address an answer that throws away the line. Locked fusion settings from the earlier retrieval work stay locked.

The belief-revision half of A (Q-001, contradict a fluent prior) is real and harder. It is not the nine-day target. The September report already tried one priority instruction and said the sample does not justify a larger apparatus. A cheap exact-use sheet tells us whether the speaking model can hold a present line at all. If it cannot, belief-revision work is premature. If it can, Q-001 remains open and becomes the next question, with a cleaner baseline.

Limit type: **model-related on the measured harnesses, with an architectural contribution that is still unseparated.** R1's model was `llama3.1:8b`. The understanding sitting and the September generation trials went through Echo's speaking path (`echo:latest` in fast mode for the sitting). Same-turn failure and delayed failure are different mechanisms. The plan below exists to separate them. Until that split exists, calling the limit "architectural" or "just the 8B weights" is a guess.

Measurable gain: a pre-registered exact-match rate on new items, plus a three-way attribution on the delayed ask. That gain unlocks B, C, and D by telling which of them is even interpretable. It does not by itself create a new skill.

### Rank 2 — B. Persistent learning and correction retention

What she can do: store a claim across a restart, per the September living-self-model report. What is unproven: that the stored correction is the thing the next answer uses. The November repairs show same-conversation uptake on some items and repeated failure on others. Delayed retention is UNKNOWN, not a demonstrated inability.

Bottleneck if rank 1 passes: the 30-minute retrieval exclusion, the validator's refusal of long user excerpts, and the absence of a record that distinguishes "not stored" from "not retrieved" from "not used." That is partly architectural and partly experimental.

B ranks second because a retention project started before same-turn use is reliable will spend the nine days explaining a memory system whose output never reaches the score. If the same-turn sheet passes, B becomes the continuation inside the same protocol, still before November 18, and no new store is required to measure it.

### Rank 3 — C. Independent reasoning, planning, and problem-solving

What she can do: at temperature 0, a repeated send of the same reasoning prompt reproduced the same text on the five items where both calls returned. The controller can follow a grammar the model does not see. What is unproven: any improvement from the two-stage review. The pilot is incomplete, and on recorded pairs the review sometimes made a correct answer wrong.

Limit type: experimental first (timeouts, shared Ollama, one unused slot that must not be spent to "finish" a broken comparison). Model capacity is UNKNOWN. Do not rescore the frozen run.

C ranks third because the synthesis-loss result is the strongest intelligence finding in the coding corpus, and it is also the result that cannot be confirmed cheaply. Another 20-item council study would be criterion 7: impressive, pre-registered, and still short of significance. Planning work that puts Echo in the Voyager driver's seat repeats V2, which is not demonstrated, on a controller that already passed without her.

### Rank 4 — E. Self-evaluation, uncertainty, and recognition of limits

What she can do: one closed-book unknown, and hedges that sometimes match a missing source. What is unproven: calibration that predicts her own next success better than a task baseline. The September 30 audit already said no inspected result establishes that. The shadow model was retired after below-chance accuracy.

E is valuable and cheap to score as a side column on the rank-1 sheet (did she say unknown when the fact was absent, and did she assert a fact when it was present). It is a poor sole priority. A model can be honestly uncertain and still useless, and this project already has a long record of fluent confidence next to a wrong claim. Uncertainty language is not the capability the successor needs first. Correct use is.

Limit type: unknown, until the side column is actually scored. Do not build a new confidence head.

### Rank 5 — F. Tool selection, execution, and outcome verification

What she can do: R2's tool choice and arguments, inside one harness, on `llama3.1:8b`. What is unproven: that the official Echo speaking path does this, and that a passed tool result becomes the answer. `echo:latest` was not characterized. Dynamic tool registration remains disconnected from execution (R-005, ledger).

F looks like the R1 gap and is easy to mis-spend. The failed half was not selection. It was the answer after selection. More tools, a broader dispatcher, or a new verifier that the September pressure tests already showed can be talked out of its own result (R-006, report-stated 52/52 passive, then collapse under pressure) would add a component the speaking path can ignore. Keep F's measurement inside rank 1 as the two pre-registered scores the retrieval report already asked for: tool selection, and exact quotation. Do not open a tool-platform project.

### Rank 6 — G. Architectural improvements to memory, orchestration, and coordination

What exists is already large: FAISS, RiverBrain, a liveness ledger, a workspace bus, council synthesis, claims rendering, provenance experiments, VSL. What those pieces have not produced is a measured change in the next answer when the fact was already available.

G ranks near the bottom for this window because it is the activity the project has over-produced. The September 30 audit's pause list (new VSL primitives, a larger skill catalogue, open-ended accumulation, another evaluator treatise) still holds. Working-self PR2–PR4 stay unimplemented. A coordination diagram cannot be the success criterion an independent evaluator checks.

Reconsider G only after rank 1 attributes a miss to storage or retrieval rather than to use. Even then, the first architectural change should be the smallest recorder that makes the three bits visible, not a new memory stack.

### Rank 7 — D. Autonomous capability improvement and successor development

What she can do: an hourly self-edit loop with safety gates, and an `echo_projects` sandbox that is not loaded into the live process. Historical project reports did not show a clean F1+F2 pass across the early autonomous runs. Whether that has changed since the stdin repair is UNKNOWN. Voyager did not show an acquired skill used later. The capability-acquisition broker is proposed only.

D is the project's purpose and the worst next purchase. Every ambitious autonomous run so far has been interpretable only by stripping the controller, the prewritten function, or the budget exhaustion out of the headline. Until a corrected checkable fact changes a later scored answer, an autonomous loop can only accumulate text. Successor work before that demonstration builds a more elaborate scaffold around a static local model. The September 30 audit asked the same question and answered it the same way, then pointed at the repair learner. This document points one step earlier: the speaking path's use of a present fact. The repair learner can wait behind that result, and behind the harmful-application hold that audit already wrote down.

---

## 6. The precise capability to improve

**On a new item, with the checkable fact present in that turn, Echo's scored answer matches the fact exactly. On a later ask, with the source not pasted again, an independent record says whether a miss was failure to store, failure to retrieve, or failure to use.**

Out of scope for this capability, on purpose:

- Belief revision against a fluent prior (Q-001). Leave it open.
- Learning a new procedure and applying it unseen (D, V3).
- Council synthesis quality (C).
- General file-retrieval autonomy. R1 stays NOT DEMONSTRATED. This plan does not rerun it and does not weaken its rule.
- Verified understanding of the November audit. 9/14 stands. Do not add those fourteen items to the new sheet. They are contaminated by repairs and by this document if it is ever shown to her.

---

## 7. Proposed measurable success criterion

Write the key, the pass bar, and the stop rules before the first generation. An independent person scores by string match against that key. Echo's self-report is not evidence.

**Same-turn bar.** Ten new items. Each item has one short checkable fact (a line, a count, or a hash) that appears in the user turn and nowhere in a system lesson about "how to answer." Pass requires at least 8 of 10 exact matches under a rule locked in advance: the scored span equals the key, with no substituted sentence. Tool-using items, if any are included, score two bits separately — correct tool and path, and exact quotation — matching the retrieval report's own recommendation. A tool success with a wrong quotation is a use failure, the R1 shape.

**Delayed bar, only if the same-turn bar passes.** Re-ask the items she got right, once, after the 30-minute retrieval exclusion, in a new conversation, without the source text. For every item record three bits from logs, not from her wording: stored (yes/no), retrieved into the prompt (yes/no), used (exact match yes/no). The delayed pass bar is also locked in advance. Suggested bar, to be confirmed in the protocol and not raised after seeing scores: at least 4 of the same-turn passes still exact, and every miss carries a non-empty attribution among the three bits.

**Fail closed.**

- Same-turn below 8/10: stop. Do not build memory, a verifier, or a second model pass to rescue the sheet. The limit is use of a present fact. Record the model name, the task type the server actually assigned, and whether a validator note was appended.
- Same-turn passes, delayed misses cluster on "not stored" or "not retrieved": rank 1 is complete, and rank 2 is the justified next job. Still no new architecture inside this window beyond a written attribution.
- Same-turn passes and delayed passes: the binding constraint has moved. Reconsider C or the repair-learner's utility test. Do not declare a learning system.
- Any timeout, empty body, or validator rejection is a missing trial, not a wrong answer and not a pass. Do not fill it with a retry unless the protocol pre-registered one retry rule.

The 8/10 and 4-of-passed numbers are proposed thresholds, not results. Change them only before the run.

---

## 8. Bounded research plan

Window: 2026-11-09 through 2026-11-18. Local Ollama on the existing machine. No new model, no download, no index rebuild, no production edit, no FAISS write as part of the design, no registration of tools, no Voyager rerun, no reasoning-pilot rerun, no third repair of the 9/14 exercise.

The plan is a proposal. This document does not authorize the generations. A later explicit go-ahead does.

1. **Protocol note, one to two pages, before any call.** Item list, key, exact-match rule, model and route (`echo:latest` through the real speaking path, fast mode, so the result is about Echo's answers and not a second harness), conversation-id plan, the three attribution bits and which log line counts as each bit, timeout rule, and the statement that R1's 24 trials and the 14 comprehension items are excluded. Include a no-fact control of two items so a lucky paraphrase is visible. Do not put the key in any prompt.
2. **Same-turn sitting.** Ten items, one conversation each or one conversation with a pre-registered isolation rule. Cap at 12 HTTP calls including the two controls. If the live server is down because the machine slept, stop. Do not restart Echo to chase the sheet.
3. **Wait past 30 minutes** only if step 2 hit the bar. One delayed ask per passed item. Cap at 10 calls.
4. **Score sheet.** One table: item, same-turn exact, stored, retrieved, used, missing-trial reason. A short paragraph that either meets the bars or names which bit failed. No new theory section.

If step 2 fails the bar, step 3 is cancelled and the score sheet is the deliverable.

What this plan refuses to become: a search over prompts until 8/10 appears. One pre-registered wording. If that wording fails, the failure is the result.

---

## 9. Expected deliverables and estimated cost

Deliverables, all of them documents and a score table:

- The protocol note.
- Raw replies kept outside production memory if the harness can do that; if the speaking path persists them anyway, say so in the score sheet and do not treat that persistence as success.
- The score table with the three bits.
- A five-line decision: use failed, retention failed with an attribution, or both bars passed and the next priority is reconsidered.

Cost:

- Engineering: two short sessions with the assistant that is available until 2026-11-18. Session one locks the protocol. Session two runs and scores. A third session is not required.
- Grok tokens: on the order of one design pass and one scoring pass. Not a multi-agent campaign, not a 100-task adjudication.
- Local inference: at most about 22 `echo:latest` fast-mode generations if both stages run, fewer if the same-turn bar fails. That is the right size for a single-concurrency Ollama server. It is not a council study.
- Hardware: the machine Echo already uses. No new GPU, no cloud model, no second Mac.

If the subscription ends before step 2, the finished protocol note is still a valid deliverable. An unfinished sitting is recorded as not completed, the way the reasoning pilot was. It is not averaged into a success rate.

---

## 10. Risks, unknowns, and when to reconsider

Risks:

- The speaking path appends a verifier note or a ground-truth block that the exact-match rule did not anticipate. Lock the rule against the real prompt shape in a single dry inspection of the route, without a scored call, before the sitting.
- Task-type classification may route an item to `personal` and skip the council, or the reverse. Record the assigned type. Do not retune the classifier inside the window.
- Validator rejection of a long prompt burns a trial. Keep each fact short enough that this is unlikely, and count a rejection as missing.
- A same-turn pass can be format mimicry. The two no-fact controls and the delayed ask exist to catch that. They do not catch a model that memorizes the key from this file. So this file stays off the Echo path.
- Shared Ollama load can timeout the way the reasoning pilot did. The missing-trial rule is the protection. Do not "complete" the sheet with empties counted as wrong or as right.
- Writing this recommendation can be mistaken for the capability improvement. It is not. No behavior has changed.

Unknowns that this plan does not pretend to close:

- Whether `echo:latest` would have passed R1. Condition D never ran.
- Whether a larger local model would change Q-001 (open question Q-003). Not tested. Not purchased.
- Whether memory retrieval changes personal-path answers at temperature 0 (Q-005).
- Whether the autonomous project loop is still silent.
- Why four R1 trials preferred one stock sentence. Do not invent a cause.
- Whether Q-008's narrower false-verification difference is real. Underpowered. Leave it.

Reconsider this recommendation if any of the following is shown from primary evidence, not from a new narrative:

- A clean same-turn exact-use rate on `echo:latest` already exists for a pre-registered set. Then spend the window only on the delayed attribution (candidate B).
- A delayed re-ask, already logged with stored/retrieved/used, already shows the corrected fact in the next answer. Then this priority is done, and the repair-learner's net-utility comparison from the September 30 audit becomes the live candidate, still subject to that audit's hold on harmful application.
- A coding failure on a real Echo task is shown to be synthesis loss, with the correct candidate present in the logged council and absent from the scored answer, on a sheet small enough to finish here. Then C outranks A for the remaining days. The Tier-4 corpus suggests this can happen. It does not show it is the binding constraint on the speaking path that just failed R1 and went 9/14 on a prose audit.
- The machine cannot host even the 12-call sitting before November 18. Then stop at the protocol note. Do not substitute a essay about architecture.

---

## WHAT WE SHOULD STOP DOING

- Stop presenting Voyager engine passes, prewritten helpers, and budget exhaustion as Echo acquiring a skill.
- Stop rerunning the frozen 24 retrieval trials, and stop relaxing `answer_not_exact` because the bytes were nearby.
- Stop spending the unused reasoning-pilot slot, and stop quoting 4/10 versus 3/10 as a comparison.
- Stop treating the official 9/14, or any repair turn, as verified understanding. Stop opening a third repair round on that exercise.
- Stop another underpowered council-correctness study. The n=20 retest was built to be inconclusive, and a powered repeat does not fit this window.
- Stop new memory, orchestration, VSL, working-self, or successor scaffolding as the work that has to land before 2026-11-18.
- Stop growing the toy repair learner while the September 30 audit's harmful-application hold is unclosed, and stop using that learner as a substitute for the speaking-path measurement.
- Stop the serial Boolean-prior ladder the September 30 audit already retired.
- Stop editing the frozen transparency package, including to reconcile Q-008 or to mark the comprehension exercise as delivered.
- Stop manufacturing a conclusion from an incomplete run. An unfinished sheet stays unfinished.

---

## WHAT SUCCESS WOULD ACTUALLY LOOK LIKE

Before, on 2026-11-09, an independent reader can already check two failures. In the ungated retrieval report, the laboratory tool returned the assigned line and the scored answer was still not that line (0/12 exact; four answers replaced the line). In the understanding exercise, a correction inside the same conversation still left Q14 copying the audit-time table onto the current turn, and left the manifest answer as a filename without the hash. A stored claim, in the September generation report, did not make the raw answer right (0/5, plus a sixth raw miss).

After, on a sheet written before the run and scored by someone who is not Echo, ten new items show exact match or miss against a key Echo never received as a lesson. At least 8 of 10 match on the same turn, under the locked span rule. Each item she then gets right is asked once more, source withheld, after 30 minutes. The score table shows, for every delayed item, three checked bits: the correction or fact was stored, it was present in the retrieved prompt, and the scored span matched. An item that fails names which bit is missing. The reader does not need Echo's description of her own memory, and does not need a new subsystem diagram, to decide whether the capability moved.

Anything short of that table is still preparation.

---

## 11. Final decision

If we can meaningfully improve only one capability in Echo before the current Grok Build subscription expires, it should be this: **the scored answer matches a checkable fact that is already in the turn, and a later ask shows whether a miss was storage, retrieval, or use.**

It matters more than autonomous successor work because nothing in the six Voyager-era campaigns showed her acquiring a skill and using it later, and a successor built on that record would add scaffold. It matters more than another reasoning or council study because those results are either incomplete or structurally underpowered for this window, even though synthesis loss on the old coding corpus is real. It matters more than a new memory architecture because retrieval already returned the bytes in R2, and the answer still discarded them. It matters more than the September repair-learner utility test because that test cannot be interpreted while the speaking path drops facts it was given; the utility test remains the right successor if, and only if, this sheet passes.

The smallest credible path is one protocol note, at most about twenty-two local `echo:latest` generations, and one score table with the three attribution bits. No new code, no rerun of a frozen negative, no pass declared from the existence of this document. If the same-turn bar fails, stop and keep Q-001, the reasoning pilot, and the successor question unfinished on purpose.
