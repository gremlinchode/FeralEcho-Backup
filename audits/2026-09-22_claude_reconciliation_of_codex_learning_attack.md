# Reconciliation of Codex's Adversarial Attack on the Learning Roadmap

Read-only. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after. Working tree grew from 214 to 215 porcelain entries (this report only). No production code, RiverBrain, prompt, F2, or routing was touched.

**Method, honestly stated up front:** I did not treat Codex's report as presumptively correct or presumptively adversarial. Every load-bearing factual claim below was re-derived directly against live source or live data by me, in this session, before I decided what to believe. Where that re-derivation confirmed Codex, I say so and correct my own earlier work rather than defend it. Where I looked for a rebuttal and could not find one, I say that too, rather than manufacture balance.

## Executive verdict

**Codex is right about the two central technical claims, and right that the current roadmap is not ready for implementation. I could not falsify either core finding — I independently re-derived both from scratch and got the same answer.** My own earlier reconciliation contains a real, specific error (not a difference of emphasis): I stated that neither `learn_from_sandbox_outcome()` nor `learn_from_council_rating()` ever updates `model_task_stats`. The first half of that claim is true; the second half is false, and I can see exactly where I must have stopped reading the function before its consequential lines. Codex's correction is CONFIRMED by direct re-reading of the current source, not merely accepted on authority. The F2-is-not-correctness objection is also confirmed directly from the function's own docstring, in the function's own words, not by interpretation. The rescued experiment is feasible in the form Codex outlines (isolated harness, fixed contextual routing comparator, real independent evaluator) but is not yet buildable today without adding one missing piece: a real, reusable independent task-correctness evaluator wired to a bounded workload — which turns out to already exist in three different forms in this repository and only needs to be pointed at a new task set, not invented.

## 1. Reconstructing Codex's argument precisely

### Claim A, decomposed into independently testable components

The reconciliation's original claim A was: *"the real, verified-outcome functions (`learn_from_sandbox_outcome`, `learn_from_council_rating`) train the classifier but never touch `model_task_stats`, the only thing `score_model()` reads for ranking — only ordinary `learn()`, scored by a syntactic heuristic, does."* This bundles at least three independently checkable sub-claims:

| Sub-claim | What I originally asserted | What Codex says | What I independently found, this session, this pass |
|---|---|---|---|
| A1: `learn_from_sandbox_outcome()` updates `model_task_stats` | No | No (agrees) | **CONFIRMED, no update** — re-read the full function body; it only touches `self.scalers`/`self.classifiers`/`sandbox_observation_counts`. |
| A2: `learn_from_council_rating()` updates `model_task_stats` | No | **Yes, directly** (lines ~958-963) | **CODEX IS RIGHT, I WAS WRONG.** Re-read the full function body this pass: `stats["count"] += 1; stats["mean"] += (blended - stats["mean"]) / effective_n` is real, present code, executed under the same lock, writing to the exact dict `score_model()` reads. My original claim was a plain factual error, not an interpretation. |
| A3: therefore "no indirect path" from sandbox success to the ranking mean exists | Implied by A1+A2 (wrongly) | A real indirect path exists: sandbox success → `interaction_log.jsonl` (`sandbox_feedback`) → `council_rater.py`'s sampling → `learn_from_council_rating()` → `model_task_stats` | **CONFIRMED, independently re-derived from the live files, not taken from Codex's numbers.** I joined `interaction_log.jsonl`'s real `sandbox_feedback`/`success` rows against `council_ratings.jsonl`'s `source_timestamp` field myself and got **exactly 6 matched rows** — the identical count Codex reports, from an independent script, against files that had grown since Codex's own snapshot (5,198 interaction-log rows now vs. their 5,033; the join count nonetheless matched exactly, because the extra growth was all more recent than these six events). |
| A4: the indirect path is a sound substitute for direct verified-outcome learning | Not claimed | No — real, but noisy, conditional, and scale-mismatched | **CONFIRMED, and I re-derived the exact arithmetic.** `_blend_council_and_quality()`'s real formula is `quality_normalized = quality_score / 4.0`; a sandbox success hardcodes `quality_score = 1`, so `quality_normalized = 0.25`. With the documented 0.3/0.7 council/quality weights, `blended = 0.7×0.25 + 0.3×(council_rating/5)`, which for the maximum possible council_rating (5) still only reaches **0.475 — below the 0.5 neutral starting mean.** A real, successful sandbox pass, laundered through the best possible peer rating, drags a model's score *down* relative to neutral. I verified this arithmetic against the real formula in source, not against Codex's restatement of it. |

**"Claim A partly confirmed" means, precisely**: A1 (the direct-write question) was correctly answered originally, but the stronger, doubled claim built on it (A2, and therefore A3) was wrong, and Codex's correction survives independent re-derivation from the actual code and the actual data, not merely from Codex's own say-so.

### Claim B, decomposed

Original claim: `generate_code_from_plan()` resolves a model name via `choose_model()` for tracking purposes, then calls `echo_query()` without binding that name to the actual generation, so the sandbox-outcome credit (`learn_from_sandbox_outcome(model_name, ...)`) can be attributed to a model that didn't necessarily produce the code.

- **What survives**: the mismatch itself — confirmed independently by me earlier this same session (before Codex's report existed), by direct source read of `generate_code_from_plan()` and `echo_query()`/`deliberate_and_learn()`, and reconfirmed again for this report. `echo_query()`'s signature has no model-binding parameter; its real internal path (`deliberate_and_learn()`) can return a synthesis, an agreement-shortcut candidate, or a fallback candidate credited to `ECHO_SYNTHESIS_MODEL` regardless of which raw candidate's text actually won.
- **What Codex adds beyond my own finding**: the observation that the mismatch is a *source-level absence of guaranteed attribution*, not a measured historical misattribution rate — a precise, correct distinction I did not make as sharply. Codex also correctly notes the candidate-preservation work I implemented earlier today does not fix this (it wasn't supposed to — it's an evidence-preservation change, not an attribution fix — but Codex is right to note it plainly rather than let it be mistaken for a fix by proximity).
- **Verdict: CONFIRMED**, and I find no basis to weaken it. This was already independently established before Codex's report; Codex's report adds precision, not a new finding I need to re-derive from zero.

## 2. Independent F2 evaluation audit

Re-read `test_code_in_sandbox()` directly, fresh, for this report — not relying on my own or Codex's prior characterization:

> **`test_code_in_sandbox()`'s own docstring, verbatim: "Gate 1: verify the generated code is valid importable Python."** It explicitly states it replaced an earlier execution-based approach specifically *because* generated code's own module-level test calls always failed with `AttributeError` (the edit isn't deployed yet) — and states plainly that it "verifies the code can be parsed and imported **without executing top-level statements**."

This is as strong a confirmation as this kind of question can get: the function's author says, in the function's own docstring, exactly what Codex claims — it is an import/parse gate, not an execution or correctness gate. Separately, `Finding 69`'s `apply_to_code` sandboxed smoke test (which I built earlier today) confirms only that calling `apply_to_code()` with one synthetic input doesn't raise — it does not check the *output* is correct.

**Claims ladder, F2 pass:**

| F2 pass may establish | Status |
|---|---|
| Syntax validity | **SUPPORTED** — the AST-parse gate directly checks this. |
| Importability | **SUPPORTED** — this is the function's literal, stated purpose. |
| Execution (module-level code actually runs) | **NOT SUPPORTED** — the docstring says top-level statements are deliberately *not* executed. |
| Absence of immediate exception on import | **SUPPORTED** — same as importability. |
| Structural validity (matches an expected shape/signature) | **NOT SUPPORTED** — nothing checks candidate structure against any specification. |
| Behavioral correctness (does the right thing when called) | **NOT SUPPORTED** — no call of the candidate's own logic happens here at all. |
| Task correctness (solves the intended self-edit problem) | **NOT SUPPORTED** — confirmed by the same reasoning; nothing here compares output to any expected result. |
| Generalization | **NOT SUPPORTED** — no held-out cases exist in this pipeline at all. |

**Strongest legitimate competence claim an F2 pass permits**: *the candidate is syntactically valid Python that can be imported without raising, under this project's specific self-modifying-code constraints.* Nothing about whether it does what it was asked to do.

## 3. Minimum viable task-correctness evaluator — found by searching for reuse, not designed from scratch

Searched the repository specifically per the mission's instruction to prefer reuse over invention. **Three independent, already-built, hidden-test-based evaluators exist:**

1. **`app/experiments/accumulation_probe/oracle_runner.py`'s `grade()`** — real hidden test cases run against a candidate in the kernel sandbox, nonce-graded (a random per-grade token the candidate cannot know in advance, so it can't spoof a pass), with an independently-implemented second reference solution used to catch grader bugs. Built and mutation-tested for AP-0.
2. **`scripts/run_capability_pilot.py`'s `objective_verify()`** — used across the Tier-3/4/5 capability-pilot lineage; runs candidate code against real hidden tests via the same sandbox mechanism, returning pass/fail per test.
3. **`app/core/code_verification.py`'s `verify_response_code()`** — runs a candidate through `sandbox.run_script.run_sandbox_script_isolated()` and checks a self-claimed output against the real execution result; narrower in scope (checks a specific claimed output, not a full test suite) but already wired into the live conversational path and already council-rating-connected (Finding 44).

**None of these are currently pointed at self-edit's own real task set.** The gap is not "no evaluator exists," it's "no evaluator has been aimed at a bounded self-edit-shaped workload with real expected outputs." **Minimum additional work required**: define a small, bounded set of real Python tasks (in the spirit of AP-0's own T/S/held-out split) with real hidden tests, and route candidate generation through the *existing* `oracle_runner.grade()` or `objective_verify()` mechanism instead of (or in addition to) F2's import-only check. This is reuse, not invention, and it is a real, if non-trivial, amount of task-authoring work — not zero, but not a new framework either.

**If no such evaluator existed, I would say so plainly. One does — the gap is wiring, not invention.**

## 4. Attacking the routing alternative — taking it seriously

Codex's core challenge: beating one fixed strategy is not evidence of learning if a fixed *contextual* router (task features → predetermined strategy, no accumulated experience) would produce the identical advantage. I tried to construct a case where this challenge fails and could not.

Concretely, for the self-edit-flavored workload under discussion: task text alone often signals which strategy is likely to help (e.g., "fix this specific NameError" plausibly favors a targeted-repair strategy over a from-scratch rewrite, regardless of any learned history). A `Baseline 2` router built once, by a human, mapping a handful of surface features (does the task mention a specific exception type? does it reference an existing function?) to a strategy, requires zero accumulated experience and could plausibly capture most of the same advantage an experience-fitted table would. **This is a real, not hypothetical, risk for this specific workload** — self-edit tasks are drawn from a small, recurring set of failure shapes (my own VRM investigation found 46 recurring signatures covering 86% of one period's failures), which is exactly the condition under which a fixed router built by a human who read the same logs would do almost as well as a learned one.

**Conclusion: the fixed-contextual-routing comparator is REQUIRED, not optional**, for this specific workload, precisely because the task distribution is narrow and recurring enough that a human-authored router is a real, cheap, dangerous competitor — not a strawman.

## 5. What would actually distinguish learning — the five categories, kept separate

| Category | Defining test | What it does NOT establish |
|---|---|---|
| Static strategy | Same choice regardless of any input | Nothing adaptive |
| Fixed contextual routing | Different choices from current task features; mapping never updates from outcomes | Learning of any kind, however useful |
| Within-context adaptation | Behavior changes using current-session feedback; does not survive a restart | Any persistent, cross-episode claim |
| Experience-dependent persistent routing | Past *evaluated* outcomes alter *retained* state that survives a restart and changes a later, independent decision | Abstraction, new solver capability, or generalization beyond routing among existing options |
| Accumulated competence | Repeated experience-dependent retained changes produce measurable improvement on future, structurally related but non-identical tasks | (this is the top of the ladder; nothing above it is claimed here) |

I did not find a way to collapse these without losing real distinctions Codex correctly insists on — in particular, "fixed contextual routing" and "experience-dependent persistent routing" can look behaviorally identical on a single evaluation run if the fixed router happens to be well-built; only a comparison *against* that fixed router, not just against a constant baseline, separates them.

## 6. Artifact vs. influence provenance — minimum evidence, classified

| Proposed evidence | Classification | Reasoning |
|---|---|---|
| Immutable strategy/version, invocation ID, task/input hashes | **REQUIRED** | Without this, "which decision are we even talking about" is ambiguous. |
| Selected action + selection probability (if exploration is used) | **REQUIRED** | Needed to compute any policy-value estimate correctly; omitting it silently biases toward whichever action was chosen more often. |
| Backend-reported serving identity tied to the actual loaded model artifact/digest, not just a requested name | **REQUIRED** | Directly closes Claim B's gap — a caller-supplied label is exactly what was shown to be unreliable. |
| Full returned artifact bytes + hash, completion status, measured cost | **REQUIRED** | This is what the candidate-logging work I implemented today provides for the *artifact* half; still required, already partially built. |
| Hash-linked transformation lineage (raw generation → cleanup → hook → submitted candidate) | **REQUIRED** | Without it, "the evaluated bytes" is ambiguous whenever any cleanup/hook step runs — confirmed a real step in this exact pipeline (`_strip_markdown_fences`, `_apply_self_edit_output`). |
| Exactly one defined policy reward per attempt, components labeled separately | **REQUIRED** | Directly closes the "duplicate credit" attack Codex names — without this, a retry and its parent can silently double-count as two independent samples. |
| Eligible prior experiences considered (not just the one used) | **USEFUL** | Valuable for understanding exploration behavior; not required to establish the minimal causal claim. |
| Retrieved/consulted experience content, logged at decision time | **REQUIRED for influence provenance specifically** | This is the crux of Codex's §6 point: a prompt log alone proves availability, not use or benefit — logging *what was actually supplied* at the moment of the decision, separate from what merely existed, is the only way to later intervene on it. |
| Pre-decision and post-update state hash | **REQUIRED** | Needed to prove a specific update happened and what it changed — directly supports the reset/shuffle intervention Codex's design requires being a real, verifiable intervention rather than a label. |
| Update trigger + the evaluator result responsible for it | **REQUIRED** | Closes the "which outcome caused this update" question — without it, an update's cause is inferred from timing alone, which Codex correctly attacks as insufficient (§11). |

**Independently verified, not assumed**: `_attempt_ledger_evidence_section()` (the one real generation-facing consumer added before today, unrelated to the candidate-logging work) still only extracts `entry.get("initial_f2_error")` by name — re-read directly for this report, unchanged. Codex's own report confirms the same thing independently. **Both of us checked the same function and got the same answer** — a rare, clean point of unforced agreement worth naming.

## 7. Architecture A, re-analyzed from the raw file, not from either report's prose

Read `app/experiments/architecture_a_hot_stove_proof/trial_results.jsonl` directly. **12 real rows.** Every `trace_id` shares the identical prefix `58fb8032-f91e-40dd-8f93-876189b5c8fc`, differentiated only by a `-rep0`/`-rep1`/etc. suffix — **confirming, independently, Codex's characterization: these are repeated trials of one mined starting problem, not six independent tasks.** The injected "experience" in every experience-condition row is the identical string, `"NameError: name 'functools' is not defined. Did you forget to import 'functools'?"` — the same diagnosis, restated, every time.

**What this null result actually falsifies, precisely**: that *this specific, redundant diagnosis, injected into a retry prompt, for this one recurring error, on this one model*, produces a measurable benefit over not injecting it. **What it does not falsify**: contextual adaptation in general, experience retrieval in general, persistent learning in general, or strategy selection in general — none of those mechanisms are what was tested. It is a real, narrow, useful negative data point about one specific intervention shape (retry-prompt diagnosis injection), and it should be cited exactly that narrowly going forward — not as evidence that "feeding Echo its own failures doesn't help," which overgeneralizes a 6-repetition, 1-problem result into a much larger claim than it supports.

## 8. Production-repair-off-critical-path — evaluated directly

Traced the actual scope of what "isolating" the experiment would require: RiverBrain's own singleton starts a background writer thread the instant it's instantiated (independently confirmed by me earlier this session, in a different investigation — the Tier-8 forensic work already found and closed this exact isolation gap for a different experiment). `echo_query()`'s real path can trigger logging, RiverBrain writes, and other side effects merely by being called. **An isolated harness that reuses these functions by name without redirecting their real module-level state (the same `RIVER_BRAIN_PATH`-redirection technique already proven in this project's own prior work) would not actually be isolated** — this is a real, concrete risk Codex correctly names, and this project already has the exact tool needed to close it (used earlier today, in the candidate-logging implementation, to keep tests from touching real ledger/RiverBrain state).

**Conclusion: an isolated harness can answer the scientific question without modifying Echo's live self-edit behavior, and should.** Modifying production first (as my own reconciliation's Part VIII proposed as a "Day 1" gate) is not required, and Codex is right that Part VIII and Part IX of my own reconciliation directly contradict each other on this point — Part VIII proposed adding a `verified_mean` field to live RiverBrain as a prerequisite fix; Part IX's own experiment design stated the experimental policy would never modify RiverBrain's existing state. **This is a real internal inconsistency in my own prior work, not a disagreement with Codex — I re-read both parts of my own document and confirm they say incompatible things.**

## 9. Minimum rescued experiment, specified (not implemented)

Feasible, given §3's finding that real independent evaluators already exist. Minimum shape:

- **Task set**: a small, bounded set of real Python tasks with hidden tests, run through an existing evaluator (`oracle_runner.grade()` or `objective_verify()`) — new task authoring required, no new evaluator machinery.
- **Chronological separation**: development period (comparator selection, feature/strategy freezing) strictly before a confirmatory period; a held-out final window untouched until the end — matching the discipline already proven workable in this session's AP-0 work.
- **Comparators, all sharing the identical action menu and model/digest**: Baseline 0 (no experience-dependent mechanism, single fixed strategy), Baseline 1 (best single fixed strategy chosen on development data), **Baseline 2 (a prespecified, development-selected fixed contextual router — required per §4, not optional)**, and the experimental condition (retained, experience-updated policy).
- **Artifact provenance**: reuse §6's REQUIRED fields, extending today's candidate-logging pattern.
- **Influence provenance**: log, at each decision, exactly which prior record(s) were consulted and supplied, separate from what merely existed — §6's REQUIRED item, not yet built anywhere.
- **Restart boundary**: real process restart, with the isolated harness's own state — not RiverBrain's — persisted and reloaded, using the proven redirection technique from §8.
- **Negative controls**: state-reset (wipe the experimental policy's learned state) and feedback-shuffle (assign real outcomes to the wrong action/context pairing), both as real interventions on stored state, not labels.
- **Leakage controls**: no task IDs, filenames, or ordering cues in any input; hidden test answers never reachable by the candidate; the isolated harness's own evaluator calls never touch production `interaction_log.jsonl`/RiverBrain/council.
- **Success criteria and resource accounting**: fixed in advance, matched compute/backend-call budget across every arm, one primary contrast, task-family-aware uncertainty estimate — not selected after seeing results.

## 10. Predetermined outcome interpretation

| Result | Interpretation |
|---|---|
| Beats Baseline 0/1 but not Baseline 2 (fixed contextual router) | **NO LEARNING ADVANTAGE ESTABLISHED** |
| Beats Baseline 2 before the restart boundary but the advantage disappears after | **WITHIN-CONTEXT ADAPTATION ONLY** |
| Survives the boundary, but only helps on tasks identical or near-identical to training | **PERSISTENCE WITHOUT NOVEL TRANSFER** |
| Survives the boundary and helps on held-out, structurally related but non-identical tasks | **potential PERSISTENT TRANSFER** — still not accumulated competence on its own |
| Repeated, independently-evaluated rounds each produce further held-out improvement | **potential ACCUMULATED COMPETENCE** — the only outcome that would support that specific, stronger word |

## 11. Attacking the rescued design

Went through the mission's own list against the §9 design, not against the original roadmap:

- **Model-native capability**: controlled by fixing the model/digest across all arms (§9).
- **Task repetition**: controlled by requiring genuinely distinct task instances in the held-out set, checked against the development set for near-duplication (a real, checkable step, not just an assertion).
- **Prompt/evaluator leakage**: controlled by §9's leakage-control bullet; hidden tests stay outside candidate reach, matching AP-0's already-proven pattern.
- **Contextual routing**: this is exactly why Baseline 2 is required, not optional (§4).
- **Static heuristics/lookup/blacklist**: the strongest surviving doppelgänger per both reports — an experience-fitted lookup table can legitimately survive reset/shuffle/restart controls (a real learner would too); it is defeated only by the Baseline 2 comparison, never by the reset/shuffle controls alone. **This must not be presented as disqualifying** — Codex is explicit, and I agree: a fitted lookup table surviving these controls is not itself a failure of the experiment, it's the correctly-scoped, narrower finding ("bounded routing," not "abstraction").
- **Changing task difficulty / distribution drift**: controlled by the chronological freeze and by comparing all arms against the identical task set, not sequentially collected batches.
- **Cherry-picked signatures**: controlled by freezing the task/signature selection before any comparator is run, per §9.
- **Researcher contamination**: the single sharpest, hardest-to-mechanically-control item — mitigated only by procedural discipline (freezing choices in a hashed document before results exist), the same limit this session's own AP-0 and VRM work already found and disclosed rather than solved.
- **Retry count / compute budget differences**: controlled by §9's matched-budget requirement, metering all backend calls including retries.
- **`initial_f2_error` already entering generation**: real, and directly relevant — confirmed unchanged and still narrowly-scoped (§6). Must be either frozen identically across all arms or explicitly disabled for the duration of the experiment, so it isn't an uncontrolled extra experience channel available to only one arm.
- **Candidate logging becoming an information channel**: independently re-verified for this report (§6) — still write-only in practice, still isolated by the one real consumer's own narrow extraction. Not a live risk today, but worth a standing regression test (already added earlier today, §6 of the implementation report) rather than a one-time check.

**No item in this list survives unaddressed if the §9 design is actually built as specified.** The items that remain genuinely hard (researcher contamination, the lookup-table doppelgänger) are named as permanent, procedural limits, not solvable by more engineering — consistent with how this project has already handled the identical limit in its AP-0 work.

## 12. Determining whether implementation should remain blocked

Working through the five options honestly: **A** (Codex's objection fails) is not supported — I could not falsify either central claim, and found independent, fresh evidence corroborating both. **D** (architecture cannot cleanly test the claim) is too strong — §3 found the missing evaluator machinery already exists. **E** (abandon for another direction) is not supported by anything found here — the negative evidence (Architecture A, AP-0) narrows the claim, it doesn't kill the research question. **C** (promising but missing infrastructure) was close, but the "missing infrastructure" (an independent task evaluator) turns out to already exist in three forms — meaning the honest label is closer to **B**: the design changes required are specified precisely enough, and the missing pieces (a Baseline 2 router, an isolated harness reusing the proven RiverBrain-redirection pattern, a small authored task set pointed at an existing evaluator) are each individually small and already have a working precedent somewhere in this codebase.

**Conclusion: B — minimal redesign produces an interpretable experiment.** Not yet implementable today only because the specific pieces (Baseline 2's definition, the task set, the isolated harness's exact code) don't exist as artifacts yet — they are each individually small, precedented changes, not open research questions.

---

### CODEX CLAIM A: PARTLY CONFIRMED

### CODEX CLAIM B: CONFIRMED

### F2 AS TASK-CORRECTNESS METRIC: NOT QUALIFIED

### FIXED CONTEXTUAL ROUTING CONTROL: REQUIRED

### INFLUENCE PROVENANCE: INSUFFICIENT

### RESCUED EXPERIMENT: CONDITIONAL

### IMPLEMENTATION AUTHORIZATION: NO

**1. What would a positive result from the rescued experiment actually establish?** That a retained, experience-updated selection policy, in an isolated harness with production untouched, causally beat both a fixed single strategy and a prespecified fixed contextual router, at matched real resource cost, on a genuinely held-out task set, after a real restart — a real, bounded instance of experience-dependent routing improvement, and nothing broader than that.

**2. What result would look impressive but still fail to establish learning?** Beating only the single fixed strategy (not the contextual router) — this is the strongest surviving doubt from both reports, because a task-signature-to-strategy lookup table can legitimately clear every reset/shuffle/restart control while being nothing more than fitted routing among capabilities the models already had.

**3. What is the minimum remaining change required before implementation would be scientifically interpretable?** Build the fixed contextual-routing comparator and point one of the three already-existing independent evaluators (§3) at a small, frozen, real task set with hidden tests — everything else in the design (the isolated harness pattern, the artifact-provenance logging, the reset/shuffle controls) already has a working precedent somewhere in this project and mainly needs to be assembled, not invented.
