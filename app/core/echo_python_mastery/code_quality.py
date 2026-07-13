# echo_python_mastery/code_quality.py
import os
import time

# Anchored via __file__, not cwd — same fix already applied to every path
# constant in self_edit_manager.py (CLAUDE.md Finding 7). This scan runs on
# every self-edit planning cycle; if the process cwd ever differs from the
# project root, the old root="." default silently fed wrong or empty
# guidance into the prompt instead of a real project-wide scan.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

_SCAN_CACHE: tuple[float, str] | None = None
_SCAN_TTL = 600  # re-scan at most every 10 minutes


def teach_code_quality():
    """
    Teach code quality checks: long functions, duplicates, empty files, permissions.
    Returns guidance as a string for autonomous consumption.
    """
    return _get_tips()


def _get_tips():
    """
    Returns code quality guidance as a plain string Echo can read and apply.
    Also performs a real scan of the project for empty files and reports findings.
    """
    tips = """CODE QUALITY:
- Avoid long functions. If a function has more than ~50 lines, split its logic into named helpers.
- Check for duplicated code. If the same logic appears in two places, factor it into a shared function.
- Empty files may indicate incomplete modules or failed self-edits. They should be investigated.
- Avoid world-writable file permissions on scripts. Use chmod 755 for executables, 644 for modules.
- Use static analysis tools: flake8 catches style violations, pylint catches deeper issues.
- After every self-edit, verify the generated file is non-empty and passes ast.parse before saving.
- Prefer explicit error handling over silent failures. Log what went wrong and where.
- Remove dead code. Commented-out blocks and unused imports accumulate and obscure intent.
"""

    # Real scan — report on actual project state
    scan_report = _scan_for_empty_files()
    if scan_report:
        tips += f"\nCURRENT PROJECT SCAN:\n{scan_report}"

    return tips


def _scan_for_empty_files(root=_PROJECT_ROOT, max_report=10):
    """
    Walk the project directory and return a report of empty .py files.
    Skips hidden directories and __pycache__. Result cached for 10 minutes.
    """
    global _SCAN_CACHE
    now = time.time()
    if _SCAN_CACHE and now - _SCAN_CACHE[0] < _SCAN_TTL:
        return _SCAN_CACHE[1]

    empty_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden dirs and pycache
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d != "__pycache__"
        ]
        for filename in filenames:
            if filename.endswith(".py"):
                full_path = os.path.join(dirpath, filename)
                try:
                    if os.path.getsize(full_path) == 0:
                        empty_files.append(full_path)
                except OSError:
                    continue

    if not empty_files:
        result = "No empty .py files found. Project structure looks clean."
    else:
        report_lines = [f"Found {len(empty_files)} empty .py file(s):"]
        for path in empty_files[:max_report]:
            report_lines.append(f"  - {path}")
        if len(empty_files) > max_report:
            report_lines.append(f"  ... and {len(empty_files) - max_report} more.")
        result = "\n".join(report_lines)

    _SCAN_CACHE = (now, result)
    return result

