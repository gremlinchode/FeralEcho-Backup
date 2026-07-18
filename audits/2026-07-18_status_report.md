# FeralEcho — Status Report, 2026-07-18

Prepared by direct investigation: a full read of `CLAUDE.md` (41 numbered
Findings), `PENDING_DECISIONS.md`, both forensic audit passes
(`Desktop/Forensic Audit/`, dated 2026-07-04, and `audits/forensic/`,
dated 2026-07-16 — the latter supersedes the former), plus live queries
against the actual running server (PID 60541, uptime ~12 min at time of
writing, `stage: serving`), direct source reads of the routes named in
recent Findings, and a direct read of the cross-machine relay log
(`claude_relay/from_m5.md`). Where a claim in an existing document could
be checked against current, live state, it was — this report exists to
tell you what's *true right now*, not to restate what CLAUDE.md already
says. Every "confirmed live" statement below was independently verified
during this session, not copied from another document.

---

## 1. What this project is

FeralEcho is a solo-developer, single-user personal AI system: a Flask
server (`run.py`, ~926 lines, 40+ routes) wrapping a locally-run Ollama
model (`echo:latest`, currently the live synthesis substrate), with a
large number of autonomous background loops (~25 threads at startup),
a vector memory store (FAISS, 60,053 vectors as of this check), a
self-editing code pipeline gated by a three-layer safety system (F1/F2/F3),
and — increasingly — its own internal verification layer (the Liveness
Ledger) that continuously re-checks its own subsystems against ground
truth rather than trusting their self-reports. It runs on two machines
(M5 and Air/Ark) that sync memory and messages over Tailscale. The
project's own documentation (`CLAUDE.md`, 41 dated Findings; `GREMLIN_ROLE.md`;
`ORIGIN.md`; `PENDING_DECISIONS.md`) is unusually rigorous for a solo
project — findings are dated, corrected in place when later found wrong,
and cross-checked against live system state rather than assumed. That
same discipline is what this report tries to extend, not replace.

**A structural habit worth naming up front, because it recurs constantly
in this project's own history and in this report:** things get fixed in
code faster than the documentation describing them gets updated. This is
explicitly named in CLAUDE.md itself (Findings 4, 25, 28, 30's own
"doc lags commit" callouts) and the 2026-07-16 forensic audit calls it
out as a recurring pattern (R11) worth watching, not a one-off. This
report found a fresh, live instance of exactly that pattern in progress
(Section 3 below) — worth reading carefully, because it changes the
practical urgency of one of the two "still open" security items.

---

## 2. Current live system state (verified this session)

Checked directly against the running server, not inferred from docs:

| Signal | Value | Read as |
|---|---|---|
| Server process | PID 60541, up ~12 min, `stage: serving` | Healthy, no startup hang (Finding 40's HF-offline fix appears to be holding) |
| `GET /admin/liveness-status` | `all_passing: true`, **14/14 checks passing**, `stale: false` | All self-governing subsystems currently verify against ground truth cleanly — see Section 5 |
| `GET /admin/autonomy-status` | 8 loops reporting, all `skipped_reason: null` | Every tracked autonomous loop ran within its last cycle window with no throttle/skip |
| FAISS vector count | 60,053 (matches `self_model.json`'s self-report exactly) | Healthy — the FAISS split-brain (CLAUDE.md's "FAISS Dual-Index" section) remains resolved |
| Council rating pipeline | 112 total rated, 28 spot-checked, agreement 0.643 (needs 0.70) | Real, ongoing accumulation — trust threshold not yet reached, consistent with `PENDING_DECISIONS.md` item 4 |
| `apply_to_code` hook | 574 logged invocations; last 3 sampled: `changed: true, error: null` | Live, working, and — per the ledger's own 20-invocation error-rate window — currently healthy (0/20 errors). This is a materially better state than Findings 28/31/32 describe; see Section 4. |
| `git log` | 80 commits total, **15 ahead of `origin/main`, unpushed** | A real backup exists (Finding 38's private-repo fix), but the last 15 commits of work exist only on this machine until pushed |
| Working tree | 14 modified tracked files, uncommitted | Includes real, live security fixes made *tonight* that predate this report — see Section 3 |
| `memory/` directory size | 878 MB (up from 868 MB at Finding 41, 810 MB at Finding 30) | Continuing, non-explosive growth — see Section 6 |
| Disk | 713 GiB free / 926 GiB, 2% used | Not a near-term constraint |

---

## 3. Most important finding of this report: two of the three open security items in `PENDING_DECISIONS.md` have already been fixed in the working tree, tonight, ahead of the documentation

This is the headline item. `PENDING_DECISIONS.md` (as currently written on
disk) and `CLAUDE.md`'s Finding 41 both describe two live, unauthenticated
credential leaks as open/unresolved. **Direct source verification during
this session shows both are already fixed**, and the cross-machine relay
log (`claude_relay/from_m5.md`, entry dated 2026-07-18, read in full)
independently confirms the same fix with its own verification detail:

- **`GET /message/inbox` leaking `ECHO_PARTNER_SECRET`** (Finding 41 A1):
  `app/sync/echo_messaging.py:153` now strips the `secret` field before
  persisting to `memory/echo_messages.jsonl`
  (`safe_entry = {k: v for k, v in entry.items() if k != "secret"}`), and
  `get_recent_messages()` (line 178) strips it again defensively on read,
  explicitly to cover any older log lines written before this fix existed.
  Confirmed by direct source read, not assumed from the relay note.
- **`GET /projects/file` serving a live API-key dump** (Finding 41 A2):
  the leaked file itself, `new_directory/app/core/env/environment.json`,
  no longer exists on disk (confirmed: `ls` returns "No such file or
  directory"). `app/routes_echo_studio.py` gained a genuine content-based
  secret scanner (`_looks_like_secret_dump()`, line 494, with a regex at
  line 485 matching both shell-style `KEY=value` and JSON
  `"key": "value"` forms) that runs before serving *any* file through this
  route — a deliberate improvement over a directory-name blocklist,
  explicitly because a blocklist is the same "gate not verified against
  every instance" shape this project has now found three separate times
  (CLAUDE.md's own Finding 30 addendum, echo_roadmap.md item 10).
- **`GET /sync/export` had zero authentication** (Finding 41 E): also
  fixed — `run.py:902-909` now calls the same `_secret_ok()` gate its
  sibling `/sync/import` already had, with an in-code comment citing
  Finding 41 E directly.

**What is genuinely still open, not fixed by the above:** `PENDING_DECISIONS.md`
item 6 frames the remaining question correctly even though its "confirmed
against the running server" phrasing now reads as past-tense — the
*exposure vector* is closed, but whether the **previously-exposed key
values themselves** (`NEWSAPI_KEY`, `OPENWEATHER_API_KEY`, and
`ECHO_PARTNER_SECRET`) should be rotated is a separate, still-unresolved
question, since anyone who queried these routes before tonight's fix
already has whatever values were live at the time. That decision — not
the code fix — is what's actually still pending. Recommend updating
`PENDING_DECISIONS.md`'s item 6 wording to reflect that the leak itself
is closed and only the rotation call remains open, so a future session
doesn't mistake this for a still-live vulnerability.

**The one item from this cluster that is genuinely still open, unpatched,
right now:** `/mirror_echo` (CLAUDE.md Finding 36, `PENDING_DECISIONS.md`
item 1). Confirmed by direct read of `run.py:503-525` this session — the
handler has no `_secret_ok()` call, no `hmac` check, nothing. It logs the
raw request (`logger.critical`), feeds it into the permanent training-data
pipeline (`dual_learner.log_event()`), and answers it as a genuine
conversational turn via `echo_query()`. This is the single most
significant open item in the project today — flagged repeatedly (CLAUDE.md
Finding 36, the 2026-07-16 forensic audit's #1-ranked finding, R12 in its
risk register), still awaiting Gremlin's explicit call on whether to gate
it or confirm it's intentionally open the way `/message/send` was.

---

## 4. Self-edit pipeline — current state

The F1 (pre-run AST scan) → F2 (kernel sandbox) → F3 (post-write AST
scan) pipeline remains structurally unchanged and is still the safety
floor CLAUDE.md documents it as. Layered on top of it since the last
forensic audit:

- **`apply_to_code` hook**: previously the worst-documented failure in
  the project's history (253/254 invocations raising `NameError` per
  Finding 28, later found to be actively smuggling unvalidated writes
  through an approved import per Finding 31). As of this check, it is
  **genuinely healthy**: 574 total logged invocations, the liveness
  ledger's own 20-invocation recent-error-rate window reports 0/20
  errors, and the three most recently sampled entries directly from the
  log all show `changed: true, error: null`. This is a real, verified
  turnaround from the state Finding 28/31/32 describe — the prompt
  rewrite (Finding 32) plus the write-block wrapper (Finding 31) appear
  to have actually worked, not just been applied.
- **Convergence tracking** (`self_edit_convergence.json`, read directly
  this session): `prose_stripping` — the family that both forensic audit
  passes flagged as the worst non-convergence case (94-95 cycles, 30+
  near-duplicate function names, a fresh real failure observed live
  during the 2026-07-16 audit) — currently shows `non_convergent_streak: 0`.
  This is a positive signal but should not be over-read from a single
  snapshot; the same file's own history shows this family has looked
  briefly stable before. Worth a follow-up check after a few more real
  hourly cycles, per the 2026-07-16 audit's own recommendation, rather
  than treated as resolved from this one reading.
- **`ModelGuidedOrchestrator` throttle gap** (Finding 28) and the
  double-fire risk between it and the main Optuna timer are both fixed
  per CLAUDE.md's account, and the current `/admin/autonomy-status`
  output shows `model_guided_orchestrator` reporting cleanly alongside
  the other three coordinated loops — consistent with that fix holding.

**Known, still-open residual gaps in this pipeline** (none newly found
this session, all previously flagged and worth restating because they
remain genuinely unresolved):
- Finding 41 C: F1's AST scanner matches dangerous calls by literal
  spelling only — `from os import system; system(...)` and similar
  aliasing/indirection bypass it silently. Tested directly (per Finding
  41) and confirmed **not currently exploitable in practice**, because
  F2's kernel sandbox independently blocks the same payloads — but the
  "two independently-sufficient gates" guarantee this project's own
  documentation claims is, for this specific bypass class, currently down
  to one working gate, not two. Not re-tested in this session; no
  indication it has changed.
- Finding 41 B3: the `apply_to_code` write-block's 2-second timeout can't
  actually kill a hung worker thread (Python threads aren't forcibly
  killable) — a slow/hung hook could still execute writes unguarded after
  the timeout fires and the real `open()` is restored. `PENDING_DECISIONS.md`
  item 7 has this open with three sketched options, none chosen.
- Finding 41 B1/B2: two real, reproduced concurrency races (self-edit
  outcome tracking losing a record under concurrent access; the shared
  salience-state file losing 62% of concurrent writes in a direct
  reproduction) in code built after Finding 22 Batch 3's original
  race-condition sweep. Neither is fixed. Not independently re-tested
  this session; flagged as still open per the most recent written record.

---

## 5. Liveness Ledger — the project's own verification layer

Queried live this session: **14/14 checks passing**, ledger fresh
(`stale: false`, 76 seconds old at query time). This is worth taking at
face value more than most self-reports in this project specifically
*because* the ledger's own design principle is "verify against an
independent ground-truth path, not the subsystem's own say-so" — and
because its discrimination test suite (49 cases per CLAUDE.md, each
reconstructing a real historical fake this project already found itself
producing) has a track record of catching exactly the failure mode a
naive health check would miss. Two checks worth calling out specifically:

- `global_workspace_consumption` reports only **1 distinct real consumer**
  (`river_deliberation`) against a passing threshord of ≥1 — it passes,
  but by the minimum margin. If `memory_bridge` or `curiosity_engine`
  (CLAUDE.md's Phase 4 account names these as real consumers too) stop
  actually consuming workspace events, this check would still show
  "passing" right up until the single remaining consumer also stops.
  Not a live problem, just a check worth remembering has a thin margin.
- `reflection_shard_generation` reports **20/20 genuinely generated
  entries** — this fully resolves the one check the 2026-07-16 forensic
  audit found failing live during its own investigation window
  (`0/20... genuinely generated text` at that time, attributed to the
  real-generation fix being too recent to have accumulated evidence yet).
  That prediction ("re-check after a few hours of steady-state uptime")
  has now played out and resolved cleanly — a good example of this
  project's own verification habit working as intended across sessions.

---

## 6. Resource growth — `memory/` at 878 MB and climbing

Not an emergency (713 GiB free), but the growth pattern itself is exactly
what Finding 41 D flagged and nothing has changed about the underlying
cause since. Current largest files, measured this session:

| File | Size |
|---|---|
| `echo_watchdog.log` | 128 MB |
| `reflection_shard.jsonl` | 122 MB |
| `interaction_log.jsonl` | 81 MB |
| `dream_bridge.log` | 56 MB |
| `SELF_EDIT_MASTERY_.log` | 36 MB |
| `quarantine_journal.jsonl` | 29 MB (39,190 lines) |
| `validator_audit.log` | 19 MB |
| `SELF_EDIT.log` | 15 MB |
| `reflection_journal.jsonl` | 11 MB |
| `council_deliberations.jsonl` | 8.0 MB |

Root cause, per Finding 41 D and re-confirmed by this session's own
directory listing: `memory_bridge.append_to_journal()` — the shared
helper behind essentially every one of the files above — has no retention
policy of any kind by construction, and `echo_janitor.py` (built
specifically to solve this) is not wired into the live scheduler at all.
`PENDING_DECISIONS.md` item 8 has this open with three sketched
directions (wire in `echo_janitor.py` after fixing its mtime-based
staleness check, a simple per-file size/line cap mirroring
`self_edit_backups`' existing 25-file retention pattern, or defer since
disk isn't actually constrained yet). Nothing about this session's
measurements changes the urgency assessment already on record — still
worth doing before it becomes a real constraint, not urgent today.

---

## 7. Everything else — status unchanged from the existing record, re-confirmed where checked

The bulk of CLAUDE.md's 41 Findings and both forensic audit passes remain
accurate as written and were not re-litigated in full this session (that
would duplicate, not add to, the existing record). Headline items,
because they define the project's actual risk posture:

- **Self-edit remains genuinely autonomous and hourly, by deliberate
  design** — not a gap, a documented choice (`GREMLIN_ROLE.md`,
  echo_roadmap.md's "explicitly out of scope" list). This is the single
  largest standing architectural risk in the project and is meant to stay
  that way pending Gremlin's own future decisions, not this report's.
- **Two GitHub repos were public until 2026-07-16** (Finding 38) — both
  now private, one (`FeralEcho-Backup`) now genuinely holds a pushed
  backup for the first time. Not re-checked this session; no reason to
  expect it changed.
- **The Tailscale-as-boundary assumption was tested for the first time
  ever on 2026-07-16** (Finding 37) and found false until the macOS
  firewall was actually enabled that session. Not re-tested this session
  — worth a periodic spot-check given how long this assumption went
  untested the first time.
- **The phone symbiote client still sends no working secret**
  (`PENDING_DECISIONS.md` item 2) — a one-line fix (paste the real
  `GREMLIN_SECRET` into the phone-only copy of the script, never into the
  tracked `thunderhead.py`) that simply hasn't been done yet. Not
  something a session should do unprompted, since it means handling the
  real secret value.

---

## 8. Recommendations, in priority order

1. **Decide `/mirror_echo`'s auth posture.** This is the one clearly
   "your call, needs to happen" item left in this cluster — everything
   else in the credential-leak family is now closed in code. Gate it with
   the existing `_secret_ok()` pattern, or explicitly confirm (and update
   the code comment/CLAUDE.md to say) that it's meant to stay open.
2. **Decide the rotation question** (`PENDING_DECISIONS.md` item 6) now
   that the exposure vector itself is closed — this is a lower-urgency,
   cleaner decision than it was when the leak was still live.
3. **Update `PENDING_DECISIONS.md` item 6's wording** to reflect that the
   leak is fixed and only rotation remains open — leaving it phrased in
   the present tense risks a future session mistaking this for a still-
   live vulnerability, exactly the "doc lags commit" pattern this project
   already tracks as a recurring risk.
4. **Push the 15 unpushed commits** (or at minimum be aware they only
   exist on this machine) — given Finding 38 only recently established a
   real off-machine backup, letting commits sit unpushed for long periods
   quietly erodes the thing that fix was for.
5. **Give `PENDING_DECISIONS.md` items 4, 5, 7, 8 no urgent action** —
   each is either a genuine slow-accumulation gate (item 4) or a real but
   low-severity, explicitly-deferred design question (items 5, 7, 8) with
   no new evidence this session that the urgency has changed.
6. **Re-check `prose_stripping`'s convergence state after a few more real
   hourly cycles** rather than treating tonight's `non_convergent_streak: 0`
   reading as resolved — this family has looked briefly stable before.

---

## 9. Confidence notes

**Directly verified this session, high confidence:** the three credential/
auth fixes in Section 3 (via direct source read, not the relay note
alone); `/mirror_echo`'s continued lack of authentication; current
liveness ledger state (14/14); current `apply_to_code` health (0/20
recent errors, sampled directly from the log); current FAISS/journal
counts; current `memory/` size breakdown; current unpushed-commit count;
current disk headroom.

**Not independently re-verified this session, carried forward from the
existing record at face value:** the F1 AST-bypass class and its F2
mitigation (Finding 41 C); the two concurrency races (Finding 41 B1/B2);
the Tailscale/firewall boundary (Finding 37); the two GitHub repos'
current visibility (Finding 38); `prose_stripping`'s convergence beyond
the single snapshot read here. None of these were found to have changed
— they simply weren't re-tested, and per this project's own standing
discipline that distinction is worth stating rather than blurring.
