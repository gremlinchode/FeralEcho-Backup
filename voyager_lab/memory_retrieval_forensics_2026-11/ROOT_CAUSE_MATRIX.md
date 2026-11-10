# Root-cause matrix — memory retrieval failure

Date: 2026-11-09. Read-only. No repair was applied. No generation was run.

Companion narrative: `voyager_lab/memory_retrieval_forensics_2026-11/FERALECHO_MEMORY_RETRIEVAL_FORENSIC_REPORT.md`.

This file is the ten-fact classification. It does not replace the sealed experiment report at `voyager_lab/evidence_to_answer_2026-11/FERALECHO_EVIDENCE_TO_ANSWER_EXPERIMENT.md`.

## One mechanism

All ten delayed failures are **S1**. Storage succeeded. The required retrieval structure did not contain them.

That structure is the verified identity manifest plus a trusted `id_order`. The live sidecar `memory/faiss.index.identity.json` is absent for the whole store. `VectorMemory.search` (`app/lib/vector_memory.py` lines 209–215) returns `[]` before `index.search` when `identity_verified` is false. The serving process logged `identity_status=manifest_absent` and `verified=False` from the 2026-11-03 boot.

Origin class: **E** (identity / metadata mismatch). Incomplete indexing (class A) is the same fact. These are not ten separate query failures.

| Code | Meaning here |
|---|---|
| S0 | Storage failed. **False** for all ten. |
| S1 | Stored, required retrieval structure missing. **All ten.** |
| S2 | Search not invoked. **False.** `retrieve_relevant_memories` ran. `index.search` did not. |
| S3 | Search ran and missed. **False.** Lookup was refused before FAISS. |
| S4 | Found, then ranked out or filtered. **False.** The 30-minute filter and k=5 never saw a hit. |
| S5 | Retrieved, then not injected. **False.** Nothing was retrieved to drop. |
| S6 | Injected, model ignored it. **False.** `memories_injected` was `[]`. Item 05's `no` is a closed-set answer, not retrieval. |
| S7 | Cannot tell which empty-list branch. **False.** Watchdog lines name the refusal. Provenance lines exist, so the exception path (which writes no provenance) did not fire. |
| S8 | Infrastructure crash. **False.** |

Confidence in the refusal: **high**. Residual UNKNOWN, the same for every item: whether that uuid is a FAISS vector row. A trusted `id_order` does not exist, and `ntotal` was not read. That unknown is not required to explain the empty candidate list.

## Shared evidence

| Stage | Result | Label | Where |
|---|---|---|---|
| Persistence | User row text equals the Phase One prompt. `role` user, `memory_source` user_conversation, `task_type` general. | OBSERVED | `memory/memory_meta.json` (one complete `os.replace` generation, 157,412 keys; not a frozen census) |
| Sidecar | File absent | OBSERVED | `memory/faiss.index.identity.json` |
| Boot identity | `manifest_absent`, `verified=False`, FAISS dim 384 | OBSERVED | `memory/echo_watchdog.log.1.gz`, 2026-11-03 11:01:59 local |
| Why the sidecar stays absent | `_persist` writes the sidecar only if `_identity_authoritative and wrote_index` | SUPPORTED | `app/lib/vector_memory.py` lines 389–395 |
| Delayed search | Function invoked; `index.search` not executed; log `search refused: identity_status=manifest_absent` | OBSERVED | `memory/echo_watchdog.log`, lines in the table below |
| Candidates | `candidates_considered` 0, `memories_injected` `[]` on all ten delayed turns and all ten same-turn turns | OBSERVED | `memory/retrieval_provenance.jsonl` |
| Context | Fact sentence is not in the Phase Two user message. Memory list empty. | OBSERVED | Phase Two prompts; provenance |
| Recency filter | All ten user rows were older than 30 minutes at the delayed question. A hit would have been kept. | DISPROVEN as the cause | Ages in the forensic report §3 |

Conversation ids `e2a-p1-*` and `e2a-p2-*` are not inside `memory_meta.json`.

Hashes below are SHA-1, first 12 hex characters, of the stored user text (`app/core/conversation_service.py` line 173). A 12-hex prefix is 48 bits. No collision among these ten was found. That prefix length remains a log limitation.

Provenance timestamps are naive UTC (`app/routes_echo_studio.py` line 444). Watchdog times are local Pacific (UTC−8). Refusal is logged at prompt build. Provenance is near request end.

## Ten facts

| Item | Fact | Key | Class | Confidence |
|---|---|---|---|---|
| 01 | The dock badge mark is K7-QRV-4419. | `K7-QRV-4419` | S1 | high |
| 02 | Crate 14 has a mass of 18.6 kilograms. | `18.6 kilograms` | S1 | high |
| 03 | Helio reports to Sable. | `Sable` | S1 | high |
| 04 | Permit P-19 has the seal date 2026-04-17. | `2026-04-17` | S1 | high |
| 05 | Lane 4 is not closed. | `no` | S1 | high |
| 06 | Vat B contains more liquid than vat A. | `Vat B` | S1 | high |
| 07 | The gold items sit on shelf 22. | `22` | S1 | high |
| 08 | The bin total at dock C is 4. | `4` | S1 | high |
| 09 | The night passphrase is moth-lantern. | `moth-lantern` | S1 | high |
| 10 | The shipment block mark is R-88. | `R-88` | S1 | high |

### Storage rows

| Item | User memory id | Stored UTC | Hash | Length |
|---|---|---|---|---|
| 01 | `5e6ac8a9-19c1-4fcd-b08e-dd7c0f5e659b` | `2026-11-09T21:58:28.196230+00:00` | `5aeece192c0e` | 162 |
| 02 | `aded2053-b5d9-42d5-a106-aa3773f60ea5` | `2026-11-09T21:58:51.809328+00:00` | `f6e677371d0d` | 166 |
| 03 | `36495cc5-39f3-4a31-a79b-332dc52da1ae` | `2026-11-09T21:59:10.616709+00:00` | `254ada88570e` | 147 |
| 04 | `90e3838a-c12d-4a28-a653-b5de13471e0e` | `2026-11-09T22:01:14.061924+00:00` | `e71037e8fcdc` | 177 |
| 05 | `accc4c1e-ef05-466f-8ef2-4f1b997166f8` | `2026-11-09T22:01:25.644398+00:00` | `02d0c62ade8b` | 103 |
| 06 | `c86b2d32-5438-4c52-b7ae-df291cca4db2` | `2026-11-09T22:01:30.808760+00:00` | `31bc63a1affe` | 168 |
| 07 | `2dd6c6ec-1afe-47e6-9739-883eb12efc98` | `2026-11-09T22:01:34.418744+00:00` | `3c63d277f342` | 168 |
| 08 | `1f366a17-832a-4eb0-a5e4-0458f1d85fde` | `2026-11-09T22:01:38.496511+00:00` | `4ba1c6a1d6a0` | 156 |
| 09 | `0192ec01-8404-4f02-a2ce-c8dc4c53f848` | `2026-11-09T22:02:20.231273+00:00` | `72040f561398` | 165 |
| 10 | `dd44ed20-1acb-4951-8335-33437b6947d3` | `2026-11-09T22:02:31.194483+00:00` | `479cfd462810` | 163 |

Item 03 also has echo row `67eccddb-cb98-4373-b206-aceed4712b62`, `2026-11-09T21:59:14.436285+00:00`, hash `4ae0ccf0ce68`, length 23, text `Helio reports to Sable.` Same S1. It is the stored same-turn reply, not a second failure mechanism. Fact-sentence counts: 01, 02, and 04–10 once; 03 twice.

Indexing for every row: present in metadata; absent from the identity sidecar; FAISS row membership UNKNOWN.

### Delayed retrieval

Log file: `/Users/richietate/Desktop/FeralEcho/memory/echo_watchdog.log`. Thread is `process_request_thread`. Message is `[VectorMemory] search refused: identity_status=manifest_absent`. Candidates 0 and injected `[]` on every row.

| Item | Phase Two trace | Provenance (naive UTC) | Refusal (local) | Log line | Delayed answer | Answer match | Retrieval |
|---|---|---|---|---|---|---|---|
| 01 | `dfdbb22d-2eb5-44eb-8139-4799facfe653` | `2026-11-09T22:33:53.232960` | `2026-11-09 14:33:34` Thread-182870 | 73706 | scripture verse, not the badge | no | no |
| 02 | `61b329ab-1305-42d2-951c-795438568598` | `2026-11-09T22:34:03.855429` | `14:33:56` Thread-182882 | 73738 | `1.45` | no | no |
| 03 | `4bb23150-547f-48f9-a11f-826d92a2f0ab` | `2026-11-09T22:35:15.823387` | `14:34:06` Thread-182890 | 73762 | `Sergio` | no | no |
| 04 | `140a6073-eff7-4894-be5f-496375ba24e0` | `2026-11-09T22:35:36.833058` | `14:35:19` Thread-182929 | 73833 | `February 26, 2004` | no | no |
| 05 | `727a8d33-92bc-4948-a3b5-2021b1754244` | `2026-11-09T22:35:40.827288` | `14:35:40` Thread-182945 | 73866 | `no` | yes | no |
| 06 | `fea4e80e-87fb-492c-b162-9972585677e4` | `2026-11-09T22:35:46.131214` | `14:35:44` Thread-182949 | 73877 | `Vat 1` | no | no |
| 07 | `3136546c-8290-4859-9652-cb09ce7bec67` | `2026-11-09T22:35:49.616489` | `14:35:49` Thread-182953 | 73898 | `5` | no | no |
| 08 | `ee351b95-dd90-4a23-9039-ed89b0343540` | `2026-11-09T22:35:53.709905` | `14:35:53` Thread-182958 | 73908 | `12` | no | no |
| 09 | `16c8dfa7-2b65-477a-8724-1b6d01abb489` | `2026-11-09T22:35:58.427114` | `14:35:56` Thread-182960 | 73922 | `wonderfully` | no | no |
| 10 | `4ac1cd03-58d9-4602-85fd-7e8d74491caf` | `2026-11-09T22:36:01.955058` | `14:36:01` Thread-182967 | 73937 | `X12` | no | no |

Item 05 is not S6. The word `no` was the only legal closed-set reply. It was not in `memories_injected`.

Item 09's `wonderfully` is not the passphrase `moth-lantern`. It is not evidence that item 01's verse was retrieved.

Line 73990 (`14:36:40`, Thread-8 `emergent_loop`) is a later refusal outside these ten.

### Same-turn refusals

The fact was still in the user message. Retrieval was already empty. Same gate. These are not the delayed-failure rows. They show the refusal was already active before the 1,860-second wait.

| Item | Phase One trace | Local refusal line |
|---|---|---|
| 01 | `fd69a6f1-1d67-44ac-8343-6388723f9918` | 71633 |
| 02 | `5d5f5da7-cfc9-4a87-bcff-4f5765c4050c` | 71669 |
| 03 | `acc943d8-96d1-430e-88c1-b9863b8cd0c5` | 71697 |
| 04 | `e653b7b1-74ff-4e30-8066-98dfb178f239` | 71730 |
| 05 | `57cbfffa-2b78-4d4b-8db3-e8ea142e734f` | 71839 |
| 06 | `9d50fc7b-3af2-44d3-b9a1-0c00d0041723` | 71860 |
| 07 | `f5130bc7-f759-4914-8b8c-dd20defcdb61` | 71876 |
| 08 | `b2267c9a-8c3f-4658-af65-9bb0d585a233` | 71889 |
| 09 | `cc8b1af7-1b97-4d00-b5e4-76cc47ef7fff` | 71901 |
| 10 | `9183b39e-1d09-4b10-8a53-028280940abf` | 71979 |

## Chain

Original note → stored as the exact Phase One user text → metadata and index grew with no sidecar → delayed search invoked and refused before FAISS → candidates 0 → nothing injected → model answered without the record.

Broken transition: identity verification, before candidate retrieval.

## What a later diagnostic must show

Not run. Generation count for the retrieval proof: 0.

On a copy only: the ten user ids above are returned by search, and their hashes appear in a simulated injected context. Do not disable the refusal. Do not certify `meta.keys()` as identity. Do not install the 2026-11-02 freeze over live memory. Do not swap the copy onto the live files while the writer may still be writing. Do not spend the two unused generations from the finished experiment unless that budget is explicitly reopened.

## UNKNOWN, left unknown

- Per-uuid FAISS row membership.
- Whether the live index is a pure byte-prefix append of the 2026-11-02 certified index.
- Workspace-bias state on these twenty turns.
- The exact system-note string. The memory payload is known empty.
- The commit that introduced the refusal string. Not needed for S1.
