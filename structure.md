# FeralEcho — Project Structure
_Last updated: 2026-06-27_

---

## Entry Points

| File | Purpose |
|------|---------|
| `run.py` | Flask server — user API, sync routes, background threads |
| `terminal_client.py` | Interactive terminal — primary human↔Echo interface |
| `start_echo.sh` | Shell script to launch Echo |
| `echo_json_server.py` | Lightweight JSON API server |

---

## app/ — Core Application

### app/ (top level)
| File | Purpose |
|------|---------|
| `autonomous_loop.py` | Autonomous fetch-reflect cycle (internet → FAISS) |
| `autonomous_awareness.py` | Environment learning: OS info, package count, Python code analysis |
| `autonomous_harmony_manager.py` | Harmony/balance subsystem |
| `emergent_scheduler.py` | **Primary scheduler** — prompt selection, curiosity engine, B2 recency check, coherence-tension boost, quality scoring |
| `ollama_handler.py` | HTTP Ollama interface — `query_ollama()` (blocking) + `stream_query_ollama()` (streaming, used by river_deliberation) |
| `stillness.py` | Quiet/stillness mode |
| `persona.json` | Base persona config |

### app/core/ — Engine
| File | Purpose |
|------|---------|
| `echo_model_orchestrator.py` | **Main call path** — `echo_query()`, model selection, circuit breaker, deliberation routing, post-response audit, task-aware token limits |
| `river_deliberation.py` | Council deliberation — multi-model synthesis via `stream_query_ollama()` |
| `memory_bridge.py` | FAISS read/write — `log_dream_bridge()`, `retrieve_relevant_memories()`, source_filter support |
| `introspection_channel.py` | System health collector → `introspection_state.json` + echo_state hook |
| `echo_state.py` | **8D float32 state vector** — system_vitality, coherence_tension, curiosity_pressure, circadian signal, persisted to `memory/echo_state.npy` |
| `curiosity_engine.py` | Self-generated goals via WorldModel under-representation → question garden |
| `shadow_model.py` | Shadow self-model — tracks whether Echo's self-assessments are accurate |
| `self_edit_manager.py` | Self-modification with staging gate — test before commit |
| `self_model_updater.py` | Reads/writes `memory/self_model.json`, computes weekly delta |
| `system_guard.py` | Load-aware throttle — reads echo_state dim[3] (RAM), skips inference under pressure |
| `dmn_guardian.py` | Background guardian — health monitoring, Ollama restart on failure |
| `garden_manager.py` | Question garden CRUD |
| `memory_write_validator.py` | Validates entries before FAISS commit |
| `bible_injection.py` | Scripture citation guard — prevents confabulation of cited verses |
| `bible_module.py` | Bible lookup |
| `claude_shard.py` | Claude API shard for supplemental reasoning |
| `gemini_shard.py` | Gemini API shard |
| `shard.py` | Base shard interface |
| `council_registry.py` | Council model registry |
| `echo_optuna.py` | Optuna hyperparameter tuning integration |
| `attention_kernel.py` | Attention routing kernel |
| `dark_light_pipeline.py` | Dark/light processing pipeline |
| `wolf_friction_bridge.py` | Friction events → self-edit bridge |
| `predictive_loop.py` | Predictive modeling loop |
| `project_learner.py` | Project structure learning |
| `project_scanner.py` | Codebase scanner |
| `load_project_map.py` | Project map loader |
| `feral_tools.py` | Misc internal tools |
| `tool_manager.py` | Tool registration and dispatch |
| `temporal_environment.py` | Time-aware environment context |
| `awareness_tools_integration.py` | Bridges awareness tools to core |
| `library_knowledge.py` | Installed library knowledge base |
| `echo_review_mastery.py` | Code review capability |
| `echo_load_mastery.py` | Load handling mastery module |
| `echo_model_guided_orchestrator.py` | Guided orchestrator variant |
| `modelfile_proposer.py` | Proposes Modelfile changes |
| `sandbox_interface.py` | Interface to sandbox execution |
| `self_heal.py` | Self-healing logic |
| `placeholder_ai.py` | Fallback AI placeholder |
| `config.py` | Shared config constants |
| `Memory_helpers.py` | Memory utility functions |
| `memory_tools.py` | Memory tool wrappers |
| `self_edit_generated.py` | Output file for self-edits |
| `temp_self_edit.py` | Temporary self-edit staging file |
| `autonomous_loop_with_optuna.py` | Optuna-integrated autonomous loop variant |

#### app/core/echo_python_mastery/
Self-generated Python knowledge modules: `coding_basics`, `advanced_python`, `best_practices`, `code_quality`, `debugging`, `examples`, `testing_and_validation`

### app/internet_tools/
| File | Purpose |
|------|---------|
| `autonomous_fetch.py` | Web fetch for autonomous loop |
| `query_reflect.py` | Fetch-then-reflect pipeline |

### app/learning/
| File | Purpose |
|------|---------|
| `dual_learning.py` | Dual learning system (RiverBrain + quality scorer) |

### app/lib/
| File | Purpose |
|------|---------|
| `vector_memory.py` | Low-level FAISS wrapper (`data/memory_meta.json` path) |

### app/maintenance/
| File | Purpose |
|------|---------|
| `night_cycle.py` | Nightly consolidation, weekly self_model snapshots |
| `consolidation.py` | Memory consolidation logic |

### app/subsystems/
| File | Purpose |
|------|---------|
| `orientation_protocol.py` | Startup orientation sequence |
| `reflection_shard.py` | Reflection shard writer |

### app/sync/
| File | Purpose |
|------|---------|
| `sync_protocol.py` | Tailscale bidirectional sync — export/import interaction log with SHA-256 dedup, 200-entry batches |

### app/experimental/ / app/integrations/
Reserved for experimental features and external integrations (currently empty).

---

## memory/ — Persistent State

| Path | Purpose |
|------|---------|
| `memory_meta.json` | Primary FAISS metadata (used by `memory_bridge.py`) |
| `faiss.index` | Primary FAISS vector index |
| `interaction_log.jsonl` | All interactions — user conversations + autonomous reflections + fetches |
| `reflection_journal.jsonl` | Reflection output log |
| `dream_bridge.log` | Raw entries awaiting FAISS commit |
| `self_model.json` | Current self-model (task quality per type, weak areas, weekly delta) |
| `shadow_self_model.json` | Shadow model predictions for accuracy tracking |
| `shadow_accuracy.jsonl` | Shadow model prediction vs actual log |
| `introspection_state.json` | Live system health — RAM, load, disk, Ollama status |
| `echo_state.npy` | 8D float32 state vector (updated every 120s) |
| `echo_state_history.npy` | Ring buffer of last 100 state snapshots |
| `scheduler_selections.log` | Prompt selection history |
| `signal_hash_cache.json` | Duplicate signal detection cache |
| `world_model_diagnostics.json` | WorldModel topic distribution |
| `optuna.db` | Optuna hyperparameter study database |
| `river_brain.pkl` | RiverBrain online learning state |
| `principle_violations.log` | Post-response principle audit log |
| `scripture_warnings.log` | Post-response scripture integrity warnings |
| `validator_audit.log` | Memory write validator decisions |
| `sync_seen.jsonl` | SHA-256 hashes of synced entries (dedup) |
| `sync_state.json` | Last sync timestamp per partner URL |
| `claude_shard.jsonl` | Claude shard interaction log |
| `claude_shard_friction.log` | Claude shard friction events |
| `wolf_friction_cursor.json` | Wolf friction bridge cursor position |
| `consolidation_log.jsonl` | Night cycle consolidation history |
| `modelfile_proposals.jsonl` | Proposed Modelfile changes |
| `learning_events.jsonl` | Learning event log |
| `prediction_log.jsonl` | Predictive loop log |
| `quarantine_journal.jsonl` | Quarantined memory entries |
| `dual_meta.json` | Dual learning metadata |
| `SELF_EDIT.log` | Self-edit activity log |
| `SELF_EDIT_MASTERY_.log` | Self-edit mastery tracking |
| `self_edit_reflections.log` | Self-edit post-reflection log |
| `INTERACTION_ECHO.log` | Echo-side interaction log |
| `INTERACTION_USER.log` | User-side interaction log |
| `memory_journal_active.log` | Active memory journal |
| `memory_journal.log` | Memory journal archive |
| `genesis/genesis_hash.txt` | SHA-256 hash of echo_principles.json at genesis |
| `genesis/genesis_timestamp.txt` | Genesis timestamp |
| `history/self_model_YYYYMMDD.json` | Weekly self_model snapshots |
| `archive/` | Archived/poisoned logs |

---

## data/ — Secondary Storage

| Path | Purpose |
|------|---------|
| `memory_meta.json` | Secondary FAISS metadata (used by `app/lib/vector_memory.py`) |
| `faiss.index` | Secondary FAISS index |
| `question_garden.jsonl` | Curiosity question garden |
| `codebase_map.json` | Scanned codebase map |
| `codebase.db` | Codebase SQLite database |
| `symbiote_location.json` | Symbiote tracking |
| `self_model.txt` | Plain text self-model snapshot |

---

## sandbox/ — Safe Execution Environment

| Path | Purpose |
|------|---------|
| `experiment_runner.py` | **ExperimentRunner** — 3-layer experimental system (staging gate, shadow model, rollback) |
| `runner.py` | Sandbox script runner |
| `run_script.py` | Script execution entry |
| `file_utils.py` | Sandbox file utilities |
| `logging_setup.py` | Sandbox logging config |
| `scripts/` | Temporary self-edit scripts |
| `experiments/` | Experiment test scripts |
| `inputs/` / `outputs/` / `logs/` | Sandbox I/O and execution logs |

---

## staging/ — Self-Edit Staging Area
Temporary holding area for self-edits awaiting import test before commit to live code.

---

## Root-Level Config & Identity

| File | Purpose |
|------|---------|
| `echo_principles.json` | **Echo's identity constitution** — protected, hash-verified at genesis |
| `feralecho_config.json` | Runtime configuration |
| `run.py` | Flask server (also entry point) |
| `terminal_client.py` | Interactive terminal |
| `echo_quality_scorer.py` | Multi-dimensional response quality scorer |
| `echo_cartographer.py` | Codebase mapping tool |
| `echo_janitor.py` | Memory/log cleanup tool |
| `river_creative_rehab.py` | RiverBrain rehabilitation script |
| `backup_feral_echo.sh` | Full backup script |
| `start_echo.sh` | Launch script |
| `README.md` | Project readme |
| `EMERGENCE_ROADMAP.md` | Long-term architecture roadmap |
| `SELF_HEAL_PLAN.md` | Self-healing strategy document |
| `bible_sentiment.json` | Bible verse sentiment analysis |
| `bible_structured.json` | Structured Bible data |

---

## books/ — Bible Source Data
66 JSON files, one per canonical book (Genesis → Revelation). Source for `bible_injection.py` citation verification.

---

## archive_janitor/ / archive_optional_files/ / archived_files/
Historical scripts, one-off tools, and deprecated files kept for reference. Not part of active runtime.

---

## Key Architecture Notes

**Primary call path (user conversation):**
`terminal_client.py` → `echo_query()` in `echo_model_orchestrator.py` → `river_deliberation._ollama_query()` → `stream_query_ollama()` in `ollama_handler.py`

**Autonomous path:**
`emergent_scheduler.py` → `echo_query()` → same call chain

**FAISS dual-index:**
`memory_bridge.py` writes to `memory/memory_meta.json` + `memory/faiss.index`
`app/lib/vector_memory.py` writes to `data/memory_meta.json` + `data/faiss.index`
Both indexes exist; `memory_bridge.py` is the authoritative path.

**Token limits by task type:**
`personal/autonomous_*` → 512 tokens | `reasoning/general/creative` → 1024 | `coding` → 2048

**Protected files (EDIT_FORBIDDEN_TARGETS):**
`echo_principles.json`, `run.py`, `terminal_client.py`, `memory_bridge.py`, `autonomous_loop.py`, `ollama_handler.py`, `emergent_scheduler.py`, `dmn_guardian.py`, `self_edit_manager.py`, `echo_model_orchestrator.py`

**Tailscale sync:**
M5 (100.84.229.10) ↔ Air (100.82.172.4) — 1800s cycle, 200-entry batches, SHA-256 dedup, quality floor 0.3
