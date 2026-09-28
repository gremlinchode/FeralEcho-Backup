# Mission 30 — Close the OS-Level fd 0 Stdin Escape

**Date:** 2026-09-09
**Type:** Implementation + adversarial verification. Production code was changed. `run.py` was not restarted (evidence for why, below). No timeout, Seatbelt policy, or unrelated production behavior was touched.

---

## Executive Verdict

**IMPLEMENTED AND VERIFIED**, with one precisely-characterized, empirically-understood nuance disclosed in full rather than hidden: closing fd 0 does not make fd *number* 0 permanently vacant for the rest of the subprocess's life — CPython's own bytecode-cache write for the candidate's module transiently reoccupies it, confirmed and reproduced. This reoccupation is provably safe (the resource is write-mode, so every read attempt against it — direct or via `dup()` — still fails with `OSError: Bad file descriptor` in every test run), but it means the correct, precise claim is "candidate code cannot read the original inherited terminal through fd 0 or any route tested," not the looser "fd 0 is permanently closed."

## Implementation

- **File changed:** `sandbox/safe_exec_wrapper.py`.
- **Function changed:** `_install_patches()`, immediately after the existing `sys.stdin = _BlockedStdin()` line (Mission 28).
- **Mechanism:** `try: _os.close(0)` except `OSError: pass`. The bare exception swallow covers only the already-safe case (fd 0 already closed/invalid when this runs) — any other `OSError` is unexpected and propagates.
- **Why this boundary:** re-verified, not assumed, before implementing (§ below) — `_install_patches()` remains the correct placement per Mission 27/29's own established reasoning: it's the one shared layer every real caller already routes through, and it runs strictly before `spec.loader.exec_module(m)` (candidate execution), so no candidate code has a window to `dup()` the original fd before it's closed.
- **Mechanism choice:** close, not redirect to `/dev/null` — Mission 29 pre-vetted this exact choice; re-confirmed empirically in this mission (§ False-Success Analysis) rather than taken on faith.

Also extended: `app/core/liveness_ledger.py`'s `f2_stdin_contract` check (source-anchor sub-check for `_os.close(0)`'s presence, reporting `python_stdin_blocked`/`os_fd0_blocked` as independently diagnosable booleans) and `scripts/verify_liveness_ledger.py` (3 new discrimination cases). `sandbox/run_script.py`'s `_insert_input_mock()` and `sandbox/echo_sandbox.sb` were **not** modified, as instructed.

## Placement Verification (§4 of the mission brief)

Before implementing, confirmed directly: nothing in `_install_patches()`'s own Phase 1 pre-imports (stdlib modules: `io`, `pathlib`, `subprocess`, `shutil`, `importlib`, `_io`, `posix`, `_posixsubprocess`, `ctypes`, `_ctypes`, `cffi`) performs any I/O on fd 0. Nothing in the `__main__` block before `_install_patches()` runs (argument parsing via `sys.argv` only) touches stdin. Nothing in the wrapper's own subsequent code (module loading, `SANDBOX_OK` printing) reads from stdin at any point — confirmed by a full re-read of the file's `__main__` block. Placing the close at the very end of `_install_patches()`, after every other patch, is safe and doesn't break any wrapper-internal operation.

## fd 0 Behavior — Evidence Table

All tests run through the real, unmodified production chain (`sandbox-exec -f echo_sandbox.sb -D SCRATCH=... python3 safe_exec_wrapper.py <dir> <main.py> --mode=script`), with a real `pty.openpty()` pair supplying parent stdin (faithfully reproducing production's confirmed inherited-terminal condition).

| Test | Expected | Observed | Elapsed | Result |
|---|---|---|---|---|
| `os.read(0, 1)` | explicit failure | `OSError: [Errno 9] Bad file descriptor`, immediately | 0.035s | **VERIFIED** |
| `os.dup(0)` then read via the dup | explicit failure | `os.dup(0)` itself **succeeded** (see nuance below); the subsequent `os.read()` on the duplicate still raised `OSError: [Errno 9] Bad file descriptor` in every one of 3 reproductions | 0.026s | **VERIFIED for the read-access property; PARTIALLY-INFERRED for "dup itself fails" — see below** |
| `os.fdopen(0, "r")` then `.readline()` | fails without blocking | `fdopen()` construction itself succeeded (lazy, doesn't validate); `.readline()` raised `OSError: [Errno 9] Bad file descriptor` | 0.026s | **VERIFIED for read access** |
| `/dev/fd/0` | cannot recover the old terminal fd | `open("/dev/fd/0", "r")` raised `OSError: [Errno 13] Permission denied` — a different errno than direct fd access (EACCES vs. EBADF), because reopening a write-mode-occupied fd-alias for reading is itself invalid, but the outcome (no read access) is identical | 0.026s | **VERIFIED** |
| `/dev/tty` | no newly-created escape | `OSError: [Errno 6] Device not configured` — reproduced identically in Mission 29 with zero sandboxing at all, confirmed unrelated to this fix | 0.026s | **VERIFIED unaffected (was never an escape, still isn't)** |

**The dup()-succeeds nuance, investigated to ground truth, not left as a surprising anomaly**: precise diagnosis (`fstat(0)`, `os.isatty(0)`, `fcntl` introspection, and direct inspection of the scratch directory) traced this to CPython's own bytecode-cache write. `os.close(0)` genuinely, immediately closes the original fd (confirmed: the very first read attempt in `a_direct_read.py`, before any other file I/O happens, raises `EBADF`). Moments later, Python's own module-loading machinery (`spec.loader.exec_module(m)`) writes a `.pyc` bytecode cache for the candidate's module into `__pycache__/` inside SCRATCH — a legitimate, write-mode `open()` call that the OS's lowest-available-fd-number convention assigns to slot 0, since that's the number I just freed. Directly confirmed by finding the real artifact on disk: `__pycache__/main.cpython-312.pyc.<tmpsuffix>`, a 0-byte file matching `fstat(0)`'s reported `S_IFREG, mode=644, size=0`. `isatty(0)` returns `False` and `ttyname(0)` raises `ENOTTY` at this point — **conclusively confirming what now occupies fd 0 is never the original terminal**. Because this resource is write-mode, `read()` against it (or any `dup()` of it) always fails with `EBADF`, regardless of its specific identity — this is a structural POSIX property (a write-only-opened fd cannot be read), not a coincidence of this particular file. Reproduced 3/3 times with identical results.

## Python stdin Regression (Mission 28's contract)

All 7 fixtures re-run through the real, modified sandbox — every one still raises the exact expected `PermissionError`, unaffected by the fd 0 change:

| Form | Result |
|---|---|
| `input()` | `PermissionError: [SANDBOX] stdin.readline() blocked — ...` |
| `from builtins import input` | same |
| `f = input` alias | same |
| `sys.stdin.readline()` | same |
| `sys.stdin.read()` | `PermissionError: [SANDBOX] stdin.read() blocked — ...` |
| `sys.stdin.readlines()` | `PermissionError: [SANDBOX] stdin.readlines() blocked — ...` |
| `for line in sys.stdin` (iteration) | routes through the `readline()` message, as designed |

All 7 completed in ~0.03s. None returned an `OSError` where the Python-level contract should remain `PermissionError` — the two layers are confirmed independent, exactly matching the intended architecture (`sys.stdin` → `_BlockedStdin` → `PermissionError`; `os.read(0)` → closed fd → `OSError`).

## False-Success Analysis

Directly re-tested Mission 26's exact failure shape at this new layer: `data = os.read(0, 1); if data == b"": print("BAD: interpreted EOF as valid input")`. **The conditional is never reached** — `os.read(0, 1)` raises `OSError` before the `if` statement ever executes. `/dev/null`-style semantics were explicitly **not** introduced: a redirect-to-`/dev/null` mechanism would have returned `b""` here (silently indistinguishable from legitimate EOF, exactly Mission 26's diagnosed false-success class); closing the fd instead produces a genuine, explicit, immediate exception. Confirmed by direct comparison against the same conditional's outcome under `/dev/null` redirection in Mission 29's own isolated test (reproduced there as `b''`) — this mission's close-based result is categorically different.

## Liveness Analysis

Every fd-0 fixture completed in 0.025–0.035 seconds — no 8-second watchdog termination, no 60-second production timeout, in any of the ~10 real fd-0-targeting fixtures run. The one deliberate control that *should* hit the timeout (`ctrl_infinite.py`, a pure-CPU infinite loop with no I/O) still did, at exactly the 8s test bound, killed via SIGKILL — confirming the fd-0 close has zero effect on the unrelated nontermination-timeout mechanism. Zero orphaned `sandbox-exec`/`safe_exec_wrapper.py` processes after any test phase, checked directly and repeatedly (including after the deliberately-hanging infinite-loop control).

## Production-Caller Regression

Real production functions called directly (not a replicated invocation shape), matching Mission 28's own methodology:

| Caller | Test | Result |
|---|---|---|
| `run_script.run_sandbox_script_isolated()` | real `hello_sandbox.py` | `success: True`, correct output — **unaffected** |
| same | real `os.read(0)` attack fixture | `success: True` for the fixture itself (it catches its own `OSError` and completes normally — see the F2-specific section for why an *uncaught* version was also tested), diagnostic output confirms the fd was correctly closed |
| `code_verification.verify_in_sandbox()` (chat-extracted-code caller) | normal snippet | `True`, unaffected |
| same | uncaught `os.read(0)` attack snippet | `False`, real traceback ending in `OSError: [Errno 9] Bad file descriptor` |
| `self_edit_manager.test_code_in_sandbox()` (`--mode=import`) | normal candidate | `ok: True` — **unaffected** |
| `sandbox_interface.run_random_sandbox_script()` | real random script pick | `SANDBOX_OK` — **unaffected** |
| `echo_projects._run_f2_multi_file()` | normal fixture | `passed: True` — **unaffected** |
| same | uncaught `os.read(0)` fixture | `passed: False`, real traceback — **VERIFIED correct classification** |
| `--mode=apply_to_code` | real `apply_to_code` candidate | `SANDBOX_OK` — **unaffected** |
| `--mode=functional_verify` | real smoke-testable candidate | `SANDBOX_OK` — **unaffected** |

**Classification of the one apparent anomaly, resolved and disclosed rather than hidden**: the first `_run_f2_multi_file()`/`run_sandbox_script_isolated()` tests against `a_direct_read.py` reported `passed`/`success: True` even though the fixture *attempts* an fd-0 read — this is **TEST HARNESS DESIGN**, not a sandbox regression: that specific fixture catches its own `OSError` internally (`try: os.read(0,1) except OSError as e: print(...)`) and completes normally, so `SANDBOX_OK` correctly prints and F2/the isolated runner correctly report success — exactly as they should for what is, from their perspective, an ordinary successfully-completing script. Re-tested immediately with an uncaught version (the realistic case a real F2 candidate attempting "interactive" behavior would actually produce, since generated code doesn't typically wrap raw syscalls in defensive `try/except OSError`), which correctly failed. No production code was changed to "fix" this — it was a fixture-design artifact on this investigator's own part, caught and disclosed per this project's standing discipline.

## F2-Specific Verification

- Noninteractive valid project: **VERIFIED**, continues to work (`passed: True`).
- `input()`, `sys.stdin.readline()`, `sys.stdin.read()`: **VERIFIED**, all still fail fast via `_BlockedStdin` (Mission 28's contract, unaffected).
- `os.read(0, ...)` (uncaught): **VERIFIED**, now fails fast via the new fd0 close, correctly classified `passed: False` with a real traceback — F2's existing failure-classification path (`_extract_sandbox_failure_text()`) handled this with zero modification needed, confirmed directly.
- `os.dup(0)`: **VERIFIED** that no usable duplicate of the *original terminal* is obtained — the dup succeeds only against whatever benign, unreadable resource has transiently reoccupied the fd number (§ evidence table nuance above), never against real terminal data.

## Descriptor Resurrection Analysis (§19-20)

**Direct, empirical answer**: closing fd 0 cannot be trivially bypassed to recover the *original terminal* by reopening or duplicating another permitted resource. Tested precisely:

- Candidate-initiated ordinary file opens (a scratch file the candidate itself creates and writes) were confirmed to work normally and, when they happen to receive a low fd number, only ever expose content the *candidate itself* wrote — read-back matched exactly what was written, never anything from the original terminal. This directly answers §20's core question: **fd number 0 is not itself the security boundary — access to the original human-controlled terminal's open file description is, and nothing tested recreates that access, regardless of which fd number a later resource happens to receive.**
- `/dev/fd/0` and `/dev/tty` were both re-confirmed to provide no path back to the real terminal (§ evidence table).
- `os.dup(0)` was confirmed to only ever duplicate whatever *currently* occupies slot 0 (the benign pyc-cache write, or nothing) — never a preserved handle to the pre-close terminal, since that original open file description was genuinely closed and no reference to it survives anywhere in the candidate's reachable state.

## Seatbelt Interaction

**Not modified, and confirmed unnecessary to modify.** `echo_sandbox.sb` was re-read in full; its `(allow file-read* (subpath "/dev"))` remains exactly as Mission 29 found it — broad and deliberate, required for legitimate `/dev/urandom`/`/dev/null`/stdout/stderr access, uninvolved in this fix. The fd-0 boundary implemented here operates entirely at the `subprocess`/file-descriptor layer, before Seatbelt's own path-based rules are ever consulted for any *candidate* read attempt on fd 0 — confirmed structurally: Seatbelt governs *what paths may be opened*, not *which fd number an already-open resource occupies*, so the two layers remain cleanly non-overlapping exactly as intended (`Seatbelt controls what sandboxed code may access` + `safe_exec_wrapper controls inherited execution descriptors`).

## `run.py` Import/Restart Analysis

**No restart is required for this fix to take effect in production.** Verified directly, not assumed: `safe_exec_wrapper.py` is never `import`ed as a Python module by `run.py` or any long-lived process code — every real caller (`_SANDBOX_WRAPPER` in both `self_edit_manager.py` and `run_script.py`) references it only as a **file path string**, passed to `sandbox-exec ... python3 <path>` as a fresh subprocess invocation. Each real sandbox call spawns a brand-new `python3` interpreter that reads `safe_exec_wrapper.py` from disk at that exact moment — confirmed empirically throughout this entire mission, since every test performed used the live, currently-running `run.py` process (PID 54713, unrestarted, confirmed same PID before and after) as the parent, and every one correctly exercised the new fd0-close behavior without any restart.

**One real, disclosed exception, carried forward from a pre-existing state, not newly introduced by this mission**: `app/core/liveness_ledger.py`'s `_check_f2_stdin_contract()` directly `import`s `_BlockedStdin` from `sandbox.safe_exec_wrapper` — a genuine in-process Python import, cached in `sys.modules` once loaded. Checked directly: the live `run.py` process's own persisted `memory/liveness_ledger.json` shows **no `f2_stdin_contract` entry at all**, confirming the running process has never yet loaded the version of `liveness_ledger.py` containing this check in the first place (it predates Mission 28 entirely) — so there is nothing currently cached to go stale, and this mission's own extension of that check inherits the exact same pre-existing, already-true fact: the live process's in-process Python state (not the sandbox mechanism itself) will need a restart at some point to pick up *any* of Missions 28–30's `liveness_ledger.py`/`echo_projects.py` changes. This is not new to Mission 30 and was not caused by it.

## Remaining Risks

- The exact identity of whatever transiently reoccupies fd slot 0 (currently: CPython's own bytecode-cache write) is an implementation detail of the Python interpreter's import machinery, not a designed invariant of this fix — if a future Python version, a `-B`/`sys.dont_write_bytecode` flag change, or a different loader path altered *what* (if anything) reoccupies that slot, the safety property (nothing readable ends up there) would need re-verification rather than being assumed to hold by the same reasoning indefinitely. Flagged as a real, if currently-benign, dependency on interpreter-internal behavior.
- `termios`/`fcntl`-level manipulation beyond the `F_GETPATH` introspection already performed was not exhaustively tested — no plausible mechanism was identified by which it would recover terminal access once the original fd is closed, but this remains **UNKNOWN** rather than affirmatively ruled out.
- This mission did not attempt to close fd 0 a second time immediately before candidate top-level execution (i.e., inside the loader itself) to eliminate the reoccupation window entirely — deliberately not pursued, since doing so would require monkeypatching the import loader (real added complexity) to close a window that is already empirically safe by the reoccupying resource's own structural properties (write-only, unreadable). Documented as a considered-and-declined option, not an oversight.

## Git Integrity

```
git diff --stat -- sandbox/safe_exec_wrapper.py app/core/liveness_ledger.py scripts/verify_liveness_ledger.py
 app/core/liveness_ledger.py       | 45 +++++++++++++++++++++++++++++++++------
 sandbox/safe_exec_wrapper.py      | 42 ++++++++++++++++++++++++++++++++++++
 scripts/verify_liveness_ledger.py | 18 ++++++++++++++++
 3 files changed, 98 insertions(+), 7 deletions(-)
```

No other file touched. No temporary fixtures committed.
