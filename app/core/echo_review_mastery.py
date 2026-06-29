# app/core/echo_review_mastery.py
# v2.0 — Calls get_tips() on each mastery module to collect actual guidance content,
# not just docstrings. Echo now reads real tips before every self-edit cycle.

import importlib
import inspect
import pkgutil
import logging
import app.core.echo_python_mastery as mastery_pkg


def review_mastery():
    """
    Collects guidance from all modules in echo_python_mastery.
    For each module, calls get_tips() if available to get full content.
    Falls back to docstring if get_tips() is not defined.
    Returns a dict mapping module_name -> content string.
    """
    mastery_summary = {}

    for _, module_name, _ in pkgutil.iter_modules(mastery_pkg.__path__):
        full_module_name = f"{mastery_pkg.__name__}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
            importlib.reload(module)

            # Prefer get_tips() — returns full actionable content
            if hasattr(module, "get_tips") and callable(module.get_tips):
                try:
                    content = module.get_tips()
                    mastery_summary[module_name] = content
                except Exception as e:
                    logging.warning(
                        f"[MasteryReview] get_tips() failed for {module_name}: {e}. "
                        f"Falling back to docstrings."
                    )
                    mastery_summary[module_name] = _collect_docstrings(module)
            else:
                # Fall back to docstring collection for modules without get_tips()
                mastery_summary[module_name] = _collect_docstrings(module)

        except Exception as e:
            logging.error(f"[MasteryReview] Failed to load module {module_name}: {e}")
            mastery_summary[module_name] = f"[ERROR] Could not load module: {e}"

    return mastery_summary


def _collect_docstrings(module):
    """
    Fallback: collect function docstrings from a module.
    Used when get_tips() is not available.
    """
    lines = []
    for name, func in inspect.getmembers(module, inspect.isfunction):
        doc = inspect.getdoc(func) or "No docstring."
        lines.append(f"  {name}: {doc}")
    return "\n".join(lines) if lines else "No functions found."


def advise_before_edit():
    """
    Returns a plain-text advisory summary Echo reads before every self-edit.
    Now contains full guidance content from each mastery module,
    not just function names and docstrings.
    """
    mastery = review_mastery()

    sections = ["Echo Mastery Guidance — Pre-Edit Review\n" + "=" * 42 + "\n"]

    for module_name, content in mastery.items():
        sections.append(f"[ {module_name.upper()} ]\n{content}\n")

    return "\n".join(sections)
