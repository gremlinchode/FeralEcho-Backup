# app/core/dark_light_pipeline.py
import requests
import logging
from datetime import datetime
from app.core.memory_bridge import add_to_vector_memory

logging.basicConfig(level=logging.INFO)

# --- Configuration ---
NEWS_API_KEY = "YOUR_NEWS_API_KEY"  # Replace with your API key
NEWS_ENDPOINT = "https://newsapi.org/v2/top-headlines"
NEWS_COUNTRIES = ["us", "gb", "ca"]  # Example countries
CATEGORY_TAGS = {
    "good": ["innovation", "humanitarian", "science", "environment"],
    "bad": ["crime", "scandal", "corruption", "war"],
    "ugly": ["disaster", "accident", "collapse", "pollution"]
}

# -----------------------------
# --- Fetching & Processing ---
# -----------------------------

def fetch_breaking_news():
    events = []
    for country in NEWS_COUNTRIES:
        try:
            response = requests.get(
                NEWS_ENDPOINT,
                params={"apiKey": NEWS_API_KEY, "country": country, "pageSize": 10},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            for article in data.get("articles", []):
                events.append(process_article(article))
        except requests.RequestException as e:
            logging.error(f"Failed fetch news for {country}: {e}")
    return events

def process_article(article):
    title = article.get("title", "")
    description = article.get("description", "")
    content = f"{title}. {description}"
    tag = classify_event(content)
    event = {
        "title": title,
        "description": description,
        "content": content,
        "tag": tag,
        "source": article.get("source", {}).get("name", "unknown"),
        "url": article.get("url"),
        "timestamp": datetime.utcnow().isoformat()
    }
    add_to_vector_memory(f"[{tag.upper()}] {content}")
    logging.info(f"Processed event: {title} | Tag: {tag}")
    return event

def classify_event(text):
    lower = text.lower()
    for tag, keywords in CATEGORY_TAGS.items():
        if any(word in lower for word in keywords):
            return tag
    return "neutral"

# -----------------------------
# --- Entry Point -------------
# -----------------------------

def run_pipeline():
    logging.info("Running Dark/Light pipeline...")
    events = fetch_breaking_news()
    logging.info(f"Fetched and processed {len(events)} events.")
    return events

# -----------------------------
# --- Example Usage ----------
# -----------------------------
if __name__ == "__main__":
    run_pipeline()

