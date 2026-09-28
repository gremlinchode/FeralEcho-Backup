"""Feature-signature extraction — pure function, derived ONLY from rendered
prompt surface text (function signature string + natural-language spec),
NEVER from internal kind/split labels. See PREREG_ADDENDUM.md 'Blocker 2'.

Verified property (checked by verify_features.py, not merely asserted
here): this function's output must be computable by someone who has never
seen AP-0's tasks.py/tasks_v2.py source and is handed only the rendered
`sig` and `spec` strings a real model would actually receive."""
from __future__ import annotations
import re


def arg_count_bucket(sig: str) -> str:
    """sig like 'def fn(a, b, c):' -> '2' style bucket. Pure string parsing,
    no AST, no import of anything task-specific."""
    m = re.search(r"\((.*)\)", sig)
    if not m:
        return "1"
    inner = m.group(1).strip()
    if not inner:
        return "1"
    n = len([p for p in inner.split(",") if p.strip()])
    if n <= 1:
        return "1"
    if n == 2:
        return "2"
    return "3+"


def input_shape(spec: str) -> str:
    """Keyword presence only -- never a substring match against the split
    label itself, which never appears in rendered spec text (confirmed by
    direct read of tasks_v2.py's BASE_SPEC/spec construction: the word
    'dict'/'tuple'/'string' appears because that's genuinely what the
    argument type is, not because it encodes T vs S)."""
    s = spec.lower()
    if "dict" in s:
        return "dict"
    if "tuple" in s:
        return "tuple"
    if "text" in s or "string" in s:
        return "string"
    return "other"


def feature_signature(sig: str, spec: str) -> "tuple[str, str]":
    """The (arg_count_bucket, input_shape) pair -- the full feature space
    the lookup-table selector indexes by. A tuple, not a dict, so it's
    directly usable as a dict key without any serialization step."""
    return (arg_count_bucket(sig), input_shape(spec))
