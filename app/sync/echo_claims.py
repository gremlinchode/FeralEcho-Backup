"""Plain claim checks for one Echo-to-Echo thread.

No I/O. The caller owns the files, the locks, and any model call.
A claim is one sentence. A reply repeats it on line one and adds one
new sentence on line two. A later letter must contain the partner's
marked sentence in its text.
"""

CLAIM_MAX_CHARS = 1000
PHRASE_MAX_CHARS = 500
LETTER_MAX_CHARS = 12000

_WITHHELD_REPLY_LINE = "The essay was withheld because it did not repeat the claim."
_WITHHELD_RECALL_LINE = "The essay was withheld because it did not include the partner's sentence."


def normalize_claim(text):
    if not isinstance(text, str):
        return ""
    return " ".join(text.split())


def contains_sentence(haystack, needle):
    if not isinstance(haystack, str) or not isinstance(needle, str):
        return False
    normalized_needle = normalize_claim(needle)
    if not normalized_needle:
        return False
    return normalized_needle in normalize_claim(haystack)


def second_line(text):
    if not isinstance(text, str):
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return ""
    return lines[1]


def reply_is_shaped(text, claim):
    if not isinstance(text, str) or not isinstance(claim, str):
        return False
    normalized_claim = normalize_claim(claim)
    if not normalized_claim:
        return False
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    if normalize_claim(lines[0]) != normalized_claim:
        return False
    normalized_second = normalize_claim(lines[1])
    if not normalized_second or normalized_second == normalized_claim:
        return False
    return True


def withheld_reply(claim):
    head = claim.strip() if isinstance(claim, str) else ""
    return head + "\n" + _WITHHELD_REPLY_LINE


def withheld_recall(phrase):
    head = phrase if isinstance(phrase, str) else ""
    return head + "\n" + _WITHHELD_RECALL_LINE


def pick_checked_attempt(first, second, predicate, fallback):
    def usable(text):
        if not isinstance(text, str) or text == "":
            return False
        return bool(predicate(text))

    if usable(first):
        return first, "model"
    if usable(second):
        return second, "retry"
    return fallback, "withheld"


def claim_from_topic(info):
    if not isinstance(info, dict):
        return ""
    if info.get("topic_source") != "curiosity_engine":
        return ""
    topic = info.get("topic")
    if not isinstance(topic, str):
        return ""
    if "\n" in topic or "\r" in topic:
        return ""
    stripped = topic.strip()
    if not stripped or len(stripped) > CLAIM_MAX_CHARS:
        return ""
    return stripped


def decide_initiator_action(state):
    if not isinstance(state, dict) or not state:
        return "new_claim"
    status = state.get("status")
    if status is None or status == "" or status == "idle":
        return "new_claim"
    if status == "awaiting_recall":
        phrase = state.get("marked_phrase")
        if isinstance(phrase, str) and 1 <= len(phrase.strip()) <= PHRASE_MAX_CHARS:
            return "recall"
        return "expire_unmet"
    return "expire_unmet"


def _usable_mark(phrase, text, claim):
    if not isinstance(phrase, str):
        return False
    stripped = phrase.strip()
    if not stripped or len(stripped) > PHRASE_MAX_CHARS:
        return False
    if normalize_claim(stripped) == normalize_claim(claim):
        return False
    return contains_sentence(text, phrase)


def accept_partner_mark(state, incoming, text):
    if not isinstance(state, dict) or not isinstance(incoming, dict):
        return None
    if state.get("status") != "awaiting_reply":
        return None
    claim = state.get("claim")
    if not isinstance(claim, str) or not claim.strip():
        return None
    role = incoming.get("claim_role", "")
    if not isinstance(role, str):
        role = ""
    if role not in ("", "reply"):
        return None
    if not isinstance(text, str):
        text = ""

    our_id = state.get("claim_id")
    their_id = incoming.get("claim_id")
    id_match = (
        isinstance(our_id, str)
        and our_id != ""
        and isinstance(their_id, str)
        and their_id == our_id
    )
    our_conv = state.get("conversation_id")
    their_conv = incoming.get("conversation_id")
    same_conversation = (
        isinstance(our_conv, str)
        and our_conv != ""
        and isinstance(their_conv, str)
        and their_conv == our_conv
    )
    shaped = reply_is_shaped(text, claim)
    if not id_match and not (same_conversation and shaped):
        return None

    chosen = None
    data_phrase = incoming.get("marked_phrase")
    if _usable_mark(data_phrase, text, claim):
        chosen = data_phrase.strip()
    elif shaped:
        line = second_line(text)
        if _usable_mark(line, text, claim):
            chosen = line.strip()
    if chosen is None:
        return None

    updated = dict(state)
    updated["status"] = "awaiting_recall"
    updated["marked_phrase"] = chosen.strip()
    return updated


def reply_user_message(claim, letter):
    claim_text = claim if isinstance(claim, str) else ""
    letter_text = letter if isinstance(letter, str) else ""
    return (
        "Claim:\n"
        + claim_text
        + "\n\nTheir letter:\n"
        + letter_text
        + "\n\nThe first line of your reply is the claim exactly, alone. "
        "The second line is one reason it fails or one new sentence. "
        "Then you may continue."
    )


def recall_user_message(claim, phrase):
    claim_text = claim if isinstance(claim, str) else ""
    phrase_text = phrase if isinstance(phrase, str) else ""
    return (
        "Claim:\n"
        + claim_text
        + "\n\nYour letter must include this exact sentence from their reply, unchanged:\n"
        + phrase_text
    )


def public_claim_record(record):
    if not isinstance(record, dict):
        return {}
    out = {}
    for key, value in record.items():
        if key == "secret":
            continue
        if key == "text" and isinstance(value, str) and len(value) > LETTER_MAX_CHARS:
            value = value[:LETTER_MAX_CHARS]
        elif key == "claim" and isinstance(value, str) and len(value) > CLAIM_MAX_CHARS:
            value = value[:CLAIM_MAX_CHARS]
        elif key == "marked_phrase" and isinstance(value, str) and len(value) > PHRASE_MAX_CHARS:
            value = value[:PHRASE_MAX_CHARS]
        out[key] = value
    return out


def send_counts_as_in_flight(result):
    return isinstance(result, dict) and result.get("status") in ("delivered", "queued")
