"""
Architecture A Minimal Hot-Stove Learning Proof -- isolated harness.

Reconstructs the REAL retry-pipeline mechanics from
app/core/self_edit_manager.py:execute_self_edit() (lines ~1998-2050,
re-read directly from current source before this file was written) without
calling execute_self_edit()/perform_self_edit() themselves -- those
functions write reflection_entry to save_reflection(), append to
memory/SELF_EDIT.log via append_to_journal(), and mutate
memory/self_edit_cooldown.json / self_edit_convergence.json, all real
production state this experiment must never touch.

Safety, by construction, verified live at harness start and end:
- RiverBrain.learn / .learn_from_sandbox_outcome / .save / ._do_save
  patched to no-ops at the CLASS level before any import that could
  construct an instance -- same pattern proven safe by
  app/experiments/first_learning_loop/harness.py this session, extended
  here to also cover learn_from_sandbox_outcome (the retry path's own
  call) since that harness's domain never exercised it.
- log_interaction (app.core.echo_model_orchestrator.log_interaction) is
  ALSO patched to a no-op in this harness -- stricter than the prior
  first_learning_loop harness, per this mission's explicit instruction not
  to alter existing interaction logs. echo_query() is still called for
  real (real Ollama traffic), only its production log-write is suppressed.
- test_code_in_sandbox() IS called for real -- this is the real F2 kernel
  sandbox (sandbox-exec + echo_sandbox.sb). It writes to
  sandbox/scripts/<script_name> and sandbox/scripts/archive/ -- this is
  the sandbox's own designated, already-existing scratch/archive area
  (CLAUDE.md: "isolated smoke tests... writes blocked outside sandbox/"),
  not production memory. Script names are prefixed hotstove_proof_ to stay
  visually distinguishable from real self-edit history in that directory.
- Never writes to app/core/self_edit_generated.py, memory/*.json(l),
  data/question_garden.jsonl, or any EDIT_FORBIDDEN_TARGETS file.
- All experiment-produced records live under this directory only.
"""
from __future__ import annotations

import json
import re
import sys
import time
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_HERE = Path(__file__).resolve().parent
CANDIDATE_KNOWLEDGE_PATH = _HERE / "candidate_knowledge.jsonl"
TRIAL_RESULTS_PATH = _HERE / "trial_results.jsonl"

_NAME_ERR_RE = re.compile(r"NameError: name '([a-zA-Z_][a-zA-Z0-9_]*)' is not defined")


def neutralize_production_writes():
    """Class-level patch, must run before any RiverBrain instance is
    constructed or echo_query() is called. Idempotent."""
    from app.core.echo_model_orchestrator import RiverBrain
    import app.core.echo_model_orchestrator as emo

    RiverBrain.learn = lambda self, *a, **kw: None
    RiverBrain.learn_from_sandbox_outcome = lambda self, *a, **kw: None
    RiverBrain.learn_from_council_rating = lambda self, *a, **kw: None
    RiverBrain.save = lambda self, *a, **kw: None
    if hasattr(RiverBrain, "_do_save"):
        RiverBrain._do_save = lambda self, *a, **kw: None

    emo.log_interaction = lambda *a, **kw: None


def verify_neutralization() -> dict:
    """Direct proof, not assumed: call the patched methods and confirm
    they do not raise and do not touch disk. Returns a small report dict
    for the audit's safety section."""
    from app.core.echo_model_orchestrator import get_river_brain
    import app.core.echo_model_orchestrator as emo
    import hashlib

    river_pkl = _ROOT / "memory" / "river_brain.pkl"
    interaction_log = _ROOT / "memory" / "interaction_log.jsonl"

    before_hash = hashlib.sha256(river_pkl.read_bytes()).hexdigest() if river_pkl.exists() else None
    before_lines = sum(1 for _ in open(interaction_log)) if interaction_log.exists() else None

    rb = get_river_brain()
    rb.learn("hotstove-proof-canary-model", "self_edit_coding", "print('canary')")
    rb.learn_from_sandbox_outcome("hotstove-proof-canary-model", success=False, error="canary error")
    rb.save()
    emo.log_interaction(
        model_name="hotstove-proof-canary-model", task_type="coding",
        prompt="canary", response="canary", quality_score=0, river_influence=0.0,
    )

    after_hash = hashlib.sha256(river_pkl.read_bytes()).hexdigest() if river_pkl.exists() else None
    after_lines = sum(1 for _ in open(interaction_log)) if interaction_log.exists() else None

    return {
        "river_brain_pkl_unchanged": before_hash == after_hash,
        "river_brain_pkl_hash": after_hash,
        "interaction_log_unchanged": before_lines == after_lines,
        "interaction_log_lines": after_lines,
    }


def _sanitize_sandbox_error(error_msg: str) -> str:
    """Byte-identical copy of self_edit_manager.py's own
    _sanitize_sandbox_error() -- imported directly below instead where
    possible; this local copy exists only as a fallback if the import
    ever fails, so the harness degrades loudly rather than silently."""
    lines = (error_msg or "").split("\n")
    for line in lines:
        if "SyntaxError" in line or "RuntimeError" in line or "Error:" in line:
            return line.strip()
    return (error_msg or "")[:200].strip()


def run_sandbox(code: str, script_name: str):
    """Calls the REAL, unmodified test_code_in_sandbox() -- real F2 kernel
    sandbox. Returns (success, error)."""
    from app.core.self_edit_manager import test_code_in_sandbox
    return test_code_in_sandbox(code, script_name)


def generate_candidate(plan_prompt: str, trace_id: str) -> "tuple[str, str]":
    """Real echo_query() call -- real Ollama traffic, real model selection
    via choose_model(), matching self_edit_manager.py's own
    generate_code_from_plan() prompt shape (CODE_OUTPUT_RULES + plan) but
    WITHOUT that function's own trailing get_river_brain().learn() call
    (avoided by calling echo_query() directly here, not
    generate_code_from_plan()). Returns (code, model_name)."""
    from app.core.self_edit_manager import (
        CODE_OUTPUT_RULES, choose_model, _strip_markdown_fences,
        _looks_like_python, _extract_code_block, _strip_toplevel_self_calls,
    )
    from app.core.echo_model_orchestrator import echo_query

    code_prompt = f"{CODE_OUTPUT_RULES}\n\nPlan to implement:\n{plan_prompt}"
    model_name, _ = choose_model(code_prompt, task_type="self_edit_coding")
    code = echo_query(code_prompt, task_type="coding", trace_id=trace_id, source="hotstove_proof_experiment")
    if not code:
        return "", model_name
    code = _strip_markdown_fences(code)
    if not _looks_like_python(code):
        code = _extract_code_block(code)
    code = _strip_toplevel_self_calls(code)
    return code, model_name


def build_retry_prompt(clean_error: str, plan_prompt: str, injected_hypothesis: str = "") -> str:
    """Byte-identical reconstruction of execute_self_edit()'s real retry
    prompt template (self_edit_manager.py lines ~2002-2010, re-read
    directly from current source this pass), with ONE additive sentence
    for the EXPERIENCE condition -- injected_hypothesis, when non-empty,
    is inserted as one extra paragraph. CONTROL calls this with
    injected_hypothesis="" and gets a prompt that is otherwise byte-for-
    byte what production would build today."""
    from app.core.self_edit_manager import CODE_OUTPUT_RULES

    experience_block = ""
    if injected_hypothesis:
        experience_block = (
            f"\nA similar failure occurred before under this exact error "
            f"signature. The confirmed cause was: {injected_hypothesis}\n"
        )

    return (
        f"{CODE_OUTPUT_RULES}\n\n"
        f"Your previous attempt failed with this error:\n"
        f"{clean_error}\n"
        f"{experience_block}\n"
        f"IMPORTANT: Do NOT include module-level test calls. "
        f"Do NOT write lines like `import app.core.self_edit_generated as x; x.some_func()` "
        f"outside of function definitions -- the module being tested is not yet deployed.\n\n"
        f"Write corrected Python code for this plan:\n{plan_prompt}"
    )


def run_retry(clean_error: str, plan_prompt: str, trace_id: str, condition: str,
              injected_hypothesis: str = "", script_suffix: str = "") -> dict:
    """One real retry attempt, matching execute_self_edit()'s real retry
    mechanics (lines 2012-2048) exactly, minus the production-write calls
    (river.learn_from_sandbox_outcome, save_reflection). Returns a full
    result dict."""
    from app.core.self_edit_manager import (
        choose_model, _strip_markdown_fences, _looks_like_python,
        _extract_code_block, _strip_toplevel_self_calls,
    )
    from app.core.echo_model_orchestrator import echo_query

    retry_prompt = build_retry_prompt(clean_error, plan_prompt, injected_hypothesis)
    retry_model_name, _ = choose_model(retry_prompt, task_type="self_edit_coding")
    retry_code = echo_query(retry_prompt, task_type="coding", trace_id=trace_id,
                             source="hotstove_proof_experiment")

    if not retry_code:
        return {
            "condition": condition, "trace_id": trace_id, "retry_model": retry_model_name,
            "retry_code": "", "retry_success": False, "retry_error": "empty_generation",
            "retry_prompt_len": len(retry_prompt),
        }

    retry_code = _strip_markdown_fences(retry_code)
    if not _looks_like_python(retry_code):
        retry_code = _extract_code_block(retry_code)
    retry_code = _strip_toplevel_self_calls(retry_code)

    script_name = f"hotstove_proof_{condition}_{script_suffix}.py"
    retry_success, retry_error = run_sandbox(retry_code, script_name)

    return {
        "condition": condition,
        "trace_id": trace_id,
        "retry_model": retry_model_name,
        "retry_code": retry_code,
        "retry_success": retry_success,
        "retry_error": retry_error,
        "retry_prompt_len": len(retry_prompt),
        "injected_hypothesis": injected_hypothesis,
    }


def append_jsonl(path: Path, record: dict):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
