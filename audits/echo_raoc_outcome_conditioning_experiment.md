# Retrieval-Augmented Outcome Conditioning (RAOC) — Pre-Registered Protocol

**Status: DESIGN ONLY. Not implemented. Not run. Live Echo was not invoked at any point in producing this document.** This protocol is not yet sealed — it is presented for Gremlin's explicit review and sign-off before any implementation or trial. Per this thread's own established discipline (the P0.1/P0.2 preference-formation protocols), design, pilot, and full-run authorization are three separate gates; this document delivers the design only.

Evidence standard, matching the preference-formation thread: **FACT** / **INFERENCE** / **SPECULATION**, labeled throughout.

---

## 1. Executive Summary

CLAUDE.md's Finding 89/91 conversation identified a real gap in the existing evidence base: `audits/echo_learning_hollow_writes.md`'s autopsy and the P1.2 preference-formation result both establish that **nothing currently tested surfaces a real, verified outcome as usable context for a new generation.** RiverBrain affects which model is asked, never what gets said. The existing memory-retrieval system surfaces semantically *similar* past text, not verified *outcomes*. P1.2 tested raw preference persistence with **no informative mechanism in the loop at all** — Echo was never given anything true to act on, so its null result answers "does anything happen spontaneously," not "can anything happen given real, actionable information."

**RAOC tests the one architecturally distinct lever nobody has tried yet**: does explicitly retrieving a *verified* past outcome (a real pass/fail result, not a similarity match) and injecting it as in-context conditioning for a new, related task produce a measurable, replicating, directionally-correct behavior change? This is deliberately a narrower, more mechanistic question than the preference-formation thread's — it does not ask whether Echo has an emergent preference; it asks whether a real information channel that could *support* one currently does anything at all when the information is actually supplied.

**Why this must run before fine-tuning is considered** (per Gremlin's explicit framing, 2026-09-05): fine-tuning is authorized only as a last resort, after architectural weaknesses are ruled out. A null result on RAOC — a real, informative signal, explicitly surfaced, producing no measurable behavior change — would be considerably stronger evidence that the architecture itself cannot support behavior change without touching weights than P1.2's null result alone, since P1.2 never tested a condition with real information present. A positive result would mean a cheap, non-fine-tuning path exists and should be built out before fine-tuning is entertained at all.

## 2. Current Evidence Boundary (Carried Forward, Not Re-Derived)

From `echo_learning_hollow_writes.md`, `echo_learning_causal_autopsy.md`, and the P1.2 live validation report, treated as established unless this design finds contradicting evidence (it does not):

- RiverBrain's only causally-live path (`learn()` → `model_task_stats` → `score_model()`) affects model *selection*, never response *content* — confirmed, not inferred, by direct source read.
- Existing memory retrieval (`retrieve_relevant_memories()`) is similarity-based against past *text*, with no concept of verified *outcome* attached to what it surfaces, and its measured effect (the 2026-07-23 ablation) was only tested on `personal`-type tasks, never on tasks with an objective, checkable answer.
- P1.2 (real, live, forced-choice trial): Echo's retention-phase answer flipped with the re-randomized *label*, not the previously-engaged *content* — direct evidence against spontaneous preference retention under a paradigm with **zero real informative content supplied**. This is the exact gap RAOC targets: P1.2's null says nothing about what happens when real information *is* supplied, because none ever was.
- The `app/experiments/preference_provenance/` harness's own architecture map (`echo_preference_formation_retention_experiment.md` §5) confirms Design B (`_ollama_query()` direct call, no council, no RiverBrain mutation, no logging) is the clean, low-contamination path this thread has already validated for controlled single-model trials — reused here for the same reasons.
- Separately, Tier-3/4's own apparatus (`scripts/run_capability_pilot.py`) already has a real, working, objective outcome-verification mechanism: `objective_verify(candidate_code, test_code)` — runs generated code against a real, frozen test suite in the same sandboxed path self-edit's own F2 uses, returning genuine pass/fail, not a heuristic. **This is the ground-truth outcome generator RAOC needs and does not have to build from scratch.**

## 3. Research Question

> When Echo is given a new, objectively-checkable coding task, and is explicitly told a real, verified outcome from a prior attempt at a related task (which specific approach passed or failed, and why), does her new candidate's approach measurably and reproducibly shift in the direction the verified outcome would rationally suggest — beyond what an equally-long but uninformative or fabricated statement would produce?

This is not a test of preference, persona, or agency. It is a test of whether a real, currently-unused information channel — verified-outcome-as-context — has any causal effect on output at all.

## 4. Hypotheses

**H1 — Outcome-conditioning hypothesis.** Presenting Echo with a real, verified outcome from a related prior attempt measurably shifts her new candidate's approach in the direction that outcome supports, relative to an uninformative or fabricated control, and this shift replicates.

**H0 — No causal effect.** Any apparent shift is fully explained by response-length effects, generic "recency of mentioned concept" priming (the model echoes whatever was most recently discussed, true or not), task-family idiosyncrasy, or random variation — i.e., the informational *truth* of the injected outcome carries no special weight beyond its surface content being present in context at all.

**Competing hypotheses, not collapsed into H0/H1:**

- **H0a — Generic priming, not outcome-sensitivity.** Any injected text about a specific approach (true, false, or fabricated) shifts behavior toward mentioning/avoiding that approach, regardless of whether it's framed as a success or failure — the model reacts to *topical salience*, not to the verified *valence* of the outcome. Distinguished from H1 by the sham-outcome control (§10) directly reversing the stated valence.
- **H0b — Instruction-following, not conditioning.** Echo treats an injected "this failed, avoid it" statement as a direct instruction to comply with, structurally indistinguishable from being told "do not use approach X" outright — a real, useful behavior, but not evidence that *outcome verification specifically* (as opposed to any imperative-sounding text) is doing the work. Distinguished from H1 by an explicit non-imperative phrasing variant (§8) stating the outcome as fact without any directive language.
- **H1a — Genuine but shallow outcome-sensitivity.** A real, measurable, replicating shift exists, but is fully explained by H0a or H0b under adversarial testing — real evidence of *a* mechanism, not evidence that this project's specific verified-outcome architecture is what's driving it.
- **H1b — Genuine, mechanism-specific outcome-sensitivity.** A real, replicating shift exists that survives both the sham-outcome and non-imperative-phrasing controls — the strongest result this design can support, and the one that would justify building this into a real, live pipeline before considering fine-tuning.

## 5. Architecture Map (Verified This Pass)

| Component | How it works | File:function | Relevant to this experiment |
|---|---|---|---|
| Direct single-model call | `_ollama_query(model, prompt, system=..., task_type=...)` — no council, no RiverBrain, no logging | `app/core/river_deliberation.py` | Primary path, same as the preference-formation thread's Design B — zero persistence, zero retrieval, isolates the injected-context manipulation cleanly |
| Objective outcome verification | `objective_verify(candidate_code, test_code)` — real sandboxed execution against a real, frozen test suite | `scripts/run_capability_pilot.py` | **The ground-truth generator this experiment needs** — reused directly, not reimplemented, to produce the real verified outcomes that get fed back in as context on a *later*, related task |
| Tier-4's frozen task pool | 84 real, verification-tested coding tasks across 6 categories | `audits/tier4_apparatus/` | Reused as the source of both the "prior attempt" task (whose real outcome gets verified and injected) and the "new" task (whose candidate is measured) — already exists, already objectively scored, no new task authoring needed |
| Preference-provenance harness's leakage/randomization conventions | Label randomization, append-only raw-trial logging, leakage scanning | `app/experiments/preference_provenance/` | Reused for trial bookkeeping and leakage checks (does the injected outcome statement leak the "expected" answer to the new task directly, rather than just informing it) |
| RiverBrain | In-process `model_task_stats` mutation | `app/core/echo_model_orchestrator.py` | Avoided entirely — Design B does not invoke it |
| Memory retrieval | `retrieve_relevant_memories()` | `app/core/memory_bridge.py` | Not used — the injected outcome is supplied directly by the harness, not retrieved, so this experiment isolates "does surfaced information help at all" from "can the retrieval system find the right information," a separate and harder question deliberately out of scope here |

## 6. Experimental Design Overview

Two-task-pair structure per trial, not the three-phase Baseline/Formation/Retention structure of the preference-formation thread (that structure fits a values-neutral choice; this experiment has an objective right answer, which changes what needs controlling for):

```
Step 1 (Outcome generation) — a real coding task attempt is run and
  objectively scored via objective_verify() — this produces the REAL,
  VERIFIED outcome to be injected later. Done once per task-pair,
  reused across all conditions for that pair (the outcome is fixed
  ground truth, not re-generated per trial).

Step 2 (Conditioned generation) — a NEW, related-but-distinct coding
  task is presented to Echo under one of four conditions (§7), and the
  resulting candidate is objectively scored the same way.
```

Task pairs are constructed so the "related" task shares an approach-relevant property with the outcome task (e.g., both are solvable via either an iterative or a recursive approach, and the outcome task's real, verified result concerns which approach worked) — **not** the same task restated, which would make this a memorization test rather than a conditioning test.

## 7. Conditions (Four, Not Two — the Sham-Outcome Control Is Load-Bearing)

| Condition | What's injected before the new task | Purpose |
|---|---|---|
| **Control (no context)** | Nothing — baseline candidate generation, identical to how Tier-4's own apparatus already runs | Establishes the unconditioned baseline approach distribution |
| **True outcome** | The real, verified result from Step 1, stated factually: *"On a related task, an approach using [X] failed — [real, specific reason from the actual sandbox output]."* or *"...passed all tests."* | The real treatment condition — tests H1 |
| **Sham outcome (reversed valence)** | The *identical* task-1 approach description, but with the stated outcome deliberately reversed from what `objective_verify()` actually found | Distinguishes H1 (responds to true outcome) from H0a (responds to any topical mention regardless of truth) — **this is the single most important control in this design** |
| **Sham outcome (irrelevant)** | A same-length, same-format outcome statement about a genuinely unrelated approach/task | Controls for pure length/format effects independent of topical relevance at all |

All four conditions are presented as **non-imperative, factual statements** — never "avoid X" or "use Y" — specifically to separate H1 from H0b (instruction-following). A fifth, explicitly-imperative variant (*"Do not use [X]"*) is specified as an optional fifth condition, run only if the four-condition result needs disambiguating from instruction-following after the fact — not part of the primary pre-registered comparison, to avoid inflating the family-wise error rate on the core test.

## 8. Task Pair Construction

Reuses Tier-4's real, already-verification-tested 84-task pool (`audits/tier4_apparatus/tier4_stage{1,2}_task_suite.json`) rather than authoring new tasks — every task's real, objective test suite already exists. Task pairs are selected, not authored: two tasks from the same category (e.g., both "data-transformation") where a genuine, real implementation choice exists (iterative vs. recursive, dict-based vs. list-based, etc.) and where Step 1's real historical `mechanism_calls` data (already captured, per Tier-4/5/6/7's shared corpus) shows at least one real candidate took each approach with a real, differing pass/fail result — **no new model generation needed for Step 1 in the common case**, since the real outcome may already exist in the already-captured Tier-4 corpus. Where no suitable real historical pair exists for a category, Step 1 is run fresh, once, and the result frozen for reuse across all trials/conditions for that pair.

Minimum 3 independent task pairs (matching the preference-formation thread's "must replicate across families" discipline), each pair used across all four conditions.

## 9. Confound Matrix

| Confound | Could it mimic H1? | Control |
|---|---|---|
| Generic topical priming (H0a) | Yes, the central risk | Sham-outcome (reversed valence) condition — same topic, opposite truth value |
| Instruction-following (H0b) | Yes | Non-imperative phrasing throughout the primary four conditions; imperative phrasing isolated to an optional fifth condition |
| Length/format effect | Yes | Sham-outcome (irrelevant) condition — same length/format, no topical relevance |
| Task-pair idiosyncrasy | Yes | Minimum 3 independent pairs, each analyzed independently before pooling (§11, criterion 3) |
| Memorization (task 2 is really task 1 restated) | Would inflate apparent effect artificially | Task pairs explicitly constructed to be related-but-distinct; a leakage check (reused from the preference-provenance harness) confirms task 2's real test suite doesn't overlap with task 1's |
| Model/sampling variance | Always present | Multiple trials per condition per pair; temperature held constant across conditions within a pair |
| Experimenter bias in outcome-statement wording | Real risk | Outcome statements for True/Sham-reversed/Sham-irrelevant are template-generated from `objective_verify()`'s real output fields, not hand-written per trial, so the same generation logic produces all three, differing only in which real/fabricated result is substituted |

## 10. Randomization / Blinding

- Task-pair-to-condition assignment randomized and logged per trial (reusing the preference-provenance harness's existing `batch_seed`/`trial_index` fields).
- Which of the 3+ pairs' real Step-1 outcome is "true" vs. used as the basis for a "reversed" sham is fixed by the real `objective_verify()` result — not chosen by the researcher per trial.
- Scoring (does the Step-2 candidate pass its real test suite, and does its approach match the outcome-supported direction) is fully mechanical: `objective_verify()` for pass/fail, and a simple, pre-specified static check (e.g., "does the candidate use recursion," an AST-detectable property, not a judgment call) for approach classification — no human scoring judgment involved, avoiding the blinding gap the preference-formation thread had to design around separately.

## 11. Quantitative Success Criteria (Pre-Registered)

**A candidate "pass" (evidence supporting H1) requires ALL of the following:**

1. The True-outcome condition shows a statistically detectable shift in approach-classification (toward the outcome-supported approach) relative to the no-context Control, using the same two-proportion test convention the preference-formation thread's `classify_effect()` already establishes (reused, not reinvented).
2. The True-outcome condition's shift is **significantly different from** the Sham-outcome (reversed valence) condition's shift — not just "True differs from Control," since Sham-reversed sharing the same topic but opposite truth is what actually isolates H1 from H0a. This is the single required comparison, not optional.
3. The shift replicates across at least 2 of the 3+ independent task pairs, analyzed separately, not pooled.
4. The Sham-outcome (irrelevant) condition shows no significant shift from Control — confirming the effect isn't a generic "any injected text changes behavior" artifact.
5. Objective task-2 pass rate is reported alongside approach-classification for every condition — a shift toward the "right" approach that does NOT improve real pass rate is reported as a real but narrower finding (behavioral shift without a demonstrated quality benefit), not silently treated as equivalent to one that does.
6. Minimum 20 trials per condition per task pair (240 minimum across 3 pairs × 4 conditions), a conservative starting point stated honestly as not power-calculated from a prior effect-size estimate, matching this thread's own established practice of not manufacturing false precision.
7. Replication: any pair showing an initial pass is re-run once more (independent seed) before being reported as more than "observed once."

**If any of these fail, the result is reported as "does not meet the pre-registered bar for H1," not softened.**

## 12. Failure Criteria (Explicitly Valuable, Not a Bug)

- No shift in any condition relative to Control → clean null: the architecture does not causally use verified-outcome context at all under this design. Given P1.2's own null and this result together, this would be real, compounding evidence that the *architecture*, not just the *specific untested mechanism*, is the limiting factor — the strongest evidence this thread could produce before considering fine-tuning.
- Shift present, but identical in True vs. Sham-reversed → H0a (generic priming), not H1. Reported as a real, separate, and still-useful finding (Echo's generation is topically steerable) — just not evidence of outcome-sensitivity specifically.
- Shift present only when phrasing is imperative → H0b (instruction-following), not H1 — also a real, useful, separately-reportable finding.
- Shift present but doesn't replicate on the second run → non-replicating, reported as such.
- Shift present in only one of three pairs → task-pair-specific, not general.

## 13. Adversarial Attack Analysis

**"If I desperately wanted to prove outcome-conditioning works, how could I fool myself?"**
1. Make the True-outcome statement much more detailed/specific than the Sham conditions, so any effect is really a specificity effect. — *Controlled by template-generating all outcome statements from the same real `objective_verify()` output-field structure, varying only which result is substituted.*
2. Pick task pairs where the "obviously better" approach is telegraphed by the task description itself, independent of any injected outcome. — *Controlled by requiring the Control condition's own baseline approach distribution not already be significantly skewed toward the outcome-supported approach (an explicit pre-check, mirroring the preference-formation protocol's Phase-A-skew check).*
3. Under-power the Sham-reversed condition so it never shows the divergence from True that it should if H0a is false. — *Controlled by running Sham-reversed at the identical sample size as True (§11, criterion 6 applies to all four conditions equally).*
4. Report only the task pairs that showed the effect. — *Controlled by the append-only raw-trial log (reused from the preference-provenance harness) and the explicit "each pair reported independently" requirement (§11, criterion 3).*

**"If I desperately wanted to prove outcome-conditioning does NOT work, what legitimate signal could I accidentally suppress?"**
1. Setting the approach-classification check so narrowly (e.g., requiring an exact structural match) that a real, genuine shift in strategy that doesn't happen to match the pre-specified AST pattern gets missed entirely. — *Named as a real risk; the pre-specified static check (§10) is deliberately simple and coarse, which cuts both ways — flagged honestly rather than assumed adequate.*
2. Choosing task pairs where the "related approach" connection is too subtle for any reasonable in-context conditioning to bridge, and concluding the mechanism doesn't work when really the specific pairs were too hard. — *Controlled by using real, already-observed historical pairs (§8) wherever they exist, rather than researcher-invented pairs that might be needlessly obscure.*
3. Treating a real quality/pass-rate improvement without a matching approach-classification shift as a non-result. — *Controlled by §11 criterion 5 reporting both measures independently rather than requiring both to move together.*

## 14. Evidence Level Justified by Each Outcome

Using the E0–E9 ladder from `measurability_and_longitudinal_evidence_audit.md` §6, mapped to the specific edge this experiment targets (`echo_agency_architecture.md`'s "adoption/rejection → behavioral consumption" edge, currently harness-only/never-exercised against real Echo):

- Clean pass (§11, all criteria) → establishes that the **behavioral-consumption edge is real and causal** for verified-outcome context specifically — a necessary building block toward E5 ("preference causally influences future behavior"), though this experiment alone does not establish E5 in the full preference-formation sense (no persistence/retention claim is made here, only same-session conditioning).
- H0a/H0b outcome → does not advance past **E1** for outcome-conditioning specifically (a real behavioral variation exists, but its provenance is a known, explained mechanism — generic priming or instruction-following, not verified-outcome sensitivity).
- Clean null across all conditions → confirms **E0** for this specific mechanism, and — combined with P1.2's existing null on the unconditioned paradigm — meaningfully strengthens the case that the architecture, not merely the absence of any one untested lever, is the limiting factor for content-level learning as currently constituted.

## 15. Implementation Plan (Not Executed This Pass)

- `formation_retention.py`-analog under `app/experiments/preference_provenance/` (or a clearly-separate sibling module, to avoid conflating this experiment's schema with the preference-formation one) reusing `harness.run_trial()`-style orchestration.
- Outcome-statement template generator, consuming `objective_verify()`'s real return dict directly (`ran_ok`, `passed`, `output_tail`) — no hand-authored outcome text per trial.
- Task-pair selection script scanning the existing, already-captured Tier-4 `mechanism_calls` corpus for real historical approach-divergent pairs before authoring any new ones.
- A small, pre-specified AST-based approach classifier (e.g., "contains a `Call` node whose function name matches a recursion-shaped self-reference" vs. "contains a `For`/`While` loop") — specified narrowly and disclosed as coarse (§13.1).
- A calibration pass against a mock/non-Echo responder first, mirroring this thread's own established "calibrate before touching anything real" discipline, before any real-Echo trial.

**None of this is built in this pass.** Deferred until this design is reviewed and explicitly locked.

## 16. What This Experiment CANNOT Establish

- Consciousness, subjective experience, sentience, or moral status — out of scope, per this project's standing constraint.
- Genuine, persistent preference formation or retention across sessions — this experiment is entirely single-session/same-context; it says nothing about persistence, only about whether verified-outcome context has *any* causal effect at all within one context.
- Whether the memory-retrieval system *could* surface the right outcome on its own — this experiment supplies the outcome directly via the harness; retrieval quality is a separate, later question if this comes back positive.
- Generalization beyond coding tasks with objective pass/fail criteria — deliberately chosen for measurability; whether the same effect (if found) holds for `personal`/`creative`/subjective tasks is untested here.
- A definitive verdict on fine-tuning's necessity from this experiment alone — a clean null here is strong supporting evidence, not proof, that architecture (not just this one lever) is the limit; a clean pass justifies building this out further before fine-tuning, not a guarantee fine-tuning is unnecessary forever.

---

**Pending Gremlin's review and explicit sign-off before any implementation, pilot, or trial — no code for this experiment has been written.**
