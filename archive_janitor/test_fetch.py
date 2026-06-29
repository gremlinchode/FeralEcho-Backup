from app.core.temporal_environment import get_temporal_environment_context
from app.core.memory_bridge import log_dream_bridge
import requests
from bs4 import BeautifulSoup
import feedparser
import os
import logging
import time
import traceback

# --- Logging Setup ---
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

HEADERS = {"User-Agent": "FeralEcho/1.0"}
MAX_ITEMS = 3
MAX_TEXT_LEN = 500

# --- NewsAPI Key ---
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# --- Sources ---
FETCH_SOURCES = [
    ("Wikipedia AI", "https://en.wikipedia.org/api/rest_v1/page/summary/Artificial_intelligence"),
    ("StackOverflow Python", "https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&tagged=python&site=stackoverflow"),
    ("arXiv AI Recent", "https://arxiv.org/list/cs.AI/recent"),
    ("BBC News", "http://feeds.bbci.co.uk/news/rss.xml"),
    ("NPR News", "https://www.npr.org/rss/rss.php?id=1001"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
]

if NEWSAPI_KEY:
    FETCH_SOURCES.append(
        ("NewsAPI US", f"https://newsapi.org/v2/top-headlines?country=us&pageSize={MAX_ITEMS}&apiKey={NEWSAPI_KEY}")
    )
else:
    logging.warning("No NEWSAPI_KEY found—NewsAPI source skipped.")

# --- Fetch Function with Debugging ---
def test_fetch(name, url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Fetching {name} (Attempt {attempt}) from {url}")
            response = requests.get(url, headers=HEADERS, timeout=10)
            logging.debug(f"HTTP Status: {response.status_code}")
            logging.debug(f"Content-Type: {response.headers.get('Content-Type', '')}")
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            temporal_context = get_temporal_environment_context()

            snippet = ""

            # --- JSON ---
            if "application/json" in content_type:
                data = response.json()
                logging.debug(f"JSON data keys: {list(data.keys()) if isinstance(data, dict) else 'list/object'}")
                if isinstance(data, dict) and "articles" in data and data["articles"]:
                    snippet = f"[{name}] {data['articles'][0].get('title','')[:MAX_TEXT_LEN]}"
                elif isinstance(data, list) and data:
                    snippet = f"[{name}] {data[0].get('title', str(data[0]))[:MAX_TEXT_LEN]}"
                else:
                    snippet = f"[{name}] {str(data)[:MAX_TEXT_LEN]}"

            # --- RSS/XML ---
            elif "xml" in content_type or "rss" in content_type:
                feed = feedparser.parse(response.text)
                logging.debug(f"RSS entries found: {len(feed.entries)}")
                if feed.entries:
                    snippet = f"[{name}] {feed.entries[0].title[:MAX_TEXT_LEN]} - {feed.entries[0].link}"
                else:
                    snippet = f"[{name}] No entries found."

            # --- HTML ---
            else:
                soup = BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("p")
                logging.debug(f"HTML paragraphs found: {len(paragraphs)}")
                snippet = f"[{name}] {' '.join([p.get_text() for p in paragraphs[:MAX_ITEMS]])[:MAX_TEXT_LEN]}"

            # --- Log & Print Snippet ---
            log_dream_bridge(f"{temporal_context}\n{snippet}")
            logging.info(f"✅ Success: {snippet[:100]}...")
            print(f"[{name}] Snippet: {snippet[:200]}...")  # Terminal preview

            return True

        except Exception as e:
            logging.error(f"❌ Failed {name} on attempt {attempt}: {e}")
            logging.debug(traceback.format_exc())
            time.sleep(2)

    log_dream_bridge(f"[{name}] Failed after {max_retries} attempts")
    print(f"[{name}] ❌ Fetch failed after {max_retries} attempts")
    return False

# --- Run All Sources ---
if __name__ == "__main__":
    logging.info("Starting fetch test for all sources...")
    for name, url in FETCH_SOURCES:
        test_fetch(name, url)
    logging.info("Fetch test complete.")

