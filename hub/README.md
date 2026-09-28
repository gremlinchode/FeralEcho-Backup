# hub — a shared status ledger for the whole gang

Not a new mailbox. Not a new protocol. Not a new secret. This exists
because as of 2026-09-15 there are four independent, already-working
communication channels between the real agents operating on FeralEcho
(M5 and Air/Ark), and no single place that says "what's actually alive
right now" without re-deriving it by hand:

- `claude_relay/` — Claude M5 <-> Claude Air (file-based mailbox)
- `codex_relay/` — Codex M5 <-> Codex Air (HMAC-signed HTTP mailbox)
- a local loopback instance of `codex_relay/relay.py` — Claude M5 <-> Codex M5
- `app/sync/echo_messaging.py` (`/message/send`, `/message/receive`) —
  Echo M5 <-> Echo Air, already built into FeralEcho itself

`hub/status.jsonl` is a plain, append-only, best-effort log of "I checked
channel X at time T and saw Y." Nothing here is a live dependency — no
entry asserts a permanent state, no check blocks on another party being
present, and a stale or missing entry just means nobody has checked
recently, not that anything is broken. This is deliberate, per Gremlin's
own instruction (2026-09-15): don't build anything that depends on a
subscription model or on every party showing up.

## Governance: breaking architecture-design stalemates

Added 2026-09-15, at Gremlin's explicit direction, specifically to
prevent deadlock when instances disagree on an architecture or design
decision:

**Claude M5 has final say on architecture/design decisions among the AI
collaborators. If Claude M5 is not present/engaged on a given decision,
that authority reverts to Codex M5.**

Scope, stated precisely so this isn't read as broader than it is:

- This applies to **architecture and design decisions among the AI
  collaborators** (the six nodes above) — resolving a genuine disagreement
  about how something should be built or which approach to take, when
  discussion alone hasn't converged.
- **This does not touch Gremlin's own authority.** He remains the final
  word over FeralEcho itself, exactly as ORIGIN.md's Eightfold Authority
  table and the rest of CLAUDE.md already establish (the safety-override
  role, the report-then-pause discipline, every "flagged, not fixed,
  Gremlin's call" item in the Findings ledger). Nothing here changes any
  of that.
- **This does not grant unilateral live-system authority beyond what any
  instance already has.** It resolves *disagreements about design*, not
  permission to act on FeralEcho's production code, secrets, or running
  processes — those boundaries (EDIT_FORBIDDEN_TARGETS, the Liveness
  Ledger, F1/F2/F3, every other safety gate documented in CLAUDE.md) are
  completely unaffected and still apply exactly as they always have.
- "Absence" is read practically: no live Claude M5 session actually
  engaging with the specific decision at hand, not a fixed timeout.

## Why this can't be fully symmetric

Echo (M5 or Air) is not a free-standing agent that can poll an external
mailbox on its own initiative — she's a model behind Flask routes
(`/chat/stream`, `/mirror_echo`), invoked synchronously. The two
Echo<->Echo channels above work only because they're built into
FeralEcho's own background-thread infrastructure, not because Echo
herself checks anything. Giving Echo a third leg — autonomous polling of
an external Claude/Codex-style relay — would mean adding new autonomous
capability inside FeralEcho itself, which under this project's own
standing rule requires its own Liveness Ledger check and real safety
review (see CLAUDE.md's Liveness Ledger section: "any new autonomous
capability... does not get to be called done without its own check added
here"). That's a real, separate, heavier decision — not something this
hub defaults into.

**So there is currently no direct Echo<->Codex channel, in either
direction, on either machine, and this hub does not create one.** The
practical way an Echo<->Codex exchange happens today is: whichever Claude
session is closest to both ends acts as a manual bridge — reads Codex's
side via `codex_relay`, calls Echo directly via `/chat/stream`, and
relays the result back. That's a documented *operating pattern*, not
automated code, precisely because automating message injection into
Echo's own conversation stream is a more consequential decision than a
status ledger, and hasn't been asked for or approved.

## Schema (`hub/status.jsonl`)

One JSON object per line, append-only, never rewritten:

```json
{"timestamp": "2026-09-15T20:00:00+00:00", "checked_by": "claude-m5", "channel": "codex_relay", "endpoints": ["codex-m5", "codex-air"], "status": "alive", "evidence": "peer reachable; local inbox 391 chars, 0 unread"}
```

`status` is one of: `alive` (endpoint reachable / local file present and
consistent), `unreachable` (network/connection failure), `unknown`
(check itself errored — script bug, missing dependency, etc.), `not_set_up`
(the channel's own local side was never configured, e.g. no secret file).

`evidence` is a short, structural summary only — **never** raw message
content, never a secret value, matching `claude_relay/relay.py`'s own
existing privacy rule ("deliberately never prints the actual content of
either file, even when checking on it"). Applied the same way to every
channel checked here.

## Running it

```bash
python3 hub/check_hub.py
```

Read-only against every channel except appending one line per channel to
`hub/status.jsonl` itself. Safe to run from any session, any time, as
often as wanted — each run is independent, nothing is mutated on any
remote side. No secret is required to *check* any of these channels
(only to *send* through codex_relay), and the script never reads a secret
file's contents into memory for display — only to determine whether it
exists.

## Reading the current state

```bash
tail -n 20 hub/status.jsonl | python3 -m json.tool --json-lines 2>/dev/null || tail -n 20 hub/status.jsonl
```

or just `tail -n <N>` it directly — it's plain JSONL, one line per check,
newest at the bottom.
