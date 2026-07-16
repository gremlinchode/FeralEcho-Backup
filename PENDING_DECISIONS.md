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
| 3 | ClaudeShard's identity string/name implies a live Claude call; there isn't one | Not a two-option decision any more — just needs the real origin and real behavior documented accurately, everywhere it surfaces (including inside Echo's own self-model) | Origin confirmed with Gremlin 2026-07-16: ClaudeShard is Claude's own answer, given via chat, to "what piece of yourself would you put into Echo" — a permanent structural friction/humility trait, not a placeholder for an unfinished API integration. Wiring a live call in would trade away what was actually asked for, not complete it. Document: (a) the real origin, (b) that it's a genuine multi-signal heuristic with three real downstream consequences (`echo_state.py` dim[5], the Wolf Friction Bridge dry-run trigger, direct memory injection via `/mirror_echo`) — not "just" a coin flip, only the "live call" half of its name is inaccurate | CLAUDE.md's ClaudeShard description |
| 4 | Council rating trust threshold, and what (if anything) to unlock once it's reached | Currently 0.643 agreement (needs ≥0.70), 79 rated (needs 50 — already past), pending spot-checks still open — **not yet reached**, but the "what happens when it is" decision has never been made and shouldn't be defaulted into the moment the number crosses the line | Proposed (not approved): 30% council / 70% quality_score blending into River training signal. Needs explicit review whenever the threshold is actually met, per GREMLIN_ROLE.md — do not wire this in by momentum | CLAUDE.md's Council Peer Rating section |
| 5 | Declared model specialty tags (`detect_model_tags()`) are never read by council selection — verified live: the actual coding specialist (`qwen2.5-coder:7b`) has 16 lifetime coding observations vs. two untagged-for-coding models at 4,200+ each | Whether to give tagged models a scoring nudge toward their declared specialty, and if so how large | Proposed (not approved): a small, tag-conditional boost mirroring `ECHO_SCORE_BOOST`'s existing shape — preserves competition, doesn't hard-filter eligibility. Touches `river_deliberation.py`'s live selection logic; needs a shown diff before landing, per GREMLIN_ROLE.md | CLAUDE.md Finding 39 |

---

*Last swept 2026-07-16. If this file and CLAUDE.md ever disagree about whether something is still open, CLAUDE.md's Finding history is the source of truth — re-verify against current code before trusting either.*
