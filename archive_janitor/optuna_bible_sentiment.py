import json
from pathlib import Path
from tqdm import tqdm
from textblob import TextBlob  # Or replace with any other sentiment analyzer

# Paths
BIBLE_FILE = Path("bible_structured.json")
OUTPUT_FILE = Path("bible_sentiment.json")

# Config
BATCH_SIZE = 128  # Number of verses per batch

# Load Bible
with open(BIBLE_FILE, "r", encoding="utf-8") as f:
    bible_data = json.load(f)

# Flatten verses with reference info
verses = [
    {
        "book": book["name"],
        "chapter": chap_num,
        "verse": verse_num,
        "text": verse
    }
    for book in bible_data
    for chap_num, chapter in enumerate(book["chapters"], start=1)
    for verse_num, verse in enumerate(chapter, start=1)
]

print(f"Total verses: {len(verses)}")

# Load previous results if exist (for resuming)
if OUTPUT_FILE.exists():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)
    processed = {(r["book"], r["chapter"], r["verse"]) for r in results}
    print(f"Resuming, already processed {len(processed)} verses")
else:
    results = []
    processed = set()

# Process in batches with a progress bar
for i in tqdm(range(0, len(verses), BATCH_SIZE), desc="Processing batches"):
    batch = verses[i:i + BATCH_SIZE]
    batch_results = []

    for v in batch:
        key = (v["book"], v["chapter"], v["verse"])
        if key in processed:
            continue

        # Sentiment analysis
        blob = TextBlob(v["text"])
        sentiment = blob.sentiment.polarity  # -1 (negative) to 1 (positive)

        batch_results.append({
            "book": v["book"],
            "chapter": v["chapter"],
            "verse": v["verse"],
            "text": v["text"],
            "sentiment": sentiment
        })

    results.extend(batch_results)
    processed.update((r["book"], r["chapter"], r["verse"]) for r in batch_results)

    # Save after each batch to allow resuming
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

print("All batches completed!")

