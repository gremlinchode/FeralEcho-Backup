import json
import time
import gc
import os
import multiprocessing
import warnings
from app.core.memory_bridge import add_to_vector_memory

# ----- CONFIGURATION -----
BIBLE_FILE = "bible_structured.json"
CHECKPOINT_FILE = "bible_checkpoint.json"

CHAPTER_BATCH_SIZE = 10       # books per batch
VERSE_CHUNK_SIZE = 400        # verses per vector memory chunk
SLEEP_BETWEEN_CHUNKS = 0.05   # small pause to reduce pressure

# ----- SETUP (macOS fix) -----
multiprocessing.set_start_method("spawn", force=True)

# Suppress macOS multiprocessing semaphore warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="multiprocessing.resource_tracker"
)

# ----- FUNCTIONS -----
def load_bible(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            print("⚠️ Checkpoint file is corrupted. Starting fresh.")
    return {
        "chunk_id": 1,
        "book_index": 0
    }

def save_checkpoint(state):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)

def flush_chunk(verse_chunk, chunk_id):
    try:
        text = "\n".join(verse_chunk)
        add_to_vector_memory(f"Bible Chunk {chunk_id}\n{text}")
        print(f"✅ Added chunk {chunk_id} ({len(verse_chunk)} verses)")
        return True
    except Exception as e:
        print(f"❌ Error in chunk {chunk_id}: {e}")
        return False

# ----- MAIN INGESTION -----
def ingest_bible():
    bible = load_bible(BIBLE_FILE)
    state = load_checkpoint()
    
    chunk_id = state["chunk_id"]
    book_index = state["book_index"]
    total_verses = 0

    print(f"📖 Starting Bible ingestion from book {book_index}, chunk {chunk_id}")

    for batch_start in range(book_index, len(bible), CHAPTER_BATCH_SIZE):
        batch_end = min(batch_start + CHAPTER_BATCH_SIZE, len(bible))
        book_batch = bible[batch_start:batch_end]
        batch_verses = []

        for book in book_batch:
            book_abbrev = book.get("abbrev", "Unknown")
            chapters = book.get("chapters", [])
            for chapter_index, chapter in enumerate(chapters, start=1):
                for verse_index, verse_text in enumerate(chapter, start=1):
                    reference = f"{book_abbrev} {chapter_index}:{verse_index}"
                    batch_verses.append(f"{reference} - {verse_text}")
                    total_verses += 1

        for i in range(0, len(batch_verses), VERSE_CHUNK_SIZE):
            verse_chunk = batch_verses[i:i + VERSE_CHUNK_SIZE]
            success = flush_chunk(verse_chunk, chunk_id)

            if not success:
                print(f"⚠️ Skipping failed chunk {chunk_id}")
            
            chunk_id += 1
            save_checkpoint({
                "chunk_id": chunk_id,
                "book_index": batch_end
            })

            # Cleanup
            del verse_chunk
            gc.collect()
            time.sleep(SLEEP_BETWEEN_CHUNKS)

        # Cleanup batch
        del batch_verses
        gc.collect()

    print(f"🎉 Bible ingestion complete. Total verses ingested: {total_verses}")

    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("🧹 Checkpoint file removed.")


# ----- RUN -----
if __name__ == "__main__":
    ingest_bible()

