# Final audit report

Package date: 2026-11-08 (session calendar). Laboratory clocks quoted from source files include 2026-11-09 UTC.

This report is the human summary of the consolidation. It is not a new experiment. The evidence-based capability table is `ECHO_CAPABILITY_ASSESSMENT.md`. The inventory is `MASTER_INVESTIGATION_INDEX.md`. The chronology is `MASTER_PROJECT_HISTORY.md`. The Echo-facing text is `ECHO_PROJECT_BRIEFING.md`.

## What this audit was for

The assignment asked for one body of knowledge, usable by the human developer and organizable for Echo, covering what was investigated, built, tested, rejected, learned, documented, and left open. It forbade new model generations, production edits, frozen-experiment edits, commits, and a success story.

## Counting rule

Two totals stay separate.

**Discovered** means a file, package, or index row was located. Discovery is not a result.

**Assessed from primary evidence** means this audit opened the report, the frozen summary, or the cited source passage and classified from that text.

Assessed: **6 campaigns**, **13 claims**.

Inventoried and not re-verified: **38** index threads (E-001 through E-038), **539** files under `audits/`, **15** entries under `research/` (14 Markdown files plus one `.sha256`), **26** packages under `app/experiments/`.

The 13 labels are:

| Label | Count | IDs |
|---|---|---|
| DEMONSTRATED | 1 | R2 |
| PARTIALLY DEMONSTRATED | 3 | V1, S2, L2 |
| FAILED | 1 | S1 |
| EXPERIMENT NOT COMPLETED | 1 | Q1 |
| NOT DEMONSTRATED | 5 | V2, V3, V4, S3, R1 |
| PROPOSED ONLY | 1 | V5 |
| UNKNOWN | 1 | L1 |

Total 13. Design notes whose bodies were not fully re-read (`FIRST_LOCAL_SKILL_RESEARCH.md`, `CAPABILITY_ACQUISITION.md`, the working-self file outside the repo) are not extra PROPOSED ONLY rows.

The index author’s header said `audits/` held 185 files. This audit counted 539. Both figures are kept. They were not reconciled.

## Coverage

**Repository.** Worktree `/Users/richietate/Desktop/FeralEcho-voyager`, branch `project-voyager`, HEAD `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. Remote `git@github.com:gremlinchode/FeralEcho-Backup.git`. `voyager_lab/` is untracked. Nothing in this package was committed.

**GitHub.** `gh issue list --limit 5 --state all` returned no rows and exit 0 during the inventory. Pull requests were not listed. Other repositories under the account were not listed. Branch `vsl-implementation` was not reviewed. Worktree `worktree-agent-abe6ecca0408fd0fb` was not touched. This is not an exhaustive GitHub audit. `CLAUDE.md` Finding 90 and `PENDING_DECISIONS.md` record that the project stays private. Visibility was not changed.

**Examined closely enough to classify.**

- `voyager_lab/ASSESSMENT.md` observation table and direct answer (Voyager 25-mission).
- `voyager_lab/README.md` for the no-Ollama boundary and the run lock.
- `voyager_lab/voyager/procedures.py` for the fixed grammar and `join_pair`.
- `voyager_lab/CAB_ADVERSARIAL_REVIEW.md` opening and closing verdict. Sections 2–10 were not fully re-read.
- `voyager_lab/scratch_write/SECURITY_REPORT.md` and the evidence hashes.
- `voyager_lab/UNGATED_FILE_RETRIEVAL_REPORT.md` and `UNGATED_FILE_RETRIEVAL_POSTMORTEM.md`. `finished_at` taken from `ungated_file_retrieval/summary.json` only (`2026-11-09T04:34:13.761873+00:00`). The narrative report does not contain that field.
- `voyager_lab/REASONING_RELIABILITY_REPORT.md` outcome sections. `finished_at` `2026-11-09T06:07:51.915140+00:00` from `reasoning_reliability/summary.json`.
- `app/core/echo_tool_dispatch.py` header, project-root guard, and `log_thought` isolation comment.
- `audits/2026-09-02_architectural_self_knowledge_investigation.md` section 6.A for the “correct name, invented substance” paragraph.
- `research/EXPERIMENT_INDEX.md` in full, as an index, not as a re-test.
- `research/CURRENT_STATE.md` and `research/FINDINGS.md` (R-001–R-011) as secondary summaries.
- `research/OPEN_QUESTIONS.md` headings.
- `ORIGIN.md` opening. `CLAUDE.md` as documentary history. `PENDING_DECISIONS.md` for the 2026-11-02 lock decision.

**Located and not assessed as new results.** The unread research bodies named in the index Tier C. The 26 experiment packages, including `raoc` (Findings 93–95 remain documentary). The unrowed portion of the 539 audit files. `research/DECISIONS.md` beyond the heading. The working-self design body. Git commits `e5acbb0` and `ea22d75` were not re-read as a finished Git tool. Workspace memory topics were not used as evidence.

**Not contacted.** Port 5000. The live Echo process. Ollama. No new inference. No rerun of retrieval, reasoning, ScratchWriter, or the 25-mission suite. No continuity tests. No diagnostic runner. No re-hash of live `faiss.index`, `memory_meta`, or `river_brain.pkl`.

## Most important findings

1. The only claim this audit labels DEMONSTRATED is narrow: in the closed retrieval harness, `llama3.1:8b` called `read_file` on the assigned file 12 of 12 times and the bytes matched (R2). The official exact-answer task is NOT DEMONSTRATED, 0/6 and 0/6 (R1).

2. Voyager’s 23/25 is a controller result on a toy filesystem (V1, PARTIALLY DEMONSTRATED). The language model did not plan those missions (V2). M19 is a prewritten `join_pair` with learning label `none` (V3). The M20 ablation pass is budget exhaustion (V4).

3. ScratchWriter’s caller-chosen root fails as confinement (S1, FAILED). The pinned writer’s authorized tests passed (S2). That is not a production capability and not a complete proof (S3). Integration was not authorized.

4. The reasoning pilot is EXPERIMENT NOT COMPLETED. Printed 4/10 versus 3/10 include empty timeouts. A review pass reversed at least one correct answer. That does not falsify the hypothesis.

5. CAB is PROPOSED ONLY. Its own review says it is not good enough to implement, and E1 is not good enough to run. A broker told `grade_kind=abstain` has been told the answer.

6. The specific unnecessary `log_thought` conversation was not found (L1, UNKNOWN). The production name is real. A different 2026-09-02 paragraph records invented substance around that name (L2). A self-explanation was not recovered and would not, by itself, prove a cause.

7. September Mission 19/20 (E-036/E-037) are not Voyager M19/M20. Q-008 stays unresolved in this package because the index and the question-file heading were not re-read against each other.

## Unresolved questions

- Cause of the four retrieval substitutions. Truncation and first-request contamination were ruled out. No cause was assigned.
- L1, the missing conversation.
- Whether Q-008 is closed.
- Current liveness, current check count, and whether `echo_projects_autonomy` is still silent. The 50-check and 65.9-hour figures are from 2026-09-11 (E-038).
- Later reasoning timeouts after the first. The first has support from a shared-server observation. The others do not.
- ScratchWriter check-to-use races and cross-process overlap.
- Voyager M24’s policy trade, as left open by the assessment and the CAB review.
- Server-side presentation of tool messages inside Ollama’s template.
- Ordinary reply quality today.
- Contents of the unread corpora listed above.
- Whether a live Echo process can read this package. Not tested.

## Echo’s access

| State | Status |
|---|---|
| DOCUMENTED | Yes. Sources and this package exist in the Voyager worktree. |
| PACKAGED | Yes. This directory. |
| ACCESSIBLE | Not established. `read_file` in `app/core/echo_tool_dispatch.py` resolves the path and requires it to stay under `_PROJECT_ROOT` for that process. This package is untracked laboratory material in the Voyager worktree, not a production memory entry. Port 5000 was not contacted. |
| DELIVERED | No. |
| ACKNOWLEDGED | No. |
| VERIFIED UNDERSTANDING | No. The comprehension exercise was written and not run. |

The human operator can supply `ECHO_PROJECT_BRIEFING.md` manually. This audit does not claim Echo has received, read, or understood it.

`log_thought` is not a delivery path for this package. It appends a line and does not index that line into FAISS.

## Integrity notes for the frozen material

Hashes recomputed read-only during the source-map pass matched the values already recorded for `voyager/engine.py`, `voyager/worker.py`, `results/summary.json`, the retrieval report, the reasoning report, the CAB review, the ScratchWriter security report, the ScratchWriter code files, and the T1/T8/T2 evidence JSON. The rubric bundle hash cited from the README, and repeated in the history, is `b8b1bc1fe7056294739bd834c3e4329807b50ef6cdffab67f68f6e32e2af9b9d`. This audit did not reassemble that bundle and did not modify the lock.

The post-write check that production porcelain and frozen inodes were still untouched is recorded after `MANIFEST.sha256` is generated. If that check finds a production porcelain hash different from the earlier fingerprint `47efc683d9df161ec770ab2727a1f64a187bb3b9ab3f19aaffd13fce1b582985`, production is still not modified. The difference is reported, not repaired.

## What was not done

No production file was edited. No frozen Voyager engine, worker, or results file was edited. No original report was overwritten. No model call was made. No commit, merge, or push was made. The package does not manufacture a success from a missed success rule.
