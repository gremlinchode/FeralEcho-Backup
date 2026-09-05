# Phase 2: Dependency Graph (raw notes)

Method: custom AST-based import scanner (.audit_scratchpad/depgraph.py + orphans.py),
scanning app/, sandbox/ (excl. archive), echo_studio/, council/, RebelCode/, scripts/, and
root-level .py files (144 files total, excludes archive_janitor/, archive_optional_files/,
sandbox/scripts/archive/, self_edit_backups/, self_edit_plans/). Captures both `import X` and
`from X import Y` (including the Y-as-submodule case, fixed after an initial false-positive pass).

## Confirmed genuine zero-inbound-importer files in app/core/ (static analysis + grep cross-check)
- app/core/council_registry.py -- small singleton registry class (CouncilRegistry), no callers
  anywhere. Superseded-looking design (echo_core.py's EchoCore likely does this job instead).
- app/core/load_project_map.py -- real function load_project_map(echo_instance, project_path)
  that would feed the whole project's module map into memory_bridge on startup. Zero live
  callers -- echo_core.py has a SAME-NAMED METHOD (self.load_project_map) that is unrelated
  (false-positive trap for naive grep). Genuinely disconnected capability, not literal dead code.
- app/core/memory_migration.py -- has __main__ guard, one-time data-migration script (data/ ->
  memory/ merge). Zero live callers. Consistent with "already run once, kept for reference" shape.
- app/core/scheduler.py -- a well-designed, documented "opt-in" shared tick-dispatcher, explicitly
  self-described in its own docstring as "additive and standalone... migration is a separate,
  reviewed step per subsystem, not automatic." Zero live callers -- confirms via its own docstring
  that adoption was planned but never executed. Real, sound, unused infrastructure.
- app/core/self_report_verifier.py -- zero real imports; only 3 hits anywhere are CODE COMMENTS
  in dmn_guardian.py/liveness_ledger.py describing that its logic "used to run here" / was
  "absorbed" elsewhere. Confirms deliberate retirement-in-place (function code kept, call site
  removed), not accidental dead code.
- app/core/self_heal.py -- zero direct `import` callers anywhere. BUT it is *referenced indirectly*
  by a live, working mechanism: routes_echo_studio.py's dashboard_health() reads run.py's own
  SOURCE TEXT at runtime (`"import app.core.self_heal" in line`) to report whether it's been
  reconnected -- a real, working "is this still disconnected" health-check via string search,
  not a real import. Genuinely disconnected functionality, correctly self-aware about its own
  disconnection state.
- app/core/shard.py -- small generic Shard class (owner/memory/growth_factor), zero callers.
  Distinct from app/subsystems/reflection_shard.py (which IS live, see below).
- app/core/config.py -- FALSE POSITIVE from initial scan (import-from-submodule form wasn't
  caught by first pass of AST scanner); re-verified: not checked individually beyond the fixed
  graph re-run, no longer shows as strict zero -- not conclusively re-examined line by line in
  this pass; treat as [HYPOTHESIS] possibly still has few/no real config-value consumers, not
  independently confirmed either way. NEEDS FOLLOW-UP if precision required.
- app/core/self_edit_generated.py -- FALSE ORPHAN. Confirmed self_edit_manager.py loads this file
  DYNAMICALLY via `importlib.util.spec_from_file_location(..., SELF_EDIT_FILE)` (a path string,
  SELF_EDIT_FILE = ".../app/core/self_edit_generated.py"), not a static `import` statement --
  invisible to AST-import-graph analysis by design, but this file IS load-bearing/live. Do not
  classify as dead code.
- app/core/temp_self_edit.py -- a genuinely tiny (7-line) DATA-ONLY file (a list of regex
  pattern/replacement dicts for spiritual-affirmation text substitution), sitting directly in
  app/core/ (not staging/ or self_edit_backups/ where such artifacts normally live). Zero
  importers anywhere. Looks like a stray self-edit-generated or manually-dropped artifact that
  landed in the wrong directory. Very low removal risk but recommend flagging rather than
  deleting outright (small, harmless, possibly meaningful test fixture).

## Modules with exactly 1 inbound importer (thin, single-consumer -- not necessarily orphaned,
   but worth knowing which single file would break if these were removed)
autonomous_loop_with_optuna.py <- echo_model_guided_orchestrator.py
bible_injection.py <- echo_model_orchestrator.py
curiosity_engine.py <- app/emergent_scheduler.py
dark_light_pipeline.py <- run.py
echo_model_guided_orchestrator.py <- run.py
echo_review_mastery.py <- self_edit_manager.py
introspection_channel.py <- run.py  (surprising -- this is a documented core subsystem; its
  ONLY direct static importer is run.py itself, which then presumably passes it around / the
  module functions are called via a singleton pattern elsewhere -- needs runtime confirmation,
  not necessarily a problem, just notable architecture: run.py is the wiring hub)
modelfile_proposer.py <- run.py
sandbox_interface.py <- run.py
wolf_friction_bridge.py <- echo_model_orchestrator.py

## Fan-in "hub" modules (highest inbound import count -- central, load-bearing, high blast radius)
24  app/core/memory_bridge.py
19  app/core/echo_model_orchestrator.py
10  app/core/echo_core.py
 8  app/core/autonomy_coordinator.py
 7  app/core/predictive_loop.py, app/core/snapshot_manager.py, app/core/stillness_state.py
 6  app/core/echo_ground_truth.py

## Root-level entry points confirmed importable / real
- run.py: the real Flask server, 42 @app.route() handlers, imports ~20+ app.core.* modules
  directly plus lazily imports app.routes_echo_studio / app.routes_messaging inside handlers.
- terminal_client.py: secondary CLI entry point, imports river_deliberation, self_edit_manager,
  echo_tool_context, liveness_ledger directly -- genuinely wired to the same core pipeline.
- echo_studio/main.py: separate PyQt6(?) desktop app, imports its own echo_studio/* views/state
  modules -- talks to run.py's Flask server over HTTP (client), not a direct Python dependency
  on app/core/. [NOT DEEPLY VERIFIED -- inferred from directory structure + naming, flagged
  HYPOTHESIS pending a direct read of echo_studio/main.py]
- echo_json_server.py: standalone Flask app at root, own routes (@app.route in same grep),
  same port 5000 as run.py by inspection of its own bind call -- FLAGGED for direct verification
  in ghost-code phase (would conflict with run.py if both run simultaneously).

## archive_janitor/ -- confirmed structurally isolated
- 70 tracked files, all with their own __main__ guards (standalone scripts)
- NOT in the scanned import graph above by design (excluded via SCAN_DIRS list) but a direct
  grep of run.py / app/ for "archive_janitor" import statements returns nothing importable from
  a normal cwd (module not on sys.path) -- consistent with dead/frozen migration-leftover status.
  [Confirmed via grep -rn "archive_janitor" across app/ + run.py: only comment references, no
  real import statements found.]
