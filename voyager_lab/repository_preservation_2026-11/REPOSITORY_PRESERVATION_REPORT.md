# Repository preservation report

Recorded 2026-11-10. This file is part of the commit that adds the reviewed Voyager research package. It does not claim that GitHub has accepted that commit. `GITHUB_PUBLICATION_STATUS.md` is written only after the remote branch SHA matches the local commit.

## Result label

PARTIALLY DEMONSTRATED at the time this file was written: the package was classified, the sensitive artifacts were left on disk, and a dedicated local commit was prepared. Publication is not claimed here.

## Where this was done

- Worktree: `/Users/richietate/Desktop/FeralEcho-voyager`
- Branch: `project-voyager`
- Parent commit: `dc8d6eb9b6479ef323614cd6820bb050a14299eb`
- Upstream before this work: none
- Remote: `git@github.com:gremlinchode/FeralEcho-Backup.git` (HTTPS equivalent `https://github.com/gremlinchode/FeralEcho-Backup`)
- Remote visibility, read from GitHub on 2026-11-10: PUBLIC (`isPrivate: false`). Default branch `main`.
- Remote heads before this push: `main` at `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, `vsl-implementation` at `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. `project-voyager` was absent.
- SSH authentication to `git@github.com` returned `Permission denied (publickey)`. The push uses HTTPS through the existing `gh` login, with a one-command credential helper. Git config was not changed. No force push.

The parent commit is already on the public remote as `vsl-implementation`. This branch adds the Voyager research package on top of that commit. It does not merge into `main` or `vsl-implementation`.

Local `main` (`e5acbb09cece8d1791fa6d967fe57067137a8cff`) is four commits ahead of `origin/main`. Those commits were not pushed.

The production worktree at `/Users/richietate/Desktop/FeralEcho` is `vsl-implementation` and has its own uncommitted files. None of those files are in this commit. No production process was signaled. No production memory file was opened for write.

## Working tree that was classified

Reconfirmed 2026-11-10T05:43:06Z. `git status -sb` showed only two untracked paths: `FERALECHO_NEXT_RESEARCH_PRIORITY.md` and `voyager_lab/`. No symlinks were found under `voyager_lab/`.

The untracked tree was inventoried before ignore rules were applied. The publishable candidate set, after the exclusions below, was 874 files and 1,884,628 bytes. Nothing in that set is 10 MB or larger. The largest publishable file is `voyager_lab/memory_retrieval_diagnostic_2026-11/search_results.json` at 87,442 bytes. A scan of those 874 files found no API key, GitHub token, private-key block, or Tailscale address, and no line longer than 2,000 characters.

Root `.gitignore` already drops `*.index`, `*.log`, `*.pyc`, and `__pycache__/`. It does not drop `memory_meta.json`, `faiss.index.identity.json`, or `.human_token`. A new `voyager_lab/.gitignore` drops the two memory-clone directories and every `.human_token` so a later `git add voyager_lab` cannot pick them up.

## What this commit contains

Reviewed research reports, protocols, harness source, scoring tools, sanitized raw results, the November transparency package (unchanged, including its `MANIFEST.sha256`), the memory-retrieval forensic reports, the copy-only diagnostic report and its hash-only search output, the full-corpus audit reports and their measurement JSON, and `FERALECHO_NEXT_RESEARCH_PRIORITY.md`.

`PUBLICATION_MANIFEST.md` is the category list. `PUBLICATION_PATHS.txt` is the path list for this commit. `EXCLUDED_ARTIFACTS.md` is the local-only record.

## What stays local

Cloned and rebuilt memory stores, the identity sidecar, two diagnostic logs, four bytecode files, and three synthetic `.human_token` fixtures. They were not deleted. Details and hashes are in `EXCLUDED_ARTIFACTS.md`.

## Privacy notes that are not credentials

`ORIGIN.md` and `COUNCIL.md` are already tracked in the parent commit, which is already on the public remote. This mission does not add or remove them.

Two transparency files restate a biographical sentence that is already in `ORIGIN.md`: `voyager_lab/project_transparency/MASTER_PROJECT_HISTORY.md` and `voyager_lab/project_transparency/ECHO_PROJECT_BRIEFING.md`. Those files belong to the sealed transparency package. They were not edited. Because the repository is public, restating that sentence on this branch is world-readable. No new personal narrative was added by this preservation pass.

`search_results.json` stores ranks, scores, source labels, roles, and short hashes. It does not store memory text. The corpus-audit measurement files store counts, inodes, filenames, and hashes. They do not store memory bodies.

Git `user.name` and `user.email` are unset and were left unset. The commit author is taken from the parent commit's author for this commit only, through the environment.

## Pre-commit checks

The staged set was 879 paths. A forbidden-path scan found none of `copy_live/`, `rebuilt/`, `memory_meta.json`, `faiss.index`, `.identity.json`, `.human_token`, `.pyc`, or `.log`. A scan of the staged blobs found no API key, GitHub token, private-key block, Tailscale address, or NUL byte.

`git diff --cached --check` reported 8 trailing-whitespace warnings, all in two sealed diagnostic files: `ARTIFACT_MANIFEST.md` and `COPY_ONLY_DIAGNOSTIC_REPORT.md`. Those lines are Markdown hard breaks. The files were not edited. The check reported no conflict markers.

## What was not done

- No push is claimed by this file.
- `main` was not updated.
- Voyager was not merged into a production branch.
- Production code, production memory, and the live process were not modified.
