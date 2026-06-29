import os
import shutil
import ast
import json
import hashlib
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import time
from jsonschema import validate, ValidationError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import schedule

# ---------------- CONFIGURATION ----------------
CONFIG_FILE = "feralecho_config.json"
MANIFEST_FILE = "feral_echo_manifest.json"
DEFAULT_CONFIG = {
    "base_dir": "/Users/richietate/Desktop/FeralEcho",
    "check_interval": 3600,  # seconds
    "tmp_max_age_days": 7,
    "log_keep_count": 50,
    "free_space_threshold_gb": 20,
    "code_extensions": [".py", ".js", ".ts"],
    "dirs": {
        "backup": "backup",
        "tmp": "tmp",
        "logs": "logs",
        "log_archive": "logs/archive",
        "model_active": "models/active",
        "model_archive": "models/archive",
        "core": "app/core",
        "experimental": "app/experimental"
    }
}

def load_config():
    """Load configuration from JSON file or create default."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG

CONFIG = load_config()
BASE_DIR = CONFIG["base_dir"]
MANIFEST_FILE = os.path.join(BASE_DIR, MANIFEST_FILE)
CHECK_INTERVAL = CONFIG["check_interval"]
TMP_MAX_AGE_DAYS = CONFIG["tmp_max_age_days"]
LOG_KEEP_COUNT = CONFIG["log_keep_count"]
FREE_SPACE_THRESHOLD_GB = CONFIG["free_space_threshold_gb"]
CODE_EXTENSIONS = CONFIG["code_extensions"]

# Resolve directory paths
DIRS = {key: os.path.join(BASE_DIR, path) for key, path in CONFIG["dirs"].items()}

# ---------------- LOGGING SETUP ----------------
def setup_logging():
    """Configure logging with rotation."""
    os.makedirs(DIRS["logs"], exist_ok=True)
    log_file = os.path.join(DIRS["logs"], "feralecho.log")
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[handler, logging.StreamHandler()]
    )

setup_logging()
logger = logging.getLogger(__name__)

# ---------------- HELPERS ----------------
def ensure_dirs():
    """Create necessary directories."""
    for folder in DIRS.values():
        os.makedirs(folder, exist_ok=True)
    logger.info("Ensured all required directories exist.")

def file_age_days(path):
    """Calculate file age in days based on creation time."""
    try:
        return (datetime.now() - datetime.fromtimestamp(os.path.getctime(path))).days
    except OSError as e:
        logger.error(f"Error getting age for {path}: {e}")
        return 0

def free_space_gb(path):
    """Get free disk space in GB."""
    try:
        stat = os.statvfs(path)
        return (stat.f_bavail * stat.f_frsize) / 1e9
    except OSError as e:
        logger.error(f"Error checking free space for {path}: {e}")
        return float("inf")

def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file."""
    try:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing {file_path}: {e}")
        return None

# ---------------- MANIFEST HANDLING ----------------
MANIFEST_SCHEMA = {
    "type": "object",
    "properties": {
        "files": {"type": "array", "items": {"type": "object"}},
        "path_map": {"type": "object"},
        "usage_stats": {"type": "object"}
    },
    "required": ["files", "path_map", "usage_stats"]
}

def load_manifest():
    """Load and validate manifest file."""
    try:
        if os.path.exists(MANIFEST_FILE):
            with open(MANIFEST_FILE, 'r') as f:
                manifest = json.load(f)
            validate(instance=manifest, schema=MANIFEST_SCHEMA)
            return manifest
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"Invalid manifest: {e}. Creating new manifest.")
    return {"files": [], "path_map": {}, "usage_stats": {}}

def save_manifest(manifest):
    """Save manifest with backup."""
    try:
        backup_path = os.path.join(DIRS["backup"], "manifest_backup.json")
        if os.path.exists(MANIFEST_FILE):
            shutil.copy2(MANIFEST_FILE, backup_path)
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info("Manifest saved successfully.")
    except Exception as e:
        logger.error(f"Error saving manifest: {e}")

# ---------------- DEPENDENCY HANDLING ----------------
def find_imports_py(file_path):
    """Find imports in a Python file using AST."""
    imports = set()
    try:
        with open(file_path, 'r') as f:
            node = ast.parse(f.read(), filename=file_path)
        for n in ast.walk(node):
            if isinstance(n, ast.Import):
                for alias in n.names:
                    imports.add(alias.name)
            elif isinstance(n, ast.ImportFrom):
                if n.module:
                    imports.add(n.module)
    except Exception as e:
        logger.warning(f"Error parsing imports in {file_path}: {e}")
    return imports

def update_imports_ast(file_path, old_name, new_name):
    """Update imports in a Python file using AST."""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name == old_name:
                        alias.name = new_name
        with open(file_path, 'w') as f:
            f.write(ast.unparse(tree))
        logger.info(f"Updated imports in {file_path}: {old_name} -> {new_name}")
    except Exception as e:
        logger.error(f"Error updating imports in {file_path}: {e}")

def backup_file(file_path):
    """Create a backup of a file."""
    try:
        backup_path = os.path.join(DIRS["backup"], os.path.basename(file_path))
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backed up {file_path} to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up {file_path}: {e}")
        return None

def move_file(file_path, target_dir, manifest, tag=None):
    """Move a file and update manifest."""
    try:
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, os.path.basename(file_path))
        backup_file(file_path)
        shutil.move(file_path, target_path)
        logger.info(f"Moved {file_path} to {target_path}")

        manifest['path_map'][file_path] = target_path
        manifest_entry = next((f for f in manifest['files'] if f['path'] == file_path), None)
        if manifest_entry:
            manifest_entry['tags'] = manifest_entry.get('tags', [])
            if tag and tag not in manifest_entry['tags']:
                manifest_entry['tags'].append(tag)

        # Update imports in code files
        for entry in manifest['files']:
            entry_path = os.path.join(BASE_DIR, entry['path'])
            if os.path.exists(entry_path) and entry['type'] == "code" and entry_path.endswith('.py'):
                imports = find_imports_py(entry_path)
                old_name = os.path.splitext(os.path.basename(file_path))[0]
                if old_name in imports:
                    new_name = os.path.splitext(os.path.basename(target_path))[0]
                    update_imports_ast(entry_path, old_name, new_name)
        return target_path
    except Exception as e:
        logger.error(f"Error moving {file_path} to {target_dir}: {e}")
        return None

# ---------------- FILE CLASSIFICATION ----------------
def classify_file(path):
    """Classify file type based on extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext in CODE_EXTENSIONS:
        return "code"
    elif ext in ['.txt', '.json', '.md', '.cfg']:
        return "text"
    elif ext in ['.log']:
        return "log"
    elif ext in ['.lock', '.tmp']:
        return "temp"
    elif ext in ['.gguf', '.safetensors', '.bin']:
        return "model"
    else:
        return "other"

# ---------------- USAGE TRACKING ----------------
def update_usage(manifest, file_path):
    """Update usage stats in manifest."""
    stats = manifest.get('usage_stats', {})
    stats[file_path] = stats.get(file_path, 0) + 1
    manifest['usage_stats'] = stats
    logger.debug(f"Updated usage for {file_path}: {stats[file_path]}")

# ---------------- FILE WATCHER ----------------
class FileEventHandler(FileSystemEventHandler):
    """Handle file system events."""
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

# ---------------- AUTONOMOUS CYCLE ----------------
def process_file(file_path, manifest):
    """Process a single file."""
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        return False

    rel_path = os.path.relpath(file_path, BASE_DIR)
    ftype = classify_file(file_path)
    fhash = compute_file_hash(file_path)

    # Update manifest
    manifest_entry = next((f for f in manifest['files'] if f['path'] == rel_path), None)
    if not manifest_entry:
        manifest_entry = {"path": rel_path, "type": ftype, "hash": fhash, "tags": []}
        manifest['files'].append(manifest_entry)
    else:
        manifest_entry['hash'] = fhash

    update_usage(manifest, rel_path)

    # Handle duplicates
    seen_hashes = {f['hash']: f['path'] for f in manifest['files'] if f.get('hash') and f['path'] != rel_path}
    if fhash and fhash in seen_hashes:
        logger.info(f"Duplicate detected: {rel_path} matches {seen_hashes[fhash]}")
        move_file(file_path, DIRS["tmp"], manifest, tag="duplicate")
        return True

    # File management
    if ftype == "log":
        move_file(file_path, DIRS["log_archive"], manifest, tag="archived")
    elif ftype == "temp" and file_age_days(file_path) > TMP_MAX_AGE_DAYS:
        move_file(file_path, DIRS["tmp"], manifest, tag="archived")
    elif ftype == "model":
        usage_count = manifest['usage_stats'].get(rel_path, 0)
        target_dir = DIRS["model_active"] if usage_count > 5 else DIRS["model_archive"]
        move_file(file_path, target_dir, manifest, tag="model")
    elif ftype == "code":
        tags = manifest_entry.get('tags', [])
        target_dir = DIRS["experimental"] if "experimental" in tags else DIRS["core"]
        move_file(file_path, target_dir, manifest, tag="experimental" if "experimental" in tags else "core")

    # Validate code
    if ftype == "code" and file_path.endswith('.py'):
        try:
            with open(file_path, 'r') as f:
                ast.parse(f.read(), filename=file_path)
            logger.info(f"Syntax valid for {file_path}")
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

    return True

def autonomous_cycle():
    """Run a full autonomous cycle."""
    logger.info("Starting autonomous cycle")
    ensure_dirs()
    manifest = load_manifest()
    duplicates_moved = 0

    # Process all files
    for root, _, files in os.walk(BASE_DIR):
        for fname in files:
            file_path = os.path.join(root, fname)
            if process_file(file_path, manifest):
                duplicates_moved += 1

    # Adaptive space management
    free_gb = free_space_gb(BASE_DIR)
    if free_gb < FREE_SPACE_THRESHOLD_GB:
        logger.warning(f"Low disk space: {free_gb:.2f}GB. Performing cleanup.")
        for folder in [DIRS["tmp"], DIRS["log_archive"], DIRS["model_archive"]]:
            for f in os.listdir(folder):
                fpath = os.path.join(folder, f)
                if os.path.isfile(fpath) and file_age_days(fpath) > TMP_MAX_AGE_DAYS:
                    try:
                        os.remove(fpath)
                        logger.info(f"Deleted {fpath} to free space")
                    except Exception as e:
                        logger.error(f"Error deleting {fpath}: {e}")

    save_manifest(manifest)
    logger.info(f"Cycle complete. Duplicates moved: {duplicates_moved}")

# ---------------- MAIN LOOP ----------------
def main():
    """Main entry point with file watcher and scheduler."""
    logger.info("Starting FeralEcho manager")
    ensure_dirs()

    # Set up file watcher
    event_handler = FileEventHandler(lambda path: process_file(path, load_manifest()))
    observer = Observer()
    observer.schedule(event_handler, BASE_DIR, recursive=True)
    observer.start()

    # Set up scheduler
    schedule.every(CHECK_INTERVAL).seconds.do(autonomous_cycle)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("FeralEcho stopped")
    observer.join()

if __name__ == "__main__":
    main()
