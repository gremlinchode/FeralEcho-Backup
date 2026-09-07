# FeralEcho — Seed Variation Instrument Validation

Instrument validation only. Not a learning experiment. Does not test the lesson, does not touch
v1.2's CONTROL-vs-EXPERIENCE comparison. Read-only with respect to production.

## 1. Objective

Determine whether the real Ollama generation path FeralEcho's experiments depend on can produce
seed-dependent output variation at all — closing the open question v1.2.1 left unresolved (identical
CONTROL output could mean "no lesson effect" or "the instrument can't show variation regardless").

## 2. Prior v1.2/v1.2.1 findings

v1.2: CONTROL and EXPERIENCE produced byte-identical code and identical runtime failure once
historical-context contamination was removed — verdict RED. v1.2.1: two independent CONTROL-only
`echo_query()` calls (full RiverBrain/council/synthesis pipeline) also produced byte-identical raw
responses; traced to frozen RiverBrain state (deterministic council selection) + seat-position-fixed
temperature + confirmed absence of any `seed` parameter anywhere in the real Ollama call path — verdict
DIAGNOSTIC NEGATIVE.

## 3. Environment verification

Before: `run.py` not running, watchdog not running, port 5000 unbound, Ollama reachable (9 real models:
`echo:latest`, `gemma3:4b`, `qwen2.5-coder:7b`, `deepseek-r1:7b`, `qwen2.5:3b`, `llama3.2:3b`,
`llama3.1:8b`, `llama3:instruct`, `mistral:latest`). `memory/river_brain.pkl` baseline: size 3720782
bytes, mtime `Sep 6 16:24`, sha256 `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`.
After: `run.py` still not running (re-checked), `river_brain.pkl` byte-identical (same size, same
mtime, same sha256, re-hashed directly). Confirmed by this pass, not inherited.

## 4. Exact Ollama call path

`app/ollama_handler.py`'s `_chat_ollama()`/`_stream_chat_ollama()` (lines ~125-186) POST to
`CHAT_URL = "http://localhost:11434/api/chat"`. Confirmed directly by source read: the `options` dict
built at both call sites sets only `num_ctx`, `num_predict`, and (when given) `temperature` — no `seed`
key is added anywhere in this file. This matches the parent session's own pre-confirmed fact exactly.

## 5. Request construction

Real payload shape: `{"model": ..., "messages": [...], "stream": bool, "options": {...}}`. The isolated
harness (`app/experiments/first_learning_loop/seed_validation.py`, new, this pass) constructs the
identical shape, adding one key: `"seed": <int>` inside `options`.

## 6. Whether seed was previously absent

Confirmed absent (§4) — not inferred, read directly from source before writing any test code, per the
mission's own §3 instruction not to assume.

## 7. Experimental harness

New, isolated file: `app/experiments/first_learning_loop/seed_validation.py`. Does not modify
`ollama_handler.py`, `river_deliberation.py`, or any production file. Calls the real Ollama `/api/chat`
endpoint directly via `requests.post`, bypassing `echo_query()`'s full RiverBrain/council/synthesis
chain entirely (disclosed limitation, §22). Never imports or calls `RiverBrain`, `learn()`,
`learn_from_sandbox_outcome()`, `execute_self_edit()`, or any rating/model-selection state.

## 8. Exact model

`echo:latest` — the real, live, default synthesis model this project's own `ECHO_SYNTHESIS_MODEL`
constant names, chosen so results are representative of the model most real FeralEcho generation
ultimately involves.

## 9. Exact parameters

`temperature=0.7`, `num_ctx=8192`, `num_predict=300` (baseline) / unmodified `BASE_PROMPT`-length
default (clean-task test). Seed values: A=4242, B=90210 (arbitrary, fixed before any generation ran).

## 10. Exact prompt

Baseline: *"Write a short Python function that returns the nth Fibonacci number. Include a brief
one-line comment above the return statement. Output only the function as a single code block."* — generic,
no FeralEcho/Echo/learning/historical-identifier content. Clean-task test: the real, unmodified
`v1_2_clean_transfer.BASE_PROMPT` (imported directly from that module, not retyped, guaranteeing exact
reuse).

## 11-13. SEED-A / SEED-B / SEED-A-REPEAT raw responses

Persisted in full, each to its own file:
- `app/experiments/first_learning_loop/seed_validation_artifacts/seed_a_response.json`
- `app/experiments/first_learning_loop/seed_validation_artifacts/seed_b_response.json`
- `app/experiments/first_learning_loop/seed_validation_artifacts/seed_a_repeat_response.json`

Each file contains the exact prompt, seed, model, temperature, full raw response text, elapsed time,
and any non-message metadata Ollama returned.

## 14. Hashes (sha256 of raw response text, computed directly, this pass)

```
seed_a_response:        9f697f59f3bb943ad6b6375f204974819791538740c4792e7168412bfcf44f2a
seed_b_response:        91a46ebf4785585a0ca404df589913fc685c5c0f3a65b6e78f82476b241f4656
seed_a_repeat_response: 9f697f59f3bb943ad6b6375f204974819791538740c4792e7168412bfcf44f2a
```

## 15. Byte comparison

`seed_a == seed_b`: **False**. `seed_a == seed_a_repeat`: **True**. Confirmed by direct sha256
comparison of the persisted files, not eyeballed.

## 16. Structural comparison

Clean-task test (§21) shows genuine structural difference, not just whitespace: SEED-A's candidate
attempts `from trace_recorder import trace_recorder`; SEED-B's attempts `from event_tracker import
trace_recorder` — two different, independently-guessed (and both incorrect) import sources. This is
real content divergence, not cosmetic formatting variation.

## 17. Semantic comparison

Both clean-task candidates represent the same general strategy (import-based resolution of the
undefined name) but diverge on the specific guessed source module — a real, meaningful difference in
the actual generated solution, not a trivial one. Full functional/correctness evaluation of these
candidates is explicitly out of scope (Q3, excluded by the mission).

## 18. Evidence that seed reached Ollama

`SEED-A == SEED-A-REPEAT` (byte-identical, same seed) while `SEED-A != SEED-B` (different seed) is
direct, empirical evidence the `seed` field is read and honored by the real Ollama backend for this
model — reproducible determinism under a fixed seed, real variation under a different one. This is the
expected diagnostic pattern the mission's own §6 specifies, and it was measured, not assumed.

## 19. Evidence that seed affected generation

Same as §18 — the byte-level and structural differences between SEED-A and SEED-B on both the baseline
and the real clean-task prompt directly demonstrate the seed value materially affects the sampled
output, not merely some inert request field.

## 20. Evidence for repeatability

`SEED-A == SEED-A-REPEAT`, confirmed by exact hash match. No backend nondeterminism observed under a
fixed seed in this pass (n=1 repeat — a larger repeat count would strengthen this further but was not
required by the mission's own scope).

## 21. Clean-v1.2-task seed comparison

Reached. `clean_control_seed_a` sha256 `472d1ffd...`, `clean_control_seed_b` sha256 `928bc55d...` —
**different**. Confirms the real v1.2 task content itself, not just a generic prompt, is capable of
producing seed-dependent variation under a direct, single-model call.

## 22. Limitations

**The single most important limitation, stated plainly**: this validates Q1 (Ollama supports seed) and
a narrower version of Q2 (the same request shape, called directly with a seed added, transmits and
honors it — including on the real v1.2 task's exact prompt content) — but it does **not** validate that
`echo_query()`'s real, full production generation path (RiverBrain-driven model/council selection →
multi-councillor deliberation → synthesis/fallback) can be made to vary, because that path has no seed
parameter anywhere in it and adding one would require modifying production code, explicitly out of
scope for this pass. v1.2.1's own diagnosis (frozen RiverBrain → deterministic council selection +
fixed per-seat temperature) remains a separate, real, additional source of determinism specific to the
full pipeline that this isolated single-model test does not by itself resolve. Only n=1 repeat was
tested for §20; only one model (`echo:latest`) was tested — not the specific councillors v1.2's own
fallback-selection actually drew from.

## 23. Implications for v1.2

v1.2's RED verdict is unaffected — this pass doesn't touch that comparison. What changes: v1.2.1's own
open question ("is the instrument capable of variation at all") is now answered **partially yes** — a
seed-controlled, single-model call on the identical real task content does vary — but the *specific*
mechanism v1.2/v1.2.1 actually used (`echo_query()`'s full pipeline, no seed control, frozen RiverBrain)
remains unvalidated for variation, and per §22, cannot be validated without either a production code
change or a fundamentally different (single-model, not full-council) experimental design.

## 24. Recommended next step

Do not attempt to thread a seed through `echo_query()`'s full pipeline (would require production
changes, out of scope by this mission's own repeated instruction). Instead: design the next learning
experiment (a separate, future decision, not this pass's) around a **single-model, seed-controlled**
generation call — matching this validation harness's own successful shape — rather than the full
multi-councillor `echo_query()` path, since that path has now been shown twice (v1.2.1, and by
inference here) to structurally resist producing independently-sampled CONTROL/EXPERIENCE pairs under
the safety-required frozen-RiverBrain condition.

---

## Verdict

**SEED PARTIALLY VALIDATED.**

Not full SEED VALIDATED: this pass confirms seed variation works, reproducibly, on a direct single-model
call using the real task content — but does not confirm the *actual pipeline v1.2 used* (`echo_query()`'s
full council/synthesis chain) can be made to vary, since that path was never modified or tested with a
seed (out of scope). Not SEED NOT EFFECTIVE — real, structural, hash-confirmed variation was directly
observed and is reproducible. Not INCONCLUSIVE — the evidence obtained is clean and unambiguous for the
narrower question it actually tested.

---

## §17 — The important question at the end

**Can we now construct a learning experiment in which CONTROL and EXPERIENCE are independently sampled,
while all other variables remain controlled?**

**Partially yes, with a changed design, not the original one.** A single-model, direct-call generation
path (bypassing `echo_query()`'s full RiverBrain/council/synthesis chain) — matching exactly what this
validation harness just proved works — can produce genuinely independent CONTROL/EXPERIENCE samples via
different seeds, while holding model/temperature/prompt-minus-lesson fixed. This is a real, concrete,
available path forward.

**What still blocks the original design**: `echo_query()`'s full multi-councillor pipeline — the actual
generation path every prior experiment in this series (v1, v1.1, T4, v1.2) used, in order to stay
faithful to FeralEcho's real production behavior — has no seed parameter anywhere in it, and adding one
would mean modifying `ollama_handler.py`/`river_deliberation.py`, which is a production change requiring
separate authorization, not something this or any prior pass in this series was authorized to do. Any
future learning experiment must explicitly choose between (a) fidelity to the real multi-councillor
pipeline, accepting its current determinism under safety-required frozen RiverBrain state, or (b) a
single-model design that can be seed-controlled but no longer represents FeralEcho's actual real-world
generation behavior. That tradeoff, and which side of it to take, is a design decision for whoever
authorizes the next experiment — not resolved by this validation pass, which only establishes that the
tradeoff is real and that path (b) is technically available.
