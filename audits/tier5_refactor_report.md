# Tier-5: Evidence-Driven Refactor of the Synthesis Pipeline

**Mission**: repair the architectural mechanisms responsible for the information-loss patterns the
Tier-4 confirmatory experiment demonstrated (`audits/tier4_confirmatory_report.md`, n=84, hash-frozen
protocol). Verdict: **REFACTOR**, not KEEP, not RETIRE. This report documents what was found, what was
changed, what was tested, and — per the mission's own explicit demand — what still isn't proven.

**The Tier-4 experiment itself is untouched.** No frozen task suite, hash, raw result file, or
preregistered protocol was modified. Every check in this report is a new artifact, run against the real,
unmodified production code this refactor changes.

## BEFORE

`app/core/river_deliberation.py`'s `deliberate_and_learn()` — the real production mechanism behind both
Echo's live Council feature and the Tier-4 experiment's `ARCH_COUNCIL` arm — had no mechanism of any kind
for:
- Detecting that candidates already agreed before invoking a synthesis call.
- Knowing whether a candidate's code was even syntactically valid before treating it as equally
  authoritative input to synthesis.
- Checking whether the synthesis output preserved what the candidates actually said.
- Rejecting a synthesis result once produced, for any reason.

Synthesis was invoked unconditionally whenever two or more valid, non-solo opinions existed — including
when they were byte-identical — using a single, generic prompt template ("integrate the best insights
while staying true to your own voice") written for personal/creative/reasoning synthesis and applied,
unmodified, to code. The only existing acceptance check was `if not final_response or "[ERROR]" in
final_response` — a liveness check, not a correctness check.

## EVIDENCE

Tier-4's mechanism analysis (re-scoring every captured pre-synthesis response against the real sandbox,
zero new model calls) found the underlying model pool solves 95-96% of tasks when any one of several
independent attempts is allowed to count, while real synthesized output only achieves 68-80%. Two
concrete, real, unedited examples anchor this report's design:

1. **`cs09`**: three independent attempts each produced a complete, correct `ThreadSafeMultiCounter`
   class. Synthesis kept only the `if __name__ == "__main__":` demo block and dropped the class
   definition entirely — `NameError`.
2. **`bf06`**: three heterogeneous councillors produced byte-for-byte identical correct code for
   `find_missing`. Synthesis still fabricated an unsupported `- 1` that appears in none of the inputs.

Separately, `ARCH_PIPELINE_ISOLATED` (self-edit's own generation framing, applied to general coding
tasks) underperformed bare prompting by 23.81 percentage points, p=0.0002 pooled — decisive at n=84,
where the 8-task pilot found nothing (p=1.0).

## ROOT CAUSES

Traced directly against source, not assumed (full trace: prompt construction → per-councillor calls →
raw opinions → token-budgeted truncation → synthesis prompt assembly → synthesis call → liveness-only
acceptance check → downstream extraction):

- **`SYNTHESIS_SYSTEM_TEMPLATE`'s own wording** licenses rewriting ("integrate... in your own voice")
  with no preservation instruction of any kind, applied identically to code and to conversational
  content.
- **No agreement detection.** Every real synthesis call was invoked with zero regard for whether the
  candidates already agreed — the `bf06` case (byte-identical inputs) had literally nothing to
  reconcile, yet still went through an LLM rewrite step that introduced a defect.
- **No post-synthesis structural check.** The `cs09` case's failure (a dropped class definition) is
  syntactically valid Python — `ast.parse()` alone would never catch it. Nothing existed to compare the
  synthesis output's structure against what the candidates had already, verifiably agreed to define.
- **Self-edit framing (`CODE_OUTPUT_RULES` + live `self_edit_generated.py` context)**, confirmed via
  direct grep to have exactly two real call sites — `self_edit_manager.py`'s own pipeline and
  `wolf_friction_bridge.py`'s dry-run simulator, both legitimate self-edit uses. **This is not currently
  leaking into ordinary conversational coding, `echo_projects.py`, or any other general-purpose path** —
  the demonstrated harm is real but contained to its intended use; the risk is a *future* misuse, not a
  live bug today.
- **Two further, independent bugs found only during live validation of the fix itself** (see RESULTS) —
  a prose-extraction gap and a case-sensitive fence regex — neither hypothesized in advance, both
  concrete, both fixed, both disclosed in full below rather than smoothed over.

## CHANGES

All changes are additive and gated to `task_type == "coding"` — every other task type
(personal/creative/reasoning/general) is byte-for-byte unaffected; verified directly (blast-radius
regression test, below).

**`app/core/river_deliberation.py`**:
1. `SYNTHESIS_SYSTEM_TEMPLATE_CODING` — a new, coding-specific synthesis prompt, selected only for
   `task_type == "coding"`. Explicit preservation contract: preserve agreed implementations verbatim,
   never invent logic/operators/constants absent from the candidates, preserve every candidate
   definition, prefer reusing the most complete candidate over constructing something new. The original
   `SYNTHESIS_SYSTEM_TEMPLATE` is untouched, still used for every other task type.
2. `detect_full_agreement()` — pure function; if every candidate's extracted code shares an identical AST
   (whitespace/comment/quote-style independent, via `ast.dump`), the LLM synthesis call is skipped
   entirely and the agreed code is returned directly. Directly, structurally eliminates the `bf06` failure
   class: a synthesis call that never happens cannot fabricate a defect.
3. `find_missing_agreed_definitions()` — pure function; if every candidate that itself parses agrees on
   defining some function/class, and the synthesis output's own top-level definitions don't include it,
   the synthesis is rejected in favor of the best individual candidate. Directly targets the `cs09`
   failure class (a structural, checkable signal independent of runtime correctness).
4. `select_best_fallback_candidate()` — replaces the pre-existing `max(..., key=len)` fallback (used both
   for empty/errored synthesis and the new completeness-check rejection) with a preference for candidates
   whose code actually parses, breaking ties by length.
5. Structured logging (`memory/synthesis_integrity_log.jsonl`) — every coding-task synthesis decision
   records candidate/synthesis SHA-1 hashes + 200-char previews (not full text, by design — see
   REMAINING RISKS), selection method, and (on a completeness rejection) the specific per-candidate and
   synthesis top-level name sets that triggered it.

**`app/core/code_verification.py`**: `_FENCE_RE` gained `re.IGNORECASE` — a real, pre-existing bug
(confirmed via live diagnostic capture: an `echo:latest` response using `` ```Python `` with a capital P
was silently un-extractable) that also affects the already-shipped `verify_response_code()` conversational
verification path, not just the new checks that exposed it.

**`app/core/self_edit_manager.py`**: `CODE_OUTPUT_RULES` and `generate_code_from_plan()` both gained
explicit guard comments citing the Tier-4 evidence, warning against reuse for general coding tasks.
Zero behavior change — confirmed the actual `CODE_OUTPUT_RULES` string value is unchanged, comments only.

## TESTS

`scripts/verify_synthesis_refactor.py` — 20 checks, all passing, covering the mission's 7 named
regression tests plus 2 found during this pass:
- **Test 1** (complete candidate preservation): detects a dropped class, accepts a complete synthesis,
  and — added after a real bug was found — correctly does *not* flag a complete synthesis just because
  it has leading prose before its code fence.
- **Test 2** (unanimous candidate preservation): confirms `detect_full_agreement()` fires on
  byte-identical-modulo-formatting candidates.
- **Test 3** (unsupported-operation detection): confirmed via the same mechanism as Test 2 — stated
  honestly as the actual scope, not a general operation-diff (see REMAINING RISKS).
- **Test 4** (genuine disagreement): confirms real disagreement is never short-circuited, and a
  reasonable reconciliation is never falsely flagged.
- **Test 5** (passing-candidate preference): implemented as *syntactic-validity* preference, explicitly
  labeled as a narrower scope than execution-based preference — see REMAINING RISKS for why.
- **Test 6** (self-edit isolation): confirms `river_deliberation.py` never references
  `CODE_OUTPUT_RULES`/`self_edit_generated`, and `generate_code_from_plan()` has exactly one real call
  site.
- **Test 7** (no self-edit regression): confirms `CODE_OUTPUT_RULES`'s actual string content is
  byte-identical to before.
- **Test 8** (found during live validation, not planned): the capitalized-fence regex fix.
- **Blast-radius check**: `SYNTHESIS_SYSTEM_TEMPLATE`'s own text is untouched.

Both real historical failures were also directly replayed against the fixed code (not just synthetic
unit tests): `bf06`'s three real councillor responses trigger `detect_full_agreement()` and return the
correct code with **zero LLM synthesis calls made**; `cs09`'s three real attempts correctly trigger
`find_missing_agreed_definitions()` and fall back to a candidate containing the required class.

## RESULTS

**A real, honest account of what live validation found, including two bugs in the fix itself — exactly
the gap between "unit tests pass" and "the real system works" this mission explicitly warned against
papering over:**

1. First live run (5 fresh, verified, never-before-used tasks, real end-to-end `deliberate_and_learn()`
   calls): 5/5 passed, but **all 5** triggered `completeness_fallback` — every single synthesis was
   rejected. Investigating rather than accepting this at face value found a real bug:
   `find_missing_agreed_definitions()` checked the synthesis output's top-level names by calling
   `ast.parse()` on the **raw** response text, which routinely opens with prose ("Here's the final
   code:\n\n```...") that `ast.parse()` rejects outright — making every synthesis with any leading prose
   look like it defined nothing at all, regardless of what its actual code did. **Fixed**: extract the
   synthesis's own code the same way every candidate's code is already extracted, symmetric on both sides
   of the comparison as it always should have been.
2. Second live run (same 5 tasks, fix applied): 5/5 passed, `completeness_fallback` dropped from 5/5 to
   1/5. Investigating the one remaining trigger (rather than accepting a 1-in-5 residual rate as
   presumably fine) found a second, independent, pre-existing bug: `code_verification.py`'s fence regex
   was case-sensitive, so a real `echo:latest` response using `` ```Python `` (capital P) was never
   matched by `extract_python_blocks()` at all — silently returning zero blocks for a response that had
   real, correct code in it. **Fixed**: `re.IGNORECASE` added; confirmed this also benefits the
   already-shipped `verify_response_code()` path, not just the new checks.
3. Third live run (same 5 tasks, both fixes applied): **5/5 passed, 5/5 `synthesis_accepted`** — zero
   false-positive rejections, zero missed real completeness issues in this sample.
4. A separate control run (same 5 tasks, identical conditions, the new mechanisms patched to permanent
   no-ops — i.e., exact pre-refactor behavior) also scored 5/5. **Stated plainly, not spun**: this small,
   5-task validation batch cannot show a pass-rate delta, because these particular tasks are easy enough
   that raw synthesis already tends to succeed on them most of the time — the batch's real job (proving
   the live pipeline works end-to-end without exceptions, and stress-testing the new logic against real,
   messy model output) is exactly what surfaced the two bugs above. The evidence that the fix
   *mechanically* prevents the demonstrated failure modes is the direct replay of `cs09`/`bf06`, not this
   validation batch's own pass rate.

**Full regression suite**: 20/20 passing after both fixes. **Self-edit**: verified via source-level
checks only (`CODE_OUTPUT_RULES` content unchanged, single call site preserved) — a live self-edit
generation call was deliberately not run as part of this validation, given self-edit's own real
production side effects (staging writes, cooldown state); this is a scope decision, stated here rather
than silently assumed safe.

**Known failure modes eliminated, reduced, or moved?** The `bf06`-class failure (unanimous agreement,
synthesis fabricates a defect) is **eliminated by construction** — no synthesis call, no possible
fabrication. The `cs09`-class failure (agreed definition dropped) is **caught and corrected**, not
prevented at the generation stage — the underlying tendency for synthesis to sometimes drop a definition
still exists; what changed is that this refactor now detects it structurally and substitutes a working
candidate instead of returning the broken output. Nothing was *moved* to a different failure mode that
this report is aware of — the fallback path reuses the existing, already-proven "return a raw candidate"
contract every prior edge case in this function already had.

## REMAINING RISKS

Stated as plainly as the successes above, per the mission's own explicit demand:

- **Test 3/Test 5's honest scope gap**: general "unsupported-operation" detection (catching an invented
  operation *inside* an otherwise-preserved, agreed-upon function body) is only fully prevented in the
  full-agreement case. A case where candidates agree on *structure* (same function signature) but
  synthesis alters *internal logic* is not caught by `find_missing_agreed_definitions()`, which only
  compares definition names, not bodies. This is a real, disclosed limitation, not a hidden one — closing
  it would need semantic diffing, a larger change than this conservative pass attempted.
- **No true execution-based evidence ranking.** Ordinary conversational coding questions have no external
  oracle to run against (unlike the Tier-4 harness's own frozen test suites) — `select_best_fallback_candidate()`
  only ranks by syntactic validity, not correctness. `code_verification.py`'s existing self-consistency
  check (does a self-claimed example's output match reality) remains the only real execution-based signal
  available for arbitrary questions, unchanged by this refactor and not yet wired into candidate selection.
- **Logging stores hashes + 200-char previews, not full text**, a deliberate log-hygiene choice (this
  project has already been burned once by unbounded raw-text logging, per CLAUDE.md's own log-retention
  history) — but this materially slowed down diagnosing the two bugs above, requiring three separate
  targeted full-capture diagnostic calls outside the normal logging path to get ground truth. A
  time-boxed, explicitly-flagged full-text capture mode (auto-expiring, not a permanent change) would be
  a reasonable, cheap follow-up.
- **Small validation sample.** 5 tasks, one real session, one pinned model, one real council composition
  (`echo:latest`, `mlx:qwen3`, `qwen2.5-coder:7b` — the same composition Tier-4 observed as structurally
  near-deterministic given current production state). Whether the fix generalizes across a wider task
  distribution, a different council composition, or a different pinned model is not established by this
  pass.
- **The completeness check can, by construction, only ever make a candidate-fallback decision *worse or
  equal* to a hypothetically-perfect synthesis, never better** — if a real disagreement exists and the
  fallback's chosen candidate happens to be wrong in a way none of the others were, this refactor has no
  way to know that (it has no oracle either). This is the same honest limitation named in Tier-4's own
  report for `select_best_fallback_candidate`'s syntactic-only preference.
- **Self-edit's own live functioning was not re-verified end-to-end** in this pass (see RESULTS) — the
  guard comments are confirmed zero-behavior-change, but a real `generate_code_from_plan()` call through
  the full self-edit pipeline was not exercised.

## NEXT EXPERIMENT

The smallest scientifically useful experiment to determine whether this refactor genuinely improves
reliability, not just passes its own tests:

**A third, fresh, disjoint, hash-frozen 20-30 task suite** (mirroring Tier-4's own discipline exactly —
authored and verified before any run, never reused from the pilot, Tier-4's 84, or this pass's 5
validation tasks), run twice under identical real conditions: once with the refactor active, once with
`detect_full_agreement`/`find_missing_agreed_definitions` patched to no-ops (the exact control-run
pattern already built in `scripts/verify_synthesis_refactor_control.py`, reused rather than
reinvented). Primary endpoint: paired McNemar comparison of the two conditions' pass rates on the
*identical* tasks — note this requires accepting that each condition's *generation* is still a fresh,
independent real API call (council composition and candidate text are not literally frozen the way
Tier-4's own historical records are), so this is a fair head-to-head rerun, not a replay. Secondary
endpoint: the real `completeness_fallback`/`full_agreement_shortcut` trigger rate on a larger, more
diverse sample than this pass's 5 tasks — directly answering whether the fix's benefit holds up, and how
often each mechanism actually engages, at a scale this report cannot claim on its own.

## EVIDENCE PRESERVATION

- Tier-4's frozen protocol, task suites, and raw results — untouched.
- `memory/synthesis_integrity_log.jsonl` — new, real, live data from every validation run in this pass,
  left in place as part of the record.
- `scripts/verify_synthesis_refactor.py`, `scripts/verify_synthesis_refactor_live.py`,
  `scripts/verify_synthesis_refactor_control.py` — new, reusable verification artifacts, not one-off
  scratch scripts.
- This document and its JSON companion are new artifacts, clearly distinct from the Tier-4 confirmatory
  report.
