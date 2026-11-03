#!/usr/bin/env python3
"""Prove the claim helpers and the three call sites without calling Echo.

Does not import echo_messaging, liveness_ledger, or any model path.
Does not write under memory/.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import app.sync.echo_claims as claims

FAILURES = []


def check(label, ok, detail=""):
    status = "OK  " if ok else "FAIL"
    print(f"[{status}] {label}")
    if not ok:
        FAILURES.append(f"{label}: {detail}")


def _call_name(node):
    if not isinstance(node, ast.Call):
        return None
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _module_fn(tree, name):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _calls_outside_nested(fn_node, name):
    count = 0

    def walk(node, nested):
        nonlocal count
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.iter_child_nodes(node):
                walk(child, True)
            return
        if isinstance(node, ast.Call) and _call_name(node) == name and not nested:
            count += 1
        for child in ast.iter_child_nodes(node):
            walk(child, nested)

    if fn_node is None:
        return 0
    for child in ast.iter_child_nodes(fn_node):
        walk(child, False)
    return count


def _calls_anywhere(fn_node, name):
    if fn_node is None:
        return 0
    count = 0
    for sub in ast.walk(fn_node):
        if isinstance(sub, ast.Call) and _call_name(sub) == name:
            count += 1
    return count


CLAIM = "The invented claim sentence stands alone."
SECOND = "A second sentence adds one reason it fails."
GOOD = CLAIM + "\n" + SECOND
WITHHELD_REPLY = "The essay was withheld because it did not repeat the claim."
WITHHELD_RECALL = "The essay was withheld because it did not include the partner's sentence."


def main():
    check(
        "importing echo_claims does not load echo_messaging",
        "app.sync.echo_messaging" not in sys.modules,
    )

    claims_path = os.path.join(ROOT, "app", "sync", "echo_claims.py")
    messaging_path = os.path.join(ROOT, "app", "sync", "echo_messaging.py")
    claims_src = open(claims_path, encoding="utf-8").read()
    messaging_src = open(messaging_path, encoding="utf-8").read()
    claims_tree = ast.parse(claims_src)
    messaging_tree = ast.parse(messaging_src)
    check("both modules parse", True)

    for banned in ("echo_query", "requests", "sync_protocol"):
        check(
            f"echo_claims source has no {banned}",
            banned not in claims_src,
            "found banned text",
        )
    import_nodes = [
        node for node in ast.walk(claims_tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    check("echo_claims has no import statements", import_nodes == [], str(len(import_nodes)))

    check("normalize collapses inner spaces", claims.normalize_claim("A  square") == "A square")
    check("normalize rejects non-strings", claims.normalize_claim(None) == "")
    check(
        "contains_sentence ignores spacing",
        claims.contains_sentence("A  square", "A square") is True,
    )
    check("empty needle fails", claims.contains_sentence("hello", "") is False)
    check("blank needle fails", claims.contains_sentence("hello", "   ") is False)
    check("none needle fails", claims.contains_sentence("hello", None) is False)
    check("none haystack fails", claims.contains_sentence(None, "hello") is False)

    check("shaped reply passes", claims.reply_is_shaped(GOOD, CLAIM) is True)
    check(
        "buried claim fails",
        claims.reply_is_shaped("A preface comes first.\n" + GOOD, CLAIM) is False,
    )
    check("one-line claim fails", claims.reply_is_shaped(CLAIM, CLAIM) is False)
    check(
        "second line equal to the claim fails",
        claims.reply_is_shaped(CLAIM + "\n" + CLAIM, CLAIM) is False,
    )
    check("non-string text fails shape", claims.reply_is_shaped(None, CLAIM) is False)
    spaced_second = "A  second sentence adds one reason it fails."
    check(
        "second_line keeps internal spaces",
        claims.second_line(CLAIM + "\n  " + spaced_second + "  ") == spaced_second,
    )

    reply = claims.withheld_reply("  " + CLAIM + "  ")
    check(
        "withheld reply uses the exact sentence",
        reply == CLAIM + "\n" + WITHHELD_REPLY,
        reply,
    )
    check("withheld reply is shaped", claims.reply_is_shaped(reply, CLAIM) is True)
    check(
        "withheld reply second line is the exact sentence",
        claims.second_line(reply) == WITHHELD_REPLY,
    )
    phrase_raw = "  partner sentence stays  "
    recall = claims.withheld_recall(phrase_raw)
    check(
        "withheld recall keeps the phrase and the exact sentence",
        recall == phrase_raw + "\n" + WITHHELD_RECALL,
        recall,
    )
    check(
        "withheld recall contains the phrase",
        claims.contains_sentence(recall, phrase_raw) is True,
    )
    check(
        "withheld recall of a non-string is the sentence alone",
        claims.withheld_recall(None) == "\n" + WITHHELD_RECALL,
    )

    seen = []

    def _pred(text):
        seen.append(text)
        return text == "second ok"

    seen.clear()
    text, how = claims.pick_checked_attempt("", None, _pred, "fallback")
    check("empty and none skip the predicate", seen == [] and how == "withheld" and text == "fallback")
    seen.clear()
    text, how = claims.pick_checked_attempt(None, "", _pred, "fallback")
    check("none then empty skip the predicate", seen == [] and how == "withheld")

    def _pred_false(text):
        seen.append(text)
        return False

    seen.clear()
    text, how = claims.pick_checked_attempt("   ", None, _pred_false, "fallback")
    check(
        "whitespace-only still reaches the predicate",
        seen == ["   "] and how == "withheld" and text == "fallback",
        str(seen),
    )

    def _pred_true(text):
        seen.append(text)
        return True

    seen.clear()
    text, how = claims.pick_checked_attempt("first ok", "second", _pred_true, "fallback")
    check(
        "first success does not test the second",
        seen == ["first ok"] and how == "model" and text == "first ok",
        str(seen),
    )
    seen.clear()
    text, how = claims.pick_checked_attempt("nope", "second ok", _pred, "fallback")
    check(
        "retry wins when the first fails",
        how == "retry" and text == "second ok" and seen == ["nope", "second ok"],
        f"{how} {text} {seen}",
    )
    text, how = claims.pick_checked_attempt("nope", "also nope", _pred, GOOD)
    check(
        "both failures return the fallback",
        how == "withheld" and text == GOOD,
        f"{how} {text}",
    )

    decisions = [
        (None, "new_claim"),
        ({}, "new_claim"),
        ({"status": None}, "new_claim"),
        ({"status": ""}, "new_claim"),
        ({"status": "idle"}, "new_claim"),
        ({"status": "awaiting_reply", "claim": CLAIM}, "expire_unmet"),
        ({"status": "awaiting_recall", "marked_phrase": SECOND}, "recall"),
        ({"status": "awaiting_recall", "marked_phrase": "  " + SECOND + "  "}, "recall"),
        ({"status": "awaiting_recall"}, "expire_unmet"),
        ({"status": "awaiting_recall", "marked_phrase": ""}, "expire_unmet"),
        ({"status": "awaiting_recall", "marked_phrase": "x" * 501}, "expire_unmet"),
        ({"status": "unknown-status"}, "expire_unmet"),
        ("nope", "new_claim"),
    ]
    for state, expected in decisions:
        got = claims.decide_initiator_action(state)
        check(f"decide {state!r} -> {expected}", got == expected, got)

    base = {
        "status": "awaiting_reply",
        "claim": CLAIM,
        "claim_id": "invented-id",
        "conversation_id": "invented-conv",
    }

    def accept(state, incoming, text):
        snapshot = dict(state)
        updated = claims.accept_partner_mark(state, incoming, text)
        mutated = state != snapshot
        return updated, mutated

    incoming = {
        "claim_role": "reply",
        "claim_id": "invented-id",
        "conversation_id": "invented-conv",
        "claim": CLAIM,
        "marked_phrase": SECOND,
    }
    updated, mutated = accept(dict(base), incoming, GOOD)
    check(
        "id plus phrase in the text is accepted",
        (not mutated) and isinstance(updated, dict)
        and updated.get("status") == "awaiting_recall"
        and updated.get("marked_phrase") == SECOND,
        str(updated),
    )

    essay = "An essay that never repeats the partner sentence."
    phantom = dict(incoming)
    phantom["marked_phrase"] = "A phantom sentence is not in the essay."
    updated, mutated = accept(dict(base), phantom, essay)
    check("data-only phrase returns none", updated is None and not mutated)

    for role in ("initiate", "recall"):
        bad = dict(incoming)
        bad["claim_role"] = role
        updated, mutated = accept(dict(base), bad, GOOD)
        check(f"role {role} is rejected", updated is None and not mutated)

    idle = dict(base)
    idle["status"] = "idle"
    updated, mutated = accept(idle, incoming, GOOD)
    check("idle returns none", updated is None and not mutated)

    no_id = {
        "claim_role": "reply",
        "conversation_id": "invented-conv",
        "claim": CLAIM,
    }
    updated, mutated = accept(dict(base), no_id, GOOD)
    check(
        "same conversation and a shaped reply accept the second line",
        (not mutated) and isinstance(updated, dict) and updated.get("marked_phrase") == SECOND,
        str(updated),
    )
    updated, mutated = accept(dict(base), no_id, essay)
    check("same conversation without the shape returns none", updated is None and not mutated)

    long_phrase = "y" * 501
    long_in = dict(incoming)
    long_in["marked_phrase"] = long_phrase
    updated, mutated = accept(dict(base), long_in, essay)
    check("a 501-character phrase with no short second line is rejected", updated is None)

    updated, mutated = accept(dict(base), long_in, GOOD)
    check(
        "a 501-character phrase falls through to the short second line",
        isinstance(updated, dict) and updated.get("marked_phrase") == SECOND,
        str(updated),
    )

    same = dict(incoming)
    same["marked_phrase"] = CLAIM
    updated, mutated = accept(dict(base), same, GOOD)
    check(
        "a phrase equal to the claim falls through to the second line",
        isinstance(updated, dict) and updated.get("marked_phrase") == SECOND,
        str(updated),
    )

    unshaped = "Not the claim line.\n" + SECOND
    loose = dict(incoming)
    loose["marked_phrase"] = SECOND
    updated, mutated = accept(dict(base), loose, unshaped)
    check(
        "an id match does not require the shaped reply when the phrase is in the text",
        isinstance(updated, dict) and updated.get("marked_phrase") == SECOND,
        str(updated),
    )

    absent = dict(incoming)
    del absent["claim_role"]
    updated, mutated = accept(dict(base), absent, GOOD)
    check(
        "a missing role with an id match is accepted",
        isinstance(updated, dict) and updated.get("marked_phrase") == SECOND,
    )
    updated, _mutated = claims.accept_partner_mark("nope", incoming, GOOD), False
    check("a non-dict state returns none", updated is None)
    updated = claims.accept_partner_mark(dict(base), "nope", GOOD)
    check("a non-dict incoming returns none", updated is None)
    empty_claim = dict(base)
    empty_claim["claim"] = ""
    check(
        "an empty claim returns none",
        claims.accept_partner_mark(empty_claim, incoming, GOOD) is None,
    )

    info_ok = {"topic_source": "curiosity_engine", "topic": "  alpha  beta  "}
    check(
        "curiosity topic keeps internal spaces",
        claims.claim_from_topic(info_ok) == "alpha  beta",
        claims.claim_from_topic(info_ok),
    )
    check(
        "a 1000-character curiosity topic is kept",
        claims.claim_from_topic({"topic_source": "curiosity_engine", "topic": "q" * 1000}) == "q" * 1000,
    )
    rejected = [
        {"topic_source": "self_model", "topic": "hello"},
        {"topic_source": "none", "topic": "hello"},
        {"topic_source": "curiosity_engine", "topic": ""},
        {"topic_source": "curiosity_engine", "topic": "   "},
        {"topic_source": "curiosity_engine", "topic": "has\nnewline"},
        {"topic_source": "curiosity_engine", "topic": "has\rreturn"},
        {"topic_source": "curiosity_engine", "topic": "q" * 1001},
        {"topic_source": "curiosity_engine", "topic": 5},
        "nope",
        None,
    ]
    for item in rejected:
        got = claims.claim_from_topic(item)
        check(f"claim_from_topic rejects {item!r}", got == "", got)

    record = {
        "secret": "nope",
        "text": "t" * 12001,
        "claim": "c" * 1001,
        "marked_phrase": "p" * 501,
        "claim_id": "keep-me",
        "note": "n" * 20,
    }
    public = claims.public_claim_record(record)
    check("public record drops secret", "secret" not in public)
    check("public record caps the letter", len(public.get("text", "")) == 12000)
    check("public record caps the claim", len(public.get("claim", "")) == 1000)
    check("public record caps the phrase", len(public.get("marked_phrase", "")) == 500)
    check("public record keeps other keys", public.get("claim_id") == "keep-me" and public.get("note") == "n" * 20)
    check("public record of a non-dict is empty", claims.public_claim_record(None) == {})
    check("public record of a string is empty", claims.public_claim_record("x") == {})

    check("delivered counts as in flight", claims.send_counts_as_in_flight({"status": "delivered"}) is True)
    check("queued counts as in flight", claims.send_counts_as_in_flight({"status": "queued"}) is True)
    check("blocked does not count", claims.send_counts_as_in_flight({"status": "blocked"}) is False)
    check("error does not count", claims.send_counts_as_in_flight({"status": "error"}) is False)
    check("a bare string does not count", claims.send_counts_as_in_flight("delivered") is False)
    check("none does not count", claims.send_counts_as_in_flight(None) is False)

    asked = claims.reply_user_message(CLAIM, "Their essay body.")
    check("reply prompt names the claim", "Claim:" in asked and CLAIM in asked)
    check("reply prompt names their letter", "Their letter:" in asked and "Their essay body." in asked)
    check(
        "reply prompt states the two-line rule",
        "The first line of your reply is the claim exactly, alone." in asked,
    )
    recall_prompt = claims.recall_user_message(CLAIM, SECOND)
    check(
        "recall prompt requires the exact sentence",
        "Your letter must include this exact sentence from their reply, unchanged:" in recall_prompt
        and SECOND in recall_prompt
        and CLAIM in recall_prompt,
    )

    reply_fn = _module_fn(messaging_tree, "_generate_and_send_reply")
    receive_fn = _module_fn(messaging_tree, "receive_message")
    reflect_fn = _module_fn(messaging_tree, "maybe_send_reflection")
    outside = _calls_outside_nested(reply_fn, "reply_is_shaped")
    accept_count = _calls_anywhere(receive_fn, "accept_partner_mark")
    decide_count = _calls_anywhere(reflect_fn, "decide_initiator_action")
    check(
        "reply_is_shaped is called outside the nested predicate",
        outside >= 1,
        str(outside),
    )
    check("receive_message calls accept_partner_mark at least twice", accept_count >= 2, str(accept_count))
    check(
        "maybe_send_reflection calls decide_initiator_action",
        decide_count >= 1,
        str(decide_count),
    )

    sibling = ast.parse(
        "def helper():\n"
        "    accept_partner_mark({}, {}, '')\n"
        "    decide_initiator_action({})\n"
        "    reply_is_shaped('', '')\n"
        "def maybe_send_reflection():\n"
        "    return None\n"
        "def receive_message(payload):\n"
        "    return helper()\n"
        "def _generate_and_send_reply():\n"
        "    return None\n"
    )
    check(
        "a sibling helper call is not counted as receive_message",
        _calls_anywhere(_module_fn(sibling, "receive_message"), "accept_partner_mark") == 0,
    )
    nested_only = ast.parse(
        "def _generate_and_send_reply():\n"
        "    def inner():\n"
        "        reply_is_shaped('', '')\n"
        "    return inner()\n"
    )
    check(
        "a nested-only reply_is_shaped call fails the outside-nested check",
        _calls_outside_nested(_module_fn(nested_only, "_generate_and_send_reply"), "reply_is_shaped") == 0,
    )

    print()
    if FAILURES:
        print(f"=== {len(FAILURES)} FAILURE(S) ===")
        for item in FAILURES:
            print(" -", item)
        return 1
    print(f"=== All echo claim checks passed ({len(FAILURES)} failures) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
