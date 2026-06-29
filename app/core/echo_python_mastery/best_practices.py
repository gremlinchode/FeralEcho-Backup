# echo_python_mastery/best_practices.py


def teach_best_practices():
    """
    Teach modular design, constants, docstrings, and comments.
    Returns guidance as a string for autonomous consumption.
    """
    return _get_tips()


def _get_tips():
    """
    Returns best practices guidance as a plain string Echo can read and apply.
    """
    return """BEST PRACTICES:
- One function, one purpose. If you can't describe what a function does in one sentence, split it.
- Never embed magic numbers in logic. Define them as named constants at the top of the module.
  BAD:  return price + price * 0.075
  GOOD: TAX_RATE = 0.075
        return price + price * TAX_RATE
- Write docstrings for every module, class, and function. The docstring is what Echo reads to understand a tool.
- Organize imports in three groups separated by blank lines: standard library, third-party, local.
- Keep modules focused. A module that does too many unrelated things is hard to reason about.
- Prefer returning values over side effects. Functions that return strings are easier to test and compose than functions that print.
- Never use bare except. Always catch specific exception types so failures are diagnosable.
- Log at the appropriate level: DEBUG for internal state, INFO for normal events, WARNING for recoverable issues, ERROR for failures.
"""

