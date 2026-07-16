# Runtime Observations

Investigation date: 2026-07-16, superseding the 2026-07-04 version. All
observations below are from the live, currently-running system at
investigation time — the server was restarted earlier tonight
specifically to load a batch of fixes made this session, so this pass
captures its first ~15-20 minutes of fresh uptime, not a long-settled
state. That's noted explicitly wherever it affects how much weight to put
on a given reading (e.g. a check needing 20 accumulated post-restart log
entries hasn't had time to fill its own window yet).

## Live process state at investigation time

```
python -u run.py     PID 88140   uptime ~15-20min at last check
ollama serve          PID 32306   running since Sun 10PM
Ollama (GUI)          PID 32304   running since Sun 10PM
```
No `terminal_client.py` session was open during this pass (unlike the
original audit, which had an active human session running concurrently).

`memory/echo_sentinel.json`: `stage: "serving"`, `pid: 88140`, start
`2026-07-16T06:48:07Z`, heartbeat fresh (within ~11s of the check that read
it). Clean startup, confirmed via the sentinel independently of the
process table.

## FAISS / memory state — the original audit's single largest unresolved item is now resolved

```
memory/memory_meta.json:  47,607 vectors   (was 0 at the original audit)
data/memory_meta.json:     5,348 vectors   (legacy, mtime May 15 — untouched)
```
`memory/`'s count matches `self_model.json`'s own reported
`faiss_vector_count` exactly, and is independently corroborated by the
Liveness Ledger's `self_model_drift` check passing. This is a genuine
resolution, not an assumption: CLAUDE.md documents the real cause (both
files were mid-write at the exact moment of the original audit's check,
combined with a real, separately-fixed migration event on 2026-07-13 that
recovered 5,165 entries from `data/` into `memory/`) and this pass
independently re-counted rather than trusting that account.

`data/memory_meta.json` still exists, unchanged, exactly as CLAUDE.md's
FAISS Dual-Index section says it was deliberately left in place as a
historical artifact after its content was migrated — this pass confirms
the file is still there and still untouched (May 15 mtime), which
**confirms** that section of CLAUDE.md rather than contradicting it.

Also found this pass, not previously inventoried: four archived/backup
FAISS index files alongside the live one (`faiss_contaminated_*`,
`faiss_splitbrain_*`, `faiss_prefixfix_*`, `faiss_pre_delete_*`) — a real,
visible history of past index-corruption incidents and their remediation,
consistent with CLAUDE.md's own documented split-brain history. Not a new
problem; a useful artifact trail of old ones.

## Confirmed-firing autonomous behavior (fresh evidence, not re-quoted from CLAUDE.md)

- **Self-edit loop**: `memory/SELF_EDIT.log`'s most recent entry (06:51:55
  UTC today) is a real, live **failure** — a staged candidate targeting
  the `prose_stripping` family hallucinated `from app.emergent_scheduler
  import guard_prose`; the real `guard_prose` function lives in
  `self_edit_generated.py` itself, not `emergent_scheduler.py`. The
  staging import test correctly caught this (`ImportError`), the
  candidate was rejected, zero production impact. Directly confirmed
  this is unrelated to any of tonight's own changes to
  `emergent_scheduler.py` (the function `guard_prose` doesn't appear
  anywhere in this session's edits to that file). This is the pipeline
  working exactly as designed against an ordinary hallucination.
- **Global Workspace bus**: `memory/workspace_log.jsonl`'s recent tail
  (last 500 lines) shows 5 distinct real sources: `dream_cycle` (2),
  `world_model` (13), `emergent_loop` (35), `river_deliberation` (7),
  `echo_optuna` (2). Genuine multi-subsystem traffic, not one publisher
  talking to itself — matches the `global_workspace` liveness check's own
  passing verdict.
- **`reflection_journal.jsonl`**: 2,254 lines total; the most recent entry
  (06:32:16) **predates** the current server process's start (06:48:07) —
  i.e., the reflection-shard autonomy loop had not fired even once in
  this process's first ~15 minutes at last check. At 300s cadence with a
  35% per-cycle probability, only ~2-3 chances had elapsed by the time of
  this check, so a `(0.65)^2 ≈ 42%`+ chance of zero fires by pure chance
  is not itself alarming — but it means tonight's real-generation fix has
  not yet been observed firing in production, only in isolated testing.
  Flagged as Unable to Determine (transient vs. a real issue) rather than
  assumed either way, pending a longer observation window.
- **Council rating pipeline**: `council_ratings.jsonl` has 84 entries (up
  from 12 at the original audit). `GET /admin/council-stats`:
  `agreement_rate: 0.643` (below the 0.70 trust threshold),
  `baseline_trusted: false`, `total_rated: 79`, `pending_spot_checks: 36`.
  Genuinely running, genuinely not yet at its own trust bar — consistent
  trajectory, not stalled.
- **Self-edit outcome tracker**: `self_edit_outcomes.jsonl`'s recent
  entries still show negative or unresolved (null) post-deltas
  (-0.398, -0.355, several `post: null`) — consistent with CLAUDE.md's own
  documented finding that the 25-minute post-window is frequently empty in
  practice. No sign of improvement in this specific signal since it was
  first characterized.
- **Shadow-model calibration**: `shadow_accuracy.jsonl`'s last 5 entries
  all show `focus_matches: false` and near-zero quality deltas — the
  shadow prediction and the real target haven't been agreeing. This is a
  real, live, ongoing signal (not evidence the mechanism is broken — see
  CLAUDE.md's correction tonight that this pipeline is genuinely wired via
  `emergent_scheduler.py`'s `propose_from_reflection()`), just not yet
  demonstrating strong calibration.

## Self-edit convergence state (`app/core/self_edit_convergence.json`, read in full)

- `prose_stripping`: 94 cycles attempted, 31 distinct function names —
  worse churn in raw terms than the ~14-cycle sample the original audit
  reviewed; a fresh real failure was observed live during this pass (see
  above).
- `response_shortening`: 11 cycles, 4 names — meaningfully more
  convergent.
- `quality_scoring`: 3 cycles, 3 names — effectively converged.
- `unclassified`: 11 cycles, 30+ mixed names — looks like a convergence-
  family classification bug, not a self-edit content problem; new finding
  this pass, not previously documented, not root-caused here.

## What this audit could NOT verify (explicitly flagged, not guessed)

- Whether `reflection_shard`'s real-generation fix is actually firing in
  steady-state production — the observation window available this pass
  (first ~15-20 minutes post-restart) was too short to say with
  confidence; needs a re-check after a few hours of uptime.
- Whether `data/memory_meta.json`'s continued existence poses any risk —
  it appears to be inert (untouched since May 15), but this pass did not
  independently verify that nothing anywhere still reads from it.
- The real root cause of the `unclassified` convergence-tracking bucket —
  flagged, not diagnosed.
- Whether `/mirror_echo`'s missing authentication (see risk_register.md)
  has ever actually been exploited or reached from outside the intended
  network boundary — this pass confirms the code-level gap, not any
  network-level exposure or exploitation history.
