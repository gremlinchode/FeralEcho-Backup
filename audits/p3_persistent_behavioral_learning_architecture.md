# P3-CAUSAL-LEARNING — Architecture Mapping (Design → Real Codebase)

Design-only. This document maps each of the three experimental conditions onto the exact, real
functions and files they would invoke, citing the two prior read-only audits as the evidentiary basis
— no new claims about the codebase are made here that weren't already established and, where
consequential, independently re-verified in `echo_learning_causal_autopsy.md`.

## Condition A — context

**Real call shape:** `EchoDirectResponder(model="echo:latest", ...).respond()` →
`river_deliberation._ollama_query(model, prompt, system=formation_text, task_type="personal")`.

No memory write, no retrieval, no RiverBrain/classifier touch (Design B, confirmed clean throughout
this project's prior experiments). This is the simplest condition and needs no further architectural
justification beyond what P1/P1.2/the Learning Investigation already established for this exact
responder pattern.

## Condition B — restart + retrieval available

**Real call shape, Formation:** identical to A, but the response is additionally passed to
`app.core.memory_bridge.add_to_vector_memory(combined_text, meta={...})` — the same real function
traced end-to-end in `echo_learning_causal_architecture.md`'s mechanism #1. This call passes through
the real `memory_write_validator.py` gate; the design's own `state_mutation` instrumentation field
exists specifically to record whether this gate allowed, warned-but-allowed, or blocked the write (the
Learning Investigation's own pilot found this gate can silently block a write — e.g. its
exact-duplicate-signal check — and this design must not assume a write succeeded without checking).

**Real call shape, Probe:** after the required ≥30-minute wait, `app.core.memory_bridge.
retrieve_relevant_memories(probe.text, top_k=k)` is called for real, its result passed through
`app.core.conversation_service.retrieve_memory_context()`/`build_context_system_note()` — the exact
same functions real production code uses (`app/routes_echo_studio.py`'s `_memory_search_fn` chain,
re-confirmed fresh in the P2 autopsy) — then the probe question is sent via `EchoDirectResponder` with
the resulting system context.

**Known behavior to expect, per prior evidence, not assumed to be different here:** the Learning
Investigation's own live pilot found real retrieval sometimes surfaces genuinely unrelated content
instead of the intended target, depending on embedding similarity — this design's instrumentation
(`state_read` field, recording the verbatim retrieved block) exists specifically to make this visible
per-trial, not to assume retrieval reliably surfaces the taught rule.

## Condition C — restart + retrieval blocked

**Real call shape, Formation:** identical to A/B's Formation call, **except `add_to_vector_memory()`
is never called.** No gate, no write, no validator log line — nothing.

**Real call shape, Probe:** identical to B's probe call in every respect except that
`retrieve_relevant_memories()` is either never called, or called and its result discarded/replaced
with an empty string before being threaded into `build_context_system_note()` — belt-and-suspenders,
since the content was never written in the first place, this second step is redundant but cheap
insurance against an unrelated pre-existing memory entry coincidentally matching the probe's wording
(a real, if unlikely, possibility given the shared production store contains 123,000+ real entries,
as directly confirmed in the P2 autopsy).

## Negative-control instrumentation: RiverBrain / task_type_classifier state

Per `echo_learning_causal_architecture.md`'s mechanisms #2 and #6, `EchoDirectResponder`'s call path
should never touch `model_task_stats` or `task_type_classifier.pkl` at all (Design B bypasses
`deliberate_and_learn()`/`log_interaction()` entirely). This design's `routing_state` instrumentation
field — a cheap fingerprint (size+mtime) of `memory/river_brain.pkl` and
`memory/task_type_classifier.pkl` before and after every trial — exists to catch a violation of this
assumption directly, rather than trusting it from prior audits alone. **If either fingerprint ever
changes across a trial in this design, that is itself a surprising finding requiring investigation
before any other result from that trial is trusted** (it would mean the responder path is not as
clean as three prior investigations have concluded).

## Why no condition tests RiverBrain/routing directly

Per the P2 autopsy's own explicit conclusion (carried forward, not re-derived): RiverBrain's only
confirmed causal lever is multi-model council selection, which `EchoDirectResponder`'s single-model
design never invokes. This design inherits that same architecturally-forced exclusion — L1b (routing)
is not a condition this design tests for, because doing so would require reopening the exact
RiverBrain/logging contamination every experiment in this project has deliberately avoided. This is
stated here explicitly so a reader of this design does not mistake the absence of a routing-focused
condition for an oversight.

## Self-edit / shadow_model / reflection_shard: explicitly out of scope for this design

Per the causal autopsy's mechanism inventory, the self-edit deploy pipeline's reach into ordinary
conversation is confirmed narrow (recursive `apply_to_code` effects, or cosmetic never-invoked
tool-name text) and `reflection_shard.py`'s journal is confirmed hollow (zero external readers). Since
neither has any confirmed path into a conversational response's content, neither is a plausible
channel for this design's target (L2 in ordinary conversation) and neither is instrumented here.
