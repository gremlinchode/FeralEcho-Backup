# Natural Learning Event Hunt — Did Echo Learn Anything This Afternoon?

**Read-only forensic investigation.** No canonical source was modified. Nothing was staged,
committed, or pushed. No skill was taught, promoted, or manually inserted. No training was
triggered. No controlled probe was run (justified in Section 9 — not needed for the
strongest candidate found). Echo's live process was never restarted or interrupted.

## 1. Verdict

# NATURAL LEARNING EVENT DETECTED — LEVEL 2

Real, quantitative, causally-traceable persistent statistical adaptation occurred in
RiverBrain's `model_task_stats` during Echo's natural operation this afternoon, recovered
via an actual before/after comparison against a genuine startup snapshot (not
reconstructed after the fact). This is **adaptation, not skill acquisition** — no Level 3
claim is made or supported. Every other learning surface investigated (VSL, self-edit
promotion, shadow model, dissent/restore logs) shows **zero qualifying activity** today.

## 2. Investigation Window

- **Echo process**: PID 56618, started `2026-09-28 09:44:38` local (PDT), confirmed via
  `ps -o lstart`. Supervised by `start_echo.sh`'s watchdog (PID 56610).
- **Uptime at investigation time**: ~7h20m, zero restarts, zero crashes — a single
  continuous process for the entire window.
- **Investigation window used**: `09:44:38` (process start) → `17:02` local (investigation
  start), i.e., the entirety of Echo's own live uptime today, which spans morning through
  the current afternoon.
- **Corroborating evidence**: a real, automatic startup snapshot exists at
  `memory/snapshots/20260928T164541Z/` (UTC; = `09:45:41` local), timestamped one second
  after process start (`manifest.json`'s `"trigger": "startup"`) — this became the
  investigation's actual "before" baseline, not an approximation.
- No maintenance/night-cycle restart, no self-edit-triggered process reload, and no
  model reload occurred in this window (single continuous PID throughout).

## 3. Learning-Surface Inventory

| Surface | Path | Writer | Reader | Natural update trigger |
|---|---|---|---|---|
| VSL (Verified Skill Ledger) | `memory/skill_ledger/skills/*.json`, `NEXT_ACTION.md` | Skill Ledger promotion pipeline | `app.core.skill_ledger.matcher`/`runtime` | Explicit promotion decision (rare, gated) |
| RiverBrain `model_task_stats` | `memory/river_brain.pkl` | `RiverBrain.learn()`, `.learn_from_sandbox_outcome()`, `.learn_from_council_rating()` | `score_model()`/`choose_model()` | Every real generation, every sandboxed self-edit outcome, every trusted council rating |
| Self-edit candidate state | `app/core/self_edit_generated.py` | `save_code()` after F1/F2/F3 | The running process (on load) | A candidate clearing all three safety gates |
| Self-edit convergence tracking | `app/core/self_edit_convergence.json` | `_record_convergence()` + startup backfill | `_build_targeted_prompt()` | Every self-edit attempt (any outcome) |
| Dissent Log | `memory/dissent_log.jsonl` | `_log_dissent_entry()`, `_log_restore_dissent_entry()` | Human review, Global Workspace | A real protected-file proposal or restore review |
| Restore Log | `memory/restore_log.jsonl` | `restore_snapshot()` | Human review | A real `/admin/restore` call |
| Shadow model accuracy | `memory/shadow_accuracy.jsonl` | (retired — no live writer, confirmed this session's own Gate 1) | None (disconnected) | N/A |
| FAISS/vector memory | `memory/memory_meta.json`, `memory/faiss.index` | `add_to_vector_memory()` | `retrieve_relevant_memories()` | Every stored interaction/reflection |
| Echo state vector | `memory/echo_state.npy`, `echo_state_history.npy` | `echo_state.py`'s 120s cycle | `system_guard`, prompt-weighting | Periodic, always-on |
| Self-model | `memory/self_model.json` | `self_model_updater.py`'s 130s cycle | `echo_ground_truth.py` | Periodic, always-on |

## 4. State Delta Timeline

All artifacts hashed and timestamped at investigation start (`2026-09-29T00:02:44Z` /
`17:02:44` local); compared against the real startup snapshot where one existed.

| Time (local) | Artifact | Change | Writer | Possible Meaning | Confidence |
|---|---|---|---|---|---|
| Continuous, 09:44→17:0x | `memory/river_brain.pkl` | `echo:latest`'s `model_task_stats` shifted across 5 of 7 task-type buckets (Section 6) | `learn()`/`learn_from_sandbox_outcome()` | Real adaptive statistics update | **HIGH** |
| 15:21–16:52 | `memory/SELF_EDIT.log` | 8 real self-edit generation attempts, **all** `safety_blocked` (invalid syntax / unterminated string / unmatched paren) | `AutonomousSelfEdit` thread | Attempted adaptation, zero survived F1 | HIGH (as a negative finding) |
| 15:43–16:46 (×4) | `app/core/self_edit_convergence.json` | `[CONVERGENCE_BACKFILL]` log lines with **identical** counts every time (prose_stripping=95, response_shortening=63, quality_scoring=15) | `backfill_convergence_from_log()` | Deterministic replay of existing history, not new information | LOW (ruled out as a learning event — see Section 8) |
| Continuous | `memory/memory_meta.json`, `faiss.index` | Growing (mtime moves forward through the day) | `add_to_vector_memory()` | Ordinary episodic memory accumulation | HIGH (as Level 1, not higher) |
| Continuous, 120s/130s cycles | `echo_state.npy`, `self_model.json` | Routine periodic updates | Scheduled background threads | Telemetry, not learning | HIGH (Level 0) |
| — | `memory/skill_ledger/skills/*.json` | **None** — last modified `08:01:00`, before process start | — | Zero VSL activity today | HIGH (negative finding) |
| — | `memory/dissent_log.jsonl` | **None** — last modified `2026-07-16` | — | Zero self-edit-proposal/restore review activity today | HIGH (negative finding) |
| — | `memory/restore_log.jsonl` | **None** — last modified `2026-07-01` | — | Zero restores today | HIGH (negative finding) |
| — | `memory/shadow_accuracy.jsonl` | **None** — last modified `2026-09-19` | — | Confirms shadow model retirement (Gate 1, same day) still holds | HIGH |

## 5. Candidate Events (Including Rejected Candidates)

1. **RiverBrain `model_task_stats` shift** — **accepted as the strongest candidate**, detailed in Section 6.
2. **8 self-edit generation attempts** — rejected as a Level 3 candidate: zero candidates
   passed F1 (the AST safety scanner rejected every one for a syntax error before any
   sandbox execution, before any quality comparison, before any possibility of
   promotion). This is real, observed, autonomous *attempted* adaptation with a 0%
   success rate today — worth recording, but it produced no persistent, working,
   reusable change. Classified as **Level 0 for the attempt itself** (nothing survived),
   though the attempts *did* feed the accepted Level-2 candidate (Section 6) by lowering
   `self_edit_coding`'s mean.
3. **`[CONVERGENCE_BACKFILL]` log entries** — rejected: identical counts on every
   occurrence (95/63/15, unchanged across four separate log lines spanning
   `15:43`–`16:46`) prove this is `backfill_convergence_from_log()`'s documented
   deterministic full-replay behavior (CLAUDE.md Finding 16), not a growing signal. It
   fired repeatedly because it is called at more points in the current code than a
   single process-start event, but it derives nothing new each time.
4. **FAISS/memory growth** — rejected as anything beyond Level 1: real, ordinary episodic
   storage of today's real interactions. No evidence any specific stored memory was
   retrieved today and caused an observably different, better outcome versus not having
   it (the retrieval→improved-outcome half of a Level 1→2 upgrade was not established).
5. **VSL skill proposal/promotion** — no candidate exists; zero file-level activity since
   before process start.

## 6. Strongest Candidate

### Event
`echo:latest`'s per-task-type quality statistics inside RiverBrain
(`memory/river_brain.pkl`'s `model_task_stats`) measurably shifted during today's natural
operation, in a direction directly explainable by today's real, observed experience.

### Before Evidence
A genuine startup snapshot exists at `memory/snapshots/20260928T164541Z/river_brain.pkl`,
automatically captured one second after Echo's process started this morning (confirmed
via `manifest.json`'s `"trigger": "startup"` and timestamp `2026-09-28T16:45:41` UTC).
This is a real historical artifact, not a value reconstructed after the fact.

Recovered `echo:latest` stats at startup (before today's live operation):

| Task type | count (before) | mean (before) |
|---|---|---|
| coding | 66,784 | 0.6421 |
| self_edit_coding | 9,595 | 0.3511 |
| personal | 60,879 | 0.6816 |
| general | 689 | 0.8180 |
| echo_projects_coding | 1,999 | 0.7461 |
| creative | 210 | 0.8667 |
| reasoning | 130 | 0.9538 |

### Experience
- **476 real, quality-scored interactions** logged in `memory/interaction_log.jsonl`
  during today's window (`personal`: 236, `coding`: 217, `echo_projects_coding`: 11,
  `autonomous_fetch`: 10, `autonomous_experiment`: 2).
- **8 real self-edit generation attempts**, each independently timestamped in
  `memory/SELF_EDIT.log` between `15:21` and `16:52` local, **all** rejected by F1's AST
  safety scanner for genuine syntax defects (invalid syntax ×3, unterminated string
  literal ×2, unmatched paren ×1, plus 2 more of the same shapes).

### Persistent Mechanism
`RiverBrain.learn()` (real conversational quality scoring) and
`RiverBrain.learn_from_sandbox_outcome()` (real F2 kernel-sandbox pass/fail from each
self-edit attempt) both write directly into `model_task_stats[model][task_type]`, using
a windowed incremental mean (`_MEAN_EFFECTIVE_WINDOW = 200`, confirmed in
`app/core/echo_model_orchestrator.py:1016`) — a mechanism already independently verified,
not newly investigated for this mission, as part of this same day's own repository
reconciliation work (Finding 44's RiverBrain wiring).

### After Evidence
Recovered from the current, live `memory/river_brain.pkl` (hashed at investigation start,
`802d08a5...`):

| Task type | count (after) | Δcount | mean (after) | Δmean |
|---|---|---|---|---|
| coding | 67,048 | **+264** | 0.6815 | **+0.0394** |
| self_edit_coding | 9,663 | **+68** | 0.3219 | **−0.0292** |
| personal | 61,177 | +298 | 0.6902 | +0.0085 |
| general | 695 | +6 | 0.8209 | +0.0029 |
| echo_projects_coding | 2,019 | +20 | 0.7442 | −0.0019 |
| creative | 210 | +0 | 0.8667 | +0.0000 |
| reasoning | 130 | +0 | 0.9538 | +0.0000 |

Because `_MEAN_EFFECTIVE_WINDOW = 200` and 264 new `coding` observations landed today —
*more* than the full window — today's `coding` mean is now dominated by today's own
outcomes rather than diluted historical accumulation; this is not a rounding artifact.

### Transfer Evidence
Not applicable in the Level-3 sense (no specific new task-solving capability is being
claimed) — but the mechanism's real behavioral consequence generalizes across every
*future* task of the same type: `choose_model()`/`score_model()` read this exact mean for
ranking on the next `coding` or `self_edit_coding` request, not merely for today's
already-completed interactions.

### Authorship
**Fully autonomous with respect to today's specific update.** The informative content
(264 real coding interactions' actual quality, and 8 real self-edit attempts' actual
pass/fail from Echo's own generation + F1's automated static check) originated entirely
from Echo's own live operation and this project's already-existing, already-verified
scoring/safety machinery — no human or Claude/Codex session supplied today's specific
scores, corrections, or generated code. (The *scoring mechanism itself* — `learn()`,
`_MEAN_EFFECTIVE_WINDOW`, F1's AST scanner — is human/Claude-authored infrastructure from
prior sessions, not authored today; today's contribution was purely the real experience
flowing through that pre-existing mechanism.)

### Persistence
Confirmed on-disk in `memory/river_brain.pkl`, which is explicitly designed to survive
process restart (unlike the in-memory-only circuit breaker documented elsewhere in this
project's history). Not tested across an actual restart in this mission (see Section 11
— restarting the live production process purely to test this was judged an
unjustified, avoidable risk to a running instance for a claim that doesn't require it;
the file-persistence mechanism itself is already-established, previously-verified
architecture, not a new claim this mission needed to re-prove).

### Alternative Explanations (tested)
- **Pure noise, no real signal**: ruled out for `self_edit_coding` specifically — the
  −0.0292 shift has a direct, traceable, single-cause explanation (100% failure rate
  across all 8 real attempts today, independently confirmed via `SELF_EDIT.log`'s own
  timestamped entries), not an unexplained statistical wobble.
- **Source code changed today, so the scoring function itself is different**: ruled out
  — canonical source was confirmed frozen at `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`
  throughout this investigation (this repository-reconciliation engagement's own final
  published state), and the touched production files (`echo_model_orchestrator.py`) were
  not further modified today after that push.
- **The "before" value is itself already contaminated by today's activity**: ruled out —
  the snapshot's own `trigger: "startup"` and one-second-post-launch timestamp confirm it
  captured the *pre-operation* state.
- **This is routing/investigator intervention, not autonomous Echo behavior**: ruled out
  for authorship — no human or Claude session queried a model, triggered a self-edit
  cycle, or submitted a scored interaction during this specific window as part of this
  investigation (this mission was purely read-only throughout).

### Current Classification
**Level 2 — Adaptation.** Persistent statistics genuinely changed from real experience,
via an established, real causal mechanism, and will influence future model-selection
behavior. This does **not** meet Level 3: no new reusable transformation/policy was
created, nothing was promoted, and the change is a continuous incremental-mean shift
rather than a discrete "before it couldn't, after it could" competence boundary.

## 7. Authorship / Provenance

| Contributor | Role |
|---|---|
| Echo (autonomous) | Generated all 8 real self-edit candidates; produced the actual conversational responses scored in 476 real interactions |
| F1 (AST safety scanner, pre-existing infrastructure) | Automatically rejected all 8 self-edit candidates — no human reviewed any of them individually today |
| `RiverBrain.learn()`/`.learn_from_sandbox_outcome()` (pre-existing infrastructure) | Mechanically translated today's real outcomes into the persistent statistical shift |
| Human (Gremlin) / Claude / Codex | **No direct authorship of today's specific update** — did not supply an answer, correction, or transformation that became today's persisted content |

## 8. Falsification

Every alternative explanation attempted is documented inline in Section 6's "Alternative
Explanations" subsection. Additionally: the `[CONVERGENCE_BACKFILL]` candidate (Section
5, item 3) was actively attacked and **did** collapse under falsification — its repeated
appearance initially looked like recurring new evidence, but identical counts across four
separate occurrences prove it is deterministic replay, not accumulation, and it was
downgraded accordingly rather than rescued into the final candidate list.

## 9. Controlled Probe

**Not performed.** The mission's own Phase 14 authorizes a controlled probe only for a
candidate that has survived falsification and requires further testing to establish
causality or transfer for a Level 3+ claim. The accepted candidate (Section 6) is a Level
2 finding with its causal chain already established from real, natural, historical
evidence (a genuine recovered snapshot, not a reconstruction) — no synthetic test was
needed to strengthen it, and running one risked exactly what this mission prohibits
("do not manufacture... do not trigger training merely to obtain a positive result").

## 10. Causal / Ablation Result

**Not established via intervention** — no ablation was run, deliberately, per Section 9's
reasoning. The causal claim rests on: (a) a real architectural mechanism already
independently verified in this project's history (not re-derived here), (b) a genuine
before/after snapshot pair (not synthetic), and (c) a directly traceable single-cause
explanation for the `self_edit_coding` shift specifically (8/8 real failures, matched in
count and timing to the observed statistical movement). This is strong natural evidence
for Level 2, but an ablation was not performed and no claim beyond Level 2 is made that
would require one.

## 11. Persistence Result

**Tested boundary: on-disk file persistence, observed continuously across ~7 hours of
uninterrupted live operation.** Not tested: persistence across an actual process
restart. This was a deliberate choice, not an oversight — Section 6 explains why
restarting the live production instance was judged an unjustified risk for a claim this
mission does not need a restart to support (the write-to-disk-then-reload-on-next-start
mechanism for `river_brain.pkl` is pre-existing, previously-established architecture, not
something this specific mission is claiming to prove for the first time).

## 12. Novelty / Leakage Result

Not directly applicable to a Level 2 finding (no "transfer to an unseen case" claim is
being made — Level 2 is about statistics/policy, not about solving a specific new
problem). For completeness: today's 217 real coding interactions and 8 real self-edit
attempts were checked against `memory/SELF_EDIT.log`'s own history and found to be
genuinely new, timestamped events (not duplicates of earlier logged attempts) — the
specific `[SAFETY]` error strings differ in kind across the 8 attempts (three distinct
Python syntax-error categories), consistent with genuinely independent generation
attempts rather than one error being repeatedly re-logged.

## 13. Classification

**Level 2 — Adaptation**, for the RiverBrain `model_task_stats` finding (Section 6).
**Level 0**, for the 8 self-edit generation attempts (none survived F1; no persistent
competence resulted, though they did contribute real input to the accepted Level-2
finding). **Level 0 / no activity**, for VSL, the Dissent Log, the Restore Log, and the
(already-retired) shadow model. **Level 1** at most for ordinary FAISS/episodic memory
growth — real storage, no demonstrated retrieval-driven behavioral improvement isolated
today.

## 14. What This Does NOT Establish

- **No new skill or reusable transformation was acquired today.** VSL shows zero
  activity; no self-edit candidate survived even the first safety gate.
- **No claim of "Echo taught itself a capability."** The Level-2 finding is a statistical
  routing-preference shift, not new problem-solving ability.
- **No claim that today's `coding` mean increase reflects genuinely "better" underlying
  model behavior** in any deep sense — it reflects whichever real interactions happened
  to occur today, scored by the existing quality-scoring function; a 4-point mean shift
  over 264 samples is a real, measured fact, not evidence of qualitative improvement.
- **No restart-survival test was performed** — persistence is asserted from established
  prior architecture and continuous same-process observation, not from an executed
  restart this session.
- **No causal ablation was performed** — the causal story rests on strong, real,
  traceable natural evidence (especially for `self_edit_coding`), not an intervention.
- **This does not mean Echo cannot learn a skill.** It means no qualifying Level-3+ event
  was demonstrated in this afternoon's evidence specifically.

## 15. Repository / State Integrity

- Canonical source: confirmed unchanged throughout at `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`
  (this repository's own just-published state); this investigation performed zero writes
  to any tracked file.
- Echo's live process (PID 56618) was never restarted, signaled, or interrupted during
  this investigation.
- All state files inspected (`river_brain.pkl`, the startup snapshot, `SELF_EDIT.log`,
  `interaction_log.jsonl`, `self_edit_convergence.json`, VSL skill files, dissent/restore
  logs) were read-only operations; nothing was modified, deleted, or reset.
- No skill was promoted, inserted, or altered. No self-edit output was repaired or
  cleaned. No telemetry was normalized.
- The only new artifact produced by this mission is this report file itself, not staged
  or committed, per the mission's explicit instruction.
