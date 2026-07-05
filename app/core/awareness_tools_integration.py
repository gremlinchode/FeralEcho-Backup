# app/core/awareness_tools_integration.py
"""
Echo's ambient tool discovery and registration engine.

Three registration pathways:
  1. discover_and_register_tools()   — scans local project .py files for callable functions
  2. register_package_functions()    — registers top-level callables from a named package
  3. discover_installed_packages()   — iterates SAFE_TOOL_PACKAGES and calls (2) for each

Design principles:
  - Only real callables are ever registered; AST nodes are used for scanning only
  - Deduplication via content hash prevents re-registering identical functions
  - Hard cap per package prevents memory blowout from large libraries
  - Directories that should never be touched are explicitly skipped
  - Failures are logged at debug level; nothing crashes Echo
"""

import os
import ast
import logging
import inspect
import hashlib
import importlib
import importlib.util
from typing import Optional, Callable

from app.core.tool_manager import Tool, ToolManager
from app.core.memory_bridge import log_dream_bridge

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared ToolManager instance
# ---------------------------------------------------------------------------
tm = ToolManager()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Directories to never descend into during local file scanning.
SKIP_DIRS = {
    "self_edit_backups",
    "sandbox",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "migrations",
}

# Packages whose top-level callables are safe to expose to Echo.
# Extend this list deliberately; do not wildcard installed packages.
SAFE_TOOL_PACKAGES = [
    # Probabilistic / active-inference
    "pymdp",
    # Computational neuroscience / spiking networks
    "brian2",
    # Nengo neural simulation
    "nengo",
    # Online / streaming ML  (river replaces scikit-multiflow)
    "river",
    # Continual learning
    "avalanche",
    # Numerical / scientific core
    "numpy",
    "scipy",
    # Plotting (Echo can describe figures even without a display)
    "matplotlib",
]

# Maximum callables registered per package; guards against oversized __all__
MAX_TOOLS_PER_PACKAGE = 30

# This file's own basename — never scan ourselves
_THIS_FILE = os.path.basename(__file__)

# ---------------------------------------------------------------------------
# Deduplication registry  {content_hash: tool_name}
# ---------------------------------------------------------------------------
_registered_hashes: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _content_hash(func: Callable) -> Optional[str]:
    """
    Returns a stable SHA-1 of a function's source code, or None if source
    is unavailable (built-ins, C extensions, etc.).
    """
    try:
        src = inspect.getsource(func)
        return hashlib.sha1(src.encode()).hexdigest()
    except (OSError, TypeError):
        return None


def _extract_description(func: Callable, fallback: str = "") -> str:
    """
    Returns a concise description string for ToolManager registration.
    Prefers the function's own docstring; falls back to the provided string.
    Truncated to 300 chars so descriptions stay LLM-friendly.
    """
    try:
        doc = inspect.getdoc(func)
        if doc:
            return doc[:300]
    except Exception:
        pass
    return fallback or "Dynamically discovered tool."


def safe_wrapper(func: Callable, func_name: str) -> Callable:
    """
    Wraps a callable so exceptions are caught, logged, and returned as None
    rather than propagating up and crashing Echo's event loop.
    """
    def wrapped(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # Success path: log at debug level only — every tool invocation was
            # previously writing to dream_bridge (a FAISS embed+write per call).
            logger.debug("[ToolManager] '%s' called args=%r kwargs=%r", func_name, args, kwargs)
            return result
        except Exception as exc:
            log_dream_bridge(f"[ToolManager] Error in '{func_name}': {exc}")
            logger.debug(f"Tool '{func_name}' raised: {exc}", exc_info=True)
            return None
    wrapped.__name__ = func_name
    return wrapped


def _load_function_from_file(file_path: str, func_name: str) -> Optional[Callable]:
    """
    Dynamically imports a single function from an arbitrary .py file.
    Returns None (and logs) on any failure rather than raising.
    """
    try:
        spec = importlib.util.spec_from_file_location("_echo_dynamic_module", file_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        attr = getattr(module, func_name, None)
        if callable(attr):
            return attr
        logger.debug(f"'{func_name}' in {file_path} is not callable after import.")
        return None
    except Exception as exc:
        logger.debug(f"Could not load '{func_name}' from {file_path}: {exc}")
        return None


def _try_register(
    name: str,
    func: Callable,
    description: str,
    source_label: str,
) -> bool:
    """
    Registers a tool with deduplication.  Returns True if registered,
    False if skipped (duplicate or already known by name).
    """
    # Name-based dedup: skip if this tool name is already known
    if name in tm.list_tools():
        return False

    # Content-hash dedup: skip if identical source was already registered
    h = _content_hash(func)
    if h and h in _registered_hashes:
        logger.debug(
            f"Skipping '{name}' — identical source already registered "
            f"as '{_registered_hashes[h]}'"
        )
        return False

    try:
        tm.register_tool(Tool(
            name=name,
            func=safe_wrapper(func, name),
            description=description,
        ))
        if h:
            _registered_hashes[h] = name
        logger.debug("[AwarenessIntegration] Registered '%s' (%s)", name, source_label)
        return True
    except Exception as exc:
        logger.debug(f"Registration failed for '{name}': {exc}")
        return False


# ---------------------------------------------------------------------------
# Primary discovery pathways
# ---------------------------------------------------------------------------

def discover_and_register_tools(path: str = ".") -> int:
    """
    Walks the local project tree, parses each .py file for top-level function
    definitions, dynamically loads the real callable, and registers it.

    Returns the count of newly registered tools.
    """
    registered = 0

    for root, dirs, files in os.walk(path, topdown=True):
        # Prune skip directories in-place so os.walk won't descend into them
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file in files:
            if not file.endswith(".py") or file == _THIS_FILE:
                continue

            full_path = os.path.join(root, file)

            try:
                with open(full_path, "r", encoding="utf-8") as fh:
                    source = fh.read()
                tree = ast.parse(source, filename=full_path)
            except Exception as exc:
                logger.debug(f"Could not parse {full_path}: {exc}")
                continue

            # Collect only top-level (module-scope) function names
            top_level_funcs = [
                node.name
                for node in ast.iter_child_nodes(tree)
                if isinstance(node, ast.FunctionDef)
                and not node.name.startswith("_")
                and node.name != "wrapped"
            ]

            for func_name in top_level_funcs:
                real_func = _load_function_from_file(full_path, func_name)
                if real_func is None:
                    continue

                desc = _extract_description(
                    real_func,
                    fallback=f"Project utility from {file}.",
                )
                if _try_register(func_name, real_func, desc, source_label=file):
                    registered += 1

    logger.info("[AwarenessIntegration] Local scan complete — %d new tools registered.", registered)
    return registered


def register_package_functions(package_name: str) -> int:
    """
    Imports a package and registers its top-level non-class callables as tools.
    Skips classes, private names, and anything beyond MAX_TOOLS_PER_PACKAGE.

    Returns the count of newly registered tools.
    """
    try:
        package = importlib.import_module(package_name)
    except Exception as exc:
        log_dream_bridge(
            f"[AwarenessIntegration] Cannot import '{package_name}': {exc}"
        )
        logger.debug(f"Skipping package '{package_name}': {exc}")
        return 0

    names = (
        list(package.__all__)
        if hasattr(package, "__all__")
        else [n for n in dir(package) if not n.startswith("_")]
    )

    registered = 0
    for name in names:
        if registered >= MAX_TOOLS_PER_PACKAGE:
            logger.debug("[AwarenessIntegration] Cap reached for '%s' (%d tools).",
                         package_name, MAX_TOOLS_PER_PACKAGE)
            break

        try:
            attr = getattr(package, name)
        except Exception:
            continue

        # Only plain callables — skip classes and non-callables
        if not callable(attr) or inspect.isclass(attr):
            continue

        tool_name = f"{package_name}.{name}"
        desc = _extract_description(
            attr,
            fallback=f"Function '{name}' from package '{package_name}'.",
        )
        if _try_register(tool_name, attr, desc, source_label=package_name):
            registered += 1

    # Register an introspection tool so Echo can query what's available
    intro_name = f"{package_name}.__functions__"
    if intro_name not in tm.list_tools():
        snapshot = [
            t for t in tm.list_tools() if t.startswith(f"{package_name}.")
        ]
        def _list_functions(snap=snapshot):
            return snap
        _try_register(
            intro_name,
            _list_functions,
            f"List all registered callables from '{package_name}'.",
            source_label="introspection",
        )

    logger.info("[AwarenessIntegration] Package '%s' — %d new tools registered.",
                package_name, registered)
    return registered


def discover_installed_packages() -> int:
    """
    Iterates SAFE_TOOL_PACKAGES and registers each via register_package_functions().
    Only whitelisted packages are ever touched.

    Returns the total count of newly registered tools.
    """
    total = 0
    for package_name in SAFE_TOOL_PACKAGES:
        # Quick pre-check: if ANY tool from this package is already registered, skip
        if any(t.startswith(f"{package_name}.") for t in tm.list_tools()):
            logger.debug(f"Package '{package_name}' already has registered tools — skipping.")
            continue
        total += register_package_functions(package_name)

    logger.info("[AwarenessIntegration] Package discovery complete — %d new tools registered.", total)
    return total


# ---------------------------------------------------------------------------
# Convenience: run all three pathways in order
# ---------------------------------------------------------------------------

def bootstrap_all(project_root: str = ".") -> dict:
    """
    Convenience entry point that runs all three discovery pathways and returns
    a summary dict suitable for logging or Echo's self-model.
    """
    local_count   = discover_and_register_tools(project_root)
    package_count = discover_installed_packages()
    total         = len(tm.list_tools())

    summary = {
        "local_tools_registered":   local_count,
        "package_tools_registered": package_count,
        "total_tools_available":    total,
    }
    log_dream_bridge(f"[AwarenessIntegration] Bootstrap complete: {summary}")
    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = bootstrap_all()
    print(f"Bootstrap complete: {result}")
