# deliberate_and_learn() Differential Audit — Correcting a Prior Claim

**Live Echo was not invoked. No production file, RiverBrain state, memory,
FAISS, log, or the protocol was modified.** Protocol P0.1 hash
re-verified matching (`2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20`)
before and after this pass.

**This audit corrects a real error in its own immediate predecessor**
(`audits/2026-09-03_echo_inference_path_audit.md`), which claimed
`RiverBrain.learn()`, `_log_council_deliberation()`, and related side
effects "live in `echo_query()`'s wrapper, not inside
`deliberate_and_learn()` itself." That claim was **false**, and this
document exists specifically to prove it false from a complete,
line-by-line read of `deliberate_and_learn()` (`app/core/river_deliberation.py:722-1069`,
the entire function to the end of the file) that the prior pass did not
perform — the prior pass inferred this from `echo_query()`'s own
structure and from a partial read of `deliberate_and_learn()`'s helper
functions, without reading `deliberate_and_learn()`'s own body in full.
This is exactly the kind of thing this project's own standing discipline
requires being stated plainly, not glossed over: **"if the audit is
wrong, say so clearly."** It was wrong.

Evidence standard: **FACT** / **INFERENCE** / **SPECULATION**, as before.

---

## 1. Decomposition

### `echo_query()` (`echo_model_orchestrator.py:1367-1630`)

| Operation | Classification |
|---|---|
| `resolve_task_type(prompt)` (unconditional, result discarded when `task_type` given) | CONTEXT CONSTRUCTION (wasted, not harmful) |
| `system_parts` assembly (EPISTEMIC-NOTE, circadian/stillness, temporal, scripture scan, tool-list) | CONTEXT CONSTRUCTION |
| `deliberate_and_learn(...)` call | COUNCIL + INFERENCE + LEARNING + PERSISTENCE (see §2 — **not a single, poolable category**, corrected below) |
| `_score_response_quality(response, task_type)` | POST-PROCESSING (pure, used only to feed the next line) |
| `get_river_brain().learn(ECHO_SYNTHESIS_MODEL, task_type, response)` | LEARNING — **confirmed redundant** with `deliberate_and_learn()`'s own internal learn calls on the main synthesis path (§2) |
| `log_interaction(...)` | PERSISTENCE (`interaction_log.jsonl`) |
| `save_reflection(...)` | PERSISTENCE (`reflection_shard.jsonl`) |
| `get_river_brain().save()` | PERSISTENCE (RiverBrain → disk) |
| `CLAUDE_SHARD.assess(...)` + possible `simulate_self_edit()` | OTHER (friction assessment; dry-run only) |
| `_post_response_audit(...)` | POST-PROCESSING (observational only) |

### `deliberate_and_learn()` (`river_deliberation.py:722-1069`) — corrected

| Operation | Classification |
|---|---|
| `task_type in DIRECT_ECHO_TASKS` branch: `_ollama_query()` call | INFERENCE |
| **`river_brain.learn(synth_model, task_type, response)`** (line 811) | **LEARNING — inside this function** |
| **`_log_council_deliberation(...)`** (lines 819-825) | **PERSISTENCE — `memory/council_deliberations.jsonl`, inside this function** |
| `_warm_up_echo(synth_model)` (line 832) | INFERENCE (a real extra model call, prompt `"."`, no learning/persistence of its own) |
| World-surprise/valence read for `exploration_bias` (lines 849-892) | RETRIEVAL (reads `echo_core.compute_salience()`/`echo_state.load()`/a module-level cache) |
| **`core.publish_salience(...)`** (lines 869-877, conditional on cache freshness) | **PERSISTENCE — `memory/workspace_log.jsonl`, inside this function** |
| `_select_council(...)` | MODEL SELECTION / COUNCIL |
| Empty-council fallback: `_ollama_query()` + **`river_brain.learn(...)`** (lines 897-900) | INFERENCE + **LEARNING** |
| Per-councillor loop: `_ollama_query()` × N | INFERENCE |
| All-errored fallback: `_ollama_query()` + **`river_brain.learn(...)`** (lines 953-956) | INFERENCE + **LEARNING** |
| Solo-Echo shortcut: **`river_brain.learn(...)`** (lines 961-964) | **LEARNING** |
| Synthesis call: `_ollama_query()` | INFERENCE |
| Synthesis-failed fallback: **`river_brain.learn(...)`** (lines 1026-1029) | **LEARNING** |
| **Main path: per-councillor `river_brain.learn(model, task_type, opinion)` for every non-synth model, then `river_brain.learn(synth_model, task_type, final_response)`** (lines 1057-1060) | **LEARNING — the real, primary path's own internal training, six lines before the function returns** |
| **`_log_council_deliberation(...)`** (lines 1062-1069, main path) | **PERSISTENCE — same file as above** |

**Every single return path in `deliberate_and_learn()` calls
`river_brain.learn()` at least once, and the two real (non-degenerate)
paths — the `DIRECT_ECHO_TASKS` bypass and the full council/synthesis
path — both also call `_log_council_deliberation()`.** There is no
return path in this function that avoids both.

## 2. Differential Call Graph

```
echo_query(input)
   │
   ├── resolve_task_type()                    [ONLY IN echo_query — wasted, discarded]
   ├── system_parts assembly                  [ONLY IN echo_query — caller-side context]
   │
   └── deliberate_and_learn(prompt, system=system_parts_joined, ...)
          │
          ├── river_brain.learn(...)  ×1-8 call sites depending on path   [PRESENT IN BOTH —
          │                                                                echo_query() ALSO calls
          │                                                                .learn() again afterward
          │                                                                on the main path — REDUNDANT,
          │                                                                double-counted training signal,
          │                                                                a real, previously undocumented
          │                                                                minor bug]
          ├── _log_council_deliberation()      [ONLY IN deliberate_and_learn() — echo_query()
          │                                      never calls this itself]
          ├── core.publish_salience() (conditional)  [ONLY IN deliberate_and_learn()]
          ├── _warm_up_echo() (extra inference call)  [ONLY IN deliberate_and_learn()]
          ├── _select_council(), per-councillor _ollama_query(), synthesis  [ONLY IN deliberate_and_learn()
          │                                                                   — the actual reasoning]
          │
          └── return response
   │
   ├── _score_response_quality()               [ONLY IN echo_query()]
   ├── get_river_brain().learn(...)  (AGAIN)    [ONLY IN echo_query() — but redundant with the above]
   ├── log_interaction()                        [ONLY IN echo_query()]
   ├── save_reflection()                        [ONLY IN echo_query()]
   ├── get_river_brain().save()                 [ONLY IN echo_query() — persists to disk]
   ├── CLAUDE_SHARD.assess() / Wolf dry-run      [ONLY IN echo_query()]
   └── _post_response_audit()                   [ONLY IN echo_query()]
```

**PRESENT IN BOTH**: `river_brain.learn()` (deliberate_and_learn() internally, echo_query() redundantly again). Nothing else is genuinely shared — everything else is cleanly on one side or the other.
**ONLY IN echo_query()**: task-type resolution (moot), system-context assembly, the second redundant learn() call, `interaction_log.jsonl`, `reflection_shard.jsonl`, `RiverBrain.save()` (disk persistence), ClaudeShard/Wolf-bridge, post-response audit.
**ONLY IN deliberate_and_learn()**: `council_deliberations.jsonl` write, conditional Global Workspace write, the warm-up call, and — obviously — the actual council selection/query/synthesis logic itself.

## 3. Input Differential

`echo_query()` passes `prompt` through to `deliberate_and_learn()` **unmodified** — `prompt` is `deliberate_and_learn()`'s first positional argument, and `echo_query()` never mutates it before the call (**FACT**, confirmed by direct read of both signatures — `echo_query(prompt, ...)` and the call `deliberate_and_learn(prompt=prompt, ...)`). The one real input difference: `system` — `echo_query()` constructs `system_prompt` (the joined `system_parts`, §1) and passes *that* as `deliberate_and_learn()`'s `system` argument; calling `deliberate_and_learn()` directly with no `system` (or a bare, researcher-supplied one) means the model never receives the EPISTEMIC-NOTE/circadian/temporal/scripture/tool-list content. **Experimentally important**: yes, in the sense that it changes what "normal Echo context" looks like, but **not asymmetrically** — omitting it is the same for every trial in a batch, so it does not by itself bias a baseline-vs-treatment comparison. Task type, temperature, and max_tokens pass through identically either way (both are explicit parameters on both functions).

## 4. Output Differential

Everything `echo_query()` does with `deliberate_and_learn()`'s return value (§1's `echo_query`-only rows) is classified:

| Operation | Classification |
|---|---|
| `_score_response_quality()` | INSTRUMENTATION ONLY |
| Second `river_brain.learn()` call | **EXPERIMENTALLY DANGEROUS** (redundant, but still a second real mutation) |
| `log_interaction()` | EXPERIMENTALLY DANGEROUS (feeds `council_rater.py`/`sync_protocol.py`, per the prior contamination audit) |
| `save_reflection()` | INSTRUMENTATION ONLY under normal operation (inert unless the legacy fallback path is reached — prior audit finding, unchanged) |
| `get_river_brain().save()` | EXPERIMENTALLY DANGEROUS **only across a process restart** — within one process, in-memory mutation already happened regardless of whether `.save()` is ever called |
| ClaudeShard/Wolf-bridge | INSTRUMENTATION ONLY (dry-run, no production write) |
| `_post_response_audit()` | INSTRUMENTATION ONLY |

## 5. Side-Effect Proof (for `deliberate_and_learn()` Specifically)

Direct evidence, not inference, for each:

- **RiverBrain mutation: PROVEN.** Lines 811, 899, 955, 963, 1028, 1057, 1060 — six distinct call sites, covering every return path.
- **Memory writes (FAISS/vector): DISPROVEN.** No call to `add_to_vector_memory()`/`retrieve_relevant_memories()` anywhere in this function (confirmed, re-grepped this pass).
- **Interaction-log writes: DISPROVEN** for this function specifically — `log_interaction()` is not called anywhere inside `deliberate_and_learn()` (confirmed via grep of the full function body).
- **Reflection-shard writes: DISPROVEN** for this function specifically — same check, `save_reflection()` is not called inside it.
- **FAISS mutation: DISPROVEN** (same as memory writes above).
- **Council-ranking mutation: PROVEN, indirectly.** `river_brain.learn()`'s in-memory mutation of `model_task_stats` directly feeds `_select_council()`'s own `river_brain.score_model()` calls on any subsequent invocation within the same process — this is the exact mechanism, not a guess.
- **Persistent model-selection changes: PARTIALLY PROVEN.** Persistent *within a process* (confirmed — nothing resets `model_task_stats` between calls), NOT persistent *across a restart* unless something else calls `.save()` (confirmed RiverBrain.learn() itself never calls save — §6 below).
- **External synchronization: DISPROVEN** for this function specifically — it never touches `interaction_log.jsonl`, the only file `sync_protocol.py` reads.
- **Background task creation: DISPROVEN** — no `threading.Thread`/`asyncio.create_task` anywhere in this function.
- **Singleton mutation: PROVEN.** `river_brain` (passed in, but it's the live singleton from `get_river_brain()` at the call site either way) and the module-level `_cb_state` circuit-breaker dict (via every `_ollama_query()` call) are both mutated.
- **Global-state mutation: PROVEN**, two distinct globals — `_cb_state` (circuit breaker, self-clearing) and, conditionally, whatever `core.publish_salience()`'s downstream dispatch does (a Global Workspace event, `memory/workspace_log.jsonl` write).

## 6. Read-Only Is Not Enough — State Classification

| State | Classification |
|---|---|
| `_cb_state` (circuit breaker) | TRANSIENT MUTATION (self-clearing on success, confirmed prior pass) |
| `river_brain.model_task_stats`/`.classifiers`/`.scalers`/`.observation_counts` | **PERSISTENT MUTATION within the process** (survives for the process's lifetime once `.learn()` is called; not written to disk unless `.save()` is separately invoked — confirmed `RiverBrain.learn()`'s own body contains no `save` call, this pass) |
| `_last_world_surprise` (module-level dict, `river_deliberation.py:157`) | **EXTERNALLY-FED, PERSISTENT MUTATION** — but the mutator is `echo_core.py`'s own Global Workspace dispatch (a lambda subscribed to `world_model.surprise` events, confirmed via direct grep: `echo_core.py:240`), **not** `deliberate_and_learn()`/`echo_query()` themselves. `deliberate_and_learn()` only *reads* this global (§1, lines 851-853). This is a real, ambient confound driven by Echo's *other* background subsystems, not a feedback loop our own trials create. |
| `memory/workspace_log.jsonl` (via `core.publish_salience()`) | PERSISTENT MUTATION (disk write), conditional on `_workspace_consumed and exploration_bias > 0.0` |
| `memory/council_deliberations.jsonl` (via `_log_council_deliberation()`) | PERSISTENT MUTATION (disk write), on every real return path |
| Random state (`_jittered_temperature`, council exploration draws) | TRANSIENT — reseeded implicitly via Python's global `random` module state each call, not itself experiment-relevant beyond ordinary stochasticity already accounted for in the protocol's replication requirement |

## 7. Council Fidelity

`deliberate_and_learn()` called directly (no wrapper) constructs the council via the **exact same** `_select_council()` call `echo_query()`'s own invocation uses — same function, same arguments shape, same `river_brain`/`model_pool` objects (since both would use the real, live singleton/pool in any real run). **No difference exists here between "through `echo_query()`" and "direct."** The one real fidelity question is upstream of council construction: whether `river_brain`'s accumulated stats (which determine ranking) have been shaped by *our own prior trials* in the same batch — which, per §5/§6, they genuinely have, on both paths, identically, since both paths run the identical `.learn()` calls.

## 8. On the Function's Name

**Explicitly not inferred from the name.** `deliberate_and_learn` does, in fact, learn — extensively, on every return path, as directly proven in §5. The name is accurate, not misleading. The prior audit's error was not "trusting the name" — it was failing to read the function's own body completely before drawing a conclusion about it, and inferring from the wrapper's own structure that all learning lived one layer up. Recorded plainly as the actual mistake, not softened.

## 9. Design B vs. Design D, Corrected

| Property | Design B (`_ollama_query()` alone) | Design D (`deliberate_and_learn()` alone) — **corrected from prior audit** |
|---|---|---|
| RiverBrain mutation | None | **Real, in-process, on every real path** |
| `council_deliberations.jsonl` write | Only if caller opts in | **Always attempted** (try/except-wrapped, not skippable without editing the function) |
| Global Workspace write | None | **Conditional, real** |
| Council-composition dependency on ambient state | None (single fixed model, no `_select_council()` call at all) | **Real** — depends on `_last_world_surprise` (externally fed) and on the same batch's own accumulated RiverBrain mutations |
| Extra inference call (warm-up) | None | One extra `_ollama_query()` call per invocation (prompt `"."`) |
| Council/synthesis fidelity | Only for `DIRECT_ECHO_TASKS` task types | Full, for any task type |
| Interaction-log / sync / peer-rating exposure | None | None (same as before — this part of the prior audit's finding still holds) |

**What Design D adds relative to Design B, precisely**: real council diversity, real synthesis, full task-type fidelity — genuine, valuable additions for architectural realism. **What it does NOT avoid, contrary to the immediately prior audit's claim**: RiverBrain training, a diagnostic-log write, and a conditional Global Workspace write, all of which create real, in-process cross-trial coupling for the duration of a single experimental session.

## 10. The Key Counterfactual

> If we replaced the normal `echo_query()` call with direct `deliberate_and_learn()`, what behaviorally relevant component of Echo would we be removing?

**Answer: X, not None.** We would remove: the ambient system-context notes (circadian/stillness/temporal/scripture/tool-list — ordinary conversational texture, not part of the *reasoning* mechanism itself), `interaction_log.jsonl` persistence (and its downstream peer-rating/sync eligibility), `reflection_shard.jsonl` persistence, disk-level RiverBrain persistence (`.save()`), and ClaudeShard/Wolf-bridge triggering. We would **not** remove RiverBrain's in-process learning, the council-selection/synthesis architecture itself, or the diagnostic council-deliberation log. This makes Design D scientifically weaker than the prior audit claimed, but still meaningfully different from — and cleaner than — Design A on several concrete, disk-persistent, cross-machine-visible axes (interaction log, sync, peer rating). It is a real middle ground, not a clean substitute for Design A, and not the confound-free alternative the prior audit described.

## 11. Experimental Interpretation

- **Claim 1 — "Direct `deliberate_and_learn()` is free of the known contamination mechanisms."** **FALSE.** Directly disproven by §5's six `river_brain.learn()` call sites and the unconditional `_log_council_deliberation()` write on every real path.
- **Claim 2 — "Direct `deliberate_and_learn()` preserves Echo's relevant deliberative architecture."** **PROBABLY TRUE**, with a real caveat: it preserves the *mechanism* (real council selection, real per-councillor queries, real synthesis) faithfully and identically to Design A — but that mechanism's own ranking inputs are, per §6, shaped by the very RiverBrain mutations the same experiment would be causing, batch over batch. A single, isolated call has fully faithful architecture; a *sequence* of calls within one experimental session does not have fully independent architecture from trial to trial.
- **Claim 3 — "Therefore direct `deliberate_and_learn()` is the strongest no-production-modification experimental path."** **FALSE**, as a direct consequence of Claim 1 being false — the "therefore" does not follow from a false premise. Design D is not confound-free; it is a real, measurable improvement over Design A on specific axes (no interaction-log/reflection-shard/sync/peer-rating/ClaudeShard exposure) while retaining Design A's RiverBrain-driven cross-trial coupling and adding its own (workspace-log write, ambient world-surprise dependency).

## 12. Final Design Recommendation

**NEITHER**, reported as a genuine, unresolved conflict rather than resolved by picking one:

- **Design B** changes experimental contamination the least (as close to zero as any real path in this codebase gets) but changes "Echo" the most for any task type outside `DIRECT_ECHO_TASKS` — it substitutes a single model's raw opinion for Echo's real, synthesized, multi-perspective voice.
- **Design D** changes "Echo" the least (the actual reasoning mechanism is untouched, identical to production) but does **not** change experimental contamination anywhere near as much as previously claimed — real RiverBrain coupling and a real diagnostic-log write remain, both capable of making trial N+1's council composition depend on trial N's own occurrence.

**The mission's own final constraint applies directly and is not resolvable by this audit alone**: "changes Echo the least" and "changes contamination the least" point at *different* designs here, not the same one. Reporting this conflict, not hiding it, is the correct output of this pass. A future decision must explicitly trade one against the other, or pursue a design not yet identified in either audit (e.g., a task-type chosen from `DIRECT_ECHO_TASKS` specifically so Design B becomes simultaneously clean *and* architecturally faithful — the one condition under which this conflict actually dissolves, already noted in the prior audit but worth restating as the most promising resolution: **choosing a `DIRECT_ECHO_TASKS`-shaped forced-choice framing makes Design B both the cleanest and the most faithful design available, with no remaining conflict** — this is the one path this audit can recommend without reservation, and it requires no new construction, only a framing decision for the forced-choice task itself).

---

## Final Response

```
DELIBERATIVE PATH DIFFERENTIAL RESULT

Live Echo invoked: NO
Production modified: NO
Protocol modified: NO

Claim 1 — no known contamination:
FALSE

Claim 2 — preserves relevant Echo deliberation:
PROBABLY TRUE

Claim 3 — strongest experimental path:
FALSE

Design B:
Cleanest available (near-zero contamination), but only architecturally
faithful for DIRECT_ECHO_TASKS-shaped task types (personal, reflection,
spiritual, identity, faith, poetry, dream); for other task types it is a
real simplification, not just a cleanliness gain.

Design D:
Preserves Echo's real council/synthesis mechanism faithfully, but is NOT
contamination-free as the prior audit claimed — real in-process RiverBrain
mutation (six call sites, every return path) and a real, unconditional
council_deliberations.jsonl write remain, both capable of coupling trial
N to trial N+1 within a session. A genuine, corrected downgrade from the
prior audit's GREEN verdict.

Recommended design:
NEITHER, as a blanket choice — report the conflict. The one design that
resolves it without new construction: Design B, deliberately scoped to a
DIRECT_ECHO_TASKS-classified task_type, which makes single-model
inference simultaneously the cleanest AND the architecturally faithful
choice, dissolving the tradeoff rather than picking a side of it.

Most important remaining uncertainty:
Whether the forced-choice experimental task can be framed in a way that
genuinely, honestly fits a DIRECT_ECHO_TASKS category (personal/identity/
reflection-shaped) without distorting the actual research question being
asked — this is a framing/content decision, not a technical one, and was
not evaluated in this pass.

Next authorized action:
A researcher decision on task-type framing for the next protocol revision.
No file was changed to enable or require this — both Designs B and D
already exist, unmodified, in production.
```
