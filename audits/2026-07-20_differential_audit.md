# Differential Forensic Audit — 2026-07-20 (into 2026-07-21)

Run per `audits/differential_audit_prompt.md`. Baseline: `CLAUDE.md` on-disk
as of this session (mtime 2026-07-20 11:42:33 PDT, includes the uncommitted
Finding 49 correction — this is genuinely current, not stale), plus
`PENDING_DECISIONS.md` (last swept 2026-07-19), `GREMLIN_ROLE.md`, `ORIGIN.md`.
Server was live throughout (`GET /admin/liveness-status` → `all_passing: true`,
`stale: false`, 18/18 checks passing at session start).

**Bottom line: no material drift.** Every specific, checkable claim spot-checked
this session held. One genuinely new finding (crash frequency, below) and one
process gap (COUNCIL.md's own open question isn't tracked in
`PENDING_DECISIONS.md`). Everything else is a clean confirmation, reported as
such rather than padded into false findings.

---

## Phase 0 — Baseline table

| Claim | Documented | Last verified per CLAUDE.md |
|---|---|---|
| 18 Liveness Ledger checks, 56 discrimination cases | Liveness Ledger section | 2026-07-19 |
| `EDIT_FORBIDDEN_TARGETS` = 10 files, `reflection_shard.py` not in it | Protected Files section / Pending #9 | 2026-07-19 (flagged open) |
| RiverBrain: `TAG_SCORE_BOOST`, `_MEAN_EFFECTIVE_WINDOW=200`, `_RETIRED_MODELS`, `fair_sample_refresh` | Finding 39 | 2026-07-16 |
| `self_edit_coding` task-type bucket | Finding 35 follow-up | 2026-07-17 |
| `apply_to_code` write-block (`_block_writes_for_apply_to_code`) | Finding 31 fix | 2026-07-15 |
| `prose_stripping` paused from self-edit rotation | Finding 43 | 2026-07-19 |
| Global Workspace: `wide_broadcast` @ 0.6 threshold, `coupling_estimate` history persistence | Phase 6 / Finding 45 #3 | 2026-07-16 / 2026-07-19 |
| `model_guided_orchestrator` gated via `autonomy_coordinator.should_run_cycle` | Finding 28 fix | 2026-07-15 |
| `conversation_activity.py` chokepoint in `should_run_cycle` | Finding 45 #4 | 2026-07-19 |
| B1/B2/B4/B5 concurrency locks (`_outcomes_lock`, `_salience_state_lock`, `_seam_state_lock`, `_dissent_log_lock`) | Finding 41 B / follow-up | 2026-07-18 |
| MLX/Metal crash: "three occurrences in about 21 hours" | Finding 49 | 2026-07-20, 11:42 |
| FAISS `data/` frozen since May 15, `memory/` growing | FAISS Dual-Index section | 2026-07-13 |

---

## Phase 1 — Drift check: all clean

Every claim below was checked against live source or live runtime state this
session, not re-read from CLAUDE.md's own prose.

- **Liveness Ledger** `[VERIFIED]` — live `GET /admin/liveness-status` returns
  exactly 18 keys with a `pass` field, names matching CLAUDE.md's table
  1:1, `all_passing: true`. `grep -c "^check(" scripts/verify_liveness_ledger.py`
  → 56, matching the doc's claimed discrimination-case count exactly.
- **RiverBrain / council mechanism** `[VERIFIED]` — `TAG_SCORE_BOOST = 1.15`,
  `UNDER_SAMPLED_REFRESH_PROBABILITY = 0.25`, `fair_sample_refresh` param,
  `exploration_bias` param all present in `river_deliberation.py` exactly as
  described. `_MEAN_EFFECTIVE_WINDOW = 200`, `_RETIRED_MODELS = {"vicuna:latest"}`,
  and `TASK_TYPE_MAP` including `"self_edit_coding": 5` all present in
  `echo_model_orchestrator.py`.
- **Self-edit pipeline** `[VERIFIED]` — `EDIT_FORBIDDEN_TARGETS` is the same
  10-file frozenset CLAUDE.md lists; `app/subsystems/reflection_shard.py` is
  still absent from it (Pending #9 is accurately still open, not stale).
  `_block_writes_for_apply_to_code()` and `_call_with_timeout()` both present
  at the cited call site. Cooldown persistence (`_load_last_autonomous_edit`/
  `_persist_last_autonomous_edit` → `memory/self_edit_cooldown.json`) intact.
  `prose_stripping` is commented out of `_FOCUS_FAMILY_BY_CREATIVITY` with the
  cited 2026-07-19 comment still in place.
- **Global Workspace** `[VERIFIED]` — `_salience_state_lock`, `_persist_salience_state`
  persisting `history`, `_load_salience_history()`, `wide_broadcast` gated at
  the documented threshold, and `reflection_shard`'s wide-broadcast subscriber
  registration are all present in `echo_core.py`. Live workspace events in the
  last 24h come from 4 distinct sources (`echo_optuna`, `emergent_loop`,
  `river_deliberation`, `world_model`) — `global_workspace` check passes with
  room to spare over its 2-source bar.
- **Autonomy gating** `[VERIFIED]` — `echo_model_guided_orchestrator.py:75`
  calls `should_run_cycle("model_guided_orchestrator")` (Finding 28's fix is
  real, not just claimed); `autonomy_coordinator.py` imports and checks
  `is_conversation_active()` from the real `conversation_activity.py` (Finding
  45 #4).
- **Concurrency fixes (Finding 41 B1/B4/B5)** `[VERIFIED]` — `_outcomes_lock`
  guards both `record_pending_outcome()` and `_evaluate_pending_outcomes_locked()`
  in `self_edit_outcome_tracker.py`; `_seam_state_lock` guards `seam_engine.py`'s
  load→compute→save section; `_dissent_log_lock` guards `self_edit_manager.py`'s
  dissent-log append. All three exist as real code, not just comments.
- **`memory_write_validator.py`** `[VERIFIED]` — `_get_validator_logger()` still
  has the try/except → `NullHandler` fallback from Finding 27's fix.
- **FAISS dual-index** `[VERIFIED]` — `memory/memory_meta.json`: 69,053 vectors
  (grown from the 41,299 recorded 2026-07-13, consistent with continuous
  autonomous writing). `data/memory_meta.json`: 5,348 vectors, `data/` file
  mtimes still May 15 — genuinely untouched, as documented.

**Nothing drifted.** Every one of these was a real risk of staleness (recently
changed code, multiple sessions touching the same file) and every one held.

---

## Phase 2 — Real gaps

### Confirmed still open, no change
- **Pending #9** (`reflection_shard.py` not in `EDIT_FORBIDDEN_TARGETS`) —
  confirmed still open, no code change since 2026-07-19.
- **Pending #10** (RiverBrain calibration scaling, blocked on the MLX crash) —
  see the new finding directly below; this pending item's blocking condition
  just got measurably worse, which is relevant to how it gets decided.

### New finding: Finding 49's crash count is a real, substantial undercount — not a documentation nit, an active reliability problem

`~/Library/Logs/DiagnosticReports/` has **9 crash reports with the identical
`mlx::core::gpu::check_error` → `libc++abi` → `SIGABRT` signature** Finding 49
describes, spanning **2026-07-17 23:06 through 2026-07-20 22:48 — about 71.5
hours, not "about 21 hours."** Finding 49 as currently written accounts for
3 of these (the two 07-17 23:06/23:08 crashes plus "a third occurrence" on
07-20). The other 6 — 07-19 09:15, 07-19 21:20, 07-19 22:56, 07-19 23:26,
07-20 11:35, and critically **two crashes at 07-20 22:44 and 22:48, which
happened after CLAUDE.md's own last edit (11:42:33 that same day)** — are not
reflected anywhere in the document. `[VERIFIED]`, direct read of all 9 `.ips`
files' embedded JSON (`exception.type`, `termination.indicator`, and the
crashing thread's top frames all cross-checked, not just filename-grepped).

This changes the shape of the finding, not just the count: Finding 49's own
"Correction, same day" already revised the theory from "sustained batch load
trigger" to "any real request with an MLX councillor carries some risk" — the
fuller count here is consistent with that revision and makes it stronger, not
different. But three occurrences in 21 hours reads like an emerging pattern;
nine in three days, including two back-to-back roughly 35 minutes before this
audit started, reads like an active, ongoing, unresolved reliability problem
directly relevant to Pending #10's blocking condition. Recommend folding this
count into Finding 49 (or a new dated correction) rather than leaving the
"three... 21 hours" framing in place — the qualitative read doesn't need to
change, but "9 crashes over 3 days, 2 of them after this doc's own last edit"
is a materially different picture than "three in one night" for anyone
deciding on Pending #10.

### New finding (smaller, separate root cause): the documented-as-resolved KMP/OpenMP crash recurred once, 2026-07-19, unexplained

One of the 10 `.ips` files in the same window (`python3.12-2026-07-19-135923.ips`,
13:59:23) does **not** match the MLX signature — it's the *other* crash
CLAUDE.md documents, the `__kmp_register_library_startup → __kmp_fatal →
abort()` OpenMP duplicate-library collision the "OpenMP / KMP startup guard"
section describes as fixed by `KMP_DUPLICATE_LIB_OK=TRUE` etc. in `run.py`,
citing two 2026-06-29/06-30 crash reports as the historical evidence for the
fix. `[VERIFIED]` — direct read of the crashed thread's frames confirms the
identical `__kmp_abort_process`/`__kmp_fatal`/`__kmp_register_library_startup`
signature, three weeks after that section describes the issue as closed.
`run.py`'s guard lines (12-20) are confirmed intact and correctly ordered.
The crash is a single occurrence (not a pattern like the MLX one), and
`SELF_EDIT.log` shows the server back to normal `AutonomousSelfEdit` activity
within under a minute (consistent with `start_echo.sh`'s crash-restart
watchdog working as designed) — so this isn't a live outage, just an
unexplained recurrence of something documented as resolved.
`[HYPOTHESIS, not investigated further this session]`: worth checking whether
this happened inside the main server process itself (env vars set) or a
subprocess that doesn't inherit/set them — a targeted grep found the KMP env
vars are **not** set anywhere in `sandbox/safe_exec_wrapper.py` (only in one
throwaway experiment fixture, `sandbox/experiments/test_faiss_atomicity.py`),
so if self-edit's F2 sandbox subprocess ever imports numpy/faiss/torch
without inheriting the parent's env, this is a plausible real gap — not
confirmed as the actual trigger for this specific crash, flagged for a real
investigation rather than asserted.

### Process gap, not a code bug: COUNCIL.md's own stated open question isn't in `PENDING_DECISIONS.md`

`COUNCIL.md` (new, committed in the latest commit, 473 lines) states directly
in its own second paragraph that whether it should be hash-protected the way
`echo_principles.json` is, and whether any of its content is ever surfaced
inside Echo's own source, "is still open... recorded here so it isn't lost
before it's decided." `[VERIFIED]` by direct read. This is exactly the shape
of item `PENDING_DECISIONS.md`'s own stated maintenance convention says
should get a row ("any future session that flags a new 'Gremlin's call' item
... should add a row here in the same change") — and it doesn't have one.
Low-stakes (a documentation/manifesto file, not live code), but it's the
project's own enforcement mechanism missing an item its own source names as
open, which is the exact failure class this project has repeatedly flagged
in other subsystems (self-report vs. ground truth). Recommend a row.

---

## Phase 2.5 — Ghost code / silent-failure sweep

Scoped to files added since the last full sweep (Findings 22/30/41 already
covered the rest): `code_verification.py`, `self_knowledge_verification.py`,
`conversation_activity.py`, `self_edit_outcome_tracker.py`.

**Clean.** All `except` blocks in these four files either re-raise-adjacent
(log with `exc_info`/message) or are narrowly scoped to genuinely benign
cases (malformed JSONL line, unparseable timestamp) — no bare
`except: pass`, no silently-swallowed real failures, no hardcoded/mock
output dressed as live computation. `conversation_activity.py` has no
exception handling at all because it doesn't need any (a plain counter).
This is a real negative result, not a skipped check — worth stating plainly
per this project's own convention of recording clean sweeps, not just
findings.

---

## Phase 3 — Red team

Applied only to the two new items above (nothing else is new enough to
red-team):

- **Crash-count finding**: could the 6 "extra" crashes be a different,
  coincidentally-similar signature rather than genuinely the same bug?
  Checked directly — `exception.type`/`termination.indicator` and the
  crashing thread's `mlx::core::gpu::check_error` frame were compared across
  all 9, not just grepped for a matching substring in isolation. Confidence:
  `[VERIFIED]`, not `[HIGH CONFIDENCE]`.
- **KMP recurrence**: could this be an artifact of a different process (some
  unrelated `python3.12` invocation, not FeralEcho)? Checked `procPath`/
  `parentProc` (`zsh`) and cross-referenced `SELF_EDIT.log` timestamps
  immediately after the crash showing `AutonomousSelfEdit` resuming — real
  evidence this was the FeralEcho server process, not a coincidence.
  Confidence: `[VERIFIED]` that it happened to this project's server;
  `[HYPOTHESIS]` on the sandbox-subprocess-env theory specifically, stated
  as such above, not asserted as root cause.

---

## Summary for `PENDING_DECISIONS.md` / `CLAUDE.md` maintenance

1. Update Finding 49 (or add a dated correction) with the real 9-crash,
   ~71-hour count instead of "three... 21 hours" — materially relevant to
   Pending #10.
2. Add a `PENDING_DECISIONS.md` row for COUNCIL.md's protection-status
   question.
3. (Optional, lower priority) Investigate whether `safe_exec_wrapper.py`'s F2
   subprocess needs its own explicit KMP guard, given the one recurrence
   found this session and the confirmed absence of the guard in that file.

Nothing here required or received a code change — this is a report-only
pass per the differential audit's own scope.
