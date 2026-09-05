# FeralEcho: Closed-Loop Capability Integration Forensic Investigation

Investigation, not implementation. Nothing in this document was applied to the codebase. All claims
below trace to either a direct read of live source code, a direct live data read (unpickled
`river_brain.pkl`, live JSON/JSONL files, a live `SELF_EDIT.log` tail, live `sandbox/echo_projects/`
report files), or an explicitly-cited prior audit document — never from documentation claims alone,
per this mission's own Hard Rule 11. Full edge-by-edge and loop-by-loop machine-readable detail is in
`audits/closed_loop_capability_forensic.json`.

## Executive Finding

**Echo is neither uniformly "capability-rich but integration-poor" nor uniformly "shallow" — it is a
mixed system with one real, already-closed adaptive loop that is currently mis-tuned rather than
disconnected, one entire training pathway that is fully wired but functionally dead due to a precise,
narrow bug, and several apparently-complete pipelines (tool use, multi-file project generation) that
are hollow or empty at the exact edge that would make them consequential.** The strongest positive
finding is that a genuine, causally-verified, closed reflection→self-model→self-edit-targeting loop
already exists and was directly observed producing a real behavioral effect this session — but it is
currently dominated by a low-information keyword heuristic rather than the well-evidenced,
99,027-observation RiverBrain signal sitting one step away, unused. The strongest negative finding is
that Echo's most curiosity-and-planning-rich pipeline (`echo_projects`) has a **0% real historical
end-to-end success rate across 61 attempts** and has no failure→adjustment edge at all, meaning its
apparent completeness (curiosity → question → spec → plan → files → verification, every step
individually real) currently produces nothing usable and nothing that improves over time. The honest
answer to the governing question is: **for a specific, identifiable subset of the system — mostly
self-edit-adjacent, well-instrumented machinery — the integration hypothesis is true and the fix is
small and surgical. For another subset — multi-file generation, tool use, memory's causal effect on
behavior — the hypothesis is either false or genuinely unresolved, and more connectivity would not by
itself fix a 0% success rate or an unmeasured behavioral effect.**

## Current Causal Graph

```
input → task classification → [REAL, mature]
  ↓
memory retrieval (FAISS) → context injection → generation
  ↓ [REAL infra, behavioral effect UNVERIFIED on personal task, UNKNOWN elsewhere]
council deliberation / model selection (RiverBrain routing) → generation
  ↓ [REAL, causally verified — routing only, not content]
  │
  ├─→ tool listing → [DEAD END: no invocation path exists]
  │
  ├─→ verification (F1/F2/F3, code_verification.py, fitness gate)
  │      ↓ [REAL, independent, CAN reject success]
  │      ├─→ quality_score → RiverBrain.learn() → model_task_stats  [REAL, CLOSED]
  │      ├─→ council_rating → is_council_trusted()==True → learn_from_council_rating()
  │      │      [WIRED BUT DEAD — stale cursor, see below]
  │      └─→ self_edit_manager.save_reflection() → reflection_shard.jsonl (structured)
  │             ↓ [REAL]
  │             self_model_updater._compute_targets() → self_model.json targets
  │                    ↓ [REAL, well-evidenced: coding@2.37 vs 2.5 threshold, obs=99,027]
  │                    perform_self_edit()'s target-selection
  │                           ↑ [DEMOTED — see shadow override below]
  │
  ├─→ reflection_shard.py generative reflection (free-association)
  │      [REAL generation, but reads NO verification/outcome data — signal+past-reflections only]
  │      ↓
  │      shadow_model.propose_from_reflection() [pure keyword-count heuristic]
  │      ↓
  │      shadow_self_model.json targets.next_self_edit_focus
  │      ↓ [DEMONSTRATED LIVE to override the real signal above — 12/15 recent disagreements]
  │      perform_self_edit()'s target-selection [WINS as "highest-trust"]
  │             ↓
  │      next self-edit cycle → F1/F2/F3 → fitness gate → deploy/reject
  │             ↓ [REAL, 92% real deploy success, but fitness metric SATURATED — see below]
  │             (loops back to reflection/verification above)
  │
  └─→ curiosity (seam_engine/dream/curiosity_engine) → question_garden.jsonl [REAL, real lineage]
         ↓
         echo_projects spec → council PLAN → per-file GENERATE → F1/F2
                ↓ [0/61 real historical end-to-end success]
                verification [REAL, independent]
                ↓
                [NO EDGE: no failure→adjustment path exists back to curiosity/planning]

trace_id (request-scoped correlation) → interaction_log.jsonl + council_deliberations.jsonl
   [REAL, built 2026-09-02 — but does NOT yet reach workspace_log.jsonl / self_edit_outcome_tracker.py]

C1 (human-confirmed directive) → behavioral_state.json → deterministic exposure → model compliance
   [REAL, 100% architectural reliability; 75% (n=4) live compliance — see Part VIII discussion below]
```

## Edge Audit

Full table (18 edges) is in `closed_loop_capability_forensic.json`'s `edges` array, each with the
required Edge/Source/Destination/Mechanism/Exists/Executes/Reader-confirmed/Behavioral-effect-proven/
Persistent/Evidence/Confidence columns. Highlights, in the order the mission's Part II lettered them:

- **A (Curiosity→Question)**: real, live, 13,417 real garden entries. Lineage is real and substantial
  (58% of entries carry `parent_questions`, 42% carry `children`) — not merely schema presence.
- **B (Question→Goal)**: **does not exist.** `echo_projects_autonomy_state.json`'s real schema is
  exactly `{last_run_utc, last_status, spec_source}` — no goal ID, no competition between goals, no
  resumption pointer. A question becomes a one-shot spec, not a persistent objective.
- **C (Goal→Plan)**: real (council-deliberated file list), but carries no persistent identifier
  forward — no goal_id/plan_id cross-reference schema exists anywhere.
- **D (Plan→Execution)**: real and **precisely quantified this session**: of 61 real
  `sandbox/echo_projects/` project directories, only 13 (21%) ever reached the F2 multi-file
  import+run stage; the other 48 (79%) were blocked at F1 before execution was ever attempted. Of the
  13 that reached F2, **13/13 (100%) show F2 status = FAIL**. Net: **0/61 real cycles have ever
  produced a project passing both gates.**
- **E (Execution→Verification)**: real and independent (kernel sandbox, not self-report) — confirmed
  by this session's own live `SELF_EDIT.log` tail showing current, real `safety_blocked`/
  `staging_import_failed` rejections, and by echo_projects' own 100% F2-fail rate.
- **F (Verification→Reflection)**: **two separate mechanisms exist and must not be conflated.**
  `self_edit_manager.py`'s `save_reflection()` writes real outcome data (result, quality delta) into
  structured `reflection_shard.jsonl` entries — real verification-to-reflection data flow. Separately,
  `reflection_shard.py`'s own generative reflection loop (`_generate_reflection()`) was read in full
  this session and confirmed to use **only** a signal string plus similarity-retrieved past
  reflections as its generation input — zero reference to verification/outcome/quality data anywhere
  in its source. Treating the latter as "verification reaching reflection" would be a real category
  error this investigation was specifically warned against.
- **G (Reflection→Self-Model)**: real, live, and well-evidenced. `self_model_updater.py`'s
  `_compute_self_edit_stats()`/`_compute_targets()` reads the structured self-edit reflection entries
  from F above and produces a genuinely data-driven target. Live confirmation:
  `self_model.json`'s current real `targets` = `{"next_self_edit_focus": "coding", "reason":
  "avg_quality=2.37 (threshold=2.5), obs=99027"}`.
- **H (Reflection→Metacognition)**: **the single most important finding of this investigation.**
  `shadow_model.propose_from_reflection()` (called every real reflection cycle, per
  `app/emergent_scheduler.py:723-724`) is a pure keyword-count heuristic — no LLM call, four task
  types with 5-6 keywords each, fires on ≥2 matches — that writes `shadow_self_model.json`'s
  `targets.next_self_edit_focus`. `perform_self_edit()` reads **this shadow file first**, explicitly
  commented `"highest-trust signals"`, and only falls back to the real, G-derived signal if the shadow
  file has no focus set. Live data: `shadow_accuracy.jsonl`'s last 15 hourly comparisons show the
  shadow focus **disagreeing with the real focus in 12/15 (80%) of readings**, with the real focus
  staying `"coding"` throughout (matching `self_model.json`'s well-evidenced target) while shadow
  bounced between `creative`/`personal`/`coding`. **This is not merely a structural risk — a real,
  concrete instance of its causal effect was found**: a real self-edit cycle at
  `2026-09-03T21:38:26` targeted `'personal'` — the *only* deviation from `'coding'` anywhere in the
  session's sampled `SELF_EDIT.log` — correlating exactly with `shadow_self_model.json`'s
  contemporaneous `'personal'` proposal.
- **I (Verification→Learning)**: two mechanisms, one alive, one wired-but-dead.
  `RiverBrain.learn()`'s direct quality-score path is real and live (Finding 39's tag-boost
  empirically confirmed working: `qwen2.5-coder:7b` now leads real coding-task mean among
  well-sampled models). `learn_from_council_rating()` is **structurally real, correctly gated
  (`is_council_trusted()` confirmed `True` live), and genuinely called from
  `council_rater.rate_one_entry()`** — but functionally dead: `memory/council_cursor.json` reads
  `{"position": 33471, ...}` while `memory/interaction_log.jsonl` currently holds only **11,671**
  lines. Python's `list[33471:]` on an 11,671-item list silently returns `[]` every time — no new
  rating has been sampled since approximately 2026-07-26, over a month of otherwise-continuous
  production activity, confirmed by `council_ratings.jsonl`'s own 133-line, late-July-dated tail. This
  precisely corrects and sharpens the prior capability-ceiling map's vaguer "confirmed dead" claim.
- **J (Learning→Model Selection)**: real, live, measured — see `model_orchestration_council` and
  `adaptation_routing_level` in the prior capability-ceiling map, re-confirmed this session via the
  same live `river_brain.pkl` unpickle.
- **K (Learning→Content Generation)**: no evidence found, in this pass or prior work, of any
  mechanism that changes response *content* from accumulated experience without either (1) re-inserting
  the original experience via retrieval, (2) a routing change, or (3) C1's human-confirmed persistent
  state. This remains the same conclusion as the prior capability-ceiling map, re-verified rather than
  merely repeated.
- **L (Failure→Adjustment)**: real for self-edit (`self_edit_convergence.json`'s
  `non_convergent_streak` schema exists and has historically retired two prompt families), but **all 4
  current families read `non_convergent_streak: 0` right now**, despite a live log tail full of recent
  real failures — this investigation could not fully resolve whether the streak-reset condition is
  simply working as designed (any candidate reaching `dry_run_staged` resets it) or is quietly inert
  in current practice; flagged as ambiguous, not concluded. **Absent entirely for `echo_projects`** —
  no comparable mechanism exists there at all.

## Existing Closed Loops

1. **Self-edit outcome → reflection → self-model target → [shadow override] → next targeting** —
   **CLOSED AND CAUSALLY VERIFIED, BUT DEGRADED.** Every edge confirmed real; the final decision is
   dominated by the low-information heuristic rather than the well-evidenced signal, demonstrated with
   a real, concrete instance this session.
2. **Interaction → council deliberation → quality_score → RiverBrain.learn() → model selection** —
   **CLOSED AND CAUSALLY VERIFIED.** Routing-level only, per Hard Rule 6 — never called "learning"
   here.
3. **C1: human-confirmed directive → persistent state → deterministic exposure → model compliance** —
   **CLOSED AND CAUSALLY VERIFIED (architecture, 100%) / EXPERIMENTALLY DEMONSTRATED, SMALL-N
   (compliance, 75% at n=4).**

## Hollow Loops

1. **Council rating → RiverBrain blended training** — **APPARENTLY CLOSED BUT CONTAINS A HOLLOW
   EDGE.** Every component is real and correctly gated; the loop produces zero real effect today
   because of a stale read cursor at the very first step.
2. **Curiosity → question → echo_projects plan → execution → verification** — **PARTIALLY CLOSED.**
   Real all the way through verification (0/61 success is a real, measured verdict, not a missing
   step), but there is no edge back from that verdict to the next cycle's question/plan/generation —
   each of the 61 cycles is causally independent of every other.
3. **ToolManager: registration → discovery → listing → invocation** — **DOES NOT EXIST** past
   listing. Traced beyond a simple grep per this mission's Part IX instruction: both instantiation
   sites read in full, the registration decorator confirmed to feed discovery only, zero Flask routes,
   council/river dispatch, or background loop found calling `get_tool()`.
4. **Memory retrieval → generation (personal task)** — **CLOSED BUT BEHAVIORAL EFFECT UNVERIFIED.**
   Real write, real read, real context injection; Finding 76's real ablation could not distinguish its
   effect from sampling noise. Genuinely open, not a hidden negative.
5. **Self-edit: F1/F2/F3 → fitness gate → deploy** — **CLOSED, SAFETY VERIFIED, QUALITY-IMPROVEMENT
   CLAIM UNSUPPORTED.** 426/463 (92%) real deploy success (2026-09-03 self-modification evidence
   index) is real, but the fitness metric (raw AST node count) is confirmed saturated at a perfect 4/4
   for all 25 currently-retained deploys — "passed the gate" and "quality genuinely improved" are
   conflated in the 92% headline.

## Minimum-Cut Analysis

Ranked by capability leverage × evidence strength × implementation simplicity × safety (full detail
and per-factor breakdown in the JSON's `minimum_cut_ranking`):

1. **`council_cursor.json`'s stale cursor** (33,471 vs. 11,671 real lines) — unlocks an entire
   already-trusted training pathway, dormant since ~2026-07-26, with a trivial, zero-safety-risk fix.
2. **`shadow_self_model.json`'s override priority** over the RiverBrain-performance-derived signal —
   reconnects an already-closed, already-verified loop to its best available signal.
3. **`trace_id`'s partial coverage** (missing from `workspace_log.jsonl`/`self_edit_outcome_tracker.py`/
   `memory_bridge.py`) — extends an already-built, already-verified mechanism at low cost.
4. **`ToolManager.get_tool()`'s total absence of invocation call sites** — high theoretical leverage,
   but genuinely uncertain practical benefit and the only candidate on this list that requires new
   safety consideration rather than a pure connectivity fix.
5. **`echo_projects`' missing failure→adjustment edge** — real leverage, but the underlying 0%
   success rate may reflect a genuine model-capability ceiling rather than a pure connectivity gap, so
   a fix here is speculative in a way the top three are not.

## Highest-Leverage Intervention

**Fix `council_cursor.json`'s stale-cursor deadlock in `council_rater.py`.** This is the single
highest-leverage, lowest-risk, most surgical repair identified: it requires no new mechanism, touches
no verification gate or safety boundary, and directly restores an entire, already-designed,
already-trusted (`is_council_trusted()` confirmed `True` live) training pathway that has been silently
producing zero effect for over a month due to nothing more than a read cursor left behind by an
interaction-log rotation event. Every other piece of the mechanism — the trust gate, the blend math
(`_blend_council_and_quality`, per prior CLAUDE.md Finding 67), the call site — was independently
re-verified this session and found genuinely intact. This is the clearest possible example this
investigation found of "insufficient connection" rather than "missing capability": the capability
(peer-rating-informed training) was fully built and is fully ready; it is simply not being fed any
input.

## Top 3 Interventions

1. **Fix `council_cursor.json`'s stale cursor** — leverage: high; evidence: high (exact numbers
   measured); cost: very low (5-15 LOC); safety: very high (no gate touched); reversibility: trivial.
2. **Rebalance `perform_self_edit()`'s target-selection priority** so `self_model.json`'s
   RiverBrain-derived signal is not unconditionally demoted beneath `shadow_self_model.json`'s
   keyword heuristic — leverage: high (reconnects a real, already-closed loop to its best signal);
   evidence: high (a concrete causal instance was directly observed); cost: low (5-20 LOC); safety:
   high (changes targeting, not safety gating); reversibility: trivial.
3. **Extend `trace_id` propagation to `workspace_log.jsonl`, `self_edit_outcome_tracker.py`, and
   `memory_bridge.py`** — leverage: medium (completes an already-proven pattern for the
   autonomous-loop/self-edit side of the system); evidence: high (absence directly confirmed);
   cost: medium (an additive-parameter exercise across a few more call sites); safety: very high
   (pure logging, no behavior change).

## Minimum Viable Closed Loop

The mission's own suggested shape (curiosity → goal → plan → execution → verification → outcome →
reflection → metacognition → routing/behavior adjustment → next attempt → verification → measurable
change) was tested directly against its most plausible existing substrate, `echo_projects`. **It is
not the best candidate**: no goal-persistence structure, no failure→adjustment edge, and a 0/61
historical success rate. **The self-edit loop, not explicitly named in the mission's suggested shape,
was found during this investigation to already satisfy nearly every requirement of that shape**, with
one identified, small, surgical defect. Proposed minimum viable closed loop:

> Self-edit outcome → structured reflection → self-model target (RiverBrain-derived) →
> [priority-fixed] self-edit targeting → next attempt → F1/F2/F3/fitness gate → outcome → verify
> improvement.

Two surgical changes, both fixes to existing wiring, neither a new mechanism:

| # | Change | Files | Approx. LOC | Risk | Rollback | Edge closed | Experiment required |
|---|---|---|---|---|---|---|---|
| 1 | Fix stale cursor | `app/core/council_rater.py` | 5-15 | very low | trivial (small JSON file) | council rating → RiverBrain training | confirm `council_ratings.jsonl` resumes growing; confirm a real rating produces a measurable `model_task_stats` change, mirroring Finding 44's own before/after method |
| 2 | Rebalance target-selection priority | `app/core/self_edit_manager.py` | 5-20 | low | trivial (priority-order change) | self-model target → actual targeting decision | controlled before/after comparison of real target selections against `self_model.json`'s own target over a comparable window, confirming agreement rate rises |

**Total: 2 surgical changes.** Consistent with the mission's stated preference for 1-3 changes over a
rewrite, and with Hard Rule 12 (prefer existing mechanisms over new ones) — both changes repair
already-built machinery.

## Required Experiments

Before either proposed change (or any other repair) can be claimed to produce genuine adaptive
behavior, rather than merely "the code now runs":

1. **Council-cursor fix validation**: post-fix, confirm `council_ratings.jsonl` resumes real growth
   within one real sampling cycle, and directly measure one real rating's effect on
   `model_task_stats` (same before/after methodology already proven in Finding 44).
2. **Shadow-override priority fix validation**: a controlled window (e.g., 48h) comparing real
   `perform_self_edit()` target selections against `self_model.json`'s own target before and after the
   change, measuring agreement rate — pre-registered, restart-tested (confirm the new priority
   survives a real server restart), control-tested (confirm the shadow signal still applies when it
   *agrees* with the real signal, so the fix doesn't silently disable the shadow mechanism entirely).
3. **Memory-retrieval causal-effect replication** (carried forward from the prior capability-ceiling
   map, re-affirmed as still the single most important open memory question): re-run Finding 76's
   ablation at **temperature=0**, across all five task types, not just `personal` — temperature=0
   removes sampling-noise confound almost entirely, directly testable and falsifiable.
4. **`self_edit_convergence.json`'s zero-streak ambiguity**: instrument (log-only, no behavior change)
   exactly which condition resets `non_convergent_streak` on each real cycle, to resolve whether the
   mechanism is genuinely working as designed or quietly inert — falsifiable against the mechanism's
   own documented reset condition.
5. **Any future ToolManager wiring** (explicitly not recommended for immediate action, given rank 4
   in the minimum-cut list): would require its own pre-registered, narrow, single-tool experiment with
   an explicit safety review, not bundled with the two surgical changes above.

All five experiments are zero-cost, reproducible from files already on disk, and resistant to
confabulation/label-following in the same way this project's own C1 validation was designed (real
subprocess/session isolation where relevant, real before/after measurement rather than self-report).

## Falsification Evidence

Reported prominently, per this mission's explicit instruction, not minimized:

- **`echo_projects`' 0/61 real historical end-to-end success rate** is direct evidence that local
  models may be too weak for reliable multi-file, cross-referencing code generation — a real ceiling,
  not merely an unconnected pipeline.
- **C1's own 75% (n=4) compliance rate**, even with a 100%-reliable architectural chain, is direct
  evidence that persistent state alone does not guarantee adaptive behavioral change — the frozen-weight
  model's own stochastic compliance is a real, separate ceiling from anything architecture can fix.
- **`reflection_shard.py`'s generative reflection reads zero verification/outcome data** — confirming
  at least one major "reflection" mechanism in this codebase is closer to stylistic free-association
  than outcome-grounded introspection, exactly the adversarial hypothesis this mission asked to be
  checked.
- **No evidence was found that RiverBrain's routing-level adaptation (tag-boost) has ever been
  measured against actual downstream outcome quality**, only against which model gets selected —
  "routing adaptation may not improve outcomes" remains live and unrefuted by this investigation.
- **The 2026-09-03 measurability audit's own finding** (cited, not re-derived) that apparent
  curiosity-category drift resolves to scheduling/persona code rather than emergent interest directly
  supports "curiosity may be scheduling rather than intrinsic inquiry."
- **`self_edit_convergence.json`'s zero streaks despite nearby real failures** is either the mechanism
  working exactly as designed, or quiet inertness — this investigation could not distinguish the two,
  which is itself evidence the mechanism's real engagement rate may be lower than its mere existence
  implies.

## Revised Capability Map

Per this mission's Hard Rule and Part XI's explicit instruction, existing scores from
`audits/echo_capability_ceiling_map.json` are **not silently rewritten** — the following are stated as
explicit corrections, with before/after and the new evidence:

| Dimension | Prior score | Revision | Reason |
|---|---|---|---|
| `learning_l2_autonomous` | 2 (hollow-dead) | **unchanged, but re-grounded**: the "hollow-dead" classification for `learn_from_council_rating()` now has a precise root cause (stale cursor, exact numbers) rather than a general "confirmed dead" citation. Score stands; confidence rises from medium-high to high. | Precision improvement, not a score change. |
| `observability_auditability` | 5 | **upward pressure noted, not applied**: the correlation-ID gap this investigation's own prior pass named as the #1 intervention has already been substantially fixed (real `trace_id`, 2026-09-02) — but coverage is still partial (workspace_log/self_edit_outcome_tracker/memory_bridge remain uncovered), so the score is left at 5 rather than raised, with the partial-fix explicitly noted. | Real, verified improvement exists but does not yet close the full gap the original score's ceiling discussion named. |
| `epistemic_calibration_honesty` | 3 | **upward pressure noted, not applied**: the specific "caveat doesn't reach interaction_log" gap this investigation's own prior pass named as intervention #3 has already been implemented and verified (2026-09-02 information-flow-integrity pass, two live reproductions). A future full re-audit of this dimension would likely raise its score; this document flags the change without re-scoring it, since this investigation did not independently re-verify the fix beyond reading its own report. | Same reasoning as above — real fix exists, not independently re-confirmed live in this pass. |
| `metacognition` | 3 (reader unconfirmed) | **resolved, upward**: this investigation directly confirmed `shadow_accuracy.jsonl`-adjacent `shadow_self_model.json` IS read, by `self_edit_manager.py`, and DOES causally affect real self-edit targeting decisions (a concrete instance observed). Score should rise to at least 4 (experimentally demonstrated) — **not applied automatically here per Hard Rule against silent rewrites; flagged for explicit adoption.** | Direct resolution of a previously-named "unconfirmed reader" gap. |
| `multi_file_generation_echo_projects` | 4 (partial, experimentally-demonstrated) | **downward pressure, explicit**: the prior score's evidence cited a real 6-file cycle and 2,535 RiverBrain observations as positive signal; this investigation's 0/61 real end-to-end success rate is a substantially harder negative than the prior pass's own "most recent cycle was f1_failed" framing. A re-scored value of 2-3 (implemented but effectively non-functional end-to-end) is more consistent with the fuller evidence now available — **flagged for explicit adoption, not applied automatically.** | Fuller, quantified evidence changes the picture materially. |
| `tool_use` | 1 (hollow-dead, "verify-before-concluding") | **resolved, confirmed**: the prior pass's own stated caveat ("2 hits found live were not individually traced") is now fully resolved — both instantiation sites were traced in full; the listing/injection half is real (upgrading the classification detail from pure "hollow" to "registration+listing real, invocation absent"), while the score of 1 for the capability this dimension is actually named for (tool USE) is confirmed correct. | Caveat closed; score confirmed, not changed. |

## Explicit Non-Claims

Everything the evidence gathered in this pass still does **not** establish (full list in the JSON's
`explicit_non_claims`, key items restated here):

- That either proposed surgical fix would produce content-level learning — both affect
  routing/targeting only.
- Whether memory retrieval causally affects behavior on any task type other than `personal`, or at
  temperature=0.
- The definitive root cause of `self_edit_convergence.json`'s currently-zero streaks despite nearby
  real failures.
- Whether wiring a real `ToolManager` invocation path would produce any net capability gain for this
  system's real task mix.
- Whether `echo_projects`' 0/61 success rate reflects a fixable gate-calibration issue or a genuine,
  currently-unmovable model-capability ceiling.
- The current, full content of the 2026-09-02 architectural self-knowledge document series beyond its
  existence and the information-flow-integrity document's own headline conclusions.
- That RiverBrain's routing-level adaptation constitutes "learning" in any content-level sense — it is
  reported strictly as routing adaptation throughout, per Hard Rule 6.
