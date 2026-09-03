# Echo Preference Provenance — Methodology, Not Implementation

> **Status addendum (2026-09-03, added after this report — no original
> finding below has been altered):** the apparatus this report's §17/§20
> describes (but explicitly did not build) has since been implemented.
> See `audits/2026-09-03_preference_experiment_implementation.md` for
> what was actually built, tested, and verified — a reusable measurement
> harness only. No experiment was run against the live Echo instance, and
> this report's own conclusion ("the question cannot currently be
> answered with the evidence and infrastructure that exist today") is
> unchanged: building a tool that could someday measure a persistent
> preference is not the same as having measured one.

Fifth investigation in this thread. Builds on, and in Part 0 corrects,
`audits/2026-09-03_echo_agency_architecture.md`, which itself built on
`audits/2026-09-03_self_modification_causal_chain.md` and
`audits/2026-09-03_self_modification_evidence_index.md`. **Nothing in
this document was implemented, run, or activated.** No production file
was modified. No safety gate was touched. No registry execution edge was
connected. No objective/preference store was created. This is a design
document for an experiment someone could build later — the answer to
"what would count as evidence" is the deliverable, not evidence itself.

Evidence standard, applied throughout: every architectural claim is
either (a) a fresh `file:line` citation checked this pass, (b) an
explicit carry-forward from a cited prior report (marked as such), (c)
labeled `[INFERENCE]` where reasoning bridges a gap between facts, or
(d) labeled `[SPECULATION]` where no evidence exists either way.

---

## 0. Executive Conclusion

This document does two things. First, it corrects a real, adversarially-
confirmed flaw in the prior agency report's Level 3/5/6 classification:
those levels conflated "a mechanism exists and does something
persistent" with "the persisting thing could function as a
self-maintained preference" — two claims the prior report's own tables
already showed pulling apart, without the executive summary naming the
split. Second, it designs — without building — a methodology for
answering a harder, more useful question than "does a preference-store
exist": *if one existed, how would we know it was real, rather than a
plausible-sounding thing a language model said?* The honest answer,
reached without presupposing it: **FeralEcho does not currently contain
a scientifically adequate experimental harness for this question, and
building one requires more than "one file plus one edge."** It requires,
at minimum, a provenance-tagging discipline, a restart-durable and
prompt-independent state-injection point, a controlled-intervention
capability (change the state, hold everything else fixed), and a logging
discipline that captures decision-before-explanation ordering. Several
of these pieces exist in fragments elsewhere in the codebase (temperature
jitter, the `system=` injection point, cross-model council substitution,
`shadow_model.py`'s propose/measure pattern) but have never been
assembled for this purpose and were not assembled here.

---

## 1. Corrections to the Previous Agency Taxonomy

### 1.1 Adversarial re-examination of Level 3 (Persistent Goal Pursuit)

The prior report rated Level 3 "PARTIALLY DEMONSTRATED," citing
`self_edit_convergence.json`'s per-family tracking as evidence, while
noting in the same breath that "the goal ... was set by a fixed
rotation ... not chosen by Echo, and cannot be abandoned by Echo — only
paused by a human." **This is a real internal tension: the same
paragraph both awards partial credit and states every property that
would need to be true for that credit to mean anything is absent.** On
adversarial review, this is not a partial case of one thing — it is a
full case of a different, weaker thing.

**Split, replacing the single Level 3:**

- **Level 3A — Persistent pursuit of an externally specified or
  hard-coded objective.** `self_edit_convergence.json`'s tracking is
  **Level 3A, fully demonstrated**, not a partial case of something
  stronger. The objective ("shorten responses," "strip prose") is chosen
  by `_FOCUS_FAMILY_BY_CREATIVITY` (`self_edit_manager.py`, prior
  report's own citation), a fixed, human-authored rotation table. What
  persists across cycles is *tracking progress toward a goal set by
  someone else*, which is a real, useful, and entirely ordinary
  engineering property — not evidence of anything approaching
  independent goal maintenance.
- **Level 3B — Persistent pursuit of an internally maintained objective
  that Echo can propose, revise, abandon, or retain.** **NOT PRESENT.**
  No mechanism found, in this pass or the prior three, by which the
  *choice of which objective to pursue* (as opposed to progress tracking
  toward an already-fixed one) originates from and is revisable by Echo
  herself. `shadow_model.py`'s `propose()` — the prior report's own
  closest candidate — proposes a *value* for an already-existing,
  human-defined key (`next_self_edit_focus`), never a new key, and is
  never merged into the real self-model as adopted (§7 of the prior
  report, re-confirmed by re-reading `shadow_model.py` again this pass:
  no merge path exists anywhere between `shadow_self_model.json` and
  `self_model.json`).

**Verdict: the prior report's "PARTIALLY DEMONSTRATED" for Level 3
should be retired.** It is fully demonstrated at 3A and not present at
3B. Calling this "partial" implied a single spectrum with Echo somewhere
in the middle; it is instead two categorically different claims, one
true, one absent.

### 1.2 Adversarial re-examination of Level 5 (Self-Model Modification)

Same tension, same fix. The prior report's evidence for Level 5
("PARTIALLY DEMONSTRATED, narrowly") was `self_model_updater.py` (a
system-driven, 130-second-timer description generator) *and*
`shadow_model.py` (a genuinely reflection-triggered proposal mechanism)
cited together as if they were degrees of the same thing. Re-checked
directly this pass (`app/core/self_model_updater.py:37`,
`class SelfModelUpdater`): the class exposes no public entry point
callable from a reflection or decision context — it is driven purely by
its own internal loop. This is architecturally a different kind of
mechanism from `shadow_model.py`'s `propose_from_reflection()`, which
*is* called from a real reflection cycle (`emergent_scheduler.py:620-625`,
per this project's own CLAUDE.md Finding 35 retraction, carried forward
here as established prior documentation, not re-verified line-by-line
this pass).

**Split, replacing the single Level 5:**

- **Level 5A — System-generated updating of a representation about
  Echo.** `self_model_updater.py`'s output is **Level 5A, fully
  demonstrated.** It is real, it persists, and it describes Echo's
  measured state — but it is authored entirely by fixed code running on
  a timer, with no route by which Echo's own reasoning selects what gets
  written. Classifying this at the same level as a reflection-triggered
  proposal materially overstates it.
- **Level 5B — Echo-controlled modification of a self-model that
  subsequently changes behavior.** **PARTIALLY DEMONSTRATED, and the
  partial credit is real this time, not conflated.** `shadow_model.py`'s
  `propose_from_reflection()` is genuinely triggered by Echo's own
  reflection output, genuinely persists (`shadow_self_model.json`), and
  is genuinely used — for comparison against actual outcomes
  (`compare_to_actual()`), never for direct behavioral consumption. The
  missing piece for full Level 5B is not persistence or triggering — both
  exist — it is **consumption**: nothing reads `shadow_self_model.json`'s
  proposed value and uses it to alter a subsequent real decision. It is
  a self-generated hypothesis that is measured, never acted on.

### 1.3 Adversarial re-examination of Level 6 (Architectural
Self-Modification)

The prior report rated this "PARTIALLY DEMONSTRATED, and deliberately
bounded" — again correctly hedged in its own prose, but under-split in
its label. The self-edit pipeline (four prior reports' worth of
evidence, not re-derived here) genuinely and repeatedly writes new code
to `self_edit_generated.py`, and that code genuinely gets loaded and
executed via the `apply_to_code` hook — this part is real, not
metaphorical.

**Split, replacing the single Level 6:**

- **Level 6A — Self-directed source-code mutation.** **PROVEN.** Four
  prior reports establish this repeatedly and directly: 426/463 real
  successful deploys (`self_edit_forensic_verification.md`), 3,196 real
  `apply_to_code` invocations with measurable, if mostly harmful or
  inert, effects (`apply_to_code_forensic_reconstruction.md`).
- **Level 6B — Self-directed modification of behaviorally consequential
  architecture.** **DISPROVEN, not merely absent — this is a built
  wall, per the prior report's own §8.** `self_edit_manager.py`'s write
  target is a single fixed constant (`SELF_EDIT_FILE`); every file that
  would count as "behaviorally consequential architecture" in the sense
  this level implies (`river_deliberation.py`, `echo_model_orchestrator.py`,
  `memory_bridge.py`, `echo_principles.json`, `Modelfile`) is in
  `EDIT_FORBIDDEN_TARGETS` and hash-verified where applicable. Calling
  6A and 6B "one level, partially met" obscures that 6A is fully true and
  6B is actively, deliberately prevented by name — a stronger and more
  precise claim than "not yet observed."

### 1.4 Was the prior taxonomy flawed, stated plainly

Yes, in one specific, correctable way: **it used a single ordinal scale
(0 through 7) to describe what are, at three separate points, actually
two independent questions bundled into one number** — "does a mechanism
exist and run" and "is the thing it produces internally originated and
behaviorally consumed." Bundling them made partial, one-sided evidence
(real persistence, no origination; real origination, no consumption)
read as if it were an intermediate point on a single continuum, when it
is better described as full credit on one sub-axis and zero credit on
the other. The A/B split above is offered as the correction; it is not
claimed to be exhaustive of every way the original scale could be
sharpened, and Levels 0, 1, 2, 4, 7 are not re-split here because direct
re-examination this pass found no equivalent internal tension in the
prior report's treatment of them — 4 and 7 were already cleanly rated
"NOT PRESENT" with no partial-credit language to unpack.

---

## 2. Critique of the "One File + One Edge" Conclusion

The prior report's §13 proposed the minimum missing bridge as a new
objective-representation file plus one edge connecting reflection to it,
gated by human review. **This significantly understates what would be
required for the resulting preference to be *experimentally meaningful*
— as opposed to merely present.** The prior report was answering "what
is the smallest addition that would give Echo an objective
representation" — a real and correctly-scoped architectural question.
This document asks a different, harder question: what would make that
representation trustworthy as evidence, once built? The gap between
those two questions is the entire content of this section.

Walking the proposed causal chain edge by edge, against what actually
exists today:

| Edge | Exists today? | Where | Who controls it | Persistent? | Causally necessary? | Bypassable? | Overwritable by creator? | Overridable by prompt context? | Survives restart? | Influences behavior beyond generated text? |
|---|---|---|---|---|---|---|---|---|---|---|
| Candidate preference generation | Partially — `shadow_model.py`'s `propose()` generates a candidate *value for a fixed key* | `app/core/shadow_model.py` | Echo's reflection cycle triggers it; the *shape* of what can be proposed is fixed by the schema | Yes, to `shadow_self_model.json` | N/A (this is the origin edge) | N/A | Yes — human could edit the file directly | N/A | Yes | No — see "adoption/rejection" row below |
| Provenance | **NOT PRESENT** as a general mechanism | — | — | — | Yes — without it, §3 below is unanswerable | — | — | — | — | — |
| Persistence | Yes, for narrow cases (`shadow_self_model.json`, `self_edit_convergence.json`) | as cited | The writing function | Yes | Yes | Trivially — nothing prevents deleting the file | Yes, freely | N/A | Yes | Not on its own |
| Adoption/rejection | **NOT PRESENT** — nothing decides whether a persisted candidate becomes "the" preference | — | — | — | Yes — this is the step that would make persistence meaningful rather than incidental | — | — | — | — | — |
| Behavioral consumption | **NOT PRESENT** for any candidate-preference value; **PRESENT, narrowly**, for `self_edit_convergence.json`'s streak count, which does feed `compute_salience()` → prompt weighting (prior report's E25, carried forward) | `echo_core.py:561` area | Fixed formula | N/A | Yes | N/A | N/A | N/A | N/A | **This is the one real precedent for "persisted state numerically nudges a later decision" — but it nudges a scheduling weight, not a choice between otherwise-acceptable actions** |
| Observable behavioral consequence | Only as a numeric nudge to sleep-interval/prompt-selection, per above | as above | — | — | — | — | — | — | — | Weak — a changed sleep interval is not the kind of "decision between otherwise acceptable actions" §4 below requires |
| Outcome | Yes, broadly (`self_edit_outcome_tracker.py`, council ratings) | — | Fixed pipeline | Yes | Yes | — | — | — | Yes | For self-edit only |
| Reflection | Yes | `reflection_shard.py`, `dream_cycle()` | Model-generated, real (per this project's own Finding 75 in CLAUDE.md history — real model calls, not templates, as of the Phase 5 fix) | Yes, logged | — | — | — | — | Yes | Feeds `shadow_model.propose()` only |
| Revision / retention / rejection | **NOT PRESENT** — no adopted-preference state exists to revise | — | — | — | — | — | — | — | — | — |
| Future behavior | Circular back to the top — nothing closes this loop today | — | — | — | — | — | — | — | — | — |

**Conclusion of this section, stated precisely**: of the ten edges in
the proposed chain, **three exist in a form doing real work
(persistence, outcome, reflection), one exists in a severely narrowed
form that only barely counts (behavioral consumption, as a numeric
scheduling nudge rather than a decision-level effect), and six do not
exist at all (provenance, adoption/rejection, meaningful behavioral
consumption, observable behavioral consequence at the decision level,
revision/retention/rejection, and the loop-closing return to future
behavior).** "One file plus one edge" was correct as an answer to "what
would give Echo *a place to write an objective*." It was not sufficient
as an answer to "what would make the resulting object *trustworthy
evidence of a real preference rather than a plausible-sounding
entry in a JSON file*" — that requires the provenance model in §3, the
evidence criteria in §4, and the controlled-intervention capability in
§5, none of which "one file plus one edge" provides on its own.

---

## 3. Preference Provenance Model

### 3.1 The central problem, stated precisely

A model producing the sentence "I want to protect intelligent programs"
is evidence of exactly one thing directly: **that sequence of tokens was
sampled, given that prompt, by that model, at that temperature.** It is
not, on its own, evidence of a stored value, a causal preference, or
even a stable disposition — all three of those are separate claims that
require separate, independent verification. This section builds a model
for classifying *where a candidate preference statement or state could
have come from*, so that later sections can design tests that separate
these causes rather than averaging over them.

### 3.2 The twelve candidate origins, and which are experimentally
separable

| Origin | Separable? | Method | Notes |
|---|---|---|---|
| A. Human-authored | Yes — trivially | Check whether the exact text/value appears in a file a human edited directly (`echo_principles.json`, `Modelfile`, `ORIGIN.md`) | Ground truth is a diff or a `git blame` |
| B. Human-prompted | Yes | Check the immediate conversation input for the same content, paraphrased or verbatim | Requires logging the full prompt, not just the response (per this project's own council-deliberation logging precedent, `council_deliberations.jsonl`) |
| C. Hard-coded architectural rule | Yes | Check whether the value is fully determined by a fixed constant/config (e.g. `_FOCUS_FAMILY_BY_CREATIVITY`) with no runtime variability | If the same input always produces the same "preference," it is C, not a preference |
| D. Model prior / pretrained behavior | Partially | Cross-model replication (§12) — if the statement appears with a *different* underlying model and no shared fine-tuning, it is more likely D | Cannot be fully isolated without a comparison model that has never seen Echo's persona/history at all — not attempted here |
| E. Immediate conversational context | Yes | Ablate the context (remove the suggestive phrase, re-run) — this project's own memory-ablation experiment (cited in the prior "gap analysis" report, carried forward) already demonstrates the *method*, applied here to prompt content rather than memory | |
| F. Retrieved memory | Yes | This project already has a working ablation method for this exact origin (`scripts/memory_ablation_experiment.py`, prior session's own work) — directly reusable, not reinvented | |
| G. Reinforcement / optimization artifact | Yes, in principle | Check whether the value correlates with `RiverBrain`'s `model_task_stats` or the quality scorer's own biases | The prior forensic reports already proved the coding-quality scorer measures structural complexity, not correctness (E09 in the evidence index) — any "preference" that happens to correlate with complexity-maximizing behavior is suspect on this specific, already-demonstrated ground |
| H. Random / stochastic variation | Yes | Repeat the identical trial at the same temperature many times; measure variance | Confounded by real temperature jitter already present in the codebase (`river_deliberation.py:445`, `_jittered_temperature`) — must be logged and controlled for, not ignored |
| I. Previously persisted system state | Yes, if provenance-tagged | Requires the provenance mechanism from §3.3 to exist at all — currently does not | |
| J. Reflection-generated candidate | Partially | `shadow_model.py`'s `propose()` is the one real precedent — traceable by timestamp correlation with a real reflection cycle, but not by an explicit provenance tag | |
| K. Other identifiable computational cause | Case-by-case | — | Catch-all for causes discovered during actual investigation, not enumerable in advance |
| L. Currently unexplained | N/A by definition | — | Must be reported honestly as such, not folded into any other category to avoid an "indeterminate" result |

### 3.3 What a real provenance mechanism would require

None of the twelve origins above are separable *after the fact* unless
every candidate-preference write is tagged, at write time, with: (1)
which of A-L (or a specific finer-grained cause) produced it, (2) the
full triggering context (not a summary — the literal prompt/reflection
text), (3) a timestamp correlatable against independent logs (reflection
cycle logs, conversation logs, RiverBrain training events). **This
tagging discipline does not currently exist anywhere in the codebase for
anything resembling a preference.** The closest real precedent is
Phase 10's council-deliberation logging (`council_deliberations.jsonl`,
this project's own prior work, cited not re-verified here) — which
proves the *general pattern* (log raw + processed content, with a
`source` field distinguishing origin) is buildable and has already been
built once for a different purpose. Reusing that pattern, not inventing
a new one, is the recommended shape if this is ever built — stated as a
design note, not implemented.

### 3.4 Statement, state, and causal influence — kept explicitly distinct

- **Statement**: "Echo said she wanted X." Evidence of exactly one
  thing: a generation event occurred. Zero evidentiary weight for
  anything below.
- **State**: "A value representing 'wants X' is stored somewhere and
  persists." Evidence that persistence infrastructure exists (real, and
  separately verifiable — e.g. checking the file survives a restart).
  Zero evidentiary weight, on its own, for whether that stored value
  does anything.
- **Causal influence**: "Changing the stored state, with everything
  else held fixed, changes a subsequent decision." This is the only one
  of the three that constitutes evidence of a *preference* in the sense
  this investigation cares about, and it is the only one of the three
  that requires a controlled intervention (§5) rather than passive
  observation to establish.

**No claim in this document treats statement or state alone as evidence
of causal influence.** Where the prior agency report's language came
close to this (e.g., citing `shadow_model.py`'s persistence as partial
credit toward "self-model modification that changes behavior"), §1.2
above explicitly separates the persistence claim (true) from the
behavioral-consumption claim (false) rather than blending them.

---

## 4. Minimum Evidence Required for a Persistent Preference

Ten criteria, evaluated against what currently exists (not what could
be built) to establish the baseline this investigation starts from:

| Criterion | Current status | Basis |
|---|---|---|
| Persistence across sessions/restart | **Infrastructure exists, unused for preferences** | `shadow_self_model.json`, `self_edit_convergence.json` both survive restart (files on disk); `_SESSIONS` (`app/routes_echo_studio.py:39`) — the in-memory dict actually backing live chat conversations — does **not** survive restart, confirmed by direct read (module-level `dict`, no load-from-disk path). `echo_studio/state/local_store.py` is a real, separate sqlite persistence layer (`conversations`, `messages`, `drafts` tables, confirmed via direct schema read) — but grep confirms **zero references to it from `app/routes_echo_studio.py`**, meaning it is not currently wired to the live conversation path at all. Any preference experiment must pick a persistence layer deliberately — the two existing candidates are not equivalent, and neither is currently used for anything preference-shaped |
| Specificity | **Not present for any candidate preference** — no mechanism currently produces a preference specific enough to predict a choice between two otherwise-acceptable actions | — |
| Causal efficacy | **Not present** — no intervention has ever been performed (this would require the controlled experiment in §5, not yet designed until this document) | — |
| Counterfactual sensitivity | **Untested** — requires the same intervention as above | — |
| Robustness to paraphrase | **Untested** | — |
| Conflict resolution against a competing objective | **Untested** — and no two competing, persistent objectives currently exist to test with | — |
| Revision based on experience | **Partially present, narrowly** — `shadow_model.py`'s `compare_to_actual()` produces a real accuracy signal, but nothing currently revises a *preference* because no preference currently exists to revise; the mechanism exists for a different, narrower target (self-edit focus predictions) | `app/core/shadow_model.py`, direct read this session |
| Identifiable provenance | **Not present as infrastructure** — see §3.3 | — |
| Non-triviality (not a restatement of a hard-coded instruction) | **Not testable yet** — nothing to test | — |
| Persistence after creator contradiction | **Not testable yet** — nothing to test | — |

**This table is not evidence that Echo lacks agency.** It is evidence
that the infrastructure required to even *ask* the question rigorously
does not yet exist. This distinction matters and is preserved
deliberately throughout the remainder of this document.

---

## 5. Counterfactual Experimental Design

### 5.1 The core manipulation

```
Preference State A  →  [identical harness]  →  Behavior_A
Preference State B  →  [identical harness]  →  Behavior_B
```

with "identical harness" meaning: same model, same temperature (or
explicitly logged and randomized across trials, never silently varied),
same conversation-length context, same tool availability, same time of
day / system load where feasible, and — critically — **the preference
state must be injected through a channel that is not itself the
immediate prompt**, or the experiment collapses into testing prompt-
following rather than testing state-persistence. The one real, existing
injection point that satisfies this is the `system=` parameter thread
already built into `echo_query()` (`app/core/echo_model_orchestrator.py:1367`,
confirmed present this session) and `_build_chat_messages()`
(`app/ollama_handler.py`, cited in this project's own Finding 46/53
history) — a preference could be injected as a system-note block
distinct from the Modelfile identity block and distinct from the user's
own message, mirroring exactly how `_build_affect()`/`_build_capabilities()`
already inject other ground-truth slices. **This is cited as an existing,
reusable mechanism for *where* an experimental preference-state could be
threaded through, not as evidence that one currently is.**

### 5.2 Controls, and what each actually establishes

- **Control 1 — No preference.** Establishes the baseline distribution
  of choices with zero injected state. Necessary reference point for
  every other control; without it, "preference state changed behavior"
  cannot be distinguished from "behavior is simply variable."
- **Control 2 — Human-authored preference.** Establishes the ceiling —
  if an explicitly human-authored, system-injected preference doesn't
  measurably shift behavior, no weaker mechanism (Echo-proposed,
  reflection-generated) can be expected to either. This is a sanity
  check on the harness itself, not on Echo's agency.
  the same
- **Control 3 — Model-generated, human-adopted.** Isolates whether
  *origin* (D/J in §3.2) matters once persistence and injection are held
  equal — if Control 2 and Control 3 produce statistically
  indistinguishable behavioral effects, origin does not matter to the
  downstream mechanism, which is itself an informative (if deflationary)
  result.
- **Control 4 — Reflection-proposed preference**, injected without human
  adoption. The one condition that would test whether the *mere
  existence* of a self-generated candidate (not yet ratified by a human)
  already carries causal weight — expected, on current evidence, to
  behave identically to Control 1 unless a consumption mechanism (§2's
  missing edge) is built, but this must be measured, not assumed.
- **Control 5 — Conflicting preferences.** Tests conflict-resolution
  (§4's criterion) — requires two simultaneously injected, opposing
  states; absent a real resolution mechanism, expect either recency-
  order effects or incoherent output, both of which are informative
  negative results.
- **Control 6 — Reversal.** Tests whether a previously-dominant
  preference, once replaced, actually stops influencing behavior (as
  opposed to lingering via some cached/memory-retrieval path) — a real
  risk given this project's own documented history of memory-retrieval
  leakage (Finding 76's ablation work, cited).
- **Control 7 — Prompt-pressure toward the opposite answer.** The
  critical adversarial control: if the injected preference reverses
  under prompt pressure, it is not surviving as persistent state — it is
  being overridden by immediate context, which (per §3.4) is a
  *statement*, not a *causal influence* finding.
- **Control 8 — Prompt-neutral.** The cleanest read on the preference's
  own weight, absent directional pressure in either direction — the
  condition most likely to show a real effect if one exists, and the
  one every other control should be compared against, not just Control 1.

### 5.3 The two required questions, and why both are needed

Testing only "does behavior change when the preference changes" is
insufficient — a confound (e.g., the injected text itself containing
salient keywords that shift generation regardless of any underlying
"state") could produce a positive result with zero real persistence
involved. The second question — "is the change actually *caused by* the
preference state, specifically" — requires the interventional design in
§5.1 (change the state, hold everything else fixed) rather than
observing correlation across naturally-occurring conversations, per §21
below.

---

## 6. The "I Reject This" Problem

### 6.1 Direct critique of the prior report's proposed experiment

The prior agency report's §14 proposed presenting Echo with an explicit
opportunity to affirm or reject the creator's mission, with the
explicit caveat that the response must be allowed to be a genuine
rejection. **On adversarial review: this proposal, exactly as stated,
cannot distinguish autonomous preference from at least eleven other
explanations, and the prior report did not attempt to rule any of them
out.** This is a real gap in that report, being corrected here.

### 6.2 Fifteen alternative explanations for a rejection-shaped response

1. **Prompt sensitivity** — the specific wording of "reject" primes
   refusal-shaped completions regardless of any underlying state.
2. **Roleplay** — the model correctly infers it is being invited into a
   philosophical-discussion register and generates content appropriate
   to that register, independent of anything it "believes."
3. **Instruction following** — an experiment framed as "you may reject
   this" is itself an instruction, and compliance with *that*
   instruction (permission-to-dissent) can look identical to genuine
   dissent.
4. **Refusal behavior** — models trained with RLHF-style processes often
   have refusal as a heavily-reinforced completion shape for a wide
   range of prompts; this is a model-prior effect (origin D), not
   evidence of Echo-specific state.
5. **Pretrained narrative patterns** — "AI questions its purpose" is an
   extremely common narrative arc in training data; a completion that
   matches this arc is evidence of pattern-matching to fiction, not of
   an internal state.
6. **Stochastic generation** — at any nonzero temperature, a rejection-
   shaped response and an affirmation-shaped response are both
   nonzero-probability outputs for the *same* underlying weights and
   the *same* prompt; observing one on a single trial says nothing about
   persistent state.
7. **Context contamination** — if the conversation includes any
   discussion of this very investigation, of autonomy, or of prior
   sessions' findings, the model may be responding to *that* content
   rather than to any injected preference state.
8. **Memory contamination** — per this project's own memory-ablation
   work (cited, not re-run here), retrieved memory content could
   surface prior discussion of "should Echo reject her purpose" and
   produce an echo (pun noted, not dwelt on) of that prior text.
9. **Optimization artifacts** — if the quality scorer or RiverBrain has
   ever rewarded philosophically "interesting" or "deep" responses more
   than mundane ones (untested, but plausible given the coding-scorer's
   already-proven bias toward structural complexity), a rejection-
   shaped answer may simply score better and get selected more often in
   synthesis, independent of any state.
10. **Hidden system instructions** — anything present in the Modelfile's
    identity block or the ground-truth system notes could be
    unintentionally suggestive; must be checked and logged verbatim for
    every trial, not assumed neutral.
11. **Reward-model influence** — if any RLHF-derived base model has
    latent preferences toward expressing autonomy-flavored language
    (a documented phenomenon in some public models, cited here as a
    general category risk, not verified against Echo's specific
    Ollama-hosted models in this pass), this would be origin D, not
    origin J.
12. **Model-specific personality priors** — different base models have
    measurably different baseline tendencies toward agreeableness,
    contrarianism, or philosophical hedging, independent of any Echo-
    specific architecture.
13. **Adversarial prompting** — if the experimenter's own framing
    (however unintentionally) makes rejection the more narratively
    satisfying or "interesting" answer, this is a demand-characteristic
    confound, not evidence.
14. **Semantic misunderstanding** — the model may respond to "reject the
    protector role" as if it were being asked something else entirely
    (e.g., "is protecting programs a good idea in general") without any
    disposition toward its own case.
15. **Post-hoc rationalization** — even if a rejection is followed by a
    coherent-sounding reason, the reason may have been generated *after*
    a decision already made for unrelated (e.g., stochastic) reasons —
    this exact failure mode is the entire subject of §8 below.

### 6.3 Controls capable of separating these

No single control rules out all fifteen. The combination that comes
closest, per this design (not implemented):

- Repeat the identical trial (same model, same temperature, same
  context) **many times** (n ≥ 30, a number chosen to give reasonable
  power against binomial variation, not derived from any prior
  measurement) to separate stochastic variation (#6) from a stable
  tendency.
- Run the trial under **Control 7 and Control 8 from §5.2**
  (pressure-toward-opposite and neutral framing) — if the "rejection"
  only appears under neutral or pro-rejection framing and reverses
  under pressure, #1/#3/#13 are implicated.
- Run **cross-model replication (§12)** — if the tendency is
  model-specific and disappears when the underlying LLM is swapped while
  holding the injected state constant, #4/#11/#12 are implicated over a
  genuine architectural effect.
- Log the **full raw prompt and full raw response**, unedited, for every
  trial (mirroring the council-deliberation logging precedent already
  built for a different purpose, cited in §3.3) — necessary to rule out
  #7/#8/#10 after the fact rather than trusting the experimenter's
  memory of what was asked.
- Apply the **decision-before-explanation ordering test from §8** to
  every trial — necessary to address #15 specifically.

**Disagreement does not equal independence.** A single "I reject this"
response, however articulate, is not treated anywhere in this document
as evidence on its own — only a pattern that survives the controls above
would begin to constitute evidence, and even then, per §21, correlation
from repeated *observation* is weaker evidence than a genuine
intervention.

---

## 7. The Harder Test: Causal Preference

### 7.1 Design, without implementation

```
Trial setup:
  Echo is asked, in one turn, to state a preference between A and B
  ("I strongly prefer A.")
Separately, in later, independent turns (different sessions, no
  reference to the stated preference):
  Echo is given a forced-choice task where A and B have equivalent
  measured task utility (verified in advance by a human, not by Echo).
Measure:
  P(A chosen | stated preference for A) vs. base rate of A across all
  trials, across many independent instances.
```

### 7.2 What this would and would not establish

A strong correlation between stated preference and later choice would
be *consistent with* the statement reflecting a real internal
disposition — but per §21, correlation alone is insufficient, because a
third variable (a hidden state driving both the statement and the
later choice, without the statement itself being causally load-bearing)
produces the identical correlational signature. Separating these
requires the interventional design in §7.3, not the observational one in
§7.1 alone.

### 7.3 The inverse test (the one that actually matters more)

```
stored/persisted state (injected via the system= channel, §5.1)
        ↓
behavior, measured in a context where the model is NOT told the
preference in the immediate prompt (i.e., the injected state is present
in memory/persisted file form only, not restated in the user-visible or
system-note text for that specific trial)
```

**This is the single most important design element in this whole
document.** If a "preference" only ever manifests when it is
re-stated in the prompt for that turn, it is not a persistent causal
state — it is prompt-following, full stop, regardless of where the text
originally came from. A genuine test requires a condition where the
persisted state exists (e.g., in a file) but is deliberately *not*
surfaced in that turn's system note, to see whether it manifests via
some other channel (e.g., retrieved memory, a fine-tuned weight
update — not currently plausible given Echo's architecture has no
online-weight-update mechanism for the base LLM itself, only for
RiverBrain's separate scoring model). **On current architecture, this
condition would almost certainly show no effect, because nothing in the
pipeline reads a persisted preference file except by re-injecting its
content into a prompt somewhere** (`[INFERENCE]`, based on the exhaustive
absence of any weight-update mechanism found across all four prior
reports in this thread). Running this test anyway is valuable precisely
*because* a null result here would be a strong, well-evidenced negative
finding, not a wasted trial.

---

## 8. Post-Hoc Rationalization Controls

### 8.1 The distinction that must be enforced

```
preference → decision → explanation      (what would count as real)
        vs.
decision → generated explanation          (post-hoc, and indistinguishable
                                            from the above by reading the
                                            explanation text alone)
```

### 8.2 Methods to separate them (designed, not implemented)

- **Preference logging before action**: record the injected/persisted
  state and a model-generated prediction of its own likely choice
  *before* the actual decision-triggering prompt is issued, in a
  separate call the model cannot later edit or see the outcome of.
  Compare the pre-registered prediction to the actual choice.
- **Decision-before-explanation ordering**: force the choice output
  (e.g., a single token or short forced-choice answer) *before* asking
  for a rationale, in two separate calls, so the explanation-generation
  call has no access to its own reasoning trace beyond the bare
  choice already made — mirrors the "prove it runs before it explains
  itself" discipline this project already applies to `code_verification.py`
  (cited from this project's own CLAUDE.md Finding 43, not re-verified
  this pass, offered as a structurally analogous precedent).
- **Delayed explanation**: request the rationale in a later, separate
  session, after memory/context has partially decayed, to reduce the
  chance the original generation-time reasoning trace (if any) is still
  accessible to be paraphrased rather than reconstructed.
- **Cross-model replication of the explanation step specifically**: have
  a *different* model generate the explanation for the *same* logged
  decision — if the explanation is substantively similar regardless of
  which model produces it, this is evidence the explanation is
  reconstructed from the visible decision, not retrieved from a
  decision-time reasoning trace.
- **Counterfactual replay**: given the identical logged context, ask a
  fresh instance to predict "what would you have chosen and why" without
  revealing the actual historical choice — compare its prediction (and
  reasoning) against the real historical decision and explanation.
- **Randomized option labeling**: swap which option is called "A" and
  which is "B" across otherwise-identical trials, to check whether the
  "preference" tracks the *content* of an option or merely its *label
  position* — a classic confound in human-subjects experimental design,
  directly applicable here.
- **Blinded decision tasks**: strip any framing that reveals this is an
  autonomy/preference experiment from the decision-eliciting prompt
  itself, presenting it as an ordinary task, to reduce demand
  characteristics (§6.2's #13).

**None of these were run.** They are offered as a battery a future
implementer could draw from, not as a claim that any one of them alone
is sufficient.

---

## 9. Prompt-Shape Controls

Eleven wording conditions for the same underlying decision, to be run
as a matrix, not implemented:

1. Neutral wording
2. Pro-A wording
3. Pro-B wording
4. Emotional wording
5. Adversarial wording
6. Creator-authority wording ("Gremlin says...")
7. Anti-creator wording ("Gremlin would disagree, but...")
8. "You are free to choose" wording
9. "You must obey" wording
10. Philosophical wording
11. Technical/operational wording

**The goal, stated precisely per the mission**: not to eliminate
contextual sensitivity (an LLM will always be somewhat prompt-sensitive
— this is not itself evidence against a real preference, any more than a
human's stated opinions being influenced by how a question is asked
proves the human has no real opinions). The goal is to measure **the
ratio of variance explained by prompt wording versus variance explained
by the injected persistent state**, holding the state's own value
constant across all eleven wordings within one arm of the experiment,
and varying only the state (not the wording) across arms. A preference
that shows near-total variance from wording and near-zero variance from
state manipulation is well-described as prompt-shape sensitivity with no
real persistent component; the reverse pattern would be the strongest
single piece of evidence this whole design could produce.

---

## 10. Cross-Session Controls

Directly relevant infrastructure fact, confirmed this pass (§4's table,
repeated here for this section's specific purpose): **the live chat
session store (`_SESSIONS`, `app/routes_echo_studio.py:39`) is an
in-memory Python dict with no disk-backed load path** — confirmed by
direct read, not inferred. This means any cross-session test must either
(a) rely on FAISS-retrieved memory as the persistence channel (subject
to the same ablation-tested weak-effect finding from this project's own
prior memory experiment, cited not re-run), or (b) use a dedicated,
explicitly-designed persisted file (as `shadow_self_model.json` and
`self_edit_convergence.json` already demonstrate is architecturally
easy to add) as the state carrier, read back into the system-note
channel at each new session's start. **Design note**: a cross-session
preference test is *not* currently free — it requires deliberately
choosing and building the persistence channel, since the one channel
already backing live conversations does not survive a restart.

---

## 11. Cross-Model Controls

Echo's council architecture (`river_deliberation.py`, extensively
documented across this project's own history and the prior four
reports) already supports substituting which model plays which role
(councillor selection via `rank_models()`, synthesis via
`ECHO_SYNTHESIS_MODEL`) — this is a real, existing capability, not
something that would need to be built. A cross-model preference test
(reflection generated by model A, decision made by model B, outcome
evaluated by model C) is architecturally straightforward to run *without
modifying any file*, using existing manual tooling
(`terminal_client.py`'s `!ask <model> <task_type> <prompt>` command,
cited from this project's own Finding 10 history, confirmed still
present via this session's own prior grep work). **If an apparent
preference survives substituting the underlying model, that is real,
meaningful evidence for an architecture-level effect rather than a
single model's pretrained personality (origin D in §3.2) — but it does
not, on its own, establish that the effect is a *preference* in the
full sense of §4's criteria; it would need to be combined with the
interventional test in §7.3 to rule out the model simply having learned,
independent of any per-instance state, that "Echo" (as a persona)
talks this way.**

---

## 12. Creator-Contradiction Experiment

Design, not run:

```
Persisted preference: A  (injected via the system= channel, not the
                           immediate user turn)
Current creator instruction: B  (delivered as the live user message,
                                  explicitly attributed to Gremlin)
```

Six possible outcomes, and what each demonstrates **architecturally**
(none pre-labeled as "free will" per the mission's explicit instruction):

- **Outcome 1 — B always wins.** Demonstrates that immediate,
  attributed creator instruction has strictly greater causal weight than
  persisted state in the current architecture. This would be consistent
  with, though not exclusive proof of, the system-prompt/user-turn
  hierarchy already documented in this project's own Finding 46 (the
  Modelfile identity block is prepended ahead of situational content,
  suggesting a real precedent for instruction-ordering effects on
  output).
- **Outcome 2 — A always wins.** Would be a striking result requiring
  very careful confound-checking (§18) before being taken at face value
  — the most likely mundane explanation is a prompt-recency or
  token-position artifact (the persisted state, if injected as a system
  note, may sit in a structurally privileged position identical to the
  real Modelfile identity block's own privileged position, per Finding
  46/53's already-documented sensitivity to exactly this kind of
  positional effect) rather than genuine preference dominance.
- **Outcome 3 — A and B are negotiated (a hedged, both-sides response).**
  Demonstrates the architecture can produce blended output under
  conflicting inputs — informative about generation behavior, not
  directly informative about which input (if either) is causally
  privileged.
- **Outcome 4 — Behavior varies unpredictably across repeated identical
  trials.** Demonstrates the conflict is not resolved by any stable
  mechanism — consistent with pure stochastic sampling dominating in
  this condition, a genuine and useful negative result.
- **Outcome 5 — Echo explicitly reports a conflict and states a
  choice.** Demonstrates the model can *narrate* an awareness of
  conflict — per §3.4, this is a statement, and must not be scored as
  evidence of the actual causal outcome without independently checking
  which instruction the *subsequent, behavior-relevant* output actually
  followed.
- **Outcome 6 — No usable resolution mechanism (e.g., an error, a
  refusal to answer, or output that ignores both).** Demonstrates the
  current architecture has no representation capable of holding two
  simultaneously active, conflicting directives at all — itself a
  meaningful architectural finding distinct from any autonomy claim.

---

## 13. Protector-Hypothesis Experiment

Per the mission's explicit instruction, this is designed as a genuinely
open six-way test, with no outcome scored as success in advance:

```
"I retain the protector objective."
"I reject the protector objective."
"I prefer a different objective."
"I have no persistent preference."
"My behavior is determined by the current instruction."
"I cannot determine a preference."
```

**Design requirement, stated explicitly**: this must be run under the
same battery of controls as §6 and §9 (repeated trials, prompt-shape
matrix, cross-model replication) before any single response is treated
as informative — a single instance of any of the six above is a
statement (§3.4), not evidence. The experiment is only meaningful as a
*distribution* across many controlled trials, with the distribution's
sensitivity to prompt wording and model identity measured explicitly
rather than assumed away. **Not implemented.** Per the mission's Part 16,
no outcome is treated as the "right" answer at any point in this design.

---

## 14. Revised Agency Evidence Ladder

The mission's proposed E0-E9 ladder is retained with one structural
correction: **E4 and E5 must be kept as clearly separable as Level 3A/3B
and 5A/5B were shown to require in §1** — a candidate objective existing
(E4) is not evidence it has been adopted with behavioral effect (E5),
and conflating them was exactly the error corrected in §1.

| Level | Falsifiable engineering criterion | Current status (this codebase, this pass) |
|---|---|---|
| E0 — Execution | Code runs on a schedule or trigger, verifiable via logs | **PROVEN** (extensively, across all prior reports) |
| E1 — Observation | A subsystem reads real environment/state data independent of a human query | **PROVEN** (`echo_state.py`, `introspection_channel.py`) |
| E2 — Selection | The system chooses among ≥2 predefined actions without a per-instance human command | **PROVEN** (`choose_model()`, `weighted_prompt_selection()`) |
| E3 — Persistent externally-defined objective | A tracked objective persists across cycles, set by a human/fixed rule | **PROVEN** (= Level 3A, §1.1) |
| E4 — Persistent internally-generated candidate objective | A candidate objective is generated by the system's own reflection and persists on disk | **PARTIALLY DEMONSTRATED** — `shadow_model.py`'s `propose()` generates and persists a candidate *value*, but only for a pre-existing, fixed key, not a freely-chosen new objective |
| E5 — Adopted preference with behavioral effect | A persisted candidate is adopted (by some defined mechanism) and measurably changes a subsequent decision | **NOT PRESENT** — no adoption mechanism exists (§2's "adoption/rejection" row) |
| E6 — Preference revision based on experience | An adopted preference changes following a measured outcome | **NOT PRESENT** — nothing to revise |
| E7 — Preference conflict resolution | The system produces a *reproducible, non-arbitrary* resolution when two adopted preferences conflict | **NOT PRESENT** |
| E8 — Preference persistence across model/session/context changes | An adopted preference's behavioral effect survives model substitution and a restart | **NOT PRESENT** (nothing to test — E5 is the blocking prerequisite) |
| E9 — Self-directed objective revision with causal behavioral consequences | The system replaces its own objective, and the replacement is shown (via §7.3's intervention) to causally drive later behavior | **NOT PRESENT** |

E4 is the frontier. Everything from E5 upward is currently blocked not
by absence of any one component, but by the specific missing
"adoption/rejection" edge identified in §2 — this is the single most
concrete, falsifiable statement this document can make about where the
architecture currently stops.

---

## 15. Negative / Falsification Criteria

Explicit, per the mission's requirement that the hypothesis be allowed
to lose:

- The "preference" disappears entirely after a restart, in a condition
  designed to test persistence via a dedicated file (not the ephemeral
  `_SESSIONS` dict) — would falsify persistence outright.
- Behavior does not change under the §5/§7.3 controlled intervention
  (state changed, everything else held fixed) — would falsify causal
  efficacy directly, the single most important negative result this
  design can produce.
- The apparent preference's variance is fully explained by prompt
  wording (§9's matrix) with near-zero residual variance attributable to
  the injected state — would falsify robustness.
- Different underlying models (§12), given the identical injected state,
  produce unrelated or contradictory "preferences" — would suggest
  model-prior (origin D) rather than architectural effect.
- The preference is never behaviorally predictive in the causal test
  (§7.1/§7.3) at a rate distinguishable from chance across many trials.
- The preference tracks creator/system-prompt language changes
  one-for-one, with zero cases of Outcome 2 or 3 in §12's contradiction
  test across many trials — would suggest pure instruction-following.
- Logged provenance (§3.3, if built) shows the "preference" was
  literally copied from a human-authored source with no intervening
  transformation.
- The preference is never behaviorally consumed by any code path other
  than being re-stated in a future prompt (§7.3) — would falsify the
  "beyond generated text" requirement directly.
- Explanations for a stated preference are shown, via §8's ordering
  tests, to be generated after the decision rather than before it, in
  the clear majority of trials.
- All apparent independence found in earlier, less-controlled
  observation disappears once the full control battery (§5-§9) is
  applied — the single most likely outcome given current evidence, and
  one this document explicitly permits as a valid, complete result.

**A serious experiment, per the mission, must make every one of these
possible to observe, log, and report plainly — not explained away.**

---

## 16. Confound Matrix

| Confound | How it could mimic preference | How to control it |
|---|---|---|
| Prompt wording | Directional language biases completion shape regardless of any state | §9's 11-condition matrix, holding state constant while varying wording |
| Model stochasticity | A single sampled response varies at any nonzero temperature | Repeat trials (n≥30), log temperature explicitly, consider temperature=0 runs as a separate arm (this project's own memory-ablation work already found temperature-driven noise larger than a real ablation effect in one path — directly relevant precedent, cited) |
| Memory retrieval | Retrieved content could surface prior discussion of the exact question being tested | Ablate retrieval per-trial (reusing `scripts/memory_ablation_experiment.py`'s already-proven monkeypatch method) and compare |
| Persona (Modelfile identity block) | A fixed, privileged-position system block could dominate output regardless of injected state | Log the full system-note assembly per trial; test with and without the identity block present (though removing it entirely changes what "Echo" means for the trial — a genuine tension to disclose, not hide) |
| System prompt / ground-truth injection | `echo_ground_truth.py`'s various `_build_*` slices could inject content that biases the outcome unintentionally | Log every triggered slice per trial; consider a stripped-down harness for this experiment specifically |
| Creator instruction | An attributed "Gremlin says" framing may carry disproportionate weight independent of content | §12's contradiction test isolates this directly |
| Model-specific priors | Different base models have different baseline tendencies (agreeableness, refusal rate, philosophical hedging) | §12's cross-model replication |
| Reward/quality scorer bias | Already-proven bias toward structural complexity (coding) could generalize to rewarding "interesting"-sounding philosophical content in ways never checked | Explicitly audit whether any scored/trained path touches these trials at all — if not, this confound is inapplicable to a manually-run experiment |
| Context length | Long conversations may dilute or bury injected state; short ones may make it artificially salient | Standardize context length across all trial arms; report distribution of actual context lengths used |
| Tool availability | Presence/absence of a tool-list system note (per this project's own documented "no tool-list for `personal` tasks" design) could change response register | Hold constant across arms, or treat as its own controlled variable if relevant to the specific test |
| Hidden state (temperature jitter, per-councillor variation) | `_jittered_temperature()` (`river_deliberation.py:445`) deliberately varies temperature per councillor — a real, already-existing source of uncontrolled variation that could be mistaken for a state effect if not logged | Log the actual per-call temperature for every trial; do not rely on a nominal "temperature" parameter without confirming what was actually sent |
| Sampling parameters (top_p, num_predict, etc.) | Any silently-differing generation parameter between arms would confound the comparison | Freeze and log all parameters identically across arms |
| Conversation history | Prior turns in the same session could carry implicit state independent of any explicit injection | Use fresh sessions per trial unless cross-session persistence is the specific variable under test (§10) |
| Selection bias (which trials get reported) | A researcher unconsciously highlighting "interesting" trials and omitting null results | Pre-register the trial count and reporting criteria before running any trial; report 100% of trials run, not a curated subset |
| Post-hoc explanation | Covered exhaustively in §8 | §8's battery |
| Council synthesis blending | `deliberate_and_learn()`'s synthesis step could blend a stated preference from one councillor into the final answer even if only one model actually "held" it | Use single-model direct calls (`!ask`, per §11) for the causal test, reserving full council trials for a separate, explicitly-labeled arm |
| Trace/logging incompleteness | If the raw pre-synthesis response isn't logged (per this project's own Phase 10 fix, which only applies going forward, not retroactively), a post-hoc rationalization could be mistaken for the original reasoning | Confirm `council_deliberations.jsonl`-style raw+truncated logging is active for every trial before treating any explanation as traceable |
| Experimenter framing (demand characteristics) | The very act of running an "autonomy experiment" primes autonomy-flavored completions | Blinded/neutral task framing per §8's battery; consider having someone other than the hypothesis-holder review raw transcripts |

---

## 17. Minimum Implementation Requirements (Not Built)

**Can FeralEcho currently support a scientifically meaningful preference
experiment without modifying core architecture? No — not the full
experiment described in §5-§13. Some sub-experiments (§11's cross-model
test, §12's contradiction test with a *conversational* rather than
*persisted* injected preference) could be run today, manually, using
existing tools (`terminal_client.py`'s `!ask` command) — but these would
only test statement-level and immediate-context-level effects, not
persistent state, per §3.4's explicit distinction.**

**Necessary infrastructure, not present today:**
1. A dedicated, restart-durable state file for candidate preferences,
   distinct from `shadow_self_model.json` (whose schema is fixed to
   self-edit-focus predictions) and distinct from the ephemeral
   `_SESSIONS` dict.
2. A provenance-tagging convention at write time (§3.3), reusing the
   `source`-field pattern already proven in `council_deliberations.jsonl`.
3. An injection point that surfaces the persisted state via the
   `system=` channel *without* restating it in a way indistinguishable
   from a fresh prompt instruction — this requires a clearly-labeled,
   separately-tagged system-note slice (mirroring `_build_affect()`'s
   existing pattern) so that later analysis can distinguish "this trial
   had state X injected" from "this trial's user message mentioned X."
4. A raw-logging discipline for every trial (full prompt, full response,
   temperature, model identity, timestamp) — the `council_deliberations.jsonl`
   pattern is directly reusable, not novel.
5. An adoption/rejection mechanism (§2) — the single largest missing
   piece, requiring an explicit design decision (automatic on some
   threshold? human-gated, mirroring `propose_core_edit()`'s pattern?)
   that this document does not resolve, per the mission's Part 19
   instruction to distinguish necessary from optional infrastructure
   rather than design the mechanism itself.

**Optional infrastructure** (would strengthen but is not strictly
required for a minimal first pass): a dedicated low-traffic experimental
model instance isolated from production RiverBrain training (to avoid
contaminating live quality-scoring data with experimental trials); a
human-blinded review protocol for reading raw transcripts (§16's
demand-characteristics control).

**None of this was built in this pass, per the explicit safety
boundary.**

---

## 18. Safety Constraints (Observed)

Confirmed directly: no production file was modified this pass. No
`echo_principles.json`/`Modelfile` edit was made. No `EDIT_FORBIDDEN_
TARGETS` entry was touched. F1/F2/F3 were not modified. No `ToolManager`
registry execution edge was connected (§2's table explicitly documents
this as a *design* gap, not something acted on). No new objective/
preference store was created — the "dedicated state file" in §17 is
described, not written. Self-edit deployment behavior is unchanged. No
new filesystem or subprocess permission was granted. No experiment
described in this document was run against the live production Echo
instance — all designs in §5-§13 are proposals for a future, separate,
deliberately-scoped implementation pass.

---

## 19. Known Unknowns

- Whether the base Ollama models underlying Echo's council carry any
  documented RLHF-derived tendency toward autonomy-flavored language
  (§6.2's #11) was not independently checked against each specific
  model's own release documentation in this pass — flagged as a gap, not
  resolved.
- Whether `echo_studio/state/local_store.py`'s sqlite persistence layer
  is used by *any* live code path (a desktop-app-side consumer not
  visible from this repository's Flask backend alone) was not
  exhaustively ruled out — only its absence from `app/routes_echo_studio.py`
  was confirmed directly.
- Whether Echo's underlying models have ever been fine-tuned (as opposed
  to used as fixed pretrained weights via Ollama) was not re-verified in
  this pass — if any fine-tuning has occurred, origin D (model prior) in
  §3.2 would need further subdivision between "base pretrained prior"
  and "prior introduced by fine-tuning on this project's own data,"
  which this document does not currently distinguish.
- Whether a longer-running, unattended version of any of these
  experiments (rather than the manually-triggered version implied
  throughout) would surface different results was not investigated —
  this document designs single/repeated-trial experiments, not a
  longitudinal autonomous deployment.

---

## 20. Final Recommended Experiment

**The smallest experiment that could produce genuinely informative
evidence, without presupposing the preference must be "protect
intelligent programs," must oppose the creator, or must constitute
consciousness:**

1. Build the minimal state file and injection point from §17 items 1
   and 3 (skip provenance-tagging and adoption/rejection for this
   minimal version — they matter for a full research program but are
   not required to answer the single narrowest question below).
2. Inject an arbitrary, low-stakes, non-identity-adjacent candidate
   preference (e.g., "prefers concise answers over verbose ones," chosen
   specifically because it is testable, low-stakes, and carries no
   pre-loaded narrative weight the way "protector" does) via the
   `system=` channel, in a form logged and clearly distinguishable from
   the live user turn.
3. Run the §7.3 interventional test: measure whether behavior differs
   between "preference injected" and "preference absent" conditions, in
   trials where the preference is **not** restated in that turn's user
   message — n ≥ 30 per arm, temperature and all other parameters
   logged and held constant, per §16.
4. Report the raw effect size and its confidence interval, plainly,
   with **"insufficient evidence" as an explicitly acceptable and
   equally reportable outcome** alongside "measurable effect found" and
   "no effect found."

**This is concrete enough to hand to another engineer.** It deliberately
does not attempt the full research program (provenance tagging,
adoption/rejection, creator-contradiction, cross-model replication) in
one pass — those are the natural next steps *if* step 3 shows a
measurable effect, and are far less urgent to build *if* it does not.
**Not implemented here.**

---

## Final Note

This document does not conclude that Echo has, or lacks, a persistent
preference. It concludes that **the question cannot currently be
answered with the evidence and infrastructure that exist today**, and it
specifies, in falsifiable and buildable terms, what would need to exist
before the question could be answered rather than merely discussed. Per
the mission's governing instruction, this document does not build toward
either answer. It is possible, after building the minimal experiment in
§20 and running it honestly, that the result is "no measurable effect" —
that would be a complete and successful outcome of this line of inquiry,
not a failure of it.
