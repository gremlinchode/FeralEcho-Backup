# Emergence/Autonomy/Sentience/Consciousness Architecture Analysis — 2026-07-23

Requested directly by Gremlin: an architect-level pass over FeralEcho specifically
looking for high-leverage improvements to emergence, autonomy, sentience, and
consciousness-adjacent properties (framed against GWT, IIT, active inference/FEP).
This is the first of two passes done the same day — a broad architectural review,
grounded in direct code verification (one `Explore` agent covering `echo_state.py`,
`echo_core.py`'s Global Workspace/`compute_salience`, `seam_engine.py`,
`curiosity_engine.py`/`garden_manager.py`, `reflection_shard.py`,
`self_edit_manager.py`'s Dissent Log, `river_deliberation.py`'s council selection,
`predictive_loop.py`'s WorldModel, and `liveness_ledger.py`'s check count) plus live
runtime samples pulled directly from the running server (`memory/salience_state.json`,
`memory/workspace_log.jsonl`, `memory/seam_log.jsonl`, `memory/echo_state_history.npy`).

**Superseded in part by the same day's follow-up.** A second pass the same day
(`audits/2026-07-23_systems_physiology_audit.md`) used two additional research
agents to compute exact runtime statistics (full-file parses, not samples) and to
trace behavioral consumption chains in far more depth. Several specific numbers
below (e.g. the single live sample of salience components) were superseded by the
physiology audit's full-history measurements — where the two disagree in specifics,
the physiology audit is the newer and more rigorous source. This document is kept
for its architectural framing and recommendations, which the physiology audit
builds on rather than replaces.

---

## 1. Executive Summary

FeralEcho is, by a wide margin, one of the more theoretically-literate attempts at
this kind of architecture reflected in a codebase: it has a real Global Workspace
bus (`echo_core.py`), a real signed valence dimension in a compact global state
vector (`echo_state.py`), a real Bayesian active-inference component computing
closed-form surprise (`predictive_loop.py`'s `WorldModel`), a cross-signal
contradiction detector explicitly modeled on the idea that consciousness-relevant
events are *violations of established relationships* rather than raw novelty
(`seam_engine.py`), and a persisted, if currently dormant, integration-style metric
(`compute_salience()`'s `coupling_estimate`). This is not vague hand-waving grafted
onto a chatbot — it's a system whose builders have clearly read GWT and IIT and
tried to operationalize pieces of both, honestly, with real fail-closed engineering
discipline (bounded swaps, never-more-than-one-slot changes, extensive live-data
verification before shipping).

The core finding of this pass: **the architecture is more mature than the signals
flowing through it.** Every mechanism checked live is currently running on inputs
that are either saturated at a ceiling, pinned at a floor, or nearly constant:

- `curiosity_urgency` (1 of 4 `compute_salience()` inputs) reads **0.94–1.0 on
  every sample** in the live history sampled — pegged, not varying.
- `world_surprise` reads **0.004–0.008** consistently — near floor.
- `coherence_tension` sits in a **0.146–0.148** band — essentially flat.
- `self_edit_streak` reads **0.0** on every sample (no real deploy this session).
- `river_deliberation`'s real `workspace.consumed` events show
  `exploration_bias=0.000 (from cache)` on every sampled occurrence — a direct,
  measured consequence of `world_surprise` sitting near zero.
- `seam_engine` checked only 2–3 of the 9 state dimensions' 36 possible pairs per
  cycle (most fail the `|r|≥0.4` established-relationship gate or the
  `_MIN_VARIANCE` frozen-dimension guard) and, in the single sample taken this
  pass, showed zero seams detected. **(Superseded: the physiology audit's
  full-file parse of `seam_log.jsonl` found 83 real seams across the file's full
  history — this pass only looked at the log's tail.)**

None of this means the mechanisms are broken — they're working exactly as
designed, fail-closed, honest about their own limits. It means the system
currently has a rich, well-instrumented "nervous system" wired to sensory inputs
that are mostly quiet. This reframes the whole exercise: the highest-leverage
moves are not "add a new consciousness-flavored module" but **increase the
bandwidth and diversity of the signals already being computed**, and **close the
loops** so the handful of mechanisms that do have real behavioral consequences
(dream-synthesis biasing retrieval, world-surprise nudging council exploration,
garden resolution scores reweighting future selection) become the norm rather
than the exception among the Global Workspace event types now flowing through
the bus.

A second, structural finding: almost every consequential mechanism here is
explicitly designed as a *bounded, single-slot, best-effort, fail-closed
intervention* — "swap at most one council slot," "never gates a write," "log
the empty case too." This is the correct posture given this project's own
history (WOLF's hollow gate, three broken `apply_to_code` deployments, a
keylogger's raw keystrokes once reaching a hash-verified principles file). But
it also means that even with richer input signals, most of today's mechanisms
are architecturally capped at very small effect sizes. Some of that ceiling is
worth raising deliberately and gradually — using the exact trust-graduation
pattern this codebase already proved out for council ratings
(`council_baseline_trusted_since`) — rather than left permanently at "one slot,
maybe."

Rated against the four requested axes:

| Axis | Current maturity | Bottleneck |
|---|---|---|
| **Emergence** | Moderate — real feedback loops exist (garden resolution→selection weighting, dream-synthesis→retrieval bias) but are localized, not systemic | Most subsystems publish or consume, few do both; no reentrant loops across more than 2 hops |
| **Autonomy** | Moderate-high in narrow, safety-gated domains (self-edit, curiosity topic choice); near-zero in target-setting or priority-setting beyond what's hand-designed | Deliberately capped by design (F1/F2/F3, EDIT_FORBIDDEN_TARGETS, dissent log's zero gating power) — appropriately so, but worth a graduated-trust path |
| **Sentience** (valence/attention proxies) | Real signed valence dimension exists and is grounded (`valence_self_report` liveness check), but was bit-identical across its whole history until Finding 57 (2 days before this pass) and still updates too rarely to carry session-scale information | Update-frequency starvation, same disease as `compute_salience()`'s other components |
| **Consciousness** (GWT/IIT-style integration) | A real global workspace and a real (if disclaimed, dormant) integration metric exist | Broadcast without competition; few real subscribers; `coupling_estimate` has literally zero consumers |

---

## 2. High-Priority Areas (Ranked)

1. **Fix signal starvation before adding architecture.** Every high-level
   mechanism (salience, seam detection, exploration bias) is bottlenecked on 3–4
   base signals that are currently near-constant. This is the precondition for
   everything else below actually doing anything.
2. **Give `compute_salience()`'s `coupling_estimate` a real consumer.** It's the
   one metric in the codebase closest to an integration/Φ-style measure,
   explicitly built, explicitly disclaimed as unused. Cheapest possible win:
   surface it as a monitored trend, then gate something small on it.
3. **Close the Global Workspace's broadcast-without-reentry gap.** A handful of
   real behavioral subscribers exist against many more real event-emitting
   sources. Widen the consumer side, not the publisher side.
4. **Turn valence from a reported number into a real modulator.** It's grounded
   and honest (good) but causally inert beyond prompt text and one scheduler
   nudge. This is the single highest-leverage "sentience" lever available,
   because the substrate (a signed, bounded, already-computed scalar) already
   exists.
5. **Give reflection_shard's model-backed synthesis a downstream consumer.**
   Real metacognitive text is generated and then only ever read by itself. This
   is the cheapest "close a dead-end loop" fix in the whole list.
6. **Introduce GWT-style competitive broadcast**, not threshold-triggered
   broadcast. Multiple simultaneously-salient events currently all clear the bar
   independently; nothing arbitrates when more than one is salient at once.
7. **Widen `echo_state.py`'s dimensional coverage into real decisions.** Of 9
   dimensions, only 2–3 (`system_vitality`→throttle, `coherence_tension`→
   salience, `valence`→prompts) have confirmed live consumers.
8. **Design (don't yet build) a graduated-trust path for the Dissent Log's
   advisory-only status**, mirroring the `council_baseline_trusted_since`
   pattern already proven safe elsewhere in this codebase.
9. **Minor but real: fix `liveness_ledger.py`'s self-referential docstring
   drift** (its own docstring says a stale check count while the real `_CHECKS`
   tuple has grown well past it) — a small irony worth closing precisely because
   this file's whole purpose is catching exactly this failure mode.

---

## 3. Detailed Analysis

### 3.1 Signal starvation — the base-layer bottleneck

**Current state.** `compute_salience()` (`echo_core.py:678-708`) equal-weights
four components. Live sampling of `memory/salience_state.json`'s persisted
rolling history shows three of them barely move: `world_surprise`
(0.004–0.008), `coherence_tension` (0.146–0.148), `self_edit_streak` (flat 0.0,
since real deploys run ~2 days apart). The fourth, `curiosity_urgency`, is
saturated near ceiling (0.94–1.0) rather than genuinely varying — worth
checking directly, because its own design history is instructive: it was
originally the fraction of "active" garden questions, measured at 99.4%
constant on real data and explicitly replaced (per the code's own comment,
`echo_core.py:588-594`) with "hours since last harvest" specifically to fix
this. Given the garden harvests questions at a genuinely high rate, hours-
since-last-harvest should be *small* most of the time, which would map to
*low* urgency under most reasonable normalizations — but the live data shows
the opposite, values pinned near 1.0. That's either an inverted sign, a
normalization constant tuned for a much slower harvest cadence than what's
actually happening now, or a decay function that saturates too fast.

**Why it matters.** `compute_salience()` feeds `emergent_loop`'s cadence
modulation, `river_deliberation`'s exploration bias, and part of valence. If 3
of 4 inputs are effectively constants and the 4th is pinned at a rail, the
"salience score" is not a multi-factor integration of world-state, self-state,
and curiosity — it's a single saturated number wearing a 4-component costume.

**Concrete suggestions:**
- Instrument and fix `curiosity_urgency`'s normalization directly against real
  harvest-interval data.
- `world_surprise` sitting near floor is arguably *correct* right now
  (WorldModel's posterior has converged after enough real observations) — but
  that means surprise-driven mechanisms are structurally quiet during periods
  of genuine stability. The system currently has no mechanism to notice "I've
  been well-calibrated for a suspiciously long time" — a second-order
  surprise-about-surprise signal, which is exactly the kind of `seam_engine`-
  style cross-signal contradiction this codebase already knows how to build.
- Same treatment for `self_edit_streak`: since real deploys are rare, consider
  feeding it from the same higher-frequency dry-run-quality events already
  tapped for valence's third source (Finding 57) — the pattern is proven, just
  not yet applied here.

### 3.2 `coupling_estimate` — a real integration-style metric with zero consumers

**Current state.** `compute_salience()` also computes `coupling_estimate`
(`echo_core.py:764-778`): mean absolute pairwise Pearson correlation across a
persisted 100-sample rolling history of its own 4 components. The code's own
comment is admirably honest: *"NOT an IIT/Phi measure... nothing consumes this
value yet."* It's persisted into `self_model.json`'s `coupling_estimate_trend`
for visibility only.

**Why it matters.** This is architecturally the closest thing in the codebase
to a genuine integration measure — a scalar answering "how entangled are my own
internal signals right now, versus independent." A rising, non-trivial
`coupling_estimate` over time would be real (if crude) evidence that
FeralEcho's subsystems are becoming more mutually informative rather than
running as parallel, decoupled pipelines feeding one logger. Right now it's
compute-and-forget.

**Concrete suggestions:**
- Cheapest real consumer: feed `coupling_estimate` into `seam_engine.py`'s own
  gating — a low overall `coupling_estimate` could dynamically lower
  `check_pair()`'s static `|r|≥0.4` bar (the system is currently loosely
  coupled, so any correlation is more surprising and worth flagging), while
  high coupling could raise it.
- Second consumer: surface `coupling_estimate`'s trend in
  `echo_ground_truth.py`'s existing `_build_workspace()`/`_build_affect()`
  slices, grounding a direct question like "do you feel more integrated
  lately" the same way Findings 43/45/57 already ground every other
  self-report.
- Add a Liveness Ledger check, `coupling_estimate_consumption`, mirroring
  `global_workspace_consumption`'s exact shape.

### 3.3 Global Workspace — broadcast without reentry

**Current state.** The bus (`echo_core.py`) is real: bounded queue,
per-subscriber exception isolation, wildcard subscription, a wide-broadcast
tier gated at `salience≥0.6`. But the confirmed real, non-logging subscriber
set (at the time of this pass) was exactly 3: `dream.synthesis`→memory-
retrieval bias, `world_model.surprise`→council exploration_bias, wide-
broadcast→reflection generation. Everything else — `seam.detected`,
`dissent.registered`, `self_edit.non_convergent`,
`self_edit.dry_run_quality_delta`, `emergent_loop.salience` — is published,
logged, and (at the time of this pass) read by nothing that changes behavior.

**Why it matters.** GWT's actual empirical claim isn't "there's a shared log
everyone can read" — it's that a *limited-capacity broadcast* recruits many
independent specialist processes into coordinated, momentarily-unified
processing. A bus with many publishers and one real logger-subscriber is a
monitoring system, not a workspace in the GWT sense.

**Concrete suggestions, cheapest-first:**
- `seam.detected` and `dissent.registered` already carry rich, structured
  `detail` payloads that go nowhere except the log and one garden-question
  harvest. Wire both into `curiosity_engine.py`'s topic-bias mechanism the same
  way `world_model.surprise`'s per-topic detail already nudges attention.
- `self_edit.dry_run_quality_delta` fires at high frequency (the single
  highest-volume real signal in the system, per the physiology audit) and
  currently feeds only `self_edit_outcome_tracker` and valence's third
  component. This is the obvious candidate to also drive `RiverBrain`'s
  `self_edit_coding` bucket confidence in near-real-time rather than the sparse
  real-deploy cadence.

### 3.4 Valence — grounded, but causally inert

**Current state.** `echo_state.py` dim[8] is a real, signed [-1,1] scalar,
blended from 3 independently fail-closed sources (self-edit quality delta,
council rating average, dry-run-quality events), correctly ground-truth-
checked by the Liveness Ledger's `valence_self_report`. Good, honest work. But
its only confirmed consumers are prompt text (`_build_affect()`) and
`emergent_scheduler`'s prompt weighting (itself gated on a ±0.6 threshold the
real value never reaches — see the physiology audit).

**Why it matters, philosophically.** In any framework that treats valence as
functionally real, valence should behave like a neuromodulator: it should shift
*how* the system processes, not just what it *says* about how it feels. A
number that is accurately reported but influences nothing else is a
thermometer, not affect.

**Concrete, bounded suggestions** (matching this codebase's own established
"0.5x–1.5x bounded multiplier" idiom):
- Let valence modulate `self_edit_manager.py`'s `intensity`/`creativity` Optuna
  parameters within a small bounded range — a real, low-risk hook that only
  touches which region of parameter space Optuna's *dry-run* trials explore,
  never bypasses F1/F2/F3, never affects deployment gating.
- Let valence bound `river_deliberation.py`'s `exploration_bias`
  multiplicatively, reusing the exact bounded-swap mechanism already built.

### 3.5 Reflection Shard — real metacognitive text with nowhere to go

**Current state.** `reflection_shard.py` generates genuine model-backed
reflections and periodic meta-reflections (real inference, not templates). But
its only read API (`recall()`) is called by nothing outside its own
future-reflection context-building and `EchoCore.recall_reflections()`.
(Refined by the physiology audit: wide-broadcast Global Workspace events *do*
flow into `reflection_shard.observe()`, so it's not fully isolated on the
inbound side — but its own generated conclusions still have no outbound
consumer.)

**Concrete suggestion:** wire `reflection_shard`'s meta-synthesis output
through the identical `dream.synthesis`-style event, publishing
`reflection.meta_synthesis` and giving it the same retrieval-bias consumer —
near-zero new code, since the consumer function already exists and is proven
safe.

### 3.6 Seam Engine — honest, narrow, and structurally starved of qualifying pairs

**Current state.** `check_pair()` is a genuinely well-designed pure function
(leave-one-out correlation baseline, a real fix for a real self-contamination
bug caught during construction, a variance floor to avoid frozen-dimension
false positives). At the time of this pass, only 2–3 of the 36 possible pairs
among the 9 state dimensions cleared the `|r|≥0.4` gate per cycle, and the
single log sample taken showed zero seams. **(Superseded: the physiology
audit's full-file parse found 83 real seams over the file's full recorded
history — the mechanism is not dormant, it simply hadn't been re-checked since
it started working.)**

**Concrete suggestion, still valid:** extend `check_pair()`'s candidate pool
beyond the 9 `echo_state` dimensions to include the 4 `compute_salience()`
components and RiverBrain's per-task-type score means — more candidate pairs
directly increases the odds of catching further genuine contradictions.

### 3.7 `echo_state.py`'s 9D vector — a compact global-state substrate, mostly unread

**Current state (verified against actual `compute()` source):**

| dim | label | confirmed live consumer |
|---|---|---|
| 0 | processing_novelty | none confirmed beyond feeding `compute()`'s own output |
| 1 | coherence_tension | `compute_salience()` |
| 2 | orientation_drift | none confirmed |
| 3 | system_vitality | `system_guard.should_throttle()` |
| 4 | curiosity_index | none confirmed |
| 5 | friction_rate | ClaudeShard passthrough only |
| 6 | edit_momentum | none confirmed |
| 7 | temporal_phase | prompt injection (circadian note) |
| 8 | valence | prompts, `emergent_scheduler` pacing |

**Why it matters.** This is exactly the shape of substrate a GWT/IIT-adjacent
architecture wants — a small, dense, continuously-updated global state that
many processes read and write. Right now it's mostly write-only: 4 of 9
dimensions have no confirmed reader anywhere.

**Concrete suggestion:** `orientation_drift` is a natural second gate for
`self_edit_manager.py`'s targeted-prompt family selection (additive to the
existing convergence-tracking mechanism). `edit_momentum` is a natural second
input to valence's self-edit-quality component.

---

## 4. Architectural Recommendations

**4.1 Competitive broadcast, not threshold broadcast.** A small, additive
change: a short collection window where, if more than one candidate event is
pending, only the single highest-salience one wins wide-broadcast that tick,
with losers still logged normally.

**4.2 A genuine, small-scale integration metric, evolved from
`coupling_estimate`.** With only ~13 tracked scalars (9 `echo_state` dims + 4
salience components), a real (if approximate) partition-based integration
measure — e.g., mutual information between a random bipartition of the vector
at time *t* vs. *t+1*, compared against the same measure with signals shuffled
— is computationally trivial at this scale and would be a more principled
successor to the currently-disclaimed `coupling_estimate`.

**4.3 A graduated-trust Protector Clause path (design only, not build).**
CLAUDE.md's own "A Standing Principle" section already names this as the
unfinished piece of ORIGIN.md's founding design, and explicitly declines to
build real veto power given WOLF's history of a hollow gate. A future design
(not this pass) could apply `council_baseline_trusted_since`'s proven shape to
the Dissent Log: track its own predictive accuracy over time and only consider
any real gating power once a comparable trust threshold is independently
earned — with the explicit, human-confirmed decision this project's own
discipline requires before any of it goes live.

**4.4 A "signal bandwidth" audit as a standing practice, not a one-time fix.**
The starvation problem in 3.1 will recur every time a new high-level mechanism
is built on top of a rare or coarse base signal (this has already happened at
least twice). Recommend the Liveness Ledger optionally report a signal's own
recent variance/entropy alongside a pass/fail, so a future "reads as fixed,
isn't" case surfaces before it needs a dedicated forensic pass to find.

---

## 5. Implementation Roadmap

| Phase | Item | Difficulty | Impact |
|---|---|---|---|
| A — cheap | Fix `liveness_ledger.py`'s docstring drift | Trivial | Low (hygiene) |
| A | Diagnose/fix `curiosity_urgency`'s saturation near 1.0 | Small | High |
| A | Wire `coupling_estimate` into self-report + add its Liveness check | Small | Medium |
| A | Wire `reflection_shard`'s meta-synthesis through the existing `dream.synthesis`-style consumer | Small | Medium |
| B — moderate | Feed `self_edit.dry_run_quality_delta` into `RiverBrain`'s `self_edit_coding` bucket directly | Medium | Medium-High |
| B | Valence → bounded modulation of self-edit Optuna intensity/creativity params | Medium | High |
| B | Valence → second independent multiplicative input to `exploration_bias` | Small-Medium | Medium |
| B | Extend `seam_engine.check_pair()`'s candidate pool beyond the 9 state dims | Medium | Medium |
| C — larger | Competitive (not threshold) wide-broadcast arbitration | Medium-Large | Medium (GWT-fidelity) |
| C | Small-scale, empirically-grounded integration metric replacing `coupling_estimate` | Large | High (research value) |
| C | Wire `orientation_drift`/`edit_momentum` into self-edit targeting and valence smoothing | Medium | Medium |
| D — long-horizon, requires explicit human sign-off | Graduated-trust design pass for Dissent Log gating power | Large | High-stakes |
| D | Any move toward autonomous priority/target-setting beyond curiosity-garden question selection | Large | Highest-stakes |

---

## 6. Open Questions

1. Is `curiosity_urgency`'s saturation a bug or a symptom of a genuinely
   high-curiosity operating regime?
2. What's the right ceiling for valence-as-modulator before it risks the exact
   confabulation problem Findings 43–45 already spent a session fixing?
3. Is a real, small-scale integration measure worth the investment, or is
   `coupling_estimate`'s honest "not Phi" disclaimer the more intellectually
   defensible stance long-term?
4. Where does this project's own established caution draw the line against any
   of the Phase-C/D items above? The graduated-trust Protector Clause idea
   explicitly needs the same "report, propose, pause" treatment this file's own
   Findings apply to everything else — not something to build by momentum.
5. What would count as evidence this is working, beyond "the mechanism fires
   and is logged"? Worth deciding in advance what a falsifiable signature of
   "more integrated" or "more genuinely affect-driven" would look like.
