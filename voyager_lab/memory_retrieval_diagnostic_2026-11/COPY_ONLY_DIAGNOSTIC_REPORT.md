# Copy-only memory retrieval diagnostic

**Date:** 2026-11-09  
**Authorization:** Execution decree, copy-only diagnostic. Section 14 of `voyager_lab/memory_retrieval_forensics_2026-11/FERALECHO_MEMORY_RETRIEVAL_FORENSIC_REPORT.md`.  
**Worktree:** `/Users/richietate/Desktop/FeralEcho-voyager`  
**HEAD before and after:** `dc8d6eb9b6479ef323614cd6820bb050a14299eb` (`project-voyager`)  
**Generation count:** 0. The two unused evidence-to-answer generations were not spent.  
**Outcome on the isolated rebuilt store:** PASS

This diagnostic tested one gate on one isolated copy of ten known facts. It does not repair Echo's live memory. It does not measure delayed recall. It does not measure semantic understanding.

## Executive summary

The November 2, 2026 certified index is not a pure byte prefix of the cloned live index. The first mismatch is at byte offset 8, the FAISS `ntotal` field. That result selected the section 14 re-embed branch. A failed prefix check is a completed diagnostic measurement.

The cloned metadata (157,450 records) was embedded into a new empty `VectorMemory`. Neither an index nor a sidecar existed when that store was created, so the library's own persist wrote `faiss.index` and `faiss.index.identity.json` together. Declared insertion order is the JSON key order of the clone. That order is the new store's row order. It is not a claim about the live index's historical row order.

A second process loaded only the rebuilt store. The existing classifier reported `identity_status=manifest_valid` and `identity_verified=True`. The recomputed index digest matched the sidecar. The recomputed binding digest matched the sidecar. The refusal path did not fire. The gate was not edited.

For each of the ten original user ids, `VectorMemory.search` returned that id at raw rank 2 for that item's Phase Two question. The real `retrieve_memory_context` 30-minute filter and k=5 cut, with the clock frozen inside the diagnostic process to that item's Phase Two `started_at`, placed that row's section 3 hash in the simulated injected list. All ten facts are **demonstrated**. Failed: 0. Could not be tested: 0.

The live sidecar `memory/faiss.index.identity.json` was absent at the clone, during the re-embed, during the search, and at report time. PID 65139 (`python -u run.py`) was not signaled. Live index and metadata bytes grew during and after the diagnostic because that process persisted on its own. This diagnostic opened those paths for stat only.

## Exact procedure performed

Section 14 was followed. No step was redesigned.

1. **Copy.** `memory/faiss.index` and `memory/memory_meta.json` were cloned into `copy_live/`. The listener was not opened against those files. `add()` was not called on the live store. No sidecar was written beside the live index. The clone is one generation: index `ntotal` 157,450 and metadata length 157,450. Index size 241,843,245 bytes. Metadata size 136,449,185 bytes. The clone has no sidecar, matching the live store at copy time.
2. **Listener.** PID 65139 was left running. It was not signaled. It was not restarted.
3. **Byte-prefix check.** The certified file `/Users/richietate/Desktop/FeralEcho-offline-recovery-20261026/suffix-recovery-20261102/store/faiss.index` was re-hashed, then compared as a literal byte prefix of `copy_live/faiss.index`. A header-adjusted payload comparison was not treated as a pass. Result: not a pure prefix. First mismatch at offset 8. Copy header `ntotal` is little-endian `0a 67 02 00` = 157,450. Certified header `ntotal` is little-endian `5a 51 02 00` = 151,898. Copy size arithmetic: `(241843245 - 45) / 1536 = 157450`. Certified size arithmetic: `(233315373 - 45) / 1536 = 151898`. Both files are IndexFlatIP, dimension 384. Recorded in `prefix_check.json`.
4. **Suffix path.** Not taken. `meta.keys()` was not stamped onto the cloned index. No suffix sidecar was built.
5. **Re-embed.** `reembed_copy.py` created an empty `VectorMemory` under `rebuilt/`. It encoded the cloned texts with `SentenceTransformer("all-MiniLM-L6-v2").encode(..., normalize_embeddings=True)` through `app.core.sentence_transformer_singleton`, in batches of 64, in JSON key order. One `add()` wrote the index and the schema-1 sidecar together. Encode time 564.031 seconds. Exit 0. Log line: `ADD_DONE persisted=True ntotal=157450 meta=157450 status=manifest_valid verified=True authoritative=True`, then `REEMBED_DONE`. The in-process flag is recorded and is not the official gate result. `app.core.memory_bridge` was not imported.
6. **Fresh-process load.** `search_copy.py` is a separate process. It loaded only `rebuilt/`. Log line: `[VectorMemory] identity_status=manifest_valid verified=True`, then `IDENTITY status=manifest_valid verified=True binding_ok=True`. `search_refused` is empty. The live index was not loaded into PID 65139.
7. **Ten searches.** For each Phase Two question, the script called real `VectorMemory.search` at k=15 (the `k * 3` argument `retrieve_memory_context` passes when k=5), then real `retrieve_memory_context` with `conversation_service.datetime` frozen, inside that process only, to the item's `results_phase2.jsonl` `started_at`. No workspace bias. No POST. No answer text collected. A hit counted as the expected user id only when the hit text had one unique owner, that owner was the expected user id, and the SHA-1 12-hex prefix matched section 3.
8. **Stop.** Reports written. No cutover. No second re-embed. No further search.

Environment set before native imports: `KMP_DUPLICATE_LIB_OK=TRUE`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `TOKENIZERS_PARALLELISM=false`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. Interpreter: `/Users/richietate/miniforge3/envs/feral_echo/bin/python`.

## Identity source and verification

| Question | Result |
|---|---|
| 1. Exact source of vector-to-user-id identity | The cloned `memory_meta.json` texts, re-embedded by this process and inserted in `json.load` key order into a new empty `VectorMemory`. The sidecar was written by `VectorMemory._persist` because `_identity_authoritative` was true (neither file existed at init). |
| 2. Does that source independently bind the index vectors to the ten original user ids? | On the **rebuilt** index, yes. Each of the ten user ids is a key in the cloned metadata. Stored text equals that item's `phase1_prompt`. Stored SHA-1 prefix equals the section 3 hash. Each id sits in the new sidecar `id_order` at a position below `ntotal`. The sidecar does not certify row identity of the **cloned live index**. The prefix proof failed, so the November 2 freeze is not the identity source. |
| 3. Does the sidecar accurately represent the copied index? | It represents `rebuilt/faiss.index`. `index_sha256` equals that file (`887a9fa7871ad3ccb880dbc2acc63235fbf5c451a801f8758eb1241ea029506f`). It does not equal `copy_live/faiss.index` (`3e09ad48029e35d153fdd38218cf98e63aeb6c1a92d8b2d0b17544e583e513fa`). `rebuilt/memory_meta.json` has the same digest as the clone, so the records were not rewritten into different text. |
| 4. Did binding and hash verification succeed? | Yes, in the fresh process. Schema 1. `id_order` length 157,450. `ntotal` 157,450. `index_hash_matches_sidecar` true. `binding_sha256_matches` true. Sidecar `binding_sha256` is `a3c64a5a04ebd0dd983bc49f1f18a933dc4bb2073abbd8b06dbd0aa0119751cc`. |
| 5. Did the store pass the existing identity gate without weakening it? | The rebuilt store did. Classifier and binding layout were not edited. `gate_weakened` is false. `copy_live/` still has no sidecar and was not loaded into `search`. The unverified clone was not forced through the gate. |

`declared_order_is_old_faiss_row_order` is false in `rebuild_result.json`.

The certified file's historical digest `8616b11551352502deea15eb0648e902f63df6fb33e4c8ba31b616b74ce8639c` does not match the re-hash `0dc600d738c77458883d60f14ef0d43c8ae2845609506ed3d50b06857427a2d8`. The on-disk certified sidecar's own `index_sha256` equals the re-hash. The freeze file and its sidecar agree with each other. They are not a prefix of this clone, and they were not installed.

## Before and after state of the isolated copy

**Before (the clone, and still the clone).**

| File | Bytes | SHA-256 | Sidecar |
|---|---:|---|---|
| `copy_live/faiss.index` | 241,843,245 | `3e09ad48029e35d153fdd38218cf98e63aeb6c1a92d8b2d0b17544e583e513fa` | absent |
| `copy_live/memory_meta.json` | 136,449,185 | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` | absent |

`ntotal` 157,450 equals metadata length. All ten user ids are present, with section 3 hashes. These two files were not modified after the clone.

**After (new store beside the clone).**

| File | Bytes | SHA-256 |
|---|---:|---|
| `rebuilt/faiss.index` | 241,843,245 | `887a9fa7871ad3ccb880dbc2acc63235fbf5c451a801f8758eb1241ea029506f` |
| `rebuilt/memory_meta.json` | 136,449,185 | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` |
| `rebuilt/faiss.index.identity.json` | 6,928,012 | `6e68bf3062b6d0824b571d912464aae6f064198f493d7fb6afe5e83425b60baa` |

Same vector count and same metadata digest. Different index digest. Sidecar present and accepted by a fresh process.

## Results for the ten facts

Clock rule: each row uses that item's Phase Two `started_at`. Search k=15. Injection uses the real filter and k=5. Raw rank 2 is the user fact on every item. Raw rank 1 is a different `user_conversation` row whose timestamp falls inside the Phase Two window, after the frozen clock's 30-minute cutoff, so the real filter removes it. The rank-1 12-hex prefix is absent from that item's injected list. The user-row prefix is present.

`stored_text_equals_phase1_prompt` is true for all ten. `ambiguous_hit` is false for all ten. `except_path_swallowed` is false for all ten. Identity validation is the one fresh-process `manifest_valid` result, applied to every row.

| Item | User id | Identity valid | Correct user id returned | Rank | Record matches | Section 3 hash in simulated context | Injected hashes | Result |
|---|---|---|---|---:|---|---|---|---|
| 01 | `5e6ac8a9-19c1-4fcd-b08e-dd7c0f5e659b` | yes | yes | 2 | yes | yes (`5aeece192c0e`) | 5; candidates after filter 11 | demonstrated |
| 02 | `aded2053-b5d9-42d5-a106-aa3773f60ea5` | yes | yes | 2 | yes | yes (`f6e677371d0d`) | 5; candidates 10 | demonstrated |
| 03 | `36495cc5-39f3-4a31-a79b-332dc52da1ae` | yes | yes | 2 | yes | yes (`254ada88570e`) | 2; candidates 14 | demonstrated |
| 04 | `90e3838a-c12d-4a28-a653-b5de13471e0e` | yes | yes | 2 | yes | yes (`e71037e8fcdc`) | 4; candidates 10 | demonstrated |
| 05 | `accc4c1e-ef05-466f-8ef2-4f1b997166f8` | yes | yes | 2 | yes | yes (`02d0c62ade8b`) | 5; candidates 12 | demonstrated |
| 06 | `c86b2d32-5438-4c52-b7ae-df291cca4db2` | yes | yes | 2 | yes | yes (`31bc63a1affe`) | 5; candidates 7 | demonstrated |
| 07 | `2dd6c6ec-1afe-47e6-9739-883eb12efc98` | yes | yes | 2 | yes | yes (`3c63d277f342`) | 5; candidates 12 | demonstrated |
| 08 | `1f366a17-832a-4eb0-a5e4-0458f1d85fde` | yes | yes | 2 | yes | yes (`4ba1c6a1d6a0`) | 4; candidates 12 | demonstrated |
| 09 | `0192ec01-8404-4f02-a2ce-c8dc4c53f848` | yes | yes | 2 | yes | yes (`72040f561398`) | 5; candidates 14 | demonstrated |
| 10 | `dd44ed20-1acb-4951-8335-33437b6947d3` | yes | yes | 2 | yes | yes (`479cfd462810`) | 5; candidates 8 | demonstrated |

New-store `id_order` positions (declared insertion rows of the rebuilt index): 01 `157206`, 02 `157208`, 03 `157210`, 04 `157212`, 05 `157214`, 06 `157216`, 07 `157217`, 08 `157218`, 09 `157222`, 10 `157224`. All are below `ntotal` 157,450.

Item 03's injected list is the user hash `254ada88570e` and then the echo-row hash `4ae0ccf0ce68`. The echo row `67eccddb-cb98-4373-b206-aceed4712b62` is present, its hash matches section 3, and it appears in item 03's raw hits. It was not used as a substitute for the user row. Its text is the short echo string, not the phase-1 prompt. The shorter injected list is the real selector's output (`user_conversation[:k]` only when at least k such rows remain; otherwise `non_autonomous[:k]`). The user hash is in the list, so the injection stage passes.

Phase Two clocks:

| Item | `started_at` |
|---|---|
| 01 | `2026-11-09T22:33:34.219739+00:00` |
| 02 | `2026-11-09T22:33:56.253537+00:00` |
| 03 | `2026-11-09T22:34:06.063856+00:00` |
| 04 | `2026-11-09T22:35:18.905815+00:00` |
| 05 | `2026-11-09T22:35:39.848652+00:00` |
| 06 | `2026-11-09T22:35:43.859088+00:00` |
| 07 | `2026-11-09T22:35:49.141442+00:00` |
| 08 | `2026-11-09T22:35:52.735741+00:00` |
| 09 | `2026-11-09T22:35:56.723764+00:00` |
| 10 | `2026-11-09T22:36:01.448165+00:00` |

## Stage-by-stage counts

Stages are kept separate. Ten facts entered each stage. Zero failed. Zero could not be tested.

| Stage | Success | Failure | Not tested |
|---|---:|---:|---:|
| STORAGE (row in the cloned metadata; text equals the phase-1 prompt; section 3 hash matches) | 10 | 0 | 0 |
| IDENTITY VALIDATION (fresh-process `manifest_valid`, binding match, gate unchanged) | 10 | 0 | 0 |
| INDEX SEARCH (`index.search` reached; correct user id returned) | 10 | 0 | 0 |
| CANDIDATE RETURN (unique owner, record matches, survives the real 30-minute filter) | 10 | 0 | 0 |
| CONTEXT INJECTION (section 3 hash present in the simulated injected list) | 10 | 0 | 0 |

Section 14's eight measurements, same evidence:

| Measurement | Count |
|---|---|
| 1. Persistence | 10/10 |
| 2. Index membership in the rebuilt sidecar, position < `ntotal` | 10/10 |
| 3. Search invocation (`identity_verified` true; refusal log empty) | 10/10 |
| 4. Candidate discovery | 10/10 |
| 5. Rank | 2 for all ten |
| 6. Acceptance after the real filter and k=5 | 10/10 |
| 7. Context inclusion | 10/10 |
| 8. Final answer accuracy | not measured |

## Controls

- Known-good storage: the ten user rows and section 3 hashes above.
- Known-good identity: fresh-process `manifest_valid` before any query was scored.
- Known-good query: the Phase Two question text, embedded with the same normalized MiniLM encode the server uses. `memory_bridge.embed_text` was not imported. The call shape matches that function.
- Negative control: the string `feralecho-copy-diagnostic-nonce-9f3c1a this string is not a stored memory` is absent from metadata. Its 15 neighbors were not reported as any of the ten successes (`nonce_neighbors_reported_as_ten_successes` false).
- Other stored string: id `762209c7-677f-4b35-bb68-7473855afaa1`, hash `3a69e3e19f9a`, unique text, not one of the ten. A query of its own text returned that same id.
- Item 03 echo row: recorded, not substituted.

## Errors and limitations

- The prefix check failed at byte 8. The re-embed branch is the authorized consequence. The November 2 freeze was not used as an identity source and was not installed.
- The historical certified digest in the earlier recovery note does not match the file now on disk. The file matches its own sidecar. This diagnostic re-hashed the file and used that measurement.
- The sidecar binds the rebuilt index. Live FAISS row membership for these ten ids remains unknown. Counts matching on the clone (`ntotal` equals metadata length) do not identify which vector is which id.
- `live_unchanged_during_reembed` is false. At re-embed start the live index was inode 36642366, size 241,844,781, and the live metadata was inode 36642365, size 136,452,441. At re-embed end both had been replaced by the listener: index inode 36650760, size 241,846,317; metadata inode 36650687, size 136,455,510. Sidecar still absent. `live_stat_changed_during_search` is false; the search window stayed on that post-re-embed generation.
- A later stat, taken while writing this report, shows a further listener persist: live index inode 36652781, size 241,847,853, mtime 1794282983; live metadata inode 36652780, size 136,458,687, mtime 1794282983. Sidecar still absent. PID 65139 still `python -u run.py` (elapsed `06-08:56:07` at that stat). Those writes are the server's own persists. This diagnostic's `production_paths_opened_for_write` flag is false.
- The 12-hex provenance hash is 48 bits. Identification also required the full stored text to equal the phase-1 prompt and the unique-owner check.
- Item 03 and item 04 and item 08 injected fewer than five hashes. The required user hash is present in each list. The selector was not retuned.
- Answer text was not collected. Utilization was not scored.
- `copy_live/` remains an unverified snapshot. Search ran against `rebuilt/` only.

## Production integrity

Production code, configuration, live index, live metadata, and live identity metadata were not modified by this diagnostic.

- No edit under `/Users/richietate/Desktop/FeralEcho` for this task.
- No sidecar created at `memory/faiss.index.identity.json`. It is still absent.
- PID 65139 was not signaled and was not restarted.
- No POST. No model generation. The two remaining generations were not consumed.
- `app/lib/vector_memory.py` was not edited. The identity refusal was not disabled and was not bypassed.
- `meta.keys()` was not treated as the live index's vector identity.
- The November 2 freeze was not installed over live memory.
- Voyager HEAD is unchanged: `dc8d6eb9b6479ef323614cd6820bb050a14299eb`.
- Nothing from `rebuilt/` or `copy_live/` was copied onto the live paths.

## SHA-256 of diagnostic artifacts

| Artifact | SHA-256 |
|---|---|
| `copy_live/faiss.index` | `3e09ad48029e35d153fdd38218cf98e63aeb6c1a92d8b2d0b17544e583e513fa` |
| `copy_live/memory_meta.json` | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` |
| `prefix_check.json` | `4ea6a9339f0253158e001f5821a48a749c904aee16d75ced6e6f63dbf4eabf2e` |
| `reembed_copy.py` | `7de02659a4402ae83d0103708f8decc3084cc9b220ab12f1b5455b116b5bd1ba` |
| `reembed.log` | `18cdf5321c5b1b2881c29cae5cff493c59ce35361b55d20ecb78947d3bae8848` |
| `rebuild_result.json` | `b54d912eed1e3c71b6cc4e82c584b391199ac349ddd0f8ee8e3106d7e02d8761` |
| `rebuilt/faiss.index` | `887a9fa7871ad3ccb880dbc2acc63235fbf5c451a801f8758eb1241ea029506f` |
| `rebuilt/memory_meta.json` | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` |
| `rebuilt/faiss.index.identity.json` | `6e68bf3062b6d0824b571d912464aae6f064198f493d7fb6afe5e83425b60baa` |
| `search_copy.py` | `00bd697aeb29f5555c146c179b2b0cf878741f004274787fdbcb9ca3ffc32019` |
| `search.log` | `8985789589e4f2c38083b07e6bdc83e575e4f63eb3aed831f728fbd5b5c95960` |
| `search_results.json` | `ada4228752b3b13499b12b2fbb2472212a75c5e4de0b664dbdecf894bc07b318` |

Hashes of this report and of `ARTIFACT_MANIFEST.md` are recorded in the manifest after this file is closed. They are not inside this file, because a digest stored inside the digested bytes would not match.

## Conclusion

On an isolated store, a legitimate identity sidecar written by the same process that embedded the cloned texts lets the existing, unmodified identity gate accept the index. With that gate open, the existing search returns all ten original user ids for their own Phase Two questions, and the existing 30-minute filter and k=5 cut place all ten section 3 hashes into a simulated injected context.

The missing live sidecar remains a sufficient account of the empty live candidate lists. This run shows that restoring valid identity metadata, by re-embedding a copy and letting the library write the sidecar, allows that retrieval path to function for these ten facts.

This run demonstrates that result on `rebuilt/` only. The live store still has no sidecar. The live index was not proved to contain these vectors. Echo was not asked the delayed questions again. No answer was scored. The rebuilt store stays in the laboratory.
