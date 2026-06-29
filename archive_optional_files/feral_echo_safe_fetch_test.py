# feral_echo_safe_fetch_test.py
import requests
import logging

# Configure logging so we can see detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def safe_fetch(url):
    """Fetch a URL with proper headers and error handling."""
    headers = {
        "User-Agent": "FeralEchoBot/1.0 (https://example.com/contact)"
        # Wikipedia blocks requests without UA
    }
    try:
        logging.info(f"Fetching {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        logging.info(f"Success: {url}")
        # Show a preview of the content
        logging.debug(response.text[:300])
        return response.text
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

if __name__ == "__main__":
    logging.info("=== Safe Autonomous Fetch Test ===")
    
    # Two test URLs (summary + on-this-day feed)
    urls = [
        "https://en.wikipedia.org/api/rest_v1/page/summary/Artificial_intelligence",
        "https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/09/07"
    ]
    
    for url in urls:
        safe_fetch(url)

