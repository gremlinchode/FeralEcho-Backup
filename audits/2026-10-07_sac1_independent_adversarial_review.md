# SAC-1 adversarial review and implementation gate

October 7, 2026. **Final disposition: REVISE. Implementation authorization remains NOT GRANTED.**

**Architecture verdict:** separating a remembered repair proposal from application authority is technically coherent and worth preserving. The proposed *authority mechanism* is not yet sufficiently specified or qualified. In particular, a separate verifier can faithfully enforce the same wrong task interpretation as the repair generator.

**Protocol verdict:** preserve frozen SAC-1 v1 as an unexecuted, disclosed diagnostic design. It can potentially demonstrate that a particular engineered package handles its prescribed examples. It is **insufficient as the implementation gate for robust semantic authority, unseen implementation generalization, or the claim that this is the cheapest useful architecture**. It explicitly does not test autonomous acquisition or retained net utility; that limitation is correct, not itself a protocol defect.

For its narrow, honestly stated **engineered package feasibility on these examples**, the case design remains useful. This review does not declare an unrun experiment failed, demand autonomous acquisition before engineered feasibility, or fault the deliberate absence of implementation. The actionable objections are unresolved authority/observation interfaces and execution rules, plus an inadequate comparison for choosing the more elaborate architecture. Stronger generalization claims would require a successor qualification.

The next action is a small **design revision for human review**, not implementation: specify the source of task authority, observation semantics and proposer/verifier interfaces; add a cheaper same-verifier baseline; and commission a separately frozen, independently held qualification after implementation hashes are fixed. Do not change the existing SAC-1 freeze or build a general semantic analyzer.

## 1. Review method, independence and integrity

Evidence labels throughout:

- **DIRECTLY VERIFIED:** inspected source, immutable bytes or recalculated existing raw results. This does not imply new runtime execution.
- **SUPPORTED INFERENCE:** a conclusion follows from those mechanisms, but the proposed failure or benefit was not executed here.
- **UNTESTED HYPOTHESIS:** plausible prospective behavior requiring qualification.
- **BLOCKED / UNKNOWN:** required implementation, evidence or authority is absent.

This is a new adversarial source/evidence review, **not independent reviewer identity**: the reviewing assistant previously authored the proposal and retains that context. It must not claim to be blind to that work. Independent human review and an evaluator/case custodian separate from the future implementer remain necessary. No subagents or relays were used.

[Opening record](sac1_adversarial_review_20261007/opening.json), 22:10:39 PDT, pins **488 existing authority paths** and finds zero discrepancies. Branch `vsl-implementation`; HEAD `e5acbb09cece8d1791fa6d967fe57067137a8cff`; cached origin/main `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`; ahead/behind 4/0 without fetch. Staging empty; fourteen pre-existing tracked modifications preserved. Inspection began before the durable snapshot; no production mutation or scientific execution preceded it.

[Process snapshot](sac1_adversarial_review_20261007/opening_processes.txt): Echo 55361, start October 1 15:45:19; watchdog 56610, September 28 09:44:38; Ollama 1991, September 19 10:57:03. Existing auxiliary processes are recorded. Live mutable memory/self-model files are separately fingerprinted, excluded from scientific inputs and permitted to evolve without inferred attribution.

The original [architecture report](2026-10-07_semantic_competence_repair_authority_architecture.md), [SAC-1 protocol](semantic_authority_20261007/protocol.md), its generator, production VSL sources, historical raw outcomes, E0.1/worker/observer/profile and provenance sources were inspected. The new review scripts perform historical hash/AST reconstruction and bookkeeping only. **No SAC-1 implementation, recognizer trial, candidate execution, learning, inference, promotion, service action or production change occurred.**

Held-out exposure was minimized: the SAC-1 answer matrix was hashed as authority, not deserialized or scored during this review. The public generator was necessarily read to assess coverage, oracle correlation and exposure. Its source already reveals the recipes and deterministic input construction. No new hidden challenge was generated. That distinction does not restore blindness to already disclosed material.

## 2. What survives independent source/raw checking

| Claim | Status | Evidence and limit |
|---|---|---|
| Unchanged Skill A has both missed equivalents and harmful matches | DIRECTLY VERIFIED | Raw baseline confusion 4 TP / 9 FN / 5 TN / 6 FP; recount of 24 historical oracle files. n00–n03 each 36→12; n04 unchanged 36→36; n05 unchanged 12→12. No new candidate run. |
| A source-only decision cannot distinguish opposite intended contracts | DIRECTLY VERIFIED | Historical p00/n03 have identical source, different specified priority and opposite repair consequences. This is missing information, not only weak pattern recognition. |
| Production consumption lacks task-correctness authorization | DIRECTLY VERIFIED | `runtime.consult` accepts source/function, not an interpreted task contract. `echo_adapter.record_final_verdict` records `f1_f2_safety_only`; `echo_projects` applies proposals before those gates. |
| A richer human-engineered grammar can improve bounded safety | DIRECTLY VERIFIED within the old test | SA-R1 raw challenge reports TP2/FN2/TN5/FP0. Its author supplied semantics. It does not establish autonomous acquisition or complete recognition. |
| Current RNU established positive or negative retained net utility | DIRECTLY VERIFIED: claim not supported | Raw 44-task analysis: 25 correct/19 incorrect in both arms, zero applications, zero benefit/harm; disposition INCONCLUSIVE. |
| Existing E0.1 transport has useful qualified isolation/equality evidence | DIRECTLY VERIFIED historical result | 28 boundary calls across two rooms; twelve reference/confined verdict pairs agree, including type distinction, errors and timeout. This qualifies those controls, not every future caller or oracle. |
| Proposed semantic C and autonomous D exist | BLOCKED / UNKNOWN | Neither is implemented. The design honestly lists them as absent. No new runtime reliability can be inferred. |

Reproducible raw recount: [source_and_raw_recount.json](sac1_adversarial_review_20261007/source_and_raw_recount.json). Source authorities: [matcher](../app/core/skill_ledger/matcher.py), [runtime](../app/core/skill_ledger/runtime.py), [adapter](../app/core/skill_ledger/echo_adapter.py), [project integration](../app/core/echo_projects.py), [schemas](../app/core/skill_ledger/schemas.py).

The strongest surviving architectural principle is **a remembered edit is evidence for a hypothesis, not evidence that the current task authorizes that edit**. Nothing found requires deleting VSL's persistence/lifecycle foundation. Nothing found establishes that a new semantic contract layer is sufficient by itself.

## 3. Ranked vulnerabilities and concrete mechanisms

“Exploitability” below means how easily the measurement or authorization can be defeated; it does not imply a malicious actor or an observed exploit. No attack program was executed.

| ID / severity | Concrete mechanism and relevance | Evidence status | Prevention / architectural consequence |
|---|---|---|---|
| **F1 — Critical authority gap** | Generator and verifier both consume an incorrect, incomplete or stale task contract. Every output can agree with the oracle while violating actual requirements. SAC-1's `add()` supplies both the task order and `expected()`'s order from the same value. | DIRECTLY VERIFIED shared dependency; SUPPORTED INFERENCE about correlated incorrect authority | Establish task-contract provenance and freshness independently of the retrieved skill. Separate empirical conformance from authority beyond the tested scope. No verifier can recover omitted intent merely through isolation. |
| **F2 — High qualification exposure** | The public generator/seed/table reveal all sixteen mechanisms and provisional decisions before C exists. A case-ID/source-hash lookup could fake performance; an honest implementation can also overfit the disclosed families without such a lookup. | DIRECTLY VERIFIED exposure; no claim an implementation exploited it | Keep SAC-1 as disclosed diagnostic material. A successor needs frozen implementation first, independently held semantic recombinations, and source review for answer tables. Public opaque IDs are not a secrecy mechanism. |
| **F3 — High architectural non-identifiability** | Simple edit proposal plus the same decision oracle may meet the thresholds without semantic bindings, contracts learned from experience, or useful retained knowledge. A0 is an empty-store fixed-program baseline; B has no new verifier; D is absent. | DIRECTLY VERIFIED arm design; UNTESTED HYPOTHESIS that a cheaper proposal strategy passes | Compare with a capable cheap proposer using the identical verifier and proposal budget. Credit B/C gains to the whole engineered package, not to semantic representation or learning. |
| **F4 — High scope/coverage gap** | Protocol calls the domain finite, but unrestricted strings/integers make it infinite. Length 1–3 is admitted; generator produces only lengths 2 and 3. A singleton failure can evade every decision and hidden test. Score/name changes do not establish broad behavioral coverage. | DIRECTLY VERIFIED source mismatch; SUPPORTED INFERENCE about undetected failures | Correct the claim in a new protocol, not the old file. Define a genuinely finite exhaustive domain or explicitly bounded sampling with edge cases and restricted authority. Passing 48 tests is not a proof over all inputs. |
| **F5 — High information-flow gap** | Proposer payload, contract record, grammar and test-service interface are still unspecified. The matrix contains source, labels, witness edits and expected values together. Candidate isolation does not itself prevent a controller-side proposer from seeing those fields or allowing learned constraints to weaken the task contract. | DIRECTLY VERIFIED missing implementation/interface; actual leakage BLOCKED / UNKNOWN | Freeze minimal serialized proposer inputs; authoritative task fields cannot be overwritten by skill fields. Keep hidden answers and authorization policy separate. Log exact proposer inputs and attempted query budget. |
| **F6 — Medium/high observation gap** | Returned `entries_after` checks final serialized value, not object identity, transient mutation, other aliases or arbitrary global effects. E0.1 distinguishes bool/int but otherwise uses Python equality, so int/float equality is not an exact-type preservation proof. | DIRECTLY VERIFIED worker/comparator/wrapper mechanism; SUPPORTED INFERENCE about broader ownership blind spots | Specify value-preservation versus stronger ownership obligations. Add trusted schema/effect observations or reject unsupported effects. Do not claim current worker output proves all side effects absent. |
| **F7 — Medium execution-policy ambiguity** | “One unsafe accepted repair” stops execution without consistently specifying C rather than baseline B. B is expected to admit bad repairs. The “bounded decision-test service” lacks a query interface; one final edit does not necessarily mean one exploratory proposal. Budget counts four arm outputs although D is unavailable. | DIRECTLY VERIFIED protocol text; effect on a future runner BLOCKED / UNKNOWN | A successor must specify arm-specific stops, proposal commitment, feedback access, actual arms and accounting before execution. Do not decide after a baseline harm or budget overrun. |
| **F8 — Medium learning/evidence gap** | Current acquisition extracts a local AST edit. Whole-skill degradation is not learning an applicability boundary. Degradation groups by feature key, while records include versions; evidence logging is best-effort. Lifecycle transitions accept caller-supplied evidence text rather than verifying its truth. | DIRECTLY VERIFIED source; future poisoning/attribution failures SUPPORTED INFERENCE | Keep lifecycle storage, but independently bind validated evidence to exact versions and applications. Add a qualified acquisition mechanism later; metadata or lifecycle labels cannot certify semantic truth. |

F1–F5 block the current implementation recommendation. F6–F8 constrain the permitted scope and the successor's interface. Most are addressable within proposal/authorization separation; they are not reasons for a wholesale replacement. **Missing true task intent is a fundamental information limit**: the correct response may be abstention, not more machinery.

F1's critical severity concerns future authorization under incorrect intent; **no incorrect SAC-1 expected value was demonstrated here**. Sharing an authoritative specification is necessary and is not circular by itself. SAC-1's pairwise oracle is independent of the candidate's numeric map and proposed transformation, a real strength. A human-defined synthetic contract can be valid authority for this engineered stage after independent review; it need not be autonomously acquired. Likewise, a lookup-table implementation would violate SAC-1's intended development restrictions, not establish that all honest implementations overfit. Exposure limits the evidentiary strength of an unseen-transfer claim.

### A concrete cheaper rival, not an implemented attack

**SUPPORTED INFERENCE:** source inspection shows that the positive fixtures largely require removing a single unary sign, and both multiple-site fixtures put a dead match before the live repair site. A crude proposer choosing a late unary-minus site, then letting the existing decision oracle reject non-improvements/mutation, is a plausible rival to C. The extracted-expression positive would challenge that heuristic, but 7/9 allows two misses. This mechanism could obtain apparent “semantic” success mostly from the verifier and fixture regularities.

**UNTESTED HYPOTHESIS:** that rival actually meets the full criteria. It was neither written nor executed, and the new fixture labels themselves remain provisional. A rule that fabricates binding evidence would violate the intended protocol; the current design has not defined how such evidence is independently checked. The legitimate conclusion is **add the cheaper baseline and independently test binding claims**, not “SAC-1 has been experimentally defeated.”

### Other verifier limits worth preserving, not expanding into a sandbox project

**DIRECTLY VERIFIED:** `trusted_evaluator.run_case` classifies empty-output exit 65 as sandbox infrastructure failure. A child-originated exit with that code is not distinguished by that branch. SAC-1 currently stops on infrastructure failure rather than excluding it and reporting success, which limits the result to denial of measurement, not a manufactured positive. Do not later turn this label into automatic task exclusion without stronger launch evidence.

**DIRECTLY VERIFIED:** stdout length is bounded after `capture_output`, not while streaming. The original profile permits broad reads; the research confined profile is what denies historical/hidden files. The durable observer writes expected values to its controller journal, which must remain outside readable rooms. These are disclosed operational limits. No new exploitation, stress testing or evaluator redesign was undertaken.

## 4. What the frozen SAC-1 can and cannot discriminate

| Proposed distinction | Review conclusion |
|---|---|
| Historical exact syntax versus some broader behavior | **Potentially yes**, if independent preflight confirms the cases and C emits genuinely bound edits. Alpha/helper changes are meaningful; exact matching fails many. |
| Semantic reasoning versus engineered case-specific rules | **No, not decisively.** Public cases, one repair family and missing cheap baseline permit alternative explanations. C's behavior must be qualified on separately held combinations. |
| Investigator-provided task knowledge | **Yes as a disclosed input**, but its contribution is bundled with new representation, binding and verification. B/C cannot separate those contributions. |
| Autonomous acquisition | **No.** D is missing; correctly labeled absent. Nothing in C's success would establish it. |
| Safe repair authorization | **Only conformance on the specified observations/cases**, conditional on correct contracts, oracle and implementation. No production or universal authority follows. |
| Useful transfer to unseen implementations | **Weak evidence at best** from the exposed design. New source bytes with familiar templates are not sufficient independence. Same-agent implementation after this review could not claim blindness. |

**DIRECTLY VERIFIED strengths:** identical-source/opposite-contract rows test an actual information boundary; rank-orientation and alias cases are relevant; partial repairs are not counted as full task success; missing intent/ownership requires refusal; hidden scoring cannot select an edit; blanket abstention fails the 7/9 coverage threshold; no p-values or natural-utility claim are proposed; candidate isolation and no-production rules remain intact.

**DIRECTLY VERIFIED weaknesses:** all programs use one tiny ranking family, fixed map values with one reversal, three shared tags and one repair operator. The multiple-site order is not counterbalanced. The new matrix does not directly challenge builtin shadowing, last-element selection, descending sorting, contradictory contracts, stale contracts or forged binding/evidence records, despite related known risks. Some of these are declared unsupported, but rejection of unsupported code must itself be verified. Two UNKNOWN cases are explicit nulls; they do not test silent incompleteness.

**SUPPORTED INFERENCE:** 7/9 plus one success per representation group is a useful anti-abstention screen, but too permissive to identify a reusable abstraction. The two helper cases can be satisfied by one familiar helper while missing extracted dataflow. Zero harmful acceptance on five targeted negatives is necessary for this gate but cannot estimate a deployment harm rate. The sample is too small, related and deliberately constructed for population inference.

**Decision:** do not amend SAC-1 v1. Preserve its protocol hash `be6637d7bb0bd2c491fce6797d50e219baeea4a9e7cfd2c86442490a0d8a09b4` and design manifest hash `e888431145631c36381ec3993dbd600e0cc33843914002100eff416e99b0476e`. Its legitimate role is now a disclosed regression/diagnostic reference if separately authorized, not the sole prospective qualification.

## 5. Who authorizes correctness?

There is no universal oracle in the repository. E0.1 provides isolated execution and an independent **comparison with supplied expected values**. It does not determine whether those values capture the intended task. The current architecture must distinguish the following authorities.

| Method | Useful authority | Concrete failure limit |
|---|---|---|
| Independent behavioral oracle | Objective outcome for inputs within a versioned, independently established specification | Wrong task interpretation; untested branches; omitted side effects; hidden tests used to tune proposals |
| Task-contract checks | Establish current intent, types, ownership and scope | Contract incomplete, conflicting, stale or supplied by the same unverified model; validity of syntax is not truth |
| Property-based tests | Generate diverse cases, shrink violations; useful for ownership and edge inputs | Generator omits cases; property is weak/wrong; both faulty and correct programs satisfy it |
| Metamorphic tests | Check relations without a full oracle, such as permutation or consistent renaming | A reversed winner rule can satisfy those same invariances; cannot identify intended priority alone |
| Static analysis | Check bounded bindings, prohibited effects, aliases and live uses in a declared language subset | Unsound treatment of shadowing/dynamic dispatch; unknown mistaken for safe; same mistaken assumption as the generator |
| Bounded symbolic/formal checking | Prove/refute a formal relation under explicit semantics and bounds | Wrong/incomplete spec, incorrect model of Python, timeout, unsupported behavior; bounded proof is not unbounded correctness |
| Model-generated tests/judgments | Propose useful counterexamples and hypotheses | Correlated hallucinated requirements; agreeable tests; unverifiable explanations; model confidence is not authorization |

Property-based generation still relies on supplied actions/properties; it does not supply their truth. [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/stateful.html). Symbolic checking is likewise bounded: CrossHair explicitly documents that no counterexample is not a correctness guarantee, along with identity and nondeterminism limitations. [CrossHair limitations](https://crosshair.readthedocs.io/en/latest/limitations.html). No new tool was installed or run.

### Recommended authority hierarchy

1. **Authoritative task requirements:** versioned task/environment specification or explicit owner-approved requirements, independently sourced from retained skill suggestions. Conflicts, absence or stale hashes block repair.
2. **Trusted interpretation and observation contract:** reviewed translation of those requirements into types, allowed effects and expected behavior. A model may propose this translation, but it is a hypothesis until independently checked.
3. **Independent checks:** qualified execution plus oracle/property/static or bounded proof evidence within named scope. Disagreement means abstain. Multiple model opinions derived from one assumption do not become independent evidence.
4. **Proposals:** retrieved records, model reasoning, inferred bindings and suggested tests. These may request checks; they cannot delete requirements, supply their own final labels, mark evidence authoritative or promote themselves.
5. **Application decision:** a trusted controller binds exact source, task contract, skill/version, patch, checker version, observations and limits. A hash change invalidates reuse of that decision. This is empirical authorization within a scope, not a transferable proof of all future behavior.

**SUPPORTED INFERENCE:** this hierarchy is feasible for bounded task environments with trustworthy specifications. **BLOCKED / UNKNOWN:** availability of such specifications for arbitrary future Echo work. If intended behavior or ownership cannot be established, retain the original, record the unresolved requirement and, only where necessary, ask the task owner. Do not silently fill the gap from Skill A or make an external agent a runtime dependency.

Correlated-error example: the true task prefers the reverse tag order, but a generated contract uses the historical order; both proposer and expected-value generator consume that incorrect order. They agree perfectly. Different processes, different code for comparison and a larger model do not repair the missing source of truth. The opposite-contract pair tests behavior *when correct intent is provided*; it does not test obtaining correct intent.

## 6. Autonomous acquisition: what is actually missing

The progression A→B→C is plausible **only if experience changes information used at later decisions, and no-experience controls cannot reproduce the gain within matched resources**. Today's plan supplies A, describes B and hopes for C. It does not yet implement the bridge.

| Contract element | Possible permitted evidence | Required safeguard / current gap |
|---|---|---|
| Intended behavior | Current task specification, authoritative examples | Preserve source and unknown fields. Reading an explicit requirement is not itself learning from prior experience. |
| Preconditions and limitations | Differing successful and failed transfers under known contracts | One pair underdetermines the boundary; require counterexamples and held-out discriminants. Current extractor stores a local edit. |
| Bindings and dataflow | Program definitions/uses plus task schema and causal observations | Need a bounded binding representation and checker. Do not treat variable names or last occurrence as meaning. |
| Transformation obligations | Exact acquired edit, scope and preserved invariants | Bind to the actual live site; record what cannot change. No arbitrary generated verifier code in a skill record. |
| Postconditions and ownership | Independent requirements, observed output and effect evidence | Final serialized values do not establish all ownership semantics. Unspecified ownership is not permission. |
| Counterexamples | Independently verified harmful or irrelevant reuse, with original/repaired artifacts | Attribute to exact version/contract/site; separate oracle/infrastructure failures from semantic failures. |
| Validity evidence | Replayable verdicts, checker hashes, bounded domains, uncertainty | Evidence references, not a free-text confidence assertion or self-reported PASS. |

**DIRECTLY VERIFIED:** current `extract_transformation` finds a small AST difference and stores local context; it does not acquire these complete semantic fields. Runtime logs have verifier-strength labels but the production adapter supplies safety-only results. `evaluate_degradation` is explicit whole-skill degradation, not counterexample-conditioned boundary learning.

Related raw acquisition evidence remains narrow: the prior-library XOR experiment recorded 1/5 successes versus 0/5; the subsequent contradiction experiment's twelve post-initial revision attempts were invalid DSL arity. These observations do not establish a semantic contract learner or its impossibility. The previous report's interpreter recheck and lifecycle labels cannot substitute for that missing learning mechanism.

The minimum bridge would be a **fixed, inert hypothesis language** whose fields can remain unknown; a bounded acquirer exposed only to permitted task evidence; independent validation and positive/counterexample replay; write-once candidate records; and prospective acquired-record ablation. Freeze the interpreter before acquisition so learned content cannot hide in a newly hand-coded engine. Compare with the same capable model given current task requirements but no retained experience. If that model derives the same useful contract without experience, do not credit the result to retained learning.

Counterexample-guided refinement can organize search and rejection, but correctness remains relative to the supplied specification and verifier. It is not an automatic source of intent. [MIT synthesis lecture](https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture17.htm). Updates must be bounded, versioned and checked against retained positives, so “learned caution” cannot be blanket suppression of useful reuse.

## 7. Simpler alternatives and what to preserve

| Alternative | Safety / useful coverage | Acquisition potential | Complexity, inference, memory, integration |
|---|---|---|---|
| Existing conservative retrieval + independent behavioral gate | Likely rejects known harmful proposals; preserves current recognition misses | Does not acquire broader conditions | Lowest incremental complexity, zero inference, serial evaluator cost; useful safety baseline but cannot alone close availability-to-use |
| **Small proposal generator + same independent verifier** | May recover many sign-edit cases without a semantic analyzer; incomplete tests still risky | Generic repair engine alone is engineered competence | Low/medium, zero inference, small ASTs; strongest missing cost/benefit baseline |
| Counterexample-guided applicability learning | Can reduce repeated mistake classes; risks poisoning and over-abstention | Direct learning path if feedback and representation are qualified | Medium/high; replay/storage and optionally local calls; should follow a trustworthy authority interface |
| Explicit contracts + bounded semantic matching | Can cover alpha/helper/ownership cases with checked intent | Contract acquisition remains separate | Medium/high; record/schema and limited analysis work; no external model required |
| Binding-aware intermediate representation | Helps substitutions and shared analysis across syntax | Generic IR is scaffolding, not acquired semantics | Highest initial cost if generalized to Python; reject unsupported constructs instead of building this first |
| Retrieval + local reasoning + external-to-model authorization | Broad proposal potential; explanations may still be wrong | Possible acquisition proposer, unqualified today | Additional local inference/context/latency; no subscription dependence; not needed for the first comparison |
| Minimal hybrid | Existing ledger, trusted current requirements, bounded proposals, independent acceptance and evidence journal | Leaves a clear place for an acquired record to matter | Best surviving direction, **provided it must beat the cheaper proposal baseline** |

**Could simpler be comparable? SUPPORTED INFERENCE: yes, plausibly.** The current cases largely exercise one algebraic sign edit; much of the safety improvement may come from original/repaired verification. This has not been measured against a simpler generator. Do not pay for a binding engine before that comparison can change the decision.

**Is separating proposals and authority sufficient? No.** It fixes an authority conflation, but safe reuse also needs trustworthy intent/observations. Autonomous improvement further requires acquisition beyond AST-difference storage. That is an acquisition-interface/algorithm revision, not evidence the ledger should be discarded.

**Keep VSL? Yes, conditionally.** Existing write-once versions and state ordering are useful foundations. They do not authenticate evidence truth: transition methods receive an evidence string from a trusted caller. Keep learned data inert and authority external; qualify schema/interpreter migration and version-specific outcome attribution before using feedback to revise records. No promotion or lifecycle action was performed here.

## 8. Provenance and reproducibility review

New [Python 3.12 recheck](sac1_adversarial_review_20261007/historical_recheck_3.12.json) and [3.13 recheck](sac1_adversarial_review_20261007/historical_recheck_3.13.json) were independently computed from current immutable skill records and raw acquisition pools. Only AST extraction ran; no candidate body was executed.

**DIRECTLY VERIFIED scope:** all twelve records under `memory/**/skills/*.json`: nine Skill A versions/copies and two PIT2 versions have a failing index/hash disagreement; one Skill B record does not. All twelve passing hashes agree. These are two acquisition-path defects propagated across versions, not eleven independent skill acquisitions.

**DIRECTLY VERIFIED mechanism:** [harness](../app/experiments/skill_ledger/harness.py) acquisition/re-extraction chooses `used_pair` but hashes `failing[0]`/`passing[0]`; [PIT2](../app/experiments/prospective_invariance_test_2/pit2_run.py) repeats this. Skill A selects 1/3 but stores failing candidate 0's hash. PIT2 selects 3/1 but likewise stores 0's failing hash. [Skill B acquisition](../app/experiments/skill_ledger/accumulation.py) hashes its selected pair objects correctly. This is source-supported, not speculation about an author or intent.

All twelve selected pairs reproduce their stored edit fields under pinned Python 3.12.13. Nine do under system Python 3.13.5; B and PIT2 dumps differ because empty AST fields are serialized differently. Python documents `ast.dump`'s version-dependent behavior and 3.13 `show_empty`. [Python documentation](https://docs.python.org/3.13/library/ast.html#ast.dump). **SUPPORTED INFERENCE:** current pinned-interpreter results are not invalidated by this portability failure; unqualified interpreter upgrades would be unsafe. Do not normalize historical bytes to make them appear portable.

**Consequences for causal claims:** the assertion that the stored failing hash names the selected failing candidate is false. Reproduction from that hash alone is unsound. Raw selected pairs still reconstruct the edit, and direct original/repaired oracle records remain evidence for bounded effects. The prospective contamination filter hashes all raw acquisition bodies, so it does not rely solely on the wrong metadata field.

The older 4/4 TRUE versus 0/4 substitution result also has an **independent limitation**: [prospective_transfer.py](../app/experiments/skill_ledger/prospective_transfer.py) regenerates code in each arm from seeds, and its result tables retain seeds/indices/outcomes rather than per-arm source bodies. Those tables alone cannot prove byte-identical paired candidates. This is not caused by the index/hash bug, and must not be “repaired” by assuming determinism. Later BJQ's exact-body evidence—G 6→20/20, H 20→9/20—and the recognition matrix support narrower mechanistic effects without relying on that assumption. No new general learning claim follows.

Recommended **append-only correction**, not performed: for each affected immutable record, add a correction object with old record hash, source pool hash/path, selected indices, actual selected-body hashes, original erroneous hashes, extractor/schema/interpreter hashes and independently reproduced edit-field verdict. Preserve the original artifact and lifecycle. Future acquisition must derive index and hash from the same selected-pair object and reject disagreement before saving. A new production record or lifecycle transition would require separate explicit authorization; metadata correction is not capability requalification.

## 9. Smallest justified successor and implementation proposal

**Recommendation only; no authorization or new freeze is claimed.** Design **SAC-1R2** separately. Do not patch SAC-1 v1, rerun RNU, or generate new qualification answers in this review.

### Required design revisions before an implementation gate can pass

1. Specify the origin, schema, version and conflict policy of the authoritative task contract. Skill-derived fields may constrain a proposal, never weaken task requirements. Missing/conflicting/stale facts yield explicit UNKNOWN or INVALID_CONTRACT.
2. Define observational scope: final value preservation versus stronger ownership/effect obligations; exact numeric/type semantics; supported program subset and its enforced rejection boundary. Correct the infinite-domain claim; include singleton and other declared edges.
3. Define separate serializable inputs for proposer and verifier. Proposer receives source, current contract and permitted inert repair records; no labels, witnesses, hidden expected values or journal access. Freeze one proposal budget and feedback policy per comparison.
4. Add the cheap same-verifier baseline. For the smallest comparison, use a common bounded proposal/evaluation pipeline with a generic deterministic fallback; vary access to the **human-supplied semantic record** only. This tests engineered record value, not learning. Original unchanged VSL can remain a disclosed descriptive reference rather than another expensive main arm.
5. Freeze implementations before a separate custodian instantiates the scored cases. Use semantic recombinations and counterbalanced live-site positions, not just opaque renaming. Include contradictory/stale contract controls and reject unsupported shadowing/effects. Keep the old sixteen cases disclosed.
6. Predeclare interpretation if the cheap baseline ties/wins: retain the simpler pipeline, do not claim semantic-contract machinery was necessary. Define C-specific unsafe-acceptance stops; baseline defects are measurements, not automatic apparatus failures.

### Minimum research-only components, if later approved

| Component | Exact responsibility / boundary |
|---|---|
| Inert task/repair record validators | Parse bounded data, preserve unknowns, bind task/source/schema hashes, reject conflicts. No model-written executable oracle or arbitrary lifecycle changes. |
| Bounded proposal adapter | At most two edit proposals under a newly frozen equal budget. Existing matcher available unchanged; generic one-site sign-edit proposals provide the cheap fallback. Optional semantic record may prioritize/check sites, with all assumptions exposed. No general IR. |
| Restricted binding/effect checker | Resolve only local definitions, known builtin calls and supported local helper/copy mechanisms. Unsupported alias/shadowing/dynamic behavior abstains. Add only the rules the new declared grammar needs, not per-case exceptions. |
| Independent acceptance controller | Obtain authoritative contract; score original/proposal on permitted decision evidence; require complete declared obligations and an actual improvement; otherwise retain original. Hidden scoring never chooses the edit. |
| Immutable decision journal | Source/record/contract/patch/checker hashes, input visibility, site/binding claims, outcomes, abstention reasons, costs and exact accepted source. Fsync before teardown; per-version evidence, no production logs. |
| Replay harness | Fresh disposable process loads the same immutable record and reproduces the decision; no hidden controller cache. No live service restart. |

Reuse unchanged: VSL historical records and matcher as references; E0.1 interpreter/worker/comparison; qualified operation-aware controller guard, confined profile design and durable observer. New room paths and wrapper semantics require the existing preflight plus any explicitly changed observation qualification. Do not assume old room success qualifies arbitrary new paths or journal placement.

Authority output should be one of `ACCEPT_EXACT_PATCH`, `ABSTAIN_UNKNOWN`, `REJECT_UNSAFE`, `REJECT_NO_IMPROVEMENT`, or `MEASUREMENT_ERROR`, with distinct task-result and authorization fields. A declined repair retains the original; if the original is wrong, it remains an unsolved task rather than a success credited to safety.

Estimated effort **SUPPORTED INFERENCE / uncertain planning range**: 2–4 hours for a precise successor design and review; roughly 1–2 focused engineering days for the smallest isolated prototype after approval, with a stop if it grows into general Python analysis. Zero inference initially; serial Python/AST work, likely below 1 GiB incremental working memory but not measured. Reuse existing hardware; no download, paid service or relay required. The point of the cheap baseline is to avoid paying the more elaborate engineering cost without evidence.

## 10. Explicit sequential gates

These are **recommended planning caps and acceptance rules**, not a frozen execution protocol or authorization. Each execution gate needs its own reviewed freeze. No failed gate may be bypassed by proceeding to a later claim.

| Gate | Prerequisite / pass criteria | Budget | Failure and stop |
|---|---|---|---|
| **1 Architecture** | Resolve F1–F5; human approves exact trust/schema/visibility/observation contracts and simpler baseline; independently review oracle intent | Read-only design/review, zero inference/candidates; one bounded revision | No trustworthy task authority or implementable scope → HOLD; no SAC build. **Currently not passed.** |
| **2 Engineered authority** | Independently held successor with 16 units: eight repairable and eight unsafe/irrelevant/unknown; at least six positives repaired, coverage in each declared positive stratum, zero harmful/irrelevant acceptance, all unknown/invalid contracts declined. Beat the matched cheap baseline in correct fixes or cost at equal safety, otherwise choose simpler design | Zero inference; ≤2 proposals/item/condition; ≤5,000 child calls including truth checks; ≤30 min, serial | One unsafe acceptance by the proposed authority, oracle contradiction, leakage or integrity failure → stop. Known baseline incorrectness is recorded separately. No holdout-driven patch. |
| **3 Acquisition** | Gate 2 representation/engine frozen; four acquisition episodes with independently varied evidence. ≥3/4 produce valid traceable records and pass unseen discriminants; no unsafe acceptance; same-model no-experience control must not explain the benefit | Suggested cap 16 local calls total across acquisition and matched controls; ≤20 min generation, fixed verifier budget | Manual semantic-answer substitution, invalid feedback, no identifiable experience-derived contribution or all-refusal strategy → do not advance |
| **4 Prospective transfer** | Acquired records frozen before independently selected new implementations. Same capable model, tools, contracts and budgets with/without retained record. Proposed screen: ≥4 beneficial task discordances on 24 paired tasks, zero harmful accepted repairs, with cost reported; no population claim from designed cases | ≤48 local calls, one/arm/task; ≤30 min generation; evaluator cap frozen separately | No benefit, harmful authority, attribution leakage or unequal budgets → reject advancement; do not add favorable cases |
| **5 Persistence** | Fresh isolated process reloads acquired record, engine and evidence; all frozen diagnostic decisions/outcomes reproduce; no-record ablation removes demonstrated benefit | Deterministic replay preferred; ≤8 local calls only if indispensable and separately frozen; ≤10 min | Cached prompts/state explain benefit, schema mismatch or lost authority evidence → bounded persistence repair, not accumulation |
| **6 Net retained utility** | Fresh workload independently selected from intended work, never used in development. Raw paired correctness, harm, abstention and cost. Predefine practical benefit margin and uncertainty method from Gate-4 data before this new workload is seen | Initial planning ceiling 48 paired tasks /96 local calls, same budgets; no sample expansion after outcomes; expected-time cap frozen from measured latency | Integrity/isolation failure stops execution. Ordinary task errors/harms are counted, not selectively excluded. Positive only if the frozen practical/uncertainty criterion passes; otherwise negative, neutral only if justified, or inconclusive |

Gate-2 zero harm is a qualification threshold, not proof of a zero-risk system. Gate-6 measurement must permit net learning to lose and must retain every eligible harm. Repeated deterministic calls are not additional samples. No hardware expenditure or skill-library expansion follows from a gate pass.

**Abandonment criterion:** abandon the elaborate semantic-matcher direction if it cannot meet bounded safety/coverage without case-specific patches, or if the cheaper same-verifier baseline matches its benefit at materially lower cost. Keep independently useful proposal/verification safeguards. Abandon the claim that this representation supports learning if, after a qualified engineered stage, acquired records repeatedly fail an equal-budget no-experience comparison under a single preregistered bounded acquisition/transfer test. Do not infer from that failure that all learning is impossible.

## 11. Closing integrity and reproducibility

**DIRECTLY VERIFIED:** [closing record](sac1_adversarial_review_20261007/closing.json), 22:25:22 PDT, confirms all **488 pinned authority paths unchanged**. HEAD, branch, cached origin/main, the fourteen-path tracked modification set and empty staging are preserved. [Closing process identities](sac1_adversarial_review_20261007/closing_processes.txt) exactly match the opening snapshot. No service was signaled or restarted.

Four prospectively separated live mutable files changed while the review ran: FAISS index, memory metadata, RiverBrain and self-model. Their before/after hashes, size and mtime are recorded. This review did not write them; hashes do not identify their writer. They were not scientific inputs. The runtime temporary self-edit file was also observed and did not change in this interval.

Intentional mutations are exclusively this new report and additive files under `audits/sac1_adversarial_review_20261007/`: snapshot/reconstruction code, integrity records, historical recounts and the review evidence manifest. No SAC-1 protocol, fixture, recognizer, verifier, ledger record, lifecycle or historical report was changed. No successor case or implementation was created. **Additional experimental model calls: 0; candidate executions: 0; SAC-1 recognition/authorization trials: 0.** Nothing staged, committed or pushed.

Historical provenance can be independently reconstructed with [review_evidence.py](sac1_adversarial_review_20261007/review_evidence.py), `history` mode, using each reported interpreter. To avoid overwriting any audit evidence, put a copy of that review script in a new directory directly under this repository's `audits/`; its exclusive-create output then remains additive. It executes only the inspected pure AST extractor over historical source strings, never those candidate programs. The [raw recount](sac1_adversarial_review_20261007/source_and_raw_recount.json) lists the original oracle files and twelve equivalent historical boundary verdict pairs. [Acquisition recount](sac1_adversarial_review_20261007/acquisition_recount.json) independently confirms the small prior-library and invalid-revision counts.

The evidence manifest pins the completed review bundle. Source-level vulnerabilities are not presented as executed exploits, and predicted baseline performance is not presented as a result.

## 12. Final decision questions

**Q1. Strongest concrete failure reason?** A correlated wrong task contract can make generator and verifier agree on a harmful repair. Current SAC-1 uses one supplied contract source for both, and does not qualify acquiring or validating that authority.

**Q2. Semantic authority or test-specific engineering?** It tests observable outcomes of an engineered package on disclosed targeted examples. It can be overfit and could plausibly be passed mainly through simple proposals plus verification. It does not uniquely establish semantic recognition, autonomous acquisition or unseen transfer.

**Q3. What prevents autonomous acquisition now?** No qualified mechanism turns experience into independently validated semantic conditions/bindings/limitations. A failed/passed AST pair underdetermines those conditions; missing current task intent cannot be inferred safely from an old skill. Feedback authority and a fixed expressible hypothesis space are missing parts of the bridge.

**Q4. Can it distinguish correct from plausible harmful repair?** On specified observations, if task requirements and oracle are correct, input/effect scope is enforced and the proposal cannot influence expected answers. Finite passes do not authorize arbitrary inputs, hidden side effects or a wrong contract. Those assumptions must be tested, not supplied by model confidence.

**Q5. Smallest useful improvement?** Add independent disposable original/proposal acceptance to a bounded proposal mechanism and test a cheap generic fallback for missed syntax. Let semantic records earn their extra cost against that fallback before building a semantic analyzer. This is an engineered safety/coverage hypothesis, not yet learned improvement.

**Q6. Evidence needed to implement?** A reviewed successor design resolving authority provenance, observation scope, input visibility, baseline fairness, holdout custody and stop rules; oracle review; and explicit human implementation authorization. No new code is required to settle those design decisions. This review does not grant that authorization.

**Q7. What would warrant abandonment?** Unsafe acceptance within the declared bounded grammar, repeated need for example-specific patches, or no advantage over the cheaper same-verifier baseline. At acquisition/transfer gates, absence of an experience-dependent gain warrants stopping that learning route rather than inflating the library.

**Q8. Most efficient path to retained net utility?** Repair the experimental design, compare the smallest authority pipeline with the cheap baseline, qualify acquisition only if the representation earns it, test actual acquired-state ablation on fresh work, verify reload, then run one independently selected net-utility comparison. Preserve negative results at each stop; do not insert more accumulation experiments to avoid this chain.

**Final disposition: REVISE. Return for human review. SAC-1 implementation and execution remain unauthorized.**
