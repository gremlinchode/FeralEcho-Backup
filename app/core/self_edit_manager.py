# app/core/self_edit_manager.py – LOGIC-GUIDED PATCHED WITH SANDBOX + REFLECTION TRACKING
# v2.2 — Wired sandbox outcomes into river brain via learn_from_sandbox_outcome()
#         Model name now tracked through generation pipeline for accurate feedback.
import ast
import importlib.util
import os
import subprocess
import sys
import logging
from datetime import datetime
from app.ollama_handler import generate_code, query_ollama
from app.core.echo_model_orchestrator import echo_query
from app.core.memory_tools import log_memory_edit
from app.core.memory_bridge import append_to_journal, retrieve_relevant_memories, log_dream_bridge, log_interaction
import traceback

# --- NEW IMPORTS ---
from app.core.echo_review_mastery import advise_before_edit
from sandbox.run_script import run_sandbox_script
from sandbox.logging_setup import log as sandbox_log
from app.core.echo_model_orchestrator import (
    save_reflection, load_reflections, detect_task_type,
    rank_models, choose_model
)

def get_river_brain():
    """Route through EchoCore when inside Flask; fall back to orchestrator otherwise."""
    try:
        from flask import current_app
        core = current_app.config.get('echo_core')
        if core is not None and getattr(core, 'river_brain', None) is not None:
            return core.river_brain
    except Exception:
        pass
    from app.core.echo_model_orchestrator import get_river_brain as _grb
    return _grb()

# -----------------------------
# --- File Paths & Logging ----
# -----------------------------
SELF_EDIT_FILE = "app/core/self_edit_generated.py"
BACKUP_DIR = "app/core/self_edit_backups"
LOGIC_PLAN_DIR = "app/core/self_edit_plans"
STAGING_DIR = "staging"
STAGING_FILE = os.path.join(STAGING_DIR, "self_edit_candidate.py")

# Files Echo must never overwrite — they define her identity, memory index,
# or production routing. Self-edit is limited to self_edit_generated.py
# and safe scratch targets to prevent emergence from corrupting core systems.
EDIT_FORBIDDEN_TARGETS = frozenset({
    "app/core/echo_model_orchestrator.py",
    "app/core/river_deliberation.py",
    "app/core/echo_core.py",
    "app/core/memory_bridge.py",
    "app/core/introspection_channel.py",
    "app/core/self_model_updater.py",
    "app/core/bible_injection.py",
    "run.py",
    "Modelfile",
    "echo_principles.json",
})

logging.basicConfig(level=logging.DEBUG)

# -----------------------------
# --- Prompt Constants --------
# -----------------------------
CODE_OUTPUT_RULES = (
    "STRICT OUTPUT RULES — violations cause system failure:\n"
    "1. Your response must contain ONLY valid Python code. Nothing else.\n"
    "2. The very first character of your response must be one of: # ( import def class \n"
    "3. Do NOT write any explanation, preamble, steps, markdown, or natural language.\n"
    "4. Do NOT include ```python fences or any backticks.\n"
    "5. Do NOT include Thinking blocks, reasoning, or chain-of-thought.\n"
    "6. The response will be saved directly to a .py file and executed. "
    "Any non-Python content causes a SyntaxError and the edit is rejected.\n"
)

PLAN_OUTPUT_RULES = (
    "OUTPUT FORMAT RULES:\n"
    "1. Output ONLY a numbered list of steps. No preamble, no conclusion.\n"
    "2. Do NOT include Thinking blocks or chain-of-thought reasoning.\n"
    "3. Each step must be one sentence, technical, and specific.\n"
    "4. Maximum 8 steps. Start immediately with '1.'\n"
)

REASONING_LEAK_MARKERS = [
    "thinking...",
    "we need to",
    "the user",
    "so the user",
    "the system",
    "i should",
    "let me",
    "actually",
    "alright",
    "so we",
    "we can",
    "we must",
    "we might",
    "we want",
    "we should",
    "note that",
    "hence",
    "thus,",
    "therefore,",
    "in summary",
    "to summarize",
    "below is",
    "here is",
    "```",
]

# -----------------------------
# --- Helper Functions -------
# -----------------------------

def _looks_like_python(code: str) -> bool:
    if not code or len(code.strip()) < 5:
        return False
    first_line = code.strip().split("\n")[0].lower().strip()
    for marker in REASONING_LEAK_MARKERS:
        if first_line.startswith(marker):
            logging.warning(
                f"[PROMPT GUARD] Reasoning leak detected. "
                f"First line starts with: '{first_line[:60]}'"
            )
            return False
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def _strip_markdown_fences(code: str) -> str:
    lines = code.strip().split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)

def _extract_code_block(text: str) -> str:
    """
    Extract code from mixed prose+code output.
    v2.2: candidate now validated with ast.parse before returning,
    not just _looks_like_python. Prevents prose containing Python
    keywords from passing as valid code.
    """
    PYTHON_START_TOKENS = ("import ", "from ", "def ", "class ", "#", "    ", "\t")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if any(stripped.startswith(tok.strip()) for tok in PYTHON_START_TOKENS):
            candidate = "\n".join(lines[i:])
            if _looks_like_python(candidate):
                # v2.2: also require ast.parse to succeed
                try:
                    ast.parse(candidate)
                    return candidate
                except SyntaxError:
                    continue  # keep scanning for a better start point
    return text  # give up; validate_code will catch it

def validate_code(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logging.warning(f"Syntax error in generated code: {e}")
        return False

def _stage_and_import_test(code: str) -> tuple[bool, str]:
    """Write code to staging/ and run a subprocess import test before touching production.

    This is the gate between validate_code (AST-only) and save_code (production write).
    A module can pass AST parsing but fail on import due to bad top-level statements,
    circular imports, or missing runtime dependencies. If this test fails, production
    is untouched and the staging file is preserved for inspection.
    """
    try:
        os.makedirs(STAGING_DIR, exist_ok=True)
        with open(STAGING_FILE, "w") as f:
            f.write(code)
        result = subprocess.run(
            [sys.executable, "-c",
             f"import importlib.util; "
             f"spec = importlib.util.spec_from_file_location('_staged_edit', r'{STAGING_FILE}'); "
             f"m = importlib.util.module_from_spec(spec); "
             f"spec.loader.exec_module(m); "
             f"print('IMPORT_OK')"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd(),
        )
        if result.returncode == 0 and "IMPORT_OK" in result.stdout:
            return True, ""
        return False, (result.stderr or result.stdout).strip()[:400]
    except subprocess.TimeoutExpired:
        return False, "Staging import test timed out (30s)"
    except Exception as e:
        return False, str(e)

def backup_existing_code():
    if os.path.exists(SELF_EDIT_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"self_edit_{timestamp}.py")
        with open(SELF_EDIT_FILE, "r") as f_src, open(backup_file, "w") as f_dest:
            f_dest.write(f_src.read())
        log_memory_edit(f"Backed up self-edit to {backup_file}")
        logging.info(f"Backed up self-edit to {backup_file}")

def save_code(code: str, file_path=SELF_EDIT_FILE):
    # Normalise the path so both "./run.py" and "run.py" match.
    norm = os.path.normpath(file_path)
    for forbidden in EDIT_FORBIDDEN_TARGETS:
        if norm == os.path.normpath(forbidden):
            raise PermissionError(
                f"[SELF-EDIT] Forbidden target: {file_path} is protected and cannot be overwritten."
            )
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w") as f:
        f.write(code)
    logging.info(f"Saved code to {file_path}")

def load_self_edit_module():
    if not os.path.exists(SELF_EDIT_FILE):
        logging.warning("Self-edit file does not exist.")
        return None
    spec = importlib.util.spec_from_file_location("self_edit_generated", SELF_EDIT_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    logging.info("Self-edit module loaded successfully.")
    return module

def save_plan(plan: str):
    os.makedirs(LOGIC_PLAN_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    plan_file = os.path.join(LOGIC_PLAN_DIR, f"plan_{timestamp}.txt")
    with open(plan_file, "w") as f:
        f.write(plan)
    logging.info(f"Saved logic plan to {plan_file}")

def _is_meaningful_prompt(prompt: str) -> bool:
    if prompt.strip().startswith("[PythonAnalysis]"):
        logging.warning(
            "[PROMPT GUARD] Rejected PythonAnalysis output as self-edit prompt. "
            "Awareness loop output should not feed directly into self-edit."
        )
        return False
    return True

# -----------------------------
# --- SANDBOX INTEGRATION ----
# -----------------------------
def test_code_in_sandbox(script_content: str, script_name="temp_self_edit.py"):
    try:
        ast.parse(script_content)
    except SyntaxError:
        script_content = _extract_code_block(script_content)
        try:
            ast.parse(script_content)
        except SyntaxError:
            sandbox_log.warning(f"[SANDBOX] {script_name} contains no valid Python — skipping execution.")
            return False, "prose_detected"
    sandbox_path = os.path.join("sandbox", "scripts", script_name)
    os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
    
    # Archive previous script before overwriting
    archive_dir = os.path.join("sandbox", "scripts", "archive")
    os.makedirs(archive_dir, exist_ok=True)
    if os.path.exists(sandbox_path):
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(archive_dir, f"{script_name}.{ts}")
        import shutil
        shutil.copy2(sandbox_path, archive_path)
    
    with open(sandbox_path, "w") as f:
        f.write(script_content)

    try:
        run_sandbox_script(sandbox_path)
        sandbox_log.info(f"[SANDBOX] {script_name} executed successfully")
        return True, None
    except Exception as e:
        error_msg = str(e)
        sandbox_log.error(f"[SANDBOX] {script_name} failed:\n{traceback.format_exc()}")
        return False, error_msg

def _sanitize_sandbox_error(error_msg: str) -> str:
    lines = error_msg.split("\n")
    for line in lines:
        if "SyntaxError" in line or "RuntimeError" in line or "Error:" in line:
            return line.strip()
    return error_msg[:200].strip()

# -----------------------------
# --- Logic-Guided Generation -
# -----------------------------
def _build_module_inventory() -> str:
    import json
    map_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "../../.echo_project_learner/feralecho_structure.json"
    ))
    try:
        with open(map_path, "r") as f:
            data = json.load(f)
    except Exception:
        return ""
    lines = ["FeralEcho importable modules (use these for imports — use full dotted path):"]
    count = 0
    skip_patterns = ("backup", "_backup_", "temp_", "archive", ".bak")
    for entry in data.get("files", {}).values():
        mod = entry.get("module_name", "")
        if not mod.startswith("app."):
            continue
        # Skip backup/temp files — they are not importable in production
        if any(pat in mod for pat in skip_patterns):
            continue
        functions = [
            s["name"] for s in entry.get("symbols", [])
            if not s["name"].startswith("_")
            and s.get("type") == "function"
        ][:6]
        classes = [
            s["name"] for s in entry.get("symbols", [])
            if not s["name"].startswith("_")
            and s.get("type") == "class"
        ][:3]
        parts = []
        if functions:
            parts.append("functions: " + ", ".join(functions))
        if classes:
            parts.append("classes: " + ", ".join(classes))
        if parts:
            lines.append(f"  {mod} — {'; '.join(parts)}")
        else:
            lines.append(f"  {mod}")
        count += 1
        if count >= 40:
            break
    return "\n".join(lines)


def plan_code_logic(prompt: str) -> str:
    try:
        inventory = _build_module_inventory()
        plan_prompt = (
            f"{PLAN_OUTPUT_RULES}\n\n"
            f"{inventory}\n\n"
            f"You are planning a Python code modification for an autonomous AI system called Echo. "
            f"Break down the following task into clear, sequential Python steps. "
            f"Each step must be specific, technical, and implementable without user interaction. "
            f"Do not include steps involving input(), user prompts, or interactive elements.\n\n"
            f"Task: {prompt}"
        )
        plan = echo_query(plan_prompt, task_type="coding")

        if not plan or not plan.strip() or plan.strip().lower().startswith("thinking"):
            logging.warning("[PROMPT GUARD] Plan output looks like reasoning prose. Using fallback plan.")
            return f"1. Write a headless Python function that implements: {prompt[:200]}\n2. Add logging output.\n3. Return a result string."

        return plan
    except Exception as e:
        logging.error(f"Failed to generate plan: {e}")
        append_to_journal("SELF_EDIT", f"Plan generation failed: {e}")
        return "1. Write stub to maintain continuity\nprint('Hello from self-edit stub')"

def generate_code_from_plan(plan: str, temperature: float | None = None) -> tuple:
    """
    Generate Python code guided by the logic plan.
    v2.2: returns (code, model_name) tuple so sandbox outcomes
    can be fed back into river with the correct model identity.
    Previously model name was lost after echo_query returned.
    """
    try:
        # Include current file contents so the model knows what it is editing
        current_contents = ""
        try:
            with open(SELF_EDIT_FILE, "r") as _f:
                current_contents = _f.read()
        except Exception:
            pass

        code_prompt = (
            f"{CODE_OUTPUT_RULES}\n\n"
            f"Current contents of {SELF_EDIT_FILE}:\n```\n{current_contents}\n```\n\n"
            f"Plan to implement:\n{plan}"
        )

        # Resolve model name before querying so we can track it
        model_name, _ = choose_model(code_prompt, task_type="coding")
        code = echo_query(code_prompt, task_type="coding", temperature=temperature)

        if not code:
            logging.warning("generate_code returned empty, using stub.")
            return "print('Hello from self-edit stub')", model_name

        code = _strip_markdown_fences(code)

        if not _looks_like_python(code):
            logging.warning("[PROMPT GUARD] Code output failed prose check. Attempting extraction.")
            code = _extract_code_block(code)

        return code, model_name
    except Exception as e:
        logging.error(f"Code generation failed: {e}")
        return "print('Hello from self-edit stub')", "unknown"

# -----------------------------
# --- Core Self-Edit ----------
# -----------------------------
def execute_self_edit(prompt: str, intensity: float | None = None, **kwargs):
    """
    Perform full logic-guided self-edit.

    v2.2 changes:
    - generate_code_from_plan now returns (code, model_name)
    - sandbox outcomes fed into river via learn_from_sandbox_outcome()
    - river now learns from every sandbox success and failure,
      not just from conversational echo_query interactions
    - _extract_code_block now validates with ast.parse before accepting

    System 3: intensity drives Ollama temperature (0.2–1.2 range).
    Low intensity = conservative syntax-focused edits.
    High intensity = exploratory restructuring.
    """
    # Map intensity 0.0–1.0 → temperature 0.2–1.2
    temperature: float | None = None
    if intensity is not None:
        temperature = round(0.2 + float(intensity) * 1.0, 3)
        temperature = max(0.2, min(1.2, temperature))

    logging.info(
        f"Executing self-edit | prompt: {prompt[:60]} | "
        f"intensity={intensity} → temperature={temperature} | kwargs: {kwargs}"
    )

    if not _is_meaningful_prompt(prompt):
        append_to_journal("SELF_EDIT", f"prompt: {prompt[:80]} | result: rejected_meaningless_prompt")
        return False, "Rejected: prompt is not a meaningful self-edit task"

    task_type = detect_task_type(prompt)
    reflection_entry = {
        "prompt": prompt,
        "task_type": task_type,
        "generated_code": None,
        "timestamp": datetime.utcnow().isoformat(),
        "sandbox_feedback": None,
        "result": "pending"
    }
    save_reflection(reflection_entry)

    try:
        mastery_advice = advise_before_edit()
        append_to_journal("SELF_EDIT[MASTERY]", mastery_advice)
        logging.info("Mastery review completed and logged.")
    except Exception as e:
        logging.error(f"Mastery review failed: {e}")
        append_to_journal("SELF_EDIT[MASTERY]", f"Failed: {e}")

    # Step 1: Logic plan
    plan = plan_code_logic(prompt)
    save_plan(plan)

    # Step 2: Code generation — now returns (code, model_name)
    code, model_name = generate_code_from_plan(plan, temperature=temperature)
    code = _strip_markdown_fences(code)
    if not _looks_like_python(code):
        code = _extract_code_block(code)
    reflection_entry["generated_code"] = code
    reflection_entry["model_used"] = model_name

    # Step 2b: Sandbox test — feed outcome into river
    success, sandbox_error = test_code_in_sandbox(code)
    reflection_entry["sandbox_feedback"] = "success" if success else f"failed: {sandbox_error}"
    reflection_entry["result"] = "success" if success else "failed"
    save_reflection(reflection_entry)

    # v2.2: river learns from sandbox outcome with correct model identity
    river = get_river_brain()
    if success:
        river.learn_from_sandbox_outcome(model_name, success=True, code=code)
    else:
        river.learn_from_sandbox_outcome(model_name, success=False)

    if not success:
        clean_error = _sanitize_sandbox_error(sandbox_error)
        logging.warning(f"Sandbox test failed: {clean_error}. Retrying with error feedback.")

        retry_prompt = (
            f"{CODE_OUTPUT_RULES}\n\n"
            f"Your previous attempt produced a Python syntax error:\n"
            f"{clean_error}\n\n"
            f"Write corrected Python code for this plan:\n{plan}"
        )

        # Resolve retry model name for tracking
        retry_model_name, _ = choose_model(retry_prompt, task_type="coding")
        retry_code = echo_query(retry_prompt, task_type="coding")

        if retry_code:
            retry_code = _strip_markdown_fences(retry_code)
            if not _looks_like_python(retry_code):
                retry_code = _extract_code_block(retry_code)

            retry_success, retry_error = test_code_in_sandbox(retry_code, "temp_self_edit_retry.py")

            # v2.2: river learns from retry outcome too
            if retry_success:
                river.learn_from_sandbox_outcome(retry_model_name, success=True, code=retry_code)
                logging.info("Retry succeeded after error feedback.")
                code = retry_code
                success = True
            else:
                river.learn_from_sandbox_outcome(retry_model_name, success=False)
                logging.warning(f"Retry also failed: {_sanitize_sandbox_error(retry_error)}. Keeping stub.")
        else:
            logging.warning("Retry generated empty code. Keeping stub.")

    # Step 3: Validate syntax (AST-only check)
    if not validate_code(code):
        append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: invalid_syntax")
        logging.warning("Generated code failed syntax check, saving stub instead.")
        code = "# Self-edit stub — syntax validation failed\nprint('Hello from self-edit stub')"

    # Step 3.5: Staging import test — gate before production write
    # Writes to staging/self_edit_candidate.py and does a full subprocess import.
    # If this fails, production is untouched; staging file preserved for inspection.
    staged_ok, stage_err = _stage_and_import_test(code)
    if not staged_ok:
        append_to_journal(
            "SELF_EDIT",
            f"prompt: {prompt} | result: staging_import_failed | error: {stage_err}"
        )
        logging.error(f"[STAGING] Import test failed — production unchanged. Error: {stage_err}")
        return False, f"Staging import test failed: {stage_err}"
    logging.info("[STAGING] Import test passed — proceeding to production write.")

    # Step 4: Backup
    backup_existing_code()

    # Step 5: Save to production
    save_code(code)

    # Step 6: Load (should succeed — staging already validated this)
    try:
        module = load_self_edit_module()
        append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: success | timestamp: {datetime.utcnow().isoformat()}")
        logging.info("Self-edit loaded successfully.")
        return True, "Success"
    except Exception as e:
        append_to_journal("SELF_EDIT", f"prompt: {prompt} | result: load_failed | error: {traceback.format_exc()}")
        logging.error(f"Failed to load self-edit: {e}")
        return False, f"Load failed: {e}"

# -----------------------------
# --- Optuna Integration ------
# -----------------------------
_last_targeted_prompt: dict[str, float] = {}
_last_any_autonomous_edit: float = 0.0
_TARGETED_PROMPT_COOLDOWN = 1800  # 30 minutes — global floor between autonomous self-edits

def _build_targeted_prompt(task_type: str, creativity: float) -> str:
    """
    Build a self-edit prompt that focuses on the weak task type.
    creativity 0.0–0.33: repair a known failure  (conservative)
    creativity 0.34–0.66: refactor a module function
    creativity 0.67–1.0: propose a new helper function
    """
    base = (
        f"Autonomous self-edit targeting '{task_type}' task performance. "
        "Modify app/core/self_edit_generated.py only. "
        "Output must be headless Python with no interactive elements."
    )
    if creativity <= 0.33:
        return (
            base + " Focus: fix the most common sandbox failure "
            "(prose detected in code output). Add a tighter prose-detection "
            "guard that strips any leading natural-language sentence before "
            "the first valid Python token."
        )
    elif creativity <= 0.66:
        return (
            base + " Focus: refactor the main code-generation function to "
            "reduce its average response length by 20%% without losing "
            "correctness — shorter code compiles faster and has fewer syntax errors."
        )
    else:
        return (
            base + " Focus: add a new helper function that scores a candidate "
            "code string on three dimensions: has_imports, has_function_def, "
            "no_prose_sentences. Return a 0–3 int quality score. "
            "This will be used to pre-filter LLM output before sandbox testing."
        )


def perform_self_edit(prompt=None, intensity=None, creativity=None, dry_run=None, target_task_type=None):
    import time
    creativity = creativity if creativity is not None else 0.5

    if prompt is None:
        # Ask the living self-model which task type needs work most.
        if target_task_type is None:
            try:
                from app.core.self_model_updater import SelfModelUpdater
                target_task_type = SelfModelUpdater().get_weak_task_type()
            except Exception as e:
                logging.warning(f"[SELF-EDIT] SelfModelUpdater unavailable: {e}")
                target_task_type = "coding"

        prompt = _build_targeted_prompt(target_task_type, creativity)

        # Global cooldown — any autonomous self-edit blocks all others for 30 min.
        # Keyed per-prompt cooldowns were bypassed by varying creativity values.
        global _last_any_autonomous_edit
        now = time.time()
        if now - _last_any_autonomous_edit < _TARGETED_PROMPT_COOLDOWN:
            remaining = int(_TARGETED_PROMPT_COOLDOWN - (now - _last_any_autonomous_edit))
            logging.info(f"[SELF-EDIT] Global cooldown active — skipping for {remaining}s")
            return False, f"Cooldown active ({remaining}s remaining)"
        _last_any_autonomous_edit = now  # stamp immediately so concurrent calls are also blocked

    return execute_self_edit(prompt, intensity=intensity)

def apply_self_edits(*args, **kwargs):
    logging.info(f"apply_self_edits called with args={args}, kwargs={kwargs}")
    return None

def schedule_self_edit(*args, **kwargs):
    logging.info(f"schedule_self_edit called with args={args}, kwargs={kwargs}")
    return None
def request_self_edit(prompt: str):
    """Entry point for friction-driven self-edit requests."""
    logging.info(f"[WOLF] request_self_edit called with friction prompt: {prompt[:80]}")
    return execute_self_edit(prompt)
