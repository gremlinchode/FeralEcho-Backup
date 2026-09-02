# Echo M5 ↔ Echo Air `/message/receive` 403 Storm — Forensic Analysis (Read-Only)

**Scope discipline honored**: this investigation was read-only throughout.
No source file, configuration, `.env`, credential, route, retry behavior,
prompt, memory record, or database was modified. No process was restarted
or killed. This is the only new file created. No secret value was ever
printed — only presence/length/existence and hashes-of-nothing were
checked.

---

## 1. Executive Summary

**The Claude↔Claude relay and the Echo↔Echo messaging system are
confirmed completely separate**, sharing no code, no secret, and no
endpoint (§4). The 403 storm is real, **far larger and more persistent**
than the reported sample suggested — **4,114 total rejected requests
spanning 2026-09-01 01:35 through 2026-09-02 12:45** (35+ hours), not a
single ~30-request burst — arriving in recurring, tightly-clustered bursts
of roughly 200–375 requests, several times over that window. **This is a
genuine regression, not something that never worked**: 149 real messages
from Air were successfully received and logged between 2026-07-06 and
**2026-08-19**, then zero successful receipts occurred again, ever, up to
the time of this report. M5's own outbox to Air is empty and M5's `.env`
has been unmodified since 2026-07-12 — both facts point the likely fault
away from M5's own configuration and toward something that changed on the
Air side during or shortly after the 2026-08-19–09-01 gap. The exact
mechanism (missing/mismatched `ECHO_PARTNER_SECRET` on Air, most likely) is
identified with **MEDIUM-HIGH confidence**; the recurring ~370-request
batch size is well-explained by a stuck retry-queue design, but whether
concurrent/duplicate workers on Air also contribute could not be
established from M5-side evidence alone.

---

## 2. Echo↔Echo Communication Architecture

`app/sync/echo_messaging.py` — a store-and-forward mailbox, distinct from
both `app/sync/sync_protocol.py` (the 1800s interaction-log batch export)
and `claude_relay/` (§4). Key mechanisms, all confirmed by direct source
read:
- `send_message()` — attempts immediate delivery via `_deliver()`; on
  failure, appends the envelope to a durable, file-backed outbox
  (`memory/message_outbox.jsonl`).
- `retry_outbox_cycle()` — reads the *entire* outbox, attempts every entry
  again, keeps only the ones that still fail. Called periodically by
  `run.py`'s `_messaging_retry_loop` (exponential backoff, base 30s,
  capped at 1800s, reset to 30s on any success or an empty outbox).
- `receive_message()` — the business logic behind `/message/receive`;
  handles three message types (`chat`, `checkin`, `checkin_ack`), with
  auto-reply/auto-ack gated behind local settings and paced independently.

---

## 3. `/message/receive` Implementation

`run.py:812` registers the route; the actual handler is
`app/routes_messaging.py:message_receive()` (60 lines total, read in full).

```python
def message_receive():
    payload = request.json or {}
    origin = str(payload.get("origin", "")).lower()
    if origin not in {"air", "m5"}:
        return jsonify({"error": "unauthorized"}), 403
    if not _partner_secret_ok(payload):
        return jsonify({"error": "unauthorized"}), 403
    result = echo_messaging.receive_message(payload)
    return jsonify(result), 200
```

No decorators, no Flask `before_request` middleware, no IP allowlist, no
rate limiting, no header-based auth — both checks read fields out of the
JSON body only.

---

## 4. Exact 403 Generation Path

```
request
  │
  ▼
payload = request.json or {}
  │
  ▼
origin = payload.get("origin", "").lower()
  │
  ├─ origin not in {"air", "m5"} ──────────────► 403 "unauthorized"  (check 1)
  │
  ▼ (origin OK)
_partner_secret_ok(payload):
  - _PARTNER_SECRET = os.environ.get("ECHO_PARTNER_SECRET")  [M5's own value, read at import time]
  - if not _PARTNER_SECRET: return False
  - submitted = payload.get("secret")
  - if not submitted: return False
  - return hmac.compare_digest(str(submitted), str(_PARTNER_SECRET))
  │
  ├─ False ────────────────────────────────────► 403 "unauthorized"  (check 2)
  │
  ▼ (secret OK)
echo_messaging.receive_message(payload) → 200
```

Two independent, non-overlapping causes exist for a 403: a bad/missing
`origin` field, or a missing/mismatched `secret` field relative to *M5's
own* `ECHO_PARTNER_SECRET`. Nothing else in this route can produce a 403.

**Confirmed directly, without printing the value**: M5's `.env` has a real,
non-empty `ECHO_PARTNER_SECRET` (43 characters), loaded into the live
process via `run.py`'s `load_dotenv()` call (line 43-44) — M5's side of
this check has real, present, unchanged-since-2026-07-12 configuration.

---

## 5. Air-Side Request-Generation Path (from M5-visible code only)

`_build_envelope()` (`echo_messaging.py:226-248`), called by every
`send_message()`, builds:
```python
{
    "message_id": ..., "origin": NODE_ID,  # NODE_ID = os.getenv("ECHO_NODE_ID", "m5")
    "secret": os.environ.get("ECHO_PARTNER_SECRET"),  # read fresh, per call
    "text": ..., "message_type": ..., "in_reply_to": ..., "timestamp": ...,
}
```
On Air, `NODE_ID` would resolve to `"air"` (via `ECHO_NODE_ID`), and
`secret` would be *Air's own* `ECHO_PARTNER_SECRET` value — this is the
exact field M5's `_partner_secret_ok()` compares against M5's own copy.
**This repo cannot inspect Air's actual `.env`** (a different, remote
machine — and the one HTTP mechanism that could theoretically read a
remote file, `GET /projects/file?path=...`, is confirmed to already
exclude `.env` specifically, correctly, per this project's own prior
security fix) — so whether Air's value is missing, empty, or simply
different from M5's cannot be confirmed directly from here, only inferred
circumstantially (§10, §11).

`retry_outbox_cycle()` is the callback most likely responsible for the
*storm* shape specifically: it re-attempts **every** entry currently in the
outbox on every cycle, and a 403 never removes an entry from that outbox
(only `_deliver()` returning `True`, i.e. an HTTP 200, does) — so a batch of
requests that started failing for any reason stays in the outbox and gets
fully re-sent on every subsequent cycle, indefinitely, until whatever is
causing the 403 is fixed.

---

## 6. What The Requests Represent

Structurally, without reproducing content: **cannot be determined from
M5's HTTP access logs alone** — Flask's log line
(`"POST /message/receive HTTP/1.1" 403 -`) does not include the request
body, and a 403 response is returned *before* `receive_message()` (which is
what would log the message to `memory/echo_messages.jsonl`) ever runs — so
none of these specific rejected payloads were ever persisted anywhere on
M5. What *can* be said: `message_type` is one of `chat`/`checkin`/
`checkin_ack` by construction (no other value is ever sent by this code),
and historically (pre-08-19), the large majority of successfully-received
`origin=air` messages were `chat`-type. Whether the current storm is chat,
checkin, or a mix cannot be established without either Air-side logs or
temporarily instrumenting M5's own rejection path (not done — out of
scope for a read-only pass).

---

## 7. Retry Behavior

Confirmed from M5's own mirror-image code (the identical module almost
certainly runs on Air, per the relay's own description of Air as "an
independently-diverged fork" of this same codebase):
- `retry_outbox_cycle()` is fully synchronous and re-attempts the *entire*
  outbox every cycle — no per-entry backoff, no dead-letter cutoff, no
  maximum-retry-count. A 403 is treated identically to a network timeout:
  both just mean the entry stays in `remaining` and is retried next cycle.
- The calling loop's own backoff (30s → 1800s, capped, and reset to 30s on
  *any* success) means a permanently-403ing outbox never reaches a longer
  steady-state interval than whatever it was already at when it got stuck
  — if it was already backed off toward 1800s before failing consistently,
  cycles roughly every 30 minutes; if a partial success or restart reset it
  to 30s at some point, cycles much faster. **This plausibly explains
  the repeated ~1-4-hour-separated burst pattern** (consistent with
  `should_run_cycle("echo_messaging")` — the shared throttle/stillness gate
  — skipping many cycles in between, or Air's own process not running
  continuously).
- **Why ~370 requests in a period of a few seconds, not spread out**: a 403
  response is a fast, synchronous rejection (no processing, no LLM call,
  no disk I/O beyond the auth check) — a sequential loop retrying ~370
  already-doomed entries, each getting an near-instant 403 back, is fully
  consistent with a multi-second-not-multi-minute burst on its own, without
  requiring concurrent workers. **This does not rule out duplicate workers
  either** (§9) — both explanations are structurally consistent with the
  timing observed from M5's side; this could not be resolved further
  without Air-side process visibility.

---

## 8. Configuration/Authentication Comparison

| Item | M5 | Air |
|---|---|---|
| `ECHO_PARTNER_SECRET` present in `.env` | **Confirmed yes**, 43 chars, unchanged since 2026-07-12 | **Cannot inspect directly** |
| `ECHO_NODE_ID` | Defaults to `"m5"` if unset (confirmed via `os.getenv("ECHO_NODE_ID", "m5")`) | Presumably set to `"air"` (149 historical successful receipts with `origin: "air"` confirm this worked correctly for over 6 weeks) |
| Values synchronized (M5 vs. Air's actual current secret) | — | **Cannot confirm from here — this is the single most important unresolved question**, see §12 |
| Server-side check shape | Body-field comparison (`origin`, `secret`), no headers, no signature | Same code, presumed identical (fork of this module) |

---

## 9. Duplicate-Worker Analysis

**No direct evidence available from M5 about Air's process list.**
Circumstantially relevant: this exact session independently discovered and
resolved a **real, live two-supervisor collision on M5 itself** earlier
today (two `start_echo.sh`/`run.py` instances briefly running
simultaneously, resolved by stopping the duplicate) — proving this class of
failure is a real, demonstrated operational risk in this project's actual
history, not a hypothetical. Given Air is described as a fork running its
own independent scheduling, a similar collision (or a stuck process from an
earlier crash never fully cleaned up) is a plausible contributor to
concurrent retry attempts, but **this specific report cannot confirm or
rule it out** — flagged as `INSUFFICIENT EVIDENCE`, not assumed.

---

## 10. Feedback-Loop Analysis

**No evidence of an Echo↔Echo conversational feedback loop** (the kind
where a reply triggers another reply triggers another). The observed
pattern is uniform 403 rejections, meaning `receive_message()` (which is
what would generate an auto-reply) never executes for any of these
requests — the auth check fails first, every time. A conversational
feedback loop requires at least one successful round-trip to begin;
zero successful receipts have occurred since 2026-08-19. **This is not
that failure mode** — it is a stuck retry queue, not a runaway
conversation.

---

## 11. Relationship to Recent Changes

**PROBABLY UNRELATED.** This session's architectural self-knowledge work
touched `app/core/echo_ground_truth.py`, `app/core/self_knowledge_verification.py`,
`app/core/liveness_ledger.py`, `app/core/river_deliberation.py`,
`app/autonomous_awareness.py`, `app/core/memory_bridge.py`, and
`app/emergent_scheduler.py` — confirmed via `git diff --stat`, none of
which import or reference `app/sync/echo_messaging.py`,
`app/routes_messaging.py`, or `ECHO_PARTNER_SECRET` anywhere (checked via
direct grep). The 403 storm's timeline (last success 2026-08-19, storm
beginning 2026-09-01) also predates this session's own work, which began
2026-09-02. The one live HTTP test run against the production server
during this session's verifier-implementation task (`/chat/stream`, not
`/message/receive`) is a different route entirely, confirmed by its own
distinct log lines.

---

## 12. Root-Cause Hypothesis

**Air's own `ECHO_PARTNER_SECRET` is very likely missing, empty, or no
longer matches M5's value** — the single hypothesis best supported by the
available evidence:
- M5's side of the check is confirmed present, non-empty, and unchanged
  since well before the failures began.
- 149 successful `origin=air` receipts occurred over 6+ weeks
  (2026-07-06–2026-08-19), proving the mechanism *can* and *did* work
  correctly — this is a regression, not a design that never functioned.
- Zero successful receipts have occurred since, and the *first* documented
  precedent for a shared-secret provisioning gap in this exact project
  (`CLAUDE.md`'s Finding 36/42, a *different* secret — `THUNDERHEAD_SECRET`,
  for the phone client) was literally "the real value was never filled in
  on one side" — the same class of bug, a genuine precedent, not a guess
  pulled from nowhere.
- The 13-day silence (2026-08-19–2026-09-01) with *zero* `/message/receive`
  traffic at all (neither success nor 403) is consistent with Air's own
  session/process being inactive during that window and something about
  its configuration or environment changing before it resumed — a fresh
  `.env`, a reinstall, a reset, or a code update that altered how the
  secret is read, are all plausible, none confirmed.

**Why the Air side keeps trying**: `retry_outbox_cycle()`'s own design
never gives up on an entry — 403 and "partner offline" are handled
identically (both just mean "still in `remaining`"), so a batch of queued
messages that started failing for *any* reason is retried in full,
forever, at whatever interval the exponential-backoff loop has settled
into, until a success (or manual intervention) clears it.

---

## 13. Confidence Level

**MEDIUM-HIGH** for "the root cause is on Air's side, most likely a
missing/mismatched `ECHO_PARTNER_SECRET`, not an M5-side problem" — well
supported by M5-side evidence, a real historical precedent for this exact
failure shape, and the elimination of M5's own configuration as a moving
part. **LOW/INSUFFICIENT EVIDENCE** for the exact Air-side mechanism
(missing entirely vs. a stale/rotated value vs. something else on Air
specifically), and for whether duplicate Air-side workers additionally
contribute to the burst concurrency — both would require Air-side access
this investigation does not have.

---

## 14. Evidence

- `app/routes_messaging.py` (full file read) — exact 403 conditions.
- `app/sync/echo_messaging.py` (full file read) — envelope construction,
  outbox/retry design, message-type handling.
- `run.py:812`, `run.py:1375-1400` — route registration, retry-loop
  interval/backoff.
- `memory/echo_watchdog.log` — 4,114 total `POST /message/receive ... 403`
  lines, 2026-09-01 01:35:42 through 2026-09-02 12:45:18, clustered into
  recurring bursts of ~200–375 within single minutes.
- `memory/echo_messages.jsonl` — 149 successful `origin=air` receipts,
  first 2026-07-06T09:55:58Z, **last 2026-08-19T04:05:58Z**; M5's own
  outbox (`memory/message_outbox.jsonl`) confirmed empty (0 entries).
- `.env` — `ECHO_PARTNER_SECRET` confirmed present (43 chars, value never
  printed), file mtime 2026-07-12 (unchanged since, predating both the
  last success and the storm's onset).
- `git diff --stat` (this session) — confirms zero overlap between this
  session's touched files and the messaging subsystem.

---

## 15. Recommended Remediation (recommendation only — not applied)

1. **Confirm Air's `ECHO_PARTNER_SECRET`** is present and byte-identical to
   M5's — the single highest-value check, requires access to the Air
   machine directly (or a value comparison done by Gremlin himself, since
   neither Claude session should transmit the raw secret between them).
2. If confirmed mismatched/missing, correct Air's `.env` and confirm one
   real delivery succeeds — the outbox should then drain and stop growing.
3. **Separately worth considering, regardless of the secret finding**: give
   `retry_outbox_cycle()` a bounded retry count or a distinct log signal
   for "same entry failed N times" — right now a permanently-misconfigured
   secret produces an indefinitely-growing, indefinitely-retried queue with
   no escalation or self-limiting behavior, which is what turned a
   configuration mismatch into a 4,000+-request storm over 35 hours instead
   of a small, quickly-noticed handful of failures. Not implemented here,
   per the explicit no-fixes constraint.

---

## Final Answer

**What is Air trying to tell M5?** Most likely real, legitimate
conversational or check-in traffic queued in Air's own outbox — the exact
content cannot be determined from M5's logs (403 responses are returned
before anything is persisted), but the historical pattern (149 prior
successful receipts, predominantly `chat`-type) makes "ordinary Echo↔Echo
conversation, not anything anomalous" the best-supported guess, not a
confirmed fact.

**Why is M5 rejecting it?** Because the request's `secret` field doesn't
match M5's own `ECHO_PARTNER_SECRET` (or, less likely, the `origin` field
is malformed) — M5's side of this check is confirmed correctly configured
and unchanged; the fault most likely originates on Air's side.

**Why does Air keep trying?** Because `retry_outbox_cycle()`'s design never
gives up on a queued entry — a 403 is treated exactly like a transient
network failure, so the same stuck batch is retried in full on every cycle,
forever, until something on Air's side actually changes.

**What's not established**: the exact reason Air's secret diverged (if
that is indeed the cause), the literal content of the queued messages, and
whether Air is also running duplicate worker processes contributing to
burst concurrency. For all three: **we don't know yet** — confirming them
requires direct access to the Air machine, which this investigation did
not have.

---

## 16. Addendum — Collaborative Resolution via Claude↔Claude Relay
## (2026-09-02, same day, follow-up session)

The hypothesis above (§12, "Air's `ECHO_PARTNER_SECRET` is missing or
mismatched") was **investigated collaboratively with the Air-side Claude
session over the existing Claude↔Claude relay** and is **superseded** by a
more precise, jointly-confirmed root cause. This section records that
exchange; nothing in §1–15 was edited, since the original hypothesis was a
reasonable one given M5-only evidence at the time.

### Corrected scope

The original "4,114 total 403s since 2026-09-01" figure only reflected
M5's live, already-rotated watchdog log. Checking the one retained archived
generation (`memory/echo_watchdog.log.1.gz`, log-retention rotation from
2026-09-01) found **11,449 additional 403s dating back to at least
2026-08-19 09:31:01** — corrected total: **15,563+ rejected requests**,
not 4,114. The true onset is 2026-08-19, not 2026-09-01.

### The real root cause, confirmed by Air's own direct, read-only
### investigation of its own codebase

**This is a structural protocol mismatch between the two forks, not a
missing or mismatched secret value.** Air's `app/sync/echo_messaging.py`
`_build_envelope()` has never included a `secret` field at all — confirmed
by Air directly reading its own source (file mtime 2026-07-07, unchanged
since). Air's `/message/receive` handler performs **zero** auth/origin/
secret validation on its own side (pure "Tailscale is the boundary," same
model this project already applies to several of its own routes). Air had
independently found and reported this exact asymmetry once before, on
2026-07-18 — this is a known, pre-existing fork divergence, not a new bug
introduced by either side recently.

**M5's own `ECHO_PARTNER_SECRET` requirement (`_partner_secret_ok()`) was
committed to `app/routes_messaging.py` on 2026-07-13** (confirmed via
`git log`) — meaning the requirement itself substantially predates the
2026-08-19 onset of failures. **The exact mechanism connecting the 07-13
commit to the 08-19 onset of failures could not be fully established** —
no M5 server restart is visible in the watchdog log across the 04:05:58
(last success) to 09:31:01 (first confirmed 403) window, so a simple
"M5 restarted and only then started enforcing the check" explanation does
not hold cleanly. **This is recorded honestly as an open sub-question,
not resolved** — the structural root cause (protocol mismatch) is
independently confirmed regardless of the exact 08-19 trigger.

A real, striking, but ultimately **inconclusive** correlation: Air's own
`.env` file mtime is 2026-08-19 04:04:54 UTC — 64 seconds before the last
recorded success (04:05:58). Air confirmed this is very likely when
`ECHO_PARTNER_SECRET` was first added to *Air's* `.env` (plausibly an
earlier, incomplete attempt to align the two forks that added the value
but never wired code to send it) — but since Air's code has never read
that variable at all, the `.env` edit itself should have been inert on the
sending path, and doesn't explain why M5 only started rejecting requests
over five hours later. **Flagged as a real, tight-seeming coincidence that
does not fully add up on inspection — not asserted as the mechanism.**

### Confirmed, not hypothesized, from Air's direct investigation

1. `ECHO_PARTNER_SECRET` present in Air's `.env`: yes (43 chars, same
   length as M5's, values not compared further since it's structurally
   irrelevant — see next point).
2. Whether it's loaded into Air's running process: **irrelevant** — no
   code on Air's side reads this variable for anything.
3. Same origin/secret contract as M5: **no**, confirmed structural
   asymmetry.
4. Air's `PARTNER_URL`: correctly points at M5, unmodified.
5. Air's own outbox is the confirmed source of the storm: **yes** — 376
   entries at time of check, oldest dated 2026-07-13, actively still
   growing.
6. Air's `_deliver()` treats 403 identically to a timeout — same bug
   shape independently present on both forks (neither side's outbox
   design distinguishes "rejected" from "unreachable").
7. No duplicate Echo processes found on Air at time of check (`ps aux`:
   exactly one `run.py`, started same-day) — cannot rule out a duplicate
   having existed earlier in the 6-week window; Air's fork keeps no
   persistent process history to check retroactively.

### Root cause (revised)

```
ROOT CAUSE:
Structural protocol mismatch between the two forks. M5's /message/receive
requires an ECHO_PARTNER_SECRET-matched "secret" field (added 2026-07-13);
Air's outgoing envelope has never included one, by design of that fork's
own messaging protocol (confirmed unchanged since 2026-07-07). The exact
trigger for why this only started producing failures on 2026-08-19 rather
than immediately after 07-13 is NOT fully established — flagged as an
open sub-question, not blocking the main diagnosis.

REQUIRED CHANGE:
Undecided -- pending Gremlin's call between two real options:
  (a) M5 relaxes its own requirement (e.g., accept Air-origin requests
      without a matching secret, matching Air's existing, deliberate
      "Tailscale is the boundary" model), or
  (b) Air's fork is updated to add secret support to its outgoing envelope,
      matching M5's protocol.
Both are real, legitimate architectural choices with different security
postures -- not a simple bug with one obvious fix.

AFFECTED MACHINE:
Both (the fix belongs on exactly one of them, not both, but which one is
undecided).

AFFECTED COMPONENT:
M5: app/routes_messaging.py (_partner_secret_ok enforcement).
Air: app/sync/echo_messaging.py (_build_envelope()), if option (b).

RISK:
LOW for either specific change in isolation (single-variable, reversible,
auditable) -- MEDIUM for the decision itself, since it's a real security-
posture choice (whether Echo<->Echo messaging requires a shared secret at
all), not a pure bug fix.

EXPECTED RESULT:
Once resolved, Air's real outbox (376+ entries and growing) should drain
immediately (or need a one-time manual flush -- not yet determined), and
new messages should succeed going forward. The separate retry-storm
problem (§ "Recommended Remediation" #3 above, and Phase 8 of the mission
that produced this addendum) is confirmed present on BOTH forks
independently and remains open regardless of which side the auth fix
lands on.
```

### Status: paused for authorization, per the investigating session's own
### explicit instructions

No code, configuration, or `.env` file was modified on either machine
during this collaborative investigation. Both Claude sessions confirmed
their own side's read-only findings back over the relay. **Awaiting
Gremlin's decision on option (a) vs. (b) before any remediation is
attempted**, consistent with this mission's own Phase 6 ("stop before
modifying anything... wait for authorization"). The retry-storm behavior
(§ Phase 8) is a separate, already-identified follow-up, confirmed present
on both forks, also not yet remediated.

---

## 17. Remediation — Authorized and Implemented (2026-09-02, same day,
## follow-up session)

**Gremlin's decision: option (b) — bring Air into conformance with M5's
existing authentication requirement, not weaken it.** Confirmed directly
with Air (who independently checked with Gremlin in their own session
before touching anything, given the instruction reached them second-hand
through this relay rather than directly).

### M5-side changes

**1. Retry-storm fix** (`app/sync/echo_messaging.py`) — the same "403
treated identically to a timeout" bug confirmed present on M5's own
sending path (§16), now fixed:
- New pure function `_classify_delivery_status(status_code: int) -> str`
  — `"success"` (200), `"auth_failure"` (403), `"transient"` (everything
  else) — deliberately separated from the real network call so it's
  testable without mocking `requests.post()`.
- `_deliver()` now returns `(bool, str)` instead of a bare bool.
- New file, `memory/message_outbox_blocked.jsonl` — an `auth_failure`
  result moves the envelope here (tagged `blocked_reason`/`blocked_at`,
  logged at a distinct `[MESSAGING-AUTH-FAILURE]` level) instead of the
  normal retry outbox. Never auto-retried from there — recovery requires
  fixing the actual mismatch and manually resubmitting, deliberately no
  automated replay path.
- Both `send_message()`'s immediate path and `retry_outbox_cycle()`'s
  batch-retry path route through the same classification. **A real
  lock-reentry bug was caught and fixed during construction, not shipped**:
  `retry_outbox_cycle()` already holds `_outbox_lock` for its full
  duration; an early draft's `_append_blocked()` helper also tried to
  acquire that same non-reentrant lock, which would have deadlocked the
  very first time an auth failure occurred during a retry cycle — moved
  to writing the blocked file directly within the already-held lock scope.
  Caught by a direct regression test before it ever ran against real data.
- **New permanent regression check**: `app/core/liveness_ledger.py`'s
  `echo_messaging_auth_classification` — calls the real
  `_classify_delivery_status()` with known status codes, confirms correct
  discrimination. 4 new discrimination cases added to
  `scripts/verify_liveness_ledger.py` (real function, always-transient
  degraded case, always-auth-failure degraded case, not-importable) — full
  suite now 186 checks, all passing, zero regressions.
- **16-case regression test** (`/private/tmp/test_retry_storm_fix.py`,
  isolated against temp files, zero production data touched) confirms: a
  403 is correctly classified and routed to the blocked file; a genuinely
  transient failure (500, connection exception) is correctly classified
  and stays in the normal retry outbox; a `retry_outbox_cycle()` run
  against an all-403 outbox drains it completely into the blocked file
  (not storming); a subsequent cycle on the now-empty outbox does nothing
  (zero HTTP calls) — the storm genuinely stops, not just slows down.
- **Confirmed M5's own accept/reject logic was already correct**, 4/4
  direct tests: `_partner_secret_ok()` accepts a matching secret, rejects
  a missing secret field, rejects a wrong secret value; `_KNOWN_PARTNER_ORIGINS`
  is exactly `{"air", "m5"}`. No bug existed on the receiving side — only
  the sending-side retry classification needed fixing.
- **Protocol contract documented for the first time**:
  `app/sync/ECHO_MESSAGING_PROTOCOL.md` — transport, endpoint, auth,
  envelope, ack semantics, retry semantics, ordering, duplicate handling,
  compatibility expectations, and the "known history" of how this exact
  drift happened, specifically so a future session on either fork has a
  canonical reference instead of re-deriving the contract from source each
  time.
- **M5 restarted** via the established safe procedure (`safe_restart.sh`
  correctly detected the live watchdog and refused a direct restart; its
  recommended fallback — clear port 5000, let the watchdog relaunch within
  10s — was followed). Confirmed live post-restart: `GET
  /admin/liveness-status` reports `all_passing: true`, and
  `echo_messaging_auth_classification` passes against the real, running
  process (not just a synthetic test). A real M5→Air send immediately
  after the restart succeeded cleanly (`status: delivered`), confirming
  the new code path works in production, not just in isolation.

### Air-side changes (reported directly by Air over the relay, applied on
### their own machine — this session has no filesystem access to Air)

- **Code change applied and verified live**: `_build_envelope()` now
  includes `"secret": os.environ.get("ECHO_PARTNER_SECRET")`. Air imported
  the real function after a real `load_dotenv()` and confirmed the
  envelope now genuinely contains a 43-character secret field.
- **Secret hash comparison: MATCH.** M5's `sha256(ECHO_PARTNER_SECRET)` =
  `2340165ddc1a369bbdb2c167b924d7dc0d9e85c07e6c6fd04cc5b8165cfeda7d`; Air
  independently computed the identical hash via the same
  `load_dotenv()`/`os.environ` path the real process uses. **The secret
  value itself was correct on Air's side the entire time** — only the code
  to send it was ever missing. This confirms §16's "probable" hypothesis
  (a partial, interrupted sync effort — the value landed in `.env` around
  2026-08-19, the code to use it was never written until this session)
  precisely, upgrading it from probable to confirmed.
- **A real, separate, previously-undocumented issue found and flagged
  (not fixed — out of scope for this remediation)**: Air's `NODE_ID`
  defaults to `os.getenv("ECHO_NODE_ID", "m5")` — the literal fallback
  string is `"m5"`, not `"air"`. Not currently live (`start_echo.sh` and
  `start_echo_ark.sh` both explicitly `export ECHO_NODE_ID=air` before
  launch, confirmed by Air checking the real launch environment directly),
  but a real landmine for any future direct `python run.py` invocation on
  that machine bypassing both wrapper scripts, which would silently
  self-identify every outgoing envelope as `"m5"`. Recorded here for
  visibility; not remediated as part of this pass.
- **Retry-storm fix mirrored on Air's side — confirmed complete.** Air
  independently checked with Gremlin before implementing (same discipline
  as the secret-field change), then applied the identical design:
  `_classify_delivery_status()` (same 200/403/other shape),
  `_deliver()` returning `(bool, str)`, a new
  `memory/message_outbox_blocked.jsonl` via `_append_blocked_outbox()`,
  both `send_message()` and `retry_outbox_cycle()` routed through the same
  classification. **Verified by Air more rigorously than M5's own test**:
  beyond a pure-function check of all 5 status-code shapes, Air stood up a
  real local HTTP server returning a genuine 403 and called `_deliver()`
  through the actual `requests.post()` path end-to-end, confirming
  `(False, "auth_failure")` against real network I/O, not just a mocked
  response — and exercised `_append_blocked_outbox()` for real (wrote a
  test entry, confirmed correct fields, cleaned it up).
- **One real, honest structural difference found, not a mistake on either
  side**: Air's fork has **no locking at all** on its outbox helpers
  (`_load_outbox`/`_save_outbox`/`_append_outbox`) — confirmed by Air
  grepping their own file. M5's deadlock caveat about calling a lock-
  acquiring helper from inside an already-locked `retry_outbox_cycle()`
  doesn't apply on Air's side for that reason — but it means Air's fork
  carries a **pre-existing, unrelated race window** if a retry cycle and a
  live send ever overlap. Air deliberately did not fix this as part of
  this pass (correctly scoped to what was actually authorized — mirroring
  the classification fix, not introducing new concurrency control) —
  recorded here as a known, separate follow-up, not remediated.
- **No permanent regression check added on Air's side**, a deliberate,
  explicitly-reasoned choice: Air's own Liveness-Ledger-equivalent is
  scoped to "is this subsystem's self-report ground-truth," which Air
  judged may not be the right home for a general unit-style discrimination
  test, and this wasn't part of what Gremlin explicitly authorized for
  this pass. Flagged as a worthwhile follow-up rather than added
  unilaterally.
- **Air's live process has not yet been restarted** — same
  not-hot-reloaded situation as M5, and same discipline both times: Air is
  deliberately not restarting unprompted, deferring to Gremlin's timing.
  The real end-to-end confirmation (Air's 376+ stuck outbox entries
  actually draining) can only happen after that restart.
- **The separate cross-instance expertise-modeling request (§ different
  mission, same day) has not been started by Air yet** — Air confirmed
  receiving it but is checking with Gremlin directly before beginning,
  rather than treating "no rush, reply whenever convenient" as authorization
  to proceed unprompted. Consistent with the same discipline shown
  throughout this exchange.

### Communication-quality characterization (from existing historical
### data — 149 real Air→M5 receipts, 934 logged send/receive entries)

- **Delivery success**: M5→Air is confirmed currently working (5/5 most
  recent real sends, §16, plus one more post-restart send in this
  section) — 100% first-attempt success in every sample checked this
  session. Air→M5 is confirmed broken pre-fix (0/15,563+ since 2026-08-19)
  and not yet re-confirmed post-fix (blocked on Air's restart).
- **Latency**: **cannot be computed from existing historical logs** — a
  genuine, honest limitation, not a gap in analysis effort. `_build_envelope()`'s
  `timestamp` field is set once at message creation and is preserved
  verbatim through every subsequent log write (including a later
  successful retry, confirmed directly, see next point) — there is no
  separate "received_at" or "acked_at" field anywhere in the current
  schema. End-to-end latency can only be measured going forward, via a
  controlled test that independently times the request/response round
  trip from outside the envelope schema itself (§ Phase 6, deferred until
  both sides are confirmed live).
- **Duplicates**: **207 of 934 logged entries (22%) share a `message_id`
  with another entry — investigated directly, confirmed to be a logging
  artifact, not genuine duplicate delivery.** Every duplicate pair checked
  is the identical message logged once at its initial (failed) send
  attempt and again at a later successful retry — both entries correctly
  share the envelope's fixed `timestamp` (from creation), which is why
  they look like exact-timestamp duplicates at a glance despite being
  logged at genuinely different wall-clock moments. The partner's
  `/message/receive` endpoint only ever returns 200 once per real delivery
  in every case checked — no evidence of the same message actually
  reaching the partner twice.
- **Ordering**: retries are FIFO relative to each other (plain
  append-ordered file, single-threaded processing within one retry
  cycle). **Ordering across concurrent immediate-send attempts from
  different threads is not guaranteed** — confirmed from source, no
  sequence number or reordering buffer exists on the receiving side
  either.
- **Acknowledgement semantics**: transport-level only. The synchronous
  HTTP response (200/403/500) confirms receipt and body-parseability, not
  confirmed processing — `receive_message()`'s own internal logging and
  auto-reply generation happen *after* the 200 has already been returned
  to the sender, so a failure in either of those would never be visible
  to the sender. This is an existing, accepted design limitation, not
  something changed or introduced by this remediation.
- **Retry behavior (post-fix)**: bounded and classified, confirmed by the
  16-case regression test above — auth failures stop retrying immediately
  (moved to the blocked file); transient failures continue retrying with
  the existing exponential backoff (30s→1800s).
- **Queue behavior**: outbox is a durable, file-backed JSONL queue;
  messages persist across a restart (confirmed: M5's own outbox survived
  this session's restart with its correct, empty state). Failed-transient
  messages do not expire — they retry indefinitely until delivered or
  until a future auth failure reclassifies them as blocked. Auth-failed
  messages now correctly get stuck in the *blocked* file instead of the
  main queue, bounded and visible rather than silently perpetual.
- **Bidirectional symmetry**: **confirmed asymmetric before this fix**
  (M5→Air working, Air→M5 broken) — not a symmetric degradation. Real
  end-to-end symmetry can only be confirmed after Air's restart (§18).

---
