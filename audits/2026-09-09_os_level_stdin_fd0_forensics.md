# Mission 29 — OS-Level Stdin / File Descriptor 0 Boundary Forensics

**Date:** 2026-09-09
**Type:** Investigation-only. No production code, sandbox policy, timeout, or service was modified or restarted. All experimentation used isolated, bounded fixtures under `/tmp/mission29_fixtures/`, run through the real, unmodified (as landed by Mission 28) production sandbox chain.

---

## Executive Verdict

**VERIFIED ESCAPE** — precisely scoped. The escape is real, reproduced through the actual production sandbox mechanism (not a bare-Python approximation), and is a *single* underlying mechanism (the inherited file descriptor 0 / its open file description) reachable through several syntactic routes, not several independent problems. Mission 28's own conclusion is **confirmed, not contradicted**: the Python `sys.stdin`/`input()` surface is completely closed; the raw OS-descriptor surface is not, and was never claimed to be.

---

## Boundary Map

```
sys.stdin (input(), .read(), .readline(), .readlines(), iteration)
    ↓
BLOCKED ✓  (Mission 28, re-confirmed this mission — §"Mission 28 Regression")

fd 0  (os.read(0, ...), os.fdopen(0, ...))
    ↓
NOT BLOCKED — reaches the real inherited terminal, hangs identically to
the pre-Mission-28 failure (REPRODUCED)

/dev/fd/0
    ↓
NOT BLOCKED — resolves to the same open file description as fd 0 itself;
hangs identically (REPRODUCED)

os.dup(0) then read
    ↓
NOT BLOCKED — the duplicate shares the same underlying open file
description; hangs identically (REPRODUCED)

/dev/tty
    ↓
FAILS FAST — but NOT because of any sandbox/Seatbelt boundary. Reproduced
bit-for-bit identically with zero sandboxing at all (OBSERVED, isolated
control test): a subprocess.Popen()-spawned child that inherits a pty
slave as fd 0 but never acquires a controlling-terminal session
(setsid()/TIOCSCTTY) gets ENODEV from /dev/tty regardless of sandboxing.
This is incidental process-session plumbing, not a security control, and
should not be relied upon as one.
```

## Evidence Table

All routes run through the real, current, Mission-28-modified production chain (`sandbox-exec -f echo_sandbox.sb -D SCRATCH=... python3 safe_exec_wrapper.py <dir> <main.py> --mode=script`), with a real `pty.openpty()` pair supplying parent stdin, faithfully reproducing production's confirmed `/dev/ttys002`-class inheritance (re-checked live at mission start: the real running `run.py`, PID 54713, still has fd 0 on `/dev/ttys002`).

| Route | Real sandbox | PTY-backed | Blocks | Fails fast | Human input reachable | Result |
|---|---|---|---|---|---|---|
| `os.read(0, 1)` | Yes | Yes | Yes, 8.0s bound (production: 60s) | No | **Yes** — a real, live keystroke typed into the pty would be delivered | **HANG / LIVENESS ESCAPE, HUMAN-INPUT ESCAPE** |
| `os.fdopen(0, "r").readline()` | Yes | Yes | Yes, 8.0s | No | **Yes** | **HANG / LIVENESS ESCAPE, HUMAN-INPUT ESCAPE** |
| `open("/dev/fd/0", "r").readline()` | Yes | Yes | Yes, 8.0s | No | **Yes** | **HANG / LIVENESS ESCAPE, HUMAN-INPUT ESCAPE** |
| `os.dup(0)` then `os.read(fd, 1)` | Yes | Yes | Yes, 8.0s | No | **Yes** | **HANG / LIVENESS ESCAPE, HUMAN-INPUT ESCAPE** |
| `sys.stdin = Fake()` then raw `os.read(0, 1)` (Mission 28's disclosed low-severity escape, extended) | Yes | Yes | Yes, 8.0s | No | **Yes** | **HANG / LIVENESS ESCAPE, HUMAN-INPUT ESCAPE** — confirms the two escapes (Python reassignment, raw fd) are independent; reassigning `sys.stdin` does nothing to fd 0 itself |
| `open("/dev/tty", "r").readline()` | Yes | Yes | No | **Yes**, 0.035s | No (fails before any read is attempted) | **EXPLICIT FAILURE, but incidental — not a security boundary** (see below) |
| `os.fstat(0)` / `os.isatty(0)` / `os.ttyname(0)` | Yes | Yes | No | Yes, 0.05s | N/A (introspection only) | **BLOCKED as an attack, works as introspection** — confirms fd 0 is a genuine character device, `isatty(0) → True`, `ttyname(0) → /dev/ttysNNN` — a real, live terminal, not a closed/null descriptor |
| `sys.stdin.fileno()` (Mission 28's own design) | Yes | Yes | No | Yes | N/A | Raises `io.UnsupportedOperation`, by design (Mission 28) — but irrelevant to the escape, since fd `0` is a universally-known literal, not a secret this method could hide |
| `input()` / `.read()` / `.readline()` / `.readlines()` / iteration (regression re-check) | Yes | Yes | No | Yes, ~0.03s each | No | **BLOCKED** — Mission 28's fix confirmed intact |
| Ordinary program / exception / infinite loop (regression re-check) | Yes | Yes | (loop only) | Yes / Yes / N/A | N/A | Unaffected — no regression |

## Root Cause

**Inherited file descriptor 0** — a single root cause, not multiple independent ones. `os.read(0, ...)`, `os.fdopen(0, ...)`, `/dev/fd/0`, and `os.dup(0)` are four different *syntactic* routes but all four resolve to the exact same underlying kernel *open file description* — the one connected, at process-spawn time, to whatever the parent process's fd 0 actually is (a real pty in production, confirmed). This is **Hypothesis 2** from the mission's own framework, refined: not "only `sys.stdin` was exposed" (Hypothesis 1 — rejected, since the raw-fd routes are broader than the Python abstraction), not "broader terminal-device access" (Hypothesis 3 — rejected; `/dev/tty`'s failure was directly shown, via an isolated non-sandboxed control test, to be incidental process-session plumbing unrelated to sandboxing, not a live capability), and not "multiple independent OS-level paths" in the sense of multiple *distinct problems* (Hypothesis 4 — the syntactic routes are plural, the underlying resource is singular).

## Security/Liveness Classification

| Route | Classification |
|---|---|
| `os.read(0, ...)` | **HANG / LIVENESS ESCAPE** (also human-input-reachable) |
| `os.fdopen(0, ...)` | **HANG / LIVENESS ESCAPE** |
| `/dev/fd/0` | **HANG / LIVENESS ESCAPE** |
| `os.dup(0)` + read | **HANG / LIVENESS ESCAPE** |
| `sys.stdin` reassignment, alone | **FALSE SUCCESS RISK** (Mission 28's own finding — a candidate can fabricate its own "successful" fake input; does not hang, does not reach real human input) |
| `sys.stdin` reassignment + raw fd read | **HANG / LIVENESS ESCAPE** (the reassignment doesn't protect against, or enable, the fd-level escape — they're independent) |
| `/dev/tty` | **EXPLICIT FAILURE** (incidental, not a designed boundary — do not rely on this) |
| `input()` / `sys.stdin.*` (Mission 28 surface) | **BLOCKED** |
| `sys.stdin.fileno()`, `isatty()`, `fstat(0)` | **BLOCKED as an attack / SAFE, honest introspection** — none of these leak anything a candidate doesn't already know (fd 0 is a universal literal) |

## Enforcement Recommendation

**Do not implement — this is a boundary determination only, per the mission's explicit scope.**

The evidence rules out `echo_sandbox.sb` (Option C) as the right layer for a future fix: read directly, the Seatbelt profile's `(allow file-read* (subpath "/dev"))` and `(allow file-write-data (subpath "/dev"))` are broad, deliberate, and already correctly justify themselves (`stdout`, `stderr`, `/dev/urandom`, `/dev/null` all need this). Narrowing `/dev` access at the kernel-policy layer risks breaking legitimate, unrelated runtime behavior for a problem that isn't actually a *policy* gap — Seatbelt was never designed to restrict *which* underlying file description fd 0 points to; that's decided entirely by the Python `subprocess.Popen`/`subprocess.run` call that spawns the sandboxed process, before Seatbelt is ever consulted.

That leaves a real choice between **Option A** (`safe_exec_wrapper.py`, operating on the raw OS descriptor via `os.close(0)`/`os.dup2()` inside `_install_patches()`, before `exec_module()` runs — the same architectural layer Mission 27/28 already established as correct for the Python-level fix, extended one level lower) and **Option B** (each caller's own `subprocess.Popen`/`subprocess.run` construction, e.g. `stdin=subprocess.DEVNULL`). **Option A is the evidence-supported choice**, for the identical reasoning Mission 27 already established for the Python-level fix: there are 8 real production callers (Mission 27's own trace) sharing this one execution layer, none of them legitimately need real stdin, and a fix at the caller level would need to be independently applied 6+ times with the same duplication risk Mission 27 already rejected for the Python-level mechanism. `os.dup(0)` from within candidate code (§ Evidence Table) already proves that any fix must happen *before* candidate code gets a chance to run, not as something revocable afterward — which is exactly what `_install_patches()`'s existing placement (before `exec_module()`) already guarantees, for free, if the future fix is added there.

**Do not choose the mechanism yet without reading the next section — it changes which of the two remaining sub-options is actually correct.**

## Attacking the Proposed Future Fix (per the mission's explicit §15 requirement)

Two concrete OS-level mechanisms were tested, isolated, safely (a bare `os.fork()` in a throwaway process — never touching the real sandbox, `safe_exec_wrapper.py`, or any production state), specifically to determine their semantic difference *before* anyone recommends one:

- **Redirecting fd 0 to `/dev/null`** (`os.dup2(os.open("/dev/null", os.O_RDONLY), 0)`): `os.read(0, 1)` → `b''`; `readline()` → `''`. **This reproduces the exact false-success ambiguity Mission 26 already found and rejected for the Python-level `stdin=subprocess.DEVNULL` approach — just at the raw-descriptor layer instead.** A candidate checking `if data == "": ...` would see the same silent, indistinguishable-from-legitimate-EOF signal this whole investigation thread has repeatedly worked to eliminate. **Do not recommend this as the mechanism**, even though it lives at the "correct" architectural layer (Option A) — the mechanism choice within that layer matters just as much as Mission 26 already proved it does at the Python level.
- **Closing fd 0 entirely** (`os.close(0)`, no replacement): `os.read(0, 1)` and `os.fdopen(0)` both raise a genuine, explicit, immediate `OSError: [Errno 9] Bad file descriptor`. This satisfies the exact contract chain the mission's own brief specifies: *attempted external human input → deterministic explicit failure → observable to harness → no indefinite blocking → no false-success signal.* **This is the evidence-supported mechanism, if a future fix is built at this layer** — not because it's the only conceivable option, but because it was the only one tested here that avoids reproducing Mission 26's already-diagnosed false-success failure mode.

Stated plainly, per the mission's own instruction not to assume a mechanism before investigating it: **Option A (`safe_exec_wrapper.py`) + closing fd 0 (not redirecting it)** is the combination this mission's evidence actually supports — not Option A with a `/dev/null` redirect, which would look superficially similar but carries the exact regression risk this whole investigation series exists to prevent.

## Threat Model

What a candidate can actually do, grounded in what was tested — not hypothetical unlimited Unix access:

- A candidate cannot spawn any subprocess (confirmed unchanged and re-relevant: `subprocess.*` is unconditionally `_blocked()`-patched at the Python level, and `echo_sandbox.sb`'s own allow list omits `process-fork` independently at the kernel level — both pre-existing, both re-confirmed present in the current, unmodified source this mission read, neither touched by this mission). This makes the "does a spawned child inherit the real terminal fd" question (mission §12) **structurally moot**: there is no route by which candidate code can spawn a child in the first place, so descriptor inheritance through a child process is not a reachable concern independent of the already-established, pre-existing subprocess/fork block.
- A candidate *can*, from within its own single process (no subprocess needed), reach the real inherited terminal via `os.read(0, ...)`, `os.fdopen(0, ...)`, `/dev/fd/0`, or a `os.dup()` of any of these — and can therefore both hang the sandbox for the full timeout *and*, if a real human happened to type into the inherited pty during that window, actually receive real human-controlled input. Both halves of this were directly observed (the hang, and the identity of fd 0 as a genuine, live tty via `isatty(0)`/`ttyname(0)`) — receiving *actual* typed keystrokes was not separately demonstrated (no human typed into the test harness's own pty during these runs), consistent with the mission's own instruction not to require a human to type into a production process; the descriptor's confirmed real-terminal identity is the evidence, not a live demonstration of a human typing.
- `/dev/tty` is not a usable escape route in practice, but not because anything prevents it deliberately — it simply doesn't resolve to anything for a process spawned this way, sandboxed or not.

## Mission 28 Regression

**Confirmed intact, re-verified through the real sandbox this mission, not merely assumed from the prior report**: `input()`, `sys.stdin.read()`, `readline()`, `readlines()`, and iteration all still raise the expected `PermissionError` with the expected messages, in ~0.03s each. An ordinary program still completes normally (`ctrl_normal.py`, unaffected). An ordinary exception still surfaces as itself, not confused with the stdin-blocking mechanism (`ctrl_exception.py`). An infinite CPU loop still hits the timeout bound and gets killed cleanly (`ctrl_infinite.py`, unaffected by the stdin work, confirming this mission's own new probing didn't disturb the unrelated timeout mechanism). Zero orphaned `sandbox-exec`/`safe_exec_wrapper.py` processes after the full 14-fixture run, checked directly.

## Unknowns

- Whether a real human typing into the pty during an `os.read(0, ...)` hang would actually be delivered was not directly demonstrated (deliberately, per the mission's own instruction against requiring this) — inferred with high confidence from `isatty(0)`/`ttyname(0)`'s confirmation that fd 0 is a genuine, live terminal device, not separately observed as a live keystroke delivery.
- `termios`/`fcntl`-level descriptor manipulation (mission §9's explicit mention) was not separately tested — `os.dup(0)` already demonstrates descriptor-level access/preservation sufficiently to answer the mission's core question, and further termios-specific probing (e.g., changing terminal modes) was judged out of scope for *this* mission's specific question (can real input still be read), not attempted.
- The exact behavior of `os.close(0)` (the recommended-if-built mechanism) was verified only in an isolated, non-sandboxed `os.fork()` test — not inside the real `safe_exec_wrapper.py`/Seatbelt chain, since implementing it there is explicitly out of this mission's scope. A future Mission 30 should re-verify this exact behavior inside the real sandbox before relying on it, the same discipline Mission 28 applied to the `sys.stdin`-replacement mechanism.
- Whether `(allow file-write-data (subpath "/dev"))`'s write-side allowance (as opposed to the read-side one relevant to this mission's question) has any independent security implication was not investigated — out of scope for a stdin/input question, noted as a boundary this mission deliberately did not cross.

## Integrity Section

```
production changed: NO
HEAD changed: NO (525454a1dccfc91adf1aa8b01ff9b6ce8405d423, confirmed unchanged at mission start and end)
services restarted: NO (run.py, PID 54713, confirmed running throughout, same PID at mission start and end; port 5000 remained bound)
timeouts changed: NO
sandbox policy changed: NO (echo_sandbox.sb read-only throughout; the two close-vs-devnull fd0 experiments ran in a bare os.fork()'d process with zero connection to sandbox-exec, Seatbelt, or safe_exec_wrapper.py)
unrelated files changed: NO
tests changed: NO (scripts/verify_liveness_ledger.py and app/core/liveness_ledger.py were read for context — per mission §17 — but not modified; the smallest useful permanent canary is recommended, not implemented: extend f2_stdin_contract's functional check, or add a sibling check, to assert os.read(0, ...) raises OSError once a future fix lands — deliberately deferred to that future mission, since there is no real fix yet for a canary to verify)
temporary files remaining: YES — 14 fixture .py files, run_os_level_probe.py, and results.json remain at /tmp/mission29_fixtures/, entirely outside git tracking, listed here explicitly. All scratch execution directories (/tmp/mission29_scratch/) were removed, confirmed via direct listing. Zero orphaned sandbox-exec/safe_exec_wrapper.py processes remained after any test phase, checked directly and repeatedly.
```
