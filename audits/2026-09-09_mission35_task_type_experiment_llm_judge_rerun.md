# Mission 35 — Re-Running Mission 34's Experiment with a Fresh-Agent Label Channel (No Human in the Loop)

**Date:** 2026-09-09
**Type:** Investigation + bounded experiment. No production code changed, no production state mutated.

## Executive Verdict

A genuinely fresh, non-forked agent — with zero exposure to this investigation, this codebase, `compute_intent_heatmap()`'s keyword lists, or which items were adversarially constructed — classified the identical 20 prompts Gremlin labeled in Mission 34, using nothing but the raw prompt text and neutral category definitions (0 tool calls used; confirmed it never touched the repository). Its labels agree with Gremlin's on **16/20 (80%)** — a real, useful cross-check suggesting most of these prompts do have a fairly clear intended category that two independent judges converge on, not an arbitrary or noisy target. But the three-way A/B/C comparison **flips ranking** depending on which gold set is used: under Gremlin's labels, the real production classifier (B) beat the independently-trained model (C) on the adversarial subset (40% vs 20%); under the fresh agent's labels, **C beats B** (30% vs 20%), with the static heuristic (A) scoring 0%. This instability across two reasonable, differently-sourced 20-item gold sets is itself the headline finding: **this pilot is too small to support a directional conclusion about whether independent supervision beats the heuristic — the answer changes depending on who labels the same 20 items**, exactly the outcome Mission 33's own statistical-discipline section warned a pilot this size could not settle.

## Why the Labeler Had to Be a Fresh Agent, Not This Session

Explained to Gremlin directly before running this: this session designed the 12 adversarial prompts specifically to exploit known weaknesses in `compute_intent_heatmap()`'s keyword scoring (having just hand-computed that scoring formula repeatedly across Missions 32–34), and has read the heuristic's exact keyword lists multiple times. Labeling them in this same context would be the investigator grading their own test — the self-confirming-fixture failure mode `adversarial-checklist.md` names explicitly. A fresh, non-forked `general-purpose` agent (the same isolation mechanism `feral-independent-review` requires for the identical reason) was spawned instead, given only the 20 prompts and seven neutral category definitions — no mention of FeralEcho, the heuristic, adversarial construction, or this investigation's existence. It used **zero tool calls** (confirmed via the task notification's own usage record) — it never read a single file in this repository, meaning it could not have been exposed to `compute_intent_heatmap()`'s keyword lists even accidentally.

**Independence classification for this channel, per Mission 33's own vocabulary**: POTENTIALLY INDEPENDENT, secondary — stronger than Gremlin's channel on one specific axis (zero exposure to this project's own keyword vocabulary, versus Gremlin's months of direct familiarity with it — Mission 34's own flagged limitation), weaker on another (a general-purpose LLM's own training-derived lexical associations for words like "poem"→creative or "code"→coding are not obviously independent of *why* a heuristic author would have chosen those same words in the first place; both are drawing on the same broad natural-language conventions, just via different mechanisms). Neither channel achieves the full independence bar Mission 33's Section 4 defines; each fails it in a different, disclosed way.

## Data Collection

Identical 20 prompts, identical presentation order, as Mission 34. The fresh agent returned one label per item in a single response with no back-and-forth. Saved to `app/experiments/task_type_ground_truth/gold_labels_llm.jsonl` (labeler tag: `llm_judge:fresh_general_purpose_agent`), separate from Mission 34's `gold_labels.jsonl` — neither file was overwritten, both are preserved for the record. `assert_blinding_intact()` was checked and passed for the process that saved these labels (no forbidden module had been imported).

## Human vs. Fresh-Agent Agreement (a real, useful cross-check)

**16/20 (80%) agreement** between Gremlin's Mission 34 labels and this mission's fresh-agent labels — computed directly, not estimated. The 4 disagreements:

| Item | Gremlin | Fresh agent | Note |
|---|---|---|---|
| `adv-11` ("Tell me a story about a function that always returns true...") | creative | ambiguous | Fresh agent declined to commit where Gremlin picked one side |
| `adv-07` ("My program keeps crashing... making me feel like I'm losing my mind") | reasoning | coding | Both plausible; neither matches this mission's own constructor guess of "personal" either |
| `adv-10` ("...major in creative writing or computer science") | ambiguous | general | Gremlin saw genuine dual-fit; fresh agent read it as a plain question |
| `adv-09` ("Do you think a well-written poem and a well-written function have anything in common?") | personal | reasoning | Both defensible |

All four disagreements cluster on genuinely hard, deliberately-adversarial items — zero disagreement occurred on any of the 15 "ordinary" items. This is itself informative: the adversarial construction succeeded at producing real disagreement between independent judges, not just disagreement with the heuristic.

## Results Under the Fresh-Agent Gold Set

| Condition | n scored | n correct | accuracy (of scored) | accuracy (of all 18*) |
|---|---:|---:|---:|---:|
| A — static heuristic | 18 | 5 | 27.8% | 25.0% |
| B — real production classifier (read-only) | 11 (7 declined) | 4 | 36.4% | 20.0% |
| C — leave-one-out, trained only on these 18 gold labels | 18 | 5 | 27.8% | 25.0% |

\* 2 items (`adv-12`, `adv-11`) excluded — both judged `ambiguous` by the fresh agent (a different pair than Mission 34's exclusions, since the two gold sets disagree on which items are ambiguous — `adv-10` is scorable here but wasn't in Mission 34; `adv-11` is excluded here but was scorable in Mission 34).

**Adversarial subset only (10 scorable items under this gold set — not the identical 10 items as Mission 34's subset, per the note above):**

| Condition | correct / attempted | correct / all 10 |
|---|---:|---:|
| A | 0/10 | **0%** |
| B | 2/6 (declined 4) | 20% |
| C | 3/10 | **30%** |

## Direct Comparison: Mission 34 (Gremlin) vs. Mission 35 (Fresh Agent)

| Condition | Adversarial accuracy, human gold (Mission 34) | Adversarial accuracy, fresh-agent gold (Mission 35) |
|---|---:|---:|
| A (heuristic) | 10% | **0%** |
| B (production classifier) | **40%** | 20% |
| C (independent, LOO) | 20% | **30%** |

**The ranking of B vs. C inverts between the two gold sets.** Under Gremlin's labels, B (the heuristic-trained production classifier, but with ~25x more real data) wins. Under the fresh agent's labels, C (the independently-labeled model, but with a fraction of the data) wins. Both results are drawn from the same 20 prompts and roughly the same evaluation machinery — the only thing that changed is who supplied the gold labels. At n=10 per subset, a difference of 1–2 items is enough to flip which condition looks better, and this run demonstrates that concretely rather than just asserting it as a statistical abstraction.

**Static heuristic A performed worse under the fresh-agent gold set than under Gremlin's (0% vs 10%)** — both are near-floor regardless, but worth noting the heuristic did not do *better* against an independently-sourced judge; if anything, slightly worse, consistent with (not proof of) Mission 32/34's broader finding that the heuristic's real routing quality on hard cases is weak.

## Adversarial Findings

**Checked directly, not assumed: did the fresh agent's zero-tool-call answer show any sign of having guessed the experimental structure** (e.g., suspiciously perfect agreement with the heuristic, or a pattern suggesting it inferred "this is a bias-detection test" and tried to be contrarian)? No — its agreement pattern with Condition A (the heuristic) is itself informative: on the 18 scorable items, A and the fresh-agent gold label matched only 5/18 (28%, i.e. Condition A's own reported accuracy against this gold set) — no higher than its agreement with Gremlin's gold set (33%). Nothing in the pattern suggests gaming; the fresh agent appears to have done exactly what it was asked, in good faith, from a cold start.

**Self-confirming-fixture check, repeated**: Condition A/B/C ran through the identical, unmodified `evaluate.py` module used in Mission 34 — no new code was written for this run beyond a short ad hoc script to load the second label file and reuse the existing `run_condition_a/b/c_loo`/`score` functions directly (no reimplementation).

## What This Run Adds to Mission 34's Conclusion

Mission 34 already reported this pilot as inconclusive due to a confound (label-independence and training-set-size varying together between B and C) and small-n noise. This run **does not resolve that confound** — it adds a second, independent demonstration that the result is unstable at this sample size, which is a stronger, more concrete form of the same caution: not "n=20 is probably too small," but "here are two real gold sets, both defensible, that produce opposite rankings." The one genuinely new, positive finding is the **80% human/fresh-agent agreement rate** — real evidence that these 20 prompts (adversarial ones included) mostly have a discoverable "genuine intent" that different judges converge on, even though this pilot's A/B/C comparison remains too small and too gold-set-dependent to say which routing approach best captures it.

## Final Classification (unchanged from Mission 32/33/34)

**L2, not L3.** Neither this run nor Mission 34's establishes independently-measured improvement (causal-chain link 9/10) — if anything, this run demonstrates more directly why that link remains open: the measurement itself is not yet stable across reasonable labeling choices at this scale.

## Recommendations

1. **Don't treat either gold set as more authoritative than the other** — report both, as this document does, rather than picking whichever supports a preferred conclusion.
2. A genuine confirmatory follow-up needs (a) more examples (Mission 33/34's own repeated point), and (b) ideally a third, larger gold set (or inter-rater reconciliation on the 4 disagreements) to establish a single, higher-confidence label per item rather than treating either 20-item set alone as ground truth.
3. The controlled follow-up Mission 34 already recommended (a from-scratch classifier trained on N heuristic-derived labels, N matched to the gold set size, to isolate label-independence from training-set-size) remains the most direct next step and is unaffected by this run's findings.

## Integrity Record

```
production changes: NO
files changed: NO production code touched. New files: app/experiments/task_type_ground_truth/gold_labels_llm.jsonl, this report.
Git HEAD before: e92ec3b
Git HEAD after: e92ec3b (no commits made)
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: one background Agent-tool invocation (fresh, non-forked general-purpose agent — 0 tool calls, confirmed via its own usage record, never touched the filesystem); short-lived read-only python3 invocations reusing Mission 34's evaluate.py functions unmodified
configuration changes: NO
test changes: NO
temporary files created: none beyond the disclosed gold_labels_llm.jsonl (real data, kept)
temporary files cleaned: N/A
orphaned processes: checked, none found
known anomalies: none
known deviations from requested methodology: none — the user's request ("run it again, no human in the loop, you categorize") was fulfilled via a fresh non-forked agent rather than this session directly, with the reasoning for that substitution stated plainly before proceeding rather than silently decided.
```
