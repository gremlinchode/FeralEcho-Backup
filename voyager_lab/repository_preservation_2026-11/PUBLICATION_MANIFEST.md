# Publication manifest

Branch `project-voyager`. Parent `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. The exact path list for the commit that adds this package is `PUBLICATION_PATHS.txt` in this directory. That list includes this file.

This manifest is a classification, not a claim that GitHub has the commit. See `GITHUB_PUBLICATION_STATUS.md` after the remote check.

## Included

| Class | What | Notes |
|---|---|---|
| Research indexes and reports | `voyager_lab/*.md`, `README.md`, `FERALECHO_NEXT_RESEARCH_PRIORITY.md` | Priority document was scanned and included unchanged. |
| Transparency package | `voyager_lab/project_transparency/` | Eight files, including `MANIFEST.sha256`. Not edited. |
| Evidence-to-answer experiment | `voyager_lab/evidence_to_answer_2026-11/` | Protocol, harness, scores, and raw phase JSONL. Sealed files were not edited. Bytecode excluded. |
| Memory-retrieval forensics | `voyager_lab/memory_retrieval_forensics_2026-11/` | Two reports. Not edited. |
| Copy-only diagnostic, publishable half | Report, artifact manifest, `reembed_copy.py`, `search_copy.py`, `rebuild_result.json`, `prefix_check.json`, `search_results.json` | Search output is hashes and ranks, not memory text. |
| Corpus audit | Four reports plus `measurements.json` and `measurements_supplement.json` | Counts, hashes, inodes, filenames. No memory bodies. Not edited. |
| Voyager harness | `voyager_lab/voyager/`, `run_experiment.py`, `freeze.py`, `self_check.py`, `RUBRIC_FREEZE.json` | Source and frozen rubric. |
| Raw Voyager results | `voyager_lab/results/` | Per-mission grades and tiny synthetic world files. Token fixtures excluded. |
| Other laboratory packages | `ungated_file_retrieval/`, `reasoning_reliability/`, `scratch_write/` | Harnesses, fixtures, and reports. Bytecode excluded. |

Publishable candidate count before these preservation files: 874 files, 1,884,628 bytes. No publishable candidate is 10 MB or larger.

## Excluded from the commit, kept on disk

See `EXCLUDED_ARTIFACTS.md`. Short form:

- `memory_retrieval_diagnostic_2026-11/copy_live/` — cloned memory index and metadata.
- `memory_retrieval_diagnostic_2026-11/rebuilt/` — re-embedded index, metadata, and identity sidecar.
- `search.log` and `reembed.log` — already ignored by root `*.log`.
- `__pycache__/*.pyc` — already ignored.
- Three `.human_token` files — synthetic fixtures, excluded by `voyager_lab/.gitignore`.

## Not in this branch's new commit

- Anything already in parent `dc8d6eb`, including production source, `ORIGIN.md`, and `COUNCIL.md`.
- The dirty production worktree.
- Local `main`'s four unpushed commits.

## Checks required before the push

`git diff --check` on the staged diff. Staged names must not contain `copy_live`, `rebuilt`, `memory_meta.json`, `faiss.index`, `.identity.json`, `.human_token`, `.pyc`, or `.log`. A staged-diff scan must not find an API key, a GitHub token, a private-key block, or a Tailscale address. The push must not be a force push, and it must update only `project-voyager`.
