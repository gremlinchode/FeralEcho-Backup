# Architecture Drift

Investigation date: 2026-07-16, superseding the 2026-07-04 version. Unlike
that version, this pass has a real, non-rewritten git history to work
from — the single biggest methodological change since the original audit.

## Git history is now real evidence, not reconstructed from filesystem mtimes

The original audit found exactly one commit ("clean initial commit,"
2026-06-28) and `git filter-repo` artifacts implying a deliberate history
scrub — it explicitly warned that its own timeline reconstruction (from
file mtimes) was weak, directional evidence only. **This is no longer
true.** `git log --oneline` now shows 58 commits, an incremental,
individually-dated, individually-messaged history spanning from that
original squash through tonight's work. This is a genuine, verifiable
change in the project's own practices — real commit-by-commit history now
exists for anyone (including a future audit) to read directly, rather
than needing to infer a timeline from file modification times.

## What actually changed since 2026-07-04 (from the real commit log, not reconstruction)

Roughly in order: a security-and-correctness bug-hunt pass (108 findings,
CLAUDE.md's Finding 22, fixed in batches); the `/api/generate` → `/api/chat`
transport migration (Finding 17); several rounds of self-edit pipeline
hardening (dry_run made real, Optuna's stale-best-trial bug, a quality gate
against production, apply_to_code's write-block); a FAISS split-brain
migration; the WOLF/SensoryHub retirement (with its real, alarming root
cause documented); and, most recently, the "Emergence Roadmap" — seven
phases (2026-07-15/16) building a Global Workspace event bus, a shared
salience function, a signed valence dimension, a 14-check Liveness Ledger
with a 47-case discrimination suite, and — as of tonight — real generation
in the reflection shard, wide-broadcast arbitration on the workspace bus,
and an observational quality-delta stream for self-edit dry-run trials.
None of this existed, even as a plan, at the time of the original audit.

## Drift patterns observed — some resolved, one new, two still recurring

1. **Migration-without-cleanup — RESOLVED.** The original audit's largest
   finding (WOLF/SensoryHub/Bible-art/continuity-master silently dead)
   is now an honestly-retired state with a documented real root cause
   (WOLF auto-approving raw keystrokes against a hash-verified file). This
   pattern, as originally described, no longer exists in the codebase.

2. **Uncoordinated hourly loops — STILL TRUE, one instance actively
   caught and fixed mid-drift.** At least three independent ~3600s loops
   still exist (self-edit, main autonomous_loop, NightCycle). New this
   session: `ModelGuidedOrchestrator` was found to be a *fourth*
   autonomous loop that had been running entirely outside the shared
   throttle gate the other loops share — caught and fixed this session
   (CLAUDE.md Finding 28). The pattern the original audit named
   ("features added incrementally, older loops never refactored to match
   newer scheduling maturity") is still visible in the fact that a fourth
   loop could exist unnoticed by the gate for as long as it did.

3. **Parallel/duplicate implementations left in place — RESOLVED for the
   originally-named instances.** `river_deliberation_backup.py` and
   `dual_learning_backup.py` are confirmed deleted. A **new, smaller**
   instance of the same underlying habit was found and fixed tonight: the
   `world_surprise`/`coherence_tension` normalization formula was
   independently reimplemented in three separate files
   (`echo_core.py`, `emergent_scheduler.py`, `river_deliberation.py`)
   before being deduplicated onto one shared function this session. Same
   root habit (write a fresh copy rather than reuse), smaller blast
   radius (a formula, not a whole module) — worth naming as the same
   pattern recurring at a different scale, not a new pattern.

4. **Naming/branding outpacing implementation — STILL TRUE for ClaudeShard/Harmony, WITH ONE GENUINE PARTIAL RESOLUTION.**
   ClaudeShard is unchanged (still keyword+random, still branded as AI).
   Harmony/Nature Spark's specific gap **has narrowed**: a 2026-07-13
   singleton fix resolved a concurrent-cache race that was causing it to
   silently fall back to fixed strings almost every cycle; it now
   genuinely generates distinct text most of the time. The
   "EVOLUTIONARY_PRESSURE / Kill the weakest 7" language is still not
   backed by an actual selection algorithm — that half of the original
   finding is unchanged.

5. **Documentation lags fixes — STILL A RECURRING PATTERN, now with a
   second independent instance.** The original audit's example
   (`cpu_tuning()`) is itself now fixed in CLAUDE.md. This session found a
   second instance of the identical shape: Phase 4 of the Emergence
   Roadmap sat undocumented in CLAUDE.md for hours after being committed,
   discovered only because later work needed to reference it. The
   project's overall documentation discipline is much stronger now (35
   numbered, self-correcting Findings, several literally titled
   "Correction"), but this specific failure mode — a real, committed
   change not making it into the narrative doc promptly — has now
   recurred at least twice across the project's life. Worth tracking as
   an ongoing risk to watch, not a solved problem.

6. **Relative-path assumptions causing scaffold sprawl — RESOLVED (root
   cause), residue is historical.** `self_edit_manager.py`'s path
   constants are confirmed anchored via `__file__`. The 18 scaffold
   directories the sprawl produced are still present but inert (re-swept,
   zero new secrets).

7. **NEW PATTERN this pass: a security-relevant fix applied to a class of
   endpoint, but not exhaustively to every member of that class.**
   The 2026-07-08 auth-hardening pass (CLAUDE.md Findings 14/15) added
   `_secret_ok()` gating to `/nuke`, `/admin/restore`,
   `/admin/council-spotcheck`, `/inject_memory`, `/force_nightcycle` — but
   not `/mirror_echo`, a comparably state-mutating endpoint that predates
   and postdates that fix pass untouched (see risk_register.md R12). This
   is structurally the same shape as pattern #2's `ModelGuidedOrchestrator`
   gap (a fix applied to the loops/endpoints someone thought to check, not
   proven exhaustive against every actual instance) and the same shape
   this project's own sibling-machine briefing (`SIBLING_BRIEFING_FROM_ARK.MD`)
   already flagged as a repeat pattern on the Ark fork (a throttle gate
   covering one entry point while a second wasn't checked). This is now
   the third independent instance of "a gate was added, not every real
   entry point it should cover was verified" found across this project's
   own history (self-edit throttle/Ark, ModelGuidedOrchestrator/M5, and
   now the auth-hardening pass/M5) — worth naming explicitly as a
   standing category of gap to check for whenever a new gate is added
   anywhere in this codebase, not just this one instance.

## Is complexity necessary, accidental, or emergent? — updated assessment

Still primarily **emergent through iterative, additive development**, and
now with a genuinely new category to weigh: the Emergence Roadmap's Global
Workspace/Liveness Ledger layer is meaningfully more architecturally
ambitious than anything in the original audit's scope, but was built with
visible discipline about staying additive and observational (Phase 2a's
explicit "observational-only" posture, Phase 3's decision to downgrade a
planned new integrator to a verification-only check once its premise
didn't hold up, Phase 5's own retraction of a planned fix after checking
its premise against ground truth). This reads as **necessary complexity
built carefully**, not scope creep — a meaningfully different profile than
the "add another hourly loop" pattern that characterizes most of the
project's older growth. The accidental-complexity items from the original
audit (scaffold sprawl, dead-import branding mismatch, duplicate Bible-art
modules) are resolved. The main open question for a future audit: whether
the Liveness Ledger and Emergence Roadmap machinery itself avoids becoming
the next generation's "duplicate implementation left in place" — its own
17 constants/thresholds (0.6 salience cutoffs, 0.15 valence neutral bands,
50% distinct-text ratios) are exactly the kind of scattered magic numbers
that tend to drift out of sync with each other over time if not
periodically consolidated, the same way the world-surprise formula did
before this session deduplicated it.
