from bible_module import (
    get_verse,
    get_book_sentiment,
    get_most_positive_verse,
    get_most_negative_verse
)

def query_bible(reference=None, book=None, chapter=None, verse=None, sentiment=None):
    """
    Echo-friendly interface to Bible data.
    
    Returns a consistent dict with:
    {
        "book": str,
        "chapter": int | None,
        "verse": int | None,
        "text": str | None,
        "sentiment": float | None
    }

    Options:
    - reference: "most_positive" or "most_negative"
    - book/chapter/verse: specify integers/strings for a specific verse
    - sentiment: "average" for book sentiment
    """
    result = {
        "book": None,
        "chapter": None,
        "verse": None,
        "text": None,
        "sentiment": None
    }

    if reference == "most_positive":
        data = get_most_positive_verse(book)
        if data:
            result.update({
                "book": data[0],
                "chapter": data[1],
                "verse": data[2],
                "text": data[3],
                "sentiment": data[4]
            })
    elif reference == "most_negative":
        data = get_most_negative_verse(book)
        if data:
            result.update({
                "book": data[0],
                "chapter": data[1],
                "verse": data[2],
                "text": data[3],
                "sentiment": data[4]
            })
    elif sentiment == "average" and book:
        avg_sent = get_book_sentiment(book)
        result.update({
            "book": book,
            "sentiment": avg_sent
        })
    elif book and chapter and verse:
        v = get_verse(book, chapter, verse)
        if v["text"] is not None:
            result.update({
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "text": v["text"],
                "sentiment": v["sentiment"]
            })

    return result

