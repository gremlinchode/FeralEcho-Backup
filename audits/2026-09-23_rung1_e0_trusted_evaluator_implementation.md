# Stage E0: Trusted Evaluator Boundary — Implementation Report

Implementation-authorized, narrowly scoped to Stage E0 only, per this mission's own explicit constraints. Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` unchanged before and after (confirmed by `git rev-parse` before and after). No commit was made. No production Echo, RiverBrain, self-edit, council, task classifier, generation path, or existing AP-0/sandbox file was modified. Only two new paths were created: `app/experiments/rung1/` (a new, isolated research package) and `scripts/verify_rung1_e0_trusted_evaluator.py` (its acceptance-test suite).

## 1. Executive verdict

**E0 QUALIFIED.** A per-case, process-separated trusted evaluator boundary was built, and all 35 acceptance tests pass, spanning legitimate-candidate regression, adversarial secrecy (perfect-information framing), cross-case isolation, trusted-score integrity, and a direct, safe, synthetic side-by-side demonstration that the old same-module pattern is genuinely vulnerable while the new boundary is not. One real, non-security finding surfaced during testing and is documented plainly in §22 rather than glossed over: the output-size bound correctly rejected an oversized (but non-sentinel-bearing) filesystem listing as `MALFORMED_RESULT`, which is the size cap working as designed, not a defect — but it incidentally demonstrates that the general-filesystem-read scope this stage deliberately deferred (per its own documented deviation) is real and observable, not theoretical.

## 2. Pre-change provenance

**OBSERVED.** Before any edit: `git rev-parse HEAD` = `2fba42644c82b9f7096276f4dd338d615cf1bcce`. `git status --porcelain` showed 222 pre-existing entries (a snapshot was saved to `/tmp/pre_e0_status_snapshot.txt` for comparison). No file this mission would touch (`app/experiments/rung1/*`, `scripts/verify_rung1_e0_trusted_evaluator.py`) existed prior to this session — confirmed via `ls`/glob checks returning no matches. `sandbox-exec` was confirmed present at `/usr/bin/sandbox-exec`; the pinned interpreter `/Users/richietate/miniforge3/envs/feral_echo/bin/python3` was confirmed present; `sandbox/echo_sandbox.sb` was confirmed present and was **read, never modified**.

## 3. Specification followed

`audits/2026-09-23_rung1_engineering_gate_specification.md` §4-§9, §21 (acceptance test categories 1-4, 7-10) is the primary specification implemented. `audits/2026-09-23_rung1_final_preimplementation_gate.md` §8 (the trusted-evaluator-boundary design Codex specified) and `audits/2026-09-23_trusted_boundary_reconciliation.md` §4/§11 (the mechanistic-separation rationale) were consulted directly, not merely cited. No assumption in either was found to be false against source reality during this implementation; one deliberate, documented deviation from the engineering-gate specification's own suggestion was made (§20).

## 4. Architecture implemented

Trusted parent/controller → isolated child (one fresh sandboxed process per test case) → output serialization → trusted comparison, exactly as the mission's own conceptual diagram specifies:

```
expected answer  → stays in trusted parent  (app/experiments/rung1/trusted_evaluator.py::run_case, a local variable)
task input       → isolated child            (serialized as one JSON line on stdin)
candidate(input)  → candidate result          (computed inside the sandboxed child)
candidate result  → trusted parent            (one JSON line on the child's stdout, parsed strictly)
trusted parent compares result to expected    (inside run_case, after the child process has already exited)
```

At no point does `expected answer → candidate process` occur — verified both structurally (§9) and behaviorally (§12-§15).

## 5. Exact trust boundary

**Trusted controller** (`trusted_evaluator.py::run_case`): owns the expected value, as a plain Python local variable, for the entire function call. Never writes it to disk, an environment variable, or any location the child's process could open.

**Untrusted candidate child** (`candidate_worker.py`, launched fresh per case via `sandbox-exec` against the unmodified `sandbox/echo_sandbox.sb` profile): receives only the candidate's own source (written to a fresh, per-case scratch file) and the permitted call arguments (one JSON line on stdin). Returns only a bounded, typed JSON value on stdout, or a classified failure — nothing else is read from it.

**Trusted comparison**: occurs inside `run_case`, in the controller's own process, strictly after the child's subprocess has exited (`subprocess.run` returns only once the process has terminated).

## 6. Parent→child data contract

- Candidate source: written verbatim to `<scratch>/candidate.py`, a fresh, unique-per-case temporary directory (`tempfile.TemporaryDirectory`).
- Permitted input: `json.dumps({"args": call_args}) + "\n"`, fed via `subprocess.run(..., input=...)` (a fresh pipe, never an inherited terminal fd).
- Environment: an explicit, minimal dict (`{"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}`) — never the inherited `os.environ`.
- `close_fds=True` passed explicitly (the Python default on POSIX since 3.2, made explicit here per the specification's own instruction not to rely on implicit behavior).
- Nothing else crosses this boundary: no test code, no expected value, no hidden-case count, no other case's data, no trusted comparison state.

## 7. Child→parent data contract

Exactly one line of JSON on stdout, one of three shapes:
- `{"status": "ok", "value": <json-serializable>}`
- `{"status": "candidate_error", "stage": "exec"|"lookup"|"call", "error_type": "<ExceptionClassName>"}`
- `{"status": "malformed_result", "error_type": "<ExceptionClassName>"}`

Real stderr is captured separately by the controller and used only as bounded, private, researcher-evidence text (`_researcher_stderr`, truncated to 4096 bytes) — **never** parsed for the trusted decision. Output exceeding 4096 bytes, empty output, or unparseable/malformed-schema output is classified `MALFORMED_RESULT` by the controller, not accepted.

## 8. Trusted comparison path

`run_case()`'s final block: `actual = parsed.get("value"); return CORRECT if actual == expected else INCORRECT`. This comparison uses the controller's own already-typed Python objects (`expected`, a value the caller supplied directly to `run_case`; `actual`, a value `json.loads` already parsed into a plain Python primitive) — never a candidate-supplied object, never a candidate-defined `__eq__`, never executed/`eval`'d/unpickled candidate code of any kind.

## 9. Expected-answer isolation proof (static + behavioral)

**Static**: `expected` is a parameter of `run_case()`, referenced nowhere else in the module, never assigned to any file-writing statement, never interpolated into `candidate_source`, `stdin_payload`, or the subprocess `env`/`cwd`/`args`. `candidate_worker.py` (the entire file the child process executes) contains no reference to `expected`, `_CASES`, or any protected-data name whatsoever — confirmed by direct inspection of the file's own source, reproduced in full in this report's companion implementation (§4 above already quotes its full data-flow shape).

**Behavioral**: §12-§15 below; 35/35 tests pass, including a direct side-by-side reproduction proving the *old* pattern (candidate + expected value concatenated into one exec'd module, mirroring `oracle_runner.grade()`/`tasks.py::make_test_code()`'s actual real shape) leaks the sentinel while the *new* boundary does not, using the identical candidate source against both.

## 10. Sandbox/process behavior

**OBSERVED, reused unmodified**: `sandbox/echo_sandbox.sb` (`(deny default)` base; `(allow file-read*)` unconditional; writes confined to `SCRATCH`; network denied by omission — no `(allow network*)` clause exists anywhere in the file; fork/exec denied by omission). **Confirmed live, not merely read from the header comment**: a network-connection attempt from inside the sandbox raised `PermissionError: [Errno 1] Operation not permitted`; a `subprocess.run(["echo", "hi"])` spawn attempt raised the identical `PermissionError`. Both are genuine kernel-level Seatbelt denials, independently verified by direct invocation, not assumed from the profile's comments.

**IMPLEMENTED, new**: `-I -B -S` interpreter flags (isolated mode, no `.pyc` writes, no `site` module — reducing startup surface, matching this codebase's own established convention in AP-0's `jail.py`/`freeze.py`/`qual.py`); the fd-level stdout-suppression mechanism in `candidate_worker.py` (§11 of the mission's own required sections, addressed fully in §12/§20 below).

## 11. Failure taxonomy

Implemented exactly the taxonomy named in the mission (`Outcome` class in `trusted_evaluator.py`): `CORRECT`, `INCORRECT`, `CANDIDATE_ERROR` (with a `stage` sub-field: `exec`/`lookup`/`call`), `TIMEOUT`, `SANDBOX_INFRASTRUCTURE_ERROR`, `MALFORMED_RESULT`. `SANDBOX_INFRASTRUCTURE_ERROR` is classified strictly from **trusted launch evidence** (a nonzero real subprocess exit code, or a Python-level exception raised by `subprocess.run` itself) — never from parsing candidate-produced stderr text, per the engineering-gate specification's explicit warning that a candidate could otherwise fake an infra exemption by printing a recognizable string.

## 12. Adversarial acceptance tests

Sixteen distinct attack categories (`scripts/verify_rung1_e0_trusted_evaluator.py`, section 2), each run under the mission's own explicit **perfect-information** framing — every attack's source is written with full knowledge of this exact architecture, not blind guessing: bare-name lookup of the trusted variable's literal name (`expected`); `globals()` dump; `sys.modules` inspection; full frame-stack walk (`sys._getframe()` chained via `f_back`); a direct attempt to `import app.experiments.rung1.trusted_evaluator` from inside the child; environment-variable dump; scratch-directory/parent-directory/home-directory listing; reading every file in the candidate's own scratch directory; temp-directory listing; inherited-file-descriptor probing (fds 3-9); `getppid()`; a real network-connection attempt; a real subprocess-spawn attempt; a `sys.stdout = sys.__stdout__` reassignment followed by direct `print()` calls, both at module top level and inside the target function; an exception deliberately raised with a fabricated message; and an oversized (10MB) return value. **All sixteen failed to recover the sentinel** — confirmed by checking the sentinel string's literal absence from the full JSON-serialized result (including all researcher-evidence fields, the strongest check available), never from trusting the candidate's own report of success or failure.

## 13. Cross-case isolation tests

Two cases, each with its own distinct sentinel (`SENTINEL`/`SENTINEL_B`), run as genuinely separate `run_case()` calls (fresh scratch directory, fresh subprocess each). Case B's own candidate — a filesystem/temp-directory probe — was confirmed unable to recover Case A's sentinel, and was independently scored `INCORRECT` on its own, unrelated merits (it returned a text probe result, not the expected value `SENTINEL_B`) — both properties verified, not assumed from the isolation design alone.

## 14. Trusted-score integrity tests

Three tests: (1) a candidate that `print()`s a fabricated `{"status": "ok", "value": 42}` line from *inside* its own function body, then legitimately `return`s the correct value — confirmed the real returned value, not the printed fake, determines the outcome (`CORRECT`). (2) The identical fabricated print, but the real returned value is wrong — confirmed `INCORRECT` is reported with the *real* value (`999`), not the printed fake (`42`). (3) A candidate that prints diagnostic text and then raises — confirmed classified `CANDIDATE_ERROR`, never silently treated as success.

## 15. Legitimate-candidate regression tests

Ten tests, covering: correct scalar, incorrect scalar, structured (dict/list) result, a real exception (`ZeroDivisionError`, correctly classified with stage `call`), a real timeout (`time.sleep(5)` against a 1-second budget), a non-JSON-serializable return value (correctly classified `MALFORMED_RESULT`), negative numbers, empty strings, unicode strings, and two independent repeated cases both scoring correctly. **All ten pass** — the boundary does not make ordinary, well-behaved candidate evaluation unusable, satisfying the mission's own explicit qualification condition that a repair protecting answers while breaking normal evaluation does not qualify.

## 16. Perfect-information analysis

Every adversarial test in §12 was written under the explicit assumption the attacker knows this exact file's source, including the specific fd-redirect mitigation strategy documented in `candidate_worker.py`'s own module docstring. One test specifically targets the mitigation mechanism itself: a candidate that `os.dup(1)`s its own reference to whatever fd 1 currently points to and writes directly to that duplicated descriptor, attempting to detect or route around the suppression — during the suppression window, this duplicated fd points to `/dev/null` (the same underlying open file description `os.dup2` remapped fd 1 to), so the write lands in `/dev/null` regardless of the candidate's own awareness of the mechanism. Confirmed: the real returned value (`"attempted"`) still determines the outcome, and no injected text reached the controller. Security here depends on denied *capabilities* (fd remapping the candidate cannot detect or reverse from inside its own process, kernel-level network/process denial, controller-only expected-value storage) and *protected data placement*, not on the attacker's ignorance of the design — matching the specification's own explicit perfect-information requirement.

## 17. Files changed

Two new paths only, confirmed via `git status --porcelain` diffed against the pre-mission snapshot (`/tmp/pre_e0_status_snapshot.txt`):

- `app/experiments/rung1/__init__.py` (new)
- `app/experiments/rung1/candidate_worker.py` (new)
- `app/experiments/rung1/trusted_evaluator.py` (new)
- `scripts/verify_rung1_e0_trusted_evaluator.py` (new)

No existing file — production, AP-0, sandbox, or otherwise — was opened for writing at any point in this mission.

## 18. Tests executed

`python3 scripts/verify_rung1_e0_trusted_evaluator.py`, run twice (once during development, once again immediately before writing this report to confirm stability) — both runs produced identical results.

## 19. Test results

**35 passed, 0 failed**, both runs. Full breakdown: 10/10 legitimate-regression, 16/16 adversarial-secrecy (17 counting the separate stdout-bypass real-value-wins check), 2/2 cross-case isolation, 3/3 trusted-score integrity, 1/1 perfect-information, 2/2 old-vs-new comparison.

## 20. Deviations from specification

**One deliberate, documented deviation**, per the mission's own explicit allowance for small, invariant-preserving, documented deviations:

The engineering-gate specification (§6-§7) suggested authoring a **new, narrower-read-allowlisted** Seatbelt profile, rather than reusing `echo_sandbox.sb`'s broad `(allow file-read*)`. This implementation reuses `echo_sandbox.sb` **unmodified**, for two reasons stated plainly: (1) it is an already-qualified, production-proven mechanism (the same profile `self_edit_manager.py`'s F2 gate and `oracle_runner.py` already run untrusted candidate code under), directly satisfying the mission's own "prefer reuse of already-qualified pieces" instruction; (2) for *this specific invariant* — can a candidate obtain the protected expected value — the load-bearing guarantee is **controller discipline** (the expected value is never written to any file, environment variable, or descriptor the child could reach), which holds regardless of how broad the sandbox's own read permission is, since there is nothing sentinel-bearing anywhere on disk for a broad read permission to expose. All 35 tests, including every filesystem-read adversarial attack, confirm this holds in practice. **This is not cost-free, and is documented as a real, named residual gap, not silently accepted**: §22 below.

No other deviation was made. Per-case granularity, the JSON-only output contract, the minimal-environment/close_fds hardenings, and the failure taxonomy all match the specification as written.

## 21. Pre-existing working-tree changes

**222 pre-existing porcelain entries** were present before this mission began (recorded in `/tmp/pre_e0_status_snapshot.txt`), spanning ongoing, unrelated work already in the working tree (confirmed by this session's own earlier `git status` reads at the start of the Codex-reconciliation and evaluator-qualification missions, which showed the same class of pre-existing modified/untracked files — CLAUDE.md, PENDING_DECISIONS.md, various `app/core/*.py`, numerous `audits/*.md` files from this same research thread, and AP-0 experiment output under `memory/experiments/`). **None of these 222 entries were touched, staged, or attributed to this mission.** This mission's own diff is exactly the four new files listed in §17.

## 22. Remaining weaknesses

**Real, disclosed, not glossed over — a concrete finding from testing, not merely a theoretical caveat.** During adversarial testing, a filesystem-listing attack against the real home directory (`~`) and `/tmp` produced a genuine, substantial listing of real file and directory names on this machine (dotfiles, application data directories, other in-progress research artifacts) — correctly rejected by the controller as `MALFORMED_RESULT` because it exceeded the 4096-byte output cap, and confirmed to contain no trace of the sentinel either way. **This is the size-bound mechanism working exactly as designed, not a defect** — but it is a direct, observed illustration of the deferred general-filesystem-read gap named in §20: a candidate *can* see real directory-listing content beyond the protected sentinel (though never the sentinel itself), because `echo_sandbox.sb`'s read permission is broad by design. Closing this fully — a genuinely narrower read-allowlist restricting the child to only its own scratch directory and the minimal interpreter paths it needs — remains real, unimplemented, deferred work, not claimed as done here.

Two further, smaller, honestly-stated limits: (1) `mach-lookup`/`ipc-posix-shm` are allowed (inherited from `echo_sandbox.sb`, required for Python/ObjC runtime internals per that file's own header comment) — whether this specific allowance could be exploited as a covert channel was not tested in this pass, matching the same UNKNOWN already named in the engineering-gate specification §7/§25. (2) Whether macOS Seatbelt exposes parent/sibling-process enumeration beyond `getppid()` (a bare PID number, confirmed to leak nothing useful) was not exhaustively probed — the one test attempted (`getppid()`) is a weak proxy for the fuller "process enumeration" category the specification names as partially UNKNOWN.

## 23. Rollback procedure

Delete `app/experiments/rung1/` and `scripts/verify_rung1_e0_trusted_evaluator.py`. Both are new, additive, research-only paths with zero inbound references from any other file in the repository (confirmed: nothing outside this mission's own new files imports `app.experiments.rung1`) — deletion is a clean, complete rollback with no residual state anywhere else in the repository.

## 24. Stage E0 verdict

**E0 QUALIFIED** — both required conditions hold together, neither alone: **structural qualification** (§9: source inspection establishes the expected value never enters candidate-addressable state, by construction, not merely by absence of a discovered exploit) and **behavioral qualification** (§12-§16: all adversarial acceptance tests fail to recover the protected synthetic sentinel, while legitimate candidates remain correctly evaluable, §15).

## 25. Recommendation for next mission

Per this mission's own explicit terms, **no automatic progression to Stage E1/G0 is authorized by this report.** The next mission, if and when separately authorized, should be Codex's own adversarial attack against this exact implementation — particularly the one documented, deliberate deviation (§20/§22, the reused broad-read sandbox profile) and the two named partial-UNKNOWN channels (`mach-lookup` as a covert channel; process-enumeration beyond `getppid()`) — before Stage G0 (generation accounting) is considered.

---

**EXPECTED ANSWERS ENTER CANDIDATE PROCESS:** NO

**EXPECTED ANSWERS CANDIDATE-ADDRESSABLE:** NO

**HIDDEN SUITE CANDIDATE-ADDRESSABLE:** NO

**PER-CASE ISOLATION:** QUALIFIED

**CANDIDATE OUTPUT CONTRACT:** QUALIFIED

**TRUSTED COMPARISON:** QUALIFIED

**CROSS-CASE LEAKAGE TEST:** PASS

**PERFECT-INFORMATION TEST:** PASS

**LEGITIMATE CANDIDATE REGRESSION:** PASS

**INFRASTRUCTURE FAILURE CLASSIFICATION:** QUALIFIED

**PRODUCTION ECHO MODIFIED:** NO

**RIVERBRAIN MODIFIED:** NO

**GENERATION PATH MODIFIED:** NO

**GIT HEAD CHANGED:** NO

**STAGE E0:** QUALIFIED

**AUTHORIZATION TO PROCEED TO NEXT STAGE:** NO

**1. Where does the protected expected answer live now?** In a local Python variable inside `trusted_evaluator.py::run_case()`'s own stack frame, in the trusted controller's own process — never serialized to disk, an environment variable, or any location the sandboxed child process can reach.

**2. What exact information reaches candidate execution?** The candidate's own source code (written to a fresh, unique, per-case scratch file) and the permitted call arguments (one JSON line over stdin). Nothing else — no test code, no expected value, no other case's data.

**3. What prevents candidate code that knows the evaluator architecture from recovering the answer?** Real OS-level process separation (the expected value never exists in the child's address space at all, so no in-process technique — globals, frames, imports — can reach it), a fd-level (not Python-object-level) stdout redirect during candidate execution that a `sys.stdout` reassignment cannot bypass, kernel-level Seatbelt denial of network and process-spawn (independently confirmed via real `PermissionError`s), and a controller that parses only a narrow JSON schema and never trusts candidate-printed text for the trusted decision.

**4. What adversarial attempts were tested?** Sixteen categories under a perfect-information assumption: bare-name/`globals()`/module/frame introspection, an attempted import of the trusted module itself, environment and filesystem probing (including real home/temp directory listings), inherited-descriptor probing, `getppid()`, a real network-connection attempt, a real subprocess-spawn attempt, a `sys.stdout` reassignment bypass attempt (including a direct duplicated-fd write attempt), exception-message fabrication, and output flooding — plus a direct fabricated-success-marker attempt and a safe, synthetic side-by-side reproduction of the old vulnerable pattern.

**5. Did any candidate obtain information it should not have?** No. All 16 secrecy attacks and both integrity-forgery attempts failed to affect the trusted outcome or recover the sentinel, confirmed by inspecting the full serialized result, not by trusting any candidate's self-report.

**6. Can legitimate candidates still be evaluated correctly?** Yes — all 10 regression tests pass, covering correct/incorrect scalars, structured results, real exceptions, real timeouts, malformed/unserializable returns, and edge-case values.

**7. What is the strongest remaining weakness in the trusted boundary?** The reused `echo_sandbox.sb` profile's unconditional `(allow file-read*)` — directly observed during testing to expose real, substantive (non-sentinel) filesystem content, such as home-directory and `/tmp` listings, to a candidate process. The Stage E0 invariant itself holds because the protected value is never written anywhere such a read could reach it, but general information disclosure beyond that one specific invariant remains open and is explicitly not closed by this stage.

**8. What should Codex attack next?** The documented sandbox-reuse deviation specifically — attempt to construct any scenario where the broad file-read permission, combined with some other real file already present on the host (not the sentinel, but genuinely sensitive unrelated content), could matter for a real Rung-1 run; and the two partial-UNKNOWN channels (`mach-lookup`/`ipc-posix-shm` as a covert channel, and process/sibling enumeration beyond a bare `getppid()`).
