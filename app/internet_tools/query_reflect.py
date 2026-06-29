import os

LOG_DIR = "memory/internet_logs"

def echo_query_reflect(keyword: str):
    """
    Search through internet log files for a keyword and return matching lines.
    """
    results = []
    if not os.path.exists(LOG_DIR):
        return [f"[WARN] Log directory not found: {LOG_DIR}"]

    for fname in os.listdir(LOG_DIR):
        fpath = os.path.join(LOG_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r", errors="ignore") as f:
            for line in f:
                if keyword.lower() in line.lower():
                    results.append(f"[{fname}] {line.strip()}")

    if not results:
        results.append(f"[INFO] No results found for keyword: {keyword}")
    return results

