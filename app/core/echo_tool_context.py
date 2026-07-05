# app/core/echo_tool_context.py
# ============================================================
# PRE-EXECUTION TOOL CONTEXT — Option A injection pattern
# ============================================================
# Detects tool-eligible prompts, executes the tool in Python
# before generation, and returns a labeled result block for
# injection into the prompt — same pattern as echo_ground_truth.py.
#
# No ReAct loop. No new dependencies. No model-side parsing.
# The model receives real data and generates a response from it.
#
# Current tools:
#   list_directory — read-only, path-guarded to FeralEcho root
#
# Expanding: add a new _build_<tool>() and wire it into
# get_tool_context(). Add detection signals to the relevant
# _SIGNALS set. Never remove the path guard.
# ============================================================

import os
import re
import logging

logger = logging.getLogger(__name__)

# Path-structured traversal patterns — match paths, not words.
# ../  or  /..  — relative traversal components
_RELATIVE_TRAVERSAL_RE = re.compile(r'\.\.[/\\]|[/\\]\.\.')
# /etc/  /users/  etc. — absolute paths to system directories
# Requires a space/quote/paren before the slash so bare words like "root" or
# "home" in English prose never match.  Word-end anchor handles trailing cases.
_ABSOLUTE_SYS_PATH_RE = re.compile(
    r'(?:^|[\s\'"`(])'
    r'/(?:etc|usr|var|home|root|tmp|sys|proc|dev|users|private)'
    r'(?:/|[\s\'"`)]|$)',
    re.IGNORECASE,
)

def _find_project_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isfile(os.path.join(here, "run.py")):
            return os.path.realpath(here)
        here = os.path.dirname(here)
    return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

_PROJECT_ROOT = _find_project_root()

# ---------------------------------------------------------------------------
# Detection signals
# ---------------------------------------------------------------------------

_LISTING_SIGNALS = frozenset([
    "list files", "list the files", "what files", "which files",
    "what's in", "what is in", "whats in",
    "show me", "show files", "show the files",
    "what's inside", "what is inside",
    "contents of", "content of",
    "directory listing", "folder listing",
    "browse", "explore the",
    "review the folder", "review the directory",
    "look at the folder", "look at the files",
    "what does", "what do the files",
    "files in", "files at", "files under",
    "folder", "directory",
])

# Signals that the user wants a specific subdirectory named in the prompt.
# Used by _extract_target_path to find a path token.
_KNOWN_SUBDIRS = [
    "app/core", "app/lib", "app/sync", "app/tools",
    "app/core/echo_python_mastery", "app/core/self_edit_backups",
    "app/internet_tools", "app/maintenance", "app/subsystems",
    "app", "memory", "data", "sandbox", "books",
    "archive_janitor", "staging",
]

_PATH_TOKEN_RE = re.compile(
    r"(?:^|[\s'\"`(])("
    r"(?:app|memory|data|sandbox|archive_janitor|books|staging)"
    r"(?:/[^\s'\"`),;?!]*)*"
    r")",
    re.IGNORECASE,
)


def _needs_tool_context(prompt: str) -> bool:
    low = prompt.lower()
    return any(sig in low for sig in _LISTING_SIGNALS)


# ---------------------------------------------------------------------------
# Path extraction
# ---------------------------------------------------------------------------

def _extract_target_path(prompt: str) -> tuple[str, bool]:
    """
    Try to find a relative path in the prompt that resolves to a real
    directory inside the project root.

    Returns (rel_path, traversal_attempted).
    - rel_path: safe path to list, or "" for project root
    - traversal_attempted: True if any path candidate showed signs of
      traversal — checked on extracted candidates and recognizable
      path-structured patterns only, NOT on free-text substrings like
      the words "root" or "home" in normal prose.
    """
    traversal_attempted = False

    # 1. Explicit path token matched by regex (e.g. "app/core", "memory/")
    for m in _PATH_TOKEN_RE.finditer(prompt):
        candidate = m.group(1).rstrip("/.,;)")
        # Check for relative traversal inside the candidate itself
        if ".." in candidate:
            traversal_attempted = True
            continue
        full = os.path.realpath(os.path.join(_PROJECT_ROOT, candidate))
        if not full.startswith(_PROJECT_ROOT):
            # realpath resolved outside root — traversal via symlink or odd path
            traversal_attempted = True
            continue
        if os.path.isdir(full):
            return candidate, False  # valid, safe, use it

    # 2. Detect path-structured traversal patterns in the raw prompt.
    #    These regexes look for traversal syntax (../ or /etc/), NOT bare words.
    if _RELATIVE_TRAVERSAL_RE.search(prompt):
        traversal_attempted = True
    if _ABSOLUTE_SYS_PATH_RE.search(prompt):
        traversal_attempted = True

    if traversal_attempted:
        return "", True  # don't fall through to root listing

    # 3. Known subdir named anywhere in the prompt (longest match first)
    low = prompt.lower()
    for subdir in _KNOWN_SUBDIRS:
        if subdir in low:
            full = os.path.join(_PROJECT_ROOT, subdir)
            if os.path.isdir(full):
                return subdir, False

    return "", False  # no specific subdir — list project root


# ---------------------------------------------------------------------------
# Directory listing — path-guarded
# ---------------------------------------------------------------------------

_MAX_ENTRIES = 60


def _safe_listdir(rel_path: str) -> tuple[str, list[str], list[str], str]:
    """
    List a directory inside _PROJECT_ROOT.
    Returns (resolved_rel, dirs, files, error_or_empty).
    Never escapes the project root.
    """
    target = os.path.realpath(
        os.path.join(_PROJECT_ROOT, rel_path) if rel_path else _PROJECT_ROOT
    )

    if not target.startswith(_PROJECT_ROOT):
        return rel_path, [], [], "path would escape project root — refused"

    if not os.path.isdir(target):
        return rel_path, [], [], f"not a directory: {rel_path or '.'}"

    try:
        raw = sorted(os.listdir(target))
    except PermissionError:
        return rel_path, [], [], "permission denied"

    dirs, files = [], []
    for name in raw:
        if os.path.isdir(os.path.join(target, name)):
            dirs.append(name + "/")
        else:
            files.append(name)

    # Relative label for the header
    rel_label = os.path.relpath(target, _PROJECT_ROOT)
    if rel_label == ".":
        rel_label = "(project root)"

    return rel_label, dirs[:_MAX_ENTRIES], files[:_MAX_ENTRIES], ""


# ---------------------------------------------------------------------------
# Block builder
# ---------------------------------------------------------------------------

def _build_listing(prompt: str) -> str:
    rel_path, traversal = _extract_target_path(prompt)

    if traversal:
        return "[Tool: list_directory — refused: path traversal attempt detected]"

    rel_label, dirs, files, err = _safe_listdir(rel_path)

    if err:
        return f"[Tool: list_directory — error: {err}]"

    total = len(dirs) + len(files)
    truncated = total >= _MAX_ENTRIES

    lines = [
        f"[Tool result — directory listing read from disk at query time]",
        f"Path: {rel_label}  ({total}{'+ ' if truncated else ' '}items{', truncated at ' + str(_MAX_ENTRIES) if truncated else ''})",
    ]
    if dirs:
        lines.append("Subdirectories: " + "  ".join(dirs))
    if files:
        # Wrap file list at 80 chars for readability
        file_str = "  ".join(files)
        lines.append("Files: " + file_str)
    if not dirs and not files:
        lines.append("(empty directory)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_tool_context(prompt: str) -> str:
    """
    Return a pre-executed tool result block for injection into the prompt,
    or "" if no tool applies or execution fails.
    """
    try:
        if _needs_tool_context(prompt):
            result = _build_listing(prompt)
            if result:
                return result
    except Exception as e:
        logger.warning("[ToolContext] %s", e)
    return ""
