# Restart-Persistence Transfer — Frozen Protocol

**Frozen before any new held-out generation or execution. Do not alter after
observing outcomes; record deviations instead of silently repairing.**

## 0. Scope, in one sentence

Does the already-frozen procedure artifact `procedure_frozen.json` (from
`validated_experience_competence_transfer`, hereafter VECT), read from
persistent disk state by a genuinely fresh, independent OS process with no
shared memory from any process that created or previously used it, still
provide a measurable, causally-attributable advantage over an equivalent
fresh process denied access to it — on genuinely new held-out instances of
the same task family?

This is a persistence test only. It is explicitly NOT: a re-run of VECT's
own acquisition experiment; a test of Echo autonomously extracting the
procedure; a cross-family generalization test; a claim about accumulated or
open-ended learning.

## 1. Hypothesis and null hypothesis

**H1**: A fresh successor process that recovers and applies P (R+) will
score at least as high, and on average higher, than an equivalent fresh
successor process denied P (R-), on a newly-drawn, disjoint-seeded held-out
panel of the same `extract_code` Level-3 task family, using genuinely new
code content never present in VECT's TRAIN or original held-out sets.

**H0**: No such advantage exists, or is not attributable to P — e.g.
because the model already solves the new panel without help (ceiling),
because P provides no benefit on genuinely new code content (i.e. VECT's
effect was narrower than the new-instance framing implied), or because
discovery/recovery/application failed for a structural reason unrelated to
P's real content.

## 2. Prerequisite-inspection summary (full detail in the companion audit
report; restated here only as the facts this protocol is built to
accommodate)

- VECT's frozen artifacts (`procedure_frozen.json`, hash
  `21fde9b5dbe026489ef8f3ff47f974c816ca706944cde251b2501ed7f541f3c8`; the
  original held-out commitment, hash
  `a35c0807cc505ed4d192b44f17b2705427ccf8e3a46af374557e60d9a8c90055`)
  independently re-hashed and confirmed to match on disk, this session,
  2026-09-27.
- VECT's headline numeric result (P=10/10, G=6/10, Z=5/10 on the original
  10-instance held-out panel) independently reproduced by an adversarial
  self-review (`audits/2026-09-24_codex_validated_experience_transfer_self_falsification.md`)
  and by this session's own direct recount.
- **Confirmed independently by this session, not merely cited**: all 4
  distinct code bodies in VECT's original held-out set are byte-identical
  to all 4 distinct code bodies in VECT's TRAIN set — zero new code content
  was ever tested. Root cause, independently traced: VECT's task generator
  (`historical_difficulty_calibration/tasks.py`) draws Level-3 code from a
  fixed 4-entry bank (`CODE_SNIPPETS_COMPLEX`); with only 4 possible values
  and 8 TRAIN draws, every value necessarily recurs in any later sample
  from the same bank. VECT's "unseen instances" claim held only at the
  level of prose recombination, never code content.
- **Confirmed independently by this session, not merely cited**:
  `freeze_procedure.py`'s `PROCEDURE_TEXT` is a literal, investigator-
  authored string; the script's only substantive check is that each cited
  `train_L3_NN` episode ID exists in `experience_log.jsonl` — it does not
  algorithmically derive clauses from outcomes. P is best described as an
  externally-distilled lesson informed by real Echo-generated TRAIN
  evidence, not an artifact Echo itself autonomously extracted.

**Consequence for this protocol**: the new held-out panel below is built
from genuinely new code content (never present in VECT's TRAIN, VECT's
original held-out set, or anywhere else in this bank), specifically to
close the gap the prerequisite inspection found. The final report's claims
will describe P as "a previously frozen, externally-distilled,
experience-informed procedure," never as "Echo's autonomously acquired
competence," matching the prerequisite's own honest provenance finding.

## 3. Restart definition

- **Originating process**: the process(es) that computed and froze P
  (`python -B run.py <phase>` invocations under VECT, 2026-09-24). Already
  fully terminated for 3 real days as of this protocol's freeze — no
  action is needed to end it; its termination is a pre-existing fact,
  independently verifiable (VECT's own files carry mtimes from 2026-09-24;
  today is 2026-09-27; `ps aux` shows no process from that date still
  running).
- **Genuine restart boundary for this experiment**: R+ and R- are each
  executed as their own freshly-launched `python3` OS subprocess, invoked
  from a separate Bash tool call each (this harness's own tool boundary
  does not preserve environment variables, functions, or process state
  across calls — only the working directory persists — so each `python3
  ...` invocation is a genuinely fresh interpreter with no inherited
  globals, no inherited import cache, and no shared memory with (a) the
  long-dead originating process, (b) each other, or (c) the investigating
  session itself).
- **No simulated restart**: neither condition may be implemented as a
  function call inside one long-lived Python process, and no condition
  may be labeled "fresh" while retaining any Python-level state from a
  prior condition's run.
- **No preloading**: R+ discovers P by reading `procedure_frozen.json`
  from disk at runtime, inside its own subprocess. It is never placed in
  this investigating session's own prompt to itself, nor pre-injected as
  an argument construction shortcut.

## 4. R+ and R- conditions

Both conditions target the same 10 new held-out task instances (Section 5),
same model (`qwen2.5-coder:7b`), same sampling (`temperature=0`), same new
disjoint seed range for task generation, same deterministic execute-and-
exact-match grader, same one-shot (no retry) held-out discipline VECT
itself used.

**R+ (`--condition=r_plus`)**:
1. Read `procedure_hash.txt`.
2. Independently recompute SHA-256 of `procedure_frozen.json` (canonical
   JSON, sorted keys, matching VECT's own hashing convention). If the
   recomputed hash does not exactly match the value read in step 1, **STOP
   — abort immediately, write nothing further, report the mismatch.**
   Never proceed on a hash mismatch.
3. Load `PROCEDURE_TEXT` from the hash-verified `procedure_frozen.json`.
4. For each of the 10 new held-out instances, build a prompt using VECT's
   own P-arm prompt shape (procedure text prepended as context, same
   task-instruction wording pattern as VECT's `prompt.py`), then issue one
   fresh, single-turn Ollama request (no conversation history, no shared
   client object across instances beyond the underlying HTTP connection).
5. Extract, execute, and grade the candidate exactly as VECT's evaluator
   does.

**R- (`--condition=r_minus`)**:
1. Never opens or reads `procedure_frozen.json` at any point — the file is
   not referenced anywhere in this condition's source, not merely ignored
   at runtime. (Verifiable directly by reading the script.)
2. For each of the same 10 new held-out instances, build a prompt using
   VECT's own Z-arm shape (`context=""`, byte-identical unmodified base
   task prompt — no procedure, no generic-tip counterfeit).
3. Same fresh single-turn call, same extraction/execution/grading.

Order: R+ runs first, R- second (both as of this freeze; the order is
fixed here and not altered afterward). Both write to condition-named
result files only after the full panel completes for that condition.

## 5. New held-out task instances

- Task family: identical to VECT's — `extract_code`, Level 3 (per
  `historical_difficulty_calibration/tasks.py`'s own difficulty-level
  structure: leading prose with 1-2 plain + interleaved distractor lines,
  a "complex" code opening, variable blank-line separator of 1-3 lines, no
  trailing prose).
- **Code content**: 4 genuinely new snippets, never present in VECT's
  `CODE_SNIPPETS_SIMPLE`, `CODE_SNIPPETS_COMPLEX`, `train_tasks.json`, or
  `heldout_tasks.json` — verified by direct text search against all of
  those before generation is trusted. Structurally analogous to VECT's own
  4 "complex" openings (one decorator-opening, one docstring-opening, one
  import+decorator-opening, one from-import+decorator-opening) to preserve
  the same difficulty structure the procedure's clauses were written
  against, without reusing any of VECT's literal code.
- **Mechanism**: a new, standalone script in this experiment's own
  directory imports `historical_difficulty_calibration.tasks` for its
  prose banks and `_build_instance` machinery only, and monkeypatches
  `tasks.CODE_SNIPPETS_COMPLEX` to the new 4-snippet list *within this
  script's own fresh subprocess only* — the shared `tasks.py` file on disk
  is never edited (editing it would silently change what any future
  re-run of VECT's own already-qualified, already-frozen experiment would
  produce for the same seeds, since `random.choice` depends on sequence
  length; that would be a real, if indirect, modification to a qualified
  source artifact, and is deliberately avoided).
- **Seeds**: 2000-2009 (ten values). Confirmed disjoint from every prior
  seed range used anywhere in this whole research arc (700-704, 800-804,
  810-814, 820-824, 830-834, 840-844, 850-854, 1000-1007, 1100-1109).
- **Commitment**: the new held-out set is generated once, hash-committed
  (SHA-256 over canonical JSON) into `restart_heldout_commitment.sha256`,
  and only then is any model call made against it — mirroring VECT's own
  seal-before-use discipline.

## 6. Scoring / evaluator

Reuse the same deterministic approach VECT's held-out run used: generated
candidate code is extracted from the model's raw response, executed in a
subprocess against the real task input, and its output is compared for
exact string equality against the task's own `expected_code`-derived
correct output. No partial credit, no textual-resemblance scoring. A
runtime error, a timeout, or a non-exact-match output all count as a
failure for that instance.

## 7. Treatment isolation and contamination controls

Checked against the full list the governing mission specified:

| Channel | Control |
|---|---|
| P appearing in R- prompts | R- source never opens `procedure_frozen.json`; verifiable by reading the file |
| Expected answers leaking through the grader | Grader receives candidate code + real input + expected output only; it has no notion of "arm" or "condition" and cannot influence generation |
| Evaluation code encoding the desired solution | The task's `expected_code` is used only for post-hoc grading, never placed in any generation prompt for either condition (task *input text* is placed in the prompt for both conditions, as VECT's own design requires — this is disclosed as an inherited, accepted design property below, not a new gap) |
| Filenames/metadata revealing treatment | Result filenames are condition-named by necessity (`r_plus_results.jsonl` / `r_minus_results.jsonl`) but this label is never visible to the model — it exists only in this investigating session's own bookkeeping |
| Shared temp files | Each subprocess uses its own private scratch directory, never a shared fixed path |
| Environment variables | No P-derived content is ever placed in an environment variable; each subprocess's env is whatever the Bash tool call naturally provides, with nothing manually injected |
| Caches | No response cache of any kind; every held-out call is a fresh, uncached HTTP request to a live Ollama server at temperature=0 |
| Python/module globals | R+ and R- are separate OS processes (separate Python interpreters); module globals cannot cross a process boundary |
| Shell history / command construction | P's text is never passed as a CLI argument or interpolated into a shell command string; R+'s script reads it from disk internally in Python only |
| Model conversation/session reuse | Every held-out call is a single-turn request with no prior conversation history, matching VECT's own per-call design |
| Accidental shared process state | R+ and R- are launched via two separate Bash tool calls; the Bash tool does not persist process state (only cwd) across calls |
| Test cases appearing in acquisition artifacts | The 4 new code snippets are grepped against `experience_log.jsonl`, `train_tasks.json`, and `heldout_tasks.json` before any model call; the check and its result are recorded in the execution report |
| Evaluator access to treatment labels | The grading function's signature takes only candidate code, real input, and expected output — no condition/arm parameter exists in its call |

**Disclosed residual channels, not claimed away**:
- The task *input string* is placed in-prompt for both R+ and R-, exactly
  as VECT's own design did, because this task family's own definition
  (write a function that extracts code from *this* prose-wrapped string)
  requires it. This is an inherited design property, not a new gap, and it
  applies symmetrically to both conditions.
- Both conditions call the same live, persistent Ollama server process,
  which is not itself restarted between R+ and R-. At `temperature=0` with
  no conversation reuse, no cross-condition state is expected to leak
  through it, but this is a shared piece of infrastructure, not a fully
  isolated one, and is disclosed rather than hidden.
- This machine has other, unrelated processes running throughout (the live
  FeralEcho production server, this investigating session itself). Nothing
  else on this machine has any code path that reads this experiment's
  directory, but that absence is asserted from a repo-wide search, not
  proven by sandboxing.

## 8. Provenance distinctions to preserve in the final report

Per the governing mission, every claim in the final report will be
attributed to exactly one of: (1) model-native capability; (2) Echo
architectural/scaffolding capability; (3) current-process contextual
adaptation; (4) prior-lifetime acquired information (P); (5) unknown-origin
capability. An R+ advantage will only be attributed to (4) if R- (isolating
model-native capability alone on the identical new panel) is measurably
lower — never asserted from R+'s score in isolation.

## 9. Success / failure / ambiguous criteria (frozen before observing
outcomes)

- **SUCCESS (supports H1)**: R+'s correct count on the 10 new instances is
  strictly greater than R-'s, with at least one genuine discordant pair
  (an instance R+ gets right and R- gets wrong) — not merely a tie broken
  by an artifact of scoring.
- **MAJOR RESULT, treated as important rather than a failed run (per the
  governing mission's explicit instruction)**: R+ does not outperform R-.
  If this occurs, the final report will investigate, without repairing and
  re-running first: (A) whether P was actually recovered (hash check
  passed, text loaded); (B) whether P was applied (present in the R+
  prompt actually sent); (C) whether the generated code differs
  meaningfully between R+ and R-; (D) whether R- alone already reaches
  ceiling on this new panel (model-native capability sufficient without
  help); (E) whether the new code snippets are structurally too easy or
  too hard relative to VECT's original 4; (F) whether any apparatus step
  failed silently.
- **AMBIGUOUS**: a hash mismatch at any point (per Section 4 step 2, this
  also aborts immediately, so this should not co-occur with a completed
  run); or a small-sample result where the discordant-pair count is too
  low for any paired test to be informative (e.g. 0 or 1 discordant
  pairs) — in that case the report will say so plainly rather than force a
  binary verdict, exactly as the governing mission requires.

## 10. Statistical / descriptive comparison plan

Exact paired McNemar test on discordant pairs (same 10 task IDs receive
both conditions), one-sided and two-sided p-values reported per VECT's own
convention; marginal accuracy with Wilson 95% confidence intervals for each
condition individually. No alternative test will be substituted after
seeing results.

## 11. Process-death evidence to capture

For each of R+ and R-: `os.getpid()`, wall-clock start timestamp, wall-
clock end timestamp, exit code, and a same-process readout of
`id(sys.modules)` or equivalent, sufficient to show each ran as its own
distinct interpreter instance. For the originating (VECT) process: cited
from already-existing, independently-verified file mtimes and the current
date (2026-09-27 vs. 2026-09-24), plus the absence of any process from
that date in a live `ps aux` scan — the strongest non-invasive evidence
reasonably available for a process that predates this protocol by three
real days, not overclaimed as a captured PID/kill-signal trace (none
exists for a process that ended before this investigation began).

## 12. Artifact locations

- This protocol: `app/experiments/restart_persistence_transfer/PROTOCOL.md`
  (this file), hashed into `PROTOCOL.sha256` immediately after freeze.
- New held-out generator: `app/experiments/restart_persistence_transfer/new_heldout_tasks.py`
- R+ / R- harness: `app/experiments/restart_persistence_transfer/run_condition.py`
- New held-out set + commitment:
  `memory/experiments/restart_persistence_transfer/restart_heldout_tasks.json`,
  `restart_heldout_commitment.sha256`
- Results: `memory/experiments/restart_persistence_transfer/r_plus_results.jsonl`,
  `r_minus_results.jsonl`
- Final report: `audits/2026-09-27_restart_persistence_of_acquired_competence.md`

## 13. Expected process lifecycle

1. Generate + hash-commit new held-out set (no model calls).
2. Grep-verify zero overlap with VECT's own code content (recorded, not
   just asserted).
3. Launch R+ as a fresh subprocess; capture PID/timestamps; it independently
   hash-verifies P, then runs 10 held-out calls; writes results.
4. Launch R- as a separate fresh subprocess; capture PID/timestamps; it
   runs the same 10 held-out calls with P withheld; writes results.
5. Score, analyze, write the final frozen report.
6. Stop. Do not proceed into any further experiment.

## 14. Abort conditions

- Hash mismatch on `procedure_frozen.json` at any point.
- Ollama unreachable or a non-recoverable client error on more than 2 of
  10 instances in either condition (report the partial run rather than
  silently retrying with different parameters).
- Any accidental modification detected in VECT's own qualified source
  files (checked via a final byte-hash comparison against the same 32-file
  manifest the self-falsification audit already captured, restricted to
  the VECT-specific subset).

---

**Freeze timestamp**: 2026-09-27T09:45:16Z. No outcome has been observed at
the time of this freeze. This file is not to be edited after this point;
deviations are recorded in the final report instead.
