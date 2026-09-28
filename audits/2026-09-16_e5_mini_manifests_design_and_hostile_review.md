# E5-mini: Anomaly #17 Integration + Three Frozen Manifests — Design and Hostile Review

**Date:** 2026-09-16
**Scope:** (1) close the one disclosed gap from
`audits/2026-09-16_e5_mini_g0_mock_implementation.md` (anomaly #17 not
integrated into `checker.py::check_ledger()`); (2) design the task,
role/access, and resource-budget manifests that report's own §14/§18
named as the actual remaining blockers to real E5 execution; (3) hostile-
review all three designs with the same rigor used throughout this
mission chain.

**Absolute constraint honored throughout, unchanged from every prior
mission in this chain:** no real model inference was run. No Ollama
call, no Echo query, no production FeralEcho import, no
RiverBrain/FAISS/production-memory access, no live-process interaction.
Real E5 execution was not attempted, considered necessary, or performed
at any point.

---

## 1. Part 1 — Anomaly #17 Integration

**Before:** `checker.py::check_ledger()` had no dedicated detector for
generation-options drift; anomaly #17 was caught only by a direct
field-level assertion inside its own test, never exercising the
aggregated checker path the other 29 anomalies all go through.

**Fix:** added a symmetric `OPTIONS_DRIFT` check (comparing
`requested_options` vs `effective_options`) to both
`check_construction_records()` and `check_solver_records()` — construction
calls are generation events too, and the mission's own confound register
never restricted this to solver calls specifically. Verified the clean
path never had `requested_options != effective_options` anywhere before
adding the check (both fields are built from the identical
`REQUESTED_OPTIONS` constant in `builder.py`), so this addition carries
zero false-positive risk against the existing 52 tests.

Updated `test_anomaly_17_changed_generation_options` to: (a) assert a
clean baseline produces zero `OPTIONS_DRIFT` violations, (b) assert the
tampered solver record is caught via the real `check_ledger()` path, and
(c) added a second case proving the identical drift on a *construction*
record is also caught — this last case is new coverage, not just a
refactor of the existing test.

**Re-verified:** `python3 -m unittest app.experiments.e5_mini.tests.test_e5_mini_g0 -v` →
**52/52 pass, 0 failed** (same count as before — the fix added assertions
to an existing test method rather than a new one). Anomaly #17 is now a
first-class, named, aggregated `checker.py` detector, on equal footing
with the other 29.

---

## 2. Manifest Designs

All three live under `app/experiments/e5_mini/manifests/`, matching the
existing package's style (typed dataclasses, `sha256_of()`/`unknown()`
from `schema.py`, zero production imports). Each is accompanied by a
cross-check function that validates the manifest against the REAL,
already-implemented apparatus rather than trusting its own declared
content — the same "declared policy vs. actual code" discipline
`checker.py` itself already applies to builder.py's output, now applied
one level up, to these manifests' own claims about the code.

### 2.1 Task Manifest (`task_manifest.py`)

Reuses `schema.MicroWorldSpec` verbatim (not redefined) as the per-world
fixture shape. Adds `MechanicalDuplicationCheck` + `NoveltyEvidence` +
`QueryNoveltyRecord`, directly implementing the non-duplication standard
already derived in
`audits/2026-09-16_e5_mini_adversarial_preimplementation_review.md` §6:
a withheld query is genuinely novel only if it (a) fails every mechanical
duplication check (hash/lexical/AST/I-O) **and** (b) shows a real
difficulty differential between a blind zero-context solve and a
teaching-informed solve, above a frozen minimum gap. `TaskManifest.freeze()`
refuses to freeze while any related query lacks a passing
`QueryNoveltyRecord`, and encodes the §8 MUST-FIX rule from the same
review ("pre-register the full family list and forbid post hoc family
exclusion") as `assert_no_family_removed()` — a real, callable check, not
a written rule someone has to remember.

### 2.2 Role/Access Manifest (`role_access_manifest.py`)

Turns the mission's own §6 information invariants (what N/Z/P/E/solver
stages may and must not receive) into a declarative `AccessRule` table
per stage, each rule naming the real `checker.py` violation code(s) that
enforce it. `verify_manifest_coverage()` greps `checker.py`'s actual
source for every live `Violation("CODE"` call site (never hand-copied
from memory) and cross-checks in both directions: every declared
enforcement must correspond to a real code, and every real code must
correspond to a declared rule (or be in the explicit
`INTENTIONALLY_UNMAPPED_CODES` set with a stated reason).

### 2.3 Resource-Budget Manifest (`resource_budget_manifest.py`)

Freezes the ceilings the mission asked for: per-arm construction-call
counts (P=2/family, E=2/family, Z=1/family shared, N=0), the real
`OUTPUT_CEILING_TOKENS`/`REQUESTED_OPTIONS` imported directly from
`builder.py` (not retyped), sandbox/containment parameters (honestly
marked `candidate_can_execute_real_code: False`), and the
one-generation/multiple-oracle-references cost rule stated as an
explicit frozen constraint. `model_backend_identity` is an explicit
`unknown()` — real E5 execution is not authorized, so there is no real
identity to record, and this module does not fabricate one.
`verify_against_real_apparatus()` runs the real `orchestrator.run_family()`
against a fresh synthetic family and confirms the frozen numbers and the
cost-accounting rule actually match what the real apparatus does, live.

### 2.4 Populated Example (`example_synthetic.py`)

Builds a real 2-family `TaskManifest` from `mock.py`'s actual
`make_synthetic_family()` fixture generator (explicitly labeled
synthetic throughout — not the frozen scientific manifest), freezes it,
and exercises all three manifests' cross-checks end to end. Used as the
concrete substrate for the hostile review below rather than reviewing an
abstract schema in the void, per the mission's own instruction.

---

## 3. Hostile Review Findings

Evidence discipline per the mission's own request: **OBSERVED(source)** /
**OBSERVED(artifact)** / **SUPPORTED** / **INFERRED** / **PROPOSED** /
**UNRESOLVED**.

### TASK-1 — "Frozen" only meant "a hash was taken," not "tamper-detectable" — FIXED

**OBSERVED(artifact):** the first draft of `TaskManifest.freeze()`
computed `manifest_hash` from `protocol_id` + the *set of family_ids*
only — never from each family's actual content (novelty records, world
specs). A caller mutating `tm.families[0].related_query_novelty` after
freezing — e.g. forging a passing `QueryNoveltyRecord` to sneak a
duplicate task past `unvalidated_related_queries()` — would leave
`frozen_family_ids` and the hash completely unchanged, since neither
depends on record content.

**Fixed:** `manifest_hash` now hashes the full `dataclasses.asdict()` of
every family (recursively including novelty records and world specs).
Added `TaskManifest.verify_not_tampered()`. **Verified with a real
adversarial reproduction, not just asserted:** built a clean 2-family
manifest, froze it, confirmed `verify_not_tampered() == True`, then
appended a forged passing `QueryNoveltyRecord` to an existing family
(confirming `family_ids` stayed byte-identical, precisely to prove this
isn't just re-detecting TASK-set changes) — `verify_not_tampered()`
correctly returned `False`. Wired into the automated suite as
`test_internal_content_tamper_is_detected_without_touching_family_ids`
(`tests/test_manifests.py`).

### TASK-2 — `min_difficulty_gap_required` is an arbitrary placeholder — UNRESOLVED, OPEN

**PROPOSED:** the example uses `0.30` for the required difficulty
differential between blind and teaching-informed success rates. Nothing
in this design derives that number from a real calibration — it is a
placeholder, exactly the same category of "do not invent a magical
threshold" concern the prior adversarial review already raised about
sample sizes (§9). **This cannot be fixed by more code** — it requires
either a real calibration pilot (out of scope, would require real model
inference) or an explicit, human-owned policy decision to accept a
stated placeholder pending calibration. Flagged, not silently resolved.

### TASK-3 — The blind-vs-informed comparison's "same model/backend/budget" requirement is declared, not enforced — UNRESOLVED, OPEN

**SUPPORTED:** `NoveltyEvidence`'s own docstring states both conditions
"must" use matching parameters to be comparable, but nothing in the data
structure enforces or even records what those parameters were, so a
`NoveltyEvidence` instance provides no way to verify after the fact that
this requirement was honored. **Not fixable within this mission's scope**
— doing so meaningfully requires the real model/backend identity this
manifest's own `resource_budget_manifest.py` already records as
`unknown()`, i.e. it's downstream of the same real-execution blocker.
Noted as a requirement for whoever runs the real blind-solver pilot, not
closed here.

### ROLE-1 — The coverage cross-check existed but nothing ran it automatically — FIXED

**OBSERVED(artifact):** `verify_manifest_coverage()` was a real, correct
function, but calling it was a manual action nobody was obligated to
take. A future edit to `checker.py` (renaming or removing a violation
code) would silently desynchronize the manifest from reality with
nothing to notice, which is exactly the "doc lags commit" failure class
this project's own broader history (CLAUDE.md's Findings ledger) has
repeatedly rediscovered in other subsystems.

**Fixed:** wired into `tests/test_manifests.py` as three real assertions
(`test_every_declared_rule_maps_to_a_real_checker_code`,
`test_no_undocumented_real_checker_code`,
`test_no_stage_left_with_zero_enforcement`), run as part of the same
suite as everything else. **Verified this genuinely catches drift, not
just passes by construction:** the initial cross-check run (before any
manifest fixes) reported 7 real, undeclared codes
(`CROSS_ARM_GENERATION_SHARING`, `DECLARED_DISPATCH_MISMATCH`,
`MISSING_PARENT_CONSTRUCTION`, `OPTIONS_DRIFT`, `P_E_GENERATION_REUSED`,
`STALE_OR_CHANGED_ARTIFACT`, `UNKNOWN_WORLD_ASSIGNMENT`) — a live
demonstration of the check working correctly against a genuinely
incomplete first draft, not a synthetic test case. Five were mapped to
their correct stage; two (see ROLE-2) were deliberately, explicitly
excluded rather than force-fit.

### ROLE-2 — `OPTIONS_DRIFT` and `DECLARED_DISPATCH_MISMATCH` don't fit any of the three manifests — UNRESOLVED, OPEN, genuine scope-boundary finding

**SUPPORTED:** both check real invariants, but neither is an
"information access" property — `OPTIONS_DRIFT` is a resource/generation-
parameter integrity property (arguably belongs to the resource-budget
manifest instead — noted there, but the resource-budget manifest's own
scope as designed is about frozen *ceilings*, not per-call *fidelity to
requested parameters*, so it doesn't cleanly fit there either without
redefining that manifest's scope too). `DECLARED_DISPATCH_MISMATCH` (an
action-integrity property: declared action vs. actually-dispatched
entrypoint) has no home in any of the three manifests at all. **This
suggests the three-manifest design itself may be missing a fourth
category** — something like a "behavioral/generation-fidelity manifest"
— rather than being a gap in any one manifest's execution. Documented
here as an open design question, not silently absorbed into role/access
where it does not conceptually belong; not fixed, because fixing it
would mean redesigning the manifest taxonomy itself, a larger decision
than this mission's scope.

### ROLE-3 — `NON_CHECKER_ENFORCEMENT`'s named functions were never verified to actually exist — FIXED

**OBSERVED(artifact):** the same class of drift risk as ROLE-1, one
level down — `sandbox.guarded_write`, `sandbox.scan_for_escalation_patterns`,
etc. were named in prose with no check that they still resolve to real,
importable code. **Fixed:** `verify_non_checker_enforcement_exists()`
imports each named module and confirms `hasattr()` on the named
attribute; wired into the suite as
`test_non_checker_enforcement_mechanisms_still_exist`.

### ROLE-4 — Cross-arm construction leakage is prevented by call-signature design, not a runtime check — SUPPORTED, monitorable

**OBSERVED(source):** `builder.py::construct_arm()`'s signature has no
parameter through which one arm's constructor could ever receive
another arm's artifact — `mock_construct()` only ever takes this call's
own world's teaching text. This is real, structural protection (nothing
to bypass, since no channel exists), genuinely *stronger* than a runtime
check in one sense. **But it is also untested as its own property** — a
future code change adding a parameter (e.g. "pass prior arms' outputs
for context") could silently reopen this path, and nothing in the
current suite would catch it, since there is no dedicated test asserting
"no construction call site can reach another arm's artifact." Classified
**SHOULD ADD IF CHEAP**, not MUST FIX — the protection is real today; the
residual risk is about future drift, and a static AST-based "no
cross-arm parameter exists in any constructor call site" check would be
a reasonable, cheap follow-up but was judged not urgent enough to build
speculatively within this mission's remaining scope.

### BUDGET-1 — `model_backend_identity` is `unknown()` — SUPPORTED, correctly disclosed, genuine open blocker

Not a gap in this mission's design — an honest, structurally-enforced
statement that this precondition for real execution remains unmet. No
fix is possible here; a real model/package decision is required, which
is explicitly outside this mission's authority per every prior mission's
boundary in this chain.

### BUDGET-2 — Sandbox containment is declared, and honestly declared as inadequate for real execution — SUPPORTED, not a new finding

`SANDBOX_CONTAINMENT_PARAMS` states `candidate_can_execute_real_code: False`
and `real_kernel_sandbox_required_for_real_execution: True` explicitly —
this manifest does not overclaim readiness here, consistent with the
prior implementation report's own §13 known limitation #2.

### BUDGET-3 — `timeout_seconds=60` is an unjustified placeholder — UNRESOLVED, OPEN

Same category as TASK-2: a real number with no real derivation behind
it. Flagged, not silently treated as calibrated.

### BUDGET-4 — Does the frozen arithmetic actually match the real apparatus at scale? — VERIFIED, not a gap

**OBSERVED(artifact):** `EXPECTED_CONSTRUCTION_CALLS_TOTAL_AT_N_FAMILIES(4) == 20`,
matching the prior mission's own verified `construction_calls_total == 20`
finding exactly (8P + 8E + 4Z). Not asserted from the formula alone —
independently re-derived and confirmed to match.

### BUDGET-5 — The resource-budget manifest's "frozen" was weaker than the task manifest's "frozen" — SUPPORTED, genuine design inconsistency, partially addressed

**OBSERVED(artifact):** `TaskManifest.freeze()` captures a real
point-in-time snapshot hash that `verify_not_tampered()` can compare
against later. `resource_budget_manifest.py`'s original `freeze_hash()`
was a *live* function recomputing a hash from current module-level
constants on every call — with no persisted snapshot, it could never
detect "this changed since we last called it frozen," only ever report
"here is the hash right now." This is a real asymmetry between the two
manifests' notion of "frozen." **Not fully restructured in this
mission** (doing so properly means converting `resource_budget_manifest.py`'s
module-level constants into a `TaskManifest`-style dataclass instance
with a captured snapshot, a larger change than remaining scope
comfortably allowed) — but `verify_against_real_apparatus()`'s live
cross-check against the actual code (rather than trusting the manifest's
own numbers) provides a *different*, real form of protection: it would
catch the practical failure mode (the manifest's frozen numbers silently
diverging from what the real apparatus does) even without true
point-in-time tamper detection. Recorded here as **MUST FIX BEFORE this
manifest can be called "frozen" in the same sense as the task
manifest** — a real, named follow-up, not glossed over as already
adequate.

---

## 4. Fixed-in-place vs. Remaining Open

| Finding | Status |
|---|---|
| Anomaly #17 (Part 1) | **FIXED**, integrated + tested |
| TASK-1 (tamper detection) | **FIXED**, verified with a real adversarial reproduction |
| ROLE-1 (coverage check not automated) | **FIXED**, wired into the real test suite |
| ROLE-3 (unverified NON_CHECKER_ENFORCEMENT) | **FIXED** |
| TASK-2 (difficulty-gap threshold uncalibrated) | **OPEN** — needs real calibration, not code |
| TASK-3 (matching-parameters requirement unenforced) | **OPEN** — downstream of real-execution blockers |
| ROLE-2 (OPTIONS_DRIFT/DECLARED_DISPATCH_MISMATCH scope gap) | **OPEN** — possible missing 4th manifest category |
| ROLE-4 (cross-arm leak prevented by signature, untested as its own property) | **OPEN**, SHOULD ADD IF CHEAP |
| BUDGET-1 (model identity unresolved) | **OPEN** — genuine, correctly-disclosed blocker |
| BUDGET-3 (timeout uncalibrated) | **OPEN** — needs real calibration |
| BUDGET-5 (weaker freeze semantics than task manifest) | **PARTIALLY ADDRESSED** — live cross-check exists; true point-in-time tamper detection does not |

---

## 5. Are These Three Manifests Adequate to Be Called "Frozen"?

**Distinct question from whether real E5 execution is authorized — answered
separately, per the mission's own instruction not to conflate the two.**

- **Task manifest design:** adequate as a *mechanism* — `freeze()` now
  has real tamper-detection, `assert_no_family_removed()` is a genuine
  callable guard, and the non-duplication standard is directly
  implemented rather than described in prose. **Not adequate as
  *content*** — the example is explicitly synthetic, and the real
  frozen manifest (the actual scientific task families) does not exist
  and generating it remains outside every mission's scope in this chain.
  The difficulty-gap threshold (TASK-2) is an unjustified placeholder in
  the mechanism even once real content exists.
- **Role/access manifest:** adequate and verified — the two-way
  cross-check against `checker.py`'s real, current enforcement is clean
  (0 declared-but-nonexistent, 0 undeclared-real-codes), and this is now
  a live regression test, not a one-time check. ROLE-2's scope-boundary
  question is real but does not undermine what this manifest does cover.
- **Resource-budget manifest:** **not yet adequate to call frozen** in
  the full sense — `model_backend_identity` is honestly `unknown()`,
  `timeout_seconds` is an uncalibrated placeholder, and BUDGET-5's
  weaker freeze semantics mean this manifest cannot yet detect its own
  tampering the way the task manifest can.

**Real E5 execution is NOT any closer to authorized after this mission**,
and should not be treated as such regardless of how clean the test
counts look. This mission closed real gaps in the *instrument*
(anomaly #17, tamper detection, automated cross-checks) — it did not
resolve any of the substantive, real-world preconditions (real task
content, real model/package identity, real calibrated thresholds, human
sign-off) that remain the actual blockers, exactly as the prior
mission's own §18 stated.

---

## 6. Verification Summary

```
python3 -m unittest app.experiments.e5_mini.tests.test_e5_mini_g0 app.experiments.e5_mini.tests.test_manifests
Ran 64 tests in 0.025s
OK
```

52 original (unchanged in count, extended in assertions for anomaly #17)
+ 12 new manifest tests. 0 failures.

---

## 7. Git / Process Integrity

- **Opening HEAD:** `2fba42644c82b9f7096276f4dd318d615cf1bcce` — wait, corrected below.
- **Opening HEAD (correct):** `2fba42644c82b9f7096276f4dd338d615cf1bcce`
- **Closing HEAD:** `2fba42644c82b9f7096276f4dd338d615cf1bcce` — **unchanged**, no commit made.
- **Opening status:** 193 changed/untracked paths (pre-existing, unrelated concurrent work — same 27 modified tracked files documented in the prior mission's report, e.g. `CLAUDE.md`, `app/core/*`, `claude_relay/*`, `run.py`, `sandbox/*`; none touched by this mission).
- **Closing status:** 199 changed/untracked paths. Delta of +6 attributable to this mission: `manifests/__init__.py`, `manifests/task_manifest.py`, `manifests/role_access_manifest.py`, `manifests/resource_budget_manifest.py`, `manifests/example_synthetic.py`, `tests/test_manifests.py` — all new, isolated files under `app/experiments/e5_mini/`. `checker.py` and `test_e5_mini_g0.py` were modified (both were already untracked from the prior mission, so this shows as no visible git-status change beyond the new files above). **No pre-existing tracked file was touched** — verified directly: every `M` entry in the closing `git status` is identical to the pre-existing modified-file list, none newly appears.
- **Real E5 execution:** not attempted, not run, not considered necessary at any point. No Ollama call, no model load, no production import.
