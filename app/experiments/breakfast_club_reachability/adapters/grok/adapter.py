"""
Grok/xAI adapter -- STUB, correctly non-functional. Discovery (this
mission's Phase 4) found no Grok/xAI CLI, no xai_sdk/openai-compatible
xAI configuration, and no XAI_API_KEY/GROK_API_KEY-shaped environment
variable anywhere on this machine. Real live invocation would require
creating a new account at console.x.ai, loading paid credits, and
creating a new API key -- three separate, explicit STOP conditions in
this mission's own Authorization Boundary (new account connection, new
billing, new credential). This adapter always returns a clean, honest
failure rather than attempting any network call.
"""
from __future__ import annotations

from app.experiments.breakfast_club_reachability.core.adapter_interface import (
    AdapterResult, EndpointAdapter,
)


class GrokAdapter(EndpointAdapter):
    name = "grok"
    qualification_status = "NOT_INSTALLED"  # see README.md's Phase 4 discovery table

    def dispatch(self, prompt: str) -> AdapterResult:
        return AdapterResult(
            success=False, stdout="", stderr="", elapsed_s=0.0,
            error="blocked_at_discovery: no Grok/xAI CLI/SDK installed, no credential present; "
                  "would require a new console.x.ai account, loaded billing credits, and a new "
                  "API key -- three explicit STOP conditions in this mission's Authorization Boundary",
        )
