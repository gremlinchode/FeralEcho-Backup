# optimize_files.py – Safe runtime-aware Echo project file optimizer (report only)
import os
import sys
import threading
import time

PROJECT_ROOT = "."
REPORT_FILE = "unused_files_report.txt"

# Collect all .py files
def list_py_files(root):
    py_files = []
    for dirpath, _, filenames in os.walk(root):
        # Skip virtualenvs or archive folders
        if "archive_unused_files" in dirpath or "__pycache__" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.abspath(os.path.join(dirpath, filename))
                py_files.append(full_path)
    return set(py_files)

# Runtime tracker
executed_files = set()

def trace_calls(frame, event, arg):
    if event == "call":
        filename = os.path.abspath(frame.f_code.co_filename)
        if filename.startswith(os.path.abspath(PROJECT_ROOT)):
            executed_files.add(filename)
    return trace_calls

def run_echo_for_coverage():
    """
    Import Echo's run.py and start it in a thread.
    This will execute code and let the trace capture all imported files.
    """
    import run  # Assumes run.py is in PROJECT_ROOT
    # Start background threads safely
    thread = threading.Thread(target=run.start_background_threads, daemon=True)
    thread.start()
    # Let it run briefly to initialize modules
    time.sleep(10)
    print("Echo modules executed for coverage capture...")

def main():
    all_files = list_py_files(PROJECT_ROOT)

    # Enable tracing
    sys.settrace(trace_calls)
    run_echo_for_coverage()
    sys.settrace(None)

    unused_files = all_files - executed_files

    # Write report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("=== Potentially Unused Files (Runtime Coverage) ===\n")
        for file in sorted(unused_files):
            f.write(file + "\n")

    print(f"Report written to {REPORT_FILE}")
    print(f"Total .py files: {len(all_files)}")
    print(f"Files executed: {len(executed_files)}")
    print(f"Potentially unused files: {len(unused_files)}")

if __name__ == "__main__":
    main()

