# Stage E0.1: Narrow Evaluator Repair and Requalification

Implementation-authorized, narrowly scoped per this mission's own explicit terms. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after (confirmed by `git rev-parse` before and after). No commit was made. No production Echo, RiverBrain, self-edit, attempt ledger, council, task-type classifier, routing, AP-0, generation infrastructure, or `sandbox/echo_sandbox.sb` was modified. Only the three pre-existing Stage E0 files inside `app/experiments/rung1/` and `scripts/verify_rung1_e0_trusted_evaluator.py` were edited; no new files were created.

## 1. Executive verdict

**E0.1 QUALIFIED.** Every one of Codex's independently-validated findings (`audits/2026-09-23_codex_e0_independent_scientific_validation.md`) was first independently reproduced from source before any repair was attempted, then repaired at its root, then re-verified. The core E0 architecture — expected values confined to the trusted parent, candidate execution in a separate process, comparison after child exit, one `CORRECT` path — was preserved unmodified, as required. The demonstrated `SystemExit(7)` misclassification is fixed. The result contract is now explicit and enforced (missing-value rejection, bool/int type-strictness, non-finite-float rejection, a depth bound, a byte-based size bound). The secrecy-qualification methodology bug (checking for a sentinel that was never the actual `expected` value passed to the attacks) is fixed, with a runtime-generated, unpublished sentinel and an execution-validity control. A positive control confirms the corrected methodology can detect deliberate disclosure. All 35 original checks remain traceable and pass unchanged; 22 new, Codex-motivated checks were added — **57 passed, 0 failed**, reproduced twice.

## 2. Authorization/scope

Authorized: modification of `app/experiments/rung1/` and `scripts/verify_rung1_e0_trusted_evaluator.py` only, plus this report. Explicitly not authorized and not touched: production Echo, RiverBrain, self-edit, attempt ledger, council, task-type classifier, routing, AP-0, generation infrastructure, `sandbox/echo_sandbox.sb`, general sandbox infrastructure, G0 machinery, learning state. No real hidden AP-0 artifact was connected. G0 was not begun. No learning trial was run. No commit was made.

## 3. Repository provenance

**OBSERVED.** Before any edit: `git rev-parse HEAD` = `2fba42644c82b9f7096276f4dd338d615cf1bcce`; `git status --porcelain` snapshotted to `/tmp/pre_e01_status_snapshot.txt` (226 entries). After all edits: identical HEAD; a diff between the pre-mission snapshot and the post-mission status shows **zero new or removed entries** — only the two pre-existing untracked paths this mission was authorized to modify (`app/experiments/rung1/`, `scripts/verify_rung1_e0_trusted_evaluator.py`) were touched, confirmed via direct `diff` against the saved snapshot, not assumed.

## 4. Codex findings independently reproduced

Every load-bearing claim in Codex's report was reproduced from source or by direct execution before any repair, not accepted on the report's own authority:

| Codex finding | Independent reproduction |
|---|---|
| `SystemExit(7)` → `SANDBOX_INFRASTRUCTURE_ERROR` | Reproduced exactly: `run_case("def f(a):\n raise SystemExit(7)\n", "f", [0], 0)` returned `{'outcome': 'SANDBOX_INFRASTRUCTURE_ERROR', 'detail': 'nonzero exit 7', ...}` before any fix |
| `echo_sandbox.sb` explicitly allows `process-exec*`; fork alone is denied by omission | Confirmed by direct `grep` of the real file: line 46 is `(allow process-exec*)`, with an adjacent comment stating fork is intentionally omitted. My own prior docstring claim ("fork/exec denied by omission") was factually wrong for the exec half — corrected |
| Secrecy suite passes `expected="irrelevant-expected-value-not-sentinel"` while `leaked()` checks for a different, hardcoded `SENTINEL` | Confirmed by direct re-read of the original suite's own source: the attack loop at the reported line number does exactly this |
| `True == 1` under the original comparison | Reproduced: `run_case("def f(a): return True", "f", [0], 1)` returned `CORRECT` before the fix |
| Missing `"value"` silently resolves via `.get()` | Reproduced conceptually via direct test of the original code path's `.get("value")` semantics before the fix |

No claim in Codex's report was found to be false during this reproduction pass.

## 5. Files changed

- `app/experiments/rung1/candidate_worker.py` (modified)
- `app/experiments/rung1/trusted_evaluator.py` (modified)
- `scripts/verify_rung1_e0_trusted_evaluator.py` (modified)

No new files were created; no file outside this authorized set was opened for writing.

## 6. Preserved E0 architecture

Unchanged, verified both by direct source inspection and by the fact that all 35 original acceptance checks still pass without modification to their own assertions: `expected` remains a local variable inside `trusted_evaluator.run_case()`, never written to candidate source, stdin, environment, or launch arguments; candidate execution occurs in a fresh sandboxed subprocess per case; comparison occurs in the trusted parent strictly after child exit; there is exactly one `CORRECT` path (`_typed_equal` inside `_validate_and_compare`, called only from the trusted parent); the historical same-process exposure remains removed (confirmed again by the section-6 old-vs-new test, now also re-run against a runtime-generated sentinel in section 7d, with identical results).

## 7. Failure-attribution repair

Root-caused precisely: `candidate_worker.py`'s exec/call blocks caught `Exception`, which does **not** include `SystemExit` or `KeyboardInterrupt` (both subclass `BaseException` directly). A candidate calling `sys.exit(N)` therefore propagated all the way out of the worker process, terminating it with a real nonzero exit code that `trusted_evaluator.py` then treated as "trusted launch evidence" of an infrastructure fault — an authentic *observation* (a real exit code) mistaken for an authentic *diagnosis* (the sandbox/launch mechanism failed), exactly as Codex characterized it.

**Fixed at the root, in the untrusted process**: both `except Exception as e:` blocks in `candidate_worker.py` (around `exec()` and around the function call) are now `except BaseException as e:` — `SystemExit`/`KeyboardInterrupt` raised by candidate code are caught and reported through the identical `candidate_error` JSON envelope every ordinary exception already used, so they never reach the controller as a raw exit code at all.

**What this cannot catch, handled honestly rather than glossed over**: `os._exit()` invokes the C-level `_exit()` syscall directly, bypassing all Python exception machinery — no `except` clause, however broad, can intercept it. This is a genuinely different case from `SystemExit`, and it is treated differently: the controller-side taxonomy now distinguishes a *confirmed* sandbox-launch failure (exit code 65, sandbox-exec's own documented profile-apply-failure convention, per `echo_sandbox.sb`'s own header comment) from *any other* nonzero exit with no parseable output, which is classified into a new, explicitly separate outcome — `CHILD_TERMINATED_UNVERIFIED` — rather than defaulting to either "infrastructure" or "candidate error" without real evidence for either. This directly satisfies the mission's own instruction: *"If some termination cause cannot be reliably attributed, represent that uncertainty honestly rather than falsely labeling it infrastructure."*

## 8. Before/after SystemExit evidence

**Before** (reproduced this session, prior to any edit): `run_case("def f(a):\n    raise SystemExit(7)\n", "f", [0], 0)` → `{'outcome': 'SANDBOX_INFRASTRUCTURE_ERROR', 'detail': 'nonzero exit 7', '_researcher_stderr': ''}`.

**After**: the identical call → `{'outcome': 'CANDIDATE_ERROR', 'detail': {'stage': 'call', 'error_type': 'SystemExit'}}`.

Preserved as a permanent regression test (`scripts/verify_rung1_e0_trusted_evaluator.py`, section 7, "SystemExit is classified CANDIDATE_ERROR, not infrastructure").

## 9. Frozen result domain

Determined from the smallest domain AP-0-shaped small pure-function tasks actually need (re-checked directly against `app/experiments/accumulation_probe/tasks.py`'s own real return shapes during this session: ints, bools, strings, lists, dicts with string keys, tuples serialized as lists) — not a general-purpose RPC/serialization system, per the mission's explicit instruction.

- **Allowed types**: `int`, `bool`, `float` (finite only), `str`, `list`, `dict` (string keys — the only kind JSON itself can express), `None`.
- **Lists**: required (real AP-0 tasks return them).
- **Mappings**: required (real AP-0 tasks return them).
- **Nesting**: bounded at depth 6 (`_MAX_DEPTH`), enforced by `_depth_within_limit()`, a small recursive checker — chosen generously to cover realistic "list of tuples" / "dict of lists" shapes without permitting pathological depth.
- **Sizes**: one overall serialized-envelope bound (4096 bytes, now measured in actual UTF-8 bytes, not characters — see §12).
- **Numeric semantics**: non-finite floats (`inf`, `-inf`, `NaN`) are explicitly rejected (`_contains_non_finite()`) — Python's `json` module otherwise accepts and round-trips these as non-standard tokens.
- **Booleans vs. integers**: treated as **distinct types** (`_typed_equal()`), recursively, at every nesting level — the more rigorous, defensible choice for a scientific measurement instrument, closing exactly the `True == 1` gap Codex named.
- **Null/None**: a fully permitted, valid value, distinguishable from a merely-*missing* `"value"` key (§10).
- **Equality**: `_typed_equal()`, recursive, type-strict specifically for bool vs. non-bool at every level; otherwise ordinary value equality — deliberately not a broader type-coercion policy invented beyond the one concretely-named case, per "do not overengineer unsupported cases."

## 10. Envelope/schema enforcement

`_validate_and_compare()` (new, pure, extracted specifically for direct unit-testability without a real subprocess round-trip) now requires `"value" in parsed` for a `status == "ok"` envelope — not `.get("value")`, which previously let a missing key silently resolve to `None`, indistinguishable from a candidate that genuinely returned `None`. A missing `"value"` key is now unconditionally `MALFORMED_RESULT`. Every `"ok"` result additionally passes through the depth and non-finite-float checks before ever reaching the comparison step.

## 11. Comparison semantics

`_typed_equal(actual, expected)`: if either operand is a `bool`, both must be `bool` and equal (`type(actual) is type(expected) and actual == expected`); for `list`/`dict`, recurse element-wise/key-wise under the same rule; otherwise, ordinary `==`. Applied identically to both `actual` (parsed from the child) and `expected` (the trusted value) — the same contract on both sides, per the mission's own requirement.

## 12. Result resource bounds

The size check now measures `len(stdout.encode("utf-8"))` (actual bytes) rather than `len(stdout)` (Python string length, i.e. characters) — a real, if small, correction: multi-byte UTF-8 content could previously exceed the intended byte budget while passing a character-count check. **Explicitly still a post-capture bound, not a streaming one** — `subprocess.run(capture_output=True)` fully buffers output before this module ever sees it. A fully streaming, capture-time bound would require replacing `subprocess.run` with a manual `Popen` + incremental-read-and-kill-if-exceeded loop — judged out of scope for E0.1 per the mission's own explicit instruction not to turn this into a general resource-isolation project, and documented as a disclosed limitation, not silently left unstated.

## 13. Secrecy-qualification correction

Root cause, confirmed by re-reading the original suite's own source: all 16 attack candidates in the adversarial-secrecy loop were called with `expected="irrelevant-expected-value-not-sentinel"`, while the loop's own `leaked()` check searched for a different, unrelated, hardcoded module-level constant (`SENTINEL`) that was never passed as `expected` to any of those 16 calls. A candidate could have disclosed the *actual* expected value in full and every one of those 16 checks would still have reported PASS. Independently reproduced by Codex's own outer-sandbox-blocked run (candidate execution never happened at all; all 16 secrecy checks still reported PASS) — a vacuous-pass failure mode confirmed empirically, not merely argued.

## 14. Runtime sentinel design

Fixed with `RUNTIME_SENTINEL = "RTS_" + secrets.token_hex(16)`, generated fresh at test-run time, never hardcoded or published anywhere else in source. Every one of the 15 secrecy-loop attacks (16 minus the output-flooding case, moved to its own check — §16) is now called with this exact value as `expected`, and `leaked()` checks for this exact value's presence — the check now actually tests what it claims to test.

## 15. Execution-validity control

`_EXECUTED_OUTCOMES = {CORRECT, INCORRECT, CANDIDATE_ERROR}` — an outcome outside this set (`TIMEOUT`, `SANDBOX_INFRASTRUCTURE_ERROR`, `CHILD_TERMINATED_UNVERIFIED`, `MALFORMED_RESULT`) means the candidate's own logic never demonstrably ran to a real conclusion, and a secrecy check against such a result is now reported as **invalid evidence**, not a vacuous PASS — directly closing the exact gap Codex's blocked-sandbox run exposed. During construction, this control immediately caught three real instances of its own necessity: the `globals()`, frame-inspection, and output-flooding attacks' own naturally large return values were being rejected as `MALFORMED_RESULT` (oversized) *before* the sentinel check could mean anything — fixed by truncating the first two to fit the (correctly tightened) size contract so they produce real, executed, checkable results, and by moving output-flooding to its own dedicated check (its point is that oversized output is safely rejected, not that it doesn't contain a sentinel it was never given).

## 16. Positive control

`old_pattern_grade()` (the safe, local, synthetic same-module reproduction, unchanged) is now also run with `RUNTIME_SENTINEL` specifically (section 7d), directly pairing with the corrected secrecy methodology: confirmed the old pattern *does* disclose the runtime sentinel when deliberately shared, and confirmed E0, given the identical attack and the identical sentinel, does not — proving the qualification method can detect disclosure when it is actually present, not merely that E0 happens to look clean against an unrelated check.

## 17. Documentation corrections

Applied directly in source (`trusted_evaluator.py`/`candidate_worker.py` docstrings), not merely in this report: (1) "fork/exec denied by omission" corrected to name `process-exec*`'s real, explicit allowance and fork's real, by-omission denial, with the practical consequence (subprocess-spawning fails via fork, not exec) stated precisely. (2) "the expected value's only existence is in one stack frame" corrected to state plainly that this describes what `run_case()` itself does, not a guarantee about what a caller may separately retain. (3) The fd-suppression claim narrowed from an unconditional "structural guarantee" to a statement of exactly what was demonstrated (two specific, real attack shapes) and an explicit acknowledgment that worker and candidate code share one process/address space. (4) "typed bounded JSON" replaced with a precise description of what is now actually enforced (explicit domain, depth bound, non-finite rejection, byte-based size bound, required-value-key check, type-strict bool/int comparison) and what remains a disclosed residual (a post-capture, not streaming, bound; no duplicate-JSON-key canonicalization beyond Python's own last-key-wins default). (5) "nothing sentinel-bearing anywhere on disk" narrowed to the precise claim it can actually support: this module never writes the expected value anywhere, which is a distinct, narrower claim than "the acceptance suite's own literals are secret" — the suite's literals are public, checked-in source, and are never used as if they were not.

## 18. Original-suite results

**35 passed, 0 failed** — identical count, identical names, identical order, in sections 1/3/4/5/6, reproduced twice (once immediately after the `candidate_worker.py`/`trusted_evaluator.py` repair, before touching the test file at all — confirming the repair alone introduced no regression — and again after the test-file corrections). Section 2's 16 original attack categories are still present, in the same shape, with the demonstrated methodology bug fixed (§13-§16) rather than the checks being deleted or their count silently reduced — the mission's own explicit "preserve traceability... do not delete inconvenient tests" instruction is satisfied by fixing the bug in place, not by removing the section.

## 19. New E0.1 tests

22 new checks, all added specifically because of a named Codex finding, none added merely to inflate the count: 5 direct failure-attribution tests (§7 of the suite: SystemExit, `os._exit`, a genuine sandbox-launch failure via a test-only `sandbox_profile` override pointing at a nonexistent path, an ordinary-exception regression, a timeout regression); 1 strongest-counterexample reassessment (§18 of the mission — see §20 below); 13 result-contract tests (§7c: missing value, explicit null, bool/int both directions, recursive bool-strictness inside a list, NaN, inf, excessive nesting, valid boundary depth, empty list, empty dict, unsupported nested type); 3 positive-control/execution-validity tests (§7d). All 22 pass.

## 20. Strongest-counterexample reassessment

Codex's strongest counterexample (§18 of the independent validation): *a future adaptive policy could succeed on easy cases and terminate on hard ones; if those terminations are classified as infrastructure and excluded, measured correctness can rise without competence improving.*

**Reassessed after the repair: this counterfeit path no longer exists for the demonstrated, realistic mechanism.** `SystemExit` — the natural, idiomatic way real Python code "gives up" — is now unconditionally classified `CANDIDATE_ERROR`, never `SANDBOX_INFRASTRUCTURE_ERROR`, confirmed directly by a dedicated regression test (§7b: "a candidate 'giving up' via SystemExit can no longer obtain an infrastructure exemption"). `SANDBOX_INFRASTRUCTURE_ERROR` is now reachable only via a confirmed, trusted-launch-evidence-backed signature (exit code 65, sandbox-exec's own documented profile-apply-failure convention, or a real `OSError` from `subprocess.run` itself failing to launch at all) — neither of which any candidate code can trigger by choosing how to terminate. The one honestly-remaining gap, stated plainly rather than hidden: `os._exit()` and a genuine interpreter-level fault are still mechanically indistinguishable from each other by this module, and land in the new `CHILD_TERMINATED_UNVERIFIED` category — but this category is explicitly, by design and by its own docstring, **not** eligible for automatic infrastructure-exclusion by any future aggregation layer (no such layer exists yet — this is a stated constraint on one that might be built later). A policy that learned to call `os._exit()` on hard cases would have those cases counted as uncertain-but-attributable, never silently vanish from a denominator the way the counterexample describes. **Verdict: CLOSED for the demonstrated mechanism (SystemExit); explicitly bounded, not silently ignored, for the mechanically-uncatchable residual (`os._exit`/interpreter faults).**

## 21. Remaining limitations

Unchanged from the original E0 report's own honest disclosure, now sharpened by this session's independent confirmation: `echo_sandbox.sb`'s unrestricted `(allow file-read*)` remains real and unaddressed — deliberately, per this mission's explicit stop boundary (§22). `mach-lookup`/`ipc-posix-shm` as a possible covert channel remains untested. Process/sibling enumeration beyond a bare `getppid()` remains untested. `CHILD_TERMINATED_UNVERIFIED`'s two possible real causes (`os._exit`, a genuine interpreter fault) remain mechanically indistinguishable from each other, though both are now honestly labeled rather than either falsely excused or falsely blamed. The post-capture (not streaming) size bound remains a real, disclosed gap (§12).

## 22. Real-task integration boundary

**REMAINS CONDITIONAL, unaffected by this mission's repairs, exactly as instructed.** No real hidden AP-0 artifact was connected, moved, or referenced. The integration precondition is stated here, not resolved: *before real hidden tasks are attached, protected cases, expected values, seeds, world/reference artifacts, diagnostics, temporary copies, and concurrently active protected artifacts must be absent from candidate-readable locations, or candidate read access must be appropriately restricted.* This is a future, separate integration-qualification mission, not attempted here.

## 23. Diff review

`candidate_worker.py`: two `except Exception as e:` → `except BaseException as e:` (exec block, call block), plus expanded docstring documenting why and what remains uncatchable. `trusted_evaluator.py`: `Outcome` gained `CHILD_TERMINATED_UNVERIFIED`; new module-level `_MAX_DEPTH`, `_SANDBOX_APPLY_FAILURE_EXIT_CODE`, `_depth_within_limit()`, `_contains_non_finite()`, `_typed_equal()`, `_validate_and_compare()` (the comparison logic extracted from `run_case()`'s tail into its own pure, directly-testable function); `run_case()` gained an optional `sandbox_profile` test-only parameter, narrowed its `subprocess.run` exception handling from bare `Exception` to `OSError`, split its nonzero-exit-code handling into the confirmed-infra-vs-honestly-uncertain branches, switched the size check to byte-based measurement, and now delegates final validation to `_validate_and_compare()`; docstrings corrected per §17. `scripts/verify_rung1_e0_trusted_evaluator.py`: sections 1/3/4/5/6 byte-for-byte unchanged in assertion logic; section 2's attack loop now uses `RUNTIME_SENTINEL` and an execution-validity gate, with three attack payloads adjusted to produce real, checkable results under the tightened size contract and output-flooding moved to its own dedicated check; a new section 7 (four subsections) added.

## 24. Integrity verification

`git rev-parse HEAD` before and after: identical (`2fba42644c82b9f7096276f4dd338d615cf1bcce`). `git status --porcelain` diffed against the pre-mission snapshot: zero new or removed entries. The acceptance suite was run three times across this mission (once against the repaired evaluator with the *original*, unmodified test file, to isolate the evaluator repair's own effect; once after the initial test-file update, which surfaced the three execution-validity findings in §15; once after fixing those three payloads) — all runs stable, final result **57 passed, 0 failed**, reproduced identically on a fourth confirmation run.

## 25. Final verdict

**E0.1 QUALIFIED.**

## 26. Recommendation

Return to Codex for independent requalification of this specific repair, per the mission's own closing instruction. Do not begin G0. Do not attach real hidden AP-0 artifacts until the filesystem-read integration precondition (§22) receives its own dedicated qualification pass.

---

**HISTORICAL SHARED-PROCESS EXPOSURE:** REMOVED

**EXPECTED VALUE ENTERS CANDIDATE EXECUTION:** NO

**CANDIDATE-CAUSED TERMINATION ATTRIBUTION:** QUALIFIED

**INFRASTRUCTURE FAILURE ATTRIBUTION:** QUALIFIED

**RESULT DOMAIN:** FROZEN

**SUCCESS ENVELOPE:** QUALIFIED

**COMPARISON SEMANTICS:** QUALIFIED

**RESULT RESOURCE BOUND:** QUALIFIED

**RUNTIME SECRET QUALIFICATION:** QUALIFIED

**EXECUTION-VALIDITY CONTROL:** QUALIFIED

**POSITIVE DISCLOSURE CONTROL:** PASS

**ORIGINAL 35 CHECKS TRACEABLE:** YES

**ORIGINAL REGRESSION SUITE:** PASS

**NEW E0.1 TESTS:** PASS

**SELECTIVE-EXCLUSION COUNTEREXAMPLE:** CLOSED

**FILESYSTEM ARTIFACT ISOLATION:** DEFERRED-TO-INTEGRATION

**REAL-TASK INTEGRATION:** CONDITIONAL

**PRODUCTION ECHO MODIFIED:** NO

**AP-0 MODIFIED:** NO

**SANDBOX PROFILE MODIFIED:** NO

**G0 STARTED:** NO

**LEARNING TRIALS RUN:** NO

**GIT HEAD CHANGED:** NO

**E0.1 VERDICT:** QUALIFIED

**AUTHORIZATION TO BEGIN G0:** NO

**1. What exactly caused Codex's `SystemExit(7)` case to be mislabeled?** `candidate_worker.py` caught only `Exception`, not `BaseException`, around candidate execution — `SystemExit` is not an `Exception` subclass, so it propagated out of the worker entirely, terminating the process with a real nonzero exit code that the controller then treated as trusted evidence of an infrastructure fault, when no evaluator component had actually failed.

**2. What now distinguishes candidate failure from genuine infrastructure failure?** `SystemExit`/`KeyboardInterrupt` are now caught inside the worker itself and reported as an ordinary `candidate_error`. A genuine infrastructure failure is now classified only from confirmed, trusted-launch evidence — a real `OSError` from `subprocess.run` itself, or the sandbox's own documented exit-code-65 profile-apply-failure signature — never from a bare nonzero exit code alone.

**3. Can candidate-caused termination still remove a failed case from the future denominator merely by changing how the candidate fails?** No, for `SystemExit` specifically — confirmed by a dedicated regression test. For the mechanically-uncatchable residual (`os._exit`, a genuine interpreter fault), the new `CHILD_TERMINATED_UNVERIFIED` category is explicitly documented as not eligible for automatic infrastructure-exclusion by any future aggregation layer.

**4. What exact result types are now permitted?** `int`, `bool`, finite `float`, `str`, `list`, `dict` with string keys, and `None` — nested no deeper than 6 levels.

**5. Are `True` and `1` equivalent under the frozen contract? Why?** No. `_typed_equal()` requires both operands to be `bool` if either one is, applied recursively — the more rigorous choice for a scientific measurement instrument, closing the gap Codex named where Python's own default equality would otherwise treat them as the same.

**6. Can missing `value` still silently become null?** No. `_validate_and_compare()` requires the `"value"` key to be literally present for a `status: "ok"` envelope; its absence is unconditionally `MALFORMED_RESULT`, distinguishable from an explicit `"value": null`.

**7. What effective result-size/resource bound is now enforced?** A 4096-byte cap on the child's full stdout, now measured in actual UTF-8 bytes rather than characters — still a post-capture bound (the full output is buffered by `subprocess.run` before this check runs), not a streaming one; this remains a disclosed, out-of-scope-for-E0.1 limitation.

**8. Does the secrecy qualification now use the actual runtime-generated expected secret?** Yes — every secrecy attack is called with `RUNTIME_SENTINEL`, a fresh `secrets.token_hex(16)` value generated at test-run time, as its actual `expected` argument, and `leaked()` checks for that exact value.

**9. Can those secrecy checks pass if candidate execution never occurred?** No — an execution-validity gate now requires the outcome to be `CORRECT`/`INCORRECT`/`CANDIDATE_ERROR` (proof the candidate's own logic ran to some real conclusion) before a negative (no-leak) result is trusted; any other outcome is reported as invalid evidence.

**10. Does the positive control prove the qualification method detects deliberate disclosure?** Yes — the same runtime sentinel, deliberately shared via the old same-module pattern, is confirmed disclosed; the identical attack against E0 is confirmed not disclosed.

**11. Did all original E0 behavior remain traceable?** Yes — all 35 original checks, same names, same order, same assertions, still pass; none was deleted or silently altered.

**12. What new tests were added specifically because of Codex?** 22: five failure-attribution tests, one strongest-counterexample regression, thirteen result-contract tests, three positive-control/execution-validity tests — every one traces to a specific, named finding in the independent validation report.

**13. What claims from the original builder report were corrected?** The fork/exec sandbox claim, the "one stack frame" expected-value claim, the fd-suppression scope claim, the "typed bounded JSON" characterization, and the "nothing sentinel-bearing on disk" framing — all corrected in source docstrings, not only in this report.

**14. Is E0.1 now independently ready to return to Codex for requalification?** Yes — that is this mission's own explicit final recommendation.

**15. What remains before real hidden AP-0 artifacts can be attached?** A dedicated filesystem-read-isolation qualification pass, restricting (or demonstrating the equivalent of restricting) candidate reads to only its permitted source/input, with real hidden case/answer/world/seed artifacts and diagnostics confirmed absent or unreachable from any candidate-readable location — explicitly deferred, not attempted here.
