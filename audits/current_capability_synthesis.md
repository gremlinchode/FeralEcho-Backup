# FeralEcho: Current Capability Synthesis & Tier-3 Readiness Verdict

**No Tier-3 held-out experiment was run. No held-out task material was inspected, executed, referenced, or
modified. No fine-tuning occurred. No production behavior was changed. Nothing was "improved."** This is a
reconciliation-and-decision document, built from direct re-reading of the prior evidence record, direct
re-verification of specific claims against current live state, and new, execution-based (not merely
source-read) verification of the Tier-3 apparatus itself. Where this document disagrees with a prior
document, that disagreement is stated plainly. Where evidence is ambiguous, it is left ambiguous.

---

## 1. Executive Verdict

**Echo is a mature, extensively-instrumented, routing-and-retrieval-driven conversational and
code-generation system with exactly one confirmed, causally-demonstrated content-independent behavioral
channel (C1's directive persistence), a real but narrow and statistically-marginal self-editing feedback
loop confined to target *selection* rather than content, and no confirmed autonomous content-level learning
or preference formation.** Three independent investigative threads (this session's own autonomous-fruit
audit, `echo_learning_causal_autopsy.md`, and `self_edit_closed_loop_validation.md`) converged, via
different methods, on the identical finding that `RiverBrain.learn_from_council_rating()` has been silently
dead for weeks — the single strongest piece of cross-corroborated evidence in this entire synthesis. The
Tier-3 apparatus itself is now, as of this mission, more thoroughly execution-verified than at any prior
point in this investigation (29 of 31 new execution-based checks VERIFIED, 2 explicitly left OPEN, 0
FAILED) — but its own design documents have always disclosed, and this mission independently confirms, that
its four-arm structure **cannot** isolate model diversity from council-specific orchestration, a limitation
that must shape how any future result is read, not something a clean apparatus can retroactively fix.
**Verdict: READY WITH CONDITIONS** (§9) — the apparatus is sound; the precondition that has blocked every
serious execution attempt across three separate experimental threads in this project (Ollama contention
under concurrent autonomous load) has not yet been satisfied, and satisfying it is a scientifically
material, not a merely convenient, condition.

## 2. Corrections to Prior Conclusions

Reconciliation table. `CURRENT EVIDENCE` cites the specific document(s)/live check performed
during or before this mission; `STILL TRUE?` and `CORRECTION REQUIRED?` are stated plainly, never softened.

| # | Claim | Previous Conclusion | Current Evidence | Still True? | Correction Required? | Confidence |
|---|---|---|---|---|---|---|
| 1 | `RiverBrain.learn_from_council_rating()` is a real, live, wired training-signal path | Finding 67 (2026-07-22, CLAUDE.md): "built and verified live" | **Independently re-derived three separate times**: this session's own autonomous-fruit audit (stale cursor 33471 vs. 11,970-line post-rotation log), `echo_learning_causal_autopsy.md` (identical root cause, independently reasoned, 11,602 lines at its own check time), `self_edit_closed_loop_validation.md` (identical root cause, plus a timeline tension noting the cursor's own last-update timestamp, 2026-07-26, actually *predates* the confirmed 2026-08-22 rotation by a month — meaning the mechanism may have stopped meaningfully polling even earlier, for a still-unrecovered reason) | **NO — CONTRADICTED** | Yes. Finding 67 was accurate *at the time it was written*; it has silently regressed since, and — notably — no Liveness Ledger check caught the regression (the existing `council_river_blend` check is a static source-anchor check with no data-freshness component; this is itself evidence for capability dimension #30/observability, not a new bug) | **VERY HIGH** (triple-independent convergence via three different methods) |
| 2 | Self-edit deploys succeed at a low rate ("0/37"-shaped framing used informally in earlier threads) | An earlier, informal figure implying near-total failure | `2026-09-03_self_modification_evidence_index.md` (cited, not re-derived this session): 426/463 (92%) pass the safety/import/fitness gate | **PARTIALLY — CORRECTED, THEN RE-QUALIFIED** | Yes, twice over: first upward (92% gate-pass, not near-zero), then downward in a different dimension — the fitness gate's own AST-node-count metric is confirmed saturated at a perfect score for all 25 currently-retained deploys, meaning "passed the gate" is a much weaker quality signal than the 92% headline implies on its own | **HIGH** |
| 3 | Self-editing constitutes measurable iterative quality improvement (Level 4) | Implicit in the self-edit pipeline's own design intent and framing throughout this project's history | `self_edit_closed_loop_validation.md`: n=103 real evaluated outcomes, mean quality delta **+0.103** (t=1.65, p≈0.10 — not significant), 61 improved (59.2%)/42 worsened (40.8%), and — the more important structural finding — **100% of 103 tracked outcomes targeted `coding`**, so `P(improvement \| feedback-informed target)` vs. baseline **cannot even be computed**; mean delta is statistically indistinguishable across empirical-matched/shadow-matched/neither-matched subgroups | **NO — ACTIVELY ARGUED AGAINST, NOT MERELY UNSUPPORTED** | Yes — this is Level 3 (persistent targeting adaptation), not Level 4, and the evidence gathered *argues against* Level 4 rather than simply failing to find it | **HIGH** |
| 4 | The shadow signal (Signal B, keyword-heuristic) is the system's "highest-trust" self-edit targeting input, per its own code comment | Implicit in `perform_self_edit()`'s own check-shadow-first arbitration order | `self_edit_closed_loop_validation.md`: shadow predicts the real historical target correctly in only 14/103 (13.6%) of matched readings; the empirical (RiverBrain) signal predicts it in 74/103 (71.8%) — a 5x accuracy gap in the *opposite* direction of the arbitration priority | **NO — CONTRADICTED** | Yes — "highest trust" in the source comment appears to mean "most recently/specifically proposed," a recency heuristic mistaken for a confidence ranking, not measured empirical reliability | **HIGH** |
| 5 | `model_task_stats` is "never read" (an even-more-recent, informally-stated claim this session found circulating) | Not attributable to a single named document — flagged as a live risk of confusion given `learn_from_council_rating()`'s dormancy | This session's own direct, live singleton inspection: `model_task_stats` holds real, large, differentiated data for **12 models** (e.g. `echo:latest` coding n=49,139, self_edit_coding n=7,908, echo_projects_coding n=1,282); read by `_select_council()`'s exploration floor and `TAG_SCORE_BOOST` | **NO — CONTRADICTED, AND THE MISCONCEPTION ITSELF IS WORTH NAMING** | Yes — this is precisely the confusion this synthesis exists to prevent: `learn_from_council_rating()`'s dormancy affects only ONE of RiverBrain's write pathways (`learn()` remains fully live and is the dominant contributor by volume); conflating "one pathway is dead" with "the whole structure is dead" would be a real, avoidable error | **VERY HIGH** |
| 6 | `echo_projects` is a functioning multi-file generation capability, experimentally demonstrated (capability ceiling map's original score: 4/7) | `echo_capability_ceiling_map.md`'s dimension #20, citing a real 6-file cycle and 2,535 RiverBrain observations as positive signal | Both this session's own autonomous-fruit audit and `closed_loop_capability_forensic.md` independently measured the **full historical population**: 61 real reports, 48 fail F1 entirely, 13 reach F2, **0/13 (0%) pass F2 — 0/61 overall end-to-end success**, with zero automated reader of the generated code existing anywhere by design | **NO — the prior score was too generous; `closed_loop_capability_forensic.md` itself already flagged this for downward revision (to 2-3) but explicitly did not apply it, per its own stated no-silent-rewrite rule** | **Adopting the correction explicitly in this synthesis**: score should read 2 (implemented but effectively non-functional end-to-end), not 4 | **VERY HIGH** (two independent full-population measurements agree exactly: 0/61) |
| 7 | Preference formation/retention is untested but architecturally plausible | Implicit optimism in the P1/P1.1 design phase, before any live data existed | `P1.2_live_validation_report.md`: a rigorous, pre-registered, controlled, 32-real-call live experiment. **NULL result, actively falsified at the one directly-testable point**: Echo selected label "A" in 10/10 measurements; the one genuine label-flip test showed the answer tracked the *label*, not the previously-engaged *content*. A non-Echo control showed an equal-or-stronger apparent-persistence pattern, arguing the phenomenon (where present at all) is not Echo-specific. Two confabulated, persona-laden justifications for an arbitrary choice were also directly observed | **NO — FALSIFIED, not merely unsupported** | Yes, and stated as such already by the source document itself — recorded here because it must be carried into any capability ledger, not softened into "inconclusive" | **HIGH** (single well-designed run; not yet replicated, but internally self-falsifying via its own label-flip control) |
| 8 | Persistent behavioral state/directive-following (C1) is unproven | No prior live test existed before this project's own C1 mechanism was built | `c1_live_validation_report.md`: 9 real live trials. The architectural chain (`state_existence → state_retrieval → directive_exposure`) is **100% reliable** across every trial, including correctly discriminating a near-miss invented word. Actual model compliance with an exposed directive: **75% (3/4)** — a real, measured, non-zero behavioral effect (0% baseline → 75% post-directive) | **YES — a genuinely new, confirmed capability**, distinct from and not in tension with the P2/P3 finding that no *prior* content-level learning channel existed — this is a new channel this project *built*, human-mediated by design | Adopting `echo_capability_ceiling_map.md`'s own already-recorded score of 4/7 (experimentally-demonstrated, small-N) | **MEDIUM-HIGH** (n=4 for the compliance edge specifically — small, honestly disclosed as such by the source document) |
| 9 | `ToolManager` provides real tool-use capability | Implicit in the module's existence and its wiring into prompt construction | This session's own direct grep/trace, cross-confirmed by `echo_learning_causal_autopsy.md` and `closed_loop_capability_forensic.md`: `.get_tool()` and `.func(` are called **zero times** anywhere in the live codebase; only `list_tools()` (a text-summary injection into prompts) is ever called | **NO — CONFIRMED HOLLOW FOR INVOCATION, REAL FOR EXPOSURE** | None needed beyond precision — "tool use" (score 1/7) is correctly distinguished from "tool listing/registration" (real, functioning) | **VERY HIGH** |
| 10 | Memory/FAISS retrieval measurably changes conversational behavior | Assumed by virtue of being the system's largest, most continuously-written subsystem | `2026-07-23_memory_ablation_experiment.md` (Finding 76): real embedding-distance effect statistically indistinguishable from the system's own sampling noise floor, for the `personal`-task path, n=30 pairs vs. a 5-pair noise-floor calibration. This session confirmed a follow-up attempt exists (`scripts/memory_ablation_results_nonpersonal_2026-09-03.json`, stratified across coding/creative/reasoning/general) but it contains **zero computed distance values** — incomplete, not new evidence either way | **UNKNOWN — genuinely, not resolved either direction, and the one attempt to resolve it did not complete** | The capability ceiling map's own scoring (5/7, "robustly demonstrated" for retrieval infrastructure) is accurate for the *infrastructure*; the *causal behavioral effect* remains untested outside one task type and is explicitly flagged there as the map's own #1/#4 highest-priority open question — this synthesis does not weaken or strengthen that framing, only re-confirms it is still open | **MEDIUM** (infra) / **LOW** (causal effect) |
| 11 | Curiosity/reflection/self-model/shadow-model mechanisms are "real, closed loops" | General framing across CLAUDE.md's Emergence-roadmap Findings | This session's own live checks (13,470 garden entries; 20,526 reflection-shard entries including at least one non-reflection, planning-shaped entry; 2,035 shadow-accuracy entries, freshly updated; self_model.json updated minutes before this check) confirm real, continuous, restart-durable **activity** — but `echo_learning_causal_autopsy.md`'s own, more precise framing (§7, "Ordinary-LLM equivalent") is the correct one to carry forward: every one of these mechanisms has a mundane equivalent in conventional production ML engineering (a contextual bandit router, an intent classifier, a monitored retraining loop) — none demonstrates a capability that would be surprising in an ordinary, well-engineered system | **PARTIALLY TRUE, PRECISION REQUIRED** | Downgrade the implicit framing from "closed, meaningful loops" to "real, persistent, restart-durable activity, mostly terminating at routing/selection rather than content, each with an ordinary engineering analogue" | **HIGH** |
| 12 | The current four-arm Tier-3 design isolates model diversity from council-specific orchestration | Not explicitly claimed as achieved anywhere, but implicitly assumed workable by virtue of `BASE_N` "removing diversity" | `tier3_design_preflight.md` §3 ("Is Model Diversity Actually Isolated? No.") and its own Final GO/NO-GO item #4 already state this explicitly and plainly, before this mission began | **NEVER TRUE — the design's own authors already disclosed this; this mission's Objective 6 (§8 below) re-confirms and sharpens it, it does not discover it new** | None to the design's own honesty; this synthesis's job is to make sure this limitation is not quietly dropped when results are eventually reported | **VERY HIGH** |

## 3. Current Capability Ledger

Classification key: **A** Causally demonstrated · **B** Functional, causal effect unproven · **C**
Persistence/infrastructure only · **D** Activity without demonstrated fruit · **E** Dormant/broken · **F**
Falsified/negative result · **G** Investigator-side capability, not Echo's · **H** Ambiguous.

| Capability | Class | Mechanism | Evidence | Reader/consumer | Demonstrated downstream effect | Known confounds | Confidence | What would change the classification |
|---|---|---|---|---|---|---|---|---|
| Persistent behavioral directive-following (C1) | **A** | `behavioral_state.py` → `echo_ground_truth.py` keyword-gated exposure | 9 real live trials, 100% architectural reliability, 75% (3/4) real model compliance | `echo_ground_truth.py`'s prompt construction | A real, measured 0%→75% shift in a specific real behavior | n=4 on the one probabilistic edge; single continuous-process test | HIGH | A larger-N (20+) replication holding steady near 75% would raise confidence further; a replication trending toward 0% would downgrade to B |
| RiverBrain routing (`model_task_stats` via `learn()`) | **A** | Real quality-scored writes → EMA-windowed stats → `_select_council()`/`TAG_SCORE_BOOST` reads | 12 models, up to 49,139 obs/bucket, live-unpickled this session | Council/model selection for the next deliberation | Real, demonstrated shift in which models are selected | **Terminates at selection, never content** — no model's actual output is changed by this mechanism, only whether it gets asked at all | HIGH | A retrospective correlation between `model_task_stats` state and downstream response *quality* (proposed, not run, by `echo_learning_causal_autopsy.md` §10) would establish or refute a *quality* effect, not just a selection effect |
| Self-edit target selection (Level 3) | **A** (targeting only) / **F** (quality improvement) | `reflection_shard.jsonl` → `self_model_updater.py` → `self_model.json`/`shadow_self_model.json` → `perform_self_edit()`'s arbitration | Real, persistent, restart-durable; n=103 tracked outcomes | `perform_self_edit()`'s target_task_type | Real targeting persists across restart; **quality effect actively falsified** (t=1.65, p≈0.10, 40.8% worsened) | Shadow signal empirically less accurate (13.6%) than empirical signal (71.8%) yet checked first; 100% of tracked outcomes share one target, blocking any targeting-quality contrast | HIGH | A controlled A/B/C/D arbitration experiment (proposed, not run) holding model/prompts/gates constant across real targeting variation would be the direct test |
| `RiverBrain.learn_from_council_rating()` | **E** | Council rating → `is_council_trusted()`-gated blend → `model_task_stats` | Stale cursor (33,471) vs. post-rotation log (11,970 lines) — silent, no-exception stall | None currently reached | None currently | Triple-independently confirmed root cause; timeline tension (cursor stopped ~1 month before the confirmed rotation) not fully resolved | VERY HIGH (dead) / MEDIUM (exact original trigger date) | A repaired cursor + one polling cycle showing `council_ratings.jsonl` growth again would confirm the fix; the real magnitude of its downstream effect on `model_task_stats` would still need separate measurement |
| Preference formation/retention | **F** | Forced-choice name task, formation→immediate→distractor→retention sequence | 32 real live calls, 10/10 label-A selections, direct label-flip falsification, non-Echo control showing an equal-or-stronger pattern, 2 confabulated justifications observed | N/A — negative result | N/A | Position/label bias is the dominant, best-supported explanation; single continuous session cannot in principle distinguish genuine retention from in-context momentum (the design's own disclosed ceiling) | HIGH | A redesigned task structurally decoupling position from the forced-choice mechanism (proposed, not run) is the one concrete follow-up that could change this without re-litigating the same confound |
| `ToolManager` tool invocation | **E** | `.get_tool()`/`Tool.func()` call chain | Zero real callers anywhere in the codebase (direct grep, cross-confirmed by two independent audits) | N/A | N/A | Registration + `list_tools()`-based prompt exposure IS real and live — only invocation is dead | VERY HIGH | Wiring one real invocation call site and observing a real tool call in `interaction_log.jsonl` |
| `ToolManager` tool listing/exposure | **C** | `list_tools()` → prompt injection | Real, live, task-type-gated | Real conversational system prompt | Text appears in real prompts; no evidence any conversation's outcome depended on it | Cosmetic exposure with no functional backing behind it | HIGH | Any evidence a model's response changed *because* a specific listed tool was named, absent the tool ever being called |
| `echo_projects` end-to-end generation | **D** | Council plan → per-file generation → F1 → F2 → report | 61 real historical attempts, 48 F1-blocked, 13 reach F2, **0/13 F2-pass** | Human (report only); zero automated code reader exists, by design | None | Real, repeated, non-trivial compute expenditure with a clean null outcome — could reflect model-class ceiling or task/prompt design; not disambiguated | VERY HIGH (0/61 measurement) / LOW (cause) | A human-authored failure-mode taxonomy across all 61 reports, or a retry with a different model pool, would distinguish "model ceiling" from "fixable prompt/gate calibration" |
| Memory/FAISS retrieval (infrastructure) | **C** | `memory_bridge.py`'s real similarity search | 123,793 entries, live, continuously written | `retrieve_relevant_memories()` → real conversational prompts | Real content genuinely reaches real prompts | 48.4% of the entire store is confirmed-excluded `code_analysis` contamination (now frozen, not growing, per a live fix this session) | HIGH | N/A for this dimension — infrastructure reality is not in question |
| Memory/FAISS retrieval (causal behavioral effect) | **H** | Same mechanism, judged on outcome not existence | One completed ablation (personal-task, temp>0): indistinguishable from noise floor. One incomplete follow-up (non-personal, stratified): zero computed distances | N/A | **Not established either direction** | Sampling-temperature noise was not controlled in the completed study; the follow-up never finished | LOW-MEDIUM | A completed temp=0 ablation across all 5 task types (proposed by the capability ceiling map as its own top-ranked intervention) |
| Curiosity engine / garden | **B** (real, mechanistic) / ordinary-analogue framing applies | `garden_manager.py` → `emergent_scheduler`/`echo_projects` reads | 13,470 real entries; two demonstrated real readers this session | Next autonomous prompt/project spec selection | Real, mechanical selection-shifting; **not shown to reflect genuine "interest" vs. scheduling artifact** (per `2026-09-03_measurability_and_longitudinal_evidence_audit.md`, cited not re-derived) | Category distribution may reflect scheduling code, not emergent preference | MEDIUM | A controlled comparison of garden-driven vs. randomly-selected prompts on some downstream quality/coherence metric |
| Reflection cycle / shards | **D** (mostly) / narrow **B** (Global Workspace link) | `reflection_shard.py`'s real model-generated text → `memory/reflection_shard.jsonl` → (since Finding 78) Global Workspace publish | 20,526 real entries; `echo_learning_causal_autopsy.md` independently confirmed the journal's own accessor functions have zero external callers; this session independently confirmed a live Global Workspace consumption event exists in general (not traced to this specific source) | Global Workspace wide-broadcast (confirmed live); the plain journal itself — no confirmed reader | Real text generation; downstream consequence limited to the Global Workspace link, and even that link's specific consumption was not traced end-to-end this session | Free-association content, not outcome-grounded introspection (confirmed by direct source read) — a real risk of "reflection" being read as more meaningful than it is | HIGH (mechanism) / MEDIUM (any downstream effect) | Tracing one real `reflection.meta_synthesis` event through to a specific changed downstream decision |
| Self-model (`self_model.json`) | **B** | `self_model_updater.py`'s 130s-timer writer → `echo_ground_truth.py`'s reader | Fresh (minutes-old) at every check this session | Real conversational system prompts, when introspective keywords trigger | Real content reaches real prompts | No check performed this session on whether the *content* changes anything beyond being present in the prompt | MEDIUM-HIGH | Evidence that a specific `self_model.json` field's value, not just its presence, changed a response |
| Shadow self-model / shadow accuracy | **B** | `shadow_model.propose_from_reflection()` → `shadow_self_model.json`/`shadow_accuracy.jsonl` | 2,035 real entries, freshly growing; directly confirmed to causally affect real self-edit targeting on at least one occasion (per `self_edit_closed_loop_validation.md`) | `perform_self_edit()`'s arbitration (checked first) | Real, demonstrated: overrides empirical signal when present, despite the empirical signal being 5x more historically accurate | Pure keyword-count heuristic, not semantic inference (confirmed) — real but shallow | HIGH | The proposed A/B/C/D arbitration experiment would show whether this override has any real quality consequence, positive or negative |
| Global Workspace publish/consume | **A** | 6+ real publishers → `workspace_log.jsonl` → real consumers (`river_deliberation`'s `exploration_bias`) | This session: 6 distinct real sources in a 500-event window; one directly-observed live `workspace.consumed` event (`exploration_bias=0.001`) | A real Bernoulli gate in `_select_council()` | Real, small-magnitude (p=0.001 observed), demonstrated causal effect on council-slot composition | Magnitude is genuinely small at the moment observed; not measured over a longer window | HIGH | A longer observation window computing the realized rate of actual council-slot swaps attributable to this gate |
| Crash avoidance (`crash_awareness.py`) | **A** | Real crash detection → temporary `mlx:*` pool exclusion → `list_mlx_models()` | 14 real log occurrences this project's history | Every real council selection during the cooldown window | Real, repeated, demonstrated composition change | None of significance found | HIGH | N/A — already the cleanest confirmed case in this ledger |
| Dissent Log | **D** (effectively unused) | `propose_core_edit()`'s council review → `dissent_log.jsonl` | 1 entry, ever, dated 2026-07-17 | Human review only (by design, `!propose`-invoked) | None since its single historical use | By-design human-invoked-only; absence of use is not itself a defect | HIGH | Any second real invocation |
| Goal persistence (`goals.txt`) | **E** | A static, 3-line file | Zero live references anywhere; last touched 2026-07-04 | None | None | The curiosity garden is this project's real functioning analogue; `goals.txt` is a separate, wholly inert artifact | HIGH | N/A |
| Tier-3 apparatus itself (as a capability of the *investigation*, not of Echo) | **G** | Budget-matched 4-arm design, execution-verified this session | 29/31 new execution checks VERIFIED, 0 FAILED, 2 OPEN | The investigators (human + Claude) | The apparatus can now correctly attribute truncation, pin models, anonymize identity, block RiverBrain contamination, and gate held-out access | Cannot isolate model diversity from council orchestration (disclosed by its own design, re-confirmed here); Ollama contention remains the dominant practical risk | HIGH | Running the held-out set (not done here) |
| Investigative/scientific rigor generally | **G** | The whole multi-month audit corpus this synthesis reconciles | Dozens of independent, cross-corroborating documents, several with contradictory-then-reconciled claims explicitly tracked | This document, future sessions | Real, demonstrated improvement in the reliability of THIS PROJECT'S OWN CLAIMS about Echo, not in Echo itself | This is the investigators' rigor, explicitly flagged as such by `echo_capability_ceiling_map.md`'s own dimension #29 — must never be conflated with Echo's own capability | HIGH | N/A |

## 4. Autonomous Fruit Ledger (stress-tested)

This section re-examines this mission's immediately-prior `autonomous_fruit_forensic_audit.md` as a hypothesis
under adversarial scrutiny, per Objective 3's explicit instruction. Full per-item causal-chain detail
(trigger→output→persistence→reader→consumer→downstream change→repeatability) is unchanged from that report
and not restated in full here; this section adds the stress test and the requested quantification.

**Stress test result: the prior audit's classifications survive scrutiny, with one sharpening.** Re-checking
each claimed FRUIT item against the stricter repeatability bar:

- **Crash avoidance — FRUIT, confirmed repeatable.** 14 independent log occurrences across this project's
  history is genuine repeatability, not a single lucky observation. Survives stress-testing.
- **RiverBrain `model_task_stats` routing — FRUIT for *selection*, re-confirmed and sharpened by
  `echo_learning_causal_autopsy.md`'s more precise framing: it is causally real but structurally incapable of
  affecting response *content*.** The prior audit's own text already noted the `choose_model()` primary-rank
  limitation; this synthesis adopts the causal autopsy's sharper articulation of the same point.
- **Global Workspace exploration-bias consumption — FRUIT, but re-examined magnitude is genuinely small**
  (`p=0.001` observed once). Repeatability across a longer window was not established in either this
  session or the prior audit — downgrading confidence in the *magnitude* claim from HIGH to MEDIUM while
  leaving the *mechanism-is-real* claim at HIGH.
- **Curiosity-garden → `echo_projects` spec — re-examined against `2026-09-03_measurability_and_longitudinal_
  evidence_audit.md`'s finding (cited, not independently re-derived) that apparent curiosity-category drift
  is more parsimoniously explained by scheduling/persona code than by emergent interest.** This does not
  overturn the causal chain itself (a real garden question does become a real project spec, repeatably,
  confirmed by direct trace this session) — but it downgrades the *interpretive* framing from "the system
  chooses what interests it" to "a real, mechanical selection process feeds a real downstream consumer,"
  which is a materially weaker and more accurate claim. Reclassified from the prior audit's POTENTIAL_FRUIT
  to a stricter **ACTIVITY-with-a-real-mechanical-link**, not withdrawn as a finding, but its strength
  reduced.
- **`echo_projects`'s own generated code — DEAD/ACTIVITY, unchanged and now doubly confirmed** (this session
  and `closed_loop_capability_forensic.md` independently converge on 0/61).

**Quantification** (evidence permits partial, not complete, computation — stated honestly where a number
cannot be produced):

| Metric | Value | Basis |
|---|---|---|
| Autonomous events observed (proxy: `interaction_log.jsonl` entries in one directly-observed hour) | 53 | Direct count, this session |
| Verified fruitful events in the same window | **Not separately countable** — FRUIT-classified mechanisms (crash avoidance, exploration-bias consumption) do not fire once per interaction_log entry; they fire on their own, much rarer triggers (crash clusters; a probabilistic gate) | Stated as a genuine measurement gap, not estimated |
| Fruit rate (fruitful / total autonomous events) | **Cannot be computed from available data** — no single accounting unit spans both the numerator (rare, mechanism-specific triggers) and the denominator (per-interaction volume) | Honest non-computation, per the mission's own instruction against manufactured denominators |
| Activity-to-fruit ratio, by volume proxy | **Heavily activity-dominated**: `echo_projects`'s 61 real, expensive cycles (0 fruit) vs. crash avoidance's 14 real occurrences (fruit) illustrates the shape, without collapsing to one ratio | Direct counts, both this session |
| Approximate compute/resource burden | 53 real Ollama-touching entries/hour observed; swap at 5.6/7.0GB used at time of check; `qwen2.5-coder:7b` (5.0GB) resident and 100% GPU-utilized at check time; multiple concurrent autonomous deliberation loops directly observed in the same ~5-minute window | Direct measurement, this session |
| Strongest fruit per unit resource | **Crash avoidance** — fires only on real crash clusters (rare), each occurrence cheap (a pool-exclusion decision, no extra inference), with a clean, repeatable, real downstream effect | Qualitative ranking, not a computed ratio (no shared unit exists between "crash count" and "compute cost") |
| Largest resource sink with no demonstrated fruit | **`echo_projects`** — 61 real cycles, each involving a real multi-model council-planning deliberation, N real per-file generations, and a real 3-model council review (a materially larger per-cycle compute footprint than almost anything else in this ledger), 0/61 useful output | Direct measurement, this session and independently by `closed_loop_capability_forensic.md` |

**Frequency was not equated with value anywhere in this section** — `emergent_loop`'s 326 real workspace
events (the single largest source in the 500-event sample) is the highest-frequency mechanism in the whole
audit and is classified no higher than ACTIVITY/narrow-FRUIT on its own merits, exactly matched to what was
actually demonstrated, not to how often it fires.

**What should be preserved for experimentation**: crash avoidance (cheap, real, safety-relevant, orthogonal
to any Tier-3 measurement); RiverBrain `learn()`'s routing signal (real, needed for any council-selection
fidelity a Tier-3 `ARCH_COUNCIL` arm would want to reflect); Global Workspace publish/consume (cheap,
already-instrumented, no reason to disable).

**What should be throttled** (for the specific, temporary purpose of a Tier-3 measurement window, not as a
permanent recommendation): `AutonomousSelfEdit` and `model_guided_autonomous_loop` — both directly observed
this session running full, multi-minute, multi-councillor deliberation cycles concurrently, the single
largest concurrent-demand source on the same Ollama queue Tier-3 needs exclusive/low-contention access to;
`echo_projects`'s autonomous 6h cycle — the single largest confirmed no-fruit compute sink, cheap to pause
for a bounded window without risking any confirmed-real mechanism.

**What should merely be instrumented, not touched**: the curiosity garden and reflection-shard write paths
(cheap, already real, no reason to interfere, but worth a lighter-weight freshness/drift check per
`echo_learning_causal_autopsy.md`'s own observability finding); `learn_from_council_rating()` — instrument
(a regression test computing `interaction_log_line_count − cursor_position`, alerting if negative) before
even considering a repair, so a future silent regression of the *same* class is caught automatically.

**What should eventually be repaired or removed** (not now, not by this mission): the stale council cursor
(a ~5-15 LOC fix per `self_edit_closed_loop_validation.md`'s own proposal, not implemented); the
shadow-over-empirical arbitration priority inversion (same document's Fix A, also not implemented, and
explicitly requiring its own controlled A/B/C/D validation before being trusted); `ToolManager`'s
zero-invocation gap (a genuine wiring question, not evaluated for cost/benefit here).

## 5. Resource/Fruit Analysis

Restated from §4 with the explicit framing the mission requires: **resource cost is not equated with lack
of value.** Crash avoidance and the RiverBrain routing signal are real, demonstrated fruit that cost very
little to sustain. `echo_projects` is real, demonstrated *activity* at real, substantial cost, with zero
demonstrated fruit — this is reported as a cost/fruit mismatch specifically for that one mechanism, not as
a verdict on the autonomous workload as a whole. The autonomous workload in aggregate is neither cheap nor
free of real value; it is a mixed picture, reported as such.

## 6. Recommended Experimental Operating Profile

Four options evaluated against the specific axes the mission specifies. "Best for Echo in production" and
"best for scientifically measuring Echo" are kept explicitly separate, per the mission's own instruction.

| Option | Contamination risk | Ollama contention | Swap/memory pressure | Reproducibility | Ecological validity | Risk of suppressing a genuinely important mechanism | Expected information gain |
|---|---|---|---|---|---|---|---|
| **1. FULL_AUTONOMY** (run Tier-3 alongside every autonomous loop, unmodified) | Low for the held-out data itself (isolation proxy already verified this session to block RiverBrain/memory writes) | **HIGH** — directly, repeatedly measured across three separate experimental threads in this project's history (this Tier-3 pilot's own remaining-blockers investigation; the self-edit Level-4 experiment's own inability to complete a prospective test for the identical reason) | HIGH — swap already at 5.6/7.0GB used under ordinary current load, before adding Tier-3's own demand | LOW — per-candidate wall-clock time becomes unpredictable and contention-dependent, making a future replication attempt hard to compare against this run | HIGHEST — this is literally how the system runs day to day | LOWEST | LOW-MEDIUM — real risk that `INFRASTRUCTURE_FAILURE` exceeds the design's own pre-registered 15% override threshold, producing an inconclusive-pending-infrastructure result regardless of the substantive numbers |
| **2. THROTTLED_AUTONOMY** (pause/throttle only the two heaviest, no-fruit-implicated loops — `model_guided_autonomous_loop` and `echo_projects`'s 6h cycle — leave everything else, including crash avoidance and RiverBrain's live routing, running) | Low, same isolation proxy | MEDIUM — removes the two loops directly observed running full multi-councillor cycles concurrently with this session's own checks, without eliminating all background demand | MEDIUM | MEDIUM | HIGH — the system is still substantively "itself," just without its two heaviest, currently-zero-fruit consumers | LOW — both throttled mechanisms are exactly the ones this synthesis found weakest on fruit | MEDIUM-HIGH |
| **3. EXPERIMENT_WINDOW / LOW_CONTENTION_MODE** (a scheduled window where all autonomous loops are paused for the duration of the held-out run only, resumed immediately after) | Low, same isolation proxy | **LOW** — directly addresses the confirmed dominant practical blocker | LOW | **HIGH** — a controlled, comparable window is exactly what makes a future replication meaningful | MEDIUM — the system is measured in a state it does not normally occupy | MEDIUM — a temporary pause of everything, including the demonstrated-real crash-avoidance and routing mechanisms, for a bounded window is a real, if small and reversible, cost | **HIGHEST** — the cleanest, most interpretable data this apparatus can produce |
| **4. PAUSED_AUTONOMY** (a longer-term, not-just-experiment-scoped pause) | Low | LOW | LOW | HIGH | LOW | **HIGH** — this is not scoped to the experiment and risks suppressing real, demonstrated mechanisms (crash avoidance, routing) for no measurement benefit beyond what option 3 already provides | Same as option 3, no additional gain, at a materially higher and unjustified cost |

**Recommendation: Option 3, EXPERIMENT_WINDOW / LOW_CONTENTION_MODE, scoped strictly to the duration of the
held-out run.** This is not the most convenient option (it requires deliberately coordinating a pause/resume
around the actual execution, not simply "running it whenever"), and it is explicitly **not** a recommendation
to suppress autonomy in production — the moment the held-out run completes, full autonomy should resume
exactly as before. **What is best for Echo in production (full, continuous autonomy, including the real,
demonstrated crash-avoidance and routing mechanisms) is different from what is best for measuring Echo
cleanly (a bounded, low-contention window) — this synthesis explicitly does not conflate the two, and does
not recommend option 3 as a standing operating mode.**

## 7. Tier-3 Apparatus Verification

Executed this mission, via `scripts/verify_tier3_apparatus_readiness_audit.py` (new; no held-out task
touched; no live Ollama call made anywhere in the script). **29 of 31 checks VERIFIED by direct execution,
2 explicitly marked OPEN, 0 FAILED.** Full machine-readable results:
`audits/tier3_apparatus/readiness_verification_results.json`.

| Property required by Objective 5 | Result | How verified |
|---|---|---|
| Equal `max_tokens` | VERIFIED | Direct constant read (`MAX_TOKENS=2048`) + source-grep of all 4 real call sites, cross-checked against direct function reads |
| Equal call budgets (`BASE_N` vs. `ARCH_COUNCIL`) | VERIFIED | `N_BASEN+1 == 4 == ARCH_COUNCIL`'s real `DEFAULT_COUNCIL_SIZE(3)+1`, confirmed by direct source read |
| `BASE_1` implementation | VERIFIED | Direct `inspect.getsource()` read, confirmed structurally distinct from the other 3 arms |
| `BASE_N` implementation | VERIFIED | Same, plus direct execution confirms its own attempt loop is a fixed-N, disclosed construct, not a hidden retry |
| `ARCH_PIPELINE` implementation | VERIFIED | Direct source read of `generate_code_from_plan()`, the real function this arm calls |
| `ARCH_COUNCIL` implementation | VERIFIED | Direct source read of `deliberate_and_learn()`, the real function this arm calls |
| Model pinning across the entire experiment | VERIFIED | Live execution: patched `install_model_pin()` with a fake sentinel model, called the REAL `self_edit_manager.choose_model()`, confirmed it returned the sentinel |
| **Interception of Pipeline's internal model selection** | VERIFIED | Same live execution as above — this is the exact interception point `generate_code_from_plan()` depends on |
| **Interception of Pipeline's internal RiverBrain writes** (a new, previously-unexecuted check this mission specifically surfaced) | VERIFIED | Live execution: confirmed `self_edit_manager.get_river_brain()` (the actual function `generate_code_from_plan()` calls at 3 real call sites, via a late, call-time import) correctly resolves through `install_isolation()`'s patched `echo_model_orchestrator.get_river_brain` — object-identity-confirmed against both a synthetic fake proxy and the real, live isolation proxy. **This specific check did not exist in any prior mission's own verification pass** — prior passes verified `choose_model()` interception for this call path, not `get_river_brain()` interception, leaving a real, previously-unclosed gap in how confidently "no RiverBrain contamination from ARCH_PIPELINE" could be claimed before this session |
| Synthesis prompt equivalence | VERIFIED | Direct diff: real template 29 non-blank lines, `BASE_N`'s 19, 3 shared verbatim — a genuine, disclosed, structurally-mirrored rewrite |
| Anonymization | VERIFIED | Live execution: patched the real `_format_opinions()`, fed it real model-name keys, confirmed the rendered output contains zero real model-name substrings and correct `[Attempt N]` labels; confirmed the patch restores cleanly afterward |
| Randomized arm ordering | VERIFIED | Live execution across 25 seeds × 2 development tasks: deterministic given `(seed, task_id)`, 16/16 distinct orderings for each task (non-degenerate), independent per task |
| Task randomization (held-out set) | **OPEN** | No held-out task suite exists yet — this property is not yet instantiable; explicitly not assumed either way |
| Truncation classification | VERIFIED | Full 23-case suite from this mission's own Objective-1 repair re-run fresh, exit code 0 |
| Infrastructure-failure classification | VERIFIED | Live execution: real `_classify_exception()` called against synthetic `TimeoutError`/`ConnectionError` (both correctly → `INFRASTRUCTURE_FAILURE`) and `ValueError` (correctly → a different class) |
| Objective sandbox scoring | VERIFIED | Direct source read confirms `objective_verify()` receives no arm/condition label; live execution ran one real correct and one real incorrect trivial function through the actual kernel sandbox, both scored correctly |
| No hidden retries | VERIFIED (3 arms) / **OPEN** (ARCH_PIPELINE's own internal function) | Direct source read of all 4 arm functions found no retry/while-loop construct beyond `BASE_N`'s disclosed fixed-N loop; whether `generate_code_from_plan()` itself (production code) contains any internal retry was resolved by static reading only (it does not; the real single-retry mechanism lives in the separate `execute_self_edit()`, which this harness never calls) — not additionally confirmed by a live execution trace, so marked OPEN rather than VERIFIED per the mission's own instruction |
| No production-memory contamination | VERIFIED | `install_isolation()`'s `log_interaction`/`save_reflection`/`_log_council_deliberation` no-ops confirmed by source read; the harness's own results are written only to `audits/tier3_apparatus/`, never to any live `memory/*.jsonl` |
| No RiverBrain learning contamination | VERIFIED | See the interception check above — the highest-value new verification this mission performed |
| No `model_task_stats` contamination | VERIFIED | Same mechanism — `learn()`/`save()`/`learn_from_sandbox_outcome()`/`learn_from_council_rating()` are all proxy-blocked, confirmed by live execution, not just source read |
| No held-out access | VERIFIED | `HELD_OUT_MANIFEST_PATH` confirmed absent; `assert_development_task_only()` executed live against both a valid dev task and an invalid one, and against a simulated held-out manifest (confirming precedence over the dev allowlist) |
| Frozen task-suite integrity | VERIFIED | Live SHA-256 recomputed this session, matches the constant in source exactly |

**Everything marked OPEN is marked OPEN deliberately, not softened into VERIFIED.**

## 8. Hypothesis Boundaries

**What Tier-3, as currently designed, CAN establish**: whether council's real, combined mechanism, at a
genuinely token-and-call-matched budget against a same-model self-consistency baseline, produces a
detectable pass-rate advantage on frozen, mechanism-untuned held-out single-function coding tasks (the
`ARCH_COUNCIL` vs. `BASE_N` comparison); separately, whether self-edit's own real prompt framing helps at an
honestly equal single-call budget (`ARCH_PIPELINE` vs. `BASE_1`).

**What it CANNOT establish, even after every disclosed repair**:

- **H4, examined with the care the mission demands**: the current four-arm design does **not** isolate
  model diversity from council-specific orchestration. `BASE_N` removes diversity (one model, self-consistency)
  but also uses that one model's own synthesis mechanism; `ARCH_COUNCIL` has both diversity (3 different
  models) *and* council's specific selection/synthesis apparatus, changing simultaneously. **If
  `ARCH_COUNCIL` beats `BASE_N`, the strongest claim this experiment can support is: "council's real,
  combined package — diversity plus its specific orchestration, considered together — beats a budget-matched
  single-model baseline."** The experiment **cannot** support the narrower, more specific claim "council's
  *orchestration/synthesis mechanism itself* is the active ingredient, independent of model diversity" — that
  would require a fifth arm (e.g., 3 diverse models' single attempts, synthesized via `BASE_N`'s own neutral
  template, or conversely one model's N attempts synthesized via council's real synthesis template) that does
  not exist in the current design and was not built in this mission. This limitation was already disclosed by
  the design's own preflight audit before this mission began (`tier3_design_preflight.md` §3, Final GO/NO-GO
  item #4); this mission's contribution is confirming it remains true of the *repaired* code and stating it
  with the precision the current mission specifically demands.
- Whether any result generalizes beyond single-function coding tasks to decomposition-heavy, multi-file
  domains (`echo_projects`' own actual domain, where the current pilot's own evidence — 0/61 — suggests real,
  independent limits exist regardless of what Tier-3 finds on simpler tasks).
- Anything about learning, self-improvement, generalized capability (Level G, per the design's own 7-level
  framework), consciousness, or emergent capability beyond this specific, bounded, budget-matched comparison.

**Effect sizes and uncertainty, not p-values alone**: the design's own pre-registered interpretation rules
(§21/§22 of `tier3_architecture_vs_model_design.md`) already specify a ≥25-percentage-point paired advantage,
not a bare significance threshold, as the bar for a positive H1 read — this synthesis explicitly endorses that
choice and explicitly warns against the single most common statistical misreading available here: **"not
statistically significant" must not be silently converted into "no difference exists."** At the design's own
disclosed pilot scale (n=8/arm on the held-out set), the design's own authors already predicted the most
likely honest outcome is AMBIGUOUS (insufficient power to resolve at the pre-specified effect size) — this is
a valid, anticipated outcome requiring the confirmatory sample size, not a failure of the pilot.

**Strongest claim the current experiment can support, stated in one sentence**: *"Whether FeralEcho's real,
combined council package — diversity and orchestration together, exactly as it exists in production — beats
a budget-matched, same-model self-consistency baseline on frozen, held-out, single-function coding tasks."*
**Claim it cannot support, stated in one sentence, to guard against the single most likely overreach**:
*"Whether council's specific orchestration/synthesis mechanism, independent of having multiple different
models available, is what makes any observed advantage happen."*

## 9. Readiness Verdict

# READY WITH CONDITIONS

The apparatus itself is sound: three prior repair/preflight passes (B1-B3, M2-M6, the truncation-attribution
repair) plus this mission's own 29/31-execution-verified audit constitute the most thoroughly checked state
this design has ever been in. The remaining conditions are scientifically material — each is tied directly to
a specific, previously-demonstrated failure mode in this project's own history, not invented to make the
experiment artificially harder to run:

1. **A genuine low-contention execution window must be secured before the held-out run begins** (per §6's
   recommended operating profile). This condition exists because Ollama/resource contention has directly,
   repeatedly blocked or degraded serious execution attempts across at least three separate threads in this
   project's history (this Tier-3 pilot's own remaining-blockers investigation; the self-edit Level-4
   prospective test's own inability to complete for the identical reason; multiple earlier sanity-run stalls).
   The design's own pre-registered H5 override rule (>15% `INFRASTRUCTURE_FAILURE` → inconclusive regardless
   of substantive numbers) exists specifically because of this risk and should be enforced exactly as written.
2. **8 real, frozen held-out tasks must exist and be hashed before any generation begins** — they do not yet
   exist (re-confirmed this mission). Authoring them is a real, undone piece of work, not a formality.
3. **The `BASE_N` synthesis step must be sanity-checked on the 2 development tasks first**, per the design's
   own protocol step 3 — this mission's execution-based verification confirmed the synthesis *template* is
   genuinely distinct and structurally sound, but has not observed it produce a real, non-degenerate result
   against genuine same-model attempts on a real task (the currently-running/completed development-sanity data
   was produced entirely under the pre-repair code, per this mission's companion truncation-repair report).
4. **Any eventual report of results must explicitly state the H4 boundary from §8** — that a council win
   supports only the bounded "combined package" claim, never "orchestration specifically" in isolation — as a
   condition of interpretation, not merely a footnote.
5. **No production change, no autonomy repair (the stale cursor, the arbitration priority), and no fine-tuning
   should be bundled into or precede this run** — each is a real, separately-proposed, separately-testable
   change per §§2-4, and conflating any of them with the Tier-3 measurement would reintroduce exactly the kind
   of confound this whole design exists to avoid.

None of these five conditions was added to make the experiment artificially harder to run; each traces to a
specific, already-demonstrated risk in this project's own recorded history.

## 10. Highest-Information-Gain Next Experiment

Compared honestly against the named alternatives, using expected information gain and discriminating power
between the live competing explanations (not excitement or sunk cost):

- **(A) Tier-3 as currently designed**: uniquely positioned to answer a question **no other existing evidence
  in this entire corpus bears on at all** — whether architecture contributes anything beyond raw compute/
  diversity, at a controlled budget, on a genuinely held-out task set. Every other finding in this synthesis
  (self-edit targeting, council-cursor, ToolManager, `echo_projects`, C1, preference formation, memory
  retrieval) is orthogonal to this specific question, per `tier3_architecture_vs_model_design.md`'s own
  evidence matrix, independently re-confirmed by this synthesis's own reconciliation in §2. Marginal
  engineering cost remaining is now low (design + two repair passes + this mission's execution audit are
  already done); marginal *resource* cost is real and non-trivial (an estimated 1-4+ hours of contended-queue
  wall-clock time across 32 real generation candidates, per this project's own historical per-candidate
  timing).
- **(B) Additional autonomy investigation**: largely completed by this mission's own §4 stress-test and the
  immediately-prior autonomous-fruit audit — further investigation here would have low marginal information
  gain relative to what has already been extracted, absent a specific new hypothesis to test.
- **(C) A new learning experiment**: P1.2 already delivered a clean, well-powered, self-falsifying null result
  for preference formation specifically; a *content-level* learning question broader than preference (e.g.,
  a differently-designed task) remains conceptually open but has no currently-designed apparatus, meaning this
  option would require substantial new engineering before producing any data at all — a materially higher
  up-front cost than (A) for a question this synthesis's own capability ledger already scores as having a
  hard, disclosed architectural ceiling (no candidate-preference data structure exists anywhere in this
  codebase, per `echo_capability_ceiling_map.md`).
- **(D) Self-edit Level 4 experiment**: its own retrospective evidence (n=103, t=1.65) already argues fairly
  clearly against Level 4; a prospective, adequately-powered confirmatory test was already attempted and could
  not complete, for the **identical** resource-contention reason blocking Tier-3 — meaning (D) requires the
  same operating-profile precondition as (A) without offering comparably unique discriminating power (its
  central question, "does feedback improve self-edit quality," already has a fairly clear negative-leaning
  answer; Tier-3's central question has essentially no prior answer at all).
- **(E) Another targeted causal experiment — specifically, the memory-retrieval ablation at temperature=0
  across all 5 task types**, independently ranked by `echo_capability_ceiling_map.md` as one of its own top
  interventions, and the single largest genuinely open causal question about the system's single largest
  subsystem. This is a real, close competitor to (A): lower resource cost (no held-out set to author, no
  32-candidate multi-arm run, reuses an existing ablation script's design), and it resolves an
  **independently important** question this synthesis's own §2/§3 confirms is still fully open (memory's
  causal effect, class **H**/ambiguous throughout this document). It does not, however, bear on the
  architecture-vs-model question at all — it is a genuinely different axis of uncertainty, not a cheaper
  substitute for (A).
- **(F) Something else discovered during this mission**: the stale council-cursor repair (§2/§4), while cheap
  (~5-15 LOC) and already-scoped by `self_edit_closed_loop_validation.md`, is explicitly **not** a
  high-information experiment on its own — it is a plausible fix whose *effect*, if any, would still need
  the same kind of controlled before/after measurement this whole synthesis has been arguing for throughout,
  not a substitute for one.

**Recommendation**: **(A), Tier-3 as currently designed, run under the Option-3 (EXPERIMENT_WINDOW) operating
profile from §6, is the single highest-information-gain experiment available**, because it is the only
option targeting a question with essentially zero prior discriminating evidence in this entire corpus, its
apparatus is now the most thoroughly verified it has ever been, and its marginal engineering cost is lower
than any alternative except (B), which has already been substantially extracted. **(E), the memory-retrieval
ablation at temperature=0 across all task types, is the strongest genuine runner-up** and — notably — could
plausibly be run in the *same* low-contention window as (A), since it uses a different task pool and does not
compete with Tier-3 for the same held-out data; this is named as a real efficiency opportunity, not a
requirement.

## 11. Exact Next-Step Protocol (not executed in this mission)

1. Author and freeze 8 new held-out tasks spanning bug-fixing, concurrency/stateful reasoning, algorithmic
   edge cases, and refactoring, per `tier3_architecture_vs_model_design.md` §20 step 1; hash the frozen set
   immediately.
2. Secure a genuine low-contention execution window (Option 3, §6): pause `model_guided_autonomous_loop` and
   `echo_projects`'s autonomous cycle for the duration of the run only; leave crash avoidance and RiverBrain's
   live routing running.
3. Confirm the pinned model (already persisted in `audits/tier3_apparatus/pinned_model.json` from this
   project's prior sessions) is still the intended choice, or re-pin deliberately if not.
4. Run all 4 arms on the 2 development tasks first (task_11/task_12) under the **repaired** code
   (this mission's truncation fix), confirming a sane, non-degenerate `BASE_N` synthesis result before
   touching held-out data — the existing `dev_sanity_results.jsonl` records from the pre-repair process do
   not satisfy this step; a fresh run under the repaired script is required.
5. Run all 4 arms on the 8 held-out tasks, in the randomized order `randomized_arm_order()` produces per task,
   with pre-batch telemetry recorded each time.
6. Score every candidate via the existing `objective_verify()` + the repaired `classify_result()`; tag
   `INFRASTRUCTURE_FAILURE`/`GENERATION_TRUNCATED`/`TASK_LOGIC_FAILURE`/`PASS` per the pre-declared rules,
   preserving the internal `truncation_evidence_type` audit trail this mission's Objective-1 repair added.
7. Independently spot-check at least 20% of verdicts (stratified, at least 1-2 per arm) against raw text
   before analysis.
8. Unblind, compute the paired comparisons (`ARCH_COUNCIL` vs. `BASE_N`; `ARCH_PIPELINE` vs. `BASE_1`), apply
   the pre-registered ≥25pp effect-size threshold and the H5 (>15% infrastructure-failure) override rule, and
   report once — with the §8 hypothesis-boundary language included verbatim in that report, not summarized
   away.
9. Resume full autonomy immediately after step 8 completes.

**This protocol is not executed by this mission.**

## 12. Open Uncertainties

- The exact original trigger date/cause of `learn_from_council_rating()`'s stall (the cursor's own last
  update, 2026-07-26, predates the confirmed rotation, 2026-08-22, by about a month — the logs from that
  earlier window have themselves already been rotated out, so the original trigger could not be recovered by
  any thread that has investigated this so far).
- Whether repairing the stale cursor or the shadow/empirical arbitration priority would produce any
  *measurable* quality benefit — both are structurally ready to flow through already-verified mechanisms, but
  magnitude is unconfirmed in both cases.
- Whether `self_edit_convergence.json`'s currently-zero non-convergent streaks reflect correct design behavior
  or quiet inertness (`self_edit_closed_loop_validation.md`'s own unresolved finding, not re-investigated this
  mission).
- Whether memory retrieval has any causal effect on task types other than `personal`, or at temperature=0 —
  the one attempt to answer this did not complete (§2, item 10).
- Whether `echo_projects`'s 0/61 reflects a genuine model-class ceiling or a fixable prompt/gate-calibration
  issue — not disambiguated by any investigation to date.
- Whether the current 4-model-diverse council composition, if `ARCH_COUNCIL` does win, reflects something
  about *this specific* model pool rather than model diversity in general — untested by any design.
- The full current content of the 2026-09-02 architectural-self-knowledge document series was not read in
  full depth by this synthesis (only cross-cited where other documents already summarized it) — this
  synthesis's self-model/metacognition entries in §3 should be treated as provisional pending a dedicated read.

## 13. Falsification Criteria

Stated in advance, for the specific claims this synthesis makes, so a future session can check them cleanly:

- **This synthesis's H1-support reading of any future Tier-3 result would be falsified** by `BASE_N`
  performing statistically indistinguishably from `ARCH_COUNCIL` on the held-out set (direct support for H4
  instead) — this is a valid, anticipated, non-failure outcome, not evidence the experiment failed.
- **This synthesis's claim that `learn_from_council_rating()` is currently dead would be falsified** by
  `council_ratings.jsonl` growing within one real polling cycle without any code change — i.e., if
  `interaction_log.jsonl`'s natural growth carries the line count back past the stale cursor's position
  (33,471) before any repair is applied, at the observed ~53/hour rate this would occur around 2026-09-17;
  this is a plausible, if slow, self-resolution path already named in the companion autonomous-fruit audit.
- **This synthesis's `echo_projects` classification (D, no demonstrated fruit) would be falsified** by any
  single real, human-verified, F2-passing, genuinely useful multi-file project emerging from either the
  manual or autonomous path.
- **This synthesis's P1.2-null-result-carries-forward claim would be falsified** by a replication (with the
  position-decoupling redesign §3's own follow-up names) showing genuine content-tracking through a real,
  repeated label flip, with power sufficient to distinguish it from the position-bias explanation already
  confirmed dominant in the existing data.
- **This synthesis's C1 75% compliance estimate would be meaningfully revised** by a larger-N (20+)
  replication landing outside a reasonable confidence interval around 75%.
- **This synthesis's readiness verdict (READY WITH CONDITIONS) would become NOT READY** if a genuine
  low-contention window proves structurally unobtainable (e.g., if throttling `model_guided_autonomous_loop`/
  `echo_projects` for the run's duration turns out to still leave >15% `INFRASTRUCTURE_FAILURE` on a real
  attempt) — that would indicate the contention problem is deeper than this synthesis's own operating-profile
  analysis assumed, and would need its own follow-up investigation before Tier-3 could proceed.

---

**NEXT MISSION: Author and freeze 8 held-out tasks, secure a genuine EXPERIMENT_WINDOW (Option 3) low-contention operating window, run a fresh development-sanity pass under the repaired `scripts/run_tier3_apparatus.py` to confirm `BASE_N`'s synthesis behaves sanely, then execute the full 4-arm Tier-3 held-out comparison exactly per the protocol in §11 of this document — reporting the §8 hypothesis-boundary language verbatim alongside any result.**
