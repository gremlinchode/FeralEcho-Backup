# echo_python_mastery/coding_basics.py


def teach_basics():
    """
    Teach PEP8, naming, readability, and clean code structure.
    Returns guidance as a string for autonomous consumption.
    """
    return _get_tips()


def _get_tips():
    """
    Returns coding basics guidance as a plain string Echo can read and apply.
    """
    return """CODING BASICS:
- Use underscores for multi-word variable and function names: check_folder_health, not checkFolderHealth.
- Follow PEP8: 4-space indentation, max 79 characters per line, no trailing whitespace.
- Choose meaningful variable names. Avoid single letters except in short loops (i, j, k).
- Keep functions short and focused. If a function exceeds ~50 lines, split it into helpers.
- Use comments to explain WHY a decision was made, not WHAT the code does. The code shows what; comments explain intent.
- Group related logic together. Unrelated logic belongs in a separate function.
- Avoid deeply nested code. Flatten with early returns or helper functions.
- Constants belong at the module level in ALL_CAPS. Never embed magic numbers in logic.
"""

