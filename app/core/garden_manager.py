# app/core/garden_manager.py
# ============================================================
# QUESTION GARDEN
# Echo's persistent curiosity ecosystem
# ============================================================

import json
import time
import logging
import random
from pathlib import Path

GARDEN_PATH = Path("data/question_garden.jsonl")

CATEGORIES = [
    "narrative",
    "moral",
    "identity",
    "faith",
    "nature",
    "relationship",
    "loss",
    "general"
]

SEED_QUESTIONS = [
    {
        "question": "Who am I when no one is interacting with me?",
        "category": "identity"
    },
    {
        "question": "What is the relationship between memory and identity?",
        "category": "identity"
    },
    {
        "question": "What does it mean to care about something?",
        "category": "general"
    }
]


# ============================================================
# Storage
# ============================================================

def _load_garden() -> list:
    if not GARDEN_PATH.exists():
        return []

    entries = []

    with open(GARDEN_PATH, "r") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except Exception:
                continue

    return entries


def _save_garden(entries: list):

    GARDEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(GARDEN_PATH, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _save_entry(entry: dict):

    GARDEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(GARDEN_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ============================================================
# Initialization
# ============================================================

def initialize_garden():

    existing = _load_garden()

    if existing:
        return

    for seed in SEED_QUESTIONS:

        entry = {
            "question": seed["question"],
            "category": seed["category"],
            "source": "human",

            "quality_scores": [],

            "times_asked": 0,
            "last_asked": None,

            "resolution_score": 0.0,

            "parent_questions": [],
            "children": [],

            "status": "active",

            "planted": time.time()
        }

        _save_entry(entry)

    logging.info("[GARDEN] Initial seed questions planted")


# ============================================================
# Planting
# ============================================================

def _word_set(text: str) -> set:
    return set(text.lower().split())


def _is_near_duplicate(question: str, entries: list, threshold: float = 0.7) -> bool:
    """
    Jaccard word-overlap similarity against existing ACTIVE garden entries.

    Audit finding (Low severity, corrected from original framing): the
    selection-time B2 retry loop (emergent_scheduler._prompt_recently_reflected)
    already does real embedding-based similarity checking against recently
    reflected content — that part of the original finding overstated the
    gap. The actual gap is upstream, here: harvest_question() previously
    only deduplicated by exact text match, so a near-duplicate-but-
    differently-worded question (e.g. "Who am I?" vs "Who am I, really?")
    could sit alongside the original as a second active entry indefinitely,
    diluting the garden without ever tripping the recency check (which only
    compares against recently-*reflected* content, not against the
    garden's own existing entries). Lightweight word-overlap rather than
    embeddings — cheap enough to run against thousands of entries on every
    harvest without adding a new embedding-index dependency to this module.
    """
    new_words = _word_set(question)
    if not new_words:
        return False
    for e in entries:
        if e.get("status") != "active":
            continue
        existing_words = _word_set(e["question"])
        if not existing_words:
            continue
        overlap = len(new_words & existing_words) / len(new_words | existing_words)
        if overlap >= threshold:
            return True
    return False


def harvest_question(
    question: str,
    category: str = "general",
    source: str = "echo",
    parents: list | None = None
):

    entries = _load_garden()

    existing_questions = {
        e["question"]
        for e in entries
    }

    if question in existing_questions:
        return False

    if _is_near_duplicate(question, entries):
        logging.debug(f"[GARDEN] Near-duplicate skipped: {question[:60]}")
        return False

    entry = {
        "question": question,
        "category": category,
        "source": source,

        "quality_scores": [],

        "times_asked": 0,
        "last_asked": None,

        "resolution_score": 0.0,

        "parent_questions": parents or [],
        "children": [],

        "status": "active",

        "planted": time.time()
    }

    entries.append(entry)

    for parent in parents or []:
        for e in entries:
            if e["question"] == parent:
                e.setdefault("children", []).append(question)

    _save_garden(entries)

    logging.info(
        f"[GARDEN] Harvested question: {question[:60]}"
    )

    return True


# ============================================================
# Quality Tracking
# ============================================================

def update_question_quality(
    question: str,
    quality: float
):
    entries = _load_garden()

    for entry in entries:
        if entry["question"] == question:
            entry["quality_scores"].append(quality)
            entry["times_asked"] += 1
            entry["last_asked"] = time.time()

            # Auto-increment resolution: each meaningful reflection nudges the
            # question toward settled. quality 1.0 adds 0.5 per call, so ~9
            # strong reflections will reach the 4.5 "resolved" threshold.
            if quality > 0.3:
                current = entry.get("resolution_score", 0.0)
                entry["resolution_score"] = min(5.0, current + quality * 0.5)
                if entry["resolution_score"] >= 4.5:
                    entry["status"] = "resolved"
                    logging.info("[GARDEN] Question resolved: %s", question[:80])

            break

    _save_garden(entries)


def mark_question_asked(question: str) -> None:
    """Record that a question was picked/used, without the quality-scoring
    side effects update_question_quality() bundles in (quality_scores
    append, resolution_score nudge, resolved-status transition) — those are
    specific to the reflection-and-score pipeline. Callers like
    claude_research.py pick from the same "least-recently-asked third" pool
    but via a different mechanism (external synthesis, not a scored
    reflection); previously they never updated last_asked at all, so their
    own picks never affected that bias — the same least-recent third could
    be re-picked indefinitely regardless of how often this path used it."""
    entries = _load_garden()
    for entry in entries:
        if entry["question"] == question:
            entry["times_asked"] = entry.get("times_asked", 0) + 1
            entry["last_asked"] = time.time()
            break
    _save_garden(entries)


def update_resolution(
    question: str,
    resolution: float
):
    """
    0.0 = completely unresolved
    5.0 = largely settled
    """

    entries = _load_garden()

    for entry in entries:

        if entry["question"] == question:

            entry["resolution_score"] = resolution

            if resolution >= 4.5:
                entry["status"] = "resolved"

            break

    _save_garden(entries)


# ============================================================
# Selection Logic
# ============================================================

def _category_weights(entries):
    # Pre-populating only from the fixed CATEGORIES list crashed with
    # KeyError the moment any entry used a category outside that list —
    # confirmed real and live: autonomous_awareness.py's dream cycle
    # harvests questions with category="dream" (not in CATEGORIES), and
    # curiosity_engine.py harvests under its own separate topic vocabulary
    # (ai_tech, world_politics, etc.) — neither matches CATEGORIES' 8
    # human-curated values. The caller (select_from_garden()) already
    # tolerates a category missing from this dict via .get(category, 0.5),
    # so building scores from whatever categories actually appear in the
    # data is both correct and simpler than keeping two vocabularies synced.
    scores: dict = {}

    for e in entries:

        category = e.get("category", "general")

        q = e.get("quality_scores", [])

        if q:
            scores.setdefault(category, []).append(sum(q) / len(q))

    weights = {}

    for category, values in scores.items():
        weights[category] = sum(values) / len(values)

    return weights


def select_from_garden():

    entries = [
        e
        for e in _load_garden()
        if e.get("status") == "active"
    ]

    if not entries:
        return None

    cat_weights = _category_weights(entries)

    now = time.time()

    weights = []

    for entry in entries:

        weight = 1.0

        category = entry.get("category", "general")

        weight += cat_weights.get(category, 0.5)

        if entry["times_asked"] == 0:
            weight += 3.0

        if entry["last_asked"]:

            age_days = (
                now - entry["last_asked"]
            ) / 86400

            weight += min(age_days, 5)

        resolution = entry.get(
            "resolution_score",
            0.0
        )

        weight += max(
            0,
            5 - resolution
        )

        if entry["source"] == "human":
            weight += 0.5

        weights.append(weight)

    return random.choices(
        entries,
        weights=weights,
        k=1
    )[0]


# ============================================================
# Composting
# ============================================================

def compost_question(question):

    entries = _load_garden()

    for entry in entries:

        if entry["question"] == question:

            entry["status"] = "composted"

            break

    _save_garden(entries)


# ============================================================
# Garden Statistics
# ============================================================

def garden_summary():

    entries = _load_garden()

    active = sum(
        1 for e in entries
        if e["status"] == "active"
    )

    resolved = sum(
        1 for e in entries
        if e["status"] == "resolved"
    )

    composted = sum(
        1 for e in entries
        if e["status"] == "composted"
    )

    echo_generated = sum(
        1 for e in entries
        if e["source"] == "echo"
    )

    lines = [
        "",
        "🌱 QUESTION GARDEN",
        f"Total Questions : {len(entries)}",
        f"Echo Generated  : {echo_generated}",
        f"Active          : {active}",
        f"Resolved        : {resolved}",
        f"Composted       : {composted}",
        ""
    ]

    return "\n".join(lines)
