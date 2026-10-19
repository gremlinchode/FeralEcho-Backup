# Echo Studio Timeout, `run.py` Request Lifecycle & Information-Fate Study

**Live read-only investigation.** No restart, no stop, no source modification, no
timeout/config change, no controlled probe executed (justified in Section 14).
Nothing staged, committed, or pushed.

---

## 1. Executive Summary

**When Echo Studio shows `Read timed out`, the most likely real meaning in this
architecture is: "Echo got your message and is still working on it — Studio just
stopped waiting."** Traced directly from source, not inferred from the error text:
the server-side generator that handles `/chat/stream` runs `echo_query()` as one
single, unbroken, synchronous call with **zero output produced while it runs** —
between the initial "deliberating…" status frame and the first real response
token, nothing is sent over the wire. If that gap exceeds Echo Studio's 300-second
read timeout, the client gives up and raises `Read timed out` — but Python has no
mechanism to interrupt a thread that's actively executing (not suspended at a
yield), so **the server cannot know the client left, and keeps computing exactly
as if nothing happened.**

Once `echo_query()` finally returns, its own internal persistence — the real
interaction log, the full council-deliberation record, and RiverBrain's adaptive
statistics — has **already been written, synchronously, before the timeout could
have any effect on it.** What's genuinely at risk is narrower than "the whole
interaction": Echo Studio's own conversation-history record and the FAISS
vector-memory write both happen *after* the response starts streaming back, and a
client that already disconnected will very likely cause that final stretch of the
generator to be torn down mid-flight (via Python's `GeneratorExit`) before it gets
there — meaning the completed response is very plausibly generated and durably
logged, but not shown to Gremlin and not folded into Studio's own visible
conversation or memory.

This project's own history already recorded the shape of this exact phenomenon
once before (CLAUDE.md Finding 54: "a client-side stream that this session's own
tooling had already shown, twice, same night, can time out client-side while the
server keeps working") — this investigation traces precisely *why* that happens
and *which* downstream pathways survive it.

---

## 2. Live Runtime Baseline

Captured fresh, this session:

- **Timestamp**: 2026-09-28 22:28:21 PDT.
- **Git**: HEAD `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`;
  34 pre-existing dirty paths, none touched by this mission.
- **`start_echo.sh`** (watchdog): PID 56610, started 2026-09-28 09:44:38, uptime
  ~12h44m.
- **`run.py`**: PID 71538, started 2026-09-28 19:15:54, uptime ~3h12m — this start
  time is consistent with a real crash-and-restart already independently
  identified in this session's own earlier seam-signal research (a real
  MLX-signature crash at 2026-09-28T19:15:45 -0700, watchdog restart 9 seconds
  later).
- **Multiprocessing resource tracker**: PID 71548 (child of 71538).
- **`tee -a memory/echo_watchdog.log`**: PID 71539.
- **Port 5000**: bound and `LISTEN`ing, owned by PID 71538 — confirmed via `lsof`.
- **Flask server mode**: `app.run(host="0.0.0.0", port=5000, threaded=True,
  use_reloader=False)` (`run.py:1581`) — every incoming request gets its own
  worker thread; there is no async event loop or WSGI worker pool beyond this.

---

## 3. Echo Studio Client

Traced to source, not inferred from the exception text.

- **File**: `echo_studio/api_client.py`, `ApiClient.stream_chat()`.
- **Library**: plain `requests` (deliberately, per the module's own docstring, to
  avoid an SSE-client dependency the backend doesn't need).
- **Call shape**:
  ```python
  with requests.post(
      f"{self.base_url}/chat/stream", json=payload, stream=True,
      timeout=(self.timeout, 300),  # (connect=10s, read=300s)
  ) as resp:
      for raw_line in resp.iter_lines(decode_unicode=True):
          ...
  ```
- **Timeout is a tuple**: `self.timeout` (10.0s) is the *connect* timeout; `300`
  is the *read* timeout. With `requests`/`urllib3`, a read timeout on a streamed
  response applies **per underlying socket read** — i.e., the maximum gap allowed
  between successive bytes arriving, not a cap on the total request duration. A
  server that keeps sending *something* (even a small keep-alive chunk) every
  under-300s would never trip this; a server that goes fully silent for ≥300s
  will.
- **No retries**: nothing in `stream_chat()` retries on failure — a `ReadTimeout`
  propagates straight up to the caller (`ChatStreamWorker`, per the module's own
  docstring reference) as an uncaught exception from the `with` block.
- **Synchronous/blocking**: `stream_chat()` is a blocking call, explicitly
  documented as intended to run on a worker thread, never the Qt main thread.
- **Confirmed the exact exception source**: `HTTPConnectionPool(host='127.0.0.1',
  port=5000): Read timed out` is `urllib3`'s own exception string, raised when the
  300-second read-timeout tuple value is exceeded — this is the `requests`/
  `urllib3` library's standard wording, not custom FeralEcho code, confirming
  this is the client's read timeout specifically (not a connect failure, and not
  a custom application-level error).

---

## 4. Server Request Path

- **Route**: `POST /chat/stream` → `chat_stream()` (`app/routes_echo_studio.py:384`).
- **Response construction**: `Response(stream_with_context(_generate_chat_response(...)),
  mimetype="text/event-stream")` — a genuine SSE stream, generator-driven.
- **`_generate_chat_response()`** (`:140`): a thin wrapper whose only job is a
  `try/finally` around `yield from _generate_chat_response_body(...)`, calling
  `conversation_activity.mark_start()`/`mark_end()` so autonomous loops defer to
  a real conversation in flight — this `finally` **does** run even on early
  generator termination (Python guarantees `finally` blocks run when a suspended
  generator is closed via `GeneratorExit`), so this one piece of bookkeeping is
  the most timeout-resilient part of the whole path.
- **`_generate_chat_response_body()`** (`:158`) — the real work, entirely
  synchronous within one Python generator, one thread, no background tasks:
  1. Build the full prompt + retrieve memory (`_build_full_prompt`).
  2. Check for tool dispatch.
  3. `yield` the initial `{"type": "status", "status": "deliberating"}` frame —
     **the first and only bytes sent before real generation begins.**
  4. For full mode: `raw_response = echo_query(full_msg, task_type=..., source="user_conversation",
     system=system_context, trace_id=trace_id, post_synthesis_hook=_post_synthesis_verify)`
     — **one single, blocking call.** Nothing is yielded while this runs.
  5. Once it returns: chunk the completed response text and `yield` each chunk as
     a `{"type": "token", ...}` frame (with a small `_CHUNK_DELAY_S` sleep between
     chunks — presentation-layer "typing" effect over an already-finished answer,
     not real generation latency).
  6. Run post-synthesis verification (code/self-knowledge caveats), if not
     already run inside `echo_query()`'s own hook.
  7. Write `memory/retrieval_provenance.jsonl` (best-effort, `try/except`).
  8. Persist to Studio's own conversation history: `store_turn_in_history()`
     (in-memory only) then `save_turn_to_server()` (a self-loopback `POST
     /memory/conversation`, 3s timeout, which is the actual FAISS-write trigger
     per that function's own docstring) — wrapped in `try/except Exception`
     (Finding 47's fix, see Section 9).
  9. `yield` the final `{"type": "done", ...}` frame.

---

## 5. Causal Diagram

```
Gremlin types message
  -> Echo Studio's ChatStreamWorker thread
    -> ApiClient.stream_chat() -- requests.post(stream=True, timeout=(10,300))
      -> 127.0.0.1:5000  POST /chat/stream
        -> Flask (threaded=True) spawns a dedicated worker thread
          -> chat_stream() builds Response(stream_with_context(generator))
            -> _generate_chat_response_body() [ONE thread, ONE generator, fully synchronous]
               1. build prompt + retrieve memory
               2. yield "status: deliberating"   <-- LAST byte sent before the gap
               3. echo_query(...)                <-- BLOCKING, no yields inside;
                    |                                 this is where deliberate_and_learn()
                    |                                 runs its full council cycle AND
                    |                                 synchronously writes
                    |                                 interaction_log.jsonl,
                    |                                 council_deliberations.jsonl,
                    |                                 RiverBrain.learn()/.save()
                    |                                 -- ALL BEFORE RETURNING
                    v
               4. yield token chunks              <-- FIRST byte after the gap;
                                                       this is where a dead client
                                                       socket first gets discovered
               5. post-synthesis verification
               6. write retrieval_provenance.jsonl
               7. store_turn_in_history() [in-memory] + save_turn_to_server()
                    [self-POST -> /memory/conversation -> FAISS write]
               8. yield "done"
```

**The gap between steps 2 and 4 is exactly where a 300s client read timeout would
fire** — and it is a gap with zero bytes in flight, entirely inside one blocking
Python call.

---

## 6. Timeout Semantics

Answering Phase 3's exact taxonomy: this is **Case B** — the connection succeeds
(the client can reach 127.0.0.1:5000 and the request is accepted; if it weren't,
`requests` would raise a *connect* timeout or a connection-refused error with
different wording, not "Read timed out"), but no response bytes arrive before the
client's read deadline. A secondary possibility, **Case C** (response began, then
stalled), is architecturally possible too if the client happens to be mid-way
through consuming token chunks when some *later* step stalls (e.g., a slow
`save_turn_to_server()` self-POST, though that has its own independent 3s
timeout and silently swallows its own failure) — but the dominant, best-evidenced
case is B: the "deliberating" status frame arrives quickly, then total silence
until `echo_query()` returns.

**Does the client timeout automatically cancel server-side processing? No — and
it structurally cannot, for the specific window that matters most.** While
`echo_query()` is executing, the server's request-handling thread is not
suspended at a `yield` — it is actively running Python code. Python's generator
protocol only allows an external caller (here, Werkzeug's response-writing loop)
to inject `GeneratorExit` at a point where the generator is *suspended* (i.e., at
a `yield`). A generator that is not currently suspended cannot be interrupted by
anything short of forcibly killing the OS thread, which nothing in this codebase
does. **This is not a design choice that could be described as a "cancellation
policy" — it is a direct, mechanical consequence of Python's generator model
combined with this specific code putting the entire long-running call in one
unbroken stretch with no intermediate yield.**

---

## 7. Historical Timeout Reconstruction

**No clean historical timeout event could be reconstructed with precise
before/after timestamps from currently available logs**, for two disclosed
reasons, not for lack of trying:

- `memory/echo_watchdog.log`'s current live window covers 2026-09-14 → present
  (95.5MB, near Finding 51's 100MB rotation cap; the prior generation,
  `echo_watchdog.log.1.gz`, is the only older history retained, per this
  project's own one-generation retention policy). Within the current 14-day
  window, **every single logged `POST /chat/stream` request shows HTTP 200** —
  zero non-200 or otherwise anomalous status codes.
- **This 200-only pattern does not prove no timeout occurred.** Werkzeug's access
  log records the response's nominal status code (set the moment headers are
  first sent, i.e., as soon as the "deliberating" frame goes out) — it has no way
  to retroactively mark a stream as "started successfully, then the client
  vanished partway through." A request whose client disconnected after the
  status frame but before "done" would be logged identically to a fully
  successful one. **The specific failure mode this mission investigates is
  architecturally invisible to the one access log available.**
- No server-side exception log lines (`chat generation failed`, `history persist
  failed`, `prompt assembly failed`) appear anywhere in the current 95MB window —
  consistent with the finding above: a client-side `GeneratorExit`-triggered
  termination produces **no log line at all**, since nothing in
  `_generate_chat_response_body()` wraps that specific failure path with a
  logging `except` clause (and, per Section 6, could not catch it with a plain
  `except Exception` even if it tried).

**Directly corroborating, already-documented precedent, found in this project's
own prior history rather than reconstructed fresh**: CLAUDE.md's Finding 54
explicitly records, from direct first-hand observation the same night it was
written, that "a client-side stream... this session's own tooling had already
shown (twice, same night) can time out client-side while the server keeps
working." This is independent, already-existing confirmation that the mechanism
traced in this report is not merely theoretical — it has been directly observed
in this exact codebase before.

---

## 8. Information-Fate Matrix

| Artifact / subsystem | Input written? | When (relative to timeout)? | Survives client timeout? | Response written? | Evidence |
|---|---:|---|---:|---:|---|
| `memory/interaction_log.jsonl` | Yes | **Before** — inside `echo_query()`'s own synchronous call, before it returns to the generator | **Yes, unconditionally** — this write happens regardless of whether the client is still connected | Yes (the real generated response text) | `app/core/echo_model_orchestrator.py:206`, called from within `echo_query()`/`deliberate_and_learn()`'s own return path |
| `memory/council_deliberations.jsonl` | Yes (full mode only) | **Before** — `_log_council_deliberation()` runs synchronously inside `deliberate_and_learn()`, "right before the final `return final_response`" per its own documented design | **Yes, unconditionally** | Yes (raw + truncated per-councillor responses) | `app/core/river_deliberation.py:684, 1183, 1511` |
| RiverBrain `model_task_stats` (in-memory) | Yes | **Before** — `.learn()` updates the in-memory dict synchronously inside `echo_query()` | **Yes, unconditionally** (the in-memory update; see below for on-disk persistence) | N/A (statistics, not response content) | Established architecture, independently re-confirmed this session's own earlier "Natural Learning Event Hunt" mission |
| `memory/river_brain.pkl` (on-disk) | Yes, eventually | **Independent of this request entirely** — a separate background writer thread persists on its own ~60s timer, not tied to any single `.learn()` call | Yes — unaffected by a client-side HTTP timeout, since the server process itself never stops | N/A | Confirmed in this session's own prior Tier-7/8 capability-ceiling research |
| `memory/retrieval_provenance.jsonl` | Conditional | **After** the token-yielding loop, before "done" | **At risk** — only reached if the generator survives past the token-yield stage | N/A (metadata, not the response) | `app/routes_echo_studio.py:339-352` |
| Studio's `session["conv_history"]` (in-memory) | Yes, if reached | **After** the token-yielding loop | **At risk**, same reason | Yes | `app/routes_echo_studio.py:365-368` |
| `save_turn_to_server()` → `/memory/conversation` → FAISS | Yes, if reached | **After** the token-yielding loop, via a self-loopback HTTP POST with its own independent 3s timeout | **At risk**, twice over — both from the outer generator possibly being torn down before reaching this line, and from this call's own short timeout silently failing under any contention | Yes | `app/core/conversation_service.py:284-313` |
| Final SSE `"done"` frame (what Echo Studio itself would display) | — | Last step | **Never reached if the client already disconnected** | — | `app/routes_echo_studio.py:375-381` |

---

## 9. Post-Timeout Processing

**Yes — for the specific case this mission asked about, server processing
demonstrably continues after a client would time out, because it structurally
cannot be stopped while `echo_query()` is running (Section 6).** The generator
does not "notice" a client disappearing; there is no polling, no cancellation
token, nothing analogous. The only place the server can discover a dead
connection is at its own next attempted socket write — which, per this code's
structure, is the first `yield` of a response token, occurring only after
`echo_query()` has already fully completed and done all of its own internal
persistence.

Once that first post-generation write is attempted against an already-closed
client socket, the practical outcome depends on WSGI/Werkzeug's own handling of a
failed write during streamed response delivery — standard behavior for a
generator-based streaming response under `stream_with_context` is that a write
failure causes the serving layer to stop iterating and close/garbage-collect the
generator, which raises `GeneratorExit` at that suspended `yield` point. Since
`GeneratorExit` is a `BaseException`, not an `Exception`, **it is not caught by
any of the `except Exception` blocks present in this function** — it propagates
straight through, immediately halting execution at that point. This specific
mechanical detail was reasoned from Python's own generator/exception semantics
and this file's actual code structure, not observed directly in a live trace in
this pass (see Section 14 for why a live probe was judged unnecessary to confirm
it further).

---

## 10. Response Fate

**Generated but orphaned, in the specific and most likely case.** The complete
response text exists — it was fully computed by `echo_query()` and is already
durably recorded in `memory/interaction_log.jsonl` and
`memory/council_deliberations.jsonl` **before** the point where a dead client
connection would ever be discovered. But delivery to Echo Studio itself fails
(the "done" frame, and likely the token chunks too, never successfully reach a
client that already gave up), and the Studio-specific persistence (conversation
history, FAISS) sits downstream of the point where execution is most likely to
be cut off.

**The response is not lost in any absolute sense — it is recoverable, just not
through Echo Studio's own normal display or retrieval path.** Both
`interaction_log.jsonl` and `council_deliberations.jsonl` entries carry the same
real `trace_id` (minted once at the top of `_generate_chat_response_body()`),
so a specific orphaned turn can be located precisely by searching either file for
that ID, or by timestamp and message content, even though Echo Studio's own UI
never showed it.

---

## 11. Memory / Learning Fate

Using the mission's own Level 0–3 scale, precisely:

- **Level 1 (persistent memory)**: **Reached, unconditionally** for
  `interaction_log.jsonl`/`council_deliberations.jsonl` — these are real,
  durable, retrievable records regardless of client timeout. **Conditionally
  reached** for FAISS/vector memory specifically (via `save_turn_to_server()`),
  which sits downstream of the at-risk zone.
- **Level 2 (adaptive statistics)**: **Reached, unconditionally.** RiverBrain's
  in-memory `model_task_stats` update happens inside `echo_query()`'s own call,
  before any timeout-vulnerable code runs; on-disk persistence follows its own
  independent ~60-second writer-thread schedule, unaffected by this request's
  own HTTP lifecycle.
- **Level 3 (reusable competence)**: not applicable to an ordinary conversational
  turn, and nothing here suggests otherwise — consistent with this mission's own
  stated expectation.

**The ordering that matters most, stated plainly**: the two most valuable
persistence/adaptation pathways (real interaction log, RiverBrain's adaptive
statistics) run *before* the HTTP response delivery even begins in earnest — a
timeout downstream of that point does not un-happen them. The pathways that
*are* at genuine risk (Studio's own conversation history, FAISS) are exactly the
ones a user would notice missing (their message wouldn't appear in later
retrieval or in Studio's own history), which is a real, disclosable asymmetry:
**the system learns from and logs the interaction reliably; showing it back to
the user, and folding it into the conversational-memory surface a human would
naturally check, is the fragile part.**

---

## 12. Root-Cause Analysis

**Timeout cause: LIKELY BUT NOT PROVEN.** The architectural mechanism (one
long, unbroken blocking call with zero intermediate output, against a 300s
client read timeout) is established with high confidence directly from source.
What is *not* independently, empirically confirmed in this pass is that a real
`echo_query()` full-mode deliberation has, in fact, exceeded 300 seconds on this
machine recently — no historical log data (Section 7) could establish that
duration directly, and no live probe was run to measure it (Section 14).
Directly corroborating precedent exists (Finding 54, cited above), but that
observation predates this specific investigation and wasn't re-measured here.

**Latency decomposition, to the extent evidence allows**:
- Studio → server receive: near-instant (localhost, no network hop).
- Server receive → "status" frame: fast — this only requires prompt assembly and
  a tool-dispatch check, both light-weight per the code read.
- **`echo_query()` (deliberation + synthesis + persistence)**: the entire
  candidate window for a 300s+ stall. Full mode's real cost here is a multi-model
  council deliberation (several sequential real Ollama calls, each with its own
  real generation latency) followed by a synthesis pass — this project's own
  extensive documented history (CLAUDE.md's Token Limits, Council Deliberation
  Logging sections) confirms this is genuinely capable of taking substantial
  wall-clock time under real model load, though no single measured real-world
  duration was captured in this pass.
- Post-processing (verification, chunking, persistence): comparatively brief per
  the code read (no additional model calls beyond what verification's own sandbox
  checks require, and those are narrowly scoped).
- Response return: only reached if the client is still there to receive it.

**No evidence was found of the other candidate causes** (lock contention, model
loading/swapping, a stuck subprocess) actively contributing right now — this
reflects the absence of any anomalous log evidence in the current window, not a
direct measurement ruling each one out individually.

---

## 13. Concurrency / Retry Risk

**Yes — resending a timed-out message risks genuine duplicate processing, not a
harmless retry.** `run.py` runs Flask with `threaded=True`: a new `POST
/chat/stream` for the same `conversation_id`, submitted while the original
request's `echo_query()` call is *still running* in its own thread, executes
**fully independently and concurrently** — nothing in this code path checks
whether a request for the same conversation is already in flight.

Concretely, if Gremlin resends after seeing "Read timed out":
- Both the original (still-running) and the new request will independently run
  their own full council deliberation.
- Both will independently write their own `interaction_log.jsonl` and
  `council_deliberations.jsonl` entries, and both will independently feed
  RiverBrain's adaptive statistics — **the same semantic input processed and
  learned from twice**, not deduplicated anywhere in this path.
- `session["_lock"]` (around `store_turn_in_history()`) prevents the two
  requests from *corrupting* the in-memory history list by racing on it, but
  does **not** prevent both from appending their own separate turns to it —
  whichever finishes first is appended first.
- Responses can arrive out of order relative to which was sent first, and
  persistence likewise.

---

## 14. Controlled Probe

**Not performed, deliberately, and stated as such per this mission's own
guidance that a non-diagnostic outcome is an acceptable result.** Two reasons:

1. The core mechanical questions this mission asks (does a client timeout
   interrupt server processing; what runs before vs. after the response
   delivery point) are settled by direct, deterministic facts about Python's
   generator/exception model combined with this specific code's structure — they
   do not require empirical reproduction to establish with confidence, the same
   way tracing `edit_momentum`'s definition in a prior mission this session
   didn't require running new correlations to be certain of its source.
2. A genuinely benign, ordinary Echo Studio message is *unlikely* to naturally
   take ≥300 seconds under normal (non-degraded) conditions — reliably
   reproducing the exact failure state would most likely require either waiting
   for organic load to recreate it, or artificially degrading the system, both
   of which are outside this mission's explicit boundaries (no manufacturing a
   timeout through destructive means, no escalating load to force one).

If a future mission wants direct empirical confirmation of the exact
write-failure/`GeneratorExit` behavior, the safest non-destructive approach
would be a real Echo Studio session naturally producing a long full-mode
deliberation, observed passively (log tailing, not code instrumentation) — not
attempted here.

---

## 15. Practical Guidance for Gremlin

Based only on the established architecture above:

- **Do not immediately resend.** The original request is very likely still
  running — Section 6 establishes that a client-side timeout has no way to
  interrupt server-side processing while `echo_query()` is executing. Resending
  while it's still in flight will cause Echo to process the same message twice
  (Section 13), not just retry a failed attempt.
- **A reliable signal the original request actually finished**: check
  `memory/interaction_log.jsonl`'s or `memory/council_deliberations.jsonl`'s most
  recent entries for content matching the timed-out message. Both are written
  **synchronously, before the response ever reaches Echo Studio** (Section 8) —
  if a matching, recently-timestamped entry appears there, the original request
  completed on the server even though Studio never showed it, and it is safe to
  read the answer directly from that log rather than resend.
- **No specific wait time is recommended** — this report does not have a
  measured real-world duration for a full-mode deliberation to base one on
  (Section 12), and inventing one would overstate what the evidence establishes.
- **If checking the logs shows no matching entry after a reasonable wait**, the
  request more plausibly failed before or during `echo_query()` itself (e.g., a
  genuine exception, which *would* be logged per `_generate_chat_response_body()`'s
  own `except Exception` block around that call) — in that case a resend is the
  right call, since nothing would be running to duplicate.

---

## 16. Remaining Uncertainties

Stated plainly, not glossed over:

- **No real, measured `echo_query()` full-mode duration was captured** — the
  root cause (a deliberation genuinely exceeding 300s) is architecturally
  well-supported and independently corroborated by this project's own prior
  Finding 54, but not freshly, empirically measured in this pass.
- **The exact WSGI-layer behavior on a failed write** (whether Werkzeug's dev
  server explicitly calls `.close()` on the generator immediately upon a
  detected `BrokenPipeError`, versus relying on garbage collection to eventually
  trigger the same `GeneratorExit`) was reasoned from Python/WSGI's documented
  generator-closing semantics, not observed directly in a live trace.
- **Whether the very first post-`echo_query()` write reliably fails immediately**
  (versus succeeding into a kernel buffer before a later write fails) is a
  real, OS/timing-dependent detail not independently confirmed here.
- **No definitive historical instance** (with clean before/after timestamps) of
  this exact failure was reconstructed, for the reasons given in Section 7 —
  the available log genuinely cannot distinguish this case from an ordinary
  successful request.

---

## Required Verdicts

**Timeout Cause**: **LIKELY BUT NOT PROVEN** — mechanism is established with high
confidence from source; the specific real-world duration trigger was not
freshly measured.

**Input Fate**: **PERSISTED BEFORE TIMEOUT** — the user's message and Echo's full
response are written to `interaction_log.jsonl`/`council_deliberations.jsonl`
synchronously inside `echo_query()`, before the point where a client timeout
could have any effect.

**Server Processing**: **CONTINUES AFTER CLIENT TIMEOUT** — established directly
from Python's generator/exception model: a non-suspended generator cannot be
externally interrupted.

**Response Fate**: **TIMING-DEPENDENT, LEANING GENERATED BUT ORPHANED** —
the response is very likely fully generated and durably logged
(`interaction_log.jsonl`/`council_deliberations.jsonl`), but delivery to Echo
Studio, and the Studio-specific conversation-history/FAISS persistence
downstream of the token-yield stage, are architecturally at risk of never
completing once the client has already disconnected.

**Echo Digestion**: **PARTIAL PATHWAYS RUN** — the core learning/logging
pathways (interaction log, council deliberation record, RiverBrain adaptive
statistics) run unconditionally and complete before any timeout-vulnerable code;
Studio's own conversation-history and FAISS-write pathways are conditional on
the generator surviving past the point a dead connection would be discovered.

---

## 17. Repository / Runtime Integrity

- `echo_studio/api_client.py`, `app/routes_echo_studio.py`,
  `app/core/conversation_service.py`, `app/core/river_deliberation.py`,
  `app/core/echo_model_orchestrator.py`, `run.py`: all read only, zero edits.
- No timeout value, Flask configuration, Ollama configuration, or Echo Studio
  code was modified.
- Echo's live process (PID 71538, confirmed running throughout at the start and
  end of this investigation) was not stopped, restarted, or signaled.
- No memory, learned state, or persistent file was modified by this
  investigation — all reads were passive (`grep`, `ps`, `lsof`, file reads).
- No controlled probe was executed (Section 14).
- Nothing was staged, committed, or pushed. HEAD remained at
  `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, matching `origin/main`, throughout.
- The only new artifact produced is this report file itself, left untracked and
  unstaged.
