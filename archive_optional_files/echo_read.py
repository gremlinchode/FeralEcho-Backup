#!/usr/bin/env python3
import json
from pathlib import Path
from tqdm import tqdm
import logging
import time
from app.core.memory_bridge import add_to_vector_memory

logging.basicConfig(level=logging.INFO)

FERALECHO_FOLDER = Path("./")  # Root folder of FeralEcho
CHECKPOINT_FILE = Path("./feralecho_read_checkpoint.json")
CHUNK_SIZE = 500  # words per chunk
RETRY_LIMIT = 3
MAX_FILE_SIZE_MB = 5  # skip files larger than 5MB to avoid crashes

# Allowed text-based file types
ALLOWED_EXTENSIONS = [".json", ".txt", ".md", ".py"]

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

def read_file(file_path: Path):
    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        logging.info(f"Skipping unsupported file type: {file_path}")
        return None

    if file_path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        logging.info(f"Skipping large file (> {MAX_FILE_SIZE_MB} MB): {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.suffix.lower() == ".json":
                data = json.load(f)
                return json.dumps(data)  # flatten JSON to string
            else:
                return f.read()
    except Exception as e:
        logging.warning(f"Failed to read {file_path}: {e}")
        return None

def send_file(file_path: Path, start_chunk=0):
    content = read_file(file_path)
    if not content:
        return 0

    chunks = list(chunk_text(content))
    total_chunks = 0
    for i, chunk in enumerate(tqdm(chunks, desc=f"Processing {file_path.name}")):
        if i < start_chunk:
            continue

        ref = f"{file_path.name} (chunk {i+1})"
        for attempt in range(RETRY_LIMIT):
            try:
                add_to_vector_memory(ref, chunk)
                break
            except Exception as e:
                logging.warning(f"Attempt {attempt+1} failed for {ref}: {e}")
                time.sleep(1)
        else:
            logging.error(f"Failed to add {ref} after {RETRY_LIMIT} attempts")

        total_chunks += 1
        checkpoint[file_path.name] = start_chunk + total_chunks
        save_checkpoint(checkpoint)

    return total_chunks

def main():
    global checkpoint
    checkpoint = load_checkpoint()

    file_paths = sorted(FERALECHO_FOLDER.rglob("*.*"))
    for file_path in file_paths:
        start_chunk = checkpoint.get(file_path.name, 0)
        logging.info(f"Sending file: {file_path.name} starting at chunk {start_chunk + 1}")
        send_file(file_path, start_chunk=start_chunk)

    logging.info("FeralEcho reading complete.")

if __name__ == "__main__":
    main()

