import json
import os

file_path = os.path.join(os.path.dirname(__file__), "bible_structured.json")

try:
    with open(file_path, "r") as f:
        bible_data = json.load(f)

    print("✅ JSON loaded successfully!")

    # Check top-level structure
    if isinstance(bible_data, list):
        print(f"Number of books: {len(bible_data)}")
        for book in bible_data[:3]:  # Just check first 3 books to avoid massive print
            print(f"- Book name: {book.get('name')}")
            chapters = book.get("chapters")
            if isinstance(chapters, list):
                print(f"  Chapters: {len(chapters)}")
                for chapter_idx, chapter in enumerate(chapters[:2], start=1):  # first 2 chapters
                    print(f"    Chapter {chapter_idx} verses: {len(chapter)}")
            else:
                print("  ❌ Chapters not a list!")
    else:
        print("❌ Top-level JSON is not a list of books!")

except json.JSONDecodeError as e:
    print("❌ JSON is invalid!")
    print("Error:", e)

