"""
Codex adapter -- wraps the EXACT same subprocess call already proven live
in ../../run_codex_proof.py (which remains completely untouched, frozen,
and independently reproducible as the qualified reference implementation;
this file does not replace it, it exposes the identical dispatch logic
behind the shared EndpointAdapter interface for substitution testing).
"""
from __future__ import annotations

import subprocess
import time

from app.experiments.breakfast_club_reachability.core.adapter_interface import (
    AdapterResult, EndpointAdapter,
)

CODEX_TIMEOUT_S = 120


class CodexAdapter(EndpointAdapter):
    name = "codex"
    # Already authenticated on this machine (codex login status ->
    # "Logged in using ChatGPT"), no new credential -- verified live,
    # this session, in the reference proof. Real qualification status,
    # not asserted from documentation.
    qualification_status = "READY_WITH_EXISTING_AUTH"

    def dispatch(self, prompt: str) -> AdapterResult:
        t0 = time.time()
        try:
            result = subprocess.run(
                ["codex", "exec", prompt],
                capture_output=True, text=True, timeout=CODEX_TIMEOUT_S,
            )
            elapsed = time.time() - t0
        except subprocess.TimeoutExpired:
            return AdapterResult(success=False, stdout="", stderr="",
                                  elapsed_s=time.time() - t0, error="timeout")
        except FileNotFoundError:
            return AdapterResult(success=False, stdout="", stderr="",
                                  elapsed_s=0.0, error="codex_binary_not_found")

        return AdapterResult(
            success=(result.returncode == 0),
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            elapsed_s=elapsed,
            error=None if result.returncode == 0 else f"nonzero_exit_{result.returncode}",
        )


class CodexReplayAdapter(EndpointAdapter):
    """Replays the REAL, already-captured Phase 8 exchange
    (memory/experiments/breakfast_club_reachability/raw_exchange_log.jsonl)
    instead of spending new Codex quota -- used only for the substitution
    test (Phase 7 of this mission), which asks whether the SAME bridge
    core behaves correctly across different adapters, not whether Codex
    can be re-proven live a second time (already proven, prior mission)."""
    name = "codex-replay"
    qualification_status = "READY_WITH_EXISTING_AUTH (replayed from real prior data)"

    def __init__(self, raw_log_path):
        import json
        with open(raw_log_path) as f:
            self._entries = [json.loads(l) for l in f if l.strip()]

    def dispatch(self, prompt: str) -> AdapterResult:
        # Replays the most recent real entry's own stdout, regardless of
        # the exact prompt text passed in this test run -- this adapter
        # exists purely to exercise the core's plumbing with real,
        # previously-verified data, not to answer a new nonce live.
        real = self._entries[-1]
        return AdapterResult(success=True, stdout=real["stdout"], stderr=real.get("stderr") or "",
                              elapsed_s=real.get("elapsed_s", 0.0))
