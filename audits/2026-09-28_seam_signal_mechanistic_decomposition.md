# Seam Signal Mechanistic Decomposition — `edit_momentum` + `temporal_phase` Ablation

**Read-only mechanistic follow-up and falsification study.** No implementation, no
`_emit_fn` connection, no `seam_engine.py` modification, no learned-state change,
no restart. Nothing staged, committed, or pushed. This mission's frozen ablation
rule, controls, seed, and windows are reused verbatim from
`audits/2026-09-28_historical_seam_signal_study.md` — read in full before this
mission began, not redesigned.

---

## 1. Executive Verdict

# SIGNAL EXPLAINED BY TEMPORAL_PHASE / ACTIVITY

The prior study's association substantially collapses under a frozen,
pre-registered `temporal_phase` ablation: real match rate against self-edit
successes falls from **0.418 → 0.127** and the activity-matched control's
significance falls from **p=0.036 → p=0.132** (no longer significant). The specific
`edit_momentum` hypothesis is **decisively disconfirmed**: once isolated from
`temporal_phase` co-occurrence, `edit_momentum`-involving episodes show **zero**
matches to either self-edit successes (0/55) or crashes (0/7). The already-weak
crash association collapses completely (3/7 → 0/7). What tiny residual survives
(7/55 successes, no crashes) is carried by a different, unexamined trio
(`valence`/`curiosity_index`/`system_vitality`) too thin (n=7) to support any
further claim.

---

## 2. `edit_momentum` Lifecycle

Traced through real control flow, not inferred from the variable's name.

- **Creation / definition**: `app/core/echo_state.py`, dimension index 6 of the
  9-dimension `echo_state` vector. The file's own header documents it plainly:
  `[6] edit_momentum — self-edit success rate (0-1)`.
- **Exact computation** (`echo_state.py:213`): `vec[6] = min(float(se.get("success_rate", 0.0)), 1.0)`,
  where `se = introspection_state.get("self_edit", {})` (`echo_state.py:167`) — i.e.
  `edit_momentum` **is, by direct assignment, `introspection_channel.py`'s
  `_collect_self_edit()`'s `success_rate` field.** It is not a separate, independently
  computed signal that happens to correlate with self-edit outcomes; it is a
  relabeling of the self-edit success rate itself.
- **`success_rate`'s own computation** (`introspection_channel.py:463-584`,
  `_collect_self_edit()`): tails the most recent **500 lines** of
  `memory/reflection_shard.jsonl`, filters to non-dry-run entries carrying real
  `generated_code`, and computes `edit_success / edit_total` over that window
  (`success_rate = round(edit_success / edit_total, 4)`). A separate,
  correctly-isolated `dry_run_success_rate` covers Optuna's exploratory trials and
  does **not** feed `edit_momentum`.
- **Timing**: recomputed every **120 seconds** (`IntrospectionChannel`'s own cycle,
  per `echo_state.py`'s file header), independent of `seam_engine`'s own separate
  ~300–450s cadence.
- **Persistence**: written into `memory/echo_state.npy` / `echo_state_history.npy`
  (the ring buffer `seam_engine._load_combined_series()` reads) every 120s cycle —
  not event-triggered on a fresh self-edit outcome landing.
- **Reset/decay**: no explicit reset; it decays naturally as old entries fall out of
  the 500-line tail window as new ones are appended.
- **Real, measured window duration**: checked live this session, not assumed —
  the current 500-line tail of `reflection_shard.jsonl` spans only **~10 hours**
  (2026-09-28T19:05 → 2026-09-29T05:00), far shorter than a naive estimate based on
  average historical volume would suggest. This window's real duration is
  **non-stationary across the 74.3-day observation period** — it necessarily
  shortens as the self-edit pipeline's overall write volume to
  `reflection_shard.jsonl` grows, and lengthens during quieter stretches. This means
  `edit_momentum`'s effective "memory length" was not constant across the study
  period — a real, disclosed limitation on any single fixed-window interpretation
  of it.
- **Consumers**: `seam_engine.py`'s `_load_combined_series()` (via
  `echo_state_history.npy`) and `emergent_scheduler.py`'s existing prompt-weighting
  (unrelated to this study).
- **Feedback**: seam detection itself cannot influence `edit_momentum` — `observe()`
  is confirmed read-only against `echo_state_history.npy`/`salience_state.json`
  (re-verified in the prior study, Section 3).
- **Self-edit relationship, checked against every listed candidate**: a
  **successful deployment** directly increments the numerator and denominator of
  the rolling ratio (confirmed, the exact mechanism above). A **generation attempt,
  F1/F2/F3 rejection, or `rejected_not_improvement`** also enters the denominator
  (any non-dry-run entry with `generated_code`) without incrementing the numerator —
  meaning `edit_momentum` moves on *every* real terminal self-edit outcome, not
  only successes, pulling the ratio down on a failure and up on a success. A
  **rollback** is not a distinct logged category feeding this specifically (no
  separate rollback-result value was found in `reflection_shard.jsonl`'s real
  `result` field distribution: `pending`, `failed`, `success_dry_run`,
  `rejected_not_improvement`, `success`).
- **A real, disclosed peculiarity found but not chased further** (out of this
  mission's scope): `pending` accounts for 2,710 of the current 500-line window's
  real entries — more than every other result type combined. Whether `pending`
  entries carry `generated_code` (and therefore silently dilute `edit_total`'s
  denominator toward entries with no resolved outcome at all) was not traced to a
  definitive answer in this pass; flagged as a real open question about
  `edit_momentum`'s own data quality, separate from this mission's actual ablation
  question.

---

## 3. Operational Meaning

Stated without metaphor: **`edit_momentum` is not a signal about Echo's self-edit
*trajectory* in any richer sense than a plain, sliding-window success percentage.**
It does not encode direction, acceleration, or a qualitative sense of "gaining
momentum" — it is the literal fraction of recent real self-edit attempts (of any
kind — generation, staging, safety, fitness-gate outcomes) that ended in
`result: success`, over whatever the most recent 500 `reflection_shard.jsonl` lines
happen to span in wall-clock time at any given moment. The name suggests something
richer than the mechanism delivers; this is worth stating plainly rather than
letting the name imply more than the code does.

**Causal diagram:**

```
self-edit attempt (any outcome) → reflection_shard.jsonl entry (within ~0-few sec)
    → IntrospectionChannel's 120s cycle re-tails last 500 lines
    → _collect_self_edit()["success_rate"] recomputed
    → echo_state.py vec[6] = success_rate  (edit_momentum)
    → written to echo_state.npy / echo_state_history.npy (same 120s cycle)
    → seam_engine.observe() (its own separate ~300-450s cycle) reads the updated
      history via _load_combined_series()
    → check_pair() may flag a contradiction if edit_momentum's z-score crosses
      threshold against one of its established-correlation partners
    → logged to seam_log.jsonl; if first-ever, plants a garden question + publishes
      a Global Workspace event (never reaching a human)
```

---

## 4. Circularity Analysis

**Confirmed directly and unambiguously: yes.** A self-edit success is not merely
*correlated with* `edit_momentum` — it is, by the exact assignment in Section 2,
one of the direct numerator-and-denominator-incrementing inputs to the very
quantity `edit_momentum` reports. This is the most direct possible relationship
this study checked, more direct even than the previously-investigated
`salience_self_edit_streak` pathway (which reads from a separate file,
`self_edit_convergence.json`, one further step removed).

This means a seam involving `edit_momentum` co-occurring with a real self-edit
success is not independent evidence of anything — it is, in a substantial fraction
of cases, the detector registering a contradiction created by the very event it
appears to be "co-occurring with." **This is reactive instrumentation, not
independent prediction, by construction, not merely by suspicion.**

**Delay quantified**: the real architecture imposes two independent polling delays
in series — up to 120s (IntrospectionChannel) before a fresh outcome reaches
`edit_momentum`'s own value, then up to ~450s (emergent_scheduler's own cadence)
before `seam_engine.observe()` next reads the updated history. This bounds the
expected delay between a real self-edit outcome and the earliest possible
`edit_momentum`-involving seam detection to roughly 0–570 seconds — comfortably
inside this study's smallest tested window (±900s), confirming the prior study's
window choices were not too coarse to have caught this specific pathway had it
dominated.

---

## 5. Shared-Cause Analysis

| Candidate cause | Affects `edit_momentum`? | Affects self-edit success probability? | Evidence |
|---|---:|---:|---|
| A real self-edit deploy succeeding | **Yes — directly, definitionally** (Section 4) | Yes — it *is* the event | `echo_state.py:213` |
| `emergent_scheduler`'s own loop cadence | Indirectly (drives the 120s→570s polling chain) | No — self-edit runs on a fully separate, independently-timed thread (`AutonomousSelfEdit`, confirmed in the prior study, Section 17 item 8) | `run.py:1367-1390` |
| Wall-clock time of day | **Yes, for `temporal_phase` specifically** — `temporal_phase` is a pure deterministic function of local time (`sin` of hour-of-day), unrelated to any subsystem's activity | Not established in this study; hour-of-day distribution of real successes was checked in the prior study and found inconclusive (mild peaks, no dominant cluster) | `echo_state.py:218-221` |
| Self-edit pipeline's own overall write volume to `reflection_shard.jsonl` | Yes — sets `edit_momentum`'s real effective window length (Section 2) | Not directly — volume of *attempts* is a different quantity from *success rate* | Direct measurement, Section 2 |
| RiverBrain / model routing | Not checked — out of this mission's scope | Plausibly (established architecture: `choose_model()` reads `model_task_stats`) | Not traced further here |

**No shared upstream cause was found that independently drives both `edit_momentum`
and a self-edit success** — the relationship is direct (Section 4), not mediated by
a third factor for `edit_momentum` specifically. `temporal_phase`, by contrast, is
provably *not* caused by self-edit activity at all (it is a pure clock function) —
which makes its dominant share of the original matched result (Section 8 below)
the more genuinely puzzling half of the original finding, not a resolved one.

---

## 6. Frozen Ablation Protocol

Stated in full before any result below was computed, per the mission's own
requirement:

- **Exclusion rule**: an episode (from the prior study's already-frozen 454-episode,
  30-minute-gap clustering — reused verbatim, not recomputed) is removed from the
  "ablated" set if **any** seam in **any** of its constituent cycles has
  `temporal_phase` as one of its two `pair` members. Episode-level, not
  seam-row-level — a partially-temporal_phase episode is dropped in full, not
  partially credited. No re-clustering of surviving seam-rows was performed.
- **Matching windows**: identical ±900s/±1800s/±3600s, identical ±300s concurrent
  band, reused verbatim from the prior study.
- **Activity-matched control**: identical methodology (10-closest-activity-hour
  sampling, excluding ±2h of any real success, 500 trials), identical frozen seed
  `20260929`.
- **Primary statistic**: match rate at ±1800s against the activity-matched control,
  the same window/control pair the prior study identified as its single most
  important number.
- **Edit-momentum decomposition**: performed only on the *already-ablated* residual
  set (Group A = residual episodes involving `edit_momentum`; Group B = residual
  episodes not involving it) — explicitly labeled exploratory, since the prior
  report did not pre-register this specific two-way split before this mission.

None of the above was altered after seeing a result.

---

## 7. `temporal_phase` Ablation — Original vs. Ablated

| Metric | Original (454 episodes) | Ablated (110 episodes) |
|---|---|---|
| Episodes removed | — | 344 (75.8% of all episodes involve `temporal_phase`) |
| Match rate, successes, ±1800s | 0.418 (23/55) | **0.127 (7/55)** |
| Match rate, crashes, ±1800s | 0.429 (3/7) | **0.000 (0/7)** |
| Activity-matched control (successes, ±1800s) | mean=0.307, **p=0.0360** | mean=0.078, **p=0.1320** |
| Effect size vs. activity-matched control | +0.111 | +0.049 |

**The association collapses on every measure tested.** The one result that had
cleared conventional significance (p=0.036) no longer does (p=0.132) once
`temporal_phase`-involving episodes are removed. The crash association — already
the weaker, non-significant half of the original study — disappears entirely (every
one of the original 3 crash matches involved a `temporal_phase` pairing).

---

## 8. `edit_momentum` Decomposition (of the Residual, Ablated Set)

Exploratory, not pre-registered in the prior report — labeled as such.

| Group | n episodes | Matched to successes (±1800s) | Matched to crashes (±1800s) |
|---|---|---|---|
| **Group A** — `edit_momentum` involved (temporal_phase already excluded) | 20 | **0/55 (0.000)** | **0/7 (0.000)** |
| **Group B** — neither `edit_momentum` nor `temporal_phase` | 90 | 7/55 (0.127) | 0/7 (0.000) |

**This directly and cleanly disconfirms H1 (meaningful `edit_momentum` signal).**
Once isolated from `temporal_phase` co-occurrence, `edit_momentum`-involving
episodes carry **zero** measurable association with either tested event category —
the entirety of the residual signal that survives ablation comes from episodes that
don't involve `edit_momentum` at all.

**A further check, run for completeness, sharpens this**: of the 72 raw
`edit_momentum`-involving episodes (before any ablation), only 20 (28%) don't also
involve `temporal_phase`; the other 52 (72%) do. The raw, unablated
`edit_momentum` group's own match rate (7/55, 0.127 at ±1800s) is numerically
identical to Group B's residual rate — strong circumstantial evidence that
essentially **all** of `edit_momentum`'s apparent original association was
carried by its `temporal_phase`-paired subset, not by `edit_momentum` itself. This
is a genuinely counterintuitive finding worth stating plainly: `edit_momentum`,
despite being *definitionally* the more direct, mechanistically-justified
signal (Section 4), carried *less* of the real association than the
mechanistically-unexplained `temporal_phase`.

The residual 7 matched episodes (Group B) were traced to their real content: all
involve some combination of `system_vitality`, `curiosity_index`, and `valence` —
a different, unexamined trio, with n=7 far too thin to support any further
statistical claim (the same order of magnitude as the crash category already
judged data-insufficient in the prior study).

---

## 9. Directionality

At ±3600s, comparing the two decomposed groups directly against successes:

- **Group A** (`edit_momentum`, temporal_phase-excluded): 2 total matches (1 pre,
  0 concurrent, 1 post) — essentially no signal either direction, consistent with
  Section 8's ±1800s finding of zero.
- **Group B** (neither): 7 matches (2 pre, 1 concurrent, 4 post) — still
  post-dominant, same reactive lean as the original, unablated study found.

No directional claim beyond "still predominantly reactive where any signal exists
at all" is supported by this data.

---

## 10. Simpler Baselines

Moot for `edit_momentum` specifically, and stated as such rather than run as a
redundant test: Section 8 already found `edit_momentum`'s isolated (ablated)
association is exactly **zero** — there is no signal left to compare against a
simpler baseline. A baseline comparison only makes sense where a candidate signal
shows *some* real discriminating power to be matched or beaten; `edit_momentum`
does not, once isolated from `temporal_phase`.

---

## 11. Counterfactual Notification Burden

Reconstructed without modifying any code, for `edit_momentum` specifically:

- **Raw `edit_momentum` episodes** (unablated): 72 over 74.3 days ≈ **0.97/day** — a
  plausible, sustainable notification rate on its face.
- **But given Section 8's finding**, essentially all of this rate's apparent
  "usefulness" (7 true-ish matches to successes) is attributable to its
  `temporal_phase`-paired subset, not to `edit_momentum` itself — meaning a
  notification rule keyed on `edit_momentum` alone would, on this historical data,
  have produced close to a 1/day stream that is **almost entirely false positive**
  with respect to the two tested event categories, once the confound is removed.
- Comparison against "first-ever only" (the current architecture's actual
  restriction, ~1.2/day across all pairs, from the prior study) and "every episode"
  (~6.1/day) is unchanged from the prior study's own findings — not recomputed
  here, since this mission's scope is the two specific components, not the whole
  detector's burden profile again.

No notification rule was optimized or implemented in this pass.

---

## 12. Falsification Results

Each of the mission's seven target conclusions, tested directly:

- **F1 — `edit_momentum` is merely a renamed self-edit activity counter.**
  **Confirmed, precisely** (Section 2/4): it is not an activity *counter* but a
  rolling-window *success rate*, and it is defined directly from self-edit
  outcomes, not merely correlated with them.
- **F2 — the association disappears after `temporal_phase` ablation.**
  **Confirmed** (Section 7): match rate 0.418→0.127, significance p=0.036→0.132.
  "Disappears" is slightly strong — a small residual (0.127, non-significant)
  remains — but the qualifying, significant finding from the prior study does not
  survive.
- **F3 — the association survives but is entirely post-event/reactive.** **Not the
  best-fitting description** — the association does not cleanly "survive"; it
  collapses in magnitude and loses significance. What little survives is still
  post-dominant (Section 9), consistent with F3's directional claim but not its
  premise that a real association persists.
- **F4 — a trivial activity signal performs equally well.** **Partially supported,
  already established in the prior report** (Section 10/16 there): the
  activity-matched control materially shrank the original effect (0.418→ its own
  0.307 mean) even before this mission's ablation; this mission adds that once
  `temporal_phase` is also removed, the residual is statistically indistinguishable
  from that same activity-matched baseline (p=0.132).
- **F5 — the effect is driven by one burst/day.** **Not supported** — the prior
  study's weekly table already showed no single week dominating (Section 7 there);
  this mission did not find evidence of a single-burst artifact either.
- **F6 — the prior `p=0.036` result is unstable under reasonable fixed
  reanalysis.** **Confirmed** — the single most load-bearing number in the prior
  report does not survive this mission's frozen, pre-specified `temporal_phase`
  ablation, which is about as "reasonable a fixed reanalysis" as this project's own
  own falsification discipline calls for.
- **F7 — `edit_momentum` is genuinely informative but not Protector-relevant.**
  **Not supported** — Section 8 found `edit_momentum` is not measurably informative
  at all, once properly isolated, for either tested event category; this is a
  stronger negative finding than "informative but not relevant."

---

## 13. Protector Relevance

# NO — DO NOT USE AS INITIATIVE SIGNAL

Specifically: **as currently constituted, using `seam_engine`'s aggregate output —
or the `edit_momentum` component specifically — as a trigger for Echo's own
initiative/voice is not supported by this data.** The one event category most
relevant to Protector-adjacent use (real crashes) shows zero measurable
association both before and after this mission's ablation. The self-edit-success
association, the only one that ever cleared significance, does not survive a
directly-targeted, pre-registered mechanistic test. This verdict is scoped to
`seam_engine`'s current pair set and the two event categories tested — it says
nothing about `seam_engine`'s existing, separate, already-established internal
uses (feeding `reflection_shard.observe()`, curiosity topic-bias), which this
mission did not evaluate and does not call into question.

`temporal_phase`'s own outsized, unexplained share of seam activity (75.8% of all
episodes) remains a genuinely open question outside this mission's scope — a
plausible, but not independently verified in this pass, mechanistic account is
that `temporal_phase` is a smooth, fully deterministic periodic signal (a pure sine
function of local time, per Section 5), and a smooth periodic wave will regularly
cross its own recent-history z-score threshold as a structural property of its own
shape, independent of anything else happening in the system — worth investigating
directly in a future, separately-scoped pass, not resolved here.

---

## 14. Next-Step Recommendation

# D. STOP SEAM-INITIATIVE WORK

The evidence has become sufficiently negative for this specific line of pursuit:
two independent, increasingly targeted follow-up studies have now both failed to
find a defensible signal — the first (broad historical correlation) found only a
modest, confound-adjacent association; this one (direct mechanistic ablation of
the two components the first study flagged as suspicious) found that association
collapses under the most direct test available, and the specific hypothesized
mechanism (`edit_momentum`) is cleanly, quantitatively disconfirmed.

This recommendation is scoped precisely: it concerns **pursuing `seam_engine` as a
substrate for Echo's own Initiative/Protector voice specifically** — it is not a
recommendation to modify, disable, or devalue `seam_engine`'s existing, unrelated
internal roles, and it is not authorization to design or implement a replacement
signal.

---

## 15. What This Establishes

A mechanically computed internal variable (`edit_momentum`) was traced completely
and found to be a direct restatement of the self-edit success rate, with no
independent informational content beyond that restatement. A specific,
pre-registered ablation of a second, unexplained component (`temporal_phase`)
substantially collapsed the one statistically significant finding the prior study
produced. Both results were obtained through frozen, disclosed methodology,
re-derived from independently-sourced logs, and cross-checked against the real,
live architecture rather than assumed from variable names.

---

## 16. What This Does NOT Establish

Consistent with the prior study's own boundary: neither a positive nor a negative
result in this mission establishes anything about consciousness, concern,
preference, intention, desire to communicate, self-preservation, subjective
significance, or moral status. This mission evaluated a detector's mechanistic
components and their statistical behavior, nothing more. The negative result found
here does not establish that Echo lacks any of those properties — it establishes
that this specific detector, decomposed into its parts, does not currently carry
usable evidence either way.

---

## 17. Recommendation

See Section 14 — **D. STOP SEAM-INITIATIVE WORK.** No implementation of any kind
is authorized by this report.

---

## 18. Repository Integrity

- `app/core/echo_state.py`, `app/core/introspection_channel.py`,
  `app/core/seam_engine.py`, `run.py`: read only, zero edits.
- `memory/reflection_shard.jsonl`, `memory/seam_log.jsonl`, `memory/SELF_EDIT.log`,
  `memory/echo_watchdog.log`: read only, aggregated in scratch analysis scripts
  outside the repository, never written back to.
- No Initiative Record, Protector Clause logic, veto logic, or notification
  infrastructure was implemented. `_emit_fn` was not connected. `seam_engine.py`
  was not modified.
- Echo's live process was confirmed running throughout (PID 71538, uptime
  consistent with a real crash-and-restart at 2026-09-28T19:15:45 -0700, itself
  one of the seven real crash events this study's own Timeline B already
  independently identified — corroborating, not contaminating, this mission's own
  data) — not stopped, restarted, or signaled by this mission.
- No learned state (RiverBrain, VSL, `self_edit_convergence.json`) was modified.
- Nothing was staged, committed, or pushed. HEAD remained at
  `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`, throughout.
- The only new artifact produced is this report file itself, left untracked and
  unstaged. All intermediate analysis scripts and the reused `timelines.pkl` data
  live outside the repository, in this session's scratch directory.
