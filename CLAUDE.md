# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Starting the System

```bash
# Activate environment and start the Flask server
source ~/miniforge3/etc/profile.d/conda.sh
conda activate feral_echo
python run.py
# Server binds to 0.0.0.0:5000 — Tailscale is the security boundary

# Interactive terminal (talk to Echo)
python terminal_client.py

# Restart after code changes — always kill the existing server first.
# Starting python run.py while port 5000 is occupied causes the new process
# to die silently inside start_background_threads() with no error message.
kill $(lsof -ti :5000) && python run.py
```

Ollama must be running before `run.py` starts. If it isn't: `ollama serve`. Echo's primary model is dynamically discovered via `list_ollama_models()` in `echo_model_orchestrator.py` — whatever models are pulled in Ollama are available automatically.

---

## Running Tests

```bash
# Smoke test (safe, sandboxed)
python -m pytest sandbox/experiments/test_smoke.py

# Syntax-check a specific module without running it
python -c "import ast; ast.parse(open('app/core/some_file.py').read()); print('OK')"

# Import-test a staged self-edit before committing
python -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('_test', 'staging/self_edit_candidate.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('IMPORT_OK')
"
```

There is no project-wide test suite. The sandbox in `sandbox/experiments/` provides isolated smoke tests. All sandbox scripts run with writes blocked outside `sandbox/` and network modules nulled.

---

## Architecture

### Primary Call Path (user conversation)
```
terminal_client.py
  → echo_query()                     # app/core/echo_model_orchestrator.py
    → river_deliberation._ollama_query()   # app/core/river_deliberation.py
      → stream_query_ollama()        # app/ollama_handler.py  (streaming HTTP)
        → Ollama HTTP API :11434
    [fallback subprocess if HTTP fails — uncapped, fires only on HTTP failure]
```

### Autonomous Background Path
```
emergent_scheduler.py (emergent_loop)
  → select_next_prompt()  [curiosity engine + B2 recency check + coherence boost]
  → echo_query()          [same call chain as above]
  → log_interaction()     [memory/interaction_log.jsonl]
  → log_dream_bridge()    [memory/dream_bridge.log → FAISS]
```

**Additional autonomous subsystems (previously undocumented, found via forensic audit 2026-07-04):** the emergent scheduler above is not the only background cycle. `app/autonomous_loop.py` runs its own independent ~3600s cycle (separate `time.sleep(3600)`, gated by a stillness check and `should_throttle()`) that does real outbound HTTP fetches from ~13 external sources (Wikipedia, arXiv ×3, BBC, NPR, Guardian, Reddit ×3, StackOverflow, Hacker News, optionally NASA/NewsAPI) plus the `claude_research.py` Anthropic call described in the Wolf Friction Bridge section above, and conditionally hands off to `app/autonomous_harmony_manager.py` ("Harmony"/"Nature Spark") — despite alarming log lines like `EVOLUTIONARY_PRESSURE → Kill the weakest 7`, this is confirmed to be purely cosmetic reflective-text generation from a static string dictionary, not an actual selection algorithm; it logs to `WhisperingWires/thoughts.log` and `WhisperingWires/harmony.log`. Separately, `app/learning/dual_learning.py` (`dual_learner`) is a full ML ingestion/training pipeline exposed via `/learning_event`, `/learning_batch`, `/start_training`, `/download_model` for the iPhone mirror client — not previously documented here and not deep-audited beyond confirming it is live and wired.

### Token Limits by Task Type (app/core/echo_model_orchestrator.py: _TASK_TOKEN_LIMITS)
- `personal`, `autonomous_*` → 512 tokens (reflections stay concise)
- `reasoning`, `general`, `creative` → 1024 tokens
- `coding` → 2048 tokens

### FAISS Dual-Index (known split-brain)
`memory_bridge.py` writes to `memory/memory_meta.json` + `memory/faiss.index` — this is the authoritative path used by all runtime code. `app/lib/vector_memory.py` writes to `data/memory_meta.json` + `data/faiss.index` — a secondary path used by some legacy callers. They are separate indexes. Always use `memory_bridge.py` for new code.

### Self-Edit System
Echo autonomously modifies `app/core/self_edit_generated.py` only. The pipeline:
1. `perform_self_edit()` — global 60-min cooldown blocks storm conditions
2. `plan_code_logic()` — generates numbered plan, injects current file contents + module inventory
3. `generate_code_from_plan()` — generates Python only, strips markdown fences
4. `_stage_and_import_test()` — subprocess import test in `staging/` before touching production
5. `backup_existing_code()` + `save_code()` — atomic write with backup

The cooldown is a global in-memory `_last_any_autonomous_edit: float` — it resets on server restart. If the self-edit loop is producing rapid `sandbox_syntax_failure` entries in the interaction log, this is a prompt/model hallucination storm; restart the server to reset the cooldown.

**Confirmed live trigger (forensic audit 2026-07-04):** a dedicated module-level loop in `run.py` (`self_edit_loop`, thread name `AutonomousSelfEdit`) calls `EchoOptuna().optimize_self_edit(n_trials=10)` then `self_edit_manager.perform_self_edit(dry_run=False)` unconditionally every `time.sleep(3600)` — this is separate from the Model-Guided Orchestrator (Finding 5 below) and from the Wolf Friction Bridge dry-run path. Verified genuinely firing: `memory/SELF_EDIT.log` showed real success/failure entries every ~62 minutes continuously for 17+ hours of uptime, and `app/core/self_edit_generated.py`'s mtime matched the last successful entry exactly. The F1 (AST scan) / F2 (`sandbox-exec` + `SANDBOX_OK` check) / F3 (post-write AST scan) pipeline was independently re-verified against source during that audit and is accurately described above. Observed content quality issue: successive hourly cycles tend to re-implement near-duplicate helper functions (e.g. `strip_sandbox_prose`, `strip_sandbox_prose_in_code`, `new_strip_sandbox_prose_in_code`, `strip_leading_prose`) targeting the same "prose in code output" prompt rather than converging on one implementation — the safety gates are working, but the loop is not demonstrably improving over time.

### Machine-Native Awareness (added 2026-06)
- **`app/core/echo_state.py`** — 8D float32 state vector, updated every 120s, persisted to `memory/echo_state.npy`. Dim [3] = system_vitality (1 - RAM/100). Dim [7] = circadian signal.
- **`app/core/curiosity_engine.py`** — self-generated goals via WorldModel topic under-representation → `data/question_garden.jsonl`
- **`app/core/shadow_model.py`** — tracks whether Echo's self-assessments match actual outcomes
- **`app/core/system_guard.py`** — reads `echo_state.npy` dim [3]; returns True (throttle) when RAM > 92%. Called at the top of autonomous loops.

---

## Self-Edit Safety Pipeline (F1/F2/F3)

Three independent gates in `app/core/self_edit_manager.py`. Each is independently sufficient to block the most common failure modes. All three run on every autonomous edit attempt.

**F1 — Pre-run AST scanner** (`scan_for_unsafe_operations()`, line 220)
Parses generated code and walks the AST before any execution. Unconditionally blocks: `exec()`, `eval()`, `os.system/popen/execv/spawn*`, `subprocess.call/run/Popen/check_*`, `shutil` copy/move/rmtree, `Path.write_text()`, `Path.write_bytes()`. Also blocks any `open()` call targeting a forbidden path or whose path is statically unresolvable. Raises `ValueError` listing all violations; the edit aborts before any subprocess is spawned. Must run before F2.

**F2 — Kernel + Python sandbox** (`test_code_in_sandbox()`, line 699; `sandbox-exec -f echo_sandbox.sb`)
Runs the code inside a macOS `sandbox-exec` profile that blocks all filesystem writes outside `sandbox/`. Also monkeypatches Python builtins inside the wrapper so write attempts that evade the profile raise at the Python layer. The subprocess must exit 0 and emit `SANDBOX_OK`; any other result aborts the edit.

**F3 — Post-write AST scan before load** (`save_code()`, line 632)
After the file is written to disk and before it is loaded into the running process, `scan_for_unsafe_operations()` runs again on the on-disk content. Catches discrepancy between what was generated and what was actually written. If this scan fails, the file is not loaded.

**Layering:** pre-run static gate → kernel + Python sandbox → post-write static gate. Each gate is independently sufficient. Ordering ensures no executable code runs before both static gates pass.

**Known residual gap:** Third-party C extensions loaded by generated code can execute arbitrary native code below the Python monkeypatch layer. The F1 AST scanner cannot see inside C extension behavior. This is the current safety floor; it is a known and understood boundary, not a hidden gap.

**Known static-analysis limit:** Dict-subscript paths (e.g., `d["__builtins__"]`) are not caught by the static variable-string collector. The AST scanner catches the common cases; the kernel sandbox is the backstop for cases it misses.

---

## Wolf Friction Bridge

**`app/core/wolf_friction_bridge.py`** — connects ClaudeShard friction events to Echo's self-edit pipeline. Currently disabled at the call site: the call in `echo_model_orchestrator.py` (~line 1144) invokes `simulate_self_edit()`, not `perform_self_edit()`.

**`simulate_self_edit()`** (line 149): receives a friction event dict, runs the full generation pipeline (plan → generate → F1/F2 scan), logs results to `memory/wolf_dryrun.jsonl`, and stops. It does not call `save_code()`, does not load the candidate into the running process, and produces no River training signal.

**Dry-run log fields:** `timestamp`, `friction_question`, `candidate_code_preview`, `f1_passed`, `f2_passed`, `would_have_applied`.

**`memory/wolf_dryrun_window.json`** — **DISCONNECTED DEAD CODE.** Described above as tracking window state, but grep of the entire codebase finds zero Python files that read or write this file. It is mentioned in prior CLAUDE.md versions as if active, but no code ever implemented it. Do not treat this file as a live state signal — it does not exist in practice and would not be updated if it did. (Audited 2026-07-03.)

Reactivating the live friction bridge — replacing `simulate_self_edit()` with `perform_self_edit()` — is a deliberate future decision requiring human confirmation. It is not the default outcome when the dry-run window closes.

**Important disambiguation (forensic audit 2026-07-04):** "ClaudeShard" (`app/core/claude_shard.py`, `CLAUDE_SHARD` singleton, started in `run.py`) is a **completely different subsystem from the WOLF/`alignment_kernel.py` subprocess** described nowhere else in this doc but present in `run.py` (`start_wolf()`/`kill_wolf_gracefully()`, `/trigger_wolf_kill`, `/howl` endpoints). The two share "wolf/friction" naming but are unrelated code paths — do not conflate them:
- **ClaudeShard is NOT an LLM call of any kind.** Despite its identity string ("Claude - Friction Engine - FeralEcho Council") and the "friction" vocabulary, `assess()` is pure keyword-substring matching against a hardcoded `SMOOTHNESS_MARKERS` list (`"certainly"`, `"of course"`, etc.) plus `random.random() < 0.28` gating — verified by full source read. It makes no network call and does not import `anthropic`. Its autonomy thread runs every 420s and is wired into `/mirror_echo`. Treat any "friction" flag from it as a coin flip with cosmetic dressing, not a model-derived signal.
- **WOLF/`alignment_kernel.py` is fully dead.** `start_wolf()` is commented out at both call sites ("WOLF ARCHIVED — alignment_kernel retired 2026-06-14"), and the underlying script now lives only in `archive_janitor/alignment_kernel.py`, which is not importable from `run.py`'s working directory (confirmed via a live `ModuleNotFoundError` test). The `/trigger_wolf_kill` and `/howl` endpoints still exist and return dramatic JSON but do not actually start or kill any subprocess.
- **A real Anthropic API integration does exist**, just not in ClaudeShard: `app/internet_tools/claude_research.py` calls `anthropic.Anthropic(...).messages.create(model="claude-haiku-4-5-20251001", ...)`, rate-limited to 1 call/hour, drawing questions from `data/question_garden.jsonl` (curiosity engine), wired into `app/autonomous_loop.py`'s main cycle. As of the 2026-07-04 audit, no successful firing has ever been confirmed (`memory/claude_research_cursor.json`, written only on success, does not exist, and no `[Claude Research] Question:` entries appear in `memory/dream_bridge.log`) — needs live instrumentation to diagnose (bad key, no candidate question, silently swallowed exception, etc.).

---

## Health Monitoring

Six components audited 2026-07-01. Current status:

**`app/core/self_heal.py`** — FIXED, INTENTIONALLY DISCONNECTED. Not imported anywhere; has no live caller. Fixed two stale-assumption bugs (wrong `append_to_journal` signature, wrong FAISS index path). Kept disconnected deliberately; reconnecting requires explicit human decision and review.

**`app/core/system_guard.py`** — ACTIVE. `should_throttle()` reads `memory/echo_state.npy` dim [3] (system_vitality = 1 - RAM/100), returns True when RAM > 92%. Called at the top of autonomous loops. Ground-truth signal.

**`app/core/introspection_channel.py`** — ACTIVE. Runs every 120s, writes `memory/introspection_state.json` with live subsystem state (FAISS vector count, River obs, Ollama process status). Provides the ground-truth readings used by `check_and_alert()`. `reset_drift_detectors()` added 2026-07-01 for clean recalibration after contaminated-era data was cleared.

**`app/core/echo_state.py`** — ACTIVE. 8D float32 vector, updated every 120s. Dim [3] used by system_guard. Dim [7] = circadian signal. Dims [1] and [2] (intent_coherence, memory_stability) are not yet used as alert triggers — excluded pending `baseline_trusted_since` being set.

**`app/core/dmn_guardian.py`** — ACTIVE WITH KNOWN LIMITS. Runs every 60s. One active autonomous remediation: Ollama restart via `subprocess.Popen(["ollama", "serve"])` when `ollama_process_alive` is False in introspection state, with 120s cooldown. `verify_integrity()` checks module importability only — not functional state. `measure_efficiency()` uses `echo_core.operations_completed / energy_used`, which returns 1.0 in practice because EchoCore does not expose those attributes. Both are documented accurately here; neither has been removed because neither causes harm.

**`app/core/self_model_updater.py`** — ACTIVE. Writes the live `memory/self_model.json` on significant focus shifts and reads `memory/history/` for its weekly-drift calculation. **Correction (forensic audit 2026-07-04):** the actual weekly *snapshot into* `memory/history/self_model_YYYYMMDD.json` is performed by `app/maintenance/night_cycle.py`'s `_maybe_snapshot_self_model()` ("copy self_model.json to memory/history/ if no snapshot in the last 7 days"), not by self_model_updater.py itself — the mechanism is real, the file attribution above was wrong. Clean baseline `self_model_20260701.json` created 2026-07-01 (contaminated `self_model_20260627.json` archived). `mark_baseline_trusted()` pending until PageHinkley detectors accumulate 30+ clean observations per task type.

---

## Snapshot and Restore System

**`app/core/snapshot_manager.py`**

**What is snapshotted:** A health manifest per snapshot containing River brain obs/accuracy/drift alerts, FAISS vector count, sandbox success rate, and Ollama process status. Not a full filesystem backup.

**Cadence and retention:** Startup snapshot on each server start (background thread). `_MAX_SNAPSHOTS = 5` most recent retained, plus the most recent startup snapshot if it falls outside that window (max 6 total). Storage: `memory/snapshots/`.

**`find_last_known_good(alert_condition)`:** Walks backwards through snapshots to find the most recent where the named condition was healthy. Used by `check_and_alert()` to surface the suggested restore target.

**Active alert conditions:** `ollama_down` (process not detected in introspection state). Alert path: `check_and_alert()` → guardian loop → WARNING log with restore command. Human executes restore.

**What does NOT yet trigger restore alerts:** `drift_alerts` (River PageHinkley), `weekly_delta` (self-model divergence), `echo_state` dims [1]/[2]. Explicitly excluded until `baseline_trusted_since` is set in `memory/snapshot_baseline.json`. Adding them before that point would generate false alerts from contaminated-era baselines.

**Restore is alert-and-propose, human-confirmed only. No autonomous restore path exists.**

```bash
# Human-initiated restore
curl -X POST http://localhost:5000/admin/restore \
     -H 'Content-Type: application/json' \
     -d '{"snapshot_id": "20260701T214512Z"}'
```

---

## Rating and Training Signal

### Terminal User Rating

`terminal_client.py` shows a dim hint after each response: "type 1–5 at the next prompt to rate this response." A bare digit at the `You:` prompt saves the rating via `_save_rating()` (no tty/cbreak/timer). Confirmed working as of 2026-07-02.

### Council Peer Rating (`app/core/council_rater.py`)

Background daemon thread: 90s poll cycle, 1-in-5 sampling of rateable entries.

**Hard constraint:** Rater model must differ from `model_used`. Same-model fallback is intentionally absent. If no peer is available, the entry logs as `skipped_no_peer` and the count surfaces in `GET /admin/council-stats`.

**Sampling and spot-checks:** First 20 ratings (`_CALIBRATION_WINDOW`) are all flagged `spot_check_required: true`. After calibration: every 10th rating, plus any where |council_rating - quality_score| ≥ 2 or rating is 1 or 5.

**Output:** `memory/council_ratings.jsonl`. Fields: `council_rating`, `council_rating_model`, `council_rationale_preview`, `task_type`, `quality_score`, `spot_check_required`, `human_spot_check_rating`.

**Trust gate:** `learn_from_rating()` is not called anywhere in this pipeline. No training signal is produced until `council_baseline_trusted_since` is written to `memory/snapshot_baseline.json`, which requires 50 ratings, 10 completed human spot-checks, and ≥70% council/human agreement. Setting this threshold and the subsequent blending decision are explicit human decisions.

**Important disambiguation (confirmed 2026-07-04/05, this trust gate is easy to conflate with self-edit gating — it is not the same thing):** `council_baseline_trusted_since` has **zero code paths reading it anywhere outside `council_rater.py` itself.** It does not gate, unlock, or influence `self_edit_manager.perform_self_edit()` in any way — the only real gate on self-edit is the 60-minute cooldown plus the F1/F2/F3 safety pipeline. If this trust flag is ever set, it currently does nothing downstream. Live `get_council_stats()` as of 2026-07-04: `total_rated=8` (need 50), `spot_checks_completed=8` (need 10) — 5 of 13 raw logged entries are excluded by the `scorer_baseline_timestamp` cutoff (ratings computed before a quality-scorer fix don't count toward the tally). **What to unlock once trust is reached, if anything, is an explicit decision for Gremlin to make — do not wire `council_baseline_trusted_since` into River blending, self-edit gating, or any other consequential path by default or by momentum, per GREMLIN_ROLE.md.**

**River blending (pending, not implemented):** Proposed 30% council / 70% quality_score once trust threshold is met. When the threshold is met, it will be flagged for approval — not wired in automatically.

**Human spot-check channel:** `python spot_check.py` — reads `council_ratings.jsonl`, presents flagged entries with full interaction context where available, writes ratings back atomically.

**Status (2026-07-04, re-verified live):** 13 entries in `memory/council_ratings.jsonl` (8 counted post-scorer-baseline), all currently spot-checked (0 pending). Thread confirmed running.

---

## Protected Files (EDIT_FORBIDDEN_TARGETS)

Hardcoded in `self_edit_manager.py`. Must never be overwritten by self-edits or tooling:

```
run.py                              echo_principles.json
Modelfile                           app/core/echo_model_orchestrator.py
app/core/river_deliberation.py      app/core/echo_core.py
app/core/memory_bridge.py           app/core/introspection_channel.py
app/core/self_model_updater.py      app/core/bible_injection.py
```

`echo_principles.json` is hash-verified at startup against `memory/genesis/genesis_hash.txt`. Do not modify it.

---

## Key Constraints

**Module inventory for self-edits** (`_build_module_inventory` in `self_edit_manager.py`): only shows `app.*` modules, filters backup/temp files. Labels functions and classes separately to prevent the LLM from treating class names as module names (e.g., `from ToolManager import ToolManager` is a hallucination — correct import is `from app.core.tool_manager import ToolManager`).

**Autonomous awareness modules** (`app/core/echo_python_mastery/`): all `get_tips()` functions are private (`_get_tips()`). Only `teach_X()` functions are registered as tools. `code_quality.py` caches its filesystem scan for 10 minutes. **Correction (re-verified 2026-07-05): this is not just an import-path mismatch.** `run.py` and `app/emergent_scheduler.py` both reference a bare top-level `echo_python_mastery` name, while the real package lives at `app.core.echo_python_mastery` — but the real package's `__init__.py` only exports `teach_basics`/`teach_code_quality`/`teach_best_practices`/`teach_advanced`/`teach_debugging`/`teach_testing`. It has never implemented `get_recent_feedback()` or `practice_idle()` under any name, so pointing the import at the real package would still fail. `emergent_scheduler.py`'s in-process stub (`get_recent_feedback = lambda: {}`, `practice_idle = lambda: None`) is an honest no-op, not a workaround for a fixable path bug — mastery feedback reaching the scheduler is a real, unimplemented feature gap, not a one-line fix.

**Empty directories (found 2026-07-04):** `app/experimental/` and `app/integrations/` exist but contain zero files, not even `__init__.py`. Do not assume any implementation lives there without checking first.

**Large orphaned files (found 2026-07-04, zero callers confirmed via repo-wide grep):** `app/core/library_knowledge.py` (6,775 lines, an auto-generated and partially-inaccurate library-description database — e.g. it categorizes the `anthropic` SDK as a "Web Framework"), `app/core/attention_kernel.py`, `app/core/feral_tools.py`, `app/core/placeholder_ai.py`, `app/core/project_scanner.py`, `app/core/river_deliberation_backup.py`, `app/learning/dual_learning_backup.py`, `app/subsystems/orientation_protocol.py`. Safe to ignore as "missing features" — they are dead weight, not disconnected capability.

**Tailscale sync** (`app/sync/sync_protocol.py`): M5 (100.84.229.10) syncs with Air (100.82.172.4) every 1800s. Quality floor 0.3, 200-entry batches, SHA-256 dedup. `LOCAL_ONLY_SOURCES = {"self_edit"}` — self-edit entries never sync.

**Memory source tags**: `memory_source: "autonomous"` (autonomous paths), `"user_conversation"` (terminal), `"sync_m5"` / `"sync_air"` (Tailscale). `retrieve_relevant_memories()` accepts `source_filter` to exclude autonomous self-talk from user-facing context.

**Scripture integrity**: `bible_injection.py` prevents verse confabulation at generation time. Post-response scripture scan in `echo_model_orchestrator.py` logs mismatches to `memory/scripture_warnings.log`. Principle drift logged to `memory/principle_violations.log`.

**OpenMP / KMP startup guard** (`run.py`, lines 13–16): `KMP_DUPLICATE_LIB_OK=TRUE`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `TOKENIZERS_PARALLELISM=false` — set before any native extension imports. Required because faiss and numpy/MKL each ship `libkmp.dylib`; without this, the second load triggers `__kmp_register_library_startup → __kmp_fatal → abort()` (confirmed SIGABRT in two crash reports, 2026-06-29 and 2026-06-30). Safe for this workload: all faiss callers set `faiss.omp_set_num_threads(1)`; no parallel numeric compute paths exist.

---

## Known Findings (Security/Health Audit, 2026-07)

**Finding 3 — RiverBrain cross-training contamination (fixed, downstream pending):** A heatmap cross-training loop in `echo_model_orchestrator.py` was training `personal` and other classifiers on responses from mismatched task types. Loop removed. Clean baseline `self_model_20260701.json` established. `mark_baseline_trusted()` and `reset_drift_detectors()` pending 30+ clean observations per task type from PageHinkley detectors.

**Finding 4 — `cpu_tuning()` nice-value ratchet — RESOLVED BY REMOVAL (confirmed 2026-07-04):** This entry previously described `dmn_guardian.py`'s `RealWorldAdaptiveRegulator.cpu_tuning()` as a diagnosed-but-unfixed bug. A forensic audit on 2026-07-04 found the function no longer exists anywhere in the codebase (`grep -rn cpu_tuning app/` returns zero hits); `dmn_guardian.py`'s own docstring now states the adaptive-regulator/experimental-zone infrastructure was "removed 2026-07-01 (phantom metrics, no live readers)". The fix outpaced this doc's update — treat any CLAUDE.md claim about specific line-level bugs as needing re-verification against current source before acting on it, per this exact case.

**Finding 5 — Model-guided Optuna loop silently dead since built (fixed 2026-07-01):** `echo_model_guided_orchestrator.py` had two chained bugs: `retrieve_recent_reflections(top_k=5)` (wrong kwarg; function takes `n`) and `[r['text'] for r in ...]` (wrong key; entries have `content`). The outer `except Exception` swallowed both silently. Optuna ran every cycle but with empty reflection hints. Both fixed; loop fires correctly from the next cycle.

**Finding 6 — Five `run.py` subsystems silently dead due to an incomplete `archive_janitor/` migration (found 2026-07-04):** `run.py` imports five bare top-level modules — `echo_bible_interface`, `bible_module`, `sensory_hub_autonomous`, `feralecho_continuity_master`, `alignment_kernel` — that only exist under `archive_janitor/`, which is not on `sys.path`. Verified with a live `importlib.import_module()` test inside `conda activate feral_echo`: all five raise `ModuleNotFoundError`. Each import is guarded by a try/except that falls back to a no-op stub, so the server doesn't crash, but the corresponding features (WOLF subprocess, SensoryHub on port 5050, Bible-art generation every 2h, Bible-quote lookup, the "FeralEchoMain" continuity thread) do not run, despite `run.py`'s log lines narrating them as live ("ECHO IS NOW EMBODIED", "WOLF RESTARTED"). The `/trigger_wolf_kill` and `/howl` endpoints still respond but do nothing. Fixing this requires a deliberate decision (restore the imports vs. formally retire the dead code) — not a default action.

**Finding 7 — Autonomous scaffold-directory sprawl, including one leaked-secrets file (found 2026-07-04):** The dozens of duplicate-looking top-level project folders (`calculator/`, `chatbot/`, `echo_scripts/`, `new_directory/`, `PythonAnalysis/`, etc.) are not manual clutter — they are a demonstrated byproduct of `self_edit_manager.py`'s write-target constants being relative paths (`"app/core/self_edit_generated.py"`, `"app/core/self_edit_backups"`, `"app/core/self_edit_plans"`) rather than anchored to the project root via `__file__`. Whenever the self-edit pipeline (or LLM-generated code within it) runs with a different working directory, it recreates its own scaffold there. A second, independent cause is `RebelCode/territory_steward.py`'s `claim_new_ground()`, which calls `.mkdir()` directly on LLM-supplied names. **Security-relevant:** `new_directory/app/core/env/environment.json` — a byproduct of this pattern — is tracked in git (the repo's single commit, `dc3795a`) and contains real plaintext `NEWSAPI_KEY` and `OPENWEATHER_API_KEY` values, with `origin` set to `git@github.com:gremlinchode/FeralEcho-Backup.git`. **This has not yet been confirmed remediated — check whether it was ever pushed to GitHub, and if so rotate both keys and scrub the file from history.** `.env` itself (holding `ANTHROPIC_API_KEY`) is correctly gitignored and unaffected. Fix requires anchoring `self_edit_manager.py`'s path constants to `__file__` and adding `.gitignore` coverage for the scaffold directories.

**Finding 8 — `com.gremlin.echo` launchd job is an inert fossil, not a live daemon (found 2026-07-04):** `~/Library/LaunchAgents/com.gremlin.echo.plist` (last modified 2025-07-19) points to a nonexistent script (`~/Scripts/start_echo.sh`) and a different, abandoned working directory (`~/EchoCoreV2`, a predecessor project). `launchctl print` shows `active count = 0`, `last exit code = 78: EX_CONFIG` — it has never successfully run. The current system's only confirmed startup path is manual (`python run.py`, per the top of this doc). Do not assume any launchd-managed background instance of Echo exists.

---

## Monitoring

```bash
# Watch for self-edit storm (0-1 coding entries per 30 min is normal)
tail -f memory/SELF_EDIT.log

# Watch live interaction quality
tail -f memory/interaction_log.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    print(e.get('task_type'), e.get('quality_score'), repr((e.get('response_preview') or '')[:80]))
"

# Council rating pipeline status
curl http://localhost:5000/admin/council-stats

# Run human spot-checks interactively
python spot_check.py

# Check crash sentinel (last-run stage + heartbeat)
cat memory/echo_sentinel.json

# Check if self_edit_generated.py is clean
python3 -c "import ast; ast.parse(open('app/core/self_edit_generated.py').read()); print('OK')"

# Check both FAISS indexes for divergence
# NOTE: memory_meta.json/data/memory_meta.json are dicts keyed by UUID, not
# {"texts": [...]} — an earlier version of this snippet used .get('texts', [])
# and always reported 0 regardless of actual health (confirmed 2026-07-04: this
# produced a false "FAISS reports 0 vectors" alarm during the forensic audit;
# real counts at the time were memory/=7225, data/=5348). Count dict keys instead.
python3 -c "
import json
m = json.load(open('memory/memory_meta.json'))
d = json.load(open('data/memory_meta.json'))
print('memory/:', len(m), 'vectors')
print('data/:  ', len(d), 'vectors')
"
```

---

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| New `python run.py` exits silently within 15s, no error visible | Port 5000 still held by previous server | `kill $(lsof -ti :5000) && python run.py` — always kill first |
| Rapid `sandbox_syntax_failure` in interaction_log | Self-edit storm — cooldown reset on restart | Restart server |
| `self_edit_generated.py` overwritten with hallucinated imports | Loop fired before cooldown active | Restore baseline from `memory/backups/`, restart |
| `DUPLICATE_SIGNAL_EXACT` dominating scheduler | Empty `__init__.py` files or unchanged pip count generating identical FAISS entries | Fixed in `autonomous_awareness.py` — restart to activate |
| `staging_import_failed: ImportError: cannot import` | Model hallucinated module name | Check generated imports against `_build_module_inventory` output |
| B2 recency check not working (same prompts repeat) | FAISS split-brain — `memory_meta.json` empty or orphaned | Merge `data/memory_meta.json` into `memory/memory_meta.json`, rebuild index |
| Responses cut off mid-sentence | Wrong `num_predict` path | Primary: `stream_query_ollama` in `ollama_handler.py`. Secondary: `ollama_query` in `echo_model_orchestrator.py`. Both must match. |
| `[RESTORE-ALERT] condition=ollama_down` in logs | Ollama not detected in introspection state | `ollama serve` — guardian will attempt restart but 120s cooldown applies |
| `council_ratings.jsonl` not accumulating | Only one Ollama model available; `skipped_no_peer` rising | Pull additional models so `_select_peer_model()` has options |
| A new top-level scaffold directory appears (e.g. another `new_directory`-style folder with its own `app/core/self_edit_*`) | Self-edit pipeline invoked with `cwd` != project root (relative path constants in `self_edit_manager.py`), or `RebelCode/territory_steward.py`'s `claim_new_ground()` | Anchor `self_edit_manager.py`'s path constants to `__file__`; do not manually "clean up" by deleting without checking for real content first (`my_python_project/` has its own `.git` and predates the sprawl pattern) |
| `run.py` logs "SensoryHub failed to start" / silently no-ops the Bible-art or WOLF endpoints | Expected — see Finding 6. Five modules referenced by `run.py` live only in `archive_janitor/` and are not importable | Not a bug to "fix" reflexively; restoring them or removing the dead code is a deliberate decision, not a default action |
| `launchctl list` shows `com.gremlin.echo` | Dead fossil pointing at an abandoned predecessor project (`~/EchoCoreV2`) — see Finding 8 | Ignore; the only real startup path is manual `python run.py` |
