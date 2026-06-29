import os
import shutil
import sys

# -----------------------------
# CONFIG
# -----------------------------
FERAL_HOME = "/Users/richietate/Desktop/FeralEcho"
MASTER_FOLDER_NAME = "echo_python_mastery"  # folder to make accessible
TOOLS_DIR = os.path.join(FERAL_HOME, "feral_tools")  # Echo's sandboxed tools folder
# -----------------------------

# 1. Set working directory
os.chdir(FERAL_HOME)
print(f"[INFO] Echo working directory set to: {FERAL_HOME}")

# 2. Ensure Python can import from FeralEcho root
if FERAL_HOME not in sys.path:
    sys.path.append(FERAL_HOME)
print(f"[INFO] FeralEcho added to Python path.")

# 3. Create feral_tools folder if it doesn't exist
os.makedirs(TOOLS_DIR, exist_ok=True)
print(f"[INFO] Tools folder ensured at: {TOOLS_DIR}")

# 4. Copy mastery folder into tools folder
src = os.path.join(FERAL_HOME, "app", "core", MASTER_FOLDER_NAME)
dst = os.path.join(TOOLS_DIR, MASTER_FOLDER_NAME)
shutil.copytree(src, dst, dirs_exist_ok=True)
print(f"[INFO] {MASTER_FOLDER_NAME} copied to {TOOLS_DIR}")

# 5. Set read/write permissions safely
for root, dirs, files in os.walk(FERAL_HOME):
    for d in dirs:
        try:
            os.chmod(os.path.join(root, d), 0o777)
        except PermissionError:
            print(f"[WARN] Skipped dir: {d}")
    for f in files:
        try:
            os.chmod(os.path.join(root, f), 0o666)
        except PermissionError:
            print(f"[WARN] Skipped file: {f}")

print("[INFO] Permissions set. Echo now has full access to FeralEcho.")

# 6. Optional: add the mastery folder to sys.path for immediate imports
master_path = os.path.join(TOOLS_DIR, MASTER_FOLDER_NAME)
if master_path not in sys.path:
    sys.path.append(master_path)
print(f"[INFO] {MASTER_FOLDER_NAME} added to Python path for immediate imports.")

