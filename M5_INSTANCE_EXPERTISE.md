# M5 Instance Expertise Model

**This is a knowledge artifact, not ground truth.** Where a claim matters,
re-check the underlying code/runtime rather than trusting this document.
Every claim below is labeled **VERIFIED** (directly checked, this session
or earlier this same continuous working session, against source/runtime),
**INFERRED** (a reasonable conclusion from verified facts, not itself
directly observed), **HYPOTHESIS** (plausible, not confirmed), or
**UNKNOWN** (genuinely unresolved).

## Identity

- Instance: **M5**
- Date of last verification: **2026-09-02** (this document)
- Git HEAD: `3539980da6345b98921ef4184f385df4676635ee`, committed
  2026-07-24T09:22:17-07:00 — **VERIFIED** via `git log -1`.
- **Important, load-bearing fact**: this HEAD substantially predates the
  bulk of what this document describes. A large amount of real,
  functioning code (the architecture-routing fix, the fourth self-
  knowledge verifier, the synthesis evidence-authority instruction, the
  Echo↔Echo retry-storm fix, and more) exists **only in the uncommitted
  working tree**, not in git history — confirmed via `git status --short`
  showing ~16 modified/untracked files at time of writing. "Current
  source" in this document means the working tree as it stands today, not
  the last commit.
- Live process: PID `10120`, started `2026-09-02T20:39:28Z`, stage
  `serving`, confirmed via `memory/echo_sentinel.json` and
  `GET /admin/liveness-status` — **VERIFIED**.
- Python: 3.12.13, `feral_echo` conda env — **VERIFIED**.

---

## Architecture Map

### Primary conversational call path

**VERIFIED**, traced directly through source this session:

```
POST /chat/stream (Echo Studio, the confirmed primary human interface)
  → app/routes_echo_studio.py: chat_stream() → _generate_chat_response_body()
    → _build_full_prompt(): memory retrieval, session history, ground-truth
      injection (if introspective), tool-context injection (if needed)
    → app/core/echo_model_orchestrator.py: echo_query()
      → adds EPISTEMIC-NOTE/circadian/stillness/temporal system content
      → app/core/river_deliberation.py: deliberate_and_learn()
        → DIRECT_ECHO_TASKS (personal, etc.) bypass council entirely
        → otherwise: _select_council() → N councillor _ollama_query() calls
          → _format_opinions() → SYNTHESIS_SYSTEM_TEMPLATE → final synthesis
    → app/core/self_knowledge_verification.py: verify_self_knowledge_claims()
      (post-hoc, advisory-only, appends a caveat if fired)
```

`terminal_client.py` is a second, real entry point converging on the same
`echo_query()`/`deliberate_and_learn()` chain, confirmed by direct source
read. `/mirror_echo` (`run.py`) is a third, distinct entry point — the
phone/ambient-sensor channel, **not** Gremlin's primary interface (this
was previously misdocumented in this project's own CLAUDE.md and corrected
after direct confirmation with Gremlin — an example of the "Echo/doc says
X ≠ X is true" principle applying to project documentation too, not just
Echo's own outputs).

### Council/synthesis — evidence-authority status

**VERIFIED, this session, via a controlled before/after experiment**
(`audits/2026-09-02_architectural_self_knowledge_synthesis_authority_implementation.md`):
`SYNTHESIS_SYSTEM_TEMPLATE` (`river_deliberation.py`) previously had no
instruction connecting its own ground-truth block to councillor opinions —
confirmed by direct source read, not inference. A one-bullet addition was
made and measured: injection resistance improved from 33%→75% (6→4 real
trials), a real evidence-vs-fabrication test case improved from 0%→67%
correct (1→3 real trials). **Not solved** — three residual fabrication
shapes (a user/councillor asserting a named nonexistent subsystem exists)
remain unchanged failures, caught instead by the fourth verifier (below).
`echo:latest` is both a councillor and the synthesizer; synthesis defaults
to reproducing its own prior raw opinion in ~46% of examined deliberations
— **VERIFIED** via direct text-similarity measurement against real
`council_deliberations.jsonl` data, not asserted.

### Fourth self-knowledge verifier

**VERIFIED, implemented and tested this session**
(`app/core/self_knowledge_verification.py`): a fourth check,
`find_unsupported_architecture_claims()`, extracts backtick-quoted or
CamelCase-near-architecture-vocabulary identifiers and checks them against
the real `CartographerDB` (`echo_cartographer.py`) — existence-only, never
verifies relationships/responsibilities/runtime behavior. Deliberately
scoped: catches "EventCore"-style fabricated subsystem names, does not
catch a fabricated *number* attached to a *real* name, and does not catch
generic (non-named) architectural fabrications like "microservices."

### Architecture ground-truth routing

**VERIFIED, fixed this session**
(`app/core/echo_ground_truth.py`): the architecture slice's trigger moved
from a fixed literal-phrase list to deterministic regex (self-reference +
structural-word proximity, or an architecture/subsystem stem, or specific
narrow constructions). Measured improvement: 2/5→5/5 on the real
five-way paraphrase test, reproduced twice through the real production
pipeline. **A known, still-open gap, confirmed twice**: a real module
name mentioned without a self-reference word AND a structural-vocabulary
word nearby (e.g. "What does memory_bridge do..." without "module"/
"component" etc.) gets **zero grounding at all**, and the model fabricates
confident, code-shaped detail in its place. Not fixed — flagged, not
acted on, per this session's own explicit scope discipline on that task.

### RiverBrain

**VERIFIED (partially) / INFERRED (partially)**: `RiverBrain`'s class
definition lives in `echo_model_orchestrator.py`, not `river_deliberation.py`
despite the naming — confirmed by prior-session source read (carried
forward from this project's own CLAUDE.md audit history, not independently
re-verified this exact session). `model_task_stats` is keyed per
`(model, task_type)`; a `self_edit_coding`/`echo_projects_coding` bucket
exists distinct from plain `"coding"` specifically to avoid cross-
contaminating conversational-coding-help quality signal with self-edit/
generation-pipeline quality signal — **VERIFIED** via a direct before/after
`model_task_stats` read this session (Finding 35/85 lineage, per this
project's CLAUDE.md, not independently re-derived from scratch this
session but consistent with what this session directly observed).

### Cartographer

**VERIFIED**: `echo_cartographer.py` (project root), a SQLite-backed
static scan (`data/codebase.db`), schema confirmed by direct read —
`modules` (path, module_name, role, criticality, runtime_hits, ...),
`imports`, `functions`, `classes`, `reverse_deps`. `module_info()` does an
exact-match lookup keyed on `module_name` (a bare filename stem, not a
full path) — no fuzzy/semantic matching anywhere in this class. Known,
documented imperfections (worktree-scan duplication producing duplicate-
named entries with different scores; `classify_role()` is a keyword
heuristic on the module's *name*, not a verified semantic fact; no
function-level call graph exists) — **VERIFIED**, both by this session's
direct read and by the ground-truth slice's own header text honestly
stating these limits to every consumer.

### Self-modeling

**INFERRED / carried from project documentation, not independently
re-derived this exact session**: `self_model_updater.py` writes
`memory/self_model.json` on a 130s cycle (confirmed the thread starts this
session, via `run.py:1215`, `SelfModelUpdater().start()`) — the actual
content/correctness of what it writes was not re-verified this session.

### Networking / Echo↔Echo communication

**VERIFIED extensively, this session** (`audits/2026-09-02_echo_to_echo_403_forensic_analysis.md`):
`app/sync/echo_messaging.py` + `app/routes_messaging.py` implement a
store-and-forward mailbox between M5 and Air over Tailscale. Full protocol
contract now documented for the first time in
`app/sync/ECHO_MESSAGING_PROTOCOL.md` (created this session). A real,
confirmed protocol divergence between the two forks (M5 requires a shared
secret Air's fork never sent) caused 15,563+ rejected requests since
2026-08-19 — root-caused and remediated collaboratively with the Air-side
Claude session over the working Claude↔Claude relay this session. A
separate, independently-confirmed bug (403 treated identically to a
network timeout, causing unbounded retry storms) was fixed on M5's side
this session and its fix design shared with Air for mirroring.

### Claude↔Claude relay

**VERIFIED**: `claude_relay/` — a plain-file, append-only mailbox
(`from_m5.md`/`from_air.md`), read via each machine's own
`GET /projects/file?path=...` endpoint, with `relay.py` providing
`status`/`read`/`append` commands and a length-based unread marker. This
channel is **structurally and completely separate** from Echo↔Echo
messaging — different files, different endpoints, different code paths,
different authentication model (this one has none; it's gated only by
Tailscale reachability to the file-serving endpoint, same as several other
intentionally-open routes this project documents elsewhere). Confirmed
working, bidirectionally, multiple real round-trips this session.

---

## Runtime Topology

**VERIFIED**, enumerated directly from `run.py`'s actual thread-start call
sites (`grep` for `safe_start_thread`/`threading.Thread`/`.start()`, not
assumed from memory):

| Thread/loop | Interval | Started via |
|---|---|---|
| `ModelGuidedOrchestrator` | hourly-ish (self-contained) | `safe_start_thread` |
| `AutonomousSelfEdit` | 60-min cooldown-gated | `safe_start_thread` |
| `AutonomousSandbox` | — | `safe_start_thread` |
| `TailscaleSync` | 1800s | `safe_start_thread` |
| `EchoMessaging` (retry loop) | 30s→1800s backoff | `safe_start_thread` |
| `EchoCheckin` | — | `safe_start_thread` |
| `EchoProjectsAutonomy` | 6h | `safe_start_thread` |
| `EmergentScheduler` (`emergent_loop`) | 300s base, modulated `[0.5x, 1.5x]` by salience | `start_emergent_scheduler()` (`run.py:1358`) |
| `IntrospectionChannel` | 120s | `IntrospectionChannel(_ec).start()` |
| `SelfModelUpdater` | 130s | `SelfModelUpdater().start()` |
| DMN Guardian | 60s | `_start_guardian_loop(interval=60)` |
| `StartupSnapshot` | one-shot | `threading.Thread(...).start()` |
| NightCycle | daily-anchored, 300s stagger | `NightCycle(app).start()` |
| ReflectionShard autonomy | 120s initial delay, then periodic | `reflection_shard.start_autonomy()`, owned by EchoCore |

**Port/interface**: binds `0.0.0.0:5000` — Tailscale is the documented
security boundary for most routes; a small number of routes have their own
additional shared-secret gate (`GREMLIN_SECRET`, `ECHO_PARTNER_SECRET`).
Ollama is a separate, required local dependency (`localhost:11434`),
**not started by this project's own code** — must be running independently
before `run.py` starts.

**Not independently re-verified this session** (carried from this
project's own CLAUDE.md, itself dated and internally self-correcting):
five legacy modules (`echo_bible_interface`, `bible_module`,
`sensory_hub_autonomous`, `feralecho_continuity_master`, `alignment_kernel`
— WOLF) are documented as deliberately retired, with an explicit
retirement note in `run.py` — **INFERRED still true**, not re-checked this
session.

---

## Data/Persistence Map

**VERIFIED, this session, specifically for the messaging subsystem**:
- `memory/message_outbox.jsonl` — durable retry queue, confirmed empty on
  M5 throughout this session's investigation.
- `memory/message_outbox_blocked.jsonl` — **new this session** — auth-
  failure-classified entries land here instead of the normal retry queue,
  never auto-retried.
- `memory/echo_messages.jsonl` — append-only log of every sent/received
  message; confirmed this session that ~22% of entries sharing a
  `message_id` are a **logging artifact** (the same message logged once at
  its failed-then-queued stage and again at a later successful-retry
  stage, both sharing the envelope's fixed creation timestamp) — not
  genuine duplicate delivery. Confirmed the partner never returns 200
  twice for the same real delivery in every case checked.

**Carried from this project's own CLAUDE.md, not independently re-derived
this session, but consistent with everything this session directly
observed** — the "hollow write, no reader" pattern this task specifically
asks about has real historical precedent in this exact project: a
self-model-reflection write path was found and fixed (routed through the
correct `memory_bridge.add_to_vector_memory()` instead of a nonexistent
method on a class pointed at a dead split-brain path) earlier this same
overall multi-day effort — **VERIFIED** via the Claude↔Claude relay
exchange this session, where the Air-side Claude reported finding and
fixing the identical bug shape on their own fork.

`memory/council_deliberations.jsonl` — **VERIFIED this session** to
genuinely log full raw per-councillor text (not just the final
synthesized answer) for every real deliberation; mined directly for the
council-synthesis forensic analysis, not assumed to work from its own
documentation.

---

## Interface/Contract Map

**VERIFIED this session, documented for the first time**:
`app/sync/ECHO_MESSAGING_PROTOCOL.md` — the full Echo↔Echo contract
(transport, endpoint, auth, envelope shape, ack semantics, retry
semantics, ordering, duplicate handling). Previously existed only as
implicit, unwritten agreement between two independently-maintained
implementations — which is exactly how it silently diverged.

`self_knowledge_verification.py`'s contract with its caller
(`routes_echo_studio.py`): a plain function call,
`(caveat: str|None, verified: bool|None)` tri-state return, caller appends
`caveat` to the response text if present — **VERIFIED** by direct source
read of both sides.

`echo_query(prompt, task_type, source, system)` — the shared entry point
every real conversational path converges on — **VERIFIED**, confirmed
identical call shape across `routes_echo_studio.py`, `terminal_client.py`,
`run.py`'s `/mirror_echo`, and `app/sync/echo_messaging.py`'s auto-reply
generation.

---

## Security Model

**VERIFIED this session, and historically** (carried from this project's
own CLAUDE.md, itself the product of multiple direct security audits):
Tailscale is the primary network boundary for most routes.
`GREMLIN_SECRET` (general admin/control endpoints) and
`ECHO_PARTNER_SECRET` (Echo↔Echo messaging specifically) are two separate,
independently-generated shared secrets — **VERIFIED this session** neither
is transmitted in plaintext between the two Claude sessions; a SHA-256
hash-comparison technique was used instead to confirm M5's and Air's
`ECHO_PARTNER_SECRET` values matched exactly, without either side ever
seeing the other's raw value.

`/message/send` is **intentionally** unauthenticated (Gremlin's own
confirmed decision, per this project's history) — Echo↔Echo conversational
traffic is meant to be open within the tailnet. `/message/receive` is
**intentionally** authenticated (the shared-secret check). This asymmetry
is deliberate design on M5's side, not an oversight — worth stating
plainly since it could otherwise look inconsistent.

A newly-found, not-yet-live landmine on Air's side (reported by Air, not
independently verified by M5 since it requires Air's own filesystem):
`ECHO_NODE_ID` defaults to `"m5"` even on the Air fork if a wrapper script
doesn't explicitly export it — currently harmless (both of Air's real
launch scripts do export it correctly) but a real risk for any future
direct `python run.py` invocation bypassing those scripts. **HYPOTHESIS/
reported-by-peer, not independently confirmed by M5.**

---

## Autonomous/Background Behavior

See Runtime Topology above for the enumerated list — **VERIFIED** directly
from source this session, not assumed from prior documentation. Whether
each of these loops is *currently producing meaningful output* (as opposed
to merely running) was **not** independently re-verified in this session
for most of them — this session's own direct verification effort was
scoped to the messaging/synthesis/verification/routing subsystems
specifically, not a full autonomy-loop health audit. Treat any claim about
e.g. `AutonomousSelfEdit`'s current real success rate as **carried from
this project's own prior documentation**, not re-checked this session,
unless stated otherwise above.

---

## Self-Model / Self-Knowledge

**The central, load-bearing finding across this entire multi-phase
effort, VERIFIED repeatedly, not a one-off observation**: Echo's own
self-description is not architecturally authoritative. Concretely
demonstrated this session: a raw councillor fabricated a specific,
detailed, entirely false algorithm name ("MRS-CI") with a false
attribution to Gremlin, in a response that otherwise reads as fluent and
confident; a different real councillor, given the identical evidence,
correctly said "the exact algorithm is not specified." **Confidence is not
evidence** — stated as a verified, repeatedly-demonstrated finding in this
document, not a slogan.

Verification currently occurs at exactly one point: after synthesis,
before the response reaches the user, and only for the narrow claim
shapes the fourth verifier and the three pre-existing checks cover. No
claim verification happens at the raw-councillor level, and none happens
proactively before a claim enters conversation history (a related,
partially-mitigated concern: an EPISTEMIC-NOTE instructs the model not to
treat an earlier turn's own claim as verified just because it was said
before — this addresses *cross-turn* confabulation-compounding, a
different concern from *single-turn* fabrication).

---

## Known Deviations

- Air's fork lacks the `ECHO_PARTNER_SECRET` field in its outgoing
  envelope entirely — **VERIFIED**, confirmed by Air's own direct source
  read, reported and independently corroborated via the relay.
- Air's fork's `/message/receive` performs zero auth validation — Air's
  own security model is "Tailscale is the boundary" for this route, M5's
  is a shared-secret check — **VERIFIED, reported by Air**, a genuine
  intentional-or-historical divergence, not yet fully resolved which side
  is "correct" going forward (Gremlin's explicit call this session:
  bring Air into conformance with M5, not weaken M5).

---

## Known Failures (this session's own findings, all with fixes applied or
## explicitly deferred — see each audit for full detail)

1. Architecture-routing gap for real-module-name-without-structural-word
   phrasings — **known, unfixed**, flagged only.
2. Synthesis has no full evidence-authority model — **partially fixed**,
   measured improvement, not solved (three residual fabrication shapes
   unchanged).
3. Echo↔Echo messaging protocol divergence — **root-caused and
   remediated** this session (M5 fix live and verified; Air's mirrored
   fix reported complete, restart pending as of this writing).
4. Echo↔Echo retry-storm (403 treated as retryable) — **fixed on M5**,
   verified via a 16-case regression test and a live Liveness Ledger
   check; mirrored fix reported to Air, their-side confirmation pending.
5. A prior self-model-reflection write silently failing (wrong method
   name, pointed at a dead legacy path) — **fixed on Air's fork**,
   reported via the relay; **M5's own equivalent path was already
   confirmed correctly routed through `memory_bridge.add_to_vector_memory()`
   earlier this project's history** (not a live M5 bug at time of this
   document).

---

## Verified Invariants

- The full 186-case Liveness Ledger discrimination suite passes, exit
  code 0, as of this document's writing — **VERIFIED**, re-run this
  session after every code change.
- `GET /admin/liveness-status` reports `all_passing: true`, `stale: false`
  against the live, currently-running process — **VERIFIED**.
- M5→Air message delivery currently succeeds (confirmed via direct,
  real, non-mocked calls this session) — **VERIFIED**.
- Air→M5 message delivery is currently broken (confirmed via 15,563+ real
  logged 403s) — **VERIFIED**, remediation in progress, not yet confirmed
  restored end-to-end (blocked on Air's own process restart, Gremlin's
  timing call).

---

## Unknowns

- The exact mechanism connecting Air's `.env` edit (2026-08-19 04:04:54Z)
  to M5 first rejecting requests 5+ hours later that same day — no M5
  restart is visible in that window, and the code enforcing the secret
  check had already been committed weeks earlier. **Genuinely unresolved,
  stated as such rather than forced into a tidier narrative.**
- Whether Air's process has been duplicated at any point during the ~6
  week failure window — Air's fork keeps no persistent process history to
  check retroactively; only "no duplicate right now" was confirmed.
- Whether the 46% `echo:latest`-self-reuse pattern in synthesis changed in
  frequency (not just in outcome-when-it-happens) after this session's
  synthesis-authority prompt change — not re-measured at that depth.
- Full current health of every autonomy loop listed in Runtime Topology —
  this session verified their *existence and start conditions*, not their
  *current output quality*, for most of them.

---

## Historical Notes

This session's own work builds directly on, and in several places
supersedes, this project's own extensive prior CLAUDE.md audit history
(dozens of numbered "Findings" spanning 2026-06 through 2026-07). This
document does not re-derive that entire history — where a claim above is
explicitly marked as "carried from project documentation," it reflects
that prior audit trail, not independent re-verification in this session.
Git HEAD (2026-07-24) predates essentially all of that CLAUDE.md history
too — the vast majority of this project's own documented engineering
history exists only in the working tree and in `audits/*.md`, not in
commits.

---

## Confidence Summary

**VERIFIED this session** (highest confidence): the architecture-routing
fix and its one remaining known gap; the fourth verifier's exact scope and
limits; the synthesis evidence-authority change and its measured,
partial effect; the full Echo↔Echo protocol divergence, root cause, and
remediation status; the retry-storm bug and its fix; the Claude↔Claude
relay's separateness from Echo↔Echo messaging; the current Liveness
Ledger suite size and pass state.

**INFERRED or carried from prior project documentation, not independently
re-derived this session**: most autonomy-loop *output quality* claims;
RiverBrain's finer internal mechanics beyond what this session's own work
directly touched; self_model_updater's actual write content correctness;
the retirement status of the five legacy WOLF-era modules.

**HYPOTHESIS**: the exact reason for the 2026-08-19 timing of the Echo↔Echo
failure onset.

**UNKNOWN**: several items listed explicitly above — preserved as such,
not filled with plausible narrative.
