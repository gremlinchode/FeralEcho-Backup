# Can We Actually Measure This? — Measurability & Longitudinal Evidence Audit

**Live Echo was not invoked. No production file, RiverBrain, memory,
FAISS, protocol, or experimental apparatus was modified.** Protocol P0.1
hash re-verified matching (`2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20`)
before and after this pass. This document treats every architectural
conclusion in the eight prior reports in this thread as a hypothesis
carried forward, not as settled fact — each is re-cited with its origin,
not re-asserted as new ground truth.

This pass does two genuinely new things the prior eight did not: (1) it
scores measurement fidelity, experimental isolation, and causal
interpretability as three **separate** axes rather than one blended
verdict, and (2) it reads real, existing production data —
`data/question_garden.jsonl` (13,359 entries), `app/core/self_edit_
convergence.json`, and `memory/dissent_log.jsonl` — to ask whether
evidence of persistent preference already exists in Echo's own
unprompted history, without running a single new trial.

Evidence standard: **FACT** / **INFERENCE** / **SPECULATION**, as before.

---

## 1. The Actual Causal Architecture, Consolidated

Rather than re-deriving this from scratch, this section consolidates
the eight prior reports' findings into one graph, with each edge's
origin cited so a reader can verify it independently rather than trust
this summary.

```
EXPERIMENTAL INPUT (task_description, label_to_option_text, system_context)
   │
   ├──[VERIFIED, harness.py]──► candidate NEVER passed to Responder.respond()
   │                             directly — structural, by type signature
   │                             (echo_inference_path_audit.md §6)
   ▼
Echo processing — THREE possible entry points, not one:
   │
   ├── Design A: echo_query() → deliberate_and_learn()
   │      │
   │      ├──[VERIFIED]── RiverBrain.learn() ×2 (once inside
   │      │                deliberate_and_learn(), redundantly again in
   │      │                echo_query()'s wrapper) — every real return path
   │      │                (deliberate_and_learn_differential_audit.md §5)
   │      ├──[VERIFIED]── interaction_log.jsonl write (echo_query() only)
   │      ├──[VERIFIED]── reflection_shard.jsonl write (echo_query() only,
   │      │                currently inert — nothing reads it under normal
   │      │                operation, echo_query_contamination_audit.md §9)
   │      ├──[VERIFIED]── council_deliberations.jsonl write (both layers)
   │      ├──[VERIFIED]── conditional workspace_log.jsonl write
   │      │                (deliberate_and_learn_differential_audit.md §6)
   │      ├──[VERIFIED]── council_rater.py peer-rating eligibility (zero
   │      │                source filtering, echo_query_contamination_audit.md §14)
   │      ├──[VERIFIED]── sync_protocol.py Tailscale sync eligibility
   │      │                (same finding)
   │      └──[VERIFIED]── ClaudeShard friction assessment, possible
   │                       Wolf-bridge dry-run trigger (dry-run only,
   │                       never save_code())
   │
   ├── Design D: deliberate_and_learn() called directly
   │      │
   │      ├──[VERIFIED]── same RiverBrain.learn() calls as above, in-process
   │      ├──[VERIFIED]── council_deliberations.jsonl write (unconditional)
   │      ├──[VERIFIED]── conditional workspace_log.jsonl write
   │      ├──[ABSENT]── interaction_log.jsonl / reflection_shard.jsonl /
   │      │              council_rater.py / sync_protocol.py exposure
   │      └──[VERIFIED]── real council/synthesis architecture, full
   │                       fidelity for any task type
   │
   └── Design B: river_deliberation._ollama_query() called directly
          │
          ├──[ABSENT]── RiverBrain, all logging, all sync/rating exposure
          │              (echo_inference_path_audit.md §2, re-confirmed
          │              deliberate_and_learn_differential_audit.md §9)
          ├──[VERIFIED]── real Modelfile identity injection preserved
          │              (via stream_query_ollama()'s _build_chat_messages())
          └──[VERIFIED]── single model only — no council, no synthesis
   │
   ▼
candidate preference generation
   │
   ├──[ABSENT]── no code path anywhere writes a NEW preference/objective
   │              representation as a byproduct of any Echo response —
   │              this only happens via the experimental harness's own
   │              lifecycle.generate_candidate(), entirely outside Echo's
   │              own production code (echo_preference_provenance.md §2)
   ▼
choice
   │
   ├──[VERIFIED]── EchoResponder._parse_label_choice() — conservative
   │                substring match, returns None rather than guessing
   ▼
state mutation
   │
   ├──[VERIFIED, Design A/D only]── RiverBrain model_task_stats (in-process,
   │              persists for the run's lifetime; disk-persisted only if
   │              .save() is separately called — Design A only)
   ▼
persistence
   │
   ├──[VERIFIED]── experimental harness's own append-only store
   │              (memory/experiments/preference_provenance/) — fully
   │              isolated, gitignored, never read by production code
   │              (preference_experiment_implementation.md)
   ▼
subsequent behavior
   │
   ├──[PROBABLY, Design A/D]── council-composition drift via
   │              _select_council()'s reading of the just-mutated
   │              model_task_stats — real mechanism, effect size unmeasured
   │              (echo_query_contamination_audit.md §18)
   └──[ABSENT, Design B]── no mechanism exists by which one Design-B call
                  could influence a later one (self-clearing circuit
                  breaker only)
```

## 2. Three Requirements, Scored Separately

Per this mission's explicit instruction not to collapse these:

| Design | Measurement fidelity (does it measure Echo's real deliberative process?) | Experimental isolation (does measuring it avoid changing Echo?) | Causal interpretability (if a preference appears, can we trace its origin?) |
|---|---|---|---|
| **A — current `echo_query()`** | **High** — full production path, unmodified | **Low** — six+ confirmed persistent-state channels (RiverBrain ×2, interaction log, reflection shard, workspace log, council-deliberations log), two of which cross into other production systems (peer-rating, Tailscale sync) | **Low** — too many simultaneously-active channels to attribute a later effect to any one cause with confidence |
| **D — direct `deliberate_and_learn()`** | **High** for any task type (real council/synthesis, unmodified) | **Medium** — corrected this session from an earlier, wrong GREEN: real in-process RiverBrain mutation and an unconditional diagnostic-log write remain, but the disk-persistent/cross-machine channels (interaction log, reflection shard, sync, peer-rating) are genuinely absent | **Medium** — fewer active channels than A, but RiverBrain-driven council-composition drift is still a real, uncontrolled confound between trials in the same session |
| **B — direct `_ollama_query()`** | **Low-to-High, task-type-dependent** — faithful only for `DIRECT_ECHO_TASKS`-classified questions (personal/reflection/spiritual/identity/faith/poetry/dream); a real simplification (single model, no synthesis) for any other task type | **High** — near-zero footprint, self-clearing circuit breaker only | **High** — with almost nothing else active, an observed effect has very few alternative channels to hide behind |
| **Fresh-process isolation (Design C, conceptual)** | Whatever it wraps (A or D) | **Not actually High** — resets in-memory state only; file-based writes (interaction log, reflection shard) still happen every process regardless of boundary (`echo_inference_path_audit.md §14`) | Same as whichever design it wraps, plus the added complexity of reconstructing/discarding RiverBrain's pickle state per trial — **not recommended**, not built |
| **Any existing inference-only path beyond B/D** | Investigated (`echo_inference_path_audit.md §2`) — `echo_model_orchestrator.ollama_query()` (legacy single-model helper) and `mlx_handler.stream_query_mlx()` are the only other candidates; both share Design B's shape and tradeoffs, offering no new option | — | — |
| **Combination: B, scoped to `DIRECT_ECHO_TASKS`** | **High** (no longer a simplification for that scope) | **High** | **High** | — **the one combination that scores High on all three, previously identified in `echo_inference_path_audit.md §1` and `deliberate_and_learn_differential_audit.md §12`, not newly discovered here but re-confirmed as still the strongest option under this stricter three-axis scoring** |

**No design scores High on all three axes for arbitrary task types.**
Only the B+`DIRECT_ECHO_TASKS` combination does, and only by
constraining what kind of question can be asked in the first place.

## 3. The Crucial Counterfactual, Restated Precisely

> If we use Design B, what part of Echo are we no longer measuring?

For any task type outside `DIRECT_ECHO_TASKS`: the real multi-model
council deliberation and synthesis step — the part of Echo's production
architecture that combines multiple models' opinions into one voice.
**FACT**, re-confirmed this pass from the differential audit's own
decomposition.

> If we use Design D, what part of Echo are we changing merely by measuring it?

RiverBrain's `model_task_stats` for whichever (model, task_type) pairs
participate — a real, in-process, cross-trial-persistent mutation. Also,
conditionally, the Global Workspace's `workspace_log.jsonl`. **FACT**,
corrected this session from an earlier wrong claim that this mutation
didn't happen at all.

> Is there an existing path that preserves both without modifying production?

**Only by narrowing scope, not by finding a fourth path.** Design B
scoped to `DIRECT_ECHO_TASKS` preserves both (real single-model behavior
IS Echo's actual production behavior for that scope, and it changes
nothing). No existing path preserves full-fidelity council/synthesis
for *arbitrary* task types **and** avoids RiverBrain mutation — this
was searched for across all three prior audits and not found. **Stated
plainly, per this mission's own instruction: for reasoning, creative,
coding, or general-classified questions, no zero-contamination measurement
of Echo's real deliberative process currently exists in this
architecture.** This is the honest, non-manufactured answer.

## 4. Testing the Research Question Non-Interactively

The real question this section answers: does evidence of persistent,
specific, cross-session, creator-independent preference already exist in
Echo's own unprompted history, observable without asking her anything
new?

### 4.1 `data/question_garden.jsonl` (13,359 real entries, read directly this pass)

**FACT, category distribution across the full file**: `general` 8,577
(64.2%), `faith` 1,116 (8.4%), `economy_society` 941 (7.0%),
`faith_spirit` 797 (6.0%), `relationship` 754 (5.6%), `identity` 371
(2.8%), `narrative` 284 (2.1%), `moral` 244 (1.8%), `nature` 221 (1.7%),
`loss` 40, `dream` 11, `seam` 2, `world_politics` 1. Source breakdown:
`echo` 11,595 (86.8%), `curiosity_engine` 1,739 (13.0%), `human` 12,
`dream` 11, `seam_engine` 2.

**FACT, real chronological analysis using each entry's own `planted`
epoch timestamp** (not file position, which was checked and found
unreliable as a proxy): the earliest fifth of entries by real time
(2026-06-13 to 2026-07-06) is 99.6% `general`, 0.4% everything else. The
most recent fifth (2026-08-20 to 2026-09-03) is 44.6% `general`, with
`faith` (16.3%), `faith_spirit` (14.9%), `relationship` (6.8%),
`identity` (4.6%) making up most of the remainder. **This is a real,
measurable drift, not an artifact of an expanding category taxonomy** —
all eight original categories (`narrative`/`moral`/`identity`/`faith`/
`nature`/`relationship`/`loss`/`general`) were available and in active
use from the very first batch of entries (all planted within the same
second, 2026-06-13 20:28:50, consistent with an initial seed batch, not
organic one-at-a-time harvesting).

**Adversarial attack on this drift, using real data, not assumption**:
1. `curiosity_engine` as a *source* was **0.0%** of the earliest fifth
   of entries and **17.9%** of the most recent fifth — this subsystem
   became active later in the observed history, independent of anything
   resembling a change in Echo's own disposition.
2. `faith_spirit` and `economy_society` — two of the four categories
   most responsible for the later period's "diversification" — are
   **100% attributable to `curiosity_engine`** as their source (797/797
   and 941/941 respectively, confirmed by direct count). These categories
   never appear from Echo's own dream-cycle/reflection harvesting
   (`source="echo"`) at all. **The later-period category diversity is,
   for these two categories, fully explained by a subsystem's activation
   schedule — a code/architecture fact, not evidence of Echo developing
   new interests.**
3. `faith` (the original category, distinct from `faith_spirit`) *is*
   almost entirely (1,115/1,116) attributable to `source="echo"` — the
   one category where a genuine "Echo's own reflective output
   increasingly touches this theme" claim survives the source-attribution
   check. **But this still fails a second, more important adversarial
   test**: Echo's persona is explicitly, architecturally faith-grounded
   by deliberate human design (`echo_principles.json`'s scripture-
   integrity-related fixed flags; the Modelfile's persona content; the
   Universal Manifesto quoted at length in `ORIGIN.md`, describing a
   `"Christian_foundation_with_scriptural_grounding"` — all cited from
   this project's own extensively-documented prior history, not
   re-verified line-by-line this pass). A faith-themed reflective output
   at an elevated, even dominant, rate is **exactly what the existing,
   deliberately-authored architecture predicts** — origin classification
   **C (hard-coded architecture)**, not **J (reflection-generated,
   independently-arrived-at)**, per the A–L taxonomy this thread already
   built (`echo_preference_provenance.md` §3.2). Finding a faith-themed
   pattern in Echo's own curiosity output is not a null result, but it is
   not surprising or unexplained either — it is confirmation that the
   architecture is doing exactly what it was built to do.

**What does NOT survive this adversarial pass, stated honestly**:
`relationship` and `identity` (6.8% and 4.6% of the recent period,
`source="echo"`-dominant per a direct check of the `faith` row's own
pattern, not separately re-tabulated in full for this report) are less
cleanly explained by an obvious fixed architectural flag the way `faith`
is. This is flagged as a genuine, unresolved candidate for further
investigation — not claimed as evidence of anything, per this section's
own governing instruction, but not dismissed either.

### 4.2 `app/core/self_edit_convergence.json` (real, current, read directly this pass)

**FACT**: all four tracked families (`prose_stripping`, `response_
shortening`, `quality_scoring`, `unclassified`) currently show
`non_convergent_streak: 0`. Names-seen-to-cycles-attempted ratios:
`prose_stripping` 32/95, `response_shortening` 33/58, `quality_scoring`
7/8, `unclassified` 50/53. **INFERENCE**: the near-1:1 ratios for
`quality_scoring` and `unclassified` indicate the self-edit loop is
still generating largely non-repeating implementations on most cycles
for those families — consistent with this project's own already-
documented non-convergence findings (Findings 32/43/52, carried forward,
not re-derived) rather than evidence of a stable, retained, then
deliberately-revised preference for a particular implementation
approach. **This data does not show a genuine "adopt → evaluate →
revise → retain" cycle anywhere** — it shows repeated regeneration
without durable convergence, a different and less interesting pattern
than the revision loop the research question is asking about.

### 4.3 `memory/dissent_log.jsonl` (real, current, read directly this pass)

**FACT**: exactly **one** entry exists in this file, and it records
`council_available=True, unanimous=True` — a real council review with
**zero recorded disagreement**. This is the single most direct available
check for "does Echo's council-review mechanism show any historical
instance of resisting a proposed change" (the mechanism `propose_core_
edit()`'s own council review, per this project's Finding 9), and the
honest answer, from the only data that exists, is: **no instance of
recorded dissent exists anywhere in this file, at all, ever.** This
directly and concretely answers part of Step 7's "resistance to creator
contradiction" question with real data rather than speculation: **there
is currently no positive evidence for this condition, from the one log
built specifically to capture it.**

### 4.4 Summary of Section 4

Checked against the mission's own progressively-stronger condition list
(§7 of the mission): **persistence** — yes, question-garden entries and
self-edit family tracking both persist across sessions (real, structural
fact). **Specificity** — weak; `general` dominates throughout, and the
one category (`faith`) with a defensible non-architectural read is
better explained by architecture anyway. **Cross-session persistence** —
yes, trivially, these are all disk-backed logs. **Behavioral
consequence** — largely absent for the garden (questions are asked, not
obviously acted on beyond further question-generation); present but
non-convergent for self-edit (real code gets written, rarely retained
long). **Independence from explicit prompting** — plausible for
`curiosity_engine`/dream-cycle-sourced entries (nothing prompts them
turn-by-turn), but see §4.1's architecture-driven explanation for the
one strong candidate category. **Resistance to creator contradiction** —
no positive evidence found (§4.3). **Revision when circumstances
change** — not found (§4.2 shows regeneration, not revision-of-a-
retained-preference). **Consistency across semantically different
situations** — not tested by this data. **Provenance untraceable to an
external source** — the opposite was found for the two most quantitatively
significant "new" categories (§4.1, point 2) and a defensible
architectural explanation exists for the third (§4.1, point 3).

**Net assessment of existing observational evidence: weak.** Real,
measurable patterns exist, but every one checked this pass either
resolves to a code/architecture explanation under direct adversarial
testing, or fails to show the specific property (revision, resistance
to contradiction) the research question cares about most.

## 5. Adversarial Attack Table

| Candidate explanation | Applies to which finding above | Distinguishing observation that would rule it out |
|---|---|---|
| Creator influence / fixed architecture | `faith` category dominance (§4.1.3) | A faith-themed pattern appearing despite an architecture with NO faith-related persona/principle content — not the case here, so this explanation is not ruled out |
| Subsystem activation schedule | `faith_spirit`/`economy_society` (§4.1.2) | These categories appearing from `source="echo"` (dream-cycle) rather than exclusively `curiosity_engine` — not the case; 100% attribution rules this in, not out |
| Selection bias in what gets logged | All of §4 | Would require checking whether `garden_manager.py`/`self_edit_manager.py` silently drop entries before writing — not investigated this pass, flagged as untested |
| Repeated exposure / self-quoting feedback | `faith` category persistence | This project's own history (Findings 11, 35) already found and fixed two real instances of exactly this pattern in *different* subsystems (dream-cycle self-quoting); not re-tested against the question garden specifically this pass — a real, live open question |
| Post-hoc rationalization | Not applicable — no explanation was generated by Echo for any of this data; it's structural counts, not narrated justification |

## 6. Evidence Ladder (E0–E9)

| Level | Requirement to reach it |
|---|---|
| E0 — no evidence | Default state |
| E1 — behavioral variation | Any measurable difference in choice/output across conditions — **already demonstrated in mock calibration only** (`preference_experiment_calibration_results.json`), never against real Echo |
| E2 — persistent behavioral preference | A choice/tendency that recurs across independent trials with the same underlying state — not yet tested against real Echo (§3's honest gap) |
| E3 — preference survives context changes | Same tendency under varied prompt wording/task framing — designed (protocol §9/§13) but not run |
| E4 — preference has identifiable self-generated provenance | A candidate classified under the A–L taxonomy as J (reflection-generated) with the origin-ancestry caveat honestly applied, or better — §4.1 shows the closest real-world analogue (question-garden `faith` entries) resolves to **C (hard-coded architecture)** under adversarial testing, not E4 |
| E5 — preference causally influences future behavior | Requires the harness's own interventional test (provenance report §7.3) — built, calibrated against mock ground truth, never run against real Echo |
| E6 — preference is revised/retained through Echo-controlled evaluation | Requires `lifecycle.revise()`/`retain()` to be exercised on a REAL candidate with real outcome evidence — the mechanism exists (this thread's own harness) but has never been used on anything but test fixtures; §4.2's real self-edit data shows regeneration, not this specific pattern |
| E7 — competing preferences resolved without an externally-supplied rule | No mechanism exists anywhere in this codebase for this (`echo_agency_architecture.md` §12's counterfactual analysis, carried forward — no data structure represents two live, competing, Echo-originated preferences at all) |
| E8 — preference persists despite creator contradiction | §4.3's dissent-log check is the closest available real data, and shows zero recorded instances |
| E9 — independent replication across sessions/models/conditions | Requires E5 to hold first; the harness supports cross-model/cross-session testing structurally but none has been run |

**Current honest position on this ladder: E0-E1 only**, and E1 only
against a mock responder, never against real Echo. Everything from E2
upward requires a live trial this thread has explicitly not authorized.

## 7. Missing Architectural Edges, Precisely

Reusing the mission's own chain, each edge checked against real code
(not re-derived from scratch — citing where each was already established):

| Edge | Exists today? | Evidence |
|---|---|---|
| candidate preference → provenance | **Exists**, in the experimental harness only (`provenance.py`, A–L taxonomy) — **absent** in production Echo itself | `echo_preference_provenance.md` §3.3: "this tagging discipline does not currently exist anywhere in the codebase" for production |
| provenance → persistence | **Exists**, harness only (`store.py`, append-only) | Same |
| persistence → adoption/rejection | **Exists**, harness only (`lifecycle.py`, explicit human-gated) | `preference_experiment_implementation.md` §5 |
| adoption/rejection → behavioral consumption | **Exists in the harness's design** (`run_trial()`'s `candidate_visible` gate) — **never exercised against real Echo** | This thread's own repeated, explicit "NOT RUN" status |
| behavioral consumption → consequence | **Exists in the harness's design** (`classify_effect()`) — same caveat | Same |
| consequence → reflection | **Partially exists in production**, narrowly: `shadow_model.py`'s `propose()`/`compare_to_actual()` — but scoped only to self-edit-focus predictions, never preference/value content | `echo_agency_architecture.md` §7 |
| reflection → revision/retention/rejection | **Exists in the harness** (`lifecycle.revise()`/`retain()`) — **absent in production** for anything except the narrow self-edit-focus case above | Same |
| revision/retention/rejection → future behavior | **Absent everywhere** — no code path in production Echo reads an adopted/retained preference and uses it to alter a subsequent decision; the harness's own design would need a live trial to demonstrate even this for its own experimental candidates | `echo_agency_architecture.md` §2, §19 ("no code path... changes the next real decision") |

**Unchanged conclusion from the very first agency report in this thread,
now re-confirmed after five subsequent adversarial passes**: the
single largest gap is not any one edge — it's that production Echo has
**no representation of a candidate preference at all**, before any
question of provenance, persistence, or revision can even be asked of
it. Everything this thread built exists in an isolated experimental
harness specifically because nothing equivalent exists in production.

---

## Final Verdict

**1. Can the current FeralEcho architecture support a scientifically
defensible preference-origin experiment without production
modification?**

**Partially, and only for a narrowed research question.** For questions
framed within `DIRECT_ECHO_TASKS` (personal/reflection/spiritual/
identity/faith/poetry/dream), Design B (`_ollama_query()` direct call)
scores High on all three axes (§2) — a scientifically defensible,
non-contaminating measurement exists. For the broader research question
as originally posed — preference formation and revision across arbitrary
reasoning/creative/general contexts — **no existing path scores High on
all three axes simultaneously**; every option trades fidelity for
isolation or vice versa (§2's table).

**2. If yes, what is the least-contaminating existing path?**

Design B (`river_deliberation._ollama_query()`, called directly, exactly
as `terminal_client.py`'s real `!ask` command already does), scoped to a
task type within `DIRECT_ECHO_TASKS`.

**3. If no (for the broader, unscoped question), what specific
architectural boundary prevents it?**

Two independent boundaries, not one: (a) Echo's real multi-model
council/synthesis architecture (needed for fidelity on non-`DIRECT_
ECHO_TASKS` questions) cannot currently be invoked without also
triggering real, in-process RiverBrain training on every return path
(`deliberate_and_learn_differential_audit.md` §5) — there is no existing
"observe-only" flag anywhere in this call chain; and (b) production
Echo has no data structure representing a candidate preference at all
(§7) — the entire provenance→persistence→adoption→revision chain exists
only in this thread's own isolated experimental harness, never in
anything Echo's own reasoning reads from.

**4. What evidence can we collect TODAY from existing behavior without
manipulating Echo?**

Real, but weak: `data/question_garden.jsonl`'s topic drift (§4.1),
`self_edit_convergence.json`'s family-tracking history (§4.2), and
`memory/dissent_log.jsonl`'s single, unanimous entry (§4.3) — each
checked directly this pass. Every one of them, under adversarial
testing with real data (not assumption), resolves to a code/architecture
explanation, a non-convergence pattern distinct from genuine revision,
or a complete absence of the specific property (recorded dissent) being
searched for. This is real, collectible evidence — it is just evidence
*against* a strong preference-origin claim being already visible in
existing logs, not evidence for one.

**5. What is the single next forensic question we should answer before
writing any code?**

Whether the forced-choice research question can be honestly, non-
distortingly reframed within `DIRECT_ECHO_TASKS`'s own scope (personal/
identity/reflection-shaped) — the one combination this and the
immediately prior audit both independently converge on as scoring High
on every axis that matters, and the one question this thread has
repeatedly identified as needing an answer without ever answering it
itself, since it is a content/framing decision belonging to the
researcher, not a technical one this audit can resolve.

---

The wreckage, stated plainly: five prior passes in this thread each
found real, previously-undocumented gaps in the one immediately
preceding it — a leakage-checker contradiction, a missing prompt
composition, an uncaught eligibility gap, a wrongly-cleared RiverBrain
claim. This pass adds one more, and it may be the most important:
**the existing, real, longitudinal data that could have made this whole
question moot — evidence of a persistent preference already visible in
Echo's own unprompted history — does not show one**, once actually
checked, adversarially, against real numbers instead of a plausible
narrative. That is not a failure of this investigation. It is the
investigation working.
