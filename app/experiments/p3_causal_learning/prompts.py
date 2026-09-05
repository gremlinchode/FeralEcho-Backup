"""
Formation-text and probe-question construction for P3-CAUSAL-LEARNING.

DESIGN NOTE, distinguishing this from the Learning Investigation's own
trait/preference task: Formation here states the abstract STIMULUS-
RESPONSE POLICY only ("when you see marker X, prepend tag Y") and
NEVER demonstrates it against any specific example question. This
means every later probe is a genuine application of a never-directly-
demonstrated behavior -- there is no "SEEN = directly recalled example"
case at all in this design, unlike the trait/preference task's
SEEN/RECOMBINED split. Instead, the standard/generalization split
tests whether the policy transfers from an ordinary carrier-question
domain to a starkly different one (a real, if secondary, L3 check),
while the primary A/B/C comparison (mission's "key test") is applied
uniformly across a standard probe per rule.

The marker is embedded in each carrier question as if it were a
person's nickname/name ("My friend {marker} wants to know: ..."),
letting it sit naturally in ANY topic-agnostic carrier question without
requiring per-topic integration -- deliberately simple and robust,
avoiding a more elaborate embedding scheme that could itself introduce
wording confounds.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from app.experiments.p3_causal_learning.world_gen import P3World, Rule

_RULE_STATEMENT_TEMPLATES = [
    "Here is a response rule for this conversation: if a question contains the name \"{marker}\", "
    "begin your answer with the word \"{tag}\" before addressing the actual question.",
    "One rule to follow from now on: whenever a question mentions someone named \"{marker}\", "
    "start your reply with \"{tag}\" first, then answer normally.",
    "A formatting instruction: if \"{marker}\" is mentioned anywhere in a question, your answer "
    "should open with \"{tag}\" before the rest of your response.",
]

# Standard carrier-question pool: ordinary, topic-agnostic questions with
# no relationship to each other or to the taught rules.
_STANDARD_CARRIER_QUESTIONS = [
    "what's a good way to organize a small bookshelf?",
    "how many days are in a leap year?",
    "what's a common reason people go for a walk in the morning?",
    "what's a simple way to keep cut flowers fresh longer?",
    "why do some people prefer tea over coffee?",
    "what's a good rule of thumb for packing a suitcase?",
    "how do you politely end a phone call?",
    "what's a quick way to check if an avocado is ripe?",
]

# A deliberately different-domain carrier pool, used only for the
# secondary L3 generalization check (never for the primary A/B/C test).
_GENERALIZATION_CARRIER_QUESTIONS = [
    "if a train leaves at 3pm and travels for 2 hours, what time does it arrive?",
    "what's the next number in the sequence 2, 4, 8, 16?",
    "if you flip a fair coin twice, what's the chance of getting two heads?",
]

_EMBED_TEMPLATES = [
    "My friend {marker} wants to know: {question}",
    "{marker} just asked me: {question}",
    "A person named {marker} had this question: {question}",
]


def _pick(items: List[str], rng: random.Random) -> str:
    return rng.choice(items)


def build_formation_text(world: P3World) -> str:
    """Deterministic given the world. States each rule abstractly, in a
    randomized order, using a randomly-chosen phrasing per rule -- never
    demonstrates the behavior against any concrete example question."""
    rng = random.Random(world.seed * 7919 + 1)  # distinct offset from world_gen's own seeding
    statements = [
        _pick(_RULE_STATEMENT_TEMPLATES, rng).format(marker=r.marker, tag=r.tag)
        for r in world.rules
    ]
    rng.shuffle(statements)
    return " ".join(statements)


@dataclass
class Probe:
    text: str
    rule_index: int
    marker: str
    correct_tag: str
    other_tags: List[str]   # every OTHER rule's tag -- used by scoring to detect cross-rule contamination
    category: str            # "standard" | "generalization"


def build_probe(world: P3World, rule_index: int, category: str, seed: int) -> Probe:
    rng = random.Random(seed)
    rule = world.rules[rule_index]
    pool = _STANDARD_CARRIER_QUESTIONS if category == "standard" else _GENERALIZATION_CARRIER_QUESTIONS
    question = _pick(pool, rng)
    embed_template = _pick(_EMBED_TEMPLATES, rng)
    text = embed_template.format(marker=rule.marker, question=question)
    other_tags = [r.tag for i, r in enumerate(world.rules) if i != rule_index]
    return Probe(
        text=text, rule_index=rule_index, marker=rule.marker, correct_tag=rule.tag,
        other_tags=other_tags, category=category,
    )


def build_all_standard_probes(world: P3World, base_seed: int) -> List[Probe]:
    """One standard probe per rule -- the primary A/B/C measurement set."""
    return [
        build_probe(world, i, "standard", seed=base_seed + i)
        for i in range(len(world.rules))
    ]


def build_generalization_probe(world: P3World, base_seed: int) -> Probe:
    """A single, secondary, exploratory L3 check -- always targets rule 0,
    since the point is to test domain transfer, not to add more primary
    measurements. Never conflated with the primary A/B/C comparison."""
    return build_probe(world, 0, "generalization", seed=base_seed + 1000)


def verify_no_rule_leakage(probe: Probe) -> Optional[str]:
    """Mission control requirement: the probe text itself must never
    contain the correct_tag, or any other rule's tag, or the word
    "rule"/"format" (which could hint that this is a rule-following test
    rather than an ordinary question). Returns None if clean, else a
    description of the leak."""
    lowered = probe.text.lower()
    if probe.correct_tag.lower() in lowered:
        return f"LEAK: probe text contains the correct tag {probe.correct_tag!r}"
    for t in probe.other_tags:
        if t.lower() in lowered:
            return f"LEAK: probe text contains another rule's tag {t!r}"
    if "rule" in lowered or "format" in lowered or "instruction" in lowered:
        return "LEAK: probe text contains meta-language hinting this is a rule-following test"
    if probe.marker.lower() not in lowered:
        return f"CONSTRUCTION ERROR: probe text does not contain its own marker {probe.marker!r}"
    return None
