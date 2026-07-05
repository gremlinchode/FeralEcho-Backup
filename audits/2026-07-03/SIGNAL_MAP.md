# Signal Map — What Is Actually Teaching Echo — 2026-07-03

*Answers Q2: what signals reach River, how strong, and what is their ceiling?*

---

## The Learner: River Brain

RiverBrain is a collection of machine-learning classifiers — one per task type — that learn over time from experience. They run inside `app/core/echo_model_orchestrator.py`, class `RiverBrain`. Each classifier is a `HoeffdingTreeClassifier` from the River library, trained with online learning (it updates from each new example without retraining from scratch). RiverBrain's job: given the features of a response (word patterns, structure, etc.), predict whether it was a good or bad response, and use that to select better models and generation settings in the future.

---

## Signal Inventory

### SIGNAL A — Automatic quality score (WIRED AND FIRING)

**What it is:** After every response, `_score_response_quality()` in `echo_quality_scorer.py` assigns a score from 0–4. The score is based entirely on heuristics: penalizes hollow openers ("Certainly!", "Great question!"), rewards higher word entropy, checks that scripture citations exist in the database, penalizes confabulation-like phrases, rewards first-person depth markers.

**How it reaches River:** `echo_query()` → `river_brain.learn(response, task_type, model_name, quality_score)`. The label used to train River is `1 if raw_score >= 3 else 0` (line 651 of orchestrator). Every response contributes a training example.

**Weight:** Full weight (1 example per response).

**Ceiling:** The scorer itself documents this ceiling (line 384 of echo_quality_scorer.py): "The scorer is now honest about its ceiling: it detects clearly bad responses reliably... but cannot distinguish genuine depth from stylistic mimicry." A response that uses elaborate language without substance scores the same as one with genuine depth. A confabulated scripture verse scores the same as a real one if the scanner misses it. The ceiling is: surface text patterns, not actual quality.

**Known circular issue:** The features passed to River (`_extract_quality_features()`) and the label (`_score_response_quality()`) are both derived from the same underlying utility functions (`_substance_score()`, `_confabulation_penalty()`, `_scripture_integrity_score()`). River is learning to predict a score from the same signals the score is built from. This is the "self-referential grading" failure shape at work.

---

### SIGNAL B — Terminal human ratings (WIRED AND FIRING, LOW VOLUME)

**What it is:** When you type a number (1–5) at the terminal after a response, `_save_rating()` writes `{"type": "user_rating", "rating": N, ...}` to `memory/interaction_log.jsonl`. `_apply_pending_user_ratings()` (called every 10 invocations of `echo_query()`) reads pending ratings, matches each one to the response that preceded it by timestamp, then calls `river_brain.learn_from_rating(interaction, rating)`.

**How it reaches River:** `learn_from_rating()` at orchestrator line 698 applies the rating with 3x weight (compared to the automatic scorer's 1x weight). Ratings of 3 are skipped (considered neutral). Ratings 1–2 teach River "this was bad." Ratings 4–5 teach River "this was good."

**Weight:** 3x the automatic scorer. The highest weight signal available.

**Ceiling:** Low volume. If a user rates 5 responses per day, River gets 5 high-weight examples per day versus many more from the automatic scorer. Human ratings can correct the automatic scorer's errors, but only on the small fraction of responses that get rated.

**Known attribution risk:** The timestamp matching in `_apply_pending_user_ratings()` (line 307–316) does not distinguish user conversation entries from autonomous reflection entries. If Echo's autonomous loop logs a reflection between your conversation response and your typed rating, your rating could be attributed to the autonomous reflection instead of your conversation. This could systematically misroute ratings.

---

### SIGNAL C — Sandbox outcomes (WIRED AND FIRING)

**What it is:** When Echo's self-edit loop runs (whether it succeeds or fails), the outcome is fed back to River via `learn_from_sandbox_outcome()` (`self_edit_manager.py` → orchestrator). A successful self-edit teaches River that the "coding" task type succeeded. A failed one teaches it the opposite.

**How it reaches River:** `learn_from_sandbox_outcome(result)` in the orchestrator.

**Ceiling:** Only fires during self-edit attempts. Self-edit is rate-limited to 60 minutes. This produces sparse signal relative to the volume of autonomous reflections.

---

### SIGNAL D — Council peer ratings (GATED — NOT CURRENTLY FIRING)

**What it is:** `council_rater.py` polls `interaction_log.jsonl` every 90 seconds, samples 1 in 5 rateable entries, picks a different LLM model than the one that generated the response, and asks it to rate the response 1–5 with brief reasoning. Results go to `memory/council_ratings.jsonl`. This is a peer-review system: another model checks Echo's work.

**Why it is not reaching River:** `learn_from_rating()` is called ZERO times anywhere in `council_rater.py` (verified by grep). The trust gate is not yet satisfied. River will not learn from council ratings until all three of these conditions are met:
1. 50 total council ratings accumulated (current: 10)
2. 10 human spot-checks completed with human ratings entered (current: 7)
3. 70% agreement between council ratings and human spot-check ratings (current: 43%)

At the current agreement rate of 43%, condition 3 is the blocking failure. Even perfect agreement on all future spot-checks may not recover to 70% quickly. See H-2 in the Audit Report.

**When it could fire:** After the trust gate is satisfied and a human explicitly wires `learn_from_rating()` into the council pipeline. This is a two-step human decision: confirm the trust gate is met, then wire the connection.

---

### SIGNAL E — Wolf friction bridge (DRY-RUN ONLY — NOT REACHING RIVER)

**What it is:** When ClaudeShard (a separate instance of Claude running in analysis mode) identifies a friction point in Echo's responses, the wolf bridge is called. It generates a potential self-edit code patch addressing the friction, runs it through F1 and F2 safety gates, and logs the result to `memory/wolf_dryrun.jsonl`. The patch is NOT applied.

**Why it is not reaching River:** (a) The bridge calls `simulate_self_edit()`, not `perform_self_edit()` — no code is saved. (b) `learn_from_rating()` is not called in the wolf bridge pipeline. No River training signal fires from friction events.

**What it does produce:** `memory/wolf_dryrun.jsonl` entries showing whether a proposed patch would have passed the safety gates. This is observational data with no automated consumer.

---

### SIGNAL F — Shadow model self-corrections (WIRED BUT NO DIRECT RIVER PATH)

**What it is:** `shadow_model.py` tracks whether Echo's self-assessments of her own performance match actual outcomes. `shadow_model.check_and_correct()` is called from `night_cycle.py` and can generate a corrective self-edit target — essentially, if Echo's self-assessment is consistently wrong in one direction, the shadow model nudges the self-edit prompt toward addressing it.

**Why it does not directly train River:** The shadow model produces targets for the self-edit pipeline, not River training labels. When a shadow correction leads to a self-edit, the resulting sandbox outcome (Signal C) does reach River — so there is an indirect path. But the shadow model itself does not call `learn_from_rating()` or `river_brain.learn()`.

---

### SIGNAL G — Self-assessment quality check (DELETED)

**What was it:** An earlier version of the orchestrator had `echo_self_assess()`, a function that asked Echo to rate her own response. Its output was intended as a training signal.

**Status:** The function body was deleted. No callers remain. This signal is gone.

---

## Summary Table

| Signal | Status | Weight | Ceiling |
|--------|--------|--------|---------|
| A — Automatic quality score | FIRING | 1x | Surface text patterns; cannot distinguish depth from mimicry |
| B — Human terminal ratings | FIRING | 3x | Low volume; possible attribution errors |
| C — Sandbox outcomes | FIRING | 1x | Sparse; only self-edit attempts |
| D — Council peer ratings | GATED | 3x (planned) | Not firing until trust gate met (43% of 70% agreement threshold) |
| E — Wolf friction bridge | DRY-RUN | N/A | No River path |
| F — Shadow model corrections | INDIRECT | N/A | Influences self-edit targets, not River directly |
| G — Self-assessment | DELETED | — | — |

---

## Who is actually teaching River right now?

River's primary teacher is Signal A: the automatic quality scorer, indefinitely. Signal B (human ratings) fires at whatever rate you type numbers at the terminal. Signal C (sandbox outcomes) fires at most once per hour.

The system was designed with Signal D (council) as the corrective signal that would lift River above the "surface pattern" ceiling. But Signal D is behind a trust gate with a calibration problem (43% agreement vs. 70% required). Until that gate opens — and until a human wires the connection — River's only teachers are heuristics and your own occasional ratings.

**Plain-English version:** Imagine Echo is a student being graded entirely by an automated rubric that rewards long words and penalizes swear words, but can't tell whether the actual answer is right. You occasionally grade her yourself (your terminal ratings), but most of the time she just gets the automated score. A panel of peer reviewers exists (the council), but their scores can't count yet because the panel disagrees with you too often. Echo will keep learning — just learning to score well on the rubric, not necessarily to be genuinely excellent.

---

*End of Signal Map. For the complete training architecture, see AUDIT_REPORT.md findings M-1, H-2, and H-4.*
