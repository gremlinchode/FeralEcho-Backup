# FeralEcho: Tier 3 Design — Adversarial Preflight Audit

No code was written, executed, fine-tuned, or modified to produce this audit. The live production
process was not touched. `OLLAMA_NUM_PARALLEL` was not touched. This document tries to break the Tier
3 design, not defend it. Full structured detail is in `audits/tier3_design_preflight.json`.

**Bottom line up front, because it matters more than anything else in this document**: the Tier 3
design document describes an experiment that, as currently specified, **cannot yet be built as
described**. Three of its claimed equivalences are either factually wrong (verified directly against
running code) or entirely unimplemented. This is not a matter of theoretical rigor — one of the three
is a real, mechanically-guaranteed confound that would produce a false positive for the architecture
hypothesis on its own, with no further intervention needed.

## 1. Audit the Four Arms at the Implementation Level

Three of the four arms map onto real, already-executed code and were verified directly against it,
not inferred from the design document. The fourth does not exist.

- **`BASE_1`**: real, verified. One call, `river_deliberation._ollama_query()`, temperature 0.0, no
  system prompt, bare task text, 8192 context, **`max_tokens` never passed → silently defaults to
  1024** (confirmed by tracing `stream_query_ollama()`'s own default). Zero production side effects by
  construction.
- **`BASE_N_selfconsistency`**: **does not exist.** No function, no prompt, no call sequence anywhere
  in the codebase implements "N attempts + same-model synthesis." Every claim about its behavior in the
  design document is currently prose, not verifiable code (§1's own instruction — "do not infer merely
  from the design document if source inspection can establish them" — cannot be honored for this arm,
  because there is no source to inspect).
- **`ARCH_PIPELINE`**: real, verified. One call to `generate_code_from_plan()` → internally one
  `echo_query()` call, temperature 0.0 (passed through), prompt = `CODE_OUTPUT_RULES` + the full
  current contents of `self_edit_generated.py` + the task text as "the plan," **`max_tokens=2048`
  explicit**, via `_TASK_TOKEN_LIMITS['coding']`. F1 (`scan_for_unsafe_operations`) runs after
  generation but — confirmed directly from this harness's own code — **never gates, rejects, or
  triggers regeneration; the candidate proceeds to scoring regardless of F1's verdict.** Zero retries
  in this harness (self-edit's real intrinsic retry lives one level up, in `execute_self_edit()`,
  never invoked here). Production writes neutralized via monkeypatch, empirically verified across 22
  real candidates.
- **`ARCH_COUNCIL`**: real, verified. `DEFAULT_COUNCIL_SIZE=3` councillors + 1 synthesis = 4 real
  calls, via `deliberate_and_learn()`. Model selection via the real `_select_council()` (reads the
  real, proxied RiverBrain, applies `ECHO_SCORE_BOOST`/`TAG_SCORE_BOOST`). **Per-councillor temperature
  is jittered** (real production behavior), not fixed. **`max_tokens` never passed by this harness →
  defaults to 1024 for both councillor and synthesis calls** — the same silent default `BASE_1` gets,
  confirmed by tracing `deliberate_and_learn()`'s own `max_tokens=None` default through to
  `_ollama_query()`. Synthesis uses the real `SYNTHESIS_SYSTEM_TEMPLATE`, which explicitly frames its
  input as "the council has offered the following perspectives" and labels each entry with the real
  model's short name (`[1. Echo]`, `[2. Qwen2]`, ...) — confirmed by direct read of `_format_opinions()`.

## 2. The BASE_N Problem — Attacked

**A-J, answered directly**: BASE_N does not currently receive *any* defined quantity of information at
synthesis time, because it doesn't exist (A). Its synthesis prompt's structural power is undefined (B).
Its selection capability is undefined (C). Council provides real per-model identity labels and a
sophisticated, tension-preserving synthesis instruction set BASE_N's design never addressed matching or
deliberately not matching (D). Whether BASE_N's synthesis model can inspect all N attempts depends on
implementation choices not yet made (E). Token budgets are not just unequal between the concept of
BASE_N and council — council's own REAL synthesis token budget is itself silently wrong (1024, not the
intended 2048), so there is currently no correct target to even match (F). Context windows are nominally
equal (8192) but this has not been verified for a not-yet-built arm (G). Truncation handling is
undefined for BASE_N (H). **Council performs no intermediate critique/voting/ranking before synthesis**
— its "structure" is entirely in `_select_council()`'s model-selection logic and the synthesis
instruction text, not a multi-round deliberation (I) — this is worth stating precisely, since it means
BASE_N's needed complexity is lower than a naive reading might assume. Whether "self-consistency" is
computationally equivalent to "candidate generation + synthesis" depends entirely on whether BASE_N's
synthesis reuses or diverges from the real template (J) — currently undefined either way.

**The crucial question, answered precisely**: if `ARCH_COUNCIL` beats `BASE_N` *as currently
underspecified*, we could legitimately conclude nothing — the comparison isn't yet a comparison of
anything specific. Even once `BASE_N` is built per this audit's minimum repairs, the legitimate
conclusion is bounded: **council's real, *combined* package (model diversity + real selection ranking +
real synthesis structure) beats a budget-matched single model** — not "model diversity specifically,"
not "architecture specifically" in any decomposed sense. See §3 for why.

## 3. Is Model Diversity Actually Isolated? No.

**Stated plainly, as instructed**: the four-arm design, even fully repaired, **cannot distinguish
heterogeneous-models-helping from council's-specific-orchestration-structure-helping.** `BASE_N` is
homogeneous; `ARCH_COUNCIL` is both heterogeneous *and* structured (real ranking, real synthesis
instructions) — two co-occurring differences, one comparison. The minimum additional control that
*would* separate them: a fifth arm, `DIVERSE_N` — N different models (the same real
`_select_council()` pool/pick), combined via the *same* minimal, non-oracle rule as `BASE_N` (not
council's real structured synthesis). `DIVERSE_N` vs. `BASE_N` would isolate diversity; `ARCH_COUNCIL`
vs. `DIVERSE_N` would isolate structure. **Not recommended for addition now**, per the mission's own
explicit instruction to check whether the existing four arms suffice first: they do, at a narrower,
explicitly-bounded scope (§14's "final claim boundary"), and that narrower scope should be stated in
any Tier 3 report rather than silently expanded into a stronger claim than the data supports.

## 4. The Synthesis Control — Audited, Found Wanting

Per-item classification (full table in JSON): candidate count is an **ACCEPTABLE_DESIGN_CHOICE**
(matched by definition once `BASE_N` exists). Metadata/model-identity labels are an
**UNCONTROLLED_CONFOUND** until repaired — council's real template names real models; `BASE_N`'s design
never specified whether it would. The synthesis prompt *text* is a **FATAL_CONFOUND**: reusing the real
`SYNTHESIS_SYSTEM_TEMPLATE` verbatim for `BASE_N` would be literally false ("the council has offered...
perspectives" when there is no council) and its explicit instruction to "identify the sharpest point of
tension" could cause a same-model self-consistency check to manufacture spurious disagreement among
near-identical outputs, degrading `BASE_N`'s own true ceiling — inflating any apparent `ARCH_COUNCIL`
advantage for a reason having nothing to do with real diversity. Writing an entirely new prompt instead
introduces a different, equally uncontrolled confound (the synthesis *mechanism* itself would no longer
be held constant). Token budget is a **FATAL_CONFOUND**, and not only for the not-yet-built arm — it is
already wrong for the real, already-executed `ARCH_COUNCIL` condition (1024, not the intended
production-realistic 2048). **The minimum repair that resolves this without inventing a new mechanism**:
a minimally-edited version of the real template — "you previously produced the following independent
attempts" instead of "the council has offered... perspectives," anonymized `[Attempt N]` labels instead
of real model names — applied *identically* to both arms, so the only thing that differs is whether the
underlying attempts actually came from different models, not whether the prompt admits it.

## 5. `ARCH_PIPELINE` vs. `BASE_1` — Audited

**Yes, `ARCH_PIPELINE` sees additional information**: the full current contents of `self_edit_generated.py`
plus `CODE_OUTPUT_RULES`, ahead of the identical task text. This is the intended manipulated variable,
not an accidental leak. **The "plan" is the task text itself**, passed as a literal string — no separate
plan-generation call occurs, confirmed directly from `generate_code_from_plan()`'s own signature
(`plan: str`, not something it derives). **F1 does not alter, gate, reject, or trigger regeneration**
for the candidate in this harness — confirmed directly, this is the same finding as §1/§6. **The
claimed "one generation call" is confirmed to be exactly one real inference call.** **The pipeline's
framing is prompt framing (Level A), not decomposition (Level D)** — no subtask breakdown occurs.

**If `ARCH_PIPELINE` wins `BASE_1`**: proves Level-A framing helps — *but only once the token-budget
asymmetry (§1, §7) is fixed.* As currently unfixed, a win proves nothing beyond "2048 tokens beats
1024 tokens," which is not an interesting or contested claim. **If `ARCH_PIPELINE` loses `BASE_1`
despite its current, unfixed 2x token advantage**, that would actually be the more informative of the
two possible *unfixed*-state outcomes — a real, if accidental, stress test showing framing can hurt
even with more room to use it.

## 6. The F1 Prediction — Attacked

**Detectable by F1**: unconditionally-blocked dangerous calls (`exec`/`eval`/`os.system`/`subprocess`/
`shutil` writes/`Path.write_text`), forbidden-path `open()` calls, self-edit escalation calls, and
`SyntaxError` (the code fails to parse at all). **Undetectable by F1, by construction**: any wrong
comparison operator, off-by-one error, swapped lookup direction, or incorrect algorithm not involving a
blocked call — i.e., every real logic bug this investigation has actually observed
(`candidate_005`'s swapped dict lookup, `candidate_007`'s LRU ordering bug). **F1 cannot change
generation behavior, cannot trigger regeneration, cannot reject a candidate in this harness, cannot
influence later candidates, and cannot affect final scoring in this harness** — all four confirmed by
direct source read, not inferred.

**Is "approximately zero contribution to correctness" genuinely falsifiable, or merely intuitive?**
**Neither, precisely — it is *structurally, trivially true* given the current wiring, not a genuine
empirical prediction Tier 3 could falsify.** F1's verdict is recorded but never consulted by the scoring
path. No observed result from running Tier 3 could ever contradict this claim, because the code
guarantees it by construction. This should be stated as a fact established by code inspection, not
presented as something the experiment "discovers" — doing the latter would be quietly overselling
what Tier 3 actually tests.

## 7. Budget Matching — Audited

**Calls matched**: yes, by design, between `BASE_N`/`ARCH_COUNCIL` (N+1 each) once `BASE_N` exists;
`BASE_1`/`ARCH_PIPELINE` at 1 each. **Tokens NOT matched — a real, confirmed asymmetry, not a
hypothetical one**: `ARCH_PIPELINE` gets 2048; every other arm, as actually coded (or, for `BASE_N`,
as it would silently inherit if built the way the other arms were), defaults to 1024. **Prompt content
is intentionally unmatched** for the Level-A test (`ARCH_PIPELINE`'s file-context is the manipulated
variable) but *should* be matched for the diversity-vs-compute test (`BASE_N` vs. `ARCH_COUNCIL` — both
should receive the bare task text). **Model parameter count is intentionally unmatched** — council
draws from a 9-model, 3B-8B pool; the pinned arms use one model — a disclosed asymmetry appropriate to
the diversity question, not an oversight, but one that should be *stated*, not silently assumed
"equal." **Wall-clock is correctly NOT used as the budget definition** — it is itself confounded by
real, independently-demonstrated infrastructure contention (swap, model residency, live production
loops), and using it would conflate "the machine was busy" with "the arm needed more compute."
**Recommended operational definition of "equal inference budget": equal call count AND equal
`max_tokens` per call, held identical across arms wherever the comparison isn't specifically testing
prompt content or model diversity.**

## 8. Model Pinning — Audited

**"Pinned once per batch" is insufficient.** This investigation's own executed pilot needed multiple
separate, controlled batch invocations across real, separate script runs — a fresh `choose_model()`
call at the start of every future batch could silently select a *different* model between batches,
reintroducing exactly the confound pinning was meant to remove. Ollama itself was not observed silently
substituting a model mid-session in any of this investigation's real data; the risk is at the
`choose_model()` call boundary, not inside Ollama. **A second, distinct gap**: pinning the *harness's
own* model choice does not pin `generate_code_from_plan()`'s **internal, separate** `choose_model()`
call — `ARCH_PIPELINE`'s real model selection is not automatically the same as `BASE_1`/`BASE_N`'s
pinned choice unless this internal call is also intercepted. Model identity is **not currently
sufficiently controlled for causal inference** across a multi-batch study without both fixes.

## 9. Task Design and Holdout Integrity — Audited

The held-out set is genuinely independent of *mechanism tuning* — no arm's code or prompt has been, or
would be, adjusted based on any task-level result. It is **not** independent of the investigator's own
accumulated knowledge of which general failure categories (bug-fixing, concurrency, algorithmic edge
cases) tend to be hard for these models — an honest, real, but *different and weaker* threat than the
mission's original concern, since it does not involve tuning any mechanism against the tasks. This is
classified as **ACCEPTABLE**, stated plainly rather than glossed over: a genuinely blind third-party
task-writer is an unrealistic standard for a small, resource-constrained investigation, but "held-out"
should be understood in this report to mean "held out from mechanism tuning," not "held out from all
investigator knowledge whatsoever." Task ordering **could matter** (§ below). Candidate IDs are
blinded, proven working in the executed pilot. The evaluator itself was developed and debugged against
the *original* 15-task suite, not the new held-out set — a real, but already cross-validated (22 real
candidates, zero further extraction anomalies since the fix) risk, not a new one introduced by Tier 3.

## 10. Statistics — Audited

McNemar's test is appropriate for this paired design. n=8 can meaningfully distinguish only a large,
pre-specified effect (25-30pp) — correctly scoped as pilot-only. The effect threshold is coherent with
this investigation's own prior power work. Multiplicity (2 comparisons) is real but minor given the
large target effect size. **The sentence "statistical indistinguishability... is read as support for
H4 over H1" is too strong, exactly as flagged for audit.** At n=8, a non-significant result is the
expected outcome under BOTH a true null and an underpowered real effect — these are not distinguishable
from a p-value alone, and the design's own go/no-go criteria currently list both "NO_GO supports H4"
and "AMBIGUOUS" as possible labels for what could be the *same* empirical result, with no rule
specifying which applies. **Repair**: use the observed point estimate alongside the p-value — a small
point-estimate difference with a reasonably tight CI supports H4; a large point-estimate difference with
a wide, zero-crossing CI is AMBIGUOUS, not H4 support. A BASE_N win legitimately and unambiguously
supports H4 (or H2, if both arms are weak in absolute terms). Failure to detect H1 legitimately supports
H2 *only* when paired with a small observed effect size, not merely a non-significant p-value.

## 11. Infrastructure Contamination — Audited

RiverBrain/FAISS/interaction_log/reflection-shard isolation is proven working empirically across 22
real candidates via the recorded side-effect counter — real evidence, not an assumption. This proof
does **not** automatically extend to `BASE_N`'s not-yet-written code; the same isolation layer must be
explicitly reapplied and re-verified for whatever new call path `BASE_N` ends up using, not assumed
inherited by association. Cross-arm write contamination is architecturally prevented by the monkeypatch
design as it stands. **Condition-dependent infrastructure bias is plausible and currently
uncontrolled**: real, rising swap pressure and model-residency churn have been independently measured
across this entire investigation, and a fixed (non-randomized) arm order per task risks systematically
favoring or disfavoring whichever arm happens to run first or last, for reasons having nothing to do
with the arm's own merit. Live production contention (the `model_guided_autonomous_loop` directly
observed competing for the same Ollama queue during the prior pilot) will very likely recur during
Tier 3 and cannot be scheduled around without authorization this audit does not have.

## 12. Order Effects and Randomization — Audited

**Arm order should be randomized independently per held-out task**, not once for the whole study and
not fixed. The prior, executed controlled continuation processed tasks in a fixed `A, then B, then C`
loop order — confirmed directly from the real resumability code — which is exactly the kind of
systematic ordering this section warns about, now identified as a real gap in already-collected data,
not merely a hypothetical future risk. The minimum fix is a one-line change to how the task/arm pair
list is constructed (shuffle per task), not a new mechanism.

## 13. Evaluator Validity — Audited

`PASS`/`TASK_LOGIC_FAILURE`/`INFRASTRUCTURE_FAILURE`/`GENERATION_TRUNCATED` are mutually exclusive and
deterministic **as designed** — but **`GENERATION_TRUNCATED` does not exist in the actual harness code**.
A truncated response (the exact real failure mode already observed in `candidate_019`) currently reads
as an ordinary `TASK_LOGIC_FAILURE`, indistinguishable in the recorded data from a genuine reasoning
error. This means the evaluator, as it stands, **can and does** misclassify an infrastructure/budget
artifact as a model failure — a real, already-demonstrated instance, not a theoretical risk. The
independent 20% spot-check is a reasonable but not airtight safeguard — at n=32 (8 tasks × 4 arms), a
pure random 20% sample could by chance skip an entire arm's worth of candidates; stratifying the
sample (at least 1-2 per arm) closes this cheaply. The evaluator itself is confirmed blind to condition
— `verify_in_sandbox()` receives only code and test text, never a label, by direct source read.

## 14. The Actual Claim Each Result Supports — Decision Matrix

Full 9-row table in the JSON's `result_interpretation_matrix`. The single most important row: **"council
wins" (outcome A/I) legitimately supports only the bounded claim "council's real, combined package beats
a budget-matched single model" — never "architecture" or "model diversity" in isolation**, per §3's own
finding. A win for `ARCH_PIPELINE` over `BASE_1` (outcome D) is **uninterpretable, not merely weaker
evidence**, until the token-budget confound (§1, §7) is fixed — this is stated as a hard gate, not a
caveat to soften. High infrastructure failure (outcome G) or large evaluator disagreement (outcome H)
both legitimately block *any* claim about H1/H2/H3/H4 from the same run's pass-rate numbers, regardless
of what those numbers show — this is the design's own hard override rule, correctly retained.

## 15. Falsification Test (Mandatory)

**Strongest plausible false-positive scenario (architecture does nothing, Tier 3 says it does)**: the
token-budget asymmetry (§1/§7) is left unfixed. `ARCH_PIPELINE` (2048 tokens) beats `BASE_1` (1024
tokens, silently defaulted) on tasks near the truncation boundary — exactly the failure mode already
observed live in `candidate_019` with a different model. The result is reported as "self-edit's prompt
framing helps," when the true, mundane cause is "more tokens avoid truncation." This is not a
hypothetical risk — it is the *default, currently-coded behavior* of every arm as they stand today.
A second, independent false-positive pathway: `BASE_N`'s synthesis, if built by reusing the real
"council of perspectives" template verbatim on same-model attempts, could manufacture spurious
disagreement and degrade its own true ceiling, making `ARCH_COUNCIL` look better by comparison to a
sabotaged baseline rather than a fair one.

**Strongest plausible false-negative scenario (architecture genuinely helps, Tier 3 says model is the
bottleneck)**: architecture's real value concentrates in decomposition/multi-step/multi-file capability
(echo_projects' own domain) — Tier 3, as scoped, tests only single-function tasks, which don't need
decomposition at all. A null result would correctly show "no advantage on this task class" but could be
misreported as "architecture doesn't help," full stop, when the true, narrower finding is "architecture
doesn't help on tasks that don't need the specific thing it's built to provide." A second pathway: an
unpinned or inconsistently-pinned model (§8) drifts between the development and held-out phases of the
same study — a real effect measured on development tasks could fail to replicate on held-out data for a
reason having nothing to do with generalization, and would be misread as evidence against Level G
(generalized capability) when the true cause is "we tested a different model the second time."

## 16. Minimum Repair

Full table with severities in the JSON's `minimum_repairs_summary`. Three **BLOCKER**s (B1 token
budget, B2 BASE_N non-existence, B3 synthesis-prompt equivalence), four **MAJOR**s (M2 model pinning
scope, M3 truncation classification, M4 order randomization, M5 statistical disambiguation), one
favorably-resolved **MAJOR** (M6, F1's prediction is trivially true — relabel, don't re-test), and four
**MINOR/ACCEPTABLE** items requiring no action beyond honest disclosure. None of these require a
redesign — every repair is a small, mechanical, one-to-few-line change to a specification or a call
site, consistent with the mission's own instruction to maximize information while minimizing
engineering and researcher degrees of freedom.

## 17. Final GO/NO-GO

# GO WITH REQUIRED DESIGN AMENDMENTS

1. **The single biggest remaining confound**: the token-budget asymmetry (B1) — `ARCH_PIPELINE`
   already runs at 2x the token budget of every other arm, in already-real, already-executed code, with
   zero prior disclosure. This alone could manufacture a false positive for the architecture hypothesis
   with no further intervention needed.
2. **The single most important repair**: explicitly set `max_tokens=2048` for every call in every arm,
   with no exceptions and no silent defaults. This is a smaller fix than it might sound — a handful of
   call sites, all already identified precisely in §1/§7.
3. **What the experiment can genuinely establish after all seven repairs (B1-B3, M2-M6)**: whether
   council's real, combined mechanism, at a genuinely token-and-call-matched budget, beats a
   same-model self-consistency baseline on frozen, mechanism-untuned held-out coding tasks; and
   separately, whether self-edit's real prompt framing helps at an honestly equal single-call budget.
   Both are real, bounded, legitimately interpretable questions.
4. **What it still cannot establish, even after every repair**: whether model diversity specifically
   (as opposed to council's selection/synthesis structure) is the active ingredient in any observed
   advantage (§3); whether any result generalizes beyond single-function coding tasks to
   decomposition-heavy domains; anything about learning, self-improvement, or emergent capability
   beyond this specific, bounded comparison.
5. **Should Tier 3 execute now?** **No** — not until the three BLOCKERs are closed. `BASE_N` cannot be
   built responsibly without first deciding its exact synthesis prompt and token budget (B2, B3), and
   running `ARCH_PIPELINE`/`ARCH_COUNCIL` again without fixing B1 would simply reproduce and compound
   an already-identified, already-serious confound in the pilot's own data.
6. **Should fine-tuning remain deferred?** **Yes, unchanged from the prior design's own conclusion** —
   nothing found in this audit weakens that reasoning; if anything, the newly-confirmed token-budget
   bug strengthens it, since fine-tuning on top of a currently-miscalibrated baseline would make an
   already-confounded comparison even harder to later disentangle.
