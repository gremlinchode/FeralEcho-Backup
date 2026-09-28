# Memory Preservation Set Audit — Final Gate Before Off-Machine Copy

> **READ-ONLY FINAL PRESERVATION GATE — NO COPY PERFORMED — NOT IMPLEMENTED**

Nothing under `memory/` was modified, moved, copied, deleted, renamed, or touched (mtime-wise) to produce this document. Every inspection used a read-only command (`stat`, `ls`, `find`, `grep -l`, direct source reads of `app/core/echo_model_orchestrator.py`). No new file, hash, or checksum was created anywhere, inside or outside the repository. The live FeralEcho process (PID 7644, `Thu Sep 10 22:41:53 2026`) was checked only via read-only `ps`, never signaled or restarted.

---

## 1. Executive Summary

The prior archaeology's proposed ~600MB minimal set **survives this audit's scrutiny in composition, with one real correction: its own size estimate was overstated.** Independent, byte-exact recalculation of the same 13-item set gives **536,089,378 bytes (≈511.2 MiB / ≈536.1 MB decimal / ≈0.50 GiB)** — real, but roughly 11-12% smaller than the previously reported "~600MB." No member was found that should be excluded on redundancy, disposability, or excessive-sensitivity grounds, and no missing irreplaceable member was found. One genuinely new finding not present in the prior pass: `memory/snapshots/`'s five most recent automated snapshots (dated Sep 11-13) **each already contain a full copy of `river_brain.pkl`**, confirmed by direct `find`. This is real, but is explicitly **same-failure-domain redundancy** (Section 8) — it does not reduce the case for off-machine copying, it only confirms the file is already treated as critical enough to snapshot automatically.

## 2. Previous Proposed Set

Reconstructed directly from `research/MEMORY_PRESERVATION_ARCHAEOLOGY.md` Section 10, not from the coordinator's paraphrase: `river_brain.pkl`; `faiss.index` + `memory_meta.json` (paired); `self_model_claims.jsonl`; `task_type_classifier.pkl` + `drift_detectors.pkl`; `genesis/` (all 3 files); `interaction_log.jsonl`, `reflection_journal.jsonl`, `reflection_shard.jsonl`, `council_deliberations.jsonl`, `dream_bridge.log`. Thirteen files total. The prior document's own Section 10 table already used approximate, `du`-rounded sizes (4.0M, 279M combined, 8.0K, 56K combined, 12K, ~248M combined) and explicitly labeled the ~600MB total as a sum of those roundings, not an exact figure — this audit's job is exactly the reconciliation the prior document itself deferred.

## 3. Exact Size Reconciliation

Byte-exact `stat -f "%z"` on every member, independently summed:

| Path | Exact bytes |
|---|---|
| `river_brain.pkl` | 4,049,550 |
| `faiss.index` | 196,455,981 |
| `memory_meta.json` | 96,411,247 |
| `self_model_claims.jsonl` | 7,364 |
| `task_type_classifier.pkl` | 49,354 |
| `drift_detectors.pkl` | 1,034 |
| `genesis/genesis_hash.txt` | 64 |
| `genesis/genesis_timestamp.txt` | 18 |
| `genesis/council_hash.txt` | 65 |
| `interaction_log.jsonl` | 96,604,555 |
| `reflection_journal.jsonl` | 13,140,560 |
| `reflection_shard.jsonl` | 6,383,735 |
| `council_deliberations.jsonl` | 42,825,089 |
| `dream_bridge.log` | 80,160,762 |
| **Total** | **536,089,378 bytes** |

= **511.24 MiB = 0.4993 GiB = 536.09 MB (decimal) = 0.536 GB (decimal).**

**Verdict on "~600MB": substantially rounded, not materially incorrect.** The real figure (≈536MB decimal) is about 64MB (≈11%) smaller than previously stated. The prior document's own qualitative conclusion — "roughly 600MB of `memory/`'s 1.3GB, under half" — still holds directionally (536MB is ≈41% of the independently-reconfirmed 1.3GB total, still well under half), but the specific number should be corrected going forward. Root cause of the discrepancy, OBSERVED directly: the prior pass's own Section 10 table sums `du`-style block-rounded figures (which round every file, however small, up to the next allocation-block multiple) rather than exact byte counts — a real, disclosed methodological gap in that pass, not a data-entry error.

## 4. Artifact-by-Artifact Audit

**`river_brain.pkl` — KEEP.** VERIFIED (direct source read, `app/core/echo_model_orchestrator.py:1113-1148`): `RiverBrain.load()` merges classifiers/scalers/observation_counts/accuracy_trackers/model_task_stats from the pickle. No equivalent information exists anywhere else — `model_task_stats` in particular is nowhere else persisted. Confirmed machine-independent in content (per-model performance statistics, not host-specific paths), though the *model names* used as dict keys (e.g. `qwen2.5-coder:7b`) are Ollama tags that must exist by the same name on a restore target for the restored state to remain meaningful — a restoration dependency (Section 11), not a reason to exclude.

**`faiss.index` + `memory_meta.json` — KEEP, structurally paired.** OBSERVED: `faiss.index` is a raw FAISS binary index (vector embeddings only, no human-readable content); `memory_meta.json` (96.4MB) is the UUID→text/metadata map that makes the index's vector IDs meaningful. Restoring one without the other would produce either an unusable index (no way to recover what any vector represents) or an orphaned metadata file with nothing to search against — genuinely unsafe to split. No smaller "index-only" or "metadata-only" fallback was found; both or neither.

**`memory_meta.json` — confirmed structurally required alongside `faiss.index`, not independently sufficient.** Reconfirms the prior pass's own finding; no new evidence contradicts it.

**`self_model_claims.jsonl` — KEEP.** Small (7,364 bytes), append-only evidence-tiered claim ledger per `self_model_claims.py`. No duplicate found anywhere else in `memory/` or the repository (checked via `find`/`grep -l` in Section 6 below). Historical substrate, not regenerable.

**`task_type_classifier.pkl` — KEEP.** 49,354 bytes, online-learned classifier state. No equivalent training-data snapshot found preserved elsewhere that would let this be retrained to the same state; loss would silently degrade `detect_task_type()`'s low-confidence fallback path without necessarily erroring.

**`drift_detectors.pkl` — KEEP.** 1,034 bytes — trivially cheap to preserve regardless of its accumulated-observation value, and per `CLAUDE.md`'s own documented history carries 5,000+ real PageHinkley observations per task type. No cost argument exists against keeping this one.

No member of the six core artifacts was found UNCERTAIN — all six are confidently KEEP on direct re-evaluation.

## 5. Historical Log Audit

All five re-evaluated against the specific question asked: **do they contain historical information not reconstructable from committed research or other surviving memory files?**

- **`interaction_log.jsonl`** (96.6MB) — raw per-interaction records. `research/`'s own ledger (`FINDINGS.md` etc.) captures *conclusions drawn from* patterns in this data, never the individual raw turns themselves. **Irreplaceable historical substrate.**
- **`reflection_journal.jsonl`** (13.1MB) and **`reflection_shard.jsonl`** (6.4MB) — accumulated real reflections. Per `CLAUDE.md`'s documented dream-cycle sampling mechanism, `reflection_journal.jsonl` is also *read back* as future sampling material — meaning its loss is not just a historical-record loss but also a live, forward-looking input loss. **Irreplaceable historical substrate**, with an additional live-dependency dimension the prior pass already flagged (Section 6 of the prior document) and this audit reconfirms rather than revises.
- **`council_deliberations.jsonl`** (42.8MB) — raw per-councillor pre-synthesis opinions, per `CLAUDE.md`'s Phase 10 documentation the *only* record of what individual councillors said before synthesis discarded or altered it. This is the single clearest case in the whole set of information that cannot be reconstructed from anywhere else — not from `interaction_log.jsonl` (which only records the final synthesized answer), not from research conclusions. **Irreplaceable historical substrate**, arguably the highest-value-per-byte item in the entire five-log group.
- **`dream_bridge.log`** (80.2MB) — dream-cycle text log. Largest of the five logs by a wide margin relative to its likely unique-information density (plain-text log, not structured JSONL with distinct per-record fields). **Irreplaceable in the sense that no other file duplicates it, but the lowest-confidence member of this group** on a pure information-density basis — flagged as a genuine judgment call in Section 12, not a settled EXCLUDE.

**Confirmed, explicitly, per the mission's own instruction not to assume the research ledger substitutes for raw evidence**: none of the five logs have an equivalent record anywhere in `research/` or `audits/` — those directories contain interpretations and conclusions, never a verbatim replay of the underlying conversational/behavioral substrate.

## 6. Genesis Anchor Audit

`genesis/genesis_timestamp.txt` (18 bytes, dated Jun 27) — DOCUMENTED (per `CLAUDE.md` Finding 68, cross-referenced, not independently re-traced to source in this pass) as read once at server startup to establish the tamper-detection hash-lock's own historical anchor. Genuinely write-once: `stat` confirms an mtime of Jun 27, unchanged since, consistent with the prior pass's characterization. No equivalent record of this exact moment exists elsewhere in the repository (the Git commit history for `echo_principles.json` records *when the file was committed*, not necessarily the same moment the hash-lock was established against a possibly-uncommitted or differently-timed local state). **Should be preserved, confirmed, despite its trivial size** — the earlier pass's reasoning holds without revision.

## 7. Redundancy Analysis

Explicit `find`-based search of the whole `memory/` tree for anything sharing a name pattern with the 13 proposed members:

- **`river_brain.pkl`**: found duplicated in `memory/snapshots/20260911T054301Z/`, `.../20260912T063742Z/`, `.../20260912T093336Z/`, `.../20260912T114131Z/`, `.../20260913T161158Z/` (5 recent automated snapshots), plus historical, stale, dated `.pre_*_backup`/`.restore_tmp`/`.zeroed_backup` siblings directly in `memory/` (already noted by the prior pass). **All same-filesystem, same-machine — see Section 8, none count as independent protection.**
- **`faiss.index` / `memory_meta.json`**: found duplicated (stale, historical, not current) in `memory/backups/faiss_pre_delete_20260705T213227Z.index` + matching `memory_meta_pre_delete_*.json`, `memory/backups/pre_migration_20260713/{faiss.index,memory_meta.json}`, and three further stale copies in `memory/archive/` (`faiss_contaminated_*`, `faiss_splitbrain_*`, `faiss_prefixfix_*`, each with a matching `memory_meta_*` sibling) — these correspond to the real FAISS split-brain/contamination incidents `CLAUDE.md` already documents extensively. **All stale (dated Jul 2-13), all same-filesystem — none are current-state redundancy and none are independent.**
- **`self_model_claims.jsonl`, `task_type_classifier.pkl`, `drift_detectors.pkl`, `genesis/*`, and all five raw logs**: no duplicate, archive, or backup copy of any of these found anywhere in `memory/`'s `snapshots/`, `backups/`, `archive/`, or `history/` subdirectories, nor anywhere else in the repository. **Single points of failure with zero informal redundancy, formal or otherwise.**

**No member of the proposed set has an equivalent copy that is actually independent of the M5's local filesystem.** This confirms, rather than weakens, the case for the proposed off-machine copy.

## 8. Same-Failure-Domain Analysis

Explicitly reported per the mission's required framing: the `river_brain.pkl` copies inside `memory/snapshots/`, and every `faiss.index`/`memory_meta.json` copy inside `memory/backups/` and `memory/archive/`, are **Same-failure-domain redundancy** — real files, genuinely present, but residing on the exact same physical disk that would be destroyed along with the M5. None of them constitute off-machine disaster protection, and none of them should be relied upon as a substitute for the proposed copy. This is the same conclusion the prior archaeology's Section 9 already reached in general terms; this audit adds the specific, confirmed file-level evidence (the five dated snapshot directories) that the prior pass did not enumerate.

## 9. Sensitivity Findings

Reconfirms the prior pass's findings; no new sensitive material was found in this audit's narrower re-scan of the 13 proposed members specifically, and none was newly introduced by this pass's own read-only inspection (no file content beyond structure/size/existence was read for the large conversational files, matching the safety scope).

- `memory_meta.json` and the raw conversational/reflection logs (`interaction_log.jsonl`, `reflection_journal.jsonl`, `reflection_shard.jsonl`, `council_deliberations.jsonl`, `dream_bridge.log`) **almost certainly contain real personal conversational content by their documented purpose** — this remains an inference from what these files are, not from reading their content, per the mission's own instruction.
- No credential-shaped or secret-shaped value was read, printed, or reproduced anywhere in this pass.
- **`sync_state.json` — confirmed EXCLUDE, was never part of the proposed set to begin with.** The prior archaeology correctly did not include it. Re-confirmed here: it holds live network-topology state (a second machine's Tailscale IP, per the prior pass's own finding, not reproduced here either) relevant to the *current* sync protocol's operation, not to historical recovery of accumulated knowledge — restoring it onto a replacement machine would encode a stale, potentially wrong network address rather than provide any recoverable value. No reason found to add it to the minimal set.

## 10. Restoration Coherence

**Confirmed real, disclosed limitation, not resolved here (per the mission's own explicit instruction not to invent a solution):** none of the 13 proposed artifacts carry any cross-artifact synchronization or version marker that would let a future restoration process confirm they were captured *from the same point in time*. Concretely — nothing prevents, and nothing would detect, a hypothetical future restoration that combined `river_brain.pkl` from one moment with `faiss.index`/`memory_meta.json` from a different moment; the only relationship enforced by anything found in this pass is the internal `faiss.index` ↔ `memory_meta.json` pairing itself (Section 4), which matters because they're read together at retrieval time, not because anything checks their timestamps agree.

**One genuinely reassuring finding, not present in the prior pass**: `memory/snapshots/*/manifest.json` (per Section 7's discovery) already bundles `river_brain.pkl` with `echo_principles.json`, `Modelfile`, `self_edit_generated.py`, and hash files, captured together at one real, atomic point in time, by the existing `snapshot_manager.py` mechanism. This does not solve the coherence problem for the *full* 13-item preservation set (snapshots don't include `faiss.index`/`memory_meta.json`/the raw logs at all), but it does mean a real precedent for "capture several related artifacts atomically" already exists in this codebase, should a future mission want to build on it rather than invent one from scratch. Not proposed as a solution here — noted as an existing building block.

## 11. Integrity / Provenance Findings

Reconfirms the prior pass, with one addition: **VERIFIED** directly this pass (source read, Section 4) that `RiverBrain.load()` contains no schema/version check of any kind — it reads whatever keys happen to be present in the pickle (`data.get("model_task_stats", {})` with silent empty-dict fallback for missing keys, `data["classifiers"]` with a hard `KeyError` — caught by the surrounding broad `except Exception`, not a specific schema-mismatch error) — meaning a restored `river_brain.pkl` from a genuinely different, incompatible schema version would either silently lose the mismatched fields or trigger the same generic "starting fresh" fallback as outright corruption, with no distinguishing signal between the two. **No hash, checksum, or provenance marker was found on any of the 13 proposed artifacts in this pass** (UNKNOWN whether one exists internal to the FAISS binary or pickle structure without deeper, more invasive inspection this audit's safety scope doesn't require) — the mission's own central question ("how could we later establish the preserved artifact is the one that existed on the M5") remains genuinely open, exactly as the prior pass already disclosed. Not solved here.

## 12. Cold-Start Degradation Findings

**VERIFIED, via direct source read of `app/core/echo_model_orchestrator.py:1113-1148` — not inferred, not assumed:**

- **Missing `river_brain.pkl`**: `RiverBrain.load()` checks `os.path.exists()`, and if absent, logs `"[RIVER] No persisted brain found — starting fresh"` at **INFO** level and returns a freshly-constructed, unlearned `RiverBrain` instance. Startup does **not** fail.
- **Corrupt `river_brain.pkl`**: any exception during `pickle.load()` or the subsequent key access is caught by a broad `except Exception as e:`, logged as `"[RIVER] Brain load failed: {e} — starting fresh"` at **WARNING** level, and — identically to the missing-file case — silently falls back to a fresh instance. Startup does **not** fail here either.
- **No operator-visible alert distinct from an ordinary log line was found in this function** for either case — no exception propagates, no Liveness Ledger check was traced in this pass as specifically watching for "did RiverBrain just cold-start unexpectedly" (UNKNOWN whether one exists elsewhere; not traced further given this audit's scope).
- **Resulting behavior does differ from a healthy installation**, confirmed structurally: `observation_counts`, `model_task_stats`, `accuracy_trackers` all start empty, meaning `_select_council()`'s ranking logic (which reads directly from this state) would operate under cold-start/exploration-priority rules for every model, indistinguishable in its own logging from genuinely having never run before.

This fully reconfirms the prior archaeology's own "silently behaves differently" finding, now at **VERIFIED** confidence rather than the prior pass's DOCUMENTED-only status, because this pass traced the actual source rather than relying on `CLAUDE.md`'s narrative.

## 13. Adversarial Challenge

**Unnecessary members**: none found. All 13 proposed members independently re-justify their inclusion on direct re-evaluation (Sections 4-6).

**Missing members**: none found with the same confidence as the existing 13, but one candidate was surfaced and explicitly rejected rather than silently ignored — `memory/experiments/` (56MB, `learning/` and `preference_provenance/` subdirectories, per the prior pass's own Section 2 inventory, not further opened in this pass either, consistent with time/scope). This was considered for inclusion given its name suggests research value, but **excluded from the recommended set** pending the same open question the prior pass already flagged (Open Question 5): its actual contents were not inventoried in either pass, and adding an unexamined 56MB directory to a "minimal, defensible" set would violate the mission's own stated goal of finding the smallest defensible boundary, not the most inclusive one. Flagged for a future, narrower follow-up, not added here.

**Conditional members**: `dream_bridge.log` (Section 5) is the one item in the current 13 that this audit would downgrade from unconditional KEEP to **CONDITIONAL** — its size (80.2MB, the second-largest item in the whole set after `faiss.index`) is large relative to its likely unique-information density as a plain-text log rather than structured per-record JSONL, and unlike `council_deliberations.jsonl` it does not represent the *only* record of something otherwise permanently lost (dream-cycle synthesis text, per `CLAUDE.md`'s own documentation, is also written back into `memory_meta.json`/the FAISS index as `dream_v2`-tagged entries, meaning at least some of `dream_bridge.log`'s content may already be recoverable from the already-included FAISS pair). Recommend: **KEEP for this first preservation pass** (the overlap with FAISS content is not confirmed complete, and 80MB is not a large enough cost to justify excluding a file with any unique content), but flagged explicitly as the one item most worth re-examining in a future, more granular follow-up.

**Machine-specific members**: none of the 13 proposed members were found to be machine-specific in a way that would make restoring them elsewhere dangerous or useless — this is a real, positive finding for the set's actual portability (as distinct from `sync_state.json`, correctly excluded in Section 9, and as distinct from the *model-name* dependency noted in Section 4, which is a restoration precondition, not a reason to exclude the file itself).

**Integrity-critical companions**: none found beyond the already-identified `faiss.index`/`memory_meta.json` pairing (Section 4) — no additional small sidecar/index file was found alongside `faiss.index` at the top level of `memory/` in this pass.

## 14. Final Recommended Preservation Set

**Unchanged in composition from the prior archaeology's proposed 13 files.** The only change from this audit is the corrected exact size.

| Path | Exact size | Reason | Dependency | Sensitivity |
|---|---|---|---|---|
| `river_brain.pkl` | 4,049,550 B | Learned model-selection weights, no regeneration path | Model names (Ollama tags) must exist by the same name on restore | Low |
| `faiss.index` | 196,455,981 B | Vector index, entire searchable memory | Must be restored together with `memory_meta.json` | Low (binary vectors) |
| `memory_meta.json` | 96,411,247 B | UUID→text metadata for the index | Same as above | High — likely real conversational content |
| `self_model_claims.jsonl` | 7,364 B | Evidence-tiered claim history | None found | Low |
| `task_type_classifier.pkl` | 49,354 B | Online-learned classifier state | None found | Low |
| `drift_detectors.pkl` | 1,034 B | 5,000+ accumulated PageHinkley observations | None found | Low |
| `genesis/genesis_hash.txt` | 64 B | Tamper-detection hash anchor | None found | Low |
| `genesis/genesis_timestamp.txt` | 18 B | Write-once historical fact | None found | Low |
| `genesis/council_hash.txt` | 65 B | Tamper-detection hash anchor for `COUNCIL.md` | None found | Low |
| `interaction_log.jsonl` | 96,604,555 B | Raw historical substrate | None found | High — real conversational content |
| `reflection_journal.jsonl` | 13,140,560 B | Raw historical substrate + live dream-cycle input | None found | High — real reflection content |
| `reflection_shard.jsonl` | 6,383,735 B | Raw historical substrate | None found | High — likely real content |
| `council_deliberations.jsonl` | 42,825,089 B | Only record of pre-synthesis councillor opinions | None found | Moderate |
| `dream_bridge.log` | 80,160,762 B | Dream-cycle history, conditional per Section 13 | Possible partial overlap with FAISS `dream_v2` entries, unconfirmed | Moderate |

**Total: 536,089,378 bytes ≈ 511.2 MiB ≈ 536.1 MB (decimal) ≈ 0.50 GiB.**

**Comparison to the previous proposed set: composition unchanged, size corrected from ~600MB to the exact 536,089,378 bytes above** — an ≈11% reduction from the prior estimate, driven entirely by the prior pass's own block-rounded (`du`-style) size accounting rather than by any change in which files are recommended.

## 15. Disaster-Recovery Consequences

Under the stated scenario (M5 destroyed; Git + committed research survive; the Section 14 set survives off-machine; everything else under `memory/` is gone):

**FeralEcho would still know**: which models historically performed well on which task types (`river_brain.pkl`); its entire searchable conversational/reflection memory (`faiss.index`/`memory_meta.json`); its evidence-tiered self-knowledge claim history; its learned task-classification behavior and drift-detection baselines; the exact historical moment its constitutional hash-lock was first established; the full raw substrate of past interactions, reflections, and pre-synthesis council opinions.

**FeralEcho would permanently lose**: every operational log not in the Section 14 set (`echo_watchdog.log`, `SELF_EDIT.log`, `validator_audit.log`, etc. — real forensic value, per Category B, but not preserved under this minimal set); the Optuna hyperparameter-search history (`optuna.db`, cold-starts, but does not erase conclusions already reflected in `app/core/self_edit_generated.py`, which lives outside `memory/`); `echo_state_history.npy`'s rolling correlation baseline for seam-detection (a secondary/observational mechanism, per the prior pass); every informal same-machine backup copy in `snapshots/`/`backups/`/`archive/`/`history/` (irrelevant, since these were never independent protection to begin with — Section 8); and — genuinely unresolved either way — whether `christian_naturalist_reference.txt`, the sensor-signature files, and `behavioral_directives.json` (Open Question 2, inherited unresolved from the prior pass) represented anything irreplaceable, since this audit did not resolve that open question either.

## 16. Open Questions

1. (Inherited, unresolved) What do `christian_naturalist_reference.txt`, `touch_signature.json`/`vision_signature.json`/`hearing_signature.json`, and `behavioral_directives.json` actually contain — authored/calibrated state worth adding to a future preservation pass, or regenerable? Neither this audit nor its predecessor read them.
2. (Inherited, unresolved) How would a restored `memory/` be verified authentic versus an arbitrary substitute of the same shape? No mechanism found in either pass.
3. (New, this audit) Does `dream_bridge.log`'s content genuinely overlap with the `dream_v2`-tagged entries already present in `memory_meta.json`, and if substantially so, could `dream_bridge.log` be safely downgraded from the minimal set in a future, more granular pass? Flagged (Section 13) but not resolved here.
4. (New, this audit) Does any Liveness Ledger check exist that would notice and alert on an unexpected RiverBrain cold-start (Section 12), or is the INFO/WARNING log line genuinely the only operator-visible signal? Not traced in this pass.
5. (Inherited) What does `memory/experiments/` (56MB) actually contain? Considered and explicitly excluded from the recommended set (Section 13) pending this still-open question, not silently dropped.

## 17. Recommended Next Action

The corrected, exact 536,089,378-byte set in Section 14 is confirmed ready for a **separate, controlled off-machine-copy mission** — not performed here. That future mission should treat `dream_bridge.log`'s inclusion as provisional (Section 13) pending Open Question 3, and should not attempt to solve the restoration-coherence or authenticity-verification gaps (Sections 10-11) as part of a first copy — those remain real, disclosed, unresolved limitations of *this* preservation set's design, not blockers to performing the copy itself.

## 18. Repository Impact

- Path count before: 135. Path count after: 136 (this one new document).
- HEAD before: `2fba42644c82b9f7096276f4dd338d615cf1bcce`. HEAD after: unchanged.
- Nothing staged. Nothing committed. Nothing pushed.
- Confirmed: no file under `memory/` was modified, moved, copied, deleted, renamed, or had its mtime altered — every command used was read-only (`stat`, `ls -la`, `find`, direct source reads).
- Confirmed: no new hash, checksum, or backup-infrastructure file was created anywhere, inside or outside the repository.
- Confirmed: the live FeralEcho process (PID 7644) was checked only via read-only `ps`, never signaled, restarted, or otherwise touched.

---

### FINAL PRESERVATION-GATE VERDICT

**A — SET CONFIRMED.** The proposed preservation set survives this adversarial audit with its composition unchanged (all 13 members independently re-justified, no unnecessary or missing member found) and its size corrected to an exact 536,089,378 bytes. One item (`dream_bridge.log`) is flagged CONDITIONAL for a future, more granular pass, but is recommended KEEP for this first copy given its unconfirmed overlap with other preserved content. The set is ready for a separate, controlled off-machine-copy mission.

**Single safest next action after this audit**: a controlled, read-verified, off-machine copy of exactly the Section 14 file list (536,089,378 bytes) to at least one location physically independent of the M5 — performed as its own separate, explicitly-scoped mission, not as part of this audit.
