# FeralEcho Runtime Identity and State Preservation Investigation

**Date:** 2026-09-20
**Mode:** read-only with respect to production. The persistent-competence protocol lineage (v1.0/v1.1, tasks, carriers, infrastructure) was not opened, critiqued, extended, or used; nothing here generates or anticipates its outcomes.
**Companions:** `audits/2026-09-20_feralecho_runtime_identity_manifest.json` (per-file identity/evidence records, fingerprints), `audits/2026-09-20_feralecho_state_preservation_evidence.json` (fixture results, production observations, exposure model).

**Evidence labels.** Every finding carries one of:
- **SOURCE-VERIFIED** — read directly in current source.
- **FIXTURE-REPRODUCED** — reproduced with the *real production code* in an isolated temporary fixture. A fixture proves a mechanism *can* occur, not that it *has* occurred in production.
- **PRODUCTION-OBSERVED** — seen in production runtime state, logs, or endpoints.
- **INFERRED** — modelled from measured inputs under stated assumptions.
- **UNKNOWN / ABSENT** — as stated.

**Fixture isolation (stop-condition compliance).** All fixtures ran under a macOS `sandbox-exec` profile (`deny default`; file writes allowed **only** inside the fixture directory; network denied). The jail was validated first: a write outside the fixture directory raised `PermissionError` and created nothing. Real classes were pointed at fixture-only paths; production write access was kernel-denied, so no test could touch production state, acquire a production lock, or trigger a production autosave. One fixture (the PID-gate semantics test) needed `kill(pid, 0)` and used a jail variant that permits the null signal; its first run under the stricter jail returned artefactual results (every "is the process alive?" check failed), which I detected and discarded before re-running. Fixtures were deleted afterward (318 MB). Read-only `git status`/`git diff` may opportunistically refresh the index's stat cache; the staging area was verified empty (`git diff --cached --quiet`) and no commit, stash, or ref was touched.

---

## 0. Git and working-tree state

```
Git HEAD (before): 2fba42644c82b9f7096276f4dd338d615cf1bcce   (committed 2026-09-13 22:27 -0700)
Working tree (before): 183 changed/untracked paths (27 tracked-modified, 156 untracked)
Git HEAD (after):  see §20
```

---

## 1. Executive verdict

1. **What is running.** PID 29288 (`python -u run.py`, conda env `feral_echo`, Python 3.12.13, cwd = repo root), started 2026-09-20 07:30:10 local by the `start_echo.sh` watchdog (PID 2136). It executes the **uncommitted working tree**: HEAD `2fba426` plus 27 tracked-modified files (17 under `app/ run.py sandbox/ scripts/`, ~1,697 inserted lines). **PRODUCTION-OBSERVED** proof that the process loaded working-tree bytes: the live liveness endpoint returns checks (`restore_council_gate`, `task_type_map_sync`) that exist only in the uncommitted `liveness_ledger.py`. **PRODUCTION-OBSERVED** proof that a *previous* process ran stale bytes: shadow-model code removed from source on 2026-09-13 08:49 was still executing on 2026-09-19 (log lines through 10:14) — the process lagged its own source by ≥ 6 days.
2. **State is protected by less than it appears.** `memory/` and `data/` are entirely git-ignored (0 tracked state files). Time Machine has no destination; iCloud Desktop sync is off; there is no external volume; the local `main` is 17 commits ahead of `origin/main` (last push 2026-09-05), so even authored work from the last 15 days exists **only on this SSD**. The only extra copies of state are same-disk snapshots: 5 `river_brain.pkl` copies spanning ~20 hours, two 89 MB `memory_meta` backups from 2026-09-02, and a few older manual copies.
3. **The FAISS/metadata pair is better protected than I previously implied — and more fragile in one specific way.** Each file is written by tmp+`os.replace` (atomic per file), and production is currently consistent (130,837 = 130,837, zero mismatch/persist errors in the current log window). But the two files are replaced separately, and **FIXTURE-REPRODUCED:** a hard abort between the replaces leaves meta = N+1, index = N, and the *next* add then **permanently misaligns vectors and texts** (a query returns the wrong memory's text); nothing in the running system repairs it. Measured at production scale the exposure window is ~18 ms per ~0.63 s persist.
4. **Whole-file non-atomic rewrites are the sharpest silent-loss pattern.** **FIXTURE-REPRODUCED:** `RiverBrain._do_save` truncates the live pickle (`open(..., "wb")`) before dumping; a hard abort mid-write destroys the previous valid state, `load()` then returns a *fresh* brain, and the next save overwrites the wreckage — with only a WARNING logged. The **question garden** (`data/question_garden.jsonl`, 16,228 entries) is rewritten in full by `open(..., "w")` with no lock and no fallback: an abort mid-rewrite silently leaves a shorter, perfectly loadable file (5,000 of 16,228 survived in the fixture) and nothing notices. There is no backup of the garden at all.
5. **The exposure is real, not theoretical, because hard aborts are frequent.** Two Metal-exception `abort()`s occurred in the current ~25-hour watchdog window (2026-09-19 19:31Z and 2026-09-20 14:30Z; exit code 134). Modelled from measured windows (INFERRED, assumptions stated in §16), the expected number of torn writes per year at the observed abort rate is on the order of **0.1–1 per artifact class**, i.e. a non-trivial probability that at least one of these mechanisms fires within a year.
6. **Correction to my previous audit (F-34).** `terminal_client.save_memory()` is gated by `conversation_service.server_is_running()`; I reported the terminal's stale-write hazard without that gate. The hazard is **conditional and narrower**: it requires the terminal to write while the server is *not* running, after having loaded state while the server *was* running. See §9.

**Bottom line.** Runtime identity is answerable and now has a reproducible manifest. Continuity state is *not* currently recoverable from any off-disk copy, and three write paths (RiverBrain pickle, task-type-classifier pickle, question garden) can be silently truncated by the abort rate the machine is already experiencing. The cheapest high-value protections are boring: atomic write helper, refuse-to-overwrite after a failed load, and a checksummed generational off-disk copy of a ~0.6 GB minimal set.

---

## 2. Repository HEAD vs working tree vs running-process identity

| Layer | Identity | Label |
|---|---|---|
| **Repository HEAD** | `2fba42644c82b9f7096276f4dd338d615cf1bcce`, tree `af580de5…`, 2026-09-13 22:27 -0700; `origin/main` = `d6cd738` (2026-09-05); local `main` ahead 17 | SOURCE-VERIFIED (local refs; remote not contacted) |
| **Working tree** | 27 tracked files differ from HEAD (17 executable-scope); 156 untracked non-ignored paths (mostly `audits/`, `research/`, `hub/`, `app/experiments/`, 7 `scripts/*`); `.env` present but ignored (mtime 2026-07-12) | SOURCE-VERIFIED |
| **Running process** | PID 29288; parent `/bin/zsh start_echo.sh` (PID 2136, started 2026-09-19 11:00:21 local); `python -u run.py`; interpreter `~/miniforge3/envs/feral_echo/bin/python3.12`; cwd `/Users/richietate/Desktop/FeralEcho`; started 2026-09-20 07:30:10 local; sentinel `stage: serving`, uptime ~4.4 h at capture | PRODUCTION-OBSERVED |
| Import path | `python run.py` puts the script directory (repo root) first on `sys.path`; **no `PYTHONPATH` in the process environment** | INFERRED from OBSERVED env names |
| Environment-derived config | Process env names: conda vars, `ECHO_DONT_KILL_ME_DADDY`, `FLASK_ENV`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_NUM_PARALLEL`, `TOKENIZERS_PARALLELISM`, `SSH_AUTH_SOCK`, macOS session vars. `.env` (7 names, values not recorded here) supplies `OLLAMA_MODEL`, `OLLAMA_URL`, API keys, two shared secrets; only its SHA-256 and name list are in the manifest | OBSERVED |
| Co-resident process | `python -m echo_studio.main` (PID 34531, since 10:35) — the GUI; separate process, HTTP client | OBSERVED |
| Ollama | 9 models, 35.3 GB; `echo:latest` 4.66 GB, digest prefix `8cbcbe23800bfe9c`, created 2026-07-01 from `FROM llama3:instruct` (tracked Modelfile) | OBSERVED |

**Which working-tree changes could the process have loaded?** Every modified executable-scope file has an mtime *before* the process start (only generated `sandbox/scripts/temp_self_edit.py`, 11:53, postdates it). Therefore for any module that was imported at process start, the loaded bytes equal the current bytes. Static import analysis (module-level vs function-level imports, closed transitively from `run.py`) classifies 234 candidate files: 55 `SUPPORTED_LOADED*` (eager import path + mtime precedes start), 41 `POSSIBLE*` (lazy path only), 137 `NOT_EVIDENCED` (no static import path — scripts, experiments, data, configs), and exactly **1 `PRODUCTION_OBSERVED_LOADED_AT_CURRENT_BYTES`** (`liveness_ledger.py`). "Present in the working tree" is **never** converted into "executed by the process" in the manifest; loading is reported at the strongest class the evidence supports. No file is claimed as executed on the basis of existence.

**Limits.** I did not attach to the process (no ptrace/py-spy) and there is no runtime module registry, so "actually loaded" is provable only where an observable effect exists. Import-failure fallbacks (`try/except` stubs) mean an eager static import path is strong-but-not-conclusive evidence.

---

## 3. Uncommitted-change archaeology

Provenance is dated from file mtimes, in-file comments that cite audit documents and `PENDING_DECISIONS.md` items, HEAD's commit history (e.g. `1081f26 sandbox: enforce noninteractive stdin contract`), and the existing audit corpus. Where a file's origin is not evidenced I say so.

| File (Δ lines) | mtime (local) | Content | Class | Materially affects |
|---|---|---|---|---|
| `app/core/shadow_model.py` (+35) | 09-13 08:49 | Retirement notice; implementation unchanged | intentional (retirement), documentation | none at runtime (module already unimported) |
| `app/emergent_scheduler.py` (+14/−6) | 09-13 08:49 | Removes `propose_from_reflection` call | intentional | autonomy (stops shadow proposals) |
| `app/maintenance/night_cycle.py` (+24/−12) | 09-13 08:49 | Removes shadow accuracy check | intentional | autonomy/observability |
| `app/core/self_edit_manager.py` (+34/−16) | 09-13 08:49 | Removes shadow-model fallback in target selection | intentional | **self-editing** (target choice now empirical-only, default `coding`) |
| `app/core/provenance_check.py` (+372) | 09-13 07:25 | `reconcile_process_and_selfreport()` (provenance leaf 3) | intentional feature work; **no live importer** | provenance only (unwired) |
| `scripts/verify_provenance_check.py` (+373) | 09-13 07:33 | Verification for the above | audit support | none |
| `app/core/liveness_ledger.py` (+275) | 09-17 12:07 | New checks `restore_council_gate`, `task_type_map_sync`; extended f2-stdin check | instrumentation | **recovery/safety observability** (production-observed loaded) |
| `scripts/verify_liveness_ledger.py` (+125) | 09-17 12:07 | Discrimination cases | audit support | none |
| `app/core/snapshot_manager.py` (+144) | 09-09 15:55 | Council review + dissent logging for restore | intentional (Standing Principle gap) | **recovery**, safety |
| `run.py` (+59) | 09-09 15:55 | `/admin/restore` wired to the council review (`override_council_concern`) | intentional | **recovery**, human-approval path |
| `app/core/river_deliberation.py` (+102/−10) | 09-09 15:49 | `select_best_fallback_candidate` three-stage rule (Tier-6 forensic result) | bug fix / evidence-driven | **model selection/synthesis** (fallback branch only) |
| `app/core/temporal_environment.py` (+100) | 09-09 15:53 | Splits MacBook vs phone location; `ip-api.com`; staleness flag | intentional (PENDING_DECISIONS #23) | prompt context |
| `app/core/echo_ground_truth.py` (+36) | 09-08 00:52 | See/hear conjunction gate | bug fix | prompt grounding |
| `sandbox/safe_exec_wrapper.py` (+42) | 09-09 12:24 | Closes fd 0 in the sandbox | safety hardening (follow-on to committed `1081f26`) | **safety/code execution** |
| `app/core/self_edit_generated.py` (+66/−…) | 09-20 04:09 | Self-edit's own deployed output | **generated** | none (no live caller — prior audit F-24) |
| `app/core/self_edit_convergence.json` | 09-20 11:31 | Convergence counters | **generated state** | self-edit prompting |
| `sandbox/scripts/temp_self_edit.py`, `staging/self_edit_candidate.py` | 09-20 | Autonomous scratch/candidate files | **generated** | none |

Non-executable tracked modifications: `CLAUDE.md`, `PENDING_DECISIONS.md`, `research/OPEN_QUESTIONS.md`, one audit doc, `claude_relay/{README.md,from_m5.md,relay.py,.last_seen_from_air.json}` (**`relay.py` is modified and mtime-precedes the process but has no import path from `run.py`; unknown provenance — not evidenced by this pass**), `logs/janitor_report.json` (generated).

**Untracked source capable of affecting runtime:** none *reachable* from `run.py`. `app/experiments/e5_mini/`, `app/experiments/task_type_ground_truth/` and 7 `scripts/*` have no import path from the server; `.claude/skills/*` are tooling. Ignored config that *does* affect runtime: `.env`, `.echo_project_learner/`, `app/core/memory/` (a stray state dir from a past cwd), `MyPythonProject/`, `PythonAnalysis/`, `NewBeginning/` (scaffold sprawl, inert).

**Concise change map (behaviour-relevant, uncommitted):** shadow-model retirement (autonomy, self-edit targeting); restore council gate (recovery, human approval); synthesis fallback rule (selection); fd-0 closure (sandbox safety); location split (prompt context); liveness checks (observability); provenance leaf 3 (unwired). **No uncommitted change touches persistence code** (RiverBrain, VectorMemory, garden, snapshots' artifact list are all identical to HEAD except `snapshot_manager.py`'s restore-review addition). None was staged, reverted, cleaned, or committed.

---

## 4. Runtime source manifest

`audits/2026-09-20_feralecho_runtime_identity_manifest.json` (234 files). Per file: path; tracked/untracked; `differs_from_HEAD`; Git blob at HEAD and in the working tree; SHA-256 of current bytes; size; mtime; `mtime_after_process_start`; diffstat; static import reachability from `run.py` (eager / lazy / none); `.pyc` cross-check; log-string probes for modified files; and a **`runtime_load_evidence`** class (never above what evidence supports).

**Aggregate fingerprints (deterministic; recomputed within the script and across two consecutive runs).**

| Fingerprint | Value (prefix) | Scope |
|---|---|---|
| `authored_source_sha256_excluding_self_mutating_files` | `8e6808dc64fbebe5…` | 513-file runtime-candidate set minus the four self-mutating files — the **stable identity of the authored source** |
| `runtime_candidate_source_sha256` | `0330734c876035aa…` | same set including self-edit output/state (drifts with self-edit activity) |
| `live_scope_py_sha256` | `6ecee9f04a5a7660…` | 187 live-scope `.py` files |
| `tracked_diff_vs_HEAD_sha256` | `32a09b13aec83e29…` | `git diff HEAD` over `app run.py sandbox scripts echo_studio terminal_client.py echo_quality_scorer.py` (**not stable**: includes generated self-edit files — it changed between two runs minutes apart) |
| self-mutating files | `self_edit_generated.py`, `self_edit_convergence.json`, `sandbox/scripts/temp_self_edit.py`, `staging/self_edit_candidate.py` | reported individually so they cannot destabilize the authored fingerprint |

**Answer to "can a deterministic aggregate fingerprint identify the working-tree source state?"** Yes, with two conditions: (a) the file set must be defined (here: `git ls-files -co --exclude-standard`, restricted to source/config suffixes, excluding audit/relay/state directories), and (b) self-mutating files must be separated. Nothing was committed.

---

## 5. Persistent-state inventory

Columns compressed; full per-file facts (size, age) are in the evidence file. **Class:** IRR = irreplaceable, EXP = expensive to recreate, REB = rebuildable, EPH = ephemeral. "Atomic" means tmp-file + `os.replace` (no `fsync` was found in any writer: **SOURCE-VERIFIED absent**). "Lock" is cooperative and **process-local unless stated**.

| Artifact (format, size) | Writers → readers | Freq / method | Atomic | Lock | Backup | Validation → corruption handling → empty fallback | Rebuild | Class |
|---|---|---|---|---|---|---|---|---|
| `memory/river_brain.pkl` (pickle, 4.4 MB) | `RiverBrain._do_save` (server writer thread; any process calling `get_river_brain()` incl. `terminal_client`, `river_creative_rehab.py`) → `RiverBrain.load` (startup), snapshot copy | ~80 saves/h (PRODUCTION-OBSERVED); ≤60 s idle + ≥5 s throttle; `open("wb")`+`pickle.dump` | **NO** | `fcntl.flock` on `.lock` (cross-process, cooperative) | ≤5 snapshots/≈20 h; older manual `.pre_*` copies | none (no checksum) → WARNING + fresh brain; "richer-than-disk" guard bypassed when disk copy unreadable → **fresh state overwrites** | relearn from autonomous stream (~1.2k obs/day; 210k obs) | **EXP** |
| `memory/memory_meta.json` (JSON, 101 MB) | `VectorMemory._persist` (server via `memory_bridge` singleton; gated `terminal_client`; disconnected `self_heal`; manual `memory_migration`) → load at startup, search | ~26 persists/h; tmp+replace, **meta first** | per-file yes | `memory_lock` (intra-process only) | 2 dated pre-migration copies (2026-09-02, 122.4k/122.5k of ~130.8k entries); Jul-5 copy stale (11k) — **same disk** | none → parse failure ⇒ `{}` + WARNING; next `add` persists over the file | not rebuildable (texts are the data) | **IRR** |
| `memory/faiss.index` (FAISS, 201 MB) | same → same | same; written second | per-file yes | as above | none | count vs meta at load: WARNING only; read failure ⇒ **empty index persisted at construction** | re-embed all meta texts (time UNMEASURED — plausibly tens of minutes to hours; needs SentenceTransformer; no wired, tested tool) | **REB** (cost UNMEASURED) |
| `data/question_garden.jsonl` (JSONL, 10.6 MB, 16,228 entries) | `garden_manager._save_garden` (full rewrite) / `_save_entry` (append) from ≥6 modules → scheduler, ground-truth, salience | ≥ every emergent cycle (~5 min); frequency UNKNOWN | **NO** | **none** | **none** | per-line `json.loads` skip → silent shorter garden | partially regenerable (curiosity engine ~247/wk); lineage/quality not | **EXP** |
| `memory/self_model_claims.jsonl` (8.9 KB) | `record_claim` → verification/ground-truth | per claim; append | append | `threading.Lock` | none | line-level | none | **IRR** (small) |
| `memory/task_type_classifier.pkl` (50 KB) | `TaskTypeClassifier._write_if_richer` → load | on learn; `open("wb")` | **NO** | `flock` + richer-guard | none | as RiverBrain | `bootstrap_from_log` (UNTESTED) | REB |
| `memory/drift_detectors.pkl` (1 KB) | `introspection_channel._save_drift_detectors` | 120 s; tmp+replace | yes | none | none | none | re-accumulate (5k obs/type) | REB |
| `memory/council_ratings.jsonl` (119 KB) | rater append; `fill_spot_check` atomic rewrite under lock | 90 s poll | rewrite yes | `_council_log_lock` | none | line-level | human labels not regenerable | **IRR** (small) |
| `memory/snapshot_baseline.json` (1 KB) | `patch_baseline_meta` | rare; tmp+replace under lock | yes | `_baseline_meta_lock` | in snapshots? no | none | trust decisions (human) | IRR (decisions) |
| `memory/self_model.json` (19 KB) | `SelfModelUpdater._write` | 130 s; tmp+replace | yes | none | weekly copies in `memory/history/` | none | rebuilt each cycle | REB |
| `memory/echo_state.npy`, `echo_state_history.npy` | `np.save` direct | 120 s | **NO** | none | daily archives (30 gens) | none | REB | EPH |
| `memory/interaction_log.jsonl` (19 MB) | `log_interaction` append → many | per interaction | append | none observed | single-generation `.1.gz` (12 MB), overwritten on rotation | line-level | none | **IRR/EXP** |
| `memory/reflection_shard.jsonl` (38 MB; **written by `save_reflection`, not by the ReflectionShard class**) | append → `rank_models` legacy score | per interaction | append | none | `.1.gz` | line-level | none | EXP |
| `memory/reflection_journal.jsonl` (13 MB) | `ReflectionShard` | 300 s×35% | append | own | rotation | line-level | none | EXP |
| `memory/SELF_EDIT.log` (28 MB) + attempt ledger (1.8 MB) | self-edit loop → convergence backfill (full replay) | per attempt | append | none | none | — | convergence rebuildable from it | EXP |
| `memory/echo_messages.jsonl` (2.9 MB), `sync_*`, `chat_thread_pacing.json` | messaging/sync | varies | mixed (`sync_state.json` direct `w`) | partial | none | — | UNKNOWN (Air may hold peers) | UNKNOWN |
| touch/vision/hearing `*_signature.json` | sense modules | per report | tmp+replace (pid/thread-suffixed) | lock | none | — | physical-world accumulation | EXP (small) |
| `memory/echo_sentinel.json`, `echo_server.pid` | `run.py` | startup/heartbeat | sentinel atomic; pid plain | — | — | stale after `kill -9` | — | EPH |
| `memory/optuna.db` (SQLite, 9.7 MB) | Optuna | per trial | SQLite | SQLite | none | SQLite | search history | REB |
| `memory/dream_state.json`, `prompt_history_state.json`, `autonomous_loop_momentum.json`, `seam_state.json`, `salience_state.json`, `mlx_crash_avoidance.json` | respective modules | periodic | mostly tmp+replace (`dream_state.json` direct) | mixed | none | — | derived | REB/EPH |
| `memory/behavioral_directives.json` (empty) | `behavioral_state` | human-confirmed | tmp+replace + backup dir | — | 1 backup | — | would be IRR once populated | (empty) |
| `memory/snapshots/*` (40 files) | `snapshot_manager` | startup + post-self-edit | `shutil.copy2` + sha256 of the copy | none | self | sha256 recorded; **no loadability check** | — | derived |
| `echo_principles.json`, `Modelfile`, `COUNCIL.md`, `ORIGIN.md`, `bible_sentiment.json`, `app/persona.json` | human | rare | — | — | **git-tracked**, origin/main | genesis/council hashes checked at startup (alert-only) | git | recoverable to origin state |
| `memory/genesis/*.txt` | startup | — | — | — | in snapshots (git-ignored) | — | re-anchoring is a human decision | REB* |
| Ollama models (35 GB) | `ollama pull/create` | — | — | — | registry (needs network) | — | `echo:latest` from Modelfile + `llama3:instruct` | REB |
| `.env` | human | — | — | — | **none** | — | API keys re-issuable; `GREMLIN_SECRET`/`ECHO_PARTNER_SECRET` must match the peer | IRR-ish |
| uncommitted working tree + 17 unpushed commits | human/Claude | — | — | — | **none off this disk** | — | — | **IRR** (authored work) |

---

## 6. Write-authority map (artifact → all known writers → mode → coordination)

| Artifact | Known writers | Mode | Coordination / gap |
|---|---|---|---|
| `river_brain.pkl` | server writer thread; `terminal_client` (calls `echo_query`→`get_river_brain().save()` in-process); `river_creative_rehab.py` (CLI, flushes production RiverBrain); scripts that call `get_river_brain()`; snapshot **restore** (human) | full overwrite | `fcntl` lock + guard comparing **only total observation count** — **FIXTURE-REPRODUCED:** a higher-count stale writer replaces another writer's `model_task_stats` increments |
| `task_type_classifier.pkl` | server; `terminal_client` (imports orchestrator) | full overwrite | same pattern |
| `faiss.index`+`memory_meta.json` | server (`add_to_vector_memory`, `log_dream_bridge` incl. sync import, consolidation, `/memory/conversation`); `terminal_client` local `VectorMemory` (**gated**); `self_heal.repair_vector_memory_index` (no callers); `memory_migration` (manual) | full rewrite per add | intra-process `memory_lock` only; **no cross-process lock, no version/generation check** |
| `question_garden.jsonl` | `emergent_loop`, `seam_engine`, dream, `curiosity_engine`, `echo_projects`, `echo_messaging` (multi-thread, one process) | full rewrite + append | **none** — **FIXTURE-REPRODUCED** lost-update: an entry appended between another thread's load and rewrite vanishes |
| `self_model_claims.jsonl` | chat path | append | `threading.Lock` |
| `council_ratings.jsonl` | rater thread; `spot_check.py` (CLI) | append / atomic rewrite | `_council_log_lock` (process-local; `spot_check.py` is a second process — UNKNOWN interplay) |
| `interaction_log.jsonl`, `reflection_shard.jsonl` | server, `terminal_client`, scripts | append | none needed for append (partial last line possible) |
| snapshot dirs | `take_snapshot` (startup thread, post-self-edit) | copy | no lock vs. the RiverBrain writer |

**Multi-writer state with no concurrency/version protection:** FAISS/meta (cross-process), question garden (in-process too), RiverBrain `model_task_stats` (count-only guard), classifier pickle. Ad-hoc code pointing at production paths: `river_creative_rehab.py` (intended production writer), `verify_riverbrain.py` (read-only by its own claim), `sandbox/experiments/test_faiss_atomicity.py` (not inspected), several `scripts/*` and `app/experiments/*` reference production paths (their isolation was not audited here). Bare `VectorMemory()` defaults are cwd-relative production paths (`"memory/faiss.index"`, `"memory/memory_meta.json"`); `RIVER_BRAIN_PATH = "memory/river_brain.pkl"` is also cwd-relative (**SOURCE-VERIFIED**; my earlier audit assumed absolute).

---

## 7. RiverBrain hazard analysis

| Question | Answer | Label |
|---|---|---|
| How does it write? | `with open(RIVER_BRAIN_PATH,"wb") as f: pickle.dump(snapshot, f)` inside an `fcntl.LOCK_EX` on `.lock`; before that it unpickles the existing file for the guard | SOURCE-VERIFIED |
| Atomic? fsync/rename? | **No / neither.** The open truncates the live file first | SOURCE-VERIFIED |
| Locking | `fcntl.flock` cross-process, cooperative; load takes `LOCK_SH` | SOURCE-VERIFIED |
| Autosave timing | queue `save()` (rate-limited ≥5 s) + every 60 s idle; ~80 saves/hour observed; unchanged pickles are rewritten (identical `total_obs` logged consecutively) | PRODUCTION-OBSERVED |
| Shutdown | `shutdown_handler`: unlink PID, no-op `kill_wolf_gracefully`, `sys.exit(0)`. **`RiverBrain.shutdown()` has zero callers; no `atexit`**; writer is a daemon thread | SOURCE-VERIFIED |
| Corrupt-load | WARNING `Brain load failed: … — starting fresh`; returns fresh brain | SOURCE-VERIFIED + FIXTURE-REPRODUCED |
| Can a fresh fallback later overwrite the original? | **Yes.** The richer-than-disk guard runs `pickle.load(existing)` inside `try/except: pass`; when the file is unreadable the guard is skipped and the fresh instance's next save overwrites it | FIXTURE-REPRODUCED |
| Does an abort mid-write destroy the *previous valid* state? | **Yes** — the truncation happens at `open("wb")`, before any bytes of the new state are written | FIXTURE-REPRODUCED |

**Fixture results (real `RiverBrain` class source extracted by AST; synthetic state; jailed).**
- S1 round-trip valid → OK. S2 guard on a *valid* file works (lower-obs writer refused; file unchanged).
- **S3 torn write:** child died inside `pickle.dump` (exit 134). File 196 of 392 bytes; `pickle.load` → `UnpicklingError`; `RiverBrain.load()` → **obs 0** (fresh); one later save wrote obs = 1. Original 13,500-obs state existed only in an external copy.
- **S4 variants:** zero-length, 90 % truncation, random garbage → all load as fresh and are **overwritten by the next save**. A single mantissa bit-flip in a stored float **loads successfully with a silently altered value** (0.61 → 0.6099999999999999) — there is no integrity check at all.
- **S5:** a pickle missing `accuracy_trackers` raises *after* classifiers/scalers/observation counts were merged: the log says "starting fresh" but observation counts (777) are loaded while `model_task_stats` is empty — a partial-state hazard for format drift.
- **S6 two-instance lost update:** disk 155 obs; a stale instance at 153 is refused; at 163 it overwrites, and the other writer's `model_task_stats` increments are lost (count 100 instead of 105).
- **S7 window:** 3.8 MB pickle saves in a median 7.6 ms (synthetic floats; real HoeffdingTree serialization may be slower — treated as a range in §16).

**Hazard grades.** Torn write destroys previous state: **FIXTURE-REPRODUCED**. Corrupt → fresh → overwrite: **FIXTURE-REPRODUCED**. That it *has* happened in production: **no evidence** (current log window: 0 load/save failures; obs monotone). SIGTERM path: **SOURCE-PROVEN** exposure (daemon writer killed at exit), not exercised. Power-loss/OS-crash durability (no `fsync`): **THEORETICAL** (APFS reduces but does not remove it).

---

## 8. VectorMemory / FAISS hazard analysis

**Lifecycle (SOURCE-VERIFIED).** `VectorMemory.__init__` → `_load_metadata()` (parse failure ⇒ `meta = {}`) → `_load_or_rebuild_index()` (read failure ⇒ new empty `IndexFlatIP` **and immediate `_persist()`**; count mismatch ⇒ WARNING only) → `add()` mutates memory then `_persist()`: meta tmp+replace **first**, index tmp+replace **second**. `id_order` = `list(meta.keys())` at load; FAISS position *i* ↔ `id_order[i]` by convention only. No generation ID, no ID cross-check, no versioning, no cross-process lock. A single `add` costs ~0.65 s at production scale (full 114 MB JSON + 201 MB index rewrite, plus an O(N) `id not in id_order` scan).

**Fixtures (real `VectorMemory`, dim 16, jailed).**

| ID | Sequence | Result |
|---|---|---|
| **V2** | valid → meta truncated → construct → add one | constructor writes nothing; the add rewrites meta with **1 entry** (originals gone from disk); querying an original embedding returns **the wrong text** (`text-of-Q`) |
| **V3** | valid → index truncated → **construct only** | **constructor alone overwrote the index with an empty one** (ntotal 0, new SHA); meta intact. One later add: vector at position 0 but `id_order[0]` is the *oldest* memory → querying the new item returns **an unrelated memory's text** |
| **V4** | valid → meta deleted → add | same misalignment; the new item is unsearchable |
| **V5a** | child killed between meta replace and index write | meta 4 / index 3, no tmp file; load warns; **next add: querying Z returns Y's text** — misalignment persists |
| **V5b** | child killed after index tmp written, before rename | meta 4 / index 3, a *complete* `faiss.index.tmp` left on disk that recovery ignores; same misalignment |

**Production-scale window (fixture, synthetic 130,838×384):** persist ≈ 0.63 s, of which the *mismatch window* (meta replaced, index not yet) ≈ **18 ms** (page-cache writes; real-disk pressure UNMEASURED). Production persists ≈ 26/h. Current production state: counts equal (130,837 = 130,837), zero divergence/persist-failure log lines (PRODUCTION-OBSERVED). Detection if it occurred: a WARNING on load and an `introspection_channel` "FAISS/meta divergence" WARNING every 120 s — **no alert path, no self-heal** (`self_heal.py` is disconnected).

**Classification.** Interrupted-persist misalignment — FIXTURE-REPRODUCED; empty-index-on-unreadable-index — FIXTURE-REPRODUCED and SOURCE-VERIFIED; occurrence in production — none observed. Importantly the **texts survive** in the misalignment cases (meta is intact and authoritative), so the damage is *retrieval corruption*, recoverable by re-embedding — but only if noticed and only with tooling that is not wired.

---

## 9. `terminal_client` stale-write investigation (priority question)

**End-to-end trace (SOURCE-VERIFIED).**
1. **Independent `VectorMemory`?** Yes. Module-level `vm = VectorMemory(index_path="memory/faiss.index", meta_path="memory/memory_meta.json", dim=…)` at import (cwd-relative paths).
2. **Loads production persistence?** Yes when cwd = repo root (the normal case).
3. **Server and client diverge?** Yes: the server keeps adding (~26 persists/h); the terminal's copy is frozen at its startup.
4. **Can the client save its older full copy?** Only via `save_memory()`, which begins with `if conversation_service.server_is_running(): return`. `server_is_running()` = PID file exists and `os.kill(pid, 0)` succeeds. So the ungated path executes only when the gate returns False.
5. **Overwrite newer server additions?** If the gate returns False **and** the server had added memories since the terminal started, yes (mechanism below).

**Gate semantics (fixture; real function extracted).** Live same-user PID → True (write skipped). Dead PID (stale after `kill -9`), missing file, garbage → False. **PID reused by a process the user cannot signal (tested with PID 1)** → `EPERM` → **False (unsafe direction)**. Default path is cwd-relative: from another directory the gate returns False — but then the terminal's `vm` also points at a *different* `memory/` (not production), so production is unaffected. Also, the terminal process imports the orchestrator: it constructs its own RiverBrain and classifier singletons and calls `save()`; those writes are guarded only by the richer-count guard (§7).

**Exact sequence reproduced (jailed; hashes/counts at every stage).**

| Stage | Disk meta / index | Notes |
|---|---|---|
| T0 A persisted S1..S3; B loaded | 3 / 3, meta `d420…`, index `ed48…` | identical |
| T1 A (server) adds & persists X | 4 / 4 | X on disk |
| T2 B stale in memory | B holds 3 / 3 | |
| **T3 B persists Y** | 4 / 4, keys S1,S2,S3,**Y** | **X is gone from disk** |
| T4a fresh process loads disk | X absent, Y present | X permanently lost if the server died before persisting again |
| T4b (branch) server, still alive, adds Z | 5 / 5 keys S1,S2,S3,X,Z | X restored, **Y (the terminal's) lost** |

**Verdict.** The mechanism is real and **FIXTURE-REPRODUCED**, and the gate is **SOURCE-VERIFIED**. In production the loss window requires: terminal started while the server was up → server keeps persisting → server not running at the moment a terminal message is saved (restart window ~10 s after each SIGABRT, or a stopped server) → terminal writes. The terminal is a secondary interface and is not running now. **Production occurrence: UNKNOWN (no terminal process observed; not detectable after the fact).** Realistic consequence when it does happen: the server's in-memory copy re-asserts itself at its next persist unless the server also dies; the terminal's own memories are silently lost either way. This is a **narrow, conditional** hazard — materially lower than the unconditional stale-write I described in the previous audit.

---

## 10. Corruption → fallback → overwrite experiments

| Artifact | Corruption | Load result | Destructive persistence path? | Grade |
|---|---|---|---|---|
| RiverBrain pickle | zero-length / truncated / garbage | fresh brain, WARNING | **Yes** — next save overwrites (guard skipped) | FIXTURE-REPRODUCED |
| RiverBrain pickle | 1-bit flip in a float | loads, altered silently | not a fallback issue; **undetected corruption** | FIXTURE-REPRODUCED |
| `memory_meta.json` | truncated | `meta={}` | Yes on the **next add** (meta rewritten with 1 entry; originals lost from disk) | FIXTURE-REPRODUCED |
| `memory_meta.json` | deleted | `meta={}` | Yes on next add | FIXTURE-REPRODUCED |
| `faiss.index` | truncated | empty index | **Yes at construction** (no add needed); meta preserved; then misalignment on the next add | FIXTURE-REPRODUCED |
| Question garden | truncated file | loads shorter | n/a — already destructive; `_load_garden` skips bad lines silently | FIXTURE-REPRODUCED |
| Classifier pickle | corrupt | fresh (same code pattern) | Yes (`_write_if_richer` guard bypass) | SOURCE-VERIFIED (not fixtured) |

A graceful in-memory fallback is not data loss by itself; the destructive step is always the *subsequent save*, which none of these paths prevents.

---

## 11. Partial-write / crash analysis

| Interruption | Old valid state | Result | Distinguishable? |
|---|---|---|---|
| Mid `pickle.dump` (RiverBrain/classifier) | **destroyed** (truncate-first) | truncated file → fresh | Only by a WARNING string; no marker distinguishes *old-valid / partial / corrupt / empty-initial* |
| Mid meta tmp write | intact (tmp orphan) | old pair consistent | yes (atomic) |
| Between meta and index replace | old index intact; meta ahead | N+1 / N mismatch | count comparison **detects**, nothing repairs; next add misaligns |
| Mid index tmp write / before rename | old index intact | orphan `.tmp` (possibly complete) | detectable by count; tmp ignored |
| Mid garden rewrite | **destroyed** (truncate-first) | shorter valid file | **not detectable** |
| Mid JSON state write (`dream_state.json`, `sync_state.json`, `np.save` states) | destroyed | tiny/derived | UNKNOWN handling; low value |
| Mid append (logs) | prior lines intact | partial last line | line-level parsers skip it |
| Before normal shutdown (SIGTERM) | ≤ ~65 s of RiverBrain increments unsaved | small loss | no |
| Power loss / OS crash | (no `fsync`) any of the above, plus zero-length-after-rename risk | THEORETICAL on APFS | — |

**Recovery cannot distinguish OLD VALID / PARTIAL NEW / CORRUPT / EMPTY INITIAL for the pickles or the garden**; for the FAISS/meta pair only the *count* is a signal.

---

## 12. Existing backup reality (PRODUCTION-OBSERVED unless noted)

- **Time Machine:** `tmutil destinationinfo` → *No destinations configured*.
- **iCloud Desktop/Documents:** `FXICloudDriveDesktop = 0`; no iCloud Drive directory.
- **External volumes:** none mounted. Single internal SSD (706 GB free of 926 GB).
- **Git:** `memory/`, `data/`, `*.index`, and `.env` are ignored; 0 tracked state files. `origin/main` (local ref) `d6cd738`, 2026-09-05; local `main` ahead 17; plus 27 modified/156 untracked paths. Remote availability and content were **not contacted** (UNKNOWN beyond the local ref).
- **Scripts/schedulers:** `backup_feral_echo.sh` (2025-11-10) is a code-push script that **rewrites `.gitignore` with `cat >`**; it is not scheduled (no crontab; only `com.gremlin.echo.plist` in LaunchAgents) and is not a state backup.
- **Repository-local copies (all same disk):** `memory/snapshots/` — 5 slots, each with sha256-recorded `river_brain.pkl` + 6 small files, **all within ~20.5 h** (2026-09-19T18:01Z–2026-09-20T14:31Z), all verified sha-OK; retention is by count, and the observed restart/self-edit cadence rotates the whole window in about a day. `memory_meta_backup_before_{backfill,reflection}_migration_20260902*.json` (122.5k/122.4k entries vs ~130.8k now); `memory/backups/` (Jul-5 pair, 11k entries; `pre_migration_20260713/`); `river_brain.pkl.pre_*` (Jul–Sep); `memory/history/` (self-model weekly, 30 daily `echo_state`/`salience` archives).
- **M5↔Intel copies:** the M5↔Air sync exchanges interaction-log entries into the peer's memory; it is **not** a backup of `memory/`, and the Air was not inspected (UNKNOWN whether it holds any usable copy). `claude_relay/` is message plumbing.
- **Snapshot content gaps (SOURCE-VERIFIED):** `_ARTIFACTS` = `self_edit_generated.py`, `river_brain.pkl`, `echo_principles.json`, genesis hash, `Modelfile`, `COUNCIL.md`, council hash. **Not snapshotted:** FAISS, meta, garden, claims, classifier, drift detectors, council ratings, baseline.
- **Snapshot hazards:** copies bytes without a loadability check ("bytes-only, no pickle.load"), takes no lock against the RiverBrain writer (torn copy possible; THEORETICAL), and a startup snapshot taken after a torn write would rotate good copies out within ~a day.

**"If this file disappeared right now, what verified recovery path exists?"**

| Artifact | Verified path | Age / loss |
|---|---|---|
| `river_brain.pkl` | latest snapshot (sha256 verified, **not** loadability-tested) | ≤ ~20 h of observations |
| `memory_meta.json` | 2026-09-02 pre-migration copy (same disk) | ~8.3k entries newer than the copy are lost; texts otherwise intact |
| `faiss.index` | none stored; rebuildable from meta by re-embedding (no wired, tested tool: `self_heal.repair_vector_memory_index` is disconnected and UNTESTED) | re-embed time UNMEASURED + code |
| `question_garden.jsonl` | **none** | total |
| `self_model_claims.jsonl`, `council_ratings.jsonl`, `snapshot_baseline.json` | **none** | total |
| `task_type_classifier.pkl` | `bootstrap_from_log` from `interaction_log` (UNTESTED) | partial |
| `drift_detectors.pkl` | none; re-accumulates | time |
| `interaction_log.jsonl` | `.1.gz` (single generation, same disk) | partial |
| `echo_principles.json`, `Modelfile`, `COUNCIL.md`, `ORIGIN.md` | git (local + `origin/main`@Sep 5); snapshots | to last commit |
| Source since 2026-09-05 | **none off this SSD** | 17 commits + uncommitted |
| `.env` | none | API keys re-issuable; shared secrets must match the peer (peer copy UNKNOWN) |
| **If the whole machine died tonight** | Git origin (source ≤ Sep 5, remote unverified), Ollama registry (needs network). **Nothing under `memory/` or `data/` is provably recoverable.** | — |

---

## 13. Zero-cost preservation design (not implemented)

Principles: boring, auditable, no new dependencies, no paid services. Each item: **type · engineering cost · regression risk**. (Files named here include `EDIT_FORBIDDEN_TARGETS` entries; changes are human-directed edits.)

| # | Mechanism | Type | Cost | Risk |
|---|---|---|---|---|
| P1 | Shared `atomic_write` helper: write tmp in the same dir → `flush` → `os.fsync` → `os.replace` → fsync the directory (macOS: `fcntl.F_FULLFSYNC` optional). Apply to RiverBrain pickle, classifier pickle, question-garden rewrite, `np.save` states, `dream_state`/`sync_state` | DATA-LOSS PREVENTION | low | low (removes the truncate-first window; pure write-path change) |
| P2 | **Refuse to overwrite after a failed load**: on unreadable pickle/meta/index, rename the file to `<name>.corrupt-<UTCts>` (never delete), set a `load_failed` flag, disable automatic saves (or save to `<name>.recovered`), and emit one alert | DATA-LOSS PREVENTION + OBSERVABILITY | low | low–med (needs a human ack path) |
| P3 | Previous-known-good: `os.link(path, path + ".prev")` (hard link, zero copy) immediately before each replace; one `.prev` per artifact | RECOVERY | trivial | very low |
| P4 | **Paired generation manifest** `vector_store.manifest.json` written last (atomic): `{generation, meta_count, index_ntotal, meta_bytes, index_bytes}`; verify on load | CORRUPTION DETECTION | low | low |
| P5 | **Alignment guard in `VectorMemory.add`**: refuse (raise + alert) if `index.ntotal != len(id_order)`; **deterministic repair** when meta is ahead: positions `< ntotal` are valid, move trailing ids to a `pending_embed` list and re-embed them (meta is insertion-ordered) | DATA-LOSS/CORRUPTION PREVENTION + RECOVERY | low–med | med — converts silent misalignment into loud failures until repair exists |
| P6 | **Single-writer authority for FAISS/meta:** server only; `terminal_client` never constructs a writable `VectorMemory` (read-only load or HTTP); add a cross-process `fcntl` lock and generation check (reload/merge if disk generation ≠ in-memory) | CONCURRENCY CONTROL | med | med |
| P7 | Checksum sidecars (`<file>.sha256`) written by P1 and verified on load for pickles/claims; for 100–200 MB files verify size/counts at load and full hash nightly | CORRUPTION DETECTION | low | low |
| P8 | **Snapshot policy by time and content**, not restart count: keep ≥ 1/day for 14 days plus hourly for 24 h; verify loadability (subprocess unpickle/`json.load`, count check) *before* counting a snapshot as good; skip (and alert) if the source is unloadable; never prune below the last 3 verified-good; extend `_ARTIFACTS` to classifier, drift detectors, claims, garden, council ratings, baseline, behavioral directives | RECOVERY | med | low |
| P9 | Backup manifest + restore drill: each backup generation carries `MANIFEST.json` (paths, sizes, sha256, entry counts, Git HEAD, authored-source fingerprint); a restore checker loads copies in a write-jail (as in this audit) and asserts counts | RECOVERY + OBSERVABILITY | med | very low |
| P10 | Liveness-ledger check `state_preservation_health`: latest snapshot loadable, backup age, RiverBrain obs not dropped > 5 %, garden line count not dropped, FAISS/meta count equal, no `.corrupt-*` files | OBSERVABILITY | low | very low |
| P11 | Shrink windows: flush RiverBrain in `shutdown_handler`; save only when dirty; coalesce FAISS persists (e.g. ≤ 1 per 30 s); these cut exposure ~10–100× | DATA-LOSS PREVENTION | low–med | med (batching delays durability) |

**Priority by evidence value / cost:** P1+P2 (RiverBrain, classifier, garden) → P9/§14 off-disk generations → P5/P4 → P3 → P8 → the rest.

---

## 14. Two-machine preservation design (not executed)

**Distinguish BACKUP from SYNC.** The existing M5↔Air sync merges peer state; a synchronized deletion or corruption is not a backup, and *nothing here should be added to that channel*. Requirements: no paid service; either machine may be offline; checksummed manifests; corruption must not overwrite the last good copy; multiple generations; explicit restore; no bidirectional sync of live mutable state.

**Scheme (append-only generations, pull-based).**
1. **Producer (M5), no server downtime required.** A scheduled job (the existing `night_cycle` daily gate is the natural home; a human-run script also works) creates `gen-<UTC>/` containing the **minimal set** (~536 MB per the earlier byte-exact audit, ≈ 0.55 GB now): `river_brain.pkl`, FAISS + meta *as a pair*, `self_model_claims.jsonl`, `task_type_classifier.pkl`, `drift_detectors.pkl`, `question_garden.jsonl`, `council_ratings.jsonl`, `snapshot_baseline.json`, genesis/council hashes, `interaction_log.jsonl` (+`.1.gz`), plus `MANIFEST.json` (sizes, sha256, meta count, index ntotal, authored-source fingerprint, Git HEAD, `git bundle` of unpushed commits) and a `git diff HEAD` patch of the working tree. Pair consistency: copy meta then index, then re-read counts; if `meta_count != index_ntotal` or mtimes moved during the copy, discard and retry (never publish a torn pair).
2. **Local generations first** (`~/FeralEcho_backups/gen-*`, same disk — protects against logical corruption only): keep 24 hourly / 14 daily / 8 weekly by hard-link dedup where possible. Verify each generation immediately (recompute sha256; load in a write-jail; assert counts) before it may displace an older one.
3. **Off-machine copy — pull from the Air when it is online, or a removable disk.** The Air (or a $0 USB drive if one exists) *pulls* completed, verified generations (`rsync`/`scp` over the tailnet, or manual copy) into its own `received/gen-*` directory; it never writes back. Because it copies only *completed, manifest-verified* generations and never mirrors deletions (no `--delete`), a corrupted or deleted M5 source cannot overwrite a prior generation. Keep ≥ 3 generations on the Air; prune only on the Air, only by age, only after re-verifying a newer generation. Whether the Air is reachable over SSH from the M5 (or vice versa) is **UNKNOWN**; the manual USB path has no such dependency.
4. **Git:** push (human decision) or `git bundle` the 17 unpushed commits inside each generation so the authored source also exists off the SSD; do not track `memory/`.
5. **Restore procedure (documented, rehearsed):** stop the server via the watchdog path; verify a chosen generation's manifest; restore into a *new* directory; run the jailed loadability checker; only then swap files (`RiverBrain` pickle last, as `snapshot_manager` already orders); start; compare counts to the manifest. Never restore over live state without a fresh pre-restore copy.
6. **Drill:** restore the newest generation into a scratch directory monthly and record the result in the manifest history.

**What it deliberately avoids:** live two-way sync of FAISS/pickles/garden (concurrent writers would recreate the very lost-update problem in §9); "latest only" mirroring; automatic pruning without verification.

---

## 15. Runtime identity record for future experiments (general recommendation)

Capture, immediately before and after any serious run, one immutable `identity.json` (hash-chained if kept in a ledger):

1. **Source:** Git HEAD; dirty/clean; `git diff --cached` empty?; `git diff HEAD` sha256; **authored-source fingerprint** (§4 definition); individual hashes of self-mutating files; list of untracked non-ignored runtime-capable files with hashes; `.env` SHA-256 and name list (never values).
2. **Process:** PID, start time, parent, full command line, cwd, interpreter path and version, package-set hash (`pip list --format=freeze` sha256), Ollama version and **model digests** (`/api/tags`), sentinel contents.
3. **Loaded-code proof (the missing piece):** at startup, record every loaded source file and its SHA-256 into `memory/runtime_identity.json` (e.g. by walking `sys.modules` after imports, and again at intervals) and expose it read-only; this turns "present in the working tree" into "loaded by PID N". Until then, use the manifest's evidence classes and keep the distinction explicit.
4. **State generation:** RiverBrain observation total and file sha256; FAISS `ntotal` + meta count + both file hashes; claims/garden line counts and hashes; snapshot ids; last-backup generation id.
5. **Configuration/environment fingerprint:** sorted env names + safelisted values, `.env` hash, the relevant constants read from source.
6. **Operational context:** watchdog window (restart/abort counts since), recent `abort()` reports, disk free space.

The manifest in this audit is a working example of items 1, 2, 5 (partially) and the evidence-class discipline. This is a general recommendation only; the frozen persistent-competence protocol was not consulted or altered.

---

## 16. Ranked failure modes

Ratings: L = likelihood, B = blast radius, D = detectability, R = recoverability (1 low … 5 high, but for D and R **low is bad**). "Evidence" uses the labels above. Likelihoods for torn writes are **INFERRED** (formula: per-hard-abort probability = write-window × writes/hour ÷ 3600; expected events/year = that × aborts/year). Assumptions (stated in the evidence file): aborts interrupt writes uniformly in time; SIGTERM restarts behave equivalently; fixture windows measured on synthetic data at production scale; RiverBrain real serialization could be ~6× slower (pessimistic column); garden rewrite frequency assumed 36/h (unmeasured). Observed abort rate: 2 in ~25 h (~2/day) but variable (earlier weeks had more).

| # | Failure mode | Expected events/yr @ 2 aborts/day (fixture → pessimistic) | L | B | D | R | Evidence |
|---|---|---|---|---|---|---|---|
| 1 | **Question garden truncated by a hard abort mid-rewrite** | 0.25 → 0.73 | med | med (up to ~70 % of 16k entries) | **very low** (loads fine) | **none** (no backup) | FIXTURE-REPRODUCED; frequency INFERRED |
| 2 | **RiverBrain (and classifier) torn write → silent fresh reset** | 0.12 → 0.81 | med | med–high (selection statistics) | low (WARNING only) | med (snapshot ≤ ~1 day, sha-verified, unloaded) | FIXTURE-REPRODUCED |
| 3 | Interrupted FAISS/meta persist → permanent misalignment | 0.10 → 1.05 | low–med | high (retrieval correctness of all later memories) | med (WARNING per 120 s; no alert) | med–high (meta intact; needs re-embed + unwired tooling) | FIXTURE-REPRODUCED |
| 4 | **Loss of `memory/`/`data/`/uncommitted source (disk failure, mistaken cleanup, theft)** | UNKNOWN (rate not estimable) | low–unk | **total** | high | **none for nearly all** | PRODUCTION-OBSERVED (absence of backup) |
| 5 | Snapshot rotation evicts the last good RiverBrain copy within ~1 day (and may copy a torn file) | compounding with #2 | med | amplifies #2 | low | — | PRODUCTION-OBSERVED cadence; SOURCE-VERIFIED policy |
| 6 | Corrupt meta/index at load → empty state → overwrite | needs a corruption event (none observed) | very low | high (meta) | low–med | Sep-2 copy only | FIXTURE-REPRODUCED mechanism |
| 7 | `terminal_client` stale write while the server is down | needs concurrent terminal use + restart window | low | med | low | server re-asserts unless it dies | FIXTURE-REPRODUCED; gate SOURCE-VERIFIED |
| 8 | Two RiverBrain processes: higher-count stale writer wins | low (terminal/rehab CLI use) | low | low–med | low | — | FIXTURE-REPRODUCED |
| 9 | Running process ≠ committed/working source | already occurred (≥ 6 days lag) | — | identity/reproducibility, not data | med | — | PRODUCTION-OBSERVED |
| 10 | Undetected bit-level corruption of pickles (no checksum) | very low | low–med | low | none | — | FIXTURE-REPRODUCED (silent load) |
| 11 | Accidental `backup_feral_echo.sh` run (rewrites `.gitignore`, Git config, LFS) | low | low–med | high | high | — | SOURCE-VERIFIED |
| 12 | cwd-relative/hardcoded paths write state to the wrong tree | low impact to prod | low | low | — | — | SOURCE-VERIFIED |

**Highest-priority (high blast + low detectability + low recoverability):** #1 (garden), then #4 (no backup at all), then #2. #3 is the worst *quiet corruption* but is recoverable in principle. Likelihood was not inflated by consequence: none of these has been observed to occur in production.

---

## 17. Immediate no-code operational precautions

1. **Take a verified cold copy by hand** of the minimal set (§14 step 1) to a location off the SSD when convenient — checksum it, and record meta count vs index count (they must match). This is the single highest-value act available without changing code.
2. **Do not run `backup_feral_echo.sh`.** It overwrites `.gitignore`.
3. Prefer `SIGTERM` via `safe_restart.sh` (which correctly refuses when the watchdog is live); **never `kill -9` the server**; avoid restarts while a burst of activity is in flight; count restarts as exposure.
4. **Do not run `terminal_client.py` while the server is down or from a different directory**, and do not leave it running across server restarts.
5. Do not import `app.core.memory_bridge` (or the orchestrator) in ad-hoc Python sessions or scripts from the repo root: import-time construction loads production state and a later add persists over it. Use the jail pattern used here for any experiment that must load real classes.
6. Do not delete, "clean up", archive, or rotate the old backups (`memory/memory_meta_backup_before_*`, `memory/backups/`, `river_brain.pkl.pre_*`, `memory/reflection_shard.jsonl.pre_pending_cleanup`) — they are the only extra copies. The janitor already flags stale-backup patterns; treat those flags as *do not act*.
7. Do not restore a snapshot in response to `[RESTORE-ALERT] ram_sustained_92pct` (78 of 92 alerts) — that alert recommends the wrong remedy.
8. Push or bundle the 17 unpushed commits and commit or export the working tree when Gremlin decides (human action; not done here).

---

## 18. Recommended future fixes, ranked by evidence value and risk

| Rank | Fix | Why (evidence) | Risk |
|---|---|---|---|
| 1 | Verified off-disk generational backup (§14) with manifest + restore drill | #4: no verified recovery path for irreplaceable state | very low |
| 2 | P1 atomic-write helper on garden, RiverBrain, classifier, `np.save` states | #1, #2 fixture-reproduced | low |
| 3 | P2 refuse-to-overwrite/quarantine after failed load (+ alert) | #2, #6 | low–med |
| 4 | P5+P4 alignment guard, deterministic repair, paired manifest | #3 fixture-reproduced | med |
| 5 | P8 snapshot policy (time-based, loadability-verified, broader artifact list) | production-observed 20 h window | low |
| 6 | Runtime loaded-code registry (§15 item 3) | production-observed 6-day lag | very low |
| 7 | P6 single-writer + cross-process lock for FAISS/meta; remove the terminal's writable `VectorMemory` | #7 | med |
| 8 | Observability: `state_preservation_health` liveness check; alert on FAISS/meta divergence, RiverBrain obs drop | detectability gaps | very low |
| 9 | Anchor `RIVER_BRAIN_PATH`, `_CLASSIFIER_PATH`, garden path, and the two `~/Desktop/FeralEcho` hard-codes to `config.MEMORY_DIR`; change `VectorMemory` defaults to require explicit paths | #12 | low |
| 10 | Root-cause the Metal `abort()` rate (MLX) — reduces exposure to everything above | 2 aborts/day observed | separate investigation |

---

## 19. UNKNOWN items requiring later investigation

- Real (not synthetic) serialization time of the production RiverBrain pickle and real-disk persist timing under load; measured windows here are page-cache buffered.
- Question-garden rewrite frequency (not counted); the 36/h assumption is a midpoint.
- Whether the Air holds any usable copy of M5 state, whether SSH/rsync between the machines is enabled, and whether `origin` is reachable/current.
- Whether the terminal, `river_creative_rehab.py`, `spot_check.py`, or any script has actually written production state (not detectable retroactively).
- Isolation of the `scripts/*` and `app/experiments/*` modules that reference production paths (deliberately not audited: quarantine-adjacent).
- `claude_relay/relay.py` (modified, unimported): provenance not established.
- Whether `TaskTypeClassifier.bootstrap_from_log` and `self_heal.repair_vector_memory_index` actually work (untested).
- Whether APFS/`F_FULLFSYNC` durability matters at this abort/power profile.
- Historical abort rate across weeks (only one 25-hour window plus three retained crash reports measured now).
- Effect of `os.kill(pid,0)` `EPERM` on the gate in any real PID-reuse event.

---

## 20. Integrity record

```
Git HEAD (before): 2fba42644c82b9f7096276f4dd338d615cf1bcce
Working tree (before): 183 paths
Git HEAD (after):  2fba42644c82b9f7096276f4dd338d615cf1bcce (unchanged)
Working tree (after): 186 paths = 183 + the three audit artifacts created by this mission
Staging area: empty (git diff --cached --quiet) before and after; no commit, stash, ref, or index content changed
New files: audits/2026-09-20_feralecho_runtime_identity_and_state_preservation.md
           audits/2026-09-20_feralecho_runtime_identity_manifest.json
           audits/2026-09-20_feralecho_state_preservation_evidence.json
Also edited: audits/2026-09-20_feralecho_architectural_integrity_audit.md and its ledger (one correction notice re F-34)
Production source/config/state/model files modified: NONE. Server not restarted, signalled, or attached to.
Fixtures: kernel write-jailed; deleted (318 MB); scripts and jail profiles remain only in the session scratchpad
Protocol v1.0/v1.1 artifacts: not opened, not modified, not used
```

---

## Final questions

**1. What exact source identity best describes the FeralEcho instance running right now?**
Git HEAD `2fba42644c82b9f7096276f4dd338d615cf1bcce` **plus the uncommitted working tree as it stood at the process start**, i.e. 27 modified tracked files (17 executable-scope, ~1,697 inserted lines: shadow-model retirement, restore council gate, synthesis-fallback rule, fd-0 sandbox closure, location split, extra liveness checks) — authored-source fingerprint `8e6808dc64fbebe5…`, running as PID 29288 (`python -u run.py`, conda `feral_echo` Python 3.12.13, started 2026-09-20 07:30:10 local under the watchdog). Loaded-at-current-bytes is proven for `liveness_ledger.py` and inferred for the eagerly imported modified modules; it is **not** HEAD, and it is **not** whatever a later edit to the working tree says.

**2. What single credible mechanism presents the greatest risk of silently destroying irreplaceable accumulated state?**
A **hard process abort (the Metal `abort()` already occurring about twice a day, or a SIGTERM/SIGKILL) landing inside a non-atomic whole-file rewrite** — most damagingly `question_garden.jsonl` (truncated to a shorter, perfectly loadable file, no alert, no backup) and, next, `river_brain.pkl` (previous state destroyed by the truncate-first write, then silently replaced by a fresh brain). Both were reproduced with the real code. The quietest but recoverable neighbour is the FAISS/meta persist interrupted between its two replaces, which permanently misaligns later memories.

**3. What is the cheapest protection that would most reduce that risk?**
Two boring measures together: (a) one shared **atomic write helper** (tmp + fsync + `os.replace`) with **refuse-to-overwrite/quarantine after a failed load** on the garden, RiverBrain, and classifier — this removes the truncate-first window and the fresh-state overwrite; and (b) a **checksummed, generational, off-disk copy of the ~0.55 GB minimal state set** (§14) so that whatever slips through is recoverable. If only one can be done first, do (b) by hand today (§17.1): it protects against every mechanism, including the ones nobody has found.

**4. If the machine died tonight, which state could we actually prove is recoverable?**
Provable: git-tracked source, Modelfile, `echo_principles.json`, `COUNCIL.md`, `ORIGIN.md` up to the last commit that reached the remote (local ref `origin/main` = 2026-09-05; remote itself not contacted), and Ollama base models (registry, needs network). **Not provable — no off-disk copy exists: everything under `memory/` and `data/` (RiverBrain, all 130,837 memories, the question garden, claims, council ratings, classifier, drift detectors, logs), `.env`, and all source authored since 2026-09-05 (17 unpushed commits plus the uncommitted work).** Whether the Air holds a usable partial copy is UNKNOWN and was not inspected.

**5. What should we absolutely NOT do until preservation is improved?**
Do not run anything that loads or writes production state outside the server — no ad-hoc imports of `memory_bridge`/the orchestrator, no `terminal_client.py` while the server is down or started elsewhere, no `river_creative_rehab.py`, no experiments or pilots that construct RiverBrain/VectorMemory over real paths (including the quarantined persistent-competence work); do not `kill -9` or restart casually; do not run `backup_feral_echo.sh`; do not delete, archive, or "clean up" the old `memory_meta`/RiverBrain backups or rotate away the only snapshots; do not restore a snapshot in response to the RAM `[RESTORE-ALERT]`; and do not assume any of this is safe because the last hour of logs looked healthy — nothing here has *failed*, it has merely never been tested by an unlucky abort.
