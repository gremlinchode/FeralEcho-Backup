import os
import shutil
import time
from pathlib import Path

# === Configuration ===
FOLDER = Path("/Users/richietate/Desktop/FeralEcho")  # <- Set your actual FeralEcho path
TRASH = FOLDER / "trash_autonomous"
TRASH.mkdir(parents=True, exist_ok=True)

# Files safe to delete
SAFE_PATTERNS = ["*.log", "*.tmp", "*.pyc", "*.bak"]

# Critical folders to never touch
CRITICAL_FOLDERS = ["app/core", "app/emergent_scheduler", "WhisperingWires"]

# Age threshold for old files (in days)
OLD_FILE_DAYS = 90

# === Helper Functions ===
def is_safe_to_delete(file_path: Path) -> bool:
    # Skip critical folders
    for cf in CRITICAL_FOLDERS:
        if cf in str(file_path):
            return False
    # Match safe patterns
    for pattern in SAFE_PATTERNS:
        if file_path.match(pattern):
            return True
    # Old file heuristic
    if file_path.exists() and file_path.stat().st_atime < time.time() - OLD_FILE_DAYS * 24 * 3600:
        return True
    return False

# === Autonomous Cleanup ===
def autonomous_cleanup():
    moved_count = 0
    for root, dirs, files in os.walk(FOLDER):
        for name in files:
            file_path = Path(root) / name
            if is_safe_to_delete(file_path):
                timestamped_name = f"{int(time.time())}_{name}"
                dest = TRASH / timestamped_name
                try:
                    shutil.move(str(file_path), str(dest))
                    print(f"[Moved] {file_path} -> {dest}")
                    moved_count += 1
                    time.sleep(0.01)  # Small delay to avoid filesystem stress
                except Exception as e:
                    print(f"[Error] Could not move {file_path}: {e}")
    print(f"[Autonomous Cleanup] Total files moved: {moved_count}")

# === Run ===
if __name__ == "__main__":
    autonomous_cleanup()

