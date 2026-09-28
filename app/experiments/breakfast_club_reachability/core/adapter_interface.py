"""
Endpoint-neutral adapter interface (mission Phase 2/Phase 13). Defines the
one contract every endpoint adapter must satisfy; the bridge core
(protocol.py, verifier.py -- both UNCHANGED, UNMOVED from the qualified
Codex reference) never imports a specific adapter directly, only this
interface's shape.

Endpoint-specific concerns live entirely inside a concrete adapter
(executable/CLI, base URL, request syntax, response parsing,
authentication mechanism, model selector, provider metadata). Nothing
here knows what "Codex," "Gemini," or "Grok" mean.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdapterResult:
    """What every adapter returns, regardless of provider. Fields chosen
    to be the minimal, provider-agnostic shape run_codex_proof.py's own
    real dispatch loop already needed -- extracted here, not invented."""
    success: bool
    stdout: str
    stderr: str
    elapsed_s: float
    error: "str | None" = None
    endpoint_metadata: "dict | None" = None  # provider-reported metadata only, never a secret


class EndpointAdapter:
    """The one contract. A concrete adapter implements dispatch(); nothing
    else about it is assumed by the bridge core."""

    name: str = "unnamed"
    qualification_status: str = "UNKNOWN"  # READY_WITH_EXISTING_AUTH / INSTALLED_NOT_AUTHENTICATED /
                                            # AUTHENTICATED_BUT_HUMAN_GATED / REQUIRES_NEW_CREDENTIAL /
                                            # REQUIRES_BILLING / NOT_INSTALLED / UNSUPPORTED / UNKNOWN

    def dispatch(self, prompt: str) -> AdapterResult:
        raise NotImplementedError
