"""
Autonomous Fetch for FeralEcho
- Fetches data from multiple sources including current events
- Logs relevant snippets to Echo's memory using log_dream_bridge
- Handles JSON, RSS, and HTML content intelligently
- Includes NewsAPI key for US news headlines
"""
from app.core.temporal_environment import get_temporal_environment_context
from app.core.memory_bridge import log_dream_bridge, retrieve_relevant_memories
import os
import logging
import requests
import time
from bs4 import BeautifulSoup
import feedparser

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# --- Configuration ---
MAX_ITEMS = 3           # max items per source
MAX_TEXT_LEN = 500      # max snippet length
HEADERS = {"User-Agent": "FeralEcho/1.0"}

# --- NewsAPI Key ---
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# --- Sources ---
FETCH_SOURCES = [
    # Static informational sources
    ("Wikipedia AI", "https://en.wikipedia.org/api/rest_v1/page/summary/Artificial_intelligence"),
    ("StackOverflow Python", "https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&tagged=python&site=stackoverflow"),
    ("arXiv AI Recent", "https://arxiv.org/list/cs.AI/recent"),

    # Current events RSS feeds
    ("BBC News", "http://feeds.bbci.co.uk/news/rss.xml"),
    ("NPR News", "https://www.npr.org/rss/rss.php?id=1001"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
]

# Add NewsAPI if key is present
if NEWSAPI_KEY:
    FETCH_SOURCES.append(
        ("NewsAPI US", f"https://newsapi.org/v2/top-headlines?country=us&pageSize={MAX_ITEMS}&apiKey={NEWSAPI_KEY}")
    )
else:
    logging.warning("No NEWSAPI_KEY found—NewsAPI source skipped.")

_DEDUP_THRESHOLD = 0.92

def _is_duplicate(snippet: str) -> bool:
    """True if a near-identical snippet already exists in FAISS (cosine > 0.92)."""
    try:
        results = retrieve_relevant_memories(snippet[:100], top_k=1)
        if results and results[0]["score"] > _DEDUP_THRESHOLD:
            logging.debug(f"[FETCH] Dedup skip (score={results[0]['score']:.3f}): {snippet[:60]}")
            return True
    except Exception:
        pass
    return False

_FETCH_META = {"memory_source": "autonomous"}

# --- Fetch & Log Function ---
def fetch_and_log(name, url, max_retries=3) -> list[str]:
    """Fetch data from URL, log to Echo's memory, return collected text snippets."""
    WEATHER_KEY = os.environ.get("OPENWEATHER_API_KEY")
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Fetching {name} from {url} (Attempt {attempt})")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")

            # Temporal context snapshot
            temporal_context = get_temporal_environment_context(weather_api_key=WEATHER_KEY)

            collected: list[str] = []

            # --- JSON ---
            if "application/json" in content_type:
                data = response.json()
                if isinstance(data, dict) and "articles" in data:
                    for art in data["articles"][:MAX_ITEMS]:
                        snippet = f"[{name}] {art.get('title', '')[:MAX_TEXT_LEN]}"
                        if not _is_duplicate(snippet):
                            log_dream_bridge(f"{temporal_context}\n{snippet}", meta=_FETCH_META)
                        collected.append(snippet)
                elif isinstance(data, list):
                    for item in data[:MAX_ITEMS]:
                        text = item.get("title") if isinstance(item, dict) else str(item)
                        snippet = f"[{name}] {text[:MAX_TEXT_LEN]}"
                        if not _is_duplicate(snippet):
                            log_dream_bridge(f"{temporal_context}\n{snippet}", meta=_FETCH_META)
                        collected.append(snippet)
                else:
                    snippet = f"[{name}] {str(data)[:MAX_TEXT_LEN]}"
                    if not _is_duplicate(snippet):
                        log_dream_bridge(f"{temporal_context}\n{snippet}", meta=_FETCH_META)
                    collected.append(snippet)

            # --- RSS / XML ---
            elif "xml" in content_type or "rss" in content_type:
                feed = feedparser.parse(response.text)
                for entry in feed.entries[:MAX_ITEMS]:
                    snippet = f"[{name}] {entry.title[:MAX_TEXT_LEN]} - {entry.link}"
                    if not _is_duplicate(snippet):
                        log_dream_bridge(f"{temporal_context}\n{snippet}", meta=_FETCH_META)
                    collected.append(snippet)

            # --- HTML ---
            else:
                soup = BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("p")
                text = " ".join([p.get_text() for p in paragraphs[:MAX_ITEMS]])
                snippet = f"[{name}] {text[:MAX_TEXT_LEN]}"
                if not _is_duplicate(snippet):
                    log_dream_bridge(f"{temporal_context}\n{snippet}", meta=_FETCH_META)
                collected.append(snippet)

            logging.info(f"Successfully fetched {name}")
            return collected

        except requests.HTTPError as he:
            if response.status_code in (401, 403):
                logging.error(f"{name}: Unauthorized or forbidden (check API key). Skipping.")
                break
            logging.error(f"HTTP error for {name}: {he}")
        except Exception as e:
            logging.error(f"Failed fetch {name}: {e}")

        time.sleep(2)

    log_dream_bridge(f"[{name}] Failed after {max_retries} attempts")
    return []

# --- Autonomous Fetch Cycle ---
def run_autonomous_fetch():
    """Iterate over all sources and fetch content."""
    logging.info("Starting autonomous fetch cycle...")
    for name, url in FETCH_SOURCES:
        fetch_and_log(name, url)
    logging.info("Autonomous fetch cycle complete.")

# --- Safe Fetch Helper ---
def safe_fetch(url: str, max_retries: int = 3) -> str:
    """Returns first item text content or empty string on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = response.json()
                if isinstance(data, dict) and "articles" in data:
                    articles = data.get("articles", [])
                    return str(articles[0].get("title", "")) if articles else ""
                elif isinstance(data, list) and data:
                    return str(data[0].get("title", data[0]))
                return str(data)

            elif "xml" in content_type or "rss" in content_type:
                feed = feedparser.parse(response.text)
                if feed.entries:
                    return f"{feed.entries[0].title} - {feed.entries[0].link}"
                return ""

            else:
                soup = BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("p")
                return " ".join([p.get_text() for p in paragraphs[:MAX_ITEMS]])[:MAX_TEXT_LEN]

        except requests.RequestException:
            continue

    return ""

# --- Quick Test / Manual Run ---
if __name__ == "__main__":
    run_autonomous_fetch()

