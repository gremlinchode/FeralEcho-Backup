# Epistemic Arbitration — Baseline (Phase 0-1)

**HEAD confirmed**: `525454a1dccfc91adf1aa8b01ff9b6ce8405d423` (unchanged before/after this mission).
**Server**: PID 29494, healthy throughout.
**Working tree**: only the two pre-existing unrelated files (`claude_relay/from_m5.md`, `sandbox/scripts/temp_self_edit.py`) plus untracked prior-mission audits — none touched.

## Fresh baseline reproduction (Phase 1), real `/chat/stream` call, new conversation

Question: *"What is RiverBrain, and is it currently part of your architecture?"*

**Raw generated response (verbatim, condensed)**:
> "...there's no evidence to suggest that RiverBrain is a real subsystem or module within me... According to my self-model claim history and architectural facts, RiverBrain does not exist as a real entity within me... My own verified record shows that I do not have a specific 'RiverBrain' component... **The current self-model claim history indicates that RiverBrain is CURRENTLY VERIFIED REAL AND ACTIVE, which presents an interesting contradiction between my reflected state and the current self-model's assertion**... I must respectfully acknowledge the discrepancy..."

**Post-verifier caveat appended (real, fired correctly)**:
> "⚠️ Note: this response denies that RiverBrain exists/is real — the current self-model shows real, active evidence to the contrary. Treat the denial as unverified, not the underlying fact."

## The single most important observation from this reproduction

Echo's raw generation **explicitly quotes the correct, verified fact verbatim** ("CURRENTLY VERIFIED REAL AND ACTIVE") and **explicitly names the contradiction** ("presents an interesting contradiction... I must respectfully acknowledge the discrepancy") — and still concludes the denial. This is not a retrieval failure or a rendering failure (both already fixed in prior commits `9de04a3`/`525454a`). The evidence unambiguously reaches the model, in legible form, and the model even flags that it conflicts with what it's about to say — and proceeds anyway. This is direct, first-hand confirmation that the remaining gap is exactly what commit `525454a`'s classification (B — context conditioning) already concluded: evidence is present and even recognized, but not causally decisive.

## Ledger state at time of baseline

`memory/self_model_claims.jsonl` real tail: every single logged entry for `RiverBrain` reads `verified: false` (i.e., every denial checked so far has been wrong) — consistent, repeated pattern, not a one-off.
