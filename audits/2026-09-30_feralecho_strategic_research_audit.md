# FeralEcho strategic research audit

Date: 2026-09-30. Investigator: Codex. Analysis only; no model calls, new experimental trials, production changes, repairs, or Git mutations.

## 1. Executive assessment

**FeralEcho is a functioning local agent scaffold with persistent memory, online statistical adaptation, guarded automation, and a research prototype that has extracted and reused narrow code repairs from machine-generated experience. It is not yet a demonstrated continually improving agent.** Neither “nothing has learned” nor “persistent accumulated competence has been established” fits the evidence.

The strongest positive learning result is the Verified Skill Ledger's experience-derived executable repair, not a conversational claim, a growing log, or the Boolean learner's latest output. A generic investigator-written extractor obtained a transformation from failed/passing local-model candidates; the retained transformation subsequently corrected selected related programs, including after process boundaries. The strongest qualification is equally concrete: a stored repair also damages a correct program, its tested coverage is small and selected, and the purported accumulation result does not establish that learning A improved learning B.

**The current balance of research effort is wrong.** The project has spent enough time establishing that its local model can mishandle simple relational evidence and that surrounding representations matter. More variations of that demonstration are unlikely to decide whether FeralEcho is useful or developing. The decision-changing questions are now: can retained changes be recovered and withdrawn reliably; can the system tell when a change helps rather than harms; and does the resulting system outperform a competent simpler baseline on an unselected, useful workload at comparable cost?

My three immediate priorities are:

1. Establish a verified recovery boundary for the state the project claims to retain.
2. Resolve the known mismatch between a skill being labelled ACTIVE/qualified and its having permission to alter a particular program correctly.
3. Measure the net useful contribution of current architecture and retained state against strong simpler controls, including regressions, non-matches, timeouts, and cost.

These are research and qualification recommendations, not authorization to change anything. Keep autonomous-acquisition and accumulation work conditional on those results. Stop the current serial Boolean-explanation search; preserve its findings and reusable controls. Keep AP-0 as a component substrate. Do not expand VSL or build another learning architecture merely because the present apparatus can generate more experiments.

## 2. Scope, method, and repository provenance

**DIRECT EVIDENCE** means source, raw structured records, or deterministic recomputation inspected in this audit. **STRONG INFERENCE** means a conclusion supported by those observations but not itself experimentally measured. **SPECULATION** means a proposed possibility. A historical report's result is labelled as reported when I did not independently regrade its underlying executions.

The inventory found 34 experiment namespaces and initially 393 Markdown audit files; a BA-3 report appeared during this review, bringing the latter to 394 before this report. I inventoried these collections, read architecture and consequential code first, then used reports to locate raw evidence and disagreements. This is a broad, selective strategic audit, **not a claim to have read every line of every report or independently rerun every historical qualification**. No historical candidate program or production module was imported/executed. Read-only checks used standard-library JSON/text/hash processing and a two-entry arithmetic witness.

Opening baseline, recorded before analysis:

| Item | Observation |
|---|---|
| Time | 2026-09-30 12:00:46.837516 PDT, America/Los_Angeles |
| Branch | `vsl-implementation` |
| HEAD | `e5acbb09cece8d1791fa6d967fe57067137a8cff` |
| Cached `origin/main` | `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0` |
| Relative to cached remote | 4 ahead, 0 behind; no fetch or remote mutation performed |
| Staged changes | None |
| Live Echo | PID 71538, parent/watchdog 56610, start September 28 19:15:54 PDT |
| Ollama | PID 1991; existing process, not invoked for inference |
| Evidence protection | In-session SHA-256 baseline of 739 existing audit/experiment/skill-ledger source and structured files, plus hashes of the 11 pre-existing tracked dirty files |

Pre-existing tracked modifications were `CLAUDE.md`, `PENDING_DECISIONS.md`, `app/core/self_edit_convergence.json`, `app/core/self_edit_generated.py`, `app/core/temporal_environment.py`, both `claude_relay/.last_seen_from_air*.json` files, `claude_relay/from_m5.md`, `logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`, and `staging/self_edit_candidate.py`. There were numerous untracked audits and experiment namespaces, including the Boolean diagnostics, BA/PA work, and prospective invariance tests. None was assumed to belong to this mission. BA-3 is concurrent work, not my implementation or independently completed qualification.

The report's final integrity note records the closing comparison. A running server may legitimately write its own state; a before/after hash comparison is not proof that no other actor wrote anything during the interval.

## 3. Architecture reconstructed from current source

| System | What the code actually provides | What it does not establish |
|---|---|---|
| Local inference and council | `run.py`, `echo_model_orchestrator.py`, `river_deliberation.py`: local models, task routing, candidate generation, synthesis, agreement/fallback paths | That council overhead improves correctness or that a named synthesis model authored every delivered artifact |
| Memory | `memory_bridge.py`, `app/lib/vector_memory.py`: embedding retrieval, metadata, persisted conversation/experience material | Retrieval relevance, causal use, or competence improvement merely from corpus growth |
| RiverBrain | Online classifier/scaler updates; per-model/task rolling means consumed by ranking; persistence | A clean estimate of model competence: automatic quality, council ratings and sandbox outcomes have different meanings |
| Task classifier | Online task classification, heuristic/training labels, routing inputs | Independently calibrated task truth or improved downstream task correctness |
| Behavioral directives and self-model claims | Explicit durable directives; verified claim/correction records rendered into prompts | Autonomous acquisition of those directives, reliable compliance, introspective access, or calibrated self-prediction |
| World model/drift | `predictive_loop.py`: Bayesian updates over lexicon-derived news sentiment/topic counts, history replay, surprise events; telemetry/drift consumers | An open-ended causal world model or proof that its surprises predict useful interventions |
| Autonomous operation | Schedulers, reflection, curiosity, project/self-edit proposals, guarded execution, watchdog recovery | Autonomous scientific discovery or durable self-improvement |
| Production VSL | `app/core/skill_ledger/`: versioned skill records, structural matching, application, outcome records, explicit degradation operation; project-generation hook | Autonomous production skill acquisition, semantic applicability, automatic detection of harmful task regressions |
| Evaluation | F1/F2/F3 safety/execution checks; task-specific test oracles; E0.1 trusted comparison apparatus | F2 task correctness, or universal evaluator integrity for every historical harness |
| Governance/recovery | Protected files, approval boundaries, snapshot/restore machinery, crash evidence, hashes | A complete, transactionally coherent, off-device recovery of all acquired state |
| External collaboration | File relays, message provenance, optional frontier-agent workflows | Core independence of the research program, reasoning-endpoint liveness, or transferred identity |

Important source facts:

* `RiverBrain.score_model()` reads `model_task_stats[*][*]["mean"]`, with a minimum-observation gate. It does not rank models from the trained classifier's predictions. The September 27 sandbox-outcome change now reaches that mean; council ratings already did. Explicit human ratings still train the classifier and increase observation counts without updating that model-specific mean. Counts can change the overall River weighting: “human feedback has absolutely no consequence” would also be too strong.
* VSL is disabled unless `VSL_ENABLED` is explicitly true; its enabled default mode is shadow. I found no VSL configuration assignment in the inspected `.env`, but did not inspect the live process's private environment. Stored lifecycle `ACTIVE` is therefore **not proof of current runtime application**. The latest stored Skill A version is nevertheless ACTIVE, which matters if it is enabled later.
* VSL chooses the first matching active feature key in sorted order. It has no demonstrated multi-skill arbitration or semantic applicability confidence. `record_outcome()` records an externally supplied verdict; `evaluate_degradation()` is separate and explicitly invoked. The production project path labels its verdict `f1_f2_safety_only`, which does not supply the `full_oracle` evidence used for semantic degradation.
* `snapshot_manager.py` snapshots seven named artifacts. It does not cover the full vector-store pair, task classifier, VSL, self-model claims, or all the other claimed continuity state. Existing partial snapshot/restore machinery is an asset, not proof of complete developmental continuity.

Sources: [orchestrator](../app/core/echo_model_orchestrator.py), [deliberation](../app/core/river_deliberation.py), [VSL runtime](../app/core/skill_ledger/runtime.py), [matcher](../app/core/skill_ledger/matcher.py), [project consumer](../app/core/echo_projects.py), [snapshot manager](../app/core/snapshot_manager.py), [predictive loop](../app/core/predictive_loop.py).

## 4. Research-program inventory

Statuses concern the scientific question, not whether a directory exists. Related namespaces are grouped without treating them as independent replications.

| Research program | Original question | Strongest result | Current status | Open question | Evidence quality |
|---|---|---|---|---|---|
| Council/capability Tiers 3–8 | Does architecture outperform model-only computation? | Historical synthesis can lose correct candidates; fixes have a small positive fresh retest | PARTIALLY ANSWERED | Current net advantage over a cost-matched simple system | Strong historical comparisons; limited current extrapolation |
| RiverBrain reward/ranking | Does feedback improve selection? | Real update/consumer paths; some old disconnects corrected | PARTIALLY ANSWERED | Correct actor/task credit and independent benefit | Strong source; weak causal utility evidence |
| Task-type classification | Does learned classification improve behavior? | Persisted classifier and routing consequences; downstream experiment isolation confounds documented | PARTIALLY ANSWERED | Out-of-sample task truth and net downstream benefit | Mixed; labels are not automatically ground truth |
| Memory ablation | Does retrieval improve responses? | July ablation did not separate measured differences from sampling noise | INCONCLUSIVE | Useful correctness gain, not response distance | Limited task coverage and metric |
| Retrieval capacity/minimal relevance gate | Can useful past evidence be found? | Relevant synthetic causal record in top six, unreliable first rank | PARTIALLY ANSWERED | Useful selection/abstention on real experience | Small, meaningful component evidence |
| Preference provenance | Are preferences formed and retained? | Label/position tracking explains the tested “preference” | NEGATIVE RESULT | Nothing requiring immediate extension | Strong counterexample; narrow domain |
| `learning`, `p3_causal_learning`, C1 directives | Can persistent state alter behavior? | Explicit directive exposure survives fresh processes; compliance 3/4 exposed trials | PARTIALLY ANSWERED | Experience-derived useful content, not explicit instruction storage | Real mechanism; tiny behavioral sample |
| RAOC | Does retrieved verified outcome change a new solution? | Existing 12-row pilot: control 3/3 correct, true-outcome 1/3 | INCONCLUSIVE | General useful benefit | Pilot only, three source pairs |
| Architecture A/first learning loop | Does historical failure advice improve retry/transfer? | Architecture A 5/6 vs 5/6 on one starting problem; clean-transfer identical outputs | NEGATIVE RESULT | No basis for repeating the same advice format | Bounded negative evidence, not all learning falsified |
| Attempt/F2/real-trace provenance | Can generated attempts and their outcomes be joined? | Candidate preservation and trace machinery exist | PARTIALLY ANSWERED | Complete influence/actor chain and task-correctness labels | Artifact evidence stronger than causal attribution |
| E5-mini/manifests/checkers | Can teaching/persistence be causally isolated? | Mock instrumentation and adversarial qualification exposed witness/checker limits | BLOCKED | Real, qualified discriminating trial | Apparatus/design, not learning evidence |
| AP-0/accumulation probe | Do experience-derived carriers improve fresh-worker performance? | Strong carrier-consumption results; constructor/execution limits and compiler doppelgänger | ANSWERED as component; SUPERSEDED as general learning test | No automatic Stage-1 entitlement | Rich artifacts; claims must remain conditional |
| Rung-1/E0 | Can hidden correctness be measured across a trusted boundary? | E0 defects found; E0.1 separated expected values and strengthened result contract | PARTIALLY ANSWERED | Actual corpus visibility and integration qualification | Strong source/tests; integration is separate |
| Persistent routing | Does retained feedback improve future strategy choice? | Three histories changed state; every holdout condition still chose DIRECT | NEGATIVE RESULT for this setup | Better routing representation/value remains unproven | Raw decisions decisive about absence of expression |
| Strategy characterization | Is there useful task-dependent strategy variation? | 216-generation corpus contains recurring, world-replicated defect families | PARTIALLY ANSWERED | Prospective exploitable advantage beyond static routing | Rich descriptive data; primary n=6 result inconclusive |
| G3 diagnosis/belief revision | Can model diagnostics repair/revise failures? | Reported 0/7 successful diagnoses/corrections and 0/3 useful revisions | NEGATIVE RESULT | Broad capability is not determined | Small but mechanistically informative |
| Minimal procedure transfer/VECT | Does retained procedural text help? | VECT 10/10 versus generic 6/10 and zero-state 5/10 | PARTIALLY ANSWERED | Autonomous lesson extraction | External authorship and underlying-program overlap |
| Restart procedure transfer | Does the same P help a fresh successor on new code? | Raw 9/10 with P versus 4/10 without, new code bank | ANSWERED narrowly | Origin of P remains external | Real persistence/use; small clustered panel |
| VSL acquisition/prospective transfer | Can a machine-extracted repair be retained and reused? | Skill A selected prospective 4/4 versus 0/4 ablation | PARTIALLY ANSWERED | Unselected coverage, harmful matches, independent acquisition replication | Best narrow positive learning evidence; duplicate code/selection limit |
| VSL “accumulation” | Does A help acquire B? | A-present 4/8 versus 3/8; B independently extracted and transferred | PARTIALLY ANSWERED | A→better B acquisition not established | Direct state/behavior evidence; accumulation interpretation too strong |
| Counterfactual autonomous acquisition | Do changed experiences produce selectively useful retained policies? | Codex mixed equality/difference qualification failed; later different-only A/B study 1/5 versus 0/5 | BLOCKED for original test; INCONCLUSIVE for later accumulation effect | Original crossover claim still unanswered | Do not conflate separate protocols |
| Equality/structural-prior/label-neutral diagnostics | Where does Boolean interpretation fail? | Real semantic errors and library-induced hypothesis changes | PARTIALLY ANSWERED; SHOULD CONSIDER RETIRING this sequence | Exact internal mechanism not identified | Good local contrasts; poor basis for global learning claims |
| Same-value/recoding/order studies | Are diagonal defaults evidence-resistant? | Recoding and row ordering alter outputs; simple diagonal/global-majority account incomplete | PARTIALLY ANSWERED | Encoding-resistant relational prior not established | Useful falsification; instrument/prompt dependence |
| Shadow invariance gate/blind cohort | Can invariance flag misleading success? | Retrospective discrimination; no independent prospective cohort | BLOCKED | Out-of-sample added value | Diagnostic, not qualified predictor |
| Prospective invariance tests 1–3 | Can newly acquired skills predict invariant transfer? | No novel eligible task passed the full gate; a known transformation did pass S9 | BLOCKED | Adequate untouched eligible evidence | Raw results support a narrower conclusion than PIT3 headline |
| PA-1 applicability induction | Can AST features identify repair applicability? | Same abstract pattern can require opposite decisions | BLOCKED | Adequate input representation and ground truth | Strong representation counterexample; no learner result |
| BA-0/1/2/3 | Can behavioral fingerprints identify a specific defect? | Harmful false positive; target-vs-whole-program distinction; BA-3 retrospective component judge | ACTIVE; PARTIALLY ANSWERED | Prospective predictor and repair compatibility | New BA-3 is useful, not untouched confirmation |
| Self-knowledge/epistemic arbitration/gen-epistemic | Can checked claims constrain narration? | Ground-truth/verification mechanisms work in bounded paths; pressure/uptake failures persist | PARTIALLY ANSWERED | Predictive or decision-useful self-knowledge | Good boundary work; narrative ≠ calibration |
| Shadow self-model | Can it predict its own behavior? | Prior performance inadequate; component retired | ABANDONED | No reason to resurrect without a new decision-relevant hypothesis | Explicit retirement record |
| Seams/Protector initiative | Do internal detections predict need for action? | Association explained by temporal component/circularity; residual proposed signal failed | NEGATIVE RESULT; branch closed | Voice/governance is a separate design question | Important negative evidence |
| Natural learning hunts | Does live unattended operation improve competence? | Updates and real watchdog restart; no demonstrated competence gain in inspected window | PARTIALLY ANSWERED | Useful autonomous improvement | Observational, with concurrent activity limits |
| Runtime/state/recovery/publication | Can lineage and behavior be reproduced/recovered? | Startup recovery, snapshot checks, publication repair, clean-checkout tests | PARTIALLY ANSWERED | Complete learned-state restore and coherent writes | Some closed defects; remaining state boundary important |
| Studio durable request lifecycle | Does a timeout lose/duplicate an experience? | Source shows work can outlive client and a retry can duplicate generation/learning | BLOCKED pending decision/implementation | Durable request identity and delivery semantics | Concrete engineering evidence; no new lifecycle implementation verified |
| Breakfast Club/externalizable state/relay | Can behavior, project state, communication survive boundaries? | Real messaging/watcher machinery; conditionable behavior; finite reachability | PARTIALLY ANSWERED | Provider-change attribution/identity continuity not identified | Engineering evidence; metaphysical claims unsupported |
| Inheritance/spore/open-ended development | Can descendants inherit and grow competence? | Exportable files/metadata and design concepts | Conceptual; BLOCKED | Validated inherited capability and autonomous accumulation | No corresponding full causal demonstration found |

Evidence anchors for this inventory include the linked primary records in §§5–7 and the dated reports under `audits/` named for each program. This inventory does **not** mark all old proposals as obligations to execute. Several have been superseded by a better specified claim or bounded sufficiently to stop.

## 5. The strongest evidence, independently reconciled

### 5.1 Real repair learning, with a much smaller transfer claim than the headline suggests

**DIRECT EVIDENCE.** `memory/experiments/skill_ledger/mvk/acquisition_result.json` records Skill A's failed/passing candidate pair. The extractor derives a restricted AST edit, subsequently refined by an investigator-added enclosing-call guard. That guard is scaffolding, not autonomous discovery of applicability. The experience-derived edit removes a negation from a tag-priority sorting key.

The [prospective true arm](../memory/experiments/skill_ledger/prospective/true_result.json) contains four selected applications that change failure to pass; its [substitution arm](../memory/experiments/skill_ledger/prospective/substitution_result.json) leaves all four failing. Selection and generation artifacts exist separately. However, the four selected candidates contain only two distinct exact code bodies; three are identical. These are four task instances, not four independent discoveries or four distinct program structures. New world vocabulary supplies limited new content, not arbitrary structural transfer.

The [accumulation true arm](../memory/experiments/skill_ledger/accumulation/a_present_result.json) versus [absent arm](../memory/experiments/skill_ledger/accumulation/a_absent_result.json) gives 4/8 versus 3/8. Only one candidate becomes correct because of A. The [B acquisition record](../memory/experiments/skill_ledger/accumulation/qualify_b_result.json) takes its failing/passing pair from **unaided** candidates; A-repaired outputs were excluded. B's later 2/2 versus 0/2 and [restart record](../memory/experiments/skill_ledger/accumulation/restart_check_b_result.json) support another retained repair. They do not establish A caused B's discovery or improved the learning algorithm.

**STRONG INFERENCE:** this is genuine, bounded system-level acquisition through investigator-designed extraction from machine experience. It is more than persisting an externally written lesson. It is also much less than autonomous open-ended learning. A deterministic extractor is allowed to learn; complexity and frozen foundation-model weights do not decide the classification.

### 5.2 The retained repair can harm a correct program

**DIRECT EVIDENCE.** [BA-0's false-positive artifact](../memory/experiments/ba0_behavioral_applicability/false_positive_evidence.json) contains a correct sorting key with descending numeric priorities: `nizog:3`, `renem:2`, `dulup:1`, `dogiz:0`. It correctly uses `-tag_priority[x[2]]`. Skill A removes the minus sign and breaks the ordering.

Independent two-entry witness, with equal scores: `(good,7,nizog)` and `(bad,7,dogiz)`. The original sort selects `good`; the retained edit selects `bad`. This follows by integer ordering and was recomputed without executing the artifact's candidate code. No model self-report or oracle verdict is needed to establish the reversal.

The current stored production record is [Skill A v4](../memory/skill_ledger/skills/K2.T5.tag_priority_direction.v4.json), lifecycle ACTIVE. **This is a mismatch between eligibility metadata and semantic jurisdiction, not evidence that the disabled-by-default production consumer has already caused a live incident.** It is the most important immediate safety implication of the learning research.

### 5.3 External instruction retention is real, but is a different result

Recounted [restart with P](../memory/experiments/restart_persistence_transfer/r_plus_results.jsonl): 9/10. [Without P](../memory/experiments/restart_persistence_transfer/r_minus_results.jsonl): 4/10. The September 27 restart report documents separate processes and a new four-program bank, improving on VECT's original overlap. The retained procedure was still an investigator-authored literal. New inputs are clustered within four programs, and candidates are generated for visible task instances. This establishes useful external instruction persistence/consumption, not an independently acquired general stripping procedure.

### 5.4 Routing state changed, but holdout decisions did not

Recounted all nine `memory/experiments/persistent_routing/lineage_*/holdout_result*.json` files. For each of three histories, the twin, adaptive state, and S0-restored condition choose DIRECT on every holdout task. Correctness is respectively 1/4, 2/4, 1/4 across histories, identical across conditions. State hashes differ; behavior does not.

This directly falsifies behavioral expression **in that run**. It does not show that useful contextual routing is impossible: unseen/coarse buckets and an unchanged winning action prevented the proposed mechanism from distinguishing itself. Repeating the same setup would not be informative.

### 5.5 The later Boolean A/B study ran; the original mixed-world mission did not

The Codex equality/difference qualification stopped below its 90% oracle gate. Equality was expressible, manually correct policies survived parsing/execution, and generated AND policies were correctly scored. That is not an autonomous-acquisition result.

Separately, [Claude's different-only protocol](2026-09-29_oracle_requalification_and_first_learner_ab_test.md) ran a five-target, single-shot comparison with an externally supplied, oracle-verified library. Recounted [raw result](../memory/experiments/counterfactual_acquisition/20260929_phase4_learner_ab/results/phase4_result.json): A succeeds fully on 1/5, B on 0/5; mean held-out accuracy .600 versus .541667. Two A trials copy a library policy inappropriately. The proper conclusion is **no demonstrated acquisition advantage at this sample size**, not established equivalence, and not “no learner was ever run anywhere.” Its library construction is not proof of accumulated autonomous experience.

### 5.6 Some recent summaries overstate what failed or qualified

* [PIT3](2026-09-29_prospective_invariance_prediction_test_3.md) says every task failed S9 in its executive account. Its own §15 and [raw task pool](../memory/experiments/prospective_invariance_test_3/task_pool_scored3.json) show K2.T1 had **2/10 independent matches and S9=true**, but was rejected as an already-known transformation. The sound conclusion is **no novel task passed the full eligibility gate**. It is not “no skill can ever transfer to an independently generated implementation.”
* [BA-2](2026-09-30_ba2_prospective_behavioral_fingerprint_test.md) had two eligible cases, but both primary labels were UNDETERMINED because other program defects masked the target property. That is an instrument limitation, not a prospective negative predictor result.
* Concurrent [BA-3](2026-09-30_ba3_ground_truth_instrument_qualification.md) introduces component-specific retrospective judgment and explicitly keeps revealed BA-2 cases contaminated for prospective reuse. The [22-row qualification artifact](../memory/experiments/ba0_behavioral_applicability/ba3_qualification_results.json) has **11 agreement=true and 11 agreement=null**, not 22 independent confirmed label agreements. The remainder includes mixed whole-program evidence and execution-invalid cases. This does not by itself refute BA-3's property-specific classifications; it bounds the independent confirmation. I inspected the artifact and design, not a fresh execution or exhaustive adversarial qualification.
* [Phase 11 raw predictions](../memory/experiments/counterfactual_acquisition/20260929_phase11_feedback_recoding_invariance/results/phase11_result.json) change under an information-preserving feedback recoding: equality 3/4→1/4, difference 3/4→2/4. The difference world's `11` answer also changes. [Phase 12](../memory/experiments/counterfactual_acquisition/20260929_phase12_frequency_recency_ordering/results/phase12_result.json) changes the equality mixed-row answer under ordering alone. A universal fixed diagonal rule plus evidence-sensitive mixed rows is therefore too strong. My earlier [same-value audit](2026-09-29_codex_same_value_prior_falsification.md) was inconclusive; later evidence does not justify upgrading it to a general low-level mechanism.

### 5.7 Council work has earned a bounded update, not either blanket verdict

The historical Tier-4 corpus contains real synthesis failures. The later [Tier-5 raw retest](tier5_retest/tier5_retest_results.jsonl) recounts **18/20 treatment versus 17/20 control**, with five discordant pairs; the reported paired exact p-value is 1.0. The control disables two synthesis fixes; it is **not** a cost-matched bare-model comparison. This supports specific fixes and corrects “the current council is proven worse.” It does not establish current council superiority. Preserve both facts.

### 5.8 Persistence works in places; complete recoverability has not been established

`memory/restore_log.jsonl` has four records: one successful and three failed restore attempts, all from July 1. Thus “restore has never been tested” is false. But those records and the seven-artifact snapshot do not establish recovery of today's much larger learned-state boundary.

The [September 20 recovery document](2026-09-20_feralecho_verified_backup_and_recovery_plan.md) explicitly says DESIGN ONLY. I did not locate a current complete-state, restore-tested generation manifest in the inspected repository paths. Off-repository/off-device success remains UNKNOWN, not presumed absent. The legacy [backup script](../backup_feral_echo.sh) rewrites `.gitignore`, excludes memory/data, and commits/pushes batches: it must not be described as a learned-state backup. It was only read.

## 6. TOP 10 STRONGEST THINGS FERALECHO ACTUALLY KNOWS

| # | Empirical finding | Strength and boundary |
|---|---|---|
| 1 | A restricted repair can be extracted from machine-generated failed/passing code and causally repair selected later code | Provisionally demonstrated; VSL A/B, small selected and partly duplicated corpus |
| 2 | Durable external instructions can improve fresh-process performance on new underlying code | Provisionally demonstrated; restart P 9/10 vs 4/10; external authorship |
| 3 | A syntactically matching retained repair can break a correct program | Demonstrated by actual artifact and independent ordering witness |
| 4 | Persistent statistical state can change without changing later decisions | Demonstrated; three routing histories, identical holdout actions |
| 5 | Sandbox execution/safety success is not task correctness | Demonstrated source distinction and wrong-output programs; F2 is not a learning reward oracle |
| 6 | More elaborate generation can damage correct candidate material; specific checks can prevent some such damage | Historical council artifacts plus bounded Tier-5 repair evidence |
| 7 | Information availability does not ensure model use | Boolean oracle misses, G3/first-loop failures, directive noncompliance; mechanism-specific, not universal inability |
| 8 | Semantically equivalent presentation can change predictions materially | Direct Phase 11/12 raw comparisons; rules out simple confidence in invariant induction |
| 9 | Apparent internal predictive signals can be reactive or circular | Seam decomposition removed the proposed predictive basis; retain the branch's negative conclusion |
| 10 | Recovery and reproducibility boundaries are concrete engineering constraints, not philosophical questions | Real watchdog restart, partial restore tests, clean-checkout failure and later source-publication repair |

## 7. TOP 10 THINGS FERALECHO SOMETIMES TALKS AS IF IT KNOWS BUT HAS NOT ACTUALLY ESTABLISHED

These are temptations in terminology or roadmap interpretation, not assertions that every investigator endorses them.

1. That ordinary unattended operation produces increasing task competence.
2. That acquiring A improves acquisition of B, rather than adding two independently obtainable repairs.
3. That an ACTIVE, held-out-PASS skill is safe wherever its AST precondition matches.
4. That a large River observation count or high classifier accuracy means correct model selection.
5. That a selected/requested model name proves who generated the credited code.
6. That F2 pass means the requested function works.
7. That retained self-descriptions are accurate, calibrated, decision-useful self-knowledge.
8. That successful file persistence/restart proves complete developmental continuity or recoverability.
9. That Boolean diagnostic failures identify a universal internal relational mechanism, or a ceiling on all local-model/system learning.
10. That a relay, copied context, “spore,” or externalizable-state package preserves a collaborator's identity or provides autonomous coordination.

## 8. Capability and acquisition ledger

| Category | Strongest present evidence | Boundary |
|---|---|---|
| Foundation/model-native | Local models already generate many correct programs; historical model-only baselines are substantial | Do not credit pretraining to Echo's lifetime |
| Architectural/scaffolding | Execution confinement, local routing, retrieval, guarded generation, candidate preservation, trusted comparison, lifecycle controls | Often real and valuable even with no learning |
| Acquired capability | VSL's restricted AST repair extracted from machine fail/pass experience; isolated correct Boolean induction in one library-conditioned trial | Investigator designs extractor/hypothesis language and experiment; applicability is not autonomously mastered |
| Persisted acquired capability | Stored VSL records and separate-process reuse, including B restart evidence | Small repair inventory; complete live-state restore not proved |
| Transferable acquired capability | VSL's selected same-family cases/new world vocabulary; second repair's small transfer panel | Mostly narrow syntax/domain; duplicate programs and selection reduce effective evidence |
| Persistent adaptation without established competence gain | RiverBrain statistics/classifier; task classifier; Bayesian news posterior | Real updates and consumers, but no clean general gain attribution |
| Externally assisted retained competence | VECT/restart P and C1 human-confirmed directive | Useful state supplied externally; distinguish from autonomous extraction |
| Accumulated competence | Multiple artifacts exist; A improves one later performance case | No demonstrated improvement in acquisition of B, broad cumulative growth, or learning-to-learn |
| Unknown causal provenance | Natural self-edit “success,” many quality scores, actor labels on fallback/retry paths | Activity and bookkeeping cannot fill the missing causal links |

**What has Echo actually learned?** In a narrow research subsystem it has acquired reusable edit state from its own locally generated attempts, through an explicit investigator-written extraction algorithm. In production it also updates several statistical models from streams of observations. The stronger phrase “learned useful competence during ordinary autonomous life” is not yet supported by an adequate state→decision→independent-outcome comparison.

**Is it a continual-learning system?** Technically, it contains online learners and persistent adaptive state. As a system demonstrated to continually improve useful competence while retaining old abilities, **not yet**. The production VSL is a consumer, not an autonomous acquisition service. Both qualifications matter; frozen foundation weights are not the deciding objection.

The [natural learning hunt II](2026-09-29_natural_learning_event_hunt_ii.md) reports 106 self-edit terminal events in its bounded window: 94 safety-blocked, 12 dry-run-staged, zero success. It documents state changes and a watchdog restart, not an isolated improvement. Those observations neither negate the controlled VSL result nor prove a lifetime learning trajectory.

## 9. Original ambitions: preserve the questions, retire unwarranted answers

[ORIGIN.md](../ORIGIN.md), [COUNCIL.md](../COUNCIL.md), [README](../README.md), and [EMERGENCE_ROADMAP](../EMERGENCE_ROADMAP.md) describe a local persistent collaborator with memory, self-observation, initiative, guarded self-modification, and continuity. They also contain normative identity/governance language. That is evidence of intended design and values, not evidence of an experienced identity or a growing intelligence.

| Ambition | Assessment | Decision |
|---|---|---|
| Local, useful collaborator | Already operational; usefulness above simpler inference remains workload-dependent | KEEP; measure user-valued outcomes |
| Persistent developmental continuity | Plausible operationally as recoverable, influential learned state | REFRAME around declared state, restoration and retained competence |
| Autonomous learning | A plausible bounded target; narrow extraction proof exists | CONTINUE conditionally, not as a present general property |
| Continual accumulated competence | No evidence of sustained positive growth with retention/interference control | PAUSE expansion until a useful repeatable learning unit exists |
| Self-model/introspection | Telemetry and checked architectural facts are real; predictive self-knowledge is weak | Keep instrumentation; stop narrative-based evidentiary claims |
| Autonomous experimentation | Schedulers can initiate actions; closed scientific hypothesis→test→revision competence is missing | Treat as a future capability, not scheduler liveness |
| Inheritance/digital instinct | Files and rules can be copied; adaptive utility in descendants remains unproved | PAUSE as research; do not conflate with backups |
| Open-ended development | Neither logically excluded nor supported by current toy results | Retain as motivation, remove from near-term success criteria |
| External-agent collaboration | Useful research aid and optional relay | KEEP optional; explicitly separate from Echo's native competence |
| Protector/constitutional voice | Legitimate governance design question, not an inferred autonomous faculty | PAUSE automatic authority; do not revive disconfirmed seam trigger |

The appropriate causal skeleton remains useful but needs two additions:

`evaluated experience → attributed update → retained state → trustworthy boundary → measured use → correctness benefit minus regressions and cost → repeated retention under interference`.

The original experience→evaluation→retention→transfer sequence omitted **correct causal credit** and **net benefit including harm**. Neither is optional when acquired state can modify code or influence future training data.

## 10. UNFINISHED BUSINESS REGISTER

Importance concerns consequences, not permission to implement. Costs are relative to this project's local resources: LOW = focused inspection/offline checks; MEDIUM = bounded integration/qualification or small local trial; HIGH = extended histories, workload studies, or broad redesign. “External” means dependence on frontier services, not local Ollama.

| ID | Unfinished obligation and evidence | Status | Scientific / engineering importance | Risk if ignored | Information gain | Cost | External dependence / prerequisite |
|---|---|---|---|---|---|---|---|
| U1 | Complete, valid, coherent recoverable state: seven-artifact snapshots versus larger actual state; September 20 design not a restore proof | OPEN / qualification debt | HIGH / CRITICAL | Lost/corrupted development mistaken for continuity | HIGH | MEDIUM | None intrinsically; declared manifest and disposable recovery target |
| U2 | Skill A semantic permission: current ACTIVE record plus demonstrated harmful match | OPEN / qualification debt | CRITICAL / HIGH | Correct code damaged while metadata still says qualified | HIGH | LOW–MEDIUM | Independent target/full correctness; no production activation assumed |
| U3 | Current whole-system net useful advantage at matched cost, before selecting successes/matches | EXPERIMENT DEBT | CRITICAL / HIGH | Optimize impressive logs instead of useful work | HIGH | MEDIUM | Frozen bounded workload, strong simple comparator, correct evaluator |
| U4 | Actor and outcome credit: retry selected-name mismatch; synthesis shortcut/fallback ownership | OPEN / provenance debt | HIGH / HIGH | Wrong model rewarded/punished and misleading learning analysis | HIGH | LOW for localization; MEDIUM for qualification | No frontier dependence; bind claims to actual route |
| U5 | Reward meaning: F2 import/execution, heuristic quality and council opinion share rank statistics | OPEN / evidence debt | CRITICAL for learning / HIGH | Learn proxy satisfaction rather than requested competence | HIGH | MEDIUM | Independent task labels, declared estimand |
| U6 | Human-rating sign does not reach model-specific mean; counts still change influence weighting | OPEN / implementation decision | MEDIUM / MEDIUM | “High-trust learning” label overstates targeted consequence | MEDIUM | LOW | Decide intended behavior first; do not blindly wire into same scalar |
| U7 | River multiwriter freshness and non-atomic pickle write; vector index/metadata are separately persisted | OPEN / integrity debt | HIGH / HIGH | Valid state silently overwritten or mismatched | HIGH | MEDIUM | Isolated writer/recovery qualification; no live test needed here |
| U8 | End-to-end request identity across Studio timeout/retry | IMPLEMENTATION DEBT | HIGH / HIGH | Duplicate experiences, split conversation and training histories | HIGH | MEDIUM | Existing trace/outcome patterns; no new agent architecture needed |
| U9 | Original autonomous counterfactual acquisition crossover remains unexecuted after mixed-world qualification failed | BLOCKED | HIGH / LOW | Premature attribution of experience-derived competence | MEDIUM–HIGH | MEDIUM | Original oracle gate; any altered task is a new protocol, not retroactive completion |
| U10 | Independent VSL acquisition replication on unselected fresh material | EXPERIMENT DEBT | HIGH / MEDIUM | One selected extraction mistaken for reliable learning | HIGH | MEDIUM | U2/U3 measurement; frozen extractor and failure accounting |
| U11 | A+B retention, competition, forgetting and acquisition benefit | DEFERRED | HIGH / MEDIUM | Count of stored skills mistaken for accumulation | HIGH eventually | HIGH | Repeatably useful acquisition; B must not be independently obtained by identical control |
| U12 | BA predictor's untouched prospective added value, distinct from BA-3 instrument qualification | BLOCKED / evidence debt | MEDIUM–HIGH / MEDIUM | Retrospective relabelling mistaken for confirmation | MEDIUM | MEDIUM | Qualified property judge, uncontaminated cohort; do not reuse BA-2 as prospective |
| U13 | Retained-state benefit in ordinary natural operation | OPEN | HIGH / MEDIUM | Autonomous activity narrated as improvement | HIGH | MEDIUM–HIGH | U3–U5 and reliable request/event boundaries |
| U14 | E0.1 actual-corpus integration boundary | QUALIFICATION DEBT | HIGH / HIGH | Hidden answers reintroduced through readable files/metadata | HIGH if integrating | LOW–MEDIUM | Review exact attached corpus/path; no need to re-audit unrelated sandbox features |
| U15 | Research clean-room package including declared ignored state/data/model digest | PARTIALLY RESOLVED | HIGH / MEDIUM | Published source cannot reproduce result | MEDIUM–HIGH | LOW–MEDIUM | Publication fix exists; newest untracked code and ignored artifacts still need explicit packaging |
| U16 | Useful retrieval ranking and abstention | DEFERRED | MEDIUM / MEDIUM | Irrelevant history consumes context or misleads | MEDIUM | MEDIUM | Outcome-labelled workload, not generic similarity score |
| U17 | Calibrated self-prediction that changes a useful decision | DEFERRED | MEDIUM / LOW | Narrative mistaken for metacognition | MEDIUM | MEDIUM | Out-of-sample target and simple baseline; old retired predictor is not the answer |
| U18 | Relay endpoint/mission liveness beyond transport ACK | PARTIALLY ANSWERED | LOW for learning / MEDIUM for operations | Delivered message mistaken for ongoing reasoning | LOW for current main effort | MEDIUM | Optional operator workflow, never core autonomy dependency |
| U19 | Historical failed-source reconstruction | ABANDONED where bytes are absent | HIGH historical limit / LOW | Invented transfer claims from incomplete history | LOW to pursue | Unbounded/impossible in missing cases | Preserve limitation; candidate logging only helps subsequent attempts |

### Dependencies and actual closure

The nearest defensible learning objective is **repeatable net benefit from experience-derived state on later useful cases**, not the completion of every historical protocol. It depends on trustworthy correctness and state/actor boundaries. A credible live accumulation claim additionally depends on recovering that state and controlling interference.

```
declared recovery/state boundary ─────────────────────────────┐
task correctness + attribution + per-request identity ───────┤
independent skill-jurisdiction/harm evidence ────────────────┤
                                                           v
                  unselected, cost-matched net-utility comparison
                                                           |
                                      if useful and repeatable
                                                           v
                    independent acquisition/retention replication
                                                           |
                                                then accumulation
```

Some items are genuinely closed or materially advanced and should not return as blanket blockers:

* The old missing-source clean-checkout failure was followed by publication/reconciliation commits and the [Gate-3 execution report](2026-09-28_gate3_execution_report.md). Current tracked source includes the previously missing research dependencies. That does not package all ignored learned data or today's new untracked research.
* Candidate-code preservation is implemented. It repairs artifact provenance, not proof of influence or old missing bytes.
* The sandbox-outcome→ranking-mean disconnect was changed. The broader “all verified rewards now correctly guide model choice” claim remains unqualified.
* E0.1 repairs are real code, not an active E0.1 implementation mission waiting to happen. Do not carry forward the September 23 “Claude is currently repairing it” status indefinitely.
* The seam initiative branch has an explicit negative closure. It is not an orphan to reactivate.
* BA-3 changes the status of BA-2's ground-truth instrument problem. It does not change BA-2's original prospective verdict.

## 11. Dead ends, pauses, and diminishing returns

| Direction | Decision | Why; what could reopen it |
|---|---|---|
| Repeated attempts to prove the same Boolean diagonal/label explanation | STOP current sequence | Presentation and induction failures are established sufficiently to distrust this interface. A concrete deployment decision requiring a discriminating mechanism would justify a new bounded test; curiosity alone does not |
| More single-task prompt/diagnostic injections after Architecture A, G3 and recoding results | STOP as main effort | The program repeatedly measures unreliable uptake. Require a new causal mechanism and an out-of-sample decision, not a new wording |
| Broad evaluator philosophy/security audits of unchanged apparatus | STOP repetition | Check a new integration's concrete information paths; rerun a small frozen qualification when code changes |
| AP-0 Stage 1 as proof of general learning | RETIRE that claim | Fixed compilation/selection can pass. Component carrier and task tests remain useful |
| Unqualified ACTIVE skill use | PAUSE | A demonstrated harmful match already exists; more positive cases cannot cancel it |
| More invariance task-pool hunting until an eligible new task appears | PAUSE | PIT1–3 already identify a task/extractor/coverage bottleneck. Eligibility failure is data, not a reason for unlimited selection |
| Behavioral applicability research | CONTINUE conditionally and briefly | It addresses a real harm, but needs target-specific truth and separate repair compatibility. BA-3 may reduce apparatus debt; do not elevate it into the automatic main research program |
| Accumulation/learning-to-learn ladders | PAUSE | One useful retained unit is not yet repeatably safe and valuable on an unselected distribution |
| Self-description/identity preference probes as learning evidence | STOP | Persona/position effects and lack of independent prediction make the claim non-diagnostic |
| Predictive seam-driven Protector initiative | STOP this branch | Existing decomposition and closure already removed its proposed empirical basis |
| Source publication and recovery verification | CONTINUE | Protects all current findings and the stated continuity objective; concrete, finite closure possible |
| Same frozen routing setup | STOP repetition | All holdout actions stay at the default. A future revision needs qualified decision headroom, not more identical histories |
| Local-model fine-tuning as the immediate remedy | PAUSE | No evidence yet that weight change is the missing minimal mechanism; evaluation/credit/jurisdiction deficiencies would contaminate training too |
| External-model identity rescue/continuity metaphors | RETIRE as empirical claims | Preserve transcripts/project state and measure functionality; do not claim identity moved |

The disproportionate expenditure is **serial explanation of failures in tiny constructed tasks without a sufficiently explicit downstream decision**. The early experiments were valuable. Their existence does not justify an indefinite chain of follow-ups.

## 12. Architectural archaeology: what to keep or retire

| Component/concept | Recommendation | Evidence-based reason |
|---|---|---|
| Local inference, guarded execution and deterministic task testing | KEEP | They are functioning assets independent of frontier subscriptions |
| VSL versioning, kill switch, scratch-isolation and provenance | KEEP | Useful substrate with demonstrated narrow causal reuse; preserve conservative defaults |
| VSL “verified” as universal semantic permission | DEPRECATE that interpretation | Actual harmful false positive; qualification applies to specified evidence/domain |
| VSL lexical first-match arbitration | REVALIDATE before multi-skill use | It has not earned claims of relevance, conflict resolution or optimal composition |
| River classifiers/accuracy metrics as model-competence evidence | DEPRECATE interpretation; REVALIDATE utility | Rank consumer is the rolling mean; predictor targets are quality proxies |
| Human-feedback pathway | REVALIDATE intended contract | Persisted classifier changes and global weighting differ from targeted model reward |
| Snapshot manager | KEEP, accurately scoped | Real partial restore infrastructure; not a complete backup/continuity service |
| `backup_feral_echo.sh` as a state-backup procedure | DEPRECATE; preserve historically | Rewrites ignore rules, omits learned state, pushes; does not satisfy the recovery plan |
| Shadow model, WOLF/unsafe retired authority machinery | KEEP RETIRED / ARCHIVE | Prior retirement and safety decisions should not be reversed by anthropomorphic ambition |
| Completed Boolean/first-loop/old routing experiments | ARCHIVE as immutable evidence | Keep scripts and failed results; remove from the active default agenda |
| E0.1, AP-0 generators, cost-recording/checker utilities | KEEP as reusable components | Reduces rebuilding; qualify each actual integration and avoid sealed Stage-1 exposure |
| Multiple inconsistent “current” roadmaps | ARCHIVE superseded authority, retain history | Contradictory claims and stale statuses are now an operational evidence problem |
| Relay infrastructure | KEEP optional | Message transport and provenance are useful; cannot supply core recovery or autonomy |
| Telemetry called “self-awareness,” “confidence” or “competence” | REPLACE terminology where it implies unmeasured ability | Measurements should be named for their actual source and target |

No component was deleted, disabled, renamed, or changed by this audit.

## 13. TOP 5 EXPERIMENTS WE SHOULD BE EMBARRASSED WE HAVEN'T RUN YET

This title names **missing decisive versions**, not an assertion that no related pilot exists. In particular, council comparisons, partial restores, VSL transfer, and a five-trial accumulation-style comparison have already run.

1. **Unselected net-utility test of retained repairs.** Include tasks where a skill should help, where it should abstain, where it can hurt, and where nothing matches; count all tasks. Compare current retained-state use with state removed and a competent frozen repair/strategy baseline at matched total opportunity/cost. Primary target: independent correctness and harmful regressions, not match rate. This decides whether the existing learning unit deserves expansion. Another Boolean label probe does not.

2. **A complete declared-state recovery drill.** Recover a disposable successor from the exact package claimed to preserve Echo, and compare previously recorded capabilities plus state identity and cross-file consistency. Include a bad-state/rollback condition without touching live Echo. July's partial restores and a watchdog restart are insufficient. If retained knowledge cannot be recovered, the project's central persistence promise fails before abstraction matters.

3. **Independent end-to-end acquisition replication with no success-selection escape.** Freeze the existing extraction mechanism before new histories; count histories that produce no extractable pair, no applicable later case, or harmful state. The comparator gets the same search/evaluation budget. Evaluate later program structures not chosen because the learned matcher already fits them. This distinguishes a productive learning mechanism from one successful mined diff. It is conditional on a trustworthy measurement boundary, not authorization to reopen the stopped equality protocol.

4. **Retention/interference and net gain after acquiring a second skill.** Existing A/B work is not this test: B came from unaided candidates and A→B acquisition benefit was not shown. Ask whether B degrades A or unrelated correct behavior, whether overlapping matches compete, and whether the full retained set beats isolated skills and fixed baselines. More ledger entries alone cannot answer it.

5. **Prospective applicability *and* repair-compatibility risk/coverage test.** Separate “target defect exists” from “this edit fixes it without breaking other requirements.” Compare the proposed behavioral predictor against the current structural matcher and a simple frozen baseline; preserve UNDETERMINED and abstentions in the denominator. BA-3 supplies a possible component judge, not this missing prospective result. This test could rule out the proposed direction cheaply before another architecture is built.

## 14. Missing architecture and the wrong-abstraction test

The most conspicuous gap is **a defensible contract connecting a learned action to the conditions where it is useful, the independent evidence supporting that use, and the conditions where it must abstain or lose authority**. This is a capability requirement, not a proposal to build a new relational module, applicability learner, VRM, or ledger.

Current objects and metrics are carrying several different meanings:

| Object | Distinctions currently at risk of collapse | Consequence |
|---|---|---|
| “Skill” | Defect recognition; syntactic match; edit compatibility; correctness; authority to act | A match can be correct structurally and wrong semantically; BA-0/1 demonstrate it |
| Model/task mean | Style/heuristic quality; peer preference; execution success; actor credit; task difficulty | A rising value is not an interpretable competence improvement |
| “Memory” | Availability; retrieval; exposure; use; useful effect | Storage/retrieval graphs overstate learning without the last links |
| “Outcome” | Safe execution; task correctness; deployment; user receipt; future utility | Dry-run/sandbox success can masquerade as useful completed work |
| “Independent task” | New input; new vocabulary/world; new program; new template; independent acquisition history | Repeated variants inflate transfer and significance claims |
| “Continuity” | Restored bytes; restored dependencies; behavioral resemblance; retained ability; identity | Backups or prompt conditioning get credited with much more than they show |

Decomposition is warranted **only where it changes a decision or prevents a measured error**. BA-3's component truth is useful because unrelated defects masked the target. It does not follow that every component needs a new learned subsystem. A direct independent correctness test or explicit abstention may be simpler and more reliable.

Other missing or unqualified capabilities: causal actor credit across fallback/retry; transactional learned-state ownership/recovery; selection under competing skills; outcome-grounded confidence/abstention; and a verified process for extracting useful new procedures reliably. Generalized abstraction, self-curriculum, and learner modification are further away and should not be built around first.

## 15. Accumulation and autonomy

**Same-task reuse:** supported in narrow conditions. **Near transfer:** supported for selected VSL structures and externally supplied P on new snippets. **Far transfer:** not established. **Repeated skill retention:** partial evidence. **Learning A improves learning B:** not established. **Learning-to-learn:** not established.

A fixed algorithm can accumulate useful state and deserve the label learning. Conversely, a growing library can repeatedly retrieve independently acquired solutions without making acquisition itself better. The project should stop treating those two observations as a semantic dispute and keep separate endpoints.

| Description | Does current FeralEcho earn it? |
|---|---|
| Automated | Yes: persistent schedulers, generation, updates, logs and watchdog operation |
| Agentic | Yes in bounded software terms: it selects actions/models and pursues supplied or scaffold-generated goals |
| Autonomous | Qualified: some initiatives run without immediate keystrokes under investigator-written goals/governance; consequential actions and research competence retain external dependencies |
| Self-improving | Not established as a general operating property; narrow research mechanisms improve later outputs, but natural cumulative improvement is unproved |

Automation can be useful without developmental autonomy. Criticism of the stronger claim should not erase the useful engineering; neither should it turn uptime or many attempts into evidence of improvement.

## 16. Self-model, introspection, and the seam branch

The current `memory/self_model_claims.jsonl` contains 24 rows, all `verified=false`; 19 concern RiverBrain and five the generic self-knowledge subject. That is evidence of recorded verification/correction events, not 24 learned positive capabilities. The [September 23 self-model audit](2026-09-23_self_model_claims_adversarial_learning_audit.md) previously counted 23 and exposed consumer/subject limitations. This review's count updates the state without inferring that the new row improved anything.

Verified architecture notes, direct ground truth, and explicit uncertainty boundaries have real practical value. The [living self-model](2026-09-08_living_self_model_FINAL.md) and [epistemic arbitration](2026-09-08_epistemic_arbitration_FINAL.md) work support bounded persistence and checking, while pressure/uptake experiments show that exposed facts do not guarantee faithful later narration. No inspected result establishes a generally calibrated model of Echo's own future success that improves decisions beyond a simple task/performance baseline.

The Bayesian news `WorldModel` is a real statistical learner over supplied counts, not fictional because its domain is small. Its surprise events and restored posterior are also not a validated model of the agent's own competence.

The [seam mechanistic decomposition](2026-09-28_seam_signal_mechanistic_decomposition.md) and [closure](2026-09-28_seam_initiative_branch_closure.md) are decision-relevant negative evidence: the proposed independent initiative signal did not survive analysis of temporal/circular components. Do not turn that closed empirical branch into a Protector trigger.

**Recommendation:** CONTINUE factual telemetry/provenance as maintenance; PAUSE new self-model research until there is an externally checkable prediction and useful decision; STOP self-narrative, preferred-label, or watcher-presence results being used as evidence of identity, introspection, or acquired competence. Breakfast Club can remain a modest behavioral regression instrument, with UNKNOWN provider-cause attribution, if there is a practical monitoring need.

## 17. Governance, safety, and the risk created by successful learning

Strong safeguards include restricted self-edit targets, sandbox/process boundaries, human authorization for consequential operations, immutable/additive evidence habits, VSL's kill switch and conservative default, explicit lifecycle states, and independently inspected evaluators. They are real engineering assets. A governance document alone is not a mechanism; the project has correctly retired some mechanisms that violated its intent.

Ranked risks specific to more effective persistence/learning:

1. **Incorrect authority to reuse a learned action.** Skill A's harmful match is already demonstrated. F1/F2 can approve a safe but wrong transformation. This is the first weakness that becomes dangerous if learning suddenly becomes more prolific.
2. **Incorrect credit and reward semantics.** Bad actor labels or proxy outcomes make the system retain the wrong lesson or favor the wrong generator. More observations amplify the error rather than cure it.
3. **Silent state loss or corruption.** River's save compares total generic observation counts, not the complete state version, and writes the pickle directly. Independent vectors/metadata and other writers have separate consistency boundaries. File locks do not establish semantic freshness.
4. **Unmeasured interference.** First-match skill selection, no demonstrated composition policy, and small near-transfer tests leave regressions outside the qualification panel largely unmeasured.
5. **Evidence duplication/loss at operational boundaries.** A timed-out Studio request can have updated internal logs/models before its response is delivered; a resubmission has a new trace ID. Candidate preservation cannot by itself repair that causal history.

No live damage rate is inferred from these source paths. Risks 1 and the partial source defects are demonstrated; their population impact is UNKNOWN. This is sufficient to prioritize bounded qualification, not to authorize emergency changes.

## 18. External dependencies and the October-1 test

If frontier subscriptions disappear tomorrow, installed local inference, routing, schedulers, vector retrieval, local state, sandbox execution, existing skills, project files, and deterministic analysis tools remain. Explicit directives and retained repairs do not need Claude or Codex to be read. Existing source and preserved raw evidence remain analyzable locally, subject to declared environments and artifact availability.

What does **not** survive automatically is the current rate of scientific work: investigators author protocols, build oracles, choose useful task distributions, localize defects, and reconcile claims. The local G3/Boolean evidence is a direct warning against assuming Echo will simply take over those tasks. It can continue producing attempts and statistical updates; that is not autonomous continuation of a valid research program.

| Dependency | Classification | Consequence of losing it |
|---|---|---|
| Installed Ollama/MLX models and local Python dependencies | Core local execution | Existing installation remains usable; rebuilding requires preserved binaries/configuration |
| Claude/Codex reasoning and code work | Research dependency | Investigative throughput and methodology support decline sharply |
| Frontier relay processes/subscriptions | Optional collaboration | Messages/reasoning at those endpoints stop; Echo core should continue |
| Internet/news/optional tools | Feature dependency | Some input streams/tools stop; not equivalent to core failure |
| Human authorization and scientific judgement | Governance/research dependency | Consequential approvals and valid experimental design do not become automatic |
| Ignored learned-state files and model digests | Reproducibility dependency | Git source alone cannot recreate actual lifetime state |

The relay work usefully distinguishes transport, delivery, consumption, acknowledgement, endpoint liveness and mission liveness. Replicated mission text cannot wake a nonexistent reasoning process. [Ark's corrected check-in report](2026-09-27_ark_checkin_protocol_design.md) also shows the cost of treating a deployment label as a separate machine. Neither a mailbox nor an “Ark” name is a verified independent descendant or backup.

**STRONG INFERENCE:** frontier independence is plausible for local operation, partially achieved for reproducible bounded experiments, and not established for independent open-ended research or self-repair. These are different requirements.

## 19. Information gain versus cost

These are judgement rankings, not numerical utility estimates. Each direction has a decision it could change. Further work is warranted only while that decision remains open.

| Rank | Direction | Information gain | Cost | Decision changed / evidence basis |
|---|---|---|---|---|
| 1 | Bound harmful skill application and distinguish permission from match | HIGH | LOW–MEDIUM | Whether any active learned repair is acceptable; direct false-positive artifact |
| 2 | Complete-state recovery qualification | HIGH | MEDIUM | Whether retention/continuity is operationally credible; current partial snapshot boundary |
| 3 | Current system/retained-state net utility against a strong frozen baseline | HIGH | MEDIUM | Whether to expand, simplify or retire architecture; historical tiers do not settle current net value |
| 4 | Actor, task and outcome-credit audit of actual consumer paths | HIGH | LOW–MEDIUM | Whether live adaptation can be interpreted at all; concrete remaining mismatches |
| 5 | Independent unselected acquisition replication | HIGH | MEDIUM | Whether narrow VSL success is a reliable learning unit |
| 6 | Multi-skill interference and forgetting | HIGH after prerequisites | HIGH | Whether accumulation is feasible without erasing prior utility |
| 7 | Prospective BA risk/coverage and repair compatibility | MEDIUM–HIGH | MEDIUM | Whether behavior-based recognition beats a simpler guard |
| 8 | Revised contextual routing, only after demonstrating decision headroom | MEDIUM | MEDIUM | Whether history beats competent static selection; old frozen setup cannot answer it |
| 9 | Retrieval abstention and causal relevance on useful tasks | MEDIUM | MEDIUM | Whether memory helps rather than adds context noise |
| 10 | Calibrated self-prediction with a decision consumer | MEDIUM | MEDIUM–HIGH | Whether self-model work deserves renewed investment |

The next Boolean label variant, another general evaluator treatise, and another persona/identity probe rank LOW information gain for the current strategic decision. Cheap does not mean worth doing if the result cannot change the allocation of work.

## 20. One-month research agenda

This agenda is conditional, finite, and centered on current assets. It is not an implementation plan or permission to run it.

| Week | Primary question | Required decision / stop condition |
|---|---|---|
| 1 | Can the declared retained state be recovered, and can we measure known beneficial and harmful skill uses honestly? | Stop capability trials if restoration, actor attribution needed for the claim, or independent correctness is not trustworthy. Resolve the bounded infrastructure question; do not start a new learner |
| 2 | What useful workload and strong simpler baseline expose whether current Echo adds value? | Freeze a small externally checkable panel and cost accounting. Stop if baseline saturates, evaluator is ambiguous, or the workload has no legitimate use. Do not keep searching for a favorable panel |
| 3 | Does retained state improve net correctness on the full panel after a clean boundary, with harms and costs counted? | One preregistered bounded comparison; no selective repair/rerun of valid failures. Stop on a valid result or a documented instrument defect |
| 4 | Is the effect large, reliable and useful enough to justify expanding acquisition? | If yes, choose one independent acquisition replication next. If no useful advantage and uncertainty is sufficiently bounded, simplify the system and retire the unhelpful path. If underpowered, state that; do not promote a suggestive result into a new ladder |

Success for this month is a resource-allocation decision supported by evidence. It need not be a positive learning result.

## 21. Independent final surprise pass

I found no defensible wholly new latent faculty or secret learning mechanism. The strongest neglected issue is an **incompletely reconciled interaction between reward wiring and producer attribution**.

**DIRECT EVIDENCE:** `self_edit_manager.generate_code_from_plan()` now assigns `ECHO_SYNTHESIS_MODEL`, with a comment claiming that model always produces the delivered text. But `river_deliberation.py` explicitly returns agreed candidate code without synthesis, and returns a selected candidate on empty/completeness-failed synthesis. Even when synthesis runs, it consumes other models' work: a single producer label is not automatically valid causal credit. The retry at `self_edit_manager.py:2121` still calls `choose_model()` for a tracking name and separately calls `echo_query()` without binding that choice, then credits the tracked name's heuristic/sandbox statistics.

The September 22 adversarial report already identified these exceptions. The later primary-attempt fix did not close all of them. Meanwhile, `learn_from_sandbox_outcome()` now updates the ranking mean. The issue is therefore not merely a misleading log label: **a stronger feedback wire can make an old attribution error consequential to future selection**. Actual historical frequency and the size of the resulting routing error remain UNKNOWN; no live test was performed.

This was overlooked in the sense that the repair narrative is broader than its coverage, not in the sense that nobody ever noticed any part of it. The question worth recovering is:

> **What behavior is each learning signal actually rewarding, whose behavior was it, and can that update change the later decision we claim it changes?**

A related old orphan is explicit human feedback: its sign trains a classifier not used for model ranking, while its count can increase global River influence. That is already documented in the September 23 reward-wire audit and still present in source. Do not “discover” it anew as a universal dead-feedback claim; do not assume the sandbox repair fixed it.

## 22. Direct answers, including the brutal questions

1. **What is FeralEcho today?** A local, persistent, guarded agent system and a large research scaffold, with real online adaptation and narrow experience-derived repair reuse.
2. **What has it actually demonstrated?** The strongest developmental result is that a machine-extracted executable edit can survive a boundary and causally improve selected later cases. The strongest general engineering result is controlled observation and falsification of its own apparent successes.
3. **What has it actually learned?** Restricted repair transformations and statistical state; not a demonstrated general procedure for discovering useful abstractions or improving its own learner.
4. **What remains unproven?** Net useful lifetime improvement, reliable applicability, broad transfer, robust complete-state continuity, and accumulation that improves future acquisition.
5. **What has been falsified or materially weakened?** F2-as-correctness, persona-as-preference evidence, seam-based predictive initiative, universal safety of the stored syntactic repair, and the simple stable diagonal-prior interpretation. None falsifies all possible system learning.
6. **What substantial work is unfinished?** U1–U18 above: recovery, safe jurisdiction, attribution/reward, unselected utility, independent acquisition, interference, prospective applicability, and current artifact reproducibility. Historical missing source cannot be retroactively repaired.
7. **What should continue?** Bounded independent correctness/provenance work and a finite test of whether existing retained state is useful at acceptable risk and cost.
8. **What should pause?** Accumulation expansion, new learner architectures, fine-tuning, generalized applicability machinery, descendant/identity experiments, and new self-model programs.
9. **What should stop?** Serial prompt/label diagnostics without a decision consequence; treating memory, state change, agreement, uptime, or stored skill counts as competence evidence.
10. **What should be archived/deprecated?** Completed negative diagnostic branches, superseded roadmap authority, retired shadow/unsafe-authority mechanisms, the legacy backup script's role as a state backup, and overbroad “verified/confidence/self-awareness” terminology.
11. **Which missing experiments matter most?** The five in §13. The most valuable is a non-selected net-benefit comparison; the most urgent prerequisite is trustworthy recovery and safe correctness measurement.
12. **What architectural capability is most conspicuously missing?** A reliable connection between a retained action, its justified applicability, independent benefit/harm evidence, and authority to act or abstain.
13. **What safety weakness matters first if learning improves tomorrow?** Wrongly applying durable knowledge to a superficially matching case, then validating only safe execution and preserving the mistake.
14. **How dependent is meaningful progress on frontier agents?** Current scientific diagnosis, design and adjudication are heavily dependent. Local runtime and deterministic retained-state use need not be.
15. **What survives if Claude/Codex disappear?** Installed local operation and declared files/skills; not an automatically self-directing scientific team. Reproduction still requires the ignored artifacts and environment, not just Git.
16. **What are the three highest-value next moves?** Recovery qualification, known harmful-applicability closure, and a finite cost-matched utility comparison.
17. **What should not be next?** More Boolean variants, another sweeping learning theory audit, a larger VSL, or a new autonomous curriculum.
18. **What single result would most change this assessment?** Several independently acquired states repeatedly improving useful, previously unselected later work after restart, beating the best fixed baseline at matched cost without increasing harmful applications. The independence and denominator matter more than a spectacular percentage on a selected panel.
19. **What negative result would justify a major pivot?** A properly powered, qualified net-utility test showing that the present learned-repair mechanism cannot deliver a worthwhile benefit over simple frozen alternatives once non-matches, harm and cost count. Pivot to a reliable local assistant with explicit tools/curated procedures, not another representation tuned until a benchmark turns positive. A five-history ambiguous result would not justify that conclusion.
20. **What important question have we failed to keep asking?** Whether the full system produces more correct, recoverable, user-valued work per unit cost than a simpler system—and whether its rewards are attributed to the mechanisms that actually produced that work.

**If development stopped today, the single most important demonstrated learning result** would be narrow machine-derived repair reuse. **The biggest unsupported hoped-for property** is useful, cumulative autonomous development. **The disproportionate expenditure** is the increasingly granular explanation of tiny synthetic failures after their operational implication is already clear. **The neglected component** is the integrity and withdrawal/recovery boundary around acquired state.

**What should we stop trying to prove?** That fluent self-description, activity, or a frozen model consuming persisted instructions is evidence of open-ended learning. Also stop trying to disqualify all system learning because it uses simple tables or deterministic edits.

**Are we building a learning system or an elaborate scaffold around a mostly static model?** Both, but unevenly: the foundation model remains static, the scaffold contains real adaptive mechanisms, and one narrow repair learner has earned a limited positive claim. Most of the claimed developmental trajectory is still experimental scaffolding. The next allocation of effort should test whether that small learning core produces enough safe utility to deserve a larger system around it.

## 23. Evidence index, limitations, and integrity

Major source/evidence families inspected beyond the primary links above:

* Runtime, governance and continuity: [run.py](../run.py), [snapshot manager](../app/core/snapshot_manager.py), [vector persistence](../app/lib/vector_memory.py), [September 20 architectural integrity](2026-09-20_feralecho_architectural_integrity_audit.md), [runtime identity/state preservation](2026-09-20_feralecho_runtime_identity_and_state_preservation.md), [natural learning hunt II](2026-09-29_natural_learning_event_hunt_ii.md).
* Learning/credit: [self-edit manager](../app/core/self_edit_manager.py), [reward-wire design audit](2026-09-23_riverbrain_independent_outcome_reward_wire_design_audit.md), [September 22 adversarial roadmap review](2026-09-22_codex_adversarial_attack_on_reconciled_roadmap.md), [learning synthesis](2026-09-27_learning_investigation_synthesis.md), [VSL first run](2026-09-27_verified_skill_ledger_mvk_first_run_report.md), [prospective transfer protocol](2026-09-27_vsl_prospective_causal_transfer_protocol.md), [accumulation protocol](2026-09-27_vsl_accumulated_competence_protocol.md).
* Controls/negative evidence: [AP-0 independent audit](2026-09-22_codex_ap0_independent_forensic_audit.md), [E0.1 repair](2026-09-23_rung1_e0_1_repair_and_requalification.md), [Codex qualification autopsy](2026-09-29_codex_learning_experiment_qualification_repair.md), [equality localization](2026-09-29_codex_equality_and_failure_localization.md), [feedback recoding](2026-09-29_feedback_recoding_invariance_test.md), [ordering decomposition](2026-09-29_frequency_recency_ordering_separation.md), [BA-1 collision autopsy](2026-09-29_ba1_behavioral_collision_autopsy.md), [PA-1](2026-09-29_pa1_applicability_abstraction_induction.md).
* Earlier controls: [memory ablation](2026-07-23_memory_ablation_experiment.md), [retrieval capacity](2026-09-06_retrieval_capacity_proof.md), [Architecture A](2026-09-06_architecture_A_hot_stove_proof.md), [first learning loop v1.2](2026-09-06_first_real_learning_loop_v1.2_clean_causal_transfer.md), [preference live validation](P1.2_live_validation_report.md), [C1 live validation](c1_live_validation_report.md), [RAOC pilot source](../app/experiments/raoc/pilot.py) and `memory/raoc_pilot_trials.jsonl`.
* Capability and provenance corrections: [Tier-4](tier4_confirmatory_report.md), [Tier-5 retest](2026-09-13_tier5_council_correctness_retest.md), [Tier-5 adversarial recheck](2026-09-14_tier5_retest_adversarial_audit.md), [task-type reconciliation](2026-09-15_task_type_experiment_reconciliation.md), [VECT self-falsification](2026-09-24_codex_validated_experience_transfer_self_falsification.md), [restart transfer](2026-09-27_restart_persistence_of_acquired_competence.md), [VSL final gate](2026-09-28_vsl_final_premerge_adversarial_gate.md), [Gate-3 publication](2026-09-28_gate3_execution_report.md).
* Operational and external boundaries: [Studio request lifecycle](2026-09-28_echo_studio_durable_request_lifecycle_feasibility.md), [Studio routes](../app/routes_echo_studio.py), [client](../echo_studio/api_client.py), [Breakfast Club red team](2026-09-24_operation_breakfast_club_codex_red_team.md), [relay stalemate](2026-09-24_feralecho_two_node_relay_stalemate_forensic.md), [relay semantics](2026-09-29_relay_hub_reliability_semantics_audit.md), [shadow retirement](2026-09-13_shadow_model_retirement.md).

Confidence is HIGH in the inspected source distinctions and raw recounts; MODERATE in the ranking of future work, because actual user-workload utility is precisely what remains insufficiently measured. Confidence is LOW in any extrapolation from these toy domains to open-ended development. No claim is made that every absent artifact is nonexistent outside the repository, that every report's own frozen-protocol claim was independently reverified, or that current source was loaded by the already-running process. No new p-values were searched for and no model-generated judgement was used as outcome evidence.

The source/report contradictions described here are corrections to this assessment, not edits to historical evidence. In particular: do not erase the Tier-5 improvement, the PIT3 known-transformation success, BA-3's new instrument, the valid narrow VSL acquisition, or the stronger restart result merely because a skeptical narrative is convenient.

**Closing integrity check, 2026-09-30 12:20:59 PDT:** HEAD and cached `origin/main` unchanged; branch still `vsl-implementation`, 4 ahead/0 behind; staging empty. All 739 baseline protected files and all 11 baseline tracked dirty files retained identical SHA-256 values. Echo PID 71538, watchdog 56610 and Ollama 1991 retained their recorded start times. No production/experiment source, VSL state, memory, process, or Git state was changed by this mission; no inference or experimental trial was run; nothing staged, committed or pushed.

Expanded working-tree comparison added this report, the concurrent BA-3 report, and `app/experiments/ba0_behavioral_applicability/ba4_protocol.py` plus `ba4_run.py`; no original status entry disappeared. **Only this report was created by Codex during this mission.** The BA-4 scripts are another investigator's concurrent artifacts: not modified, not executed, and not counted as a completed or qualified result. The strategic cut-off includes the inspected BA-3 evidence, not a forecast of BA-4's outcome. All report links to local evidence resolved at verification time. This report remains untracked and unstaged.

# RECOMMENDED RESEARCH PORTFOLIO

## DO NOW

1. **Qualify recovery of the actual retained-state boundary.** DIRECT EVIDENCE: current snapshot scope is partial and full-state restore evidence was not located. Success is an independently checked recoverable successor, not another backup design.
2. **Close the demonstrated harmful-application qualification gap before any expansion of active skill use.** DIRECT EVIDENCE: Skill A can damage correct code. Preserve the distinction between structural recognition, component truth, compatible edit and full correctness; use BA-3 only for the claim it measures.
3. **Run one bounded, preregistered net-utility comparison of existing Echo/retained state against competent simpler controls, once its measurement prerequisites hold.** STRONG INFERENCE: this is the highest-information strategic discriminator. Count useful success, harm, abstention, non-match, failed acquisition and total cost. No new architecture is a prerequisite by default.

## DO LATER

1. Independent prospective replication of experience-derived acquisition on unselected new material, if current retained-state use earns its cost.
2. Multi-skill retention/interference and genuinely causal acquisition-efficiency tests, if replication succeeds.
3. Outcome-grounded contextual routing and credit calibration, only after existing headroom and actual actor attribution qualify.
4. Retrieval relevance/abstention and prospective behavioral applicability, when a useful workload shows either is the limiting factor.
5. Calibrated self-prediction or independent descendant transfer, only with an externally checkable outcome and a decision consumer.

## PAUSE

* The original mixed-world autonomous learner pending its own qualification decision; do not silently substitute the different-only protocol.
* New VSL primitives, a larger skill catalogue, learned applicability architecture, relational modules and fine-tuning.
* Open-ended accumulation, self-curriculum and recursive improvement claims.
* Further invariance cohort searches without a fixed task population and a decision-changing hypothesis.
* General self-model/identity/continuity experiments and external handoff research as the main effort.
* Additional relay automation except a demonstrated operational need; core Echo must remain independent of it.

## STOP / RETIRE

* The current serial Boolean-prior diagnostic ladder as the default next mission.
* AP-0 as evidence of general acquisition, while keeping its component instruments.
* The disconfirmed seam-initiative branch and resurrection of retired shadow/unsafe authority mechanisms.
* Repeating general evaluator audits without changed code or a new integration boundary.
* Treating F2, heuristic quality, ACTIVE metadata, more stored state, or more activity as competence evidence.
* The legacy Git-push “backup” procedure as a learned-state recovery method.
* Claims that copied context or transmitted messages preserve identity or guarantee autonomous collaboration.

# IF I OWNED THIS PROJECT

I would stop commissioning one more explanation of the latest Boolean failure. It has already told us enough to stop trusting that representation pipeline as a general learner. I would preserve the evidence and stop spending the main research budget there.

I would keep the narrow repair-learning result. A system that automatically extracts a useful edit from its own failures and reuses it is worth having, even if the extractor is simple. But I would not grow its authority while its stored rule can break a correct program and its practical coverage is mostly unknown.

First I would verify that the state we care about can be recovered on a disposable successor, and settle the known harmful-application boundary. Then I would give the present system one fair, finite test on useful, independently checkable work against a strong cheaper baseline. I would count every opportunity, including no-match cases, wrong repairs, failures to acquire anything, timeouts and cost. I would not select the panel by looking for cases the ledger can already repair.

If that comparison showed a worthwhile, reproducible benefit, I would invest in independent acquisition and interference testing. If it showed no useful advantage with adequate sensitivity, I would simplify FeralEcho into a reliable local assistant with explicit tools and curated procedures. That would be a rational outcome, not a betrayal of the original project.

The ambition I would preserve is useful experience changing future ability. The assumption I would discard is that more internal machinery, more autonomous activity, or a more elaborate account of its failures moves us closer to that ambition. The next result should decide whether the small learning mechanism already present deserves to grow.
