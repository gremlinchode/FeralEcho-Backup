# Persistent-learning experiment: adversarial pre-mortem

Mission date: 2026-09-22; completed after resumption on 2026-09-23. Author: Codex. The requested filename is preserved. Scope: the proposed bounded strategy-selection experiment and its proposed AP-0 substrate. This is a conceptual and source-level review, not an experimental run.

**OBSERVED — integrity at entry.** At 2026-09-22 22:51:48 UTC, Git HEAD was `2fba42644c82b9f7096276f4dd338d615cf1bcce`; branch `main`, ahead 17 / behind 0 relative to the recorded upstream. Porcelain-v2 status contained 28 modified tracked files and 276 untracked files, with no staged changes. This was an already dirty workspace. Ten AP-0 source files were fingerprinted at entry; twelve additional relevant files were fingerprinted during inspection. Closing verification is recorded in §20. No application imports, verification suites, model calls, candidate execution, experiment construction, or process restarts were performed. Sealed Stage 1 material was not opened.

**Resumed mission state.** The completed roadmap attack had already rejected production repair as a prerequisite, required a competent fixed contextual comparator, separated artifact provenance from influence provenance, and left implementation unauthorized. The subsequent influence analysis proposed experience substitution, state substitution, restart/restoration, and independent outcome comparison. The unresolved question here is whether even apparently successful versions of those tests could support a false or overstated conclusion. The next step was to inspect the proposed evaluator/task stack and attack those interventions; that is the work reported below. This does not reopen the general repository audit.

Labels throughout: **OBSERVED** means directly inspected source or an identified existing artifact; **INFERRED** means a consequence or counterexample derived from that evidence; **PROPOSED** means a prospective requirement, not implemented or qualified; **UNKNOWN** means not established by this review. Static attack constructions are not claims that historical candidates actually exploited them.

**OBSERVED — late evidence incorporated without restarting.** During closing verification, another author created [the preregistered routing design](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_preregistered_persistent_routing_experiment_design.md). It was absent at entry. I read it because it directly specifies the experiment under attack; its inspected SHA-256 is `ae01655ab8970834b398653ebd9224ab5ca759724056fb4180e9bf0d662346c8`. It explicitly chooses a standalone selector, one frozen model, fixed prompt strategies, PASS/FAIL-only updates, independent lineages, and an update-disabled twin. These are meaningful design commitments, not omissions. It retains the unmodified grader and contains unresolved replay, client, and analysis problems identified below. No claim here treats its proposed exclusion of production memory as an already demonstrated leak in that future standalone harness.

## 1. Executive verdict

**INFERRED — not ready for implementation.** All the advertised positive numbers could coexist with failure of the strongest interpretation. There are two different reasons, which must not be conflated:

1. **False correctness:** AP-0 currently executes candidate code and expected answers in the same Python module. A candidate can consult the answer table at execution time. Its apparent correctness can rise as a selector increasingly chooses that candidate-producing strategy. Updates, restart persistence, state interventions, and a separately invoked grader can all look convincing while task-solving competence has not improved.
2. **Real but bounded adaptation:** a finite task-signature table can learn which existing strategy works on familiar structures, persist, beat a development-frozen router, and improve genuinely hidden correctness. That can establish useful experience-dependent routing. It does not establish reusable abstraction formation, improved acquisition competence, or open-ended accumulation.

The second mechanism is not a disproof of the carefully bounded routing claim. If evaluated experience really changes retained routing state and that change really improves later correctness under fair controls, a fixed update algorithm and frozen model weights do not invalidate system-level learning. Calling this a false positive would move the goalposts. Calling it developmental or general accumulated competence would move them in the opposite direction.

**OBSERVED — the evaluator-readiness conclusion requires correction.** The recommendation in [Claude's evaluator qualification](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_task_correctness_evaluator_qualification.md:150) to use `oracle_runner.grade()` unmodified is not justified for this adversarial claim. A nonce prevents a generator from guessing a fresh literal in advance; it does not isolate an executing candidate from the oracle or its nonce. Generation confinement and grading confinement are also different mechanisms here.

The late routing design repeats this unmodified-grader assumption. It also claims both to replay one fixed task/action/outcome trace without new generation and to obtain a counterfactual history with different task/strategy choices. Those are different estimands. Its selected production `_ollama_query()` client does not expose a generation seed or return the full telemetry the design assumes, and has a fallback generation path with different controls. These are concrete design/source mismatches, not generic concerns.

**INFERRED — effect of the new Claude findings: REFINE.** Candidate preservation improves evidence about what was attempted. Historical `initial_f2_error` already entering prompts makes the uncontrolled-history concern concrete. Architecture A remains a relevant narrow null. These findings strengthen the previous distinction between artifact and influence provenance without reversing the previous no-authorization conclusion. The present source inspection separately **changes the assessment of reusing the AP-0 grader unmodified**: evaluator independence is an unresolved blocker, not a solved prerequisite.

No finite experiment can make every false positive impossible. The achievable standard is to defeat specified alternatives, bound residual uncertainty, and refuse claims the intervention does not identify.

## 2. Claim decomposition

Target: “Retained, independently evaluated experience caused persistent changes in strategy selection that improved later hidden-task correctness beyond what competent fixed contextual routing could explain.”

**PROPOSED — acceptance requirements.** Each row is a separate obligation; passing another row cannot substitute for it.

| Clause | Evidence required | A beautiful-looking failure |
|---|---|---|
| Retained | A reconstructible state checkpoint or base plus deltas, committed before the later decision, with exact state ownership | A ledger contains the experience but the consumer never reads it |
| Independently evaluated | A task contract and expected behavior independent of the candidate; expected values inaccessible to candidate execution; grader output bound to the artifact actually evaluated | A separate process grades against answers the candidate can inspect |
| Experience caused | Controlled intervention on eligible evaluated feedback with task, initial state, routing features, random streams, and other history channels controlled | Record count, elapsed time, or a new error prompt causes the apparent gain regardless of feedback content |
| Persistent | The committed state is loaded after the specified boundary and reproduces the relevant decision effect without reconstruction from another surviving history store | A fresh client reconnects to a warm backend or silently rebuilds state from interaction logs |
| Changed selection | Identical present-task inputs and controlled choice randomness yield a different action or action distribution under the retained-state intervention | Scores change, but ranking/action does not; or the requested route is not the executed route |
| Improved correctness | Independent hidden evaluation of actual artifacts; paired causal utility comparison, uncertainty, and matched resource envelopes | More retries, a stronger backend, oracle exploitation, or different task difficulty raises pass rate |
| Later tasks | Prospective task lineage, exposure records, and a frozen final evaluation window | A new ID or pseudo-word relabels a previously solved template or repeats validation cases |
| Beyond contextual routing | A competent development-selected frozen champion plus an identical update-disabled twin, with equal current-task information and strategy access | A weak or poorly tuned frozen router loses to ordinary calibration |

**INFERRED.** “Beyond contextual routing” can only mean beyond the specified, competently selected comparators on the specified distribution. A finite experiment cannot rule out every possible fixed router, including one tailored with hindsight to the test set.

The following distinctions remain mandatory:

| Observation | Maximum immediate inference |
|---|---|
| Repeated behavior | Recurrence; neither recognition nor benefit follows |
| Recurrence recognition | Similarity was detected; a static signature matcher suffices |
| Static lookup or blacklist | A rule was consulted; its origin and usefulness remain separate |
| Within-context adaptation | Current context affected behavior; persistence remains untested |
| Model-native capability | The worker already possessed a solution procedure |
| Experience availability | Evidence could be read |
| Experience consultation | A mechanically recorded read occurred |
| Experience-caused behavioral change | An intervention changed behavior; benefit remains untested |
| Persistent retained change | The relevant change survived the defined boundary |
| Related-task transfer | Benefit extends to a specified non-identical task relation |
| Independently measured competence improvement | A valid matched comparison shows improved task performance |
| Repeated accumulation | Multiple acquisition episodes add retained value without simply repeating one calibration event |

## 3. AP-0 attack

### What the existing substrate actually supplies

**OBSERVED.** [tasks_v2.py](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks_v2.py:74) specifies 18 T, 12 S, 18 NEAR, and 12 UNREL templates. These are a finite authored repertoire, instantiated with variable worlds and inputs. Fresh tokens and inputs do not make the underlying algorithms prospectively novel.

| Attack | Actual source basis | Consequence |
|---|---|---|
| Template recognition | Stable signatures such as `categorize`, `pick_winner`, `final_state`, CSV/batch variants, and explicit output contracts | A frozen parser/classifier can recover much of the relevant strategy context without any hidden literal |
| Pseudo-word regularities | [worlds.py:15](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/worlds.py:15) emits CVCVC words from fixed alphabets, filtering an OS dictionary | Tokens reduce ordinary semantic associations but expose membership in a manufactured vocabulary; they do not conceal template identity |
| Restricted world prior | K1 has exactly two codes per category; K2 accepts only priority orders with exactly two adjacent lexical descents; K3 contains one each of add/subtract/multiply/set with small specified parameter ranges | A programmer familiar with the generator can use a much narrower hypothesis space than the learner's prose alone supplies |
| Teaching-order shortcut | K2 canonical teaching episodes enumerate adjacent priority pairs in their true priority order | An order-sensitive extractor can recover the order from presentation structure; it need not infer it from the winners |
| World/seed reconstruction | World generation uses `random.Random(seed)`; case seeds derive deterministically from task ID, world, and partition | Known world/seed information can reconstruct answers. Merely using a different seed is not an access-control argument |
| Metadata routing | Task records carry family, split, base implementation, signature, and realization labels | Accidentally exposing internal metadata can turn the purported transfer test into task-ID routing |
| Narrow input support | Record amounts are nonnegative, ranking scores lie in a small range, names come from a fixed list, event sequences are short | Programs exploiting generator invariants can pass while violating the broader natural-language contract |
| Familiar unrelated tasks | UNREL includes palindrome, FizzBuzz, flattening, reversing words, and basic aggregation | Improvement may select already capable pretrained procedures; it does not show acquisition of those procedures |

**UNKNOWN.** I have not established that an LLM inferred a hidden seed from pseudo-words. That is unnecessary for the stronger attacks above. A fresh, secret, unexposed seed blocks a particular reconstruction route, not template recognition or privileged schema knowledge. Dictionary contents can also affect reproducibility; a seed and code hash alone do not pin an OS-dependent dictionary.

**OBSERVED — a semantic boundary matters.** The current simple AP-0 worker constructs a fixed request from public specification, carrier, and examples. The existence of a readable source file does not prove it entered that request. Conversely, extending this machinery to a tool-using FeralEcho agent makes its broader read surface relevant. Actual request bytes and actual allowed reads must be distinguished from intentions stated in docstrings.

**INFERRED — freezing is narrower than secrecy.** Content hashes, refuse-to-overwrite writes, and read-only file modes are useful integrity controls. They do not prove that a researcher or process never read the answers, that a fresh vocabulary was never exposed, or that every runtime dependency was frozen. The whole repository is not identified by HEAD in this dirty workspace. A prospective freeze needs actual task/prompt/strategy/evaluator/client/profile bytes, model identity, relevant configuration, development history and analysis choices, with a dated commitment outside the mutable result chain if chronology is load-bearing. A hash chain whose contents and final anchor can both be replaced is not independent proof of chronology. These are limits of what the mechanism establishes, not allegations of evidence tampering.

### The partition and mutation claims are weaker than advertised

**OBSERVED.** [make_cases2()](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks_v2.py:164) uses different RNG streams for VAL and TEST, deduplicates only within a stream, and greedily chooses cases to kill a finite mutant catalogue. It does not exclude VAL inputs from TEST. The [verification script](/Users/richietate/Desktop/FeralEcho/scripts/verify_accumulation_probe_v2.py:22) checks literal VAL/TEST non-overlap for one `K1.T3` realization, not every task.

**INFERRED — concrete collision counterexample.** The palindrome generator draws from only seven fixed strings. The default requested case count is ten. If each pool encounters all seven strings, each partition includes all seven, so VAL and TEST inputs coincide despite different seeds. The six-code `category_of` domain has the same problem. This is a source-derived possibility, not a newly generated dataset or a claim that every existing partition overlaps. A prospective “untouched held-out cases” claim needs actual set/lineage checks, not distinct seed labels.

**OBSERVED.** A surviving mutant is labeled equivalent when 4,000 additional draws from the same generator fail to distinguish it. This is not a proof of semantic equivalence. `k1_log` explicitly promises behavior for an empty string, but its generator uses `_rec()` with a positive record count. Thousands more draws from that support cannot test the empty string.

**INFERRED.** The mutant catalogue usefully attacks specified local mistakes. It does not cover answer-table access, pathological equality objects, evaluator sabotage, untested domain boundaries, or all materially wrong implementations. Agreement with `oracle_b_v2` helps catch implementation disagreements; both implementations still share the contract, world, input distribution, and assumptions. It does not establish an adversarial oracle boundary.

### Is this the right workload for routing?

**OBSERVED.** T/S intentionally omit local convention values. AP-0 normally supplies those through acquisition episodes or retained carriers. A selector that only receives pass/fail rewards is not automatically a mechanism for giving workers the missing convention.

**UNKNOWN — presently unspecified.** Will every arm receive the same convention evidence? Will it receive a GOLD carrier? Will a constructor run? Will a strategy itself infer the rule? These choices change the estimand. Giving only the adaptive arm accumulated convention answers would measure extra answer information, not just a better choice among equally informed strategies. Giving everyone GOLD would remove induction from the task. Both can be legitimate component designs, but cannot be silently interchanged.

The late design specifies fixed single-call prompt strategies on one model, with zero retries recommended, but leaves their content undesigned. It does not resolve this convention-information question. If worlds are genuinely fresh and the missing random convention is neither supplied nor inferable from the allowed inputs, routing among differently phrased prompts cannot recover it reliably. Hidden answers must not become the unnoticed substitute for missing task information.

**OBSERVED — qualification remains incomplete.** Existing [primary qualification results](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/results/primary/summary.json) report GOLD gate acceptance 10/12, including K2 2/4, below the declared 0.85 pooled sensitivity threshold. WRONG and NONE each accept 0/12. The [post-hoc auditor correction](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/results/posthoc_auditor_v2/summary.json) recovers K1 exactness of 6/6 R0 and 5/6 R1 while leaving K2/K3 at zero; it labels K1 partially qualified and the gate unqualified. [QB results](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/results/qb/summary.json) report K2 0/6 and K3 0/6 exact, with respectively one and five empty, length-terminated drafts. These figures are readings of existing result artifacts, not a new regrading.

**INFERRED.** The failures do not all identify an induction deficit: K1 had an auditor problem; K3's unrestricted rule is underdetermined without a declared hypothesis family; generation budget and worker execution also matter. A strategy menu needs demonstrable feasible solutions and useful differences on development tasks before a routing opportunity can be assumed. No model replacement is warranted by this review.

**Verdict:** reusable procedural-task components exist; the proposed task substrate as a qualified measurement of this new claim does not yet exist. T/S/NEAR/UNREL distances are analyzed in §12.

## 4. Oracle/evaluator attack

**OBSERVED — decisive source path.** [oracle_runner.grade()](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/oracle_runner.py:41) concatenates candidate source and nonce-substituted test source. [make_test_code()](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks.py:246) defines `_CASES`, a list of `(args, expected)` pairs, in that same module before calling the candidate function. The grader accepts a successful wrapper run containing the nonce-bearing pass marker.

**INFERRED — answer-reading candidate.** A candidate function can, when invoked, inspect the module's `_CASES`, match its current arguments, and return the associated expected value. The legitimate test loop then emits the legitimate fresh marker. It need not guess the nonce, know the world before generation, implement the intended rule, or write outside the sandbox. This directly defeats the claim that a fresh nonce makes hidden expected answers inaccessible to generated code. The candidate can also inspect the caller's current expected value; hiding a variable name would not establish a security boundary.

Other source-level attacks include returning an object with adversarial comparison behavior where `r != e` is the correctness check, modifying the shared execution environment, or reading the concatenated script containing the nonce. These are counterexamples for qualification, not allegations about observed model behavior. None was executed during this review.

**OBSERVED — the two jails are different.** [jail.py:6](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/jail.py:6) starts from `allow default`, denies reads under the experiment root except the arm root, denies most writes, inherits the environment, and leaves networking open. It does not enforce its docstring's claim that an arm can read only its own root. Source, audit copies, and other history outside the experiment root are outside that read denial. The network rule does not limit access specifically to the intended Ollama endpoint.

Grading uses [sandbox/echo_sandbox.sb](/Users/richietate/Desktop/FeralEcho/sandbox/echo_sandbox.sb), which denies network and most writes but allows `file-read*`. The [wrapper's script execution](/Users/richietate/Desktop/FeralEcho/sandbox/safe_exec_wrapper.py:464) loads the combined file as a Python module. Its write restrictions do not hide the module's contents or its globals. The AP-0 [analysis grader](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/grade.py:1) explicitly runs outside the generation-arm jails.

**INFERRED.** Nesting a generation jail around grading, even if done, would not solve same-module answer access. The trusted comparison must occur outside the untrusted candidate's addressable state. The candidate may receive function inputs; it must not receive expected outputs, grading control, or executable comparison hooks inside the trusted checker.

**PROPOSED — qualification requirement, not an implementation.** Specify a process/data boundary where a trusted evaluator holds expected values and compares constrained serialized candidate outputs; candidate stdout cannot authenticate a pass; candidate execution cannot read oracle files, test control state, or other arms. Qualification must include hostile candidate behavior, not only correct references and ordinary mutants. Require a defined correctness contract and independent checks of the oracle itself. No change to AP-0 is made or authorized here.

## 5. Feedback-leak attack

**OBSERVED.** The test loop deliberately prints failing input, actual result, and expected result. This is not merely an accidental `AssertionError` disclosure. `grade()` returns stdout/stderr tails, duration, timeout, infrastructure status, and pass status. A 300-character limit reduces volume, not the presence of answer information.

| Channel | Concrete way the oracle becomes a teacher | Necessary boundary |
|---|---|---|
| Stdout | First failing `(args, actual, expected)` appears by design; candidate can print accessible oracle state | Never deliver hidden-test stdout to generation, selection, or retries |
| Stderr / exceptions | Exception values, tracebacks, source lines, paths, or deliberately encoded answers reach error tails | Separate trusted administrative diagnostics from learner-visible feedback |
| Return structure | Per-case results, number of tests reached, timeout class, and infra classification reveal more than one reward | An explicit schema, not arbitrary forwarding of the grade dictionary |
| Pass marker | Same-process code can access or arrange the marker; substring matching is not proof of semantic success | Trusted evaluator creates the outcome outside candidate-controlled stdout |
| Timing | Early failure reveals a prefix length; repeated timings can encode which cases failed | No evaluator timing feature for the selector; keep resource administration separate |
| Metadata / filenames | World, split, task base, seed, or expected-answer location leaks through names or errors | Opaque identifiers and an allowlisted present-task interface |
| Environment / filesystem | Inherited variables, readable oracle copies, artifacts outside the denied root | Explicit accessible inputs; no ambient production or audit state |
| Researcher decisions | Looking at failed TEST answers informs prompts, task exclusions, champion choice, or checkpoint selection | Final sealed evaluation after protocol lock; changes invalidate that confirmatory window |

**PROPOSED — minimum learning feedback.** After an irrevocably completed training attempt, expose only a trusted episode identifier and one defined task-level correctness bit. Bind the bit externally to artifact, actor, task-contract, and evaluator hashes. Keep diagnostics and cost measurements in a separate audit channel unavailable to policy and worker. Even coarse failure labels require justification; they are additional teaching information, not free bookkeeping.

For a repair strategy, distinguish a declared public/development test tool from the final hidden evaluator. Its permitted diagnostic channel and query budget must be identical for fixed and adaptive versions. Do not turn final hidden correctness into a retry oracle. If training uses a richer oracle, name that treatment and prevent overlap with final evaluation.

**INFERRED.** A correctness bit is still information. Repeated adaptive queries can identify a finite hidden rule, especially in these small worlds. The defensible requirement is bounded, declared training feedback and an untouched final holdout, not “no information flows from evaluation.” At final evaluation there should be no feedback to update, select another candidate, repair, choose a checkpoint, or change researcher decisions before the confirmatory analysis is locked.

**OBSERVED — existing history already supplies another teaching channel.** [_attempt_ledger_evidence_section()](/Users/richietate/Desktop/FeralEcho/app/core/self_edit_manager.py:2843) reads `initial_f2_error`, truncates it to 400 characters, and inserts it into a later targeted prompt alongside outcome and convergence information. Candidate-source preservation does not create this existing path, and the current consumer reads that named error field rather than preserved candidate source. Freezing only the proposed selector does not remove this path. This review neither changes the logger nor proposes candidate retrieval.

## 6. Influence-provenance attack

The four proposed interventions are useful, but their labels alone do not identify the causal mechanism.

| Intervention | Positive result that still misleads | What would make it informative |
|---|---|---|
| Experience substitution | Removing a record changes event count, RNG consumption, classifier training, or the historical error text in a prompt; the correctness content is irrelevant | Preserve eligibility/count/timing and declared exogenous inputs; substitute the intended feedback content only; separately test omission if that is the estimand |
| State substitution | The checkpoint bundles a task-answer cache, feature scaler, route counter, or prompt note with the proposed policy | Enumerate owned state and verify every consumer input; interpret the effect of the whole swapped state unless a narrower intervention is actually performed |
| Restart/restoration | The restored policy is accompanied by surviving logs, backend state, or a bootstrap path that reconstructs the useful information | Restore into a fresh isolated consumer with the declared retained state as its only history channel; compare loaded semantic state and decisions |
| Independent outcome comparison | A separately invoked but vulnerable oracle rewards answer-reading programs; or the swapped state routes to extra retries | Qualify correctness independently of candidate behavior; match action execution and resource contracts |

**INFERRED — all four can be positive together.** Suppose historical records affect a persisted route counter and a prompt-history cache; later tasks happen to favor the stronger strategy. Removing experience changes the counter/cache; swapping the checkpoint changes routes; restoring it preserves the effect; ordinary functional grading confirms better programs. Yet independently evaluated outcome content may have had no role. A count-matched, content-substituted control with all other history channels controlled would attack this alternative. A weak “delete history” control would not.

A more damaging construction genuinely updates strategy success statistics from feedback but learns to prefer a candidate that reads `_CASES`. Experience substitution, complete state substitution, restart, and independent invocation of the same grader all validate a real causal route to higher scores. The interpretation fails specifically at correctness and evaluator independence.

Finally, a correctly instrumented finite routing table can pass every intervention with a sound oracle. That supports bounded adaptation and still leaves abstraction and acquisition improvement unestablished. No provenance mechanism can manufacture the stronger inference.

**PROPOSED — minimal causal record.** Required fields are: episode ID; task/lineage and allowed-input hashes; actual generation actor and artifact hash; independent evaluator/version and eligible outcome; update ID/rule version and parent episode; reconstructible pre-state, committed post-state, and delta; restart/checkpoint/load identity; later decision ID, feature values/hash, feasible action menu, consumed state identity, scores/action probabilities where applicable, choice randomness, actual chosen/executed action; resulting artifact, evaluated outcome, and resource use. A base snapshot plus deltas can suffice; full snapshots at every event are unnecessary. Exact inputs must remain recoverable behind hashes.

Update explanations in prose are useful debugging notes and unnecessary as causal evidence. Logging a read proves availability/consultation, not effect. Model statements that they “used E” add no causal identification. Records must come from the experiment controller's observation of inputs, state transitions, and execution, not just the learner's account of itself. Hashes bind bytes; they do not independently attest honest execution.

**PROPOSED — replay estimand.** To estimate an experience's total downstream effect, replay the branch from before that experience, including later decisions, observations, and updates under the same exogenous task schedule. Deleting E from the final ledger while leaving its descendants unchanged is not that counterfactual. Reusing fixed later logged observations can estimate a narrower update effect, if explicitly named; those observations may have been produced by actions the counterfactual branch would never take. Do not silently treat that as the total learning effect.

**OBSERVED — the late design makes this error concretely.** Its §11 records Arm C once, replays the identical `(task, selected strategy, candidate, outcome)` trace with all outcome labels flipped, and forbids new generation. The next paragraph says TRUE and SHAM will diverge in which task/strategy pairs occur. They cannot both replay the identical recorded action trace and generate their own divergent action histories. Fixed-trace label flipping is a legitimate controlled test of update-content sensitivity conditional on that trace; it is not a full counterfactual online rollout. A diverging rollout requires valid outcomes for the actions it actually selects, obtained under a prospectively specified common-randomness or complete potential-outcome procedure, not borrowed from another action.

**INFERRED.** TRUE beating inverted labels is also weaker than beating an uninformative count-matched feedback control: deliberately anti-correlated labels can actively poison a sensible fixed update rule. Conversely, indistinguishable held-out utility does not prove insensitivity to feedback; distinct policies can tie, saturate, or lack statistical power. The design must distinguish state sensitivity, action effects, and beneficial utility. Its provenance specification also says U is written by the selector's `update()` and later says all records are controller-written; independent observation must be explicit rather than inferred from the record's name.

## 7. State-boundary analysis

**OBSERVED — current selection is not one scalar.** [learn()](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:808) updates classifier/scaler state, counts, and heuristic quality means. `learn_from_sandbox_outcome()` updates coding classifier/scaler state and a separate sandbox count, rather than directly updating the mean consumed by `score_model()`. [Council ratings](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:936) do update that mean; the prior blanket claim that council outcomes cannot affect selection was false. Council preference is still not independent task correctness.

[score_model()](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:995) uses a count threshold of five and the mean; `rank_models()` combines it with historical reflection scores whose decay depends on wall-clock age. River influence depends on observation counts. `choose_model()` uses task classification, candidate tags, score-derived exploration, and global randomness. Thus changing counts alone can change selection without demonstrating sensitivity to correct versus incorrect outcomes.

**OBSERVED — persistence is not a synchronous assertion.** [_do_save()/save()/load()](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:1058) use a background writer, a queued save request, several state structures, and a rule refusing to overwrite a disk state with more observations. The snapshot contains object references rather than a full deep immutable copy. A call to `save()` or a hash of one dictionary is insufficient evidence of a coherent, committed checkpoint. These are source-level reasons to verify persistence, not a claim that an observed historical checkpoint was corrupted.

**PROPOSED — exact experimental boundary.** At decision time, the action must be expressible as a function of the allowed current-task record, frozen mechanism, declared retained state, and assigned random input. Every other cause must be excluded, held fixed, or treated as randomized nuisance—not omitted from the state definition because it is inconvenient.

| Boundary component | Must be controlled |
|---|---|
| Owned retained policy state | Parameters/tables, counts, priors, thresholds, exploration schedule, learned normalization, eligibility and pending update state |
| Task representation | Classifier, feature extractor, tokenization/features, task-type override, preprocessing, normalization and their versions |
| History exposure | Prompt builders, conversation context, reflection files, initial-F2 error evidence, outcome/convergence notes, retrieval/FAISS/council memories if reachable |
| Strategy execution | Exact prompts, public examples/carriers, tools, parsing, retries, repair feedback, council/synthesis graph, fallback and circuit-breaker state |
| Actor/backend | Actual resolved model/digest, adapter, quantization/runtime/options, response association, context/session state, cache policy and backend availability |
| Randomness and time | Separate named streams for choice, generation, task order, and updates; clocks if policy uses age/timeout; execution order and concurrent load |
| Persistence | Files, in-memory consumers, write queue, completion/commit identity, loader behavior, bootstrap/reconstruction paths, and any external history reads |
| Evaluation | Hidden oracle state outside this boundary; candidate sees only permitted inputs, policy only declared training reward |

This is not a demand to snapshot all of production. The smaller and safer design is an isolated consumer with a small enumerated read interface, excluding production memory and background mechanisms entirely. Redirecting one pickle path while importing everything else does not prove isolation.

**OBSERVED — what the late design resolves and does not.** It explicitly excludes RiverBrain, council learning, task classification, retrieval, and the attempt ledger by using direct generation. That is the appropriate conceptual exclusion; the production paths above are a boundary checklist, not evidence that its not-yet-built selector already reads them. However, its proposed direct client is a production helper with additional behavior:

- [river_deliberation._ollama_query()](/Users/richietate/Desktop/FeralEcho/app/core/river_deliberation.py:397) imports `_cb_is_open`, `_cb_record_failure`, and `_cb_record_success` from the orchestrator. Their [definition](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:1254) is a process-global in-memory dictionary keyed by model/task type, with a three-failure threshold and 300-second wall-clock cooldown. This resolves the design's named UNKNOWN: the traced breaker is not a file-persisted learner. It can still couple arms sharing a process or alter attempted exposure after failures.
- `_ollama_query()` accepts no generation seed or general options dictionary. It collects `result_meta` internally, uses `done_reason` for a warning, and returns only text. Its caller cannot obtain the assumed generation-token accounting or matched backend seed merely by passing a selector seed.
- A streaming exception can trigger a second call through `ollama run`; this fallback drops the supplied system message and does not forward the same temperature/max-token settings. “One call, zero retries, identical request controls” is therefore not guaranteed by choosing this helper.
- Its downstream [stream_query_ollama()](/Users/richietate/Desktop/FeralEcho/app/ollama_handler.py:421) performs one-time model-pool registration and can route MLX names. For the configured Echo model, [_build_chat_messages()](/Users/richietate/Desktop/FeralEcho/app/ollama_handler.py:97) reads an mtime-cached Modelfile identity block. These conditional inputs must be pinned or excluded; the helper's immediate body is not the whole request-construction boundary.

The existing AP-0 HTTP client illustrates a smaller request interface, but this review neither replaces the selected client nor authorizes an adapter. A future implementation must satisfy the stated boundary and retain actual response metadata; a promise of statelessness does not resolve these source facts.

**OBSERVED.** AP-0's direct Ollama client requests `keep_alive: "10m"`. A fresh Python generation process therefore does not imply a fresh model-server process or cleared cache. The requests may still be logically stateless; backend warmth is not itself evidence of semantic memory. It can nevertheless affect timeouts, latency, or resource comparisons.

**PROPOSED.** Declare which boundary is tested: fresh selector process, fresh worker context, or backend restart. Control hidden context and standardize or randomize cache/load conditions. If the backend is nondeterministic, identical seeds do not guarantee identical outputs; use repeated paired histories and report that uncertainty. Do not infer the absence of all hidden state from a policy-state hash.

## 8. Update-disabled-twin attack

**INFERRED.** “Same initial checkpoint, updates off” can still be an unfair comparison. Updates may add context, evaluator calls, feature learning, retry opportunities, time to warm a model, or a different RNG trajectory. An adaptive arm may appear better because its normalization/classifier changed, not because the named strategy policy learned. That is an alternative system mechanism requiring its own claim.

**PROPOSED — couple these between twins:**

1. The development-trained starting state; frozen classifier/features; model pool and actual backend identities; action implementations; prompt/context limits; tool and feedback permissions.
2. The exogenous prospective task sequence and task contracts within each paired history, with no arm choosing easier later tasks. An adaptive curriculum is a different treatment.
3. Per-task generation, token, retry, evaluation-query, and tool budgets. Account for every planning, repair, alternate, council, and synthesis call. Equal calls are not equal compute if models or token limits differ.
4. Choice random variates and action-specific generation seeds indexed by history/task/action/attempt, rather than a shared mutable RNG whose draw count changes when an update occurs. Different actions may legitimately yield different rewards.
5. The administrative execution schedule, logging interface, environment, and cache policy. Interleave/randomize arm order; prevent cross-arm cache, file, or conversational information transfer. Measure overhead rather than claiming equality from equal settings.
6. Restart/restoration and final evaluation rules. Both arms receive the same operational treatment, except that the adaptive arm retains the declared experimental updates.

The twin can perform a discard-only update calculation if update overhead would otherwise confound resource or timing comparisons, but that calculation must not mutate feature state, advance decision randomness, or leak into later decisions. Matching context does not mean padding an adaptive history into the frozen policy's decision input: that would let a nominally frozen program adapt in context. Both get the same present task; only the specified retained-state channel differs.

**INFERRED.** Exact rewards cannot be coupled when arms take different actions; forcing them to receive the same observed reward creates fictitious experience. Exogenous opportunities and evaluation contracts should be coupled. Unchosen-action outcomes used for analysis must remain hidden from a bandit learner unless every comparator receives the same declared full-information interface.

**OBSERVED / INFERRED — late design's resource scope.** Its §14 gives only C a prospective acquisition phase and matches inference cost during final evaluation, with acquisition cost reported separately. That is a defensible **matched final-inference-cost** estimand, not equal lifetime compute. Do not describe it as the latter. If total-cost superiority is intended, the frozen policies need a prespecified way to spend the same available resource budget. If only final inference is compared, report acquisition cost and control backend warmth before evaluation without pretending the frozen arms underwent identical execution histories. Its demand for deterministically identical generated outcomes after restoring S1 is also unsupported by a matched selector seed; reproducible selector actions and reproducible backend text are separate properties.

## 9. Frozen-router attack

**INFERRED.** Beating a hand-written straw man is easy. Beating a poorly selected winner from a weak development set is also easy. A development-frozen policy can lose through calibration mismatch while having exactly the same representational competence as the adaptive one.

**PROPOSED — strongest cheap selection procedure.** Before prospective tasks are exposed, define a modest comparator set: competent rules using legitimate present-time features; a regularized contextual value model or shallow decision policy; the identical adaptive architecture fitted on development experience then frozen; best constant model/strategy; and a fixed retry policy under the same resource envelope. Include a straightforward task-signature-to-strategy mapping where the available features make that feasible. “Non-learning” here means no updating from prospective experience, not that development training is forbidden.

Use development training to fit candidates and a separate development validation set, split by world/template lineage, to choose the champion under a predeclared score/cost rule. Give every candidate the same allowed information and feasible menu. Check action coverage and whether an apparent specialization rests on a handful of easier examples. Select once, with a specified tie/fallback rule; freeze mapping, features, thresholds, menu, and tuning procedure. If there is insufficient development evidence to choose credibly, call champion quality uncertain rather than selecting whichever comparator is most convenient.

**INFERRED — selection overfitting remains.** Trying many policies or repeatedly inspecting validation results spends the validation set. A held-out development qualification block or properly nested development splits can check stability. Development superiority alone cannot certify future optimality. Human iterations and feature choices are part of baseline development and must not be informed by prospective outcomes.

**PROPOSED — minimum competence evidence.** Report the candidates considered, development lineage splits, resource accounting, validation performance and uncertainty, action coverage, and sensitivity to plausible development resampling. Demonstrate that the champion captures obvious task-type and difficulty routing advantages and is competitive with the frozen twin and constants. Freeze remaining comparator results as secondary checks: if the adaptive arm beats the selected champion but loses to another predeclared frozen policy, disclose it and narrow the conclusion. Do not switch the primary comparator after seeing final results.

**OBSERVED.** The late design describes A as hand-built and B as necessarily a different architecture, without specifying the champion-selection competition above. Competence does not require different architecture: the best development-frozen policy could be the update-disabled twin itself. Do not restrict A to hand-written rules merely to keep the arms distinct. If A and B coincide after an honest development comparison, their conceptual questions remain distinct but duplicate model calls need not manufacture an artificial comparator difference.

**Model-capability control.** Prefer one fixed local model with fixed direct/repair/alternate strategies if it supplies a real routing opportunity. If multiple models are used, include always-the-strongest-feasible-model and competent static difficulty routing, with model-sensitive cost accounting. A policy can legitimately learn where an existing model succeeds; it has not thereby improved that model. Existing AP-0 worker failures make solvability a qualification issue, not a reason to upgrade models until a positive result appears.

## 10. Task-history/order attack

**INFERRED — histories are the primary experimental units.** A final selector is a product of an entire path of tasks, choices, rewards, and updates. A thousand final tasks scored under one fortunate learned state do not provide a thousand independent demonstrations that experience reliably improves a learner.

An early lucky success can lock in a strategy; early failures can suppress it. Family clustering makes a recency rule seem to specialize. A late easy-task block creates a rising curve with no improvement at all. An adaptive sampler can present the learner only tasks it already handles. Discarding failed or crashed histories selects survivors. A deliberate curriculum can help, but then the result is conditional on that curriculum.

**PROPOSED.** Replicate independently initialized paired histories across prospectively sampled worlds and orders. Pair arms within a history on the same exogenous schedule and evaluate their locked final states on the same held-out tasks. Use independent held-out worlds across independent history pairs, or explicitly model shared test-world dependence. Repeating generation seeds within a history estimates worker variability, not independent acquisition histories.

Counterbalance order and family positions so later is not systematically easier. Predeclare the order distribution; retain adverse as well as lucky histories. If tasks must be clustered, report that regime and test the claim within it. Do not attribute a curriculum-specific benefit to general order-robust accumulation. The required history count is a prospective precision/power decision, not a number of cheap repeated calls chosen after the effect appears.

## 11. Statistical attack

**OBSERVED.** AP-0's existing [bootstrap](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/grade.py:22) samples task identifiers after averaging calls within those units. It was written for an earlier carrier comparison. It is not automatically an appropriate uncertainty estimator for selectors sharing a longitudinal learning history or for tasks sharing a convention world.

**PROPOSED — minimum analysis before implementation.** Define a per-history final score using a fixed weighting of prespecified task families. For each independent paired history, compute adaptive minus champion and adaptive minus update-disabled-twin scores. The primary endpoint is the post-boundary held-out difference at a fixed budget, not the slope of the training curve. Specify a practically meaningful improvement and a history-level interval/test before collection. Choose the number of histories from development estimates of between-history variability and the desired precision/power. If the budget permits only a pilot, label it a pilot.

| Statistical attack | Minimum protection |
|---|---|
| Many calls, one world or learned state | Analyze at the history/world level; retain within-history correlation |
| Multiple retries from one artifact lineage | One prespecified task-level outcome at its full allowed budget; record every attempt and cost |
| Shared test families/worlds | Independent evaluation sets across history pairs or a design/analysis respecting both dependencies |
| Repeated checkpoint peeking | One locked primary checkpoint; earlier curves descriptive or handled by a prespecified sequential rule |
| Optional stopping | Fixed history count/budget or an explicit valid sequential design |
| Many endpoints/comparators | One primary estimand; prespecify required joint claims and multiplicity handling; no “whichever contrast wins” |
| Subgroup fishing | Fixed family weights and subgroup definitions; exploratory findings labeled exploratory |
| Transfer redefined after results | Freeze the structural novelty relation and exposure exclusions before collection |
| Infra exclusions | Count all started histories; define outcome-blind administrative invalidation/replacement rules and report every exclusion |
| Length termination / empty output | Treat according to the frozen end-to-end task contract, ordinarily a failure within budget; do not delete difficult attempts |
| Adaptive retries | Charge all calls and evaluator queries; include success only under the same retry contract |
| Regression to the mean | Select histories/tasks prospectively, not because of an unusually poor initial score; use concurrent paired controls |

A candidate can print text resembling an infrastructure error; current error-string classification must not grant it an outcome-dependent free retry or exclusion. Administrative failures need trusted attribution. Shared outages can invalidate a whole paired block under a predeclared rule, but dropping only the arm that failed is not neutral.

If both adaptive-versus-twin and adaptive-versus-champion superiority are required for one joint claim, prespecify that joint success rule. If separate claims or many structural strata are advertised, handle their additional multiplicity. Thousands of task outcomes do not compensate for too few histories to estimate between-history uncertainty.

**INFERRED.** Positive training trends can vanish under these comparisons. A null final contrast is a valid result. Failure to reject zero is not evidence of equivalence; a claim of no meaningful effect needs sufficient precision around a declared equivalence margin. No precise sample-size sufficiency is established here because the prospective workload and history variance are still unknown.

**OBSERVED — the late design supplies a partial statistical plan.** It correctly names lineage as the unit, C-minus-B on S as primary, C-minus-A as secondary, and pilot-informed final sizing. Those are real commitments. The remaining problems are specific: its full claim requires both comparisons although only one is primary; no effect threshold or final lineage count is fixed; three to five pilot lineages cannot justify a precise variance/effect estimate without substantial uncertainty; and a stopping rule frozen only before holdout must not permit choosing acquisition length after seeing favorable prospective trajectories. The earlier general absence of a plan is narrowed to these unresolved specifications.

Its §17 also excludes timeouts from the correctness denominator under an infrastructure heading. A candidate that exceeds the task's runtime budget is ordinarily an end-to-end failure, not administrative missingness; the actual grader distinguishes timeout from `infra`. Comparing exclusion rates afterward does not recover outcomes selectively removed from harder arms. Pooled-task Wilson intervals, even alongside cluster-aware analysis, must not be presented as valid uncertainty intervals for correlated observations. Its proposed literal-input non-overlap check is a useful new requirement, but it is not already guaranteed by `make_cases2()`'s within-partition deduplication.

## 12. Transfer/lookup-table attack

**INFERRED — concrete weaker system.** Freeze a parser that maps current text to a small signature: aggregation/ranking/state-update, input representation, requested output, presence of an explicit convention, and difficulty/repair indicators. Persist outcome counts per signature and fixed strategy. Select the best estimated strategy with a fixed exploration rule. Workers, solution procedures, hypothesis space, and update rule never improve. A fresh worker reads the selected strategy and current task; only the selector table persists.

This system can outperform a development-frozen mapping when prospective outcome frequencies differ or development estimates were noisy. It can pass hidden correctness tests using model-native solutions, survive restart, and show genuine experience-caused state/decision effects. It can saturate after estimating a finite table and never invent an abstraction or solve a problem outside the capabilities of its fixed menu.

| AP-0 label | Actual distance supplied by source | Could this system pass? |
|---|---|---|
| T | New task applications within the same small convention families | Yes; signature mapping plus current convention information is sufficient in principle |
| S | Tuple/dict/CSV/batch/repetition changes around the same convention and familiar operators | Yes; a fixed parser and pretrained worker can already handle the wrapper; routing gains need no new abstraction |
| NEAR | Same vocabulary with an explicitly supplied conflicting convention, generated by a fixed mismatch transformation | Yes; recognizing explicit override instructions tests interference control/instruction following, not acquisition of a new hidden family |
| UNREL | Familiar ordinary programming operations, unrelated to the local conventions | Yes; general routing calibration or choosing the better pretrained strategy can improve these without acquiring their algorithms |

**INFERRED.** None of these labels by itself rules out the signature-table explanation. Holding an S template out of online training is useful, but the parser or pretrained model may already represent its structure. New pseudo-words challenge exact token memorization; new worlds challenge reuse of particular convention values; new wrappers challenge literal prompt lookup. These are distinct achievements, all weaker than constructing a reusable abstraction.

A prospectively withheld rule family, with different relations/compositions and controlled feature overlap, begins to challenge the declared finite signature table only if the fixed feature extractor, pretrained workers, and available strategies could not already handle it equally well. Behavioral transfer alone does not locate where the reusable structure arose. A finite task suite also cannot refute every possible lookup implementation.

**PROPOSED — claim discipline.** Report the achieved distance explicitly: unseen instances, unseen parameter realizations, unseen wrappers, or prospectively unseen rule families. Do not pool them into one “novel tasks” claim. A future stronger transfer study would need an explicit bounded lookup comparator and interventions on the purported reusable representation; that is beyond the first unsupported arrow here and is not a recommendation to build it now.

**INFERRED — two mistakes in the late interpretation matrix.** Higher correctness on NEAR is not itself evidence of overgeneralization: a better general strategy can obey the explicitly conflicting convention more reliably. The adverse outcome is inappropriate application of the old convention, not a positive correctness delta. Likewise, improvement on UNREL can be legitimate general portfolio calibration; it warrants checking nonspecific alternatives but does not logically prove a confound. “NEAR/UNREL flat” requires a precision/equivalence criterion, not two nonsignificant differences. Predetermined interpretations can still be wrong.

The recommended exact signature table also needs a clear generalization mechanism. If its key includes a unique function name and S functions were unseen during prospective updates, those S keys may retain their development values or use an unchanged fallback. T-key updates then cannot change S decisions. A coarser shared signature could transfer routing estimates, but that shared structure is engineer-supplied. Specify which case is intended before interpreting an S effect as learned abstraction; an impossible S effect can reveal a hidden channel rather than surprising intelligence.

## 13. Accumulation boundary

**INFERRED.** An ordinary contextual bandit over fixed strategies can keep adapting forever to changing task frequencies without acquiring a new problem-solving primitive. Its stored table can improve routing repeatedly while remaining bounded by the fixed feature representation and action menu. For a one-action decision, its attainable expected performance is bounded by choosing the best available strategy for each context; for repair sequences, the analogous bound is the best permitted action sequence under the resource contract. More experience cannot create an absent strategy.

A successful bounded routing experiment therefore does not establish: improved acquisition efficiency; autonomous hypothesis-space construction; new reusable abstractions; retention across multiple genuinely new families; avoidance of interference; autonomous useful curriculum generation; or an ability to expand its own competence frontier. It establishes none of these by extrapolation from a rising curve.

**PROPOSED — minimum before a broader accumulation phrase.** Require several prospectively separated acquisition cycles, retained benefit on earlier capabilities, additional benefit on later non-identical tasks, independently measured utility at controlled cost, and a causal account of the retained state responsible. Specify whether the accumulation is of routing estimates, task rules, reusable procedures, or an improved acquisition mechanism. Those are different targets.

Reduced sample complexity on prospectively novel rule families would be a useful later primary endpoint for improved acquisition competence: it asks whether prior development makes the next acquisition more efficient. It remains vulnerable to privileged schemas, increasingly easy families, hidden-answer feedback, and native model knowledge. This routing experiment does not supply that endpoint merely by using fewer retries on familiar signatures.

**OBSERVED — negative evidence stays in the record.** The prior audit's recount of [Architecture A trial results](/Users/richietate/Desktop/FeralEcho/app/experiments/architecture_a_hot_stove_proof/trial_results.jsonl) found 5/6 sandbox successes in both control and experience conditions, repeated on one mined problem with a redundant diagnosis. This is a narrow observed null, not proof of universal impossibility or equivalence. Historical F2 failures' recurring structure does not establish successful repair transfer, especially where historical failed candidate source was not preserved. Improved artifact logging cannot recover the missing past or establish that preserved experience will help.

## 14. Singularity Archaeology ladder

**PROPOSED thought experiment.** Read this table backward from the hypothetical endpoint. Each transition has a concrete requirement; every lower rung admits a system that will never reach the next one. These are necessary distinctions, not a prediction or an engineering roadmap. “State” can be software, models, policies, or representations; it need not be foundation-model weights.

| Transition toward the endpoint | Mechanism, necessary input, and retained change | Observable consequence / falsification test | Counterexample possessing lower rungs |
|---|---|---|---|
| Repeated bounded growth → sustained expansion of the competence frontier | Generation of useful harder problems plus access to trustworthy external constraints; acquisition/search mechanisms able to add new solution classes; validated retained changes | Continued success on independently chosen new problem classes under explicit resource accounting; repeated saturation or evaluator exploitation defeats the stronger claim | A learner improves forever only because a benchmark generator renames easy tasks or chases a gameable score |
| Improved acquisition → useful autonomous curriculum | A calibrated model of its limitations proposes attainable informative challenges; independent validation rejects trivial, impossible, or irrelevant tasks; curriculum state changes | Chosen tasks improve later external performance more efficiently than matched fixed/random curricula | A good learner given human tasks cannot identify which problems are useful or independently validate its own generated benchmarks |
| Reusable knowledge → improved acquisition mechanism | Prior experience changes hypothesis proposals, search priorities, representations, or update procedures; new-family evidence and fair cost accounting | Lower evidence/compute requirement on prospectively withheld families under a state intervention | A growing library solves more known compositions but learns each genuinely new relation no faster |
| Retained procedures → reusable abstraction construction | A mechanism proposes latent relations/compositions beyond fixed signatures and validates them against discriminating examples; a representation changes | New representation supports correctly predicted behavior on withheld structural relations; ablation/substitution removes the benefit | An indefinitely growing exact rule library memorizes every encountered family but cannot form a new relation |
| One useful acquisition → repeated acquisition without losing prior value | Credit assignment, validation, retention, and interference control across cycles; old and new task evidence | Successive retained gains plus controlled retesting of earlier capabilities | A recency policy always improves the latest family while erasing the previous one |
| Useful outcome-conditioned selection → acquisition beyond a fixed action menu | A search/induction mechanism proposes a genuinely new useful procedure, validates it independently, and makes it available later | Solves cases no permitted old strategy/sequence could solve at the same budget; benefit follows the new retained procedure | A perfectly calibrated router always chooses the best existing solver but cannot create a missing one |
| Existing state/selection machinery → causally useful retained outcome-conditioned selection | Correct actor attribution and independent task outcomes update declared state, survive a boundary, change selection, and improve later performance beyond competent frozen controls | Paired history and state interventions show post-boundary correctness benefit at matched resources; no effect, invalid oracle, or hidden history defeats it | A system stores experiences, changes scores, and routes differently but optimizes heuristics, counter values, or evaluator exploits |
| Existing logs/persistence → identified behavioral consequence | Mechanically bound write/load/read/action records plus controlled state substitution | Same present task changes action under the declared state change; no action effect defeats it | A rich memory archive is never consulted, or is consulted without affecting a decision |

**OBSERVED — intersection with FeralEcho today.** The source contains persistent state, history-to-prompt paths, score consumers, exploration, and executable generation/evaluation machinery. The earlier investigation also identified some consequential state paths. This does not make all independently verified outcomes well attributed or show improved prospective task correctness. Source capability, a synthetic state perturbation, and a real beneficial acquisition history are separate evidence levels.

**INFERRED.** Frozen foundation models do not prohibit learning at the system level. They do impose no automatic mechanism for any of the higher transitions. Conversely, changing model weights would not itself supply trustworthy evaluation, credit assignment, or useful curriculum construction. Every upward arrow requires its own causal evidence.

This is a decomposition of the proposed route, not proof that success on fixed-portfolio routing is necessary for every possible learning architecture. A system could acquire new procedures directly while having little useful choice among its existing strategies. The late design's assertion that a system unable to do this routing experiment “certainly cannot do more” is too strong. Failure here would constrain this mechanism, menu, and workload; it would not establish a universal impossibility theorem.

## 15. First unsupported arrow

**INFERRED:** correctly attributed, independently verified experience → a retained selection change that causes better later task correctness at matched cost beyond competent frozen routing.

There are partial pieces on both sides: persistence, reads, updates, and changed decisions are technically possible. Their useful causal composition has not been demonstrated. The current evaluator boundary blocks accepting the “independently verified correctness” premise for an adversarial candidate. Historical proxy scores, F2 importability, council agreement, or logging cannot bridge it.

Do not build a curriculum generator, VRM, learner self-modification, or an abstraction engine to leap over this arrow. The immediate decision is whether a small, valid isolated measurement can establish it at all. A null or an inability to qualify the measurement is informative.

## 16. Strongest skeptical interpretation

**INFERRED — skeptical review compatible with beautiful numbers:**

> The study demonstrates, at most, calibration of a fixed solver portfolio on a small authored template ecology. Its “novel” tasks reuse generator structure, recognizable wrappers, and native programming skills. A persistent signature table can select better pretrained behavior without developing any new abstraction or acquisition ability. The comparator may have been fitted to a different difficulty mix or selected poorly. Restarting a client does not isolate historical error prompts, classifier state, reflected scores, caches, or backend state. Logged updates and hashes do not establish that evaluated outcome content caused the improvement. Most seriously, the proposed hidden evaluator places expected answers in the candidate's own runtime module and returns failure diagnostics containing expected values. Higher hidden-test pass rates therefore need not mean higher task correctness. The reported causal interventions could identify a persistent route to a measurement exploit. Until these alternatives are excluded, “FeralEcho learned persistently and improved on novel tasks” is underspecified and potentially misleading; reusable accumulated competence is unsupported.

This criticism does not claim that finite routing adaptation is worthless or that an exploit actually occurred. It identifies what the proposed evidence would fail to distinguish.

## 17. Evidence required to defeat it

**PROPOSED.** The skeptical review is defeasible for the bounded routing claim, subject to the following evidence:

1. **Qualified correctness:** trusted expected values and comparison outside candidate control, hostile-candidate qualification, adequate contract coverage, and a sealed final evaluation channel. A nonce and mutation score are insufficient.
2. **Exact actor/artifact binding:** capture the generation-time backend identity and actual response; bind extracted code and every transformation/repair to their parent hashes; evaluate that resulting artifact. A selected/requested/logged model name is insufficient. For council synthesis, credit the composite strategy with its candidate and synthesis graph, not a single selected model. The current `generate_code_from_plan()` attribution limitation must be excluded from the experimental path rather than assumed repaired.
3. **Closed state boundary:** demonstrate that the declared checkpoint is the only retained experimental history reaching later decisions. Log actual present-task features, consumed state, action probabilities/choices, prompts, and all external reads allowed by the design. Candidate preservation alone supplies none of this causal guarantee.
4. **Content-sensitive causal intervention:** match record count, eligibility, schedule, and resources while changing the evaluated feedback content; replay descendants for a total-history claim. Couple choice randomness and distinguish decision effects from incidental RNG divergence.
5. **Post-boundary value:** locked-state evaluation after restoration, paired with the identical update-disabled twin and a competent frozen champion, using genuinely unqueried task lineages and independent history replication.
6. **Complete accounting:** include all histories, failed attempts, empty/length-terminated outputs, retries, exclusions, model changes, researcher interventions, and costs under a frozen analysis.

If these conditions hold and the effect is precise and useful, I would accept persistent experience-dependent improvement of this bounded routing policy. A task-signature table would then be an admissible explanation of the mechanism, not a refutation of that limited result.

**UNKNOWN.** Whether the local strategies possess enough reliable correctness and complementary strengths for a useful effect is not established by this design review. Existing 7B-class failures and Architecture A's null make that a real possibility, not a detail to explain away.

No feasible outcome of this one bounded routing experiment defeats the broader criticism that it has not demonstrated new abstractions, improved acquisition competence, or open-ended cumulative growth. Those claims require different later evidence. Do not demand impossible proof for the small claim or use success on the small claim as proof of the large one.

## 18. Remaining blockers

**OBSERVED / UNKNOWN — blockers at this review boundary:**

- The proposed unmodified oracle exposes expected answers to candidate execution; failure output also exposes them to potential downstream consumers.
- Generation-jail protection is narrower than its docstring, and does not describe the grader's actual access boundary.
- The prospective task contract, available convention information, action menu, permissible feedback, cost envelope, and actual actor binding are not yet a frozen qualified experimental specification.
- Existing AP-0 qualification is incomplete. A fresh seed does not repair that or establish new structural families.
- Literal partition disjointness and lineage novelty are not guaranteed by the current generator interface.
- Complete state ownership, loading, history exclusion, intervention semantics, and twin coupling remain proposed controls rather than demonstrated properties of the new experiment.
- There is no demonstrated competent frozen champion for the final workload. The late design supplies a partial analysis plan, but not a justified final number of independent histories or a complete frozen joint success rule.
- The intended transfer and accumulation claims remain broader than the distances this substrate directly supplies.

These are blockers to interpreting the experiment, not requests to repair production or rerun AP-0 qualification. The report does not establish that all require expensive new infrastructure; it establishes that calling them already solved would be false.

The late design reduces several omissions to specified-but-unqualified controls. It does not close the grader boundary, convention-information gap, fixed-trace/full-rollout contradiction, client telemetry/seed/fallback mismatch, or denominator problem. Resolving its circuit-breaker UNKNOWN therefore does not make implementation ready.

## 19. Minimum design changes

**PROPOSED — conditions for a later authorization decision, not authorization now:**

1. Withdraw the assertion that unmodified `oracle_runner.grade()` is qualified for adversarial hidden correctness. Specify a trusted expected-answer/comparison boundary and a bounded hostile-candidate qualification requirement for the isolated experiment. Keep production and AP-0 untouched.
2. Define one falsifiable bounded routing claim and an explicit information/cost contract. Decide how convention information reaches all arms. Require a generation interface that actually enforces the stated seed, request, fallback, actor and telemetry contract. Treat existing AP-0 material as development; freeze novelty and actual partition checks instead of relying on seed names.
3. Restrict retained experimental influence to a small declared policy state and freeze features, workers, strategies, prompt assembly, and environment access. Exclude ambient historical error, reflection, retrieval, and council-learning channels from the causal path unless they are explicitly the treatment.
4. Require the identical update-disabled twin, a credibly development-selected frozen contextual champion, correctly bound actors/artifacts, and count-matched feedback interventions. Specify full-state restoration and downstream replay semantics before building the harness. Choose explicitly between fixed-trace update sensitivity and a full counterfactual rollout; the late design currently claims both from one incompatible procedure.
5. Make independent paired histories the replication unit; predeclare one post-restart correctness endpoint, resources, sample-size justification, stopping/exclusion rules, and the exact success/claim boundaries. Do not optimize for a positive deadline result.

These changes narrow the experiment to a testable first arrow. They do not add a new learning mechanism, turn logging into retrieval, or prescribe implementation of higher developmental rungs.

## 20. Final recommendation

**PROPOSED — stop before implementation.** The next action should be a written evaluator-boundary qualification specification for the isolated experiment, centered on the same-module expected-answer counterexample. Until the expected-answer and trusted-comparison boundary is resolved, better provenance and stronger statistics would only make a potentially invalid score more convincingly attributable.

Keep the rest of the decision conditional. A valid positive would be useful bounded adaptation; a valid null would show that this policy/menu/workload did not yield a measured benefit under the stated budget. Neither outcome licenses an accumulated-competence narrative without additional evidence. The new Claude findings **REFINE** the previous conclusions: the strongest reason is that they establish more about available historical artifacts and prompt influence, while still supplying no causal demonstration of improved independently measured later competence.

**OBSERVED — inspection fingerprints.** The following hashes identify particularly load-bearing source, with entry fingerprints for the first four and during-inspection fingerprints for the remaining three:

| File | SHA-256 |
|---|---|
| `app/experiments/accumulation_probe/oracle_runner.py` | `12a6420959ce8a55222397e9bbba285c64242a90f4637302c3a2275dc1169c75` |
| `app/experiments/accumulation_probe/jail.py` | `044f9d80379f7931de6e12d682540c92845f7901a3b056b3d35a8e4dc25a6501` |
| `app/experiments/accumulation_probe/tasks_v2.py` | `b2229e9f3ab6cff3f827305106d6525a0992ac68fd4d484ab6952f7f3bfa9702` |
| `app/experiments/accumulation_probe/worlds.py` | `9d495f967808ff8a175794ed8373f161f6703c45289015f97aff1f7df214c56f` |
| `app/experiments/accumulation_probe/tasks.py` | `e73d790cdb7fa494db84cc22dc0a16250e35f7d6907e9ac27ef6562fbe73ea38` |
| `sandbox/safe_exec_wrapper.py` | `7605102d2eb0b9a25c6e5e2704a1efff849a06743334160c4e92a84b170f8cc7` |
| `audits/2026-09-22_task_correctness_evaluator_qualification.md` | `6df015dc8dd4446a7026073f7a07d0805162e6a9ad314c787641ccbf7e1b293b` |

**OBSERVED — closing integrity verification, 2026-09-23 11:47:30 UTC.** HEAD remained `2fba42644c82b9f7096276f4dd338d615cf1bcce`. All 22 source/report fingerprints matched their recorded inspection baselines. Porcelain-v2 status still contained the same 28 tracked modifications and no staged changes; untracked files increased from 276 to 278. The only added status entries were this report and `audits/2026-09-22_preregistered_persistent_routing_experiment_design.md`, which appeared independently during the review and was not created or edited by me. No pre-existing status entry disappeared or changed. The late design still matched its inspected SHA-256 on resumption. This is a scoped file/status integrity check, not a claim to have measured every byte of live runtime state. Additional source inspected for the late client trace was `app/core/river_deliberation.py` (SHA-256 `5d1aa77911509ebbc90d01cd084e5ac3b4c8bd7b9790bc2780b5ce226c253585`) and `app/ollama_handler.py` (`7b926934abcde70b388e7366ad31e5e3916a833376372f86c37946c99901cadd`), fingerprinted on resumption rather than at entry.

Only file created: `audits/2026-09-22_persistent_learning_experiment_premortem.md`. Existing reports were not overwritten. No production or experiment code/configuration was edited; no Git state-changing operation was performed; no model call, trial, new dataset, verification suite, constructor retry, or Stage 1 run was performed. No candidate logger change or candidate retrieval mechanism was introduced.

Statuses below apply to the proposed experiment as currently evidenced. **CONDITIONAL** means an identifiable conceptual control exists but has not been qualified in an implemented harness; it does not grant authorization. **NOT QUALIFIED** denotes a concrete failure or missing evidence necessary for the stated claim.

**AP-0 TASK SUBSTRATE:** NOT QUALIFIED

**EVALUATOR INDEPENDENCE:** NOT QUALIFIED

**INFLUENCE INTERVENTIONS:** CONDITIONAL

**UPDATE-DISABLED TWIN:** CONDITIONAL

**FROZEN CONTEXTUAL CHAMPION:** CONDITIONAL

**STATISTICAL IDENTIFIABILITY:** NOT QUALIFIED

**TRANSFER CLAIM:** NOT QUALIFIED

**FIRST UNSUPPORTED ARROW:** Independently verified, correctly attributed experience causes retained selection changes that improve later correctness beyond competent frozen routing at matched cost.

**READY FOR IMPLEMENTATION:** NO

1. **If the experiment returned its best imaginable result, what is the strongest claim I would accept?** After the qualifications above, retained evaluated experience improved this fixed strategy portfolio's post-restart task performance over its update-disabled twin and specified competent frozen contextual comparator on the preregistered distribution and budget: a bounded instance of system-level routing adaptation.

2. **What weaker mechanism could most plausibly impersonate that result?** A persistent task-signature success table that calibrates access to already capable pretrained strategies, saturates within a fixed repertoire, and never improves abstraction or acquisition. It can produce the entire legitimate bounded result; the impersonation occurs when that result is described as broader accumulated competence. Under the current evaluator, learning to select answer-reading artifacts is also a concrete route to invalid apparent correctness.

3. **What single control or intervention matters most for distinguishing them?** For the bounded causal claim, complete-boundary retained-state substitution against the identical update-disabled twin on unqueried held-out task lineages, evaluated by a qualified external oracle. This distinguishes useful retained-state influence from ambient history and native capability. It cannot distinguish finite-table adaptation from the bounded claim because the table is a valid instance of that claim. Distinguishing it from reusable abstraction would require a separate structural-generalization test against an equally informed adaptive signature-table comparator; that stronger experiment is not authorized or proposed for implementation here.

4. **What first developmental transition remains unsupported?** From existing persistence, feedback, and routing machinery to a demonstrated causal improvement in later independently verified task correctness attributable to retained evaluated experience under fair frozen controls—not yet from routing adaptation to open-ended self-improvement.
