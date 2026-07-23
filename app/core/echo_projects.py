"""
app/core/echo_projects.py — sandboxed multi-file code generation, with full
library access (no _ALLOWED_TOP_LEVEL restriction), never auto-loaded into
the live process.

This is NOT a replacement for or extension of the single-file self-edit
pipeline (self_edit_manager.py) — it's a deliberately separate, parallel
capability: generate and test real multi-file Python projects in a
directory that is (a) never auto-loaded into the running server, and (b)
never has any promotion/escalation path into anything trusted. Both
properties are structural, not just conventional — verified live by two
Liveness Ledger checks (echo_projects_isolation, echo_projects_no_escalation).

"Full library access" specifically means: this pipeline does NOT call
self_edit_manager._validate_imports()/_ALLOWED_TOP_LEVEL at all. Every file
still goes through the real, unmodified F1 (scan_for_unsafe_operations(),
including the self-edit-escalation-call block added alongside this module)
and the real, unmodified F2 kernel sandbox (echo_sandbox.sb's unconditional
network deny + write confinement, safe_exec_wrapper.py's GUI stubs).
Removing the allowlist doesn't touch either of those — neither cares what
was imported.

Explicit, stated scope caveat, not oversold: this is full ATTEMPT access,
not a guarantee every installed package works inside the sandbox. Self-edit's
own narrower pipeline has only ever exercised a small, already-audited set
of imports (CLAUDE.md Finding 23: 9 direct + 4 transitive native-extension
packages). Full-library projects will exercise far more of the real
environment — expect the same class of friction Finding 23 already found
and accepted for torch/mlx_lm (native extensions whose own import trips
F2's ctypes.CDLL patch) to recur for other native-extension packages nobody
has run through this sandbox before. Not a safety gap (F2's kernel profile
holds regardless of what was imported) — a reliability caveat.

V1 scope, stated plainly: flat, absolute-import multi-file layouts only
(`import helper`, not `from . import helper`) — the loading mechanism
(importlib.util.spec_from_file_location, loading main.py as "__main__" with
no package context) doesn't support package-relative imports. Every project
must include a main.py entry point; every other file is import-tested only
(F1 scan + F2 import survives), not executed.
"""
import ast
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.core.self_edit_manager import (
    scan_for_unsafe_operations,
    _PROJECT_ROOT,
    _SANDBOX_PROFILE,
    _SANDBOX_WRAPPER,
    _extract_sandbox_failure_text,
)

logger = logging.getLogger(__name__)

_PROJECTS_DIR = Path(_PROJECT_ROOT) / "sandbox" / "echo_projects"
_MAX_ECHO_PROJECTS = 20


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", (text or "").strip())[:max_len].strip("_")
    return slug or "project"


def _prune_old_projects(projects_dir: "Path | None" = None, max_projects: "int | None" = None) -> int:
    """Cap total retained projects, oldest pruned first — mirrors
    self_edit_backups'/self_edit_plans' existing capped-and-pruned pattern
    (CLAUDE.md Finding 58). Parameterized (not hardcoded to the real
    module-level constants) specifically so a test/liveness-check can
    exercise this against a scratch directory — same reasoning as
    self_edit_manager.py's _prune_self_edit_plans() gaining optional params
    for the identical purpose. Returns the number of directories pruned."""
    projects_dir = projects_dir if projects_dir is not None else _PROJECTS_DIR
    max_projects = max_projects if max_projects is not None else _MAX_ECHO_PROJECTS
    pruned = 0
    try:
        if not projects_dir.exists():
            return 0
        dirs = sorted((d for d in projects_dir.iterdir() if d.is_dir()), key=lambda d: d.name)
        for old in dirs[:-max_projects] if max_projects > 0 else dirs:
            shutil.rmtree(old, ignore_errors=True)
            pruned += 1
            logger.info(f"[ECHO-PROJECTS] Pruned old project: {old.name}")
    except Exception as e:
        logger.warning(f"[ECHO-PROJECTS] Prune failed: {e}")
    return pruned


def _extract_imports(code: str) -> list:
    """Best-effort list of real top-level import names used, for the
    report manifest's "imports used" audit line only — not a safety check,
    just observability into what "full library access" is actually being
    used for in practice."""
    names = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
    except Exception:
        pass
    return sorted(names)


def _run_f2_multi_file(project_dir: Path, timeout: int = 60) -> dict:
    """Real, unmodified F2: sandbox-exec + echo_sandbox.sb + safe_exec_wrapper.py
    --mode=script, run against main.py with project_dir itself as both the
    SCRATCH root (write confinement) and the sys.path addition (so flat
    sibling imports resolve — see safe_exec_wrapper.py's own scratch-dir
    sys.path.append() fix). Reuses the exact real sandbox-exec invocation
    shape self_edit_manager.py's test_code_in_sandbox() already uses —
    not a new sandboxing mechanism, the same one, generalized to a
    directory that already contains more than one file."""
    main_path = str(project_dir / "main.py")
    try:
        result = subprocess.run(
            ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={project_dir}",
             sys.executable, _SANDBOX_WRAPPER, str(project_dir), main_path, "--mode=script"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        if result.returncode == 0 and "SANDBOX_OK" in result.stdout:
            return {"passed": True, "stdout_tail": result.stdout[-500:]}
        raw = (result.stderr or result.stdout).strip()
        err = _extract_sandbox_failure_text(raw)
        return {"passed": False, "returncode": result.returncode, "error": err[:500]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "sandbox test timed out"}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def _write_report(project_dir: Path, spec: str, files: dict, f1_results: dict,
                   f2_result: "dict | None", ts: str) -> Path:
    lines = [
        "# ECHO PROJECT — not loaded, not promoted, for human review only.",
        f"# Generated: {ts}",
        f"# Spec: {spec}",
        f"# Files: {', '.join(files.keys())}",
        "#",
        "# F1 (per file):",
    ]
    for filename, result in f1_results.items():
        lines.append(f"#   {filename}: {result}")
    if f2_result is not None:
        lines.append("#")
        status = "PASS" if f2_result.get("passed") else "FAIL"
        lines.append(f"# F2 (multi-file import+run test): {status}")
        if not f2_result.get("passed"):
            detail = f2_result.get("error", "")
            lines.append(f"#   detail: {detail}")
    all_imports = sorted({imp for code in files.values() for imp in _extract_imports(code)})
    lines.append("#")
    lines.append(
        "# Imports used (auditing full-library-access in practice): "
        + (", ".join(all_imports) if all_imports else "(none)")
    )
    report_path = project_dir / "_report.md"
    report_path.write_text("\n".join(lines) + "\n")
    return report_path


def generate_project(spec: str, files: dict) -> dict:
    """
    Core pipeline. `files` is a dict of {filename: code}, already generated
    by the caller (this function does not itself call an LLM) — must
    include "main.py" as the entry point; every other file is import-tested
    only (F1 scan + F2 import-mode survives), never executed.

    Runs the real, unmodified F1 (scan_for_unsafe_operations(), including
    the self-edit-escalation-call block) per file, then — only if every
    file passes F1 — stages all files into one fresh, timestamped project
    directory under sandbox/echo_projects/ and runs the real, unmodified F2
    kernel sandbox against main.py. Writes a human-readable report either
    way. Deliberately stops there: NEVER calls save_code(), NEVER loads
    anything into the running process — this is the one invariant this
    whole feature's safety case depends on, verified live by
    liveness_ledger.py's echo_projects_no_escalation check.

    Returns {"status": "f1_failed"|"ok"|"f2_failed"|"error", "project_dir":
    str, "report_path": str, "f1_results": dict, "f2_result": dict|None}.
    """
    if not files or "main.py" not in files:
        return {"status": "error", "detail": "files must be a non-empty dict including 'main.py' as the entry point"}

    _prune_old_projects()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(spec)
    project_dir = _PROJECTS_DIR / f"{ts}_{slug}"
    project_dir.mkdir(parents=True, exist_ok=True)

    # F1 — real, unmodified, per file. No _validate_imports()/
    # _ALLOWED_TOP_LEVEL call anywhere in this pipeline — that's the actual
    # mechanism of "full library access" (see module docstring).
    f1_results = {}
    f1_all_ok = True
    for filename, code in files.items():
        try:
            scan_for_unsafe_operations(code)
            f1_results[filename] = "OK"
        except ValueError as e:
            f1_results[filename] = f"BLOCKED: {e}"
            f1_all_ok = False

    if not f1_all_ok:
        report = _write_report(project_dir, spec, files, f1_results, None, ts)
        logger.warning(f"[ECHO-PROJECTS] F1 blocked one or more files in {project_dir.name}")
        return {
            "status": "f1_failed", "project_dir": str(project_dir),
            "report_path": str(report), "f1_results": f1_results, "f2_result": None,
        }

    for filename, code in files.items():
        (project_dir / filename).write_text(code)

    f2_result = _run_f2_multi_file(project_dir)
    report = _write_report(project_dir, spec, files, f1_results, f2_result, ts)
    status = "ok" if f2_result.get("passed") else "f2_failed"
    logger.info(f"[ECHO-PROJECTS] {project_dir.name}: {status}")
    return {
        "status": status, "project_dir": str(project_dir),
        "report_path": str(report), "f1_results": f1_results, "f2_result": f2_result,
    }
