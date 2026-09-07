# FeralEcho — Direct Councillor Boundary Trace

Forensic capture, not a fix. No production code modified, no commits, no RiverBrain mutation.

---

## 1. Executive Finding

During one real, genuine, production-path `deliberate_and_learn()` call, all three councillors
produced **completely distinct raw outputs**, and the synthesis stage produced a further distinct
output that was returned as the final response with **zero downstream collapse** — no fallback, no
convergence, no identity between any two captured values anywhere in the chain. This directly
contradicts the "byte-identical raw councillor responses" claim in a prior report in this series
(`v1.2.1`) for the specific call captured here. A second, foundational finding, established from
source before any call was made: **`deliberate_and_learn()`'s councillor loop is a plain, sequential
Python `for` loop — there is no concurrency of any kind in this function.** The "concurrency collapse"
hypothesis this investigation thread has been chasing across the last two passes does not apply,
because there is no concurrency mechanism present to collapse anything.

---

## 2. Environment Safety

Verified before the real call:
- `run.py`: not running (direct process check, no match)
- watchdog (`start_echo.sh`): not running
- port 5000: unbound
- Ollama: reachable, 9 models
- `memory/river_brain.pkl`: sha256 `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`
- git HEAD: `2cf2d95009943797db5ec41fea9b4021634fd5e6`
- `git status --porcelain`: 29 lines, all pre-existing

Verified after the real call, all identical:
- `run.py`: still not running
- watchdog: still not running
- port 5000: still unbound
- `memory/river_brain.pkl`: sha256 **identical**, `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` — byte-for-byte unchanged
- git HEAD: **unchanged**, `2cf2d95009943797db5ec41fea9b4021634fd5e6` — no commit made
- `git status --porcelain`: still 29 top-level lines — the new capture script and its artifacts landed
  entirely inside the already-untracked `app/experiments/first_learning_loop/` directory, which git
  already reported as one line before this pass; `git status --porcelain -- app/core/river_deliberation.py`
  returns nothing — **zero diff on the forbidden-target source file**, confirming no source
  instrumentation was needed or used.

`RiverBrain.learn`/`.save` were neutralized at the class level (identical pattern to
`scripts/memory_ablation_experiment.py`'s already-proven `neutralize_river_brain_writes()`) before the
real call — confirmed in the run's own log line: `"RiverBrain.learn/.save neutralized at class level."`

---

## 3. Actual Call Graph

Traced directly from `app/core/river_deliberation.py` source, not inferred from prior reports:

```
deliberate_and_learn(prompt, task_type="coding", river_brain, model_pool, max_tokens=512)
    │
    ├─ task_type not in DIRECT_ECHO_TASKS → proceeds past the direct-Echo bypass
    │
    ├─ _warm_up_echo(synth_model)                     [real _ollama_query call, prompt="."]
    │
    ├─ exploration_bias computed (world-surprise + valence, best-effort, non-blocking)
    │
    ├─ council = _select_council(...)                 → real 3-model council chosen
    │
    ├─ for i, model in enumerate(council):             ← PLAIN SEQUENTIAL for LOOP, no concurrency
    │     councillor_temp = _jittered_temperature(base, i, len(council))
    │     response = _ollama_query(model, prompt_with_system, temperature=councillor_temp, ...)
    │     opinions[model] = response
    │
    ├─ valid_opinions = {non-empty, non-[ERROR] opinions}
    │
    ├─ detect_full_agreement(valid_opinions)           [coding tasks only — not triggered this run]
    │
    ├─ synthesis: final_response = _ollama_query(synth_model, prompt_with_synthesis_system, ...)
    │
    ├─ find_missing_agreed_definitions() completeness check [coding tasks only]
    │     → if it had failed: select_best_fallback_candidate() (max(pool, key=len))
    │     → this run: NOT triggered — synthesis passed cleanly
    │
    └─ return final_response
```

**Confirmed, source-level fact**: `grep -c "ThreadPoolExecutor\|asyncio\|threading.Thread"
app/core/river_deliberation.py` → zero matches. The only two uses of `threading` in the entire file
(`_council_log_lock`, `_synthesis_integrity_log_lock`) guard log-file writes against races from
*separate, independently-scheduled* callers of this module (e.g. two different autonomous loops both
calling `deliberate_and_learn()` at once) — not from anything inside one single call. The councillor
loop itself makes each real Ollama request, waits for it to fully return, then starts the next.

---

## 4. Instrumentation

**No source file was modified.** A standalone, isolated script
(`app/experiments/first_learning_loop/councillor_boundary_capture.py`) monkeypatches the module-level
`river_deliberation._ollama_query` reference at runtime, inside a fresh Python process, before calling
the real `deliberate_and_learn()`. The wrapper calls through to the real, original function and returns
its real, unmodified result — it changes nothing about what the real function does or receives, only
observes and persists what passes through. The original reference was restored at the end of the same
process (`rd._ollama_query = real_ollama_query`), confirmed in the run log
(`"Restored original _ollama_query reference in this process."`) — though this restoration is
inherently moot for correctness, since the process exits immediately after and never touches any
persistent state.

`git status --porcelain -- app/core/river_deliberation.py` (checked after the run, §2) confirms zero
diff — the strongest available proof that no source-level change occurred or persisted.

---

## 5. Raw Councillor Results

All captured from the one real run, `20260907T010823Z`. Call #0 is the warm-up ping (prompt `"."`,
not a real councillor opinion) — included for completeness since the instrumentation wraps every
`_ollama_query` call in the process, but excluded from the "councillor" analysis below. Calls #1-#3 are
the three real councillors; call #4 is the real synthesis call.

| Call | Role | Model | Temp | Response SHA-256 (16) | Length | Start→End | Identical to any other? |
|---|---|---|---:|---|---:|---|---|
| 0 | warm-up | `echo:latest` | (default) | `af74607624c858bc` | 887 | 11.02s | N/A — not a councillor opinion |
| 1 | councillor A | `qwen2.5-coder:7b` | 0.55 | `32a1727149911659` | 1461 | 16.29s | No |
| 2 | councillor B | `mlx:qwen3` | 0.70 | `b7d8075fef32ab2c` | 319 | 5.81s | No |
| 3 | councillor C | `echo:latest` | 0.85 | `9766be735110a18b` | 662 | 6.36s | No |
| 4 | synthesis | `echo:latest` | (default) | `3677c85b5a5cd50f` | 369 | 6.58s | No — but matches the final returned response |

Full raw artifacts persisted at
`app/experiments/first_learning_loop/councillor_boundary_artifacts/20260907T010823Z_call{0-4}_*.json`
and `..._final_response.json`, each containing the complete prompt, exact kwargs, full raw response
text, and sha256. Independently re-hashable by anyone with repository access — no summary substituted
for raw evidence anywhere in this report.

---

## 6. Variation Analysis

```
A == B  (qwen2.5-coder:7b vs mlx:qwen3):     FALSE
A == C  (qwen2.5-coder:7b vs echo:latest):   FALSE
B == C  (mlx:qwen3 vs echo:latest):          FALSE
```

All three pairwise comparisons: **genuinely different**, confirmed by direct SHA-256 inequality, not
approximate/semantic judgment. Structural confirmation, read directly from the persisted response text
(§ "Raw Councillor Results" content, verified via direct file read): all three implement the same
correct algorithm (two-pointer merge of sorted lists) with genuinely different code — different
variable names (`i, j` vs `i = j = 0`), different loop structure phrasing, different explanatory prose
around the code block, different code-fence casing (```` ```python ```` vs ```` ```Python ````).
This is real content variation, not whitespace-only noise — directly satisfying the evidence standard
several prior passes in this series required and, in the one case tested here, did not previously
observe.

The synthesis call (#4) also produced its own genuinely distinct text — not a copy of any single
councillor's response, consistent with a real synthesis having occurred, not a rejection/fallback.

---

## 7. Downstream Boundary

**Variation was never lost. There is no collapse boundary to report in this run.** The final returned
response's SHA-256 (`3677c85b5a5cd50f`) exactly matches call #4's (the synthesis call) — meaning
`deliberate_and_learn()` used the real synthesis output directly as its return value, with no fallback
substitution. Every stage this mission asked about — raw councillor responses, council input, the
selected/synthesized candidate, and the final output — remained genuinely distinct from every other
stage's content throughout this one real call.

---

## 8. Concurrency Findings

**Concurrency is not a relevant factor for this function, at the code level, at all** — confirmed by
direct source read (§3): the councillor loop is a plain sequential `for` loop, not a concurrent one.
This is worth stating plainly as a correction to this investigation thread's own working framing across
its last two passes (`v1.2.1`'s diagnosis and the immediately preceding
`full_pipeline_determinism_boundary` report both discussed "the real concurrent
`deliberate_and_learn()` path" as an open unknown) — there is no concurrent execution path in this
function to have collapsed anything, real or hypothetical. Whatever explains `v1.2` and `v1.2.1`'s
original observed convergence, it cannot be a concurrency-specific mechanism, because none exists here.

---

## 9. Competing Explanations

| Hypothesis | Status |
|---|---|
| Model-layer determinism (Ollama itself deterministic without a seed) | **RULED OUT** — already falsified in the immediately prior pass (`full_pipeline_determinism_boundary`), and reconfirmed here: three real, distinct models each produced genuinely distinct output in this same run |
| Parameter/temperature determinism | **RULED OUT** — `_jittered_temperature()`'s real per-seat values (0.55/0.70/0.85, confirmed in the captured kwargs) are distinct and real, and the resulting outputs varied correspondingly |
| Concurrency-specific collapse | **RULED OUT AS A CATEGORY** — no concurrency mechanism exists in this function to have caused a collapse (§3, §8) |
| Council selection collapse (always picks the same council) | **NOT TESTED THIS PASS** — only one council selection was observed; this run's council was `[qwen2.5-coder:7b, mlx:qwen3, echo:latest]`, plausible but not confirmed to be the *same* council `v1.2`/`v1.2.1` selected |
| Synthesis/fallback-stage collapse | **RULED OUT for this specific run** — synthesis genuinely fired and its real, distinct output was returned; no fallback was triggered |
| `v1.2.1`'s original "byte-identical raw responses" claim, taken at face value | **CONTRADICTED by this run's direct evidence** — not proven false in general (a single positive-variation sample cannot rule out that the original observation was also real, under different specific conditions — different task content, different council composition, or simple run-to-run variance), but this specific claim does not hold universally, which is itself the important finding |
| Caching / response reuse | **NOT INDEPENDENTLY TESTED THIS PASS** — no evidence for it was found (elapsed times, §5, are all realistically distinct — 5.8s to 16.3s — inconsistent with an instant cache hit on any call), but not explicitly red-teamed with a dedicated cache-detection probe in this narrow pass |

---

## 10. Implications for Learning Experiments

This result establishes that the FeralEcho pipeline **is** capable of producing genuinely independent,
non-collapsing behavioral samples through its real production path — at least under the conditions of
this one real call. This directly reopens (does not settle) the question `v1.2`'s clean experiment was
designed to answer: whether a verified lesson causes a measurably different downstream decision.
`v1.2`'s own specific RED result (CONTROL == EXPERIENCE, byte-identical) may have been a genuine,
task-specific or run-specific outcome rather than evidence of a structural, universal determinism in
this pipeline — this pass cannot resolve which, since it used a different task and did not repeat the
exact `v1.2` conditions.

Keeping the mission's own required distinctions separate: this pass demonstrates **stochasticity**
(the pipeline can produce different raw outputs across councillors and across the synthesis step) and,
in this one case, **exploration** in a weak sense (three genuinely different candidate solutions were
generated and one was synthesized from them). It says nothing about **feedback**, **learning**, or
**generalization** — those remain exactly as unresolved as `v1`, `v1.1`, `T4`, and `v1.2` left them.
Demonstrating that the instrument *can* vary is a precondition for a learning experiment to be
interpretable, not evidence of learning itself.

---

## 11. Implementation Recommendation

**`NO CHANGE`.**

No production code was found to require modification, and none was made. The real pipeline already
produces genuine variation without any seed, sampling, or architectural change — this pass's evidence
does not support adding seed plumbing, modifying sampling architecture, or touching council/synthesis
logic. If a future pass wants to determine whether `v1.2`'s specific convergence was a one-off or
reflects something real about that particular task/council combination, the correct next step is a
narrow, targeted replication of `v1.2`'s own exact conditions using this same read-only capture
technique — not a production change.

---

## 12. Final Verdict

**`COUNCILLOR VARIATION CONFIRMED.`**

Real, concurrent-in-name-only (§3, §8) execution of `deliberate_and_learn()` produced three genuinely
distinct councillor raw responses and a genuinely distinct, non-fallback synthesis — with no collapse
observed at any traced boundary. This is a single real sample, not a replicated finding, and it directly
contradicts a specific claim from an earlier report in this series without fully resolving the earlier
report's own underlying observation — both facts are stated here plainly, per this investigation
series' own standing discipline, rather than either being smoothed over.

---

## Evidence Ledger

- Commands run: environment checks (`ps`, `lsof`, `curl`, `shasum`, `git log`/`status`) before and
  after; source reads of `app/core/river_deliberation.py` (`deliberate_and_learn`, `_select_council`,
  `_jittered_temperature`, `select_best_fallback_candidate`, `detect_full_agreement`,
  `find_missing_agreed_definitions`); one real script execution
  (`app/experiments/first_learning_loop/councillor_boundary_capture.py`).
- Files inspected: `app/core/river_deliberation.py` (full relevant sections read directly, not
  summarized from memory), `scripts/memory_ablation_experiment.py`
  (`neutralize_river_brain_writes()`), `app/core/echo_model_orchestrator.py` (`get_river_brain`,
  `MODEL_POOL`, the real `deliberate_and_learn()` call-site shape).
- Experiment performed: one real `deliberate_and_learn()` call, `task_type="coding"`, a fresh
  contamination-free prompt (`merge_sorted_lists`), `max_tokens=512`, RiverBrain writes neutralized.
- Artifacts created: `app/experiments/first_learning_loop/councillor_boundary_capture.py` (the
  instrumentation script, kept as a reusable read-only harness);
  `app/experiments/first_learning_loop/councillor_boundary_artifacts/` (6 JSON files: 5 per-call
  captures + 1 final-response record, all with real sha256 hashes recorded inline).
- Hashes: recorded in full in §5's table and inline in each persisted artifact file.
- Git status before: 29 porcelain lines (all pre-existing). Git status after: 29 porcelain lines (new
  files absorbed into the already-untracked `app/experiments/first_learning_loop/` directory entry;
  zero diff on `app/core/river_deliberation.py` specifically, confirmed via targeted `git status
  --porcelain -- <path>`). No commit made. HEAD unchanged
  (`2cf2d95009943797db5ec41fea9b4021634fd5e6`). `memory/river_brain.pkl` sha256 unchanged
  (`eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`).
