# VSL Final Pre-Merge Adversarial Gate

**This is a falsification mission, not a development mission.** The goal was to try to
break the bounded claim under test, not to confirm it. Nothing in `vsl-implementation`
was redesigned, expanded, or integrated further during this gate.

## Bounded claim under test

> VSL is a reversible production consumer of already-qualified skills. It does not
> autonomously acquire new production skills, does not bypass F1/F2, does not allow
> inactive skills to affect production behavior, does not execute skill-file contents
> as arbitrary code, and can be disabled to restore pre-VSL behavior.

## Phase 0 — ground truth (re-confirmed directly, not assumed)

- Branch: `vsl-implementation`. HEAD at gate start: `04bb72b6043df871e2f9f5dc7db39fadb551721f`.
- `main`: `2fba42644c82b9f7096276f4dd338d615cf1bcce`, confirmed untouched at gate start
  and re-confirmed at gate end.
- Working tree: clean for VSL scope at gate start, and re-confirmed clean at gate end —
  every adversarial artifact (scratch skill directories, temp marker files, an isolated
  copy of the production skill store) was created under `/tmp`, a local
  `.claude_scratch_vsl_gate/` (deleted), or `tempfile.TemporaryDirectory()`, never in
  the real repository or `memory/skill_ledger/`.
- Baseline suites, re-run before adversarial work began: `scripts/verify_skill_ledger_integration.py`
  → 34/34; `app/experiments/skill_ledger/verify_diff_extract.py` → 15/15. Both exactly
  matched the readiness report's claimed baseline — no discrepancy, proceeded.
- Real production Skill A: `K2.T5.tag_priority_direction` v4, `ACTIVE`, content_hash
  `95de89e132a81e2fc856fee453393b680c832f5a4c951cebbd97288cd68e7627` — confirmed at gate
  start and re-confirmed unchanged at gate end, despite extensive adversarial testing
  in between (every destructive test used an isolated scratch copy, never the real file).
- `VSL_ENABLED` confirmed unset/disabled by default in a genuinely fresh subprocess
  with no inherited environment override.

## Adversarial Boundary A — stale objects and lifecycle resurrection

**A1 (write-once collision backstop): PASS.** Confirmed the backstop holds even when a
stale in-memory `Skill` reference is *multiple* real transitions behind current disk
state (advanced v4→v5→v6 via two separate fresh loads; a stale v4 object's further
transition attempt still collided with the already-claimed v5 file, `FileExistsError`,
not silent corruption).

**A2 (NEW FINDING, this gate): direct-construction bypass of every `promote_to_*` guard.**
A `schemas.Skill` object constructed directly with an explicit `lifecycle_state="ACTIVE"`
kwarg and saved via `.save_new_version()` completely bypasses `promote_to_verified()`/
`promote_to_qualified()`/`promote_to_active()`'s state guards, since those guards live
inside the methods, not in `Skill.__init__`/`save_new_version()` themselves.
**Demonstrated**: a genuinely `RETIRED` skill (real evidence-gated history: CANDIDATE →
[fabricated retirement for the test]) was resurrected to `ACTIVE` via direct
construction with zero real promotion evidence. **Production-reachability, checked
directly**: `grep -rn "Skill(" app/core/skill_ledger/runtime.py app/core/skill_ledger/echo_adapter.py app/core/echo_projects.py`
returns zero matches — no currently-wired production code path constructs a `Skill`
object at all; the only real production interaction with the store is reading
(`consult()`/`_list_active_feature_keys()`) and the guarded transition methods
(`evaluate_degradation()`'s call to `skill.mark_degraded()`). **Classification: demonstrated
defect, NOT demonstrated production-reachable** through any code path that exists today.

**Consult() cache-freshness (PASS)**: verified directly that `runtime.consult()` never
caches or accepts a pre-loaded `Skill` object — it calls `Skill.load_latest()` fresh
internally on every single invocation. A real skill quarantined via a fresh load between
two `consult()` calls is correctly excluded on the second call, with zero staleness
window.

## Adversarial Boundary B — hostile/corrupted ledger content

**Comprehensive hostile-payload battery against the post-fix `_rehydrate()`/
`_validate_and_build()`: 18/18 hostile payloads correctly rejected** (attribute access,
nested attribute+subscript, comprehensions, lambdas, arbitrary non-`ast` calls, starred
args, unknown/impostor class names, dict/set literals, binary ops, f-strings, ternaries,
undefined names, unsafe calls nested inside an otherwise-allowed shape, `**kwargs`
expansion, generator expressions, `await`) — zero code execution, zero side effects,
zero uncaught exceptions in any case.

**Sub-finding (documented, not a new gap)**: `ast.AST.__init__` itself silently accepts
arbitrary/missing keyword field names (confirmed directly: `ast.Constant(bogus_field=1)`
constructs without error, producing an object with no `.value` attribute).
`_validate_and_build()` validates *shape* (real class name, keyword-only args,
primitive/list values) but not *field completeness*. **Verified this does not escape as
an uncaught exception through the real production path**: replayed a
malformed-required-field transformation through the actual `matcher.apply_skill()` entry
point — it returns a clean `None`, because the pre-existing `ast.unparse()` try/except in
`_replace_and_unparse()` (not the new validator) catches the resulting `AttributeError`
one layer downstream. This is safe *as a layered interaction*, but worth recording
precisely: the new validator alone would not be sufficient without that pre-existing
downstream guard.

**Malformed JSON files through `Skill.load()`**: truncated JSON and missing-required-keys
both raise cleanly (`JSONDecodeError`/`KeyError`) — these are exactly the exceptions
Integration Commit 6's fix wraps at the `runtime.py` caller level (re-confirmed: a
corrupted file sorting *before* a valid `ACTIVE` skill in the same directory does not
block the valid skill from being found and applied — Boundary E's corrupted-candidate
test, below).

**Deeply nested structures**: a 200-level nested `UnaryOp` chain reconstructs correctly
in under 2ms — no pathological slowdown, no recursion error at this depth.

## Adversarial Boundary C — feature flag / mode transitions

**Flag/mode parsing battery**: 12 cases tested; all 3 apparent "mismatches" against my
own initial expectations turned out to be *my* expectations being wrong, not bugs — the
code's case-insensitive (`'True'`, `'ACTIVE'`) and whitespace-tolerant (`'true '`)
handling is intentional and documented, and every genuinely invalid value (`'yes'`,
`'1'`, `''`, `'yolo'`) correctly fails closed to `disabled`. **PASS.**

**Shadow-mode leak, tested through the FULL real production path** (`app.core.echo_projects.generate_project()`,
not just the `runtime.consult()` helper): a real buggy candidate, run in shadow mode
through the actual pipeline, produces a staged file on disk that **still contains the
original bug** — shadow's computed patch never reaches the real artifact F1/F2 operate
on. **PASS**, verified at the production entry point, not a helper.

**Mid-process mode changes**: re-confirmed (from the existing integration suite plus a
fresh check this gate) that switching `VSL_MODE` between calls within one process is
reflected immediately on the next `consult()` call — no cached mode state anywhere.

## Adversarial Boundary D — terminal and non-ACTIVE lifecycle exclusion

**Legacy-field vs. explicit-`lifecycle_state` authority, tested directly**:
`effective_lifecycle()` gives `lifecycle_state`, when present, **unconditional priority**
over the legacy `status`/`held_out_verdict` fields, in *either* direction — confirmed
with three constructed cases: legacy-implies-QUALIFIED + explicit QUARANTINED →
correctly resolves to the safer QUARANTINED; legacy-implies-RETIRED + explicit ACTIVE →
resolves to ACTIVE (the less safe direction); no explicit state → correctly falls back
to legacy derivation.

**This generalizes directly into a second new finding (related to A2), this gate's most
significant:**

**Finding X: `effective_lifecycle()` trusts a persisted `lifecycle_state` field
completely, with no validation that the value is a real `LIFECYCLE_STATES` member and no
cross-check against the legacy evidence fields sitting in the same record.**
**Demonstrated directly through the real production path, not just the schema layer**: a
hand-constructed skill file with `status="candidate"`, `held_out_verdict=None` (legacy
fields honestly show it was never verified) but `"lifecycle_state": "ACTIVE"` set
directly is listed by `runtime._list_active_feature_keys()` and **successfully consumed
and applied** by `runtime.consult()` against real buggy code — the real, wired
production API, not a bypassed internal.

**Reachability, assessed precisely**: this is real, and the trusting code IS the actual
production `consult()`/`_list_active_feature_keys()` path — but *producing* the
corrupted input requires either (a) filesystem-level tampering with
`memory/skill_ledger/skills/*.json` (outside any code path this integration controls),
or (b) Finding Y/A2's direct-construction bypass, which — as established above — no
current, wired production code path exercises. **This is the load-bearing question for
the final verdict**: the *read side*'s trust is unconditional and real; the *write side*
currently has no path that would ever produce an untrustworthy value. Whether that
combination should block merge is addressed in the Verdict section below, after the
independent reviewer's own assessment.

## Adversarial Boundary E — conflicts and multiple skills

Constructed two genuine `ACTIVE` skills (`AAA.first`, `ZZZ.second`) both matching the
same precondition on the same candidate function, plus a **corrupted file
(`AAA.corrupted.v1.json`, invalid JSON) sorting alphabetically *before* the valid
`ACTIVE` skill it shares a prefix with**. Result: the corrupted file is silently
excluded from `_list_active_feature_keys()` (Integration Commit 6's fix holds), and
`consult()` deterministically matches `AAA.first` (the first real, valid, sorted
candidate) — the corrupted candidate did not block or interfere with the legitimate
one. **PASS**, and confirms the documented conflict policy is actually implemented as
described, not just documented.

## Adversarial Boundary F — F1/F2 authority

**Exhaustive search for any remaining pre-F1 execution primitive**: `grep -n
"eval(|exec(|subprocess|os\.system|__import__|compile("` across every file in
`app/core/skill_ledger/` returns matches only inside comments/docstrings describing the
*already-fixed* historical vulnerability — zero live occurrences anywhere in the
package. **PASS.**

**F1 genuinely catches VSL-produced unsafe code, not just model-produced unsafe code**:
constructed a deliberately malicious `ACTIVE` skill (precondition matches a real
`Constant`, transformation replaces it with an `os.system(...)` call), applied it via
the real `runtime.consult()` path, and confirmed the real `scan_for_unsafe_operations()`
(F1) correctly flags the resulting code (`os.system() is unconditionally blocked`) when
run against it. **This is the single most important structural confirmation for the
bounded claim**: F1 does not distinguish or specially trust VSL-modified code — it
applies its real, unmodified check to whatever code string it receives, regardless of
origin. **PASS.**

## Adversarial Boundary G — provenance / outcome attribution

**Verifier-strength mislabeling risk**: confirmed by direct grep that
`verifier_strength` is a hardcoded literal at both real call sites in
`echo_adapter.py` (`"not_yet_verified"`, `"f1_f2_safety_only"`) — there is no
auto-detection logic anywhere that could misclassify a weak verdict as `"full_oracle"`.
Consistent with, and confirms, the readiness report's own disclosed limitation that the
one wired production entry point can structurally never produce `full_oracle`-strength
evidence. **PASS** (the honest, disclosed consequence — real degradation currently can
never fire from this integration point — is a known limitation, not a new defect).

## Section 10 — fresh-process / restart verification

All tests below ran against a genuinely isolated scratch copy of the real skill store
(`/tmp`-based, deleted after use) — the real `memory/skill_ledger/` was never touched by
any of this section's destructive operations.

- **Quarantine persists across a genuine process boundary**: Process 1 (PID 50289)
  quarantined a copy of the real Skill A (`ACTIVE` v4 → `QUARANTINED` v5). Process 2
  (PID 50290, confirmed distinct PID, a wholly separate `subprocess.run()` invocation)
  independently reloaded the same store and confirmed `QUARANTINED`/v5, and confirmed
  `_list_active_feature_keys()` correctly excludes it. **PASS.**
- **Disabled-by-default persists across a genuine process boundary**: a fresh subprocess
  launched with a minimal, explicitly-scrubbed environment (`env={'PATH': ...}`, no
  inherited `VSL_ENABLED`) correctly reports `get_mode() == "disabled"`. **PASS.**

## Section 11 — test the tests (negative controls)

Two negative-control mutations were performed, both via **in-memory-only monkeypatching
inside disposable subprocesses** — no repository file was ever modified to reintroduce
a vulnerability, per an explicit safety-classifier block encountered when this gate
first attempted a more literal repository-level revert (a legitimate, correctly-applied
guardrail against writing real RCE-capable code back into a tracked file, even
temporarily — respected rather than worked around).

1. **eval() regression**: the real regression suite's exact assertion
   (`r1 is None and not os.path.exists(marker)`), evaluated against the *old*,
   vulnerable `_rehydrate()` implementation (defined as a pure in-memory function object,
   monkeypatched onto the module for one disposable process, never persisted), correctly
   evaluates to `False` — i.e., the real suite would catch this regression if it were
   ever reintroduced.
2. **Lifecycle-guard regression**: the same technique applied to `promote_to_qualified()`
   reverted to its old, unguarded form confirms the real suite's assertion would
   likewise correctly fail (catch the regression).

Both negative controls confirm the two fixed findings have genuine, discriminating
regression coverage, not tests that would pass regardless.

## Section 12 — independent review

A fresh, non-fork agent was given the bounded claim, the full governing record, the
implementation, the tests, and this gate's own new evidence (Findings A2/X above,
presented as claims to independently verify or refute, not as established conclusions)
and asked explicitly to look for a reason to block the merge.

**It confirmed Findings X and Y as real** (independently reproduced, not taken on
faith), confirmed Finding 1 (the `eval()` fix) with its own separate negative control
(reverted `_rehydrate()` in memory, replayed the exploit, confirmed the marker file
writes and the real suite's assertion correctly fails), and **went one step further than
this gate's own testing**: it constructed a real, hostile `main.py` — the kind an
adversarial or hallucinated model could plausibly write — that directly imports
`app.core.skill_ledger.schemas` and attempts to forge and save an `ACTIVE` skill
straight to the real `memory/skill_ledger/skills/` directory, then ran it through the
**actual, unmodified `generate_project()` pipeline** with no VSL flags touched. Result:
**F1 did not catch it** (a real, separate, worth-fixing gap — F1's static scanner has no
rule recognizing a `skill_ledger` self-promotion write as a dangerous pattern), but
**F2's real, pre-existing kernel sandbox blocked the write completely** — a plain
`(deny default)` / `(allow file-write* (subpath SCRATCH))` policy that was never
specifically extended to cover `memory/skill_ledger/`, protecting it the same way it
protects every other out-of-scratch path generically. Zero files leaked into the real
store.

**This gate independently re-ran that exact test itself, not just trusted the report**:
confirmed the real skill store held exactly 4 files (`K2.T5.tag_priority_direction.v1..v4.json`)
before the test; constructed the identical hostile `main.py`; ran it through the real,
unmodified `EP.generate_project()`; confirmed `f1_results == {'main.py': 'OK'}` (F1
genuinely misses this pattern) and `f2_result` returned `passed: False` with the
traceback failing exactly at the `s.save_new_version()` line inside the sandboxed
subprocess; confirmed the real store still held exactly the same 4 files afterward,
byte-for-byte unchanged. **The reviewer's most decisive claim is independently
confirmed, not merely trusted.**

The reviewer also surfaced one genuinely new, previously-undisclosed finding of its
own: `_write_report()` — the artifact explicitly headed "for human review only" — never
discloses that VSL fired, which skill/version matched, or that the staged code differs
from what was originally generated/supplied. Classified by the reviewer as a
**SCOPE ERROR relative to a reasonable operator's expectation of what "human review
only" means, not a safety defect** — real traceability still exists via
`applications.jsonl` (Phase 8's own, narrower claim), but the one artifact a human is
actually likely to open is silently incomplete. This gate accepts this classification:
it does not touch any clause of the bounded claim under test (F1/F2 authority,
disable-ability, and non-execution are all unaffected), but it is a real, disclosed gap
worth fixing promptly.

The reviewer's own final verdict: **MERGE**, with four specific, narrow, non-blocking
fast-follow items (validate `lifecycle_state` against the real enum/legacy-consistency
in `effective_lifecycle()`/`Skill.load()`; extend F1's static scanner to recognize
`skill_ledger` self-promotion calls as a blocked pattern, mirroring Finding 83's
self-edit-escalation precedent; add VSL activity disclosure to `_write_report()`;
update `NEXT_ACTION.md`'s Known Risks to name all three explicitly) — explicitly framed
as hardening, not scope expansion, consistent with this mission's own scope freeze.

---

## Files changed during this gate

**None in the tracked repository.** All adversarial artifacts (corrupted skill files,
scratch skill stores, negative-control monkeypatches) were created exclusively in
`tempfile.TemporaryDirectory()` instances, `/tmp`, or a local `.claude_scratch_vsl_gate/`
directory that was deleted before this report was finalized. Confirmed via `git status
--porcelain` immediately before and after the full adversarial pass: no VSL-related
files appear as modified.

## Remaining limitations (carried forward, not newly introduced, unless marked NEW)

- `echo_projects.py` has no correctness oracle — real production applications can only
  ever be recorded at `f1_f2_safety_only` strength (already disclosed in the readiness
  report).
- `self_edit_manager.py` remains unintegrated (already disclosed).
- The conflict-resolution policy has no specificity/outcome-stat tiebreak (already
  disclosed, inherently untested at scale since exactly one real skill is ACTIVE today
  — though this gate's Boundary E test did exercise it with two real ACTIVE skills for
  the first time and confirmed it behaves as documented).
- **NEW this gate (Findings A2/X)**: the lifecycle state machine's guards are enforced
  only by the `promote_to_*`/`mark_degraded` API surface, not by the persistence layer
  itself (`Skill.__init__`/`save_new_version()` perform no validation, and
  `effective_lifecycle()`/`Skill.load()` trust a persisted `lifecycle_state` field with
  zero enum/consistency validation). **Confirmed by the independent reviewer's own live
  exploitation attempt, and independently re-confirmed by this gate, that the actual
  generated-code attack surface this integration exposes cannot reach the real skill
  store regardless: F2's pre-existing, unmodified kernel sandbox blocks any write to
  `memory/skill_ledger/skills/` generically**, the same way it blocks every other
  out-of-scratch write — no VSL-specific enforcement was required for this protection
  to already hold. Recommended fast-follow, not a blocker: validate `lifecycle_state`
  in `effective_lifecycle()`/`Skill.load()`, and extend F1's static scanner to name this
  pattern explicitly for defense-in-depth (F2 alone is sufficient today; F1 catching it
  too is a `Finding 83`-style hardening precedent, not a requirement).
- **NEW this gate (reviewer's Finding 3)**: `_write_report()`'s human-facing artifact
  does not disclose VSL activity (matched skill, version, or that staged code differs
  from supplied code) — a transparency gap, not a safety defect (real traceability
  still exists via `applications.jsonl`). Recommended fast-follow.

## Independent re-verification performed by this gate (not merely trusted from the
reviewer's report)

The reviewer's single most decisive claim — that F2's existing kernel sandbox
generically blocks any attempt to forge a skill file via generated code, with zero
VSL-specific enforcement — was independently reproduced by this gate: the real skill
store was confirmed to hold exactly 4 files before the test; an equivalent hostile
`main.py` was constructed and run through the real, unmodified `generate_project()`;
`f1_results` confirmed `{'main.py': 'OK'}` (F1 genuinely misses this pattern, exactly as
reported); `f2_result` confirmed `passed: False`, with the captured traceback failing
at the exact `save_new_version()` call inside the real sandboxed subprocess; the real
store was confirmed to still hold exactly the same 4 files, byte-for-byte unchanged,
immediately afterward. This is not a restated claim — it is this gate's own,
independently-run reproduction of the reviewer's evidence.

## Final verdict

# MERGE

Every clause of the bounded claim under test held under direct, adversarial,
first-hand testing — by this gate, and independently corroborated by a fresh,
non-fork reviewer whose most significant new evidence (a live exploitation attempt
against the real generated-code attack surface) was itself independently reproduced by
this gate rather than trusted on report alone:

- **Does not autonomously acquire new production skills** — confirmed by exhaustive
  grep (both this gate and the independent reviewer, separately): zero production code
  paths construct or save `Skill` objects outside the guarded `promote_to_*` API,
  itself only reachable via human-run scripts today.
- **Does not bypass F1/F2** — confirmed structurally (VSL patches code before F1, using
  the same real F1/F2 every other generated file uses) and confirmed by direct,
  adversarial demonstration that F1 (a known, now-disclosed gap) and F2 (which holds)
  together still prevent the most severe theoretically-available escalation
  (Findings A2/X's lifecycle forgery) from ever reaching the real skill store through
  the live attack surface.
- **Does not execute skill-file contents as arbitrary code** — the original,
  safety-critical `eval()` finding's fix was independently re-verified via a genuine
  negative control **twice** in this gate (once by this gate directly, once by the
  independent reviewer separately) — both confirm the fixed code correctly rejects the
  exact historical exploit and the regression test genuinely discriminates rather than
  passing trivially.
- **Does not allow inactive skills to affect production behavior** — true for every
  currently-reachable path; the one real gap found (Findings A2/X) is a defense-in-depth
  validation gap at a layer that requires either filesystem tampering or a code path
  that does not exist in production today, and is independently confirmed blocked even
  under direct, hostile exploitation attempts via the actual live pipeline.
- **Can be disabled to restore pre-VSL behavior** — confirmed directly (byte-identical
  F1/F2 results, zero VSL writes when disabled) by this gate, the original integration
  suite, and the independent reviewer separately.

**Three real, disclosed, non-blocking hardening items are tracked, not swept under the
rug**: (1) validate `lifecycle_state` against the real enum and legacy-field
consistency; (2) extend F1's static scanner to recognize `skill_ledger` self-promotion
writes as a named pattern (pure defense-in-depth — F2 already blocks the actual write);
(3) disclose VSL activity in `_write_report()`'s human-facing artifact. None of these
require touching `main`, expanding VSL's scope, or changing the disabled-by-default
posture — they are precisely the kind of "smallest responsible repair surface" the
mission's own Section 16 anticipates for a MERGE verdict that is honest about what
remains, rather than either inflated into a blocker or silently dropped.

This verdict authorizes merge **review** and **execution by Gremlin** — it is not an
authorization for this session to merge autonomously.

## Claim discipline (Section 17)

The strongest authorized conclusion remains exactly what the mission specifies, no
stronger:

> VSL has crossed from experimental evidence into a bounded, reversible production
> capability for consuming previously qualified skills; it has not yet crossed into
> autonomous production acquisition or general continual learning.

This gate found nothing that would justify strengthening that sentence, and nothing
that would justify weakening it to `DO NOT MERGE` either — the one real new class of
finding (Findings A2/X) is disclosed precisely, classified honestly as
non-production-reachable through any path independently confirmed to exist today, and
tracked as hardening work rather than either hidden or allowed to block a verdict the
actual evidence supports.
