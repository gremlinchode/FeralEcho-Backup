import os
from pathlib import Path
import shutil

# Path to your project folder
FERAL_PATH = Path("/Users/richietate/Desktop/FeralEcho")  # adjust if needed

# Files to keep
KEEP = {"echo_json_server.py", "terminal_client.py"}

# List of optional files to archive (from your list)
OPTIONAL_FILES = {
    "echo_curl_test.sh",
    "echo_env_check.py",
    "feral_echo_debug_test.py",
    "feral_echo_flask_test.py",
    "feral_echo_safe_fetch_test.py",
    "feralecho_master_inspector.py",
    "feralecho_master_inspector.py.save",
    "feralecho_read_checkpoint.json",
    "inspection_report.txt",
    "unused_files_report.txt",
    "verify_env.sh",
    "test_embedding.py",
    "test_memory_stack.py",
    "split_bible.py",
    "send_bible_to_echo.py",
    "ingest_bible.py",
    "echo_read.py",
    "scars_to_light.py",
    "tree.txt",
    "test.txt",
    "setup_echo_python_mastery.sh"
}

# Archive folder
ARCHIVE = FERAL_PATH / "archive_optional_files"
ARCHIVE.mkdir(exist_ok=True)

# Move optional files not in KEEP
for file_name in OPTIONAL_FILES:
    file_path = FERAL_PATH / file_name
    if file_path.exists() and file_name not in KEEP:
        shutil.move(str(file_path), ARCHIVE / file_name)
        print(f"Moved {file_name} to archive")

