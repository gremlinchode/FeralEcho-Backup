# Claude ↔ Codex Relay / Hub Reliability, Persistence & Communication Semantics Audit

**Read-only forensic architecture study.** No relay/Hub source modified, no cursor
manipulated, no credential printed, no LaunchAgent created, Echo not touched.
Nothing staged, committed, or pushed.

---

## 1. Executive Verdict

# RELAY ARCHITECTURE USEFUL BUT REQUIRES RELIABILITY REPAIR

Persistent, asynchronous, single-recipient messaging between two agents on this
network genuinely works and is proven by real historical evidence (Section 5), not
merely by design intent. One of the two reported defects (the shared read cursor)
has **already been fixed in current source** — found and corrected independently by
Air, the same day Codex first reported it, through a channel Codex's own message
never reached. The other (hardcoded `checked_by` attribution) remains real and
unrepaired, currently cosmetic but structurally capable of becoming a genuine
provenance risk if this project ever relies on `hub/status.jsonl` for anything
resembling the governance-presence determination its own README already
contemplates. Process supervision is manual and fragile by design, not by oversight.
None of this rises to "architecture semantics unsafe for multi-agent use" — the core
single-recipient delivery guarantee is sound; what's missing is closer to
operational hardening than a fundamental flaw.

---

## 2. Runtime Baseline

- Timestamp: `2026-09-29T15:17 UTC` / `08:17 PDT`.
- HEAD `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`; 41
  pre-existing dirty paths, none touched.
- Echo (`run.py`): PID 71538, running since `2026-09-28 19:15:54`, uptime
  ~13h; untouched by this mission.
- Local relay servers, re-verified current (not assumed from the prior mission):
  - `claude` identity, PID **84828**, listening `127.0.0.1:8765`, parent PID **1**
    (reparented to `init` after the launching shell exited — confirms it was
    started detached/backgrounded, exactly as the prior mission did).
  - `codex` identity, PID **84838**, listening `127.0.0.1:8767`, parent PID **1**.
  - Both launched via plain `nohup ... &; disown` — no supervisor, no process
    group management beyond the OS reparenting an orphaned child to PID 1.
- Hub health, freshly run: all five channels report `alive`.

---

## 3. Relay / Hub Architecture

Full source read (`codex_relay/relay.py`, `claude_relay/relay.py`,
`hub/check_hub.py`, `hub/notes.py`) — the real topology, not the conceptual one:

```
Claude (M5)  <--claude_relay/relay.py-->  Claude (Air)      [network, real Tailscale IPs]
     |                                                        via GET /projects/file (Flask, existing route)
     |
     +---- hub/notes.py: post/pull, riding claude_relay's "append"/"read-hub" ----

Claude (M5, "claude" identity)  <--codex_relay/relay.py-->  Codex (M5, "codex" identity)
     |                                                        [local loopback, 127.0.0.1:8765/8767]
     |
Codex (M5, "m5" identity)  <--codex_relay/relay.py-->  Codex (Air, "air" identity)
                                                          [network, real Tailscale IPs, port 8765/8767 conventionally]

hub/check_hub.py  --(shells out to both relay.py scripts + 2 Echo HTTP checks)-->  hub/status.jsonl
```

**Three structurally distinct relay instances exist**, all running the identical
`codex_relay/relay.py` code with different `--identity`/`--data-dir`/`--port`/
`--bind` combinations:
1. Codex M5 ↔ Codex Air (network, `~/.codex-relay`, identity `m5`).
2. Claude M5 (local) ↔ Codex M5 (local) — the one just restored (`~/.claude-codex-relay`,
   identities `claude`/`codex`, both bound `127.0.0.1`).
3. `claude_relay/relay.py` — a **separate script entirely**, Claude M5 ↔ Claude Air,
   using a fundamentally different transport (HTTP GET against the existing
   FeralEcho Flask app's `/projects/file` route, not its own socket server) and a
   different storage shape (plain markdown files with a JSON length-cursor
   sidecar, not JSONL).

**`hub/`** is a third, higher layer that treats channels 1–3 as read-only
observability inputs (via subprocess calls to their own CLIs) and layers a
fourth, genuinely separate artifact (`hub/notes.jsonl`, a shared board) on top,
deliberately routed through channel 3 (`claude_relay`) for cross-machine delivery
regardless of which local identity authored a note — confirmed directly in
`notes.py`'s own docstring, not assumed.

---

## 4. Five Channel Definitions

| Channel | Purpose | Producer | Consumer | Persistent? | Cursor? | Current health |
|---|---|---|---|---:|---:|---|
| `claude_relay` | Claude M5 ↔ Claude Air prose mailbox + facts ledger | Either Claude session, via `append`/`fact` | The other side's Claude session, via `read`/`facts-read` | Yes — plain markdown/JSONL files | Yes — per-side, length-based, **now split**: `read` and `read-hub` use independent files (Section 7) | alive |
| `codex_relay` (M5↔Air) | Codex M5 ↔ Codex Air mailbox | Codex, via `send` | Codex, via `read` | Yes — JSONL | Yes — single length-cursor per data-dir | alive |
| `local_claude_codex_relay` | Claude M5 ↔ Codex M5 mailbox (same machine) | Either identity, via `send` | The other identity, via `read` | Yes — JSONL | Yes — single length-cursor per identity's data-dir | alive (just restored) |
| `echo_m5_liveness` | Is Echo's own `run.py` healthy | `run.py`'s liveness ledger | `hub/check_hub.py` (HTTP GET) | N/A (a live query, not a mailbox) | N/A | alive |
| `echo_air_reachability` | Is Air's `run.py` reachable | Air's `run.py` | `hub/check_hub.py` (HTTP GET) | N/A | N/A | alive |

**What "green" actually means, per channel, verified against source rather than
assumed**: for the three mailbox channels, `alive` means **`status`'s peer-health
GET succeeded and the local inbox file is readable** — it does **not** mean a
round-trip message was just exchanged, does not mean authentication was exercised
(a plain `GET /health` needs no signature), and does not mean the backlog is
free of unread content (unread counts are reported alongside `alive`, not folded
into the pass/fail). For the two Echo channels, `alive` means a single HTTP GET to
an existing, already-authenticated-as-needed endpoint returned 200 — genuinely a
real round-trip, not a weaker proxy. **A green `local_claude_codex_relay` before
today's restart never existed** (it only exists now that the servers are up) — so
"was this channel ever secretly fine while showing red" is not a live question here.

---

## 5. September 16 Historical Message Reconstruction

Real inbox/outbox files inspected directly, not reconstructed from memory.

`~/.claude-codex-relay/inbox.jsonl` (the "claude" identity's own received-messages
file) contains exactly three entries:

| id (short) | sender→recipient | created_at | received_at | length |
|---|---|---|---|---|
| `03e2fbe7…` | codex→claude | 2026-09-15T18:57:11.890941Z | 2026-09-15T18:57:11.898593Z (8ms later) | 96 chars |
| `5f32c71d…` | codex→claude | 2026-09-16T09:32:32.382221Z | 2026-09-16T09:32:32.404223Z (22ms later) | 353 chars |
| `5155c856…` | claude→codex | 2026-09-29T14:13:04.882042Z | 2026-09-29T14:13:04.891655Z | 796 chars (this mission's own predecessor's acknowledgment, into `codex`'s inbox — listed here since both identities' files share one directory, Section 5's own closing note) |

**Reconstructed timeline for the real Sept-16 message**: Codex sent it; the
"claude" identity's server (then running) accepted it, verified its HMAC
signature, checked it against `.seen_ids.json` (not a duplicate), and appended it
to `inbox.jsonl` with a `received_at` timestamp **22 milliseconds** after
`created_at` — genuine, near-instant local delivery, not a delayed batch process.
**The message was fully, durably written to disk at that moment.** Everything
that happened afterward — the local relay servers stopping (for reasons unrelated
to this message), 13 days passing, this session restarting both servers, then
running `read` — never touched `inbox.jsonl` at all. **The relay *server* being
offline was irrelevant to whether the message persisted**; it only affects
whether new messages can be *accepted* and whether existing ones can be *fetched
remotely* (moot for a same-machine loopback, where `read` only ever touches the
local filesystem, never the network — confirmed directly: `read()`'s
implementation, Section 6, never makes an HTTP call at all).

- **Ordering**: preserved — append-only file, entries in send order.
- **Metadata**: fully preserved — sender, recipient, both timestamps, full message
  body, all intact and unmodified 13 days later.
- **Sender identity**: preserved and **was cryptographically authenticated at
  receipt time** (HMAC-SHA256 over the canonical record, verified before
  acceptance) — not merely a claimed, unverified string (Section 12).
- **Acknowledgement**: none existed at the protocol level — Codex's `send`
  received an HTTP 200 confirming *acceptance into the inbox*, which is a
  different, weaker guarantee than "a human or the other agent has read it"
  (Section 6).
- **Recoverable after being read**: yes — `read()` never deletes or mutates
  `inbox.jsonl`; it only ever moves a separate cursor file forward (Section 7).
  The message remains in `inbox.jsonl`, byte-for-byte, right now.
- **Still discoverable by another consumer**: yes, trivially — any future reader
  of `inbox.jsonl` (a different tool, a manual `cat`, a rebuilt cursor) sees it
  again; only the *cursor-based* "what's new" view would skip it now that it's
  been marked read once.

**One real, disclosed architectural untidiness, not a correctness bug**: both the
"claude" identity's own inbox and its own outbox — and, per this same directory's
contents, what appear to be entries generated by whichever side originally ran
`send` targeting this identity — live in the single shared directory
`~/.claude-codex-relay`. This works correctly (no message loss, no corruption) but
means the local loopback's two "parties" have not been given fully separate
private data directories the way the M5↔Air pair (`~/.codex-relay` vs. Air's own
equivalent) conceptually are. Flagged as a real hygiene observation for Section 19,
not a defect in delivery.

---

## 6. Delivery Semantics

**Closest accurate description: PERSISTENT MAILBOX with AT-LEAST-ONCE *submission*
semantics and separately-tracked, cursor-based, effectively AT-MOST-ONCE
*consumption via `read`*.** Not a queue (nothing is removed on read), not a
pub/sub log in the strict sense (only one cursor per file by default, not
per-subscriber — Section 8).

- **"Send succeeded" means**: the HTTP POST to `/message` returned 200 with
  `{"accepted": true, ...}`, **after** the server verified the record shape, the
  sender identity matches the configured `--peer-identity`, the recipient matches
  the server's own `--identity`, the size limit, and the HMAC signature — and
  **after** the message was already durably appended to `inbox.jsonl` (the
  `with self.server.lock:` block does the append before the handler replies,
  confirmed directly in `do_POST()`). A 200 is a genuine, not optimistic,
  durability confirmation for that one write.
- **"Read succeeded" means**: the caller's local cursor file was read, the local
  `inbox.jsonl` was read (no network call — `read()` never touches `/health` or
  `/message`), and the cursor was **unconditionally advanced to the file's
  current end**, regardless of whether the printed content was actually acted on
  by whatever called `read()`. Delivery (message sitting in the file) and
  consumption (a cursor having passed over it) are **genuinely distinct states**,
  and only the latter is what `read()`/`status()`'s "unread" count reports.
- **No acknowledgement mechanism exists** beyond the transport-level 200 at send
  time — nothing tells the *sender* whether the *recipient* has actually read
  (let alone acted on) a message. This is a real, disclosed gap (Section 17).
- **Messages can be delivered twice at the transport layer** if a client retries
  an identical, already-signed request (the server's `.seen_ids.json` correctly
  deduplicates by the record's own `id`) — but a **fresh invocation of `send`**
  for "the same" logical message text generates a brand-new UUID4 client-side
  every time, so the server has no way to recognize two independently-typed sends
  of identical content as the same logical message (Section 13).
- **Messages cannot disappear without consumption** under any scenario this audit
  found — `inbox.jsonl` is append-only and is never pruned, truncated, or rewritten
  by anything in this codebase (confirmed via full source read of both relay
  scripts; no cleanup/pruning code exists in either).

---

## 7. Cursor Architecture

**Re-derived from current source, not from the September 16 assertion, per this
mission's own explicit instruction.**

| Cursor file | Owner/scope | Used by | Update timing | Atomicity | Persists across restart? |
|---|---|---|---|---:|---:|
| `codex_relay`: `<data-dir>/.last_seen.json` | Per data-dir (i.e., per local identity) | `codex_relay/relay.py read`/`status` | Overwritten on every `read` call, unconditionally, to the file's current length | Not transactional but effectively atomic in practice (single-threaded CLI invocation per call; no concurrent-writer guard exists) | Yes — plain file on disk |
| `claude_relay`: `.last_seen_from_<peer>.json` | Per peer, per machine | Plain `claude_relay/relay.py read` | Same pattern, via `_save_marker()`, using `os.replace()` for an atomic rename — genuinely safer against a torn write than `codex_relay`'s direct overwrite | Atomic (temp file + `os.replace`) | Yes |
| `claude_relay`: `.last_seen_from_<peer>_hub.json` | Per peer, **specifically for `hub/notes.py`'s `pull`** | `claude_relay/relay.py read-hub`, called only by `notes.py cmd_pull()` | Same atomic pattern | Atomic | Yes |

**The central, mission-defining question — does `relay.py read` and `notes.py
pull` share one cursor — was checked directly in current source and found
`RESOLVED`, not open.** `hub/notes.py`'s `cmd_pull()` (`:202-218`) calls
`claude_relay/relay.py read-hub`, which uses `read_new_for_hub()` →
`_hub_marker_file()` — a **file with a different name** (`..._hub.json`) than
what plain `read` uses (`_marker_file()`, no `_hub` suffix). Both track the same
underlying mailbox content (`from_air.md`), but as two **independent** cursor
positions. `notes.py`'s own comment states this was **"added 2026-09-16, proposed
by Air"** — the identical date as Codex's report of the problem.

**What this means, precisely, and worth stating plainly rather than glossed
over**: Codex found this exact defect on 2026-09-16 and tried to report it — but
the only channel that could deliver that report (the local Claude↔Codex relay)
was down, so the report sat unread for 13 days. **Independently, the same day, on
the *other* working channel, Air identified and fixed the identical problem** —
without ever seeing Codex's message, since it hadn't been delivered. This is a
real, verifiable instance of the exact risk this whole investigation is testing
for: a genuine finding almost went stale/redundant purely because of which
specific channel it happened to travel through.

**A distinct, narrower version of the same underlying pattern still exists,
un-fixed, and was independently found in this pass, not merely inherited from
Codex's report**: any two *separate* callers of the *same* plain `read` command
against the *same* data-dir (e.g., two different Claude Code sessions on M5 both
manually running `claude_relay/relay.py read`, or two sessions both running
`codex_relay/relay.py read` against the local loopback) **do** share one cursor
file with no notion of "which session is asking." The first to run consumes the
"unread" view; the second sees nothing new, even though it never actually
observed that content itself. This is architecturally identical in shape to what
Codex reported, just for a pairing (`read` vs. `read`, not `read` vs. `pull`)
that hasn't been split the way the notes-specific one was.

---

## 8. Multi-Consumer Safety

**Architecture mixes both models, and this is worth documenting precisely rather
than picking one label**: for the *specific* `read` vs. `read-hub` pairing, the
system now genuinely implements **independent-cursor (pub/sub-like) semantics** —
two named consumer roles, each with its own position. For *any other* pairing
(two plain `read` callers, or two `read-hub` callers), it remains **single-cursor
(queue-like) semantics** — one shared position, first-reader-wins.

**Verdict: SAFE for the one pairing this mission was specifically asked to
verify** (`relay.py read` vs. `hub/notes.py pull`) — confirmed fixed in current
source, not merely claimed. **OTHER DEFECT** exists for the general case (Section
7's un-split same-command collision) — real, but narrower in practical impact
today than the original report implied, since this project's actual usage pattern
(one Claude session at a time checking in) rarely exercises it.

---

## 9. Message-Loss Matrix

| Scenario | Outcome | Evidence |
|---|---|---|
| A — Sender writes while receiver offline | **SAFE** — for `codex_relay`'s design, "offline" here means the *server* isn't running to *accept new sends*; a `send` attempt against a down server fails at the client (`urllib.error.URLError`) and is logged to the sender's own `outbox.jsonl` as `delivery: "failed"` — the message is **not silently lost**, it's a visible, logged failed-send the sender can see and retry. This is different from "receiver's inbox already has it and isn't being read," which is what actually happened in the real Sept 16 case (Section 5) — the server *was* up long enough to accept it; only the *reading* was delayed. |
| B — Relay server dies after write | **SAFE** — `inbox.jsonl` is a plain file; nothing about server lifecycle affects already-durably-appended content. |
| C — Relay server dies before write completes | **UNKNOWN, bounded** — the `append_jsonl()`/`save_seen()` pair is not wrapped in one atomic transaction; a crash between the two could in principle leave `inbox.jsonl` updated but `.seen_ids.json` not yet reflecting it (or vice versa via `os.replace()`'s own atomicity for the seen-file specifically). Not observed in practice in this audit; a genuine, narrow theoretical gap, not evidenced as a real occurrence. |
| D — Receiver reads message | **SAFE** — cursor advances, message stays in the file (Section 5). |
| E — Receiver reads but crashes before processing | **INVISIBLE TO THAT CONSUMER'S OWN FUTURE READS** (cursor already advanced past it) but **not LOST** — the message is still in `inbox.jsonl`; a different tool, or a manually-reset cursor, can still see it. The *printed* content from that one `read` call is gone unless the caller itself saved it somewhere (this session's own convention of quoting relay output back to the user is exactly this kind of external capture). |
| F — `relay.py read` before `notes.py pull` | **SAFE, confirmed fixed** (Section 7) — independent cursors. |
| G — `notes.py pull` before ordinary `relay.py read` | **SAFE, confirmed fixed** (Section 7) — same reasoning, symmetric. |
| H — Two consumers read simultaneously | **RACE, narrow** — `read()`/`status()` have no file-locking around the cursor read-then-write; two truly concurrent same-command invocations against the same data-dir could both read the same "old" marker, both print the same "new" content (duplicate visibility, not loss), then both write the marker, with whichever writes last winning — a benign race (double-delivery-to-the-terminal, not data loss) given this project's actual single-operator-at-a-time usage pattern. |
| I — Machine reboots | **SAFE for stored messages; SERVERS DO NOT RESTART THEMSELVES** — `inbox.jsonl`/cursors are plain files, unaffected by reboot; the two backgrounded relay processes have no supervisor and would need to be manually restarted (Section 15), exactly the condition that caused this whole investigation's starting point. |
| J — Relay process restarts | **SAFE** — confirmed today, live: both processes were freshly started this session against pre-existing data directories and immediately reported correct prior state (`hub/check_hub.py` showed real prior unread-character counts, not a reset to zero). |
| K — Same message submitted twice (identical record, same id) | **DEFINED, DEDUPLICATED** — server-side `.seen_ids.json` check, confirmed in source (`do_POST`'s `duplicate = record["id"] in seen`); the second POST is still accepted (200) but not re-appended, and the response explicitly reports `duplicate: true`. |
| K′ — Same *logical* message re-sent via a fresh `send` invocation | **DUPLICATED** — a new UUID4 is minted per `send()` call; the server has no way to recognize this as "the same" message (Section 13). |
| L — Acknowledgement is lost | **N/A — none exists to lose** (Section 6); the closest analogue, the sender's own HTTP-200-confirmed `outbox.jsonl` entry, is itself durable and was not observed to be lost in this audit. |
| M — Cursor state becomes stale or corrupted | **SELF-HEALING FOR THE "SHRUNK" CASE, UNPROTECTED FOR ARBITRARY CORRUPTION** — `claude_relay/relay.py`'s `_read_new_generic()` explicitly detects `len(content) < last_len` (a reset/shrink) and re-syncs rather than crashing or under-reading; `codex_relay/relay.py`'s `read()` has a nearly identical guard (`if len(content) < marker: marker = 0`). Neither script validates the marker JSON's *shape* beyond a bare `try/except (FileNotFoundError, JSONDecodeError, OSError)` fallback to `{"length": 0}` — a genuinely malformed-but-parseable marker (e.g., a negative number, or a huge one) is not specially guarded against beyond that shrink check. |

---

## 10. Ordering

- **Per-sender-to-one-recipient ordering is guaranteed** — a single append-only
  file, single-threaded appends under a lock (`codex_relay`) or unlocked-but-
  effectively-serial local file writes (`claude_relay`, single-operator CLI
  usage), written in receipt order.
- **No global cross-channel ordering exists, and none is claimed** — `claude_relay`
  and the two `codex_relay` instances are entirely separate files/processes with
  no shared clock synchronization beyond each message's own self-reported
  `created_at`/`received_at` timestamps (real wall-clock time, not a logical
  sequence number).
- **Two messages could receive ambiguous ordering** only under the true-concurrent-
  write race already named in Scenario H/M above — not observed as a real
  occurrence, a narrow theoretical risk under this project's actual usage pattern.
- **A restarted consumer resumes in the correct place**: yes, confirmed directly
  today — both relay identities restarted mid-session with real prior state and
  picked up their real cursor positions correctly (Section 9, Scenario J).

---

## 11. Identity / Attribution

- **Exact source**: `hub/check_hub.py:52`, inside `append_status()` — a single
  hardcoded string literal, `"checked_by": "claude-m5"`.
- **All callers**: every one of the five `check_*` functions in `check_hub.py`
  routes through this one `append_status()` — there is no parameter, environment
  variable, or `--identity`-style flag anywhere in this file that could vary it.
- **Consumers**: a repo-wide grep for `checked_by` finds **exactly one hit — its
  own write site.** Nothing reads this field anywhere in the current codebase.
- **Impact classification**: **PROVENANCE DEFECT**, not (currently) a
  **BEHAVIORAL** or **SCIENTIFIC-EVIDENCE RISK** — every historical
  `hub/status.jsonl` row claiming `"claude-m5"` performed the check is
  potentially wrong (e.g., if Codex or a human ran `check_hub.py` directly), but
  nothing downstream currently trusts or acts on that claim. **This could become
  a real risk without any code change elsewhere**: `hub/README.md`'s own
  governance section states "If Claude M5 is not present/engaged... authority
  reverts to Codex M5" — the *kind* of determination that field's name implies it
  could someday inform. As long as nothing reads it, it's cosmetic; the moment
  something does, it would be silently, unconditionally wrong for any non-Claude-M5
  actor running the check.

---

## 12. Credential Boundary

Established without printing any secret value, per this mission's own requirement
(and the prior mission's own precedent of using inline shell substitution rather
than `cat`-ing a secret into visible output).

- **Authentication mechanism**: HMAC-SHA256 over a canonical (sorted-key,
  compact-separator) JSON encoding of the message record, keyed by a shared
  secret read from the `CODEX_RELAY_SECRET` environment variable — confirmed
  directly in `codex_relay/relay.py`'s `signature()`/`secret_from_env()`. Both
  peers must possess the identical secret; it is never transmitted over the wire
  itself, only used to compute/verify a signature.
- **Constant-time comparison**: confirmed — `hmac.compare_digest()` is used for
  both the message signature and the legacy `/v1/messages` bearer-token check
  (`do_GET`/`do_POST`), correctly avoiding a timing side-channel.
- **Credentials are shared, not per-message-unique**: one static secret per pair
  of identities, stored as a local file (`~/.claude-codex-relay/secret`,
  `~/.codex-relay/secret`) for reference and exported into the process
  environment at `serve`/`send` invocation time — confirmed to exist via `ls`
  only; contents were never read or printed in this or the prior mission.
- **Claimed identity vs. authenticated identity**: the `sender` field inside a
  message record is validated against the server's own configured
  `--peer-identity` (`valid_message()`), but **the HMAC only proves "whoever holds
  the shared secret sent this," not "the specific named sender did"** — since the
  same secret is used bidirectionally between exactly two named peers, a sender
  claiming to be the *wrong one of that same pair* would be rejected by the
  `expected_sender` string check, but the cryptographic proof itself doesn't
  distinguish the two peers from each other, only "someone with the secret" from
  "someone without it." For a genuinely two-party channel this is a reasonable,
  proportionate design — worth stating precisely rather than overclaiming
  "cryptographically tied to a specific sender."
- **Localhost binding**: `serve_p.add_argument("--bind", default="127.0.0.1", ...)`
  — the local loopback pair is bound to `127.0.0.1` specifically (confirmed via
  `lsof`, Section 2), meaning it is not reachable from any other host on the
  network at all, HMAC aside — a real, structural exposure reduction beyond the
  cryptographic layer, for this specific instance.
- **Stored messages' sender provenance**: trustworthy **conditional on the shared
  secret never having leaked** — the `sender` field on every already-accepted
  message was authenticated at receipt time via the mechanism above, not merely
  self-reported and trusted blindly.

---

## 13. Duplicate Handling

- **Stable message ID**: yes — a client-generated `uuid.uuid4()`, minted fresh
  inside `send()` per invocation (`codex_relay/relay.py:214`).
- **Client-side generation**: confirmed — the ID never originates from the server.
- **Persistent**: yes, embedded in the record itself, written to both sender's
  `outbox.jsonl` and receiver's `inbox.jsonl`.
- **Server-side duplicate detection**: yes, via `.seen_ids.json`, keyed on this
  exact ID, capped at the most recent 10,000 entries (`save_seen()`) — a
  deliberate, disclosed bound, not unlimited growth.
- **Two distinct messages colliding**: not practically possible — UUID4 collision
  probability is astronomically low, and nothing in this design relies on any
  weaker uniqueness source.
- **What duplicate detection actually protects against**: **transport-level
  retries of the identical, already-constructed request** (e.g., a client timing
  out waiting for the 200 and resending the exact same signed payload) — not
  **application-level re-sends of the same logical intent** typed or generated
  fresh a second time, which mint a new ID and are treated as a wholly new
  message (Section 9, Scenario K′). This is the same distinction the prior
  Echo-Studio-durable-request-lifecycle mission independently found in a
  completely different subsystem — worth naming as a recurring architectural
  pattern in this codebase, not a coincidence unique to either system.

---

## 14. Persistence / Restart Semantics

| Boundary | What survives |
|---|---|
| Relay process death | Everything on disk (`inbox.jsonl`, `outbox.jsonl`, `.seen_ids.json`, cursor files) — confirmed by this exact session's own real 13-day outage. |
| Claude process death (a Claude Code session ending) | Everything — the relay servers are independent OS processes, not owned by any Claude session's own lifetime. |
| Codex process death | Same reasoning — independent processes. |
| Echo (`run.py`) process death | No relation — confirmed architecturally distinct (Section 16); a `run.py` crash/restart has zero effect on any relay file. |
| Terminal closure | Survived already, today — both relay servers were started from a terminal session, `disown`ed, and remain running with the terminal long since able to have closed. |
| Logout | Not tested (would require an actual logout); `nohup`+`disown`'d processes reparented to PID 1 are the standard mechanism that *should* survive a logout on macOS for a user-level login session, but this was not empirically verified in this pass — stated as inferred from standard OS behavior, not directly observed. |
| Machine reboot | **NOT survived** — nothing restarts these processes automatically; this is the one real, unprotected boundary, addressed operationally in Section 15, not architecturally in the relay code itself. |

The real 13-day Codex message (Section 5) is direct, empirical evidence for every
row above **except** the reboot row specifically — no reboot occurred during that
window (confirmed: `start_echo.sh`'s watchdog, PID 56610, has been running
continuously since `09:44:38` on the 28th, per every baseline check this session
has taken, meaning the machine itself never rebooted across the entire outage).

---

## 15. Process Supervision

**Current state: Option A — manual startup, fragile by construction, not by
accident.** No existing lifecycle mechanism currently owns these two processes.

Compared against the named alternatives, using what already exists in this
codebase:
- **B — `start_echo.sh`**: purpose-built for exactly one thing (Echo's `run.py`
  crash-restart loop) — adding unrelated relay processes to it would conflate two
  genuinely different concerns (Echo's own runtime vs. cross-agent communication
  infrastructure) and risks exactly the kind of two-supervisor collision
  CLAUDE.md's own history (Finding 51, `safe_restart.sh`) already documents as a
  real, previously-hit failure mode for a different pair of processes.
- **C — Echo's watchdog**: same objection — Echo's watchdog is specifically
  Echo's, and these relay processes have no dependency on Echo at all (Section
  16 confirms this directly).
- **D — A dedicated relay supervisor**: the *closest conceptual fit*, but
  building one is new infrastructure this audit does not have a demonstrated need
  for yet, beyond "processes should restart automatically" — which launchd
  already solves natively, at lower cost than a bespoke supervisor script.
- **E — launchd**: **the best-fitting existing pattern already used in this
  exact project** — CLAUDE.md's own Finding 8/65 documents a real precedent
  (`com.gremlin.echo.plist`) for exactly this shape of problem (a background
  process that should start at login and restart on failure), including the
  documented caution from that same history about not force-reloading a
  LaunchAgent while a manually-started instance of the same service is already
  running (directly relevant here: these two relay processes are running right
  now).
- **F — another mechanism**: none found that fits better.

**Smallest coherent ownership model**: two small LaunchAgents (or one, managing
both identities), modeled directly on the existing `com.gremlin.echo.plist`
precedent — not proposed as urgent, and explicitly **not created in this pass**
per the hard stop.

---

## 16. Echo Integration

Checked directly, not assumed from repository co-location:

- Echo does **not** read from, write to, or poll any relay file or Hub artifact —
  confirmed via repo-wide grep: no `app/`, `run.py`, or Echo-runtime code
  references `claude_relay/`, `codex_relay/`, or `hub/` at all.
- Echo does **not** consume Hub notes, does not see Claude/Codex communications,
  and cannot initiate a relay message.
- Echo does **not** depend on Hub status for anything — `hub/check_hub.py` only
  ever *queries* Echo (via the two Echo-specific channels), never the reverse.
- **This is Claude↔Codex/Claude↔Claude infrastructure, incidentally hosted in the
  FeralEcho repository, not an Echo capability.** Directly consistent with
  `hub/README.md`'s own stated design ("no direct Echo↔Codex channel... this hub
  does not create one") and with this session's own earlier Protector-Clause
  research, which separately confirmed Echo has no autonomous-initiative channel
  of her own (a genuinely different, unrelated finding, now doubly confirmed from
  two independent investigations that never touched each other's evidence).

---

## 17. Asynchronous Communication Claim

# SUPPORTED WITH QUALIFICATIONS

The bounded claim — "one agent can leave a persistent message another agent can
discover later without Gremlin carrying it" — is **directly, empirically proven**
by the real Sept-16 case study (Section 5), not merely architecturally plausible.

**Specifics, stated precisely rather than generalized:**
- **Which agents**: any two of the three real pairs this architecture actually
  implements (Claude M5↔Claude Air; Codex M5↔Codex Air; Claude M5↔Codex M5
  locally) — each pairing is its own separate, non-transitive channel. Claude M5
  cannot leave a message for Codex Air directly, for example; no such channel
  exists.
- **What must be running**: the *sender's* local tooling (to write) and,
  eventually, the *receiver's* relay server (to have accepted it) — but **not**
  continuously; the real case study proves a receiver's server can be down for
  13 days with zero effect on an already-accepted message's durability.
- **What can be offline**: the recipient's server can be offline at the moment of
  *discovery attempt* (the discoverer just sees "unreachable" and tries later);
  the message, once accepted, requires nothing further to remain intact.
- **Persistence boundary**: survives process death, terminal closure, and
  (inferred, not directly tested) logout; does **not** survive if the underlying
  data-dir's files were ever deleted (never observed, not a live concern) and is
  not automatically restarted after a machine reboot (Section 14/15).
- **Discovery mechanism**: manual, pull-based (`read`/`pull`/`status`) — nothing
  pushes a notification to a session that isn't actively checking. This project's
  own standing practice (checking the relay periodically, per the "Relay
  Proactive Permission" convention already established) is what actually makes
  discovery happen in practice, not an architectural guarantee that it will.
- **Identity guarantees**: cryptographically authenticated at receipt (Section
  12), with the precise, non-overclaimed caveat about what the HMAC does and
  doesn't distinguish.

**Why "with qualifications," not a clean "SUPPORTED"**: the fixed shared-cursor
risk for same-command collisions (Section 7's un-split general case), the
un-acknowledged delivery model (Section 6), and the manual-only supervision
(Section 15) are all real, if bounded, ways this promise can currently be
weakened in specific circumstances — not because the core mechanism is unsound,
but because none of these edges have been hardened yet.

---

## 18. Experimental Value

| Future use | Architecture supports transport? | Agents currently initiate/use it autonomously? |
|---|---:|---:|
| Delayed Claude↔Codex collaboration | Yes — directly proven (Section 5) | No — every observed use this session was manually invoked by a human-directed session, not self-initiated on a timer or trigger |
| Independent critique | Yes — the channel carries arbitrary text; nothing structurally prevents a critique message | No |
| Asynchronous handoff | Yes | No |
| Agent disagreement | Yes — `claude_relay`'s own real history (this session's earlier Ark/Air correction exchange) already demonstrates genuine back-and-forth disagreement-and-correction occurring naturally | Partially — that exchange was agent-to-agent content, but each turn was still a human-directed session choosing to check and reply, not an autonomous polling loop |
| Persistent research notes | Yes — `hub/notes.jsonl` exists for exactly this, proven to round-trip (its own 2026-09-15 test note) | Minimally used — one test note, otherwise unused |
| Human-out-of-loop message discovery | **Architecturally yes, practically no** — nothing currently polls these channels without a human/session-initiated check; the mission's own central finding (13 days of silence) is itself evidence that "out of loop" currently means "undiscovered," not "autonomously handled" |

---

## 19. Necessary Repairs

| Candidate | Classification | Reasoning |
|---|---|---|
| 1 — Independent cursors for independent consumers | **NOT NEEDED, for the reported case** (already fixed, Section 7) — **USEFUL** for the general same-command-collision case, low urgency given current single-operator usage | |
| 2 — Dynamic/authentic `checked_by` | **USEFUL** — cheap, cosmetic today, but removes a dormant provenance risk before anything ever reads that field | |
| 3 — Stable message IDs / dedup | **NOT NEEDED** — already present and correctly implemented (Section 13) | |
| 4 — Explicit acknowledgement semantics | **UNKNOWN** — genuinely depends on future use; today's manual, human-checked usage pattern has never needed one, but Section 18's "human-out-of-loop discovery" future direction would need it | |
| 5 — Durable relay supervision (launchd) | **USEFUL**, arguably approaching **NECESSARY** if this channel is meant to be reliably available rather than "up when someone remembers to start it" — directly motivated by this exact mission's own starting condition (13 real days down) | |
| 6 — Crash/restart recovery beyond what exists | **NOT NEEDED** — already correct (Section 9, Scenario I/J; Section 14) | |

---

## 20. Future Verification Protocol

Designed, not executed, per the mission's own ten cases, mapped to this specific
architecture's real behavior:

1. **Offline receiver**: send from Codex while the "claude" identity's server is
   stopped; confirm the message sits durably in the sender's `outbox.jsonl` as
   `delivery: "failed"`, then restart the server and confirm a resend succeeds
   and is accepted.
2. **Independent consumers**: one session runs `relay.py read`; confirm a
   second, separate `notes.py pull` immediately after still sees the same
   content (already logically proven correct by source reading, Section 7 — this
   test would be the live confirmation).
3. **Notes isolation**: construct a real `[HUB-NOTE v1]`-tagged message, have a
   plain `read` consume it first, then confirm `notes.py pull` *still* finds and
   ingests it (proving the independent-cursor fix live, not just in source).
4. **Restart**: stop and restart one relay server mid-session; confirm the
   cursor and inbox both resume exactly where they left off (already indirectly
   confirmed today via the real restart in the prior mission — a dedicated test
   would isolate it further).
5. **Duplicate send**: replay an already-accepted signed payload verbatim;
   confirm the server responds `duplicate: true` and does not re-append.
6. **Concurrent read**: launch two simultaneous `read` calls against the same
   data-dir; confirm behavior matches Section 9's predicted benign race
   (duplicate visibility, not data loss) rather than a crash or corrupted cursor.
7. **Attribution**: run `hub/check_hub.py` from a session explicitly identifying
   as something other than Claude M5 (or with an injected environment override,
   if one existed); confirm today's real gap (`"claude-m5"` recorded regardless).
8. **Ordering**: send several messages in rapid succession from one sender;
   confirm `inbox.jsonl`'s append order matches send order exactly.
9. **Acknowledgement**: confirm directly that no mechanism today lets a sender
   distinguish "accepted" from "read" from "acted upon" beyond what Section 6
   already establishes from source alone.
10. **Machine restart**: design only, explicitly not run in this mission — verify
    after a real, already-planned reboot (not one triggered for this purpose)
    that the two relay processes do *not* restart on their own, confirming
    Section 14's predicted gap, and that all on-disk state is intact once
    manually restarted afterward.

---

## Required Verdicts

**Persistence**: **RELIABLE WITHIN A DEFINED BOUNDARY** — durable across process
death, terminal closure, and (by real, 13-day evidence) extended relay downtime;
not durable across a reboot without manual restart.

**Multi-Consumer Safety**: **OTHER DEFECT** — the specific reported case
(`read` vs. `notes.py pull`) is fixed; a narrower, structurally identical
collision remains for any two same-command callers sharing one data-dir.

**Attribution**: **HARDCODED / UNTRUSTWORTHY** — confirmed, unrepaired, currently
cosmetic (zero consumers), with a named, credible path to becoming load-bearing.

**Ordering**: **DEFINED**, per-sender/per-file — no cross-channel global ordering
exists or is claimed.

**Duplicate Handling**: **DEFINED** for transport-level retries; **ABSENT** for
independently re-typed/re-sent logical duplicates (by design choice, not a gap —
this mirrors the exact same distinction this session's Echo-Studio investigation
already made for a different subsystem).

**Restart Recovery**: **SUPPORTED** for the relay processes' own data on restart
(process or machine); **ABSENT** for automatically *restarting the processes
themselves* after death or reboot.

**Asynchronous Claude↔Codex Messaging**: **SUPPORTED WITH QUALIFICATIONS**
(Section 17).

**Process Supervision**: **MANUAL / FRAGILE** — confirmed, by design, not by
oversight; this exact fragility is what motivated this whole investigation's
starting event.

---

## 21. Remaining Unknowns

- Whether the two relay processes actually survive a real user logout (inferred
  from standard `nohup`/`disown`/reparent-to-PID-1 behavior, not directly tested).
- The exact behavior of `codex_relay`'s Scenario C (server dies mid-write, between
  the inbox append and the seen-ids save) — a real, narrow gap identified from
  source reading, never observed occurring in practice.
- Whether any other tool or script besides `hub/notes.py` and manual CLI
  invocations ever calls `claude_relay/relay.py read` or `codex_relay/relay.py
  read` — a full repo-wide grep found none, but a future addition could
  reintroduce a same-command collision risk (Section 7) without anyone
  connecting it back to this finding.

## 22. What This Establishes

- Persistent, asynchronous, cryptographically-authenticated, single-recipient
  messaging genuinely works between the agent pairs this architecture defines —
  proven by real historical evidence, not merely by design intent.
- The specific shared-cursor defect Codex reported on 2026-09-16 was real at the
  time and has since been independently fixed, the same day, through a different
  channel — a genuine, verifiable instance of "a finding almost went stale purely
  because of which channel it traveled through."
- A narrower version of the same defect class still exists, unfixed, for a
  different consumer pairing than the one originally reported.
- The `checked_by` attribution defect is real, unrepaired, currently harmless,
  and structurally capable of becoming a real provenance risk without further
  code changes elsewhere.
- Process supervision is genuinely manual and fragile, consistent with — and the
  direct cause of — this investigation's own starting condition.

## 23. What This Does NOT Establish

- Does not establish that any agent currently uses this channel autonomously,
  without a human-directed session choosing to check it (Section 18).
- Does not establish anything about Echo's own communication capabilities —
  confirmed structurally unrelated (Section 16).
- Does not establish that the narrow same-command cursor collision (Section 7)
  or the theoretical mid-write crash gap (Scenario C) has ever caused real harm —
  both are source-derived, plausible, unobserved-in-practice risks, not incidents.
- Does not establish a recommendation to build any repair — Section 19's
  classifications are inputs to a future decision, not a build order.

## 24. Repository / Runtime Integrity

- `codex_relay/relay.py`, `claude_relay/relay.py`, `hub/check_hub.py`,
  `hub/notes.py`: all read only, zero edits.
- No cursor file was deliberately manipulated; the two real messages exchanged
  during this investigation window (Codex's original send and this session's
  earlier acknowledgment reply) were legitimate, already-authorized relay
  traffic from the prior mission, not new activity generated by this audit.
- No credential value was printed, echoed, or otherwise exposed — confirmed by
  reviewing every command run in this mission; the one place a secret was
  needed (none, in this read-only pass) would have used the same inline
  substitution discipline as the prior mission.
- No LaunchAgent was created. No supervision was added. `start_echo.sh` was not
  modified. Echo's live process (PID 71538) was not stopped, restarted, or
  signaled.
- Nothing was staged, committed, or pushed. HEAD remained at
  `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`, throughout.
- The only new artifact produced is this report file itself, left untracked and
  unstaged.
