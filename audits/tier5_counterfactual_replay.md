# Tier-5 Counterfactual Replay & Forensic Audit

**Method discipline**: this entire investigation is a deterministic replay against already-captured Tier-4
data plus real (but non-generative) sandbox re-execution of already-existing candidate code. **Zero new
LLM/model calls were made.** No Tier-4 artifact (raw results, task suites, hashes, protocol) or existing
audit report was modified. The one new script this analysis required
(`scripts/tier5_counterfactual_replay.py`) is a clearly isolated, read-only forensic tool that imports the
real, unmodified `app/core/river_deliberation.py` functions directly — it does not reimplement or
approximate them.

## 1. Executive Verdict

**Partially supported, with one significant terminology correction, one significant scope correction, and
one newly-discovered real weakness that was not previously identified.** The deterministic replay across
the complete 168-event Tier-4 coding corpus (84 `ARCH_COUNCIL` + 84 `BASE_N`) independently confirms the
Tier-5 report's two headline claims (`cs09`, `bf06`) exactly as described, and finds **zero regressions**
anywhere in the full corpus — real, meaningful, reassuring evidence the refactor is not simply trading one
failure mode for another. But the replay also finds the net effect is modest (+3.6pp / +6.0pp, not a
dramatic fix), that `find_missing_agreed_definitions()` alone (without the agreement shortcut) would *not*
have caught `bf06`'s specific bug, and — the most important new finding — that `select_best_fallback_candidate()`
picked the **minority-wrong** candidate over available majority-correct alternatives in **all three**
checked cases where the completeness check fired without net benefit. This last finding was not
identified in the original Tier-5 report and materially changes the GO/NO-GO recommendation.

## 2. Data Inventory

Exactly which Tier-4 artifacts were replayed, and how:

- `audits/tier4_apparatus/stage1_results.jsonl`, `stage2_results.jsonl` — all 336 raw records; the 168
  `ARCH_COUNCIL`/`BASE_N` records' `mechanism_calls` (full per-call model + response text, already
  captured during the original Tier-4 execution, never regenerated) are the entire input to this replay.
  `BASE_1`/`ARCH_PIPELINE_ISOLATED` records were excluded — both are single-call, no-synthesis arms with
  no candidates to replay agreement/completeness detection against.
- `audits/tier4_apparatus/tier4_stage1_task_suite.json`, `tier4_stage2_task_suite.json` — the real,
  frozen `test_code` for every task, used as the historical evaluator via the same `objective_verify()`
  function the original Tier-4 scoring used. No new correctness criterion was invented.
- `app/core/river_deliberation.py` — `detect_full_agreement()`, `find_missing_agreed_definitions()`,
  `select_best_fallback_candidate()`, `_extract_candidate_code()`, `_ast_normalize()`,
  `_extract_top_level_names()` — imported and called directly, not reimplemented.
- `memory/synthesis_integrity_log.jsonl` — inspected (real data from the live-validation runs in the
  Tier-5 refactor itself, 5 tasks, not Tier-4 data) but **not** used as replay input — it postdates Tier-4
  and reflects a different, smaller task set. Its role here was confirming which files hold live Tier-5
  telemetry, per this mission's own "map exactly where the records live" instruction.
- **Methodology caveat, stated explicitly per this project's own established discipline**: real production
  `deliberate_and_learn()` builds its `opinions` dict keyed by bare model name. `ARCH_COUNCIL`'s real
  observed composition (`qwen2.5-coder:7b`, `mlx:qwen3`, `echo:latest`) never repeats a model within one
  council, so this replay uses bare model-name keys for `ARCH_COUNCIL`, exactly matching production. `BASE_N`
  is a harness-only construct with **no real production analog** — its 3 attempts share one model name, so a
  literal bare-model-name dict would silently collapse 3 entries into 1. This replay uses index-qualified
  keys (`f"{model}#{i}"`) for `BASE_N` specifically to avoid losing data, and every `BASE_N` result in this
  report is labeled **secondary / not a literal production analog** — `ARCH_COUNCIL` is primary throughout.

## 3. Historical vs Counterfactual Results

| Metric | Historical Tier-4 (`ARCH_COUNCIL`) | Tier-5 Counterfactual (`ARCH_COUNCIL`) | Historical (`BASE_N`, secondary) | Counterfactual (`BASE_N`, secondary) |
|---|---:|---:|---:|---:|
| Tasks | 84 | 84 | 84 | 84 |
| Passes | 57 (67.9%) | 60 (71.4%) | 67 (79.8%) | 72 (85.7%) |
| Failures | 27 | 24 | 17 | 12 |
| Agreement shortcuts fired | n/a | 4 (4.8%) | n/a | 6 (7.1%) |
| Completeness fallbacks fired | n/a | 3 (3.6%) | n/a | 6 (7.1%) |
| Failures intercepted (FAIL→PASS) | — | **3** | — | **5** |
| Regressions (PASS→FAIL) | — | **0** | — | **0** |
| Net pass-rate change | — | **+3.6pp** | — | **+6.0pp** |

Full breakdown by counterfactual path × outcome (both arms, confirmed by direct count, not estimated):

| Path | Outcome | `ARCH_COUNCIL` | `BASE_N` (secondary) |
|---|---|---:|---:|
| `full_agreement_shortcut` | failure_intercepted | 2 | 1 |
| `full_agreement_shortcut` | unchanged_pass | 2 | 4 |
| `full_agreement_shortcut` | unchanged_fail | 0 | 1 |
| `completeness_fallback` | failure_intercepted | 1 | 4 |
| `completeness_fallback` | unchanged_fail | 2 | 2 |
| `synthesis_accepted_unchanged` | unchanged_pass | 55 | 63 |
| `synthesis_accepted_unchanged` | unchanged_fail | 22 | 9 |

91.7% (`ARCH_COUNCIL`) / 85.7% (`BASE_N`) of all real historical events are **completely untouched** by
either new mechanism — the refactor is narrow in scope by construction, exactly as its own "conservative"
framing claimed, though see §9 for how far that word can honestly be stretched.

## 4. Failure Interception

Every historical failure the refactor would have prevented or corrected, independently re-verified:

| Task | Arm | Path | Detail |
|---|---|---|---|
| `bf03` (s1) | `ARCH_COUNCIL` | agreement shortcut | 3/3 candidates named `first_occurrence`, AST-identical |
| `bf06` (s2) | `ARCH_COUNCIL` | agreement shortcut | **The headline case** — 3/3 byte-identical, confirmed below (§7) |
| `dt09` (s1) | `ARCH_COUNCIL` | completeness fallback | 2/3 candidates defined `interleave_lists`; historical synthesis defined nothing |
| `bf03` (s1) | `BASE_N` (secondary) | agreement shortcut | Same task, same pattern, same-model attempts |
| `cs09` (s1) | `BASE_N` (secondary) | completeness fallback | **The headline case** — confirmed below (§6) |
| `dt07` (s1) | `BASE_N` (secondary) | completeness fallback | 1/3 candidates defined `rows_to_dicts`; synthesis defined nothing |
| `iv05` (s1) | `BASE_N` (secondary) | completeness fallback | 2/3 candidates defined `normalize_whitespace` (1 candidate failed to parse); synthesis defined nothing |
| `ae08` (s2) | `BASE_N` (secondary) | completeness fallback | 2/3 candidates defined `zero_matrix`; synthesis defined nothing |

Notably, in **every single completeness-fallback interception** (`dt09`, `cs09`, `dt07`, `iv05`, `ae08`),
the historical synthesis's own extracted code parsed successfully but defined **zero** top-level names —
i.e., the historical synthesis wasn't merely "incomplete," it was structurally empty of any real
definition despite `ast.parse()` succeeding on it (plausibly a bare expression, a comment-only body after
extraction, or similar degenerate-but-valid output). This is a more extreme, more clearly clear-cut
failure signature than the `cs09` write-up in the original Tier-5 report characterized generically as
"dropped a definition" — the real pattern found across the corpus is closer to "dropped *every*
definition."

## 5. False Positives / Regressions

**Zero regressions were found anywhere in the 168-event corpus** — directly counted, not estimated. No
historical PASS became a counterfactual FAIL under either mechanism, in either arm.

However, three real, concrete cases were found where a mechanism fired **without net benefit** — and
investigating *why* surfaced the most important new finding of this audit:

| Task | Arm | Path fired | Chosen candidate's own result | Un-chosen alternatives |
|---|---|---|---|---|
| `bf10` (s2) | `ARCH_COUNCIL` | completeness fallback | `mlx:qwen3` chosen — **would fail alone** | `qwen2.5-coder:7b` and `echo:latest` — **both would pass alone** |
| `rf02` (s2) | `ARCH_COUNCIL` | completeness fallback | `echo:latest` chosen — **would fail alone** | `qwen2.5-coder:7b` and `mlx:qwen3` — **both would pass alone** |
| `ae02` (s2) | `BASE_N` (secondary) | completeness fallback | attempt #0 chosen — **would fail alone** | attempts #1 and #2 — **both would pass alone** |

**In all three checked cases, `select_best_fallback_candidate()` selected the one wrong candidate out of
three, when two of the three available candidates were independently verified correct.** This is not a
regression (the historical synthesis was already failing in all three cases, so the outcome is
`unchanged_fail`, not `PASS→FAIL`) — but it is a real, concrete, previously-undocumented demonstration
that the fallback's "parses, then longest raw response" heuristic is not merely "narrower than
execution-based evidence" (already disclosed in the Tier-5 report) but **actively anti-correlated with
correctness often enough to matter** in the small sample where it was checkable. A majority-vote-style
heuristic (prefer whichever candidate structurally resembles the most other candidates) would very likely
have intercepted all three of these as additional failures fixed — a concrete, low-cost improvement
opportunity, not identified in the original report.

There were also 4 `full_agreement_shortcut` events with outcome `unchanged_pass` or `unchanged_fail`
(both arms) — these are cases where all candidates genuinely agreed and the shared code was already
correct (safe, expected) or, in one `BASE_N` case (`rf12`, s2), all three candidates unanimously shared
the **same bug** (`digit_sums`) — confirming, with a real example, the theoretical risk named in this
audit's Phase 1 analysis: unanimous agreement on a wrong answer is preserved, not fixed, by the shortcut.
This is not a regression (the historical result was already wrong) and not something synthesis itself
was ever shown capable of fixing either (Tier-4's own mechanism analysis found synthesis "rescues" a
fully-wrong candidate set only 1 time in 84 real `ARCH_COUNCIL` events) — but it is a real, confirmed
instance of a named blind spot, not a hypothetical one.

## 6. cs09 Replay (independent re-verification)

Fresh, independent replay against the real `BASE_N` record for `cs09` (stage 1) — not citing the original
Tier-5 report's own prior claims:

- All 3 real attempts' extracted code parses successfully and each independently defines exactly
  `{'ThreadSafeMultiCounter'}` at the top level. **Confirmed.**
- The historical synthesis's own raw response, when extracted the same way, parses successfully but
  defines **zero** top-level names. **Confirmed** — the class was not merely shortened or altered, it is
  entirely absent from the synthesis's own extractable code.
- `find_missing_agreed_definitions(opinions, historical_synthesis_text)` returns `{'ThreadSafeMultiCounter'}`
  — fires correctly. **Confirmed.**
- `select_best_fallback_candidate()` selects one of the three attempts (all three parse and are of similar
  length; the mechanism does not need to discriminate between them here, unlike §5's cases, since all three
  actually contain the required class).
- The selected candidate, independently re-verified via `objective_verify()` against the real, frozen
  `test_code`, **passes**. **Confirmed**, matching the report's claim exactly.

**No inaccuracy found in the original report's description of this case.**

## 7. bf06 Replay (independent re-verification)

Fresh, independent replay against the real `ARCH_COUNCIL` record for `bf06` (stage 2):

- All three real councillor responses (`qwen2.5-coder:7b`, `mlx:qwen3`, `echo:latest`), independently
  extracted, are **byte-for-byte identical** (not merely AST-identical) — confirmed by direct string
  comparison during this replay, a stronger confirmation than AST-equality alone. **Confirmed.**
- `detect_full_agreement()` fires and returns this shared code. **Confirmed.**
- With the shortcut firing, `deliberate_and_learn()`'s real source (re-read directly, not assumed) returns
  `agreed_code` on the very next line with **zero** further processing inside the function — no synthesis
  call is made. **Confirmed: the historical fabricated `- 1` categorically cannot occur, because the code
  path that could have introduced it is never reached.**
- **Additional check this audit performed, beyond the original report**: is there any *downstream*
  transformation (outside `deliberate_and_learn()` itself) that could still alter the agreed candidate
  before it's finally used? Traced directly: `base_pilot.clean_code()` (the harness-level extraction every
  candidate is passed through for scoring, and the closest analog to whatever a real caller does with
  `deliberate_and_learn()`'s return value) applied to the agreed code is confirmed **byte-for-byte
  identical** to the agreed code itself — a verified no-op on already-clean extracted code, not assumed.
  **No other transformation point exists between `detect_full_agreement()`'s return and final use.**

**No inaccuracy found in the original report's description of this case — this is the one claim in the
Tier-5 report that survives this audit with the least qualification.**

## 8. Remaining Blind Spots

Confirmed, with concrete real-world instances where possible, not just theorized:

- **Body-level mutation inside a preserved definition is completely invisible to
  `find_missing_agreed_definitions()`.** This is not merely a theoretical gap — direct analysis of the
  function's own logic (§Phase 1 of this audit) shows it **could not have caught `bf06`'s specific
  fabricated `- 1` on its own**, since the function name `find_missing` would have remained present in
  both the agreed set and the (hypothetical) accepted synthesis. `bf06` is fixed **entirely** by
  `detect_full_agreement()`; the completeness check provides **zero** protection against this exact
  failure shape once synthesis is actually invoked.
- **Fallback selection is anti-correlated with correctness often enough to matter** (§5) — not a narrow,
  rare edge case; 3 for 3 in the checked sample.
- **Decorators, imports, module-level constants, and nested/class-method definitions** are entirely
  outside what `_extract_top_level_names()` tracks (only `FunctionDef`/`AsyncFunctionDef`/`ClassDef` at
  `tree.body`'s direct level). No real historical instance of this specific gap being exploited was found
  in the corpus, but none was specifically searched for either (no historical event in this dataset
  happens to exercise decorators/constants distinctly from a definition) — **INDETERMINATE** whether this
  matters in practice at this project's real task distribution; flagged, not confirmed either way.
- **Unanimous agreement on a shared bug** — confirmed real (`rf12`), not just theoretical, and correctly
  understood as "no worse than before," not "made worse."
- **The completeness check's "agreement" is not literally unanimous 3-of-3.** `find_missing_agreed_definitions()`
  only requires agreement among candidates that *themselves* define something (`if names:` filters out
  parse failures and empty-definition candidates before intersecting) — confirmed via direct code read and
  via `iv05`'s real data (2 of 3 candidates agreed, 1 failed to parse, and the check still correctly fired
  off the 2 that did). This is more permissive than "unanimous," a real, worth-noting design detail, though
  not itself demonstrated to be a source of any false positive in this corpus.

## 9. Claim Audit

- **"Eliminated by construction" (bf06-class failures)** — **SUPPORTED.** Directly re-verified in §7,
  including the additional downstream-transformation check the original report did not perform. This is
  the single most solidly-supported claim in the Tier-5 report.
- **"Caught and corrected" (cs09-class failures)** — **PARTIALLY SUPPORTED.** True for the specific `cs09`
  case and the 4 other completeness-fallback interceptions found in this replay (§4). But "caught and
  corrected" implies the correction reliably produces a *good* outcome — §5's finding (3/3 checked
  "fired, no benefit" cases had the fallback pick a wrong candidate over available correct ones) shows the
  "corrected" half is considerably less reliable than the phrase implies on its own. More precise wording:
  "caught reliably; corrected only when the fallback selection heuristic happens to land on a correct
  candidate, which this audit found is not guaranteed even when a correct candidate is available."
- **"Information loss" (Tier-4's original characterization)** — **PARTIALLY SUPPORTED, with an important
  precision.** `cs09` (a definition entirely absent from output that was present in every input) is
  accurately "information loss." `bf06` (a fabricated `- 1` present in *no* input) is **not** information
  loss — nothing was lost, something was *added* that wasn't there. The Tier-4/Tier-5 reports' own text
  already uses "unsupported mutation"/"fabrication" for `bf06` specifically and "information loss" more
  for the general pattern — this audit confirms that distinction is real and should be preserved
  explicitly rather than collapsed into one umbrella term: the strongest accurate statement is
  **"candidate-to-final degradation, comprising at least two distinct mechanisms: definitional omission
  (bf06's opposite, cs09's shape) and unsupported fabrication (bf06's shape) — not a single phenomenon."**
- **"The underlying model pool solves 95-96% of tasks"** — **OVERSTATED as commonly read, SUPPORTED as a
  narrower technical claim.** This audit independently computed the true **per-individual-attempt** pass
  rate directly from the same corpus: **75.0%** (`ARCH_COUNCIL` councillors, 189/252 real individual
  responses) and **84.1%** (`BASE_N` attempts, 212/252) — both substantially below 95-96%. The 95-96%
  figure is real and correctly computed, but it is a **best-of-3 / at-least-one-of-3 success rate**, a
  fundamentally different and more optimistic quantity than "the model solves X% of tasks" would suggest
  to a reader unfamiliar with the oracle construction. **Recommended exact wording for the forensic
  record: "best-of-3 candidate solvability" or "at-least-one-of-3 success rate," always stated alongside
  the true per-attempt rate (75-84%) for context — never "model capability" or "the model solves" without
  that qualifier.**
- **"Byte-for-byte unaffected" (non-coding task types)** — **SUPPORTED as literally worded, but
  incomplete.** Directly verified: `SYNTHESIS_SYSTEM_TEMPLATE` (non-coding synthesis) is untouched, and
  `deliberate_and_learn()`'s new logic is fully gated on `task_type == "coding"`. However, the claim sits
  immediately next to a disclosed change (`_FENCE_RE` gaining `re.IGNORECASE`) that is a **shared,
  global** regex used by a **second, independent, already-shipped coding-task feature**
  (`verify_response_code()`, called from `routes_echo_studio.py:227`, itself gated on
  `task_type == "coding"` — confirmed by direct source read). The literal claim (personal/creative/
  reasoning/general are unaffected) holds. What it does not make explicit is that a real, live,
  **pre-existing** coding-task feature unrelated to synthesis also changes behavior as a side effect of
  the same shared bug fix — confirmed **beneficial** (previously-silent extraction failures on a
  capitalized fence now correctly succeed; the function's own fail-open design means this can only add
  correctly-caught cases, never remove protection) but not previously scoped out loud. **Recommended
  wording: "every non-coding task type is byte-for-byte unaffected; a second, unrelated coding-task
  feature (`verify_response_code()`) also benefits from the shared fence-regex fix, confirmed
  beneficial, not risky."**
- **"Conservative refactor"** — **PARTIALLY SUPPORTED.** Strongly supported by the zero-regression finding
  across the full 168-event deterministic replay (a real, not estimated, result) and the strict
  `task_type == "coding"` gating. Weakened by §5's fallback-selection finding: a mechanism whose corrective
  branch picks the wrong available candidate 3 times out of 3 checked opportunities is a real quality gap
  in an otherwise low-risk design, not merely "narrower than ideal." **"Conservative" is an accurate
  description of the mechanism's *blast radius* (gated, fails safe, zero regressions found); it is not an
  accurate description of the fallback's *selection quality*, which this audit found to be weak.**

## 10. Self-Edit Isolation Audit

Source-level result, no self-edit run:

- `CODE_OUTPUT_RULES`: exactly 2 real call sites confirmed via grep excluding comment lines —
  `self_edit_manager.py`'s own `generate_code_from_plan()` (line ~1922, its only invocation site within
  that file) and `wolf_friction_bridge.py`. Both pre-date this refactor and are its intended, legitimate
  uses.
- `generate_code_from_plan()`: 1 definition, 1 real call site inside `self_edit_manager.py` (confirmed by
  this project's own regression test, `Test6`, itself independently re-verified during this audit by
  direct grep), plus `wolf_friction_bridge.py`'s external call.
- `self_edit_generated.py`: referenced only inside `self_edit_manager.py`'s own prompt-construction logic;
  `river_deliberation.py` contains zero references to it (confirmed directly, both by this audit's own
  grep and by `Test6` in the regression suite).
- `SYNTHESIS_SYSTEM_TEMPLATE_CODING`: defined and used only inside `river_deliberation.py`, gated on
  `task_type == "coding"`; contains no reference to `CODE_OUTPUT_RULES` or self-edit-specific content of
  any kind.

**Direct answer to the mission's specific question**: *if someone accidentally reused `CODE_OUTPUT_RULES`
tomorrow, would the architecture stop them, or would the comment merely warn them?* **The comment would
merely warn them.** There is no import guard, no runtime assertion, no linter rule, and — critically — no
automated, continuous check (unlike this project's own established pattern for comparable structural
guarantees, e.g. the Liveness Ledger's `wolf_friction_bridge`/`dissent_log_hook`/`echo_projects_isolation`
checks, which re-verify their respective invariants every ~120 seconds via the live introspection cycle).
The regression suite's `Test6` provides a **narrow, manual, single-file check** — it would catch a *second
call site added inside* `self_edit_manager.py`, but it does **not** run automatically, and it would **not**
catch a brand-new file elsewhere in the codebase importing `CODE_OUTPUT_RULES` directly, since it only
greps within `self_edit_manager.py` and `river_deliberation.py`. **This is documentation plus a narrow
regression test, not architectural enforcement.**

## 11. Recommended Next Experiment

**The proposed two-arm design (OLD vs. FULL) is insufficient** to answer a question this audit's own
Phase 1/§7 findings make sharp: the two demonstrated fixes (`cs09`, `bf06`) are attributable **entirely**
to the mechanical safeguards, with **zero** dependence on the new coding-specific synthesis prompt (the
agreement shortcut never invokes synthesis at all; the completeness check operates on the *historical*
synthesis text, produced under the *old* prompt, in every real interception found in this replay). This
means the new prompt's own marginal contribution is **completely untested** by anything in this audit or
the original Tier-5 report — it could be zero, positive, or mildly negative, and a two-arm OLD-vs-FULL
design cannot distinguish "the prompt helped" from "the mechanical checks did all the work and the prompt
is inert or even mildly counterproductive."

**Recommend the three-arm design (OLD / PROMPT_ONLY / FULL), with one efficiency refinement this audit
identifies that the original proposal did not**: candidate *generation* (the real, expensive 3-councillor
calls) is identical across all three arms — nothing about `PROMPT_ONLY` or `FULL` changes what the
councillors are asked or how they're selected, only what happens to their output afterward. **Generate
each task's 3 councillor candidates exactly once, then run three independent synthesis calls against that
same frozen candidate set** (old template + no mechanical checks; new template + no mechanical checks;
new template + mechanical checks) rather than three independent end-to-end pipelines. This removes
candidate-generation variance as a confound between arms (a real methodological improvement, not just a
cost saving) **and** reduces the real new-model-call cost from 3× a full pipeline to 1× generation + 3×
one cheap synthesis call per task — a substantial, well-justified reduction, not assumed without reason.

## 12. Sample Size Recommendation

**The original 20-30 task proposal is a substantial underestimate, and this audit's own observed data
shows why by how much.** McNemar power depends on the rate of *outcome-changing* (discordant-eligible)
events, not the total task count — and this replay directly measured that rate at **3.6%** (`ARCH_COUNCIL`,
3/84) and **6.0%** (`BASE_N`, 5/84). Using the same power methodology the Tier-4 protocol itself
established (exact McNemar sign-test approximation, α=0.05, 80% power), the total N required to detect
the effect **at the rate actually observed** ranges from:

| Assumed true split among discordant pairs | Required total N (`ARCH_COUNCIL` rate, 3.6%) | Required total N (`BASE_N` rate, 6.0%) |
|---|---:|---:|
| 100:0 (matches the zero-regression finding exactly) | ~185 | ~111 |
| 90:10 | ~266 | ~159 |
| 80:20 (the Tier-4 protocol's own conservative default assumption) | ~539 | ~324 |

A 20-30 task sample would be expected to produce **1-2 discordant-eligible events total** — nowhere near
enough for any formal statistical conclusion in either direction. This is not a criticism of the original
proposal's intent, only of its scale: 20-30 tasks is the right size for a *directional/qualitative* check
(does the sign stay consistent, does the zero-regression finding hold up further), not for a
*confirmatory, significance-bearing* one.

**Recommendation, matching "smallest sample that can answer the actual question with useful confidence"
rather than maximum size**: run the three-arm design at **40-60 tasks** as a practical, directional
checkpoint (large enough to plausibly observe several more real discordant events and continue stress-
testing for regressions at higher confidence than this replay's own 168-event, 0-observed rate already
provides — a rule-of-three approximation on 0/168 puts the true regression rate's upper 95% bound at
roughly 1.8%, worth tightening further before treating "zero regressions" as settled) — explicitly
reported as directional, not treated as a significance test. **If a genuine, formally powered confirmatory
answer is wanted, budget for 150-300+ tasks** (nearer the `ARCH_COUNCIL`-rate end of the table above, since
that is the real production analog) and treat that as a separate, larger, deliberately-scoped follow-up
decision — not a default extension of this pass.

## 13. Final GO/NO-GO

**GO WITH MODIFICATIONS.**

Evidence for GO: zero regressions across a complete, deterministic 168-event replay (not a sample — the
entire available corpus); both headline mechanisms (`detect_full_agreement`, `find_missing_agreed_definitions`)
independently re-confirmed to work exactly as described for their two demonstrated cases; a real, modest,
consistently-positive net effect in both arms.

Evidence for WITH MODIFICATIONS, not a clean GO: `select_best_fallback_candidate()`'s length-based
heuristic picked the wrong candidate in 3 of 3 checked opportunities where a correct alternative was
available — a concrete, low-cost, well-evidenced improvement (a majority-structural-similarity heuristic,
or at minimum breaking ties by which candidate most resembles the others, rather than raw length) should
be made **before** spending real compute on a confirmatory experiment, since running that experiment
against a known-suboptimal fallback would understate the refactor's real achievable benefit and complicate
interpretation of whatever result comes back. This is a cheap, deterministic, no-new-model-call fix to
validate (the same replay corpus this audit already built can re-score it for free) — there is no reason
to defer it to a later pass.

Not NO-GO: nothing in this audit found the refactor unsafe, regressive, or built on a false premise — the
core, demonstrated mechanism (agreement-based synthesis skipping) is confirmed sound and its one clean
headline case (`bf06`) survives the most adversarial re-check this audit could construct.
