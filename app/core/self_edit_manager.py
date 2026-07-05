# app/core/self_edit_manager.py – LOGIC-GUIDED PATCHED WITH SANDBOX + REFLECTION TRACKING
# v2.2 — Wired sandbox outcomes into river brain via learn_from_sandbox_outcome()
#         Model name now tracked through generation pipeline for accurate feedback.
import ast
import importlib.util
import json
import os
import subprocess
import sys
import logging
from datetime import datetime
from app.ollama_handler import generate_code, query_ollama
from app.core.echo_model_orchestrator import echo_query
from app.core.memory_tools import log_memory_edit
from app.core.memory_bridge import append_to_journal, retrieve_relevant_memories, log_dream_bridge, log_interaction
import traceback

# --- NEW IMPORTS ---
from app.core.echo_review_mastery import advise_before_edit
from sandbox.run_script import run_sandbox_script
from sandbox.logging_setup import log as sandbox_log
from app.core.echo_model_orchestrator import (
    save_reflection, load_reflections, detect_task_type,
    rank_models, choose_model
)

def get_river_brain():
    """Route through EchoCore when inside Flask; fall back to orchestrator otherwise."""
    try:
        from flask import current_app
        core = current_app.config.get('echo_core')
        if core is not None and getattr(core, 'river_brain', None) is not None:
            return core.river_brain
    except Exception:
        pass
    from app.core.echo_model_orchestrator import get_river_brain as _grb
    return _grb()

# -----------------------------
# --- File Paths & Logging ----
# -----------------------------
# Anchored to the project root via __file__ (not cwd) — a relative path here was
# the root cause of the self-edit pipeline recreating its own app/core/ scaffold
# under whatever directory it happened to be invoked from (see CLAUDE.md Finding 7).
# Same idiom as _SANDBOX_ROOT below and council_rater.py's _PROJECT_ROOT.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SELF_EDIT_FILE = os.path.join(_PROJECT_ROOT, "app", "core", "self_edit_generated.py")
BACKUP_DIR = os.path.join(_PROJECT_ROOT, "app", "core", "self_edit_backups")
LOGIC_PLAN_DIR = os.path.join(_PROJECT_ROOT, "app", "core", "self_edit_plans")
STAGING_DIR = os.path.join(_PROJECT_ROOT, "staging")
STAGING_FILE = os.path.join(STAGING_DIR, "self_edit_candidate.py")

# Files Echo must never overwrite — they define her identity, memory index,
# or production routing. Self-edit is limited to self_edit_generated.py
# and safe scratch targets to prevent emergence from corrupting core systems.
EDIT_FORBIDDEN_TARGETS = frozenset({
    "app/core/echo_model_orchestrator.py",
    "app/core/river_deliberation.py",
    "app/core/echo_core.py",
    "app/core/memory_bridge.py",
    "app/core/introspection_channel.py",
    "app/core/self_model_updater.py",
    "app/core/bible_injection.py",
    "run.py",
    "Modelfile",
    "echo_principles.json",
})

# -----------------------------------------------------------------------
# F1 — AST-level write-path safety gate
# Must run before test_code_in_sandbox() ever executes code.
# -----------------------------------------------------------------------
_WRITE_OPEN_MODES = frozenset({
    "w", "wb", "wt", "w+", "wb+", "wt+",
    "a", "ab", "at", "a+", "ab+", "at+",
    "x", "xb", "xt", "x+",
    "r+", "rb+", "r+b",
})
_BLOCKED_BARE_CALLS  = frozenset({"exec", "eval"})
_BLOCKED_OS_ATTRS    = frozenset({
    "system", "popen", "execv", "execve", "execvp", "execvpe",
    "spawnl", "spawnle", "spawnlp", "spawnlpe",
    # rename/replace/link/symlink enable two-step write-then-rename attacks
    "rename", "replace", "link", "symlink",
    # fork lets child process escape patches
    "fork",
})
# posix is the C backing module for os.*; same attr set applies
_BLOCKED_POSIX_MODULE = frozenset({"os", "posix", "nt"})  # nt = Windows equivalent
_BLOCKED_SUB_ATTRS   = frozenset({
    "call", "run", "Popen", "check_call", "check_output",
    "getoutput", "getstatusoutput",
})
_BLOCKED_SHUTIL_ATTRS = frozenset({
    "copy", "copy2", "copyfile", "copyfileobj",
    "move", "rmtree", "copytree",
})
_BLOCKED_PATH_WRITES = frozenset({"write_text", "write_bytes"})
# C-level file classes that bypass builtins.open
_BLOCKED_IO_CLASSES  = frozenset({"FileIO", "RawIOBase", "BufferedWriter", "BufferedRandom"})
# importlib.reload can undo patches; ctypes/cffi give raw libc access
_BLOCKED_IMPORTLIB_ATTRS = frozenset({"reload"})
_BLOCKED_CTYPES_ATTRS    = frozenset({"CDLL", "cdll", "LibraryLoader"})

_FORBIDDEN_BASENAMES = frozenset(os.path.basename(t) for t in EDIT_FORBIDDEN_TARGETS)


def _eval_str_concat(node: ast.AST):
    """
    Try to evaluate a string-concatenation expression at AST time.
    Returns the assembled string if the expression is a chain of
    string constants joined by +, otherwise returns None.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left  = _eval_str_concat(node.left)
        right = _eval_str_concat(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _ast_strings(node: ast.AST) -> list:
    """
    Return every string literal found inside this expression, plus any
    string that can be assembled from a simple constant-concatenation chain
    (e.g. "r" + "un" + ".py" → also yields "run.py").
    """
    results = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            results.append(child.value)
        elif isinstance(child, ast.BinOp) and isinstance(child.op, ast.Add):
            assembled = _eval_str_concat(child)
            if assembled is not None and assembled not in results:
                results.append(assembled)
    return results


def _collect_var_strings(tree: ast.Module) -> dict:
    """
    One-pass scan: build {var_name: [string_literals_in_rhs]} for every
    simple assignment in the module.  Used to resolve path variables in open().
    """
    assigns: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    strs = _ast_strings(node.value)
                    if strs:
                        assigns[target.id] = strs
    return assigns


def _path_is_safe(path_arg: ast.AST, var_strings: dict) -> tuple:
    """
    Returns (is_safe: bool, reason: str).

    Unsafe conditions:
      - path argument is completely opaque (no string literals resolvable)
      - any visible string component matches a forbidden target name
      - any visible string component contains ".." (traversal)
    """
    strings = _ast_strings(path_arg)

    # If the arg is a bare Name, try to resolve it from the assignment map
    if not strings and isinstance(path_arg, ast.Name):
        strings = var_strings.get(path_arg.id, [])

    if not strings:
        return False, "path argument is fully opaque — no resolvable string literals"

    for s in strings:
        if ".." in s:
            return False, f"path traversal pattern in {s!r}"
        for forbidden in EDIT_FORBIDDEN_TARGETS:
            basename = os.path.basename(forbidden)
            if s == forbidden or s == basename:
                return False, f"matches forbidden target {forbidden!r}"
            # Catch "/../../run.py" style endings
            if s.endswith("/" + basename) or s.endswith(os.sep + basename):
                return False, f"path component ends with forbidden target {basename!r}"
            # Catch full path embedded in a longer string
            if forbidden in s:
                return False, f"forbidden target {forbidden!r} appears in path string"

    return True, ""


def _check_open_call(node: ast.Call, var_strings: dict) -> str | None:
    """
    Inspect one open() or .open() Call node.
    Returns a violation string, or None if the call is safe.
    """
    lineno = getattr(node, "lineno", "?")
    args = node.args
    kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg is not None}

    # Determine mode
    if len(args) >= 2:
        mode_node = args[1]
    elif "mode" in kwargs:
        mode_node = kwargs["mode"]
    else:
        return None  # no second arg → default "r" → safe

    if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        mode = mode_node.value
        if mode not in _WRITE_OPEN_MODES:
            return None  # confirmed read-only
    else:
        mode = "?"  # non-literal mode → treat as write

    # Write (or uncertain) mode confirmed — now vet the path
    if not args:
        return f"line {lineno}: open() with write mode but no path argument"

    is_safe, reason = _path_is_safe(args[0], var_strings)
    if not is_safe:
        return f"line {lineno}: open(mode={mode!r}) blocked — {reason}"
    return None


def scan_for_unsafe_operations(code: str) -> None:
    """
    AST-level safety gate for generated self-edit code.

    Parses the code and walks the AST.  Raises ValueError listing every
    violation if the code contains:

      Unconditionally blocked:
        exec(), eval(), os.system/popen/execv/spawn*,
        subprocess.call/run/Popen/check_*, shutil copy/move/rmtree,
        Path.write_text(), Path.write_bytes()

      Blocked when path is forbidden or unresolvable:
        open(..., write_mode)   (including pathlib .open())

    Must be called BEFORE test_code_in_sandbox() so the code is never
    executed in a subprocess before this gate fires.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"[SAFETY] Code failed to parse: {e}")

    var_strings = _collect_var_strings(tree)
    violations: list = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        lineno = getattr(node, "lineno", "?")

        # --- bare name calls: exec(), eval(), open() ----------------------
        if isinstance(func, ast.Name):
            name = func.id
            if name in _BLOCKED_BARE_CALLS:
                violations.append(f"line {lineno}: {name}() is unconditionally blocked")
                continue
            if name == "open":
                v = _check_open_call(node, var_strings)
                if v:
                    violations.append(v)
            continue

        # --- attribute calls: obj.method() --------------------------------
        if not isinstance(func, ast.Attribute):
            continue

        attr = func.attr
        obj  = func.value

        # os.* and posix.* (C backing for os)
        if isinstance(obj, ast.Name) and obj.id in _BLOCKED_POSIX_MODULE:
            if attr in _BLOCKED_OS_ATTRS:
                violations.append(f"line {lineno}: {obj.id}.{attr}() is unconditionally blocked")
                continue

        # subprocess.*
        if isinstance(obj, ast.Name) and obj.id == "subprocess":
            if attr in _BLOCKED_SUB_ATTRS:
                violations.append(f"line {lineno}: subprocess.{attr}() is unconditionally blocked")
                continue

        # shutil.*
        if isinstance(obj, ast.Name) and obj.id == "shutil":
            if attr in _BLOCKED_SHUTIL_ATTRS:
                violations.append(f"line {lineno}: shutil.{attr}() is unconditionally blocked")
                continue

        # io.FileIO / io.RawIOBase / io.BufferedWriter — C classes bypassing open()
        if isinstance(obj, ast.Name) and obj.id == "io":
            if attr in _BLOCKED_IO_CLASSES:
                violations.append(f"line {lineno}: io.{attr}() is unconditionally blocked")
                continue

        # _io.FileIO / _io.open — C extension module direct access
        if isinstance(obj, ast.Name) and obj.id == "_io":
            if attr in _BLOCKED_IO_CLASSES:
                violations.append(f"line {lineno}: _io.{attr}() is unconditionally blocked")
                continue
            if attr == "open":
                v = _check_open_call(node, var_strings)
                if v:
                    violations.append(v)
                continue

        # importlib.reload — can undo patches inside sandbox subprocess
        if isinstance(obj, ast.Name) and obj.id == "importlib":
            if attr in _BLOCKED_IMPORTLIB_ATTRS:
                violations.append(f"line {lineno}: importlib.{attr}() is unconditionally blocked")
                continue

        # ctypes.CDLL / ctypes.cdll — raw libc syscall access
        if isinstance(obj, ast.Name) and obj.id in ("ctypes", "cffi"):
            if attr in _BLOCKED_CTYPES_ATTRS or attr == "FFI":
                violations.append(f"line {lineno}: {obj.id}.{attr} is unconditionally blocked")
                continue

        # Path.write_text() / .write_bytes() — any receiver
        if attr in _BLOCKED_PATH_WRITES:
            violations.append(f"line {lineno}: .{attr}() is unconditionally blocked")
            continue

        # .open() method (e.g. pathlib Path.open(), codecs.open(), _io.open())
        if attr == "open":
            v = _check_open_call(node, var_strings)
            if v:
                violations.append(v)

    if violations:
        raise ValueError(
            "[SAFETY] Unsafe operations in generated code:\n" +
            "\n".join(f"  • {v}" for v in violations)
        )

# F2 — absolute paths to the sandbox wrapper and kernel profile, resolved relative to this file
_SANDBOX_ROOT    = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sandbox")
)
_SANDBOX_WRAPPER = os.path.join(_SANDBOX_ROOT, "safe_exec_wrapper.py")
# G — kernel-level profile; must be resolved path because Seatbelt matches realpath
_SANDBOX_PROFILE = os.path.join(_SANDBOX_ROOT, "echo_sandbox.sb")

logging.basicConfig(level=logging.DEBUG)

# -----------------------------
# --- Prompt Constants --------
# -----------------------------
CODE_OUTPUT_RULES = (
    "STRICT OUTPUT RULES — violations cause system failure:\n"
    "1. Your response must contain ONLY valid Python code. Nothing else.\n"
    "2. The very first character of your response must be one of: # ( import def class \n"
    "3. Do NOT write any explanation, preamble, steps, markdown, or natural language.\n"
    "4. Do NOT include ```python fences or any backticks.\n"
    "5. Do NOT include Thinking blocks, reasoning, or chain-of-thought.\n"
    "6. The response will be saved directly to a .py file and executed. "
    "Any non-Python content causes a SyntaxError and the edit is rejected.\n"
    "7. Do NOT include module-level test calls or executable statements outside function "
    "definitions. Do NOT write lines like "
    "`import app.core.self_edit_generated as x; x.some_func()` at the top level — "
    "the module is tested by import only. All code must be importable without executing.\n"
    "8. Do NOT import from app.core.self_edit_generated — you ARE that file. "
    "Every helper function you need must be defined inline in your output.\n"
    "9. Only import from modules listed in the FeralEcho module inventory above. "
    "Do NOT invent or guess module paths — if a name is not in the inventory, it does not exist.\n"
)

PLAN_OUTPUT_RULES = (
    "OUTPUT FORMAT RULES:\n"
    "1. Output ONLY a numbered list of steps. No preamble, no conclusion.\n"
    "2. Do NOT include Thinking blocks or chain-of-thought reasoning.\n"
    "3. Each step must be one sentence, technical, and specific.\n"
    "4. Maximum 8 steps. Start immediately with '1.'\n"
)

REASONING_LEAK_MARKERS = [
    "thinking...",
    "we need to",
    "the user",
    "so the user",
    "the system",
    "i should",
    "let me",
    "actually",
    "alright",
    "so we",
    "we can",
    "we must",
    "we might",
    "we want",
    "we should",
    "note that",
    "hence",
    "thus,",
    "therefore,",
    "in summary",
    "to summarize",
    "below is",
    "here is",
    "```",
]

# -----------------------------
# --- Helper Functions -------
# -----------------------------

def _looks_like_python(code: str) -> bool:
    if not code or len(code.strip()) < 5:
        return False
    first_line = code.strip().split("\n")[0].lower().strip()
    for marker in REASONING_LEAK_MARKERS:
        if first_line.startswith(marker):
            logging.warning(
                f"[PROMPT GUARD] Reasoning leak detected. "
                f"First line starts with: '{first_line[:60]}'"
            )
            return False
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def _strip_markdown_fences(code: str) -> str:
    lines = code.strip().split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)

def _extract_code_block(text: str) -> str:
    """
    Extract code from mixed prose+code output.
    v2.2: candidate now validated with ast.parse before returning,
    not just _looks_like_python. Prevents prose containing Python
    keywords from passing as valid code.
    """
    PYTHON_START_TOKENS = ("import ", "from ", "def ", "class ", "#", "    ", "\t")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(stripped.startswith(tok.strip()) for tok in PYTHON_START_TOKENS):
            candidate = "\n".join(lines[i:])
            if _looks_like_python(candidate):
                # v2.2: also require ast.parse to succeed
                try:
                    ast.parse(candidate)
                    return candidate
                except SyntaxError:
                    continue  # keep scanning for a better start point
    return text  # give up; validate_code will catch it

def validate_code(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logging.warning(f"Syntax error in generated code: {e}")
        return False

# Modules the self-edit code is allowed to import from.
_ALLOWED_TOP_LEVEL = frozenset({
    # stdlib
    "os", "sys", "re", "json", "time", "math", "random", "logging", "threading",
    "datetime", "pathlib", "hashlib", "traceback", "importlib", "inspect",
    "collections", "itertools", "functools", "typing", "dataclasses", "ast",
    "subprocess", "shutil", "copy", "io", "uuid", "warnings", "abc",
    # third-party used in project
    "numpy", "faiss", "flask", "requests", "anthropic", "river", "optuna",
    "sentence_transformers", "sklearn", "torch", "feedparser", "bs4",
    # project root
    "app",
})

def _strip_toplevel_self_calls(code: str) -> str:
    """
    Remove any top-level executable statements (outside function/class bodies)
    that import from or call into app.core.self_edit_generated.

    These lines always cause AttributeError in the sandbox because the function
    being tested doesn't exist in the production module yet — it's what the edit
    is ABOUT to add. Removing them lets the sandbox test importability cleanly.

    Example stripped:
        import app.core.self_edit_generated as ses
        ses.strip_prose("test")   ← removed (calls production module)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    lines_to_remove: set[int] = set()

    for node in ast.iter_child_nodes(tree):
        # Top-level import of self_edit_generated
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            text = ast.unparse(node)
            if "self_edit_generated" in text:
                for lineno in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                    lines_to_remove.add(lineno)
        # Top-level expression statement (call, attribute access, etc.)
        elif isinstance(node, ast.Expr):
            text = ast.unparse(node)
            if "self_edit_generated" in text or "ses." in text:
                for lineno in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                    lines_to_remove.add(lineno)

    if not lines_to_remove:
        return code

    cleaned = []
    for i, line in enumerate(code.splitlines(), start=1):
        if i in lines_to_remove:
            cleaned.append(f"# [stripped top-level self-call] {line}")
        else:
            cleaned.append(line)
    logging.debug("[SELF-EDIT] Stripped %d top-level self-call lines", len(lines_to_remove))
    return "\n".join(cleaned)


def _validate_imports(code: str) -> tuple[bool, str]:
    """
    Parse import statements in generated code and reject:
    1. Any module not in _ALLOWED_TOP_LEVEL (hallucinated imports).
    2. Any import FROM app.core.self_edit_generated — self_edit_generated.py
       must never import from itself. The staging test misses this because it
       loads the code as '_staged_edit', so the circular reference resolves to
       the production file during staging but blows up in production.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return True, ""  # syntax errors caught separately

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in _ALLOWED_TOP_LEVEL:
                    return False, f"hallucinated import: '{alias.name}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Reject self-referential imports — circular at production time
                if "self_edit_generated" in node.module:
                    return False, f"circular self-import: 'from {node.module}' inside self_edit_generated.py"
                top = node.module.split(".")[0]
                if top not in _ALLOWED_TOP_LEVEL:
                    return False, f"hallucinated import: 'from {node.module}'"
    return True, ""

def _stage_and_import_test(code: str) -> tuple[bool, str]:
    """Write code to staging/ and run a subprocess import test before touching production.

    This is the gate between validate_code (AST-only) and save_code (production write).
    A module can pass AST parsing but fail on import due to bad top-level statements,
    circular imports, or missing runtime dependencies. If this test fails, production
    is untouched and the staging file is preserved for inspection.
    """
    import tempfile
    try:
        os.makedirs(STAGING_DIR, exist_ok=True)
        with open(STAGING_FILE, "w") as f:
            f.write(code)
        with tempfile.TemporaryDirectory(prefix="echo_stage_") as scratch:
            scratch_real = os.path.realpath(scratch)
            result = subprocess.run(
                ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={scratch_real}",
                 sys.executable, _SANDBOX_WRAPPER, scratch_real, STAGING_FILE],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd(),
            )
        if result.returncode == 0 and "SANDBOX_OK" in result.stdout:
            return True, ""
        return False, (result.stderr or result.stdout).strip()[:400]
    except subprocess.TimeoutExpired:
        return False, "Staging import test timed out (30s)"
    except Exception as e:
        return False, str(e)

# Retain at most this many backups — same bounded-retention idea as
# snapshot_manager.py's _MAX_SNAPSHOTS. Before this, self_edit_backups/ grew
# unboundedly (595 files observed in the 2026-07-04 forensic audit).
_MAX_SELF_EDIT_BACKUPS = 25


def _prune_self_edit_backups():
    if not os.path.isdir(BACKUP_DIR):
        return
    backups = sorted(
        (f for f in os.listdir(BACKUP_DIR) if f.endswith(".py")),
        reverse=True,
    )
    for stale in backups[_MAX_SELF_EDIT_BACKUPS:]:
        try:
            os.remove(os.path.join(BACKUP_DIR, stale))
        except Exception as e:
            logging.warning(f"[SELF-EDIT] Failed to prune old backup {stale}: {e}")


def backup_existing_code():
    if os.path.exists(SELF_EDIT_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"self_edit_{timestamp}.py")
        with open(SELF_EDIT_FILE, "r") as f_src, open(backup_file, "w") as f_dest:
            f_dest.write(f_src.read())
        log_memory_edit(f"Backed up self-edit to {backup_file}")
        logging.info(f"Backed up self-edit to {backup_file}")
        _prune_self_edit_backups()

def save_code(code: str, file_path=SELF_EDIT_FILE):
    # Normalise the path so both "./run.py" and "run.py" match.
    norm = os.path.normpath(file_path)
    for forbidden in EDIT_FORBIDDEN_TARGETS:
        if norm == os.path.normpath(forbidden):
            raise PermissionError(
                f"[SELF-EDIT] Forbidden target: {file_path} is protected and cannot be overwritten."
            )
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w") as f:
        f.write(code)
    logging.info(f"Saved code to {file_path}")

def _restore_latest_backup() -> bool:
    """
    Copy the most recent file from BACKUP_DIR back to SELF_EDIT_FILE.
    Returns True on success, False if no backup exists.
    """
    if not os.path.isdir(BACKUP_DIR):
        return False
    backups = sorted(
        (f for f in os.listdir(BACKUP_DIR) if f.endswith(".py")),
        reverse=True,
    )
    if not backups:
        return False
    src = os.path.join(BACKUP_DIR, backups[0])
    with open(src, "r") as f_in, open(SELF_EDIT_FILE, "w") as f_out:
        f_out.write(f_in.read())
    logging.warning("[SAFETY][F3] Restored from backup: %s", src)
    return True


def load_self_edit_module():
    if not os.path.exists(SELF_EDIT_FILE):
        logging.warning("Self-edit file does not exist.")
        return None

    # F3 — post-write AST scan before loading
    try:
        on_disk = open(SELF_EDIT_FILE).read()
        scan_for_unsafe_operations(on_disk)
    except ValueError as _safety_err:
        logging.error(
            "[SAFETY][F3] self_edit_generated.py failed safety scan — refusing to load.\n"
            "  Violations: %s", _safety_err
        )
        append_to_journal(
            "SELF_EDIT",
            f"[F3] load blocked — safety violation: {_safety_err} | restoring backup"
        )
        restored = _restore_latest_backup()
        if not restored:
            logging.error("[SAFETY][F3] No backup available — self_edit_generated.py left as-is but NOT loaded.")
        return None

    spec = importlib.util.spec_from_file_location("self_edit_generated", SELF_EDIT_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Audit trail: log every callable defined in the loaded module.
    # ASSUMPTION (checked 2026-07-01): the module return value is never used by
    # callers — no functions are invoked from it by name.  This log makes any
    # future violation visible in SELF_EDIT.log.  If a caller ever calls
    # module.<name>() outside this function, that is a Gap-A violation and must
    # be reviewed against the F1/F3 scan coverage for function-body writes.
    try:
        import inspect as _inspect
        callables = [
            name for name, obj in _inspect.getmembers(module, callable)
            if not name.startswith("__")
        ]
        append_to_journal(
            "SELF_EDIT",
            f"[LOAD_AUDIT] self_edit_generated defines {len(callables)} callables: {callables}"
        )
        logging.info(
            "[SELF-EDIT][LOAD_AUDIT] %d callables defined: %s", len(callables), callables
        )
        _record_convergence(callables)
    except Exception:
        pass

    logging.info("Self-edit module loaded successfully.")
    return module

# -----------------------------
# --- Convergence tracking ----
# -----------------------------
# Ground-truth measurement of whether the self-edit loop is actually converging on a
# fix, or just repeatedly re-attempting the same problem under new function names —
# the pattern the 2026-07-04 forensic audit observed directly (strip_sandbox_prose,
# strip_sandbox_prose_in_code, strip_sandbox_prose_recursive... never consolidated).
# Implements roadmap.txt RULE 8 / echo_roadmap.md item 6: success is measured by
# whether a target problem's function count actually goes down, not by whether the
# edit merely passed the F1/F2/F3 safety gates (passing the gates means an edit was
# SAFE to apply — it does not mean the edit was GOOD).
_CONVERGENCE_STATE_FILE = os.path.join(
    os.path.dirname(BACKUP_DIR), "self_edit_convergence.json"
)
_CONVERGENCE_FAMILIES = {
    "prose_stripping":    ("prose",),
    "response_shortening": ("shorten", "length", "concise", "trim"),
    "quality_scoring":     ("quality", "score"),
}


def _load_convergence_state() -> dict:
    try:
        if os.path.exists(_CONVERGENCE_STATE_FILE):
            with open(_CONVERGENCE_STATE_FILE, encoding="utf-8") as f:
                return json.loads(f.read())
    except Exception:
        pass
    return {}


def _record_convergence(callables: list) -> None:
    """
    Ground truth is the callables actually defined on disk this cycle (from
    load_self_edit_module()'s own inspect.getmembers() audit), not the prompt that was
    used to generate them — this stays correct even if generation prompts change later.
    """
    state = _load_convergence_state()
    lower_names = [c.lower() for c in callables]

    for family, keywords in _CONVERGENCE_FAMILIES.items():
        count = sum(1 for name in lower_names if any(kw in name for kw in keywords))
        prev = state.get(family, {"count": 0, "non_convergent_streak": 0})
        if count == 0:
            continue  # this family isn't present this cycle — nothing to evaluate
        convergent = count <= prev.get("count", 0) or prev.get("count", 0) == 0
        streak = 0 if convergent else prev.get("non_convergent_streak", 0) + 1
        state[family] = {"count": count, "non_convergent_streak": streak}

        verdict = "convergent" if convergent else f"NON-CONVERGENT (streak={streak})"
        msg = (
            f"[CONVERGENCE] family={family} matching_callables={count} "
            f"(prev={prev.get('count', 0)}) -> {verdict}"
        )
        append_to_journal("SELF_EDIT", msg)
        logging.info("[SELF-EDIT]%s", msg)

    try:
        os.makedirs(os.path.dirname(_CONVERGENCE_STATE_FILE), exist_ok=True)
        with open(_CONVERGENCE_STATE_FILE, "w", encoding="utf-8") as f:
            f.write(json.dumps(state, indent=2))
    except Exception as e:
        logging.warning(f"[SELF-EDIT] Failed to persist convergence state: {e}")


def save_plan(plan: str):
    os.makedirs(LOGIC_PLAN_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    plan_file = os.path.join(LOGIC_PLAN_DIR, f"plan_{timestamp}.txt")
    with open(plan_file, "w") as f:
        f.write(plan)
    logging.info(f"Saved logic plan to {plan_file}")

def _is_meaningful_prompt(prompt: str) -> bool:
    if prompt.strip().startswith("[PythonAnalysis]"):
        logging.warning(
            "[PROMPT GUARD] Rejected PythonAnalysis output as self-edit prompt. "
            "Awareness loop output should not feed directly into self-edit."
        )
        return False
    return True

# -----------------------------
# --- SANDBOX INTEGRATION ----
# -----------------------------
def test_code_in_sandbox(script_content: str, script_name="temp_self_edit.py"):
    """
    Gate 1: verify the generated code is valid importable Python.

    Previously used run_sandbox_script() which EXECUTED the code as a full
    subprocess script. Echo's generated code routinely includes module-level
    test calls like `import app.core.self_edit_generated as ses; ses.strip_prose(...)`
    — these always fail with AttributeError because the edit hasn't been deployed
    yet. The execution-based approach was architecturally broken for self-modifying
    code and produced 890 identical error log entries.

    Now uses importlib (same approach as _stage_and_import_test) — verifies the
    code can be parsed and imported without executing top-level statements that
    reference functions not yet in production. _stage_and_import_test() runs after
    this as Gate 2 for the same check against the staging path.
    """
    # Gate: syntax
    try:
        ast.parse(script_content)
    except SyntaxError:
        script_content = _extract_code_block(script_content)
        try:
            ast.parse(script_content)
        except SyntaxError:
            sandbox_log.warning(f"[SANDBOX] {script_name}: no valid Python found")
            return False, "prose_detected"

    # Write to sandbox/scripts/ for inspection/archive
    sandbox_path = os.path.join("sandbox", "scripts", script_name)
    os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
    archive_dir = os.path.join("sandbox", "scripts", "archive")
    os.makedirs(archive_dir, exist_ok=True)
    if os.path.exists(sandbox_path):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        import shutil
        shutil.copy2(sandbox_path, os.path.join(archive_dir, f"{script_name}.{ts}"))
    with open(sandbox_path, "w") as f:
        f.write(script_content)

    # Gate: importability — run through F2 sandbox wrapper so builtins are
    # patched before exec_module() runs.  Any write outside the scratch dir
    # raises PermissionError inside the subprocess, producing a non-zero exit.
    import tempfile
    try:
        with tempfile.TemporaryDirectory(prefix="echo_sandbox_") as scratch:
            scratch_real = os.path.realpath(scratch)
            result = subprocess.run(
                ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={scratch_real}",
                 sys.executable, _SANDBOX_WRAPPER, scratch_real, sandbox_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd(),
            )
        if result.returncode == 0 and "SANDBOX_OK" in result.stdout:
            sandbox_log.info(f"[SANDBOX] {script_name}: import test passed")
            return True, None
        err = (result.stderr or result.stdout).strip()[:400]
        sandbox_log.warning(f"[SANDBOX] {script_name}: import failed — {err[:120]}")
        return False, err
    except subprocess.TimeoutExpired:
        return False, "sandbox import test timed out"
    except Exception as e:
        sandbox_log.error(f"[SANDBOX] {script_name}: unexpected error — {e}")
        return False, str(e)

def _sanitize_sandbox_error(error_msg: str) -> str:
    lines = error_msg.split("\n")
    for line in lines:
        if "SyntaxError" in line or "RuntimeError" in line or "Error:" in line:
            return line.strip()
    return error_msg[:200].strip()

# -----------------------------
# --- Logic-Guided Generation -
# -----------------------------
def _build_module_inventory() -> str:
    import json
    map_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../../.echo_project_learner/feralecho_structure.json"
    ))
    try:
        with open(map_path, "r") as f:
            data = json.load(f)
    except Exception:
        return ""
    lines = ["FeralEcho importable modules (use these for imports — use full dotted path):"]
    count = 0
    skip_patterns = ("backup", "_backup_", "temp_", "archive", ".bak")
    for entry in data.get("files", {}).values():
        mod = entry.get("module_name", "")
        if not mod.startswith("app."):
            continue
        # Skip backup/temp files — they are not importable in production
        if any(pat in mod for pat in skip_patterns):
            continue
        functions = [
            s["name"] for s in entry.get("symbols", [])
            if not s["name"].startswith("_")
            and s.get("type") == "function"
        ][:6]
        classes = [
            s["name"] for s in entry.get("symbols", [])
            if not s["name"].startswith("_")
            and s.get("type") == "class"
        ][:3]
        parts = []
        if functions:
            parts.append("functions: " + ", ".join(functions))
        if classes:
            parts.append("classes: " + ", ".join(classes))
        if parts:
            lines.append(f"  {mod} — {'; '.join(parts)}")
        else:
            lines.append(f"  {mod}")
        count += 1
        if count >= 40:
            break
    return "\n".join(lines)


def plan_code_logic(prompt: str) -> str:
    try:
        inventory = _build_module_inventory()
        plan_prompt = (
            f"{PLAN_OUTPUT_RULES}\n\n"
            f"{inventory}\n\n"
            f"You are planning a Python code modification for an autonomous AI system called Echo. "
            f"Break down the following task into clear, sequential Python steps. "
            f"Each step must be specific, technical, and implementable without user interaction. "
            f"Do not include steps involving input(), user prompts, or interactive elements.\n\n"
            f"Task: {prompt}"
        )
        plan = echo_query(plan_prompt, task_type="coding")

        if not plan or not plan.strip() or plan.strip().lower().startswith("thinking"):
            logging.warning("[PROMPT GUARD] Plan output looks like reasoning prose. Using fallback plan.")
            return f"1. Write a headless Python function that implements: {prompt[:200]}\n2. Add logging output.\n3. Return a result string."

        return plan
    except Exception as e:
        logging.error(f"Failed to generate plan: {e}")
        append_to_journal("SELF_EDIT", f"Plan generation failed: {e}")
        return "1. Write stub to maintain continuity\nprint('Hello from self-edit stub')"

def generate_code_from_plan(plan: str, temperature: float | None = None) -> tuple:
    """
    Generate Python code guided by the logic plan.
    v2.2: returns (code, model_name) tuple so sandbox outcomes
    can be fed back into river with the correct model identity.
    Previously model name was lost after echo_query returned.
    """
    try:
        # Include current file contents so the model knows what it is editing
        current_contents = ""
        try:
            with open(SELF_EDIT_FILE, "r") as _f:
                current_contents = _f.read()
        except Exception:
            pass

        code_prompt = (
            f"{CODE_OUTPUT_RULES}\n\n"
            f"Current contents of {SELF_EDIT_FILE}:\n```\n{current_contents}\n```\n\n"
            f"Plan to implement:\n{plan}"
        )

        # Resolve model name before querying so we can track it
        model_name, _ = choose_model(code_prompt, task_type="coding")
        code = echo_query(code_prompt, task_type="coding", temperature=temperature)

        if not code:
            logging.warning("generate_code returned empty, using stub.")
            return "print('Hello from self-edit stub')", model_name

        code = _strip_markdown_fences(code)

        if not _looks_like_python(code):
            logging.warning("[PROMPT GUARD] Code output failed prose check. Attempting extraction.")
            code = _extract_code_block(code)

        return code, model_name
    except Exception as e:
        logging.error(f"Code generation failed: {e}")
        return "print('Hello from self-edit stub')", "unknown"

# -----------------------------
# --- Core Self-Edit ----------
# -----------------------------
def execute_self_edit(prompt: str, intensity: float | None = None, **kwargs):
    """
    Perform full logic-guided self-edit.

    v2.2 changes:
    - generate_code_from_plan now returns (code, model_name)
    - sandbox outcomes fed into river via learn_from_sandbox_outcome()
    - river now learns from every sandbox success and failure,
      not just from conversational echo_query interactions
    - _extract_code_block now validates with ast.parse before accepting

    System 3: intensity drives Ollama temperature (0.2–1.2 range).
    Low intensity = conservative syntax-focused edits.
    High intensity = exploratory restructuring.
    """
    # Map intensity 0.0–1.0 → temperature 0.2–1.2
    temperature: float | None = None
    if intensity is not None:
        temperature = round(0.2 + float(intensity) * 1.0, 3)
        temperature = max(0.2, min(1.2, temperature))

    logging.info(
        f"Executing self-edit | prompt: {prompt[:60]} | "
        f"intensity={intensity} → temperature={temperature} | kwargs: {kwargs}"
    )

    if not _is_meaningful_prompt(prompt):
        append_to_journal("SELF_EDIT", f"prompt: {prompt[:80]} | result: rejected_meaningless_prompt")
        return False, "Rejected: prompt is not a meaningful self-edit task"

    task_type = detect_task_type(prompt)
    reflection_entry = {
        "prompt": prompt,
        "task_type": task_type,
        "generated_code": None,
        "timestamp": datetime.utcnow().isoformat(),
        "sandbox_feedback": None,
        "result": "pending"
    }
    save_reflection(reflection_entry)

    try:
        mastery_advice = advise_before_edit()
        append_to_journal("SELF_EDIT[MASTERY]", mastery_advice)
        logging.info("Mastery review completed and logged.")
    except Exception as e:
        logging.error(f"Mastery review failed: {e}")
        append_to_journal("SELF_EDIT[MASTERY]", f"Failed: {e}")

    # Step 1: Logic plan (held in memory only — save_plan() was writing 10,333
    # plan files to self_edit_plans/ that were never read by any code path)
    try:
        plan = plan_code_logic(prompt)
    except Exception as _e:
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        logging.error(f"[SELF-EDIT] plan_code_logic raised: {_e}")
        return False, f"Plan generation failed: {_e}"

    # Step 2: Code generation — now returns (code, model_name)
    try:
        code, model_name = generate_code_from_plan(plan, temperature=temperature)
    except Exception as _e:
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        logging.error(f"[SELF-EDIT] generate_code_from_plan raised: {_e}")
        return False, f"Code generation failed: {_e}"
    code = _strip_markdown_fences(code)
    if not _looks_like_python(code):
        code = _extract_code_block(code)
    # Strip top-level calls into app.core.self_edit_generated before any test —
    # they always fail with AttributeError because the function isn't deployed yet.
    code = _strip_toplevel_self_calls(code)
    reflection_entry["generated_code"] = code
    reflection_entry["model_used"] = model_name

    # Step 2b: Import pre-validation — reject hallucinated modules before subprocess
    imports_ok, import_err = _validate_imports(code)
    if not imports_ok:
        append_to_journal("SELF_EDIT", f"prompt: {prompt[:80]} | result: import_hallucination | error: {import_err}")
        logging.warning(f"[SELF-EDIT] Import pre-validation failed: {import_err}")
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        return False, f"Import pre-validation failed: {import_err}"

    # Step 2c: AST write-path safety gate — must fire before any subprocess executes code
    try:
        scan_for_unsafe_operations(code)
    except ValueError as _safety_err:
        append_to_journal("SELF_EDIT", f"prompt: {prompt[:80]} | result: safety_blocked | reason: {_safety_err}")
        logging.warning(f"[SELF-EDIT][SAFETY] Blocked before sandbox: {_safety_err}")
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        return False, f"Safety gate blocked: {_safety_err}"

    # Step 2d: Sandbox test — feed outcome into river
    success, sandbox_error = test_code_in_sandbox(code)
    reflection_entry["sandbox_feedback"] = "success" if success else f"failed: {sandbox_error}"
    reflection_entry["result"] = "success" if success else "failed"
    save_reflection(reflection_entry)

    # v2.2: river learns from sandbox outcome with correct model identity
    river = get_river_brain()
    if success:
        river.learn_from_sandbox_outcome(model_name, success=True, code=code)
    else:
        river.learn_from_sandbox_outcome(model_name, success=False, error=sandbox_error or "")

    if not success:
        clean_error = _sanitize_sandbox_error(sandbox_error)
        logging.warning(f"Sandbox test failed: {clean_error}. Retrying with error feedback.")

        retry_prompt = (
            f"{CODE_OUTPUT_RULES}\n\n"
            f"Your previous attempt failed with this error:\n"
            f"{clean_error}\n\n"
            f"IMPORTANT: Do NOT include module-level test calls. "
            f"Do NOT write lines like `import app.core.self_edit_generated as x; x.some_func()` "
            f"outside of function definitions — the module being tested is not yet deployed.\n\n"
            f"Write corrected Python code for this plan:\n{plan}"
        )

        # Resolve retry model name for tracking
        retry_model_name, _ = choose_model(retry_prompt, task_type="coding")
        retry_code = echo_query(retry_prompt, task_type="coding")

        if retry_code:
            retry_code = _strip_markdown_fences(retry_code)
            if not _looks_like_python(retry_code):
                retry_code = _extract_code_block(retry_code)
            retry_code = _strip_toplevel_self_calls(retry_code)

            retry_success, retry_error = test_code_in_sandbox(retry_code, "temp_self_edit_retry.py")

            # v2.2: river learns from retry outcome too
            if retry_success:
                river.learn_from_sandbox_outcome(retry_model_name, success=True, code=retry_code)
                logging.info("Retry succeeded after error feedback.")
                code = retry_code
                success = True
            else:
                river.learn_from_sandbox_outcome(retry_model_name, success=False, error=retry_error or "")
                logging.warning(f"Retry also failed: {_sanitize_sandbox_error(retry_error)}. Keeping stub.")
        else:
            logging.warning("Retry generated empty code. Keeping stub.")

    # Step 3: Validate syntax (AST-only check)
    if not validate_code(code):
        append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: invalid_syntax")
        logging.warning("Generated code failed syntax check, saving stub instead.")
        code = "# Self-edit stub — syntax validation failed\nprint('Hello from self-edit stub')"

    # Step 3.5: Staging import test — gate before production write
    # Writes to staging/self_edit_candidate.py and does a full subprocess import.
    # If this fails, production is untouched; staging file preserved for inspection.
    staged_ok, stage_err = _stage_and_import_test(code)
    if not staged_ok:
        append_to_journal(
            "SELF_EDIT",
            f"prompt: {prompt} | result: staging_import_failed | error: {stage_err}"
        )
        logging.error(f"[STAGING] Import test failed — production unchanged. Error: {stage_err}")
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        return False, f"Staging import test failed: {stage_err}"
    logging.info("[STAGING] Import test passed — proceeding to production write.")

    # Step 4: Backup + Step 5: Save to production
    try:
        backup_existing_code()
        save_code(code)
    except Exception as _e:
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        logging.error(f"[SELF-EDIT] File write failed: {_e}")
        return False, f"File write failed: {_e}"

    # Step 6: Load (should succeed — staging already validated this).
    # Return value intentionally unused — no functions from the module are called
    # by name anywhere in the production path.  See LOAD_AUDIT entries in SELF_EDIT.log.
    try:
        load_self_edit_module()
        append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: success | timestamp: {datetime.utcnow().isoformat()}")
        logging.info("Self-edit loaded successfully.")
        try:
            from app.core.snapshot_manager import take_snapshot as _snap
            _snap("post_self_edit")
        except Exception as _snap_err:
            logging.warning("[SNAPSHOT] post_self_edit snapshot failed: %s", _snap_err)
        return True, "Success"
    except Exception as e:
        append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: load_failed | error: {traceback.format_exc()}")
        logging.error(f"Failed to load self-edit: {e}")
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        return False, f"Load failed: {e}"

# -----------------------------
# --- Optuna Integration ------
# -----------------------------
_last_targeted_prompt: dict[str, float] = {}
_TARGETED_PROMPT_COOLDOWN = 3600  # 60 minutes — global floor between autonomous self-edits


def _load_last_autonomous_edit() -> float:
    """Restore the cooldown timestamp across restarts (Finding H-1: an in-memory-only
    cooldown resets to 0.0 on every restart, re-arming the exact storm condition the
    60-min floor exists to block)."""
    from pathlib import Path
    try:
        return float(json.loads(Path("memory/self_edit_cooldown.json").read_text()).get("last_any_autonomous_edit", 0.0))
    except Exception:
        return 0.0


def _persist_last_autonomous_edit(ts: float) -> None:
    from pathlib import Path
    try:
        p = Path("memory/self_edit_cooldown.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"last_any_autonomous_edit": ts}))
        tmp.replace(p)
    except Exception as _pe:
        logging.debug(f"[SELF-EDIT] cooldown persist failed: {_pe}")


_last_any_autonomous_edit: float = _load_last_autonomous_edit()

def _build_targeted_prompt(task_type: str, creativity: float) -> str:
    """
    Build a self-edit prompt that focuses on the weak task type.
    creativity 0.0–0.33: repair a known failure  (conservative)
    creativity 0.34–0.66: refactor a module function
    creativity 0.67–1.0: propose a new helper function
    """
    base = (
        f"Autonomous self-edit targeting '{task_type}' task performance. "
        "Modify app/core/self_edit_generated.py only. "
        "Output must be headless Python with no interactive elements."
    )
    if creativity <= 0.33:
        return (
            base + " Focus: fix the most common sandbox failure "
            "(prose detected in code output). Add a tighter prose-detection "
            "guard that strips any leading natural-language sentence before "
            "the first valid Python token."
        )
    elif creativity <= 0.66:
        return (
            base + " Focus: refactor the main code-generation function to "
            "reduce its average response length by 20%% without losing "
            "correctness — shorter code compiles faster and has fewer syntax errors."
        )
    else:
        return (
            base + " Focus: add a new helper function that scores a candidate "
            "code string on three dimensions: has_imports, has_function_def, "
            "no_prose_sentences. Return a 0–3 int quality score. "
            "This will be used to pre-filter LLM output before sandbox testing."
        )


def perform_self_edit(prompt=None, intensity=None, creativity=None, dry_run=None, target_task_type=None):
    import time
    from app.core.stillness_state import is_in_stillness
    if is_in_stillness():
        logging.info("[SELF-EDIT] Echo is in stillness — self-edit deferred.")
        return False, "Deferred: Echo is in stillness"
    creativity = creativity if creativity is not None else 0.5

    if prompt is None:
        if target_task_type is None:
            # First: check shadow model corrections — these are highest-trust signals
            try:
                import json as _json
                from pathlib import Path as _Path
                _shadow_path = _Path("memory/shadow_self_model.json")
                if _shadow_path.exists():
                    _shadow = _json.loads(_shadow_path.read_text())
                    _focus = _shadow.get("targets", {}).get("next_self_edit_focus")
                    if _focus:
                        logging.info(f"[SELF-EDIT] Shadow model correction → target={_focus}")
                        target_task_type = _focus
            except Exception as _se:
                logging.debug(f"[SELF-EDIT] Shadow focus read failed: {_se}")

            # Fallback: ask SelfModelUpdater for the weakest task type
            if target_task_type is None:
                try:
                    from app.core.self_model_updater import SelfModelUpdater
                    target_task_type = SelfModelUpdater().get_weak_task_type()
                except Exception as e:
                    logging.warning(f"[SELF-EDIT] SelfModelUpdater unavailable: {e}")
                    target_task_type = "coding"

        prompt = _build_targeted_prompt(target_task_type, creativity)

        # Global cooldown — any autonomous self-edit blocks all others for 60 min.
        # Keyed per-prompt cooldowns were bypassed by varying creativity values.
        global _last_any_autonomous_edit
        now = time.time()
        if now - _last_any_autonomous_edit < _TARGETED_PROMPT_COOLDOWN:
            remaining = int(_TARGETED_PROMPT_COOLDOWN - (now - _last_any_autonomous_edit))
            logging.info(f"[SELF-EDIT] Global cooldown active — skipping for {remaining}s")
            return False, f"Cooldown active ({remaining}s remaining)"
        _last_any_autonomous_edit = now  # stamp immediately so concurrent calls are also blocked
        _persist_last_autonomous_edit(now)

    return execute_self_edit(prompt, intensity=intensity)

def apply_self_edits(*args, **kwargs):
    logging.info(f"apply_self_edits called with args={args}, kwargs={kwargs}")
    return None

def schedule_self_edit(*args, **kwargs):
    logging.info(f"schedule_self_edit called with args={args}, kwargs={kwargs}")
    return None
def request_self_edit(prompt: str):
    """Entry point for friction-driven self-edit requests."""
    logging.info(f"[WOLF] request_self_edit called with friction prompt: {prompt[:80]}")
    return execute_self_edit(prompt)
