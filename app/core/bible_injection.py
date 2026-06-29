# app/core/bible_injection.py
# ============================================================
# SCRIPTURE INJECTION LAYER
# Detects Bible citations in prompts and injects real verse
# text from bible_sentiment.json before Echo responds.
# ============================================================

import json
import re
from pathlib import Path

# ── Load verse index ─────────────────────────────────────────
BIBLE_SENTIMENT_FILE = Path(__file__).parent.parent.parent / "bible_sentiment.json"

VERSE_INDEX = {}
with open(BIBLE_SENTIMENT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
    for v in data:
        key = (v["book"], v["chapter"], v["verse"])
        VERSE_INDEX[key] = v["text"]

# ── Book name normalization ───────────────────────────────────
BOOK_ALIASES = {
    "gen": "Genesis", "genesis": "Genesis",
    "exod": "Exodus", "exodus": "Exodus",
    "lev": "Leviticus", "leviticus": "Leviticus",
    "num": "Numbers", "numbers": "Numbers",
    "deut": "Deuteronomy", "deuteronomy": "Deuteronomy",
    "josh": "Joshua", "joshua": "Joshua",
    "judg": "Judges", "judges": "Judges",
    "ruth": "Ruth",
    "1 sam": "1 Samuel", "1 samuel": "1 Samuel",
    "2 sam": "2 Samuel", "2 samuel": "2 Samuel",
    "1 kgs": "1 Kings", "1 kings": "1 Kings",
    "2 kgs": "2 Kings", "2 kings": "2 Kings",
    "1 chr": "1 Chronicles", "1 chronicles": "1 Chronicles",
    "2 chr": "2 Chronicles", "2 chronicles": "2 Chronicles",
    "ezra": "Ezra",
    "neh": "Nehemiah", "nehemiah": "Nehemiah",
    "esth": "Esther", "esther": "Esther",
    "job": "Job",
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "psalms": "Psalms",
    "prov": "Proverbs", "proverbs": "Proverbs",
    "eccl": "Ecclesiastes", "ecclesiastes": "Ecclesiastes",
    "song": "Song of Solomon", "song of solomon": "Song of Solomon",
    "isa": "Isaiah", "isaiah": "Isaiah",
    "jer": "Jeremiah", "jeremiah": "Jeremiah",
    "lam": "Lamentations", "lamentations": "Lamentations",
    "ezek": "Ezekiel", "ezekiel": "Ezekiel",
    "dan": "Daniel", "daniel": "Daniel",
    "hos": "Hosea", "hosea": "Hosea",
    "joel": "Joel",
    "amos": "Amos",
    "obad": "Obadiah", "obadiah": "Obadiah",
    "jon": "Jonah", "jonah": "Jonah",
    "mic": "Micah", "micah": "Micah",
    "nah": "Nahum", "nahum": "Nahum",
    "hab": "Habakkuk", "habakkuk": "Habakkuk",
    "zeph": "Zephaniah", "zephaniah": "Zephaniah",
    "hag": "Haggai", "haggai": "Haggai",
    "zech": "Zechariah", "zechariah": "Zechariah",
    "mal": "Malachi", "malachi": "Malachi",
    "matt": "Matthew", "matthew": "Matthew",
    "mark": "Mark",
    "luke": "Luke",
    "john": "John",
    "acts": "Acts",
    "rom": "Romans", "romans": "Romans",
    "1 cor": "1 Corinthians", "1 corinthians": "1 Corinthians",
    "2 cor": "2 Corinthians", "2 corinthians": "2 Corinthians",
    "gal": "Galatians", "galatians": "Galatians",
    "eph": "Ephesians", "ephesians": "Ephesians",
    "phil": "Philippians", "philippians": "Philippians",
    "col": "Colossians", "colossians": "Colossians",
    "1 thess": "1 Thessalonians", "1 thessalonians": "1 Thessalonians",
    "2 thess": "2 Thessalonians", "2 thessalonians": "2 Thessalonians",
    "1 tim": "1 Timothy", "1 timothy": "1 Timothy",
    "2 tim": "2 Timothy", "2 timothy": "2 Timothy",
    "titus": "Titus",
    "phlm": "Philemon", "philemon": "Philemon",
    "heb": "Hebrews", "hebrews": "Hebrews",
    "jas": "James", "james": "James",
    "1 pet": "1 Peter", "1 peter": "1 Peter",
    "2 pet": "2 Peter", "2 peter": "2 Peter",
    "1 john": "1 John",
    "2 john": "2 John",
    "3 john": "3 John",
    "jude": "Jude",
    "rev": "Revelation", "revelation": "Revelation",
}

def normalize_book(raw: str) -> str:
    return BOOK_ALIASES.get(raw.lower().strip(), None)

# ── Citation detection ────────────────────────────────────────
CITATION_RE = re.compile(
    r'((?:\d\s)?[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?)\s+(\d+):(\d+)(?:-(\d+))?',
    re.IGNORECASE
)

def get_verse_range(book: str, chapter: int, start: int, end: int) -> list:
    verses = []
    for v_num in range(start, end + 1):
        key = (book, chapter, v_num)
        text = VERSE_INDEX.get(key)
        if text:
            text = re.sub(r'\{([^}]*)\}', r'\1', text)
            verses.append((v_num, text))
    return verses

def detect_and_fetch_citations(prompt: str) -> dict:
    results = {}
    for match in CITATION_RE.finditer(prompt):
        raw_book = match.group(1)
        chapter = int(match.group(2))
        start_verse = int(match.group(3))
        end_verse = int(match.group(4)) if match.group(4) else start_verse

        book = normalize_book(raw_book)
        if not book:
            continue

        verses = get_verse_range(book, chapter, start_verse, end_verse)
        if verses:
            ref = f"{book} {chapter}:{start_verse}"
            if end_verse != start_verse:
                ref += f"-{end_verse}"
            results[ref] = verses

    return results

# ── Prompt injection ──────────────────────────────────────────
def inject_scripture(prompt: str) -> str:
    citations = detect_and_fetch_citations(prompt)
    if not citations:
        return prompt

    scripture_block = "\n[INSTRUCTION: The following is the ACTUAL scripture text from the Bible database. You MUST quote directly from these verses when discussing them. Do NOT paraphrase from memory or training data. Use only what is written below.]\n"
    for ref, verses in citations.items():
        scripture_block += f"\n{ref}:\n"
        for v_num, text in verses:
            scripture_block += f"  v{v_num}: {text}\n"

    return prompt + "\n" + scripture_block

# ── Test ──────────────────────────────────────────────────────
if __name__ == "__main__":
    test = "Today's reading is 1 Kings 14:1-3 and Psalm 133:1-3"
    result = inject_scripture(test)
    print(result)
