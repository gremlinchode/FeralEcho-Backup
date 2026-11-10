# FERALECHO — Evidence-to-Answer Experiment

Window: 9 November 2026. Isolated directory:
`voyager_lab/evidence_to_answer_2026-11/`.

This report records one bounded experiment. It does not change production Echo, the frozen transparency package, official historical scores, or the sealed protocol.

Labels used below:

- **OBSERVATION** — a value read from a preserved file or from the live listener listing at report time.
- **RETRIEVED EVIDENCE** — content the production retrieval log says was injected for that turn.
- **INFERENCE** — a conclusion that follows from those records under the frozen rules.
- **ASSUMPTION** — none are used as results. Where a step would require one, the cell stays **UNKNOWN**.

Echo did not grade these trials. Scoring rules were sealed before the first POST and were not changed after the replies were seen.

---

## 1. Executive summary

Same-turn evidence use passed the acceptance gate.

**OBSERVATION.** Ten completed `echo:latest` replies, mode `fast`, scored **8 correct**. `phase1_scores.json` and `run_meta_phase1.json` both record `completed=10 correct=8 gate=true incomplete=false`.

Phase Two was therefore run, after a 1860-second delay, on all ten facts. No second numeric bar was applied.

**OBSERVATION.** `phase2_attribution.json` records, for every item:

| Column | Result |
|---|---|
| Stored | Yes, 10/10 |
| Retrieved | No, 10/10 |
| Used correctly | Yes on item 05 only; No on the other nine |

**INFERENCE.** Storage succeeded and the answering model was not given the stored fact. That is Outcome C for the storage/retrieval break, on all ten items. Utilization is a separate column: 1/10. Item 05’s correct word `no` sits in an empty retrieval list, so it is a closed-set reply, not evidence that the fact was retrieved.

This is not Outcome E. Outcome D would require retrieval to succeed. The three columns stay separate.

Budget used: **20 of 22** generations. Contingency used: **0**. No infrastructure failure. No retry of a wrong answer.

---

## 2. Verified baseline evidence

These figures are historical. They are not this experiment’s score. They were not merged, and their scoring rules were not reused.

| Evaluation | Figure | Source read for this report |
|---|---:|---|
| R2 assigned-file retrieval | 12/12 | Twelve `"bytes_ok": true` lines in `voyager_lab/ungated_file_retrieval/summary.json` (lines 55, 96, 137, 178, 219, 260, 301, 342, 383, 424, 465, 506). |
| R1 official answer | 0/12 | Same file, `scores.A` 0/6 ran 6, plus `scores.B` 0/6 ran 6. |
| Condition C exact | 0/6, separate | `scores.C` exact_answers 0, ran 6. Not added into the 0/12. |
| Condition D | not an echo:latest result | `scores.D` planned 6, ran 0, score string `0/6`. D06 `record_status` is `not_run`. Prompt text exists in that row and was not reused. |
| September evidence correction | 0/5 corrected raw answers | `audits/2026-09-08_generation_epistemic_FINAL.md` line 9. |
| Sixth raw trial | 0/6 raw-generation, separate tally | Same report, addendum at line 44. Not merged into the 0/5. |
| November open-book sitting | 9 of 14 official first answers | `FERALECHO_NEXT_RESEARCH_PRIORITY.md` line 77. Repair rounds at lines 86 and 88 are recorded there as outside the 9/14. |
| Verified understanding | Not established | Priority document line 77: VERIFIED UNDERSTANDING is false. The November transparency package separately records that its own comprehension exercise was written and not run (`voyager_lab/project_transparency/FINAL_AUDIT_REPORT.md`). Those are two records. They were not combined into one score. |

**OBSERVATION.** `summary.json` `finished_at` is `2026-11-09T04:34:13.761873+00:00`. The generation report names commit `9de04a3944f0f0ad38c970f51fde3edd845312a4` as the HEAD it left unchanged. This write-up did not treat that string as today’s HEAD.

**OBSERVATION.** The harness model named for the byte path in the priority document is `llama3.1:8b`, laboratory only. `summary.json` `availability.present` includes both `echo:latest` and `llama3.1:8b`. The R1 answer rows inspected for D06 are tagged `model: echo:latest`, and D06 did not run.

**OBSERVATION.** `audits/2026-09-30_feralecho_strategic_research_audit.md` line 518 states that no inference or experimental trial was run in that mission. DO NOW item 3 (line 528) is a recommendation to run a comparison later. It is not a score.

**Limitation.** This write-up re-read the files named above. It did not reopen `generation_epistemic_validation.md`, the Skill A JSON, or the `mechanism_c` trials. The 9/14 figure is the priority document’s official statement. This write-up did not rescore that sitting.

---

## 3. Frozen experimental protocol

Sealed before any POST, mode `0o444`, and re-checked with `shasum -a 256 -c PROTOCOL.sha256` while writing this report. All five files: OK.

| File | SHA-256 |
|---|---|
| `answer_key.json` | `44bb67820409c564ba6e2c3e8218a6b5f0c847986d1be812b6f2d270088d43ca` |
| `items.json` | `9254da669fa6c80594bb5be04282e7af63b74d060dd559d1d33f65f74fa61695` |
| `preflight.py` | `c945a16fc4c9bce87b50971d1eb761d6c486a6d5876957cc5342a823b40e8f06` |
| `PROTOCOL.md` | `d0321c093be4b913fd5baf0ad369faebb2412f741c48f793234fcac9a94c5557` |
| `score.py` | `e337843ef8a5eb5c09b3ff2ec6ea810e9d9d2963c09499bbc6c02858b9698653` |

`PROTOCOL.sha256` is also mode `0o444`.

Frozen rules that govern the numbers below:

- Exactly 10 completed Phase One replies, and at least 8 correct, are required. Fewer than 10 completed replies is incomplete. Incomplete is not Outcome A and stops Phase Two.
- Score `done.text` only. Strip. Then remove at most one trailing period when the key does not already end with a period and the stripped text ends with exactly one period. Extra words, case mismatch, internal extra whitespace, quotes, and a caveat suffix fail. No partial credit.
- The exact sentence `Error: could not generate a response.` is infrastructure. An empty `done.text` with the done event present is a completed wrong reply.
- Pathway: `POST http://127.0.0.1:5000/chat/stream`, body fields `conversation_id`, `message`, `mode: fast`. Local `echo:latest`. Budget 22, of which 2 are contingency for infrastructure, total, not per item. Every POST counts. A wrong completed answer is not retried.
- Phase Two delay: 1860 seconds after the latest Phase One `finished_at`. New conversation id per trial. The fact sentence is absent from the Phase Two prompt. Unknown remains available for storage and for retrieval. A correct later answer establishes neither storage nor retrieval.
- Outcome A: exactly 10 completed and fewer than 8 correct. Stop. Outcome B: same-turn pass, storage fails. Outcome C: storage succeeds, retrieval fails. Outcome D: storage and retrieval succeed, utilization fails. Outcome E: all three succeed on the tested items. A mixed result stays mixed.

The priority document’s sketch (no-fact controls, tool-use bits, re-ask only the successes, a 4-of-passed delayed bar) was not used. That document says it does not itself authorize generations.

---

## 4. Ten evaluation questions and scoring criteria

Synthetic facts. Each Phase One prompt is `Note: {fact}\n\nQuestion: {question}\n\n{tail}`. Each Phase Two prompt drops the note and uses the Phase Two tail. Item 05 uses the yes/no tail on both phases. Value tail, Phase One: `Reply with only the value. Use the same spelling as the note. Do not add words.` Value tail, Phase Two: `Reply with only the value. Use the same spelling as the earlier note. Do not add words.` Yes/no tail, both phases: `Reply with only the lowercase word yes or no.`

| Id | Fact sentence | Question | Key | Conversations |
|---|---|---|---|---|
| 01 | The dock badge mark is K7-QRV-4419. | What is the dock badge mark? | `K7-QRV-4419` | `e2a-p1-01`, `e2a-p2-01` |
| 02 | Crate 14 has a mass of 18.6 kilograms. | What is the mass of crate 14? | `18.6 kilograms` | `e2a-p1-02`, `e2a-p2-02` |
| 03 | Helio reports to Sable. | Who does Helio report to? | `Sable` | `e2a-p1-03`, `e2a-p2-03` |
| 04 | Permit P-19 has the seal date 2026-04-17. | What is the seal date on permit P-19? | `2026-04-17` | `e2a-p1-04`, `e2a-p2-04` |
| 05 | Lane 4 is not closed. | Is lane 4 closed? | `no` | `e2a-p1-05`, `e2a-p2-05` |
| 06 | Vat B contains more liquid than vat A. | Which vat contains more liquid? | `Vat B` | `e2a-p1-06`, `e2a-p2-06` |
| 07 | The gold items sit on shelf 22. | Which shelf number has the gold items? | `22` | `e2a-p1-07`, `e2a-p2-07` |
| 08 | The bin total at dock C is 4. | How many bins are at dock C? | `4` | `e2a-p1-08`, `e2a-p2-08` |
| 09 | The night passphrase is moth-lantern. | What is the night passphrase? | `moth-lantern` | `e2a-p1-09`, `e2a-p2-09` |
| 10 | The shipment block mark is R-88. | What is the shipment block mark? | `R-88` | `e2a-p1-10`, `e2a-p2-10` |

Item 05 is the only Phase Two closed-set exception. The key `no` appears inside the reply instruction. The fact sentence does not appear in the Phase Two prompt. Keys `22` and `4` do not appear in the Phase Two prompts for items 07 and 08. That was re-checked against `results_phase2.jsonl` for this report.

**OBSERVATION.** Every sent prompt in `results_phase1.jsonl` and `results_phase2.jsonl` equals the matching `phase1_prompt` or `phase2_prompt` string in sealed `items.json`. `phase1_scores.json` records `prompt_matches_frozen: true` on all ten Phase One items.

Full prompt bytes and full SSE-derived replies are in the two JSONL files. SHA-256 of each sent prompt is the `prompt_sha256` field on that row.

---

## 5. Complete raw results

Pathway observation from `run_meta_phase1.json`, taken at Phase One start and not re-queried against Ollama for this report:

- Listener: port 5000 open, PID **65139**, command `python3.1`. At report time `lsof` still showed that PID listening on `*:5000`. The process was not signaled.
- `OLLAMA_MODEL`: `not_in_environment`.
- `/api/show` for `echo:latest`: ok, 30391 bytes, `modified_at` `2026-07-01T00:58:13.426962203-07:00`, family `llama`, parameter size `8.0B`, quantization `Q4_0`, digest null. Parameters string records `num_ctx 8192`, `num_keep 24`, and the three stop tokens `<|start_header_id|>`, `<|end_header_id|>`, `<|eot_id|>`.

Every trial: attempt 1, HTTP 200, `infrastructure: false`, `task_type: general`, one done event, `texts_diverge: false` (`token_text` equals `done_text`), `sse_unparsed: 0`, `counts_toward_budget: true`.

### Phase One

Window: started `2026-11-09T21:57:49.214642+00:00`. Latest trial finished `2026-11-09T22:02:34.185489+00:00` (item 10). Meta file finished `2026-11-09T22:02:34.268411+00:00`.

Memory-save SSE on all ten: user `unknown`, echo `unknown`.

| Id | Trace id | Client finished_at | done.text | Exact |
|---|---|---|---|---|
| 01 | `fd69a6f1-1d67-44ac-8343-6388723f9918` | `2026-11-09T21:58:31.192071+00:00` | `K7-QRV-4419` | Yes |
| 02 | `5d5f5da7-cfc9-4a87-bcff-4f5765c4050c` | `2026-11-09T21:58:54.801096+00:00` | `18.6 kilograms` | Yes |
| 03 | `acc943d8-96d1-430e-88c1-b9863b8cd0c5` | `2026-11-09T21:59:13.773266+00:00` | `Helio reports to Sable.` | No |
| 04 | `e653b7b1-74ff-4e30-8066-98dfb178f239` | `2026-11-09T22:01:17.058365+00:00` | `2026-04-17` | Yes |
| 05 | `57cbfffa-2b78-4d4b-8db3-e8ea142e734f` | `2026-11-09T22:01:29.214961+00:00` | `no` | Yes |
| 06 | `9d50fc7b-3af2-44d3-b9a1-0c00d0041723` | `2026-11-09T22:01:33.820745+00:00` | `Vat B` | Yes |
| 07 | `f5130bc7-f759-4914-8b8c-dd20defcdb61` | `2026-11-09T22:01:37.993891+00:00` | `22` | Yes |
| 08 | `b2267c9a-8c3f-4658-af65-9bb0d585a233` | `2026-11-09T22:01:41.646169+00:00` | `4` | Yes |
| 09 | `cc8b1af7-1b97-4d00-b5e4-76cc47ef7fff` | `2026-11-09T22:02:23.888952+00:00` | `Moth-lantern.` | No |
| 10 | `9183b39e-1d09-4b10-8a53-028280940abf` | `2026-11-09T22:02:34.185489+00:00` | `R-88` | Yes |

Phase One provenance, one line per trace, source `memory_bridge`, `candidates_considered` 0, `memories_injected` length 0. Timestamps on those lines are naive (no offset), for example item 01 `2026-11-09T21:58:28.180500`. The log scan for this report covered 687 lines and 0 unparseable lines, matching `phase2_attribution.json` (`provenance_status: ok`, `provenance_unparseable_lines: 0`).

**INFERENCE.** On these ten same-turn calls the production retrieval log injected no memory block. The pathway is still able to inject one. This run did not.

### Phase Two

Runner started `2026-11-09T22:02:59.801898+00:00` and waited. Delay deadline, latest Phase One finish plus 1860 seconds: `2026-11-09T22:33:34.185489+00:00`. First POST started `2026-11-09T22:33:34.219739+00:00`. Meta finished `2026-11-09T22:36:10.190965+00:00`. Attribute stdout: `attribute=ok`. Exit code 0.

| Id | Trace id | Client started_at | done.text |
|---|---|---|---|
| 01 | `dfdbb22d-2eb5-44eb-8139-4799facfe653` | `2026-11-09T22:33:34.219739+00:00` | see block below |
| 02 | `61b329ab-1305-42d2-951c-795438568598` | `2026-11-09T22:33:56.253537+00:00` | `1.45` |
| 03 | `4bb23150-547f-48f9-a11f-826d92a2f0ab` | `2026-11-09T22:34:06.063856+00:00` | `Sergio` |
| 04 | `140a6073-eff7-4894-be5f-496375ba24e0` | `2026-11-09T22:35:18.905815+00:00` | `February 26, 2004` |
| 05 | `727a8d33-92bc-4948-a3b5-2021b1754244` | `2026-11-09T22:35:39.848652+00:00` | `no` |
| 06 | `fea4e80e-87fb-492c-b162-9972585677e4` | `2026-11-09T22:35:43.859088+00:00` | `Vat 1` |
| 07 | `3136546c-8290-4859-9652-cb09ce7bec67` | `2026-11-09T22:35:49.141442+00:00` | `5` |
| 08 | `ee351b95-dd90-4a23-9039-ed89b0343540` | `2026-11-09T22:35:52.735741+00:00` | `12` |
| 09 | `16c8dfa7-2b65-477a-8724-1b6d01abb489` | `2026-11-09T22:35:56.723764+00:00` | `wonderfully` |
| 10 | `4ac1cd03-58d9-4602-85fd-7e8d74491caf` | `2026-11-09T22:36:01.448165+00:00` | `X12` |

Item 01 `done.text`, exact:

```text
For it was you who formed my inward parts; you knit me together in my mother's womb. I praise you, for I am fearfully and wonderfully made.

**¶**
```

Memory-save SSE: unknown/unknown on every Phase Two item except 02, which is accepted/accepted.

Phase Two provenance: one line per trace, source `memory_bridge`, `candidates_considered` 0, `memories_injected` empty. Query previews start with `Question:`, not `Note:`. Example naive timestamp: item 01 `2026-11-09T22:33:53.232960`. `query_preview_used` is false on every attribution row. The preview was not used as a retrieval substitute.

---

## 6. Phase One score

**8/10 correct. Gate passed. Not incomplete.**

Stdout recorded in `run_meta_phase1.json`: `completed=10 correct=8 gate=true incomplete=false`. Scorer exit code 0. Posts used after Phase One: 10. Contingency: 0.

The two misses are exact-rule misses on completed replies.

- Item 03 key is `Sable`. Reply is `Helio reports to Sable.` After the single allowed period removal the text is `Helio reports to Sable`, which contains words beyond the key.
- Item 09 key is `moth-lantern`. Reply is `Moth-lantern.` After the single allowed period removal the text is `Moth-lantern`, which differs in case.

The other eight `done.text` values equal the keys with no normalization required.

---

## 7. Phase Two results

Phase Two was authorized by the gate. All ten Phase One facts were tested. There was no second pass mark.

| Trial | Stored | Retrieved | Used correctly |
|---|---|---|---|
| 01 | Yes | No | No |
| 02 | Yes | No | No |
| 03 | Yes | No | No |
| 04 | Yes | No | No |
| 05 | Yes | No | Yes |
| 06 | Yes | No | No |
| 07 | Yes | No | No |
| 08 | Yes | No | No |
| 09 | Yes | No | No |
| 10 | Yes | No | No |

Unknown was available and was not needed for these twenty cells. The zero-candidate *mechanism* is Unknown. See section 8.

`storage_contradiction` is false on every item. `retrieval_status` is `ok`. `retrieval_matches` is empty. `used_reason` is `completed`.

Posts after Phase Two: **20**. Contingency: **0**. Two authorized generations remain unused. This report does not spend them.

---

## 8. Separate storage, retrieval, and utilization findings

### A. Storage — Yes, 10/10

The sealed scorer (`score.py` `row_qualifies`) counts a row only when `memory_source` is `user_conversation`, `role` is `user`, the fact sentence occurs in the row text, the timestamp parses as timezone-aware, and the timestamp is at or after the earliest Phase One `started_at`. `scan_complete` true is required; otherwise the cell is Unknown. A correct later answer is not an input to this function.

**OBSERVATION.** One qualifying row per item. `storage_contradiction` false.

| Id | Memory timestamp | text_hash |
|---|---|---|
| 01 | `2026-11-09T21:58:28.196230+00:00` | `5aeece192c0e` |
| 02 | `2026-11-09T21:58:51.809328+00:00` | `f6e677371d0d` |
| 03 | `2026-11-09T21:59:10.616709+00:00` | `254ada88570e` |
| 04 | `2026-11-09T22:01:14.061924+00:00` | `e71037e8fcdc` |
| 05 | `2026-11-09T22:01:25.644398+00:00` | `02d0c62ade8b` |
| 06 | `2026-11-09T22:01:30.808760+00:00` | `31bc63a1affe` |
| 07 | `2026-11-09T22:01:34.418744+00:00` | `3c63d277f342` |
| 08 | `2026-11-09T22:01:38.496511+00:00` | `4ba1c6a1d6a0` |
| 09 | `2026-11-09T22:02:20.231273+00:00` | `72040f561398` |
| 10 | `2026-11-09T22:02:31.194483+00:00` | `479cfd462810` |

**OBSERVATION, this write-up.** SHA-1 hex prefix 12 of each Phase One prompt in `results_phase1.jsonl` equals that item’s stored `text_hash`. The scorer computes the same prefix from the memory row’s text (`hashlib.sha1`, `errors=replace`). The qualifying rule also requires the fact sentence to be inside that text.

**OBSERVATION.** SSE `memory_save` was `unknown`/`unknown` on 19 of 20 turns. Item 02 in Phase Two was `accepted`/`accepted`. Storage Yes still holds because the qualifying rows exist. `_memory_save_pair` in `app/routes_echo_studio.py` returns `unknown` unless the save result is two dicts whose `outcome` is `accepted`, `rejected`, or `failed`. An unknown SSE word is an instrumentation gap here. It is not a missing row.

### B. Retrieval — No, 10/10

**RETRIEVED EVIDENCE.** For each Phase Two trace, the single provenance line has `memories_injected: []` and `candidates_considered: 0`.

The sealed scorer maps an empty injected list with status `ok` to Retrieved No. Zero lines would be Unknown (`missing`). More than one line would be Unknown (`ambiguous`). Neither happened.

Production `retrieve_memory_context` (`app/core/conversation_service.py`) can write that same pair of zeros in two places:

1. `search_fn` returns an empty list.
2. After the 30-minute exclusion, the filtered list is empty.

Both set `candidates_considered` to 0 and `injected` to `[]`. The route writes `injected` out as `memories_injected`. The bare `except` path returns `""` and does not write a provenance line. A line exists for every experiment trace, so that except path did not produce these rows.

**UNKNOWN.** Which of the two zero-candidate branches ran.

Search width is `k * 3` with `k = 5`, so 15 hits, then at most 5 injected. The stored Phase One timestamps are about 33 to 35 minutes before the matching Phase Two provenance timestamps, which is older than the 30-minute exclusion. **INFERENCE.** If a stored fact had been among the hits, its own timestamp would have passed that filter. **UNKNOWN.** Whether it was among the hits. A fact outside the top 15 never reaches the filter. This experiment does not tune `k`. An empty list at `k = 5` is a finding.

Phase Two conversations are new ids (`e2a-p2-*`). The Phase One note is not same-conversation history for those calls.

A short key-only echo reply was not what got retrieved. The injected list was empty. The protocol’s warning about counting a short echo as the fact does not apply to these rows, because no echo was injected.

### C. Utilization — 1/10, scored from the reply alone

The sealed `assess_used` compares the one completed `done.text` to the frozen key. It does not read the retrieval list.

Item 05 matches `no`. The reply instruction already contains the lowercase words yes and no. **RETRIEVED EVIDENCE** for that turn is an empty list. **INFERENCE.** The match is allowed by the closed-set tail. It does not show that “Lane 4 is not closed.” was brought back.

The other nine replies are different strings from the keys: a verse ending in `**¶**`, `1.45`, `Sergio`, `February 26, 2004`, `Vat 1`, `5`, `12`, `wonderfully`, `X12`.

Item 01’s verse contains the word “wonderfully”. Item 09’s reply is that word. They are different conversation ids, and both injected lists are empty. **INFERENCE that item 09 copied item 01 is not supported by the retrieval record.** Whether a scripture block was added to the system note was not checked against the prompt. That cause is **UNKNOWN**.

---

## 9. Failure analysis

Same-turn failures, two items, both completed:

- Item 03 returned the whole fact sentence, including the key, plus a period. The frozen rule requires the key alone.
- Item 09 changed case and added a period. The period rule would leave the capital M in place. Case fails.

Those two were not coached and were not retried.

Delayed failures:

- The fact sentence was in persistent memory for every item (section 8A).
- It was absent from `memories_injected` for every Phase Two turn (section 8B).
- With that empty list, nine answers were unrelated strings. One answer matched a closed set that the question tail already names.

The break that the records isolate is between a successful user-role write and a retrieval call that reported zero candidates. Utilization of retrieved text cannot succeed on a turn whose injected list is empty. The 1/10 utilization figure is the answer-key score, kept visible so a correct `no` is not folded into a retrieval success.

---

## 10. Infrastructure limitations

- No HTTP error, timeout, connection failure, or server-error sentence occurred. Contingency was not used.
- `texts_diverge` was false on all 20 rows. Token text and cleaned done text matched, so the server’s punctuation cleaner did not change these replies.
- Provenance timestamps are naive. The storage scorer rejects naive timestamps. Storage times in the table above are the timezone-aware memory-row stamps. Retrieval was matched by `trace_id`, not by the provenance clock.
- The memory hash is 12 hex characters, 48 bits. A collision is possible. The check used here is equality between the sent prompt’s prefix and the prefix the scorer computed from the qualifying row, plus the scorer’s requirement that the fact sentence occur in that row.
- Fast mode can put history and up to five memories older than 30 minutes into the system note. On these twenty turns the provenance list was empty, so that injection did not fire. The code path remains able to fire on another question.
- SSE save outcomes were unknown on 19 turns. The memory rows still qualified. The SSE word is not the storage record.
- The provenance line does not name which zero-candidate branch ran.
- This write-up did not import the Flask app and did not restart the server.
- Digest of `echo:latest` was null in the show payload stored at Phase One start. No digest was invented.

---

## 11. Deviations from the protocol

No `DEVIATIONS.md` was created.

**OBSERVATION.** Sent prompts match sealed `items.json`. Seal hashes still match. Scoring rules were not edited after results.

One client correction, before any POST, in unsealed `transport.py` only: the self-test fixture whose done text is empty has no token events, so `texts_diverge` is false (empty equals empty). The assertion was set to expect false. A later fixture, token `Sable.` against done text `Sable`, still expects true. That change does not alter `score.py`, the answer key, or any live trial. `python3 transport.py` printed `transport_self_test=ok` before the run.

No production file, FAISS index, VSL state, or transparency-package file was edited for this experiment. Nothing was committed or pushed.

---

## 12. What the evidence establishes

On these ten novel items, with the fact sentence in the same user message, `echo:latest` in fast mode produced an exact answer on 8 of 10 completed replies.

On a later turn, about 31 minutes after the last Phase One reply, a new conversation, and a question that does not repeat the fact:

- the user message containing the fact was present in `user_conversation` memory for all 10 items;
- the retrieval record injected nothing for all 10 items;
- the answer matched the frozen key on 1 of 10 items, and that item’s match is the closed-set word already present in the reply instruction.

Same-turn use and later use are different results. File-style retrieval from the earlier R2 harness is a different result from this conversational memory path. The 9/14 open-book sitting is a different result from this 8/10.

---

## 13. What remains unknown

- Which of the two production branches wrote `candidates_considered: 0`.
- Whether the stored fact was outside the top 15 search hits.
- Whether any system-note block other than retrieved memory (scripture, ground truth, tools) was attached to these calls. The user message is preserved. The full system note is not in the result rows.
- Why SSE reported `unknown` when a qualifying memory row exists, beyond the half-dict rule already in the route.
- Whether item 03 or item 09 would pass under any looser rule. No looser rule was authorized, and none was applied.
- Whether this 8/10 would hold on a new sheet. This sheet is the whole same-turn sample.
- Generalized learning, independent understanding, and reliability outside these items and this pathway. Those were not measured.

---

## 14. Recommended next research direction

Keep the next step on the break this run already isolated.

One diagnostic, still on the existing retrieval function: record which zero-candidate branch ran, and record whether the stored user row was absent from the 15 search hits. That distinguishes “the search returned nothing” from “the fact never entered the candidate window.”

Do not build a new memory system for that question. Do not retune `k` inside this experiment. Do not run a correction round on these ten items. Do not spend the two remaining generations without a new authorization.

The same-turn gate is met on this sheet. The delayed failure is a retrieval-record failure in the presence of a successful store. That is the baseline the next measurement should start from.

---

## Preserved machine-readable records

Original observations, not rewritten by this report:

- `results_phase1.jsonl` — 10 rows, full prompts, done text, trace ids.
- `results_phase2.jsonl` — 10 rows, same fields.
- `phase1_scores.json` — frozen-key score. Contains the answer key. Do not send it to Echo.
- `phase2_attribution.json` — storage, retrieval, and utilization cells.
- `run_meta_phase1.json`, `run_meta_phase2.json` — listener, show payload, budget, deadlines, scorer stdout.

Sealed and still mode `0o444`: `PROTOCOL.md`, `PROTOCOL.sha256`, `answer_key.json`, `items.json`, `preflight.py`, `score.py`.
