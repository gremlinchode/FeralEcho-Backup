# FeralEcho: Tier-3 `ARCH_PIPELINE` Isolation — Surgical Experimental Correction

**No held-out task was executed, inspected beyond existence/hash/integrity metadata, or modified. No fine-tuning
occurred. Production self-edit behavior, `echo_model_orchestrator.py`, `river_deliberation.py` are all completely
untouched. `self_edit_manager.py` was not modified — only two of its existing constants (`CODE_OUTPUT_RULES`,
`SELF_EDIT_FILE`) are imported (read-only) by the harness, exactly as its own `generate_code_from_plan()` already
does internally.** The only file changed is `scripts/run_tier3_apparatus.py` (the Tier-3 experimental harness
itself). No historical data was deleted or rewritten — three archived files, one already-frozen historical
results file, and this report together preserve every prior observation exactly as it was recorded.

## 1. Exact Previous Production Call Path

`run_condition_arch_pipeline(task)` → `self_edit_manager.generate_code_from_plan(task["prompt"], temperature=0.0)`
→ `echo_model_orchestrator.echo_query(code_prompt, task_type="coding", temperature=temperature)` (no `use_all`
argument passed, defaults to `False`) → the `if not use_all:` branch (`echo_model_orchestrator.py:1525`)
unconditionally calls `river_deliberation.deliberate_and_learn(prompt=code_prompt, task_type="coding",
river_brain=get_river_brain(), model_pool=MODEL_POOL, ..., max_tokens=_TASK_TOKEN_LIMITS.get("coding", 1024),
...)`. `"coding"` is not in `river_deliberation.DIRECT_ECHO_TASKS = {"personal", "reflection", "spiritual",
"identity", "faith", "poetry", "dream"}`, so the direct-Echo bypass never fires — every real `ARCH_PIPELINE`
generation invoked the full council path: `_select_council()`/`rank_models()` pick 3 real councillors from the
live, unpinned model pool, each is queried independently, and `echo:latest` synthesizes their opinions into the
final response.

**Directly confirmed live**, not just re-derived from source, during this mission's own fresh dev-sanity run
(prior to the fix): task_12's `ARCH_PIPELINE` candidate showed, in the real process log:
```
[DELIBERATION] Council for task=coding: ['qwen2.5-coder:7b', 'mlx:qwen3', 'echo:latest']
[DELIBERATION] Sending 3 opinions to echo:latest for synthesis
[DELIBERATION] Synthesis complete | council_size=3 | synth_model=echo:latest
```
while the harness recorded `model_used="qwen2.5-coder:7b"` (a label from `generate_code_from_plan()`'s own,
separate, non-generating `choose_model()` call, used only for RiverBrain bucket attribution) and `total_calls=1`
(a hardcoded literal at the old `scripts/run_tier3_apparatus.py:524`, never a measured count). Real generation
times under the old path (32.83s / 37.37s across the two development tasks) were consistent with a genuine
multi-call council, not a single call — `BASE_1`'s real single calls completed in 2.69s / 6.6s on the same
development tasks under the same run.

**Scope of the defect, confirmed across the whole project, not just the current harness**: the *original*
3-condition pilot (`scripts/run_capability_pilot.py`)'s own condition `B` (`run_condition_b_pipeline()`) calls
`generate_code_from_plan()` the identical way, and therefore carries the identical confound — 9 historical
records, `audits/capability_pilot/raw_results.jsonl`. This pilot never had model pinning at all (its own
`model_used` values span `echo:latest`, `llama3:instruct`, `llama3.2:3b`, `qwen2.5-coder:7b` across its 9 `B`
records) — a second, independent, already-documented confound this finding compounds rather than introduces.

## 2. Exact New Experimental Call Path

`run_condition_arch_pipeline(task, pinned_model)` → builds `code_prompt` by reproducing
`generate_code_from_plan()`'s own real prompt-construction shape exactly (`CODE_OUTPUT_RULES` + the live contents
of `self_edit_generated.py` + `"Plan to implement:\n{task['prompt']}"`) → calls
`river_deliberation._ollama_query(pinned_model, code_prompt, temperature=0.0, max_tokens=MAX_TOKENS,
task_type="coding")` directly — the exact same low-level mechanism `run_condition_base1()` uses, not a second,
independent implementation. `scan_for_unsafe_operations()` (F1) is retained as an observational, non-gating
check, matching the prior implementation's own behavior and real self-edit's own pipeline. No `echo_query()`, no
`deliberate_and_learn()`, no council, no live `choose_model()`-driven model selection, no reachable production
RiverBrain/interaction-log/reflection/memory writes. The arm is labeled `ARCH_PIPELINE_ISOLATED` in all new data
(`randomized_arm_order()`'s arm list and the dispatch in `_run_single_candidate()`) — kept as a distinct string
specifically so historical `ARCH_PIPELINE`-labeled records and new `ARCH_PIPELINE_ISOLATED`-labeled records can
never be silently conflated by a future reader filtering on arm name.

## 3. Context/Prompt Equivalence Table

| Attribute | BASE_1 | ARCH_PIPELINE (old, confounded) | ARCH_PIPELINE_ISOLATED (new) | Difference vs. BASE_1 | Intentional? |
|---|---|---|---|---|---|
| Model | pinned model | cosmetic label only — real generation used an unpinned, live-selected 3-model council | pinned model, **verified as the real generating model**, not a label | none | Yes — parity is the point |
| System prompt | `None` | `None` explicitly, but `echo_query()`'s own `system_parts` (see below) traveled as the `system=` argument to `deliberate_and_learn()` | `None` (no `system=` argument passed, matching `BASE_1` exactly) | none | Yes |
| Hidden system-role content injected by wrappers | none | `EPISTEMIC-NOTE` (unconditional), plus conditionally `CIRCADIAN-STATE`/`STILLNESS-STATE`/temporal-weather/scripture/`TOOL-LIST` (since `"coding"` ∈ `TOOL_AWARE_TASKS = {"coding","reasoning"}`) — all from `echo_query()`'s own assembly | none — this call path never reaches `echo_query()` | current: several hidden notes; isolated: none | Removing them is intentional and correct — none of that content is part of "self-edit's own framing," it is `echo_query()`'s own general-purpose conversational scaffolding |
| User/task prompt | `task["prompt"]` verbatim | `CODE_OUTPUT_RULES` + live `self_edit_generated.py` contents + `"Plan to implement:\n{task['prompt']}"` (the raw task substituted directly as "plan" — `plan_code_logic()`, self-edit's real planning step, is never called by either the old or new implementation) | identical framing to the old path's prompt construction — this is the **one intended difference under test** | `CODE_OUTPUT_RULES` + file contents + wrapper text | **Yes — this is the self-edit generation mechanism being isolated** |
| `CODE_OUTPUT_RULES` | absent | present (10 numbered output-format rules; rule 10 is specific to self-edit's own `apply_to_code` naming convention and is irrelevant to every task in this study) | present, unchanged | present vs. absent | Yes, intentional |
| Live `self_edit_generated.py` contents | absent | present, 2,324 characters at the time read (a `HealthMonitor` class, a `log_call` decorator, a duplicated/broken `run_code_generator` — real, accumulated self-edit output) | present, unchanged | present vs. absent | Yes, intentional — **but see §Step-1-finding below: checked directly for task-relevant information advantage, none found** |
| `plan_code_logic()` (self-edit's real planning step) | n/a | never called by either implementation | unchanged (still never called) | n/a | Disclosed limitation, not newly introduced: neither the old nor the new `ARCH_PIPELINE` exercises self-edit's real planning step — both test only the generate-from-plan step, with the raw task description standing in for a plan |
| Temperature | 0.0 | 0.0 | 0.0 | none | Yes |
| `max_tokens` | `MAX_TOKENS` (2048), explicit | 2048 via production's own `_TASK_TOKEN_LIMITS["coding"]` default — numerically equal, but incidentally so, never explicitly passed by the harness | `MAX_TOKENS` (2048), explicitly passed by the harness — **verified equal by direct measurement, see §6** | none numerically, but now structurally guaranteed rather than incidental | Yes |
| Context length (`num_ctx`) | 8192 (flat constant, model-agnostic) | 8192 (same flat constant) | 8192 | none | n/a — already identical, confirmed by direct source read (`app/ollama_handler.py`) |
| Retry behavior | none | none (`generate_code_from_plan()` has no internal retry; `execute_self_edit()`'s real single-retry-on-sandbox-failure mechanism is a separate function, never called by either implementation) | none | none | n/a |
| Number of real inference calls | 1 | **actually 4** (3 councillors + 1 synthesis), reported as 1 | **1, measured, not assumed** — see §6 | current: +3 hidden calls (the entire defect); isolated: 0 | Fixed |
| Synthesis | none | real (`echo:latest` synthesizing 3 councillors' opinions) | none | current: yes; isolated: none | Fixed |
| Tool-list access | none | possible (`TOOL-LIST` system note when `task_type ∈ TOOL_AWARE_TASKS`, which `"coding"` is) | none (this call path never reaches `echo_query()`, the only place that injects it) | current: possible hidden tool-name text; isolated: none | Fixed |
| Memory/RAG access | none | none — `echo_query()`'s own assembly never calls `retrieve_relevant_memories()` (confirmed by direct read of its full body; that function is only called by other, separate callers such as `terminal_client.py`) | none | none | n/a, already equivalent |
| RiverBrain access | none (a pure `_ollama_query()` call has no learning side effect) | real attempts (`get_river_brain().learn(...)` inside both `echo_query()` and `deliberate_and_learn()`), correctly intercepted by the harness's existing isolation proxy | none — **verified 0 side-effect attempts, not merely 0 successful writes, see §8** | current: real attempted writes (blocked); isolated: no attempt at all | Fixed, and strictly cleaner than before |
| Model selection | fixed at the pin (`self_edit_manager.choose_model` patched) | the pin was **cosmetic** — real councillor selection came from `deliberate_and_learn()`'s own `_select_council()`/`rank_models()`, entirely unaffected by the patched `choose_model` | fixed and real — the pinned model is passed directly to `_ollama_query()`, with no `choose_model()` call anywhere in this path at all | current: pin ineffective; isolated: pin effective and verified | Fixed |
| Production-state access | none | reads the live `self_edit_generated.py` (see above) | same, unchanged | none new | Intentional/disclosed |

## 4. Differences Between BASE_1 and ARCH_PIPELINE_ISOLATED

Exactly one substantive difference remains, by design: the **self-edit-specific framing/context**
(`CODE_OUTPUT_RULES` + the live `self_edit_generated.py` contents + the wrapper text around the task prompt).
Every other attribute in §3 is now identical or structurally guaranteed identical (model, temperature,
`max_tokens`, context length, call count, retry behavior, tool/memory/RiverBrain access).

## 5. Why Each Difference Is Intentional

The self-edit framing difference is the entire point of this arm — it is what "isolating the self-edit
generation mechanism" means. Everything else that used to differ (hidden council calls, hidden system notes,
tool-list injection, an ineffective model pin) was never part of any stated intervention; each was a genuine
confound, now removed. **Step-1 finding, reported explicitly per this mission's own instruction, not silently
normalized away**: the live `self_edit_generated.py` content (2,324 characters, read directly and reproduced in
full in this mission's own working notes) was checked line-by-line for anything that could give
`ARCH_PIPELINE_ISOLATED` an unfair, task-relevant advantage over `BASE_1` on the actual tasks in this study
(interval merging, LRU caching, token buckets, run-length encoding, circular-array traversal, permission lookup,
coin-change DP, binary search, prose-stripping). **None was found** — the file's real content (a `HealthMonitor`
class, a `log_call` logging decorator, a duplicated and internally-broken `run_code_generator`/
`generate_and_modify_code` pair) is unrelated, disclosed noise, not task-relevant signal. If anything, its
inclusion very plausibly **dilutes or distracts** rather than helps (a live demonstration of exactly this
occurred during this mission's own verification run: given a trivial `add_one(x)` task, the pinned model's real
output under this framing was `# def add_one(x: int) -> int:\n#     return x + 1` — the entire function commented
out, a real, observed failure mode, not a hypothetical one). **One real, disclosed, NOT-newly-introduced
limitation, reported rather than hidden**: this file is the live, continuously-self-edited production file, not
a frozen artifact — its exact text can differ between two separate runs of this harness at different times
(confirmed: the file's content read during this mission's dev-sanity run is not guaranteed identical to what it
will read during any future held-out run). This is a genuine reproducibility caveat, carried into §13.

## 6. Call/Token Budget Verification

Executed, not assumed (`scripts/verify_arch_pipeline_isolation.py`, full results in the companion JSON):
- **AST-based source check** (immune to the same self-referential-docstring false-positive class this project
  has already caught and fixed multiple times — Findings 63/83/84): `run_condition_arch_pipeline()`'s real
  `ast.Call` nodes contain zero references to `generate_code_from_plan`/`echo_query`/`deliberate_and_learn`. The
  first draft of this exact check produced a false `FAIL` by naive substring search, because the function's own
  docstring legitimately narrates these names as history — caught and fixed before being reported here.
- **Canary test**: `echo_query()`, `deliberate_and_learn()`, and `generate_code_from_plan()` were live-patched to
  raise `RuntimeError` if called, then a real, live generation was run through `run_condition_arch_pipeline()`.
  **No canary fired.**
- **Call counting**: `river_deliberation._ollama_query()` was live-patched to record every call made during one
  real `run_condition_arch_pipeline()` invocation. **Exactly 1 call was recorded**, with `model_name` equal to
  the pinned model.
- **`max_tokens` equality**: `requested_max_tokens_per_call == MAX_TOKENS == 2048` for both `BASE_1` and
  `ARCH_PIPELINE_ISOLATED`, confirmed directly from the real dev-sanity results (all 8 records, both arms, both
  tasks).

## 7. Model-Pinning Verification

Executed: the real, patched `_ollama_query()` recorded the actual `model_name` argument it was called with —
`qwen2.5-coder:7b`, exactly the pinned model, with no drift. Since this call path never invokes `choose_model()`
at all (confirmed by the AST check in §6), there is no internal mechanism left that could select a different
model — the prior implementation's cosmetic pin (a label from a call that never generated the text) is fully
retired. `result["model_used"]` now equals the model that actually generated the candidate, verified by object
identity against the recorded real call, not merely by field-name coincidence.

## 8. Isolation Verification

`base_pilot.install_isolation()`'s existing `_side_effects_detected` counter was checked before and after a real
`run_condition_arch_pipeline()` call: **0 → 0**. This is a strictly stronger property than "blocked" — this path
does not even *attempt* a `log_interaction`/`save_reflection`/`river_brain.learn`/`river_brain.save` call, since
it never reaches any of the production functions that would make one. Confirmed live in the full fresh dev-sanity
run too (§10): the cumulative `side_effects_total` counter advanced by exactly 4 on each of the 2 real
`ARCH_COUNCIL` executions (8 total) and by exactly 0 on each of the 6 real `BASE_1`/`BASE_N`/
`ARCH_PIPELINE_ISOLATED` executions — a clean, real-data confirmation that only the arm intentionally reaching
production-adjacent code (`ARCH_COUNCIL`) ever attempts anything there.

## 9. Truncation/Extraction Verification

- **Ground truth is now available for `ARCH_PIPELINE_ISOLATED`** — it routes through the same
  `install_truncation_capture()`-wrapped `_ollama_query()` call as `BASE_1`/`BASE_N`, so its `call_id` is a real
  integer (not the `PIPELINE_NO_GROUND_TRUTH` sentinel the old, council-routed arm structurally required), and a
  real `done_reason` event was directly confirmed captured under that `call_id` for a live test call.
- **Extraction edge cases**, tested against the shared, unmodified `clean_code()` function every arm already
  uses: normal fenced code, reasoning-then-fenced-code, a truncated (unclosed) fence, and a malformed
  (syntax-broken) candidate all behave correctly. Two cases surfaced real nuances, disclosed rather than hidden:
  **unfenced code directly followed by trailing prose** (no code fence at all) is not correctly extracted by
  `clean_code()` — a genuine, pre-existing, shared-across-all-four-arms limitation, not introduced by this fix,
  and mitigated in practice for this arm specifically by `CODE_OUTPUT_RULES`' own rule 3 (explicitly forbidding
  exactly this output shape). **An empty generation** trivially `ast.parse()`s as a valid (empty) module — this
  is not a system bug, it is the correct behavior of `ast.parse()`; the real, end-to-end question (does an empty
  candidate pass the actual sandbox test) was checked directly and correctly fails (`NameError` calling an
  undefined function).
- **`INFRASTRUCTURE_FAILURE` classification** is unchanged and reused verbatim — `run_condition_arch_pipeline()`
  raises through the same shared `try/except` in `_run_single_candidate()` as every other arm, using the
  already-verified `base_pilot._classify_exception()`.

Full suite: **19/19 checks VERIFIED, 0 OPEN, 0 FAIL** (`scripts/verify_arch_pipeline_isolation.py`,
`audits/tier3_apparatus/arch_pipeline_isolation_verification_results.json`).

## 10. Development Sanity Results

A fresh development-sanity pass (`task_11`, `task_12`, both required development tasks — no held-out task
touched) was run under the fixed code. Full 8 records:

| task | arm | model | passed | classification | calls | gen_time | cumulative side effects |
|---|---|---|---|---|---:|---:|---:|
| task_11 | ARCH_PIPELINE_ISOLATED | qwen2.5-coder:7b | True | PASS | 1 | 11.44s | 0 |
| task_11 | ARCH_COUNCIL | council_synthesis | False | TASK_LOGIC_FAILURE | 4 | 129.81s | 4 |
| task_11 | BASE_N | qwen2.5-coder:7b | False | TASK_LOGIC_FAILURE | 4 | — | 4 |
| task_11 | BASE_1 | qwen2.5-coder:7b | False | TASK_LOGIC_FAILURE | 1 | 6.59s | 4 |
| task_12 | ARCH_COUNCIL | council_synthesis | False | TASK_LOGIC_FAILURE | 4 | 177.06s | 8 |
| task_12 | BASE_1 | qwen2.5-coder:7b | True | PASS | 1 | 84.08s | 8 |
| task_12 | BASE_N | qwen2.5-coder:7b | True | PASS | 4 | — | 8 |
| task_12 | ARCH_PIPELINE_ISOLATED | qwen2.5-coder:7b | True | PASS | 1 | 17.47s | 8 |

- `BASE_1`/`BASE_N` produce valid candidates and — where they fail — fail for a genuine, reproducible reason
  (`task_11`'s TASK_LOGIC_FAILURE is shared across `BASE_1`/`BASE_N`/`ARCH_COUNCIL` alike, not an isolated
  artifact of one arm).
- `BASE_N` produces real independent attempts and a real same-model synthesis; its outcome tracks task
  difficulty sanely (fails on the same task every other arm finds hard, passes on the same task every other arm
  finds tractable) — non-degenerate, per this step's own required standard.
- `ARCH_PIPELINE_ISOLATED` produces a genuine single-call candidate on both tasks, `calls=1` both times, model
  identity correct both times, `max_tokens=2048` both times (verified directly from the records), and
  `side_effects` unchanged by its own execution both times.
- `ARCH_COUNCIL` produces its intended real council candidate (4 calls, `council_synthesis` label) both times.
- Truncation classification: `truncation_evidence_type` is `None` for all 8 records (no truncation occurred in
  this run; `call_id` is a real integer for every record, including `ARCH_PIPELINE_ISOLATED`'s two — ground truth
  was genuinely available and checked for all four arms this time, not three).
- No production contamination: the cumulative side-effects counter is attributable entirely to
  `ARCH_COUNCIL`'s two real executions (4 + 4 = 8), confirming the other three arms across all 6 of their
  combined executions added zero.
- Objective sandbox scoring: `passed`/`classification` are populated and mutually consistent for all 8 records.

**This is apparatus validation only — development-set performance here is not interpreted as evidence for any
held-out hypothesis**, per this mission's own explicit instruction.

## 11. Historical `ARCH_PIPELINE` Data — Invalidation Statement

**None of the following data was deleted, edited, or reinterpreted. Each is preserved exactly as originally
recorded, and is now explicitly classified `INVALID_FOR_ISOLATED_SINGLE_CALL_COMPARISON`** — it never was a
genuine single-call self-edit-generation observation; it was, in every case, a real council deliberation
routed through self-edit's own prompt-construction wrapper.

| Source file | Records | Note |
|---|---|---|
| `audits/capability_pilot/raw_results.jsonl` (condition `B`) | 9 | The *original* 3-condition pilot's own PIPELINE condition. Same root defect (`generate_code_from_plan()` → `echo_query()` → `deliberate_and_learn()`), compounded by a second, already-documented, independent confound: no model pinning existed at all in this pilot (`model_used` spans `echo:latest`/`llama3:instruct`/`llama3.2:3b`/`qwen2.5-coder:7b` across the 9 records). |
| `audits/tier3_apparatus/dev_sanity_results.PRE_REPAIR_20260904.jsonl` (arm `ARCH_PIPELINE`) | 2 | Produced before the Objective-1 truncation-attribution repair. |
| `audits/tier3_apparatus/dev_sanity_results.PRE_ISOLATION_FIX_20260904.jsonl` (arm `ARCH_PIPELINE`) | 2 | Produced *after* the truncation repair, *before* this isolation fix — the run that directly surfaced this finding. |

**13 historical records total, across the entire project's history, all reclassified. Zero of them are valid
evidence for "does self-edit's isolated generation mechanism, at equal budget, outperform a single-model
baseline" — the only question `ARCH_PIPELINE_ISOLATED` now exists to answer.** They remain valid, disclosed
historical evidence of a real, confirmed measurement defect, and of the original pilot's own separately-already-
known confounds — nothing about their *existence* is erased, only their *interpretability* for this specific
comparison.

## 12. Updated Four-Arm Scientific Interpretation

| Arm | Calls | Model(s) | Token budget | Context/framing | Synthesis | Scientific question |
|---|---:|---|---:|---|---|---|
| `BASE_1` | 1 | pinned (single) | 2048 | bare task prompt | none | What can the pinned model do with one attempt, no framing, no extra compute? |
| `BASE_N` | 4 (3+1) | pinned (single, reused) | 2048/call | bare task prompt × 3, then own attempts for synthesis | same-model, neutral template | What can the pinned model do with 3 independent attempts and self-synthesis — compute-matched to Council, diversity removed? |
| `ARCH_PIPELINE_ISOLATED` | 1 | pinned (single) | 2048 | `CODE_OUTPUT_RULES` + live `self_edit_generated.py` contents + task | none | **Does self-edit's own generation framing/context improve objectively-measured correctness beyond a budget-matched single-model baseline?** |
| `ARCH_COUNCIL` | 4 (3+1) | 3 real, diverse models + synthesis | 2048/call | production's real council system-prompt assembly | real, heterogeneous | Does FeralEcho's real, combined council package (diversity + selection + synthesis together) beat a budget-matched same-model baseline? |

### `ARCH_PIPELINE_ISOLATED` can support:

> A test of whether the isolated self-edit generation framing/context contributes correctness beyond a
> budget-matched single-model generation on this task class.

### `ARCH_PIPELINE_ISOLATED` cannot support:

> A claim that Echo's literal current production self-edit path is superior to the baseline.

That production claim would require a separate experiment measuring the *actual* current production call path
(now known, per §1, to itself be a real council deliberation under self-edit's own framing) — a materially
different, not-yet-designed comparison, out of scope for this correction.

### The H4 boundary, preserved verbatim, unchanged by this fix:

> **This four-arm design cannot separate heterogeneous model diversity from Council-specific orchestration as
> competing explanations for a Council win.**

Therefore: `ARCH_COUNCIL > BASE_N` can support only the bounded claim that the Council package — including model
diversity, selection, and synthesis — outperforms budget-matched same-model self-consistency. It cannot isolate
Council-specific orchestration from model diversity. This isolation fix is orthogonal to, and does not touch,
this boundary — it was never in question for `ARCH_PIPELINE`, only for `ARCH_COUNCIL` vs. `BASE_N`.

## 13. Remaining Confounds

- **`self_edit_generated.py`'s content is not frozen.** It is the live, continuously-self-edited production
  file (real self-edit cycles were observed running during this same investigation). Its exact text at
  dev-sanity time is not guaranteed identical to its text at any future held-out run time. Checked and confirmed
  harmless for the *specific tasks in this study* (§5) — but this is a real, disclosed, non-reproducible input,
  not eliminated by this fix.
- **`plan_code_logic()`, self-edit's real planning step, is still never exercised** by either the old or the new
  implementation — both substitute the raw task description directly as "the plan." This was already true
  before this fix and is unchanged by it; a fully faithful reproduction of self-edit's real multi-step pipeline
  would be a larger, separate undertaking.
- **`CODE_OUTPUT_RULES`' rule 10** (the `apply_to_code` naming convention) is irrelevant to every task in this
  study and could plausibly, mildly confuse or distract a model solving an unrelated task — disclosed, not
  removed (removing it would itself be an undisclosed, un-authorized change to "the self-edit framing under
  test").
- **Model diversity vs. Council-specific orchestration remains unresolved for the `ARCH_COUNCIL` vs. `BASE_N`
  comparison** — restated in §12, unaffected by this fix.
- **This fix has not yet been run against held-out data** — every verification and every sanity result in this
  report is development-set-only, per explicit instruction.

## 14. Explicit H4 Boundary (restated for completeness)

> **This four-arm design cannot separate heterogeneous model diversity from Council-specific orchestration as
> competing explanations for a Council win.** A win for `ARCH_COUNCIL` over `BASE_N` supports only "the Council
> package as a whole — diversity, selection, and synthesis together — beats a budget-matched same-model
> baseline," never "Council-specific orchestration, independent of model diversity, is the active ingredient."

## 15. Readiness for Held-Out Execution

# READY WITH CONDITIONS

The specific defect this mission was authorized to fix — `ARCH_PIPELINE`'s hidden council invocation — is fixed,
verified by execution (19/19 checks), and sanity-confirmed on the development set (8/8 clean, correctly-behaved
records, zero contamination, zero call-count/token-budget/model-identity discrepancies). This resolves the
specific blocker that halted the prior mission before it. The conditions below are carried forward from the
prior `current_capability_synthesis.md` readiness verdict, restated because nothing in this fix changes them:

1. A genuine low-contention execution window should still be secured before the held-out run — Ollama
   contention remains a real, independently-documented risk across this project's history, unaffected by this
   fix.
2. The 8 held-out tasks (already authored and frozen, hash `2d78cbdb...`, integrity re-confirmed throughout this
   mission) remain untouched and ready.
3. Any future report of results must state the H4 boundary (§14) verbatim, and must also now state the
   `ARCH_PIPELINE_ISOLATED` scope boundary (§12) verbatim — a win or loss for this arm answers the *isolated
   generation-mechanism* question, not a claim about Echo's literal production self-edit path.
4. No production change, autonomy repair, or fine-tuning should be bundled into or precede the held-out run.
5. **New, added by this mission**: the held-out run must use the arm label `ARCH_PIPELINE_ISOLATED` (already
   wired into `randomized_arm_order()`/`main_heldout()`) — any future report must not silently conflate its
   results with the 13 historical `ARCH_PIPELINE`-labeled records this report explicitly invalidated.

**This mission does not execute the held-out experiment and does not authorize it.** That decision remains
outside this report's own scope, per explicit instruction.
