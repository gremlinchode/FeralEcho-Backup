# Frozen Protocol: K2 Strategy-Characterization Study

**Status: DESIGN ONLY. IMPLEMENTATION AUTHORIZATION: NO.**
No code has been written, no directories created, no model calls made. This document is
the complete frozen design for adversarial review by Gremlin and ChatGPT before any
model call is authorized, per the mission's explicit stop condition.

**Revised 2026-09-27, after a dedicated adversarial pseudoreplication/power review**
(`audits/2026-09-27_strategy_characterization_protocol_adversarial_review.md`) — two
real defects were found and corrected here directly: (1) the original analysis plan
treated 18 (task, world) cells as fully independent blocks, when only 6 are (the 3
worlds per template are within-template replicates, not fresh templates), and at the
correspondingly conservative n=6, no pairwise strategy comparison can reach the
pre-registered Bonferroni-corrected significance threshold at *any* effect size (exact
minimum achievable p = 0.03125 > α = 0.0167) — a hard mathematical ceiling, not a power
estimate; (2) two of the four pre-declared Q2 task dimensions (`operation`, `arg_count`)
turn out to have exactly one task per level among the 6 T-templates, making them
structurally confounded with individual-task identity, not merely underpowered. Neither
defect required changing the data-collection design (same 216 generations, same tasks,
strategies, seeds, grader, holdout split) — both are corrections to the analysis and
interpretation plan, applied in place below and marked inline. See the linked review for
the full derivation.

**Provenance:** the original, pre-review version of this document is preserved verbatim
at `audits/2026-09-27_strategy_characterization_protocol_design_v1_SUPERSEDED.md`
(status: SUPERSEDED — NEVER EXECUTED). The full hash chain (original → review →
corrected) is recorded at
`audits/2026-09-27_strategy_characterization_protocol_PROVENANCE.md`. **This document,
as corrected, is the controlling frozen protocol** — Phase 0 and Stage 1 execute against
this version.

**Supersedes nothing; is gated by nothing else.** This is a standalone measurement study,
deliberately decoupled from `app/experiments/persistent_routing/` (no learning, no
persistent state, no epsilon-greedy, no reward update — see "No Learning," below). It
exists to answer the question the persistent-routing postmortem
(`audits/2026-09-27_...` — the adversarial postmortem — see conversation record; not
yet its own separately-filed audit, referenced here as "the postmortem") found
unanswered: **does this environment contain a strategy-outcome signal at all**, before
any further learning experiment is contemplated.

---

## 0. Hypothesis

**H0 (null):** DIRECT, STEPWISE, and WORKED_EXAMPLE — the exact three strategies frozen
in `app/experiments/persistent_routing/strategies.py` — do not differ in real,
independently-verified success rate on K2-family tasks by more than ordinary
generation-sampling variance, either globally or conditional on any pre-declared task
characteristic.

**H1 (strategy effect):** at least one pairwise strategy comparison shows a real,
statistically supported difference in success rate that exceeds within-strategy sampling
variance.

**H1a (conditional refinement of H1):** any such difference is systematically associated
with a pre-declared, pre-action-visible task characteristic, and that association
survives testing on genuinely held-out task instances never used to discover it.

This study is designed to distinguish H0 from H1, and — only if H1 is supported — to
attempt H1a with an explicit, pre-committed held-out confirmation stage. It is not
designed, and must not be read, as a test of whether a learner *could* discover any of
this; that is a separate, later, explicitly-gated question (see "Two closing
questions," end of document).

---

## 1. Candidate strategies — Strategy Audit Before Freeze

**Decision: (A) — characterize the exact existing three strategies, unmodified.**

Read directly from `app/experiments/persistent_routing/strategies.py` before writing
this design (not re-derived from memory):

```python
def direct(task, procedure_text):
    return _base(task, procedure_text) + "Respond with only the function in a ```python block."

def stepwise(task, procedure_text):
    return (_base(task, procedure_text)
        + "First restate the requirement as a short numbered list of exactly what the "
          "function must do, then write the function. Respond with the numbered list "
          "followed by the function in a ```python block.")

def worked_example(task, procedure_text):
    return _WORKED_EXAMPLE + _base(task, procedure_text) + "Respond with only the function in a ```python block."
```

`_WORKED_EXAMPLE` is a fixed, generic, deliberately unrelated one-shot demonstration
("return the larger of two numbers") with no structural overlap with K2's actual
difficulty (a three-level tie-break: score → tag priority → alphabetical name).

**Why (A), not (B):** the open question this study exists to answer is specifically
whether the persistent-routing pilot's own null result reflects a real absence of signal
in *its own action space*, or a design limitation. Substituting a "more obviously
different" strategy set (B) would answer a different question — whether *some* maximally
distinct action space could show a signal, which is almost certainly true trivially
(e.g., a strategy that returns `None` unconditionally) and tells us nothing about whether
the routing pilot was ever given a fair test. Characterizing (A) is the only design that
directly closes the loop the postmortem opened.

**Named, disclosed risk of choosing (A):** the audit already found a mechanistic reason
DIRECT and WORKED_EXAMPLE might be near-aliases in effect (identical closing instruction;
an off-topic demonstration). If the study returns Outcome A (no meaningful difference),
that result will be genuinely ambiguous between "prompt-framing strategies don't matter
for this task family" and "these three specific strategies happen to be poorly
differentiated as a menu." This is stated here, before data collection, precisely so it
cannot be raised only after an inconvenient result. A intentionally-distinct action set
(B) is named as a legitimate follow-on question if this study returns Outcome A or D —
not built here.

**Strategies will not be modified after seeing comparative performance**, full stop —
including after Stage 1 (Discovery), before any Stage 2 (Confirmation) is run.

---

## 2. Task set and diversity rationale

**Decision: reuse K2's existing, already-frozen task registry unmodified — do not invent
new tasks.** This is a deliberate choice, not laziness: it means no new task-generation
code needs independent verification, and it makes this study's result directly
comparable to the exact environment the persistent-routing pilot actually ran in.

**Discovery set — K2's six T-split templates** (`tasks_v2.py`, `KT["K2"]`), given the
identical real, correct `procedure_text` in every case (Blocker 1's information-parity
design is inherited unchanged — no strategy ever gets more or less solving information
than another):

| Task | Function | Args | Return type | Operation |
|---|---|---|---|---|
| T1 | `pick_winner` | 1 (`entries`) | `str` | select-best |
| T2 | `rank_all` | 1 | `list[str]` | full order |
| T3 | `pick_loser` | 1 | `str` | select-worst |
| T4 | `top_two` | 1 | `list[str]` (≤2) | partial order/select |
| T5 | `winner_with_score` | 1 | `tuple` | select + extract secondary field |
| T6 | `is_winner` | 2 (`entries, name`) | `bool` | membership/comparison check |

This table was built by reading `tasks_v2.py`'s `KT["K2"]` registry directly — **not**
via `feature_signature()`, which the postmortem showed collapses 5 of these 6 into one
lookup bucket via a shared boilerplate artifact. Documented pre-declared dimensions
(fixed **before** any outcome is examined, per the mission's requirement — these are the
only dimensions any Q2 analysis is permitted to test against):

- `return_type ∈ {str, list, tuple, bool}` (str: T1,T3 — list: T2,T4 — tuple: T5 — bool: T6)
- `arg_count ∈ {1, 2}` (1: T1–T5 — 2: T6)
- `operation ∈ {select_best, select_worst, full_order, partial_order, select_extract, membership_check}` — six distinct values, one per task (no collapsing)
- `output_cardinality ∈ {scalar, bounded_collection, full_collection}` (scalar: T1,T3,T5,T6 — bounded: T4 — full: T2)

`aggregation_vs_selection` is **not** used as a live dimension: every K2 T-task is a
selection/ranking operation over the same convention — this axis is degenerate within
K2 by construction, stated here rather than silently dropped later.

**Correction (adversarial review): two of the four dimensions above are structurally
untestable for Q2, not merely thin.** Exact within-level task counts among the 6
T-templates: `operation` has **one task per level** (6 levels, 6 tasks — no level has
more than one representative); `arg_count` is 5-vs-1 (the entire 2-arg level is a single
task, T6). With n=1 per level, there is no within-level variance to compare against — any
apparent "operation" or "arg_count" effect is mathematically indistinguishable from that
one task's own individual idiosyncrasy. These two dimensions are **removed as Q2
candidates** by this correction, not merely down-weighted. `output_cardinality` (4-1-1)
has the same near-total-confound shape for two of its three levels and is retained only
as a secondary, heavily-caveated check. **`return_type` (2 str, 2 list, 1 tuple, 1 bool)
is the sole dimension with any real within-level replication**, and even its best case
is a 2-vs-2 split — this is the only Q2 finding this task registry can ever produce with
any statistical legitimacy, and it must be reported as thin even if found. The held-out
S-task confirmation set has the identical thinness for `return_type` (str-like: S1, S3;
list-like: S2, S4 — 2-vs-2) — so even a fully-confirmed Q2 pattern from this exact
registry rests on a 2-vs-2-vs-2-vs-2 evidentiary base end to end, a real ceiling on what
Outcome C could ever mean here (see the revised Section 10).

**Confirmation set — K2's four S-split templates** (`KS["K2"]`), reserved, untouched
during Discovery, used only if Stage 2 is triggered:

| Task | Function | Structural difference from T-set |
|---|---|---|
| S1 | `pick_winner_dicts` | dict-keyed entries instead of tuples |
| S2 | `winners_by_round` | multiple independent rounds, per-round winner |
| S3 | `winner_from_text` | single delimited string requiring parsing, not a list |
| S4 | `rankings_by_round` | multiple rounds, full ranking per round |

These are genuinely structurally distinct from every T-task (different input
representation, or a repeated-substructure task shape) — a real test of transfer, not a
relabeled copy.

**No task contamination from the persistent-routing pilot:** this study reuses the *task
definitions* (public, known-to-the-model-anyway specification text), never the pilot's
own prior *generations*. All generations here are fresh, under a new, disjoint seed
namespace (Section 6) — nothing from the pilot's recorded outcomes leaks in.

---

## 3. Pairing / counterbalancing method

The comparison unit is **(task_id, world_index)** — same task, same real convention
realization, strategy varied. **3 worlds** (fresh realizations, not reused from the
pilot) × **6 T-tasks** = **18 paired blocks**. Each block is evaluated under all three
strategies (full factorial, no strategy ever restricted to a favorable subset of tasks).

**Execution order is randomized, not blocked by strategy.** A single fixed pre-registered
random permutation (seeded independently of the generation seeds — see Section 6) decides
the literal call order across the full (strategy × task × world × repeat) grid before any
call is made, so a model-state drift, thermal/load effect, or any other time-varying
confound cannot systematically align with strategy identity.

---

## 4. Same-strategy repeat structure (Q3 — sampling noise)

**k = 4 independent repeats per (task, world, strategy) cell**, each with its own
independently-derived seed (not shared across repeats, strategies, or tasks). This gives:
- 18 blocks × 3 strategies × 4 repeats = **216 total generations** for Stage 1 (Discovery).
- A per-cell empirical pass rate ∈ {0, 0.25, 0.5, 0.75, 1.0} for every (task, world,
  strategy) combination.
- A direct, non-parametric **flip-rate** estimate: the fraction of same-condition repeat
  pairs that disagree (pass vs. fail) purely from re-sampling at temperature 0.2 — this
  is the literal, measured noise floor Q1's between-strategy differences must be judged
  against, not an assumed one.

**k=4 is the frozen baseline, not an arbitrary pick — see Section 8 for its power
justification and an explicitly costed k=8 alternative**, offered rather than silently
chosen, since doubling k roughly doubles Stage 1's cost for a real, quantifiable power
gain.

---

## 5. Independent grading mechanism

Reuses the exact, already-proven `app.experiments.accumulation_probe.oracle_runner.grade()`
pipeline — real, hidden, mutation-killing test suites (`tasks_v2.make_cases2()`, the same
machinery every completed AP-0 stage and the persistent-routing pilot already trust) run
under the real kernel-level sandbox. **Not** a heuristic quality score, **not** Claude
judgment, **not** prose similarity — pass/fail comes from executing candidate code
against real, independently-constructed test cases, exactly as the mission requires.
Raw model output, extracted code, and the full grader result dict are persisted for every
one of the 216 (Stage 1) + any Stage 2 replicates, unmodified — nothing is
summarized-then-discarded.

---

## 6. Seed / determinism policy — stated precisely, not oversold

**What is seeded:** each independent replicate — one (task_id, world_index, strategy,
repeat_index) tuple — gets its own deterministic seed via
`seed_for("CHAR", f"{task_id}|{world_index}|{strategy}", repeat_index)`, a new,
dedicated namespace (`MASTER_SEED = 20260927` reused from the persistent-routing
package's own constant is available but a **new, disjoint `SEED_OFFSET = 120000`** is
used — confirmed disjoint from every prior offset in this codebase (0, 100, 5000, 5100,
7000, 40000, 90000) by the same direct token-overlap check discipline already
established, before any real call). World realizations are drawn fresh at this new
offset — never reused from the persistent-routing pilot's own `SEED_OFFSET=90000` worlds.

**Identical seeds are deliberately NOT used across strategy conditions for the same
(task, world)** — this is a considered decision, not an oversight the mission's own
question ("whether identical seeds across strategy conditions are scientifically
appropriate") flagged as needing an explicit answer. Reasoning: DIRECT, STEPWISE, and
WORKED_EXAMPLE produce genuinely different *prompt text*. A model's seed governs its
sampling RNG stream conditioned on whatever tokens precede each sampling step — applying
the identical seed value to two different prompts does not create any meaningful shared
randomness between the two outputs; it does not "control" anything across strategies the
way it controls reproducibility of the *same* prompt run twice. What actually makes this
design paired is the shared (task, world) identity, not a shared literal seed. Each
strategy still gets its own `k=4` independently-seeded repeats.

**What determinism is and isn't claimed:** a seed makes a specific (task, world,
strategy, repeat) call **re-runnable and auditable** — the same call, replayed later
against the same live Ollama server state, is expected to reproduce its logged output.
This has **not** been independently verified for byte-for-byte reproducibility anywhere
in this codebase yet (the persistent-routing pilot only verified that a seed parameter
*exists and is threaded through*, via `ollama_client.py`, not that repeated calls with an
identical seed are bit-identical). **Phase 0 of this protocol (below) is a mandatory,
cheap pre-flight smoke test — 2 real calls, identical seed and prompt, comparing output —
before any of the real 216-call budget is spent.** If that smoke test fails (the two
calls disagree), the seeded-determinism claim in this document is void and must be
re-examined before proceeding; this is stated as an explicit go/no-go gate, not an
optional nicety.

**Independent replicate, defined exactly:** one (task_id, world_index, strategy,
repeat_index) tuple, one deterministic seed, one real Ollama generation, one real
oracle-verified grade. No seed or generation is ever reused across replicates.

---

## 7. Statistical analysis plan (pre-registered)

**Primary unit of analysis, corrected:** two nested units, not one. **Task-template
(n=6) is the properly independent unit** — the 6 K2 T-templates are fixed and exhaustive
(the entire real population being characterized, not a sample of it). **World (n=3 per
template) is a within-template replicate**, not a fresh independent template — three
worlds of the same template share the same underlying skill and procedure structure.
Individual-generation-level McNemar (Tier-4's own precedent) is **not** used at all,
because it would treat each of the 4 repeats as if it were a separate independent
"task," double-counting within-cell noise as if it were between-block signal.

- **Q1 — global strategy effect, PRIMARY test:** Friedman test at the conservative,
  properly-independent **template level (n=6)** — each template's mean pass rate per
  strategy, pooled across its 3 worlds × 4 repeats. This is the test whose result is
  load-bearing for any Q1 claim. Exact minimum achievable p at n=6, k=3 (a perfectly
  consistent 3-way rank order across all 6 templates) ≈ 0.00013 — Friedman remains
  genuinely capable of detecting a strong, broadly consistent global pattern at this n
  (see Section 8 for the full derivation).
- **Q1 — pooled/pairwise, SECONDARY/EXPLORATORY only, not confirmatory:** (a) the same
  Friedman/Wilcoxon machinery re-run at the naive, pooled **n=18 (task,world) level**,
  explicitly flagged as an anti-conservative unit that treats within-template worlds as
  if they were fresh independent templates — reported for descriptive/hypothesis-
  generating purposes only; (b) pairwise Wilcoxon signed-rank tests (DIRECT-vs-STEPWISE,
  DIRECT-vs-WORKED_EXAMPLE, STEPWISE-vs-WORKED_EXAMPLE) at **Bonferroni-corrected
  α = 0.05/3 ≈ 0.0167**, run at both n=6 and pooled n=18, with an explicit, disclosed
  fact stated in advance: **at n=6, no pairwise comparison can reach this threshold at
  any effect size** (exact minimum achievable two-sided p = 2/2⁶ = 0.03125 > 0.0167,
  even for a perfect unanimous 6/6 result) — pairwise strategy-level claims are
  therefore never confirmatory in this design at the honest unit of analysis, and any
  pairwise pattern found at the pooled n=18 level is exploratory input to a possible
  Stage 2, never a standalone finding.
- **Q2 — conditional effect:** for each of the four pre-declared dimensions
  (`return_type`, `arg_count`, `operation`, `output_cardinality`), test whether the
  strategy effect differs across dimension levels (interaction test, or — given the very
  small per-level task counts this task family affords — a qualitative, explicitly
  **exploratory/hypothesis-generating-only** comparison of per-level effect direction and
  magnitude). **Stated plainly, in advance: with only 6 discovery tasks split across up
  to 4 dimension levels, Q2 is underpowered for a confirmatory claim at this sample size
  by construction.** Any pattern Q2 surfaces is a candidate hypothesis, not a finding,
  until it survives Stage 2.
- **Q3 — within-strategy noise:** reported directly as the empirical flip-rate (Section
  4), **broken out per strategy (18 cells each) in addition to the pooled figure across
  all 54 cells** (corrected: the original pooled-only figure could mask real
  heterogeneity — e.g., STEPWISE's extra reasoning step could genuinely raise or lower
  repeat-to-repeat variance relative to DIRECT; both figures cost nothing extra to
  compute from data already being collected). This is the noise floor against which
  Q1's effect sizes are interpreted, not a separate hypothesis test.
- **Q4 — oracle ceiling, corrected for overfitting:** two figures are reported, not one:
  1. **Naive in-sample ceiling** — for each of the 18 blocks, `best_strategy_rate = max`
     over the three strategies' full 4-repeat mean pass rate in that block; average
     `best_strategy_rate - DIRECT_rate` across blocks. This number is **definitionally
     inflated** (picking the best of three noisy estimates in hindsight cannot lose to
     any single one, even under pure noise) and must never be reported without the next
     figure alongside it.
  2. **Split-sample corrected ceiling** — within each block, use repeats 1–2 only to
     pick the apparent best strategy, then measure that chosen strategy's real pass rate
     on repeats 3–4 only (held out from the selection step); compare against DIRECT's own
     repeats 3–4 rate. This removes most of the selection-inflation bias and answers a
     materially more honest question: "if you had to commit to a strategy per task from
     a small sample, would that have helped." **This split-sample figure, not the naive
     one, is the number to actually interpret** — stated explicitly per the mission's own
     warning that an oracle calculation "demonstrates available opportunity, not
     learnability," and this project's own standing discipline of not letting a
     flattering number stand uncorrected next to the honest one.

  **Two further caveats, added on adversarial review, not in the original design:**
  first, the split-sample correction removes selection *bias* but not selection
  *noise* — the "which strategy looks best" step chooses among proportions estimated
  from only n=2 draws per strategy per cell, itself a highly noisy criterion (near-ties
  will be common even under a real underlying difference); the corrected ceiling should
  be read as a rough, exploratory bound, not a precise figure. Second, the ceiling
  inherits Q1's same unit-of-analysis ambiguity and should be reported at both the
  conservative n=6 (per-template) and pooled n=18 level, for the same reason Q1's
  significance test now is.

---

## 8. Sample-size / power justification — including the honest "this is not enough" case

**Corrected on adversarial review — the original version of this section understated a
hard limitation, not just a power tradeoff.** The original power claim below is real, but
applies only to the anti-conservative, pooled n=18 unit; at the properly independent,
conservative unit (n=6 templates), a categorically different and more serious limit
applies:

**At n=6 (the honest unit), no pairwise strategy comparison can reach the pre-registered
Bonferroni-corrected threshold (α=0.0167) at *any* effect size.** This is not a power
estimate — it is an exact combinatorial fact: for a Wilcoxon signed-rank test with n=6
non-tied paired differences, the most extreme possible outcome (all 6 templates
unanimously favor the same strategy) has exact two-sided p = 2/2⁶ = **0.03125**, which
exceeds 0.0167. A perfect, unanimous result across every template in the study would
still fail to clear the pre-registered bar. **Pairwise strategy-superiority claims are
therefore never statistically confirmable in this design at the honest unit of
analysis**, regardless of how large the true effect is.

**The Friedman omnibus at n=6 is not subject to this ceiling** and remains this study's
real, primary discriminating tool: for n=6 blocks and k=3 treatments, the most extreme
possible joint-rank pattern (an identical 3-way strategy order in every one of the 6
templates) has exact p = 6/6⁶ ≈ **0.00013** — comfortably significant. This design *can*
detect a very strong, broadly consistent global ranking pattern; it *cannot* certify
which specific strategy drives that pattern with statistical confidence at this n. Any
pairwise attribution therefore relies on the secondary, explicitly-flagged pooled n=18
analysis (below) as exploratory input, gated behind Stage 2 confirmation before being
trusted at all.

**No increase to the call budget was made in response to this finding**, per the
mission's explicit instruction not to reflexively add generations — the correct response
to a hard significance ceiling is to be honest about what the design can and cannot
support, not to inflate the sample size until a chosen number theoretically clears a
threshold.

**The original, pooled n=18 estimate, retained below but now explicitly scoped as
describing only the secondary/exploratory analysis, not a confirmatory one:**

For a paired non-parametric test (Wilcoxon signed-rank) at
n = 18 blocks and α = 0.0167 (Bonferroni-corrected), approximate 80% power is achievable
for a **large** paired effect (Cohen's dz ≈ 0.75–0.8) — very roughly corresponding to a
between-strategy difference in per-block mean pass rate on the order of **30–40
percentage points**, averaged across blocks, given the k=4-repeat cell noise floor. This
figure describes the anti-conservative n=18 unit only (which treats within-template
worlds as if they were independent fresh templates) — it must not be read as the design's
true, honest sensitivity.

**This design is honestly not well-powered for a Tier-4-scale effect (~10–20
percentage points)** — the closest real precedent this codebase has for what a genuine,
still-only-marginally-significant effect looks like in an adjacent problem (Finding
87/88's ARCH_COUNCIL-vs-BASE_N comparison, 11.9pp, p=0.087 at n=84 *independent* tasks).
Reaching comparable power for an effect that size, in *this* design's repeated-measures
shape, would require roughly **4–8× more blocks** (≈70–150 (task, world) pairs) — not
achievable within K2's own 6 real T-templates without diluting the design into mostly
world-replication rather than task diversity, or expanding into K1/K3 (which would
reopen the question of whether any finding generalizes across kinds, a larger and
different study).

**Stated per the mission's explicit instruction, not glossed over:** if the true effect
is Tier-4-scale rather than large, this Stage-1 budget will most likely return **Outcome
E (inconclusive)**, not a confident A. That is an accepted, disclosed property of this
budget, not a flaw discovered after the fact. A properly-powered study for a moderate
effect is a materially larger, separately-costed undertaking (Section 14) and is
**not** proposed here.

**k=4 vs. k=8, costed explicitly rather than silently decided:**

| k (repeats/cell) | Total Stage 1 calls | Est. runtime | Effect this design can reliably detect |
|---|---|---|---|
| 4 (frozen baseline) | 216 | ~40 min | large (≥~30–40pp) |
| 8 (offered alternative) | 432 | ~80 min | moderately smaller, still not Tier-4-scale |

k=4 is the frozen recommendation on cost-discipline grounds; k=8 is available at 2× cost
if more resolution is wanted before running — this choice is Gremlin/ChatGPT's to make,
not defaulted silently.

---

## 9. Held-out confirmation stage (only if Q2 surfaces a candidate)

**Trigger condition, fixed now, not chosen after seeing Stage 1 results:** Stage 2 runs
**only if** Q2's exploratory analysis shows a qualitatively clear, directionally
consistent pattern (one strategy visibly ahead of the others within a specific dimension
level, and reversed or absent in at least one other level) — not merely "some numeric
variation exists," which is expected under noise alone.

**Stage 2 design, fixed here in advance:** apply the discovered strategy pairing/pattern
to the **4 held-out S-tasks** (Section 2), using the **same sample-size formula from
Section 8**, computed from Stage 1's own observed effect size (the specific discordant
split Stage 1 found) — **before** collecting a single Stage 2 generation. This is a
legitimate, standard two-stage design (size Stage 2 from Stage 1's estimate, then collect
entirely fresh data), not data dredging, provided:
- Stage 2 uses new worlds, new seeds, disjoint from Stage 1's namespace,
- the hypothesis being tested (which strategy should win, under which dimension value)
  is written down and frozen before any Stage 2 call is made,
- Stage 2's result is reported regardless of outcome — a failed confirmation is reported
  as a failed confirmation, not quietly dropped.

If the required Stage 2 N (per Section 8's formula, applied to Stage 1's actual observed
split) is itself unreasonably large given Stage 1's effect size, that is reported
honestly as "Stage 1 found a numeric pattern too weak to afford confirming" — **not**
treated as license to lower the confirmation bar.

**Added on adversarial review — the explicit freeze record, operationalized, not just
asserted as a principle.** Given Section 2's correction (only `return_type` is an
eligible Q2 dimension at all), a candidate pattern can only ever concern that one
dimension. Before any Stage 2 generation is made, the following must be written down and
timestamped, verbatim:

1. **Dimension value** that triggered Stage 2 (necessarily a `return_type` level: str,
   list, tuple, or bool).
2. **Predicted winning strategy** for that value — one specific strategy, not "a
   pattern."
3. **Predicted comparator** — the specific strategy the prediction is made against (if
   more than one alternative exists, which one is being tested).
4. **The exact test to run on Stage 2 data** — a **one-sided** Wilcoxon/sign test on the
   matching S-holdout tasks (str-like: S1, S3; list-like: S2, S4), matching the
   directional, confirmatory nature of Stage 2 as distinct from Stage 1's exploratory
   two-sided tests.
5. **The exact α and success threshold**, fixed now: one-sided α = 0.05 for Stage 2 (a
   single, pre-specified, directional confirmation — not Stage 1's Bonferroni-corrected
   family-wise threshold, since Stage 2 tests exactly one, already-committed hypothesis).

This freeze record must exist, complete, before the first Stage 2 seed is drawn. Its
narrower scope than originally implied (one eligible dimension, not up to four) is itself
a partial mitigation of the multiple-comparisons risk this section exists to guard
against — a direct, disclosed consequence of Section 2's correction, not a separate fix.

---

## 10. Pre-registered interpretation matrix

| Outcome | Criterion | Interpretation |
|---|---|---|
| **A — Equivalent** | Friedman non-significant; all 3 pairwise Wilcoxon non-significant at corrected α; between-strategy spread ≤ within-strategy flip-rate | Abandon strategy-selection learning for this action space on K2-family tasks. |
| **B — Global winner** | ≥1 pairwise comparison significant, same direction and magnitude across all 4 dimension levels (no interaction) | One strategy dominates; adopt it as a fixed default; adaptive routing unnecessary here. |
| **C — Conditional superiority** | Q2 (necessarily `return_type` — see Section 2's correction) surfaces a directional pattern AND it survives the frozen, one-sided Stage 2 confirmation on the matching held-out S-tasks | **Corrected on review**: given this registry's 2-vs-2-vs-2-vs-2 evidentiary ceiling (Section 2), even a fully-confirmed Outcome C here should be reported as "a candidate signal warranting a properly-powered follow-up," not as full validation of a learnable routing signal — the evidentiary base is real but thin end to end. Returning to persistent/incremental policy learning is a reasonable next step to *consider*, not something this specific result alone fully justifies. |
| **D — Unpredictable difference** | ≥1 pairwise comparison significant, but no pre-declared dimension predicts direction (Q2 finds nothing coherent, or Stage 2 fails to confirm a candidate) | A real oracle opportunity exists (Section 7's Q4), but current observable task features do not support learning a useful policy from it. |
| **E — Inconclusive** | Neither A's nor B's nor D's criteria are cleanly met — e.g., underpowered null, unstable/non-reproducible effect | Report as inconclusive. **Do not** relabel as C via post-hoc reanalysis; report the honest limitation (most likely outcome given Section 8's power analysis) and state what a properly-powered follow-up would need. |

**Added on adversarial review, stated explicitly rather than left only implied by this
matrix's structure: a statistically significant Q1 result (the template-level Friedman
omnibus) BY ITSELF, without Outcome C's held-out confirmation, licenses only Outcome B's
claim — adopt a fixed default strategy — and must never be reported as evidence that
adaptive routing is useful.** The distinction was already present in the original matrix
and in Section 14 below; this sentence exists so it cannot be missed by a reader who
skims only the top-line significance result.

---

## 11. Adversarial controls — named threat, named defense

| Threat | Defense in this frozen design |
|---|---|
| Stochastic generation noise | Directly measured, not assumed: k=4 independently-seeded repeats per cell (Section 4), reported as the explicit noise floor (Q3). |
| Order effects | Full call order randomized by one pre-registered permutation across the whole grid, not blocked by strategy (Section 3). |
| Seed artifacts | Every replicate gets its own unique, disjoint, deterministically-derived seed (Section 6); Phase 0 smoke-tests the determinism claim before real spend. |
| Task difficulty imbalance | Not eliminated — modeled: task identity is a block factor in every analysis, and each task's own DIRECT baseline pass rate is reported alongside any strategy comparison. |
| Prompt-length effects | Disclosed, not hidden: STEPWISE and WORKED_EXAMPLE are both longer than DIRECT by construction; this design cannot cleanly separate "length" from "structure"/"demonstration," and says so rather than claiming isolation it doesn't have. |
| Information-content differences | Structurally ruled out, not merely controlled: all three strategies receive the identical, complete, correct `procedure_text` (inherited from the pilot's own Blocker 1 design). |
| Grader weakness | Reuses the already-proven `oracle_runner.grade()` real-sandbox test-execution pipeline — not a new, unverified grader, not a heuristic score. |
| Contamination between repeated trials | Structurally impossible, not just controlled: `strategies.py`'s `build_prompt()` has no carrier/retained-notes mechanism at all (confirmed by direct read) — every call is single-shot, stateless. |
| Investigator-selected favorable pairings | Full factorial: every strategy × every one of all 6 real T-tasks × every world; no task subset chosen for being strategy-favorable. |
| Post-hoc feature invention | The four Q2 dimensions (Section 2) are declared in this document, before Stage 1 data collection, and will not be revised afterward. |
| Multiple-comparison fishing | Bonferroni-corrected α=0.0167 fixed in advance for the 3 pairwise tests (Section 7); Q2 is explicitly labeled exploratory-only, gated behind Stage 2's independent confirmation before being trusted as a finding. |

---

## 12. Cost discipline — estimated before execution

- **Stage 1 (Discovery):** 216 real model calls (`qwen2.5-coder:7b`, same `OPTIONS` as
  the persistent-routing pilot: temperature 0.2, top_p 1.0, num_predict 512, num_ctx
  4096), each followed by one real sandboxed grade. Estimated runtime ≈ 40 minutes
  (based directly on the persistent-routing pilot's own observed ≈11s/call). Estimated
  artifact growth: low single-digit MB of JSONL (raw prompt, raw response, extracted
  code, grade dict, per replicate) — no risk to `memory/` retention budgets.
- **Stage 2 (Confirmation), conditional:** sized from Stage 1's own observed effect via
  Section 8's formula, only if Section 9's trigger condition is met. Not committed to a
  fixed number here; reported honestly if the required N is disproportionate to what
  Stage 1 found.
- **A properly-powered study for a Tier-4-scale (10–20pp) effect** would require roughly
  4–8× Stage 1's block count (≈70–150 blocks, i.e., on the order of 850–1,800 total
  generations at k=4) — **explicitly not proposed here**, named only so the cost of
  "doing this properly for a small effect" is visible rather than silently assumed away.

---

## 13. Exact stop conditions

1. Nothing in this document authorizes any model call. Execution requires separate,
   explicit authorization from Gremlin (and, per this mission's framing, adversarial
   review from ChatGPT) after reading this design.
2. Phase 0 (seed-determinism smoke test, Section 6) is a mandatory go/no-go gate before
   any of the real 216-call Stage 1 budget is spent.
3. Strategies are never modified after any outcome is observed, at any stage.
4. Stage 2 runs only if Section 9's pre-declared trigger condition is met — not by
   default, not because Stage 1 happened to finish.
5. If Stage 2's required sample size (per Section 8's formula, applied honestly to Stage
   1's own observed effect) is disproportionate, that is reported as the result, not
   silently downsized to force a confirmation.
6. No result from this study — A, B, C, D, or E — triggers any change to
   `app/experiments/persistent_routing/` or any production code by default. Any such
   follow-up is a separate, later, explicitly-authorized decision.
7. After Stage 1 (and Stage 2, if triggered) complete, the results are reported for
   adversarial review and this protocol stops — no Stage 3, no scope expansion, no
   "while we're at it" additions.

---

## 14. Two closing questions, answered directly

> **What result would convince us that strategy-selection learning should be abandoned
> for this task family?**

Outcome A (Section 10) — **corrected**: the template-level Friedman omnibus (n=6, the
primary, load-bearing test — see Section 8) non-significant, and the observed
between-strategy spread does not exceed the measured within-strategy flip-rate. (The
pairwise Wilcoxon tests are no longer part of this criterion at n=6, since they cannot
reach significance at any effect size at that unit — see Section 8 — so their being
"non-significant" is no longer informative on its own.) Also: Outcome D that is
*attempted* at Stage 2 and fails to confirm — i.e., a real difference exists somewhere,
but no pre-declared, pre-action-visible task feature predicts it even after a genuine,
pre-committed attempt to find one.

> **What result would justify returning to the persistent-learning experiment?**

Outcome C only, and even then with the caveat Section 10 now states explicitly: a
significant template-level Friedman result **and** a `return_type`-conditioned pattern
that **survives** the frozen, one-sided Stage 2 confirmation on the matching S-holdout
tasks. Given this registry's 2-vs-2-vs-2-vs-2 evidentiary ceiling (Section 2), even this
should be read as "worth a properly-powered follow-up," not as full, standalone
justification on its own. Outcome B (a global winner with no interaction) does *not*
justify returning to learning — it justifies adopting a fixed default strategy instead,
which needs no adaptive mechanism at all.

---

**End of frozen design. Returned for adversarial review. No model calls authorized.**
