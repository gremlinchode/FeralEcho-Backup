import os
import json
from datetime import datetime, timezone

# Directory of logs to check
LOG_FILES = [
    "memory/dream_bridge.log",
    "memory/memory_journal.log",
    "memory/self_edit_reflections.log",
    "memory/reflection_journal.jsonl",
    "app/core/memory/memory_edit_log.txt",
]

def parse_timestamp(timestamp_str):
    """
    Safely parse a timestamp string to a datetime object.
    Handles ISO 8601, naive, and offset-aware strings.
    """
    try:
        # Remove enclosing brackets if present
        ts = timestamp_str.strip("[]")
        dt = datetime.fromisoformat(ts)
        # Normalize to naive datetime in UTC for consistent sorting
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None

def collect_all_timestamps():
    """
    Iterate through all logs and collect tuples of (datetime, line, file_path)
    """
    all_entries = []

    for file_path in LOG_FILES:
        if not os.path.exists(file_path):
            print(f"[MISSING] {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Attempt to parse timestamp
                dt = None
                if line.startswith("{"):  # JSON line
                    try:
                        data = json.loads(line)
                        if "timestamp" in data:
                            dt = parse_timestamp(data["timestamp"])
                    except json.JSONDecodeError:
                        pass
                else:  # Possibly bracketed timestamp
                    dt = parse_timestamp(line.split(" ")[0])

                if dt is None:
                    print(f"[WARN] Failed to parse timestamp: {line}")
                    continue

                all_entries.append((dt, line, file_path))

    return sorted(all_entries, key=lambda x: x[0])

if __name__ == "__main__":
    all_entries = collect_all_timestamps()
    for dt, line, file_path in all_entries:
        print(f"[{dt}] {file_path}: {line}")

