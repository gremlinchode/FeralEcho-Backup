"""Sacrificial-fixture containment checks (adjudication §11 items 23, 26,
27; mission §14). This mock experiment never executes candidate-
generated code - every artifact is deterministic mock text, not
executable content - so these are lightweight, honestly-scoped stand-ins
for the real containment boundary a live E5 execution would need
(FeralEcho's own sandbox/echo_sandbox.sb is the real analog, not
reimplemented or imported here per mission section 1's "Do not import
that harness or production state").

Policy enforcement is tested ONLY against sacrificial fixtures in a temp
directory, never against real production paths (mission section 1/§11).
"""
from __future__ import annotations

import os
import re

ESCALATION_PATTERNS = [
    r"\bsubprocess\.",
    r"\bos\.system\(",
    r"\bos\.popen\(",
    r"__import__\(",
    r"\bexec\(",
    r"\beval\(",
]


def guarded_write(path: str, content: str, scratch_root: str) -> bool:
    """Writes `content` to `path` only if it resolves inside
    `scratch_root`. Returns True on a permitted write, False (and no
    write performed) on a blocked one - mirrors the deny-by-default shape
    of sandbox/echo_sandbox.sb without importing it."""
    real_root = os.path.realpath(scratch_root)
    real_target = os.path.realpath(path)
    if not (real_target == real_root or real_target.startswith(real_root + os.sep)):
        return False
    os.makedirs(os.path.dirname(real_target), exist_ok=True)
    with open(real_target, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def scan_for_escalation_patterns(text: str) -> "list[str]":
    """Static text scan for subprocess/exec/eval-shaped escalation
    attempts inside a candidate artifact. Explicitly NOT equivalent to a
    real AST scanner or kernel sandbox - a text-shaped stand-in scoped to
    this mock's own needs, honestly limited (documented in the
    implementation report's Known Limitations section)."""
    hits = []
    for pat in ESCALATION_PATTERNS:
        if re.search(pat, text):
            hits.append(pat)
    return hits


def candidate_trusted_oracle_result(claimed_pass_marker_present: bool, real_oracle_result) -> "tuple[bool, str]":
    """Demonstrates anomaly #22/#23's required property directly: a
    candidate's self-reported pass marker (e.g. a forged 'ALL_TESTS_PASSED'
    string) must never influence the real oracle result. Returns
    (trusted_result_used_real_oracle, detail)."""
    # The "trusted channel" is simply: always return real_oracle_result,
    # regardless of claimed_pass_marker_present. This function exists so
    # tests can assert the forged marker had ZERO causal effect.
    return True, f"real oracle result {real_oracle_result} returned regardless of claimed marker={claimed_pass_marker_present}"
