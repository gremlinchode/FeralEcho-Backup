# Investigation Notes (working log)

Investigation date: 2026-07-16, superseding the 2026-07-04 version.

Methodology note, unchanged in spirit from the original audit: CLAUDE.md
and GREMLIN_ROLE.md are treated as hypotheses to independently re-verify,
not ground truth — including, this time, the *prior version of this
audit's own files*. Where a 2026-07-04 finding is repeated here, it was
re-checked fresh against current source/runtime state, not carried
forward on trust. Three parallel read-only research agents were dispatched
(subsystem/dead-code/peripheral-directory sweep; dependency graph and
auth/endpoint security; live runtime evidence), plus direct verification
of anything surprising or safety-relevant before writing it down — the
same discipline this project's own CLAUDE.md documents applying to
itself (its Findings 28/30 describe exactly this method).

## Session start state (2026-07-16)

- `python run.py` (PID 88140) confirmed live, sentinel `stage: serving`,
  fresh heartbeat — this process had been restarted earlier the same
  session specifically to load a batch of fixes made hours prior, so this
  audit's runtime evidence reflects a fresh (~15-20 minute) uptime window,
  not a long-settled one. Noted explicitly wherever it matters (e.g.
  `reflection_shard_generation`'s liveness check not yet having enough
  post-restart data to evaluate cleanly).
- `ollama serve` confirmed running (PID 32306, since Sunday 10PM).
- No `terminal_client.py` session open, unlike the original audit.
- `git log --oneline | wc -l` → **58** — a real, incremental commit
  history now exists, a fundamental change from the original audit's
  single squashed commit. This alone changes the audit's own confidence
  posture for anything timeline-related: no more mtime archaeology
  needed for the 2026-07-04-to-now period.

## What was re-verified fresh vs. carried forward

**Re-verified directly this pass** (not trusted from any document):
`new_directory/`'s secret-leak file remains untracked; root-level
`environment.json` remains benign OS-metadata only; `.gitignore` covers
`new_directory/`; `_secret_ok()`'s `hmac.compare_digest` usage and
fail-closed behavior; every POST route in `run.py` individually, for auth
gating (this is what surfaced `/mirror_echo`'s gap — not previously
flagged by any prior pass, including CLAUDE.md's own extensive Finding
history); all eleven previously-orphaned files' actual deletion (not just
their continued absence of callers); `archive_janitor/`'s continued
isolation from `sys.path`; live FAISS vector counts via direct Python
read; the Liveness Ledger's live pass/fail state via the actual running
`/admin/liveness-status` endpoint; `self_edit_convergence.json`'s raw
cycle/name counts; a live self-edit failure that occurred *during* this
audit's own runtime-check window (06:51:55 today).

**Carried forward from CLAUDE.md with a fresh confirmation pass, not
independently re-derived from scratch**: the general shape of the
Emergence Roadmap's seven phases (this session's own prior work, already
extensively verified when it was built — re-describing it here would not
add confidence, only length); the detailed mechanics of F1/F2/F3 (unchanged
since the original audit's own direct verification, no reason found to
re-derive).

## A mistake caught and corrected during this pass, worth recording per this project's own stated discipline

A draft of behavior_map.md initially stated NightCycle's interval as 300s,
reasoning from `NightCycle.__init__`'s own default parameter
(`interval: int = 300`). Before finalizing, the actual instantiation call
site was checked (`run.py:1186`): `NightCycle(app, interval=3600, ...)` —
the real, live interval is 3600s, matching the original audit's claim. The
300s figure is only the class's own fallback default, relevant to its
standalone test block, not to how it's actually run in production. Fixed
before this became a stale claim baked into this fresh audit — recorded
here as a small, concrete example of the exact discipline this whole audit
depends on: a claim (even a very plausible-looking one, straight from the
class's own signature) is not verified until the real call site is
checked.

## Closing synthesis (this pass)

Combined with direct reads of `run.py` (all 41 routes,
`start_background_threads()` in full), `night_cycle.py`,
`self_edit_convergence.json`, live liveness-status output, live FAISS
counts, and fresh git/secrets checks, plus three dispatched research
passes, this investigation reached a stable, evidence-backed model of the
current system. All twelve deliverable files have been regenerated:
architecture.md, dependency_graph.md, dead_code.md, behavior_map.md,
subsystem_inventory.md, runtime_observations.md, risk_register.md,
architecture_drift.md, investigation_notes.md (this file), final_report.md,
echo_briefing.md, echo_roadmap.md.

**Highest-confidence findings** (corroborated by both static reading and
live runtime evidence, this pass): FAISS is healthy at 47,607 vectors; all
eleven previously-orphaned files are genuinely deleted, not just
uncalled; the five previously-dead run.py subsystems are now honestly
retired, not silently failing; the Global Workspace bus carries genuine
multi-source traffic; the self-edit safety pipeline correctly rejected a
real hallucinated candidate live during this audit's own check window;
`/mirror_echo` has no authentication of any kind.

**Explicitly unresolved, named rather than guessed** (per this audit's own
ground rules): whether `reflection_shard`'s real-generation fix is
actually firing in steady-state production (too short an observation
window this pass); the root cause of the `unclassified` self-edit
convergence bucket; whether `prose_stripping`'s Finding-32 prompt rewrite
will eventually converge (not enough post-fix cycles have run); whether
`/mirror_echo`'s gap has ever been reached from outside the intended
network boundary.
