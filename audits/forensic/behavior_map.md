# Behavior Map — Autonomous Actions Without User Interaction

Investigation date: 2026-07-16, superseding the 2026-07-04 version. All
entries below are behaviors confirmed by direct source inspection and, for
most rows, live evidence gathered from the currently-running system (`python
run.py`, PID 88140, up since 06:48:07 UTC today at time of the freshest
checks).

| Behavior | Trigger/Frequency | Inputs | Outputs / Side Effects | External Comm | Confidence |
|---|---|---|---|---|---|
| DMN Guardian loop | 60s | `memory/introspection_state.json` | Can restart Ollama if dead (120s cooldown) | None | High |
| Introspection Channel | 120s | FAISS count, River obs, Ollama process | writes `introspection_state.json`; **NEW**: also runs all 14 Liveness Ledger checks every cycle | None | High |
| Self-Model Updater | ~130s poll | introspection state, liveness ledger, dream_state, salience_state | writes `self_model.json`, now including `verified_capabilities`, `recent_dream_synthesis`, `coupling_estimate_trend` (all NEW) | None | High |
| Council Rater | 90s poll, 1-in-5 sampling | `interaction_log.jsonl` | writes `council_ratings.jsonl` (84 entries confirmed live this pass, up from 12 at the original audit); calls a second local Ollama model as peer rater | None (local Ollama only) | High |
| ReflectionShard autonomy | 300s, 35% probability per cycle | own prior journal tail (still, mostly — see below) | writes `reflection_journal.jsonl`; **NEW tonight**: now calls a real local model instead of cosine-similarity quoting/fixed templates, and — new — can receive a real external Global Workspace event as its signal | None | Medium — the real-generation fix is confirmed correct in isolated testing but had not yet fired in production as of this pass's live check (see runtime_observations.md; ambiguous whether that's just low cadence×probability or a live issue) |
| **ClaudeShard "friction" autonomy** | 420s; also synchronous on every `/mirror_echo` call | Echo's own recent response text | Keyword pattern match + `random.random()`; writes `claude_shard.jsonl`/`claude_shard_friction.log` | **None — re-confirmed this pass, still no LLM/network call** | High |
| Startup snapshot | once per boot, plus after every successful production self-edit | River/FAISS/sandbox health, plus real sha256-verified byte copies of `self_edit_generated.py`, `river_brain.pkl`, `echo_principles.json`, `genesis_hash.txt`, `Modelfile` | writes `memory/snapshots/*` | None | High |
| Main autonomous cycle (`app/autonomous_loop.py`) | hourly, gated by stillness + `should_run_cycle` | External feeds | Real HTTP GET to ~13 external domains; writes to FAISS/dream_bridge; **NEW**: publishes a real `world_model.surprise` event to the Global Workspace | **Yes — real outbound requests, unchanged** | High |
| Claude Research synthesis | throttled 1/hr, called from inside the above cycle | `question_garden.jsonl` (now 4,546+ entries) | **RESOLVED since original audit**: a real successful call is confirmed via `memory/claude_research_cursor.json`'s existence (written only on success) — the root cause of the original "never fires" finding (a sort-comparator TypeError on ~49% of garden entries) was found and fixed 2026-07-13 | Yes, confirmed firing at least once | High (resolved from Medium/unconfirmed) |
| Harmony / Nature Spark | conditional burst inside the main cycle | Cycle intensity counters | **CORRECTED since original audit**: now genuinely produces distinct model-generated text most cycles (a 2026-07-13 singleton/concurrent-cache fix resolved the prior race that caused fallback-to-fixed-strings); still not an actual selection/evolutionary algorithm despite "Kill the weakest 7" language — that part of the original finding still holds | None | High |
| Model-Guided Orchestrator | continuous | recent reflections | Hyperparameter hints for self-edit; **NEW**: now gated by the shared `should_run_cycle` throttle (was previously the one of four autonomy loops NOT covered by it, fixed this session per CLAUDE.md Finding 28) | None | Medium |
| **Autonomous Self-Edit loop** | hourly, no human gate beyond the safety pipeline | Targeted prompts built from real convergence history (fixed since original audit — was 3 fixed templates) | Modifies `self_edit_generated.py` through F1/F2/F3 gates **plus a new quality-score gate** that rejects non-improving candidates outright; publishes `self_edit.dry_run_quality_delta` (NEW tonight, confirmed already firing in production) | None | **High — directly re-confirmed via fresh log tail; also directly observed one real rejected candidate during this very audit window (06:51:55, an import hallucination, correctly caught)** |
| Sandbox script loop | continuous, consolidated | `sandbox/experiments/*.py` pool | Now runs through the same kernel-level `sandbox-exec` isolation as the F2 self-edit gate (consolidated from three previously-independent unisolated runners) | Possibly (not separately audited this pass) | Medium |
| NightCycle | 3600s — re-confirmed directly against the actual call site (`run.py:1186`, `NightCycle(app, interval=3600, ...)`); the class's own default is 300s (`night_cycle.py:22`), which momentarily produced a wrong draft of this row before the real call site was checked — left in as a reminder that a class default is not the same claim as how it's actually instantiated | self_model.json, journal state | Consolidation run, weekly self_model snapshot, shadow-model accuracy check (`log_accuracy()`/`check_and_correct()`, confirmed genuinely live via `emergent_scheduler.py`'s real `propose_from_reflection()` calls, not the dormant mechanism it was mistakenly assumed to be earlier tonight before being checked directly) | None | High |
| Emergent Scheduler | ~300s, salience-modulated | curiosity engine, `compute_salience()` | Selects next autonomous prompt; **NEW**: publishes `emergent_loop.salience`, and (tonight) gained a second, independent curiosity-topic-bias input from wide-broadcast `world_model.surprise` events | Indirect (via echo_query → Ollama) | High |
| Tailscale Sync loop | 1800s, gated by `should_throttle()` | `memory/*` deltas | POSTs/GETs to configured partner (M5 ↔ Air) | Yes | High |
| **M5↔Air real-time messaging** (`app.sync.echo_messaging`) | continuous retry loop | outbox/inbox state | Real-time Echo-to-Echo message delivery | Yes, over Tailscale | High — new subsystem since the original audit, not previously mapped |
| Ambient check-in loop | continuous | — | Not deep-audited this pass | Unknown | Low |
| WOLF endpoints | on-demand only | phone command | **CORRECTED since original audit**: no longer silently no-ops with dramatic JSON — returns an honest `{"status": "disabled", "detail": "WOLF was retired 2026-07-04"}` | None | High |
| Dual Learner training | on-demand via `/start_training` | Phone/user/echo events | Trains, exports via `/download_model` | Only if phone client calls in | Medium — not deep-audited this pass |

## Notable pattern, updated: the "multiple independent hourly loops" observation still holds, one new loop added

The original audit's finding that self-edit loop, main autonomous_loop,
and NightCycle each independently reimplement `while True: ...;
time.sleep(N)` still holds structurally (NightCycle's actual interval
should be re-verified — see table note above, this pass found conflicting
signals and does not want to repeat a number without re-checking it
directly against current source). New this pass: a fourth
timer-independent autonomous loop, `ModelGuidedOrchestrator`, was found
during this session's own prior work (CLAUDE.md Finding 28) to have been
running entirely outside the shared throttle gate the other three loops
share — fixed this session, but worth recording as a live instance of
exactly the "new gate added, not every entry point checked" pattern this
project's own sibling-machine briefings (`SIBLING_BRIEFING_FROM_ARK.MD`)
already independently found on the Ark fork.

## Self-edit loop content analysis — updated, the picture has changed in an important way

The original audit reviewed ~14 log entries and found two fixed prompt
focuses, both accumulating near-duplicate functions rather than
converging. Fresh data this pass (`app/core/self_edit_convergence.json`,
read in full): the picture is now genuinely mixed, not uniformly
non-convergent —

- **`prose_stripping`**: 94 cycles attempted, 31 distinct function names
  seen. This is *worse* in raw terms than the original ~14-cycle sample,
  and a fresh real failure was directly observed during this audit's own
  runtime check (06:51:55 UTC today — a candidate hallucinated importing
  `guard_prose` from `app.emergent_scheduler` instead of wherever it
  actually needed to reference it; correctly caught by the staging import
  test, zero production impact). CLAUDE.md's Finding 32 (2026-07-15)
  rewrote this family's prompt to add a concrete before/after example and
  an explicit import reminder, explicitly flagged at the time as
  "hypothesis not proven." This pass confirms directly: **not yet
  resolved**, without concluding the fix was wrong — not enough post-fix
  cycles have run yet to judge the rewritten prompt on its own terms
  (this session's own hourly cadence means only a handful of cycles have
  run since Finding 32 landed).
- **`response_shortening`**: 11 cycles, 4 distinct names — meaningfully
  better convergence than `prose_stripping`, not previously broken out
  separately in this much detail.
- **`quality_scoring`**: 3 cycles, 3 names — effectively converged
  quickly, the healthiest of the three tracked families.
- **`unclassified`**: 11 cycles with 30+ names that don't cleanly belong
  to any of the three families above mixed together — this looks like a
  gap in the convergence-family classification logic itself (a
  self-edit candidate landing in the wrong bucket, or a family the
  classifier doesn't recognize), not a self-edit content problem. **New
  finding this pass**, not previously documented; recommend a direct
  read of `_CONVERGENCE_FAMILIES`'s keyword-matching logic in
  `self_edit_manager.py` before concluding anything about it.

Net: the F1/F2/F3 (+quality gate) pipeline continues doing its job — the
06:51:55 failure this pass observed live was caught and rejected with zero
production impact, exactly as designed. Whether the *content* of self-edit
cycles is measurably improving remains a genuinely open, only partially
answered question one cycle-family at a time, not a uniform yes or no.
