# Adversarial Review: K2 Strategy-Characterization Protocol

**Reviewing:** `audits/2026-09-27_strategy_characterization_protocol_design.md`
**Method:** read-only, self-review (no independent agent spawned — this review is of my
own design, so per this project's own `feral-independent-review` discipline I'm holding
it to the standard of "did I actually try to break this," not "does it look careful").
No model generations. No code written. No production changes.

**Verdict, stated up front per the mission's requirement: REVISE BEFORE EXECUTION.**

Two defects were found that are serious enough to block authorization as originally
written; both are corrected below directly in the frozen document (permitted per the
mission's own instruction — modification is allowed once a specific defect is identified
and documented, which is what follows). No data-collection mechanics changed: same 216
generations, same tasks, same strategies, same seeds, same grading, same holdout split.
Only the analysis/interpretation plan and one dimension-eligibility claim are corrected.

---

## Experimental unit — stated exactly, per test

| Test | Stated unit (original doc) | Actual independent unit |
|---|---|---|
| Q1 global (Friedman/Wilcoxon) | 18 "paired blocks" (6 tasks × 3 worlds), each block = 1 cell-mean per strategy from k=4 repeats | **Two nested units, not one**: 6 task-templates (fixed, exhaustive — not a sample from a larger population) × 3 worlds (a genuine random factor) nested within template. Worlds within the same template are correlated (same underlying skill, same procedure_text structure); repeats within a cell are pure generation noise, already correctly excluded from being counted as "N" by the cell-mean aggregation — that part was right. |
| Q2 conditional | "up to 4 dimension levels" across 6 tasks | Per-dimension, exact task counts per level (below) — for 3 of 4 dimensions, level counts are so low that within-level replication is literally 1, which is not "underpowered," it's confounded. |
| Q3 noise | k=4 repeats per cell, pooled across 54 cells | Correctly isolated from task diversity by construction (task+world held fixed across repeats) — this part of the original design was sound. |
| Q4 oracle ceiling | naive + split-sample, at n=18 | Inherits Q1's same clustering ambiguity; the split-sample correction's own selection step is itself noisy (n=2 per side). |

The generation count (216) does **not** overstate itself in the way "216 independent
samples" would — the original design already correctly aggregates the 4 repeats into one
cell-mean before testing, so it was never proposing to treat 216 raw outcomes as 216
independent data points. **The real problem is one level up**: it proposed treating the
**18 (task, world) cells** as 18 mutually independent blocks, when only 6 of those are
truly independent (the 6 task templates); the 3 worlds per template are within-template
replicates, not fresh independent templates.

---

## Audit Q1 — Global strategy effect: can the frozen analysis answer this?

**Not as originally specified, at the corrected/conservative unit — but a fix exists
using the same tools already chosen.**

I computed the exact consequence of using the conservative n=6 (one independent unit per
template, pooling that template's 3 worlds × 4 repeats into one mean per strategy) rather
than the pooled n=18:

- **Wilcoxon signed-rank, n=6, no ties:** the most extreme possible outcome (all 6
  templates favor the same strategy, unanimously) has exact two-sided p = 2/2⁶ =
  **0.03125**. The frozen document's own pre-registered corrected threshold is α =
  0.05/3 ≈ **0.0167**. **0.03125 > 0.0167** — meaning a perfect, unanimous 6/6-template
  result would still fail the pre-registered significance bar. No pairwise comparison at
  the honest, non-pseudoreplicated unit of analysis can ever reach the stated threshold
  in this design, regardless of the true effect size. This is a hard mathematical fact
  about n=6 combined with a 3-comparison Bonferroni correction, not a judgment call.
- **Friedman omnibus, n=6, k=3 treatments:** by contrast, the omnibus test **can** reach
  significance at this n — the most extreme possible pattern (the same 3-way rank order
  in every one of the 6 blocks) occurs in 6 of 6⁶ = 46,656 possible joint-rank
  assignments, giving exact p = 6/46,656 ≈ **0.00013**, comfortably below any reasonable
  α. Friedman uses more information per block (a full 3-way ranking, not one pairwise
  sign) and is meaningfully more powerful at this scale.

**Fix applied to the frozen document (Section 7, 8):** the template-level (n=6) Friedman
omnibus is now the **primary, confirmatory** test for Q1. Pairwise comparisons — whether
run at the conservative n=6 or the pooled n=18 — are demoted to **descriptive/exploratory**
status, with n=6 pairwise results explicitly flagged as structurally unable to reach
corrected significance regardless of effect size, and n=18 pairwise results explicitly
flagged as using an anti-conservative unit that likely overstates independence. No new
test was invented — Friedman and Wilcoxon were already the chosen tools; this fix is a
change in which result is load-bearing, not a new method.

---

## Audit Q2 — Conditional strategy effect: is there enough task diversity to test this?

Checked exact within-level replication for each pre-declared dimension against the 6
real T-tasks (`tasks_v2.py`'s `KT["K2"]`, already read directly for the original design):

| Dimension | Level counts among the 6 T-tasks | Verdict |
|---|---|---|
| `operation` | select_best:1, full_order:1, select_worst:1, partial_order:1, select_extract:1, membership_check:1 — **every level has exactly 1 task** | **Structurally untestable, not merely underpowered.** With n=1 per level, any apparent "operation effect" is perfectly confounded with that one task's own individual idiosyncrasy — there is no statistical way to distinguish the two. |
| `arg_count` | 1-arg:5, 2-arg:1 | **Near-total confound.** The entire "2-arg" level is one task (T6). Any apparent arg-count effect is indistinguishable from a T6-specific effect. |
| `output_cardinality` | scalar:4, bounded:1, full:1 | **Near-total confound** for 2 of 3 levels, same shape as arg_count. |
| `return_type` | str:2, list:2, tuple:1, bool:1 | The **only** dimension with any (still thin) within-level replication — 2 vs. 2 is the best case this task registry can offer. |

**This is a stronger statement than the original document made.** The original design
correctly called Q2 "underpowered... by construction" but did not disclose that 3 of its
4 declared dimensions are not merely thin but **mathematically incapable** of separating
a characteristic-level effect from a single-task effect, because n=1 per level admits no
within-level variance to compare against. Only `return_type` can, in principle, support
even a qualitative signal — and only with a 2-vs-2 split.

**Downstream consequence for Stage 2, also disclosed but understated originally:** the
held-out S-task set has the same thinness for `return_type` (str-like: S1, S3; list-like:
S2, S4 — again a 2-vs-2 split at best). **Even a full, "confirmed" Outcome C from this
exact task registry rests on a 2-vs-2 discovery pattern validated against a 2-vs-2
confirmation set** — real signal if it appears and survives, but nowhere near the
evidentiary weight "conditional superiority, learnable routing signal" ordinarily implies.

**Fix applied to the frozen document (Section 2, 10):** `operation` and `arg_count`
reclassified as structurally untestable (not "exploratory-but-thin"); `return_type`
retained as the sole eligible Q2 dimension; Outcome C's interpretation explicitly
downgraded to "a candidate signal warranting a properly-powered follow-up," not full
validation, given this registry's ceiling — stated plainly rather than let the label
"Outcome C" imply more rigor than 2-vs-2-vs-2-vs-2 evidence can support.

---

## Audit Q3 — Within-strategy noise: is k=4 useful, and is it kept separate from task diversity?

**The original design's core mechanism here was already sound** — the 4 repeats hold
task and world fixed and vary only the generation seed, so noise and task-diversity are
mechanically un-confusable by construction (there was never a path for repeat-variance to
be mistaken for task-variance in the design itself).

**One real gap, minor:** the original design pooled flip-rate across all 54 cells into
one overall noise number. This risks masking real heterogeneity — noise could plausibly
differ by strategy (e.g., STEPWISE's extra reasoning step could genuinely raise or lower
repeat-to-repeat variance relative to DIRECT) or by task. **Fix applied:** report
flip-rate broken out per strategy (18 cells each) in addition to the pooled figure — a
free addition to an analysis that's already being run, not new data collection.

---

## Audit Q4 — Oracle ceiling: selection bias and what the corrected estimate can support

The split-sample correction (repeats 1–2 to select, repeats 3–4 to validate) is the right
shape to remove selection bias, and I'm not replacing it. Two things the original
document under-stated:

1. **The correction removes bias but not noise.** The "pick the apparent best strategy"
   step is choosing among proportions estimated from only n=2 Bernoulli draws per
   strategy per cell — a highly noisy selection criterion in its own right (near-ties
   will be common even under a real underlying difference). The corrected ceiling should
   be read as a **rough, exploratory bound**, not a precise figure — stated now
   explicitly rather than left implicit.
2. **It inherits Q1's unit-of-analysis ambiguity.** The ceiling should be reported at
   both the conservative (n=6, per-template) and pooled (n=18) level, for the same reason
   Q1's significance test now is.

Does the corrected estimate answer "how much actionable performance opportunity exists"?
**Yes, in kind** — that is the right question for an oracle-ceiling calculation to
target — but given both caveats above, only as a rough order-of-magnitude figure, and per
the mission's own standing warning (already in the frozen document), it demonstrates
opportunity, never learnability.

**Fix applied:** both caveats added explicitly to Section 7's Q4 write-up.

---

## Audit Q5 — Discovery → Confirmation logic: is the freeze operationally real?

The original Section 9 said the hypothesis "is written down and frozen before any Stage 2
call is made" but did not specify **exactly what** gets written down — a real gap between
stating the *principle* of pre-registration and actually *operationalizing* it in a way
that can't quietly drift.

**Fix applied:** Section 9 now requires an explicit, literal, timestamped freeze record
containing all five of: (1) the specific dimension value that triggered Stage 2 — given
Q2's corrected scope, this can now only ever be a `return_type` value; (2) the
specifically predicted winning strategy; (3) the specific comparator strategy the
prediction is made against; (4) the exact test to be run on Stage 2 data (a one-sided
Wilcoxon/sign test, matching a directional confirmation rather than Stage 1's exploratory
two-sided tests); (5) the exact α and threshold, fixed before any Stage 2 generation.

One genuine silver lining surfaced by the Q2 correction: since `operation` and
`arg_count` are no longer eligible candidates at all, the "garden of forking paths" for
what Stage 2 could be triggered by is narrower than the original 4-dimension framing
implied — there is really only one live candidate dimension left to freeze a hypothesis
about, which reduces (without eliminating) the multiple-comparisons risk Q5 exists to
guard against.

---

## Audit Q6 — What result matters for learning?

**Largely already correct in the original document — confirmed, not revised.** Section
10's original interpretation matrix already scoped Outcome B ("global winner") to "adopt
it as a fixed default; adaptive routing unnecessary," explicitly distinct from Outcome C;
Section 14 already stated directly "Outcome B... does *not* justify returning to
learning." This is the distinction the mission asked me to confirm, and it holds up under
review without needing invention.

**One tightening added anyway**, to close a plausible skim-reading failure mode: a bolded,
explicit sentence added to Section 10 stating that a significant Q1 result **alone**,
without Outcome C's held-out confirmation, must never be reported as evidence that
adaptive routing is useful — naming the exact prohibited misreading directly rather than
leaving it only implied by the matrix's structure.

---

## Audit Q7 — Power, recalculated at the actual independent unit

**The original claim ("~30–40 percentage points, detectable via Wilcoxon at n=18") is
true only of the anti-conservative, pooled n=18 unit, and is misleading if read (as a
reasonable reader would) as applying to a properly independent unit of analysis.**

At the corrected, conservative unit (n=6 templates):
- **No pairwise comparison can reach the pre-registered corrected significance threshold
  at any effect size** — the mathematical ceiling on achievable significance (min exact
  p = 0.03125) sits above the required α (0.0167), independent of how large the real
  effect is. This is not a "detects large effects only" statement — it's a **cannot
  detect anything via this specific test at this n, full stop** statement, which is a
  categorically different and more serious limitation than "underpowered for small
  effects."
- **The Friedman omnibus at n=6 remains genuinely informative** — it can detect a very
  strong, broadly consistent global ranking pattern (formally, the theoretical ceiling is
  p≈0.00013 for a perfectly unanimous pattern; realistically, a strong-but-imperfect
  pattern — e.g., 5 of 6 templates agreeing — would still likely clear a conventional
  α=0.05, thoughI have not computed every intermediate case exactly here and am not
  claiming more precision than that).

I am **not** increasing the call budget in response to this, per the mission's explicit
instruction. The honest statement, now in the document: *this design can detect a very
strong global (omnibus) strategy-ranking pattern; it cannot, at any effect size, produce
a statistically defensible single pairwise strategy winner at the properly conservative
unit of analysis; any pairwise-level claim must rely on the explicitly-flagged
anti-conservative n=18 analysis and treat it as exploratory, pending the Stage 2
held-out check.*

**Fix applied to Section 8**, replacing the original headline claim with the corrected
one above.

---

## Summary of changes applied to the frozen document

1. §2 — `operation` and `arg_count` reclassified as structurally untestable (n=1 or
   near-n=1 per level), not merely thin; `return_type` (2-vs-2, best case) named as the
   sole eligible Q2 dimension; the S-holdout's matching thinness (2-vs-2) disclosed as a
   ceiling on what any confirmed Outcome C could mean here.
2. §7 — template-level (n=6) Friedman promoted to the primary Q1 test; pairwise Wilcoxon
   (at either n=6 or pooled n=18) demoted to descriptive/exploratory, each with its own
   disclosed limitation stated explicitly; Q3 flip-rate now reported per-strategy in
   addition to pooled; Q4's two under-stated caveats (selection-step noise; unit-of-
   analysis ambiguity) made explicit.
3. §8 — power claim corrected: n=6 pairwise tests cannot reach the corrected threshold at
   any effect size (stated as a hard fact, not an estimate); Friedman-at-n=6's real
   (strong-effects-only) sensitivity stated in its place; the original n=18-based
   "~30–40pp" figure retained but explicitly re-labeled as describing only the secondary,
   anti-conservative pooled analysis.
4. §9 — an explicit, itemized, timestamp-required freeze record (dimension value,
   predicted winner, comparator, exact test, exact threshold) added as a hard
   precondition for any Stage 2 call.
5. §10 / §14 — Outcome C's claimed strength downgraded to match Q2's real ceiling
   ("candidate signal warranting further work," not full validation); one explicit,
   bolded sentence added guarding against a lone significant Q1 result being reported as
   evidence for adaptive routing.

**None of these changes touch data collection**: same 216 generations, same 6 T-tasks and
4 S-tasks, same 3 strategies unmodified, same 3 worlds, same k=4 repeats, same seeding
scheme, same grader, same holdout split, same overall budget and runtime estimate.

---

## Final verdict

**REVISE BEFORE EXECUTION** — as the document stood before this review. The corrections
above have now been applied directly to
`audits/2026-09-27_strategy_characterization_protocol_design.md`. I have not
re-authorized it myself; the revised document is being returned, alongside this review,
for Gremlin's and ChatGPT's own confirmation that the corrected analysis plan is
acceptable before any execution is authorized.

---

## What we will be entitled to say if this experiment (as corrected) returns a positive result

- If the **template-level Friedman omnibus (n=6)** is significant: "there is evidence of
  a real, non-noise global ranking among DIRECT/STEPWISE/WORKED_EXAMPLE for this exact
  task family, model, and generation setting" — **not** which specific strategy wins with
  statistical confidence; pairwise claims stay descriptive.
- If a `return_type`-conditioned pattern is found in Discovery **and** survives the
  pre-frozen, one-sided Stage 2 confirmation on the matching S-holdout tasks: "there is a
  thin but independently confirmed association between output return-type and relative
  strategy performance, for this exact task family and strategy menu" — explicitly
  described as resting on a 2-vs-2-vs-2-vs-2 evidentiary base and warranting a
  properly-powered follow-up, not treated as an established routing policy.

## What we will still NOT be entitled to say about Echo learning

- Nothing about whether a persistent-state selector (the already-run, already-null
  persistent-routing pilot) **can actually discover, retain, and act on** whatever
  signal this study finds — this study characterizes the environment only, never a
  learning mechanism.
- Nothing beyond this exact slice: K2's task family, this exact 3-strategy menu,
  `qwen2.5-coder:7b`, temperature 0.2 — no generalization to other kinds, other models,
  other strategy sets is licensed.
- Even a full, clean Outcome C would establish only that a learnable-in-principle signal
  *exists* — it would not establish that persistent-routing learning *would succeed* at
  capturing it; that remains a separate, future, explicitly-gated question.
