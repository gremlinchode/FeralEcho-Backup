# Operation Breakfast Club — Reachability Proof-of-Capability Harness

Isolated, standalone experiment code (imports nothing from `app/` proper or `run.py`),
matching this project's own established convention for experiment directories that must
never touch production state (`minimal_procedure_transfer/`, `historical_difficulty_calibration/`,
etc.). Full design rationale, authorization reasoning, and results:
`audits/2026-09-24_operation_breakfast_club_reachability_proof_of_capability.md`.

**Deviation from the mission brief's own "suggested location" (`experiments/breakfast_club_reachability/`),
disclosed rather than silently done**: placed under `app/experiments/` instead, matching this
project's own already-established convention for every other experiment this session, since the
brief's own wording says "suggested," not mandatory.

## Files

- `protocol.py` — envelope schema, the frozen challenge-response transformation rule (protocol
  version `bfc-reach-v1`), and the durable, append-only `ObligationLedger` state machine.
- `verifier.py` — deterministic, non-LLM verification. The only code path permitted to declare
  a match; never calls a model.
- `mock_recipient.py` — deterministic mock recipient for local testing, never calls any real
  model or network endpoint.
- `test_local.py` — Phase 7's 13 required failure/success cases, run against the mock before
  any live external call. `python -B test_local.py` (or run from the repo root as a module).
- `run_codex_proof.py` — the one live proof (Phase 8), against the already-authenticated
  `codex` CLI (`codex exec`, non-interactive). No new credential, no billing change. Writes
  real, durable evidence to `memory/experiments/breakfast_club_reachability/`.
- `negative_controls.py` — Phase 9's cost-free negative controls (N1 wrong-response, N2 replay,
  N3 pre-response-prediction), run against the real data `run_codex_proof.py` already produced —
  makes zero new external calls.

## What this harness does and does not prove

Proves: that this M5 machine's Claude Code session can, in one process, generate a genuinely
novel local challenge, dispatch it to a real, already-authenticated OpenAI-hosted reasoning
endpoint (Codex) without any human retyping it, receive a machine-readable response without
human transport, and independently, deterministically verify that response depended on the
specific novel content sent — all logged to a durable, cursor-independent obligation ledger.

Does NOT prove: that this reaches ChatGPT, GPT-5.6 Sol, or "the existing collaborator Gremlin
calls Don" — Codex is a structurally different product/endpoint, established repeatedly
elsewhere in this research thread and restated in the accompanying audit report's own
"Important Distinctions" analysis. Does not by itself demonstrate R5 (failure-recoverable,
restart-surviving bidirectional reachability across process boundaries) — this was a single,
synchronous, one-shot exchange within one process's lifetime, not a durable daemon design.
