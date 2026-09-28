# Claude/Codex Reconciliation and October 1 Roadmap

**Git HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` (unchanged throughout this reconciliation).
**Working tree:** dirty at start (204 porcelain entries: the same 27 pre-existing tracked-modified files present since before this session's AP-0 work, plus untracked experiment/audit files); unchanged in kind by this document — only this new file was added.
**SHA-256, Claude's independent report** (`audits/2026-09-22_claude_feralecho_research_direction_reassessment.md`): `41e74987f04e998550eb382119163d7571a51485eb21d2aff57d91341035258c`
**SHA-256, Codex's independent report** (`audits/2026-09-22_feralecho_research_direction_reassessment.md`): `7b5d2d6acd24b2ad13f48010589fa14700979e4bb238c7cd333d89af493808c7`
**Confirmation:** both source reports are treated as immutable evidence in this document. Neither was modified, and both hashes were re-verified against disk immediately before writing this file.

**Method.** I read both reports in full before writing anything below. Where a claim from either report was load-bearing for the reconciliation, I re-checked it directly against current source (labeled **CONFIRMED**, **PARTIALLY CONFIRMED**, or **NOT INDEPENDENTLY VERIFIED** below) rather than taking either report's word for it — including my own. No production code, RiverBrain, FAISS, council/routing, self-edit, AP-0, model configuration, git history, or experimental evidence was modified to write this. No expensive model experiment was run.

---

## PART I — RECONCILE THE TWO MAPS

| Proposition | Claude's position | Codex's position | Classification | Evidence |
|---|---|---|---|---|
| Proper role of AP-0 | Keep as component test / reusable tooling; not the primary path | Same, more explicitly scoped: a test of "one carrier-mediated architecture," not a universal prerequisite | **AGREE** | Both independently landed on Decision B before comparison. |
| Strongest thing AP-0 established | K2/K3 are identifiable from the episodes (deterministic solver, mutation-tested); the local constructor fails anyway | Agrees on the fact pattern, adds the scope limit that this is specific to a *natural-language-note* carrier architecture, not evidence against e.g. a contextual policy or deterministic parser | **COMPATIBLE** | AP-0 qualification report (this session); Codex §5. |
| Local-model induction limitation | Real, demonstrated twice (QA, QB); a genuine bottleneck for this task shape | Real but explicitly bounded — "does not establish a universal local-model incapacity"; candidate-sufficiency must be checked before blaming selection | **COMPATIBLE, with a real emphasis difference** | Neither claim contradicts the other; Codex's caveat is the more careful one and I adopt it below. |
| Procedure-consumption/execution limitation | Real, independent of induction (GOLD K2 2/4) | Not directly addressed in Codex's report (Codex's own primary proposal is about *strategy selection*, a different consumption question) | **UNRESOLVED (Codex is silent, not disagreeing)** | AP-0 QUAL-1 gate data, this session. |
| RiverBrain's actual learning/adaptation status | Framed as "a narrow, real, working example" of experience→evaluation→retained state→behavior change | Sharper and, on direct verification, **more accurate**: the specific real, verified-outcome functions (`learn_from_sandbox_outcome`, `learn_from_council_rating`) never update the scalar mean that `score_model()` reads for ranking — only ordinary `learn()`, scored by a syntactic heuristic, does that | **CONTRADICTION, resolved in Codex's favor** — see Part III | Directly re-read `echo_model_orchestrator.py`'s `learn()` (line ~808), `score_model()` (line ~995), `learn_from_sandbox_outcome()` (line ~870), `learn_from_council_rating()` (line ~936) this session. **CONFIRMED.** |
| Feedback-to-future-behavior wiring | Assumed mostly present for RiverBrain; flagged as broken for `coupling_estimate` and memory retrieval | Names the same general disease with more specific, currently-live instances: the RiverBrain wiring gap above, plus a live model-attribution gap in `generate_code_from_plan` | **AGREE on the disease; Codex's specific instances are stronger and independently confirmed** | See Part II/V. |
| Whole-artifact vs. component-level credit assignment | My distinct contribution: retention is binary at the whole-artifact level; no partial credit for a near-miss | Codex's distinct contribution: credit is often assigned to the *wrong actor/state entirely* (strategy-level), independent of whether it's partial | **COMPATIBLE — two different, both-real layers of the same problem, not competing explanations** | See Part V. |
| Abstraction formation | "Not attempted anywhere in a genuine sense" | Same conclusion, plus a concrete better next test (Program 2, verified reusable skills against a full-solution-retrieval baseline) | **AGREE** | Neither report found a counter-example; not independently re-searched further here. |
| Memory/retrieval | Dead end for accumulated competence specifically (Finding 76 ablation, noise-floor-comparable effect) | Names a *different*, concrete defect: `VectorMemory.add`'s duplicate-ID metadata-replacement behavior, with a real recorded reproduction (`r5_memory.json`) | **COMPATIBLE** — both are real, independent problems with the same subsystem | Finding 76 (prior session, re-cited); `r5_memory.json` exists on disk (confirmed, not opened in depth). |
| Council synthesis | Not directly addressed | "Unconditional council synthesis is not a general improvement operator" — cost/correctness tradeoff, not always positive | **NOT ADDRESSED BY CLAUDE — no conflict, an addition** | Not independently re-verified this pass; consistent with CLAUDE.md's own Tier-4/5 findings (Findings 87-88) about council sometimes losing capability the direct model had. |
| Self-edit | Convergence data doesn't show improvement; "4/4 quality ceiling" cited as *possibly* a metric-coarseness artifact per Finding 91's fix | Independently found and directly named the deeper problem: **the currently-deployed `apply_to_code` hook is a real, live, plausibly destructive keyword-line-filter** (CONFIRMED, see below), and **all 15 real deployed candidates in `self_edit_attempt_ledger.jsonl` score exactly (4,4)**, i.e. the gate has never once discriminated a real deploy from its own baseline | **PARTIALLY CONTRADICTS Claude's more optimistic framing** — Finding 91's recalibration is real, but this ledger's most recent deploy (2026-09-20, after Finding 91) still reads (4,4), so the coarseness problem is not resolved in practice regardless of the formula fix | **CONFIRMED** directly: `memory/self_edit_attempt_ledger.jsonl`, 1,294 rows, 15 deployed, `{(fitness_score, production_score)} == {(4, 4)}` for all 15. `app/core/self_edit_generated.py`'s live `apply_to_code` genuinely drops any line without `def`/`class`/`if`/`for`/`while` and truncates survivors — read directly, current file. |
| Autonomous curriculum | Signals feeding it look saturated (physiology audit) | Distinguishes curriculum-in-name from curriculum-in-fact: novelty-maximizing or weak-task selection isn't curriculum learning unless chosen practice measurably beats matched random practice | **AGREE, Codex's framing is more precise; adopted below** | Finding 75 (prior session); not re-verified further this pass. |
| Developmental continuity | Not treated as a separate axis | Explicitly separated from competence accumulation as its own, third objective (task/evidence/commitment continuity across interruption) | **COMPATIBLE — a genuine addition, not a conflict** | Adopted in Part VII's claims ladder. |
| Accumulated competence | Not yet demonstrated; premature as the *immediate* target | Same conclusion, operationalized as "a claim supported by repeated retained improvements, not a phrase that determines every experiment in advance" | **AGREE** | — |
| Improved acquisition competence (learning-to-learn) | Not addressed as its own tier | Explicitly named as a *second*, harder, later objective, separate from ordinary competence accumulation | **COMPATIBLE — Codex's finer-grained tier structure is adopted in Part VII** | — |

## PART II — THE ACTUAL BOTTLENECK CHAIN

The proposed chain in the mission prompt is close but, once attacked against what's actually in the repository, needs one addition Codex's own diagram already makes and I confirm independently: **action/actor identity must be pinned *before* the outcome is observed, not reconstructed afterward.** `generate_code_from_plan` is a live, current counter-example to the assumption that this is already solved: it resolves `model_name` via `choose_model(task_type="self_edit_coding")`, then calls `echo_query(task_type="coding", ...)` **without binding that model into the call** — `echo_query` is free to internally select or synthesize across a different model or council, and the function nonetheless returns `(code, model_name)`, which downstream code (the four `learn_from_sandbox_outcome(model_name, ...)` call sites, confirmed at lines ~2041/2043/2081/2097) uses to attribute the sandbox's real pass/fail outcome. A code-level comment even says this was already "fixed" (v2.2, "so sandbox outcomes can be fed back into river with the correct model identity") — the fix addressed a plumbing bug (the name used to be lost entirely) but not the actual attribution bug (the name was never bound to what generated the code in the first place). **This is a real, currently-live instance of exactly the failure Codex's chain worries about, independently confirmed, not inferred from an old audit.**

Revised chain, with each link's status:

```
real attempt
  → independently verified outcome                         [WORKING — F2 sandbox pass/fail is a real, kernel-verified boolean]
  → correct identity/provenance of what produced the attempt [PARTLY BROKEN — CONFIRMED gap in generate_code_from_plan; OK elsewhere (RiverBrain's ordinary learn() calls, which pass model_name from the same call site that generated the response)]
  → credit assignment to the right STATE                    [BROKEN for the two real verified-outcome functions — CONFIRMED: learn_from_sandbox_outcome/learn_from_council_rating update the classifier, never model_task_stats]
  → partial or structured retention                         [ABSENT — every retention decision in this codebase (self-edit fitness gate, AP-0's draft/gate, council accept/reject) is whole-artifact binary]
  → consequential update to strategy/policy/skill state     [PARTLY WORKING — ordinary learn() does reach model_task_stats and does change score_model()'s output, just not from the verified-outcome path]
  → restart/context boundary                                [WORKING — RiverBrain persists and reloads (Finding 39 verification); self-edit's carrier (the file itself) persists trivially since it's just a file]
  → future state consumption                                [WORKING for RiverBrain's ordinary mean → choose_model()/score_model(); ABSENT for coupling_estimate (zero consumer, reconfirmed by grep this session against current source) and largely absent for memory retrieval (Finding 75/76, not independently re-verified this pass)]
  → improved later behavior at equal resource cost           [NEVER TESTED — no experiment in this repository has ever compared an adaptive policy against a frozen baseline at matched cost]
  → repeated accumulation                                    [NEVER TESTED, by construction, since the previous link was never tested]
```

**The single most consequential, newly-confirmed fact from this reconciliation:** the two links most people would assume are already solid — "verified outcome" and "credit assignment to the decision-controlling state" — are each real in isolation but **do not connect to each other** for the two mechanisms (sandbox F2 outcomes, council ratings) that most resemble genuine ground truth. The mean that actually controls model selection is fed almost entirely by a cheap syntactic quality heuristic (`_score_response_quality`), not by the system's own best verified signals. This is worse, not better, than either report's initial framing — my report treated RiverBrain as "a narrow but real, already-working example" without checking this; Codex's report named the general shape of the problem correctly and, on verification, was right about the specific mechanism.

## PART III — RIVERBRAIN AS THE CONTROL CASE

Established directly against source (`app/core/echo_model_orchestrator.py`), not assumed:

- **What updates it, exactly:** three distinct methods write to `RiverBrain`'s internal state, and they write to **different** parts of it. `learn(model_name, task_type, response)` — called from ordinary conversational/generation paths, including `generate_code_from_plan`'s self-edit generation call — scores `response` with a cheap syntactic/structural heuristic (`_score_response_quality`), updates the classifier/scaler, **and** updates `model_task_stats[model_name][task_type]["mean"]`/`["count"]`. `learn_from_sandbox_outcome(model_name, success, code, error)` — the one function fed by a real, kernel-verified pass/fail boolean (F2) — updates the classifier/scaler and a separate `sandbox_observation_counts` counter, and **does not touch `model_task_stats` at all**. `learn_from_council_rating(model_name, task_type, response_preview, council_rating, quality_score)` — fed by real peer-council ratings, gated on `is_council_trusted()` upstream — likewise updates only the classifier/scaler, **not `model_task_stats`**.
- **What state actually controls future selection:** `score_model(model_name, task_type)` — used by `choose_model()`'s ranking/entropy/exploration logic — reads **only** `model_task_stats[model_name][task_type]["mean"]`. It has no path to the classifier, the accuracy tracker, `sandbox_observation_counts`, or anything `learn_from_sandbox_outcome`/`learn_from_council_rating` ever touch.
- **Does the observation reflect independently verified outcomes, heuristics, ratings, or a mixture?** A mixture, but **the mixture never actually combines** — the part of RiverBrain that controls selection is fed almost entirely by the heuristic path (`learn()`'s `_score_response_quality`), and the two paths fed by genuinely independent verification (sandbox pass/fail, council rating) are functionally quarantined from that decision.
- **Does state persist across restart?** Yes, confirmed by prior verification in this codebase's own history (Finding 39's live-restart check) and unchanged in this session's reading of the persistence code path; not re-run live here since that would require a production restart, out of scope for a read-only reconciliation.
- **Is the actor receiving credit always the actor that produced the result?** No — `generate_code_from_plan` is a confirmed, current counter-example (Part II).
- **Known broken/indirect wires:** the sandbox→ranking-mean gap and the council-rating→ranking-mean gap (both newly confirmed this session); `coupling_estimate`'s zero-consumer status (re-confirmed by grep this session: no call site outside `echo_core.py`/`self_model_updater.py`'s own read reaches any decision).
- **Has its behavioral consequence been causally demonstrated?** Only for the heuristic-fed path — Finding 39's prior verification showed real score changes moving real selection outcomes. The verified-outcome-fed paths have **no** demonstrated behavioral consequence, because they don't reach the state that has one.

**The strongest claim justified, no stronger:** RiverBrain demonstrates that FeralEcho *can* run a real experience→evaluation→persisted-state→changed-selection loop, end to end, for one specific, cheap, heuristic-scored kind of evidence. It does **not** yet demonstrate that FeralEcho's *best, most-verified* evidence (sandbox pass/fail, council agreement) ever reaches that loop. This is a materially weaker claim than my own original report made, and I'm revising it here rather than defending the earlier framing.

**Smallest extension with genuine new capability, given this:** wire `learn_from_sandbox_outcome` and `learn_from_council_rating` into `model_task_stats` too — not as a wholesale replacement of the heuristic mean, but as a second, disclosed, separately-tracked statistic (e.g., `model_task_stats[model_name][task_type]["verified_mean"]`) that `score_model()` can optionally consult where enough verified observations exist, falling back to the heuristic mean otherwise (mirroring the existing `_MIN_MODEL_OBSERVATIONS` fallback pattern already in the code). This is small, additive, reuses the exact persistence/locking/fallback machinery already proven safe, and directly closes the specific wiring gap this reconciliation found — without inventing a new subsystem.

## PART IV — RECONCILE THE TWO PROPOSED PRIMARY EXPERIMENTS

**Attacking the suggested combined structure first, as instructed.** The suggested sequence (real history → verified outcomes → qualified induction/credit assignment → frozen rule → prospective test → equal-cost baseline → measured improvement) has a real flaw: it silently assumes the *same* induced object (a rule) is the right target for both a symbolic-induction test (Claude's direction) and a strategy-selection test (Codex's direction). They are not the same object. Claude's direction induces a **static, human-reviewed gating rule** (e.g., "don't self-edit within 30 minutes of an MLX crash cluster") — a one-shot artifact, checked once against a held-out future window, never updated again without a new human-reviewed cycle. Codex's direction requires a **live, continuously-updating policy** that changes its own future choices as new outcomes arrive, compared against a frozen baseline at matched cost. Forcing these into one pipeline would conflate "did we find one good static rule" with "does an online policy beat a frozen one," which are different claims needing different controls (a static rule needs a held-out time window; an online policy needs progressive/predict-before-update validation, per Codex's own citation of River's own documented pattern).

**Decision: D — one primary experiment plus one prerequisite/component test**, not a forced merger.

- **Primary (Codex's direction, adopted as primary):** outcome-conditioned strategy selection on a small, real, bounded workload, compared against the best frozen policy at equal cost. This is the more general, more scientifically central claim (it's the actual accumulated-competence question, narrowly and testably stated), and it's the one neither the RiverBrain-wiring fact nor AP-0's result rules out — if anything, Part III's finding sharpens exactly what it needs to fix.
- **Prerequisite component test (Claude's direction, demoted but not discarded):** the self-edit historical-rule induction test is smaller, cheaper, uses data that already exists, and — critically — **directly produces the "correct action/actor identity" and "verified outcome" inputs the primary experiment needs**, since it forces a clean read of `self_edit_attempt_ledger.jsonl`/`SELF_EDIT.log` with real timestamps and real F2 outcomes. Running it first is a cheap way to (a) get early, real signal on whether historical logs support this class of claim at all, and (b) surface any remaining data-quality problems (like the model-attribution gap just found) before they contaminate the more expensive primary experiment.

**Contamination controls required for either, made explicit and testable, not just named:**
- *Retrieval of historical answers*: the primary experiment's task set must be tasks the policy has never seen an answer to; the component test's rule must be evaluated only on a time window strictly after the rule was frozen.
- *Static configuration / fixed hand-written routing*: both experiments require the "best frozen policy chosen on development data" as an explicit competitor, not an implicit assumption that adaptation wins.
- *More compute/retries*: budgets must be equalized and reported, per Codex's explicit requirement — this needs to be a hard, checked constraint, not a stated intention.
- *Benchmark contamination*: no task whose answer or outcome appears anywhere in AP-0's or the component test's own training data may appear in either experiment's held-out set.
- *Task-specific memorization*: features available to the policy/rule must be restricted to information available *before* the action (Codex's explicit requirement, adopted directly) — no task IDs, no peeking at the hidden outcome.
- *Actual experience-dependent improvement*: the discriminating comparison is always against a reset/shuffled-feedback control (does the *content* of the feedback matter, or would any persistent-seeming state look the same) — this closes the same "naive lookup" attack AP-0's own mutation suite used, generalized to this new setting.

## PART V — CREDIT ASSIGNMENT

Both layers are real and independently confirmed this session, and they are not the same problem:

1. **Actor/strategy credit** (Codex's concern) — confirmed broken in a specific, live, current mechanism (`generate_code_from_plan`'s model-name/`echo_query` mismatch; Part II). This is about *which decision-maker* gets blamed or rewarded for an outcome.
2. **Artifact/component credit** (my concern) — confirmed by the self-edit fitness gate's binary accept/reject structure and by AP-0's own K3 evidence (partial correctness on the "add" operation family, discarded wholesale rather than selectively retained). This is about *which part of what was produced* deserves credit.

**Minimum version required for the next experiment (Part IX), not a general system:** for the primary strategy-selection experiment, only **layer 1** is strictly required — the experiment already operates at the level of "which strategy was chosen," so correct actor/strategy identity is load-bearing from the start (get this wrong and the whole experiment measures noise), while component-level partial credit is out of scope (there's no sub-artifact to partially credit in a strategy-selection choice). For the component test (self-edit historical rule), **neither** layer is strictly required in its minimal form, since it operates on already-labeled whole-attempt outcomes (success/fail) rather than partial artifacts — but if it's extended later to explain *why* an attempt failed, layer 2 becomes relevant. Building a general-purpose credit system now is not justified by current evidence; both experiments can proceed with layer-1-only, applied narrowly.

## PART VI — SIGNAL AND PHYSIOLOGY GATE

Evaluated specifically against what the proposed primary experiment (Program 1 / outcome-conditioned strategy selection) would actually consume — not the whole Global Workspace inventory, per the instruction not to require unrelated cleanup:

**MUST FIX/RETIRE BEFORE EXPERIMENT:**
- The RiverBrain wiring gap itself (Part III) — if the experiment's "verified outcome" signal is meant to include sandbox/council-verified evidence rather than only the heuristic mean, the gap identified here must be closed (or explicitly worked around) first, or the experiment will silently fall back to measuring the heuristic path only.
- Correct actor/strategy binding in whatever code path the experiment's chosen strategies run through (a scoped fix, not a rewrite of `generate_code_from_plan` — the experiment can use its own clean call sites rather than inheriting self-edit's).

**CAN DEFER (real, but not load-bearing for this specific experiment):**
- `coupling_estimate`'s zero-consumer status — irrelevant unless the experiment's policy features include it.
- The three previously-saturated `emergent_scheduler.py` thresholds — already partially recalibrated (Finding 77) and not part of a strategy-selection policy's natural feature set.
- Memory retrieval's measured near-null effect (Finding 76) — irrelevant unless the experiment's policy consumes retrieved memory as a feature, which it should not by default given the null result.

**IRRELEVANT TO THIS EXPERIMENT:**
- `VectorMemory.add`'s duplicate-ID metadata bug (Codex's finding) — a real defect, unrelated to strategy selection.
- Reflection-shard near-duplication rate, autonomous curriculum saturation — unrelated to this experiment's scope.

## PART VII — CLAIMS LADDER

| Level | Minimum evidence required | Where FeralEcho currently sits |
|---|---|---|
| 1. Persistent state | A value survives a process restart, verified by direct read, not self-report | **MET** — RiverBrain's `model_task_stats`, self-edit's file-based carrier, AP-0's frozen artifacts all independently demonstrate this. |
| 2. Behavioral consequence of persistent state | The persisted value provably changes a later decision, shown by a direct before/after comparison | **PARTIALLY MET** — true for RiverBrain's heuristic-fed mean → `score_model()` → `choose_model()` (Finding 39's prior verification); **not met** for the verified-outcome-fed paths (Part III) or `coupling_estimate`. |
| 3. Experience-dependent adaptation | The behavioral change's *content* is shown to depend on the specific experience, not just its presence (a reset/shuffled-feedback control fails to reproduce the effect) | **NOT MET anywhere in this codebase yet** — no experiment in the repository has run this control. |
| 4. Bounded system learning | Level 3, plus a real comparison against a frozen baseline at equal cost, on a task the system wasn't specifically tuned for | **NOT MET** — this is exactly what Part IX's minimal experiment is designed to test. |
| 5. Reusable skill/abstraction accumulation | A component learned from one task is shown to causally help a *different*, genuinely novel composition, beyond what full-solution retrieval would already provide | **NOT MET** — nothing in the repository attempts this yet (Codex's Program 2, correctly scoped as a later escalation). |
| 6. Accumulated competence | Level 4 or 5, demonstrated repeatedly, without measurable loss of prior gains, across multiple independent cycles | **NOT MET** — no cycle has even completed level 4 once. |
| 7. Improved acquisition competence / learning-to-learn | Prior experience is shown to *reduce* the evidence/attempts/compute needed on a later, structurally novel task, relative to a matched fresh-start baseline | **NOT MET, NOT ATTEMPTED** — correctly scoped by both reports as a much later target. |
| 8. Developmental continuity | Relevant commitments, evidence, and unfinished work are shown to be preserved and coherently revised across an interruption, independent of whether any "learning" occurred | **PARTIALLY MET at best** — real persistence mechanisms exist (snapshots, ledgers, the Liveness Ledger), but no experiment has tested coherent revision under changed circumstances; Codex's "periodic activity is not a resumable goal system" finding (stub `schedule_task`/`run_pending`) argues against overclaiming this. |

No level here requires a neural-weight change; every level is stated in terms of the causal level where the claimed change actually occurs, per the mission's explicit instruction.

## PART VIII — OCTOBER 1 PLAN

Nine days (2026-09-22 → 2026-10-01). Optimized for scientific leverage and continuity, not for a positive result by the deadline. Each phase has a hard STOP/GO gate; a STOP at any gate means the *next* phase doesn't run, not that the whole plan collapses — earlier phases' outputs (the succession package, the frozen workload/task set) remain valuable regardless.

**Day 1 (today/tomorrow) — Close the confirmed wiring gaps that would contaminate anything built on top of them.**
Fix, with a shown diff and explicit review (not defaulted into): (a) `generate_code_from_plan`'s model-attribution gap — either bind the resolved model into `echo_query`'s call or stop attributing `learn_from_sandbox_outcome` calls to a name that wasn't actually bound; (b) add the `verified_mean` extension to `model_task_stats` sketched in Part III, wired from `learn_from_sandbox_outcome`/`learn_from_council_rating`, additive and fallback-safe. **GATE:** both fixes verified against real data (a real sandbox call correctly updates the new field; `generate_code_from_plan`'s returned model name is now provably the one that generated the code) before Day 2. If either fix can't be verified cleanly in one day, stop and use the remaining time for the succession package instead — do not let this slip into the experiment's own budget.

**Days 2–3 — Freeze the primary experiment's workload, task set, and contamination controls.**
Choose a small, real, bounded Python-repair/transformation workload (per Codex's §9 sketch); freeze the task set, the fixed strategy set (direct generation, one verified-repair attempt, one alternate approach), and every contamination control from Part IV, in a written, hashed preregistration — same discipline AP-0 already established. **GATE:** the preregistration document exists, is hashed, and states the STOP/GO threshold *before* any real data is collected. If the workload can't be scoped small enough to fit the remaining budget, narrow it further rather than slip the timeline.

**Days 4–6 — Run the component test (Claude's direction) as a cheap, parallel-track prerequisite, and begin the primary experiment's baseline collection.**
Run the self-edit historical-rule induction test on real logs, held out on a strictly later time window (a few hours of analysis, not model calls — this is nearly free). Concurrently, collect the primary experiment's frozen-baseline data (the "best frozen policy" and fixed-strategy comparators) — this is real model-call cost but bounded by the frozen task set's size. **GATE:** both produce real, disclosed results (positive or negative) by end of Day 6. A negative component-test result is not a stop condition for the primary experiment — they're independent, per Part IV's decision.

**Days 7–8 — Run the primary experiment's adaptive condition and the required controls (reset state, shuffled feedback) at matched budget.**
**GATE (hard, predeclared):** apply the STOP/GO threshold from Day 2's preregistration. If the adaptive condition doesn't beat the frozen baseline by a practically meaningful margin accounting for uncertainty, or if the reset/shuffled controls reproduce the same effect, **stop and report a negative result plainly** — do not extend the experiment past the deadline chasing significance.

**Day 9 — Finalize the succession package and close out.**
Regardless of the experiment's outcome, produce the succession package (below) and a final status report. This is not optional and does not depend on the experiment's result.

**Claude succession package — must exist before October 1, regardless of experiment outcome:**
1. A single current-state document (or a clearly-dated pointer into CLAUDE.md/PENDING_DECISIONS.md) stating: what's running, what's stopped, what's frozen/preregistered, and the exact resume commands for anything in flight (mirroring this session's own AP-0 resume-from-ledger pattern).
2. The two independent reassessments, this reconciliation, and the primary experiment's preregistration and results, cross-linked.
3. A precise list of every known-live gap this reconciliation surfaced (the RiverBrain wiring gap, the `generate_code_from_plan` attribution gap, `self_edit_generated.py`'s currently-deployed hook and its (4,4)-ceiling gate, `coupling_estimate`'s dead consumer, `VectorMemory.add`'s duplicate-ID behavior) with file:line references, so a future agent doesn't have to rediscover them.
4. The exact commands to check system health (`safe_restart.sh`, `/admin/liveness-status`, the verify scripts for AP-0/QUAL) and the standing operating rules (report-then-pause, diff-before-touching-forbidden-files, don't restart Echo without checking for a live watchdog).
5. Git HEAD and a clean `git status` at the moment of handoff, so continuity of provenance doesn't depend on any conversational memory.

**Local inference/backend independence — read-only investigation only, does not displace the primary program:** spend at most part of one day (folded into Day 9, not a separate phase) documenting, without modifying anything: which exact model names/digests the live system depends on (Ollama, MLX), whether an equivalent local backend (llama.cpp, MLX-LM directly) could serve the same model files if Ollama became unavailable, and where that dependency is concentrated in code (`ollama_client.py`, `mlx_handler.py`). This is a documentation task, not an integration — write it down, don't build a fallback, and stop immediately if it threatens to consume more than the allotted slice of time.

## PART IX — MINIMAL FIRST IMPLEMENTATION (SPECIFIED, NOT IMPLEMENTED)

**Causal hypothesis:** a small, online contextual policy that consumes real, verified outcomes from FeralEcho's own bounded Python-repair workload will select among a fixed, small set of strategies (direct generation / one verified-repair attempt / one fixed alternate approach) better than the single best strategy chosen in advance, at equal inference budget.

**Primary endpoint:** proportion of tasks solved correctly (independently verified, e.g. by real test execution) under a fixed total inference-call budget, on a held-out task set never used to develop the policy or the frozen baseline.

**Frozen baseline:** the single best-performing fixed strategy, chosen on a separate development split, never updated during evaluation.

**Equalized budget:** total model calls (or token-equivalent cost) capped identically across the adaptive policy, the frozen baseline, a fixed same-budget retry policy, and a permuted-feedback control.

**Actor provenance:** every response bound at generation time to the exact strategy/model that produced it — closing the specific gap found in Part II, not inheriting `generate_code_from_plan`'s existing mechanism.

**Independent outcome evaluation:** real execution against held-out tests, in the existing sandboxed runner (F2's mechanism, reused, not reimplemented) — never the policy's or generator's own self-report.

**Prospective/held-out evaluation:** predict-then-reveal on a sequential task stream (River's own progressive-validation shape, cited by Codex), plus a genuinely later, untouched task batch.

**Restart/context boundary:** the policy's learned state is persisted and reloaded from a real process restart before the held-out evaluation batch runs, mirroring RiverBrain's own already-proven persistence mechanism.

**Contamination controls:** exactly the list in Part IV — no repeat tasks from AP-0/Tier-4, no task-ID or hidden-answer features, held-out tasks never seen by the policy in any form before evaluation.

**Explicit failure interpretation:** stated per Part VIII's outcome table before any data exists — "adaptive ≈ frozen" means the policy adds nothing at this scale (a real, useful negative result); "adaptive < frozen" means the policy is actively harmful (stop and revert); "reset/shuffled control matches the real result" means whatever gain exists isn't experience-dependent.

**Predeclared STOP/GO threshold:** a practically meaningful improvement over the frozen baseline (not merely nominally positive), with uncertainty accounted for at the task level, decided and written down before Day 7's run per Part VIII.

**Rollback/reversibility:** the policy is purely additive — it selects among existing strategies, never modifies self-edit, RiverBrain's existing state, or production routing; if it fails, deleting its output changes nothing else.

**No self-report as ground truth:** every outcome is a real, independently executed test result, never a model's own claim about its output.

**Estimate:** implementation complexity — small (a CPU-only online classifier/bandit over a handful of features, reusing River's own library already in the dependency tree); model-call cost — bounded by the frozen task set's size times the number of conditions (adaptive, frozen baseline, retry control, shuffled control), realistically low hundreds of calls, similar order of magnitude to AP-0's QUAL-1 gate phase; runtime — comparable to AP-0's gate phase (roughly an hour to a few hours, depending on task-set size); major risks — the task set being too small to produce a statistically meaningful comparison (mitigated by choosing task count against a precomputed minimum-detectable-effect, the same discipline AP-0's own prereg used), and the frozen baseline being hard to beat at all (a real possibility Codex's report treats as a legitimate, useful outcome, not a failure of the experiment).

## PART X — ADVERSARIAL SELF-REVIEW

**Strongest non-learning doppelgänger:** if the adaptive policy "wins," the most boring explanation is that the fixed task set has a small number of task *types*, and the policy is doing nothing more than **memorizing which strategy works for which superficial task-type signature** (e.g., "tasks whose docstring contains the word 'sort' always favor strategy B") — a lookup table dressed as a contextual policy, exactly AP-0's own "the constructor already contains the answer" attack, recurring one level up.

**Can it be killed with available resources?** Partially. The genuinely-held-out, strictly-later task batch (already in the design) directly attacks this: a pure lookup table built on development-split task-type signatures should fail to transfer to held-out tasks whose signatures weren't in the development set, while a real contextual policy that's actually using outcome information should degrade more gracefully. The reset/shuffled-feedback control also helps: a lookup table built from real feedback should collapse under shuffled feedback, same as a real policy would — so this control alone doesn't fully distinguish them. **The doppelgänger cannot be fully killed with this design as specified** — a large-enough table could still generalize across a small task-type space by coincidence, and this experiment's budget doesn't support a task set large and diverse enough to rule that out with confidence.

**Revision, or narrowed claim:** rather than inflate the design to chase this (more task diversity than the nine-day budget supports), **narrow the claim in advance**: a positive result under this design should be reported as *"a policy conditioned on real outcomes outperformed a frozen baseline on this specific bounded workload, at this task-set scale"* — explicitly not generalized to "FeralEcho learns," and explicitly flagged as consistent with, and not yet distinguished from, a superficial-signature lookup table at this scale. Distinguishing the two properly is the natural next escalation (a larger, more diverse task set), not something to claim solved by the first run.

---

### RECONCILIATION VERDICT
The two independent assessments converge on the top-level decision (demote AP-0, make outcome-conditioned adaptation the primary target, treat accumulated competence as an unearned long-term hypothesis) and on most of the diagnosis, but they differ in resolution: Claude's report treated RiverBrain as an already-working proof of the target mechanism, while Codex's report — confirmed directly against source during this reconciliation — showed that the specific, most-verified evidence RiverBrain receives (sandbox pass/fail, council ratings) never reaches the state that actually controls model selection, which is instead driven almost entirely by a cheap syntactic heuristic; this is a genuine, material correction to Claude's report, not a difference of emphasis. The two reports' distinct proposed experiments (Codex: outcome-conditioned strategy selection; Claude: symbolic induction over self-edit history) are compatible as a primary-plus-prerequisite pair rather than competitors, and their two credit-assignment concerns (actor-level vs. component-level) are both real and independently confirmed, operating at different layers of the same underlying problem.

### PRIMARY BOTTLENECK
FeralEcho's genuinely verified outcomes (sandbox pass/fail, council agreement, and AP-0's own gate results) are real but structurally disconnected from the specific persisted state that controls the system's future choices — the state that does control choices is instead fed by a cheap, unverified heuristic — and no experiment anywhere in the repository has ever compared an adaptive policy against a frozen baseline at equal cost to show this connection, once made, would actually help.

### AP-0 STATUS
COMPONENT TEST

### PRIMARY RESEARCH PROGRAM THROUGH OCTOBER 1
Close the two confirmed credit/attribution wiring gaps (RiverBrain's verified-outcome-to-ranking-mean gap; `generate_code_from_plan`'s model-attribution gap), then run one small, preregistered, outcome-conditioned strategy-selection experiment on a bounded real workload against a frozen baseline and the required reset/shuffled/retry controls, with a real self-edit-history rule-induction test run in parallel as a cheap, independent, lower-stakes prerequisite that exercises the same real data and the same contamination discipline.

### FIRST EXPERIMENT
A small online contextual policy chooses among a fixed set of existing strategies (direct generation, one verified-repair attempt, one alternate approach) on a bounded, real, held-out Python-repair workload, evaluated by real test execution under a budget matched exactly against the best frozen fixed strategy, a fixed retry policy, and a permuted-feedback control, with actor provenance bound at generation time and the policy's state required to survive a real process restart before the final held-out evaluation.

### CLAIM IT COULD ESTABLISH
That FeralEcho's own verified task outcomes, at this specific bounded scale, causally improve its choice among existing strategies beyond the best fixed policy at equal cost — a real, if narrow and bounded, instance of system-level learning.

### CLAIM IT COULD NOT ESTABLISH
That FeralEcho accumulates competence generally, forms reusable abstractions, improves its own ability to learn, or that any result is distinguishable with confidence from a superficial task-signature lookup table at this task-set scale.

### TOP THREE PRIORITIES BEFORE OCTOBER 1
1. Fix and verify the two confirmed wiring gaps (RiverBrain's verified-outcome-to-ranking-mean disconnect; `generate_code_from_plan`'s model-attribution mismatch) before building anything on top of either.
2. Freeze and run the single outcome-conditioned strategy-selection experiment (Part IX) with its predeclared STOP/GO threshold, treating a clean negative result as a genuine, valuable outcome.
3. Produce the Claude succession package (Part VIII) regardless of the experiment's outcome, so continuity does not depend on this conversation.

### CLAUDE SUCCESSION REQUIREMENT
Before October 1: a single, current, dated status document (or a clearly-pointed section of CLAUDE.md/PENDING_DECISIONS.md) stating exactly what is running, stopped, frozen, or preregistered, with resume commands for anything in flight; both independent reassessments and this reconciliation cross-linked; a plain list of every confirmed live gap this reconciliation found, with file:line references; the exact health-check and restart commands and standing operating rules; and a clean, recorded git HEAD/status at the moment of handoff — sufficient for another capable coding agent to continue without relying on this conversation's memory.

### IMPLEMENTATION AUTHORIZATION
NOT AUTHORIZED
