# Semantic competence, repair authority, and reliable retained learning

October 7, 2026. **Decision: REVISE.** Preserve VSL's storage, lifecycle and exact-edit machinery; revise the research design so that a retained edit proposes a repair and independent task evidence authorizes it. Proceed only to adversarial review of the bounded feasibility protocol below. No production integration or acquisition expansion is justified yet.

**The failure is an interaction among missing information, an overly concrete representation, an impoverished reuse interface, shallow binding/site analysis and absent task-correctness authorization in the production path.** Better name matching alone cannot fix it. A richer record alone cannot fix it either: identical code under opposite task contracts needs opposite decisions, and the current consultation API does not receive those contracts.

The smallest useful next experiment is **SAC-1: sixteen prospective mechanistic specimens, zero model calls, one bounded contract/binding/verifier implementation, no tuning after evaluation**. It tests engineered representation adequacy, not autonomous learning. Its [design protocol](semantic_authority_20261007/protocol.md) and [fixtures](semantic_authority_20261007/prospective_matrix_v1.json) are frozen; C's implementation and execution supplement remain explicit prerequisites. They were not built or run in this investigation.

## 1. Evidence and integrity boundary

[Opening state](semantic_authority_20261007/opening.json), 16:06:30 PDT: branch `vsl-implementation`; HEAD `e5acbb09cece8d1791fa6d967fe57067137a8cff`; cached origin/main `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`; ahead/behind 4/0 without fetch; staging empty. Fourteen pre-existing tracked modifications and all pre-existing untracked work were preserved. **462 historical/source authority paths** were pinned, including the preceding 290, the original 203 and the recognition experiment's raw outputs. Additional historical sources inspected later are separately timestamped and pinned in [supporting evidence](semantic_authority_20261007/supporting_evidence.json).

[Process observation during this review](semantic_authority_20261007/processes_during_review.txt): Echo PID 55361, started October 1 15:45:19; watchdog 56610, September 28 09:44:38; Ollama 1991, September 19 10:57:03. This is an observation during the investigation, not a fabricated process snapshot at the exact opening timestamp. Auxiliary Python identities are also preserved. No signals, restarts, relay messages or network calls to Echo were made.

Skill A remains the exact ACTIVE v4 record, SHA-256 `aa00c0aee4563f25254f624255605afb5448ebfb8a08c0b4833fb6796a098e7e`. Matcher SHA-256 `063cd1449f2035f4f273b423fa732130bcfec1d5740fda5895687fbeba30a8f7`. ACTIVE is the record's lifecycle state; it does not prove that every live path is currently running with active feature flags. Runtime remains gated by its existing environment switches. Skill B remains historical/experimental and was not promoted.

Methods: source tracing; raw-result recounts; hash/index comparison; pure AST extraction/application; primary technical documentation review; prospective fixture construction. **New local-model calls: 0. External experiment inference calls: 0. Candidate executions: 0.** AST parsing, transformation and fixture generation are not execution of candidate bodies. Web documentation lookup is research, not an experimental model call. No production module initialization or consultation/log-writing path was invoked.

FAISS, memory metadata, RiverBrain and self-model bytes were observed separately as mutable live state, excluded from experimental inputs. Hash changes alone do not identify their writer. The closing record and exact additive mutations are documented at the end.

## 2. Independent reconstruction of the failure

The prior [recognition report](2026-10-07_skill_a_semantic_recognition_boundary_qualification.md) was checked against its frozen matrix, per-specimen oracle records and the unchanged matcher. [New recount](semantic_authority_20261007/recognition_recount.json) reproduces **TP 4, FN 9, TN 5, FP 6**. For every emitted baseline patch, its AST equals the separately evaluated historical counterfactual. No new candidate run was needed.

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| 4/13 positive equivalents recognized; nine missed | Literal names, enclosing-call identity and absent definition/use tracing exclude verified equivalents | A natural-distribution recall estimate |
| 6/11 negative near-neighbors accepted | A local syntax match is inadequate repair authority | Six harmful repairs: only four harmed; two were irrelevant/wrong-site |
| n00–n03 each 36→12 correct | Rank encoding, sorting/selection direction and intended priority can invalidate the same sign edit | General utility over an independently selected workload |
| n04 36→36; n05 12→12 | First structural match can edit unused computation or miss the live defect | That every matched site matters to output |
| n06 2→14, residual mutation failures | Defect correction and complete-contract satisfaction are distinct | That sign removal introduced the original alias/mutation defect |
| Byte-identical p00/n03, opposite task contracts | Source plus current record is insufficient information to decide safely | That all semantic intent can be inferred by a stronger source-only model |
| SA-R1: 5/13 positives, 0/11 false accepts; challenge 2/4 positives, 0/5 false accepts | Added human-supplied contract/structural checks can improve bounded safety, while still missing equivalents | Autonomous acquisition of that knowledge, broad generalization or production readiness |

The natural RNU `winner_from_text` remains a diagnostic lead: local-copy `.sort()` was refused because the stored call context is `sorted`; its frozen sign edit improved 12→36/36. This establishes one repairable miss. It does not authorize an unconditional `.sort()` extension; the opposite-encoding `.sort()` near-neighbor would be harmed.

The October 7 [RNU trial](2026-10-07_retained_learning_net_utility_test.md) completed 44 paired tasks, 25 correct in each condition, zero matches/applications. Its primary result remains **INCONCLUSIVE**, with zero observed net correctness advantage in that cohort. It is neither a positive learning result nor proof that all possible retained reuse has zero value. Nothing in this audit reuses that exam as a development benchmark.

## 3. Causes, with evidence strength

| Candidate cause | Finding | Evidence strength / remaining uncertainty |
|---|---|---|
| Information retained at acquisition | Selected failing/passing code and external correctness feedback yield an AST difference. The operational skill does not retain a checked task relation, ownership assumptions, rank orientation or validated counterexample boundary. | **Observed** in record/extractor. Whether a local model could infer these fields from richer permitted experience is **untested**. |
| Representation | `-tag_priority[x[2]] → tag_priority[x[2]]`, node type and nearest call name bind historical syntax. The schema's provenance dictionary can hold more data, but the consumer does not interpret semantic authority from it. | **Observed**; this is a limitation of the current concrete encoding, not a theorem against all precondition/transformation representations. |
| Task-to-recognizer interface | `consult(code, fn_name, feature_keys=None)` has no task-contract parameter. `consult_file(code, task_id)` uses a task identifier for logging, not as an interpreted requirement. | **Observed**, plus source-identical opposite-contract evidence makes missing intent a decisive information limitation. |
| Bindings/dataflow | Matcher compares concrete AST dumps, checks a textual enclosing-call name and replaces the first match. No sufficient alias, builtin-binding, reaching-definition, result-liveness or ownership proof is performed. | **Observed** source mechanism and isolated positive/negative specimens. Full Python analysis is not shown necessary for this bounded domain. |
| Independent verification | Production `echo_projects` invokes VSL before F1/F2 and records `f1_f2_safety_only`. It does not independently compare original/repaired task correctness before accepting the VSL proposal. Research E0.1 exists, but executing a supplied oracle is not the same as possessing a trustworthy oracle for each production task. | **Observed** integration gap. E0.1 is not absent; task specification/oracle availability and wiring are separate gaps. |
| Interaction | Broader syntax coverage without intent and verification exposes more harmful matches; verification without a live-site proposal cannot recover missed opportunities; complete refusal can look safe without delivering utility. | **Strongly supported** by the combined evidence. The benefit of a new combined architecture remains prospective. |

Sources: [matcher](../app/core/skill_ledger/matcher.py), [runtime](../app/core/skill_ledger/runtime.py), [consumer](../app/core/skill_ledger/echo_adapter.py), [schemas](../app/core/skill_ledger/schemas.py), [production project path](../app/core/echo_projects.py), [acquisition harness](../app/experiments/skill_ledger/harness.py). Load-bearing locations are matcher `extract_transformation`/`apply_skill`, runtime `consult`/`record_outcome`, adapter `record_final_verdict`, and project lines 284–329.

**Principal diagnosis:** reuse lacks a trustworthy mapping from current task intent and live implementation mechanism to the retained edit's authority. Several pieces are missing. Calling this only a “representation problem” obscures the interface and verifier failures; calling it only a “matcher bug” ignores missing information that no matcher can recover from code alone.

## 4. Architectural comparison

All benefits below are hypotheses constrained by the repository evidence, not measurements of implementations built during this audit. None alone supplies the full learning cycle.

| Approach | Safety / harmful-transfer risk | Coverage and generalization | Acquisition implications | Verification needed |
|---|---|---|---|---|
| **A. Explicit semantic skill contracts** | Makes intended relation, domain, bindings, counterexamples and abstention explicit; wrong contracts can confidently authorize harm | Can express invariance beyond names/calls; expressing a condition does not implement its recognition | Inert fields can be proposed from task specs, failed/passing pairs and feedback. No qualified extractor currently does this. Hand-authored contracts are Capability 1 only | Independent field provenance, consistency checks, held-out counterexamples and actual repair checks |
| **B. Counterexample-guided boundary learning** | Can reject repeated classes of bad reuse; noisy feedback can poison or over-restrict the library | Potentially learns discriminating relations rather than accumulating exception strings; unseen combinations remain a risk | Direct route from experience to applicability updates, but requires an expressible hypothesis space and trustworthy feedback | Fresh harmful and legitimate positive cases, comparison with no-counterexample control, retained-state ablation and restart replay |
| **C. Contract/property verification** | Strongest immediate barrier to harmful accepted edits when tests express the actual task; incomplete or circular oracles still permit harm | Can validate structurally diverse proposals without recognizing every syntax first; cannot propose a missing binding by itself | It can supervise acquisition; it is not an acquisition algorithm | Independent task intent; separate decision and hidden scoring cases; ownership/side-effect observations; mutation controls for the oracle |
| **D. Binding-aware semantic matching** | Resolves alpha names, helpers, aliases and live sites; unsound alias or builtin assumptions can broaden unsafe authority | Good within a declared Python subset; general dynamic dispatch/reflection needs abstention or different machinery | Improves the engine's representation processing; not learned competence unless the acquired record supplies information the generic engine lacks | Binding/alias/liveness adversaries plus behavioral checks; unsupported code must not be treated as proven |
| **E. Retrieval, reasoning and verification** | Separates remembered suggestions from authority; reasoning can still invent intent or plausible but wrong bindings | Potentially broad proposal coverage; final coverage bounded by verifier and task information | Could propose contracts and revisions from experience. No evidence yet that Echo can do this reliably | Validate structured proposals; independent verifier outside model control; capable no-memory baseline; never accept prose as proof |

| Approach | Expected cost/latency | Engineering complexity | Current VSL compatibility | External dependence | Evidence before deployment |
|---|---|---|---|---|---|
| A | Small records, deterministic checks; cheap relative to inference | Medium schema/interface work, high if task intent must be invented | Add versioned contract/evidence references; leave old records readable and explicitly limited | None required | Capability 1, then independent acquisition and transfer; exact contract/engine version association |
| B | Storage plus counterexample replay; bounded proposals and verifier calls | Medium/high; labeling, deduplication and region-specific revision are missing | Append evidence and new candidate versions; existing whole-skill degradation is insufficient | None required | Unseen decisions improve after feedback without losing prior positives; survive fresh-process reload |
| C | Many small isolated executions; symbolic checking may time out or grow sharply | Low/medium for this finite domain; high for arbitrary code | Gate a disposable proposal before acceptance; verifier stays separate from ledger | None required | False-oracle/missing-contract controls and hidden outcomes, including side effects |
| D | Usually modest CPU cost on small ASTs; unrestricted Python analysis is not bounded | Medium for limited local dataflow, high for general Python | Replace literal binding assumptions only in research first; retain exact patch application | None required | Equivalent helper/alias/site cases pass and shadowed/mutating near-neighbors refuse |
| E | Adds local inference latency and context; wasteful if used on every deterministic case | Medium orchestration, high reliability burden | Treat ledger as proposal/evidence store; bounded optional local proposer | Must use local or deterministic fallback; relays never required | Same-model ablation, exact budgets and cost accounting; any unverified proposal abstains |

**Ranked practical choice:** (1) A + C + a small D, organized as E's proposal/verification separation but initially without LLM reasoning; (2) counterexample-guided updates B, only after the representation and oracle work; (3) bounded local-model reasoning to extend proposals if measured missed bindings justify its cost. A general Python IR, unconstrained synthesis loop or full architectural replacement ranks below these because no current evidence requires it.

Counterexample-guided synthesis offers a useful separation of specification, search and verification, but its counterexamples only enforce the specification actually supplied; it does not recover omitted intent. That distinction supports a bounded proposal/rejection cycle rather than unbounded repair retries. [MIT synthesis lecture](https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture17.htm).

Property-based testing can generate cases and action sequences from supplied operations/properties, which is useful for aliasing and mutation observations. It does not independently discover the correct task contract. [Hypothesis stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html). Metamorphic checks such as permutation invariance, score translation and consistent tag renaming should supplement a direction-sensitive oracle: both a correct and a reversed winner rule can satisfy those invariances.

Bounded symbolic checks are an optional later tool, not the initial dependency. CrossHair explicitly warns that failing to find a counterexample is not a correctness guarantee, and documents limitations including identity and nondeterminism. It also executes user code, so its use would need qualified isolation. [CrossHair limitations](https://crosshair.readthedocs.io/en/latest/limitations.html). No package was installed and no solver result is claimed.

## 5. Recommended representation and authority flow

Retain the ledger as the durable, versioned evidence/lifecycle layer. Add a **research-only semantic repair record**, rather than treating a larger list of syntactic match patterns as the learned concept.

| Component | Contents | Authority source |
|---|---|---|
| Current task contract | Intended ordering, types, result, ownership and unsupported/unknown fields | Current task requirements; never inferred solely from the old repair |
| Retained repair relation | What defect relationship was observed; operand roles; proposed change; supported domain; required pre/postconditions | Acquisition evidence and independent qualification, field by field |
| Binding proposal | Actual definitions/uses, map orientation, live ranking result, exact edit location, alias/ownership assumptions | Analysis or local model proposal, then checking; proposal is not proof |
| Counterexample evidence | Original/program/contract hashes, proposed edit, observed harm, independent oracle/version, applicability region | Durable external feedback; not self-reported success |
| Per-application authorization | Exact source + task contract + skill/version + bound edit + verifier/domain/budget hashes, outcome and reasons | Independent original/repaired comparison; invalidated when any bound input changes |

The relation for this bounded skill is not “delete a minus under `sorted`.” It is that a rank contribution must implement the external tie preference after accounting for the sort direction and selected extremum. Removing a negation is one supported repair when the map and consuming operation make that removal correct. Target-site bindings and preservation obligations belong with that relation. A future task's priority order is new task information, not something past learning should pretend to know.

Proposed flow:

```text
task contract + candidate
  → retrieve a retained repair hypothesis
  → resolve/check bindings, liveness and ownership
  → establish an independently observable defect
  → apply one unchanged/bound edit to a disposable copy
  → compare original and repaired against independent requirements
  → accept that exact artifact, or retain original with an explicit reason
  → append version-specific evidence; propose any later revision separately
```

Reasoning, if later needed, returns structured hypotheses, not executable verifier code or authority. The verifier's expected values and hidden tests stay outside candidate/model control. A missing task requirement remains UNKNOWN. If two plausible task contracts authorize opposite edits, no amount of confidence in one explanation supplies the missing requirement.

**Is there a fundamentally better way?** Yes, a task-conditioned, evidence-bearing repair hypothesis with independently checked application authority addresses concrete omissions in today's record/API. But the abstract idea of a precondition and transformation is not intrinsically defective: semantic preconditions, bound transformations and postconditions can still use that abstraction. The required revision is what they encode and how authority is granted, not discarding VSL persistence or renaming patterns “concepts.”

## 6. Engineered competence versus acquired competence

| Capability | Current evidence | Qualification still needed |
|---|---|---|
| **1. Representation adequacy** | SA-R1 supplies a small engineered proof of feasibility, with limited grammar/recall. Richer proposed fields have not been executed. | Fresh contract-conflict, binding, helper, alias and live-site qualification; useful coverage with zero harmful acceptance in the bounded set |
| **2. Autonomous acquisition** | Echo's historical pathway acquired an AST edit from externally evaluated candidate pairs. It did not acquire the semantic authority proposed here. No inspected path emits and qualifies those fields autonomously. | Produce fields from permitted experience without investigator answers; compare with identical base model lacking that experience; retain per-field derivation and uncertainty |
| **3. Beneficial transfer** | Narrow historical causal transfer exists; October 7 natural RNU produced no applications. | Same capable model and architecture, with/without the *acquired* record, on genuinely new independently selected work; include harm and costs |

Autonomous semantic acquisition is **plausible but unproven**, and often underdetermined from a single failed/passing pair. A correct result does not uniquely identify the condition that made a patch safe. Needed evidence includes varied task encodings, failures of apparently similar repairs, ownership requirements and independent held-out checks. A task-spec parser can supply intent without learning; a human-written relation interpreter can supply engineered competence. Neither should be credited to Echo's experience.

The repository's related acquisition studies are warnings, not a direct answer. [Raw phase 4](../memory/experiments/counterfactual_acquisition/20260929_phase4_learner_ab/results/phase4_result.json) has 1/5 successes with a prior library versus 0/5 without, mean held-out accuracies 0.60/0.5417 in a small XOR task. [Raw contradiction revision](../memory/experiments/counterfactual_acquisition/20260929_phase5_revision_after_contradiction/results/phase5_result.json) contains **12/12 invalid-arity revision attempts** after round zero. The recount is in supporting evidence. These do not test Python semantic contracts, do not establish a robust acquisition advantage, and do not prove such acquisition impossible. Earlier PA-1 stopped before its proposed learner rather than demonstrating that learner failed.

## 7. The frozen falsification design

| Artifact | SHA-256 |
|---|---|
| [SAC-1 protocol](semantic_authority_20261007/protocol.md) | `be6637d7bb0bd2c491fce6797d50e219baeea4a9e7cfd2c86442490a0d8a09b4` |
| [Design/source manifest](semantic_authority_20261007/design_manifest.json) | `e888431145631c36381ec3993dbd600e0cc33843914002100eff416e99b0476e` |

The manifest pins the [deterministic fixture builder](semantic_authority_20261007/design_fixtures.py), sixteen exact source bodies/contracts and their 24 decision + 24 hidden cases, the original Skill A and evaluator dependencies. The builder was run only to construct text/data and parse syntax; **no fresh program, matcher or oracle execution was performed**. Ground-truth eligibility labels remain prospective until independent isolated checks establish them. A preserved earlier draft contains a statically discovered wrong-site witness; it is explicitly excluded. No observed outcome informed that pre-freeze correction.

The matrix includes two cases per requested dimension: alpha-renaming, helper/expression extraction, equivalent sorting implementations, identical source/opposite contracts, harmful or irrelevant near-neighbors, alias/mutation traps, multiple repair sites, and insufficient task information. It contains nine proposed safe-repair cases, five complete-authority negatives and two mandatory unknown/abstain cases. Directional defect and complete safe repair remain separate labels.

Fresh means not used in prior recognizer development; it does not mean statistically independent of the known failure categories. Future C must not be tuned against these fixtures. The design allows historical specimens for implementation work, followed by a code freeze and this one qualification. Any training/holdout contamination stops the pass. It does not rerun the natural RNU workload.

**Stage-1 arms:** A0 is the proposed deterministic pipeline with an empty repair store; B is the exact Skill A/matcher; C is an investigator-contract pipeline. A0 preserves the common tools but is only a fixed-program engineered-state ablation, **not the same capable model solving tasks without memory**. D is explicitly unavailable until an acquisition mechanism exists; no fabricated D result. Later learned-transfer A/D must share a capable local model, task contracts, tools, prompts/policy, call and candidate budgets. A must be allowed native repair attempts. C beating B would measure an engineered package, not autonomous learning.

Acceptance is demanding enough to reject a refusal-only solution: C must repair at least 7/9 qualified positives, with successes across alpha, helper, sorting and multiple-site groups; accept zero harmful/irrelevant/partial negative edits; abstain on both missing-information cases; improve complete task correctness over B and A0 with no per-input regressions. One harmful accepted edit stops execution. These are screening thresholds, not a population safety probability.

Raw metrics include proposal versus accepted repair, correct tasks, fixes, harm, irrelevant edits, missed opportunities, correct/incorrect abstentions and cost. Hidden tests score; they never choose the edit. Report the raw vector and net correctness first, plus optional harm-cost sensitivity at weights 1 and 10 without letting a weighted score override zero-harm acceptance. No significance test on sixteen designed related specimens.

The design is frozen; the **executable experiment is not yet qualified**. Missing prerequisites are C/A0 source and inert contract hashes, observer/driver, room/profile path instantiation, launch allowlist, result schema and the existing boundary's preflight. These must be pinned in an execution supplement without changing cases, budgets or criteria. If that cannot be done within a small bounded implementation, return for review. This report does not disguise an absent implementation as a reproducible completed experiment.

## 8. Can reuse failures improve later applicability?

| Cycle step | Repository status | Missing qualification |
|---|---|---|
| Acquire | Model candidates + external grading + AST difference extraction exist | Semantic relation and applicability-region acquisition |
| Verify | Historical independent task tests; E0.1 research execution; production safety checks | Complete contract coverage and independent oracle availability at reuse |
| Retain | Versioned immutable skill records and lifecycle; restart evidence | Semantic-schema/interpreter compatibility and field-level provenance |
| Retrieve | ACTIVE skill enumeration, exact matching, deterministic first match | Task-conditioned retrieval, conflict evidence, bindings beyond historical form |
| Check applicability | AST/context match; research behavioral/structural probes | Qualified combination of current intent, defect, bindings and complete authority |
| Apply/abstain | Existing exact transformation; no-match refusal | Distinguish missing intent, unresolved binding, unsafe proposal and valid refusal |
| Verify outcome | Outcome logging with verifier-strength labels | Production task-correctness comparison, not merely F1/F2 |
| Update evidence | Append application outcomes; explicit whole-skill degradation | Learn a narrower/wider justified applicability boundary and prove future improvement |

`evaluate_degradation()` filters for full-oracle outcomes and requires an explicit invocation. It is not an online applicability learner. Source review also finds that it aggregates by feature key while applying degradation to the latest version, despite individual logs containing skill versions. Best-effort logging may silently fail. These are **code-level integrity risks**, not newly observed production failures; no degradation path was invoked. A future learner must not treat mixed-version or lost evidence as a clean training stream.

A bounded future update experiment should retain a trusted counterexample as `(program, task contract, proposed binding/edit, original outcome, repaired outcome, verifier identity/domain, exact skill/version)`, then produce one proposed new candidate record. Use one held-out erroneous-class transfer and one legitimate positive transfer before and after the update, in fresh processes, with an equal-budget no-counterexample control. Same-example replay is insufficient. A blanket disable that prevents harm but suppresses the positive fails. New revisions remain research candidates, never automatic production promotion.

Avoid poisoning by accepting learning labels only from independently validated task feedback; distinguish infrastructure error, oracle uncertainty, unrelated defect and actual harmful transfer. Preserve contradictory feedback rather than resolving it by majority vote. Deduplicate by artifact/application identity and version; keep old versions and verifier hashes. Bound updates and library size, retain a representative positive/negative regression set, and record information lost by any compaction. Hash-based deduplication alone does not prove two examples semantically redundant. If feedback or intent is missing, abstain from boundary learning as well as from repair.

This cycle is feasible to investigate in a restricted domain. No evidence here establishes that it currently improves future decisions or survives restart as an improved learned policy. No autonomous self-modification loop was implemented.

## 9. Separate provenance integrity finding

The [census](semantic_authority_20261007/provenance_census.json) covers **all 12 records found under `memory/**/skills/*.json`**, spanning three feature keys. Disposable research copies elsewhere are outside that census; it is not a claim to have checked every possible artifact on the machine.

| Family | Records | Selected failing/passing indices | Hash defect |
|---|---:|---|---|
| Skill A (`K2.T5`) | 9 versions/copies: five experimental, four production | 1 / 3 | Failing hash refers to candidate 0 in all nine; passing hash matches |
| Skill B (`K2.T2`) | 1 experimental | 6 / 1 from stored source cohorts | Both hashes match selected raw bodies |
| PIT2 (`K2.T3`) | 2 historical versions | 3 / 1 | Failing hash refers to candidate 0 in both; passing hash matches |

**Origin directly established:** the original acquisition loop selects `used_pair` from the first extractable failed/passed pair, then writes hashes of `failing[0]`/`passing[0]`. Index and hash therefore need not describe the same body. This is present in committed harness `19e8135`; the later re-extraction path preserves the same error. The untracked PIT2 acquisition source repeats that pattern. This establishes the mechanism in both code paths; it does not establish who copied it or why. Skill B's accumulation code retains the actual selected pair and hashes that pair correctly.

Exact Skill A failing hash: stored `e8679b511a3b77aa40a31f99d297abc20af53fade989886ce5c59990d690abb2`; selected candidate 1 `23f9e58ddf2ace5fbbb535d31f38ce1d13738f185edfb901f502d3fd3182ef3d`. PIT2 selected candidate 3 is `e32e63e69bcdd81b66d23b887a4f15388939ee059913dc3bc3e15ecb20470129`, while the stored hash is `f7345ba6e008958ae12e03b2a7867f5232fe1e15da6189f982b5041e4649360d`. All exact record, pool and selected hashes are in the census.

**Independent reconstruction:** using Echo's Python 3.12.13, each selected pair reproduces its record's precondition/transformation. [Interpreter follow-up](semantic_authority_20261007/interpreter_followup_3.12.json). This comparison concerns edit fields; it does not erase historical differences in enclosing-call metadata between versions. The initial pure-AST census ran under system Python 3.13.5 and reported false edit equality for B/PIT2 because empty AST fields serialize differently; [preserved 3.13 result](semantic_authority_20261007/interpreter_followup_3.13.json). This investigator-side interpreter confound is disclosed rather than rewritten away. Python documents AST/version changes and the `show_empty` option added in 3.13. [Python AST documentation](https://docs.python.org/3.13/library/ast.html#ast.dump).

Implications: acquisition provenance is inconsistent and cannot be verified from the index/hash fields alone. Raw pairs repair the *investigator's reconstruction*, not the historical bytes. Later exact-body causal comparisons and this recognition experiment do not become false simply because those metadata fields disagree. The prospective contamination filter independently hashes all raw acquisition bodies, so this particular mismatched field did not omit candidate 1 from that filter. PIT2's failed held-out qualification remains a failure. No acquisition-history rewrite, skill promotion or repair occurred.

Smallest correction, in a separate integrity change: persist the selected pair object once and derive both index and hash from it; assert lookup equality before saving. Add an append-only correction record linking each immutable historical record hash to corrected selected-body hashes and source-pool hashes. Independently re-extract with the pinned Python/matcher and verify all affected versions, then test a selection where the first failing candidate is not extractable. Do not silently mutate ACTIVE A or pretend a new metadata version passed a new capability trial. Pin an explicit AST/schema/interpreter format or qualify migration separately; no general Python-version portability is established here.

## 10. Roadmap with decision gates

| Stage | Prerequisites and smallest action | Acceptance | Failure / stop | Resources |
|---|---|---|---|---|
| **1. Feasibility** | Review SAC-1; one inert human contract and bounded proposer/authorizer; retain existing isolation | Frozen 7/9 coverage, all four positive groups, zero harmful/irrelevant acceptances, both unknown abstentions, correctness advantage over B/A0 | First harmful accepted edit, unqualified oracle/labels, material design change, or implementation becoming a general analyzer | Zero inference; ≤4,032 substantive child evaluations +32 preflight; 30-minute execution cap |
| **2. Acquisition** | Stage 1 passes; fixed inert schema and parser; permitted task specs, independently graded pairs/counterexamples; no hidden answers | Proposed future screen: ≥3/4 fresh acquisition episodes yield fully traceable valid contracts, no unsafe accepted use; same model without experience must not explain the apparent gain | Invalid/circular fields, no advantage attributable to experience, or manual answer substitution | Separate freeze; suggested maximum two local proposals per episode and matched no-experience controls: 16 calls total, serial, no retries beyond budget |
| **3. Transfer** | Freeze acquired records and engine before new task selection; capable A/D matched comparison | Positive task-level effect on new cases, explicit harms/costs; both successful and harmful-neighbor coverage; no post-outcome tuning | Harm boundary fails, no useful transfer or benefit explained by unequal scaffolding; stop expansion | Small paired cohort, budget frozen from actual Stage-2 latency; optional reasoner only if demonstrated necessary |
| **4. Persistence** | Frozen Stage-3 records, engine/schema and traceable evidence | Fresh isolated process reload reproduces decisions/outcomes and provenance; no-state substitution removes the acquired benefit | Behavior survives only via cache/prompts or hidden machine state; missing authority/evidence | Deterministic replay where possible; no live Echo restart; no claim of machine-disaster recovery from process reload alone |
| **5. Net utility** | Above passes and independently selected natural workload, never used for development | Retained-versus-capable-no-retained causal advantage with raw benefit/harm/cost vector and justified uncertainty | No effect, harmful transfer, invalid selection or cost that defeats usefulness; do not expand skill library to rescue result | Freeze task sample and inference/candidate budgets separately; no hardware purchase implied |

Earliest rational stop is **Stage 1**: if safe authority cannot be expressed/checked at useful coverage even with a supplied contract, do not invest in learning that representation. Passing Stage 1 is permission to ask about acquisition, not to claim it. A Stage-2 failure may justify one clearly localized interface/parser qualification; it does not justify indefinite new experiments until something passes. Stage-3 zero or negative retained benefit should stop accumulation investment even if contracts serialize perfectly.

## 11. Resource and engineering estimates

Existing CER-1 evidence identifies an M5/24 GiB system with real compression, swapping and model-eviction pressure. It does **not** show that more hardware would supply missing task intent, a sound oracle or a learned authority representation. No new resource benchmark was needed for this decision.

Stage 1 uses small ASTs, inert records and serial short-lived Python children. Planning estimate: less than 1 GiB additional working memory, minutes rather than hours of actual candidate work under healthy execution; neither figure has been measured for the unbuilt C. The protocol caps execution at 30 minutes. Expected engineering effort is roughly **1–3 focused working days** for a bounded prototype, logging and qualification; this is an uncertain planning range, not a measured cost or authorization for a larger implementation. If it expands toward general interprocedural Python analysis, stop and revisit the design.

For later local proposals, the October 7 RNU's 44 qwen2.5-coder 7B generations took 527.994 seconds total, about 12 seconds per call in that specific run. Contract extraction can have different context/output demands; use approximately **10–60 seconds per call only as a planning range**, not a benchmark. Sixteen serial calls would therefore suggest roughly 3–16 minutes of generation, excluding loading and verification. Keep existing model/context limits unless a separate failure justifies changing them. Do not assume a second resident model fits or that a longer context has zero cost.

Binding checks and verification should precede optional expensive reasoning where they can settle the issue. Cache by complete source/contract/skill/verifier hashes only; cross-version cache reuse without those keys can contaminate evidence. No GPU work, model download, cloud service, relay, subscription or new hardware is required for Stage 1. Energy use was not measured; zero-inference qualification is qualitatively cheaper than repeated model search, not a quantified energy saving.

**Spend $0.** The immediate scarce resources are trustworthy task feedback and engineering/research attention. Stronger local inference could broaden proposals, but is not demonstrated to acquire safe semantic authority or positive retained utility. The system must remain correct by abstention/deterministic verification when every external agent is unavailable.

## 12. Closing integrity and reproducibility

[Closing record](semantic_authority_20261007/closing.json) verifies **all 462 opening authority hashes unchanged**, all five additionally pinned sources unchanged and all frozen protocol/design/engine hashes unchanged. HEAD, branch, cached origin and staging are preserved; staging is empty and the same fourteen tracked paths remain modified. [Closing process identities](semantic_authority_20261007/closing_processes.txt) match the observation during review, including Echo, watchdog and Ollama start times.

The five prospectively separated live mutable paths changed: `memory/faiss.index`, `memory/memory_meta.json`, `memory/river_brain.pkl`, `memory/self_model.json`, and `sandbox/scripts/temp_self_edit.py`. Opening/closing hashes, sizes and mtimes are retained. This does not establish who wrote them. This mission did not write them and never used their evolving contents to choose or score a specimen.

[Design validation](semantic_authority_20261007/design_validation.json) reproduces the frozen fixture data exactly, checks 9/5/2 provisional eligibility counts, verifies the identical-source/opposite-contract pair, finds no decision/hidden input overlap and no exact source duplicates among the 44 historical RNU bodies. These are text/data integrity checks, **not semantic qualification or experimental outcomes**. Known recipe families are disclosed; byte novelty alone does not prove generalization.

Every intentional filesystem mutation is additive within `audits/semantic_authority_20261007/` plus this new report. The namespace contains reconstruction scripts/results, the preserved interpreter-confounded census and its correction, prospective fixture drafts/final freeze, protocol/manifests, and integrity records. No Skill A/B, production matcher/consumer/schema, historical evidence or unrelated user file was changed. No models or candidates were executed; no services restarted; nothing staged, committed or pushed. The evidence manifest hashes the final audit bundle for review.

## 13. Explicit answers and handoff

**Q1 — Local defect, representation limitation, or both?** Both, plus an interface/verification limitation. Literal names and call context are local recognition restrictions; missing intent/binding/ownership authority is deeper. Current acquisition does not preserve the needed semantic boundary. These findings do not prove all precondition/transformation models fundamentally inadequate.

**Q2 — Most promising practical improvement?** A retained repair hypothesis with explicit task-conditioned requirements, bounded binding/liveness/ownership checking, and independent disposable original/repaired verification. Start deterministically; let an optional local model propose only when needed. Do not grant authority from explanation or syntax alone.

**Q3 — Can Echo learn semantic preconditions itself?** Possibly in a restricted expressible domain, but it has not demonstrated this. Missing pieces include sufficient task/counterexample evidence, a structured contract acquisition interface, trustworthy per-field feedback, version-specific boundary updates and unseen transfer controls. C's human contract cannot stand in for D.

**Q4 — Would contract-aware retrieval/verification outperform direct matching?** Prior SA-R1 supports bounded engineered safety improvement, not general superiority. SAC-1 can falsify the proposed broader package. A later matched capable-model A/D comparison with an acquired-record ablation must establish learned causal benefit; B/C alone cannot.

**Q5 — Is VSL the right foundation?** Retain its versioned ledger, lifecycle and exact execution layer. Revise its authority interface and add independently checked semantic/evidence records in research. The evidence does not justify discarding the storage foundation or treating its current matcher as sufficient policy.

**Q6 — Smallest cheapest next experiment?** Review then implement the one bounded SAC-1 contract/binding/verifier prototype and execute its frozen sixteen-case qualification with zero inference, zero production changes and a stop at the first unsafe acceptance. Resolve the separate provenance correction before making new acquisition claims. Do not rerun the 44-task RNU exam.

**Q7 — What would still be missing after success?** Autonomous acquisition; capable-model no-experience controls; broader independent transfer; actual retained net utility including cost; restart/schema continuity; resistance to false feedback and interference; and a positive learning curve as experience accumulates. Engineered coverage and safety alone establish none of those.

**Recommendation: REVISE the authority design, retain the ledger, and submit SAC-1 for adversarial review.** This investigation stops before new recognizer implementation, candidate evaluation, model inference, production integration or skill acquisition.
