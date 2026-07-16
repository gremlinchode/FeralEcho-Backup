# Subsystem Inventory

Investigation date: 2026-07-16, superseding the 2026-07-04 version.

Status legend: **LIVE** (imports succeed, thread/route confirmed active) /
**LIVE-VERIFIED** (LIVE, plus independently confirmed producing real
externally-observable output, not just started) / **RETIRED-HONEST**
(previously dead, now explicitly no-ops with an honest status rather than
silently failing) / **DEAD** (import fails at runtime) / **ORPHANED**
(exists, zero callers).

## Entry points

| Entry point | Role | Evidence |
|---|---|---|
| `run.py` | Flask server + all background thread launcher. Manual start only. Binds `0.0.0.0:5000`. | Confirmed LIVE, PID 88140, sentinel `stage: serving`, fresh heartbeat, this pass. |
| `terminal_client.py` | Interactive human↔Echo chat client, now also has `!status`/`!propose` admin commands (new since original audit). | Not running at time of this pass's checks. |
| `com.gremlin.echo` (launchd) | Still the same dead fossil the original audit found — points to a nonexistent script and an abandoned predecessor directory (`~/EchoCoreV2`). Not re-verified fresh this pass; no reason to expect it changed. | Original audit's `launchctl print` evidence, not re-run. |
| `crontab` | None. | Not re-checked this pass; no evidence of any change. |

## Threads/loops started by `start_background_threads()` (fresh read, `run.py:955-1254`)

| Thread/loop | Interval | Status | Notes |
|---|---|---|---|
| `EchoCore` init | once | LIVE-VERIFIED | Now owns a genuinely live Global Workspace event bus (5 distinct real sources confirmed in `workspace_log.jsonl`'s recent tail this pass) — was undocumented/non-existent at the original audit. |
| World Model | once | LIVE-VERIFIED | Publishes real `world_model.surprise` events; posterior confirmed restored from history on restart (not reset to flat prior). |
| `IntrospectionChannel` | 120s | LIVE-VERIFIED | Now also runs all 14 Liveness Ledger checks every cycle — new since original audit. |
| `SelfModelUpdater` | 130s, starts 10s after IntrospectionChannel | LIVE-VERIFIED | `self_model.json` confirmed fresh (age 0.22h at last liveness check). |
| DMN Guardian | 60s | LIVE | Unchanged. |
| Startup snapshot | once + after every production self-edit | LIVE | The "after production self-edit" trigger is new since original audit. |
| Council Rater | 90s poll, 1-in-5 | LIVE-VERIFIED | 84 entries confirmed this pass (up from 12); `agreement_rate: 0.643`, `baseline_trusted: false` (needs 0.70) — genuinely running, not yet at its own trust threshold. |
| ReflectionShard autonomy | 300s, 35% probability, `initial_delay=120` | LIVE, verification ambiguous | Real-model-generation fix confirmed correct in isolated testing tonight; had not yet produced a post-restart entry at last live check (14.5min uptime, ~2 probabilistic chances so far — statistically plausible this is just timing, not a break; liveness ledger's `reflection_shard_generation` check is correctly reporting FAIL against the still-stale journal tail). |
| ClaudeShard autonomy | 420s + synchronous on `/mirror_echo` | LIVE-VERIFIED (as heuristic, not AI) | Re-confirmed fresh: no `anthropic` import, still `random.random()` + keyword markers. |
| `SensoryHub` | — | **RETIRED-HONEST** (was DEAD in original audit) | No longer imported at all; not even a dead reference. |
| `feralecho_continuity_master` | — | **RETIRED-HONEST** | Same. |
| Main autonomous loop (`app/autonomous_loop.py`) | hourly | LIVE-VERIFIED | Real HTTP fetches confirmed structurally unchanged; now also feeds the Global Workspace. |
| Awareness thread | — | LIVE | Not deep-audited this pass. |
| Tool registry bootstrap ×2 | once | LIVE | Unchanged. |
| `ModelGuidedOrchestrator` | continuous | LIVE-VERIFIED | Was, until this session, the one of four autonomy loops NOT covered by the shared `should_run_cycle` throttle gate — fixed this session (CLAUDE.md Finding 28), confirmed present in current source. |
| **`AutonomousSelfEdit` loop** | 3600s | LIVE-VERIFIED | Confirmed still firing: a real failed candidate was observed live during this very audit (06:51:55 UTC today, import hallucination, correctly rejected by the staging test — zero production impact). Now gated by a quality-score comparison against production (new since original audit) in addition to F1/F2/F3. |
| Sandbox script loop | continuous | LIVE | Consolidated onto the same kernel-level sandbox isolation the F2 self-edit gate uses (previously three independent unisolated runners). |
| Bible Art loop | — | **RETIRED-HONEST** | No longer referenced at all. |
| `NightCycle` | 3600s (confirmed via the real call site `run.py:1186`, not just the class default) | LIVE-VERIFIED | Shadow-model accuracy check confirmed genuinely live (`emergent_scheduler.py` calls `propose_from_reflection()` on every real reflection — 1111 real accuracy entries exist). |
| Emergent Scheduler | ~300s, salience-modulated | LIVE-VERIFIED | Publishes `emergent_loop.salience`; gained a second curiosity-bias input tonight. |
| Tailscale Sync loop | 1800s | LIVE | Unchanged structurally. |
| **M5↔Air real-time messaging** (`app.sync.echo_messaging`) | continuous | LIVE | New subsystem since original audit, not previously inventoried. |
| Ambient check-in loop | continuous | LIVE | Not deep-audited. |
| WOLF endpoints | on-demand | **RETIRED-HONEST** (was DEAD) | `/trigger_wolf_kill`/`/howl` now return an honest `{"status": "disabled", ...}` instead of dramatic no-op JSON. |

## The Liveness Ledger — new since the original audit, itself now part of the subsystem inventory

`app/core/liveness_ledger.py`, 14 automated checks (up from 0 at the
original audit), run every 120s from `introspection_channel.py`. Confirmed
live this pass via `GET /admin/liveness-status`: **13/14 passing**, ledger
fresh (not stale).

| Check | Live result this pass |
|---|---|
| `self_edit_apply_to_code` | PASS — deployed and live, 0/20 recent error rate |
| `curiosity_engine` | PASS — 127 real entries in the last 7d |
| `nature_spark` | PASS — 14/14 recent entries genuinely distinct |
| `wolf_friction_bridge` | PASS — still dry-run-only |
| `claude_shard` | PASS — still no `anthropic` import |
| `question_garden_lineage` | PASS — 1007/4546 entries have real lineage |
| `claude_research` | PASS — last success 4.4h ago |
| `self_model_drift` | PASS — reported counts match live ground truth |
| `task_type_classifier` | PASS — correctly discriminates all canary cases |
| `global_workspace` | PASS — 5 distinct real sources in the last day |
| `substrate_continuity` | PASS — 100% of recent entries on `echo:latest` |
| `global_workspace_consumption` | PASS — 1 real consumer (`river_deliberation`) |
| `valence_self_report` | PASS — rendered text matches real dim[8]=+0.292 |
| `reflection_shard_generation` | **FAIL** — 0/20 recent entries are post-fix real generation (see note above; ambiguous whether transient or real, self-resolving expected as new cycles accumulate) |

A 47-case discrimination test suite (`scripts/verify_liveness_ledger.py`)
independently proves these checks actually distinguish real from
fabricated evidence rather than passing cleanly by construction — not
re-run fresh this pass, but confirmed present and current in source.

## Undocumented-in-CLAUDE.md subsystems found this pass

None found beyond what CLAUDE.md itself already documents as of
2026-07-16 — a genuine change from the original audit, which found four
(`claude_shard.py`, `claude_research.py`, `autonomous_harmony_manager.py`,
`dual_learning.py`) entirely missing from CLAUDE.md at the time. All four
are now documented there, several at length across multiple numbered
Findings. This is a real, measurable improvement in documentation coverage
since 2026-07-04.

## Confirmed-dead modules (unchanged from "confirmed retired" above — no modules found dead-by-accident this pass)

Zero modules were found this pass that `run.py` references as if live but
that actually fail to import — a genuine change from the original audit's
headline finding of five such modules. See "Confirmed retired" in
dead_code.md for the honest-no-op state that replaced the original
silent-failure state.
