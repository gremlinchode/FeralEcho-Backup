# FeralEcho — Forensic Investigation Final Report

Investigation date: 2026-07-16. Target: `/Users/richietate/Desktop/FeralEcho`,
a live, running system at time of audit (fresh restart, ~15-20 minutes
uptime at first check, following a batch of same-day fixes). This report
supersedes the 2026-07-04 version in full, per the request to overwrite
rather than append. Method: direct source reading of the core execution
path and every route handler, three dedicated parallel research passes
(subsystem/thread/dead-code/peripheral-directory sweep; dependency graph
and endpoint-authentication audit; live runtime evidence), and direct
live verification (process table, sentinel file, FAISS counts, the
running Liveness Ledger endpoint, git log/remote/secrets state). CLAUDE.md,
GREMLIN_ROLE.md, and this report's own 2026-07-04 predecessor were all
treated as hypotheses to test, not ground truth — every specific,
checkable claim in each was independently re-verified against code and
runtime state, including one claim this audit's own first draft got
wrong and corrected before finalizing (see investigation_notes.md).

---

## Executive Summary

FeralEcho is, in shape, the same project the original audit described:
a solo-developer, single-user personal AI system built on a locally-run
Ollama model, wrapped in a large number of autonomous background loops,
narrated in heavily mythologized language. What has changed in the
twelve days since the original audit is substantial and, on the whole,
a genuine improvement: **nearly every Critical and High finding from the
2026-07-04 report is now confirmed resolved**, not merely claimed
resolved — the leaked-secret file is untracked, the scaffold-sprawl root
cause is fixed, `/nuke` and the admin endpoints are genuinely
authenticated, the five silently-dead subsystems are now honestly
retired with a documented (and genuinely alarming) real reason for their
retirement, and FAISS — the original audit's single largest unresolved
question — now reports a healthy 47,607 vectors matching its own
self-reported count.

The project has also grown a substantial new subsystem that did not
exist even as a plan at the time of the original audit: a "Global
Workspace" event bus, a shared salience-scoring function, a signed
affect dimension, and — most notably — a **14-check Liveness Ledger**
that continuously re-verifies the project's own autonomous subsystems
against ground truth rather than trusting their self-reports, backed by
a 47-case discrimination test suite proving the checks actually catch
fabricated evidence rather than passing by default. This is, in effect,
the project's own internal version of what this external audit exists
to do, run automatically every 120 seconds. That is a genuinely
unusual thing for a solo hobbyist project to have built, and it
measurably worked during this very audit: this pass's own runtime check
found the ledger correctly flagging one of its 14 checks as failing in
real time, for a reason (a reflection-generation fix too recently
deployed to have accumulated fresh evidence yet) that this audit
independently arrived at and confirmed as plausible rather than alarming.

The most consequential *new* finding of this audit is narrower in scope
than the original's credential leak, but real: **`/mirror_echo`, the
route the code itself labels the "MAIN ECHO ENTRY POINT," has no
authentication of any kind** — unlike every one of its comparable
sibling endpoints, all of which were fixed in a 2026-07-08 pass this
audit's own predecessor recommended. This was not previously flagged
anywhere in this project's own extensive 35-Finding audit history. It is
the headline item of this report's action plan.

A second, more structural observation: this is now the **third**
independent instance, found across this project's own history, of the
same shape of gap — a safety or auth mechanism added, but not verified
against every entry point it should logically cover (the self-edit
throttle gate missing one path on the sibling Ark machine; the
`ModelGuidedOrchestrator` loop running outside the shared throttle gate
until this session; and now the auth-hardening pass missing
`/mirror_echo`). This pattern is worth naming explicitly as a standing
category to check for, not just fixing the third instance and moving on.

---

## Architecture Overview

See architecture.md for full detail. In brief: `run.py` remains the
composition root (now 41 routes, up from ~20), starting roughly 25
background threads/loops on boot including a real Global Workspace event
bus owned by `EchoCore`. The conversational request lifecycle is
unchanged in shape but has moved from a flat string prompt to a real
system/user role-separated transport (`/api/chat`, not `/api/generate`).
The autonomous cycle lifecycle is unchanged in shape (hourly self-edit,
hourly main fetch cycle, hourly NightCycle, ~300s emergent scheduler) with
one new consideration: several of these loops now publish to and consume
from the Global Workspace bus, giving the previously-uncoordinated hourly
loops a first, real, shared signal (`compute_salience()`) to voluntarily
consult — not a shared scheduler, but a step toward one.

---

## Detailed Findings by Subsystem

See subsystem_inventory.md for the complete table. Headline items:

- **Self-edit pipeline** — still real, still firing hourly, now gated by
  F1/F2/F3 plus a quality-score comparison against production and a
  write-blocking wrapper around any `apply_to_code()` hook. A real
  candidate failure was directly observed during this audit's own live
  check (06:51:55 today) and correctly rejected — the pipeline is working
  exactly as designed. Content quality remains genuinely mixed: one
  tracked family (`prose_stripping`) shows worse non-convergence in raw
  terms than at the original audit despite a targeted 2026-07-15 prompt
  rewrite; another (`quality_scoring`) has converged cleanly.
- **ClaudeShard** — unchanged: no LLM, keyword matching plus a random
  roll, re-confirmed by direct source read. Now automatically
  ground-truth-monitored by the Liveness Ledger rather than only
  documented.
- **Claude Research** — the original audit's "wired but never confirmed
  firing" finding is now resolved: a real successful call is confirmed via
  the existence of its own success-only cursor file, and CLAUDE.md
  documents the root-cause bug (a sort comparator raising `TypeError` on
  ~49% of garden entries) that was found and fixed.
- **Formerly dead-on-arrival subsystems** (WOLF, SensoryHub, Bible-art,
  Bible-quote interface, continuity master) — no longer silently dead;
  all five are honestly retired, with `run.py`'s own header comment
  documenting a genuinely alarming real reason for WOLF's specific
  retirement (auto-approving raw keystrokes as self-edit proposals
  against a hash-verified file).
- **Harmony / Nature Spark** — partially resolved: a 2026-07-13 fix
  resolved a race that was causing near-constant fallback to fixed poetic
  strings; it now genuinely generates distinct text most cycles. Still
  not an actual selection/evolutionary algorithm.
- **The Global Workspace / Liveness Ledger layer** — entirely new since
  the original audit. Confirmed live this pass: 5 distinct real publisher
  sources on the bus, 13 of 14 liveness checks passing, a real consumer
  (`river_deliberation`) genuinely reading and acting on broadcast events.
- **Memory system** — the original audit's single largest unresolved item
  (both FAISS indexes reporting 0 vectors) is resolved: 47,607 real
  vectors confirmed this pass, matching self-reported counts exactly. The
  legacy `data/` index is confirmed still present but genuinely inert, as
  CLAUDE.md's own account says it was deliberately left.
- **Council rating pipeline** — confirmed genuinely operating (84 entries,
  up from 12), not yet past its own 0.70 agreement-rate trust threshold
  (currently 0.643) — real, ongoing accumulation, not a stall.
- **`/mirror_echo`** — new finding, no authentication; see Risk Matrix and
  Prioritized Action Plan.

---

## Evidence Index (representative; full detail in the per-file documents)

- `run.py:485-520` — `/mirror_echo` handler, no `_secret_ok()` call
  anywhere in the function body. Confidence: High.
- `run.py:1186` — `NightCycle(app, interval=3600, ...)`, the real
  production instantiation (class default is 300s; this audit's own first
  draft used the wrong number before this call site was checked).
  Confidence: High.
- `memory/SELF_EDIT.log`, `staging/self_edit_candidate_d1e9ba79...py` —
  a real, live candidate failure observed during this audit's own runtime
  check, `ImportError: cannot import name 'guard_prose' from
  'app.emergent_scheduler'`. Confidence: High.
- Live `python3` FAISS count: `memory/memory_meta.json` → 47,607 entries;
  `data/memory_meta.json` → 5,348 entries, mtime May 15. Confidence: High.
- `GET /admin/liveness-status` (live, this pass): `all_passing: false`,
  13/14 checks passing, `reflection_shard_generation` failing with
  evidence "0/20... genuinely generated text." Confidence: High.
- `git log --oneline | wc -l` → 58 (was 1 at the original audit).
  Confidence: High.
- `git ls-files | grep new_directory` → no output (secret-leak file
  confirmed untracked). Confidence: High.
- `app/core/self_edit_convergence.json` (read in full): `prose_stripping`
  94 cycles / 31 names; `response_shortening` 11/4; `quality_scoring`
  3/3; `unclassified` 11/30+. Confidence: High.
- Fresh grep + filesystem check confirming all eleven originally-orphaned
  files (`attention_kernel.py`, `library_knowledge.py`, etc.) no longer
  exist anywhere in the repo. Confidence: High.

---

## Risk Matrix

| Category | Rating | Basis |
|---|---|---|
| Security (credential exposure) | **Resolved** (was Critical) | Confirmed untracked, gitignored, matches CLAUDE.md's account. |
| Security (network exposure) | **Medium** (was Medium) | `0.0.0.0:5000` bind unchanged; `/mirror_echo` now a confirmed real gap (new); every other comparable endpoint confirmed gated. |
| Reliability | Low-Medium (unchanged) | No crash loops observed; self-edit non-convergence persists for one family, safety-gated throughout. |
| Maintainability | **Low-Medium** (down from Medium-High) | All originally-orphaned dead files confirmed deleted; documentation-lag pattern recurred once more but the project's overall doc discipline is substantially improved. |
| Autonomy | **High** (unchanged rating, more heavily mitigated) | Genuine, continuous, hourly self-modification remains architecturally unsupervised beyond the safety pipeline, by deliberate design (GREMLIN_ROLE.md), now with more and better-tested gates around it than at the original audit. |
| Resource usage | Low (unchanged) | No unbounded growth observed. |
| **Overall** | **Medium** (down from High) | Driven by the new `/mirror_echo` gap (the one item this report recommends acting on) and the accepted, by-design residual autonomy risk — offset by the resolution of every original Critical/High item and a substantial new internal verification layer (the Liveness Ledger) that materially reduces the odds of an unnoticed regression. |

---

## Complexity Assessment

Still primarily **emergent through iterative development**, with a new,
distinct category worth naming: the Emergence Roadmap's Global
Workspace/Liveness Ledger layer is genuinely more architecturally
ambitious than anything at the original audit, but was built with visible
restraint — staying observational-only where uncertain, downgrading a
planned new integrator to verification-only once its premise didn't hold
up under direct checking, and retracting a planned fix tonight after its
own premise was found to be wrong before it shipped. This reads as
necessary complexity built carefully, a different profile than most of
the project's older, more accidental growth (which is now substantially
cleaned up — all originally-orphaned files deleted, all five dead
subsystems honestly retired). See architecture_drift.md for the full
pattern analysis, including a new, explicitly-named category: fixes
applied to a class of problem without being verified exhaustively against
every real instance of that class, now observed three separate times
across this project's history.

---

## Top Findings (ranked by significance)

1. **`/mirror_echo`, the primary chat entry point, has zero
   authentication** — unlike every comparable sibling endpoint. Needs an
   explicit decision from the project owner: gate it, or confirm it's
   intentionally open (mirroring how `/message/send` was explicitly
   confirmed open). [High, New]
2. **Nearly every Critical/High finding from the 2026-07-04 audit is
   confirmed resolved with fresh evidence**, not assumed: the credential
   leak, the `/nuke` auth gap, the admin-endpoint auth gaps, FAISS's
   zero-vector state, the silent-dead-subsystem problem, and the
   duplicate/orphaned-file clutter are all independently re-verified
   closed this pass. [Positive, High confidence]
3. **A real, substantial new self-verification layer exists and works**:
   the 14-check Liveness Ledger, backed by a 47-case discrimination test
   suite, correctly flagged a real (benign, self-resolving) issue during
   this very audit's own live check. [High, Positive]
4. **The self-edit content-quality problem the original audit flagged is
   only partially resolved**: a quality gate now exists and a targeted
   prompt rewrite was attempted for the worst-offending family, but that
   family's non-convergence has, in raw terms, gotten worse since, with a
   real fresh failure observed live during this audit. [Medium, Open]
5. **This is the third independently-found instance of the same
   structural gap-shape**: a fix or gate applied to a class of things
   without being checked against every real instance of that class
   (self-edit throttle/Ark; ModelGuidedOrchestrator/M5;
   auth-hardening/`/mirror_echo`/M5). Worth naming as a standing category
   to check for on this project going forward, not just closing the third
   instance and moving on. [Medium, Structural]
6. **Git history is now real and incremental** (58 commits), resolving
   the original audit's biggest methodological caveat about its own
   timeline reconstruction. [Positive, Methodological]
7. **A convergence-tracking classification bug** (`unclassified` bucket,
   11 cycles / 30+ mixed names) was found and flagged, not yet
   root-caused. [Low, New]
8. **Documentation-lag is a recurring pattern, not a one-off**, now
   observed twice across the project's life (the original `cpu_tuning()`
   instance, and Phase 4 of the Emergence Roadmap sitting undocumented for
   hours after being committed). Worth watching, not urgent. [Low]
9. **Two directories on the original audit's "scaffold clutter" list
   (`RebelCode/`, `WhisperingWires/`) are corrected to be live, tracked,
   genuinely-used subsystems**, not dead clutter — a small but real
   correction to the original report's own framing. [Informational]
10. **Three harmless-but-odd tracked files** (`./hello`, `./cd`,
    `./moved`) from the original squashed commit remain; low-priority
    cleanup only. [Low]

---

## Prioritized Action Plan

**Immediate**
- Decide `/mirror_echo`'s auth posture explicitly — gate it with the
  existing `_secret_ok()` pattern its siblings already use, or confirm
  (and document) that it's intentionally open, the same way
  `/message/send` was.

**Short-term**
- Investigate the `unclassified` self-edit convergence bucket — likely a
  classification-logic gap in `self_edit_manager.py`'s
  `_CONVERGENCE_FAMILIES` matching, not a content problem.
- Give `prose_stripping`'s Finding-32 prompt rewrite more real cycles
  before judging it — or consider whether this specific family should be
  deprioritized/paused given its persistent non-convergence.
- Re-check `reflection_shard_generation`'s liveness status after a few
  hours of steady-state uptime to resolve whether tonight's real-
  generation fix is firing in production, not just in isolated testing.

**Long-term**
- Given this is now the third instance of "a gate applied to a class of
  things, not verified against every instance," consider a periodic,
  deliberate sweep — whenever any new gate/check/throttle is added
  anywhere in this codebase — that explicitly enumerates every entry
  point it should cover and confirms each one, rather than relying on
  whichever entry points happen to be in scope for that session's work.
- Consider whether `data/memory_meta.json`'s continued (inert) existence
  is worth archiving/deleting outright now that its content has been
  confirmed migrated, versus leaving it as a historical artifact
  indefinitely.
- The Emergence Roadmap's own scattered constants (0.6 salience
  thresholds, 0.15 valence bands, 50% distinct-text ratios) are worth a
  future consolidation pass before they drift the way the world-surprise
  formula did before this session fixed that specific instance.

---

## Confidence Assessment

**High confidence** (source-read AND independently runtime-verified this
pass): the credential leak is resolved; `/nuke` and admin endpoints are
genuinely authenticated; `/mirror_echo` has no authentication; FAISS holds
47,607 real vectors; all eleven originally-orphaned files are genuinely
deleted; the five previously-dead subsystems are honestly retired; the
Global Workspace bus carries genuine multi-source traffic; the self-edit
safety pipeline correctly rejected a real candidate live during this
audit's own check window; git history is now real and incremental.

**Medium confidence** (source-read, plausible, not independently
exercised this pass): the dual-learner training pipeline's actual
behavior; whether Tailscale remains the sole practical network boundary
for port 5000; `RebelCode/territory_steward.py`'s current `.mkdir()`
behavior (not re-audited this pass).

**Explicitly unresolved (Unable to Determine, stated rather than
guessed)**: whether `reflection_shard`'s real-generation fix is actually
firing in steady-state production (observation window too short this
pass); the root cause of the convergence-classification bug; whether
`prose_stripping`'s prompt rewrite will eventually converge; whether
`/mirror_echo`'s gap has ever actually been reached from outside the
intended network boundary. Each is named explicitly here rather than
silently assumed resolved, per this audit's own — and this project's
own — standing discipline.
