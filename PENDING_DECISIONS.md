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
| 1 | `/mirror_echo` has no authentication | Gate it like every sibling endpoint, or confirm it's intentionally open the way `/message/send` was | (a) Add the existing `_secret_ok()` check, same pattern as `/nuke`/`/admin/*`/`/learning_*`; (b) explicitly confirm it should stay open and fix the doc/comment to say so, not just leave it unstated | CLAUDE.md Finding 36 |
| 2 | Phone symbiote client (`thunderhead.py` / `feral_echo_symbiote.py`) sends no working secret to `/learning_event`/`/learning_batch` | Not really an "options" decision — a real value needs to be pasted into `THUNDERHEAD_SECRET` in whichever copy actually runs on the phone | Copy the real `GREMLIN_SECRET` value from `.env` into the **phone-only** copy of the script — never into the tracked `thunderhead.py`, which must keep the empty placeholder to avoid committing the secret | CLAUDE.md Finding 36 |
| 4 | Council rating trust threshold, and what (if anything) to unlock once it's reached | Currently 0.643 agreement (needs ≥0.70), 79 rated (needs 50 — already past), pending spot-checks still open — **not yet reached**, but the "what happens when it is" decision has never been made and shouldn't be defaulted into the moment the number crosses the line | Proposed (not approved): 30% council / 70% quality_score blending into River training signal. Needs explicit review whenever the threshold is actually met, per GREMLIN_ROLE.md — do not wire this in by momentum | CLAUDE.md's Council Peer Rating section |
| 5 | `start_echo.sh`'s watchdog only detects the process *exiting* (crash), not *hanging* (alive but stuck, never reaching `serving`) — confirmed real 2026-07-17, one incident, not an established pattern | Low urgency by Gremlin's own read: the specific trigger (a coincident DNS resolution quirk) probably won't recur, though the general shape of the gap (crash-detection without hang-detection) is a little broader than that one cause. Not decided whether it's worth building for. | Sketched, not built: poll `echo_sentinel.json` while the child process runs; if `stage != "serving"` for longer than startup should ever reasonably take (~180s), kill and let the existing restart loop take over. No diff written yet — sit with it first. | CLAUDE.md Finding 40 |

---

*Last swept 2026-07-16. If this file and CLAUDE.md ever disagree about whether something is still open, CLAUDE.md's Finding history is the source of truth — re-verify against current code before trusting either.*
