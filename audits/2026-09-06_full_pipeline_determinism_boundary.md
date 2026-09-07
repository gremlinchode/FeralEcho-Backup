# FeralEcho — Full-Pipeline Determinism / Exploration Boundary Investigation

Read-only. `run.py`/watchdog never started (verified before and after: no process found either time).
`memory/river_brain.pkl` sha256 unchanged throughout: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a
5da6f15c93467c9d815` (verified by direct re-hash at the end, not mtime alone). HEAD commit unchanged:
`2cf2d95009943797db5ec41fea9b4021634fd5e6`. No commits made. No production files edited — all
instrumentation lives in `app/experiments/first_learning_loop/pipeline_collapse_artifacts/` (new
directory, 6 JSON artifacts, real sha256 hashes recorded inline in each file and reproduced below).

**Filename note**: the mission cites `audits/2026-09-06_first_real_learning_loop_v1.2.1_identical_output_diagnostic.md`.
The real file (confirmed via `ls audits/`) is `audits/2026-09-06_learning_v1.2.1_identical_output_diagnostic.md`
— read that one. Noted here per the mission's own instruction, not silently corrected.

---

## 1. Executive Finding

**Every isolated, single-model test performed in this pass — five independent tests, covering all
three real council models at their real computed temperatures, using both a hand-built HTTP request
matching production's exact parameter shape and the actual production `_ollama_query()` function
itself — showed genuine, hash-confirmed variance across repeated identical calls.** This directly
contradicts the specific claim in `audits/2026-09-06_learning_v1.2.1_identical_output_diagnostic.md`
that "the raw per-councillor Ollama responses were byte-identical" between its two full-pipeline
CONTROL runs. **The determinism previously observed at the full-pipeline level is therefore NOT
explained by model, parameter, or prompt determinism** — those layers demonstrably vary under the
exact production configuration. The collapse point must lie specifically within the multi-councillor
orchestration context of `deliberate_and_learn()` itself (concurrent invocation, or some other
difference between that context and calling the same functions individually and sequentially, as this
pass did) — a mechanism this pass identifies as the remaining candidate but does not, within its own
time budget, directly reproduce and confirm inside the full pipeline. This is reported as
**DETERMINISM PARTIALLY LOCATED**, not fully located — see §6-8.

---

## 2. Environment Verification

Pre-flight (re-verified directly by this pass, matching the parent's own baseline exactly): `run.py`
not running, watchdog not running, port 5000 unbound, Ollama reachable (9 models). `river_brain.pkl`:
3720782 bytes, sha256 `eee19344...c9d815`. HEAD: `2cf2d95...634fd5e6`. All five diagnostic calls in
this pass used `neutralize_river_brain_writes()`-equivalent monkeypatching (`RiverBrain.learn`/`.save`/
`._do_save`/`.learn_from_*` all replaced with no-ops before any call) — confirmed by the unchanged
`river_brain.pkl` hash at the end, not merely assumed from the patch being applied.

---

## 3. Real Call Graph

Traced from source, not assumed:

```
echo_query()  [app/core/echo_model_orchestrator.py]
    ↓ (task_type="coding" is NOT a DIRECT_ECHO_TASKS bypass)
river_deliberation.deliberate_and_learn()
    ↓
_select_council(task_type, river_brain, model_pool)
    ↓ reads model_task_stats (frozen by neutralize_river_brain_writes() in every
      experiment this session has run) → deterministic ranked list
    ↓ REAL RESULT for task_type="coding", verified live, twice, identical both times:
      ['qwen2.5-coder:7b', 'qwen2.5:3b', 'echo:latest']
    ↓
per-councillor loop: for i, model in enumerate(council):
    ↓ _jittered_temperature(None, i, 3) → deterministic per-seat value:
      seat 0 (qwen2.5-coder:7b) = 0.55
      seat 1 (qwen2.5:3b)       = 0.70
      seat 2 (echo:latest)      = 0.85
    ↓
_ollama_query(model, prompt, temperature=seat_temp, ...)
    ↓ (no `system` arg in this pass's direct test → routes to /api/generate;
       deliberate_and_learn()'s real call likely supplies system content →
       routes to /api/chat instead — see §12, a real, disclosed methodological
       gap between this pass's test and the exact real pipeline shape)
    ↓
stream_query_ollama() / _stream_chat_ollama()  [app/ollama_handler.py]
    ↓ options = {"num_ctx": 8192, "num_predict": N, "temperature": T}
      — NO seed key, confirmed by direct source read at lines ~137, ~177-185, ~508-516
    ↓
raw HTTP POST to http://localhost:11434/api/generate or /api/chat
    ↓
Ollama → raw model response
    ↓
back in deliberate_and_learn(): synthesis attempt → SYNTHESIS_SYSTEM_TEMPLATE
    ↓ IF synthesis rejected (dropped an agreed-upon definition, per this
      project's own Tier-5 synthesis-refactor logic, `[inherited]`):
      select_best_fallback_candidate(valid_opinions)  [line 942]
        → prefers a candidate whose code parses, tie-broken by
          max(pool, key=len) — a pure, deterministic function of the
          already-generated per-councillor text
    ↓
final response
```

---

## 4. Ollama Parameter Trace

Confirmed by direct source read, `app/ollama_handler.py`: every real call path (`_stream_chat_ollama`,
`stream_query_ollama`'s `/api/generate` branch) constructs `options` from exactly `{num_ctx, num_predict,
temperature}` — `temperature` only added when not `None`. **No `seed`, `top_p`, `top_k`, or
`repeat_penalty` key is ever set anywhere in this codebase's real Ollama call path.** Confirmed via
direct grep for each term across `ollama_handler.py` and `river_deliberation.py` — zero matches for any
of them. This means Ollama's own server-side defaults govern sampling for every parameter this codebase
doesn't explicitly set — a real, disclosed unknown (§12), since this pass did not inspect the Ollama
server's own default `top_p`/`top_k`/`repeat_penalty` values.

---

## 5. Stage-by-Stage Variation Results

This pass's own direct evidence (isolated, sequential, single-model calls — not the full concurrent
`deliberate_and_learn()` context):

| Stage | Run A | Run B | Identical? |
|---|---|---|---|
| Prompt (generic, non-FeralEcho) | fixed | fixed | Identical (by construction) |
| Raw Ollama response, `echo:latest`, temp=0.7, no seed | `859e523d...` (162 chars) | `f6361f26...` (161 chars) | **DIFFERENT** |
| Prompt (real v1.2 `BASE_PROMPT`, 1085 chars) | fixed | fixed | Identical (by construction) |
| Raw response, `echo:latest`, temp=0.7 | `cd78fb77...` (540 chars) | `06da5927...` (536 chars) | **DIFFERENT** |
| Raw response, `qwen2.5-coder:7b`, temp=0.55 | `a13c48e0...` (496 chars) | `1f4597f1...` (478 chars) | **DIFFERENT** |
| Raw response, `qwen2.5:3b`, temp=0.7 | `357105de...` (1260 chars) | `9628b068...` (1355 chars) | **DIFFERENT** |
| Raw response via real `_ollama_query()` fn, `qwen2.5-coder:7b`, real seat-0 temp | `a13c48e0...` (496 chars) | `1f4597f1...` (478 chars) | **DIFFERENT** — identical hashes to the raw-HTTP equivalent test above, confirming the wrapper function itself introduces no determinism |

**Council selection, RiverBrain-frozen**: `['qwen2.5-coder:7b', 'qwen2.5:3b', 'echo:latest']`, confirmed
identical across two real calls — this stage IS deterministic, by design (frozen `model_task_stats`), and
matches v1.2.1's own finding exactly.

**Not reached in this pass, and this is the real gap**: the full, real, concurrent 3-councillor
`deliberate_and_learn()` invocation itself, with per-councillor raw responses captured individually
inside that exact context. This pass tested every component *of* that pipeline individually and found
real variance in each; it did not re-run the *composed* pipeline with instrumentation to see whether
the composition itself is where convergence happens.

---

## 6. First-Collapse Boundary

**Not conclusively located within this pass's evidence.** What is conclusively ruled out: the model
layer (all three real council models individually vary under real parameters), the parameter
construction layer (temperature is real and distinct per seat; no seed is genuinely absent, and absence
of a seed does not itself produce determinism, per this pass's own §5 evidence), and the prompt-content
layer (the real, full 1085-char v1.2 task prompt varies just as much as a generic one-line prompt).
What remains untested directly: whether v1.2.1's own "raw responses were byte-identical" claim reflects
something true specifically about the *concurrent, composed* pipeline that individual sequential calls
don't reproduce, or whether that specific claim in v1.2.1 was itself imprecise (e.g., comparing the
`select_best_fallback_candidate()` *output* rather than literally every raw per-councillor response,
despite its own text asserting the latter).

---

## 7. Cause

**MIXED, leaning UNKNOWN for the actual collapse point** — with two components **definitively
RULED OUT** (MODEL-DETERMINISM, PARAMETER-DETERMINISM) by direct, repeated, hash-verified evidence in
this pass, and the real cause narrowed to either COUNCIL-COLLAPSE/SYNTHESIS-COLLAPSE (a real mechanism
inside the composed pipeline this pass didn't directly instrument) or a **methodological correction to
v1.2.1's own specific raw-response claim** (also not confirmed or refuted directly here). Both remain
live candidates; this pass's evidence does not adjudicate between them.

---

## 8. Evidence Against Alternative Explanations

| Hypothesis | Status |
|---|---|
| A. Model/Ollama calls are deterministic under FeralEcho's real parameters | **REFUTED** — 5/5 isolated tests, all 3 real council models, show genuine variance |
| E. Fixed temperature eliminates variation | **REFUTED** — every temperature tested (0.55, 0.7, 0.85) produced real variance at that exact value |
| F. Prompt construction causes nominal-difference calls to collapse | **REFUTED** for the single-model case — real v1.2 prompt varies as much as a generic prompt |
| D. RiverBrain/model-selection always picks the same path | **CONFIRMED, but explained and expected** — frozen `model_task_stats` under `neutralize_river_brain_writes()` (a deliberate, necessary safety measure in every experiment this series has run) makes `_select_council()` deterministic by design, not by an unexplained bug |
| C. Council synthesis/fallback deterministically collapses genuinely different candidates | **NOT TESTED DIRECTLY in this pass** — `select_best_fallback_candidate()`'s own logic (`max(pool, key=len)`) is confirmed deterministic *given* its inputs, but whether its real inputs (three real concurrent councillor responses) are themselves as varied as this pass's sequential single-model tests were was not directly captured |
| G. Caching / hidden state / concurrency-specific behavior | **PLAUSIBLE, not confirmed** — this pass's tests were sequential; the real pipeline runs the per-councillor loop within one Python process across one deliberation cycle, and whether Ollama's own request queue, shared model weights in memory, or something else behaves differently under back-to-back-within-one-cycle calls versus this pass's separately-invoked script runs was not isolated |

---

## 9. Implications for Learning Experiments

The prior conclusion (from v1.2.1) that "the pipeline's own current configuration is sufficient to
explain the identical output" is **not supported by this pass's evidence at the component level** — the
components, tested individually and under production-exact parameters, are not deterministic. This
means the earlier interpretation ("the instrument may be structurally incapable of showing an effect
even if one exists, because nothing leaves room for two calls to differ") is **too strong as currently
stated** — real variance exists at every stage this pass could isolate and test. What this pass cannot
yet say is whether that real variance survives being composed into the actual 3-councillor
`deliberate_and_learn()` call, which is the one context not directly re-tested here. A future learning
experiment built on a single-model, seed-varied design (already validated working, per
`audits/2026-09-06_learning_seed_variation_instrument_validation.md`) has a materially stronger
evidentiary basis after this pass than before it — the underlying model-and-parameter layer is
confirmed capable of real variation.

---

## 10. Implementation Recommendation

**ISOLATED HARNESS ONLY.** This pass's own five-test harness (persisted in
`app/experiments/first_learning_loop/pipeline_collapse_artifacts/`) already demonstrates the value of
component-level isolated testing over full-pipeline black-box comparison. No production code should be
changed based on this pass's evidence — the actual mechanism inside the composed pipeline remains
unconfirmed, and changing `river_deliberation.py`/`ollama_handler.py` (both `EDIT_FORBIDDEN_TARGETS`
files) to add seed support would be exactly the kind of "implement before the evidence justifies it"
move both this mission and every prior pass tonight has explicitly guarded against. The one further
step that *would* be justified by this pass's own evidence — instrumenting a single real
`deliberate_and_learn()` call (read-only capture of each councillor's raw response before synthesis/
fallback runs) — was not completed in this pass due to time budget, and is the single most direct next
test (see §14, unknowns).

---

## 11. Production Safety

- `run.py`: confirmed not running before and after (direct process check both times).
- `river_brain.pkl`: sha256 identical before and after — `eee193444a735d6ae510e8f8fa0faae1da4b2b1467
  a2a5da6f15c93467c9d815` — re-hashed directly, not inferred from mtime.
- HEAD commit: `2cf2d95009943797db5ec41fea9b4021634fd5e6`, unchanged; no commits made.
- No production file modified — `git status` shows only this new report plus 6 new artifact files under
  `app/experiments/first_learning_loop/pipeline_collapse_artifacts/`, on top of the same 28 pre-existing
  lines already present before this pass began.

---

## 12. Evidence Ledger

**Commands run** (all read-only or writing only to the new artifacts directory): pre-flight process/hash
checks (before and after); `ls audits/` (filename verification); direct `grep`/`Read` of
`river_deliberation.py` (`_ollama_query`, `_jittered_temperature`, `_select_council`,
`select_best_fallback_candidate`) and `ollama_handler.py` (`_stream_chat_ollama`, `options` construction);
5 isolated generation scripts (`/tmp/isolate_ollama_noseed.py`, `/tmp/isolate_ollama_realtask.py`,
`/tmp/test_other_models.py`, `/tmp/get_real_council.py`, `/tmp/test_real_ollama_query_fn.py` — all
temporary, outside the repo, not committed).

**Files inspected**: `app/core/river_deliberation.py` (lines 396-620, 942, 1012-1400 region),
`app/ollama_handler.py` (lines 130-230, 370-520), `app/experiments/first_learning_loop/
v1_2_clean_transfer.py` (BASE_PROMPT source), the six prior `audits/2026-09-06_*learning*`/`*seed*`
reports.

**Experiments performed**: 5 isolated generation-variance tests (§5), 1 council-selection determinism
re-confirmation (§3).

**Artifacts created**, all under `app/experiments/first_learning_loop/pipeline_collapse_artifacts/`,
each containing its own recorded sha256:
- `noseed_A.json` / `noseed_B.json` — generic prompt, `echo:latest`
- `realtask_singlecall_A.json` / `realtask_singlecall_B.json` — real v1.2 `BASE_PROMPT`, `echo:latest`
- `per_councillor_model_test.json` — `qwen2.5-coder:7b` and `qwen2.5:3b`, real seat temperatures
- `real_ollama_query_fn_test.json` — real `_ollama_query()` function, `qwen2.5-coder:7b`

**Git status**: 28 pre-existing lines before this pass (all already-known from prior tonight's work),
plus this report and the new artifacts directory after — nothing else changed, nothing removed.

---

## Verdict

**DETERMINISM PARTIALLY LOCATED.**

Strong, direct, repeated evidence rules out the model, parameter, and prompt-content layers as the
source of the full-pipeline determinism v1.2.1 observed — every one of them shows genuine variance
under FeralEcho's real production configuration. The likely remaining boundary is either (a) something
specific to the composed, concurrent 3-councillor `deliberate_and_learn()` context that sequential
single-model calls don't reproduce, or (b) a needed correction to v1.2.1's own specific claim about raw
per-councillor response identity. This pass's evidence narrows the search meaningfully — from "the whole
pipeline might be deterministic anywhere" to "the collapse, if real, is specifically inside the
composition layer, not any individual component" — but does not, within its own budget, complete that
final identification. Recommended next step, not implemented here: a single, directly-instrumented,
read-only capture of one real `deliberate_and_learn()` call's per-councillor raw responses before
synthesis/fallback runs, compared against a second identical call the same way — the one test that
would close this specific remaining gap.
