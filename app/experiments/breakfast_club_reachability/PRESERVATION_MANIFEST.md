# Preservation Manifest — Breakfast Club Reachability Harness

Per mission Phase 13's own explicit allowance: **the known-good Codex reference files were not moved or rewritten.** This manifest points to them in place, rather than risk altering the qualified reference by relocating it into the new `adapters/codex/` structure.

| Component | File (unmoved, unmodified) | Role |
|---|---|---|
| Bridge core — protocol/envelope/ledger | `protocol.py` | Endpoint-neutral (Phase 2) |
| Bridge core — deterministic verifier | `verifier.py` | Endpoint-neutral |
| Codex reference implementation (frozen, qualified, live-proven) | `run_codex_proof.py` | Endpoint-specific (Codex) — **the original, reproducible reference. Untouched.** |
| Codex reference — real live evidence | `../../memory/experiments/breakfast_club_reachability/obligation_ledger.jsonl`, `raw_exchange_log.jsonl` | Durable proof artifacts from the live Phase 8 run |
| Local mock testing (13-case suite) | `test_local.py`, `mock_recipient.py` | Endpoint-neutral test infrastructure |
| Negative controls (against real Codex data) | `negative_controls.py` | Endpoint-neutral, reused as-is |
| Shared adapter interface (new, this mission) | `core/adapter_interface.py` | Endpoint-neutral |
| Codex adapter wrapper (new, this mission — wraps, does not replace, `run_codex_proof.py`'s dispatch logic) | `adapters/codex/adapter.py` | `qualification_status = READY_WITH_EXISTING_AUTH` |
| Gemini adapter (new, this mission — honest stub) | `adapters/gemini/adapter.py` | `qualification_status = NOT_INSTALLED` |
| Grok adapter (new, this mission — honest stub) | `adapters/grok/adapter.py` | `qualification_status = NOT_INSTALLED` |
| Cross-adapter substitution test (new, this mission) | `test_adapter_substitution.py` | Proves the SAME core behaves correctly across Codex-replay, a generic mock, and both honest-failure stubs |

**Disable mechanism**: none of these files are imported by `app/` proper or `run.py` — deleting the entire `app/experiments/breakfast_club_reachability/` directory removes this experiment completely, with zero effect on production FeralEcho, matching every other experiment directory's own established convention this session.

**No secrets anywhere in this manifest or the files it lists** — `codex`'s own OAuth session is never read, stored, or referenced by name/value in any file here.
