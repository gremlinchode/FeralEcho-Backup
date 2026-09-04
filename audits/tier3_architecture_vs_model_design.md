# FeralEcho: Tier 3 Experimental Design — Architecture Capability vs. Model Capability

Design only. Nothing was implemented, fine-tuned, or modified. Full structured detail is in
`audits/tier3_architecture_vs_model_design.json`.

## 1. Executive Conclusion

**The RAW/PIPELINE/COUNCIL pilot cannot answer the central question, and was never designed to.** It
measured whether three existing pathways produce different outcomes — real, useful, but confounded by
unequal inference budgets (COUNCIL spends ~4x RAW's compute) and uncontrolled model selection
(`choose_model()` varies live, within a single run, across conditions). **The single highest-value next
experiment is a 4-arm, budget-matched, held-out design**: `BASE_1` (single model, single attempt),
`BASE_N_selfconsistency` (same model, N attempts, self-selected — same total compute as council, with
model *diversity* specifically removed), `ARCH_PIPELINE` (self-edit's real generation, single-call
budget, isolating prompt framing), and `ARCH_COUNCIL` (the real council, same N+1 budget as
`BASE_N`). This isolates exactly two things the current evidence cannot separate: whether an
architecture advantage is genuine structure (H1) or just more compute (H4), and whether self-edit's own
prompt framing contributes anything at equal budget (Level A). Evaluated on a frozen, genuinely
held-out task set, not the tasks the mechanisms were built or reused against.

## 2. Current Evidence Matrix

Full table in the JSON's `evidence_matrix` (10 rows). Highlights: the self-edit targeting loop, the
council-rating cursor bug, ToolManager, `echo_projects`' 0/61, C1, preference formation, and memory
retrieval are all **real, well-characterized findings that do not bear on Tier 3's question at all** —
each is orthogonal (routing, training-signal, tool-invocation, multi-file generation, persistent-state,
preference, or memory-retrieval questions, not single-function code-generation capability under a
controlled budget). The two findings that DO bear directly: the RAW/PIPELINE/COUNCIL pilot itself
(22/45, `task_03`/`task_06` showing opposite directions, never budget-matched) and the two measurement
bugs found and fixed/disclosed mid-pilot (real, precisely diagnosed, now narrowing but not closing H3).

## 3. Remaining Uncertainties

Listed in full in the JSON. The two load-bearing ones: **(a)** whether any PIPELINE/COUNCIL advantage
reflects real architectural structure or just more compute — never tested with budget held constant;
**(b)** whether an advantage, if real, survives on tasks never used to build or tune the mechanism —
never tested at all, since the original pilot's 15 tasks are not split into development/held-out sets.

## 4. Formal Hypotheses

- **H1 — Architecture/integration contribution**: a reproducible performance advantage over an
  appropriately matched baseline, at *equal inference budget*.
- **H2 — Model ceiling**: the architecture cannot reliably overcome the model's limitations even given
  equal or greater budget.
- **H3 — Measurement limitation**: existing evaluators fail to capture meaningful differences.
- **H4 — Orchestration/sampling advantage**: FeralEcho helps mainly via more attempts/diversity/
  selection, not new capability per se — a real, useful, but *scientifically different* claim from H1.
- **H5 — Infrastructure ceiling**: the M5/Ollama operating envelope prevents valid evaluation before
  the substantive comparison can even complete.

## 5. Definition of Architectural Contribution

Seven levels, deliberately not collapsed into one category (full detail in JSON):

- **A — Prompt advantage**: a better prompt/context than a bare task description.
- **B — Sampling advantage**: multiple attempts, best selected.
- **C — Verification advantage**: errors detected/corrected. **A falsifiable prediction, stated now,
  before running anything**: F1 (self-edit's real verification step in PIPELINE) is a *safety* scanner,
  not a correctness verifier — it should contribute ~zero to correctness, since it cannot catch a logic
  bug like the ones already directly observed (`candidate_005`'s swapped dict lookup,
  `candidate_007`'s LRU ordering bug). Tier 3 can directly test whether this prediction holds.
- **D — Decomposition advantage**: a hard task broken into tractable subtasks. **Not exercised by any
  of the three existing pilot conditions** for single-function tasks — council's synthesis is
  aggregation, not decomposition, and conflating the two would be a real category error.
- **E — Memory/retrieval advantage**: information unavailable to the base model. **Confirmed not
  applicable to this domain** — self-edit's code generation does not call memory retrieval at all.
- **F — Persistent behavioral adaptation**: behavior changes across sessions. Not exercised by any
  pilot condition; C1 is the only mechanism demonstrating this, and it is orthogonal here.
- **G — Generalized capability improvement**: better performance on genuinely unseen tasks, without
  task-specific engineering. **The level Tier 3's held-out methodology exists specifically to test** —
  the strongest, least-demonstrated claim of the seven, and the one a positive Tier 3 result should be
  read against most skeptically.

## 6. Definition of Model Capability

For this design: **model capability** is what a single, unaided instance of a given model produces on a
task at a *fixed, pre-declared inference budget* (one call, or — for the budget-matched comparison — N
calls with self-consistency selection but no architectural diversity or verification). This definition
is deliberately budget-relative, not absolute — "the model's capability" at N=1 and at N=4 (with
self-selection) are two different, both-legitimate baselines, and Tier 3's whole design exists to keep
architecture from being compared against the wrong one of the two.

## 7. Candidate Tier 3 Experiments

Four considered, ranked in §18. Full detail in JSON's `ranked_candidate_designs`.

## 8. Control Analysis

A bare "ask the model once" baseline (the original pilot's RAW) is **not a fair control for COUNCIL**,
since council's real budget is ~4x larger. The matched controls:

- **`BASE_1`**: single model, single attempt, temp=0 — the floor, identical to the original RAW.
- **`BASE_N_selfconsistency`**: the *same* single model, N independent attempts at temp>0 (real
  diversity across attempts, not across models), then a synthesis call using the *same* model to
  reconcile/pick the best answer among its own attempts. Total calls = N+1, matching council's real
  budget exactly, with model diversity specifically subtracted out as the one remaining variable.
- **`ARCH_PIPELINE`**: the real `generate_code_from_plan()` + F1, one generation call — compared
  directly against `BASE_1` (same single-call budget) to isolate prompt framing (Level A) cleanly,
  since PIPELINE's budget is *not* larger than `BASE_1`'s.
- **`ARCH_COUNCIL`**: the real `deliberate_and_learn()`, N different models + synthesis, same N+1
  budget as `BASE_N`.

Variables held constant per comparison (full table in JSON): for the H1-vs-H4 test
(`ARCH_COUNCIL` vs. `BASE_N`), total call count, per-call temperature policy, task text, and scoring
method are all held fixed — only model *diversity* varies. For the Level-A isolation
(`ARCH_PIPELINE` vs. `BASE_1`), model identity (pinned, not re-selected per candidate) and single-call
budget are held fixed — only prompt framing varies.

## 9. Capability-Target Analysis

**Coding remains the best domain**, narrowed specifically to Tier-3-style hard tasks. Objective
evaluation and zero infrastructure burden are already proven across 22 real candidates. Tier 1/2 tasks
already tested show near-ceiling performance (14/19 passed) — too easy to discriminate a rescue effect.
Switching domains would require new evaluator infrastructure from scratch for no demonstrated benefit
over reusing what already works. Against the mission's own eight target criteria: objective evaluation
✓ (reused), reproducible scoring ✓ (reused, spot-check added), meaningful base-model failure rate ✓
(Tier 3 tasks specifically seeded from real historical failures), realistic possibility of
architectural assistance ✓ (untested but plausible), low evaluator ambiguity ✓ (two known gaps now
fixed/disclosed), low infrastructure burden ✓ (reuses proven tooling), no paid services ✓, no
production mutation ✓ (isolation layer already proven).

## 10. Proposed Ablations

**Four arms, not the full suggested list** (`BASE_1`, `BASE_N_selfconsistency`, `ARCH_PIPELINE`,
`ARCH_COUNCIL`). Explicitly excluded, with reasons: memory/retrieval and reflection ablations — both
confirmed, by direct source read, to be outside self-edit's code-generation causal path entirely (an
ablation of a mechanism that was never in play provides zero information). Council-composition
ablations (drop one councillor) — a real, lower-priority question, deferred to keep this a *minimum*
causal experiment rather than a benchmark, per the mission's own explicit instruction.

## 11. Infrastructure-Control Plan

No pausing or signaling of the live `run.py` process — not authorized, consistent with this
investigation's own prior, disclosed decision. `OLLAMA_NUM_PARALLEL` untouched. All generation
sequential, one real call in flight at a time. Controlled batches with resumability (the pattern
already proven working this investigation). Pre-batch telemetry (`ollama ps`, `vm.swapusage`,
timestamp) recorded before each batch, so Tier 3's own contention level is comparably documented, not
assumed identical to the prior pilot's. **`choose_model()`'s live variability is pinned** for the
`BASE`/`PIPELINE` arms — read once at batch start, held fixed, passed explicitly rather than
re-invoked per candidate — a disclosed, deliberate deviation from the original pilot specifically to
remove a confound Tier 3's stricter causal question cannot tolerate. Thermal effects not independently
measurable with available tooling; not treated as a dedicated control given no evidence so far they are
live.

## 12. Evaluator-Validation Plan

`code_verification.verify_in_sandbox()` and the corrected `clean_code()` (self-edit's real helpers plus
the disclosed last-fenced-block fallback) are reused unmodified — both already proven across 22 real
candidates. **A new, third failure class is added**: `GENERATION_TRUNCATED` (a candidate whose only
code-shaped text sits inside an unclosed fence) — closing the exact gap disclosed in the prior report's
§C.2, where a truncated response and a genuine logic failure both currently read as the same
`TASK_LOGIC_FAILURE` label. A random 20% sample of PASS/FAIL verdicts is manually re-read against the
raw candidate text before the study's final report is written — a direct, concrete answer to H3's own
standing concern, not a one-time fix mistaken for a permanent guarantee.

## 13. Blind/Held-Out Methodology

**Development set**: 2 tasks, reused from the existing frozen suite's own Tier 3 (`task_11`, `task_12`)
— used only to confirm each arm produces a sane, non-degenerate result, never to tune any arm's
prompts or parameters. **Held-out set**: 8 genuinely new tasks, written for this study specifically,
never present in the original 15-task suite, spanning the same category spread the original Tier 3
design intended (bug-fixing, concurrency/stateful reasoning, algorithmic edge cases, refactoring) —
frozen and hashed *before* any arm touches them, exactly mirroring the original suite's own freeze
discipline. **The held-out set's result is the study's real verdict; the development set is a sanity
check only.** This directly implements the mission's own Sixth/Seventh Task requirement: if the four
arms were implicitly tuned while watching development-task scores, any resulting advantage could be
development-set-specific optimization (not Level G) rather than genuine generalized capability.

## 14. Statistical Plan

**Paired design**: each held-out task is attempted by all 4 arms, enabling McNemar's test (paired
binary outcomes) rather than the prior pilot's unpaired two-proportion approach — a real, meaningful
power improvement at small N. Primary endpoint: binary PASS/FAIL on the held-out set only. Secondary:
generation/wall-clock time per arm, failure-class distribution, development-set pass rate (sanity only).
Effect size of interest: a large, pre-specified 25-30 percentage-point difference (consistent with this
investigation's own prior power calculations, which already showed smaller effects require infeasibly
large N given this system's real throughput). Repeated attempts within `BASE_N` are not separately
analyzed — only the arm's final, self-selected answer counts as one observation. Infrastructure
failures excluded from the primary denominator, reported separately. Evaluator-flagged corrections
disclosed, not silently applied. **Stopping rule, pre-registered**: run the full pilot once, analyze,
stop — no added held-out tasks or re-runs after seeing results, no endpoint redefinition after the
fact, directly guarding against the p-hacking risk the mission names explicitly.

## 15. Power/Sample-Size Reasoning

**Pilot**: 8 held-out tasks × 4 arms = 32 trials — real, executable within this machine's demonstrated
throughput (mean ≈85s/candidate observed in the prior pilot; 32 trials ≈ 45 minutes of real, sequential
generation time, before any contention-driven slowdown). **Confirmatory**: detecting a 25pp paired
difference at α=0.05/power=0.80 requires approximately 25-30 held-out tasks per arm-pair comparison — a
real improvement over the ~50-70/arm the prior *unpaired* pilot design required for a comparable
effect, but still a substantial undertaking, stated as an estimate to refine once real pilot-stage
variance is observed, not treated as exact in advance.

## 16. Fine-Tuning Timing Analysis

**Fine-tuning should occur AFTER Tier 3** — independently derived, not merely accepted because it is
the mission's own stated default. Fine-tuning before Tier 3 changes the very quantity ("the underlying
model's capability") the experiment holds fixed while varying architecture — running Tier 3 post-tuning
would measure a different model than all 22+ RAW/PIPELINE/COUNCIL candidates already characterized,
breaking comparability. If tuning raises the base ceiling on tasks where PIPELINE/COUNCIL previously
showed an advantage, that advantage could vanish for a confounded reason (the model no longer needs the
help) misread as "architecture doesn't matter." If tuning uses Echo's own generated interactions, it
risks baking in exactly the errors this investigation has spent its effort finding (the LRU bug, the
flatten-one-level failures) before they are even fully characterized. Tuning could also amplify a real
architecture effect — a genuine possible benefit, but one a future decision should be made about *after*
understanding the current baseline's real gaps, not before.

## 17. Threats to Validity

Live-server contention (unresolved, same as before — batches and telemetry mitigate, do not eliminate
it). `choose_model()`'s pinning for `BASE`/`PIPELINE` arms is itself a disclosed deviation from
"test the system exactly as it naturally operates" — a deliberate trade of ecological validity for
causal clarity, stated plainly. The development/held-out split relies on the 2 development tasks
genuinely not influencing the held-out design — a human/investigator discipline, not an enforced
technical control. `BASE_N_selfconsistency`'s synthesis step, while budget-matched to council, is a
novel construction (self-edit/council don't have an exact analogue) and its own behavior should be
sanity-checked on the development set before being trusted as a fair control.

## 18. Ranked Experiment Candidates

| Rank | Design | Causal clarity | H1/H2/H4 separation | H3/H5 detection | Generalization | Effort |
|---|---|---|---|---|---|---|
| **1** | **4-arm budget-matched, held-out** | high | high | medium-high / medium | high (held-out is the verdict) | low-medium |
| 2 | PIPELINE-vs-BASE-1 only | high | none (doesn't test diversity-vs-compute) | medium | low | low |
| 3 | Full ablation grid | medium | high in principle | medium | medium | high, low marginal value (3/4 ablations target mechanisms outside the causal path) |
| 4 | Cross-domain (non-coding) | unknown (new infra) | unknown | unknown | potentially high | highest |

## 19. Selected Single Best Experiment

**The 4-arm budget-matched design on a frozen, held-out hard-task set** (§8, §13), evaluated via paired
McNemar's testing (§14) at a pre-specified 25-30pp effect size, with `choose_model()` pinned for the
`BASE`/`PIPELINE` arms and a new `GENERATION_TRUNCATED` failure class closing the one remaining
disclosed evaluator gap.

## 20. Exact Protocol

1. Write and freeze 8 new held-out tasks (spanning bug-fixing, concurrency/stateful reasoning,
   algorithmic edge cases, refactoring); hash the frozen set before any generation.
2. Pin one model for `BASE_1`/`BASE_N`/`ARCH_PIPELINE` via a single `choose_model()` call at batch
   start; record it.
3. Run all 4 arms on the 2 development tasks first; confirm each produces a sane, non-degenerate
   result (a real, working `BASE_N` synthesis step in particular) before touching the held-out set.
4. Run all 4 arms on the 8 held-out tasks, sequentially, in controlled batches, with pre-batch
   telemetry recorded each time.
5. Score every candidate via the reused `verify_in_sandbox()` + the new truncation check; tag
   `INFRASTRUCTURE_FAILURE`/`GENERATION_TRUNCATED`/`TASK_LOGIC_FAILURE` per the pre-declared rules.
6. Independently spot-check 20% of verdicts against raw text before analysis.
7. Unblind, compute the paired comparisons (`ARCH_COUNCIL` vs. `BASE_N`; `ARCH_PIPELINE` vs.
   `BASE_1`), apply the pre-registered stopping rule, and report — once.

## 21. Pre-Registered Interpretation Rules

Stated in full in §14/§15/JSON's `go_no_go_criteria`. In brief: a ≥25pp paired advantage for
`ARCH_COUNCIL` over `BASE_N`, directionally consistent on the development set, is read as real support
for H1 over H4. Statistical indistinguishability (or a `BASE_N` win) is read as support for H4 over H1.
A ≥25pp `ARCH_PIPELINE` advantage over `BASE_1` at equal single-call budget is read as real Level-A
prompt-framing contribution. Anything smaller than the pre-specified effect size at pilot scale is
**AMBIGUOUS**, not a forced conclusion in either direction — triggering the confirmatory sample size,
not a rewritten endpoint.

## 22. GO / NO-GO Criteria

- **GO on H1**: `ARCH_COUNCIL` beats `BASE_N` by ≥25pp on held-out, consistent in direction on
  development.
- **Supports H4 (a real, valid, non-failure outcome)**: `ARCH_COUNCIL` ≈ `BASE_N` or `BASE_N` wins.
- **GO on Level A**: `ARCH_PIPELINE` beats `BASE_1` by a large margin at equal budget.
- **AMBIGUOUS**: pilot-scale n insufficient to resolve at the pre-specified effect size — the likely,
  honest outcome at n=8/arm given this investigation's own repeated experience, and itself a valid
  trigger for the confirmatory sample size, not a failure.
- **H5 flag, overriding everything else**: if `INFRASTRUCTURE_FAILURE`-classified trials exceed 15% of
  attempted trials, the result is reported as inconclusive-pending-infrastructure regardless of the
  pass-rate numbers — the hardest-won, most repeated lesson of this entire investigation, applied here
  explicitly rather than re-learned.

---

## Final Question, Answered Plainly

**If we had only enough time and compute for ONE more serious experiment before touching Echo's
architecture or fine-tuning any model, we should run the 4-arm budget-matched design on 8 frozen,
genuinely held-out hard coding tasks — `BASE_1`, `BASE_N`-self-consistency, `ARCH_PIPELINE`, and
`ARCH_COUNCIL` — scored only by real sandboxed execution, with the model pinned for the non-council
arms and the council's real N+1 call budget matched exactly by `BASE_N`'s own attempt-plus-synthesis
structure.**

**What would convince me the bottleneck is the model, not the architecture**: `BASE_N`
(same model, same total compute, no architectural diversity) performing statistically
indistinguishably from `ARCH_COUNCIL` on the held-out set — direct, budget-controlled proof that
whatever COUNCIL's real advantage over a single naive call has been (and this investigation's own
partial pilot data is genuinely mixed on whether there even is one), it is fully explained by *spending
more compute*, not by anything architecturally specific to model diversity, verification, or
orchestration. Paired with `ARCH_PIPELINE` failing to beat `BASE_1` at equal single-call budget — direct
evidence self-edit's own prompt framing adds nothing measurable either — that combination would be a
real, specific, model-ceiling verdict, not a vague shrug. Conversely, `ARCH_COUNCIL` beating a
genuinely budget-matched `BASE_N` by a large, held-out-replicated margin would be the first piece of
evidence in this entire investigation that architecture does something a single model, given equal
resources, cannot do for itself — and that is the bar this design is built to hold it to, not a lower
one dressed up to look like it.
