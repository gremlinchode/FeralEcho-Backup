# Durable Echo Studio Request Lifecycle — Feasibility Study

**Read-only architecture/feasibility study.** Nothing implemented, nothing added,
no source modified, no timeout changed, Echo not restarted. Nothing staged,
committed, or pushed.

---

## 1. Executive Verdict

# BUILD DURABLE REQUEST LIFECYCLE

**Implementation family: A — EXTEND EXISTING INFRASTRUCTURE.**

The demonstrated retry-duplication risk (Section 2) is real, not hypothetical,
and this project's own established values (clean, uncontaminated training
signal — the entire Finding 3 cross-contamination history) make it worth closing
properly rather than papering over with a heartbeat. But FeralEcho already has
roughly 70% of what's needed: a real per-request identity (`trace_id`), a proven
pending→evaluated status-ledger pattern (`self_edit_outcome_tracker.py`), and a
proven atomic claim-lock pattern (`claim_fetch_cycle()`). The smallest safe
design is a thin, additive layer over the existing `threaded=True` Flask model —
not a background-job queue, not a new worker process, not a message broker.

---

## 2. Verified Current Failure Mode

Re-verified in source this session, independent of the prior report's own
narration — all nine load-bearing claims hold:

1. **Studio's read timeout is 300s** — confirmed live: `echo_studio/api_client.py:89`,
   `timeout=(self.timeout, 300)`.
2. **`echo_query()` is one blocking call** — confirmed: `app/routes_echo_studio.py:306-309`,
   `raw_response = echo_query(...)`, no `yield` inside it.
3. **No meaningful bytes are yielded during that call** — confirmed: the only
   `yield` between the "status" frame (`:199-202`) and the response chunks
   (`:312-314`) is the `echo_query()` call itself, which produces no output.
4. **Server work can outlive client patience** — confirmed by Python's own
   generator/exception model (a non-suspended generator cannot be externally
   interrupted; re-verified this session, not merely cited from the prior report).
5. **Important persistence occurs before response delivery** — confirmed:
   `interaction_log.jsonl`/`council_deliberations.jsonl`/RiverBrain's in-memory
   update all happen inside `echo_query()`'s own synchronous return path
   (`app/core/river_deliberation.py:684,1183,1511`).
6. **Later persistence can occur after `echo_query()` and is at risk** —
   confirmed: `store_turn_in_history()`/`save_turn_to_server()` sit after the
   token-yielding loop (`:365-371`).
7. **Flask is threaded** — confirmed live: `run.py:1581`, `threaded=True`.
8. **Duplicate submission can create concurrent duplicate executions** —
   confirmed by the absence of any request-scoped guard anywhere in
   `chat_stream()`/`_generate_chat_response_body()`.
9. **No existing request-level idempotency/deduplication exists** — confirmed:
   `_SESSIONS` (`:39-49`) is keyed by `conversation_id`, not by
   message/request — it has no concept of "have I already started processing
   this specific submission." No other guard was found anywhere in this path.

**No discrepancy found. The prior report's architectural claims all hold.**

---

## 3. Existing Reusable Infrastructure

| Component | Existing purpose | Durable? | Unique identity? | Reusable here? | Risk |
|---|---|---:|---:|---:|---|
| `trace_id` (`uuid.uuid4()`, `routes_echo_studio.py:178`) | Joins `interaction_log.jsonl`/`council_deliberations.jsonl`/`retrieval_provenance.jsonl` entries for one real turn (Finding 92, this session) | Yes, in the logs it's written to | Yes, but **minted fresh on every HTTP POST**, never client-supplied | **Partially** — the identity concept is right; it needs to originate from the client to survive a retry, and needs to reach the client *early* (currently only appears in the final "done" frame, never seen if the client already timed out) | Low — purely additive change |
| `self_edit_outcome_tracker.py`'s `pending`→evaluated status field (`:72-235`) | Tracks self-edit outcome evaluation lifecycle, lock-guarded read-modify-writeback | Yes (JSONL file) | Per self-edit attempt | **Yes, as a direct structural template** for a request-status ledger | Low-medium — full-file rewrite per update doesn't scale to chat volume without its own retention cap (Section 9) |
| `claim_fetch_cycle()` (`app/internet_tools/autonomous_fetch.py:64`) | Atomic check-and-claim lock preventing two autonomous loops from double-running the same fetch cycle | In-memory only | Time-window-based, not identity-based | **Yes, as a pattern** — generalizes cleanly from "one global timestamp" to "one dict keyed by request_id" | Low |
| `_SESSIONS` dict (`routes_echo_studio.py:39`) | Per-conversation in-memory history + lock | No — explicitly documented as process-lifetime only | Per `conversation_id`, not per request | Partially — shows where request-scoped state could live (in-memory, same file), but is the wrong granularity on its own | Low |
| `interaction_log.jsonl` / `council_deliberations.jsonl` | Durable, append-only record of *completed* turns | Yes | Via `trace_id` | **Not as the ledger itself** — these are scientific/behavioral records other subsystems (RiverBrain, task-type classifier) already depend on; Phase 8 explicitly warns against overloading them with transport bookkeeping | Medium if reused directly — would mix concerns |
| Global Workspace (`echo_core.publish_salience()`) | Cross-subsystem event broadcast | Yes (`workspace_log.jsonl`) | Per event | No — wrong shape (broadcast, not a queryable per-request status record) | — |
| `crash_awareness.py`'s startup-time evidence scan (Finding 51/64) | Reconciles real crash evidence at process start | Yes | N/A | **Yes, as a pattern** for Phase 11's abandoned-`RUNNING`-entry reconciliation | Low |

**Conclusion: extend, don't invent.** Every piece needed already has a close,
proven analogue in this codebase.

---

## 4. Required Semantics

Four states are mechanically justified by what actually happens in this
pipeline; no more were added merely because they sound complete.

- **`RECEIVED`**: the server has accepted a complete `(request_id,
  conversation_id, message)` tuple and is about to begin work. Mechanically:
  written the instant `chat_stream()` validates the payload, before anything
  else runs.
- **`RUNNING`**: exactly one `echo_query()` (or fast-mode/dispatch equivalent)
  call is in progress for this `request_id`. Mechanically: the state that makes
  deduplication possible — checked-and-claimed atomically before starting work.
- **`COMPLETED`**: `echo_query()` returned successfully and the full response
  text is durably recorded in the ledger. Mechanically: written immediately
  after the blocking call returns, **before** any token is yielded over HTTP.
- **`FAILED`**: the generation call itself raised (the existing `except
  Exception` block at `:316-319` already detects this) — recorded instead of
  `COMPLETED`.

**Rejected as unnecessary distinctions, with reasons:**
- `QUEUED` — there is no queue in the recommended design (Section 12); every
  accepted request begins running immediately on its own thread, so `RECEIVED`
  and the transition to `RUNNING` are effectively simultaneous. Adding a
  distinct `QUEUED` state would describe a queue that doesn't exist.
- `PERSISTING` — the interaction-log/council/RiverBrain writes happen *inside*
  `echo_query()` itself, atomically with the work; there is no observable
  window where "the answer exists but isn't yet being persisted" worth
  surfacing as its own state.
- `DELIVERED` — genuinely useful conceptually (Section 5), but tracking it
  reliably would require the client to acknowledge receipt, which is a real,
  separate feature this study does not find justified by the demonstrated
  problem (Section 19).
- `CLIENT_DISCONNECTED` — the server frequently cannot know this reliably
  (Section 6 of the prior report), so making it a first-class ledger state
  would create a state that's often wrong; better to leave the client's own
  connection status as the client's concern and let the ledger only describe
  what the *server* actually did.

---

## 5. Atomicity Boundary

**The smallest defensible canonical boundary for "the interaction successfully
happened" is: `echo_query()` returned AND its full result was durably written
to the request ledger — not "response reached Studio," and not merely
"`echo_query()` started."**

This is deliberately smaller than "FAISS persistence completed" (already
best-effort/non-critical in the existing architecture — `save_turn_to_server()`
silently swallows its own failures) and bigger than "request received" (which
doesn't yet mean any work was done). It is chosen specifically because it is the
exact point where every subsystem this project already treats as
consequential — the real interaction log, the council record, RiverBrain's
adaptive statistics — has *already* run, synchronously, with nothing left to
lose if delivery fails afterward. Moving the ledger's `COMPLETED` write to this
same instant means "Echo did the work" and "the work is durably recorded"
become effectively one atomic event in practice, closing the split-brain gap
Phase 12 of the mission worries about.

---

## 6. Request Identity

- **Origin: client-generated, not server-generated.** This is the one place
  this study's design diverges from the *current* `trace_id`'s own behavior,
  and it matters precisely because of Phase 6's requirement: only the client
  knows whether a given `POST /chat/stream` is a retry of an earlier, uncertain
  attempt or a genuinely new message. A server that mints a fresh ID on every
  HTTP request — exactly what happens today — cannot make that distinction by
  construction, no matter how good the ID's own properties are.
- **Format**: a client-generated UUIDv4 is appropriate — no collision risk at
  this scale, no coordination needed, matches the existing `trace_id`'s own
  format exactly.
- **Backward compatibility**: the field is optional in the request payload.
  Absent → server mints one itself (today's exact behavior, unchanged) — a
  caller like `app/experiments/gen_epistemic/chat_helper.py` (a real,
  additional caller of this route, found this session — Section 17) that
  never sends one keeps working exactly as it does today, just without
  reconnect/dedup benefits.
- **Reuse of the existing `trace_id`**: yes — this is not a new, second
  identity concept. The client-supplied ID *becomes* the `trace_id` threaded
  through `interaction_log.jsonl`/`council_deliberations.jsonl` exactly as it
  is today; this design adds an origin option to an identity that already
  exists everywhere it needs to, rather than inventing a parallel one.
- **Maps to exactly one execution**: yes, by construction of the dedup check
  in Section 7 — the entire point of moving identity generation to the client.

---

## 7. Deduplication

Exact retry semantics, precisely as the mission's own Phase 6 framed them:

- **Existing request is `RUNNING`**: return the current status (e.g., an SSE
  `{"type": "status", "status": "already_running", "request_id": ...}` frame,
  or an HTTP 202) — **do not start a second `echo_query()` call.** Enforced via
  an atomic check-and-claim, generalizing `claim_fetch_cycle()`'s proven
  lock-guarded pattern from "one global timestamp" to "a lock-guarded
  in-memory `dict[request_id] -> status]`, checked and set in one critical
  section before any work begins.
- **Existing request is `COMPLETED`**: return the stored result immediately
  from the ledger — **do not recompute.** This is the direct fix for the prior
  report's central concern: a resend after a timeout becomes a cheap ledger
  read, not a second full council deliberation.
- **Existing request `FAILED`**: `echo_query()` has no checkpoint/resume
  concept — "resuming" isn't mechanically meaningful. The simplest, least
  surprising behavior: allow a fresh execution under the *same* request_id
  (the user's retry intent is honored, without inventing partial-resume
  machinery that doesn't map to anything real in this pipeline).
- **Same text, different request_id**: treated as a genuinely new,
  intentional interaction, exactly as the mission specifies — deduplication is
  keyed strictly on identity, never on message content, since two identical
  messages may be deliberate.

---

## 8. Disconnect Behavior

**Recommended policy: client disconnect does not cancel server-side
computation** — both because it matches the mission's own suggested default
and because it is, in practice, the *only* option available: Section 2's
already-re-verified finding is that Python's generator model gives the server
no reliable, safe way to interrupt an in-progress `echo_query()` call from
outside without forcibly killing a thread (something nothing in this codebase
does, and which risks corrupting whatever that thread was mid-write on).

**Tested against the mission's own risk list:**
- **Resource exhaustion / runaway model calls**: the real risk here isn't one
  abandoned client — it's *uncontrolled retries* multiplying real Ollama load,
  which is exactly what Section 7's dedup closes. A single walked-away request
  finishing on its own schedule is not, by itself, dangerous.
- **Abandoned requests / browser refresh / Studio restart**: addressed by
  Section 9's retention policy, not by cancellation.
- **Multiple simultaneous clients**: already handled today by
  `threaded=True`; unaffected by this design.
- **Malicious clients**: out of scope for a `127.0.0.1`-only tool today
  (Section 15), flagged for the future.

---

## 9. Result Durability

**A new, small, dedicated ledger — not a reuse of `interaction_log.jsonl` or
`council_deliberations.jsonl`.** Phase 8's own instruction is directly on
point here: keep transport state separate from Echo's memory and from her
learning state. Proposed shape (structurally identical to
`self_edit_outcome_tracker.py`'s own JSONL pattern, not a new format):

```json
{"request_id": "...", "conversation_id": "...", "status": "RECEIVED|RUNNING|COMPLETED|FAILED",
 "message_preview": "first ~120 chars", "created_at": "...", "updated_at": "...",
 "response_text": null, "task_type": null, "error": null}
```

- **Location**: a new file, e.g. `memory/echo_studio_requests.jsonl` — plain
  transport bookkeeping, never read by RiverBrain, the task-type classifier, or
  any training pathway.
- **Update mechanism**: the same lock-guarded read-modify-writeback shape
  `self_edit_outcome_tracker.py` already proves out — acceptable at self-edit's
  low (~daily) volume; Echo Studio's real volume (hundreds of turns/day, per
  this session's own earlier interaction_log.jsonl counts) means the file
  needs its **own retention cap from day one** (Section 15), not deferred as
  an afterthought the way some of this project's own history shows other logs
  going unbounded until found the hard way (CLAUDE.md Finding 41 D).
- **Retention**: a real number should be chosen deliberately, not invented
  here — but a bound in the same spirit as `log_retention.py`'s existing
  100MB caps or `_MAX_SELF_EDIT_PLANS`' file-count cap (prune `COMPLETED`/
  `FAILED` entries after some fixed age, e.g. 24h, long enough for any
  plausible reconnect) is the right *shape* of answer.

---

## 10. Persistence Ordering

Transport, memory, and learning state, kept explicitly distinct per Phase 8:

| Layer | What lives there | Ordering relative to `echo_query()` |
|---|---|---|
| **Transport** (new) | `request_id`, status, response text copy, timestamps | `RECEIVED` before; `RUNNING` immediately before the call; `COMPLETED`/`FAILED` immediately after, before any HTTP write |
| **Echo memory** | `interaction_log.jsonl`, `council_deliberations.jsonl`, `retrieval_provenance.jsonl`, Studio's own `conv_history`/FAISS | The first two happen *inside* `echo_query()`; the last two remain exactly where they are today, after the token-yield loop — this design does not move them, since they are not the split-brain risk (Section 5 already covers the risk by moving the *transport* ledger, not by touching Echo's own memory-write ordering) |
| **Learning state** | RiverBrain `model_task_stats` (in-memory update inside `echo_query()`; on-disk persistence on its own independent ~60s writer-thread schedule) | Unaffected by this design entirely |

**No existing split-brain state was found to require fixing beyond what
Section 5 already closes.** The specific example the mission raises ("RiverBrain
learned from interaction but response result vanished") is exactly the gap
this design closes — once the transport ledger's `COMPLETED` write happens at
the same instant, "RiverBrain learned but the answer is unrecoverable" becomes
architecturally impossible, since the answer is now durably captured at that
identical moment.

---

## 11. Architecture Alternatives

- **A — Minimal request ledger around existing threaded execution
  (recommended)**: extends what's already proven; smallest diff; no new
  processes, dependencies, or coordination primitives.
- **B — Background job abstraction** (a real worker-queue/broker model,
  `POST` returns immediately, work happens fully decoupled from any HTTP
  request thread): **rejected as over-scoped.** Nothing about the demonstrated
  problem requires decoupling computation from the request thread — the actual
  gaps are identity, a status record, and dedup, all of which Design A
  supplies without touching how or where `echo_query()` itself runs. A real
  job queue would add operational complexity (a broker or at minimum a second
  polling/worker loop) this single-machine, single-process architecture has no
  other need for.
- **C — Current streaming architecture + request identity/recovery**: this is
  effectively Design A stated differently — the recommendation *is* "keep the
  current stream, add identity and a recovery path on top," not a replacement
  of streaming with polling-only. Folded into Design A above rather than
  treated as a separate option.
- **D — Heartbeat-only extension**: **explicitly insufficient**, tested
  directly against Phase 9's own question. A periodic "still deliberating"
  frame during `echo_query()` would reduce how *often* the 300s timeout trips
  (a real, cheap UX improvement) but does nothing for: a genuine network drop
  independent of the timeout, a Studio app restart, or — most importantly —
  deduplication, since a heartbeat carries no identity a later, independent
  HTTP request could use to recognize "this is the same interaction I already
  started." **Recommended as a complementary layer on top of Design A, not a
  substitute for it.**

---

## 12. Recommended Architecture

```
Echo Studio
  -> generates request_id (uuid4) once, at send-time
  -> POST /chat/stream {conversation_id, message, mode, request_id}
    -> server: atomic check-and-claim on request_id (generalized claim_fetch_cycle pattern)
       - already RUNNING?  -> return current status, no new echo_query()
       - already COMPLETED? -> return stored response_text, no new echo_query()
       - otherwise: write ledger entry {status: RECEIVED}, claim it {status: RUNNING}
    -> yield "status: deliberating" frame, NOW INCLUDING request_id
       (the one change that makes reconnection possible at all --
       today request_id/trace_id is only ever revealed in the final "done"
       frame, which a timed-out client never sees)
    -> echo_query(...)  [UNCHANGED -- still one blocking call, same thread]
       -- interaction_log.jsonl / council_deliberations.jsonl / RiverBrain --
       -- ALL UNCHANGED, still synchronous inside this call --
    -> ledger entry updated: {status: COMPLETED, response_text: ...}
       *** THIS is the new atomicity boundary, Section 5 ***
    -> yield token chunks (unchanged) -> yield "done" (unchanged)

If Studio's connection dies at any point:
  -> Studio reconnects via GET /chat/request/<request_id>  [NEW, minimal endpoint]
    -> reads the ledger -> RUNNING: "still working", COMPLETED: full result, FAILED: error
```

This is a genuinely small diff: one optional new request field, one new small
ledger file, one new lock-guarded dict for the claim check, one new GET
endpoint, and moving one existing write (the ledger's `COMPLETED` record)
earlier in the existing function. **No change to `echo_query()`, RiverBrain,
council deliberation, FAISS, or the token-streaming mechanism itself.**

---

## 13. Crash Semantics

- **Client disconnect**: covered by Section 8 — work continues, result becomes
  recoverable via the ledger.
- **Server crash** (`run.py` dies mid-`RUNNING`): the in-memory claim-lock dict
  is lost entirely (expected — it's deliberately in-memory only, matching
  `_SESSIONS`' own existing non-durability). The on-disk ledger entry, however,
  would be stuck reading `RUNNING` forever unless reconciled. **Recommended
  fix, reusing an existing pattern rather than inventing one**: at the next
  process startup, sweep the ledger (mirroring `crash_awareness.py`'s own
  startup-time evidence scan, Finding 51/64) and mark any entry still
  `RUNNING` from *before* the current process's own start timestamp as a
  distinct `ABANDONED` status — never silently left as a false `RUNNING`
  forever, and never silently reinterpreted as `COMPLETED`.
- **Model failure** (Ollama itself errors/hangs): already surfaces as an
  exception `echo_query()` raises, already caught by the existing `except
  Exception` block (`:316-319`) — this design routes that into `FAILED`
  rather than leaving it unrecorded.
- **Process restart** (the normal `safe_restart.sh` path): identical to server
  crash from the ledger's point of view — the startup sweep handles both
  uniformly.

---

## 14. At-Most-Once Analysis

**Yes, at-most-once execution per request_id is the correct target, confirmed
by walking through the actual side effects:**

- **RiverBrain updates**: duplicate execution means duplicate training
  observations from what was semantically one interaction — directly
  contaminates the same kind of clean-signal property this project has
  invested heavily in protecting elsewhere (Finding 3's entire cross-training
  contamination fix, Finding 35's `self_edit_coding` bucket separation).
- **Council records**: a duplicate `council_deliberations.jsonl` entry for the
  same logical turn muddies any future audit or research use of that log
  (directly relevant to this session's own earlier capability-ceiling research,
  which depends on that file's entries being real, independent observations).
- **Memory writes**: a duplicate FAISS entry for the same content is wasteful
  and could skew future retrieval (duplicate near-identical vectors).
- **Self-edit triggers**: not applicable — this path never triggers self-edit.
- **Logs / future adaptive state**: any future mechanism built on top of
  `interaction_log.jsonl` inherits whatever contamination duplication
  introduces here.

**Current behavior is honestly "at-least-once if the human retries
manually"** — precisely the mission's own suggested framing, confirmed
accurate rather than assumed. The recommended design closes this to
true at-most-once per client-supplied `request_id`.

---

## 15. Public-Exposure Considerations

Brief, per the mission's own scope — no authentication is proposed or built.

- **Request-ID guessing / cross-client result retrieval**: `GET
  /chat/request/<request_id>` should validate that the requested ID actually
  belongs to a request scoped to a `conversation_id` the caller can already
  reach through its own client-side state, not just any syntactically valid
  UUID — a cheap, structural habit to build in now even though today's
  single-user, localhost-only deployment makes it low-stakes.
- **Replay**: a `COMPLETED` result is idempotent-safe to serve repeatedly by
  design (Section 7) — this is a feature here, not a new replay vulnerability,
  since it only ever returns a result to a request_id that legitimately
  originated it.
- **Unlimited abandoned jobs / disk growth**: directly why Section 9's
  retention cap is listed as a day-one requirement, not a later optimization —
  an attacker (or just heavy future multi-user usage) submitting many distinct
  `request_id`s with no cap would otherwise grow the ledger unbounded, the
  same class of gap this project has already found and fixed for other logs
  more than once (Finding 41 D, Finding 59).
- **DoS via durable computation**: unchanged from today's risk profile — this
  design doesn't make a genuinely malicious flood of *new* distinct requests
  any cheaper to mount than it already is (each still triggers one real
  `echo_query()` call); it specifically prevents *accidental* duplication from
  a legitimate client's own retry, which is the demonstrated problem.

---

## 16. Future Verification Protocol

Designed, not executed, matching the mission's own ten cases to this specific
recommended architecture's expected behavior:

1. **Normal fast response**: `RECEIVED`→`RUNNING`→`COMPLETED`, one ledger
   entry, response delivered normally, no behavior change visible to the user.
2. **Client disconnect while Echo runs**: `echo_query()` completes regardless;
   ledger reaches `COMPLETED` with the full response text.
3. **Reconnect while request remains `RUNNING`**: `GET
   /chat/request/<id>` returns a "still running" status, no second
   `echo_query()` starts.
4. **Reconnect after completion**: `GET /chat/request/<id>` returns the
   stored `response_text` directly, no recomputation.
5. **Retry same request_id while `RUNNING`**: exactly one Echo execution —
   verified by asserting `interaction_log.jsonl`/`council_deliberations.jsonl`
   gain exactly one new entry for that `request_id`, not two.
6. **Retry same request_id after `COMPLETED`**: stored response returned;
   zero new `interaction_log.jsonl`/RiverBrain observations recorded.
7. **Same message, different request_id**: two independent, fully-run
   interactions — confirmed intentional, not deduplicated.
8. **Server crash during `RUNNING`**: after restart, the startup sweep
   (Section 13) marks the entry `ABANDONED`, never a false permanent
   `RUNNING`.
9. **Persistence substep failure** (e.g., the ledger write itself fails after
   `echo_query()` succeeded): the interaction is still correctly recorded in
   `interaction_log.jsonl`/RiverBrain (unaffected, since those writes are
   inside `echo_query()` and precede the ledger write) — but the ledger
   itself should expose this as a distinguishable partial state (e.g.,
   `COMPLETED_UNLOGGED` or a logged warning) rather than silently reporting
   full success when the transport layer's own record failed.
10. **Studio itself restarts**: a known `request_id` persisted client-side
    (e.g., in Studio's own local session state) should be recoverable via the
    same `GET /chat/request/<id>` endpoint, proving the durability promise
    survives a client-side restart, not just a network blip.

---

## 17. Compatibility

- **Other real callers of `/chat/stream`, found this session**:
  `app/experiments/gen_epistemic/chat_helper.py` (a real research script,
  confirmed via direct grep — not previously mentioned in either prior report
  in this chain). `echo_studio/api_client.py` is the other. Both continue to
  work unchanged: `request_id` is an optional field, defaulting to
  today's exact server-minted-`trace_id` behavior when absent.
- **`interaction_log.jsonl`, `council_deliberations.jsonl`, RiverBrain,
  FAISS, council behavior**: none are touched by this design — the same
  `echo_query()` call, same arguments, same internal logging.
- **Existing logs**: unaffected; the new ledger is a wholly separate file.
- **`chat_regenerate()`**: shares the exact same generator
  (`_generate_chat_response`) — the same `request_id` mechanism applies to it
  identically, with no special-casing needed.

---

## 18. What This Solves

1. Studio can time out while Echo continues — now recoverable via `GET
   /chat/request/<id>` instead of silently lost from the user's perspective.
2. The user can reliably tell whether Echo is still working — a direct ledger
   read, not a guess.
3. Completed responses becoming orphaned — closed by moving the durable
   `COMPLETED` write to immediately after `echo_query()` returns, before any
   delivery-vulnerable code runs.
4. Retries duplicating computation — closed by the atomic claim-lock keyed on
   a client-supplied, retry-stable `request_id`.
5. Persistence stages split across the lifecycle — the transport layer now has
   its own single, clear atomicity boundary (Section 5), explicitly
   distinguished from Echo's own memory/learning persistence, which this
   design deliberately does not touch or reorder.

---

## 19. What This Does NOT Solve

- **Does not make `echo_query()` itself faster** — a genuinely long
  deliberation still takes as long as it takes; this design makes that
  survivable, not shorter. (Reducing full-mode latency is a separate,
  unexamined question.)
- **Does not provide true mid-computation cancellation** — a client
  "give up" still can't stop an in-progress `echo_query()` call; Section 8
  explains why this is the correct, not merely convenient, choice given
  Python's generator model.
- **Does not add authentication or true multi-user isolation** — Section 15's
  scoping recommendation is a hygiene habit, not real access control; this
  study explicitly declines to build authentication per its own scope.
- **Does not solve delivery-acknowledgment (`DELIVERED`) tracking** — a
  `COMPLETED` result being fetched once via polling doesn't confirm Studio's
  UI actually rendered it to the user; not pursued here (Section 4).
- **Does not change how `interaction_log.jsonl`/council/RiverBrain/FAISS are
  written or ordered** — this design is additive around the existing pipeline,
  not a rework of it.

---

## 20. Repository / Runtime Integrity

- `echo_studio/api_client.py`, `app/routes_echo_studio.py`,
  `app/core/self_edit_outcome_tracker.py`, `app/internet_tools/autonomous_fetch.py`,
  `run.py`: all read only, zero edits.
- No request ledger, endpoint, request ID, queue, or heartbeat was created.
- The 300-second timeout was not changed. Persistence ordering was not
  altered. No source file was modified anywhere in this repository.
- Echo's live process (PID 71538, confirmed running at both the start and end
  of this investigation) was not stopped, restarted, or signaled.
- No learned state was modified.
- Nothing was staged, committed, or pushed. HEAD remained at
  `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`,
  throughout.
- The only new artifact produced is this report file itself, left untracked
  and unstaged.
