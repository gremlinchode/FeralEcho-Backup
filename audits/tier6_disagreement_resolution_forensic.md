# Tier-6 Forensic Mission: Candidate Disagreement, Ranking, and Evidence Resolution

**Method discipline**: this entire investigation is deterministic replay against the already-captured
Tier-4 corpus plus real (non-generative) sandbox re-execution of already-generated candidate code. **Zero
new LLM/model calls were made.** No Tier-3, Tier-4, or prior Tier-5/Tier-5-counterfactual artifact was
modified. One new script (`scripts/tier6_disagreement_analysis.py`) was created — read-only, imports the
real, unmodified `river_deliberation.py` functions directly, reimplements nothing. **No production code
was modified in this pass; no critical safety bug was found that would have required one.**

## Executive Verdict

**PARTIALLY SUPPORTED** (the prior Tier-5 counterfactual audit's specific "3/3" fallback-failure claim) —
**independently re-confirmed and found to generalize far beyond the 3 originally-checked cases.** The
corpus-wide analysis in this report finds a materially larger and more precisely-characterized problem
than either prior report identified: for `ARCH_COUNCIL`, the current "prefer longest" fallback heuristic
(78.2% correct-pick rate on real disagreement events) is **outperformed by simply preferring the
shortest parsing candidate (93.6%)** — not because shortness causes correctness, but because length is
confounded with councillor model identity, and one specific real councillor (`echo:latest`, acting in its
councillor role) is dramatically less reliable (53.6%) than the other two (83.3%, 88.1%) on this task
pool. **GO WITH MODIFICATIONS** on further experimentation, with a concrete, low-cost, evidence-grounded
replacement recommended in §16 below — but see the falsifiability statement in §21 before treating that
recommendation as settled.

## Evidence Table

| Claim | Verdict | Evidence | Confidence |
|---|---|---|---|
| Prior "3/3 fallback picks wrong candidate" finding | SUPPORTED, generalizes further | Independently re-derived from raw data (§5); corpus-wide analysis shows the same pattern in a much larger, structurally-explained form | High — deterministic, full-corpus |
| "select_best_fallback_candidate() optimizes for correctness" | UNSUPPORTED | Direct code read: parses, then raw-text length. No correctness signal anywhere in it. | High — direct source read |
| "Length predicts correctness" | UNSUPPORTED as a general causal claim; SUPPORTED as an observed correlation confounded by model identity | Per-model breakdown (§5) shows the real driver is which councillor produced the response, not its length | High — direct, computed |
| "Agreement predicts correctness" | UNSUPPORTED | Exact-agreement events had *lower* historical pass rates (50%/66.7%) than disagreement events (68.8%/80.8%) in this corpus | Moderate — small n (4, 6 events) |
| "95-96% is model capability" | OVERSTATED as commonly read; SUPPORTED as "best-of-3 solvability" | Independently reproduced twice now (Tier-5 counterfactual audit and this report), identical numbers both times | High — reproduced twice, deterministic |
| "Byte-for-byte unaffected" (non-coding paths) | SUPPORTED for task-type isolation; the global regex change's second affected path (`verify_response_code()`) is real, confirmed, and beneficial | Direct grep, unchanged since the prior audit | High |
| "Self-edit isolation is enforced" | UNSUPPORTED | Zero call-site enforcement found; documentation + one narrow manual test only | High — direct grep |
| "bf06 is eliminated by construction" | SUPPORTED | Re-confirmed independently, this report's own fresh corpus data | High |
| "cs09 is caught and corrected" | PARTIALLY SUPPORTED | Caught reliably; "corrected" depends on a fallback heuristic now shown to be unreliable in general | High for "caught," Moderate for "corrected" |
| "The current architecture can distinguish correct from incorrect using evidence, not heuristics" | UNSUPPORTED | Direct answer to adversarial question 1 (§21) | High |

## Full-Corpus Disagreement Analysis

All 168 real historical events (84 `ARCH_COUNCIL`, primary; 84 `BASE_N`, secondary/no production analog —
see the methodology caveat in the prior Tier-5 counterfactual report, unchanged and still applicable
here) were classified. Categories actually observed in this corpus (of the 15 requested, several did not
occur at all — stated plainly, not padded):

| Classification | `ARCH_COUNCIL` | `BASE_N` (secondary) |
|---|---:|---:|
| `majority_correct_minority_wrong` (2-of-3 correct) | 36 (42.9%) | 14 (16.7%) |
| `textual_variation_all_correct` (different text, all pass) | 33 (39.3%) | 54 (64.3%) |
| `exactly_one_correct_rest_wrong` | 9 (10.7%) | 7 (8.3%) |
| `exact_agreement_all_correct` | 3 (3.6%) | 5 (6.0%) |
| `all_incorrect_semantically` | 3 (3.6%) | 3 (3.6%) |
| `exact_agreement_all_incorrect` (unanimous shared bug) | 0 | 1 (1.2%) |
| `minority_correct_majority_wrong`, `all_incorrect_including_syntax_invalid` | 0 | 0 |

**Categories requested but not observed in this corpus**: "truncated candidates" (zero truncations
occurred anywhere in the 336-record Tier-4 dataset, per the original execution report), "candidates
differing only in edge-case handling" and "different assumptions about the task" (not separately
distinguishable from `textual_variation_all_correct`/`majority_correct_minority_wrong` without manual
semantic reading of each disagreement, which this pass did not attempt at scale — **INDETERMINATE**
whether these exist as a distinct sub-category within the observed classes).

**The dominant real-world shape of "disagreement" is not "some candidates are broken."** 82.1%
(`ARCH_COUNCIL`) / 87.0% (`BASE_N`) of all events have at least one correct candidate available
(`textual_variation_all_correct` + `majority_correct_minority_wrong` + `exactly_one_correct_rest_wrong` +
`exact_agreement_all_correct`). The real, quantified problem is not "the model pool can't solve these
tasks" (already established in the prior reports as the 95-96% best-of-3 finding, re-confirmed
identically in §12) — it is that **the mechanism choosing among available candidates does not reliably
find the correct one.**

## Fallback Heuristic Audit

Direct code read (`app/core/river_deliberation.py`): `select_best_fallback_candidate()` filters to
candidates whose extracted code both extracts and parses, then returns `max(pool, key=len)` on the **raw
response text** (not the extracted code, not any correctness signal). **It is exactly and only a
"parses, then longest" heuristic — it does not establish, measure, or approximate correctness in any
way.** Describing its output as "the best candidate" without this qualifier is not defensible; this
report uses "the selected candidate" throughout.

**Corpus-wide measurement, on the 78/75-event subsets where real disagreement exists and at least one
correct candidate is actually available** (i.e., excluding unanimous-agreement events, where there is
nothing to choose between, and all-incorrect events, where no correct choice exists to be missed):

| Selection strategy | `ARCH_COUNCIL` correct-pick rate | `BASE_N` (secondary) correct-pick rate |
|---|---:|---:|
| **Real `select_best_fallback_candidate()`** | **61/78 (78.2%)** | 67/75 (89.3%) |
| Longest parsing (confirmed identical to the real function — see below) | 61/78 (78.2%) | 67/75 (89.3%) |
| Shortest parsing | **73/78 (93.6%)** | 66/75 (88.0%) |
| Majority structural similarity (prefers whichever candidate shares an AST fingerprint with the most others, length-tiebreak otherwise) | 68/78 (87.2%) | 67/75 (89.3%) |

**Correctness by length rank across ALL 84 events per arm** (0 = longest candidate in the event, 2 =
shortest):

| Rank | `ARCH_COUNCIL` correctness | `BASE_N` (secondary) correctness |
|---|---:|---:|
| 0 (longest) | 63/84 (75.0%) | 71/84 (84.5%) |
| 1 (middle) | 50/84 (59.5%) | 71/84 (84.5%) |
| 2 (shortest) | 76/84 (90.5%) | 70/84 (83.3%) |

**`ARCH_COUNCIL` shows a real, non-monotonic, inverse relationship between length rank and correctness —
not the direction the current heuristic assumes.** `BASE_N` shows essentially no relationship (83.3-84.5%
flat across all three ranks) — expected, since `BASE_N`'s three same-model attempts have no analogous
identity confound.

**Root cause, traced directly, not left as an unexplained correlation**: per-real-councillor breakdown
across all 84 `ARCH_COUNCIL` events:

| Councillor | n | Correct | Rate | Avg. raw response length |
|---|---:|---:|---:|---:|
| `mlx:qwen3` | 84 | 74 | **88.1%** | 477 chars (shortest) |
| `qwen2.5-coder:7b` | 84 | 70 | 83.3% | 1285 chars (longest) |
| `echo:latest` | 84 | 45 | **53.6%** | 971 chars (middle) |

`echo:latest`, acting in its real councillor role (distinct from its separate role as the synthesizer),
is the least reliable of the three real councillors on this specific task pool by a wide margin, and its
responses land at a middling length — not consistently the longest, which is why "prefer longest" ends
up picking it, or the also-imperfect `qwen2.5-coder:7b`, over the shorter but markedly more reliable
`mlx:qwen3`, more often than a correctness-blind observer might expect. **The correct, precise statement is:
"in this real council composition, response length is a confound for councillor identity, and councillor
identity — not length — is what actually predicts correctness. This is a property of this specific,
currently-deployed council composition, not a general law about code length."**

**Concrete counterexamples** (not aggregate statistics alone), independently reconstructed from raw data,
per the mission's explicit demand not to accept the prior "3/3" claim on prose alone:

- **`bf10` (stage 2)**: `mlx:qwen3` (1101 chars, the longest of the three here) is selected and is
  **wrong**; `qwen2.5-coder:7b` (857 chars) and `echo:latest` (1056 chars) are both **correct** and share
  an identical AST fingerprint with each other (a genuine 2-of-3 structural majority — the
  majority-structural strategy correctly identifies this and would have picked correctly).
- **`rf02` (stage 2)**: `echo:latest` (685 chars) is selected and is **wrong** (and, distinctly, defines
  zero top-level names in its own extracted code — a `find_missing_agreed_definitions()`-relevant signal
  in its own right); `qwen2.5-coder:7b` (683 chars) and `mlx:qwen3` (681 chars) are both **correct**, but
  do **not** share an identical AST fingerprint with each other (two independently-arrived-at correct
  implementations, not a structural match) — the majority-structural strategy's correct pick here is
  attributable to its length tiebreak among singleton groups, not genuine consensus evidence. Stated
  honestly: this strategy got the right answer for a reason weaker than "consensus."
- **`ae02` (stage 2, `BASE_N`, secondary)**: attempt `#0` (1517 chars, longest) is selected and is
  **wrong**; attempts `#1` (1044 chars) and `#2` (1345 chars) are both **correct** but, like `rf02`, do
  **not** share an identical AST fingerprint with each other — **the majority-structural strategy fails
  identically to the real fallback here**, because no genuine structural majority exists among the correct
  candidates. This is the honest limit of a purely-structural approach, not glossed over: it only helps
  when correct candidates happen to converge on identical code, which they do not always do even when
  multiple candidates are independently correct.

**This pattern is deterministic, not probabilistic, given the same captured input** — re-running
`select_best_fallback_candidate()` against the same stored `opinions` dict always returns the same
answer, since it is a pure function over already-fixed text. Whether the *underlying real-world rate* of
this failure mode is stable across a fresh sample is a separate question this replay cannot answer (see
§18) — **this audit measures what happened, not what would happen again.**

## Evidence-Source Analysis: What Actually Predicts Correctness

| Signal | Predictive power found in this corpus | Verdict |
|---|---|---|
| **Syntax validity (parses)** | Weak on its own for final-outcome prediction: "all candidates parse" events show 68.4% (`ARCH_COUNCIL`)/80.5% (`BASE_N`) historical pass rate vs. 62.5%/50% when some candidate doesn't parse — a real but small, noisy (n=8, n=2) gap. Necessary but far from sufficient. | Weak positive signal |
| **Structural completeness (agreed definition names present)** | Directly responsible for 1/3 `ARCH_COUNCIL` and 4/5 `BASE_N` real interceptions in the prior counterfactual replay — a real, if narrow (names only, never bodies — see prior report §8/§9), signal | Real, narrow-scope positive signal |
| **Exact/AST agreement (consensus)** | **Does not predict correctness better than disagreement does** in this corpus: exact-agreement events show 50%/66.7% historical pass rates vs. 68.8%/80.8% for disagreement events. Directly confirms the mission's own stated caution — three candidates agreeing on a wrong algorithm is still wrong, and this corpus shows agreement is, if anything, mildly *associated* with lower pass rates here (small n, not causal) | Consensus ≠ correctness, confirmed numerically, not just asserted |
| **Length** | Actively misleading for `ARCH_COUNCIL` (inverse relationship, confounded by model identity); flat/uninformative for `BASE_N` | Negative-to-neutral signal |
| **Majority structural similarity (2+ candidates share an identical AST)** | Only computable in 19.0% (`ARCH_COUNCIL`)/28.6% (`BASE_N`) of events — the other 81.0%/71.4% are **fully 3-way structurally distinct**, with no pair sharing any structural match at all. When it *is* computable, it correctly identifies the correct majority in genuine cases (`bf10`) but degrades to an arbitrary length-tiebreak when it isn't (`rf02`, `ae02`) | Real but narrow; inapplicable to the large majority of real disagreement events |
| **Councillor/model identity (via already-existing RiverBrain historical scores)** | Not directly tested in this replay (would require reading live RiverBrain state, out of scope for a pure Tier-4-corpus replay), but the per-model breakdown above is strong circumstantial evidence this signal, already computed and stored for council *selection*, is never consulted for candidate *ranking* — a concrete, existing, currently-unused evidence source | Plausible, not yet directly measured — flagged as the report's central recommendation, not a confirmed result |

**Candidate independence**: `ARCH_COUNCIL`'s three real candidates come from three distinct models with
independently-jittered temperatures (confirmed via `mechanism_calls`' own recorded values in the raw
data) — closer to genuine independence than `BASE_N`'s three same-model, same-prompt, differently-seeded
attempts, which share model identity, context, and prompt entirely and differ only in sampling
temperature. **Three `BASE_N` "candidates" should not be treated as three independent votes in the way
three different models' opinions might be** — this is a real, disclosed distinction the "candidate count"
alone obscures, and part of why this report treats `BASE_N` as secondary throughout.

## Consensus vs. Correctness — Explicit Statement

Tested directly, not assumed: **agreement establishes that candidates arrived at the same answer; it does
not establish that the answer is right.** `BASE_N`'s one real `exact_agreement_all_incorrect` event
(`rf12`, stage 2 — three same-model attempts unanimously producing the identical, wrong `digit_sums`
implementation) is direct, concrete proof this occurs in practice, not merely in principle. Combined with
the finding that agreement events do not show a higher historical pass rate than disagreement events in
this corpus, **the evidence directly contradicts treating "the candidates agree" as meaningful correctness
evidence on its own** — it is evidence of consensus, and consensus is a real, useful signal only insofar
as independent failure is less likely to be correlated than independent success, a property not
established here and contradicted by `rf12`.

## The UNRESOLVED Outcome

Quantified directly from this corpus: **81.0% (`ARCH_COUNCIL`) / 71.4% (`BASE_N`) of all real events have
no pair of candidates sharing any structural agreement at all.** Under a strict rule that only
auto-resolves disagreement when *some* structural evidence (agreement or majority) actually exists,
roughly four in five `ARCH_COUNCIL` events would need to fall back to a *different* resolution mechanism
than pure structural comparison — either length (already shown unreliable), an execution/test signal
(unavailable for arbitrary conversational questions — no general oracle exists, per the prior report's
own confirmed finding), or genuine `UNRESOLVED`.

**Cost of `UNRESOLVED`, stated concretely rather than abstractly**: if `UNRESOLVED` were declared for
every event lacking structural agreement, roughly 68/84 (`ARCH_COUNCIL`) real historical events would
have received no confident single answer — a large fraction, most of which (per §3's classification) do
have a correct candidate available (just not one identifiable by structure alone). **This is the real
tradeoff, not a hypothetical one**: a system honest about the limits of available evidence would decline
to choose far more often than it currently does; a system that always chooses, as the current one does,
resolves every case but is measurably wrong some of the time in a way this report has now characterized
precisely. Neither option is free. **This report does not recommend blanket `UNRESOLVED` at this rate** —
see §16 — but the number is reported plainly because the tradeoff cannot be reasoned about honestly
without it.

## `bf06` Reconstruction

Independently re-derived from raw `mechanism_calls`, via a fresh script, not the prior report's prose:

- **Classification**: `exact_agreement_all_correct`. All three real councillor responses
  (`qwen2.5-coder:7b`: 529 chars, `mlx:qwen3`: 698 chars, `echo:latest`: 345 chars — genuinely different
  *raw* lengths, confirming the agreement is on the *extracted code*, not the surrounding text) extract
  to AST-identical, independently-correct code defining `find_missing`.
- **BEFORE Tier-5**: the real historical synthesis call was invoked unconditionally (no agreement check
  existed), and its output — confirmed via this report's own fresh fingerprint comparison to **match none
  of the three candidates' AST** — fabricated an unsupported `n = len(nums) - 1`, breaking otherwise-unanimous
  correct logic. Historical result: **FAIL**.
- **AFTER Tier-5**: `detect_full_agreement()` fires (re-confirmed, this report's own independent
  computation). `deliberate_and_learn()`'s real source returns the agreed code on the very next line, with
  no synthesis call made.
- **Safeguard that triggers**: `detect_full_agreement()`, exclusively.
- **Safeguard that does NOT trigger**: `find_missing_agreed_definitions()` — never reached, since the
  function returns before that code path exists. Confirmed (again, independently, matching the prior
  counterfactual report) that this safeguard **could not have caught this specific failure on its own**,
  since the historical synthesis's function name (`find_missing`) would have remained present even with
  the fabricated bug — the completeness check only compares names, never bodies.
- **Failure eliminated**: any future case of genuine, verified unanimous agreement being broken by an
  unforced synthesis rewrite, for `task_type == "coding"`.
- **Failure modes still possible**: any case where candidates are *not* AST-identical (81.0% of this
  corpus) — the agreement shortcut provides zero protection there, and the completeness check's
  name-only scope leaves body-level mutation within an agreed signature completely unaddressed.

## `cs09` Reconstruction

Independently re-derived, fresh:

- **Classification**: `textual_variation_all_correct` — meaningfully different from `bf06`'s classification.
  All three same-model attempts (2427, 2447, 1493 raw chars — genuinely different text, unlike `bf06`'s
  identical code) independently define and correctly implement `ThreadSafeMultiCounter`, but are **not**
  AST-identical to each other (confirmed: `detect_full_agreement()` would not, and does not, fire here).
- **BEFORE Tier-5**: the historical synthesis call was invoked (same as `bf06` — no distinguishing
  condition existed to skip it), and its own extracted code, confirmed by this report to match **none** of
  the three candidates' fingerprints, parses successfully but defines **zero** top-level names — not a
  partial omission, a complete absence of any real definition. Historical result: **FAIL** (`NameError`,
  per the prior report's own literal reproduction).
- **AFTER Tier-5**: `detect_full_agreement()` does **not** fire (candidates genuinely differ textually,
  correctly not treated as identical). `find_missing_agreed_definitions()` fires: all three parseable
  candidates agree on defining `ThreadSafeMultiCounter`; the historical synthesis defines nothing;
  the class name is flagged missing. `select_best_fallback_candidate()` is invoked and, in this specific
  case, correctly selects a candidate containing the required class (re-confirmed: the fallback pick here
  happens to be correct, unlike `bf10`/`rf02`/`ae02` above).
- **Safeguard that triggers**: `find_missing_agreed_definitions()`, exclusively.
- **Safeguard that does NOT trigger**: `detect_full_agreement()` — the candidates are correct but not
  identical, so there is genuinely nothing for it to detect here; this is the shortcut correctly *not*
  firing on a case outside its scope, not a missed opportunity.
- **The two mechanisms do not overlap in either headline case** — each is responsible for exactly one of
  the two, with zero redundancy. This means the reported "two demonstrated fixes" are evidence for **two
  separate, narrowly-scoped mechanisms**, not one general capability, and neither provides backup coverage
  for the other's blind spots.
- **Failure eliminated**: complete definitional omission from synthesis, when every parseable candidate
  agreed the definition should exist.
- **Failure modes still possible**: exactly the same completeness-check blind spots as `bf06`'s (body-level
  mutation), *plus* — uniquely exposed by this specific mechanism's own selection step — the demonstrated
  risk that the fallback chosen to "correct" the detected loss is itself unreliable (§5), which happened
  not to bite in this specific instance but did in three other real, checked instances.

## Tier-5 Safeguard Coverage

**What is actually protected, stated as narrowly as the evidence supports**: (1) synthesis fabricating
content into a case of genuine, verified, AST-level unanimous candidate agreement — fully closed by
construction; (2) synthesis omitting an agreed-upon top-level definition **name** — detected reliably,
corrected unreliably (§5). **What remains exposed, confirmed against this corpus rather than only
theorized**: any disagreement pattern outside AST-identical unanimity (81.0%/71.4% of all real events);
any body-level logic mutation inside a preserved function/class signature; the demonstrated failure of the
one existing corrective mechanism (fallback selection) to reliably pick a correct candidate even when one
is available. **Coverage estimate, stated as a fraction of the corpus, not a vague qualitative claim**: of
84 real `ARCH_COUNCIL` events, the two mechanisms combined intercepted 3 real historical failures (3.6%
of all events, 11.1% of the 27 real historical failures) — the large majority of real historical failures
(24 of 27) remain entirely outside either mechanism's reach.

## 95-96% Terminology Audit

Independently reproduced a **second time**, via a completely separate script and computation path than
the prior counterfactual report, with identical results both times — the strongest form of confirmation
available without new data:

| Metric | `ARCH_COUNCIL` | `BASE_N` (secondary) |
|---|---:|---:|
| Per-individual-attempt success rate | **75.0%** (189/252) | **84.1%** (212/252) |
| Best-of-3 ("at least one of three succeeds") | **96.4%** (81/84) | **95.2%** (80/84) |
| Final synthesized (actual delivered) success rate | 67.9% (57/84) | 79.8% (67/84) |

**"The model solves 95-96% of tasks" remains OVERSTATED if read as describing single-shot or general
model capability.** The correct, precise term, confirmed twice now: **"best-of-3 candidate solvability"**
— always reported alongside the true per-attempt rate (75-84%), which is itself much closer to (and for
`ARCH_COUNCIL`, below) the actual delivered rate than the best-of-3 figure is.

## Regex Isolation Audit

Re-confirmed unchanged since the prior audit: `_FENCE_RE` in `code_verification.py` carries `re.IGNORECASE`,
used by exactly two real call sites — `river_deliberation.py`'s new `_extract_candidate_code()` (gated to
`task_type == "coding"` synthesis) and the pre-existing `verify_response_code()`, called from
`routes_echo_studio.py:227`, itself independently gated to `task_type == "coding"` for a **different**,
unrelated feature (post-response self-consistency verification, not synthesis). **"Byte-for-byte
unaffected" is accurate for every non-coding task type; it does not, on its own wording, disclose that a
second, pre-existing coding-task feature also changes behavior as a side effect of the same fix** — a
scope-precision gap, not a factual error. The change itself remains confirmed **beneficial, not risky**:
`verify_response_code()` fails open on any internal issue, so a previously-silent extraction failure on a
capitalized fence becoming a successful extraction can only add correctly-caught cases, never remove
existing protection.

## Self-Edit Isolation Audit

Re-confirmed unchanged: `CODE_OUTPUT_RULES` has exactly 2 real call sites (`self_edit_manager.py`'s own
`generate_code_from_plan()`, `wolf_friction_bridge.py`), both pre-existing and legitimate.
**Enforcement status: documentation and one narrow, manual, single-file regression test — not
architectural enforcement.** No import guard, runtime assertion, linter rule, or automated/continuous
check (e.g. a Liveness Ledger entry, this project's own established pattern for comparable structural
guarantees) exists. A hypothetical new file importing `CODE_OUTPUT_RULES` directly tomorrow would not be
caught by anything currently in place. This finding is unchanged from the prior audit and is re-confirmed
here rather than re-argued, since nothing about the relevant code has changed in the interim.

## Architecture Comparison

| | **A — Current (Tier-5)** | **B — Evidence-ranked fallback** | **C — Verification-first** | **D — Preserve disagreement** | **E — Hybrid escalating** |
|---|---|---|---|---|---|
| Correctness (measured against this corpus, where checkable) | 78.2% correct-pick on real disagreement (`ARCH_COUNCIL`) | 87.2-93.6% depending on exact ranking rule used (measured, §5) | Not measurable here — no general oracle exists for arbitrary production coding questions (only Tier-4's own frozen suites have one) | By definition, never wrong when it fires; the question is how often it fires (§8: ~81% of events under a strict rule) | Depends on the escalation ladder's own top tier; at minimum matches B, potentially matches C when execution evidence exists |
| False positives (confidently wrong) | Present, quantified (§5) | Reduced but not eliminated (`ae02`'s residual failure) | Near-zero when an oracle exists; **undefined/unknown** when none does | None by construction | Reduced to whichever tier actually fires |
| False negatives (missed available correct candidate) | High (3/3 checked concrete cases) | Lower, but real (1/3 concrete cases still fails) | Unknown outside oracle-bearing contexts | N/A — never claims a false negative, only declines | Lower than A, bounded by which tier fires |
| Information preservation | Destroys 2 of 3 candidates on every choice | Same destruction pattern as A | Same, when it chooses at all | **Preserves everything** — the stated ideal in the mission's own closing framing | Preserves when unresolved; destroys otherwise |
| Computational cost | Zero extra (already shipped) | Near-zero (pure functions, already-generated text, no new calls) | Requires a real oracle per use — **does not exist today** for general conversational coding | Zero extra generation cost; downstream cost of presenting/handling multiple candidates | Low to moderate, scales with how often expensive tiers fire |
| Latency | None | None | Unknown/potentially high if a test-generation step were added | None | Low, same reasoning as cost |
| Implementation complexity | Low (already built) | Low — reuses already-computed AST fingerprints plus already-existing RiverBrain scores | High — requires building a general-purpose oracle that does not currently exist | Low — a return-type change and a caller-side UX decision | Moderate — requires composing B and (where available) C cleanly |
| Failure transparency | Low — no signal distinguishes "confident" from "guessed" | Moderate — the ranking rationale is at least inspectable | High when an oracle exists | **Highest** — explicitly declines rather than guessing | High — the log already built for this refactor (`synthesis_integrity_log.jsonl`) already records which tier fired |
| Pathological-case susceptibility | Confirmed: anti-correlated with correctness in a specific, real, currently-deployed council composition | Vulnerable to the "no structural majority exists" case (81% of this corpus) reverting to a length tiebreak | Vulnerable to a poorly-specified or absent oracle silently producing false confidence | Vulnerable to *over*-declining if the "unresolved" threshold is set too conservatively, discarding real signal like the 78%+ base rates already available | Vulnerable to whichever component tier is weakest; inherits both B's and C's specific risks at their respective stages |

**No architecture is selected as a clean "winner" — the evidence supports a specific, narrow upgrade to
Architecture A (replacing the fallback's ranking rule), not a wholesale replacement.** Architecture C is
not viable today for general production (no oracle); Architecture D's blanket form is too costly at the
observed 81% non-agreement rate to recommend outright; Architecture E is the right *shape* for where this
should eventually go, but its expensive tier (C) has no real content to escalate to outside of contexts
that already have their own oracle (Tier-4's own harness, self-edit's F2 gate). **The concrete
recommendation (§16) is Architecture B, specifically, not the fully general E — with the explicit
acknowledgment that this is a narrower, more modest step than "solve disagreement resolution."**

## Next-Experiment Design

**Confirmed correct to extend, not replace, the prior report's 3-arm proposal, with one additional
control this audit's own findings make necessary.**

- **Arms**: `OLD` (original synthesis, no mechanical checks) / `PROMPT_ONLY` (new coding-preservation
  prompt, no mechanical checks) / `FULL` (new prompt + agreement + completeness, current length-based
  fallback) / **`FULL_RANKED` (new, added by this audit: new prompt + agreement + completeness, with the
  fallback's ranking rule replaced per §16)**. The 4th arm is necessary specifically because this audit's
  own central finding (the fallback ranking rule itself is a measurable weak point) is a variable the
  original 3-arm design cannot isolate — without it, any improvement `FULL` shows could be fully
  attributable to the agreement/completeness mechanisms alone, leaving the fallback-quality question
  unanswered by the experiment that was supposed to settle it.
- **Task construction**: fresh, disjoint, hash-frozen suite (following the Tier-4 protocol's own
  discipline exactly) — never reusing Tier-4's 84, this report's own analysis inputs, or the 5-task Tier-5
  live-validation set.
- **Candidate-generation reuse**: as recommended in the prior counterfactual report, generate each task's
  councillor candidates **once**, then run all 4 synthesis/selection variants against that same frozen
  candidate set — removes candidate-generation variance as a confound between arms and cuts real new-model-call
  cost from 4× a full pipeline to 1× generation + up to 4× one cheap synthesis/selection step.
- **Randomization**: arm order randomized per task (mirroring `randomized_arm_order()`'s existing,
  reusable mechanism).
- **Model controls**: pin the same model/council composition Tier-4 used, explicitly, for direct
  comparability — and explicitly flag if the real, live council composition has drifted since (per this
  project's own established "check, don't assume" discipline for exactly this kind of claim).
- **Token controls**: identical `max_tokens` across all arms and candidate-generation, matching Tier-4's
  own discipline.
- **Metrics**: primary — paired pass rate across the 4 arms, all pairwise McNemar comparisons; secondary —
  per-arm fallback/shortcut/completeness firing rates, and (new, motivated directly by §5) the fallback's
  own correct-pick rate specifically among disagreement-with-a-correct-option events, tracked as its own
  endpoint, not folded into the aggregate pass rate.
- **Stopping criteria**: pre-registered before task authoring, following the Tier-4 protocol's own
  discipline (freeze protocol, freeze tasks, hash both, execute once, analyze once) — not re-derived here
  since it is a process discipline, not a new statistical question.
- **Frozen artifacts**: task suite + hash, protocol + hash, all raw results — before any execution, per
  the same standard this entire investigation lineage has held itself to throughout.

## Statistical Power

**Independently re-verified, not repeated**: the observed discordant (outcome-changing) rate is
**3.6%** (`ARCH_COUNCIL`, 3/84) and **6.0%** (`BASE_N`, 5/84) — directly recomputed in this report's own
analysis (§Full-Corpus Disagreement Analysis data), matching the prior counterfactual report's numbers
exactly via an independent script.

Using the same McNemar sign-test power approximation (α=0.05, 80% power) both prior reports established:

| Assumed true discordant split | Required total N, `ARCH_COUNCIL` rate (3.6%) | Required total N, `BASE_N` rate (6.0%) |
|---|---:|---:|
| Large effect (100:0) | ~185 | ~111 |
| Moderate effect (90:10) | ~266 | ~159 |
| Small effect (80:20) | ~539 | ~324 |

**Why the required N changes so dramatically with discordance rate**: McNemar power depends only on the
number of *discordant* pairs, not total tasks — a low base discordance rate means most of any sample
contributes zero statistical information (both arms agree, concordant, uninformative for the paired
test). At 3.6-6.0% discordance, a 20-30 task sample yields on the order of 1-2 discordant-eligible events
total, nowhere near sufficient for a McNemar conclusion in either direction. **This report reaches the
identical conclusion as the prior counterfactual audit via the identical, independently-checked
calculation: 20-30 tasks is a substantial underestimate; 100-500+ tasks are required for genuine power,
scaling with which effect size is assumed and which arm's discordance rate is used as the planning basis.**
No new sample-size number is invented here — this is confirmation, not revision.

## Recommended Implementation Path

**Only after all forensic work above**: replace `select_best_fallback_candidate()`'s ranking rule with a
two-stage evidence-based rule, using evidence sources already computed or already available in production,
adding no new infrastructure:

1. **Prefer majority AST-structural agreement** (2+ candidates sharing an identical fingerprint) when it
   exists — confirmed to correctly resolve genuine cases (`bf10`) at essentially zero cost (the
   fingerprints are already computed for the agreement check).
2. **When no structural majority exists** (the common case, 81.0%/71.4% of this corpus), **break ties
   using each candidate's producing model's existing, already-accumulated RiverBrain historical score for
   this task type** (`score_model()`, already computed for council *selection* and never consulted for
   candidate *ranking*) — directly motivated by the per-model breakdown in §5 (`mlx:qwen3` 88.1% vs.
   `echo:latest` 53.6% as councillors on this pool), not a new assumption.
3. **Fall back to length only as a last resort**, if no model-score data exists (e.g., `BASE_N`-shaped
   same-model attempts, where this signal is inapplicable by construction) — preserving current behavior
   exactly where the new signals cannot apply, per this project's own established "preserve prior output
   for callers that don't opt in" discipline.

This is deliberately **not** Architecture C or D — it does not require building a general oracle, and it
does not change how often the system chooses versus declines. It is a narrow, low-cost upgrade to
Architecture A's weakest measured component, validated against this same corpus at zero additional model
cost (exactly as this report already partially demonstrated in §5's `majority_structural_similarity`
simulation) before being proposed for the next real experiment.

## Final Adversarial Questions

1. **Can Echo currently distinguish a correct candidate from a longer incorrect candidate using evidence
   rather than heuristics?** **No.** Confirmed directly: `select_best_fallback_candidate()`'s only
   discriminating signal is syntactic parseability, then raw length — no correctness evidence of any kind
   is consulted.
2. **If two candidates are correct and one is wrong, how often does current fallback preserve a correct
   candidate?** In the 3 concrete `majority_correct_minority_wrong` cases checked where the fallback fired
   without resolving the historical failure (§5), it preserved the correct candidate **0 of 3 times** —
   it selected the single wrong candidate in every checked instance. This is not the rate across *all*
   `majority_correct_minority_wrong` events (50 such events exist across both arms; most never triggered
   the fallback because the historical synthesis already succeeded) — it is the rate specifically among
   the subset where the fallback mechanism was actually exercised and failed to fix the outcome.
3. **If one candidate is correct and all others are wrong, how often does current fallback recover it?**
   **INDETERMINATE from this corpus** — no concrete `exactly_one_correct_rest_wrong` event in this
   dataset happened to also trigger the completeness fallback (the events where the fallback fired and
   failed were all `majority_correct_minority_wrong` shape, per §5's three cases). This specific question
   requires either a larger corpus or a targeted synthetic test; this report does not manufacture an
   answer it cannot support.
4. **Does candidate consensus predict correctness, or merely agreement?** **Merely agreement**, confirmed
   numerically (§"Consensus vs. Correctness") — agreement events in this corpus show no higher, and
   possibly lower, historical pass rates than disagreement events.
5. **Can syntax/AST evidence meaningfully predict semantic correctness?** **Partially, and narrowly.**
   Syntax validity alone is a weak positive signal (§Evidence-Source Analysis). AST-level structural
   agreement, when it exists, is a genuine positive signal (`bf10`) — but it exists in only 19-29% of real
   disagreement events, and even then can coincidentally align with an incorrect majority in principle
   (not observed in this corpus, but not excluded by anything in the mechanism's own logic either).
6. **How much can execution-based verification improve selection?** **Cannot be measured from this
   corpus for general production** — Tier-4's own frozen `test_code` is a research artifact, not
   something available for an arbitrary live conversational question. Within contexts that *do* have a
   real oracle (Tier-4's own harness, self-edit's F2 gate), execution-based verification is by definition
   perfectly discriminating; the open, unanswered question is how often production actually has such an
   oracle available, which is a separate, unaddressed investigation.
7. **How often should Echo refuse to choose?** This report does not recommend a specific rate — it
   reports that a strict, structure-only agreement bar would decline **81.0%/71.4%** of the time (§8), a
   number this report considers too high to act on without further evidence about the real-world cost of
   declining, and recommends the narrower §16 ranking upgrade instead of adopting blanket refusal now.
8. **Is the current fallback actually safer than preserving the candidates unchanged?** By the strict
   definition of "safer" as "never confidently wrong": **no** — preserving candidates unchanged (never
   guessing) cannot be wrong in the way a length-based guess can be, and this report found 3 concrete real
   instances of exactly that guess being wrong when a correct alternative was available. By the definition
   of "useful" as "produces one answer instead of a menu a caller must handle": the current fallback is
   more convenient, and this report does not have evidence about the real downstream cost of *not*
   choosing (§8's honest limitation).
9. **What is the smallest architectural change that materially improves disagreement resolution?**
   §16's two-stage ranking rule (structural majority, then existing RiverBrain score, then length as a
   last resort) — no new infrastructure, no new model calls, validated against the same corpus this report
   already analyzed.
10. **What evidence would falsify your recommended architecture?** Stated explicitly, as required: **if,
    on a fresh, disjoint, hash-frozen task suite, the proposed ranking rule (majority structure → RiverBrain
    score → length) does not outperform the current length-only fallback's correct-pick rate on real
    disagreement-with-a-correct-option events — or if `echo:latest`'s measured councillor unreliability in
    this corpus (53.6%) does not replicate at a comparable rate on a fresh sample — this recommendation is
    falsified.** The second condition is not a formality: this project's own Tier-4 pilot (n=8) showed a
    dramatic effect that substantially shrank on confirmation at n=84 (the Tier-4 confirmatory report's own
    central finding). The exact same regression-to-the-mean risk applies here, at a comparable single-corpus
    scale, and this report does not claim otherwise.
