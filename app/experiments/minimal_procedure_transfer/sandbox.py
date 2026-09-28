"""
Minimal, standalone execution-based checker for this experiment ("F2" for
the purposes of this pilot). Deliberately NOT FeralEcho's own production F2
(sandbox/echo_sandbox.sb + safe_exec_wrapper.py) or the frozen persistent-
competence protocol's own Seatbelt-based oracle -- per this experiment's
explicit safety instructions, this harness imports nothing from app.* or
sandbox.* and starts no FeralEcho process of any kind.

Honesty about what this IS and is NOT, stated here rather than only in the
report: this is a real, deterministic, execution-based correctness check
(the candidate's own `solve()` function is actually run against real
hidden test inputs and its real output is compared to a pre-computed
reference value) -- genuinely independent of any LLM's own claims about its
own code, which is the property this experiment's own evaluator needs. It
is NOT a security-hardened sandbox: it runs the candidate code in a fresh
OS subprocess with a short wall-clock timeout, a fresh temp working
directory, and a stripped environment, but it does not attempt kernel-level
(Seatbelt) filesystem/network denial the way FeralEcho's real production
F2 does. This is judged an acceptable, disclosed limitation for this
specific pilot: the candidate code is a single small, non-adversarial
function written by a local, non-agentic model attempting a simple
algorithmic task, not an untrusted third party's submission.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import time

_TIMEOUT_S = 10
_CODE_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)

_RUNNER_TEMPLATE = """
import json, sys
sys.path.insert(0, {scratch_dir!r})
import candidate

with open({inputs_path!r}) as f:
    hidden_tests = json.load(f)

results = []
for t in hidden_tests:
    try:
        out = candidate.solve(t["input"])
        results.append({{"ok": True, "output": out}})
    except Exception as e:
        results.append({{"ok": False, "error": f"{{type(e).__name__}}: {{e}}"}})

with open({outputs_path!r}, "w") as f:
    json.dump(results, f)
"""


def extract_code(raw_response: str) -> "str | None":
    """Last closed fenced code block in the response, mirroring the frozen
    protocol's own [INF-6] convention. Returns None (malformed) if no
    fenced block is present."""
    matches = _CODE_FENCE_RE.findall(raw_response)
    if not matches:
        return None
    return matches[-1].strip()


def run_candidate(code: str, hidden_tests: "list[dict]") -> dict:
    """Runs `code` (must define a top-level `solve` function) against every
    hidden test's real input, in a fresh subprocess with a fresh scratch
    directory, and compares each real output to the pre-computed expected
    value. Returns a dict with per-test pass/fail and an overall `passed`
    bool (True iff every hidden test passes and the process didn't crash/
    time out). Never raises -- any failure (syntax error, timeout, crash)
    is recorded as a failed run, not an exception propagated to the
    caller."""
    if code is None:
        return {"passed": False, "category": "malformed_no_code_block", "per_test": []}

    with tempfile.TemporaryDirectory(prefix="mpt_sandbox_") as scratch:
        candidate_path = os.path.join(scratch, "candidate.py")
        inputs_path = os.path.join(scratch, "inputs.json")
        outputs_path = os.path.join(scratch, "outputs.json")
        runner_path = os.path.join(scratch, "runner.py")

        try:
            with open(candidate_path, "w") as f:
                f.write(code)
        except Exception as e:
            return {"passed": False, "category": f"write_failed: {e}", "per_test": []}

        with open(inputs_path, "w") as f:
            json.dump([{"input": t["input"]} for t in hidden_tests], f)

        with open(runner_path, "w") as f:
            f.write(
                _RUNNER_TEMPLATE.format(
                    scratch_dir=scratch, inputs_path=inputs_path, outputs_path=outputs_path
                )
            )

        env = {
            "PATH": "/usr/bin:/bin",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
        }
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-B", runner_path],
                cwd=scratch,
                env=env,
                timeout=_TIMEOUT_S,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            return {"passed": False, "category": "timeout", "per_test": []}
        except Exception as e:
            return {"passed": False, "category": f"subprocess_launch_failed: {e}", "per_test": []}

        if proc.returncode != 0:
            return {
                "passed": False,
                "category": "runtime_error",
                "stderr_tail": proc.stderr[-800:],
                "per_test": [],
            }

        try:
            with open(outputs_path) as f:
                results = json.load(f)
        except Exception as e:
            return {
                "passed": False,
                "category": f"no_output_produced: {e}",
                "stderr_tail": proc.stderr[-800:],
                "per_test": [],
            }

        per_test = []
        all_pass = True
        for t, r in zip(hidden_tests, results):
            ok = bool(r.get("ok")) and r.get("output") == t["expected"]
            per_test.append({
                "input": t["input"],
                "expected": t["expected"],
                "got": r.get("output") if r.get("ok") else None,
                "error": r.get("error"),
                "pass": ok,
            })
            all_pass = all_pass and ok
        return {
            "passed": all_pass,
            "category": "graded" if all_pass else "wrong_output",
            "per_test": per_test,
        }


def format_failure_feedback(grade_result: dict) -> str:
    """A short, honest, mechanically-generated description of what went
    wrong, suitable for feeding back to the model as real corrective
    information from the real execution outcome -- never an LLM's own
    opinion, never this experiment's own authors' general knowledge of the
    task family. Used only in the experience/training phase (Phase 5),
    never during held-out testing."""
    cat = grade_result.get("category")
    if cat == "malformed_no_code_block":
        return "Your response did not contain a fenced Python code block defining `solve`."
    if cat == "timeout":
        return "Your solution timed out (ran longer than 10 seconds)."
    if cat == "runtime_error":
        return f"Your solution raised an error when run:\n{grade_result.get('stderr_tail', '')[-400:]}"
    if cat == "wrong_output":
        for t in grade_result.get("per_test", []):
            if not t["pass"]:
                if t.get("error"):
                    return f"For input {t['input']}, your function raised: {t['error']}"
                return (
                    f"For input {t['input']}, your function returned {t['got']!r}, "
                    f"but the correct output is {t['expected']!r}."
                )
    return "Your solution did not pass."


if __name__ == "__main__":
    # Self-check: a correct solution passes; a plausible buggy one (uses
    # `<` instead of `<=`, so touching intervals are not merged) fails on
    # exactly the touching-interval case, confirming the checker actually
    # discriminates rather than passing everything.
    correct_code = textwrap.dedent("""
    ```python
    def solve(intervals):
        if not intervals:
            return []
        ordered = sorted((int(a), int(b)) for a, b in intervals)
        merged = [list(ordered[0])]
        for start, end in ordered[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return merged
    ```
    """)
    buggy_code = textwrap.dedent("""
    ```python
    def solve(intervals):
        if not intervals:
            return []
        ordered = sorted((int(a), int(b)) for a, b in intervals)
        merged = [list(ordered[0])]
        for start, end in ordered[1:]:
            if start < merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return merged
    ```
    """)
    hidden = [
        {"input": [[1, 3], [3, 5]], "expected": [[1, 5]]},
        {"input": [[1, 2], [4, 5]], "expected": [[1, 2], [4, 5]]},
    ]
    r_correct = run_candidate(extract_code(correct_code), hidden)
    r_buggy = run_candidate(extract_code(buggy_code), hidden)
    assert r_correct["passed"] is True, r_correct
    assert r_buggy["passed"] is False, r_buggy
    print("sandbox self-check: OK (correct solution passes, touching-interval bug correctly caught)")
