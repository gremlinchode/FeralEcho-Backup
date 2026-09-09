# Mission 26 — F2 stdin Contract Resolution / Fix Design Experiment

**Date:** 2026-09-09
**Type:** Investigation-only, with bounded, isolated experimental reproductions under `/tmp`. No production code, configuration, timeout, sandbox profile, generator specification, or safety policy was modified. No service was restarted. No fix was applied.

---

## 1. Executive Summary

Three candidate mechanisms were empirically compared, using the real, unmodified kernel sandbox stack (`sandbox-exec` + `echo_sandbox.sb` + `safe_exec_wrapper.py --mode=script`) — the same one `_run_f2_multi_file()` actually uses — against 9 fixtures covering direct `input()`, `sys.stdin.readline()`, `sys.stdin.read()`, two aliasing patterns, an ordinary exception, an infinite loop, normal stdout/stderr, and a normal program.

The result is more precise than either Mission 24 or Mission 25 anticipated, and changes the shape of the recommendation: **the existing sibling mechanism (`_insert_input_mock()`) and the previously-proposed `stdin=subprocess.DEVNULL` fix are each only *partially* sufficient, and for different reasons.** `_insert_input_mock()` only patches the `input()` builtin — it does **not** intercept `sys.stdin.readline()` or `sys.stdin.read()`, both of which hang for the full timeout under the mock exactly as they do today, unmodified. `stdin=subprocess.DEVNULL` closes the hang for every stdin-consuming form tested, but for `readline()`/`read()` specifically it does so by silently returning an empty string and letting the program continue and report success (`SANDBOX_OK`) — a real, previously-uncharacterized risk of false-positive "passes" for candidates whose interactive logic never actually ran.

**Primary recommendation: D (specification + harness alignment)** — not because it "sounds safest," but because the experiment directly answers Mission's §13 question set: fixing only the specification leaves the harness structurally vulnerable to any model that generates `input()`/`readline()`-based code regardless of what the prompt says (this project's own history shows models routinely deviate from prompt constraints); fixing only the harness leaves the specification inviting a creative direction that would then be deterministically engineered to fail every time, wasting real, non-trivial compute (`council_generate_project()`'s own documented cost: 1 planning deliberation + N per-file generations + up to 3 review calls) on an interpretation that can never succeed. These are two manifestations of one unresolved contract mismatch, not two independent bugs — evidence-backed, not assumed.

The specific harness change this evidence supports is **not** a blind adoption of either Option A or Option B as originally framed — it's a refinement: extend the *existing, precedented* input-mock pattern to also cover `sys.stdin.readline`/`sys.stdin.read`, closing the exact gap this mission discovered, rather than switching to `DEVNULL`'s coarser, silently-permissive behavior.

## 2. Mission Scope

Investigation-only. Determine, experimentally rather than by assumption, which of Options A (existing input-mock precedent), B (`stdin=DEVNULL`), C (specification-only), or D (specification + harness) is best supported by evidence — and whether Option D is actually necessary or merely intuitively appealing.

## 3. Integrity / Starting State

```
branch: main
HEAD:   525454a1dccfc91adf1aa8b01ff9b6ce8405d423
working tree: 66 changed/untracked paths (all pre-existing live-system drift and prior-session audit files, none touched by this mission)
```

All experimentation was performed under `/tmp/mission26_fixtures/` and `/tmp/mission26_scratch/` — entirely outside git tracking. No file inside the repository was written, edited, or staged during this mission's experiments.

## 4. Mission 24 Findings Used

- `_run_f2_multi_file()` never sets `stdin=`; the sandboxed subprocess inherits whatever fd 0 the real `run.py` process has (confirmed live: a genuine terminal, `/dev/ttys002`).
- All 4 real historical `F2_TIMEOUT` cases contain a reachable `input()` call; a real pty with nobody typing reproduces the hang; `stdin=subprocess.DEVNULL` instead produces an immediate `EOFError`.
- Process lifecycle on timeout-kill is clean (no orphans).
- The timeout mechanism itself is genuine and correctly functioning — not a mislabeled or broken failure mode.

## 5. Mission 25 Findings Used

- `sandbox/run_script.py`'s `run_sandbox_script_isolated()` — using the *identical* kernel-sandbox invocation shape `_run_f2_multi_file()` uses — already applies `_insert_input_mock()` before staging any script, and has done so since the function's introduction (2026-07-13), 10 days before `echo_projects.py` (2026-07-23).
- Three live prompt-construction sites elsewhere in the codebase explicitly forbid `input()`/interactivity in autonomous generation, all dated to the repo's first commit.
- `echo_projects.py`'s own `_build_autonomous_spec()` is the one place in the codebase inviting "an interactive text scenario," unchanged since introduction.
- No test or Liveness Ledger check anywhere covers F2's stdin behavior.
- Contract determination: Autonomous F2, as established project practice not an explicit rule for this file.

This mission does not re-litigate those findings; it tests, for the first time, what each *candidate fix* actually does under real, varied conditions.

## 6. `_insert_input_mock()` Forensic Analysis

Read directly from `sandbox/run_script.py` (lines 50-83), and exercised live via direct import (`sys.path.insert(0, "sandbox"); import run_script; run_script._insert_input_mock(...)`) rather than assumed from its docstring alone.

**Mechanism (OBSERVED):**

```python
_INPUT_MOCK = (
    "import builtins; "
    "builtins.input = lambda *a, **kw: (_ for _ in ()).throw("
    "RuntimeError('input() is disabled in sandbox'))\n"
)

def _insert_input_mock(script_text: str) -> str:
    """... inserts after any leading docstring and/or `from __future__ import ...`
    line(s) ..."""
```

Precise properties, all confirmed directly (not inferred from the docstring):

- **Source-text transformation, not a runtime monkeypatch applied from outside.** It's a single line of real Python (`import builtins; builtins.input = lambda ...`) textually inserted into the candidate's own source, at the top (after any docstring/`__future__` imports, via a real `ast.parse()` walk of the candidate's own body to find the correct insertion point — falls back to prepending unconditionally if the source doesn't parse, deliberately not blocking a genuine syntax error from surfacing on its own).
- **Replaces the `builtins.input` attribute globally**, not `sys.stdin`, not any per-module reference. Because it runs as the literal first executable statement of the candidate (module-level, before any of the candidate's own top-level code), any subsequent `import input` re-binding, `f = input` aliasing, or direct call all observe the already-mocked function — confirmed empirically (Fixtures 5a/5b below), not assumed from reading the source alone.
- **Does not touch `sys.stdin` in any way.** No reference to `sys.stdin`, `readline`, or `read` exists anywhere in `_insert_input_mock()` or `_INPUT_MOCK`. This is the mission's single most important forensic finding — confirmed both by direct source reading and by the fixture experiment (§9) showing `sys.stdin.readline()`/`sys.stdin.read()` are completely unaffected by this mechanism.
- **Result on interception:** a real, specific `RuntimeError('input() is disabled in sandbox')` — distinguishable from an ordinary candidate-code exception (Fixture 6) both by message content and, more importantly, by being *instantaneous* rather than delayed.
- **Operates before compilation/execution of the candidate's own logic**, and before sandboxing in the sense that it's baked into the source file that then gets staged and passed to the sandbox-exec + wrapper mechanism — the mock line executes *inside* the sandbox (same process, same patches from `safe_exec_wrapper.py` already installed), not as a separate pre-flight step outside it.
- **Effect on legitimate non-interactive programs:** none observed (Fixtures 1, 6, 8 below are byte-for-byte unaffected across all three modes).
- **Limitation relevant to F2, newly discovered by this mission's fixtures, not previously documented anywhere in this codebase**: does not intercept `sys.stdin.readline()` or `sys.stdin.read()` — both hang identically with or without the mock applied.

**Execution-path diagram (both real call chains, as they exist today — neither modified):**

```
run_sandbox_script_isolated(script_path)                    _run_f2_multi_file(project_dir)
        |                                                             |
        v                                                             v
  open(script_path).read()                                staged project_dir/main.py
        |                                                    (files already written
        v                                                     by generate_project(),
  _insert_input_mock(raw_text)   <-- APPLIED HERE              unmodified source)
        |                                                             |
        v                                                             |
  write mocked_content to scratch/_script.py                          |
        |                                                             |    <-- NOT APPLIED
        v                                                             v         anywhere
  subprocess.run(["sandbox-exec", "-f", echo_sandbox.sb,   subprocess.run(["sandbox-exec", "-f", echo_sandbox.sb,
     "-D", SCRATCH=..., sys.executable,                       "-D", SCRATCH=..., sys.executable,
     safe_exec_wrapper.py, scratch, mocked_path,               safe_exec_wrapper.py, project_dir, main_path,
     "--mode=script"], ..., timeout=timeout)                   "--mode=script"], ..., timeout=timeout)
        |    (stdin= not set -> inherits parent's fd 0             |    (stdin= not set -> inherits parent's
        |     regardless of the mock; the mock protects             |     fd 0, no source-level protection
        |     input() specifically, independent of stdin           |     of any kind)
        |     source)                                               |
        v                                                             v
  safe_exec_wrapper.py --mode=script                        safe_exec_wrapper.py --mode=script
  (installs write/network/GUI patches,                      (installs the same patches,
   loads module as "__main__")                                loads module as "__main__")
        |                                                             |
        v                                                             v
  mock line runs FIRST (module-level),                       candidate's own top-level code
  patches builtins.input before any                          runs directly; input() or
  candidate code executes                                    sys.stdin.* inherits whatever
                                                               fd 0 actually is
```

**Important structural note, confirmed directly**: `run_sandbox_script_isolated()` *also* never sets `stdin=` on its own `subprocess.run()` call — its protection against `input()` comes entirely from the source-text mock, not from any stdin redirection. This means `run_sandbox_script_isolated()` itself is *not* fully protected against `sys.stdin.readline()`/`sys.stdin.read()` either — the sibling mechanism Mission 25 held up as "already solving this" has the same gap `echo_projects.py` has, just narrower in scope (it covers `input()`, `echo_projects.py`'s F2 covers nothing). This was not previously known and is a genuinely new finding of this mission, not carried forward from Mission 25.

## 7. Interactivity Fixture Design

Nine fixtures, written to `/tmp/mission26_fixtures/`, matching the mission's required set exactly (Fixtures 5a/5b split the combined "Fixture 5" into its two named sub-patterns for precision):

| Fixture | File | Tests |
|---|---|---|
| 1 | `fixture1_normal.py` | Ordinary autonomous computation, no I/O |
| 2 | `fixture2_direct_input.py` | `x = input("Enter something: ")` |
| 3 | `fixture3_stdin_readline.py` | `x = sys.stdin.readline()` |
| 4 | `fixture4_stdin_read.py` | `x = sys.stdin.read()` |
| 5a | `fixture5a_from_builtins_import.py` | `from builtins import input; x = input()` |
| 5b | `fixture5b_aliased_ref.py` | `f = input; x = f()` |
| 6 | `fixture6_ordinary_exception.py` | `raise RuntimeError("ordinary failure")` |
| 7 | `fixture7_infinite_loop.py` | Pure-CPU `while True: x += 1`, no I/O |
| 8 | `fixture8_stdout_stderr.py` | Normal stdout + stderr output |

Each was run through the real, unmodified kernel sandbox mechanism under three modes, bounded to an **8-second timeout** (scaled down from production's real 60s for speed/safety, per this mission's own instruction not to let an experiment sit indefinitely):

- **Mode 1 — current F2 behavior**: a real `pty.openpty()` pair supplies stdin (faithfully mirroring production's real, confirmed `/dev/ttys002` — a live terminal with nobody typing), unmodified source.
- **Mode 2 — `stdin=subprocess.DEVNULL`**: unmodified source, explicit closed stdin.
- **Mode 3 — real `_insert_input_mock()` applied**, source pre-processed via direct import of the real, unmodified function, **then run with the same real-pty inherited stdin as Mode 1** — deliberately isolating whether the mock *alone* (independent of any stdin= change) is sufficient.

## 8. Current-Inheritance Results (Mode 1)

| Fixture | Result | Elapsed |
|---|---|---|
| 1 (normal) | `rc=0`, `SANDBOX_OK` | 0.03s |
| 2 (`input()`) | **TIMED OUT**, killed (`rc=-9`) | 8.01s |
| 3 (`readline()`) | **TIMED OUT**, killed | 8.01s |
| 4 (`read()`) | **TIMED OUT**, killed | 8.01s |
| 5a (imported `input`) | **TIMED OUT**, killed | 8.01s |
| 5b (aliased `input`) | **TIMED OUT**, killed | 8.01s |
| 6 (exception) | `rc=1`, real traceback | 0.03s |
| 7 (infinite loop) | **TIMED OUT**, killed | 8.00s |
| 8 (stdout/stderr) | `rc=0`, `SANDBOX_OK` | 0.03s |

Confirms Mission 24's finding across a wider fixture set: every stdin-consuming form hangs identically for the full timeout under current, unmodified F2 behavior. No orphaned processes after any kill (checked directly post-experiment).

## 9. DEVNULL Results (Mode 2)

| Fixture | Result | Elapsed |
|---|---|---|
| 1 (normal) | `rc=0`, `SANDBOX_OK` | 0.03s |
| 2 (`input()`) | `rc=1`, `EOFError: EOF when reading a line` | 0.03s |
| 3 (`readline()`) | **`rc=0`, `SANDBOX_OK`** — got `''`, program completed normally | 0.03s |
| 4 (`read()`) | **`rc=0`, `SANDBOX_OK`** — got `''`, program completed normally | 0.03s |
| 5a (imported `input`) | `rc=1`, `EOFError` | 0.03s |
| 5b (aliased `input`) | `rc=1`, `EOFError` | 0.03s |
| 6 (exception) | `rc=1`, real traceback (unaffected) | 0.03s |
| 7 (infinite loop) | **TIMED OUT** (unaffected — not a stdin issue) | 8.00s |
| 8 (stdout/stderr) | `rc=0`, `SANDBOX_OK` (unaffected) | 0.03s |

**The critical finding**: `DEVNULL` converts every `input()`-based hang into a fast, clean `EOFError` — but for `sys.stdin.readline()`/`sys.stdin.read()`, it does **not** produce a failure at all. It produces a *silent pass*: the candidate reads an empty string (the standard POSIX behavior of reading from an already-closed/empty stream) and, in these fixtures, continues to completion and reports `SANDBOX_OK`. A generated project whose interactive logic genuinely depended on real input would report success under F2 without its core logic ever having been meaningfully exercised.

## 10. Input-Mock Results (Mode 3)

| Fixture | Result | Elapsed |
|---|---|---|
| 1 (normal) | `rc=0`, `SANDBOX_OK` (unaffected) | 0.03s |
| 2 (`input()`) | `rc=1`, `RuntimeError: input() is disabled in sandbox` | 0.03s |
| 3 (`readline()`) | **TIMED OUT, killed — mock does not help at all** | 8.01s |
| 4 (`read()`) | **TIMED OUT, killed — mock does not help at all** | 8.01s |
| 5a (imported `input`) | `rc=1`, `RuntimeError: input() is disabled in sandbox` (correctly caught despite the alias) | 0.03s |
| 5b (aliased `input`) | `rc=1`, `RuntimeError: input() is disabled in sandbox` (correctly caught despite the alias) | 0.03s |
| 6 (exception) | `rc=1`, real traceback (unaffected) | 0.03s |
| 7 (infinite loop) | **TIMED OUT** (unaffected — not a stdin issue) | 8.00s |
| 8 (stdout/stderr) | `rc=0`, `SANDBOX_OK` (unaffected) | 0.03s |

**The other critical finding**: applying the real, unmodified `_insert_input_mock()` — with stdin still inherited from a live pty, exactly like current production — fully and cleanly resolves `input()` in every form tested, including both aliasing patterns, with a self-documenting, project-specific error message. But it leaves `sys.stdin.readline()`/`sys.stdin.read()` **completely unprotected** — Fixtures 3 and 4 hang for the full timeout under the mock exactly as under current, unmodified behavior. Adopting this existing precedent as-is would only partially close the vulnerability Mission 24 found.

## 11. Specification Archaeology (Investigation D)

`_build_autonomous_spec()`'s text — "*a simulation, a toy model, an interactive text scenario, a data visualization, etc. — creative interpretation is expected*" — is genuinely ambiguous on its face (DOCUMENTED, re-confirmed by direct reading). Nothing in the surrounding language specifies whether "interactive" means real stdin consumption, a scripted/simulated exchange using predefined data, or merely conversational-sounding output with no actual interaction loop.

This mission does not resolve that ambiguity from the text alone — it resolves it **empirically**: 100% (7/7) of the real historical `echo_projects` candidates that took this interpretation chose literal, direct `input()` calls (re-confirmed via Mission 24's own historical grep, not re-derived here), and this mission's own fixture set shows that even a maximally simple, idiomatic realization of "interactive text scenario" naturally reaches for `input()` or `sys.stdin.*` — there is no evidence anywhere in the codebase, the generated corpus, or the models' own realized behavior of the "simulated interaction, no real stdin" reading ever being produced in practice. **OBSERVED**, not assumed: whatever the phrase might theoretically permit, its only ever-realized meaning in this codebase's real history is real stdin consumption.

## 12. Historical Success Analysis (Investigation E)

A fresh, independent sweep (not reused from Mission 25) for any evidence of stdin ever being deliberately supplied to an F2 candidate — commit messages (`git log --all -i --grep="stdin"`), source comments, test fixtures — returned **zero hits** anywhere in the repository's full history. Combined with Mission 24's confirmed 0/61 real F2-reaching success rate, this mission finds **no evidence, of any kind, that actual interactive stdin has ever been a successful, intended, or even attempted capability of F2.** Stated explicitly per the mission's own instruction: absence of evidence is reported as absence of evidence, not converted into proof that interactivity was never intended — see §16 for what remains genuinely unresolved.

## 13. Failure Classification Analysis (Investigation F)

| Mechanism | `input()` outcome | `readline()`/`read()` outcome | Diagnosability |
|---|---|---|---|
| Current (inherited stdin) | 60s timeout, generic `"sandbox test timed out"` | 60s timeout, same generic label | Poor — indistinguishable from an infinite loop (Fixture 7 produces the identical label) |
| `DEVNULL` | Immediate `EOFError` | Immediate silent **success** (`SANDBOX_OK`) | Good for `input()`; actively misleading for `readline()`/`read()` — a real defect looks like a pass |
| Input-mock (as-is) | Immediate, explicit `RuntimeError('input() is disabled in sandbox')` | 60s timeout, same generic label as current behavior | Best-in-class for `input()`; no better than doing nothing for `readline()`/`read()` |

None of the three, as they exist today, gives a uniformly truthful, diagnosable classification across every stdin-consuming form. The mock's `input()` message is the clearest failure signal observed anywhere in this experiment; `DEVNULL`'s uniform coverage is real but comes at the cost of converting a subclass of genuine defects into false passes.

## 14. Adversarial Comparison (Investigation G)

**Option A (input-mock, as-is) — strongest counterargument, and it holds:** incomplete interception. This mission directly demonstrated the mock does not cover `sys.stdin.readline()`/`sys.stdin.read()` — a real, not hypothetical, gap. Adopting Option A alone would still leave the exact hang class Mission 24 found reachable via a different, equally idiomatic stdin-consumption pattern. The "duplicated sandbox logic" concern is weaker: the mock is a small, self-contained text insertion, not a parallel reimplementation of anything F1/F2 already do.

**Option B (`DEVNULL`) — strongest counterargument, and it holds:** the resulting classification is not merely "less clear" but actively wrong for a subclass of candidates — `readline()`/`read()`-based interactivity silently degrades to false success rather than any failure at all. This is worse than Mission 24's original framing suggested (that framing treated `DEVNULL` as a uniformly-good "fast, honest failure" fix; this mission found it is not honest for two of the four stdin-consumption patterns tested). The "inconsistent with existing project precedent" concern also holds: `DEVNULL` would be a wholly new pattern in this codebase, where the mock-based approach already has a 10-day-earlier precedent for the identical execution mechanism.

**Option C (spec-only) — strongest counterargument, and it holds:** confirmed directly against §13's own question — a specification change is a prompt-level instruction, not an enforcement mechanism. F1's AST scanner (traced directly, not assumed) never checks for `input()`/interactivity in any form; nothing in the harness would change. This project's own extensive, self-documented history (`CLAUDE.md`'s many self-edit hallucination findings) already establishes that generated code routinely deviates from explicit prompt constraints — the four existing sibling prompts that already forbid `input()` elsewhere in this codebase have not eliminated `input()`-shaped generation attempts *at those other sites* either (this mission did not independently verify the self-edit pipeline's own historical `input()` rate, but the general pattern of prompt-noncompliance is already well-documented in this project's own findings history, cited here as HISTORICAL precedent, not re-derived).

**Option D (spec + harness) — strongest counterargument, and it holds partially:** redundancy is a real, legitimate concern if the harness fix is complete on its own (a fully-hardened harness makes the spec's wording moot from a safety standpoint). But per §16 below, a harness-only fix still leaves the specification actively inviting an interpretation that would then be *guaranteed* to fail every time it's chosen — real generation compute spent on a dead end, not a safety issue but a real efficiency/honesty one. The "could make legitimate future interactive F2 experiments impossible" concern is worth taking seriously and is addressed directly in §17.

## 15. Decision Matrix

| Criterion | Input Mock (as-is) | DEVNULL | Spec Only | Spec + Harness |
|---|---|---|---|---|
| Prevents PTY hang (`input()`) | Yes — OBSERVED | Yes — OBSERVED | No (probabilistic reduction only) — INFERRED | Yes, if harness component covers all forms — INFERRED |
| Prevents PTY hang (`readline`/`read`) | **No — OBSERVED** | Yes — OBSERVED | No — INFERRED | Yes, only if harness is extended beyond the as-is mock — OBSERVED gap, INFERRED fix |
| Preserves normal autonomous execution | Yes — OBSERVED (Fixtures 1/6/8 unaffected) | Yes — OBSERVED | Yes (no harness change) | Yes, if implemented correctly — INFERRED |
| Gives diagnosable failure (`input()`) | Best — OBSERVED (explicit, self-documenting message) | Good — OBSERVED (`EOFError`, generic but real) | N/A (no harness change) | Best, inherits mock's clarity — INFERRED |
| Gives diagnosable failure (`readline`/`read`) | **Poor — OBSERVED (still a bare timeout)** | **Actively misleading — OBSERVED (silent false success)** | N/A | Needs a real fix beyond either as-is option — OBSERVED gap |
| Existing project precedent | Strong — HISTORICAL (10 days prior, identical invocation shape) | None — OBSERVED (`DEVNULL` appears nowhere else in this codebase's sandbox mechanisms) | Strong, at the prompt level — HISTORICAL (4 sibling sites) | Strong on both halves — HISTORICAL |
| Requires source transformation | Yes — OBSERVED | No | No | Yes, on the harness half |
| Requires production changes | Yes | Yes | Yes (prompt text only) | Yes, both spec and harness |
| Protects against model noncompliance | Yes, for `input()` only | Yes, for hang; no for silent-false-success | **No — this is C's defining weakness, confirmed by F1 tracing** | Yes |
| Keeps future interactive capability possible | No (permanently disables `input()`) | Partially (silently no-ops rather than erroring) | Yes, until harness changes | Depends entirely on implementation — a real design choice, not resolved here |
| Architectural coherence | High — reuses an existing, precedented mechanism | Low — introduces a pattern with no precedent elsewhere in this codebase | Low alone — doesn't resolve the harness-side half of the mismatch | Highest, if both halves are done consistently |
| Implementation complexity | Low (already exists; would need extension for full coverage) | Very low (one kwarg) | Very low (prompt text edit) | Moderate (both halves) |

Scoring methodology: qualitative, evidence-anchored per cell (each cell cites the specific fixture result or documented fact it rests on) rather than a numeric weighted score — per this mission's own instruction to use evidence, not arbitrary scoring, and consistent with the discipline established across Missions 24/25.

## 16. The Most Important Question (§13 of the brief)

**"If we only remove 'an interactive text scenario' from the generator specification, have we actually fixed the F2 architectural defect?"**

**No.** F1's AST scanner (traced directly in this mission and confirmed unchanged from Mission 24/25's reading) has no `input()`/interactivity check of any kind — it blocks specific dangerous *operations* (exec, eval, os.system, subprocess, file writes, self-edit-escalation calls), never this class of behavior. Nothing in the harness would change. A model that generates `input()`-based code for any reason other than following this one specific invitation (misreading a different part of the spec, defaulting to a common training-data pattern for "build a program that does X" prompts) would still hang F2 for the full timeout, exactly as today.

**"If we only enforce non-interactive stdin in the harness, have we actually fixed the specification defect?"**

**No, in a distinct sense.** Even a perfectly-hardened harness (covering `input()`, `readline()`, and `read()` uniformly) leaves the specification still telling models that "an interactive text scenario" is a valid, encouraged creative direction — one that would then be deterministically engineered to fail at F2 every single time it's chosen. This spends real compute (per `council_generate_project()`'s own documented cost model: a planning deliberation, N per-file generations each running their own internal council, up to 3 review calls) on an interpretation the system itself has now guaranteed can never succeed. This is not a safety defect once the harness is fixed, but it is a real, evidence-supported inefficiency and honesty gap in the specification that a harness fix alone does not touch.

**"Are these two independent defects, or two manifestations of the same contract mismatch?"**

**Two manifestations of one mismatch**, not two independent bugs. The evidence for this: fixing either side alone leaves the *other* side's exact symptom fully exposed (a harness-only fix leaves a now-permanently-failing invitation in the spec; a spec-only fix leaves the harness exactly as vulnerable as it is today to any non-compliant generation). Both trace to the same root fact Mission 25 established — nobody made the generator and the evaluator agree about interactivity at the point `echo_projects.py` was written — and closing only one side does not make that underlying disagreement go away, it only relocates which side's symptom is currently visible.

## 17. Primary Recommendation

```text
RECOMMENDATION: D
```

**Why**, mapped against the mission's own eight satisfaction criteria:

1. **Strongest evidence** — §16 directly answers the mission's own decisive question set: C alone and (as originally scoped) A/B alone each leave a real, evidence-demonstrated gap; only addressing both sides closes what this mission actually found.
2. **Smallest justified architectural change** — the harness half is an *extension* of an already-existing, already-precedented mechanism (§6), not a new one; the spec half is a prompt-text edit, the smallest possible change at that layer.
3. **No unnecessary behavior changes** — confirmed directly: neither the mock nor `DEVNULL` altered Fixtures 1/6/8 (ordinary programs, ordinary exceptions, ordinary output) in any way, across all three modes tested.
4. **Protection against silent 60-second hangs** — requires closing the `readline()`/`read()` gap this mission discovered, which neither Option A (as-is) nor Option B fully closes; D is the only option whose harness half can be defined to actually satisfy this criterion.
5. **Truthful failure classification** — the mock's `input()` message is the best-observed outcome in this entire experiment; extending that same pattern (rather than switching to `DEVNULL`) preserves that clarity for `readline()`/`read()` too, avoiding `DEVNULL`'s confirmed false-success risk.
6. **Consistency with existing FeralEcho architecture** — D's harness half reuses a 10-day-earlier, same-invocation-shape precedent (`run_sandbox_script_isolated()`); D's spec half brings `echo_projects.py` in line with the four sibling sites that already forbid interactivity elsewhere in this codebase.
7. **Maintainability** — one mechanism (an extended input/stdin mock), reused across two call sites, rather than two divergent stdin-handling strategies living side by side in the same codebase.
8. **Testability** — a mock-based approach produces a distinct, assertable exception type/message per stdin-consumption form, which is straightforward to cover with exactly the kind of functional-canary Liveness Ledger check this project already builds for every other safety-relevant mechanism (and which §5/§6 of Mission 25 found conspicuously absent here).

**This is not "D because it sounds safest."** Options A and B were tested in full, on their own terms, before this conclusion was reached, and both were found genuinely, specifically insufficient — A structurally (misses two of four tested stdin forms), B semantically (silently converts a real defect class into a false pass). D is the only option this mission's own evidence leaves standing once both are examined this closely.

## 18. Exact Proposed Future Change (NOT applied in this mission)

Stated precisely, for a future, separate, human-reviewed change — no part of this was implemented:

- **Harness half**: extend the pattern already used by `_insert_input_mock()` to also patch `sys.stdin.readline` and `sys.stdin.read` (and plausibly `sys.stdin.readlines`/iteration over `sys.stdin`, not individually tested this mission — see §19) with the same self-documenting-`RuntimeError` shape, rather than adopting `stdin=subprocess.DEVNULL`. This closes the exact gap found in §10 while preserving the mock's superior diagnosability found in §13. Whether this extension is added to `run_script.py`'s existing `_insert_input_mock()` (benefiting both call sites) or as a new, `echo_projects.py`-specific mechanism is a real design choice not resolved here.
- **Specification half**: revise `_build_autonomous_spec()`'s wording so it no longer invites "an interactive text scenario" as a creative-interpretation example, consistent with the non-interactive framing already used at the four sibling prompt-construction sites elsewhere in this codebase (§11 of Mission 25). Whether to replace it with a different example (e.g., a *simulated* interaction represented via predefined data, which this mission found no evidence models currently produce unprompted) or simply drop it is a real, undecided design choice.
- **New Liveness Ledger check** (per this project's own standing rule for any new safety-relevant mechanism): a functional canary confirming the extended mock still correctly intercepts all covered stdin forms and does not regress ordinary program execution — mirroring the discrimination-case shape already used throughout `scripts/verify_liveness_ledger.py`.

None of this was written, staged, or applied during Mission 26.

## 19. What Was NOT Changed

- No file inside the repository (tracked or otherwise) was created, edited, or deleted.
- `app/core/echo_projects.py`, `sandbox/run_script.py`, `sandbox/safe_exec_wrapper.py`, `sandbox/echo_sandbox.sb`: read-only for the entire mission.
- No timeout value, subprocess argument, generator prompt, environment variable, or safety policy was altered anywhere in production.
- `run.py`, Ollama, the watchdog, and every other live service were left untouched and unrestarted throughout.
- Temporary fixtures and scratch directories under `/tmp/mission26_fixtures/` and `/tmp/mission26_scratch/`: the scratch execution directories (`/tmp/mission26_scratch/`) were deleted after the experiment concluded (confirmed via `rm -rf`, verified no orphaned sandbox processes remained beforehand). The fixture source files and the experiment harness script itself remain at `/tmp/mission26_fixtures/` (9 fixture `.py` files, `run_experiment.py`, `results.json`) — entirely outside git tracking, disposable, listed here explicitly per this mission's own instruction rather than silently left unaccounted for.

## 20. Remaining Uncertainties

- `sys.stdin.readlines()` and direct iteration (`for line in sys.stdin:`) were not individually fixture-tested this mission — `readline()`/`read()` were treated as representative of the broader `sys.stdin` surface, but this is an INFERRED generalization, not independently OBSERVED for every method on the object.
- Whether Seatbelt's `/dev` allowance (`echo_sandbox.sb`, flagged as UNKNOWN in Mission 25 §13) plays any role independent of `subprocess.run()`'s own fd-inheritance default was not resolved by this mission either — the experiment's Mode 1 vs. Mode 2 comparison shows *that* the stdin source matters, not which specific layer (kernel profile vs. Python-level default) is the operative one; this remains open.
- Whether extending the mock is best done inside `run_script.py` (shared) or as a new, `echo_projects.py`-local mechanism is a real, unresolved design question — this mission surfaced the requirement, not the implementation location.
- Whether the specification should retain any form of "interactive" wording (simulated rather than real) was investigated (§11) but not settled — this remains a genuine open design choice for whoever makes the future change described in §18.
- Whether models given the current, unmodified "interactive text scenario" wording would, if asked freshly today, ever choose a simulated (non-`input()`/non-`stdin`) realization was not tested — this mission's 100% (7/7) figure is drawn from the existing historical corpus (Mission 24), not a fresh generation run, which this mission deliberately did not perform (no new `council_generate_project()` calls were made — that would have been a real, non-trivial model-call cost, and was judged unnecessary given the historical corpus already answers the question this mission needed).

## 21. Integrity / Ending State

```bash
git rev-parse HEAD
# 525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged from mission start)

git status --short | wc -l
# 66 (unchanged count; same pre-existing set as mission start, plus this
#     mission's own two new files: this report, and append-only annotations
#     to research/FINDINGS.md and research/OPEN_QUESTIONS.md — see below)
```

- HEAD unchanged: **confirmed**.
- No production files modified: **confirmed** (§19).
- No configuration changed: **confirmed**.
- No timeout changed: **confirmed** — all experiment timeouts (8s) existed only inside the disposable `/tmp` harness script, never touching `_run_f2_multi_file()`'s real 60s default.
- No service restarted: **confirmed** — `run.py`, Ollama, and the watchdog were never touched.
- No commit created: **confirmed**.
- Temporary fixtures: fixture sources and the harness script remain at `/tmp/mission26_fixtures/` (listed explicitly, §19); scratch execution directories were removed.
- Audit/research changes: this report (`audits/2026-09-09_f2_stdin_resolution_experiment.md`), plus append-only additions to `research/FINDINGS.md` and `research/OPEN_QUESTIONS.md`.
