#!/usr/bin/env python3
"""
feral_echo_master_inspector.py
Safely inspects the FeralEcho project for:
- unused Python files
- sensitive info patterns
- empty or stale log files
"""

import os
import re
import json
import argparse
from datetime import datetime, timedelta

# -------- Config --------
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(PROJECT_DIR, "inspection_report.txt")

SENSITIVE_PATTERNS = {
    "api_key": r"(?i)(api[_-]?key\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"])",
    "password": r"(?i)(password\s*=\s*['\"][^'\"]+['\"])",
    "secret": r"(?i)(secret[_-]?key\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"])",
    "token": r"(?i)(['\"]?[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,}['\"]?)"
}

STALE_THRESHOLD_HOURS = 24  # default

# -------- Log Helpers --------
def parse_log_timestamp(line):
    """Try to parse a timestamp from a log line (ISO or prefix)."""
    try:
        if line.startswith("{"):  # JSON log line
            data = json.loads(line)
            ts = data.get("timestamp")
            if ts:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            token = line.strip().split(" ")[0].strip("[]")
            return datetime.fromisoformat(token)
    except Exception:
        return None

def check_log_file(filepath):
    """Check if log file is empty or stale."""
    if os.path.getsize(filepath) == 0:
        return [(0, "empty_log_file", "file has no content")]

    last_dt = None
    with open(filepath, "r", errors="ignore") as f:
        for line in f:
            dt = parse_log_timestamp(line)
            if dt:
                last_dt = dt

    findings = []
    if last_dt is None:
        findings.append((0, "unparseable_log", "could not extract timestamps"))
    else:
        age = datetime.utcnow() - last_dt.replace(tzinfo=None)
        if age > timedelta(hours=STALE_THRESHOLD_HOURS):
            findings.append((0, "stale_log_file", f"last entry {age} old: {last_dt}"))

    return findings

# -------- File Inspectors --------
def inspect_file(filepath):
    """Scan file for sensitive patterns."""
    findings = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            for i, line in enumerate(f, start=1):
                for label, pattern in SENSITIVE_PATTERNS.items():
                    if re.search(pattern, line):
                        findings.append((i, label, line.strip()))
    except Exception as e:
        findings.append((0, "error", f"Could not read file: {e}"))
    return findings

def find_unused_files(project_dir):
    """List .py files not imported anywhere."""
    py_files = []
    imports = set()

    for root, _, files in os.walk(project_dir):
        for fname in files:
            if fname.endswith(".py") and fname != os.path.basename(__file__):
                full = os.path.relpath(os.path.join(root, fname), project_dir)
                py_files.append(full)
                try:
                    with open(os.path.join(root, fname), "r", errors="ignore") as f:
                        for line in f:
                            if line.strip().startswith("import ") or "from " in line:
                                parts = re.split(r"\s+", line.strip())
                                if len(parts) >= 2:
                                    imports.add(parts[1].split(".")[0])
                except Exception:
                    pass

    unused = []
    for f in py_files:
        mod = os.path.splitext(os.path.basename(f))[0]
        if mod not in imports:
            unused.append(f)
    return unused

# -------- Main --------
def run_inspector(threshold_hours=24):
    global STALE_THRESHOLD_HOURS
    STALE_THRESHOLD_HOURS = threshold_hours

    report = []
    for root, _, files in os.walk(PROJECT_DIR):
        for fname in files:
            path = os.path.join(root, fname)

            # skip the report file itself
            if path == REPORT_FILE:
                continue

            findings = []
            if fname.endswith(".py"):
                findings = inspect_file(path)
            elif fname.endswith(".log"):
                findings = check_log_file(path)

            if findings:
                for line_no, label, detail in findings:
                    rel = os.path.relpath(path, PROJECT_DIR)
                    report.append(f"[{rel}:{line_no}] {label} -> {detail}")

    unused_files = find_unused_files(PROJECT_DIR)
    if unused_files:
        report.append("\n--- Unused Python Files ---")
        report.extend(unused_files)

    with open(REPORT_FILE, "w") as out:
        out.write("\n".join(report) if report else "No issues found.\n")

    print(f"[Inspector] Report written to {REPORT_FILE}")

# -------- CLI --------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FeralEcho Project Inspector")
    parser.add_argument("--hours", type=int, default=24,
                        help="Stale log threshold in hours (default=24)")
    args = parser.parse_args()

    run_inspector(threshold_hours=args.hours)

