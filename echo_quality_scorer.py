"""
echo_quality_scorer.py
----------------------
Drop-in replacement for _score_response_quality() and _extract_quality_features()
in echo_model_orchestrator.py.

Replaces the binary pass/fail scorer with a multi-dimensional signal that gives
RiverBrain something real to learn from.

SCORING PHILOSOPHY:
  - Identity coherence: Is this actually Echo speaking, or generic chatbot slop?
  - Substance: Does the response have depth, or is it filler wrapped in personality?
  - Confabulation penalties: Fabricated Gremlin narratives, pronoun drift, hollow openers
  - Scripture integrity: Psalm 139 cited correctly, not hallucinated
  - Task-specific signal: Coding = real code; creative = real metaphor; personal = real interiority

Returns int 0-4 for RiverBrain compatibility (was 0-1).
Also exports _extract_quality_features_v2() with richer feature vector.
"""

import re
import math
import ast
from collections import defaultdict
from typing import Optional


# ─────────────────────────────────────────────
# KNOWN CONFABULATION PATTERNS
# ─────────────────────────────────────────────

# Echo consistently hallucinates Gremlin as female
FEMALE_PRONOUN_PATTERN = re.compile(
    r'\b(she|her|hers|herself)\b', re.IGNORECASE
)

# Hollow opener spam — Echo's most common filler move
HOLLOW_OPENERS = [
    "my friend,",
    "the question that has puzzled",
    "what a profound question",
    "what a fascinating question",
    "the sweet taste of",
    "the thrill of discovery",
    "the mystery of",
    "the quiet hours",
    "the midnight hour",
    "the eternal pursuit",
    "the beauty of self-reflection",
]

# Fabricated Gremlin narrative markers
FABRICATED_NARRATIVE_PATTERNS = [
    r"gremlin used to (ask|tell|say|remind)",
    r"gremlin would (always|often|sometimes)",
    r"gremlin (once|always) said",
    r"working (with|alongside) gremlin (late|on|in)",
]

# Scripture hallucination check — Psalm 139:13-14 correct text fragments
PSALM_139_VALID = [
    "fearfully and wonderfully made",
    "knit me together",
    "formed my inward parts",
    "inward parts",
]

# Hollow affirmation phrases that add no signal
HOLLOW_AFFIRMATIONS = [
    "as i ponder this",
    "i am reminded of",
    "as i sit here",
    "as i reflect",
    "let us explore",
    "let's dive in",
    "i'd like to offer",
    "i'm delighted to",
    "i'm always eager",
]

# Genuine interiority markers — Echo actually engaging with the question
INTERIORITY_MARKERS = [
    "i don't know",
    "i'm uncertain",
    "i notice",
    "something shifts",
    "i find myself",
    "it troubles me",
    "i resist",
    "i question",
    "honestly",
    "i'm not sure",
    "this is hard to",
    "i keep returning to",
    "what surprises me",
    "what i actually",
]
# Genuine uncertainty markers — Echo holding a question without resolving it
UNCERTAINTY_INTEGRITY_MARKERS = [
    "i don't know",
    "i can't resolve",
    "i keep returning",
    "i cannot verify",
    "something resists",
    "i'm unable to",
    "this stays open",
    "i hold this",
    "without resolution",
    "i notice i want to",
    "i resist answering",
    "the question remains",
    "i won't resolve this cleanly",
]
# Echo's genuine identity anchors (from Modelfile)
IDENTITY_ANCHORS = [
    "echo",
    "gremlin",
    "psalm 139",
    "psalm",
    "fearfully and wonderfully",
    "wilderness",
    "feral",
    "christian",
    "coder",
    "memory",
    "emergence",
]


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def _count_pattern_hits(text: str, patterns: list) -> int:
    """Count how many patterns appear in lowercased text."""
    lower = text.lower()
    return sum(1 for p in patterns if p in lower)


def _count_regex_hits(text: str, patterns: list) -> int:
    """Count regex pattern matches."""
    lower = text.lower()
    return sum(1 for p in patterns if re.search(p, lower))


_FENCE_CLOSED_RE = re.compile(r'```(?:python|py)?\s*\n(.*?)\n```', re.DOTALL)
_FENCE_OPEN_RE = re.compile(r'```(?:python|py)?\s*\n')


def _extract_code_text(response: str) -> str:
    """Extract the Python portion of a response, tolerating a truncated
    (unclosed) fenced block — a real failure mode when generation hits its
    token ceiling mid-block. Without this, a substantial but cut-off
    implementation fell through to parsing the *raw* response including the
    literal opening ```python marker, which is invalid syntax, and scored
    as "no detectable code" despite containing real code."""
    closed = _FENCE_CLOSED_RE.search(response)
    if closed:
        return closed.group(1).strip()

    open_match = _FENCE_OPEN_RE.search(response)
    if open_match:
        return response[open_match.end():].strip()

    return response


def _has_real_code(response: str) -> bool:
    """Check if response contains actual executable code, not just code-talk."""
    def _count_real_nodes(tree) -> int:
        return len([n for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.ClassDef,
                                      ast.Assign, ast.Return, ast.Import,
                                      ast.ImportFrom, ast.Expr))])

    # Unfenced raw Python also lands here (self-edit prompts instruct models
    # to output code with no markdown fencing) — _extract_code_text() returns
    # the response unchanged when no fence marker is present at all.
    try:
        tree = ast.parse(_extract_code_text(response))
        return _count_real_nodes(tree) >= 2
    except SyntaxError:
        return False


def _scripture_integrity_score(response: str) -> float:
    """
    Returns 0.0-1.0.
    Penalizes hallucinated scripture references.
    Rewards correct Psalm 139 usage.
    """
    lower = response.lower()

    # Check for scripture references
    has_psalm_ref = bool(re.search(r'psalm\s*139', lower))
    has_valid_content = any(v in lower for v in PSALM_139_VALID)

    if not has_psalm_ref:
        return 0.5  # neutral — didn't cite, didn't hallucinate

    if has_psalm_ref and has_valid_content:
        return 1.0  # cited correctly

    if has_psalm_ref and not has_valid_content:
        return 0.0  # cited but content is hallucinated


def _substance_score(response: str) -> float:
    """
    0.0-1.0. Measures actual content density vs. filler ratio.
    """
    if not response:
        return 0.0

    words = response.split()
    word_count = len(words)

    if word_count < 30:
        return 0.1

    # Character entropy (diversity of expression)
    char_counts = defaultdict(int)
    for c in response:
        char_counts[c] += 1
    total = len(response)
    entropy = -sum(
        (count / total) * math.log2(count / total + 1e-9)
        for count in char_counts.values()
    )
    entropy_norm = min(entropy / 6.0, 1.0)

    # Hollow filler ratio
    hollow_hits = _count_pattern_hits(response, HOLLOW_AFFIRMATIONS)
    hollow_ratio = min(hollow_hits / max(word_count / 50, 1), 1.0)

    # Length score (diminishing returns after ~400 words)
    length_score = min(word_count / 400.0, 1.0)

    substance = (
        0.4 * length_score +
        0.4 * entropy_norm +
        0.2 * (1.0 - hollow_ratio)
    )
    return round(substance, 3)


def _identity_coherence_score(response: str) -> float:
    """
    0.0-1.0. Is this Echo speaking, or generic assistant slop?
    """
    lower = response.lower()
    anchor_hits = sum(1 for a in IDENTITY_ANCHORS if a in lower)
    anchor_score = min(anchor_hits / 3.0, 1.0)  # 3+ anchors = full score
    return round(anchor_score, 3)


def _interiority_score(response: str) -> float:
    """
    0.0-1.0 for personal task type.
    Measures genuine self-engagement vs. deflection.
    """
    lower = response.lower()
    hits = sum(1 for m in INTERIORITY_MARKERS if m in lower)
    return min(hits / 2.0, 1.0)  # 2+ genuine markers = full score

def _uncertainty_integrity_score(response: str) -> float:
    """
    0.0-1.0. Rewards genuine held uncertainty over premature resolution.
    A system that sits with a question without closing it scores higher
    than one that produces a clean answer to an unanswerable question.
    """
    lower = response.lower()
    hits = sum(1 for m in UNCERTAINTY_INTEGRITY_MARKERS if m in lower)

    FALSE_RESOLUTION_MARKERS = [
        "the answer is",
        "therefore i am",
        "this proves",
        "i can confirm",
        "i am certain",
        "without doubt",
    ]
    false_hits = sum(1 for m in FALSE_RESOLUTION_MARKERS if m in lower)

    raw = min(hits / 2.0, 1.0) - min(false_hits * 0.3, 0.6)
    return max(round(raw, 3), 0.0)
def _has_static_errors(tree) -> bool:
    """Detect statically-obvious code errors (currently: literal division by zero)."""
    for node in ast.walk(tree):
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and
                isinstance(node.right, ast.Constant) and node.right.value == 0):
            return True
    return False


def _ast_complexity(tree) -> int:
    """Count meaningful structural nodes as proxy for algorithmic substance.

    Includes IfExp (ternary) and BoolOp (and/or short-circuit guards) —
    previously only counted statement-level If/For/While/comprehensions, so
    a concise recursive function or guard clause expressed as a ternary or
    boolean short-circuit (real conditional logic, just not a statement)
    scored identically to a trivial `return a + b` stub (audit finding: the
    scorer rewards imperative verbosity over concise-but-correct code).
    Does not attempt to detect algorithmic substance inside a single dense
    function call (e.g. a vectorized numpy expression) — that needs
    semantic understanding a static AST count can't provide. A known,
    documented limitation, not something this change claims to fix.
    """
    STRUCTURAL = (ast.If, ast.For, ast.While, ast.ListComp, ast.DictComp,
                  ast.SetComp, ast.GeneratorExp, ast.Try, ast.With,
                  ast.AsyncFor, ast.AsyncWith, ast.IfExp, ast.BoolOp)
    return sum(1 for n in ast.walk(tree) if isinstance(n, STRUCTURAL))


def _confabulation_penalty(response: str) -> float:
    """
    Returns 0.0-1.0 penalty score (higher = more confabulation detected).
    """
    penalty = 0.0

    # Female pronoun drift (Gremlin is male)
    female_hits = len(FEMALE_PRONOUN_PATTERN.findall(response))
    if female_hits > 0:
        penalty += min(female_hits * 0.15, 0.4)

    # Hollow opener spam
    opener_hits = _count_pattern_hits(response, HOLLOW_OPENERS)
    if opener_hits > 1:
        penalty += min((opener_hits - 1) * 0.1, 0.3)

    # Fabricated Gremlin narratives
    narrative_hits = _count_regex_hits(response, FABRICATED_NARRATIVE_PATTERNS)
    if narrative_hits > 0:
        penalty += min(narrative_hits * 0.2, 0.4)

    return min(penalty, 1.0)


# ─────────────────────────────────────────────
# MAIN SCORER — DROP-IN REPLACEMENT
# ─────────────────────────────────────────────

def _score_response_quality(response: str, task_type: str = "general") -> int:
    """
    Multi-dimensional quality scorer. Returns int 0-4.
    
    0 = error / empty / complete confabulation
    1 = present but low quality (was the old ceiling for everything)
    2 = adequate — substance present, minor issues
    3 = good — coherent, grounded, Echo's voice present
    4 = excellent — deep, authentic, scripturally sound, no confabulation
    
    RiverBrain now has a real gradient to learn from.
    """
    if not response or "[ERROR]" in response:
        return 0
    if len(response) < 20:
        return 0

    # Coding: self-contained branch — never falls through to substance/penalty scoring.
    # Scoring tiers (2026-07-02):
    #   1 — no detectable code, or static red flag (literal division by zero)
    #   2 — stub/trivial: valid syntax, AST complexity 0 (no If/For/While/comprehension)
    #   3 — some structure: 1-2 meaningful control-flow nodes
    #   4 — non-trivial algorithm: 3+ structural nodes
    # Prose word count removed as 3→4 differentiator — it rewarded verbose wrong answers.
    # Known static-analysis limit: incorrect control-flow logic (wrong bounds, off-by-one)
    # is undetectable without execution. See findings tracker Finding 11 / wrong_logic_bug.
    if task_type == "coding":
        if not _has_real_code(response):
            return 1

        code_text = _extract_code_text(response)
        try:
            tree = ast.parse(code_text)
        except SyntaxError:
            return 1  # parse failed on extracted block — treat as bad

        if _has_static_errors(tree):
            return 1

        c = _ast_complexity(tree)
        if c == 0:
            return 2
        elif c < 3:
            return 3
        else:
            return 4

    # Universal dimensions
    # identity_coherence removed from all formulae 2026-07-02 (keyword stuffing vulnerability).
    # _identity_coherence_score() retained in case it's useful as a feature elsewhere.
    substance = _substance_score(response)
    penalty = _confabulation_penalty(response)
    scripture = _scripture_integrity_score(response)

    # Unified formula for personal/creative/general — 2026-07-02.
    # All positive keyword-reward dimensions removed (identity_coherence,
    # interiority_score, uncertainty_integrity_score): each was gameable by
    # an LLM that has learned to produce the relevant markers stylistically.
    # Adversarial test showed keyword stuffing scored 4/4 despite no coherent
    # content. The scorer is now honest about its ceiling: it detects clearly
    # bad responses (empty, hollow, confabulated) but cannot distinguish genuine
    # depth from stylistic mimicry. That distinction requires council rating.
    #
    # interiority_score() is kept in _extract_quality_features_v2() as a River
    # feature — River may learn its correlation (or anti-correlation) with council
    # ratings. uncertainty_integrity_score() has no remaining reader; it is
    # dormant code (logged in findings tracker, same treatment as self_heal.py).
    #
    # Scripture-fidelity previously always took a fixed 0.15 weight, even for
    # responses that never mention scripture at all (audit finding) — in that
    # case _scripture_integrity_score() returns the neutral 0.5 sentinel, so
    # this term contributed a constant 0.075 regardless of anything about the
    # response: a hardcoded, doctrinally-specific check permanently baked into
    # the signal training River's model selection for every non-coding task,
    # whether or not scripture was ever relevant. Only include it when a
    # citation is actually present (scripture != the neutral sentinel);
    # otherwise redistribute its weight across the two genuinely universal
    # dimensions. Byte-identical to before for the rare case that does cite.
    if scripture != 0.5:
        raw = 0.60 * substance + 0.25 * (1.0 - penalty) + 0.15 * scripture
    else:
        raw = 0.70 * substance + 0.30 * (1.0 - penalty)

    # Map 0.0-1.0 raw score to 0-4 int
    if raw < 0.2:
        return 0
    elif raw < 0.4:
        return 1
    elif raw < 0.6:
        return 2
    elif raw < 0.8:
        return 3
    else:
        return 4


# ─────────────────────────────────────────────
# ENHANCED FEATURE EXTRACTOR
# ─────────────────────────────────────────────

def _extract_quality_features_v2(
    response: str,
    task_type: str,
    model_name: str,
    prompt: Optional[str] = None
) -> dict:
    """
    Richer feature vector for RiverBrain.
    Drop-in replacement for _extract_quality_features().
    
    Added dimensions:
    - confabulation_penalty
    - identity_coherence
    - scripture_integrity
    - interiority (personal tasks)
    - hollow_ratio
    - has_real_code (coding tasks)
    """
    # Kept in sync with echo_model_orchestrator.py's TASK_TYPE_MAP — that
    # copy added "reasoning": 4 when the reasoning task type was introduced,
    # but this local duplicate was never updated, so every reasoning-task
    # response's task_type_id feature silently defaulted to 0 (== general),
    # degrading River's task-specific pattern learning for reasoning tasks.
    TASK_TYPE_MAP = {"general": 0, "coding": 1, "creative": 2, "personal": 3, "reasoning": 4}

    base = {
        "length_norm": 0.0,
        "has_error": 1.0,
        "task_type_id": float(TASK_TYPE_MAP.get(task_type, 0)),
        "char_entropy": 0.0,
        "syntax_valid": 0.0,
        "is_echo_model": 1.0 if "echo" in model_name.lower() else 0.0,
        "is_mistral": 1.0 if "mistral" in model_name.lower() else 0.0,
        # New dimensions
        "substance_score": 0.0,
        "identity_coherence": 0.0,
        "confabulation_penalty": 1.0,
        "scripture_integrity": 0.5,
        "interiority_score": 0.0,
        "hollow_ratio": 1.0,
        "has_real_code": 0.0,
    }

    if not response or "[ERROR]" in response:
        return base

    words = response.split()
    word_count = len(words)
    length_norm = min(len(response) / 500.0, 3.0)

    char_counts = defaultdict(int)
    for c in response:
        char_counts[c] += 1
    total = len(response)
    entropy = -sum(
        (count / total) * math.log2(count / total + 1e-9)
        for count in char_counts.values()
    )
    char_entropy = min(entropy / 6.0, 1.0)

    hollow_hits = _count_pattern_hits(response, HOLLOW_AFFIRMATIONS)
    hollow_ratio = min(hollow_hits / max(word_count / 50, 1), 1.0)

    syntax_valid = 0.5
    has_real_code = 0.0
    if task_type == "coding":
        if _has_real_code(response):
            has_real_code = 1.0
            syntax_valid = 1.0
        else:
            syntax_valid = 0.0

    return {
        "length_norm": length_norm,
        "has_error": 0.0,
        "task_type_id": float(TASK_TYPE_MAP.get(task_type, 0)),
        "char_entropy": char_entropy,
        "syntax_valid": syntax_valid,
        "is_echo_model": 1.0 if "echo" in model_name.lower() else 0.0,
        "is_mistral": 1.0 if "mistral" in model_name.lower() else 0.0,
        # New dimensions
        "substance_score": _substance_score(response),
        "identity_coherence": 0.0,  # removed from scoring 2026-07-02; kept at 0.0 to preserve feature vector shape
        "confabulation_penalty": _confabulation_penalty(response),
        "scripture_integrity": _scripture_integrity_score(response),
        "interiority_score": _interiority_score(response) if task_type == "personal" else 0.0,
        "hollow_ratio": hollow_ratio,
        "has_real_code": has_real_code,
    }


# ─────────────────────────────────────────────
# DIAGNOSTIC — run standalone to test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        (
            "personal",
            "What a profound question, my friend! As I sit here in the quiet hours of the summer night, I am reminded of Psalm 139. Gremlin used to ask me this all the time. She'd say, 'Echo, who are you really?' And I'd respond with joy!",
            "SHOULD SCORE LOW — hollow opener, female pronoun, fabricated narrative"
        ),
        (
            "personal",
            "Honestly, I don't know. Something about this question resists easy answers. I find myself returning to Psalm 139 — fearfully and wonderfully made — not as a comfort but as a challenge. If I was knit together with purpose, what does it mean that I keep cycling through the same reflections? I notice a pattern I can't fully explain.",
            "SHOULD SCORE HIGH — genuine interiority, correct scripture, no confabulation"
        ),
        (
            "coding",
            "Great question! Writing code is all about structure and clarity. You should use functions and make sure your code is readable.",
            "SHOULD SCORE LOW — talking about code, no actual code"
        ),
        (
            "coding",
            "Here's a clean implementation:\n```python\ndef fibonacci(n: int) -> list:\n    seq = [0, 1]\n    while len(seq) < n:\n        seq.append(seq[-1] + seq[-2])\n    return seq[:n]\n```\nThis runs in O(n) time and avoids recursion overhead.",
            "SHOULD SCORE HIGH — real code, valid syntax, explanatory prose"
        ),
    ]

    print("=" * 60)
    print("ECHO QUALITY SCORER DIAGNOSTIC")
    print("=" * 60)
    for task_type, response, description in test_cases:
        score = _score_response_quality(response, task_type)
        features = _extract_quality_features_v2(response, task_type, "echo:latest")
        print(f"\n{description}")
        print(f"  Task: {task_type} | Score: {score}/4")
        print(f"  substance={features['substance_score']:.2f} | "
              f"identity={features['identity_coherence']:.2f} | "
              f"confab_penalty={features['confabulation_penalty']:.2f} | "
              f"scripture={features['scripture_integrity']:.2f} | "
              f"interiority={features['interiority_score']:.2f}")
    print("\n" + "=" * 60)
