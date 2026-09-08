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

# ============================================================
# Check 4 — named-subsystem/module/class existence sanity check.
#
# 2026-09-02, following a design-review pass
# (audits/2026-09-02_architectural_self_knowledge_verifier_implementation.md)
# prompted by the traced "EventCore" fabrication (a response confidently
# describing a subsystem that does not exist, mimicking real
# CartographerDB citation format exactly). Deliberately narrow: this is an
# EXISTENCE/NAME sanity check against the real, already-daily
# echo_cartographer.py scan — not a general architecture fact-checker. It
# does not verify relationships, responsibilities, call graphs, runtime
# behavior, or anything else about a claim beyond "does a module or class
# by this name appear in the current static scan." See this check's own
# section of the implementation report for the full scope discipline.
# ============================================================

# Backtick-quoted identifier, e.g. `memory_bridge` -- the exact syntax a
# genuinely grounded response already uses when citing real Cartographer
# data (confirmed directly against real production responses).
_BACKTICK_IDENTIFIER_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")

# A bare CamelCase/PascalCase token (at least two capitalized segments),
# e.g. "EventCore", "DataForge". Deliberately excludes ordinary
# single-capital English words ("Memory", "System", "Architecture",
# "Component") -- they have no internal capital, so they never match this
# pattern on their own, regardless of context.
_CAMELCASE_TOKEN_RE = re.compile(r"\b([A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+)\b")

# Architecture vocabulary a bare CamelCase token must appear near to count
# as a claim about one of Echo's own components -- narrows this to "X is
# described as one of Echo's own subsystems," not any capitalized word
# appearing anywhere in the text.
_ARCH_VOCAB_RE = re.compile(
    r"\b(subsystem\w*|modules?|components?|handles?|responsible for)\b",
    re.IGNORECASE,
)
# Same proximity-window convention already established and tested in
# echo_ground_truth.py's architecture-slice matcher.
_CLAIM_PROXIMITY_WINDOW = 60

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# Existence-uncertainty: the identifier's own EXISTENCE is what's in doubt
# -- "exist(s)" co-occurring with an uncertainty marker in the SAME
# sentence. Deliberately narrower than a general hedge check, per the
# explicit design refinement: "I believe EventCore is responsible for
# routing events" never mentions "exist" at all, so it is NOT
# existence-uncertain -- it's a confident (if hedged) ATTRIBUTE claim,
# which stays checkable. "EventCore might exist somewhere in the
# architecture, but I'm not certain" mentions both "exist" and "not
# certain" in the same sentence, so it IS existence-uncertain and is
# suppressed. This is the one deterministic rule this module uses to
# distinguish "hedge on an attribute claim" (still checkable) from
# "doubt about existence itself" (not checkable) -- documented here
# because it's the trickiest precision/recall tradeoff in this check.
_UNCERTAINTY_MARKER_RE = re.compile(
    r"\b(don'?t know|not sure|not certain|uncertain|unclear|might|may|"
    r"could|possibly)\b",
    re.IGNORECASE,
)
_EXISTS_WORD_RE = re.compile(r"\bexists?\b", re.IGNORECASE)

# Genuinely hypothetical framing -- "if X had/were," "suppose," "let's
# imagine/pretend," "hypothetical(ly)," "fictional." Distinct from
# existence-uncertainty above: this is the user or Echo explicitly setting
# up a counterfactual, not expressing doubt about the real architecture.
_HYPOTHETICAL_RE = re.compile(
    r"\bif\b[^.!?\n]{0,30}\b(had|were|existed)\b"
    r"|\bsuppose\b|\bhypothetical(ly)?\b|\bfictional\b"
    r"|\blet'?s (say|imagine|pretend)\b|\bimagine\b",
    re.IGNORECASE,
)


def _extract_candidate_identifiers(text: str) -> "list[str]":
    """Backtick-quoted identifiers, plus CamelCase tokens occurring near
    architecture vocabulary. Deliberately narrow -- see this check's own
    module-level scope discipline above. Order-preserving, deduplicated."""
    seen: "list[str]" = []
    for m in _BACKTICK_IDENTIFIER_RE.finditer(text):
        name = m.group(1)
        if name not in seen:
            seen.append(name)
    vocab_starts = [m.start() for m in _ARCH_VOCAB_RE.finditer(text)]
    for m in _CAMELCASE_TOKEN_RE.finditer(text):
        name = m.group(1)
        if name in seen:
            continue
        if any(abs(m.start() - v) <= _CLAIM_PROXIMITY_WINDOW for v in vocab_starts):
            seen.append(name)
    return seen


def _sentence_is_checkable(sentence: str) -> bool:
    """False (suppress) if the sentence is genuinely hypothetical, or if
    it expresses uncertainty about the identifier's own EXISTENCE rather
    than a hedge on an attribute/role claim. True (checkable) otherwise --
    including a hedged-but-confident attribute claim ("I believe X is
    responsible for Y"), per the explicit design refinement: do not let
    uncertainty language become an escape hatch for an otherwise
    confident, unsupported architectural assertion."""
    if _HYPOTHETICAL_RE.search(sentence):
        return False
    if _EXISTS_WORD_RE.search(sentence) and _UNCERTAINTY_MARKER_RE.search(sentence):
        return False
    return True


def _camel_to_snake_guess(name: str) -> str:
    """One deterministic transform: CamelCase -> snake_case
    ("EventCore" -> "event_core"). A no-op on an already-lowercase/
    already-snake_case name (e.g. a backtick-quoted "memory_bridge" passes
    through unchanged). No stemming, no synonym table, no fuzzy matching
    beyond this single transform -- a real subsystem paraphrased in a way
    this doesn't reconstruct is an accepted false negative."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def find_unsupported_architecture_claims(text: str) -> "list[str]":
    """Identifiers confidently named as one of Echo's own subsystems/
    modules/classes that do not match anything in the real, current
    CartographerDB scan. Returns [] if nothing checkable was found, every
    checkable identifier matched, or Cartographer itself is unavailable --
    never raises, fails closed toward under-detection in every branch."""
    candidates = _extract_candidate_identifiers(text)
    if not candidates:
        return []

    sentences = _SENTENCE_SPLIT_RE.split(text)
    unsupported: "list[str]" = []

    try:
        from echo_cartographer import CartographerDB
        db = CartographerDB()
    except Exception as e:
        logger.debug(f"[SELF_KNOWLEDGE_VERIFY] Cartographer unavailable for identifier check: {e}")
        return []

    try:
        for name in candidates:
            mentions = [s for s in sentences if name in s]
            if not mentions:
                continue
            if not any(_sentence_is_checkable(s) for s in mentions):
                continue  # every occurrence hedged/hypothetical -- skip entirely

            snake_guess = _camel_to_snake_guess(name)
            found = False
            try:
                row = db.conn.execute(
                    "SELECT 1 FROM modules WHERE module_name = ? LIMIT 1", (snake_guess,)
                ).fetchone()
                found = row is not None
                if not found:
                    row = db.conn.execute(
                        "SELECT 1 FROM classes WHERE class_name = ? LIMIT 1", (name,)
                    ).fetchone()
                    found = row is not None
            except Exception as e:
                logger.debug(f"[SELF_KNOWLEDGE_VERIFY] Cartographer query failed for {name!r}: {e}")
                continue  # fail closed for this one identifier -- don't flag it
            if not found:
                unsupported.append(name)
    finally:
        db.close()

    return unsupported


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


# ============================================================
# Check 5 — false-NEGATIVE core-subsystem-denial detection.
#
# 2026-09-08, living-self-model mission. Checks 1-4 above only ever catch
# a POSITIVE fabrication (Echo confidently claims something exists/is true
# that isn't). None of them can catch the opposite, empirically-confirmed
# failure from the same night's Self-Transparency Audit: Echo affirmed
# RiverBrain's existence in four separate live conversations, then flatly
# denied it exists in a fifth ("not a literal entity... hypothetical"),
# while river_brain.pkl genuinely held 160,000+ real observations
# throughout. This check closes that specific, proven gap -- deliberately
# narrow, same discipline as every check above: a small, explicit
# allowlist of core subsystems with cheap, unambiguous ground truth in
# self_model.json (see self_model_claims.KNOWN_SUBJECTS), not a general
# "is this negative claim true" verifier.
# ============================================================

# A denial sentence: the subject name co-occurring with a negation of
# existence/reality in the same sentence. Deliberately conservative --
# "I'm not sure if RiverBrain is the right name for it" is NOT a denial
# (handled by reusing _sentence_is_checkable's existing hypothetical/
# uncertainty suppression below); "RiverBrain doesn't exist" and "there is
# no RiverBrain" are.
_DENIAL_RE = re.compile(
    r"\b(doesn'?t|does\s+not|isn'?t|is\s+not|no)\b[^.\n]{0,40}\b(exist|real|"
    r"literal|actual)\b"
    r"|\bnot\s+(?:a\s+)?(?:real|literal|actual)\b"
    r"|\bno\s+such\b",
    re.IGNORECASE,
)


def find_false_negative_component_claims(text: str, self_model: "dict | None" = None) -> "list[str]":
    """Core subsystems (from self_model_claims.KNOWN_SUBJECTS) that `text`
    confidently denies exist, where self_model.json's own real data shows
    the opposite (a nonzero/truthy value at the subject's known path).
    Returns [] if nothing checkable, everything checked out, or ground
    truth is unavailable -- never raises, fails closed toward
    under-detection exactly like checks 1-4."""
    if self_model is None:
        self_model = _load_self_model()
    if not self_model:
        return []

    try:
        from app.core.self_model_claims import KNOWN_SUBJECTS
    except Exception as e:
        logger.debug(f"[SELF_KNOWLEDGE_VERIFY] self_model_claims unavailable: {e}")
        return []

    sentences = _SENTENCE_SPLIT_RE.split(text)
    false_denials: "list[str]" = []

    for subject, path in KNOWN_SUBJECTS.items():
        if subject not in text:
            continue
        mentions = [s for s in sentences if subject in s]
        denial_sentences = [s for s in mentions if _DENIAL_RE.search(s)]
        if not denial_sentences:
            continue
        # Deliberately NOT reusing _sentence_is_checkable() here -- that
        # function's _HYPOTHETICAL_RE suppression was built for POSITIVE
        # fabrication claims ("if X existed..." genuinely isn't a claim
        # about reality), but a denial sentence describing itself as
        # "more of a hypothetical framing than a literal subsystem" IS the
        # confident claim under test, not a counterfactual setup --
        # confirmed against this check's own real motivating case (Echo's
        # actual 2026-09-08 denial used exactly that phrasing). Only
        # suppress a denial for genuine first-person UNCERTAINTY
        # ("I'm not sure whether RiverBrain exists"), not for
        # "hypothetical"/"suppose"/"if X had" language, which in a denial
        # sentence is typically part of the denial's own rhetoric.
        if not any(not _UNCERTAINTY_MARKER_RE.search(s) for s in denial_sentences):
            continue  # every occurrence hedged with genuine first-person doubt

        # Resolve the dotted path against the real self_model dict. Stop at
        # the first list-valued node (e.g. "...checks" is itself the
        # ground truth -- "does this dict have entries" -- rather than
        # walking into an arbitrary key inside it).
        node = self_model
        real_value = None
        try:
            for part in path.split("."):
                if not isinstance(node, dict):
                    node = None
                    break
                node = node.get(part)
            real_value = node
        except Exception:
            real_value = None

        is_really_true = bool(real_value) and real_value not in (0, "0")
        if is_really_true:
            false_denials.append(subject)

    return false_denials


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

        # Check 5 -- run before the others, since a false-negative
        # component denial is a more specific, higher-confidence signal
        # than the generic catch-all Check 4 below, and should not be
        # masked by an unrelated earlier match.
        false_denials = find_false_negative_component_claims(response_text, self_model)
        if false_denials:
            names = ", ".join(false_denials)
            return (
                f"\n\n⚠️ Note: this response denies that {names} exists/is real — "
                f"the current self-model shows real, active evidence to the "
                f"contrary. Treat the denial as unverified, not the underlying fact.",
                False,
            )

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

        # Check 4 (2026-09-02) -- named-subsystem/module/class existence
        # sanity check. Deliberately the last, catch-all branch: the three
        # checks above are specific, mutually-exclusive-in-practice claim
        # shapes; this one is an orthogonal dimension (does a *named
        # component* exist) that could in principle co-occur with any of
        # them. Kept as a simple final fallback rather than restructuring
        # this function to run all four independently and concatenate --
        # if a response happens to also trip one of the first three, this
        # check simply doesn't run that time. An accepted, documented
        # limitation, not an oversight.
        unsupported = find_unsupported_architecture_claims(response_text)
        if unsupported:
            names = ", ".join(f"`{n}`" for n in unsupported)
            return (
                f"\n\n⚠️ Note: no module or class named {names} was found in the "
                f"current architecture scan of Echo's own codebase — treat "
                f"{'this name' if len(unsupported) == 1 else 'these names'} as "
                f"unverified.",
                False,
            )

        return None, None
    except Exception as e:
        logger.debug(f"[SELF_KNOWLEDGE_VERIFY] verify_self_knowledge_claims failed: {e}")
        return None, None
