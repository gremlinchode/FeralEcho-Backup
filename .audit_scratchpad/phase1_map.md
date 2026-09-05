# Phase 1: Repository Mapping (raw notes)

## Repo identity
- Working dir: git worktree of FeralEcho, main repo at /Users/richietate/Desktop/FeralEcho
- Branch: worktree-agent-abe6ecca0408fd0fb (agent worktree)
- Remote: git@github.com:gremlinchode/FeralEcho-Backup.git
- 114 commits total, first 2026-06-28, last 2026-07-22 (~3.5 weeks of history)
- Tracked files: 2125 (git ls-files)
- Total tracked bytes: ~69MB
- memory/ and data/ directories are gitignored and NOT PRESENT in this worktree checkout (runtime state, not code)

## File extension breakdown (tracked)
- 547 .txt
- 236 .py
- 90 .json
- 49 .md
- 6 .sh
- 3 .save, 3 .jsonl, 3 .bak, 2 .pkl, 2 .csv
- Many hundreds of files with backup-timestamp "extensions" like .20260625_073834 (these are actually
  sandbox/scripts/archive/temp_self_edit*.py.<timestamp> snapshot files, NOT real distinct extensions)

## LOC
- 236 tracked .py files, 50,356 total lines (via wc -l) -- but this INCLUDES ~1167 archived
  self-edit snapshot .py-suffixed-with-timestamp files under sandbox/scripts/archive/, which
  inflates the .py count/LOC substantially. Need to separate "real" source from generated snapshots.

## Top-level directory breakdown (git ls-files, files with a "/" in path)
1185 sandbox       (1167 are sandbox/scripts/archive/* timestamped snapshots; only ~18 real files)
 615 app
  70 archive_janitor
  66 books           (Bible JSON data, per-book)
  22 archive_optional_files
  21 audits
  18 echo_studio     (separate PyQt desktop app)
  15 council
   4 RebelCode
   3 scripts
   2 WhisperingWires
   2 messages
   2 claude_relay
   1 staging
   1 logs
   1 FeralEcho        <- suspicious: nested self-referential dir, contains only
                          FeralEcho/app/stillness/silence.jsonl (328KB)
   1 backup

## app/ subdirectory breakdown
588 app/core
  4 app/internet_tools
  3 app/sync
  2 app/maintenance
  2 app/lib
  1 app/subsystems
  1 app/learning

## sandbox/scripts breakdown -- CONFIRMED DEAD WEIGHT / REPO BLOAT
- 1167 files under sandbox/scripts/archive/ are git-TRACKED, timestamped
  (temp_self_edit.py.<YYYYMMDD_HHMMSS>, temp_self_edit_retry.py.<timestamp>), dated 2026-06-21
  through 2026-06-28 -- i.e. an entire early week of self-edit sandbox test snapshots was
  committed to git before a later .gitignore rule ("sandbox/scripts/archive/") was added.
  gitignore does NOT retroactively untrack already-committed files, so these 1167 files
  (4.6MB) remain in the repo and its history forever unless explicitly `git rm`'d.
- Only 2 real files exist directly in sandbox/scripts/: hello_sandbox.py, temp_self_edit.py
  (temp_self_edit.py itself is a live/current working-tree-modified file per initial git status)

## app/core/self_edit_plans/ -- ALSO CONFIRMED DEAD WEIGHT, SAME CLASS OF BUG
- .gitignore lists "app/core/self_edit_plans/" (would exclude going forward)
- BUT 500 files are still git-tracked under this path (again: pre-ignore-rule commits never untracked)
- Filenames: plan_<YYYYMMDDHHMMSS>.txt, dated 2026-06-25 range in the head of the list
- Exactly 500 -- suggests some retention/prune cap exists somewhere in the codebase (not confirmed yet)

## app/core/app/core/self_edit_backups/ -- LIVE EVIDENCE OF THE RELATIVE-PATH SELF-EDIT BUG
- Real, git-tracked, nested duplicate path: app/core/app/core/self_edit_backups/self_edit_<ts>.py
  and app/core/app/core/self_edit_plans/plan_<ts>.txt, all dated 2025-11-16 (much older than the
  rest of repo's June/July history -- pre-dates git history start of 2026-06-28, meaning these
  files were carried into the very first commit already in this broken nested shape).
- This is DIRECT, INDEPENDENT EVIDENCE (not taken from any doc) that self_edit_manager.py's
  write-target path constants were, at some point, relative rather than anchored to project root
  -- when invoked from a cwd of app/core/ (or similar), it recreated its own app/core/... scaffold
  one level deep inside itself.
- [VERIFIED] via direct git ls-files output.

## No dependency manifest at all
- No requirements.txt, no pyproject.toml, no Pipfile, no environment.yml anywhere in tracked files.
- condaenv.m446rkpc.requirements.txt exists at root but is 0 bytes (empty).
- [VERIFIED] Repo has NO reproducible-environment file. All deps must be inferred from actual
  `import` statements. This is a real production-readiness gap.

## Root-level Python entry points (files with `if __name__ == "__main__"`)
Real/live-looking (not under archive_janitor/archive_optional_files/sandbox archive):
- run.py (main Flask server, 61KB)
- terminal_client.py (28KB, secondary CLI entry point)
- thunderhead.py (35KB, phone-symbiote reference client)
- echo_json_server.py (4KB, standalone Flask app, separate from run.py)
- echo_cartographer.py, echo_janitor.py, echo_quality_scorer.py, river_creative_rehab.py,
  spot_check.py, verify_riverbrain.py -- root-level manual/diagnostic scripts
- echo_studio/main.py -- separate PyQt desktop app entry point
- Many app/core/*.py files ALSO have __main__ guards (self-test blocks), e.g.
  echo_model_orchestrator.py, memory_bridge.py, seam_engine.py, project_learner.py, etc.
- archive_janitor/*.py (~40 files) all have __main__ guards too but archive_janitor is confirmed
  NOT importable from run.py's cwd (see below) -- these are frozen/dead.

## Flask route surface
- run.py: 42 @app.route() decorators (confirmed via grep)
- echo_json_server.py: separate Flask app, its own routes (binds same port 5000 per its own
  apparent design -- would conflict with run.py if both run)
- app/routes_echo_studio.py (720 lines) and app/routes_messaging.py (130 lines): NOT decorated
  with @app.route themselves -- run.py imports them lazily inside each route handler function
  and calls the corresponding bare function, e.g.:
    @app.route("/chat/stream", methods=["POST"])
    def _chat_stream():
        from app import routes_echo_studio
        return routes_echo_studio.chat_stream()
  This is a real, consistent "thin wrapper, logic lives in dedicated module" pattern, confirmed
  by reading both files' own docstrings, which independently state this convention.

## Auth audit (run.py + routes_echo_studio.py + routes_messaging.py) -- via grep for _secret_ok/_partner_secret_ok
run.py routes WITH _secret_ok() gate confirmed: force_nightcycle, inject_memory, learning_event,
  learning_batch, start_training, mirror_echo (POST, gated), memory/conversation, admin/restore,
  admin/council-spotcheck, sync/export (GET, gated via request.args), sync/import
run.py routes WITHOUT any _secret_ok() call (confirmed via absence of nearby grep hit):
  /ip, /symbiote_location, /symbiote_status, /trigger_wolf_kill, /download_model, /howl, /state,
  /sensory_status, /api/modelfile/proposal, /chat/stream, /chat/regenerate, /dashboard/health,
  /memory/search, /memory/browse, /activity/log, /projects/tree, /projects/file, /settings/view,
  /health, /admin/snapshots, /admin/council-stats, /admin/self-edit-outcomes, /admin/autonomy-status,
  /admin/liveness-status, /sync/genesis, /sync/state
  (/nuke has its OWN inverted-logic secret check, not a bare "if not _secret_ok" -- flagged for closer read)

routes_echo_studio.py: grep for `_secret_ok` across the WHOLE file returns ZERO hits.
  -> chat_stream, chat_regenerate, dashboard_health, memory_search, memory_browse, activity_log,
     projects_tree, projects_file, settings_view are ALL unauthenticated. [VERIFIED]

routes_messaging.py:
  - message_receive(): gated via _partner_secret_ok() + an origin allowlist check (own separate
    ECHO_PARTNER_SECRET, distinct from GREMLIN_SECRET) [VERIFIED]
  - message_send(): NO secret_ok call anywhere in the function body -- confirmed by direct Read of
    the function; its own docstring explicitly states this is INTENTIONAL ("Intentionally
    unauthenticated... Tailscale network boundary is the access control here") [VERIFIED]
  - message_inbox(): NO secret_ok call anywhere in the function body [VERIFIED] -- this returns
    echo_messaging.get_recent_messages(limit) directly via jsonify with NO auth at all. Need to
    check get_recent_messages()/the envelope shape for whether it leaks ECHO_PARTNER_SECRET
    (flagged for phase 2.5 deep dive).
  - message_settings(): GET unauthenticated (returns settings), POST gated via _secret_ok(data)
    [VERIFIED]

