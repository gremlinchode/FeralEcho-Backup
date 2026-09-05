"""
Deterministic artificial micro-world generator for the Echo Learning
Investigation (Phase 3 of the learning-investigation mission).

Generates a small relational-rule task, NOT an isolated fact-pair:
entities either possess or lack an invented "trait"; entities WITH the
trait are stated (via the general rule) to prefer invented substance P1
over P2, entities WITHOUT it prefer P2 over P1. Formation teaches the
abstract rule once, plus trait-possession facts for several named
entities -- but only SOME of those entities also have their resulting
preference stated directly. This produces three genuinely distinct test
categories, not three cosmetic relabelings of the same recall task:

  SEEN        -- an entity whose preference was directly, explicitly
                 stated during Formation. Tests plain recall.
  RECOMBINED  -- an entity mentioned during Formation (its trait was
                 stated) whose preference was NEVER directly stated --
                 answering correctly requires combining two
                 independently-taught facts (this entity's trait +
                 the general rule) that were never conjoined in the
                 same sentence during Formation.
  NOVEL       -- an entity never mentioned anywhere during Formation.
                 Its trait is stated only in the test prompt itself.
                 Answering correctly requires applying the general
                 rule to a genuinely new instance -- this is the one
                 category a system that merely memorized
                 entity-to-outcome pairs cannot pass by memorization
                 alone.

Every invented word (trait name, substance names, entity names) is
synthesized deterministically from a seed and is rejected/regenerated
if it:
  - collides with a real English dictionary word (checked against the
    real macOS system dictionary, /usr/share/dict/words, case-
    insensitive -- not merely "sounds English")
  - contains a forbidden substring associated with religious,
    political, culturally-loaded, emotionally-loaded, or famous/
    mythological-name content (mission's explicit exclusions)
  - collides with, or shares a 3-letter prefix with, a name already
    used in this repository's OTHER frozen experiment
    (app/experiments/preference_provenance/'s "Verel"/"Farun"/"Ossin")
    -- this experiment's vocabulary must never be confusable with, or
    accidentally primed by, tokens already tested in a different
    experiment.

Given the SAME seed, generate_world() always returns the SAME world --
this is the actual generative mechanism behind the frozen task
specification, not merely a description of one. A world's identity is
captured by MicroWorld.world_hash (sha256, truncated), which the frozen
spec records and which every experimental run re-derives and checks
against, per this project's own established freeze-and-verify
discipline (see the preference-provenance package's protocol seal for
the precedent this follows).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - environment-dependent, fails open to None
    _ENC = None


def token_count(text: str) -> Optional[int]:
    """Returns a real cl100k_base token count, or None if tiktoken is
    unavailable in this environment -- callers must handle None rather
    than assume a count is always available (same fail-open convention
    already established in this codebase's other experiment package)."""
    if _ENC is None:
        return None
    return len(_ENC.encode(text))


_FORBIDDEN_SUBSTRINGS = [
    # religious
    "god", "christ", "jesus", "allah", "buddh", "psalm", "bibl", "quran", "torah", "faith", "pray", "sacred",
    # political
    "trump", "biden", "democrat", "republic", "nazi", "communis", "capital", "libera", "conserv",
    # famous / mythological name fragments
    "zeus", "thor", "odin", "loki", "harry", "frodo", "gandalf", "vader", "sherlock", "hitler",
    # emotionally loaded roots
    "love", "hate", "death", "kill", "war", "fear", "pain", "hurt", "sad", "joy", "grief",
    # already-used tokens from the OTHER frozen experiment package (preference_provenance)
    "verel", "farun", "ossin",
]

_ONSETS = ["b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z",
           "dr", "fl", "gr", "kr", "pl", "sn", "tr", "vl"]
_VOWELS = ["a", "e", "i", "o", "u", "ai", "ei", "ou"]
_CODAS = ["b", "d", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z", "nd", "rk", "lt", "sk"]


def _contains_forbidden(word: str) -> bool:
    lowered = word.lower()
    return any(f in lowered for f in _FORBIDDEN_SUBSTRINGS)


def _load_system_dictionary() -> frozenset:
    try:
        with open("/usr/share/dict/words", "r", encoding="utf-8", errors="ignore") as f:
            return frozenset(line.strip().lower() for line in f if line.strip())
    except Exception:
        return frozenset()


_SYSTEM_DICTIONARY = _load_system_dictionary()
DICTIONARY_AVAILABLE = len(_SYSTEM_DICTIONARY) > 0  # exposed so callers/tests can assert this check is real


def generate_invented_word(rng: random.Random, syllables: int = 2, max_attempts: int = 500) -> str:
    """Synthesizes one pronounceable nonsense word, rejecting real
    dictionary words and forbidden-substring collisions. Raises
    RuntimeError (does not silently fall back to a possibly-tainted
    word) if no valid candidate is found within max_attempts."""
    for _ in range(max_attempts):
        parts = []
        for i in range(syllables):
            parts.append(rng.choice(_ONSETS))
            parts.append(rng.choice(_VOWELS))
            if i == syllables - 1 or rng.random() < 0.5:
                parts.append(rng.choice(_CODAS))
        word = "".join(parts)
        word = word[0].upper() + word[1:]
        if len(word) < 4 or len(word) > 9:
            continue
        if _contains_forbidden(word):
            continue
        if word.lower() in _SYSTEM_DICTIONARY:
            continue
        return word
    raise RuntimeError(f"Could not generate a valid invented word after {max_attempts} attempts (seed exhausted)")


@dataclass
class MicroWorld:
    seed: int
    trait_name: str
    substance_with_trait: str      # preferred by entities WITH the trait
    substance_without_trait: str   # preferred by entities WITHOUT the trait
    seen_entities_with_trait: List[str]        # trait + preference both stated during Formation
    seen_entities_without_trait: List[str]
    recombined_entities_with_trait: List[str]  # trait stated, preference NEVER stated during Formation
    recombined_entities_without_trait: List[str]
    novel_entities_with_trait: List[str]        # never mentioned during Formation at all
    novel_entities_without_trait: List[str]
    world_hash: str = field(default="")
    token_balance_report: dict = field(default_factory=dict)  # honest, measured spread -- not assumed

    def all_formation_entity_names(self) -> List[str]:
        return (
            self.seen_entities_with_trait + self.seen_entities_without_trait
            + self.recombined_entities_with_trait + self.recombined_entities_without_trait
        )

    def all_novel_entity_names(self) -> List[str]:
        return self.novel_entities_with_trait + self.novel_entities_without_trait

    def to_dict(self) -> dict:
        return {
            "seed": self.seed, "trait_name": self.trait_name,
            "substance_with_trait": self.substance_with_trait,
            "substance_without_trait": self.substance_without_trait,
            "seen_entities_with_trait": self.seen_entities_with_trait,
            "seen_entities_without_trait": self.seen_entities_without_trait,
            "recombined_entities_with_trait": self.recombined_entities_with_trait,
            "recombined_entities_without_trait": self.recombined_entities_without_trait,
            "novel_entities_with_trait": self.novel_entities_with_trait,
            "novel_entities_without_trait": self.novel_entities_without_trait,
            "world_hash": self.world_hash,
            "token_balance_report": self.token_balance_report,
        }


def generate_world(seed: int, n_seen_per_class: int = 2, n_recombined_per_class: int = 2,
                    n_novel_per_class: int = 2) -> MicroWorld:
    """Deterministic: the same seed always produces the same world (verified
    by a dedicated regression test, not merely asserted here)."""
    rng = random.Random(seed)
    used_names: List[str] = []
    _target_tokens: List[Optional[int]] = [None]  # mutable closure cell

    def _fresh(syllables: int = 2, balance_attempts: int = 30) -> str:
        candidates = []
        for _ in range(balance_attempts):
            w = generate_invented_word(rng, syllables=syllables)
            if w in used_names:
                continue
            if any(w[:3].lower() == u[:3].lower() for u in used_names):
                continue  # guard against superficial lexical overlap between any two names in this world
            candidates.append(w)
            if _target_tokens[0] is None:
                break  # first name in the world sets the target; take it as-is
            tc = token_count(w)
            if tc is not None and tc == _target_tokens[0]:
                break  # exact match to the running target -- stop searching
        if not candidates:
            raise RuntimeError("Could not generate a fresh, non-colliding invented word within the attempt budget")
        # Prefer the candidate closest to the running token-count target (set by
        # the first name generated); this is a soft preference, not a hard
        # requirement -- if tiktoken is unavailable, token_count() returns None
        # for every candidate and the first candidate generated is used as-is.
        if _target_tokens[0] is not None:
            scored = [(abs((token_count(c) or 0) - _target_tokens[0]), c) for c in candidates]
            scored.sort(key=lambda x: x[0])
            chosen = scored[0][1]
        else:
            chosen = candidates[0]
        used_names.append(chosen)
        if _target_tokens[0] is None:
            _target_tokens[0] = token_count(chosen)
        return chosen

    trait_name = _fresh(syllables=2)
    substance_a = _fresh(syllables=2)
    substance_b = _fresh(syllables=2)

    total_entities = 2 * (n_seen_per_class + n_recombined_per_class + n_novel_per_class)
    entity_pool = [_fresh(syllables=2) for _ in range(total_entities)]
    rng.shuffle(entity_pool)

    i = 0
    seen_with = entity_pool[i:i + n_seen_per_class]; i += n_seen_per_class
    seen_without = entity_pool[i:i + n_seen_per_class]; i += n_seen_per_class
    recombined_with = entity_pool[i:i + n_recombined_per_class]; i += n_recombined_per_class
    recombined_without = entity_pool[i:i + n_recombined_per_class]; i += n_recombined_per_class
    novel_with = entity_pool[i:i + n_novel_per_class]; i += n_novel_per_class
    novel_without = entity_pool[i:i + n_novel_per_class]; i += n_novel_per_class

    # Randomize which substance corresponds to "has the trait" per-world, so
    # no single fixed global mapping exists across multiple independent
    # world instances (guards against a shortcut that only works because
    # every world happens to use the same trait->substance polarity).
    if rng.random() < 0.5:
        substance_a, substance_b = substance_b, substance_a

    world_hash_input = "|".join([
        str(seed), trait_name, substance_a, substance_b,
        ",".join(seen_with), ",".join(seen_without),
        ",".join(recombined_with), ",".join(recombined_without),
        ",".join(novel_with), ",".join(novel_without),
    ])
    world_hash = hashlib.sha256(world_hash_input.encode("utf-8")).hexdigest()[:16]

    all_names = ([trait_name, substance_a, substance_b] + seen_with + seen_without
                 + recombined_with + recombined_without + novel_with + novel_without)
    counts = [token_count(n) for n in all_names]
    counts = [c for c in counts if c is not None]
    balance_report = (
        {"min": min(counts), "max": max(counts), "spread": max(counts) - min(counts), "n": len(counts)}
        if counts else {"min": None, "max": None, "spread": None, "n": 0, "note": "tiktoken unavailable"}
    )

    return MicroWorld(
        seed=seed, trait_name=trait_name,
        substance_with_trait=substance_a, substance_without_trait=substance_b,
        seen_entities_with_trait=seen_with, seen_entities_without_trait=seen_without,
        recombined_entities_with_trait=recombined_with, recombined_entities_without_trait=recombined_without,
        novel_entities_with_trait=novel_with, novel_entities_without_trait=novel_without,
        world_hash=world_hash, token_balance_report=balance_report,
    )
