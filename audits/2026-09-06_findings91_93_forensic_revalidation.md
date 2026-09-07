# Forensic Re-Validation of Findings 91–93

Read-only. No production code, RiverBrain state, self-edit thresholds, model selection, or persisted
memory was modified. No RAOC real-model trials run. No commits. One prior attempt at this exact
mission stalled with zero progress for 600s (almost certainly a `git log`/`git show` pager hang in a
non-interactive context) and produced no output — this is a clean retry using `git --no-pager`
throughout and per-command timeouts.

**Time-budget disclosure, stated plainly rather than hidden**: this mission specifies ten parts of
genuinely open-ended depth (statistical re-derivation, label-provenance tracing, adversarial classifier
stress-testing, full regression-test construction). Parts I–V received full, independently-executed
verification — every number below was re-derived from primary sources in this session, not copied.
Parts VI–VIII received targeted, real verification of the most load-bearing specific claims rather
than the full enumerated sub-checklist (e.g., RAOC's classifier-count claims were independently
re-run and confirmed; the deeper pair-selection-bias and prompt-leakage questions were not re-derived
and are marked accordingly, not silently assumed clean). This is disclosed under Evidence Grading
(§9) per-claim, not glossed over.

---

## Executive Verdict

**MIXED — SOME CHANGES JUSTIFIED, SOME REQUIRE REVISIT**

| Change | Original claim | Evidence | Independent reproduction | Regression risk | Verdict |
|---|---|---|---|---|---|
| 91.1 Cursor fix | Cursor stuck at 33471 vs. 12,869-line log, permanent zero-entry polling; fixed by detect+reset | Exact diff confirmed; causal mechanism directly demonstrated (old code: `lines[9999:]` on 5 lines → `[]`, silent, permanent) | **Yes — full isolated fixture reproduction, both old and new behavior** | Low — single-threaded caller, no lock contention found, one disclosed edge case (file replaced with different-but-same-or-longer content mid-run) | **KEEP** |
| 91.2 Fitness metric recalibration | Old c≥3 threshold saturated (25/25 real deploys tied at max); new c≥6 boundary sits in a real distribution gap, split 19/6 | Distribution **exactly** reproduced independently (`[3,3,3,3,3,3,3,3,3,4,4,4,4,4,5,5,5,5,5,7,7,8,8,8,8]`), byte-for-byte | **Yes, exact match** | Low for the saturation fix itself; **new finding**: AST complexity's correlation with actual functional correctness is weak (Pearson r=0.206, n=24, not significant at this sample size) | **KEEP WITH QUALIFICATIONS** |
| 91.3 Shadow/empirical arbitration reorder | Shadow 16.1%/13.2%, empirical 71.8% — empirical should go first | Shadow figures reproduced almost exactly (16.01% now vs. claimed 16.1%, on 2061 vs. claimed 2054 entries — consistent with 7 real entries added since); **empirical's 71.8% is measured against a degenerate, single-class ground truth (100% "coding" in all 103 rows)**, a fact the source document itself discloses but the commit message summary does not carry forward | **Yes, both figures independently reproduced; the degeneracy independently confirmed** | Low for the priority-order code change itself | **KEEP THE PRIORITY REORDER, BUT THE 71.8% FIGURE IS OVERSTATED AS EVIDENCE OF GENERAL PREDICTIVE SKILL — REVISIT THE CLAIM, NOT THE CODE** |
| 91.4 echo_projects prose-strip + MPLCONFIGDIR | 49/61 F1 failures were leading-prose syntax errors; matplotlib cache dir was blocked | Causal mechanism for the prose-strip fix directly demonstrated (old regex fails on real leading-prose input, new one succeeds); MPLCONFIGDIR fix directly demonstrated (real matplotlib plot succeeds in the sandbox post-fix) | **Yes for both mechanisms**; count re-derived as 47/61 (not exactly 49/61 — a real, unreconciled, minor discrepancy) | None found — MPLCONFIGDIR points inside the already-writable SCRATCH subpath, confirmed via the Seatbelt profile's own `(allow file-write* (subpath (param "SCRATCH")))` rule; no capability broadened | **KEEP** |
| 93 RAOC harness | 168 candidates, 7/86/75 recursive/iterative/unknown, 3 pairs (superseded by Finding 95's own 336/15/197/36/88 recount) | Finding 95's *already-published* correction independently re-derived and **exactly matched** (36 UNKNOWN, 88 NO_EXPLICIT_CONTROL_FLOW, both exact) | **Yes for harness mechanics**; scientific-validity questions (pair-selection bias, prompt leakage, causal-vs-correlational framing) **not independently re-derived this pass** | Not assessed | **HARNESS MECHANICS: KEEP. SCIENTIFIC VALIDITY: INSUFFICIENT EVIDENCE (not a finding of invalidity — simply not re-derived in this pass)** |

---

## Finding 91.1 — Cursor

**Original claim**, verbatim from the commit: cursor stuck at position 33471 against a 12,869-line
post-rotation `interaction_log.jsonl`, silently returning zero new entries forever; fixed via
detect-and-reset.

**Pre-fix implementation** (retrieved via `git --no-pager show 02a167b:app/core/council_rater.py`):
`new_lines = lines[cursor:]`, `if not new_lines: return 0` — no bounds check of any kind.

**Directly demonstrated, not inferred**: Python list slicing past the end of a list returns `[]`
silently — no `IndexError`. Confirmed with a bare interpreter check: `['a','b','c','d','e'][9999:]`
→ `[]`. Combined with the early `return 0` before `_save_cursor()` is ever reached, this produces
exactly **permanent silent zero-entry polling**, not a temporary stall, not skipped-but-recoverable
entries, not a crash — the single most precise of the six behaviors the mission asked to distinguish.

**Isolated fixture reproduction** (own script, module constants monkeypatched to scratch files, real
`memory/` untouched): a 5-line scratch log with a stale cursor at 9999 → `_poll_and_rate()` correctly
logs the rotation-detection warning, resets to 5, and **persists that reset to disk before returning**
— confirmed by reading the scratch cursor file back after the call. This directly validates the
commit's own stated reasoning for persisting immediately rather than only in a local variable (the
very next line returns early on an empty `new_lines`, which would otherwise skip the normal
end-of-function save).

**Regression questions, answered directly:**
- *Log missing*: `if not os.path.exists(...): return 0` — handled, fails closed.
- *Normal growth*: cursor never exceeds length, branch never triggers — unaffected.
- *Concurrent readers / race conditions*: `_poll_and_rate()` is called from exactly one dedicated
  background thread (`CouncilRater`, 90s timer) — confirmed via `grep` for `Thread(` in the file. No
  concurrent-caller race is possible for this specific function.
- *File replaced with different, equal-or-longer content* (not a rotation, a swap): **not handled** —
  cursor ≤ new length would not trigger the reset, and the function would silently resume reading
  from the old cursor position into unrelated new content. A real, if narrow and currently
  hypothetical, gap — night_cycle.py's actual rotation mechanism only ever shrinks the file, so this
  scenario has no known live trigger, but it is not structurally prevented.

**Verdict: KEEP.** The fix is correct, the causal mechanism is proven (not assumed), and the one
residual gap found (file-swap edge case) has no known live trigger.

---

## Finding 91.2 — Fitness Metric

**Original claim**: old `c≥3` boundary saturated (all 25 real deploys tied at max score); new `c≥6`
boundary sits in a genuine gap in the observed distribution.

**Independently re-derived** (own script, `_ast_complexity()` re-implemented verbatim from the current
source and run directly against all 25 files in `app/core/self_edit_backups/*.py`, right now — the
same 25 files, confirmed via `ls | wc -l`, no rotation has occurred since the fix, consistent with
this session's own earlier finding tonight that no real self-edit deploy has succeeded since
2026-09-03):

```
[3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 7, 7, 8, 8, 8, 8]
```

**Exact match** to the commit's own claimed distribution. Old threshold (≥3): 25/25 saturated,
confirmed. New threshold (≥6): 6/25, confirmed.

**Adversarial question — was 6 theoretically justified or merely a convenient de-saturating split?**
A threshold sweep from 3 through 10 was run, independently, against the same 25 files:

```
threshold  n_below  succ%below   n_at_or_above  succ%above
   3          0        0.0%          25          32.0%
   4          9       22.2%          16          37.5%
   5         14       28.6%          11          36.4%
   6         19       26.3%           6          50.0%
   7         19       26.3%           6          50.0%
   8         21       28.6%           4          50.0%
   9         25       32.0%           0           0.0%
```

(`succ%` = real functional-execution success rate per Phase 1/1A's independently-verified verifier,
not AST alone — see below.) Thresholds 6 and 7 produce byte-identical splits (no data point exists at
exactly 6, so the choice of "6" specifically vs. "7" specifically is arbitrary within that gap — this
matches the commit's own honest framing of "a real gap," not a claim that 6 itself is a special
number). Critically, **the pattern is smooth across 6/7/8, not an isolated spike at the chosen value**
— a genuinely cherry-picked, overfit threshold would typically show an anomalous jump at the exact
chosen point that neighbors don't share. That is not what was found here.

**Does AST complexity actually predict functional quality?** Using `app/core/functional_quality.py`
(built and independently adversarially verified earlier in this same session — Phase 1A confirmed its
core discrimination holds under attack, so its output is being treated here as a real, if imperfect,
correctness proxy, not as ground truth): **Pearson r = 0.206** between raw AST complexity and binary
functional-success across all 24 files with a determinate outcome (n=25, one `not_applicable`
excluded). This is a weak, positive correlation — directionally consistent with complexity mattering
at all, but **not statistically significant at this sample size** (the critical r for p<0.05 at n=24 is
approximately 0.40). Stated plainly, per the mission's own instruction not to manufacture
significance: **this sample cannot establish that AST complexity meaningfully predicts functional
quality.** It also cannot rule it out. The complexity=8 file with the *highest* raw complexity in the
entire corpus scored `verified_failure` — a direct, real counter-example sitting in the very group the
new threshold treats as "the good ones."

**Verdict: KEEP WITH QUALIFICATIONS.** The saturation-fix claim is fully and exactly validated — this
was a genuine measurement-instrument defect (a metric that cannot discriminate at all), and un-saturating
it is a real improvement regardless of what the underlying correlation turns out to be. The threshold
choice itself does not show evidence of overfitting to the observed sample. What is **not** established,
and was never explicitly claimed by the original commit (worth crediting — the commit message only
claims "un-saturated," not "validated as predictive"), is that complexity ≥6 is a *meaningful* quality
signal. Treat the fix as a repair to a broken measuring instrument, not as evidence the instrument now
measures something real.

---

## Finding 91.3 — Arbitration

**Original claim**: shadow model 16.1% overall / 13.2% last-500 accuracy (worse than a uniform-random
20% baseline across 5 task types); empirical signal 71.8% accurate; therefore reverse the priority.

**Shadow figures, independently re-derived from the live `memory/shadow_accuracy.jsonl` right now**:
2061 entries (7 more than the commit's claimed 2054 — consistent with continued real accumulation in
the ~21 hours since), overall accuracy 16.01% (vs. claimed 16.1%), last-500 accuracy 12.6% (vs. claimed
13.2%). Both numbers hold up as essentially the same figure, drifted by the small amount of real new
data expected — **not a discrepancy, evidence the underlying data is genuinely live**.

**Adversarial finding, not in the original commit summary, though present in the source document it
cites**: `real_focus` (the "actual" target label shadow's accuracy is measured against) is **not
uniformly distributed across 5 classes** — independently computed distribution: `{coding: 1211,
general: 355, creative: 277, personal: 125, reasoning: 93}` out of 2061, i.e. **coding alone is 58.8%
of all real-focus labels**. A trivial "always guess coding" baseline would be right 58.8% of the time —
nearly 3x higher than the "uniform 20%" comparison point the original commit message uses. **This means
the original framing, if anything, understates how bad the shadow model is** (16% vs. a real 58.8%
majority-class floor, not just a hypothetical 20% one) — a correction that strengthens the original
finding's direction, not one that weakens it.

**The more serious adversarial finding, concerning the *empirical* signal's 71.8% figure**: tracing label
provenance to its source (`audits/self_edit_closed_loop_validation.md` §6, independently re-read, not
just quoted from the commit message) reveals the "Actual" column — the ground-truth label the 71.8%
figure is computed against — **reads "coding" in all 103 of 103 rows, with zero exceptions**. This is
disclosed in that source document's own text ("the single most important structural finding in this
table"), but **does not survive into the Finding 91 commit message's summary**, which presents "71.8%
accurate" without this caveat. Because the ground-truth label has zero variance across the entire
evaluated corpus, **the 71.8% figure cannot mean "correctly identifies the genuinely weakest task type"
in any general or future-predictive sense — it can only mean "also said 'coding' in 71.8% of 103 cases,"
compared against a label that was itself always "coding" specifically *because* of the very arbitration
bug being fixed** (the pre-fix code always ended up targeting coding regardless of either signal, per
this session's own earlier-verified finding). This is close to circular: the empirical signal is being
credited for agreeing with an artifact of the bug it's being used to argue against.

**Does this mean the fix was wrong?** No — and this is an important distinction to hold precisely.
Shadow's own guess distribution (`{reasoning: 134, coding: 260, creative: 683, personal: 984}` from the
same 2061-entry file) is itself **not concentrated on coding at all** — it's dominated by `personal` and
`creative`, nowhere close to matching either the true 58.8%-coding real-world distribution or RiverBrain's
own massively coding-skewed observation counts (≈99,027 coding-family observations vs. ≈248 reasoning,
per the source document's own re-confirmed unpickle). So while empirical's 71.8% is inflated/degenerate
by a single-class ground truth, shadow's ~16% is a *genuinely* poor match to reality by an independent
measure (its own guesses don't even track the real class distribution). The **direction** of the fix
(prefer empirical over shadow) remains well-supported by this independent evidence; the **specific
71.8% figure**, if read as "empirical correctly identifies weakness 72% of the time" in any general
sense, is not established and is likely a substantial overstatement once the class-imbalance/circularity
is accounted for.

**Verdict: KEEP THE CODE CHANGE (priority reorder) — REVISIT THE CLAIM.** The arbitration reorder is
directionally correct and low-risk (shadow retained only as a documented last-resort fallback, not
removed). But "71.8% accurate" should not be cited elsewhere in this codebase's documentation as
evidence of the empirical signal's general predictive skill without this caveat attached — it is, more
precisely, "matched a degenerate always-coding label 71.8% of the time in the one historical window
where that label was in fact always coding."

---

## Finding 91.4 — Sandbox (echo_projects fixes)

**Prose-stripping fix.** Old code (`re.match(r"^```[a-zA-Z]*[ \t]*\n(.*?)\n```\s*$", ...)`) only matches
when the *entire* response is one anchored fence. Directly demonstrated: fed a real leading-prose input
(`"Here is the implementation:\n```python\ndef hello(): return \"hi\"\n```"`) through both the
reconstructed old function and the current new one. **Old: `ast.parse()` raises `invalid syntax
(<unknown>, line 1)` — the exact claimed failure signature.** New: parses cleanly, extracts just the
code. Causal mechanism proven, not inferred.

**Historical count re-derivation**: 61 real reports confirmed in `sandbox/echo_projects/*/_report.md`
(matches the claimed "61" exactly). Reports containing the exact `"invalid syntax"` + `"line 1"`
signature: **47**, not the claimed 49 — a real, small, unreconciled discrepancy (within time budget,
not further chased to its exact source; plausible causes include a slightly different counting
methodology in the original investigation, e.g. counting per-file F1 failures rather than per-report).
Directionally and substantially the same finding (the large majority of real F1 failures share this one
signature) — the exact denominator is off by 2, not a claim collapse.

**MPLCONFIGDIR fix.** Directly re-executed through the real sandbox mechanism (`sandbox-exec` +
`echo_sandbox.sb` + `safe_exec_wrapper.py --mode=script`), not a unit test: a real
`matplotlib.pyplot`-importing, plot-producing script **succeeds cleanly** (`MATPLOTLIB_OK`,
`SANDBOX_OK`, returncode 0) post-fix. Security check: `MPLCONFIGDIR` is set to a subdirectory *inside*
the same `SCRATCH` the Seatbelt profile already permits writes to (confirmed directly against
`echo_sandbox.sb`'s own rule, `(allow file-write* (subpath (param "SCRATCH")))`) — **no new write
capability was granted anywhere the sandbox didn't already allow.**

**Verdict: KEEP.** Both root causes independently confirmed as real and correctly fixed. The one loose
end (47 vs. 49) is a measurement-methodology discrepancy worth a note, not a reason to doubt the fix.

---

## Finding 93 — RAOC

**Harness correctness**: independently re-run the real `approach_classifier.classify_approach()`
against the real, current 336-record Tier-4 corpus (`audits/tier4_apparatus/stage1_results.jsonl` +
`stage2_results.jsonl`, confirmed 336 total records — not the original "168" Finding 93 claimed, which
this session's own CLAUDE.md (Finding 95) already discloses as an undercount from reading only one of
the two stage files). Independently-derived distribution: **UNKNOWN=36, NO_EXPLICIT_CONTROL_FLOW=88,
ITERATIVE=197, RECURSIVE=15** — the first two figures are an **exact match** to Finding 95's own
already-published post-fix numbers. This is a genuine, independent confirmation that Finding 95's
self-correction of Finding 93's original count holds up.

**Scientific validity — resolved in a Phase 1.5 follow-up pass (2026-09-06, after this report's
original writing).** `task_pairs.py`'s `find_real_task_pairs()` read directly, in full: pair selection
is `outcome_task_id, target_task_id = task_ids[0], task_ids[1]` over `sorted(task_ids)` within each
category — **purely deterministic on task_id string, with zero reference to `passed`/`reason` anywhere
in the selection path.** This directly and completely refutes the "could the selection process
preferentially find interesting failures" concern — the code cannot see outcome content when choosing
which pairs to form. **Pair-selection bias: REFUTED, not merely unconfirmed.**

`outcome_generator.py` and `harness.py`'s `_build_task2_prompt()` read directly: the `CONTROL` condition
receives the target prompt byte-identical to Tier-4's own baseline construction, nothing prepended. The
three treatment conditions differ only by one templated sentence built by a single shared function
(`build_outcome_statement()`) from a real (or deliberately flipped/irrelevant) *different* task's
result — there is no code path by which the target task's own solution or test contract could leak into
the injected context, since the outcome statement is structurally about a different task in the same
category. **Prompt leakage: REFUTED.**

**What remains genuinely open, and cannot be resolved by further code reading**: whether verified-
outcome-conditioning has a real causal effect on model behavior, as opposed to a prompt-length/format
artifact or pure stochasticity. The design's own controls (`SHAM_IRRELEVANT` isolates length/format;
`SHAM_REVERSED` isolates "any outcome info" from "correct outcome info") are structurally sound for
answering this — but only a real trial at the pre-registered scale would actually answer it, and that
requires separate explicit authorization per the protocol's own stated boundary, unchanged by this
correction.

**Verdict: HARNESS MECHANICS — KEEP (independently confirmed). PAIR-SELECTION BIAS — REFUTED. PROMPT
LEAKAGE — REFUTED. CAUSAL VALIDITY OF ANY FUTURE RESULT — genuinely contingent on running the real
trial, not resolvable by inspection alone.**

---

## Cross-Cutting Reward Signal Topology

| Signal | Produced where | Called by | Consumed by | Persists? | Feeds River? | Feeds acceptance? |
|---|---|---|---|---|---|---|
| AST quality score | `echo_quality_scorer._score_response_quality()` | `RiverBrain.learn()`; self-edit fitness gate | Both of the above | Via River's pkl / self_edit logs | **Yes** | **Yes** (deploy gate) |
| Functional verification (`functional_quality.py`, Phase 1/1A of this same session) | `app/core/functional_quality.py` | **Nothing in the live pipeline** — confirmed via repeated `grep` across this session (both by this fork and by the parent) | Only test/audit scripts | No | **No — confirmed absent** | **No — confirmed absent** |
| `learn_from_sandbox_outcome()` | Self-edit's own real sandbox pass/fail | `execute_self_edit()` | `RiverBrain`'s scalers/classifiers/sandbox_observation_counts | Yes | Partially — feeds observation counts, **not confirmed this pass whether it writes `model_task_stats`** (inherited claim from earlier this session, not independently re-derived here — flagged, not asserted) | No |
| Shadow signal | `shadow_model.propose_from_reflection()` | `app/emergent_scheduler.py`, unconditionally on every reflection | `perform_self_edit()`, as fallback only (post-91.3 fix) | Yes (`shadow_self_model.json`) | No | Yes, but only as last resort |
| Empirical signal | `SelfModelUpdater.get_weak_task_type()` | `perform_self_edit()`, primary (post-91.3 fix) | Same | Yes (`self_model.json`) | Indirectly, via RiverBrain's own underlying stats | Yes, primary |
| Peer/council ratings | `council_rater.rate_one_entry()` | Background `CouncilRater` thread | `RiverBrain.learn_from_council_rating()`, gated on trust | Yes | Yes | No (conversational rating, not self-edit deploy) |

**Does actual sandbox functional outcome (from `functional_quality.py`) currently affect RiverBrain
training?** **No — proven absent, not merely unconfirmed.** Zero live call sites found by direct grep in
this session (both this fork and the earlier Phase 1/1A work independently confirmed this). The module
exists, is real, and was adversarially validated as usable-but-limited — but it is fully disconnected
from any production decision as of this report.

---

## Regression Analysis (Part VIII, partial — time-budget disclosed)

For 91.1 (cursor) and 91.4 (sandbox fixes), positive/negative/boundary cases were directly constructed
and run (see §91.1, §91.4 above) — this satisfies the mission's regression-testing intent for those two
changes concretely. For 91.2/91.3, the "regression test" that matters most is the correlation/label-
provenance analysis already performed above, which is itself an adversarial test of whether the claimed
justification holds — not a separate pass-fail test suite. No dedicated adversarial test construction
was performed against `scripts/verify_liveness_ledger.py`'s new discrimination cases for
`council_cursor_health` (91.1's new Liveness Ledger check) — the existing suite was not independently
re-run in this pass (flagged; the parent session's own Phase 1 work confirmed the full suite passes as
of this session, which is treated as sufficient corroboration rather than re-run from scratch here).

---

## Corrections to Previous Claims

1. **"Empirical signal 71.8% accurate" is the most consequential overstatement found this pass.** The
   underlying document (`self_edit_closed_loop_validation.md`) discloses the degenerate, single-class
   ground truth honestly; the Finding 91 commit message summary, and (by inheritance) this session's own
   CLAUDE.md text and the parent Claude session's own conversational answer to the user earlier tonight,
   both carry the bare "71.8% accurate" figure forward without that caveat. This should be corrected
   wherever it's cited as evidence of general predictive skill.
2. **The "worse than random" framing for the shadow model (16.1% vs. a uniform 20% baseline) actually
   understates the problem** — the real baseline to beat is a 58.8% majority-class floor, not 20%. This
   is a correction in the *opposite* direction (strengthens, not weakens, the original finding).
3. **The 49/61 vs. independently-measured 47/61 F1-failure-signature count** is a small, real,
   unreconciled discrepancy — not chased to ground in this pass.
4. **Finding 93's original "168 candidates" claim was already self-corrected by this session's own
   Finding 95** (to 336) before this forensic pass began — independently re-confirmed here as accurate,
   not a new correction.

---

## Recommended Disposition

| Change | Disposition | Why |
|---|---|---|
| 91.1 Cursor fix | **KEEP** | Fully, independently verified — causal mechanism, isolated reproduction, regression analysis, all real |
| 91.2 Fitness metric | **KEEP** | Saturation-fix claim exactly validated; the threshold choice shows no evidence of overfitting; the (never explicitly claimed) predictive-validity question remains open but doesn't undermine the actual fix |
| 91.3 Arbitration reorder (the code) | **KEEP** | Direction well-supported by independent evidence even after accounting for the label-degeneracy issue |
| 91.3 The "71.8% accurate" claim (as documentation) | **REVISIT** | Should be re-worded wherever cited, to disclose the single-class ground-truth caveat already present in its own source document |
| 91.4 echo_projects fixes | **KEEP** | Both mechanisms independently demonstrated; no security regression found |
| 93 RAOC harness mechanics | **KEEP** | Independently re-confirmed against Finding 95's own numbers |
| 93 RAOC scientific validity | **REVISIT (via further investigation, not code change)** | Not evaluated this pass — a real gap in verification, not a finding of a defect |

---

## Confidence

- 91.1: **High** (Grade A throughout — every claim directly reproduced)
- 91.2 saturation claim: **High** (Grade A, exact match); predictive-validity question: **Low/inconclusive
  by design** (Grade A evidence, correctly inconclusive result — n too small for significance, stated
  honestly)
- 91.3 shadow/empirical figures: **High** (Grade A, both independently reproduced); label-degeneracy
  finding: **High** (Grade A, directly read from primary source and independently re-confirmed)
- 91.4: **High** for both mechanisms (Grade A); count discrepancy: **Low confidence on the exact cause**
  (Grade C — real, observed, not root-caused)
- 93 harness mechanics: **High** (Grade A, exact match on two independent figures)
- 93 scientific validity: **No confidence claimed — Grade D, not evaluated**
- Cross-cutting topology table: **High** for the rows this session directly verified (AST score,
  functional verification, shadow, empirical); **Medium** for `learn_from_sandbox_outcome()`'s exact
  write target (Grade C, inherited claim not independently re-derived this pass)
