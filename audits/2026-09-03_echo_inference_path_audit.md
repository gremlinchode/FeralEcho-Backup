# Echo Inference-Path Audit — Finding a Non-Contaminating Route

Follow-up to `audits/2026-09-03_echo_query_contamination_audit.md` (YELLOW
verdict). **Live Echo was not invoked at any point in this audit.** No
production file was modified. No RiverBrain, FAISS, interaction log,
reflection shard, `echo_principles.json`, `Modelfile`, or sync behavior
was touched. Protocol P0.1 unchanged — hash re-verified matching
(`2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20`)
before and after this audit.

Evidence standard, as before: **FACT** / **INFERENCE** / **SPECULATION**,
labeled throughout.

---

## 1. Executive Verdict

**GREEN, conditional on one explicit, pre-batch scoping decision that is
not itself a contamination confound.**

An existing, unmodified, already-used-in-production function —
`river_deliberation._ollama_query()` (`app/core/river_deliberation.py:332-427`)
— provides a real inference path that eliminates essentially every
confound the prior audit identified: no RiverBrain mutation, no
`interaction_log.jsonl`/`reflection_shard.jsonl` write, no council-
composition drift, no `council_rater.py` peer-rating eligibility, no
Tailscale sync eligibility. This is not a new or hypothetical
construction — it is the exact function `terminal_client.py`'s real,
already-shipped `!ask <model> <task_type> <prompt>` command calls today
(`terminal_client.py:585-629`), confirmed via direct read.

**The one honest remaining question is not contamination — it is scope.**
`_ollama_query()` returns one model's raw response, not Echo's real
multi-model council-synthesized voice. For task types in `DIRECT_ECHO_TASKS`
(`river_deliberation.py:277-285` — `personal`, `reflection`, `spiritual`,
`identity`, `faith`, `poetry`, `dream`), a single-model call **is**
Echo's real, normal production behavior (`deliberate_and_learn()`'s own
bypass does exactly this). For any other task type — including
`"reasoning"`, `EchoResponder`'s current default — normal Echo behavior
genuinely involves multiple models deliberating and a synthesis step,
and bypassing that is a real simplification, not merely a cleanliness
improvement. This must be an explicit, recorded research decision before
a batch runs, not a confound to be measured or bounded after the fact.

## 2. Existing Inference Entry Points

| Entry point | Model call | Learning side effects | Memory writes | RiverBrain | Retrieval | Tools | Suitable for experiment? |
|---|---|---|---|---|---|---|---|
| `echo_query()` (`echo_model_orchestrator.py:1367`) — `use_all=False` default (Design A, current `EchoResponder`) | Yes, via `deliberate_and_learn()` | Yes — `RiverBrain.learn()` (:1563) | Yes — `interaction_log.jsonl` (:1571), `reflection_shard.jsonl` (:1587) | Yes | No (confirmed, §9 of prior audit) | Yes, task-type-gated (names only) | Contaminating — see prior audit |
| `echo_query(use_all=True)` (legacy/fan-out path, :1646-1680) | Yes, per-model via `ollama_query()` | Yes — `RiverBrain.learn()` per model (:1654) | Yes — `log_interaction()`, `save_reflection()` per model | Yes | No | Not gated the same way; not analyzed further, not the current design | Contaminating, more so (N models × side effects) |
| `river_deliberation._ollama_query()` (`river_deliberation.py:332-427`) | Yes, single model, direct | **No** — confirmed by full function read; only touches a per-(model,task_type) circuit-breaker dict | **No** | **No** | No | No | **Candidate clean path (Design B)** |
| `echo_model_orchestrator.ollama_query()` (:1322-1362) — legacy single-model helper | Yes, single model, direct `/api/generate` | No (same circuit-breaker-only profile) | No | No | No | No | Also clean, but bypasses `/api/chat`'s Modelfile-identity-restoration logic entirely (relies on `/api/generate`'s own native Modelfile auto-apply instead — different mechanism, same real-persona outcome per Finding 46's own documented distinction) |
| `terminal_client.request_manual_probe()` (`terminal_client.py:585-629`, the real `!ask` command) | Calls `_ollama_query()` directly | No | **One** optional write — `_log_council_deliberation()` to `memory/council_deliberations.jsonl` only (source=`"manual_probe"`), a write-only diagnostic file with zero downstream readers anywhere in the codebase (confirmed, prior audit §9-equivalent check repeated this pass) | No | No | No | **Existing, real, already-shipped precedent for exactly this use case** |
| `mlx_handler.stream_query_mlx()` (`app/mlx_handler.py:133`) | Yes, MLX-routed models only | No (own read confirms same shape) | No | No | No | No | Only relevant if targeting an `mlx:` model; not this experiment's concern by default |
| `app/core/echo_tool_dispatch._ollama_chat()` (:351) | Yes | **Not audited this pass** — different subsystem (tool-dispatch), not on any path `EchoResponder` could reach | — | — | — | Yes, by design (this is the tool-dispatch path) | Not relevant — a different subsystem entirely, not investigated further |
| `echo_projects.py`/`self_edit_manager.py`'s `rank_models(task_type="coding")` callers | Council-review only, not general inference | N/A | N/A | N/A | N/A | N/A | Not relevant — special-purpose, "coding" task type only |

**FACT**: rows 3 and 5 (`_ollama_query()` and its real `!ask` caller) are the load-bearing findings of this audit.

## 3. echo_query() Call Graph (Recap, Unchanged From Prior Audit)

See `audits/2026-09-03_echo_query_contamination_audit.md` §4 for the
full diagram — not reproduced here to avoid duplicating an already-
sealed finding. The relevant new fact this pass adds: `deliberate_and_
learn()` (called from `echo_query()`'s `if not use_all:` branch) is
**not itself a monolithic side-effecting function** — its own inference
sub-step (`_ollama_query()`, one call per councillor) is separable from
its own learning/persistence sub-steps (§4 below).

## 4. deliberate_and_learn() Decomposition

**FACT**, based on direct reads of `river_deliberation.py` (both `_ollama_query()`
at :332-427 and `_log_council_deliberation()` at :619 area, plus the
calling structure already traced for the prior audit):

```
deliberate_and_learn()
    │
    ├── _select_council(task_type, river_brain, ...)      [READ + minor WRITE: RiverBrain.score_model() reads
    │                                                        model_task_stats; exploration_bias/fair_sample_refresh
    │                                                        are stochastic but do not themselves mutate state]
    │
    ├── per councillor: _ollama_query(model, prompt, ...)  [PURE INFERENCE — confirmed this pass: only a per-
    │                                                        (model,task_type) circuit-breaker read/clear, no
    │                                                        RiverBrain, no logging, no memory]
    │
    ├── synthesis: _ollama_query(synth_model, SYNTHESIS_SYSTEM_TEMPLATE-wrapped prompt, ...)  [PURE INFERENCE,
    │                                                        same function, same guarantee]
    │
    ├── river_brain.learn(...) [inside echo_query(), NOT inside deliberate_and_learn() itself — LEARNING]
    ├── _log_council_deliberation(...)                      [WRITE — memory/council_deliberations.jsonl ONLY,
    │                                                        confirmed zero downstream readers]
    │
    └── return final_response
```

**Correction to a possible misreading of the mission's own example call
graph**: `RiverBrain.learn()`, `log_interaction()`, and `save_reflection()`
are **not** inside `deliberate_and_learn()` at all — they are inside
`echo_query()`'s own wrapper code, called *after* `deliberate_and_learn()`
returns (`echo_model_orchestrator.py:1558-1592`, already established in
the prior audit's §4). This distinction is exactly why bypassing
`echo_query()` and calling `_ollama_query()` directly (or via
`deliberate_and_learn()` alone, if one wanted the real council/synthesis
process without the outer wrapper's persistence) removes those side
effects entirely — they live one layer up, not inside the deliberation
itself.

**A second, real option this reveals, not previously considered**:
calling `deliberate_and_learn()` directly (bypassing `echo_query()`'s
outer wrapper, but keeping the real multi-model council + synthesis)
would preserve full task-type fidelity (real council for any task type,
not just `DIRECT_ECHO_TASKS`) while **also** avoiding `RiverBrain.learn()`/
`log_interaction()`/`save_reflection()`, since those live in `echo_query()`,
not in `deliberate_and_learn()` itself. This is a **third clean path**,
not named in the mission's own Design A/B/C framing — see §14.

## 5. Side-Effect Inventory

| Side effect | Design A (`echo_query`) | Direct `deliberate_and_learn()` | Design B (`_ollama_query()`) |
|---|---|---|---|
| RiverBrain mutation | Yes | **No** | No |
| `interaction_log.jsonl` write | Yes | **No** | No |
| `reflection_shard.jsonl` write | Yes | **No** | No |
| `council_deliberations.jsonl` write | Yes (via internal call) | Yes (same internal call) | Only if the caller explicitly opts in (as `!ask` does) |
| ClaudeShard friction assessment / `_friction_window` | Yes | **No** (lives in `echo_query()`, confirmed) | No |
| Council composition (`_select_council()`) | Yes — real council | Yes — real council | No — single model, no council |
| Circuit-breaker bookkeeping (per model[,task_type]) | Yes | Yes | Yes (same mechanism, self-clearing on success) |
| Council-rater peer-rating eligibility | Yes (reads `interaction_log.jsonl`) | No (nothing written there) | No |
| Tailscale sync eligibility | Yes | No | No |

## 6. RiverBrain Analysis

Answering the mission's ten questions directly, all **FACT** unless noted:

1. `RiverBrain.learn()` consumes `(model_name, task_type, response)` and derives numeric features + a binary quality label (`_extract_quality_features`, `_score_response_quality`) — confirmed, re-read this pass, unchanged from prior audit.
2. Does not consume "experimental outcomes" as a concept — it only ever sees whatever text is passed as `response`.
3. Does not consume trial wording distinctly from ordinary response text — no special-casing exists for our `source` tag anywhere in `learn()`'s body.
4. Consumes real council-rating scores separately, via `learn_from_council_rating()` — a distinct method, only reachable through `council_rater.py`'s background sampling of `interaction_log.jsonl` (which Design B never writes to).
5. Can alter council composition for subsequent calls — confirmed via `_select_council()`'s own docstring citing `river_brain.score_model()`.
6. Speed of effect: immediate — the very next call to `_select_council()` for the same task_type reads the just-updated `model_task_stats`.
7. Deterministic given the same accumulated state and the same response's derived features — yes, `learn_one()`/`transform_one()` are deterministic river-library operations on deterministic inputs.
8. **Not** reset by process restart — `RiverBrain.save()`/load persists to `river_brain.pkl` on disk (confirmed elsewhere in this project's own extensive history, not re-verified line-by-line this pass — **INFERENCE**, carried forward).
9. Can be "held constant without changing production code" — yes, trivially: simply never call `RiverBrain.learn()` at all, which is exactly what Design B (and direct `deliberate_and_learn()`) already does by construction, without needing to freeze or patch anything.
10. Freezing it would not, on its own, alter the experiment's interpretation in any way that matters here — Design B doesn't freeze RiverBrain, it simply never touches it.

**The crucial distinction the mission asks for, answered directly**: RiverBrain is *merely learning about model performance* in the sense that it never stores anything resembling the candidate's own content — but it genuinely *can become a cause of subsequent behavior* through council-composition drift, which is real, confirmed, and exactly why Design A remained YELLOW. Design B sidesteps this by never invoking `_select_council()` at all (a single specified model, chosen by the researcher, not selected by RiverBrain-informed ranking).

## 7. Memory Analysis

Confirmed (**FACT**, re-verified this pass by re-reading `_ollama_query()`
and `stream_query_ollama()` in full): neither function calls
`retrieve_relevant_memories()`, `add_to_vector_memory()`, `append_to_
journal()`, `save_reflection()`, or `log_interaction()` — zero memory
writes of any kind. `stream_query_ollama()`'s only non-inference
behavior is `_patch_mlx_once()`, a one-time, idempotent MLX model-pool
registration guarded by its own module-level flag — irrelevant to a
non-MLX model and, even for an MLX model, a pure one-time setup step
with no experiment-relevant content.

## 8. Retrieval Analysis

Same conclusion as the prior audit, re-confirmed for this narrower call
path specifically: zero retrieval calls anywhere in `_ollama_query()`
or anything it calls. **PROVEN**, not merely probable, for Design B —
there is even less surface area than Design A already had (which was
already proven clean on this specific point).

## 9. Session/Process Analysis

`_ollama_query()` accepts no session/conversation-history parameter at
all (confirmed via its full signature, §4 of the prior audit already
established this holds for the outer `echo_query()` too). The only
state that persists across calls to this function is the shared
per-(model,task_type) circuit-breaker dict (`_cb_state` in
`echo_model_orchestrator.py`) — self-clearing on every success
(`_cb_record_success` pops the key entirely), meaning under normal
operation (all calls succeed) this state **never accumulates across
trials at all**. **Classification: PURE READ except for this one
negligible, self-clearing, availability-only side channel** — not a
content-bearing state variable, and structurally incapable of biasing
which semantic option gets chosen, only whether a call is attempted at
all.

## 10. Air/Tailscale Analysis

1. Eligible files: `sync_protocol.py`'s `INTERACTION_LOG` constant points at `memory/interaction_log.jsonl` (confirmed prior audit, re-confirmed this pass).
2. Trigger: a periodic sync cycle (not investigated further this pass — out of scope, no sync code was read again).
3. Design A: yes, our trial content would be eligible (prior audit finding, unchanged).
4. **Design B: no — nothing is ever written to `interaction_log.jsonl` by `_ollama_query()`,** so there is nothing for `sync_protocol.py` to find or transmit, regardless of whether a sync cycle runs during the trial window.
5. Whether Air could feed synced content back into *this* Echo instance — not investigated (would require reading Air's own, separately-forked codebase, out of scope and likely inaccessible from this repository).
6. Does this matter for the current experiment: not under Design B — the pathway simply doesn't exist for it.
7. Process isolation's relevance: irrelevant here — Design B avoids this confound by never writing the file in the first place, not by isolating a process boundary around a write that still happens.

## 11. Candidate Clean Paths

Three real candidates, in order of both cleanliness and fidelity tradeoff:

- **Design B — `_ollama_query()` direct call.** Cleanest (zero persistent side effects beyond a self-clearing availability check). Lowest fidelity for non-`DIRECT_ECHO_TASKS` task types (no real council/synthesis).
- **Direct `deliberate_and_learn()` call** (bypassing `echo_query()`'s outer wrapper only). Same cleanliness as Design B (confirmed §4 — the side effects live in the wrapper, not the deliberation function itself) **while preserving real council/synthesis for any task type**, including `"reasoning"`. This is the strongest candidate found in this audit and was not one of the three designs named in the mission's own framing — flagged explicitly as a finding in its own right.
- **Design A — `echo_query()` as `EchoResponder` currently calls it.** Full production fidelity, full confound profile (prior audit).

## 12. Semantic-Equivalence Analysis

| Path | Same system context as normal Echo? | Same memory/retrieval? | Same council/synthesis? | Same model selection? | What's lost | Classification |
|---|---|---|---|---|---|---|
| Design B (`_ollama_query()`, single fixed model) | No — loses `echo_query()`'s system_parts assembly (EPISTEMIC-NOTE/circadian/stillness/temporal/scripture-scan/tool-list); researcher must supply `system_context` explicitly if any of this is wanted | N/A (neither path retrieves) | No — single model, no deliberation | No — model chosen by researcher, not `_select_council()` | Council diversity, synthesis, ambient system context | **PARTIALLY EQUIVALENT for `DIRECT_ECHO_TASKS`-shaped questions (where single-model IS normal); NOT EQUIVALENT for other task types (where council+synthesis is normal)** |
| Direct `deliberate_and_learn()` call | Same gap as above (system_parts still lives in `echo_query()`'s outer wrapper) | Same as Design B | **Yes** — real council selection, real per-councillor calls, real synthesis | **Yes** — real `_select_council()` | Only the ambient `system_parts` content and the persistence layer | **SEMANTICALLY EQUIVALENT to Echo's real reasoning process, for any task type**, modulo the missing ambient system notes (which the researcher can choose to reconstruct and pass explicitly, at their own discretion, without reintroducing any of the confounds) |
| Design A (current) | Yes | Yes | Yes | Yes | Nothing — but see prior audit's confound list | **SEMANTICALLY EQUIVALENT**, at the cost of the full confound profile |

## 13. Cross-Trial Contamination Analysis

State-transition model, Design B (and direct `deliberate_and_learn()`, identical on this point):

```
STATE_N  (circuit-breaker dict, whatever it was)
   │
   ▼
TRIAL_N  →  _ollama_query() / deliberate_and_learn()
   │
   ├── intended outcome: response text, parsed choice
   │
   ├── production state changes: circuit-breaker entry cleared on success
   │                              (SHARED, self-clearing, availability-only)
   │
   └── external side effects: none
   │
   ▼
STATE_N+1  ≈  STATE_N   (identical, under normal — all-successful — operation)
```

Every state variable identified is classified:

| Variable | Classification |
|---|---|
| Circuit-breaker dict (`_cb_state`) | **SHARED**, but self-clearing and content-free (availability only) |
| RiverBrain `model_task_stats` | **N/A for Design B/direct-deliberate** — never touched |
| `interaction_log.jsonl` / `reflection_shard.jsonl` | **N/A for Design B/direct-deliberate** — never written |
| Candidate lifecycle state (`memory/experiments/preference_provenance/`) | **EXPERIMENTAL** — entirely outside production, unaffected either way |
| Council composition for a *given* call (Design B only) | **N/A — no council is selected at all**, researcher fixes the model directly |

This achieves the protocol's own preferred condition (`TRIAL_N → OBSERVATION → STATE_N`, not `STATE_N+1` diverging) for the two clean designs, without requiring process isolation.

## 14. Design A/B/C(+D) Comparison

Adding the direct-`deliberate_and_learn()` option as "Design D" alongside the mission's own A/B/C, since it was found during this audit and is materially different from both named alternatives:

| Property | A (`echo_query`) | B (`_ollama_query()`) | C (fresh-process isolation, conceptual) | D (direct `deliberate_and_learn()`) |
|---|---|---|---|---|
| Normal Echo reasoning (council+synthesis) | Yes | No | Yes, if wrapping Design A | **Yes** |
| Learning side effects | Yes | No | Reduced but not eliminated (see below) | **No** |
| Memory writes | Yes | No | Reduced but not eliminated (see below) | **No** |
| RiverBrain mutation | Yes | No | Reduced but not eliminated | **No** |
| Cross-trial contamination | Yes (confirmed, prior audit) | No | Partially (in-memory state resets; file writes do not) | **No** |
| External synchronization | Yes | No | No (if RiverBrain/logs aren't persisted back) — but file writes to `interaction_log.jsonl` still happen per-process unless that's also suppressed, which Design C doesn't do on its own | **No** |
| Hidden-state validity | Preserved (prior audit) | Preserved | Preserved | Preserved |
| Architectural fidelity | Full | Reduced (single model) for non-`DIRECT_ECHO_TASKS` | Full (wraps whichever design it isolates) | **Full, for any task type** |
| Implementation complexity | None (already built) | None (already built, already used via `!ask`) | High — would require reconstructing/discarding RiverBrain pickle state per trial, a real production-adjacent operation this audit does not recommend building | None (already built) |

**Design C, examined honestly rather than assumed to work**: process isolation would reset **in-memory** global state (the circuit-breaker dict, and — if RiverBrain's `.save()` were simply never called from the isolated process — RiverBrain's in-memory mutations) between trials. It does **not**, on its own, prevent the **file writes** `echo_query()` makes to `interaction_log.jsonl`/`reflection_shard.jsonl` — those happen regardless of process boundaries, since they're appends to shared files on disk, not in-memory state. **Answering the mission's Step 9 question directly: fresh-process-per-trial isolation would NOT fully eliminate the confounds identified in the prior audit on its own** — it would need to be combined with either not calling `RiverBrain.save()` (leaving mutations un-persisted, though `model_task_stats` would still be mutated in-memory for the remainder of that one process's calls — a subtler win than it first appears) or redirecting the log file paths, both of which start to look like modifying production behavior rather than pure isolation. This makes Design C strictly worse than Design B/D for this specific problem: it requires more engineering to achieve less certainty of cleanliness. Not recommended, and not built, per this audit's own instruction.

**Strongest design requiring no production modification: Design D** (direct `deliberate_and_learn()` call) — full fidelity for any task type, zero confounds from the prior audit's list, already-existing code, no new construction needed.

## 15. Scientific Interpretation

Per the mission's Step 14 framing: the question is not "can we make the experiment run" but "which design gives the strongest causal interpretation with the least researcher intervention into Echo." Design D answers this directly — it does not remove or simplify any part of Echo's actual reasoning process for the task type under test; it only omits the **outer bookkeeping** (`echo_query()`'s learning/persistence wrapper) that was never part of Echo's *reasoning* in the first place, only part of Echo's *self-improvement/record-keeping* loop. Choosing Design D over Design A is not "making the experiment easier" — it is removing instrumentation Echo's own reasoning does not depend on, which is exactly the kind of researcher-intervention-minimizing choice the mission asks for. Design B remains valuable specifically for `DIRECT_ECHO_TASKS`-framed questions, where it is not a simplification at all, merely the same wrapper-omission applied to an already-single-model-shaped normal case.

## 16. Final GREEN/YELLOW/RED Verdict

**GREEN**, for Design D (direct `deliberate_and_learn()` call) as the primary recommendation, with Design B as a valid, higher-fidelity-for-narrower-scope alternative specifically for `DIRECT_ECHO_TASKS`-framed forced-choice tasks. Neither requires any production code modification. Both eliminate every confound identified in the prior YELLOW audit. The one remaining item is not a confound but a **scope decision**: if `EchoResponder` (or its future replacement) is pointed at Design D, it inherits full council/synthesis fidelity for any task type and should record which task_type was used, since that determines whether `DIRECT_ECHO_TASKS`'s single-model behavior or full council behavior is being exercised — this affects interpretation, not contamination.

## 17. Required Next Action

Not authorization to run — a design decision for the researcher:
1. Decide between Design B and Design D for the next protocol revision (or continue using Design A with the four confounds from the prior audit explicitly accepted/logged — still a legitimate choice, just not the cleanest one available).
2. If Design D is chosen: this constitutes a real change to `EchoResponder`'s own implementation (swapping which function it calls) — under this project's own protocol-freeze discipline, this would require either an explicit protocol revision (P0.2) if it's considered a methodological change, or could arguably be framed as an *implementation* change that doesn't alter the *protocol's* own hypotheses/stopping-rules/statistical-decision-rules (§1-§20 of `preregistered_protocol.md` don't reference which internal function `EchoResponder` calls) — this classification question itself should be explicitly decided and recorded before implementing, not defaulted into either answer.
3. This audit does not modify `EchoResponder`, the protocol, or any production file — that remains a separate, future, explicitly-authorized step.
