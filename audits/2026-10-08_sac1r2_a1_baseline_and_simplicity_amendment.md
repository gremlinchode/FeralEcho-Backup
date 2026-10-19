# SAC-1R2-A1 — Baseline competence and simplicity amendment

October 8, 2026. Design amendment for human review. **Recommendation: RETAIN B — POSTPONE C. Implementation and experimental execution remain NOT AUTHORIZED.**

## 1. Executive decision and amendment scope

The proposed semantic record's principal relationship—how numeric sign, rank-map orientation, sort direction and selected endpoint determine preference—is cheaply derivable from current source and current task requirements. Give that relationship to both arms. Ownership, bindings, liveness, task validity and independent verification were already common machinery. Historical counterexample references add provenance, but the proposed interpreter supplies no separately established inference mechanism that turns those references into a new decision capability.

**SUPPORTED INFERENCE:** no concrete, non-contrived residual C capability has been established for this declared task family. Its present justification is another encoding of an ordinary rule, plus optional proposal ordering. That does not justify building and maintaining a record interpreter. **Stop C's development here.** Preserve the generic proposer and independent-authority/verifier concepts for separate consideration; neither is implemented or qualified by this report.

This is a design investment decision, **not an executed B victory, proof of universal redundancy, or a retained-learning result**. A different, independently evidenced acquired relationship could matter in the future. No such relationship is invented here, and no task family, grammar, arm, skill library or analyzer is expanded to create one.

Evidence labels:

- **DIRECTLY VERIFIED:** inspected source, existing raw fields, hashes or arithmetic. This does not mean a new candidate was executed.
- **SUPPORTED INFERENCE:** reasoning from identified mechanisms within stated assumptions.
- **UNTESTED HYPOTHESIS:** prospective performance or behavior requiring qualification.
- **BLOCKED / UNKNOWN:** absent evidence, implementation, role acceptance or authorization.

The following amendments supersede **only proposed provisions**, upon independent approval; they do not alter historical files or claim an executable protocol freeze:

| Prior proposed provision | A1 replacement |
|---|---|
| [SAC-1R2 design](2026-10-08_sac1r2_design_and_experimental_gate.md) §6: optional common polarity heuristic and C-first prioritization | §§3–5 below: required common polarity rule, deterministic ordering and protected common prefix; no justified residual record investment. |
| Design §7: site-count/position balancing | §6: balance actual eligible live sites after common filtering; no manufactured competition. |
| Design §8: original-cache assumption, child-call/replay and time accounting | §§7–8: no-cache ledger, distinct counters, phase clocks and public qualification allocation. |
| Design §§8,10: combined gate and unspecified engineering-day/runtime denominator | §§9–10: separate measurement-integrity and record-value outcomes; exact cost definitions. |
| Design §§7,11: custody and authorization prerequisites | §§11–12: explicit unfilled roles, access evidence and conditional authorization checklist. |

The [readiness review](2026-10-08_sac1r2_final_adversarial_readiness_review.md), [SAC-1 adversarial review](2026-10-07_sac1_independent_adversarial_review.md), [architecture report](2026-10-07_semantic_competence_repair_authority_architecture.md) and [frozen SAC-1 v1](semantic_authority_20261007/protocol.md) remain unchanged. All other R2 restrictions remain. Sections describing a possible future comparison are **dormant specifications**, completed to resolve the requested design defects; they are not a recommendation to proceed with C despite the simplicity stop.

## 2. Verified starting evidence and exact comparison amendment

**DIRECTLY VERIFIED:** [opening.json](sac1r2_a1_20261008/opening.json) pins 516 authorities, with zero discrepancies from the prior review's 506 pins. No A1 report/directory existed at initial inspection. A subsequent durable snapshot was taken at 13:12:48 PDT after the user's continuation; no prior command with missing output was treated as a successful write. Repository state is recorded in §13.

Fresh read-only [recount](sac1r2_a1_20261008/source_and_evidence_recheck.json) confirms:

- Skill A is unchanged ACTIVE v4, `K2.T5.tag_priority_direction`, with `sorted` call context. The [matcher](../app/core/skill_ledger/matcher.py), `apply_skill`, returns the first matching structural replacement. [Runtime](../app/core/skill_ledger/runtime.py), `consult`, has no interpreted task-contract parameter; the [adapter](../app/core/skill_ledger/echo_adapter.py) records `f1_f2_safety_only`. These facts do not establish live feature-flag settings or task-correctness authority.
- Historical recognition: TP4/FN9/TN5/FP6 over the 24 categorized rows, with the natural lead separate. Historical RNU: 44 pairs, 25 correct/19 incorrect each, zero skill applications, **INCONCLUSIVE**. Nothing here converts that result into neutrality or positive utility.
- Historical boundary: 28 candidate calls and twelve agreeing reference/confined pairs. This supports those historical controls, not a new proposer, observer, directory or controller.
- [E0.1](../app/experiments/rung1/trusted_evaluator.py) compares caller-supplied expectations in the parent. Its `_typed_equal` distinguishes bool/int but otherwise uses Python equality. [Durable evaluator](retained_utility_20261006/durable_evaluator.py) journals launch/return/comparison before cleanup. [Operation-aware guard](retained_utility_20261006/guard_v3.py) treats unlink as a directory-entry operation, while retaining target-following write restrictions. None was invoked.
- The acquisition [harness](../app/experiments/skill_ledger/harness.py) and [PIT2 acquisition](../app/experiments/prospective_invariance_test_2/pit2_run.py) select a `used_pair` but hash `failing[0]`. The previously checked nine A/two PIT2 attribution discrepancies remain preserved; wrong hashes are not authoritative provenance for this proposal. No historical extraction or correction was rerun.

**DIRECTLY VERIFIED design:** B and C were proposed to share source, current requirements, analyzer, eligible single-sign-edit universe, fallback, verifier, independent expected-value authority, two proposals, timeouts and rooms. C's only intended difference is an inert investigator-authored priority record. Its concrete record was not authored in R2; a vocabulary and bounded clause interpreter were specified. Thus this audit compares the **specified informational contribution**, not an unavailable fully enumerated record.

**A1 comparison, if ever separately justified:** both arms use the exact common rule in §3. C cannot displace its priority prefix, suppress generic fallback, invent facts, change eligibility, add operators, modify current requirements, query decision tests or receive acceptance feedback. At most two proposals per arm are committed together, each one site relative to the original. C may reorder only eligible fallback proposals left after the common prefix. Proposer exits before checking. Both final decisions and output hashes seal before hidden scoring. A remains a historical descriptive reference, not a third executed arm.

Identical canonical task payloads, shared facts/site universe and checker manifests must be journaled, apart from neutral request IDs and C's record. Current task authority, oracle values and permission to apply are never supplied by the record. Different proposal ordering is a possible treatment effect; different analyzers, budgets, task facts or verifier behavior are a protocol failure.

## 3. Formal common polarity rule and exact ordering

**Proposed specification; algebra is SUPPORTED INFERENCE, runtime behavior UNTESTED.** This is generic ranking consistency, not historical Skill A knowledge.

### Applicability and direction

First require a valid, current, supported task contract and common source/ownership checks. For an eligible numeric component, resolve its binding, all relevant uses, key precedence, literal sort direction and returned first/last endpoint. Its dependence must reduce to a monotone numeric encoding of the relevant task criterion, multiplied by an effective sign `s ∈ {−1,+1}`. Pure helper substitution and unary sign composition are common analysis. No assumption is made from variable names or enclosing spelling alone.

For every pair of tags `g,b` with `g` preferred by the **current contract**, let `d = rank(g) − rank(b)`. Require all declared tags mapped, nonzero differences, known monotone orientation and a setting where higher-priority key components can be equal. The position/meaning of this component must agree with the task's criterion precedence; a wrong key order is not certified fixable by a sign change. Lower tie-breaks cannot overturn a nonzero component difference.

| Sort direction | Returned endpoint | Effective selection | `q` |
|---|---|---|---:|
| Ascending | First | Minimum key | −1 |
| Ascending | Last | Maximum key | +1 |
| Descending | First | Maximum key | +1 |
| Descending | Last | Minimum key | −1 |

Correct local orientation requires **`q × s × d > 0`** for every preferred pair. The test uses signs; it need not multiply potentially large runtime values. If every product is negative and the proposed one-site toggle reverses this effective sign at every relevant resolved use, prioritize that edit as **POLARITY_INCONSISTENT**. If every product is positive, give no polarity-repair priority. A zero/missing/mixed difference, unknown sign, ambiguous endpoint/binding, unresolved key precedence, interacting sort or conflicting use gives **POLARITY_UNKNOWN**: abstain from this rule.

The same inexpensive rule applies to a resolved direct numeric score component using the current contract's score preference instead of a tag map. It does not extend the edit universe to strings or arbitrary comparators. This prevents granting C ordinary numeric-ranking knowledge while withholding it from B.

A shared extracted expression used in multiple places receives priority only if all relevant uses are resolved and agree that this toggle repairs their local orientation without reversing a required orientation elsewhere. Otherwise use UNKNOWN. No general alias/dataflow analyzer is implied. Unsupported/ambiguous sites fail the common eligibility check; a supported eligible site with insufficient **polarity** facts may remain in generic fallback. This distinction prevents both guessing a sign and crippling the generic search.

This proves a local ordering relation under its premises, **not whole-task repair correctness**. Even prioritized proposals still require complete independent verification. A correct orientation does not mean the original task is correct. Unknown cannot be negated into evidence, and a record may not fill it from historical intent.

### Deterministic proposal order

Use the unchanged proposed sign-toggle universe: adding/removing a unary minus at a resolved numeric key component or uniquely bound extracted expression, plus the already specified eligible return-dependent numeric sites. Filter dead, unsafe, nonnumeric, unsupported or unresolvable sites first. Count each physical AST edit site once; coalesce multiple analysis paths to the same edit. Do not collapse distinct sites by guessed semantic equivalence. If complete patched ASTs are identical, retain the earliest canonical site only; no execution is needed or permitted for this deduplication.

Define a shared total order `G` with these ascending keys:

1. Live ranking-key site before other return-dependent numeric site.
2. Rank-map-derived key component before direct numeric field, then other eligible numeric expression.
3. Fewest def-use edges to the returned selection, in the common normalized graph; ambiguous paths are ineligible, not guessed short paths.
4. Original source `(line, column, end_line, end_column)`, then canonical AST field/index path. Fixed operator ID breaks any remaining tie. No identifier spelling, task ID, historical hash, record clause or oracle answer breaks a tie.

Let `H` be all POLARITY_INCONSISTENT proposals, ordered by `G`, and `F` all other eligible proposals in `G` order. Both arms take the first `min(2, |H|)` entries of `H` unchanged. If fewer than two were selected, B fills from `F`. C may order `F` by the minimum priority tier among its fully known matching clauses (0–3), unmatched last (4), ties by `G`; it fills only the remaining slots. Unsupported/conflicting record data gives no boost and is recorded; it cannot disable common proposals. Unknown predicates never match. No proposal is executed to establish either ordering.

Both preserve the complete enumeration for audit but commit at most two. When the universe has at most two entries, both include them. When `|H| ≥ 2`, C has no ordering discretion under A1. This deliberately protects inexpensive common competence; a record that offers no residual information has no entitlement to displace it. For unresolved fallback competition C might still change selections, but that alone is not evidence of semantic value.

## 4. Common-versus-record-only capability matrix

The classifications below concern the **proposed design**, not implemented capability. **DIRECTLY VERIFIED:** the common facts and record vocabulary are specified in R2 §§4,6,9. **SUPPORTED INFERENCE:** their implications below.

| Capability | Source/class | What C adds after A1 |
|---|---|---|
| Intended ranking direction and precedence | **COMMON** — authoritative current task | Nothing; a record cannot replace it. |
| Selection endpoint / ascending versus descending | **COMMON** — source analysis | Nothing; `q` is a four-entry ordinary relation. |
| Numeric-sign orientation | **COMMON** — effective sign plus polarity rule | An equivalent clause is another encoding, not additional information. |
| Literal rank-map orientation | **COMMON** — source versus current order | Nothing; nonmonotone/unknown remains unresolved. |
| Helper/extracted expression recognition | **COMMON** — bounded bindings/substitution | Record does not supply another resolver. Unsupported helpers remain **UNSUPPORTED**. |
| Live-site recognition | **COMMON** — def-use to returned selection | No record-only liveness evidence. |
| Multiple eligible sites | **COMMON** enumeration, two slots, protected polarity prefix | **RECORD-ONLY** residual priority choices are possible, but no evidenced superior relationship is specified. |
| Ownership and mutation restrictions | **COMMON** contract/checker/verifier | Repeating them cannot create new authority. General ownership/identity effects remain **UNSUPPORTED**. |
| Unknown/ambiguous bindings | **COMMON** fail-closed eligibility/rule abstention | No permitted clause resolves missing facts by assertion. |
| Conflicting/stale/missing requirements | **COMMON** authority registry and refusal | Nothing; current intent cannot be inferred from retained history. |
| Historical failure contexts | **RECORD-ONLY** references to earlier evidence | References are inert; there is no qualified mapping from them to a new applicable condition. |
| Applicable operand-role restrictions | **COMMON** role facts and resolved ranking relation | Their record encoding is duplicative where resolved. A new, unexpressed condition remains **UNSUPPORTED**. |
| Counterexamples | **RECORD-ONLY** provenance references; runtime checks **COMMON** | No learned classifier/update rule is specified. Known unsafe ownership, shadowing and wrong direction are already common checks. |
| Expected values / task completion / postconditions | **COMMON** independent oracle and acceptance controller | No C-specific verifier or answer source is allowed. |
| New empirical failure probabilities or cross-task cost predictions | **UNSUPPORTED** by current evidence/interpreter | A conceivable future information source, not an existing C capability. Do not build one here. |

The abstract field name `known_counterexamples` does not demonstrate that a system can use counterexamples. The proposed fixed interpreter evaluates enum conjunctions and priority tiers; it does not read evidence references as executable tests, explanations or new predicates. Making it do so would be a new mechanism requiring separate review.

## 5. Residual-value determination and simplicity stop

**SUPPORTED INFERENCE:** the specified polarity relation is subsumed in the resolved subcase. The remaining stated restrictions—known builtin, unique definition, ownership, return dependency and task validity—are common eligibility or verification conditions. Existing conditional clauses therefore do not identify a separate useful applicability relation that B cannot derive cheaply.

There are several distinct possible explanations for an apparent future C difference:

| Explanation | Determination here |
|---|---|
| Genuinely additional cross-task relation | **BLOCKED / UNKNOWN:** none specified and independently supported. |
| Same ordinary relation stored as data instead of code | **SUPPORTED INFERENCE:** accounts for the record's principal contribution. Prefer the ordinary rule. |
| Different ordering among unresolved fallback sites | Mechanically possible, **UNTESTED HYPOTHESIS** of benefit. No independent reason to expect better ordering was found. |
| Extra engineering knowledge withheld from B | Unfair for this investment decision; A1 gives both arms the ordinary rule and shared facts. |
| Test construction makes C's favored position useful | A confound, not transfer. Post-filter balancing helps diagnose it; it cannot create a justification for C. |

A table can encode many policies; this audit does **not** prove that every possible table has the same output as B. Nor does it predict 8/8 B repairs. It finds no evidence-supported incremental content in the **proposed** record worth paying to implement. Fresh hidden cases cannot substitute for an absent architectural hypothesis.

**Decision: RETAIN B — POSTPONE C.** Stop before record implementation, scored-case instantiation or public runtime qualification. A direct generic rule plus independent verifier is the cheaper surviving concept, not yet qualified software. Preserve VSL's production ledger/skills unchanged; no wholesale replacement is justified.

Reopening C would require an independently reviewed, precisely expressible relation supported by permitted evidence that remains additional after common inexpensive reasoning, plus a plausible maintenance-cost benefit and fair selection procedure. It may not be created by withholding common facts, picking B failures, enlarging this grammar or inventing another task family to rescue the experiment. No such reopening is recommended now.

## 6. Corrected eligible-site allocation — dormant, not cases

This resolves R2's site-balancing defect without generating any source, seed, witness or answer. It is conditional on a separately justified residual comparison. **UNTESTED HYPOTHESIS:** the existing grammar can naturally support all requested allocations. Inability to do so is a stop, not permission to add distractors.

Preserve eight positive slots: two each for alpha/direct equivalence, pure helper/extraction, equivalent sorting, and multiple-site mechanisms. Preserve eight negative/refusal slots: already-correct opposite-contract twin; irrelevant/dead apparent repair; ownership violation; unsupported shadow; missing fact; conflict; stale contract/source; partial repair with another obligation unsatisfied.

Before generating scored material the accepted custodian must commit the approved grammar/checker/eligibility version, role declarations, independent oracle/owner approvals, factor domains, allocation algorithm, privately committed seed, two-instantiation limit, rejection codes, input-partition policy and implementation hashes. The private seed is committed after implementation freeze; no seed search based on proposal order or outcomes. Exact cases/answers are not public design inputs.

**Precise proposed allocation:** each positive stratum gets one low-count slot and one high-count slot. Independently permute low counts `[1,1,2,2]` and high counts `[3,3,4,4]` across the four strata using the committed custodian seed. Counts mean unique **eligible live edit sites after the shared filter/deduplication**, not apparent signs, dead expressions or number of sorts. No C clauses or B/C priority tiers participate in eligibility.

For the two slots of each count `n`, privately draw `p` uniformly from `1..n`; assign positions `p` and `n+1−p` to their independently established repair witnesses, swapping assignment by a committed fair draw. Positions are in canonical source order over eligible sites, not B's or C's chosen proposals. For `n=1` both are necessarily first; for odd `n` a midpoint pair is allowed. This achieves mirror balance, not all-position coverage or statistical independence. Do not redraw to put witnesses beyond the two-proposal cutoff. No witness/index is sent to a proposer.

Only naturally required operations of an independently defined task mechanism may supply competing sites. A dead expression, no-op numeric ornament, duplicate alias or unrelated sort inserted to fill the quota is not legitimate competition. Independent review must approve the finite production choices and necessity of their operations before scored instantiation; the checker verifies realized counts, the custodian verifies intended mechanisms. The multisite stratum still requires meaningful multiple-site structure, not padding. If this allocation cannot be met naturally within the existing grammar, **the residual investment screen is unjustified; stop**. Do not move slots, widen grammar or search indefinitely.

For each slot take the first qualifying instantiation in committed order, at most two. Eligibility may use the authoritative oracle/witness, common static filter, stratum constraints and independent semantic novelty review; it may not run either proposer, inspect arm ranking/success, or select B failures. Log every rejection before the next instantiation. Historical hashes only detect duplication; names/hash differences do not establish semantic novelty. Negative slots retain their mechanisms without artificial site quotas. No replacement after scoring starts. This document contains an allocation procedure, **not a generated held-out answer matrix**.

Because §5 found no justified residual C relation, this procedure remains unused. Fair site balancing can remove an artifact; it cannot make redundant information valuable.

## 7. No-cache resource-accounting specification

**DIRECTLY VERIFIED arithmetic**, conditional on the retained design. Reproducible counts: [resource_accounting.json](sac1r2_a1_20261008/resource_accounting.json). No launch occurred here.

Exactly five slots prohibit candidate execution during custody **and** the paired run: (1) alias/ownership violation, (2) unsupported builtin/helper shadow, (3) missing required contract fact, (4) conflicting contract, (5) stale task/source/interpretation binding. These receive structural/authority-refusal evidence, not invented task scores. A confined validator/proposer process may still consume one of its reserved launches, but it may not execute the supplied candidate.

Eleven slots may need candidate execution: eight repairable positives and the three known-contract supported negatives—already-correct twin, irrelevant apparent repair, and incomplete repair. A valid source with no eligible edit can still have its original evaluated; that does not permit executing dead code as a supposed repair. Each executable custody slot has at most two instantiations and at most one original plus one witness per instantiation. No third arm or witness search.

| Component | No-cache calculation | Candidate launches |
|---|---:|---:|
| Custodian original evaluations | 11 × 2 instantiations × 48 inputs | 1,056 |
| Custodian witness evaluations | 11 × 2 × 48 | 1,056 |
| Original decision evaluations | 11 × 2 arms × 24 | 528 |
| Original hidden evaluations, scorer only | 11 × 2 × 24 | 528 |
| Proposal decision evaluations | 11 × 2 × 2 proposals × 24 | 1,056 |
| Final hidden evaluations, even unchanged final | 11 × 2 × 24 | 528 |
| **Candidate total** | | **4,752** |
| Proposer launches, including refusal slots conservatively | 16 × 2 | **32** |
| **Combined main boundary-launch ceiling** | | **4,784** |
| Main boundary-attempt cap / remaining margin | 6,000 − 4,784 | **1,216** |

No original-result cache is used across custody, rooms or phases. No count assumes early rejection, first-proposal success or identical-output reuse. Originals and final outputs run again in their declared phases even if byte-identical. Duplicate physical evaluations count separately, never as independent scientific units. Decision controller sees only decision inputs/results. Original-hidden results, custody witness observations and expected hidden values stay in custody/scorer storage and are inaccessible to acceptance, proposer and candidate. Hidden originals are not a budget-saving acceptance input.

Counters must distinguish: logical requests; prelaunch validation failures; boundary launch attempts; OS child starts where observable; candidate entry execution where evidenced; returns/timeouts; trusted comparisons; durable completion; cleanup. One `sandbox-exec`→Python execution chain is one boundary launch, not two independent evaluations. A request failing before launch is not a successful child execution. **Each attempted boundary invocation consumes the cap even when child creation fails**; record zero starts or UNKNOWN accurately. Launch infrastructure failure stops, with no free retry or refunded slot.

The 6,000 ceiling is explicitly for candidate/proposer boundary attempts. Controller-only arithmetic/schema work creates no such attempt; separately journal top-level phase processes and monitoring activity. Future implementation must use in-process monitoring and at most one controller invocation per custody, decision and hidden-scoring phase, rather than hiding thousands of helper subprocesses outside the counter. Any required extra execution service/helper needs a prospectively reviewed allocation. The 1,216 margin does not authorize more cases, proposals, replays or retries.

Qualification has its own **128 boundary-attempt / ten-minute** cap. Retain the review's allocation:

| Public qualification category | Launch allocation |
|---|---:|
| Existing six semantic domains, two rooms, reference/confined | 24 |
| Combined filesystem controls, two roles/two rooms | 4 |
| Successful transport/execution | 4 |
| New observation comparisons | 16 |
| Schema, binding and authority process controls | 16 |
| Transport and cleanup success/failure | 8 |
| Fresh proposer reload/replay | 8 |
| Public candidate replay | 16 |
| **Allocated / unallocated reserve** | **96 / 32** |

Before any authorization to execute, map these allocations to an exact public control manifest, individual assertions, expected results and timeouts. Combined probes must preserve each control's evidence. The reserve is not discretionary experimentation: any use must be in that pre-execution manifest, within 128. No retries after a failed frozen qualification, and no dropped controls to fit the count. Public replay belongs here, not in main-run margin; no scored replay or reviewer rerun is silently free. These counts are a design specification, not claims that new tests have been written.

## 8. Phase clocks, serialization and resource distress

**BLOCKED / UNKNOWN:** timing and memory feasibility. Thirty minutes is a hard main **abort budget**, not a completion guarantee. Candidate calls retain ten-second deadlines. `4,752 × 10 = 47,520 seconds` is a crude 13 h 12 min envelope, not an attainable all-timeout path or a runtime forecast. Completing that many ordinary calls within 1,800 seconds needs mean time below 0.379 seconds before overhead, or below 0.365 after reserving 64 seconds for 32 proposers. Neither arithmetic nor historical latency proves completion.

Proposed clock boundaries, using monotonic wall time:

- **Q (≤600 seconds):** from public qualification setup through final durable manifest/cleanup. Includes public replay, process startup, intentional timeout controls, monitoring, fsync and teardown. Stops on first qualification failure. Exact deliberate-timeout controls may have their own prospectively specified short deadlines; ordinary successful calls and timeout controls have different costs.
- **M-custody:** machine instantiation, eligibility/oracle/witness validation, serialization, hashing, durable logs and cleanup, including rejected instantiations.
- **M-decision:** room setup and paired proposal/decision work, originals/proposals, decision sealing and cleanup.
- **M-hidden:** post-seal original/final hidden evaluation, durable scoring and cleanup.
- **M-total = M-custody + M-decision + M-hidden ≤1,800 seconds.** All computational work is included even if custody is offline or performed on another permitted machine; no offloading to hide it. Both compared arms still use the same approved machine/runtime. Human approval/offline waiting between declared phases is separately timestamped, excluded from machine budget, and grants no tuning or extra computation. Actual calendar elapsed is also reported.

If phases interleave per unit, tag intervals and count each wall interval once. Arm order remains prospectively counterbalanced 8/8, serial. No pause for tuning after outcomes. Do not start a new child when its declared deadline cannot fit the remaining phase budget; record budget exhaustion rather than silently shorten its experimental timeout. Enforced shutdown overhead is recorded as overrun, never concealed by stopping the clock before cleanup. Stop only research-owned processes if necessary under a later authorized execution policy; never signal Echo or its services.

The two-second proposer timeout starts immediately before its launch attempt and ends only when its complete, schema-valid committed payload is received and the process has exited. It includes startup, imports/loading, common analysis, record interpretation and serialization; no free pre-analysis or preloaded C cache. Parent verification/journal/cleanup time counts toward operational and M clocks even when outside this subprocess deadline.

**Serialization requirement:** before execution, qualify an observer encoding bounded by the existing 4,096-byte E0.1 output envelope. Reserve at most 2,048 UTF-8 bytes for the tagged observation and verify the complete envelope bound. Validate exact primitive types, declared list dimensions and bounded fixture values before traversing/encoding; refuse unsupported results without calling their custom representations or recursively serializing arbitrary objects. No full unbounded serialization followed by truncation. Original/after-input observations remain exact for admitted inputs; overflow is visible unsupported/measurement failure, never truncated equality. The exact encoder and public limits still need review/qualification and cannot alter scored labels to fit. E0.1's current post-capture size check is **not** a hard stream-memory limit.

Proposed guardrail: sample aggregate research controller/proposer/candidate resident memory at process boundaries and no slower than every 100 ms during active children, with timestamps and missed samples recorded. Use an in-process OS interface, not repeated uncounted monitor launches. Conservative summed RSS may double-count shared pages; disclose it. Stop before more work on sampled aggregate RSS above 512 MiB, critical OS memory pressure, unavailable mandatory monitoring, disk-write failure or evidence loss; preserve partial results. No production intervention. Qualify reading pressure/child identities and the research-only stop path on public controls.

The 512 MiB value is an operational stop threshold, **not an enforced allocation maximum**. Sampling can miss peaks; Python/native allocations and buffered output are not bounded merely by small ASTs. If bounded source/observer plus monitoring is inadequate for this narrow use, stop for separate review, not a general sandbox redesign or hardware purchase.

Before attempting scored execution, non-scored qualification must demonstrate exact new paths/roles, reference/confined behavior, output bounds, durable-result survival, ordinary throughput and timeout/cleanup behavior. Its measured projection plus disclosed overhead/timeout assumptions must fit the caps sufficiently to justify an attempt; any completion forecast remains conditional. A cap hit yields incomplete measurement evidence, not negative retained utility. No such measurements occurred here.

## 9. Separate measurement integrity from engineered-record value

These are two future outputs. Neither was measured in A1.

**Outcome A — common measurement integrity:**

| Outcome | Meaning |
|---|---|
| QUALIFIED FOR BOUNDED SCREEN | Authority/oracle approvals, checker/observation qualification, both-room access controls, durable evidence and declared measurements passed for this scope; no known shared-verifier defect. Not general correctness or production authority. |
| REQUALIFICATION REQUIRED | A concrete shared-verifier/observer blind spot or invalid acceptance was found. Preserve evidence; no promotion to trusted authority or acquisition feedback. |
| MEASUREMENT BLOCKED | Missing custody/authority/isolation prerequisite, leakage, protected mutation or infrastructure prevents an interpretable screen. |
| INCONCLUSIVE | Valid partial evidence cannot resolve the qualified-scope claim, including relevant cap exhaustion without a demonstrated defect. |

A harmful B acceptance on hidden observations can expose a common-verifier defect even if C happens to avoid that proposal. Record it prominently, assign REQUALIFICATION REQUIRED, and block trusted-authority/acquisition use. Safely confined B measurement may continue under the previously declared policy; incorrect proposals rejected by the verifier are ordinary outcomes, not shared-verifier failures. A contradictory oracle or evidence-integrity problem instead stops immediately. Do not repair the oracle during the run.

**Outcome B — incremental engineered-record value:** preserve all existing investment conditions: complete interpretable sixteen-unit screen; C completes at least 6/8 positives and at least one in every positive stratum; at least two more than B; no B success lost; zero harmful, irrelevant, incomplete or unsupported accepted C edits; no hidden per-input regression in accepted C repairs; correct authority/unsupported refusals; equal maxima, zero inference and the declared cost limits.

C's first harmful or irrelevant acceptance triggers the safety stop. Every remaining unit is **NOT RUN**, not a tie, exclusion or inferred success. Preserve the harm and observed prefix; no favorable complete-sample effect is extrapolated. B ordinary errors remain outcomes; baseline weakness is not a reason to discard cases. Report per-input regressions even if both final programs fail another obligation.

Outcome B can descriptively show a relative gain while Outcome A fails. **B never overrides A.** Such a result cannot authorize a trusted mechanism or validate acquisition feedback. A complete tie/loss, one extra fix, efficiency-only gain or insufficient coverage fails this particular investment gate and favors the cheaper B, provided B's common measurement system is itself qualified. If B repairs seven or eight positives, accept that C cannot earn the required two-fix margin; do not adjust the exam.

Five refusal slots test non-execution authority, not five behavioral harm trials. A safe refusal on a repairable case is an unsolved task. Report eight-positive paired counts and all negative/refusal categories separately. Sixteen constructed, related units support a feasibility screen, not a natural-workload or population reliability estimate. No arbitrary harm weights, p-value search or post-result threshold changes.

## 10. Exact operational and engineering costs

**Proposed accounting, not measured performance.** For arm `X`, define:

`T_op(X) = Σ over all 16 units [proposer + shared analysis + original decision evaluation + proposal decision evaluation + durable decision journal + operational cleanup]`.

Each bracket is elapsed machine time on disjoint intervals: common analysis inside the proposer is included in proposer time and separately attributed, **not counted twice**. Analysis independently repeated by the controller is an additional actual cost. Setup/contract checks required for ordinary reuse are included. No-cache originals are charged to the arm that executes them. One-time common operational setup is allocated half to each; proposer-specific loading/record handling is charged to its arm. Both arms receive identical apportionment rules, without omitting failed attempts or refusals.

The runtime test is exactly **`T_op(C) / T_op(B) ≤ 1.25`** over a complete run; an invalid/zero denominator or incomplete run cannot pass. Also retain **`max(0, ΣT_proposer(C) − ΣT_proposer(B)) ≤ 10 seconds`**. Measured stochastic machine noise and schedule are disclosed; do not selectively repeat scored timing to improve the ratio. Faster rejection and longer successful verification are genuine costs, not corrections applied after results.

Report separately: custody generation/validation, independent oracle review, original/final hidden scoring, qualification/replay, safety monitoring not inherent in ordinary reuse, final audit analysis and total experimental storage/time. These do not dilute the operational ratio, but remain part of total experimental cost and phase clocks. Monitoring or bookkeeping required by the operational boundary belongs in operational cost and is apportioned symmetrically. Deployed-cost estimates are scoped to this prototype path, not production forecasts.

One incremental engineer-day means **eight active person-hours total**, not eight hours per contributor. Charge C's record design/curation, interpreter, C-only tests, C-specific qualification, independent review, and any extra common-analyzer feature needed solely by C. Do not reclassify C engineering as shared to stay below eight hours. Human waiting is separate. Prior sunk design work and unmeasured future maintenance are disclosed separately, never claimed zero. Work logs and reviewer declarations, not code-line count, establish this budget.

The direct common polarity rule encodes the identified relationship without a record schema/interpreter/versioned clause evaluator. **SUPPORTED INFERENCE:** this is cheaper to maintain for the current fixed relationship; actual engineer hours are unmeasured. The existing 1–2 day common implementation plus 1–2 day independent qualification estimates remain uncertain planning estimates, not spending authorization. No C cost should be incurred after this simplicity decision. No additional hardware, model inference or service is proposed.

## 11. Independent custody and oracle-review prerequisites

**BLOCKED / UNKNOWN:** no independent custodian, oracle reviewer or approved execution identity is established. This amendment assigns nobody and claims no independence from the prior author. Different model names or readable sessions in one repository are not custody. Missing custody preserves HOLD for any future experiment, including a cheaper prototype's scored qualification.

| Required role | Controls / access | Required separation evidence | Current status |
|---|---|---|---|
| Approved task owner/specification authority | Versioned intended behavior and observation scope | Accepted responsibility, signed/independently controlled approval registry, source/revision/interpretation hashes | Unassigned/unapproved |
| Implementer | Public specification/development controls and frozen code | Cannot read scored bodies, labels, seeds, witnesses, expected values or hidden journals; exact account/tool privilege inventory | No implementation authorized |
| Independent case custodian | Hidden sources, seeds, instantiations, witnesses and rejection ledger | Not the party solely implementing/tuning B/C; accepted role, exposure declaration, protected storage and chain of custody | Not established |
| Independent oracle reviewer | Owner specification, translation, oracle and custody validation | Obligation-by-obligation review independent of solely authoring the oracle or tuning arms; no outcome-based expectation changes | Not established |
| Controlled decision executor | Frozen proposals, current contract and decision partition | No hidden originals/finals, witness outcomes or scorer journal; actual access-denial evidence | Proposed only |
| Controlled hidden-scoring identity | Sealed decisions and hidden partition | Cannot feed back to proposer/acceptance; independent identity/access manifest | Proposed only |
| Final evidence reviewer | Full released bundle after sealing/scoring | Accepted review; role-overlap/prior-exposure disclosure; independent reconciliation, no selective exclusions | Not established |

Smallest proposed workflow, requiring acceptance before use:

1. An independent custodian controls an offline environment or genuinely separately permissioned account, outside implementer access. The task owner approves the formal task family. The oracle reviewer checks intended rank order, tie-break, singleton, type and ownership obligations against it. An internally consistent but wrong interpretation is still possible; disagreements block, not invite relabeling.
2. Record exact storage paths, owners, user/group/ACL/tool permissions and available privilege escalation. The implementer must lack a permitted route to hidden material, including logs, caches, backups, shared history, sync and inherited descriptors. A separate local UID is useful only if these controls actually hold; administrator access or shared readable workspaces defeat a claim of inaccessible custody. No account is created here.
3. Use harmless dummy canaries to prove authorized custodian/scorer reads and denied implementer/proposer/candidate reads from their actual identities, in both rooms, before any hidden source exists. Also test positive own-root reads. Save exact paths, identity/privileges, exit/error and hashes. Folder names or a declaration of blindness are insufficient.
4. Freeze implementation, common rule/order, analyzer, oracle/observer/checker, resource/visibility policy and, only if separately justified, C record. Custodian then commits seed/allocation and instantiates cases within §6 limits. Preserve every eligible/rejected attempt, exact reason and timestamp. No B/C outcome or priority feedback may guide selection.
5. Export only sanitized source/current-task projections to proposers during the controlled run. The **program** must see its task; the **implementer** must not inspect scored bodies for tuning. Both arms run on the same approved machine/runtime; offline preparation does not grant another environment's cache authority.
6. Decision executor has decision tests only. After both decisions/output hashes seal, a separate scorer reads hidden original/final evidence. Sealed proposal processes are gone; hidden outcomes cannot select another edit. A supervisory safety-stop signal may halt the run, but does not expose scoring to an active proposer or create a retry.
7. Release the complete committed bundle and rejected/NOT RUN evidence to the final reviewer after the run/stop. Reconcile hashes, access logs, budgets, ordering and all harms. Do not repair an exposure breach by regenerating a favorable holdout inside the same pass.

Designer/implementer overlap may be disclosed. Implementer/custodian must be substantively separated; the sole oracle author cannot be its only independent approver. Other overlaps must be declared and cannot be counted as extra independent corroboration. Offline controls do not require a relay, network, paid service or model subscription. If no accepted independent custodian exists, stop with HOLD; do not quietly substitute a same-author demonstration.

Current authority-state behavior remains unchanged: VALID may enter shared analysis; UNKNOWN, CONFLICTING, STALE and UNSUPPORTED prohibit repair. All reason flags persist. Only externally approved task revisions can resolve missing/contradictory intent; records may not certify or weaken requirements. Finite decision/hidden observations support bounded conformance, not arbitrary correctness, identity preservation or unknown side effects.

## 12. Minimal authorization checklist and next action

**Immediate action:** independent human review of the simplicity conclusion and common-rule specification. No case custodian needs to generate material to confirm that the stated record lacks a distinct informational hypothesis. No C implementation is recommended.

If a research-only **B plus independent verifier** prototype is considered worthwhile later, approval must first specify the reduced objective and scope, competent shared logic, approved task authority/oracle and accepted independent custody plan. Keep the existing isolation/worker/durable-journal/cleanup concepts, but qualify new paths, proposer, checker and observer afresh. A B prototype may assess engineered proposal/verification feasibility; it cannot demonstrate acquired experience's value.

Checklist before any construction or execution:

- Independent review accepts this amendment and its limits; old freezes stay immutable.
- Human explicitly selects and authorizes the smallest prototype; no automatic permission from this report.
- Task owner, custodian, oracle reviewer and final reviewer accept roles and overlap disclosures; access plan is approved.
- Interfaces enforce identical current facts, no hidden answers, inert records if ever reconsidered, committed proposals and separate acceptance/scoring.
- Public control manifest and exact new boundary/observation qualifications are approved, within declared caps; runtime/serialization/memory requirements are enforceable enough for an attempt.
- Actual implementation hashes are frozen before scored instantiation; real access evidence and throughput qualification precede scored authorization.
- Experimental execution receives its own explicit permission. Failed qualification stops that version; no fix-forward or broader grammar to preserve a result.

For C there is an additional prerequisite **before spending any of its eight hours**: a credible residual relation that survives the common-rule redundancy audit. It is absent. If reviewers agree, retain B conceptually and close this C investment proposal rather than proceed through the checklist by momentum.

The eventual learning question still requires independently acquired, verified content under a fixed interpreter, then paired new-task access/no-access evaluation with the same capable model/tools/current facts/verifier/budget and fresh-process persistence. If the no-record system cheaply derives the same relation, there is no demonstrated retained benefit. This report authorizes neither that acquisition nor a new net-utility workload.

## 13. Repository integrity and reproducibility

**DIRECTLY VERIFIED opening:** branch `vsl-implementation`; HEAD `e5acbb09cece8d1791fa6d967fe57067137a8cff`; cached origin/main `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`; ahead/behind 4/0 without fetching; staging empty; fourteen pre-existing tracked modifications. Full untracked inventory and tracked hashes are in [opening.json](sac1r2_a1_20261008/opening.json). All 516 authority pins matched. This includes prior reports/protocols, production records/sources and qualified historical evidence.

Key immutable SHA-256 values:

| Artifact | SHA-256 |
|---|---|
| SAC-1R2 design | `275313ac2877eacd92be2eac235d9ec18ed6dd9697d6a3c1604259d3832575f2` |
| SAC-1R2 readiness review | `0f1cdad9c430d43282aa936d6472763f757c4ac44815a2706fee79cb1bc7da60` |
| SAC-1 v1 protocol | `be6637d7bb0bd2c491fce6797d50e219baeea4a9e7cfd2c86442490a0d8a09b4` |
| Production Skill A v4 | `aa00c0aee4563f25254f624255605afb5448ebfb8a08c0b4833fb6796a098e7e` |
| Production matcher | `063cd1449f2035f4f273b423fa732130bcfec1d5740fda5895687fbeba30a8f7` |

[Opening processes](sac1r2_a1_20261008/opening_processes.txt): Echo 55361, October 1 15:45:19; watchdog 56610, September 28 09:44:38; Ollama 1991, September 19 10:57:03; auxiliary PIDs 55366/84828/84838/35573 recorded. No service was signaled, restarted or contacted for inference. Live mutable FAISS, metadata, RiverBrain, self-model and temporary self-edit state are separately fingerprinted, not scientific inputs. Changes in those files alone do not identify their writer.

Only this report and additive documentation/data under `audits/sac1r2_a1_20261008/` are authored by this mission. Inline bookkeeping reads JSON and hashes files; no experimental module import, candidate execution, new case generation, oracle scoring, learned-state intervention or inference experiment occurred. Historical raw outcome summaries were inspected; SAC held-out answer matrices were not opened. No agents/relays were invoked. No staging, commit, push, reset, production edit or cleanup of user files.

Closing checks and the exact additive file inventory are recorded in [closing.json](sac1r2_a1_20261008/closing.json), process observations in [closing_processes.txt](sac1r2_a1_20261008/closing_processes.txt), and deliverable hashes in [evidence_manifest.json](sac1r2_a1_20261008/evidence_manifest.json). The manifest attests this document's bytes, **not an executable scientific protocol freeze**. The same assistant reviewed earlier proposals; this amendment is not an independent custodian/oracle review.

**DIRECTLY VERIFIED closing, 13:21:38 PDT:** all 516 pinned authorities and all fourteen pre-existing tracked modifications retain their opening bytes; branch/HEAD/cached origin and empty staging remain unchanged. No opening status entry disappeared. Observed process PID/start/parent/command rows are identical. FAISS, memory metadata, RiverBrain and self-model hashes evolved; the temporary self-edit file did not. These mutable files were not inputs and were not written by the research commands; the observations do not establish who wrote them. No global live-state byte-stability claim is made.

## 14. Final answers and investment recommendation

**Q1. Does B capture the essential relationship?** Yes, at the design/algebra level where ranking, bindings and precedence are resolved. Runtime coverage has not been measured.

**Q2. What remains record-only?** Historical references and optional residual ordering choices. No independently supported additional applicability capability is specified.

**Q3. Transferable information or inexpensive rule?** The principal proposed relation is an inexpensive generic rule. Counterexample-driven transferable information is conceivable but currently unimplemented and unqualified; references alone do not supply it.

**Q4. Is a fair held-out B/C comparison still justified?** Fairness controls can be specified, but no credible incremental-information hypothesis remains to justify its cost now. Do not manufacture competing sites or weaken B. The dormant allocation is not permission to create cases.

**Q5. Does the resource ledger fit?** Yes conditionally: 4,752 candidate plus 32 proposer launches = 4,784, leaving 1,216 under the main 6,000-attempt cap, without cache credits. Separate qualification remains 128. It does not guarantee runtime completion.

**Q6. What precedes a thirty-minute attempt?** Explicit implementation/execution approvals, independent custody/oracle acceptance, public two-room and observer qualification, bounded serialization and monitoring, durable-evidence tests and measured throughput/timeout overhead supporting an attempt. None occurred here.

**Q7. How is shared-verifier failure separated?** Outcome A reports REQUALIFICATION REQUIRED or the relevant integrity/blocking outcome independently of Outcome B. A C gain never overrides it. C harm stops with remaining units NOT RUN.

**Q8. What custody evidence is missing?** Accepted independent roles, owner/oracle attestations, controlled storage/identities, audited access paths, positive/denied dummy-canary results, implementation-before-case commitments and post-seal scoring/release evidence. All remain prerequisites; no consent was assigned.

**Q9. Smallest justified implementation?** None is authorized. If separately approved, a research-only generic polarity proposer with the bounded common verifier/authority interface is the smallest surviving prototype concept. Do not implement C or a general analyzer for this family.

**Q10. Where should investment go?** Retain the cheaper architecture and postpone this semantic-record mechanism. Preserve the eventual research question of independently acquired information adding value over an equally capable no-record system; do not reopen broad acquisition merely to fill the record. The immediate next action is human review of this stop decision, not another implementation layer.

**Final recommendation: RETAIN B — POSTPONE C.** All new candidate executions and local/external experimental inference calls: **0**. Neither positive nor negative retained-learning utility was measured. **STOP BEFORE IMPLEMENTATION.**
