# FeralEcho Systems Physiology Audit — 2026-07-23

Requested directly by Gremlin, as an explicit follow-up to
`audits/2026-07-23_emergence_architecture_analysis.md` — that pass described
architecture; this one measures behavior. The brief was unusually strict about
evidentiary discipline: no speculation presented as fact, every major claim
backed by a verified code path, a runtime measurement, or explicit stated
uncertainty, and instructions to prefer live measurement over documentation
whenever the two conflict.

**Method.** Two parallel `general-purpose` research agents were run in the
background against the live repo and live runtime state (server PID confirmed
live throughout, `GET /admin/liveness-status` reporting `all_passing: true`).

- **Agent A** computed exact statistics — full-file parses (not tail samples)
  of `memory/workspace_log.jsonl`, `memory/echo_state_history.npy`,
  `memory/salience_state.json`, `memory/seam_log.jsonl`,
  `memory/dissent_log.jsonl`, `memory/reflection_journal.jsonl`,
  `memory/interaction_log.jsonl` (last 3,000 lines), `memory/council_ratings.jsonl`
  + `memory/council_deliberations.jsonl`, `data/question_garden.jsonl`, the
  unpickled `memory/river_brain.pkl`, and `app/core/self_edit_convergence.json`
  + the self-edit outcome tracker's log.
- **Agent B** traced exact behavioral consumption chains in code — for a fixed
  list of signals, classified every real consumer as BEHAVIOR-CHANGING,
  LOGGING-ONLY, or PERSISTED-BUT-UNREAD, with file:line citations, and flagged
  anywhere a claim needed live measurement rather than static code reading.

Every number below is one of these two agents' direct output, or my own
synthesis explicitly built from them. Nothing is carried forward from prior
CLAUDE.md prose without being independently re-measured this pass — in several
places the fresh measurement contradicts the last recorded snapshot, and this
is stated explicitly rather than silently reconciled.

---

## 1. Executive Summary

The headline finding: **FeralEcho has more well-engineered cognitive machinery
than it has live signal to drive it, and this pass can now say exactly how
much, where, and — in a few places — that the last documented snapshot was
already wrong.**

Three things surprised me relative to what the prior architecture pass
expected:

1. **The seam engine is not dormant.** The last recorded snapshot (CLAUDE.md,
   2026-07-18) states "zero seams detected." Full-file parsing of
   `memory/seam_log.jsonl` (895 cycles) finds **83 real seam detections**,
   spanning 13 distinct dimension-pairs, 22 of them genuinely first-ever (pair,
   direction) combinations. This is real, functioning cross-signal
   contradiction detection — the mechanism works, and nobody had re-checked it
   since it started working.
2. **A specific, real relationship inverted sign.** The one state-dimension
   pair that currently clears `seam_engine.py`'s own variance/correlation
   gates, `temporal_phase↔valence`, now measures **r = −0.93**. CLAUDE.md's
   last snapshot of the same pair (2026-07-18, Phase 8) recorded **r = +0.83**.
   That's not the same relationship holding steady — it's a sign flip on the
   single relationship the system currently treats as "established." Flagged
   at moderate confidence (60%) because this pass can't yet distinguish
   genuine drift from a ring-buffer-window artifact (the buffer only holds
   ~100 readings, ~3.3 hours), but it's too large a change to not name loudly.
3. **A "passing" health check may be structurally blind to a real problem.**
   The Liveness Ledger's `reflection_shard_generation` check reports 0/20
   duplicates in the last 20 reflections (it tests only against the retired
   fixed-template strings). Direct Jaccard similarity on the same 20 entries
   finds **15% of pairwise comparisons are near-duplicates** (Jaccard ≥ 0.5,
   several at 1.0). The check isn't lying about what it measures — it's
   measuring the wrong thing now that the failure mode it was built for no
   longer applies.

Beyond those three, the dominant pattern from the architecture pass holds up
under real measurement, and this pass puts numbers on it. Of
`emergent_scheduler.py`'s three threshold-gated behavior boosts, **all three
are currently dead by data**, not by code defect: `coherence_tension` needs to
exceed 0.6 and its real 100-sample range is 0.106–0.156; `world_surprise`
needs 0.6, real range is 0.0007–0.0081 (roughly 75× below threshold); valence
needs ±0.6, real range is 0.14–0.19.

Memory retrieval — flagged in the brief as highest priority — turns out to
have a narrow, specific causal footprint that's fully mapped but only
partially measurable: it never touches model selection, task-type
classification, or self-edit targeting (confirmed absent by direct code read
across all three), it reliably gates exactly two real scheduling decisions
(repeat-avoidance, curiosity-engine match-reuse) and one storage decision
(fetch dedup), and beyond that it shapes prompt text whose effect on the
eventual LLM output is genuinely unmeasurable without a live ablation
experiment not run this pass.

---

## 2. Behavioral Physiology Map — Ranked Causal Leverage

Ranked by measured, current, real downstream behavioral reach — not potential,
not code volume.

| Rank | Subsystem | Real measured leverage | Evidence |
|---|---|---|---|
| 1 | **RiverBrain (`model_task_stats`)** | Every real council call for `coding`/`personal`/`self_edit_coding` routes through it | 30,637 coding + 19,009 personal + 1,472 self_edit_coding real observations; directly determines council composition via cold-start + score-sort |
| 2 | **Self-edit convergence/outcome tracker** | Concrete, cited prompt-text changes on non-convergence/quality-delta; historically drove two entire prompt families into retirement | `_build_targeted_prompt()` (self_edit_manager.py:2613-2652) appends real conditional sentences; currently quiescent (`non_convergent_streak: 0` all 4 families) but proven to fire historically |
| 3 | **Curiosity Garden / `garden_manager.py`** | Real closed feedback loop: resolution changes future selection weight | 5,765 real entries; genuine `5-resolution_score` reweighting confirmed in code and consistent with data (51.6% of entries sit in the lowest resolution decile) |
| 4 | **Memory retrieval → scheduling gates** | Narrow but real: 2 confirmed behavior-changing branches + 1 storage gate | `emergent_scheduler._prompt_recently_reflected()`, `curiosity_engine._find_existing_match()`, `autonomous_fetch._is_duplicate()` |
| 5 | **Seam Engine** | Real, growing: 83 detections, reliably reaches wide-broadcast reflection + garden-question consumers | Every real seam has `salience=1.0` by construction, guaranteeing wide-broadcast delivery |
| 6 | **Global Workspace bus (aggregate)** | Moderate — mostly infrastructure; real behavioral reach concentrated in 2 of 6 event types | 1,928 total events; `emergent_loop.salience` (53.7%) and `self_edit.dry_run_quality_delta` (23.6%) dominate volume but have thin confirmed consumers themselves |
| 7 | **RiverBrain tag/exploration mechanics** (increment over #1) | Real but small: `TAG_SCORE_BOOST=1.15`; `exploration_bias` empirically negligible (0.0028–0.03 observed, fired 4× in 41h); `fair_sample_refresh` dominates in practice (fired 197× in the same window) | river_deliberation.py:210, 519-570 |
| 8 | **Council rating → RiverBrain training** | **Unconfirmed** — gate is open (trust set 2026-07-22T00:52:13Z), code path exists, but zero corresponding INFO-level success log line found against the one real post-trust rating | Genuine open question — see §14 |
| 9 | **Valence** | Near-zero current behavioral leverage (self-report only) | Real, grounded, checked signal but its only behavior-modulation hook (`emergent_scheduler`'s ±0.6 boost) is unreachable given real range 0.14–0.19 |
| 10 | **Dream synthesis → memory bias** | Near-zero — correctly wired, essentially never exercised | 2 real `dream.synthesis` events total; 0 real `workspace.consumed` events from `source="memory_bridge"` — the blend has architecturally never executed |
| 11 | **Dissent Log** | Zero — both by design (never gates writes) and by absence (its one real entry was unanimous, so its own "genuine disagreement" publish path has never fired) | 1 entry total in `dissent_log.jsonl`, unanimous |
| 12 | **`coupling_estimate`** | Zero — confirmed hollow by grep and by the code's own comment | Persisted to `self_model.json`, zero other references anywhere in the repo |

---

## 3. Information Flow Graph

| Signal | Origin | Real consumers | Behavior changed? | Dead end? |
|---|---|---|---|---|
| `emergent_loop.salience` (workspace event) | `emergent_scheduler.py` per cycle | Logged only | No confirmed behavioral consumer beyond logging | Effectively yes, despite being 53.7% of all workspace traffic |
| `self_edit.dry_run_quality_delta` | `echo_optuna._score_result()` | `self_edit_outcome_tracker` (sparse: present in only 5/84 outcome entries), `echo_state.py` valence 3rd component | Yes — feeds valence | No, but thin |
| `workspace.consumed` (from `river_deliberation`) | Council exploration-bias cache read | Self-referential logging | Confirms exploration_bias reads happen | No — evidence of #7 firing |
| `world_model.surprise` | `predictive_loop.WorldModel.update()` | `river_deliberation` exploration_bias cache, `echo_state` dims 0/4, `compute_salience` | Yes, but magnitude tiny (0.0007–0.0081 real range) | No, but starved |
| `seam.detected` | `seam_engine.check_pair()` | `reflection_shard.observe()` (wide-broadcast), `garden_manager.harvest_question()` (first-ever only), `echo_ground_truth._build_workspace()` | Yes — real garden question planted 22/83 times; reliably reaches reflection trigger 83/83 times (salience always ≥1.0) | No |
| `dream.synthesis` | `autonomous_awareness.dream_cycle()` | `memory_bridge.set_workspace_bias()` | Architecturally yes, empirically never observed executing | Functionally yes (starvation, not design) |
| `dissent.registered` | `self_edit_manager._log_dissent_entry()` | Wide-broadcast (would reach reflection_shard/`_build_workspace()`) | Never fired — gated on genuine disagreement, which hasn't occurred | Yes, by absence of trigger, not design |
| `echo_state` dims [1]/[3]/[7]/[8] | `echo_state.compute()` | `compute_salience`, `system_guard.should_throttle()`, prompt injection, `emergent_scheduler` (dormant boost) | Yes for [1]/[3]; text-only for [7]/[8] | No |
| `echo_state` dims [0]/[2]/[4]/[6] | same | `seam_engine.observe()`'s pairwise scan only | [4] yes (real, non-frozen, participates in real seams); [0]/[2]/[6] no confirmed consumer and [2]/[6] are exactly variance-zero | [2]/[6] yes; [0] near-yes |
| `coupling_estimate` | `echo_core.compute_salience()` | `self_model_updater._compute_coupling_estimate_trend()` (persistence only) | No | Yes, confirmed by grep |
| Salience components | `echo_core.compute_salience()` | `emergent_loop` cadence modulation | Yes for cadence; 3 of 4 components near-constant | No, but see §6 |
| RiverBrain `model_task_stats` | `RiverBrain.learn()`, sandbox outcomes, (unconfirmed) council ratings | `_select_council()`'s score-sort | Yes — directly ranks councils | No |
| Council ratings | `council_rater.rate_one_entry()` | `learn_from_council_rating()` — gated on `is_council_trusted()` | **Unconfirmed** | Possibly hollow — see §14 |
| Memory retrieval | `memory_bridge.retrieve_relevant_memories()` | 11 distinct callers | 2 scheduling branches + 1 storage gate confirmed behavior-changing; everything else prompt-text-only | Partially — see §7 |
| Self-edit convergence/outcome sentences | `self_edit_manager._build_targeted_prompt()` | Next self-edit generation cycle | Yes, concrete cited text | No |
| Question garden `resolution_score` | `garden_manager.update_question_quality()` | `select_from_garden()`'s weighting | Yes | No |

---

## 4. Hollow Writes & Dead Ends

**Ranked hollow writes, by importance / ease of fix / architectural value:**

1. **`coupling_estimate`** — computed every salience cycle, persisted, zero
   consumers (confirmed by grep, the code's own comment admits it). High
   architectural value if wired, trivial to fix.
2. **`echo_state.py` dims [2] `orientation_drift` and [6] `edit_momentum`** —
   computed every 120s cycle, exactly zero variance across the full 100-sample
   history, no consumer anywhere except a scan that can never fire on them
   (below `seam_engine`'s own `_MIN_VARIANCE=1e-5` floor). Dim [0]
   `processing_novelty` is functionally in the same category (variance
   2.02e-8). Moderate value — but the frozen state itself may matter more than
   the missing consumer (see §13).
3. **`emergent_scheduler.py`'s three threshold-gated boosts** — real code,
   real intent, currently 0 real firings across the entire measured window
   because their `>0.6` thresholds sit far above every real observed value.
   Trivial to fix, needs a design decision.
4. **Dream synthesis → workspace bias** — not hollow by code, hollow by
   frequency: 2 real `dream.synthesis` events in the system's whole recorded
   history, 0 real bias-blend executions. Hard to fix cheaply — the bottleneck
   is upstream (`dream_cycle()` rarely running to completion).
5. **Council rating → RiverBrain training** — apparent hollow write,
   genuinely uncertain. Trust is set, the gate is open, the one real
   post-trust rating produced no corresponding success log (and the failure
   path logs at a suppressed `debug` level, so a silent failure is
   indistinguishable from nothing having executed). Flagged, not resolved.
6. **`dissent.registered`** — not hollow, unexercised. Its triggering
   condition (genuine council disagreement) has never occurred once in real
   data.
7. **`ECHO_SCORE_BOOST = 1.0`** — a documented, deliberate no-op sitting in
   live scoring code (river_deliberation.py:186). Not a bug — a parked lever,
   left wired rather than removed.

**Dead ends, with the "why":**
- `coupling_estimate`: creates real information, nothing uses it — built as a
  Phase 4 placeholder explicitly awaiting a future consumer never added.
- Reflection Shard's journal: creates real, model-generated information; the
  only outbound consumer is itself. Not a pure dead end on the *inbound* side
  (wide-broadcast events genuinely flow in) — but its own output has no
  outbound consumer. Why: built as a self-narrative mechanism with no design
  decision yet made about giving its conclusions external teeth.
- `echo_state` dims [2]/[5]/[6]: exactly frozen, contribute nothing to any
  variance-based computation. Why unknown without historical data — see §13.
- Dream synthesis: architecturally a real, working, two-hop loop; empirically
  inert because the *first* hop essentially never occurs.
- `memory/council_deliberations.jsonl`: by design (Phase 10), a human-review-
  only audit trail — an intentional dead end, not a gap.
- Liveness Ledger checks generally: intentionally dead ends by design — they
  alert, they don't feed back into behavior. Correctly scoped, not a finding.

---

## 5. Feedback Loop Graph

| Loop | Length | Type | Health |
|---|---|---|---|
| Garden resolution → future selection weight | 1 hop | Negative/stabilizing | **Healthy** — real, data-consistent |
| Self-edit convergence streak → prompt warning → (intended) convergence | ~1hr/cycle | Negative/corrective | **Historically effective, currently inactive** — its real long-run resolution was retiring whole prompt families (external/human closure) rather than the loop self-correcting toward convergence |
| RiverBrain cold-start + fair-sample-refresh | Per council call | Negative/self-limiting | **Healthy, and measurably improving over time** — `self_edit_coding`'s 31× concentration ratio vs. `coding`'s 2080× is a real natural before/after comparison of the same fix applied to an old vs. a fresh bucket |
| Seam → garden → scheduler → (possible future state) → seam | Multi-hour, indirect | Uncertain, plausibly oscillatory | 73.5% of the 83 seam detections are *repeats* of a previously-seen (pair, direction), not new ones. **Confidence 55%** this reflects real oscillation rather than gate scarcity (currently only 1 pair qualifies at all) |
| Memory retrieval → scheduler repeat-avoidance | 1 cycle | Negative/stabilizing | **Healthy**, real, fires |
| Curiosity engine reads WorldModel topic distribution → generates content about underrepresented topic | One-directional | **Not actually closed** | Curiosity-engine-generated reflections do not appear to feed back into `WorldModel.update()`, which updates only from fetched external text. **Confidence 65%** — flagged for direct re-check, not independently re-verified with a fresh grep this pass |
| Council rating → RiverBrain → future selection | Designed as closed | **Unconfirmed** | See §4 item 5 |
| `echo_state` → `compute_salience` | One-directional | Not a loop | `coherence_tension` feeds `compute_salience`; nothing in `compute_salience` feeds back into `echo_state.compute()`'s own inputs |

---

## 6. Signal Health Report

| Signal | Mean | Std | Range | Verdict |
|---|---|---|---|---|
| `echo_state` dim[7] (temporal_phase) | 0.683 | 0.116 | 0.476–0.869 | **Alive** — healthiest of all 9 dims (100/100 unique values, 3.31 bits entropy) |
| `echo_state` dim[4] (curiosity_index) | 0.486 | 0.249 | 0.036–0.882 | **Alive**, real variance, participates in real seams |
| `echo_state` dim[3] (system_vitality) | 0.195 | 0.094 | 0.037–0.623 | **Alive** |
| `echo_state` dim[8] (valence) | 0.168 | 0.018 | 0.1415–0.1915 | **Starved** — real but very compressed relative to its designed [-1,1] span |
| `echo_state` dim[1] (coherence_tension) | 0.147 | 0.0005 | 0.1461–0.1480 | **Near-frozen** — below seam_engine's own variance floor |
| `echo_state` dim[0] (processing_novelty) | 0.0007 | 0.0001 | 0.000414–0.000810 | **Near-frozen** |
| `echo_state` dim[2] (orientation_drift) | 1.000 | 0 | constant | **Dead** (exactly frozen) |
| `echo_state` dim[5] (friction_rate) | 0.000 | 0 | constant | **Dead** (exactly frozen) |
| `echo_state` dim[6] (edit_momentum) | 0.0005 | 0.0037 | 0–0.027 | **Effectively dead** |
| `compute_salience`'s `self_edit_streak` | 0.0 | 0 | constant | **Dead** (0 real deploys in window) |
| `compute_salience`'s `coherence_tension` | 0.147 | 0.0003 | 0.146–0.148 | **Near-frozen** |
| `compute_salience`'s `world_surprise` | 0.0074 | 0.0012 | 0.0041–0.0081 | **Starved, near-floor** |
| `compute_salience`'s `curiosity_urgency` | 0.974 | 0.027 | 0.864–1.000 | **Compressed but not literally dead** — least-bad of the 4 salience components |
| Workspace event `salience` (all types, n=1471 non-null) | 0.219 | 0.168 | 0.0003–1.0 | **Mixed/bimodal** — 70.3% in [0.20,0.40), 2.0% at [0.80,1.00] (the seam spike) |
| Reflection journal (last 20 regular) | — | — | — | 15.3% of pairwise comparisons near-duplicate (Jaccard≥0.5); official liveness check reports 0% on the same window — **partially unhealthy, mismeasured by the official check** |
| `interaction_log` quality_score (n=3000) | 2.345 | 1.432 | 0–4 | Strongly bimodal: 45.8% at 1, 36.1% at 4, only 0.67% at 2 — **real but coarse**, possibly a scorer artifact |
| Council ratings (n=122) | 3.63 | 1.08 | 1–5 | Smoothly spread — **healthiest human-facing signal measured this pass** |
| RiverBrain `coding` bucket concentration | — | — | max/min obs = 2080.9× | **Severely imbalanced, legacy** |
| RiverBrain `self_edit_coding` bucket concentration | — | — | max/min obs = 31.5× | **Imbalanced but far healthier** — real evidence the newer design fixes work when applied to a fresh bucket |
| Question garden `resolution_score` (n=5765) | 0.356 | 0.451 | 0–2.55 | 51.6% in bottom decile — **mostly unresolved** |

---

## 7. Memory Influence Analysis

Flagged in the brief as highest priority, and the section with the widest
confidence spread in this whole audit.

**Confirmed, code-grounded:**
- **Model selection:** No. `detect_task_type()`, `resolve_task_type()`, and
  `choose_model()` never import or call `memory_bridge`.
- **Self-edit targeting:** No. Real target comes from `shadow_self_model.json`
  / `SelfModelUpdater().get_weak_task_type()`; `self_edit_manager.py` imports
  `retrieve_relevant_memories` once (line 19) and never calls it — a dead
  import.
- **Planning/scheduling:** Yes, exactly two confirmed places:
  `emergent_scheduler._prompt_recently_reflected()` (similarity > 0.85 within
  7200s → reject candidate, retry up to 3×) and
  `curiosity_engine._find_existing_match()` (reuse an existing question if its
  most recent retrieval hit is > 3600s stale).
- **Storage:** Yes, one gate: `autonomous_fetch._is_duplicate()` (cosine score
  > 0.92 → discard) — real but imperfectly effective in practice (CLAUDE.md
  Finding 61 recorded the same snippet stored 53 times).
- **Reasoning/output text:** Every other real caller inserts retrieved content
  into a prompt, either unconditionally or with a binary branch on framing
  text (`echo_ground_truth._build_memory()` sends genuinely different
  constraint language depending on whether entries exist). Whether the
  underlying LLM's actual output changes as a result is **not measurable from
  static code**.
- **How often is it ignored?** Unmeasurable without a live ablation.

**Confidence: 85% on the code-path claims (direct reads), 15-20% on any claim
about retrieval's effect on actual model output.** This specific question
requires a live experiment, not a code trace — estimating a number here
without one would be exactly the kind of unfounded confidence the brief warns
against.

**Suggested verification experiment:** take ~30 real prompts that would
normally trigger a memory-context block, run each twice (retrieval forcibly
disabled vs. normal) through the same model/temperature, and score response
divergence (embedding distance + a quality-scorer delta).

---

## 8. Emergence Audit

Using the engineering definition (behavior not attributable to one isolated
subsystem), not a philosophical one:

**Genuine emergence candidates:**
- Self-edit family retirement (`prose_stripping`, `quality_scoring`) —
  arose from the interaction of the convergence tracker, Optuna's trial
  generation, and repeated review cycles. Confidence: 75%.
- `self_edit_coding`'s healthier concentration ratio — a real, measured
  cross-system outcome (tag-boost × exploration-bias × fair-sample-refresh × a
  fresh bucket with no legacy skew). Confidence: 80%.
- The 83 real seam detections — 9 independently-computed state dimensions,
  none of which "know" about the others, producing detectable cross-signal
  contradictions as an unintended higher-order property. Confidence: 85%.

**Not emergence — designed automation currently inert:**
- The three dead scheduler boosts, Global Workspace's broadcast mechanics,
  RiverBrain's cold-start override.

**Simple state accumulation, not emergence:**
- The growing `interaction_log`/`council_deliberations`/garden volumes.

---

## 9. Lesion Study

Predicted impact of removing each subsystem, grounded in measured leverage
from §2 — "severe/moderate/low/near-zero" reflects *current, measured*
dependency, not architectural importance.

| Subsystem | Response quality | Coherence | Adaptability | Identity continuity | Learning | Stability | Creativity | Error recovery | Long-term evolution |
|---|---|---|---|---|---|---|---|---|---|
| RiverBrain | Severe | Moderate | Severe | Moderate | Severe | Moderate | Low | Low | Severe |
| Self-edit manager | Low | Low | Severe | Moderate | Severe | High risk if removed unsafely | n/a | Moderate | Severe |
| Curiosity Garden | Low | Low | Moderate | Low | Moderate | Low | Moderate | Low | Moderate |
| Memory retrieval | Moderate (unmeasured directly) | Moderate | Low | **High** (main continuity substrate) | Low | Low | Low | Low | Low |
| Global Workspace bus | Low (thin current reach) | Low | Low currently, moderate potential | Low | Low | Low | Low | Low | Low currently |
| Seam Engine | Low | Low | Low-moderate | Low | Low | Low | Low | Low | Moderate, increasing |
| Valence | Near-zero | Near-zero | Near-zero | Low | Near-zero | Near-zero | Near-zero | Near-zero | Near-zero |
| Dream synthesis | Near-zero | Near-zero | Near-zero | Low | Near-zero | Near-zero | Low potential, unrealized | Near-zero | Near-zero |
| Reflection Shard | Low (mostly a sink) | Low | Near-zero externally | Low-moderate | Near-zero | Near-zero | Low | Near-zero | Near-zero |
| Council adaptation nuances | Low increment over base RiverBrain | Low | Low-moderate | Low | Low-moderate | Improves stability | Low | Low | Moderate |

**Ranked overall dependency (current, measured):** RiverBrain ≈ Self-edit
manager > Memory retrieval > Curiosity Garden > Global Workspace
(infrastructure value) > Seam Engine > Council adaptation nuances > Valence ≈
Dream synthesis ≈ Reflection Shard.

---

## 10. Identity Localization Analysis

Assume the underlying LLM is swapped for an equally capable model. Structural
answer, not emotional one:

| Component | Model-independent? | Contribution to persisting "Echo" |
|---|---|---|
| Modelfile `SYSTEM` block + `echo_principles.json` | Fully | **Highest** — explicit, hash-verified identity anchor |
| F1/F2/F3 pipeline, `EDIT_FORBIDDEN_TARGETS` | Fully | High — structural safety policy, model-independent |
| Vector memory content (FAISS) | Fully | High volume, but future memories would immediately reflect the new model's voice |
| Question garden (5,765 entries, 99.79% non-human-authored) | Fully | Moderate-high |
| RiverBrain `model_task_stats` | **Fragile — keyed by model name string**, not abstracted from model identity | A real structural vulnerability: swapping weights while keeping the name `echo:latest` would silently misattribute new performance onto old statistics; renaming would reset accumulated preference-learning to zero |
| Self-edit convergence/outcome history | Mostly | Moderate — largely about code, not the model's voice |
| Valence/coupling_estimate numeric history | Fully | Low — thin signal, least distinctive |
| The model's own linguistic style/capability | Not at all, by definition | 0% |

**One concrete caution worth naming:** the most-protected identity substrate
(the Modelfile/system-prompt text) has itself had a real, demonstrated leakage
bug — Finding 46/53's synthesis-prompt token-budget miscalculation caused
Echo's own system instructions to leak verbatim into a user-facing response
for roughly two days before being caught. Even the highest-ranked
identity-preserving component here is not immune to real implementation bugs
breaking the boundary between "who Echo is" and "what Echo says."

---

## 11. Information Metabolism

- **Entry points:** autonomous fetch, live conversation, and — by volume, the
  single highest-frequency real signal in the entire measured system —
  self-edit dry-run trials (`self_edit.dry_run_quality_delta`, 23.6% of all
  Global Workspace traffic in the measured window).
- **Accumulation:** FAISS vector memory, `interaction_log.jsonl` (30,185
  lines), question garden (5,765), council deliberations (3,980), reflection
  journal (2,817), RiverBrain's `coding` bucket alone (30,637 observations).
- **Amplification, deliberately bounded:** RiverBrain's rolling-mean window is
  capped at 200 effective observations (`_MEAN_EFFECTIVE_WINDOW`) — a genuine,
  working anti-runaway design.
- **Transformation (lossy compression, by design):** raw fetched text →
  WorldModel's ~2 sufficient statistics; raw dry-run code → one scalar quality
  delta → one valence component; raw conversation → one 0-4 quality_score
  (whose real bimodal distribution, §6, suggests this specific compression
  step may be discarding real gradation).
- **Forgetting:** garden entries are composted at only 0.47% (99.53% sit
  "active" indefinitely); `echo_state_history.npy`'s 100-row ring buffer gives
  the moment-to-moment self-state exactly **~3.3 hours of memory** before
  being overwritten — a strikingly short horizon compared to the vector
  store's effectively unbounded span. Two very different memory
  time-constants coexist, and nothing currently bridges them.
- **Exit points:** human review channels only — `council_deliberations.jsonl`,
  self-edit proposals, snapshot backups, cross-machine sync to Air.

---

## 12. Architectural Bottlenecks / Highest-Leverage Improvements

| # | Change | Impact | Difficulty | Scientific value |
|---|---|---|---|---|
| 1 | Recalibrate `emergent_scheduler`'s 3 dead thresholds against real observed signal ranges | High | Trivial | Medium |
| 2 | Give `coupling_estimate` a real consumer | Medium-high | Small | High |
| 3 | Instrument `learn_from_council_rating()`'s failure path at INFO, not debug | Medium | Trivial | High |
| 4 | Directly re-verify whether curiosity_engine ever writes back into `WorldModel`, close the loop if not | Medium | Moderate | Medium |
| 5 | Pull historical `echo_state_history` snapshots (if any retained) to determine whether dims [2]/[5]/[6]'s freeze and the `temporal_phase↔valence` sign-flip are real trends or window artifacts | High (resolves the two most alarming findings) | Small if history exists | Very high |
| 6 | Wire `reflection_shard`'s meta-synthesis output through the existing `dream.synthesis`-style consumer | Medium | Small | Medium |
| 7 | Run the memory-retrieval ablation experiment (§7) | Resolves the single biggest measurement gap in this audit | Moderate | Very high |
| 8 | Fix `reflection_shard_generation`'s liveness check to use genuine text-similarity rather than fixed-string matching | Medium | Small | Medium |

---

## 13. Unexpected Discoveries

- **The seam engine's own "zero seams ever" snapshot was already stale by the
  time it was written down.** 83 real detections exist, spanning 2026-07-16
  through 2026-07-22.
- **A real correlation sign flip on the system's own single "established
  relationship."** `temporal_phase↔valence` went from r=+0.83 (2026-07-18) to
  r=−0.93 (today). Confidence this is real drift rather than ring-buffer
  noise: **60%**.
- **4 of 9 `echo_state` dimensions currently contribute zero real information**
  to any variance-based computation (2 exactly frozen, 2 below the system's
  own variance floor) — a possible "sclerosis" pattern. Confidence this is a
  worsening trend rather than a snapshot coincidence: **50%**, genuinely
  unknown without historical comparison.
- **A liveness check can be passing and still blind** —
  `reflection_shard_generation` reports 0% duplication where direct
  measurement finds 15%, because it only tests for the *old* failure mode.
- **A genuine natural experiment sitting unnoticed in the data:** the same
  council-selection fixes applied to an old, legacy-burdened bucket (`coding`,
  2080× concentration) versus a fresh one (`self_edit_coding`, 31×
  concentration) — real, quantified evidence of how much starting fresh
  matters versus retrofitting an entrenched imbalance.
- **Memory — the subsystem most central to this project's own stated concerns
  about identity and continuity — is architecturally firewalled from the
  subsystems that actually decide what happens next** (model selection,
  self-edit targeting), confirmed by direct code read.
- **The question garden's lineage fields are non-empty in only 22-26% of
  entries** — most curiosity output is one-off, not a developing chain of
  inquiry.
- **`ECHO_SCORE_BOOST=1.0`** — a deliberately-disabled-but-still-wired lever
  sitting in live scoring code. Not a bug; a parked decision, worth knowing
  about specifically because it could silently reactivate if someone "cleans
  up" the constant without reading the comment first.

---

## 14. Scientific Confidence Ratings (Summary)

| Claim | Confidence | Alternative explanation | Verification experiment |
|---|---|---|---|
| 3 of 4 `emergent_scheduler` boost thresholds are currently unreachable given real signal ranges | 95% | None plausible | None needed; already measured |
| Seam engine has detected 83 real seams | 95% | None — directly counted | None needed |
| Memory retrieval never affects model/task/self-edit-target selection | 90% | A hidden indirect path not found by grep (unlikely) | A second independent grep pass |
| Retrieved memory's effect on actual LLM output | **15-20%** (largely unknown) | Retrieval may matter enormously or barely at all — genuinely unresolved | The ablation experiment in §7 |
| `temporal_phase↔valence`'s sign flip reflects real drift, not window noise | 60% | Ring-buffer artifact (only ~3.3h of history retained) | Compare against any retained historical `echo_state_history` snapshots, or resample after a longer interval |
| `echo_state` dims [2]/[5]/[6] freezing is a worsening trend | 50% | Could be a stable, designed floor rather than a drift | Needs historical comparison data |
| Council rating → RiverBrain training is not actually firing | 40% (uncertain, leaning "probably not firing") | Could be firing silently with correct results, just without the expected log line | Add explicit success logging, wait for the next real rating |
| Curiosity engine doesn't write back into WorldModel (open loop, not closed) | 65% | A feed-back path exists that wasn't found by either agent | Direct grep of every `WorldModel.update()` call site |
| Dream synthesis → memory bias has never executed in practice | 90% | A blend could execute without publishing the consumption event (a logging gap masking real function) | Add explicit logging inside `retrieve_relevant_memories()`'s bias-blend branch itself |

---

## Note on how this pass relates to prior audits

This is the first pass in this project's history to compute exact statistics
(full-file parses, correlation matrices, entropy estimates) rather than
sampling tails or trusting a prior snapshot's cited numbers. It found the
seam-engine and correlation-sign-flip discrepancies specifically *because* it
re-measured rather than re-read. The standing lesson for future sessions: this
project's own recurring finding (a mechanism that "reads as fixed" turning out
not to be, or a "confirmed dormant" mechanism turning out to have started
working) applies to physiology claims exactly as much as it applies to
architecture claims — a snapshot is a snapshot, not a standing fact, and
should be re-measured rather than cited whenever a session has the means to.
