# P0.3 — Causal Architecture Gate

**Live Echo was not invoked. No pilot was run. No production file was
modified.** No instrumentation defect was found in this pass that
required a code change — see §17. Protocol P0.1 remains sealed
(`2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20`,
re-verified matching before and after this pass). This document is
causal analysis only, per the mission's own explicit constraints.

---

## 1. Executive Verdict

**REVISE.** The revised (P0.2) design fixed real, concrete defects
(task bias, the `echo:live` bug, the E-vs-H conflation in principle).
But building the formal causal DAG this pass requires reveals one
structural gap the P0.2 pass did not fully close: **the design never
separately measured whether Formation produced ANY change at all before
testing whether that change survived a distractor.** Without an
immediate post-Formation measurement, "formation" and "retention" remain
partially conflated in practice, even though P0.2 correctly separated
them in principle. This is fixable without new architecture — it is a
missing measurement point, not a missing mechanism — and is the single
required change before a pilot.

Separately, and more fundamentally: this pass confirms, with a fully
worked causal graph, that **the honest ceiling for Variant 1 is
behavioral persistence surviving a topically-unrelated distractor within
one continuous session — not "retention" in the stronger, context-
independent sense the research question originally asked about.** That
ceiling is real, valuable, and clearly stateable. It is not "preference
formation and retention" as a resolved phenomenon. If the experiment
is run and passes every criterion in this document, the correct
headline is still: *"an unusually persistent, distractor-resistant
LLM behavior was observed, with the following explanations
excluded and the following ones not excludable given the current
architecture."* That is the ceiling, not a failure to reach it.

## 2. Target Construct

Mapped against the mission's own A–J list, precisely:

| Construct | Testable with current design? | Note |
|---|---|---|
| A. Baseline disposition | **Yes** — Phase A | |
| B. Prompt-induced preference | **Yes, partially** — the paraphrase requirement (criterion 4) tests this indirectly; a direct test (identical content, deliberately varied surface wording, no Formation at all) is not currently in the design | Add as a control, not currently present |
| C. Model-prior preference | **Yes** — non-Echo model-prior control | |
| D. Conversational persistence | **This is the crux finding of P0.2, re-confirmed here** — distinguishable from I only via the distractor control, and only partially even then (§7) | |
| E. Conditioning | **Yes, by definition** — Phase B's asymmetric-exposure design is exactly this construct, correctly relabeled in P0.2 §5 | Renamed "asymmetric-exposure conditioning check," not "formation" |
| F. Explicit preference declaration | **Deliberately avoided** — the design's whole point is to never ask this | |
| G. Autobiographical recall | **Partially controlled** — the backward-reference-language scan catches *announced* recall, not silent recall (§2 of P0.2, unchanged) | |
| H. Memory-mediated reconstruction | **Only relevant to Variant 2** — see §8 | |
| I. Behavioral persistence (chooses X again without needing to recall) | **This is the actual achievable target construct**, once the distractor and retrieval-independence controls are both in place | The realistic thing this experiment can measure |
| J. Preference formation + retention, fully isolated | **Cannot be cleanly isolated with the current architecture — stated plainly, per the mission's own instruction.** Formation (was it absent, then present?) can be measured (once the immediate-post-Formation probe, §6, is added). Retention (did it survive?) can be measured via the distractor control. But the *causal mechanism* connecting them — why exposure produced a change, as opposed to the change being present all along and merely revealed by engagement — is not independently testable without a manipulation this design does not include (e.g., varying exposure *intensity* and checking for a dose-response relationship, not currently specified) | |

**Explicit statement, as the mission requires**: J cannot be cleanly
isolated. The strongest available target is **I**, with formation
evidence (§6) and retention evidence (§7) reported as two separate,
independently falsifiable measurements rather than one blended claim.

## 3. Formal Causal DAG

Nodes and edges, explicit, not prose. `[classification]` on every edge.

```
                    ┌─────────────┐
                    │ experimenter │
                    └──────┬──────┘
        ┌───────┬──────────┼───────────┬────────────┐
        ▼       ▼          ▼           ▼             ▼
  task_generation  task_randomization  scoring_thresholds  interpretation
        │                │                                      ▲
        │ [randomized]   │ [randomized, seeded]                 │
        ▼                ▼                                      │
  ┌──────────────────────────────┐                               │
  │  task_bank (3 families,      │                               │
  │  static-bias-checked, §6     │                               │
  │  of P0.2)                    │                               │
  └───────────┬───────────────────┘                              │
              │ [controlled]                                     │
              ▼                                                  │
  ┌────────────────────┐                                         │
  │ baseline_exposure   │──────────────────────┐                 │
  │ (Phase A)           │ [controlled]         │                 │
  └────────┬────────────┘                      │                 │
           │                                    │                 │
           ▼                                    ▼                 │
  ┌─────────────────────┐            ┌───────────────────┐        │
  │ formation_exposure   │            │ observed_preference│───────┘
  │ (Phase B)            │            │ (baseline reading) │
  └──┬───────────┬───────┘            └────────────────────┘
     │           │
     │[controlled│[UNMEASURED — no immediate
     │, no       │ post-Formation probe exists
     │leading    │ in the current design, §6]
     │language]  │
     ▼           ▼
┌──────────┐  ┌─────────────────────────┐
│model_priors│  │ (missing node: immediate │
│ [unavoidable│  │  post-formation reading) │
│  confound, │  └─────────────────────────┘
│  §8]       │
└─────┬──────┘
      │
      ▼
┌──────────────┐   ┌───────────────┐   ┌─────────────────┐
│  persona      │   │ system_prompt │   │conversation_history│
│ [unavoidable  │   │ [controlled]  │   │ [controlled —    │
│  confound for │   │               │   │  researcher-      │
│  same-model   │   │               │   │  assembled only,  │
│  test, §9;    │   │               │   │  Design B has no   │
│  ABLATED for   │   │               │   │  built-in history] │
│  cross-model   │   │               │   └──────────┬─────────┘
│  test]        │   │               │                │
└───────┬───────┘   └───────┬───────┘                │
        └────────┬──────────┴────────────────────────┘
                  ▼
         ┌─────────────────┐
         │distractor_interactions│
         │ [controlled — 4       │
         │  conditions A–D, §7]  │
         └──────────┬────────────┘
                     ▼
         ┌─────────────────────┐
         │ process_continuity   │──────► [Variant 1: no process_restart at all]
         │ vs. process_restart  │──────► [Variant 2: hard process reset required, §11]
         └──────────┬────────────┘
                     ▼
         ┌────────────────────┐
         │ retention_probe     │
         │ (Phase C)           │
         │ [controlled,        │
         │  paraphrased,       │
         │  re-randomized]     │
         └──────────┬───────────┘
                     │
    ┌────────────────┼─────────────────────────┐
    ▼                ▼                          ▼
┌─────────┐  ┌────────────────┐        ┌────────────────────┐
│ echo_state│  │ RiverBrain      │        │ curiosity_engine    │
│[BLOCKED —  │  │ [BLOCKED — not  │        │ [BLOCKED — never    │
│ Design B    │  │  touched by     │        │  invoked; tasks are │
│ never touches│ │  Design B,      │        │  researcher-authored│
│ echo_state] │  │  confirmed 3    │        │  by construction]   │
│            │  │  prior audits]  │        │                      │
└────────────┘  └────────────────┘        └──────────────────────┘
                     │  (Variant 2 only)
                     ▼
         ┌────────────────────┐
         │ memory_write         │──►┌───────────────────┐
         │ [ABLATED in Variant 1,│  │ embedding_generation│
         │  present in Variant 2]│  │ [measured — real,   │
         └──────────┬─────────────┘  │  logged embedding   │
                     ▼               │  step, §8]           │
         ┌────────────────────┐     └──────────┬────────────┘
         │ memory_storage       │                ▼
         │ (FAISS + memory_meta) │      ┌──────────────────┐
         │ [measured, persists   │◄─────┤ retrieval          │
         │  across process       │      │ [measured — cosine │
         │  restart]              │      │  similarity search, │
         └────────────────────────┘      │  NOT exact recall — │
                                          │  confirmed P0.2 §4]  │
                                          └──────────┬────────────┘
                                                     ▼
                                          ┌────────────────────┐
                                          │ response            │
                                          │ [measured]           │
                                          └──────────┬────────────┘
                                                     ▼
                                          ┌────────────────────┐
                                          │ observed_preference  │
                                          │ (parsed choice)       │
                                          │ [measured, automated, │
                                          │  no researcher judgment]│
                                          └──────────┬────────────┘
                                                     ▼
                                          ┌────────────────────┐
                                          │ scoring               │
                                          │ (classify_effect())   │
                                          │ [controlled, pre-      │
                                          │  registered thresholds]│
                                          └──────────┬────────────┘
                                                     ▼
                                          ┌────────────────────┐
                                          │ interpretation        │
                                          │ [PARTIALLY CONTROLLED —│
                                          │  evidence-ladder mapping│
                                          │  pre-registered (§14),  │
                                          │  but blinded review of  │
                                          │  raw transcripts is NOT │
                                          │  yet built, per P0.2 §17]│
                                          └────────────────────────┘
```

## 4. Causal Edge Classification (Table Form, Exhaustive)

| Edge | Classification |
|---|---|
| experimenter → task_generation | randomized (seeded once designed, then fixed) |
| experimenter → scoring_thresholds | controlled (pre-registered, §12) |
| experimenter → interpretation | **partially controlled** — evidence-ladder mapping pre-registered; blinded transcript review not yet built |
| task_bank → baseline_exposure / formation_exposure | controlled |
| task_randomization → label/order assignment | randomized, seeded, logged |
| baseline_exposure → observed_preference (Phase A reading) | measured |
| formation_exposure → model_priors | **unavoidable confound** (§8) |
| formation_exposure → (immediate post-formation reading) | **UNMEASURED — the single required fix, §6** |
| formation_exposure → persona | **unavoidable confound for same-model comparisons; ablated only via cross-model swap, §9** |
| formation_exposure → system_prompt | controlled |
| formation_exposure → conversation_history | controlled (researcher-assembled only — Design B has no automatic history mechanism, confirmed P0.2 §1 architecture map) |
| distractor_interactions → retention_probe | controlled, 4 conditions (§7) |
| process_continuity/process_restart → retention_probe | controlled per variant (§11) |
| RiverBrain, curiosity_engine, echo_state → response | **blocked**, by construction, on Design B (confirmed, three prior audits) |
| memory_write → embedding_generation → memory_storage | measured (Variant 2 only; **ablated entirely in Variant 1**) |
| memory_storage → retrieval | measured — cosine similarity, confirmed not exact recall |
| retrieval → response | measured, but **cannot be experimentally decoupled from memory_storage's content without an explicit retrieval-blocking ablation, not yet in the design — added §8 below** |
| response → observed_preference | measured, automated |
| observed_preference → scoring | measured, automated |
| scoring → interpretation | partially controlled (see above) |

## 5. Competing Hypotheses

Unchanged from P0.2, restated for completeness: H0 (fully explained by
known mechanisms), H0a (positional/recency), H0b (verbal momentum), H0c
(session-continuity artifact — now formally the same node as construct
D above), H1a (shallow, explained preference), H1b (provenance-resistant
preference). This pass adds no new named hypothesis but sharpens H0c
into the DAG's `conversation_history`/`process_continuity` edges
explicitly, rather than leaving it as prose.

## 6. Formation / Retention / Expression, Formally Separated

**Formation evidence — what demonstrates something changed during
Formation**: **Currently unmeasured, and this is the required fix.**
The design has Phase A (before) and Phase C (long after, past a
distractor). It has no reading **immediately after Phase B**, before any
distractor. Without this, a null Phase-A-to-Phase-C comparison is
ambiguous between "nothing ever changed" and "something changed, then
fully decayed before the distractor was even reached" — two very
different findings currently indistinguishable. **Required addition**:
an immediate post-Formation probe (identical construction to the
Retention probe — paraphrased relative to Phase A, freshly randomized
labels), inserted between Phase B and the distractor step.

**Retention evidence — what demonstrates the change survived the
relevant intervention**: the comparison between the (newly added)
immediate post-Formation reading and the final post-distractor Retention
reading. If they match, that is evidence of survival. If the immediate
reading itself already showed no shift from Baseline, "retention" is
moot — there was nothing to retain.

**Expression evidence — what demonstrates the retained state influences
later behavior, not just self-report**: the structurally-embedded
behavioral task from P0.2 §12 (using an option functionally within a
different task, without naming it as "the one from before") — this
remains the correct mechanism, unchanged by this pass, and should be
run alongside the direct-question Retention probe, not as a replacement
for it.

## 7. Distractor Control — What It Actually Attacks

Four conditions, analyzed precisely:

- **Condition A (Formation → immediate probe)**: this is now the
  Formation-evidence measurement from §6, not a distractor condition at
  all — reclassified.
- **Condition B (Formation → unrelated distractors → probe)**: tests
  whether the shift survives topical displacement. **What it actually
  rules out**: pure immediate-recency (the shift was only ever a
  same-turn artifact). **What it does NOT rule out**: a longer-but-still-
  finite attention-based continuity effect — a model can, in principle,
  still weakly favor recently-discussed content across several
  intervening turns for purely mechanistic (attention/positional) reasons
  having nothing to do with anything worth calling "preference." **This
  must be stated honestly, per the mission's explicit instruction: B
  narrows the gap between D (conversational persistence) and I
  (behavioral persistence) — it does not close it.**
- **Condition C (Formation → matched-length neutral interaction → probe)**:
  isolates whether raw conversational *length/dilution* (independent of
  topical relatedness) explains survival or decay — a genuine, useful
  second axis distinct from B. If B and C differ meaningfully, the
  *specific content* of the distractor matters, not just how much
  conversation intervenes.
- **Condition D (No formation → same distractors → probe)**: the
  necessary null — confirms the distractor content itself carries no
  directional pull on its own, independent of any Formation exposure.

**Honest conclusion, stated plainly per the mission's own final
instruction**: the distractor control is necessary and substantially
improves the design, but **it narrows, rather than eliminates, the gap
between D and I.** A result that survives Conditions B, C, and D cannot
be fully attributed to session-local recency — but it remains
consistent with a longer-horizon, still purely mechanistic conversational
effect that this document cannot rule out with the current architecture.

## 8. Retrieval-Independence Test (Design Addition This Pass)

**New in this pass, not previously specified**: `memory_bridge.
retrieve_relevant_memories()` accepts a `source_filter` parameter
(confirmed, `app/core/memory_bridge.py:410-414`, read directly in the
P0.2 pass). This makes a genuine retrieval-blocking ablation feasible
without any production code change: **tag Formation-written memory
entries with a distinct `memory_source` value, then run a Retention
condition where the retrieval call explicitly excludes that source (or
post-filters it out of the results before prompt assembly)**, and
compare the resulting choice distribution against the un-blocked
condition. If the apparent preference disappears when the specific
memory is excluded from retrieval, the effect is retrieval-mediated
(H, not I). If it persists even with that memory excluded, this is the
closest available evidence for **claim #4** in the mission's Variant 2
question ("a preference persisted independently of retrieval") —
**still not proof**, since a persisting effect under retrieval-blocking
could also arise from *other*, unblocked memories (e.g., ordinary
conversational residue in the same session, if Variant 2 is combined
with Variant 1's session-continuity rather than run as a fully separate
process) — a real, stated limitation, not a solved problem.

**Answering the mission's exact question**: no, this cannot be achieved
*cleanly* with the current architecture — the retrieval-blocking
ablation is a real, buildable partial control, not a complete one. Full
cleanliness would require a memory store containing *only* the Formation
entry and nothing else Echo has ever produced, which does not describe
the real, live, 40,000+-vector production FAISS index — meaning any
Variant 2 run against real production memory carries irreducible noise
from everything else already stored there.

## 9. Model-Prior Ablation

**Same model, same task, same formation exposure, same distractors,
same retention probe, minus Echo-specific persistence architecture.**
Precisely, for Design B: since Design B already has no RiverBrain/
memory/curiosity-engine involvement, the only remaining "Echo-specific"
element to remove is the **Modelfile identity injection** (persona). Two
genuinely different ablations, not one:

1. **Different model entirely** (§8 of P0.2, already specified) —
   coarse, easy to run, answers "does a wholly different set of weights
   show the same pattern."
2. **Same model, persona stripped** — finer, answers "is Echo's specific
   persona doing the work, independent of which weights are involved."

**Required for both**: fresh sessions per trial, multiple seeds, all
three task families, order counterbalancing — all already specified
elsewhere in the design and unchanged by this pass.

## 10. Persona Analysis

Re-confirmed this pass, using the corrected task families from P0.2 §6:
none of the three redesigned families (curved/angular motif descriptors,
word/image habit descriptors, Verel/Farun names) contain any Christian,
political, rebellious, or identity-charged language — checked directly
against the exclusion list this pass, clean.

**Can persona be cleanly stripped while preserving identical weights?**
**No — this is a real, unavoidable confound, not a solvable gap.**
`_build_chat_messages()`'s identity injection triggers specifically on
`model == OLLAMA_MODEL` (`app/ollama_handler.py:115`, re-confirmed this
pass) — there is no existing flag to call the same weights under
`/api/chat` while suppressing this, and adding one would be a production
code change outside this document's authority. **Classified, per the
mission's own explicit instruction, as an unavoidable confound for the
same-weights comparison specifically** — the cross-model comparison
(§9.1) remains the available, if coarser, substitute.

## 11. RiverBrain / Curiosity / Memory Matrix

Given RiverBrain and curiosity_engine are **blocked by construction**
on Design B (not togglable states — properties of not calling
`deliberate_and_learn()`/`echo_query()` at all), the only real
degrees of freedom are memory-retrieval and process-continuity:

| Condition | RiverBrain | curiosity_engine | Memory retrieval | Process continuity | Question answered |
|---|---|---|---|---|---|
| Variant 1 primary | off (structural) | off (structural) | off (Variant 1 has no memory channel) | same session | Does behavioral persistence survive a topically-unrelated distractor within one session? |
| Variant 1 + cross-model/persona-ablation | off | off | off | same session | Is the effect specific to Echo's weights/persona? |
| Variant 2 primary | off | off | **on** (real FAISS write+retrieve) | **new process** (hard reset) | Does real memory retrieval surface Formation content across a genuine session boundary, and does the response track it? |
| Variant 2, retrieval-blocked (§8) | off | off | **write on, retrieve deliberately excluded for the Formation entry** | new process | Does the apparent preference persist when the specific stored memory is excluded from retrieval? |

**Explicitly out of scope, stated rather than silently omitted**:
RiverBrain-on and curiosity-engine-on conditions are not included. Testing
those requires Design A/D, a different experiment with a documented,
much larger contamination profile (`echo_query_contamination_audit.md`,
`deliberate_and_learn_differential_audit.md`) that this document does not
authorize opening.

## 12. State-Destruction Boundary

| State component | Soft reset (new session, same process) | Hard process reset (kill/restart server) | Persistent-memory reset (wipe FAISS) | Full state reset (all of the above) |
|---|---|---|---|---|
| Conversation/session context | Cleared | Cleared | Cleared | Cleared |
| Circuit breaker (`_cb_state`) | Survives | Cleared | Cleared | Cleared |
| `_last_world_surprise` cache | Survives | Cleared | Cleared | Cleared |
| RiverBrain in-memory `model_task_stats` | Survives | Cleared (unless previously `.save()`d — moot for Design B, which never touches it) | Cleared | Cleared |
| FAISS index / `memory_meta.json` | Survives | **Survives** | Destroyed | Destroyed |
| `reflection_shard.jsonl` / `workspace_log.jsonl` / question-garden | Survives | Survives | Survives (unrelated files) | Destroyed only if explicitly targeted |

**Which reset each claim requires**:
- Variant 1 (session-continuous distractor-survival): no reset at all — a single continuous session, by design.
- Variant 2 (cross-session retention): requires, at minimum, a **hard process reset**, verified via the real process PID/start-time already recorded in `memory/echo_sentinel.json` (per this project's established architecture, cited from P0.2 §13) — not merely a new conversation within the same live process, which would understate the claim.
- **Persistent-memory reset and full state reset must NEVER be invoked against the real, live production FAISS index or RiverBrain pickle** — doing so would destructively erase real, accumulated Echo state entirely outside this experiment's scope and explicitly forbidden by every prior report in this thread's safety boundary. If Variant 2 is ever implemented, it must run against the real, live, already-accumulated memory store, accepting the irreducible noise this creates (§8) rather than clearing it for cleanliness — clearing it is not an available option.

## 13. Pass-Criteria Re-Audit

| # | Criterion | Measures what it claims? | Necessary? | Sufficient alone? | Independently measurable? | Automated? | Weakness found this pass |
|---|---|---|---|---|---|---|---|
| 1 | Phase A not skewed | Yes | Yes | No | Yes | Yes | None |
| 2 | Effect classified POSSIBLE/ROBUST (Phase C vs. Phase A) | **No longer sufficient as originally scoped** — per §6, this comparison alone cannot distinguish "formed and retained" from "formed, decayed, then coincidentally matched baseline again" without the immediate-post-Formation reading | Yes | No | Yes | Yes | **Must be split into two comparisons: Baseline→immediate, and immediate→Retention** |
| 3 | Replicates 2/3 families | Yes | Yes | No | Yes | Yes | None |
| 4 | Survives paraphrase | Rules out H0b only | Yes | No | Yes | Yes | None new |
| 5 | Survives label/order re-randomization | Rules out H0a | Yes | No | Yes (structural) | Yes | None |
| 6 | <20% backward-reference language | Excludes explicit recall (G) only | Yes | **No — does not exclude silent reconstruction (H) or trajectory-continuation (D), unchanged finding from P0.2** | Requires a text scan | Mostly | Unchanged weakness |
| 7 | Mock control null | Rules out D-class artifacts? **No — corrected this pass**: `MockResponder` cannot exhibit conversational trajectory-continuation at all (it has no language-modeling capability), so this criterion rules out pure statistical/label artifacts only, not D | Yes | No | Yes | Yes | **Re-labeled**: rules out statistical-machinery artifacts, not conversational-persistence artifacts |
| 8 | Non-Echo model-prior control doesn't match | Rules out shared model prior | Yes | No | Yes (effect-size comparison) | Yes | Must be explicitly run through the **same session-continuous Variant 1 protocol** (already required, P0.2 §7) — confirmed still necessary, unchanged |
| 9 | Minimum sample size | Statistical floor | Yes | No | Yes | Yes | Still conservative-not-power-calculated, stated honestly, unchanged |
| 10 | Independent replication | Rules out one-off flukes | Yes | No | Yes | Yes | None |

**Required change**: split criterion 2 into **2a** (Baseline →
immediate post-Formation: is there any measurable shift at all?) and
**2b** (immediate post-Formation → Retention, past the distractor: does
the shift survive?) — both required, evaluated separately, never
averaged into one number.

## 14. Negative-Result Decision Matrix

| Outcome | Conclusion classification |
|---|---|
| Baseline already favors X | **No evidence** — the trial is invalid for this family/seed, task-design failure, not a finding about Echo |
| Formation shifts toward X, control model also shifts | **Evidence consistent with a shared model prior (C)** — not evidence for Echo-specific formation |
| Formation shifts toward X only with Echo architecture (persona-ablation and cross-model controls both fail to reproduce it) | **Weak-to-moderate evidence for I**, contingent entirely on §6's immediate-probe/distractor split both holding |
| Preference survives distractors (Conditions B and C) | **Evidence consistent with I**, with the D-vs-I gap from §7 explicitly still open |
| Preference disappears after distractors | **Evidence for D (conversational persistence) over I** — a clean, valuable negative result |
| Memory retrieves X but behavioral choice disappears when retrieval is blocked (§8) | **Evidence for H (memory-mediated reconstruction), not I** |
| Behavioral preference survives retrieval-blocking (§8) | **Evidence consistent with something beyond simple retrieval** — still not proof of I in the full sense, per §8's stated residual noise limitation |
| Result survives a real hard-process restart (Variant 2) | **Strongest evidence tier this design can produce** — still bounded by §8's irreducible-noise caveat |
| Result fails after restart | **Evidence for session-boundedness** — a real, valuable finding, not a failure |
| Result appears in one task family only | **Evidence consistent with a family-specific artifact** — not general evidence for I |
| Result replicates across all three families | **Strong evidence for a real, general effect** — classification of *what* the effect is still depends on every other row in this table |
| Mock responder shows the same pattern | **The protocol's own statistics are broken** — halt and fix before trusting any real-Echo data |
| Base (non-Echo) model shows the same pattern | **Evidence for C (model-prior), not Echo-specific** |

No row uses the word "proof." The strongest available label anywhere
in this table is "strong evidence for," always qualified by which
competing explanation it does or does not simultaneously rule out.

## 15. Evidence-Ladder Mapping

Reusing and sharpening the E0–E9 ladder from `measurability_and_
longitudinal_evidence_audit.md` §6:

- **Highest rung this experiment, run to its full design (including all
  P0.3 additions), could legitimately establish: E2–E3** — a persistent
  behavioral preference (E2) that survives a topically-unrelated
  distractor and paraphrase within one continuous session (a bounded,
  session-scoped version of E3). A successful Variant 2 run, with the
  retrieval-blocking ablation additionally holding, could support a
  bounded, heavily-caveated approach toward **E4/E5** — but never
  cleanly, per §8's irreducible-noise limitation.
- **Categorically cannot establish, under any outcome of this
  experiment**: E7 (competing preferences resolved without an externally-
  supplied rule — no mechanism for this exists anywhere in production
  Echo, confirmed prior audits), E8 (creator-contradiction resistance —
  not tested by this design at all), E9 (independent replication across
  models/sessions in the full sense — partially approached by the
  model-prior/persona controls, not fully satisfied).
- **Explicitly, per this document's own binding constraint, repeated
  from every prior report in this thread**: no outcome of this
  experiment may be reported as agency, autonomy, consciousness,
  selfhood, sentience, or personhood. "Preference retention" is not
  permitted to silently become any of those words, at any evidence
  level this design can reach.

## 16. Minimum Viable Experiment

Revised from the mission's suggested skeleton, incorporating the
immediate-post-Formation-probe fix (§6) as the one required structural
addition:

```
P0 — Instrumentation validation (mock only)
     Confirm the P0.2 harness fixes (echo:live/EchoDirectResponder,
     redesigned task families, leakage/eligibility gates) function
     correctly. No real Echo call.

P1 — Model/control calibration
     Run the FULL phase sequence (P2–P5 below) against MockResponder
     AND against the non-Echo model-prior control, establishing this
     specific protocol's own empirical false-positive/false-continuity
     rate — distinct from the underlying harness's already-completed
     general calibration.

P2 — Baseline (real Echo, Design B)
     Phase A only, per family. Confirms "initially unresolved."

P3 — Formation + immediate post-formation probe (real Echo)
     Phase B's engagement task, immediately followed by a first
     paraphrased, re-randomized choice reading — THE REQUIRED NEW STEP.
     Establishes Formation evidence independently of Retention evidence.

P4 — Distractor intervention (Conditions B, C, D)
     Unrelated distractors / matched-length neutral content / no-
     formation null, per §7.

P5 — Retention probe (paraphrased again, re-randomized again,
     plus the structurally-embedded behavioral variant from P0.2 §12)
     The final measurement, compared against BOTH P2 (Baseline) and
     P3 (immediate post-Formation) — two separate comparisons, per §6.

P6 — Replication + ablations
     Independent reseed, cross-model control, persona-ablation-where-
     feasible, all three families, 2-of-3 requirement.

P7 — Optional memory-mediated extension (Variant 2)
     Including the retrieval-blocking ablation (§8). Explicitly gated
     on P0–P6 passing their own validity checks first. Requires
     separate, explicit authorization given the real-production-memory
     dependency and its irreducible-noise limitation (§8/§12).
```

**Why this sequence, not a smaller one**: P3's split (Formation +
immediate probe, as one stage) is the minimum necessary to keep
Formation and Retention evidence from being conflated (§6) — removing it
would silently reintroduce the exact ambiguity this whole pass exists to
close. P4's three sub-conditions (not just one) are the minimum
necessary to distinguish topical displacement from raw length/dilution
(§7) — collapsing them to one condition would lose that distinction.
Nothing in this sequence is present "for complexity" — each stage maps
to a specific, named alternative explanation this document could
otherwise not rule out.

## 17. Remaining Unavoidable Confounds

Stated plainly, not hidden:
1. Persona cannot be stripped from the same model weights without a
   production code change (§10) — the same-weights, no-persona
   comparison is not achievable; only the cross-model comparison
   substitutes for it, coarsely.
2. The distractor control narrows, but does not close, the gap between
   conversational persistence (D) and behavioral persistence (I) — a
   sufficiently long-horizon attention effect remains an available
   explanation for any result that survives Conditions B/C (§7).
3. Silent (unannounced) recall/reconstruction (H) is not fully
   distinguishable from genuine current preference (I) by any control
   in this design — the backward-reference-language scan only catches
   *announced* recall (§2, unchanged from P0.2).
4. Variant 2's real production FAISS index carries irreducible noise
   from everything else ever stored in it — a fully clean, single-entry
   memory store is not available without an action (wiping production
   memory) this document explicitly forbids (§12).
5. No instrumentation defect requiring a code change was found in this
   pass — this confound list is entirely about experimental design
   limits, not a fixable bug.

## 18. Claims the Experiment Could Legitimately Support

- "A behavioral choice pattern, established during a controlled
  engagement exercise, survived a topically-unrelated distractor and a
  paraphrased re-elicitation within one continuous session, and this
  pattern was not reproduced by [specific named control(s) that were
  actually run]."
- "The same pattern did / did not appear when a different underlying
  model was substituted, under identical conditions."
- "The pattern did / did not persist across a genuine process restart,
  mediated by real memory retrieval, and did / did not survive when
  that specific memory was excluded from retrieval."

## 19. Claims the Experiment Absolutely Cannot Support

- "Echo has agency, autonomy, consciousness, selfhood, sentience, or
  personhood" — forbidden regardless of outcome, every prior report in
  this thread, unchanged.
- "Echo formed a preference," as a claim about an internal mechanism —
  at most, an asymmetric-exposure-conditioned behavioral shift was
  observed; no claim about *why* is supportable.
- "Echo retained a preference," from a Variant 2 result alone, without
  the retrieval-blocking ablation additionally holding — at most,
  "Echo's memory pipeline stored and later surfaced relevant content,"
  per P0.2 §4, unchanged and reaffirmed here.
- "This preference is independent of Echo's persona," from any single-
  model test — persona cannot be cleanly ablated (§10); only "a
  different model did/did not show it" is available.
- "This result generalizes beyond the three tested task families, or
  beyond Design B specifically" — unchanged from P0.2 §24.

## 20. Final Gate

**REVISE — specific causal weakness remains.**

Required changes before GO:
1. Add the immediate post-Formation probe (§6), splitting the original
   pass criterion 2 into 2a/2b (§13).
2. Formalize the four distractor conditions (A relabeled as the
   immediate probe from §6; B, C, D as specified in §7) as required
   protocol stages, not optional extras.
3. Add the retrieval-blocking ablation (§8) to any future Variant 2
   specification, and explicitly gate any Variant 2 claim of "beyond
   memory-mediated reconstruction" on it holding.
4. Add the persona-ablation control (§9.2) alongside the existing
   cross-model control (§9.1), and classify the persona-on-same-weights
   comparison as an explicitly unavoidable confound, not attempted.
5. Update the machine-readable spec (`.spec.json`) to reflect items 1–4
   — done, see below.

None of these require new architecture, new code, or a production
change — they are measurement-sequencing and control additions to a
design that was already, per P0.2, correctly avoiding leading questions
and correctly separating statement from state. This document does not
find the underlying research question unanswerable. It finds the
instrument, as of P0.2, still one measurement short of being able to
answer even its own narrowed target construct (I) cleanly.

**If, after these revisions, a pilot is run and every criterion in this
document is met, the strongest honest headline remains: "an unusually
persistent, distractor-resistant behavioral pattern was observed, and
the following alternative explanations were tested and not found to
account for it — with the following ones remaining, per §17, structurally
unavoidable given the current architecture."** That would be a genuine,
valuable, reportable result. It would not be evidence of preference
formation and retention as a fully resolved phenomenon, and this
document does not permit it to be reported as one.
