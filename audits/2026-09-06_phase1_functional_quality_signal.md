# Phase 1 — Functional Quality Signal (implementation + validation)

Per explicit Phase 1 authorization following Phase 0's "HYPOTHESIS STRONGLY SUPPORTED" verdict
(`audits/2026-09-06_phase0_reward_signal_verification.md`). Scope: build and validate a functional
execution signal capable of distinguishing working code from broken code, using the existing sandbox
infrastructure. **Not** "fix Echo." Nothing beyond this scope was attempted.

---

## 1. Implementation Summary

A new `--mode=functional_verify` in `sandbox/safe_exec_wrapper.py` — the same real kernel-level
Seatbelt sandbox (`echo_sandbox.sb`) and write-blocking patches self-edit's own F2 gate already
trusts, extended rather than duplicated. After a candidate module imports, it enumerates every
top-level function/class *defined in that module* (not merely imported) and smoke-tests each with a
minimal synthetic call, catching genuine runtime exceptions (`NameError`, `AttributeError`,
`TypeError`, blocked writes, etc.) that no static AST check can see.

A new, entirely standalone module, `app/core/functional_quality.py`, orchestrates this from the
Python side and computes an explicit, documented `combined_score` alongside the untouched original
AST score — but **is not imported by anything in the live pipeline**. Nothing about self-edit's real
deployment gate, RiverBrain's real training, or any autonomous loop changed today.

---

## 2. Files Changed

| File | Change | Forbidden-target? |
|---|---|---|
| `sandbox/safe_exec_wrapper.py` | Additive only — one new `elif` branch (+92/-2 lines, confirmed via `git diff --stat`). Existing `import`/`script`/`apply_to_code` modes' code paths are byte-identical to before. | No |
| `app/core/functional_quality.py` | New file. | No |
| `scripts/verify_functional_quality_signal.py` | New file — discrimination test matrix. | No |
| `echo_quality_scorer.py` | **Not touched.** | No (but confirmed untouched anyway) |
| `self_edit_manager.py` | **Not touched.** | No (but confirmed untouched anyway) |
| `echo_model_orchestrator.py` | **Not touched — the one file that would have required stopping and showing a diff first.** | **Yes — confirmed zero edits, per `git status`.** |

---

## 3. Exact Functional Scoring Definition

Four states, chosen specifically so a sandbox/harness-level failure can never be confused with a
candidate-level one:

- **`verified_success`** — the module imported and at least one top-level callable was smoke-tested
  with none raising.
- **`verified_failure`** — the module imported and at least one smoke-tested callable raised, **or**
  the module failed to import at all (treated as the candidate's own fault, consistent with how this
  codebase's existing F2 gate already judges import failures).
- **`not_applicable`** — the module imported cleanly but defined zero testable top-level callables
  (e.g. pure constants), or every candidate had an unsupported signature (2+ required params —
  skipped rather than guessed, a real, disclosed scope limit, not a false confidence).
- **`sandbox_infra_failure`** — the subprocess itself didn't complete cleanly for a reason unrelated
  to the candidate's own logic: a timeout (`timed_out: true`), or no informative traceback at all.
  Also tracked separately: `blocked_write: true` when the candidate attempted a real write outside
  its scratch directory — a distinct, real signal, never folded into either success or failure.

`combined_score` (explicit formula, documented in the module docstring, computed but never fed
anywhere live during this phase):

```
functional == verified_failure                       → combined = 0   (overrides AST entirely)
functional == verified_success                        → combined = max(ast_score, 3)
functional in (not_applicable, sandbox_infra_failure)  → combined = ast_score  (honest fallback)
```

---

## 4. Sandbox Integration Path

`app/core/functional_quality.functional_execution_score(code)` → writes `code` to a fresh
`tempfile.TemporaryDirectory` → `subprocess.run(["sandbox-exec", "-f", echo_sandbox.sb, "-D",
"SCRATCH=...", python3, safe_exec_wrapper.py, scratch, candidate.py, "--mode=functional_verify",
"--", output.json], timeout=N)` → parses the JSON result file written inside `SCRATCH` (the only
place the sandbox profile permits writes) → classifies into the four states above. This is the exact
subprocess-invocation shape already established by `self_edit_manager.py:_run_apply_to_code_sandboxed()`
(Finding 69), reused rather than reinvented.

---

## 5. Old vs. New Scoring Comparison

Run against all 25 real, currently-retained self-edit backups (`app/core/self_edit_backups/*.py`) —
the same corpus Phase 0 found **all scoring a perfect 3-4/4 under the old AST-only scorer, with zero
discrimination power**:

| Metric | Old (AST-only) | New (functional) |
|---|---|---|
| Distinct scores produced | 2 values (3 or 4), no candidate below the recalibrated ceiling | 4 distinct outcomes |
| Real discrimination | None — every file ties near the top | **16/25 (64%) `verified_failure` → combined 0; 8/25 (32%) `verified_success` → combined 3-4; 1/25 (4%) `not_applicable`** |

This is not a constructed example — it's the real historical population Phase 0 already established
is opaque to the old scorer, now measurably differentiated for the first time.

---

## 6. Deterministic Test Matrix

All cases deliberately take a single `code: str` parameter — see §9 for why this choice itself is a
disclosed, load-bearing limitation.

| Case | AST score (old) | Functional outcome | Combined score |
|---|---|---|---|
| A — Simple correct (`strip_blank_lines`) | 3 | `verified_success` | 3 |
| B — Complex correct (`normalize_code`, if/elif/try/for) | 3 | `verified_success` | 3 |
| C — Simple broken (undefined name) | 2 | `verified_failure` | **0** |
| D — Complex broken (for/if/try + undefined class) | 3 | `verified_failure` | **0** |
| E — Real deployed `self_edit_generated.py` (known-bad) | 4 | `verified_failure` | **0** |

Case E's per-function breakdown, real, not constructed: `HealthMonitor`/`log_call` executed cleanly;
`generate_and_modify_code` and `run_code_generator` both raised `NameError: name 'logging' is not
defined`; `get_shortened_code` raised `PermissionError: [SANDBOX] Write blocked outside scratch dir`
— a genuine attempted write to `shortened_codes.txt` in the real project root, caught by the same
sandbox write-guard that already protects production, now visible as data rather than silently
denied and forgotten.

---

## 7. Test Results

```
Criterion 1 (known-working -> positive functional result):  PASS  (A=verified_success, B=verified_success)
Criterion 2 (known-broken -> negative functional result):   PASS  (C, D, E all verified_failure)
Criterion 3 (complex-broken NOT >= verified-correct):        PASS  (D.combined=0 < A.combined=3)
Criterion 3b (real E vs A):                                  PASS  (E.combined=0 < A.combined=3, despite E's AST score of 4 being HIGHER than A's 3)
```

Criterion 3b is the single most direct proof this phase set out to establish: the real, currently-
deployed file scores *higher* on the old metric (4 vs 3) while being *functionally broken*, and the
new combined score correctly inverts that ranking.

---

## 8. Regression Results

| Check | Result |
|---|---|
| `--mode=import` (F2's real gate, `self_edit_manager.test_code_in_sandbox()`) against known-good code | PASS, unaffected |
| `--mode=apply_to_code` against a fresh synthetic hook (isolated from the real `self_edit_generated.py` to avoid touching production state) | PASS, unaffected — `SANDBOX_OK`, correct output round-tripped |
| `--mode=script` (`sandbox.run_script.run_sandbox_script_isolated()`) | PASS, unaffected |
| `scripts/verify_liveness_ledger.py` (full discrimination suite, unrelated to this change) | All cases pass, zero regressions |

No existing test suite failures, baseline or otherwise — nothing broke.

---

## 9. Environmental Limitations (disclosed, not smoothed over)

- **Only 0 or exactly 1 required-parameter callables are smoke-tested; 2+ required params are
  skipped, never guessed.** A deliberate, conservative scope limit stated in the code and in
  `safe_exec_wrapper.py`'s own docstring — guessing multiple argument values has high false-positive
  risk this phase was not designed to absorb.
- **The single synthetic argument is always the string `"test"`.** This was discovered, live, during
  this session's own test construction: an initial draft of Case A/B used generic, non-string-typed
  functions (`add(a, b)`, `classify_number(n)`) and produced misleading results — a 2-param function
  was correctly skipped rather than tested (not a bug, but not useful evidence either), and the
  numeric function raised a real but *false* `TypeError` purely from being handed a string. Corrected
  by rewriting the test cases to match this codebase's actual domain — every one of the 25 real
  self-edit backups sampled takes a `code`/`original_code` string parameter, so `"test"` is a
  reasonable synthetic input *for this specific system* — but this remains a real, permanent property
  of Phase 1's implementation: **a hypothetical self-edit family whose target function expects a
  non-string type would see elevated false-failure risk.** Not fixed in this phase (would require
  either type-annotation-aware argument synthesis or per-family expected-input specs, both explicitly
  larger changes than "smallest necessary").
- **Only module-level functions and bare class construction are tested — not individual class
  methods.** A stated scope boundary, not an oversight.
- **This does not verify semantic correctness against any spec.** No such spec exists per self-edit
  family in this codebase today, and building one was out of scope. It answers exactly one question:
  does the candidate's own code raise when invoked with a generic, non-adversarial input. That
  question turned out to be sufficient to catch the real, already-diagnosed `CodeGenerator` bug and
  64% of the real historical corpus — but it is not a general correctness prover, and should never be
  described as one.

---

## 10. Evidence River Was Not Retrained

- `app/core/functional_quality.py` contains zero references to `RiverBrain`, `river_brain`, or
  `get_river_brain` anywhere (grepped directly, confirmed above the line citing this exact claim in
  its own docstring).
- `memory/river_brain.pkl`'s mtime (04:36 local) is attributable to the live production server's own
  pre-existing ~60s background writer thread (Finding 89's already-documented mechanism), not this
  session's testing — this session never called `.learn()`, `.save()`, or any RiverBrain method.
- `echo_model_orchestrator.py` — zero diff, confirmed via `git status`/`git diff --stat`.

## 11. Evidence No Phase 2 Signal Was Connected

- `self_edit_manager.py` — zero diff, confirmed via `git status`. The fitness gate at line 2119-2146
  still calls only the original, unmodified `_score_response_quality()`.
- `echo_quality_scorer.py` — zero diff.
- Repo-wide grep for `functional_quality` outside the three new/changed files above: one match, a
  prose mention inside `safe_exec_wrapper.py`'s own docstring (pointing at this report) — not an
  import, not a call site.

---

## 12. Unexpected Findings

1. **64% real functional-failure rate among files that all scored at or near the AST scorer's
   ceiling** — a starker number than anticipated. Phase 0 established the old scorer couldn't
   discriminate; this phase establishes that when it can't discriminate, the true population isn't
   "mostly fine, a few outliers" — it's closer to a coin flip weighted toward broken.
2. **The synthetic-argument false-failure risk (§9)**, found by the test construction process itself
   catching its own flawed first draft — exactly the kind of self-correcting discipline this
   investigation lineage has repeatedly demonstrated elsewhere in this codebase, now demonstrated
   here too.
3. **A real attempted write outside the project's write boundary was caught and correctly blocked**
   (Case E's `get_shortened_code`) — not a new gap, the existing sandbox write-guard already prevents
   this in production; what's new is that this specific failure mode is now visible as classified
   data (`verified_failure`) rather than something that would have silently succeeded or failed
   opaquely if this file were ever actually invoked.

---

## 13. Acceptance Criteria — Pass/Fail

| # | Criterion | Result |
|---|---|---|
| 1 | Known-working code receives a positive functional result | **PASS** |
| 2 | Known-broken code receives a negative functional result | **PASS** |
| 3 | Complex-broken candidate does not tie/beat verified-correct on AST complexity alone | **PASS** |
| 4 | Sandbox infra failures stay distinguishable from candidate failures | **PASS** (4-state design; `timed_out`/`blocked_write` tracked separately; not exercised by a real infra failure in this session's runs, but the code path exists and is structurally separate from `verified_failure`) |
| 5 | Existing AST information remains available for comparison | **PASS** — `ast_score` returned unchanged, alongside, never overwritten |
| 6 | No unintended River training occurs | **PASS** — see §10 |
| 7 | No unrelated production behavior changes | **PASS** — see §11, plus full regression suite (§8) |
| 8 | Deterministic tests demonstrate the above | **PASS** — `scripts/verify_functional_quality_signal.py`, committed nowhere, run live this session |

---

## 14. Recommendation for Next Phase

**The functional signal works, discriminates correctly, and is fully isolated from production.**
Per the explicit Phase 1 stop condition, no further action was taken. Two honest notes for whoever
reviews this before authorizing anything further:

- The 2+-required-param skip and the string-only synthetic argument (§9) are the most likely places
  a future phase would want to invest, if broader coverage is ever wanted — not because anything here
  is wrong, but because they're the two clearest edges of what this phase deliberately chose not to
  attempt.
- This report makes no recommendation about *whether or how* to eventually connect this signal to
  RiverBrain training or the self-edit deployment gate — that is explicitly Phase 2+ territory, not
  something Phase 1's own evidence should be read as arguing for by default.

**STOP. Awaiting explicit authorization for anything beyond Phase 1.**
