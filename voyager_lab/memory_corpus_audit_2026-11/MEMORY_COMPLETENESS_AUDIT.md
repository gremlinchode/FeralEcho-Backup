# Memory completeness audit

Generation under audit: the live pair opened `2026-11-10T05:20:06.095028+00:00` through `2026-11-10T05:20:20.907322+00:00`.

- Index inode 36671434, size 241904685, SHA-256 `4abab200c591a6bf56264105d6170c855a539db001ff21e7262e5290b19945d6`
- Metadata inode 36671431, size 136497506, SHA-256 `912b7b1e320d11f1f45c256b7eb97b20dd301be2ac6b317d919368413fddb2cc`
- Sidecar absent
- Same inodes, sizes, and `mtime_ns` still the path at `2026-11-10T05:27:23.776130+00:00`

The bytes were not retained. A later `os.replace` can publish a new inode. Completeness below is about this generation, read by holding the inode, because `_persist` replaces one file at a time.

`measurements.json` field `uuid_shaped_keys` is 0 on every store. That checker is wrong: it rejects hyphens. The recount in `measurements_supplement.json` is the UUID result. The measurement file was not rewritten to hide the bad field.

The ten-fact laboratory store is 157450 records and a different index hash. It is not this generation. Its retrieval pass is not completeness evidence for inode 36671434.

## Mission

Falsifiable claim: on one named generation, metadata key count, header `ntotal`, and size arithmetic describe the same number of records, and record-field identity is known separately from manifest binding.

Competing hypotheses:

1. The live files are one count-aligned generation and the sidecar binds every id to a row.
2. The live files are count-aligned and unbound, so row identity stays unknown.
3. The live files are torn: header count and metadata count disagree.
4. Journals, the garden, Studio, and `data/` are the same record set as the vector pair.

What would change the conclusion: a schema-1 sidecar whose `index_sha256` equals `4abab200…` and whose `id_order` is a permutation of the 157490 metadata keys with length 157490. Or a before/after inode change showing the read crossed two generations. Neither was observed.

Non-goals: no search, no re-embed, no snapshot copy, no production write, no model generation, no interruption of pid 65139 or pid 86938.

## Count reconciliation

| Check | Result | Label |
|---|---|---|
| Fourcc | `IxFI` | VERIFIED |
| Dimension at offset 4 | 384 | VERIFIED |
| `ntotal` at offset 8 | 157490 | VERIFIED |
| `(size - 45) / (384 * 4)` | 157490, divides evenly | VERIFIED |
| Metadata keys on the opened inode | 157490 | VERIFIED |
| Header `ntotal` equals metadata keys | true | VERIFIED |
| Unique keys | 157490 | VERIFIED |
| Non-dict values | 0 | VERIFIED |
| `text` nonempty | 157490 | VERIFIED |
| `text` missing, empty, or non-string | 0 | VERIFIED |
| Repeated JSON keys | 0 | VERIFIED |
| Path inode changed during either read | false | OBSERVED |
| Opened byte length equals file size | true for both files | VERIFIED |
| Sidecar present | false | OBSERVED |
| Verified `id_order` length | 0 | VERIFIED from absence |

Hypothesis 3 is DISPROVEN for this read. The two files agree on 157490. Hypothesis 1 is DISPROVEN: there is no sidecar, so verified binding coverage is 0. Hypothesis 2 is VERIFIED as a count claim and left UNKNOWN as a row-order claim.

Equal counts are necessary. They are not sufficient for "metadata key i is FAISS row i." `vector_memory.py` says key order is not vector identity. Duplicate ids update metadata and do not append a second vector. This audit did not recover the insertion order the running process used.

## Identity coverage, two layers

These are different facts. Coverage on one does not move the other.

### Manifest binding

OBSERVED: `memory/faiss.index.identity.json` does not exist. VERIFIED consequences on this generation: `id_order` length 0, unique bound ids 0, index hash recorded by a sidecar 0, binding coverage 0 / 157490.

A sidecar is valid for an index when the process that wrote those index bytes recorded insertion order and the sidecar's `index_sha256` equals that file. Stamping `memory_meta.json` key order onto inode 36671434 would invent an order. This audit did not write that file.

### Record-field identity

VERIFIED on a second read of inode 36671431, size 136497506, at `2026-11-10T05:22:42.971310+00:00`, with `same_inode_and_size_as_measurements: true`:

| Field | Count |
|---|---:|
| Keys | 157490 |
| Lowercase hyphenated UUID keys | 157490 |
| Other keys | 0 |
| Nonempty `text` | 157490 |

Record-field coverage of this metadata generation is 157490 / 157490 UUID keys and 157490 / 157490 nonempty texts. Manifest coverage of the paired index is 0 / 157490.

## Field completeness inside the 157490

| Field | Present | Missing |
|---|---:|---:|
| `text` | 157490 | 0 |
| `timestamp` | 157458 | 32 |
| `memory_source` | 133774 | 23716 |
| `role` | 132528 | 24962 |
| `validation_warning` true | 21139 | the rest are not a counted "false" bucket in this profile |

Timestamp span: `2026-07-02T21:40:53.854995+00:00` through `2026-11-10T05:14:03.470526+00:00`. The 32 missing timestamps are a real gap. Their ids were not listed individually in the measurement output.

`memory_source` missing is exactly 23716, the same missing count as the November 2 freeze (151898 records). The untagged set did not grow across the +5592 records added after that freeze. That is a field-count agreement. It does not by itself prove the same 23716 ids.

Source and role tables, and the check that each sums to 157490, are in `FULL_MEMORY_CORPUS_INVENTORY.md`. Freeze-to-live deltas also sum to 5592 on both tables.

## Distinct text versus record count

VERIFIED arithmetic on the opened metadata:

- Unique nonempty text hashes: 58652
- Duplicate-text groups: 3121
- Records participating in those groups: 101959
- Singletons: 157490 − 101959 = 55531
- Unique texts: 55531 + 3121 = 58652
- Extra copies beyond one per group: 101959 − 3121 = 98838

157490 is the record count. It is not 157490 distinct texts. A full re-embed of every text would re-encode duplicate strings. Whether those duplicates are the same memory restated or independent events that share wording was not decided. UNKNOWN.

## Other stores against this generation

Hypothesis 4 is DISPROVEN as equality. None of these counts is 157490.

| Store | Count on its own opened inode | Relation to 157490 |
|---|---:|---|
| November 2 freeze `ntotal` and keys | 151898 | 5592 behind; sidecar-bound there |
| Legacy `data/` `ntotal` and keys | 5348 | dimension 512; no sidecar; empty inner meta |
| Laboratory rebuilt `ntotal` and keys | 157450 | 40 behind; different index hash; sidecar-bound there |
| `interaction_log.jsonl` lines | 4375 | rotated; `.1.gz` exists; overlap UNKNOWN |
| `user_conversation` source | 7481 | subset label, not a journal line count |
| `role=user` | 1809 | subset label |
| `dream_bridge.log` lines | 559978 | far above `role=dream` 24137 |
| `role=dream` | 24137 | unchanged since the freeze |
| `memory_journal.log` lines | 5487 | separate journal |
| `quarantine_journal.jsonl` lines | 49288 | separate journal |
| `reflection_journal.jsonl` lines | 12060 | separate journal |
| `reflection_shard.jsonl` lines | 12899 | separate journal |
| `council_deliberations.jsonl` lines | 3527 | separate journal |
| `question_garden.jsonl` lines | 23562 | 23535 active, 27 composted; id overlap UNKNOWN |
| Echo Studio `messages` | 3284 | separate sqlite; id overlap UNKNOWN |
| `retrieval_provenance.jsonl` lines | 688 | see below |
| `search_provenance.jsonl` lines | 2796 | different log; see below |

September 2 metadata backups (about 89MB each) are earlier files in `memory/`. They were stat-listed. They were not parsed. They are not this generation.

## Provenance completeness

`retrieval_provenance.jsonl` does not contain one line per vector record. It contains 688 retrieval events.

Supplement recount, which replaces the script's failed candidate-field probe:

| Fact | Value |
|---|---|
| Lines | 688 |
| `candidates_considered` > 0 | 446 |
| `candidates_considered` = 0 | 242 |
| Last positive | `2026-10-28T04:04:29.156643`, 15 considered, 5 injected |
| Records after that positive | 241 |
| Nonzero candidates after that positive | 0 |
| Nonempty injected list after that positive | 0 |
| First timestamp after that positive | `2026-10-29T02:21:39.525310` |
| Last record | `2026-11-10T03:34:06.234790`, candidates 0, injected empty |
| Injected empty while candidates > 0 | 11 |
| Injected nonempty while candidates = 0 | 0 |
| File-order time inversions | 0 |

From `2026-10-29T02:21:39.525310` through the last provenance line, recorded vector retrieval considered nothing. That is a log fact. It does not, by itself, name the code branch. The live sidecar is absent on the generation above. How that absence maps onto the October 29 boundary was established in the earlier forensic report. This completeness audit does not re-litigate those ten facts.

`search_provenance.jsonl` carries `injected_count` on all 2796 lines. A later read of inode 30805598 at the same size 947032 found every `injected_count` positive. That field is a web-search injection count. It is not `candidates_considered`. Using it as evidence that vector search returned hits would mix two logs. DISPROVEN as a vector-retrieval completeness signal.

## Certified comparison, binding only

The November 2 freeze and the laboratory rebuilt store each have schema 1, `id_order` length equal to `ntotal` equal to metadata keys, 0 ids missing, 0 ids extra, and sidecar `index_sha256` equal to the index file that was opened. The live generation has the count equality and lacks the binding. Those are three corpora.

The freeze index hash `0dc600d7…` equals that freeze sidecar's `index_sha256`. It is not the live hash `4abab200…`.

## Gaps left UNKNOWN

- FAISS row for each live UUID.
- Whether the 23716 untagged live records are the same ids as the 23716 untagged freeze records.
- Which 32 records lack timestamps.
- Distinct records excluded by the `code_analysis` / `self_model_reflection` filter.
- Join of garden ids, Studio message ids, interaction-log ids, and vector ids.
- Whether duplicate texts are repeated events or duplicate storage.
- Contents of the September 2 metadata backups, `memory/archive`, `memory/backups`, and `memory/experiments` beyond file counts.
- Any vector write after `2026-11-10T05:27:23Z`.

## Conclusion

This generation is count-complete as a pair of files: 157490 header vectors, 157490 size-implied vectors, 157490 metadata records, 157490 nonempty texts, 157490 UUID keys. It is identity-incomplete as a searchable manifest: binding coverage 0. It is text-redundant: 58652 distinct texts. It is not the union of the journals, the garden, Studio, `data/`, or the laboratory rebuild.

A full rebuild from these texts is a new embedding of a metadata generation. It becomes possible only after a quiescent copy of that metadata file exists. This audit did not make that copy. Readiness is decided in `FULL_REBUILD_READINESS_DECISION.md`.
