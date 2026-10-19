# SAC-1R2 final adversarial implementation-readiness review

October 8, 2026. **Final disposition: REVISE. The existing implementation/execution HOLD remains in force. Neither is authorized.**

## 1. Executive verdict

The comparison is coherent, but it is not ready to implement as an architectural investment test. Its main remaining scientific weakness is an unsettled baseline: the common analyzer exposes the facts needed for a cheap polarity-consistency rule, while B's specified ranking does not require that rule. A C win could therefore reward moving an ordinary engineering rule into a record rather than justify additional semantic-record machinery.

The resource arithmetic also needs a more precise ledger, not an automatic increase in compute. The published 5,376 count assumes original-result cache reuse that is not assured across custody and two differently confined rooms. However, accounting for the five units explicitly prohibited from execution gives a conservative **4,752 candidate launches without original caching**, plus at most **32 proposer launches**. Thus the 6,000 main cap can fit the stated small design. **Thirty-minute completion is not established:** a call ceiling and a ten-second per-call deadline do not imply that completion bound.

The task-authority hierarchy is a credible design for conditional, sampled conformance. It is not a qualified oracle yet. No independent custodian, oracle reviewer or demonstrably separate evaluation account has been established. The current assistant authored the prior design: this review independently checks sources and arithmetic but does **not** supply independent reviewer identity or held-out custody.

| Required verdict | Finding |
|---|---|
| Baseline competence | **REVISE BEFORE FREEZE** — resolve the ordinary polarity rule and exact ranking before reviewing any held-out result. |
| Oracle/authority | **HOLD** — conditionally adequate hierarchy; actual authority approvals, oracle and new observation qualification absent. |
| Resource feasibility | **REVISE ACCOUNTING OR CAPS BEFORE FREEZE** — revise accounting first; retain caps provisionally. Timing/memory feasibility remains **UNKNOWN UNTIL NON-SCORED QUALIFICATION**. |
| Custody readiness | **Not established** — a separate-session or different-model label is insufficient. |
| Overall | **REVISE**, with independent-custody HOLD preserved. No architecture replacement, implementation or scored run recommended now. |

The smallest next action is one separately versioned design amendment resolving baseline competence, cache/phase accounting and decision semantics, reviewed alongside an accepted custody plan. Do not open another general architecture investigation. If the cheap rule subsumes the record's only proposed contribution, retain the cheap proposer/verifier design and postpone the record interpreter rather than engineer an artificial C advantage.

Evidence labels: **DIRECTLY VERIFIED** = inspected source/bytes, existing raw result fields or arithmetic; **SUPPORTED INFERENCE** = follows from identified mechanisms, not newly executed; **UNTESTED HYPOTHESIS** = prospective performance; **BLOCKED / UNKNOWN** = evidence/prerequisite absent. Future recommendations below are not modifications to the existing design or an execution freeze.

## 2. Reconstruction and evidence boundary

### Exact proposed comparison

**DIRECTLY VERIFIED in the [SAC-1R2 design](2026-10-08_sac1r2_design_and_experimental_gate.md), sections 4–9:**

- B receives the source, current authoritative requirements and shared analysis. It enumerates one-site numeric-sign edits, eliminates ineligible sites, ranks live key sites, then map-derived sites, then return distance, then source position. No semantic record.
- C is the same engine, analyzer, candidate universe, operator set, fallback and verifier, with a frozen investigator-authored conditional-priority record. The record may reorder proposals; it supplies neither current-task authority nor an independent acceptance rule.
- Both commit at most two one-site proposals relative to the original, without verifier feedback. Neither may compose repairs or adapt after hidden scoring.
- The common controller validates authority, scope, bindings and ownership, evaluates the original on 24 decision inputs, and accepts the first committed proposal that satisfies the complete decision observations with an original failure fixed. Otherwise it keeps the original.
- After both decisions/output hashes are sealed, a hidden scorer evaluates 24 other inputs. Hidden results never choose a replacement edit. A remains a historical descriptive reference, not an executed third arm.
- Sixteen designed units comprise eight repairable positives and eight negative/refusal units. These are a mechanistic engineering screen, not an independently sampled natural workload or sixteen independent population observations.

The intended treatment is access to **engineered applicability/priority information**, not learning. Equal verifier code is necessary but not sufficient for matching: test inputs, cache availability, controller configuration, accessible files and accounting must also match.

| Potential accidental asymmetry | Required audit evidence before scoring |
|---|---|
| C gets additional task facts, corrected ownership or binding hints through a record | Canonical B/C requests identical except record array and neutral IDs; current requirements and extracted facts separately hashed. |
| Different eligibility/candidate universes | Journal common pre-ranking site universe, operator and analyzer hashes; C cannot invent candidates or relax eligibility. |
| C-only semantic analysis hidden in the common engine | Inventory facts computed, their provenance and cost; common computation charged to both, C-specific work charged to C. |
| Different expected values or checker rules | Same contract/oracle/observer/checker manifests and per-input expected commitments; no arm-based verifier branch. |
| C changes ordering and displaces B proposals | Legitimate treatment effect within two slots, but not a guarantee of additive behavior. Preserve both full enumerations and selected proposals. |
| Feedback or hidden-original cache leaks | No feedback before commitment; decision and hidden data separated; hidden cache must not enter the acceptance service. |
| Different rooms, runtimes, cache hits or failure policy | Room/profile/argv/environment hashes, paired scheduling, per-arm logical and physical execution counters, identical timeout and scoring policy. |
| Different author effort or semantic knowledge | Record authorship/curation and special-case implementation time disclosed; a C gain is not evidence that Echo learned its content. |
| Journals or opposite-arm results accessible to a proposer | OS-enforced denial demonstrated in each proposer room, separately from candidate denial. |

### Historical facts independently checked

**DIRECTLY VERIFIED:** the current [matcher](../app/core/skill_ledger/matcher.py) still uses local AST/context matching and first-match replacement; [runtime](../app/core/skill_ledger/runtime.py) `consult` accepts no interpreted task contract; [adapter](../app/core/skill_ledger/echo_adapter.py) explicitly labels production outcomes `f1_f2_safety_only`. [Schema transitions](../app/core/skill_ledger/schemas.py) persist versions and caller-supplied evidence text; they do not independently prove the evidence true. [Acquisition harness](../app/experiments/skill_ledger/harness.py) selects `used_pair` but hashes `failing[0]`, explaining the historical attribution defect. None of those APIs was invoked.

Fresh raw-JSON recount in [raw_recheck.json](sac1r2_readiness_20261008/raw_recheck.json): historical recognition TP4/FN9/TN5/FP6, with one separately recorded natural lead excluded from that confusion matrix; RNU 44 tasks, 25 correct/19 incorrect each arm, zero applications, INCONCLUSIVE; historical boundary 28 calls and twelve equal reference/confined verdict pairs. These do not show a SAC-1R2 result. Eleven Skill A/PIT2 record discrepancies remain historical integrity findings, not corrected authority; the prior checked raw reconstruction remains pinned. No new acquisition or AST-extraction execution was performed.

The [earlier review](2026-10-07_sac1_independent_adversarial_review.md), [architecture report](2026-10-07_semantic_competence_repair_authority_architecture.md) and immutable [SAC-1 v1 protocol](semantic_authority_20261007/protocol.md) were inspected. The 4/4-versus-0/4 prospective tables still do not independently establish byte-identical per-arm candidates. The public historical protocol is disclosed material; no hidden answer matrix was opened or generated in this review.

**DIRECTLY VERIFIED source limits:** [E0.1](../app/experiments/rung1/trusted_evaluator.py) compares caller-supplied expectations, distinguishes bool/int but otherwise uses Python equality, and launches a separate worker through `sandbox-exec`. [Worker](../app/experiments/rung1/candidate_worker.py), candidate and observer share a child address space. The [durable observer](retained_utility_20261006/durable_evaluator.py) records raw child return and comparison before cleanup; [guard v3](retained_utility_20261006/guard_v3.py) resolves the unlink directory entry without following its final symlink target. Historical cleanup controls intentionally reproduced the old cleanup failure while preserving child results; their `qualified` flag is not evidence that the old guard permitted successful cleanup. New proposer/observer/root qualification remains necessary.

## 3. Baseline competence

**Verdict: REVISE BEFORE FREEZE.** The proposed B is substantially better than the historical matcher: it has generic edits, live-site filtering, helper/binding analysis and equal tests. It is not an intentionally disabled control. Nevertheless, its exact competence is left undecided by the sentence allowing a polarity check to be added if a reviewer thinks it belongs. That decision is central to the architectural comparison and must be resolved before implementation/holdout commitments.

### Concrete cheap alternative, derived without candidate execution

**DIRECTLY VERIFIED design facts:** the common analyzer is proposed to expose map orientation relative to the current contract, sort direction, first/last selection, current sign, unique definitions and return dependency.

**SUPPORTED INFERENCE, bounded algebra:** where one live monotone numeric tag component decides a tie and the relevant other key components are equal, choose two tags `g` and `b` with `g` preferred by the current task. Let `d = rank(g) - rank(b)`; let `s` be the component's effective sign. Let `q = -1` when the returned selection minimizes the key (ascending/first or descending/last), and `q = +1` when it maximizes it. Correct direction requires:

`q × s × d > 0`.

If this fails consistently across the contract's tag pairs, flipping the sign is a deterministic hypothesis for correcting that component. This uses current source and current task facts, not historical Skill A or test answers. No table of scored cases is needed. Unknown/nonmonotone maps, interacting sorts, ambiguous reaching definitions or unestablished key precedence must remain unknown; this is not a proof that one edit repairs arbitrary code. The independent verifier is still required.

This identifies a concrete low-cost rival to C's eight-clause priority table. **UNTESTED HYPOTHESIS:** its runtime repair rate across the proposed cases; no rival or benchmark was implemented. **SUPPORTED INFERENCE:** omitting this ordinary rule while giving its equivalent to C creates avoidable uncertainty about whether record machinery deserves investment.

| Challenge | Assessment |
|---|---|
| Does the analyzer already contain the answer? | For the simple known-polarity subcase, its facts plus the above relation determine direction. Extraction remains substantial engineered scaffolding. Do not count it as acquired knowledge. Complex supported paths may still need search; their behavior is untested. |
| Should C's rule belong in B? | The ordinary local consistency rule is a credible cheap-baseline feature. Resolve it in the shared generic ordering, not by suppressing it to preserve room for C. If C adds nothing beyond it, that is useful evidence to postpone C. |
| Is two proposals fair? | Equal two-slot budgets are a legitimate fixed-budget search comparison. They do not compare unbounded repair ability. With more than two eligible sites, arbitrary tie-breaks become consequential. |
| Does source-order balancing suffice? | No. Balancing a live site before/after a dead site does not balance B's competition: the shared analyzer has already removed dead sites. The relevant ordering is among **eligible live sites**, after filtering and normalization. |
| Can C exploit construction regularities? | Yes in principle: fixed site counts, key-component arrangement, or helper placement can correlate with the useful edit. Fresh names/hashes do not remove those regularities. No exploitation has been observed. |
| Does generic fallback guarantee no regression? | No. C's two promoted proposals can displace a useful B fallback. The no-lost-success threshold tests this possibility; it is not a property of the architecture. |
| Can C's information be encoded more simply? | Yes, plausibly as a direct ordinary priority rule using the same facts. A data interpreter may be useful for future updates, but this engineering screen must not assume that benefit. |

**Minimum correction:** in a separately versioned amendment, require the cheap polarity-consistency priority for the resolvable subcase in common B/C logic, retain the existing generic fallback elsewhere, and specify tie-breaking precisely. Alternatively an independent reviewer must document a concrete reason it is not cheap or applicable; current text supplies none. Do not change the candidate universe, add a third arm or widen the grammar to manufacture a C advantage.

The same amendment should make site-count allocation and post-filter eligible-site positional counterbalancing exact. Custodian selection must not inspect B/C success or choose only cases where B's preferred site is wrong. Freeze the allocation procedure, not new source bodies here. If the declared grammar cannot produce a meaningful remaining distinction without contrived distractors, stop at design and keep the simpler proposal/verification route. A competent baseline leaving no headroom is not an experimental failure to be repaired.

## 4. Oracle authority and conceptual failure scenarios

**Verdict: HOLD.** The proposed hierarchy is sufficient in principle for the narrowly declared empirical claim, but actual approvals, oracle implementation and observer qualification are absent. The design has materially improved on letting a skill authorize itself. Sharing a *correct, independently established* specification is appropriate; process diversity is not required to invent a different intended task.

Task intent is established by the independent synthetic-task owner/custodian under an approved task-family specification. A separate reviewer must check both structured translation and oracle against that source, before arm outcomes. The current contract is not learned applicability information. Proposers cannot modify it; records cannot supply expected values or mark their own postconditions satisfied. Contract/source/revision hashes establish binding and freshness, not truth. Human approval strings inside untrusted payloads have no authority.

**DIRECTLY VERIFIED design responses:** `UNKNOWN_CONTRACT`, `CONFLICTING_CONTRACT`, `STALE_CONTRACT` and `UNSUPPORTED_CONTRACT` all prevent repair; flags are retained and no skill-derived defaults fill missing facts. Oracle disagreement or inconsistent witness validation stops rather than revises expected values after outcomes. These are proposed fail-closed requirements, not tested implementations.

The following are conceptual mechanisms, not generated challenge cases or executed attacks:

| Failure scenario | Does the design prevent it? | Residual qualification/limit |
|---|---|---|
| Record recommends historical priority while current task reverses it | **By design**, current contract controls oracle and shared acceptance; record cannot overwrite it. | Must test record non-authority. A source-identical contract twin is useful when independently held. |
| Task translation and oracle both reverse the owner's intended ranking | **Not automatically.** Internally consistent wrong authority can pass every comparison. | Separate owner-spec translation/oracle review. For synthetic tasks the approved formal specification defines intent; do not posit hidden intent beyond it, but detect disagreement with the approved source. |
| Wrong final name tie-break | Pairwise oracle might repeat a translation error even if tag checks pass. | Review this obligation separately; both partitions include name ties. Passing sampled ties is not all-input proof. |
| Ownership omitted or weakened to final equality | Missing declared fields require abstention, but an owner-approved incomplete requirement may evade schema checks. | Reject identity/transient-effect requirements outside scope; source checker must independently prohibit input/inner-entry writes. Do not equate unchanged final JSON with full ownership. |
| Singleton behavior wrong | Singleton observations are now explicitly required in both partitions. | Three samples per partition do not prove all singleton behavior. Missing required coverage is a protocol failure, not a score exclusion. |
| Binding resolver names the wrong live site | Controller recomputes bindings, but reuse of the same mistaken analysis can correlate proposer/controller errors. | Independent behavioral oracle may catch it; forged-binding controls and source review are necessary. Recomputing with identical flawed code is not independent semantic evidence. |
| Unsupported shadowing or dynamic effects admitted as safe | Grammar mandates rejection. | Checker soundness is unqualified. New observer does not observe all effects; OS denial protects external state but does not prove intended semantics. |
| Repair passes decision and hidden samples but violates another input/requirement | **Possible.** Finite observations and a restricted checker do not prove general correctness. | Limit the claim to specified observations and enforced subset; do not promote to production authority. |
| Hidden custodian results leak into acceptance through caching | Visibility policy forbids it, but cache partition/access is not fully specified. | Separate decision and hidden caches/journals; simplest option is to re-evaluate originals rather than import a mixed cache. Hidden originals are released only to post-seal scorer. |

**Necessary small clarification:** the cache policy must explicitly preserve both room/isolation identity and phase secrecy. Existing [boundary construction](retained_utility_20261006/boundary_v4.py) substitutes different absolute room paths into profiles. Different profile hashes cannot satisfy the proposed exact cache key. A custody machine may also have different interpreter/profile identity. Do not silently drop profile identity for a hit. Do not make hidden original observations available to the acceptance service merely to save calls. The no-cache resource bound below avoids needing this optimization.

A legitimate pass claim would be: **under approved task requirements, this frozen engineered record increased completed repairs over the approved generic baseline by the preregistered margin on this independently held, constructed sixteen-unit screen, with zero observed C harm within the stated observations and costs.** It would not establish universal task correctness, verifier completeness, record-format superiority, acquisition, production readiness or natural retained net utility.

## 5. Independent resource accounting

**Resource verdict: REVISE ACCOUNTING OR CAPS BEFORE FREEZE.** The correction can retain the numeric caps provisionally. Actual timing/memory feasibility is **UNKNOWN UNTIL NON-SCORED QUALIFICATION**. Arithmetic and assumptions are preserved in [resource_accounting.json](sac1r2_readiness_20261008/resource_accounting.json).

### Logical evaluations versus physical launches

An E0.1 invocation requests one candidate computation and ordinarily launches one `sandbox-exec`/Python execution chain through `subprocess.run`; a failure before launch creates a logical attempt but no executed candidate. The counter must distinguish requested evaluations, cache hits, launch attempts, actual child starts, returned outcomes and candidate executions. A cached observation is not a fresh launch or timing sample. Proposer subprocesses are additional launches. Reference/confined controls execute separately. No such calls were made in this review.

The published arithmetic is correct **under its cache assumption**:

| Published component | Calculation | Calls |
|---|---:|---:|
| Up to two instantiations for each of sixteen custody slots, original + witness, both partitions | 32 × 2 × 48 | 3,072 |
| Two proposals in each arm, decision partition | 16 × 2 × 2 × 24 | 1,536 |
| Final output in each arm, hidden partition | 16 × 2 × 24 | 768 |
| Total / margin to 6,000 | | **5,376 / 624** |

Missing as explicit terms: original evaluations in the scored rooms when cache keys do not match, proposer launches, exact replay/preflight allocation and shared-controller overhead. If all sixteen units were executable and originals needed 48 checks in both rooms, the loose bound becomes **6,912 candidate launches**, not 5,376. **That is a warning about the assumption, not proof that this actual sixteen-unit design exceeds 6,000.**

The current design explicitly prohibits candidate execution for five slots: missing, conflicting and stale contract; ownership violation; unsupported shadow. Treating them as executable would violate its own rules. Eight positives plus three potentially executable known-contract negatives leave **eleven** executable slots. The following tighter count requires no cross-room or custody cache and credits no proposal early-stop savings:

| Tight component | Calculation | Candidate launches |
|---|---:|---:|
| Custodian originals, max two instantiations in each executable slot | 11 × 2 × 48 | 1,056 |
| Custodian witnesses, same conservative maximum | 11 × 2 × 48 | 1,056 |
| Original decision observations, independently in B/C rooms | 11 × 2 × 24 | 528 |
| Original hidden observations, independently in B/C rooms | 11 × 2 × 24 | 528 |
| Proposed repairs, two per arm, all decision inputs | 11 × 2 × 2 × 24 | 1,056 |
| Final hidden output, separately even if it equals original | 11 × 2 × 24 | 528 |
| Candidate total | | **4,752** |
| Main proposer-process reserve, including refusal slots conservatively | 16 × 2 | **32** |
| Main boundary-launch total / margin | | **4,784 / 1,216** |

These are **DIRECTLY VERIFIED arithmetic bounds conditional on the documented execution policy**, not predicted actual call counts. Failed custody instantiations are included. A correct original, static rejection, first failed proposal test, early accepted proposal or cached output can reduce the actual count, but no such reduction is needed for this bound. No third arm, post-score rerun, multiple witnesses per instantiation or extra ground-truth search is allowed. Reviewer replay of candidates is not free; use existing raw evidence or count any separately authorized replay explicitly. If the five refusal policies, two-instantiation limit or witness count changes, recalculate prospectively.

### Qualification and replay

The 128-launch qualification cap is **separate** from 6,000. Historical reference/confined comparisons alone require `2 rooms × 6 domains × 2 modes = 24` calls. Proposer/candidate filesystem probes, actual successful execution, transport, cleanup, exact-type/mutation observer checks, static-contract controls and reload replay are additional. Current design lists them but does not fix their individual allocation.

A feasible **proposed allocation ceiling**, not new fixtures or authorization, is: 24 historical semantic comparisons; 4 combined filesystem probes (two roles/two rooms); 4 successful transport/execution controls; 16 new observer comparisons (four obligations/two rooms/reference-and-confined); 16 grouped schema/binding/authority rejection process controls; 8 transport/cleanup failure/success controls; 8 fresh proposer replay launches; 16 public candidate replay calls. Total **96**, leaving 32 within 128. This is an allocation proposal: a reviewer must map every required control to a manifest entry and ensure grouping preserves individual evidence. If actual qualification cannot fit, stop for a prospective amendment; do not omit controls to fit the arithmetic.

No static rejection needs a candidate run, but running its validator in a fresh confined proposer process still consumes a process launch. Bookkeeping done in the controller does not launch a child; an external monitoring command does. Freeze counters for candidate boundary calls, proposer/validator calls, monitoring/control processes and top-level phase invocations separately. Do not count `sandbox-exec` replacing itself with Python as two independent candidate evaluations. If the main/qualification ceiling means all child processes, reserve/count them explicitly; the current term “child calls” is insufficiently precise.

**Minimal accounting correction:** use the no-cache 4,784 main boundary-launch bound; keep 6,000 as the main ceiling and 128 as the separate qualification ceiling; place public replay inside the latter rather than spend the main margin opportunistically. Freeze exact permitted invocations and counters. The unused margin grants no authority for new experiments or retries.

### Time, memory and I/O

**DIRECTLY VERIFIED arithmetic:** 4,752 candidates at a ten-second deadline have a crude upper envelope of **47,520 seconds, 13 h 12 min**, before other costs. The full 6,000 × 10 envelope is 16 h 40 min. These are conservative envelopes, not claims all timeouts can coexist with eligibility and early-failure rules. A timed-out proposal stops after its first failed input, reducing that path's calls. Original/witness validation and other paths can still consume substantial time; a 30-minute worst-case completion guarantee has not been shown. One 24-input original at the per-call deadline already consumes four minutes.

Finishing 4,752 calls in 1,800 seconds requires a mean below **0.379 s/call** before overhead; allowing 32 two-second proposer launches reduces that to **0.365 s/call**, still excluding other controller costs. Historical RNU's recorded evaluation fields average about **0.032 s/call** across 2,112 calls. This makes a short successful run plausible, but it is not a bound for new observers, filesystem durability, load or timeouts. No new benchmark was run.

The separate qualification envelope `128 × 10 = 1,280 s` exceeds its 600-second cap. Qualification contains only a few deliberate timeout controls and can specify shorter timeouts for those controls prospectively, as historical tests did; the exact manifest and measured ordinary overhead are still needed. Do not infer completion from average historical latency or weaken candidate timeouts after seeing outcomes.

**Minimum time clarification:** retain 30 minutes as a hard **machine-execution stop budget**, explicitly not guaranteed completion; distinguish cumulative custody/run machine time from elapsed human review/offline waiting time. Freeze the phase clocks before execution. A runtime cap hit yields incomplete/unqualified evidence, not a negative learning result. No pause for tuning, extra runtime or selective continuation. The two-second proposer limit should include launch, loading, analysis, record processing, serialization and receipt, equally in both arms; define that wall-clock boundary before freezing.

**DIRECTLY VERIFIED I/O mechanism:** a normal durable E0.1 evaluation writes approximately five event files: begin, launch request, child return, trusted comparison and evaluation return. [common_rnu.py](retained_utility_20261006/common_rnu.py) flushes and fsyncs each event file. At 4,752 successful calls that is about **23,760 event files**, plus sources/manifests and cleanup. The final event and setup costs must not disappear from runtime accounting. File fsync here supports evidence surviving ordinary teardown; it is not a newly qualified whole-machine crash-recovery guarantee. Cleanup failure must retain prior results and stop further execution when integrity is uncertain.

**BLOCKED / UNKNOWN memory containment:** the design states a desired RSS below 512 MiB and “resource distress” but supplies no measured limit, monitor interval or enforcement policy. A source/AST bound is not by itself a runtime/serialization memory proof; the new observer must bound tagged encoding and reject unsupported return types before traversing arbitrary structures. E0.1's output-size check occurs after capture, not as a stream-memory bound. Do not solve this with hardware or a general sandbox redesign. Specify a bounded observer output and a monitor/abort policy for research processes only, then qualify it on public controls. Monitoring is a guardrail, not proof that no allocation can exceed a sampled RSS threshold.

Non-scored qualification may establish ordinary throughput, peak observed working sets and durable-journal costs **only after implementation is explicitly authorized**. If those measurements cannot support attempting the frozen workload inside the unchanged caps, stop before generating/using scored cases. Reduce scope only through a reviewed new design, not by dropping difficult outcomes.

## 6. Holdout custody and review readiness

**Verdict: HOLD.** No role acceptance or access proof is present. Different sessions/models with the same readable repository do not satisfy this requirement. This review supplies neither an independent case author nor an independent oracle approver.

| Role / requirement | Required access | Prohibited access or action | Evidence required | Current status / exact next action |
|---|---|---|---|---|
| Architecture designer | Public design, historical evidence | Future hidden set before implementation commitment | Exposure declaration and dated design hash | Design exists; author overlap disclosed. Human must review amendments. |
| Implementer | Public material and disposable development controls | Scored source bodies, seeds, labels, witness edits, expected values and hidden journals before completion | Frozen source manifest; restricted account/tool identity; export/access review | No implementation or assigned implementer. Obtain acceptance and access plan. |
| Independent custodian/task owner | Approved spec, frozen executable bundle, private cases/seed/answers | Implementation changes or outcome-based case selection | Accepted role; precommitted pool/seed manifest; generation/eligibility/rejection log; chain of custody | Unassigned. Identify a willing human/controlled independent process with a distinct decision history and protected storage. |
| Oracle reviewer | Original task requirements, translation, independent oracle and custody validation evidence | Using B/C outcomes to repair expectations; self-certifying an oracle solely authored by them | Accepted role; obligation-by-obligation signoff; oracle/spec hashes and disagreement log | Unassigned. Secure review before scored instantiation/results. |
| Execution controller | Sanitized task/source, decision evidence, frozen shared logic | Hidden scoring data before decision seal; changing implementation or contracts | Exact visibility manifests; permission probes; audit of inherited descriptors/cache/journal flow | Absent. Qualify after separate implementation authorization. |
| Hidden scorer | Sealed decisions and custody-held scoring data | Returning feedback to proposer or changing selected repair | Decision hashes precede scoring events; separate inaccessible hidden journal | Proposed only. Assign ownership/access before execution freeze. |
| Final evidence reviewer | Full committed bundle and unblinded outcomes after run | Tuning on scored results; silently excluding failures | Accepted role, independent interpretation, full inventory and hash reconciliation | Unassigned. Obtain independent review commitment. |

Designer and implementer may overlap with disclosure. The implementer and hidden-case custodian must not. The person solely authoring an oracle cannot be its only independent reviewer. Custodian and final reviewer may overlap if disclosed, but that is not an additional independent validation of the custodian's own choices; final scientific acceptance should include someone not responsible for those choices. Multiple independent processes can enforce access restrictions without creating independent human judgment. Neither identity labels nor hashes prove impartiality.

A separate local OS identity **can** enforce access differences if ownership, ACLs, sandbox/tool permissions, group access and privilege boundaries actually deny the implementer. It is not protection against a party retaining unrestricted administrator/root or physical access to the custody environment. Apple documents OS-enforced permissions and the significance of effective user identity, as well as privileged-access limits. [Apple permissions guide](https://developer.apple.com/library/archive/documentation/Security/Conceptual/AuthenticationAndAuthorizationGuide/Permissions/Permissions.html), [current file-permissions guidance](https://support.apple.com/guide/mac-help/change-permissions-for-files-folders-or-disks-mchlp1203/mac). These documents establish mechanisms, not this machine's current separation.

**Practical preference, SUPPORTED INFERENCE:** an independently controlled offline machine/account is simpler for scientific custody than trying to make the current broad-access development session blind to files on its own machine. The custodian can prepare sealed material offline; execute the frozen bundle under a separate controlled evaluation identity on the M5, keeping both arms on the same hardware; release full evidence only after commitments. No purchase, subscription, network or relay is required. Another machine's validation results must not be silently imported as identical M5/profile cache hits.

Required audit artifacts: role acceptances and conflict/exposure declarations; exact user/group/tool privileges; ownership/ACL/storage/export inventory; synthetic existing-but-denied canary read tests from the actual implementer and proposer identities; positive authorized reads by custodian; no shared history/backup/sync/log path exposing answers; implementation freeze predating case instantiation; sealed seed/eligible/rejected case manifests; no feedback export before commitment; raw execution/access records and post-run disclosure. Use dummy canaries for access qualification, **not hidden answers**. Permission-denied evidence under the actual identity is stronger than a different directory name. It still establishes practical procedural isolation, not impossibility of malicious collusion or every covert channel.

If no independent custodian is available, retain HOLD. A same-author disclosed demonstration may have engineering value but cannot silently replace this independently held test. No roles were assigned, accounts created, remote machines contacted or access tests performed during this mission.

## 7. Decision-rule consistency

| Rule | Review conclusion and smallest clarification |
|---|---|
| ≥6/8 positives and at least one per stratum | Coherent anti-abstention feasibility criterion. Not a reliability estimate; related cases and designed strata prohibit population interpretation. |
| ≥2 more repairs than B, no lost B success | Coherent conservative investment threshold. If B repairs 7 or 8, C cannot pass this margin; accept the resulting no-investment decision, do not weaken B or raise difficulty to manufacture headroom. |
| Strict no lost B success | Appropriate if the engineering goal is additive useful coverage on this screen. C's fallback does not guarantee this mechanically under a two-slot budget. A one-loss result fails this gate, but does not prove all record systems are harmful. |
| Zero harmful/irrelevant/incomplete accepted C edits | Appropriate necessary condition for this small authority screen, not proof of zero deployment risk. Keep task completion separate from refusal. |
| C harm immediately stops | Acceptable safety gate, but all unrun units are NOT RUN, never ties or exclusions. Report the triggering harm and observed prefix; no favorable total effect or population inference from an incomplete sample. |
| B harm counted, run continues if confined | Coherent for safely measuring a baseline; it exposes a blind spot in the **shared** acceptance mechanism. Such a result cannot coexist with an unqualified claim that the common verifier is trustworthy. |
| Zero inference and matched maxima | Preserve. Equal maxima do not require wasting calls until both arms spend equally; observed computation differences are costs. |
| 1.25× time and ≤10 s extra proposer overhead | Legitimate prospective spending preferences, not evidence-calibrated facts. Currently “complete paired pipeline” and charging of shared costs are ambiguous. Define numerator/denominator and clock before freeze. |
| One incremental engineer-day | Useful anti-expansion cap if a day has fixed hours and includes record curation, implementation, review and C-specific qualification. Do not hide C-specific analysis in the common budget. Actual future maintenance remains unknown. |

**Denominator clarification:** five of the eight negative/refusal units are required to stop before candidate execution. They test authority and unsupported-effect refusal, not behavioral detection of a harmful repair. Only three negative units are potentially behaviorally scored; the positive units also test whether accepted edits cause regression. Report these strata separately. “Zero harmful acceptance on eight negatives” must not be interpreted as eight independent behavioral safety trials. This limits evidentiary strength without requiring a larger challenge in this mission.

**Necessary decision clarification:** record-value evidence and verifier-readiness are two outputs. If B accepts a harmful repair on hidden scoring while C meets its thresholds, one may report C's observed relative improvement, but **VERIFIER-REQUALIFICATION-REQUIRED** must block advancement to trusted authority or acquisition feedback based on that verifier. The existing design says broader authority is blocked but leaves the investment-gate/next-stage consequence too vague. Do not change the common oracle mid-run or retrospectively count hidden evidence as acceptance input. If C itself harms, the safety stop yields failed qualification regardless of prefix benefits.

**Necessary cost clarification:** compare operational reuse cost—proposer, shared analysis, original decision evaluation, proposal decision evaluations, durable decision journaling and cleanup—with shared work apportioned symmetrically. Separately report total experimental cost including custody, hidden scoring and qualification. Hidden scoring is not a deployed repair cost and must not dilute a C-specific overhead ratio. If no original cache is used, charge each arm its actual original evaluations. If shared, charge half the measured common cost, identically. Freeze time bounds, scheduling and observation intervals before results. No repeated scored trials to obtain a favorable timing sample.

Early rejection can make wrong B proposals cheap while a successful C proposal needs all decision tests; that is a real cost of verification, not a reason to hide calls or count failure as utility. The 1.25 threshold may reject a useful but expensive gain; it is a declared engineering preference. Keep it unless humans prospectively choose another explicit tradeoff before a successor freeze. Tied correctness remains a choice of the cheaper architecture under this gate, even if a later economic question might value faster answers.

**Representation versus information:** a C win would identify supplied-information/ordering value against this B under this budget. It would not establish that a record interpreter beats hard-coding the same ordinary relationship, that a learned abstraction was acquired, or that verification alone was insufficient. The first requires an equally informed representation comparison or compelling cost reasoning; the second requires an acquisition experiment. Neither should be retrofitted onto these sixteen results.

## 8. Future autonomous-acquisition compatibility

**SUPPORTED INFERENCE:** the fixed role/predicate/operator interface preserves a plausible acquisition test. A learner could populate priority clauses and evidence references under a frozen interpreter, then test record availability against no record in new processes. Unknown conditions remain non-authorizing, task authority stays external and acquired data cannot add executable verifier logic.

**DIRECTLY VERIFIED design limits:** at most eight conjunction clauses, eight atoms per clause, fixed three-valued facts, sign-toggle operator and bounded role vocabulary. Versioned references and counterexamples are representable. Merely storing counterexample references does not implement learning from them; evidence validation and any update rule remain absent. The schema cannot represent arbitrary new concepts or edits without a separately reviewed interpreter/schema revision. That limit is useful, not a reason to add a general analyzer now.

Still investigator-engineered: task ontology, field meanings, source grammar, bindings/effect analyzer, predicate vocabulary, operator semantics, authority validator, oracle, validation policy and resource budget. Acquired content would have to be a relation inferred and independently validated from permitted experience, not a copied current requirement or a hand-completed clause table. No existing VSL extraction/lifecycle path was found to acquire and qualify those semantic clauses today.

Minimal future safeguards before an acquisition claim: freeze meanings, canonical clause normalization, conflict/priority resolution, unknown behavior and interpretation version before learning; bind each update to independently verified original/proposal outcomes and exact task/source/record/checker versions; distinguish semantic counterexamples from infrastructure or oracle error; preserve positive examples so blanket suppression cannot masquerade as improvement. Learner proposals remain untrusted data and never certify their own authority.

The decisive later contrast is the same capable system, current requirements, local model, tools, verifier and resource limits, with/without an autonomously acquired record. No-record reasoning is permitted. If common logic or native reasoning derives the same useful rule within budget, retained-learning benefit has not been established. If the revised cheap rule leaves these record atoms no useful residual information to learn, postpone this acquisition route instead of weakening that control. No acquisition implementation or learner inference was performed here.

## 9. Ranked blockers and corrections

| Priority / severity | Finding and evidence status | Claim impact | Minimum action / kind |
|---|---|---|---|
| 1 — High | Baseline leaves cheap polarity rule optional; common facts expose it. **DIRECTLY VERIFIED design; SUPPORTED INFERENCE rival.** | A C win may depend on an unnecessarily weak engineered comparator. | One versioned amendment settling generic polarity ordering and exact ties; independent baseline review. **Documentation + human review**, later code only if authorized. |
| 2 — Critical prerequisite | No accepted independent custody/reviewer/access evidence. **BLOCKED / UNKNOWN.** | Cannot claim independently held qualification. | Obtain role acceptance and approve a concrete offline/separate-identity plan, then access evidence before cases. **Human + independent custody**. |
| 3 — High | Original-cache reuse and hidden/decision cache partition are underspecified; historical room profiles differ. **DIRECTLY VERIFIED source/design.** | Budget could be wrong or hidden information could enter acceptance. | Prefer no-cache originals for the small screen; explicit separate phase visibility and immutable identity keys for any cache. **Documentation**, later qualified code. |
| 4 — High | B harm versus common-verifier qualification has no explicit next-gate outcome. **DIRECTLY VERIFIED text; SUPPORTED INFERENCE ambiguity.** | Record-value improvement could be mistaken for qualified authorization/feedback. | Separate empirical record result from verifier qualification; shared blind spot blocks advancement. **Documentation + reviewer approval**. |
| 5 — Medium/high | Launch classes, preflight/replay allocation, clocks and memory guardrail unfinished. **DIRECTLY VERIFIED omissions; runtime UNKNOWN.** | Cap exhaustion/overhead could defeat reproducibility or be misreported as learning failure. | Adopt explicit bounded ledger and cost definitions; non-scored feasibility after separate authorization, no automatic cap increase. **Documentation then public qualification**. |
| 6 — Medium | Balancing dead-site order does not balance post-filter live competition; counts are not exact. **SUPPORTED INFERENCE from shared filtering.** | Construction artifacts could account for C advantage. | Exact eligible-site allocation/position policy independent of arm rankings; no manufactured distractors. **Documentation + custodian review**. |
| 7 — Known bounded limitation | Finite oracle and shared analysis can miss intent/effect errors. **DIRECTLY VERIFIED mechanism; proposed behavior UNTESTED.** | No general safety/task-correctness claim even after a pass. | Keep narrow claim, independent authority review and planned observation/checker qualification. **Human review + later public qualification**, no wholesale redesign. |

None of these findings is evidence of positive or negative retained net utility. They concern whether this engineering experiment would be interpretable. The original design/report and SAC-1 v1 remain immutable.

## 10. Minimal next-step authorization checklist

The next deliverable should be **one separately versioned readiness amendment**, not implementation and not another broad architecture proposal. It should contain only the necessary corrections above and accepted ownership of the remaining gates.

Before **implementation authorization**:

1. Independent human approves B's competence, exact ordering and the residual reason C could add value without removing an ordinary B capability.
2. Approve the task-authority chain and oracle review roles; confirm they accept the assignment and are not the implementer certifying their own hidden answers.
3. Accept a workable custody/storage/execution-identity plan outside implementer access. If unavailable, remain on HOLD.
4. Approve cache/visibility rules, explicit launch ledger, machine-time versus human-wait clocks, operational cost definition, engineering-day accounting and memory/observer guardrail requirements.
5. Approve distinct record-value and verifier-readiness outcomes, strict no-regression/safety stops and incomplete-sample reporting.
6. Give explicit permission for the smallest research-only prototype and public non-scored qualification. This report does not provide that permission.

Before **scored execution authorization**, later: pin the actual implementation/record/independent oracle; qualify exact new paths, proposer/observer and both rooms; verify throughput/resource policy without held-out material; demonstrate real custody/access denial; commit exact case-selection allocation/seed custody and oracle attestations; instantiate hidden cases only after implementation freeze; freeze all execution criteria and run once. Failed public qualification means stop that version. No held-out material should be generated merely because a draft implementation exists.

If the baseline rule makes C demonstrably redundant within the proposed scope, the smallest next action is to stop investing in the record interpreter, retain independently useful task-authority/verifier safeguards, and separately assess whether that cheaper engineered pipeline is worth implementing. Do not widen the test or add learned skills just to preserve SAC-1R2.

## 11. Repository integrity and reproducibility

**DIRECTLY VERIFIED opening:** [opening.json](sac1r2_readiness_20261008/opening.json), 06:35:17 PDT, pins **506 authorities**, including the prior 499 and the complete SAC-1R2 design/evidence bundle. No discrepancy from the previous pins. The reviewed design hash is `275313ac2877eacd92be2eac235d9ec18ed6dd9697d6a3c1604259d3832575f2`. Branch `vsl-implementation`; HEAD `e5acbb09cece8d1791fa6d967fe57067137a8cff`; cached origin/main `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`; ahead/behind 4/0; staging empty; fourteen pre-existing tracked modifications. Full untracked inventory preserved. No fetch.

[Opening process observation](sac1r2_readiness_20261008/opening_processes.txt): Echo 55361, October 1 15:45:19; watchdog 56610, September 28 09:44:38; Ollama 1991, September 19 10:57:03; auxiliary identities recorded. Mutable FAISS/memory/RiverBrain/self-model/runtime files are fingerprinted separately, excluded from scientific inputs. Their evolution is not automatically an integrity failure and is not attributed from hashes alone.

Reproducibility evidence consists of read-only raw outcome counts, source references, explicit arithmetic in [resource_accounting.json](sac1r2_readiness_20261008/resource_accounting.json), and primary permission-documentation references in [documentation_sources.json](sac1r2_readiness_20261008/documentation_sources.json). The source inspection used no experiment imports or candidate evaluation. No held-out answer matrix was opened, generated or scored. Mathematical reasoning about signs and budget arithmetic are not candidate trials.

**DIRECTLY VERIFIED closing:** [closing.json](sac1r2_readiness_20261008/closing.json), 06:58:40 PDT, confirms all **506 pinned authorities unchanged**, including the reviewed SAC-1R2 report. HEAD, branch, cached origin, staging and the fourteen tracked modifications and their contents are unchanged; no pre-existing status entries disappeared. [Closing process observation](sac1r2_readiness_20261008/closing_processes.txt) is byte-identical to the opening observation. Four excluded live mutable files changed—FAISS, memory metadata, RiverBrain and self-model—with no attribution inferred from their hashes; this review did not write them. Runtime temporary self-edit state did not change in this interval.

The [manifest](sac1r2_readiness_20261008/evidence_manifest.json) pins the final additive artifacts. The closing tree observation precedes creation of its own file and final review-document/manifest bookkeeping. This report and files under `audits/sac1r2_readiness_20261008/` are the only intended writes. No implementation, skill/lifecycle change, production mutation by the review, service signal/restart, staging, commit, push or pre-existing cleanup. **Candidate executions: 0. Experimental model inference calls: 0. Held-out generation/scoring: 0.** External access was limited to primary technical documentation; no relay/model runtime dependency was introduced.

## 12. Final questions

**Q1. Is B competent or artificially advantaging C?** It is a credible starting baseline but not yet adequate for the investment decision. The ordinary polarity rule remains optional despite available facts. Baseline verdict: **REVISE BEFORE FREEZE**, without alleging deliberate weakening.

**Q2. Could shared analysis already encode the repair?** Yes for the simple resolved monotone-key subcase: orientation, effective sign and selected extremum determine local consistency. Whole-program repair safety still needs verification. Whether any record adds value beyond that common rule is untested.

**Q3. Independent oracle authority or repeated interpretation?** The proposed owner/reviewer/contract hierarchy can support independent expected-value authority; sharing a correct spec is appropriate. Actual approval and qualification are missing, and consistent wrong translation remains possible. Oracle verdict: **HOLD**, with conditional sampled conformance as the strongest future claim.

**Q4. Are 6,000 calls and thirty minutes feasible worst-case?** The launch ceiling can fit the exact refusal policy: at most 4,752 candidate plus 32 main proposer launches without original caching, with qualification separately capped. Thirty-minute completion is not proved under ten-second deadlines; it is an abort cap. Revise the ledger and qualify ordinary timing/memory prospectively; do not increase resources on this evidence.

**Q5. What establishes custody?** Accepted independent roles, actual restricted identities/storage, canary access-denial evidence, no privileged/shared export path in the stated threat model, implementation freeze before case generation, sealed manifests and complete no-feedback provenance. None is established by a second model session or new directory.

**Q6. Are strict no-regression/zero-harm rules appropriate?** Yes for a conservative additive engineering gate, not a statistical proof. Reordering two slots is not inherently additive. A safety-stop prefix must be reported incomplete; B harm still blocks claims of an adequately qualified shared verifier.

**Q7. What does C winning establish?** Conditional incremental value of investigator-supplied priority information against the approved B on these held units and budgets. Not autonomous acquisition, superiority over an equally informed hard-coded rule, general safety or retained-learning net utility.

**Q8. What if B ties or wins?** Keep independently qualified common authority, isolation, observation and verification safeguards; prefer B's simpler proposal mechanism. Postpone or abandon the extra interpreter for this scope. Do not weaken B, tune against the holdout or expand skills to rescue C.

**Q9. Does the representation preserve a future learning test?** Plausibly, within its fixed atoms/operators, provided learned clauses/evidence are the changed data and the interpreter stays frozen. Acquisition is absent today. Common engineered semantics or native same-budget derivation may eliminate any retained benefit; that is an admissible result.

**Q10. Smallest action toward authorization?** Obtain one independent human review of a narrow, separately versioned amendment resolving baseline polarity, cache/cost/launch accounting and verifier-gate semantics, together with willing custodian/oracle-reviewer acceptance. Until both design defects and custody prerequisites are addressed, build nothing.

**Final disposition: REVISE. The existing HOLD on implementation and experimental execution is not lifted. Return for human review and stop before construction.**
