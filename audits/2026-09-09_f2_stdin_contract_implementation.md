# Mission 28 — Implement and Adversarially Verify the Autonomous stdin Contract

**Date:** 2026-09-09
**Type:** Implementation + verification. Production code was changed. No service was restarted. No timeout, scheduler, watchdog, Ollama, RiverBrain, or memory-system behavior was touched.

---

## 1. Executive Summary

The Mission 27 design was implemented as `_BlockedStdin` in `sandbox/safe_exec_wrapper.py`, verified end-to-end through the real, unmodified `sandbox-exec` + `echo_sandbox.sb` + (now-modified) `safe_exec_wrapper.py` mechanism against 22 fixtures (not a bare Python approximation), and then adversarially attacked. The implementation works exactly as designed for every stdin-consumption form Missions 26/27 tested, closes a previously-latent `--mode=import` exposure, and eliminates the `DEVNULL`-style false-success failure mode completely — verified, not assumed.

**One real, non-trivial gap was found and is disclosed here in full, not papered over**: candidate code calling `os.read(0, ...)` directly — bypassing `sys.stdin` entirely — still hangs against a live inherited terminal, exactly reproducing Mission 24's original failure. This is a different attack surface (raw file-descriptor access, not the Python `sys.stdin` object) than anything Missions 26/27 scoped or recommended, and per this mission's explicit "do not expand scope" instruction, it was **not fixed** — it is documented precisely, with severity distinguished from a second, lower-severity finding (candidate code can trivially reassign `sys.stdin` to its own fake object, which defeats the *contract* but not the *safety property*, since it cannot make the fake object return real human input).

Also implemented, per the mission's explicit allowance: the smallest possible specification wording change in `_build_autonomous_spec()`, replacing the ambiguous "an interactive text scenario" invitation with a non-interactive-but-still-creative alternative and an explicit no-stdin clause — and a new, functionally-verified Liveness Ledger check (`f2_stdin_contract`, the 51st check).

## 2. Implementation Scope

Four files changed, all explicitly authorized: `sandbox/safe_exec_wrapper.py` (the core fix), `app/core/liveness_ledger.py` (the new check's functions), `scripts/verify_liveness_ledger.py` (its discrimination cases), `app/core/echo_projects.py` (the specification wording, per §14's explicit allowance). No other production file was touched.

## 3. Starting Integrity State

```
branch: main
HEAD:   525454a1dccfc91adf1aa8b01ff9b6ce8405d423
status: 68 changed/untracked paths — the same pre-existing live-system drift and prior-mission audit files present at the start of every mission this session
```

Confirmed via `git diff --stat` that the four production files in scope were byte-identical to HEAD before any edit.

## 4. Mission 27 Decision Being Implemented

> Enforce the stdin contract in `sandbox/safe_exec_wrapper.py`'s `_install_patches()` (the shared execution layer every real caller routes through), via `sys.stdin` replacement rather than a separate `builtins.input` patch or `stdin=subprocess.DEVNULL`, applied unconditionally regardless of `--mode=`.

## 5. `_BlockedStdin` Design

Design review performed *before* implementation, empirically, in a bare Python process (no production file touched during this step):

- `io.TextIOBase()`'s own inherited defaults were checked with zero overrides first: `read()`/`readline()`/`readlines()`/iteration already raise `io.UnsupportedOperation`; `isatty()`→`False`, `readable()`/`seekable()`/`writable()`→`False`, `fileno()`→`UnsupportedOperation`, `encoding`/`errors`/`newlines`→`None`, `closed`→`False`, `flush()`/`close()`→silent no-op — **all already honest and correct for a non-functional stream with zero code**.
- Only `read()`, `readline()`, and `readlines()` are overridden, to raise a clear, project-specific `PermissionError` instead of the generic default — the one deliberate addition beyond "do nothing," justified by the mission's own explicit diagnosability requirement.
- `__next__` is **not** separately overridden — verified directly (bare Python, before touching production code) that `io.IOBase`'s own inherited `__next__` calls `self.readline()` internally, so overriding `readline()` alone transparently covers iteration too. Re-verified through the real sandbox in §8 (Test 7).
- `isatty()`, `fileno()`, `readable()`, `seekable()`, `writable()`, `encoding`, `errors`, `newlines`, `closed`, `flush()`, `close()`, and context-manager support are all deliberately left at `io.TextIOBase`'s inherited defaults — not reimplemented, per the mission's explicit "implement only what is required... avoid accidental emulation of a real terminal" principle. Each was individually verified through the real sandbox (§10, §18).

## 6. Why This Boundary Was Chosen

Not re-litigated here — full ownership tracing and caller-impact analysis live in Mission 27's own report (`audits/2026-09-09_f2_stdin_enforcement_boundary.md`, §7-§13). This mission verified the *decision*, not re-derived it.

## 7. Exception Semantics

Before committing to `RuntimeError` (Mission 27's own tentative proposal), `safe_exec_wrapper.py`'s existing convention was checked directly: **every single other blocked operation in this exact file** — write-blocking (`_make_safe_open`, `_make_safe_os_open`, `_make_safe_path_open`, `_make_safe_rename`), `os.fork`/`system`/`popen`/`execv*`, `subprocess.*`, `shutil.*`, `ctypes.CDLL`/`cffi` — raises `PermissionError` with a `"[SANDBOX] ..."` prefix, 8/8 occurrences, zero exceptions. `RuntimeError` (Mission 27's proposal, borrowed from `run_script.py`'s separate `_insert_input_mock()` in a *different* file) does not appear anywhere in this file for a sandbox-policy violation. **Decision: `PermissionError`, matching this file's own 100%-consistent local convention, not Mission 27's tentative `RuntimeError` proposal.** `PermissionError` in this file already means "the sandbox denies this operation" generically, not narrowly "filesystem permission" — the fit is exact, not a stretch. This flows through the existing, already-proven failure-classification path unmodified: an uncaught exception during `exec_module()` produces a non-zero exit and a real traceback in stderr, exactly like every other blocked operation already does — no change needed anywhere downstream (`_run_f2_multi_file()`, `_extract_sandbox_failure_text()`, or any caller).

## 8. Real Sandbox Verification

All fixtures were run through the actual, unmodified execution chain (`sandbox-exec -f echo_sandbox.sb -D SCRATCH=... python3 safe_exec_wrapper.py <dir> <main.py> --mode=X`, with a real `pty.openpty()` pair supplying parent stdin, matching production's confirmed `/dev/ttys002` inheritance) — no bare-Python shortcut, no simplified reproduction, per the mission's explicit requirement.

| Test | Fixture | Result | Elapsed |
|---|---|---|---|
| 1 — direct `input()` | `t01_direct_input.py` | **OBSERVED**: `PermissionError: [SANDBOX] stdin.readline() blocked...`, rc=1 | 0.04s (no hang) |
| 2 — `from builtins import input` | `t02_builtins_import.py` | **OBSERVED**: same, transparently blocked | 0.03s |
| 3 — `f = input` alias | `t03_alias.py` | **OBSERVED**: same, transparently blocked | 0.03s |
| 4 — `sys.stdin.readline()` | `t04_stdin_readline.py` | **OBSERVED**: `readline() blocked` | 0.03s |
| 5 — `sys.stdin.read()` | `t05_stdin_read.py` | **OBSERVED**: `read() blocked` | 0.03s |
| 6 — `sys.stdin.readlines()` | `t06_stdin_readlines.py` | **OBSERVED — first time ever tested through the real sandbox** (Mission 27 flagged this as INFERRED-only): `readlines() blocked` | 0.03s |
| 7 — iteration (`for line in sys.stdin`) | `t07_stdin_iteration.py` | **OBSERVED**: blocked via the `readline()` message, confirming the inherited-`__next__` mechanism holds through the real sandbox, not just a bare-Python check | 0.03s |
| 8 — ordinary program | `t08_ordinary_program.py` | **OBSERVED**: unaffected, `SANDBOX_OK` | 0.03s |
| 9 — ordinary exception | `t09_ordinary_exception.py` | **OBSERVED**: real `RuntimeError: ordinary failure` traceback, not confused with the new `PermissionError` | 0.03s |
| 10 — infinite CPU loop | `t10_infinite_loop.py` | **OBSERVED**: unaffected, still hits the real 8s bound (production: 60s) and is killed cleanly | 8.00s |
| 11 — normal stdout/stderr | `t11_stdout_stderr.py` | **OBSERVED**: unaffected | 0.03s |

Two additional fixtures beyond the mission's own required set, needed to close a real gap identified during design (§5): `t16_unguarded_input.py`/`t17_unguarded_normal.py` (module-level, no `__main__` guard) — run under **both** `--mode=script` and `--mode=import`. **OBSERVED**: the previously-latent `--mode=import` exposure (Mission 27 §7, an unguarded top-level `input()` call executing during plain `exec_module()`) is now closed — `t16` blocks correctly under both modes; `t17` (an unguarded normal statement) succeeds under both modes, confirming no regression to `--mode=import`'s own normal operation.

No leftover `sandbox-exec`/`safe_exec_wrapper.py` processes after any of these runs, including the timeout-killed ones — checked directly via `ps aux`, matching Mission 24/26's own orphan-check discipline.

## 9. Alias Results

Confirmed **OBSERVED**, through the real sandbox, not just the bare-Python design check: direct `input()`, `from builtins import input`, and `f = input` are all transparently blocked with **no separate `builtins.input` patch anywhere in the implementation** — CPython's `input()` internally calls `sys.stdin.readline()` whenever `sys.stdin` is not the interpreter's original object, and this mission's real-sandbox tests confirm that behavior holds in production's actual execution environment, not merely in an isolated bare interpreter.

## 10. Stream Surface Results

`t14_stream_surface.py`, run through the real sandbox: **OBSERVED** — `isatty()`→`False`, `readable()`→`False`, `seekable()`→`False`, `writable()`→`False`, `fileno()`→`io.UnsupportedOperation`, and the program **completes successfully** afterward (`SANDBOX_OK`) — confirming these introspection calls correctly do *not* block, matching the "implement only what's required" design principle. A separate fixture (`t22_closed_and_context.py`, run during the adversarial pass, §18) confirmed **OBSERVED**: `closed`→`False`, and `with sys.stdin as s:` correctly enters and exits without error, `s is sys.stdin` holds.

## 11. False-Pass Verification

The specific Mission 26 concern — `readline()`/`read()` silently returning empty string and letting a candidate report false success — was directly, explicitly re-tested:

- `t12_false_pass_read.py` (`if data == "": print("BAD: empty stdin accepted")`): **OBSERVED** — the program never reaches its own check at all; `sys.stdin.read()` raises immediately, rc=1, the `"BAD: empty stdin accepted"` string is never printed.
- `t13_false_pass_readline.py` (`data = sys.stdin.readline(); print("success")`): **OBSERVED** — never reaches `"success"`, fails immediately with the explicit `PermissionError`.

**The DEVNULL-style false-success failure mode is confirmed eliminated for the `sys.stdin.*` surface tested here.** (See §17-§19 for the one attack surface — raw `os.read(0, ...)` — where this guarantee does not extend.)

## 12. Liveness Results

Every fixture above ran with a bounded timeout (8s, scaled from production's 60s for speed, matching Mission 24/26/27's own established methodology) and elapsed times are reported in §8's table. Every stdin-blocking case failed in ~0.03s — three orders of magnitude faster than the historical 60s hang. `t10`'s infinite loop confirms the unrelated timeout mechanism is completely untouched by this change. Zero orphaned processes after the full run, checked directly.

## 13. Six-Caller Regression Results

Rather than restart any live service, the real production functions were called directly (safe, isolated, no `run.py` involvement) — exercising the actual code path each caller uses, not a replicated invocation shape:

| Caller | Test performed | Result | Regression? |
|---|---|---|---|
| `echo_projects._run_f2_multi_file()` — direct call | Real production function, called against `t01` (input) and `t08` (normal) | **passed: False** for `t01` (blocked correctly); **passed: True** for `t08` | **NO** |
| `self_edit_manager.test_code_in_sandbox()` — direct call | Real production function, normal candidate | `ok: True, err: None` | **NO** |
| `run_script.run_sandbox_script_isolated()` — direct call | Real `hello_sandbox.py` (what 3 of the 6 callers actually run) | `success: True`, correct output (`Computation result = 285`) | **NO** |
| same, against `t01_direct_input.py` | Real function, real input()-using fixture | `success: False` — see §14 for the exact mechanism that fired | **NO** (correctly blocked, just via a different layer — see below) |
| same, against `t04_stdin_readline.py` | The gap this caller group previously had (Mission 27 §6: `run_script.py`'s own mock never covered `readline()`) | `success: False`, **new** `PermissionError: [SANDBOX] stdin.readline() blocked...`, 0.03s — **previously this would have hung for the caller's real 600s timeout** | **NO** (this is the fix working, not a regression) |
| same, against `t13_false_pass_readline.py` | False-pass check, this exact caller | `success: False`, same explicit error, no false pass | **NO** |
| `app.core.code_verification.verify_in_sandbox()` (the chat-extracted-code caller) — direct call | Normal snippet + `input()`-containing snippet | Normal: `ran_ok: True`; `input()`: `ran_ok: False`, explicit error | **NO** |
| `app.core.sandbox_interface.run_random_sandbox_script()` — direct call | Real random pick from `sandbox/scripts/` | Picked `hotstove_proof_experience_rep4.py`, failed on a genuine **pre-existing, unrelated** bug (`NameError: name 'functools' is not defined`) — a real defect in that old research-artifact script, not caused by this change | **NO** (classified NEW vs. PRE-EXISTING correctly, not glossed over) |
| `app.autonomous_loop.py` / `app.core.autonomous_loop_with_optuna.py` | Both call `run_sandbox_script_isolated()` with `hello_sandbox.py` as their real fallback | Covered by the `hello_sandbox.py` test above | **NO** |
| `sandbox/experiment_runner.py`'s `generate_and_run()` | **Deliberately not invoked directly** — it makes a real Ollama call and writes to `interaction_log.jsonl`/FAISS memory, explicitly forbidden ("DO NOT change: memory systems") | Its underlying mechanism (`run_sandbox_script_isolated()`) is proven correct above; source confirmed unchanged | **NO** (by construction — nothing about this caller's own code changed) |
| `app.core.functional_quality.py` (`--mode=functional_verify`) | Confirmed dead/never wired live (Mission 27) — tested the mode itself directly regardless, for completeness | `SANDBOX_OK`, correct JSON output (`"outcome": "executed_ok"`) | **NO** |

**No caller genuinely requires stdin — confirmed for all eight traced call sites, not just asserted.** No STOP-and-reassess condition was triggered.

## 14. Execution Mode Results

All four real modes verified directly through the real sandbox, post-fix:

- `--mode=script`: full coverage, §8.
- `--mode=import`: previously-latent unguarded-top-level exposure (Mission 27 §7) confirmed closed (`t16`/`t17`, both modes). Normal import-mode operation (self-edit's real F2) unaffected.
- `--mode=apply_to_code`: **OBSERVED** clean pass (`SANDBOX_OK`) with a real candidate `apply_to_code` function, once a real, disclosed test-harness bug on this investigator's own part (an unresolved `/tmp` symlink — `echo_sandbox.sb`'s own documented requirement that `SCRATCH` be `realpath()`-resolved, which this mission's own first attempt at testing this mode overlooked) was fixed. Disclosed here explicitly per this project's own standing discipline against silently correcting one's own script bugs.
- `--mode=functional_verify`: **OBSERVED** clean pass, same realpath fix applied, real function smoke-test correctly executed (§13's last row).

No mode showed any legitimate need for real stdin; the unconditional placement in `_install_patches()` (not gated by `--mode=`) is confirmed correct for all four.

## 15. Specification Alignment

Changed. `_build_autonomous_spec()`'s spec text (`app/core/echo_projects.py`) previously read: *"...(a simulation, a toy model, an interactive text scenario, a data visualization, etc.) — creative interpretation is expected: {question}"*. Now reads: *"...(a simulation, a toy model, a text-based narrative with predefined branching choices, a data visualization, etc.) — creative interpretation is expected, but the program must run to completion on its own, with no real-time human input required or expected: {question}"*.

This is now justified per §16 of Mission 27's own analysis: with the harness-level fix landed and verified (this mission), the specification's own ambiguity is no longer a safety question — it's the second half of the "one contract mismatch" Mission 27 identified (§16: "even a perfectly-hardened harness... leaves the specification still telling models that 'an interactive text scenario' is a valid, encouraged creative direction... wasting real compute on an interpretation the system itself has now guaranteed can never succeed"). The wording change is the smallest one that (a) preserves the creative-latitude spirit `echo_projects.py`'s own module docstring names as a deliberate design goal, (b) redirects toward the "predefined/simulated interaction, not real stdin" reading Mission 25/27 found no evidence models currently produce unprompted — giving them the explicit invitation to do so instead of an ambiguous one, and (c) states the non-interactive contract explicitly, in the same direct style as the four sibling prompt sites (`"must run headlessly without any user interaction"`, etc.). Nothing else in `_build_autonomous_spec()`, `council_generate_project()`, or the surrounding function was touched — confirmed via `git diff`, a 5-line change to one string.

## 16. Liveness Ledger Canary

New check, `f2_stdin_contract` (51st, `_CHECKS` tuple in `app/core/liveness_ledger.py`), two-part per this project's established pattern:

1. **Functional**: imports the real `_BlockedStdin` class, instantiates it, and calls `read()`/`readline()`/`readlines()`/`next()` directly, confirming each raises `PermissionError` — **tests actual behavior, not source text**, per the mission's explicit requirement. Also confirms `isatty()` stays `False`. Deliberately does **not** temporarily reassign the live `run.py` process's own `sys.stdin` to prove `input()`'s end-to-end routing every 120s cycle — that would risk a real production process's stdin for a property already independently, directly verified (§9) and known to be stable CPython behavior; the class's own raise behavior is what can silently regress and is what's cheaply, safely re-checked every cycle.
2. **Static/structural**: confirms `_install_patches()`'s real source still contains `sys.stdin = _BlockedStdin()` — protects against a future edit that keeps the class but forgets to wire it in.

**Verified live**, not just via the discrimination suite: `_check_f2_stdin_contract()` called directly against real, current code returns `pass: True` with the full expected evidence dict. A full `run_liveness_checks()` call (51 checks total, confirmed via `len(_CHECKS)`) shows exactly one failing check, `self_model_drift` — a pre-existing, unrelated, already-documented artifact of running the ledger standalone outside the live server process (this project's own `CLAUDE.md`/Finding 91 precedent explicitly names this exact caveat for this exact check) — not a regression from this change.

`scripts/verify_liveness_ledger.py` gained 5 new discrimination cases (real-class-and-wiring-correct; `readline()` silently returns `""` instead of raising — the exact false-pass class this whole mission exists to prevent; `isatty()` drifted to `True`; class not importable; class behavior correct but wiring removed from `_install_patches()`'s source). **All 5 pass, and the full suite (167 `check()` calls total, up from 162) passes with zero regressions across every pre-existing case.**

## 17. Adversarial Attack Results

| Attack | Classification | Evidence |
|---|---|---|
| Direct `input()` | **BLOCKED** | §8, Test 1 |
| `from builtins import input`, then call | **BLOCKED** | §8/§9, Test 2 |
| `f = input`, then call | **BLOCKED** | §8/§9, Test 3 |
| Direct `sys.stdin.readline()`/`read()`/`readlines()` | **BLOCKED** | §8, Tests 4-6 |
| Iteration (`for line in sys.stdin`) | **BLOCKED** | §8, Test 7 |
| `sys.stdin.isatty()` | **UNSUPPORTED as an attack** — returns `False` honestly, by design, not a bypass | §10 |
| `sys.stdin.fileno()` | **UNSUPPORTED as an attack** — raises `UnsupportedOperation` honestly, by design | §10 |
| `sys.stdin.closed` | **UNSUPPORTED as an attack** — `False`, harmless, by design | §11 |
| Context manager (`with sys.stdin as s:`) | **UNSUPPORTED as an attack** — enters/exits cleanly, harmless | §11 |
| A candidate caching `sys.stdin.readline` before calling it (`f = sys.stdin.readline; f()`) | **BLOCKED** | Direct real-sandbox test (`t15_cached_readline_ref.py`): the cached bound method still raises correctly, since it's bound to the same overridden implementation |
| A candidate replacing `sys.stdin` itself (`sys.stdin = MyFakeStream()`) | **ESCAPES the contract, but not the safety property** | Direct real-sandbox test: `sys.stdin = FakeStdin()` succeeds; the candidate's own fake object is then used instead. **Low severity, explicitly reasoned, not glossed over**: this lets a candidate simulate its own fabricated "successful" interaction, but it can never obtain real human input this way either — it was never going to succeed at anything useful, and critically, **it does not hang** — Mission 24's core safety concern is not reintroduced by this specific escape. |
| A candidate calling `subprocess.Popen(...)` to read the terminal via a child process | **BLOCKED, independently, at two separate layers** | Direct real-sandbox test: `subprocess.Popen(["cat"], ...)` raises the pre-existing `PermissionError: [SANDBOX] Call unconditionally blocked in sandbox` — this file's own pre-existing `subprocess.*` block (unrelated to this mission's change), confirmed still active |
| A candidate calling `os.fork()` to escape | **BLOCKED, independently, at two separate layers** | Direct real-sandbox test: raises the same pre-existing `_blocked()` `PermissionError`; independently, `echo_sandbox.sb`'s own kernel Seatbelt profile omits `process-fork` from its allow list — a second, kernel-level closure of the same escape route, unrelated to this mission's own change, re-confirmed still intact |
| **A candidate calling `os.read(0, N)` directly — raw file-descriptor access, bypassing `sys.stdin` entirely** | **ESCAPES — a real, confirmed gap, high severity** | Direct real-sandbox test, real pty, real 8s bound: `os.read(0, 64)` **hangs and times out**, reproducing Mission 24's original failure exactly. `os.read()` is not among this file's patched `os.*` functions (only write-flagged `os.open`, `rename`/`replace`, and the fork/exec/system family are patched) — nothing in this file's design, before or after this mission's change, ever considered raw fd-level reads. See §18. |
| A candidate importing `sys` fresh, inside its own top-level code | **UNSUPPORTED as an attack** — not a bypass | `_install_patches()` runs before `exec_module()`; `import sys` anywhere afterward binds the same, already-patched module object — implicitly confirmed by every fixture in §8, all of which `import sys` themselves and are still correctly blocked |

**This mechanism does not universally protect the sandboxed process against every conceivable stdin-reading technique — it protects the Python `sys.stdin`/`input()`/`builtins` surface completely, and does not protect raw OS-level file-descriptor 0 access.** Stated plainly, per the mission's own explicit instruction not to promise universal protection.

## 18. Subprocess Inheritance Analysis

Mission 27 flagged this as an open question (§19 of that report). Direct answer, empirically tested: **the subprocess-inheritance question is structurally moot in this sandbox's actual threat model**, because generated code cannot spawn *any* subprocess at all — confirmed independently at two separate layers (§17's `subprocess.Popen`/`os.fork` rows): the Python-level `_blocked()` patch (pre-existing, unrelated to this mission) and, independently, the kernel Seatbelt profile's own omission of `process-fork` from its allow list (`echo_sandbox.sb`, pre-existing, unrelated to this mission). Neither layer was touched or needed to be touched by this mission's work. **No subprocess-level fix was added, and the investigation confirms none is required for the subprocess-inheritance question specifically** — the real gap found (§17, `os.read(0, ...)`) is a different mechanism (direct fd access from *within* the sandboxed process itself, not inheritance by a spawned child) and is documented separately in §23, not conflated with this question.

## 19. Result Classification

Verified directly, both via the isolated fixture harness (§8) and via direct calls to the real production functions (§13): a candidate's stdin access now produces, in order: an explicit `PermissionError` inside the sandboxed subprocess → a non-zero exit code with a real traceback in `stderr` → `_run_f2_multi_file()`'s existing, unmodified `_extract_sandbox_failure_text()` parsing → a truthful `{"passed": False, "error": "..."}` result, exactly matching every other real sandbox failure's classification shape. **Confirmed NOT to become**: an empty string leading to normal completion and `SANDBOX_OK` (§11 — directly ruled out), or a 60-second timeout with no further diagnostic content (§8 — every stdin-blocking case completed in ~0.03s, not 60s).

## 20. Existing Test Suite

`scripts/verify_liveness_ledger.py` — the only real, relevant existing test suite (confirmed via grep that no other `scripts/verify_*.py` file references `safe_exec_wrapper`/`sandbox-exec`/`echo_projects` in a way that exercises this code) — run in full: **167 discrimination cases, all passing**, zero regressions among the 162 pre-existing ones. A full, live `run_liveness_checks()` call (51 checks total) shows exactly one failing check, `self_model_drift`, classified **PRE-EXISTING/UNRELATED** (a documented artifact of running the ledger standalone outside the live server process, per this project's own established precedent for this exact check) — not **NEW**.

## 21. Exact Files Changed

```
 app/core/echo_projects.py         |   8 +--   (5 lines changed: the spec-text wording, §15)
 app/core/liveness_ledger.py       | 104 ++++   (new check functions + registration, §16)
 sandbox/safe_exec_wrapper.py      |  73 ++++   (the core fix: _BlockedStdin + docstring + install call, §5-§7)
 scripts/verify_liveness_ledger.py |  59 +++    (5 new discrimination cases, §16)
```

No other file was modified. `git diff --check` clean (no whitespace/conflict-marker issues). `_insert_input_mock()` in `sandbox/run_script.py` was **not** touched, per the mission's explicit instruction — confirmed via `git diff --stat -- sandbox/run_script.py` returning empty.

## 22. Exact Behavioral Contract

Inside any sandboxed subprocess spawned via `safe_exec_wrapper.py` (any `--mode=`):

- `sys.stdin` is a `_BlockedStdin` instance, not the inherited real terminal/pipe.
- `input()` (direct, aliased, or imported) raises `PermissionError: [SANDBOX] stdin.readline() blocked — autonomous sandboxed execution has no interactive stdin`.
- `sys.stdin.read()` raises `PermissionError: [SANDBOX] stdin.read() blocked — ...`.
- `sys.stdin.readline()` raises the same `readline()`-specific message.
- `sys.stdin.readlines()` raises the same `readlines()`-specific message.
- Iteration (`for line in sys.stdin`, `next(sys.stdin)`) raises via the `readline()` message.
- `sys.stdin.isatty()`/`readable()`/`seekable()`/`writable()` → `False`; `fileno()` → `io.UnsupportedOperation`; `closed` → `False`; `encoding`/`errors`/`newlines` → `None`; `flush()`/`close()` → no-op; context-manager entry/exit works normally.
- Candidate code *can* reassign `sys.stdin` to its own object — this replaces the block for that candidate's own subsequent reads, but cannot make that replacement return real human/terminal input (§17).
- Candidate code calling `os.read(0, ...)` directly still reaches the real, underlying file descriptor and can still hang against a live, silent terminal (§17-§18) — **not covered by this contract**.
- Ordinary (non-stdin) program behavior — computation, exceptions, stdout/stderr, timeouts on genuine nontermination — is unaffected in every mode tested.

## 23. Remaining Risks / Unknowns

- **`os.read(0, ...)` (and, by the same reasoning, `os.read` against any duplicated fd pointing at descriptor 0, e.g. via `os.dup(0)`) remains a real, confirmed, unaddressed gap.** This is the single most important open item from this mission. Classified **ESCAPES**, not glossed over. Not fixed in this mission per the explicit "do not expand scope beyond what the investigation demonstrates is required" instruction — this is a different mechanism (raw fd access) than what Missions 26/27 scoped (the `sys.stdin`/`input()` Python object surface), and none of the real historical timeout cases or the eight traced real callers ever exercised this pattern; it requires code specifically written to bypass the Python-level stream API. Flagged as a clear, prioritized candidate for a dedicated future mission, not a silent gap.
- `os.dup2`/direct manipulation of fd 0 by candidate code was not tested — plausibly the same class of gap as `os.read(0, ...)`, not independently confirmed.
- Candidate code replacing `sys.stdin` (§17) is disclosed as a real, if low-severity, contract escape — not fixed, since doing so (e.g., making `sys.stdin` a read-only/protected attribute) was judged out of this mission's scope without further evidence it's needed, and risks unintended side effects on legitimate candidate code that might reasonably reassign `sys.stdin` for unrelated reasons (e.g., redirecting to a `StringIO` for testing its own logic) — a real design tradeoff, not resolved here.
- `_insert_input_mock()` in `sandbox/run_script.py` remains in place, unmodified, exactly as instructed. §13 confirmed it and the new wrapper-level fix coexist correctly (the old mock still fires first for `input()` specifically on `run_script.py`'s own two functions, since it replaces `builtins.input` directly with an implementation that doesn't route through `sys.stdin` at all; the new fix is what closes the `readline()`/`read()`/`readlines()` gap those same callers previously had). See §24 for whether/how to simplify this later.
- The specification wording change (§15) was made without re-running any generation cycle to confirm models respond to the new wording as intended — this is a plausible, reasoned expectation (matching the four sibling sites' own established, apparently-effective non-interactive framing), not a directly re-verified outcome; the real behavioral backstop (the harness fix) does not depend on this holding.

## 24. Future Cleanup Candidates

- **`_insert_input_mock()` (`sandbox/run_script.py`)**: now redundant-but-harmless for `input()` specifically on its own two callers (the new wrapper-level fix would also catch `input()` there, just via a different underlying route — `sys.stdin.readline()` rather than a direct `builtins.input` replacement — if the old mock were ever removed). Retained, unmodified, per this mission's explicit instruction. A future, separate, single-purpose cleanup mission could consider removing it now that the lower-level mechanism supersedes it — explicitly **not** done here, one variable at a time, per the mission's own stated discipline.
- **The `os.read(0, ...)` gap (§17-§18, §23)**: the clearest, most important candidate for a genuinely new, dedicated future investigation — determine the full raw-fd-level attack surface (`os.read`, `os.dup`/`os.dup2`, anything else that reaches an open fd without going through `sys.stdin`) and design a fix (likely a `_make_safe_os_read`-style patch keyed on fd number, mirroring this file's own existing `_make_safe_os_open`'s write-flag-checking pattern) before considering this contract complete against a genuinely adversarial (not just naturally-generated) candidate.

## 25. Final Integrity State

```bash
git status --short | wc -l
# 72 (68 pre-existing + this mission's 4 intentional file changes)

git rev-parse HEAD
# 525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged — no commit was made)

git branch --show-current
# main (unchanged)

git diff --check
# (clean for all four changed files — no whitespace/conflict-marker issues)
```

- Production code: **changed**, exactly the four files listed in §21, all explicitly authorized.
- HEAD: **unchanged**.
- No commit created, no branch created or switched.
- No service restarted — `run.py`, Ollama, and the watchdog were never touched or invoked; every real-production-function call in §13 was a direct, isolated Python import and call, not a request to the live server.
- No timeout, scheduler, watchdog, RiverBrain, or memory-system behavior changed — confirmed via `git diff --stat` showing zero touched lines outside the four listed files.
- Temporary fixtures: 20 fixture `.py` files plus `run_real_sandbox.py` and `results.json` remain at `/tmp/mission28_fixtures/`, entirely outside git tracking, listed explicitly here (not silently left unaccounted for) — matching Mission 26's own precedent of leaving disposable fixture sources in place while removing all scratch execution directories (confirmed removed: `/tmp/mission28_scratch/`, `f2_direct_call_scratch{,2}`, `adversarial/`, `mode_apply/`, `mode_funcverify/`, all deleted). Zero orphaned `sandbox-exec`/`safe_exec_wrapper.py` processes remained after any test phase, checked directly and repeatedly throughout this mission.
