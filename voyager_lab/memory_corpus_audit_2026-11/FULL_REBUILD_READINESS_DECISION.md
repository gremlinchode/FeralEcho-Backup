# Full rebuild readiness decision

**Decision: NOT READY.**

This is a decision about rebuilding or snapshotting Echo's full memory corpus. It is not a decision about the ten-fact laboratory store. That store already exists, already has its own sidecar, and already returned its ten records in a finished diagnostic. Those facts stay in that diagnostic. They do not move this decision to GO.

## What was executed

The full-corpus measurement was executed. The four reports were not on disk at the start of this write; they are the audit's deliverables. Production was not modified. Pid 65139 was not signaled. Pid 86938 was not stopped. No model generation was spent. The live index was not re-embedded. No sidecar was written. No snapshot copy was retained.

The original decree text, beyond the follow-up that names these four files, was not recovered from disk. The decision uses the follow-up's scope: inventory, verified counts, identity coverage, completeness reconciliation, and a snapshot procedure that is technically defensible.

## The generation the decision is about

Live generation opened `2026-11-10T05:20:06.095028+00:00`–`2026-11-10T05:20:20.907322+00:00`, and still the path at `2026-11-10T05:27:23.776130+00:00`:

| | Index | Metadata |
|---|---|---|
| Path | `memory/faiss.index` | `memory/memory_meta.json` |
| Inode | 36671434 | 36671431 |
| Size | 241904685 | 136497506 |
| SHA-256 | `4abab200c591a6bf56264105d6170c855a539db001ff21e7262e5290b19945d6` | `912b7b1e320d11f1f45c256b7eb97b20dd301be2ac6b317d919368413fddb2cc` |
| Count | header `ntotal` 157490; size arithmetic 157490 | 157490 keys; 157490 nonempty texts; 157490 UUID keys |

Sidecar absent. Verified binding coverage 0. Row order of inode 36671434 UNKNOWN. Distinct texts 58652. Records inside duplicate-text groups 101959. `memory_source` missing on 23716 records. Timestamp missing on 32 records.

Writer still alive: pid 65139, `python -u run.py`, sentinel stage `serving`, heartbeat `2026-11-10T05:26:55.113302Z`.

## Why NOT READY

1. Quiescence fails. `QUIESCENT_SNAPSHOT_READINESS.md` step 1 fails while pid 65139 is `python -u run.py`. A seven-minute stable inode window, with the sentinel inode changing underneath it, is a window that did not tear. It is not a stopped writer. Copying now can still straddle two `os.replace` calls.

2. There is nothing retained to rebuild from. The audit hashed and counted the generation. It did not keep the bytes. A SHA-256 cannot be decoded back into `memory_meta.json`. The older laboratory copy is 40 records behind (157450 versus 157490) and its index hash is `887a9fa7…`, not `4abab200…`. The November 2 freeze is 5592 records behind and is a different index hash. Neither file set is this generation.

3. A rebuild would be a new embedding, not a restoration of the live index. The live process has no `id_order`. Metadata key order is not vector identity. Re-encoding the 157490 texts produces new vectors, a new row order, and a new sidecar for that new index. It does not reveal the rows inside inode 36671434. It must not be copied over `memory/faiss.index`.

4. Count alignment is not searchability. Header, size arithmetic, and key count agree at 157490. Search on the live store still has no manifest. This audit did not call search. Completeness of the pair is not a retrieval result.

5. 157490 records are not 157490 distinct memories. 101959 records share stripped text with at least one other record. 58652 unique texts is the distinct-text count. A rebuild that ignores that fact will faithfully re-embed duplicates. That may be the right preservation choice. It is not evidence the corpus is 157490 independent memories.

6. Other memory stores are outside the vector pair. Journals, the question garden (23562), Echo Studio (3284 messages), RiverBrain's pickle, provenance logs, the dimension-512 `data/` store (5348), and `memory/snapshots/` were inventoried. They were not inputs to any rebuild. Equality with `ntotal` is DISPROVEN for each counted store. Joins between them are UNKNOWN. A "full corpus" rebuild that reads only `memory_meta.json` leaves those stores behind, and a rebuild that tries to merge them has no verified id crosswalk.

7. The ten-fact pass does not generalize. It demonstrated retrieval on one rebuilt laboratory index after that index and its sidecar were written together. The live index hash differs. The live record count differs by 40. The live sidecar is absent. Success on ten ids in the laboratory store is reference evidence that a fresh embed-plus-sidecar pair can be searched. It is not evidence that the untouched live corpus is ready to rebuild, snapshot, or install.

## What would have to be true before a later GO

All of the following, under a new decree. This decision does not grant them.

- `ps` shows no `python -u run.py`, and the sentinel pid is not alive. Studio may keep running.
- No temp siblings.
- Double-stat stable, then `O_RDONLY` reads whose path stat still matches, with bytes retained in a laboratory directory that is not `memory/`.
- The retained index passes the `IxFI` / dimension 384 / `ntotal` / size-arithmetic / metadata-key-count test, and the report says explicitly that row order is still unknown if no sidecar was present.
- An explicit authorization to re-embed that retained metadata into a new store, producing new index bytes and a new sidecar, without installing either file over the live paths.
- A stated choice about duplicate texts and about whether journals, the garden, and Studio are in scope. They are not in scope of a vector re-embed unless that decree adds them.

Until those are true, the allowed state is: leave the live pair where it is, leave the laboratory rebuild where it is, and leave the November 2 freeze where it is.

## What this decision refuses

- Installing `rebuilt/` over live memory.
- Writing `faiss.index.identity.json` beside the live index from metadata key order.
- Treating the 05:20–05:27 stable window as a snapshot.
- Spending the two unused evidence-to-answer generations.
- Stopping or restarting Echo to manufacture quiescence inside this audit.
- Editing production code, sealed experiment files, forensic reports, or the finished ten-fact reports.

## One next step, not executed

Stop is the missing precondition, and this audit does not take it. The next step is a human decision to stop `python -u run.py` cleanly, then a new decree to retain a quiescent copy under the procedure in `QUIESCENT_SNAPSHOT_READINESS.md`. No re-embed starts from that copy unless that later decree says so.

## Integrity

| Item | State |
|---|---|
| Production writes | None in this audit |
| Processes signaled | None |
| Model generations | 0 |
| Live sidecar after the audit | Absent at `2026-11-10T05:27:23Z` |
| Live index inode after the audit | 36671434, size 241904685, `mtime_ns` `1794287645468709385` |
| Live metadata inode after the audit | 36671431, size 136497506, `mtime_ns` `1794287645392385325` |
| Temp siblings | Absent |
| Pid 65139 | Still `python -u run.py` |
| Independent review | Not required. No production code changed |

Measurement evidence: `measurements.json` and `measurements_supplement.json` in this directory. The invalid `uuid_shaped_keys` field stays in the measurement file. The supplement corrects it.
