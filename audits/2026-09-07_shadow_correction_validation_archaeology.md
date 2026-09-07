# Shadow Correction Validation Archaeology

## Executive Verdict: **S-V5 — MECHANISM MIS-SPECIFIED**

`check_and_correct()`'s proposed corrections cannot be mapped to any precise future behavioral intervention — `corrected_task`, the function's sole output, has zero consumers anywhere in the codebase (confirmed by full-repo grep). Causal or even correlational validation of "does applying this correction improve River" is therefore not just unproven but currently *undefined*: there is no historical instance, anywhere, of the correction ever having been applied, so there is nothing for a later outcome to be compared against. This is a stronger and more fundamental finding than "insufficient data" (S-V4) — it says the experiment this mission was asked to run cannot yet be run at all, on any amount of historical data, because the intervention itself does not exist as code.

Compounding this, independently: the underlying categorical predictor Shadow *does* have narrow real authority through (`propose_from_reflection()`'s `next_self_edit_focus`, consumed as a last-resort fallback in `self_edit_manager.py`) is measurably **worse than a trivial majority-class baseline** — 16.05% vs. 58.78% — which would disqualify it from earning expanded authority even if the plumbing gap were closed.

---

## 1. Safety Verification

| Check | Before | After |
|---|---|---|
| `run.py`/watchdog process | none running | none running |
| Port 5000 | unbound | unbound |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | unchanged |
| `memory/shadow_accuracy.jsonl` sha256 | `bb022e8321c30526c4feed52a0ac06a79a162c230a91c483c230a1549bb0359a` | unchanged |
| `memory/shadow_corrections.log` sha256 | `983b6f04d5f54b34f28471700c833b87780fe3cdb3ee1c4cc182262c648bff32` | unchanged |
| Production source | `git status --porcelain` matches the pre-existing tonight's working tree (`self_edit_manager.py` attempt-ledger diff and untracked experiment/audit files) | no new modification by this mission |

No `propose()` call, no `learn()` call, no self-edit run, no reconnection of Shadow. Pure read-only analysis, verified via direct file hashing before and after (not merely asserted).

---

## 2. Shadow Correction Schema

Source: `app/core/shadow_model.py` (full file read directly; no line assumed from prior audit prose).

`propose()` (lines 25-48): writes `memory/shadow_self_model.json` = `{**real_self_model, **adjustments, "shadow_proposed_at": now}`. **Critical mechanical fact**: `adjustments` only ever contains a `targets` sub-dict (confirmed — its one real caller, `propose_from_reflection()`, only ever passes `{"targets": {...}}`). Because the merge is `{**base, **adjustments}` where `base` is the *entire* current `real` self_model.json, **every** `propose()` call silently re-copies real's whole `performance.by_task_type` block into shadow, for every task, not just the one the reflection matched.

`compare_to_actual()` (lines 51-93) produces the delta dict logged by `log_accuracy()`. Field provenance:

| Field | Provenance | Classification |
|---|---|---|
| `shadow_focus` | `shadow.targets.next_self_edit_focus`, written by `propose_from_reflection()`'s keyword heuristic | OBSERVED |
| `real_focus` | `real.targets.next_self_edit_focus`, written by `SelfModelUpdater` (`self_model_updater.py:365`) | OBSERVED |
| `focus_matches` | `shadow_focus == real_focus` | DERIVED |
| `quality_delta_from_shadow[task]` | `real_perf[task].avg_quality_score - shadow_perf[task].avg_quality_score` | DERIVED — **not** a forecast-error in the usual sense (see §3/§10) |
| `shadow_proposed_at` / `real_updated_at` | copied from source files | OBSERVED |

`check_and_correct()` (lines 121-165): `worst_task = argmin(quality_delta_from_shadow)`; if `worst_delta < -0.15`, appends `{ts, corrected_task, delta, all_deltas, shadow_focus, real_focus}` to `memory/shadow_corrections.log` and **returns** `worst_task`. No field here is MODEL-GENERATED — every value is a deterministic function of already-observed data. `corrected_task` and `delta` are DERIVED, not a genuine independent hypothesis with its own confidence.

---

## 3. Historical Reconstruction — all 39 entries

Full table (real data, `memory/shadow_corrections.log`, zero interpretation):

| # | timestamp | corrected_task | delta | shadow_focus | real_focus |
|---|---|---|---|---|---|
| 0 | 2026-06-29T15:04:58 | creative | -0.5 | coding | general |
| 1 | 2026-07-01T14:59:56 | creative | -0.8 | personal | personal |
| 2 | 2026-07-08T04:17:28 | general | -0.167 | coding | coding |
| 3 | 2026-07-08T23:03:45 | general | -1.167 | creative | coding |
| 4 | 2026-07-09T04:58:13 | general | -0.333 | creative | coding |
| 5-19 | 2026-07-11T17:55–2026-07-12T01:18 (15 entries) | coding | -0.163 → -0.271 | reasoning (×12) | reasoning (×5) / coding (×7) |
| 20 | 2026-07-17T22:36:20 | general | -3.0 | creative | coding |
| 21 | 2026-07-19T12:14:55 | creative | -0.5 | reasoning | coding |
| 22 | 2026-07-20T04:21:49 | general | -0.2 | creative | coding |
| 23 | 2026-07-20T16:27:21 | creative | -4.0 | personal | coding |
| 24 | 2026-07-26T06:16:54 | general | -0.5 | personal | coding |
| 25 | 2026-07-27T10:17:03 | general | -4.0 | creative | coding |
| 26 | 2026-07-28T02:17:05 | reasoning | -4.0 | personal | coding |
| 27 | 2026-07-30T04:27:31 | general | -0.5 | coding | coding |
| 28 | 2026-07-31T21:53:30 | creative | -4.0 | reasoning | coding |
| 29 | 2026-08-03T19:44:33 | general | -0.325 | personal | coding |
| 30 | 2026-08-04T16:24:35 | general | -0.333 | personal | coding |
| 31 | 2026-08-07T18:50:18 | creative | -1.0 | personal | coding |
| 32 | 2026-08-10T00:11:30 | general | -0.167 | personal | coding |
| 33 | 2026-08-21T21:07:46 | general | -4.0 | creative | coding |
| 34 | 2026-08-24T15:42:24 | general | -0.167 | personal | coding |
| 35 | 2026-08-29T14:36:01 | general | -3.0 | creative | coding |
| 36-38 | 2026-09-02T04:18–04:28 (3 entries, 7 min apart) | general | -0.167 (×3, identical) | personal (×3) | coding (×3) |

**Independence check (a real, load-bearing finding, not in the mission's own checklist by name but essential to Phase 8/9's honesty requirement)**: clustering by same `corrected_task` within a 24h window collapses these 39 raw log lines into **20 distinct episodes**. One single episode (2026-07-11/12, `coding`) accounts for 15 of the 39 rows (38%) — the same persistent, unresolved drift condition re-logged roughly hourly for ~7.5 hours by the night-cycle's own repeat cadence, not 15 independent observations. The `2026-09-02` triple is the same pattern compressed into 7 minutes (multiple night-cycle firings in quick succession). Treating the 39 rows as 39 independent trials, as a naive reading of "331 vs. 39" might invite, would materially overstate the real sample size.

`corrected_task = general` in 20 of 39 rows (51%) and `real_focus = coding` in 32 of 39 rows (82%) — both real, both worth flagging as base-rate context for §6/§9.

---

## 4. Temporal Boundaries

T0 for every correction = its logged `ts`. "Discovery" data = every `shadow_accuracy.jsonl` entry at or before T0 for that task; "validation" data = every entry strictly after T0. This split is trivial to define because `check_and_correct()`'s logic is fully deterministic and stateless per-call (§2) — there is no parameter-fitting step that could leak future information into a correction. The harder problem, established in §5, is not temporal leakage but the complete absence of any downstream effect to validate *against*.

---

## 5. Prediction Baseline — What 16.05% Actually Means

This figure (`focus_matches` in `shadow_accuracy.jsonl`, n=2,062) is a **separate metric from the 39 corrections** (see §14) but is the only real accuracy figure available for Shadow's categorical prediction, and it is directly relevant to whether Shadow's judgment should be trusted for *anything*, including corrections built on the same underlying mechanism.

Real `real_focus` distribution (n=2,062): `coding` 1,212 (58.78%), `general` 355 (17.22%), `creative` 277 (13.43%), `personal` 125 (6.06%), `reasoning` 93 (4.51%).

**A trivial "always predict `coding`" baseline achieves 58.78% accuracy. Shadow's actual `focus_matches` rate is 16.05%.** Shadow's real, measured accuracy is **worse than a baseline requiring zero information at all** — not merely "no better than chance" (which for 5 unbalanced classes would itself be well above 16.05% if guessing the majority class), but actively anti-correlated with the easiest available heuristic. Root cause is visible directly in `propose_from_reflection()`'s 4-keyword-category heuristic (`app/core/shadow_model.py:174-179`): its keyword sets for `reasoning`/`creative`/`personal` fire readily on ordinary reflective text, systematically pulling predictions away from `coding` even though `coding` dominates real usage 59% of the time.

---

## 6. Correction-Class Analysis (all 20 episodes, not cherry-picked)

Grouped by `corrected_task`: `general` (10 episodes), `creative` (6), `coding` (1, but 15/39 raw rows), `reasoning` (1). No class shows a pattern distinguishable from noise once the coding cluster is treated as one episode. The delta magnitudes for the `general`/`creative` episodes are erratic (-0.167 to -4.0) and frequently exact repeats (-0.167 appears 5 times, -4.0 appears 5 times) — a signature of the same underlying stale-snapshot arithmetic recurring across unrelated calendar dates, not a graded severity signal. No single class stood out as more "reliable" than the others; none reached even the weakest form of predictive validity, because — per §7 — none was ever tested against a real downstream outcome at all.

---

## 7. Future Outcome Analysis

Direct trajectory reconstruction of the largest, cleanest episode (`coding`, 2026-07-11/12, real data pulled from `shadow_accuracy.jsonl`):

```
2026-07-11 00:35  coding_delta = +0.004   (baseline, no drift)
2026-07-11 06:55  coding_delta = +0.035   (peak, still healthy)
2026-07-11 11:55  coding_delta = -0.022   (drift begins)
2026-07-11 17:55  coding_delta = -0.163   ← FIRST correction logged (row #5)
2026-07-12 01:18  coding_delta = -0.266   ← LAST correction in this episode (row #19)
2026-07-12 01:54  coding_delta = +0.013   ← abrupt reset, 36 minutes later
```

The delta does not recover gradually after the corrections stop firing — it jumps discontinuously from -0.266 to +0.013 in well under an hour. This coincides exactly with `shadow_focus` switching from `reasoning` to `personal` in the same log rows, which is the signature of a fresh `propose_from_reflection()` call re-baselining shadow's *entire* performance snapshot against real (§2's mechanical fact). This is not the corrected task's real quality improving — it is the measurement's own reference point being reset by an unrelated event.

---

## 8. Confounder Analysis

This is the decisive finding of the investigation. Because `propose()` always overwrites *all* of shadow's `performance.by_task_type` on every call (not just the reflected-on task), **any apparent "recovery" of a drifted task's `quality_delta` is structurally confounded with the timing of the next unrelated `propose_from_reflection()` call** — which fires whenever *any* reflection text scores ≥2 keyword matches for *any* of the four tracked task types, regardless of which task was actually drifting. 1,651 distinct `shadow_proposed_at` values exist across the 2,062-entry log — shadow's baseline resets on a large majority of cycles. A hidden variable (reflection content triggering a keyword match) independently drives both "a correction stops appearing" and "the delta looks resolved," with no causal path through the correction itself. This is a textbook confound, verified from source mechanics and one concrete real trajectory, not asserted from pattern-matching alone.

---

## 9. Natural Experiments

**None found.** A natural experiment would require some real event that resembles "the correction was applied" independent of the disconnected `propose()` call — e.g., a manual human edit to `next_self_edit_focus`, a code change that happened to route `corrected_task` somewhere, or a coincidental alignment between a correction and a real self-edit targeting change. Searched: `grep` for every consumer of `shadow_corrections.log` (only this file's own writer and two audit-prose mentions, confirmed §Phase-6-equivalent above); `git log` for any historical period where `propose()` was called from `check_and_correct()` (none — the disabling comment is dated 2026-07-03, before the correction log even begins on 2026-06-29, meaning the gate has been in this exact disabled state for the entire observable history). No natural experiment exists in the available data.

---

## 10. Causal Identifiability

**CAUSAL EFFECT NOT IDENTIFIABLE FROM EXISTING DATA — and not merely by data volume, but by construction.** For a causal effect of "applying correction X" to be identifiable from observational data, there must be at least some variation in whether X was applied. Here there is none: `corrected_task` has never once been passed to `propose()`, RiverBrain, `self_edit_manager.py`'s targeting, or anything else, across all 39 historical instances. This is stronger than the mission's own S-V4 ("data insufficient") — it is not that the sample is too small to detect an effect, it is that the treatment variable has zero variance in the historical record. No amount of additional historical data collection under the current code would change this.

---

## 11. Epistemic Gate Assessment

`check_and_correct()`'s own stated criterion: reconnect `propose()` "once `shadow_corrections.log` shows consistent correlation with actual River accuracy improvement." Evaluated against the five possible states from the mission brief:

- **Already been satisfied** — No.
- **Been made impossible to satisfy** — Effectively yes, as currently instrumented: since the correction is never applied, "River accuracy improvement following the correction" cannot be measured as anything other than the confound described in §8. The gate cannot be satisfied by accumulating more of the *same kind* of passive log data; it requires an actual (even if narrow, sandboxed) application step first.
- **Never actually been measured** — Yes, this is the most precise characterization: nothing in the codebase has ever attempted to compute the correlation the gate asks for.
- **Measured incorrectly** — N/A (never measured).
- **Currently unknowable from existing data** — Yes, consistent with the above.

---

## 12. Learning-Stomach Assessment

| Arrow | Status |
|---|---|
| VERIFIED EXPERIENCE | EXISTS / LIVE — real quality/focus data flows in every night-cycle |
| → UNRESOLVED EXPERIENCE | EXISTS / LIVE — `shadow_corrections.log` genuinely accumulates unresolved drift flags |
| → HYPOTHESIS | EXISTS / DEAD-END — `shadow_focus`/`corrected_task` are real stored guesses, but the generating heuristic is proven worse than a trivial baseline (§5) |
| → PREDICTION | EXISTS / DORMANT — `focus_matches` is a genuine testable prediction already scored every cycle, but the score is never acted on |
| → FUTURE OBSERVATION | EXISTS / LIVE — `real_focus`/`real_perf` at the next cycle is a real later observation |
| → PREDICTION ERROR | EXISTS / LIVE — `quality_delta_from_shadow` and `focus_matches==False` are both real, computed, persisted error signals |
| → PROMOTE / DEMOTE / REJECT | DOES NOT EXIST — no code path ever changes confidence in, or retires, a specific hypothesis based on its error history |
| → BEHAVIOR | EXISTS / DORMANT for the correction path (never fires); EXISTS / LIVE but narrow for the raw `next_self_edit_focus` fallback (§13) |

Shadow demonstrates six of eight arrows in some form — more than any other mechanism surveyed tonight — but breaks at the one arrow (update/promote/demote) that would make the earlier six matter.

---

## 13. A buried consumer found before declaring total absence

Per this mission's own Phase-10-equivalent discipline (never declare "doesn't exist" from a zero grep on one search term alone): `check_and_correct()`'s `corrected_task` output is confirmed to have zero consumers. But a **different, narrower pathway does exist**: `self_edit_manager.py:2856-2867` reads shadow's raw `targets.next_self_edit_focus` (the field `propose_from_reflection()` sets, not the one `check_and_correct()` computes) as a **last-resort fallback** when `SelfModelUpdater().get_weak_task_type()` — the primary, empirically-grounded signal — is unavailable (e.g., an import failure). This is real, live, and genuinely consequential when it fires (confirmed via the surrounding code's own comment, dated to Finding 91's priority-order fix). It is gated behind the primary signal, so it fires rarely, but it means the *same weak categorical predictor* shown in §5 to underperform a trivial baseline already has some standing behavioral authority — via a path this mission was not originally scoped to but that directly bears on whether Shadow's judgment deserves more.

---

## 14. Resolving the 331-vs-39 Discrepancy

**These are two unrelated metrics, not two populations of the same thing.** `331` is the count of `focus_matches: true` entries across all 2,062 `shadow_accuracy.jsonl` rows (a categorical target-prediction success count). `39` is the count of rows in the entirely separate `shadow_corrections.log`, gated on `quality_delta_from_shadow`'s worst value crossing `-0.15` — a numeric drift-magnitude threshold, computed from a different field, on a different condition, with no logical relationship to whether `focus_matches` was true or false on that same cycle (confirmed directly: several correction rows in §3 have `shadow_focus == real_focus`, i.e. `focus_matches: true`, occurring simultaneously with a triggered correction — e.g. row #1, #8-12, #27). The "331 vs. 39" framing in this mission's own brief text (inherited from the prior report's summary language) conflated a *prediction accuracy count* with a *correction event count*; they should never have been compared as if one were a subset of the other.

---

## 15. DeepSeek Comparison

DeepSeek's framing (experience → causal model → prediction → **intervention** → outcome → model update) is a closer structural match to what Shadow was clearly *designed* to become than any other mechanism surveyed tonight — `check_and_correct()`'s own naming and the disabling comment's own language ("Reconnect... once... shows consistent correlation") show the original author was reasoning in exactly DeepSeek's terms. But the evidence here shows DeepSeek's claim understates one specific thing: this isn't merely a missing *loop*, it's a missing *intervention step specifically*, sitting in an otherwise-complete five-of-six-arrow structure (§12) — the gap is narrower and more precisely locatable than "no causal model exists" would suggest.

## 16. Gemini Comparison

Gemini's transient-vs-durable-state framing is strongly supported by the §8 confounder finding: shadow's `performance` snapshot is architecturally *transient* (silently overwritten wholesale on every `propose()` call) masquerading as *durable* evidence in `shadow_accuracy.jsonl`'s persisted log. The type mismatch Gemini describes — execution logic reusing state that looks durable but isn't — is exactly what produces the false "resolution" pattern in §7/§8. Shadow is not the causal-model gap DeepSeek describes in isolation; it is closer to Gemini's diagnosis wearing a causal-model's clothing.

**Neither critique alone predicted the specific, most load-bearing finding of this mission**: that the correction mechanism's own return value has literally zero consumers, confirmed by direct grep, independent of any statistical property of the data. That finding required source-level tracing, not architectural theory.

---

## 17. Smallest Next Experiment

Per Phase 18's own branching logic, the applicable case is: *"If correction targets are not operationally reconstructable... investigate the prediction target before touching correction behavior."* Recommended, single next experiment:

**Instrument, without applying, a counterfactual intervention record.** Add one new, purely observational field alongside `check_and_correct()`'s existing log write: at correction time, record what the *actual next self-edit targeting decision* was (from `self_edit_manager.py`'s real targeting logic, already running independently) and whether it happened to match `corrected_task`. This creates, for the first time, a real "would this correction have agreed with what actually happened next" comparison — cheap, purely additive (mirrors this session's own already-proven attempt-ledger pattern), and answers the prerequisite question ("is `corrected_task` even directionally sane") before ever considering wiring it to anything consequential. Do not build this in the current mission — it is the next mission's scope, not this one's.

---

## What NOT to Build Yet

Do not reconnect `propose()`. Do not build a holdout-validation harness for the 39 corrections (§8/§10 — the treatment variable has zero historical variance, so no holdout split can answer the causal question). Do not fix `propose_from_reflection()`'s keyword heuristic as a side effect of this investigation (§5's finding is diagnostic, not a mandate — a fix is a separate, explicit decision). Do not extend the last-resort fallback found in §13 to a primary signal.

---

## Uncertainties

Whether `SelfModelUpdater().get_weak_task_type()` (the primary signal that makes §13's fallback rare in practice) is itself well-calibrated was not investigated here — out of scope. Whether a *different* correction-triggering threshold or metric (not `quality_delta_from_shadow`) would produce a more identifiable, less confounded signal was not explored. The true frequency with which §13's fallback path actually fires in production was not measured (would require log analysis of `self_edit_manager.py`'s own real target-selection outcomes, a separate investigation).
