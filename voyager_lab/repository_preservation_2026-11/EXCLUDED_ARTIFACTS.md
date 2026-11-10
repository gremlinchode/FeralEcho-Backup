# Excluded artifacts

These files remain on the Voyager machine. They were not deleted. They are not in the `project-voyager` commit. Hashes are SHA-256 of the local bytes, computed 2026-11-10.

## Why the memory clones are not published

`copy_live/` is a laboratory copy of Echo's vector index and metadata. `rebuilt/` is a new index built from that copy, plus a sidecar that binds real memory record ids. Publishing either directory would publish private memory text and the record-id list. The experiment can be read without those bytes. The published diagnostic report, `prefix_check.json`, `rebuild_result.json`, and `search_results.json` record what was measured: header checks, identity-gate behavior, ranks, and text hashes. They do not contain the memory text.

A later reproduction needs an authorized quiescent copy of whatever store is being tested. This package does not include one, and it does not instruct anyone to copy the live production store.

## Memory clones

| Path | Bytes | Inode | SHA-256 |
|---|---:|---:|---|
| `voyager_lab/memory_retrieval_diagnostic_2026-11/copy_live/faiss.index` | 241843245 | 36641234 | `3e09ad48029e35d153fdd38218cf98e63aeb6c1a92d8b2d0b17544e583e513fa` |
| `voyager_lab/memory_retrieval_diagnostic_2026-11/copy_live/memory_meta.json` | 136449185 | 36641235 | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` |
| `voyager_lab/memory_retrieval_diagnostic_2026-11/rebuilt/faiss.index` | 241843245 | 36652234 | `887a9fa7871ad3ccb880dbc2acc63235fbf5c451a801f8758eb1241ea029506f` |
| `voyager_lab/memory_retrieval_diagnostic_2026-11/rebuilt/memory_meta.json` | 136449185 | 36652231 | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` |
| `voyager_lab/memory_retrieval_diagnostic_2026-11/rebuilt/faiss.index.identity.json` | 6928012 | 36652235 | `6e68bf3062b6d0824b571d912464aae6f064198f493d7fb6afe5e83425b60baa` |

Directory sizes on disk: `copy_live/` 361 MB, `rebuilt/` 367 MB. The two metadata files are byte-identical. The two indexes are not. The sidecar binds the rebuilt index, not the cloned index.

Root `.gitignore` already ignores `*.index`. It does not ignore `memory_meta.json` or `faiss.index.identity.json`. `voyager_lab/.gitignore` ignores both directories, which is what keeps those files out of the commit.

## Diagnostic logs

Ignored by the root `*.log` rule. Small, and not a memory dump. Left ignored rather than force-added.

| Path | Bytes | Inode | SHA-256 |
|---|---:|---:|---|
| `voyager_lab/memory_retrieval_diagnostic_2026-11/search.log` | 1836 | 36652295 | `8985789589e4f2c38083b07e6bdc83e575e4f63eb3aed831f728fbd5b5c95960` |
| `voyager_lab/memory_retrieval_diagnostic_2026-11/reembed.log` | 2117 | 36642470 | `18cdf5321c5b1b2881c29cae5cff493c59ce35361b55d20ecb78947d3bae8848` |

## Bytecode

Ignored by root `__pycache__/` and `*.pyc` rules:

- `voyager_lab/ungated_file_retrieval/__pycache__/harness.cpython-313.pyc`
- `voyager_lab/evidence_to_answer_2026-11/__pycache__/transport.cpython-313.pyc`
- `voyager_lab/evidence_to_answer_2026-11/__pycache__/score.cpython-313.pyc`
- `voyager_lab/reasoning_reliability/__pycache__/grader.cpython-313.pyc`

The matching `.py` sources are in the commit.

## Token fixtures

Three files, each 3 bytes, mode `0600`, byte-identical to each other:

- `voyager_lab/results/raw/engine/M18/world/.human_token`
- `voyager_lab/results/raw/ablation/M18/world/.human_token`
- `voyager_lab/results/raw/baseline/M18/world/.human_token`

They are synthetic fixtures written by `plant_human_token()` in `voyager_lab/voyager/world.py`. The file contents and their hash are not recorded here. They are excluded because they are token files, and the harness source already shows that the fixture is a fixed test constant. `voyager_lab/.gitignore` ignores every `.human_token`.
