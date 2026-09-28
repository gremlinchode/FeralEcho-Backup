# Mission 34 — Running Mission 33's Experiment: Blinded Gold Labels vs. Heuristic vs. Production Classifier

**Date:** 2026-09-09
**Type:** Investigation + bounded experiment. No production code changed, no production state mutated. New, isolated experiment module added (`app/experiments/task_type_ground_truth/`), matching this codebase's own established pattern for out-of-band research harnesses.

## Executive Verdict

The pilot ran clean, the blinding held, and the result is genuinely informative — but it is a **null-to-inconclusive result at this scale, not a positive demonstration that independent supervision beats the heuristic**, and it surfaced a real confound this mission did not fully control for. On the decisive adversarial subset (10 scorable items where lexical cues and Gremlin's genuine judgment diverged), the independently-trained leave-one-out classifier (Condition C) narrowly beat the pure static heuristic (Condition A) — 2/10 vs 1/10 — and was clearly beaten by the real, currently-deployed production classifier (Condition B) — 4/10. At n=10, a 1-item difference is not distinguishable from chance (SUPPORTED, not VERIFIED, as a directional signal; explicitly **not** a significant result — see Section 6). Separately, and not the mission's original target, this pilot surfaced a real, concrete, previously-undocumented weakness in `compute_intent_heatmap()` itself: a bare first-person pronoun ("I"/"my") reliably outvotes a single technical keyword, misrouting plainly technical questions toward `personal` — confirmed directly against the real function, not inferred (Section 7).

## Question

Mission 33's question, now run rather than only designed: does a task-type classifier trained on genuinely independent, blinded human labels outperform (a) the static keyword heuristic and (b) the real, currently-deployed classifier (99.5% heuristic-derived per Mission 32) — specifically on prompts where lexical cues and actual intent diverge?

## What Was Built (Phase B, per Mission 33's own recommended next step)

`app/experiments/task_type_ground_truth/` — `schema.py` (data classes), `dataset.py` (the candidate pool), `blind_label.py` (label storage with a real, checkable `assert_blinding_intact()` guard), `evaluate.py` (Conditions A/B/C). Mirrors the isolation convention already established by `app/experiments/raoc/` and `app/experiments/preference_provenance/` — not imported by any production path.

**A design pivot, disclosed rather than silently made**: Mission 33's sketch suggested sampling real historical prompts for the "ordinary" subset where feasible. Checked directly before building anything: essentially all 205 real, currently-visible `source=="user_conversation"` trustworthy examples in `interaction_log.jsonl` have already been fed to the production classifier's `learn()` via its online hook (Mission 32's own trace). Using any of them would have given Condition B a hidden home-field advantage on its own training data. Pivoted to a fully **constructed** dataset instead — 27 candidates (15 "ordinary," 12 "lexically adversarial"), every item honestly tagged with its provenance, none reused from Mission 33's own report text (which already carried the investigator's speculative "genuine intent" for its 4 illustrative examples — reusing those verbatim would have risked a pre-seeded answer).

## Data Collection and Blinding

Gremlin selected a 20-item pilot (all 12 adversarial + 8 of the 15 ordinary, his choice from an explicit menu of options — this mission did not decide his time commitment for him). The 20 prompts were presented in **randomized order** (fixed seed 34, disclosed) as plain text, with no heuristic or classifier output computed or shown before or during labeling — confirmed as a real, checkable property, not an assumption: `assert_blinding_intact()` was called immediately before writing `gold_labels.jsonl` and raised no error, meaning neither `app.core.echo_model_orchestrator` nor `app.core.task_type_classifier` had been imported into that Python process at any point before the labels were locked.

**A real limitation, disclosed rather than glossed over — the most important caveat in this report**: Gremlin's blinding was *procedural* (he did not see any prediction for these specific items) but not *conceptual*. He is this project's own architect, with months of direct exposure to `compute_intent_heatmap()`'s exact five-category taxonomy and its documented quirks (including, per CLAUDE.md's own Finding 43, prior specific knowledge that bare "memory" and other keywords have caused misrouting before). Mission 33's Section 6.B named "taxonomy inheritance" as a risk specifically for an LLM-judge channel; this mission's result shows the identical risk applies to a human labeler who already deeply understands the system being evaluated. This does not invalidate the procedural blinding (which is real and was checked, not assumed) — it means the independence bar from Mission 33's own Section 4, items 6–7 ("independent of lexical features that mechanically encode the existing heuristic," "independent of any judge merely prompted to imitate the existing classifier's taxonomy") is only **partially** met even by this channel. Labeled explicitly: **POTENTIALLY INDEPENDENT (procedural blinding VERIFIED; conceptual/taxonomy independence NOT established and likely only partial)**, not the unqualified "independent" Mission 33's ideal design called for.

Two of 20 items (`adv-12`, `adv-10`) were judged genuinely `ambiguous` by Gremlin himself and correctly excluded from scoring — worth noting as a real data point: 2/12 (16.7%) of the adversarially-constructed items were judged too ambiguous to have a single right answer at all, not a design failure but a real property of prompts built to sit between categories.

## Results

n=20 total, n=18 scorable (2 excluded as gold=ambiguous).

| Condition | n scored | n correct | accuracy (of scored) | accuracy (of all 18) |
|---|---:|---:|---:|---:|
| A — static heuristic (`compute_intent_heatmap()`, classifier never consulted) | 18 | 6 | 33.3% | 33.3% |
| B — real production classifier (`predict()`, read-only against the real 480-observation persisted state) | 12 (6 declined: untrusted/low-confidence) | 6 | 50.0% | 33.3% |
| C — leave-one-out, trained only on the 18 scorable blind gold labels, never touching the real pickle | 18 | 5 | 27.8% | 27.8% |

**On the decisive subset — the 10 scorable adversarial items only** (this is the metric Mission 33 called decisive, not overall accuracy, which is dominated by the easy majority of "ordinary" items):

| Condition | correct / attempted | correct / all 10 |
|---|---:|---:|
| A | 1/10 | 10% |
| B | 4/7 (declined 3) | 40% |
| C | 2/10 | 20% |

**Interpretation, stated plainly rather than dressed up**: Condition C beat Condition A on the adversarial subset (20% vs 10%) — directionally consistent with "independent labels carry some real signal beyond the heuristic" — but this is a **1-item difference at n=10**, not distinguishable from chance, and explicitly not claimed as significant (Section 6). Condition B clearly won the adversarial subset despite Mission 32's own finding that B's real training labels are 99.5% heuristic-derived — most plausibly because B has ~25x more real training observations (480, even if largely heuristic-imitation-learned) than any single Condition C leave-one-out fold (19 examples, only 2–3 of any given class). **This is a real, unresolved confound this pilot did not control for**: Conditions B and C differ in *both* label-independence *and* training-set-size simultaneously, so this result cannot cleanly attribute B's advantage to "more data" versus "the same heuristic-derived label quality being fine at scale" — see Section 8's recommendation for the controlled follow-up that would isolate this.

## Adversarial Findings

**A real bug in this mission's own scoring code was caught and fixed before the experiment ran, not after** — matching this project's own established "disclose your own measurement bugs" discipline. `evaluate.py`'s first draft used `gold in ("ambiguous", "none_of_these") is False` intending "gold is not one of these two values" — Python's chained-comparison semantics make this `(gold in X) and (X is False)`, not `gold not in X`. Caught by direct inspection before the first real run (not discovered via a wrong result), fixed to an explicit `gold not in (...)` check, with the fix and its reasoning left as an inline comment in the source rather than silently corrected.

**The real, unexpected side-finding**: `compute_intent_heatmap()` re-run directly (read-only, no mutation) against the two "ordinary, unambiguous coding" items this mission misjudged as easy — `ord-07` ("I keep getting a segmentation fault in my C program...") and `ord-13` ("If I have 3 apples...") — confirms a precise, reproducible mechanism, not a fluke: `personal_word_boundary_keywords = ["i", "my"]` contributes a flat +1 per word type *present at all* (not per occurrence), and this alone is enough to make `personal` win the heatmap (0.615 and 0.571 respectively) over a single technical keyword hit (`"program"` → `coding` 0.308) or zero other signal at all (`general` 0.429). **Any first-person-phrased message with at most one weak counter-signal gets pulled toward `personal`** — a real, previously-undocumented production behavior, found as a byproduct of this experiment, not something this mission was authorized to fix (investigation only). Flagged for a decision, not silently patched.

**Randomness/determinism check**: `evaluate.py` re-run a second time, byte-identical results (river's NB `predict_proba_one` is deterministic; the LOO training order is fixed by `gold_labels.jsonl`'s own on-disk order) — upgraded from an assumption to VERIFIED.

**Self-confirming-fixture check**: Condition A/B call the real, unmodified `compute_intent_heatmap()`/`get_task_type_classifier().predict()` directly — no reimplementation. Condition C uses the real `TaskTypeClassifier` class and the real `river` pipeline, deliberately bypassing only the production trust-floor gate (`is_well_observed()`) via a direct `predict_proba_one()` call — disclosed explicitly in `evaluate.py`'s own comments as a deliberate, necessary deviation (the real gate's thresholds, 200/30, can never be met at n<20 and would make Condition C trivially return "no prediction" for every single item, which would answer a different question — "is this dataset big enough to pass the production safety gate," not "did the model learn a useful boundary").

## Statistical Discipline

n=20 (18 scorable, 10 adversarial-scorable) is explicitly a pilot, per Mission 33's own pre-registered discipline — no significance test is reported because none would be meaningful at this scale. The single-item adversarial-subset gap (Condition C: 2/10 vs Condition A: 1/10) is reported as a directional data point only. This project's own precedent (CLAUDE.md's Tier-3→Tier-4 capability-ceiling research, cited directly in Mission 33's design) is the reason this mission does not attempt to read more into it.

## Causal Chain (update to Mission 33's Section 15 table)

| # | Link | Status after this run |
|---|---|---|
| 1 | Independent observation | OBSERVED — 20 constructed prompts, presented |
| 2 | Independent label | **OBSERVED, with the taxonomy-inheritance caveat above** — procedural blinding VERIFIED (`assert_blinding_intact()` passed); full conceptual independence NOT established |
| 3 | Training example | OBSERVED — 18 usable (2 ambiguous excluded) |
| 4 | Model update | VERIFIED — real `learn_one()` calls, real `river` pipeline |
| 5 | Persisted state (in-memory only) | VERIFIED — confirmed never written to `memory/task_type_classifier.pkl` |
| 6 | New prediction | VERIFIED |
| 7 | Held-out prediction | VERIFIED — genuine leave-one-out, each fold's test item excluded from its own training |
| 8 | Comparison against gold label | VERIFIED — scored directly, bug caught and fixed first |
| 9 | Measurable improvement (Condition C vs. A/B on the adversarial subset) | **INCONCLUSIVE at this n — directionally beat A (20% vs 10%), directionally lost to B (20% vs 40%), neither difference statistically meaningful at n=10, and the B comparison is confounded by training-set size, not label independence alone** |

## What This Mission Does and Does Not Establish

**Established**: a real, working, blinding-checked harness now exists and was run end-to-end against the real production functions with zero production mutation. A real weakness in the static heuristic was found and confirmed. The pilot did not find evidence strong enough to claim independent supervision beats the heuristic, nor strong enough to rule it out.

**Not established**: whether independently-labeled supervision, given training data at parity with the production classifier's real 480-observation scale, would outperform it. This pilot's Condition C had roughly 25x less training data than Condition B, confounded with Condition C's label-independence advantage — this mission cannot separate those two effects from each other.

## Recommendations

1. **The controlled follow-up this pilot's own confound calls for**: a fourth condition — a from-scratch classifier trained on *N* heuristic-derived labels (N matched to Condition C's real gold-label count, not the full 480) — would isolate "label independence" from "training-set size" as separate variables, which this run did not do.
2. **Scale the gold set**, per Mission 33's own statistical framing — 20 is a discriminating pilot, not a confirmatory one; a properly-powered follow-up (Mission 33's own Section 14 discussion, and this project's Tier-3→Tier-4 precedent) would need substantially more than 20 examples, and should recruit blinding from someone with less prior exposure to this project's own taxonomy than Gremlin, if that's practically achievable, to close the conceptual-independence gap this mission's own labeler could not close.
3. **The `compute_intent_heatmap()` "I"/"my" over-weighting finding** (Section 7) is a real, disclosed, unauthorized-to-fix production observation — flagged for a separate decision, not bundled into this mission's own scope.

## Integrity Record

```
production changes: NO
files changed: NO production code touched. New files: app/experiments/task_type_ground_truth/{__init__.py,schema.py,dataset.py,blind_label.py,evaluate.py,gold_labels.jsonl}, this report.
Git HEAD before: e92ec3b
Git HEAD after: e92ec3b (no commits made)
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: none beyond short-lived read-only python3 invocations (module import, predict()/predict_proba_one() calls only — confirmed via source read, never learn_one()/.save() against the real singleton, never touched memory/task_type_classifier.pkl or memory/interaction_log.jsonl in write mode)
configuration changes: NO
test changes: NO (new experiment module, not a test suite change)
temporary files created: none outside the repo were needed this time; all new files are the disclosed app/experiments/task_type_ground_truth/ module plus gold_labels.jsonl (real human-labeled data, kept, not a scratch artifact)
temporary files cleaned: N/A — nothing scratch-only was created
orphaned processes: checked, none found
known anomalies: a real scoring-logic bug (chained-comparison misuse) was caught and fixed before the first real run — see Adversarial Findings
known deviations from requested methodology: (1) the dataset pivoted from "sample real historical prompts" to fully constructed prompts, disclosed and justified in "What Was Built"; (2) Condition C bypasses the production trust-floor gate deliberately, disclosed in evaluate.py's own comments and this report's Adversarial Findings; (3) the human labeler's conceptual (not procedural) blinding is only partial, disclosed prominently in "Data Collection and Blinding" rather than left implicit.
```
