import os
import shutil

PROJECT_DIR = "/Users/richietate/Desktop/FeralEcho"
ARCHIVE_DIR = os.path.join(PROJECT_DIR, "archived_files")

# Walk through the archive folder
for root, dirs, files in os.walk(ARCHIVE_DIR):
    for file in files:
        archived_path = os.path.join(root, file)
        # Compute the original path relative to PROJECT_DIR
        relative_path = os.path.relpath(archived_path, ARCHIVE_DIR)
        original_path = os.path.join(PROJECT_DIR, relative_path)

        # Make sure the original directory exists
        os.makedirs(os.path.dirname(original_path), exist_ok=True)

        # Move the file back
        shutil.move(archived_path, original_path)
        print(f"Restored: {relative_path}")

# Optional: remove empty archive directories
for root, dirs, _ in os.walk(ARCHIVE_DIR, topdown=False):
    for d in dirs:
        dir_path = os.path.join(root, d)
        if not os.listdir(dir_path):
            os.rmdir(dir_path)

