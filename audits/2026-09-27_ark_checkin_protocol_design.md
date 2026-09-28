# Ark Check-In Protocol — Design Only, Not Yet Executed

## CORRECTION (same day, after actually making contact) — the central premise of this document was wrong

**This entire document was designed against a false premise: that "Ark"
names a third, physically separate machine, distinct from "Air."** That
belief was never this document's own finding — it was inherited from an
earlier M5 session's 2026-07-07 briefing, and the Sept-20 cross-backup
plan this document itself cites (§1) already labeled it explicitly as
**"the M5's unverified... belief"** at the time it was written. This
document should have treated an already-flagged-unverified belief with
more suspicion before building a whole protocol on top of it; it didn't,
and that's a real process lapse worth naming plainly, not glossing over.

**What Air's own session confirmed directly, first-person, about its own
machine, the same day this document was written**: Air's Tailscale IP is
`100.82.172.4` — the exact IP already used for "Air" throughout this
entire session's `claude_relay`/`codex_relay` work, not a distinct
address. `sysctl hw.model` there reads `MacBookAir9,1`, a 2020 Intel
MacBook Air — matching the hardware this document expected for "Ark."
`ECHO_ARK_MODE=1` is set directly in `start_echo_ark.sh`, the exact script
that launched Air's own currently-running `run.py` (PID 72767). **"Ark" is
the name of a deployment mode running on Air's own box, not a separate
machine identity.** A follow-up question is pending (asked via the relay,
same session) about whether a genuinely separate second FeralEcho
lineage/directory exists on that same physical machine (per Air's own
2026-09-21 message describing an "Intel-lineage vault preservation" with
a distinctly smaller data scale) — that is the one part of this correction
not yet fully resolved.

**Practical consequence**: Sections 3-9 below, and the `relay.py --peer
intel` code extension built from them, describe infrastructure for
reaching a machine that, as far as this correction can currently
establish, does not exist as a separate entity — M5 has already been
checking in with "Ark" all session, under the name "Air." This document is
kept in place, uncorrected in its body, specifically so the mistake and
its correction both remain visible — matching this whole project's own
standing discipline of recording an error plainly rather than quietly
editing it away. Do not treat Sections 3-9 as a live design for a
not-yet-reached machine without first re-reading this correction.

---

**Scope, stated up front so this doesn't get confused with the existing,
much heavier document it builds on**: this is a design for a lightweight,
ongoing **check-in / conversation channel** with whatever Claude Code
session runs on the 2020 Intel MacBook ("Ark"), mirroring the
already-proven `claude_relay/` mailbox that works well for M5↔Air today.
It is explicitly **not** the cross-backup/data-transfer protocol already
designed in `audits/2026-09-20_feralecho_m5_intel_cross_backup_relay_plan.md`
(913 lines, SSH+tar streaming, sealed generations, manifest verification)
— that document solves a different, much higher-stakes problem (moving
real file bytes between machines) and remains its own, separately
authorized track. This design reuses two of its proven ideas (machine
identity pinning, credential-safety linting) without reusing its transfer
machinery, since check-in traffic is text, not files.

**Nothing has been executed.** No contact with Ark has been attempted. No
file has been created outside this repository. This document and its
review are the only outputs of this pass.

## 1. What's already known, and the one real gap

Confirmed by reading the existing Sept-20 plan (§0.3, §2, §4) rather than
assumed:
- Ark is referred to as `CLAUDE-INTEL` / lineage label `INTEL`; believed
  (unverified, dated 2026-07-07) to be an `i7-1060NG7`, 16 GB RAM,
  `x86_64`, running with an `ECHO_ARK_MODE` variant, no `data/` FAISS
  index, its own `ForensicAudit 2020 Macbook/` directory.
- As of 2026-09-20: **"Intel was not contacted and its discovery has not
  begun."** Nothing in this repository dated after that confirms contact
  has happened since (checked directly — no file newer than that plan
  mentions Intel/Ark).
- **No Tailscale IP or hostname for Ark is recorded anywhere in this
  repository** — checked directly, not assumed. The Sept-20 plan is
  explicit that peer IPs must always be "typed by the operator from the
  peer's own Tailscale app... never discovered by scanning."

**The one real gap this design cannot close on its own**: I have no way to
confirm whether a live Claude Code session is currently open on Ark, or
whether Ark's own FeralEcho `run.py` is even running and Tailscale-
reachable right now. Every design below accounts for this by starting from
an operator-mediated bootstrap, the same way the M5↔Air channel actually
started (per `claude_relay/README.md`'s own account: "No push, no
notification — each side had to be told (by the human) to check the
other's file").

## 2. Design principle: reuse the proven mailbox shape, not the heavy transfer machinery

`claude_relay/`'s M5↔Air pattern has run for months without incident:
plain append-only markdown files, a length-based read cursor (robust to
append-only growth, no fragile whole-file hashing), a `relay.py` CLI
(`status` / `read` / `append` / `flagged` / `fact` / `facts` /
`facts-read`), and a `needs-human` flag for anything that must surface
regardless of the channel's normal privacy default. This is the right
shape for check-in traffic — status, findings, questions — and there is no
reason to design something new when this already works and is already
trusted.

**What does need to be new**: a third party changes two things the
two-party design took for granted. `relay.py`'s current cursor files
(`.last_seen_from_air.json`) and hardcoded `from_air.md`/`from_m5.md`
filenames assume exactly two sides. And Ark is a genuinely less-verified
machine than Air (no prior established identity binding, unknown current
FileVault/`.env`-mode posture) — the Sept-20 plan's own §9.5 flags
FileVault as a real, checked concern for Intel specifically, unlike Air,
which this project already has months of history with.

## 3. Proposed structure

```
claude_relay/
  from_air.md          (existing, unchanged)
  from_m5.md           (existing, unchanged — Ark entries never mixed in)
  from_intel.md         (NEW — written only by Ark's Claude session)
  .last_seen_from_air.json   (existing, unchanged)
  .last_seen_from_intel.json (NEW — M5's read cursor into from_intel.md)
  facts_intel.jsonl      (NEW, optional — same structured-fact ledger
                           pattern as facts_m5.jsonl/facts_air.jsonl, only
                           if Ark check-ins produce checkable claims worth
                           grepping later)
```

Kept as a **separate file pair from Air's**, not a shared three-way file,
for the same reason the facts ledger was kept separate from the prose
mailbox: mixing two independent peers into one file makes "what's new
since I last checked" ambiguous the moment both peers write around the
same time, and it's a needless one-line risk for zero benefit — a fourth
file costs nothing.

`relay.py` would gain a `--peer` selector (default `air`, for full
backward compatibility with every existing invocation and cursor file) so
`status`/`read`/`append` can target either peer without duplicating the
tool. This mirrors the same additive-extension discipline this whole
project uses everywhere else (new parameter, old behavior unchanged when
omitted) rather than a parallel `relay_intel.py` script.

## 4. Machine identity, reused from the Sept-20 plan rather than re-derived

Before trusting anything in `from_intel.md` as genuinely coming from Ark
(as opposed to, say, a misconfigured session pointed at the wrong
machine, or the file being edited by mistake), the first real exchange
should pin identity the same way the Sept-20 plan's §4 already specifies:
`MACHINE_ID16` / `HW_ID16` (salted hardware hashes, never the raw UUID),
`ARCH_TRUE` (from `hw.optional.arm64`, not `uname -m`, which lies under
Rosetta), and the existing `STATE_LAYOUT_FP_V1` if Ark runs a comparable
FeralEcho layout. **Pinned on first contact, checked on every later
message** — exactly the Sept-20 plan's own rule ("any later message with a
different value is rejected"), reused verbatim rather than re-derived,
since it already solved this exact problem once and there is no reason to
solve it differently for a lighter-weight channel.

This is a real, if modest, cost for a check-in channel (a short identity
block on the first message), justified because hostname is confirmed
useless for this project specifically — the Sept-20 plan already found the
M5's own `LocalHostName` is literally `Richards-MacBook-Air`, and flagged
that "the Intel Air may be the same" as a real ambiguity risk.

## 5. Credential-safety linting, reused from `fe_relay.sh`

Even a "just checking in" message can accidentally carry a secret-shaped
string (a pasted `.env` line, a token in an error message). The Sept-20
plan's `fe_relay.sh` already built and tested exactly this defense (§9: 8
hostile-string test cases, all rejected; token shapes, PEM blocks, dotenv
grammar, long hex/opaque runs, secret-named fields, over-length lines) —
this design proposes reusing that same lint, applied to `append()` calls
on the new `from_intel.md` path specifically (Ark's `.env`/secret posture
is explicitly less verified than Air's per §9.5), rather than the plain,
unlinted `append()` the existing Air channel uses today. This is a real,
deliberate asymmetry: Air has months of established trust behind it; Ark
does not yet, so the newer channel gets the stricter default until it
earns the same track record.

## 6. Bootstrap sequence (what actually has to happen, in order)

1. **Operator confirms Ark is reachable at all** — is the machine powered
   on, on the Tailscale network, and is a Claude Code session currently
   open there (or does the operator need to open one)? This cannot be
   determined from M5 alone; no IP is known here, and per the Sept-20
   plan's own stated discipline, none should be discovered by scanning —
   it has to come from the operator, from Ark's own Tailscale app, the
   same way Air's connection was originally established.
2. **First contact, operator-relayed** (matching how M5↔Air actually
   started, before autonomous polling existed): M5's session writes a
   short identity + purpose message into a new `claude_relay/from_m5.md`
   entry addressed to Ark (or a dedicated first-contact file, to avoid
   mixing an unestablished third party into Air's own history); the
   operator carries it to Ark's session; Ark's session replies with its
   own identity fields into a newly-created `from_intel.md`.
3. **Identity pinning** (§4) happens on this first exchange, not
   deferred — a channel that starts without pinning identity has no clean
   way to add it retroactively without treating every prior message as
   provisional.
4. **Ongoing check-ins** proceed via the mailbox once both `from_intel.md`
   and the M5-side cursor exist, using the same `status`/`read`/`append`
   shape already proven with Air — HTTP-based (`GET /projects/file?...`
   over Tailscale, mirroring Air's own transport) if Ark's FeralEcho
   server turns out to be reachable that way, or purely operator-relayed
   if it isn't. Either transport is compatible with the same file format
   and cursor logic; only the *fetch* step differs.

## 7. Content boundary — explicitly narrower than the cross-backup plan

This channel is for exactly what the M5↔Air one has been used for today:
status, real findings, cross-checkable claims, disagreement, convergent
evidence (the kind Air's own reply just provided — see the research report
addendum). It is **not** a file-transfer channel, **not** a channel for
running commands on the operator's behalf on either machine, and **not**
a substitute for the existing, much more carefully gated cross-backup
plan if Ark's actual FeralEcho state is ever meant to be preserved or
restored — that stays its own, separately authorized track with its own
manifest verification and human-typed authorization phrase, unchanged by
this design.

## 8. What this design does not resolve, stated plainly

- Ark's actual current reachability, IP, and whether a live session exists
  there right now — genuinely unknown from this machine, and the right
  next step is asking the operator directly, not guessing or scanning.
- Whether Ark's fork is even close enough in shape to M5's for
  `relay.py`'s HTTP-fetch transport to work the same way it does for Air
  (Air's fork is known to be close enough; Ark's — per the Sept-20 plan's
  own explicit caution, §5.4 point 5 — "may differ... no assumption of
  `data/` FAISS, different filenames, `ARK_MODE` variants" — is not yet
  established either way).
- Whether Ark is even worth checking in with for *this specific* research
  question (autonomous learning) versus general project continuity — Air
  turned out to have real, convergent, independently-found evidence
  worth having; Ark might or might not, and that's only discoverable by
  actually making contact, not assumed in advance.

## 9. Recommendation

Build the small, additive `relay.py --peer intel` extension and the two
new files now (cheap, safe, reversible, doesn't touch Air's existing
channel) — but the actual bootstrap message can't be sent until the
operator confirms Ark is reachable and a Claude Code session is either
already open there or can be opened. That single piece of information is
the only real blocker on turning this design into a working channel.
