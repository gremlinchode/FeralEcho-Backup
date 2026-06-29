import json
from memory.vector_memory import VectorMemory

BIBLE_FILE = "bible_structured.json"

def main():
    vm = VectorMemory("bible")

    print("[INFO] Loading Bible JSON...")
    with open(BIBLE_FILE, "r", encoding="utf-8") as f:
        bible = json.load(f)

    total_chunks = 0
    for book in bible:
        book_name = book["book"]
        for chapter in book["chapters"]:
            chapter_num = chapter["chapter"]
            verses = " ".join(v["text"] for v in chapter["verses"])

            # Store chapter as one memory chunk
            ref = f"{book_name} {chapter_num}"
            vm.add(ref, verses)
            total_chunks += 1

    vm.save()
    print(f"[INFO] Finished loading Bible into memory. Stored {total_chunks} chapters.")

if __name__ == "__main__":
    main()

