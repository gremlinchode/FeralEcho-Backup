"""Thin re-export wrapper. The real implementation moved verbatim to
app/core/skill_ledger/matcher.py during the 2026-09-28 integration-readiness pass (see
audits/2026-09-28_vsl_integration_readiness.md) -- the production Echo adapter imports
that module directly; this module exists so every historical harness
(prospective_transfer.py, accumulation.py, harness.py, verify_diff_extract.py) and
every `from . import diff_extract as DE` call site keeps working, unmodified, exactly
as before this move. Zero logic differs (confirmed: verify_diff_extract.py's full
15/15 suite re-run immediately after this move, unchanged result) except one
byte-for-byte-behavior-preserving dead-code removal inside `_wildcard_aware_equal`
(an unused `pattern_re = re.escape(...)` assignment and a no-op `for m in
re.finditer(...): pass` loop, neither of which had any observable effect) -- disclosed
here rather than silently dropped, per this project's own standing discipline.
"""
from app.core.skill_ledger.matcher import (  # noqa: F401
    collect_dict_key_vocab,
    abstract,
    find_divergence,
    extract_transformation,
    apply_skill,
    _WILDCARD_PREFIX,
    _Abstractor,
    _is_wildcard_value,
    _call_name,
    _enclosing_call_name,
    _find_function,
    _dump,
    _matches,
    _wildcard_aware_equal,
    _rehydrate,
    _replace_and_unparse,
)
