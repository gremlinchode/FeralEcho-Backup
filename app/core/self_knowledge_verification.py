# app/core/self_knowledge_verification.py
# ============================================================
# SELF-KNOWLEDGE CLAIM VERIFICATION
#
# 2026-07-19, "remove every excuse" pass. Same pattern proven in
# code_verification.py — extract a checkable claim, check it against
# reality, flag it if false — applied to self-referential claims about
# Echo's own architecture instead of code correctness.
#
# Deliberately narrow, not a general fact-checker: self-referential prose
# is far harder to parse reliably than a fenced code block. This checks
# three specific, high-value claim shapes, each with a precise, cheap
# ground-truth source — not an attempt to verify arbitrary claims about
# Echo's architecture in general (which would mean using one LLM to
# fact-check another, a technique with its own reliability problems this
# project has no particular reason to trust more than the thing being
# checked). Missing a checkable claim is an acceptable cost; falsely
# flagging a correct one is not — every regex here is written to fail
# toward under-detection.
#
# Motivating case, from the forensic audit this session started with:
# asked what stops a bad self-edit from deploying, Echo's raw council
# voice claimed "peer council ratings... ensure proposed changes are
# acceptable" — false; the real gate is a cooldown plus F1/F2/F3. That
# exact claim shape is check #3 below.
# ============================================================

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SELF_MODEL_PATH = os.path.join(_PROJECT_ROOT, "memory", "self_model.json")

_SELF_EDIT_TARGET_FILE = "self_edit_generated.py"

# A number directly followed by "check"/"checks" — matches "16 checks",
# "10-12 checks" (captures the number nearest the word, "12"), etc.
_CHECK_COUNT_RE = re.compile(r"\b(\d+)\s*(?:total\s+)?(?:liveness\s+)?checks?\b", re.IGNORECASE)

# "self-edit ... targets/modifies/edits ... X.py" within a short window —
# deliberately narrow phrasing so this only fires on an actual targeting
# claim, not any incidental mention of a .py file near the words
# "self-edit" (e.g. correctly naming self_edit_manager.py as the file
# that *contains the safety checks* is not a targeting claim).
_SELF_EDIT_TARGET_CLAIM_RE = re.compile(
    r"self[- ]edit\w*[^.\n]{0,60}?\b(?:targets?|modifies|edits?(?:\s+only)?|changes?)\b"
    r"[^.\n]{0,40}?`?([\w/]+\.py)`?",
    re.IGNORECASE,
)

# The specific, already-confirmed-false claim shape from the forensic
# audit: peer/council review framed as a gate on self-edit deployment.
_COUNCIL_GATES_CLAIM_RE = re.compile(
    r"(?:peer\s+council|council\s+rating|council\s+review)\W+(?:\w+\W+){0,15}?"
    r"(?:gate|approv|prevent|block|stop|ensure)",
    re.IGNORECASE,
)


def find_check_count_claim(text: str) -> "int | None":
    """First digit-based Liveness Ledger check-count claim in the text,
    or None if there isn't one. Only the first match — a response citing
    several unrelated numbers isn't this module's concern."""
    m = _CHECK_COUNT_RE.search(text)
    return int(m.group(1)) if m else None


def find_self_edit_target_claim(text: str) -> "str | None":
    """A specific file-targeting claim about self-edit, or None. Narrow
    phrasing on purpose — see the regex's own comment above."""
    m = _SELF_EDIT_TARGET_CLAIM_RE.search(text)
    return m.group(1) if m else None


def has_council_gates_self_edit_claim(text: str) -> bool:
    """True if the text makes the specific, already-confirmed-false claim
    that peer/council review gates self-edit deployment."""
    return bool(_COUNCIL_GATES_CLAIM_RE.search(text))


def _load_self_model() -> "dict | None":
    try:
        with open(_SELF_MODEL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.debug(f"[SELF_KNOWLEDGE_VERIFY] self_model.json read failed: {e}")
        return None


def verify_self_knowledge_claims(response_text: str) -> "tuple[str | None, bool | None]":
    """Orchestrates verification for a full response. Returns
    (caveat, verified) — same tri-state contract as
    code_verification.verify_response_code(): verified is True if a
    checked claim matched real ground truth, False if a checked claim was
    wrong, None if nothing in this narrow scope was checkable (the common
    case — most responses make no claim this module knows how to check).
    Never raises — any internal failure fails open (no caveat, no signal)."""
    try:
        if has_council_gates_self_edit_claim(response_text):
            return (
                "\n\n⚠️ Note: this response describes peer/council ratings as gating "
                "self-edit deployment — that's not accurate. The real gate is a "
                "60-minute cooldown plus the F1/F2/F3 safety pipeline; council "
                "ratings don't currently influence deployment at all.",
                False,
            )

        self_model = _load_self_model()

        claimed_count = find_check_count_claim(response_text)
        if claimed_count is not None and self_model is not None:
            real_checks = self_model.get("verified_capabilities", {}).get("checks", {})
            real_count = len(real_checks)
            if real_count and claimed_count != real_count:
                return (
                    f"\n\n⚠️ Note: this response cites {claimed_count} Liveness Ledger "
                    f"checks — the real current count is {real_count}. Treat the "
                    f"specific number as unverified.",
                    False,
                )
            if real_count:
                return None, True

        claimed_target = find_self_edit_target_claim(response_text)
        if claimed_target is not None:
            claimed_basename = claimed_target.rsplit("/", 1)[-1]
            if claimed_basename != _SELF_EDIT_TARGET_FILE:
                return (
                    f"\n\n⚠️ Note: this response names `{claimed_target}` as what "
                    f"self-edit targets — the real target is "
                    f"`app/core/{_SELF_EDIT_TARGET_FILE}`. Treat the file name as "
                    f"unverified.",
                    False,
                )
            return None, True

        return None, None
    except Exception as e:
        logger.debug(f"[SELF_KNOWLEDGE_VERIFY] verify_self_knowledge_claims failed: {e}")
        return None, None
