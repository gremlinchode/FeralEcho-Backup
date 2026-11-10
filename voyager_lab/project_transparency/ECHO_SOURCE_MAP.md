# Source map

Paths are relative to this directory (`voyager_lab/project_transparency/`). A path that begins with `../` is still inside `voyager_lab/`. A path that begins with `../../` is in the worktree root.

Hashes in this file were recomputed with `shasum -a 256` during this writing pass, read-only, on 2026-11-08 session calendar. They matched the hashes already cited in `MASTER_INVESTIGATION_INDEX.md` and `MASTER_PROJECT_HISTORY.md`. Recomputation is not a new experiment.

This map does not copy evidence bodies. Secret fixture lines are not repeated here.

## Package files

| Document | Role |
|---|---|
| `MASTER_PROJECT_HISTORY.md` | Chronology and boundaries. |
| `MASTER_INVESTIGATION_INDEX.md` | Inventory, twelve-field campaign records, the 13-claim table, E-001–E-038 as index-reported. |
| `ECHO_CAPABILITY_ASSESSMENT.md` | Categories A–H and the same 13 claims. |
| `ECHO_PROJECT_BRIEFING.md` | Echo-facing briefing. |
| `ECHO_SOURCE_MAP.md` | This file. |
| `ECHO_COMPREHENSION_EXERCISE.md` | Questions and answer key. Not administered. |
| `FINAL_AUDIT_REPORT.md` | Coverage, limits, access states. |
| `MANIFEST.sha256` | Hashes of the seven Markdown files. The manifest does not hash itself. |

## Claim to source

| Claim | Label | Primary source | Supporting source |
|---|---|---|---|
| V1, V2, V3, V4 | See index | `../ASSESSMENT.md` | `../results/summary.json`, `../voyager/procedures.py`, `../voyager/engine.py`, `../voyager/worker.py`, `../README.md` |
| V5 | PROPOSED ONLY | `../CAB_ADVERSARIAL_REVIEW.md` | Executive verdict. Middle sections 2–10 were not fully re-read. |
| S1, S2, S3 | See index | `../scratch_write/SECURITY_REPORT.md` | Evidence JSON and code hashes below. |
| R1, R2 | See index | `../UNGATED_FILE_RETRIEVAL_REPORT.md` | `../UNGATED_FILE_RETRIEVAL_POSTMORTEM.md`, `../ungated_file_retrieval/summary.json` |
| Q1 | EXPERIMENT NOT COMPLETED | `../REASONING_RELIABILITY_REPORT.md` | `../reasoning_reliability/summary.json`, `../reasoning_reliability/protocol.json` |
| L1 | UNKNOWN | Search recorded in the index. No transcript file. | Do not substitute L2. |
| L2 | PARTIALLY DEMONSTRATED | `../../audits/2026-09-02_architectural_self_knowledge_investigation.md` section 6.A | Production tool definition: `../../app/core/echo_tool_dispatch.py` |

## Frozen Voyager objects

Recomputed SHA-256:

| Path | SHA-256 |
|---|---|
| `../voyager/engine.py` | `8ddc23b64bcdff997b307df3c6be7c8d4167dfd18bcafff0293df19c33b63cf3` |
| `../voyager/worker.py` | `3695250e882dae67a133aee477d95db5d95de5ef29531b1efd65656add49d8c6` |
| `../results/summary.json` | `7bdc1d4311701883aecfd6d62815f17046a9252c4f5641e91e8029e3bf2d761d` |

Rubric bundle hash, as recorded in `../README.md` and quoted in `MASTER_PROJECT_HISTORY.md`: `b8b1bc1fe7056294739bd834c3e4329807b50ef6cdffab67f68f6e32e2af9b9d`. This writing pass did not reassemble that bundle. It confirmed the history file still cites that string. There is no second summary at `voyager_lab/voyager/results/summary.json`.

`../README.md` states that `run_experiment.py --run` refuses when `../results/summary.json` or `../results/raw/` already exists. The grammar note is in `../voyager/procedures.py`: fixed procedures, not a language-model reading of free text. `join_pair` reads two slots, joins them, and writes.

## ScratchWriter hashes

Code and reports, recomputed:

| Path | SHA-256 |
|---|---|
| `../scratch_write/pinned_writer.py` | `285b05521916770ab798d07df29f0c44c51d8f256c81c9b870dc31ff3d0e830a` |
| `../scratch_write/confine.py` | `f7520a948f5f11ce42958aa11d81b76a18e2bc52eb0d94eb637e42d4ece4b0f2` |
| `../scratch_write/write_file.py` | `897454a5169fa7922c270eb2f117c0c354847fb27ca8337688708251893184b9` |
| `../scratch_write/verify_file.py` | `638e589ba3bcec9aa738a4d50dd781bf504660df7a5408ea509614d4e094069d` |
| `../scratch_write/tests/test_scratch_write.py` | `880eb11218cc174a227159f0e384968f64d2e9bc35200f436ae81b99f1eab1db` |
| `../scratch_write/tests/test_pinned_writer.py` | `30c0385356c8e32f9735a14685e5c75a6a5e1f77260f14a4969bf37dc8ec74eb` |
| `../scratch_write/SECURITY_REPORT.md` | `48a674d902a773c10fdc711d7c717f1a7dc54c09e5852e58a85bd156c7d38ac0` |
| `../scratch_write/IMPLEMENTATION_AND_VERIFICATION_REPORT.md` | `61329569f9d049ca2c3e6fd3ef57868986e7b71a1a717f8feec9a01a4259495d` |

Evidence JSON, recomputed. These match the hashes already printed in `MASTER_INVESTIGATION_INDEX.md` section A3.

| Path | SHA-256 |
|---|---|
| `../scratch_write/evidence/scratch_writer_t1.json` | `3f1ca84ef0434129eeba50d17a39fda7c8393c7e483eaf6cffaf5c056a8bb8f0` |
| `../scratch_write/evidence/scratch_writer_t8.json` | `a1f668d7a6f0223875b7d2894365045e6380490642921c4885cb80688868edd6` |
| `../scratch_write/evidence/scratch_writer_t2.json` | `94d183397af92b8f55b22ad71bfa2d379c07dc6e01339374183e93f141c434e5` |
| `../scratch_write/evidence/scratch_writer_t8_scoring_bug.json` | `aa7b85d37e736699104af2b6e95fbeba093f5759cb4bfe90c589cfb7db9be6f2` |
| `../scratch_write/evidence/scratch_writer_t2_scorer_mismatch.json` | `81ab8602fdc63ec514b9cf9a33da2c562d3462989fc0db6243ee95db4544f07e` |

Also present and not re-hashed individually: `../scratch_write/FINAL_SECURITY_DESIGN.md`, `../scratch_write/evidence/MANIFEST.json`, `../scratch_write/evidence/README.md`. The T2 temporary directory was left where the earlier run created it. This audit did not copy, move, or delete it.

## Retrieval and reasoning objects

| Path | SHA-256 | Role |
|---|---|---|
| `../UNGATED_FILE_RETRIEVAL_REPORT.md` | `8b83d601a4a8b1685a45b94c4075c3840ec40b219a0f83249a1b5a4a1f86e3ad` | Official retrieval report. Does not itself contain `finished_at`. |
| `../ungated_file_retrieval/summary.json` | `e21b738c13d04b4b26f55dea6152e6138456432fa16f99e9f60787c904768d97` | `finished_at` `2026-11-09T04:34:13.761873+00:00`. |
| `../REASONING_RELIABILITY_REPORT.md` | `ee3830b5e92a886420dc0e3ee0264a38fcfe5bc5ac48e3d637ecfef0b4834f0a` | Official reasoning report. |
| `../CAB_ADVERSARIAL_REVIEW.md` | `aceab7c557c8b1860c60572d59ccc266fc55a77310a79a255e0c83e6c5aaf6bf` | CAB rejection. |
| `../reasoning_reliability/protocol.json` | `e48a01336daed49a08fa05e9332dfadb50861e92b7917e5c802f45210ac020ea` | Frozen protocol. |
| `../reasoning_reliability/problems.json` | `68d3b820b4fd211495be354593d9d714befb4f0098f56c5af6aaa38bd7f42fcb` | Frozen problems. |
| `../reasoning_reliability/grader.py` | `fa707a9abad7a072600c92fda6ec45c57e2c401004bcc7f6eebd69e61e2fb080` | Frozen grader. |
| `../reasoning_reliability/harness.py` | `017e7bf077d6b5c95c7704514d5dd4ef08711657bab388892a6890b162e69ec7` | Frozen harness. |
| `../reasoning_reliability/summary.json` | `84f1408f498e7447f75af17a8deefc2489d6e3649de02b547deb22e200f070ec` | `finished_at` `2026-11-09T06:07:51.915140+00:00`. |
| `../reasoning_reliability/budget.json` | `2ddd2e178e0914860e36bd4d27eb9c20175594c0629293cc69ee9029a4565138` | Budget record. |
| `../reasoning_reliability/freeze.json` | `91dbc1cc8e4cb1d663af34109e57d84cea31ec4233d83919761d8d27993388f5` | `frozen_at` `2026-11-09T05:17:33.457005+00:00` is the value cited from the report. |
| `../reasoning_reliability/blind_package.json` | `945a9d9146b0a5fd7249734ad9b55b08b5312c5291bacedc05bab5d082c5c289` | Blind package. |
| `../reasoning_reliability/blind_key.json` | `a0027d5af3e695283653cd3ef9ab041ac3bfce385e07d8bce1180a88047a9e3a` | Blind key. |

`../UNGATED_FILE_RETRIEVAL_POSTMORTEM.md` is the stop recommendation. It was not re-hashed in the table above. `../CAPABILITY_GAP_AND_NEXT_EXPERIMENT.md` recommended a retrieval run and stated that the note itself did not authorize one. The later official label supersedes that recommendation as a result.

## Production and research documents this audit used

| Path | Use in this audit |
|---|---|
| `../../ORIGIN.md` | Opening, lines read in an earlier pass of this investigation. Rest of the file was not the basis of new claims. |
| `../../CLAUDE.md` | Documentary history. Findings were not re-executed. |
| `../../PENDING_DECISIONS.md` | 2026-11-02 independence bar not met. Lock stays off. Project stays private. |
| `../../app/core/echo_tool_dispatch.py` | Tool names, project-root guard, thought-log path. Not invoked. |
| `../../research/EXPERIMENT_INDEX.md` | Full index read. Source of E-001–E-038 summaries. |
| `../../research/CURRENT_STATE.md` | Secondary summary. Not re-executed. |
| `../../research/FINDINGS.md` | R-001–R-011 as secondary summary. Not re-executed. |
| `../../research/OPEN_QUESTIONS.md` | Headings Q-001, Q-002, Q-008, Q-003, Q-004, Q-005, Q-006, Q-009, Q-007, Q-010. Bodies mostly unread. |
| `../../audits/2026-09-02_architectural_self_knowledge_investigation.md` | Section 6.A paragraph only, for L2. |
| `../../audits/2026-07-18_echo_self_awareness_probe.md` | Searched for `log_thought`. No hit in that search. |

## Git objects

Worktree: `/Users/richietate/Desktop/FeralEcho-voyager`. Branch: `project-voyager`. HEAD cited throughout this package: `dc8d6eb9b6479ef323614cd6820bb050a14299eb`. Remote: `git@github.com:gremlinchode/FeralEcho-Backup.git`.

`MASTER_PROJECT_HISTORY.md` section 6 lists further commits from `git log`. Those messages are chronology. This map does not treat a commit message as a re-verified test.

Branches named in the index: `main`, `project-voyager`, `vsl-implementation`, `worktree-agent-abe6ecca0408fd0fb`. `vsl-implementation` was not reviewed. The other worktree was not touched. `gh issue list --limit 5 --state all` returned no rows. Pull requests and any other GitHub repositories were not listed.

## Located and not used as new results

`../FIRST_LOCAL_SKILL_RESEARCH.md`, `../CAPABILITY_ACQUISITION.md`, and `../RUBRIC_FREEZE.json` exist. The first two bodies were not re-read. They are not extra PROPOSED ONLY rows.

Unread research bodies are listed in `MASTER_INVESTIGATION_INDEX.md` Tier C. Twenty-six directories under `../../app/experiments/` were listed and not assessed. `audits/` held 539 files at the count used in the index. The index author’s header said 185. Both figures stand.

Outside the repo: `/Users/richietate/Desktop/FeralEcho-working-self-design-da499375.md` existed at the existence check (121559 bytes). Body not read. Not hashed again in this pass. Not an implementation.

## Glossary

| Term | Meaning in this package |
|---|---|
| DEMONSTRATED | The cited test measured the claim, and the result matched that claim. |
| PARTIALLY DEMONSTRATED | A real result exists, and it covers only the narrower claim named in the table. |
| NOT DEMONSTRATED | The study ran, or the architecture was inspected, and the broader claim does not hold on that evidence. |
| EXPERIMENT NOT COMPLETED | The study started and did not meet its own completion rule. The hypothesis is not decided. |
| FAILED | The mechanism was tested against the property it claimed and did not provide that property. |
| UNKNOWN | The evidence needed for the claim was not found, or the cause was not established. |
| PROPOSED ONLY | A design or review exists. The mechanism was not added to the running system by that work. |
| DOCUMENTED | A source file contains the information. |
| PACKAGED | This directory organizes it for a reader. |
| ACCESSIBLE | An existing authorized Echo mechanism can retrieve it. Not established for this package. |
| DELIVERED | Echo was actually given the material. |
| ACKNOWLEDGED | Echo responded to the material. |
| VERIFIED UNDERSTANDING | Echo answered source-grounded questions accurately. One reply is not permanent learning. |
| Controller | Python, a grader, a pass rule, a keyword gate, or a prewritten procedure. Not the language model. |
| Model-native | Behavior the evidence assigns to the language model rather than to those controllers. |
| Voyager M19 / M20 | Missions in the frozen 25-mission suite. |
| E-036 / E-037 | September research Mission 19 and Mission 20. Different studies. |
| R2 versus R1 | Tool call and file bytes, versus the official exact-line answer. |
| Learning label `none` | The Voyager record’s own mark that M19 did not store a new lesson. |
| Index-reported | Taken from `research/EXPERIMENT_INDEX.md` and not re-opened. |
| Documentary | Taken from `CLAUDE.md` or a research summary and not re-watched on the live server. |

## Access pointer

`../../app/core/echo_tool_dispatch.py` keeps `read_file` under the process project root (`_PROJECT_ROOT`, set by `_find_project_root()`). This package is not in the production checkout. Whether a live process could read it was not tested. The human supplies the briefing until a later check shows otherwise. Details: `FINAL_AUDIT_REPORT.md`.
