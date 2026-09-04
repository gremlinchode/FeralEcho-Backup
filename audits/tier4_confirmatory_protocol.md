# Tier-4 Confirmatory Experiment: Frozen Pre-Registration Protocol

**Status at freeze time: this document is written and hashed BEFORE any Stage 1 or Stage 2 task is
authored, and BEFORE any confirmatory generation call is made.** No confirmatory outcome of any kind
has been observed by the author of this document at the time it was written. The two task suites this
protocol commits to are authored immediately after this file is hashed, using content unrelated to any
outcome (see §4).

This protocol governs a **direct follow-up** to the completed Tier-3 pilot (`audits/
tier3_heldout_execution_report.{md,json}`, `audits/tier3_heldout_scoring_analysis.{md,json}`), which
found: `BASE_1` 5/8 (62.5%), `BASE_N` 6/8 (75.0%), `ARCH_PIPELINE_ISOLATED` 4/8 (50.0%), `ARCH_COUNCIL`
3/8 (37.5%); `BASE_N` vs `ARCH_COUNCIL` discordant 3-0 in favor of `BASE_N`, exact McNemar p=0.25
(not significant at n=8). That result is **frozen historical evidence and is not modified, re-scored,
or re-interpreted by this document.**

## 1. Primary Scientific Question

> When the underlying model is held constant, does Echo's Council orchestration produce measurably
> better task performance than simply giving that same model several independent attempts plus a
> synthesis step?

## 2. Hypotheses (restated from the Tier-3 design, unchanged)

- **H1** — Architecture/integration contribution: a reproducible performance advantage for
  `ARCH_COUNCIL` over `BASE_N` at matched generative-call budget.
- **H2** — Model ceiling: the architecture cannot reliably overcome the model's limitations even given
  equal or greater budget.
- **H3** — Measurement limitation: existing evaluators fail to capture meaningful differences.
- **H4** — Orchestration/sampling advantage: any apparent Council benefit is explained by more
  attempts/diversity/selection, not new capability from orchestration itself.

## 3. Phase 1 Forensic Reconnaissance — Findings and Protocol Consequences

A full reconnaissance pass was performed on the exact apparatus (`scripts/run_tier3_apparatus.py`,
`scripts/run_capability_pilot.py`), the real production functions it calls (`app/core/
river_deliberation.py`'s `deliberate_and_learn()`, `_select_council()`, `_jittered_temperature()`,
`_warm_up_echo()`, `SYNTHESIS_SYSTEM_TEMPLATE`), and the current live (frozen, server-off) production
state, before designing this protocol. Four real findings, each with a protocol consequence stated
explicitly:

### Finding A — A real, previously undisclosed wording asymmetry favors `BASE_N`, not `ARCH_COUNCIL`

The harness's `BASEN_SYNTHESIS_SYSTEM_TEMPLATE` (`run_tier3_apparatus.py`) instructs the synthesizer to
"Weigh each attempt according to its coherence and **correctness**." The real production `
SYNTHESIS_SYSTEM_TEMPLATE` (`river_deliberation.py`, used verbatim by `ARCH_COUNCIL`'s real synthesis
call) instructs "Weigh each perspective according to its coherence and **relevance**." For a coding
task with an objectively checkable answer, explicitly cueing the synthesizer to weigh by *correctness*
is a real, plausible advantage for `BASE_N` that `ARCH_COUNCIL` structurally cannot receive, since it
uses the unmodified real production template. This asymmetry was never previously disclosed (the
harness's own comments state the two templates "mirror" each other's structure "as closely as is
honest," which is true of structure but not of this one substantive word).

**Protocol consequence**: For this confirmatory experiment, `BASEN_SYNTHESIS_SYSTEM_TEMPLATE` is
corrected to use "coherence and relevance," matching the real production wording exactly (word-for-word
on this point). This is a deliberate, disclosed deviation from the original pilot's exact template,
made because it *removes* a bias that previously favored `BASE_N` — i.e., it makes the confirmatory
test harder for `BASE_N` to win, not easier, than the pilot's own conditions. The original pilot's
result stands, unedited, with this newly-identified limitation now recorded against it.

### Finding B — Council composition is not fully deterministic, and this must be captured, not assumed away

`deliberate_and_learn()` always calls `_select_council(..., fair_sample_refresh=True)`, which has a
real, unconditional `UNDER_SAMPLED_REFRESH_PROBABILITY = 0.25` (25%) chance per call of attempting a
random swap toward whichever eligible model has fewest real observations, if any qualify (real
observation count `< river_brain._MEAN_EFFECTIVE_WINDOW`, currently 200, for that task type). Checked
directly against live, frozen production state at protocol-freeze time: every model in the current pool
(`echo:latest`, `gemma3:4b`, `qwen2.5-coder:7b`, `deepseek-r1:7b`, `qwen2.5:3b`, `llama3.2:3b`,
`llama3.1:8b`, `llama3:instruct`, `mistral:latest`) shows ≥200 real "coding" observations, so no
currently-known model qualifies as under-observed — this mechanism is expected, but not guaranteed, to
be a no-op throughout this study. Separately, `exploration_bias` (a second, independent swap mechanism)
is confirmed to evaluate to exactly `0.0` given the current real, frozen `memory/salience_state.json`
(`world_surprise: 0.0`) and `memory/echo_state.npy` (valence `+0.0637`, which if anything pushes
`exploration_bias` further *toward* zero, not away from it, per `_apply_valence_to_exploration_bias()`'s
own sign) — this specific swap path is confirmed structurally inert for this study, not merely assumed
quiet. `mlx:gemma3` is confirmed absent from the real pool (permanently retired, per Finding 74) and MLX
avoidance is confirmed currently inactive, so `mlx:qwen3` is available.

**Protocol consequence**: council composition is treated as a **possible**, not fixed, nuisance
variable. Every candidate record captures `councillor_models`/`synthesis_model`/`warmup_model`
explicitly (already true of the original apparatus's `run_condition_arch_council()`, reused unmodified
here). If composition ever varies across candidates within this study, that variation is reported
plainly as an exploratory finding, not suppressed or treated as a confound to explain away after the
fact.

### Finding C — The warm-up call has a real, disclosed operational justification, not an arbitrary asymmetry

`_warm_up_echo()`'s own docstring: "Prevents synthesis timeouts caused by councillors evicting Echo
under memory pressure." This is a genuine reliability mechanism (multiple different councillor models
loading into Ollama's limited resident-model memory can evict the synthesis model, `echo:latest`,
forcing a slow reload exactly when synthesis needs it) — not a placeholder or leftover of unclear
purpose. It plausibly *improves* `ARCH_COUNCIL`'s reliability (fewer real synthesis timeouts) at the
cost of one extra, content-discarded, real call. This nuances, without eliminating, the disclosed 5-vs-4
call asymmetry: the asymmetry is real and un-eliminated in this protocol's primary design (see §9), but
it is not an unexplained implementation quirk — it is a real production trade-off this confirmatory
experiment inherits as-is.

### Finding D — Isolation coverage is confirmed complete for `deliberate_and_learn()`, not merely assumed

A full text scan of `deliberate_and_learn()`'s body found every disk/state-mutating call
(`river_brain.learn()` ×5 call sites, `_log_council_deliberation()`, `core.publish_salience()`) is
either routed through the existing read-only proxy (`river_brain=proxy`), already monkeypatched to a
recording no-op (`_log_council_deliberation`), or gated on a condition (`exploration_bias > 0.0`)
confirmed false under current real state (Finding B). No additional, previously-uncovered production
write path was found. `install_isolation()` is reused unmodified for this study.

## 4. Sample-Size / Power Justification

**The pilot's own point estimate is explicitly not used directly for power planning.** At n=8 with only
3 discordant pairs, the observed 100%-of-discordants-favor-`BASE_N` pattern could plausibly reflect a
true population split anywhere from a modest majority to near-total — 3-for-3 is not statistically
distinguishable from, e.g., a true 75:25 split (exact binomial: P(3/3 or more extreme | p=0.75) ≈ 0.42,
non-rejectable). A conservative assumption is required.

McNemar power was computed via the normal approximation to the binomial sign test on discordant pairs
(`nd = [z_{α/2}·√0.25 + z_β·√(p₁(1-p₁))]² / (p₁-0.5)²`, then total N = nd / assumed discordant rate),
α=0.05 two-sided:

| Assumed discordant split | Assumed discordant rate | Required discordant pairs (80% power) | Required TOTAL N |
|---|---:|---:|---:|
| 95:5 (near-total, matches raw pilot direction) | 37.5% (pilot's own rate) | 6.7 | 18 |
| 85:15 (very strong) | 37.5% | 13.4 | 36 |
| 80:20 (strong, conservative-but-real) | 37.5% | 19.3 | 51 |
| 75:25 (moderate-strong) | 37.5% | 28.9 | 77 |
| 85:15 | 25% (mid-range of the pilot's 4 comparisons) | 13.4 | 54 |
| **80:20 (chosen)** | **25% (chosen)** | **19.3** | **≈77, rounded to 80** |
| 75:25 | 25% | 28.9 | 116 |
| 75:25 | 15% (conservative lower bound) | 28.9 | 193 |

**Chosen planning assumption: an 80:20 discordant split at a 25% discordant rate** — deliberately more
conservative than the pilot's own literal 100:0 split (which is very likely an artifact of only 3
discordant pairs, not a stable population estimate), and using the middle of the four pilot comparisons'
own observed discordant rates (12.5%–37.5%) rather than the highest. This is a genuine judgment call,
stated as such: it is not derived from a formal prior, but from treating the pilot's directional signal
as real-but-noisy and asking "what is the smallest total N that could still detect a large, honestly
plausible effect at 80% power" without assuming the most optimistic reading of 8 data points.

**This yields a target total N ≈ 80** (across both confirmatory stages combined; realized as N=84, see §5's disclosed pre-execution adjustment) for the primary
endpoint. This is explicitly **not** claimed to achieve 80% power for a more modest true effect (e.g.,
a 70:30 split, which per the table would require ~187 total tasks at a 25% discordant rate — outside
this study's practical compute/time budget for a single investigation). This limitation is carried
into the final report, not hidden.

## 5. Design: Two-Stage Sequential Confirmatory Experiment

- **Stage 1**: 42 fresh, never-before-used held-out tasks, all 4 arms, McNemar computed on Stage 1
  alone as an interim analysis.
- **Stage 2**: 42 additional fresh, disjoint held-out tasks (a **separate, independently-authored**
  suite — not a re-run of Stage 1's tasks), executed only if Stage 1's interim rule (§6) does not permit
  early stopping. McNemar computed on the pooled n=84.

**Pre-execution revision, disclosed (2026-09-04, before Stage 1 execution begins, permitted under §17
since no execution has occurred yet):** the task pool was authored as 84 candidate tasks (14 per
category × 6 categories) specifically so that every reference solution could be independently verified
against the real sandbox before any were frozen (see `scripts/tier4_verify_task_pool.py`'s full run —
84/84 reference solutions confirmed correct after one authoring bug in a test's own expected value was
found and fixed, `bf05`'s `rotate_right` case). Splitting 40/40 from this pool would have meant
arbitrarily discarding 4 already-verified, good tasks for no scientific reason. Using all 84 (42/stage,
a clean 7-per-category-per-stage split) instead is a strictly conservative adjustment — more data,
raising power slightly above the §4 target rather than below it — made before any task suite was hashed
or any confirmatory generation call was issued, and applied uniformly (not selected based on any
outcome, since no outcome existed yet to select on).
- Both suites are authored and hash-frozen **before Stage 1 execution begins** (see §4 of the mission
  instructions: "If a single large suite is impractical, design sequential batches with predefined
  stopping rules" — implemented here as freeze-both-first, execute-sequentially, to remove any
  possibility of Stage 2's task design being influenced by Stage 1's outcome).
- Maximum 2 stages under this protocol. Any further extension requires a new, separately pre-registered
  protocol — not a default continuation.

## 6. Sequential Stopping Rule (pre-registered, approximate O'Brien-Fleming-style two-look boundary)

**Disclosed limitation on rigor**: this is an approximate implementation using standard published
two-look O'Brien-Fleming boundary values (Stage 1 nominal α≈0.0052, Stage 2 cumulative nominal α≈0.048,
for two equally-sized looks at overall two-sided α=0.05), not a formally re-derived alpha-spending
function computed from this specific design's exact information fraction. This is stated as an honest
approximation, not a formal guarantee of exact family-wise error control.

- **After Stage 1** (n=40): compute exact two-sided McNemar p for `BASE_N` vs `ARCH_COUNCIL`.
  - **Stop early and declare the Stage-1-only result as final** only if ALL of: (a) p ≤ 0.0052, (b)
    absolute effect size ≥ 25pp, (c) all discordant pairs favor the same direction (no reversal).
  - Otherwise, proceed to Stage 2 regardless of how the Stage 1 point estimate looks (including if it
    looks favorable to `ARCH_COUNCIL` — replication is pursued precisely because a single-suite result,
    however clean, is weaker evidence than one that survives an independent task suite, per the
    mission's own explicit instruction).
- **After Stage 2** (pooled n=84): compute exact two-sided McNemar p on the pooled discordant pairs.
  Declare significant if pooled p ≤ 0.048. Report the pooled result as final **regardless of whether
  this threshold is crossed** — a non-significant pooled result is a fully legitimate, reportable
  outcome (inconclusive at this sample size), not grounds for a third stage under this protocol.
- Per-stage and pooled results are BOTH always reported in full — pooling never replaces or hides the
  per-stage breakdown (this is also how genuine replication is assessed: does Stage 2 point in the same
  direction as Stage 1, independently).

## 7. Primary and Secondary Endpoints

- **Primary**: `BASE_N` vs `ARCH_COUNCIL`, paired binary PASS/FAIL, exact McNemar test.
- **Secondary** (reported, not multiplicity-corrected against the primary, explicitly labeled
  secondary): `BASE_1` vs `BASE_N`; `BASE_1` vs `ARCH_PIPELINE_ISOLATED`; `BASE_1` vs `ARCH_COUNCIL`;
  generation/wall-clock time per arm; failure-class distribution; per-stage (Stage 1 vs Stage 2)
  breakdown for replication assessment; council-composition variability (Finding B).
- **Exploratory** (not part of the confirmatory statistical test under any condition): mechanism
  analysis of individual councillor/attempt outputs (§10 of the mission); a compute-budget-normalized
  side probe (§11), if executed.

## 8. Model Pinning

The confirmatory experiment reuses the **identical pinned model from the original Tier-3 pilot**,
`qwen2.5-coder:7b` (read from the existing `audits/tier3_apparatus/pinned_model.json`, not re-selected
via a fresh `choose_model()` call), for `BASE_1`/`BASE_N`/`ARCH_PIPELINE_ISOLATED`. This is a deliberate
choice, not an oversight: the mission's own "Critical Control: Model vs Orchestration" instructs holding
the underlying model fixed whenever possible, and reusing the exact same pin maximizes direct
comparability with the historical pilot result rather than introducing a fresh, potentially different
model-selection outcome as an uncontrolled variable. This pin is persisted to a **new, separate** file
(`audits/tier4_apparatus/pinned_model.json`) so the original pilot's own artifact is never touched.

## 9. Compute-Budget Decision

**Primary confirmatory design: Option A — preserve existing `ARCH_COUNCIL` behavior exactly as it runs
in real production, including the disclosed 5-real-call warm-up asymmetry (Finding C).** Justification:
(1) this is what Council actually does when deployed — testing it under its real operating conditions
has direct ecological validity; (2) artificially removing or normalizing the warm-up would silently
answer a different question (does the warm-up call specifically cause the gap) rather than the primary
question (does Council-as-actually-deployed beat `BASE_N`-as-actually-deployed at matched *generative*
call count). This asymmetry is not retroactively hidden, removed, or reinterpreted as compute-normalized
anywhere in the primary analysis.

**Secondary, exploratory-only: Option B — a compute-normalized side probe**, if time/resources permit
after the primary confirmatory result (§11 of the mission; see Phase 10 in this investigation's own task
tracker). If run, it adds one symmetric, content-discarded extra call to `BASE_N` (mirroring the
warm-up's shape: real cost, zero content contribution) rather than removing Council's real warm-up —
chosen specifically because adding a symmetric no-op call to the simpler arm does not alter
`ARCH_COUNCIL`'s real, disclosed behavior in any way, whereas removing the warm-up would change a real,
justified (Finding C) production mechanism and confound "no compute asymmetry" with "no warm-up
reliability benefit either." This probe, if run, is never pooled into the primary McNemar test under any
circumstance and is reported in a clearly separate section.

## 10. Task Inclusion/Exclusion Rules

Tasks must be: independent (no shared setup/state across tasks); objectively scorable via a real,
executable `test_code` block ending in `print('ALL_TESTS_PASSED')`, matching the existing sandbox
convention; solvable in principle within `MAX_TOKENS=2048` output tokens; not a verbatim or
near-verbatim duplicate of any task in the original 15-task pilot suite, the original 8-task held-out
suite, or each other (checked by direct text comparison before freezing, not assumed). Category spread:
the original four categories (bug-fixing, concurrency/stateful reasoning, algorithmic edge cases,
refactoring) are retained, and at least one genuinely new category not previously tested (e.g.,
input-validation/defensive-coding, or data-transformation/parsing) is added per stage, specifically to
probe whether a result generalizes beyond the original suite's exact category mix, per the mission's own
"resistant to trivial pattern matching" and "representative of the capability being tested" requirements.

## 11. Handling of Malformed Output, Truncation, and Infrastructure Failure

Unchanged from the Tier-3 protocol, reused verbatim (not reimplemented): `classify_result()`'s
call-ID-scoped, ground-truth-first, text-backstop-second classification into `PASS` /
`GENERATION_TRUNCATED` / `TASK_LOGIC_FAILURE`, with `INFRASTRUCTURE_FAILURE` assigned separately at the
exception-handling call site via `_classify_exception()`'s substring-matched connection/timeout
signatures. The `TEXT_BACKSTOP_TRUNCATED` failure mode identified during Tier-3 scoring (§3 of the
Tier-3 scoring analysis — a stray unclosed fence in an otherwise-complete `ARCH_COUNCIL` synthesis
misclassified as truncation) is a known, disclosed limitation of this reused evaluator: any record with
`truncation_evidence_type == "TEXT_BACKSTOP_TRUNCATED"` is manually spot-checked against the raw
response before the final report is written (not assumed correct), exactly as done for the Tier-3
pilot. **`INFRASTRUCTURE_FAILURE`-classified trials exceeding 15% of attempted trials in either stage
overrides every other rule** — the stage's own primary-endpoint result is reported as inconclusive
regardless of its own McNemar p-value (H5, unchanged from Tier-3).

## 12. Treatment of Ties

A "tie" in this design means both arms in a paired comparison produced the same PASS/FAIL outcome on a
given task — a concordant pair. Concordant pairs are correctly excluded from the McNemar discordant-pair
calculation (standard, unchanged McNemar methodology) but are always reported in full (both-pass and
both-fail counts), never silently dropped from the record.

## 13. Paired Comparison Method, Significance Threshold, Confidence Interval Method

- **Paired test**: exact two-sided McNemar test via direct binomial coefficient summation on discordant
  pairs (not the chi-squared approximation, which is unreliable at the discordant-pair counts this
  study expects).
- **Significance threshold**: see §6's two-look boundary (Stage 1: p≤0.0052; pooled: p≤0.048).
  Conventional α=0.05 is also reported alongside for readers who want the single-look reference value,
  clearly labeled as not the pre-registered decision threshold.
- **Confidence interval method**: Wilson score interval for each arm's individual pass rate (reported
  for context, not as the primary inferential test).
- **Effect size**: absolute percentage-point difference in paired pass rates, plus the discordant-pair
  breakdown (which direction, how many).

## 14. Randomization

Arm execution order per task is randomized and recorded, reusing the existing, unmodified
`randomized_arm_order(task_id, seed)` function (seeded per-task, not globally, so no cross-task
correlation) — identical mechanism to the Tier-3 pilot, applied to the new task IDs.

## 15. Replication Policy

Stage 2, when run, constitutes the pre-planned replication (§5, §6) — an independently-authored,
disjoint task suite, not a re-run of Stage 1's own tasks. This satisfies the mission's replication
requirement structurally, not as an afterthought: the two-stage design *is* the replication design, not
a single large batch with replication bolted on if convenient.

## 16. Rules for Discovering and Correcting Evaluator Bugs

If a genuine evaluator bug (not a surprising-but-correct result) is found during or after execution: (a)
it is fixed only in a way that is blind to which arm benefits — i.e., the fix must be justifiable purely
from the bug's own mechanics (as Finding A and the original Tier-3 truncation-heuristic fixes both were),
never chosen because it produces a preferred outcome; (b) the fix and its justification are documented
in full, including which specific records it affects and in which direction; (c) if a fix is found only
after Stage 2 execution has begun, both stages are re-scored under the corrected rule and the change is
disclosed explicitly — the raw generation outputs are never re-generated or discarded, only re-scored.

## 17. Rules Governing Protocol Modification

No change to §1–§14 (hypotheses, design, sample size, stopping rule, endpoints, model pin, compute-
budget decision, task rules, scoring rules, statistics, randomization) is permitted after Stage 1
execution begins, except under §16's evaluator-bug provision. Any such change, if it ever occurs, is
documented with a timestamp, a full justification, and an explicit statement of what was true before and
after — never a silent edit.

## 18. Protocol Hash

This file is hashed immediately after being written, before either task suite is authored. See
`audits/tier4_confirmatory_protocol.hash.txt` for the recorded SHA-256. Any future re-read of this file
is checked against that hash before being trusted as the frozen version.
