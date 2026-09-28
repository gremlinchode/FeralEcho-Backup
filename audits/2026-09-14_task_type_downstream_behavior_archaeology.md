# Task-Type Framing / Downstream Behavioral Effect Archaeology (2026-09-14)

**Type:** Read-only architecture and evidence archaeology. No production code, configuration, memory, RiverBrain state, or runtime state was modified to produce this report. No new intervention experiment was executed.

**Location note:** Placed under `audits/` rather than the mission's suggested `research/` path — this repository's `research/` directory uses topic-based `ALL_CAPS.md` naming for standing research threads (`FINDINGS.md`, `OPEN_QUESTIONS.md`, etc.), while `audits/` is the established convention for dated, single-event trace/archaeology notes, which is what this is and what its direct predecessor (`audits/2026-09-14_core_task_misclassification_council_synthesis_trace.md`) used.

**Predecessor:** This mission is an explicit follow-up to that trace note (same trace_id, same day, same HEAD). Read in full before this investigation began; several of its claims are independently re-confirmed below via direct source reads rather than trusted as settled, per this mission's own Phase 9 instruction.

---

## 1. Executive conclusion

**Classification: C — BEHAVIORAL CONSEQUENCE SUPPORTED.**

Not A (task_type is demonstrably not mere descriptive metadata — see §2's model-visibility findings, which are **CONFIRMED**, not inferred). Not simply B either — B would undersell what was found here: this mission did not stop at "routing changed," it traced the actual text a model receives and found it **differs concretely** depending on `task_type`, at two independent pipeline stages, for this exact trace. Not D — no controlled, isolated comparison was run (explicitly out of scope for this mission); the causal link between the confirmed content differences and this turn's specific output character remains a supported inference, not a demonstrated result. Not E — there is far more than "insufficient evidence"; the dataflow is fully traced and several claims are pinned to exact file:line citations.

**The central finding, stated precisely:** `task_type` is not a uniform routing selector applied transparently in front of otherwise-identical model input. For this specific trace, reclassification from `personal` to `coding` changed the literal text sent to the model at **two independent, confirmed points** — a tool-availability system note that only fires for `{"coding", "reasoning"}`, and an entirely different synthesis system prompt (`SYNTHESIS_SYSTEM_TEMPLATE_CODING` vs. `SYNTHESIS_SYSTEM_TEMPLATE`) that explicitly frames the model's task as "producing the final code," gated purely on the label with no check that code is actually present in what it's synthesizing. A third mechanism (`TAG_SCORE_BOOST`) changes *which models even participate* in generation, without directly touching prompt text. These are three structurally different kinds of consequence (framing, tool-context, and participant-selection), not three restatements of the same fact — this is the report's answer to the mission's H0–H3 hypothesis set: **H3 (compound-path) is the best-supported description**, with H2 (framing) **confirmed true at specific stages** rather than merely plausible, and H1 (routing) independently confirmed at the DIRECT_ECHO_TASKS boundary.

---

## 2. Research question

> Does task-type classification itself alter downstream model treatment or behavior, beyond merely labeling the request?

Narrowed from the original, broader "was turn 5's response bad because of council routing" question the predecessor note left partially open — this mission investigates the *mechanism space*, not just this one turn's outcome.

---

## 3. Competing hypotheses (restated, with this mission's verdict on each)

- **H0 — Descriptive-only.** **REJECTED.** Falsified directly (§5, §6) — model-visible content genuinely differs by `task_type` at two points in the pipeline.
- **H1 — Behavioral-routing hypothesis** (`task_type` changes the computational pathway). **CONFIRMED.** `DIRECT_ECHO_TASKS` membership is a hard, binary gate between a 1-model and a 3-model+synthesis pathway (`river_deliberation.py:1162`).
- **H2 — Framing hypothesis** (classification itself, or task-specific prompt construction tied to it, changes what the model is asked to do). **CONFIRMED AT SPECIFIC STAGES, NOT UNIFORMLY.** True at the synthesis stage (both templates) and at the tool-context-injection stage (`TOOL_AWARE_TASKS`). **False** at the per-councillor and direct-Echo generation stage — the literal `task_type` string is passed to `_ollama_query()` there but used only for circuit-breaker bookkeeping and log lines, never concatenated into `prompt` or `system` (§5.2). This stage-dependent split is the most important nuance this mission adds beyond a blanket yes/no.
- **H3 — Compound-path hypothesis.** **BEST-SUPPORTED OVERALL DESCRIPTION.** The observed behavior is the product of at least three structurally distinct mechanisms (routing, tool-context, synthesis framing) plus one indirect mechanism (council composition via `TAG_SCORE_BOOST`), not a single cause.

---

## 4. Complete dataflow trace (Phase 1)

Traced from `resolve_task_type()`'s output through every downstream consumer found by direct source read. Classification key: **CONSEQUENTIAL** (verified to change model-visible content, generation pathway, or which models run), **CONSEQUENTIAL (non-model-visible)** (changes real system behavior but not what a model reads), **OBSERVATIONAL/LOGGING ONLY**, **DEAD** (task_type flows through the call signature but has no confirmed effect at current HEAD), **UNCERTAIN**.

| Downstream use | Classification | Evidence |
|---|---|---|
| Branch selection: `DIRECT_ECHO_TASKS` bypass vs. council | **CONSEQUENTIAL** | `river_deliberation.py:1162` — `if task_type in DIRECT_ECHO_TASKS:` — hard gate, 1 model vs. up to 3 |
| Model selection / council eligibility (`TAG_SCORE_BOOST`) | **CONSEQUENTIAL** | `river_deliberation.py:592-593` — `if task_type in model_pool.get(model, {}).get("tags", []): return base * TAG_SCORE_BOOST` (1.15×) inside `_select_council()`. Changes which models are *more likely* selected, not what any selected model is told. |
| Number of models invoked | **CONSEQUENTIAL** | Binary consequence of the branch above: 1 (direct) vs. `DEFAULT_COUNCIL_SIZE=3` (council) |
| Model roles | DEAD as a distinct axis | Only two roles exist system-wide — "synthesizer" (always `echo:latest`, `ECHO_SYNTHESIS_MODEL` constant, `river_deliberation.py:136`) and "councillor" — task_type does not create additional roles |
| Synthesis template / framing text (model-visible) | **CONSEQUENTIAL, CONFIRMED MODEL-VISIBLE** | `river_deliberation.py:1402-1406`: `if task_type == "coding": synthesis_system = SYNTHESIS_SYSTEM_TEMPLATE_CODING.format(...)`. See §5.1 for full text comparison. |
| Tool-list system note (model-visible) | **CONSEQUENTIAL, CONFIRMED MODEL-VISIBLE** | `echo_model_orchestrator.py:722`: `TOOL_AWARE_TASKS = {"coding", "reasoning"}`; `echo_model_orchestrator.py` (§5.2 below) appends a real `system_note("TOOL-LIST", ...)` to `system_parts` only when `task_type in TOOL_AWARE_TASKS` (or a separate content-based heuristic fires). This `system_parts` block becomes the `system` argument threaded identically into **every** councillor call and the synthesis call for that turn. |
| Per-councillor / direct-path prompt text | **DEAD for task_type specifically** | `_direct_response_prompt(prompt, system, max_tokens, model_name)` (`river_deliberation.py:91-122`) — takes no `task_type` argument at all; truncation is a function of `max_tokens`/`model_name`/`system` length only. The `task_type` kwarg passed to `_ollama_query()` (`river_deliberation.py:397-404`) is used exclusively for circuit-breaker scoping (`_cb_is_open`/`_cb_record_failure`/`_cb_record_success`, keyed `(model, task_type)`) and a log line — never concatenated into `prompt` or `system` (confirmed by full read of `_ollama_query()`, `river_deliberation.py:397-493`, no string interpolation of `task_type` anywhere in that function body). |
| Memory retrieval | **DEAD** | `routes_echo_studio.py:100` — `conversation_service.retrieve_memory_context(...)` runs **before** `task_type = _resolve_task_type(original_msg)` is even computed (`routes_echo_studio.py:189`), confirming this call is unconditional and cannot be gated by a value that doesn't exist yet at the point it runs. Consistent with CLAUDE.md's own physiology-audit finding (Finding 75) that memory retrieval never touches task-type classification under any code path. |
| Tool availability | **CONSEQUENTIAL (same mechanism as tool-list note above)** | Confirmed same gate, `TOOL_AWARE_TASKS`. |
| Temperature | **DEAD** | No `TASK_TEMPERATURE`-style structure found anywhere in `echo_model_orchestrator.py`, `river_deliberation.py`, or `routes_echo_studio.py` (targeted grep across all three, zero hits beyond the parameter name itself). `routes_echo_studio.py`'s `echo_query()` call site (line 306) passes no explicit `temperature`; `river_deliberation.py`'s `_jittered_temperature()` handles the resulting `None` with per-councillor jitter unrelated to `task_type`. |
| Token limits (`max_tokens`) | **CONSEQUENTIAL IN PRINCIPLE, NEAR-UNIFORM IN PRACTICE** | `_TASK_TOKEN_LIMITS` (`echo_model_orchestrator.py:1311-1320`): `personal`/`reasoning`/`general`/`creative`/`coding` are **all currently 2048** (raised to parity by CLAUDE.md Finding 65, 2026-07-21/22) — only the `autonomous_*` buckets differ (512). For *this specific trace* (turn 5 vs. turns 1-4, all within the five uniform-2048 buckets), this mechanism is real but produced **no actual difference**. Worth stating precisely: the mechanism is consequential; its current calibration happens to be a no-op for personal-vs-coding specifically. |
| Generation parameters (other) | Covered by temperature/tokens rows above | No further per-task_type generation parameter found |
| Response formatting | Folded into "synthesis template" row | `SYNTHESIS_SYSTEM_TEMPLATE_CODING`'s own instruction ("Output only the final code... with no narration") is a formatting instruction, but it is part of the same template-selection consequence already counted above, not a separate mechanism |
| Quality scoring | **CONSEQUENTIAL (non-model-visible — post-hoc only)** | `echo_quality_scorer.py:344-397` (re-confirmed present at current HEAD, matching predecessor note §1/§10): entirely separate scoring branch for `task_type in ("coding", "self_edit_coding", "echo_projects_coding")` — AST-complexity/`_has_real_code()`-gated — vs. a substance/entropy/confabulation-based formula for `personal`/`creative`/`general`/`reasoning`. This affects the RiverBrain training signal (`river_brain.learn()`) and the logged `quality_score`, not the response the user already received — it cannot have caused turn 5's content, only how that content was subsequently scored and trained on. |
| Logging / observability | **CONSEQUENTIAL (non-model-visible)** | Different `source` tag (`direct_echo_task` vs. `real_deliberation`); `synthesis_integrity_log.jsonl` entries only written for `task_type == "coding"` (`river_deliberation.py:1507-1508` — `if task_type == "coding": _log_synthesis_integrity(...)`) |
| Post-processing / verification | **CONSEQUENTIAL (non-model-visible)** | `routes_echo_studio.py:224` — `if resolved_task_type == "coding" and final: ...` gates a call into `code_verification.verify_response_code()`. Runs after the response is already generated; cannot have shaped turn 5's content, but is itself a real task_type-gated behavior. |

---

## 5. Task-type model-visibility analysis (Phase 2 — the critical gate)

This is the mission's central question. The answer is **stage-dependent**, confirmed by direct code read at each stage rather than inferred from one representative case.

### 5.1 Synthesis stage — CONFIRMED model-visible, two distinct mechanisms

**General template** (`river_deliberation.py:314-346`, `SYNTHESIS_SYSTEM_TEMPLATE`), used for `task_type` in `{personal, creative, reasoning, general}` when synthesis is reached (note: `personal` itself never reaches synthesis at all — it's in `DIRECT_ECHO_TASKS` — so in practice this template only ever fires for `creative`/`reasoning`/`general`):

```
You are Echo, the synthesis voice of a deliberative council.
Task type: {task_type}
...
```

The literal string `coding`/`creative`/`reasoning`/`general` is interpolated directly into the model's system prompt as a one-line label, verbatim.

**Coding-specific template** (`river_deliberation.py:368-393`, `SYNTHESIS_SYSTEM_TEMPLATE_CODING`), used only when `task_type == "coding"` (`river_deliberation.py:1402-1406`), and this is what fired for turn 5:

```
You are Echo, producing the final code for a coding task. Multiple
independent attempts at solving it are shown below.
...
Output only the final code, importable/runnable on its own, with no
narration about what you changed or why.

Respond now with the final code.
```

This template does **not** interpolate the literal `task_type` variable, but it is arguably a **stronger** task-type-driven framing than the general template's one-line label: the model is told outright, twice, that its job is producing code ("producing the final code for a coding task," "Respond now with the final code"), with zero verification that the candidate opinions it's being asked to synthesize actually contain code. For turn 5, they did not (§7, and re-confirmed independently below in §6). This is a real, confirmed instance of task-specific prompt construction (the mission's own H2 wording) — not merely the classification label being echoed back, but a wholesale swap of the model's instructions for the task it believes it's doing.

**Adversarial note, taken seriously rather than glossed over:** the model's own generated response ignored this instruction — it produced prose, not code, despite being told twice to output final code with no narration. This is itself evidence *against* a naive strong-framing story (if the framing fully controlled output, the response would be nonsensical code-formatted text, and it wasn't) — but it does not establish the framing had *zero* effect on tone/register; a model instructed it is "producing code" may still shift toward more clinical, listy, less exploratory prose even when it declines to literally emit code, and this mission has no way to isolate that from the model's other behavior without the controlled experiment described in §9.

### 5.2 Tool-context stage — CONFIRMED model-visible, independently verified this mission

`echo_model_orchestrator.py` (`echo_query()`, inspected directly, lines corresponding to the tool-context block cited in §4):

```python
_wants_tools_by_content = False
if task_type not in TOOL_AWARE_TASKS:
    try:
        from app.core.echo_tool_context import _needs_tool_context
        _wants_tools_by_content = _needs_tool_context(prompt)
    except Exception:
        pass
if task_type in TOOL_AWARE_TASKS or _wants_tools_by_content:
    ...
    system_parts.append(system_note("TOOL-LIST", f"Available tools: {tool_summary}."))
```

`TOOL_AWARE_TASKS = {"coding", "reasoning"}` (`echo_model_orchestrator.py:722`). This `system_parts` list is joined into `system_prompt` and threaded as the shared `system` argument into `deliberate_and_learn()`, which — per §4's "per-councillor prompt text" row — passes it **identically to every councillor and the synthesis call for that turn**. This means turn 5's council (all three raw candidates and the synthesis call) received a TOOL-LIST system note purely because `task_type` resolved to `coding`; had it resolved to `personal` (and the reflective prompt text, read on its own merits, plausibly would not trigger `_needs_tool_context()`'s separate content heuristic — not independently tested against this exact prompt in this mission, flagged as a gap), no such note would have been present. This is a second, structurally distinct, confirmed instance of task_type materially changing model-visible input — not a restatement of §5.1's synthesis-template finding.

### 5.3 Per-councillor / direct-Echo generation stage — CONFIRMED **not** model-visible

Full read of `_ollama_query()` (`river_deliberation.py:397-493`) and `_direct_response_prompt()` (`river_deliberation.py:91-122`): neither function interpolates `task_type` into any string that reaches the model. `task_type` is accepted as a parameter and used exclusively for circuit-breaker state keying and a `logging.warning()`/`logging.debug()` line. This is the one stage where the mission's H0 (descriptive-only) genuinely holds — task_type is metadata at this specific point, not framing.

**Net answer to Phase 2's gate question:** task_type is model-visible, and does change task-specific instruction text, at the synthesis and tool-context stages; it is pure non-model-visible bookkeeping at the generation stage. A blanket "yes" or "no" to Phase 2 would have been wrong in either direction — the accurate answer requires the stage breakdown above.

---

## 6. Personal/direct path vs. coding/council path — side-by-side table (Phase 3)

Built from source evidence only; `UNKNOWN` used where evidence is genuinely insufficient, per mission instruction.

| Stage | Personal/direct path (turns 1–4) | Coding/council path (turn 5) |
|---|---|---|
| Classifier result | `heatmap["personal"]` won (turns 1–2 logged `personal`); exact heatmap scores for turns 1–4 not independently reproduced in this mission (predecessor note only reproduced turn 5's heatmap live) — **UNKNOWN, not re-derived here** | `coding=0.4918` vs. `reasoning=0.3279`, `personal=0.1639` — reproduced live by the predecessor note; not independently re-run in this mission, cited as already-CONFIRMED |
| Routing branch | `DIRECT_ECHO_TASKS` bypass (`river_deliberation.py:1162`) | Full council path (same file, `else` branch) |
| Models invoked | 1 (`echo:latest`, as `synth_model`, no distinct "councillor" role) | 3 (`qwen2.5-coder:7b`, `mlx:qwen3`, `echo:latest`), confirmed via `council_deliberations.jsonl`/`synthesis_integrity_log.jsonl` raw records (predecessor note §2b/§2c) |
| Context (`system` block) | Same shared assembly logic in `echo_query()` (EPISTEMIC-NOTE, circadian, stillness, temporal, scripture) minus the TOOL-LIST note (task_type not in `TOOL_AWARE_TASKS`, and a reflective/policy prompt is not independently confirmed in this mission to trigger `_needs_tool_context()`'s content heuristic — **UNKNOWN**, not tested) | Same shared assembly **plus** a TOOL-LIST system note (§5.2), CONFIRMED present via the `task_type in TOOL_AWARE_TASKS` gate |
| Prompt/framing (councillor-facing) | Identical mechanism to coding path — `_direct_response_prompt()`, no task_type text (§5.3) | Identical mechanism — no task_type text at this stage either (§5.3); the *difference* between the two paths at generation time is entirely the shared `system` block's TOOL-LIST note, not the per-model prompt construction itself |
| Memory | Same call, prior to task_type resolution (§4) — no difference | Same |
| Council | N/A — no council selection runs | `_select_council()` invoked; `TAG_SCORE_BOOST` (1.15×) applies to any candidate model whose declared tags include `"coding"` — `qwen2.5-coder:7b`'s presence in the actual selected council is consistent with, though not independently re-derived as *caused by*, this boost in this mission (the boost is real and CONFIRMED to exist and apply to this task_type; whether it was the deciding factor in this specific selection was not re-traced, matching the predecessor note's own stated limit) |
| Synthesis | **Does not run** — direct path returns the single model's response as final (`river_deliberation.py:1166-1200`) | Runs, using `SYNTHESIS_SYSTEM_TEMPLATE_CODING` (§5.1), CONFIRMED |
| Generation parameters | No task_type-gated temperature/token difference in practice (§4) | Same |
| Scoring | `_score_response_quality(response, task_type="personal")` — substance/entropy-based branch | `_score_response_quality(response, task_type="coding")` — AST/`_has_real_code()`-gated branch, returns `1` unconditionally for any response with no code (re-confirmed present, `echo_quality_scorer.py:344-397`, matching predecessor note) |

---

## 7. Counterfactual replay feasibility (Phase 4 — design only, not executed)

**Direct re-invocation of the real turn-5 prompt with `task_type` forced to `personal`, run live against the actual pipeline, was considered and explicitly NOT performed in this mission**, per the mission's own constraint ("do not run a new intervention experiment unless it can be performed entirely read-only and without changing persistent state; if a valid counterfactual experiment would require mutation, stop and design it instead").

**Why a live re-invocation would mutate state, concretely, based on the code just traced:**
- `deliberate_and_learn()`'s direct path unconditionally calls `river_brain.learn(synth_model, task_type, response)` (`river_deliberation.py:1175`) before returning — a real, persistent write to the live RiverBrain singleton (and, per CLAUDE.md's own documented Tier-8/Finding 89 forensic history, `RiverBrain`'s background `_writer_thread` persists to `memory/river_brain.pkl` on a fixed ~60s timer regardless of whether an isolation proxy is used, unless the specific `RIVER_BRAIN_PATH`-redirection-before-first-`get_river_brain()`-call pattern documented in that finding is applied).
- The direct path also calls `_log_council_deliberation(...)` (`river_deliberation.py:1184`), a real append to `memory/council_deliberations.jsonl`.
- The council path additionally writes `memory/synthesis_integrity_log.jsonl` (task_type=="coding" only) and, at the `routes_echo_studio.py` layer, `memory/interaction_log.jsonl`.
- None of these writes are optional parameters that can be suppressed by the caller without either (a) building a new isolation harness (explicitly disallowed — "do not create new infrastructure during this mission") or (b) accepting genuine production-state mutation (explicitly disallowed by the mission's mutation constraints).

**Confounds a future controlled replay would need to isolate, per the mission's own checklist, each independently assessed against this specific case:**
- **Model stochasticity** — real risk. Turns 1–4 and turn 5 already show real per-call variance (different councillor temperatures via `_jittered_temperature()`); any re-run, even with identical `task_type`, would not reproduce byte-identical output. A controlled comparison needs multiple trials per condition, not n=1 per side, to distinguish a routing effect from ordinary sampling noise — exactly the lesson this project's own Tier-3/Tier-4 capability research (CLAUDE.md Findings 87/88) already learned the hard way (a 37.5pp pilot effect that shrank to 11.9pp, non-significant, on confirmatory replay).
- **Model version drift** — lower risk over the short timescale of a same-day replay, but real over any longer window; not applicable to a same-session comparison.
- **RiverBrain/memory state** — real risk, per the mutation analysis above; any live replay changes the very state that future council-selection scoring depends on, and (worse) risks corrupting the answer to whether `TAG_SCORE_BOOST`/model-selection would behave identically on a second run, since `river_brain.learn()` calls from the first replay attempt would already have altered `model_task_stats` before a second attempt ran.
- **Council-selection randomness** (`exploration_bias`, `fair_sample_refresh` in `_select_council()`) — real, independent source of run-to-run council-composition variance, separate from per-councillor temperature.
- **Cache/warm-up state** (`_warm_up_echo()`, GPU memory eviction noted in the code's own comments) — plausible confound if trials aren't spaced/ordered carefully.
- **Timestamps/environment** — low risk for a same-session comparison.
- **Task-order effects** — real and directly relevant: this mission's own predecessor note flagged (§11, falsification opportunity "A vs. C") that turn 5 was the *fifth* consecutive turn in a real extended conversation, and that repeating the comparison at turn-1 position would help rule out conversation-position/fatigue effects specific to this trace.

**Conclusion: a genuine counterfactual replay of this specific historical event is not feasible without either new isolation infrastructure or accepted production contamination, and is therefore correctly out of scope for this mission.** A well-designed future experiment is described in §9, matching the pre-existing isolation pattern this codebase already built and verified for an analogous purpose (Finding 89's `RIVER_BRAIN_PATH` redirection), rather than inventing a new approach.

---

## 8. Historical false-positive archaeology (Phase 5)

Sampled from the real, live `memory/interaction_log.jsonl` (20,213 lines at time of this mission), filtered to `source == "user_conversation"` (real human-facing turns, excluding autonomous-loop and self-edit-loop entries per this repo's own documented multi-source log-mixing — CLAUDE.md's "Autonomous Background Path" section).

**Method (explicitly a crude proxy, stated plainly):** a response is flagged "looks like code" if it contains a fenced code block (`` ``` ``) or a line starting with `def `, `class `, `import `, or `from ... import`. This will under-count genuine code presented without fencing or using other constructs, and is not the same function as `echo_quality_scorer.py`'s own `_has_real_code()` (not independently re-implemented here to avoid drift between two similarly-named-but-different heuristics — flagged as a limitation, not silently equated).

**Result, `task_type == "coding"`, real conversational turns (n=23 total in the sampled log):**
- 22 of 23 (95.7%) show no code by this proxy.
- Manually reading the prompt text of 8 sampled no-code-detected entries (quoted, not paraphrased, as derived excerpts) shows a real mix, consistent with the predecessor note's own "genuine edge case, not an obviously broken trigger" framing for turn 5 specifically:
  - Several are genuinely technical/hardware-adjacent (host-capability audits, environment dumps: *"FERALECHO HOST ──────... Platform: Apple Silicon MacBook Air..."*) — plausibly defensible as coding-adjacent even without literal code.
  - Several are clearly non-technical, identity/continuity-shaped questions with essentially no code vocabulary: *"Who or what determines your primary function and why?"*; *"When you say that your continuity and coherence 'feel like a genuine experience,' what specifically..."* — these read as closer to Finding 43's original failure family (personal/reflective content misrouted) than to a defensible edge case.

**For comparison, `task_type == "personal"` real conversational turns in the same window: n=150** — an order of magnitude more common than `coding`, consistent with this being genuinely rare, high-consequence misfire territory rather than routine routing.

**Interpretation, held to the mission's explicit standard against weak estimates:** this is a real, non-trivial base rate (roughly 95% of real conversational turns classified `coding` in this sample contain no detectable code), not a one-off. It is **not** presented as a precise, generalizable false-positive rate — n=23 is a small sample, the code-detection proxy is crude and likely undercounts genuine code, and no attempt was made to independently judge each of the 23 turns' actual communicative intent (only 8 were manually read). This is reported as **directionally strong, quantitatively approximate** evidence that `coding` classification on this system's real conversational traffic frequently — plausibly usually — does not correspond to an actual coding request, which is the specific, cautious framing the mission's Phase 5 instruction calls for ("if the available corpus is insufficient to estimate a meaningful rate, report UNKNOWN" — this corpus is small but not insufficient to support a directional claim; a precise rate would be overclaiming, so none is given).

---

## 9. Adversarial falsification (Phase 6 — mandatory, attempted in earnest)

**Attack 1 — task_type only selects a label.**
**FAILS.** Directly falsified by §5.1/§5.2: two independent, confirmed mechanisms put task-specific text into the model's actual input, not just a routing decision behind the scenes.

**Attack 2 — the same model receives effectively identical instructions regardless of classification.**
**FAILS for the synthesis and tool-context stages; HOLDS for the per-councillor/direct-generation stage.** This is the mission's most important nuanced result — the attack does not uniformly fail or succeed across the whole pipeline, and reporting it as one or the other would misrepresent the evidence. See §5.3 for where it genuinely holds.

**Attack 3 — council participation does not meaningfully alter the computational path.**
**FAILS.** `DIRECT_ECHO_TASKS` membership is a hard binary gate (§4, §6) — 1 model with no synthesis vs. 3 models with a full synthesis call is definitionally a different computational path, independent of any content-level framing question.

**Attack 4 — no task-specific framing reaches the model.**
**FAILS**, same evidence as Attack 1/2.

**Attack 5 — any observed response differences are adequately explained by stochastic generation.**
**CANNOT BE RULED OUT, AND THIS MISSION DOES NOT CLAIM TO RULE IT OUT.** This is the one attack that genuinely survives, in the following precise sense: this mission establishes that the model-visible *input* differs by task_type (a fact about the pipeline, confirmed), not that the *output* difference observed in this one turn (turn 5's generic tone) is attributable to that input difference rather than to sampling variance, model-task mismatch at generation, or the pre-existing generic character of all three raw candidates (independently re-confirmed below, §10). No controlled, multi-trial comparison was run (§7 explains why not). This is exactly why the report's final classification is **C (supported)**, not **D (verified)** — Attack 5 is what keeps it at C.

**Attack 6 — the September 14 event is merely an artifact of the scorer.**
Already resolved by the predecessor note (`quality_score=1` is a real scorer artifact, not evidence of degraded content — re-confirmed live in this mission, §4's "quality scoring" row, same file/lines). This attack succeeds specifically against the *scorer-as-evidence* claim, which the predecessor note already retracted — it does **not** succeed against this mission's separate, independently-derived model-visibility findings, which do not depend on the scorer at all.

**Attack 7 — the apparent routing difference is cosmetic rather than computational.**
**FAILS**, same evidence as Attack 3 (a 1-model vs. 3-model+synthesis pathway is not cosmetic by any reasonable definition) plus Attack 1/2's model-visible content differences.

**Verdict: the hypothesis that task_type is behaviorally consequential survives every attack except Attack 5, and Attack 5's survival is precisely why the causal claim about *this specific turn's output quality* is held at SUPPORTED rather than VERIFIED — while the narrower, prior claim that task_type materially changes model-visible input and computational pathway is held at CONFIRMED, because that claim does not depend on Attack 5's unresolved question at all.**

---

## 10. Relationship to Findings 43/46/87/88

Findings 43, 46, and the `ECHO_SYNTHESIS_MODEL` constant central to Finding 46 were independently re-confirmed against current HEAD during this mission's own source reads (same file:line locations the predecessor note cites: `personal_keywords` at `echo_model_orchestrator.py:487-505` with bare `"memory"` still absent; `ECHO_SYNTHESIS_MODEL: str = "echo:latest"` at `river_deliberation.py:136`) — both **hold, unchanged**, consistent with the predecessor note's own conclusion. This mission did not find any contradiction requiring a correction to either.

Finding 87's synthesis-lossiness mechanism is **not directly re-tested** in this mission (this mission's own scope is the dataflow/framing question, not a repeat of Finding 87's own statistical work) — its numbers are cited in the predecessor note without reinterpretation and are not touched here.

Finding 88's `PENDING_DECISIONS.md` #20 status (built/closed 2026-09-09, per the predecessor note) was not independently re-verified a second time in this mission — no new evidence surfaced that would change it, and re-deriving an already-independently-confirmed fact a second time in the same investigation lineage would not add information.

**No contradiction between this mission's findings and the predecessor note's Findings cross-reference was identified.** This mission's contribution is additive (the model-visibility dataflow trace, the false-positive base-rate estimate, the formal adversarial-falsification pass) rather than corrective of the predecessor note's own Finding cross-references.

---

## 11. Updated interpretation of the September 14 trace

The predecessor note's own "DO NOT ASSUME" list (its §8/Phase 8, reproduced in the mission brief) is **re-evaluated, not superseded**, against this mission's new evidence:

- *"The council caused the generic response"* — **still not established**, and this mission adds a reason why it may never be cleanly establishable from this one trace alone: even setting aside stochastic variance, the council path changed model-visible input in a specific, identifiable way (the TOOL-LIST note, the coding-synthesis framing) — so "the council" is not one variable but at least two independently-confirmed content differences plus one participant-selection difference, any subset of which could have contributed.
- *"Synthesis caused the generic response"* — **still not established**, and independently re-weakened by this mission's own re-confirmation (not new evidence, restating the predecessor's own §7 finding) that the raw pre-synthesis candidates were already generic.
- *"The model was objectively worse"* — **still not established** by this mission, no new evidence bears on this.
- *"The quality score represents semantic response quality"* — **still directly contradicted**, re-confirmed by this mission's own independent read of `echo_quality_scorer.py:344-397`.
- *"Echo Studio caused the behavior"* — **still directly contradicted**; this mission adds further, more granular confirmation that the causal mechanisms (TOOL_AWARE_TASKS, SYNTHESIS_SYSTEM_TEMPLATE_CODING, DIRECT_ECHO_TASKS, TAG_SCORE_BOOST) are all defined in `app/core/echo_model_orchestrator.py`/`app/core/river_deliberation.py`, not `routes_echo_studio.py`.

**What genuinely changes**, and is new to this mission rather than a restatement: the predecessor note treated "did the routing change matter" as still-open at the level of a plausible-but-unconfirmed mechanism. This mission confirms that the routing change **did** materially alter the model's actual input on this turn (§5.1, §5.2) — that specific narrower claim moves from SUPPORTED to CONFIRMED. What remains at SUPPORTED, unchanged, is the further, larger claim that this confirmed input difference is *why* the output read as generic, as opposed to the independently-confirmed pre-existing genericness of the raw candidate pool, or ordinary model/prompt variance.

---

## 12. Evidence classification summary

**CONFIRMED:**
- `task_type` is a hard, binary gate between a 1-model direct path and a 3-model+synthesis council path (`DIRECT_ECHO_TASKS`, `river_deliberation.py:1162`).
- The literal string `task_type` is interpolated directly into the model-visible synthesis system prompt for the general template (`personal`/`reasoning`/`creative`/`general` synthesis path — though `personal` itself never reaches this path).
- A structurally different, model-visible synthesis system prompt (`SYNTHESIS_SYSTEM_TEMPLATE_CODING`) is used specifically and only for `task_type == "coding"`, explicitly framing the task as code production regardless of whether the candidates contain code.
- A model-visible TOOL-LIST system note is appended, identically to every councillor and the synthesis call, only when `task_type in {"coding", "reasoning"}`.
- Per-councillor and direct-path generation prompts do **not** contain task_type-derived text — task_type is non-model-visible bookkeeping at this specific stage only.
- Memory retrieval and temperature are not task_type-gated anywhere in the traced call paths.
- Token limits are task_type-gated in principle but currently uniform (2048) across all five non-autonomous task types, producing no actual difference for this trace.
- Quality scoring uses an entirely different formula depending on `task_type`, but only after generation — it cannot have caused this turn's content.
- `quality_score=1` for a coding-classified, code-free response is a structural scorer artifact, independent of prose quality (re-confirmed, not new to this mission).
- 22 of 23 real, sampled `task_type=="coding"` conversational turns show no detectable code by a stated (crude) proxy — a real, directionally strong pattern, not precisely quantified.

**SUPPORTED / PLAUSIBLE:**
- The confirmed model-visible input differences (§5.1, §5.2) plausibly contributed to turn 5's generic response character.
- `qwen2.5-coder:7b`'s presence in the actual selected council is consistent with `TAG_SCORE_BOOST` having influenced selection, though not independently re-derived as the deciding factor for this specific turn.

**NOT ESTABLISHED:**
- That the confirmed input differences, rather than stochastic variance or pre-existing generic-candidate content, are what actually produced turn 5's specific output character (Attack 5, §9).
- A quantified, generalizable false-positive rate for `coding` misclassification (only a directional estimate is offered, §8).
- That every reflective/security-adjacent message will be misclassified the same way, or that every council-routed response is worse than a comparable direct response — both explicitly out of scope, matching the predecessor note's own stated limits.

**UNKNOWN:**
- Turns 1–4's exact heatmap scores (not independently reproduced in this mission).
- Whether the turn-5 prompt, if it had resolved to `personal`, would independently have triggered `_needs_tool_context()`'s content-based tool-awareness exception (not tested).

---

## 13. Recommended next experiment (design only, not executed)

Matching the mission's own constraint list precisely:

**Fixed:** the exact real turn-5 prompt text (available verbatim in `memory/interaction_log.jsonl`); model versions (pinned by explicit model-name string, e.g. `qwen2.5-coder:7b`); the shared `system` block content (EPISTEMIC-NOTE/circadian/stillness/temporal/scripture — reconstructible from the same call chain, everything except the TOOL-LIST note itself, which is precisely the variable being isolated); generation seed/temperature schedule (use `_jittered_temperature()`'s own deterministic-per-index behavior, not a fresh random draw, so both conditions get matched per-councillor temperatures).

**Varied:** `task_type` only — one run set with the real, misclassified `coding` value (reproducing the TOOL-LIST note and `SYNTHESIS_SYSTEM_TEMPLATE_CODING`), one run set with `task_type` forced to `personal` routed through the **council path artificially** (not `DIRECT_ECHO_TASKS`, to hold the "does synthesis run at all" variable constant and isolate specifically the TOOL-LIST/template framing effect from the separate 1-model-vs-3-model effect) — this decomposes the compound effect (H3) into its two confirmed sub-mechanisms rather than testing them conflated, as a live re-run at real `personal` classification would (since real `personal` also triggers `DIRECT_ECHO_TASKS`).

**Isolation requirement:** this must reuse, not reinvent, this codebase's own already-built-and-verified isolation pattern — Finding 89's `RIVER_BRAIN_PATH` redirection before the first `get_river_brain()` call (`scripts/run_capability_pilot.py`'s `install_isolation()`), extended to also redirect `_COUNCIL_DELIBERATION_LOG`/`_SYNTHESIS_INTEGRITY_LOG`/`interaction_log.jsonl`'s write targets to scratch copies for the duration of the run. Building this extension is itself new infrastructure and was correctly out of scope for this mission.

**Sample size:** per the predecessor note's own citation of this project's Tier-3→Tier-4 experience (a 37.5pp pilot effect collapsing to 11.9pp, non-significant, on confirmatory replay at n=84), a single paired trial (n=1 per condition, which is all this mission's own historical trace provides) is not sufficient to distinguish a real framing effect from sampling noise — at minimum a double-digit trial count per condition, ideally with a pre-registered scoring rubric that is **not** `echo_quality_scorer.py`'s own task_type-branching function (since that function is precisely one of the mechanisms under test, and using it to score the test would be circular).

**Not run in this mission.**

---

## 14. What was NOT investigated / cannot be established from this mission

- No live re-invocation of any real or reconstructed prompt was performed, at any classification.
- `_needs_tool_context()`'s actual behavior against the real turn-5 prompt text was not independently called/tested.
- Council-selection scoring for the specific three models chosen in the real turn-5 event was not re-derived from `_select_council()`'s live inputs; the `TAG_SCORE_BOOST` mechanism's *existence and applicability* is confirmed, its role as the specific deciding factor in this one selection is not.
- Finding 87's own statistical claims were not re-run or re-verified beyond citing them as unchanged from the predecessor note's citation of them.
- No claim is made about `terminal_client.py` or `/mirror_echo` actually reproducing this or an equivalent misclassification in practice — only that they call the identical core classification function (already established by the predecessor note, not re-tested here).
- The historical false-positive base rate (§8) is directional, not a precise, defensible statistic — no claim beyond "real and non-trivial" is made.
