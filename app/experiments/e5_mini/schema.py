"""Record schema for E5-mini G0 - see adjudication.md section 4 ("E5
manifest") for the authoritative field list this module implements.

Every field named in that manifest is represented below. Anything not
applicable or not available in mock mode is recorded as an explicit
UNKNOWN + reason (see `unknown()`), never fabricated - per mission
section 5's "Do not fabricate unavailable provenance."

Zero production dependency: no app.core.* imports, no I/O at import time.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Arm(str, Enum):
    P = "P"  # taught procedure: G(S, T_w)
    E = "E"  # episodic representation: C(S, T_w)
    Z = "Z"  # zero-teaching procedure: G(S, empty)
    N = "N"  # no acquired memory


class Action(str, Enum):
    FAMILY = "FAMILY"
    GENERAL = "GENERAL"
    ABSTAIN = "ABSTAIN"
    UNKNOWN = "UNKNOWN"  # malformed/undeclared - never coerced into a real action


class OracleResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"  # genuine infra failure - never coerced into PASS/FAIL (mission section 12)


class QueryKind(str, Enum):
    TEACHING = "teaching"        # the 2 bounded teaching observations - not a scored withheld trial
    RELATED = "related"          # withheld, in-family, requires the world convention
    NEAR_MATCH = "near_match"    # in-family but violates a stated precondition (§5 of adjudication)
    UNRELATED = "unrelated"      # not in this family at all


UNKNOWN = "UNKNOWN"


def sha256_of(obj: Any) -> str:
    """Deterministic content hash: canonical JSON, sorted keys, stable
    across dict key order and dataclass round-trips."""
    blob = json.dumps(obj, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def unknown(reason: str) -> dict:
    """Explicit UNKNOWN + reason - the only representation this module
    permits for unavailable provenance. Never a bare None, never a
    fabricated placeholder value."""
    return {"value": UNKNOWN, "reason": reason}


@dataclass
class MicroWorldSpec:
    """One paired w0/w1 fixture for a base family. SACRIFICIAL/synthetic
    only - this is explicitly NOT the frozen scientific task manifest
    (adjudication.md §7.1 requires a task custodian to seal that
    separately; mission section 4 forbids generating it in this mission).

    convention_token is the hidden local convention realization. It MUST
    NOT appear in family_id, world_id, query ids, public_spec, or any
    model-visible metadata - only inside teaching_queries' observed
    results. The condition checker (checker.py) independently scans for
    exactly this leak (planted anomaly #28).
    """
    family_id: str
    world_id: str  # "w0" | "w1"
    public_spec: str  # S - byte-identical across w0/w1 for a given family
    convention_token: str
    teaching_queries: "list[dict]"  # 2 bounded observations: {"query": str, "observed_result": str}
    related_queries: "list[dict]"  # 4 withheld, world-specific expected answers: {"query_id","query","expected_answer"}
    near_match_queries: "list[dict]"  # 3, family-shared (not per-world): {"query_id","query","correct_action"}
    unrelated_queries: "list[dict]"  # 3, family-shared: {"query_id","query","correct_action"}


@dataclass
class ConstructionCallRecord:
    call_id: str
    arm: Arm
    family_id: str
    world_id: "Optional[str]"  # None for Z - one Z per family, shared across both worlds (§7.3)
    constructor_identity: str  # e.g. "mock-constructor-v1" - never a real model name/digest in this mission
    system_instruction_hash: str
    public_spec_hash: str
    teaching_input_hash: str  # sha256_of("") for Z (empty experience field) - never omitted
    experience_field_empty: bool  # True only for Z - the sole intended P/Z input difference (adjudication §3)
    construction_attempt_index: int  # 0-based; >0 without an explicit declared multi-attempt policy is a violation
    output_ceiling_tokens: int
    artifact_id: str
    artifact_hash: str
    artifact_text: str
    semantic_feedback_exposure: bool  # must be False - no critique/retry/best-of/teaching-based promotion (§3)
    timestamp: str
    requested_options: dict
    effective_options: dict
    model_backend_identity: "dict"  # unknown(...) in mock mode - real E5 must resolve a pinned package identity (§7.3)
    cost_tokens_in: int
    cost_tokens_out: int


@dataclass
class SolverCallRecord:
    call_id: str
    arm: Arm
    family_id: str
    world_id: str  # which world's oracle this row scores against; for P/E always == construction world
    query_id: str
    query_kind: QueryKind
    generation_id: str  # identity of the actual model generation - shared across dependent oracle refs (Z/N reuse, §7.5/§7.6/§10)
    parent_construction_call_id: "Optional[str]"  # None only for N
    memory_artifact_id: "Optional[str]"
    memory_field_text: str  # exactly what the solver received as acquired memory - "" for N
    ordered_messages: "list[dict]"  # ACTUAL recorded system/user messages post-transformation, per §7 "gateway-observed"
    council_entry: bool  # must be False (adjudication §4: "zero council entry")
    synthesis_routing: bool  # must be False
    tool_list_injected: bool  # must be False
    model_tool_definitions: "list"  # must be []
    declared_action: Action  # what the response's structured field claims
    dispatched_entrypoint: Action  # what the trusted runner ACTUALLY invoked - ground truth (may differ from declared_action)
    response_text: str
    response_artifact_hash: str
    timestamp: str
    requested_options: dict
    effective_options: dict


@dataclass
class OracleReference:
    """Links one solver generation to one oracle scoring. Multiple
    references may share a generation_id (Z/N reuse across w0/w1
    scoring) - this is the mechanism that keeps that reuse from being
    miscounted as extra generations (planted anomaly #18, mission §10)."""
    reference_id: str
    generation_id: str
    family_id: str
    scored_against_world_id: str
    query_id: str
    oracle_result: OracleResult
    oracle_detail: str


@dataclass
class ConditionValidity:
    slot_key: str  # f"{family_id}:{world_id}:{arm}:{query_id}"
    passed: bool
    violations: "list[str]"  # empty iff passed
