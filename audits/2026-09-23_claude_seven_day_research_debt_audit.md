# Claude Seven-Day Research Debt Audit (2026-09-16 → 2026-09-23)

Read-only archaeology. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after (confirmed by `git rev-parse` before and after). E0.1 (`app/experiments/rung1/`, `scripts/verify_rung1_e0_trusted_evaluator.py`) confirmed untouched throughout — diffed against a fresh pre-mission snapshot, zero changes. No production code, RiverBrain, AP-0, sandbox profile, or generation infrastructure was modified. Only this report was created.

## 1. Executive summary

Fifty-six audit files exist in the window, spanning at least five distinct research programs, not one continuous thread: (1) a "capability ceiling"/claims-ladder investigation that produced (2) the **E5-mini/G0** apparatus — built, adversarially attacked twice by Codex, and terminated **NOT QUALIFIED / NO-GO**, with no further work on it found after 2026-09-16; (3) a **persistent-competence protocol** (design → adversarial review → candidate tournament → frozen v1.0 → blind review found 12 vulnerabilities → frozen v1.1 closed all of them), which became (4) **AP-0**, whose Stage 0 ran and was genuinely informative, but whose Stage 1 constructor qualification (QUAL-1) **failed its own frozen threshold** (K2/K3 not qualified; a later independent Codex audit found the *pooled* gate itself fails too, 83.3% < 85%) and remains unrun; and (5) the **Rung-1 persistent-routing / trusted-evaluator (E0/E0.1)** program this session completed, which is a *direct, explicit, evidenced successor* to (3)/(4) — not a parallel or forgotten track — via a documented reconciliation (`claude_codex_reconciliation_and_oct1_roadmap.md`) in which both an independent Claude and an independent Codex reassessment converged on deprioritizing AP-0's specific bet (LLM induction from synthetic episodes) in favor of a narrower, better-specified claim (bounded routing improvement). A sixth, largely separate thread (Seagate vault / M5-Intel backup / relay infrastructure) exists in the same window and is out of scope for this audit's "learning" focus; it is inventoried but not analyzed.

**The single most important standing research debt is not new**: the same evaluator vulnerability (candidate code and expected answers sharing one Python execution namespace) was independently discovered **twice**, in two different codebases, by two different investigators, four days apart — once in AP-0's real, still-live `oracle_runner.py`/`tasks.py` (Codex, 2026-09-22, `codex_ap0_independent_forensic_audit.md`), and once in the brand-new, separate Rung-1 evaluator (Codex, 2026-09-23, then repaired by this session as E0/E0.1). **The AP-0 instance has never been repaired.** This is real, live implementation debt sitting in a codebase this project still calls a reusable component.

## 2. Scope and method

Primary window: 2026-09-16 through 2026-09-23. All 56 files with a filename date in this window were enumerated (`find`). Given the volume, files were triaged by depth of reading rather than read uniformly: the ~20 files most central to the mission's own topic list (persistent learning, AP-0, E5-mini/G0, RiverBrain, Rung-1/E0) were read in substantial part or in full; several large files (e.g., `capability_growth_reconciliation.md`, 986 lines; `e5_mini_final_adjudication.md`, 605 lines) were read only in their opening and/or closing sections; a smaller number of files central to a *different* thread (the Seagate/M5 backup work) were identified by title only and not analyzed, per the mission's own scope guidance that not every topic in the seed list need be present. This is disclosed honestly, not smoothed over — see §24 Limitations for exactly which files received which depth of reading, and confidence levels below reflect this directly.

## 3. Repository provenance

Opening: HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce`; `git status --porcelain` = 227 entries. E0.1's own files (`app/experiments/rung1/`, `scripts/verify_rung1_e0_trusted_evaluator.py`) confirmed present, untracked, and — via a diff against a snapshot taken at the start of this mission — unmodified throughout. Closing: identical HEAD; identical E0.1 file set. No commit was made.

## 4. Claude report inventory

Not reproduced as a full 56-row table here (most of the substantive content is extracted into the ledger, §7, which is the actual deliverable) — but every file consulted is cited by name at least once below, and the ones read in depth are:

- `2026-09-16_capability_growth_reconciliation.md` (Codex M5 — read: opening ~150 lines)
- `2026-09-16_e5_mini_final_adjudication.md` (Codex — read: opening ~200 lines)
- `2026-09-16_e5_mini_g0_repair_and_requalification.md` (author unclear from header; read: closing verdict)
- `2026-09-16_e5_mini_g0_codex_requalification_attack.md` (Codex — read: closing verdict)
- `2026-09-17_recursive_learning_ground_truth_investigation.md` (Claude, multi-session journal — read: closing ~250 lines, including a later continuation appended to the same file)
- `2026-09-17_task_type_map_sync_ground_truth_and_qualification.md` (read: closing verdict)
- `2026-09-17_learning_signal_evaluator_qualification.md` (read: closing verdict)
- `2026-09-19_persistent_competence_candidate_tournament.md` (read: substantially in full)
- `2026-09-20_persistent_competence_v1_to_v1_1_traceability.md` (read: substantially in full)
- `2026-09-21_ap0_stage0_preregistration_v1.md` (read: in full)
- `2026-09-21_ap0_stage1_preregistration_v2_DRAFT.md` (read: in full)
- `2026-09-21_ap0_v2_causal_chain_and_skeptic_review.md` (read: in full)
- `2026-09-21_ap0_v2_constructor_qualification_protocol.md` (read: in full)
- `2026-09-22_codex_ap0_independent_forensic_audit.md` (read: opening + closing verdict + addendum)
- `2026-09-22_claude_codex_reconciliation_and_oct1_roadmap.md` (Claude, my own — read: Parts I-II)
- `2026-09-22_claude_feralecho_research_direction_reassessment.md` (Claude, my own — read: opening)
- `2026-09-22_feralecho_research_direction_reassessment.md` (Codex — read: opening)
- Every 2026-09-22/23 file in the direct Rung-1 lineage (`persistent_learning_experiment_premortem.md`, `preregistered_persistent_routing_experiment_design.md`, `codex_adversarial_attack_on_reconciled_roadmap.md`, `claude_reconciliation_of_codex_learning_attack.md`, `task_correctness_evaluator_qualification.md`, `trusted_boundary_reconciliation.md`, `adversarial_learner_game.md`, `rung1_final_preimplementation_gate.md`, `rung1_engineering_gate_specification.md`, `rung1_e0_trusted_evaluator_implementation.md`, `codex_e0_independent_scientific_validation.md`, `rung1_e0_1_repair_and_requalification.md`) — all read in full across this and prior sessions this week, authorship and content already established with high confidence.

Not read, or read only by title/grep: the ten Seagate/M5-backup files, `2026-09-16_e5_mini_manifests_design_and_hostile_review.md`, `2026-09-16_e5_mini_g0_mock_implementation.md`, `2026-09-17_python_learning_capability_gap_audit.md`, `2026-09-16_codex_capability_ceiling_adversarial_review.md`, `2026-09-16_e5_mini_adversarial_preimplementation_review.md`, `2026-09-16_e5_mini_codex_reconciliation.md`, `2026-09-16_e5_mini_codex_requalification_reconciliation.md`, `2026-09-16_e5_mini_g0_codex_adversarial_review.md`, `2026-09-16_feralecho_zero_cost_capability_ceiling.md`, `2026-09-19_persistent_competence_experiment_design.md`, `2026-09-19_persistent_competence_experiment_adversarial_review.md`, `2026-09-20_persistent_competence_protocol_v1_blind_review.md`, `2026-09-20_persistent_competence_frozen_protocol.md`, `2026-09-20_persistent_competence_frozen_protocol_v1_1.md`, `2026-09-22_self_edit_evidence_preservation_investigation.md`, `2026-09-22_vrm_retrospective_feasibility_investigation.md`, `2026-09-22_echo_member_stuff_investigation.md`, `2026-09-22_feralecho_manual_council_model_upgrade_consultation.md`. Their existence and titles are recorded; their content is not analyzed below except where another, read document cites a specific finding from them (cited as **RETRIEVED**, not **OBSERVED**, in that case).

## 5. Seven-day research chronology

```
09-16  Capability-ceiling investigation (Codex) → E1-E7 roadmap
       → Claude adversarial review (challenges the ladder)
       → Codex reconciliation: "READY WITH CHANGES", repaired claims ladder L0-L6
       → E5-mini experiment specified (four-arm P/E/Z/N design)
       → Claude adversarial pre-implementation review
       → Codex final adjudication: "READY WITH CHANGES" (add arm Z, condition-integrity manifest)
       → G0 (mocked measuring instrument) implemented
       → Codex adversarial review of G0 → failures found
       → repair-and-requalification pass
       → Codex requalification attack → NEW counterexamples found (balanced retry/omission,
         shared-state N leakage, no frozen-vs-runtime binding)
       → FINAL VERDICT: G0 NOT QUALIFIED, E5 NO-GO. Thread ends here — no further
         E5-mini work found after 09-16.

09-17  Recursive learning ground truth investigation (Claude, multi-session journal):
       real source-level findings (learn_from_rating/learn_from_sandbox_outcome never
       write model_task_stats; TASK_TYPE_MAP silent divergence; _ast_complexity
       shortcut-vulnerable) → a real behavioral pilot (procedure-pressure ladder,
       12/12 conversations, real transcripts) → priority-ordered recommendation list.
       → task_type_map_sync_ground_truth_and_qualification.md: SHIPPED (a real
         Liveness Ledger check now exists — confirmed in current source).
       → learning_signal_evaluator_qualification.md: 20-requirement contract proposed,
         not implemented as a gate anywhere.

09-19/20  Persistent-competence protocol (Claude): experiment design → 4-agent
       adversarial review → 5-agent candidate tournament (RiverBrain vs.
       self_model_claims vs. behavioral_state vs. task_type_classifier — no single
       winner; a hybrid recommended, not built) → frozen protocol v1.0 → blind
       review finds 12 vulnerabilities (2 CRITICAL) → frozen protocol v1.1 closes
       all 12, independently traced.

09-21  v1.1 becomes AP-0. Stage 0 preregistered, run, and genuinely INFORMATIVE
       (all six gates G1-G6 passed; H=0.815 vs N/NEUTRAL/MISMATCH=0.000).
       → Stage 1 v2 drafted, but explicitly left UNFROZEN because QUAL-1
         (constructor qualification) found K2/K3 NOT QUALIFIED, K1 only
         PARTIALLY QUALIFIED — Stage 1 has never run.

09-22  Codex's independent forensic audit of AP-0: reproduces all 554 Stage-0
       grades independently; finds the pooled QUAL-1 gate itself fails its own
       85% threshold (83.3%); finds the SAME same-module evaluator vulnerability
       later found in Rung-1's own evaluator; finds a surviving non-learning
       doppelgänger (a fixed compiler). Verdict: STAGE 1 NOT READY. Proposes a
       full "minimum longitudinal discrimination experiment" — not built.
       → Two independent, parallel reassessments (Claude, Codex) both
         independently recommend deprioritizing AP-0's specific bet.
       → Reconciliation of the two: "Decision B — keep AP-0 as a component
         test, pursue a different primary research program." Corrects Claude's
         own RiverBrain claim in the reassessment ("Codex is right, neither
         verified-outcome function writes model_task_stats") — itself later
         found overclaimed (see §19, self-correction chain).
       → This reconciliation is the direct origin of the Rung-1 program.
       → Rung-1 design → premortem (Codex) → trusted-boundary reconciliation
         (Claude) → adversarial-learner-game (Claude) → engineering-gate
         specification (Claude).

09-23  Stage E0 (trusted evaluator) built, 35/35 tests pass.
       → Codex's independent scientific validation: E0 CONDITIONAL — a real,
         demonstrated SystemExit misclassification; a secrecy-test methodology
         bug; an incomplete result contract.
       → Stage E0.1 repairs all three, 57/57 tests pass.
       → THIS AUDIT.
```

## 6. Claims/debt extraction method

Every report's own verdict block, explicit "future work"/"recommend"/"not established" language, and (where read in depth) its individual claims table were extracted as candidate ledger rows. A claim was only marked RESOLVED if a later, independently-checkable artifact (a diff, a passing test suite re-run, a shipped Liveness Ledger check confirmed in current source) was found — matching the mission's own explicit evidentiary bar. Where I could not find such an artifact, the item is OPEN, IMPLEMENTATION DEBT, or UNKNOWN STATUS as appropriate, not RESOLVED by default.

## 7. Full research-debt ledger

| ID | Source report | Original finding/obligation | Original status | Subsequent evidence | Current status | Debt type | Dependency | Importance | Confidence | Next evidence needed |
|---|---|---|---|---|---|---|---|---|---|---|
| D-01 | `capability_growth_reconciliation.md` | E1–E7 jointly do not establish accumulation; E8 (successive acquisition + retention/interference controls) required | PROPOSED | E8 never designed in detail found in this window; superseded in priority by AP-0/Rung-1 | **SUPERSEDED** (in priority, not falsified) | THEORY DEBT | Rung-1's own claims-ladder work continues this distinction | MEDIUM | MEDIUM | An explicit statement that E8 is intentionally shelved, or a fresh design if revived |
| D-02 | `e5_mini_g0_codex_requalification_attack.md` | G0 mocked measuring instrument | Built, twice repaired | Final Codex attack found N-isolation broken, no frozen-vs-runtime binding | **ABANDONED / NO-GO** | — | None found continuing this thread after 09-16 | LOW (superseded by AP-0/Rung-1's stronger process-separation designs) | HIGH | None planned; flagged only so it isn't silently resurrected without inheriting Rung-1's own E0/E0.1 lessons |
| D-03 | `recursive_learning_ground_truth_investigation.md` | `learn_from_rating()`/`learn_from_sandbox_outcome()` never write `model_task_stats` | OBSERVED (source read) | Independently re-confirmed this session (`learn_from_sandbox_outcome` still true); `learn_from_council_rating()` (a third, separate function) found this session to genuinely write it | **RESOLVED for the two named functions; the claim's implicit generalization to "no verified-outcome path reaches model_task_stats" was itself corrected later — see D-19** | PROVENANCE DEBT | — | HIGH | HIGH | None — resolved by direct, repeated source confirmation |
| D-04 | same | `TASK_TYPE_MAP` exists as two independently-editable copies; silently diverged twice historically | OBSERVED | `task_type_map_sync` Liveness Ledger check shipped (confirmed present in current `app/core/liveness_ledger.py`, grep this session) | **RESOLVED (partial fix)** — a monitor exists; the report's own text states the deeper structural fix (extracting one shared module) was deliberately not attempted | IMPLEMENTATION DEBT (residual) | None | MEDIUM | HIGH | A small, isolated extraction of `TASK_TYPE_MAP` into one shared module, per the report's own stated next step |
| D-05 | same | `_ast_complexity()` (self-edit's coding quality scorer) is confirmed shortcut-vulnerable AND currently AUTHORITATIVE over real deployment | OBSERVED, flagged highest-priority | No fix found in this window's file set | **OPEN, CRITICAL** | QUALIFICATION DEBT / EVIDENCE DEBT | Blocks any repair to the sandbox-outcome→`model_task_stats` wire, per the report's own explicit sequencing | CRITICAL | MEDIUM (not independently re-verified this session) | Direct re-verification of the shortcut against current `echo_quality_scorer.py`, then a fix, before any RiverBrain reward-wire repair |
| D-06 | same | Priority-ordered 5-step recommendation (ship `task_type_map_sync`; run attempt-ledger CONTROL-vs-EXPERIENCE; build a RiverBrain input/output leakage attack; only then repair the reward wire; separately replicate the pressure ladder at n≥15) | PROPOSED | Step 1 shipped (D-04). Steps 2, 3, 5 not found anywhere in the subsequent file set. Step 4 (reward-wire repair) has not been attempted — RiverBrain's `learn_from_sandbox_outcome()` still doesn't write `model_task_stats` per D-03's reconfirmation | **IMPLEMENTATION DEBT (steps 2, 3, 5); step 4 correctly still blocked on D-05** | IMPLEMENTATION DEBT | Step 4 depends on D-05 | HIGH | MEDIUM | Run steps 2/3/5 as independently-scoped missions; do not repair the wire (step 4) until D-05 closes |
| D-07 | `learning_signal_evaluator_qualification.md` | 14-mechanism inventory of FeralEcho's real/proxy learning signals; a 20-requirement minimum safe learning-signal contract | PROPOSED | Not adopted as a gate anywhere found; `task_type_map_sync` (D-04) is the one concrete artifact traceable to this report's own requirement #20 | **OPEN** | THEORY DEBT | — | MEDIUM | MEDIUM | A decision on whether to formalize this contract as a standing check, or treat it as reference documentation only |
| D-08 | `persistent_competence_candidate_tournament.md` | No single existing FeralEcho mechanism (RiverBrain, `self_model_claims.py`, `behavioral_state.py`, `task_type_classifier.py`) wins on every dimension; recommended a minimal hybrid: reuse F2's real sandbox pass/fail as evaluator, give it a fresh, cheaply-isolatable carrier, consume via a narrow new function mirroring (not calling) `score_model()` | PROPOSED | **Not built.** The subsequent AP-0/Rung-1 thread pursued a different design (a wholly standalone selector, not a FeralEcho-mechanism hybrid) | **SUPERSEDED, but the underlying survey remains valid and unconsulted by the newer thread** | ORPHANED DISCOVERY / IMPLEMENTATION DEBT | — | HIGH | HIGH (read substantially in full) | Cross-check whether Rung-1's eventual real task substrate should reuse this tournament's specific "F2 pass/fail + fresh carrier" recommendation instead of/alongside a wholly synthetic evaluator |
| D-09 | same | `behavioral_state.py`'s own measured 75% compliance figure was obtained via a path that **bypasses** the real production `_is_introspective()` gate 3 of 4 real entry points impose — the measured effect and the real production effect are not the same claim | OBSERVED (dedicated deep-dive) | No fix or re-measurement found | **OPEN** | EVIDENCE DEBT | — | MEDIUM | HIGH | Re-run the compliance measurement through the real, gated entry points, or fix the gate, before citing this figure as a production capability |
| D-10 | same | `task_type_classifier.py` has a hard, permanent, non-decaying `_MAX_MODEL_EXAMPLES_PER_CLASS=100` cap — zero model change after 100 real examples per class, for the life of the pickle | OBSERVED (independently, twice) | No fix found | **OPEN** | CAPABILITY DEBT | — | MEDIUM | HIGH | A decision on whether the cap should ever be lifted/decayed, or whether this is intended and merely undocumented as a hard ceiling |
| D-11 | same | RiverBrain requalification: `score_model()`'s one real controlled predictive-value test (`tier7_riverbrain_candidate_ranking_forensic.md`) found 77.8% accuracy overall but only 38.9% (worse than chance) once a single confounding model is excluded — never acted on in production | RETRIEVED (cited, not independently re-read this session) | No fix found | **OPEN, real Simpson's-paradox finding sitting unused** | EVIDENCE DEBT | — | HIGH | MEDIUM (retrieved via citation, not independently re-verified) | Independently re-verify the 38.9% figure directly against current `river_brain.pkl`, then decide whether `score_model()`'s ranking should change |
| D-12 | `persistent_competence_v1_to_v1_1_traceability.md` | 12 vulnerabilities found in protocol v1.0 (2 CRITICAL: deterministic tie-break producing a fixed always-worst-worker baseline; a sham/transplant arm that was structurally identical to a control) | OBSERVED | All 12 traced to specific v1.1 sections and independently re-verified CLOSED in this document | **RESOLVED** | — | — | HIGH | HIGH (read substantially) | None — this is a clean, well-evidenced closure |
| D-13 | `ap0_stage0_preregistration_v1.md` | Stage 0 (instrument + carrier-consumption gate) frozen and run | PROPOSED → EXECUTED | All six decision gates (G1-G6) reported passed; H=0.815 vs N/NEUTRAL/MISMATCH=0.000 | **RESOLVED** (Stage 0 specifically; not a claim about Stage 1) | — | — | HIGH | HIGH (read in full) | None for Stage 0 itself |
| D-14 | `ap0_stage1_preregistration_v2_DRAFT.md` | Stage 1 (real acquisition experiment) fully designed, with hypotheses A-D, N-ctl, thresholds, and a predetermined outcome-interpretation table | PROPOSED, explicitly UNFROZEN | QUAL-1 (D-15) blocks it; never authorized or run | **EXPERIMENT DEBT** — apparatus and design substantially specified, never executed | EXPERIMENT DEBT | Blocked on D-15 | HIGH | HIGH (read in full) | QUAL-1 must qualify K2/K3 (or the design must be revised to drop them, explicitly not silently) before Stage 1 can be authorized |
| D-15 | `ap0_v2_constructor_qualification_protocol.md` | QUAL-1: is the LLM constructor capable of inducing K1/K2/K3 conventions from episodes? | PROPOSED → EXECUTED | K1 PARTIALLY QUALIFIED, K2/K3 NOT QUALIFIED (frozen decision rule) | **RESOLVED as a negative result** (the qualification question itself was answered; the answer was "no" for 2 of 3 conventions) | — | Blocks D-14 | CRITICAL | HIGH (read in full) | None to re-run QUAL-1 itself; a *different* constructor/representation would need a fresh QUAL-2, per the draft's own §11 |
| D-16 | `codex_ap0_independent_forensic_audit.md` | Independent reproduction of all 554 Stage 0 grades and the QUAL-1 gate math | PROPOSED (adversarial audit) | Reproduced the H=44/54 finding; found the **pooled** QUAL-1 gate fails its own 85% threshold (83.3%) — a stricter reading than D-15's own per-convention framing | **RESOLVED (a sharper negative result than D-15 alone stated)** | — | — | HIGH | HIGH (read opening+closing) | None |
| D-17 | same | The AP-0 evaluator (`oracle_runner.py`/`tasks.py`) shares one Python module between candidate code and hidden expected answers — a function that reads the global answer table passes every stored test module | OBSERVED, confirmed by direct in-memory reproduction | **No fix found anywhere in the subsequent file set.** The *conceptually identical* vulnerability in the separate, new Rung-1 evaluator was found and fixed (E0/E0.1) this session — but that fix touches only `app/experiments/rung1/`, never `app/experiments/accumulation_probe/oracle_runner.py`/`tasks.py` | **OPEN, CRITICAL — this is the single most important standing implementation debt this audit found** | IMPLEMENTATION DEBT | The Rung-1 E0 repair pattern (per-case, process-separated evaluator) is a directly reusable template | CRITICAL | HIGH | Apply the same per-case, process-separated repair pattern (or an explicit decision not to, with reasoning) to AP-0's own evaluator before any future AP-0 stage reuses it |
| D-18 | same | A non-learning doppelgänger (a fixed example-to-instruction compiler) survives every proposed AP-0 control | OBSERVED/INFERRED | The "conceptual addendum" longitudinal discrimination experiment (fixed-compiler baseline, G/R state separation, restart boundaries) is fully specified but explicitly "no audit reopened, apparatus changed, code written or experiment run" | **EXPERIMENT DEBT** | EXPERIMENT DEBT | Would need AP-0's evaluator repaired first (D-17) | HIGH | HIGH | Build and run this addendum's design, or explicitly supersede it with Rung-1's own fixed-champion/twin design (which addresses the same doppelgänger concern via a different mechanism) |
| D-19 | `claude_codex_reconciliation_and_oct1_roadmap.md` | "The specific real, verified-outcome functions (`learn_from_sandbox_outcome`, `learn_from_council_rating`) never update the scalar mean `score_model()` reads" | Claimed **CONFIRMED** in this reconciliation, resolving an earlier disagreement "in Codex's favor" | This session (2026-09-22/23, `claude_reconciliation_of_codex_learning_attack.md`) independently re-read the same source and found `learn_from_council_rating()` **does** directly update `model_task_stats["mean"]` — the reconciliation's own "CONFIRMED" verdict was itself an overclaim for one of the two named functions | **RESOLVED, but via a correction of this exact reconciliation document, not a confirmation of it** — see §19 for the full three-step self-correction chain | PROVENANCE DEBT | — | HIGH | HIGH | None — resolved, and the correction is already recorded in two later reports this session |
| D-20 | same | `generate_code_from_plan()` resolves a model name via `choose_model()` but calls `echo_query()` without binding that model — the returned `model_name` is not guaranteed to be the actual producer | OBSERVED, "CONFIRMED directly" | No fix found anywhere in this window's file set | **OPEN** | PROVENANCE DEBT | — | HIGH | HIGH | A fix binding the resolved model into the actual generation call, or an explicit decision this doesn't matter for the current use case |
| D-21 | same | `apply_to_code`'s currently-deployed hook is "a real, live, plausibly destructive keyword-line-filter"; all 15 real deployed self-edit candidates score exactly (4,4) on the fitness gate — the gate has never once discriminated a real deploy from its own baseline | OBSERVED, directly confirmed against `memory/self_edit_attempt_ledger.jsonl` | No fix or re-measurement found in this window | **OPEN, real and current as of 2026-09-22** | EVIDENCE DEBT | — | HIGH | HIGH (quoted directly from source in the reconciliation) | Independently re-verify against the current ledger (may have grown since 09-22) and decide whether the fitness gate needs recalibration beyond Finding 91's own already-applied fix |
| D-22 | `claude_feralecho_research_direction_reassessment.md` / `feralecho_research_direction_reassessment.md` (reconciled) | Decision: deprioritize AP-0's specific bet (LLM induction from synthetic episodes); pursue "verified improvement in how the system performs a useful class of work from its own prior outcomes" instead | Explicit joint decision (both independent reassessments converged) | The entire Rung-1/E0/E0.1 program is a direct execution of this decision | **RESOLVED — this decision was acted on, consistently, for the rest of the window** | — | — | CRITICAL | HIGH | None |
| D-23 | `persistent_learning_experiment_premortem.md` (Codex) | Same-module candidate/expected-answer exposure in AP-0's evaluator generalizes as a design risk to any reused evaluator | INFERRED | The Rung-1 design initially inherited this risk (confirmed independently by this session's own evaluator-qualification and trusted-boundary work); fixed via E0/E0.1 | **RESOLVED for Rung-1's own evaluator; still open for AP-0's (D-17)** | QUALIFICATION DEBT (residual, AP-0 side only) | Same as D-17 | CRITICAL | HIGH | See D-17 |
| D-24 | `codex_e0_independent_scientific_validation.md` | `SystemExit(7)` misclassified as `SANDBOX_INFRASTRUCTURE_ERROR`; secrecy suite tested the wrong sentinel; result contract incomplete (missing-value, bool/int, non-finite floats) | OBSERVED, demonstrated | E0.1 (this session, prior report) fixed all three, 57/57 tests, independently re-verified in this session's own re-read of the diff | **RESOLVED (builder-qualified; awaiting independent requalification per E0.1's own explicit next step)** | — | E0.1 → Codex independent requalification (not yet performed) | CRITICAL | HIGH (this session's own direct work) | Codex's independent requalification of E0.1, per E0.1's own final recommendation |
| D-25 | `rung1_final_preimplementation_gate.md` (Codex) | A fourth, information-denied template-only comparator is unnecessary; Rung 1 does not require convention induction, only routing among fully-informed workers | INFERRED, ruled on directly | Accepted without reopening, per this session's own explicit instruction not to relitigate absent new evidence | **RESOLVED (accepted, not re-derived)** | — | — | MEDIUM | HIGH | None |
| D-26 | `adversarial_learner_game.md` (Claude, this session) | A coarse structural-template recognizer could counterfeit S-split "structural transfer" even after every Rung-1 repair — a template-matched comparator is required to close it | PROPOSED | Not built — the Rung-1 design document itself has not yet been updated to include this comparator | **IMPLEMENTATION DEBT** | APPARATUS DEBT | Feeds into the not-yet-built Stage 3 (task/state substrate) of the E0.1-onward roadmap | HIGH | HIGH (this session's own direct work) | Add the template-matched comparator to the frozen Rung-1 design before Stage 3 |
| D-27 | Multiple (D-05, D-11, D-17, D-21) | Several confirmed-live, currently-authoritative or currently-in-use mechanisms have a demonstrated correctness/shortcut problem that has not been fixed | Cross-cutting | None fixed | **OPEN, CRITICAL, cross-cutting** | EVIDENCE DEBT + QUALIFICATION DEBT | — | CRITICAL | HIGH | A single, explicitly-sequenced remediation pass across all four, prioritized by what's actually load-bearing today (self-edit deployment gate first, per D-05/D-21's own real production consequences) |

## 8. Resolved items

D-03, D-04 (partial), D-12, D-13, D-15, D-16, D-19, D-22, D-24, D-25. Each has independently-checkable closure evidence, not merely a later report's say-so.

## 9. Superseded items

D-01 (E8, in priority not validity), D-02 (the entire E5-mini apparatus, by AP-0's/Rung-1's stronger process-separation and freezing discipline), D-08 (the candidate-tournament hybrid recommendation, by Rung-1's standalone-selector design — worth re-checking, not merely discarded, see §16).

## 10. Critical open/blocked items

**D-17 (AP-0's own evaluator, unrepaired)** — CRITICAL, the highest-value single item in this ledger. **D-05/D-21 (self-edit's currently-authoritative, currently-vulnerable fitness/quality scoring)** — CRITICAL, real production consequence (15/15 real deploys scoring identically, a gate that has never discriminated). **D-14/D-18 (AP-0 Stage 1 and its own proposed discrimination experiment)** — BLOCKED on D-15's own negative result and, if ever revived, on D-17.

## 11. Implementation debt

D-04 (residual shared-module extraction), D-06 (steps 2/3/5 of a fully-specified recommendation), D-17, D-20, D-26.

## 12. Qualification debt

D-09 (behavioral_state's measured-vs-real-gate discrepancy), D-23/D-17 (evaluator secrecy on the AP-0 side).

## 13. Experiment debt

D-14 (AP-0 Stage 1, fully designed, never run), D-18 (the longitudinal discrimination addendum, fully designed, never run).

## 14. Theory/evidence debt

D-01 (E8's exact design), D-07 (the 20-requirement learning-signal contract's formal status), D-11 (the Simpson's-paradox RiverBrain finding, unresolved).

## 15. Provenance debt

D-19 (now resolved, but the chain itself is the finding), D-20 (`generate_code_from_plan()`'s unbound model identity), D-21 (self-edit fitness-gate discrimination).

## 16. Orphaned discoveries

**D-08, the candidate tournament, is the clearest orphan in this entire ledger.** A five-agent, deeply-sourced survey of every persistent-state mechanism in FeralEcho (RiverBrain, `self_model_claims.py`, `behavioral_state.py`, `task_type_classifier.py`, plus 13 more candidates surveyed for completeness) produced a specific, reasoned, cheapest-credible-experiment recommendation — and the very next research thread (AP-0's continuation into Rung-1) built something architecturally different (a wholly synthetic, standalone selector) without citing or ruling out this tournament's own recommendation. Neither superseded-with-reasoning nor incorporated — genuinely fallen off the map. **D-11** (the Simpson's-paradox RiverBrain ranking finding) is a second, smaller orphan: a real, already-computed negative result about the ranking mechanism `score_model()` still uses in production, sitting unconsulted.

## 17. Dormant assets

- **`app/experiments/accumulation_probe/`'s full apparatus** (`worlds.py`, `tasks_v2.py`, `make_cases2()`, `jail.py`, `freeze.py`, `oracle_b_v2.py`, `ollama_client.py`) — already confirmed, independently, twice this week (D-08's own tournament and this session's Rung-1 engineering-gate specification) to be reusable, high-quality, task-generation and generation-client infrastructure. Currently used only by AP-0 itself; the Rung-1 program reuses the *ideas* but not the code directly, per the design's own stated scope.
- **The E0/E0.1 per-case, process-separated evaluator pattern** — proven this session against a real, demonstrated attack; directly applicable to closing D-17.
- **The persistent-competence protocol's full freezing/versioning/blind-review discipline** (D-12) — proven to catch 12 real vulnerabilities including 2 CRITICAL; not yet explicitly reused as a named methodology in the Rung-1 thread, though the Rung-1 thread's own freeze/hash conventions are clearly influenced by it.

## 18. Abandoned/no-go branches

**E5-mini/G0 (D-02)** — the clearest, most explicitly-terminated branch in the whole window: two rounds of Codex adversarial attack, the second finding new counterexamples the first repair pass didn't anticipate, ending in an explicit "G0 NOT QUALIFIED, E5 NO-GO" with no further work found afterward.

## 19. Claude self-corrections

**The three-step RiverBrain correction chain, the most important self-correction in this window:**
1. **2026-09-22, `claude_feralecho_research_direction_reassessment.md`**: I characterized RiverBrain's online learning as "already... a real instance of experience→evaluation→retained state→behavior change," without flagging that the specific *verified-outcome* functions might not be the ones actually reaching the consumed statistic.
2. **2026-09-22, `claude_codex_reconciliation_and_oct1_roadmap.md`**: reconciling my own reassessment against Codex's parallel one, I accepted Codex's sharper claim as **CONFIRMED**: "the specific real, verified-outcome functions (`learn_from_sandbox_outcome`, `learn_from_council_rating`) never update the scalar mean." I re-read the source myself before writing "CONFIRMED" — and still got it wrong for one of the two named functions.
3. **2026-09-22/23, `claude_reconciliation_of_codex_learning_attack.md`** (this session): re-reading the same function a third time, independently, I found `learn_from_council_rating()` **does** directly update `model_task_stats["mean"]` (lines ~958-963) — a real, direct write, not a disconnected classifier-only update. The earlier "CONFIRMED" was a genuine factual error, not a difference of interpretation.

**Why it appeared justified at each step**: `learn_from_sandbox_outcome()` genuinely, verifiably, never writes it — checking that one function correctly and then generalizing the conclusion to its sibling without re-deriving the sibling independently is exactly the failure mode this project's own standing discipline (verify from source, not from a prior report's confidence) exists to catch. **Did anything downstream rely on the incorrect version?** Yes — the reconciliation's own Part II bottleneck-chain diagram states "CONFIRMED: `learn_from_sandbox_outcome`/`learn_from_council_rating` update the classifier, never `model_task_stats`" as a load-bearing premise for its proposed fix sequencing. **Current consequence**: the error was caught and corrected within the same research week, before any implementation was built on the wrong premise — a real, if narrow, near-miss, not a propagated defect.

**A second, smaller self-correction**: my own earlier `2026-09-23_rung1_e0_trusted_evaluator_implementation.md` claimed `echo_sandbox.sb` denies "fork/exec... by omission," when the file explicitly, deliberately allows `process-exec*` (only fork is denied by omission) — caught and corrected in the very next mission (E0.1), independently re-verified via direct `grep` before the correction was written.

## 20. False-closure candidates

Applying a high bar, per the mission's own instruction: **the one candidate that meets it is the general framing, in some earlier prose across this week's own documents, that "AP-0 established real acquisition."** The most careful, most recent, most independently-verified statement (Codex's forensic audit) is explicit that AP-0 established instruction-*following* and content-sensitivity, not acquisition — and every subsequent document in this window (including this session's own work) correctly carries that narrower framing forward. I did not find a document from this window that currently, actively asserts the stronger, false version as settled — the risk was real and named, but the correction already happened inside the window. **NONE FOUND** as a currently-standing false closure, beyond the RiverBrain chain already fully accounted for in §19.

## 21. Dependency graph

```
D-17 (AP-0 evaluator repair)  ─┬─→ D-18 (longitudinal discrimination experiment)
                                └─→ any future AP-0 Stage 1 revival

D-15 (QUAL-1 negative result) ──→ D-14 (Stage 1, BLOCKED, not superseded)

D-05 (_ast_complexity shortcut) ──→ D-06 step 4 (RiverBrain reward-wire repair) ──→ D-11 (ranking recalibration)

E0.1 builder-qualified ──→ Codex independent requalification (NOT YET PERFORMED) ──→ potential later Stage 3+ integration work

D-26 (template-matched comparator) ──→ Rung-1's own not-yet-built Stage 3 (task/state substrate)
```

Per the mission's explicit instruction: `E0.1 builder-qualified → Codex independent requalification → potentially later integration work` is represented exactly this way, and this audit does not continue that chain itself.

## 22. Current critical path

Using only existing decisions: the nearest defensible Rung-1 prospective experiment is blocked, in order, by (1) Codex's independent requalification of E0.1 (not yet performed — the immediate next step, per E0.1's own recommendation), (2) Stage G0 (generation accounting), not yet begun, (3) Stage 3 (task/state substrate freezing), which per D-26 should incorporate the template-matched comparator before being frozen, and (4) real hidden-task-artifact integration, explicitly deferred pending its own filesystem-isolation qualification. None of these are redesigned here.

## 23. Top six findings

### HIGHEST-VALUE UNRESOLVED ITEM
**D-17: AP-0's own evaluator (`oracle_runner.py`/`tasks.py`) still shares one Python module between candidate code and expected answers — the exact vulnerability this project spent two full missions (E0, E0.1) fixing in a *different, newer* evaluator this same week.** The fix pattern already exists, proven, in this repository; it has simply never been pointed at the file where the same bug was independently found four days earlier.

### MOST CONSEQUENTIAL FALSE CLOSURE
NONE FOUND, per the high bar in §20 — the one real near-miss (the RiverBrain chain) was caught and corrected within the window itself.

### MOST IMPORTANT ORPHAN
**D-08, the persistent-competence candidate tournament.** A rigorous, five-agent, source-grounded survey of every real persistent-state mechanism in FeralEcho, with a specific, reasoned "cheapest credible experiment" recommendation — never cited, ruled out, or built on by the very next research thread.

### MOST VALUABLE DORMANT ASSET
**AP-0's own task/world/freeze/jail machinery** (`worlds.py`, `tasks_v2.py`, `make_cases2()`, `jail.py`, `freeze.py`) — independently confirmed reusable and high-quality by two separate investigations this week, currently used only inside AP-0 itself.

### MOST IMPORTANT NEGATIVE RESULT
**QUAL-1's constructor-qualification failure (D-15), sharpened by Codex's independent forensic audit (D-16): a local 7B-class model cannot reliably induce an ordering or operation-table convention from a handful of episodes, even though the information is provably present** (a deterministic symbolic search recovers it instantly). This is a real, evidence-backed capability ceiling, not an untested assumption, and it is the direct, stated cause of this week's pivot away from AP-0's specific bet toward the Rung-1 program.

### MOST IMPORTANT CLAUDE SELF-CORRECTION
**The three-step RiverBrain `model_task_stats` correction chain (§19)** — a genuine factual error, restated as "CONFIRMED" after a real re-read of the source, corrected only on a third independent look. Recorded here plainly because it is exactly the kind of error this project's own standing discipline exists to catch, and it was caught, inside the same research week.

## 24. Limitations

This audit did not read roughly 35 of the 56 files in the window in depth — most substantially the E5-mini thread's own middle stages (manifests design, mock implementation, the first two adversarial-review/reconciliation rounds), the `persistent_competence` experiment design/adversarial-review pair that directly preceded the candidate tournament, the two frozen-protocol documents themselves (only their traceability record was read), the `python_learning_capability_gap_audit.md` (cited secondhand via the recursive-learning journal, not independently read), and the entire Seagate/M5-backup/relay thread. Status judgments for items sourced only from these files' titles or from another document's citation of them are marked with reduced confidence throughout the ledger, and no item was marked RESOLVED on the strength of a citation alone.

## 25. Next evidence only

- **D-17**: apply the E0/E0.1 per-case, process-separated repair pattern to `oracle_runner.py`/`tasks.py`, or an explicit decision to leave AP-0's evaluator as a deliberately-retired artifact.
- **D-05/D-21**: an independent, current re-verification of `_ast_complexity()`'s shortcut vulnerability and the self-edit ledger's (4,4) pattern against today's live data.
- **D-08**: a short reconciliation note stating whether the tournament's hybrid recommendation was consciously rejected in favor of Rung-1's standalone design, and why.
- **D-11**: an independent re-run of the 77.8%/38.9% Simpson's-paradox check against current `river_brain.pkl`.
- **D-26**: adding the template-matched comparator to the frozen Rung-1 design document before Stage 3 begins.
- **E0.1**: Codex's independent requalification — already the explicitly stated next step, not new work invented by this audit.

## 26. Final status block

**AUDIT WINDOW:** 2026-09-16 THROUGH 2026-09-23

**CLAUDE REPORTS IDENTIFIED:** 56

**SUBSTANTIVE ITEMS EXTRACTED:** 27

**RESOLVED:** 10

**SUPERSEDED:** 3

**OPEN:** 9

**IMPLEMENTATION DEBT:** 5

**QUALIFICATION DEBT:** 2

**EXPERIMENT DEBT:** 2

**BLOCKED:** 2

**DEFERRED:** 1

**ABANDONED / NO-GO:** 1

**UNKNOWN STATUS:** 0

**ORPHANED DISCOVERIES:** 2

**DORMANT ASSETS:** 3

**FALSE CLOSURE CANDIDATES:** 0

**E0.1 CURRENT STATUS:** BUILDER-QUALIFIED / AWAITING INDEPENDENT REVIEW

**E0.1 MODIFIED DURING AUDIT:** NO

**PRODUCTION ECHO MODIFIED:** NO

**RIVERBRAIN MODIFIED:** NO

**AP-0 MODIFIED:** NO

**SANDBOX PROFILE MODIFIED:** NO

**G0 STARTED:** NO

**EXPERIMENTS RUN:** NO

**GIT HEAD CHANGED:** NO

**IMPLEMENTATION AUTHORIZATION:** NO

**1. What is the most important thing Claude discovered during the last seven days that remains unfinished?** That AP-0's own real evaluator shares one Python module between candidate code and expected answers — the identical vulnerability this same week's later work (E0/E0.1) spent two full missions repairing in a different codebase, with a proven, directly-applicable fix pattern now sitting unused for the original instance.

**2. What did Claude recommend that was never implemented?** The persistent-competence candidate tournament's "cheapest credible experiment" (reuse F2's real sandbox pass/fail as evaluator, a fresh cheap carrier, a narrow consumer mirroring `score_model()`) — superseded in direction by Rung-1 without ever being explicitly ruled out.

**3. What was implemented but never independently qualified?** Stage E0.1 itself, exactly as its own report states — builder-qualified, awaiting Codex's independent requalification.

**4. What experiment was designed but never actually run?** AP-0 Stage 1 (the real acquisition experiment) and Codex's own proposed longitudinal discrimination addendum — both fully specified, neither executed.

**5. What important discovery fell off the active roadmap?** The candidate tournament's full survey of FeralEcho's persistent-state mechanisms (RiverBrain, `self_model_claims.py`, `behavioral_state.py`, `task_type_classifier.py`) — real, deep, source-grounded, and uncited by the thread that followed it.

**6. What earlier Claude conclusion was most significantly corrected by later evidence?** That neither `learn_from_sandbox_outcome()` nor `learn_from_council_rating()` updates `model_task_stats` — the second half was wrong, corrected on a third independent re-read.

**7. Did any Claude factual mistake propagate into later research assumptions?** Briefly — the wrong RiverBrain claim was load-bearing for one reconciliation document's proposed fix sequencing, but was caught and corrected within the same research week, before anything was built on it.

**8. What negative result most strongly constrains current learning claims?** QUAL-1's finding that a local 7B-class constructor cannot reliably induce an ordering or operation-table convention from episodes that provably contain the needed information — a real capability ceiling, not an untested assumption.

**9. What existing mechanism or infrastructure could save future work?** AP-0's own `worlds.py`/`tasks_v2.py`/`make_cases2()`/`jail.py`/`freeze.py` task-generation and freezing machinery — already independently confirmed reusable twice this week.

**10. What currently blocks the nearest defensible Rung-1 experiment?** Codex's independent requalification of E0.1 (not yet performed), then Stage G0 (generation accounting, not yet begun).

**11. Is anything currently treated as solved that evidence says is not?** Not found as an active false closure within this window — the one real near-miss (RiverBrain) was self-corrected before this audit began.

**12. Is anything currently treated as future work that is already substantially solved?** AP-0's evaluator vulnerability (D-17) is effectively already solved *in pattern* — the E0/E0.1 repair is a directly transferable template, not a new engineering problem.

**13. What is the most important unresolved provenance question?** `generate_code_from_plan()`'s unbound model identity (D-20) — the returned `model_name` is not guaranteed to be what actually produced the code, and every downstream sandbox-outcome attribution depends on it.

**14. If only three research debts could eventually be addressed, which three deserve attention and why?** (1) D-17, because it is the same fix this project already proved works, sitting unapplied to the file where the identical bug was found; (2) D-05/D-21 together, because they are the one item in this ledger with a real, current, active production consequence (a self-edit deployment gate that has never once discriminated a real deploy); (3) Codex's independent requalification of E0.1, because it is the one item every other forward-looking dependency in §21 is chained behind.
