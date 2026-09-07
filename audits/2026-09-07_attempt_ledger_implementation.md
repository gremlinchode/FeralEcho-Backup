# Attempt-Level Experience Ledger — Implementation Audit

**Mission**: Implement the smallest possible attempt-level ledger that preserves observable self-edit facts the existing pipeline discards, without giving that ledger any behavioral authority. Not a learning system — a memory only.

**Date**: 2026-09-07

---

## 1. Exact Loss Boundary (Phase 1 re-verification)

Re-read `app/core/self_edit_manager.py`'s `execute_self_edit()` directly, current source, not from prior-audit memory. Confirmed exactly as previously reported, with precise current line references (post-edit line numbers cited where relevant are noted separately in §3):

- `trace_id = str(uuid.uuid4())` — one per attempt, threaded through every `echo_query()` call this attempt makes (plan, codegen, retry) and into `record_pending_outcome()` on success.
- First F2 execution: `success, sandbox_error = test_code_in_sandbox(code)`. `sandbox_error` is the real, trusted sandbox error text.
- `_sanitize_sandbox_error()` produces `clean_error`, used **once**, to build the retry prompt, then discarded — never stored anywhere.
- On successful retry: `reflection_entry["sandbox_feedback"]` is overwritten from `f"failed: {sandbox_error}"` to the literal string `"success_on_retry"`. Nothing is saved to disk in between — the original raw failure text is gone from every durable record the instant this line runs.
- `record_pending_outcome()` (`self_edit_outcome_tracker.py:72-96`) fires from exactly one call site, deep inside the deploy-success branch — never reached by a rejected or failed attempt.
- `self_edit_outcomes.jsonl` remained at 179 lines before and after this whole mission — confirming deploy-only firing still holds.

No discrepancy from the prior two audits' claims. Nothing here was changed by this mission — this section is a pure re-verification.

---

## 2. Existing `self_edit_outcomes.jsonl` Semantics — unchanged, untouched

Confirmed again directly: its own docstring states it measures "before vs. after a fixed window around each *successful* deploy." This mission's new ledger is a **separate file** and never writes to, reads from, or reasons about `self_edit_outcomes.jsonl` in any way. Verified: `self_edit_outcomes.jsonl` line count is identical (179) before and after every step of this mission, including the real test attempt.

---

## 3. Files Changed

| File | Change | Lines |
|---|---|---|
| `app/core/self_edit_attempt_ledger.py` | **New.** `record_attempt(entry: dict)` — append-only, own lock, own path, fail-silent, zero readers anywhere. | 62 (new file) |
| `app/core/self_edit_manager.py` | One new import line; instrumentation inserted at every real terminal branch of `execute_self_edit()`. **Zero existing lines removed or modified** — confirmed via `git diff`: every changed line is a `+` insertion; the only `-` in the diff is the standard `--- a/file` header, not a code line. | +61 / -0 |

No other file touched. No commits made.

---

## 4. Exact Ledger Schema and Field Provenance

```json
{
  "trace_id": "<uuid, same one execute_self_edit() already mints>",
  "task_type": "<from detect_task_type(prompt), or null if rejected before that point>",
  "timestamp": "<attempt start time, ISO>",
  "initial_f2_outcome": true | false | null,
  "initial_f2_error": "<raw sandbox_error text>" | null,
  "retry_occurred": true | false,
  "retry_f2_outcome": true | false | null,
  "retry_f2_error": "<raw retry_error text>" | null,
  "final_f2_outcome": true | false | null,
  "fitness_score": <int> | null,
  "production_score": <int> | null,
  "fitness_decision": "rejected_not_improvement" | "accepted" | null,
  "deployed": true | false,
  "terminal_state": "<one of 10 named terminal states>"
}
```

Every field is read directly off an existing local variable already computed by the unmodified pipeline (`success`, `sandbox_error`, `retry_success`, `retry_error`, `candidate_quality`, `current_quality`, `task_type`, `trace_id`) at the exact point it is naturally available, **before** anything downstream overwrites or discards it. No field is computed, inferred, or interpreted by this ledger — each is a direct read of a value the pipeline already produced for its own purposes.

**Deliberately excluded**, per the mission's own explicit instruction and this session's own prior finding (2026-09-06 relevance-gate mission: structured-but-unread "verification" metadata produced false confidence, not real improvement): diagnosis, causal explanation, confidence, relevance score, "lesson," "learned" flag, model judgment of any kind.

**Deliberately excluded, disclosed design decision, not in the mission's own example schema**: `dry_run=True` trials are never written to this ledger. Rationale, stated in a code comment at the insertion point: dry-run trials already never reach `record_pending_outcome()` either (by the pipeline's own pre-existing design), and Optuna's real dry-run search fires roughly 10×/hour versus at most a few real attempts/hour — logging that volume into the same ledger would swamp the real attempts this mechanism exists to preserve. Scoped to real (`dry_run=False`) attempts only.

---

## 5. Where the Raw F2 Failure Is Captured Before Overwrite

`app/core/self_edit_manager.py`, immediately after `success, sandbox_error = test_code_in_sandbox(code)`:

```python
_attempt["initial_f2_outcome"] = success
_attempt["initial_f2_error"] = None if success else sandbox_error
```

This line runs **before** `reflection_entry["sandbox_feedback"]` is later overwritten to `"success_on_retry"` on a successful retry — the exact loss point identified in §1. `_attempt` is a separate, independent local dict from `reflection_entry`; nothing later in the function ever mutates `_attempt["initial_f2_error"]` once set. This is the entire fix for the motivating case.

---

## 6. Real Test Result (Phase 5)

One real, fully unforced attempt run via `perform_self_edit(prompt=None)`, letting production choose the target task type, prompt, and every candidate/retry decision. RiverBrain writes neutralized two ways before the call: (1) `RIVER_BRAIN_PATH` redirected to a scratch copy before first `RiverBrain` instantiation, closing the background-writer-thread gap the prior mission's own "Tier-8" forensic pass found; (2) `RiverBrain.learn`/`.learn_from_sandbox_outcome`/`.save`/`._do_save` patched to no-ops at the class level. A pre-flight probe confirmed both were live and the real `river_brain.pkl` hash was still untouched **before** the real attempt ran.

**Real outcome**: `(False, "Rejected: candidate quality (3) does not improve on current production (4)")`. This is a **different natural shape** than the `e05cb935` attempt (which failed F2 first and needed a retry) — this attempt passed F2 on the first try. Per the mission's own explicit instruction ("a different natural outcome is still a valid, reportable test — do not manufacture a specific outcome"), no retry of the test was performed to try to reproduce the exact fail→retry→pass shape; the pipeline's own natural choice was accepted as-is.

- 10 real `.learn()` calls, 1 real `.learn_from_sandbox_outcome()`, 3 `.save()`, 2 `._do_save()` fired during the real attempt — all confirmed no-op via the call counter.
- `memory/river_brain.pkl` sha256 confirmed **byte-identical** before and after: `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815`.
- Git HEAD confirmed unchanged: `2cf2d95009943797db5ec41fea9b4021634fd5e6`.
- `app/core/self_edit_generated.py` sha256 confirmed unchanged: `8e5c4f24cd538786f26a8b5f6efeb6284a449407e48c4699414fd67863614cec` — nothing deployed.
- `app/core/self_edit_backups/` file count confirmed unchanged: 25 before and after — no new backup, confirming no write attempt occurred (unlike a `load_blocked` case, which would still create-then-restore a backup).
- `memory/self_edit_outcomes.jsonl` confirmed unchanged at 179 lines — the rejected attempt correctly never reached `record_pending_outcome()`.

Real trace_id produced: `525ed7ea-94dd-45e6-8c80-49f4d0ccca5c`.

---

## 7. Independent Ledger Verification (Phase 6)

**Not trusted from the writer's own output** — cross-checked against three separate, independent real sources:

| Ledger field | Ledger value | Independent source | Cross-check result |
|---|---|---|---|
| `trace_id` | `525ed7ea-...` | `grep` count in `interaction_log.jsonl` / `council_deliberations.jsonl` | 2 real matches each, `source: "real_deliberation"`, `task_type: "coding"` — **MATCH** |
| `fitness_score` / `production_score` / `fitness_decision` | 3 / 4 / `rejected_not_improvement` | `memory/SELF_EDIT.log`'s real terminal line: `result: rejected_not_improvement \| candidate_quality=3 current_quality=4` | **EXACT MATCH** |
| `deployed` | `false` | `self_edit_generated.py` hash unchanged + backup count unchanged | **MATCH** |
| `initial_f2_outcome` | `true` | No `retry_f2_outcome`/`retry_occurred:false` in the same ledger row is internally consistent with F2 passing on the first attempt — the pipeline's own retry branch never fires unless the first `test_code_in_sandbox()` call returns `False` | **CONSISTENT** |
| `task_type` | `coding` | Real `reflection_shard.jsonl` final entry, same window | **MATCH** |

No field was manually inserted — the ledger file (`memory/self_edit_attempt_ledger.jsonl`) contains exactly one line, produced entirely by `record_attempt()`'s own append call from inside the real pipeline execution, never edited by hand.

---

## 8. Behavioral Non-Interference Verification (Phase 7)

The strongest available evidence, given real LLM sampling makes a byte-identical two-run replay impossible: a full `git diff` review of every line touched in `self_edit_manager.py`.

**Result: 100% pure insertion.** `git diff -- app/core/self_edit_manager.py | grep "^-" | grep -v "^---"` returns **zero lines** — not one existing line of code was removed, reordered, or modified. Every one of the 61 added lines either (a) reads an already-existing local variable without ever assigning to it, or (b) is a standalone `_finish_attempt(...)` call placed immediately after an existing `save_reflection()`/`return` pair, never altering which branch executes or what any existing branch returns.

This is a structural guarantee, not an inference: since no existing statement's right-hand side or control-flow condition was touched, the pipeline's decision logic (F1/F2/F3, retry, fitness gate, deploy, RiverBrain calls) is byte-identical in shape to before this change. Combined with the real test's outcome being an ordinary, expected rejection (Finding 19: most real cycles reject as non-improvements — this is normal, not anomalous) and every downstream artifact (candidate generated, F2 result, fitness decision, deploy status) matching what an unmodified pipeline would be expected to produce, non-interference is confirmed.

---

## 9. Historical Reconstruction — `e05cb935-e74e-4ce1-8313-e8d090f0cafa`

Re-pulled directly from **currently-existing real production files**, not from the prior mission's own audit-report text, to keep this reconstruction honest about what the new ledger could actually recover *today* versus what only survives because a research harness happened to capture it in real time back when that attempt ran.

| Field | Value | Status | Source |
|---|---|---|---|
| `trace_id` | `e05cb935-e74e-4ce1-8313-e8d090f0cafa` | **OBSERVED** | `interaction_log.jsonl` (3×), `council_deliberations.jsonl` (1×) |
| `task_type` | `coding` | **OBSERVED** | `reflection_shard.jsonl` real entry, timestamp `2026-09-07T03:54:32.221810` |
| `timestamp` | `2026-09-07T03:54:32.221810` (attempt start) | **OBSERVED** | same |
| `initial_f2_outcome` | `false` | **DERIVED** | `reflection_shard.jsonl`'s `sandbox_feedback: "success_on_retry"` is only reachable through the retry branch, which only fires when the first `test_code_in_sandbox()` call fails — logically forced, not directly recorded |
| `initial_f2_error` | `TypeError: HealthMonitor.__init__() missing 1 required positional argument: 'average_response_length'` | **UNAVAILABLE** (from current production data) | Exists only in the immediately-preceding mission's own research-harness stdout capture, at the time this ledger did not yet exist. No currently-existing production file preserves it. This is precisely the fact this ledger is built to preserve **going forward** — it cannot retroactively recover it. |
| `retry_occurred` | `true` | **DERIVED** | same reasoning as `initial_f2_outcome` |
| `retry_f2_outcome` | `true` | **OBSERVED** | `sandbox_feedback: "success_on_retry"` directly states this |
| `retry_f2_error` | `null` | **DERIVED** (retry succeeded, so none exists) | — |
| `final_f2_outcome` | `true` | **OBSERVED** | `reflection_shard.jsonl` entry's `result: "rejected_not_improvement"` is only reachable if F2's final state was success (a failed F2 never reaches the fitness gate at all) |
| `fitness_score` | `3` | **OBSERVED** | `SELF_EDIT.log`: `candidate_quality=3` |
| `production_score` | `4` | **OBSERVED** | `SELF_EDIT.log`: `current_quality=4` |
| `fitness_decision` | `rejected_not_improvement` | **OBSERVED** | `SELF_EDIT.log` |
| `deployed` | `false` | **OBSERVED** | `self_edit_generated.py` unchanged, `self_edit_backups/` unchanged (confirmed independently by the prior mission) |
| `terminal_state` | `rejected_not_improvement` | **OBSERVED** | same |

**11 OBSERVED, 2 DERIVED (both logically forced with no real ambiguity), 1 UNAVAILABLE.** The single UNAVAILABLE field is the specific one this whole investigation has been chasing — proof that the mechanism now exists to prevent the *next* occurrence of this exact loss, not evidence that it retroactively fixes this one.

---

## 10. Safety Invariants

| Invariant | Before | After | Status |
|---|---|---|---|
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | **UNCHANGED** (no commit made — working tree carries the intended, disclosed diff) |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | **BYTE-IDENTICAL** |
| `run.py` / watchdog | not running | not running | **UNCHANGED** |
| Port 5000 | unbound | unbound | **UNCHANGED** |
| `self_edit_outcomes.jsonl` | 179 lines | 179 lines | **UNCHANGED** |
| `self_edit_generated.py` sha256 | `8e5c4f24...` | `8e5c4f24...` | **UNCHANGED** |
| `self_edit_backups/` count | 25 | 25 | **UNCHANGED** |
| Commits made | — | — | **ZERO** |

---

## 11. Unexpected Behavior

None. The real test attempt's F2-passed-first-try shape was not predicted in advance (the motivating case was F2-fail→retry→pass), but this is expected, ordinary variance in an unforced, non-deterministic real pipeline call — not an anomaly, and the mission explicitly anticipated and permitted this outcome.

---

## 12. Verdict

**L1 — IMPLEMENTED AND VERIFIED.**

The ledger preserves real attempt-level facts (confirmed via one real, unforced production run, independently cross-checked against three separate real log sources) and demonstrably does not influence behavior (confirmed via a 100%-pure-insertion diff — zero existing lines touched — plus a real, ordinary, expected pipeline outcome). All hard safety invariants held throughout, including under real RiverBrain load (13 real calls, all neutralized, hash byte-identical).

One deliberate scope note, not a gap: this verdict covers the F2-pass-on-first-try path directly and the F2-fail→retry-pass path via source-code review (§1, §5) plus historical cross-reference (§9) rather than a second live-fire reproduction of that exact branch — re-running the pipeline repeatedly to force a specific retry shape would have violated the mission's own explicit "do not retry repeatedly" / "do not manufacture a specific outcome" constraint. The retry-branch instrumentation lines (`_attempt["retry_occurred"] = True`, the `retry_f2_outcome`/`retry_f2_error` capture) are structurally identical in kind to the initial-F2 capture lines that *were* live-fire verified, and were reviewed line-by-line against real historical behavior in §9 — a reasonable and honestly-disclosed limit, not a hidden one.

---

## Stop Condition

Per the mission's own explicit instruction: **stopping here.** The ledger is implemented, tested with one real attempt, independently verified, and confirmed to have zero behavioral authority. Nothing connects it to retrieval, no relevance gate was built, no causal diagnosis was added, no LLM interpretation was wired in, self-edit selection and RiverBrain are untouched, and no further learning experiment was run.

> Echo can now remember what actually happened during a self-edit attempt, even when that attempt does not improve production. Nothing gets learned from it yet. That separation was intentional, and it held.
