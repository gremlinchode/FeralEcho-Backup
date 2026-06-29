# echo_python_mastery/debugging.py
import logging


def teach_debugging():
    """
    Teach try/except, logging, and reading tracebacks.
    Returns guidance as a string for autonomous consumption.
    """
    return _get_tips()


def _get_tips():
    """
    Returns debugging guidance as a plain string Echo can read and apply.
    """
    return """DEBUGGING:
- Wrap risky operations in try/except. Never let an unhandled exception silently kill a thread.
- Use specific exception types. 'except Exception as e' is acceptable. Bare 'except:' is not.
- Always log the full traceback for unexpected errors: logging.error("msg", exc_info=True)
- Use logging instead of print. Print output is lost in headless execution. Log output persists.
- Read tracebacks bottom-up. The last line is the actual error. Lines above show the call chain.
- Validate inputs at the top of functions before any processing begins. Fail fast with a clear message.
- When a sandbox execution fails with SyntaxError, the line number in the traceback is the exact location. Read it.
- Use try/except/finally for resource cleanup: file handles, subprocess calls, network connections.
- After catching an error, decide: can Echo recover autonomously, or should it log and skip this cycle?

PATTERN — correct exception handling for autonomous systems:
  try:
      result = risky_operation()
  except ValueError as e:
      logging.warning(f"[MODULE] Invalid value: {e}")
      result = fallback_value
  except Exception as e:
      logging.error(f"[MODULE] Unexpected failure: {e}", exc_info=True)
      result = None
"""

