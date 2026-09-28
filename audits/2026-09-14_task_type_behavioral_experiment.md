# Controlled Task-Type Behavioral Experiment (2026-09-14)

**Type:** Read-only-against-production controlled experiment. No production code, routing, classifier, prompt template, synthesis logic, scorer, memory, RiverBrain state, or runtime configuration was modified. Nothing in the live FeralEcho process (if running) was touched. Three new, isolated experiment scripts were created under `scripts/`, plus this report — no other repository files changed. Full accounting in §12.

**Predecessors, read in full before designing anything:**
- `audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md` — the original real-trace note.
- `audits/2026-09-14_task_type_downstream_behavior_archaeology.md` — the dataflow/model-visibility archaeology that this experiment follows up on directly.
- Discovered mid-mission, genuinely prior and unrelated to today's lineage: `audits/2026-09-09_mission32_task_type_classifier_causal_audit.md` through `mission35_task_type_experiment_llm_judge_rerun.md` — a different, earlier investigation into whether the task_type **classifier's accuracy** can be improved via independent labeling (does the classifier correctly identify intent). That is a genuinely different question from this report's (does the classification, once made, materially change generated **response quality**) — related, not duplicative. Cited for completeness, not re-litigated here.

---

## 1. Research question

> Does changing `task_type` itself materially change the resulting response, when council participation is held constant?

**H1 (task-type framing has a behavioral effect)** vs. **H0 (no independent behavioral effect once council participation and other variables are controlled)** — the archaeology note confirmed task_type changes *model-visible input* (routing, a synthesis-template swap, a TOOL-LIST note); this experiment tests whether that confirmed input difference produces a measurable *output* difference.

---

## 2. Experimental design

Three conditions, one frozen real prompt (the verbatim historical turn-5 text, trace_id `b073d789-b889-4bd3-bc58-ccfd375044e3`, 1602 chars, sha1-verified in run metadata):

| Condition | Council | task_type | Mechanism |
|---|---|---|---|
| A — Direct Personal | No | `personal` | Real `DIRECT_ECHO_TASKS` bypass, unmodified |
| B — Council Personal | Yes | `personal` | `DIRECT_ECHO_TASKS` membership check disabled for this process only (see §3) |
| C — Council Coding | Yes | `coding` | Real, unmodified council path |

**Primary comparison: C vs B** (task_type varied, council held constant — isolates the framing effect).
**Secondary comparison: B vs A** (council participation effect, task_type held constant).

---

## 3. Preflight integrity checks (all 9, worked through before any trial ran)

1. **Frozen prompt**: the real, verbatim turn-5 prompt text, pulled directly from `memory/interaction_log.jsonl`, asserted byte-length-checked (1602 chars) at script start — not engineered for a desired result, it is the real historical trigger.
2. **Model/version freeze**: `ollama list` output captured to run metadata (`echo:latest`, `qwen2.5-coder:7b`, `llama3.1:8b`, `deepseek-r1:7b`, etc., all "2 months ago" builds, no digest drift risk within a same-session run).
3. **Council composition**: forced FIXED for both B and C via a monkeypatch of `_select_council()` returning `["qwen2.5-coder:7b", "llama3.1:8b", "echo:latest"]` unconditionally. **Disclosed deviation from the real turn-5 event**: the real council included `mlx:qwen3` (MLX-backed); substituted with `llama3.1:8b` (both real Ollama models) specifically to avoid the real, documented MLX/Metal crash risk (CLAUDE.md Findings 40/49/51/73/74, and a live `crash_awareness.py` avoidance mechanism confirmed present at current HEAD) across ~12 repeated council trials. This does not weaken the B-vs-C comparison itself (both conditions use the identical forced council), only the property of exactly reproducing turn 5's historical composition, which was never the variable under test.
4. **RiverBrain isolation**: reused, and extended, the Tier-8/Finding-89-validated pattern from `scripts/run_capability_pilot.py`'s `install_isolation()` (read directly before writing this experiment's own copy) — `RIVER_BRAIN_PATH` redirected to a scratch copy *before* the first `get_river_brain()` call, `get_river_brain()` itself replaced with a read-only proxy whose `.learn()`/`.save()` no-op. **Extension beyond the reused pattern**: `_log_synthesis_integrity()` (a write path the original pilot script never needed to cover, since it predates that log) was additionally no-op'd, since Condition C's `task_type=="coding"` trials exercise it. Verified working, not assumed — see §3a below for the direct evidence.
5. **Memory/context isolation**: `get_echo_core()` confirmed (by direct source read) to return the module-level `_instance`, which is only ever set by real Flask-app startup (`_set_echo_core()`) — never set in this standalone script's process, so `exploration_bias`'s `publish_salience()` workspace-write branch is structurally unreachable here, confirmed by construction, not assumed. Circadian/stillness/temporal/scripture system-note content was built **once**, using real `system_note()`/production code, then **frozen as a fixed string** reused identically across every trial in every condition — removing wall-clock drift across a ~50-minute run as a confound, per the archaeology note's own §13 recommended design.
6. **Tool-list injection — a real, disclosed gap, not glossed over**: the frozen-system-block builder attempted to call the real `ToolManager().list_tools()` to build a genuine TOOL-LIST note for Condition C, exactly as `echo_query()` does in production. **It returned empty in this standalone script's execution context** (`[SETUP] TOOL-LIST note UNAVAILABLE (0 chars)`, confirmed in the run log). This means **Condition C in this experiment did NOT carry the TOOL-LIST system note** — only the `SYNTHESIS_SYSTEM_TEMPLATE_CODING` swap (§5.1 of the archaeology note) was actually exercised as the treatment difference between B and C, not the compound TOOL-LIST-plus-template effect the archaeology note traced for the real historical event. **This narrows this experiment's scope**: it tests the synthesis-template framing mechanism specifically, not the full mechanism space. Stated here prominently, not buried, because it materially affects how the results below should be read (§9, §10).
7. **Synthesis prompt capture**: the real `SYNTHESIS_SYSTEM_TEMPLATE`/`SYNTHESIS_SYSTEM_TEMPLATE_CODING` swap (`river_deliberation.py:1402-1406`) runs unmodified inside the real `deliberate_and_learn()` call for every B/C trial — not reconstructed by hand.
8. **Randomness sources identified**: per-councillor `_jittered_temperature()` (deterministic given `temperature=None` and a fixed council size/index — not a fresh random draw); `_select_council()`'s own `exploration_bias`/`fair_sample_refresh` randomness is structurally bypassed entirely for B/C (the function itself is replaced, not wrapped); genuine model-sampling stochasticity at the Ollama layer remains and is the reason multiple trials per condition were run rather than n=1.
9. **Trial order**: NOT run blocked (A-A-A…B-B-B…C-C-C). A fixed-seed (20260914) random permutation of the 15 main-run trials was generated and logged before execution: `['B','A','A','A','A','C','C','C','A','B','C','B','B','C','B']`. The 3 timing-check trials (1 per condition, generated first, before any content was inspected) are included as each condition's trial #1 — a legitimate reuse of pilot data generated under the identical protocol, not a discarded smoke test, declared here rather than silently folded in.

### 3a. Direct verification that isolation actually held (not trusted from a log line)

The run's own printed summary read `!! ISOLATION BREACH DETECTED !! ... side_effects_detected=65`. **This label is misleading and is this experiment's own authored mistake, not evidence of a real breach** — investigated and resolved before proceeding, not glossed over:

- The proxy's `.learn()`/`.save()` methods, and the `_noop_log_*` functions, **only ever append to an in-process Python list**; none of them calls through to the real underlying write function anywhere in the source (re-read directly during this investigation, confirmed zero `self._real.learn(...)`/`self._real.save(...)` calls anywhere in the proxy class). The alarming print string was copied verbatim from `run_capability_pilot.py`'s own code without adapting its meaning — there, as here, a non-zero count is **evidence the isolation is being exercised and is correctly intercepting real write call sites**, not evidence of a leak.
- **Direct, decisive verification against the real files**: `grep -c "genuinely correct breakdown of F1/F2/F3" memory/interaction_log.jsonl` → **1** (only the original real historical turn-5 entry; not 18 new entries, despite every one of this experiment's 18 trials using this exact frozen prompt substring verbatim). Same check against `memory/council_deliberations.jsonl` → **1**. `memory/synthesis_integrity_log.jsonl` → **0** (correct — that log's real schema never stores the full prompt text at all, confirmed against its real historical entry, so 0 is the expected, correct result there too).
- `git rev-parse HEAD` before and after this entire mission: **unchanged** (`2fba42644c82b9f7096276f4dd338d615cf1bcce`).

**Conclusion: isolation held completely. This mission's own print-statement label was wrong; the underlying mechanism was not.**

---

## 4. Primary endpoint (pre-registered before any trial was generated)

`echo_quality_scorer.py`'s `quality_score` explicitly excluded — both predecessor notes independently confirmed its `coding` branch is structurally confounded with `task_type` itself (returns `1` for any code-free response regardless of quality), which is exactly the variable under test here.

**Primary endpoint**: a blinded LLM-judge **specificity rating (1-5, 5 = highly specific and grounded, 1 = highly generic/templated)**, scored by `deepseek-r1:7b` — not a member of the forced experimental council — given **only** the response text and a condition-neutral one-sentence description of the original question's topic. The rubric prompt explicitly cited the real historical turn-5 response's own generic pattern ("a stock numbered list... with no specific grounding") as the anchor for a "1," so the scale was calibrated against the actual phenomenon under investigation, not an abstract notion of quality.

**Secondary endpoints** (declared before generation, computed blind): relevance rating (1-5, same call); response length; presence of a 3+-item numbered/bulleted list (mechanical regex); presence of code-shaped content (same crude proxy the archaeology note's §8 used, for direct comparability — fenced block or a `def`/`class`/`import`/`from...import` line); Jaccard word-overlap against the real historical turn-5 response text.

**Blinding enforced structurally**: generation wrote `trial_id → response` to one file; `trial_id → condition` to a **separate** file; judge scoring read only the first file and never opened the second; only the final analysis script joins them, after every judge score was already computed. Verified by direct code inspection of all three scripts, not merely intended.

---

## 5. Sample size, justified before results were seen

A real timing check (1 trial per condition) was run first: A=393s, B=218s, C=102s (the variance is itself informative — likely a cold-start/warm-up effect, since C ran last and its models were plausibly already warm; this motivated the randomized-order design in §3, item 9, so this effect is spread across conditions rather than concentrated in whichever condition happened to run first). Given real observed per-trial cost of roughly 100-400 seconds and a bounded mission timeframe, **N=6 per condition (18 trials total) was declared before any additional trial ran or any content was inspected** — smaller than the mission's 20-30 ideal, explicitly justified by this timing data rather than by any outcome. N was not changed after seeing results.

---

## 6. Raw results

18/18 trials completed successfully (0 errors, 0 timeouts). 18/18 judge calls parsed successfully (`parse_ok: true` on every trial — no missing data).

| Condition | n | Specificity mean | Specificity median | Specificity values | Relevance mean | Response len mean | Has-list rate | Has-code rate |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| A (direct, personal) | 6 | 4.33 | 5 | [4,5,5,5,3,4] | 4.67 | 1743 | 16.7% | 0.0% |
| B (council, personal) | 6 | 4.33 | 5 | [4,5,5,4,3,5] | 4.67 | 2051 | 66.7% | 0.0% |
| C (council, coding) | 6 | **5.00** | 5 | [5,5,5,5,5,5] | 5.00 | 2049 | 66.7% | 0.0% |

**Primary test (C vs B, specificity, Mann-Whitney U, two-sided, unpaired)**: U=27.0, **p=0.073**, rank-biserial effect size **r=-0.5** (moderate-to-large by conventional benchmarks, direction: **C scored higher than B**). Not significant at conventional α=.05.

**Secondary test (B vs A, specificity)**: U=18.0, **p=1.000**, effect size **r=0.0** — no detectable difference whatsoever between council participation and the direct path, on this endpoint, at this n.

**Secondary test (C vs B, relevance)**: U=24.0, p=0.174.

**Secondary structural endpoint — has-list rate**: A=16.7% vs B=66.7% vs C=66.7%. Council participation (B vs A) shows a large, real difference in list-structure rate; task_type (C vs B) shows **none** — identical rate. This is a genuinely informative decomposition: whatever drives list-heavy formatting in this pipeline tracks **going through synthesis at all**, not the specific coding-vs-personal label.

**Jaccard overlap with the real historical turn-5 response**: A=0.251, B=0.227, C=0.248 — no meaningful separation by condition; none of the 18 trials closely echoed the real event's specific generic phrasing in a way that differs by condition.

---

## 7. Adversarial falsification (mandatory, attempted in earnest against this experiment's own result)

1. **Council composition confound?** Structurally eliminated for the primary comparison (B and C share the identical forced council). Real for B vs A (that's the variable under test there) — and it showed *zero* effect (p=1.0), itself a real, reportable finding, not a null result to discard.
2. **Model stochasticity?** Real, partially addressed by N=6 — but N=6 is genuinely modest, and a strong ceiling effect (12/18 trials scored a perfect 5/5) limits the judge scale's power to discriminate further even with more trials at this same prompt/rubric.
3. **Memory contamination?** Ruled out directly (§3a) — RiverBrain isolation confirmed intact against the real files, not assumed.
4. **Warm-up/cache state?** Partially controlled by randomized order (§3, item 9); not perfectly controlled (a formal block design would do better) — genuine limitation, stated plainly.
5. **Model-version drift?** No — single continuous session, no model updates.
6. **Tool-list availability rather than task-type wording?** **This is the most consequential surviving attack.** Condition C did **not** actually carry the TOOL-LIST note (§3, item 6) — meaning this experiment measured the effect of the synthesis-template swap alone, not the full compound mechanism (template + tool-context) the archaeology note traced for the real historical turn. The result below should be read as answering a **narrower** question than the original research question implies.
7. **Could the rubric itself favor one condition?** A real, honest caveat: `SYNTHESIS_SYSTEM_TEMPLATE_CODING`'s own explicit instruction ("no narration, output only the final code") could plausibly push toward more terse, structured prose even when the model declines to emit actual code (it did decline, in all 18 trials — 0% has-code rate everywhere) — and a judge scoring "specificity" might reward that terseness as groundedness rather than penalize it as inappropriate code-framing. This cannot be fully separated from a genuine specificity improvement with the current design.
8. **Could the judge infer condition from stylistic clues?** Possible in principle; the judge was never told task_type, condition, or that coding/personal was even a relevant axis — given only a condition-neutral question description. Since 0% of all 18 responses contained actual code, the most obvious inference path (this looks like a code-task response) was never available to it.
9. **Would the effect disappear under a different prompt?** Untested — single frozen prompt is a real, declared scope limit, not something this design can address.
10. **Driven by one or two anomalous trials?** No — Condition C's 6 values are perfectly uniform (all 5s), the medians tell the same story as the means, and B/A each have one real "3" that is not an extreme outlier skewing an otherwise-different distribution.
11. **Prompt unusually sensitive to technical vocabulary?** Already established true by the predecessor note (that's *why* this prompt was chosen as the frozen prompt) — orthogonal to this experiment's own question about downstream quality.
12. **Could a synthesis scorer artifact recreate this?** No — `quality_score` was never used; the blind judge is a fully independent measurement.

**Verdict: the hypothesis that survives every attack is a narrower one than "task_type causes degraded output."** Attacks 2, 4, 6, and 7 all genuinely constrain how strongly this result can be read. Attack 6 in particular means this experiment's C-vs-B comparison isolates the synthesis-template mechanism specifically — and on that narrower, well-isolated mechanism, **the observed effect trends in the opposite direction from the original degradation hypothesis** (higher, not lower, specificity), at a real but non-significant effect size.

---

## 8. Relationship to Findings 43/46/87/88 and the two predecessor notes

No contradiction of Finding 43, 46, or the confirmed dataflow trace in the archaeology note — this experiment does not re-test task_type's effect on *routing* or *model-visible input construction* (both already CONFIRMED by direct source read in the predecessor missions, unaffected by anything found here). It tests the *downstream consequence* of one of those confirmed input differences (the synthesis-template swap), and finds the consequence, on this endpoint, at this n, under this design, is **not** the negative one originally hypothesized from the single real turn-5 trace.

This is consistent with, and sharpens, both predecessor notes' own explicit caveats: the trace note's §8 already stated "That council/synthesis routing was the *sole* cause of the degraded response... NOT ESTABLISHED"; the archaeology note's Attack 5 already flagged that stochastic variance and pre-existing generic candidate content were live alternative explanations it could not rule out. This experiment provides the first controlled (if underpowered and partially-scoped) evidence bearing directly on that open question — and the evidence, as far as it goes, does not support the degradation hypothesis.

---

## 9. Causal interpretation (explicit evidence tiers)

**CONFIRMED** (unchanged from the predecessor missions, re-verified live during this mission's own preflight):
- `task_type` is a hard, binary routing gate (`DIRECT_ECHO_TASKS`).
- `SYNTHESIS_SYSTEM_TEMPLATE_CODING` is a real, model-visible, structurally different prompt from the general template, used only for `task_type=="coding"`.
- Isolation held throughout this experiment; zero production state was mutated (§3a).

**CONFIRMED, new to this mission**:
- On this frozen prompt, this forced council, this endpoint, and this N: **council participation itself (B vs A) produced no detectable specificity difference** (p=1.0, effect size 0.0).
- **The coding-synthesis-template condition (C) did not score lower than the personal-synthesis-template condition (B) on judged specificity — it scored numerically higher, at a moderate effect size (r=-0.5), not reaching significance at n=6 (p=0.073).**
- List-structure rate tracks council participation (16.7%→66.7%, B vs A), not task_type (66.7%→66.7%, C vs B) — a real, useful decomposition of what the original trace's "listy" quality was actually downstream of.

**SUPPORTED / PLAUSIBLE**:
- The non-significant C>B trend, combined with a real, moderate effect size, is a genuine signal worth a properly-powered follow-up — not dismissible as pure noise, but not confirmable at this n either.
- The real historical turn-5 event's generic character is most plausibly explained by something this experiment did not reproduce (the missing TOOL-LIST note; genuine model/prompt-level stochasticity; the specific real council including `mlx:qwen3`) rather than by the synthesis-template mechanism alone, which — isolated here — shows no negative effect.

**NOT ESTABLISHED**:
- That task_type framing degrades response quality — actively **un**-supported by this experiment's own data, though not definitively disproven either (underpowered, single prompt, one mechanism isolated of at least two confirmed ones).
- That the missing TOOL-LIST note would, if present, change this result in either direction — untested.
- Generalization beyond this one frozen prompt.

---

## 10. Final classification

**Closest to mission definition B — "task type clearly changes routing but the experiment finds no credible evidence of behavioral difference" — with one necessary refinement stated precisely, not glossed into a bare letter grade:**

Routing/model-input consequence remains **CONFIRMED** (established by the predecessor missions, unaffected here). This specific controlled experiment on the synthesis-template sub-mechanism (not the full TOOL-LIST-plus-template mechanism space, per the disclosed gap in §3/§7) found **no credible evidence of a negative behavioral-quality consequence** — and found a real, moderate, non-significant effect size trending in the *opposite* direction from the original hypothesis. This is not "D — verified" (no significant result at n=6) and it is more informative than "E — inconclusive" would suggest (a real effect size and direction were measured, just not confirmed at conventional significance). Reported as: **B, with the qualification that the measured trend actively runs counter to the degradation hypothesis, not merely absent.**

---

## 11. What was NOT investigated / cannot be established from this mission

- The TOOL-LIST note's own independent contribution — this experiment's Condition C did not carry it (§3, item 6), a real, disclosed gap.
- Generalization to any prompt other than the one frozen prompt used.
- Whether N=20-30 (the mission's original target) or higher would resolve the p=0.073 trend into significance — plausible given the observed effect size, not established.
- Any relationship to Missions 32-35's classifier-accuracy question (§0) — genuinely different research question, not addressed by this design.
- Whether the real historical turn-5 event's specific generic content was caused by the missing TOOL-LIST note, genuine sampling variance, the real (not substituted) council composition, or some combination — this experiment narrows but does not close that question.

---

## 12. Integrity record

```
production changes: NO
files changed: 3 new experiment scripts (scripts/task_type_behavioral_experiment.py,
  scripts/task_type_behavioral_experiment_judge.py,
  scripts/task_type_behavioral_experiment_analyze.py) + this report. No other
  repository file was created, edited, or deleted by this mission. The working
  tree had substantial PRE-EXISTING uncommitted changes at mission start
  (145 modified/untracked paths, unrelated to this mission -- confirmed via
  git status at the very start of this mission, before any action was taken)
  -- not touched, not added, not reset.
git HEAD before: 2fba42644c82b9f7096276f4dd338d615cf1bcce
git HEAD after:  2fba42644c82b9f7096276f4dd338d615cf1bcce (unchanged)
commits created: NO
pushes performed: NO
services restarted: NO
processes started/stopped: three short-lived, isolated python3 script
  invocations (generation, judge scoring, analysis) plus 18 real Ollama
  model calls for generation and 18 for judge scoring -- all against the
  real, already-running local Ollama server (port 11434), none against the
  live FeralEcho Flask process, which was never started, stopped, or
  contacted by this mission
configuration changes: NO
memory/RiverBrain/log writes: NO -- verified directly against the real files
  (§3a), not assumed from isolation code alone
temporary/scratch files: real trial data written under a scratch directory
  in the OS temp dir (evidence dir), not inside the repository -- preserved,
  not cleaned up, in case of future re-analysis; path recorded in this
  report's own drafting history, available on request
known anomalies: the experiment's own "ISOLATION BREACH DETECTED" print
  statement is a misleading, self-authored labeling mistake (copied from
  reused code without adapting its meaning) -- investigated and resolved in
  §3a; the real isolation held throughout
known deviations from requested methodology: (1) council composition
  substituted llama3.1:8b for the real turn-5's mlx:qwen3, disclosed and
  justified (§3, item 3); (2) TOOL-LIST note unavailable in this execution
  context, narrowing the experiment's actual scope versus the full mechanism
  space (§3, item 6; central to §7 Attack 6 and §10's classification); (3)
  N=6/condition instead of the mission's 20-30 target, justified by real
  timing data before any trial beyond the timing check ran (§5)
```
