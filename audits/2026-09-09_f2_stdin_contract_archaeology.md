# Mission 25 — F2 stdin Contract / Specification Archaeology

**Date:** 2026-09-09
**Type:** Investigation-only. No production code, configuration, timeouts, sandbox profiles, or safety controls modified. No restart of `run.py`, the watchdog, or Ollama performed. Mission 24's `stdin=subprocess.DEVNULL` recommendation was **not** applied.

---

## 1. Executive Summary

The evidence points, with **high confidence**, toward **Contract A (Autonomous F2)** — but with an important, precisely-evidenced qualification: the contract is well-established as *project practice*, not as an explicit rule written for F2 or `echo_projects.py` specifically.

Every other place in this codebase where generated code's interactivity was directly addressed in a prompt or a sandbox mechanism — four separate prompt-construction sites (three live, one dead) all dated to the repository's first commit, plus a sibling kernel-sandboxed execution path (`sandbox/run_script.py`'s `run_sandbox_script_isolated()`, introduced 10 days before `echo_projects.py`, using the *identical* `sandbox-exec` + `echo_sandbox.sb` + `safe_exec_wrapper.py --mode=script` invocation shape) — treats `input()`/interactivity in autonomously-executed code as something to be explicitly forbidden or defused, never as something to be supported. `echo_projects.py`'s own spec-construction function (`_build_autonomous_spec()`) is the one place in the entire codebase that runs the other direction: it explicitly invites "an interactive text scenario" as a creative-interpretation example, and its F2 harness (`_run_f2_multi_file()`) never adopted the anti-hang mechanism its own sibling mechanism already had, 10 days earlier, for the exact same execution shape.

No test, fixture, or Liveness Ledger check anywhere in the codebase exercises F2's stdin behavior specifically — the extensive discrimination-testing discipline this project applies everywhere else (documented at length in `CLAUDE.md`) has a genuine, confirmed gap here.

**Bottom line, stated as precisely as the evidence supports:** `echo_projects.py`'s F2 does not carry an *explicit* stdin contract of its own — no comment, docstring, or test in that file says anything about stdin either way. But the surrounding, dated, first-party evidence from the rest of this codebase is one-sided and consistent: wherever this project's authors *did* address the question directly, non-interactivity was the answer, every time, before `echo_projects.py` existed. The strongest-supported reading is that `echo_projects.py`'s F2 is an **incomplete implementation of an autonomous-F2 contract already established elsewhere**, not a deliberately-designed interactive one, and not a genuinely undefined/never-considered question at the level of the whole project — only at the level of this one file.

## 2. Mission Question

*When F2 executes a generated multi-file project, is the generated project supposed to be autonomous/non-interactive, is interactive stdin intentionally supported, or is the behavior simply unspecified/accidental?*

## 3. Evidence Matrix

| Question | Evidence | Classification | Confidence |
|---|---|---|---|
| Does `_run_f2_multi_file()` set `stdin=` explicitly? | No — read directly, `app/core/echo_projects.py:163-170` | OBSERVED | High |
| Does its docstring/comments mention stdin or interactivity at all? | No — zero mentions anywhere in the function or module docstring | OBSERVED | High |
| Does `safe_exec_wrapper.py` (the shared wrapper) mention stdin anywhere? | No — full 527-line file read; extensive comments on every other patched primitive (open, os.*, subprocess, ctypes, GUI, matplotlib), zero mention of stdin/input/tty | OBSERVED | High |
| Does `echo_sandbox.sb` (the kernel profile) mention stdin? | Yes — one comment, "`/dev — stdout, stderr, stdin, /dev/urandom, /dev/null`," bundled with unrelated mundane devices, justifying broad `(allow file-write-data (subpath "/dev"))` | DOCUMENTED | Moderate (names stdin explicitly; framing suggests generic `/dev` necessity, not deliberate interactivity design — see §9) |
| Does the kernel profile control which fd inherits stdin? | No positive evidence either way found; Seatbelt governs path-based syscalls, not fd-inheritance at process spawn, which is a `subprocess.run()`-level Python decision | INFERRED | Moderate — plausible but not independently verified in this mission |
| Does a sibling mechanism using the identical kernel-sandbox invocation shape (`sandbox-exec`+`echo_sandbox.sb`+`safe_exec_wrapper.py --mode=script`) already handle interactive-hang risk? | Yes — `sandbox/run_script.py`'s `_insert_input_mock()`, applied inside `run_sandbox_script_isolated()` from the moment that function was introduced | HISTORICAL / DOCUMENTED | High |
| Did that sibling mechanism predate `echo_projects.py`? | Yes — `run_sandbox_script_isolated()` introduced 2026-07-13 (`805218c2`); `echo_projects.py` introduced 2026-07-23 (`93e3456c`) — 10 days later | HISTORICAL | High |
| Is that sibling's input-mock comment itself explicit about the failure mode? | Yes — "`CHANGE 2: Insert input() mock so interactive scripts fail immediately instead of hanging for the full timeout duration`" | DOCUMENTED | High |
| Does the *original*, older (pre-kernel-sandbox) version of that same file also mock `input()`? | Yes — present at the repo's first visible commit (2026-06-28), applied to `run_sandbox_script()`'s plain-subprocess path | HISTORICAL | High |
| Does the single-file self-edit pipeline's own generation prompts forbid `input()`/interactivity? | Yes, at three live sites: `self_edit_manager.py:1577` (`plan_code_logic`'s plan prompt), `self_edit_manager.py:2844` (`_build_targeted_prompt`'s base), `wolf_friction_bridge.py:74` (dry-run friction-bridge prompt) — all three dated to the repo's first commit | DOCUMENTED / HISTORICAL | High |
| Does a fourth, dead code-generation helper say the same thing? | Yes — `app/ollama_handler.py`'s `generate_code()` ("No input() calls. No interactive elements... must run headlessly"), dated to the first commit, but confirmed to have zero live callers (only a comment references it by name) | DOCUMENTED (orphaned) | High for the statement's existence; N/A for live enforcement |
| Does `echo_projects.py`'s own spec text invite interactivity? | Yes — `_build_autonomous_spec()`'s spec string lists "an interactive text scenario" as an explicit creative-interpretation example, unchanged since introduction (`git log -S` on the exact phrase returns only the introducing commit) | OBSERVED / HISTORICAL | High |
| Does `council_generate_project()`'s own plan/file prompts (the manual-`!project` path) contain any interactivity guidance either way? | No — read in full; neither prompt mentions `input()`, interactivity, or headlessness | OBSERVED | High |
| Is there any dedicated test/fixture for F2's stdin behavior specifically? | No — searched all test/verify scripts referencing `echo_projects`/`_run_f2_multi_file`; the only real hits (`scripts/verify_liveness_ledger.py`) test isolation/escalation/path-safety/council-advisory/autonomy-gating invariants, none touch stdin/interactivity | OBSERVED | High |
| Has any historical F2-reaching project's success ever depended on stdin? | No — 0/61 real F2-reaching attempts have ever passed (re-confirmed this mission and in Mission 24); by definition, none succeeded via any mechanism, stdin included | OBSERVED | High |
| Do the 4 real F2_TIMEOUT cases and 3 non-timeout `input()`-containing cases show what "interactive text scenario" gets realized as in practice? | Yes — 100% of the 7 real cases containing `input()` chose literal, direct `input()` calls, not a simulated/scripted interaction | OBSERVED (Mission 24, re-confirmed) | High |
| Is the 60s timeout framed anywhere as specifically targeting interactive hangs? | No — bare default value, zero explanatory comment in `echo_projects.py`; contrasts with `run_script.py`'s explicit "CHANGE 1 (general timeout tightened)" *and* separately-needed "CHANGE 2 (input mock)," implying this project's own prior practice treats general-timeout and interactive-hang protection as two distinct, both-necessary layers | DOCUMENTED (for the sibling) / INFERRED (for `echo_projects.py`'s own timeout intent) | Moderate |
| Does F2 distinguish "needs input" from "hangs forever" in its result? | No — a single `except subprocess.TimeoutExpired: return {"error": "sandbox test timed out"}` covers both | OBSERVED | High |
| Does F3 (or an equivalent later gate) impose any different interactivity expectation? | N/A — `echo_projects.py` has no F3-equivalent stage at all; nothing is ever promoted or re-scanned post-write, confirmed directly from `generate_project()`'s own code and docstring | OBSERVED | High |

## 4. F2 Implementation Contract

`_run_f2_multi_file()` (`app/core/echo_projects.py:152-179`) is a real, unmodified reuse of the kernel-level `sandbox-exec` + `echo_sandbox.sb` + `safe_exec_wrapper.py` mechanism, invoked with `--mode=script` so `main.py`'s own `if __name__ == "__main__":` guard actually fires (real execution, not merely import). Its own docstring frames this as reusing "the exact real sandbox-exec invocation shape `self_edit_manager.py`'s `test_code_in_sandbox()` already uses" — accurate for the *invocation shape* (profile, wrapper, subprocess pattern), but **not accurate for execution mode**: `test_code_in_sandbox()` uses the default `--mode=import`, which never executes a script's top-level `__main__` guard at all (imports never set `__name__ == "__main__"`), so it structurally cannot hit an `input()` call behind a standard guard. `_run_f2_multi_file()`'s `--mode=script` deliberately can and does. This is a real, meaningful divergence from the mechanism its own docstring cites as precedent, not a cosmetic one.

No `stdin=` is set. Per Python's own `subprocess.run()` semantics, this means the child inherits file descriptor 0 from the parent (`run.py`) unmodified — confirmed directly against the live process in Mission 24 to be a real terminal (`/dev/ttys002`), not `/dev/null`. Nothing in `echo_projects.py`, `safe_exec_wrapper.py`, or `echo_sandbox.sb` overrides, blocks, mocks, or discusses this inheritance in either direction.

## 5. Generator Specification Contract

`_build_autonomous_spec()` (`app/core/echo_projects.py:600-629`) constructs the spec text used by the autonomous loop:

> *"Design and build a small, self-contained Python program that explores, models, or illustrates the following idea in some concrete way (a simulation, a toy model, an interactive text scenario, a data visualization, etc.) — creative interpretation is expected: {question}"*

"An interactive text scenario" is one of four parenthetical examples in a list explicitly framed as non-exhaustive ("etc."), not a directive, requirement, or emphasized option — it carries equal textual weight to "a simulation," "a toy model," and "a data visualization." This is the **only** authoritative specification text in the entire codebase using this phrase; `git log -S` on the exact string returns only the file's introducing commit, confirming it is original, unmodified wording, not a later addition or a duplicate found elsewhere.

`council_generate_project()`'s own `plan_prompt` and `file_prompt` (the actual prompts sent to models, both for the manual `!project` path and downstream of the autonomous spec) carry **no** interactivity guidance of any kind — neither inviting nor forbidding it. The "interactive text scenario" invitation lives entirely in the upstream spec-construction step, not in the generation prompts themselves; a generating model sees it only as part of whatever `spec` text got threaded through.

## 6. Test Contract

There is no dedicated test, fixture, or discrimination case anywhere in this codebase covering F2's stdin behavior. The Liveness Ledger's six `echo_projects_*` checks (`echo_projects_isolation`, `echo_projects_no_escalation`, `echo_projects_path_safety`, `echo_projects_council_advisory`, `echo_projects_autonomy_gated`, `echo_projects_autonomy_activity`) are thorough about the properties this project has historically cared most about — never loading into production, never escalating self-edit privilege, filename safety, review never gating a write, autonomy respecting the shared coordinator gate — but none of them assert anything about whether a generated project can or should call `input()`, what happens if it does, or what F2's timeout is actually for. Given this project's own extensive, repeatedly-demonstrated discipline of adding a Liveness Ledger check alongside any new safety-relevant capability (stated as a standing rule in `CLAUDE.md`'s Liveness Ledger section), the absence of one here is itself meaningful: it indicates the stdin question was never identified as a property worth verifying, one way or the other, at the time these six checks were written.

## 7. Git History

Chronology, established directly via `git log`/`git log -S` (not inferred):

| Date | Commit | Event |
|---|---|---|
| 2026-06-28 | `44e7a8e` (repo's clean initial commit) | `sandbox/run_script.py`'s `_insert_input_mock()` and its `run_sandbox_script()` caller already present. Same commit: `self_edit_manager.py`'s two no-`input()` prompt constraints, `wolf_friction_bridge.py`'s no-`input()` prompt constraint, and `ollama_handler.py`'s `generate_code()` ("must run headlessly") all already present. |
| 2026-07-13 | `805218c2` ("fix: sandbox pipeline and standalone entry-point correctness, Finding 22 Batch 7/8") | `--mode=script` added to `safe_exec_wrapper.py`; `run_sandbox_script_isolated()` (the kernel-sandboxed sibling to `echo_projects.py`'s F2) introduced in the same commit, with `_insert_input_mock()` already wired into it from this exact commit — not added later. |
| 2026-07-23 | `93e3456c` ("Add echo_projects: sandboxed multi-file generation with full library access") | `echo_projects.py`, `_run_f2_multi_file()`, and the "interactive text scenario" spec wording all introduced together, in this one commit, with no `stdin=` handling and no input-mock. |

**Interpretation, held to the evidence available and no further:** the anti-interactive-hang design pattern (mock `input()`, fail fast) was already a working, dated, 10-day-old feature of a sibling mechanism sharing the *identical* underlying kernel-sandbox invocation — sandbox-exec, `echo_sandbox.sb`, `safe_exec_wrapper.py`, `--mode=script` — at the exact moment `echo_projects.py` was written. Whether `echo_projects.py`'s author was aware of `run_script.py`'s specific mechanism cannot be established from source alone — no comment in `echo_projects.py` references `run_script.py`, and the imports (`_SANDBOX_PROFILE`, `_SANDBOX_WRAPPER`) are drawn from `self_edit_manager.py`, not `run_script.py`, which is a plausible reason the pattern wasn't ported over even if it was known. This is a genuine, disclosed limit of this archaeology: **the evidence supports "the precedent existed and wasn't followed," not "the precedent was seen and consciously rejected."** Both are consistent with the same observable facts; this investigation cannot distinguish them further.

## 8. Historical Success/Failure Evidence

0/61 real F2-reaching attempts have ever passed F2 (re-confirmed this mission, consistent with Mission 24 and `CLAUDE.md` Finding 91). No historical candidate has ever legitimately required or benefited from stdin to succeed, because no candidate has ever succeeded via any path. Among the 14 real F2-reaching attempts, 7 contain a reachable `input()` call; of those, 4 timed out (100% correlation with a reachable call) and 3 failed earlier on unrelated bugs (confirmed via direct, untruncated re-execution in Mission 24) — meaning even the *attempted* interactive cases never reached a point where stdin behavior would have mattered to a successful outcome. This mission finds no case, anywhere in the historical record, where a human operator supplied real input to a generated project running under F2.

## 9. Sandbox / Wrapper Behavior

Tracing the descriptor as far as repository evidence permits:

1. **Python's `subprocess.run()` default (no `stdin=` argument):** inherits fd 0 from the calling process. This is standard-library behavior, not a choice made anywhere in this codebase — its presence here is the *absence* of an override, not an affirmative act.
2. **`safe_exec_wrapper.py`:** patches `open`, `os.*`, `subprocess.*`, `shutil.*`, `ctypes`/`cffi`, GUI toolkits, and matplotlib's config directory — an extensively-documented, deliberate patch list. Stdin is not among the patched primitives; there is no comment anywhere in this 527-line file acknowledging its existence, whether to permit or restrict it. This reads as an omission, not a decision — every other primitive this file touches has multiple lines of rationale attached; stdin has none.
3. **`echo_sandbox.sb` (the kernel Seatbelt profile):** the one place stdin is named explicitly, in a single comment bundling it with `/dev/urandom` and `/dev/null` under a generic "`/dev` — stdout, stderr, stdin, /dev/urandom, /dev/null`" justification for `(allow file-write-data (subpath "/dev"))`. This reads as a broad, generic accommodation for ordinary Python runtime needs (writing to stdout/stderr, reading urandom) rather than a deliberate design choice about *interactive* stdin specifically — nothing in the surrounding comments discusses TTYs, keystrokes, or `input()`. Whether this kernel-level allowance is even the operative mechanism for the observed hang, versus fd-inheritance happening independently at process-spawn time (before any Seatbelt rule is evaluated), was not independently verified in this mission — flagged as **UNKNOWN**, not assumed.

**Direct answer to the framed question ("does the sandbox itself intentionally provide interactive stdin, or is it simply receiving fd 0 from the parent process?")**: the evidence supports the latter more than the former. The one place stdin is named (`echo_sandbox.sb`'s comment) frames it as part of ordinary `/dev` access, not as a deliberate interactivity feature; the fd-inheritance itself is a `subprocess.run()` default that nothing in this codebase's F2 call chain overrides in either direction.

## 10. Adversarial Findings

Working through the mission's 12 adversarial questions directly against the evidence gathered:

1. **Could the timeout be an intentional way of rejecting interactive projects?** No supporting evidence found — the 60s value in `_run_f2_multi_file()` has zero explanatory comment, unlike its sibling's own dated, two-part history ("CHANGE 1: reduced from 600→30s" for general nontermination, "CHANGE 2: input mock" as a *separate, later, additional* fix) — which itself is evidence *against* treating a bare timeout as sufficient interactive-hang handling in this project's own prior practice.
2. **Does documentation require generated projects to terminate without user input?** Not within `echo_projects.py` itself. Yes, repeatedly, elsewhere in the codebase (§3, §5).
3. **Could "interactive text scenario" mean simulated interaction, not real `input()`?** The text alone is ambiguous. But empirically, 100% (7/7) of real historical cases that took this interpretation chose literal `input()` calls — whatever the phrase might theoretically have meant, its realized behavior in every observed instance was direct stdin consumption.
4. **Does F2's wrapper intentionally permit stdin for some other reason?** No — see §9; the wrapper never discusses it.
5. **Could `input()` historically have been considered acceptable if the parent had stdin?** No affirmative evidence found anywhere.
6. **Was a human operator ever expected to interact with F2 candidates?** No evidence found, in either the manual (`!project`) or autonomous invocation path.
7. **Would `DEVNULL` merely expose an existing incompatibility, or change intended semantics?** Given the sibling precedent (§4, §7) already treats fast-failing on `input()` as the intended behavior for this exact execution shape, `DEVNULL`-style handling would align `echo_projects.py`'s F2 with an already-established, dated pattern rather than introduce a new constraint — this is the strongest reading the evidence supports, though it remains an inference, not a certainty, and is noted here only as an evidence-based observation, not a recommendation (see mission constraints).
8. **Could the correct fix instead belong in the generation specification?** Genuinely two-sided, and not resolved by this investigation. `echo_projects.py`'s own module docstring frames "full library access" and "creative interpretation is expected" as deliberate design goals distinguishing it from self-edit's narrower pipeline — so the interactive-scenario invitation could be read as an intentional expansion of creative latitude specific to this one pipeline, not an oversight, whose downstream consequence for F2 simply was never worked through. Both readings are consistent with the same facts.
9. **Could the correct design be a deterministic synthetic stdin stream?** Not addressed anywhere in the codebase; no evidence either way.
10. **Is the 60s timeout primarily a general nontermination safety boundary, with interactive blocking just one instance of that broader class?** This is the best-supported reading of `_run_f2_multi_file()`'s own timeout, taken alone. But the sibling mechanism's two-part history (§7, §10.1) shows this project's own prior practice does *not* treat a general timeout as sufficient for the interactive case specifically — it added a second, dedicated mechanism on top, which `echo_projects.py` never inherited.
11. **Does F2 distinguish "needs input" from "hangs forever" anywhere?** No — confirmed directly (§3, §6).
12. **Does F3 or a later stage impose a different interactivity expectation?** N/A — `echo_projects.py` has no F3-equivalent stage.

**What survives of Mission 24's "structural spec/testability mismatch" framing:** it survives, and this mission sharpens rather than weakens it. Mission 24 characterized the gap as F2 lacking "a controlled stdin contract" against a spec that "explicitly invites" interactivity. This mission adds the more precise finding that the *rest of this project* already has a controlled, working answer to this exact question — both at the specification level (three live, dated prompts forbidding `input()`) and at the harness level (a dated, kernel-sandboxed sibling mechanism that mocks `input()` for exactly this execution shape) — and `echo_projects.py` is the one place that diverges from both, on both sides, simultaneously.

## 11. Contract Determination

**Autonomous F2** — best-supported by the available evidence, with the qualification stated in §1 and repeated here for precision: this is a determination about **established project practice**, not about an **explicit rule targeting F2 or `echo_projects.py`**, neither of which exists.

Why the alternatives are weaker:

- **Interactive F2** has essentially no supporting evidence. Nothing in `safe_exec_wrapper.py`, `echo_sandbox.sb`'s comments (beyond the generic `/dev`-access justification), or `echo_projects.py` itself frames stdin inheritance as a deliberate feature. No test expects an interactive candidate to pass. No historical success ever depended on it. The one piece of evidence that could be read this way — `echo_sandbox.sb`'s explicit naming of "stdin" — is better explained as incidental, generic `/dev` access than as purposeful interactivity support (§9).
- **Undefined/accidental** is the closest competitor, and is correct at the narrow level of "did anyone writing `echo_projects.py` specifically think about stdin" — the evidence strongly suggests no. But it is too weak a conclusion for the *project as a whole*: this is not a question the codebase never addressed. It addressed it, repeatedly, consistently, and always the same way, in every other place it came up, both before and roughly contemporaneously with `echo_projects.py`'s creation. Calling the overall contract "undefined" would understate real, dated, first-party evidence of an established norm that this one file simply didn't inherit.

## 12. Implications

No code change is recommended here — that determination belongs to a future, separate decision, per this mission's own constraints, and Mission 24 already surfaced the mechanical option (`stdin=subprocess.DEVNULL`) without applying it.

What this mission adds for that future decision: the choice is not between "invent a new stdin policy for F2" and "leave it alone" — it is between **catching `echo_projects.py`'s F2 up to a pattern this project already built, tested by nothing but proven in practice by 10 days' head start, for the identical execution mechanism** versus **deliberately deciding, for the first time, that this one pipeline should diverge from that pattern** (which would itself be a new decision, not a restoration of status quo, and would still leave the generation-specification side — "interactive text scenario" — inconsistent with every sibling prompt in the codebase unless that were also revisited). Evidence does not establish which of these two paths was ever actually chosen; it establishes that the codebase's default, everywhere else, is the first one.

## 13. Open Questions

- Was `run_script.py`'s input-mock pattern known to whoever wrote `echo_projects.py`, or independently not-considered? Source evidence cannot distinguish these (§7).
- Does Seatbelt's kernel-level `/dev` allowance in `echo_sandbox.sb` actually govern the observed hang, or is fd-inheritance at process-spawn entirely independent of it (i.e., would the hang still occur even under a maximally restrictive `/dev` policy)? Not verified in this mission — would require a further, bounded reproduction (denying `/dev` access in a scratch copy of the profile) that this mission did not attempt, since it risks touching sandbox-profile behavior close to the "do not modify" boundary even in a throwaway copy, and was judged not essential to answering the primary contract question.
- Is "an interactive text scenario"'s inclusion in `_build_autonomous_spec()` a deliberate, considered design choice (expanding creative latitude, per the module's own stated goals) or an oversight carried over from generic brainstorming language? No commit message, comment, or design note addresses this directly; §10.8 leaves it genuinely open.
- If this gap is ever closed, should the fix live in the harness (F2), the specification (drop or qualify "interactive text scenario"), or both? This mission deliberately does not answer this — see §12.

## 14. Repository Integrity

```
Mission start — HEAD: 525454a1dccfc91adf1aa8b01ff9b6ce8405d423
Mission end   — HEAD: 525454a1dccfc91adf1aa8b01ff9b6ce8405d423   (unchanged)
```

Working tree: the pre-existing set of modified/untracked files present at mission start (live-system drift in `claude_relay/`, `logs/janitor_report.json`, `sandbox/scripts/temp_self_edit.py`, `app/core/echo_ground_truth.py`, `PENDING_DECISIONS.md`, plus the large pre-existing set of untracked `audits/`/`.claude/` files from prior sessions) is unchanged in kind. This mission added exactly one new file, `audits/2026-09-09_f2_stdin_contract_archaeology.md`, plus append-only annotations to `research/FINDINGS.md` and `research/OPEN_QUESTIONS.md` (see below) — no other file was modified, no restart was performed, no reproduction script wrote outside `/tmp`-equivalent scratch or already-quarantined `sandbox/echo_projects/*` content that this mission only read, never modified.
