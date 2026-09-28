# FeralEcho research-direction reassessment — 2026-09-22

**Decision: B — keep AP-0 as a component test; pursue a different primary research program.**

FeralEcho's broad ambition remains plausible at a bounded system level. Its current research emphasis is misordered. The next scientific target should be **verified improvement in how the system performs a useful class of work from its own prior outcomes**, under fixed resource and human-assistance budgets. Improvement in its ability to acquire new capabilities is a subsequent, stronger target.

I would stop treating proof that an experience-derived file survives a restart as the main obstacle. I would also stop treating compilation, retrieval or unchanged foundation-model weights as automatic disqualifications. The immediate problem is a poorly established relationship between the feedback FeralEcho receives, the state it changes, the decisions that consume that state, and independently measured usefulness.

**My strongest architectural inference:** FeralEcho has more mechanisms for recording, proposing and changing things than for selecting changes because they improve future performance. That imbalance can produce indefinite activity without cumulative progress.

This recommendation supersedes the project-level priority implied by my AP-0 audit's next-step recommendation. The proposed schema/representation diagnostic remains useful for understanding AP-0. It is not the highest-value next project for FeralEcho.

## Basis and limits

**Repository evidence** below means source inspected during this reassessment, existing raw records reaggregated without executing candidates, or the completed AP-0 audit. **Inference** means a conclusion about the architecture or research priorities. **Hypothesis** identifies an untested causal proposal. **Speculation** identifies a more distant possibility.

This was a strategic reassessment, not another exhaustive forensic audit. Historical success labels outside AP-0 were counted from their existing records; I did not independently rerun their graders. I read previous capability/evaluator investigations as navigation and comparison, then checked the relevant source and selected raw artifacts. Claims about the live running process are not inferred merely from current source.

No production imports, pickle loads, model calls, training, self-edit attempts, service operations or new experiments occurred. The sole new file is this assessment. AP-0 and its report were not modified.

## 1. What the repository actually establishes

### Existing capability is substantial, but its interpretation needs care

| Mechanism or evidence | What is established at the inspected boundary | What is not established |
|---|---|---|
| Local generation and instruction use | AP-0's independently regraded H arm passes 44/54 versus 0/54 absent/foreign/wrong-note controls | Autonomous acquisition or improvement of the base model |
| Direct coding capability | Existing Tier-4 records contain 74/84 passes for direct Qwen | General reliability outside these old tasks or under today's complete runtime |
| Adaptive statistical state | RiverBrain updates classifiers, scalers and model/task performance statistics, persists them, and reads statistics in selection | That the signals measure correctness, or that updating them improves later outcomes |
| Persistent retrieval | Conversation construction injects selected FAISS memories with source/history boundaries | That more stored text increases competence, or that retrieval is the main control path for autonomous work |
| Self-editing | The retained attempt ledger contains 1,294 attempts and 15 deployments | That any deployment improved task-solving capability |
| Generated code transformation | Current source defines a top-level apply_to_code hook; retained invocation records contain 2,180 changed outputs among 3,564 calls | That a changed string is an improved program |
| Small learned models | Task-type classification has learned parameters and a prediction consumer; DualLearner contains actual neural optimization and checkpoint saving | That all learned parameters influence useful decisions, or that foundation-model weights are being trained |
| Bounded tool use | A real model/tool-result loop exists for file reading, memory search and thought logging | A general persistent planner that reliably resumes and completes arbitrary projects |
| Autonomous initiation | Timed/background routines choose prompts, fetch, reflect and attempt projects or self-edits | A measured increase in useful completions per human intervention |
| Provenance and liveness | File/process identity, trace IDs, state records and functional checks provide unusually useful observability | Semantic correctness, causal credit assignment, or developmental continuity merely from matching hashes |

Primary paths: [RiverBrain and routing](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:758), [conversation memory construction](/Users/richietate/Desktop/FeralEcho/app/core/conversation_service.py:78), [memory retrieval](/Users/richietate/Desktop/FeralEcho/app/core/memory_bridge.py:410), [tool dispatch](/Users/richietate/Desktop/FeralEcho/app/core/echo_tool_dispatch.py:386), [task classifier](/Users/richietate/Desktop/FeralEcho/app/core/task_type_classifier.py:177), [DualLearner](/Users/richietate/Desktop/FeralEcho/app/learning/dual_learning.py:225), [provenance primitive](/Users/richietate/Desktop/FeralEcho/app/core/provenance_check.py).

### The historical architecture sometimes discards available competence

Reaggregation of both [Tier-4 raw result files](/Users/richietate/Desktop/FeralEcho/audits/tier4_apparatus/stage1_results.jsonl), including [stage 2](/Users/richietate/Desktop/FeralEcho/audits/tier4_apparatus/stage2_results.jsonl):

| Historical condition | Passes / tasks | Recorded generation calls |
|---|---:|---:|
| BASE_1: direct model | 74/84 | 84 |
| ARCH_PIPELINE_ISOLATED | 54/84 | 84 |
| BASE_N: multiple generations plus synthesis | 67/84 | 336 |
| ARCH_COUNCIL | 57/84 | 336 |

At least one condition passes **82/84** tasks. Relative to direct generation, BASE_N rescues five failures but introduces twelve regressions; council rescues six but introduces twenty-three; the isolated pipeline rescues four but introduces twenty-four.

These are historical labels from an imperfect apparatus, not a new controlled comparison of today's software. The 82/84 figure is a **hindsight upper bound across observed outputs**, not a deployable selector, a compute-matched result or permission to use hidden answers to choose outputs. Nevertheless, the pattern is important: additional machinery can lose capabilities the worker already possesses.

A later [Tier-5 retest](/Users/richietate/Desktop/FeralEcho/audits/tier5_retest/tier5_retest_results.jsonl) records 18/20 treatment passes versus 17/20 control passes. Its [driver](/Users/richietate/Desktop/FeralEcho/scripts/run_tier5_retest.py) toggles agreement/completeness safeguards and runs treatment first. That small result does not establish either a broad council advantage or that councils are always harmful.

**Inference:** a strategy-selection problem is worth testing before another capability-creation claim. But even perfect selection among these recorded outputs offers only eight additional successes beyond the direct baseline. The opportunity is bounded; it must earn further investment on fresh tasks.

### The learning signal is often aimed at the wrong quantity or state

[RiverBrain.learn](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:809) trains against a response-quality heuristic and updates model/task means. [score_model](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:995) reads those means for ranking. In contrast, learn_from_sandbox_outcome updates classifiers and sandbox counters, **not those ranking means**. Explicit user ratings also train classifiers without directly updating that mean in their own method. Thus “the system received feedback” does not imply that the decisive selector learned from it.

The coding [quality scorer](/Users/richietate/Desktop/FeralEcho/echo_quality_scorer.py:296) rewards syntactic/control-flow structure; it does not establish functional correctness. The [self-edit deployment gate](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_manager.py:2170) accepts a candidate when its heuristic score is no worse than the current score. All **15 deployed records** in the retained [attempt ledger](/Users/richietate/Desktop/FeralEcho/memory/self_edit_attempt_ledger.jsonl) have **4 versus 4** scores. This does not prove all fifteen were useless; it proves their admission criterion did not demonstrate improvement.

The feedback path is not wholly absent. Current self-edit prompts consume a recent outcome delta and a recent failure through [_recent_outcome_note and _attempt_ledger_evidence_section](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_manager.py:2757). These are task-type-level, recency-based signals, not verified causal attribution to a reusable strategy. Calling that tracker universally “write-only” would rely on stale comments.

There is also an inspected credit-assignment gap: [generate_code_from_plan](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_manager.py:1797) selects a model name, then calls echo_query without binding that selected model to the request, and later attributes the code to the earlier name. [echo_query](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:1524) can use council synthesis or another selection. Its ordinary path also learns on a final response after the deliberation layer has already learned on it. These source paths do not establish the frequency of misattribution in live traffic, but they show why trace IDs and growing observation counts alone cannot certify correct learning credit.

### Earlier isolated records already point toward a more useful experiment

The [recursive-learning component records](/Users/richietate/Desktop/FeralEcho/audits/recursive_learning_ground_truth/r1_r3_results.json) explicitly use authored fixed workers, not live Echo inference. They show a correct simple function receiving heuristic score 2 while an incorrect structurally elaborate function receives 4. Verified-outcome updates select the correct fixed worker; reversed updates select the wrong one. The [producer](/Users/richietate/Desktop/FeralEcho/audits/recursive_learning_ground_truth/r4_producer.json) and [consumer](/Users/richietate/Desktop/FeralEcho/audits/recursive_learning_ground_truth/r4_consumer.json) record preserved statistics across different PIDs and 24/24 held-out successes for the selected correct worker.

The later [finite accumulation fixture](/Users/richietate/Desktop/FeralEcho/audits/recursive_learning_ground_truth/accumulation.py:114) stores explicit context-to-worker scores. Its recorded contextual policy goes 30→50→70→90 correct out of 90 while the global/frozen policies stay at 30. It also fails completely under the final changed mapping. That is useful evidence about conditional state and drift, **not autonomous abstraction or improving acquisition competence**.

The unresolved project question is whether an analogous outcome-to-policy connection improves real local-model work on new tasks. Another toy demonstration that a lookup table persists is unnecessary.

## 2. Is persistent accumulated competence the right next target?

**As a long-term organizing hypothesis: yes, if operationalized. As the immediate experiment: too broad and too easy to pursue through proxies.**

Three objectives should be distinguished:

1. **Competence accumulation:** experience leaves state that improves later useful performance without losing previous gains.
2. **Improved acquisition competence:** prior experience reduces the evidence, attempts, computation or assistance needed to learn later tasks.
3. **Developmental continuity:** the system preserves relevant commitments, evidence, uncertainty, capabilities and unfinished work across interruptions, and revises them coherently when circumstances change.

A system can achieve one without the others. A durable task journal may improve continuity without learning. A learned router may improve work without inventing a new skill. A reusable abstraction may improve acquisition without any foundation-model update.

The immediate target I recommend is:

> Can verified consequences of FeralEcho's own attempts improve its later choice of solving strategy on a useful, bounded workload, beyond the best frozen policy at the same cost?

Measure independently verified completions under a fixed inference budget, with latency, wrong answers, abstentions and human interventions reported separately. Do not reduce all of these to an adjustable utility score after seeing results.

This is a tractable claim about system-level learning. It is also an engineering decision: if adaptation cannot beat a simpler fixed policy, retain the simpler policy. Making the system better matters more than ensuring that the successful explanation includes learning.

“Persistent accumulated competence” should become a claim supported by repeated retained improvements, not a phrase that determines every experiment in advance.

## 3. What is actually missing?

**Inference, ordered by immediate leverage:**

| Candidate bottleneck | Assessment | Discriminating evidence |
|---|---|---|
| Retention | Present for files, vectors, statistics and some histories; consistency/revision limitations remain | Same verified useful state improves behavior after reload and under later revisions |
| Trustworthy evaluation | Most immediate weakness for coding/self-edit growth; safety, importability, stylistic quality and correctness are conflated | Outcome-based selection beats heuristic selection on unseen tasks; adversarial evaluator probes fail |
| Credit assignment and consequential update | Feedback often reaches a different state from the state used for decisions; action identity can be ambiguous | A bound outcome changes the intended policy and improves future decisions; shuffled outcomes do not |
| Stable useful work and task continuity | Autonomous initiation is stronger than evidence of durable goal execution/resumption | More verified tasks finished per intervention, including interrupted tasks, with no-learning controls |
| Induction and hypothesis generation | Frozen LLMs provide candidates; AP-0 shows limits but does not establish a universal local-model incapacity | Correct schemas/representations separate induction from execution; sufficient candidates exist before selection is blamed |
| Abstraction formation | No inspected general loop discovers, validates and reuses abstractions with measured cross-task benefit | Learned reusable components improve genuinely new compositions beyond full-solution retrieval |
| Metacognition | Self-reports, heuristics and agreement are not calibrated decision competence | Confidence predicts independent failure; test/retry/abstain choices improve cost and correctness |
| Autonomous curriculum | Novel prompts and weak-task scheduling exist, but selection for transferable learning progress is unestablished | Chosen practice improves later blinded tasks more than matched random practice |
| Modification of the learner | Possible through policies/programs/small models; modifying itself is not the first necessity | Changed acquisition policy lowers future learning cost beyond fixed-policy baselines |

This is a combination problem, not one missing magical primitive. The most immediate pair is **valid outcomes plus correct assignment of those outcomes to a state that controls future action**. Better evaluators alone do nothing if they only write logs. More powerful generators alone can worsen optimization against the wrong target.

The base models may also be a hard limitation on some tasks. If no proposed candidate solves a task under a sensible search budget, routing cannot create a correct candidate. That possibility must remain live rather than being explained away by apparatus defects indefinitely.

## 4. Frozen models, system learning, and a correction to our framing

A frozen pretrained model does not update its weights through ordinary inference. FeralEcho can nevertheless change its policy, executable procedures, search distribution, representations, external memory and small learned models. Those changes can constitute learning at the system level if experience causes a retained improvement on later work.

Conversely, weight changes do not guarantee useful learning. DualLearner's optimization reconstructs the first dimensions of event embeddings; I found training/export paths but no inspected response/routing inference consumer of that learned projection. A falling reconstruction loss is not evidence of increasing FeralEcho competence. This is an especially concrete example of why “weights changed” is the wrong admission criterion.

**The compiler objection needs a boundary.** AP-0 does not distinguish a fixed example-to-configuration mechanism from a stronger acquisition mechanism. That remains true. It does **not** follow that useful configuration inference, learned selection or accumulated executable skills are scientifically worthless.

Every implemented learner begins with some pre-existing update algorithm. A fixed algorithm can update an expressive policy or library in ways that improve future learning. No behavioral test can exclude every possible fixed program that emulates its observations. The productive question is what was acquired, what later performance it changes, and which simpler specified baseline explains the gain.

Accordingly, my longitudinal addendum is best understood as a stringent **test of improving acquisition competence**, not the minimum definition of all system learning. Requiring all task records to be removed is a useful mechanism ablation, but would wrongly exclude some legitimate skill-library learning if imposed universally. Likewise, a system matching a strong fixed meta-learning baseline might still learn; it would lack evidence of an advantage beyond that baseline.

Memory, retrieval, configuration and compilation are **candidate mechanisms**, not mutually exclusive alternatives to learning. To meet the project's stronger ambition, however, FeralEcho must demonstrate more than old-answer replay: new combinations, improved acquisition efficiency, reliable adaptation to changes, or better decisions on tasks whose solutions were not previously stored.

The published [Reflexion work](https://arxiv.org/abs/2303.11366) explores feedback stored as text rather than foundation-model updates. [Voyager](https://arxiv.org/abs/2305.16291) uses an executable skill library and curriculum with GPT-4. These are precedents for mechanisms, not evidence that FeralEcho's local models can reproduce their reported results or that reflective text necessarily generalizes.

## 5. AP-0's proper place

AP-0 tests a plausible prerequisite **for one carrier-mediated architecture**: whether a worker consumes convention information, and whether a constructor can produce usable text under the supplied conditions. Its decomposition of construction, consumption and scoring is valuable.

It is not a universal prerequisite for system learning. A contextual action policy, a deterministic learned parser, an executable skill library or a calibrated verifier could improve performance without passing through a natural-language convention note. The production architecture is largely outside the AP-0 path.

The research has diminishing returns if each response to an ambiguous learning claim is another toy control, while the production learning signal remains a syntactic proxy and the system's useful workload stays unspecified. Perfectly establishing that K3 is solvable under an explicit arithmetic schema would resolve an AP-0 question; it would not by itself give FeralEcho an effective learning loop.

I would preserve AP-0's artifacts and findings, use appropriate pieces as regression/component tests when a proposed mechanism needs them, and pause expansion of its acquisition program. The scorer vulnerability still matters wherever that scorer is reused. It does not require making AP-0 repair the next central project.

## 6. Strong alternative research programs within the resource envelope

The available planning evidence is a September 16 hardware record of **24 GiB on the M5**, local 3B–8B-class models, and September 17 environment records containing River, FAISS, PyTorch, scikit-learn, MLX and related tools. AP-0 independently establishes recorded use of local Qwen and DeepSeek. Current hardware capacity and serving configuration were not newly attested here; a direct sysctl read was blocked, so the hardware figure remains an attributed historical observation. I do not assume spare Air capacity, pooled accelerators, paid APIs or unattended frontier assistance. See the [recorded resource inventory](/Users/richietate/Desktop/FeralEcho/audits/2026-09-16_feralecho_zero_cost_capability_ceiling.md:246) and [environment inventory](/Users/richietate/Desktop/FeralEcho/audits/python_learning_capability_gap/environment_inventory.json).

“Zero additional money” still incurs inference time, electricity, contention and maintenance. The following priorities favor small persistent states and bounded local calls. Their proposed gains are hypotheses, not results established by this reassessment.

| Program | What can improve and what carries it | Test against simpler explanations | Feasibility and judgment |
|---|---|---|---|
| **1. Outcome-conditioned strategy selection** | Better choice of direct answer, verification, repair, alternate model or abstention; persistent contextual policy and calibrated outcome/cost estimates | Prospectively novel tasks; fixed best policy, same-budget retry, reset and shuffled-feedback controls; no task-ID features or answer lookup | Small CPU learner plus existing local generators. **Primary next program.** It improves use of existing capabilities; it does not by itself create new solver primitives |
| **2. Verified reusable skills and abstraction** | System proposes functions, contracts and reusable compositions; accepted library and learned search preferences accumulate | Compare raw episodes, retrieved complete solutions and learned abstractions at matched storage/compute; hold out combinations and structures, not just names; remove a learned primitive and restore it | Local code proposals plus deterministic tests. **Best next path toward a stronger capability frontier**, after a trustworthy promotion loop exists |
| **3. Active experiment selection and world-model learning** | Better choice of observations that distinguish hypotheses; persistent model, uncertainty and query-selection policy | Matched random queries and fixed enumerator; declared broad schema; unseen mechanisms within that scope; ambiguity/out-of-space cases; labels and compute to mastery | Cheap in bounded simulators/parsers/state machines. Directly targets learning efficiency, but easy to overclaim a human-supplied hypothesis family |
| **4. Developmental continuity through useful work** | Better task resumption, evidence revision, error recovery and commitment preservation; persistent task/evidence/dependency state | Same-state/no-learning baseline; interrupted runs, stale observations, changed requirements, fewer interventions and repeated mistakes | Mostly ordinary engineering, strongly aligned with practical independence. Continuity alone is not learning; evaluate it separately |
| **5. Learned evaluation and metacognitive control** | Predict own failure, choose informative tests, allocate attempts, abstain appropriately; calibration model and test-selection policy | Independent outcomes, proper scoring/calibration, precision/coverage, new failure families; compare confidence heuristics and fixed verification policies | Small models are feasible. Most useful as part of Program 1; do not let an unqualified learned judge become its own ground truth |
| **6. Targeted local distillation or small adapters** | Internalize a repeatedly useful, verified transformation or repair behavior; learned predictor/adapter weights | Base-plus-retrieval versus trained model, held-out families, matched total budgets, retention/regression tests and contaminated-data controls | Conditional later option. Data quality and actual memory/throughput must qualify it; not the first investment |

### Why Program 2 is a serious alternative to endless prompt-state tests

A learned library can change the effective language in which the system searches. For example, separately acquired routines for validating records, preserving order and merging grouped results might support a new workflow without storing that workflow's complete answer. The scientific object is then the new compositional problem-solving capacity and its cost, not whether its implementation is a text file or executable code.

[DreamCoder](https://arxiv.org/abs/2006.08381) provides a relevant primary example of growing symbolic abstractions together with search guidance. It motivates a mechanism, not a claim that its entire system is cheap or directly applicable here. FeralEcho could investigate a much smaller declared domain using existing interpreters and tests.

A library of copied complete solutions is an essential baseline. If it performs as well as learned abstractions at comparable cost, the claimed abstraction advantage fails. If new tasks require recombinations that no stored answer directly supplies, and particular learned primitives causally enable success, the evidence is stronger than AP-0's convention transcription.

### Where local weight training fits

The official [MLX-LM project](https://github.com/ml-explore/mlx-lm) supports low-rank and full fine-tuning, including quantized models. That makes a small-adapter program technically conceivable; it does not establish that any chosen configuration fits this machine or improves its tasks.

Training on unverified self-produced answers would move the current evaluation problem into weights. Start with a tiny predictor or controller whose labels are independently checkable; only consider an LLM adapter after a useful, repeatable skill and a clean dataset exist. Weight changes are an implementation choice, not a scientific promotion.

### What not to confuse with autonomous curriculum learning

Generating more questions, selecting a weak task label, or maximizing novelty does not establish curriculum learning. A curriculum earns that name here only if its chosen practice yields more later improvement per unit cost than a matched alternative. First use an external, fixed curriculum to make the update mechanism measurable; then test whether FeralEcho can choose better practice. Otherwise curriculum, induction, feedback and transfer fail together and remain uninterpretable.

## 7. Architectural dead ends and mechanisms worth preserving

These judgments concern the current mechanism under its present objective, not a prohibition on repurposing it.

- **Proxy-optimized self-editing is a dead end for demonstrating competence growth.** Syntax, importability and nondecreasing AST-complexity scores cannot make repeated code changes converge on correctness. The current [generated hook](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_generated.py:9) drops lines lacking selected keywords, truncates surviving lines and concatenates fragments. Static inspection shows it can destroy a valid function body. I did not execute it or attribute all historical failures to it. A hook can be causally active and still oppose improvement.
- **Training state with no useful consumer is not a path to system competence.** River's outcome-trained trees and DualLearner's projection illustrate different versions of this risk. Connect a predictor to a justified decision or stop counting its training events as capability progress.
- **Reflection without external correction cannot certify its own progress.** Rephrased self-narratives can still serve conversational purposes; their persistence and volume are not evidence of task learning.
- **Unconditional council synthesis is not a general improvement operator.** More responses and an extra rewriting step can increase cost and lose correct content. Preserve council use where task-specific evidence earns it; do not assume architectural complexity should win.
- **Appending everything to semantic memory is not abstraction formation.** It can increase interference and stale recall. The current [VectorMemory.add path](/Users/richietate/Desktop/FeralEcho/app/lib/vector_memory.py:94) appends vectors while replacing metadata for reused IDs; the existing [duplicate-ID probe](/Users/richietate/Desktop/FeralEcho/audits/recursive_learning_ground_truth/r5_memory.json) records mismatched retrieval after reload. This is a bounded revision defect, not proof all FAISS memory is invalid.
- **Periodic activity is not a resumable goal system.** Current loops and project generation are real; the inspected path does not establish a general transactional task-resumption mechanism. The compatibility functions schedule_task/run_pending are stubs, although other scheduler loops do run.
- **Unlimited self-modification is not a substitute for a learning rule.** It expands the space of harmful or unmeasurable changes faster than it establishes reliable improvement.

I would preserve source/provenance instrumentation, local inference, bounded execution, honest failure records, memory source boundaries and reliable snapshots. They make causal tests and recovery possible. I would stop expanding their complexity unless a concrete failure mode or upcoming decision needs it.

There is an organizational dead end too: repeatedly auditing a missing feedback-to-improvement connection without funding one small controlled implementation of that connection. The September 16–17 investigations already identified much of this problem. Today's source and records strengthen it; another terminology ladder will not close it.

## 8. A better causal skeleton

The proposed sequence—

experience → evaluation → retained change → boundary → novel transfer → measurable improvement → accumulation—

is a useful **evidence checklist**, but incomplete as a model of the learning system. It omits where experience comes from, how credit is assigned, what is updated, which decision consumes it and how regressions are corrected.

I would use:

~~~mermaid
flowchart TD
    A["Useful task distribution and resource limits"] --> B["Current policy chooses an action or information request"]
    B --> C["Attempt with recorded inputs, state and action identity"]
    C --> D["Independent task outcome and observed costs"]
    D --> E["Assign credit; retain uncertainty and counterexamples"]
    E --> F["Update a named policy, model or skill library"]
    F --> G["Check benefit and regression; version accepted state"]
    G --> H["Later task consumes that state"]
    H --> B
    G --> I["Restart / restore checks"]
    I --> H
    H --> J["Blinded comparison with frozen and ablated baselines"]
    J --> K["Accept, revise or abandon the learning mechanism"]
~~~

A separate curriculum policy can later choose tasks or experiments based on measured learning progress. A separate acquisition-policy update can later improve how the system searches or learns. Neither should be silently inferred from the first loop.

A process boundary is one intervention on persistence, not the engine of accumulation. Meaningful continuity is a causal chain from past evidence and commitments to later choices, including correction and forgetting when the environment changes. Exact retention of a bad rule can be the opposite of developmental progress.

## 9. The experiment I would choose if AP-0 had never existed

**One isolated, outcome-conditioned strategy-selection experiment on small Python repair tasks, with the existing local model kept fixed.**

This is the first engineering intervention I would authorize next, not an implementation performed in this assessment. It should be small enough that a negative result ends the branch rather than triggering an automatic apparatus expansion.

1. **Choose a useful workload and freeze its success criterion.** Use bounded pure-function repairs or data transformations representative of work FeralEcho actually needs. Keep expected answers outside candidate memory and expose only authorized training feedback. Old Tier-4/AP-0 tasks are development material; their now-known results cannot serve as fresh confirmation.
2. **Make actual actions and costs explicit.** Start with a few fixed strategies: direct generation, one verified repair attempt, and a fixed alternate approach if budget permits. Bind each response and outcome to the strategy/model/options that actually produced it. Count every attempt, including errors, empty generations and abstentions.
3. **Use a small learner, not a self-editing language model.** Fit a contextual strategy/value predictor from verified outcomes using existing CPU tooling. Permit features available before the action, not task IDs, test answers or future execution results. The controller can use an observed failure only at a later decision where that observation is genuinely available.
4. **Compare against strong cheap controls.** The best frozen strategy chosen on development tasks, a fixed same-budget retry policy, history/retrieval without policy adaptation, reset learning state, and permuted-feedback learning. Equalize available inference budgets and report actual expenditure. A human-written routing rule is also a legitimate competitor.
5. **Evaluate sequentially, then across boundaries.** Predict/choose before revealing each outcome; use it for subsequent updates only. Test later untouched tasks and restart checkpoints. Include a changed-condition segment to expose stale policies and a retention panel to detect loss of earlier gains. River's [progressive-validation documentation](https://riverml.xyz/latest/api/overview/) describes the basic predict-before-update evaluation pattern; the FeralEcho action-selection test still requires its own task and cost contract.
6. **Precommit the decision, including stopping.** Require a practically useful improvement over the best frozen comparator with uncertainty accounted for at the independent task/history level. If benefits vanish under matched compute, feedback does not change consequential choices, or a simple fixed policy matches the result, stop claiming an adaptive advantage. If all strategies fail, investigate generation/representation or reduce the domain; routing cannot solve missing candidate capability.

The existing corpus is enough to motivate this test, not to prove it will work. Retrospective oracle selection is a diagnostic upper bound only. Offline learning from logs with incomplete action coverage needs explicit support assumptions; it cannot manufacture outcomes for untried strategies.

**What success would mean:** retained experience improves FeralEcho's effective policy for using existing capabilities. That is real but bounded system learning. It does not yet mean that the learner becomes a better learner.

**Next escalation only after that success:** use the same trustworthy outcome-to-state-to-action connection to promote reusable skills or learned abstractions. Then assess whether accumulated abstractions lower acquisition cost on prospectively new but related problems. Reduced sample complexity is valuable at that stage, provided accuracy, compute, access to feedback and task difficulty are controlled.

This ordering avoids two errors: demanding open-ended meta-learning before establishing an effective feedback loop, and indefinitely celebrating better routing as if it were open-ended capability creation.

## 10. What would change my mind?

| Competing explanation | Current status | Observation that would discriminate |
|---|---|---|
| FeralEcho mainly needs stronger base models | Plausible for some tasks; not sufficient to explain signal/consumer defects | Under qualified evaluation, a stronger local worker helps while policy/library changes do not; compare within real resource limits |
| Fixed engineering is enough | Entirely plausible and potentially the best practical outcome | A frozen simple policy matches or beats adaptive versions prospectively; then keep it |
| Better feedback can unlock current architecture | Leading near-term hypothesis | True outcomes improve consequential selection on new work; shuffled outcomes/reset state remove the benefit |
| A reusable library can grow effective capability | Plausible, currently unestablished | New compositions become solvable or cheaper; learned-component ablation removes the gain; full-solution retrieval does not explain it |
| Prior experience improves acquisition itself | Stronger hypothesis, untested | Less evidence or search is needed on later novel structures after controlling ordinary skill reuse and resource changes |
| Current architecture cannot support the ambition at all | Too strong for present evidence | Repeated well-powered failures across bounded, qualified mechanisms and sufficient candidate capacity would lower confidence; present proxy-driven failures do not establish impossibility |
| Human/frontier intervention is the real learner | Serious unresolved alternative | Freeze external assistance during measurement, record every intervention, and isolate which retained changes FeralEcho produced and validated itself |

The project should not require a specific impressive interpretation to count as success. Discovering that a small fixed workflow reliably does useful work may be the best engineering result, even if it rejects the current learning hypothesis. Conversely, a simple learned controller should not be dismissed because it is less evocative than an autonomous self-editing council.

## 11. Decision among the proposed options

**Choose B.**

- **A is not my choice:** AP-0 repair and continuation would answer a narrower question than the project's current bottleneck.
- **B preserves useful instrumentation without letting a toy acquisition program govern the research agenda.** Make verified task improvement through a consequential learned state the primary program.
- **C may become warranted for the acquisition/library subsystem**, but a wholesale redesign before testing the existing useful primitives would add another large unvalidated architecture. B does not prohibit replacing a failed mechanism.
- **D is not supported:** the architecture already has local generators, persistence, bounded execution and small adaptive models. They can support scientifically meaningful bounded learning. Nothing here establishes open-ended autonomous self-improvement, but its absence is not proof that all useful accumulation requires unavailable resources.
- **E is unnecessary:** B with explicit stopping rules is a sufficiently clear commitment.

The broader mountain is worthwhile: a local system that uses its history to do useful work better, with fewer interventions. The wrong summit would be a perfectly defended vocabulary claim about retained text while the operational system continues to optimize weak proxies.

## Integrity and exact artifact

Opening HEAD: **2fba42644c82b9f7096276f4dd338d615cf1bcce**. The working tree was already dirty. A 94-file fingerprint taken at 2026-09-22T17:28:37.631893+00:00 covered core/learning source, selected historical learning artifacts, run.py, scheduler/night-cycle source and the prior AP-0 report. This was a scoped mid-inspection integrity snapshot, not a full transactional snapshot of the host.

Final verification at **2026-09-22T17:37:50.126104+00:00** found the same HEAD and unchanged contents/sizes for all **94 fingerprinted files**, including the prior AP-0 report. Git status retained the same 27 modified tracked paths; untracked paths increased from 263 to 264 solely through this assessment. No previous status entry disappeared. All local source links resolved, and the final two sections match the requested headings. Recording this verification changes only this assessment.

Only this file was created:

~~~text
audits/2026-09-22_feralecho_research_direction_reassessment.md
~~~

No production changes, new experiment data, model calls or AP-0 modifications were made. External reading was limited to primary research papers and official documentation cited above; no repository content was sent in those searches.

## IF THIS WERE MY PROJECT

I would pause AP-0 expansion and authorize one isolated, bounded test of **whether verified task outcomes improve a small strategy-selection policy over the best frozen policy on fresh Python repair work**. I would preserve a direct-model baseline and a hard resource budget, then stop the adaptive branch if it cannot earn its complexity. This tests the most consequential missing connection using resources already available, before attempting autonomous abstraction or modification of the learner.

## THE QUESTION WE SHOULD BE ASKING

**What can FeralEcho do reliably tomorrow, at the same resource budget and with less human help, because of an independently verified consequence of what it did today?**
