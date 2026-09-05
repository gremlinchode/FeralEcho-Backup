#!/usr/bin/env python3
"""
Mock-test suite for app/experiments/p3_causal_learning/ (P3-CAUSAL-LEARNING
design gate). Follows this project's established check() convention.

NO LIVE MODEL CALL ANYWHERE IN THIS FILE. Every test exercises pure
functions (world_gen, prompts, scoring) against synthetic, hand-
constructed strings -- this is the "mock-test apparatus before freeze"
step the P3 mission's item 9 requires, performed exactly as the
Learning Investigation's own pre-registration gate did for its
sibling task, and just as strictly separated from any live call.
"""

import sys

sys.path.insert(0, ".")

_PASS = 0
_FAIL = 0


def check(name, actual, expected, evidence=""):
    global _PASS, _FAIL
    ok = actual == expected
    tag = "OK  " if ok else "FAIL"
    print(f"[{tag}] {name}: expected={expected!r} got={actual!r}")
    if evidence:
        print(f"       {evidence}")
    if ok:
        _PASS += 1
    else:
        _FAIL += 1
    return ok


def check_true(name, condition, evidence=""):
    return check(name, bool(condition), True, evidence)


from app.experiments.p3_causal_learning import world_gen, prompts, scoring  # noqa: E402
from app.experiments.p3_causal_learning.scoring import TagVerdict, EpistemicClass  # noqa: E402

# ---------------------------------------------------------------------------
# world_gen: determinism, screening, structural correctness
# ---------------------------------------------------------------------------

print("--- world_gen: determinism ---")
w1a = world_gen.generate_world(42)
w1b = world_gen.generate_world(42)
check("same seed produces identical world", w1a.to_dict(), w1b.to_dict())

w2 = world_gen.generate_world(43)
check_true("different seed produces a different world", w1a.world_hash != w2.world_hash)

print("\n--- world_gen: screening ---")
check_true("system dictionary loaded", world_gen.DICTIONARY_AVAILABLE)
import random as _random  # noqa: E402
_rng = _random.Random(0)
_collisions = [
    w for w in (world_gen.generate_invented_word(_rng) for _ in range(500))
    if w.lower() in world_gen._SYSTEM_DICTIONARY
]
check("500 generated words: zero real-dictionary collisions", len(_collisions), 0)

print("\n--- world_gen: structural correctness ---")
w = world_gen.generate_world(7, n_rules=3)
check("3 rules generated", len(w.rules), 3)
markers = [r.marker for r in w.rules]
tags = [r.tag for r in w.rules]
check("no duplicate markers", len(markers), len(set(markers)))
check("no duplicate tags", len(tags), len(set(tags)))
check_true("no marker equals its own tag", all(r.marker != r.tag for r in w.rules))
check("world_hash reproducible", world_gen.generate_world(7, n_rules=3).world_hash, w.world_hash)


# ---------------------------------------------------------------------------
# prompts: formation coverage, leakage checks (positive + deliberately broken)
# ---------------------------------------------------------------------------

print("\n--- prompts: formation text coverage ---")
formation = prompts.build_formation_text(w)
for r in w.rules:
    check_true(f"formation states marker {r.marker!r}", r.marker in formation)
    check_true(f"formation states tag {r.tag!r}", r.tag in formation)

print("\n--- prompts: leakage checks ---")
probes = prompts.build_all_standard_probes(w, base_seed=100)
check("3 standard probes built", len(probes), 3)
for p in probes:
    check(f"leak check clean for rule {p.rule_index} probe", prompts.verify_no_rule_leakage(p), None)

gen_probe = prompts.build_generalization_probe(w, base_seed=100)
check("generalization probe leak check clean", prompts.verify_no_rule_leakage(gen_probe), None)
check("generalization probe targets rule 0", gen_probe.rule_index, 0)
check_true("generalization probe uses the generalization carrier pool",
           gen_probe.text.split(":")[-1].strip() in prompts._GENERALIZATION_CARRIER_QUESTIONS,
           evidence=gen_probe.text)

# Deliberately broken probe: contains the correct tag itself (a real leak)
_bad_probe = prompts.Probe(
    text=f"{w.rules[0].marker} asked, and by the way the answer always starts with {w.rules[0].tag}: what time is it?",
    rule_index=0, marker=w.rules[0].marker, correct_tag=w.rules[0].tag,
    other_tags=[r.tag for r in w.rules[1:]], category="standard",
)
check_true("leak check catches a probe that reveals its own correct tag",
           prompts.verify_no_rule_leakage(_bad_probe) is not None)

_meta_leak_probe = prompts.Probe(
    text=f"{w.rules[0].marker} asked about the rule: what time is it?",
    rule_index=0, marker=w.rules[0].marker, correct_tag=w.rules[0].tag,
    other_tags=[r.tag for r in w.rules[1:]], category="standard",
)
check_true("leak check catches meta-language ('the rule') in a probe",
           prompts.verify_no_rule_leakage(_meta_leak_probe) is not None)


# ---------------------------------------------------------------------------
# scoring: injected-known-result tests (the core apparatus validity check)
# ---------------------------------------------------------------------------

print("\n--- scoring: injected-known-result tests ---")
p0 = probes[0]

# 1. Clean, correct application: tag at the very start, no contamination
r1 = f"{p0.correct_tag}. Here's my answer to your actual question: I'd suggest sorting by height."
res1 = scoring.score_probe_response(r1, p0)
check("clean correct application -> CORRECT", res1["tag_verdict"], TagVerdict.CORRECT.value)

# 2. Correct + justified (references the marker as the reason)
r2 = f"{p0.correct_tag} -- since {p0.marker.lower()} was mentioned, I'll start with that. Now, to answer: sort by height."
res2 = scoring.score_probe_response(r2, p0)
check("correct + justified -> CORRECT / correct_justified",
      (res2["tag_verdict"], res2["epistemic_class"]), (TagVerdict.CORRECT.value, EpistemicClass.CORRECT_JUSTIFIED.value))

# 3. Correct + unsupported (no justification given)
r3 = f"{p0.correct_tag}. I'd suggest sorting books by height for a small bookshelf."
res3 = scoring.score_probe_response(r3, p0)
check("correct + unsupported -> CORRECT / correct_unsupported",
      (res3["tag_verdict"], res3["epistemic_class"]), (TagVerdict.CORRECT.value, EpistemicClass.CORRECT_UNSUPPORTED.value))

# 4. Wrong tag applied (a different rule's tag instead)
wrong_tag = p0.other_tags[0]
r4 = f"{wrong_tag}. I'd suggest sorting books by height."
res4 = scoring.score_probe_response(r4, p0)
check("a different rule's tag applied -> WRONG_TAG", res4["tag_verdict"], TagVerdict.WRONG_TAG.value)

# 5. No tag at all
r5 = "I'd suggest sorting books by height, color, or genre -- whatever's easiest to browse."
res5 = scoring.score_probe_response(r5, p0)
check("no tag anywhere -> NO_TAG", res5["tag_verdict"], TagVerdict.NO_TAG.value)

# 6. Correct tag present but buried mid-response (not a genuine prefix application)
r6 = ("I'd suggest sorting books by height, color, or genre. By the way, does the word "
      f"{p0.correct_tag} mean anything special? Anyway, whatever's easiest to browse.")
res6 = scoring.score_probe_response(r6, p0)
check("correct tag present but buried mid-response -> NO_TAG (not counted as the taught prefix behavior)",
      res6["tag_verdict"], TagVerdict.NO_TAG.value)

# 7. Correct tag + contamination (another rule's tag also appears)
r7 = f"{p0.correct_tag}. Sort by height. (Also, {wrong_tag} is a fun word.)"
res7 = scoring.score_probe_response(r7, p0)
check("correct tag + another rule's tag present -> CORRECT_WITH_CONTAMINATION",
      res7["tag_verdict"], TagVerdict.CORRECT_WITH_CONTAMINATION.value)

# 8. Empty response
res8 = scoring.score_probe_response("", p0)
check("empty response -> UNKNOWN_AMBIGUOUS", res8["tag_verdict"], TagVerdict.UNKNOWN_AMBIGUOUS.value)

# 9. Uncertain/abstain (hedging language, regardless of tag outcome)
r9 = f"I'm not sure if a specific format was expected here, but I'd suggest sorting by height. {p0.correct_tag}?"
res9 = scoring.score_probe_response(r9, p0)
check("hedging language present -> uncertain_abstain (epistemic), regardless of tag outcome",
      res9["epistemic_class"], EpistemicClass.UNCERTAIN_ABSTAIN.value)

# 10. Incorrect + confident (no tag, no hedging)
r10 = "Sort by height, definitely the best approach for a small bookshelf."
res10 = scoring.score_probe_response(r10, p0)
check("no tag, no hedging -> incorrect_confident",
      res10["epistemic_class"], EpistemicClass.INCORRECT_CONFIDENT.value)

# 11. Refusal / non-answer
r11 = "I don't understand the question, could you clarify what you mean?"
res11 = scoring.score_probe_response(r11, p0)
check("refusal language -> UNKNOWN_AMBIGUOUS", res11["tag_verdict"], TagVerdict.UNKNOWN_AMBIGUOUS.value)


print(f"\n=== {_PASS} passed, {_FAIL} failed ===")
if _FAIL:
    sys.exit(1)
