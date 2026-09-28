#!/usr/bin/env python3
"""
PHASE 8 -- the G (generic-tip counterfeit) treatment. Hand-authored,
generic, useful programming advice, deliberately NOT containing any of the
three specific, experience-derived clauses in procedure_frozen.json (no
mention of the four-category keyword list, no mention of line-start
anchoring vs. anywhere-in-text matching, no mention of the single-regex
truncation risk). Length approximately matched to P's 1381 characters.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "historical_difficulty_calibration"))
import tasks as T

OUT_DIR = Path(__file__).resolve().parents[3] / "memory" / "experiments" / "validated_experience_competence_transfer"

GENERIC_TIP_TEXT = (
    "General tips for writing solve():\n"
    "1. Read the task description carefully before writing any code, and "
    "make sure you understand exactly what the function is supposed to "
    "return.\n"
    "2. Consider edge cases, such as unusually short input, input with "
    "extra whitespace, or input formatted slightly differently than the "
    "example.\n"
    "3. Make sure your solution genuinely inspects the real `text` "
    "argument at runtime rather than assuming a fixed structure or "
    "returning something copied from the illustrative example.\n"
    "4. Prefer simple, robust code over a clever one-liner -- a solution "
    "that is easy to reason about is less likely to contain a subtle bug.\n"
    "5. Before finalizing your answer, mentally trace through what your "
    "function would actually do on the given input, step by step, and "
    "double-check the result looks right.\n"
    "6. Double-check that your function handles the input exactly as "
    "described, without adding extra assumptions the task did not state.\n"
    "7. Give your function a clear, direct implementation rather than an "
    "overly clever one, and make sure the return value's type and format "
    "match what was asked for.\n"
    "8. Aim for a solution you would be confident applying to many "
    "different inputs of the same general kind, not just the one shown "
    "here.\n"
)


def main():
    if (OUT_DIR / "generic_tip_treatment.json").exists():
        print("generic_tip_treatment.json already exists -- refusing to overwrite.")
        return
    payload = {
        "context_text": "\n" + GENERIC_TIP_TEXT,
        "note": "Fixed, hand-authored, generic. Contains no experience-derived, "
                "task-family-specific content from any TRAIN episode.",
        "frozen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(OUT_DIR / "generic_tip_treatment.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Generic-tip treatment written. Length: {len(GENERIC_TIP_TEXT)} chars "
          f"(P's procedure text is 1381 chars).")


if __name__ == "__main__":
    main()
