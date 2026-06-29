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

# Restart after code changes (most fixes require this — Python modules are cached at import time)
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

### Token Limits by Task Type (app/core/echo_model_orchestrator.py: _TASK_TOKEN_LIMITS)
- `personal`, `autonomous_*` → 512 tokens (reflections stay concise)
- `reasoning`, `general`, `creative` → 1024 tokens
- `coding` → 2048 tokens

### FAISS Dual-Index (known split-brain)
`memory_bridge.py` writes to `memory/memory_meta.json` + `memory/faiss.index` — this is the authoritative path used by all runtime code. `app/lib/vector_memory.py` writes to `data/memory_meta.json` + `data/faiss.index` — a secondary path used by some legacy callers. They are separate indexes. Always use `memory_bridge.py` for new code.

### Self-Edit System
Echo autonomously modifies `app/core/self_edit_generated.py` only. The pipeline:
1. `perform_self_edit()` — global 30-min cooldown blocks storm conditions
2. `plan_code_logic()` — generates numbered plan, injects current file contents + module inventory
3. `generate_code_from_plan()` — generates Python only, strips markdown fences
4. `_stage_and_import_test()` — subprocess import test in `staging/` before touching production
5. `backup_existing_code()` + `save_code()` — atomic write with backup

The cooldown is a global in-memory `_last_any_autonomous_edit: float` — it resets on server restart. If the self-edit loop is producing rapid `sandbox_syntax_failure` entries in the interaction log, this is a prompt/model hallucination storm; restart the server to reset the cooldown.

### Machine-Native Awareness (added 2026-06)
- **`app/core/echo_state.py`** — 8D float32 state vector, updated every 120s, persisted to `memory/echo_state.npy`. Dim [3] = system_vitality (1 - RAM/100). Dim [7] = circadian signal.
- **`app/core/curiosity_engine.py`** — self-generated goals via WorldModel topic under-representation → `data/question_garden.jsonl`
- **`app/core/shadow_model.py`** — tracks whether Echo's self-assessments match actual outcomes
- **`app/core/system_guard.py`** — reads `echo_state.npy` dim [3]; returns True (throttle) when RAM > 92%. Called at the top of autonomous loops.

---

## Protected Files (EDIT_FORBIDDEN_TARGETS)

These files are hardcoded in `self_edit_manager.py` and must never be overwritten by self-edits or tooling:

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

**Module inventory for self-edits** (`_build_module_inventory` in `self_edit_manager.py`): only shows `app.*` modules, filters backup/temp files. The inventory labels functions and classes separately to prevent the LLM from treating class names as module names (e.g., `from ToolManager import ToolManager` is a hallucination — the correct import is `from app.core.tool_manager import ToolManager`).

**Autonomous awareness modules** (`app/core/echo_python_mastery/`): all `get_tips()` functions are private (`_get_tips()`). Only `teach_X()` functions are registered as tools. `code_quality.py` caches its filesystem scan for 10 minutes.

**Tailscale sync** (`app/sync/sync_protocol.py`): M5 (100.84.229.10) syncs with Air (100.82.172.4) every 1800s. Quality floor 0.3, 200-entry batches, SHA-256 dedup. `LOCAL_ONLY_SOURCES = {"self_edit"}` — self-edit entries never sync.

**Memory source tags**: entries written by autonomous paths carry `memory_source: "autonomous"`. User conversation entries carry `memory_source: "user_conversation"`. Sync entries carry `memory_source: "sync_m5"` or `"sync_air"`. `retrieve_relevant_memories()` accepts `source_filter` to exclude autonomous self-talk from user-facing context.

**Scripture integrity**: `bible_injection.py` prevents confabulation of cited verses at generation time. Post-response scripture scan in `echo_model_orchestrator.py` logs mismatches to `memory/scripture_warnings.log`. Principle drift is logged to `memory/principle_violations.log`.

---

## Monitoring

```bash
# Watch for self-edit storm (should see 0-1 coding entries per 30 min after fix)
tail -f memory/SELF_EDIT.log

# Watch live interaction quality
tail -f memory/interaction_log.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    print(e.get('task_type'), e.get('quality_score'), repr((e.get('response_preview') or '')[:80]))
"

# Check if self_edit_generated.py is clean
python3 -c "import ast; ast.parse(open('app/core/self_edit_generated.py').read()); print('OK')"

# Check both FAISS indexes for divergence
python3 -c "
import json
m = json.load(open('memory/memory_meta.json'))
d = json.load(open('data/memory_meta.json'))
print('memory/:', len(m.get('texts',[])), 'vectors')
print('data/:  ', len(d.get('texts',[])), 'vectors')
"
```

---

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Rapid `sandbox_syntax_failure` in interaction_log | Self-edit storm — cooldown reset | Restart server |
| `self_edit_generated.py` overwritten with hallucinated imports | Loop fired before cooldown active | Restore baseline, restart |
| `DUPLICATE_SIGNAL_EXACT` dominating scheduler | Empty `__init__.py` files or unchanged pip count generating identical FAISS entries | Fixed in `autonomous_awareness.py` — restart to activate |
| `staging_import_failed: ImportError: cannot import` | Model hallucinated module name | Check generated imports against `_build_module_inventory` output |
| B2 recency check not working (same prompts repeat) | FAISS split-brain — `memory_meta.json` empty or orphaned | Merge `data/memory_meta.json` into `memory/memory_meta.json`, rebuild index |
| Responses cut off mid-sentence | Wrong `num_predict` path | Primary path: `stream_query_ollama` in `ollama_handler.py`. Secondary: `ollama_query` in `echo_model_orchestrator.py`. Both must have matching limits. |
