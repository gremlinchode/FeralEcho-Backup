"""
Gemini adapter -- STUB, correctly non-functional. Discovery (this
mission's Phase 3) found no Gemini CLI, no gcloud, no Google-AI Python
SDK, no cached OAuth state, and no GEMINI_API_KEY/GOOGLE_API_KEY-shaped
environment variable anywhere on this machine. Real live invocation would
require, at minimum, one of: creating a new Gemini API key, or logging
into a new/existing Google account via OAuth for gemini-cli -- both
explicitly listed as NOT AUTHORIZED WITHOUT STOPPING FOR GREMLIN in this
mission's own Authorization Boundary. This adapter therefore always
returns a clean, honest failure rather than attempting any network call,
and exists to prove the adapter INTERFACE accepts a "cannot proceed"
outcome correctly (mirroring the already-tested "no_response"/timeout
paths in the Codex reference's own Phase 7 suite).
"""
from __future__ import annotations

from app.experiments.breakfast_club_reachability.core.adapter_interface import (
    AdapterResult, EndpointAdapter,
)


class GeminiAdapter(EndpointAdapter):
    name = "gemini"
    qualification_status = "NOT_INSTALLED"  # see README.md's Phase 3 discovery table

    def dispatch(self, prompt: str) -> AdapterResult:
        return AdapterResult(
            success=False, stdout="", stderr="", elapsed_s=0.0,
            error="blocked_at_discovery: no Gemini CLI/SDK installed, no credential present; "
                  "would require creating a new API key or new Google OAuth login, both "
                  "explicit STOP conditions in this mission's Authorization Boundary",
        )
