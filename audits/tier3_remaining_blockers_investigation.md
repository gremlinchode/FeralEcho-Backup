# FeralEcho: Forensic Investigation of the Remaining Tier-3 Blockers

No held-out task was touched, referenced, or executed. No production file was modified. The live
production server was not paused, restarted, or reconfigured. `OLLAMA_NUM_PARALLEL` was not touched.
This document investigates two specific, named questions; it does not re-litigate the whole apparatus.

## A. Development Sanity Diagnosis

**Two real candidates completed during this investigation** (up from zero at the start of this
session): `task_11` (strip_leading_prose) under `ARCH_PIPELINE` — model `qwen2.5-coder:7b` (the
pinned model, confirmed correctly propagated), 208.16s, a genuine logic bug, correctly classified
`TASK_LOGIC_FAILURE` — and the same task under `ARCH_COUNCIL` — 4 real calls, 451.2s, **passed**. This
matters for the diagnosis itself: **the apparatus is not fundamentally broken.** It produced two
complete, correctly-classified, differentiated real results. What prevents it from completing quickly
is external, not internal.

**Direct, concurrent measurement, taken without disturbing production**: five consecutive samples of
the live server's own CPU usage read 93.0%, 96.1%, 99.0%, 98.0%, 96.0% — sustained, not intermittent.
`echo:latest` was resident in `ollama ps` on every sample, with its keep-alive countdown reading
~26 seconds *every time* — meaning the countdown was being continuously reset by fresh incoming
requests, not idling. Direct log evidence, from the same window, names the actual sources: **three
separate, genuinely concurrent autonomous loops** — `emergent_loop` (a complete real
reflection/memory/garden cycle observed inside a ~40s window), `AutonomousSelfEdit` (a real council
synthesis completing, followed ~30s later by a fresh "Warming up echo:latest" for another Optuna
trial), and `model_guided_autonomous_loop` (observed actively querying councillors and sending
opinions for synthesis in the same window — the same loop this investigation previously identified as
a contention source, confirmed still active now). This is not circumstantial correlation; it is direct,
timestamped proof of concurrent demand on the one Ollama queue (`OLLAMA_NUM_PARALLEL` still unset)
this session's own script was also waiting on.

The harness process itself is confirmed **alive, not deadlocked** — real wall-clock progress occurred
(two full candidates), and its own CPU time crept upward across repeated checks, consistent with
genuine I/O-wait on a queued request rather than a hang. Internal sequencing is confirmed correct (this
was already verified at the code level in the prior mission); the delay is external.

## B. Operating-Envelope Determination

**Yes — exclusive or substantially lower-contention Ollama capacity is required for this experiment to
complete in a practical timeframe.** This is classified as **A and C together, not B**: the apparatus
is technically valid (proven by two real completions) but cannot obtain a clean, *timely* measurement
environment while at least three live production autonomous loops compete for the same
single-threaded queue. This is documented as an **experimental prerequisite**, not worked around:
*"the Tier-3 experiment, including its own development sanity check, requires either an explicit
low/no-contention window, or acceptance of substantially longer, patient, unattended wall-clock time
per candidate under real production load."* Distinguishing the two framings the mission asked for
directly: **this is "the experiment is valid, but the machine cannot provide a clean measurement
environment while production inference is active" — not "the experiment is broken."**

## C. Pipeline Call-Path Forensic Trace

Full table in the JSON. Summary: `BASE_1`, every `BASE_N` call, and both `ARCH_COUNCIL` legs
(councillor + synthesis) all funnel through `app.ollama_handler.stream_query_ollama()`, which this
investigation's own monkeypatch captures `done_reason` from. **`ARCH_PIPELINE` alone routes through a
separate, independent function** — `generate_code_from_plan()` → `echo_query()` →
`echo_model_orchestrator.ollama_query()` — a direct, non-streaming `/api/generate` call that discards
any `done_reason` field before this harness ever sees the response, confirmed by the function's own
docstring ("bypasses app/ollama_handler.py entirely") and by direct source read. This is not recoverable
without touching that second production function, which this investigation continues to decline to do.

## D. Truncation-Bias Analysis — A More Serious Finding Than Originally Scoped

All 7 required synthetic cases were constructed and run directly against the real classification logic,
with no model calls: genuine truncation via ground-truth `done_reason` (cases 1-2) → correctly
`GENERATION_TRUNCATED`; normal completion with genuine wrong logic (cases 3-4) → correctly
`TASK_LOGIC_FAILURE`; no ground truth available, obvious truncation via the fence heuristic (case 5) →
correctly `GENERATION_TRUNCATED`; no ground truth, valid completion (case 6) → correctly `PASS`;
extraction/logic failure with no truncation signal at all (case 7) → correctly `TASK_LOGIC_FAILURE`.
**All seven pass in isolation.**

**But investigating *why* they pass in isolation surfaced a real, confirmed bug the original scoping
didn't anticipate**: `classify_result()`'s ground-truth lookup is a shared, global,
300-second-windowed list with **no per-call scoping** — it simply takes the most recently appended
event. For `BASE_1`/`BASE_N`/`ARCH_COUNCIL`, this is safe only because each arm's own call is always
the last thing appended before its own classification runs (a property of sequential execution, not of
any explicit scoping in the code). **For `ARCH_PIPELINE` specifically — which never appends anything of
its own, since its call path bypasses the shared capture point entirely — this means the "most recent"
event is *always* some other arm's leftover, never its own.** A direct synthetic test proved this: an
ordinary `ARCH_PIPELINE`-shaped response (valid-looking, closed fence, genuinely failed for an ordinary
reason) was wrongly classified `GENERATION_TRUNCATED` purely because a *different* arm's real
truncation event from 5 seconds earlier was still sitting in the shared list. **The one real completed
`ARCH_PIPELINE` candidate this session was not affected only because it happened to run first in its
randomized arm order, before any event existed to contaminate it — fortunate ordering, not correct
code.** This is worse than the originally-disclosed gap: that gap was an *absence* of signal (safe,
correctly falls back to the fence heuristic); this bug is a *false-attribution* risk, capable of
tagging a perfectly ordinary Pipeline failure as a phantom truncation using a real signal that belongs
to someone else's call entirely.

## E. Synthetic Test Results

All 7 required cases plus the additional cross-contamination case are tabulated in full in the JSON's
`part3_truncation_bias_analysis`. Net finding: **the classification rules themselves are correct; the
supporting state-tracking mechanism that feeds them is not.**

## F. Minimum Repair (Designed, Not Implemented)

Tag every `_truncation_events` entry, at capture time, with a unique per-call identifier, and have
`classify_result()` consult *only* the entry matching the current call's own marker — never "whatever is
most recent." For `ARCH_PIPELINE` specifically, since its path structurally cannot ever produce such a
tag, the classifier should explicitly branch on a known per-arm capability flag and skip the
ground-truth lookup entirely for it, falling straight through to the fence heuristic every time, rather
than silently querying a list that may hold irrelevant data. This touches only this investigation's own
harness script — no production file, no retries, no change to F1's role, no change to the primary
endpoint, no additional inference opportunity for any arm. **Designed here; not implemented, per
instruction.**

## G. Residual Confounds

The newly-found event-scoping bug is designed but not repaired — a live risk for any future run of the
current code. `BASE_N` has still never completed a real cycle; its synthesis behavior against genuine
same-model attempts remains entirely unobserved. The synthesis-equivalence question is explicitly
**unresolved, not merely under-tested**: it is genuinely unknown whether reconciling one's own
near-identical attempts is systematically easier or harder than reconciling visibly different models'
outputs, and this investigation does not guess in either direction. Ollama contention is, per today's
direct measurement, *not* worse in every respect than prior sessions (swap was measured lower than one
earlier peak) but is real, current, and — via three concurrently-active loops — arguably more precisely
characterized as severe than before. Model-diversity-vs-orchestration-structure remains structurally
unresolvable by this four-arm design, as repeatedly disclosed; any report language must keep using the
bounded phrasing ("the real Council package vs. a budget-matched self-consistency baseline"), never
"orchestration" or "architecture" in isolation.

## H. Readiness Verdict

# NOT READY — BLOCKERS REMAIN

A completed real sanity candidate *is* necessary and has now partially happened — two, not zero,
completed this session, which is genuine progress and is recorded as such. But readiness requires more
than "the apparatus can complete a candidate when circumstances allow it" — it requires (1) `BASE_N`
completing at least once for real, which has not happened, and (2) the newly-found truncation-scoping
bug being repaired, since it is a confirmed, real risk of contaminating the primary endpoint's data
specifically for the arm this whole investigation was already worried about. Both are concrete,
nameable gaps, not vague caution. The default the mission specified — remain NOT READY absent strong
evidence otherwise — is exactly the correct call here: two lucky, well-ordered completions are
encouraging, not sufficient.
