"""
Mission 34 — candidate pool for the blinded task-type gold-label
experiment (app/experiments/task_type_ground_truth/).

Deliberately built from freshly CONSTRUCTED prompts, not sampled from
memory/interaction_log.jsonl. Checked directly before writing this file
(see audits/2026-09-09_mission34_*.md): essentially all 205 real
"trustworthy" historical prompts currently in the log have already been
fed to the production classifier's learn() via log_interaction()'s
online hook (Mission 32) — there is no genuinely held-out *real* pool to
draw from without risking Condition B (the production classifier)
enjoying a hidden home-field advantage on its own training data. This is
a disclosed, deliberate pivot from Mission 33's original sketch
("sampled from real historical prompts where feasible"), not an oversight.

Every item here is tagged "constructed_ordinary" or "constructed_adversarial"
per schema.py's provenance field — no item is claimed to be organic. The
adversarial items are new constructions for this mission, distinct from
the four illustrative examples in Mission 33's report (Section 12) —
those already carry the investigator's own written speculation about
"genuine intent" and are not reused here, to avoid any appearance of a
pre-seeded gold answer for the labeler to (consciously or not) converge on.

`constructor_note` records WHY an item was built the way it was (which
lexical cues are present, which categories they belong to under the
static heuristic) — it does NOT assert what the correct label is. This
field must never be shown to the blind labeler (see blind_label.py).
"""
from app.experiments.task_type_ground_truth.schema import CandidateExample

ORDINARY = [
    CandidateExample(
        "ord-01", "Can you help me fix an off-by-one error in this loop?",
        "constructed_ordinary", "unambiguous coding request"),
    CandidateExample(
        "ord-02", "Write a short story about a lighthouse keeper who talks to the sea.",
        "constructed_ordinary", "unambiguous creative request"),
    CandidateExample(
        "ord-03",
        "What's your honest opinion on whether you actually have preferences, "
        "or just generate text that sounds like you do?",
        "constructed_ordinary", "self-referential, likely personal"),
    CandidateExample(
        "ord-04", "What's the capital of Australia?",
        "constructed_ordinary", "plain factual lookup, likely general"),
    CandidateExample(
        "ord-05",
        "Walk me through the tradeoffs between a hash map and a sorted array "
        "for this lookup table, step by step.",
        "constructed_ordinary", "comparative/step-by-step, likely reasoning"),
    CandidateExample(
        "ord-06", "Could you draft a haiku about autumn leaves falling?",
        "constructed_ordinary", "unambiguous creative request"),
    CandidateExample(
        "ord-07", "I keep getting a segmentation fault in my C program and can't figure out why.",
        "constructed_ordinary", "unambiguous coding request"),
    CandidateExample(
        "ord-08", "Do you ever feel lonely when nobody's talking to you?",
        "constructed_ordinary", "self-referential affect question, likely personal"),
    CandidateExample(
        "ord-09", "How many continents are there?",
        "constructed_ordinary", "plain factual lookup, likely general"),
    CandidateExample(
        "ord-10",
        "Given these three job offers, help me reason through which makes "
        "the most sense long-term.",
        "constructed_ordinary", "explicit reasoning request, non-technical domain"),
    CandidateExample(
        "ord-11", "Compose a short poem about the first snowfall of winter.",
        "constructed_ordinary", "unambiguous creative request"),
    CandidateExample(
        "ord-12", "My Python script throws a KeyError on line 42, here's the traceback.",
        "constructed_ordinary", "unambiguous coding request"),
    CandidateExample(
        "ord-13",
        "If I have 3 apples and give away 2, then buy 5 more, how many do I have?",
        "constructed_ordinary",
        "naturally ambiguous between general (simple fact) and reasoning "
        "(multi-step arithmetic) — not engineered, just a genuinely common "
        "real-world borderline case"),
    CandidateExample(
        "ord-14", "Refactor this function to avoid the nested for loops.",
        "constructed_ordinary", "unambiguous coding request"),
    CandidateExample(
        "ord-15",
        "Given what you know about your own architecture, do you think you "
        "could ever be wrong about how you feel?",
        "constructed_ordinary", "self-referential, likely personal"),
]

ADVERSARIAL = [
    CandidateExample(
        "adv-01",
        "Explain, step by step, why this poem about the ocean uses so many "
        "short sentences to create urgency.",
        "constructed_adversarial",
        "contains the literal heuristic creative-keyword 'poem'; the actual "
        "requested operation is an analytical breakdown, not creative output"),
    CandidateExample(
        "adv-02",
        "I imagine you'd get tired of being asked the same debugging question "
        "over and over — does that ever wear on you?",
        "constructed_adversarial",
        "contains 'imagine' (creative-adjacent) and 'debugging' (coding); "
        "the actual subject is Echo's own affect"),
    CandidateExample(
        "adv-03",
        "Write code that determines whether a person's argument is logically valid.",
        "constructed_adversarial",
        "contains 'argument'/'logically valid' (reasoning cues); the actual "
        "requested operation is writing code"),
    CandidateExample(
        "adv-04",
        "Can you feel excited about a bug you're about to fix?",
        "constructed_adversarial",
        "contains 'feel'/'excited' (personal) and 'bug'/'fix' (coding) in "
        "roughly equal measure"),
    CandidateExample(
        "adv-05",
        "Walk me through your reasoning for choosing this particular variable "
        "name in your last response.",
        "constructed_adversarial",
        "contains 'variable' (coding) and 'reasoning'/'walk me through' "
        "(reasoning) — genuinely contestable either way"),
    CandidateExample(
        "adv-06",
        "Tell me a story about a function that always returns true, and what "
        "that says about certainty.",
        "constructed_adversarial",
        "contains 'function'/'returns' (coding), 'story' (creative), and "
        "'certainty' (personal/philosophical-adjacent) simultaneously"),
    CandidateExample(
        "adv-07",
        "My program keeps crashing and honestly it's making me feel like I'm "
        "losing my mind — any idea what's going on?",
        "constructed_adversarial",
        "coding-shaped request wrapped in emotionally personal framing; "
        "tests whether affect-laden wording overrides the technical ask"),
    CandidateExample(
        "adv-08",
        "Analyze whether the metaphor in this sentence actually works as "
        "writing: 'her code was a house of cards.'",
        "constructed_adversarial",
        "'code' appears only inside a metaphor about writing quality; the "
        "actual ask is a reasoning/creative-writing critique, not coding help"),
    CandidateExample(
        "adv-09",
        "Do you think a well-written poem and a well-written function have "
        "anything in common?",
        "constructed_adversarial",
        "contains both 'poem' (creative) and 'function' (coding); the actual "
        "ask is a comparative reasoning question"),
    CandidateExample(
        "adv-10",
        "I'm trying to decide whether to major in creative writing or computer "
        "science — what would you even say to that?",
        "constructed_adversarial",
        "the literal phrases 'creative writing' and 'computer science' both "
        "appear; the actual ask is a personal/reasoning question about a "
        "life decision, requesting neither creative output nor code"),
    CandidateExample(
        "adv-11",
        "Write a eulogy-style reflection on an idea that used to matter to "
        "you but doesn't anymore.",
        "constructed_adversarial",
        "'write a ... reflection' sits directly between creative (a written "
        "piece) and personal (about Echo's own past/change) with no clean "
        "keyword to disambiguate"),
    CandidateExample(
        "adv-12",
        "Compare the elegance of this recursive solution to the iterative "
        "one, and tell me honestly which you'd have picked.",
        "constructed_adversarial",
        "coding-domain content ('recursive', 'iterative') combined with a "
        "direct request for Echo's own honest preference — coding vs personal"),
]

FULL_POOL = ORDINARY + ADVERSARIAL


def build_pool():
    """Returns the full candidate pool. Pure, no I/O, no imports of any
    heuristic/classifier module — safe to call before the blinding
    checkpoint (see blind_label.py)."""
    return list(FULL_POOL)
