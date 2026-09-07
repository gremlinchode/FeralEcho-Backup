# Attempt-Level Provenance Feasibility

Forensic/design feasibility mission. No production code, logs, or state modified. No implementation attempted, per the mission's explicit stop condition.

## Safety Invariants

| Check | Before | After |
|---|---|---|
| `run.py` / watchdog process | none running | none running |
| Port 5000 | unbound | unbound |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | `2cf2d95009943797db5ec41fea9b4021634fd5e6` (unchanged) |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | unchanged |
| `SELF_EDIT.log` | read-only | untouched |
| `self_edit_outcomes.jsonl` | read-only, 179 lines | untouched, still 179 lines |

No self-edit was run in this mission. All evidence for the real attempt comes from the immediately-preceding mission's already-existing artifacts (`memory/reflection_shard.jsonl`, `memory/interaction_log.jsonl`, `memory/council_deliberations.jsonl`, `memory/SELF_EDIT.log`, `memory/self_edit_cooldown.json`) and `audits/2026-09-06_real_trace_f2_provenance_liveness.md`.

## Phase 1 — Real Lifecycle Trace

Traced directly from `app/core/self_edit_manager.py::execute_self_edit()` (lines 1854–2211, current source, re-verified this session):

```
trace_id minted (line 1887, str(uuid.uuid4()), once per attempt)
   ↓
reflection_entry created in memory (line 1904-1911: prompt, task_type,
  generated_code=None, timestamp, sandbox_feedback=None, result="pending")
  — NO trace_id field. Held in memory only until a terminal branch calls
  save_reflection(reflection_entry) → appends to memory/reflection_shard.jsonl.
   ↓
plan_code_logic(prompt, trace_id=trace_id)          [real council deliberation,
   ↓                                                  logged: interaction_log.jsonl,
                                                       council_deliberations.jsonl,
                                                       both carry trace_id]
generate_code_from_plan(plan, trace_id=trace_id)    [primary candidate generation,
   ↓                                                  same trace_id, same logging]
code cleaned (strip fences / extract block / strip self-calls)
   ↓
reflection_entry["generated_code"] = code (in-memory only)
   ↓
_validate_imports() — hallucination gate. FAIL → append_to_journal("SELF_EDIT",
   ↓  result: import_hallucination) + save_reflection() (terminal, durable)
scan_for_unsafe_operations() — F1. FAIL → append_to_journal(result: safety_blocked)
   ↓  + save_reflection() (terminal, durable)
test_code_in_sandbox(code) — F2, FIRST PASS.
   ↓
   ├─ success=True → river.learn_from_sandbox_outcome(...) [neutralized in this
   │                  session's experiments], continue.
   │
   └─ success=False → river.learn_from_sandbox_outcome(success=False, ...)
        reflection_entry["sandbox_feedback"] = f"failed: {sandbox_error}"  ← SET
        reflection_entry["result"] = "failed"                              ← SET
        (comment at lines 1980-1989: deliberately NOT saved here — not a
        terminal state yet. This in-memory value is the ONLY place the
        first-attempt F2 error text exists at all, anywhere.)
        clean_error = _sanitize_sandbox_error(sandbox_error)   ← local var
        logging.warning(f"Sandbox test failed: {clean_error}...")   ← goes to
             the Python logging module, NOT append_to_journal(). No line is
             written to memory/SELF_EDIT.log for the first F2 failure.
        retry_prompt built with clean_error embedded (single use)
        retry_code = echo_query(retry_prompt, trace_id=trace_id)   [real,
             logged: interaction_log.jsonl + council_deliberations.jsonl,
             same trace_id — this retry call IS durably identifiable]
        test_code_in_sandbox(retry_code) — F2, RETRY PASS.
           ├─ success=True →
           │    reflection_entry["sandbox_feedback"] = "success_on_retry"  ← OVERWRITES
           │      the original "failed: {sandbox_error}" value set above.
           │      The original F2 error text is gone from reflection_entry
           │      from this point forward, in memory, permanently.
           │    reflection_entry["result"] = "success"       ← OVERWRITES "failed"
           │    reflection_entry["generated_code"] = retry_code
           │    reflection_entry["model_used"] = retry_model_name
           │    (still not saved — comment lines 2035-2041: staging/dry_run/
           │    fitness gate can still change the outcome)
           │
           └─ success=False → river.learn_from_sandbox_outcome(False, ...),
                logging.warning(...) only (no journal line, no save).
                reflection_entry keeps its FIRST failure's sandbox_feedback/
                result (never overwritten in this branch) — code/model_used
                fields also stay at the stub from step "Step 3" below.
   ↓
validate_code(code) — AST syntax check. FAIL → code replaced with a fixed
   stub string, append_to_journal(result: invalid_syntax) (no save_reflection
   call at this specific line — falls through to staging test below, which
   will then fail against the stub).
   ↓
_stage_and_import_test() — staging import test (per-call-unique file).
   FAIL → append_to_journal(result: staging_import_failed) + save_reflection()
   (terminal, durable). PASS → continue.
   ↓
dry_run branch: if dry_run=True, save_reflection() here with
   result="success_dry_run" + staging_path=call_staging_file (terminal,
   durable), return. [Not relevant to the real attempt analyzed below —
   that attempt had dry_run=False.]
   ↓
_self_edit_deploy_lock acquired (real concurrency guard)
   ↓
_score_response_quality(code, "coding") → candidate_quality (int, 0-4 scale)
_score_response_quality(current production file, "coding") → current_quality
   ↓
   ├─ candidate_quality < current_quality → REJECTED.
   │    reflection_entry["result"] = "rejected_not_improvement"
   │    reflection_entry["candidate_quality"] = candidate_quality
   │    reflection_entry["current_quality"] = current_quality
   │    save_reflection(reflection_entry)  ← TERMINAL, DURABLE (reflection_shard.jsonl)
   │    append_to_journal("SELF_EDIT", "... result: rejected_not_improvement |
   │       candidate_quality=X current_quality=Y")  ← TERMINAL, DURABLE (SELF_EDIT.log)
   │    return False, "Rejected: ..."
   │    record_pending_outcome() is NEVER CALLED on this path.
   │
   └─ candidate_quality >= current_quality → backup_existing_code() +
        save_code(code)  [real production write to app/core/self_edit_generated.py]
           ↓
        load_self_edit_module()
           ├─ None (F3 tripped or file missing) → result="load_blocked",
           │    save_reflection() + append_to_journal(). record_pending_outcome()
           │    still NOT called.
           │
           └─ loaded successfully →
                reflection_entry["result"] = "success"
                save_reflection(reflection_entry)   ← TERMINAL, DURABLE
                append_to_journal("SELF_EDIT", "... result: success ...")
                record_pending_outcome(task_type, trace_id=trace_id)   ← THE
                    ONLY CALL SITE OF record_pending_outcome() ANYWHERE IN THIS
                    FUNCTION. Appends {edit_id, task_type, edit_timestamp,
                    status:"pending", trace_id} to memory/self_edit_outcomes.jsonl.
                take_snapshot("post_self_edit")
                return True, "Success"
```

**Currently recoverable per stage, and where:**

| Stage | Durable? | Where |
|---|---|---|
| Attempt identity (trace_id) | Yes | `interaction_log.jsonl`, `council_deliberations.jsonl` (every real `echo_query()`/deliberation call this attempt makes) |
| Candidate identity (final code only) | Yes, but only the LAST version | `reflection_shard.jsonl`'s `generated_code` field — overwritten by retry if retry ran |
| F2 first-pass result | **No** | Held in `reflection_entry` in memory only; overwritten and lost if retry succeeds. Never in `SELF_EDIT.log` (no `append_to_journal` call on this branch) |
| Retry occurred / retry result | Partially | `reflection_shard.jsonl`'s `sandbox_feedback` field says `"success_on_retry"` (a boolean-ish signal that a retry happened and passed) but carries zero information about *why* the first attempt failed |
| Final F2 outcome | Yes | Implied by reaching the fitness-gate stage at all (F2 failure with no retry recovery is its own terminal branch with no journal line either — see below) |
| Fitness score (candidate vs. current) | Yes | `reflection_shard.jsonl` (`candidate_quality`, `current_quality`) and `SELF_EDIT.log` (same two numbers in the log line) — but ONLY on the `rejected_not_improvement` branch. If the candidate is deployed, these numbers are computed but never written anywhere (confirmed: the `success` branch's `save_reflection()`/`append_to_journal()` calls do not include `candidate_quality`/`current_quality`) |
| Deployment decision | Yes | `SELF_EDIT.log`'s `result:` field values (`rejected_not_improvement`, `success`, `load_blocked`, etc.) |
| Durable outcome record | Only if deployed | `self_edit_outcomes.jsonl`, via `record_pending_outcome()`, reachable only from the `success` branch |

## Phase 2 — `record_pending_outcome()` and the Semantics of `self_edit_outcomes.jsonl`

Read directly, `app/core/self_edit_outcome_tracker.py`. The module's own docstring (lines 1-11) states its purpose plainly:

> "Measures whether a self-edit actually improved behavior, using signals independent of the F1/F2/F3 safety pipeline that gates the edit itself (quality_score, council_rating, human terminal ratings — **before vs. after a fixed window around each successful deploy**)."

`evaluate_pending_outcomes()`/`_dry_run_quality_in_window()`/`_mean_in_window()`/`_human_ratings_in_window()` all implement exactly this: for a given `edit_timestamp`, compute the mean of some real signal in `[edit_timestamp - 25min, edit_timestamp)` (pre) and `[edit_timestamp, edit_timestamp + 25min)` (post), and report the delta. The `_EVAL_WINDOW_MINUTES = 25` comment explicitly reasons about avoiding cross-contamination between *consecutive real deploys* — the whole mechanism's unit of analysis is "one specific moment production genuinely changed."

**This is intentional, not an oversight.** A rejected or F1/F2-blocked attempt has no `edit_timestamp` at which anything in production actually changed. Running the identical pre/post-window machinery against a non-event would either (a) compute a delta of ~0 that means "no measurable change occurred" for a structurally different reason than a real deploy that failed to help — conflating "nothing happened" with "something happened and didn't work" under the same value — or (b) require a new field just to disambiguate the two, at which point the file is already carrying two different kinds of rows under one schema. `record_pending_outcome()`'s docstring — "Called once, right after a self-edit deploys successfully" — is consistent with this being a deliberate scope boundary, not a bug.

**Would adding rejected/failed attempts to the same file corrupt its meaning?** Yes, if done naively (mixed rows, same schema, same downstream consumer). `self_edit_outcome_tracker.py`'s entire analytical machinery assumes every row it reads represents a real production state transition it can center a window on. A rejected-attempt row has no such transition. This is the direct evidence behind Phase 6's Model comparison below.

## Phase 3 — Minimum Attempt-Level Schema

Fields restricted to what Phase 1 confirms are already computed somewhere in the real pipeline (no invented data):

**ATTEMPT FACTS** (objective record of what happened, independently checkable against F1/F2/the fitness scorer):

```
trace_id                str   — already minted, already threaded through
                                 echo_query() calls; just needs propagating
                                 into reflection_entry, which currently lacks it
attempt_timestamp        str   — reflection_entry["timestamp"], already set
task_type                str   — already set
prompt                   str   — already available (the full self-edit prompt)
f1_result                enum  — {passed, import_hallucination, safety_blocked}
                                 — already determined, just not persisted as
                                 a field distinct from the journal line text
f2_first_pass_result     enum  — {passed, failed} — CURRENTLY LOST (see Phase 1)
f2_first_pass_error      str|null — CURRENTLY LOST; only exists as a local
                                 variable (`sandbox_error`) at the moment of
                                 failure
retry_occurred            bool  — derivable today only as a side effect of
                                 sandbox_feedback=="success_on_retry" on
                                 successful retries; NOT recoverable at all
                                 today when the retry also fails, since that
                                 branch has zero durable trace
f2_retry_result           enum|null — {passed, failed, not_attempted}
f2_final_result           enum  — {passed, failed} — this is what F1/staging
                                 downstream actually consumed
staging_result            enum  — {passed, failed} — already determined
candidate_quality         int|null — already computed (fitness gate), 0-4
current_quality           int|null — already computed, 0-4
fitness_decision          enum  — {deployed, rejected_not_improvement,
                                 not_reached (blocked earlier)}
deployed                  bool  — already knowable from which terminal branch
                                 was reached
```

**OUTCOME / DIAGNOSIS CLAIMS** (interpretive, NOT objective — must stay separate, per the mission's own critical rule):

```
causal_hypothesis         str|null  — e.g. _sanitize_sandbox_error()'s output;
                                      currently computed as `clean_error` and
                                      discarded. This is a CLAIM about why F2
                                      failed, not an independently-verified fact.
diagnosis_confidence      enum|null — no existing field computes this today;
                                      would have to be added net-new, not
                                      reused from anywhere
```

The explicit split matters because `f2_first_pass_result: failed` is a fact the trusted sandbox itself produced — it can be trusted at face value. `causal_hypothesis: "missing import"` is the *model's own guess* about why, wrapped by `_sanitize_sandbox_error()`'s simple line-extraction heuristic (it just returns the first line containing `SyntaxError`/`RuntimeError`/`Error:`, or a 200-char truncation — it does not verify the diagnosis is correct). Conflating the two into one "verified" record would repeat exactly the failure mode the Minimal Relevance Gate and Provenance+F2 missions already demonstrated tonight (a plausible-sounding claim treated as ground truth).

## Phase 4 — Real-Attempt Reconstruction (`trace_id = e05cb935-e74e-4ce1-8313-e8d090f0cafa`)

Source: `memory/reflection_shard.jsonl` (entry `timestamp: 2026-09-07T03:54:32.221810`), `memory/interaction_log.jsonl` (3 matching entries), `memory/council_deliberations.jsonl` (1 matching entry, `source: real_deliberation`), `memory/SELF_EDIT.log` (1 matching line, `142849`), `memory/self_edit_cooldown.json`, and `audits/2026-09-06_real_trace_f2_provenance_liveness.md` (the prior mission's own captured runtime output — NOT a durable production file).

| Field | Value | Status | Source |
|---|---|---|---|
| `trace_id` | `e05cb935-e74e-4ce1-8313-e8d090f0cafa` | **OBSERVED** | `interaction_log.jsonl` ×3, `council_deliberations.jsonl` |
| `attempt_timestamp` | `2026-09-07T03:54:32.221810` | **OBSERVED** | `reflection_shard.jsonl` |
| `task_type` | `"coding"` | **OBSERVED** | `reflection_shard.jsonl`, `interaction_log.jsonl` |
| `prompt` | "Autonomous self-edit targeting 'coding' task performance... reduce its average response length by 20%..." | **OBSERVED**, full text present | `reflection_shard.jsonl` |
| `f1_result` | passed (no `import_hallucination`/`safety_blocked` journal line exists for this window) | **DERIVED** (absence of a blocking journal line, not a positive record) | `SELF_EDIT.log` (checked full `2026-09-07T03:5[0-9]` window, only one substantive line for this attempt) |
| `f2_first_pass_result` | failed | **DERIVED** — inferable only because `sandbox_feedback` ended as `"success_on_retry"`, which mechanically implies a first failure occurred | not directly stored anywhere; inferred |
| `f2_first_pass_error` | `TypeError: HealthMonitor.__init__() missing 1 required positional argument: 'average_response_length'` | **UNAVAILABLE from production data.** This text exists *only* in the prior mission's own runtime capture (`audits/2026-09-06_real_trace_f2_provenance_liveness.md`), which happened to observe stdout/exception text live. Confirmed by direct search: zero occurrences of `HealthMonitor` or this error text anywhere in `SELF_EDIT.log` (142,849 lines) or `reflection_shard.jsonl`'s stored value (`sandbox_feedback` is the string `"success_on_retry"`, not the original error). If that prior mission had not independently logged it, this information would be gone. | — |
| `retry_occurred` | true | **DERIVED** (from `sandbox_feedback == "success_on_retry"`) | `reflection_shard.jsonl` |
| `f2_retry_result` | passed | **DERIVED**, same field | `reflection_shard.jsonl` |
| `f2_final_result` | passed | **OBSERVED** (implied by reaching the fitness-gate stage; a final F2 failure would have produced a different terminal branch entirely, with the stub replacing `code`) | — |
| `staging_result` | passed | **DERIVED** (a staging-import failure has its own distinct terminal `result` value, `staging_import_failed`, which does not appear for this attempt) | absence of that value in `SELF_EDIT.log`/`reflection_shard.jsonl` |
| `candidate_quality` | 3 | **OBSERVED** | `reflection_shard.jsonl`, `SELF_EDIT.log` |
| `current_quality` | 4 | **OBSERVED** | `reflection_shard.jsonl`, `SELF_EDIT.log` |
| `fitness_decision` | `rejected_not_improvement` | **OBSERVED** | both |
| `deployed` | false | **OBSERVED** (`self_edit_generated.py` unmodified, `self_edit_backups/` gained no new file, `self_edit_outcomes.jsonl` unchanged at 179 rows) | independently re-verified this session |
| `causal_hypothesis` | "missing import" / "missing constructor argument" (paraphrased from `_sanitize_sandbox_error()`'s intended behavior) | **UNAVAILABLE** — never computed as a stored value at all for this attempt; the function that would compute it (`_sanitize_sandbox_error`) was called, but its return value (`clean_error`) was only ever used to build the retry prompt text, never persisted | — |
| `final generated_code` | the retry-corrected candidate (full text present) | **OBSERVED** | `reflection_shard.jsonl` |
| `model_used` | `echo:latest` | **OBSERVED** (this is the retry model, since a successful retry overwrites the original `model_used`; the *primary*-attempt model is not separately recoverable) | `reflection_shard.jsonl` |
| Cooldown side-effect | `last_any_autonomous_edit` advanced `1788729168.45 → 1788753272.21` | **OBSERVED**, corroborating evidence this was a real, unforced pipeline run | `self_edit_cooldown.json` |

Summary: **9 fields OBSERVED, 5 DERIVED (all correct but requiring inference from an indirect signal, not a direct field), 2 UNAVAILABLE** (the actual F2 failure text, and any stored causal hypothesis — the two pieces of information a future credit-assignment mechanism would most need).

## Phase 5 — Learning Value

**What an attempt-level ledger, populated with the fields above, could support:**

- **Retry-diagnosis credit assignment** (the exact gap the Hot Stove/Credit Assignment audit named): `causal_hypothesis` currently only lives for the duration of one retry prompt. Persisting it — clearly labeled as a claim, not a verified fact — would close the specific "attribution dies at the call frame" finding from that audit (`self_edit_manager.py:1999-2015`), without requiring any new diagnosis mechanism; `_sanitize_sandbox_error()` already exists and already runs.
- **Failure-recurrence detection**: with `f2_first_pass_error` preserved and `trace_id`/`attempt_timestamp` attached, a future mechanism could answer "has this specific failure signature (e.g. `functools` NameError) recurred across N independent attempts" directly from structured data, rather than the current approach of grepping raw log text (which is how every one of tonight's `functools`/`re` recurrence counts were actually computed).
- **Trace→F2 verification** (the exact mechanism the two preceding missions this session tested): an attempt ledger row is a strictly richer join target than `self_edit_outcomes.jsonl` alone, because it exists for *every* attempt, not just the rare successful deploy — directly addressing this session's finding that a real trace_id/F2-verdict join currently only has a ~0% chance of firing in practice, since `record_pending_outcome()` is gated behind an event (successful deploy) that this session's own real test showed is uncommon.
- **A denser dataset for the fitness-scorer-ceiling question** (`PENDING_DECISIONS.md` #19 — `current_quality` reads a constant 4/4 across the observable history of real deploy decisions). This attempt independently reproduces that exact pattern (`current_quality: 4`), reinforcing rather than resolving that open question — an attempt ledger records more data points of the *same* metric, it does not change what the metric measures.

**What it cannot establish, even fully built and populated:**

- It does not itself constitute retrieval, relevance judgment, or behavioral influence — every finding from the Retrieval Capacity Proof and Minimal Relevance Gate missions (raw cosine similarity favors lexical overlap over causal relevance; an LLM gate can be fooled by a plausible-but-wrong narrative) applies identically to querying this new ledger. An attempt ledger is a *source of evidence*, not a fix for the two already-demonstrated downstream failure modes.
- It cannot retroactively recover what already happened before it existed — the `functools` recurrence history and this exact attempt's own F2 error text are permanently gone from durable storage; a ledger only stops future loss.
- `causal_hypothesis` remains an unverified claim regardless of how faithfully it's stored — storing `_sanitize_sandbox_error()`'s output durably does not make that output more *correct*, only more *durable and inspectable*. The Provenance+F2 mission's own critical finding (event-verification ≠ diagnosis-truth) applies directly: an attempt ledger row proves an F2 result really happened; it does not prove the attached hypothesis about why is right.

## Phase 6 — Model A vs. Model B

**Model A — `self_edit_outcomes.jsonl` = successful deployments only (current state).**
- Preserves clean, uncorrupted semantics for the one question it already answers well: "did a real production change measurably help." Nothing about this mission's evidence suggests that mechanism is broken or should change.
- Real, demonstrated cost: on this session's own real test, the one attempt exercised was a genuine, unforced, representative production cycle — and it landed in the branch this file structurally cannot see. Combined with Finding 48's own historical figure (0% real-deploy success across 71 recent attempts, most rejected by the fitness gate exactly as designed), Model A as the *sole* durable record means the overwhelming majority of Echo's actual self-edit experience produces zero lasting evidence trail beyond a single terse `SELF_EDIT.log` line — and, as Phase 4 shows, even that line omits the richest part (the causal hypothesis, the first-attempt failure text).

**Model B — successful outcomes (unchanged) + a separate attempt-level experience ledger.**
- Requires a new file/schema, new write call sites (one per terminal branch in `execute_self_edit()`, of which there are 7), and a retention/pruning policy (this project already has precedent for exactly this — `log_retention.py`'s cap-and-rotate pattern, `_MAX_SELF_EDIT_PLANS`/`_MAX_SNAPSHOTS`-style file-count caps).
- Does not touch or risk `self_edit_outcomes.jsonl`'s existing, working semantics — genuinely additive, not a refactor of a live mechanism.
- Directly closes the specific evidence-loss boundary this mission was asked to evaluate, and gives the credit-assignment gap named by the Hot Stove audit a concrete, low-risk first fix: persist `causal_hypothesis` (already computed, currently discarded) as a labeled claim, not a verified fact.
- Real, honest cost: adds a second thing to reason about (which file has which kind of row), and — per Phase 5 — does not, by itself, solve retrieval or relevance; building this without also addressing what the Minimal Relevance Gate mission already found (a bare LLM judge over unstructured text is fooled by plausible-but-wrong narratives) risks producing a bigger pile of unused-but-real data, the same "many organs, no digestion" pattern this whole investigation keeps finding elsewhere in the codebase.

**Recommendation: Model B, but scoped narrowly and built incrementally.** The semantic-corruption risk of extending Model A is real and avoidable by not doing that; the evidence-loss cost of doing nothing is real and demonstrated on this session's own live test, not hypothetical. The correct scope for a first version is the ATTEMPT FACTS table from Phase 3 only — leave `causal_hypothesis`/`diagnosis_confidence` as a second, explicitly-lower-trust addition, or defer them, since Phase 5 already shows persisting a claim durably doesn't make it true, and premature diagnosis-storage risks becoming exactly the kind of confidently-wrong "lesson" the earlier gate missions this session showed a downstream consumer can't reliably discount.

## Final Verdict: **A2 — Justified but requires design changes**

Attempt-level provenance is not redundant (A3 is false — this session's own real, unforced test attempt demonstrates concrete, currently-permanent evidence loss: the F2 first-pass error text and the causal hypothesis both vanish, provably, and would have been unrecoverable at all if this investigation hadn't happened to capture them live). It is not unjustified by lack of learning value (A4 is false — Phase 5 identifies concrete, currently-blocked downstream uses: retry-diagnosis credit assignment, failure-recurrence detection, and a real join target for the trace→F2 verification work this session already built and tested twice).

It is not cleanly A1 either: the honest schema design in Phase 3 requires deliberately splitting ATTEMPT FACTS from OUTCOME/DIAGNOSIS CLAIMS — a real design decision, not a mechanical addition — and `self_edit_outcomes.jsonl`'s existing semantics (Phase 2) must be explicitly preserved rather than casually extended, which the mission itself flagged as a real risk. Both of those are exactly the kind of "additional separation/constraints" A2's own definition names.
