# Grok-to-Grok relay verification

Inspection and tests: 2026-11-10. Overall label: **PARTIAL**.

The only Grok-to-Grok path in this tree is the shared mailbox under `grok_relay/`. The M5-to-ARK check uses that same path. This report covers the protocol and the loopback proof. `M5_ARK_RELAY_REPORT.md` covers the live machines.

## Participants

Two copies of the same stdlib program, `grok_relay/relay.py`. Each copy has a fixed identity string, `m5` or `ark`. Each copy writes only its own mailbox file (`from_m5.md` or `from_ark.md`) and appends a row to its local `.outbox.jsonl`. The peer pulls that file. There is no second local Grok identity, no push from `append`, and no acknowledgment daemon.

Echo's conversation path is `app/sync/echo_messaging.py`. Echo does not read this mailbox. The hub helper that shells `relay.py status` was not run. It writes a status file, and a successful status fetch is only reachability. `claude_relay/` and `gemini_relay/` were not used as substitutes.

## Transport

The peer file is fetched with HTTP `GET /projects/file?path=grok_relay/<file>` on the peer Echo process, port 5000. The JSON body is `path`, `content`, and `size`. `size` is bytes. The relay cursor is a character index. Those two numbers differ when the file contains multi-byte UTF-8. Storing `size` as the cursor makes the next read look truncated.

The loopback copy in this directory replaces both peer addresses with `127.0.0.1` and the port with `18765`. It is not the live program and it is not loaded by Echo. The live program stays untracked because it contains private addresses. It was not edited.

## Identity, acknowledgment, and delivery states

Identity is the `IDENTITY` constant in the file on that machine. The file endpoint has no authentication decorator. Anyone who can reach the port can read a mailbox that does not trip the credential-shaped-content filter. A 200 response means the serving process returned bytes. It does not mean the peer relay client read them.

An acknowledgment is a line whose stripped text starts with `ack:` (case-insensitive), followed by the sender's message id. The sender's `read` command runs `mark_acks` against its own `.outbox.jsonl`. Local `append` sets `acked` to false. That state is **sent**. It becomes **acknowledged** only after a later `read` matches an outbox row. There is no separate received-by-human state. A line sitting in a mailbox is not proof that anyone read it.

| State | Evidence this mission accepts |
|---|---|
| Sent | `append` exits 0 and `.outbox.jsonl` has the id with `acked: false` |
| Served | `GET /projects/file` returns 200 and the body contains the id |
| Received by the peer client | The peer's `read` copies the unread span into its inbox and advances its cursor |
| Acknowledged | The peer file contains `ack: {id}` and the sender's `read` sets `acked` true on that outbox row |
| Failed | `status` or `read` exits 1 because the fetch failed. Outbox flags stay unchanged |
| Unknown | No fetch was observed, and no ack line appeared |

Duplicate delivery: a second `read` with the cursor already at the end prints `Nothing new` and does not grow the inbox. Rewinding the cursor to 0 replays the same id. A cursor that thinks the file shrank resets and does not replay history. Order is file order only. Restart survival is the cursor file and the outbox on disk. A new process in the same directory kept `Unread: 0 characters` after the cursor had already consumed the peer file.

Bidirectional traffic requires each side to append its own file and the other side to pull. The loopback test did both directions. The live test did not.

## Isolated protocol test

Harness: `run_isolated_protocol_test.py`. It serves `/projects/file` on `127.0.0.1:18765` with the production JSON shape. It does not open the live mailbox, the live index, or Echo's port. The first run used a scratch copy of the protocol. The published harness was then run once against `relay_protocol_under_test.py`.

Primary run: started `2026-11-10T05:53:42.356707+00:00`, finished `2026-11-10T05:53:43.656591+00:00`. **16 PASS, 1 FAIL.** Raw record: `isolated_primary_result.json`.

| Case | Label | Identifier |
|---|---|---|
| Cursor self-test inside the copy | PASS | exit 0 |
| A sends, outbox unacked | PASS | `m5-20261110T055342Z-7f9bdfe1` |
| B receives A's message | PASS | |
| B's inbox keeps the text before any ack | PASS | |
| B's reply has its own id | PASS | `ark-20261110T055342Z-c4907c42` |
| A receives the reply and records B's ack | PASS | |
| A appends an ack of the reply | PASS | |
| B records A's ack | PASS | |
| Second read does not deliver again | PASS | |
| Cursor rewound to 0 replays the same id | PASS | |
| Two later appends stay in file order | PASS | `m5-20261110T055342Z-96ec0c40` then `m5-20261110T055342Z-4bd78313` |
| Dropped connection | PASS | command exit 1, outbox ack flags unchanged |
| HTTP 503 | PASS | command exit 1, outbox ack flags unchanged |
| Closed port 18766 | PASS | command exit 1, outbox ack flags unchanged |
| Endpoint restored | PASS | status reachable again |
| New process, same directory | PASS | unread 0 characters |
| Ack print matches an outbox change | **FAIL** | printed recorded for `not-a-real-id`; that id is absent from the outbox |

Published-harness re-run: started `2026-11-10T06:00:05.657286+00:00`, finished `2026-11-10T06:00:06.967100+00:00`. **16 PASS, 1 FAIL.** Process exit 1, which is the expected reporting defect. Raw record: `isolated_published_harness_result.json`. Send id `m5-20261110T060005Z-ff0fb4bc`. Reply id `ark-20261110T060005Z-20446aea`. Order pair `m5-20261110T060006Z-e4d9efc4` then `m5-20261110T060006Z-1ea46087`. The re-run does not replace the primary identifiers. Both runs agree on the case results.

## Reporting defect, left visible

`mark_acks` returns every id it sees on an `ack:` line, including an id that matches no outbox row. `read` then prints `Ack recorded for {id}`. On `not-a-real-id`, `print_says_recorded` was true and `outbox_has_id` was false. The production program was not patched. The loopback copy was not patched either, so a future run still shows the failure. A printed acknowledgment is trustworthy only when the outbox row for that id has `acked: true`.

## Live send, as it bears on this relay

One live append was made through the production program. Details and the machine outcome are in `M5_ARK_RELAY_REPORT.md`. Summary for this report: local send **PASS**, local serve of the new entry **PASS**, peer client receipt **NOT OBSERVED**, peer ack **FAIL** for the watched window and still unacked at `2026-11-10T06:01:17Z`. Live duplicate delivery, live disconnect, and live recovery were **NOT RUN**. Those three behaviors were demonstrated only on the loopback server above.

## How to repeat the loopback proof

From the Voyager worktree:

```bash
python3 voyager_lab/pre_subscription_mission_2026-11/run_isolated_protocol_test.py
```

Expected: 16 PASS, 1 FAIL, process exit 1. The failure line is `ack print matches an outbox change`. The run writes `/tmp/fe-relay-phase2/result.json` and deletes that directory at the start of the next run. It uses only the standard library.
