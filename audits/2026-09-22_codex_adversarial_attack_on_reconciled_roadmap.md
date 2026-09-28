# Codex adversarial attack on the reconciled roadmap — 2026-09-22

**Opening Git HEAD:** 2fba42644c82b9f7096276f4dd338d615cf1bcce.

**Opening working-tree status, 2026-09-22T18:15:33.068092+00:00:** main, 17 commits ahead of origin/main, none behind; 27 tracked files modified, no staged changes, 266 untracked files. The requested output did not exist. This review evaluates the working tree, not an assumption that HEAD contains all inspected source.

**SHA-256 of the three immutable source reports:**

| Source report | SHA-256 |
|---|---|
| [Independent Codex reassessment](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_feralecho_research_direction_reassessment.md) | 7b5d2d6acd24b2ad13f48010589fa14700979e4bb238c7cd333d89af493808c7 |
| [Independent Claude reassessment](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_claude_feralecho_research_direction_reassessment.md) | 41e74987f04e998550eb382119163d7571a51485eb21d2aff57d91341035258c |
| [Reconciliation and October 1 roadmap](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_claude_codex_reconciliation_and_oct1_roadmap.md) | afd8c292c090ac18cab634e2dbd0132243c1dbfc6feab41ff822416b04fd526d |

**Preservation confirmation:** all three reports were read and not modified by this review. Closing hash verification is recorded below. No production imports, model calls, sandbox executions, verification-script executions, training, service operations, or experiments were performed. Read-only source inspection and aggregation of existing JSON records supplied the evidence. Only this report was written.

**Concurrent-change qualification:** the repository changed externally during this review. Before this report was created, tracked modifications increased to 28 and untracked paths to 273. Candidate-logging changes appeared in self_edit_manager.py and self_edit_attempt_ledger.py, with seven new untracked paths. I neither implemented nor reverted them. I rechecked the affected attribution and historical-evidence paths against the updated source. Their substantive findings below survive. A whole-tree “unchanged throughout” claim would be false.

## Executive decision

**B — AUTHORIZE ONLY AFTER SPECIFIED DESIGN CHANGES. Implementation is not authorized now.**

The proposed research question remains answerable at the level of a bounded routing policy. The reconciled implementation order and its central code justification do not survive.

1. **Claim A is PARTIALLY CONFIRMED.** Sandbox feedback does not directly update the ranking mean. Council feedback explicitly does. Successful sandbox records also have an indirect route through the council rater. The reconciliation's supposed confirmation of two disconnected verified-feedback paths is incorrect.
2. **Claim B is CONFIRMED.** The self-edit path selects a name for tracking, invokes a separately routed generation, and credits the former. Returning a name alongside text does not repair that mismatch.
3. **F2 success is not task correctness.** Its inspected path checks parsing/importability and a hook smoke invocation. A kernel sandbox makes execution constrained; it does not make the result a functional ground-truth label.
4. **The comparator changes meaning within the roadmap.** “Best frozen policy” becomes a single fixed strategy in Part IX. A contextual policy can beat that constant choice without demonstrating an advantage over an ordinary fixed contextual router.
5. **A learned task-signature table survives the proposed reset, shuffle, and restart controls.** That can be narrow parameter learning, but it cannot establish abstraction, stronger acquisition competence, or development beyond routing among pretrained capabilities.
6. **Repairing production first is unnecessary and makes attribution harder.** The isolated harness should contain the experimental feedback-to-selection loop. Production repair needs its own later justification and review.
7. **The succession package should start immediately.** The historical-rule test is neither a prerequisite for this experiment nor a source of trustworthy retrospective actor attribution.

These are implementation-blocking defects in the current proposal, not evidence that every outcome-conditioned controller is futile. My own earlier recommendation is subject to the same burden: if a cheap fixed router matches it, the adaptive branch has not earned its complexity.

## 1. Claim A: exact writers, consumers, and the missed indirect route

The relevant current source is [RiverBrain](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:758), especially lines 808–1029. The orchestrator's opening and closing fingerprint is included in the integrity scope; its relevant source did not change during inspection.

| Entry point | State actually written | Consequence for selection |
|---|---|---|
| learn(model, task, response), lines 808–868 | Classifier/scaler; observation_counts; model_task_stats count and mean, using a response heuristic divided by four | Directly reaches score_model |
| learn_from_sandbox_outcome, lines 870–896 | Coding classifier/scaler; sandbox_observation_counts; successful outcomes additionally enter interaction_log | No direct model_task_stats update; success-only indirect route described below |
| learn_from_rating, lines 898–918 | Classifier/scaler; observation_counts increased by three | No direct mean update, but counts can affect the global influence weight; this is the user-rating method, not the council method |
| learn_from_council_rating, lines 936–984 | Classifier/scaler; observation_counts; model_task_stats count, mean, and council_vetted_count | Directly reaches score_model and observation-based council eligibility |

**The decisive contradiction is at lines 958–963:** the council method obtains the model/task statistics, increments count, and updates mean toward the blended score. The update denominator is min(count, 200). The blend is 0.3 × council_rating/5 + 0.7 × quality_score/4 when quality_score is numeric; otherwise it uses council_rating/5. This is an additional observation, not replacement of the earlier heuristic observation.

**Consumers:**

- score_model, lines 995–1010, returns that mean after five observations; otherwise 0.5.
- rank_models, lines 1153–1196, mixes it with legacy reflection scores using influence_weight.
- choose_model, lines 1212–1237, uses the ranking and score-derived entropy for exploration.
- [_select_council](/Users/richietate/Desktop/FeralEcho/app/core/river_deliberation.py:533) consumes score_model directly at line 589, applies model/tag boosts, and uses the statistics' count to prioritize undersampled models.
- influence_weight uses ordinary observation_counts. Council updates therefore have an additional route into the mixture weight; sandbox_observation_counts do not enter that formula.

The inspected production source contains no decision consumer of the outcome-trained River classifiers' predictions: their prediction call in learn is for tracking accuracy. A future fix cannot simply assume a classifier trained on response features already supplies a pre-generation contextual action value.

### The indirect sandbox route exists

The success branch logs model, task_type=coding, prompt=[SANDBOX], the first 200 code characters, quality_score=1, and sandbox_outcome=success. [log_interaction](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:206) puts these into the interaction log.

[Council polling](/Users/richietate/Desktop/FeralEcho/app/core/council_rater.py:574) admits entries with an eligible model and a nonempty response preview, selecting every fifth eligible entry within a poll batch. It does not exclude sandbox_feedback. [rate_one_entry](/Users/richietate/Desktop/FeralEcho/app/core/council_rater.py:222) rates that preview and, when is_council_trusted is true, calls learn_from_council_rating at lines 297–303. Consequently:

**sandbox success → interaction record → sampled peer rating → blended ranking mean → later selection.**

This is conditional on logging, sampling, a usable peer response, the trust gate, and successful training. It is neither a direct binary-outcome update nor a complete success/failure channel.

A read-only join of the retained files found:

| Existing record aggregation | Count |
|---|---:|
| interaction_log rows | 5,033 |
| sandbox-feedback rows | 407 |
| These rows labeled success | 407 |
| council_ratings rows | 203 |
| Council records joined to sandbox-feedback timestamps | 6 |
| Joined records with a non-skipped rating | 6 |
| Duplicate sandbox timestamps in this join | 0 |

All six joined records carry quality_score=1; their council timestamps range from September 17 to September 20. snapshot_baseline records council trust since July 22. This substantiates actual traversal through peer rating in retained history. It does **not** prove each subsequent in-memory update succeeded or changed a particular live selection; that would require the corresponding state/decision evidence.

There is also a scale mismatch: success=1 is logged into a field the blend interprets on a 0–4 scale. Such a record contributes 0.175 + 0.3 × council_rating/5, between 0.235 and 0.475. Even the highest peer rating produces a blended value below the neutral 0.5. The indirect route is therefore real but not a sound substitute for functional success learning. Failure feedback lacks this logging route.

**Claim A verdict: PARTIALLY CONFIRMED.** The direct sandbox gap survives; the council-disconnection subclaim is **FALSIFIED**, and the universal “no indirect path” claim is false. Adding a missing council wire is not a justified repair. Calling both signals “independently verified outcomes” also needs correction: peer judgment is not independent task ground truth.

The independent Codex report distinguished sandbox and explicit user ratings. It did not assert that the council method lacked a mean update. The reconciliation introduced that stronger assertion and then incorrectly attributed agreement to both reviewers.

## 2. Claim B: the selected name is not the generating actor

The relevant flow in [generate_code_from_plan](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_manager.py:1797) is unambiguous:

1. It builds a prompt including the current self-edit file and plan.
2. At line 1834 it calls choose_model with task_type=self_edit_coding.
3. At line 1835 it calls echo_query with task_type=coding, without passing the selected name.
4. It strips/extracts code, invokes the current apply_to_code transformation, heuristically credits the originally selected name, and returns code plus that name.
5. The caller performs additional cleanup and gates before F2 evaluation; sandbox feedback is credited to the returned name. In the closing source these calls are at lines 2087/2089.
6. The retry repeats the mismatch at lines 2108–2109 and credits its independently selected retry name.

[echo_query](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:1367) has no model-binding argument in this signature. Its normal path invokes deliberate_and_learn with the entire model pool and returns a string. Its fallback calls choose_model again, now in the coding bucket. Coincidental equality of names is possible; equality is not guaranteed.

The [deliberation implementation](/Users/richietate/Desktop/FeralEcho/app/core/river_deliberation.py:1086) can return:

- A directly generated synthesis-model response.
- A council-derived synthesis.
- An agreed candidate without a synthesis generation.
- A fallback candidate after failed or incomplete synthesis.

For coding, the agreement shortcut returns a candidate while crediting the synthesis-model bucket. Error/completeness fallbacks likewise can credit synth_model for another candidate's returned text. echo_query then credits ECHO_SYNTHESIS_MODEL again. Thus the reconciliation's additional assurance that ordinary learn calls elsewhere always name the actual producer is also too broad.

At the backend boundary, [_ollama_query](/Users/richietate/Desktop/FeralEcho/app/core/river_deliberation.py:397) assembles streamed text, consults done_reason, and returns only text; its subprocess fallback is another route. [stream_query_ollama](/Users/richietate/Desktop/FeralEcho/app/ollama_handler.py:421) can route to MLX or Ollama. Its chat metadata output retains done_reason, not a complete artifact-bound actual-model identity. None of that lineage is returned to generate_code_from_plan.

The evaluated artifact can additionally reflect the persisted apply_to_code hook and later deterministic cleanup. A correct claim about the final code must include those producers/transforms, not just the LLM.

**Claim B verdict: CONFIRMED.** This establishes a source-level absence of guaranteed attribution, not a measured historical misattribution rate. The concurrent candidate-preservation additions do not bind the selected model or add that missing return lineage.

A second boundary matters for any later repair: sandbox feedback hardcodes the coding bucket, while the outer tracking selection uses self_edit_coding. Adding a mean write without deciding the intended task/strategy identity could train the wrong bucket even after fixing the actor name.

## 3. Attack on verified_mean

A scalar mean is not inherently invalid. For a fixed action evaluated under a defined task distribution and consistent binary success contract, it estimates a useful average. The proposed production field does not establish those conditions.

| Attack | Why the proposed field does not solve it |
|---|---|
| Different meanings of “pass” | F2 import/smoke success, held-out functional correctness, deployment, and peer approval are distinct outcomes. Combining them destroys interpretability |
| Task difficulty and selection | Each model sees tasks chosen by the current policy. Its observed success mean is not success on a common target distribution |
| Specialization | One broad coding mean can suppress a model useful on a small class. A second broad mean preserves the same limitation |
| Sparse data and lock-in | Five observations is an existing engineering threshold, not an adequate confidence criterion. Early failures can remove the observations needed to recover |
| Exploration amplifies noise | Choosing actions from noisy scores changes the future data distribution. Score entropy is not uncertainty about each action's success probability |
| Feedback sources | Council ratings are judgments on truncated text, often of responses already heuristically scored. They must not share a “verified” Bernoulli statistic with independent tests |
| Duplicate credit | Initial attempts, retries, peer re-ratings, and synthesis-layer updates can count one task several times. Count is then neither independent sample size nor task count |
| Proxy fallback | Switching between heuristic mean and verified_mean at a count threshold can create a discontinuity unrelated to improved competence |
| Nonstationarity | A cumulative mean can become stale; an EMA can forget past specialization. Neither choice removes the need for a specified task distribution and evaluation |
| Hidden filtering | Passing only F2-eligible candidates or logging only successes changes the denominator. Empty generations, parsing failures, timeouts, and rejected candidates are still policy outcomes |

A hypothetical difficulty reversal illustrates the problem without any new experiment: suppose A succeeds on 90% of easy and 60% of hard tasks, while B succeeds on 80% and 50%. A is better in both strata. If A receives 10% easy tasks and B receives 90%, their observed averages are 63% and 77%. A production mean ranks the inferior model higher because it ranks assignment histories.

FeralEcho already has mean/count persistence, capped updates, cold-start handling, council statistics, and small online classifiers. These are reusable mechanics, not a qualified causal estimator. The response-feature classifiers are especially unsuitable as drop-in pre-action predictors because features extracted from an answer do not exist when choosing who should produce it.

**Minimum safe production repair before this experiment: none.** Do not add verified_mean to live RiverBrain for this study, and do not count council feedback as independent correctness. In an isolated harness, the minimum necessary contract is one fully specified strategy invocation, its actual artifact lineage, a functional outcome and measured cost, and one controlled update to experiment-owned policy state. Failures must remain in the accounting. Any scalar used there needs counts/support and a disclosed context/assignment scheme.

**F2 cannot supply the proposed label by itself.** [test_code_in_sandbox](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_manager.py:1370) parses and imports the candidate; the [wrapper](/Users/richietate/Desktop/FeralEcho/sandbox/safe_exec_wrapper.py:629) invokes apply_to_code on one probe but does not check its returned transformation against a task answer. A pure wrong function can pass. This is static reasoning, not an executed attack. Reuse of a sandbox boundary is permissible; reuse of “SANDBOX_OK” as functional correctness is not.

## 4. Can the experiment be passed without the claimed acquisition?

Yes, if the claim exceeds experience-dependent routing.

Consider a fixed procedure that extracts a few superficial prompt features, maintains successes/attempts for each feature bucket and strategy, and picks the best bucket entry. Persist the table. It never changes its features, generates a new solution primitive, or improves its acquisition algorithm. On tasks whose optimal strategies align with those buckets, it beats every single constant strategy, loses under reset or misleading feedback, and survives a process restart. Different task IDs and a later timestamp do not defeat it.

Under a reasonable broad definition, the fitted table is a learned routing policy. Under the project's stronger target it is the same fixed acquisition mechanism accumulating task-specific configuration. The experiment must name which claim it is testing rather than attempting to make “lookup” an automatic disqualification.

A fully prewritten router whose decisions never depend on feedback should **not** beat correctly constructed state-reset and feedback-content controls causally. If it appears to, the controls, information budget, task assignment, or analysis have failed. An experience-fitted lookup, however, survives them legitimately.

### Adversarial verdicts

“KILLS THE EXPERIMENT” below means fatal to the proposed causal interpretation if the route remains open; it does not mean this route has been observed in a future experiment.

| Doppelgänger or alternative | Current verdict | What is missing or bounded |
|---|---|---|
| Superficial task-type lookup learned from outcomes | **NARROWS THE CLAIM** | Reset/shuffle/restart do not distinguish it from a richer learner. Report bounded routing; no abstraction or acquisition improvement |
| Prewritten contextual router versus a weak constant baseline | **KILLS THE EXPERIMENT** for an advantage-over-fixed-policy claim | Include a prespecified, development-selected fixed contextual comparator with the same permissible features; “best fixed strategy” is insufficient |
| Hidden family label, filename, template, or ordering encodes the preferred strategy | **KILLS THE EXPERIMENT** | Ban explicit IDs and audit semantic/structural proxies; split independent task-generating structures where structural transfer is claimed |
| Strongest pretrained strategy selected more often | **NARROWS THE CLAIM** | May be useful routing; compare always-strongest and fixed contextual routing. It is not evidence the solver acquired a capability |
| More tokens, planning, synthesis, or hidden retry calls | **KILLS THE EXPERIMENT** | A top-level call is not an inference unit. Meter all backend calls, input/output/thinking tokens, retries, and warm-ups; disclose model-dependent costs |
| Repair arm gets current test failures unavailable to competitors | **KILLS THE EXPERIMENT** if credited to cross-task learning | Make within-task feedback an explicit resource available under comparator policies too; keep final scoring tests hidden |
| Strategies differ in built-in capability | **NARROWS THE CLAIM** when fixed and shared across arms | Strategy differences are legitimate actions, but their availability cannot be exclusive to the adaptive policy or changed during evaluation |
| Baselines run earlier, adaptation later, with changing load/software | **KILLS THE EXPERIMENT** | The roadmap's separate-day collection is vulnerable. Pair/interleave conditions under a fixed manifest; freeze updates on final evaluation |
| Warm model, prefix/KV cache, conversation context, or response cache | **KILLS THE EXPERIMENT** if uncontrolled | Same stateless request contract and counterbalanced execution; no outcome/answer cache crossing arms. Warm weights can affect latency without constituting learning |
| Easy tasks assigned preferentially to one policy | **KILLS THE EXPERIMENT** | Compare the same independent evaluation tasks or randomized balanced assignments; include unsolved and unattempted tasks in the declared budget endpoint |
| Adaptive arm receives extra history, oracle information, or development tuning | **KILLS THE EXPERIMENT** | Equal feature/test access and disclosed training budgets. Frozen contextual policies get the same development opportunity; ablations differ only in the designated learning state/feedback |
| Selected-action success rate presented as overall policy value | **KILLS THE EXPERIMENT** | Score all assigned tasks. Do not infer values for untried actions from selective logs without support and an appropriate estimator |
| Regression to the mean after choosing a “weak” initial window | **KILLS THE EXPERIMENT** for a before/after inference | Concurrent matched controls and prespecified splits; improvement over a selected bad run is not the endpoint |
| Tiny samples, many subgroups/seeds, optional stopping | **KILLS THE EXPERIMENT** for a decisive positive claim | One primary contrast, independent task-family/history units, multiplicity handling, prospective power/MDE and fixed stopping |
| AP-0/Tier/Architecture A answers or historical results reused | **KILLS THE EXPERIMENT** as prospective confirmation | Treat known material as development. Novel IDs or paraphrases are insufficient; track generator/template/solution ancestry |
| Candidate reads the oracle, modifies tests, or self-reports pass | **KILLS THE EXPERIMENT** | Independent functional evaluation with expected answers outside candidate memory/files; trusted result aggregation; qualify against wrong-but-runnable artifacts |
| Restart merely reloads a lookup table | **NARROWS THE CLAIM** | It establishes persistence of that table only. Retained-state intervention must remove and restore the later effect |
| Fixed retry procedure already solves the failures | **NARROWS THE CLAIM**, or eliminates the adaptive advantage | The named retry control is appropriate, but it must match actual feedback access and resources. Architecture A supplies relevant negative evidence |
| Current production history already enters prompts | **KILLS THE EXPERIMENT** if only the new policy state is reset | Bypass or identically freeze all historical prompt inputs. Resetting one table does not remove existing experience |
| Researcher selects task families, features, strategies, or stopping after seeing outcomes | **KILLS THE EXPERIMENT** | Freeze those choices before confirmation; record all outside intervention. The human must not become an unreported adaptive controller |

Some named controls are appropriate **in principle**, but none is “adequately controlled” merely by being listed in a roadmap. A genuine isolated restart controls loss of the worker process context; it does not control external files, backend caches, history-driven prompts, or what the persisted state represents.

### The minimum statistical and causal commitments

The independent unit must match the inference. Tasks sampled from independent structures support a bounded workload comparison; several paraphrases, seeds, or repeated retries of one problem do not become independent transfer examples. One training history supports conclusions about that fitted policy conditional on its history. A claim about the learning procedure's reliability needs replicated independent training histories.

Predeclare the practically important improvement and a task-family/history-aware uncertainty calculation. No honest sample count can be selected here because the workload, effect size, dependence, and total resource budget remain unspecified. A deadline-sized pilot may be informative but inconclusive. A nonsignificant difference is not equivalence; a confidence interval excluding the prespecified useful improvement is a stronger negative finding.

Keep two quantities separate: cumulative performance including learning/exploration cost, and post-restart performance of a frozen checkpoint on untouched tasks. The latter shows retained policy value; it does not retroactively pay for acquisition.

Reset and shuffle must be explicit interventions, not labels. Reset must remove every experiment-owned learned state while retaining the same nonlearning machinery. The feedback null must break the association the learner is hypothesized to use without leaking future outcomes, changing the feedback schedule, or merely preserving each context/action mean through an ineffective permutation. If shuffled policies select different actions, their later histories legitimately diverge; compare complete assigned-task outcomes rather than pretending their selected-action data are paired counterfactuals.

A fully observed, balanced training panel can simplify that initial identification; it cannot be advertised as online exploration learning if the policy did not acquire the observations itself. This is an optional simplification, not a second required experiment.

## 5. Repair production first?

| Option | Causal consequence | Judgment |
|---|---|---|
| A. Repair production first | Changes attribution, statistics, routing, and subsequent history before the reference system is frozen; introduces concurrency and hidden consumers | Reject as prerequisite |
| B. Put the feedback/selection loop in an isolated harness | Separates a single proposed mechanism from live state and allows exact reset/checkpoint interventions | **Choose B** |
| C. Start with an offline outcome panel or shadow policy | Can qualify selection/provenance cheaply when outcomes cover the relevant actions; incomplete historical logs cannot supply missing counterfactuals | Optional qualification, not evidence of live deployment benefit |

Editing code is reversible; undoing outcomes already learned by live processes or artifacts generated under altered routing is not accomplished by reverting a diff. Production-first does not inevitably make causal inference impossible, but it purchases extra confounds without answering the narrow question.

The roadmap itself is inconsistent: Part VIII makes live RiverBrain and self-edit repairs Day 1 gates, while Part IX says the experimental policy never modifies RiverBrain's existing state or production routing. The latter boundary is the scientifically cleaner one.

Isolation must include imports and side effects. RiverBrain starts a writer thread, production query paths learn/log/save, and echo_query can trigger additional machinery. Reusing a function name without excluding those effects is not isolation. The minimum harness should own its policy state, fixed strategy definitions, generator interface, and evaluator artifacts. This is a design requirement for later authorized work, not code written here.

Claim B remains a legitimate production defect to consider separately. Its presence does not force the experiment to inherit that path or fix it first. The false council half of Claim A supplies no repair justification at all.

## 6. Actor provenance and influence provenance

**Artifact provenance asks what was actually produced, by what execution path, and what exact bytes were evaluated. Influence provenance asks which earlier evidence reached this decision and whether its content caused a later change. One does not establish the other.**

Minimum evidence for crediting an outcome to a strategy/model:

1. An immutable strategy definition/version, invocation ID, task and input hashes, policy checkpoint, selected action, and selection probability where exploration is used.
2. At the actual generation boundary, the dispatched request plus backend-reported serving identity tied to the loaded model artifact/version, tokenizer/template/options, and model-content digest or manifest. A mutable alias, requested name, or caller-generated label alone is insufficient. For a local backend the trust boundary includes the server/process and resolved loaded artifact; a digest recorded elsewhere does not independently prove which weights served this response.
3. Full returned artifact bytes and hash, completion status/termination reason, measured cost, and explicit fallback/retry records. Preserve failures and empty responses. If multiple backend calls contribute, retain their parent/child lineage.
4. Hash-linked transformations from raw generation to the submitted candidate, including extraction, cleanup, repair, retained hooks, selection, and synthesis. The evaluator record must identify the exact final hash, test version, isolated run, and trusted outcome.
5. Exactly one defined policy reward per task/strategy attempt, with component observations labeled separately rather than silently counted as independent successes.

For council synthesis, credit the **composite strategy**. The final writer can be named as a provenance fact, but task success does not estimate that model's independent contribution. Agreement shortcuts and fallbacks must name the actual selected candidate. Attribution of marginal credit to individual contributors requires additional interventions; it is unnecessary for the proposed strategy-level experiment.

For influence provenance, record the actual prior-record IDs/versions selected, exact prompt/feature material supplied, and policy state read before the action. This establishes availability and consultation. Then intervene on that historical content/state to establish caused behavior and independently score whether the change helped. A prompt log alone does not show that the model used the information internally or benefited from it.

The updated [_attempt_ledger_evidence_section](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_manager.py:2843) reads initial_f2_error, truncates it to 400 characters, and adds it to later targeted prompts. The reader returns a whole matching row, but this consumer extracts the named error field. Preserved candidate-source fields must remain excluded. Their appearance in a row does not authorize retrieval, and this review does not propose such a consumer.

## 7. Claims ladder under attack

The ladder must separate existence, causal influence, utility, and generality.

| Proposed level | Defensible present status after attack |
|---|---|
| Persistent state: MET | **MET for particular recorded states and components**, not universal reliable continuity. Existing producer/consumer records and source support persistence; no production restart was rerun here |
| Behavioral consequence: PARTIALLY MET | **PARTIALLY MET.** Statistics are read by selectors and historical error text enters prompts. These establish mechanisms and some component consequences, not verified improvement. The council path cannot be excluded on the reconciliation's stated ground |
| Experience-dependent adaptation: NOT MET anywhere | **Too absolute.** Existing authored-worker component records contrast verified and reversed feedback, with different choices/results. Production benefit on novel useful work remains **NOT ESTABLISHED** |
| Bounded system learning: NOT MET | **NOT ESTABLISHED for the proposed real-model workload.** Toy outcome-to-selection demonstrations are narrower evidence; the new experiment must add real task value |
| Reusable abstraction accumulation: NOT MET | **NOT ESTABLISHED.** Neither routing statistics nor preserved candidate source establish reusable abstractions |
| Accumulated competence: NOT MET | **NOT ESTABLISHED.** One successful routing experiment would not establish repeated retained improvement across episodes |
| Improved acquisition competence: NOT MET | **UNTESTED/NOT ESTABLISHED.** No result from a fixed strategy chooser alone changes its acquisition algorithm or establishes lower acquisition cost on new structural families |
| Developmental continuity: PARTIALLY MET at best | **PARTIALLY SUPPORTED for persistence infrastructure; coherent goal/evidence revision across interruption remains NOT ESTABLISHED.** A restart is not that test |

The [existing component results](/Users/richietate/Desktop/FeralEcho/audits/recursive_learning_ground_truth/r1_r3_results.json) explicitly identify their scope as authored fixed workers, not Echo inference. Verified-feedback and reversed-feedback arms select different workers and obtain 24/24 versus 0/24 in that fixture. [Separate producer/consumer records](/Users/richietate/Desktop/FeralEcho/audits/recursive_learning_ground_truth/r4_consumer.json) document distinct PIDs. This refutes “no content-of-feedback contrast anywhere,” without establishing real local-model learning. Some sandbox-only fixture successes depend on the unchanged selection/tie setup; they do not close the direct sandbox-to-mean gap.

### Required distinctions for any future learning claim

| Observation | What it would establish, and what it would not |
|---|---|
| Repeated behavior | Recurrence; not adaptation |
| Recurrence recognition | Detection of similarity or an error signature; not repair or transfer |
| Static lookup/blacklist behavior | Execution of a stored association; experience-derived fitting must be shown separately |
| Within-context adaptation | A response changes with current feedback; no persistent cross-episode claim follows |
| Model-native capability | A pretrained solver can already perform the operation; later routing may expose this capability |
| Experience availability | A usable record exists; no evidence it was read |
| Experience consultation | The record enters a prompt/feature/state read; no proof it caused the answer |
| Experience-caused behavioral change | A controlled historical-content intervention changes behavior; the change may be harmful |
| Persistent retained change | The causally relevant state and effect survive the boundary; it may still be lookup |
| Transfer to related, non-identical tasks | Help on a specified new structure/composition, with duplicates and answer replay excluded; not general learning-to-learn |
| Independently measured competence improvement | Better verified outcomes under matched opportunity/cost; not established by self-ratings or syntax |
| Repeated accumulation across episodes | Multiple retained gains with earlier capabilities checked; not one fitted table or one favorable batch |

**Could “a narrow and bounded instance of system-level learning” ever be justified?** Yes, if a retained policy fitted from outcomes causally improves independently verified future task performance, and the claim explicitly names routing. Fixed model weights and a simple update rule do not disqualify this.

**Does the current roadmap guarantee that interpretation from a positive result? No.** A win against one constant strategy can be explained by ordinary contextual routing; a win with extra feedback or compute does not isolate retained learning. At present the strongest descriptive wording would be that the tested condition outperformed the specified constant comparator on this task sample. Causal learning language requires the missing controls to qualify.

Even after those changes, say “experience-dependent improvement in a bounded strategy-selection policy.” Do not turn that into “FeralEcho learns to learn,” “new solver competence,” or “persistent accumulated competence.”

## 8. Model capability and negative evidence

The AP-0 evidence makes candidate sufficiency a real concern. The completed audit found K2 constructor failures despite the declared ordering schema being informative, and K2 GOLD gate acceptance of only 2/4. Routing cannot choose a correct solution when all available strategies fail.

The reconciliation overstates a different result: K3 identifiability was conditional on an operation family supplied to the diagnostic but not to QA/QB. Five of six QB K3 generations were empty and length-terminated. The claim that both K2 and K3 cleanly establish a universal 7B induction ceiling is not supported. No new AP-0 work was needed to resolve this discrepancy; it is explicit in the preserved [forensic report](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_codex_ap0_independent_forensic_audit.md).

“Send hard-looking tasks to the strongest pretrained strategy” is a surviving explanation. It is:

- Foundation-model capability if the improvement comes from changing the worker itself.
- Static routing if a fixed feature rule achieves it without task-outcome updates.
- Experience-dependent routing improvement if matched outcome histories update the selector and those updates add later value beyond the specified fixed rules.

The cleanest minimal control is to keep the backend model/digest fixed across conditions and compare fixed direct/repair/alternate strategies, as my independent reassessment originally proposed. If multiple models are necessary, include the best always-one-model policy and a fixed contextual router over the identical model menu, with model-dependent resource accounting. Do not replace the 7B models merely to rescue a weak effect. If existing strategies lack sufficient independently verified successes or meaningful differences on development work, report that the routing opportunity is inadequate.

### Architecture A: a real null, with limits

I recounted [trial_results.jsonl](/Users/richietate/Desktop/FeralEcho/app/experiments/architecture_a_hot_stove_proof/trial_results.jsonl): **control 5/6, experience 5/6**. These are six paired repetitions of **one mined starting problem/error**, not six independent transfer tasks. Execution order alternated. Both retry prompts already contained the current NameError; the added historical “hypothesis” repeated that same missing-functools diagnosis. This is strong evidence against claiming benefit from that particular redundant prompt addition, not an equivalence demonstration for all experience use.

The [harness](/Users/richietate/Desktop/FeralEcho/app/experiments/architecture_a_hot_stove_proof/harness.py:179) also uses choose_model for a recorded retry name followed by separately routed echo_query, reproducing Claim B's attribution limitation. Its pass measure is sandbox success, not full functional correctness. Those limits constrain interpretation; they do not erase the null or justify relabeling it as hidden success.

Historical recurring failures motivate measurement. Missing failed source prevents a clean retrospective demonstration that an earlier repair would fix a later real artifact. New candidate preservation cannot reconstruct the missing past, establish transfer, or make a previously null intervention effective.

## 9. Attack on the October 1 sequence

The proposed order is not the highest-value use of the remaining time.

**Start succession now, before any implementation.** A dated handoff should preserve actual HEAD, dirty-tree manifest, artifact hashes, current findings including this correction, experiment status, and the decisions still requiring authorization. Finish it incrementally, so a stopped or inconclusive experiment still leaves a usable project.

A “clean git status” should not be a handoff requirement. This repository contains substantial pre-existing modified and untracked evidence. Forcing cleanliness would require a separate decision about staging/committing/moving it; recording actual state is what provenance needs. Likewise, safe_restart.sh is a state-changing operation, not a read-only health check. The package should distinguish those command classes.

After handoff begins, the short critical path is:

1. Resolve the experiment's claim, isolation boundary, fixed contextual comparator, outcome contract, resource accounting, and stopping rule on paper.
2. If separately authorized, implement only the isolated path and qualify evaluator/provenance/state isolation on development material.
3. Freeze the complete confirmatory manifest before confirmatory collection, including development-selected baselines; run matched conditions in paired/interleaved blocks rather than baselines days before treatment.
4. Report a positive, negative, invalid, or inconclusive result as warranted, and update succession throughout.

Remove these from the experiment's critical path:

- Live verified_mean and self-edit attribution repairs.
- General physiology cleanup, model upgrades, backend migration, AP-0 repair, and extra learning mechanisms.
- A mandatory historical self-edit-rule experiment. It is independent; its failure need not stop routing, and its success cannot establish missing actor provenance.
- Candidate retrieval/VRM. Evidence preservation is a separate provenance improvement, not an experimental treatment.

The historical-rule proposal has its own problems: old failed source is incomplete; “self-edit success” may mean importability or deployment rather than useful improvement; task/software/load drift can explain correlations; and a gate cannot validate the counterfactual success of attempts it prevents. A strictly post-freeze later window cannot already exist when the rule is frozen. Historical analysis may be cheap, but a prospective claim needs later observations and specified endpoints. It should not be advertised simultaneously as an independent side study and a prerequisite that repairs the primary experiment's identity records.

Do not select sample size to fit a desired significance result before October 1. If only a pilot fits, label it a pilot and preserve the negative/inconclusive outcome. The handoff has value regardless.

## 10. Integration of the new Claude findings

I resumed the original mission rather than reopening the project audit. Before the new message, both wiring claims had been traced, the false council-disconnection claim and sandbox peer-rating route identified, and the main experimental confounds established. The remaining work was controls, provenance, roadmap ordering, and this report.

The new findings **REFINE** that reasoning:

- They strengthen the reason to exclude historical repair/transfer claims from the proposed prerequisite: the relevant failed artifact often did not survive.
- They make the distinction between artifact provenance and influence provenance explicit. Candidate logging improves future inspectability, not evidence that experience improved generation.
- They reinforce an already-inspected source fact: the attempt ledger is not write-only. Error text already reaches later prompts, so a production “reset-state” experiment can retain an uncontrolled experience channel.
- Architecture A adds a directly relevant null against a simple feedback-prompt explanation. Its single starting problem and redundant information prevent extrapolation to impossibility.
- The source changed concurrently to include candidate-preservation fields. That is recorded as external workspace drift, not a change authorized or qualified by this review. The generation-facing consumer still extracts error text rather than forwarding candidate-source fields.

The strongest reason this is a refinement rather than a reversal is that neither preserving candidate bytes nor recognizing recurring failures supplies the missing causal comparison: **does changing the content of prior experience improve independently verified later outcomes beyond matched static routing and retry?** The verdict remains conditional B, with no production-first requirement and no present implementation authorization.

## 11. Closing integrity and scope

Closing verification at **2026-09-22T22:21:28.813590+00:00** found the same HEAD, the same branch relation, no staged changes, **28 modified tracked paths and 274 untracked files**. No opening status entry disappeared. Relative to the immediately preceding pre-write status, the sole added path was this report.

All **three immutable source reports match their opening SHA-256 values exactly**. Of 23 scoped fingerprints taken during inspection, 21 remained identical through closing verification. Two changed externally:

| Path | Earlier SHA-256 | Closing SHA-256 | Interpretation |
|---|---|---|---|
| app/core/self_edit_manager.py | 2e747acc5bf353335596ddc75c94025dc51e7866cef6127aa1042fa9a1a0b36a | e698ab0fbbea5ffde0b14e2806260aa1dc0f1d7cd9af882912683bfdfe5334b9 | Candidate-logging additions appeared during the review; affected paths were reread |
| memory/interaction_log.jsonl | d0c0574291e3b9bfe107e3de30ade8b2ac36d230f96f2cf0589d9b35ae97a764 | a5d2cd1bd29244af80814a576dda9c65b8cd7e8c9a13d7e4b5b1c757b6a205d9 | The live log grew from 25728985 to 26714778 bytes; this review made no log writes |

The 5,033-row/407-sandbox-row aggregation in section 1 describes the exact earlier log snapshot identified above, not the subsequently growing live file. The council-log fingerprint remained fbb8b4a0a528f951c076c73ceeadcd971ab6e39feda275a4d09cefdd24612164; the six joined records remain evidence about that recorded snapshot. Source findings concern inspected files, not an attestation of which version a live process loaded.

SHA-256 of the complete porcelain-v2 status text (including branch headers): opening **a949d05562866c9dbd121b83e1282291268703949f24f5cecb25402b57ce0675**; closing **283b515b40ef2aa97fe77ac2886ccc3fc9ee7dde1624ac7d85569e9d7fee44cc**. These are inventory fingerprints, not substitutes for content fingerprints. This was not a transactional snapshot of the running host.

<details>
<summary>Opening tracked modifications and concurrent added paths</summary>

The opening 27 tracked modifications were:

- CLAUDE.md
- PENDING_DECISIONS.md
- app/core/echo_ground_truth.py
- app/core/liveness_ledger.py
- app/core/provenance_check.py
- app/core/river_deliberation.py
- app/core/self_edit_convergence.json
- app/core/self_edit_generated.py
- app/core/self_edit_manager.py
- app/core/shadow_model.py
- app/core/snapshot_manager.py
- app/core/temporal_environment.py
- app/emergent_scheduler.py
- app/maintenance/night_cycle.py
- audits/2026-09-14_tier5_followup_experiment_design.md
- claude_relay/.last_seen_from_air.json
- claude_relay/README.md
- claude_relay/from_m5.md
- claude_relay/relay.py
- logs/janitor_report.json
- research/OPEN_QUESTIONS.md
- run.py
- sandbox/safe_exec_wrapper.py
- sandbox/scripts/temp_self_edit.py
- scripts/verify_liveness_ledger.py
- scripts/verify_provenance_check.py
- staging/self_edit_candidate.py

In addition to this report, these paths newly appeared in status during the review; they were not created or edited by this review:

- app/core/self_edit_attempt_ledger.py
- audits/2026-09-22_echo_member_stuff_investigation.md
- audits/2026-09-22_feralecho_manual_council_model_upgrade_consultation.md
- audits/2026-09-22_self_edit_candidate_logging_implementation.md
- audits/2026-09-22_self_edit_candidate_logging_qualification.md
- audits/2026-09-22_self_edit_evidence_preservation_investigation.md
- audits/2026-09-22_vrm_retrospective_feasibility_investigation.md
- scripts/verify_self_edit_candidate_preservation.py

self_edit_manager.py was already marked modified at opening, so its additional content change is visible in the fingerprint comparison rather than as a new status path.

</details>

This review created exactly:

audits/2026-09-22_codex_adversarial_attack_on_reconciled_roadmap.md

No code was implemented or repaired by this review. No proposed experiment, AP-0 Stage 1, new constructor, or candidate-logger verification was run. No new experiment data were generated. Existing JSON records were only read and counted. The logger was neither redesigned nor converted into retrieval.

**Effect of the new Claude findings: REFINE.** They strengthen the provenance and existing-history controls and add a bounded null result; they do not change the conclusion that the current roadmap is not ready for implementation.

### VERDICT

B

### WIRING CLAIM A

PARTIALLY CONFIRMED

### WIRING CLAIM B

CONFIRMED

### STRONGEST SURVIVING DOPPELGÄNGER

A fixed feature extractor plus a persisted task-signature-to-strategy success table can beat every single fixed strategy, fail under reset or shuffled feedback, and survive restart while acquiring no new solver primitive or stronger acquisition mechanism. This survives the current design and limits a positive interpretation to fitted routing among existing capabilities; without a competitive frozen contextual router, even the practical advantage over static routing remains unidentified.

### PRODUCTION REPAIR BEFORE EXPERIMENT

NO

### MINIMUM REQUIRED DESIGN CHANGES

1. Keep production untouched by the experiment; use an isolated, versioned strategy/outcome/policy path with experiment-owned state and no inherited history, automatic learning, or hidden query side effects.
2. Replace the false two-wire repair premise: council feedback already reaches ranking; do not pool peer ratings, F2 import success, and functional correctness into verified_mean.
3. Bind actual backend execution and all artifact transformations to the evaluated bytes; credit composite strategies, preserve failures, and distinguish artifact provenance from evidence consultation and causal influence.
4. Use qualified independent functional tests, separate permitted repair feedback from final scoring information, and keep oracle answers inaccessible to candidates.
5. Add a prespecified development-selected frozen contextual router alongside fixed-strategy and retry controls; give comparators the same action menu, feature access, development opportunity, and disclosed training budget.
6. Freeze task ancestry/splits, strategy definitions, real inference/resource accounting, execution order, state-reset and feedback-null interventions, and independent task/history-level analysis with a practical effect threshold and stopping rule.
7. Freeze learning during the final untouched post-restart comparison; restrict positive claims to verified routing improvement and report inadequate power or candidate capability as inconclusive or negative findings.
8. Begin succession immediately and remove production repair, the historical-rule side study, and candidate retrieval from the experiment's critical path.

### STRONGEST CLAIM A POSITIVE RESULT COULD SUPPORT

In the isolated harness, retained verified feedback causally improved strategy selection on the prespecified later workload after restart, beyond the specified frozen contextual and retry controls at matched resource limits.

### FIRST THING TO DO TOMORROW

Create the dated succession manifest recording the actual dirty working tree, immutable evidence hashes, corrected wiring findings, and the unresolved implementation decision.

### IMPLEMENTATION AUTHORIZATION

NOT AUTHORIZED
