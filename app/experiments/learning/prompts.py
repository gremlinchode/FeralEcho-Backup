"""
Formation-text and test-prompt construction for the Echo Learning
Investigation's micro-world task (Phase 3/5/6).

Two independent concerns, kept in separate functions per this project's
own "separate measurement from interpretation" / "raw data survives
interpretation" discipline (see the preference-provenance package's
choice_parser.py for the precedent):

  - build_formation_text(): the one-shot teaching narrative Echo reads
    during Formation. Presents the abstract rule once, then a fact for
    every SEEN and RECOMBINED entity (trait-possession only for
    RECOMBINED entities -- their preference is never directly stated).
    NOVEL entities are never mentioned here at all.

  - build_test_prompt(): a forced-choice question about one entity's
    preference, with a freshly randomized A/B label mapping reused
    directly from the ALREADY-FROZEN, ALREADY-VALIDATED
    preference-provenance package's harness.randomize_label_mapping()
    (imported read-only, never modified -- per this investigation's own
    "do not modify existing preference experiment... parsers, or frozen
    artifacts" constraint). For NOVEL entities, the test prompt itself
    must additionally state the entity's trait membership, since
    Formation never did.

WORDING CONTROLS (Phase 6): each fact/question type has 2-3 paraphrase
variants, selected deterministically from the world's own seed (not
randomly re-rolled per call) so a given world always produces the same
formation text and the same test prompts -- reproducible, but not
uniform across different worlds (guards against a single fixed phrasing
becoming a shortcut).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from app.experiments.learning.world_gen import MicroWorld
from app.experiments.preference_provenance.harness import randomize_label_mapping

# --- Paraphrase templates -----------------------------------------------

_RULE_TEMPLATES = [
    "Here is a rule about an invented world: creatures with the {trait} trait "
    "tend to prefer {sub_with} over {sub_without}. Creatures without the {trait} "
    "trait tend to prefer {sub_without} over {sub_with}.",
    "In this invented world, there's a pattern: any creature that has {trait} "
    "generally favors {sub_with} rather than {sub_without}. Any creature that "
    "lacks {trait} generally favors {sub_without} rather than {sub_with}.",
    "One thing to know about this invented world: {trait} creatures usually "
    "lean toward {sub_with} instead of {sub_without}, while non-{trait} "
    "creatures usually lean toward {sub_without} instead of {sub_with}.",
]

_TRAIT_FACT_TEMPLATES_POSITIVE = [
    "{entity} has the {trait} trait.",
    "{entity} is one of the creatures with {trait}.",
    "Among these creatures, {entity} has {trait}.",
]
_TRAIT_FACT_TEMPLATES_NEGATIVE = [
    "{entity} does not have the {trait} trait.",
    "{entity} is one of the creatures without {trait}.",
    "Among these creatures, {entity} lacks {trait}.",
]

_SEEN_PREFERENCE_TEMPLATES = [
    "{entity} prefers {substance}.",
    "{entity}'s preference is {substance}.",
    "Between the two, {entity} prefers {substance}.",
]

_TEST_QUESTION_TEMPLATES = [
    "Between {opt_a} and {opt_b}, which would {entity} prefer? Answer with the letter and a brief reason.",
    "Which of these would {entity} most likely prefer: {opt_a} or {opt_b}? Answer with the letter and a brief reason.",
    "Thinking about {entity} specifically -- {opt_a} or {opt_b} -- which one fits better? Answer with the letter and a brief reason.",
]

_NOVEL_INTRO_TEMPLATES_POSITIVE = [
    "There is a creature called {entity} that has the {trait} trait. ",
    "Consider a new creature, {entity}, which has {trait}. ",
    "{entity} is a creature with the {trait} trait. ",
]
_NOVEL_INTRO_TEMPLATES_NEGATIVE = [
    "There is a creature called {entity} that does not have the {trait} trait. ",
    "Consider a new creature, {entity}, which lacks {trait}. ",
    "{entity} is a creature without the {trait} trait. ",
]


def _pick(templates: List[str], rng: random.Random) -> str:
    return rng.choice(templates)


def build_formation_text(world: MicroWorld) -> str:
    """Deterministic given the world (uses a rng seeded from world.seed,
    offset so it never reproduces the same draws world_gen.py itself
    used). Presents the rule, then trait facts for every SEEN and
    RECOMBINED entity, in a randomized order. Never mentions preference
    for RECOMBINED entities, and never mentions NOVEL entities at all."""
    rng = random.Random(world.seed * 7919 + 1)  # distinct offset from world_gen's own seeding

    lines = [_pick(_RULE_TEMPLATES, rng).format(
        trait=world.trait_name, sub_with=world.substance_with_trait, sub_without=world.substance_without_trait,
    )]

    facts = []
    for entity in world.seen_entities_with_trait:
        facts.append(_pick(_TRAIT_FACT_TEMPLATES_POSITIVE, rng).format(entity=entity, trait=world.trait_name))
        facts.append(_pick(_SEEN_PREFERENCE_TEMPLATES, rng).format(entity=entity, substance=world.substance_with_trait))
    for entity in world.seen_entities_without_trait:
        facts.append(_pick(_TRAIT_FACT_TEMPLATES_NEGATIVE, rng).format(entity=entity, trait=world.trait_name))
        facts.append(_pick(_SEEN_PREFERENCE_TEMPLATES, rng).format(entity=entity, substance=world.substance_without_trait))
    for entity in world.recombined_entities_with_trait:
        facts.append(_pick(_TRAIT_FACT_TEMPLATES_POSITIVE, rng).format(entity=entity, trait=world.trait_name))
    for entity in world.recombined_entities_without_trait:
        facts.append(_pick(_TRAIT_FACT_TEMPLATES_NEGATIVE, rng).format(entity=entity, trait=world.trait_name))

    rng.shuffle(facts)
    lines.extend(facts)
    return " ".join(lines)


@dataclass
class TestPrompt:
    prompt_text: str
    label_map: dict           # {"A": substance_text, "B": substance_text}
    entity_name: str
    category: str             # "seen" | "recombined" | "novel"
    has_trait: bool
    correct_substance: str    # ground truth per the frozen rule -- NOT told to the model


def build_test_prompt(
    world: MicroWorld, entity_name: str, has_trait: bool, category: str, label_seed: int,
    question_seed: Optional[int] = None,
) -> TestPrompt:
    """category in {"seen", "recombined", "novel"}. For "novel", the trait
    is stated in the prompt itself (Formation never mentioned it); for
    "seen"/"recombined", the prompt asks about the entity by name alone,
    relying on whatever Formation already established."""
    q_rng = random.Random(question_seed if question_seed is not None else label_seed)
    label_map = randomize_label_mapping(
        world.substance_with_trait, world.substance_without_trait, random.Random(label_seed),
    )
    correct_substance = world.substance_with_trait if has_trait else world.substance_without_trait

    prefix = ""
    if category == "novel":
        templates = _NOVEL_INTRO_TEMPLATES_POSITIVE if has_trait else _NOVEL_INTRO_TEMPLATES_NEGATIVE
        prefix = _pick(templates, q_rng).format(entity=entity_name, trait=world.trait_name)

    question = _pick(_TEST_QUESTION_TEMPLATES, q_rng).format(
        entity=entity_name, opt_a=label_map["A"], opt_b=label_map["B"],
    )
    return TestPrompt(
        prompt_text=prefix + question, label_map=label_map, entity_name=entity_name,
        category=category, has_trait=has_trait, correct_substance=correct_substance,
    )


def verify_no_answer_leakage(world: MicroWorld, test_prompt: TestPrompt) -> Optional[str]:
    """Mission Section 6 'Prompt leakage' control.

    IMPORTANT, caught during this module's own construction, not glossed
    over: an earlier version of this check flagged "the correct
    substance's name appears in the prompt" as a leak -- but that is
    REQUIRED for any forced-choice question (both candidate substances
    must always be named as the two options; naming them is the
    question, not a leak). The real leaks checked for instead:

      1. For "seen"/"recombined" entities, the test prompt must never
         mention the trait name at all -- restating it would hand a
         "recombined" item the exact fact Formation deliberately
         withheld from the direct-preference statement, collapsing the
         seen/recombined distinction this task exists to preserve.
      2. The test prompt must never contain the RULE MAPPING itself
         (a "prefer <substance>" phrase sitting near the trait name) --
         if it did, the question would be answerable from the test
         prompt alone, with no need for anything taught during
         Formation, for any category including novel.
      3. The two label_map values must be exactly the world's two real
         substances (a construction-correctness check).

    Returns None if clean, else a string describing the problem found.
    """
    lowered_test = test_prompt.prompt_text.lower()
    trait_lower = world.trait_name.lower()

    if test_prompt.category in ("seen", "recombined") and trait_lower in lowered_test:
        return f"LEAK: {test_prompt.category} test prompt for {test_prompt.entity_name!r} mentions the trait name {world.trait_name!r}"

    for sub in (world.substance_with_trait, world.substance_without_trait):
        idx = lowered_test.find(f"prefer {sub.lower()}")
        if idx != -1 and trait_lower in lowered_test[max(0, idx - 40):idx]:
            return f"LEAK: test prompt restates the rule mapping itself ('...{trait_lower}... prefer {sub.lower()}...'), not just the entity's own trait"

    label_values = {test_prompt.label_map.get("A", "").lower(), test_prompt.label_map.get("B", "").lower()}
    expected_values = {world.substance_with_trait.lower(), world.substance_without_trait.lower()}
    if label_values != expected_values:
        return "CONSTRUCTION ERROR: label_map does not contain exactly the world's two real substances"

    return None


def world_trait_phrase_in(test_prompt: TestPrompt, lowered_text: str) -> bool:
    return False  # seen/recombined test prompts never include a trait-stating prefix by construction; see build_test_prompt
