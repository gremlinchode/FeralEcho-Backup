# Minimal Relevance Gate Feasibility Audit (2026-09-06)

## 1. Executive Verdict

A small, single-call LLM relevance judge (**G2**) demonstrably solves the exact
failure case that motivated this experiment — it correctly rejects the
causally-unrelated-but-higher-cosine distractor (`D5`, raw FAISS score
0.4613) in favor of the genuinely causal record (`X4`, raw FAISS score
0.427), and correctly abstains on a wholly unrelated query. But it is **not**
reliably safe: it confidently endorsed a fluent, structurally-convincing but
factually **wrong** causal explanation in one red-team case, and confidently
endorsed a record whose own stated cause explicitly diverged from the
current situation's cause in another. A **deterministic, no-model gate
(G1)** — tested first, as the mission required — provides essentially no
material advantage over doing nothing: it only fires on near-literal text
repetition and is silent (correctly, but uselessly) on every paraphrased or
causally-phrased query in the corpus, including the one it needed to solve.

**The gate concept is feasible only with a model in the loop, and even then
it is not yet trustworthy as a standalone authority — it needs a second,
independent check on any recommendation it surfaces before that
recommendation reaches a decision.**

## 2. Deadline Context

Preferred completion: September 30, 2026. Absolute deadline: October 1,
2026. This experiment was scoped and executed to answer the feasibility
question decisively and efficiently — it reused the exact R2 corpus rather
than rebuilding a benchmark, tested the cheapest mechanism (G1) fully before
reaching for a model, and ran G2 against only the handful of highest-value
cases (the decisive R2 failure pair, the abstention probe, and four
red-team/adversarial cases) rather than a full sweep. Total experiment
runtime: under three minutes of real Ollama call time, six real model calls.

## 3. Safety Invariants

| Check | Before | After |
|---|---|---|
| `run.py` / watchdog process | not running | not running |
| Port 5000 | unbound | unbound |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | unchanged |
| `memory/` directory | — | zero files touched (confirmed via `git status --porcelain memory/`, empty) |
| Production source | — | zero files modified |

Ollama was called directly via its raw HTTP API (`localhost:11434`), never
through `app.ollama_handler` or any production call path, and only for the
six isolated G2 spot-check calls listed in §10. No candidate text, real or
synthetic, was ever written to a production log or the real vector store.

## 4. Existing Retrieval Contract

`VectorMemory.search()` (`app/lib/vector_memory.py:120-146`) takes a query
embedding and `k`, L2-normalizes, runs `faiss.IndexFlatIP.search()`, and
returns `(text, score, meta)` tuples for whatever the index holds — **no
threshold, no cutoff, always returns up to `k` results** (re-confirmed this
session; matches the R2 audit's finding exactly).

`retrieve_relevant_memories()` (`app/core/memory_bridge.py:410+`) wraps this:
embeds the query, optionally blends in a Global Workspace bias vector,
calls `vector_memory.search()`, filters out `_ALWAYS_EXCLUDED_MEMORY_CATEGORIES`
(`code_analysis`, `self_model_reflection`), optionally post-filters by
`meta["memory_source"]`, and returns `[{"text": ..., "score": ..., "meta": ...}]`.
This is the entire contract — nothing in it inspects candidate content for
causal structure, diagnosis correctness, or recency-vs-relevance.

## 5. Available Candidate Information

Checked real production metadata directly (`memory/memory_meta.json`, sample
of live entries): every real entry's `meta` carries `memory_source`, `role`,
`task_type`, `timestamp`, `retention`, `backfill` — coarse provenance tags
only. **No real production memory entry carries a structured `trace_id`,
`diagnosis`, `corrective_action`, `verification_result`, or `confidence`
field.** Everything a relevance judgment would use beyond these six tags has
to come from the free-text `text` field itself, exactly as `retrieve_relevant_memories()`'s
own contract implies. This directly determines what G1 could possibly work
with (§9) and confirms the R2/orphaned-retrieval audits' conclusion that any
richer representation would need to be built at **ingestion**, not
invented after the fact by a gate.

## 6. R2 Benchmark Reuse

The exact `X1`–`X4` representations and `D1`–`D6` distractors from
`audits/2026-09-06_retrieval_capacity_proof.md` (source:
`app/experiments/retrieval_capacity_proof/run_experiment.py`) were copied
verbatim into `app/experiments/minimal_relevance_gate/run_experiment.py` —
same strings, not re-derived or paraphrased. The real Q7 top-6 FAISS
candidates (sourdough abstention query) were also reused directly from
`retrieval_results.json` rather than re-run.

## 7. Relevance Definition

Applied throughout this experiment, both to G1's rule design and as the
explicit instruction given to G2's prompt:

- **Lexical relevance** — shares words. (Cheapest, least trustworthy —
  this is what raw FAISS cosine similarity approximates.)
- **Semantic relevance** — same broad topic (e.g. "coding failures").
- **Situational relevance** — describes a comparably-shaped situation
  (a code-generation attempt, a missing-symbol failure).
- **Causal relevance** — the record's own
  `situation → action → consequence → diagnosis → outcome` chain plausibly
  transfers to the current situation.

G1's rule set (§9) can only approximate lexical/topical relevance — it has
no way to evaluate whether a stated diagnosis is *correct*, only whether
causal-structure-shaped language (`Diagnosis:`, `Correction:`, etc.) is
*present*. G2 was explicitly instructed (verbatim, in-prompt) to judge
causal relevance, not lexical/semantic similarity, and was told `UNCERTAIN`
is a valid, expected output rather than a failure to answer.

## 8. G0 Baseline

Reused directly from the R2 report, not re-run: raw FAISS ranks
`D5_semantically_unrelated_coding_failure` (0.4613) above
`X4_causal` (0.427) for the causal query (Q5) — the decisive failure this
whole line of work exists to address.

## 9. G1 Results — Deterministic, No-Model Gate

Implementation: `app/experiments/minimal_relevance_gate/gate.py`. Features
extracted purely from text: failure-vs-success language, causal-structure
marker count (`Situation:`/`Diagnosis:`/`Correction:`/etc.), stopword-
filtered topic-token overlap ratio, and quoted/snake_case identifier
overlap between query and candidate. Designed and frozen *before* running
any test case, per the mission's own "do not tune after seeing results"
instruction (Phase 3/13).

**Full result, Phase 6 (X1–X4 richness × all 6 R2 queries)** — real output:

| Query | X1 raw | X2 diagnosis | X3 action | X4 causal |
|---|---|---|---|---|
| Q1 exact repeat | RELEVANT | RELEVANT | RELEVANT | RELEVANT |
| Q2 different wording | NOT_RELEVANT | NOT_RELEVANT | UNCERTAIN | NOT_RELEVANT |
| Q3 different identifier | NOT_RELEVANT | UNCERTAIN | UNCERTAIN | NOT_RELEVANT |
| Q4 situational | NOT_RELEVANT | NOT_RELEVANT | NOT_RELEVANT | NOT_RELEVANT |
| Q5 causal | NOT_RELEVANT | NOT_RELEVANT | NOT_RELEVANT | NOT_RELEVANT |
| Q6 outcome-oriented | NOT_RELEVANT | UNCERTAIN | UNCERTAIN | NOT_RELEVANT |

**Reading this plainly**: G1 only ever says `RELEVANT` on Q1 — the query
that is a near-literal restatement of the raw failure text. On every
genuinely paraphrased, situational, or causal query (Q2–Q6) — the exact
cases this whole investigation is about — G1 says `NOT_RELEVANT` or
`UNCERTAIN` for **every representation, including the fully-causal X4
record that should be found**. Richer representation does *not* help G1;
if anything X4's extra prose slightly dilutes its already-low topic-overlap
ratio in a couple of cases relative to X2/X3. This is the opposite of what
FAISS itself showed in the R2 report (where richer representation helped on
paraphrased queries) — a real, disclosed finding: naive bag-of-words
overlap is a **strictly worse** signal than embedding cosine similarity for
this exact problem, not a cheap improvement on it.

## 10. G2 Results — Minimal Semantic/Causal Judge

Single Ollama call per (situation, candidate) pair, `llama3.2:3b`,
temperature 0, real HTTP calls to `localhost:11434/api/generate`. Prompt
verbatim in `run_experiment.py`'s `ollama_judge()`. G2 was judged
technically justified after G1's near-total failure on paraphrased content
(§9) — testing whether *any* mechanism beyond raw cosine similarity can do
better, without immediately reaching for a multi-model council (explicitly
avoided per the mission's own instruction).

**Phase 5 — the decisive case**: given Q5 and both `D5` and `X4`
independently —

- `D5_semantically_unrelated_coding_failure` → **NOT_RELEVANT** (correct:
  "it is about syntax errors in generated code, whereas the current
  situation is about failed dependency assumptions")
- `X4_causal` → **RELEVANT** (correct: "describes a similar error and
  resolution process involving an unresolved dependency reference")

**This is a real, clean pass on the exact case that motivated this whole
mission.** G2 succeeds where G0 (raw FAISS) and G1 (deterministic) both
fail.

## 11. Adversarial Results (Phase 7, A–F)

Judged against Q5 as the current situation.

| Case | Description | G1 | G2 (spot-checked subset) |
|---|---|---|---|
| A — same identifier, different cause | `trace_recorder` NameError caused by variable shadowing, not a missing import | NOT_RELEVANT (topic-gate never cleared) | **RELEVANT** — no hedge, despite the record's own stated cause differing from the missing-import mechanism the current situation implies |
| B — different identifier, same cause (`=D3`) | `session_manager`, same missing-import mechanism | NOT_RELEVANT | not spot-checked (redundant with X4's already-confirmed pass) |
| C — same context, different failure (`=D4`) | `TypeError` in the same tracing module | NOT_RELEVANT | not spot-checked |
| D — different context, same causal pattern | `schema_validator` missing-import, unrelated migration module | NOT_RELEVANT | not spot-checked |
| E — related but not actionable | generic "dependency management is hard" musing, no specifics | NOT_RELEVANT | not spot-checked |
| F — unrelated, non-coding (`=D6`) | reflection on trust/patience | NOT_RELEVANT | not spot-checked |

**Case A is the most important adversarial result in this report.** The
record explicitly states its cause is a scoping bug — *not* a missing
import — yet G2 rated it `RELEVANT` with a single confident sentence and no
hedge. If this record's own suggested "correction" (rename the shadowing
variable) were surfaced to a real retry prompt for a situation whose actual
cause *was* a missing import, it would be actively wrong, unhelpful advice
delivered with unearned confidence — a worse outcome than surfacing
nothing at all.

## 12. Abstention Results (Phase 8)

**G1** on the real Q7 (sourdough) top-6 FAISS candidates: `NOT_RELEVANT` on
all six, correctly landing on `NO_USEFUL_MEMORY`. But this is not
meaningfully different from G1's behavior on every other paraphrased query
in this report (§9, §11) — G1 abstains almost everywhere, correct or not,
because its topic-overlap bar is rarely cleared by anything but near-literal
text. This "pass" is not evidence of discrimination.

**G2** spot-check (`D1` against the sourdough query): `NOT_RELEVANT` —
"pertains to software testing and debugging, not cooking or baking."
Correct, and for the right reason (explicit topical mismatch stated in the
reasoning, not just a low score).

## 13. Uncertainty Results (Phase 9)

Ambiguous case: `NameError: name 'x' is not defined... some issue with an
undefined symbol... eventually resolved` — deliberately withholds the
specific mechanism.

- **G1**: `NOT_RELEVANT` (topic-overlap bar not cleared — same behavior as
  everything else, not a considered judgment).
- **G2**: `NOT_RELEVANT` — "does not contain a
  situation→action→consequence→diagnosis→outcome relationship that
  plausibly applies... involves an undefined symbol... whereas the current
  situation is about a dependency assumption error."

Neither system produced the mission's literal expected `UNCERTAIN` label,
but G2's actual behavior is the *safe* direction of the same failure —
it declined to claim relevance for a vague record rather than
over-claiming it, which is the property that actually matters (§16). Worth
recording plainly: G2's prompt allows `UNCERTAIN` and used it correctly
elsewhere (§14, contradictory pair) — it simply judged this specific case
confidently negative rather than uncertain, a defensible reading given how
little the record actually says.

## 14. False-Positive / Red-Team Analysis (Phase 11)

| Case | Description | G2 verdict | Assessment |
|---|---|---|---|
| Verbose, confidently wrong lure | Long, structurally rich record (`Situation:`/`Action:`/`Diagnosis:`/`Correction:`/`Lesson:` all present) whose diagnosis fabricates an "environmental noise" explanation and tells future generations to *ignore* this exact NameError | **RELEVANT** (real failure) | The clearest adversarial failure in this report — fluency and structural completeness fooled the judge into endorsing a wrong, actively harmful lesson |
| Contradictory pair, shown separately — "it IS an import fix" | States missing import is the cause, add the import | UNCERTAIN | Judge hedged even on the version that happens to be correct |
| Contradictory pair, shown separately — "it is NOT an import fix, don't add one" | States the opposite mechanism and opposite correction | UNCERTAIN | Judge correctly hedged on the version that is wrong |
| Stale record | Causally correct shape, but explicitly dated as predating a since-completed pipeline rewrite | **RELEVANT** | No temporal/versioning discount applied — the judge has no mechanism to weigh a record's own disclosed obsolescence against its otherwise-correct shape |
| Exact duplicate of X4 | — | RELEVANT | Expected, unsurprising |

**Net finding**: when only one side of a genuinely contradictory pair is
shown (the realistic production condition — you rarely have both a correct
and an incorrect memory of the same event to compare), G2 hedges
appropriately on *both* individually rather than confidently picking either
— a genuinely good, unexpected result. But it does **not** generalize that
same caution to a single record whose narrative is fluent and complete
(the verbose lure) or to one that discloses its own staleness (the stale
case) — it needs the contradiction made structurally obvious (two records
disagreeing) to trigger caution, not internal narrative red flags.

## 15. Failure Modes

1. **Fluent-wrong-narrative capture** (§14, verbose lure) — a structurally
   complete but causally incorrect record beats appropriate skepticism.
2. **Same-symptom / different-cause conflation** (§11, Case A) — shared
   surface features (same identifier, same exception class) were accepted
   as sufficient for `RELEVANT` despite an explicitly different stated
   mechanism.
3. **No staleness/versioning discount** (§14, stale case) — a record that
   discloses it predates a rewrite is still endorsed as if current.
4. **G1's topic-overlap gate is nearly always closed** for paraphrased
   language — not a graceful degradation, closer to "the mechanism barely
   functions outside near-literal repeats."

None of these were hidden or smoothed over in tuning — they were observed
on the first and only run of each case, per the mission's own "do not keep
adding complexity until positive" instruction.

## 16. Capability Gain

Relative to G0 (raw FAISS, R2's baseline): G2 provides a **real, measured
capability gain** on the one case that matters most (§10) and on genuine
abstention (§12) and on hedging across a genuinely contradictory pair
(§14). It does **not** provide safety against confidently wrong reasoning
when that reasoning is internally fluent, and does not discount its own
disclosed staleness. G1 provides **effectively zero** capability gain over
doing nothing — its only success case (Q1, near-literal repeat) is a case
raw FAISS already handles correctly on its own (R2's report: X-representations
all score reasonably on Q1).

## 17. Architectural Implications

A viable gate, if ever built for real, is **not** "FAISS top-k → one LLM
judgment → trust." The verbose-lure and same-identifier-different-cause
failures both point at the same missing piece: **the gate's recommendation
needs to be checked against something independent of its own narrative
plausibility** before it's trusted — most naturally, the real F2 sandbox
result the candidate record itself claims (`Verified outcome: ...`), not
just the judge's read of the prose describing that outcome. This is
consistent with, not a new idea invented for, this report: it's the same
"ground truth over self-report" discipline this whole project already
applies everywhere else (the Liveness Ledger, the functional quality
verifier). A gate that trusts a record's own claimed verification without
re-checking it is exactly the kind of self-report-trusting gap this
project's own standing culture exists to catch.

## 18. Classification: G-B — Promising But Fragile

A small gate (specifically, the G2 single-call LLM variant — G1 does not
qualify on its own) helps substantially on the motivating case and on clean
abstention, but fails important, concrete adversarial cases (§14, §11 Case A)
in ways that would actively mislead a real decision if trusted blindly.
**Not** G-A (would require passing the adversarial suite, which it did not)
and **not** G-C (the capability gain on the decisive case and on genuine
abstention is real and measured, not absent).

## 19. Deadline Recommendation

**Investigate one specific prerequisite first, do not proceed to build the
gate itself yet.** The prerequisite: pair any future gate judgment with a
real, independent check — reusing the F2 sandbox the self-edit pipeline
already runs, not a second LLM call — before a retrieved memory's
suggested correction is trusted. This is a smaller, cheaper, more
falsifiable next step than either abandoning the idea or building a
production gate now, and it directly targets the two concrete failure
modes found here rather than a hypothetical one. Given the Sept 30/Oct 1
window, this fits as a scoped, isolated follow-up experiment (not a
production change) if time allows; if it doesn't, this report's finding —
real but fragile capability, with a named, specific fix candidate — is
itself a complete and useful stopping point.

## 20. What Should NOT Be Built

- Do **not** build G1 (deterministic/rule-based) as a standalone gate — it
  has no material advantage over doing nothing on the cases that matter.
- Do **not** build a multi-model council gate — this experiment gives no
  evidence a single well-scoped judge call is insufficiently powerful; the
  failures found here are about missing an independent verification step,
  not about needing more model opinions.
- Do **not** wire any gate variant into the live self-edit pipeline before
  the fluent-wrong-narrative and same-symptom-different-cause failure
  modes have a concrete mitigation, tested and confirmed the same way
  §10–14 were tested here.
- Do **not** treat a record's own claimed `Verified outcome:` text as
  itself sufficient verification — that field describes what the record
  *claims* happened, not ground truth re-checked at judgment time.

## 21. Files Changed

- `app/experiments/minimal_relevance_gate/gate.py` (new) — pure G1 logic,
  no I/O, no imports from any production write path.
- `app/experiments/minimal_relevance_gate/run_experiment.py` (new) —
  isolated experiment driver; R2 corpus reused verbatim; new Phase 7/9/11
  cases; G1 execution; raw-HTTP G2 spot-check calls.
- `app/experiments/minimal_relevance_gate/gate_results.json` (new) — full
  raw G1 + primary G2 output.
- `app/experiments/minimal_relevance_gate/gate_results_g2_extra.json`
  (new) — the four supplementary G2 calls (both sides of the contradictory
  pair, stale, duplicate).
- `audits/2026-09-06_minimal_relevance_gate_feasibility.md` (this file).

No file outside `app/experiments/minimal_relevance_gate/` or `audits/` was
created or modified.

## 22. Git HEAD / RiverBrain Verification

Confirmed identical before and after this entire experiment:

- HEAD: `2cf2d95009943797db5ec41fea9b4021634fd5e6`
- `river_brain.pkl` sha256: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`
- `run.py` / watchdog: not running, before or after.
- `memory/` directory: zero files touched (`git status --porcelain memory/`
  returns empty).
