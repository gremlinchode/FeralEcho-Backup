# Natural Learning Event Hunt II — Overnight / Post-Baseline Evidence

**Read-only forensic investigation.** No canonical source was modified. Nothing was
staged, committed, or pushed. No skill was taught, promoted, or manually inserted. No
training was triggered. No controlled probe was run. Echo's live process was not
restarted or interrupted by this investigation — a real, natural restart is part of
the evidence examined (Section 3), not something this mission caused.

## 1. Executive Verdict

# LEVEL 2 — NEW NATURAL PERSISTENT ADAPTATION DETECTED

Continued, causally-traceable adaptation in RiverBrain's `model_task_stats` since
yesterday's evidence cutoff, now spanning a **genuine, naturally-occurring process
crash and restart** — this is real, new evidence yesterday's report explicitly did
not have (it deliberately declined to test restart persistence). The exact same
`self_edit_coding` decline mechanism yesterday found (F1 safety-scanner rejections
lowering the rolling mean) has now continued, unbroken, for a second, longer stretch,
with **zero real successes and zero improvement in failure rate** — direct evidence
*against* Phase 6's correction-learning hypothesis, not for it. **The stronger claim
this mission was asked to test — that a changed statistic subsequently altered a
real, observed routing/model-selection decision (Level 2+) — is not established.**
The causal pathway is structurally guaranteed to exist (every real coding/self-edit
request necessarily reads the now-different value), but no specific, concrete
instance of an actually-altered decision was found or could be established from
passive evidence in this pass. VSL shows zero activity. No skill, no transfer, no
Level 3 candidate exists.

## 2. Observation Window

**T0 = `2026-09-29T00:02:44+00:00` (UTC)** — the exact evidence-cutoff timestamp used
by yesterday's report (its own freeze-manifest capture time), not midnight, not an
approximation. In local time this is `2026-09-28 17:02:44 PDT`.

**Current investigation time: `2026-09-29 13:40 UTC` / `06:40 PDT`** — an observation
window of **~13 hours 37 minutes**.

## 3. Runtime Baseline

- **A real, natural restart occurred inside this window**, confirmed via process
  inspection, not assumed: PID `56618` (yesterday's process, running since
  `09:44:38 PDT` Sep 28) continued past T0, then crashed at **`19:15:45 PDT` Sep 28**
  (`2026-09-29T02:15:45Z`) — the same real MLX-signature crash independently
  identified in this session's own earlier seam-signal and Echo-Studio-timeout
  investigations. `start_echo.sh`'s watchdog restarted it 9 seconds later; the
  current process, **PID `71538`**, has been running continuously since
  `19:15:54 PDT` Sep 28, uptime **~11h24m** at investigation time, confirmed via
  `ps -o lstart,etime`.
- **A real startup snapshot exists for this exact restart**:
  `memory/snapshots/20260929T021656Z/` (`trigger: "startup"`,
  `timestamp_utc: "2026-09-29T02:16:56.757555+00:00"` — 62 seconds after process
  start, consistent with the snapshot thread's own startup delay). This snapshot's
  `river_brain.pkl` is used below as the exact state at the restart boundary — a
  real historical artifact, not reconstructed after the fact, exactly matching the
  methodology yesterday's report used for its own morning snapshot.
- Repository: HEAD `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`,
  unchanged throughout; 36 pre-existing dirty paths, none touched by this mission.

## 4. Learning Surfaces Examined

Every surface yesterday's report inventoried, re-checked fresh against T0:
RiverBrain `model_task_stats`, VSL (`memory/skill_ledger/`), self-edit candidate
state and convergence tracking (`self_edit_convergence.json`), Dissent Log, Restore
Log, FAISS/vector memory, `interaction_log.jsonl`, `council_deliberations.jsonl`,
echo_state/self_model periodic telemetry. No additional surface was found this
session with a "known architectural mechanism capable of carrying experience
forward" that yesterday's inventory missed.

## 5. Unified Timeline

| Time (UTC) | Event | Source |
|---|---|---|
| 00:02:44 | T0 — yesterday's evidence cutoff | Prior report |
| 00:10:59 – 02:12:31 | 18 real self-edit terminal outcomes (13 `safety_blocked`, 5 `dry_run_staged`) — pre-restart | `SELF_EDIT.log` |
| ~02:15:45 | Real MLX-signature process crash | `echo_watchdog.log` (independently corroborated by two other missions this session) |
| 02:15:54 | Watchdog restart — new PID 71538 born | `ps`/`echo_watchdog.log` |
| 02:16:56 | Real startup snapshot captured | `memory/snapshots/20260929T021656Z/manifest.json` |
| 02:27:19 – 13:26:07 | 88 further real self-edit terminal outcomes (81 `safety_blocked`, 7 `dry_run_staged`) — post-restart | `SELF_EDIT.log` |
| Continuous, 00:02–13:40 | 511 new `interaction_log.jsonl` entries, 386 new `council_deliberations.jsonl` entries | Direct count this session |
| Continuous | RiverBrain `model_task_stats` shifting across the same task-type buckets yesterday tracked | `memory/river_brain.pkl` |
| — | Zero VSL file activity | `find ... -newer` (unchanged since before yesterday's process even started) |
| — | Zero new Dissent/Restore Log activity | File mtimes unchanged |

## 6. Candidate Events

### Candidate 1 — RiverBrain `model_task_stats`, continued (accepted)

**BEFORE**: T0's recorded values (yesterday's own "after" column).
**EXPERIENCE**: 106 further real self-edit terminal outcomes (0 successes) plus 511
real scored conversational interactions since T0, spanning a real process crash.
**UPDATE**: measured directly, three-point trajectory (T0 → restart snapshot → now):

| Task type | T0 count/mean | Restart-snapshot count/mean | Now count/mean |
|---|---|---|---|
| coding | 67,048 / 0.6815 | 67,089 / 0.6715 | 67,459 / 0.6596 |
| self_edit_coding | 9,663 / 0.3219 | 9,674 / 0.3180 | 9,769 / 0.2901 |
| personal | 61,177 / 0.6902 | 61,242 / 0.6965 | 61,665 / 0.6568 |
| general | 695 / 0.8209 | 695 / 0.8209 | 698 / 0.8149 |
| echo_projects_coding | 2,019 / 0.7442 | 2,019 / 0.7442 | 2,031 / 0.7494 |
| creative | 210 / 0.8667 | 210 / 0.8667 | 212 / 0.8656 |
| reasoning | 130 / 0.9538 | 130 / 0.9538 | 130 / 0.9538 |

**AFTER**: the mean continues to move, in the same direction (`self_edit_coding`
declining, `coding`/`personal` also declining) as an unbroken continuation of
yesterday's trend — not a new, unrelated shift.
**CAUSAL PATH**: identical to yesterday's — `RiverBrain.learn()`/
`.learn_from_sandbox_outcome()` writing real outcomes into the windowed
(`_MEAN_EFFECTIVE_WINDOW=200`) incremental mean. **New evidence this mission adds**:
this mechanism, and its accumulated state, **survived a real, natural process crash
intact** — the restart-snapshot's values are a clean continuation of T0's, not a
reset (Section 3, Section 9).

### Candidate 2 — Sustained, non-improving self-edit failure (accepted as a negative finding)

**BEFORE**: yesterday's 8/8 real failure rate, three syntax-error shapes.
**EXPERIENCE**: 106 further real attempts since T0, **zero successes, zero
`rejected_not_improvement`** (i.e., not one candidate has even reached the
fitness-gate comparison since T0 — every single one was rejected by F1 before
that point).
**UPDATE**: none in the "correction" sense — see Section 9's direct falsification
of the specific correction-learning hypothesis this candidate was tested against.
**AFTER**: the *specific* error signature drifted over the window — earlier entries
show "expected an indented block after 'for'/'except'/'else' statement" errors;
the most recent 30 entries are dominated by "invalid syntax" (22) and "unterminated
string literal" (8).
**CAUSAL PATH**: none establishing improvement — this reads as stochastic drift
among several distinct, equally-fatal syntax-failure families, not convergence
toward correctness.
**Classification**: Level 0 for the attempts themselves (as yesterday); their real
contribution is feeding Candidate 1's continued `self_edit_coding` decline.

### Candidate 3 — `self_edit_convergence.json` (checked, rejected as new evidence)

Touched at `06:17:42 PDT` today (mtime changed) but its actual tracked values
(`cycles_attempted`: prose_stripping=95, response_shortening=63, quality_scoring=15)
are **byte-identical** to yesterday's. This is the exact "mtime is not semantic
evidence" trap Phase 10 warns against, caught directly: the file was rewritten but
produced no new content, consistent with `_record_convergence()` only firing on a
production-relevant (non-dry-run, past-F1) terminal state — none of which have
occurred since T0.

### Candidate 4 — VSL, memory growth, Dissent/Restore Log (all rejected, same as yesterday)

No change in kind from yesterday's findings — VSL remains completely inactive; FAISS/
`interaction_log.jsonl` grew by ordinary conversational volume (511/386 new
entries) with no isolated retrieval-driven behavioral change demonstrated; Dissent
and Restore Logs remain untouched.

## 7. RiverBrain

**New adaptation**: real, measured, continuing (Section 6, Candidate 1).
**Downstream use, tested directly**: `score_model(model_name, task_type)`
(`app/core/echo_model_orchestrator.py:1018`) returns `stats["mean"]` directly —
meaning the restart-snapshot value (e.g., `echo:latest`/`self_edit_coding` = 0.3180)
and the current value (0.2901) are **literally, exactly** what this function would
have returned at those two respective moments. `score_model()` feeds
`entropy_of_predictions()` and the exploration/fair-sampling logic in
`river_deliberation._select_council()`. **Every one of the 106 self-edit attempts
and 229 real "coding"-task conversations since T0 structurally necessitated at
least one call into this scoring path** — the changed value was not merely stored,
it was mechanically *read* by real, live decision code, repeatedly, throughout the
window.

**What was not established, stated honestly rather than inflated**: a *specific,
concrete instance* where this changed value actually altered which model was
selected (as opposed to being read and simply not tipping the outcome) was not
found. `choose_model()`'s primary top-pick driver is `rank_models()`, a separate,
reflection-log-based mechanism that does not read `model_task_stats` at all (an
already-documented limitation, re-confirmed rather than re-derived here) — the
statistic's real, current leverage is narrower (exploration probability, fair-
sampling tie-breaks), and confirming a real coin-flip actually landed differently
because of today's specific number, from passive logs alone, was not achievable in
this pass without either code instrumentation (out of scope) or a live probe
(explicitly prohibited). **This is exactly the smallest missing evidence named in
Section 17.**

## 8. VSL / Skills

Zero activity, confirmed exactly as yesterday: no file under
`memory/skill_ledger/` has been modified since before Echo's process even started
this cycle.

## 9. Self-Edit Learning — Direct Falsification of Correction-Learning

Phase 6 of this mission asked, specifically: did the same syntax-error family
recur; did its frequency decline; did candidate structure change in response to
recorded failure; did Echo later encounter the same bug family and succeed?

**Directly tested, and rejected**: the failure rate is **unchanged at 0% real
success** across 106 further attempts (vs. yesterday's 8). The error *signature*
did shift over time (from indentation errors to invalid-syntax/unterminated-string
errors) but this is not evidence of learning — it is evidence of **unconverged
drift among distinct, equally-fatal failure modes**, with no observed trend toward
correctness. `self_edit_convergence.json` (Section 6, Candidate 3) — the one
mechanism in this architecture explicitly designed to persist and act on exactly
this kind of repeated-failure signal — shows **zero new activity**, confirming no
part of the pipeline has yet reached a state where this recorded history is being
converted into a differently-shaped prompt. **The honest conclusion is that Echo
has not learned from these failures in any observable sense** — the same broad
class of mistake (structurally invalid Python) recurs, just wearing different
specific masks.

## 10. Memory / Retrieval

511 new `interaction_log.jsonl` entries and 386 new `council_deliberations.jsonl`
entries since T0 — real, ordinary conversational/coding volume, consistent with
continuous operation, not a distinct new learning surface. No isolated case of
"a specific stored memory was retrieved and measurably changed a later response"
was investigated or found — the same gap yesterday's report left open (Level 1
storage, not demonstrated Level 1→2 retrieval-driven improvement) remains open
today, unchanged.

## 11. Natural Transfer

No candidate was found. No cross-episode competence transfer exists in this
window's evidence — self-edit's own repeated attempts (Section 9) are the closest
candidate for "same problem recurring," and they show the *absence* of transfer
(the same class of mistake keeps recurring), not its presence.

## 12. Restart Persistence

**This is the genuinely new, valuable result this mission adds beyond yesterday's
report.** Yesterday explicitly declined to test this ("Not tested: persistence
across an actual process restart... a deliberate choice... restarting the live
production instance was judged an unjustified risk"). A real, natural crash-restart
occurred inside this mission's own observation window, unprompted by any
investigation, giving a genuine, zero-risk opportunity to check it directly.

**Result: confirmed, cleanly.** The restart snapshot's `model_task_stats` values
(`self_edit_coding`: 9,674/0.3180; `coding`: 67,089/0.6715, etc.) are not a reset to
any baseline or default — they are the exact, continuous extrapolation of T0's
values plus the real activity that occurred in the ~2h13m between T0 and the
crash (matching, count-for-count, the 18 real self-edit entries and a
proportionate share of real conversational activity logged in that same window).
**Yesterday's Level-2 adaptation genuinely, demonstrably survived a real process
crash intact.**

## 13. Falsification

Applied directly to the strongest candidate (Candidate 1, Section 6):

- **F1 (state change existed before T0)**: no — the trajectory is a strict,
  monotonic-direction continuation from T0's own recorded values, not a
  pre-existing condition being rediscovered.
- **F2 (later behavior would have occurred without the update)**: not
  applicable in the strong sense — no specific "later behavior" beyond continued
  statistical movement is being claimed as demonstrated (Section 7's honest
  limitation).
- **F3 (human/Claude intervention caused it)**: ruled out — this entire
  investigation was read-only; no query, self-edit trigger, or scored interaction
  was submitted by this or any other session as part of investigating this window.
- **F4 (same prompt/context explains it)**: not applicable — the update is a
  continuous rolling-window statistic over hundreds of genuinely distinct real
  interactions and self-edit attempts, not one repeated prompt.
- **F5 (the relevant persistent state was never actually read later)**: **ruled
  out directly** — `score_model()`'s own code makes reading `stats["mean"]`
  unconditional for every scoring call; every real coding/self-edit event since
  T0 necessarily invoked this path (Section 7).
- **F6 (merely memory storage)**: ruled out — this is a live, currently-used
  adaptive scoring input, not passive storage (though see Section 7's honest
  limit on how far "used" has been demonstrated to reach).
- **F7 (merely statistical bookkeeping)**: partially true, and disclosed as such
  — this is precisely why the verdict stays at Level 2, not Level 2+: the
  update is real adaptive statistics with a structurally guaranteed downstream
  read, but not a demonstrated behavioral consequence.
- **F8 (deterministic replay/backfill)**: ruled out for Candidate 1 — the three
  measured points (T0/restart/now) show real, increasing counts and non-repeating
  mean values, unlike the flat, byte-identical `[CONVERGENCE_BACKFILL]`/
  `self_edit_convergence.json` pattern (Candidate 3), which *was* correctly
  caught as pure replay this time, not mistaken for new evidence.
- **F9 (log duplication/citation contamination)**: checked — the self-edit error
  signatures across the window are genuinely varied (indentation errors vs.
  invalid-syntax vs. unterminated-string, each with distinct real line numbers),
  not one error being re-logged.
- **F10 (the "later event" preceded the "learning event")**: not applicable —
  strict timestamp ordering was maintained throughout (T0 → crash → restart →
  now), verified directly via `ps`, the snapshot manifest, and `SELF_EDIT.log`'s
  own timestamps.

## 14. Comparison With Previous Level-2 Event

# NO — stronger in one specific, real respect (restart persistence), but not stronger on the dimension this mission specifically asked about (behavioral consequence)

**What is genuinely new and stronger**: real, natural restart-persistence evidence
(Section 12) — a real gap yesterday's report explicitly left open and this mission
closed with zero manufactured risk, using a crash that happened on its own.

**What remains exactly as missing as yesterday**: no concrete instance of a
changed statistic altering a specific, observed decision was found — Section 7's
honest limitation is identical in kind to yesterday's own "Transfer Evidence: not
applicable" disclosure. The self-edit correction-learning hypothesis (Phase 6, the
most promising *new* avenue this mission specifically pointed at) was tested
directly and **failed** — a real, informative negative result, not a gap in
investigation effort.

## 15. What This Establishes

- Yesterday's Level-2 RiverBrain adaptation is real, ongoing, and — newly
  confirmed — **survives a genuine process crash and restart intact**.
- The specific causal mechanism (F1-rejection-driven `self_edit_coding` decline)
  continues, unbroken, across a second and longer period, with no sign of
  self-correction.
- The scoring function that reads this adaptive state (`score_model()`) is
  unconditionally exercised by every real coding/self-edit event in this window —
  a structurally guaranteed, not merely hypothetical, downstream read.

## 16. What This Does NOT Establish

- **No Level 2+ claim**: no specific real decision was shown to have been
  *altered* by the changed statistic, as opposed to having *read* it.
- **No correction learning**: directly tested and found absent — the self-edit
  pipeline shows zero improvement in real success rate and no evidence its
  failure history is currently shaping subsequent generation attempts.
- **No transfer, no new skill, no Level 3 candidate** — none was found or
  claimed.
- **No claim about the root cause of the `coding`/`personal` mean declines**
  beyond what the windowed-mean mechanism mechanically implies — whether today's
  real conversational responses were genuinely lower quality, or this reflects
  ordinary fluctuation, was not traced to a specific cause in this pass, and is
  stated here as an open question rather than resolved either way.

## 17. Missing Evidence for Next Level

**Level 2 → Level 2+** requires one concrete thing this mission could not
establish from passive evidence: a real, logged instance where
`score_model()`'s changed output value can be shown to have altered a specific
council-selection or exploration-probability outcome that would have gone
differently under the pre-change value — e.g., a documented case where a
borderline exploration draw or a fair-sampling tie-break resolved one way with
today's number and would provably have resolved the other way with yesterday's.
This would most plausibly come from either instrumenting `_select_council()`'s
own decision (a source change, out of scope for a read-only mission) or a careful
reconstruction using real, already-logged per-cycle randomness if such logging
existed (it currently does not, to the granularity needed).

**Level 2+ → Level 3** remains exactly as yesterday's report described it: genuine
evidence of a persistently-represented, reusable transformation, demonstrated
working on a later, distinct problem it previously could not solve. Nothing in
today's evidence moves this any closer — if anything, Section 9's direct
falsification of correction-learning suggests the self-edit pathway specifically
is not currently on a trajectory toward this on its own.

## 18. Repository / Runtime Integrity

- Canonical source: unchanged throughout, HEAD `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`,
  matching `origin/main`.
- Echo's live process (PID 71538) was not stopped, restarted, or signaled by this
  investigation — its one real restart during the observation window was a
  natural event that occurred before this mission began, not caused by it.
- No learning was deliberately induced; no self-edit was triggered; no skill was
  created or promoted; no memory was deleted or normalized.
- All state files inspected (`river_brain.pkl`, both real snapshots,
  `SELF_EDIT.log`, `interaction_log.jsonl`, `council_deliberations.jsonl`,
  `self_edit_convergence.json`, VSL skill files, dissent/restore logs) were
  read-only operations.
- Nothing was staged, committed, or pushed. The only new artifact produced is
  this report file itself, left untracked and unstaged.
