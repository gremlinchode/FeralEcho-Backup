# Experience → Hypothesis → Prediction → Update Archaeology

Read-only investigation. No production code, RiverBrain state, or memory data modified. Safety
invariants re-verified at start and end (§1) — HEAD and `river_brain.pkl` hash unchanged both times;
the working tree's pre-existing uncommitted changes from earlier tonight (`self_edit_manager.py`'s
attempt-ledger diff, `self_edit_attempt_ledger.py`, and the large `app/experiments/`/`audits/` pile)
were left untouched, confirmed by `git status` before and after showing only this new report file added.

## Executive Verdict: **EHPU-PARTIAL**

Several real components of the loop exist, independently, in different mechanisms — but no single
mechanism in the codebase closes all six edges (hypothesis → prediction → outcome-join →
prediction-error → update-rule → future-behavior). The single closest candidate breaks at one precisely
identified, already-diagnosed edge (§9).

---

## 1. Safety Verification

| Check | Before | After |
|---|---|---|
| `run.py`/watchdog process | not running | not running |
| Port 5000 | unbound | unbound |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | unchanged |
| Production source files modified this pass | none | none |
| Real self-edit run this pass | no | no |
| RiverBrain calls this pass | no | no |

This mission produced exactly one new file: this report. No experiment harness was created — every
finding below is source/log archaeology, per the mission's stricter (no-pipeline-exercise) constraint
compared to the two missions preceding it.

---

## 2. Candidate Mechanism Inventory

Strict evidentiary standard per Phase 3 — YES only when source/logs prove it, never inferred from a
name or comment.

| Mechanism | Source | Input | Persistent State | Hypothesis? | Prediction? | Later Outcome? | Updates From Outcome? | Changes Future Behavior? |
|---|---|---|---|---|---|---|---|---|
| RiverBrain `model_task_stats` | `echo_model_orchestrator.py` | response text, scored | `river_brain.pkl` (rolling mean) | **NO** — no discrete per-episode hypothesis, only a continuously-shifting aggregate value | **NO** — `score_model()` reads the current mean as a ranking heuristic, never stores it as "I expect X" before the outcome | N/A (no discrete prediction to join) | **YES** (mean shifts via `.learn()`) — but this is EMA continuity, not hypothesis revision | **YES** — `_select_council()`/`rank_models()` read the moved mean |
| `predictive_loop.py` WorldModel | `app/core/predictive_loop.py` | fetched news text | `prediction_log.jsonl`, in-memory Beta/Dirichlet posterior | **PARTIAL** — `predict()` computes an explicit expected sentiment/topic distribution | **YES, structurally** — `predict()`'s return dict is a real, computed forward expectation | **YES** — `update()` runs moments later against the same live state | **YES** — real KL-divergence (surprise_F) computed between prior and posterior | **YES** — surprise_F feeds `echo_state.py`, `exploration_bias`, curiosity-topic-bias (`[inherited]`) |
| `shadow_model.py` | `app/core/shadow_model.py` | `self_model.json["targets"]` | `shadow_self_model.json`, `shadow_accuracy.jsonl` (2,062 real entries), `shadow_corrections.log` (39 real entries) | **YES** — `propose()` writes an explicit `next_self_edit_focus` prediction | **YES** — the prediction is stored, not just computed transiently | **YES** — `compare_to_actual()` joins it against the real `self_model.json` outcome per cycle | **PARTIAL, then NO** — `check_and_correct()` computes exactly which correction is warranted (39 times, real) but **never applies it** — see §9 | **NO, automatically** — the one real behavior change (Finding 91's priority demotion) was a one-time human-reviewed code edit off the aggregate 16.1% figure, not this mechanism acting on itself |
| `seam_engine.py` | `app/core/seam_engine.py` | 9 `echo_state` dims + 3 salience components | `seam_log.jsonl` (754 real detections, 78 `first_ever`) | **YES, structurally** — an established correlation is an implicit prediction ("these move together") | **NO explicit stored value** — the "prediction" is the correlation sign itself, never separately recorded before the contradicting observation arrives | **YES** — the very next joint reading is the "outcome" checked against the established relationship | **NO** — no mechanism re-evaluates whether a flagged contradiction was itself validated by subsequent data; the correlation baseline is just recomputed leave-one-out each cycle, not revised based on whether past contradictions "held up" | **NO, effectively** — 76/78 real detections die at `garden_manager`'s dedup filter before reaching anything (`[inherited: Michelangelo III]`) |
| `garden_manager.py` `resolution_score` | `app/core/garden_manager.py:229-251` | quality score per ask | `data/question_garden.jsonl` | **NO** — confirmed by direct read (§6): purely a monotonic +0.5-per-ask accumulator, never decremented, never falsifiable | **NO** | N/A | **NO** — "resolution" only ever increases; nothing can demote a question back to unresolved | N/A |
| Attempt ledger (`self_edit_attempt_ledger.py`) | this session, live as of the immediately-preceding mission | F2/fitness facts per self-edit attempt | `memory/self_edit_attempt_ledger.jsonl` | **NO** | **NO** | N/A | N/A | **NO — confirmed zero readers** (§7) |
| RAOC | `app/experiments/raoc/` | — | `memory/raoc_pilot_trials.jsonl` (12 entries) | designed to test one, never run at scale | — | — | — | **NO** — `memory/raoc_trials.jsonl` does not exist; the pre-registered protocol was never executed beyond a 12-trial, explicitly non-evidentiary pilot (`[inherited: CLAUDE.md Findings 93-95]`) |
| Council-rating blend | `echo_model_orchestrator.py:737-756` | council rating + quality_score | `model_task_stats` | **NO** — not a prediction, a weighted-average fusion | **NO** | — | **YES** mechanically, but structurally cannot resolve in council's favor at score extremes (`[inherited: Michelangelo III §8]`) | **YES**, but effectively as quality_score alone |

---

## 3. Strongest Real Dataflow

```
shadow_model.propose_from_reflection() / propose()
      │  writes shadow_self_model.json["targets"]["next_self_edit_focus"]
      ▼
[time passes — real self-edit cycles run, self_model.json updates independently]
      │
      ▼
shadow_model.compare_to_actual()
      │  reads shadow_self_model.json + self_model.json, computes focus_matches (bool),
      │  quality_delta_from_shadow (per-task-type real number)
      ▼
shadow_model.log_accuracy()
      │  appends {focus_matches, shadow_focus, real_focus, quality_delta...} to
      │  shadow_accuracy.jsonl  ← 2,062 real, independently-verifiable entries
      ▼
shadow_model.check_and_correct(delta)
      │  identifies worst_task, worst_delta; if worse than _DRIFT_THRESHOLD (-0.15),
      │  logs {corrected_task, delta, all_deltas...} to shadow_corrections.log
      │  ← 39 real entries, confirmed this pass
      ▼
      X   ← propose() call is commented out. "intentionally absent (2026-07-03)... 
            Corrections are logged below for future human review." (source comment,
            self_edit_manager.py — verified verbatim this pass)
```

This is the single most complete real dataflow found anywhere in this investigation. It genuinely
reaches: real stored hypothesis → real stored prediction → real outcome join → real, persisted
prediction-error (`focus_matches`, `quality_delta_from_shadow`) → real, computed corrective action
(`worst_task`). It breaks at the very last edge: the corrective action is computed and logged, never
applied.

---

## 4. Strongest Apparent Learning Loop

Per §3, `shadow_model.py`'s propose→compare→log→correct chain. It is the only mechanism in this
codebase where a genuine, discrete, situation-specific prediction (not an aggregate rolling mean) is
stored *before* the outcome is known, then explicitly joined against the real outcome by field name
(`shadow_focus` vs `real_focus`), with the resulting error persisted 2,062 times.

---

## 5. Exact First Missing Edge

**In `shadow_model.py`'s `check_and_correct()` (lines ~121-159): the function computes `worst_task`
correctly, writes a complete, correctly-shaped correction record to `shadow_corrections.log`, and then
returns `worst_task` to its caller — but the one call that would close the loop, `propose({"targets":
{"next_self_edit_focus": worst_task}})`, is not present.** The code's own comment states this is
deliberate: *"Shadow corrections are advisory-only until the signal is externally validated. Both sides
of the shadow comparison trace to Echo's own outputs... no external anchor. ... Reconnect by restoring
`propose()` here once `shadow_corrections.log` shows consistent correlation with actual River accuracy
improvement."* Verified this pass: `memory/shadow_corrections.log` has 39 real entries spanning real
dates — genuine, ongoing evidence has been accumulating since at least 2026-09-02, and nothing has ever
read that file to perform the validation the comment describes as the reconnection trigger. **This is
the UPDATE-RULE GAP** — not because the mechanism is broken, but because the human-in-the-loop
validation step it was deliberately built to wait for has never itself run.

---

## 6. Evidence For/Against Hypothesis State

**For**: `shadow_model.propose()` (explicit, named prediction field), `predictive_loop.WorldModel.predict()`
(explicit Bayesian expectation), `seam_engine.check_pair()`'s established-correlation-as-implicit-
prediction (structural, not explicit).

**Against**: RiverBrain has no discrete hypothesis object anywhere — confirmed by reading
`score_model()`/`.learn()` in full this pass; it is pure continuous value estimation. `garden_manager.py`'s
`resolution_score` was directly read this pass (§2's table; source at lines 229-251) and confirmed to
contain zero hypothesis semantics — it is a repetition counter with a floor of "keeps asking" and a
ceiling of "resolved," with no possibility of a question being marked wrong.

---

## 7. Evidence For/Against Prediction State

**For**: `shadow_self_model.json`'s stored `next_self_edit_focus` field is a genuine, durable,
inspectable prediction that exists *before* the corresponding real outcome is known.
`predictive_loop.predict()`'s return dict is a genuine forward-computed expectation, though (§ next
paragraph) it is never durably stored.

**Against**: verified this pass by reading `app/autonomous_loop.py:243-249` directly — `predict()`'s
result (`_pred`) is used for exactly one purpose, a `logger.info()` call, then discarded. It is never
written to any file keyed by cycle/timestamp/trace_id, so nothing downstream can later fetch "what did
the world model expect on cycle N" and compare it explicitly — the actual `surprise_F` computed 60 lines
later in `update()` recomputes its own prior internally from the live class state, which happens to be
numerically identical (nothing else touches the posterior in between), but there is no explicit join —
it works by state continuity, not by a retrievable prediction record. This is a real, if narrow,
**PREDICTION-PRESERVATION gap**, distinct from the shadow model's clean stored-prediction pattern.

The new attempt ledger (§2) currently stores zero prediction-shaped fields by design — it is
observational, not predictive, per its own explicit non-goal (verified against its docstring this pass).

---

## 8. Evidence For/Against Outcome Joining

**For**: `shadow_model.compare_to_actual()` performs a real, field-name-based join
(`shadow_targets.get(...)` vs `real_targets.get(...)`), persisted per-cycle. `seam_engine.check_pair()`
joins the current joint reading against the leave-one-out historical correlation by construction (same
signal-pair identity). The real self-edit attempt ledger (this session's own prior work) now joins
`trace_id` across `interaction_log.jsonl`/`council_deliberations.jsonl`/`self_edit_attempt_ledger.jsonl`
— confirmed live with two real trace_ids (`e05cb935...`, `525ed7ea...`) this session — but nothing
downstream currently reads that join for anything (§7's absence of readers).

**Against**: RiverBrain has no outcome-join in the strict sense — `.learn()` scores the *just-produced*
response with the *same* function that would score any response; there is no separate, later "did this
selection turn out to be good" check performed against an independent future signal.

---

## 9. Evidence For/Against Update Rules

**For**: `predictive_loop.WorldModel.update()`'s conjugate Bayesian posterior update is a real,
mathematically legitimate update rule — the posterior genuinely shifts in the direction of new evidence
every cycle. RiverBrain's `.learn()` is a real (if simple) update rule (capped-window EMA).

**Against, specifically and precisely (§5)**: `shadow_model.check_and_correct()` computes a correct,
real update and then does not apply it — the single cleanest "the update rule exists in code and is
never executed" finding in this investigation. `garden_manager.update_question_quality()` has an update
rule, but it is one-directional (can only increase toward "resolved," can never decrease or reject) —
not a genuine hypothesis-test update in the falsifiable sense the mission requires.

---

## 10. Evidence For/Against Future Behavioral Authority

**For**: RiverBrain (`model_task_stats` genuinely moves selection — demonstrated live multiple times
this session, `[inherited]`), WorldModel's `surprise_F` (feeds `exploration_bias`/curiosity-topic-bias,
`[inherited: CLAUDE.md Phase 2b/2c]`), shadow model's one-time Finding-91 priority reorder (a real,
still-in-effect code change, `[inherited]`).

**Against**: the attempt ledger (zero readers, confirmed this pass), seam_engine (97% of outputs die
downstream, `[inherited]`), the 39 logged-but-unapplied shadow corrections (§5) — real diagnosed
authority that was never granted, not authority that was granted and found ineffective.

---

## 11. Live vs. Dormant vs. Dead-End Classification

| Mechanism | Classification |
|---|---|
| RiverBrain `model_task_stats` | **LIVE** (as a value-estimation loop) — but never reaches the HYPOTHESIS stage in the strict sense this mission defines |
| `predictive_loop.py` WorldModel | **LIVE** — genuine predict/update/surprise cycle running on real fetch cycles, confirmed called from `autonomous_loop.py` — but the literal prediction object is a **DEAD END** (discarded after one log line) even though the aggregate state it's drawn from is genuinely live |
| `shadow_model.py` propose→compare→log | **LIVE** through `log_accuracy()`; **DEAD END** exactly at `check_and_correct()`'s missing `propose()` call (§5) |
| `seam_engine.py` | **LIVE** for detection; **DORMANT/DEAD-END** for anything past detection (`[inherited]`) |
| `garden_manager.py` resolution | **LIVE**, but structurally incapable of ever being a hypothesis-test mechanism |
| Attempt ledger | **LIVE** for writing, **DORMANT** — genuinely new, zero consumers exist yet by design, not by failure |
| RAOC | **DORMANT** — real, well-designed protocol, never executed past a non-evidentiary pilot |

---

## 12. Learning-Stomach Assessment

Arrow-by-arrow, per Phase 13's required structure:

```
UNRESOLVED EXPERIENCE        → EXISTS / LIVE   (attempt ledger now preserves rejected self-edit
                                 attempts durably; shadow_corrections.log preserves 39 real,
                                 unresolved drift flags)
        ↓
REVISIT                      → DOES NOT EXIST  — nothing schedules a later look at either the
                                 attempt ledger or shadow_corrections.log; both are write-only stores
                                 with zero readers (confirmed this pass for the ledger; confirmed for
                                 shadow_corrections.log — grep for any reader beyond the write call
                                 itself returns nothing)
        ↓
MULTIPLE HYPOTHESES          → DOES NOT EXIST  — no mechanism anywhere generates competing
                                 explanations for the same experience; shadow_model's single
                                 `next_self_edit_focus` prediction is the closest analogue and it is
                                 singular, not competing
        ↓
PREDICTIONS                  → EXISTS / DORMANT — shadow_model's stored prediction is real but its
                                 update path is disabled (§5); WorldModel's prediction is live but
                                 discarded (§7)
        ↓
NEW EVIDENCE                 → EXISTS / LIVE   — real, continuous (interaction_log.jsonl, F2 results,
                                 self_model.json updates all genuinely accumulate)
        ↓
UPDATE                       → EXISTS / DEAD-END for shadow_model (computed, unapplied, §5);
                                 EXISTS / LIVE but aggregate-only for RiverBrain/WorldModel (no
                                 discrete hypothesis to update, only a continuous parameter)
```

**Verdict on the metaphor**: the "stomach" — a place for unresolved experience to wait — is now
genuinely closer to existing than it was at the start of tonight's investigation (the attempt ledger is
real preservation infrastructure). But the metaphor's most important implied capability, *revisiting*
unresolved material and *testing competing explanations* against later evidence, has **no real
implementation anywhere in the codebase**, not even a dormant or disabled one. The single closest thing
to a "revisit" trigger that exists — `check_and_correct()`'s comment describing exactly what evidence
would justify reconnecting it — is itself unread by anything. **The stomach metaphor is not wrong, but
it was never the accurate name for the gap this investigation actually found.** The gap is narrower and
more precise: a *scheduled reconsideration* step is absent, not a storage reservoir (storage now
exists, as of this session's own work).

---

## 13. DeepSeek Comparison

**DeepSeek's claim**: the deepest problem is a missing causal model / epistemic feedback loop
(experience → candidate causal model → prediction → intervention → outcome → model update).

**What the evidence supports**: partially correct, and shadow_model.py is direct, concrete evidence for
almost the entire chain DeepSeek describes — a candidate causal-ish model (a predicted focus), a real
outcome, a real update computation. **What it overstates**: DeepSeek's framing implies this loop is
absent architecturally; the forensic evidence shows a version of it *exists*, is *exercised
continuously* (2,062 real cycles), and breaks at exactly one identifiable call site, not throughout the
architecture generally. **What it misses**: the loop's break point is a *deliberate, documented,
human-gated design decision* (§5's comment), not an oversight — DeepSeek's "missing" framing doesn't
distinguish "never built" from "built, and paused pending validation that was never performed."

---

## 14. Gemini Comparison

**Gemini's claim**: a type mismatch between transient execution/control state and durable epistemic
state — execution consumes failure evidence for recovery, learning needs that evidence to survive.

**What the evidence supports**: strongly, and this session's own prior missions (the `sandbox_feedback
= "success_on_retry"` overwrite, §3 of `audits/2026-09-07_attempt_level_provenance_feasibility.md`)
are exactly this pattern, independently discovered before Gemini's critique was compared against
evidence here. `predictive_loop.predict()`'s discarded return value (§7) is a second, previously-unnoted
instance of the identical shape — a real, momentarily-correct piece of epistemic state (a prediction)
that only survives as a log line, consumed by nothing. **What it overstates**: not clearly anything
found this pass — Gemini's framing holds up better under this investigation's evidence than DeepSeek's
does. **What it misses**: the shadow-model case (§5) is not a type mismatch — the prediction *does*
survive durably (`shadow_accuracy.jsonl`, `shadow_corrections.log`), in exactly the persistent form
Gemini's framing calls for. It fails for a different reason: durable epistemic state exists, and the
update rule that should consume it is present in code but deliberately not invoked. Gemini's diagnosis
explains WorldModel and the pre-ledger self-edit retry path well; it does not explain shadow_model's
failure mode, which is a governance/wiring gap, not a state-representation gap.

**Net**: the two critiques are not in conflict; they each correctly describe a different mechanism.
Neither, on its own, would have predicted the *specific* first-missing-edge finding in §5 — that
required tracing shadow_model's actual source, not reasoning from architecture-level principles.

---

## 15. Smallest Next Experiment

Not an implementation — a **read-only historical analysis**, in the same spirit as tonight's
garden-relevance and consequence-audit work: pull all 39 real `shadow_corrections.log` entries, and for
each, check whether the `corrected_task` it identified subsequently showed real quality improvement in
`self_model.json`'s own historical snapshots (`memory/history/self_model_*.json`) over the following
window — i.e., retroactively test the exact validation `check_and_correct()`'s own comment says is the
prerequisite for reconnecting `propose()`. This produces, at zero implementation cost, the specific
evidence the code has been waiting for since 2026-07-03: does the corrective signal actually correlate
with subsequent real improvement, or not. If it does, reconnecting `propose()` is justified by the
mechanism's own stated bar. If it doesn't, that's equally valuable — a concrete answer to a
three-month-old open question, either way.

---

## 16. What NOT to Build Yet

Do not implement `check_and_correct()`'s missing `propose()` call without first running §15's
retroactive validation — restoring it blind would be exactly the "connect an unvalidated signal to
consequential behavior" mistake this whole session's relevance-gate mission (`audits/2026-09-06_minimal_relevance_gate_feasibility.md`)
already demonstrated can produce false confidence rather than real improvement. Do not build a
"revisit scheduler" for the attempt ledger or `shadow_corrections.log` yet — no evidence exists yet
that either log's content, once revisited, would produce anything actionable; §15 is the cheap
pre-check. Do not extend `predictive_loop.py`'s `predict()` to persist its output — a real, useful,
low-risk candidate fix, but out of scope for this archaeology-only mission per its own final constraint.

---

## 17. Exact Uncertainties

- Whether `predict()`'s literal returned value, if it were persisted and explicitly joined against
  `update()`'s surprise computation, would ever produce a materially different surprise reading than the
  current implicit-state-continuity approach already does — likely not (nothing intervenes between the
  two calls in the current control flow), but not directly tested this pass.
- Whether `seam_engine`'s implicit hypothesis (an established correlation) would benefit from an
  explicit "was this contradiction later validated" follow-up mechanism, or whether the underlying
  correlations are too noisy/low-n for that to be meaningful — not evaluated this pass.
- Whether §15's proposed retroactive validation is itself confounded (e.g., `self_model.json`'s
  historical snapshots may not be dense enough, or other concurrent self-edit activity may swamp any
  real signal from a single corrected-task nudge) — flagged as a real risk for whoever runs that
  analysis, not resolved here.
- Whether other, unexamined corners of the codebase contain a comparable "computed-but-unapplied
  update" pattern to shadow_model's — this pass found one clean example via targeted search on the
  existing forensic leads; a full-repository sweep for this exact shape (a correction computed, logged,
  and never applied) was not performed.

---

## Final Required Answers

**Strongest real pathway found, and where it breaks**: `shadow_model.py`'s propose → compare_to_actual
→ log_accuracy → check_and_correct chain (§3). It breaks at `check_and_correct()`
(`app/core/shadow_model.py`, lines ~121-159): the corrective `worst_task` is computed and logged to
`memory/shadow_corrections.log` (39 real entries) but the `propose()` call that would apply it is
absent by deliberate design, pending a validation step (§5) that has never itself been run.

**RiverBrain episode-level predictive state**: **absent**. RiverBrain contains no discrete, per-episode
hypothesis or stored prediction distinguishable from the selection decision itself — `score_model()`
reads a continuously-updated aggregate mean as a ranking heuristic; `.learn()` folds new evidence into
that same mean unconditionally. It is real, live, and behaviorally consequential (§2), but it is value
estimation, not hypothesis-testing, and does not qualify under this mission's strict definitions.

**DeepSeek vs. Gemini**: both are directionally right about different mechanisms and neither alone
predicts this pass's most precise finding (§13, §14). Gemini's transient-vs-durable framing better
explains `predictive_loop.py`'s discarded prediction and this session's earlier `sandbox_feedback`
overwrite finding; DeepSeek's causal-model framing better matches shadow_model's genuine (if broken)
predict/observe/update shape, but understates that the break is a documented pause, not an absence.

**Learning-stomach classification summary**: storage/preservation now genuinely exists (this session's
own attempt-ledger work); revisitation and competing-hypothesis generation do not exist anywhere in the
codebase, dormant or otherwise; the update step exists and is live for continuous/aggregate mechanisms
(RiverBrain, WorldModel) and exists-but-disabled for the one genuinely episodic, falsifiable mechanism
(shadow_model).
