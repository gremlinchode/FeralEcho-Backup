# FeralEcho Architectural Integrity and Dormant-Capability Audit

**Date:** 2026-09-20
**Mode:** read-only. No production code, configuration, persistent state, model state, Git history, or protocol file was modified. The persistent-competence experimental lineage (v1.0/v1.1 protocol, its tasks/infrastructure/carriers) was treated as quarantined and not opened, critiqued, or extended.
**Companion:** `audits/2026-09-20_feralecho_architecture_evidence_ledger.json` (every numbered finding `F-xx` below, with label, basis, and evidence pointers).
**Method:** AST-based static scans (imports, definitions, call sites, reader/writer resolution for 114 state files, singleton patterns), targeted source reads, and read-only runtime reads (state-file inspection; `GET /admin/liveness-status`, `/admin/autonomy-status`, `/health`; log tails). The static tools live in the session scratchpad only.

> **CORRECTION (2026-09-20, later the same day, from the runtime-identity/state-preservation investigation):** F-34/§8 rank 1/§17 risk 3 described `terminal_client.py`'s independent `VectorMemory` as writing a stale full copy over production files. That omitted a gate: `terminal_client.save_memory()` begins with `if conversation_service.server_is_running(): return`. The hazard is **conditional** (terminal saves while the server is not running, after loading state while it was) and was **reproduced only in an isolated fixture**; production occurrence is UNKNOWN. Also: `RIVER_BRAIN_PATH` is the cwd-relative `"memory/river_brain.pkl"` (not absolute). See `audits/2026-09-20_feralecho_runtime_identity_and_state_preservation.md` §9.

**Claim labels (used throughout).**
- **OBSERVED** — read directly in source or runtime state this session.
- **SUPPORTED** — two independent lines agree (typically source + runtime), but no direct positive test was run.
- **INFERRED** — follows from observed facts by stated reasoning.
- **UNKNOWN** — not established.
- **ABSENT** — searched for and confirmed missing (e.g. zero callers).

"Live scope" = `run.py`, `terminal_client.py`, `echo_quality_scorer.py`, `app/**`, `echo_studio/**`, `sandbox/*.py`, excluding archives, backups, generated project dirs, and `app/experiments/`.

---

## 0. Git and working-tree state

```
Git HEAD (before): 2fba42644c82b9f7096276f4dd338d615cf1bcce   (committed 2026-09-13 22:27 -0700)
Working tree (before): 181 changed/untracked paths
Git HEAD (after): unchanged; working tree (after): 183 paths (+2 new audit files) — see §21
```

**F-02 (OBSERVED):** the running server (PID 29288, started 2026-09-20 07:30 local, sentinel `stage: serving`) executes the **working tree**, not HEAD. 17 tracked files under `app/`, `run.py`, `sandbox/`, `scripts/` carry **1,697 uncommitted insertions / 178 deletions** relative to a commit that is 7 days old. Several of the behaviours audited below (shadow-model retirement, liveness checks, snapshot drift notices, provenance module) exist only in uncommitted state. There is no runtime artifact tying a running process to a commit (`provenance_check.py` was built for this; it is not wired, F-18).

---

## 1. Executive verdict

FeralEcho is a real, live, heavily instrumented system — not vaporware and not a facade. **OBSERVED at runtime:** 187 live-scope modules / ~65.5k lines (F-01); ~19 background threads; 130,838 vectors with FAISS count equal to metadata count; ~210k RiverBrain observations; 54 Liveness Ledger checks all passing; zero vector-persist or brain-save errors in the current 33 MB log window.

The pattern that dominates the architecture is **produce-heavy, consume-light**:

1. **Behaviour is decided by a small core.** Model choice = a per-(model, task) running mean of *one* heuristic text/AST scorer (F-06, F-08). Council-vs-single-model routing = keyword lists (F-32). Retrieval = FAISS cosine + a validator. Everything else mostly *observes*.
2. **Most of the machine's own activity feeds itself.** 97% of the last ~1,192 logged interactions were autonomous (F-04); RiverBrain's selection statistics are therefore trained mostly on Echo's own outputs to Echo's own prompts, scored by that one heuristic (F-09). Human feedback has no path from the primary interface (F-26).
3. **A large amount of state is written and never read by anything that changes behaviour** (F-19–F-22, F-24, F-30, F-31), and several consumers are wired to inert or saturated inputs (F-14, F-15, F-17).
4. **Specific verified defects:** the dream cycle is unreachable by construction (F-10); RiverBrain's ML classifiers are diagnostic-only (F-07); the self-edit loop's deployed artifact has no caller (F-24); `ToolManager` names are shown to models but cannot be executed (F-25); the Global Workspace has effectively one real consumer (F-12/F-13); persistence has a non-atomic pickle and a stale-copy multi-writer hazard (F-34/F-36/F-37).
5. **Documentation lags reality in both directions** (F-41, F-42), and the deployed process has lagged the source (F-40).

**What I did not find:** no evidence of silent data loss *now*; no evidence that the safety gates (F1/F2/F3, Liveness Ledger canaries) are hollow — the ledger's canaries genuinely discriminate on their own terms. The problem is not that verification is fake; it is that verification is applied far more thoroughly to *safety* than to *usefulness*: nothing in the architecture requires an autonomous output to have a consumer.

---

## 2. Current architecture map (traced, not inferred from names)

### 2.1 Entry points
| Entry | What it is | Status |
|---|---|---|
| `run.py` (Flask, 45 routes) started by `start_echo.sh` watchdog | The server + all background threads | OBSERVED live |
| Echo Studio → `POST /chat/stream` → `app/routes_echo_studio.py` | The primary human interface | OBSERVED (per README/CLAUDE.md; route exists) |
| `terminal_client.py` | Secondary interface; **separate process with its own `VectorMemory`** (F-34) | OBSERVED source |
| `POST /mirror_echo` | Phone channel; last learning event ~60 days ago (`learning_events.jsonl`, `dual_meta.json`) | SUPPORTED dormant in practice |
| `/touch|vision|hearing/report` | Sensor ingestion | OBSERVED live (signatures updated) |

### 2.2 The conversational path (OBSERVED, source)
`_generate_chat_response_body` → `_build_full_prompt` (memory via `conversation_service.retrieve_memory_context` → `memory_bridge.retrieve_relevant_memories`; session history; `echo_ground_truth` slices *only if* `_is_introspective(msg)`; tool context *only if* `_needs_tool_context`) → `echo_query` (`resolve_task_type`; system notes: circadian, stillness, temporal, scripture, tool-list) → `river_deliberation.deliberate_and_learn`:
- `task_type ∈ DIRECT_ECHO_TASKS` (personal) → **one** `echo:latest` call (417 of 856 recent council-log rows, F-05);
- otherwise `_select_council` (3 models) → per-councillor `_ollama_query` → each raw opinion `river_brain.learn`-ed individually → synthesis by `echo:latest` with Tier-5 safeguards (`detect_full_agreement`, `find_missing_agreed_definitions`, `select_best_fallback_candidate`) → `post_synthesis_hook` (code/self-knowledge verification) → `log_interaction`, `save_reflection`, `river_brain.learn(synth)`, `CLAUDE_SHARD.assess`.

### 2.3 Background threads (OBSERVED, `run.py`, `start_background_threads`)
| Thread | Period | Shared gate (`should_run_cycle`)? |
|---|---|---|
| DMN Guardian (`dmn_guardian.py`) | 60 s | no (cheap) |
| CouncilRater | 90 s poll | no |
| ReflectionShard autonomy | 300 s, 35% fire | **no** (now makes a real model call, F-13) |
| ClaudeShard autonomy | — | no |
| `autonomous_loop` (external fetch, ~3600 s) | 1800–5400 s | yes |
| `awareness_loop` (dream branch, daily code scan) | poll | yes (`awareness_dream`, `awareness_code_scan`) |
| ModelGuidedOrchestrator (Optuna) | hourly | yes |
| AutonomousSelfEdit | hourly | yes |
| **AutonomousSandbox** (`run_random_sandbox_script`) | 600 s | **no** |
| NightCycle | 3600 s | yes |
| Emergent scheduler | ~300 s (salience-modulated) | yes |
| TailscaleSync / EchoMessaging / EchoCheckin | 1800 s / — / ~3 h | throttle / yes / yes |
| EchoProjectsAutonomy | 6 h | yes |
| IntrospectionChannel / SelfModelUpdater | 120 s / 130 s | no |
| RiverBrain-Writer | ≤60 s | no |

(F-46: ten loop names call the shared gate; the rest do not.) `GET /admin/autonomy-status` (runtime) lists nine gated loops; **`awareness_dream` is not among them** (F-10).

### 2.4 Persistence and recovery skeleton
Sentinel `memory/echo_sentinel.json` (stage/heartbeat), `memory/echo_server.pid`, atomic FAISS+meta swap, RiverBrain pickle (non-atomic), 5-slot snapshot manager, genesis/council hash checks (alert-only), watchdog restart after 10 s.

---

## 3. Producer → state → consumer → behavioural effect

Legend for *effect*: **B** = changes a decision/prompt/selection; **D** = diagnostic/alert only; **H** = historical/log only; **—** = none found.

| # | Producer | State | Consumers (traced) | Effect |
|---|---|---|---|---|
| 1 | `echo_query`/`log_interaction` | `interaction_log.jsonl` | rating cursor, `task_type_classifier` bootstrap, council_rater poll, `self_model_updater`, many audits | B (indirect) |
| 2 | `RiverBrain.learn` | `model_task_stats` (mean/count per model×task) | `_select_council`, `rank_models`, `entropy_of_predictions` | **B — the selection authority** |
| 3 | `RiverBrain.learn` | Hoeffding-tree classifiers + scalers | `predict_one` only feeds `accuracy_trackers` → `introspection_channel` → PageHinkley → `river_drift_sustained` notice | **D** (F-07) |
| 4 | `echo_quality_scorer._score_response_quality` | int 0–4 | RiverBrain, self-edit fitness gate, Optuna, scheduler prompt weights, outcome tracker | **B — single quality authority** (F-08) |
| 5 | `memory_write_validator` | `quarantine_journal.jsonl` (35 MB), `validator_audit.log` (25 MB), `signal_hash_cache.json` | gate itself consumes hash cache; journals only rotated | B (gate) / H (journals) |
| 6 | `memory_bridge.add_to_vector_memory` / `log_dream_bridge` | FAISS + `memory_meta.json` | chat retrieval, dream sampling, scheduler recency, snapshot health | **B** |
| 7 | `EchoCore.publish_salience` | `workspace_log.jsonl` (16,060 events) | logger; `river_deliberation` (940 consumptions); curiosity (1); memory_bridge (0) | mostly D (F-12) |
| 8 | `echo_state` (9-D) | `echo_state.npy`, history ring (100) | seam_engine, echo_ground_truth affect, valence consumers (4) | weak B (F-14/F-16) |
| 9 | `compute_salience` | `salience_state.json` | emergent loop sleep modulation; self-report slice | weak B (F-15) |
| 10 | `seam_engine.observe` | `seam_log.jsonl`, `seam_state.json`, workspace `seam.detected` (84), garden questions | log: **no reader**; workspace: `reflection_shard.observe` (spawns a model call per seam) | B (small) |
| 11 | `curiosity_engine`/`garden_manager` | `question_garden.jsonl` (16,223 entries) | emergent prompt selection | **B** |
| 12 | `WorldModel` (`predictive_loop`) | posterior, `world_model_diagnostics.json` | river exploration bias, curiosity topic pick (read-only), self_model | weak B (surprise ≈ 0.002) |
| 13 | `SelfModelUpdater` (130 s) | `self_model.json` | `echo_ground_truth` (introspective gate), `get_weak_task_type` → self-edit target + scheduler focus, echo_state dim[2] | **B** |
| 14 | chat path | `self_model_claims.jsonl` | `self_knowledge_verification`, ground-truth slice | B (caveats) |
| 15 | human-confirmed only | `behavioral_directives.json` (**empty**) | `echo_ground_truth._build_behavioral` | — (F-17) |
| 16 | — | `provenance_check.py` | **only its verify script** | — (F-18) |
| 17 | Echo Studio chat | `retrieval_provenance.jsonl` | **none** | H (F-19) |
| 18 | `dream_cycle` | `dream_state.json`, `dream.synthesis` | **unreachable producer** | — (F-10) |
| 19 | `reflection_shard` class | `reflection_journal.jsonl` | echo_optuna, echo_state valence component, night-cycle rotation | B (small) |
| 20 | `save_reflection` | **`reflection_shard.jsonl`** (38 MB; *not* the class's file) | `rank_models` (whole-file parse per call), `self_model_updater` | B (legacy rank blend) |
| 21 | self-edit loop | `self_edit_generated.py` | **no live importer/caller** (F-24) | — (artifact); telemetry side-effects B |
| 22 | self-edit loop | `self_edit_attempt_ledger.jsonl`, `SELF_EDIT.log`, `self_edit_outcomes.jsonl` | convergence backfill, outcome tracker, prompt-building (last F2 error), liveness | B (prompt shaping) |
| 23 | `echo_projects` (6 h) | `sandbox/echo_projects/*` (61) + reports | **human review only** | — |
| 24 | `council_rater` | `council_ratings.jsonl` | `learn_from_council_rating` (30/70 blend, trust-gated) | **B** |
| 25 | terminal rating only | `user_rating_cursor.json` | `learn_from_rating` (3× weight) | B — but no primary-UI path (F-26) |
| 26 | `snapshot_manager` | `restore_alerts.jsonl`, snapshots | **no programmatic reader**; human action | D (F-21) |
| 27 | `crash_awareness` | `mlx_crash_avoidance.json` | `list_mlx_models()` filter → council pool | **B** (hidden, F-43) |
| 28 | touch/vision/hearing endpoints | `*_signature.json` | own modules + liveness checks only | — (F-30) |
| 29 | `DualLearner` | `learning_events.jsonl`, `dual_meta.json` | phone download only | — (F-31) |
| 30 | `ToolManager` | tool-name list | injected as "Available tools:" text; **no executor** | prompt only (F-25) |
| 31 | `echo_tool_dispatch` | `tool_dispatch.log`, `thought_log.jsonl` | 3 executable tools; logs unread | B (tool result) / H |
| 32 | `wolf_friction_bridge` | `wolf_dryrun.jsonl` | `get_dry_run_tally`: **0 callers** | — (F-29) |

---

## 4. Producer-without-consumer findings

| ID | State produced | Classification | Label |
|---|---|---|---|
| F-07 | RiverBrain Hoeffding trees + scalers (trained every response) | **DIAGNOSTIC ONLY** — predictions exist solely to score accuracy → drift notice; they never rank or gate anything | OBSERVED (`grep predict_one`) |
| F-10/F-11 | `dream_state.json`, `dream.synthesis`, `self_model.json:recent_dream_synthesis` | **DEAD producer**; downstream fields carry a 2026-07-15 synthesis | SUPPORTED |
| F-19 | `retrieval_provenance.jsonl` (which memories were injected per chat turn) | DIAGNOSTIC/HISTORICAL — zero readers | OBSERVED |
| F-20 | `seam_log.jsonl` | DIAGNOSTIC (events, not the log, have consumers) | OBSERVED |
| F-21 | `dissent_log.jsonl` (last write 1,573 h ago), `restore_alerts.jsonl` (92 alerts) | HISTORICAL — zero readers | OBSERVED |
| F-22 | `council_deliberations.jsonl` (29.8 MB + 8.2 MB gz), `synthesis_integrity_log.jsonl` (9 MB), `scheduler_selections.log`, `quarantine_journal.jsonl` | HISTORICAL — read only by rotation and offline scripts | OBSERVED |
| F-24 | `self_edit_generated.py` deployments | **artifact has no caller**; only the telemetry side-effects are used | OBSERVED |
| F-29 | `wolf_dryrun.jsonl`, friction events | DIAGNOSTIC; friction raised 0 of last 50 | OBSERVED |
| F-30 | touch/vision/hearing signatures (50,126 / 14,728 / 30,000 observations) | DIAGNOSTIC (liveness only) | OBSERVED |
| F-31 | `learning_events.jsonl`, dual-learner model | serves the phone only | OBSERVED |
| F-25 | `thought_log.jsonl` (from the `log_thought` tool) | HISTORICAL — write-only tool | OBSERVED |
| F-45 | `codebase_map.json` (rewritten daily) | DERIVED duplicate — the SQLite `CartographerDB` is what is consumed | OBSERVED |
| F-42 | `dark_light_pipeline.run_pipeline` | imported into `run.py` (line 288), **never called**; carries a placeholder API key | OBSERVED |

**Names that imply learning/adaptation but resolve to logging:** `RiverBrain` classifiers (F-07), `dissent`, `seam`, `provenance` outputs, "self-edit" artifact (F-24), `coupling_estimate` (consumer: a self-report sentence only).

---

## 5. Consumer-without-meaningful-producer findings

| ID | Consumer | Input reality | Label |
|---|---|---|---|
| F-17 | `echo_ground_truth._build_behavioral` (prompt injection) | `behavioral_directives.json` = `{"directives": [], "version": 1}` — human-confirm-only, currently empty | OBSERVED |
| F-14 | `seam_engine`, salience, affect slice, valence consumers | Over the last 100 readings only vitality, curiosity_index, and circadian phase vary; `processing_novelty ≈ 0.0002`, `coherence_tension ≈ 0.120 ± 0.0003`, **`orientation_drift = 1.0` exactly**, **`friction_rate = 0.0` exactly**, `edit_momentum ≈ 0.03`, `valence` std 0.008 | OBSERVED (runtime) |
| F-14 | `echo_state` dim[2] | computed from `weekly_delta`; `creative: −1.0` (tiny-n) saturates the mean → constant 1.0 | OBSERVED |
| F-15 | emergent-loop sleep modulation, self-report | salience components: `world_surprise 0.0017`, `coherence_tension 0.12`, `curiosity_urgency 0.9999` (saturated), `self_edit_streak 0.0` → score 0.28 | OBSERVED |
| F-16 | valence consumers (emergent weights, river exploration bias, optuna bounds, affect slice) | real wiring, near-constant input | SUPPORTED |
| F-06 | `rank_models` `influence_weight` | saturated at its 0.65 cap (210k observations) — the "blend" is a constant | OBSERVED |
| F-11 | `self_model.json:recent_dream_synthesis` | stale since 2026-07-15 | OBSERVED |
| — | `memory_bridge.set_workspace_bias` ← `dream.synthesis` | 2 events all-time; 0 consumption events | OBSERVED |
| F-08 | RiverBrain / fitness gate / Optuna | fed by a heuristic that scores code by *parse validity + AST complexity* and prose by substance/penalty keywords; never executes code | OBSERVED |

---

## 6. Broken or missing wires

Not implementing any; ranked by how plausible an intended connection is.

| ID | Signal exists | Plausible consumer | Missing wire | Class |
|---|---|---|---|---|
| F-26 | `RiverBrain.learn_from_rating` (3× human weight) | Echo Studio (primary UI) | No rating submission path found in `echo_studio/` or `routes_echo_studio.py`; only `terminal_client` writes the rating file; `user_rating_cursor.json` last updated ~78 days ago | **A/B** — restores intended wiring / exposes existing capability |
| F-18 | `provenance_check.py` (git identity of files, process identity) | liveness ledger, `echo_ground_truth`, restore alerts | zero live importers | B |
| F-28 | `functional_quality.py` (execution-based candidate check) | `_score_response_quality` for autonomous coding | deliberately un-imported (documented decision, 2026-09-06) | C (a training-signal change; explicitly Gremlin's call) |
| F-19 | `retrieval_provenance.jsonl` | answer-quality attribution, self-knowledge verification | no reader | B |
| F-22 | raw per-councillor opinions + which text survived synthesis | per-model "synthesis survival" stats | logged, never aggregated | D (new feature on existing data) |
| F-30 | sense signatures | stillness/scheduler/ground-truth | none | B |
| F-29 | wolf dry-run tally | any consumer | none | B/legacy |
| F-21 | dissent log; restore alerts | ground-truth slice / human dashboard | Echo Studio surfaces liveness and workspace events but not these | B |
| F-13 | `dream.synthesis` → memory_bias | needs producer alive (F-10) | producer unreachable | A (bug) |
| F-24 | self-edit deployments | tool registry / apply hook | `apply_to_code` undefined in deployed file; no other caller | C/D |
| F-25 | `ToolManager` registered functions | an executor | listing-only | C |

The already-known sandbox-outcome/RiverBrain disconnect is the same *class* as these; per instruction it was not re-investigated here.

---

## 7. Duplicated responsibilities

| Concept | Implementations (traced) | Interaction | Who controls behaviour |
|---|---|---|---|
| **Task type** | `compute_intent_heatmap` keyword scoring; `detect_task_type` = trust-gated Naive-Bayes classifier → keyword ladder; per-model tags (`detect_model_tags`); `TASK_TYPE_MAP` defined twice (`echo_model_orchestrator.py:717`, `echo_quality_scorer.py:495`) | `resolve_task_type`: heatmap primary unless <0.4, then `detect_task_type`. The duplicated map is guarded by liveness check `task_type_map_sync`. | heatmap/keywords; NB classifier only after trust gates (F-32) |
| **Model selection** | (a) `_select_council` (chat): `score_model` + `ECHO_SCORE_BOOST` + `TAG_SCORE_BOOST` + exploration; (b) `rank_models`/`choose_model` (self-edit generation; council *reviewers* in self-edit, echo_projects, restore): legacy reflection-count score blended by `influence_weight` (constant 0.65) with `score_model` | Different math, same underlying stats; (b) parses the 38 MB `reflection_shard.jsonl` on **every** call | (a) for conversation; (b) for code generation and review councils (F-06) |
| **Competence / quality** | `_score_response_quality` (AST/keyword); LLM peer rating (30% blend when trusted); human rating (terminal only); `code_verification` (conversational coding claims); self-edit fitness gate (same AST scorer); shadow model (retired) | Not independent: everything but peer/human/code_verification derives from the same scorer | the heuristic scorer (F-08) |
| **Self-knowledge** | `self_model.json`; `self_model_claims.jsonl`; `echo_state.npy`; `introspection_state.json`; `shadow_self_model.json` (stale); `behavioral_directives.json` (empty); `liveness_ledger.json` | Layered, not conflicting; only `self_model.json` reaches behaviour (`get_weak_task_type`) and words (introspective gate) | `self_model.json` |
| **Tools** | `ToolManager` (list-only) vs `echo_tool_dispatch` (3 executable tools) | Never interact; the prompt lists the former's names as "Available tools:" | `echo_tool_dispatch` is the only executable path (F-25) |
| **Scheduling** (F-33) | `emergent_scheduler` loop; `app/core/scheduler.py` (orphan, never imported); `schedule_task`/`run_pending` (print stubs, 0 callers) | dead duplicates | `emergent_loop` |
| **Liveness** | `liveness_ledger` (54 checks), `dmn_guardian`, `introspection_channel`, `snapshot_manager.check_and_alert`, `self_report_verifier` (disconnected), `self_heal` (disconnected) | alert-only; only Ollama restart is automatic | human |
| **Memory relevance** | FAISS cosine; workspace bias; recency exclusion; source preference (`user_conversation`); validator gates | layered | `retrieve_relevant_memories` |
| **Uncertainty** | `entropy_of_predictions` (over scores), WorldModel surprise, salience, coherence_tension | independent inputs to different consumers | exploration bias / scheduler sleep |
| **Reflection logs** | `reflection_shard.jsonl` (per-interaction, written by `save_reflection`) vs `reflection_journal.jsonl` (written by the `ReflectionShard` class) | **name collision** (F-42) | — |

---

## 8. Singleton / global-state map

Scan: 44 live-scope modules carry module-level mutable state, lazy-global getters, locks, or import-time work (94 items; ledger `singletons`). Ranked risks:

| Rank | Pattern | Evidence | Risk to |
|---|---|---|---|
| 1 | **Independent `VectorMemory` on production paths in a second process** — `terminal_client.py:102` builds `VectorMemory("memory/faiss.index","memory/memory_meta.json")`; `save_memory()` (line 478) → `vm.add` → `_persist()` rewrites the **entire in-memory** meta and index. `VectorMemory` has no reload, merge, or file lock. | F-34 (SUPPORTED, source; not exercised) | PRODUCTION INTEGRITY, MULTI-INSTANCE |
| 2 | **Import-time construction** — `memory_bridge` builds `VectorMemory` (loads 100 MB JSON + 200 MB FAISS) and the SentenceTransformer at import; **28** live modules import it | F-34 | TEST VALIDITY, MULTI-INSTANCE |
| 3 | **RiverBrain** — `get_river_brain()` singleton; every construction (`RiverBrain()`/`.load()`) starts its own writer thread; global `RIVER_BRAIN_PATH`; 32 importers of the orchestrator | F-36 | TEST VALIDITY, RESTART |
| 4 | **Hard-coded absolute paths** — `claude_shard.py`, `reflection_shard.py` use `~/Desktop/FeralEcho/memory/...`; 87 literal cwd-relative `"memory/..."` strings in 26 files vs 65 `MEMORY_DIR` uses in 14; `.claude/worktrees/*` holds a full repo copy | F-35 | MULTI-INSTANCE (a worktree/clone writes into the primary's state) |
| 5 | Other singletons: `TaskTypeClassifier` (`_instance`), `EchoCore` (`get_echo_core`), `WorldModel` (`_init_lock`), `ToolManager` (`__new__`), `sentence_transformer_singleton` | source | TEST VALIDITY |
| 6 | In-process global caches lost at restart: `_friction_window`, `_cb_state` (circuit breakers), **`_SESSIONS` (Echo Studio conversation history)**, `_workspace_bias`, `_last_world_surprise` | `routes_echo_studio.py:39` | RESTART CORRECTNESS |
| 7 | Autosave: RiverBrain writer rewrites the 4.4 MB pickle every ≤60 s even when nothing changed (`total_obs=210691` logged three times consecutively); `VectorMemory.add` persists 100 MB `indent=2` JSON + 200 MB FAISS **per add** and does an O(N) `id not in id_order` list scan | F-36/F-37 | PRODUCTION INTEGRITY (write amplification) |
| 8 | Import-time file loads: `bible_injection` loads a 7.7 MB JSON into `VERSE_INDEX` at import; `dark_light_pipeline` calls `logging.basicConfig` at import | source | TEST VALIDITY |

Documented prior isolation gap (RiverBrain background writer, CLAUDE.md Finding 89) is consistent with #3 and was not re-derived.

---

## 9. Persistence inventory

(Full per-file reader/writer resolution is in the ledger. Below: the load-bearing stores. "Derived" = rebuildable from other state.)

| Store | Format | Writers | Readers / when | Authoritative? | Corruption detectable? | Backed up? |
|---|---|---|---|---|---|---|
| `memory/faiss.index` (200 MB) + `memory_meta.json` (100 MB) | FAISS + JSON | `VectorMemory._persist` (per add; atomic tmp+replace, meta first) | startup load; every search | meta authoritative; index derived-in-principle | mismatch → **warning only**; meta parse failure → `{}` then next persist overwrites; index read failure → empty index persisted immediately (F-37) | snapshot manager (health only for meta count; artifacts list is the 5 small files — **FAISS/meta are not in `_ARTIFACTS`**: UNKNOWN whether other backups exist beyond dated `memory_meta_backup_*.json`) |
| `river_brain.pkl` (4.4 MB) | pickle | `RiverBrain._do_save` (**non-atomic**, `fcntl` lock) | startup `load()` | authoritative for `model_task_stats` | parse failure → "starting fresh" (state loss); the richer-guard swallows the same failure and overwrites | snapshots (5 retained) + `river_brain.pkl.pre_*` files |
| `task_type_classifier.pkl` | pickle | `_write_if_richer` | startup | derived-ish (bootstrap from log exists) | guarded by richness | snapshot: no (UNKNOWN) |
| `drift_detectors.pkl` | pickle | introspection | startup | derived | — | no |
| `self_model.json` | JSON | SelfModelUpdater (130 s) | ground-truth, self-edit targeting, echo_state | derived (rebuilt every cycle) | staleness check via liveness | weekly history copy (`memory/history/`, night cycle) |
| `interaction_log.jsonl` (19 MB) | JSONL | `log_interaction` | many | authoritative record | line-level | rotation to `.1.gz` (single generation) |
| `SELF_EDIT.log` (28 MB) | log | self-edit | `backfill_convergence_from_log` (full replay) | authoritative for convergence history | — | exempted from rotation (documented) |
| `echo_state.npy`, `echo_state_history.npy` | numpy | echo_state (120 s) | seam, valence consumers | derived | — | daily archive to `memory/history/` |
| `question_garden.jsonl` (`data/`) | JSONL | garden_manager | scheduler, curiosity | authoritative | — | UNKNOWN |
| `workspace_log.jsonl` (5 MB), `seam_*`, `dissent_log`, `restore_alerts`, `retrieval_provenance` | JSONL | see §3 | mostly none | records | — | — |
| `echo_sentinel.json`, `echo_server.pid` | JSON/text | `run.py` | startup, terminal_client, conversation_service | authoritative for liveness | stale after `kill -9` | — |
| `snapshots/*` (40 files) | copies | `snapshot_manager` | `/admin/restore` (human) | derived copies | sha256 recorded | self |
| `optuna.db` | SQLite | optuna | optuna | authoritative for trial history | SQLite | no |

**Startup reads:** sentinel, genesis/council hashes (alert-only), river pickle, FAISS+meta, classifier pickle, self-edit cooldown. **Shutdown:** `shutdown_handler` unlinks the PID file and calls `kill_wolf_gracefully` (a no-op); **`RiverBrain.shutdown()` has zero callers** (F-38). Loss window ≤ ~65 s of RiverBrain observations on SIGTERM; SIGKILL by the watchdog can additionally interrupt a non-atomic pickle write.

---

## 10. Documentation vs reality

| Claim (source) | Reality | Class |
|---|---|---|
| README: CLAUDE.md "89 and counting" | CLAUDE.md contains 95 numbered findings | DOCUMENTATION STALE |
| README: `RebelCode/` = "Echo's more autonomous, less-gated exploratory layer" | No live module imports it (`howl_engine`, `territory_steward` never imported) | **NAME OVERSTATES FUNCTION** |
| README: `books/` "for the scripture-injection layer" | `bible_injection.py` loads root `bible_sentiment.json`; `books/` is never read at runtime | DOCUMENTATION OVERSTATES |
| `structure.md` (last updated 2026-06-27): `terminal_client.py` "primary human↔Echo interface" | README/CLAUDE.md: Echo Studio is primary | DOCUMENTATION STALE |
| CLAUDE.md Liveness Ledger section: "22 checks" (later text 41) | 54 checks at runtime (F-03) | DOCUMENTATION STALE |
| CLAUDE.md: "shadow_model RETIRED FROM LIVE USE 2026-09-13" | Process logged `[SHADOW] Accuracy logged` through 2026-09-19 10:14; source now has no live callers; files stale since | IMPLEMENTATION LAGGED SOURCE → now matches (F-40) |
| CLAUDE.md Finding 11 / Phase 1 Area 5: DMN dream cycle "live-verified" | Verified by a direct call; the autonomous path is unreachable (F-10) | **DOCUMENTATION OVERSTATES** |
| CLAUDE.md: Global Workspace has real consumers `memory_bridge`, `river_deliberation`, `curiosity_engine` | Runtime: 940 / 1 / 0 consumption events respectively (F-12) | PARTIALLY MATCHES |
| Name `reflection_shard.jsonl` | Not written by `ReflectionShard`; that class writes `reflection_journal.jsonl` | **NAME MISLEADS** |
| Name `RiverBrain` "learned model" | selection uses `model_task_stats` (a mean table); classifiers are diagnostic | NAME OVERSTATES FUNCTION |
| `ToolManager` "Available tools" prompt line | names are not executable | NAME/PROMPT OVERSTATES |
| `emergent_scheduler.schedule_task` | `print` stub | NAME OVERSTATES |
| `self_edit_generated.py` output as "self-improvement" | no live caller (F-24) | NAME OVERSTATES |
| CLAUDE.md: `apply_to_code` hook honestly inert / `not_deployed` | matches (liveness: "does not currently define apply_to_code") | BEHAVIOR MATCHES CLAIM |
| CLAUDE.md: Liveness canaries discriminate; `task_type_map_sync` guards duplicated map | source shows both maps and the guard | BEHAVIOR MATCHES CLAIM |
| CLAUDE.md: FAISS/meta consistency, non-atomic pickle noted? | FAISS==meta at runtime; the pickle non-atomicity is **not** documented | MATCH / gap |

---

## 11. Dormant capability findings

Classification of what activation would be — **A** restoring intended wiring; **B** exposing already-existing capability; **C** changing architecture; **D** new capability. None activated.

| ID | Mechanism | State | Activation class |
|---|---|---|---|
| F-10 | `dream_cycle` (two-pass synthesis + question harvest) | implemented, tested by direct call, **unreachable** (mutually exclusive gate) | **A** |
| F-26 | `learn_from_rating` (human 3× rating) | implemented; fed only by terminal | **A/B** |
| F-18 | `provenance_check` (git/process identity) | implemented, verified by its own script, unwired | **B** |
| F-28 | `functional_quality` (execution check) | implemented, deliberately unwired | **C** (training-signal decision) |
| F-07 | Hoeffding-tree quality predictors (features per response) | trained, never used for a decision | **C/D** |
| F-19 | `retrieval_provenance` | recorded, unread | **B** |
| F-22 | per-councillor raw outputs + synthesis-survival | recorded, unaggregated | **D** |
| F-20/F-21 | seam log, dissent log | recorded, unread | **B** |
| F-30 | sense signatures | recorded, unread | **B** |
| F-24 | self-edit deployments as callable/registered capability | produced, uncalled | **C/D** |
| F-25 | `ToolManager` registry as executor | listing only | **C** |
| F-45 | `codebase_map.json` | derived duplicate | — (no value) |

---

## 12. False-sophistication findings

State precisely what each does; not mocking.

| ID | Looks like | Is |
|---|---|---|
| F-07 | Online ML "brain" learning per task | A per-task Hoeffding tree whose only downstream use is an accuracy number feeding a review-only drift notice; selection uses a running mean table. |
| F-08 | "Quality" / "authentic, scripturally sound" 0–4 | For code: parse validity + AST node counts (no execution). For prose: substance/penalty/scripture keyword heuristics. 5 discrete values; recent mean 2.31. |
| F-06 | Adaptive blending `influence_weight` | Saturated constant 0.65. |
| F-16/F-14 | 9-D affective/state vector with valence | 3 varying dimensions; valence std 0.008; `orientation_drift` pinned at 1.0 by a tiny-n weekly delta; `friction_rate` pinned at 0. |
| F-15 | Salience + coupling estimate | components: one saturated (0.9999), one ≈0, one ≈constant, one 0; `coupling_estimate` reaches only a self-report sentence. |
| F-24 | Autonomous self-editing with F1/F2/F3, Optuna | 1,086 attempts in 13 days, **14 deployed (1.3%)**, 77% fail at staging import; the deployed file is executed at load but no function in it is called. Effects are telemetry (self_edit_coding stats, valence input, convergence). |
| F-25 | Tool use | Names shown to models; the only executable tools are 3 (read_file, search_memory, log_thought). |
| F-10 | Dreaming | Unreachable by gate logic. |
| F-29 | Friction → self-edit bridge | 0 friction of the last 50 assessments; dry-run outputs unread. |
| F-13 | Global Workspace "broadcast" | 61% of events are the emergent loop's own salience heartbeat; one real consumer in practice. |
| F-44 | Autonomous project building | 61 projects; report parse shows 39 F2 FAIL, 1 PASS, 21 unparsed (SUPPORTED; regex incomplete); last cycle `f2_failed`. |
| F-17 | Behavioural directive store | empty. |

---

## 13. Hidden-capability findings

Mundane-looking pieces with outsized influence (code-evidenced):

1. **`echo_quality_scorer.py` (repo root, 1 file):** sole quality authority for RiverBrain, the self-edit deploy gate (`rejected_not_improvement`), Optuna scores, scheduler prompt weights, outcome tracking (F-08).
2. **Keyword lists in `compute_intent_heatmap`/`detect_task_type`:** decide whether a message gets a 3-model council or a single call (`DIRECT_ECHO_TASKS`); "do you", "would you", "echo", "identity"… → personal → no council (417/856 recent council rows).
3. **`crash_awareness` + `list_mlx_models()`:** a crash-report file scan silently removes MLX councillors from the pool for a cooldown (currently inactive: `avoid_until: null`).
4. **`ollama_handler._get_echo_identity_block()`:** re-reads the `Modelfile` (mtime-cached) and prepends it to every `echo:latest` system message — editing a config file changes live identity without a restart.
5. **`memory_write_validator`:** gate on all memory writes; 5,181 of the 5,190 most recent quarantines are `DUPLICATE_SIGNAL_EXACT` — it is what keeps repeated fetch snippets out of FAISS.
6. **`autonomy_coordinator.should_run_cycle` + `conversation_activity`:** the one gate that defers ten loops to a live conversation *and* (by an exclusivity bug) disables `awareness_dream` (F-10).
7. **`self_edit_manager.load_self_edit_module` → `exec_module`:** runs deployed generated code's top level inside the production process (F3 AST scan only); the generated file currently begins `from app.emergent_scheduler import select_next_prompt`, i.e. loading it imports live modules. (OBSERVED; safety gates F1/F2/F3 are genuine — this is authority, not a bypass.)
8. **`snapshot_manager.check_and_alert`:** emits a `[RESTORE-ALERT]` with a suggested restore command for **RAM pressure** (78 of 92 alerts) — semantically the wrong remedy, and hence effectively noise.
9. **`night_cycle` (hourly):** snapshots self_model weekly, rotates 10+ logs, and (weekly) runs `echo_janitor` with real archiving of narrow categories — an autonomous file-mover living inside a "reflection" module name.

---

## 14. Authority graph

```
HUMAN ────────────────────────────────────────────────────────────────┐
 │ chat (Echo Studio /chat/stream)                                    │ approves: restores, principle/Modelfile edits,
 ▼                                                                    │ propose_core_edit patches, janitor 'flag' items,
resolve_task_type (KEYWORDS ▸ NB classifier if trusted)               │ directive confirmation, rating (terminal)
 ├─ personal ───────────► echo:latest alone                           │
 └─ other ─► _select_council ◄── RiverBrain.model_task_stats ◄── echo_quality_scorer (heuristic)
              │                 ◄── crash_awareness pool filter          ▲
              ▼                                                          │ (97% autonomous data)
      3 councillors ─► synthesis (echo:latest) ─► post_synthesis_hook ─► response
              │                                   (code_verification / self_knowledge caveat)
              ▼
   memory_write_validator ─► FAISS (retrieved next turn: user_conversation preferred)

AUTONOMOUS TRIGGERS (all ▸ should_run_cycle: RAM/stillness/conversation):
  emergent_loop ▸ question garden ▸ echo_query ▸ reflection ▸ FAISS ▸ salience ▸ seam ▸ workspace ▸ reflection_shard(model call)
  self_edit_loop ▸ generate ▸ F1/F2/F3 ▸ fitness gate ▸ save_code ▸ exec_module (no callers)
  night_cycle ▸ snapshot/rotation/janitor(archive) ; echo_projects ▸ sandbox dir (human review)
  UNGATED by shared gate: AutonomousSandbox, ReflectionShard, ClaudeShard, guardian, introspection, self_model, council_rater
```

Direct answers:

| Decision | Ultimate authority (OBSERVED) |
|---|---|
| Which model is selected | `_select_council` (chat) / `rank_models` (code generation, review councils) over `model_task_stats`, boosted/explored |
| Which memory enters context | `retrieve_relevant_memories` (+workspace bias) → `retrieve_memory_context` filter (recency, `user_conversation` preferred) |
| Which candidate wins | none is "chosen": synthesis rewrites; Tier-5 rules can bypass synthesis when all AST-equal or fall back to a candidate |
| What survives restart | FAISS/meta, RiverBrain pickle, self_model, ledgers; **not** `_SESSIONS`, breakers, workspace bias |
| What triggers autonomous action | timers + `should_run_cycle`; `simulate_self_edit` on friction (dry-run only) |
| What can modify persistent state | ~19 threads; `add_to_vector_memory` gated by validator; RiverBrain learn from any interaction |
| What can execute code | F2 sandbox (self-edit staging, echo_projects, experiment runner, code_verification, AutonomousSandbox); **and** `exec_module` of the deployed self-edit file in-process |
| What can modify the repository | self-edit → `self_edit_generated.py` (+ backups); `echo_janitor` (weekly, archive of `known_clutter/duplicate/old_log` only); `log_retention`; snapshot restore (human-confirmed). **No live code uses git** (only unwired `provenance_check`). |
| What can veto | F1/F2/F3, fitness gate, `EDIT_FORBIDDEN_TARGETS`, validator, throttle/stillness; **no component can veto a model-selection outcome**; dissent log has no gating role |
| What requires human approval | restore, principle/Modelfile changes, `propose_core_edit`, directive creation, janitor `flag` items, ratings |

---

## 15. Failure and recovery map

| Failure | Behaviour | Class |
|---|---|---|
| Crash (MLX SIGABRT, etc.) | watchdog restarts in 10 s; `crash_awareness` may withhold MLX; ≤~65 s RiverBrain loss | **WITH FALLBACK / minor STATE LOSS** |
| SIGTERM | PID unlinked; **no RiverBrain flush**; sentinel not marked clean | **WITH STATE LOSS (≤65 s)** |
| Watchdog `kill -9` of port holder mid-`_do_save` | truncated non-atomic pickle possible; `load()` → "starting fresh"; richer-guard `except: pass` then overwrites | **WITH STATE CORRUPTION RISK → SILENT STATE LOSS** (mitigated by human restore from snapshots) |
| Corrupt `memory_meta.json` | `{}` loaded; index loaded; next add persists 1 entry over the file | **STATE CORRUPTION RISK** |
| FAISS read failure | empty index built **and persisted immediately** | **STATE LOSS RISK** |
| Meta/index count mismatch | warning; self-corrects on rebuild | OPEN (detection only); runtime: 0 mismatches |
| Second process persisting stale `VectorMemory` | overwrites newer server entries | **SUPPORTED corruption risk** (F-34) |
| Stale PID after `kill -9` | file remains; consumers (`terminal_client`, `conversation_service`) may trust it | UNKNOWN impact |
| Ollama down | guardian `ollama serve` restart with cooldown; circuit breaker per (model, task); legacy uncapped subprocess fallback on HTTP failure | **WITH FALLBACK** |
| Malformed model output | extraction fallbacks; scorers return low | CLOSED (scored) |
| Sandbox unavailable | `FileNotFoundError` → fails closed | **CLOSED** |
| Corrupted `self_edit_generated.py` | F3 scan → restore latest backup | **CLOSED** |
| Alert conditions | logged/jsonl; nothing consumes; only Ollama restart automatic | **OPEN (human-only)** |
| Running-code ≠ committed code | undetected | **SILENTLY** (F-02) |

Not induced: no destructive test was run. All entries are from source reading plus the runtime log window (0 persist/save failures).

---

## 16. Zero-cost opportunity ranking

Rank order = evidence value first, then capability value; **all require no new paid service, no larger model, no API spend, and no new dependency.** None implemented.

| # | Opportunity | Type | Evidence value | Capability value | Cost | Regression risk | Reversibility |
|---|---|---|---|---|---|---|---|
| 1 | Give a running process a commit identity: wire `provenance_check` into liveness/ground-truth; commit the working tree | WIRING REPAIR / EXPOSURE | very high (F-02) | medium | low | very low | full |
| 2 | Fix `dream_cycle` gate exclusivity (`should_run_cycle` false in stillness) | BUG FIX | high | medium (restores DMN consolidation + workspace producer + self_model field) | low | low–medium (resumes MLX/Ollama calls during stillness) | full |
| 3 | Atomic `RiverBrain._do_save` + flush in `shutdown_handler` + refuse to overwrite an unreadable pickle | BUG FIX | high | protects the selection state | low | low | full |
| 4 | `VectorMemory`: never persist after a failed load; lock or refuse concurrent writers; drop `terminal_client`'s local `vm.add` (write via server only) | BUG FIX | high | protects 130k memories | low–med | low | full |
| 5 | Echo Studio rating affordance → existing `learn_from_rating` | EXPOSURE | very high (only independent human signal; F-26) | high | medium (UI + route) | medium — **training-signal path; Gremlin's call** | full |
| 6 | Aggregate raw councillor opinions vs synthesis survival into per-model stats (data already logged) | NEW FEATURE on existing data | high | high | medium | low if observational-first | full |
| 7 | Make prompt honest about tools: stop listing non-executable `ToolManager` names, or route them through the executor | ARCH/BUG | medium | medium | low | low–med | full |
| 8 | Suppress/reshape `[RESTORE-ALERT]` for resource pressure; give alerts a reader (dashboard) | WIRING REPAIR | medium | low–med | low | very low | full |
| 9 | Either use the Hoeffding classifiers (e.g. response pre-screen) or stop training them | ARCH CHANGE | medium | medium | medium | medium | full |
| 10 | Compute orientation_drift with a minimum-n floor; cap saturating dims | BUG FIX | medium | low | low | low | full |
| 11 | Anchor `claude_shard.py`/`reflection_shard.py` and relative `"memory/…"` paths to `config.MEMORY_DIR` | BUG FIX | medium | protects multi-instance | low | low | full |
| 12 | Documentation reconciliation (README counts, `books/`, `RebelCode`, `structure.md`, liveness count, dream status) | none/doc | medium | low | low | none | full |
| 13 | Give every autonomous loop an explicit consumer contract in its liveness check (not just "ran") | ARCH CHANGE | high | high | medium | low | full |
| 14 | Wire `functional_quality` into autonomous-coding scoring | ARCH CHANGE | high | high | medium | **high** (changes the selection signal; explicit Gremlin decision) | full |

---

## 17. Top 10 architectural risks

1. **Running process ≠ committed code**; 1,697 uncommitted lines; no runtime commit identity (F-02, F-18).
2. **Closed-loop single-scorer learning:** selection trained 97% on autonomous output, scored by one heuristic that never executes code; no human path from the primary UI (F-04, F-08, F-26).
3. **Multi-writer `VectorMemory`:** `terminal_client` persists a stale full copy over production files (F-34).
4. **Non-atomic RiverBrain pickle** + silent "start fresh" + guard that swallows the same failure + no shutdown flush + watchdog `kill -9` (F-36, F-38).
5. **Failed-load-then-persist in `VectorMemory`:** corrupt meta or unreadable index can overwrite good state with empty state (F-37).
6. **Import-time singletons on production paths** (28 importers of `memory_bridge`) make any test/tool process a potential production writer (F-34).
7. **Unreachable dream cycle presented as live**, with stale downstream fields (F-10, F-11).
8. **Self-edit compute with no consumer** and in-process `exec_module` of its output (F-24).
9. **Alerting that no one reads and that recommends restores for RAM pressure** (F-21).
10. **Hard-coded absolute/relative paths and worktree copies** that let non-primary checkouts write into primary state (F-35).

---

## 18. Top 10 underused existing capabilities

1. Independent verification signals: peer-council ratings are 1-in-5 sampled and human ratings are terminal-only, while the bulk of data is heuristic-scored (F-26, F-27).
2. `functional_quality.py` execution check (built, validated, unwired by decision) (F-28).
3. Raw multi-model candidate diversity in `council_deliberations.jsonl` — logged in full, never aggregated (F-22).
4. `provenance_check` git/process identity (F-18).
5. `retrieval_provenance` — which memories actually shaped each answer (F-19).
6. RiverBrain classifier features/predictions (F-07).
7. Dream consolidation (F-10).
8. Sense signatures (F-30).
9. Seam/dissent outputs as anything other than transient events (F-20/F-21).
10. Self-edit deployments as a callable capability (F-24), and `ToolManager` as an executor (F-25).

---

## 19. Questions that remain UNKNOWN

- Whether `dream_cycle()` would run correctly if reached (no positive test was run; only logic + runtime absence).
- Whether the `terminal_client` lost-update race occurs in practice (terminal not running; race not reproduced).
- Whether Echo Studio has a rating control I did not find in `echo_studio/` (searched `rating`/`rate`; only display code found).
- How often a council's selection is decided by boosts/exploration rather than score differences (needs replay of `council_deliberations.jsonl`).
- The share of autonomous vs human interactions over longer windows (one ~23 h window sampled).
- Whether FAISS/meta are backed up outside `memory_meta_backup_*.json` snapshots (snapshot `_ARTIFACTS` does not list them).
- Impact of a stale `echo_server.pid` on `terminal_client`/`conversation_service`.
- Whether the Air (sibling) instance shares these defects; it was not audited.
- Real echo_projects pass rate (report-parsing was regex-based and incomplete: 21/61 unparsed).
- Effect size of valence/salience consumers on behaviour (wiring real; inputs near-constant; magnitude not measured).
- Whether any process other than `run.py` loads `memory_bridge` at the same time in normal operation.

---

## 20. Recommended future investigations

1. Scratch-instance positive test of `dream_cycle` reachability (copy of `memory/`, isolated).
2. Offline replay of `council_deliberations.jsonl` to measure how much the selection is decided by score vs boosts/exploration, and per-councillor synthesis survival.
3. Reproduce the multi-process `VectorMemory` lost-update on a **copy** of `memory/` (never production).
4. Corruption drill on a copy: truncated pickle, corrupt meta, unreadable FAISS — confirm the predicted behaviours in §15.
5. Longer-window autonomy census (7–30 days) of interaction sources and RiverBrain training composition.
6. Echo Studio client audit for other missing wires (ratings, dissent/alert surfaces).
7. Sibling-instance (Air) differential audit.
8. A "consumer contract" audit: for every thread, name the artifact, the consumer, and the observable behavioural change.
9. Measure the sensitivity of behaviour to valence/salience by counterfactual replay (no live change).

---

## 21. Integrity record

```
Git HEAD (before):     2fba42644c82b9f7096276f4dd338d615cf1bcce
Working tree (before): 181 paths
Git HEAD (after):      2fba42644c82b9f7096276f4dd338d615cf1bcce (unchanged)
Working tree (after):  183 paths = the 181 before + exactly these two new audit files
Files created by this audit: audits/2026-09-20_feralecho_architectural_integrity_audit.md
                             audits/2026-09-20_feralecho_architecture_evidence_ledger.json
Production code/config/state/model state modified: NO
Protocol files (v1.0/v1.1) opened or modified: NO
Persistent-competence experiment infrastructure created: NO
Server restarted: NO. Destructive tests: NONE. Read-only HTTP GETs only.
```

---

## Final question

**"If FeralEcho received no new models, no additional API budget, and no new external services, what existing capability is currently being wasted the most — and what architectural defect prevents FeralEcho from using it?"**

**Answer (my best-supported judgement, with its limits stated).** The most wasted existing capability is its **autonomous local-inference budget and the verification machinery that surrounds it**. About 97% of the interactions FeralEcho logged in the sampled day were its own autonomous work (F-04); its largest single autonomous consumer, the self-edit loop, produced 1,086 attempts in 13 days of which 14 deployed (F-23), and the deployed file has no caller (F-24); the dream cycle never runs (F-10); the autonomous-project loop's reports are read by no one (F-44); the seam, dissent, provenance and sense signals end in logs (F-19–F-21, F-30). Meanwhile the only thing these loops reliably *feed* is RiverBrain's selection table, scored by a single heuristic that cannot see whether code works (F-08) — even though FeralEcho already owns tested ways to see more: sandbox-execution checks (F-28), human ratings that work from the terminal (F-26), peer-council ratings (F-27), and per-councillor raw candidates it already logs in full (F-22).

**The architectural defect:** loops are engineered to be *safe to run* (throttles, stillness, F1/F2/F3, canary-tested liveness checks) but nothing requires — or checks — that a loop's output has a **consumer with an observable behavioural effect**, and the one universal feedback channel is **self-scored** by one heuristic. So compute is spent producing artifacts and telemetry inside a closed loop, and independent ground truth that already exists cannot reach it in bulk. This is my inference from the traced wiring (SUPPORTED, not measured as a counterfactual): I did not test what would happen if a consumer contract were enforced.
