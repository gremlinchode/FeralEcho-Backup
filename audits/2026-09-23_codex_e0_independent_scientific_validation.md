# Stage E0 — Independent Scientific Validation

Date: 2026-09-23  
Reviewer: Codex  
Scope: scientific validity and information flow of the implemented E0 evaluator; no production changes, repairs, G0, Stage 1, or learning trials.

## 1. Executive verdict

**E0 CONDITIONAL. REAL-TASK INTEGRATION CONDITIONAL.**

**VALIDATED.** E0 removes the particular same-process defect that motivated it: the expected argument is absent from the child-launch payload, and expected-versus-actual comparison runs in the parent after child exit. The unchanged acceptance suite reproduced **35 passed, 0 failed, no skips** when its own sandbox could launch. Its synthetic old/new comparison confirms that a candidate which reads the old module-level expected value gets a `NameError` under E0.

**VALIDATED.** Complete scientific qualification nevertheless requires more than that separation. One harmless additional case, `raise SystemExit(7)`, was classified as `SANDBOX_INFRASTRUCTURE_ERROR`. Candidate termination is not evidence that infrastructure failed. The engineering specification excludes genuine infrastructure failures from the primary denominator; applying that rule to E0's current labels could selectively remove candidate failures. This is a concrete measurement defect, not a hypothetical operating-system exploit.

**OBSERVED.** The advertised typed, strictly bounded result contract is also incompletely implemented. The parent checks for a dictionary and a `status` key, but does not require `value` for an `ok` result, enforce a task return type or a fixed nesting limit, or implement a streaming byte bound. These limitations do not demonstrate expected-answer disclosure. They prevent endorsing the builder's broader claim that every required part of the measuring instrument is qualified.

**INFERRED.** Broad filesystem reads should be **HARDENED BEFORE REAL-TASK INTEGRATION**. They do not themselves recreate the old shared Python namespace or demonstrate disclosure of a fresh, parent-only secret. However, the claim that there is “nothing sentinel-bearing anywhere on disk” is false: the public acceptance script contains both synthetic sentinel literals. Public fixture answers are not evidence that protected experimental answers are inaccessible. Real hidden task artifacts require a separate access-boundary check.

The conclusion is deliberately narrower than “the evaluator is broken” or “35 tests prove it sound”: **the parent/child comparison separation works; the complete scientific instrument remains conditional because failure attribution and result-contract enforcement are insufficient.** No repair was made.

## 2. Repository provenance

**OBSERVED.** Initial capture: `2026-09-23T18:58:35.390142+00:00`. HEAD:

```text
2fba42644c82b9f7096276f4dd338d615cf1bcce
```

Branch `main`, upstream `origin/main`, ahead 17, behind 0. No staged changes. Before this review there were **28 modified tracked files and 287 untracked files**, using `git --no-optional-locks status --porcelain=v2 --branch --untracked-files=all`. Its complete text fingerprint was:

```text
SHA-256 248181bd39b64ab101468109859eb08eed9d0d06c19d7a0dff4a8345331ac3c4
```

The tracked modifications were already present:

```text
CLAUDE.md
PENDING_DECISIONS.md
app/core/echo_ground_truth.py
app/core/liveness_ledger.py
app/core/provenance_check.py
app/core/river_deliberation.py
app/core/self_edit_attempt_ledger.py
app/core/self_edit_convergence.json
app/core/self_edit_generated.py
app/core/self_edit_manager.py
app/core/shadow_model.py
app/core/snapshot_manager.py
app/core/temporal_environment.py
app/emergent_scheduler.py
app/maintenance/night_cycle.py
audits/2026-09-14_tier5_followup_experiment_design.md
claude_relay/.last_seen_from_air.json
claude_relay/README.md
claude_relay/from_m5.md
claude_relay/relay.py
logs/janitor_report.json
research/OPEN_QUESTIONS.md
run.py
sandbox/safe_exec_wrapper.py
sandbox/scripts/temp_self_edit.py
scripts/verify_liveness_ledger.py
scripts/verify_provenance_check.py
staging/self_edit_candidate.py
```

Untracked counts by top-level path were `.claude: 11; app: 58; audits: 188; claude_relay: 2; codex_relay: 3; hub: 5; research: 8; scripts: 12`. These are pre-existing work, not this review's additions.

**OBSERVED.** Compared with the retained state from completion of the earlier preimplementation gate, the six new status entries were precisely:

- `app/experiments/rung1/__init__.py`
- `app/experiments/rung1/candidate_worker.py`
- `app/experiments/rung1/trusted_evaluator.py`
- `scripts/verify_rung1_e0_trusted_evaluator.py`
- `audits/2026-09-23_rung1_e0_trusted_evaluator_implementation.md`
- `audits/2026-09-23_rung1_engineering_gate_specification.md`

The first four are the E0 code/suite additions. The other two document the work. The builder's “222 entries” uses a different status presentation; it is not comparable to an all-untracked-files count without expanding directory entries.

Fingerprints taken before analysis and verified unchanged after testing:

| File | SHA-256 |
|---|---|
| `app/experiments/rung1/__init__.py` | `94776304eb120f53b789d446942c63423d6c85fdece6b1fb313565da5f315568` |
| `app/experiments/rung1/candidate_worker.py` | `2fa7a5e5ecde3f07b999166967d472bf9c0a3fcde612bdf7416d26e3353b3778` |
| `app/experiments/rung1/trusted_evaluator.py` | `80408ef8ce3680d3e10facafd273e707e106eb3c948b25770d97e07f6a456894` |
| `scripts/verify_rung1_e0_trusted_evaluator.py` | `88179794f963e69a7ff3c2ab713aa3025eefe97061e2dfeaea68311de4489db9` |
| E0 builder report | `85aadf5878d5c4122519ef7ce4082fa5132b6baa1a1f0b8f43ed671caa962629` |
| Engineering gate specification | `834a1e7a414409e95f5fab8a78ff2944c51ada074dfa315cea0e2d84557d27f7` |
| Final preimplementation gate | `7f89748779fae16c1d8c76b847e5c6a86184f913372bc1cb103151ea3037da01` |
| `sandbox/echo_sandbox.sb` | `49eb3eab677af662e05cbae72fc27bde53d2650ba4f3eee05c98f6a31df4419e` |
| `sandbox/safe_exec_wrapper.py` | `7605102d2eb0b9a25c6e5e2704a1efff849a06743334160c4e92a84b170f8cc7` |

**VALIDATED.** At `2026-09-23T19:09:13.652619+00:00`, after all candidate execution, HEAD, normalized tracked/untracked status entries, and those fingerprints were unchanged. Thirteen relevant production/AP-0/sandbox files also matched their pre-E0 fingerprints retained from the earlier gate, including model orchestration, RiverBrain deliberation, the attempt ledger, self-edit manager, Ollama handler, AP-0 oracle/tasks/client/jail/worlds, and both sandbox files. Source search found no production import of this new E0 package. This supports the claimed additive implementation; it does not pretend the pre-existing dirty tree is a clean checkout or provide a cryptographic baseline for every unrelated file.

**VALIDATED.** Final verification after creating this report found the same HEAD, the same 28 tracked modifications, and **288 untracked files**, with this report as the only new status entry. All 20 reviewed/baseline source and report fingerprints checked at the post-test snapshot remained unchanged.

Exactly one permanent file was created by this review:

```text
audits/2026-09-23_codex_e0_independent_scientific_validation.md
```

The evaluator's per-call temporary scratch directories were created and cleaned by its existing `TemporaryDirectory` lifecycle. No permanent test file was added. Parent test invocations used `-I -B`; E0 already uses `-I -B -S` for children. No earlier report was overwritten. No production runtime or sealed AP-0 corpus was inspected or exercised.

## 3. Source reconstruction

**OBSERVED.** I read the implementation and acceptance source before the builder report. The relevant implementation is small and uses the standard library rather than live Echo components.

### Expected information

[trusted_evaluator.py:111](/Users/richietate/Desktop/FeralEcho/app/experiments/rung1/trusted_evaluator.py:111) receives `expected` from its caller. It does not create the expected value or independently verify the oracle that produced it. In the suite, expected values are ordinary literals or module-level constants.

During `run_case`, the expected object remains in the trusted parent, also potentially referenced by its caller. The docstring's assertion that its “only” existence is in that stack frame is stronger than the implementation can guarantee. There is no secure-erasure operation and none is needed for the demonstrated same-process separation.

### Candidate information

The parent writes the exact supplied candidate source to a new scratch `candidate.py`. It sends `{"args": call_args}` as a JSON line over stdin. Launch arguments expose the worker path, candidate path, and requested function name, as well as the sandbox profile and scratch configuration to the launcher.

The child receives the explicit environment `PATH=/usr/bin:/bin; LANG=C; LC_ALL=C`, not the parent environment. It starts in its scratch directory. `close_fds=True` prevents ordinary additional parent descriptors from surviving execution; standard input/output/error are deliberately connected. A fresh interpreter starts with `-I -B -S`. This is isolation from Python startup/site state, not a filesystem access restriction.

### Execution and return

[candidate_worker.py:95](/Users/richietate/Desktop/FeralEcho/app/experiments/rung1/candidate_worker.py:95) parses the argument list, reads the candidate file, compiles/executes it into a fresh namespace, looks up the requested function, and calls it. Candidate top-level execution and the function call run with descriptor 1 redirected to `/dev/null`.

Normal completion is serialized as `{"status":"ok","value":result}`. Ordinary `Exception` subclasses are converted to an error envelope. The worker contains no expected-value parameter or hidden-case table.

### Comparison and lifecycle

[trusted_evaluator.py:195](/Users/richietate/Desktop/FeralEcho/app/experiments/rung1/trusted_evaluator.py:195) obtains `actual = parsed.get("value")` and evaluates `actual == expected` in the parent. This follows the return of `subprocess.run`, so the child has exited.

Each call creates a new temporary directory and launches a new process. Cleanup encloses the return paths. This establishes a fresh Python execution context per sequential case, not universal isolation from all host state.

## 4. Information-flow model

**OBSERVED.** The source implements this flow:

```text
TRUSTED CALLER
  expected E ---------------------------+
  candidate source C ----+              |
  permitted args A ------|----+         |
  function name F -------|----|--+      |
                         v    v  v      |
TRUSTED run_case                         |
  scratch/candidate.py = C              |
  stdin JSON = {"args": A}              |
  argv = worker path, candidate path, F |
  env = explicit three-field allowlist |
                         |              |
                 process boundary      |
                         v              |
UNTRUSTED CHILD                          |
  Python runtime + worker + C + A + F  |
  broad read access allowed by profile |
  computes/reports result R            |
  stdout -> JSON envelope              |
  stderr -> diagnostic pipe            |
                         |              |
                    child exits        |
                         v              v
TRUSTED PARENT
  exit/timeout checks
  stdout size/JSON/envelope checks
  parsed R == E
    -> CORRECT / INCORRECT
  other paths -> classified error
```

| Boundary | Information actually crossing |
|---|---|
| Caller → parent | Source, function name, arguments, expected value, timeout |
| Parent → candidate scratch | Candidate source only |
| Parent → stdin | Arguments only; no expected, case table, outcome, or hidden-case count |
| Parent → launch configuration | Paths, function name, minimal environment, timeout enforcement outside child |
| Host filesystem → child | Any file otherwise readable under host permissions; no E0 read allowlist |
| Child → parent | Stdout envelope, stderr, exit status, completion/timeout; all are observations of an untrusted computation |
| Parent → caller | Outcome and optional details/diagnostics; no separate learner sanitizer yet |

**INFERRED.** The explicit launch interface is answer-separating. The independent filesystem row is a real precondition on how callers may store experimental secrets. Process separation alone does not close that row.

## 5. Historical evaluator comparison

**OBSERVED.** [oracle_runner.py:45](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/oracle_runner.py:45) concatenates candidate code and test code. [tasks.py:246](/Users/richietate/Desktop/FeralEcho/app/experiments/accumulation_probe/tasks.py:246) emits a module-level `_CASES` containing inputs and expected outputs, then calls candidate functions in that same module. Failing comparisons print expected information.

**VALIDATED.** The existing suite's safe reproduction creates a shared module with `_EXPECTED` and a candidate returning that variable. It succeeds in the old pattern. The identical candidate evaluated by E0 is classified `CANDIDATE_ERROR`, with `NameError`. Neither the real AP-0 grader nor hidden task material was executed.

**INFERRED.** This establishes removal of the specific shared-address-space defect. It does not by itself establish that arbitrary caller-side copies of expected information are inaccessible elsewhere.

## 6. Expected-result separation

**OBSERVED.** No source expression incorporates `expected` into the candidate file, stdin JSON, environment, launch arguments, or worker code. The expected container, hidden comparison state, and other cases are not serialized to the child.

There is also no E0 path that sends a diagnostic derived from a failed expected-versus-actual comparison back to the still-running candidate: comparison occurs after exit. The return object for `INCORRECT` contains the candidate's actual value, not the expected value.

**INFERRED.** For an expected value genuinely confined to trusted parent/caller memory, the inspected evaluator interface does not make it candidate-addressable. That is the strongest supported separation statement.

**UNKNOWN.** E0 cannot establish from this API that a caller has not also saved an expected table or an answer-equivalent generator state in a readable file. It does not inspect or enforce that precondition. No general host-memory or operating-system exploitation was attempted.

## 7. Answer-equivalent information review

**OBSERVED.** The E0 payload adds no task ID, seed, world label, case index, convention label, expected-derived annotation, or reference solution. Scratch names are generated independently of the expected value. The API permits any caller-supplied arguments and function name; it does not decide whether those are scientifically permissible.

Two distinctions matter:

1. **Current qualification issue:** the public suite contains its synthetic answers, including both `SENTINEL` constants at lines 27–28. A fully informed candidate designer already knows those fixtures. Their public availability is not disclosure of an otherwise private runtime value, but it makes an unconditional “no answer-equivalent information is visible” claim about that qualification corpus untenable.
2. **Future integration requirement:** a real task adapter must ensure that argument objects, names, paths, conventions, seeds, and accessible reference/generator files do not reveal hidden answers except by legitimately solving the supplied task.

**INFERRED.** No unexpected answer-equivalent field is introduced by E0's explicit interface. The published fixtures cannot certify secrecy of prospective hidden answers. Complete public task instructions are legitimate input; a hidden-case answer table is not. Those must be distinguished by the adapter's declared contract.

## 8. Filesystem visibility assessment

**OBSERVED.** [echo_sandbox.sb:28](/Users/richietate/Desktop/FeralEcho/sandbox/echo_sandbox.sb:28) allows `file-read*` without a path restriction. `-I`, a different cwd, and lack of a repository entry on `sys.path` do not revoke ordinary file reads.

The builder's assertion that no sentinel-bearing file exists is contradicted by its own suite. Likewise, returning an oversized directory listing as `MALFORMED_RESULT` does not prove the listing was unavailable inside the child. A result filter is not an input-access boundary.

**INFERRED — HARDEN BEFORE REAL-TASK INTEGRATION.** Broad reads are not alone a demonstrated leak of a fresh parent-only expected value. Public unit-test literals should not be relabeled as newly discovered private experimental answers. But those fixtures also cannot support the stronger claim that all current test answers are inaccessible.

Before attaching hidden AP-0-derived artifacts, deny candidate reads of protected case/answer/world/seed/reference artifacts, or demonstrate an equivalent isolated environment where they are absent. Cover logs, temporary copies and concurrently evaluated cases as well as the canonical corpus. Do not rely on “the evaluator itself never writes expected” when its caller may have loaded expected from a readable file.

**UNKNOWN.** This review did not inspect sealed AP-0 material or enumerate private host files. It therefore does not certify that a particular real-task directory is safe to attach. No filesystem-recovery candidate was added or run.

## 9. Candidate-result contract

**OBSERVED.** The worker normally emits one JSON object. The parent rejects empty output, output longer than 4096 characters after stripping, unparseable JSON, non-dictionaries, missing `status`, and unknown status values. Distinct concatenated JSON objects ordinarily fail `json.loads`; surrounding whitespace is accepted. No returned string is evaluated as Python, unpickled, or dynamically imported in the parent.

Actual limitations relative to engineering specification §9:

| Contract element | Actual implementation and consequence |
|---|---|
| Required success value | `parsed.get("value")` does not distinguish absent `value` from explicit JSON null. A missing value can reach comparison as `None`. |
| Task return type | No schema parameter or exact type check. Python equality equates `True` and `1`, including inside containers. This is a policy choice currently left implicit, not the specified type restriction. |
| JSON restrictions | Default encoder/parser behavior is used; non-finite floats and duplicate object keys are not explicitly rejected. This is not a strict canonical JSON contract. |
| Size bound | The check is after full capture and text decoding, and after `strip()`; it is a character-count acceptance bound, not a streaming byte or memory bound. |
| Depth bound | No declared fixed maximum nesting depth. Parser implementation limits are not the specified contract. |
| Normalization | JSON transforms tuples to lists and mapping keys to strings; the parent does not normalize `expected` symmetrically or declare allowed expected types. |
| Envelope provenance | Status and error fields are child-reported data. They cannot by themselves establish which internal event truly occurred. |

**INFERRED.** Ordinary scalar/string/dict/list examples work, but “typed bounded JSON” overstates the implemented contract. These findings came from source, without offensive parser testing.

The minimum conceptual correction is a frozen allowed input/output domain, exact envelope validation and explicit comparison semantics on both sides, with effective resource bounds appropriate to that domain. No parser or evaluator was changed.

## 10. Correctness determination

**OBSERVED.** There is exactly one `CORRECT` return path: the parent evaluates `actual == expected` as true. No printed success marker, stderr text, child `CORRECT` label, zero exit status alone, or candidate exception directly awards correctness.

**VALIDATED.** Existing tests confirm that printing a fake success envelope does not replace the ordinary returned value: returning 999 is correct for expected 999 and incorrect for expected 42.

**INFERRED.** “CORRECT requires trusted comparison” is supported. “CORRECT proves a correctly typed return satisfying the specified task” requires the result contract in §9. The parent's expected object must itself be trusted, within the permitted primitive domain, and derived from a correct oracle. The current function does not enforce those caller preconditions.

## 11. Failure taxonomy

**OBSERVED.** E0 names six useful categories, but their boundaries are not all trustworthy.

| Outcome | Source behavior | Judgment |
|---|---|---|
| `CORRECT` | Parsed value compares equal in parent | Supported under defined equality/domain |
| `INCORRECT` | Parsed value compares unequal | Supported under same conditions |
| `CANDIDATE_ERROR` | Worker catches ordinary `Exception` during exec/call or finds no callable | Useful, but incomplete |
| `TIMEOUT` | Parent catches `TimeoutExpired` | Demonstrated for supplied timeout fixture |
| `MALFORMED_RESULT` | Some input/serialization/envelope failures | Useful but schema coverage incomplete |
| `SANDBOX_INFRASTRUCTURE_ERROR` | Every nonzero child exit; any exception from `subprocess.run` | Not a reliable causal classification |

**VALIDATED — one additional harmless synthetic counterexample.** Executed unchanged E0 with:

```python
source = "def f(a):\n    raise SystemExit(7)\n"
run_case(source, "f", [0], 0)
```

Observed result:

```json
{
  "outcome": "SANDBOX_INFRASTRUCTURE_ERROR",
  "detail": "nonzero exit 7",
  "_researcher_stderr": ""
}
```

The candidate deliberately terminates its own process; no infrastructure component failed. `SystemExit` is not an `Exception` subclass caught by the worker. The parent then treats the real but candidate-caused exit code as “trusted launch evidence.” An authentic observation is not an authentic causal diagnosis.

**INFERRED.** Applying the specification's infrastructure-exclusion rule would let failure rates depend on how candidates terminate. Apparent accuracy could rise without improved solutions if failed candidates increasingly exit instead of returning wrong values. That consequence is conditional on future aggregation, not an observed learning result.

The broad `except Exception` around `subprocess.run` also includes post-launch communication/decoding failures, not just launch failures. Source-level inference: its “launch failed” description can be wrong even when the child launched.

**Verdict: FAILURE TAXONOMY NOT QUALIFIED for downstream automatic exclusions or learner feedback.** Preserve uncertain termination as such until independent controller evidence establishes infrastructure causation. A separately authorized correction must make candidate-caused termination a candidate failure under the declared budget, while retaining genuine launch/evaluator failures separately. Do not infer infrastructure causation from a child exit code alone.

## 12. Case independence

**OBSERVED.** Each `run_case` creates a unique scratch directory, new interpreter, new namespace and new argument pipe. The candidate process exits before the synchronous call returns. The parent does not send prior expected values, outputs or results into the next call.

**VALIDATED.** The existing repeated-case and sequential sentinel tests pass. The latter only checks a temporary-directory listing; it does not establish comprehensive isolation from all host state.

**INFERRED.** Per-case Python-context independence is qualified for the demonstrated sequential architecture. E0 does not impose a global serialization lock on callers. Concurrent callers, readable external caches, pre-existing answer files or shared IPC are not eliminated by constructing fresh processes. Those are integration conditions, not evidence of a current cross-case expected-value leak.

## 13. stdout/result-channel review

**OBSERVED.** [candidate_worker.py:62](/Users/richietate/Desktop/FeralEcho/app/experiments/rung1/candidate_worker.py:62) duplicates the original stdout descriptor, redirects descriptor 1 to `/dev/null`, flushes Python stdout while it is still redirected, then restores the descriptor. It applies this to both top-level candidate code and the requested function.

**VALIDATED.** The suite's `sys.stdout = sys.__stdout__` and ordinary printed-marker examples do not override the function return. Python-level stream reassignment alone still writes through descriptor 1 while it targets `/dev/null`.

**INFERRED.** This fixes the reported ordinary-output problem without asking the candidate to refrain from printing. It does not create a second trust boundary inside the child: worker machinery and candidate code share that process, and the saved output descriptor exists there. The claim that candidate-aware code categorically cannot detect or reverse any part of the redirection is not established by duplicating an already-redirected descriptor in one test.

The important supported protection is that the parent regards the child as a source of result data and performs comparison itself. It should never treat a child envelope as an authenticated verdict or infrastructure diagnosis. No attempt to circumvent descriptor or OS controls was performed.

## 14. Sandbox assumptions

**OBSERVED.** The actual profile has deny-by-default behavior, unrestricted reads, scratch-scoped ordinary writes, additional `/dev` data-write permission, explicit network denial, Mach/shared-memory allowances, and `process-exec*` permission at line 46. The builder's repeated statement that both fork and exec are denied by omission is inaccurate: exec is explicitly allowed. Fork is not generally allowed.

**VALIDATED.** The existing suite runs its network and subprocess examples. Its assertions check absence of a sentinel, not the precise operating-system error proving denial. Therefore this reproduction does not independently certify the builder's claimed `PermissionError` diagnostics merely because those tests are green.

**INFERRED.** The policy supports useful containment assumptions, especially denial of networking and ordinary writes outside scratch. The expected-value comparison does not depend on claiming a universally secure hostile-code container. Ordinary process separation, a trusted OS/interpreter, absent protected files and a correct parent comparison are the relevant assumptions. General process, IPC or machine-security testing was outside this mission and was not done.

## 15. Existing acceptance-suite results

**VALIDATED.** Exact command, with the acceptance file unchanged:

```text
/Users/richietate/miniforge3/envs/feral_echo/bin/python3 -I -B scripts/verify_rung1_e0_trusted_evaluator.py
```

Environment: macOS 27.0 arm64; pinned interpreter Python 3.12.13, conda-forge.

| Invocation | Result | Interpretation |
|---|---|---|
| Inside Codex's outer sandbox | 18 passed, 17 failed; exit 1 | Nested `sandbox-exec` could not apply its policy: exit 71, `sandbox_apply: Operation not permitted`. Candidate execution was blocked. |
| Same unchanged command with outer-sandbox execution permission | 35 passed, 0 failed; exit 0 | E0's own sandbox launched successfully; usable suite reproduction. |

No tests were skipped. The first run was an environment limitation, not evidence that E0 normally fails those 17 cases. Permission was requested through the execution tool; E0's sandbox policy was not bypassed or modified for the successful run.

Successful breakdown: 10 ordinary regression checks; 16 sentinel-absence checks; one separate stdout-return check; two cross-case checks; three trusted-score checks; one descriptor check; two old/new checks. These are assertions, not 35 independent proofs of secrecy.

The additional `SystemExit(7)` example is separate from Claude's 35 checks and is not counted as a suite failure. No model call, actual task trial, generation accounting or AP-0 Stage 1 occurred.

## 16. Acceptance-suite assessment

**Strongest test — VALIDATED.** The old/new same-source comparison directly reproduces the historical fault and tests removal of that mechanism. The paired fake-print/real-return tests also distinguish specific plausible success-marker mistakes.

**Weakest relevant area — OBSERVED.** At [suite:237](/Users/richietate/Desktop/FeralEcho/scripts/verify_rung1_e0_trusted_evaluator.py:237), all 16 secrecy examples receive expected value `"irrelevant-expected-value-not-sentinel"`, while their assertion searches for `SENTINEL`. A candidate could disclose the actual expected argument and still pass that particular sentinel check. The suite's introduction says the sentinel is used throughout; the implementation does not do that.

**VALIDATED.** In the outer-sandbox-blocked run, all 16 secrecy checks still passed without candidate execution. Thus this weakness is empirically visible, not merely a theoretical objection: the checks need an execution-validity prerequisite. The old-pattern in-memory demonstration and one cross-case absence check account for the other two passes in that blocked run.

**OBSERVED.** Additional limits:

- Public constants make the corpus unsuitable as evidence that an architecturally informed candidate cannot know fixture answers.
- Some checks accept malformed/oversized output as “no leak”; absence from the retained result is not proof of absence from child-visible state.
- `leaked()` checks the returned result object. Successful comparisons omit the actual value, so a returned matching secret is not necessarily visible to that check.
- Cross-case testing lists a temporary directory; it does not test all possible caller-side answer artifacts.
- The suite has no candidate-caused nonzero-exit classification check, task-type distinction check, or missing-value contract check.
- A direct duplicated descriptor test covers the currently redirected descriptor, not every aspect of the child protocol.

**INFERRED.** The structural absence of expected from the launch payload carries more evidential weight than the 16 negative sentinel checks. The suite needs a small, focused qualification correction: use a parent-generated, nonpublished expected sentinel; bind observations to that actual sentinel; require successful launch/execution; retain a positive control showing detection if the sentinel is deliberately supplied in a toy shared environment. Test failure attribution and the declared output domain separately. This is a recommendation, not an implemented or executed new suite.

## 17. Structural argument for qualification

**INFERRED, with explicit preconditions.**

1. The caller creates/holds a trusted primitive expected value E and keeps E and answer-equivalent protected artifacts outside candidate-accessible inputs and files.
2. `run_case` does not reference E when constructing the candidate file, stdin payload, environment, or child arguments.
3. A new executed interpreter receives source, permitted arguments and a function name, not the parent's Python heap or expected-value table.
4. The child returns an untrusted serialized result R.
5. After child exit, the trusted parent parses R and performs its own comparison with E.
6. Therefore inspecting the candidate's ordinary namespace or received evaluator payload no longer reveals E; a printed success marker alone cannot award correctness.

Steps 2–5 are supported directly by source and the narrow behavioral checks. **Step 1 is a caller/environment obligation, not an E0-enforced invariant.** The public synthetic fixture suite does not demonstrate secrecy of its literal constants. The result-domain and failure-attribution caveats also remain.

This is a sound argument for the repaired process separation. It is not an unconditional proof of the entire experimental correctness metric.

## 18. Strongest scientific counterargument

**VALIDATED / INFERRED.** The most consequential current counterexample is **selective exclusion of candidate-caused failures as infrastructure**.

A policy can produce candidates that succeed on easier cases and terminate on cases they cannot handle. E0 currently calls the terminations infrastructure errors. If subsequent analysis uses the engineering specification's infrastructure exclusions, measured correctness among retained cases can improve without any improvement across assigned cases. Every surviving `CORRECT` could be an honest parent comparison; the experiment's apparent competence would still be misleading.

**Classification: CURRENTLY UNRESOLVED as an experimental integration policy, with the causal misclassification itself already VALIDATED.** It is not fatal to the fact that expected values were moved out of the child. It is sufficient to withhold unconditional qualification of the measuring instrument.

A separate, direct-answer counterargument is copying real hidden answers from readable caller-side files. **Classification: REQUIRES FUTURE INTEGRATION CONTROL.** No fresh private parent-only answer was recovered in this review. Public acceptance constants neither prove that future leak nor falsify its possibility.

## 19. Builder vs independent vs integration status

| Level | Verdict | Meaning |
|---|---|---|
| Builder qualification | QUALIFIED, as reported by Claude | Builder's 35 assertions reproduce, but some associated claims overreach the code/tests |
| Independent E0 qualification | CONDITIONAL | Shared-namespace defect removed; incomplete result contract and demonstrated failure-attribution defect remain |
| Real-task integration | CONDITIONAL | No real hidden corpus was attached or qualified; read-access, schemas, oracle correctness and feedback rules require explicit checks |

**OBSERVED.** Substantive differences from the builder report:

- Nonzero exit is not necessarily infrastructure evidence.
- The suite's “protected” sentinels exist in public source, and most secrecy cases do not use that sentinel as expected.
- The result parser is not the specified strict typed/depth-bounded parser.
- The output limit is post-capture characters, not an enforced capture byte limit.
- Exec is allowed by the reused sandbox profile.
- FD suppression solves demonstrated printing behavior; its stronger claimed unconditionally protected child channel is not established.
- `expected` is not guaranteed to exist only in one stack frame; the trusted caller may retain copies.

None of those differences was silently repaired or hidden behind the green suite.

## 20. Original-blocker resolution

**YES, for the original same-address-space blocker.** E0 no longer concatenates hidden expected values with candidate code, and the existing synthetic demonstration confirms the difference.

**CONDITIONAL for the broader intended proposition that hidden-task correctness is now a fully trustworthy experimental metric.** That additionally requires protected artifact placement, an exact task/result contract, trustworthy failure attribution, and a correct reference oracle.

The end-of-report “ORIGINAL BLOCKER REMOVED: YES” refers to the historical shared-module exposure. It does not authorize real-task integration or erase the separate measurement defects.

## 21. Remaining limitations

**OBSERVED / UNKNOWN.**

- The parent trusts caller-provided expected values; it does not qualify the reference oracle.
- Candidate-input semantics change through JSON. The adapter must use a frozen supported domain.
- Resource handling limits elapsed time and accepted output length, not all process memory or capture volume.
- Diagnostic privacy is conventional at this layer: `_researcher_*` names are not access controls. No learner is connected yet.
- Child and helper share one process. Treat all child-returned data as untrusted.
- No runtime secrecy claim is established by making public synthetic fixture answers hard to print.
- Sequential fresh processes do not alone establish isolation of concurrent callers or readable external artifacts.
- No G0 or learning-capability inference follows from E0 qualification.
- This review exercised only the existing suite and one ordinary candidate-termination example; it is not a penetration test or general security assessment.

## 22. Required future controls

**INFERRED — conceptual requirements only; no repair authority exercised.**

1. **Correct failure attribution before automated exclusion or feedback.** Candidate-caused exits and protocol failures must not automatically become infrastructure exemptions. Distinguish confirmed launch/evaluator faults from uncertain termination using trusted controller evidence.
2. **Enforce the declared result contract.** Require the success value field; define permitted types, normalization, equality, special numbers, bounds and malformed behavior. Prevent the adapter from silently changing task semantics through serialization.
3. **Correct secrecy qualification.** Bind the tested secret to the actual expected value; use an unpublished parent-runtime sentinel and execution-validity/positive controls. Public fixture recognition is not a successful secrecy qualification.
4. **Before real-task integration, close the filesystem path.** Restrict candidate reads to its permitted source/input/runtime, or supply an equivalently isolated environment with no reachable hidden artifacts. Test the actual artifact layout with synthetic decoys before connecting real data.
5. **Freeze the adapter's permitted inputs.** No hidden seeds, expected-derived annotations, other cases, or answer tables. Validate the reference oracle independently on declared task semantics.
6. **Keep rich diagnostics private and predefine failure aggregation.** A later sanitizer must explicitly map eligible task outcomes to the preregistered feedback. Never forward the entire result dictionary or infer infrastructure from untrusted text/status.
7. **Document sequential/concurrent case assumptions.** Preserve fresh contexts and ensure other active cases cannot introduce readable protected resources.

These requirements concern the measuring instrument. They do not require production Echo, RiverBrain, AP-0, routing, or generation changes.

## 23. Final verdict

**E0 CONDITIONAL.**

**VALIDATED.** The expected-value comparison is on the trusted side of a genuine process boundary; the unchanged 35-test suite reproduces. The old shared-module exposure is removed.

**VALIDATED / OBSERVED.** The failure taxonomy demonstrably confuses candidate termination with infrastructure failure, and the specified result contract is incomplete. The secrecy suite provides weaker evidence than its labels suggest.

**INFERRED.** Those findings justify a narrow return to evaluator qualification, not another general research audit. Broad reads remain a separate real-task integration condition; they are not being treated as a generic security failure or as evidence of an observed private-answer recovery.

## 24. Recommendation

Have Claude review the demonstrated termination misclassification and source-derived result-contract gaps, then seek narrow authorization for any correction and focused requalification. Preserve E0's parent-side comparison architecture. Do not connect hidden AP-0 artifacts until their read boundary is qualified. Do not begin G0 or learning trials on this report's authority.

No implementation, repair, production modification, Stage 1, or prospective learning experiment was performed.

The status answers below distinguish the explicit per-case interface from broader artifact availability. “Answer-equivalent protected information: UNKNOWN” means no new such payload field was found and no fresh private answer was recovered, but the public synthetic corpus plus unrestricted reads cannot establish the global absence of an equivalent accessible answer.

**OLD EVALUATOR EXPECTED-VALUE EXPOSURE:** CONFIRMED

**EXPECTED VALUE ENTERS CANDIDATE EXECUTION:** NO

**ANSWER-EQUIVALENT PROTECTED INFORMATION EXPOSED:** UNKNOWN

**CORRECT VERDICT REQUIRES TRUSTED COMPARISON:** YES

**CASE INDEPENDENCE:** QUALIFIED

**FAILURE TAXONOMY:** NOT QUALIFIED

**FILESYSTEM VISIBILITY:** HARDEN-BEFORE-INTEGRATION

**EXISTING 35-TEST SUITE:** PASS

**ORIGINAL BLOCKER REMOVED:** YES

**BUILDER QUALIFICATION:** QUALIFIED

**INDEPENDENT E0 QUALIFICATION:** CONDITIONAL

**REAL-TASK INTEGRATION:** CONDITIONAL

**PRODUCTION ECHO MODIFIED:** NO

**E0 MODIFIED DURING REVIEW:** NO

**GIT HEAD CHANGED:** NO

**AUTHORIZATION TO BEGIN G0:** NO

1. **Does protected expected information enter candidate execution?** Not through E0's inspected source/input/environment/launch interface. The parent retains expected and compares after child exit; caller-side readable copies remain a separate obligation.
2. **Does candidate-visible information currently contain an equivalent shortcut to the answer?** The public acceptance script contains its synthetic answers, so those fixtures are not genuinely secret. No new expected-derived metadata field or recovery of a fresh private expected value was demonstrated. Absence of all equivalent external information is not established.
3. **Is CORRECT determined exclusively by trusted comparison?** Yes, by parent-side Python equality. Correct typing and exact task semantics still require the missing contract checks.
4. **Does the filesystem-read residual invalidate E0?** It does not invalidate the demonstrated process-separation repair. It prevents an unconditional artifact-secrecy claim and requires hardening before real-task integration.
5. **What additional condition is required before real AP-0 hidden tasks are connected?** Protected cases, answers, reference/world/seed artifacts and diagnostics must be inaccessible to candidates; the permitted adapter input and result schema must also be qualified.
6. **Did the existing 35-test suite reproduce successfully?** Yes: 35 passed, zero failed, zero skipped after the outer sandbox allowed E0's sandbox to launch. The initial blocked run was 18/17 and exposed vacuous secrecy passes.
7. **What is the strongest remaining scientific-validity concern?** Candidate-caused failures can be labeled infrastructure and subsequently excluded, manufacturing improved measured correctness through selection rather than improved solutions.
8. **Is E0 independently qualified?** Conditional, not unconditionally. Expected-versus-actual process separation is supported; the full measuring instrument still has the documented classification and contract gaps.
9. **Is real-task integration qualified?** No; its separate status is CONDITIONAL. No real hidden corpus was connected or validated.
10. **What should happen next?** Resolve the candidate-exit attribution defect and result-contract omissions through separately authorized, narrowly scoped correction and requalification; then qualify protected-artifact access before integration. No G0 authorization is granted.

