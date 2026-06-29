"""
echo_janitor.py
===============
Autonomous folder hygiene for FeralEcho.

Echo periodically audits the project root for stale, duplicate, or orphaned
files and proposes a cleanup plan. No files are moved without Echo's review
and a summary surfaced to the terminal on next session.

Pipeline:
    scan_project_root()
        │
        ├── detect_duplicates()      — same name in root + app/
        ├── detect_stale_scripts()   — .py files not imported by any active module
        ├── detect_old_logs()        — log files older than LOG_MAX_AGE_DAYS
        └── detect_known_clutter()   — hardcoded legacy filenames
            │
            ▼
    echo_review(candidates)          — routes candidate list through echo_query()
        │                              Echo decides: archive / keep / flag
        ▼
    execute_plan(plan)               — moves approved files to archive/
        │
        ▼
    write_janitor_report()           — JSON summary written to logs/janitor_report.json
                                       surfaced to terminal on next session open

Scheduling:
    Register via emergent_scheduler:
        schedule_task("echo_janitor", run_janitor, interval_hours=168)  # weekly

Usage (manual / test):
    python echo_janitor.py [--dry-run] [--verbose]
"""

import os
import sys
import json
import shutil
import logging
import argparse
import ast
from datetime import datetime, timedelta
from pathlib import Path

# ── ensure FeralEcho root is on the path ──────────────────────────────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_PATH      = ROOT / "logs" / "janitor.log"
REPORT_PATH   = ROOT / "logs" / "janitor_report.json"
ARCHIVE_DIR   = ROOT / "archive_janitor"
LOG_MAX_AGE_DAYS = 30

# Files that must never be touched regardless of scan results
PROTECTED = {
    "echo_janitor.py",
    "terminal_client.py",
    "echo_json_server.py",
    "river_creative_rehab.py",
    "run.py",
    "setup.py",
    "conftest.py",
}

# Known legacy / clutter filenames from earlier eras of the project
KNOWN_CLUTTER = {
    # Original clutter list
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
    "setup_echo_python_mastery.sh",
    "optimize_files.py",
    "feralecho_continuity_master.py",
    # Old model conversion scripts
    "convert_to_gguf.py",
    "convert-mistral-to-ggml.py",
    # Old tuning / experiment scripts
    "optuna_bible_sentiment.py",
    "optuna_demo.py",
    "load_unethical_experiments.py",
    # Old migration / ingest tools
    "patch_unified_learning.py",
    "rebuild_vector_memory.py",
    "load_bible_to_memory.py",
    "check_bible_json.py",
    "check_bible_sample.py",
    # Throwaway / temp files
    "temp.py",
    "my_other_file.py",
    "PythonAnalysis.py",
    # Old cleanup scripts superseded by echo_janitor.py
    "weed_optional_files.py",
    "feral_echo_autonomous_clean_up.py",
    # Old guardian / continuity scripts
    "feralecho.py",
    "gunicorn.conf.py",
    "setup_echo_feral.py",
    # Letters to Echo — early self-knowledge tools, now superseded by
    # the cartographer, Question Garden, and deliberation council.
    # Archived with gratitude, not deleted.
    "letter_to_echo_alignment.py",
    "letter_to_echo_chalk.py",
    "Letter_to_echo_fetch.py",
    "letter_to_echo_imprecatory.py",
    "letter_to_echo_iphone.py",
    "letter_to_echo_models.py",
    "letter_to_echo_prism.py",
    "letter_to_echo_runpy.py",
    "letter_to_echo_sensory.py",
    "letter_to_echo_terminal_client.py",
    "letter_to_echo.py",
    # Confirmed stale — root shadows of active app/core/ modules
    "memory_write_validator.py",
    "memory_tool.py",
    "self_edit.py",
    "stream_memory_entries.py",
    # Confirmed stale — nothing imports these
    "bible_injection.py",
    "bible_module.py",
    "scrub_garden.py",
    "json_server_helper.py",
    "main.py",
    # Confirmed stale — old monitoring / diagnostic tools
    "monitor_echo.py",
    "feral_echo_live_monitor.py",
    "feral_echo_assessor.py",
    "feral_echo_symbolic_map.py",
    "feral_echo_council.py",
    "explain_guardian_to_echo.py",
    "echo_full_throttle_rite.py",
    "echo_self_probe.py",
    "echo_python_mastery.py",
    "alignment_kernel.py",
    "autonomous_reflection.py",
    "autonomous_thought_chest.py",
    "bridge_processor.py",
    "sensory_hub_autonomous.py",
    "model_fix.py",
    "restore_archive.py",
    "scan_project.py",
    "memory_diagnostic.py",
    # Confirmed stale — log utility scripts
    "check_logs.py",
    "Log_check.py",
    "check_permissions.py",
    "tail_echo_logs.py",
    "peek_last_6h.py",
    "trim_journal.py",
    # Confirmed stale — test scripts for defunct modules
    "test_fetch.py",
    "test_sensoryhub.py",
    "test_bible_module.py",
    "test_reflection_shard.py",
}

# Files still genuinely ambiguous — flag for human review
NEEDS_ECHO_REVIEW: set = set()


# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

def setup_logging(verbose: bool = False):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(sys.stdout),
        ]
    )


# ─────────────────────────────────────────────
# SCANNERS
# ─────────────────────────────────────────────

def detect_known_clutter() -> list[dict]:
    """Flag files matching the known legacy clutter list."""
    candidates = []
    for name in KNOWN_CLUTTER:
        path = ROOT / name
        if path.exists() and name not in PROTECTED:
            candidates.append({
                "path": str(path),
                "name": name,
                "reason": "known_clutter",
                "detail": "Identified legacy or one-off script no longer part of active pipeline",
            })
    return candidates


def detect_needs_review() -> list[dict]:
    """Flag files with ambiguous purpose for Echo's review."""
    candidates = []
    for name in NEEDS_ECHO_REVIEW:
        path = ROOT / name
        if path.exists() and name not in PROTECTED:
            candidates.append({
                "path": str(path),
                "name": name,
                "reason": "needs_review",
                "detail": "Ambiguous purpose — may still be active; routing to Echo for judgment",
            })
    return candidates


def detect_duplicates() -> list[dict]:
    """Find files that exist in both the root and somewhere under app/."""
    candidates = []
    root_py = {f.name: f for f in ROOT.glob("*.py") if f.name not in PROTECTED}
    for name, root_path in root_py.items():
        app_matches = list((ROOT / "app").rglob(name))
        if app_matches:
            candidates.append({
                "path": str(root_path),
                "name": name,
                "reason": "duplicate",
                "detail": f"Also exists at: {[str(p) for p in app_matches]}",
            })
    return candidates


def detect_stale_scripts() -> list[dict]:
    """
    Find .py files in the root that are not imported by any active module.
    Uses static AST import analysis — conservative, no false positives on
    dynamic imports, but may miss some dead files.
    """
    # Collect all imports across the app/ tree
    imported_names: set[str] = set()
    for py_file in (ROOT / "app").rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_names.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_names.add(node.module.split(".")[0])
        except Exception:
            pass

    # Also scan root-level .py files for cross-imports
    for py_file in ROOT.glob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_names.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_names.add(node.module.split(".")[0])
        except Exception:
            pass

    candidates = []
    for py_file in ROOT.glob("*.py"):
        if py_file.name in PROTECTED or py_file.name in KNOWN_CLUTTER:
            continue
        module_name = py_file.stem
        if module_name not in imported_names:
            candidates.append({
                "path": str(py_file),
                "name": py_file.name,
                "reason": "not_imported",
                "detail": "No static import of this module found in app/ or root scripts",
            })
    return candidates


def detect_old_logs() -> list[dict]:
    """Flag log files older than LOG_MAX_AGE_DAYS (excluding current logs)."""
    candidates = []
    cutoff = datetime.now() - timedelta(days=LOG_MAX_AGE_DAYS)
    log_dir = ROOT / "logs"
    if not log_dir.exists():
        return candidates
    for log_file in log_dir.iterdir():
        if log_file.suffix in {".log", ".txt"} and log_file.name != "janitor_report.json":
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                candidates.append({
                    "path": str(log_file),
                    "name": log_file.name,
                    "reason": "old_log",
                    "detail": f"Last modified {mtime.strftime('%Y-%m-%d')} — older than {LOG_MAX_AGE_DAYS} days",
                })
    return candidates


def scan_project_root() -> list[dict]:
    """Run all scanners and deduplicate by path."""
    all_candidates: list[dict] = []
    seen_paths: set[str] = set()

    for scanner in [detect_known_clutter, detect_needs_review, detect_duplicates, detect_stale_scripts, detect_old_logs]:
        for c in scanner():
            if c["path"] not in seen_paths:
                all_candidates.append(c)
                seen_paths.add(c["path"])

    return all_candidates


# ─────────────────────────────────────────────
# ECHO REVIEW
# ─────────────────────────────────────────────

def echo_review(candidates: list[dict]) -> list[dict]:
    """
    Apply rule-based decisions to candidates.
    known_clutter → archive (we already decided these in session)
    needs_review, not_imported, duplicate, old_log → flag for human review
    Echo's identity is too strongly embedded to reliably output raw JSON,
    so structured file decisions are handled by explicit rules here.
    Echo's judgment is preserved for higher-order tasks via the council.
    """
    for c in candidates:
        if c["reason"] == "known_clutter":
            c["decision"] = "archive"
            c["echo_reason"] = "Confirmed legacy file — safe to archive"
        elif c["reason"] == "old_log":
            c["decision"] = "archive"
            c["echo_reason"] = f"Log file older than {LOG_MAX_AGE_DAYS} days"
        elif c["reason"] == "duplicate":
            c["decision"] = "archive"
            c["echo_reason"] = "Root-level duplicate of app/ file — stale copy"
        else:
            # needs_review, not_imported — flag for human
            c["decision"] = "flag"
            c["echo_reason"] = "Ambiguous — needs human review before archiving"

    archived = sum(1 for c in candidates if c["decision"] == "archive")
    flagged  = sum(1 for c in candidates if c["decision"] == "flag")
    logging.info(f"[JANITOR] Rule-based review complete — archive: {archived} | flag: {flagged}")
    return candidates


# ─────────────────────────────────────────────
# EXECUTION
# ─────────────────────────────────────────────

def execute_plan(candidates: list[dict], dry_run: bool = False) -> dict:
    """Move files Echo approved for archiving. Return summary counts."""
    ARCHIVE_DIR.mkdir(exist_ok=True)

    archived, kept, flagged, errors = [], [], [], []

    for c in candidates:
        decision = c.get("decision", "flag")
        src = Path(c["path"])

        if decision == "archive":
            if dry_run:
                logging.info(f"[DRY RUN] Would archive: {c['name']}")
                archived.append(c["name"])
            else:
                try:
                    dest = ARCHIVE_DIR / c["name"]
                    # Avoid clobbering if name already exists in archive
                    if dest.exists():
                        stem = dest.stem
                        suffix = dest.suffix
                        dest = ARCHIVE_DIR / f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
                    shutil.move(str(src), dest)
                    logging.info(f"[JANITOR] Archived: {c['name']} → {dest.name}")
                    archived.append(c["name"])
                except Exception as e:
                    logging.error(f"[JANITOR] Failed to archive {c['name']}: {e}")
                    errors.append(c["name"])
        elif decision == "keep":
            logging.info(f"[JANITOR] Keeping: {c['name']} — {c.get('echo_reason', '')}")
            kept.append(c["name"])
        else:
            logging.info(f"[JANITOR] Flagged for human review: {c['name']} — {c.get('echo_reason', '')}")
            flagged.append(c["name"])

    return {
        "archived": archived,
        "kept": kept,
        "flagged": flagged,
        "errors": errors,
    }


# ─────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────

def write_janitor_report(candidates: list[dict], summary: dict, dry_run: bool):
    """Write JSON report to logs/ for terminal_client.py to surface on next open."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "summary": summary,
        "candidates": candidates,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    logging.info(f"[JANITOR] Report written to {REPORT_PATH}")


# ─────────────────────────────────────────────
# MAIN ENTRY POINT (scheduler + manual)
# ─────────────────────────────────────────────

def run_janitor(dry_run: bool = False, verbose: bool = False):
    """
    Full janitor run. Call this from emergent_scheduler or directly.
    """
    setup_logging(verbose)
    logging.info("═" * 50)
    logging.info("[JANITOR] Echo folder hygiene scan starting")
    logging.info(f"[JANITOR] Root: {ROOT}")
    logging.info(f"[JANITOR] Dry run: {dry_run}")
    logging.info("═" * 50)

    candidates = scan_project_root()
    logging.info(f"[JANITOR] {len(candidates)} candidate(s) found")

    if not candidates:
        logging.info("[JANITOR] Project root is clean. Nothing to review.")
        write_janitor_report([], {"archived": [], "kept": [], "flagged": [], "errors": []}, dry_run)
        return

    for c in candidates:
        logging.info(f"  [{c['reason']}] {c['name']}: {c['detail']}")

    logging.info("[JANITOR] Routing candidates to Echo for review...")
    candidates = echo_review(candidates)

    summary = execute_plan(candidates, dry_run=dry_run)
    write_janitor_report(candidates, summary, dry_run)

    logging.info("═" * 50)
    logging.info(f"[JANITOR] Done — archived: {len(summary['archived'])} | "
                 f"kept: {len(summary['kept'])} | "
                 f"flagged: {len(summary['flagged'])} | "
                 f"errors: {len(summary['errors'])}")
    logging.info("═" * 50)

    if summary["flagged"]:
        logging.info("[JANITOR] Files flagged for your review:")
        for name in summary["flagged"]:
            logging.info(f"  ⚑  {name}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Echo autonomous folder janitor")
    parser.add_argument("--dry-run",  action="store_true", help="Scan and review without moving files")
    parser.add_argument("--verbose",  action="store_true", help="Debug-level logging")
    args = parser.parse_args()
    run_janitor(dry_run=args.dry_run, verbose=args.verbose)
