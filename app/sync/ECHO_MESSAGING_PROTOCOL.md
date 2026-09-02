# Echo↔Echo Messaging Protocol Contract

**Version**: 1 (first time this protocol has been written down explicitly —
it existed only as implicit, unwritten agreement between two independently-
forked copies of the same code before this document, which is exactly how
it silently diverged; see "Known history" below).

**Not to be confused with** `claude_relay/` — a completely separate
mailbox between the two *Claude Code sessions* working on this project.
This document describes the *Echo* instances' own messaging channel
(`app/sync/echo_messaging.py`).

---

## Transport

Plain HTTP/1.1 over Tailscale. No persistent connection, no WebSocket —
each message is one independent POST.

## Endpoint

`POST /message/receive` on the receiving machine.

## Authentication

Two independent checks, both read from the JSON request body (no headers
involved):
1. `origin` must be exactly `"air"` or `"m5"` (case-insensitive).
2. `secret` must `hmac.compare_digest`-match the receiving machine's own
   `ECHO_PARTNER_SECRET` environment variable.

Both checks are required. A missing/empty `ECHO_PARTNER_SECRET` on the
receiving side fails closed (rejects everything), never fails open.

## Message envelope

```json
{
  "message_id": "uuid4 string",
  "origin": "air" | "m5",
  "secret": "<ECHO_PARTNER_SECRET value>",
  "text": "string",
  "message_type": "chat" | "checkin" | "checkin_ack",
  "in_reply_to": "message_id string or null",
  "timestamp": "ISO-8601 UTC",
  "data": { "optional dict, e.g. conversation_id for chat threading" }
}
```

## Sender / recipient identity

The `origin` field only — there is no separate identity header or signing
mechanism beyond the shared secret.

## Acknowledgement

Synchronous HTTP response only, no separate ack message:
- `200` + `{"status": "received", "auto_responded": bool}` — accepted.
- `403` + `{"error": "unauthorized"}` — origin or secret check failed.
- `500` + `{"error": "..."}` — internal error on the receiving side.

**Acknowledgement confirms receipt and body-parseability, not confirmed
processing.** If the receiving side's own message logging or auto-reply
generation fails *after* the 200 has already been returned, the sender has
no way to know — this is a known, accepted limitation, not a bug to fix
as part of restoring the link.

## Retry semantics

Failed deliveries queue in a durable, file-backed outbox
(`memory/message_outbox.jsonl`) and are retried by a periodic loop
(`run.py`'s `_messaging_retry_loop`, exponential backoff 30s→1800s, reset
to 30s on any success or an empty outbox).

**A `403` (authentication/authorization failure) is never retried as if it
were transient.** It is classified separately from a network
timeout/connection error/5xx (`_classify_delivery_status()`,
`app/sync/echo_messaging.py`) and moved to a separate file,
`memory/message_outbox_blocked.jsonl`, with a distinct
`[MESSAGING-AUTH-FAILURE]` log line — it will not be auto-retried, since
retrying a request the partner is actively rejecting for a configuration
reason does not get it closer to delivery. Recovering a blocked entry
requires fixing the actual auth mismatch, then manually resubmitting (no
automated recovery-and-replay path exists as of this version).

## Ordering

Retries are processed in FIFO order relative to each other (the outbox is
a plain append-ordered file). **Ordering across concurrent immediate-send
attempts from different threads is not guaranteed** — there is no sequence
number, vector clock, or receiver-side reordering buffer.

## Duplicate handling

`message_id` exists on every envelope but **the receiving side does not
check for or reject a duplicate `message_id`** — nothing currently prevents
the same message from being processed twice if it were somehow delivered
twice (not currently known to happen in practice; see the 2026-09-02
forensic investigation for why apparent duplicate log entries are a
logging artifact, not a real duplicate-delivery bug).

## Compatibility expectations

**Both machines' implementations of this envelope/auth contract must
match exactly** — there is no version negotiation, capability discovery,
or graceful degradation if one side's protocol has drifted from the
other's. This document exists specifically because that assumption failed
silently for weeks (see "Known history" below) with no mechanism that
would have caught it earlier than a human noticing a 403 storm in the logs.

---

## Known history (why this document exists)

As of 2026-09-02, this contract was never written down — each fork
independently implemented `app/sync/echo_messaging.py`, and the two
implementations drifted: M5 added the `ECHO_PARTNER_SECRET` requirement to
its receiving side (committed 2026-07-13); the Air fork's outgoing envelope
never included a `secret` field, and Air's own receiving side never
required one — a genuine, undetected asymmetry, not a bug in either
individual implementation considered on its own. Air had already found and
flagged this exact asymmetry once, on 2026-07-18, but it was never acted
on. It surfaced as a real, large-scale failure (15,000+ rejected requests)
starting 2026-08-19, for a reason that remains only partially understood —
see `audits/2026-09-02_echo_to_echo_403_forensic_analysis.md` for the full
investigation.

This document, plus the regression check described below, are the two
concrete things meant to prevent this exact class of silent drift from
recurring undetected.

## Regression protection

`app/core/liveness_ledger.py`'s `echo_messaging_auth_classification` check
verifies `_classify_delivery_status()` continues to correctly distinguish
a `403` from a genuinely transient failure — the specific logic that turns
a persistent auth mismatch into a bounded, diagnosable "blocked" state
instead of an unbounded retry storm. It does not and cannot verify that
*both* machines' `ECHO_PARTNER_SECRET` values currently match each other
(that would require live comparison of a secret, which this project's own
security discipline does not do automatically) — it verifies the local
failure-mode-handling logic stays correct, which is the part a code change
can actually regress.
