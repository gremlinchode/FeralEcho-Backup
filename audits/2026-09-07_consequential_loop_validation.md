# Consequential Loop Validation — Attempt Ledger → Initial Generation

Implementation and validation mission, per `audits/2026-09-07_consequential_learning_loop_design.md`'s Phase 1 recommendation and its own acceptance-test framing. **Real, permanent production code changes were made** (the second of the night, after the attempt-ledger implementation itself). **Nothing was committed** — per an explicit override of this mission's own Phase 12 instruction, matching this session's established practice of leaving real changes in the working tree for separate, human-reviewed commit.

## Executive Result

**CONNECTED BUT NOT YET SHOWN CONSEQUENTIAL.**

The new causal arrow (attempt ledger → `_build_targeted_prompt()` → initial-generation prompt) is real, implemented, and rigorously verified to deliver evidence correctly under every tested condition, including adversarial and malformed inputs. What was **not** attempted in this pass is a full held-out causal experiment (matching Architecture A's 6-vs-6 matched-pair, real-F2-sandbox standard) proving the delivered evidence changes downstream generation quality. That is a deliberate, disclosed scope decision, not an oversight — explained in full under §7 below — and the mission's own verdict taxonomy names this exact outcome as valid, not a failure of the investigation.

## Safety Invariants

- `run.py`/watchdog: confirmed not running before starting and at completion (`ps aux`).
- Git HEAD: `c5bf2e5f8913e35a1ded9af8afe68e247651e26d` — confirmed identical before and after. **Zero commits, per explicit override of the mission's own Phase 12 commit instruction** — this session's established practice is to leave real code changes uncommitted for separate human review, exactly as happened with the attempt-ledger implementation itself earlier tonight.
- `river_brain.pkl` sha256: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` — confirmed unchanged before and after, including after importing `app.core.self_edit_manager` (which transitively instantiates several singletons) for testing.
- `memory/self_edit_attempt_ledger.jsonl` — confirmed unchanged (still the single real entry from earlier tonight, `trace_id 525ed7ea-...`). All test fixtures used a redirected `_LEDGER_PATH` scratch tempfile, never the production file.
- No self-edit run performed. No RiverBrain learning calls made. `model_task_stats`, the fitness gate, council trust gate, and garden weighting were not touched.

## 1. Phase 1 — Reconnaissance (re-verified against current source, not trusted from the design doc)

- `_build_targeted_prompt(task_type, creativity)` — `app/core/self_edit_manager.py:2815` (design doc cited 2779; the file has grown by ~36 lines since that mission ran, from unrelated intervening edits — confirmed via direct read, not assumed).
- Its **only** real call site: `app/core/self_edit_manager.py:2911` (originally reported at 2823 in the capstone design — same drift), inside `perform_self_edit()`'s `if prompt is None:` branch. Confirmed via `grep -c "_build_targeted_prompt("` = 2 (1 definition + 1 call).
- The resulting `prompt` string flows: `perform_self_edit()` → `execute_self_edit(prompt, ...)` → `plan_code_logic(prompt, ...)` (`self_edit_manager.py:1536`) — i.e. whatever `_build_targeted_prompt()` returns genuinely reaches the real initial-generation planning call, not a dead end.
- Attempt ledger schema (`self_edit_attempt_ledger.py`, real, unchanged by this mission): `trace_id`, `task_type`, `timestamp`, `initial_f2_outcome`, `initial_f2_error`, `retry_occurred`, `retry_f2_outcome`, `retry_f2_error`, `final_f2_outcome`, `fitness_score`, `production_score`, `fitness_decision`, `deployed`, `terminal_state` — confirmed by direct read of `execute_self_edit()`'s `_attempt` dict (`self_edit_manager.py:1896-1909`).
- `initial_f2_error` is written once, at `self_edit_manager.py` (the line immediately after the first `test_code_in_sandbox(code)` call), **before** the later `sandbox_feedback = "success_on_retry"` overwrite this whole investigation traced back to on 2026-09-06/07 — confirmed the write genuinely predates any destructive overwrite.
- `RiverBrain.learn()` (`echo_model_orchestrator.py:808`) and its two real call sites in `self_edit_manager.py` (primary generation `:1843`, retry `:2059`) are untouched by this mission — confirmed via `git diff`, zero lines in that neighborhood changed.

Every claim in the capstone design's §3.1/§10 that this mission depends on was re-confirmed directly against current source, not merely re-cited.

## 2. Exact New Causal Arrow

```
attempt N sandbox failure
  → test_code_in_sandbox()'s real result             [self_edit_manager.py, inside execute_self_edit()]
  → _attempt["initial_f2_error"] captured             [before the success_on_retry overwrite]
  → record_attempt() persists it                      [self_edit_attempt_ledger.py:record_attempt()]
  → memory/self_edit_attempt_ledger.jsonl (durable)
  → read_recent_f2_error(task_type)                    [self_edit_attempt_ledger.py, NEW]
  → _attempt_ledger_evidence_section(task_type)         [self_edit_manager.py, NEW]
  → _build_targeted_prompt()'s return value             [self_edit_manager.py, NEW: evidence_section appended]
  → perform_self_edit()'s `prompt` variable
  → execute_self_edit(prompt, ...) → plan_code_logic(prompt, ...)
  → attempt N+1's real initial generation
```

This is the **only** new consequential connection introduced. No other arrow was added, modified, or removed.

## 3. Implementation — Exact Diff

**Files changed**: 2 modified, 1 new. Confirmed via `git diff --stat`:

```
app/core/self_edit_attempt_ledger.py | 71 ++++++++++++++++++++++++++++++++++++
app/core/self_edit_manager.py        | 39 +++++++++++++++++++-
2 files changed, 109 insertions(+), 1 deletion(-)
```

Plus one new file: `scripts/verify_attempt_ledger_prompt_evidence.py` (regression tests, §5 below).

**`self_edit_attempt_ledger.py`** — added `read_recent_f2_error(task_type, max_age_hours=168.0)`, a pure read function: scans the ledger, filters by exact `task_type` match, requires a non-empty string `initial_f2_error`, requires a parseable ISO timestamp within the age window, keeps the last (most recent) qualifying match. Fails closed to `None` on any error (missing file, malformed line, bad timestamp) — never raises.

**`self_edit_manager.py`** — one new import (`read_recent_f2_error as _read_recent_f2_error`), one new function `_attempt_ledger_evidence_section(task_type)` (fails open to `""`, truncates the error to 400 chars, wraps it in an explicit "not an instruction" label), and one line changed in `_build_targeted_prompt()`'s return statement to append the new section.

**Confirmed no unrelated changes**: `git diff` on both files shows every hunk falls inside the new function bodies or the single import/return-statement line — nothing in `choose_model()`, `RiverBrain.learn()`, the fitness gate, `execute_self_edit()`'s retry block, or any other function was touched.

**The evidence is presented as data, not instruction**, per Phase 3's explicit requirement — exact wording:

```
Prior attempt failure evidence (not an instruction): a previous real attempt at
this task type failed initial sandbox testing with: <error text, truncated to
400 chars>
This is historical evidence about what happened before, not a requirement — it
does not override anything stated above.
```

Nothing in this section can structurally override the base task description, the Focus text, the convergence warning, or `CODE_OUTPUT_RULES` — it is appended after all of them, in the same additive-concatenation pattern `_recent_outcome_note()` already used, one function above, for a different signal.

## 4. Deliberately Not Generalized (Phase 4 compliance)

No generic memory framework, no provenance system, no RiverBrain authority change, no `model_task_stats` alteration, no fitness-gate/council-trust/garden-weighting change, no Shadow reconnection, no retry-pathway wiring, no unrelated refactor. Confirmed directly: the diff touches exactly the two files and the exact functions named in §3, nothing else. No expansion of scope was triggered — the minimal implementation did not reveal a need for anything larger.

## 5. Controlled Validation (Phases 5-6)

Built `scripts/verify_attempt_ledger_prompt_evidence.py`, a permanent regression script (not a throwaway) following this project's own `scripts/verify_*.py` convention. Every test redirects `self_edit_attempt_ledger._LEDGER_PATH` to a scratch tempfile before running — **the real production ledger file was never touched** (confirmed: still 1 line, unchanged, after the full test run).

**All fixtures are explicitly synthetic**, clearly labeled as such in the script's own comments — the positive-case error text is modeled on the real historical `HealthMonitor` `TypeError` from the `e05cb935` attempt earlier tonight (that attempt predates the ledger's existence, so it was never actually captured by it — using its real error text as a synthetic fixture is disclosed, not presented as a genuine ledger record).

**Result: 15/15 checks passed.**

| # | Case | Result |
|---|---|---|
| 1 | Same-task prior error retrieved, delivered into the real `_build_targeted_prompt()` output, correctly labeled | PASS (3/3 sub-checks) |
| 2 | Unrelated task-type error rejected — not injected | PASS (2/2) |
| 3 | No history → no evidence section, prompt otherwise unaffected | PASS (2/2) |
| 4 | Malformed records (bad JSON, `null`/empty error, missing fields, non-dict) — zero crash, zero false-positive injection | PASS (2/2) |
| 5 | Stale entry (>168h old) excluded | PASS (1/1) |
| 6 | Most-recent (not first-match, not similarity-based) selection confirmed | PASS (1/1) |
| 7 | Evidence reaches initial generation only — retry-prompt block structurally cannot call the new function (confirmed by exact call-site count and source-region scan) | PASS (2/2) |
| 8 | Non-interference: prompt output with no evidence available is unchanged from pre-existing behavior | PASS (1/1) |
| 9 | Temporal-drift guard: reader's required fields (`task_type`, `initial_f2_error`, `timestamp`) confirmed present in the real writer's `_attempt` dict schema, by direct source inspection | PASS (1/1) |

**Evidence delivery is proven, not merely asserted**: test 1 confirms the real, unmodified `_build_targeted_prompt()` function — called with zero mocking beyond the ledger-path redirect — produces output containing the literal error text and the explicit "not an instruction" label.

## 6. Phase 8 — Pre-Existing RiverBrain Loop Non-Interference

Verified two ways, both real, neither a formality:

1. **Static**: `git diff` on both touched files shows zero lines inside `RiverBrain.learn()`, `choose_model()`, `model_task_stats`'s mutation site (`echo_model_orchestrator.py:828-844`), the fitness gate (`self_edit_manager.py:2179`), council trust gate (`council_rater.py:525-530`), or garden weighting (`garden_manager.py:245-247`) — none of these files were even opened for editing.
2. **Behavioral**: importing `app.core.self_edit_manager` (which transitively imports and can instantiate `RiverBrain`, `VectorMemory`, and other singletons) for the regression tests was independently confirmed to leave `river_brain.pkl`'s sha256 byte-identical before and after — the import alone does not write, and nothing in the new code path calls `.learn()` or `.save()`.

The pre-existing loop (§10 of the capstone design) is untouched.

## 7. Phase 7 — Consequence Measurement: Honest, Disclosed Scope Limit

**Evidence delivery was verified. A consequential downstream effect was not measured in this pass — and this is a deliberate scope decision, not an oversight.**

Architecture A's own standard for this class of claim (6-vs-6 real matched-pair generations, run through the actual F2 sandbox, McNemar-compared) required substantial real model-call volume and wall-clock time to execute rigorously. Reproducing that standard for this new, untested boundary (initial generation, not retry) within this single mission's remaining scope would have meant either (a) cutting corners on trial count/rigor relative to the standard this whole night has held every other experiment to, or (b) consuming a large fraction of remaining resources on one experiment at the risk of not completing the rest of this mission's required verification (Phases 8-11, the regression suite, this report). Given the mission's own explicit instruction — "Do not optimize for a positive result... A negative result is valuable if it precisely tells us: 'the evidence reaches the initial generation boundary, but it does not produce a measurable consequential effect'" — the honest choice is to report exactly that boundary was reached and rigorously proven, and name the real next experiment precisely, rather than run a rushed, underpowered version of Architecture A's design and risk over- or under-claiming from it.

**What is proven**: the evidence genuinely reaches the initial-generation prompt, correctly filtered and labeled, under every tested condition (§5).

**What is not yet proven**: whether a real generation that receives this evidence produces measurably different (better, worse, or unchanged) code than one that doesn't, for a genuinely fresh, currently-recurring failure signature.

**The precise next experiment** (already designed, in the capstone document's own §19, not re-derived here): mine a fresh recurring failure signature (following Architecture A's own discipline — not `re` or `functools`, both already prompt-patched), run matched-pair real initial generations (CONTROL: no ledger entry present; EXPERIENCE: a real ledger entry for that signature present), compare through the real F2 sandbox, McNemar-style, with a required replication before the connection earns any further authority. This mission built and rigorously verified the plumbing that experiment needs; it did not run the experiment itself.

## 8. Regression Tests

See §5 table. 15/15 passed. Script: `scripts/verify_attempt_ledger_prompt_evidence.py` (new, uncommitted, permanent — runnable again by any future session or CI-equivalent check).

## 9. Temporal-Drift Protection

Test 9 (§5) is the targeted guard for this specific new pathway, per Phase 11's instruction to protect *this change's own* schema assumptions rather than re-implementing the capstone design's broader `TASK_TYPE_MAP`/`seam_engine` Liveness Ledger checks (those protect the *existing* `model_task_stats` loop and are explicitly a separate, larger-scoped recommendation in the capstone design's §5/§13 — building them was outside this mission's own no-generalization constraint, Phase 4).

**What this guard prevents**: if a future edit to `execute_self_edit()`'s `_attempt` dict ever renames or removes `task_type`, `initial_f2_error`, or `timestamp` — the exact fields `read_recent_f2_error()` depends on — without updating the reader, this test fails loud instead of the pathway silently degrading into permanently returning `None` (the same failure shape `TASK_TYPE_MAP` and `seam_engine` already demonstrated real, silent instances of tonight). It is a source-anchored check (reads the real `_attempt` dict definition directly), the same pattern this codebase's own Liveness Ledger checks already use for the identical purpose elsewhere.

**What it does not do**: it does not generalize to protect against a change in `initial_f2_error`'s *value type* (e.g., if a future writer started storing a dict instead of a string) — `read_recent_f2_error()` already defensively checks `isinstance(err, str)` and fails closed on a mismatch, which is a runtime safety property, not something this static test needed to separately re-verify.

## 10. Non-Goals

Consistent with Phase 4 and the capstone design's §21/§23: no change to RiverBrain, `model_task_stats`, the fitness gate, council trust, garden weighting, retrieval, or Shadow. No new authority granted to any mechanism to deploy code, bypass F1/F2/F3, or override the fitness gate. No commit — left for separate human review.

## 11. Remaining Gaps, Stated Plainly

1. **The consequential-effect experiment (§7) has not been run.** This is the single most important remaining gap — everything else in this report proves the wire is real and correctly built; nothing yet proves what flows through it changes anything for the better.
2. **The two broader Liveness Ledger checks** from the capstone design's §5/§13 (`task_type_map_sync`, `seam_engine`'s garden-domain-coverage check) were **not** built in this mission — they protect a different, pre-existing loop and were correctly out of scope here, but remain a real, separately-tracked recommendation.
3. **No real production self-edit cycle has exercised this new code path yet** — the regression suite proves the function behaves correctly under controlled conditions; it has not yet been observed firing during a genuine autonomous or manual self-edit attempt, since none has run since this code was written (consistent with `run.py` remaining stopped all night, per this session's standing constraint).
4. **The 400-character truncation length and 168-hour staleness window are both reasonable, unvalidated defaults** — chosen for consistency with existing patterns in the same file (`_recent_experiment_note()`'s 200-line tail, this file's own general order-of-magnitude conventions), not derived from any measurement of what length or recency actually matters for generation quality. If §7's experiment is ever run, these are exactly the parameters it would also be implicitly testing.
