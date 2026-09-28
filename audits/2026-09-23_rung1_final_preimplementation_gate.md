# Rung-1 bounded persistent routing learning: final pre-implementation gate

Date: 2026-09-23. Author: Codex. Read-only engineering/scientific qualification; only this report is an authorized write. No apparatus, evaluator repair, trial, model call, or AP-0 Stage 1 was run or implemented.

**OBSERVED — entry integrity.** At 2026-09-23 12:17:07 UTC, HEAD was `2fba42644c82b9f7096276f4dd338d615cf1bcce`. Porcelain-v2 status contained 28 modified tracked files and 280 untracked files, with no staged changes. Seventeen source/report files were fingerprinted at entry; six additional report/result files were fingerprinted during inspection. The requested output did not exist. Closing verification is in §24. No repository modules were imported, no verification code was executed, and no sealed Stage 1 material was opened.

Labels: **OBSERVED** identifies inspected source or existing artifacts; **INFERRED** identifies conclusions drawn from them; **PROPOSED** identifies a specification, not an implemented property; **UNKNOWN** identifies a remaining empirical or engineering uncertainty.

## 1. Executive verdict

**INFERRED — ENGINEERING-GATE.** Rung 1 is an identifiable, useful, deliberately bounded scientific target. The remaining work is principally a small isolated apparatus and concrete qualification of its boundaries. Another broad learning thought experiment is unlikely to resolve more than building and attacking that apparatus would. This is not implementation authorization.

The existing evaluator and generation path are not qualified as-is. The reconciliation fixes the replay interpretation on paper but overstates the sufficiency of a process boundary and of switching to `stream_query_ollama()`. Expected-answer files must also be inaccessible; output must cross as constrained data; the lower-level generation helper still lacks the complete experimental request/telemetry contract.

**Do not add a fourth template-only arm to the minimum Rung-1 experiment.** A competent template router is a required candidate in selecting the frozen contextual champion. An identical frozen twin already shares the adaptive selector's engineered representation. Denying an additional comparator task information available to the adaptive worker would confound information availability with learning. Experience-derived routing through a fixed coarse representation is legitimate Rung 1, including when its benefit extends to S tasks; it is not convention induction or abstraction construction.

**A persistent outcome-updated table can satisfy Rung 1.** It need not improve its update rule, generate a procedure, or change model weights. Success requires an actual beneficial causal path from evaluated experience through retained state, under the declared controls. Neither simplicity nor lack of novelty in the underlying learning algorithm is a disqualification.

The first authorized engineering increment, if permission is later given, should establish the isolated evaluator's trust boundary and generation interface before assembling or running the learning experiment. Production, RiverBrain, the self-edit ledger, and AP-0 need no changes.

## 2. Evidence reconciled

The two September 23 reports were read in full. The earlier design and pre-mortem were already read in this continuing investigation; their current hashes match the versions reviewed. Important claims were rechecked against current source, rather than accepted because reviewers agreed.

| Evidence | Reconciled finding |
|---|---|
| [Original routing design](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_preregistered_persistent_routing_experiment_design.md) | Useful standalone three-condition architecture and history-level analysis. Its unmodified grader, ambiguous replay, information contract, client assumptions, and exclusion rules cannot be inherited unchanged |
| [Pre-mortem](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_persistent_learning_experiment_premortem.md) | Same-module oracle access and client defects survive independent source checks. Its finite-table explanation limits higher claims but does not defeat Rung 1. This gate resolves previously open design choices rather than repeating the audit |
| [Trusted-boundary reconciliation](/Users/richietate/Desktop/FeralEcho/audits/2026-09-23_trusted_boundary_reconciliation.md) | Correctly retracts evaluator qualification, separates mechanistic replay from online rollout, and accepts the NEAR/UNREL corrections. Process separation alone and its proposed client substitution remain insufficient (§8, §10) |
| [Adversarial Learner Game](/Users/richietate/Desktop/FeralEcho/audits/2026-09-23_adversarial_learner_game.md) | Correct that a causally beneficial persistent table satisfies Rung 1. Incorrect to require convention learning for bounded S-routing transfer; the proposed information-denied comparator does not identify that mechanism. “Every counterfeit is closed” is a conditional argument, not a security proof |
| [Candidate logging qualification](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_self_edit_candidate_logging_qualification.md) and [implementation report](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_self_edit_candidate_logging_implementation.md) | Preserved initial/retry source supports artifact provenance. The current source still reads only `initial_f2_error` into targeted generation. The ledger is not wholly write-only; candidate source is not currently consumed by that path |
| AP-0 qualification artifacts | [Primary](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/results/primary/summary.json): GOLD 10/12, K2 2/4, gate unqualified. [Post-hoc auditor](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/results/posthoc_auditor_v2/summary.json): K1 partially qualified; K2/K3 not qualified; gate still unqualified. [QB](/Users/richietate/Desktop/FeralEcho/memory/experiments/accumulation_probe/v2/qual/results/qb/summary.json): K2 and K3 each 0/6 exact; respectively one and five empty, length-terminated drafts. These are existing results, not new regrading |
| [Previous strategy-selection attack](/Users/richietate/Desktop/FeralEcho/audits/2026-09-22_codex_adversarial_attack_on_reconciled_roadmap.md) | Production repair is unnecessary for the isolated experiment. F2 is not a task-correctness oracle; selected-model labels are not actor provenance. The Architecture A null is narrow evidence against one redundant retry-prompt intervention, not a prohibition on routing adaptation |

**OBSERVED.** [oracle_runner.py:45](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/oracle_runner.py:45) concatenates candidate and tests; [tasks.py:246](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks.py:246) places `_CASES` and expected values in that module and prints failing expected values. [jail.py:6](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/jail.py:6) denies reads within the experiment root except the arm root, not across the general filesystem. [echo_sandbox.sb:25](/Users/richietate/Desktop/FeralEcho/sandbox/echo_sandbox.sb:25) permits all file reads. These findings require no exploit execution.

**INFERRED — corrections to earlier interpretations.** Fresh pseudo-words do not prove training-set absence or seed secrecy. Distinct PRNG streams do not guarantee disjoint inputs. An exact task signature can be recovered from prompt morphology even without internal task IDs. Higher NEAR correctness can be appropriate override following; higher UNREL correctness can be useful general routing calibration. Neither is automatically a confound. A frozen feature map is not a learned abstraction.

**UNKNOWN.** Whether the selected local model and prompt strategies offer a sufficiently reliable, context-dependent routing opportunity remains empirical. AP-0 constructor/gate failures make this a real development qualification question. They do not logically block a different, fully specified routing workload, nor must AP-0 Stage 1 succeed first.

## 3. Final bounded claim

**PROPOSED.** Prospectively evaluated task outcomes cause retained changes in a fixed selector that survive a real process boundary, change later strategy selection, and improve independently graded hidden-task correctness beyond a competent development-selected frozen contextual policy and an identical update-disabled twin, under a preregistered matched final-inference-cost contract.

The claim is about this isolated FeralEcho research component, fixed model/strategy menu, specified task distribution, and tested cost range. It is not automatically a claim about live Echo's production behavior. Acquisition cost is reported separately.

The smallest coherent workload resolves a gap left in the prior design: **give every worker the same complete current-task specification, including whatever local convention is necessary to solve it.** Reuse appropriate AP-0 task-generation/reference ideas in an isolated adapter; do not edit AP-0 or access its sealed holdout. Hidden evaluation inputs and expected outputs remain protected. This is ordinary hidden-test evaluation of specified functions, not an induction test with essential instructions withheld.

This prospective choice deliberately removes hidden-convention acquisition from the experiment. It preserves the user's Rung-1 claim, which concerns learning which available strategy works. If convention induction is later desired, it needs a different information contract; it must not enter accidentally through richer adaptive-arm prompts.

**PROPOSED — minimum mechanism.** Use two fixed single-call prompt strategies on one pinned local model, with no retries or tools. Choose their actual content using development evidence and freeze it. A small count/success table indexed by a fixed coarse task feature bucket and strategy is sufficient. Fixed priors, score formula, exploration, tie-breaking, and fallback complete the policy. The selector never generates prompts, reads candidate source, retrieves history, or modifies its features. If development cannot demonstrate a meaningful routing opportunity, report that qualification failure rather than upgrading models or multiplying strategies to chase a result.

Use a fixed weighting of later T/S-style tasks as the Rung-1 primary distribution; S-specific benefit is a separately prespecified secondary claim. This is an explicit prospective revision of the earlier S-only success rule. Rung 1 does not require structural-transfer superiority. Do not switch between these endpoints after observing results.

## 4. Explicitly excluded claims

**PROPOSED — hard interpretation boundary.** A positive result establishes none of the following: new procedure acquisition; new abstractions; model-weight learning; general learning; learning-to-learn; autonomous curriculum creation; repeated open-ended accumulation; learner self-modification; recursive self-improvement; AGI; or singularity.

Model-native skill, a human-designed feature map, prompt elicitation, and a fixed update algorithm may all contribute to a legitimate Rung-1 result. The causal change being tested is the selector's use of evaluated experience, not the origin of every capability used by its workers.

Repeated behavior, recognized recurrence, available evidence, consulted evidence, state change, changed action, durable persistence, and improved correctness remain separate findings. The full Rung-1 verdict requires their relevant causal composition, not any one proxy.

## 5. Required experimental arms

| Condition | Required role | Information and updates |
|---|---|---|
| A — frozen contextual champion | REQUIRED comparator role | Best credible development-selected non-updating policy; legitimate present-task features and identical worker specifications/menu; no prospective reward updates or rolling history |
| B — update-disabled twin | REQUIRED comparator role | Same selector code and exact development state S0 as C; prospective outcomes cannot mutate any decision-relevant state |
| C — adaptive selector | REQUIRED treatment | Same S0 and interfaces; only the declared outcome-based table updates differ |
| D — separate template-only arm | UNNECESSARY for this minimum experiment | Include its strongest fair version among A's development candidates; do not pay for a redundant, information-disadvantaged confirmatory arm |

**PROPOSED — champion selection.** Compare competent structural rules, a frozen template-to-strategy table, a small regularized contextual policy if development supports it, the frozen twin, and constant strategies. Fit on development training, choose using separate development validation split by world/task lineage, and freeze the selection rule and winner. Permit present-time morphology, syntax, length, representation, and fully public task information consistently across candidates. Give the twin/adaptive feature representation the same available structural information; engineered representation richness must not be exclusive to C.

A and B may coincide. If the development-frozen twin wins, one physical comparator can serve both roles. If two policies select the same action for the same task and assigned generation replicate, one controller-owned generated artifact/evaluation can serve both with explicit provenance; that is paired measurement, not a learner-visible cache. Never count it as independent evidence twice.

The champion is the best of a disclosed feasible development competition, not an omniscient optimum over all possible static programs. Its uncertainty and limitations must remain visible. A lack of credible development selection is a qualification failure, not grounds for substituting a weaker convenient baseline.

## 6. Causal chain

**PROPOSED — the controller owns evidence collection.** Selector self-reports are not authoritative. Hashes identify recoverable bytes; they do not prove the truth of an execution claim.

| Link | Minimum record | Causal or engineering check |
|---|---|---|
| E occurred | Episode, task lineage/contract, actual request/response and extracted artifact hashes, backend identity, trusted outcome | Independent artifact evaluation; reject an outcome not bound to the evaluated artifact |
| E eligible → U | Eligibility rule/version, episode-to-update link, exactly-once status | Controller enforces eligibility and reconstructs the update independently |
| U → S0/S1 | Pre/post canonical state, or recoverable base plus deltas; update formula/version | True-label replay reproduces recorded state; controlled label substitutions test content dependence |
| S1 → durable checkpoint | Atomic checkpoint identity, completion acknowledgement, loadable schema/version | Exit producer; fresh consumer reads committed bytes rather than an inherited object or surviving writer |
| Loaded S1 → D | Loaded semantic state, feature vector, menu, choice randomness, scores/probabilities and selected action | Substitute S0/S1 under identical permitted inputs; distinguish score, probability, and action effects |
| D → generated candidate | Strategy/prompt hashes, actual backend response association, extraction/transformation chain | No mismatch between selected label and generator; no unlogged repair/fallback |
| Candidate → O | Trusted evaluator contract/version, hidden cases, constrained observed outputs, outcome and costs | Expected answers remain outside candidate control; outcome is not a printed pass marker |
| Retained state → useful O | Locked final policy evaluated on untouched later tasks | Paired C–B and C–A comparisons across independent histories plus matched state-intervention comparisons |

**Mechanistic intervention.** Replaying a fixed real sequence of features, chosen strategies, and artifacts with substituted reward bits is well defined. Keep actions fixed; recompute all updates from S0. SHAM-REVERSED can show label sensitivity even though its labels are deliberately false. It is not a naturally acquired alternative history, and its poisoning effect alone does not show ecological improvement.

Use a count-preserving feedback-content intervention as the stronger diagnostic: a prespecified permutation of labels across the recorded eligible context/action events, preserving episode count and overall reward count while disrupting the useful outcome association. Permuting only within a bucket whose update uses unordered counts would leave that table unchanged and test nothing. Record the permutation independently; do not select a damaging permutation after seeing results. The true replay must reproduce the real S1. If the update uses randomness, replay that stream too; a deterministic count update avoids it.

**INFERRED — one remaining causal trap.** A system can put label-dependent checksums in its state while a separate episode counter or schedule causes all useful action changes. Showing checksum sensitivity plus C>B does not connect the feedback content to the benefit. Trace which state fields actually enter action values and link the content intervention to decisions and their independently measured utility. Prespecify diagnostic checkpoint comparisons on a held-out diagnostic block; do not claim a feedback-caused benefit solely because one artificial reversed-label policy was badly poisoned. A degenerate label stream or insufficient precision yields unresolved mechanistic evidence, not a forced success.

**Ecological comparison.** C's real prospective choices produce its real independently evaluated experience. C's post-boundary value is compared with B and A on the same later tasks. That is the natural-history question. A full online SHAM rollout is unnecessary for this minimum experiment. Fixed-trace intervention results remain explicitly conditional on the recorded action sequence.

## 7. Complete state manifest

**PROPOSED.** Minimize the state rather than trying to snapshot production. A selection decision must be reconstructible as a function of the current allowed feature vector, declared policy state, immutable configuration, and assigned choice random input.

| Component | Classification and contents |
|---|---|
| Retained selector state | **EXPERIMENTALLY VARIED:** per-bucket/per-strategy trial and success counts, plus any decision-relevant update index; S0/S1 schema and canonical encoding |
| Update deduplication | Controller-owned episode set and ordered event ledger; never a selector feature; reconstructed consistently during replay |
| Scoring and routing | **IMMUTABLE:** prior/pseudocounts, score formula, exploration rule, tie-breaking, unknown-bucket fallback, strategy availability |
| Features and task mapping | **IMMUTABLE:** extractor source/version, vocabulary/bucketing, schema and allowed input contract; explicit T/S bucket sharing rather than accidental function-ID routing |
| Normalizers/classifiers | **EXCLUDED** in the minimal discrete-table selector; if added, they become declared state and reopen qualification |
| Choice randomness | **EXPLICITLY RANDOMIZED:** controller-assigned named stream, coupled within paired decisions; not advanced by logging, update work, or another arm |
| Task draw/order randomness | **EXPLICITLY RANDOMIZED:** separate controller stream; task order fixed independently of policy success |
| Generation randomness | **EXPLICITLY RANDOMIZED:** separate task/action/replicate stream, pinned in actual request; backend nondeterminism measured rather than denied |
| Model and strategy menu | **IMMUTABLE:** weights/digest, model configuration, runtime version, strategy prompts, request options, extraction rule, resource limits |
| Current worker task packet | **IDENTICAL ACROSS ARMS:** full public specification and convention; no retained examples or error text beyond the chosen fixed strategy |
| Memory/retrieval/council/RiverBrain | **EXCLUDED:** no production imports, live logs, FAISS, self-edit state, classifier training, or conversational history |
| Caches and backend state | Semantic/session/response histories **EXCLUDED**; operational cache policy **IDENTICAL ACROSS ARMS**, with arm execution order randomized and load measured |
| Time, paths, process/arm IDs | **EXCLUDED** from policy inputs and worker prompts; opaque controller IDs used only to bind records |
| Oracle, future draws, expected outputs | **EXCLUDED** from selector/worker/candidate access; trusted evaluator only |

A checkpoint hash need not contain immutable model files, but its manifest must bind their identities. Conversely, a hash of the table alone cannot certify this whole boundary. Restore all decision-relevant state, not merely the field named `mean`. A fresh process is the required persistence boundary; a fresh LLM server is only required if its state cannot otherwise be kept irrelevant and controlled.

For the count-table minimum, the controller can recompute the entire learned state from validated events without trusting a learner-authored account. This materially reduces the scope of influence-provenance qualification.

## 8. Trusted evaluator boundary

**OBSERVED.** The present candidate can reference `_CASES` after the test module initializes it. A legitimate matching return triggers the legitimate nonce marker. The nonce does not stop this. Removing `_CASES` from that namespace is necessary but not sufficient if its contents remain readable elsewhere.

**INFERRED — necessary property.** Expected outputs, oracle secrets, and authoritative comparison must be outside the untrusted candidate's addressable state. Separate OS processes are the smallest suitable mechanism for unrestricted Python here; an equivalently enforced restricted interpreter could also satisfy the property. Merely different dictionaries or variable names cannot.

**PROPOSED — minimum evaluator component, isolated from AP-0:**

1. A trusted controller owns frozen case data and expected values. It launches a freshly executed sandboxed candidate worker for each test input, providing only candidate source, the permitted function contract, and that input through a constrained channel. No test-authoring code, expected output, world seed, outcome, or prior case result enters the child.
2. The child may return only a bounded serialized value under the declared task schema. Parse data, never `eval`, pickle, import returned code, or compare a candidate-supplied Python object in the trusted process. Define exact types, integer/bool distinction, tuple/list encoding, map keys, numeric limits, duplicate-key behavior and size/depth limits. Reject malformed/multiple protocol messages and nonpermitted values. Candidate-printed `PASS` is just untrusted text.
3. The controller compares its own parsed primitive data with its own expected value after execution. No candidate-controlled equality methods execute there. Bind the result to the input and exact candidate artifact. The controller alone computes suite PASS/FAIL and writes the authoritative ledger.
4. The sandbox must deny access to protected artifacts, researcher diagnostics, controller state/memory, other candidates, and experiment history even when filenames and source are known. Use an explicit read allowlist for minimal interpreter dependencies and that candidate's scratch inputs. Deny network and unauthorized process/IPC/debug access; sanitize environment and inherited file descriptors. Fresh execution avoids inheriting the controller's Python heap. An answer left in a readable temporary file or inherited descriptor defeats separation.
5. Enforce bounded CPU/runtime, memory, output, and process resources. Timeout, invalid output, crash, and forbidden access are task failures under the declared execution contract. Infrastructure failure is established by trusted launch/controller evidence, not by candidate stderr saying `sandbox_apply`.

This is a new research evaluator adapter/profile, not an edit of `oracle_runner.py`, `safe_exec_wrapper.py`, or the production sandbox. Existing launch patterns and reference functions can inform it; the broad read profile cannot be reused as if it provided confidentiality. A namespace-only repair, one new subprocess without access restrictions, or stripping stdout tails alone fails qualification.

**Perfect-information requirement.** The attacker may know source, protocol, filenames, scorer, strategies, and thresholds. Security relies on denied capabilities and protected data, not obscure names. It may compute the right result from the permitted specification/input; that is valid correctness. It must not fetch the protected expected answer, impersonate the controller, or execute code in the comparator. The trusted OS, interpreter, controller, and reference contract are explicit assumptions; this is not a proof against unknown kernel vulnerabilities or a malicious experiment operator.

**UNKNOWN — not yet qualified.** A later hostile-fixture suite must challenge globals/frames, own-source inspection, known oracle paths, path aliases, descriptors/environment, parent-process access, networking, custom comparison/serialization tricks, false markers, output flooding and exception impersonation. Correct references and genuinely wrong candidates must also pass/fail appropriately. Independent expected-value derivations and contract edge cases remain necessary: isolation cannot make a mistaken oracle correct. Finite tests establish correctness under the declared test distribution, not universal program correctness.

## 9. Feedback sanitization

**PROPOSED — field-level contract.** Researcher-visible means preserved privately for authorized audit, not available for iterative holdout tuning. Final-task outcomes remain sealed from every learner and researcher decision process until all confirmatory decisions are locked.

| Field | Classification | Rule |
|---|---|---|
| Training `passed` | **LEARNER_VISIBLE** | One controller-generated Boolean after the attempt is irrevocably complete |
| Current fixed feature bucket and executed strategy | **LEARNER_VISIBLE** | Already-known inputs needed to update the right cell; not evaluator-derived features |
| Episode association | **RESEARCHER_VISIBLE** by default | Controller binds reward to event; if an identifier must cross the API, it is an opaque independent token and cannot enter selection |
| `ran_ok`, timeout, infra class, exception class | **FORBIDDEN_TO_LEARNER** | Researcher-visible administrative evidence; crashes/timeouts collapse to FAIL, genuine infra follows an outcome-blind abort/replacement rule |
| Stdout/stderr, tails, traceback, assertion text, expected/actual values | **FORBIDDEN_TO_LEARNER** | Bounded private diagnostics only |
| Per-case outcomes, counts/reached prefix, partial credit | **FORBIDDEN_TO_LEARNER** | Only the preregistered task-level bit is released |
| Duration, latency, token counts, resource use | **FORBIDDEN_TO_LEARNER** | Controller meters for fairness; these do not become policy features or update weights |
| Seeds, split/world IDs, case filenames, expected-value hashes | **FORBIDDEN_TO_LEARNER** | Private provenance only; low-entropy answer hashes can themselves permit enumeration |
| Request, response, candidate, checkpoint and evaluator hashes | **RESEARCHER_VISIBLE** | Bind recoverable artifacts; do not substitute hashes for preserved evidence |
| Final holdout outcome of any kind | **FORBIDDEN_TO_LEARNER** | No updates, repairs, reselection, or checkpoint changes after seeing it |

The minimal update call contains a fixed feature bucket, executed strategy, and trusted bit. The policy has no clock, filesystem, or telemetry input. That interface also removes timing from the selector's effective observation channel; omitting a `duration` field alone would not if the policy could time callbacks. Candidate and generator processes do not receive prior evaluation diagnostics. Protect the diagnostic store from all experimental consumers.

PASS/FAIL still conveys information, deliberately. Bound training evaluator queries; keep final tasks unqueried and outcome-hidden. Do not say sanitization eliminates learning from the oracle—it limits that learning to the intended reward. Richer feedback is unnecessary for Rung 1 here.

## 10. `_ollama_query()` isolation

**OBSERVED — uncertainty resolved.** [river_deliberation._ollama_query()](/Users/richietate/Desktop/FeralEcho/app/core/river_deliberation.py:397) uses a real [process-global circuit breaker](/Users/richietate/Desktop/FeralEcho/app/core/echo_model_orchestrator.py:1254), keyed by model/task type: three failures, 300-second cooldown. It is not file-persisted, but calls in one process can suppress later calls from another arm. A process restart resets that breaker, not every backend dependency.

The helper has no explicit generation-seed argument, returns text rather than complete call metadata, changes Qwen prompt text, and can fall back to `ollama run` after a streaming exception. That fallback is another call with different system/temperature/token controls. Bare use is not qualified for the proposed no-retry, matched-request experiment.

**OBSERVED — the reconciliation's replacement is incomplete.** [stream_query_ollama()](/Users/richietate/Desktop/FeralEcho/app/ollama_handler.py:421) also has no exposed seed/options parameter; its chat metadata currently supplies `done_reason`, not full accounting. It invokes model-pool patching, supports MLX routing, and for the configured Echo model can use a cached Modelfile identity block. Calling it directly bypasses the breaker but does not satisfy the full contract. Excluding fallback cases after outcomes would also risk selective survival; prevent undeclared fallbacks instead.

**PROPOSED.** Use a small research-owned, single-request HTTP adapter with explicit full request bytes, seed, options, model, timeout, and complete returned metadata, no production imports and no implicit retry/fallback. [AP-0's direct client](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/ollama_client.py) is a useful source pattern: it sends explicit seeds and captures token counts, but its preflight `/api/tags` digest lookup is not independently an attestation of the model that served every later request.

Bind model identity through an immutable/pinned local model artifact or equivalent server configuration, protected from concurrent remapping, plus actual response/request association and runtime version. If the backend does not return a per-call digest, say so and document how pinning establishes identity; do not invent telemetry. Detect model/config changes and invalidate the affected frozen run. Log actual input/output counts and termination. Same seed is a requested sampling control, not a guarantee of bit-identical generation across backend states.

A restricted generation broker may access the model endpoint; candidate execution may not. The model receives only the frozen strategy and current public task. No live Echo machinery needs to be repaired, imported, restarted, or modified.

## 11. Counterfeit Learner attack

**INFERRED — strong attacker.** Grant the adversary all experiment source and criteria, candidate-code control, and knowledge of the fixed strategy set. Deny only protected draws/answers/random assignments and unauthorized access to the trusted controller. Freeze the simple selector implementation before prospective work; it cannot replace itself mid-study or provide its own authoritative evidence.

| Counterfeit | Can win the incomplete design? | Missing protection / interpretation |
|---|---|---|
| Read expected answers from another process's readable files | Yes, despite a repaired namespace | Enforced data-access boundary, not subprocess creation alone |
| Return a forged marker, Python equality object or executable serialization | Yes with a trusting output protocol | Typed bounded data and comparison exclusively in trusted code |
| Recognize B/S0/SHAM filenames or arm flags and deliberately degrade controls | Yes if evaluation mode reaches the mechanism or worker | Opaque uniform invocation, no arm/history flags to selection/generation, same worker implementation; inspect/recompute the small fixed selector |
| Improve on an episode-count schedule while logging label-sensitive dummy fields | Can pass disconnected provenance checks | Hold occurrence/count fixed, trace label-dependent action fields, test their utility; no hidden time/phase route |
| Obtain more tokens, retries or richer error context | Yes | Metered cost rule, no implicit fallback, fixed information contract |
| Learn which benchmark fingerprint predicts an existing solver's success | Yes, with actual outcome updates | If it genuinely improves later hidden correctness under controls, this **is** Rung 1 within that substrate |
| Pure fixed morphology router, never updated | Can beat a weak comparator by chance or design | Strong champion plus identical twin, independent histories; it cannot systematically acquire a C-versus-B state effect from nonexistent updates |
| Change task distribution, discard failures or exploit checkpoint peeking | Yes | Exogenous paired histories, fixed stopping/denominators and sealed final analysis |
| Forge its own E/U/S/D/O narrative | Yes if self-reports are trusted | Controller-bound artifacts, independent state reconstruction and interventions |
| Lucky sampling / a badly selected champion | Always a residual finite-sample possibility | Prospective statistical error control, honest baseline qualification and replication; no claim of logical impossibility |

The strongest current concrete counterfeit remains answer access. After that is closed, the most concerning causal counterfeit is a useful change driven by an undeclared field or schedule, coupled with a separate label-sensitive but behaviorally irrelevant record. A complete small state manifest and content-to-action-to-utility intervention address it directly. Merely adding another prose audit does not.

**INFERRED — game result with its limits.** After these qualified boundaries and fair controls, I find no reliable mechanism that both lacks the stipulated causal phenomenon and nevertheless satisfies every stipulated causal observation. A table that wins because true evaluated experience updates persistent action values and improves later choices has actually satisfied Rung 1. That is an operational conclusion, not a theorem that all future bugs, statistical errors, or deceptive research practices are impossible. The game report's conditional reasoning is sound at this narrower level; its universal “cannot counterfeit” language is too strong before engineering qualification.

## 12. Template-only control judgment

**INFERRED — no separate required arm.** The coarse-template explanation is real, but it attacks the wrong claim when framed as “the selector never learned the hidden convention.” Rung 1 does not require that. Its workers can already solve specified tasks; the selector learns which worker strategy is more reliable. A human-provided coarse representation can carry useful experience across T/S without any newly acquired representation.

There is also a limit to the alleged counterfeit itself. Hold a K1 task's morphology and status token fixed while assigning that token to different categories in two possible worlds. Without convention evidence, the same template recognizer sees the same information but the correct answers differ; it cannot reliably solve both just by recognizing “aggregation.” If a worker receives the convention and already knows how to aggregate, selecting that worker can succeed without the selector learning the convention. That is precisely the routing mechanism allowed here, not a hidden acquisition claim. Structural cues may predict strategy reliability; they do not generally determine an undisclosed random rule.

There are two possible D controls:

| D definition | Receives | Denied | What C>D would mean |
|---|---|---|---|
| Fair frozen template router | Same present-time structural cues; same complete worker task packet, model, prompts, cost envelope and development evidence | Prospective updates, historical reward summaries, hidden test data—just like A/B | C exceeds this particular frozen template mapping; already covered by including it in A's development competition |
| Convention-denied worker/control | Morphology but less task information than C's worker | Necessary current convention information as well as prospective experience | A mixture of information availability and policy effects; does **not** isolate learning or convention induction |

For the fair version, structural signals can include operation shape, representation, syntax, length and present environment constraints. Do not give it internal family/split labels or secret seeds. Do not deliberately coarsen it until it becomes weak. Its workers receive the same full convention as everyone else. Its mapping is frozen before prospective evaluation.

If C uses updated statistics over that same representation to improve S performance, the proper description is **experience-dependent routing benefit on a prespecified structural variation using a fixed feature map**. It is not counterfeited merely because the map recognizes templates. B already contains the same recognition capability. If C does not improve over B, static recognition can explain the performance level and Rung 1 fails.

If an additional frozen D is nevertheless retained diagnostically and C fails to beat it on S, superiority beyond that particular cheap static router is unestablished on S. Indistinguishability does not prove identical mechanisms, and C>D does not prove convention learning: stronger model elicitation, different development estimates, or a more effective mapping can explain it. Effect-size uncertainty and the fairness of D determine the conclusion.

The appropriate correction to the game report is to include competent template routing in the baseline search and bound the S claim. No fourth prospective arm is required. A separate convention-ablation experiment would answer another question and is outside this mission.

## 13. Experimental unit

**INFERRED.** The independent unit is a **paired learning history**, with its own prospective world/task draws, order and random streams, ending in independently sampled later evaluation worlds. Individual candidate calls and final tasks are dependent observations within that history.

Several tasks from one world share conventions and construction. Several runs of one learned checkpoint share its entire acquisition path. Multiple sampling seeds do not turn either into independent histories. Reusing common test worlds across histories adds another dependence; the simplest minimum design avoids it by giving each history pair its own later worlds, while pairing arms within the history.

A shared development-frozen S0/champion permits inference conditional on that fixed development choice. Generalization across development procedures would require additional replication and is not necessary for this bounded experiment.

## 14. Replication design

**PROPOSED — sequence within each history:**

1. Load the same development-frozen S0, menu and feature map. Assign a prospectively generated world/task sequence and order independently of outcomes.
2. Run C on that sequence with the fixed exploration/resource policy; it receives only eligible trusted task-level rewards. B remains at S0; A remains frozen. If B is exercised on the same sequence for operational matching, its own outcomes do not update it. It need not receive fictitious rewards for C's actions.
3. Commit S1, terminate the producer, verify its exit, and load S1 in a fresh isolated consumer. No state is reconstructed from ambient production history.
4. Lock all final policies before revealing final tasks/outcomes. Evaluate C/S1, B/S0, and A on the same within-history held-out tasks under coupled action-specific random assignments and randomized execution order. No final updating.
5. Perform preregistered S0 replacement/S1 restoration and feedback-content diagnostics through uniform invocations. Repeated selector decisions should be exactly reproducible when deterministic; stochastic backend utility is compared with paired uncertainty, not demanded to be byte-identical.

Repeat independently across histories. No adaptive task exposure, selective survival, or moving tasks between phases. New seed names are insufficient: verify actual overlap, world ancestry and template exposure. T/S are predefined structural relations, not post-hoc labels. Fully specified tasks remove the need to infer hidden random conventions; they do not remove the requirement to keep hidden test cases and final outcomes untouched.

**PROPOSED — analysis.** Compute one fixed-weight final correctness score per arm/history. Require positive useful C–B and C–A contrasts with prespecified history-level uncertainty and the cost rule. Predeclare a joint success criterion, effect threshold, fixed history count/stopping rule, exclusions, and any S-specific claim. A requirement that all specified contrasts pass is different from searching for whichever comparison is significant; handle additional claims/checkpoints accordingly.

Pilot sizing needs between-history variance, paired differences, worker sampling variability, action/context coverage, floor/ceiling rates, practical effect threshold, failure rates and costs. Three to five pilot histories may reveal gross feasibility problems but give uncertain variance estimates; use that uncertainty conservatively. Do not choose a numerical confirmatory sample size here without these inputs. Development/pilot tasks and results cannot become confirmatory evidence after tuning.

## 15. Matched-cost contract

**PROPOSED.** Define **matched final-inference cost**, with acquisition and apparatus qualification costs reported separately. Equal maximum token settings alone do not prove equal consumed compute. One pinned model and one generation per task minimize the problem but do not eliminate differences in prompt length or output length.

| Resource | Required treatment |
|---|---|
| Model/generation calls | One allowed call per decision in the minimum menu; no hidden planning, repair, synthesis or fallback calls |
| Input/output tokens | Same context/output limits and declared request contract; record actual prompt/completion usage and termination, including failed calls |
| Strategy evaluations | Only the selected strategy is available to the policy; qualification sweeps and analyst-only counterfactual evaluations are separately metered and never supplied as free learning feedback |
| Retries/tools | Zero retries and no tools in the minimum experiment; any future extension changes every comparator's contract |
| Evaluator calls | Same case contract per candidate; training-query budget fixed; no final feedback or extra adaptive hidden-test probes |
| Retained experience | Same state schema and development initialization for B/C; C's declared additional statistics are the treatment, not an unfairness to remove |
| Retrieval | Excluded; policy reads only its table and current allowed features |
| State reads/update compute | Metered/upper-bounded; discard-only bookkeeping must not change B's features/RNG; no extra model reasoning in the updater |
| Wall-clock/cache | Same operational policy, arm order randomized; timing is not a learner feature; report load and timeouts, especially if deadlines affect correctness |

Freeze a cost metric or resource vector before trials. For an unqualified “matched cost” verdict, require C's improvement without exceeding the preregistered metered cost tolerance relative to the required controls, or use a prespecified cost-standardized comparison. If only equal resource ceilings are established, say “equal resource budgets,” not “equal consumed cost.” Do not pad useless work into controls to hide a compute advantage. If higher correctness requires materially higher test-time expenditure outside the accepted matching rule, the full Rung-1 claim at matched cost is not established.

Acquisition cost is allowed to differ: evaluated experience is not free. Record C's prospective calls/tokens/evaluations/storage and any B/A operational matching work separately. This experiment does not establish equal lifetime compute, better learning efficiency, or an economic break-even point unless separately analyzed.

## 16. Result interpretation matrix

**PROPOSED.** “Beats” means the preregistered useful effect and uncertainty rule pass, not merely a larger point estimate. “Approximately equal” requires precision; ordinary nonsignificance means unresolved advantage, not proven equality.

| Result | Interpretation |
|---|---|
| C approximately B, or no sufficiently precise C>B result | No prospective learning advantage established under this experiment; distinguish a precise null from an inconclusive result |
| C>B but C does not beat A | Evidence may support useful experience-dependent adaptation relative to its own frozen architecture; the full Rung-1 advantage over competent frozen routing is not established |
| C>A but C does not beat a retained fair template-only comparator on S | S-specific superiority over that available static mapping remains unestablished; review baseline selection. Not proof that C contains no learning |
| S0/S1 changes scores but not action/probability | State sensitivity without demonstrated behavioral consequence |
| S0/S1 changes action but correctness does not improve | Causal behavioral adaptation without demonstrated competence improvement |
| SHAM alters state but its changed fields do not affect useful actions | Mechanistic label sensitivity is insufficient; causal chain remains incomplete |
| Benefit before restart disappears after correctly specified restoration | Persistence claim fails or is unresolved pending an identified apparatus fault; no post-boundary Rung-1 success |
| S1 survives restart/restoration, causally changes useful choices, C beats all required frozen controls, and cost/independence gates pass | Rung-1 success within the declared model/menu/task distribution |
| Only T improves | Potential narrowly scoped later-instance Rung 1 if its preregistered primary rule passes; no S-transfer claim and no post-hoc rescue of a failed S-only endpoint |
| S improves beyond twin and competent template-aware champion | Bounded routing benefit on prespecified structural variants using the fixed representation; no new abstraction/procedure claim |
| NEAR improves | Potential better obedience to explicit conflicting rules; inspect actual errors, not an automatic overgeneralization verdict |
| UNREL improves | Could be legitimate broad strategy calibration or a confound; resolve with the same causal/resource controls, not an automatic rejection |
| Correctness gains accompany unequal hidden retries, answer access or selective exclusions | Invalid for the intended causal verdict, regardless of p-values |

All started histories and attempted tasks remain accounted for. Candidate timeout, empty/length-terminated generation, malformed code and invalid output ordinarily count as failures within budget. Genuine administrative interruptions follow a prespecified, outcome-blind block rule with complete reporting. No investigator-selected favorable subset becomes the primary denominator.

## 17. Rung-1/Rung-2 boundary

**INFERRED.** Rung 1 can identify improved selection among existing alternatives. It leaves unresolved whether experience has added a useful procedure that was unavailable under the original fixed strategy menu and resources. Neither an S score nor a new-looking generated program proves that stronger fact.

A positive can be explained by pretrained capability, better elicitation, static features plus learned outcome estimates, and ordinary finite-table updating. Those mechanisms are admissible at Rung 1. The fixed workers' raw capabilities need not change.

Rung 2 would require an operational account of prior availability and a causal contribution from a newly retained procedure, distinguished from merely retrieving or eliciting something already accessible. No finite unsuccessful prompt sweep proves absence from all latent model capability. This report does not design that experiment, enlarge the strategy menu, or require its solution before measuring Rung 1.

## 18. Singularity Archaeology checkpoint

**INFERRED — backward sanity check, not a roadmap:**

| Hypothetical higher transition | Missing capability not guaranteed by lower rungs |
|---|---|
| Sustained competence-frontier expansion | Repeated external validation that progress is beyond a fixed task ecology, not benchmark generation inside an existing envelope |
| Useful autonomous challenge generation | A method for selecting informative, attainable challenges and evaluating their relevance independently |
| Improving acquisition | Prior development reduces cost/evidence for later acquisition, not merely retrieves more familiar cases |
| Accumulating retained capability without erasure | Multiple useful additions with retained earlier value and controlled interference |
| Acquiring useful procedures beyond a fixed menu | A validated persistent addition not explained by selecting/eliciting an already available option |
| Rung 1 | Evaluated experience causally improves retained strategy selection across a boundary under fair controls |
| Present demonstrated ingredients | Persistent files, update functions, routing consumers, local generation and experimental infrastructure; useful Rung-1 causal composition remains unestablished |

Every row admits a system with all the lower ingredients that never reaches it. A perfectly calibrated finite router can saturate forever. This does not make its measured Rung-1 learning unreal. Nor is success in this particular routing task a universal prerequisite for every architecture that could learn procedures directly.

For the next rung only: **target**—a useful experience-derived procedure outside the initial available menu; **strongest counterfeit**—latent pretrained capability or a previously available composition elicited through a new prompt; **eventual discriminator**—a bounded prior-availability comparison plus a causal intervention on the newly retained procedure under matched resources. That is the unresolved distinction, not an experiment designed here.

## 19. First unsupported arrow

**INFERRED.** Correctly attributed, independently evaluated prospective experience → retained state that causes improved later task correctness beyond the required frozen controls after a real process boundary at matched final-inference cost.

This remains empirically unsupported in the proposed apparatus because the apparatus has not been built or qualified. The arrow is scientifically testable; absence of evidence is not a claim that the mechanism is implausible. Passing isolated logging, serialization, or state-perturbation tests would establish only portions of it.

## 20. First counterfeitable arrow

**OBSERVED / INFERRED — current machinery:** candidate execution → supposedly trusted hidden correctness is counterfeitable through expected-answer access. This is earlier in the measurement chain than the unsupported beneficial-learning arrow, and survives a namespace-only or readable-files subprocess repair.

**INFERRED — after qualified repairs:** the next interpretive jump from genuine Rung-1 routing benefit to newly acquired procedures is still counterfeitable by elicitation or retrieval of existing capabilities. Bounded S-routing generalization is not itself an additional counterfeit when experience genuinely causes it through a fixed representation. The game report incorrectly treats hidden-convention learning as necessary to that narrower result.

These are different reference points, deliberately separated: an existing measurement exploit versus the next unjustified capability claim. Neither should be mislabeled as a reason to reject a valid outcome-updated table at Rung 1.

## 21. Remaining blockers

**OBSERVED / UNKNOWN — concrete work, not another general theory program:**

1. No qualified expected-answer/process/filesystem/output-protocol boundary exists for the proposed use. The current grader remains unsuitable unmodified.
2. Neither named production generation helper satisfies the explicit seeded, single-call, fully metered, isolated request contract. A research adapter and verifiable model pinning are needed.
3. The final public task packet, two strategies, shared feature granularity, table policy and state schema require finite development choices and freezing. Workers must receive sufficient current-task information equally; hidden random conventions cannot remain an accidental missing prerequisite.
4. Controller-owned actor/artifact binding, complete-state checkpoints, fresh-process restoration and content-to-action-to-utility diagnostics are specified but not implemented or qualified.
5. No final workload-specific champion, routing-opportunity evidence, pilot variance/cost estimates, numerical effect/cost thresholds or confirmatory history count exists yet.
6. Actual task/partition separation, oracle contract coverage and protected diagnostic/holdout access must be qualified on the new substrate; inherited AP-0 labels do not certify them.

These do not require live Echo changes, repairing AP-0 constructors, a new candidate-memory mechanism, or answering Rung 2. If a required host isolation property proves unavailable at zero cost, stop and report that engineering limitation rather than treating a weaker boundary as qualified.

## 22. Theory-done judgment

**INFERRED — ENGINEERING-GATE.** There is no remaining major ambiguity in what Rung 1 would mean or in a feasible way to identify it. The information-denied template arm and the full ecological SHAM rollout are unnecessary. The expected-answer boundary, pure state/update contract, frozen twin/champion and history-level comparison define a falsifiable ruler.

Theory is done enough to justify asking for a small, separately authorized apparatus increment. It is not done in the sense of proving that an unbuilt implementation is secure, that local strategies offer headroom, or that a tiny pilot will find an effect. Those are exactly the questions engineering qualification and development measurement should answer.

Further broad adversarial stories have diminishing value before there is a concrete boundary implementation to attack. Review should become focused on actual interfaces, hostile fixtures, complete-state reconstruction and pilot feasibility. A negative qualification or a well-measured null is an acceptable endpoint; no positive learning result is promised.

## 23. Minimal implementation plan if warranted

**PROPOSED ONLY. No step below was executed or authorized.** Paths identify possible new isolated research components, not existing files. Keep all new runtime output under a dedicated research root excluded from production. A single small package can combine these components; the table specifies responsibilities rather than demanding one file per row.

| Order / component | Purpose and invariant | Production change? | Expected qualification | Rollback | Timing |
|---|---|---|---|---|---|
| 0. Research protocol/manifest, e.g. `research/rung1/protocol.json` | Freeze this information, state, cost, arm and replay contract; distinguish synthetic qualification, development/pilot and confirmation | No | Static completeness review: no essential convention withheld, no ambiguous outcome/cost/replay rule, protected-data map and approval scope explicit | Supersede draft version; preserve prior evidence | Specify before code construction; final numeric settings before confirmation |
| 1. `app/experiments/rung1/evaluator.py`, candidate runner and dedicated sandbox profile | Expected answers and trusted comparison cannot be addressed by candidate execution; only bounded typed values cross | No; do not edit AP-0 or production sandbox | Synthetic hostile fixtures and independent reference cases, including known oracle paths/FDs/frames, marker/equality/serialization attacks, access denial, timeouts and malformed output; no model calls needed | Disable/discard isolated package version and scratch root; preserve qualification artifacts | First apparatus increment; must qualify before any candidate/model trial |
| 2. `app/experiments/rung1/client.py` | One explicitly seeded, pinned, metered request; no production imports, invisible fallback or history | No | Mock-server request/response and failure tests; source/import-side-effect checks; later controlled backend identity/telemetry check under separate permission | Disable research client; no production wiring exists to undo | Before model-backed development/pilot; can be built alongside evaluator |
| 3. Research task adapter/partition manifest | Identical complete public specifications, hidden case data, sufficient contract coverage, prospective lineage separation | No; use version-pinned reusable pure source only | Reference agreement, specified edge cases, actual overlap/exposure checks, missing-rule and metadata-leak rejection | Discard unused task freeze; never reuse exposed holdout as confirmatory | Interface before construction; fixtures before development; final draws before confirmation |
| 4. Pure selector, state serializer and controller-owned ledger | Only validated outcome counts update retained action values; E/U/S/D/artifact/O mechanically bound | No RiverBrain or ledger edits | Hand-checkable event fixtures, exactly-once updates, independent reconstruction, unknown-field rejection, label/count controls, complete canonical restore | Delete/disable only isolated state namespace; retain audit copies | Before longitudinal pilot |
| 5. History/restart/intervention controller | Real process exit/load, uniform S0/S1 invocation, coupled randomness, no hidden history; fixed-trace replay stays fixed | No | Mock generations and synthetic rewards; crash-before-commit, restored-state decisions, replay equivalence, no ambient reads/writes, no final feedback | Stop research controller and archive its state; no live Echo restart | Before longitudinal pilot; do not wait for live trials to discover boundary defects |
| 6. Frozen baseline/development selection and metering | A competent static alternative, credible strategy opportunity, and full resource accounting | No | Development-only evaluation with lineage-separated validation; template routing and constants included; all calls/costs counted; floor/ceiling or no-headroom stops accepted | Retire the development candidate set/version; never count it as confirmation | After infrastructure qualification, before choosing final sample size |
| 7. Independent history analysis and final freeze | Correct denominators, joint superiority/cost criterion, uncertainty and stopping; no outcome-selected subgroup or checkpoint | No | Synthetic correlated histories and failure/exclusion fixtures; independent recomputation of scores/interval inputs; frozen analysis reproduces from controller evidence | Supersede only pre-confirmation versions; after exposure, changes create a new study version | Analysis implemented before confirmation; final numeric freeze after a separately permitted pilot |

“Before apparatus implementation” cannot literally mean implementing a repair before writing any apparatus code—the repair is the first apparatus component. The pre-code requirement is the reviewed boundary/API specification and separate authorization. The concrete engineering blocker to assembling or using the learner apparatus is successful qualification of step 1, followed by the generation contract before real model work. Do not bundle authorization for these isolated fixtures with permission to run a prospective learning experiment.

## 24. Final recommendation

**PROPOSED.** Stop broad Rung-1 conceptual expansion. Seek a separate decision on a small isolated evaluator/generation-interface implementation and its synthetic qualification. Do not yet authorize trials, production integration, AP-0 repair or Rung 2. Use qualification results to decide whether a bounded development pilot is worth running.

The new reconciliation **REFINES** the previous no-implementation conclusion by resolving the replay estimand and acknowledging the evaluator defect. This gate additionally rejects a redundant/unfair template-only arm and closes the task-information ambiguity prospectively. The reason to move to engineering is not audit fatigue: the remaining failure conditions are concrete, implementable and independently testable. They cannot be verified by another agreement between documents.

**OBSERVED — principal report fingerprints at entry:**

| Report | SHA-256 |
|---|---|
| Original routing design | `ae01655ab8970834b398653ebd9224ab5ca759724056fb4180e9bf0d662346c8` |
| Pre-mortem | `a01dac05a97ca7f5a7b2b2f6fb1ef77ca69cdccab6c80a7fc8f5a35cd0472ae0` |
| Trusted-boundary reconciliation | `ce1ebaac1acf3643f817407c0dc6b8ca197779d26ac78f666db869ea12539f20` |
| Adversarial Learner Game | `c76fae1e75ebcce5c74a1d4fed5d45a1c3e4322a50258dd9b883a900416010c9` |

**OBSERVED — closing integrity verification, 2026-09-23 12:28:36 UTC.** HEAD remained `2fba42644c82b9f7096276f4dd338d615cf1bcce`. All 23 fingerprinted source/report/result files matched their inspection baselines. The same 28 tracked modifications remained, with no staged changes; untracked files increased from 280 to 281. The only added status entry was this report, and no pre-existing entry changed or disappeared. This scoped comparison does not claim to have measured every byte of live runtime state. All 24 required report sections were present and all local file links resolved.

Only file created by this mission: `audits/2026-09-23_rung1_final_preimplementation_gate.md`. No prior report was overwritten. No production/AP-0/evaluator/prompt/routing/state/Git change, model call, verification-suite execution, trial, constructor retry, or Stage 1 run was performed.

The statuses below qualify the proposed design, not an empirical claim that FeralEcho has already achieved Rung 1. CONDITIONAL means the specified interface still requires implementation/qualification; QUALIFIED for the feedback contract means the field-level design is adequate, not that its enforcement has been demonstrated.

**RUNG-1 CLAIM:** CONDITIONAL

**TRUSTED EVALUATOR DESIGN:** CONDITIONAL

**LEARNER FEEDBACK CONTRACT:** QUALIFIED

**GENERATION ISOLATION:** CONDITIONAL

**FIXED CONTEXTUAL CHAMPION:** REQUIRED

**UPDATE-DISABLED TWIN:** REQUIRED

**TEMPLATE-ONLY CONTROL:** UNNECESSARY

**EXPERIMENTAL UNIT:** Independent paired learning history, with evaluation worlds nested within history and shared across its compared policies.

**MATCHED-COST CONTRACT:** CONDITIONAL

**PERFECT-INFORMATION ROBUSTNESS:** CONDITIONAL

**FIRST UNSUPPORTED ARROW:** Evaluated prospective experience causes retained selection changes that improve later hidden correctness beyond the required frozen controls after a process boundary at matched final-inference cost.

**FIRST COUNTERFEITABLE ARROW:** Under current machinery, candidate execution can appear to establish trusted hidden correctness by reading protected expected answers.

**NEXT RUNG:** Determine whether experience adds a useful retained procedure beyond what the original fixed strategy menu could already deliver under a declared resource budget.

**PROJECT STATE:** ENGINEERING-GATE

**IMPLEMENTATION AUTHORIZATION:** NO

1. **What is the strongest remaining way to fake Rung 1?** Read oracle answers through the incomplete evaluator boundary and let apparent rewards favor that strategy. After answer access is closed, the strongest causal concern is an undeclared schedule/history channel causing the useful gain while label-sensitive logs merely supply a convincing story.

2. **If that counterfeit succeeds, does it satisfy Rung 1?** No: answer access defeats independent task correctness, and disconnected logs fail the stipulated causal chain. A genuine experience-updated table that improves later correctness under the controls does satisfy Rung 1, even if that is the simplest winning mechanism.

3. **What concrete blocker must be solved before apparatus implementation?** The exact candidate access boundary and typed output contract must be agreed before coding; implementing and qualifying that isolated boundary is then the first apparatus increment, and must precede real learning trials. Process separation without protected-file/descriptor access control is insufficient.

4. **More thought experiments, or engineering boundary?** Rung 1 has reached an engineering gate. The next useful evidence comes from authorized implementation and hostile qualification of the specified ruler, not another general theory document. Nothing is authorized by this report.

5. **Exact permissible sentence after a perfect success:** “In an isolated FeralEcho research harness, independently evaluated prospective experience caused routing-state changes that survived a fresh process and improved later hidden-test correctness over the preregistered competent frozen contextual policy and identical update-disabled twin at matched final-inference cost on the tested task distribution, with acquisition cost reported separately.”

6. **Still unjustified:** “FeralEcho autonomously acquired new general capabilities and improved its ability to learn.”

7. **Next developmental question:** Can experience contribute a useful new retained procedure beyond the initial available strategy menu, rather than only improve selection or elicitation within it?
