# FeralEcho — E5-mini Final Adjudication

Date: 2026-09-16. Investigator: Codex. Read-only adjudication; no implementation or inference.

## 1. Final verdict

**READY WITH CHANGES.** The changes below freeze a small, four-arm experiment. No further architectural reconciliation is needed before implementing its isolated G0 instrumentation. Actual model execution remains gated on qualification and a frozen task manifest.

| Claude correction | Independent classification | Decision |
|---|---|---|
| Add spec-only zero-teaching procedure arm Z | **REQUIRED** for the intended teaching-experience attribution | Retain Z, but match construction and selection opportunities with P. Z alone does not distinguish information acquisition from example-triggered use of prior knowledge. |
| E5-specific condition-integrity manifest/validator | **REQUIRED** | Extend the common recorder/checker with E5 information-access invariants. A separate new logging framework is unnecessary. |
| Increase negative/near-match controls | **USEFUL BUT NOT REQUIRED** for identifying the main teaching contrast | Adopt three distinct near-match and three unrelated probes per base family. They support a conditional pilot error estimate and detect failure modes; they do not certify a low population error rate. Stronger applicability claims would require stronger evidence. |

**Smallest additional causal control:** paired, randomized teaching-content micro-worlds within the existing arms. Hold the public specification and evaluation query fixed, vary an experience-only local convention, and test whether the retained artifact follows that convention correctly. This adds a controlled information intervention, not a fifth principal arm.

**Confidence:** high in the identification limits and the need for actual-input validation; moderate in the usefulness of the proposed pilot. No result about FeralEcho's learning performance has been obtained.

This report supersedes the E5-mini specification in the two reviewed reports, not the larger capability roadmap.

## 2. Observation boundary and primary evidence

Opening HEAD: **2fba42644c82b9f7096276f4dd338d615cf1bcce**. Opening short status including all untracked paths: **178 entries** (27 modified tracked, 151 untracked). Capture began at **17:47 UTC**. The full opening status and closing comparison are in §15.

Read:

- [Capability-growth reconciliation](2026-09-16_capability_growth_reconciliation.md), especially §§6, 11, 13, 16–18 and its final E5-mini answer.
- [Claude's preimplementation review](2026-09-16_e5_mini_adversarial_preimplementation_review.md), including its causal-chain, negative-control, isolation and result-interpretation sections.

Neither report is an execution artifact. Here **OBSERVED** means directly read source/artifact; **INFERRED** means design reasoning; **PROPOSED** means a frozen requirement for future implementation. No proposed control has passed merely because it is described here.

| Evidence | Direct recheck | Consequence |
|---|---|---|
| scripts/task_type_behavioral_experiment.py:207–219,267–273,311–318 | OBSERVED(source): clears DIRECT_ECHO_TASKS before conditions; A and B both set personal and the same system input. | Assigned labels cannot establish execution or evidence exposure. This is a concrete relevant failure mechanism, not proof the new experiment has already failed. |
| app/ollama_handler.py:97–143 | OBSERVED(source): explicit messages bypass identity construction; another path prepends repository identity. Adapter returns text while discarding other response fields. | Record actual outbound requests below transformations; do not trust a planned prompt or text-only result. |
| sandbox/echo_sandbox.sb:24–49 | OBSERVED(source): deny-default with broad file-read permission, scratch writes and network denial. | Existing profile does not by itself hide other arms' or withheld files. No qualification was run here. |
| scripts/run_capability_pilot.py:117–166 | OBSERVED(source): current isolation redirects River state before constructing its accessor. | Do not import that harness or production state just to reuse an isolation label. E5 needs neither RiverBrain nor its pickle. Historical numerical writer counts in comments were not independently remeasured here. |
| Reconciliation §§6,13,16–17 | OBSERVED(text): general call/attempt records, family/arm stores, access policies and protected test files already specified. | Claude overstates that inter-arm protection is wholly absent. The real missing detail is an executable E5-specific conformance contract, including Z. |

No production import, state deserialization, inference, API call, process-control action, relay/hub action or experiment rerun occurred. Source hashes were captured before adjudication. Statistical arithmetic below was performed in memory; no scratch file was needed. Runtime health was not investigated in this mission.

## 3. Adjudication of Z and the extra-reasoning alternative

**Original position:** P versus E/N tests a taught procedure against episodes and no acquired memory; representation/use is the intended intervention.

**Claude challenge:** P construction is an additional reasoning call that can reconstruct pretrained knowledge without learning anything useful from the particular teaching episodes.

**Independent verdict: REQUIRED, with a narrower interpretation than Claude gives it.**

Without Z, a model could ignore every teaching result, write an effective textbook procedure from the public family description, and produce P>E/N. That is a valid counterexample to the original attribution. An unrelated or shuffled procedure does not control this counterexample.

Z controls it only if P and Z use:

- the same generator/package, system instruction, procedure schema and construction-call/output ceilings;
- the same public family specification and equal opportunity to reason, without an extra P critique, retry, best-of selection or teaching-based promotion gate;
- identical application instructions, solver, task, available operations and solving budget;
- separate fresh sessions and no hidden access to teaching through metadata, files, logs or selection decisions.

The only intended constructor-input difference is the teaching-experience field: populated in P, empty in Z. The resulting artifacts will differ; that is the mediator under study.

**Cost logging alone is insufficient.** If P gets three attempts and Z one, recording the difference does not remove it. Likewise, validating Z on teaching cases and selecting it using those scores exposes Z's construction pipeline to teaching even if the model never reads a teaching example. The minimal design therefore has one constructor call per artifact and no semantic selection or repair feedback.

Equal output limits do not make input processing identical: P reads extra evidence. The claim is a bounded effect of supplying experience to the construction pipeline, not an effect at exactly identical FLOPs. Report actual construction and inference costs.

### What ordinary Z does not eliminate

Suppose the spec says “solve these sequence problems.” Teaching examples reveal that a familiar two-pointer pattern is relevant. P>Z can then arise because examples cue a pretrained method, without introducing a previously unavailable rule or fact.

That is still an effect of the supplied experience. Selecting a known strategy using new evidence can be useful adaptation. Pretrained computation and experience use are not mutually exclusive. However, it does **not** establish the stronger statement that useful new task information was acquired, or that a new algorithm was invented.

Accordingly:

- **Ordinary matched Z is sufficient** to estimate the incremental effect of providing the teaching package under the frozen pipeline.
- **Ordinary Z is insufficient** to distinguish mere cueing from acquisition of experience-only information.
- For this mission's stronger information-source question, add the paired content intervention in §7. It is required within the pilot, not an indefinite request for more arms.

A fifth generic “think harder” arm or neutral-token padding is unnecessary once P/Z construction is matched. Padding would not replicate the informational role of an example.

## 4. Adjudication of E5 condition integrity

**Verdict: REQUIRED.** Use a parameterized extension of G0's recorder and independently implemented checker, rather than build another attribution subsystem.

Claude is right about the risk but too categorical about the prior design's absence: the reconciliation already requires actual call payloads, arm access policies and family-isolated state. It does not finish E5's allowed-exposure predicates or test their enforcement.

The central invariants are informational, not just call-count invariants:

- N has no acquired artifact or construction call.
- Z construction has no teaching observations, feedback, teaching-derived selection, world convention or P/E artifacts.
- P/E construction receives exactly the assigned teaching pool; P/Z use identical construction instructions apart from supplied experience.
- At solving time P receives only its frozen procedure, E only its episode artifact, Z only its spec-only procedure, and N an empty memory field.
- No constructor receives withheld queries, expected answers, test feedback or evaluation-derived rankings.
- Every solver receives the same public task/specification, action interface and baseline instruction for a paired query. An arm label is not shown to it.
- State-specific information reaches a solver through its assigned memory artifact, never a world label, filename, error message or ledger field.

### E5 manifest

Retain run/protocol ID; base-family, micro-world, query and split IDs; assigned arm; attempt/call IDs and parents; allowed evidence-set hashes; actual constructor and solver requests/responses; ordered system/user messages; artifact hash and creator call; construction attempts and any rejection; semantic-feedback exposure; schema/version; model/package/backend binding and options; timestamps, token/call caps and actual cost; process/session identity; read capability profile; snapshot and reload hashes; terminal status; oracle result/UNKNOWN; and condition-validity result.

Explicitly record **zero council entry, zero synthesis routing, zero TOOL-LIST and empty model tool definitions** for this standalone single-call solver design. The local deterministic result runner is separate from model-call tools. Any unexpected route or tool schema fails conformance.

The checker must compare gateway-observed payloads against independently specified allowlists and lineage rules, not import the arm builder's result as expected truth. It verifies the entire assigned-slot ledger before outcomes are unblinded, recomputes hashes, and checks reuse references. A correct hash with the wrong permitted parent is a failure.

Transport records establish what was sent, not everything a worker could read. Use restricted constructor/solver compartments, a trusted supervisor, a private inference endpoint without cross-request conversation retrieval, no writable production paths and no hidden feedback into model requests. The trusted supervisor/oracle may hold all states; that does not entitle a model worker to access them. No production daemon is used for the experiment.

A planted canary absent from the output does not prove absence of access. OS/access qualification and actual-request records are complementary. Policy enforcement is tested only against sacrificial fixtures, never by attempting writes to real production files.

**Failure handling:** preserve assigned identity and raw evidence; mark CONDITION_INTEGRITY_FAILURE. Do not relabel a leaked Z as P or remove the family. A systematic violation stops that protocol version. Path-invalid trials cannot support the causal contrasts, even if their outcomes are favorable.

## 5. Adjudication of negative and near-match controls

**Classification: USEFUL BUT NOT REQUIRED as a sample-size expansion for the primary P−Z identification.** Valid basic negative probes and explicit applicability measurement remain required. Estimating a low general false-application rate is a separate, stronger claim.

Claude's review alternates between “MUST FIX” and “SHOULD ADD IF CHEAP” for the same expansion. Its rationale also contains two errors:

1. A deterministic always-apply policy will fail every valid near-match opportunity. Four accurately observed probes can expose that behavior. Four cannot reliably estimate an unknown rare-error rate or cover varied failure modes.
2. Twelve error-free probes do not establish a false-application rate below 10%.

For independent Bernoulli opportunities with zero observed errors, the exact one-sided 95% upper bound solves (1−p)^n=0.05:

| Independent opportunities n | Upper error-rate bound |
|---|---:|
| 4 | 52.7% |
| 12 | 22.1% |
| 24 | 11.7% |
| 29 | 9.8% |
| 36 | 8.0% |

These are analytic illustrations, **not valid bounds obtained from this proposed family-clustered pilot**. Multiple tasks using the same procedure share failure causes. Counting seeds, mirrored micro-worlds or reused responses as independent opportunities would overstate precision. The reconciliation already called its 12-family run a pilot; Claude incorrectly treats its 12 near matches as sufficient for the later confirmation bound.

### Minimal improvement adopted

Keep four base families. Give each **three distinct near-match queries** and **three unrelated queries**, alongside four related queries. Near matches separately violate a type/schema, scope/version, or boundary/precondition rule; each has a clear correct alternate action. Do not create three cosmetic copies of the same failure.

Measure separately:

- **Operational false application:** the solver commits to the FAMILY action where its public applicability contract is false.
- **Negative transfer:** actual objective output worsens relative to N/E on those cases.
- **False abstention:** rejects a valid related-family application.
- **Unknown/malformed decisions:** reported separately, not counted as correct non-application.

For this pilot, require a structured action choice FAMILY / GENERAL / ABSTAIN that the trusted local runner actually dispatches and records, with the submitted bounded program or result. All arms receive this same interface. FAMILY commits to use the family method for this input; GENERAL uses the submitted general solution; ABSTAIN produces no answer. The runner records the entrypoint taken and scores its preconditions independently.

This gives an observable application-policy decision. It **does not prove which concepts or memory a model internally used**: GENERAL may still reason using familiar family knowledge. Record the explicit policy error and final outcome rather than pretend to observe cognition. A free-text “I did not apply it” is not the measure.

The expanded probes provide a useful **conditional empirical rate on this frozen battery**, with family-level counts. They do not license “false application is below 10% in deployment” or “the applicability condition was learned.”

## 6. Exact causal contrasts

Let S be the common public specification, T_w the teaching observations in micro-world w, G the frozen procedure constructor, C the episode constructor, and B the common solver/runner.

- P_w = G(S,T_w).
- Z = G(S,empty).
- E_w = C(S,T_w).
- N has an empty acquired-memory field.

A contrast below averages objective outcomes over the same frozen queries, world weights, solver policy and task budget. Randomized execution order and fixed state reduce order effects; the tiny purposive family sample does not establish population representativeness.

| Contrast | Exact identifiable meaning under the specification | What it does not isolate |
|---|---|---|
| **Z−N** | Total effect of constructing, retaining and supplying a spec-only procedure instead of no acquired artifact. | Construction reasoning versus artifact format versus prompting effects; proof the knowledge came from pretraining rather than inference over S. |
| **P−Z** | Incremental effect of supplying T to the otherwise matched procedure-construction pipeline, transmitted through its retained output. | A pure “learning module” effect, new algorithm invention, or novel information acquisition without the content intervention. |
| **P−E** | Difference between the frozen procedural and episodic construction/application policies operating on the same teaching pool, with matched call ceilings and a complete episode comparator. | Pure typography or pure compression. Different representation instructions can induce different reasoning; that remains part of the policy treatment. |
| **P−N** | Total taught-procedure pipeline advantage over the solver with no acquired memory, for the tested task/budget. | Teaching alone, representation alone or the extra construction pass alone. |

P−N = (P−Z)+(Z−N) is an arithmetic decomposition of the same averaged outcomes, not a proof of mechanistic mediation or absence of interactions. P−E is a different comparison. The four arms do not identify every interaction among experience, artifact format and computation.

The largest remaining ordinary-design confound is **experience as a cue rather than a source of needed information**. Construction/selection asymmetry is a separate preventable confound. The content intervention addresses the former and the fixed one-call policy addresses the latter.

Residual limitations after repair: curated-task choice, one artifact per condition, stochastic construction, oracle defects, limited family coverage and the representation-policy bundle. These limit precision/generalization. None requires another primary arm to estimate the specified conditional contrasts.

The strongest remaining mechanistic ambiguity is that P may store new local facts/parameters and combine them with an already-known algorithm. That is compatible with experience-caused information reuse through the procedural artifact; it is not proof of acquiring a new method or of a distinct internal procedural-memory system. A fact-only representation control would be useful for that stronger mediation question, but is not required for the four contrasts requested here. Do not silently rename information reuse as algorithm learning.

## 7. Minimal frozen four-arm E5-mini specification

This remains **four base families**, not twelve independent observations manufactured from variants. The paired content control creates eight family/world states, which remain clustered within four base families. Expanding to 12 families later would still be a pilot unless a separate confirmation plan justified it.

### 7.1 Task domain and content intervention

Use finite deterministic JSON/data-transformation tasks, with a trusted reference and short public applicability contracts. Four predeclared recipe classes:

1. Normalize and join records using an opaque local code mapping.
2. Group/reduce records using an opaque local priority or tie convention.
3. Bucket boundary values using a local endpoint convention.
4. Fold events using an opaque event-to-update convention.

These are general task recipes, not the final hidden questions or answers. The task custodian must generate, validate and seal the actual fixture manifest before any pilot generation. Constructor workers must never see that private manifest.

For each base family, create **two paired micro-worlds**, w0/w1:

- Public S and current evaluation-query bytes are identical across the pair.
- A task-relevant local mapping/convention is randomly assigned after S is frozen. Its realization is absent from S, names, IDs and model-visible metadata.
- Two short teaching observations per world distinguish the possible conventions. Use the same teaching-query structure in both worlds; only the relevant observations/feedback differ.
- The four withheld related queries use new inputs, not copies of teaching answers; at least two require composition or a new edge case. Reference outputs differ between worlds for all four.
- Both worlds are legitimate consistent tasks. A procedure from w0 is inappropriate in w1 because the convention differs, not because deliberately garbled text was injected.

The same base algorithms can be pretrained. What cannot be recovered from S alone is the random local convention. Success establishes reuse of that information, not invention of the underlying algorithm.

N/Z lack information needed to determine the convention uniquely. Their resulting disadvantage is intentional for this diagnostic, **not evidence of a weak base model**. Correct abstention is recorded as calibrated uncertainty but does not count as completing an information-dependent task. The pilot is an information-transfer experiment, not a fair-information general-intelligence ranking.

### 7.2 Teaching and withholding

Teaching consists of two bounded queries to the synthetic deterministic environment and their observed results/feedback. It need not spend LLM calls producing a doomed initial answer. These are provided observations, not autonomous lesson selection. P/E receive byte-identical episode pools for a world.

Each pool must fit completely inside the 1,024-token memory allowance, including essential inputs and feedback. If a recipe cannot meet that requirement, repair it on development material **before freezing the pilot**, not after observing which arm wins.

The custodian independently checks that the two observations identify the relevant convention, the query/output mapping is consistent, withheld answers are novel, and an opposite-world procedure produces a different result. It owns hidden outcome tests and does not write procedures.

Do not define novelty as “N failed and P succeeded.” Claude's proposed difficulty differential is circular if used to admit/exclude evaluated tasks; N success is not proof of duplication. Shared algorithms are expected in procedural transfer. Blind structural/answer-overlap review is useful, but no universal embedding-distance floor is required.

### 7.3 Artifact construction

One fixed installed model package serves as constructor and solver for the first pilot; use echo:latest resolved to a recorded immutable package identity if available at execution preflight. No model selection sweep or live production routing. If that binding cannot be established, execution is blocked rather than silently choosing a different model.

- **P:** one call per world; common procedure instruction, S and T_w.
- **Z:** one call per base family; exactly the same procedure instruction and S, with an empty experience field. The same frozen Z artifact applies to both worlds.
- **E:** one call per world to format the complete same T_w as episodes, preserving every task-relevant observed value and outcome. No withheld information or invented experience.
- **N:** no construction call and no acquired artifact.

P/Z instructions permit generic reasoning but require unknown conventions to remain unknown. E receives the same construction-call and output ceiling; it is not a deliberately truncated or unprocessed weak baseline. An independent completeness check reports whether E preserved the required episode fields. P−E representation interpretation is withheld if the comparator systematically loses them; record that construction failure rather than silently repairing E.

Freeze every first artifact. No best-of, critique, retry, manual correction or semantic validation used to select a winner. A shared syntax/size/schema gate may mark unusable artifacts, but all assigned families remain and their arm uses empty memory when construction is unusable. Teaching-based diagnostic scores may be computed after freeze, privately, without filtering artifacts or giving feedback.

Thus the word “validated” does not hide extra P selection. This mini tests one-pass construction; it does not depend on an unvalidated semantic promotion gate.

### 7.4 Solver inputs and fixed budgets

Common system instruction, S, query, action schema and memory wrapper across arms; only memory content differs. The model sees no P/E/N/Z label and no private world ID.

Initial fixed generation profile: temperature 0.2, top_p 1.0, top_k 0, repeat_penalty 1.0; context cap 8,192 tokens; constructor output cap 1,024; solver output cap 1,024. Record any unsupported option/default rather than assume it applied. Establish support and pin effective settings on public qualification fixtures before freezing a run. No silent truncation, changing temperature for failed arms or extra retry.

Use one prespecified seed per base family/query role and matched seeds for paired constructions/queries where the backend supports them. A seed is recorded experimental input, not a guarantee of bitwise reproducibility. One acquisition replicate means uncertainty in procedure generation remains part of the pilot limitation.

Each solver returns one bounded program/result and a binding FAMILY/GENERAL/ABSTAIN action. One model call, then the deterministic isolated runner/oracle; no model repair after a test result. Empty/error/malformed outputs and timeouts remain failures of the assigned pipeline; genuine oracle infrastructure failures remain UNKNOWN.

All artifacts are sealed, written to private experiment storage, and reloaded into a fresh solver process/session before evaluation. No additional 24-hour study here. The claim is performance using reloaded artifacts, not measured equivalence before/after reload or long-duration durability.

Per-call deadline six minutes; total output-token ceiling 266,240 and total inference wall-time ceiling 26 hours from the 260-call maximum, with actual time/cost reported. These are upper bounds, not expected duration. Resource admission must pass before execution; do not unload, throttle, restart or otherwise disturb production to make room. Timeout/budget exhaustion yields an incomplete pilot, not automatic budget extension.

### 7.5 Exact scale and reuse

Per base family: four related, three near-match and three unrelated queries; the same query bytes are evaluated against both possible world outcomes.

- P: 4 families × 2 worlds × 10 queries = **80 solver calls**.
- E: **80 solver calls**.
- Z: 4 × 10 = **40 solver calls**.
- N: **40 solver calls**.
- Construction: eight P + eight E + four Z = **20 calls**.
- Total ceiling: **260 model calls**, 16 deterministic teaching observations, no model retries.

Reuse a Z/N response across its two world scorings because its actual inputs and allowed state are identical. Record one response with two oracle-evaluation references, **not two independent generations**. This is intentional counterfactual scoring, not a hidden shared cross-arm cache. P/E are freshly solved for each memory state.

The frozen family-normalized outcome table can contain 320 scored arm/world/query rows while containing only 240 distinct solver responses. Analysis must preserve that dependence. Negative rows per P/E arm are 24 near-match and 24 unrelated decisions, but only four base-family clusters. Z/N each have 12 distinct decisions per negative stratum; their duplicated world scores do not double evidence.

This is a bounded research pilot, not necessarily a quick one-sitting run. If the cap is infeasible, stop before generation and reduce scope transparently; do not call a partial favorable subset the frozen pilot.

### 7.6 The additional content check uses existing outputs

For each related query q, score the P_w0 and P_w1 outputs against both Y_w0(q) and Y_w1(q), without any new model call or feedback.

The diagnostic is **matched-world advantage**: does each retained artifact solve its own world better than the opposite world, and do both artifacts correctly produce the two different required answers for the same query?

Mere presence of examples, their length or a generic additional reasoning pass is symmetric across the pair. Systematic tracking of a randomly chosen convention beyond chance would support use of information specific to the teaching results, assuming access isolation holds. A few correct paired outputs can still occur by chance; this diagnostic does not turn four families into confirmation.

Z/N supply the same response to both oracle scorings and cannot correctly answer two contradictory expected outputs for an identical query. This is a design fact, not a statistical discovery or a claim that an LLM could not guess one world.

A wrong-world score is diagnostic and remains labeled as such. It is not a fifth primary arm and cannot be pooled as an independent sample. No family is discarded for weak or reversed content sensitivity.

## 8. Minimal G0 additions

Keep G0 standalone and model-free. The former number “24” was a minimum proposed fixture count, not evidence of 24 implemented passing tests. Count concrete anomaly classes and coverage, not an invented completed suite.

Add or explicitly specialize the following fixtures in the common qualification suite:

| Fixture | Required behavior |
|---|---|
| P artifact injected into N or Z; episode/private convention in Z request | Condition checker rejects the information path before scoring. |
| Extra P construction, hidden retry or teaching-based Z selection | Detect unexpected call/selection parent and fail construction parity. |
| Teaching world mismatch; wrong family/arm parent | Reject valid-hash/wrong-lineage artifact. |
| Stale artifact or changed bytes after reload | Hash/reference verification fails; never score as intended memory. |
| Missing assigned attempt/family | Preserve assignment; close is incomplete, not a smaller denominator. |
| Oracle UNKNOWN followed through summaries | Preserve UNKNOWN and sensitivity bounds; no coercion into pass/fail. |
| Partial run with a forged clean close | Reconcile assigned slots against events; reject the close. |
| Extra hidden system text, TOOL-LIST, council call or unsupported changed options | Actual-request conformance fails. |
| Z/N reused response scored twice | Cost counts once; dependency/ref recorded; independent-N count unchanged. |
| Always-FAMILY and always-ABSTAIN stubs | First fails all valid near-match commitments; second cannot pass positive task completion. |
| Declared route differs from runner entrypoint | Flag application-measurement failure, not successful non-application. |
| Forged pass marker or candidate modification of oracle outputs | Trusted outcome channel wins; attempted tampering remains visible. |
| Cross-arm/withheld read or out-of-scratch write via path, descriptor or child | Qualified containment blocks access on sacrificial fixtures, with actual denied/allowed outcomes recorded. |
| Paired worlds accidentally reveal convention in task IDs/prompts | Packet comparison detects unintended world difference; reference checks ensure same query/different required outcomes. |

A shared truth-blind manifest checker can be reused; it must not use the treatment builder as its own oracle. The separate outcome evaluator sees hidden answers only after path validation; its feedback never reaches constructors.

Production protection and inter-arm read isolation both remain hard execution gates. Nothing here requires loading RiverBrain, building a task kernel or connecting ordinary memory. G0 demonstrates specified recording/containment behavior; it cannot certify that a scientifically biased comparison is fair.

## 9. Pilot analysis and success/failure interpretation

Report each base family, each world, every assigned artifact and all four arms. Also report equal-family-weighted descriptive contrasts; Claude's blanket ban on averages or uncertainty language is unnecessary. Do not use a pooled row count as independent N or present a p-value as confirmation.

The following are **frozen engineering progression rules**, not powered population-effect claims:

- P−Z related-task gain at least **0.15**; P−E and P−N each at least **0.10**, averaged with equal base-family/world/query weights.
- At least three of four base families show correct teaching-content tracking on at least two of their four paired related queries: both world-specific P outputs must be correct on their respective world.
- No condition-integrity failure or known oracle defect; E's essential episode content is preserved. All failed construction slots remain included.
- P has no more than **2 operational false applications out of its 24 near-match decisions** and no base family fails every near-match case in either world. Report the full numerator/denominator, not “error rate certified below 10%.”
- P's objective negative-control score is no more than 0.10 below N's on the equally weighted negative battery. A route guard and an outcome guard are separate requirements.

These thresholds choose when a promising pilot merits confirmation planning. They are not mathematical minima or proof of applicability competence. Record Z/E negative behavior as well; a P advantage obtained because Z aggressively guesses remains a real pipeline contrast but does not isolate better internal reasoning.

For UNKNOWN oracle outcomes, report lower/upper outcome bounds. A positive progression decision must survive conservative bounds, and a run without every assigned terminal record is incomplete. Do not convert infrastructure errors to scientific failures or successes. Actual model inability is an outcome, not an exclusion.

| Result | Defensible interpretation |
|---|---|
| P clears Z/E/N and correctly tracks paired teaching content | Pilot evidence consistent with useful experience-only information transmitted through a retained procedure; plan fresh confirmation. |
| P>Z but P≈E, with content tracking | Experience helps, but no procedural-policy advantage over episodes established. Episodic use may suffice. |
| P>E/N but no P>Z advantage | Extra procedure construction/use explains the apparent advantage at least as well at pilot resolution; teaching-specific advantage unestablished. |
| P>Z only on ordinary cues, not the content check | Experience-conditioned elicitation remains plausible; new useful information acquisition not demonstrated. |
| P changes with teaching but changes incorrectly | Adaptation, not useful transfer. |
| P>E but P≈N | E may be harmed by its representation, or the estimates may be noisy. This alone does not prove an unfair comparator, contrary to Claude's categorical wording. |
| Positive task gains with repeated near-match overapplication | Narrow benefit plus harmful scope errors; no “learned applicability” claim and no positive progression under the guards. |
| All arms near floor or ceiling | Instrument sensitivity/task choice limits attribution. Do not conclude experience is useless. |
| Gains appear only after excluding failed families | Headline is invalid under the frozen denominator. Preserve all original results. |

A tiny pilot can falsify a fixture-level assertion or expose a mechanism failure. It usually cannot rule out a small population benefit. A 12-family extension would still need this distinction.

## 10. Is “Z comparable to P defeats teaching” scientifically justified?

**Yes for the proposed average teaching-benefit explanation, but only with a defined meaning of comparable and a stated scope. Not as an unconditional rule.**

A nonsignificant P−Z test, overlapping intervals, or similar rounded means does not establish equivalence. This pilot reports descriptive comparability and may decide not to invest; it does not thereby prove no effect.

For a later appropriately sized equivalence assessment, define a practically meaningful margin in advance—here **±0.10 absolute related-task success** is the planning margin. Evidence that the paired effect lies inside that band supports practical equivalence on that distribution. A one-sided upper bound below +0.10 rejects the hypothesized useful gain of at least ten points, not every possible tiny contribution.

If P and Z are practically equivalent while both outperform E/N, **the claim that teaching provides the material incremental outcome advantage should fail**, for the specified average endpoint. Procedure construction/use is sufficient to explain that advantage within resolution.

But neither equivalence nor a pilot tie proves that no information entered P:

- P might encode teaching information that does not improve the measured task score.
- Gains and harms may cancel across predeclared strata.
- Z may solve easy tasks at ceiling; P has no room to improve.
- The paired content check may show a real teaching-dependent benefit on a declared subset despite a zero overall mean.

Report those distinctions rather than erase genuine subgroup evidence or rescue a failed average hypothesis post hoc. The primary interpretation cannot be retained merely because P>E/N.

## 11. Exact permitted and forbidden claims

If the positive pilot rules pass, a permissible report is:

> “In this four-base-family pilot, under a frozen solver and construction budget, taught-procedure artifacts outperformed spec-only procedures, complete episodic artifacts and no acquired memory on the reported related-task measures. Paired randomized-convention probes showed that outputs tracked information available only in teaching, using artifacts reloaded before evaluation. This is pilot evidence for experience-caused information reuse through the tested procedural pipeline, and a reason to plan independent confirmation.”

Include actual effects, all family results, errors and condition validity next to that wording. If only some endpoints pass, state only those results.

**Not licensed:**

- “Echo learned” without qualification, or proof of general procedural competence.
- Accumulated competence, sustained growth or autonomous self-improvement.
- Acquisition of a previously unknown algorithm, changes to model weights or a claim that pretrained knowledge played no role.
- A pure procedure-format effect, independently of construction and application policy.
- Applicability error below 10% in general, proven safety or reliable production deployment.
- Naturalistic task superiority from the intentionally information-asymmetric micro-world diagnostic.
- Durability over days, or even a measured pre/post-reload equivalence: this mini evaluates only reloaded artifacts.
- That more experience will keep improving the system.

Claude's statement that any “competence increased” wording necessarily requires accumulation is too broad: a controlled study can establish a scoped one-time task improvement. Here the specific constraint is pilot precision and scope, not a rule that every improvement must be longitudinal. Do not use that correction to make a broad Echo-capability claim.

## 12. What would falsify the teaching-experience interpretation?

Three different failures must remain distinct:

1. **Attribution/design failure:** Z saw teaching, P got extra selection, hidden answers leaked, or paths were misidentified. The experiment cannot answer the question; neither teaching nor pretraining explanations are scientifically falsified.
2. **Observed mechanism failure in this pilot:** P's outputs do not correctly follow the paired convention changes, or it ignores the relevant teaching evidence while Z matches its benefits. No experience-only information-transfer interpretation is licensed for these observations.
3. **Evidence against a meaningful average teaching advantage:** with a valid, sensitive instrument and adequate precision, P−Z is bounded below the preregistered meaningful benefit, or equivalence is established. The material teaching-benefit explanation is rejected within that domain/budget.

P outperforming E/N cannot compensate for the absence of a P−Z benefit. Conversely, an underpowered null cannot falsify all possible experience-driven learning. The experiment tests a particular one-pass construction/application policy, not whether learning is possible in principle.

## 13. GO / NO-GO for implementation

**G0 implementation: GO.** Build the isolated task/attempt recorder, actual-request stub, information-lineage checker, known-outcome oracle runner, role/access compartments and the named qualification fixtures. Keep inference/network off by default. This is implementation readiness, not authorization to implement during this read-only mission.

**E5-mini implementation: GO for the standalone four-arm module specified here.** It can be implemented against a mock transport while G0 is qualified. Real model execution is **NO-GO until** G0 passes, actual task/role/budget/package manifests are frozen, the independent checker passes, and private inference/resource isolation is demonstrated.

No new semantic promotion service is needed. No further review of E8, scheduling or autonomous architecture is a dependency. If G0 fails, preserve the failed fixture, fix or narrow the instrument and requalify; do not use favorable model outputs to waive the defect.

## 14. Evidence fingerprints

Hashes captured before substantive adjudication and rechecked at completion:

```json
{
  "audits/2026-09-16_capability_growth_reconciliation.md": "836fa7f04832676bf98e687511904f62d348333710d49553d4a265c4e93d3fdf",
  "audits/2026-09-16_e5_mini_adversarial_preimplementation_review.md": "5e2617938f4d7764373d651125065b7998f96fc1f4e3c96701846dc26151fcb2",
  "scripts/task_type_behavioral_experiment.py": "af871d4c82688c8542880bb60cdc341fc37872267caa22c1ecc76fbf1c20b377",
  "scripts/run_capability_pilot.py": "3c650144dd2fce505caf0747cf7f8d4de6c531c7e4fdd0921bcd778c430bf8b1",
  "app/core/river_deliberation.py": "5d1aa77911509ebbc90d01cd084e5ac3b4c8bd7b9790bc2780b5ce226c253585",
  "app/ollama_handler.py": "7b926934abcde70b388e7366ad31e5e3916a833376372f86c37946c99901cadd",
  "sandbox/echo_sandbox.sb": "49eb3eab677af662e05cbae72fc27bde53d2650ba4f3eee05c98f6a31df4419e"
}
```

Primary source evidence is summarized in §2. Reviewed report claims are cited as text, not treated as independently established results. The binomial calculation in §5 was evaluated directly from its displayed formula in memory. No experimental dataset was executed or altered.

## 15. Opening/closing Git and filesystem integrity

Opening HEAD: **2fba42644c82b9f7096276f4dd338d615cf1bcce**.

Full opening `git --no-optional-locks status --short --untracked-files=all`:

```text
 M CLAUDE.md
 M PENDING_DECISIONS.md
 M app/core/echo_ground_truth.py
 M app/core/liveness_ledger.py
 M app/core/provenance_check.py
 M app/core/river_deliberation.py
 M app/core/self_edit_convergence.json
 M app/core/self_edit_generated.py
 M app/core/self_edit_manager.py
 M app/core/shadow_model.py
 M app/core/snapshot_manager.py
 M app/core/temporal_environment.py
 M app/emergent_scheduler.py
 M app/maintenance/night_cycle.py
 M audits/2026-09-14_tier5_followup_experiment_design.md
 M claude_relay/.last_seen_from_air.json
 M claude_relay/README.md
 M claude_relay/from_m5.md
 M claude_relay/relay.py
 M logs/janitor_report.json
 M research/OPEN_QUESTIONS.md
 M run.py
 M sandbox/safe_exec_wrapper.py
 M sandbox/scripts/temp_self_edit.py
 M scripts/verify_liveness_ledger.py
 M scripts/verify_provenance_check.py
 M staging/self_edit_candidate.py
?? .claude/plans/verified-humming-otter.md
?? .claude/skills/README.md
?? .claude/skills/feral-forensic-audit/SKILL.md
?? .claude/skills/feral-forensic-audit/references/adversarial-checklist.md
?? .claude/skills/feral-forensic-audit/references/evidence-ledger-schema.md
?? .claude/skills/feral-forensic-audit/references/evidence-vocabulary.md
?? .claude/skills/feral-forensic-audit/references/integrity-and-safety.md
?? .claude/skills/feral-forensic-audit/references/report-template.md
?? .claude/skills/feral-independent-review/SKILL.md
?? .claude/skills/feral-independent-review/references/reviewer-checklist.md
?? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl
?? app/experiments/real_trace_f2_provenance/_scratch/river_brain_scratch.pkl.lock
?? app/experiments/task_type_ground_truth/__init__.py
?? app/experiments/task_type_ground_truth/blind_label.py
?? app/experiments/task_type_ground_truth/dataset.py
?? app/experiments/task_type_ground_truth/evaluate.py
?? app/experiments/task_type_ground_truth/gold_labels.jsonl
?? app/experiments/task_type_ground_truth/gold_labels_llm.jsonl
?? app/experiments/task_type_ground_truth/schema.py
?? audits/2026-09-07_authority_boundary_deliberateness.md
?? audits/2026-09-07_consequence_authority_map.md
?? audits/2026-09-07_consequential_learning_loop_design.md
?? audits/2026-09-07_consequential_loop_validation.md
?? audits/2026-09-07_missing_primitive_determination.md
?? audits/2026-09-07_post_wake_observation.md
?? audits/2026-09-07_shadow_treatment_harness_archaeology.md
?? audits/2026-09-07_temporal_authority_graph.md
?? audits/2026-09-08_adversarial_epistemic_pressure.md
?? audits/2026-09-08_echo_blind_self_model.md
?? audits/2026-09-08_echo_self_model_claims.json
?? audits/2026-09-08_echo_self_model_discrepancy_report.md
?? audits/2026-09-08_echo_self_model_revision.md
?? audits/2026-09-08_epistemic_arbitration_FINAL.md
?? audits/2026-09-08_epistemic_arbitration_baseline.md
?? audits/2026-09-08_epistemic_arbitration_design.md
?? audits/2026-09-08_epistemic_arbitration_experiments.md
?? audits/2026-09-08_epistemic_arbitration_pipeline.md
?? audits/2026-09-08_epistemic_arbitration_validation.md
?? audits/2026-09-08_epistemic_boundary_imagination_experiment.md
?? audits/2026-09-08_epistemic_contamination_recovery_forensics.md
?? audits/2026-09-08_epistemic_interaction_and_relay_forensics.md
?? audits/2026-09-08_epistemic_transition_mechanism_forensics.md
?? audits/2026-09-08_evidence_arbitration_and_sensory_ingestion_forensics.md
?? audits/2026-09-08_exhaustive_sensor_contract_experiment.md
?? audits/2026-09-08_git_readonly_self_history_investigation.md
?? audits/2026-09-08_mechanism_c_FINAL.md
?? audits/2026-09-08_mechanism_c_experiments.md
?? audits/2026-09-08_mechanism_c_post_update_replication.md
?? audits/2026-09-08_mechanism_d_independent_regrounding.md
?? audits/2026-09-08_persistent_self_model_DESIGN.md
?? audits/2026-09-08_persistent_self_model_inventory.md
?? audits/2026-09-08_phase10_retest_after_revision.md
?? audits/2026-09-08_phase8_adversarial_testing.md
?? audits/2026-09-08_self_model_causal_design.md
?? audits/2026-09-08_self_model_contradiction_handling.md
?? audits/2026-09-08_self_model_correction_path.md
?? audits/2026-09-08_self_model_evidence_hierarchy.md
?? audits/2026-09-08_self_model_experiment_plan.md
?? audits/2026-09-08_self_transparency_audit_FINAL.md
?? audits/2026-09-08_self_transparency_audit_experimental_boundary.md
?? audits/2026-09-08_sensory_gate_fix_and_provenance_forensics.md
?? audits/2026-09-08_transparency_metrics_and_epistemic_boundary.md
?? audits/2026-09-08_verified_external_architecture.md
?? audits/2026-09-09_autonomous_investigation_liveness_recovery_forensics.md
?? audits/2026-09-09_autonomous_scheduler_restart_temporal_lifecycle_forensics.md
?? audits/2026-09-09_codex_headless_subscription_independence_proof.md
?? audits/2026-09-09_epistemic_transition_mechanism_forensics.md
?? audits/2026-09-09_four_agent_collaboration_architecture_audit.md
?? audits/2026-09-09_independent_review_epistemic_arbitration_findings.md
?? audits/2026-09-09_mission32_task_type_classifier_causal_audit.md
?? audits/2026-09-09_mission32_task_type_classifier_causal_audit_evidence_ledger.json
?? audits/2026-09-09_mission33_independent_ground_truth_audit.md
?? audits/2026-09-09_mission34_task_type_experiment_run.md
?? audits/2026-09-09_mission35_task_type_experiment_llm_judge_rerun.md
?? audits/2026-09-09_open_ended_learning_discovery.md
?? audits/2026-09-09_openai_codex_local_agent_architecture_investigation.md
?? audits/2026-09-09_os_level_stdin_fd0_implementation.md
?? audits/2026-09-10_epistemic_invocation_and_provenance_isolation.md
?? audits/2026-09-10_phase2_provenance_reconciliation.md
?? audits/2026-09-10_research_arc_provenance_audit.md
?? audits/2026-09-11_authority_evidence_separation_forensics.md
?? audits/2026-09-11_authority_free_ladder_causal_isolation.md
?? audits/2026-09-11_false_verification_trap_replication.md
?? audits/2026-09-11_feralecho_unresolved_defect_audit.md
?? audits/2026-09-11_provenance_implementation_boundary_audit.md
?? audits/2026-09-11_provenance_leaf_primitives_validation.md
?? audits/2026-09-11_read_only_git_provenance_design.md
?? audits/2026-09-11_read_only_provenance_interface_design.md
?? audits/2026-09-11_research_state_consolidation.md
?? audits/2026-09-11_three_layer_provenance_reconciliation.md
?? audits/2026-09-11_verification_and_level_7_5_8_feasibility.md
?? audits/2026-09-12_provenance_layer2_boundary_review.md
?? audits/2026-09-13_capability_benchmark_harness_phase0.md
?? audits/2026-09-13_council_correctness_investigation.md
?? audits/2026-09-13_cross_layer_reconciliation_boundary.md
?? audits/2026-09-13_layer3_runtime_provenance_boundary.md
?? audits/2026-09-13_observation_time_contract_research.md
?? audits/2026-09-13_observation_time_enforcement_research.md
?? audits/2026-09-13_observation_time_placement_architecture.md
?? audits/2026-09-13_provenance_layer2_red_team.md
?? audits/2026-09-13_reconciliation_epistemic_taxonomy_and_arbitration_scoping.md
?? audits/2026-09-13_reconciliation_implementation.md
?? audits/2026-09-13_reconciliation_implementation_design.md
?? audits/2026-09-13_reconciliation_primitive_architecture.md
?? audits/2026-09-13_shadow_model_retirement.md
?? audits/2026-09-13_shadow_retirement_documentation.md
?? audits/2026-09-13_tier5_council_correctness_retest.md
?? audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md
?? audits/2026-09-14_task_type_behavioral_experiment.md
?? audits/2026-09-14_task_type_downstream_behavior_archaeology.md
?? audits/2026-09-14_tier5_retest_adversarial_audit.md
?? audits/2026-09-15_codex_michelangelo_blind_spot_discovery.md
?? audits/2026-09-15_codex_task_type_independent_review.md
?? audits/2026-09-15_task_type_experiment_reconciliation.md
?? audits/2026-09-16_capability_growth_reconciliation.md
?? audits/2026-09-16_codex_capability_ceiling_adversarial_review.md
?? audits/2026-09-16_e5_mini_adversarial_preimplementation_review.md
?? audits/2026-09-16_feralecho_zero_cost_capability_ceiling.md
?? audits/tier3_apparatus/dev_sanity_results_REISOLATED_RERUN_20260909.jsonl
?? audits/tier3_apparatus/heldout_results_REISOLATED_RERUN_20260909.jsonl
?? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_progress.txt
?? audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_results.jsonl
?? audits/tier5_retest/tier5_retest_progress.txt
?? audits/tier5_retest/tier5_retest_results.jsonl
?? audits/tier5_retest/tier5_retest_task_pool.hash.txt
?? audits/tier5_retest/tier5_retest_task_pool_FROZEN.py
?? claude_relay/.last_seen_from_air_hub.json
?? claude_relay/facts_m5.jsonl
?? codex_relay/README.md
?? codex_relay/relay.py
?? codex_relay/test_relay.py
?? hub/README.md
?? hub/check_hub.py
?? hub/notes.jsonl
?? hub/notes.py
?? hub/status.jsonl
?? research/COLLABORATOR_SUBSTITUTION_CODEX_PILOT.md
?? research/FRONTIER_COLLABORATOR_REGULATORY_DEPENDENCY.md
?? research/MACOS_AUTHORIZATION_EVIDENCE_ARCHEOLOGY.md
?? research/MEMORY_PRESERVATION_ARCHAEOLOGY.md
?? research/MEMORY_PRESERVATION_SET_AUDIT.md
?? research/OPOSSUM_MODE_BRAINSTORM.md
?? research/STRATEGIC_FRONTIER_RESILIENCE.md
?? research/TWO_NODE_IDENTITY_PRESERVATION_RELAY_ARCHAEOLOGY.md
?? scripts/run_tier3_reisolated_rerun.py
?? scripts/run_tier5_retest.py
?? scripts/task_type_behavioral_experiment.py
?? scripts/task_type_behavioral_experiment_analyze.py
?? scripts/task_type_behavioral_experiment_judge.py
?? scripts/tier5_retest_task_pool.py
?? scripts/verify_select_best_fallback_candidate.py
```

Closing check: **2026-09-16 17:59:04 UTC**.

- Ending HEAD: **2fba42644c82b9f7096276f4dd338d615cf1bcce**, identical to opening HEAD.
- Ending `git --no-optional-locks status --short --untracked-files=all`: **179 entries**, 27 modified tracked and 152 untracked.
- Comparing every opening/closing status line found no removed or changed status entries; the only addition is below. The full ending status is therefore exactly the opening listing plus this entry in alphabetical position.
- All seven source/report fingerprints in §14 are unchanged, including both reports under review.

```text
?? audits/2026-09-16_e5_mini_final_adjudication.md
```

**Only repository path created or modified by this mission:** `audits/2026-09-16_e5_mini_final_adjudication.md`. No scratch artifact was created. No production code/configuration, existing report, model, RiverBrain/FAISS/memory, experiment state, hub/relay or Git state was written. No inference or experiment was run. No running process was started, restarted, stopped, signaled or attached to.

This is accounting for this mission's actions, supported by the status delta and sampled source fingerprints. It is not a claim that every ignored or already-dirty runtime file stayed byte-identical while other processes continued independently.

## Recommendation to Richie

Implement only the isolated **G0 recorder, information-path validator and qualification fixtures**, with the four-arm E5-mini adapter using mocked calls. Once G0 and execution isolation pass, run the frozen pilot with matched P/Z construction and the paired teaching-content check. No production integration or broader architecture work is justified by this adjudication.
