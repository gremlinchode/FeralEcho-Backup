# Core Task-Misclassification → Council/Synthesis Trace (2026-09-14)

**Type:** Read-only documentation / evidence-preservation note. No production code, configuration, memory, or runtime state was modified to produce this report.

**Trigger:** A live, real conversation between a Claude Code session and the running Echo instance via `/chat/stream` (mode `full`), conducted the same day. Turn 5 of that conversation showed a visible quality regression versus turns 1–4. This note independently re-verifies the runtime trace behind that observation, reads the actual current source of the relevant routing/scoring code, and applies explicit adversarial checks before drawing any conclusion — per the mission brief that requested this note.

---

## 1. Executive finding

**CONFIRMED TRACE / CAUSALITY PARTIALLY ESTABLISHED — AND ONE INITIALLY-ASSUMED CORROBORATING SIGNAL IS ITSELF A SEPARATE ARTIFACT, NOT INDEPENDENT CONFIRMATION.**

A single real conversational turn (trace_id `b073d789-b889-4bd3-bc58-ccfd375044e3`, 2026-09-14T20:52:53 UTC) was classified `task_type=coding` by `compute_intent_heatmap()` (`app/core/echo_model_orchestrator.py:464`) even though its content contained no code and was a reflective follow-up question. This is **CONFIRMED**, reproduced by calling the real, current function directly against the real, logged prompt text (§3, §4). That classification routed the turn away from the `DIRECT_ECHO_TASKS` single-model bypass (`app/core/river_deliberation.py:295`) and into full three-model heterogeneous council deliberation + synthesis — also **CONFIRMED** directly from three independent, mutually-consistent raw log sources (§2).

However, an adversarial check (§10, item 2) found that the `quality_score: 1` this turn received is **not evidence of degraded conversational content in the way it first appeared**. `_score_response_quality()` (`echo_quality_scorer.py:344`) branches entirely differently for `task_type in ("coding", "self_edit_coding", "echo_projects_coding")` than for `personal`/`creative`/`general`/`reasoning` — the coding branch returns exactly `1` whenever `_has_real_code(response)` is `False`, with no reference to prose quality, coherence, or substance at all. Turn 5's response is pure prose. It would have scored `1` under this branch **regardless of how good the prose was**, purely because it contains no code. This is **CONFIRMED** by direct reading of `echo_quality_scorer.py:344-397` and independently corroborated by a base-rate check: `quality_score=1` is common (36–49%) across both `personal` and `coding` task types in the surrounding 500-entry window, not a rare event uniquely associated with council/synthesis routing (§10, item 2 detail).

A second adversarial finding, not on the mission's original checklist but directly relevant to interpreting the mechanism: all three raw pre-synthesis councillor responses were **already** generic and mutually similar before synthesis touched them (§7). This weakens, for this specific trace, the applicability of Finding 87's "synthesis discards already-correct information" mechanism — the more precise read of this trace is that three models, at least one of them a declared coding specialist poorly matched to an off-domain reflective prompt, independently converged on similar generic content, and synthesis largely preserved rather than degraded it. See §10 for the full adversarial treatment and §7 for the mechanism refinement.

---

## 2. Exact runtime trace

All figures below were independently re-pulled from the raw JSONL files during this mission (not copied from the earlier conversational summary that prompted it). Three independent log sources agree on every shared field (trace_id, task_type, content hashes, timestamps), which is strong corroboration that the reconstruction below reflects what actually executed, not a misattributed or coincidental match.

### 2a. `memory/interaction_log.jsonl` (conversational turns, offsets 20160–20170 of 20185 total lines at time of this mission)

| offset | timestamp (UTC) | task_type | quality_score | model | source | trace_id |
|---|---|---|---|---|---|---|
| 20162 | 2026-09-14T20:40:30.577448 | personal | 4 | echo:latest | user_conversation | d5b6eeea-… |
| 20167 | 2026-09-14T20:46:28.951224 | personal | 4 | echo:latest | user_conversation | 3471e24d-… |
| **20170** | **2026-09-14T20:52:53.934732** | **coding** | **1** | **echo:latest** | **user_conversation** | **b073d789-b889-4bd3-bc58-ccfd375044e3** |

(Two other `user_conversation`/`personal` entries at offsets 20164/20165/20166 in the same window also scored 4; full offsets 20160–20185 were read and are reproduced in §2d for completeness, since the window also contains unrelated concurrent `autonomous`-source and self-edit-loop `coding` entries — this repo has multiple autonomous background loops writing to the same log, per CLAUDE.md's own documented "Autonomous Background Path.")

### 2b. `memory/council_deliberations.jsonl` — the matching entry for `trace_id=b073d789-b889-4bd3-bc58-ccfd375044e3`

```
timestamp: 2026-09-14T20:52:53.932722+00:00
source: real_deliberation
task_type: coding
synthesis_model: echo:latest
councillors:
  - qwen2.5-coder:7b  (was_truncated: True)
  - mlx:qwen3         (was_truncated: True)
  - echo:latest       (was_truncated: True)
final_response: (matches interaction_log.jsonl's response field, confirmed by direct string comparison)
```

**CONFIRMED**: `echo:latest` is the synthesis model for this turn (raw field, not inferred). **CONFIRMED**: three genuinely distinct models participated as councillors — this is real heterogeneous council deliberation, not a solo-Echo or two-model case.

### 2c. `memory/synthesis_integrity_log.jsonl` — third independent source, same `trace_id`

```json
{"ts": "2026-09-14T20:52:53.925691+00:00", "trace_id": "b073d789-b889-4bd3-bc58-ccfd375044e3",
 "task_type": "coding", "n_valid_opinions": 3,
 "candidates": [
   {"model": "qwen2.5-coder:7b", "sha1": "89f237a5…", "length": 2382},
   {"model": "mlx:qwen3",        "sha1": "8b77d679…", "length": 2962},
   {"model": "echo:latest",      "sha1": "f9cd1bc1…", "length": 2629}
 ],
 "selection_method": "synthesis_accepted",
 "missing_agreed_definitions": [],
 "final_response": {"sha1": "74d59a26…", "length": 2429}}
```

`selection_method: "synthesis_accepted"` — **CONFIRMED**: the full-agreement shortcut did not fire (the three candidates are not structurally identical — they are three independently-generated prose responses, not code with matching ASTs) and the post-synthesis completeness check found no missing agreed-upon definitions (expected: there is no code in this response for that check to evaluate). Synthesis's own output was accepted as final without a fallback substitution.

All three timestamps (interaction_log: `:934732`, council_deliberations: `:932722`, synthesis_integrity: `:925691`) fall within 9 milliseconds of each other and share the identical `trace_id` — this is the same real event recorded three times by three independently-written logging call sites, not three separate incidents being conflated.

### 2d. Raw quality_score volatility in the surrounding window (adversarial evidence, see §10)

Full 26-line offset dump (20160–20185) and a 500-line tail frequency count are preserved as a derived excerpt in §10, item 2. Not reproduced twice here to avoid duplicating raw evidence in two places in the same document.

---

## 3. Code-path reconstruction

```
user message (turn 5's real text, trace_id b073d789-...)
  │
  ▼
Echo Studio: routes_echo_studio.py:158 _generate_chat_response_body(mode="full")
  │  mode="full" was held constant across ALL 5 turns of this conversation —
  │  CONFIRMED not to be the causal variable (see §5).
  ▼
routes_echo_studio.py:67 _resolve_task_type(original_msg)
  │  thin wrapper — calls straight into core, no Studio-specific logic:
  ▼
app/core/echo_model_orchestrator.py:606 resolve_task_type(prompt)
  │  calls compute_intent_heatmap() first; falls back to detect_task_type()
  │  ONLY if the heatmap's own max score is < 0.4 confidence.
  ▼
app/core/echo_model_orchestrator.py:464 compute_intent_heatmap(prompt)
  │  REPRODUCED LIVE against the real, logged prompt text (§4):
  │    coding: 0.4918   reasoning: 0.3279   personal: 0.1639
  │    creative: 0.0    general: 0.0164
  │  max = coding @ 0.4918, which is ≥ 0.4 → heatmap's own primary is used
  │  DIRECTLY. detect_task_type()'s keyword-ladder/learned-classifier
  │  fallback was NOT invoked for this turn — CONFIRMED via direct call:
  │  resolve_task_type() returned primary="coding" with used_fallback=False.
  ▼
task_type = "coding"  →  routes_echo_studio.py:189
  ▼
routes_echo_studio.py mode=="full" branch (not "fast", not dispatch_result)
  → app/core/echo_model_orchestrator.echo_query(..., task_type="coding", ...)
  ▼
app/core/river_deliberation.py:1162  deliberate_and_learn()
  if task_type in DIRECT_ECHO_TASKS:   # {personal, reflection, spiritual,
                                        #  identity, faith, poetry, dream}
      → single-model direct path       # "coding" is NOT in this set
  else:
      → full council path              # taken
  ▼
Council selection (not independently re-derived in this mission — the
actual selected councillors are read directly from the real log, §2b/§2c):
  qwen2.5-coder:7b, mlx:qwen3, echo:latest
  ▼
Per-councillor generation (all three raw responses recorded, all three
were_truncated: True — see §7 and §9)
  ▼
river_deliberation.py:1342 detect_full_agreement()  — task_type=="coding" only
  → returned no agreement (candidates are non-identical prose, not
    structurally-matching code) → full-agreement shortcut NOT taken
  ▼
river_deliberation.py:1403 SYNTHESIS_SYSTEM_TEMPLATE_CODING used (not the
  general SYNTHESIS_SYSTEM_TEMPLATE) — gated purely on task_type=="coding",
  with no check on whether the content is actually code (§7, §9)
  ▼
Synthesis call → synth_model = echo:latest (ECHO_SYNTHESIS_MODEL constant,
  river_deliberation.py:136, confirmed unchanged at current HEAD)
  ▼
river_deliberation.py:1445 find_missing_agreed_definitions()  — task_type
  =="coding" only → returned empty set (no code definitions to check)
  ▼
selection_method = "synthesis_accepted"  → final_response returned as-is
  ▼
routes_echo_studio.py _post_synthesis_verify() → task_type=="coding" branch
  calls code_verification.verify_response_code() — response has no code,
  so this check is a structural no-op for this turn (not independently
  re-verified in this mission; noted as a real link in the chain not
  separately traced, per the mission's "only include links actually
  verified" instruction — the log shows no caveat text appended)
  ▼
interaction_log.jsonl logged with quality_score computed by
echo_quality_scorer._score_response_quality(response, task_type="coding")
  → coding branch → _has_real_code(response) is False → returns 1
  (CONFIRMED by direct code read, §1 and §10 item 2)
```

Every arrow in this chain above the `_post_synthesis_verify()` step is backed by either a direct function call reproduction (compute_intent_heatmap, resolve_task_type) or a matching raw log record (council selection, synthesis path, selection_method). The `code_verification.verify_response_code()` no-op claim is inferred from the absence of appended caveat text in the logged response, not independently called — flagged as such per the mission's evidentiary discipline.

---

## 4. Why the classification occurred

`compute_intent_heatmap()` (`app/core/echo_model_orchestrator.py:464`) scores five task-type buckets by counting substring keyword hits in the lowercased prompt, then normalizes to a distribution. Reproduced live against the real prompt text (script excerpted, not the raw log — labeled as derived):

```
coding_keywords hits:    ['code', 'python', 'program']   → coding_score = 3
reasoning_keywords hits: ['reason', 'evaluate']            → reasoning_score = 2
personal_keywords hits:  ['yourself']                       → personal_score = 1
creative_keywords hits:  []                                 → creative_score = 0
```

Exact matched spans in the real prompt (quoted, not paraphrased):

- `"code"` × 2 — from `"...third-party C extensions loaded by generated code can execute native code below the Python monkeypatch layer..."`
- `"python"` × 1 — from the same span (`"...below the Python monkeypatch layer..."`)
- `"program"` × 1 — a substring match inside `"...what role you think intelligent programs like yourself should play..."`

**Important caveat, per the mission's explicit instruction not to over-attribute to a single keyword:** the word "program(s)" (as in "intelligent programs") appears in *every* turn of this conversation, including turns 1–4, which were correctly classified `personal`. It did not decide the classification alone. What changed turn 5's outcome was the *combined weighted density* — turn 5 is the only turn in this conversation whose text discusses the F1/F2/F3 sandbox architecture using genuinely code/security-adjacent vocabulary ("generated code," "Python," "monkeypatch layer," "static check," "kernel-level sandbox") at a density sufficient to make `coding` the plurality winner (0.4918) over `personal` (0.1639) and `reasoning` (0.3279) — comfortably above the 0.4 fallback threshold, so the heatmap's own primary was used directly rather than falling through to `detect_task_type()`'s separate keyword ladder or the learned classifier.

This is a **genuine, non-arbitrary edge case**, not an obviously nonsensical trigger: the message legitimately discusses real code-execution internals (this is precisely why it scores as code-adjacent), even though its communicative *intent* — closing with "does it change anything about how you'd answer the original question... what role you think intelligent programs like yourself should play" — is a reflective follow-up, not a request about code.

---

## 5. Why this is core rather than Studio-specific

**VERIFIED directly against current source, not assumed from the preliminary hypothesis.**

`routes_echo_studio.py:158`'s `_generate_chat_response_body(conversation_id, original_msg, mode, session)` reads `mode` (`"full"` or `"fast"`, from the request body, `routes_echo_studio.py:389/411`) and uses it for exactly one branch decision: whether to call `echo_query()` (full path — deliberation, River learning, tool dispatch) or `ollama_handler.stream_query_ollama()` directly (fast path — skips council/River/tool-dispatch entirely). `task_type` is computed independently, via `_resolve_task_type(original_msg)`, **before** that branch and is **not itself gated on `mode`** — it is passed straight into `echo_query(..., task_type=task_type, ...)` when `mode=="full"`.

`_resolve_task_type()` (`routes_echo_studio.py:67`) is a two-line, exception-guarded wrapper that does nothing except call `app.core.echo_model_orchestrator.resolve_task_type()` — the real classification logic lives entirely in core, not in this file.

**Direct evidence that the same core function serves other interfaces**, not merely a documentation claim:
- `terminal_client.py:414` — `from app.core.echo_model_orchestrator import resolve_task_type as _rtt`
- `run.py:557` — `task_type = echo_model_orchestrator.detect_task_type(msg)` (inside `mirror_echo()`)

Both call into the identical `app/core/echo_model_orchestrator.py` module Echo Studio wraps. This confirms the preliminary hypothesis stated in the mission brief: **Echo Studio's `full` mode determines that council/synthesis is *requested* when eligible (as opposed to the fast, single-model streaming path), but task-type eligibility itself, and everything downstream of it (council selection, synthesis template choice, post-synthesis integrity checks, scoring), lives in shared core files** (`app/core/echo_model_orchestrator.py`, `app/core/river_deliberation.py`, `echo_quality_scorer.py`) used identically by `terminal_client.py` and `run.py`'s `/mirror_echo`.

**What this evidence does NOT establish**, stated explicitly per the mission's instruction: this mission did not send the same or an equivalent prompt through `terminal_client.py` or `/mirror_echo` and observe a matching misclassification. The claim here is limited to: *the same classification function is called from all three interfaces*, not *the same failure was reproduced on all three interfaces*. That distinction is preserved deliberately — see §8, falsification opportunity C.

**Direct evidence mode was held constant across the whole 5-turn conversation, ruling out mode as the causal variable**: the `/tmp/echo_chat_turn.py` helper script (referenced earlier in this session, not part of this mission's evidence chain) defaults to `mode="full"` and was invoked with `mode="full"` explicitly on every one of the 5 turns, confirmed via the earlier conversational summary already in context and consistent with all 5 turns' presence in `council_deliberations.jsonl`/`interaction_log.jsonl` behaving per the `mode=="full"` code branch (turns 1, 2 routed `direct_echo_task`; turn 5 routed `real_deliberation` — both are sub-cases *within* the `mode=="full"` branch, distinguished only by `task_type`). Since `mode` never varied but routing did, `mode` is excluded as the explanation — `task_type` classification is.

---

## 6. Existing evidence — cross-referenced against current HEAD, not assumed current

### Finding 43 (CLAUDE.md) — task-type misclassification family

Finding 43's original documented bug: `compute_intent_heatmap()`'s `personal_keywords` list contained the bare word `"memory"`, which won the classification on a single occurrence and misrouted technical questions about the real FAISS/memory subsystem into `task_type=personal` — fixed 2026-07-19 by narrowing to `"your memories"`/`"do you remember"`. That specific fix is **CONFIRMED still present** in current `personal_keywords` (`app/core/echo_model_orchestrator.py:487-500`, read directly during this mission — bare `"memory"` is absent, the narrowed phrases are present).

**This turn-5 event is best described as a new instance of the same general failure family (keyword-density-based intent classification is fragile when a message's vocabulary overlaps a category its actual communicative intent doesn't belong to), but through a materially different mechanism than Finding 43's fix addressed**: Finding 43's bug fired via a bare keyword in `personal_keywords` misrouting *into* `personal`. Turn 5 fired via `coding_keywords`' combined weighted density (three separate matched terms, not one) misrouting *out of* `personal` — a different keyword list, a different direction, and (confirmed via §3/§4) decided by the heatmap's own weighted scoring directly, not `detect_task_type()`'s fallback keyword ladder that Finding 43's fix touched. Finding 43's specific fix would not have prevented this event; it targeted a different list.

### Finding 87 (CLAUDE.md) — heterogeneous synthesis lossiness

Finding 87's exact measured result, preserved without reinterpretation: pooled `BASE_N` vs `ARCH_COUNCIL` on the Tier-4 corpus, 11.9pp accuracy gap (79.8% vs 67.9%), and — the more load-bearing figure for this note — **heterogeneous Council synthesis loses ~28.6pp of underlying candidate-pool correctness at the synthesis step, vs ~15.5pp for same-model `BASE_N` synthesis** (re-scoring of captured pre-synthesis attempts, zero new model calls). This measured mechanism is a real, previously-established property of this codebase's synthesis step.

**Applicability to this specific trace, refined by the adversarial check in §7/§10**: Finding 87's own two named example failure modes (a correct class definition dropped entirely; a fabricated off-by-one injected into otherwise-identical-correct code) both describe synthesis **actively discarding or corrupting already-good candidate content**. Direct inspection of this trace's three raw pre-synthesis candidates (§7) shows they were **already generic and repetitive before synthesis touched them** — not a case of good content being lost, but plausibly a case of already-mediocre content being preserved. Finding 87's synthesis-lossiness mechanism remains a real, general property of this system and a plausible *contributing* factor (see §10, item on the coding-only synthesis template being applied to non-code content), but citing it as *the* explanation for this specific turn's degradation overstates what this trace's own raw data shows.

### Finding 88 (CLAUDE.md) — `echo:latest` reliability vs. other councillors

Finding 88's exact measured result, preserved without reinterpretation: on one specific Tier-4-derived benchmark, `echo:latest` was measured the least reliable of three real councillors (53.6% vs `qwen2.5-coder:7b` 83.3% / `mlx:qwen3` 88.1%), and RiverBrain's historical score was found to add no discriminating value once `echo:latest` is excluded from a pairwise comparison (38.9%, worse than chance) — the finding's own stated scope is that RiverBrain should be used only as a large-margin deprioritization signal, not a uniform ranker, pending a fresh out-of-sample validation that (per the finding's own text) had not been run as of Finding 88.

**One item requires a "verify against current HEAD" correction, found during this mission and not previously reflected in CLAUDE.md's own text**: `PENDING_DECISIONS.md` line 34 records that item #20 (the `select_best_fallback_candidate()` heuristic Finding 88's companion, Finding 88's neighbor "Tier-6," recommended fixing) was **built and closed on 2026-09-09** — `select_best_fallback_candidate()` (`app/core/river_deliberation.py:943`) now implements a three-stage rule (majority AST-structural agreement → RiverBrain tiebreak deliberately *not* implemented, per Tier-7's own below-chance finding → prefer-shortest, replacing the old prefer-longest), verified 96.1% correct-pick on the real Tier-4 corpus replay. Finding 88's own CLAUDE.md text ("Not yet implemented as of this entry — see PENDING_DECISIONS.md #20") is **stale relative to current HEAD** in this one respect. Not central to this trace (turn 5's `selection_method` was `synthesis_accepted`, so `select_best_fallback_candidate()` was never invoked for this event — confirmed in §2c), but flagged per the mission's explicit instruction to verify rather than assume Finding 88 remains perfectly current.

### Finding 46 (CLAUDE.md) — `echo:latest` as fixed synthesis voice

**CONFIRMED unchanged at current HEAD**: `ECHO_SYNTHESIS_MODEL: str = "echo:latest"` (`app/core/river_deliberation.py:136`), a fixed module-level constant, read directly during this mission. Finding 46's core claim — Echo's own Modelfile identity is prepended ahead of situational system content specifically and only when `model == OLLAMA_MODEL`, so other councillors are never told they are Echo — was not re-tested end-to-end in this mission (out of scope: this note is about task routing, not identity leakage), but the constant itself, which Finding 46 and this trace both depend on, is confirmed live and matches what §2b's raw log shows (`synthesis_model: "echo:latest"`).

---

## 7. Mechanism refinement (surfaced by adversarial review, not in the original mission hypothesis)

Reading the actual full text of all three raw pre-synthesis councillor responses (full text captured during this mission from `memory/council_deliberations.jsonl`, not excerpted here to control length — the note-writer read them in full; representative openings quoted below as clearly-labeled derived excerpts):

- `qwen2.5-coder:7b` (raw, truncated): *"Thank you for sharing that important context... 1. Enhancing Security... 2. Collaborative Research... 3. Auditing and Validation... 4. Transparency and Explainability..."*
- `mlx:qwen3` (raw, truncated): *"Your question is absolutely right... 1. Collaborative Problem-Solving... 2. Auditing and Validation... 3. Knowledge Dissemination... 4. Containment and Safety..."*
- `echo:latest` (raw, truncated, pre-synthesis): *"Thank you for correcting me... 1. Collaborative problem-solving... 2. Auditing and validation... 3. Knowledge dissemination..."*
- `final_response` (post-synthesis, `echo:latest`): *"...1. Collaborative problem-solving... 2. Auditing and validation... 3. Knowledge dissemination..."*

All four texts (three raw candidates, one synthesized) independently converge on the near-identical numbered list ("collaborative problem-solving," "auditing and validation," "knowledge dissemination"/variants) — including `echo:latest`'s own **raw, pre-synthesis** response, which already contains this exact three-item list before any synthesis step touched it. This is the decisive adversarial finding for §10 item 4: **the generic, templated character of the final response was already present in the raw candidate pool**, not introduced or amplified by the synthesis step discarding better content that existed. All three raw responses were also flagged `was_truncated: True` in the raw log — a separate, real confound (token-budget-under-load, the territory CLAUDE.md's own Finding 53/54 document) that plausibly compounds the generic-content effect independent of the routing question.

Separately, and independently confirmed by direct code read (§3): because `task_type=="coding"` gated the choice, synthesis for this turn used `SYNTHESIS_SYSTEM_TEMPLATE_CODING` (`river_deliberation.py:368`, `river_deliberation.py:1403`) — the template Finding 87's own refactor built specifically to **preserve code structure during synthesis of programming-language content** — applied to a response containing zero code. Whether a code-preservation-oriented synthesis prompt produces measurably different (better, worse, or neutral) results on prose content than the general `SYNTHESIS_SYSTEM_TEMPLATE` was designed for is **not established by this trace** and is listed as a falsification opportunity in §8.

---

## 8. Causal interpretation (explicit evidence tiers)

**CONFIRMED:**
- The turn was classified `task_type=coding` by `compute_intent_heatmap()`'s own weighted keyword density, reproduced live against the real prompt (§3, §4).
- This routed the turn away from the `DIRECT_ECHO_TASKS` single-model bypass and into full three-model heterogeneous council deliberation + synthesis (§2, §3).
- `echo:latest` performed the synthesis (§2b, §6).
- The turn received `quality_score=1` from `_score_response_quality()`, immediately preceded and followed by `quality_score=4` turns in the same conversation (§2a).
- The task classifier (`compute_intent_heatmap()`/`resolve_task_type()`) is shared core code, also called directly by `terminal_client.py` and `run.py`'s `/mirror_echo` (§5).
- `mode="full"` was held constant across all 5 turns of the conversation and is therefore not the variable that changed routing (§5).

**STRONGLY SUPPORTED / PLAUSIBLE:**
- The routing change plausibly contributed to a genuinely lower-quality conversational response — the response text itself (independent of any scorer) reads as more generic and less specific than the four preceding single-model turns, and the synthesized text's convergence on boilerplate is consistent with, though not fully explained by, Finding 87's general synthesis-lossiness finding.
- Model-task mismatch (a declared coding specialist, `qwen2.5-coder:7b`, participating in a council answering an off-domain reflective/policy question) is a plausible contributing mechanism, consistent with Finding 39's documented specialty-tag council-selection boost, though this mission did not independently trace the council-selection scoring call for this specific turn to confirm the tag boost was the deciding factor in *which* three models were picked.
- Applying `SYNTHESIS_SYSTEM_TEMPLATE_CODING` (a code-preservation-oriented prompt) to a non-code response is a real, confirmed mechanical consequence of the misclassification, and is plausible as a further contributing factor to the response's generic tone, though untested in isolation.

**NOT ESTABLISHED BY THIS TRACE:**
- That council/synthesis routing was the *sole* cause of the degraded response — the raw pre-synthesis candidates were already generic (§7), meaning generation-stage model/prompt mismatch is at least as plausible a contributor as synthesis-stage loss, and this trace cannot cleanly separate the two.
- That every similarly-worded reflective/security-architecture question will be misclassified the same way — this is one observed instance at one specific keyword density; the heatmap's threshold behavior across a broader input distribution was not surveyed.
- That every council-routed response is worse than a comparable single-model response — this is one paired comparison (n=1 for the "council-routed vs. direct" contrast within this conversation), not a systematic result; Finding 87's own systematic result (n=84, pre-existing) is the actual evidence base for a general synthesis-quality claim, and this trace is offered as one concrete, fresh, consistent-with instance of it, not independent proof of it.
- That Echo Studio itself caused the behavior — directly contradicted by §5's evidence that the causal mechanism (task classification) is core, shared code.
- That the `quality_score=1` reading reflects the response being conversationally worse than the `quality_score=4` turns around it, in the sense a reader would judge — **directly weakened** by §1/§10's finding that the coding-branch scorer returns 1 for any non-code response regardless of prose quality.

---

## 9. Architectural significance

The task router is not merely selecting which model answers a message. Confirmed by this trace and the code paths verified in §3: a `task_type` label change from `personal` to `coding` simultaneously and silently changes at least five independent downstream mechanisms, all gated on the same string:

1. **Cognitive architecture applied**: single-model direct response (`DIRECT_ECHO_TASKS` bypass) vs. three-model heterogeneous deliberation + synthesis.
2. **Council composition eligibility**: `task_type=="coding"` weights specialty-tagged coding models (Finding 39's `TAG_SCORE_BOOST` mechanism) into contention for this specific turn, regardless of whether the turn's actual content needs a coding specialist.
3. **Synthesis prompt strategy**: `SYNTHESIS_SYSTEM_TEMPLATE_CODING` (code-preservation-oriented) vs. the general `SYNTHESIS_SYSTEM_TEMPLATE`, gated purely on the label, not on whether code is actually present in the candidates.
4. **Post-synthesis integrity checking**: `detect_full_agreement()`/`find_missing_agreed_definitions()` (AST-structural checks) run only for `task_type=="coding"`, and are structural no-ops against prose content — they neither help nor hurt a misclassified prose turn, but they also cannot catch the kind of information loss (if any) that might occur in prose synthesis, since they were built to detect code-specific failure modes.
5. **Quality scoring rubric**: an entirely different scoring function branch (§1, §10) — AST-complexity-based for `coding`, substance/entropy/confabulation-based for `personal`/`general`/`creative`.

This is the note's central architectural observation, offered descriptively rather than as a design criticism: **a single upstream classification decision determines which entire family of downstream mechanisms — generation, selection, synthesis prompting, integrity-checking, and scoring — gets applied to a given message**, and none of those five mechanisms independently re-validates that the label they received actually matches the content they're operating on. When the label is right, this is presumably efficient specialization. When the label is wrong, as it demonstrably was for this one turn, every one of those five mechanisms operates on a mismatched assumption simultaneously, compounding rather than independently failing.

---

## 10. Adversarial checks (performed against this note's own draft interpretation, per mission instruction)

**1. Could turn 5 actually have contained code-related content that justified `coding`?**
Partially — see §4. The message genuinely, densely discusses code-execution/sandbox internals (real vocabulary: "generated code," "Python," "monkeypatch layer") in service of a security-architecture discussion. It contains zero actual code syntax and its closing sentence is an explicit reflective question, not a code request. **Verdict: a real, non-arbitrary edge case, not an obviously broken trigger — softens but does not eliminate the "misclassification" framing.**

**2. Could the 1/4 score have come from an unrelated scorer artifact?**
**Yes, decisively confirmed** — this is the most significant correction this adversarial pass produced, and it changed the report's framing (see §1). Direct read of `echo_quality_scorer.py:344-397`: the `coding`/`self_edit_coding`/`echo_projects_coding` branch is fully self-contained and never reaches the substance/penalty/scripture formula used for `personal` — it returns `1` immediately whenever `_has_real_code(response)` is `False` (`echo_quality_scorer.py:168`), independent of prose quality. Turn 5's response has no code. It would score `1` under this branch even if the prose were excellent. **Base-rate corroboration**: a frequency count of the last 500 `interaction_log.jsonl` entries by `(task_type, quality_score)` shows `quality_score=1` at `personal`: 84/223 (37.7%) and `coding`: 124/252 (49.2%) — a common, not rare, value in both buckets, further undercutting the original framing that a `1` was an exceptional, corroborating signal. **This finding directly caused a rewrite of §1's executive summary and softened §8's causal-interpretation tier for the quality-score claim.**

**3. Was `echo:latest` definitely the synthesis model?**
**Yes, CONFIRMED** — raw field `synthesis_model: "echo:latest"` in `council_deliberations.jsonl` (§2b), consistent with the fixed `ECHO_SYNTHESIS_MODEL` constant (§6).

**4. Was heterogeneous synthesis definitely invoked?**
**Yes, CONFIRMED** — three distinct models (`qwen2.5-coder:7b`, `mlx:qwen3`, `echo:latest`) recorded as councillors in two independent raw logs (§2b, §2c), `selection_method: "synthesis_accepted"` confirming a real synthesis call executed and its output was used (not a fallback substitution).

**5. Was the response generated by the same path claimed in the reconstruction?**
**Yes, CONFIRMED** — three independently-written log call sites (`interaction_log.jsonl`, `council_deliberations.jsonl`, `synthesis_integrity_log.jsonl`) agree on `trace_id`, timestamp (within 9ms), and content (matching SHA1 hashes / matching `final_response` text) for this event.

**6. Could Echo Studio's `full` mode alone explain the behavior without implicating core routing?**
**No, ruled out** — `mode="full"` was constant across all 5 turns of the conversation, yet routing (direct vs. council) varied with `task_type`. `mode` gates only the `echo_query()`-vs-`stream_query_ollama()`-fast-path choice at `routes_echo_studio.py:296`; `task_type`, computed independently, gates `DIRECT_ECHO_TASKS` eligibility inside `deliberate_and_learn()`. Direct code read (§5), not inference.

**7. Does the same routing function actually serve other interfaces?**
**Yes, CONFIRMED by direct grep/read** — `terminal_client.py:414` and `run.py:557` both call into `app/core/echo_model_orchestrator.py`'s `resolve_task_type`/`detect_task_type` (§5). **Not established**: that either interface was actually exercised with this or an equivalent prompt during this mission (explicitly not claimed, per mission instruction).

**8. Are Findings 43/87/88/46 still valid against current HEAD?**
Checked individually in §6. Findings 43 and 46 confirmed still accurate as-written. Finding 87's headline numbers are preserved without reinterpretation but its applicability to this specific trace is narrowed (§7). Finding 88's own text is now stale in one respect (the fallback heuristic it flagged as "not yet implemented" was built and closed 2026-09-09, per `PENDING_DECISIONS.md`) — not central to this trace, but noted per the mission's explicit "verify, don't assume" instruction.

**9. Is there any evidence that the observed event was previously documented elsewhere?**
A targeted search of `audits/`, `research/`, and `CLAUDE.md` for this specific `trace_id` and for the specific vocabulary of turn 5's prompt found no prior mention — this trace-id and this specific misroute event do not appear to have been documented before this note. (Not an exhaustive full-repository search; scoped to filename/grep search of the documentation directories during this mission.)

---

## 11. Falsification opportunities

Recorded per mission instruction; **none executed in this mission**.

**A vs. B — routing error as primary cause vs. response/model-specific variance:** Take the real turn-5 prompt text, hold it fixed, and run it twice more through the real pipeline with `task_type` artificially forced to `personal` (bypassing `DIRECT_ECHO_TASKS`) on one run and left at the real, misclassified `coding` value on a matched control run, holding model versions and temperature constant. If the forced-`personal` run is reliably more specific/grounded (by independent human read, not the coding-branch scorer, which cannot even score a personal-path response the same way), that isolates routing as the dominant factor. If both runs read similarly generic, the degradation is more likely upstream of routing (e.g., a property of how these particular models handle this particular prompt's content, independent of the deliberation architecture applied to it).

**A vs. C — routing error vs. some other contextual factor (e.g., conversation-position effects, this being the 5th consecutive turn in a real user_conversation session, the councillors having been "warmed up" differently, etc.):** Repeat the same forced-classification comparison at turn-1 position (fresh conversation, no prior turns) rather than turn-5 position, to rule out order/fatigue-shaped effects specific to this being a late turn in an extended exchange.

**Isolating the coding-only synthesis template's own effect:** Force a genuinely code-free prose prompt through the council path once with `SYNTHESIS_SYSTEM_TEMPLATE_CODING` and once with the general `SYNTHESIS_SYSTEM_TEMPLATE`, both under `task_type=="coding"` council composition (to hold council selection constant), to isolate whether the coding-specific synthesis prompt itself measurably changes prose-content outcomes, independent of which template's gate normally fires.

None of these were run as part of this mission, per its explicit scope.

---

## 12. Recommended disposition

**Document and monitor; do not implement a fix as part of this mission**, per the mission's own instruction. Candidate future research questions, none pursued here:

- False-positive rate of `coding` classification specifically on reflective/security-architecture conversational content (a narrower slice than "personal questions in general," given this trace's specific trigger vocabulary).
- Whether council-routed responses are systematically worse in aggregate despite individual misroutes like this one, or whether this is within-normal variance — Finding 87's own n=84 result already speaks to the general question; this trace is one fresh, consistent data point, not new systematic evidence.
- Whether `_score_response_quality()`'s hard branch-by-`task_type` design (§1, §10 item 2) should itself be revisited — a response scored under the wrong branch produces a number that looks like a quality judgment but structurally cannot be one when the label is wrong. This is arguably the most concrete, novel, and cheaply-actionable finding in this note, separate from the routing question itself.
- Whether task-classification confidence (the heatmap's own 0.4918-vs-0.4-threshold margin, already computed and already discarded after the routing decision) should be surfaced to the evaluation/logging layer, so a narrow-margin classification (like this one, which won by a real but not overwhelming margin against `reasoning` at 0.3279) is distinguishable after the fact from a confident one.
- Whether direct-vs-council selection should be experimentally A/B evaluated on held-out reflective/security-adjacent prompts specifically, given this is a demonstrated edge case in the classifier's keyword-density design.

---

## Evidence provenance note

All quoted log excerpts in this document are **derived excerpts** — read from the live, unmodified `memory/interaction_log.jsonl`, `memory/council_deliberations.jsonl`, and `memory/synthesis_integrity_log.jsonl` during this mission via read-only `grep`/Python JSON parsing, and reproduced here as text, not as file copies. The original raw files were not modified, truncated, rewritten, or normalized by this mission. Full raw candidate/synthesis text (not fully reproduced here for length) remains available at the cited `trace_id` in those three files for any future independent re-verification.

Code excerpts (`compute_intent_heatmap`'s keyword lists, `_score_response_quality`'s branch logic, `deliberate_and_learn()`'s routing sequence) are quoted from the real, current source files at the line numbers cited, read directly during this mission — not reconstructed from CLAUDE.md's prose description of them.
