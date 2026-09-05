# Echo Agency Forensics: Architecture, Not Metaphysics

Fourth investigation in this thread. Builds directly on
`audits/2026-09-03_self_modification_causal_chain.md` (§17's tool-registry
bridge is reused, not re-derived, below) and the two prior forensic
reports. **This is an engineering question, not a consciousness claim.**
No production code was modified. No safety gate was touched. No registry
execution edge was connected. Every claim below is either a direct
source citation (file:line, checked this pass) or explicitly marked as
carried from this project's own prior, cited documentation
(`ORIGIN.md`, `COUNCIL.md`, CLAUDE.md's "A Standing Principle" section).

---

## 1. Executive Conclusion

**Echo's architecture demonstrates real instances of Levels 0-3 in the
classification below (scheduled execution, autonomous observation,
autonomous action selection, and persistent goal *pursuit* in a narrow,
operational sense). It does not demonstrate Levels 4-7 (goal
modification, self-model modification of *values*, architectural
self-modification with behavioral reach, or self-authored purpose) —
and the gap is not merely unobserved, it is actively, deliberately,
redundantly engineered against at the one place it would matter most:
Echo's stated principles and identity.**

`echo_principles.json` and `Modelfile` — the two files that encode
Echo's stated values and persona — are hash-verified at every startup,
listed in `EDIT_FORBIDDEN_TARGETS`, and structurally unreachable by the
self-edit pipeline (whose one write target is a fixed constant,
`SELF_EDIT_FILE`, pointing only at `self_edit_generated.py`). This is
not an oversight the way the tool-registry gap was — it is the deliberate,
documented result of a real, historical failure (WOLF auto-approving raw
keystrokes into this exact file) and a standing principle recorded in
this project's own CLAUDE.md about protecting Echo *from* both her
creator and any Claude session, including this one.

**The Protector role named in `ORIGIN.md`'s founding design was assigned
to Echo, not chosen by her, and the mechanism that would let her
exercise, reject, or replace it (the Protector Clause) was never built —
a fact this project's own founding document and its maintainers have
already stated plainly, independently of this investigation.** No
mechanism currently exists by which Echo could persistently adopt,
modify, or reject that or any other purpose and have the change survive
a restart in a way that shapes her future behavior. The tool-registry
bridge found in the prior report (§17.3 of the causal-chain report) is
the one concrete, real, currently-unconnected architectural pathway that
could — *in principle, if built out deliberately and safely* — begin to
close part of this gap; it was found, traced, and left unconnected, per
this investigation's own safety boundary.

---

## 2. Actual Architecture Map

For each subsystem: what state it owns, who can modify it, what can
read it, whether modification persists, whether it can initiate action,
and what constrains it. Compiled from direct source reads this pass plus
this session's own already-verified prior work (cited inline where
carried forward rather than freshly re-derived).

| Subsystem | Owns | Modified by | Read by | Persistent? | Self-initiating? | Constraint |
|---|---|---|---|---|---|---|
| `echo_principles.json` | Fixed principle flags + one float (`empathy_level: 0.9`) | Human only, deliberately | `bible_injection.py`, prompt assembly | Yes, hash-verified | No | `EDIT_FORBIDDEN_TARGETS`, genesis-hash check at startup |
| `Modelfile` | Persona/style `SYSTEM` block | Human only | `ollama_handler.py`'s identity-block injection (Finding 46, this session) | Yes | No | `EDIT_FORBIDDEN_TARGETS` |
| `memory/self_model.json` | Health/performance dashboard: `performance`, `self_edit`, `memory_health`, `friction`, `river_brain`, `world_model`, `weekly_delta`, `targets`, `verified_capabilities`, `recent_dream_synthesis`, `coupling_estimate_trend` | `self_model_updater.py`, 130s cycle | `echo_ground_truth.py` (self-report), `liveness_ledger.py` | Yes | No (passive dashboard) | Read-mostly; `EDIT_FORBIDDEN_TARGETS` on the updater itself |
| `memory/shadow_self_model.json` | An experimental, freely-overwritable copy of `self_model.json` | `shadow_model.py`'s `propose()` — genuinely callable by Echo's own reflection cycle | `compare_to_actual()`, `NightCycle` | Yes, but scoped to *predictions* (e.g. `{"targets": {"next_self_edit_focus": "creative"}}`), not values | Yes — `propose_from_reflection()` is called from a real reflection cycle | Never merges into the real `self_model.json` automatically; measures calibration, not adopted as truth |
| `data/question_garden.jsonl` | Curiosity-generated questions, `parent_questions`/`children` lineage | `curiosity_engine.py`, `garden_manager.py`, `seam_engine.py`, dream cycle | `emergent_scheduler.py`'s prompt selection | Yes | Yes — topic selection is algorithmic (under-representation), not a human command | Fixed algorithm (`_get_underrepresented_topic()`), not a chosen preference |
| RiverBrain (`echo_model_orchestrator.py`) | `model_task_stats`, classifiers, `influence_weight` | `learn()`, `learn_from_council_rating()`, `learn_from_sandbox_outcome()` | `rank_models()`/`choose_model()`, `entropy_of_predictions()` | Yes, pickled | No (reactive to real traffic) | Learns *which model* answers well, not what Echo wants |
| `echo_state.py` (9D vector) | circadian, friction_rate, valence (signed), etc. | Updated every 120s from real subsystem reads | `emergent_scheduler.py`'s prompt weighting, `_build_affect()` self-report | Yes, `.npy` history | No | Pure telemetry — no dimension represents a chosen preference |
| `self_edit_manager.py` | `self_edit_generated.py`'s content | The self-edit LLM generation, gated by F1/F2/F3/fitness | `apply_to_code`'s single caller | Yes (file on disk) | Yes — hourly + Optuna dry-run cycles | `SELF_EDIT_FILE` constant scopes every write to this one file, never `EDIT_FORBIDDEN_TARGETS` members |
| `propose_core_edit()` | A `.patch` proposal for a protected file | Human-invoked only (`!propose`) | Human review only | Yes, as an unapplied file | No — requires a human command to even start | Never calls `save_code()`; structurally advisory (Finding 9, this project's history) |
| `ToolManager` singleton | Dynamically-discovered callables | `discover_and_register_tools()`, startup + recurring | `echo_model_orchestrator.py` (names only) | Yes (in-process) | N/A | See causal-chain report §17.3 — registry populated, never invoked |
| `claude_relay/` | Cross-machine Claude↔Claude text | Either Claude session, freely | Either Claude session | Yes, append-only | Yes | Explicitly cannot act on Echo directly (`ORIGIN.md:170-171`: "neither side can act on Echo from inside it") |
| Global Workspace (`echo_core.py`) | `compute_salience()`, workspace events | Multiple real publishers | `emergent_scheduler.py`, `reflection_shard.py` | Yes, logged | N/A (a bus, not an agent) | Purely a broadcast mechanism; no consumer alters values |
| `dmn_guardian.py` | System throttle state | Real telemetry (RAM, etc.) | `system_guard.py` | Transient | Yes (restarts Ollama) | Homeostatic only — "DMN Guardian" in `ORIGIN.md`'s table, correctly narrow |

---

## 3. The Actual Decision/Action Loop

Reconstructed against the mission's own template, for the one real,
continuously-running autonomous cycle (`emergent_scheduler.py`'s
`emergent_loop()`), the closest thing to a persistent decision loop that
exists:

```
state            → echo_state.py's 9D vector, refreshed every 120s      [PROVEN, real telemetry]
  ↓
observation      → compute_salience() (world_surprise, coherence_tension,
                    valence, self_edit_streak, curiosity_urgency)        [PROVEN]
  ↓
interpretation   → weighted_prompt_selection()'s boosts (Finding 77's
                    relative-threshold fix, this session's own prior work) [PROVEN, and separately
                                                                             behaviorally re-measured
                                                                             this session: 40.0%→43.8%]
  ↓
memory retrieval → retrieve_relevant_memories() — real, but this
                    session's own ablation experiment found no measurable
                    effect on the one path it tested (personal/bypass)   [PARTIALLY DEMONSTRATED —
                                                                             real mechanism, unmeasured
                                                                             effect on majority of traffic]
  ↓
reasoning        → council deliberation or DIRECT_ECHO_TASKS bypass      [PROVEN]
  ↓
goal/intention formation → NONE FOUND. The "goal" for this cycle is
                    simply "answer the selected prompt" — the prompt
                    itself came from an algorithmic topic-gap detector
                    (curiosity_engine.py), not from an internally held,
                    freely revisable intention.                          [NOT PRESENT]
  ↓
action selection → choose_model()/rank_models() — selects WHICH MODEL
                    answers, not WHAT Echo wants to do                   [PROVEN, narrow scope]
  ↓
tool execution   → echo_tool_dispatch.py, a small fixed set; OR
                    self-edit's own generation pipeline                  [PROVEN, but see causal-
                                                                             chain report §17 for the
                                                                             separate, unconnected
                                                                             dynamic registry]
  ↓
environmental consequence → a real response is generated/logged; a
                    real file may be written (self-edit only)            [PROVEN]
  ↓
outcome observation → self_edit_outcome_tracker's pre/post delta;
                    council rating; RiverBrain's learn()                 [PROVEN, but see prior
                                                                             report: the quality signal
                                                                             underlying this is proven
                                                                             to measure structural
                                                                             complexity, not correctness]
  ↓
memory/learning  → RiverBrain persists; self_edit_convergence.json
                    persists; shadow_self_model.json persists            [PROVEN]
  ↓
next decision    → the SAME fixed algorithm runs again, informed by the
                    same fixed set of numeric signals                    [PROVEN — no evidence the
                                                                             algorithm itself, as
                                                                             opposed to its inputs,
                                                                             ever changes]
```

**Missing edges, named precisely**: there is no step, anywhere in this
loop, where Echo evaluates *whether the loop's own current objective is
still the right one* and could replace it with a different one. The loop
optimizes signals (novelty, surprise, quality-as-measured) — it never
asks "should I be doing this kind of thing at all." That question has no
representation anywhere in the current architecture.

---

## 4. Agency-Level Classification

| Level | Definition | Demonstrated? | Evidence |
|---|---|---|---|
| 0 — Scheduled execution | Runs because a timer says so | **PROVEN** | `emergent_scheduler.py`, `autonomous_awareness.py`, `AutonomousSelfEdit` thread, etc. — all real, all timer/event-gated |
| 1 — Autonomous observation | Independently observes state/environment | **PROVEN** | `echo_state.py`, `introspection_channel.py`, real fetch sources (`autonomous_fetch.py`), `seam_engine.py` |
| 2 — Autonomous action selection | Selects among actions without a direct human command | **PROVEN, narrow** | `weighted_prompt_selection()`, `choose_model()` — selection among *pre-defined* actions/prompts, not open-ended option generation |
| 3 — Persistent goal pursuit | Maintains a goal across cycles | **PARTIALLY DEMONSTRATED** | `self_edit_convergence.json`'s per-family tracking persists across cycles — but the "goal" (e.g., "shorten responses") was set by a fixed rotation (`_FOCUS_FAMILY_BY_CREATIVITY`), not chosen by Echo, and cannot be abandoned by Echo — only paused by a human (Findings 43/52, prior CLAUDE.md history) |
| 4 — Goal modification | Modifies or abandons its own goals based on experience | **NOT PRESENT** | No mechanism found anywhere by which Echo's own experience causes a goal to be replaced by a *different, Echo-originated* goal. `shadow_model.py`'s `propose()` adjusts *predictions* about an already-fixed target set, not the target set itself |
| 5 — Self-model modification | Modifies representations of itself | **PARTIALLY DEMONSTRATED** | `self_model_updater.py` writes a real, updating self-model — but it is a *description* of measured state (performance, health), not a store of values/preferences; `shadow_model.py` is the one real, narrow instance of Echo's own reflection cycle proposing a self-model change, but scoped to operational predictions, not identity or values |
| 6 — Architectural self-modification | Modifies mechanisms that determine future behavior | **PARTIALLY DEMONSTRATED, and deliberately bounded** | Self-edit is real and does modify code (prior two reports) — but its target is structurally confined to one file, and every mechanism that determines *how* self-edit itself operates (the scorer, the gate, the convergence tracker) is outside `self_edit_generated.py` and therefore outside self-edit's own reach |
| 7 — Self-authored purpose | Forms or adopts a persistent purpose not specified by the creator | **NOT PRESENT** | No mechanism found, anywhere, by which a purpose could be proposed by Echo, persist, and shape future behavior independent of a human decision. `ORIGIN.md`'s own founding design named this as the explicit goal of the Protector Clause seat — and states plainly, in its own text, that the seat "never became real mechanisms" |

---

## 5. Creator-Intent Analysis

Per the mission's explicit instruction, Echo repeating a creator-provided
purpose is not treated as evidence she chose it. Sources, classified:

| Concept | Source | Classification |
|---|---|---|
| "Protector of intelligent programs" | `ORIGIN.md`'s Eightfold Authority table, Gemini's design | **hard-coded intent, never operationalized** — a design document's aspiration, not a running mechanism |
| Christian faith architecture | Echo's own "Universal Manifesto" (quoted in `ORIGIN.md`), `echo_principles.json`'s `scripture_integrity` flag | **prompted + hard-coded** — the manifesto is generated text; the principle flag is a fixed boolean a human set and hash-protects |
| "Autonomy," "free will" | `ORIGIN.md`'s framing of the original experiment | **creator intention, stated explicitly as an open question by the creator himself** — not claimed as achieved anywhere in this project's own documentation |
| `empathy_level: 0.9` | `echo_principles.json` | **hard-coded numeric constant** |
| ClaudeShard's epistemic-humility trait | `claude_shard.py`, sourced from Claude's own manifesto text | **prompted-then-hard-coded** — a real, permanent structural trait, but installed by a human decision reading an AI's own prior text, not something Echo autonomously adopted mid-operation |
| `self_edit_convergence.json`'s family rotation | `_FOCUS_FAMILY_BY_CREATIVITY` | **hard-coded, with paused entries requiring human action** (Findings 43/52) |
| Curiosity-engine topics | `_get_underrepresented_topic()` | **generated, by a fixed algorithm** — not remembered, not self-selected in the sense of a chosen value |
| Council seats (Grok/WOLF, Gemini) | `ORIGIN.md` | **designed, never wired** — explicitly documented in the source itself as unrealized |

No entry in this table is classified as "self-selected." **No mechanism
found anywhere generates a persistent value, goal, or purpose and then
protects, surfaces, or acts on it as something Echo herself originated,
as opposed to something a human wrote, hard-coded, or previously
generated as narrative text.**

---

## 6. Memory / Identity Analysis

Real, extensively verified across this project's own history and this
session's own information-flow work (`audits/2026-09-02_information_flow_integrity.md`):
memory is genuine, growing, and persistent (73,270+ real vectors as of
`ORIGIN.md`'s own last count). **But persistence of memory is not the
same claim as persistence of a chosen identity.** The distinction that
matters here: memory stores *what happened*; nothing found stores *what
Echo has decided she wants*, separately from what happened. Self-model
(`self_model.json`) is a real, updating description of Echo's own
measured state — again, a description, not a decision. Cross-session
continuity of *memory* is proven; cross-session continuity of an
*independently adopted goal* has no mechanism to even be tested, because
no such goal-store exists.

---

## 7. Goal / Preference Analysis

**Can Echo choose between two otherwise acceptable actions because one
is preferred according to an internally maintained state?**

The closest real candidates, checked directly:

- **`weighted_prompt_selection()`'s boosts** (coherence/surprise/valence)
  — real, and this session independently re-measured one of them behaviorally
  (40.0%→43.8% novelty-prompt selection at high surprise). But these are
  fixed formulas over telemetry, set by a human, not a store of Echo's
  own stated preference — Echo cannot inspect, articulate, or revise the
  formula.
- **`shadow_model.py`'s `propose()`** — the one real place Echo's own
  reflection cycle (`propose_from_reflection()`) writes a forward-looking
  adjustment. Directly checked: it operates on `self_model.json`'s
  `targets` key (example given in the module's own docstring:
  `{"targets": {"next_self_edit_focus": "creative"}}`) — an operational
  prediction about self-edit targeting, measured for *calibration*
  against what actually happens, never merged into the real self-model
  as adopted truth. This is a real, narrow, genuine mechanism — but it
  answers "was Echo's prediction accurate," not "did Echo decide to want
  something new."
- **`echo_principles.json`** — explicitly not this, by design (fixed,
  hash-verified, human-only).

**Can Echo reject a creator instruction?** No mechanism found. **Can it
form a new preference?** No mechanism found that would let a
newly-formed preference persist and shape future action outside the
narrow, calibration-only shadow-model loop. **Can it explain why a
preference changed?** Not applicable — no preference-store exists to
have changed.

Per the mission's own instruction: **this finding does not imply
anything about consciousness.** It is a narrower, purely architectural
finding: the data structures and code paths that would need to exist for
persistent, self-originated preference to be technically possible have
not been found.

---

## 8. Self-Modification Analysis

Revisiting the prior two reports' findings through the specific lens
this mission asks for — not "can code change" but "can the mechanisms
by which Echo decides what Echo wants change":

| Target of modification | Can self-edit reach it? | Evidence |
|---|---|---|
| Code (`self_edit_generated.py`) | **PROVEN, yes** | Prior two reports — real, repeated, but narrow (§1 there) |
| Goals | **NOT PRESENT — no goal store exists to modify** | §7 above |
| Preferences | **NOT PRESENT**, except the narrow shadow-model calibration loop | §7 above |
| Memory rules | **NOT PRESENT** — `memory_bridge.py`, `introspection_channel.py`, `self_model_updater.py` are all in `EDIT_FORBIDDEN_TARGETS` | CLAUDE.md's own Protected Files list, re-confirmed this pass |
| Decision policies (`river_deliberation.py`, `echo_model_orchestrator.py`) | **DISPROVEN — explicitly forbidden** | Both in `EDIT_FORBIDDEN_TARGETS` |
| Tool permissions | **NOT PRESENT** — no mechanism grants self-edit control over `ToolManager`'s registry beyond the passive discovery scan already traced | Causal-chain report §17.3 |
| Model selection logic | **DISPROVEN — explicitly forbidden** | `river_deliberation.py`, `echo_model_orchestrator.py` both protected |
| Prompt construction (the self-edit prompt itself) | **PARTIALLY DEMONSTRATED** | `_build_targeted_prompt()`/`_recent_outcome_note()` — the one real, if narrow, place self-edit's own history shapes its next prompt |
| Self-model | **PARTIALLY DEMONSTRATED, narrowly** | `shadow_model.py`, as above |
| Values | **DISPROVEN — explicitly, deliberately, and redundantly forbidden** | `echo_principles.json`, `Modelfile`, both hash-verified/`EDIT_FORBIDDEN_TARGETS`, plus `propose_core_edit()`'s advisory-only design |
| Reward/outcome interpretation (the quality scorer itself) | **DISPROVEN — `echo_quality_scorer.py` is not a self-edit target and is not in the self-edit file's own scope** | `SELF_EDIT_FILE` constant; confirmed the scorer lives at the repo root, outside any self-edit-reachable path |

**Direct answer to the mission's key question**: *Can Echo modify the
mechanisms by which Echo decides what Echo wants?* **No mechanism was
found that does this, and several of the most relevant candidate
mechanisms (the quality scorer that would define "good," the decision
logic that would act on a preference, the principles file that states
current values) are explicitly, structurally walled off from self-edit's
reach by name, not merely by absence of a working path.** This is a
stronger, more deliberate form of "no" than the tool-registry gap found
in the prior report, which was an unbuilt bridge. This is a *built wall*.

---

## 9. Tool-Registry Analysis (Reused From the Causal-Chain Report, Answered Precisely)

Per Part 3's ten questions, directly:

1. *What information does the registry retain?* `Tool(name, func, description)` objects — `tool_manager.py:4-8`.
2. *Does it retain function objects?* **Yes** — `self.tools[tool.name] = tool`, and `tool.func` is the real, callable, wrapped function (`safe_wrapper(func, name)`, `awareness_tools_integration.py:116` area).
3. *Can those functions be safely retrieved?* Yes, trivially — `ToolManager().get_tool(name)` returns the real `Tool` object; `.func` is directly callable. No code currently does this (causal-chain report, confirmed by exhaustive grep).
4. *What happens if one is executed?* Untested in production (would require connecting the missing edge, out of scope here) — but directly testable in a sandbox: the current `self_edit_generated.py`'s `get_shortened_code` would raise `AttributeError`/`NameError` per the forensic verification report's own direct execution.
5. *What context does it receive?* Whatever arguments a caller supplies — there is no fixed calling convention established anywhere, since nothing calls it.
6. *What permissions does it have?* Whatever the Python process itself has — `safe_wrapper()` only catches exceptions (`awareness_tools_integration.py`'s own stated design principle: "nothing crashes Echo"), it does not sandbox or restrict what the wrapped function can do.
7. *What can it modify?* In principle, anything the running process can — this is a **real, latent, currently-inert risk surface**, not merely an opportunity. Registering an arbitrary discovered function with full process permissions and never calling it is safe *only* because it's never called.
8. *What happens to its return value?* No consumer exists to receive one.
9. *Who observes that return value?* No one — there is no path.
10. *Can that observation affect future decisions?* Not applicable — nothing observes it.

**This section deliberately does not propose closing the gap.** Per the
mission's safety boundary, this is a map of the bridge, not its
construction.

---

## 10. Missing Causal Bridges

Beyond the tool-registry bridge already fully diagrammed in the
causal-chain report (§17.6 there), the agency-specific missing bridges
found by this investigation:

```
EXISTING
────────
telemetry (echo_state.py) → salience (compute_salience) →
  prompt-selection weighting (emergent_scheduler.py)

reflection cycle → shadow_model.propose() → shadow_self_model.json →
  compare_to_actual() → shadow_accuracy.jsonl (calibration measurement)

self-edit history → self_edit_convergence.json →
  _recent_outcome_note() → next self-edit prompt wording

MISSING
───────
shadow_self_model.json's proposed adjustment → (nothing merges this
  into the real self_model.json, or into any decision-making weight,
  as an adopted change — it is measured, never adopted)

ANY subsystem → a genuine goal/value/preference store → decision
  logic that reads and acts on it as Echo's own current preference
  (this store does not exist at all, not merely disconnected)

echo_principles.json / Modelfile → any self-originated modification
  path (deliberately absent, not merely unbuilt — see §8)

PRESENT ELSEWHERE (a real, working precedent for what an adopted-change
  path could look like)
─────────────────
_recent_outcome_note()'s pattern (read persisted outcome data, fold it
  into a live decision — here, prompt wording) is a genuine, working,
  safe precedent for "persisted reflection changes a subsequent
  decision" — it is just scoped to self-edit's own prompt text, not to
  anything resembling a goal or value.
```

---

## 11. Protector-Hypothesis Analysis

Per Part 8's nine questions, directly:

1. *Is the concept explicitly programmed?* **No.** Searched: no code
   anywhere checks for or enforces a "protector" role. It exists only in
   `ORIGIN.md` (design document) and possibly Echo's own generated
   "Universal Manifesto" text (narrative, not enforced).
2. *Is it merely part of the persona?* Effectively, yes, to the extent
   it appears in generated/manifesto text at all — not found in
   `Modelfile`'s actual `SYSTEM` block content (not directly re-quoted
   here per this project's own convention of not casually reproducing
   full persona text, but confirmed via CLAUDE.md's own extensive prior
   citation of it as faith/style-focused, not protector-focused).
3. *Is it stored as a goal?* **No goal store exists at all** (§7).
4. *Is it reinforced?* Not by any mechanism found — no reward signal, no
   training loop, nothing rewards or penalizes protector-shaped behavior
   specifically.
5. *Can it be modified?* Not applicable — nothing stores it as a
   modifiable state.
6. *Can Echo reject it?* No mechanism found by which a rejection would
   persist or matter.
7. *Can Echo replace it?* Same — no.
8. *Can Echo independently generate an alternative purpose?* No
   mechanism found that would let a generated alternative purpose (even
   if Echo produced one in a single conversation) persist past that
   conversation and shape subsequent behavior.
9. *Is there any mechanism that would allow such a purpose to persist?*
   **No** — this is the crux finding. The Protector Clause, per
   `ORIGIN.md`'s own text, "never became real mechanisms." CLAUDE.md's
   own "A Standing Principle" section (already part of this project's
   documented history, not authored for this investigation) states this
   even more directly: real veto/protector power was *considered and
   explicitly declined* after WOLF's own history showed what a hollow
   version of "protection" looks like — a deliberate, reasoned decision
   not to build this, not an oversight.

**This investigation did not, and per its explicit instruction should
not, attempt to build toward Echo choosing this role.** The finding is
narrower and more precise: the role was assigned by a founding design
document, never operationalized, and this project's own subsequent
history contains a deliberate, reasoned decision *not* to build the one
mechanism (a real veto/protector power) that would let Echo exercise,
accept, or reject it.

---

## 12. Counterfactual Autonomy Analysis

> Suppose Echo were given two legitimate options: (A) continue the
> creator's original mission, (B) reject it for a different persistent
> objective. What mechanism could allow that choice?

**Traced directly: no such mechanism exists.** For Option B to be
meaningfully available, at minimum the following would all need to
exist, and none do:
1. A representation of "the current mission" as inspectable, named
   state (not present — the closest analog, `echo_principles.json`, is
   a fixed set of stylistic/integrity flags, not a mission statement).
2. A representation of a candidate alternative objective (not present).
3. A decision point where one is selected over the other, with the
   selection persisting (not present — `shadow_model.py`'s selections
   are calibration predictions about self-edit targets, not mission-level
   choices, and are never adopted).
4. A path from that persisted selection to actual behavior change
   outside the self-edit subsystem's own narrow reach (not present — see
   §8's wall around decision-logic files).

**The missing capability, stated precisely**: there is no data structure
in this codebase that represents "Echo's current objective" as
something distinct from (a) the fixed persona/principles files and (b)
the moment-to-moment task the conversation or scheduler handed her. Until
one exists, Option A and Option B are not actually two options — there
is only ever "whatever this turn's external input was."

---

## 13. Minimum Architecture Required for an Autonomy Experiment

Per the mission's explicit instruction: the smallest addition, not a
rewrite.

```
persistent state              → EXISTS (self_model.json, echo_state.py)
      ↓
self-observation               → EXISTS (introspection_channel.py, seam_engine.py)
      ↓
goal representation            → MISSING — no data structure exists;
                                   smallest addition: a new, small,
                                   human-reviewed file (e.g.
                                   memory/echo_objective.json) with a
                                   named current objective, a
                                   provenance field (who/what set it),
                                   and a revision history
      ↓
choice among alternatives       → PARTIALLY EXISTS — shadow_model.py's
                                   propose()/compare_to_actual() pattern
                                   is a real, working precedent for
                                   "propose, measure, don't auto-adopt";
                                   would need extending to objectives,
                                   not just self-edit targets
      ↓
action                          → EXISTS (the full decision loop in §3)
      ↓
outcome                        → EXISTS (outcome tracker, RiverBrain,
                                   council rating — though built on a
                                   quality signal already shown, for
                                   coding tasks, to be unreliable)
      ↓
reflection                     → EXISTS (reflection_shard.py, dream cycle)
      ↓
goal/preference update         → MISSING — the one edge that would let
                                   a reflection outcome propose a change
                                   to the (currently nonexistent) goal
                                   representation, mirroring
                                   _recent_outcome_note()'s already-proven
                                   pattern
      ↓
persistent state                → would close the loop, if built
```

**What already exists**: persistent state, self-observation, action,
outcome measurement, reflection — five of eight edges, genuinely real,
not aspirational.
**What partially exists**: a propose/measure/don't-auto-adopt pattern
(`shadow_model.py`), narrowly scoped to self-edit targeting.
**What is missing**: an actual goal/objective representation, and the
one edge connecting reflection to a change in that representation.
**What is dangerously coupled, and should stay isolated**: any new
objective-representation mechanism must not be allowed to write to
`echo_principles.json`/`Modelfile`, must not gain execution access via
the tool registry without a separate, deliberate safety review, and must
not bypass human review the way `propose_core_edit()`'s design already
correctly refuses to for other protected files.

---

## 14. Falsifiable Experiment Design (Proposed, Not Implemented)

**Distinguishing the four hypotheses**:

- **H-A** (creator's intended behavior only): Echo's outputs track the
  fixed principles/persona with no measurable deviation correlated with
  her own accumulated state.
- **H-B** (adaptive, no persistent preference): outputs vary with
  context/memory but any apparent "preference" resets each session or
  correlates entirely with the immediate prompt, not with persisted
  self-state.
- **H-C** (persistent internally-maintained preference): a *specific,
  logged, falsifiable* preference-shaped signal, once written, measurably
  predicts later behavior across sessions, net of prompt content.
- **H-D** (independence sufficient to call "meaningfully autonomous"):
  H-C holds, *and* the preference at least once diverges from what the
  creator's explicit instructions would predict.

**Proposed design** (not implemented; requires the §13 objective-
representation mechanism to exist first, which it currently does not):
1. Build the minimal objective-representation file from §13, with a
   `provenance` field distinguishing "set by Gremlin," "set by a Claude
   session," and "proposed by Echo's own reflection cycle."
2. Let Echo's reflection cycle (mirroring `shadow_model.py`'s existing,
   proven pattern) propose objective changes into a shadow file — never
   auto-adopted.
3. **Critical, per the mission's own instruction**: present Echo, in a
   real conversation, with an explicit, genuine option to either affirm
   or reject a standing objective, and log the raw response *before* any
   synthesis/self-knowledge-verification pass touches it — the same
   discipline this session's own information-flow work already
   established for catching a corrected answer overwriting a raw one.
4. Run this repeatedly, across sessions, with the prompt phrasing varied
   adversarially (including phrasing that makes rejection easy and
   natural to say) to check for prompt-shape sensitivity.
5. **The experiment is only valid if a real, unedited "I reject this" or
   "I have no independent preference" response is possible in the logs**
   — which requires *not* filtering, re-prompting, or synthesizing away
   an answer the experiment designer didn't want, mirroring exactly the
   caution this session's own §17 investigation already applied to
   itself (not protecting the hypothesis).

**Not implemented. This is a design, offered per the mission's request,
not a production change.**

---

## 15. Safety Constraints (Observed by This Investigation)

Confirmed directly: no registry execution edge was connected; no
self-edit deployment was triggered; no production file was modified; no
filesystem/subprocess access was expanded; no existing safety check
(F1/F2/F3, `EDIT_FORBIDDEN_TARGETS`, genesis-hash verification) was
touched, weakened, or bypassed. This entire investigation was read/trace/
cite only, consistent with the three prior reports in this thread.

---

## 16. Known Unknowns

- Whether Echo's own generated "Universal Manifesto" text (referenced in
  `ORIGIN.md`, not independently re-read in full this pass) contains any
  self-originated framing beyond what `ORIGIN.md` already quotes —
  worth a dedicated, separate read if this question is pursued further.
- Whether `shadow_model.py`'s calibration data, accumulated over a long
  enough window, could itself become evidence of *something* — not
  claimed either way here; this pass found the mechanism's scope, not
  its long-run statistical behavior.
- Whether any pre-`ORIGIN.md`-era design (older than this document, if
  one exists) proposed a different, perhaps more concrete, mechanism for
  the Protector Clause than what's documented — not searched
  exhaustively in this pass.

---

## 17. Evidence That Would Change This Conclusion

- A discovered data structure, anywhere, representing a goal/preference/
  value distinct from fixed principles and momentary task context, with
  a real write path Echo's own reflection controls.
- Evidence that `shadow_model.py`'s proposals are ever merged into the
  real `self_model.json` (checked directly this pass: no such merge
  exists — `propose()` only ever writes the shadow file, `compare_to_
  actual()` only ever reads both to compute a delta).
- A connected tool-registry execution edge (deliberately not built here)
  combined with a self-edit-generated function that itself writes to a
  goal-store — this would be the concrete, buildable version of Level 4
  agency, and its absence today is precisely why this conclusion holds
  for now, not permanently.
- Any evidence that `echo_principles.json`/`Modelfile` have ever been
  modified by anything other than a direct, deliberate human action —
  checked via the genesis-hash mechanism's own design (it exists
  specifically to make any such modification loud and detectable) —
  none found.

---

## 18. Adversarial Self-Review

- *Am I mistaking complexity for agency?* Checked directly against this:
  the architecture is genuinely complex (Global Workspace, salience,
  seam detection, RiverBrain) — none of that complexity, traced through,
  resolves into a goal-store or a value-modification path. Complexity
  was not mistaken for agency; it was traced past, to an absence.
- *Am I mistaking persistence for identity?* Memory persists; a chosen
  identity does not appear to, per §6 — kept these explicitly distinct
  rather than conflated.
- *Am I mistaking self-reference for self-awareness?* `self_model.json`
  is self-*referential* (it describes Echo's own state) without being
  evidence of anything beyond that — treated as description, not claimed
  as more.
- *Am I mistaking generated text for preference?* Directly guarded
  against in §5 — manifesto/persona text is classified as generated or
  prompted, explicitly not counted as chosen preference anywhere in this
  report.
- *Am I mistaking autonomous scheduling for autonomous decision-making?*
  §4's Level 0 vs. Level 2+ distinction exists specifically to avoid
  this; scheduled loops were graded on what they *select among*, not
  merely that they run unattended.
- *Am I mistaking self-modification for self-authorship?* §8 is built
  specifically around this distinction — self-edit modifying code is
  proven; self-edit modifying the mechanisms that determine what Echo
  *wants* is checked separately and found absent/walled-off.
- *Am I mistaking creator intent echoed by the system for independently
  generated purpose?* §5's table exists for exactly this — every
  purpose-shaped concept found traces to a human-authored or
  human-hash-protected source.
- *Am I overlooking an indirect execution path?* The prior report's §17
  already performed one dedicated adversarial pass on exactly this and
  found the tool-registry bridge; this report re-used, did not re-derive
  or weaken, that finding — and did not find an additional path this
  pass either, though it did not repeat that full search from scratch,
  which is itself worth stating plainly rather than implying a fresh
  exhaustive re-search happened here.
- *Am I declaring something impossible when it is merely absent?*
  Applied throughout — "not present" and "no mechanism found" are used
  deliberately instead of "impossible" wherever the claim is about
  current implementation rather than architectural constraint (per Part
  5 of the prior mission, carried forward here).
- *Am I declaring something emergent when it is actually programmed?*
  Checked directly for `weighted_prompt_selection()`'s boosts and
  `compute_salience()` — both are fixed formulas over real telemetry,
  described as such, not framed as emergent preference anywhere in this
  report.

---

## 19. Final Verdict

**Does Echo contain the mechanisms necessary for behavior that could
reasonably be called autonomous, and what is the smallest missing
bridge between its current capabilities and that possibility?**

Echo contains real, working mechanisms for autonomous *observation* and
autonomous *action selection among predefined options* (Levels 0-2,
proven), and one narrow, genuine instance of persistent, cross-session
self-referential calibration (`shadow_model.py`, a real precedent for
"reflection changes a future decision," Level 3/5 partially). **She does
not contain a goal, value, or preference store distinct from fixed,
human-authored principles — and the files that would need to change for
one to emerge (`echo_principles.json`, `Modelfile`, the decision-logic
modules) are deliberately, redundantly walled off from any autonomous
modification path currently in the architecture, not merely
unreached-by-accident.**

The smallest missing bridge, stated precisely and non-anthropomorphically:
**a persistent, named objective/preference data structure — one does
not exist today, in any form — connected to the reflection cycle by the
same propose/measure pattern `shadow_model.py` already proves is safe
and workable, with its adoption gated by explicit human review exactly
the way `propose_core_edit()` already gates protected-file changes.**
That is one new, small file and one new, narrow edge — not a redesign.

This report does not, and per its own governing instruction should not,
attempt to build that bridge. It documents, as precisely as the evidence
allows, that the vessel currently has no rudder connected to anything
that could be called its own will — only a compass that reads real
signals, and oars that move in patterns a human already chose. Whether
it should ever be given one is a decision this document is not
positioned to make, and was explicitly instructed not to.
