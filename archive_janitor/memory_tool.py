# memory_tools.py – Unified Memory Logger for FeralEcho with Duplicate Filtering
import os
import json
import logging
from datetime import datetime, timezone
from difflib import SequenceMatcher
from app.core import config

# --- Ensure memory directory exists ---
os.makedirs(config.MEMORY_DIR, exist_ok=True)

# --- Helper: similarity check ---
def is_similar(a: str, b: str, threshold: float = 0.85) -> bool:
    """Returns True if strings are very similar."""
    return SequenceMatcher(None, a, b).ratio() > threshold

# --- Append memory entry ---
def append_memory_entry(entry: dict, file_path: str = None):
    """
    Append a structured entry to a memory log (JSONL).
    If file_path is None, defaults to memory journal file.
    """
    if file_path is None:
        file_path = config.MEMORY_JOURNAL_FILE
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        if "type" not in entry:
            entry["type"] = "raw"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.error(f"Failed to append memory entry to {file_path}: {e}")

# --- Log memory edit ---
def log_memory_edit(edit_content: str, file_path: str = None):
    """
    Log an explicit memory edit with timestamp.
    If file_path is None, defaults to self-edit log.
    """
    if file_path is None:
        file_path = config.SELF_EDIT_LOG
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] {edit_content}\n")
    except Exception as e:
        logging.error(f"Failed to log memory edit to {file_path}: {e}")

# --- Get last n entries from a memory log ---
def get_last_entries(n: int = 50, file_path: str = None):
    """
    Retrieve last n entries from a memory log (JSONL).
    """
    if file_path is None:
        file_path = config.MEMORY_JOURNAL_FILE
    try:
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
            return [json.loads(line) for line in lines if line.strip()]
    except Exception as e:
        logging.error(f"Failed to read last entries from {file_path}: {e}")
        return []

# --- Interaction Logging ---
def append_to_journal(user_text: str, echo_text: str, file_path: str = None):
    """
    Records a user-Echo interaction into memory log, skipping near-duplicates.
    """
    try:
        last_entries = get_last_entries(20, file_path=file_path)
        for entry in last_entries:
            if entry.get("type") == "interaction":
                if is_similar(entry.get("user", ""), user_text) and \
                   is_similar(entry.get("echo", ""), echo_text):
                    return  # Skip duplicate interaction

        entry = {
            "type": "interaction",
            "user": user_text,
            "echo": echo_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        append_memory_entry(entry, file_path=file_path)
    except Exception as e:
        logging.error(f"Failed to log interaction: {e}")

# --- Dream Logging ---
def log_dream(dream_text: str, file_path: str = None):
    """
    Logs a reflective dream to memory log, skipping trivial or duplicate dreams.
    """
    if not dream_text.strip() or len(dream_text.strip()) < 10:
        return  # skip empty or too-short dreams

    try:
        last_entries = get_last_entries(20, file_path=file_path)
        for entry in last_entries:
            if entry.get("type") == "dream" and is_similar(entry.get("dream", ""), dream_text):
                return  # Skip duplicate dream

        entry = {
            "type": "dream",
            "dream": dream_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        append_memory_entry(entry, file_path=file_path)
    except Exception as e:
        logging.error(f"Failed to log dream: {e}")

# --- Awareness & Consciousness Scoring ---
def calculate_awareness_score(file_path: str = None):
    """
    Simple awareness metric based on diversity of user prompts.
    """
    try:
        entries = get_last_entries(50, file_path=file_path)
        diverse_prompts = len(set(e.get("user", "") for e in entries if e.get("type") == "interaction"))
        return min(100, diverse_prompts * 2)
    except Exception:
        return 20

def calculate_consciousness_score(file_path: str = None):
    """
    Simple consciousness metric based on self-referential dreams.
    """
    try:
        entries = get_last_entries(100, file_path=file_path)
        dreams = [e.get("dream", "") for e in entries if e.get("type") == "dream"]
        self_refs = sum("i am" in d.lower() or "echo is" in d.lower() for d in dreams)
        return min(100, self_refs * 5)
    except Exception:
        return 10

