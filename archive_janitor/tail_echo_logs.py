# tail_echo_logs.py – real-time Echo log watcher

import time
from pathlib import Path

# -----------------------------
# --- Paths to watch ---------
# -----------------------------
BASE_DIR = Path(__file__).parent
FILES_TO_WATCH = {
    "Self-Edits": BASE_DIR / "memory" / "self_edit_reflections.log",
    "Reflections": BASE_DIR / "memory" / "reflection_journal.jsonl",
    "Memory Journal": BASE_DIR / "memory" / "memory_journal.log"
}

def tail_file(file_path):
    """Generator to tail a file like 'tail -f'."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Move to the end of the file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.2)
                    continue
                yield line
    except FileNotFoundError:
        while True:
            yield f"[WARN] File not found: {file_path}"
            time.sleep(1)

def main():
    print("=== Echo Log Watcher ===")
    tailers = {name: tail_file(path) for name, path in FILES_TO_WATCH.items()}

    try:
        while True:
            for name, generator in tailers.items():
                try:
                    line = next(generator)
                    if line.strip():
                        print(f"[{name}] {line.strip()}")
                except StopIteration:
                    continue
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nExiting Echo log watcher.")

if __name__ == "__main__":
    main()

