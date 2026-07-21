"""
Autonomous Fetch for FeralEcho
- Fetches data from multiple sources including current events
- Logs relevant snippets to Echo's memory using log_dream_bridge
- Handles JSON, RSS, and HTML content intelligently
"""
from app.core.temporal_environment import get_temporal_environment_context
from app.core.memory_bridge import log_dream_bridge, retrieve_relevant_memories
import os
import re
import logging
import requests
import time
from bs4 import BeautifulSoup
import feedparser

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# NEWSAPI_KEY/NASA_API_KEY are embedded directly in FETCH_SOURCES URLs below (needed for
# the real request). Found 2026-07-05: every fetch logged the full URL via
# logging.info(f"Fetching ... from {url} ...") — which meant the real API key value was
# written in plaintext to whatever log sink is active (memory/echo_watchdog.log in
# normal operation via start_echo.sh). Redact before logging; never redact the URL
# actually used for the request itself.
_API_KEY_QUERY_PARAM = re.compile(r"([?&](?:api_?key)=)[^&]+", re.IGNORECASE)


def _redact_url_for_log(url: str) -> str:
    return _API_KEY_QUERY_PARAM.sub(r"\1***REDACTED***", url)

# --- Configuration ---
MAX_ITEMS = 3           # max items per source
MAX_TEXT_LEN = 500      # max snippet length
HEADERS = {"User-Agent": "FeralEcho/1.0"}

# Sources that returned 401/403 this run — skipped without retrying rather
# than re-attempting and re-logging the same failure every hourly cycle
# forever. In-memory only (resets on restart); some sources (e.g. Reddit)
# have no key concept at all, so there's nothing to fix by retrying.
_DISABLED_SOURCES: set[str] = set()

# --- API Keys ---
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
NASA_API_KEY = os.getenv("NASA_API_KEY")

# --- Sources ---
FETCH_SOURCES = [
    # ── Knowledge & tech ──────────────────────────────────────────────────────
    ("Wikipedia AI",       "https://en.wikipedia.org/api/rest_v1/page/summary/Artificial_intelligence"),
    ("StackOverflow",      "https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&tagged=python&site=stackoverflow"),
    ("arXiv AI",           "https://arxiv.org/rss/cs.AI"),
    ("arXiv Biology",      "https://arxiv.org/rss/q-bio"),
    ("arXiv Cosmology",    "https://arxiv.org/rss/astro-ph.CO"),

    # ── Current events ────────────────────────────────────────────────────────
    ("BBC News",           "http://feeds.bbci.co.uk/news/rss.xml"),
    ("NPR News",           "https://www.npr.org/rss/rss.php?id=1001"),
    ("The Guardian",       "https://www.theguardian.com/world/rss"),

    # ── Human discourse ───────────────────────────────────────────────────────
    ("Reddit Philosophy",  "https://www.reddit.com/r/philosophy/top.json?limit=3&t=day&raw_json=1"),
    ("Reddit Science",     "https://www.reddit.com/r/science/top.json?limit=3&t=day&raw_json=1"),
    ("Reddit WorldNews",   "https://www.reddit.com/r/worldnews/top.json?limit=3&t=day&raw_json=1"),

    # ── Cosmos & history ──────────────────────────────────────────────────────
    ("This Day History",   "https://history.muffinlabs.com/date"),
]

# Add NASA APOD only if a real API key is set — DEMO_KEY has a 30 req/hour cap
# and will 429 on any autonomous loop running more than once per two hours.
# Get a free key at https://api.nasa.gov/
if NASA_API_KEY:
    FETCH_SOURCES.append(
        ("NASA APOD", f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}")
    )
else:
    logging.debug("No NASA_API_KEY found — NASA APOD source skipped (set NASA_API_KEY env var to enable).")

# Add NewsAPI if key is present and non-empty
if NEWSAPI_KEY:
    FETCH_SOURCES.append(
        ("NewsAPI US", f"https://newsapi.org/v2/top-headlines?country=us&pageSize={MAX_ITEMS}&apiKey={NEWSAPI_KEY}")
    )
else:
    logging.debug("No NEWSAPI_KEY found — NewsAPI source skipped.")

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

_FETCH_META = {"memory_source": "autonomous", "role": "fetch"}


def _is_error_response(data) -> bool:
    """True if the JSON payload looks like an API error rather than real content."""
    if isinstance(data, dict):
        # Common error key patterns across APIs
        if any(k in data for k in ("error", "message", "fault", "status")) and \
                not any(k in data for k in ("articles", "items", "results", "entries")):
            return True
        # Empty dict
        if not data:
            return True
    if isinstance(data, list) and not data:
        return True
    return False


# --- Fetch & Log Function ---
def fetch_and_log(name, url, max_retries=3, temporal_context=None) -> list[str]:
    """
    Fetch data from URL, log unique snippets to Echo's memory, return
    collected text snippets (only snippets that were actually stored).

    temporal_context: pass a pre-built context string to avoid redundant
    API calls when iterating over multiple sources in a single cycle.
    """
    WEATHER_KEY = os.environ.get("OPENWEATHER_API_KEY")

    if name in _DISABLED_SOURCES:
        logging.debug(f"{name}: previously failed auth/access this run — skipping without retrying.")
        return []

    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Fetching {name} from {_redact_url_for_log(url)} (Attempt {attempt})")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")

            # Use cached context if provided, otherwise fetch once per source
            ctx = temporal_context or get_temporal_environment_context(weather_api_key=WEATHER_KEY)

            collected: list[str] = []

            # --- JSON ---
            if "application/json" in content_type:
                data = response.json()

                # FIX #5: skip error payloads before they reach memory
                if _is_error_response(data):
                    logging.warning(f"[FETCH] {name} returned error payload, skipping: {str(data)[:120]}")
                    return []

                if isinstance(data, dict) and "articles" in data:
                    # NewsAPI
                    for art in data["articles"][:MAX_ITEMS]:
                        snippet = f"[{name}] {art.get('title', '')[:MAX_TEXT_LEN]}"
                        if not _is_duplicate(snippet):
                            log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                            collected.append(snippet)

                elif (isinstance(data, dict) and "data" in data
                        and isinstance(data["data"], dict)
                        and "children" in data["data"]):
                    # Reddit listing format
                    for child in data["data"]["children"][:MAX_ITEMS]:
                        post = child.get("data", {})
                        title = post.get("title", "")
                        subreddit = post.get("subreddit_name_prefixed", "")
                        snippet = f"[{name}] {subreddit}: {title[:MAX_TEXT_LEN]}"
                        if not _is_duplicate(snippet):
                            log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                            collected.append(snippet)

                elif isinstance(data, dict) and "explanation" in data:
                    # NASA APOD
                    title = data.get("title", "")
                    explanation = data.get("explanation", "")[:MAX_TEXT_LEN]
                    date = data.get("date", "")
                    snippet = f"[{name}] {date} — {title}: {explanation}"
                    if not _is_duplicate(snippet):
                        log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                        collected.append(snippet)

                elif (isinstance(data, dict) and "data" in data
                        and isinstance(data.get("data"), dict)
                        and "Events" in data["data"]):
                    # This Day in History (muffinlabs)
                    events = data["data"].get("Events", [])
                    for event in events[:MAX_ITEMS]:
                        year = event.get("year", "?")
                        text = event.get("text", "")[:MAX_TEXT_LEN]
                        snippet = f"[{name}] {year}: {text}"
                        if not _is_duplicate(snippet):
                            log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                            collected.append(snippet)

                elif isinstance(data, dict) and isinstance(data.get("items"), list):
                    # StackOverflow Questions API. Found and fixed 2026-07-21:
                    # this shape had no case here at all, so every
                    # StackOverflow entry fell through to the generic dump
                    # below — a raw repr of the whole response, including
                    # irrelevant internals like owner profile-image URLs,
                    # instead of the real, useful title field confirmed live
                    # against the actual API before writing this fix.
                    for item in data["items"][:MAX_ITEMS]:
                        title = item.get("title", "")
                        score = item.get("score", 0)
                        answered = "answered" if item.get("is_answered") else "unanswered"
                        snippet = f"[{name}] {title[:MAX_TEXT_LEN]} (score {score}, {answered})"
                        if not _is_duplicate(snippet):
                            log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                            collected.append(snippet)

                elif isinstance(data, dict) and "extract" in data:
                    # Wikipedia REST summary API. Found and fixed 2026-07-21:
                    # same class of gap as StackOverflow above — this shape
                    # had no case here either, so entries stored a raw dict
                    # repr with embedded HTML markup (displaytitle) instead
                    # of the real, well-written extract field confirmed live
                    # against the actual API before writing this fix.
                    title = data.get("title", "")
                    extract = data.get("extract", "")[:MAX_TEXT_LEN]
                    snippet = f"[{name}] {title}: {extract}"
                    if not _is_duplicate(snippet):
                        log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                        collected.append(snippet)

                elif isinstance(data, list):
                    for item in data[:MAX_ITEMS]:
                        text = item.get("title") if isinstance(item, dict) else str(item)
                        snippet = f"[{name}] {str(text)[:MAX_TEXT_LEN]}"
                        if not _is_duplicate(snippet):
                            log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                            collected.append(snippet)

                else:
                    snippet = f"[{name}] {str(data)[:MAX_TEXT_LEN]}"
                    if not _is_duplicate(snippet):
                        log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                        collected.append(snippet)

            # --- RSS / XML ---
            elif "xml" in content_type or "rss" in content_type:
                feed = feedparser.parse(response.text)
                for entry in feed.entries[:MAX_ITEMS]:
                    # FIX #2: safe attribute access — not all feeds have title/link
                    title = getattr(entry, "title", None) or entry.get("title", "Untitled")
                    link = getattr(entry, "link", None) or entry.get("link", "")
                    snippet = f"[{name}] {str(title)[:MAX_TEXT_LEN]}"
                    if link:
                        snippet += f" - {link}"
                    if not _is_duplicate(snippet):
                        log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                        collected.append(snippet)  # FIX #1

            # --- HTML ---
            else:
                soup = BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("p")
                text = " ".join([p.get_text() for p in paragraphs[:MAX_ITEMS]])
                snippet = f"[{name}] {text[:MAX_TEXT_LEN]}"
                if not _is_duplicate(snippet):
                    log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                    collected.append(snippet)  # FIX #1

            logging.info(f"[FETCH] {name}: {len(collected)} unique snippet(s) stored")
            return collected

        except requests.HTTPError as he:
            if response.status_code in (401, 403):
                logging.error(f"{name}: Unauthorized or forbidden (check API key). Disabling for the rest of this run.")
                _DISABLED_SOURCES.add(name)
                break
            if response.status_code == 429:
                logging.warning(f"{name}: Rate limited (429) — aborting retries to avoid burning quota.")
                break
            logging.error(f"HTTP error for {name}: {he}")
        except Exception as e:
            logging.error(f"Failed fetch {name}: {e}")

        time.sleep(2)

    log_dream_bridge(f"[{name}] Failed after {max_retries} attempts", meta=_FETCH_META)
    return []


# --- Hacker News (two-step fetch, not in FETCH_SOURCES) ---
def _fetch_hackernews(temporal_context=None) -> list[str]:
    """Fetch HN top stories: one call for IDs, one per item. Returns stored snippets."""
    collected: list[str] = []
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers=HEADERS, timeout=10
        )
        resp.raise_for_status()
        top_ids = resp.json()[:MAX_ITEMS]

        WEATHER_KEY = os.environ.get("OPENWEATHER_API_KEY")
        ctx = temporal_context or get_temporal_environment_context(weather_api_key=WEATHER_KEY)

        for story_id in top_ids:
            try:
                item_resp = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    headers=HEADERS, timeout=10
                )
                item_resp.raise_for_status()
                item = item_resp.json()
                if not isinstance(item, dict) or item.get("type") != "story":
                    continue
                title = item.get("title", "")
                url = item.get("url", "")
                score = item.get("score", 0)
                snippet = f"[Hacker News] {title[:MAX_TEXT_LEN]}"
                if url:
                    snippet += f" ({url})"
                if score:
                    snippet += f" — score {score}"
                if not _is_duplicate(snippet):
                    log_dream_bridge(f"{ctx}\n{snippet}", meta=_FETCH_META, embedding_text=snippet)
                    collected.append(snippet)
            except Exception:
                continue

        logging.info(f"[FETCH] Hacker News: {len(collected)} unique snippet(s) stored")
    except Exception as e:
        logging.error(f"[FETCH] Hacker News failed: {e}")
    return collected


# --- Autonomous Fetch Cycle ---
def run_autonomous_fetch():
    """Iterate over all sources and fetch content. Caches temporal context once."""
    logging.info("Starting autonomous fetch cycle...")
    ctx = get_temporal_environment_context(
        weather_api_key=os.environ.get("OPENWEATHER_API_KEY")
    )
    for name, url in FETCH_SOURCES:
        fetch_and_log(name, url, temporal_context=ctx)
    _fetch_hackernews(temporal_context=ctx)
    logging.info("Autonomous fetch cycle complete.")


# --- Safe Fetch Helper (read-only, no memory logging) ---
def safe_fetch(url: str, max_retries: int = 3) -> str:
    """Returns first item text content or empty string on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                data = response.json()
                if _is_error_response(data):
                    return ""
                if isinstance(data, dict) and "articles" in data:
                    articles = data.get("articles", [])
                    return str(articles[0].get("title", "")) if articles else ""
                elif isinstance(data, list) and data:
                    return str(data[0].get("title", data[0]))
                return str(data)

            elif "xml" in content_type or "rss" in content_type:
                feed = feedparser.parse(response.text)
                if feed.entries:
                    # FIX #2 applied here too
                    title = getattr(feed.entries[0], "title", "Untitled")
                    link = getattr(feed.entries[0], "link", "")
                    return f"{title} - {link}" if link else title
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
