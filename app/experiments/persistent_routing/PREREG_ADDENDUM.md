# Addendum to `audits/2026-09-22_preregistered_persistent_routing_experiment_design.md`

**Resolves that document's §22 "Remaining blockers" 1, 2, and 4. Frozen
before any real generation call. Does not alter that document's own text —
this is an additive companion, matching this whole project's own
"correction, not silent edit" discipline.**

## Blocker 4 (resolved first, per that document's own Q3: "the smallest
missing prerequisite")

`_ollama_query()`'s circuit breaker (`app/core/echo_model_orchestrator.py:1277`,
`_cb_state`) is confirmed, by direct source read, to be:
- A plain, module-level, in-memory Python dict — no file I/O anywhere in
  `_cb_record_failure()`/`_cb_record_success()`/`_cb_is_open()`.
- Therefore genuinely per-process: a fresh process gets an empty
  `_cb_state = {}` on import, resolving the §11 restart-boundary
  interaction exactly as that document's own "probably fine" guess
  anticipated, now confirmed rather than assumed.
- Keyed by `(model_name, task_type)`.

**Residual risk, real but narrow, and closed here**: within a single
process, if two different arms happened to share the same `task_type`
string, one arm's real failures could trip the breaker and degrade a
later arm's calls in that same process. Closed by two independent
measures: (1) this experiment uses its own dedicated `task_type` key,
`"persistent_routing_experiment"`, never used anywhere else in this
codebase (confirmed by grep before adopting it); (2) per §13's own design,
each phase already runs as its own fresh process, which independently
resets `_cb_state` regardless.

**Verdict: EXCLUDED, not merely UNKNOWN.** The channel is real but cannot
contaminate this experiment given the above two measures.

## Blocker 1: strategy menu content

Three strategies, each a fixed prompt template calling `_ollama_query()`
directly (never `generate_code_from_plan()`/`deliberate_and_learn()`),
identical model/options across all three, differing only in *how* the
task is framed:

- **DIRECT**: task spec + signature, asked for immediately, no scaffolding.
- **STEPWISE**: asked to first restate the requirement as an explicit
  numbered list, then write the function — a real, distinct
  prompting shape (chain-of-thought-adjacent), not a reword of DIRECT.
- **WORKED-EXAMPLE**: given one small, genuinely generic worked example
  (unrelated to any real task content, fixed across all tasks) showing the
  *shape* of a solution before being asked for the real one.

These are a real, meaningfully different menu, not three parphrases of
the same prompt — chosen because a plausible, falsifiable hypothesis
exists for why they might differ by task shape (STEPWISE plausibly helps
more on compound-logic tasks; WORKED-EXAMPLE plausibly helps most when the
input shape itself is unfamiliar, i.e. the S-split's whole reason for
existing). This is a real prediction, stated before any data exists, not
invented post hoc to explain a result.

**The real convention/procedure text is supplied directly in every
prompt, for every strategy, identically** (mirroring AP-0's own GOLD arm
exactly) — this experiment tests *routing among prompting strategies for
a task whose solving information is already given*, deliberately
decoupled from the already-separately-tested (and already negatively
resolved, twice: QUAL-1, QUAL-2) question of whether a model can *induce*
that information from raw episodes. Conflating the two would contaminate
a settled question into an open one.

## Blocker 2: selector architecture

**Lookup table**, per the source document's own recommendation for this
minimal rung (§20, §21). State shape:
`{feature_signature: {strategy_name: {"count": int, "mean": float}}}`,
updated by a plain incremental mean (no windowing — sample sizes here are
small enough that a windowed EMA would add complexity without benefit,
unlike RiverBrain's own long-lived, high-volume case).

**Feature signature**, derived only from rendered prompt surface text,
never from internal `kind`/`split` labels (verified by construction,
checked again at implementation time by grepping the extractor's own
inputs):
- `arg_count_bucket` ∈ {`"1"`, `"2"`, `"3+"`}, parsed from the function
  signature string.
- `input_shape` ∈ {`"dict"`, `"tuple"`, `"string"`, `"other"`}, from
  keyword presence in the spec text (`"dict"`/`"dicts"` → dict;
  `"tuple"`/`"tuples"` → tuple; `"text"`/`"string"` → string).

A small, discrete 3×4 signature space, appropriate for a lookup table,
never touching the T/S/NEAR/UNREL split label the selector must not have
access to (per the source document's own §6 requirement).

**Selection rule**: during the PROSPECTIVE phase, epsilon-greedy
(`epsilon = 0.2`, fixed, frozen) — pick the highest-mean strategy for the
observed feature signature with probability `1 - epsilon`, otherwise pick
uniformly among all three, so the lookup table actually accumulates
observations across all three strategies rather than only ever
reinforcing whichever strategy happened to win first. During HOLDOUT,
**pure greedy, no exploration** — matching the source document's own §14
requirement that the holdout phase measures the policy's actual
performance, not further learning. An unobserved feature signature
(`count == 0` for every strategy) falls back to `DIRECT` as the fixed
default, identically across every arm.

## Fixed constants (frozen here, before any generation call)

```
TASK_TYPE_KEY = "persistent_routing_experiment"   # dedicated circuit-breaker key
SEED_OFFSET = 90000                                # confirmed disjoint from every
                                                    # prior offset in this codebase
                                                    # (0, 100, 5000, 5100, 7000, 40000)
EPSILON = 0.2
DEFAULT_STRATEGY = "DIRECT"
MODEL = "qwen2.5-coder:7b"                         # same model as every prior
                                                    # experiment this session, for
                                                    # direct comparability
OPTIONS = {"temperature": 0.2, "top_p": 1.0, "num_predict": 512, "num_ctx": 4096}
```
