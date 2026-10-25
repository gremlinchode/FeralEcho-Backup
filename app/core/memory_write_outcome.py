"""Per-message outcomes for one conversation-memory write.

Pure data. This module does not import the memory bridge, open an index,
or talk to the network. `accepted` means the persistence call returned
success. It does not mean a later search will return the text, and it
does not mean FAISS ntotal grew.

Future callers of `add_to_vector_memory()` must read `outcome` on the
returned object. The object is truthy for every outcome, including
`rejected` and `failed`, so a truthiness check is not evidence of a
successful write.
"""

from __future__ import annotations

from dataclasses import dataclass

ACCEPTED = "accepted"
REJECTED = "rejected"
FAILED = "failed"

VALIDATOR_BLOCK = "validator_block"
EMBED_SHAPE = "embed_shape"
PERSISTED = "persisted"
PERSIST_FAILED = "persist_failed"

OUTCOMES = frozenset({ACCEPTED, REJECTED, FAILED})
REASONS = frozenset({VALIDATOR_BLOCK, EMBED_SHAPE, PERSISTED, PERSIST_FAILED})

TRANSPORT_OR_HANDLER_ERROR = "transport_or_handler_error"

_PUBLIC_FIELDS = ("outcome", "reason", "persisted")


def _triple_ok(outcome: str, reason: str, persisted: bool) -> bool:
    if outcome not in OUTCOMES or reason not in REASONS or not isinstance(persisted, bool):
        return False
    if outcome == ACCEPTED:
        return reason == PERSISTED and persisted is True
    if outcome == REJECTED:
        return reason == VALIDATOR_BLOCK and persisted is False
    return reason in (EMBED_SHAPE, PERSIST_FAILED) and persisted is False


@dataclass(frozen=True)
class MemoryWriteOutcome:
    """One half of a conversation write.

    Read `outcome` explicitly. Do not use this object as a boolean.
    `accepted` confirms that persistence returned success, not that the
    text is retrievable and not that ntotal increased. A failed outcome
    can follow an in-memory mutation; nothing here retries or rolls back.
    """

    outcome: str
    reason: str
    persisted: bool

    def __post_init__(self) -> None:
        if not _triple_ok(self.outcome, self.reason, self.persisted):
            raise ValueError("inconsistent memory write outcome")

    def as_dict(self) -> dict:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "persisted": self.persisted,
        }


def classify_memory_write(
    *,
    validator_allowed: bool,
    embed_rows: int | None,
    persist_ok: bool | None,
) -> MemoryWriteOutcome:
    """Map a finished write attempt to one outcome.

    `validator_allowed` False is a rejection and is decided before embed
    shape or persistence are consulted. An embed row count other than 1
    is `failed` / `embed_shape` even if `persist_ok` is accidentally true.
    After a one-row embed, only `persist_ok is True` is `accepted`. False
    and None are `failed` / `persist_failed` and do not claim success.
    Exceptions are not passed in; callers let those propagate.
    """

    if not validator_allowed:
        return MemoryWriteOutcome(REJECTED, VALIDATOR_BLOCK, False)
    # `bool` is an int subclass, so True == 1. Only a real int row count counts.
    if type(embed_rows) is not int or embed_rows != 1:
        return MemoryWriteOutcome(FAILED, EMBED_SHAPE, False)
    if persist_ok is True:
        return MemoryWriteOutcome(ACCEPTED, PERSISTED, True)
    return MemoryWriteOutcome(FAILED, PERSIST_FAILED, False)


def conversation_turn_response(
    user: MemoryWriteOutcome,
    echo: MemoryWriteOutcome,
    thought_provoking: bool,
    retention: str,
) -> dict:
    """HTTP body for a completed `/memory/conversation` handler.

    `status` stays `ok` for accepted, rejected, and failed halves. The
    two halves stay separate. Message text is not a parameter and is not
    copied into the body.
    """

    if not isinstance(user, MemoryWriteOutcome) or not isinstance(echo, MemoryWriteOutcome):
        raise TypeError("conversation_turn_response requires MemoryWriteOutcome halves")
    return {
        "status": "ok",
        "thought_provoking": thought_provoking,
        "retention": retention,
        "user": user.as_dict(),
        "echo": echo.as_dict(),
    }


def _public_half(raw: object) -> dict | None:
    if not isinstance(raw, dict):
        return None
    outcome = raw.get("outcome")
    reason = raw.get("reason")
    persisted = raw.get("persisted")
    if not _triple_ok(outcome, reason, persisted):
        return None
    return {"outcome": outcome, "reason": reason, "persisted": persisted}


def client_outcome_from_body(body: object) -> dict | None:
    """Copy only the allow-listed user and echo fields.

    Returns None when either half is missing or inconsistent. Extra keys
    on the body or on a half are dropped.
    """

    if not isinstance(body, dict):
        return None
    user = _public_half(body.get("user"))
    echo = _public_half(body.get("echo"))
    if user is None or echo is None:
        return None
    return {"user": user, "echo": echo}


def client_outcome_log_line(body: object) -> str | None:
    """Enum log line, or None when both halves were accepted.

    An unsafe body returns the transport token and nothing from `body`.
    The line names only the two outcomes and the two reason codes.
    """

    parsed = client_outcome_from_body(body)
    if parsed is None:
        return TRANSPORT_OR_HANDLER_ERROR
    user = parsed["user"]
    echo = parsed["echo"]
    if user["outcome"] == ACCEPTED and echo["outcome"] == ACCEPTED:
        return None
    return (
        f"user={user['outcome']} reason={user['reason']} "
        f"echo={echo['outcome']} reason={echo['reason']}"
    )


def interpret_client_response(status_code: int, body: object) -> tuple[str | None, dict | None]:
    """Map a synthetic or parsed handler result to (log line, sanitized dict).

    Non-200 and unsafe 200 bodies produce the transport token and no
    dict. The log line is None only when both halves were accepted.
    `body` is not interpolated into the token.
    """

    if status_code != 200:
        return TRANSPORT_OR_HANDLER_ERROR, None
    sanitized = client_outcome_from_body(body)
    if sanitized is None:
        return TRANSPORT_OR_HANDLER_ERROR, None
    return client_outcome_log_line(sanitized), sanitized
