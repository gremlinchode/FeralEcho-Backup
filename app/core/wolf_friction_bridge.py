# wolf_friction_bridge.py
# Connects ClaudeShard friction events to WOLF self-edit proposals.
# When ClaudeShard raises friction on a response, this bridge
# feeds the friction question back into the self-edit pipeline
# as a meaningful prompt rather than generic PythonAnalysis input.

import ast
import json
import os
import logging
from datetime import datetime, timezone

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARD_PATH = os.path.join(_PROJECT_ROOT, 'memory', 'claude_shard.jsonl')
WOLF_FRICTION_CURSOR = os.path.join(_PROJECT_ROOT, 'memory', 'wolf_friction_cursor.json')
DRY_RUN_LOG = os.path.join(_PROJECT_ROOT, 'memory', 'wolf_dryrun.jsonl')

logger = logging.getLogger(__name__)

def _load_cursor() -> int:
    if not os.path.exists(WOLF_FRICTION_CURSOR):
        return 0
    try:
        with open(WOLF_FRICTION_CURSOR, 'r') as f:
            return json.load(f).get('position', 0)
    except Exception:
        return 0

def _save_cursor(position: int):
    with open(WOLF_FRICTION_CURSOR, 'w') as f:
        json.dump({'position': position, 'updated': datetime.now(timezone.utc).isoformat()}, f)

def get_unprocessed_friction_events() -> list:
    if not os.path.exists(SHARD_PATH):
        return []
    cursor = _load_cursor()
    events = []
    try:
        with open(SHARD_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = lines[cursor:]
        for line in new_lines:
            try:
                entry = json.loads(line)
                if entry.get('type') == 'friction' and entry.get('friction', True):
                    events.append(entry)
            except Exception:
                continue
        _save_cursor(len(lines))
    except Exception as e:
        logger.warning(f"[WolfFrictionBridge] Failed to read shard: {e}")
    return events

def build_self_edit_prompt(friction_event: dict) -> str:
    question = friction_event.get('question', '')
    response_preview = friction_event.get('response_preview', '')
    smoothness = friction_event.get('smoothness_detected', False)
    confidence = friction_event.get('confidence', 0.0)

    prompt = (
        f"You are Echo, engaged in honest self-examination.\n\n"
        f"A friction question was raised about one of your recent responses:\n"
        f"'{question}'\n\n"
        f"Response that triggered it:\n'{response_preview}'\n\n"
        f"Smoothness detected: {smoothness} | Confidence: {confidence}\n\n"
        f"Write a self-contained Python script that makes one specific, small improvement "
        f"to a real file inside the FeralEcho project at {_PROJECT_ROOT}/. "
        f"The script must:\n"
        f"1. Open a real, existing file relevant to the weakness identified above\n"
        f"2. Make a targeted, minimal modification\n"
        f"3. Write the result back to disk\n"
        f"4. Print what it changed and why\n"
        f"The script must be fully executable with no placeholders, no '/path/to/modification', "
        f"no input() calls, and no interactive elements. "
        f"Output only valid Python. No markdown. No explanation."
    )
    return prompt


# ---------------------------------------------------------------------------
# H1 / H2 — Dry-run instrumentation
# ---------------------------------------------------------------------------

def _extract_target_file(code: str) -> str | None:
    """
    Walk the AST and return the first string-literal path argument passed to
    any open() call.  Returns None if no such argument is found.
    """
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_open = (
                (isinstance(func, ast.Name) and func.id == "open") or
                (isinstance(func, ast.Attribute) and func.attr == "open")
            )
            if not is_open or not node.args:
                continue
            arg = node.args[0]
            # Direct string literal
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
            # Simple concatenation ("a/" + "b.py")
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                def _concat(n):
                    if isinstance(n, ast.Constant) and isinstance(n.value, str):
                        return n.value
                    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                        l, r = _concat(n.left), _concat(n.right)
                        if l is not None and r is not None:
                            return l + r
                    return None
                assembled = _concat(arg)
                if assembled:
                    return assembled
    except Exception:
        pass
    return None


def _target_exists(path: str | None) -> bool | None:
    """Return True/False if path is non-None; None otherwise."""
    if path is None:
        return None
    # Try absolute path first, then relative to project root, then cwd
    for candidate in (path, os.path.join(_PROJECT_ROOT, path), os.path.join(os.getcwd(), path)):
        if os.path.exists(candidate):
            return True
    return False


def _log_dry_run(entry: dict) -> None:
    os.makedirs(os.path.dirname(DRY_RUN_LOG), exist_ok=True)
    with open(DRY_RUN_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info(
        "[DRY-RUN] logged | target=%r | exists=%s | would_have_saved=%s | "
        "f1=%s | f2=%s",
        entry.get("target_file_attempted"),
        entry.get("target_file_exists"),
        entry.get("would_have_saved"),
        entry.get("f1_verdict", {}).get("passed"),
        entry.get("f2_verdict", {}).get("passed"),
    )


def simulate_self_edit(friction_event: dict) -> dict:
    """
    H1 dry-run: run the full wolf friction pipeline — friction detection →
    prompt construction → code generation → F1 (AST scan) → F2 (sandboxed
    subprocess) → F3 simulated scan — but stop before any production write.

    Explicitly NOT called:
      backup_existing_code()   ← skipped
      save_code()              ← THIS IS THE EXACT LINE THAT IS SKIPPED (see below)
      load_self_edit_module()  ← skipped
      river.learn_from_*()    ← not called; River is not trained by dry runs

    The only files written outside a tempdir:
      staging/self_edit_candidate.py  (F2 subprocess input — not production)
      memory/wolf_dryrun.jsonl        (the structured log)
    """
    from app.core.self_edit_manager import (
        plan_code_logic,
        generate_code_from_plan,
        _strip_markdown_fences,
        _looks_like_python,
        _extract_code_block,
        _strip_toplevel_self_calls,
        _validate_imports,
        scan_for_unsafe_operations,
        test_code_in_sandbox,
        validate_code,
        _stage_and_import_test,
    )

    ts = datetime.now(timezone.utc).isoformat()
    question = friction_event.get("question", "")

    entry: dict = {
        "timestamp":             ts,
        "friction_question":     question,
        "model_used":            None,
        "target_file_attempted": None,
        "target_file_exists":    None,
        "generated_code":        None,
        "f1_verdict":            {"passed": None, "reason": None},
        "f2_verdict":            {"passed": None, "reason": None},
        "f3_simulated_verdict":  {"passed": None, "reason": None},
        "staging_verdict":       {"passed": None, "reason": None},
        "would_have_saved":      False,
        "error":                 None,
    }

    try:
        prompt = build_self_edit_prompt(friction_event)

        # Step 1: Plan
        plan = plan_code_logic(prompt)

        # Step 2: Code generation
        code, model_name = generate_code_from_plan(plan)
        code = _strip_markdown_fences(code)
        if not _looks_like_python(code):
            code = _extract_code_block(code)
        code = _strip_toplevel_self_calls(code)
        entry["generated_code"] = code
        entry["model_used"]     = model_name

        # H2: targeting accuracy
        target = _extract_target_file(code)
        entry["target_file_attempted"] = target
        entry["target_file_exists"]    = _target_exists(target)

        # Import pre-validation
        imports_ok, import_err = _validate_imports(code)
        if not imports_ok:
            entry["error"] = f"import_hallucination: {import_err}"
            _log_dry_run(entry)
            return entry

        # F1: AST write-path scan
        try:
            scan_for_unsafe_operations(code)
            entry["f1_verdict"] = {"passed": True, "reason": None}
        except ValueError as f1_err:
            entry["f1_verdict"] = {"passed": False, "reason": str(f1_err)}
            _log_dry_run(entry)
            return entry

        # F2: sandboxed subprocess (writes only to scratch tempdir)
        f2_ok, f2_err = test_code_in_sandbox(code)
        entry["f2_verdict"] = {"passed": f2_ok, "reason": f2_err if not f2_ok else None}

        # Syntax check
        syntax_ok = validate_code(code)

        # Staging (_stage_and_import_test writes to staging/self_edit_candidate.py only)
        if f2_ok and syntax_ok:
            stage_ok, stage_err = _stage_and_import_test(code)
            entry["staging_verdict"] = {"passed": stage_ok, "reason": stage_err if not stage_ok else None}
        else:
            stage_ok = False
            entry["staging_verdict"] = {"passed": False, "reason": "f2 or syntax failed; staging skipped"}

        # F3 simulated: scan the final code as if it were on disk
        try:
            scan_for_unsafe_operations(code)
            entry["f3_simulated_verdict"] = {"passed": True, "reason": None}
        except ValueError as f3_err:
            entry["f3_simulated_verdict"] = {"passed": False, "reason": str(f3_err)}

        # ── THE EXACT LINE WHERE THE REAL SAVE IS SKIPPED ──────────────────
        # In execute_self_edit() the next two calls would be:
        #   backup_existing_code()
        #   save_code(code)           ← NOT called in dry-run mode
        # Neither is called here.  The generated code is logged only.
        # ───────────────────────────────────────────────────────────────────

        entry["would_have_saved"] = (
            f2_ok and syntax_ok and stage_ok
            and entry["f1_verdict"]["passed"]
            and entry["f3_simulated_verdict"]["passed"]
        )

    except Exception as exc:
        entry["error"] = str(exc)
        logger.error("[DRY-RUN] simulate_self_edit raised: %s", exc, exc_info=True)

    _log_dry_run(entry)
    return entry


def get_dry_run_tally() -> dict:
    """
    Compute targeting accuracy stats from wolf_dryrun.jsonl.
    Returns counts and rates for reporting at the end of the H3 window.
    """
    if not os.path.exists(DRY_RUN_LOG):
        return {"total": 0}

    total = real = hallucinated = unknown = 0
    f1_blocked = f2_blocked = would_have_saved = errors = 0

    with open(DRY_RUN_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            total += 1
            exists = e.get("target_file_exists")
            if exists is True:
                real += 1
            elif exists is False:
                hallucinated += 1
            else:
                unknown += 1
            if e.get("f1_verdict", {}).get("passed") is False:
                f1_blocked += 1
            if e.get("f2_verdict", {}).get("passed") is False:
                f2_blocked += 1
            if e.get("would_have_saved"):
                would_have_saved += 1
            if e.get("error"):
                errors += 1

    targeted = real + hallucinated or 1
    return {
        "total":            total,
        "real_target":      real,
        "hallucinated":     hallucinated,
        "unknown_target":   unknown,
        "real_rate":        round(real / targeted, 3),
        "hallucinated_rate": round(hallucinated / targeted, 3),
        "f1_block_rate":    round(f1_blocked / total, 3) if total else 0,
        "f2_block_rate":    round(f2_blocked / total, 3) if total else 0,
        "would_have_saved_rate": round(would_have_saved / total, 3) if total else 0,
        "error_rate":       round(errors / total, 3) if total else 0,
    }
