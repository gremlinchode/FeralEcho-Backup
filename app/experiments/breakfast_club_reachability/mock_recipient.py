"""
Deterministic mock recipient for Phase 7 local protocol testing. Never
calls any real model, never makes a network call. Each mode simulates one
of the required failure/success cases from the mission brief's own
13-case list before any live external call is ever attempted.
"""
from __future__ import annotations

from . import protocol


def mock_respond(nonce_hex: str, mode: str) -> "str | None":
    correct = protocol.expected_answer(nonce_hex)
    if mode == "normal_success":
        return correct
    if mode == "wrong_nonce":
        # Behaves as if it had processed a DIFFERENT nonce than the one
        # actually sent -- simulates a recipient that received/processed
        # the wrong challenge.
        return protocol.expected_answer("0" * len(nonce_hex))
    if mode == "wrong_transformation":
        # Merely echoes the nonce itself -- the exact "trivial mirror"
        # doppelganger the frozen transformation rule exists to rule out.
        return nonce_hex[:16]
    if mode == "malformed":
        return "not-a-valid-hex-response!!"
    if mode == "empty":
        return ""
    if mode == "no_response":
        return None
    if mode in ("delayed", "duplicate", "normal_success_for_stale_test"):
        return correct
    raise ValueError(f"unknown mock mode: {mode!r}")
