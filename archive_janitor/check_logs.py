import os

def check_log_integrity(log_path):
    if not os.path.exists(log_path):
        print(f"Log file {log_path} missing!")
        return False
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            print(f"{log_path}: {len(lines)} lines")
            # Simple sanity check: no extremely large lines
            for i, line in enumerate(lines[-10:], 1):
                if len(line) > 1000:
                    print(f"Warning: very long line near end: line {len(lines)-10+i}")
    except Exception as e:
        print(f"Error reading {log_path}: {e}")
        return False
    return True

for logfile in ["memory/dream_bridge.log", "memory/memory_journal.log", "memory/self_edit_reflections.log"]:
    check_log_integrity(logfile)

