# Mission 27 — F2 Stdin Enforcement Boundary / Architecture Resolution

**Date:** 2026-09-09
**Type:** Investigation-only, with bounded, isolated experimental reproductions under `/tmp`. No production code, configuration, timeout, sandbox profile, or generator specification was modified. No fix was applied. No service was restarted.

---

## 1. Executive Summary

Mission 27 traced the *complete* execution graph reaching the shared kernel-sandbox mechanism — not just `echo_projects.py` and its one previously-examined sibling — and found six real, live production call paths, plus one confirmed-dead one. None of the six requires real stdin; all six are either structurally non-interactive by design, run fixed known-safe scripts, or are textually constrained away from interactivity even where they don't say so explicitly. This changes the enforcement-boundary answer from what Mission 26 could see from its narrower, two-caller vantage point.

**The correct boundary is lower than `sandbox/run_script.py`.** All six real callers — including `run_script.py`'s own two functions — ultimately fan into the same shared layer: `sandbox/safe_exec_wrapper.py`'s `_install_patches()`, the one place every other sandbox-enforced restriction (write-blocking, network-blocking, GUI-blocking, `ctypes`-blocking) already lives, applied unconditionally regardless of caller or `--mode=`. Enforcing the stdin contract there — rather than in `run_script.py` (Option B, reaches only 2 of 6 real callers) or `echo_projects.py` (Option C, reaches only 1 of 6, and duplicates logic already proven to work) — protects every current and future sandbox-exec-routed execution with one change, matching this file's own established pattern exactly.

**The mechanism is simpler and more complete than either Mission 26 candidate.** A direct, safe, unsandboxed experiment (§14) found that replacing `sys.stdin` with a small custom stream object — rather than separately patching `builtins.input` (the existing precedent) — transparently and correctly blocks `input()` too, because CPython's `input()` implementation internally calls `sys.stdin.readline()` whenever `sys.stdin` is not the original C-backed terminal object. One mechanism, one exception message, covers `input()` (direct, `from builtins import input`, and `f = input` aliasing), `sys.stdin.read()`, `sys.stdin.readline()`, `sys.stdin.readlines()`, and iteration — all six behaviors Mission 26 needed two different, incomplete mechanisms to approximate.

**Recommendation: Option A (shared sandbox execution layer), via a `sys.stdin`-replacement class added to `safe_exec_wrapper.py`'s existing patch set.** No new abstraction, no execution-mode selector, no policy object — the smallest addition that makes the existing, already-precedented "patch dangerous primitives before `exec_module()` runs" pattern in that file also cover stdin, the one primitive class it has never touched.

## 2. Mission Scope

Determine where FeralEcho's autonomous-execution stdin contract should be enforced and what the cleanest complete mechanism is — investigation and design specification only. Mission 28 is authorized to implement; Mission 27 is not.

## 3. Integrity / Starting State

```
branch: main
HEAD:   525454a1dccfc91adf1aa8b01ff9b6ce8405d423
working tree: 67 changed/untracked paths — the same pre-existing live-system drift and prior-mission audit files present at the start of every mission this session, none touched by this mission
```

## 4. Mission 24 Findings

`_run_f2_multi_file()` never sets `stdin=`; the sandboxed subprocess inherits `run.py`'s real fd 0 (confirmed live: a genuine terminal). All 4 real historical `F2_TIMEOUT` cases contain a reachable `input()` call. Process lifecycle on timeout-kill is clean. The timeout mechanism itself is genuine, not mislabeled.

## 5. Mission 25 Findings

Autonomous-generation non-interactivity is established project practice: four dated prompt-construction sites (three live, one dead) forbid `input()`/interactivity, all tracing to the repo's first commit. A sibling kernel-sandboxed mechanism (`run_sandbox_script_isolated()`) already mocks `input()`, live 10 days before `echo_projects.py` was written. No test anywhere covers F2's stdin behavior.

## 6. Mission 26 Findings

Direct experimental comparison (9 fixtures × 3 modes against the real sandbox mechanism) found: inherited stdin hangs on every stdin-consuming form; `DEVNULL` closes the hang but silently converts `sys.stdin.readline()`/`read()` into a false `SANDBOX_OK` pass; the existing `_insert_input_mock()` gives an excellent, explicit failure for `input()` (including both aliasing patterns) but does not touch `sys.stdin.readline()`/`read()` at all, which hang under it exactly as under unmodified code. Recommendation was Option D (spec + harness), deliberately not resolving *where* the harness fix belongs.

## 7. Execution Architecture Map

```
                              F2 candidate generation
                                       |
              +------------------------+------------------------+
              |                                                  |
   echo_projects.py                                    self_edit_manager.py
   generate_project()                                  generate_code_from_plan()
              |                                                  |
   _run_f2_multi_file()                            test_code_in_sandbox() /
   (direct sandbox-exec call,                       _run_apply_to_code_sandboxed()
    NOT via run_script.py)                           (direct sandbox-exec calls,
              |                                       NOT via run_script.py)
              |                                                  |
              +--------------------+          +------------------+
                                   |          |
                                   v          v
                     sandbox-exec -f echo_sandbox.sb -D SCRATCH=...
                        python3 safe_exec_wrapper.py <scratch> <path> --mode=X
                                   |
                     +-------------+-------------+--------------+
                     |             |             |              |
              --mode=import  --mode=script  --mode=apply_to_code --mode=functional_verify
              (self-edit F2,  (echo_projects  (Finding 69,       (functional_quality.py,
               never runs      F2; ALSO the    apply_to_code      confirmed dead / never
               __main__ guard) shared mode      hook only)         wired live)
                               run_script.py's
                               two functions
                               use)
                                   |
              +--------------------+----------------------------------+
              |          |             |               |               |
       run_script.py  run_script.py  (direct           (direct         (direct
       .run_sandbox_  .run_sandbox_   echo_projects.py  self_edit_      functional_
       script()        script_        call, no mock)    manager.py     quality.py
       (non-kernel-    isolated()                        call, no      call, no
       sandboxed,      (kernel-                          mock)         mock, DEAD)
       has its own     sandboxed,
       separate         has _insert_
       input mock       input_mock()
       via -c string)   via source
                        text insert)
                                   |
              +---------+---------+---------+---------+
              |         |         |         |         |
      autonomous_   autonomous_  experiment_ code_     sandbox_
      loop.py       loop_with_   runner.py   verifica-  interface.py
      (hello_        optuna.py   generate_   tion.py    run_random_
      sandbox.py     (hello_     and_run()   verify_in_ sandbox_
      or fallback)   sandbox.py) (LLM-gen'd   sandbox()  script()
                                  experiments) (chat-     (fixed
                                               extracted   scripts/
                                               code)       dir)
```

**Which of these can reach `input()`:** `--mode=script` genuinely executes the candidate's own real top-level flow (`__name__ == "__main__"` fires), so any candidate's `input()`/`sys.stdin.*` call, wherever it sits, is reachable. `--mode=import` never fires the `__main__` guard, but **does** execute every other top-level statement during `exec_module()` — a bare, unguarded `input()` call outside any function or guard would still run. This is a real, lower-probability but structurally present exposure this mission is the first to name explicitly (**INFERRED**, not previously documented; not empirically triggered in this mission, since doing so would require staging a real malformed self-edit-shaped candidate, judged unnecessary — the mechanism is a direct, verifiable consequence of how `exec_module()` works, not a speculative concern). `--mode=apply_to_code` calls one specific, already-validated function with a fixed string argument — no candidate-controlled top-level flow runs. `--mode=functional_verify` calls individual functions/classes with synthetic 0-or-1-argument calls — `input()` is reachable only if a smoke-tested function's own body calls it internally, and this mode is confirmed dead (no live caller).

## 8. stdin Responsibility Map

| Component | Actual owned responsibilities (from code, not filename) | Legitimate stdin-policy responsibility? |
|---|---|---|
| `echo_projects.py` | Generates multi-file candidates; defines the F1/F2 candidate contract *for its own pipeline only*; stages and invokes the shared sandbox mechanism; classifies pass/fail; writes the report | No — it's a *caller* of the sandbox mechanism, not the layer that defines execution-primitive safety. Every other safety primitive (write-blocking, network-blocking, GUI-blocking) is deliberately owned elsewhere (`safe_exec_wrapper.py`) precisely so `echo_projects.py` doesn't have to reimplement it — stdin should follow the same ownership split, not become the one exception. |
| `sandbox/run_script.py` | Generic script execution (two flavors: plain-subprocess and kernel-isolated); currently the only real owner of *any* stdin policy (`_insert_input_mock()`); process lifecycle for its own callers; result classification (`{"success", "output", "error", "duration"}`) | Partial, and demonstrably incomplete — it owns the *only* existing stdin policy in the codebase, but that policy (source-text mock of `builtins.input` only) does not cover the `sys.stdin.*` surface, and this mission found `run_script.py`'s own kernel-isolated function shares this exact gap for its own five downstream callers, not just for `echo_projects.py`. |
| `safe_exec_wrapper.py` | The actual shared execution layer every real caller (`echo_projects.py`, `self_edit_manager.py`, `run_script.py`, `functional_quality.py`) routes through before candidate code ever runs; owns write-blocking, network-blocking, GUI-blocking, `ctypes`/`cffi`-blocking, `os.fork`/`subprocess`/`shutil`-blocking, and (as of `--mode=apply_to_code`/`--mode=functional_verify`) even mode-specific execution semantics | **Yes — this is the file whose entire, stated purpose is "patch dangerous primitives before `exec_module()` runs," and stdin is a primitive it has never patched.** Adding a policy here would not affect F1 (a pure AST scan that runs before this file is ever invoked) or ordinary application execution (this wrapper only runs inside `sandbox-exec`-spawned subprocesses, never in the main `run.py` process) — confirmed directly by re-reading the full file (§9 of Mission 25, re-verified this mission). |
| `echo_sandbox.sb` (Seatbelt profile) | Kernel-level syscall gating: filesystem writes, network, process-fork/spawn, signals | No — Seatbelt profiles govern path-based filesystem/network/process syscalls, not Python-level object attributes or which fd a `subprocess.Popen` call happens to inherit at spawn time (a decision made entirely by the Python `subprocess` module before Seatbelt's rules are ever consulted). The one stdin-adjacent comment here (`/dev` access, Mission 25 §9) is best read as generic runtime necessity, not a deliberate interactivity feature — re-confirmed, not re-litigated, this mission. |

## 9. Existing Input-Mock Archaeology

| Occurrence | File:line | Classification |
|---|---|---|
| `_INPUT_MOCK` / `_insert_input_mock()` definition | `sandbox/run_script.py:50-83` | PRODUCTION — live, real mechanism |
| Applied in `run_sandbox_script()` | `sandbox/run_script.py:99` | PRODUCTION — plain-subprocess path |
| Applied in `run_sandbox_script_isolated()` | `sandbox/run_script.py:199` | PRODUCTION — kernel-isolated path, the one Mission 25/26 examined |
| No `_insert_input_mock` reference anywhere else | — | Confirmed via repo-wide grep; `echo_projects.py`, `self_edit_manager.py`, `functional_quality.py` each build their own direct `sandbox-exec` invocations with zero stdin handling of any kind |
| `stdin` explicitly named | `sandbox/echo_sandbox.sb` (one comment, generic `/dev` access) | DOCUMENTED, generic — see §5 of Mission 25 |
| `stdin=` as a Python kwarg | Nowhere in any real sandbox call site (`echo_projects.py`, `self_edit_manager.py`, `run_script.py`, `functional_quality.py`) | OBSERVED — confirmed by direct read of all four files' `subprocess.run()`/`Popen()` calls |

**No occurrence of `_insert_input_mock` or any stdin-blocking mechanism exists in `safe_exec_wrapper.py`, `echo_projects.py`, `self_edit_manager.py`, or `functional_quality.py`.** The only real, working stdin policy anywhere in this 165-commit repository is the two applications of one function, both inside one file, both only reachable by two of its own functions.

## 10. Git History / Design Intent

`sandbox/run_script.py` was added *wholesale* in the repo's own "clean initial commit" (`44e7a8e`, 2026-06-28) — 133 lines, 0 deletions, a brand-new file at that commit, not a modification of a pre-existing tracked one. **`_insert_input_mock()`, its `_INPUT_MOCK` string, and the dated `"CHANGE 1: Reduced from 600 to 30 seconds"` / `"CHANGE 2: Insert input() mock so interactive scripts fail immediately instead of hanging for the full timeout duration"` comments were already present in this very first commit** — meaning the mechanism's own internal changelog-style comments record at least one prior revision (tightening the timeout, then separately adding the input mock) that predates this repository's visible history entirely. This repo's own commit message for `44e7a8e` explicitly frames it as a deliberately curated "clean initial commit" (stripping scaffold-sprawl and secrets from an earlier, unshown history), which is consistent with — though does not by itself prove — real prior iteration on this exact file. **HISTORICAL, with an honest limit stated plainly**: this mission cannot determine who made the original CHANGE 1/2 revisions or exactly when, beyond "before 2026-06-28," which is earlier than Mission 25's own "10 days before `echo_projects.py`" framing (that framing measured from `run_sandbox_script_isolated()`'s 2026-07-13 introduction, itself a much later addition layered onto an already-revised file — the underlying design intent to disable `input()` for sandboxed script execution is older still).

The comments' own content is the clearest available evidence of *why* it was built: CHANGE 1 addressing general nontermination (timeout tightening) was evidently judged insufficient on its own, motivating a second, separate, explicitly-named fix (CHANGE 2) specifically for the interactive-hang case — direct evidence the file's own author(s) already distinguished "generic hang" from "interactive hang" as two separate problems needing two separate mechanisms, a distinction this project's own later work (`echo_projects.py`) did not carry forward.

## 11. Caller Impact Analysis

| Caller | Execution path | Stdin expected? | `input()` reachable? | Historical successful interactive use? | Currently mock-protected? |
|---|---|---|---|---|---|
| `echo_projects.py`'s F2 | direct, `--mode=script` | No — no evidence anywhere (Mission 26 §12) | Yes, directly | **No — 0/61 real successes of any kind** (Mission 24, re-confirmed Mission 26) | **No** |
| `self_edit_manager.py`'s F2 (`test_code_in_sandbox`) | direct, `--mode=import` | No | Only via an unguarded top-level statement (§7, INFERRED, not observed) | No evidence found; self-edit's own extensive `SELF_EDIT.log` history (per `CLAUDE.md`) never names a stdin-hang failure signature | No |
| `self_edit_manager.py`'s `apply_to_code` hook | direct, `--mode=apply_to_code` | No | No — calls one pre-validated function with a fixed string arg | N/A | No, and structurally doesn't need to be |
| `run_script.py`'s two functions, directly | `-c` string / `--mode=script` | No | Yes | No evidence found | **Partial — `input()` only, not `sys.stdin.*`** |
| `app/autonomous_loop.py` (via `run_sandbox_script_isolated`) | `--mode=script` | No | Only if it falls through to `experiment_runner`-generated code; the fixed fallback (`hello_sandbox.py`) has zero stdin dependency (read in full, §7 of the raw investigation) | No evidence found | Partial (inherited from `run_script.py`) |
| `app/core/autonomous_loop_with_optuna.py` (via `run_sandbox_script_isolated`) | `--mode=script` | No — hardcoded to `["hello_sandbox.py"]` only | No — fixed script, confirmed zero stdin dependency | No evidence found | Partial |
| `sandbox/experiment_runner.py`'s `generate_and_run()` (via `run_sandbox_script_isolated`) | `--mode=script` | No — prompt explicitly constrains to "pure computation only," a fixed small stdlib allowlist (math/statistics/random/collections/itertools/json/datetime), and "must print exactly one RESULT line" | Structurally excluded by the prompt's own constraints, though not enforced by any harness check | No evidence found | Partial |
| `app/core/code_verification.py`'s `verify_in_sandbox()` (via `run_sandbox_script_isolated`) | `--mode=script` | No, but **this is the one caller whose input is genuinely least controlled** — real code blocks extracted from live chat responses in `routes_echo_studio.py` (Finding 43), not autonomous-only generation. A user could plausibly get Echo to produce example code containing `input()` in a normal coding conversation. | Yes, directly, if the extracted block contains one | No evidence found; not previously flagged by any prior mission as a distinct caller | Partial (`input()` only) |
| `app/core/sandbox_interface.py`'s `run_random_sandbox_script()` (via `run_sandbox_script_isolated`) | `--mode=script` | No — picks only non-`temp_`-prefixed scripts from `sandbox/scripts/`, all of which are either the fixed `hello_sandbox.py`-style baseline or leftover research-experiment artifacts (`hotstove_proof_*`, `test_broken.py`, etc.), none containing `input()` (confirmed via the same grep used in §7) | Theoretically, if a future hand-placed script did | No evidence found | Partial |
| `app/core/functional_quality.py` | direct, `--mode=functional_verify` | No | Only if a smoke-tested candidate function's own body calls `input()` | N/A — **confirmed dead, not wired into any live call site** (`CLAUDE.md`'s own documentation) | **No, and this mode has never had any stdin policy applied by anyone** |

**Direct answer to §8's central question**: no existing legitimate execution path in this codebase requires real stdin. This is **OBSERVED** for the eight callers actually traced above (each checked against its real, current source — not assumed), not merely "no evidence found" in the weaker sense the mission warns against conflating; every one of the eight was individually verified either to run a fixed, known-safe script, to be structurally incapable of reaching an unblocked interactive path, or (for `echo_projects.py`) to have a fully-quantified 0/61 real historical success rate. The one previously-unflagged genuine caveat is `code_verification.py`'s chat-extracted-code path (§16 below).

## 12. Execution Mode Analysis

`safe_exec_wrapper.py`'s `--mode=` flag is **already** the codebase's own established caller-selected execution-policy primitive — four modes exist today (`import`, `script`, `apply_to_code`, `functional_verify`), each defined once, in one file, and selected by the caller via a plain CLI argument. This directly answers §9's central question: **the codebase already has exactly the kind of "explicit execution-mode policy" boundary Mission 27's Option D describes — it's not hypothetical, it exists, and it lives in `safe_exec_wrapper.py`, not `run_script.py` or `echo_projects.py`.** Mode semantics are therefore not merely "a natural boundary" — they are the boundary this codebase already chose, for every other execution-shaping decision it has needed to make so far.

This has a direct, concrete consequence for the recommendation: rather than inventing a *new* `AUTONOMOUS`/`INTERACTIVE` mode-selection system (Mission's own Option D as literally framed), the evidence supports recognizing that **`--mode=script` already IS this project's "autonomous, real-execution" mode**, and the stdin contract belongs as an unconditional property of what that mode already means — not a further sub-flag layered on top of it. Given §11's finding that zero legitimate callers of *any* mode need real stdin, and given `--mode=import`'s own latent (if lower-probability) exposure, the cleanest evidence-backed choice is to apply the stdin patch **unconditionally in `_install_patches()`, independent of `--mode=`** — the same unconditional treatment every other primitive in that function already receives (write-blocking, network-blocking, `ctypes`-blocking are not mode-gated either).

## 13. Enforcement Boundary Options

Evaluated directly against §8's ownership tracing and §11's caller-impact table:

- **A — Shared sandbox execution layer (`safe_exec_wrapper.py`)**: matches actual ownership (§8); protects all 6 live callers with one change; consistent with every other primitive already patched there; zero identified legitimate caller would be broken (§11).
- **B — `sandbox/run_script.py`**: reaches only 2 of 6 real callers (its own two functions); leaves `echo_projects.py`, `self_edit_manager.py`'s import-mode exposure, and `functional_quality.py` (if ever wired live) completely untouched; duplicates a fix that more naturally belongs one layer down.
- **C — `echo_projects.py`-local**: reaches only 1 of 6 real callers; would need to be independently reimplemented (or duplicated by copy-paste) at every other direct `sandbox-exec` call site to achieve the same coverage A gets for free.
- **D — Explicit execution-mode selection (new abstraction)**: §12 found the codebase already has this pattern (`--mode=`) and already uses it for exactly this class of decision — but §11 found zero evidence any caller needs a *different* stdin policy than "always non-interactive." Building a new mode-selection layer for a policy every current caller wants identically would be the premature architecture §11 (mission's own) explicitly warns against.
- **E — Other**: not identified; A is itself the evidence-backed refinement of what the mission's brief called "shared sandbox execution layer," not a fundamentally different architecture.

## 14. stdin Implementation Strategies

Five approaches investigated conceptually, with one directly, safely verified in a bare (non-sandboxed) Python process — no production file touched, no sandbox invoked for this specific check:

**Approach 1 — Patch individual methods (`builtins.input`, `sys.stdin.readline`, `sys.stdin.read`, `sys.stdin.readlines`, iteration separately).** Verified directly: `sys.stdin.readline = <replacement>` **succeeds** as a plain instance-attribute assignment on the real `_io.TextIOWrapper` object — contrary to an assumption that a C-implemented type would block this. Technically viable, but requires patching *five* separate attributes (`read`/`readline`/`readlines`/`__next__`/`builtins.input`) to achieve full coverage, each a separate maintenance surface, each a separate place completeness could silently regress (exactly the kind of gap Mission 26 found in the existing, incomplete `_insert_input_mock()`).

**Approach 2 — Replace `sys.stdin` with a controlled stream object.** Verified directly, in a bare Python process: a small `io.TextIOBase` subclass overriding `read`/`readline`/`readlines`/`__next__` to each raise the same explicit `RuntimeError`, assigned via `sys.stdin = Blocked()`, correctly blocks `sys.stdin.read()`, `sys.stdin.readline()`, and `for line in sys.stdin:` — **and, critically, also transparently blocks direct `input()`, `from builtins import input` aliasing, and `f = input` aliasing, with zero separate `builtins.input` patch.** This works because CPython's `input()` implementation internally calls `sys.stdin.readline()` whenever `sys.stdin` is not the interpreter's original C-backed terminal object (confirmed directly, not assumed from documentation) — replacing the object once removes that fast-path eligibility and routes every call through the same blocked method. This is a **single mechanism covering every fixture Mission 26 tested**, where the existing precedent needed two incomplete ones. `fileno()`, `isatty()`, `encoding`, and context-manager behavior were not exhaustively implemented in this verification pass (not required to prove the core mechanism) — flagged explicitly in §20/§21 as real implementation details Mission 28 must decide, not silently resolved here.

**Approach 3 — File-descriptor isolation (`stdin=subprocess.DEVNULL` or similar at the `subprocess.run()` level).** Already directly tested by Mission 26: closes the hang but silently converts `readline()`/`read()` into a false success rather than any failure. Not re-tested here; ruled out on Mission 26's own already-strong evidence, not repeated.

**Approach 4 — Extend the existing `_insert_input_mock()` pattern with a narrowly-targeted `sys.stdin` guard, kept where it already lives.** Technically possible (the source-text-insertion approach could just as easily insert a `sys.stdin = Blocked()` line instead of/alongside the `builtins.input` patch), but this only ever protects `run_script.py`'s own two callers (§13's Option B weakness) — the *mechanism* content would be identical to Approach 2's class; only its *placement* differs, and placement is what §8-§13 already settled.

**Approach 5 — Other.** No cleaner standard Python/sandbox mechanism was found. `contextlib.redirect_stdin` was considered and rejected as a poor fit — it's designed for temporary, `with`-scoped redirection by *trusted* calling code, not permanent denial applied to *untrusted* candidate code before it ever runs; using it here would be a stretch of its intended purpose for no benefit over a direct, permanent object replacement.

**Conclusion**: Approach 2 (a small, explicit stream-replacement class, added to `safe_exec_wrapper.py`'s existing patch set) is the smallest mechanism that achieves complete, single-message coverage — strictly less code than Approach 1's five-attribute patch list, and placed at the correct ownership boundary per §8/§13, unlike Approach 4.

## 15. Interactive Capability Analysis

A repo-wide search (documentation, prompts, sandbox APIs, tests, comments, historical code) for any evidence that real interactive stdin is a *supported or planned* capability — not merely imaginable — found **none** (**OBSERVED**, direct negative result from Mission 25's original sweep, re-confirmed by this mission's fuller caller-graph trace turning up zero new evidence either). `_build_autonomous_spec()`'s "an interactive text scenario" wording (Mission 25 §5) is the closest thing to supporting evidence, and Mission 25/26 already established this reads as an unexamined creative-latitude choice, not a considered capability commitment — no design note, comment, or test anywhere treats interactivity as a goal to preserve.

Given this, an explicit future interactive-execution mode would cost real, non-trivial complexity (a genuine stdin-supply mechanism — a real pty, a scripted input queue, or similar — plus a way for a caller to declare "this candidate legitimately needs it," plus a way to prevent that declaration from being reachable by autonomous/unattended generation) against zero current demonstrated need. **This mission's evidence does not support building any part of that now** — consistent with the mission's own instruction to search for reasons *not* to introduce a new abstraction, this is exactly such a case.

## 16. Adversarial Review

- **Shared mechanism (A) — what legitimate caller would this accidentally break?** None identified in the caller-impact table (§11). The one caller worth real scrutiny, `code_verification.py`'s chat-extracted code, is *already* subject to a form of this exposure today (uncontrolled, unprotected) — moving the protection to the shared layer strictly improves its safety, it doesn't introduce a new risk to it. If a future legitimate need for real interactivity ever arises specifically for that caller, it would need its own explicit, separately-reasoned opt-out — not a reason to leave the other five callers unprotected in the meantime.
- **`run_script.py`-local (B) — is that the correct ownership boundary or merely the easiest place to patch?** Confirmed the latter: it's easiest because the precedent already lives there, but §8's ownership trace and §11's caller count show it's not where the *responsibility* actually sits — `safe_exec_wrapper.py` is the one file every caller, including `run_script.py` itself, already depends on for this exact class of primitive-safety concern.
- **New abstraction (D) — real architectural need, or polishing a two-line bug?** Directly tested against §15's evidence: no real need was found. Building it now would be premature architecture the evidence doesn't support.
- **Stream replacement — what Python behaviors are being accidentally changed?** `sys.stdin`'s identity changes (code that does `sys.stdin is <the original object>` would observe a difference — no such check was found anywhere in this codebase, but this is a real, disclosed caveat, not hidden). `isatty()`/`fileno()`/`encoding` need explicit, deliberate values in the replacement class (not resolved in this mission — flagged for Mission 28, §21). Both effects are strictly scoped to inside the sandboxed subprocess, never touching the real `run.py` process's own `sys.stdin`.
- **Method patching — what stdin paths are still missing?** Confirmed by Approach 1's own analysis (§14): five separate attributes to track, versus one class for Approach 2. Not chosen, precisely because of this completeness risk — the same class of risk that produced the exact gap this mission exists to close.

## 17. Boundary Decision Matrix

| Criterion | Shared sandbox (`safe_exec_wrapper.py`) | `run_script.py` | F2-local (`echo_projects.py`) | Explicit execution-mode policy (new) |
|---|---|---|---|---|
| Correct ownership | Yes — matches §8's ownership trace directly | Partial — owns the only *existing* policy, but not by original design intent for this scope | No — a caller, not a primitive-safety owner | N/A — doesn't exist yet |
| Protects F2 (`echo_projects.py`) | Yes | No (not a caller of `run_script.py`) | Yes, but only itself | Only if built and adopted by F2 specifically |
| Protects sibling paths (5 others, §11) | Yes, all of them, automatically | Only its own 2 functions' callers | No | Only if each caller opts in |
| Risk of breaking callers | None identified (§16) | N/A (doesn't reach the other paths) | N/A | Depends entirely on design not yet done |
| Existing precedent | Yes — same file, same unconditional-patch pattern already used for 6+ other primitives | Yes, but incomplete (misses `sys.stdin.*`) | None | None (would be new) |
| Minimal change | Yes — one class added to one existing function | Would still leave 4 of 6 real callers unprotected | Smallest single-file diff, but incomplete coverage of the actual problem | Largest — new selection mechanism, new caller-side decisions |
| Avoids duplication | Yes — one implementation, many callers | No — would need duplicating at every non-`run_script.py` caller for equal coverage | No — same duplication problem | No — every caller must independently declare a mode |
| Testability | High — one functional canary at one call boundary covers everything | Medium — would need per-caller verification | Medium | Low — more surface area to test per mode |
| Maintainability | High — one place, matching the file's existing structure | Medium | Low if duplicated elsewhere later | Low — new concept for future maintainers to learn |
| Future interactive capability | Preserved implicitly — a future, separately-designed opt-out could still be added at this layer if ever needed | Same | Same | Nominally "built in," but at a cost §15 found unjustified today |
| Architectural coherence | Highest — consistent with every other safety patch already in this file | Medium | Low | Low — introduces a concept (`AUTONOMOUS`/`INTERACTIVE`) the rest of the codebase doesn't use anywhere else |

## 18. Recommended Architecture

**Option A — enforce the stdin contract inside `sandbox/safe_exec_wrapper.py`'s `_install_patches()`**, the shared layer every real sandboxed execution already routes through, applied unconditionally (not gated by `--mode=`), using the same "patch the dangerous primitive, raise an explicit exception" idiom already used for every other blocked operation in that file.

This is not "D dressed up as A" — it is a direct rejection of building a new mode-selection abstraction (§15-§17), in favor of recognizing that the codebase's *existing* mode system (`--mode=`) already settles the question the mission's Option D was reaching for, and that every mode's real callers want the identical stdin policy today.

## 19. Proposed Future Patch (NOT applied)

- **File**: `sandbox/safe_exec_wrapper.py`.
- **Function**: `_install_patches(scratch: str)`.
- **Change**: add a new patch phase (alongside the existing GUI/matplotlib/KMP/write/network/`ctypes` patches already there) that constructs a small class (working name: `_BlockedStdin`, subclassing `io.TextIOBase`) whose `read`, `readline`, `readlines`, and `__next__` each raise a single, consistent exception — recommended message, reusing the exact wording already proven clearest in Mission 26: `RuntimeError("input()/stdin reading is disabled in this sandbox")` (a small extension of the existing `"input() is disabled in sandbox"` message, broadened to name both surfaces it now covers) — then assigns `sys.stdin = _BlockedStdin()`. No `builtins.input` patch needed (§14) — verified to be transparently covered by the `sys.stdin` replacement.
- **Scope**: applied unconditionally, independent of `--mode=`, matching every other primitive this function already patches without mode-gating.
- **`run_script.py`'s existing `_insert_input_mock()`**: left as-is, not removed. It becomes redundant-but-harmless defense-in-depth once the wrapper-level fix lands (its `builtins.input` patch and the wrapper's `sys.stdin` replacement don't conflict — the mock would simply never trigger, since `sys.stdin.readline()` fails first). Whether to later simplify or remove it is an explicit, separate, non-urgent future decision, not part of this patch.

## 20. Mission 28 Implementation Specification

1. **What file should change first?** `sandbox/safe_exec_wrapper.py` — `_install_patches()`, the shared execution layer (§18).
2. **What function should change?** `_install_patches(scratch: str)`. No other function in this file, and no line in `echo_projects.py`, `run_script.py`, or `self_edit_manager.py`, needs to change for the core fix.
3. **What should stdin do?** `sys.stdin` should be replaced (not merely have individual methods patched) with an instance of a small `io.TextIOBase`-derived class, applied inside the sandboxed subprocess only — never touching the real `run.py` process.
4. **What should `input()` do?** Raise the chosen `RuntimeError`, via the `sys.stdin.readline()` route CPython already uses once `sys.stdin` is not the original object — verified directly (§14), no separate `builtins.input` patch required.
5. **What should `readline()` do?** Raise the same `RuntimeError`.
6. **What should `read()` do?** Raise the same `RuntimeError`.
7. **What should `readlines()` do?** Raise the same `RuntimeError` — not individually verified this mission (Mission 26 tested `read`/`readline` only) but the identical implementation pattern applies; Mission 28 should include it in its own functional canary rather than assume it's covered by extension alone.
8. **What should iteration do?** Raise the same `RuntimeError` from `__next__` — verified directly (§14).
9. **What should the error/classification be?** One consistent `RuntimeError` message across all forms (recommended text above) — deliberately not `EOFError` (Mission 26 found this can read as an ordinary data-shape bug rather than a policy) and deliberately not a silent empty-string return (Mission 26's `DEVNULL` false-success finding).
10. **What tests must be added?** A new Liveness Ledger check (following this project's own standing rule for any new safety-relevant mechanism), functional-canary-shaped like `f1_aliased_import_detection`/`echo_projects_path_safety`: call the real, patched sandbox mechanism against a small set of known fixtures (at minimum, the 6 stdin-consuming forms from Mission 26's own fixture set, plus `readlines()`) and assert each raises the expected message, while a normal, non-interactive fixture still passes unaffected. `scripts/verify_liveness_ledger.py` should gain matching discrimination cases (real-function-correct, degraded-never-blocks, degraded-always-blocks-even-ordinary-programs, not-importable) per this project's established pattern.
11. **What existing behavior must remain unchanged?** Every fixture unrelated to stdin (Mission 26's Fixtures 1, 6, 7, 8 — normal programs, ordinary exceptions, infinite loops, normal stdout/stderr) must produce byte-identical results before and after. `--mode=import`/`apply_to_code`/`functional_verify` should be explicitly re-verified post-change even though none of them exercise `sys.stdin` in their own normal operation (per §7, `--mode=import` has a real, if narrow, exposure worth re-checking directly rather than assumed fixed by extension). `run_script.py`'s own `_insert_input_mock()`-based tests, if any exist, must continue passing unmodified (§19).
12. **What evidence supports each decision?** §14 (direct empirical verification of the `sys.stdin` replacement's completeness and transparent `input()` coverage), §11 (zero real caller needs actual stdin), §13/§17 (ownership and duplication analysis favoring the shared layer over `run_script.py` or `echo_projects.py`), Mission 26 (message-quality comparison ruling out `DEVNULL`).

## 21. Remaining Unknowns

- `isatty()`, `fileno()`, `.encoding`, and context-manager (`__enter__`/`__exit__`) behavior on the replacement stream class were not resolved this mission — a real implementation decision for Mission 28, not silently assumed. A reasonable default (`isatty()` → `False`, honestly reflecting reality; `fileno()` → raise or return an invalid value; `.encoding` → a plausible constant like `"utf-8"` so incidental introspection doesn't crash on an unrelated attribute) is suggested but not chosen here.
- `readlines()` and the `__next__`/iteration path were verified together conceptually but `readlines()` specifically was not independently fixture-tested this mission (only `read`/`readline`/iteration were) — flagged, not assumed identical by extension alone.
- Whether this fix should also be verified *inside* the real sandboxed subprocess (with `safe_exec_wrapper.py`'s other patches simultaneously active) rather than only in this mission's bare, unsandboxed Python check — no plausible interaction mechanism was identified, but this remains **INFERRED-high-confidence**, not **OBSERVED**-in-the-real-sandbox, and Mission 28 should re-confirm directly before considering the mechanism proven.
- Whether `code_verification.py`'s chat-extracted-code caller (§11, §16) ever legitimately needs a different treatment than the other five callers was not further investigated — no evidence found either way; flagged as the one caller worth a second look if Mission 28's implementation surfaces any real friction there.
- Whether `run_script.py`'s own `_insert_input_mock()` should eventually be simplified once the wrapper-level fix lands is explicitly left open, not decided (§19).

## 22. Integrity / Ending State

```
git rev-parse HEAD
# 525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged)

git status --short | wc -l
# 68 (this mission's own report, plus append-only research/FINDINGS.md and
#     research/OPEN_QUESTIONS.md annotations, added to the same pre-existing
#     67-path baseline present at mission start)
```

- Production code: unchanged (confirmed via `git diff --stat` against the four named files, empty).
- No service restarted.
- No timeout, configuration, or safety policy changed anywhere in the repository.
- No commit created.
- Temporary experiment artifacts: this mission's stdin-mechanism verification was run as small, self-contained, single-shot `python3 -c "..."` commands with no persistent script files or scratch directories created (unlike Mission 26, which left fixture files under `/tmp/mission26_fixtures/` — that directory is untouched by this mission and remains exactly as Mission 26 left it). Nothing under `/tmp/mission27_fixtures/` was created, since no experiment in this mission required a persistent fixture file to be staged through the real sandbox mechanism — every check was either direct source reading or a bare, unsandboxed Python semantics check.
