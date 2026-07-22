# Pending Decisions

A live tracker for open items that are specifically **awaiting Gremlin's
own call** — not bugs to fix, not open technical investigations, but
places where this project's own established discipline (report the
finding, propose options, don't default into an answer by momentum) means
a session stopped short of deciding for him. Everything here has full
detail in CLAUDE.md under the Finding number listed; this file exists only
so the list of "still open" items is scannable in one place instead of
buried across 37+ Findings in a document that keeps growing.

**This file only tracks things awaiting a decision.** For the *standing*
categories that always require confirmation regardless of specifics
(restoring from a snapshot, changing `EDIT_FORBIDDEN_TARGETS`, reactivating
the wolf friction bridge, loosening the peer-model council constraint,
etc.), see GREMLIN_ROLE.md's "What Requires Human Confirmation" section —
those don't need a row here since they're not open questions, they're
permanent rules.

**Maintenance convention**: any future session that flags a new
"Gremlin's call" item in CLAUDE.md should add a row here in the same
change — this is the enforcement mechanism for that habit, the same way
the Liveness Ledger is the enforcement mechanism for "self-report must
match ground truth." When an item is resolved, remove its row; the
resolution itself stays recorded in CLAUDE.md's Finding history and git,
so it doesn't need to be duplicated here.

| # | Item | What's being decided | Options on the table | Detail |
|---|---|---|---|---|
| 2 | Phone symbiote client (`thunderhead.py` / `feral_echo_symbiote.py`) sends no working secret to `/learning_event`/`/learning_batch` — **sharpened 2026-07-18 (Finding 42)**: the real phone script has no `THUNDERHEAD_SECRET` concept at all, not an unfilled placeholder as originally thought. **Decided 2026-07-22**: Gremlin will check the actual phone-side script himself to confirm whether `send_event()`/`flush_bundle()` have the secret wired in (same phone-side edit as `mirror_echo()`, which is already confirmed working) | Awaiting Gremlin's own direct look at the phone script — not a design decision, a confirmation task only he can do | N/A — nothing to build, just needs his confirmation | CLAUDE.md Finding 36, 42 |
| 16 | Now that `baseline_trusted_since` is genuinely set for the first time (Finding 66), `_collect_health()` correctly starts computing real `drift_alerts_active` values in snapshot manifests — but `check_and_alert()`'s actual restore-alert loop was never wired to check `drift_alerts_active`/`weekly_delta` at all, regardless of trust state. `snapshot_manager.py`'s own module docstring implies trust-flag-set should activate these as real alert triggers; it doesn't, and never did | Whether/how to wire `drift_alerts_active`/`weekly_delta` into `check_and_alert()`'s real alert loop now that genuinely-trusted drift data exists to alert on | Not evaluated yet — could mirror the existing `ram_sustained_92pct`-style sustain-then-alert shape, or something more conservative given this would be the first drift-based (not just resource-based) restore alert this project has ever had live | CLAUDE.md Finding 66 |

---

*Last swept 2026-07-21 (differential audit, later updated same day). Item #9 (`reflection_shard.py` protection) closed the same session — `app/subsystems/reflection_shard.py` is now in `EDIT_FORBIDDEN_TARGETS`; see CLAUDE.md Finding 50. Item #8 (`echo_janitor.py`/log retention) closed later the same day — see CLAUDE.md Finding 51. Item #1 (`/mirror_echo` auth) closed later still — see CLAUDE.md Finding 55. Item #12 (council review of janitor's flag-only candidates) closed later still, the same day it was added — built as designed, per Gremlin's direct approval; see CLAUDE.md Finding 63. If this file and CLAUDE.md ever disagree about whether something is still open, CLAUDE.md's Finding history is the source of truth — re-verify against current code before trusting either.*

*Second sweep, 2026-07-21/22: a full live ground-truth re-verification (not just re-reading this file's text) of every open item found item #4's cited figures partially stale (rated count 79→116; a new, undocumented fact — the human spot-check pipeline has been stalled 8+ days) and added three rows (#13, #14, #15) for "Gremlin's call" items that were named in CLAUDE.md Findings 3/45/57 but never got a row here, despite this file's own maintenance convention requiring one. Everything else checked out exactly as documented — no other item here had silently drifted in either direction. This sweep was prompted directly by Gremlin questioning whether a findings list this size could really all still be accurate, which turned out to be a well-founded doubt.*

*Decision session, 2026-07-22: every open row was put to Gremlin directly, in batched rounds rather than all at once. Four items were decided with nothing left to build and their rows removed: #5 (watchdog hang-detection — skip for now, matching his own prior low-urgency read), #6 (credential rotation — don't rotate), #14 (Ollama concurrency/preemption — leave as-is), #15 (valence circuit-breaker — stay observational). Five items were decided but still need real implementation, so their rows stay (updated in place, not removed) until built: #4 (wire the council/quality blend into River training), #7 (move `apply_to_code` into the F2 sandbox), #11 (two of its three sub-questions need building — hash protection, partial surfacing to Echo), #13 (auto-trigger `mark_baseline_trusted()`), and #2 (not a design decision, just awaiting Gremlin's own direct look at the phone script).*

*Note (2026-07-19): the Echo self-awareness forensic audit (CLAUDE.md Finding 43) flagged two items for a decision — a confabulation-mitigation prompt nudge, and pausing `prose_stripping` from self-edit's targeting rotation. Both were decided and implemented the same session (approved directly, not defaulted into), so neither got a row here — nothing about them is still open.*

*Build session, 2026-07-22: item #13 built and closed — `mark_baseline_trusted()` now has a real auto-trigger, mirroring `council_rater.py`'s proven pattern exactly, verified against real data (all 5 PageHinkley detectors at ~5,120 observations each) plus two synthetic fail-closed cases; `baseline_trusted_since` is genuinely set in `memory/snapshot_baseline.json` for the first time in this project's history. See CLAUDE.md Finding 66. Verifying this surfaced a real, previously-undocumented gap, added here as a new row (#16): the trust flag's one other real consumer, `_collect_health()`'s `drift_alerts_active` field, now computes for real — but `check_and_alert()`'s actual restore-alert loop was never wired to act on it, despite `snapshot_manager.py`'s own docstring implying it would be once trust was set. Not assumed into #13's scope; tracked separately.*

*Same build session, item #4 built and closed — the approved 30%/70% council-rating/quality_score blend now feeds RiverBrain training via a new `learn_from_council_rating()` method, called from `council_rater.py`'s `rate_one_entry()` gated on the pre-existing `is_council_trusted()`. Verified against real live RiverBrain data (five real cases: normal blend, missing quality_score, malformed quality_score, unknown task_type, RIVER_AVAILABLE=False — all correct, `.save()` never called so production `river_brain.pkl` was untouched by verification). New 25th Liveness Ledger check, `council_river_blend`, guards both the blend math/approved ratio and the trust gate itself. See CLAUDE.md Finding 67.*

*Same build session, item #11 built and closed — both remaining sub-items shipped. `COUNCIL.md` now has hash-verified startup protection identical in shape to `echo_principles.json`'s (verified with a real `take_snapshot()` call, not just read — the new artifacts were correctly captured with matching sha256, retention held at 5). A new `"council"` slice in `echo_ground_truth.py` surfaces existence + live-computed structural counts only (2 rounds, 9 responses, as of this change) — never the actual recorded reactions, matching the file's own explicit "stays private, full stop" decision. New 26th Liveness Ledger check, `council_content_privacy`, specifically guards against a future edit ever leaking real quoted content into that slice. See CLAUDE.md Finding 68.*

*Same build session, item #7 built and closed — the last of the four Lane A items. `apply_to_code`'s real invocation now runs inside the actual F2 kernel-sandboxed subprocess (new `--mode=apply_to_code` in `safe_exec_wrapper.py`, new `_run_apply_to_code_sandboxed()` in `self_edit_manager.py`) instead of the in-process `ThreadPoolExecutor` Finding 41 B3 found couldn't be forcibly killed on timeout. Verified against five real fixture hooks — a hanging hook was genuinely killed at 2.01s (not left running to completion), a write-attempting hook was blocked with the target file confirmed never created, plus a normal transform, a raising hook, and a bad-signature hook, all handled correctly; no regression in the pre-existing `--mode=import` staging path. New 27th Liveness Ledger check, `apply_to_code_sandbox_isolation`, statically guards against a future edit silently reverting to the removed in-process pattern. See CLAUDE.md Finding 69. **All four Lane A build items are now closed.**
