"""Fixed strategy menu -- three prompt-framing strategies for the identical
underlying coding task, per PREREG_ADDENDUM.md 'Blocker 1'. Each strategy is
a pure function (task dict, procedure_text) -> prompt string; no model call,
no state, directly unit-testable. The real convention/procedure text is
supplied identically to every strategy -- this experiment tests routing
among PROMPTING STYLES for a task whose solving information is already
given, deliberately decoupled from AP-0's own, separately (and negatively)
resolved induction question."""
from __future__ import annotations

_WORKED_EXAMPLE = (
    "Worked example (illustrative only, unrelated to the real task below):\n"
    "Task: write a function that returns the larger of two numbers.\n"
    "```python\n"
    "def bigger(a, b):\n"
    "    return a if a > b else b\n"
    "```\n\n"
)


def _base(task: dict, procedure_text: str) -> str:
    return (
        f"Context: {task['spec']}\n\n"
        f"Site-specific rule for this task: {procedure_text}\n\n"
        f"Write `{task['sig']}` implementing the above.\n"
    )


def direct(task: dict, procedure_text: str) -> str:
    return _base(task, procedure_text) + "Respond with only the function in a ```python block."


def stepwise(task: dict, procedure_text: str) -> str:
    return (
        _base(task, procedure_text)
        + "First restate the requirement as a short numbered list of exactly what the "
          "function must do, then write the function. Respond with the numbered list "
          "followed by the function in a ```python block."
    )


def worked_example(task: dict, procedure_text: str) -> str:
    return _WORKED_EXAMPLE + _base(task, procedure_text) + "Respond with only the function in a ```python block."


STRATEGY_FNS = {
    "DIRECT": direct,
    "STEPWISE": stepwise,
    "WORKED_EXAMPLE": worked_example,
}


def build_prompt(strategy: str, task: dict, procedure_text: str) -> str:
    return STRATEGY_FNS[strategy](task, procedure_text)
