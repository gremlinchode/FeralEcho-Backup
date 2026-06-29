#!/usr/bin/env python3
import json
from pathlib import Path
from tqdm import tqdm
import logging
import time
from app.core.memory_bridge import add_to_vector_memory

logging.basicConfig(level=logging.INFO)

BOOKS_FOLDER = Path("./books")  # adjust path if needed
CHECKPOINT_FILE = Path("./bible_send_checkpoint.json")
CHUNK_SIZE = 500  # number of words per chunk, adjust as needed
RETRY_LIMIT = 3   # number of retries on failure

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_checkpoint(checkpoint):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)

def chunk_text(text, chunk_size=CHUNK_SIZE):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])

def send_book(book_path: Path, start_chapter=0):
    with open(book_path, "r", encoding="utf-8") as f:
        book_data = json.load(f)

    book_name = book_path.stem.replace("_", " ").title()
    chapters_list = book_data.get("chapters") if isinstance(book_data, dict) else book_data

    if not chapters_list:
        logging.warning(f"No chapters found in {book_path.name}")
        return 0

    total_chapters = 0
    for i, chapter in enumerate(tqdm(chapters_list, desc=f"Processing {book_name}")):
        if i < start_chapter:
            continue  # skip already sent chapters

        if isinstance(chapter, dict):
            chapter_num = chapter.get("chapter", i + 1)
            verses_list = chapter.get("verses", [])
            verses_text = " ".join(v.get("text") if isinstance(v, dict) else str(v) for v in verses_list)
        else:
            chapter_num = i + 1
            verses_text = str(chapter)

        # Chunk the text to avoid embedding overload
        for j, chunk in enumerate(chunk_text(verses_text)):
            ref = f"{book_name} {chapter_num} (chunk {j+1})"
            for attempt in range(RETRY_LIMIT):
                try:
                    add_to_vector_memory(ref, chunk)
                    break
                except Exception as e:
                    logging.warning(f"Attempt {attempt+1} failed for {ref}: {e}")
                    time.sleep(1)
            else:
                logging.error(f"Failed to add {ref} after {RETRY_LIMIT} attempts")

        # Save checkpoint after each chapter
        total_chapters += 1
        checkpoint[book_name] = start_chapter + total_chapters
        save_checkpoint(checkpoint)

    return total_chapters

def main():
    global checkpoint
    checkpoint = load_checkpoint()

    book_files = sorted(BOOKS_FOLDER.glob("*.json"))
    for book_path in book_files:
        book_name = book_path.name
        start_chapter = checkpoint.get(book_name, 0)
        logging.info(f"Sending book: {book_name} starting at chapter {start_chapter + 1}")
        send_book(book_path, start_chapter=start_chapter)

    logging.info("Bible sending complete.")

if __name__ == "__main__":
    main()

