# Phase 4: Dead Weight & Artifact Inventory (raw notes)

Method: git ls-files + du -sh per candidate + grep for live .py references + git log spot-checks.
CAUTION (per this project's own established norm, independently corroborating the protocol's own
"Preserve Research Intent" directive): several large "zero live code reference" artifacts in this
specific codebase have historically turned out to be intentional, autonomously-generated, or
otherwise meaningful (a fact the codebase's own tooling -- echo_janitor.py -- explicitly guards
against by never auto-deleting, only ever flagging or moving to an archive dir). This audit
follows the same discipline: DELETE is recommended only for items with strong, multi-signal
evidence of being pure duplication/build-artifact noise; anything content-bearing or plausibly
autonomously-generated is recommended ARCHIVE or FLAG, not DELETE.

## Category A: git-tracked pre-gitignore snapshot/backup sprawl (HIGH CONFIDENCE: safe to remove
   from git tracking; genuinely mechanical, timestamped, duplicate-shaped output)
1. sandbox/scripts/archive/*  -- 1167 files, 4.6MB. Filenames: temp_self_edit(.py|_retry.py)
   .<YYYYMMDDHHMMSS>, dated 2026-06-21 through 2026-06-28. .gitignore already lists
   "sandbox/scripts/archive/" (confirmed present in .gitignore) but this only blocks FUTURE
   additions -- git does not retroactively untrack already-committed files. [VERIFIED both facts
   independently: file count/dates via git ls-files, gitignore rule via direct file read]
2. app/core/self_edit_plans/* -- 500 files, 2.0MB, plan_<YYYYMMDDHHMMSS>.txt, all dated in a
   2026-06-25 cluster at the head of a sorted listing. .gitignore already lists
   "app/core/self_edit_plans/" -- same already-tracked-before-ignore-rule situation. Exactly 500
   files present suggests a real prune-to-N-files cap exists somewhere in the live pipeline
   (self_edit_manager.py) that keeps the ON-DISK directory bounded going forward, but git's own
   historical tracking of the pre-cap backlog is untouched by that runtime behavior.
   [VERIFIED file count/pattern; the existence of a live prune mechanism is inferred from the
   suspiciously-exact 500 count, not independently confirmed by reading the prune function itself
   in this pass -- HYPOTHESIS on the *mechanism*, VERIFIED on the *file count fact*.]
3. app/core/app/core/self_edit_backups/ + app/core/app/core/self_edit_plans/ -- a nested,
   duplicate-path artifact (6 files total, small), dated 2025-11-16 -- OLDER than this repo's
   entire visible git history (starts 2026-06-28), meaning this broken nested structure was
   already present in the very first commit. [VERIFIED] This is direct, first-party evidence of
   a real historical bug: self_edit_manager.py's write-target path constants were, at some past
   point, relative rather than __file__-anchored, so running the self-edit pipeline from a cwd of
   app/core/ (or similar) caused it to recreate its own directory scaffold one level inside
   itself. The CURRENT source (self_edit_manager.py, read in Phase 1/2) anchors these constants
   via `_PROJECT_ROOT` derived from `__file__` -- so this specific bug class appears fixed in
   present-day code, but its historical wreckage (this nested directory) is still git-tracked.

RECOMMENDATION for Category A: `git rm -r --cached` (untrack, keep on disk if desired, or delete
entirely) for all three -- these are mechanical timestamped duplicates/generated snapshots with
no unique research or narrative content beyond "many similar temp-file attempts happened here",
which is already summarized adequately elsewhere. Confidence: HIGH. Space reclaimed: ~6.6MB from
git's working tree; more from history if a history rewrite is ever done (not recommended lightly
-- rewriting shared git history has its own real risks, flagged separately in the roadmap).

## Category B: root-level generated data/debug dumps with ZERO live .py references (MEDIUM-HIGH
   CONFIDENCE dead, but some ambiguity -- recommend ARCHIVE not DELETE given this project's
   history of superficially-orphaned files turning out to matter)
- lattice_log.json (12.7MB) -- zero references in any live .py file (grep-confirmed). [VERIFIED
  no reference; NOT independently confirmed what originally wrote it or whether it has narrative/
  research value -- content not deeply read in this pass given its size]
- feral_echo_symbolic_map.json (932KB) -- zero references; a DIFFERENT, similarly-named
  `feral_echo_symbolic_map.py` (a .py file) is separately referenced in echo_janitor.py's own
  known-clutter detection list -- meaning the .json data file and the .py-named clutter-detection
  entry are two different things, and the .json is orphaned. [VERIFIED]
- feral_echo_report_index.json (916KB) -- zero references anywhere. [VERIFIED]
- imports.txt (1.2MB) -- zero references anywhere; also independently a candidate the codebase's
  own echo_janitor.py flags for review (its `_read_content_preview()` council-review feature was
  seen operating against this exact file per other Findings text -- NOT independently re-verified
  live in this pass, noted for completeness only as HYPOTHESIS). [VERIFIED zero code references]
- project_learner_output.txt (764KB) -- zero references; ALSO listed in .gitignore (confirming
  it's meant to be build/debug output, tracked only because it predates that ignore rule --
  same already-tracked-before-ignored pattern as Category A). [VERIFIED]
- bible_structured.json (4.5MB) + bible_structured.json.save (170KB) + bible_queue.jsonl (5MB) +
  books/ (66 files, 4.7MB Bible-book JSON data) -- zero references found in any live .py file via
  targeted grep (`bible_structured`, `bible_queue`, `books/`). Only `bible_sentiment.json` (7.7MB,
  a DIFFERENT root-level file) is confirmed genuinely loaded, by app/core/bible_injection.py
  (a protected EDIT_FORBIDDEN_TARGETS file) at import time. [VERIFIED via direct read of
  bible_injection.py's own load logic] This suggests bible_structured.json/books/ were an earlier
  or parallel data representation that the live scripture-injection code no longer consumes --
  ~9.5MB of apparently-superseded Bible data sitting alongside the ~7.7MB that IS live.
  CONFIDENCE: MEDIUM -- did not exhaustively grep every file in the repo (e.g. sandbox/ archive
  content, which is excluded from source scanning by design) for a reference to these files, so
  a low-probability miss is possible; also did not confirm whether any one-time ingestion script
  (e.g. archive_optional_files/ingest_bible.py, split_bible.py, send_bible_to_echo.py -- all
  present per earlier directory listing) originally produced these files from the live one, which
  would make them a real historical build artifact worth keeping as provenance, not noise.

RECOMMENDATION for Category B: ARCHIVE (move to a clearly-labeled `archive/legacy_data/` or
similar, remove from the hot working tree, keep in one place) rather than delete outright, given
the ambiguity above and this project's own repeated real-world experience of superficially-
orphaned files turning out to be meaningful. Confidence: MEDIUM-HIGH that they're inactive;
LOW-MEDIUM confidence that they're safe to permanently discard without a human first confirming
they aren't wanted as historical/research record. Potential space reclaimed if archived out of
the hot tree: ~25MB.

## Category C: confirmed LIVE, do not touch
- bible_sentiment.json (7.7MB) -- loaded by bible_injection.py (protected file). KEEP.
- WhisperOfPeace.wav (21MB) -- zero live .py references found (grep-confirmed, including a
  case-insensitive re-check). [VERIFIED no current code reference] HOWEVER: per this project's
  own established pattern (its own janitor tooling explicitly treats exactly this kind of file
  -- large, autonomously-named, zero-code-reference, binary/media -- as a known false-positive
  trap for naive "safe to delete" heuristics, and keeps a standing caution about it) this audit
  explicitly does NOT recommend deletion or even archival without a human confirming its
  provenance and intent first. FLAG, do not touch. Confidence in "don't touch" recommendation:
  HIGH, specifically because of this project's own documented history with this exact file
  pattern, not because content was independently verified as meaningful in this pass.
- echo_principles.json, Modelfile, run.py, and the rest of EDIT_FORBIDDEN_TARGETS -- all
  confirmed live/protected via direct source read (Phase 1/2). KEEP, obviously.

## Category D: confirmed structurally-orphaned Python modules (real code, zero live callers)
See Phase 2 notes for full detail. Summary table:
| File | Size class | Nature | Confidence |
|---|---|---|---|
| app/core/council_registry.py | small | superseded singleton-registry class | HIGH orphan |
| app/core/load_project_map.py | small | real function, never wired to anything live | HIGH orphan, real capability gap not just dead code |
| app/core/memory_migration.py | medium | one-time data-migration script, has __main__ | HIGH orphan-by-design (kept for reference) |
| app/core/scheduler.py | medium | sound, documented, "opt-in", never adopted | HIGH orphan, genuinely reusable infrastructure |
| app/core/self_report_verifier.py | medium | deliberately retired-in-place (comments confirm) | HIGH orphan-by-design |
| app/core/self_heal.py | medium | deliberately disconnected; has a live "is this reconnected yet" self-check elsewhere | HIGH orphan-by-design, self-aware |
| app/core/shard.py | tiny | generic base class, superseded by app/subsystems/reflection_shard.py | HIGH orphan |
| app/core/temp_self_edit.py | tiny (7 lines) | stray data-only artifact in the wrong directory | MEDIUM -- flag, low removal risk but unclear provenance |
| app/emergent_scheduler.py: schedule_task()/run_pending() | function-level, not file-level | literal hollow print()-and-return-None stubs, confirmed zero real call sites, confirmed the codebase's OWN comments elsewhere already call them "hollow" | HIGH -- textbook ghost-code/mock-trap pattern, but INERT (nothing calls them, so zero live-behavior risk) |

RECOMMENDATION for Category D: KEEP all of these in place (do not delete) -- they are small,
carry real design intent/history, and several are explicitly self-documented as deliberate,
reviewed retirements rather than accidental cruft. The one exception worth actively considering:
MERGE `app/core/scheduler.py`'s design into a real adoption pass (a genuine, positive
architectural opportunity, not a cleanup item) given it already solves a real, independently-
confirmed problem (many uncoordinated `while True: sleep(N)` loops).

## Category E: archive_janitor/ (70 files) and archive_optional_files/ (22 files)
- archive_janitor/: confirmed structurally isolated -- not on sys.path from run.py's cwd, zero
  real import statements anywhere in live source (only one comment reference in run.py:57
  acknowledging this). [VERIFIED] All ~40+ of its own .py files carry `__main__` guards
  (standalone-script shape), consistent with "frozen migration leftovers", not live capability.
- archive_optional_files/ (22 files, 144KB): NOT independently deep-dived this pass beyond
  confirming zero live .py imports reference it by name. [VERIFIED absence of import; NOT
  independently confirmed content/purpose of every file -- HYPOTHESIS that it's similarly inert,
  based on directory naming and the zero-import signal alone]

RECOMMENDATION: both directories are already effectively "archived" by name and by isolation --
no action needed beyond confirming (already done) that nothing on the live path can accidentally
import from them. Do not delete outright given unclear provenance/possible historical value;
their current location already achieves the practical goal of keeping them out of the way.
