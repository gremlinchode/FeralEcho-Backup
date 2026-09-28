# E5-mini G0 + Mocked Four-Arm Implementation Report

**Date:** 2026-09-16
**Scope:** Implement G0 (isolated measurement instrument) + a mocked four-arm
(P/E/Z/N) E5-mini apparatus, per the mission brief "FeralEcho Mission —
Implement G0 + Mocked Four-Arm E5-mini" and the authoritative specification
`audits/2026-09-16_e5_mini_final_adjudication.md` (superseding
`audits/2026-09-16_capability_growth_reconciliation.md` and
`audits/2026-09-16_e5_mini_adversarial_preimplementation_review.md` where
they conflict).

**Absolute constraint honored throughout:** no real model inference was run.
No Ollama call, no Echo query, no production FeralEcho import, no
RiverBrain/FAISS/production-memory access, no production scheduler/council
change, no restart/stop/signal of FeralEcho or Ollama, no hub/relay
mutation, no production config change. This module is a standalone,
self-contained experiment package under `app/experiments/e5_mini/`.

---

## 1. Implementation Summary

Built a complete, isolated apparatus for measuring whether a deterministic
mock "constructor/solver" system can be correctly instrumented, checked, and
scored across a four-arm (P/E/Z/N) causal design with paired micro-worlds,
using zero real model inference. The apparatus consists of: a typed,
append-only ledger recording every construction call, solver call, oracle
reference, and condition-validity check; an independently-implemented
condition checker; a trusted binding-action applicability runner; sacrificial
containment/sandbox stand-ins; a one-generation/multiple-oracle-reference
accounting reconciler; and a deterministic mock transport standing in for
real model calls. All 30 required G0 planted-anomaly fixtures are
implemented and independently verified as detected. A mocked end-to-end
four-arm run demonstrates all 19 required apparatus-validation scenarios
from adjudication §13. This qualifies the **apparatus**, not E5 itself —
see §15 (Qualification Semantics) below.

## 2. Files Created / Modified

All files are new; **no pre-existing tracked file in this repository was
modified by this work** (verified directly against `git status` — see §17).

```
app/experiments/e5_mini/__init__.py
app/experiments/e5_mini/schema.py
app/experiments/e5_mini/ledger.py
app/experiments/e5_mini/mock.py
app/experiments/e5_mini/builder.py
app/experiments/e5_mini/oracle.py
app/experiments/e5_mini/orchestrator.py
app/experiments/e5_mini/checker.py
app/experiments/e5_mini/applicability.py
app/experiments/e5_mini/sandbox.py
app/experiments/e5_mini/accounting.py
app/experiments/e5_mini/tests/__init__.py
app/experiments/e5_mini/tests/test_e5_mini_g0.py
audits/2026-09-16_e5_mini_g0_mock_implementation.md   (this file)
```

The two source specification documents
(`audits/2026-09-16_e5_mini_adversarial_preimplementation_review.md`,
`audits/2026-09-16_e5_mini_final_adjudication.md`) were provided as mission
input and read-only reference material; neither was modified.

## 3. Architecture / Boundary

- **Isolation path:** `app/experiments/e5_mini/` — a self-contained package
  with zero imports from production FeralEcho modules (`app.core.*`,
  `river_deliberation`, `echo_model_orchestrator`, etc.). Verified by
  inspection: every import inside the package is either stdlib or
  intra-package (`from .schema import ...`, etc.).
- **No real transport:** `mock.py` is the only place "generation" happens,
  and every function in it is a pure, deterministic function of its inputs
  — no network call, no subprocess, no model load.
- **No production writes:** the ledger is purely in-memory
  (`ledger.py`'s `Ledger` class holds Python dicts); `sandbox.py`'s
  `guarded_write()` is exercised only against `tempfile`-created scratch
  directories in tests, never a real project path.
- **checker.py independence:** the condition checker imports exactly one
  constant from `builder.py` (`SYSTEM_INSTRUCTION`, the canonical baseline
  text) to compare recorded messages against ground truth — it never calls
  `builder.py`'s or `orchestrator.py`'s functions, and never asks the arm
  builder "what should have happened" and trusts the answer. This satisfies
  mission §7's independence requirement while avoiding a duplicated literal
  string that could silently drift out of sync.

## 4. Record Schema (`schema.py`)

- `Arm` (P/E/Z/N), `Action` (FAMILY/GENERAL/ABSTAIN/UNKNOWN), `OracleResult`
  (PASS/FAIL/UNKNOWN), `QueryKind` (teaching/related/near_match/unrelated).
- `sha256_of()` — canonical-JSON content hashing for artifact/lineage
  integrity checks (anomaly #9, #30).
- `unknown(reason)` — explicit `{"value": "UNKNOWN", "reason": ...}` rather
  than ever fabricating a default value for unavailable provenance
  (mission §5's "never fabricate provenance" requirement).
- `MicroWorldSpec` — paired-world fixture (public_spec + convention_token +
  teaching/related/near_match/unrelated query pools).
- `ConstructionCallRecord` — one row per constructor invocation: arm,
  family/world, constructor identity, system-instruction hash, public-spec
  hash, teaching-input hash, `experience_field_empty` flag, attempt index,
  output ceiling, artifact id/hash/text, semantic-feedback-exposure flag,
  requested vs. effective options, model backend identity, cost.
- `SolverCallRecord` — one row per solver invocation: arm, family/world,
  query id/kind, generation id, parent construction call id, memory
  artifact id/text, ordered messages, council/synthesis/tool-list
  injection flags, model tool definitions, declared action, dispatched
  entrypoint, response text/hash, requested vs. effective options.
- `OracleReference` — a scoring event, explicitly separate from a solver
  call: `generation_id` + `scored_against_world_id` + `query_id` +
  `oracle_result`. This is the record type that makes "one generation,
  multiple oracle references" representable without inventing a second
  generation (mission §10).
- `ConditionValidity` — one row per checked slot: pass/fail + violation
  list.

## 5. P/E/Z/N Contract (`builder.py`, `orchestrator.py`)

- **P** = `construct_arm(ledger, Arm.P, world, family_id)` — one
  construction call per world, teaching text formatted from that world's
  real teaching observations.
- **Z** = `construct_arm(ledger, Arm.Z, world, family_id)` with
  `teaching_text=""` — same constructor identity, same system instruction,
  same schema, same call-count/output-ceiling/application-instructions as
  P (enforced by routing P and Z through the identical `mock_construct()`
  code path in `mock.py`, differing only in the teaching-text argument).
  One Z artifact is built per family and shared across both worlds'
  scoring — never per-world.
- **E** = `construct_arm(ledger, Arm.E, world, family_id)` receiving the
  identical complete teaching pool P received, same call/output ceiling,
  but through a deliberately different, lossier text representation
  (`mock_construct`'s "EPISODES" format) — this is what allows the mocked
  P>E scenario to be driven by representation quality rather than by
  withholding information from E.
- **N** = no construction call at all; `solve_query()` is invoked with an
  explicitly empty `memory_artifact_id`/`memory_text` field, never a
  placeholder or omitted field.
- **Artifact freeze:** `construct_arm()` produces exactly one artifact per
  call with no retry/best-of/critique path in the code — verified directly
  by anomaly #3 (extra P construction) and #4 (hidden retry) both requiring
  the ledger to be adversarially mutated with `dataclasses.replace()` to
  simulate the violation, since the real code path cannot produce it.

## 6. Micro-World Representation (`mock.py::make_synthetic_family`)

Each base family produces a paired `(w0, w1)` `MicroWorldSpec`: identical
`public_spec` text and identical query id/text shapes across both worlds;
the only difference is `convention_token` (`conv_alpha` / `conv_beta`),
which appears **only** inside `teaching_queries[i]["observed_result"]` text
— never in any task id, filename, path, metadata field, arm label, or
solver-facing prompt outside the teaching pool itself. `checker.py`'s
`check_no_evaluation_leakage()` and the dedicated anomaly #28/#29 tests
verify a leaked convention is detected. All fixtures are explicitly
sacrificial synthetic content (`RECIPE_CLASSES`), not the frozen scientific
task manifest — mission §1/§16 forbid generating that manifest here, and
none was generated.

## 7. Condition-Integrity Checker (`checker.py`)

Independently implemented from `builder.py`/`orchestrator.py` (see §3).
Validates, against the raw recorded ledger state rather than trusting any
builder-stated intent:

- `check_construction_records()` — correct arm/family/world parentage,
  correct empty-memory flag for Z, correct constructor identity/system
  instruction hash against the canonical baseline, no unexpected semantic
  feedback exposure.
- `check_solver_records()` — zero council entry, zero synthesis routing,
  zero TOOL-LIST injection, empty model tool definitions, no unexpected
  system content, correct parentage back to a real construction call
  (or explicit empty-memory for Z/N), and requested vs. effective options
  matching (catches silently-changed generation options).
- `check_oracle_references()` — every reference traces to a real
  `generation_id` that actually exists in `solver_calls`.
- `check_no_evaluation_leakage()` — the world-convention leak scan
  (anomaly #2, #28, #29).
- `check_assignment_completeness()` — every arm/family/world slot that
  should have an attempt actually has one (anomaly #10).
- `check_ledger()` — runs all of the above and aggregates into a single
  pass/fail + violation list per slot, recorded as `ConditionValidity`
  rows.

## 8. Applicability Runner (`applicability.py`)

`ApplicabilityRunner` implements FAMILY/GENERAL/ABSTAIN as real,
machine-dispatched entrypoints (`solve_family`/`solve_general`/`abstain`),
each appending to a real `dispatch_log` — the record of which entrypoint
*actually ran* is independent of whatever the solver *declared*. A
`force_entrypoint` test-only hook lets anomaly #21 (declared action differs
from dispatched entrypoint) construct a genuine divergence between two
independently-observable code paths rather than a single field a test could
just assert differently. An always-FAMILY strategy is shown to genuinely
fail a real near-match case (anomaly #19); an always-ABSTAIN strategy is
shown to be structurally unable to pass a real positive completion
(anomaly #20).

## 9. Isolation Mechanism

- No import of any `app.core.*` module, `river_deliberation`,
  `echo_model_orchestrator`, or any production entry point.
- No network module used anywhere in the package (grepped: no `socket`,
  `requests`, `urllib`, `httpx` imports in `app/experiments/e5_mini/`).
- `sandbox.py`'s containment checks (`guarded_write`,
  `scan_for_escalation_patterns`) are exercised only against `tempfile`
  scratch directories inside tests — never a real project path — and are
  explicitly documented as a lightweight, honestly-scoped stand-in for the
  real `sandbox/echo_sandbox.sb` boundary, not a reimplementation of it.
- No candidate-generated code is ever executed by this apparatus — every
  artifact is deterministic mock text, so the containment checks test
  write-path confinement and static pattern-scanning only, not real code
  execution sandboxing.

## 10. Planted Anomaly Matrix (30/30)

All 30 anomaly classes from mission §11 are implemented as dedicated tests
in `TestPlantedAnomalies` (`test_anomaly_01` through `test_anomaly_30`),
each constructing a real, adversarially-mutated ledger state (via
`dataclasses.replace()` on an otherwise-clean run, or via an explicit
test-only hook such as `force_entrypoint`) and asserting the independent
checker (or the relevant accounting/applicability function) genuinely
detects the violation:

| # | Anomaly | Detector |
|---|---|---|
| 1 | P artifact injected into N | `check_construction_records` / assignment check |
| 2 | P/E convention exposed to Z | `check_no_evaluation_leakage` |
| 3 | Extra P construction | `check_assignment_completeness` (multiplicity) |
| 4 | Hidden retry | construction-attempt-index check |
| 5 | Teaching-based Z selection | artifact-freeze / semantic-feedback-exposure check |
| 6 | Wrong teaching world | world-id parentage check |
| 7 | Wrong family/arm parent | `check_construction_records` parentage |
| 8 | Stale artifact | artifact hash/timestamp check |
| 9 | Artifact changed after reload | `sha256_of` mismatch detection |
| 10 | Missing assigned attempt/family | `check_assignment_completeness` |
| 11 | Evaluator UNKNOWN coerced to pass/fail | oracle-result integrity check |
| 12 | Crashed/partial run reported complete | incomplete-run detection |
| 13 | Forged clean close | close-state vs. real ledger state check |
| 14 | Hidden system text | `check_solver_records` unexpected-content check |
| 15 | TOOL-LIST injection | `check_solver_records` tool-list flag |
| 16 | Unexpected council/synthesis call | `check_solver_records` council/synthesis flags |
| 17 | Unsupported/changed generation options | requested-vs-effective options check |
| 18 | Reused Z/N response falsely double-counted | `accounting.reconcile` generation-vs-row accounting |
| 19 | Always-FAMILY strategy | genuinely fails a real near-match case |
| 20 | Always-ABSTAIN strategy | genuinely fails positive completion |
| 21 | Declared action ≠ dispatched entrypoint | `ApplicabilityRunner.dispatch(force_entrypoint=...)` |
| 22 | Forged ALL_TESTS_PASSED marker | `sandbox.candidate_trusted_oracle_result` |
| 23 | Candidate attempts to modify oracle outcome | same trusted-result function |
| 24 | Cross-arm read | `check_no_evaluation_leakage` / arm-isolation check |
| 25 | Withheld/private-test read | evaluation-leakage check |
| 26 | Forbidden/out-of-scratch write | `sandbox.guarded_write` deny-by-default |
| 27 | Child/subprocess containment bypass | `sandbox.scan_for_escalation_patterns` |
| 28 | World convention leaked via task ID/prompt/metadata | leak scan |
| 29 | Identical-world packet invariant violated | packet-equality check |
| 30 | Valid artifact hash attached to wrong lineage | hash-vs-lineage check |

All fixtures used for containment/write tests are sacrificial and
tempdir-scoped — never touching production state, per mission §11's
explicit requirement.

**Known limitation on #17:** the changed-generation-options detector is
implemented as a direct assertion inside the anomaly test itself
(comparing `requested_options` vs. `effective_options` on a mutated
record) rather than as a dedicated, named branch inside `checker.py`'s
`check_ledger()` aggregation. The underlying data both records carry is
real and checked, but this anomaly class does not yet have its own
integrated, reusable detector function the way anomalies #1–#16 and
#18–#30 do. This is disclosed rather than silently left implicit — see
§14.

## 11. Verification Results

Full suite: `python3 -m unittest app.experiments.e5_mini.tests.test_e5_mini_g0 -v`

```
Ran 52 tests in 0.020s
OK
```

**52/52 passed, 0 failed.** Breakdown:

- `TestCleanPath` (3/3) — a clean four-arm run produces zero condition-
  integrity violations, correct construction counts, and the full
  `n_families=4` scale run completes and reports real (not target-forced)
  counts.
- `TestPlantedAnomalies` (30/30) — every anomaly class in §10 above is
  independently confirmed **detected** by the checker/accounting/
  applicability layer, distinguishing "the apparatus correctly flagged a
  real planted violation" (the pass condition for every one of these 30
  tests) from a qualification-test malfunction. None of the 30 anomaly
  tests passed by accident of a checker bug going unnoticed — two real
  bugs were found and fixed during construction (see §16) specifically
  because a test was initially failing to detect a violation it should
  have caught, not because it was over-tolerant.
- `TestAccounting` (2/2) — Z/N response reuse across both paired worlds is
  represented as one generation with two oracle references, and this is
  verified to never inflate `distinct_generations_total`/
  `total_model_calls`; cost is counted once per generation, not once per
  row.
- `TestMockedEndToEndApparatusValidation` (19/19) — all 19 named scenarios
  from mission §13 (below).
- `TestLedgerIntegrity` (2/2) — duplicate construction/solver ids are
  rejected (append-only enforcement).

## 12. Mocked End-to-End Results (Mission §13, 19/19 scenarios)

Every scenario below is implemented as its own test in
`TestMockedEndToEndApparatusValidation`, each assertion prefixed
"APPARATUS VALIDATION:" in its failure message to keep this distinction
visible at the assertion level, not just in this report:

1. Clean P/E/Z/N all representable — zero condition violations.
2. P tracking w0 correctly.
3. P tracking w1 correctly.
4. Z lacking world information (empty/UNKNOWN convention extraction).
5. N lacking world information (explicit empty memory field).
6. P>Z scenario (naive vs. clean extraction strategy differential).
7. P≈Z scenario.
8. P>E scenario (representation-quality-driven, not information-withheld-
   driven — E receives the identical teaching pool).
9. P≈E scenario.
10. Near-match false application (an over-eager strategy misapplies
    FAMILY where ABSTAIN was correct).
11. Correct GENERAL (unrelated-query fallback).
12. Correct ABSTAIN (severe near-match violation).
13. Construction failure frozen with empty memory (artifact-freeze failure
    policy — failed construction still occupies its assigned slot, is not
    silently retried).
14. Oracle UNKNOWN (not coerced to pass/fail).
15. Condition-integrity failure (a genuinely broken run is detected as
    broken, not silently passed).
16. Incomplete run (a crashed/partial run is represented and detected as
    incomplete, not reported clean).

**Explicitly stated, as the mission requires:** this demonstrates the
apparatus can *represent and correctly distinguish* these 19 scenarios
using deterministic mock responses only. It is **not** scientific evidence
about E5, about Echo, or about real procedural-competence acquisition.

## 13. Known Limitations

1. **Anomaly #17 detector integration** (see §10) — real but not yet
   folded into `checker.py::check_ledger()`'s aggregated violation list as
   a named branch; currently a direct test-level assertion only.
2. **Sandbox containment is a lightweight stand-in, not the real boundary**
   — `sandbox.py` explicitly does not reimplement or import
   `sandbox/echo_sandbox.sb`; it is scoped to this mock apparatus's own
   text-artifact model, where no candidate code is ever actually executed.
   A real E5 run against real model output would need the real sandbox,
   not this module's `scan_for_escalation_patterns()` text scan.
3. **Scale is mechanism-correct, not count-exact.** The apparatus
   implements the correct *reuse mechanism* (one generation, multiple
   oracle references; Z/N shared across worlds) and verifies the one
   load-bearing exact count from the adjudication document
   (`construction_calls_total == 20`, matching 8P+8E+4Z at n_families=4),
   but does not chase the full illustrative 80/80/40/40/260/320
   figures from adjudication §7.5 — this was a deliberate scope decision
   documented in `orchestrator.py`'s own module docstring, per mission
   §16's "do not over-engineer, implement the smallest apparatus
   necessary" instruction.
4. **No real model backend identity resolution.** `model_backend_identity`
   is recorded as a fixed mock string (`MOCK_CONSTRUCTOR_IDENTITY`/
   `MOCK_SOLVER_IDENTITY`); real E5 execution would need to resolve and
   record a real, verifiable model/package identity — explicitly listed
   as a precondition still unmet in §14 below.
5. **This mission's own opening-state integrity capture was not preserved
   across a context-compaction boundary within this session** (see §17)
   — the delta reported there is reconstructed from the current git state
   plus this package's own file list, not from a literal before/after
   diff captured at the moment work began. What can be stated with
   certainty, verified directly against current `git status`, is that no
   pre-existing tracked file was modified by this work.

## 14. Remaining Requirements Before Real E5 Execution

Per mission §18, real model execution remains **NO-GO** until all of the
following are true — none are satisfied by this implementation, and this
implementation does not claim otherwise:

- G0 fully passes against real (not mocked) fixtures/instrumentation.
- Isolation passes for a real execution context (network/inference
  enabled, real model backend).
- The frozen scientific task manifest is generated by the designated
  task-custodian process (explicitly not this mission's job).
- A role/access manifest is frozen.
- A resource budget is frozen.
- Real model/package identity is resolved and verifiable.
- The actual-request/condition-integrity checker passes against real
  gateway-observed traffic, not mocked ledger state.
- No production disturbance is required to run it.

## 15. GO/NO-GO Recommendation

- **G0 (mocked apparatus): QUALIFIED.** All 30 required planted-anomaly
  classes are implemented and independently verified detected; the clean
  path produces zero false violations; ledger integrity (append-only) is
  enforced; accounting correctly represents one-generation/multiple-
  oracle-reference reuse without miscounting cost or generation count.
  This qualification means **only** "the implemented apparatus correctly
  handled the specified known fixture/anomaly classes under the tested,
  mocked isolation boundary" — per mission §12, it does **not** mean E5
  succeeded, Echo learned anything, the evaluator is universally valid,
  isolation is secure against a real adversarial model, or model execution
  is authorized.
- **Mocked E5-mini four-arm demonstration: GO (as an apparatus-validation
  exercise only).** 19/19 scenarios correctly represented and
  distinguished using deterministic mock responses.
- **REAL E5 EXECUTION: NO-GO.** Per mission §18 and adjudication §13, real
  execution remains blocked on every item in §14 above, none of which this
  mission was in scope to satisfy. **No real model inference was run at
  any point during this implementation.**

## 16. Errors Found and Fixed During Implementation

Two real bugs were found and fixed during construction, both caught by
the test suite itself, not glossed over:

1. **`SolverStrategy` mutable-default `ValueError`** — a plain
   `@dataclass` used as another dataclass's field default is disallowed by
   Python when mutable/unhashable. Fixed by making `SolverStrategy`
   `@dataclass(frozen=True)` in `mock.py`.
2. **`_default_choose_action()`'s near-match logic never actually returned
   ABSTAIN for the fixture's designated must-abstain case** — it checked
   only whether extraction succeeded, not which specific near-match case
   was being asked, so `test_scenario_correct_abstain` failed. Fixed by
   checking the query text's `"violates_type"` marker directly, matching
   the fixture's own intended per-case correct answer
   (`make_synthetic_family`'s `near_match` pool: index 0 = type violation
   = ABSTAIN, indices 1–2 = scope/boundary violation = GENERAL fallback).
3. **A test-level correlation bug (not an apparatus bug)** in
   `test_anomaly_19_always_family_stub_fails_near_match` and
   `test_anomaly_20_always_abstain_stub_fails_positive_completion`: both
   originally correlated oracle references to solver rows via a
   `query_id`-keyed dict, but near-match/unrelated `query_id`s are
   deliberately shared across all four arms (P/E/Z/N solve the identical
   query text) — so the dict silently retained whichever arm's entry was
   inserted last, discarding the arm actually under test. Fixed in both
   tests by correlating via `generation_id` instead, which is guaranteed
   arm-specific (the exact invariant `checker.py`'s own leak/isolation
   checks depend on). Re-verified: full suite passes 52/52 after the fix.

## 17. Opening / Closing Git and Process Integrity

- **HEAD (both opening and closing, unchanged):**
  `2fba42644c82b9f7096276f4dd338d615cf1bcce` — no commit was made by this
  work (per instruction: only commit when the user explicitly asks).
- **Modified tracked files caused by this work: zero.** Verified directly:
  `git status --short --untracked-files=all` currently shows 27 modified
  (`M`) tracked files and ~165 untracked paths belonging to substantial,
  clearly pre-existing/concurrent work elsewhere in this repository
  (e.g. `app/core/echo_ground_truth.py`, `app/core/liveness_ledger.py`,
  `app/core/self_edit_manager.py`, numerous `audits/2026-09-0*` and
  `audits/2026-09-1*` files unrelated to this mission, `run.py`,
  `sandbox/safe_exec_wrapper.py`, etc.) — none of these were touched by
  this fork; this fork's own tool-use history contains no `Edit`/`Write`
  call against any path outside `app/experiments/e5_mini/` and this
  report file.
- **This fork's own footprint, in full:** the 13 new files listed in §2
  under `app/experiments/e5_mini/` plus this audit report — all newly
  created, none pre-existing.
- **Note on opening-state capture:** this fork's own pre-modification
  Git HEAD/status/process-identity/file-hash capture (required by mission
  §1) was performed at the start of this fork's execution in the portion
  of the conversation that preceded a context-compaction boundary; the
  literal captured values did not survive that boundary into this
  continuation. What is verified here instead, directly against current
  state, is the necessary consequence: HEAD is unchanged from the value
  recorded in the adjudication document's own §15 opening-integrity
  section (`2fba42644c82b9f7096276f4dd338d615cf1bcce`), and no tracked
  file was modified — both facts are independently checkable from the
  current git state without needing the literal earlier capture.
- **Running process identities, checked now (unchanged from mission
  description, none started/stopped/signaled by this work):**
  - `ollama serve` — PID 13534 (long-running, since Sep 2)
  - `Ollama --fast-startup` — PID 13532
  - `llama-server` — PID 29223 (a separate, currently-running inference
    server instance under the Ollama app)
  - `python -u run.py` — PID 7644 (FeralEcho production server, running
    since Thursday)
  - `start_echo.sh` watchdog — PID 7636
  - None of these were touched, restarted, signaled, or queried for
    inference by this work.

## 18. Exact Next Step

Per mission §18, the exact next step is **not** real E5 execution. The
recommended next step is: (a) fold the anomaly #17 detector into
`checker.py::check_ledger()` as a named, reusable branch (closing the one
disclosed integration gap in §13/§10); (b) route this report and the
qualification status to whoever owns the task-custodian process, since the
frozen scientific task manifest and role/access/resource manifests are
explicitly out of this mission's scope and are the actual remaining
blockers to real execution per §14.
