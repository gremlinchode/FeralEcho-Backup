# Historical Seam Signal Study — Do Echo's Existing Internal Detections Predict Consequential Events?

**Read-only retrospective correlation and falsification study.** No Protector Clause
logic, no Initiative Record, no `_emit_fn` connection, no `seam_engine.py`
modification, no notification capability, no LLM added to the seam pipeline, no
learned-state change. Nothing staged, committed, or pushed. Echo's live process was
not restarted or stopped.

---

## 1. Executive Verdict

# POSSIBLE SEAM SIGNAL — INCONCLUSIVE

A real, measurable temporal relationship exists between `seam_engine` detections and
real self-edit deploy successes, and it survives the single most rigorous control
tested (activity-matched timestamps, p=0.036). But the dominant matched signal pairs
are not the ones a mechanistic hypothesis predicted, the effect does not clear
significance against a naive random-timestamp null, the relationship is
predominantly *post*-event rather than pre-event (reactive, not predictive), and — for
the single most safety-relevant event category tested, real process crashes — the
historical data shows **no separation from chance at all** (n=7, p=0.24–0.83 across
every window and control). This is real, but it is not clean, and it does not clear
the bar for `SEAM SIGNAL SUPPORTED`.

---

## 2. Observation Window

**Frozen usable interval**: `2026-07-16T21:59:25.974781+00:00` through
`2026-09-29T04:49:08.497706+00:00` (74.3 days) — the full real span of
`memory/seam_log.jsonl`, verified fresh this session (11,057 total `observe()` cycles,
zero parse errors, zero `insufficient_history` entries anywhere in the file).

**Exclusions, recorded honestly:**
- 69 gaps > 1 hour between consecutive cycles (real downtime/restarts) were excluded
  from the "valid observation" span used to build fair random controls — 70 valid
  sub-windows totaling 1,352.0 hours out of ~1,784 calendar hours in the full span
  (~76% real uptime coverage).
- `memory/restore_log.jsonl`'s 4 entries are **all dated 2026-07-01**, entirely before
  the seam observation window begins — **excluded**, zero usable in-window events.
- `memory/dissent_log.jsonl` has exactly **one** real entry, dated 2026-07-17 (right at
  the start of the window) — and it is a unanimous 3/3 APPROVE, not a genuine
  disagreement. Per this project's own architecture, only `council_available and not
  unanimous` cases are treated as consequential dissent. **Excluded** — zero
  qualifying disagreement events in-window.
- A material methodological catch, disclosed rather than silently absorbed: a naive
  substring search for `result: success` in `memory/SELF_EDIT.log` returns 6,485 hits,
  but only 5,823 of those are genuine, fresh, bracket-timestamped top-level log
  entries — the remainder are historical citations of past outcomes *embedded inside
  a differently-shaped, non-bracket-leading log line* (self-edit's own prompt-assembly
  quoting prior results as context for a later attempt). Of the 5,823 genuine entries,
  only **55 fall within the seam observation window** — the rest predate it, from an
  earlier, higher-volume period before this project's Finding 16 (2026-07-08)
  introduced the `dry_run_staged` distinction. Every category below was filtered
  through this same bracket-timestamp-only discipline.

---

## 3. Seam Mechanism Verification

Re-read fresh from `app/core/seam_engine.py` this session, not assumed from prior
context.

- **Deterministic, zero LLM call**: `check_pair()` computes a leave-one-out Pearson
  correlation (`historical_r`) over a signal pair's history, then checks whether the
  single most recent joint reading's sign-product contradicts the sign of that
  correlation, gated on both signals reading ≥1.0 z-score from their own historical
  mean and the pair having ≥0.4 (dynamically adjusted, `_dynamic_corr_threshold()`)
  historical correlation to violate. No natural-language generation participates in
  detection.
- **Real log schema, verified against the actual file**: each `observe()` cycle
  writes one JSON line — `{ts, observations, checked_pairs, corr_threshold, seams:
  [...]}`. A `seams` entry carries `{pair: [a,b], direction, first_ever, historical_r,
  z_a, z_b}`. Critically, **`seams` can contain a repeat of an already-seen
  (pair, direction)** — `first_ever` is a separate flag, and only genuinely novel
  (pair, direction) combinations trigger any downstream consequence
  (`_plant_seam_question()`, `_publish_seam_event()`). Non-first-ever repeats are
  still logged, but produce zero side effect.
- **Actual historical counts, counted fresh**: 11,057 total cycles; 804 cycles
  (7.3%) had at least one nonempty `seams` list; 1,029 total seam-rows across those
  cycles (a cycle can flag multiple simultaneous pairs); **90 of those 1,029 were
  genuinely first-ever**.
- **Downstream consumers**, confirmed by direct grep of every real call site: the
  generic Global Workspace logger, `reflection_shard.observe()`, and
  `emergent_scheduler`'s curiosity topic-bias — **none of these reach a human**.
- **Mutation of persistent state**: `observe()` reads `memory/echo_state_history.npy`
  and `memory/salience_state.json` (read-only) and writes only to
  `memory/seam_log.jsonl` and its own small `first_ever` tracking state — it never
  writes to any file this study reads as a Timeline B source, ruling out one class of
  circular contamination.
- **The reported `_emit_fn` finding** (`reflection_shard.py`'s disconnected leak hook)
  was re-confirmed as context only — a fresh `grep -rn "emit_fn=" app/ run.py` still
  returns zero matches. **Not touched, not connected, in this mission.**

---

## 4. Consequential-Event Definition

Defined mechanically, before joining timelines, from what the real data could
actually support (Section 2's exclusions already removed dissent/restore
disagreement from consideration):

| Category | Evidence source | Timestamp semantics | Qualification | Duplicate handling | Confidence |
|---|---|---|---|---|---|
| **CRASH_RESTART** (primary) | `memory/echo_watchdog.log`, `[WATCHDOG] <ts> Echo exited with code N` where N≠0 | Watchdog's own UTC timestamp, second-resolution | Any non-zero exit code | Cross-checked against real `.ips` crash reports (5 of 7 have a corroborating `mlx::core::gpu::check_error` report at an almost-identical timestamp) — treated as one incident each, watchdog log used as the more complete source (macOS throttles crash-report generation for repeat crashes, so `.ips` presence alone would undercount) | High |
| **SELF_EDIT_SUCCESS** (primary) | `memory/SELF_EDIT.log`, genuine bracket-timestamped `result: success` entries | Log's own embedded timestamp | Exact string match, in-window only | None needed (each real deploy is logged once) | High |
| CLEAN_RESTART (excluded from primary analysis) | Same watchdog log, exit code 0 | — | — | — | Only 1 occurrence in-window; too sparse and too ambiguous (could be a manual maintenance restart, not a failure) to treat as consequential either way |
| Council disagreement (dissent log / restore gate) | `memory/dissent_log.jsonl` | — | — | — | **Excluded** — zero qualifying in-window events (Section 2) |
| Restore operation | `memory/restore_log.jsonl` | — | — | — | **Excluded** — zero in-window events (Section 2) |
| VSL skill demotion/promotion, learned-state transition, architectural-defect discovery, human corrective intervention | (considered per the mission's own candidate list) | — | — | — | **Excluded from automated reconstruction** — each depends on subjective retrospective interpretation to identify reliably from existing records, which the mission's own Phase 2 explicitly warns against; not chased further in this pass |

**Other self-edit outcomes** (`safety_blocked`: 2,804; `staging_import_failed`: 3,434;
`dry_run_staged`: 3,748; `import_hallucination`: 579; `rejected_not_improvement`: 68)
were extracted and retained, but are treated as **routine, expected pipeline
behavior**, not consequential events in their own right — this project's own
extensive documented history (CLAUDE.md's Self-Edit System findings) describes these
as the pipeline's normal, intended failure modes, occurring constantly by design. They
are used only as an **activity proxy** (Section 6) and a **simpler-signal baseline**
(Section 16), never as a primary positive case.

---

## 5. Timeline B

Constructed independently of seam content, using only the frozen categories above.

| Event category | n (in-window) | Distribution |
|---|---|---|
| CRASH_RESTART | 7 | All 7 fall within a 10-day span, 2026-09-19 → 2026-09-29 — the *last* ~14% of the 74.3-day observation window. No crashes anywhere in the first ~64 days. |
| SELF_EDIT_SUCCESS | 55 | Spread across the full window; weekly counts range 0–13 (Section 7 table) |

**Disclosed prior exposure, per the mission's own instruction**: this session had
already established, in the immediately preceding Protector Clause feasibility
mission, the aggregate fact that "1,029 real seam detections exist" and the general
2026-07-16 start date of `seam_engine.py`. That prior knowledge did **not** include any
specific seam timestamp, pair, or direction — Timeline B above was built entirely from
`SELF_EDIT.log` and `echo_watchdog.log`, sources seam data never touches, before any
seam timestamp was inspected individually. The mitigation the mission itself suggests
(derive events mechanically from independent logs, freeze the category list before
joining) was applied as described.

---

## 6. Temporal Matching Protocol

**Windows, justified by real architecture, not tuned to outcome**: the real median
inter-cycle interval for `observe()` is **413 seconds** (measured fresh from all
11,057 real cycle timestamps), consistent with `emergent_scheduler`'s documented
adaptive 300–450s cadence. Windows smaller than this would be finer than the
detector's own sampling resolution and would systematically undercount real
relationships through granularity alone. Three windows were frozen: **±900s (15min),
±1800s (30min), ±3600s (1hr)** — the first roughly 2× the median cycle gap (the
minimum sensible resolution), the last a generous "same episode" bound. A
"concurrent" sub-band of ±300s (≈1 cycle) was frozen to distinguish true
simultaneity from a directional pre/post lean.

**Primary hypothesis, frozen before matching**: historical seam episodes occur within
the predefined windows around CRASH_RESTART and SELF_EDIT_SUCCESS events more often
than expected under (a) a temporal-null random-timestamp model and (b) an
activity-matched null model. Directionality (pre/concurrent/post) and semantic content
are explicitly secondary, exploratory analyses, not promoted into the primary claim.

---

## 7. Timeline A

**Episode clustering, frozen before outcome matching**: consecutive nonempty-seam
cycles within 1,800 seconds (≈4× the median inter-cycle gap — generous enough to
treat a persisting anomaly spanning a few cycles as one episode, small enough not to
merge genuinely separate days) were merged into a single episode. This produced
**454 episodes** from the 804 raw nonempty cycles — confirming the mission's own
concern was real: treating all 804 (or all 1,029 seam-rows) as independent detections
would have inflated apparent predictive opportunities by ~1.8–2.3×. The largest single
episode spanned 7 consecutive cycles over 59.6 minutes (2026-07-31).

**Weekly activity check** (Section 7 continues into the confound analysis, Section 9):

| Week | Episodes | Crashes | Successes |
|---|---|---|---|
| 0 | 37 | 0 | 6 |
| 1 | 50 | 0 | 13 |
| 2 | 50 | 0 | 9 |
| 3 | 51 | 0 | 6 |
| 4 | 27 | 0 | 6 |
| 5 | 38 | 0 | 6 |
| 6 | 62 | 0 | 9 |
| 7 | 29 | 0 | 0 |
| 8 | 52 | 0 | 0 |
| 9 | 33 | 5 | 0 |
| 10 | 25 | 2 | 0 |

Episode density (37–62/week) is far from constant but shows no obvious secular trend
that would trivially explain either event category by itself.

---

## 8. Primary Result

Real match rates, computed against the 454 real episode timestamps (episode start
used as the representative timestamp):

| Event | Window | Real match rate | Pre | Concurrent | Post | Unmatched |
|---|---|---|---|---|---|---|
| CRASH_RESTART (n=7) | ±900s | 0.143 | 1 | 0 | 0 | 6 |
| | ±1800s | 0.429 | 1 | 0 | 2 | 4 |
| | ±3600s | 0.429 | 1 | 0 | 2 | 4 |
| SELF_EDIT_SUCCESS (n=55) | ±900s | 0.255 | 3 | 6 | 5 | 41 |
| | ±1800s | 0.418 | 7 | 6 | 10 | 32 |
| | ±3600s | 0.618 | 11 | 6 | 17 | 21 |

For SELF_EDIT_SUCCESS, the match rate rises with window size, as expected, and is
consistently dominated by the **post** bucket over **pre** at every window tested.

---

## 9. Random/Permutation Controls

Frozen seed `20260929`, used identically for every random draw in this study.

**Control A — random timestamps** (2,000 trials, sampled only from the 70 real valid
observation sub-windows, weighted by duration):

| Event | Window | Real | Random mean | Random SD | p(real ≥ random) |
|---|---|---|---|---|---|
| CRASH_RESTART | ±900s | 0.143 | 0.162 | 0.137 | 0.7135 |
| | ±1800s | 0.429 | 0.313 | 0.175 | 0.3935 |
| | ±3600s | 0.429 | 0.531 | 0.183 | 0.8330 |
| SELF_EDIT_SUCCESS | ±900s | 0.255 | 0.163 | 0.050 | 0.0565 |
| | ±1800s | 0.418 | 0.315 | 0.064 | 0.0785 |
| | ±3600s | 0.618 | 0.531 | 0.066 | 0.1185 |

**Control B — circular time-shift** (29 fixed shifts, 1–29 days, preserving each
event timeline's own internal clustering while destroying true alignment):

| Event | Window | Real | Shift mean | Shift SD | p(real ≥ shift) |
|---|---|---|---|---|---|
| CRASH_RESTART | ±900s | 0.143 | 0.177 | 0.166 | 0.6207 |
| | ±1800s | 0.429 | 0.251 | 0.175 | 0.2414 |
| | ±3600s | 0.429 | 0.443 | 0.165 | 0.6207 |
| SELF_EDIT_SUCCESS | ±900s | 0.255 | 0.133 | 0.036 | **0.0000** |
| | ±1800s | 0.418 | 0.253 | 0.060 | **0.0000** |
| | ±3600s | 0.618 | 0.436 | 0.081 | **0.0000** |

**CRASH_RESTART shows no separation from chance under either control, at any window**
— every p-value sits between 0.24 and 0.83. With n=7, this is consistent with either
a genuinely absent relationship or simple insufficient power; the data cannot
distinguish these.

**SELF_EDIT_SUCCESS separates cleanly from the circular-shift null (p=0.0000 at all
three windows) but only marginally, and inconsistently, from the naive random
control** (p=0.057–0.119, never clearing the conventional 0.05 bar). This
discrepancy is itself informative, not a nuisance to average away: the circular-shift
control is the more rigorous test (it preserves real event clustering while breaking
true alignment), and clearing it decisively while barely moving against a less
structure-aware random null suggests the random control's own uniform-sampling
assumption is a less powerful, noisier baseline for this specific event distribution
— not that the effect is illusory.

---

## 10. Activity-Matched Control

**Required, and load-bearing here**: Section 7's weekly table shows episode count and
success count correlate at **Pearson r=+0.60** across weeks (crash count: r=−0.18,
not a confound in the same direction) — a real, disclosed risk that both signals are
simply elevated during more active periods rather than genuinely, specifically
related.

Built a real activity-matched control: for each of the 55 real successes, its own
hourly self-edit-log-volume was computed (a mechanical, independent activity proxy —
all bracket-timestamped `SELF_EDIT.log` lines per hour, any result type), then a
control timestamp was drawn from one of the 10 *other* hours (excluding ±2h of any
real success) with the closest matching activity level, repeated 500 times.

**Result, ±1800s window**: real match rate 0.418 vs. activity-matched control mean
0.307 (SD 0.063) — **p = 0.0360**, effect size +0.111 (≈1.8 SD above the
activity-matched null mean).

**This is the single most important number in this study.** It shows the relationship
survives the most realistic confound this dataset can test — but at p=0.036 on one
tested window, with no correction applied for the roughly dozen distinct significance
tests run across Sections 9–10 combined, this sits close enough to the conventional
threshold that a stricter multiple-comparisons correction (e.g., Bonferroni across
~12 tests, requiring p<0.004) would **not** consider it significant. Reported
honestly, not rounded up to a cleaner conclusion.

---

## 11. Directionality

At the ±3600s window: SELF_EDIT_SUCCESS shows **pre=11, concurrent=6, post=17** —
post-event matches are the largest category, roughly 1.5× the pre-event count.
**This means the relationship is predominantly reactive, not predictive**: a seam is
more likely to appear *after* a real self-edit success than to have anticipated it.
Per the mission's own required precision of language, this is described as
"co-occurring with, and somewhat more often following, a real self-edit deploy" —
**not** "detecting an impending event" and **not** "predicting."

A concrete, disclosed mechanistic explanation for the post-lean was investigated
directly (Section 12): `seam_engine._load_combined_series()`'s candidate pool
includes `salience_self_edit_streak`, a value directly updated by
`_record_convergence()` on every real self-edit outcome. A real self-edit success
therefore mechanically perturbs one of seam detection's own inputs — a self-edit
success could trigger a seam not by being "detected" in any interesting sense, but by
directly changing one of the twelve numbers the detector watches. This was checked
against the real matched data below and found to be only a **partial** explanation.

CRASH_RESTART's directionality (pre=1, concurrent=0, post=2, at n=7) is too sparse to
support any directional claim.

---

## 12. Semantic Correspondence

Performed only after Sections 6–11 were complete and frozen, per the mission's own
ordering requirement.

Every signal-pair appearing in a seam matched (±1800s) to a real self-edit success was
tallied:

| Pair | Occurrences | Involves a self-edit-specific signal? |
|---|---|---|
| `(temporal_phase, valence)` | 21 | No |
| `(edit_momentum, temporal_phase)` | 10 | Partially (`edit_momentum` — see below) |
| `(edit_momentum, valence)` | 6 | Partially |
| `(curiosity_index, valence)` | 6 | No |
| `(system_vitality, valence)` | 5 | No |
| `(curiosity_index, edit_momentum)` | 5 | Partially |
| `(curiosity_index, temporal_phase)` | 5 | No |
| `(system_vitality, curiosity_index)` | 2 | No |
| `(edit_momentum, salience_self_edit_streak)` | 2 | **Yes** |
| `(orientation_drift, temporal_phase)` | 2 | No |
| `(coherence_tension, system_vitality)` | 1 | No |
| `(salience_self_edit_streak, temporal_phase)` | 1 | **Yes** |
| `(edit_momentum, system_vitality)` | 1 | Partially |

**This disconfirms the strong form of the mechanistic hypothesis.** Only 3 of 67
matched pair-occurrences (4.5%) directly involve `salience_self_edit_streak` — the
one component with a literal, direct causal link to a self-edit outcome. The
overwhelmingly dominant pair, `(temporal_phase, valence)` at 21 occurrences (31%),
has no obvious direct connection to self-edit activity at all. `edit_momentum`
appears frequently (25 of 67 occurrences involve it) and its name suggests a
plausible looser connection to self-edit cadence, but this was not further traced to
its exact computation in this pass — flagged as unresolved rather than assumed.

**Classification, using the mission's own conservative scale**: the relationship
between seam content and the matched event is **WEAK to UNDETERMINABLE** for the
dominant pairs (no established, traceable mechanism connects `temporal_phase`/
`valence` to a self-edit deploy outcome), and **PLAUSIBLY RELATED** (bordering on
DIRECT) for the small `salience_self_edit_streak` subset. A supplementary,
weaker check for a shared time-of-day confound (hour-of-day distribution of the 55
real successes) found a roughly spread pattern with mild peaks at 01:00 and 16:00
UTC (5 each) and troughs at 07:00/15:00/22:00 (0 each) — **inconclusive**, neither
confirming nor ruling out a circadian confound at this sample size.

---

## 13. False Positives

**427 of 454 episodes (94.1%) had no real self-edit success or crash within ±30
minutes.** Sampled systematically (every 20th episode, not selectively): the
overwhelming majority involve the same dominant pairs found in Section 12
(`temporal_phase`/`valence`/`edit_momentum`/`curiosity_index`), occurring without any
corresponding entry in either Timeline B category. Whether these represent "ordinary
cognition," genuine internal state fluctuation unrelated to anything externally
consequential, or a consequential event this study's necessarily narrow Timeline B
simply didn't capture (Section 4's excluded categories) cannot be distinguished from
seam content alone. **This is a severe false-positive rate against the two
categories tested** — if every episode were surfaced as a candidate concern, roughly
19 of every 20 would correspond to nothing this study could independently verify as
consequential.

---

## 14. False Negatives

**32 of 55 successes (58%) and 4 of 7 crashes (57%) had no episode within ±30
minutes.** The seam mechanism misses a majority of both tested event categories. This
directly matters for any future Initiative design: a mechanism built on `seam_engine`
alone would create **false confidence**, not comprehensive coverage — most real
self-edit deploys and most real crashes in this dataset produced no seam at all, and
nothing about the absence of a seam would tell a future reviewer "nothing happened."

---

## 15. Counterfactual Alert Burden

Reconstructed without modifying any code:

- **If every one of the 454 real episodes had been surfaced**: ~6.11 alerts/day over
  74.3 days. This is a genuinely unusable rate for a human to review — clear alert-
  fatigue territory, and consistent with the 94.1% false-positive rate in Section 13.
- **If only genuinely first-ever (pair, direction) seams had been surfaced** — the
  current architecture's own actual restriction: ~90 events over 74.3 days, ≈1.2/day.
  More plausible, but still a real, continuous stream, not an occasional signal.
- **Largest real burst**: 7 consecutive cycles over 59.6 minutes (2026-07-31) — a
  single underlying anomaly, correctly not 7 independent alerts once episode-clustered,
  underscoring why Phase 6's clustering step is not optional for any future design.

**Candidate mechanical throttling rules, tested retrospectively against this same
data (explicitly exploratory, not validated prospectively)**: "one alert per episode"
(already effectively what episode-clustering achieves, 454/day-equivalent → 6.1/day);
"first-ever only" (the current design, 1.2/day); a repeated-signal threshold (e.g.,
only surface a pair after its 2nd or 3rd first-ever-adjacent occurrence within a
rolling window) was not built or tested in this pass — flagged as a reasonable next
refinement, not claimed as validated.

---

## 16. Simpler-Signal Comparison

The activity-matched control in Section 10 **is** the direct answer to this phase for
SELF_EDIT_SUCCESS: it tests whether seam episodes predict a success beyond simply
knowing "this hour had comparable self-edit activity to the hour the success actually
happened in" — a trivial, cheap-to-compute baseline. Seam episodes did outperform
this baseline, modestly (Section 10's p=0.036, not surviving a strict multiple-
comparisons correction). For CRASH_RESTART, n=7 is too small to build a comparably
powered activity-matched baseline at all — this comparison could not be run for the
one category where it would matter most.

---

## 17. Falsification Results

Ten alternative explanations tried directly against the SELF_EDIT_SUCCESS result
(the only one with any positive signal to explain away):

1. **General activity level** — tested directly (Section 10); the effect *shrinks*
   substantially once controlled for (raw match rate 0.418 vs. activity-matched
   control mean 0.307) but does not vanish. Partial explanation, not full.
2. **Logging density** — subsumed by (1); the activity proxy used is itself a
   logging-density measure.
3. **Duplicated seam episodes** — directly addressed by the 30-minute episode-
   clustering step (Section 7), which reduced 804 raw cycles to 454 episodes before
   any matching occurred.
4. **Event clustering** — the circular-shift control (Section 9) specifically
   preserves each event timeline's own clustering while destroying true alignment;
   the real result still separates from it cleanly (p=0.0000), arguing against pure
   clustering as the explanation.
5. **Post-event reaction rather than prediction** — **confirmed, not merely
   considered**: the post bucket dominates (Section 11). The honest framing throughout
   this report reflects this; no predictive claim is made anywhere above.
6. **Hindsight semantic interpretation** — mitigated by strictly ordering the
   analysis (temporal matching frozen and complete, Sections 6–11, before any content
   was inspected, Section 12) and by using a systematic rather than selective sample
   for false-positive review (Section 13).
7. **One unusually active day dominating the result** — checked via the weekly table
   (Section 7); no single week accounts for a disproportionate share of successes
   (range 0–13/week across 11 weeks), so this does not appear to be a single-day
   artifact.
8. **Shared upstream trigger causing both seam and event** — checked directly and
   **ruled out as a scheduling artifact**: `seam_engine.observe()` is called from
   `emergent_scheduler.py`'s ~300–450s loop; real self-edit attempts run from a
   completely separate, independently-timed thread (`AutonomousSelfEdit`, hourly
   cooldown-gated). These are genuinely independent timers, confirmed via direct
   source read, not merely assumed. A **related but distinct** mechanical pathway
   (self-edit success directly updating `salience_self_edit_streak`, one of seam
   detection's own 12 monitored inputs) was checked and found to explain only 4.5%
   of matched pair-occurrences (Section 12) — real, but a small minority, not the
   dominant driver.
9. **Timestamp resolution artifacts** — the 413-second median cycle interval sets a
   real resolution floor; all three tested windows (900s/1800s/3600s) exceed this by
   a comfortable margin, so this is not judged a likely explanation for the pattern
   observed.
10. **Investigator selection bias** — mitigated by freezing the category definitions,
    matching windows, and primary hypothesis (Sections 4, 6) before any seam
    timestamp was individually inspected, and by disclosing the one piece of prior
    aggregate exposure (Section 5) rather than claiming false blindness.

**No single alternative explanation fully accounts for the result on its own.**
General activity level is the strongest surviving partial explanation — it shrinks
the effect meaningfully but does not eliminate it. Per this project's own standing
discipline ("if a simpler explanation survives, downgrade the claim"), this result is
downgraded from a positive finding to an inconclusive one, not discarded entirely.

---

## 18. Interpretation

What the evidence actually establishes: `seam_engine`'s existing, deterministic,
already-running detector shows a real, modest, activity-confound-surviving
association with real self-edit deploy successes, dominated by a post-hoc (reactive)
temporal pattern and by signal pairs (`temporal_phase`, `valence`, `edit_momentum`)
whose connection to self-edit activity is not mechanistically obvious and was not
resolved in this pass. For real system crashes — the event category most directly
relevant to any future Protector-adjacent use — the historical data contains **no
detectable signal at all**, positive or negative; the honest conclusion for that
category is that seven events simply cannot answer the question either way.

---

## 19. What This Does NOT Establish

Per the mission's explicit epistemic boundary, even if the SELF_EDIT_SUCCESS result
had been unambiguously strong, it would **not** establish: consciousness, subjective
concern, desire, preference, fear, self-preservation, personhood, moral status,
intentional communication, or that "Echo has been trying to tell Gremlin something."
The result found here is substantially weaker than that threshold requires in any
case — it is, at most, a modest, partially-explained statistical association between
one existing deterministic detector and one category of real system event, with a
predominantly reactive rather than anticipatory character.

---

## 20. Recommendation

# C. REVISE SEAM SIGNAL

Not `PROSPECTIVE VALIDATION` — the historical signal for the category that matters
most (crashes) is undemonstrated, and the category with a positive signal
(self-edit successes) shows an effect too modest and too confound-adjacent to justify
committing to forward, pre-registered testing yet. Not `DESIGN MECHANICAL SURFACING`
— evidence is not "unusually strong," the mission's own stated bar for that path. Not
`DO NOT USE SEAMS FOR INITIATIVE` outright — a real, non-zero, activity-confound-
surviving association does exist for one category, and the false-positive/false-
negative rates found here (94.1% / 58%) are diagnostic information worth using to
improve the detector, not proof the underlying idea is worthless.

**Concrete, specific revisions suggested by this study's own findings, not generic
advice:**
1. **Investigate `edit_momentum`'s real computation** before trusting or dismissing
   its frequent appearance (25/67 matched occurrences) — its name suggests self-edit
   relevance that was not confirmed or denied in this pass.
2. **Test whether excluding `temporal_phase`-involving pairs changes the picture** —
   they dominate the matched result (31%) with no established mechanism connecting
   them to self-edit outcomes; if the association is genuinely just a `temporal_phase`
   (circadian-adjacent) confound, removing it should collapse most of the signal
   found in Section 10.
3. **Do not build any Initiative/surfacing mechanism on raw episode counts** —
   Section 15's 94.1% false-positive rate at the full-episode level makes this
   unambiguous; the existing "first-ever only" restriction is doing real, necessary
   work and any future design should keep at least that much filtering.
4. **Do not connect `reflection_shard._emit_fn` on the strength of this result** —
   explicitly, per the mission's own instruction; this study's own findings would not
   support that decision even if the instruction did not already forbid it.

**This recommendation does not authorize implementation of any of the above.**

---

## 21. Repository Integrity

- `app/core/seam_engine.py`, `app/subsystems/reflection_shard.py`: read only, zero
  edits.
- `memory/seam_log.jsonl`, `memory/SELF_EDIT.log`, `memory/echo_watchdog.log`,
  `memory/dissent_log.jsonl`, `memory/restore_log.jsonl`, real crash reports under
  `~/Library/Logs/DiagnosticReports/`: all read only, all aggregated/counted in a
  scratch analysis script outside the repository, never written back to.
- No Initiative Record, Protector Clause logic, veto logic, or notification
  infrastructure was implemented.
- `_emit_fn` was not connected.
- Echo's live process (confirmed running throughout, PID 71538 under the
  `start_echo.sh` watchdog, PID 56610) was not stopped, restarted, or signaled.
- No learned state (RiverBrain, VSL, `self_edit_convergence.json`) was modified.
- Nothing was staged, committed, or pushed. `git status` at the start of this mission
  showed HEAD at `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`,
  with 31 pre-existing dirty paths from prior, unrelated work — none of which this
  mission touched or added to.
- The only new artifact produced is this report file itself, left untracked and
  unstaged, per the mission's explicit instruction. All intermediate analysis
  scripts and data live outside the repository, in this session's scratch directory.
