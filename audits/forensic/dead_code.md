# Dead / Orphaned / Abandoned Code

Investigation date: 2026-07-16, superseding the 2026-07-04 version. Method
unchanged: grep-for-callers plus, where the original audit found a live
import failure, a fresh confirmation. Confidence: High for items backed
by both a grep pass and either a runtime check or direct file-existence
check this pass.

## Headline change since 2026-07-04: every previously-orphaned file in this list is now confirmed genuinely deleted

The original audit found eleven files in `app/` with zero callers
(`attention_kernel.py`, `bible_module.py` [the app/core copy],
`echo_load_mastery.py`, `feral_tools.py`, `library_knowledge.py`
[6,775 lines], `Memory_helpers.py`, `placeholder_ai.py`,
`project_scanner.py`, `river_deliberation_backup.py`,
`orientation_protocol.py`, `dual_learning_backup.py`). A fresh pass this
audit re-checked every one directly: **all eleven are confirmed missing
from the filesystem**, not merely still-uncalled-but-present. A
repo-wide basename search found no relocated copies (the one exception,
`bible_module.py`, survives only under `archive_janitor/`, a different
file serving a different, already-accounted-for purpose). This is a real,
verified cleanup — CLAUDE.md's Finding 30 (2026-07-15) already claimed
this; this pass independently confirms the claim rather than repeating it.

## Confirmed retired (not silently dead) — a genuine change in kind, not just degree

The original audit's single largest finding was that `run.py` narrated
five subsystems as active while they silently failed to import
(`sensory_hub_autonomous`, `feralecho_continuity_master`,
`alignment_kernel`/WOLF, `bible_module`, `echo_bible_interface`). Re-read
`run.py` fresh this pass: **none of the five are imported anywhere in the
current file, not even as a bare name that would resolve to a stub.**
`run.py`'s own header comment (lines 3-6) states the real reason WOLF was
retired: its own audit log showed it auto-approving ~100% of "proposals"
that were actually raw keystrokes from SensoryHub's global key listener,
writing directly into the hash-verified `echo_principles.json` with no
real evaluative gate — a genuinely alarming root cause, not a vague
cleanup note. `start_wolf()`/`kill_wolf_gracefully()` are explicit no-op
functions that log their disabled status; `/trigger_wolf_kill` and
`/howl` now return `{"status": "disabled", "detail": "WOLF was retired
2026-07-04"}` instead of responding with dramatic JSON implying activity.
The distinction matters: this is "honestly retired," a strictly better
state than "silently dead," and worth recording as a genuine improvement
rather than filing under the same finding as before.

All five source files still exist, unchanged, under `archive_janitor/`
(confirmed: `archive_janitor/{sensory_hub_autonomous,
feralecho_continuity_master, alignment_kernel, bible_module,
echo_bible_interface}.py`, 70 files total in that directory). `archive_janitor/`
is confirmed still not on `sys.path` anywhere, and contains no hardcoded
credentials (checked directly this pass — only `os.getenv()` references).

## Confirmed disconnected by design (re-verified, unchanged)

- `app/core/self_heal.py` — still exists, still zero live callers
  (confirmed by fresh grep: only self-references, a `run.py` comment, and
  `audits/2026-07-03/verify_claude_md.py` reference it). Matches
  GREMLIN_ROLE.md's stated policy: reconnecting it requires explicit human
  review, not a default action. Unchanged since 2026-07-04.
- `app/core/wolf_friction_bridge.py` → `simulate_self_edit()` — still the
  only call site (`app/core/echo_model_orchestrator.py:1351`), still never
  `perform_self_edit()`. **What's new**: this is no longer just documented
  as a fact to re-verify by hand — `app/core/liveness_ledger.py`'s
  `wolf_friction_bridge` check (lines 347-390) now re-reads this exact call
  site automatically every 120s and fails loud the moment it no longer
  matches this shape. The project has effectively automated the thing this
  external audit does for a living, for this one specific fact.

## Empty aspirational directories — unchanged

`app/experimental/` and `app/integrations/` — still zero files, not even
`__init__.py`. Not re-verified with a fresh `ls` this pass, but no
evidence found anywhere that either has been populated.

## Peripheral top-level scaffold directories — re-swept, one correction to the original framing

All 18 candidate directories from the original audit's list
(calculator/, chatbot/, echo_scripts/, new_directory/, PythonAnalysis/,
NewBeginning/, MyPythonProject/, rebel_directory/, x86_64_env/,
trash_autonomous/, feral_tools/, RebelCode/, MysteriousCode/, plus
several smaller ones) still exist on disk. A fresh, targeted
credential-pattern grep (`sk-`, `ghp_`, `AKIA`, JWT-shaped strings,
`*_KEY=`/`*_TOKEN=`/`*_SECRET=` assignments) across every non-empty one
found **zero real secrets** this pass — only harmless "SECRET_NUMBER"
guessing-game text from hallucinated self-edit code. This matches
CLAUDE.md's Finding 30 (2026-07-15), independently re-confirmed rather
than assumed.

**Correction to the original audit's own framing, worth stating plainly**:
two directories on the original "peripheral scaffold" list are not dead
clutter at all.
- **`RebelCode/`** — `territory_steward.py`'s `claim_new_ground()` is
  CLAUDE.md's own documented second root cause (alongside the
  now-fixed relative-path issue) for the scaffold-sprawl pattern itself.
  It is live, tracked, and not itself dead code — it is a cause of
  clutter elsewhere, not an instance of it. Its own `.mkdir()`-on-LLM-
  supplied-names behavior was not re-audited this pass.
- **`WhisperingWires/`** — the real, live log sink for
  `app/autonomous_harmony_manager.py`'s "Nature Spark" output
  (`thoughts.log`, `harmony.log`), monitored by `liveness_ledger.py`'s
  `nature_spark` check. Genuinely written to on an ongoing basis, not
  dead.

Both are correctly un-gitignored, which is appropriate since both are
live. `feral_tools/` and `EmpathyBot/` are effectively empty (only a
`.DS_Store` file each) and can be treated as inert.

## Three odd tracked files from the original squashed commit (new finding, low priority)

`./hello` (a trivially compiled Mach-O x86_64 executable — `strings`
confirms its entire content is the literal text `Hello, world!`, nothing
concerning), `./cd` (a genuine, substantive Python script — a
memory/embedding tool using `sentence_transformers`/`sklearn` fallback —
oddly named to shadow the shell's `cd` builtin, which only matters if
someone runs it unusually, e.g. `python cd`; it is a `.py` file, not an
alias, so this is a naming confusion, not a functional hazard), and
`./moved` (literal text content: `"Hello, world!"`). All three trace to
the original `44e7a8e` "clean initial commit" and are harmless repo
clutter — worth a cleanup pass someday, not a risk-register item.

## Redundant/duplicate implementations — resolved

`river_deliberation_backup.py` and `dual_learning_backup.py` (flagged as
Low-severity R9 in the original risk register) are confirmed deleted, per
the "confirmed genuinely deleted" section above. No new duplicate
`_backup` modules were found this pass.

## Stale documentation describing already-fixed/removed things — recurring pattern, worth tracking as a pattern rather than a one-off

The original audit's single example (CLAUDE.md's Finding 4 describing a
`cpu_tuning()` bug in code already deleted) has itself since been
corrected in CLAUDE.md. This audit's own research (tonight's session, not
this pass specifically) found a fresh instance of the identical pattern:
Phase 4 of the Emergence Roadmap (a real, already-committed feature —
Global Workspace real consumers, signed valence, an observe-only coupling
estimate) sat completely undocumented in CLAUDE.md for hours after being
committed, discovered and fixed only because this session's own
implementation work needed to reference it. Two independent instances of
the same failure mode, in two different eras of the same project's
documentation, is enough to call this a recurring pattern rather than an
isolated slip — worth naming explicitly in architecture_drift.md.
