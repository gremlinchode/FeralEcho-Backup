# Shadow Retirement — Permanent Documentation Follow-Up

**Date:** 2026-09-13
**Type:** Documentation-only follow-up mission (not a research or implementation mission)
**Status:** Complete. One documentation change made. No commit made.

---

## 1. Decision

**A — Documentation was warranted. One entry added to `CLAUDE.md`.**

---

## 2. Documentation archaeology

**Existing retirement conventions found**, via direct grep of `CLAUDE.md` for `self_heal.py`, `INTENTIONALLY DISCONNECTED`, `ARCHIVED`, `retired`, `deprecated`, and related terms (not assumed from memory of an earlier read this session — re-confirmed fresh):

- **The direct precedent, `app/core/self_heal.py`** (CLAUDE.md's "Health Monitoring" section): *"FIXED, INTENTIONALLY DISCONNECTED. Not imported anywhere; has no live caller. Fixed two stale-assumption bugs (wrong `append_to_journal` signature, wrong FAISS index path). Kept disconnected deliberately; reconnecting requires explicit human decision and review."* This establishes the project's actual convention for a retired-but-preserved mechanism: a single bolded-name bullet, present-tense status label in caps, the reason, and an explicit revival condition — not a narrative retelling of the investigation that led there.
- **A second, structurally similar precedent**: WOLF/`alignment_kernel.py`, described as "fully dead," with its own explicit retirement note quoted directly from `run.py`'s own top-of-file comment, and endpoints that "now both return `{"status": "disabled", "detail": "WOLF was retired 2026-07-04"}"` — a heavier case (endpoints, not just a function) but confirming the same underlying discipline: state the retirement plainly, cite where the mechanism/evidence lives, do not silently delete the old description.
- **CLAUDE.md's own stated discipline on correcting itself**: multiple "Correction (date, Finding N): ..." annotations throughout the file, appended after a stale or wrong claim rather than silently editing it out of existence. This project does not rewrite its own history — it appends.

**What was found to be the actually load-bearing, currently-stale reference**: `CLAUDE.md`'s "Machine-Native Awareness" section already contains a standing, present-tense bullet for `app/core/shadow_model.py` — *"tracks whether Echo's self-assessments match actual outcomes"* — sitting in a flat list alongside `echo_state.py`, `curiosity_engine.py`, `garden_manager.py`, `task_type_classifier.py`, `system_guard.py`, and others. This is the line a future Claude Code session would most plausibly land on when greping `CLAUDE.md` for `shadow_model.py`'s status, and as of the retirement mission it is actively wrong — it describes Shadow as a live, functioning tracking mechanism with no indication it has been disconnected.

**A separate, historical reference was found and deliberately left untouched**: Finding 91 item 3 (further down `CLAUDE.md`) narrates the 2026-09-05 priority-order fix and states *"the shadow model's suggestion survives only as a last-resort fallback... not a decision to retire the shadow-model mechanism."* This sentence was true when written — that mission genuinely did not retire Shadow, it only reordered a priority check. A later, separate mission (the retirement mission preceding this one) made a different decision that superseded that state. Per `CLAUDE.md`'s own established convention (a Finding narrates what was true and decided *at the time*; a later Finding records what changed, rather than editing an earlier one that was accurate when written), this is not a factual error requiring a correction annotation — it is superseded history, exactly the shape this project's Findings ledger is built to hold without rewriting itself. Left as-is.

**Why `CLAUDE.md` is the appropriate place**: it is this project's single, actively-maintained, session-to-session institutional memory file — exactly where `self_heal.py`'s own retirement lives, and exactly the file a future Claude Code session is instructed to consult first. No competing or more appropriate location was found; the retirement report itself (`audits/2026-09-13_shadow_model_retirement.md`) is the detailed record, `CLAUDE.md` is the durable index pointing to it — matching the existing relationship between `self_heal.py`'s one-line entry and its own (more scattered, less centralized) supporting history elsewhere in the file.

---

## 3. Change

**File changed:** `CLAUDE.md`, one location, one bullet, in the "Machine-Native Awareness" section (immediately following the `task_type_classifier.py` entry, immediately preceding `system_guard.py`).

**Before:**
> `- **app/core/shadow_model.py** — tracks whether Echo's self-assessments match actual outcomes`

**After:**
> `- **app/core/shadow_model.py** — RETIRED FROM LIVE USE (2026-09-13), INTENTIONALLY DISCONNECTED. Previously tracked whether Echo's self-assessments matched actual outcomes; real measured accuracy (16.1% over 2054 entries, 13.2% over the most recent 500) was below the ~20% a uniform-random guess across 5 task types would get. All three live call sites (emergent_scheduler.py, night_cycle.py, self_edit_manager.py's perform_self_edit() fallback) were removed; the implementation itself was not deleted or repaired — same posture as self_heal.py's existing disconnection (see Health Monitoring section below). Revival requires a dedicated investigation into whether the below-chance result is a diagnosable defect, not a default action. See audits/2026-09-13_shadow_model_retirement.md.`

This is the single documentation change made by this mission. Nothing else in `CLAUDE.md` was touched.

---

## 4. Scope verification

This mission did **not** modify:
- `app/core/shadow_model.py` (implementation) — confirmed via `git status --short`, no change relative to the prior mission's end state.
- `app/core/self_edit_manager.py`, `app/maintenance/night_cycle.py`, `app/emergent_scheduler.py` (Shadow's former consumers) — confirmed via the same check; all three show as modified only from the *prior* retirement mission, which this mission preserved unchanged and did not touch further.
- Council, in any form.
- The evidence taxonomy work from earlier in this session.
- The capability benchmark harness or any part of it.
- Q-001/Mechanism-B/the second-model cross-check.
- Any unrelated source code, script, or documentation file.

No Shadow consumer was restored. No investigation into the below-chance cause was performed or implied. No redesign of Shadow was proposed or implied.

---

## 5. Git state

| | |
|---|---|
| Starting Git HEAD | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` |
| Ending Git HEAD | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` |
| HEAD changed | No |
| Files changed by this mission | `CLAUDE.md` (1 line modified) |
| Anything staged | No — `git diff --cached --stat` is empty |
| Anything committed | No |
| Pre-existing working-tree changes (from earlier missions this session) | Preserved untouched — verified directly before and after this mission's edit |

---

## 6. Final architectural statement

> Shadow remains preserved as a historical/research artifact and is intentionally disconnected from all live production consumers. Its below-chance behavior remains an unresolved research question requiring a dedicated future investigation before any revival.

This statement is accurate as of this mission's completion, confirmed by: the retirement mission's own verified invariant (zero live consumers, established at three independent layers — static, AST, runtime), this mission's confirmation that none of the four affected files were touched again, and the new `CLAUDE.md` entry now making that state discoverable without requiring a future session to already know the retirement report exists.
