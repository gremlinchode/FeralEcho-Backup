# Artifact manifest

**Directory:** `voyager_lab/memory_retrieval_diagnostic_2026-11/`  
**Worktree:** `/Users/richietate/Desktop/FeralEcho-voyager`  
**Date:** 2026-11-09  
**Role:** inventory for the copy-only memory retrieval diagnostic.

No temporary files remain. Nothing from this directory was copied onto the live memory paths. No `/tmp` scratch was left behind. Every file below is retained evidence.

The manifest digest is computed after this file is closed and is reported with the diagnostic answer. It is not stored inside this file.

## Retained evidence

| Path | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `COPY_ONLY_DIAGNOSTIC_REPORT.md` | 19,675 | `986a62896758e2bed4df97e7c080f3957976e8434ea9065ffd293fd8077d6af9` | The diagnostic report. |
| `copy_live/faiss.index` | 241,843,245 | `3e09ad48029e35d153fdd38218cf98e63aeb6c1a92d8b2d0b17544e583e513fa` | Frozen clone of one live index generation. No sidecar. Not modified after the clone. Not the store that search loaded. |
| `copy_live/memory_meta.json` | 136,449,185 | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` | Frozen clone of the matching metadata generation. Source texts for the re-embed. |
| `prefix_check.json` | 1,293 | `4ea6a9339f0253158e001f5821a48a749c904aee16d75ced6e6f63dbf4eabf2e` | Literal prefix comparison. `pure_byte_prefix` false. First mismatch at offset 8. |
| `reembed_copy.py` | 6,588 | `7de02659a4402ae83d0103708f8decc3084cc9b220ab12f1b5455b116b5bd1ba` | Copy-only re-embed script. Refuses to write outside this directory. |
| `reembed.log` | 2,117 | `18cdf5321c5b1b2881c29cae5cff493c59ce35361b55d20ecb78947d3bae8848` | Re-embed log. Ends `REEMBED_DONE`. |
| `rebuild_result.json` | 895 | `b54d912eed1e3c71b6cc4e82c584b391199ac349ddd0f8ee8e3106d7e02d8761` | Re-embed summary. Declared order is JSON key order. `declared_order_is_old_faiss_row_order` false. |
| `rebuilt/faiss.index` | 241,843,245 | `887a9fa7871ad3ccb880dbc2acc63235fbf5c451a801f8758eb1241ea029506f` | New index written with the sidecar. Different digest from `copy_live/faiss.index`. |
| `rebuilt/memory_meta.json` | 136,449,185 | `5cb458d440855e4305dcaa457abb4f0681a2dbf5df8c1dd69bb39cc8a43ff248` | Metadata written with the new index. Same digest as the clone. |
| `rebuilt/faiss.index.identity.json` | 6,928,012 | `6e68bf3062b6d0824b571d912464aae6f064198f493d7fb6afe5e83425b60baa` | Schema-1 sidecar. `index_sha256` `887a9fa7871ad3ccb880dbc2acc63235fbf5c451a801f8758eb1241ea029506f`. `binding_sha256` `a3c64a5a04ebd0dd983bc49f1f18a933dc4bb2073abbd8b06dbd0aa0119751cc`. `id_order` length 157,450. |
| `search_copy.py` | 14,950 | `00bd697aeb29f5555c146c179b2b0cf878741f004274787fdbcb9ca3ffc32019` | Fresh-process load and ten-fact search. Does not import `memory_bridge`. |
| `search.log` | 1,836 | `8985789589e4f2c38083b07e6bdc83e575e4f63eb3aed831f728fbd5b5c95960` | Search log. Ends `SEARCH_DONE outcome=PASS demonstrated=10/10`. |
| `search_results.json` | 87,442 | `ada4228752b3b13499b12b2fbb2472212a75c5e4de0b664dbdecf894bc07b318` | Per-fact results, identity block, controls, stage counts. |

## Temporary artifacts

None. The scripts and logs are retained procedure evidence, not disposable scratch.

## Not created

- No sidecar next to the live index.
- No production code or configuration change.
- No cutover of `rebuilt/` or `copy_live/` onto `/Users/richietate/Desktop/FeralEcho/memory/`.
- No additional model generation.
- No edit to the forensic reports, the sealed evidence-to-answer files, or the transparency package.
