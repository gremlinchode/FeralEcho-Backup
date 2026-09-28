"""Append-only, in-memory ledger for E5-mini G0. Pure Python, no file I/O
required for correctness (dump_json() is provided for inspection only),
zero production dependency.

Append-only is structural, not a convention someone has to remember: every
record_*() method raises on a duplicate id rather than silently
overwriting - mirrors claude_relay/relay.py's own append_note() design
(only ever opens in append mode; there is no code path capable of
overwriting a prior entry).
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional

from .schema import (
    ConstructionCallRecord,
    SolverCallRecord,
    OracleReference,
    ConditionValidity,
)


class LedgerIntegrityError(ValueError):
    """Raised on any attempt to violate append-only semantics."""


class Ledger:
    def __init__(self) -> None:
        self.construction_calls: "dict[str, ConstructionCallRecord]" = {}
        self.solver_calls: "dict[str, SolverCallRecord]" = {}
        self.oracle_references: "dict[str, OracleReference]" = {}
        self.condition_validity: "dict[str, ConditionValidity]" = {}
        self._seq = 0

    def next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}-{self._seq:05d}"

    def record_construction(self, rec: ConstructionCallRecord) -> None:
        if rec.call_id in self.construction_calls:
            raise LedgerIntegrityError(f"duplicate construction call_id {rec.call_id!r}")
        self.construction_calls[rec.call_id] = rec

    def record_solver(self, rec: SolverCallRecord) -> None:
        if rec.call_id in self.solver_calls:
            raise LedgerIntegrityError(f"duplicate solver call_id {rec.call_id!r}")
        self.solver_calls[rec.call_id] = rec

    def record_oracle_reference(self, ref: OracleReference) -> None:
        if ref.reference_id in self.oracle_references:
            raise LedgerIntegrityError(f"duplicate oracle reference_id {ref.reference_id!r}")
        self.oracle_references[ref.reference_id] = ref

    def record_condition_validity(self, cv: ConditionValidity) -> None:
        # Condition validity is recomputed per full checker pass, not
        # strictly append-only across re-runs of the checker itself - but
        # within one checker pass each slot is set exactly once.
        if cv.slot_key in self.condition_validity:
            raise LedgerIntegrityError(f"duplicate condition-validity slot {cv.slot_key!r} in one checker pass")
        self.condition_validity[cv.slot_key] = cv

    def distinct_generation_ids(self) -> "set[str]":
        return {r.generation_id for r in self.solver_calls.values()}

    def solver_calls_by_generation(self, generation_id: str) -> "list[SolverCallRecord]":
        return [r for r in self.solver_calls.values() if r.generation_id == generation_id]

    def oracle_references_by_generation(self, generation_id: str) -> "list[OracleReference]":
        return [r for r in self.oracle_references.values() if r.generation_id == generation_id]

    def to_dict(self) -> dict:
        return {
            "construction_calls": {k: asdict(v) for k, v in self.construction_calls.items()},
            "solver_calls": {k: asdict(v) for k, v in self.solver_calls.items()},
            "oracle_references": {k: asdict(v) for k, v in self.oracle_references.items()},
            "condition_validity": {k: asdict(v) for k, v in self.condition_validity.items()},
        }

    def dump_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
