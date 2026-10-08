"""Current-task authority is supplied by a trusted registry, never a repair."""
from dataclasses import dataclass
import hashlib
import json


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_hash(source: str) -> str:
    return digest_bytes(source.encode("utf-8"))


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value) -> str:
    return digest_bytes(canonical(value))


def strict_json(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("non-finite JSON value")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject_constant)


@dataclass(frozen=True)
class Task:
    task_id: str
    revision: str
    source_sha256: str
    entrypoint: str
    score_direction: str
    tag_order: tuple[str, ...]  # Most preferred first; current task, not history.
    name_direction: str


FIELDS = {"schema", "task_id", "revision", "source_sha256", "entrypoint",
          "requirements", "unknown_fields", "conflict_refs"}
REQ_FIELDS = {"score_direction", "tag_order", "name_direction", "return_type",
              "input_effects", "field_schema"}


def parse_task(envelope: dict) -> Task:
    if type(envelope) is not dict or set(envelope) != FIELDS:
        raise ValueError("unsupported contract fields")
    if envelope["schema"] != "B-TASK-1":
        raise ValueError("unsupported contract schema")
    for field in ("unknown_fields", "conflict_refs"):
        value = envelope[field]
        if type(value) is not list or any(type(x) is not str for x in value):
            raise ValueError("invalid contract reason list")
    req = envelope["requirements"]
    if type(req) is not dict or set(req) != REQ_FIELDS:
        raise ValueError("incomplete or unsupported requirements")
    for key in ("task_id", "revision", "entrypoint", "source_sha256"):
        if type(envelope[key]) is not str or not 1 <= len(envelope[key]) <= 128:
            raise ValueError("invalid contract identifier")
    if not envelope["entrypoint"].isidentifier():
        raise ValueError("invalid entrypoint")
    h = envelope["source_sha256"]
    if len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
        raise ValueError("invalid source hash")
    if req["score_direction"] not in ("higher", "lower"):
        raise ValueError("unknown score direction")
    if req["name_direction"] not in ("ascending", "descending"):
        raise ValueError("unknown name direction")
    tags = req["tag_order"]
    if type(tags) is not list or len(tags) != 3 or any(
            type(t) is not str or not t or len(t) > 64 for t in tags):
        raise ValueError("expected three bounded tag strings")
    if len(set(tags)) != 3:
        raise ValueError("conflicting tag order")
    if req["return_type"] != "str" or req["input_effects"] != "preserve_values":
        raise ValueError("unsupported observations")
    if req["field_schema"] != ["name:str", "score:int", "tag:str"]:
        raise ValueError("unsupported field schema")
    return Task(envelope["task_id"], envelope["revision"], h, envelope["entrypoint"],
                req["score_direction"], tuple(tags), req["name_direction"])


def authority_status(source: str, envelope: dict, registry: dict) -> dict:
    """Registry is controller-owned input, not part of a proposer request.

    An exact approved contract digest and source/revision binding are necessary,
    not sufficient proof of intent. Registry identity/access needs external review.
    """
    reasons = []
    if type(envelope) is not dict:
        return {"status": "UNSUPPORTED_CONTRACT", "reasons": ["not an object"]}
    if envelope.get("conflict_refs"):
        reasons.append("CONFLICTING_CONTRACT")
    if envelope.get("unknown_fields"):
        reasons.append("UNKNOWN_CONTRACT")
    missing = bool(FIELDS - set(envelope))
    req = envelope.get("requirements")
    if type(req) is dict:
        missing = missing or bool(REQ_FIELDS - set(req)) or any(v is None for v in req.values())
        tags = req.get("tag_order")
        if type(tags) is list and all(type(t) is str for t in tags) and len(set(tags)) != len(tags):
            reasons.append("CONFLICTING_CONTRACT")
    if missing:
        reasons.append("UNKNOWN_CONTRACT")
    try:
        task = parse_task(envelope)
    except (ValueError, TypeError):
        if not missing:
            reasons.append("UNSUPPORTED_CONTRACT")
        task = None
    if task:
        if task.source_sha256 != source_hash(source):
            reasons.append("STALE_CONTRACT")
        approval = registry.get(task.task_id) if type(registry) is dict else None
        if type(approval) is not dict:
            reasons.append("UNKNOWN_CONTRACT")
        else:
            if any(not approval.get(k) for k in ("owner_ref", "oracle_review_ref")):
                reasons.append("UNKNOWN_CONTRACT")
            if approval.get("revision") != task.revision or approval.get(
                    "contract_sha256") != digest(envelope):
                reasons.append("STALE_CONTRACT")
    order = ("CONFLICTING_CONTRACT", "STALE_CONTRACT", "UNSUPPORTED_CONTRACT",
             "UNKNOWN_CONTRACT")
    flags = [r for r in order if r in reasons]
    return {"status": flags[0] if flags else "VALID_CONTRACT", "reasons": flags}
