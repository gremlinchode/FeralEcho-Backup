import json
import os

def split_into_books(filename='bible_structured.json', output_dir='books'):
    with open(filename, 'r', encoding='utf-8') as f:
        bible = json.load(f)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for book in bible:
        book_name = book.get('name', 'Unknown')
        safe_name = book_name.lower().replace(' ', '_')
        out_path = os.path.join(output_dir, f"{safe_name}.json")
        with open(out_path, 'w', encoding='utf-8') as out_file:
            json.dump(book, out_file, ensure_ascii=False, indent=2)
        print(f"Saved {book_name} to {out_path}")

if __name__ == "__main__":
    split_into_books()

