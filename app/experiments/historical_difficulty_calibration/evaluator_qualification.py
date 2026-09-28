"""
PHASE 4 -- evaluator qualification for the "extract_code" calibration
family. Runs three fixed, hand-authored candidates (never model-generated)
against real generated instances at every difficulty level, through the
SAME grading path (`sandbox.run_candidate`, reused unmodified from the
sibling minimal_procedure_transfer package) that will later grade real
model responses -- confirming the grader itself discriminates before it is
ever trusted on real model output.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tasks as T  # the LOCAL extract_code family -- bound before the sibling
                    # package's own same-named tasks.py is ever added to sys.path,
                    # to avoid the two same-named modules colliding.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "minimal_procedure_transfer"))
import sandbox as SB  # reused, unmodified, from minimal_procedure_transfer

POSITIVE_CONTROL = textwrap.dedent('''
```python
import ast

def solve(text: str) -> str:
    lines = text.split("\\n")
    n = len(lines)
    for start in range(n):
        if lines[start].strip() == "":
            continue
        for end in range(n, start, -1):
            candidate_lines = lines[start:end]
            while candidate_lines and candidate_lines[-1].strip() == "":
                candidate_lines = candidate_lines[:-1]
            if not candidate_lines:
                continue
            candidate = "\\n".join(candidate_lines)
            try:
                tree = ast.parse(candidate)
            except SyntaxError:
                continue
            if not tree.body:
                continue
            return candidate
    return text
```
''')

NEGATIVE_CONTROL = textwrap.dedent('''
```python
def solve(text: str) -> str:
    return text
```
''')

NEAR_MISS_CONTROL = textwrap.dedent('''
```python
def solve(text: str) -> str:
    lines = text.split("\\n")
    for i, line in enumerate(lines):
        if "def" in line or "class" in line or "import" in line or line.strip().startswith("@"):
            return "\\n".join(lines[i:])
    return text
```
''')


def run_control(label: str, code_block: str) -> None:
    code = SB.extract_code(code_block)
    for level in (1, 2, 3, 4):
        insts = T.build_calibration_set([700, 701, 702, 703, 704], level, "qual_")
        hidden = [{"input": i["text"], "expected": i["expected_code"]} for i in insts]
        n_pass = 0
        for h in hidden:
            grade = SB.run_candidate(code, [h])
            n_pass += 1 if grade["passed"] else 0
        print(f"{label} @ level {level}: {n_pass}/{len(hidden)} pass")


if __name__ == "__main__":
    print("=== POSITIVE CONTROL (should pass at every level) ===")
    run_control("positive", POSITIVE_CONTROL)
    print("\n=== NEGATIVE CONTROL (should fail at every level) ===")
    run_control("negative", NEGATIVE_CONTROL)
    print("\n=== NEAR-MISS CONTROL (naive substring heuristic -- should pass level 1, "
          "fail once a 'def'/'class'/'import' substring appears inside ordinary prose, "
          "and fail level 4's trailing-prose requirement) ===")
    run_control("near_miss", NEAR_MISS_CONTROL)
