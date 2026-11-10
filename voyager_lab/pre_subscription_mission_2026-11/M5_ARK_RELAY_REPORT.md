# M5-to-ARK relay verification

Inspection and tests: 2026-11-10. Overall label: **PARTIAL**.

M5-to-ARK application delivery is the same mailbox as the Grok-to-Grok relay (`grok_relay/`). Tailscale reachability is a separate fact from application delivery. This report uses the live probe. Protocol mechanics and the loopback proof are in `GROK_TO_GROK_RELAY_REPORT.md`. Private addresses are omitted here on purpose.

## What was determined

| Question | Result |
|---|---|
| Endpoints | Each side's Echo process, port 5000, `GET /projects/file?path=grok_relay/<own file>` |
| M5 identity | `m5`, writes `from_m5.md` |
| ARK identity | `ark`, writes `from_ark.md` |
| Direction | Pull only. `append` writes the local file. The peer must run `read` |
| Who can initiate | Either side, by appending its own file. The other side learns of it only by pulling |
| Authentication | The identity string is local configuration. The file route has no auth decorator. A credential-shaped body can be refused by the existing secret-dump filter |
| Acknowledgment | A line `ack: {id}` in the peer's own file, applied by the sender's later `read`. A 200 from the file route is not that acknowledgment |
| Persistence across a client restart | Cursor and outbox are local files. Demonstrated on the loopback copy. The live Echo process was not restarted |
| Persistence across disconnect | Loopback drop, HTTP 503, and a closed port left outbox ack flags unchanged. A live disconnect was not performed |

Production `grok_relay/relay.py` was read and not modified. The live Echo process was not stopped, restarted, or signaled.

## Cursor self-test on the live program

`python3 grok_relay/relay.py self-test` completed 9/9, exit 0. That command checks cursor math offline. It does not write the mailbox and it does not contact ARK.

## Counts before the probe

`status` on M5, before the append:

- Identity `m5`
- Own file 19825 characters, 19859 bytes
- Peer reachable
- Peer file 4688 characters, 4704 bytes
- Unread 0 characters
- Unacked 0

The status body does not include message text. Historical mailbox text was not copied into this report.

## Live probe

One append, through `python3 grok_relay/relay.py append`. No second append was made.

| Field | Value |
|---|---|
| Message id | `m5-20261110T055419Z-9192ca65` |
| Outbox timestamp | `2026-11-10T05:54:19.681365+00:00` |
| Append observed at | `2026-11-10T05:54:19.685764+00:00` |
| Probe window start | `2026-11-10T05:54:19.483391+00:00` |
| Probe window end | `2026-11-10T05:54:50.124465+00:00` |
| Token | `fe-pre-sub-live-20261110` |
| New-entry length | 420 characters |
| SHA-256 of the new entry only | `273e6cc8382ba012d5274f2b02b6334ff84423a9541918c5cb93f6aca8b60ba6` |

The body was a synthetic probe. It named the token, asked for one reply containing `ack:` plus this id and a second line `reply fe-pre-sub-live-20261110`, and asked for nothing else. It contained no personal content and no request to change code, memory, or configuration.

Local serve check, immediately after the append: `GET http://127.0.0.1:5000/projects/file?path=grok_relay/from_m5.md` returned **200**. Content length 20245 characters. Size field 20281. The token and the id were both present. Own file moved from 19825/19859 to 20245/20281.

M5 access log, last 8 MB of `memory/echo_watchdog.log` (file size 12707386 bytes at the later inspection): exactly one `grok_relay` file request, `GET /projects/file?path=grok_relay/from_m5.md` **200**, local stamp `2026-11-09 21:54:19`. That stamp matches the UTC append at `2026-11-10T05:54:19Z`. The client address is omitted. No second fetch of the new entry appears in that tail.

## Peer watch

Seven pulls of the peer file, about 5 seconds apart, from `2026-11-10T05:54:19.713362+00:00` through `2026-11-10T05:54:50.017629+00:00`.

| Poll | Peer characters | `ack: {id}` present | Token present |
|---|---|---|---|
| 0 through 6 | 4688 | no | no |

Each pull succeeded. The peer Echo process answered. The peer relay client did not append an ack or a reply during the watch. Peer file length stayed 4688 characters, 4704 bytes.

Status after the watch: peer reachable, unread 0, unacked 1. Exit 0 was printed by the probe script as `STATUS_AFTER_EXIT 0`.

Outbox after the watch: 6 rows. The last row is this id, `acked: false`.

## Later inspection

By `2026-11-10T06:01:17Z`, after the published loopback harness had been re-run in `/tmp`:

- Outbox still 6 rows, last id still `m5-20261110T055419Z-9192ca65`, `acked` still false, `acked_at` null, unacked count 1
- `status` printed: own file 20245 characters / 20281 bytes, peer reachable, peer file 4688 characters / 4704 bytes, unread 0, unacked 1
- Echo pid 65139 still `python -u run.py`, state `S+`. It was not signaled

The peer file did not grow in the hour after the probe. No ack arrived.

## Step labels

| Step | Label | Evidence |
|---|---|---|
| 1. M5 sends | **PASS** | Append exit success, outbox row, suffix hash, own file grew by the new entry |
| 1b. M5's endpoint serves the new entry | **PASS** | Localhost GET 200, id and token present, one matching access-log line |
| 2. ARK's relay client receives and acknowledges | **FAIL** | Seven successful pulls plus a later status: peer file stayed 4688 characters, ack line absent, outbox still `acked: false` |
| 3. ARK replies | **NOT RUN** | No reply line and no new peer-file bytes. A reply cannot be inferred from reachability |
| 4. M5 receives the reply and acknowledges it | **NOT RUN** | No reply existed to receive. M5 `read` was not run, so the live cursor was not moved and historical peer text was not copied into an inbox |
| 5. Live duplicate delivery | **NOT RUN** | One live message only. Loopback duplicate behavior is in the other report |
| 6. Live temporary disconnect | **NOT RUN** | A disconnect would mean stopping Echo or interrupting the network. Loopback drop, HTTP 503, and a closed port were tested instead |
| 7. Live recovery after connectivity returns | **NOT RUN** | No live disconnect was created. Loopback recovery is in the other report |
| Peer process answers a file fetch | **PASS** | Peer file length was returned on every poll and on the later status |
| Cursor self-test | **PASS** | 9/9, exit 0, no mailbox write |
| False live acknowledgment | absent | Status stayed at unacked 1. The reporting defect was not triggered on the live mailbox |

## Remaining manual step

A reader on the ARK side can finish steps 2–4 without changing code, memory, or configuration:

1. Run that machine's `relay.py read` so it copies the unread span.
2. Append one reply whose body contains the line `ack: m5-20261110T055419Z-9192ca65` and the line `reply fe-pre-sub-live-20261110`.
3. On M5, run `relay.py read` and then `relay.py status`.

An acknowledgment counts only if M5's outbox row for `m5-20261110T055419Z-9192ca65` changes to `acked: true`. A line in the peer file, before that `read`, is not yet an applied acknowledgment. This mission did not perform those ARK-side commands. They remain open.
