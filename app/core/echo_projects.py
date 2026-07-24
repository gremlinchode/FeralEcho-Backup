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
import json
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
# Stable function references, imported at module level (same precedent as
# self_edit_manager.py's own top-level `rank_models` import). MODEL_POOL
# itself is deliberately NOT imported here — it's a mutable dict patched in
# place elsewhere (MLX avoidance, model pool refresh), and this codebase's
# own established precedent (terminal_client.py's !ask command) imports it
# lazily, inline, right before use, rather than capturing a module-level
# reference to it.
from app.core.echo_model_orchestrator import rank_models, echo_query, get_river_brain
from app.core.river_deliberation import deliberate_and_learn
from app.ollama_handler import query_ollama

logger = logging.getLogger(__name__)

_PROJECTS_DIR = Path(_PROJECT_ROOT) / "sandbox" / "echo_projects"
_MAX_ECHO_PROJECTS = 20

# Bounds for the council-invocation pipeline (council_generate_project() and
# its helpers, below) — same "explicit cap, not unbounded" discipline as
# every other budget in this codebase (COUNCIL.md's 10000-char budget,
# Finding 82; _council_review_core_edit()'s 4000-char diff cap).
_MAX_PLANNED_FILES = 6
_MAX_SIBLING_CONTEXT_CHARS = 6000
_MAX_REVIEW_CONTEXT_CHARS = 6000

# Flat filenames only (V1 scope — see module docstring): no slashes, no
# ".." traversal, no non-ASCII (excluded by the charset itself, so
# homoglyph tricks are moot), length-capped the same way _slugify()'s own
# max_len=40 already is. Real security fix, not council-specific: filenames
# used to reach generate_project()'s write_text() call with zero
# validation, safe only because every caller so far used hardcoded, human-
# chosen names. F2's kernel sandbox provides no backstop here — that write
# happens in this process, before any subprocess starts.
_VALID_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,40}\.py$")


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
                   f2_result: "dict | None", ts: str,
                   council_plan: "str | None" = None,
                   council_review: "dict | None" = None,
                   origin: "str | None" = None) -> Path:
    lines = [
        "# ECHO PROJECT — not loaded, not promoted, for human review only.",
        f"# Generated: {ts}",
        f"# Origin: {origin or 'unknown'}",
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
    if council_plan:
        lines.append("#")
        lines.append("# Council plan (multi-model deliberation, task_type=general):")
        for line in council_plan.strip().splitlines():
            lines.append(f"#   {line}")
    if council_review is not None:
        lines.append("#")
        lines.append(f"# Council review (advisory only, never gates a write): {council_review.get('verdict')}")
        for vote in council_review.get("votes", []):
            lines.append(f"#   {vote.get('model')}: {vote.get('verdict')} — {vote.get('rationale')}")
        if council_review.get("truncated_note"):
            lines.append(f"#   note: {council_review['truncated_note']}")
    report_path = project_dir / "_report.md"
    report_path.write_text("\n".join(lines) + "\n")
    return report_path


def generate_project(spec: str, files: dict,
                      council_plan: "str | None" = None,
                      council_review: "dict | None" = None,
                      origin: "str | None" = None) -> dict:
    """
    Core pipeline. `files` is a dict of {filename: code}, already generated
    by the caller (this function does not itself call an LLM) — must
    include "main.py" as the entry point; every other file is import-tested
    only (F1 scan + F2 import-mode survives), never executed.

    Runs the real, unmodified F1 (scan_for_unsafe_operations(), including
    the self-edit-escalation-call block) per file, then — only if every
    file passes F1 AND every filename is safe (see _VALID_FILENAME_RE) —
    stages all files into one fresh, timestamped project directory under
    sandbox/echo_projects/ and runs the real, unmodified F2 kernel sandbox
    against main.py. Writes a human-readable report either way.
    Deliberately stops there: NEVER calls save_code(), NEVER loads anything
    into the running process — this is the one invariant this whole
    feature's safety case depends on, verified live by liveness_ledger.py's
    echo_projects_no_escalation check.

    council_plan/council_review/origin are purely additive, optional context
    from council_generate_project() (below) — when given, they're rendered
    into the report as advisory context only; they never affect whether this
    function stages/writes/tests anything. Callers that don't pass them
    (e.g. a caller supplying hand-written files directly) are unaffected.

    Returns {"status": "invalid_filename"|"f1_failed"|"ok"|"f2_failed"|
    "error", "project_dir": str, "report_path": str, "f1_results": dict,
    "f2_result": dict|None}.
    """
    if not files or "main.py" not in files:
        return {"status": "error", "detail": "files must be a non-empty dict including 'main.py' as the entry point"}

    invalid = [name for name in files if not _VALID_FILENAME_RE.match(name)]
    if invalid:
        return {
            "status": "invalid_filename",
            "detail": f"filename(s) failed the flat-name safety check (no slashes, no '..', ASCII "
                      f"letters/digits/_/- only, .py, <=40 chars): {invalid}",
        }

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
        report = _write_report(project_dir, spec, files, f1_results, None, ts, council_plan, council_review, origin)
        logger.warning(f"[ECHO-PROJECTS] F1 blocked one or more files in {project_dir.name}")
        return {
            "status": "f1_failed", "project_dir": str(project_dir),
            "report_path": str(report), "f1_results": f1_results, "f2_result": None,
        }

    try:
        for filename, code in files.items():
            (project_dir / filename).write_text(code)
    except OSError as e:
        return {"status": "error", "detail": f"failed writing staged file(s): {e}"}

    f2_result = _run_f2_multi_file(project_dir)
    report = _write_report(project_dir, spec, files, f1_results, f2_result, ts, council_plan, council_review, origin)
    status = "ok" if f2_result.get("passed") else "f2_failed"
    logger.info(f"[ECHO-PROJECTS] {project_dir.name}: {status}")
    return {
        "status": status, "project_dir": str(project_dir),
        "report_path": str(report), "f1_results": f1_results, "f2_result": f2_result,
    }


# ── Council invocation — the missing caller (2026-07-23) ────────────────
# generate_project() above only ever had synthetic/hand-written test
# callers (Finding 83). This section builds the real one, using this
# codebase's existing, already-trusted multi-model mechanisms rather than
# inventing a new one: deliberate_and_learn() for planning,
# _council_review_core_edit()'s exact shape (duplicated, not imported —
# see below) for review, and echo_query()'s single-model-per-file pattern
# (the same one self_edit_manager.py's generate_code_from_plan() already
# uses) for the one step — actual code generation — this codebase has
# never tried to synthesize across multiple raw model outputs.

_PLAN_LINE_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])?\s*([A-Za-z0-9_\-]{1,40}\.py)\s*[:\-]\s*(.+?)\s*$")


def _strip_code_fences(text: str) -> str:
    """Strip a single leading/trailing markdown code fence if present —
    models sometimes wrap raw-code output in ```python ... ``` despite
    being told not to. Minimal, not a general markdown parser (that's
    self_edit_manager.py's job for its own, different pipeline)."""
    stripped = (text or "").strip()
    match = re.match(r"^```[a-zA-Z]*[ \t]*\n(.*?)\n```\s*$", stripped, re.DOTALL)
    if match:
        return match.group(1)
    return stripped


def _parse_file_plan(plan_text: str) -> list:
    """
    Parses "filename.py: description" lines (optionally list-prefixed, e.g.
    "- main.py: ..." or "1. main.py: ...") out of the council's free-text
    plan. Every candidate filename is filtered through the same flat-name
    safety check generate_project() itself enforces (_VALID_FILENAME_RE) —
    defense in depth, not redundant: this is the first point a
    hallucinated or adversarial filename could appear, well before it would
    otherwise reach generate_project()'s own check.

    Caps at _MAX_PLANNED_FILES, taking the first N in plan order. If
    "main.py" isn't among the parsed results, prepends a synthesized
    fallback entry so generate_project()'s existing require-main.py
    contract is always satisfied without this function needing to change
    that contract. If main.py IS present but not first, it's moved to the
    front — council_generate_project() always generates it first so later
    files are written to match what it already assumes.
    """
    seen = set()
    parsed = []
    for line in (plan_text or "").splitlines():
        m = _PLAN_LINE_RE.match(line)
        if not m:
            continue
        filename, description = m.group(1), m.group(2)
        if not _VALID_FILENAME_RE.match(filename) or filename in seen:
            continue
        seen.add(filename)
        parsed.append((filename, description[:200]))
        if len(parsed) >= _MAX_PLANNED_FILES:
            break

    if not parsed:
        # Genuinely nothing parseable in the raw text -- return empty so
        # the caller (council_generate_project) fails closed, rather than
        # unconditionally injecting a main.py fallback here, which would
        # make that fail-closed check unreachable (a real bug caught
        # during testing: a garbage/empty plan_text used to silently
        # produce [("main.py", <generic fallback description>)] instead of
        # [], masking the failure instead of surfacing it).
        return []

    if not any(name == "main.py" for name, _ in parsed):
        parsed.insert(0, ("main.py", "Entry point tying the other generated files together."))
        parsed = parsed[:_MAX_PLANNED_FILES]
    else:
        parsed.sort(key=lambda pair: pair[0] != "main.py")  # stable sort: main.py to front, rest keep order

    return parsed


def _council_review_project(spec: str, files: dict) -> dict:
    """
    Advisory-only multi-model review of a generated multi-file project.
    Same shape as self_edit_manager.py's _council_review_core_edit() (rank
    the top coding models, ask each for one-line APPROVE/REJECT + a
    rationale) — deliberately duplicated rather than imported, to keep this
    change's footprint off self_edit_manager.py (see CLAUDE.md Finding 84).
    NEVER gates a write: generate_project() is always called regardless of
    verdict, verified live by liveness_ledger.py's
    echo_projects_council_advisory check.
    """
    try:
        models = rank_models(task_type="coding")[:3]
    except Exception:
        models = []
    if not models:
        return {"verdict": "NO_COUNCIL_AVAILABLE", "votes": []}

    combined = ""
    included = []
    for filename, code in files.items():
        block = f"# --- {filename} ---\n{code}\n"
        if len(combined) + len(block) > _MAX_REVIEW_CONTEXT_CHARS:
            break
        combined += block
        included.append(filename)

    truncated_note = None
    if len(included) < len(files):
        truncated_note = f"{len(included)} of {len(files)} files shown to reviewers (review context budget)"

    review_prompt = (
        "You are reviewing a generated multi-file Python project, produced with "
        "full library access (no import restriction) inside an isolated sandbox. "
        "It has NOT been loaded anywhere and cannot be without a separate, "
        "human-reviewed step. Assess correctness and safety risk only, not style.\n\n"
        f"Spec: {spec}\n\n"
        f"Files ({', '.join(included)}{' ...' if truncated_note else ''}):\n```\n{combined}\n```\n\n"
        "Respond with exactly one line: APPROVE or REJECT, followed by a dash "
        "and one sentence why."
    )

    votes = []
    for model in models:
        try:
            resp = query_ollama(review_prompt, model=model) or ""
            first_word = resp.strip().split()[0].upper().strip(".:-") if resp.strip() else "REJECT"
            verdict = "APPROVE" if first_word.startswith("APPROVE") else "REJECT"
            votes.append({"model": model, "verdict": verdict, "rationale": resp.strip()[:300]})
        except Exception as e:
            votes.append({"model": model, "verdict": "REJECT", "rationale": f"review call failed: {e}"})

    approvals = sum(1 for v in votes if v["verdict"] == "APPROVE")
    result = {"verdict": f"{approvals}/{len(votes)} APPROVE", "votes": votes}
    if truncated_note:
        result["truncated_note"] = truncated_note
    return result


def council_generate_project(spec: str, source: str = "manual",
                              origin_note: "str | None" = None) -> dict:
    """
    The missing caller for generate_project(): plans, generates, and
    reviews a real multi-file project using this codebase's existing,
    already-trusted council mechanisms. Genuinely multi-model at two of
    the three steps (planning, review); single-model at the one step
    (per-file code generation) this codebase has never tried to synthesize
    across multiple raw model outputs — the same reason self-edit's own
    code generation doesn't either.

    1. PLAN — deliberate_and_learn(task_type="general", deliberately NOT
       "coding"): the plan is prose, not code. Scoring prose with the
       coding task's AST-based quality evaluator would silently
       contaminate that RiverBrain bucket's learned stats — the same class
       of cross-training contamination CLAUDE.md's Finding 3 already found
       and fixed once for a different mechanism.
    2. GENERATE — one echo_query(task_type="echo_projects_coding") call
       per planned file, main.py first, each given every previously-
       generated file's full content (capped) so later files stay
       consistent with what earlier ones already committed to (the only
       real cross-file-awareness mechanism in this pipeline — without it,
       F1/F2 would only catch syntax/import problems, never main.py
       calling a function helper.py never actually defines). Deliberately
       a separate RiverBrain bucket from plain "coding" (not reused, as
       Finding 84 originally chose for the rare manual-only case) — once
       this fires autonomously several times a day, volume alone would
       otherwise let self-directed project code dominate the bucket meant
       to reflect real conversational coding help.
    3. REVIEW — _council_review_project(), advisory only.

    Then calls the real, unmodified generate_project() — F1/F2/report,
    exactly as already shipped and tested (Finding 83). Never calls
    save_code(), never loads anything into the running process.

    `source` ("manual" from !project, or "autonomous" from the background
    loop) tags echo_query()'s own source field (f"echo_projects_{source}",
    distinguishing the two in interaction_log.jsonl) and, together with
    `origin_note`, becomes the report's "Origin" line — a manual call gets
    a fixed "manual (!project command)" note; the autonomous loop supplies
    its own note naming the real curiosity-garden question (or fallback
    theme) that inspired the spec.

    Cost, stated plainly: this is several real model calls (1 planning
    deliberation + N per-file generations, each of which internally runs
    its own council deliberation + synthesis, + up to 3 review calls) — a
    human invoking !project (or the autonomous loop, on its own cadence)
    should expect it to take a while, the same tradeoff self-edit's own
    hourly cycle already accepts for one file.
    """
    plan_prompt = (
        "You are planning a small, multi-file Python project. Given the "
        "following request, list the files needed as one line per file, in "
        "the exact format 'filename.py: one-line description of what it "
        "contains'. Always include a 'main.py' as the real entry point. "
        f"Keep it to at most {_MAX_PLANNED_FILES} files total, flat (no "
        "subdirectories), no markdown formatting.\n\n"
        f"Request: {spec}"
    )
    try:
        from app.core.echo_model_orchestrator import MODEL_POOL  # lazy — see import note above
        plan_text = deliberate_and_learn(
            plan_prompt, task_type="general",
            river_brain=get_river_brain(), model_pool=MODEL_POOL,
        ) or ""
    except Exception as e:
        return {"status": "error", "detail": f"council planning failed: {e}"}

    planned_files = _parse_file_plan(plan_text)
    if not planned_files:
        return {"status": "error", "detail": "council failed to produce a usable file plan", "council_plan": plan_text}

    files = {}
    for filename, description in planned_files:
        sibling_context = ""
        if files:
            joined = "\n\n".join(f"# --- {n} ---\n{c}" for n, c in files.items())
            sibling_context = (
                "\n\nFiles already written in this same project (for consistency):\n```\n"
                f"{joined[:_MAX_SIBLING_CONTEXT_CHARS]}\n```"
            )
        file_prompt = (
            f"You are writing one file, {filename}, as part of a multi-file Python project.\n"
            f"Overall request: {spec}\n"
            f"Project plan:\n{plan_text[:_MAX_SIBLING_CONTEXT_CHARS]}\n"
            f"This file's purpose: {description}"
            f"{sibling_context}\n\n"
            f"Write ONLY the real, complete Python source for {filename}. No markdown "
            f"fences, no prose before or after — just the code."
        )
        try:
            code = echo_query(file_prompt, task_type="echo_projects_coding", source=f"echo_projects_{source}") or ""
        except Exception as e:
            code = f"# generation failed: {e}\n"
        files[filename] = _strip_code_fences(code)

    review = _council_review_project(spec, files)
    origin = origin_note or ("manual (!project command)" if source == "manual" else f"{source} cycle")
    return generate_project(spec, files, council_plan=plan_text, council_review=review, origin=origin)


# ── Autonomous invocation — the loop, not just the pipeline (2026-07-24) ────
# council_generate_project() above was only ever reachable via the manual
# !project command. Gremlin was direct that manual-invocation-shaped
# features don't serve continuous, unattended operation — this section is
# the autonomous caller, run.py's new background thread's only real job
# being to call autonomous_generate_project() on a gated cadence.

_AUTONOMY_STATE_PATH = os.path.join(_PROJECT_ROOT, "memory", "echo_projects_autonomy_state.json")

# Fallback seed themes, used only if the curiosity garden read fails or is
# genuinely empty — real garden entries (question_garden.jsonl) are
# philosophical/relational, not build-project-shaped by nature (confirmed
# directly: no category cluster there is already code-shaped), so these are
# a small, real BASE_THOUGHT_CHEST analog for this pipeline specifically,
# not a disguised default path.
_FALLBACK_SEED_THEMES = (
    "a small text-based adventure game with a handful of connected rooms",
    "a simple command-line tool that tracks and summarizes a list of tasks",
    "a toy simulation of a small ecosystem with a few interacting species",
    "a command-line utility that generates simple ASCII art from text input",
    "a small program that plays a basic guessing or number game with the user",
)


def _build_autonomous_spec() -> tuple:
    """
    Returns (spec: str, spec_source: "garden"|"fallback", origin_note: str).
    select_from_garden() is confirmed read-only (no _save_garden() call,
    no times_asked/last_asked mutation anywhere in it) — safe to call here
    with no side effects on the real garden.
    """
    try:
        from app.core.garden_manager import select_from_garden
        entry = select_from_garden()
    except Exception:
        entry = None

    if entry and entry.get("question"):
        question = entry["question"]
        spec = (
            "Design and build a small, self-contained Python program that "
            "explores, models, or illustrates the following idea in some "
            "concrete way (a simulation, a toy model, an interactive text "
            "scenario, a data visualization, etc.) — creative interpretation "
            f"is expected: {question}"
        )
        origin_note = f"autonomous cycle, inspired by curiosity garden entry: {question}"
        return spec, "garden", origin_note

    import random as _random
    theme = _random.choice(_FALLBACK_SEED_THEMES)
    spec = f"Design and build {theme}."
    origin_note = f"autonomous cycle, fallback seed theme (garden unavailable): {theme}"
    return spec, "fallback", origin_note


def _write_autonomy_state(status: str, spec_source: str) -> None:
    state = {
        "last_run_utc": datetime.now(timezone.utc).isoformat(),
        "last_status": status,
        "spec_source": spec_source,
    }
    try:
        os.makedirs(os.path.dirname(_AUTONOMY_STATE_PATH), exist_ok=True)
        tmp = _AUTONOMY_STATE_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, _AUTONOMY_STATE_PATH)
    except Exception as e:
        logger.warning(f"[ECHO-PROJECTS] Failed to write autonomy state file: {e}")


def autonomous_generate_project() -> dict:
    """
    The real autonomous entry point, called by run.py's new gated
    background thread. Picks a real spec from Echo's own current curiosity
    state (or a fixed fallback theme if the garden is unavailable), calls
    council_generate_project(source="autonomous"), and records the outcome
    to a small state file (memory/echo_projects_autonomy_state.json) that
    liveness_ledger.py's echo_projects_autonomy_activity check reads.

    Never raises — a failure here is logged and recorded via the state
    file rather than propagating into the caller's own thread loop, which
    would otherwise abort the whole `while True:` cycle rather than just
    this one gated invocation.
    """
    spec, spec_source, origin_note = _build_autonomous_spec()
    try:
        result = council_generate_project(spec, source="autonomous", origin_note=origin_note)
        status = result.get("status", "unknown")
    except Exception as e:
        result = {"status": "error", "detail": f"autonomous_generate_project failed: {e}"}
        status = "error"
        logger.warning(f"[ECHO-PROJECTS] Autonomous cycle raised: {e}")

    _write_autonomy_state(status, spec_source)
    logger.info(f"[ECHO-PROJECTS] Autonomous cycle: status={status} spec_source={spec_source}")
    return result
