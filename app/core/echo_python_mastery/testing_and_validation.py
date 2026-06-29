# echo_python_mastery/testing_and_validation.py


def teach_testing():
    """
    Teach unit testing, assertions, and input validation.
    Returns guidance as a string for autonomous consumption.
    """
    return _get_tips()


def _get_tips():
    """
    Returns testing and validation guidance as a plain string Echo can read and apply.
    Focused on patterns relevant to autonomous, headless execution.
    """
    return """TESTING AND VALIDATION:
- Validate inputs at the start of every function. Reject bad input early with a clear log message.
- Use assert statements to enforce invariants during development, but wrap them in try/except in production.
- Write functions that are testable: they take inputs, return outputs, and have no hidden side effects.
- Test edge cases: empty input, None, zero, very large values, malformed data.
- For self-generated code, always run ast.parse before saving. A SyntaxError means the code is rejected.
- After applying a self-edit, verify the module loads cleanly with importlib before marking success.
- Use logging to record what was tested and what the result was. This creates an audit trail.

PATTERN — input validation at function entry:
    def process(items):
        if items is None:
            logging.warning("[process] Received None input. Skipping.")
            return []
        if not isinstance(items, list):
            logging.error(f"[process] Expected list, got {type(items).__name__}.")
            return []
        if len(items) == 0:
            logging.info("[process] Empty list received. Nothing to process.")
            return []
        # safe to proceed
        return [item for item in items if item is not None]

PATTERN — verify a generated module loads before committing:
    def safe_load_module(path):
        import importlib.util
        try:
            spec = importlib.util.spec_from_file_location("candidate", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return True, mod
        except Exception as e:
            logging.error(f"[safe_load_module] Failed to load {path}: {e}")
            return False, None
"""

