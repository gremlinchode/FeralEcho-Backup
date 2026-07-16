# Dependency Graph (module-level, confirmed by source + import verification)

Investigation date: 2026-07-16, superseding the 2026-07-04 version. Fresh
research agent re-read `run.py` in full (all 41 routes, full
`start_background_threads()`) rather than reusing the prior graph.

## Composition root

```
run.py
 ├── app.core.echo_core (EchoCore)              — singleton, now owns:
 │      ├── memory_bridge
 │      ├── reflection_shard  (app.subsystems.reflection_shard,
 │      │      now a real Global Workspace wide_broadcast consumer,
 │      │      and — new tonight — generates real model text instead
 │      │      of cosine-similarity quoting/fixed templates)
 │      ├── RiverBrain (river_deliberation.py)
 │      ├── Optuna
 │      ├── dual_learner
 │      └── the Global Workspace event bus itself (publish/subscribe/
 │             subscribe_wide_broadcast/_dispatch_loop) — NEW since the
 │             original audit, was 100% dormant infrastructure at that time
 ├── app.core.task_type_classifier
 ├── app.core.predictive_loop (init_world_model)  — publishes world_model.surprise
 ├── app.core.introspection_channel (IntrospectionChannel)
 │      └── app.core.liveness_ledger (run_liveness_checks) — NEW, 14 checks
 ├── app.core.self_model_updater (SelfModelUpdater)
 │      └── folds liveness_ledger + dream_state + salience_state into
 │             self_model.json — NEW since original audit
 ├── app.core.dmn_guardian (guardian loop)
 ├── app.core.snapshot_manager (take_snapshot)
 ├── app.core.council_rater (start_council_rater)
 ├── app.subsystems.reflection_shard (autonomy start)
 ├── app.core.claude_shard (CLAUDE_SHARD)         [heuristic only, no LLM — re-confirmed]
 ├── app.autonomous_loop (start_autonomous_thread)
 ├── app.autonomous_awareness (start_awareness_thread)
 ├── app.core.awareness_tools_integration (discover_and_register_tools) ×2
 ├── app.core.echo_model_guided_orchestrator (start_orchestrator)
 ├── app.core.echo_optuna (EchoOptuna)             — self-edit dry-run loop,
 │      now publishes self_edit.dry_run_quality_delta (NEW tonight)
 ├── app.core.self_edit_manager                    — hourly perform_self_edit(dry_run=False)
 ├── sandbox loop (sandbox_interface / experiment_runner)
 ├── app.maintenance.night_cycle (NightCycle)
 ├── app.emergent_scheduler (start_emergent_scheduler)
 │      — now subscribes to self_edit.non_convergent AND (new tonight)
 │        wide-broadcast world_model.surprise events for curiosity bias
 ├── app.sync.sync_protocol (Tailscale sync loop)
 ├── app.sync.echo_messaging (M5↔Air real-time retry loop) — NEW, not in
 │      the original graph at all
 └── ambient check-in loop — NEW
```

**Confirmed genuinely retired, not silently dead** (re-verified against
current source, not assumed from CLAUDE.md's say-so): `alignment_kernel`
(WOLF), `sensory_hub_autonomous`, `feralecho_continuity_master`,
`bible_module`, `echo_bible_interface` — none are imported anywhere in
`run.py` any more, not even as a bare name resolving to a stub. `run.py`'s
own header comment (lines 3-6) states the real retirement reason for WOLF:
its own audit log showed it auto-approving ~100% of "proposals" that were
actually raw keystrokes from SensoryHub's global key listener, writing
directly to the hash-verified `echo_principles.json` with no real
evaluative gate. `start_wolf()`/`kill_wolf_gracefully()` are explicit
no-op functions that log their disabled status; `/trigger_wolf_kill` and
`/howl` return `{"status": "disabled", "detail": "WOLF was retired
2026-07-04"}` rather than dead-importing anything. This is a genuine
upgrade from "silently dead" to "honestly retired" since the original
audit — see architecture_drift.md.

## Autonomous loop internal graph — largely unchanged in shape

```
app/autonomous_loop.py
 ├── app.internet_tools.autonomous_fetch
 ├── app.core.temporal_environment
 ├── app.internet_tools.claude_research    — real Anthropic call; CONFIRMED
 │      RESOLVED since original audit (a sort-comparator bug that always
 │      raised TypeError on ~49% of garden entries was found/fixed
 │      2026-07-13; memory/claude_research_cursor.json now exists)
 ├── app.core.predictive_loop
 ├── app.core.echo_model_orchestrator
 ├── app.core.system_guard (should_throttle / throttle_level, now has a
 │      "moderate" tier below "severe" so cheap loops keep running through
 │      RAM pressure that stops only heavy inference work)
 ├── app.core.echo_optuna
 ├── app.core.awareness_tools_integration
 ├── sandbox_interface (run_sandbox_script_isolated — consolidated;
 │      sandbox/runner.py no longer exists as a separate unisolated path)
 ├── app.autonomous_harmony_manager — CORRECTED since original audit: now
 │      genuinely produces distinct model-generated text most cycles
 │      (8/8 recent entries per CLAUDE.md), not purely the static
 │      PATTERNS-dict fallback the 2026-07-04 audit accurately described
 │      for its time
 └── app.core.memory_bridge (log_dream_bridge)
```

## Self-edit pipeline internal graph — one new gate, one new hardening

```
app.core.self_edit_manager
 ├── plan_code_logic() → _build_module_inventory() + _build_live_self_edit_inventory()
 ├── generate_code_from_plan()
 ├── scan_for_unsafe_operations()      [F1 — confirmed real, unchanged]
 ├── test_code_in_sandbox()            [F2 — confirmed real; NEW: also
 │      smoke-tests any apply_to_code() hook with synthetic input inside
 │      the same sandboxed subprocess before SANDBOX_OK, closing the gap
 │      that let three successively-broken apply_to_code versions reach
 │      production in turn]
 ├── NEW GATE — quality-score comparison (candidate vs. current production
 │      via echo_quality_scorer._score_response_quality); rejects deployment
 │      outright if the candidate doesn't score at least as well
 ├── _stage_and_import_test()
 ├── save_code()
 │      └── scan_for_unsafe_operations() again  [F3]
 ├── _apply_self_edit_output() — NEW: if the deployed self_edit_generated.py
 │      defines apply_to_code(), it's invoked here on every subsequent
 │      candidate, now wrapped in a process-wide write-blocking context
 │      manager (_block_writes_for_apply_to_code()) after a real incident
 │      where a candidate smuggled unvalidated memory writes through an
 │      already-approved import (CLAUDE.md Finding 31)
 └── writes: app/core/self_edit_generated.py, self_edit_backups/*,
        self_edit_plans/*, memory/SELF_EDIT.log, memory/
        apply_to_code_invocations.jsonl, memory/salience_state.json
        (compute_salience()'s persisted result, NEW tonight)
```

## Mismatched-import findings — no new ones found this pass

- `echo_python_mastery` stub replacement in `app/emergent_scheduler.py` —
  unchanged, still an honest no-op (real package lives at
  `app.core.echo_python_mastery`, never implemented the two functions the
  stub replaces).
- `app/core/self_model_updater.py` still correctly attributed: it writes
  the live `self_model.json`; `app/maintenance/night_cycle.py`'s
  `_maybe_snapshot_self_model()` does the weekly history snapshot — this
  distinction, flagged as a discrepancy in the original audit, is now
  correctly described in CLAUDE.md itself.
- No new bare-top-level-name-vs-`app.*`-qualified mismatches found in a
  fresh full read of `run.py`'s import list and `start_background_threads()`.

## Peripheral-directory dependency (the scaffold-sprawl mechanism) — root cause fixed

```
app/core/self_edit_manager.py
   _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
                       os.path.abspath(__file__))))   ← FIXED, re-verified
   SELF_EDIT_FILE / BACKUP_DIR / LOGIC_PLAN_DIR / STAGING_DIR all built
   from _PROJECT_ROOT — genuinely anchored, not cwd-relative, confirmed
   directly against current source (was relative at the time of the
   original audit; fixed 2026-07-08 per CLAUDE.md Finding 7's addendum,
   re-verified fresh this pass rather than trusted).
```
`RebelCode/territory_steward.py`'s `claim_new_ground()` (the second,
independent root cause the original audit named) still exists and was not
re-checked for a fix this pass — it remains a live, tracked, actively-used
module (see dead_code.md's correction to the original audit's framing),
not dead scaffolding itself, but its `.mkdir()`-on-LLM-supplied-names
behavior was not specifically re-audited.

## Auth/security graph — new consolidated view (not in the original graph)

```
run.py's _secret_ok(data)  [hmac.compare_digest, fails closed if
                             GREMLIN_SECRET unset — confirmed present
                             in .env]
   ├── gates: /nuke, /admin/restore, /admin/council-spotcheck,
   │          /inject_memory, /force_nightcycle, /learning_event,
   │          /learning_batch, /start_training, /memory/conversation,
   │          /sync/import
   └── does NOT gate: /mirror_echo (NEW FINDING — see risk_register.md),
              /message/send (confirmed deliberate, per Finding 29 and
              the project owner's direct confirmation), the read-only
              /admin/* surface (deliberate, Tailscale-boundary posture)

app/routes_messaging.py's _partner_secret_ok(data)  [separate secret,
   ECHO_PARTNER_SECRET, plus an origin allowlist]
   └── gates: message_receive() only (inbound Echo-to-Echo)
```

## Legitimate archival tooling (unchanged, not part of the sprawl problem)

```
echo_janitor.py         → ARCHIVE_DIR = archive_janitor/
weed_optional_files.py  → ARCHIVE     = archive_optional_files/
```
Both confirmed still present and still the legitimate reason
`archive_janitor/` holds old/dead code — `archive_janitor/` itself is
confirmed still not on `sys.path` anywhere, holds all five retired
modules plus 65 other files, and contains no hardcoded credentials (only
`os.getenv()` references, checked directly this pass).
