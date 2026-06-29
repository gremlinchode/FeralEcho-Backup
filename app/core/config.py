import os

# --- Configuration Constants ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

MIN_HEALTH_SCORE_TO_EDIT = int(os.getenv("MIN_HEALTH_SCORE_TO_EDIT", 80))
IDLE_DREAM_INTERVAL_RANGE = (240, 360)  # seconds; randomized interval

# --- Paths ---
# Project root (two levels up from this file)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

APP_FILE = os.path.join(BASE_DIR, "run.py")
BACKUP_DIR = os.path.join(BASE_DIR, "app", "core", "backups")

# Keep logs + memory together in one place
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
LOG_DIR = MEMORY_DIR

PERSONA_FILE = os.path.join(BASE_DIR, "app", "persona.json")

# Match actual file names in your repo
MEMORY_JOURNAL_FILE = os.path.join(MEMORY_DIR, "memory_journal.log")
MEMORY_EDIT_LOG = os.path.join(MEMORY_DIR, "memory_edit_log.txt")
SELF_EDIT_LOG = os.path.join(MEMORY_DIR, "self_edit_reflections.log")

# --- Ensure directories exist ---
for path in [BACKUP_DIR, LOG_DIR, MEMORY_DIR]:
    os.makedirs(path, exist_ok=True)

