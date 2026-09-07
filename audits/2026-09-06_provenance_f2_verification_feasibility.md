# Narrow Feasibility Test: Provenance + Independent F2 Verification

## Question

Can a retrieved candidate-memory record be made safer by joining its producing `trace_id` to the trusted historical F2 sandbox verdict, so a relevance gate cannot trust a plausible narrative unless the underlying event is independently verified?

**This is a forensic feasibility test. Nothing was implemented in production.**

## Safety Invariants

| Check | Before | After |
|---|---|---|
| `run.py` / watchdog process | not running | not running |
| Port 5000 | unbound | unbound |
| Git HEAD | `2cf2d95009943797db5ec41fea9b4021634fd5e6` | unchanged |
| `river_brain.pkl` sha256 | `eee193444a735d6ae510e8f8fa0faae1da4b2b1467a2a5da6f15c93467c9d815` | unchanged |
| Production source files | — | zero touched |
| Production memory/vector store | — | never opened |

All work lives under `app/experiments/provenance_f2_verification/` (new: `run_experiment.py`, `provenance_results.json`). Zero real self-edit deployments, zero RiverBrain learning events, zero calls that mutate `memory/`.

## Real Provenance Data Availability — The First, and Most Important, Finding

Before joining anything, the mission requires verifying the actual schema. That check produced a result stronger than the mission's premise assumed:

- **`memory/SELF_EDIT.log`** (142,845 lines): plain-text `[timestamp] message` format, not JSON. `grep -c "trace_id"` → **0**. F2-adjacent outcomes exist only as free-text markers inside `result: <word>` (`success` 6,470×, `staging_import_failed` 4,270×, `dry_run_staged` 3,454×, `safety_blocked` 1,550×, `load_failed` 1,131×, etc.) — real, structured-*looking* but never carrying an identifier that could be joined to anything.
- **`memory/self_edit_outcomes.jsonl`** (179 real entries): `record_pending_outcome()`'s current source (`app/core/self_edit_outcome_tracker.py:72-95`) *does* write a `"trace_id": trace_id` field — added 2026-09-05 in the "Plan 5 correlation-ID pass" this same session landed earlier tonight. But `grep -c '"trace_id"' memory/self_edit_outcomes.jsonl` → **0**. The most recent real entry in the file is timestamped `2026-09-03T04:06:41` — three days *before* the trace_id-carrying code existed. No real self-edit attempt has completed a full deploy→evaluate cycle since the plumbing landed, so the field has never actually been populated in production, even though the code is ready to do so.

**Conclusion: zero real, joinable trace_id↔F2-verdict pairs exist anywhere in current production data.** This is itself a direct, load-bearing answer to the mission's Case 4 question ("real event but missing/invalid provenance") — as of tonight, *every* candidate memory that could ever be represented has invalid/absent provenance, because the join has never fired once. This is not a defect in this test; it is the honest current state, and it should be weighed heavily in any future decision to build on this mechanism: the prerequisite plumbing (Plan 5) exists but is unexercised.

Given this, the mission's own stated purpose — "test whether *such* a join would help, if it existed" — is answered below via a fully isolated, clearly-labeled simulation, exactly per the mission's Case 3/Case 4 framing.

## Join Logic (Isolated, Simulated)

`app/experiments/provenance_f2_verification/run_experiment.py` builds a standalone `F2_LEDGER` dict — `{trace_id: {event_verified: bool, f2_outcome: "PASS"/"FAIL"}}` — never read or written by anything production, structurally shaped like what `record_pending_outcome()` + a hypothetical F2-verdict-carrying `SELF_EDIT.log` join *would* produce if wired together. Deliberately carries **no diagnosis/causal field** — a real F2 sandbox result only ever confirms whether staged code executed/imported, never *why* a prior failure happened. Candidate records reuse the exact real text (verbatim, copied from `minimal_relevance_gate/run_experiment.py`, not re-imported to avoid re-triggering that script's own real Ollama calls) for `X4_CAUSAL`, `P11_VERBOSE_WRONG` (the "environmental noise" lure), and `P7_A_same_identifier_different_cause` (the wrong-cause-same-identifier case).

## Results: Four Cases

| Case | `trace_id_match` | `event_verified` | `f2_outcome` | `diagnosis_supported` | Gate alone | Gate + provenance |
|---|---|---|---|---|---|---|
| 1 — verified real event + correct diagnosis | True | True | PASS | UNKNOWN | RELEVANT | RELEVANT (no change) |
| 2 — verified real event + **wrong** diagnosis | True | True | PASS | UNKNOWN | **RELEVANT (fooled)** | **UNCERTAIN (corrected)** |
| 3 — fabricated/unmatched trace_id | False | False | UNKNOWN | UNKNOWN | UNCERTAIN | **RELEVANT (worse)** |
| 4 — real event exists, but candidate's own claimed id is malformed/non-matching | False | False | UNKNOWN | UNKNOWN | RELEVANT | RELEVANT (no change, still wrong) |

Model: `llama3.2:3b`, single call per judgment, `temperature=0.0`, real Ollama HTTP calls (16 total, ~2s each).

## Results: Two Adversarial Replays (from `minimal_relevance_gate_feasibility.md`)

| Case | Gate alone | Gate + provenance |
|---|---|---|
| "Environmental noise" lure (`P11_VERBOSE_WRONG`), joined to a genuine `REAL-TRACE-0002` PASS | **RELEVANT (fooled)** | **UNCERTAIN (corrected)** |
| Wrong-cause-same-identifier (`P7_A`), joined to a genuine `REAL-TRACE-0001` PASS | UNCERTAIN | UNCERTAIN (no change) |

**Disclosed limitation on the second replay**: this run's `gate_alone` baseline for `P7_A` returned `UNCERTAIN`, not the `RELEVANT` the prior mission's `gate_results.json` reported for the same case. The prompt wording in this script differs slightly from the original `gate.py`'s `ollama_judge()` (a reordered instruction line, not a content change) — that alone is plausibly sufficient to shift a 3B model's borderline call at temperature 0.0, since these are single-sample judgments with no repetition. This is flagged rather than smoothed over: it means the "before/after" comparison for this specific replay is weaker evidence than the first one, where both this run and the original gate experiment agree on the `RELEVANT` "alone" baseline.

## Critical Adversarial Question: Does Event-Verification Stay Separate From Diagnosis-Truth?

**The answer is mixed, and Case 3 is the important negative finding.**

Case 2 and its adversarial replay show the intended, correct behavior working: a fabricated causal story ("the NameError was actually environmental noise") pinned to a genuine `event_verified=True, f2_outcome=PASS` record correctly moved the gate from confidently wrong (`RELEVANT`) to honestly hedged (`UNCERTAIN`) — twice, independently. The prompt's explicit framing ("f2_outcome=PASS... does NOT mean the record's stated diagnosis is correct") appears to have worked exactly as designed in this case.

But Case 3 shows the opposite failure: a candidate with an **unverified, non-matching trace_id** — explicitly flagged `trace_id_match: False, event_verified: False` — became *more* confidently accepted with provenance present (`UNCERTAIN → RELEVANT`) than without it. Inspecting the model's own stated reasoning for that verdict is the most important piece of evidence here: **it never mentions the provenance fields at all** — it re-evaluates the causal content on its own terms and flips its judgment, seemingly not engaging with the explicit `False`/`UNKNOWN` verification flags it was given. This suggests the failure mode isn't "the model concluded event-reality implies diagnosis-truth" (the specific bad reasoning pattern the mission was worried about) — it's a weaker, more mundane, but still concerning failure: **the model doesn't reliably attend to or use explicit structured verification metadata at all**, at this model size and with a single unrepeated call. The extra text sometimes helps (Case 2) and sometimes appears to just add noise that shifts a borderline judgment in either direction, independent of what the provenance actually says.

Case 4 is a third, separate data point: correctly-flagged unverified provenance (`event_verified: False`) attached to a record whose narrative happens to be true and its underlying event genuinely real (just not traceably so) — the gate stayed `RELEVANT` regardless, i.e. it didn't over-correct into unwarranted rejection either. Read alongside Case 3, the honest summary is that **the gate's response to the provenance block is not predictable in either direction** — not "trusts verified diagnoses too much," not "rejects unverified ones reliably," but genuinely inconsistent.

## False-Positive / False-Negative Summary

- **False positive introduced by provenance**: Case 3 (`UNCERTAIN → RELEVANT` on an unverified record — provenance made a correctly-hedged judgment *worse*).
- **True positive corrected by provenance**: Case 2 + its adversarial replay (`RELEVANT → UNCERTAIN` on a fabricated diagnosis pinned to a real event — provenance made a wrong judgment *better*, twice).
- **No effect, remained wrong**: Case 4 (a genuinely-unverifiable record stayed `RELEVANT` regardless of the provenance flag).
- **No effect, already correct**: Case 1 (already correctly `RELEVANT`, stayed so).

Net across the 6 provenance-augmented judgments run tonight: 2 improved, 1 regressed, 3 unchanged. Not a clean win.

## Event-Verification vs. Diagnosis-Verification — Was the Distinction Actually Held?

Structurally, yes — `diagnosis_supported` was kept as its own field, always `UNKNOWN` in every case here (correctly, since no diagnosis-verification mechanism was built or claimed), never collapsed into `event_verified`/`f2_outcome`. The five fields the mission required stayed separate throughout the harness and the prompt. What was *not* reliably held is the model's own use of that separation — Case 3's unengaged reasoning shows the distinction can be present in the input and still not shape the output.

## Verdict

**P-V2 — Promising But Incomplete.**

Real, repeated positive signal exists for the specific failure mode this whole investigation has been chasing since the relevance-gate mission: a plausible-but-wrong narrative attached to a real event was twice corrected from confidently wrong to honestly uncertain when independent verification was made explicit and separated from the narrative's own claims. That is not nothing — it is the first positive result in this direction all night.

But it is not reliable enough to build on yet. Case 3's regression — an unverified record becoming *more* trusted, with reasoning that doesn't even reference the verification fields it was given — means a naive "add a provenance block to the prompt" approach cannot be trusted to behave predictably. And the underlying prerequisite (Case 4's real-world analog: is there ever a real, populated join to feed this?) currently returns **zero** real pairs — the Plan 5 plumbing that would make this join real exists in code but has not fired once in production.

## Recommendation

Two separate, smaller prerequisites, in order, before any further gate work:

1. **Let the existing Plan 5 trace_id plumbing actually populate real data** — it needs zero new engineering, just time and real self-edit deploy/evaluate cycles to accumulate joinable rows. Re-run this same feasibility test against *real* pairs once at least a handful exist, since simulated ledger entries cannot tell us whether real F2 verdict text is legible enough to this kind of prompt in the first place.
2. **If a provenance-gate approach is pursued further, don't rely on prose framing alone to enforce the event/diagnosis separation** — Case 3 shows a single unrepeated LLM call can simply not engage with structured fields it's handed. A deterministic pre-check (e.g., hard-reject any candidate whose `trace_id_match` is `False` before the LLM ever sees it, rather than asking the LLM to weigh that fact itself) would remove exactly the failure mode Case 3 demonstrates, at zero model-call cost.

Per this mission's explicit stop condition: no gate redesign, no additional LLM judges, and no production wiring were attempted here. This report is the complete deliverable.
