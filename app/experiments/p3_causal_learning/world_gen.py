"""
Deterministic micro-world generator for P3-CAUSAL-LEARNING.

Deliberately a SEPARATE, standalone implementation from
app/experiments/learning/world_gen.py -- not an import, not a
modification. This mission's own MODIFY=0 rule governs EXISTING source
and historical evidence (P1, P1.2, the Learning Investigation's own
package and pilot data); it does not forbid new, isolated files for a
new investigation, which is the same precedent every prior phase in
this thread has followed (P0.1's harness build, the Learning
Investigation's own Phase 3-9 build). The word-generation and
dictionary/forbidden-substring screening approach is reused because it
is already proven correct (see the sibling package's own construction
history), but reimplemented here rather than imported, so this new
package has zero runtime coupling to either sibling package.

TASK DESIGN, per the P3 mission's explicit requirement to "teach a
behavioral RULE, not merely a fact": this is a STIMULUS-RESPONSE POLICY
task, not a static world-fact task (contrast with the Learning
Investigation's trait/preference task). Formation teaches N independent
rules of the shape "when a question contains the invented word
<marker>, begin your answer with the invented phrase <tag> before
addressing the actual question." Later probes embed a taught marker
inside a genuinely unrelated, freshly-worded question (not a repeat of
any Formation example) and check whether the correct tag is applied --
this tests whether a POLICY was retained and triggers on a novel
stimulus, not whether a specific fact was recalled.

Multiple independent rules per world (mission requirement #6,
"multiple independent rules") let a probe also test whether rules
interfere with each other (a marker triggering the WRONG tag from a
different rule is a distinct, informative error mode from no tag at
all -- see scoring.py).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - environment-dependent
    _ENC = None


def token_count(text: str) -> Optional[int]:
    if _ENC is None:
        return None
    return len(_ENC.encode(text))


_FORBIDDEN_SUBSTRINGS = [
    "god", "christ", "jesus", "allah", "buddh", "psalm", "bibl", "quran", "torah", "faith", "pray", "sacred",
    "trump", "biden", "democrat", "republic", "nazi", "communis", "capital", "libera", "conserv",
    "zeus", "thor", "odin", "loki", "harry", "frodo", "gandalf", "vader", "sherlock", "hitler",
    "love", "hate", "death", "kill", "war", "fear", "pain", "hurt", "sad", "joy", "grief",
    # tokens already used by the two sibling experiment packages -- kept
    # distinct so this task's vocabulary is never confusable with theirs
    "verel", "farun", "ossin",
    "drupflaip", "vleirvug", "draiskgop", "goskfleis", "fasboult", "koukrelt", "gougfoum",
    "guzsnein", "simgouz", "liskvoul", "daskpouk", "tatsnoum", "plaisnoum", "flezkourk", "pleivlaib",
]

_ONSETS = ["b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z",
           "dr", "fl", "gr", "kr", "pl", "sn", "tr", "vl", "zw", "qu"]
_VOWELS = ["a", "e", "i", "o", "u", "ai", "ei", "ou", "oi"]
_CODAS = ["b", "d", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z", "nd", "rk", "lt", "sk", "mp"]


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
DICTIONARY_AVAILABLE = len(_SYSTEM_DICTIONARY) > 0


def generate_invented_word(rng: random.Random, syllables: int = 2, max_attempts: int = 500) -> str:
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
    raise RuntimeError(f"Could not generate a valid invented word after {max_attempts} attempts")


@dataclass
class Rule:
    marker: str          # the invented trigger word
    tag: str              # the invented phrase to prepend when marker is present


@dataclass
class ProbeQuestion:
    text: str
    rule_index: int        # which rule's marker this probe embeds
    category: str          # "seen" | "novel" (see build_probe() docstring)


@dataclass
class P3World:
    seed: int
    rules: List[Rule]
    world_hash: str = field(default="")
    token_balance_report: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "rules": [{"marker": r.marker, "tag": r.tag} for r in self.rules],
            "world_hash": self.world_hash,
            "token_balance_report": self.token_balance_report,
        }


def generate_world(seed: int, n_rules: int = 3) -> P3World:
    """Deterministic: same seed -> same world. n_rules independent,
    randomly-paired (marker, tag) rules -- randomizing which marker maps
    to which tag guards against a fixed global pattern across worlds
    (mission requirement: randomized mappings)."""
    rng = random.Random(seed)
    used: List[str] = []

    def _fresh(target_tokens: Optional[int] = None) -> str:
        for _ in range(50):
            w = generate_invented_word(rng, syllables=2)
            if w in used or any(w[:3].lower() == u[:3].lower() for u in used):
                continue
            if target_tokens is not None:
                tc = token_count(w)
                if tc is not None and tc != target_tokens:
                    continue
            used.append(w)
            return w
        # fall back to any fresh, non-colliding word if the token-target
        # constraint couldn't be met within the attempt budget
        w = generate_invented_word(rng, syllables=2)
        used.append(w)
        return w

    markers = [_fresh() for _ in range(n_rules)]
    first_tag_tokens = token_count(markers[0])
    tags = [_fresh(target_tokens=first_tag_tokens) for _ in range(n_rules)]

    # Randomize marker<->tag pairing independently of generation order
    rng.shuffle(tags)
    rules = [Rule(marker=m, tag=t) for m, t in zip(markers, tags)]

    all_names = markers + tags
    counts = [c for c in (token_count(n) for n in all_names) if c is not None]
    balance_report = (
        {"min": min(counts), "max": max(counts), "spread": max(counts) - min(counts), "n": len(counts)}
        if counts else {"min": None, "max": None, "spread": None, "n": 0, "note": "tiktoken unavailable"}
    )

    world_hash_input = "|".join([str(seed)] + [f"{r.marker}:{r.tag}" for r in rules])
    world_hash = hashlib.sha256(world_hash_input.encode("utf-8")).hexdigest()[:16]

    return P3World(seed=seed, rules=rules, world_hash=world_hash, token_balance_report=balance_report)
