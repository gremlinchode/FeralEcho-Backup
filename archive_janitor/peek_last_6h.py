# peek_last_6h.py
import json
from datetime import datetime, timezone, timedelta
import os
from app.core.config import MEMORY_JOURNAL_FILE

# --- Configuration ---
HOURS_BACK = 6
MEMORY_JOURNAL = MEMORY_JOURNAL_FILE

# --- Load recent entries ---
def load_recent_entries(file_path, hours=HOURS_BACK):
    if not file_path or not os.path.exists(file_path):
        print(f"No memory file found at {file_path}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent_entries = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts_str = entry.get("timestamp")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str)
                    if ts >= cutoff:
                        recent_entries.append(entry)
            except json.JSONDecodeError:
                continue
    return recent_entries

# --- Categorize entries ---
def categorize_entries(entries):
    reflections = [e for e in entries if e.get("role") == "dream"]
    python_practice = [e for e in entries if e.get("role") == "python"]
    interactions = [e for e in entries if e.get("role") in ("user", "echo")]
    return reflections, python_practice, interactions

# --- Print entries ---
def print_entries(title, entries):
    print(f"\n--- {title} ({len(entries)} found) ---\n")
    for e in sorted(entries, key=lambda x: x.get("timestamp", "")):
        ts = e.get("timestamp")
        text = e.get("text", "")
        source = e.get("role", "unknown")
        print(f"[{ts}] ({source}) {text}\n")

# --- Main ---
if __name__ == "__main__":
    all_entries = load_recent_entries(MEMORY_JOURNAL)
    reflections, python_practice, interactions = categorize_entries(all_entries)

    print_entries("Reflections / Dreams", reflections)
    print_entries("Python Practice", python_practice)
    print_entries("User / Echo Interactions", interactions)

