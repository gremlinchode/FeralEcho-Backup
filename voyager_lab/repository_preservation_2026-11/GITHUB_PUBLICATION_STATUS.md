# GitHub publication status

Checked 2026-11-10 after the push returned.

## Result

PASS. The remote branch exists and its SHA matches the local commit.

| Item | Value |
|---|---|
| Repository | `gremlinchode/FeralEcho-Backup` |
| Visibility | PUBLIC |
| Branch | `project-voyager` |
| Commit | `38d1b4c28a32c9a63207b4b856d8861ffba42ae6` |
| Parent | `dc8d6eb9b6479ef323614cd6820bb050a14299eb` |
| Push | New branch. Not a force push. |
| Remote confirmation | `gh api` returned `{"name":"project-voyager","sha":"38d1b4c28a32c9a63207b4b856d8861ffba42ae6"}` |

URL: `https://github.com/gremlinchode/FeralEcho-Backup/tree/project-voyager`

## What that commit contains

879 paths. The preservation reports, the publication manifest, the path list, and the excluded-artifact record are in `voyager_lab/repository_preservation_2026-11/`. The remote listing of that directory shows those four files. The remote listing of `voyager_lab/memory_retrieval_diagnostic_2026-11/` shows the report, the two scripts, and the hash-only JSON files. It does not show `copy_live/`, `rebuilt/`, `search.log`, or `reembed.log`.

## What the push did not change

Remote `main` remained `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`. Remote `vsl-implementation` remained `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. Voyager was not merged into either branch.

## What remains local

The files in `EXCLUDED_ARTIFACTS.md`: both memory-clone directories, the identity sidecar, the two diagnostic logs, the bytecode, and the three `.human_token` fixtures. They are still on disk in the Voyager worktree.

## This file

This status file was written after the package commit was confirmed on the remote. Its own commit is a second, fast-forward update of `project-voyager`. The final mission report records that second SHA once the remote confirms it. This file does not rewrite the package commit.
