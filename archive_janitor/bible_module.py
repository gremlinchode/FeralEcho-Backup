# bible_module.py
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random
import logging

# -----------------------------
# --- Paths and Data ----------
# -----------------------------
BIBLE_SENTIMENT_FILE = Path("bible_sentiment.json")
ART_OUTPUT_DIR = Path("data/bible_art")
ART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the Bible sentiment data
with open(BIBLE_SENTIMENT_FILE, "r", encoding="utf-8") as f:
    bible_sentiment_data = json.load(f)

# Index data for fast lookup
VERSE_INDEX = {}
for v in bible_sentiment_data:
    key = (v["book"], v["chapter"], v["verse"])
    VERSE_INDEX[key] = {"text": v["text"], "sentiment": v["sentiment"]}

# -----------------------------
# --- Basic Verse Functions ---
# -----------------------------
def get_verse(book: str, chapter: int, verse: int):
    """Return the text and sentiment of a specific verse."""
    key = (book, chapter, verse)
    return VERSE_INDEX.get(key, {"text": None, "sentiment": None})

def get_book_sentiment(book: str):
    """Return average sentiment for a given book."""
    verses = [v["sentiment"] for k, v in VERSE_INDEX.items() if k[0] == book]
    if not verses:
        return None
    return sum(verses) / len(verses)

def get_most_positive_verse(book: str = None):
    """Return the verse with the highest sentiment. Optionally limit to a book."""
    candidates = [(k, v["sentiment"]) for k, v in VERSE_INDEX.items() if book is None or k[0] == book]
    if not candidates:
        return None
    best_key, best_sentiment = max(candidates, key=lambda x: x[1])
    return best_key + (VERSE_INDEX[best_key]["text"], best_sentiment)

def get_most_negative_verse(book: str = None):
    """Return the verse with the lowest sentiment. Optionally limit to a book."""
    candidates = [(k, v["sentiment"]) for k, v in VERSE_INDEX.items() if book is None or k[0] == book]
    if not candidates:
        return None
    worst_key, worst_sentiment = min(candidates, key=lambda x: x[1])
    return worst_key + (VERSE_INDEX[worst_key]["text"], worst_sentiment)

# -----------------------------
# --- Bible Art Generation ----
# -----------------------------
def generate_bible_art(book=None, chapter=None, verse=None, reference=None):
    """
    Generate a simple image of a Bible verse.
    - book/chapter/verse: specific verse
    - reference: 'most_positive' or 'most_negative'
    Returns the path to the generated image.
    """
    # Select the verse
    if reference == "most_positive":
        v = get_most_positive_verse(book)
    elif reference == "most_negative":
        v = get_most_negative_verse(book)
    elif book and chapter and verse:
        verse_data = get_verse(book, chapter, verse)
        v = (book, chapter, verse, verse_data["text"], verse_data["sentiment"])
    else:
        # Random verse if nothing specified
        key, val = random.choice(list(VERSE_INDEX.items()))
        v = (key[0], key[1], key[2], val["text"], val["sentiment"])

    b, c, v_num, text, sent = v

    # Create image
    img = Image.new("RGB", (800, 600), color=(255, 255, 240))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    # Wrap text for display
    lines = []
    line_len = 60
    for i in range(0, len(text), line_len):
        lines.append(text[i:i + line_len])
    wrapped_text = "\n".join(lines)

    draw.text((20, 20), f"{b} {c}:{v_num}\n\n{wrapped_text}", fill="black", font=font)

    # Save image with safe filename
    safe_book = b.replace(" ", "_")
    filename = ART_OUTPUT_DIR / f"{safe_book}_{c}_{v_num}.png"
    img.save(filename)
    logging.info(f"[BIBLE ART] Generated art → {filename}")

    return filename
