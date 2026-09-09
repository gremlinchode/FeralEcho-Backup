# Mission 24 — F2 Sandbox Timeout Forensic Investigation

**Date:** 2026-09-09
**Scope:** `app/core/echo_projects.py`'s F2 multi-file sandbox test (`_run_f2_multi_file()`), specifically the `"sandbox test timed out"` failure signature — identified in Mission 23 as the most common single F2 failure mode after F1 rejection.
**Constraints observed:** investigation-only; zero production code, config, timeouts, or safety controls modified; zero restarts performed (not needed — all reproduction was done via direct, bounded, isolated subprocess calls mirroring the real mechanism, never by restarting `run.py` or altering its live state); all reproductions used already-inert, already-quarantined generated code sitting in `sandbox/echo_projects/` (never loaded/promoted, per that pipeline's own design) or freshly-authored throwaway synthetic scripts under the session scratchpad; repo HEAD (`525454a1`) confirmed unchanged from mission start to mission end.

---

## 1. Question

What does `"sandbox test timed out"` actually mean underneath the label? Is it a real, correctly-functioning timeout catching a genuine hang — or is the label itself potentially mislabeling some other failure mode (a slow-but-eventually-successful run, a mis-set timeout, an instrumentation bug)?

## 2. The mechanism under test

`app/core/echo_projects.py:152-179`, `_run_f2_multi_file(project_dir: Path, timeout: int = 60)`:

```python
result = subprocess.run(
    ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={project_dir}",
     sys.executable, _SANDBOX_WRAPPER, str(project_dir), main_path, "--mode=script"],
    capture_output=True,
    text=True,
    timeout=timeout,
    cwd=os.getcwd(),
)
...
except subprocess.TimeoutExpired:
    return {"passed": False, "error": "sandbox test timed out"}
```

No `stdin=` argument is passed anywhere in this call. This single omission turned out to be the entire root cause — see §4.

## 3. Historical baseline (re-verified, not assumed from Mission 21/23)

Re-counted directly against the current, live `sandbox/echo_projects/` directory at mission start:

| Category | Count | % of 61 |
|---|---|---|
| Total directories | 61 | 100% |
| F1-blocked (zero `.py` files ever staged — the whole batch aborts before any file is written the instant one file fails F1) | 47 | 77.0% |
| Reached F2 (F1 passed for every file, real staged `.py` files exist) | 14 | 23.0% |
| — of which: `F2_TIMEOUT` (`"sandbox test timed out"`) | 4 | 6.6% of total, 28.6% of F2-reaching |
| — of which: `F2_OTHER_FAIL` (real exception/traceback) | 10 | 16.4% of total, 71.4% of F2-reaching |
| — of which: `F2_PASS` | 0 | 0% |

0/61 real success rate, consistent with Finding 91's own prior figure (that Finding measured 0/61 at a slightly earlier snapshot of this same, continuously-rotating, retention-capped directory). This mission's contribution is not the headline rate — it's explaining the second-largest failure category (`F2_TIMEOUT`) at the mechanism level.

**Sample of F1-blocked directories' actual detail** (confirming the 47/61 figure is genuinely F1 rejections, not some other silent failure): all three sampled show `BLOCKED: [SAFETY] Code failed to parse: ...` on at least one file — matching Finding 91's own documented root cause (leading prose before code, `invalid syntax (<unknown>, line 1)`) and its own partial fix. The fix reduced but did not eliminate this failure class; 77% F1-block rate on the current live sample is a real, current, ongoing figure, not stale.

## 4. Root cause of `F2_TIMEOUT`, established via direct, layered reproduction

### 4.1 The four real historical timeout cases all contain a reachable `input()` call

Corrected aggregate check (after finding and disclosing two of my own shell-script bugs along the way — see §9) across all 14 F2-reaching directories:

| Directory | Outcome | Contains `input()`? |
|---|---|---|
| `20260826T042413Z_...` | F2_TIMEOUT | **yes** |
| `20260902T151058Z_...` | F2_TIMEOUT | **yes** |
| `20260909T092123Z_...` | F2_TIMEOUT | **yes** |
| `20260909T152952Z_...` | F2_TIMEOUT | **yes** |
| 10 other F2-reaching dirs | F2_OTHER_FAIL | 3 contain `input()`, 7 do not |

**4/4 (100%) of real timeout cases contain a reachable `input()` call.** All four generated projects chose "an interactive text scenario" — an explicitly-invited creative interpretation of the project-generation spec's own wording (`echo_projects.py`'s spec text literally lists "an interactive text scenario" as a valid example alongside "a simulation, a toy model... a data visualization").

### 4.2 `input()`'s mere presence in the file is not sufficient — confirmed by direct counter-example

3 of the 14 F2-reaching directories contain `input()` calls but did **not** time out. Re-running each through the exact real F2 mechanism directly (bounded, isolated, with full untruncated stderr — the `_report.md` files themselves truncate the traceback mid-line, a known truncation class per CLAUDE.md Finding 27) showed all three fail on real, unrelated bugs that occur **before** their own `input()` line is ever reached:

- `20260824T143606Z_...`: `AttributeError: module 'game_simulation' has no attribute 'Simulation'` at `main.py:9`, `input()` sits unreached at line 16.
- `20260831T175906Z_...`: `NameError: name 'TaskFocusedPerson' is not defined` inside `simulator.py`'s `__init__`, `input()` sits unreached at line 27.
- `20260906T104355Z_...`: `NameError: name 'List' is not defined` (missing `from typing import List`) during module-level class definition, before `main()` is ever called at all.

This confirms `input()` co-occurrence is not causally sufficient by itself — direct re-execution, not text-matching, was necessary to establish causation. All three of these non-timeout cases are independently explained by ordinary generation-quality bugs (naming mismatches, missing imports) — the same general failure class already characterized elsewhere in this project's history (Finding 91 §4).

### 4.3 Why the reachable-`input()` cases genuinely hang: `stdin` inheritance, confirmed against the live process

`_run_f2_multi_file()` never sets `stdin=`, so the sandboxed subprocess inherits whatever file descriptor 0 the parent process (ultimately `run.py`) has open. Checked directly against the actual running production process, not inferred:

```
PID 54713 (python -u run.py), fd 0 → CHR 16,2 /dev/ttys002
```

**`run.py`'s real, live stdin is a genuine terminal device, not `/dev/null` and not closed.** Traced one level further: `start_echo.sh` (the watchdog wrapper `safe_restart.sh` defers to) runs `python -u run.py 2>&1 | tee -a "$WATCHDOG_LOG"` — the pipe redirects stdout only; stdin passes through unredirected from whatever shell/terminal window launched the watchdog. This matches the currently-live, confirmed process exactly.

A real terminal with nobody typing into it does not deliver EOF the way a closed file descriptor does — `input()` on a live, silent tty blocks indefinitely, waiting for keystrokes that will never arrive at an invisible background thread's sandboxed subprocess.

### 4.4 Direct, controlled reproduction of both stdin regimes, isolated and bounded

Two safe, synthetic reproductions, both using the real, unmodified sandbox mechanism (`sandbox-exec` + `echo_sandbox.sb` + `safe_exec_wrapper.py`) against one of the real historical timeout candidates (`20260826T042413Z_...`), bounded to short timeouts for safety:

- **Closed/EOF-immediate stdin** (`stdin=subprocess.DEVNULL`): process exits immediately, `EOFError: EOF when reading a line` at the real `input()` call site — no hang.
- **Live pty, nobody typing** (`pty.openpty()`, faithfully mirroring production's real `/dev/ttys002`): process **genuinely hangs**, confirmed via a bounded 6-second test timeout firing exactly as `subprocess.TimeoutExpired` — matching production's real 60-second mechanism precisely, just scaled down for a fast, safe test.

This directly, empirically confirms the causal chain end-to-end: it is specifically the live-terminal-with-no-typist condition — not `input()` alone, not the sandbox mechanism, not a slow import, not a generic hang-prone bug — that produces the exact `TimeoutExpired` → `"sandbox test timed out"` signature seen in all four real historical cases.

## 5. Process lifecycle (Phase 4) — confirmed clean, no orphan risk

Using the live-pty reproduction above: on `TimeoutExpired`, killing the `sandbox-exec` parent process cleanly terminated its Python child running inside the sandbox as well — a post-kill process scan for `sandbox-exec`/`safe_exec_wrapper` found **zero** surviving processes. No zombie/orphan risk from this failure mode; the real 60-second production timeout inherits the same clean-kill behavior (`subprocess.run(timeout=...)` internally calls `.kill()` + waits on `TimeoutExpired`, standard library behavior, unmodified here).

## 6. Instrumentation honesty (Phase 8)

`"sandbox test timed out"` is a **true, accurate label for a genuine `subprocess.TimeoutExpired`** — not a mislabeled crash, not a synthesized/fabricated string standing in for something else, not a symptom of a mis-set or too-short timeout value. The 60-second budget is not the problem; no amount of budget increase would resolve this specific failure mode, since a live tty with nobody typing never delivers input regardless of how long the process waits.

## 7. Is this a sleep/wake/lifecycle-dependent phenomenon? (Phase 10) — No, and this is worth stating explicitly

Unlike Mission 23's scheduler-liveness finding (which *was* explained by a real system-sleep event), `F2_TIMEOUT` is **fully explained by a deterministic structural interaction** — stdin inheritance plus a specific, spec-invited creative choice — independent of laptop sleep/wake state, time of day, or process uptime. It reproduces on demand, synchronously, any time such a candidate reaches F2, regardless of system power state. This mission found no evidence connecting `F2_TIMEOUT` frequency to sleep/wake cycles, and the root cause identified above requires no such connection to fully explain every observed instance.

## 8. Verdict

**VERIFIED F2 SANDBOX HANG — real, correctly-functioning `subprocess.TimeoutExpired`, catching a genuine, deterministic hang.** This is not an infrastructure defect in the sandbox or timeout mechanism (both work exactly as designed, and cleanly, per §5-6). It is a **structural spec/testability mismatch**: `echo_projects`' own generation spec explicitly invites "an interactive text scenario" as a valid, creative interpretation, while F2's automated test harness supplies whatever stdin the parent process happens to have (currently a live, unattended terminal) rather than a controlled, always-non-interactive source. Any candidate that takes this explicitly-invited interpretation is structurally destined to consume its full timeout budget and fail, regardless of code quality — this is a design gap in the spec-vs-test-harness pairing, not a code-generation quality problem, and not a bug in F1/F2/F3 themselves.

**Explanatory power over the observed historical data: complete for `F2_TIMEOUT` specifically (4/4 real cases, with the 3 apparent counter-examples independently and correctly explained by unrelated causes).** It explains 4 of 61 (6.6%) of all real historical attempts, and 4 of 14 (28.6%) of F2-reaching attempts. It does not explain the F1-blocked majority (77%, a separate, already-diagnosed-elsewhere failure class — Finding 91) or the other 10 F2_OTHER_FAIL cases (ordinary generation-quality bugs, not sandbox/timeout related).

## 9. Methodological notes — two of my own script bugs found and disclosed, per this project's standing discipline

While aggregating `input()` prevalence across all 61 directories, I introduced and then caught two separate bugs in my own throwaway shell loops, both disclosed here rather than silently corrected:

1. **A zsh glob failure** (`grep -lq "input(" "$d"*.py` erroring with `no matches found` on directories with zero staged `.py` files) — fixed by switching to `find -maxdepth 1 -name "*.py"` with an explicit empty-check.
2. **A more consequential zsh word-splitting bug**: `grep -lq "input(" $pyfiles`, with `$pyfiles` a multi-line, unquoted variable, does **not** word-split into separate arguments in zsh the way it would in bash — it was passed to `grep` as a single, nonexistent multi-line "filename," which errored (exit code 2) on every single directory. My loop's error handling silently treated that error exit code as `"no_input"` rather than flagging a script failure, producing a first-pass aggregate result (`0 directories contain input()`) that flatly contradicted four directories I had already confirmed by hand moments earlier. Caught specifically because that contradiction was checked directly rather than trusted — consistent with this session's own repeated rule against trusting aggregate/automated output without manual confirmation. Fixed by piping through `xargs grep -l` instead, which correctly word-splits regardless of shell.

Both bugs are recorded here in full, not smoothed over, per this project's explicit historical-evidence discipline (CLAUDE.md: "historical evidence/findings must never be silently rewritten — corrections must be stated explicitly").

## 10. Repository integrity check

```
git rev-parse HEAD  →  525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged from mission start)
```

No production file was modified. All reproduction commands ran against either already-quarantined `sandbox/echo_projects/*` content (never loaded/promoted by design) or freshly-created throwaway scripts. No restart of `run.py` was performed or required for this mission.

## 11. Recommendation (not applied — investigation only, per mission constraints)

If this gap is ever worth closing (a decision for Gremlin, not defaulted into here): the cleanest fix is scoping `_run_f2_multi_file()`'s own `subprocess.run()` call to `stdin=subprocess.DEVNULL` explicitly, converting a silent 60-second hang into an immediate, fast, clearly-diagnosable `EOFError` for any candidate that takes the interactive-scenario interpretation — trading a currently-opaque timeout for a fast, honest failure with a real traceback pointing at the exact `input()` call site. This does not make interactive-scenario projects succeed; it only makes their failure mode fast and legible instead of slow and generic. A further, separate design question (not addressed here) is whether the project-generation spec should keep inviting "an interactive text scenario" at all, given F2 can never meaningfully test one either way.
