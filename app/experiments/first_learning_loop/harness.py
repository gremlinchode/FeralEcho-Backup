"""
First Real Learning Loop -- experimental harness.

Runs real self-edit-style generation trials in CONTROL and EXPERIENCE
conditions and evaluates each with the real F2 sandbox import test.

Safety, by construction:
- RiverBrain.learn/.save neutralized at the class level before any real
  call -- the same already-proven-safe pattern from
  scripts/memory_ablation_experiment.py, reused here rather than
  reinvented.
- Never calls execute_self_edit()/perform_self_edit() -- no cooldown is
  touched, no write to app/core/self_edit_generated.py ever happens, no
  production deploy path is reachable from this module.
- Uses plan_code_logic() unmodified (it has no side effects beyond a
  real echo_query() call). Does NOT call generate_code_from_plan()
  directly, because that function's own last few lines call
  get_river_brain().learn(...) unconditionally -- this module replicates
  its prompt-construction logic instead, so the lesson sentence can be
  injected and the real-state-mutating call is never reached.
- Zero live callers: nothing outside this package imports this module.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

RESULTS_PATH = Path(__file__).resolve().parent / "trial_results.jsonl"


def neutralize_river_brain_writes():
    from app.core.echo_model_orchestrator import RiverBrain
    RiverBrain.learn = lambda self, *a, **kw: None
    RiverBrain.save = lambda self, *a, **kw: None
    RiverBrain._do_save = lambda self, *a, **kw: None


def _safe_generate(plan: str, lesson_sentence: str = "") -> "tuple[str, str]":
    """Replicates generate_code_from_plan()'s real prompt construction
    (same CODE_OUTPUT_RULES + current-file-contents + plan shape) without
    its trailing RiverBrain.learn() call. Returns (code, model_name)."""
    from app.core.self_edit_manager import (
        CODE_OUTPUT_RULES, SELF_EDIT_FILE, choose_model,
        _strip_markdown_fences, _looks_like_python, _extract_code_block,
        _apply_self_edit_output,
    )
    from app.core.echo_model_orchestrator import echo_query

    try:
        with open(SELF_EDIT_FILE, "r") as f:
            current_contents = f.read()
    except Exception:
        current_contents = ""

    experience_block = f"\n\n{lesson_sentence}\n" if lesson_sentence else ""

    code_prompt = (
        f"{CODE_OUTPUT_RULES}\n\n"
        f"Current contents of {SELF_EDIT_FILE}:\n```\n{current_contents}\n```"
        f"{experience_block}\n\n"
        f"Plan to implement:\n{plan}"
    )

    model_name, _ = choose_model(code_prompt, task_type="self_edit_coding")
    code = echo_query(code_prompt, task_type="coding", trace_id=None)

    if not code:
        return "print('Hello from stub')", model_name
    code = _strip_markdown_fences(code)
    if not _looks_like_python(code):
        code = _extract_code_block(code)
    code = _apply_self_edit_output(code)
    return code, model_name


_NAME_ERR_RE = re.compile(r"NameError: name '([a-zA-Z_][a-zA-Z0-9_]*)' is not defined")


def run_trial(prompt: str, condition: str, lesson_sentence: str = "") -> dict:
    """condition: 'control' or 'experience'. Runs one real plan+generate
    call and one real F2 sandbox check. Never deploys, never touches
    RiverBrain state (caller must have called neutralize_river_brain_writes()
    first)."""
    from app.core.self_edit_manager import plan_code_logic, test_code_in_sandbox

    t0 = time.time()
    plan = plan_code_logic(prompt)
    sentence = lesson_sentence if condition == "experience" else ""
    code, model_name = _safe_generate(plan, lesson_sentence=sentence)
    elapsed_gen = time.time() - t0

    t1 = time.time()
    passed, error = test_code_in_sandbox(code)
    elapsed_sandbox = time.time() - t1

    m = _NAME_ERR_RE.search(error or "")
    failure_class = "NameError" if m else ("none" if passed else "other")

    result = {
        "condition": condition,
        "prompt": prompt,
        "lesson_sentence_used": sentence,
        "model_name": model_name,
        "code": code,
        "passed": passed,
        "error": error,
        "failure_class": failure_class,
        "failure_undefined_name": m.group(1) if m else None,
        "elapsed_gen_s": round(elapsed_gen, 2),
        "elapsed_sandbox_s": round(elapsed_sandbox, 2),
    }
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(result) + "\n")
    return result
