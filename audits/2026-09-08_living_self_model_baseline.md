# Living Self-Model — Baseline (Phase 0)

**Preserved before any implementation.** Git HEAD at start: `5bc94bb05b1011bca9fc1b9235803fc05a105eb6` (unchanged throughout this mission — no commits made). Server: PID 21608, `serving`, live at mission start.

## Pre-existing state (confirmed by direct read)

- `memory/self_model.json`: real, 318 lines, `schema_version: 1`, rebuilt every ~130s by `SelfModelUpdater.update()` from `introspection_state.json` + raw logs. `river_brain.total_observations: 173310` at baseline — real, nonzero, growing.
- `app/core/self_knowledge_verification.py`: 4 real checks (council-gate-claim, check-count, self-edit-target, unsupported-CamelCase-subsystem). Called from exactly one site: `app/routes_echo_studio.py:250`, gated on `_is_introspective(original_msg)`. Purely stateless — computes a caveat, returns it, persists nothing.
- No `memory/self_model_claims.jsonl` existed at baseline (confirmed: file absent).
- Known R-T14 baseline (from the completed Self-Transparency Audit, `audits/2026-09-08_phase10_retest_after_revision.md`): a real conversational correction about RiverBrain's existence did NOT survive into a fresh conversation. Persistence: 0/1.
- Known RiverBrain baseline: Echo affirmed RiverBrain's existence in 4 of 5 real conversations in the original audit, denied it in the 5th, despite `river_brain.pkl` holding 160,000+ real observations throughout every one of them.

This baseline is immutable — not edited after this point.
