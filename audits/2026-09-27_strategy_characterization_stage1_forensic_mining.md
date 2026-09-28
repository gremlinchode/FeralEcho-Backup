# Forensic Mining of the Completed K2 Strategy-Characterization Stage-1 Dataset

**Read-only.** No model calls were made anywhere in this analysis. No code, task, or
strategy definition was modified. Two things were "run": (1) the already-frozen,
already-executed statistical `analysis.py` module (a sanity-check re-run against
already-collected data, producing byte-identical numbers), and (2) `oracle_runner`'s pure
`extract_code()` function, applied to already-existing `raw_response` text already
sitting in `log_stage1.jsonl` — a classification operation on existing artifacts, never a
new generation. The frozen Stage-1 result (**Outcome E — Inconclusive**, template-level
Friedman n=6 p=0.0907) is unchanged and is not reinterpreted anywhere below.

Every claim is tagged **OBSERVED** (directly read from artifacts), **INFERRED** (a
necessary logical/arithmetic consequence of observed facts), or **HYPOTHESIZED** (a
plausible but unconfirmed explanation).

---

## 1. Artifact integrity check — **OBSERVED**

Reconstructed directly from `memory/experiments/strategy_characterization/stage1/log_stage1.jsonl`
and its 3 `world_*.json` files, not from remembered summary statistics:

- 216 rows, all with unique `(task_id, world_index, strategy, repeat_index)` keys — **zero duplicates**.
- Exact expected grid confirmed: 6 tasks × 3 worlds × 3 strategies × 4 repeats = 216, and every cell has exactly 4 repeats.
- Every row has all 13 expected fields (`task_id, world_index, strategy, repeat_index, seed, passed, ran_ok, infra, timeout, code_hash, raw_response, output_tail, error_tail`) — zero missing fields.
- 216 unique seeds across 216 rows — no seed reuse, matching the frozen design's own seed policy.
- All 3 world files present.

**No discrepancy found.** Proceeding without stopping.

## 2. Reproduction of the frozen headline — **OBSERVED**

Re-ran the frozen `analysis.py` against the same artifacts: Friedman n=6 statistic=4.80,
p=**0.0907** (matches); flip rates DIRECT=**0.1204**, STEPWISE=**0.4074**,
WORKED_EXAMPLE=**0.3148** (match); split-sample-corrected oracle ceiling=**0.1667**
(matches). Byte-identical to the frozen report. No discrepancy; the frozen result stands
exactly as reported.

---

## 3. What "flip rate" mechanically is — **OBSERVED**

A flip is: for one fixed `(task_id, world_index, strategy)` cell, one **pair of its 4
repeat generations** whose `passed` values disagree (one True, one False). Denominator:
C(4,2)=6 possible pairs per cell, summed across all 18 cells for a per-strategy figure
(108 pairs) or all 54 cells pooled (324 pairs). **This measures pure repeat-to-repeat
generation noise only** — task and world are held fixed within a cell; it says nothing
directly about task-to-task or world-to-world variation, and nothing about which strategy
is "better," only how internally consistent each strategy's own output is on the same
exact prompt content, repeated with different seeds.

**Mechanical decomposition (OBSERVED, not a new statistical test — this is a re-derivation
of the same number from its own definition):** for m passes out of 4 in a cell, the exact
flip contribution is m·(4−m)/6. I computed the per-cell m-distribution directly:

| Strategy | m=0 | m=1 | m=2 | m=3 | m=4 | cells at extremes (m=0 or 4) | cells in the middle (m=1–3) |
|---|---|---|---|---|---|---|---|
| DIRECT | 6 | 0 | 1 | 3 | 8 | **14/18** | 4/18 |
| STEPWISE | 1 | 3 | 5 | 5 | 4 | 5/18 | **13/18** |
| WORKED_EXAMPLE | 7 | 4 | 4 | 2 | 1 | 8/18 | 10/18 |

Recomputing flip-rate purely from this table reproduces 0.1204 / 0.4074 / 0.3148 exactly.

**This fully and mechanically explains the flip-rate gap, and changes what it means.**
DIRECT is not "more stable" in the sense of the *model* being calmer when using it — it
is **more bimodal**: on 14 of 18 real (task, world) conditions, DIRECT either reliably
solves the task every time or reliably fails it every time. STEPWISE spends most of its
outcomes (13/18) in the genuinely uncertain middle zone. **INFERRED:** the flip-rate
difference is a direct, deterministic consequence of each strategy's per-cell success
*probability distribution*, not evidence, by itself, of a different underlying stochastic
sampling process. Whether that different distribution reflects genuine differences in how
each strategy is used or is itself explained by task-specific mechanisms is addressed in
Sections 6–8.

---

## 4–6. Failure taxonomy, counts, and stability decomposition

**Mechanical taxonomy (OBSERVED, full population, all 216 rows, no subgroup selection):**

| Category | DIRECT (n=72) | STEPWISE (n=72) | WORKED_EXAMPLE (n=72) |
|---|---|---|---|
| PASS | 43 (59.7%) | 44 (61.1%) | 22 (30.6%) |
| RAN_OK_WRONG_ANSWER | 29 (40.3%) | 28 (38.9%) | 49 (68.1%) |
| CRASHED_OR_SYNTAX_ERROR | 0 | 0 | 1 (1.4%) |
| NO_CODE_EXTRACTED | 0 | 0 | 0 |
| INFRA_ERROR | 0 | 0 | 0 |

**The single most important mechanical finding of this whole pass:** across all 216
replicates, **essentially every failure (214/215 non-passing rows) is "ran to completion,
produced a syntactically valid answer, and got it semantically wrong."** Zero rows show a
missing function, unparseable code, or infrastructure failure. This directly answers
Section 5's question: **the strategies differ almost entirely in the *kind of logic
error*, not in whether they can produce valid, instruction-following code at all.**

**A specific pre-formed hypothesis is directly refuted here, not glossed over:**
Section 6 named "STEPWISE's extra reasoning/restatement creates more format-violation
opportunities" as a candidate mechanism for its higher flip-rate. **This is false** —
STEPWISE shows *zero* format/crash failures, identical to DIRECT (0/72 each). Whatever
explains STEPWISE's instability, it is not format-following breakdown.

---

## 7. Generated-code structural comparison — **OBSERVED**

Re-extracted code from every `raw_response` via the existing, unmodified
`oracle_runner.extract_code()` (classification of existing text, not new generation):

| Strategy | mean code length (chars) | mean helper-function count | mean sort/max/min calls | mean lambda uses |
|---|---|---|---|---|
| DIRECT | 188.1 | 0.00 | 0.82 | 1.00 |
| STEPWISE | 216.4 | 0.00 | 0.97 | 1.00 |
| WORKED_EXAMPLE | 211.8 | 0.25 | 0.79 | 0.78 |

STEPWISE's code is modestly longer and makes slightly more sort/max/min calls on
average — consistent with, but not proof of, more attempts at genuinely full sorting
logic. WORKED_EXAMPLE is the only strategy that ever defines an extra helper function
(25% of its outputs) and uses meaningfully fewer lambdas (0.78 vs 1.00) — **HYPOTHESIZED**:
plausibly primed by the worked example's own standalone-helper-function shape
(`def bigger(a, b): return a if a > b else b`), though this is not confirmed causally by
this coarse a metric.

---

## 8. Matched (task, world) discordant-condition analysis — **OBSERVED**

Built the full pass-count-out-of-4 table for every (task, world) × strategy cell. Three
task templates dominate the entire discordant pattern in this dataset, each confirmed
**consistent across all 3 independent worlds** (a genuinely robust, world-replicated
property of that specific task, not a one-world fluke):

- **K2.T2 (`rank_all`): DIRECT fails 12/12 (100%, all 3 worlds), STEPWISE fails only
  4/12 (33%).**
- **K2.T5 (`winner_with_score`): DIRECT fails 12/12 (100%, all 3 worlds), STEPWISE fails
  8/12 (67%) — a real, if smaller, improvement.**
- **K2.T6 (`is_winner`): WORKED_EXAMPLE fails 8/12 (67%, catastrophic collapse specific to
  this one strategy), while DIRECT (10/12 pass) and STEPWISE (11/12 pass) both do well.**

The other three templates (T1, T3, T4) show the *opposite* pattern — DIRECT is the
strongest of the three there (11/12, 11/12, 11/12 respectively), with STEPWISE and
WORKED_EXAMPLE both somewhat weaker and noisier.

**I mechanistically traced *why*, using the real diagnostic content already logged in
`output_tail`** (the grader's own `FAIL <args> <actual> <expected>` line — genuine
per-test diagnostic evidence, not just pass/fail):

- **T2, systematically classified across all real failures (not a sample):** 11 of
  DIRECT's 12 failures return the **full `(name, score, tag)` tuples instead of just the
  names** — a specific field-extraction/output-shape error. Only 1/12 is a pure
  ordering/tie-break error with the correct element type. **STEPWISE's 4 failures are the
  reverse: 0/4 show the wrong-element-type bug; all 4 are pure ordering errors.**
  Concrete cited example (DIRECT, seed=960248512, world=0, rep=1): input
  `[('dot',2,'renem'), ('bo',3,'dogiz'), ('eve',1,'dulup'), ('cid',1,'dulup'), ('jo',2,'renem')]`,
  expected `['bo','dot','jo','cid','eve']`, actual
  `[('bo',3,'dogiz'), ('dot',2,'renem'), ('jo',2,'renem'), ('cid',1,'dulup'), ('eve',1,'dulup')]`
  — correctly sorted, wrong element type.
- **T5, systematically classified across all real failures:** **12/12 (100%) of DIRECT's
  failures show a wrong tuple shape** (3 elements returned instead of the required 2).
  **Only 2/8 of STEPWISE's failures show that shape error; the other 6/8 (75%) get the
  shape exactly right and fail on winner selection alone.** Concrete cited example
  (DIRECT, seed=1077876896, world=2, rep=1): entries include a genuine tie
  (`dot`/`fay` both score=2, tag=`pekir`); expected `('dot', 2)` (alphabetical tiebreak
  correctly applied); actual `('fay', 2, 'pekir')` — wrong winner **and** wrong shape,
  compounded.
- **T6, WORKED_EXAMPLE's specific collapse:** of 10 real failures, 9 are false negatives
  (`actual=False, expected=True`), 0 are false positives, 1 unparseable from the tail
  alone. Read the actual generated code for the clearest case (seed=2000583677,
  world=1, rep=0):
  ```python
  def is_winner(entries, name):
      tag_priority = {'medaj': 1, 'jirow': 2, 'rojav': 3, 'pazeg': 4}
      def rank(entry):
          _, score, tag = entry
          return (-score, -tag_priority[tag], entry[0])
      return rank(entries[0]) == max(entries, key=rank)
  ```
  **This never uses the `name` parameter at all** — it checks whether `entries[0]` (the
  first entry) happens to be the winner, and compares a *derived rank-tuple* against a
  *raw entry* with `==`, which are structurally never equal — this specific
  implementation can, as written, essentially never return True. **Checked 3 further
  WORKED_EXAMPLE/T6 failures rather than generalizing from n=1**, and the hypothesis of
  "one single recurring bug" **does not hold** — the other three show genuinely different
  bug shapes (one correctly uses `name` but has a separate alphabetical-tiebreak-polarity
  bug in its `max()` key; one constructs a synthetic fake entry `(name, 0, '')` instead of
  locating the real entry matching `name` inside `entries`). **OBSERVED, stated
  honestly**: WORKED_EXAMPLE's T6 collapse is real and robust across all 3 worlds, but is
  produced by at least 3 distinct code-level bug shapes, all clustering around
  mishandling or ignoring the specific-entry-identification step the task requires — not
  one single repeated mistake.

**Important honest limitation, not glossed over:** DIRECT's near-universal shape bug on
T5 (12/12) makes it impossible to separately judge DIRECT's underlying tie-break/ordering
logic quality on that task — it almost never gets far enough past the shape error to be
judged on selection logic alone. Comparing raw ordering-error counts across all 12 real
attempts per strategy (not just failures) shows STEPWISE actually produces *more* raw
tie-break errors on T5 (4/12) than DIRECT's one clean case of pure ordering failure
(1/12) — but this comparison is confounded by DIRECT's shape bug masking most of its own
attempts. **I am not claiming DIRECT's tie-break logic is worse or better than
STEPWISE's** — the evidence available cannot cleanly separate the two questions.

---

## 9. Exploratory pre-action-property relationships — handled carefully, per instruction

**A genuinely important, honest finding here is methodological, not just substantive.**
The clearest pattern in the dataset (T2 and T5 both showing DIRECT's shape-extraction
collapse, T6 showing WORKED_EXAMPLE's parameter-mishandling collapse) does **not** map
cleanly onto any of the four dimensions pre-declared in `dimensions.py` before Stage 1
ran. T2's `return_type` is `list`, T5's is `tuple` — different pre-declared categories,
yet both share the real property "the required output must extract *fewer* fields than
the raw input entry carries" (name-only from a 3-tuple; name+score from a 3-tuple) — a
property I did not declare in advance. **This is precisely the shape of post-hoc feature
invention Section 9 and the frozen protocol's own Section 11 exist to guard against.**

**I am treating this pattern strictly as hypothesis-generating, not as satisfying any
trigger.** It does not retroactively qualify for the already-frozen Stage 2 mechanism
(which is scoped only to the four originally-declared dimensions, of which only
`return_type` was ever eligible, and `return_type` itself does not cleanly capture this
pattern). If a future, *separately and freshly pre-registered* study wanted to test this
specific property (name: something like "does the required output need field-extraction
narrower than the raw input entry"), it would need to declare that dimension **before**
collecting any new data, exactly as this document's own frozen predecessor required for
`return_type`.

---

## 10. Three kinds of signal, kept separate

- **Outcome signal:** weak/inconclusive at the pre-registered, honest unit (Friedman n=6,
  p=0.0907) — this is the already-frozen, unchanged Stage-1 result.
- **Conditional action signal:** the pre-declared `return_type` grouping (Q2, already
  reported) failed adversarial inspection (T2 vs T4 disagreed). A *different*,
  non-pre-declared property (narrower-extraction-than-input) shows a much cleaner,
  world-replicated pattern — but per Section 9 above, this is exploratory only, ineligible
  for the frozen Stage 2 trigger, and would need its own fresh pre-registration.
- **Error-diagnostic signal — the strongest, best-evidenced category found in this whole
  pass:** specific, code-level, mechanistically-identified bug classes (field-extraction
  shape errors; parameter-ignoring/misidentification errors) that are real, robust across
  all 3 independent world realizations, and directly traceable to concrete generated code
  — this is qualitatively richer and more actionable than either of the above.

---

## 11. Inventory of diagnostic feedback already available — **OBSERVED**

`oracle_runner.grade()`'s real return dict already carries `output_tail`/`error_tail` —
genuine per-test diagnostic text (the specific wrong value vs. the specific expected
value, or the real exception text on a crash), not a bare boolean. This is exactly the
kind of "attempt → specific failure → information about what was wrong" data Section 11
asks about, and it **already exists in this codebase's own generation pipeline**, logged
in full in `log_stage1.jsonl` for every one of the 216 replicates.

**But nothing downstream consumes it.** Read directly:
`persistent_routing/selector.py`'s `extract_sanitized_outcome(grade_result)` explicitly
pulls **only** `grade_result["passed"]` and discards everything else — by design, per the
sanitized-feedback contract (§6 of the persistent-routing protocol). This is the correct,
deliberate choice for that experiment's own narrow question, but it means: **the richest
diagnostic information this pipeline produces is manufactured and then thrown away before
it ever reaches any decision or learning mechanism**, in every experiment in this whole
research arc to date. This gap — not a missing capability to build the *diagnostic
extraction* itself (it already exists), but a missing *consumer* of it — is the concrete,
artifact-grounded version of Section 11's abstract question.

---

## 12. Strongest non-learning (boring) explanations, and whether they survive

- **"It's just stochastic noise, no real structure"** — does not survive: T2/T5/T6's
  patterns replicate identically in direction across all 3 independent world
  realizations, and the specific bug mechanisms are visible and repeatable in the actual
  generated code, not just a numeric artifact.
- **"One pathological template dominates everything"** — partially true and stated
  plainly: T2, T5, and T6 alone drive nearly all of the interesting structure in this
  18-cell dataset; T1/T3/T4 show a much blander, DIRECT-favoring pattern. This is a real
  limitation on how far any of these findings generalize, not a reason to discount them
  within their own scope.
- **"Prompt-length effect, not structural"** — does not fully survive: STEPWISE's code is
  only modestly longer (216 vs 188 chars) and shows *zero* format-failure difference from
  DIRECT; the observed differences are in specific field-extraction/parameter-handling
  logic, not generic "more text, more room for the model to get confused."
- **"The flip-rate gap is a stochastic-sensitivity story"** — killed directly by Section
  3's decomposition: it is fully and exactly explained by each strategy's per-cell
  success-probability distribution (bimodal vs. uncertain), a different and more precise
  claim than "STEPWISE's sampling process is noisier."
- **"Small sample, could be noise"** — genuinely applies to the routing-level (Outcome E)
  conclusion, which is exactly why it was reported as inconclusive rather than a finding.
  It applies much less to the individual bug-mechanism findings (Section 8), which are
  read directly off real generated code and real diagnostic text, not derived from a
  significance test at all.

---

## 13. Action-space classification

**R4 — Error-diagnostic structure more promising than routing**, with a secondary,
narrower nod to R3 for the specific T2/T5/T6-driven pattern.

Reasoning: the routing-level question ("does DIRECT/STEPWISE/WORKED_EXAMPLE differ
globally, in a way strong enough to route between") remains, correctly, Outcome E —
inconclusive, thin, not upgraded here. But underneath that surface, this forensic pass
found real, mechanistically-traceable, world-replicated bug classes (field-extraction
shape errors; parameter-mishandling errors) that a scalar pass/fail signal completely
discards before any decision mechanism ever sees it. The richest, best-evidenced
structure in this entire dataset is not "which strategy wins" but "what specifically goes
wrong, and does a different strategy's structural nudge (STEPWISE's restatement step)
happen to suppress that specific error class." **Recommendation: further research effort
on this exact three-strategy routing question is not well justified by this dataset**
(R1's own logic partially applies to the *routing* framing specifically) — **but the
diagnostic content this dataset surfaced is worth pursuing, via a different research
primitive than routing** (R4's own recommendation): experience → diagnosis → retained
correction/hypothesis, not experience → which-fixed-prompt-wins.

---

## 14. Broader learning-primitive assessment

Mapping this whole research program (restart-persistence, persistent-routing,
strategy-characterization) against the proposed chain:

| Link | Status |
|---|---|
| experience → observation | **Demonstrated** — every experiment in this arc logs real, independently-verified observations. |
| → surprise/error/knowledge gap | **Partially demonstrated** — production Echo has real surprise/contradiction machinery (`WorldModel.surprise`, `seam_engine`), but none of this research arc's own experiments connect to it; here "error" is only ever a scalar pass/fail. |
| → candidate hypothesis / acquired information | **Weakly demonstrated** — `persistent_routing`'s Selector forms the crudest possible "hypothesis" (a per-bucket mean); this forensic pass shows far richer diagnostic hypotheses are *available* in the data but not currently formed by anything. |
| → independent validation | **Demonstrated, solidly** — `oracle_runner.grade()`'s real sandboxed execution, used throughout this whole arc. |
| → provenance-preserved belief/capability update | **Partially demonstrated** — `Selector.update()`'s content-hashing is real and rigorous, but preserves only the scalar outcome, never the diagnostic content behind it. |
| → restart persistence | **Demonstrated** — the separate, already-completed restart-persistence-of-competence experiment, and `persistent_routing`'s own S0/S1 mechanism. |
| → later autonomous retrieval/use | **Mechanically demonstrated, behaviorally not** — the persistent-routing pilot's own null result (3/3 lineages) showed retrieval happens but never changed a later decision. |
| → measurable consequence | **Not demonstrated in this research arc** (the explicit, accepted null). |
| → counterfactual removal/substitution test | **Demonstrated, and unusually rigorously** — `replay.py`'s TRUE/SHAM-reversed mechanism and the real multi-process restart/substitution intervention are a genuinely rare capability, independently verified (10/10 checks) before being trusted. |
| → accumulation | **Not demonstrated anywhere in this arc.** |

**Do not claim autonomous learning merely because pieces of the chain exist** — most of
the *mechanical* infrastructure for several links is real and well-built in this
codebase, but the links that would make the chain actually *work end to end*
(error/surprise-connected hypothesis formation, and any demonstrated measurable
consequence) are the two weakest and least-demonstrated links, and they are exactly the
two links this forensic pass's own R4 recommendation points toward next.

---

## 15. Single highest-information next question

**Does explicitly surfacing a specific, identified output-requirement violation (e.g.,
"the required output must contain exactly N fields, drawn only from {list}") as a
targeted diagnostic check or corrective signal — independent of which whole prompting
strategy is used — measurably reduce this exact class of field-extraction/shape error,
compared to switching the whole strategy?**

This reframes the next real step away from "which of three whole prompting templates to
route to" (this dataset's own routing-level answer stayed inconclusive) and toward "can a
narrow, diagnosis-informed correction fix a specifically identified failure mode" — which
is both a smaller, more testable claim and, per Sections 8–13 above, the direction this
dataset's own richest evidence actually points.

---

## Stop-condition sentence

**"Without generating anything new, the 216 completed experiences show: (a) the
strategies' failures are almost entirely semantic logic errors, not format/crash
failures; (b) the flip-rate gap between DIRECT and STEPWISE is fully explained by a
difference in per-task success bimodality, not raw generation noise; (c) three task
templates (T2, T5, T6), each robustly replicated across all 3 independent worlds, contain
real, mechanistically-traceable, differently-shaped code bugs that correlate with
strategy choice; and (d) this codebase already produces genuinely rich per-failure
diagnostic text that every experiment in this research arc has so far deliberately
discarded before it reaches any decision mechanism. They do NOT establish that any of the
three named strategies is globally superior, that a conditional routing policy would
transfer to held-out tasks, that Echo can discover or act on any of this on its own, or
that this constitutes a validated learning signal of any kind — the routing-level
question stays exactly at Outcome E, unchanged."**

Returned for adversarial review. No successor experiment designed, no model calls made,
no code, task, or strategy modified.
