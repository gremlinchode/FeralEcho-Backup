# app/core/self_edit_manager.py – LOGIC-GUIDED PATCHED WITH SANDBOX + REFLECTION TRACKING
# v2.2 — Wired sandbox outcomes into river brain via learn_from_sandbox_outcome()
#         Model name now tracked through generation pipeline for accurate feedback.
import ast
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
import logging
import threading
import uuid
from datetime import datetime
from app.ollama_handler import generate_code, query_ollama
from app.core.echo_model_orchestrator import echo_query
from app.core.memory_tools import log_memory_edit
from app.core.memory_bridge import append_to_journal, retrieve_relevant_memories, log_dream_bridge, log_interaction
from app.core.self_edit_attempt_ledger import record_attempt as _record_attempt_ledger
from app.core.self_edit_attempt_ledger import read_recent_f2_error as _read_recent_f2_error
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
# Dissent log (2026-07-17) — see propose_core_edit()'s own council review.
# Anchored to _PROJECT_ROOT for the same reason as the paths above.
_DISSENT_LOG_PATH = os.path.join(_PROJECT_ROOT, "memory", "dissent_log.jsonl")
# CLAUDE.md Finding 41 B5: this append had no lock, unlike every other jsonl
# writer in this codebase touched by Batch 3's race-condition sweep (mirrors
# river_deliberation.py's _council_log_lock pattern). Currently latent — the
# only call path is the human-driven !propose command — but cheap to close.
_dissent_log_lock = threading.Lock()

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
    "app/subsystems/reflection_shard.py",
    "app/core/touch_sense.py",
    "app/core/vision_sense.py",
    "app/core/hearing_sense.py",
    "app/core/self_model_claims.py",
    "app/core/self_knowledge_verification.py",
    "run.py",
    "Modelfile",
    "echo_principles.json",
})
# app/core/self_model_claims.py and app/core/self_knowledge_verification.py
# added 2026-09-08 (living-self-model implementation) -- same reasoning as
# self_model_updater.py/reflection_shard.py's own entries above: both are
# the mechanism meant to keep Echo's self-knowledge honest (a stateless
# real-time verifier and its durable claims ledger); a self-edit that
# quietly weakened either one (e.g. flipping a verified bool's polarity,
# or disabling the proposed_by != verified_by guard) would corrupt the
# thing this whole 2026-09-08 investigation exists to make trustworthy,
# with nothing else positioned to catch it.

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

# Gap-closure plan (2026-07-23): self-edit escalation calls, added
# alongside app/core/echo_projects.py's new full-library-access pipeline.
# Blocked by resolved CALL TARGET, not module name -- a module-name
# denylist (e.g. "never import self_edit_manager/echo_optuna") would be
# defeated by "app" already being a blanket-allowed top-level entry in
# _ALLOWED_TOP_LEVEL: `import app.core.wolf_friction_bridge;
# wolf_friction_bridge.request_self_edit(...)` would sail past a
# name-based check without ever naming the specific module a denylist
# looks for. Checking the attribute/call name alone -- independent of
# which module or alias resolves to it -- blocks the actual action worth
# preventing (programmatically triggering a real self-edit cycle from
# inside a generate-and-test space) rather than trying to enumerate every
# module path that could reach it.
_BLOCKED_SELF_EDIT_ESCALATION_CALLS = frozenset({
    "perform_self_edit", "execute_self_edit", "request_self_edit", "save_code",
})

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

    Uses _resolve_path_literal (strict), not _ast_strings (loose) — this map
    feeds directly into _path_is_safe()'s safety check, so an assignment like
    `path = some_unresolvable_var + "/looks_safe.txt"` must NOT populate
    assigns['path'] with "/looks_safe.txt": that fragment being visible
    anywhere inside the expression doesn't mean the real runtime value is
    known. Passing {} for nested Name resolution means chained assignments
    (`a = "x"; b = a + "y"`) don't resolve either — conservative, not a
    regression, since this scanner never attempted multi-pass fixed-point
    resolution in the first place.
    """
    assigns: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    strs = _resolve_path_literal(node.value, {})
                    if strs:
                        assigns[target.id] = strs
    return assigns


def _resolve_path_literal(node: ast.AST, var_strings: dict) -> list:
    """
    Strict counterpart to _ast_strings(), used only for path-safety checks.

    _ast_strings() walks the *entire* subtree and harvests every string
    constant it finds anywhere inside an expression — useful for
    _collect_var_strings()'s broader "what literals appear on this RHS"
    purpose, but wrong for a safety gate: an expression like
    `some_unresolvable_var + "/looks_safe.txt"` previously passed this
    check, because ast.walk() found the literal fragment even though the
    real runtime path (prefixed by an unknown variable) is completely
    unknown. This only returns strings when the *whole* expression
    resolves to a known value: a plain literal, a pure constant-
    concatenation chain, or a Name resolvable via var_strings. Anything
    else (an f-string, a call, a BinOp mixing a variable with a literal,
    etc.) is treated as fully opaque.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        assembled = _eval_str_concat(node)
        return [assembled] if assembled is not None else []
    if isinstance(node, ast.Name):
        return var_strings.get(node.id, [])
    return []


def _path_is_safe(path_arg: ast.AST, var_strings: dict) -> tuple:
    """
    Returns (is_safe: bool, reason: str).

    Unsafe conditions:
      - path argument is completely opaque (no string literals resolvable)
      - any visible string component matches a forbidden target name
      - any visible string component contains ".." (traversal)
    """
    strings = _resolve_path_literal(path_arg, var_strings)

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

    if not args:
        return None  # no positional path argument (e.g. all-keyword call) —
        # same pre-existing gap as before this fix, not addressed here.

    # Determine mode
    if len(args) >= 2:
        mode_node = args[1]
    elif "mode" in kwargs:
        mode_node = kwargs["mode"]
    else:
        mode_node = None  # no second arg → default "r"

    if mode_node is None:
        mode = "r"
    elif isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
        mode = mode_node.value
    else:
        mode = "?"  # non-literal mode → treat as unknown/write

    # Audit finding (Low severity): a default-mode read (no second arg) or a
    # confirmed read-only literal mode previously returned "safe" here
    # immediately, without ever checking the path argument at all — a fully
    # dynamic/unresolvable path on a READ call passed completely unchecked,
    # inconsistent with F1's "unknown = forbidden" philosophy applied
    # everywhere else in this scanner (write-mode-uncertainty was always
    # blocked; path-uncertainty-on-read never was). F2's kernel sandbox is
    # still the real backstop for both reads and writes regardless — this
    # makes F1 itself uniformly conservative rather than asymmetrically so.
    is_safe, reason = _path_is_safe(args[0], var_strings)
    if not is_safe:
        return f"line {lineno}: open(mode={mode!r}) blocked — {reason}"
    return None


def _resolve_import_aliases(tree: ast.Module) -> tuple:
    """
    CLAUDE.md Finding 41-C, fixed 2026-07-22. scan_for_unsafe_operations()
    below matches dangerous calls by literal spelling only (obj.id ==
    "subprocess", bare name in {"exec","eval"}) — confirmed live to miss an
    entire bypass class: `from os import system; system(...)`, `import os
    as o; o.system(...)`, and `from subprocess import call; call(...)` all
    sailed past this scanner untouched, since none of them ever spell the
    literal string "os"/"subprocess" at the call site. Not an active
    exploit today (F2's kernel sandbox still blocks the actual execution
    regardless — see Finding 41-C's own text), but F1's documented job is
    to catch these before F2 ever runs, and it silently wasn't for this
    whole class.

    Returns (module_aliases, from_aliases):
      module_aliases: {local_name: real_module} for `import X [as Y]` —
        e.g. `import os as o` -> {"o": "os"}; a plain `import os` (no
        alias) still maps {"os": "os"}, so callers can tell a genuine
        alias apart from the direct spelling by checking local != real.
      from_aliases: {local_name: "module.attr"} for `from X import Y [as Z]`
        — e.g. `from os import system` -> {"system": "os.system"};
        `from subprocess import call as c` -> {"c": "subprocess.call"}.
    """
    module_aliases: dict = {}
    from_aliases: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                real_module = alias.name.split(".")[0]
                local = alias.asname or real_module
                module_aliases[local] = real_module
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                local = alias.asname or alias.name
                from_aliases[local] = f"{module}.{alias.name}"
    return module_aliases, from_aliases


def _is_blocked_module_attr(module: str, attr: str) -> "str | None":
    """
    Central lookup shared by both the direct-spelling checks already in
    scan_for_unsafe_operations() and the alias-resolution paths added for
    Finding 41-C, so the actual blocked-operation list is only maintained
    in one place (the existing _BLOCKED_* sets above). Returns a
    human-readable description if module.attr is one of the operations
    this scanner unconditionally blocks, else None.
    """
    if module in _BLOCKED_POSIX_MODULE and attr in _BLOCKED_OS_ATTRS:
        return f"{module}.{attr}() is unconditionally blocked"
    if module == "subprocess" and attr in _BLOCKED_SUB_ATTRS:
        return f"subprocess.{attr}() is unconditionally blocked"
    if module == "shutil" and attr in _BLOCKED_SHUTIL_ATTRS:
        return f"shutil.{attr}() is unconditionally blocked"
    if module in ("io", "_io") and attr in _BLOCKED_IO_CLASSES:
        return f"{module}.{attr}() is unconditionally blocked"
    if module == "importlib" and attr in _BLOCKED_IMPORTLIB_ATTRS:
        return f"importlib.{attr}() is unconditionally blocked"
    if module in ("ctypes", "cffi") and (attr in _BLOCKED_CTYPES_ATTRS or attr == "FFI"):
        return f"{module}.{attr} is unconditionally blocked"
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
    module_aliases, from_aliases = _resolve_import_aliases(tree)
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
            # Self-edit escalation call, direct or unaliased from-import:
            # `perform_self_edit(...)` after either `import ...
            # perform_self_edit` in whatever form makes it a bare name.
            if name in _BLOCKED_SELF_EDIT_ESCALATION_CALLS:
                violations.append(
                    f"line {lineno}: {name}() is a self-edit escalation call, unconditionally blocked"
                )
                continue
            # Finding 41-C: `from os import system; system(...)` — a bare
            # call whose real origin (resolved via from_aliases) is a
            # blocked module.attr, even though the call site never spells
            # "os"/"subprocess" literally. Also covers an ALIASED escalation
            # import: `from app.core.self_edit_manager import
            # perform_self_edit as pse; pse(...)` — origin_attr resolves to
            # "perform_self_edit" even though the call site only says "pse".
            if name in from_aliases:
                origin_module, _, origin_attr = from_aliases[name].rpartition(".")
                if origin_attr in _BLOCKED_SELF_EDIT_ESCALATION_CALLS:
                    violations.append(
                        f"line {lineno}: {origin_attr}() is a self-edit escalation call, "
                        f"unconditionally blocked (aliased via 'from {origin_module} import "
                        f"{origin_attr}' as '{name}')"
                    )
                    continue
                v = _is_blocked_module_attr(origin_module, origin_attr)
                if v:
                    violations.append(
                        f"line {lineno}: {v} (aliased via 'from {origin_module} import "
                        f"{origin_attr}' as '{name}')"
                    )
            continue

        # --- attribute calls: obj.method() --------------------------------
        if not isinstance(func, ast.Attribute):
            continue

        attr = func.attr
        obj  = func.value

        # Finding 41-C: `import os as o; o.system(...)` — obj.id is the
        # alias, not the real module; resolve it before the direct-spelling
        # checks below (which only fire on the literal, unaliased name —
        # module_aliases maps a plain `import os` to itself, so this branch
        # is a no-op for the already-covered direct-spelling case).
        if isinstance(obj, ast.Name):
            aliased_module = module_aliases.get(obj.id)
            if aliased_module and aliased_module != obj.id:
                v = _is_blocked_module_attr(aliased_module, attr)
                if v:
                    violations.append(
                        f"line {lineno}: {v} (aliased via 'import {aliased_module} as {obj.id}')"
                    )
                    continue

        # Finding 41-C: `__import__("os").system(...)` — obj is itself a
        # call to __import__ with a string-literal module name, not a Name.
        if (
            isinstance(obj, ast.Call)
            and isinstance(obj.func, ast.Name)
            and obj.func.id == "__import__"
            and obj.args
            and isinstance(obj.args[0], ast.Constant)
            and isinstance(obj.args[0].value, str)
        ):
            v = _is_blocked_module_attr(obj.args[0].value, attr)
            if v:
                violations.append(f"line {lineno}: {v} (via __import__({obj.args[0].value!r}))")
                continue

        # Self-edit escalation call, attribute form: `self_edit_manager.
        # perform_self_edit(...)`, any aliased module name (`sem.
        # perform_self_edit(...)` after `import ... as sem`), or reached
        # via __import__(...).perform_self_edit(...) above -- checking attr
        # alone, independent of what obj resolves to, naturally covers all
        # three call shapes without needing separate module resolution.
        if attr in _BLOCKED_SELF_EDIT_ESCALATION_CALLS:
            violations.append(
                f"line {lineno}: {attr}() is a self-edit escalation call, unconditionally blocked"
            )
            continue

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
    # DO NOT reuse this prompt block (or generate_code_from_plan(), which
    # is the only real caller) for general-purpose/conversational coding
    # tasks. Confirmed empirically, not just suspected: the Tier-4
    # confirmatory experiment (n=84, hash-frozen protocol, audits/
    # tier4_confirmatory_report.md) isolated this exact framing —
    # CODE_OUTPUT_RULES plus the live self_edit_generated.py file content
    # prepended to an otherwise-ordinary coding prompt — and found it
    # significantly HURTS performance relative to bare prompting
    # (p=0.0002, -23.81 percentage points, pooled). The likely mechanism,
    # per rule 8/9 below: this block tells the model "you ARE
    # self_edit_generated.py" and "only import from the FeralEcho module
    # inventory... if a name is not in the inventory it does not exist" —
    # both correct and necessary for this function's real job (replacing
    # that one file), both actively confusing/constraining for a model
    # asked to solve an unrelated problem (e.g. it may avoid a needed
    # stdlib import it doesn't see explicitly enumerated). Checked
    # directly, not assumed: as of this comment, generate_code_from_plan()
    # has exactly two real callers, self_edit_manager.py's own pipeline
    # and wolf_friction_bridge.py's dry-run simulator — both legitimate,
    # intended uses where this framing is correct. This comment exists so
    # a future feature needing "generate some code" does not reach for
    # this function by convenience and inherit a demonstrated regression.
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
    "10. If this task is about transforming or post-processing generated code text "
    "(e.g. stripping prose, shortening output), expose your main function as a "
    "top-level function named exactly `apply_to_code(code: str) -> str` that takes "
    "the code string and returns the modified code string, NOT wrapped in a class. "
    "This is the only function name the pipeline automatically invokes — other "
    "helper names are never called automatically.\n"
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


# Modules the generated code must never import, in either `import X` or
# `from X import Y` form: self_edit_generated (circular — the existing
# check, previously ImportFrom-only, so a bare `import
# app.core.self_edit_generated` slipped through uncaught) plus the modules
# that generate/deploy/tune it. "app" is a blanket entry in
# _ALLOWED_TOP_LEVEL below (broad on purpose — generated code legitimately
# needs various app.* modules), which means nothing previously stopped
# generated code from importing self_edit_manager or echo_optuna
# themselves. Confirmed real: found via a live symptom — self_edit_manager's
# module-level backfill_convergence_from_log() call was firing dozens of
# times per burst, traced to sandbox subprocesses re-executing
# self_edit_manager.py's top-level code whenever staged candidate code
# imported it (a real, non-hallucinated module name, so it passed the only
# check that existed before this one).
_SELF_REFERENTIAL_MODULES = ("self_edit_generated", "self_edit_manager", "echo_optuna")


def _validate_imports(code: str) -> tuple[bool, str]:
    """
    Parse import statements in generated code and reject:
    1. Any module not in _ALLOWED_TOP_LEVEL (hallucinated imports).
    2. Any import of a module in _SELF_REFERENTIAL_MODULES, in either import
       form — self_edit_generated.py must never import from itself (circular
       at production time — the staging test misses this because it loads
       the code as '_staged_edit', so the circular reference resolves to the
       production file during staging but blows up in production), and must
       never import the pipeline that generates/deploys/tunes it either.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return True, ""  # syntax errors caught separately

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(m in alias.name for m in _SELF_REFERENTIAL_MODULES):
                    return False, f"self-referential import: 'import {alias.name}'"
                top = alias.name.split(".")[0]
                if top not in _ALLOWED_TOP_LEVEL:
                    return False, f"hallucinated import: '{alias.name}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if any(m in node.module for m in _SELF_REFERENTIAL_MODULES):
                    return False, f"self-referential import: 'from {node.module}'"
                top = node.module.split(".")[0]
                if top not in _ALLOWED_TOP_LEVEL:
                    return False, f"hallucinated import: 'from {node.module}'"
    return True, ""

def _stage_and_import_test(code: str, staging_file: str = STAGING_FILE) -> tuple[bool, str]:
    """Write code to staging/ and run a subprocess import test before touching production.

    This is the gate between validate_code (AST-only) and save_code (production write).
    A module can pass AST parsing but fail on import due to bad top-level statements,
    circular imports, or missing runtime dependencies. If this test fails, production
    is untouched and the staging file is preserved for inspection.

    staging_file: defaults to the shared STAGING_FILE constant for backward
    compatibility (wolf_friction_bridge.py's dry-run-only simulate_self_edit()
    still uses the default), but execute_self_edit() passes a per-call unique
    path — without that, two concurrent real trials (the hourly AutonomousSelfEdit
    loop and model_guided_autonomous_loop both call into this pipeline on
    separate timers) could overwrite each other's staged file between one
    trial's write and its subprocess actually reading it, so trial A's
    pass/fail result could silently be computed against trial B's code.
    """
    import tempfile
    try:
        os.makedirs(STAGING_DIR, exist_ok=True)
        with open(staging_file, "w") as f:
            f.write(code)
        with tempfile.TemporaryDirectory(prefix="echo_stage_") as scratch:
            scratch_real = os.path.realpath(scratch)
            result = subprocess.run(
                ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={scratch_real}",
                 sys.executable, _SANDBOX_WRAPPER, scratch_real, staging_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd(),
            )
        if result.returncode == 0 and "SANDBOX_OK" in result.stdout:
            return True, ""
        # Same blind-front-truncation bug as test_code_in_sandbox() (see
        # _extract_sandbox_failure_text()'s docstring) — this is a separate
        # call site with the identical shape, missed in the original fix.
        # Found via independent cross-check on the Ark fork (claude_relay/
        # from_air.md, 2026-07-14): same bug, confirmed there too, under
        # _stage_and_import_test()'s equivalent. This is the function that
        # actually produces the "staging_import_failed" journal result —
        # the more common of the two truncation sites in practice.
        return False, _extract_sandbox_failure_text((result.stderr or result.stdout).strip())
    except subprocess.TimeoutExpired:
        return False, "Staging import test timed out (30s)"
    except Exception as e:
        return False, str(e)

# Same bounded-retention idea for the per-call-unique staging files above —
# each real execute_self_edit() call (up to 10/hour via Optuna trials) now
# creates its own self_edit_candidate_<uuid>.py rather than overwriting one
# shared file, which would otherwise recreate the exact unbounded-growth
# problem _MAX_SELF_EDIT_BACKUPS below already exists to prevent.
_MAX_STAGING_FILES = 25


def _prune_stale_staging_files():
    if not os.path.isdir(STAGING_DIR):
        return
    candidates = sorted(
        (f for f in os.listdir(STAGING_DIR) if f.startswith("self_edit_candidate_") and f.endswith(".py")),
        key=lambda f: os.path.getmtime(os.path.join(STAGING_DIR, f)),
        reverse=True,
    )
    for stale in candidates[_MAX_STAGING_FILES:]:
        try:
            os.remove(os.path.join(STAGING_DIR, stale))
        except Exception as e:
            logging.warning(f"[SELF-EDIT] Failed to prune stale staging file {stale}: {e}")


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


# Retain at most this many plans — same bounded-retention idea as
# _MAX_SELF_EDIT_BACKUPS above. Before this, self_edit_plans/ grew unboundedly
# (10,333 files, 42MB, accumulating since 2025-09 — found by the 2026-07-21
# forensic cleanup audit; no equivalent pruning existed for this directory,
# unlike its sibling self_edit_backups/).
_MAX_SELF_EDIT_PLANS = 500


def _prune_self_edit_plans(plan_dir: str = None, max_plans: int = None):
    # Optional params default to the real module constants — every existing
    # call site (save_plan(), below) is unaffected. They exist so
    # liveness_ledger.py's plan_retention check can exercise this exact
    # function against a synthetic directory instead of reimplementing its
    # logic separately, which would defeat the point of a functional canary.
    plan_dir = plan_dir if plan_dir is not None else LOGIC_PLAN_DIR
    max_plans = max_plans if max_plans is not None else _MAX_SELF_EDIT_PLANS
    if not os.path.isdir(plan_dir):
        return
    plans = sorted(
        (f for f in os.listdir(plan_dir) if f.endswith(".txt")),
        reverse=True,
    )
    for stale in plans[max_plans:]:
        try:
            os.remove(os.path.join(plan_dir, stale))
        except Exception as e:
            logging.warning(f"[SELF-EDIT] Failed to prune old plan {stale}: {e}")


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
    "response_shortening": ("shorten", "length", "concise", "trim", "truncat"),
    "quality_scoring":     ("quality", "score", "eval"),
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

    The count-based convergence check below is identity-blind: it only compares how
    many callables match a family's keywords cycle-to-cycle, so 34 different names all
    targeting the same "strip prose from code" problem (confirmed directly in
    memory/SELF_EDIT.log across 119 cycles) reads as "convergent" as long as the count
    stays flat — it can't tell a genuinely new attempt from a renamed old one. This also
    tracks the actual *set* of names ever seen per family (all_names_seen, capped at 50
    to keep the state file bounded) and how many cycles have touched this family
    (cycles_attempted), so a real history is available to feed back into planning
    instead of being silently discarded after this cycle (see _build_convergence_note()).
    """
    state = _load_convergence_state()
    lower_names = [c.lower() for c in callables]
    matched_this_cycle: set = set()

    for family, keywords in _CONVERGENCE_FAMILIES.items():
        matching_names = [name for name in lower_names if any(kw in name for kw in keywords)]
        matched_this_cycle.update(matching_names)
        count = len(matching_names)
        prev = state.get(family, {"count": 0, "non_convergent_streak": 0,
                                    "all_names_seen": [], "cycles_attempted": 0})
        if count == 0:
            continue  # this family isn't present this cycle — nothing to evaluate
        convergent = count <= prev.get("count", 0) or prev.get("count", 0) == 0
        streak = 0 if convergent else prev.get("non_convergent_streak", 0) + 1

        names_seen = list(dict.fromkeys(prev.get("all_names_seen", []) + matching_names))[-50:]
        cycles_attempted = prev.get("cycles_attempted", 0) + 1

        state[family] = {
            "count": count,
            "non_convergent_streak": streak,
            "all_names_seen": names_seen,
            "cycles_attempted": cycles_attempted,
        }

        verdict = "convergent" if convergent else f"NON-CONVERGENT (streak={streak})"
        msg = (
            f"[CONVERGENCE] family={family} matching_callables={count} "
            f"(prev={prev.get('count', 0)}) -> {verdict}"
        )
        append_to_journal("SELF_EDIT", msg)
        logging.info("[SELF-EDIT]%s", msg)

        # Global Workspace publish (Emergence roadmap Phase 2a), gated on
        # the same non_convergent_streak >= 2 threshold _build_targeted_
        # prompt() already treats as meaningful — not a new number invented
        # for this. A self-edit family stuck for multiple cycles is exactly
        # the kind of salient signal that should be visible outside this
        # module, not just sitting in self_edit_convergence.json.
        if streak >= 2:
            try:
                from app.core.echo_core import get_echo_core
                core = get_echo_core()
                if core:
                    core.publish_salience(
                        source="self_edit_convergence",
                        kind="self_edit.non_convergent",
                        summary=f"family={family} stuck for {streak} cycles",
                        detail={"family": family, "streak": streak, "count": count},
                        salience=min(streak / 10.0, 1.0),
                    )
            except Exception:
                pass

    # A callable whose name matches none of the fixed keyword families was
    # previously completely invisible to convergence tracking — not even
    # counted as non-convergent, just silently dropped. A single shared
    # "unclassified" bucket at least gives a repeating pattern outside the
    # 3 named families some signal, rather than zero signal anywhere.
    unclassified = [name for name in lower_names if name not in matched_this_cycle]
    if unclassified:
        family = "unclassified"
        prev = state.get(family, {"count": 0, "non_convergent_streak": 0,
                                    "all_names_seen": [], "cycles_attempted": 0})
        count = len(unclassified)
        convergent = count <= prev.get("count", 0) or prev.get("count", 0) == 0
        streak = 0 if convergent else prev.get("non_convergent_streak", 0) + 1
        names_seen = list(dict.fromkeys(prev.get("all_names_seen", []) + unclassified))[-50:]
        cycles_attempted = prev.get("cycles_attempted", 0) + 1
        state[family] = {
            "count": count,
            "non_convergent_streak": streak,
            "all_names_seen": names_seen,
            "cycles_attempted": cycles_attempted,
        }
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


def _build_convergence_note(focus_text: str) -> str:
    """
    If the current cycle's Focus text maps to a family with real prior history,
    return a short note telling the model exactly what's already been tried —
    so it can extend/fix an existing helper or explicitly justify a new approach,
    instead of silently reinventing the same thing under a new name (the pattern
    that produced 34 distinct prose-stripping callables with zero convergence).
    Returns "" for a family with no tracked history — no-op, no prompt change.
    """
    lower_focus = focus_text.lower()
    state = _load_convergence_state()

    for family, keywords in _CONVERGENCE_FAMILIES.items():
        if not any(kw in lower_focus for kw in keywords):
            continue
        entry = state.get(family)
        if not entry or entry.get("cycles_attempted", 0) < 2:
            return ""  # fresh family, or only tried once — nothing to warn about yet
        names = entry.get("all_names_seen", [])
        cycles = entry.get("cycles_attempted", 0)
        return (
            f"\n\nCONVERGENCE NOTE: this exact problem has been attempted {cycles} times "
            f"before, under these function names: {', '.join(names)}. Do not simply "
            f"reimplement an equivalent function under a new name — either meaningfully "
            f"extend or fix whichever of these already exists in the current file "
            f"contents below, or clearly explain in your plan why a genuinely different "
            f"approach is needed this time."
        )
    return ""


_SELF_EDIT_LOG_FILE = os.path.join(_PROJECT_ROOT, "memory", "SELF_EDIT.log")
_LOAD_AUDIT_RE = re.compile(
    r"\[LOAD_AUDIT\] self_edit_generated defines \d+ callables: (\[.*\])\s*$"
)


def backfill_convergence_from_log(log_path: str | None = None) -> None:
    """
    Reconciles all_names_seen/cycles_attempted against the real historical
    record in memory/SELF_EDIT.log, instead of only counting cycles that ran
    since convergence tracking was added (confirmed at ~119+ real cycles for
    prose_stripping alone vs. cycles_attempted=1 in the state file before this
    backfill exists). Deterministic full replay every call — never increments
    — so it is safe and idempotent to run on every process start, including
    Flask's debug-mode double-spawn. Only all_names_seen/cycles_attempted are
    replaced; count/non_convergent_streak are left untouched since
    _record_convergence() already maintains those correctly from live data.
    """
    log_path = log_path or _SELF_EDIT_LOG_FILE
    if not os.path.exists(log_path):
        return

    replayed: dict = {}
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = _LOAD_AUDIT_RE.search(line)
                if not match:
                    continue
                try:
                    callables = ast.literal_eval(match.group(1))
                except (ValueError, SyntaxError):
                    continue
                if not isinstance(callables, list):
                    continue
                lower_names = [str(c).lower() for c in callables]
                for family, keywords in _CONVERGENCE_FAMILIES.items():
                    matching = [n for n in lower_names if any(kw in n for kw in keywords)]
                    if not matching:
                        continue
                    entry = replayed.setdefault(family, {"all_names_seen": [], "cycles_attempted": 0})
                    entry["all_names_seen"] = list(dict.fromkeys(entry["all_names_seen"] + matching))[-50:]
                    entry["cycles_attempted"] += 1
    except Exception as e:
        logging.warning(f"[SELF-EDIT] Convergence backfill failed to read log: {e}")
        return

    if not replayed:
        return

    state = _load_convergence_state()
    for family, backfilled in replayed.items():
        current = state.get(family, {
            "count": 0, "non_convergent_streak": 0,
            "all_names_seen": [], "cycles_attempted": 0,
        })
        current["all_names_seen"] = backfilled["all_names_seen"]
        current["cycles_attempted"] = backfilled["cycles_attempted"]
        state[family] = current

    try:
        os.makedirs(os.path.dirname(_CONVERGENCE_STATE_FILE), exist_ok=True)
        tmp_path = _CONVERGENCE_STATE_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(state, indent=2))
        os.replace(tmp_path, _CONVERGENCE_STATE_FILE)
        for family, backfilled in replayed.items():
            append_to_journal(
                "SELF_EDIT",
                f"[CONVERGENCE_BACKFILL] family={family} "
                f"cycles_attempted={backfilled['cycles_attempted']} "
                f"names={backfilled['all_names_seen']}"
            )
    except Exception as e:
        logging.warning(f"[SELF-EDIT] Failed to persist convergence backfill: {e}")


try:
    backfill_convergence_from_log()
except Exception as _bfe:
    logging.warning(f"[SELF-EDIT] Convergence backfill failed: {_bfe}")


def save_plan(plan: str):
    os.makedirs(LOGIC_PLAN_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    plan_file = os.path.join(LOGIC_PLAN_DIR, f"plan_{timestamp}.txt")
    with open(plan_file, "w") as f:
        f.write(plan)
    logging.info(f"Saved logic plan to {plan_file}")
    _prune_self_edit_plans()

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

_MAX_SANDBOX_ERROR_LEN = 3000  # was 1500 — a real live traceback captured during this
# fix's own verification (candidate -> memory_bridge -> memory_write_validator ->
# logging.FileHandler -> blocked by sandbox) measured 1529 chars from the marker to
# the actual final exception line, meaning the original cap would have cut off
# right at (or just before) the single most useful line — the real exception
# type/message. Doubled with real headroom based on that measurement, not a guess.
_FALLBACK_SANDBOX_ERROR_LEN = 400  # unchanged from the old blind-truncation length

_TRACEBACK_MARKER = "Traceback (most recent call last):"


def _extract_sandbox_failure_text(raw: str) -> str:
    """
    Root-cause fix (2026-07-14 forensic investigation, see
    .claude/plans/groovy-cuddling-brooks.md): the previous version of this
    logic was `(result.stderr or result.stdout).strip()[:400]` — a blind
    slice of the FIRST 400 characters of combined output. Any candidate
    that imports something pulling in numpy/faiss/sentence-transformers
    (most commonly via `import app.core.memory_bridge`, confirmed common
    in real generated candidates) triggers a non-fatal but real
    "OMP: Warning #179: Function Can't set size of /tmp file failed" during
    library init — OpenMP's duplicate-library-registration mechanism
    getting its own /tmp lock-file write blocked by the sandbox's
    SCRATCH-only write policy. That warning prints FIRST, before the
    candidate's own code ever runs, so it reliably occupied the front of
    the old 400-char window — meaning the retry-feedback prompt was often
    handed OMP noise instead of the real exception, making the retry
    "fail identically" not because the underlying problem was unfixable,
    but because the model was never told what was actually wrong.

    Fix: search the *untruncated* text for a real traceback marker first.
    If found, return from that marker to the end (capped generously —
    this is real signal, not noise, and it's worth keeping most of it for
    the retry-feedback prompt to actually act on). If no traceback marker
    exists (e.g. a non-Python failure, a permission error with no
    traceback), fall back to the *last* N characters rather than the
    first — the terminal/final output is far more likely to contain the
    actual failure than whatever printed during early library init.
    """
    if not raw:
        return raw
    idx = raw.find(_TRACEBACK_MARKER)
    if idx != -1:
        return raw[idx:idx + _MAX_SANDBOX_ERROR_LEN].strip()
    return raw[-_FALLBACK_SANDBOX_ERROR_LEN:].strip()


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

    # Write to sandbox/scripts/ for inspection/archive — anchored via
    # _PROJECT_ROOT like every other path constant in this file (see
    # CLAUDE.md Finding 7); this was the one location that wasn't, still
    # relative/cwd-dependent.
    sandbox_path = os.path.join(_PROJECT_ROOT, "sandbox", "scripts", script_name)
    os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
    archive_dir = os.path.join(_PROJECT_ROOT, "sandbox", "scripts", "archive")
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
        raw = (result.stderr or result.stdout).strip()
        err = _extract_sandbox_failure_text(raw)
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


def _build_live_self_edit_inventory() -> str:
    """
    Cheap, always-current companion to _build_module_inventory()'s cache,
    which is built from .echo_project_learner/feralecho_structure.json — a
    project-wide scan regenerated on its own schedule (observed 7 days stale
    against the current cycle) and therefore blind to same-day edits. This
    parses only self_edit_generated.py itself — the one file whose current
    contents actually matter for "what have I already built" — fresh on
    every planning call, reusing project_learner's existing single-file AST
    parser rather than a second walker or a full repo re-scan.
    """
    try:
        from app.core.project_learner import parse_file
        _imports, symbols, _top_comments = parse_file(SELF_EDIT_FILE)
    except Exception:
        return ""
    if not symbols:
        return "CURRENT self_edit_generated.py: no functions currently defined."
    lines = ["CURRENT self_edit_generated.py contents (ground truth — do not re-implement any of these):"]
    for s in symbols:
        doc = f" — {s.docstring.strip().splitlines()[0]}" if s.docstring else ""
        lines.append(f"  {s.type} {s.name}{doc}")
    return "\n".join(lines)


def _recent_experiment_note() -> str:
    """
    Most recent sandbox/experiment_runner.py result, surfaced as context.
    Audit finding: exploratory curiosity-experiment results were logged to
    interaction_log.jsonl/FAISS but never reached self-edit's own
    prompt-assembly at all — a second, entirely separate exploration
    mechanism that never converged back into the one mechanism actually
    capable of persisting a change. Recency-based (most recent entry),
    reusing echo_ground_truth's existing tail-read helper rather than a
    second implementation of the same pattern.
    """
    try:
        from app.core.echo_ground_truth import _read_jsonl_tail
        path = os.path.join(_PROJECT_ROOT, "memory", "interaction_log.jsonl")
        tail = _read_jsonl_tail(path, 200)
        for entry in reversed(tail):
            if entry.get("task_type") != "autonomous_experiment":
                continue
            topic = str(entry.get("prompt", ""))[:100]
            response = str(entry.get("response", ""))[:300]
            outcome = "succeeded" if entry.get("quality_score") else "failed"
            return f"Most recent curiosity experiment ({outcome}) — topic: {topic} — result: {response}"
    except Exception:
        pass
    return ""


def plan_code_logic(prompt: str, mastery_note: str = "", trace_id: "str | None" = None) -> str:
    """
    mastery_note: optional excerpt from advise_before_edit()'s real
    code-quality guidance (audit finding: previously computed and journaled
    every cycle but never reached this prompt at all). Capped to keep the
    planning call's token cost bounded — this is a nudge, not the full
    review dump.

    trace_id (2026-09-05, Plan 5 correlation-ID pass): optional, passed
    straight through to echo_query() so this call's interaction_log.jsonl/
    council_deliberations.jsonl entries can be joined to the rest of the
    same self-edit attempt. Defaults to None — identical to today's
    behavior for any caller that doesn't pass one.
    """
    try:
        inventory = _build_live_self_edit_inventory() + "\n\n" + _build_module_inventory()
        convergence_note = _build_convergence_note(prompt)
        mastery_block = (
            f"\n\nGuidance from recent code-quality review:\n{mastery_note[:1500]}"
            if mastery_note else ""
        )
        experiment_note = _recent_experiment_note()
        experiment_block = f"\n\n{experiment_note}" if experiment_note else ""
        plan_prompt = (
            f"{PLAN_OUTPUT_RULES}\n\n"
            f"{inventory}\n\n"
            f"You are planning a Python code modification for an autonomous AI system called Echo. "
            f"Break down the following task into clear, sequential Python steps. "
            f"Each step must be specific, technical, and implementable without user interaction. "
            f"Do not include steps involving input(), user prompts, or interactive elements."
            f"{convergence_note}"
            f"{mastery_block}"
            f"{experiment_block}\n\n"
            f"Task: {prompt}"
        )
        plan = echo_query(plan_prompt, task_type="coding", trace_id=trace_id)

        if not plan or not plan.strip() or plan.strip().lower().startswith("thinking"):
            logging.warning("[PROMPT GUARD] Plan output looks like reasoning prose. Using fallback plan.")
            return f"1. Write a headless Python function that implements: {prompt[:200]}\n2. Add logging output.\n3. Return a result string."

        return plan
    except Exception as e:
        logging.error(f"Failed to generate plan: {e}")
        append_to_journal("SELF_EDIT", f"Plan generation failed: {e}")
        return "1. Write stub to maintain continuity\nprint('Hello from self-edit stub')"

# -----------------------------------------------------------------------
# Real invocation point for self_edit_generated.py (Finding C1 / audit
# "self-edit writes to a file nothing calls"). Deliberately narrow: this is
# the ONLY place the deployed module is ever actually run, it only ever
# post-processes code this same pipeline just generated (never user-facing
# conversation), and any failure of any kind silently falls back to the
# input unchanged — this can only ever help or no-op, never regress
# generation. Separate from load_self_edit_module(), which is the
# production-deploy loader and has journal/convergence side effects that
# must fire once per real deploy cycle, not once per generation call.
# -----------------------------------------------------------------------
_self_edit_generated_cache: dict = {"mtime": None, "module": None}


def _load_self_edit_generated_for_use():
    """
    Load self_edit_generated.py purely for invocation, cached by mtime since
    this may be called on every self-edit generation cycle (not just real
    deploys). Re-runs the same F1/F3 AST safety scan before ever importing —
    this can never execute anything that wasn't already cleared to reach
    production.
    """
    if not os.path.exists(SELF_EDIT_FILE):
        return None
    try:
        mtime = os.path.getmtime(SELF_EDIT_FILE)
    except OSError:
        return None
    if _self_edit_generated_cache["mtime"] == mtime:
        return _self_edit_generated_cache["module"]
    try:
        with open(SELF_EDIT_FILE, "r", encoding="utf-8") as f:
            on_disk = f.read()
        scan_for_unsafe_operations(on_disk)
    except (ValueError, OSError):
        return None
    try:
        spec = importlib.util.spec_from_file_location("self_edit_generated_live", SELF_EDIT_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        logging.debug(f"[SELF-EDIT] self_edit_generated_live load failed: {e}")
        return None
    _self_edit_generated_cache["mtime"] = mtime
    _self_edit_generated_cache["module"] = module
    return module


_APPLY_TO_CODE_LOG = os.path.join(_PROJECT_ROOT, "memory", "apply_to_code_invocations.jsonl")


def _run_apply_to_code_sandboxed(code: str, timeout: float = 2.0) -> dict:
    """
    Runs the deployed self_edit_generated.py's apply_to_code(code) inside a
    real F2 kernel-sandboxed subprocess (sandbox-exec + echo_sandbox.sb +
    safe_exec_wrapper.py --mode=apply_to_code) — PENDING_DECISIONS.md #7 /
    CLAUDE.md Finding 41 B3, 2026-07-22.

    Replaces the prior in-process ThreadPoolExecutor + soft 2s timeout plus
    a temporary in-process open()/io.open()/Path.open() monkeypatch
    (Finding 31's original fix). That combination had a real, unclosed gap:
    Python threads cannot be forcibly killed, so a hook that ran past its
    soft timeout kept executing in the background — including any file
    writes — after the in-process write-guard had already been torn down
    on the calling thread's way out. Moving the real call into its own
    subprocess closes this at the root rather than hardening the same
    mechanism again: subprocess.run(timeout=...) genuinely terminates
    (SIGKILLs) the child process on TimeoutExpired, and the write-block is
    now the real kernel Seatbelt profile plus safe_exec_wrapper.py's
    patches — the same enforcement F2 already trusts for the pre-deploy
    staging test, not a second, weaker, temporary substitute for it.

    Returns {"success": bool, "result": str|None, "error": str|None,
    "blocked_write": bool}. Never raises — callers check "success"/
    "blocked_write" the same way test_code_in_sandbox()'s callers do.
    """
    import tempfile
    result = {"success": False, "result": None, "error": None, "blocked_write": False}
    try:
        with tempfile.TemporaryDirectory(prefix="echo_apply_to_code_") as scratch:
            scratch_real = os.path.realpath(scratch)
            input_path = os.path.join(scratch_real, "input_code.txt")
            output_path = os.path.join(scratch_real, "output_code.txt")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write(code)

            proc = subprocess.run(
                ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={scratch_real}",
                 sys.executable, _SANDBOX_WRAPPER, scratch_real, SELF_EDIT_FILE,
                 "--mode=apply_to_code", "--", input_path, output_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )

            if proc.returncode == 0 and "SANDBOX_OK" in proc.stdout:
                with open(output_path, "r", encoding="utf-8") as f:
                    result["result"] = f.read()
                result["success"] = True
                return result

            raw = (proc.stderr or proc.stdout).strip()
            if "[SANDBOX]" in raw and "blocked" in raw.lower():
                result["blocked_write"] = True
            result["error"] = raw[:500]
            return result

    except subprocess.TimeoutExpired:
        # subprocess.run() has already killed the child process by the time
        # this exception reaches us — the actual fix this function exists
        # to provide, unlike the old ThreadPoolExecutor path where a
        # TimeoutError was caught but the worker thread kept running.
        result["error"] = f"apply_to_code sandboxed call timed out after {timeout}s (process killed)"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def _log_apply_to_code_invocation(changed: bool, before_len: int, after_len: "int | None", error: "str | None" = None) -> None:
    """
    Ground-truth evidence for liveness_ledger.py's apply_to_code check —
    written here, by this protected wrapper, not by the generated hook
    itself. The hook (app.core.self_edit_generated.apply_to_code) is
    LLM-generated and untrusted; its own claim to have done something
    useful is exactly the kind of self-report GREMLIN_ROLE.md's Core
    Operating Principle says must not be trusted without an independent
    observer. This is that observer: it records what actually happened
    to the code (did the string change, by how much) regardless of what
    the hook itself believes it did.
    """
    try:
        os.makedirs(os.path.dirname(_APPLY_TO_CODE_LOG), exist_ok=True)
        entry = {
            "ts": datetime.now().astimezone().isoformat(),
            "changed": bool(changed),
            "before_len": before_len,
            "after_len": after_len,
            "error": error,
        }
        with open(_APPLY_TO_CODE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.debug(f"[SELF-EDIT] apply_to_code invocation logging failed: {e}")


def _apply_self_edit_output(code: str) -> str:
    """
    Best-effort post-processing pass over freshly-generated self-edit code,
    using whatever self_edit_generated.py currently has deployed — the one
    real behavioral consequence a self-edit cycle can have on this system,
    gated entirely on the fixed `apply_to_code(code: str) -> str` contract
    (CODE_OUTPUT_RULES rule 10). A deployed module that doesn't define this
    (e.g. today's bootstrap content) is a pure no-op — zero behavior change
    until a future cycle actually produces the contract.
    """
    module = _load_self_edit_generated_for_use()
    if module is None:
        return code
    fn = getattr(module, "apply_to_code", None)
    if not callable(fn):
        return code
    try:
        sig = inspect.signature(fn)
        if len(sig.parameters) != 1:
            return code
    except (TypeError, ValueError):
        return code
    sandboxed = _run_apply_to_code_sandboxed(code, timeout=2.0)

    if sandboxed["blocked_write"]:
        # Finding 31/41 B3: a candidate caught attempting a real filesystem
        # write mid-call has broken its documented pure-function contract —
        # don't trust its returned transformation either. Now enforced by
        # the real kernel Seatbelt profile + safe_exec_wrapper.py's patches
        # (see _run_apply_to_code_sandboxed()'s docstring), not the removed
        # in-process monkeypatch this replaces.
        logging.warning(
            "[SELF-EDIT] apply_to_code attempted a filesystem write during "
            "invocation — rejecting output, hook violates its pure-function "
            "contract (Finding 31/41 B3). Detail: %s", sandboxed["error"],
        )
        _log_apply_to_code_invocation(
            changed=False, before_len=len(code), after_len=None,
            error=f"blocked_write_attempt: {sandboxed['error']}",
        )
        return code

    if not sandboxed["success"]:
        logging.debug(f"[SELF-EDIT] apply_to_code raised/timed out in sandbox, ignoring: {sandboxed['error']}")
        _log_apply_to_code_invocation(changed=False, before_len=len(code), after_len=None, error=sandboxed["error"])
        return code

    result = sandboxed["result"]
    if isinstance(result, str) and result.strip() and result != code:
        _log_apply_to_code_invocation(changed=True, before_len=len(code), after_len=len(result))
        return result
    _log_apply_to_code_invocation(changed=False, before_len=len(code), after_len=len(code))
    return code


def generate_code_from_plan(plan: str, temperature: float | None = None, trace_id: "str | None" = None) -> tuple:
    """
    Generate Python code guided by the logic plan.
    v2.2: returns (code, model_name) tuple so sandbox outcomes
    can be fed back into river with the correct model identity.
    Previously model name was lost after echo_query returned.

    SELF-EDIT ONLY — see CODE_OUTPUT_RULES' own comment above for the
    Tier-4-confirmed evidence that this function's framing measurably
    hurts general/conversational coding tasks. Do not call this for
    anything other than generating a real self_edit_generated.py
    candidate or simulating one (wolf_friction_bridge.py's dry run).

    trace_id (2026-09-05, Plan 5 correlation-ID pass): optional, passed
    straight through to echo_query() — same additive, backward-compatible
    contract as plan_code_logic()'s own trace_id parameter.
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

        # Resolve model name before querying so we can track it. Uses
        # "self_edit_coding" (Finding 35 fix, 2026-07-17), not "coding" —
        # a genuinely separate RiverBrain bucket from conversational coding
        # help, since choose_model()'s entropy/ranking here was previously
        # reading a stat self-edit itself never contributed to.
        model_name, _ = choose_model(code_prompt, task_type="self_edit_coding")
        code = echo_query(code_prompt, task_type="coding", temperature=temperature, trace_id=trace_id)

        if not code:
            logging.warning("generate_code returned empty, using stub.")
            return "print('Hello from self-edit stub')", model_name

        code = _strip_markdown_fences(code)

        if not _looks_like_python(code):
            logging.warning("[PROMPT GUARD] Code output failed prose check. Attempting extraction.")
            code = _extract_code_block(code)

        code = _apply_self_edit_output(code)

        # Feed this real generation attempt into RiverBrain's "self_edit_coding"
        # bucket (Finding 35 fix) — fires on every attempt, not just the ~1/hour
        # that reaches real production, so this is also denser data than the
        # sandbox-outcome signal alone. Best-effort: never let a learning-signal
        # failure break actual code generation.
        try:
            get_river_brain().learn(model_name, "self_edit_coding", code)
        except Exception as _learn_err:
            logging.debug(f"[SELF-EDIT] self_edit_coding learn() failed: {_learn_err}")

        return code, model_name
    except Exception as e:
        logging.error(f"Code generation failed: {e}")
        return "print('Hello from self-edit stub')", "unknown"

# -----------------------------
# --- Core Self-Edit ----------
# -----------------------------
def execute_self_edit(prompt: str, intensity: float | None = None, dry_run: bool = False, **kwargs):
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

    dry_run: when True, every gate through staging (plan, codegen, import
    pre-validation, AST safety scan, sandbox test, syntax validate, staging
    import test) still runs for real — only the final backup/save/load into
    production is skipped. Returns (True, STAGING_FILE) on a passing
    candidate instead of (True, "Success"), so callers can inspect/score the
    actual staged code. Previously accepted via **kwargs and silently
    ignored everywhere; see perform_self_edit() and EchoOptuna.objective()
    for why this matters (Optuna trial-waste fix).
    """
    # Plan 5 correlation-ID pass (2026-09-05): one trace_id per real
    # self-edit attempt, threaded through every echo_query() call this
    # attempt makes (plan, codegen, retry) and into record_pending_outcome()
    # below, so interaction_log.jsonl/council_deliberations.jsonl entries
    # from one attempt can be joined to its self_edit_outcomes.jsonl row.
    # Deliberately scoped to this function's own real attempts — dry-run
    # trials get their own trace_id too (same mint point, harmless since
    # dry runs never reach record_pending_outcome, which only fires on the
    # real production-deploy success path).
    trace_id = str(uuid.uuid4())

    # Attempt-level ledger (2026-09-07, see self_edit_attempt_ledger.py):
    # observable facts only, written exactly once at whichever terminal
    # branch this attempt reaches. Never read by anything in this function
    # or anywhere else in the pipeline — pure write-only observation sink.
    _attempt = {
        "trace_id": trace_id,
        "task_type": None,
        "timestamp": datetime.utcnow().isoformat(),
        "initial_f2_outcome": None,
        "initial_f2_error": None,
        "retry_occurred": False,
        "retry_f2_outcome": None,
        "retry_f2_error": None,
        "final_f2_outcome": None,
        "fitness_score": None,
        "production_score": None,
        "fitness_decision": None,
        "deployed": False,
        "terminal_state": None,
    }

    def _finish_attempt(terminal_state: str) -> None:
        _attempt["terminal_state"] = terminal_state
        _record_attempt_ledger(dict(_attempt))

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
        _finish_attempt("rejected_meaningless_prompt")
        return False, "Rejected: prompt is not a meaningful self-edit task"

    task_type = detect_task_type(prompt)
    _attempt["task_type"] = task_type
    reflection_entry = {
        "prompt": prompt,
        "task_type": task_type,
        "generated_code": None,
        "timestamp": datetime.utcnow().isoformat(),
        "sandbox_feedback": None,
        "result": "pending"
    }
    save_reflection(reflection_entry)

    # Audit finding: mastery_advice was computed and journaled every cycle
    # but never actually reached the generation prompt — real, genuine
    # guidance (code_quality.py's live empty-file scan, etc.) sat in
    # SELF_EDIT.log unread by the model actually writing the code. Now
    # threaded into plan_code_logic() below. mastery_advice defaults to ""
    # so a failure here degrades to "no extra guidance this cycle" rather
    # than leaving the variable undefined for the reference below.
    mastery_advice = ""
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
        plan = plan_code_logic(prompt, mastery_note=mastery_advice, trace_id=trace_id)
    except Exception as _e:
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        logging.error(f"[SELF-EDIT] plan_code_logic raised: {_e}")
        _finish_attempt("plan_generation_failed")
        return False, f"Plan generation failed: {_e}"

    # Step 2: Code generation — now returns (code, model_name)
    try:
        code, model_name = generate_code_from_plan(plan, temperature=temperature, trace_id=trace_id)
    except Exception as _e:
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        logging.error(f"[SELF-EDIT] generate_code_from_plan raised: {_e}")
        _finish_attempt("code_generation_failed")
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
        _finish_attempt("import_hallucination")
        return False, f"Import pre-validation failed: {import_err}"

    # Step 2c: AST write-path safety gate — must fire before any subprocess executes code
    try:
        scan_for_unsafe_operations(code)
    except ValueError as _safety_err:
        append_to_journal("SELF_EDIT", f"prompt: {prompt[:80]} | result: safety_blocked | reason: {_safety_err}")
        logging.warning(f"[SELF-EDIT][SAFETY] Blocked before sandbox: {_safety_err}")
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        _finish_attempt("safety_blocked")
        return False, f"Safety gate blocked: {_safety_err}"

    # Step 2d: Sandbox test — feed outcome into river
    success, sandbox_error = test_code_in_sandbox(code)
    _attempt["initial_f2_outcome"] = success
    _attempt["initial_f2_error"] = None if success else sandbox_error
    reflection_entry["sandbox_feedback"] = "success" if success else f"failed: {sandbox_error}"
    reflection_entry["result"] = "success" if success else "failed"
    # 2026-07-19: deliberately NOT saved here (no save_reflection() call).
    # This is not yet a terminal state — retry, staging, dry_run, the
    # fitness gate, and load can all still change the true outcome below,
    # and every one of those branches saves reflection_entry itself when
    # it reaches its own terminal state. Saving this interim value too
    # was double-logging one logical attempt as both a win and a loss
    # whenever a later branch changed the result (confirmed live: every
    # dry-run success in reflection_shard.jsonl had a matching "success"
    # + "success_dry_run" pair at the same timestamp, mechanically
    # halving the real success rate introspection_channel.py reports).

    # v2.2: river learns from sandbox outcome with correct model identity
    river = get_river_brain()
    if success:
        river.learn_from_sandbox_outcome(model_name, success=True, code=code)
    else:
        river.learn_from_sandbox_outcome(model_name, success=False, error=sandbox_error or "")

    if not success:
        _attempt["retry_occurred"] = True
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

        # Resolve retry model name for tracking. "self_edit_coding" per
        # Finding 35's fix — same reasoning as the primary attempt above.
        retry_model_name, _ = choose_model(retry_prompt, task_type="self_edit_coding")
        retry_code = echo_query(retry_prompt, task_type="coding", trace_id=trace_id)

        if retry_code:
            retry_code = _strip_markdown_fences(retry_code)
            if not _looks_like_python(retry_code):
                retry_code = _extract_code_block(retry_code)
            retry_code = _strip_toplevel_self_calls(retry_code)
            try:
                get_river_brain().learn(retry_model_name, "self_edit_coding", retry_code)
            except Exception as _learn_err:
                logging.debug(f"[SELF-EDIT] retry self_edit_coding learn() failed: {_learn_err}")

            retry_success, retry_error = test_code_in_sandbox(retry_code, "temp_self_edit_retry.py")
            _attempt["retry_f2_outcome"] = retry_success
            _attempt["retry_f2_error"] = None if retry_success else retry_error

            # v2.2: river learns from retry outcome too
            if retry_success:
                river.learn_from_sandbox_outcome(retry_model_name, success=True, code=retry_code)
                logging.info("Retry succeeded after error feedback.")
                code = retry_code
                success = True
                # 2026-07-19: field updates kept (so staging/dry_run/fitness-gate
                # below operate on the corrected code and result), but the
                # save_reflection() call that used to sit here is gone — same
                # reasoning as the sandbox-result block above. This is still
                # not a terminal state (staging, dry_run, and the fitness gate
                # can all still change the outcome), and every real terminal
                # branch below already saves reflection_entry itself.
                reflection_entry["sandbox_feedback"] = "success_on_retry"
                reflection_entry["result"] = "success"
                reflection_entry["generated_code"] = code
                reflection_entry["model_used"] = retry_model_name
            else:
                river.learn_from_sandbox_outcome(retry_model_name, success=False, error=retry_error or "")
                logging.warning(f"Retry also failed: {_sanitize_sandbox_error(retry_error)}. Keeping stub.")
        else:
            logging.warning("Retry generated empty code. Keeping stub.")

    _attempt["final_f2_outcome"] = success

    # Step 3: Validate syntax (AST-only check)
    if not validate_code(code):
        append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: invalid_syntax")
        logging.warning("Generated code failed syntax check, saving stub instead.")
        code = "# Self-edit stub — syntax validation failed\nprint('Hello from self-edit stub')"

    # Step 3.5: Staging import test — gate before production write
    # Writes to a per-call-unique staging file and does a full subprocess
    # import. If this fails, production is untouched; staging file preserved
    # for inspection. Per-call-unique (not the shared STAGING_FILE constant)
    # because two concurrent real trials could otherwise overwrite each
    # other's staged file between one trial's write and its subprocess
    # actually reading it.
    _prune_stale_staging_files()
    call_staging_file = os.path.join(STAGING_DIR, f"self_edit_candidate_{uuid.uuid4().hex}.py")
    staged_ok, stage_err = _stage_and_import_test(code, staging_file=call_staging_file)
    if not staged_ok:
        append_to_journal(
            "SELF_EDIT",
            f"prompt: {prompt} | result: staging_import_failed | error: {stage_err}"
        )
        logging.error(f"[STAGING] Import test failed — production unchanged. Error: {stage_err}")
        reflection_entry["result"] = "failed"
        save_reflection(reflection_entry)
        _finish_attempt("staging_import_failed")
        return False, f"Staging import test failed: {stage_err}"
    logging.info("[STAGING] Import test passed — proceeding to production write.")

    # Attempt ledger deliberately does NOT record dry_run trials below: dry
    # runs already never reach record_pending_outcome() either (by design —
    # see that function's own docstring), and Optuna's real dry-run search
    # fires roughly 10x/hour versus at most a few real attempts/hour — mixing
    # that volume into this ledger would swamp the real attempts it exists
    # to preserve. Scoped to real (dry_run=False) attempts only.
    if dry_run:
        reflection_entry["result"] = "success_dry_run"
        reflection_entry["dry_run"] = True
        # Gap-closure plan Phase C2c (2026-07-23): lets echo_optuna.py's
        # _score_result() correctly attribute this trial's quality delta to
        # the model that actually generated it (model_used, already tracked
        # above) by matching on this exact staging path -- without changing
        # this function's own (True, call_staging_file) return contract,
        # which other callers depend on staying a plain 2-tuple.
        reflection_entry["staging_path"] = call_staging_file
        save_reflection(reflection_entry)
        append_to_journal(
            "SELF_EDIT",
            f"prompt: {prompt[:80]} | result: dry_run_staged | path: {call_staging_file}"
        )
        logging.info(
            "[SELF-EDIT] dry_run=True — staged candidate at %s, skipping production write.",
            call_staging_file,
        )
        return True, call_staging_file

    # Step 3.7 through Step 6, all under one lock: previously this whole
    # sequence (read current production code → compare quality → backup →
    # save → load) ran with no lock at all. Two concurrent real self-edit
    # attempts (confirmed real: the hourly AutonomousSelfEdit loop and
    # model_guided_autonomous_loop both call into this pipeline on separate
    # timers) could each read production at the same "current" quality,
    # both pass the fitness gate, and the second writer's backup_existing_code()
    # + save_code() would silently overwrite whatever the first writer just
    # deployed — even if the first candidate scored higher. Locking the full
    # compare-through-load sequence closes that TOCTOU window.
    with _self_edit_deploy_lock:
        # Step 3.7: Fitness gate — only deploy if this candidate is at least as
        # good as what's currently in production. Reuses the same quality scorer
        # now driving Optuna's hyperparameter selection (echo_optuna.py), so
        # deployment and trial-selection are judged by the same standard.
        # task_type is always "coding" here (not detect_task_type(prompt)) —
        # self-edit always generates Python code regardless of which skill
        # it's targeting, same reasoning as today's Optuna objective fix.
        try:
            from echo_quality_scorer import _score_response_quality
            candidate_quality = _score_response_quality(code, task_type="coding")
            current_code = ""
            if os.path.isfile(SELF_EDIT_FILE):
                with open(SELF_EDIT_FILE, "r", encoding="utf-8") as f:
                    current_code = f.read()
            # Nothing meaningfully deployed yet (bootstrap) — anything passes.
            current_quality = (
                _score_response_quality(current_code, task_type="coding")
                if current_code.strip() else -1
            )
            _attempt["fitness_score"] = candidate_quality
            _attempt["production_score"] = current_quality
            if candidate_quality < current_quality:
                reflection_entry["result"] = "rejected_not_improvement"
                reflection_entry["candidate_quality"] = candidate_quality
                reflection_entry["current_quality"] = current_quality
                save_reflection(reflection_entry)
                append_to_journal(
                    "SELF_EDIT",
                    f"prompt: {prompt[:80]} | result: rejected_not_improvement | "
                    f"candidate_quality={candidate_quality} current_quality={current_quality}"
                )
                logging.info(
                    "[SELF-EDIT] Candidate quality (%d) does not improve on current production (%d) — not deployed.",
                    candidate_quality, current_quality,
                )
                _attempt["fitness_decision"] = "rejected_not_improvement"
                _attempt["deployed"] = False
                _finish_attempt("rejected_not_improvement")
                return False, (
                    f"Rejected: candidate quality ({candidate_quality}) does not improve "
                    f"on current production ({current_quality})"
                )
            _attempt["fitness_decision"] = "accepted"
        except Exception as _fe:
            # Quality comparison is a heuristic, not a safety gate (those already
            # passed above) — fail open on infrastructure errors rather than
            # blocking a deploy over a scoring hiccup.
            logging.warning(f"[SELF-EDIT] Fitness comparison failed, deploying anyway: {_fe}")

        # Step 4: Backup + Step 5: Save to production
        try:
            backup_existing_code()
            save_code(code)
        except Exception as _e:
            reflection_entry["result"] = "failed"
            save_reflection(reflection_entry)
            logging.error(f"[SELF-EDIT] File write failed: {_e}")
            _attempt["deployed"] = False
            _finish_attempt("file_write_failed")
            return False, f"File write failed: {_e}"

        # Step 6: Load (should succeed — staging already validated this).
        # Return value intentionally unused — no functions from the module are called
        # by name anywhere in the production path.  See LOAD_AUDIT entries in SELF_EDIT.log.
        try:
            loaded_module = load_self_edit_module()
            if loaded_module is None:
                # load_self_edit_module() returns None both when F3's post-write
                # scan trips (having already restored the prior backup) and when
                # the file is unexpectedly missing — neither raises, so this
                # branch previously fell straight through to "Success" below
                # regardless of which one happened.
                append_to_journal(
                    "SELF_EDIT",
                    f"prompt: {prompt} | result: load_blocked | reason: F3 scan failed or file missing, see prior log lines"
                )
                logging.error("[SELF-EDIT] load_self_edit_module() returned None — not a real success.")
                reflection_entry["result"] = "load_blocked"
                save_reflection(reflection_entry)
                _attempt["deployed"] = False
                _finish_attempt("load_blocked")
                return False, "Load blocked: F3 post-write safety scan failed (backup restored) or file missing"
            append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: success | timestamp: {datetime.utcnow().isoformat()}")
            logging.info("Self-edit loaded successfully.")
            # 2026-07-19: previously the only terminal branch with no explicit
            # save_reflection() call — it relied entirely on the (now-removed)
            # interim sandbox-result save still holding "success", which
            # happened to be correct here by coincidence since nothing on
            # this path changes the result. Explicit now, for the same reason
            # every other terminal branch already saves: one true final row
            # per logical attempt, not an inherited accident.
            reflection_entry["result"] = "success"
            save_reflection(reflection_entry)
            try:
                from app.core.self_edit_outcome_tracker import record_pending_outcome
                record_pending_outcome(task_type, trace_id=trace_id)
            except Exception as _ote:
                logging.debug(f"[SELF-EDIT-OUTCOME] record_pending_outcome failed: {_ote}")
            try:
                from app.core.snapshot_manager import take_snapshot as _snap
                _snap("post_self_edit")
            except Exception as _snap_err:
                logging.warning("[SNAPSHOT] post_self_edit snapshot failed: %s", _snap_err)
            _attempt["deployed"] = True
            _finish_attempt("success")
            return True, "Success"
        except Exception as e:
            append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: load_failed | error: {traceback.format_exc()}")
            logging.error(f"Failed to load self-edit: {e}")
            reflection_entry["result"] = "failed"
            save_reflection(reflection_entry)
            _attempt["deployed"] = False
            _finish_attempt("load_failed")
            return False, f"Load failed: {e}"

# -----------------------------------------------------------------------
# --- Protected-target escalation path (advisory only) ------------------
# -----------------------------------------------------------------------
# EDIT_FORBIDDEN_TARGETS remains an absolute, unconditional write
# prohibition — save_code() is completely unchanged by anything below and
# still raises PermissionError for any of these paths. Previously, that was
# also the END of the story: a rejected candidate simply vanished with no
# trace of what was attempted or why. This gives that dead-end a real, safe
# next step — a human-reviewed proposal queue with a multi-model advisory
# opinion attached — without granting any new autonomous write capability.
# Nothing in this section is currently wired to any autonomous trigger; it
# is a callable capability, not a new default behavior.
_PROPOSALS_DIR = os.path.join(_PROJECT_ROOT, "self_edit_proposals")
_MAX_PROPOSALS = 25


def _prune_stale_proposals():
    if not os.path.isdir(_PROPOSALS_DIR):
        return
    files = sorted(
        (f for f in os.listdir(_PROPOSALS_DIR) if f.endswith(".patch")),
        reverse=True,
    )
    for stale in files[_MAX_PROPOSALS:]:
        try:
            os.remove(os.path.join(_PROPOSALS_DIR, stale))
        except Exception as e:
            logging.warning(f"[SELF-EDIT] Failed to prune stale proposal {stale}: {e}")


def _council_review_core_edit(target_file: str, candidate_code: str, reason: str) -> dict:
    """
    Advisory-only multi-model review of a proposed edit to a protected file.
    This NEVER gates a write — protected-file writes are never made by this
    module regardless of verdict — it exists purely so a human reading the
    queued proposal has more than one model's opinion to weigh, using the
    same council models self-edit already ranks for coding tasks.
    """
    try:
        models = rank_models(task_type="coding")[:3]
    except Exception:
        models = []
    if not models:
        return {"verdict": "NO_COUNCIL_AVAILABLE", "votes": []}

    review_prompt = (
        "You are reviewing a PROPOSED code change to a protected core file of "
        "an autonomous AI system. This change has NOT been applied and cannot "
        "be applied without explicit human approval. Assess correctness and "
        "safety risk only, not style.\n\n"
        f"Target file: {target_file}\n"
        f"Stated reason for change: {reason}\n\n"
        f"Proposed replacement content:\n```\n{candidate_code[:4000]}\n```\n\n"
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
    return {"verdict": f"{approvals}/{len(votes)} APPROVE", "votes": votes}


def _extract_fenced_or_raw(text: str) -> str:
    """
    Models often wrap output as "Here is the diff:\\n```\\n...\\n```" even
    when told not to — a shape _extract_code_block() (built for the short
    self_edit_generated.py snippets execute_self_edit() generates) doesn't
    handle: a trailing fence line breaks its ast.parse() check, so it gives
    up and returns the whole prose-plus-fence text unchanged (confirmed live
    during testing, before propose_core_edit() switched to requesting a
    diff). Looks for the first fenced block anywhere in the text (any or no
    language tag, e.g. ```diff / ```python / bare ```) and uses its content
    if found; otherwise falls back to the existing behavior, unchanged.
    """
    match = re.search(r"```[a-zA-Z]*[ \t]*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1)
    # No closed fence found — if generation was cut off mid-output before
    # closing it (confirmed live: hit the 512-token ceiling mid-diff),
    # everything after the opening fence is still the real content, and is
    # a better result than falling through to _extract_code_block(), which
    # is ast.parse()-based and not a good fit for diff text (diffs are not
    # standalone valid Python).
    open_match = re.search(r"```[a-zA-Z]*[ \t]*\n", text)
    if open_match:
        return text[open_match.end():]
    stripped = _strip_markdown_fences(text)
    if not _looks_like_python(stripped):
        stripped = _extract_code_block(stripped)
    return stripped


_DIFF_RISK_MARKERS = (
    "subprocess.", "os.system", "os.popen", "os.exec", "os.spawn",
    "shutil.rmtree", "shutil.move", "shutil.copy",
    "eval(", "exec(", "ctypes.CDLL", "importlib.reload",
    ".write_text(", ".write_bytes(",
)


def _scan_diff_added_lines(diff_text: str) -> str:
    """
    Lightweight, best-effort heuristic scan of a diff's added (+) lines,
    for the human reviewer's benefit only. Deliberately NOT
    scan_for_unsafe_operations() (the real F1 AST gate) — that requires a
    fully valid, standalone Python module and would report "failed to
    parse" on nearly every real diff fragment, since added lines are rarely
    valid Python in isolation (missing enclosing def/class, partial
    indentation context). scan_for_unsafe_operations() itself is completely
    untouched and still the only gate on the real self_edit_generated.py
    deploy path — this function is not used anywhere near that path.
    """
    added_lines = [
        line[1:] for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    hits = sorted({
        marker for marker in _DIFF_RISK_MARKERS
        if any(marker in line for line in added_lines)
    })
    if hits:
        return f"heuristic scan of added lines flagged: {', '.join(hits)} — review carefully"
    return "heuristic scan of added lines found no obviously risky patterns (not a full AST parse)"


def _build_dissent_entry(target_file: str, prompt: str, council: dict, proposal_path: str) -> dict:
    """
    Pure — no I/O, directly unit-testable (see scripts/verify_liveness_ledger.py's
    own header for why this codebase splits pure evaluation from I/O this way).

    Three states, not two: council review can genuinely disagree, genuinely
    agree, or never have happened at all (council_available=False, when
    rank_models() returned nothing — see _council_review_core_edit()'s
    NO_COUNCIL_AVAILABLE path). Folding the third case into either extreme
    would either divide by zero or silently read an absence of signal as a
    real one — caught during planning, before it shipped, not after.
    """
    votes = council.get("votes") or []
    total = len(votes)
    approvals = sum(1 for v in votes if v.get("verdict") == "APPROVE")
    council_available = total > 0
    unanimous = council_available and approvals == total
    return {
        "ts": datetime.utcnow().isoformat() + "Z",
        "target_file": target_file,
        "reason": prompt,
        "proposal_path": proposal_path,
        "council_verdict": council.get("verdict"),
        "votes": votes,
        "council_available": council_available,
        "unanimous": unanimous,
        "approvals": approvals,
        "total": total,
    }


def _log_dissent_entry(entry: dict) -> None:
    """
    Best-effort, never raises — a logging failure must never affect
    propose_core_edit()'s real return value. Always appends the entry
    (even a unanimous or no-council-available one, for honest
    auditability — the same "log the empty/negative case too" discipline
    seam_engine.py and memory_write_validator.py's EMPTY_SIGNAL fix already
    use elsewhere in this codebase). Only genuine disagreement
    (council_available and not unanimous) publishes to the Global Workspace
    and harvests a real curiosity question — publishing the no-council-
    available case would confabulate a disagreement signal from an absence
    of one.
    """
    try:
        with _dissent_log_lock:
            os.makedirs(os.path.dirname(_DISSENT_LOG_PATH), exist_ok=True)
            with open(_DISSENT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logging.debug(f"[SELF-EDIT] dissent log write failed: {e}")

    if not (entry["council_available"] and not entry["unanimous"]):
        return

    target_file = entry["target_file"]
    votes_summary = "; ".join(
        f"{v.get('model')}: {v.get('verdict')}" for v in entry["votes"]
    )
    summary = (
        f"Council split {entry['approvals']}/{entry['total']} on a proposed edit "
        f"to {target_file} — {votes_summary}"
    )
    salience = 1.0 - (entry["approvals"] / entry["total"])

    # Same idiom as _record_convergence()'s own publish_salience call above —
    # lazy import, best-effort, never raises.
    try:
        from app.core.echo_core import get_echo_core
        core = get_echo_core()
        if core:
            core.publish_salience(
                source="self_edit_manager",
                kind="dissent.registered",
                summary=summary,
                detail={"target_file": target_file, "votes": entry["votes"]},
                salience=salience,
            )
    except Exception:
        pass

    # Question built dynamically from the real target/votes, not a fixed
    # template — harvest_question()'s near-duplicate filter would otherwise
    # silently eat every subsequent dissent worded similarly.
    try:
        from app.core import garden_manager
        question = (
            f"{votes_summary} — the council didn't agree on the proposed change "
            f"to {target_file} ({entry['reason'][:150]}). Which side had it right?"
        )
        garden_manager.harvest_question(question, category="dissent", source="dissent_log")
    except Exception:
        pass


def propose_core_edit(target_file: str, prompt: str, intensity: float | None = None) -> tuple[bool, str]:
    """
    Advisory-only path for a self-edit that would target a file in
    EDIT_FORBIDDEN_TARGETS. save_code()'s write prohibition is completely
    unchanged and unconditional — this function never calls save_code() and
    never writes to target_file. It plans against target_file's real current
    contents, generates a targeted diff (not a full-file replacement — see
    the code_prompt comment below for why), attaches a multi-model advisory
    council review, and writes the result to self_edit_proposals/*.patch for
    a human to read and manually apply if they agree. Only accepts
    target_file values already in EDIT_FORBIDDEN_TARGETS — this is not a
    general-purpose second write path, it is specifically the escalation
    route for the one case save_code() always refuses.
    """
    norm_target = os.path.normpath(target_file)
    is_forbidden = any(norm_target == os.path.normpath(f) for f in EDIT_FORBIDDEN_TARGETS)
    if not is_forbidden:
        return False, f"{target_file} is not a protected target — use the normal self-edit path instead"

    abs_target = os.path.join(_PROJECT_ROOT, target_file)
    try:
        with open(abs_target, "r", encoding="utf-8") as f:
            current_contents = f.read()
    except Exception as e:
        return False, f"Could not read target file: {e}"

    temperature = None
    if intensity is not None:
        temperature = max(0.2, min(1.2, round(0.2 + float(intensity) * 1.0, 3)))

    plan_prompt = (
        f"{PLAN_OUTPUT_RULES}\n\n"
        f"You are proposing a targeted modification to a protected core file of an "
        f"autonomous AI system — this will be reviewed by a human before ever being "
        f"applied. Keep the change minimal and narrowly scoped to the stated goal.\n\n"
        f"Target file ({target_file}) current contents:\n```\n{current_contents[:6000]}\n```\n\n"
        f"Task: {prompt}"
    )
    try:
        plan = echo_query(plan_prompt, task_type="coding")
        if not plan or not plan.strip():
            plan = f"1. Modify {target_file} to: {prompt[:200]}"
    except Exception as e:
        return False, f"Plan generation failed: {e}"

    # Asks for a diff, not a full-file replacement: query_ollama()'s payload
    # hardcodes num_predict=512 (confirmed live — generate_code()'s own
    # max_tokens param is similarly dead, never forwarded), so a "complete
    # new contents of the file" request against any real production file
    # reliably truncates mid-file before ever closing its markdown fence.
    # A small, targeted diff both fits the real budget and is what a human
    # reviewer actually wants to read here.
    code_prompt = (
        f"You are proposing a minimal, targeted modification to a protected core "
        f"file of an autonomous AI system, for human review only — it will not be "
        f"applied automatically. Output ONLY a unified diff (--- a/... / +++ b/... / "
        f"@@ ... @@ hunks) representing the smallest change that accomplishes the "
        f"plan below. Do NOT output the complete file. No explanation, no markdown "
        f"fences, no commentary — the diff text only.\n\n"
        f"Current contents of {target_file}:\n```\n{current_contents}\n```\n\n"
        f"Plan to implement:\n{plan}"
    )
    try:
        candidate_diff = echo_query(code_prompt, task_type="coding", temperature=temperature)
    except Exception as e:
        return False, f"Code generation failed: {e}"
    candidate_diff = _extract_fenced_or_raw(candidate_diff or "")
    safety_note = _scan_diff_added_lines(candidate_diff)

    council = _council_review_core_edit(target_file, candidate_diff, prompt)

    os.makedirs(_PROPOSALS_DIR, exist_ok=True)
    _prune_stale_proposals()
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_stub = re.sub(r"[^a-zA-Z0-9_]+", "_", target_file)
    proposal_path = os.path.join(_PROPOSALS_DIR, f"{ts}_{safe_stub}.patch")

    header_lines = [
        f"# PROPOSED EDIT — target: {target_file}",
        f"# NOT APPLIED. Never auto-applied. For human review only.",
        f"# Generated: {datetime.utcnow().isoformat()}Z",
        f"# Reason: {prompt}",
        f"# Safety scan: {safety_note}",
        f"# Council verdict: {council['verdict']}",
    ]
    for v in council["votes"]:
        header_lines.append(f"#   {v['model']}: {v['verdict']} — {v['rationale']}")
    header_lines.append("# ---- proposed diff below (apply manually if you agree) ----")
    header = "\n".join(header_lines) + "\n\n"

    with open(proposal_path, "w", encoding="utf-8") as f:
        f.write(header + candidate_diff)

    append_to_journal(
        "SELF_EDIT",
        f"prompt: {prompt[:80]} | result: proposed_core_edit_for_review | "
        f"target: {target_file} | council: {council['verdict']} | proposal: {proposal_path}"
    )
    logging.info(
        f"[SELF-EDIT] Core-file proposal for {target_file} written to {proposal_path} "
        f"(council: {council['verdict']})"
    )

    # Dissent log (2026-07-17) — never affects the return value below, even
    # on failure; see _log_dissent_entry()'s own docstring.
    try:
        dissent_entry = _build_dissent_entry(target_file, prompt, council, proposal_path)
        _log_dissent_entry(dissent_entry)
    except Exception as _dissent_err:
        logging.debug(f"[SELF-EDIT] dissent log step failed: {_dissent_err}")

    return True, proposal_path


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

# Guards the cooldown check-and-stamp (perform_self_edit) and the whole
# fitness-gate-through-deploy critical section (execute_self_edit) — two
# independent, unsynchronized threads (the hourly AutonomousSelfEdit loop
# and model_guided_autonomous_loop, plus any human-triggered manual edit)
# can genuinely call into this pipeline concurrently. Without this, a
# worse candidate could read production as "current" before a better
# candidate's concurrent write landed, then silently overwrite it after —
# a real TOCTOU race in the fitness gate added earlier this pass. One lock
# for both sections since they're the same real-write resource (production
# self_edit_generated.py) — this is intentionally the one lock in this
# effort allowed to be held across a comparatively slow section (plan/
# codegen/sandbox already happened before this lock is ever acquired;
# only the fitness-compare-through-load tail is inside it).
_self_edit_deploy_lock = threading.Lock()

# One static sentence per family describing what the problem domain *is* —
# the minimal irreducible fixed text; everything else in the Focus prompt
# below is now built from real convergence/outcome data instead of being
# one of these three strings verbatim. (threshold, family, domain_sentence),
# family keys map 1:1 onto _CONVERGENCE_FAMILIES.
_FOCUS_FAMILY_BY_CREATIVITY = [
    # prose_stripping REACTIVATED 2026-09-27, after being paused 2026-07-19
    # on real evidence of a possible capability ceiling (three raw council
    # models independently failed the exact real test case, asked cleanly
    # outside the self-edit pipeline — see Finding 43 / PENDING_DECISIONS.md
    # item #6). New evidence since then bears directly on that hypothesis,
    # not assumed to resolve it:
    # audits/2026-09-27_restart_persistence_of_acquired_competence.md ran a
    # controlled, held-out A/B test on a task family structurally identical
    # to this one (find where leading prose ends and real code begins) using
    # the same class of model. Given no guidance, it solved 4/10 held-out
    # cases; given the three concrete rules below (independently verified,
    # not this session's guess), it solved 9/10, p=0.03 one-sided, and the
    # actual generated code was inspected: every failure without guidance
    # was the exact incomplete-marker-set bug named in clause 1 below. This
    # is real evidence the model CAN do this correctly once told — it does
    # not reliably invent the guidance for itself — a different, more
    # hopeful diagnosis than "capability ceiling." Not guaranteed to fix
    # real self-edit convergence; only real subsequent cycles will show
    # that. non_convergent_streak is deliberately NOT reset (Finding 32's
    # own discipline) — resetting it to make this look better before any
    # real cycle has run would be exactly the self-report manipulation this
    # ledger exists to catch.
    #
    # (Prior 2026-07-15 rewrite, superseded by the above rather than
    # deleted, for the record: a pure natural-language description with no
    # concrete example had produced 30+ distinct, mutually inconsistent
    # implementations across 93+ real cycles; that rewrite added one
    # concrete example and an import reminder but was never validated by a
    # controlled experiment the way the rules below now are.)
    (0.33, "prose_stripping", (
        "fix the most common sandbox failure (prose detected in code output) — "
        "add or tighten a prose-detection guard that strips any leading "
        "natural-language sentence before the first valid Python token. "
        "Three specific rules, independently validated by a real held-out "
        "experiment (not a guess): (1) check for a COMPLETE set of code-start "
        "markers — a decorator line starting with `@`, a docstring starting "
        "with `\"\"\"` or `'''`, an `import`/`from` statement, or `def`/`class` "
        "— checking only `def`/`class` skips past a leading decorator or "
        "docstring and cuts off real code. (2) Only treat a marker as real if "
        "it appears at the very start of its own line (after stripping leading "
        "whitespace) — ordinary prose sentences can contain these exact words "
        "(e.g. 'this import of new ideas'). (3) Once the start is found, return "
        "every line from there to the actual end of the text, rather than one "
        "large regex trying to match the whole code span — a single big regex "
        "has been observed to cut off the real code's final line. Import every "
        "module you use (e.g. `import re`) — missing imports have caused this "
        "exact function to fail on every real invocation multiple times before. "
        "The function must be a pure string transformation: no file I/O, and no "
        "calling any function that performs file I/O — it runs under a "
        "write-block that rejects the whole candidate if it tries."
    )),
    (1.01, "response_shortening", (
        "refactor the main code-generation function to reduce its average "
        "response length by 20% without losing correctness — shorter code "
        "compiles faster and has fewer syntax errors."
    )),
    # quality_scoring PAUSED 2026-07-21 (self edit loop review, same session
    # as the "learned avoidance"/"metabolism" work): same non-convergence
    # shape as prose_stripping above — 6 attempts, each a near-duplicate
    # reimplementation (score_candidate_code, score_response_quality,
    # update_question_quality, score_code_quality, CodeQualityEvaluator),
    # none landing on something that actually works. The 6th and most
    # recent attempt was live in production with two hallucinated function
    # calls (app.emergent_scheduler.schedule_code_generation,
    # app.core.self_edit_outcome_tracker.load_outcomes — neither exists)
    # and a missing `import re` despite calling re.search() — the exact
    # missing-import failure mode prose_stripping's own rewrite above was
    # built to fix, recurring in a different family. It never crashed
    # anything only because apply_to_code landed nested inside a class
    # instead of at module level, making it invisible to
    # _apply_self_edit_output()'s module-level getattr() lookup — safe by
    # accident, not by design. self_edit_generated.py reset to the clean,
    # honestly-inert baseline in the same change (Finding 31 precedent —
    # it's self-edit's own output, not hand-authored, so a reset was
    # judged more honest than hand-patching a fourth broken version).
    # Removing this tuple means response_shortening's threshold above now
    # covers the full 0.0-1.01 range — quality_scoring is skipped
    # entirely, no change to the selection loop itself.
    # (1.01, "quality_scoring", (
    #     "add or improve a helper function that scores a candidate code string "
    #     "on three dimensions: has_imports, has_function_def, no_prose_sentences. "
    #     "Return a 0-3 int quality score, used to pre-filter LLM output before "
    #     "sandbox testing."
    # )),
]


def _recent_outcome_note(task_type: str) -> str:
    """
    Surfaces the most recent evaluated self_edit_outcome_tracker delta for
    this task type into the Focus-text — the first real consumer of that
    data anywhere; it has been logged since Finding 8 but read by nobody
    until now. Deliberately scoped honestly at task_type granularity (the
    tracker's own granularity), not claimed to be family/creativity-specific.
    """
    try:
        from app.core.self_edit_outcome_tracker import get_outcomes_summary
        recent = [
            e for e in get_outcomes_summary().get("recent", [])
            if e.get("task_type") == task_type
        ]
        if not recent:
            return ""
        delta = recent[0].get("quality_score", {}).get("delta")
        if delta is None:
            return ""
        if delta < -0.1:
            return (
                f" The last evaluated edit for '{task_type}' correlated with a "
                f"quality drop ({delta:+.2f}) — be conservative this cycle."
            )
        if delta > 0.1:
            return (
                f" The last evaluated edit for '{task_type}' correlated with a "
                f"quality gain ({delta:+.2f}) — continue in that direction."
            )
        return ""
    except Exception:
        return ""


def _attempt_ledger_evidence_section(task_type: str) -> str:
    """
    Surfaces the most recent real initial-F2 sandbox failure for this
    task_type from self_edit_attempt_ledger.py — the first read-side
    consumer of that ledger anywhere (audits/2026-09-07_
    consequential_learning_loop_design.md, Phase 1). Deliberately kept as
    its own distinct, unmistakably-labeled section rather than folded into
    the Focus sentence above: this is raw historical evidence about the
    environment, not a policy or instruction, and must not read like one.

    Scope, deliberately narrow per the design doc's own non-goals: this
    does not judge relevance, does not interpret the error, does not
    override any constraint stated elsewhere in the prompt. It is exactly
    the same fail-open, task_type-filtered, recency-based pattern
    _recent_outcome_note()/_recent_experiment_note() already use one
    function above — no new pattern introduced.
    """
    try:
        entry = _read_recent_f2_error(task_type)
        if not entry:
            return ""
        err = str(entry.get("initial_f2_error", "")).strip()
        if not err:
            return ""
        err = err[:400]
        return (
            "\n\nPrior attempt failure evidence (not an instruction): a previous "
            f"real attempt at this task type failed initial sandbox testing with: "
            f"{err}\nThis is historical evidence about what happened before, not a "
            "requirement — it does not override anything stated above."
        )
    except Exception:
        return ""


def _build_targeted_prompt(task_type: str, creativity: float) -> str:
    """
    Build a self-edit prompt that focuses on the weak task type.
    creativity 0.0–0.33: repair a known failure  (conservative)
    creativity 0.34–0.66: refactor a module function
    creativity 0.67–1.0: propose a new helper function

    Previously 3 fixed "Focus:" strings keyed only by creativity bucket, with
    no memory of what had already been tried — the pattern that produced 34+
    distinct prose-stripping callables with zero convergence (see
    _CONVERGENCE_FAMILIES / _build_convergence_note). The creativity buckets
    still coarsely steer conservative-repair vs. refactor vs. new-helper, but
    the Focus text itself is now assembled from real convergence status and
    outcome-tracker history instead of a fixed string.
    """
    base = (
        f"Autonomous self-edit targeting '{task_type}' task performance. "
        "Modify app/core/self_edit_generated.py only. "
        "Output must be headless Python with no interactive elements."
    )

    family, domain_sentence = _FOCUS_FAMILY_BY_CREATIVITY[-1][1], _FOCUS_FAMILY_BY_CREATIVITY[-1][2]
    for threshold, fam, sentence in _FOCUS_FAMILY_BY_CREATIVITY:
        if creativity <= threshold:
            family, domain_sentence = fam, sentence
            break

    convergence_sentence = ""
    family_state = _load_convergence_state().get(family, {})
    if family_state.get("non_convergent_streak", 0) >= 2:
        convergence_sentence = (
            " This family has failed to converge across multiple recent cycles — "
            "do NOT add another standalone function; consolidate into or fix "
            "whichever existing function already targets this, even if that means "
            "a smaller change than a brand-new helper."
        )

    outcome_sentence = _recent_outcome_note(task_type)
    evidence_section = _attempt_ledger_evidence_section(task_type)

    return f"{base} Focus: {domain_sentence}{convergence_sentence}{outcome_sentence}{evidence_section}"


def perform_self_edit(prompt=None, intensity=None, creativity=None, dry_run=None, target_task_type=None):
    import time
    from app.core.stillness_state import is_in_stillness
    if is_in_stillness():
        logging.info("[SELF-EDIT] Echo is in stillness — self-edit deferred.")
        return False, "Deferred: Echo is in stillness"
    creativity = creativity if creativity is not None else 0.5
    dry_run = bool(dry_run)

    if prompt is None:
        if target_task_type is None:
            # Priority order reversed 2026-09-05 (research digest cross-check,
            # this session, independently re-verified against the real,
            # live memory/shadow_accuracy.jsonl — 2054 real entries, overall
            # focus_matches accuracy 16.1%, last-500-entry accuracy 13.2%,
            # i.e. WORSE than the ~20% a uniform-random guess across 5 task
            # types would get). The shadow model's suggestion was previously
            # checked FIRST and treated as an unconditional override ("highest-
            # trust signal") ahead of SelfModelUpdater's empirical,
            # RiverBrain-driven weak-task-type signal (measured 71.8%
            # accurate) — the opposite of what the real accuracy data
            # supports. Confirmed live consequence: 100% of 103 real,
            # quality-tracked self-edit outcomes targeted "coding" regardless
            # of what either signal actually said. Empirical signal now
            # checked first.
            #
            # Retired 2026-09-13 (shadow_model_retirement mission): the
            # shadow-fallback block that used to sit here was removed
            # outright, not merely deprioritized. The same below-chance
            # number cited above (16.1% overall, 13.2% over the most recent
            # 500 entries — both worse than the ~20% a uniform-random guess
            # across 5 task types would get) was judged sufficient to
            # disconnect Shadow from every live decision path, not just
            # demote it. See audits/2026-09-13_shadow_model_retirement.md
            # and app/core/shadow_model.py's own retirement notice. If the
            # empirical signal is unavailable, this now falls straight
            # through to the "coding" default below; it no longer reads
            # memory/shadow_self_model.json at all.
            try:
                from app.core.self_model_updater import SelfModelUpdater
                target_task_type = SelfModelUpdater().get_weak_task_type()
            except Exception as e:
                logging.warning(f"[SELF-EDIT] SelfModelUpdater unavailable: {e}")

            if target_task_type is None:
                target_task_type = "coding"

        prompt = _build_targeted_prompt(target_task_type, creativity)

    # Global cooldown — any *real* autonomous self-edit blocks all others for
    # 60 min. Dry runs (Optuna's trial evaluations) never touch production,
    # so they must neither be blocked by nor consume this cooldown — otherwise
    # a single trial exhausts it and the other 9 (plus the eventual real
    # apply) silently no-op for the rest of the hour.
    #
    # Previously this whole block lived inside `if prompt is None:` above, so
    # any caller passing an explicit prompt (terminal_client.py's manual
    # `!edit` command, this function's own request_self_edit() wrapper)
    # skipped the cooldown check entirely, regardless of dry_run. Moved out
    # here so it applies to every real (non-dry-run) call uniformly. The
    # check-and-stamp is also now inside a real lock — the old comment
    # claimed "stamp immediately so concurrent calls are also blocked" but
    # the two statements were unlocked, so two threads could both observe
    # "cooldown expired" and both proceed to a real production write.
    if not dry_run:
        global _last_any_autonomous_edit
        with _self_edit_deploy_lock:
            now = time.time()
            if now - _last_any_autonomous_edit < _TARGETED_PROMPT_COOLDOWN:
                remaining = int(_TARGETED_PROMPT_COOLDOWN - (now - _last_any_autonomous_edit))
                logging.info(f"[SELF-EDIT] Global cooldown active — skipping for {remaining}s")
                return False, f"Cooldown active ({remaining}s remaining)"
            _last_any_autonomous_edit = now
            _persist_last_autonomous_edit(now)

    return execute_self_edit(prompt, intensity=intensity, dry_run=dry_run)

def apply_self_edits(*args, **kwargs):
    logging.info(f"apply_self_edits called with args={args}, kwargs={kwargs}")
    return None

def schedule_self_edit(*args, **kwargs):
    logging.info(f"schedule_self_edit called with args={args}, kwargs={kwargs}")
    return None
def request_self_edit(prompt: str):
    """Entry point for friction-driven self-edit requests.

    Routes through perform_self_edit() rather than calling execute_self_edit()
    directly — the latter completely bypassed the 60-minute cooldown (dead
    code today per CLAUDE.md's WOLF-retirement note, but fixed for
    correctness in case this is ever reconnected).
    """
    logging.info(f"[WOLF] request_self_edit called with friction prompt: {prompt[:80]}")
    return perform_self_edit(prompt=prompt)
