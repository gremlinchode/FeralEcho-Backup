# Full memory corpus inventory

Audit window for the counts below: `2026-11-10T05:20:06.095028+00:00` through `2026-11-10T05:20:20.907322+00:00`, unless a later clock is named. Evidence file: `measurements.json` in this directory. UUID correction and the `2026-11-10T05:22:42.971310+00:00` path stat: `measurements_supplement.json`.

The body of the original FULL MEMORY CORPUS AUDIT decree was not on disk in this session. Scope is the follow-up that named these four reports: inventory, verified counts, identity coverage, completeness reconciliation, and a snapshot procedure. Production stayed read-only. No model generation was spent. No process was signaled.

The ten-fact copy-only diagnostic is a separate laboratory store. It is named once below so this inventory does not omit it. Its retrieval result is not a property of the live corpus.

Evidence labels: OBSERVED (read back from a file or process listing), VERIFIED (a check with an independent arithmetic or source-and-runtime agreement), SUPPORTED (source plus a matching runtime fact, short of a process-memory proof), INFERRED, UNKNOWN, DISPROVEN.

## Question this inventory answers

Which durable stores hold Echo's memory, which process can write the live vector pair, and which files are neighboring stores that must not be counted as that pair.

## 1. Live vector generation

OBSERVED. Opened with `os.open` `O_RDONLY` and read to EOF. The path inode and size were the same before the open, on the opened descriptor, and after the read.

| File | Inode | Size | mtime (UTC) | SHA-256 |
|---|---:|---:|---|---|
| `/Users/richietate/Desktop/FeralEcho/memory/faiss.index` | 36671434 | 241904685 | `2026-11-10T05:14:05.468709+00:00` | `4abab200c591a6bf56264105d6170c855a539db001ff21e7262e5290b19945d6` |
| `/Users/richietate/Desktop/FeralEcho/memory/memory_meta.json` | 36671431 | 136497506 | `2026-11-10T05:14:05.392385+00:00` | `912b7b1e320d11f1f45c256b7eb97b20dd301be2ac6b317d919368413fddb2cc` |

VERIFIED header, without importing FAISS: fourcc `IxFI`, dimension 384 at offset 4, `ntotal` 157490 as a little-endian int64 at offset 8, and `(241904685 - 45) / 1536 = 157490`. Metadata key count on the same read is 157490. Every value is a dict. Every `text` field is a nonempty string. Repeated JSON keys: 0.

OBSERVED at `2026-11-10T05:27:23.776130+00:00`: the same two inodes, the same two sizes, and the same `mtime_ns` values (`1794287645468709385` and `1794287645392385325`). The bytes of this generation were hashed and counted. They were not retained as a copy.

### Identity sidecar

OBSERVED absent at the start of the read, at the end of the read, at `2026-11-10T05:22:42Z`, and at `2026-11-10T05:27:23Z`:

`/Users/richietate/Desktop/FeralEcho/memory/faiss.index.identity.json`

The three temp siblings were also absent at those times: `faiss.index.tmp`, `memory_meta.json.tmp`, `faiss.index.identity.json.tmp`.

VERIFIED from `app/lib/vector_memory.py` `_persist` (read this session, lines 342–411): each of metadata, index, and sidecar is written to a temp path and published with `os.replace`. The three replacements are not one transaction. The sidecar is written only when `_identity_authoritative` is true and the index write happened. The metadata step's own comment states that key order is not vector identity. Equal key count and `ntotal` is necessary for a count-aligned generation. It does not record which metadata id sits in which FAISS row.

### Who writes it

VERIFIED in source this session:

- `app/core/memory_bridge.py` lines 58–66 set `VECTOR_INDEX_PATH` and `VECTOR_META_PATH` under `config.MEMORY_DIR` and construct `VectorMemory(dim=384)` on those two paths.
- `run.py` lines 261 and 299–301 import that module and log that the shared VectorMemory is ready.
- `echo_studio/` contains no reference to `VectorMemory`, `memory_bridge`, or `faiss`.

OBSERVED at report time: pid 65139, command `python -u run.py`, stat `R+`, elapsed `06-10:25:28`. `memory/echo_server.pid` contains `65139`. `memory/echo_sentinel.json` stage is `serving`, pid 65139, start `2026-11-03T19:02:01.305169Z`, heartbeat `2026-11-10T05:26:55.113302Z`. The index mtime falls inside that uptime.

SUPPORTED: that process is the live writer of this pair. This audit did not attach to its file table, so an open descriptor inside the process was not re-proven. Echo Studio pid 86938 (`python -m echo_studio.main`, stat `S+`) is a separate process and is not a VectorMemory constructor in the `echo_studio` tree.

Other constructors exist and are not this generation:

- `terminal_client.py` line 102 and `thunderhead.py` line 222 construct `VectorMemory` on the default `memory/` paths. This audit did not observe either script as a running process.
- `app/core/self_heal.py` can construct `VectorMemory`. Whether the running server imports it was not re-tested. UNKNOWN.
- `archive_janitor/echo_full_throttle_rite.py` constructs `VectorMemory` on `data/faiss.index`. That is the legacy store in section 3.

### What the live metadata contains

Counts are from the opened inode 36671431. They describe record fields. They do not describe FAISS row order.

| `memory_source` | Records |
|---|---:|
| `code_analysis` | 60702 |
| `autonomous` | 59103 |
| missing | 23716 |
| `user_conversation` | 7481 |
| `sync_air` | 3036 |
| `claude_research` | 1542 |
| `environment` | 1350 |
| `self_model_reflection` | 325 |
| `tool_manager` | 225 |
| `dream_v2` | 10 |
| Total | 157490 |

| `role` | Records |
|---|---:|
| `code_analysis` | 60702 |
| `fetch` | 28702 |
| missing | 24962 |
| `dream` | 24137 |
| `echo` | 5640 |
| `harmony` | 4790 |
| `sync` | 2785 |
| `user` | 1809 |
| `research` | 1391 |
| `environment` | 1350 |
| `sandbox_run` | 388 |
| `self_model_reflection` | 325 |
| `experiment` | 282 |
| `tool_error` | 225 |
| `sandbox_failure` | 1 |
| `synthesis` | 1 |
| Total | 157490 |

VERIFIED in source: `retrieve_relevant_memories` drops a hit whose `role` or `memory_source` is in `_ALWAYS_EXCLUDED_MEMORY_CATEGORIES` (`app/core/memory_bridge.py` lines 55 and 476–477), which is `code_analysis` and `self_model_reflection`. Those categories are present in this generation. The distinct count removed by that filter was not computed. UNKNOWN. The marginal source counts are 60702 and 325.

Direct readers of `memory/memory_meta.json`, VERIFIED by source this session, bypass FAISS search:

- `app/routes_echo_studio.py` lines 606 and 707
- `app/autonomous_awareness.py` line 241
- `app/emergent_scheduler.py` line 631

Inner-meta keys present on the live generation, as a presence count rather than a second corpus: `timestamp` 157458, `role` 132528, `memory_source` 133774, `validation_warning` 21139, `type` 20400, `prompt` 19767, `source` 19767, `retention` 7468, `task_type` 7468, `backfill` 3791, `sync_ts` 3036, `is_thought_provoking` 1809, `migration_ts` 231, `migrated_from_legacy_self_model_tag` 212, `migrated_from_legacy_backfill_burst` 19, `seed_ids` 10. Timestamp minimum `2026-07-02T21:40:53.854995+00:00`. Timestamp maximum `2026-11-10T05:14:03.470526+00:00`. Missing timestamps: 32. `validation_warning` true: 21139.

First key `762209c7-677f-4b35-bb68-7473855afaa1`. Last key `a7881d80-0a80-4989-b423-6bc82e3fa50b`.

Record-field identity, from a second `O_RDONLY` read of the same inode and size at `2026-11-10T05:22:42.971310+00:00`: 157490 keys, 157490 lowercase hyphenated UUID keys, 0 other. The `uuid_shaped_keys: 0` field inside `measurements.json` is invalid. The checker required hyphens to be hexadecimal. That field is not the count.

Unique nonempty text SHA-256 values: 58652. Duplicate-text groups: 3121, covering 101959 records. Singletons: 55531. Check: `55531 + 101959 = 157490` and `55531 + 3121 = 58652`.

## 2. November 2 certified freeze

A separate store. It is not the live generation.

| File | Inode | Size | mtime (UTC) | SHA-256 |
|---|---:|---:|---|---|
| `.../suffix-recovery-20261102/store/faiss.index` | 34029978 | 233315373 | `2026-11-02T03:51:45.506534+00:00` | `0dc600d738c77458883d60f14ef0d43c8ae2845609506ed3d50b06857427a2d8` |
| `.../suffix-recovery-20261102/store/memory_meta.json` | 34029977 | 130779333 | `2026-11-02T03:51:45.462247+00:00` | `813209d9b0868d85e288233c973955879dbcefb92bc9e07d7df903dc05203bc4` |
| sidecar `faiss.index.identity.json` | present | 6683724 | — | `c9e293edeed42233f59db395aec81a3857ff9e63f1aec4eac379095c5a7c3fb7` |

Full directory: `/Users/richietate/Desktop/FeralEcho-offline-recovery-20261026/suffix-recovery-20261102/store/`.

VERIFIED: dimension 384, `ntotal` 151898, size arithmetic matches, metadata keys 151898, schema-1 sidecar, `id_order` length 151898 and unique 151898, sidecar `index_sha256` equals the index file, binding `34332e14095cc9c3b40d9ff7ef6c9138ecbaaa626a94dea662d33869f12e6ea0`. All 151898 texts nonempty. Unique texts 55655. Duplicate groups 2660 covering 98903 records. `memory_source` missing 23716. `role` missing 23819. Timestamp missing 32. Timestamp maximum `2026-11-02T03:45:59.414560+00:00`. `validation_warning` true 21129. Path inode did not change during the read.

Live minus this freeze is 5592 records (`157490 - 151898`). Largest source growth is `autonomous` +5048. Largest role growth is `fetch` +3546. The untagged `memory_source` count stayed 23716. `dream` role stayed 24137. `dream_v2` stayed 10.

This freeze is 5592 records behind the measured live generation. It was not installed.

## 3. Legacy `data/` store

A different vector space. OBSERVED mtime `2026-05-15T18:39:52Z` on both files. No sidecar.

| File | Inode | Size | SHA-256 |
|---|---:|---:|---|
| `/Users/richietate/Desktop/FeralEcho/data/faiss.index` | 635187 | 10952749 | `65903b32b3a5a5353f3f92253e0ee39ff0e825910e2025ac8631282e5b9b5863` |
| `/Users/richietate/Desktop/FeralEcho/data/memory_meta.json` | 635189 | 6587816 | `7c6c2d7ddd69957f0a4a234e07f0f944bcc1620e8c5c092694534c98b03584de` |

Header fourcc `IxFI`, dimension 512, `ntotal` 5348. The measurement parser flags dimension 512 as unexpected because it only accepts dimension 384. Separate arithmetic: stride 2048, `(10952749 - 45) / 2048 = 5348`. VERIFIED. Metadata keys 5348. All texts nonempty. Unique texts 5245. Duplicate groups 8 covering 111 records. Inner meta on the profile is empty: `memory_source`, `role`, and `timestamp` missing on all 5348. First key `761eb950-44b5-419d-9714-df87f4eea805`. Last key `23ca49b6-7dc4-42eb-9a69-508151183432`.

Same sizes exist beside them as `faiss.index.tfidf_archive` and `memory_meta.json.tfidf_archive`. Those twins were stat-listed. They were not parsed.

`data/question_garden.jsonl` is a question store, not this vector space. See section 6.

`data/codebase.db` (3428352 bytes) and `data/codebase_map.json` (3442356 bytes) are cartographer files. They are not Echo conversational memory. `data/self_model.txt` is 1608 bytes. `data/symbiote_location.json` is 87 bytes. `data/bible_art/` holds 1 file, 9150 bytes.

## 4. Laboratory rebuilt store

Reference only. Directory: `/Users/richietate/Desktop/FeralEcho-voyager/voyager_lab/memory_retrieval_diagnostic_2026-11/rebuilt/`. This audit did not rebuild it and did not search it.

| File | Inode | Size | SHA-256 |
|---|---:|---:|---|
| `rebuilt/faiss.index` | 36652234 | 241843245 | `887a9fa7871ad3ccb880dbc2acc63235fbf5c451a801f8758eb1241ea029506f` |
| `rebuilt/memory_meta.json` | 36652231 | 136449185 | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` |
| sidecar | 36652235 | 6928012 | `6e68bf3062b6d0824b571d912464aae6f064198f493d7fb6afe5e83425b60baa` |

VERIFIED on this read: dimension 384, `ntotal` 157450, size arithmetic matches, metadata keys 157450, schema 1, `id_order` 157450 unique, sidecar index hash equals the index file, binding `a3c64a5a04ebd0dd983bc49f1f18a933dc4bb2073abbd8b06dbd0aa0119751cc`. Timestamp maximum `2026-11-10T03:36:28.248800+00:00`. Last key `1d4548ef-174e-4f78-ad3f-e521f92c7d29`.

This store is 40 records behind the measured live generation (`157490 - 157450`). Its index hash is a different file from inode 36671434. It was not installed over `memory/faiss.index`.

## 5. Journals and operational logs under `memory/`

These are memory-related stores. Their line counts are not `ntotal`. Each count is an `O_RDONLY` read of one inode. The path did not change during that count.

| File | Inode | Lines | Size |
|---|---:|---:|---:|
| `memory/dream_bridge.log` | 635312 | 559978 | 90719577 |
| `memory/quarantine_journal.jsonl` | 635321 | 49288 | 36471226 |
| `memory/workspace_log.jsonl` | 5643390 | 26101 | 8602401 |
| `memory/seam_log.jsonl` | 5788897 | 17557 | 2355742 |
| `memory/reflection_shard.jsonl` | 635390 | 12899 | 56840766 |
| `memory/reflection_journal.jsonl` | 635322 | 12060 | 15989286 |
| `memory/memory_journal.log` | 635318 | 5487 | 754586 |
| `memory/interaction_log.jsonl` | 635315 | 4375 | 26525701 |
| `memory/council_deliberations.jsonl` | 5912817 | 3527 | 35764322 |
| `memory/consolidation_log.jsonl` | 3440956 | 3277 | 512671 |
| `memory/sync_seen.jsonl` | 36671840 | 3049 | 198184 |
| `memory/echo_messages.jsonl` | 6107762 | 2371 | 5453279 |
| `memory/learning_events.jsonl` | 635316 | 919 | 2566698 |
| `memory/council_ratings.jsonl` | 8099206 | 227 | 133260 |
| `memory/self_edit_outcomes.jsonl` | 25252083 | 194 | 98014 |
| `memory/working_self.jsonl` | 36638027 | 150 | 170039 |
| `memory/memory_journal_active.log` | 635317 | 0 | 0 |

`interaction_log.jsonl.1.gz` is 13740841 bytes. The live interaction log is a rotated file. Its 4375 lines are not the lifetime history. Overlap with the 7481 `user_conversation` vector records is UNKNOWN.

`dream_bridge.log` has 559978 lines. The live vector role `dream` has 24137 records. Those two numbers measure different things.

Stat-only top-level `memory/` listing: 120 files. Large neighbors that were not line-counted: `SELF_EDIT_MASTERY_.log` 105121335; two September 2 metadata backups, `memory_meta_backup_before_backfill_migration_20260902T075543Z.json` 89172395 (inode 16008675) and `memory_meta_backup_before_reflection_migration_20260902T050420Z.json` 89031859 (inode 15896023); `reflection_shard.jsonl.pre_pending_cleanup` 53157632; `SELF_EDIT.log` 35963617; `synthesis_integrity_log.jsonl` 32647301; `validator_audit.log` 28023675; `optuna.db` 14151680; `self_edit_attempt_ledger.jsonl` 5858472; several `.1.gz` rotations; `scripture_warnings.log` 3353853; `scheduler_selections.log` 4305837.

Subdirectories, stat only:

| Directory | Files | Bytes |
|---|---:|---:|
| `memory/archive` | 144 | 77713074 |
| `memory/backups` | 4 | 100486846 |
| `memory/experiments` | 1001 | 81259438 |
| `memory/snapshots` | 40 | 28683882 |
| `memory/history` | 69 | 728340 |
| `memory/stillness` | 1 | 377117 |
| `memory/skill_ledger` | 5 | 26356 |
| `memory/genesis` | 3 | 147 |
| `memory/behavioral_directives_backups` | 1 | 621 |
| `memory/models` | 0 | 0 |
| `memory/test` | 0 | 0 |

`memory/snapshots/` is the health-snapshot directory from `snapshot_manager.py`. Its artifact list, lines 68–80, is `self_edit_generated.py`, `memory/river_brain.pkl`, `echo_principles.json`, `memory/genesis/genesis_hash.txt`, `Modelfile`, `COUNCIL.md`, and `memory/genesis/council_hash.txt`. It does not copy `faiss.index` or `memory_meta.json`. Those 40 files are not a vector-corpus snapshot.

### Provenance logs

`memory/retrieval_provenance.jsonl`: inode 16465627, 688 JSON lines, 462274 bytes, path unchanged during the count. Keys on every line: `candidates_considered`, `memories_injected`, `query_preview`, `source`, `timestamp`, `trace_id`. Last timestamp `2026-11-10T03:34:06.234790`. Last source `memory_bridge`.

The measurement script's `no_recognized_candidate_field: 688` is a probe defect. It looked for list fields with other names. `candidates_considered` is an integer. The supplement recount of the same file is the count to use: 446 lines with a positive `candidates_considered`, 242 with zero, 0 file-order time inversions. Last positive timestamp `2026-10-28T04:04:29.156643` (15 considered, 5 injected). Records after that: 241, all with zero candidates and an empty injected list. First timestamp after that positive: `2026-10-29T02:21:39.525310`. Lines with candidates positive and injected list empty: 11. Lines with injected nonempty and candidates zero: 0.

`memory/search_provenance.jsonl` is a different log. Inode 30805598, 2796 JSON lines, 947032 bytes. Keys: `injected_count`, `injected_preview`, `retrieval_key`, `source_url`, `timestamp`. Last timestamp `2026-11-10T04:18:47.167712+00:00`. A later `O_RDONLY` recount of that same inode and size found `injected_count > 0` on all 2796 lines and zero zeros. The measurement script's `no_recognized_candidate_field: 2796` is the same probe defect. This log does not record vector-search candidate ids.

### Model and state files that are not the vector corpus

`memory/river_brain.pkl` inode 3941690, 5849776 bytes, plus older backups (`pre_ablation`, `pre_reset`, `pre_coding_reset`, `zeroed_backup`) and `river_brain.pkl.restore_tmp` inode 3941703, 332467 bytes. `river_brain.pkl.lock` is 0 bytes. These are RiverBrain state. They are not FAISS rows.

`memory/echo_sentinel.json` at directory-inventory time was inode 36673540, 163 bytes. At `2026-11-10T05:27:23Z` it was inode 36676292, still 163 bytes, with a newer heartbeat. The sentinel is being replaced while the vector pair's inodes stay put. `memory/echo_server.pid` inode 34791308, contents `65139`.

## 6. Question garden

`/Users/richietate/Desktop/FeralEcho/data/question_garden.jsonl`, inode 5867121, 23562 lines, 15921080 bytes, 0 JSON failures. Status `active` 23535, `composted` 27. Every line has `question`, `source`, `status`, `category`, and lineage fields. Last source field value `echo`. Overlap between garden rows and FAISS ids was not joined. UNKNOWN.

## 7. Echo Studio database

Separate store. OBSERVED via SQLite URI `file:~/.echo_studio/echo_studio.db?mode=ro` with `PRAGMA query_only=ON`.

Inode 4441411, size 4923392, path `/Users/richietate/.echo_studio/echo_studio.db`.

| Table | `COUNT(*)` |
|---|---:|
| `conversations` | 91 |
| `messages` | 3284 |
| `drafts` | 87 |
| `saved_prompts` | 0 |
| `recent_files` | 0 |
| `sqlite_sequence` | 1 |

Overlap with FAISS ids is UNKNOWN. Pid 86938 was still `python -m echo_studio.main` at `2026-11-10T05:27:23Z`. It was not stopped.

## 8. Retention that can drop history without dropping the vector pair

VERIFIED in `app/maintenance/night_cycle.py` lines 24–41. Caps include `interaction_log.jsonl`, `dream_bridge.log`, `reflection_shard.jsonl`, `reflection_journal.jsonl`, `echo_watchdog.log`, and `SELF_EDIT_MASTERY_.log` at 100MB; `quarantine_journal.jsonl`, `validator_audit.log`, and `council_deliberations.jsonl` at 50MB; `scripture_warnings.log` at 10MB. The comment above that tuple excludes `SELF_EDIT.log` from rotation because startup replays it. Echo state archives of `echo_state_history.npy` and `salience_state.json` go to `memory/history/` on a 24-hour cadence, capped at 30 generations (lines 50–56). None of these caps is a vector-index retention policy.

## What this inventory does not claim

The live index and the live metadata have the same count on one opened generation. Row identity for that index is UNKNOWN. Search behavior of the running server was not exercised. No file in production was modified.
