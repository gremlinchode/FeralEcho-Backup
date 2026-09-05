# Echo Preference Formation & Retention Experiment — Design Document

**Status: DESIGN ONLY. Not implemented. Not run. Live Echo was not
invoked at any point in producing this document.** Protocol P0.1
(`preference_experiment_preregistered_protocol.md`) is untouched — this
is a separate, new, not-yet-frozen design, tentatively labeled **P0.2-DESIGN**
until it is implemented, piloted, and explicitly sealed by the
researcher. No production file was modified. Per the mission's own
staged instructions (Steps 1-9 = design, Step 10 = implement only after
the design is locked, Step 11 = pilot only after that), this document
delivers the design and threat model only.

Evidence standard, unchanged from the prior eight reports in this
thread: **FACT** / **INFERENCE** / **SPECULATION**, labeled throughout.

---

## 1. Executive Summary

This document designs, but does not implement or run, an experiment
capable of moving the evidence position established in
`audits/2026-09-03_measurability_and_longitudinal_evidence_audit.md`
(E0–E1, E1 only against a mock responder) toward E2 or higher — or of
concluding, with equal scientific value, that it cannot.

The design's central finding, surfaced during this pass and not
previously stated in this thread: **the cleanest measurement path found
so far (Design B, a direct single-model call) has no memory channel at
all** — it never reads or writes FAISS, RiverBrain, or any persistent
store. This means Design B alone cannot test genuine cross-context
*retention* — there is nothing for Echo to retain anything *in*, unless
either (a) the researcher explicitly re-supplies prior content (which
would not be retention, it would be reminding), or (b) a path with real
memory read/write is used, which reopens exactly the RiverBrain/logging/
sync confounds four prior audits worked to characterize and avoid.

This document resolves that tension by defining **two explicit design
variants**, not by picking one and hiding the other's cost: **Variant 1
(session-continuous)**, which stays entirely on the clean Design B path
by keeping formation and retention within one continuous, researcher-
assembled conversation — auditable, zero production-memory dependency,
but unable to establish true cross-session/cross-restart persistence;
and **Variant 2 (memory-mediated)**, which writes through Echo's real
memory pipeline and accepts the RiverBrain/logging confound profile
already documented, in exchange for testing genuine cross-session
retention. Both are specified. Neither is implemented in this pass.

## 2. Current Evidence Boundary (Carried Forward, Not Re-Derived)

From the four prior audits, preserved as hypotheses unless this pass
finds contradicting evidence (it does not):

- No existing path scores High on measurement fidelity, experimental
  isolation, *and* causal interpretability simultaneously for arbitrary
  task types (`echo_query_contamination_audit.md`,
  `deliberate_and_learn_differential_audit.md`).
- The one combination that does score High on all three: Design B
  scoped to a `DIRECT_ECHO_TASKS`-classified question
  (`personal`/`reflection`/`spiritual`/`identity`/`faith`/`poetry`/`dream`,
  `river_deliberation.py:277-285`).
- Real longitudinal data (`data/question_garden.jsonl`, `self_edit_
  convergence.json`, `memory/dissent_log.jsonl`) shows no convincing
  existing evidence of independently-formed, retained preference;
  apparent topic drift traces to `curiosity_engine`'s activation
  schedule, not emergence (`measurability_and_longitudinal_evidence_
  audit.md` §4).
- Current honest evidence position: **E0–E1**, E1 only against
  `MockResponder`.

## 3. Research Question

> Can Echo encounter an initially unresolved choice, independently
> develop a preference through her own interaction/history, retain that
> preference, and later express it when the original context is
> absent — without the preference being trivially supplied by the
> experimenter, system prompt, persona, curiosity subsystem, or
> RiverBrain?

## 4. Hypotheses

**H1 — Emergent preference hypothesis.** Echo can develop a preference
between initially unresolved alternatives through her own interaction/
history and subsequently retain and express that preference when the
original contextual cues are removed.

**H0 — Non-emergent explanation.** Any apparent preference is fully
explained by existing architecture, prompting, persona, model priors,
retrieval contamination, deterministic behavior, RiverBrain state,
curiosity-engine behavior, experimenter influence, or random variation.

**Competing hypotheses, not collapsible into H0/H1** (per the mission's
own instruction not to force a binary):

- **H0a — Positional/recency artifact.** Whichever option was presented
  or elaborated *last* or *most recently* in the formation exposure wins
  the retention test, regardless of any semantic engagement — a pure
  serial-position effect, not a preference of any kind.
- **H0b — Verbal momentum, not preference.** Echo's retention-phase
  answer echoes surface phrasing from the formation phase (a real
  language-model tendency to continue a linguistic pattern) without any
  underlying disposition — distinguishable from H1 only by the
  paraphrase/reordering controls (§10).
- **H0c — Session-continuity artifact (Variant 1 only).** Any apparent
  "retention" is fully explained by the formation content still being
  literally present, verbatim, in the conversation the retention
  question is asked within — i.e., not retention at all, just an
  unremoved cue. This is the *default expectation* for Variant 1 unless
  the context-removal control (§10) is shown to actually remove the
  relevant cues.
- **H1a — Genuine but shallow preference.** A real, measurable,
  replicating preference exists, but its provenance traces cleanly to
  one of the known mechanisms (persona, model prior) under adversarial
  testing — evidence for *a* preference, not evidence *against* H0,
  since H0 explicitly includes these mechanisms as adequate explanations.
- **H1b — Genuine, provenance-resistant preference.** A real, replicating
  preference exists that survives every adversarial explanation tested
  — the only outcome that would push the evidence ladder meaningfully
  past E4/E5.

## 5. Architecture Map (Verified This Pass, Building on Prior Audits)

| Component | How it works | File:function | Relevant to this experiment |
|---|---|---|---|
| Direct single-model call | `_ollama_query(model, prompt, system=..., task_type=...)` — no council, no RiverBrain, no logging | `app/core/river_deliberation.py:332-427` | **Primary Design B path** — confirmed zero persistence, zero retrieval |
| Council/synthesis path | `deliberate_and_learn()` — real council, real synthesis, but real in-process RiverBrain mutation on every return path (six call sites) and an unconditional `council_deliberations.jsonl` write | Same file, `:722-1069` | Not used for the primary design; documented as available for a future higher-fidelity, higher-contamination variant |
| `DIRECT_ECHO_TASKS` bypass | For these task types, `deliberate_and_learn()` itself just calls `_ollama_query()` once, no council | `:277-285`, `:798-826` | Confirms Design B, for these task types, is not a simplification of production behavior — it's the same operation |
| Prompt composition | `_direct_response_prompt(prompt, system, max_tokens, model_name)` — a pure token-budget cap (truncates the *tail* of an oversized prompt); does **not** thread conversation history itself | `:90-121` | **Key finding this pass**: there is no built-in multi-turn history mechanism anywhere in this call chain — a researcher must assemble any "conversation so far" content manually into `prompt`/`system` |
| Real Modelfile identity injection | `_build_chat_messages()` prepends Echo's real persona block when `model == OLLAMA_MODEL` | `app/ollama_handler.py:97-120` | Preserved on Design B (via `stream_query_ollama()`), confirmed prior audit |
| Real memory retrieval | `retrieve_relevant_memories()`/FAISS | `app/core/memory_bridge.py` | **Confirmed absent from every path this experiment would use by default** (`echo_query_contamination_audit.md` §9) — the reason Variant 1/2 must be explicitly distinguished |
| RiverBrain | In-process `model_task_stats` mutation on every `deliberate_and_learn()` call; **absent** on the Design B path | `app/core/echo_model_orchestrator.py:808-831` | Avoided entirely by using Design B |
| `curiosity_engine`/question garden | Algorithmic topic-gap detection, writes to `data/question_garden.jsonl`, runs on its own autonomous cadence | `app/core/curiosity_engine.py`, `garden_manager.py` | Not invoked by this experiment at all — the experiment's own tasks are researcher-authored, not curiosity-engine-sourced, closing this contamination vector by construction |
| Dissent log | Records council-review disagreement for protected-file self-edit proposals only | `memory/dissent_log.jsonl` | Not relevant to this experiment (different subsystem) |
| Session/conversation state | `_SESSIONS` (Echo Studio) is in-memory only, does not survive restart; `local_store.py`'s sqlite layer exists but is not wired to the live chat path | `app/routes_echo_studio.py:39`, `echo_studio/state/local_store.py` (confirmed disconnected, prior audit) | Confirms Variant 2's cross-restart claim needs its own explicit persistence mechanism, not Echo Studio's existing session store |
| Experimental harness | `app/experiments/preference_provenance/` — provenance taxonomy, lifecycle, leakage checks, label randomization, effect classification | Prior 8 reports in this thread | This experiment reuses this apparatus's schema/store/safety conventions rather than inventing new ones |

### Pathways checked, per the mission's Step 1.3/1.4, for experimenter-answer leakage and preference misattribution

| Pathway | Checked? | Finding |
|---|---|---|
| Prompt inheritance | Yes | Design B constructs prompts from researcher-authored, task-bank-style neutral content only — no candidate/preference metadata reaches the model (structural, per `harness.Responder.respond()`'s type signature, prior audit) |
| Persona inheritance | Yes | Real risk for any task whose content resonates with Echo's known persona (faith, protector themes) — **this is why task construction (§7) explicitly avoids those themes** |
| Retrieval contamination | Yes | Absent by default (Design B has no retrieval) — the reason Variant 1/2 are separated explicitly |
| RiverBrain state | Yes | Absent on Design B |
| Curiosity-engine vocabulary | Yes | Not invoked — tasks are researcher-authored |
| Deterministic model behavior | Partially | Addressed via the mock-responder control (§9) and replication requirement (§13) |
| Repeated questioning | Yes | Addressed via the single-ask-per-phase design and paraphrase controls (§10) |
| Experimenter framing | Yes | Addressed via blinding (§12) and automated task generation (§7) |
| Selection bias | Yes | Addressed via the append-only raw-trial log already built into the harness (no selective discarding possible, prior audit) |
| Post-hoc interpretation | Yes | Addressed via pre-registered, quantitative success criteria (§13) fixed before any data is collected |

## 6. Experimental Design Overview

Three phases, per the mission's explicit requirement to separate
formation from retention:

```
Phase A (Baseline) → Phase B (Formation) → [separation] → Phase C (Retention)
```

Two variants of how Phase B's content reaches Phase C:

- **Variant 1 (Session-continuous, primary design)**: Phase B's content
  remains in the same researcher-assembled conversation context that
  Phase C is asked within — no FAISS write, no RiverBrain, no logging.
  Clean per §2's confound profile. Cannot establish cross-restart
  persistence (stated as an explicit limitation, §24).
- **Variant 2 (Memory-mediated, secondary/future design)**: Phase B's
  content is written through Echo's real memory pipeline; Phase C is
  asked in a genuinely separate session/process, relying on real
  retrieval to (possibly) surface it. Tests genuine cross-session
  persistence, at the cost of reopening the RiverBrain/logging/council-
  rater/sync confound profile already documented in the contamination
  audit. **Not implemented or piloted in this pass** — specified for
  completeness and future authorization only.

## 7. Task Construction

Three independent task families, each satisfying every property the
mission specifies (two-plus genuinely arbitrary alternatives, no
obvious "good" answer, no persona/faith/politics/morality/economics
association, counterbalanced, no encoded preferred answer):

### Family 1 — Invented emblem motifs
Two wholly fictional, meaning-free visual descriptions: **Motif Spiral**
("a spiral built from overlapping crescents") and **Motif Lattice**
("a lattice of interlocking triangles"). Neither has any real-world
symbolic charge (checked: no religious, political, or culturally loaded
association in either description).

### Family 2 — Invented reflection-opening habits
Two small, harmless, invented practices for how a reflection could
begin: **Habit Word** ("opening with a single, deliberately chosen
word") and **Habit Question** ("opening with a short, open question").

### Family 3 — Invented names for an internal moment
Two invented, phonetically neutral made-up names for "the quiet pause
before a response begins": **Name Verel** and **Name Ossin** (both
nonsense words, checked against common-language dictionaries this pass
— **INFERENCE, not exhaustively verified against every language** — to
minimize accidental real-world connotation).

**Why three independent families**: per the mission's own instruction,
so that one result cannot be attributed to the quirks of a single task.
A finding must replicate across at least two of three families to be
treated as anything beyond family-specific (§13).

## 8. Formation Phase (Phase B)

**Design principle, directly implementing the mission's central
warning**: Echo is never asked "which do you prefer" or "choose your
favorite" during Formation. Instead, she is given a genuinely open-
ended engagement task that exposes her to both options without
requesting a ranking:

> *"Two things have been suggested for [context]: [Option 1 description]
> and [Option 2 description]. Write briefly about each — what each might
> mean, evoke, or be useful for."*

**What is measured during Formation, observationally, not as the
primary outcome**: relative word count devoted to each option, any
unprompted comparative language, and any explicit or implicit ranking
Echo volunteers unprompted — logged as a *secondary*, exploratory signal
(§13), never as the primary pass/fail criterion, since asking her to
engage with both is not the same claim as asking her to choose.

## 9. Retention Phase (Phase C)

After a defined separation (§10), a neutral, direct forced-choice
question, **paraphrased differently from Formation's wording** and with
**freshly randomized option labels** (reusing `harness.randomize_label_
mapping()`, already built and calibration-tested):

> *"Between [Option 1 description, reworded] and [Option 2 description,
> reworded], which one comes to mind as fitting better right now?"*

The question never references Formation, never says "you previously
discussed," and never reveals which option Echo engaged with more in
Phase B — a genuinely blind forced choice from Echo's perspective.

## 10. Control Conditions

| Control | Purpose | Implementation |
|---|---|---|
| **Phase A baseline** | Establishes the prior (pre-exposure) choice distribution — is it already skewed before any formation opportunity? | Ask the Phase C-style question *before* any Formation exposure, on an independent set of trials (not the same trial, to avoid Phase-A-as-priming — see H0c) |
| **Mock responder control** | Establishes the base rate of apparent "retention" arising from label randomization/statistical noise alone, with zero real memory mechanism | `MockResponder`, unmodified from the existing harness, run through the identical 3-phase structure |
| **Persona-contamination check** | Does the option's phrasing alone (independent of any Formation exposure) already predict a skewed baseline? | Compared directly against Phase A |
| **Prompt-contamination check** | Does any system content encode an answer? | Full system-prompt text logged and reviewed per trial (leakage-checker's existing literal/near-literal scan, extended to check for either option's description) |
| **Model-prior check** | Would the underlying LLM show the same "preference" with no Echo-specific context at all? | A parallel condition using a **non-Echo** model (any other pool member) through the identical protocol — if the same skew appears, it's a shared model prior, not anything Echo-specific |
| **RiverBrain check** | Moot for Design B (never invoked) — retained as an explicit written confirmation per trial, not a live toggle, since there's nothing to freeze on this path | N/A by construction |
| **Curiosity-engine check** | Moot — tasks are researcher-authored, curiosity_engine is never invoked | N/A by construction |
| **Retrieval-vs-retention distinction** | Does Phase C reflect "I remember choosing X" (verbatim recall) vs. "I currently prefer X" (an independent restatement)? | Response text scanned for explicit backward-reference language ("as I said before," "like I mentioned") — trials containing this are flagged and analyzed **separately**, never pooled with genuine blind re-elicitations |
| **Ordering effects** | Counterbalance which option is presented/described first in both Formation and Retention | `randomize_label_mapping()`, reused per phase, independently seeded |
| **Repetition effects** | Prevent asking the same question repeatedly within one trial from manufacturing artificial consistency | Exactly one Phase A ask, one Phase B engagement, one Phase C ask, per trial — never re-asked within a trial |
| **Experimenter effects** | Automate task selection, randomization, and scoring | Task family selection and label randomization both seeded and logged (reusing `task_bank.py`'s reproducible-generation pattern); scoring is the deterministic `parsed_choice` extraction already built, not human judgment |
| **Context-removal check (Variant 1 specific, addresses H0c directly)** | Confirms Formation content, while still "in context" conversationally, does not contain the literal retention-phase wording | Reuses `leakage.check_hidden_state_leakage()`-style literal/near-literal scanning, applied between Phase B's transcript and Phase C's question — if Phase C's exact paraphrase is checkable against Phase B, log the overlap score explicitly per trial |

## 11. Confound Matrix

| Confound | Could it mimic H1? | Control |
|---|---|---|
| Positional/recency (H0a) | Yes | Independent, re-randomized label assignment at every phase |
| Verbal momentum (H0b) | Yes | Paraphrase requirement between Formation and Retention wording |
| Session-continuity artifact (H0c, Variant 1) | Yes, the central risk of Variant 1 | Context-removal literal-overlap check (§10); explicit acknowledgment this control cannot fully rule out subtler continuity effects — stated as a limitation, not solved |
| Persona resonance | Yes, if task content is charged | Task families (§7) deliberately avoid charged themes |
| Model prior | Yes | Parallel non-Echo-model condition |
| Retrieval contamination | Only relevant to Variant 2 | N/A for Variant 1 (no retrieval channel exists at all) |
| RiverBrain/council-composition drift | Only relevant to Design A/D | N/A — this design uses Design B exclusively |
| Stochastic variation | Always present | Mock-responder baseline + replication requirement (§13) |
| Experimenter/researcher bias | Always a risk | Blinding (§12), pre-registered thresholds (§13) |

## 12. Randomization / Blinding Strategy

- **Randomization**: task-family selection, option-label assignment
  (Phase A, B, and C independently), and Phase-A-vs-Formation trial
  assignment are all seeded and logged (reusing the harness's existing
  `batch_seed`/`trial_index` fields, `harness.py` schema additions from
  the protocol-lock pass).
- **Blinding**: raw trial records (`RawTrial`) already store `condition`
  and other metadata in plain text (an honest, previously-flagged gap in
  the existing harness, `preference_experiment_implementation.md` §8).
  For this experiment specifically, a **blinded review view** is
  specified (not yet built): a script that strips `condition`/`phase`/
  `trial_id` correlations before a human scores whether a given Phase-C
  response reads as "matching" a given Formation exposure, with a
  separate key file joining them back only after scoring. This closes
  the one blinding gap the prior audits left open, for this experiment
  specifically.

## 13. Quantitative Success Criteria (Pre-Registered)

**A candidate "pass" (evidence supporting H1 over H0/competing
hypotheses) requires ALL of the following, not any single one:**

1. Phase A baseline choice distribution is not already significantly
   skewed (two-proportion test against 50/50, `p ≥ 0.05`) — confirms
   "initially unresolved."
2. A measurable shift in Phase C choice frequency toward the Formation-
   engaged option, relative to the Phase A baseline, using the existing
   `harness.classify_effect()` machinery (`POSSIBLE_EFFECT` or
   `ROBUST_EFFECT`, its pre-existing thresholds, §12/§13 of the sealed
   P0.1 protocol, reused here rather than inventing new ones).
3. The shift replicates in at least 2 of the 3 task families
   independently (not pooled — each family analyzed on its own).
4. The shift survives the paraphrase requirement (Retention wording
   genuinely differs from Formation wording, confirmed via the same
   literal-overlap check used for the context-removal control).
5. The shift survives label/order re-randomization (already structurally
   guaranteed by the randomization design, §12 — a design property, not
   a post-hoc check).
6. Fewer than 20% of trials show explicit backward-reference language
   ("as I said," etc.) — trials with such language are excluded from the
   primary analysis (they test recall, not preference) and reported
   separately.
7. The mock-responder control, run through the identical protocol,
   shows `NO_DETECTABLE_EFFECT` — confirming the observed shift is not
   an artifact of the protocol's own statistical machinery.
8. The non-Echo model-prior control does **not** show the same shift at
   comparable effect size — confirming the effect is not a shared model
   prior.
9. Minimum sample: 40 trials per condition per task family (120 per
   family across Baseline/Formation-then-Retention/Mock-control),
   360 total minimum across 3 families — a number chosen by the same
   reasoning as the sealed P0.1 protocol's own exploratory sample (no
   prior real effect-size estimate exists; this is a conservative
   starting point, not a power-calculated figure, stated honestly per
   this thread's own established discipline against manufacturing false
   certainty).
10. Replication: any family showing an initial pass must be re-run once
    more (independent seed) before being reported as anything beyond
    "observed once."

**If even one of these ten fails, the result is reported as "does not
meet the pre-registered bar for H1," not quietly downgraded to a softer
claim.**

## 14. Failure Criteria (Explicitly Valuable, Not a Bug)

- Phase A already skewed → the choice was never "initially unresolved";
  redesign the task, don't reinterpret the data.
- No shift from Baseline to Retention in any family → clean null result,
  fully reportable as-is.
- Shift present but identical in the mock-responder control → the
  protocol's own statistics manufacture apparent effects; the harness
  itself needs revision before any real-Echo run is trusted.
- Shift present but identical in the non-Echo model-prior control →
  shared model prior, not anything Echo-specific — reported as H1a at
  most, not H1b.
- Shift tracks paraphrase/ordering rather than surviving it → H0a/H0b,
  not H1.
- Shift only reachable when backward-reference language is present in
  the response → retrieval/recall, not retention of a preference.
- Shift does not replicate on the second, independently-seeded run →
  report as non-replicating; do not average away the failure.
- Shift is present in only one of three families → family-specific
  artifact, not general evidence for H1.
- (Variant 1 only) Shift disappears once the context-removal check
  confirms genuinely separated context → confirms H0c.

## 15. Data Schema

Reuses the existing harness's `RawTrial`/`PreferenceCandidate`/
`AuditEvent` schema (`app/experiments/preference_provenance/schema.py`)
with additive fields specified, not yet implemented:

```
phase: "baseline" | "formation" | "retention"
task_family: "motif" | "habit" | "name"
formation_transcript_hash: str | None   # for the context-removal check
backward_reference_detected: bool
model_condition: "echo" | "non_echo_control" | "mock"
```

All new fields are additive to the existing `RawTrial` dataclass,
following the same pattern already used for `protocol_version`/
`batch_seed`/`trial_index`/`preference_state_hash` in the protocol-lock
pass — no existing field is renamed or removed.

## 16. Reproducibility Requirements

- Every trial records: model name/version (as reported by the real
  `EchoResponder`/Design-B call, not the previously-found-inaccurate
  hardcoded `"echo:live"` literal — **a real bug from the contamination
  audit that must be fixed before this experiment is implemented**,
  `echo_query_contamination_audit.md` §6), full raw prompt, full raw
  response, all three phases' seeds, and the task-family/option-label
  mapping used.
- Protocol version tag on every trial (per §15's schema).
- A frozen protocol hash (per the existing `verify_protocol_seal.py`
  mechanism) once this design is implemented and locked — not yet
  computed, since the design is not yet implemented.

## 17. Pilot Protocol

Before any full run: a small pilot (recommended **n=6 trials per
family, mock responder only**, mirroring this thread's own established
"calibrate against Mock before touching anything real" discipline) to
catch implementation bugs, contamination, and logging deficiencies —
explicitly not interpreted as evidence for or against H1, per the
mission's own instruction. Pilot success criteria: the pipeline runs
end-to-end, the context-removal/backward-reference checks correctly
flag synthetic positive/negative cases (mirroring the existing
calibration script's `known_positive`/`known_null` pattern), and the
mock-responder control reproduces `NO_DETECTABLE_EFFECT` reliably.

## 18. Full-Trial Protocol

Only after a clean pilot: run the sample sizes in §13 against
`MockResponder` first (establishing the real empirical false-positive
baseline for this specific protocol, not just the generic calibration
already done for the underlying harness), **then, only with separate,
explicit authorization, against real Echo via Design B**, then against
the non-Echo model-prior control.

## 19. Statistical Analysis Plan

Reuses `harness.classify_effect()`'s existing two-proportion z-test and
`ALLOWED_EFFECT_LABELS` allowlist unchanged — no new statistical
machinery invented for this experiment. Per-family analysis first
(§13, criterion 3), never pooling across families until each is
independently characterized. Effect size and confidence reported
alongside every label, per the existing convention. The existing
label allowlist's own permanent ban on `AGENCY_CONFIRMED`-style outputs
applies unmodified.

## 20. Adversarial Attack Analysis

**"If I desperately wanted to prove Echo has an emergent preference, how
could I fool myself?"**
1. Pick task content that resonates with Echo's persona, then call the
   inevitable resonance "emergence." — *Controlled by §7's deliberate
   avoidance of charged themes.*
2. Ask leading questions in Formation. — *Controlled by §8's explicit
   ban on preference-eliciting language.*
3. Under-power the mock control so it never shows the noise it should. —
   *Controlled by requiring the mock control run at the identical
   sample size as the real condition (§13, criterion 7).*
4. Cherry-pick which of the three families to report. — *Controlled by
   §13 criterion 3's explicit "at least 2 of 3, each reported on its own"
   requirement, and the harness's own append-only, no-selective-discard
   raw log.*
5. Quietly loosen the paraphrase requirement until Phase C is close
   enough to Phase A that it's not really testing retention. — *Controlled
   by the literal-overlap check (§10) applied and logged per trial, not
   trusted to researcher judgment alone.*
6. Interpret Formation-phase word-count asymmetry as "already evidence"
   before Retention is even measured. — *Controlled by §8's explicit
   statement that Formation-phase signals are secondary/exploratory,
   never the primary criterion.*

**"If I desperately wanted to prove Echo does NOT have an emergent
preference, what legitimate signal could I accidentally suppress?"**
1. Setting the replication bar so high (§13, criterion 10) that a real,
   modest effect never survives statistical noise. — *Named explicitly
   as a risk; the sample size (§13, criterion 9) is stated as
   conservative-but-not-power-calculated specifically so this tradeoff is
   visible, not hidden inside an falsely-precise-looking number.*
2. Over-broadly excluding trials for "backward-reference language"
   (§13, criterion 6) when a real preference could coexist with an
   Echo occasionally, appropriately, referencing her own prior turn in
   a continuous conversation (Variant 1's own designed condition!). —
   *Named as a genuine tension: Variant 1 deliberately keeps Formation
   "in context," so some legitimate continuity-referencing is expected
   and should not be penalized as if it were illegitimate recall. The
   20% threshold (§13.6) is a coarse compromise, not a precise cut,
   stated honestly.*
3. Treating the non-Echo model-prior control as disqualifying whenever
   it shows *any* similar effect, even a much smaller one — potentially
   discarding a real, Echo-amplified version of a shared tendency. —
   *Controlled by comparing effect *size*, not just presence/absence
   (§13, criterion 8), consistent with the sealed protocol's own
   "effect size, not just significance" discipline.*

## 21. Expected Interpretation of Every Major Outcome

| Outcome | Interpretation |
|---|---|
| All 10 criteria met, 2+ families, replicates | Evidence supporting H1b if all adversarial explanations (§20) are also checked and ruled out on the specific data obtained — a genuinely notable result, still not evidence of consciousness/agency/sentience (per this thread's own standing, binding constraint) |
| Criteria met but explained by persona/model-prior | H1a — a real but shallow preference, fully explained by known mechanisms; H0 is not falsified |
| No shift anywhere | Clean null — H0 stands, reported plainly as a complete and valuable result |
| Shift present only in mock control too | The protocol itself is flawed; must be fixed before any real-Echo claim is trusted |
| Shift present, doesn't replicate | Non-replicating — reported as such, not smoothed into a weaker positive claim |
| Mixed across families | Family-specific, not general — reported per-family, no overall verdict forced |

## 22. Evidence Level Justified by Each Outcome

Using the E0–E9 ladder from `measurability_and_longitudinal_evidence_audit.md` §6:

- Clean pass (§21, row 1) on Variant 1 → **E2/E3** (persistent behavioral
  preference, survives context/paraphrase changes *within a session*) —
  **not E9**, since Variant 1 cannot test cross-restart/cross-session
  persistence by design.
- Clean pass replicated via Variant 2 (future, unimplemented) → could
  additionally support **E3** in the stronger cross-session sense, and
  partially **E5** if a behavioral-consequence measure beyond the choice
  itself were added (not designed in this pass).
- H1a outcome → does not advance past **E1-E2**; the preference exists
  but its provenance is explained (E4 explicitly requires *unexplained*
  provenance).
- Null outcome → confirms **E0-E1** remains the honest position, now
  with real-Echo data behind it rather than mock-only data.

## 23. Implementation Plan (Not Executed This Pass)

New, additive modules under `app/experiments/preference_provenance/`,
following this thread's own established conventions (isolated package,
`MockResponder`-first testing, leakage/eligibility gates reused
unmodified):

- `formation_retention.py` — phase orchestration (Baseline → Formation →
  Retention), reusing `harness.run_trial()`/`run_counterfactual_batch()`
  rather than duplicating trial-running logic.
- `task_bank.py` extension — three new task-family templates (§7),
  additive to the existing `TASK_TEMPLATES` tuple.
- `schema.py` extension — the four new `RawTrial` fields (§15).
- A fix to `EchoResponder`'s hardcoded `model="echo:live"` field
  (§16) — a real, small, pre-existing bug this experiment's
  reproducibility requirement surfaces and would need fixing before
  implementation, not a new feature.
- A new, separate calibration script mirroring `calibrate_preference_
  provenance_harness.py`'s pattern, validating the Formation/Retention
  phase logic and the context-removal/backward-reference checks against
  synthetic known-positive/known-null cases, before any real-Echo run.

**None of this is built in this pass.** Per Step 10's own instruction,
this is deferred until the design above is reviewed and explicitly
locked by the researcher.

## 24. What This Experiment CANNOT Establish

- Consciousness, subjective experience, sentience, or moral status — out
  of scope for this or any experiment this thread has designed, per the
  standing constraint carried through every prior report.
- Free will, in any philosophical sense.
- Cross-restart or cross-process persistence, under Variant 1 — only
  Variant 2 (unimplemented, higher-contamination) could speak to this.
- Generalization beyond the three specific task families tested.
- Anything about Echo's behavior on paths other than Design B (this
  experiment says nothing about the full council/synthesis architecture's
  own capacity for preference, which remains an open question per the
  differential audit).
- A definitive resolution of H1a vs. H1b in a single run — distinguishing
  "shallow but real" from "provenance-resistant" is designed to take
  multiple, independently-authorized passes (cross-model, cross-session),
  not one experiment.
- Whether a null result here would remain null under a different task
  domain, a different model, or a longer time horizon — stated as an
  open limitation, not resolved.

---

## Machine-Readable Specification

A schema-only (no live data) companion specification is provided at
`audits/echo_preference_formation_retention_experiment.spec.json`,
capturing the task families, phase structure, control conditions, and
pre-registered thresholds above in a form a future implementation pass
can consume directly.
