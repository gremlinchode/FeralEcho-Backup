# Epistemic Arbitration — Validation (what was actually tested this pass)

No implementation was built this pass (see design doc), so there is no new-code regression suite to report. What follows is the real, direct testing actually performed.

| Test | Method | Result |
|---|---|---|
| Fresh baseline reproduction | Real `/chat/stream` call, new conversation, self-referential question | Raw answer wrong (denies RiverBrain); explicitly self-contradicts mid-answer, quoting the correct fact and flagging the discrepancy, then still concludes wrong; post-hoc verifier correctly caught it, caveat appended, matches `525454a`'s prior 6/6 pattern exactly (7th consistent data point) |
| Isolated model-arbitration capability, order 1 | Raw Ollama `/api/generate` call, `echo:latest`, no persona/system prompt, abstracted claim-comparison framing | Correct: identified the verified claim as better-supported, cited its provenance |
| Isolated model-arbitration capability, order 2 (reversed) | Same, claim order swapped | Correct again, order-independent |
| Ledger consistency check | Read `memory/self_model_claims.jsonl` directly | Every real logged entry for RiverBrain shows `verified: false` (the denial was wrong) -- confirms the failure is fully consistent and reproducible, not intermittent |

## What was NOT tested this pass, disclosed explicitly

The six-shape generalization battery (verified-true, verified-false, unknown, historical, contradicted, user-assertion), the three-mechanism head-to-head comparison as live batteries, contradiction-taxonomy tests, reverse-direction re-verification, self-edit-aware arbitration, self-reference/disagreement handling, degradation-under-verifier-failure, and learning-over-time were not run this pass due to real context-budget constraints, disclosed in `epistemic_arbitration_experiments.md`. This is a real, acknowledged limitation on how far this mission's conclusions can be generalized -- the Phase 4 finding (model-can-arbitrate-in-isolation) is strong and reproducible on its own terms (2/2, order-independent), but has not been tested across the fuller shape battery the mission specified.
