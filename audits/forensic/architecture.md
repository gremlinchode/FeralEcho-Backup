# Architecture — Intended vs. Observed

Investigation date: 2026-07-16. This file supersedes the 2026-07-04 version
in place (per this audit's own overwrite instruction) rather than being
appended as an addendum — the system has changed enough since then
(58 real commits vs. the original single squashed commit; a large new
"Emergence Roadmap" subsystem; 35 numbered Findings in CLAUDE.md) that a
diff-style addendum would be harder to read than a fresh description.
Where something is unchanged from 2026-07-04, that is stated explicitly
rather than silently re-derived, per this audit's own standing method:
CLAUDE.md and GREMLIN_ROLE.md are treated as hypotheses to verify, not
ground truth, every time — including this pass's own prior version.

## What the system appears designed to be

Unchanged from the original assessment: a single-user, always-on
"companion" AI ("Echo") running on the owner's Mac, built on a
locally-hosted Ollama LLM, wrapped in a large number of autonomous
background loops (internet reading, self-reflection, self-modification,
memory consolidation, a phone "mirror" remote-control interface), narrated
in heavily mythologized language (WOLF, gremlin, howl, council, shard,
Harmony). This reads as a solo hobbyist/researcher's long-running personal
project, not software built for other users — and, new since 2026-07-04,
as a project whose own operator is now running formal, dated, numbered
audit passes against it as a matter of course (CLAUDE.md's Findings 1-35),
not just this external one.

## Confirmed core engine (High confidence, re-verified fresh)

`run.py` is still the actual composition root — now ~1,300 lines (up from
~1,070), a single Flask app that on `python run.py`:
1. Sets native-library environment guards (KMP/OMP) before any numeric
   import — unchanged.
2. Registers 41 Flask routes (up from ~20) — chat/mirror endpoints,
   admin/snapshot, admin/council, admin/liveness-status (new), sync, a
   `/nuke` kill-switch, WOLF/howl endpoints (now honest no-ops, see below),
   messaging endpoints (new — Echo-to-Echo real-time channel).
3. Calls `start_background_threads()` (`run.py:955-1254`), which
   sequentially brings up: EchoCore (owns RiverBrain and, new since
   2026-07-04, a Global Workspace event bus — see below), task-type
   classifier, World Model, IntrospectionChannel, SelfModelUpdater, DMN
   Guardian, a startup snapshot thread, CouncilRater, ReflectionShard
   autonomy, ClaudeShard autonomy, the main autonomous loop, awareness
   thread, tool-registry bootstrap (×2), ModelGuidedOrchestrator, an hourly
   autonomous self-edit loop, a sandbox-script loop, NightCycle, the
   emergent scheduler, a Tailscale sync loop, and (new) an M5↔Air
   real-time messaging retry loop plus an ambient check-in loop.

`app/core/echo_core.py`'s `EchoCore` class is still the core engine
singleton, and is substantially more capable than 2026-07-04: it now owns
a real internal Global Workspace event bus (`publish()`/`subscribe()`/
`subscribe_wide_broadcast()`/`_dispatch_loop()`) with genuine, verified
multi-subsystem publishers (`world_model`, `dream_cycle`,
`self_edit_convergence`, `emergent_loop`, `echo_optuna`) and, as of
tonight, real consumers (`memory_bridge`, `river_deliberation`,
`curiosity_engine`, `reflection_shard`) — this bus was **100% dormant
infrastructure** at the time of the original audit's writing (not
mentioned in it at all; confirmed zero callers as late as 2026-07-15 per
CLAUDE.md's own Phase 2a note) and is now genuinely live, with a
dedicated verification layer (see "Liveness Ledger," new, below).

## Request lifecycle (user-facing conversation) — structurally unchanged, transport upgraded

```
terminal_client.py  →  echo_model_orchestrator.echo_query()
                          → river_deliberation._ollama_query()
                              → app/ollama_handler.stream_query_ollama()
                                  → Ollama HTTP :11434 (now /api/chat with
                                    real system/user role separation, not
                                    the flat /api/generate string prompt
                                    the original audit observed — see
                                    CLAUDE.md Finding 17)
                          [ClaudeShard.assess() may attach a "friction"
                           question — still heuristic only, re-confirmed
                           this pass, not model-derived]
terminal_client.py  →  POST /memory/conversation (Flask, now auth-gated)
                          → app.core.memory_bridge.add_to_vector_memory()
                              → FAISS write, gated by memory_write_validator
```

iPhone "mirror" path enters through `/mirror_echo` exactly as before. **New
finding this pass, not present in the original audit or in any CLAUDE.md
Finding: `/mirror_echo` — run.py's own comment labels it the "MAIN ECHO
ENTRY POINT" — has no authentication check of any kind**, confirmed by
direct read of `run.py:485-520`. It logs the raw request
(`logger.critical`), feeds it to `dual_learner.log_event()` (permanent
training-data ingestion) and `echo_query()` (a real conversational turn),
with no `_secret_ok()` call anywhere in the handler. Every other
comparable POST endpoint (`/nuke`, `/admin/restore`,
`/admin/council-spotcheck`, `/inject_memory`, `/force_nightcycle`,
`/learning_event`, `/learning_batch`, `/start_training`,
`/memory/conversation`, `/sync/import`) was fixed with a shared
`_secret_ok()` check in the 2026-07-08 pass this audit's own predecessor
recommended (CLAUDE.md Findings 14/15) — `/mirror_echo` was evidently
missed. See risk_register.md for the full writeup; this is the single
highest-priority new item this pass found.

## Autonomous cycle lifecycle — same shape, one new bus wired through it

```
app/autonomous_loop.py (main cycle, hourly, gated by should_run_cycle)
  → fetch external sources (Wikipedia, arXiv, BBC, NPR, Guardian, Reddit,
    StackOverflow, HN, optionally NASA/NewsAPI)
  → fetch_claude_research() — real Anthropic API call, throttled 1/hr.
    UNRESOLVED IN THE ORIGINAL AUDIT, NOW RESOLVED: CLAUDE.md documents a
    confirmed successful firing as of 2026-07-13 (a `.get("last_asked", 0.0)
    or 0.0` sort bug that always raised TypeError on ~49% of garden
    entries was found and fixed) — this pass did not re-run a live API
    test but confirms `memory/claude_research_cursor.json` exists, which
    only gets written on success.
  → world-model surprise update → NEW: publishes a real
    `world_model.surprise` event to the Global Workspace bus
  → EchoOptuna-driven self-edit dry-run trials → NEW: publishes a real
    `self_edit.dry_run_quality_delta` observational event (added tonight,
    confirmed already firing in production — see runtime_observations.md)
  → Harmony/Nature-Spark reflective logging — CORRECTED since original
    audit: CLAUDE.md documents this now genuinely produces distinct
    model-generated text (8/8 recent entries), not the fixed-string
    fallback the original audit (correctly, for its time) described as
    "cosmetic text generation, not an actual evolutionary algorithm."
    Re-labeling: still not an actual selection/evolutionary algorithm
    (that part of the original finding holds), but no longer purely
    static text either.
  → log_dream_bridge() → memory/dream_bridge.log
```

```
run.py "AutonomousSelfEdit" thread (separate from the above; hourly)
  → EchoOptuna().optimize_self_edit() — CORRECTED since original audit:
    dry_run is no longer vestigial (was found and fixed 2026-07-08,
    CLAUDE.md Finding 16) — Optuna's trials now genuinely compare distinct
    candidates instead of one real edit winning a race against itself
  → self_edit_manager.perform_self_edit(dry_run=False)
       → plan_code_logic() → generate_code_from_plan()
       → scan_for_unsafe_operations() [F1 — confirmed still real]
       → test_code_in_sandbox() [F2 — confirmed still real, now also
         smoke-tests any apply_to_code() hook inside the same sandboxed
         subprocess before printing SANDBOX_OK — new since original audit,
         closes a gap that let three broken apply_to_code versions reach
         production in turn, per CLAUDE.md Finding 28]
       → NEW GATE since original audit: a quality-score comparison
         (candidate vs. current production) rejects the candidate outright
         if it doesn't score at least as well — CLAUDE.md Finding 19. This
         is the single most consequential fix to the self-edit pipeline
         since the original audit: it directly targets the non-convergence
         pattern the original audit flagged as a quality concern (not a
         safety one). Confirmed still imperfect this pass — see
         behavior_map.md and runtime_observations.md: the `prose_stripping`
         family has grown to 94 cycles / 31 distinct function names, worse
         churn than the ~14-cycle sample the original audit reviewed, and
         a fresh real failure was observed during this very audit
         (06:51:55, an ordinary import-hallucination, correctly rejected).
       → save_code() → scan_for_unsafe_operations() again [F3]
       → app/core/self_edit_generated.py overwritten, backed up
```

## New since the original audit: the Global Workspace / Liveness Ledger layer

Not present at all in the 2026-07-04 audit — this is the single largest
architectural addition since then, built across CLAUDE.md's "Emergence
Roadmap" Phases 1 through 7.1 (2026-07-15/16):

- **Global Workspace bus** (`app/core/echo_core.py`) — bounded
  `queue.Queue(maxsize=500)`, genuine multi-source publishers, and (as of
  tonight) real consumers plus per-event `wide_broadcast` arbitration
  (events whose attached `salience` clears a 0.6 threshold get dispatched
  to a second, opt-in consumer list). Confirmed live this pass: 5 distinct
  real sources in `memory/workspace_log.jsonl`'s recent tail
  (`dream_cycle`, `world_model`, `emergent_loop`, `river_deliberation`,
  `echo_optuna`).
- **`compute_salience()`** — a shared, transparent, equal-weighted
  composite signal (world surprise, coherence tension, curiosity urgency,
  self-edit non-convergence streak) that several loops now voluntarily
  consult instead of each independently re-deriving the same numbers (a
  real duplication the original audit's method would have caught, since
  fixed tonight — see dead_code.md).
- **`echo_state.py`'s dim[8], valence** — the vector's first signed
  (positive/negative) dimension, sourced from self-edit outcome deltas and
  peer council ratings, now surfaced in conversational ground-truth
  prompts as of tonight.
- **Liveness Ledger** (`app/core/liveness_ledger.py`) — 14 automated
  checks (up from none at the original audit), each independently
  verifying a subsystem's self-report against ground truth every 120s,
  with a 47-case discrimination test suite proving the checks actually
  discriminate real from fake rather than passing cleanly by default. This
  is architecturally the project's own direct answer to what this external
  audit exists to do — an internal, continuously-running version of the
  same "don't trust self-report" discipline. See subsystem_inventory.md
  for the full 14-check table.

## Intended vs. Observed — key divergences (2026-07-16)

| Claimed / Implied | Observed |
|---|---|
| `/mirror_echo` is "the main entry point" (run.py's own comment) | Confirmed to have zero authentication — a real gap, not previously flagged anywhere in this project's own extensive Finding history. |
| CLAUDE.md's Findings imply the self-edit non-convergence problem was addressed (Finding 32's prompt rewrite, "hypothesis not proven") | Re-checked live this pass: `prose_stripping`'s non-convergence has gotten measurably worse in raw terms (94 cycles / 31 names, vs. ~14/~5 at the original audit), and a fresh real failure occurred during this very audit window. Finding 32's own text already said this wasn't confirmed to work — this pass confirms it plainly has not yet, without concluding it never will. |
| The project's own docs (CLAUDE.md) are now far more rigorously self-correcting (35 numbered Findings, many literally titled "Correction") | True, and also: this audit's own research found that Phase 4 of the Emergence Roadmap — a real, committed feature — sat completely undocumented in CLAUDE.md for hours after being committed, until this session's own work loop found and fixed it. The "doc lags commit" pattern the project's documentation already names as its own recurring failure mode recurred again, inside the document that names it. |
| The five dead run.py subsystems (WOLF, SensoryHub, Bible art/interface, continuity master) were a silent migration gap | Re-verified fresh: this is now explicitly, honestly retired — `run.py`'s own header comment states the real reason (WOLF was auto-approving raw SensoryHub keystrokes as self-edit "proposals" against the hash-verified `echo_principles.json`), and every dead code path now logs or returns an honest "retired"/"disabled" status instead of silently no-opping. This is a genuine, verified improvement in honesty, not just continued dead code. |
| Peripheral top-level scaffold directories are uncontrolled clutter | Still present (18 directories), but the root cause (relative self-edit paths) was fixed 2026-07-08 (path anchoring via `__file__`), so the sprawl is now a historical artifact rather than an ongoing leak — re-swept this pass, zero new secrets found. Two of the eighteen (`RebelCode/`, `WhisperingWires/`) are corrections to the original audit's framing: both are live, tracked, genuinely-used subsystems, not dead scaffolding — see dead_code.md. |
| FAISS reported 0 vectors in both indexes at the original audit, flagged Unable to Determine | Resolved: `memory/` now holds 47,607 real vectors, matching `self_model.json`'s own reported count. `data/`'s legacy 5,348-vector index still exists, untouched, exactly as CLAUDE.md's own FAISS Dual-Index section says it was deliberately left (not a contradiction of that doc, a confirmation of it). |

See dependency_graph.md for the module-level call graph and
architecture_drift.md for a fuller discussion of how the system arrived
here since 2026-07-04.
