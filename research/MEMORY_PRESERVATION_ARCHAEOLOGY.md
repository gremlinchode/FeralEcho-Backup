# Memory Preservation Archaeology

> **READ-ONLY ARCHAEOLOGY — NOT IMPLEMENTED — NOT A BACKUP**

Nothing under `memory/` was modified, moved, copied, deleted, renamed, or compressed to produce this document. No file's mtime was touched. The live FeralEcho process (PID 7644, confirmed running via read-only `pgrep`) was never signaled or restarted.

---

## 1. Executive Summary

`memory/` is **1.3GB, VERIFIED** (fresh `du -sh`, not assumed from a prior report). It is not one thing — it is a mix of genuinely irreplaceable accumulated state (RiverBrain's learned model-selection weights, the FAISS vector memory index and its metadata, self-model claims history), real historical evidence (interaction/reflection/council-deliberation logs), operationally-derived summaries that are themselves reconstructible from other state (`self_model.json`), and large volumes of pure operational logging with low unique-information density (`echo_watchdog.log`, 112MB). The single most important finding: **FeralEcho's own internal snapshot mechanism (`snapshot_manager.py`) already lives entirely inside this same unprotected directory** (`memory/snapshots/`, `memory/backups/`, `memory/history/`) — it protects against a bad self-edit, not against losing the machine, since a lost machine loses the snapshots too.

## 2. Inventory

Full top-level inventory captured by direct `du -sh memory/* memory/.[!.]*`, sorted by size (135 entries; not reproduced item-by-item here for every 4.0K state file — see Section 3 for the ones that matter). The twenty largest real entries:

| Path | Size | Type (observed) |
|---|---|---|
| `faiss.index` | 187M | binary FAISS index (`file` reports `data`) |
| `echo_watchdog.log` | 112M | plain-text operational log |
| `interaction_log.jsonl` | 96M | JSONL, one record per interaction |
| `backups/` (dir) | 96M | self-edit backup snapshots |
| `memory_meta.json` | 92M | JSON, FAISS UUID→text/metadata map |
| `memory_meta_backup_before_backfill_migration_20260902T075543Z.json` | 85M | dated pre-migration snapshot |
| `memory_meta_backup_before_reflection_migration_20260902T050420Z.json` | 85M | dated pre-migration snapshot |
| `dream_bridge.log` | 81M | dream-cycle text log |
| `archive/` (dir) | 74M | prior quarantine/retirement archives (per `CLAUDE.md`'s own documented history) |
| `experiments/` (dir) | 56M | contains only `learning/` and `preference_provenance/` subdirs — OBSERVED, not deeply inventoried in this pass |
| `reflection_shard.jsonl.pre_pending_cleanup` | 51M | a dated pre-cleanup backup, itself inside `memory/` |
| `council_deliberations.jsonl` | 41M | raw per-councillor deliberation records |
| `quarantine_journal.jsonl` | 34M | flagged/quarantined content history |
| `SELF_EDIT.log` | 26M | self-edit pipeline log |
| `validator_audit.log` | 24M | memory-write validator log |
| `snapshots/` (dir) | 19M | `snapshot_manager.py`'s own automated snapshots |
| `SELF_EDIT_MASTERY_.log` | 18M | self-edit mastery log |
| `reflection_journal.jsonl` | 13M | accumulated reflections |
| `reflection_shard.jsonl.1.gz` / `interaction_log.jsonl.1.gz` | 12M each | log-retention-rotated generations (per `log_retention.py`, `CLAUDE.md` Finding 51) |
| `optuna.db` | 9.0M | Optuna SQLite study (self-edit hyperparameter search history) |

Sub-4MB but individually important: `river_brain.pkl` (4.0M, plus five dated `.pre_*_backup*`/`.restore_tmp` sibling copies totaling ~8.6M more), `self_model.json` (20K), `self_model_claims.jsonl` (8.0K), `task_type_classifier.pkl` (52K), `drift_detectors.pkl` (4.0K), `echo_state.npy`/`echo_state_history.npy` (4.0K each), `genesis/` (12K, 3 files), `shadow_accuracy.jsonl`/`shadow_self_model.json` (776K/20K — Shadow was retired from live consumption earlier this session; these are now purely historical), `touch_signature.json`/`vision_signature.json`/`hearing_signature.json` (124K/124K/96K — sensor calibration/signature data), `behavioral_directives.json` + `behavioral_directives_audit.jsonl` + `behavioral_directives_backups/`, `christian_naturalist_reference.txt` (124K).

Referenced by production code: VERIFIED for every file named in `CLAUDE.md`'s own extensive Findings history (RiverBrain, self_model.json, echo_state.npy, FAISS pair, genesis hashes, snapshot dirs — all independently cross-checked against this project's own documentation, which itself has a demonstrated track record of drifting from code, so treat as DOCUMENTED, re-verify before relying on any single claim in a future implementation pass). Referenced by tests: no dedicated test suite exists in this project (`CLAUDE.md`'s own "Running Tests" section states this plainly) — research/verification scripts under `scripts/` reference several of these paths directly (`river_brain.pkl` was read directly by two separate missions earlier this session). Referenced by research tools: confirmed directly — this session's own Tier-5 archaeology read `memory/river_brain.pkl` via a real pickle load twice.

## 3. Classification

| Artifact | Class | Basis |
|---|---|---|
| `river_brain.pkl` | **A** | Classifiers/scalers/observation_counts/model_task_stats accumulated over real production conversation history spanning months (per this session's own direct reads — tens of thousands of real observations per model). No deterministic regeneration path exists; regenerating it means relearning from scratch over an equally long real-usage period. |
| `faiss.index` + `memory_meta.json` | **A** (paired — neither is meaningful without the other) | The vector index and its UUID→text metadata map are Echo's entire searchable conversational/reflection memory. Not regenerable from Git (gitignored, no source-of-truth copy exists in the tracked repository). |
| `self_model_claims.jsonl` | **A** | Evidence-tiered claim history (`self_model_claims.py`'s `record_claim()`/`resolve_subject_truth()`) — a real, append-only ledger of what was verified when; not derivable from anything else. |
| `interaction_log.jsonl`, `reflection_journal.jsonl`, `reflection_shard.jsonl`, `council_deliberations.jsonl`, `dream_bridge.log` | **A** (historical evidence, not learned weights, but equally irreplaceable) | Raw records of real events. No process regenerates lost history — these are logs, not caches. |
| `self_model.json` | **B**, bordering **C** | `self_model_updater.py` recomputes this from `memory/`'s other live state (FAISS counts, journal line counts, the liveness ledger, RiverBrain) roughly every 130s per `CLAUDE.md`'s own documentation — DOCUMENTED, not independently re-verified in this pass. If the *inputs* survive, this file regenerates itself within minutes of restart. If the inputs (A-class items above) are lost, this file cannot meaningfully regenerate either — its own `schema_version`/`last_updated` fields (OBSERVED directly) confirm it is a live-recomputed summary, not raw state. |
| `task_type_classifier.pkl`, `drift_detectors.pkl` | **A** | Online-learned classifier state (`task_type_classifier.py`) and PageHinkley drift detectors — per `CLAUDE.md`'s own documented history, the drift detectors alone carry 5,000+ real accumulated observations. Not regenerable without replaying an equivalent volume of real trustworthy input. |
| `optuna.db` | **B** | A real record of self-edit hyperparameter search history; losing it resets Optuna's search state to a cold start, but does not destroy any conclusion already reflected in `self_edit_generated.py`/`self_edit_convergence.json` (which live outside `memory/`, under `app/core/`). |
| `genesis/genesis_hash.txt` + `genesis_timestamp.txt` | **A** (the *timestamp* specifically) / **C** (the hash, conditionally) | `genesis_timestamp.txt` (dated Jun 27) records a specific real historical moment — irreplaceable as a fact about when the original hash-lock happened. `genesis_hash.txt` is a SHA-256 of `echo_principles.json`'s content at that moment; if the current tracked `echo_principles.json` is still byte-identical to what was hashed then, the hash is technically re-derivable — but there is no independent way to *confirm* that identity without the original hash to check against, which is precisely the tamper-detection function this file exists to serve. Treat as A, not C, for practical purposes. |
| `council_hash.txt` | Same as above, for `COUNCIL.md` | Same reasoning. |
| `echo_state.npy` / `echo_state_history.npy` | **B** | Current 9D state vector + rolling history buffer. Current value is cheaply reconstructed on next update cycle; the *history* (used for seam-detection correlation baselines per `CLAUDE.md`'s own Phase 8/Seam Engine documentation) is not independently reconstructable once lost, though its loss degrades a secondary/observational mechanism rather than core function. |
| `echo_watchdog.log`, `validator_audit.log`, `SELF_EDIT.log`, `SELF_EDIT_MASTERY_.log` | **A**-ish historically, **D** operationally | These are real historical evidence of past crashes/decisions (e.g., the MLX crash forensics `CLAUDE.md` documents extensively drew on exactly this kind of log), but their bulk (112MB+) is dominated by routine, low-information-density operational noise. Conservative classification: **B** — genuinely useful for retrospective forensic work, not required for Echo to function, and not worth the same preservation priority as A-class items. |
| `backups/`, `snapshots/`, `archive/`, `history/` (directories) | **D**, with one caveat | These are FeralEcho's *own* internal redundancy mechanisms (self-edit backups, `snapshot_manager.py`'s automated snapshots, `echo_janitor.py`'s archived clutter, weekly self-model history). Individually disposable/regenerable by design — **but see Section 9's ironic finding: they provide zero protection against the actual threat this whole mission investigates**, since they live in the same directory that would be lost with the machine. |
| `shadow_self_model.json`, `shadow_accuracy.jsonl`, `shadow_corrections.log` | **B**, historical only | Shadow was retired from all live production consumers earlier this session (`audits/2026-09-13_shadow_model_retirement.md`). These files are now pure historical record of a disconnected subsystem's past behavior — real, but not load-bearing for current operation. |
| `touch_signature.json`, `vision_signature.json`, `hearing_signature.json` | **A**, tentatively | Sensor-derived signature/calibration data (per `CLAUDE.md`'s sensory-system references). Not independently verified in this pass whether these are re-derivable from a fresh sensor capture or represent accumulated calibration history — flagged **E (Unknown)** pending a closer look at the code that writes them, conservatively treated as A until proven otherwise. |
| `behavioral_directives.json` + audit + backups | **A**, tentatively | Name and structure strongly suggest real operator-configured or learned behavioral state; not independently traced to its writer in this pass — **E (Unknown)**, conservatively A. |
| `christian_naturalist_reference.txt` | **E (Unknown)** | 124K of plain text; not read in this pass beyond confirming it exists and is not JSON (per the safety instruction against reading conversational/personal content unnecessarily). Could be a curated reference document (worth real preservation) or a cached copy of externally-sourced material (regenerable). Genuinely unknown without reading content this mission chose not to read. |

## 4. Dependency Graph / Write-Read Relationships

Cross-referenced against `CLAUDE.md`'s own extensive documented history (DOCUMENTED, not independently re-verified against live source code in this read-only pass — flagged explicitly per this project's own repeated finding that its documentation can drift from current behavior):

- **`river_brain.pkl`**: written by `RiverBrain._do_save()` (both explicit `.save()` calls and a background writer thread firing ~every 60s, per this session's own direct Tier-8-derived knowledge of this exact mechanism); read by `RiverBrain.load()` at process start and by every `_select_council()` call thereafter. Startup depends on it (a missing/corrupt file falls back to a fresh, cold-start instance — DOCUMENTED, not re-verified here). No hash/checksum found protecting it; several dated `.pre_*_backup` siblings exist inside `memory/` itself, confirming this project has manually protected against its own corruption before, informally, by hand-copying — itself evidence this file is considered valuable enough to have been manually backed up on past occasions, never automated.
- **`memory_meta.json` + `faiss.index`**: written by `memory_bridge.py`'s `add_to_vector_memory()`/`_persist()` on every real memory write; read on every retrieval call. Two dated `memory_meta_backup_before_*_migration` files (170M combined) confirm this file has also been manually protected before a risky operation, by hand, informally — the same pattern as `river_brain.pkl`.
- **`self_model.json`**: written by `self_model_updater.py` on a fixed ~130s timer (DOCUMENTED); read by `echo_ground_truth.py`'s prompt-injection slices and by the Liveness Ledger's `self_model_drift` check. Carries its own `schema_version` field (OBSERVED directly this pass).
- **`genesis/genesis_hash.txt`, `council_hash.txt`**: read at server startup (`run.py`'s `start_background_threads()`, per `CLAUDE.md` Finding 68) to verify `echo_principles.json`/`COUNCIL.md` haven't been tampered with; written exactly once, by hand, when each hash-lock was first established.
- **`snapshots/`, `backups/`, `history/`**: written by `snapshot_manager.py` (automated, on startup and post-self-edit triggers) and `night_cycle.py`'s weekly self-model snapshot; read only by the human-confirmed restore path (`check_and_alert()`/`raise_restore_alert()` → manual `POST /admin/restore`). No autonomous restore path exists (DOCUMENTED, `CLAUDE.md`'s own explicit statement).
- **`task_type_classifier.pkl`, `drift_detectors.pkl`**: written incrementally as real conversational examples pass through `is_trustworthy_training_example()`'s filter; read at classifier-inference time and by the Liveness Ledger's drift-detector-adjacent checks.
- **Schema/version info**: found explicitly only on `self_model.json` (`schema_version` field, OBSERVED). No hash/checksum mechanism was found protecting `river_brain.pkl`, `faiss.index`, or `memory_meta.json` against silent corruption — their only informal protection is the hand-made dated backup copies already noted.
- **Corruption detection**: **UNKNOWN/not found** for the large binary/JSON state files in this pass — no code path was independently traced in this read-only session confirming a checksum or schema-validation gate exists on load for `river_brain.pkl`/`faiss.index`/`memory_meta.json`. This is a real, disclosed evidence gap, not a claim that no protection exists.

## 5. Irreplaceable vs Regenerable State

Restated plainly from Section 3: the irreplaceable core is small in *count* but large in *consequence* — `river_brain.pkl`, the `faiss.index`/`memory_meta.json` pair, `self_model_claims.jsonl`, `task_type_classifier.pkl`, `drift_detectors.pkl`, and the raw historical-evidence logs (`interaction_log.jsonl`, `reflection_journal.jsonl`, `reflection_shard.jsonl`, `council_deliberations.jsonl`, `dream_bridge.log`). Everything else in the top-20-by-size list (Section 2) is either a derivable summary (`self_model.json`), Echo's own internal (currently unprotected) redundancy mechanism (`backups/`, `snapshots/`, `archive/`), or high-volume operational logging whose forensic value is real but secondary to core function.

## 6. Historical / Learned / Executable / Derived / Cache State

- **Executable state**: `echo_server.pid`, `echo_sentinel.json`, `self_edit_cooldown.json` and similar small runtime-coordination files — needed for correct operation right now, trivially regenerated by a clean restart (Category C/D).
- **Learned state**: `river_brain.pkl`, `task_type_classifier.pkl`, `drift_detectors.pkl` — Category A, the clearest cases of genuinely learned (not merely logged) information.
- **Historical evidence**: `interaction_log.jsonl`, `reflection_journal.jsonl`, `council_deliberations.jsonl`, `dream_bridge.log`, `echo_watchdog.log`, `SELF_EDIT.log` — records of what happened, not weights that drive future behavior directly (though some, like `reflection_journal.jsonl`, are themselves *read back* as source material for future reflection sampling, per `CLAUDE.md`'s documented dream-cycle sampling mechanism — blurring the historical/learned line for this specific file).
- **Derived state**: `self_model.json`, `echo_state.npy` — computed from other `memory/` state on a live cycle; would regenerate within minutes of restart *if their own inputs survive*, otherwise regenerate to an empty/cold baseline.
- **Cache state**: log-rotation `.1.gz` generations, `.pyc`-adjacent artifacts (none found directly under `memory/` in this pass), `code_scan_hash_cache.json`, `signal_hash_cache.json` — pure performance/dedup caches, Category D.
- **Identity/self-model state**: `self_model.json`, `self_model_claims.jsonl`, `shadow_self_model.json` (historical only, post-retirement).

These categories do **not** map one-to-one with files, confirmed directly — `reflection_journal.jsonl` is simultaneously historical evidence *and* a future input to the dream cycle's own sampling process, and `self_model.json` is simultaneously derived state *and* the thing several liveness checks treat as ground truth to compare against.

## 7. Provenance & Integrity Findings

- **Timestamps**: present on most JSONL/log entries (OBSERVED — standard `ts`/`timestamp` fields throughout this codebase's own established convention). `self_model.json` has an explicit `last_updated` field (OBSERVED).
- **Provenance/schema/version info**: `schema_version` on `self_model.json` only (OBSERVED). No equivalent field found on `river_brain.pkl`, `faiss.index`, or `memory_meta.json` in this pass — **UNKNOWN** whether one exists internally to the pickle structure without a deeper, more invasive inspection this mission's safety scope didn't require.
- **Hashes**: `genesis_hash.txt`/`council_hash.txt` exist specifically to hash *other* tracked files (`echo_principles.json`/`COUNCIL.md`), not to protect `memory/`'s own content. No hash file protecting `river_brain.pkl`/`faiss.index`/`memory_meta.json` against silent corruption was found.
- **The restoration-authenticity question the mission specifically asks about — "if this state were restored onto another machine, how could FeralEcho distinguish authentic historical state from arbitrary replacement data?"** — **this is a real, confirmed, currently-unaddressed evidence gap.** No mechanism was found anywhere in this pass that would let FeralEcho verify a restored `memory/` directory's authenticity/provenance versus an arbitrary substitute of the same shape. This is not solved here, per the mission's own explicit instruction — documented as open (see Section 14).

## 8. Portability Findings

Under the assumed scenario (Mac destroyed, fresh machine + Git repo + committed research/evidence available, `memory/` unavailable):

- **Startup**: would very likely still technically succeed — most of the small runtime-coordination files (Category C/D) self-initialize on first run, per the same reasoning `self_model.json`'s own recompute cycle relies on.
- **What would silently be different, not loudly broken**: RiverBrain would start from a cold, unlearned state — council model selection would revert to whatever cold-start/exploration behavior the code defines, with zero memory of which models have historically performed well on which task types. This is the single most concerning "silently behaves differently" finding — nothing would error, but months of learned preference would be gone and nothing would announce that fact to an operator unfamiliar with this specific risk.
- **What research history would disappear**: everything in `interaction_log.jsonl`/`reflection_journal.jsonl`/`council_deliberations.jsonl`/`dream_bridge.log` — real conversational and reflective history, not reconstructable from committed Git research artifacts (which capture *conclusions*, not the underlying raw conversational substrate that produced them).
- **What self-model information would disappear**: `self_model.json` would regenerate, but starting from the same cold RiverBrain/FAISS baseline above — its *content* would be accurate to the new, impoverished state, not falsely stale, but the state it accurately describes would be much poorer than before.
- **What learned state would disappear**: `river_brain.pkl`, `task_type_classifier.pkl`, `drift_detectors.pkl` — confirmed Category A, confirmed lost under this scenario.

## 9. Hypothetical Disaster-Recovery Analysis

The clearest, most important finding of this whole archaeology: **`snapshot_manager.py`'s own automated protection mechanism (`memory/snapshots/`, `memory/backups/`, `memory/history/`) provides zero defense against the exact scenario this mission investigates**, because it stores its snapshots inside the same directory tree that would be destroyed along with the machine. This is not a design flaw in `snapshot_manager.py` itself — it was built to protect against a *bad self-edit*, a real and different threat it handles well (per `CLAUDE.md`'s own extensive documentation of it working correctly) — but it means the informal, hand-made `.pre_*_backup`/`.pre_*_migration` copies already found scattered through `memory/` (Section 4) represent the *only* redundancy this state currently has, and all of them live in the same single point of failure.

## 10. Minimal Backup Candidate Set

Not a recommendation to back up all of `memory/`. Smallest set that preserves the largest share of genuinely irreplaceable state:

| Candidate | Why it matters | Size | Sensitivity | Volatility | Regen difficulty |
|---|---|---|---|---|---|
| `river_brain.pkl` | Category A — months of learned council-selection weights | 4.0M | Low (no personal content, model performance stats only) | High (changes ~every 60s) | Cannot be regenerated except by relearning over an equivalent real-usage period |
| `faiss.index` + `memory_meta.json` | Category A pair — entire searchable conversational/reflection memory | 279M combined | **High** — likely contains real personal/conversational content, not independently read in this pass | Moderate (grows with use) | Cannot be regenerated at all |
| `self_model_claims.jsonl` | Category A — evidence-tiered claim history | 8.0K | Low | Low-moderate | Cannot be regenerated |
| `task_type_classifier.pkl` + `drift_detectors.pkl` | Category A — online-learned classifier/drift state | 56K combined | Low | Moderate | Cannot be regenerated without replaying real input volume |
| `genesis/` (all 3 files) | Irreplaceable historical anchor for tamper-detection | 12K | Low | None (write-once) | Cannot be regenerated — the timestamp specifically is a historical fact |
| `interaction_log.jsonl`, `reflection_journal.jsonl`, `reflection_shard.jsonl`, `council_deliberations.jsonl`, `dream_bridge.log` | Category A — raw historical evidence | ~248M combined | **High** — real conversational content | Continuous | Cannot be regenerated |

**Total minimal candidate set: roughly 600MB of `memory/`'s 1.3GB** — under half, while capturing essentially all of what this pass classified as genuinely irreplaceable (Category A). The remaining ~700MB is dominated by operational logs (Category B/D) and Echo's own self-redundant backup directories (Category D, per Section 9's finding — backing these up specifically would be redundant with backing up their own sources).

## 11. Sensitive Material Findings

A keyword-pattern scan (filenames matched only, no values read or reproduced) flagged **possible secret-like or sensitive-topic pattern matches** in `memory/memory_meta.json`, its two dated migration-backup siblings, `memory/prompt_history_state.json`, and `memory/christian_naturalist_reference.txt`. **These are unverified and most likely false positives** — three of the four are conversational/reflection-content files where words like "token," "secret," or "password" plausibly appear in ordinary narrative or discussion content rather than as literal credentials, and this pass deliberately did not read the matched lines to confirm either way, per the explicit instruction not to read sensitive content unnecessarily. Reported here as "secret-like material detected, unverified nature" per the mission's own required reporting format — **no value was read, printed, or reproduced anywhere in this investigation.**

Separately, `memory/sync_state.json` contains a real Tailscale IP address (a second machine's network location, per this project's own documented M5↔Air sync protocol) — network-topology information, not a credential, but real machine-specific data worth noting under restoration dependencies.

The FAISS/`memory_meta.json` pair and the raw interaction/reflection logs almost certainly contain real personal conversational content by their very nature and purpose — this is stated as an inference from what these files are documented to be, not from having read their content in this pass.

## 12. Restoration Dependencies

Not implemented, characterized only: a fresh machine would need — the same directory structure (`memory/` at the project root, matching every hardcoded relative path this project's own code uses throughout, per its extensively-documented history of exactly this kind of path-anchoring bug); a compatible Python/conda environment (per the separate strategic-resilience research's own finding that no tracked environment export currently exists); the same or compatible Ollama model tags (model identifiers embedded in `river_brain.pkl`'s `model_task_stats` keys would reference models that must be re-pulled by the same names to remain meaningful); no database migration/schema-versioning mechanism was found for `river_brain.pkl`/`memory_meta.json`/`faiss.index` in this pass (**UNKNOWN**, not confirmed absent, just not found); initialization order matters for `self_model.json` (must follow, not precede, restoration of its own inputs, or it will silently regenerate to a falsely-impoverished-looking state that is actually just temporarily uninitialized rather than genuinely lost — a real, disclosed ambiguity a restoration procedure would need to handle explicitly).

## 13. Adversarial Findings

- **Is this genuinely learned information or merely cached output?** Mixed, by design — `river_brain.pkl`/`task_type_classifier.pkl`/`drift_detectors.pkl` are genuinely learned; a meaningful fraction of the rest (Section 6) is closer to cache or derived summary.
- **Could the same state be recreated from Git and raw research evidence?** No, for the Category A items — committed research documents capture conclusions drawn *from* this state, not the state itself.
- **Is the state machine-specific?** Yes, currently entirely — nothing under `memory/` is version-controlled or otherwise replicated off this one machine (confirmed via the separate preservation-preflight mission this same session, which found no backup mechanism for `memory/` anywhere).
- **Could restoring stale memory cause Echo to make incorrect claims?** Plausibly yes — `self_model.json`'s own liveness-ledger-cross-checked staleness convention (per `CLAUDE.md`) exists specifically because this exact failure mode has happened before in this project's history for other state; a naively restored, stale `memory/` snapshot could reintroduce it.
- **Could restoring corrupted memory be worse than losing it?** Plausibly yes for `river_brain.pkl` specifically — a corrupted pickle that partially loads could silently poison council selection in a way that's harder to detect than a clean cold-start would be. Not tested in this pass; a real, open risk.
- **Does the current architecture have any integrity check for restored memory?** **Not found in this pass** — this is the same gap Section 7 already names. Genuinely open, not solved here.
- **Does memory contain state that conflicts with committed research conclusions?** Not checked directly in this pass — a real, open question (Section 14).
- **Could two reconstructed machines legitimately diverge because their memory differs?** Yes, structurally — two machines restored from different points in `memory/`'s history, or from no `memory/` at all vs. a partial restore, would develop genuinely different learned RiverBrain weights and different accumulated reflection history from that point forward.
- **What would "same FeralEcho" actually mean after reconstruction?** Genuinely unresolved by this archaeology, and stated as such rather than answered — the code and research history would be identical; the learned, accumulated, experiential state would not be, and this project has no existing framework (per Section 7's finding) for expressing how much of that difference matters.

## 14. Open Questions

1. Does any corruption-detection or schema-validation mechanism exist for `river_brain.pkl`/`faiss.index`/`memory_meta.json` on load that this read-only pass simply didn't find? (Section 4/7 — genuinely UNKNOWN, not confirmed absent.)
2. What is actually inside `christian_naturalist_reference.txt`, `touch_signature.json`/`vision_signature.json`/`hearing_signature.json`, and `behavioral_directives.json` — are they authored/calibrated (Category A) or regenerable (Category C)? Deliberately not read in this pass.
3. How would FeralEcho distinguish authentic restored `memory/` state from an arbitrary substitute of the same shape (Section 7's central unaddressed gap)?
4. Does any conflict currently exist between live `memory/` state and a committed research conclusion (Section 13's unchecked question)?
5. What, precisely, does `memory/experiments/` (56M, two subdirectories: `learning/`, `preference_provenance/`) contain — not inventoried below the top level in this pass.

## 15. Recommendation

Do not back up all of `memory/` (1.3GB, most of it operational logging or Echo's own already-redundant internal copies). Do not conclude memory is safely disposable either — Section 3's Category A list is real, substantial, and currently has zero protection beyond informal, hand-made, same-machine copies. The minimal candidate set in Section 10 (~600MB) is the evidence-grounded middle path this mission was asked to characterize, not blindly choose between the two extremes.

## 16. Repository Impact

- Path count before: 134. Path count after: 135 (this one new document).
- HEAD before: `2fba42644c82b9f7096276f4dd338d615cf1bcce`. HEAD after: unchanged.
- Nothing staged. Nothing committed. Nothing pushed.
- Confirmed: no file under `memory/` was modified, moved, copied, deleted, or renamed — every command used was a read-only inspection (`du`, `stat`, `file`, `ls`, `grep -l`, `python3 -c "json.load(...)"`).
- Confirmed: the live FeralEcho process (PID 7644) was checked only via read-only `pgrep`, never signaled, restarted, or otherwise touched.

---

### MEMORY SURVIVABILITY VERDICT

**A — Critical preservation gap.** Real, substantial, irreplaceable accumulated state exists (Section 3/5/10) and currently has no adequate preservation mechanism of any kind — not even the informal same-machine copies already scattered through `memory/` (Section 4/9) provide protection against the actual scenario this mission investigates, since they share the single point of failure they'd need to protect against.

**Smallest safe next engineering action that would materially improve survivability**: a single, simple, off-machine copy of Section 10's minimal candidate set (~600MB — `river_brain.pkl`, the `faiss.index`/`memory_meta.json` pair, `self_model_claims.jsonl`, `task_type_classifier.pkl`, `drift_detectors.pkl`, `genesis/`, and the five raw historical-evidence logs) — not a full `memory/` mirror, not a new subsystem, not an automated pipeline on day one. This action is **not performed by this mission**, per its explicit read-only scope.
