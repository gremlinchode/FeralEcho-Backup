#!/usr/bin/env python3
"""
Mission Phase 7 (multi-endpoint) -- proves the bridge CORE (protocol.py +
verifier.py, both byte-identical to the qualified Codex reference, never
modified for this mission) behaves correctly when driven through
DIFFERENT adapters implementing the shared EndpointAdapter interface.
This is real, direct evidence for "is the core endpoint-neutral,"
distinguishable from a claim that Gemini/Grok were live-tested (they
were not -- see README.md's discovery findings; both are NOT_INSTALLED,
blocked before any live call could be attempted).

Adapters exercised here:
  - CodexReplayAdapter: replays the REAL, already-verified Phase 8
    exchange (no new Codex quota spent) -- proves the core correctly
    reaches VERIFIED against genuine prior live data through the new
    adapter abstraction.
  - a local mock "generic success" adapter -- proves the core is not
    accidentally coupled to anything Codex-specific in its own logic.
  - GeminiAdapter / GrokAdapter (real stub implementations) -- proves the
    core correctly, cleanly reaches FAILED (never a false VERIFIED, never
    a corrupted ledger) when an adapter honestly reports it cannot
    proceed at all.

usage: python -B test_adapter_substitution.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.experiments.breakfast_club_reachability import protocol as P
from app.experiments.breakfast_club_reachability import verifier as V
from app.experiments.breakfast_club_reachability.core.adapter_interface import (
    AdapterResult, EndpointAdapter,
)
from app.experiments.breakfast_club_reachability.adapters.codex.adapter import CodexReplayAdapter
from app.experiments.breakfast_club_reachability.adapters.gemini.adapter import GeminiAdapter
from app.experiments.breakfast_club_reachability.adapters.grok.adapter import GrokAdapter

RAW_LOG_PATH = Path(__file__).resolve().parents[3] / "memory" / "experiments" / "breakfast_club_reachability" / "raw_exchange_log.jsonl"
_TMP_LEDGER = Path(__file__).resolve().parent / "_test_scratch_substitution_ledger.jsonl"

_PASS, _FAIL = [], []


def _check(name, condition, detail=""):
    (_PASS if condition else _FAIL).append(name)
    print(f"  {'PASS' if condition else 'FAIL'}  {name}  {detail if not condition else ''}")


class MockGenericSuccessAdapter(EndpointAdapter):
    """A fully local, deterministic, non-Codex, non-Gemini, non-Grok
    stand-in third adapter -- proves the core has no hidden dependency on
    any one provider's response shape."""
    name = "mock-generic"
    qualification_status = "READY_WITH_EXISTING_AUTH (local mock, no network)"

    def __init__(self, nonce_hex: str):
        self._nonce_hex = nonce_hex

    def dispatch(self, prompt: str) -> AdapterResult:
        answer = P.expected_answer(self._nonce_hex)
        return AdapterResult(success=True, stdout=answer, stderr="", elapsed_s=0.001)


def drive_through_adapter(adapter: EndpointAdapter, envelope: dict, ledger: P.ObligationLedger):
    mid = envelope["message_id"]
    ledger.record(message_id=mid, owner="claude", evidence=f"adapter={adapter.name}",
                   previous_state=None, new_state="CREATED")
    ledger.record(message_id=mid, owner="claude", evidence="queued", previous_state="CREATED", new_state="QUEUED")
    ledger.record(message_id=mid, owner="claude", evidence="dispatched via adapter",
                   previous_state="QUEUED", new_state="SENT")

    prompt = P.build_challenge_prompt(envelope["nonce_hex"])
    result = adapter.dispatch(prompt)

    if not result.success:
        ledger.record(message_id=mid, owner=adapter.name, evidence=f"adapter reported failure: {result.error}",
                       previous_state="SENT", new_state="FAILED")
        return {"outcome": "ADAPTER_FAILED", "error": result.error}

    ledger.record(message_id=mid, owner=adapter.name, evidence="accepted",
                   previous_state="SENT", new_state="DELIVERED_OR_ACCEPTED")
    ledger.record(message_id=mid, owner=adapter.name, evidence="processed",
                   previous_state="DELIVERED_OR_ACCEPTED", new_state="REMOTE_PROCESSING")
    ledger.record(message_id=mid, owner=adapter.name, evidence="response produced",
                   previous_state="REMOTE_PROCESSING", new_state="RESPONSE_CREATED")
    ledger.record(message_id=mid, owner="claude", evidence="durable", previous_state="RESPONSE_CREATED", new_state="RESPONSE_DURABLE")
    ledger.record(message_id=mid, owner="claude", evidence="fetched", previous_state="RESPONSE_DURABLE", new_state="RETURNED")

    import re
    candidates = re.findall(r"\b[0-9a-fA-F]{16}\b", result.stdout)
    claimed = candidates[-1] if candidates else None

    ledger.record(message_id=mid, owner="claude", evidence="explicit consumption", previous_state="RETURNED", new_state="CLAUDE_CONSUMED")
    verify_result = V.verify(envelope=envelope, response_message_id=mid, claimed_answer=claimed)
    if verify_result["outcome"] == "VERIFIED":
        ledger.record(message_id=mid, owner="verifier", evidence=str(verify_result), previous_state="CLAUDE_CONSUMED", new_state="VERIFIED")
        ledger.record(message_id=mid, owner="claude", evidence="closed", previous_state="VERIFIED", new_state="CLOSED")
    else:
        ledger.record(message_id=mid, owner="verifier", evidence=str(verify_result), previous_state="CLAUDE_CONSUMED", new_state="FAILED")
    return verify_result


def main():
    if _TMP_LEDGER.exists():
        _TMP_LEDGER.unlink()
    ledger = P.ObligationLedger(_TMP_LEDGER)

    print("Multi-endpoint substitution test -- SAME core (protocol.py + verifier.py), DIFFERENT adapters\n")

    # 1. Codex, replayed from the REAL, already-verified live proof --
    #    uses the exact real envelope/nonce from that run, so the replayed
    #    real stdout is expected to verify correctly.
    import json
    with open(RAW_LOG_PATH) as f:
        real_entries = [json.loads(l) for l in f if l.strip()]
    real_envelope = real_entries[-1]["envelope"]
    codex_result = drive_through_adapter(CodexReplayAdapter(RAW_LOG_PATH), real_envelope, ledger)
    # NOTE, found live while running this exact test (not glossed over):
    # the real envelope's own 10-minute expiry (frozen at the moment of
    # the original Phase 8 run) has genuinely elapsed by the time this
    # later substitution test runs. This is the CORRECT, intended
    # behavior of the same staleness check already proven in Phase 7 case
    # 12 -- replaying old data past its own frozen expiry should fail,
    # not silently re-verify. The honest assertion is therefore
    # REJECTED_STALE, not VERIFIED; expecting VERIFIED here would have
    # meant the verifier was NOT enforcing freshness consistently.
    _check("codex_replay_adapter_correctly_rejects_now-stale_real_envelope",
           codex_result["outcome"] == "REJECTED_STALE", codex_result)

    # Same real nonce and real Codex-produced answer, but a FRESHLY-minted
    # envelope (new message_id, new expiry) -- demonstrates the adapter/
    # core combination genuinely reaches VERIFIED for real Codex-shaped
    # data when the envelope isn't stale, isolating "is this data
    # correct" from "has this particular envelope expired."
    fresh_env_same_nonce = P.build_envelope(
        message_id=str(uuid.uuid4()), sender="claude-m5", intended_recipient="codex-replay",
        mission_id="substitution-test", reason_for_contact="re-verify real codex data under a fresh envelope",
        nonce_hex=real_envelope["nonce_hex"],
    )
    codex_fresh_result = drive_through_adapter(CodexReplayAdapter(RAW_LOG_PATH), fresh_env_same_nonce, ledger)
    _check("codex_replay_adapter_verifies_real_data_under_fresh_envelope",
           codex_fresh_result["outcome"] == "VERIFIED", codex_fresh_result)

    # 2. A fully local, generic mock adapter -- fresh nonce, proves the
    #    core has no Codex-specific coupling.
    nonce2 = P.generate_nonce()
    env2 = P.build_envelope(message_id=str(uuid.uuid4()), sender="claude-m5",
                             intended_recipient="mock-generic", mission_id="substitution-test",
                             reason_for_contact="prove endpoint-neutrality", nonce_hex=nonce2)
    mock_result = drive_through_adapter(MockGenericSuccessAdapter(nonce2), env2, ledger)
    _check("mock_generic_adapter_verifies", mock_result["outcome"] == "VERIFIED", mock_result)

    # 3. Gemini stub -- must fail cleanly, never falsely VERIFIED, never a
    #    corrupted ledger state.
    nonce3 = P.generate_nonce()
    env3 = P.build_envelope(message_id=str(uuid.uuid4()), sender="claude-m5",
                             intended_recipient="gemini", mission_id="substitution-test",
                             reason_for_contact="test gemini adapter honest failure", nonce_hex=nonce3)
    gemini_result = drive_through_adapter(GeminiAdapter(), env3, ledger)
    _check("gemini_adapter_fails_cleanly_no_false_verify",
           gemini_result["outcome"] == "ADAPTER_FAILED", gemini_result)
    _check("gemini_obligation_reaches_FAILED_not_VERIFIED",
           ledger.current_state(env3["message_id"]) == "FAILED",
           ledger.current_state(env3["message_id"]))

    # 4. Grok stub -- same check.
    nonce4 = P.generate_nonce()
    env4 = P.build_envelope(message_id=str(uuid.uuid4()), sender="claude-m5",
                             intended_recipient="grok", mission_id="substitution-test",
                             reason_for_contact="test grok adapter honest failure", nonce_hex=nonce4)
    grok_result = drive_through_adapter(GrokAdapter(), env4, ledger)
    _check("grok_adapter_fails_cleanly_no_false_verify",
           grok_result["outcome"] == "ADAPTER_FAILED", grok_result)
    _check("grok_obligation_reaches_FAILED_not_VERIFIED",
           ledger.current_state(env4["message_id"]) == "FAILED",
           ledger.current_state(env4["message_id"]))

    print(f"\n{len(_PASS)}/{len(_PASS)+len(_FAIL)} substitution checks passed.")
    _TMP_LEDGER.unlink(missing_ok=True)
    return 0 if not _FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
