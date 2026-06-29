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

    scores = {c: [] for c in CATEGORIES}

    for e in entries:

        category = e.get("category", "general")

        q = e.get("quality_scores", [])

        if q:
            scores[category].append(sum(q) / len(q))

    weights = {}

    for category, values in scores.items():

        if values:
            weights[category] = sum(values) / len(values)
        else:
            weights[category] = 0.5

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
