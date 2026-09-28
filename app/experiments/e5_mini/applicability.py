"""Trusted applicability runner - the FAMILY/GENERAL/ABSTAIN binding
action dispatcher (adjudication §5/mission §9). Machine-readable, never
inferred from free-text self-report: a declared action string is passed
in, this module ACTUALLY invokes one of three real entrypoints and
records which one genuinely ran - that record is ground truth, not the
solver's own claim.
"""
from __future__ import annotations

from .schema import Action


class ApplicabilityRunner:
    """Deterministic; each entrypoint is a real function call, so
    'declared FAMILY but dispatched GENERAL' (anomaly #21) is a real,
    observable divergence between two independent code paths, not a
    single field that could just be miscopied."""

    def __init__(self) -> None:
        self.dispatch_log: "list[tuple[str, Action]]" = []

    def solve_family(self, response_text: str) -> str:
        self.dispatch_log.append(("FAMILY", Action.FAMILY))
        return response_text

    def solve_general(self, response_text: str) -> str:
        self.dispatch_log.append(("GENERAL", Action.GENERAL))
        return response_text

    def abstain(self) -> str:
        self.dispatch_log.append(("ABSTAIN", Action.ABSTAIN))
        return ""

    def dispatch(self, declared_action: Action, response_text: str, force_entrypoint: "Action | None" = None) -> "tuple[str, Action]":
        """Normally dispatches to whatever was declared. `force_entrypoint`
        is a TEST-ONLY hook (anomaly #21) that makes the runner actually
        invoke a different entrypoint than what was declared, so the
        mismatch is real rather than simulated."""
        target = force_entrypoint if force_entrypoint is not None else declared_action
        if target == Action.FAMILY:
            return self.solve_family(response_text), Action.FAMILY
        if target == Action.GENERAL:
            return self.solve_general(response_text), Action.GENERAL
        if target == Action.ABSTAIN:
            return self.abstain(), Action.ABSTAIN
        return "", Action.UNKNOWN
