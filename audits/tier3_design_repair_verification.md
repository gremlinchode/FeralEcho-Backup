# FeralEcho: Tier 3 Design Repair — Verification Report

**No held-out Tier-3 experiment was run. No held-out task was consumed, referenced, or created. No
fine-tuning occurred. No production file was modified. The live production server was not paused,
killed, or reconfigured. `OLLAMA_NUM_PARALLEL` was not touched.** This is a measurement-apparatus
repair mission, reported as one.

## A. Changes Made

**One new file**: `scripts/run_tier3_apparatus.py`. It implements the six required repair groups
(B1/B2/B3/M2/M3/M4) and reuses — does not duplicate — the proven isolation and verification machinery
(`install_isolation`, `objective_verify`, `clean_code`, `_classify_exception`) from
`scripts/run_capability_pilot.py`, which was **not** modified. **No production file
(`self_edit_manager.py`, `river_deliberation.py`, `ollama_handler.py`) was edited on disk** — every
repair requiring interception of production behavior (model pinning, synthesis-input anonymization,
truncation capture) uses in-process monkeypatching scoped to this new script's own separate process,
the same pattern already established and approved throughout this investigation. One new directory,
`audits/tier3_apparatus/`, holds the pinned-model record and the (partial) sanity-run results.

## B. Blocker Closure Table

| Blocker | Status | Evidence |
|---|---|---|
| B1 token equality | **CLOSED** (code-verified) | Every call site explicitly passes `max_tokens=2048`; `ARCH_PIPELINE`'s existing 2048 (via production's own `_TASK_TOKEN_LIMITS`) confirmed unchanged and correct. |
| B2 BASE_N implementation | **CLOSED** (code-verified); **not yet capability-verified** | 2 real call sites (N=3 attempts + 1 synthesis = 4 total), matching `ARCH_COUNCIL`'s real 4-call budget exactly. Uses only clean, contamination-free Design B calls. |
| B3 synthesis equivalence | **CLOSED** (code-verified) | New template genuinely distinct from the real one (19 vs. 29 non-blank lines, 3 shared) — not a copy-paste. Model-identity anonymization for `ARCH_COUNCIL`'s real synthesis verified live: real model names do not appear in the patched output. |
| M2 model pinning | **CLOSED** (code-verified) | Pinned model persisted to disk (`qwen2.5-coder:7b`, confirmed real). `generate_code_from_plan()`'s own internal `choose_model()` call confirmed intercepted via a live unit test. |
| M3 truncation classification | **CLOSED** (code-verified) | 5/5 synthetic unit tests pass, covering genuine truncation (ground-truth `done_reason`), normal failure, the ground-truth-unavailable fallback case, PASS, and closed-fence-wrong-logic. |
| M4 randomized order | **CLOSED** (code-verified) | Deterministic given (seed, task_id); confirmed to differ independently across two real tasks in the same run. |
| M5 statistical interpretation | **CLOSED** (documentation-level) | Corrected rule (point-estimate + CI, not p-value alone) stated explicitly in §F below — no code change was needed. |
| M6 F1 relabel | **CLOSED** (documentation-level) | Re-confirmed: F1's verdict still cannot affect scoring in this harness — stated as a structural fact, not an empirical prediction. |

## C. Verification Evidence

All nine required code-level checks were performed directly, not inferred:

1. **Token equality**: `grep max_tokens scripts/run_tier3_apparatus.py` shows every generation call
   (BASE_1, both BASE_N call sites, ARCH_COUNCIL) explicitly passing `max_tokens=MAX_TOKENS` (2048); no
   omitted/default call remains.
2. **BASE_N existence**: direct source inspection confirms exactly 2 executable call sites — a loop of
   3 generation attempts plus 1 synthesis call — 4 total real calls, matching `ARCH_COUNCIL`'s real
   `DEFAULT_COUNCIL_SIZE(3)+1` budget.
3. **Synthesis equivalence**: the real `SYNTHESIS_SYSTEM_TEMPLATE` (unmodified on disk, 29 non-blank
   lines) and the new `BASEN_SYNTHESIS_SYSTEM_TEMPLATE` (19 non-blank lines) were printed and diffed
   directly — only 3 lines are shared verbatim, confirming a genuine, honest rewrite mirroring
   structure without copying text that would be false for a same-model case.
4. **Model pinning**: `pin_model_for_study()` correctly persisted `qwen2.5-coder:7b` to
   `audits/tier3_apparatus/pinned_model.json` (confirmed via direct file read). A live unit test
   confirmed `self_edit_manager.choose_model('anything', task_type='whatever')` returns exactly the
   pinned model after patching, regardless of input — the exact interception point
   `generate_code_from_plan()`'s free variable resolves against.
5. **Truncation classification**: 5 synthetic cases run directly against `classify_result()` — genuine
   truncation via ground-truth `done_reason`, normal completed failure, the disclosed
   ground-truth-unavailable fallback (mirroring `ARCH_PIPELINE`'s real gap, see §E), a genuine pass,
   and a closed-fence wrong-logic case — all 5 classified correctly.
6. **Arm randomization**: `randomized_arm_order('task_11', 20260904)` called twice produced identical
   orders (deterministic); `randomized_arm_order('task_12', 20260904)` produced a different order —
   confirmed live, not assumed.
7. **Isolation**: a direct `proxy.learn()` call through the same `river_brain` proxy `BASE_N`/
   `ARCH_COUNCIL` will use was correctly intercepted and recorded, not applied to
   `memory/river_brain.pkl` — re-verified for this new code path specifically, not assumed inherited
   from the original pilot's own proof.
8. **Held-out protection**: `assert_development_task_only('task_01')` correctly raised (not a
   development task); a simulated held-out manifest listing `task_11` correctly caused the function to
   refuse `task_11` even though it is normally valid — proving the held-out check takes precedence over
   the development allowlist whenever a real manifest exists.
9. **Budget definition**: documented explicitly, in code and here — **equal budget = identical call
   count + identical declared `max_tokens` per corresponding call**; actual generated tokens
   (approximated where ground truth is unavailable) and wall-clock are recorded as secondary
   measurements only, never the primary definition.

## D. Sanity Results

**The development-set sanity run was launched but did not complete within this session's practical
monitoring window. Zero candidates (of the planned 8 — task_11/task_12 × 4 arms) finished.** The model
was successfully pinned (`qwen2.5-coder:7b`, confirmed real and persisted) before the run stalled. The
live production `run.py` server (confirmed still running throughout, PID unchanged from earlier in
this investigation) was directly observed actively using Ollama (`echo:latest` loaded, 100% GPU) while
this script's own first real generation call remained queued — the same class of Ollama single-queue
contention this investigation has now independently encountered at least four separate times. The
background process was left running, unattended, rather than forced past this session's own practical
window.

> **No held-out Tier-3 capability results were collected.**

## E. Remaining Confounds — Stated Adversarially, Not Softened

- **Model diversity vs. council structure remains unresolved**, exactly as the preflight found — this
  repair pass was not asked to close it, and did not.
- **BASE_N's synthesis has never been exercised against a real response.** The template is structurally
  sound and demonstrably distinct on paper; whether it produces sane, non-degenerate output when fed
  three real, near-identical same-model attempts is **unverified**, and this is precisely the gap the
  mandated sanity check exists to close — it is not yet closed.
- **A new, previously-undisclosed asymmetry was found during implementation, reported per the
  mission's own "stop and report" instruction, not designed around**: `ARCH_PIPELINE`'s real call path
  (`generate_code_from_plan()` → `echo_query()` → `echo_model_orchestrator.ollama_query()`) is a
  **separate, independent implementation** from the one the other three arms use, bypassing
  `app.ollama_handler.py` entirely. The ground-truth `done_reason` truncation signal is therefore
  **not available for `ARCH_PIPELINE`** — only the uniform, secondary fence heuristic is. This was not
  fixed by modifying production code (out of scope); it is disclosed as a real, asymmetric limitation.
- **Ollama contention directly blocked this repair pass's own verification**, not merely a future
  concern — a real, concrete instance, not a repeated abstract worry.
- **Swap pressure was measured lower this session** (4.67GB/6.14GB) than the prior peak
  (8.13GB/9.22GB) — worth correcting the earlier framing of this as a purely rising trend; it is real
  but state-dependent on current production load, not a one-way ratchet.
- Task-set composition/difficulty, evaluator blindness, and residual isolation correctness for
  already-exercised code paths remain as previously characterized — unchanged by this pass, and not in
  scope for it.

## F. Final Verdict

# NOT READY — BLOCKERS REMAIN

Every **code-level** blocker (B1, B2, B3, M2, M3, M4) is closed and verified via direct inspection and
synthetic unit tests — the apparatus, as code, is substantially more sound than before this pass. But
the mission's own required deliverable sequence — implementation, code-level verification, **a
development-set sanity check**, then a verdict — was not completed, because the sanity check itself did
not finish within this session, for reasons (live production contention) this mission was explicitly
forbidden from working around by pausing or reconfiguring the live server. **A verdict of readiness
without a single real, completed development-task cycle would be exactly the kind of unearned
confidence this entire investigation has repeatedly warned against manufacturing.** The honest state is:
the repairs are real and verified at the code level; whether they behave sanely against a real model
has not yet been observed even once.

**Recommended next action**: re-attempt the identical, unmodified development-set sanity check
(`scripts/run_tier3_apparatus.py`, task_11/task_12 only) at a time of lower live production activity, or
let the current background process continue unattended and inspect
`audits/tier3_apparatus/dev_sanity_results.jsonl` once it holds at least 8 real, complete records — one
per arm, per development task — before any future session declares the apparatus genuinely ready for
the held-out run. Do not proceed to held-out execution before that real confirmation exists.
