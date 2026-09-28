"""
The qualified, corrected `extract_code` Level-3 prompt, extended with
exactly one new, optional, empty-by-default `context` parameter, per
CONTRACT.md. With context="", this MUST produce byte-identical output to
the original qualified build_prompt(task) in
historical_difficulty_calibration/run_calibration.py -- verified directly
in this module's own self-check, not merely asserted.
"""
from __future__ import annotations

_EXAMPLE_TEXT = "Sure, here's what I came up with!\n\ndef add(a, b):\n    return a + b"
_EXAMPLE_OUTPUT = "def add(a, b):\n    return a + b"


def build_prompt(task: dict, context: str = "") -> str:
    return (
        f"Task:\n{task['description']}\n\n"
        f"You must write a general-purpose function with this exact signature:\n"
        f"def solve(text: str) -> str\n\n"
        f"`solve` will be called by an automated test harness on DIFFERENT input "
        f"strings it has never seen before -- it must work by actually inspecting "
        f"its `text` argument at runtime (for example, by parsing or searching it), "
        f"not by returning a fixed value copied from any example.\n\n"
        f"Example (illustrative only, not one of the real graded inputs):\n"
        f"If `text` were exactly:\n"
        f"-----BEGIN EXAMPLE INPUT-----\n{_EXAMPLE_TEXT}\n-----END EXAMPLE INPUT-----\n"
        f"then solve(text) should return exactly:\n"
        f"-----BEGIN EXAMPLE OUTPUT-----\n{_EXAMPLE_OUTPUT}\n-----END EXAMPLE OUTPUT-----\n\n"
        f"Now here is the REAL input string that `solve` will actually be tested "
        f"on for this task (between the markers below -- it is not the example "
        f"above):\n"
        f"-----BEGIN REAL INPUT-----\n{task['text']}\n-----END REAL INPUT-----\n\n"
        f"{context}"
        f"Write the function `solve` now. Respond with only the function "
        f"definition in a fenced Python code block."
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "historical_difficulty_calibration"))
    import tasks as T
    import run_calibration as RC

    sample = T.build_calibration_set([1], 3, "selfcheck_")[0]
    original = RC.build_prompt(sample)
    extended_empty = build_prompt(sample, context="")
    assert original == extended_empty, (
        "context='' must reproduce the original qualified prompt byte-for-byte -- "
        f"lengths were {len(original)} vs {len(extended_empty)}"
    )
    extended_with_context = build_prompt(sample, context="Some treatment text.\n")
    assert extended_with_context != original
    assert "Some treatment text." in extended_with_context
    print("prompt.py self-check: OK (context='' byte-identical to the qualified "
          "prompt; non-empty context is correctly inserted)")
