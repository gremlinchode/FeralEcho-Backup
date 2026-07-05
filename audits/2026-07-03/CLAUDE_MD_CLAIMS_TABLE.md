# CLAUDE.md Claims vs. Reality — 2026-07-03

Every falsifiable claim from CLAUDE.md, checked against the actual code.

**Verdict codes:**
- **TRUE** — code matches the claim
- **FALSE** — code contradicts the claim
- **STALE** — was true, no longer true
- **PARTIAL** — partially true with important caveats
- **UNVERIFIABLE** — cannot verify without running the server

---

## Architecture and Primary Call Path

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Primary call path: terminal_client → echo_query → river_deliberation._ollama_query → stream_query_ollama → Ollama HTTP :11434 | **TRUE** | `terminal_client.py:559`, `echo_model_orchestrator.py:1093`, `river_deliberation.py:151`, `ollama_handler.py:267` |
| Subprocess fallback fires only on HTTP failure | **TRUE** | `river_deliberation.py:157–168`: wrapped in `except Exception` after stream_query_ollama attempt |
| Token limits: personal/autonomous_* → 512, reasoning/general/creative → 1024, coding → 2048 | **TRUE** | `echo_model_orchestrator.py:982–990`: `_TASK_TOKEN_LIMITS` matches exactly |
| `memory_bridge.py` writes to `memory/memory_meta.json` + `memory/faiss.index` | **TRUE** | `memory_bridge.py:43–44`: paths set to `config.MEMORY_DIR` which resolves to `memory/` |
| `app/lib/vector_memory.py` writes to `data/memory_meta.json` + `data/faiss.index` | **FALSE** | `vector_memory.py:32–33`: default paths are `memory/faiss.index` and `memory/memory_meta.json`, NOT `data/`. Only archive scripts use `data/` paths |
| "Always use memory_bridge.py for new code" | **TRUE** — policy | Confirmed that runtime code uses memory_bridge |

---

## Self-Edit System

| Claim | Verdict | Evidence |
|-------|---------|----------|
| `perform_self_edit()` has global 60-min cooldown | **TRUE** | `self_edit_manager.py:1091`: `_TARGETED_PROMPT_COOLDOWN = 3600` |
| Cooldown is global in-memory `_last_any_autonomous_edit: float` | **TRUE** | `self_edit_manager.py:1090`: module-level float |
| Cooldown resets on server restart | **TRUE** | Module-level variable reset to `0.0` on import — no persistence |
| "Restart the server" remediates a self-edit storm | **PARTIAL** | It stops the storm AND re-arms the cooldown to 0 — next autonomous attempt fires immediately |
| Self-edit pipeline: plan → F1 AST scan → F2 sandbox → staging import test → backup → save → F3 post-write scan | **TRUE** | `self_edit_manager.py:975–1084` traces this order |
| F1 blocks exec(), eval(), os.system, subprocess.*, shutil.*, Path.write_text/bytes | **TRUE** | `self_edit_manager.py:73–97`: all listed in `_BLOCKED_*` sets; scan in `scan_for_unsafe_operations()` line 220 |
| F2: `sandbox-exec -f echo_sandbox.sb`; must exit 0 and emit `SANDBOX_OK` | **TRUE** | `self_edit_manager.py:569–578` and `742–755` |
| F3: post-write AST scan before loading | **TRUE** | `self_edit_manager.py:632–648` |
| Residual gap: C extensions below Python monkeypatch | **TRUE** | Acknowledged in code comment at line 656 |
| Self-edit is limited to `self_edit_generated.py` only | **PARTIAL** | That is the intent and the default. But `wolf_friction_bridge.build_self_edit_prompt()` (line 62–68) asks the model to target ANY "real, existing file." The wolf bridge is currently dry-run only, so no production risk now |

---

## Wolf Friction Bridge

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Wolf bridge is "currently disabled at the call site" — `simulate_self_edit()` is called, not `perform_self_edit()` | **TRUE** | `echo_model_orchestrator.py:1153`: `simulate_self_edit(_fe)` |
| `simulate_self_edit()` does not call `save_code()`, does not load into running process, produces no River training signal | **TRUE** | `wolf_friction_bridge.py:255–265`: these three operations explicitly skipped and commented |
| `memory/wolf_dryrun_window.json` is "DISCONNECTED DEAD CODE" — zero Python files read or write it | **TRUE** | `grep -rn "wolf_dryrun_window" --include="*.py"`: no results in live code |

---

## Health Monitoring

| Claim | Verdict | Evidence |
|-------|---------|----------|
| `self_heal.py` — fixed, intentionally disconnected, no live caller | **TRUE** | `grep -rn "from app.core.self_heal\|import self_heal"`: no results in live imports |
| `system_guard.py` — ACTIVE, `should_throttle()` reads `memory/echo_state.npy` dim[3] | **UNVERIFIABLE** | File exists (`app/core/system_guard.py` referenced in run.py:1015) but server not running to confirm |
| `introspection_channel.py` — ACTIVE, runs every 120s | **TRUE** (wired) | `run.py:855`: started in `start_background_threads()`. Interval set at `IntrospectionChannel(core, interval=120)` wait — run.py line 852: `IntrospectionChannel(_ec)` — default interval is 120s (channel.__init__ line 38) |
| `echo_state.py` — 8D float32 vector, updated every 120s, persisted to `memory/echo_state.npy` | **UNVERIFIABLE** | Wired in `echo_core.py` (not fully audited) |
| `dmn_guardian.py` — ACTIVE with known limits | **TRUE** | `run.py:870`: `_start_guardian_loop(echo_core=_ec, interval=60)` |
| DMN guardian: `measure_efficiency()` returns 1.0 due to phantom metrics | **STALE** | dmn_guardian.py v4.1 comment (line 7) says "Adaptive regulator... removed 2026-07-01." The current file does not contain `measure_efficiency()`. The known issue was fixed by deletion |
| `self_model_updater.py` — ACTIVE, writes weekly and on significant shifts | **TRUE** (wired) | `run.py:863–866`: started in `start_background_threads()` |

---

## Snapshot and Restore

| Claim | Verdict | Evidence |
|-------|---------|----------|
| "What is snapshotted: A health manifest… Not a full filesystem backup." | **FALSE** | `snapshot_manager.py:55–61`: `_ARTIFACTS` includes five actual files. `take_snapshot()` copies them with `shutil.copy2()`. `restore_snapshot()` writes them back. This IS a filesystem backup of key files |
| Snapshot cadence: startup snapshot + post-self-edit snapshot | **TRUE** | `run.py:878`: startup snapshot in thread; `self_edit_manager.py:1074`: `_snap("post_self_edit")` |
| `_MAX_SNAPSHOTS = 5` most recent retained, plus most recent startup | **TRUE** | `snapshot_manager.py:76`: `_MAX_SNAPSHOTS = 5`; `_prune_snapshots()` implements the logic |
| `find_last_known_good(alert_condition)` walks backward through snapshots | **TRUE** | `snapshot_manager.py:329–346` |
| Active alert condition: `ollama_down` | **TRUE** | `snapshot_manager.py:394–395` |
| "Restore is alert-and-propose, human-confirmed only. No autonomous restore path exists." | **TRUE** | `snapshot_manager.py:18–20`: comment; `restore_snapshot()` has no auto-trigger |

---

## Rating and Training Signal

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Terminal user ratings: type 1–5 rates the response; `_save_rating()` saves via bare digit | **TRUE** | `terminal_client.py:651–655`: `if msg in {"1", "2", "3", "4", "5"} and last_response: _save_rating(int(msg), last_response)` |
| "Confirmed working as of 2026-07-02" | **TRUE** (code is wired) | Mechanism is correct; operational confirmation not re-run during audit |
| Council peer rating — rater model must differ from `model_used` | **PARTIAL** | Code enforces this (council_rater.py:81–89), BUT two entries in council_ratings.jsonl have `model_used == council_rating_model == echo:latest` (entries 3 and 10). These violate the constraint. |
| Council poll: 90s poll cycle, 1-in-5 sampling | **TRUE** | `council_rater.py:545`: `poll_interval=90`; line 40: `_SAMPLE_EVERY = 5` |
| `learn_from_rating()` is not called anywhere in council pipeline | **TRUE** | `grep -n "learn_from_rating" council_rater.py`: 0 results |
| Trust gate: 50 ratings, 10 spot-checks, 70% agreement | **TRUE** | `council_rater.py:43–45`: `_TRUST_MIN_RATINGS=50`, `_TRUST_MIN_SPOTCHECKS=10`, `_TRUST_AGREEMENT_THRESHOLD=0.70` |
| "Status (2026-07-01): 2 entries in council_ratings.jsonl, both flagged for spot-check. Thread started and confirmed running. Cursor at 11009." | **STALE** | Current state: 10 entries, all spot-checked. Agreement rate 43%. Cursor not checked but likely advanced |

---

## Protected Files

| Claim | Verdict | Evidence |
|-------|---------|----------|
| `EDIT_FORBIDDEN_TARGETS` list matches code | **TRUE** | `self_edit_manager.py:50–61`: exactly matches CLAUDE.md list |
| "echo_principles.json is hash-verified at startup against memory/genesis/genesis_hash.txt" | **FALSE** | `run.py`: no hash check at startup. `grep -rn "genesis_hash"` shows only the `/sync/genesis` HTTP endpoint (on-demand) and snapshot restore (not startup). No startup verification exists |
| Modelfile has integrity protection beyond self-edit forbidden list | **PARTIAL** | Modelfile IS in `EDIT_FORBIDDEN_TARGETS` (line 59). BUT it has no hash verification at startup. The snapshot system snapshots it and verifies on restore. No continuous runtime protection |

---

## Known Findings Section

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Finding 3 — RiverBrain cross-training contamination fixed, loop removed | **TRUE** | `echo_model_orchestrator.py:1103–1105`: only trains on `task_type`, not heatmap multi-task |
| Finding 4 — `cpu_tuning()` nice-value ratchet "disabled in experimental_zones" | **STALE** | `dmn_guardian.py` v4.1 has removed the adaptive regulator entirely (line 7 comment). `cpu_tuning()` no longer exists in the file |
| Finding 5 — Optuna loop bugs fixed (wrong kwarg `top_k`, wrong key `text`) | **UNVERIFIABLE** | `app/core/echo_model_guided_orchestrator.py` not fully audited in this pass |

---

## Monitoring Commands

| Claim | Verdict |
|-------|---------|
| `tail -f memory/SELF_EDIT.log` watches for self-edit storm | **TRUE** — file exists in the journal append path (`append_to_journal("SELF_EDIT", ...)`) |
| Check FAISS index divergence command produces counts | **PARTIAL** — command works but both show 0 vectors (see C-3) |
| `cat memory/echo_sentinel.json` shows crash sentinel | **TRUE** — sentinel write in `run.py:785–800` |

---

## Common Failure Modes Table

| Symptom | Claim | Verdict |
|---------|-------|---------|
| New python run.py exits silently within 15s | Port 5000 still held | **TRUE** — no mechanism to check for this; kill-first required |
| Rapid sandbox_syntax_failure | Self-edit storm | **TRUE** |
| Restart remediates storm | **PARTIAL** — remediates AND re-arms (see H-1) |

---

*Claims table generated from CLAUDE.md version as of audit date. Evidence citations use file:line format.*
