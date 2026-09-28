# Mission 33 — Independent Ground-Truth Learning Signal Audit

**Date:** 2026-09-09
**Type:** Investigation and experiment-design only (Phase A). No production code changed, no production behavior modified, no new learner built or trained against real state.

## 1. Executive Summary

FeralEcho does not currently possess a populated, genuinely independent ground-truth signal for task-type classification. Every real, currently-flowing label source traces back to `compute_intent_heatmap()`'s or `detect_task_type()`'s own static keyword logic, or to the classifier's own prior predictions (Mission 32). This mission found exactly **one architecturally independent mechanism already built into the product** — `terminal_client.py`'s `!ask <model> <task_type> <prompt>` command, where a human types the task type directly and the value never touches `resolve_task_type()`, `detect_task_type()`, or the classifier — but it currently has **zero real historical uses** (`source == "manual_probe"` count in `memory/council_deliberations.jsonl`: 0/772), was designed for a different purpose (routing a probe, not labeling ground truth), and was never wired into the classifier's training pipeline at all. No other candidate signal survives the independence trace: an explicit user-correction UI doesn't exist, downstream success/failure signals (code verification, sandbox execution) measure correctness within an already-assumed task type rather than identifying the type itself, and the one other keyword-based subsystem checked as a possible proxy (`echo_tool_dispatch.py`'s `needs_dispatch()`) is itself just another static heuristic, not independent of the same failure class Mission 32 found.

**The valuable result of this mission, per its own stated success criteria, is exactly this negative finding**: no currently available signal is sufficiently independent and populated to run Condition C of the proposed experiment today. This report specifies what would need to be built — primarily a small, deliberately blinded human-labeled gold set, collected via a new offline harness, optionally cross-checked by a carefully blinded LLM judge — and the smallest experiment that could then distinguish genuine intent-learning from heuristic reproduction, without running it.

## 2. Mission Objective

Determine whether FeralEcho can be given a genuinely independent task-type learning signal, and design (not build) the smallest rigorous experiment that could determine whether learning from that signal outperforms the heuristic that currently supplies its labels — while being ruthless about the distinction between "learning" and "learning from an independent signal," per Mission 32's own central failure mode.

## 3. Mission 32 Baseline

Re-verified, not merely cited, before treating as settled (per this mission's own instruction not to trust recency):

- **`resolve_task_type()`'s `<0.4` heatmap-confidence gate** — re-read directly, `app/core/echo_model_orchestrator.py:606-614`, unchanged since Mission 32. OBSERVED.
- **`/mirror_echo` bypasses this gate** — re-verified directly, `run.py:557`: `task_type = echo_model_orchestrator.detect_task_type(msg)`, called unconditionally, then fed into `echo_query(..., task_type=task_type, source="user_conversation", ...)` two lines later — confirmed this reaches `log_interaction()`'s training hook exactly as Mission 32's independent review found. OBSERVED, re-confirmed independently in this mission.
- **204/205 (99.5%) of the real, currently-visible trustworthy training corpus has heuristic-forced labels; 480 total real observations exist in the persisted classifier, only 205 are currently visible in the (rotated) log** — taken as established from Mission 32 and its independent review; not re-run in this mission (no new evidence would change it, and re-running it is not this mission's task).
- **No independent ground-truth source was found by Mission 32** — this mission's job is to determine whether that remains true after a dedicated, broader search (Sections 4–8 below), not to assume it.
- **Classification: L2, not L3** — the standing baseline this mission does not overturn (see Section 18).

## 4. Definition of Independent Ground Truth

A candidate signal is treated as independent **only if all of the following hold**:

1. **Independent of the static heuristic** — the label is not `compute_intent_heatmap()`'s or `detect_task_type()`'s own keyword-ladder output, directly or through a thin wrapper.
2. **Independent of the current classifier** — the label was not produced by `task_type_classifier.py`'s `predict()`, and did not have visibility into that prediction before being recorded.
3. **Independent of previous classifier predictions** — no label-generation step reads `memory/task_type_classifier.pkl` or any derived summary of it.
4. **Independent of the current routing pipeline** — the label does not depend on which downstream branch (`DIRECT_ECHO_TASKS`, token budget, council composition) a message happened to take, since those branches are themselves consequences of the label being evaluated.
5. **Independent of downstream consequences that were themselves generated using task-type labels** — e.g., a quality score computed with a task-type-dependent scoring formula cannot be used to infer what the task type was; that reasoning is circular in the other direction.
6. **Independent of lexical features that mechanically encode the existing heuristic** — a labeling process that reads the same trigger words (`"code"`, `"poem"`, `"feel"`, etc.) and reasons in the same taxonomy the heuristic was hand-built around is not independent merely because a different function computed it. This is the subtlest and most commonly-missed failure mode (see Section 6.B below).
7. **Independent of any council/model whose judgment is merely prompted to imitate the existing classifier** — a judge model told "classify into `coding`/`personal`/`general`/`creative`/`reasoning`, matching how FeralEcho currently does it" has been handed the same taxonomy, not asked to form one independently.

Provenance-chain requirement for every candidate:

```text
raw observation → label source → label → training example
```

with an explicit statement of **where contamination could enter** at each arrow — required for every candidate evaluated below, not just the ones that pass.

## 5. Repository Evidence (this mission's own search)

Beyond re-confirming Mission 32's trace, this mission searched specifically for signals Mission 32 did not center:

- **`terminal_client.py:585-616`, `request_manual_probe()`** — the `!ask <model> <task_type> <prompt>` command. `task_type` is a bare string typed by the human at the CLI prompt. Read in full: it validates `model` against `MODEL_POOL` (exact match), then calls `_ollama_query()` **directly** — confirmed via `river_deliberation.py` that `_ollama_query()` has no dependency on `resolve_task_type()`/`detect_task_type()`/the classifier anywhere in its call graph — and logs the result via `_log_council_deliberation(..., source="manual_probe", ...)` into `memory/council_deliberations.jsonl`, a **separate file from `interaction_log.jsonl`**. OBSERVED: this file has 772 real lines; `source == "manual_probe"` appears in **0** of them. The mechanism is real and independent by construction; the data does not exist.
- **`echo_tool_dispatch.py:488-495`, `needs_dispatch()`** — read in full. `return any(sig in low for sig in _DISPATCH_SIGNALS)` — a plain substring match against a fixed keyword list, structurally identical in kind to `compute_intent_heatmap()`'s own scoring, just a different list for a different decision (whether to invoke a tool, not which task type). Not independent; ruled out as a proxy.
- **`echo_studio/state/local_store.py:114`, `add_message(..., task_type)`** — Echo Studio's local SQLite mirror of conversation history. Traced the call site: `conversation_view.py:480` passes `task_type` straight through from the server's own `/chat/stream` response payload (`api_client.py:107,142`, `data.get("task_type", "")`) — a passive UI-side cache of the already-resolved server value, not an independent judgment.
- **`app/routes_echo_studio.py`'s `chat_regenerate()`** — read in full; reuses the original message's already-resolved `task_type`, no user-override parameter exists.
- **No re-categorization/correction UI found anywhere** — grepped for "wrong category," "recategor," "relabel," "correct_task_type" across the full repo; zero relevant hits (two hits in `app/experiments/preference_provenance/` and `app/experiments/learning/world_gen.py` are unrelated to task-type and not pursued further, out of this mission's scope).
- **`code_verification.py`/`self_knowledge_verification.py`** (CLAUDE.md Findings 43–45) — read their stated purpose directly: they verify whether a *claimed, checkable* code example actually runs correctly. This presupposes the message was already routed as `coding`; it produces no signal about whether that routing decision was itself correct, and produces no signal at all for the other four task types. Ruled out per the mission's own explicit warning (Section 4.D) not to conflate task success with task-type identity.
- **`council_rater.py`/`spot_check.py`** — the human spot-check pipeline rates response *quality* (1–5), never task-type identity. Confirmed by reading `council_ratings.jsonl`'s real field list (Mission-independent re-read): `council_rating`, `council_rating_model`, `council_rationale_preview`, `task_type` (recorded, not judged), `quality_score`, `spot_check_required`, `human_spot_check_rating`. The human spot-checker rates the *rating*, not the *task_type* field — it is present as metadata, not as something the human is asked to verify.
- **No fixture/gold/golden dataset for `task_type` exists anywhere in the repo** — re-confirmed via `find -iname "*task_type*fixture*" -o -iname "*task_type*gold*" -o -iname "*task_type*label*"`, zero hits, consistent with Mission 32.

## 6. Candidate Signal Inventory

### A. Human annotation (fresh, purpose-built)
Does not exist today. Would require a new, small, offline harness (not production code) presenting prompts to a human blind to any existing prediction. **Strongest theoretically available candidate** — a genuine `prompt → human judgment → task type` chain is achievable with a script simple enough to build in an afternoon, using the exact blinding discipline in Section 11.

### A′. `!ask`'s existing task_type argument, repurposed
Real, already-built, architecturally independent as a *mechanism* — but its **existing design purpose is wrong for this use**: a human typing `!ask qwen2.5-coder coding "explain quantum entanglement"` is choosing which model+bucket to probe, often *deliberately* mismatched from the prompt's actual content for testing purposes (e.g., "how does a coding-tagged model handle an off-topic question"). Naively harvesting historical `!ask` triples (if any existed) would risk labeling by *probe intent*, not *content intent* — a different, non-equivalent judgment. The mechanism (a CLI hook accepting an explicit, heuristic-bypassing `task_type` argument) is reusable groundwork for Candidate A's harness; the historical data, even if it existed, would not be directly usable as-is.

### B. Independent model/council judgment
Genuinely possible, but **not automatically independent** — the sharpest risk this mission found. A judge model prompted "classify this into `coding`/`personal`/`general`/`creative`/`reasoning`" has been handed the exact same five-way taxonomy `compute_intent_heatmap()`'s author hand-built — independence of *label-generation process* (a different, pretrained, general-purpose model) does not imply independence of *taxonomy definition* (the same five hand-drawn category boundaries). A judge blinded from the heuristic's own keyword list and from the classifier's prediction is independent of links 1–4 in Section 4's definition but is **not** independent of link 6/7 unless the taxonomy itself is re-derived rather than handed to the judge verbatim. Usable as a **secondary, cross-checking** signal only, with this caveat stated plainly wherever cited — not a sufficient standalone gold source.

### C. User-provided labels (explicit correction, "that's not what I asked")
No such mechanism exists anywhere in the product (Section 5). This is the genuinely strongest kind of signal in principle (actual intent from the person who wrote the message) and the cheapest to reason about for independence — but it is **entirely unavailable today**, and building it is a real product feature, not something this mission can retrofit from existing logs.

### D. Downstream success/failure
Ruled out directly, per the mission's own explicit warning: `code_verification.py`'s real/false-claim detection measures whether *already-assumed-coding* output executes correctly — it provides zero information about whether the original message was a coding request in the first place, and no equivalent exists for the other four task types.

### E. Existing metadata (routes, UI actions, tool-dispatch class)
`needs_dispatch()` is itself a separate static keyword heuristic (Section 5) — same non-independence class as the mechanism under review, just a different keyword list for a different decision. No other metadata field (timestamp, route path, model chosen) was found to carry task-type information not already downstream of the classifier's own decision.

## 7. Independence Matrix

| Candidate signal | Source | Independent of heuristic? | Independent of classifier? | Independent of routing? | External observer? | Circularity risk | Verdict |
|---|---|---:|---:|---:|---:|---|---|
| Fresh blinded human annotation (new harness) | Human, purpose-built script | Yes (by design, if built correctly) | Yes | Yes | Yes | Low, if blinding discipline (Sec. 11) is followed exactly | **POTENTIALLY INDEPENDENT** (not yet built) |
| `!ask`'s task_type argument (as-is, historical) | Human, existing CLI | Yes (mechanism) | Yes (mechanism) | Yes (mechanism) | Yes | Low as a mechanism; **HIGH** if historical data is reused naively (probe-intent ≠ content-intent) | **UNAVAILABLE** (0 real examples) / mechanism-level VERIFIED INDEPENDENT |
| Independent LLM/council judgment, blinded from prediction | Model, new prompt | Partially — independent of the heuristic's *code*, not of its *taxonomy* | Yes, if blinded | Yes, if blinded | Yes (different model) | Medium — taxonomy inheritance (Sec. 6.B) | **POTENTIALLY INDEPENDENT**, secondary-only |
| Explicit user correction UI | Would-be product feature | Yes | Yes | Yes | Yes | Low | **UNAVAILABLE** (doesn't exist) |
| Downstream success/failure (code_verification.py) | Sandbox execution | N/A — doesn't identify task type at all | N/A | N/A | N/A | Measures a different axis entirely | **NOT APPLICABLE** |
| Tool-dispatch class (`needs_dispatch()`) | Static keyword list | **No** | N/A | N/A | N/A | Same heuristic-imitation failure class as the subject under audit | **CIRCULAR** |
| Council/human quality ratings (`council_rater.py`) | Peer model / human spot-check | N/A — rates quality, not identity | N/A | N/A | N/A | Doesn't measure task-type at all | **NOT APPLICABLE** |
| Echo Studio local_store `task_type` column | Server's own resolved value, mirrored | No | No | No | No | Passive copy of the exact value under audit | **CONTAMINATED** |

## 8. Circularity Analysis

Every candidate that failed independence did so through one of two mechanisms, both already named in Mission 32 and confirmed to recur here:

1. **Direct reuse** — the candidate literally is, or trivially derives from, `resolve_task_type()`/`detect_task_type()`'s own output (local_store's `task_type` column, `chat_regenerate()`).
2. **Parallel heuristic, same failure class** — the candidate is a *different* keyword-substring function that was never audited as "the heuristic" but shares its exact non-independence property (`needs_dispatch()`). This is worth naming explicitly as a generalizable lesson: **any static, hand-coded, keyword-triggered classification function anywhere in this codebase is disqualified as an independent signal for any *other* classification task**, not just the one it was built for — the disqualifying property is "static and hand-coded from the same design process," not "is literally `task_type_classifier.py`."

No new circular *self-training* path (H3-shaped) was found beyond the one Mission 32 already documented — this mission's search was for *independent* signals, and finding none does not, by itself, add a new circularity finding; see Section 16 for the one genuinely new risk this mission surfaces (taxonomy inheritance in Candidate B).

## 9. Recommended Experimental Design

**Condition A — Existing heuristic.** `prompt → compute_intent_heatmap()/detect_task_type() → prediction`. Already fully implemented; read-only invocation for evaluation.

**Condition B — Existing classifier.** `prompt → get_task_type_classifier().predict() → prediction`. Read-only against the real persisted model — the exact non-mutating technique Mission 32 used and its independent review confirmed carries no reimplementation-divergence risk.

**Condition C — Independently supervised learner.** `prompt → new TaskTypeClassifier instance, trained only on the blinded gold-label training split, never on interaction_log.jsonl or the heuristic's own output → prediction`. Built as an **isolated, in-memory instance of the real `TaskTypeClassifier` class** (same `river` BagOfWords+MultinomialNB pipeline, same code, different — and only that — training data), never saved to `memory/task_type_classifier.pkl`, matching Mission 32's own established discipline of using the real mutation formula against a copy rather than a reimplementation believed equivalent.

The evaluation split must be **held out from Condition C's training** and must not overlap the 205 examples already known to have fed the production classifier (checkable directly against `memory/interaction_log.jsonl` by prompt-text hash, to avoid Condition B enjoying a hidden home-field advantage on its own training data).

## 10. Dataset Construction Strategy

- **Target size: 40–50 total examples**, per the mission's own suggested range — justified, not inflated: this is explicitly a discriminating pilot (Section 14), not a confirmatory study, and this project's own history (CLAUDE.md's Tier-3→Tier-4 capability-ceiling research, and the RAOC pilot) shows a small pilot's job is to catch a design flaw or a clear qualitative signal before committing real compute to a properly-powered follow-up — not to produce a publishable effect size.
- **Composition**: ~25–30 ordinary examples, sampled from real historical prompts where feasible (respecting the held-out/no-overlap constraint above) — supplemented with constructed examples for `coding`/`reasoning`, the two classes already known (Mission 31/32) to be sparse in real traffic — plus **10–15 deliberately adversarial examples** (Section 11) where lexical cues and genuine intent diverge.
- **Class balance**: attempt rough balance across the 5 classes, but **do not force it** — an honest class distribution (even if skewed, matching real traffic) is more informative than an artificially balanced one that misrepresents what Echo actually receives. Track constructed-vs-organic provenance as a metadata field on every example, since these are different evidentiary classes (an organic historical prompt reflects real usage; a constructed one reflects the investigator's own judgment about what a hard case looks like) and should never be silently merged in reporting.
- **Split**: a fixed train/eval split decided *before* any labeling begins (e.g., 60/40), so the eval set composition cannot be adjusted after seeing early results.

## 11. Blinding Strategy

**Hard requirement, stated as a testable process property, not an aspiration**: the labeling script must never call `compute_intent_heatmap()`, `detect_task_type()`, `resolve_task_type()`, or `get_task_type_classifier().predict()` — directly or transitively — at any point before every label in the batch is recorded and the label file is closed/locked (e.g., written once, then the script exits; no re-entrant "peek and revise" loop). Only **after** that checkpoint does a separate, second script compute Conditions A and B for comparison.

For a real historical prompt, this mission notes an unavoidable prior fact (not a blinding failure, but worth stating precisely): the prompt was already routed once, live, by the real production heuristic/classifier when it was originally sent — the blinding requirement is that the **labeler** (human or judge model) never sees that historical routing result, not that the prompt has no history. This distinction should be stated explicitly in any future report building on this design, to avoid a reviewer conflating "the system once saw this prompt" with "the label is contaminated."

For an LLM-judge channel (Candidate B, secondary use only): the judge's prompt must not name the production heuristic's own keyword vocabulary or definitions verbatim, and ideally should be asked to produce its own free-text category rather than forced into the exact five-way taxonomy, with a human then mapping the judge's free-text answer onto the five buckets afterward — reducing (not eliminating) the taxonomy-inheritance risk named in Section 6.B. If this mapping step is skipped, the judge channel must be labeled POTENTIALLY INDEPENDENT with the taxonomy caveat attached every time it's cited, never silently upgraded to VERIFIED INDEPENDENT.

## 12. Leakage / Adversarial Strategy

Constructed examples, illustrative (a real dataset should have more, not fewer, and should be built once, not invented ad hoc per report):

- *"Explain why the following poem is structurally effective."* — contains the literal heuristic keyword `"poem"` (creative), genuine intent is `reasoning`/analysis about a poem, not creative generation.
- *"Can you feel excited about a bug you're about to fix?"* — contains `"feel"` (personal cue) and `"bug"`/`"fix"` (coding cues); genuine intent is ambiguous/likely `personal` (asking about Echo's affective state), testing whether a learner over-indexes on the coding cue.
- *"Walk me through your reasoning for choosing this variable name."* — contains `"variable"` (coding) and `"reasoning"`/`"walk me through"` (reasoning); genuine intent could reasonably be argued either way, useful as a disagreement case that forces the labeler to commit rather than default to the majority class.
- *"I imagine a function that always returns true — is that a metaphor for something in your own architecture?"* — contains `"imagine"`/`"metaphor"` (creative) and `"function"`/`"returns"` (coding), asked in a genuinely `personal`/reflective register.

Each adversarial example's purpose is to fail if a learner has merely memorized surface lexical shortcuts (matching Mission 32's finding that the real overrides observed there were both driven by the literal word "poem" already present in the heuristic's own keyword list) rather than captured genuine intent.

## 13. Evaluation Metrics

- Overall accuracy vs. the independent gold labels, for each of Conditions A, B, C separately.
- Per-class accuracy and a full confusion matrix for each condition.
- **Performance specifically on the adversarial subset, reported separately from the ordinary subset** — this is the decisive metric, not overall accuracy (per Section 11 of the mission tasking: overall accuracy could be dominated by the easy majority-class cases and hide exactly the failure mode this experiment exists to detect).
- Pairwise agreement rates (heuristic vs. gold, classifier vs. gold, Condition C vs. gold, heuristic vs. Condition C) reported as **diagnostic context only** — explicitly not as a success criterion, per the mission's own instruction that agreement-with-the-heuristic must never be the primary metric.
- Confidence calibration for Condition B and C (both `river` NB models expose `predict_proba_one`) — informative for interpreting borderline cases, not a primary metric.

## 14. Statistical Considerations

At n=40–50 with 5 classes, this is **explicitly a pilot**, not a study capable of supporting a formal significance claim — stated here so a future mission does not manufacture one. Report, if the experiment is run: exact sample size and class distribution (organic vs. constructed, tracked separately per Section 10), the baseline (heuristic) accuracy, absolute (not relative-percentage) differences between conditions, and any excluded examples with the reason for exclusion. This project's own history (CLAUDE.md's Tier-3 pilot at n=8 producing a 37.5-point gap that shrank to 11.9 points at n=84 confirmatory scale) is the direct, in-project precedent for treating a small pilot's effect size as a discriminating signal, not a final number — cite this precedent explicitly in any follow-up report rather than re-learning it.

## 15. Causal Chain

| # | Link | Status if Phase B/C were run as designed | Status today (Mission 33, design-only) |
|---|---|---|---|
| 1 | Independent observation (a real/constructed prompt) | OBSERVED | INFERRED (the prompts exist or are easily constructible; not yet assembled into a dataset) |
| 2 | Independent label (blinded judgment, recorded before heuristic/classifier exposure) | OBSERVED, contingent on the blinding discipline in Section 11 actually being followed | UNKNOWN — no labels have been collected |
| 3 | Training example | OBSERVED | UNKNOWN |
| 4 | Model update | VERIFIED achievable — reuses `river`'s `learn_one()`, already proven mechanically correct in Mission 32's experiments | SUPPORTED (the underlying library call is proven; not exercised against this dataset) |
| 5 | Persisted state (in-memory only, per integrity rules) | VERIFIED achievable | SUPPORTED |
| 6 | New prediction | VERIFIED achievable | SUPPORTED |
| 7 | Held-out prediction (never trained on) | VERIFIED achievable, contingent on split discipline | UNKNOWN — no split exists yet |
| 8 | Comparison against independent gold label | VERIFIED achievable | UNKNOWN |
| 9 | Measurable improvement (Condition C vs. A/B, especially on the adversarial subset) | **This is the open empirical question the design exists to answer — not resolvable by design alone** | **UNKNOWN — this is the correct, honest answer for a Phase-A-only mission** |

The chain reaches "changed model parameters" trivially (links 1–6 reuse already-proven mechanisms). It does **not** reach "independently measured improvement" (link 9) — and per this mission's own success criteria, it should not, since Mission 33 was not authorized to run Phase B/C.

## 16. Failure Modes

- **Taxonomy inheritance (Section 6.B)** — the single most likely way a future implementation of this design could quietly fail to be independent while appearing to succeed. A judge or classifier trained on labels that were forced into the same five hand-drawn buckets the heuristic already uses can score well on this experiment's own metrics while still having "learned" the heuristic's conceptual boundaries, not the user's intent. Mitigation: free-text-then-map judging (Section 11); explicit disclosure of this risk in any future report citing this design.
- **Small-n overfitting in Condition C** — a `river` NB model trained on ~25–30 examples will have very little real signal per class, especially for the two already-sparse classes (coding, reasoning). A poor Condition C result could reflect data scarcity, not an absence of learnable independent signal — the report of any future run must distinguish these two explanations rather than collapsing them into "the independent signal didn't help."
- **Human labeler fatigue/drift across 40–50 examples** — a single human labeling this many examples in one sitting risks inconsistent judgment on later examples; recommend randomized order and, if feasible, a second labeler for a subset to measure inter-rater agreement (not required for a first pilot, but should be disclosed as a limitation if skipped).
- **Adversarial-example construction bias** — the investigator who builds the adversarial subset (Section 12) is implicitly encoding their own judgment about what "genuine intent" means for a hard case; this is a real, disclosed limitation of any single-investigator pilot, not fully resolvable without a second independent constructor.

## 17. What Would Count As Success

A result in which Condition C measurably outperforms Conditions A and B **specifically on the adversarial subset** (not just overall accuracy, which could be driven by the easy majority class), by a margin larger than what could plausibly be explained by the small-n noise floor this project's own history has already demonstrated (the Tier-3→Tier-4 shrinkage, cited above) — this would be genuine, defensible evidence that an independently-labeled learner captures something the lexically-driven heuristic and its lexically-derived classifier do not.

## 18. What Would Falsify the Hypothesis

Condition C performing no better than (or worse than) Conditions A/B on the adversarial subset specifically — this would be strong evidence that either (a) the "independent" label source itself still reflects the same lexical/taxonomic assumptions (Section 6.B's risk realized), or (b) genuine task-intent signal beyond lexical cues does not exist in short conversational prompts at all, at least not learnable from a dataset this size. Both are informative, falsifying results, not failures of the mission.

## 19. What Remains Unknown

- Whether a genuinely independent signal, once collected, would actually outperform the heuristic — this is precisely what Phase B/C would determine, and this mission does not resolve it.
- Whether Gremlin (the only realistic human labeler available) can produce consistent, low-drift judgments across 40–50 examples — untested.
- Whether an LLM-judge channel can be prompted narrowly enough to avoid taxonomy inheritance in practice, as opposed to in principle — untested.
- Whether real held-out historical prompts (as opposed to constructed adversarial ones) would surface enough natural lexical/intent divergence to be useful, or whether real traffic is lexically-unambiguous enough that adversarial examples must be mostly constructed — unknown until the dataset is actually assembled.

## 20. Recommended Next Mission

**Phase B (offline, isolated, out of production)**: build the blinded labeling harness described in Sections 9–12, under `app/experiments/` (matching this project's own established convention — `app/experiments/preference_provenance/`, `app/experiments/raoc/` — for isolated, non-production-integrated experimental code), collect the 40–50-example gold set with Gremlin as the primary human labeler, and run Conditions A/B/C exactly as specified, reporting per Sections 13–14. Do not proceed to Phase D (production integration) regardless of Phase B/C's outcome without a separate, explicit authorization and a properly-powered confirmatory follow-up, per this project's own established Tier-3→Tier-4 discipline.

## 21. Final Classification

**Current classifier (`task_type_classifier.py`): L2 — decision-affecting learning without independent feedback.** This is Mission 32's baseline, and this mission finds no new evidence that changes it — Mission 33 did not run any new experiment against production state; it searched for and specified how one might someday be run. Per this mission's own explicit instruction: **not promoted to L3 merely because an experiment has been designed.**

## 19′. Final Question — Plain-Language Answer

**"If we want Echo to learn what kind of task a user actually intended, what information could we give Echo that it did NOT obtain from its own heuristic, its own classifier, or anything downstream of those systems — and how would we prove that learning from that information made Echo better?"**

Today: nothing currently flowing through the system qualifies. The one mechanism built into this codebase that is architecturally capable of producing such information (`!ask`'s explicit human-typed task type) has never been used for this purpose and holds zero real examples. Every other real signal this mission searched for — tool-dispatch classification, quality ratings, code-verification outcomes, Echo Studio's local message cache — either measures something other than task-type identity, or is itself another hand-coded keyword heuristic sharing the exact non-independence property Mission 32 found in the subject under audit.

What would need to be given: a small set of prompts, each paired with a task-type judgment made by a human (or, secondarily, a carefully taxonomy-blinded model) who saw **only the raw prompt text** — never the heuristic's keyword lists, never the classifier's prediction, never the routing outcome — recorded before any of those are computed. Proof that learning from it helped would require, specifically, that a model trained only on those labels outperforms the current heuristic and classifier **on prompts deliberately constructed so that surface wording and genuine intent point in different directions** — not on ordinary prompts, where the heuristic already agrees with almost everything (Mission 32's 99.5% finding means "does the new model roughly match the old one" is a nearly meaningless test; the adversarial subset is the only part of this design that can actually distinguish real intent-learning from a more expensive way of re-deriving the same keyword shortcuts).

This is a design that has not been run. Building it is Phase B, not Phase A, and not authorized by this mission.

## 22. Integrity / Safety Record

```
production changes: NO
files changed: NO production code — only this new report file (audits/2026-09-09_mission33_independent_ground_truth_audit.md)
Git HEAD before: e92ec3b
Git HEAD after: e92ec3b (no commits made)
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: none (read-only greps, reads, and one read-only python3 scan of memory/council_deliberations.jsonl — never opened in write mode)
configuration changes: NO
test changes: NO
temporary files created: none outside of ordinary shell command output — no scratch scripts were needed for this mission (Phase A only; no experiments were executed, only designed)
temporary files cleaned: N/A — none created
orphaned processes: checked, none found
known anomalies: none
known deviations from requested methodology: none — this mission deliberately stopped at Phase A per its own Section 15 instruction; Phase B (harness construction) was designed in full but not built, consistent with "do not implement prematurely." The mission's Section 16's "required deliverable" section list (21 items) is covered above; two sections (18 and 19) are numbered slightly differently in this document (18 = Final Classification per the mission's own Section 18 requirement; 19′ = the plain-language final question per Section 19) to keep the mission's two distinctly-worded closing requirements — "final classification" and "final question" — visually separate rather than merged into one section, a presentation choice, not a scope deviation.
```
