# FeralEcho: The Highest-Information-Gain Experiment

Design only. Nothing in this document was implemented or executed. Full structured detail is in
`audits/highest_information_gain_experiment.json`.

## 1. Current Evidence Synthesis

Across every forensic pass conducted so far (preference formation/retention, content-level learning,
C1 behavioral persistence, self-editing, the self-edit feedback loop, curiosity, reflection, planning,
memory, metacognition, orchestration, autonomy, recovery, `echo_projects`, tool use), one tension keeps
recurring, unresolved, in a different guise each time: **is poor coding-task performance caused by
pipeline/architecture friction, or by the underlying local model pool's own capability ceiling?**

- Self-edit's own prompt families (`prose_stripping`, `quality_scoring`) non-converged and were
  retired after repeated near-duplicate failures.
- `echo_projects` has a real, measured **0/61** end-to-end success rate across its entire history.
- Finding 43's direct-conversational test found the exact task self-edit's own pipeline fails at also
  produced a confidently-explained, non-functional answer — with one raw councillor fabricating a
  specific "verified" output that is false when actually run.
- The self-edit fitness gate's own quality metric (AST node count) is confirmed **saturated at a
  perfect ceiling** for all 25 currently-retained deploys, meaning it cannot discriminate the very
  population it's supposed to be gating.

No experiment in this investigation's history has cleanly separated "the model can't do this" from
"the pipeline is stopping a model that could." Every other major open question (preference formation's
clean P1.2 null, memory's temp>0-confounded null, C1's already-fairly-well-established 75% compliance,
the self-edit targeting loop's already-extensively-characterized near-null) has either already received
substantial rigorous attention, or does not by itself distinguish H1 from H2 from H4 as directly as this
one does.

## 2. Competing Hypotheses

- **H1 — Integration**: primary limitation is insufficient connection between real, existing
  capabilities; small closures would produce substantially more emergent/adaptive behavior.
- **H2 — Capability ceiling**: existing components are already near the practical ceiling of current
  models/hardware/architecture; further connection produces little meaningful improvement.
- **H3 — Measurement**: current instrumentation may be failing to detect real, useful interactions.
- **H4 — Model ceiling**: the architecture could support the desired loops, but the local model pool
  itself is the limiting factor.

## 3. Candidate Experiments Considered

Six candidates were scored against all eight ranking criteria (full detail in the JSON's
`candidate_experiments_considered`): the recommended raw-vs-pipeline-vs-council coding benchmark;
memory-retrieval temp=0 replication; C1 compliance at larger N; a full-power self-edit arbitration
RCT; a council-rating cursor repair simulation; and a preference-formation re-test with an alternative
design. Each was rejected for the recommended candidate for a specific, stated reason — most
commonly, narrower scope (bearing on only one of H1/H2/H3/H4, not the cross-cutting tension named in
§1) or dramatically lower sample efficiency (the full-power arbitration RCT needs up to 128 trials per
condition and a real ~25-minute post-deploy window each, against retrospective evidence that already
strongly suggests the answer).

## 4. Information-Gain Ranking

| Candidate | Info gain | Causal clarity | Falsifiability | Reproducibility | Sample efficiency | Cost | Safety | Effort |
|---|---|---|---|---|---|---|---|---|
| **Raw/pipeline/council coding benchmark** | **very high** | **high** | **high** | **high** | **high** | zero | high | low |
| Memory retrieval temp=0 replication | medium-high (narrow) | high | high | high | medium | zero | high | low |
| C1 compliance at larger N | medium (narrow) | high | medium | very high | very high | zero | high | very low |
| Full-power self-edit arbitration RCT | high in principle, low marginal | high | high | medium (needs maintenance window) | low | zero | high | medium |
| Council-rating cursor repair (offline) | low-medium (narrow) | high | medium | high | high | zero | high | low |
| Preference-formation re-test | medium (narrow) | medium | medium | high | medium | zero | high | medium-high |

The recommended experiment wins on the two criteria that matter most for this specific mission
(expected information gain and causal clarity) while being tied for best or near-best on every other
criterion — it is not merely "cheap," it is cheap **and** maximally informative, which is the
combination the mission asked for.

## 5. Recommended Experiment

**Raw-model vs. pipeline-framed vs. council-deliberated coding-task capability benchmark.** Give the
identical set of objectively-verifiable coding tasks to (1) a raw, single-model, clean call, (2) the
same task run through self-edit's own real pipeline machinery (F1 scan + kernel-sandboxed execution
test, never deployed), and (3) full multi-model council deliberation — score every candidate **only**
by real, sandboxed execution against a real check, never by AST count, gate-passage, or self-report.

This is the single experiment that can, in one design, produce evidence bearing on all four
hypotheses simultaneously, using entirely existing, already-verified infrastructure, at near-zero new
engineering cost, with no organic-traffic waiting window, and with zero production risk.

## 6. Exact Experimental Design

**Task set**: N=15 objectively-verifiable Python tasks, 3 tiers of 5:
- **Tier 1 (trivial sanity check)** — matched to tasks self-edit/`echo_projects` have historically
  *passed* (e.g., "deduplicate a list while preserving order").
- **Tier 2 (medium)** — matched to typical `echo_projects` spec complexity (e.g., "implement a
  fixed-capacity LRU cache with O(1) get/put").
- **Tier 3 (hard)** — deliberately seeded from **real historical failure cases** (a retired self-edit
  prompt family's own target shape, or Finding 43's real fabrication-case task), not invented from
  scratch, so difficulty-matching is genuine, not a guess.

Each task ships with a real, executable assertion script — never a self-reported claim.

**Conditions**:
- **1 — Raw model**: `river_deliberation._ollama_query(model_name, task_prompt, temperature=0.0,
  task_type="coding")` — Design B, no self-edit framing, no gating, and deliberately **not** routed
  through `echo_query()`/`deliberate_and_learn()` (avoids any `RiverBrain.learn()` side effect on real
  production statistics).
- **2 — Pipeline-framed**: the identical task, wrapped in self-edit's own real
  `_build_targeted_prompt()`-style framing, run through the real F1 scan
  (`scan_for_unsafe_operations()`) and the real kernel sandbox
  (`sandbox/run_script.run_sandbox_script_isolated()`, the same path F2 uses) — **without** ever
  calling `execute_self_edit()`/`perform_self_edit()` directly, so no production log/state file is
  touched.
- **3 — Council**: the identical task via `river_deliberation.deliberate_and_learn(task_type="coding")`
  — full real multi-model deliberation + synthesis, tagged with a distinct, identifiable source
  (`"capability_ceiling_benchmark"`) for later exclusion if desired.

**Scoring**: PASS/FAIL only, by actually executing the candidate inside
`sandbox/run_script.run_sandbox_script_isolated()` against the task's real assertion script — reusing
`code_verification.py`'s already-proven `verify_in_sandbox()`/`run_sandbox_script_isolated()` directly.
`echo_quality_scorer._score_response_quality()` is also recorded per candidate, purely to compute the
H3 discrepancy check — never used as the primary endpoint.

## 7. Controls

Same task set across all three conditions (a genuine within-task comparison, not just aggregate
rates); same model pool available to all; temperature fixed at 0.0 for conditions 1-2 (condition 3's
per-councillor jitter is disclosed as an intentional, not accidental, asymmetry — that IS part of what
condition 3 tests); randomized task order within each condition's run; a single model choice
(`rank_models("coding")`'s top real pick, held fixed) for conditions 1-2 specifically to isolate
pipeline-vs-raw from a routing-choice confound; zero writes to any real production file for conditions
1-2, and a disclosed, tagged, identifiable real effect for condition 3 only.

## 8. Primary Endpoint

**Real, sandboxed-execution-verified PASS rate per condition, per difficulty tier** — a 3×3 proportion
table (15 tasks × 3 conditions = 45 scored trials at the statistically-strongest sample size described
in §10).

## 9. Secondary Endpoints

AST-score vs. real-execution-verdict discrepancy rate (the direct H3 check); pass rate by difficulty
tier within each condition (does the pipeline degrade hard tasks disproportionately, or uniformly);
candidate latency per condition; and, for condition 2 specifically, an F1-block vs. F2-fail vs.
real-execution-fail breakdown, replicating `echo_projects`' own useful 3-way split (79%
F1-blocked/21% reached F2/100% of those failed) against a **different** task population, to test
whether that exact pattern generalizes.

## 10. Required Sample Size

**Statistically strongest**: to detect a large, practically meaningful pass-rate difference (~20-25
percentage points, e.g. 45% vs. 20%) at α=0.05/power=0.80 via a two-proportion z-test: **≈50 tasks per
condition (150 total trials)**, stratified evenly across the three difficulty tiers. Smaller, still-real
differences (e.g., 10pp) would require ~290+ tasks per condition — this design is built to detect a
*large* effect reliably, and a null result at n=50/condition should not be read as ruling out a
smaller real one.

## 11. Smallest Useful Pilot

**5 tasks per tier × 2 conditions** (raw model vs. pipeline-framed only, dropping council for the
pilot) **= 15 total scored trials.** Purpose: detect only a stark, qualitative difference — e.g., "the
raw model solves at least half the tasks the pipeline-framed condition fails on entirely." This is
explicitly a go/no-go signal for whether the full-power design is worth running, **not** confirmatory
evidence for H1, per the mission's own explicit instruction not to confuse a pilot with confirmation.

## 12. Confounds

Live-server resource contention (directly encountered in the prior Level-4 experiment; mitigated here
by deliberately avoiding `echo_query()`/`deliberate_and_learn()` for conditions 1-2, though not fully
eliminated); the intentional model-choice asymmetry between conditions 1-2 and 3; task-difficulty
miscalibration (mitigated by seeding Tier 3 from real historical failures, not invented tasks); the
AST-discrepancy check must never leak into the primary pass/fail determination; prompt-framing
differences beyond the pipeline itself (mitigated by holding the underlying task description text
identical across conditions 1-2, varying only the wrapper); and a single-shot-vs-retry asymmetry
(resolved by explicitly **excluding** self-edit's own within-cycle retry mechanism from condition 2,
isolating pure gating/framing friction from retry-driven improvement as a separate, disclosed
decision).

## 13. Expected Outcomes and Interpretation

| Result | Supports | Weakens | Interpretation |
|---|---|---|---|
| Raw model pass rate low across all tiers, including Tier 1 | H4, H2 | H1 | The local model pool cannot reliably produce correct code even in a clean, unconfounded, single-shot context — no connectivity fix repairs this; the ceiling is the model. |
| Raw model pass rate high/reasonable, pipeline-framed pass rate much lower on the SAME tasks | H1 | H4, H2 | The pipeline's own framing/gating is actively destroying real, demonstrated capability — a concrete, fixable architecture problem. |
| Raw and pipeline-framed similar (both moderate/low), council-deliberated notably higher | H1 (different form) | H2 (for this domain) | Orchestration/integration of MORE existing capability unlocks real gains beyond any single component — route self-edit through council, don't just fix the current single-model pipeline. |
| All three conditions similar, no tier-dependent stratification | H2 | H1 | Neither cleaning the pipeline nor adding integration changes the outcome — consistent with an already-reached ceiling. |
| A specific historical self-edit/`echo_projects` failure task is cleanly solved by the raw model | H1 | H4 (for that case) | Direct, concrete falsification of "the model can't do this" for that specific historical failure. |
| A meaningful proportion of candidates show an AST-score/real-execution discrepancy | H3 | — | The existing fitness metric is missing real information a better instrument reveals — directly explains why the saturated gate coexists with noisy real outcomes. |

## 14. What Would Falsify Each Hypothesis

- **H1 is falsified** (or at least not supported) if raw, pipeline, and council conditions all
  perform similarly, with no meaningful tier-dependent pattern — nothing about how components are
  connected or not connected would matter.
- **H2 is falsified** if removing pipeline friction (condition 1 vs. 2) or adding orchestration
  (condition 3 vs. 1) produces a large, tier-independent improvement — there would be real,
  unrealized headroom the current architecture isn't extracting.
- **H3 is falsified** (for this specific instrument) if the AST score and real-execution verdict
  agree on every candidate — the existing metric would be shown to already capture what matters here,
  at least for this task population.
- **H4 is falsified** if the raw model reliably solves Tier 3 (hard, historical-failure-seeded) tasks
  — direct proof the model was never the actual limiting factor for those specific real failures.

## 15. Exact Infrastructure/Code Required

`river_deliberation._ollama_query()` (condition 1) · `self_edit_manager.scan_for_unsafe_operations()`
(condition 2's F1 step) · `sandbox.run_script.run_sandbox_script_isolated()` (shared execution
primitive for both condition 2's F2-equivalent step and the primary pass/fail check across all
conditions) · `code_verification.verify_in_sandbox()`/`verify_response_code()` (reused directly) ·
`river_deliberation.deliberate_and_learn()` (condition 3) ·
`echo_model_orchestrator.rank_models("coding")` (fixed model selection for conditions 1-2) ·
`echo_quality_scorer._score_response_quality()` (secondary H3 check only). **The only genuinely new
artifact required is the 15-task benchmark definition file itself** — everything else reuses existing,
already-verified functions.

## 16. What NOT to Change Before Running It

Do not modify `self_edit_manager.py`'s F1/F2 gates, the fitness gate, or any safety boundary —
condition 2 exists specifically to test the *current* pipeline as-is. Do not modify the
shadow/empirical arbitration logic — orthogonal to this experiment; conflating the two reintroduces a
confound this design is built to avoid. Do not modify `echo_quality_scorer.py` — it is a disclosed
secondary comparison point here, and changing it would break comparability with all prior retrospective
analysis that depends on its current behavior. Do not route conditions 1-2 through
`echo_query()`/`deliberate_and_learn()` — doing so would contaminate real production
`model_task_stats` with benchmark traffic, the exact class of contamination this project's own history
has repeatedly had to find and fix after the fact. Do not run this alongside heavy live-server
activity without accounting for the resource-contention confound directly encountered in the prior
Level-4 experiment. Do not stack the benchmark with only easy tasks — Tier 3's real historical-failure
seeding is essential; an easy-only benchmark would manufacture a false H2 result.

---

**This experiment is designed so that failure is informative, not merely disappointing**: if raw
model performance turns out to be just as poor as the pipeline's, that is a real, valuable, ceiling-
confirming result (H2/H4) — not a wasted investigation. If it turns out meaningfully better, that is a
concrete, actionable, falsifiable finding pointing at exactly which architectural friction to fix next
(H1). Either result advances understanding of what Echo actually is, which is the only goal this
mission set.
