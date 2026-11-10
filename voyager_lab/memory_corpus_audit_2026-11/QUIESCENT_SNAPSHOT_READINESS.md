# Quiescent snapshot readiness

Procedure only. This audit did not take the snapshot.

## Question

Can a copy of Echo's memory corpus, taken under the conditions observed on 2026-11-10, be one coherent generation?

Answer for the vector pair: the writer is still running, so the precondition fails. A copy taken now can tear across files even though each `os.replace` is atomic for one file. The read window in this audit happened to see one count-aligned generation. That window is not quiescence.

## What "one generation" means here

VERIFIED from `app/lib/vector_memory.py` `_persist`, lines 342–411, read this session:

1. Metadata is written to `memory_meta.json.tmp` and published with `os.replace`.
2. The index is written to `faiss.index.tmp`, hashed, and published with `os.replace`.
3. `faiss.index.identity.json` is written only when this process owns insertion order and the index write happened.

A crash or an interleaved copy can hold a new metadata file beside an older index, or a new index beside an older sidecar. Load is written to refuse trusted search in the mismatch cases rather than guess ids from key order. An already-open file descriptor keeps the inode it opened. A later `os.replace` changes the path, not that descriptor. Hashing a path is the current generation only when a stat before the read and a stat after the read match the opened inode and size.

The live store has no sidecar. Copying the two files that do exist, even from one quiet instant, produces an unverified pair. The copy's key order is still not row order.

`snapshot_manager.take_snapshot` is a different operation. `_ARTIFACTS` (lines 68–80) copies self-edit output, `river_brain.pkl`, principles, the Modelfile, `COUNCIL.md`, and the two genesis hashes. It does not copy `faiss.index` or `memory_meta.json`. The 40 files under `memory/snapshots/` are not a vector-corpus snapshot. This procedure does not call `take_snapshot`.

## Observed state when the procedure was scored

Scored at `2026-11-10T05:27:23.776130+00:00`. Stat and `ps` only. No signal was sent.

| Precondition | Observation | Ready? |
|---|---|---|
| No `python -u run.py` | Pid 65139, stat `R+`, elapsed `06-10:25:28`, command `python -u run.py` | Fail |
| Sentinel pid not alive | Sentinel pid 65139, stage `serving`, heartbeat `2026-11-10T05:26:55.113302Z`, uptime 555894 seconds, start `2026-11-03T19:02:01.305169Z`. Pidfile contains `65139` | Fail |
| Echo Studio | Pid 86938 still `python -m echo_studio.main`. It is not the FAISS writer. Leave it running | Not a vector-writer stop |
| No temp siblings | `faiss.index.tmp`, `memory_meta.json.tmp`, and `faiss.index.identity.json.tmp` absent | Pass at this instant |
| Sidecar | `faiss.index.identity.json` absent | Record the absence. Do not create one |
| Double-stat of the vector pair | Inode 36671434 size 241904685 and inode 36671431 size 136497506, `mtime_ns` unchanged from the 05:20 measurement through this 05:27 stat | Stable window while the writer exists. Not a pass |
| Sentinel file itself | Directory inventory inode 36673540; this stat inode 36676292, size still 163 | The process is publishing other files during the window |

The vector pair did not change across about seven minutes. The sentinel inode did. Pid 65139 was runnable (`R+`) at the later stat. A stable pair beside a live writer is a window that happened not to tear. It is not authorization to copy.

## Procedure to use when a later decree allows a snapshot

Do not run these steps while pid 65139, or any later `python -u run.py`, is alive.

1. `ps` must show no `python -u run.py`. The sentinel pid must not be alive. Do not use `kill`, including `kill -0`. If a server is running, stop the procedure and say the precondition failed.
2. Leave Echo Studio running unless a separate decree names the sqlite file. Studio is not the FAISS writer. Its database is its own generation: inode, `PRAGMA query_only`, then `COUNT(*)`.
3. Stat `memory/faiss.index.tmp`, `memory/memory_meta.json.tmp`, and `memory/faiss.index.identity.json.tmp`. Any of them existing means a persist is in progress. Stop.
4. Stat the index, the metadata, and the sidecar path. Sleep. Stat again. Inode, size, and `mtime_ns` must be identical. If the sidecar is absent, write "absent" into the manifest. Do not create a sidecar to fill the gap.
5. Open each existing file `O_RDONLY`, `fstat`, read to EOF, and hash. If the path stat after the read differs from the opened inode or size, discard the bytes. With the writer stopped, a stable double-stat plus an inode read is the generation. A racing copy while the writer exists is not quiescent, even if one window happens not to tear.
6. Accept the vector generation only when fourcc is `IxFI`, dimension at offset 4 is 384, the int64 at offset 8 equals `(size - 45) / 1536`, and that `ntotal` equals the metadata key count. Record the result. Equality is necessary and not sufficient for row identity.
7. Do not write `faiss.index.identity.json` from `memory_meta.json` keys. A sidecar is valid only when the process that wrote the index recorded insertion order. The running server does not do that for the current live files: the sidecar is absent, and loading an existing unverified index does not make `_identity_authoritative` true. A copied live pair remains unverified. Search on that copy returns nothing until a real sidecar exists for those index bytes, and those index bytes do not have one.
8. A later re-embed is a new store: new index bytes, new `id_order`, new sidecar, new hashes. It must not be copied over `memory/faiss.index`. It does not repair the running process. It does not make the old live rows match the new vectors.
9. Snapshot journals, `data/question_garden.jsonl`, `~/.echo_studio/echo_studio.db`, `memory/river_brain.pkl`, and the provenance logs as separate generations. Rotated `.1.gz` siblings are part of journal history and are not inside the live jsonl line count. `snapshot_manager` snapshots are not this corpus snapshot. The legacy `data/faiss.index` is dimension 512 and is not this corpus.
10. Retain the bytes under a laboratory path named by the decree, with inode, size, mtime, and SHA-256 recorded from the opened descriptors. A hash without the bytes cannot rebuild the store.

## What this audit already did, and where it stopped

Steps 4 and 5 were executed as reads. The opened generation matched step 6's count test: 157490, 157490, and 157490. Step 7 was obeyed: no sidecar was written. Steps 8 and 10 were not executed. No bytes were retained. The diagnostic `copy_live/` directory is an older coherent generation (`ntotal` 157450, metadata hash `5cb458d4…`). It is not inode 36671434. Do not reuse it as the current snapshot.

Step 1 failed at every observation in this audit, including `2026-11-10T05:20:20Z`, `2026-11-10T05:22:42Z`, and `2026-11-10T05:27:23Z`.

## Readiness of the procedure itself

The procedure is defined. The corpus is not in the state the procedure requires. Quiescent snapshot readiness of the live vector pair is fail until `python -u run.py` is actually absent, a double-stat is stable after that absence, and the inode reads are retained. This document does not stop the server to produce that absence.
