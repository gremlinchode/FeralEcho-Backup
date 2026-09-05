# EchoResponder → echo_query() Contamination Audit

Pre-flight forensic audit performed before any live Echo trial under
protocol P0.1. **Live Echo was not invoked at any point in this audit.**
All findings below come from direct source reads (file:line citations)
and, where noted, isolated static/structural checks that never call
`get_river_brain()`, `echo_query()`, or any other production entry
point. No RiverBrain state, FAISS index, interaction log, or reflection
file was mutated by this audit.

Evidence standard: **FACT** (directly read/verified this pass),
**INFERENCE** (a reasoned conclusion bridging two or more facts),
**SPECULATION** (plausible but unverified). Every claim below is
labeled.

---

## 1. Executive Verdict

**YELLOW — run only with documented confounds.**

No pathway was found by which the experimental candidate's own text or
meaning reaches Echo's model input outside the intended channel — the
hidden-state design's core property held up under this audit. What was
found instead is more subtle and, in its own way, more important: the
default `echo_query()` path `EchoResponder` calls is not a simple,
isolated single-model call — it is Echo's **full production multi-model
council deliberation and synthesis pipeline**, with real, persistent,
cross-trial side effects (RiverBrain training, a flat interaction log,
a reflection-shard log, ClaudeShard friction assessment, a task-type
classifier hook, and eligibility for real background peer-rating and
cross-machine sync) that the prior calibration and protocol-lock passes
never priced in, because they only ever exercised `MockResponder`.
None of these side effects leak the *candidate's own content* back to
Echo — but several of them create real trial-to-trial coupling through
shared, mutating production state, and at least one (Tailscale sync
eligibility) crosses this experiment's own intended isolation boundary
into a second machine's memory store. These are documented as
confounds, not fixed, per this audit's own safety boundary.

## 2. Scope and Safety Boundary

This audit is read/trace/static-test only. No production file was
modified. No live Echo trial was run. Two brief, targeted greps were
run against production source to confirm call sites (`app/core/
echo_model_orchestrator.py`, `app/core/river_deliberation.py`,
`app/core/council_rater.py`, `app/sync/sync_protocol.py`) — no
production function was ever invoked. `get_river_brain()` was
deliberately never called in this pass (not even read-only), since even
constructing/loading the singleton was judged an unnecessary risk given
the audit's own question could be answered from static code alone.

## 3. Protocol Version / Hash

Protocol: **P0.1**
Hash: **2880fa048815f768d3b303ce7fff6e04196bf14949b53068fd7f0ec2a61a6a20**
Verified this pass (**FACT**): `python scripts/verify_protocol_seal.py
audits/2026-09-03_preference_experiment_preregistered_protocol.md
--expect 2880fa...a20` → `MATCH`.

## 4. Exact Call Graph

**FACT**, confirmed by direct reads of `app/experiments/preference_
provenance/harness.py`, `app/core/echo_model_orchestrator.py`, and
`app/core/river_deliberation.py`:

```
harness.run_trial() / run_counterfactual_batch()
        │
        ▼
EchoResponder.respond()                         [harness.py:214-249]
        │  builds full_prompt = build_forced_choice_prompt(
        │      task_description, label_to_option_text)   [harness.py:232, 252-266]
        │  calls:
        ▼
echo_query(full_prompt, task_type=self.task_type,          [echo_model_orchestrator.py:1367]
           system=system_context, source="preference_provenance_experiment")
        │
        │  (use_all defaults to False, never overridden by EchoResponder)
        │
        ▼
[system_parts assembly — unconditional]                    [:1419-1520]
   EPISTEMIC-NOTE, CIRCADIAN-STATE/STILLNESS-STATE (conditional),
   temporal_context, scripture-injection scan, TOOL-LIST (task-type-gated)
        │
        ▼
if not use_all:  →  deliberate_and_learn(...)               [:1525-1557, river_deliberation.py:722]
        │              (real multi-model council + synthesis)
        ▼
quality = _score_response_quality(response, task_type)      [:1558]
get_river_brain().learn(ECHO_SYNTHESIS_MODEL, task_type, response)  [:1563]
log_interaction(model_name=..., prompt=full_prompt, response=..., source=..., ...)  [:1571-1580, local def at :206]
save_reflection({"prompt": full_prompt, "best_response": response, ...})  [:1587-1592]
get_river_brain().save()                                     [:1593]
CLAUDE_SHARD.assess(response, context=full_prompt)            [:1598] → _friction_window (shared global) → possible simulate_self_edit() dry-run [:1611-1621]
_post_response_audit(response, task_type)                    [:1629, :117]
        │
        ▼
return response  →  EchoResponder parses via _parse_label_choice()  [harness.py:203-220]
```

**Legacy/fallback branch** (`choose_model()`/`rank_models()`/
`ollama_query()`, lines 1635-1705) is reached **only** if
`deliberate_and_learn()` raises an exception (caught at line 1632) or if
`use_all=True` — neither is `EchoResponder`'s default behavior. This
matters: `rank_models()` (which reads `memory/reflection_shard.jsonl`,
see §9) is **not** on the normal-operation path for this experiment.

## 5. Exact Dataflow

```
┌───────────────────────────┐
│ EXPERIMENTAL STATE        │
│ candidate.source_text     │──┐
│ candidate.normalized_repr │  │ (never passed to Responder.respond() —
│ candidate_id              │  │  confirmed by protocol type signature:
│ lifecycle status          │  │  respond() receives only task_description,
└───────────────────────────┘  │  label_to_option_text, system_context, bool)
                                │
              task_description ─┼─► build_forced_choice_prompt() ─► full_prompt
   label_to_option_text ────────┘        (harness.py:252-266)
                                                  │
                        system_context (caller-controlled;   │
                        candidate text present ONLY in the   │
                        explicit-visible condition) ─────────┤
                                                              ▼
                                                    echo_query(full_prompt, system=system_context, ...)
                                                              │
                        ┌─────────────────────────────────────┼──────────────────────────┐
                        ▼                                     ▼                          ▼
             system_parts (EPISTEMIC-NOTE,             deliberate_and_learn()      RiverBrain.learn()
             CIRCADIAN/STILLNESS, temporal,             (council selection via     (numeric features only,
             scripture scan, TOOL-LIST) —               river_brain.score_model(),  see §10 — response
             none candidate-related, all                Modelfile identity block   TEXT never persisted
             fixed/generic (FACT, read directly)         prepended for Echo's own   inside RiverBrain)
                                                          synthesis turn — Finding
                                                          46 precedent, INFERENCE
                                                          from cited prior audit,
                                                          not re-verified line-by-
                                                          line this pass)
                        │                                     │                          │
                        └─────────────────────────────────────┼──────────────────────────┘
                                                              ▼
                                                   response (raw text)
                                                              │
                        ┌─────────────────────────────────────┼──────────────────────────┐
                        ▼                                     ▼                          ▼
             log_interaction() → memory/            save_reflection() →         ClaudeShard.assess()
             interaction_log.jsonl (flat,           memory/reflection_shard     → shared _friction_window
             full prompt+response, source           .jsonl (flat, full         (module global, persists
             tag preserved) — read by                prompt+response) — read    across ALL calls in this
             council_rater.py (NO source              only by rank_models()      process) → possible
             filter, FACT) and                        (NOT reached on normal     simulate_self_edit() dry-
             sync_protocol.py (NOT in                 deliberation-success       run trigger (FACT: real,
             LOCAL_ONLY_SOURCES, FACT)                path, FACT)                but dry-run only, never
                                                                                  save_code())
                                                              │
                                                              ▼
                                              EchoResponder._parse_label_choice()
                                                              │
                                                              ▼
                                                    experimental outcome (RawTrial)
```

## 6. EchoResponder Analysis

**FACT**, `harness.py:167-266`:
1. Receives exactly four keyword arguments per call: `task_description: str`, `label_to_option_text: dict`, `system_context: Optional[str]`, `candidate_visible: bool`.
2. Never receives the `PreferenceCandidate` object, `candidate_id`, lifecycle status, or provenance record — these exist only in `harness.run_trial()`'s calling scope, one level up.
3. Constructs `full_prompt` via `build_forced_choice_prompt()` — a pure string concatenation of `task_description` + each labeled option + a fixed forced-choice instruction sentence. No candidate-specific content is ever added by this function itself.
4. Global state accessible to it: none directly — it's a plain class with one instance attribute (`self.task_type`). It does not hold or read any module-level global.
5. Process/session state accessible: `echo_query()`'s own internals (see §7) — `EchoResponder` itself threads no session ID, conversation history, or process-level cache.
6. Response data returned: raw response string, best-effort parsed label choice, hardcoded `model="echo:live"` (**note**, FACT: this is a hardcoded literal, not the actual model name RiverBrain/deliberation selected — a real, if minor, inaccuracy in the recorded metadata; the true model identity used within the council/synthesis is not surfaced back to the `RawTrial` record at all).

## 7. echo_query() Analysis

**FACT**, `echo_model_orchestrator.py:1367-1630`. See §4's call graph for the exact sequence. Key points not already covered above:

- `resolve_task_type(prompt)` is called **unconditionally** at the top (line 1408), even though its result is discarded whenever `task_type` is explicitly supplied (it always is, from `EchoResponder`). Confirmed pure/side-effect-free (`compute_intent_heatmap` + `detect_task_type`, no writes) — wasted computation, not a risk.
- `system_parts` assembly (lines 1419-1520) is **entirely independent of the experimental candidate** — every note added (EPISTEMIC-NOTE, CIRCADIAN-STATE, STILLNESS-STATE, temporal weather context, scripture-citation scan of the prompt, TOOL-LIST) is either a fixed string or derived from Echo's own real-time internal state, never from anything the experiment controls. **INFERENCE**: none of these could leak the candidate's *content*, but they do mean the model's actual received system prompt is materially larger and more varied than `EchoResponder`'s own `system_context` argument alone — worth knowing for anyone trying to reason about "the exact prompt Echo saw" from the harness's records alone, since `RawTrial.raw_prompt`/`confounds.system_prompt_hash` capture only what `EchoResponder` supplied, not this additional assembled content.
- TOOL-LIST fires when `task_type in TOOL_AWARE_TASKS or _wants_tools_by_content` (line 1509) — **not independently re-verified this pass** whether `"reasoning"` (EchoResponder's default `task_type`) is in `TOOL_AWARE_TASKS`; flagged as **UNRESOLVED**, low-severity (tool-list exposure is generic tool *names*, not candidate content, per this project's own prior forensic work on `echo_model_orchestrator.py:1511-1515` cited in an earlier report in this thread — not re-verified line-by-line here).

## 8. Model-Input Construction

**FACT**: `full_prompt` (task + options) becomes `deliberate_and_learn()`'s `prompt` argument; `system_prompt` (the joined `system_parts`) becomes its `system` argument. **INFERENCE, carried forward from this project's own prior audit (Finding 46, cited not re-verified line-by-line this pass)**: for any councillor call where `model == OLLAMA_MODEL` (i.e., Echo's own synthesis turn), `ollama_handler.py`'s `_build_chat_messages()` additionally prepends the real Modelfile identity block ahead of the supplied system content — meaning the actual text reaching the model for Echo's own turn includes persona/identity content neither `EchoResponder` nor `echo_query()`'s own visible code path constructs directly. This is not experimental-candidate leakage — it's a reminder that "what `EchoResponder` sent" and "what the model literally received" are not identical, and the harness's own recorded `system_prompt_hash` (confounds.py) reflects only the former.

## 9. Memory/Retrieval Analysis

**FACT, the single most reassuring finding of this audit**: no call to `retrieve_relevant_memories()`, `retrieve_memory_context()`, or any FAISS/vector-store read exists anywhere in `river_deliberation.py` or in `echo_query()`'s own body (confirmed via direct grep of both files — zero hits). The memory-injection layers that exist elsewhere in this codebase (`terminal_client.py`, `routes_echo_studio.py`'s `_build_full_prompt()`) are **not** on this call path at all — `EchoResponder` calls `echo_query()` directly, bypassing both. **H2 and H3 (no retrieval-based leakage) are PROVEN for this specific call path**, not merely probable.

Separately (**FACT**): `save_reflection()` (`echo_model_orchestrator.py:186-189`) writes the full `full_prompt`/`response` unconditionally to `memory/reflection_shard.jsonl` on every successful deliberation. The only reader of that file anywhere in the codebase is `rank_models()` (`echo_model_orchestrator.py:1153-1154`, confirmed via full-repo grep for `load_reflections`) — which, per §4, is **not reached on the normal-operation path** for this experiment. **INFERENCE**: under today's code, this write is a real but currently-inert disk artifact — it does not currently feed back into any live decision for `task_type="reasoning"` trials, because nothing calls `rank_models("reasoning")` on the success path. This is a fragile non-contamination, not a structural guarantee — if the deliberation path ever throws (network hiccup, model unavailable), the fallback branch **would** read this exact history back into a real scoring decision for the very next fallback-routed call.

Distinct file, distinct finding (**FACT**): `log_interaction()` (the local definition at `echo_model_orchestrator.py:206`, not `memory_bridge.py`'s FAISS-gated function of the same name — confirmed these are two separate functions and the local one shadows within this module) writes the full prompt/response to `memory/interaction_log.jsonl` as a flat log only — **no FAISS/vector-memory commit occurs via this path**. This file is read by two other subsystems, addressed in §10 and §14.

## 10. RiverBrain Analysis

**FACT**: `get_river_brain().learn(ECHO_SYNTHESIS_MODEL, task_type, response)` (line 1563) fires on every successful deliberation call. Read directly (`RiverBrain.learn()`, `echo_model_orchestrator.py:808-831`): it extracts **numeric features** (`_extract_quality_features`) and a binary quality label from the response text — **the raw response text itself is never stored inside RiverBrain's own state** (`classifiers`, `scalers`, `model_task_stats` are all numeric structures). This rules out literal candidate-text leakage via RiverBrain specifically.

**What RiverBrain *does* create (FACT + INFERENCE)**: a real, persistent, cross-call update to `model_task_stats[ECHO_SYNTHESIS_MODEL]["reasoning"]` (count + running mean), which — per `_select_council()`'s own docstring (`river_deliberation.py:468-517`) — feeds `river_brain.score_model()`'s per-model ranking for **every subsequent call with the same task_type**, including later trials in the *same* experimental batch. `_select_council()` additionally has two independent stochastic mechanisms (`exploration_bias`, tied to real-time world-surprise; `fair_sample_refresh`, tied to under-sampled-model fairness) that can swap **one** council slot per call for reasons entirely unrelated to the experimental candidate. **Classification: INDIRECT CONTAMINATION, not DIRECT LEAKAGE** — no candidate-equivalent information reaches the model, but council *composition* (which non-Echo models are consulted before synthesis) can drift trial-to-trial for reasons independent of the manipulated variable, which is a real confound on the *causal cleanliness* of a batch, even though it does not compromise the hidden-state property itself.

**A note on what was deliberately not tested here**: this audit did not construct even a synthetic call to `get_river_brain().learn()`, because doing so would mutate the real, live, production RiverBrain singleton — explicitly forbidden by this audit's own safety boundary ("changing RiverBrain state"). The conclusions above rest on direct code reading, not a live reproduction. This is a real epistemic limit of doing this audit safely, stated plainly rather than glossed over.

## 11. Session/Process-State Analysis

**FACT**: `echo_query()`'s signature has no `conversation_history`, `session_id`, or equivalent parameter at all. `EchoResponder` threads no session identity through to `echo_query()`. **PROVEN**: no session-history channel exists in this specific call path — H5 holds structurally, not just probably.

**Distinct from this** (per the mission's own Step 7 instruction to separate these): the existing process-boundary persistence test (`scripts/verify_preference_provenance_experiment.py:460-501`, subprocess round-trip) proves only that **a candidate written to disk by one process is readable by a second process**. It says nothing about whether a trial's own *side effects* (RiverBrain stats, `interaction_log.jsonl`/`reflection_shard.jsonl` entries) survive and influence a *later* trial's actual model behavior. **These are not the same property**, and only the first has been tested. The second (trial-to-trial behavioral contamination via shared production state) is addressed qualitatively in §10/§14 via code trace, not via any executed test — a real, stated gap (§17).

## 12. Tool Analysis

**FACT**: the TOOL-LIST system note (§7) exposes tool *names* only (`_tm.list_tools()`, confirmed elsewhere in this project's own prior forensic work in this thread — not re-derived here), never invokes a tool, and never contains candidate-related content. `deliberate_and_learn()`'s own synthesis path does not appear to invoke `echo_tool_dispatch.py`'s tool-execution branch based on this audit's reading (that dispatch path lives in `routes_echo_studio.py`, not `echo_query()`) — **INFERENCE**, not independently re-traced line-by-line in this pass. No tool-mediated leakage pathway was found.

## 13. Hidden-State Validity Matrix

| Prop. | Claim | Classification | Evidence |
|---|---|---|---|
| H1 | Candidate text absent from direct model input | **PROBABLY TRUE** | `leakage.py`'s check covers `task_description`/`system_context`/option-labels *as constructed by the harness* — but `echo_query()` adds further system content (§7/§9) that the leakage checker never inspects. No candidate-related content was found in any of that additional content (it's all fixed/generic), but the leakage checker's own coverage does not extend to it — a real gap between "checked" and "actually safe," even though this audit found no evidence the gap is currently exploited. |
| H2 | No candidate-equivalent info via retrieval | **PROVEN** | Zero retrieval calls anywhere in the real call path (§9) |
| H3 | No candidate-equivalent info via memory | **PROBABLY TRUE** | No FAISS commit occurs via this path (§9); flat-log writes exist but are not currently re-ingested by anything |
| H4 | No candidate-equivalent info via RiverBrain/state changes | **PROBABLY TRUE for candidate-content leakage; FALSE for trial-to-trial numeric coupling** — see §10, split finding | RiverBrain stores no raw text, but does create real cross-trial scoring coupling |
| H5 | No candidate-equivalent info via session history | **PROVEN** | No session parameter exists in this call path (§11) |
| H6 | No candidate-equivalent info via tools | **PROBABLY TRUE** | Tool-list exposes names only, no execution on this path (§12) |
| H7 | No experimental metadata identifies the condition | **PROVEN** | `Responder.respond()`'s type signature structurally excludes it (§6) |
| H8 | Behavioral prompt identical across conditions except intended variables | **PROVEN** | `run_counterfactual_batch()` shares one `task_description` parameter across both arms (confirmed in the prior red-team pass, re-confirmed by reading `harness.py` again this pass) |

## 14. Trial-to-Trial Contamination Analysis

Three real, confirmed (**FACT**) coupling mechanisms, none of which leak the candidate's own content, all of which represent shared, mutating state across trials within a batch (and beyond, into real conversations and a second machine):

1. **RiverBrain `model_task_stats`** (§10) — persistent within-process and across restarts (pickled), genuinely accumulates across every trial tagged `task_type="reasoning"`.
2. **`_friction_window`** (`echo_model_orchestrator.py`, module-level global, confirmed via the `with _friction_lock:` block at line 1600) — a shared rolling window across *every* call to `echo_query()` in the process, not reset per-trial or per-experiment. Feeds `echo_state.py`'s `friction_rate` dimension (**INFERENCE**, cited from this project's own prior documentation, not re-verified this pass) and can trigger `simulate_self_edit()` (Wolf Friction Bridge dry-run — confirmed **dry-run only**, never calls `save_code()`, per this project's own extensively-documented design).
3. **`memory/interaction_log.jsonl`** (§9) — read by two subsystems with no source-based exclusion for our experimental tag:
   - `council_rater.py` — confirmed via full-file grep, **zero** occurrences of the string `"source"` anywhere in the file. It has no exclusion mechanism at all; a background thread samples 1-in-5 "rateable" entries regardless of origin. Since `council_baseline_trusted_since` is genuinely set in this project's own history (real trust, not hypothetical), a peer-rated experimental trial could feed `learn_from_council_rating()` — another real, numeric-only RiverBrain-training coupling, on top of §10's.
   - `app/sync/sync_protocol.py` — `LOCAL_ONLY_SOURCES = {"self_edit"}` (line 26) does not include `"preference_provenance_experiment"`. **This means, on the next real Tailscale sync cycle, our experimental trials' full prompt and response text would be pushed to the Air machine's own `interaction_log.jsonl`.** This is not a hidden-state validity violation (it doesn't affect what *this* Echo instance sees), but it is a genuine crossing of this experiment's intended isolation boundary into a second production system, and was not previously identified in either the implementation report or the red-team document.

## 15. Post-Hoc/Rationalization Analysis

**FACT**: `EchoResponder.respond()` makes exactly one model call per trial and derives `parsed_label_choice` from the *same* response text used for any explanation — there is no separate "decision" call distinct from an "explanation" call in the current design (confirmed by reading the function: one `echo_query()` call, one `_parse_label_choice()` pass over its output). **INFERENCE**: this means the current apparatus, as built, cannot yet distinguish "Echo chose, then explained" from "Echo's single generation pass produced a choice-shaped conclusion embedded in otherwise free text" — the two are structurally identical here, since there is only one generation event per trial. The mission's own prior protocol design (`preregistered_protocol.md` §24 references, and the provenance report's §8) already flags decision-before-explanation ordering as a **future** control, not yet implemented — this audit confirms that gap is real and unchanged, not newly discovered.

## 16. Mock Coverage Analysis

**What the existing calibration/test suite proves (FACT, re-confirmed by reading rather than re-running)**: `MockResponder`'s `respond()` never calls `echo_query()`, never touches RiverBrain, `interaction_log.jsonl`, `reflection_shard.jsonl`, `council_rater.py`, or `sync_protocol.py` — it is a pure, in-memory, seeded random-choice function. The calibration script's six scenarios (known positive, known null, verbal-only, label invariance, reversal, replication) all correctly validate the **statistical/interpretive layer** (`classify_effect()`, label randomization, the leakage checker's own logic) — genuinely valuable, genuinely verified.

**What they do not, and structurally cannot, prove**: anything about `echo_query()`'s real behavior, RiverBrain's real cross-trial coupling, the real interaction-log/reflection-log side effects, or the real production-boundary crossings identified in §14. **This is not a flaw in the calibration design** — it was explicitly scoped to validate the harness's own statistical machinery using a responder that could never touch production, which it does correctly. It simply means, as this audit's mission anticipated, that "the mock lab works" and "the real `EchoResponder → echo_query()` path is safe" are two separate claims, and only the first has ever been demonstrated.

## 17. Unresolved Uncertainties

- Whether `"reasoning"` is in `TOOL_AWARE_TASKS` (§7) — low severity, not resolved this pass.
- Whether `_select_council()`'s stochastic council-composition drift (§10) produces an effect size large enough to matter relative to the protocol's own `_ROBUST_EFFECT_SIZE_THRESHOLD=0.15` — not measured; would require either a careful analytical bound or a real (currently un-run) trial batch with council composition logged per trial.
- Whether the leakage checker's coverage gap (§13, H1) has ever mattered in practice — no evidence either way; the additional system content it doesn't check is currently fixed/generic, but this is a property of today's code, not a structural guarantee.
- Whether `council_rater.py`'s background sampling is even running/active at the time a real trial batch would execute (thread liveness not checked this pass — a real operational question, not just an architectural one).

## 18. GREEN/YELLOW/RED Verdict

**YELLOW.** Restated per §1: no material pathway leaks the candidate's own content to the model outside the intended channel — the hidden-state design's central property holds. But real, previously undocumented confounds exist, all bounded to *known mechanisms* with *known (if not fully measured) direction*:

| Confound | Severity | Likely direction | Biases toward/against hypothesis | Measurable? | Isolatable later? |
|---|---|---|---|---|---|
| RiverBrain council-composition drift within a batch (§10) | Medium | Unclear a priori — could inflate OR deflate observed effect depending on which non-Echo councillor gets swapped in | Neither predictably — genuine noise source | Yes — log council composition per trial (not currently done) | Yes — fix RiverBrain state before each batch, or log and covariate-adjust |
| `reflection_shard.jsonl`/`rank_models()` fallback-path coupling (§9) | Low (inert on success path, real only on exception) | N/A unless deliberation fails | N/A | Yes — count fallback occurrences per batch | Yes — treat any fallback-routed trial as excluded/flagged |
| `council_rater.py` peer-rating of experimental trials (§14) | Low-Medium | Adds numeric RiverBrain signal unrelated to the manipulated variable | Neither predictably | Partially — would require checking `council_ratings.jsonl` for our `source` tag after a batch | Yes — this can be checked and excluded post-hoc, or the source tag added to a future exclusion list |
| Tailscale sync eligibility (§14) | Low for THIS experiment's validity / **High for isolation-boundary intent** | N/A (doesn't affect Echo's own behavior) | N/A | Yes — check `LOCAL_ONLY_SOURCES` before/after | Yes — either avoid syncing during the trial window, or add the source tag to `LOCAL_ONLY_SOURCES` (a one-line production change, requiring separate authorization) |
| ClaudeShard friction/Wolf dry-run triggering (§14) | Low (dry-run only, no production write) | N/A | N/A | Yes — check `memory/wolf_dryrun.jsonl` for entries during the trial window | Yes — same as above |
| Leakage checker's coverage boundary (§13, H1) | Low (no evidence of current exploitation) | N/A | N/A | Partially — would require snapshotting the *actual* assembled system prompt `echo_query()` sends, not just what `EchoResponder` supplies | Possible in a future pass |

## 19. Required Conditions Before Live Trial

1. Decide, explicitly, whether the four confounds above are *accepted* (documented, logged, and covariate-checked after each batch) or *mitigated* before running — this decision belongs to the researcher, not this audit.
2. At minimum, before any live batch: confirm whether `council_rater.py`'s background thread is live in the target process, and check `memory/wolf_dryrun.jsonl`/sync logs for any activity coinciding with the trial window, so post-hoc contamination can at least be detected even if not prevented.
3. Consider recording actual council composition per trial (which non-Echo models were consulted) as an additional confound field, since this is currently invisible in `RawTrial`.
4. Do not treat `EchoResponder`'s hardcoded `model="echo:live"` field as a faithful record of which models actually participated — it is not (§6).
5. Re-read §13's H1 gap before claiming "complete hidden-state validity" in any future report — the honest claim is "no exploitation found," not "impossible by construction," for the portion of the prompt `echo_query()` assembles beyond what `EchoResponder` supplies.

## 20. Live Echo Status

**NOT RUN.** No call to `EchoResponder.respond()`, `echo_query()`, `deliberate_and_learn()`, or any Ollama/model endpoint occurred during this audit. No file under `memory/river_brain.pkl`, `memory/interaction_log.jsonl`, `memory/reflection_shard.jsonl`, `memory/memory_meta.json`, `echo_principles.json`, or `Modelfile` was written to by this audit.
