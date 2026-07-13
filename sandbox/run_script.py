# sandbox/run_script.py
import ast
import subprocess
import sys
import os
import logging
import traceback
import importlib.util
from contextlib import redirect_stdout, redirect_stderr
import io

# -----------------------------
# --- Logging Configuration ---
# -----------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs/sandbox_execution.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

def log_info(message: str):
    logging.info(message)

def log_debug(message: str):
    logging.debug(message)

def log_warning(message: str):
    logging.warning(message)

def log_error(message: str):
    logging.error(message)

def log_exception(e: Exception):
    logging.error(traceback.format_exc())

# -----------------------------
# --- Sandbox Execution -------
# -----------------------------
SANDBOX_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(SANDBOX_OUTPUT_DIR, exist_ok=True)

# CHANGE 1: Reduced from 600 to 30 seconds
DEFAULT_SANDBOX_TIMEOUT = 30

_INPUT_MOCK = (
    "import builtins; "
    "builtins.input = lambda *a, **kw: (_ for _ in ()).throw("
    "RuntimeError('input() is disabled in sandbox'))\n"
)


def _insert_input_mock(script_text: str) -> str:
    """Insert the input()-disabling shim after any leading module docstring
    and/or `from __future__ import ...` line(s) — Python requires future
    imports to be the very first statement in a file (after only an
    optional docstring), so textually prepending the shim before all of
    that broke any script that legitimately started with one, with the
    real cause buried in stderr as an unrelated-looking SyntaxError."""
    try:
        tree = ast.parse(script_text)
        insert_line = 1  # 1-indexed line number to insert before
        for node in tree.body:
            is_future_import = isinstance(node, ast.ImportFrom) and node.module == "__future__"
            is_docstring = (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
            if is_future_import or is_docstring:
                insert_line = node.end_lineno + 1
                continue
            break
        lines = script_text.splitlines(keepends=True)
        return "".join(lines[:insert_line - 1]) + _INPUT_MOCK + "".join(lines[insert_line - 1:])
    except SyntaxError:
        # Can't parse — fall back to the old behavior rather than blocking
        # a script whose real syntax error should surface on its own.
        return _INPUT_MOCK + script_text

def run_sandbox_script(script_path: str, timeout: int = DEFAULT_SANDBOX_TIMEOUT, use_subprocess=True):
    if not os.path.exists(script_path):
        log_warning(f"Script not found: {script_path}")
        raise FileNotFoundError(f"Script not found: {script_path}")

    log_info(f"[SANDBOX] Executing script: {script_path}")

    if use_subprocess:
        env = os.environ.copy()
        env["TOKENIZERS_PARALLELISM"] = "false"

        try:
            # CHANGE 2: Insert input() mock so interactive scripts fail
            # immediately instead of hanging for the full timeout duration
            script_content = _insert_input_mock(open(script_path).read())

            result = subprocess.run(
                [sys.executable, "-c", script_content],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )

            # Always log stdout and stderr
            if result.stdout.strip():
                log_info(f"[SANDBOX] stdout:\n{result.stdout}")
            if result.stderr.strip():
                log_warning(f"[SANDBOX] stderr:\n{result.stderr}")

            if result.returncode != 0:
                raise RuntimeError(f"Sandbox script failed: {script_path}\n"
                                   f"stdout:\n{result.stdout}\n"
                                   f"stderr:\n{result.stderr}")

            log_info(f"[SANDBOX] Script executed successfully")
            return result.stdout

        except subprocess.TimeoutExpired:
            log_warning(f"[SANDBOX] Script timed out after {timeout} seconds")
            raise RuntimeError(f"Sandbox script timed out: {script_path}")
        except Exception as e:
            log_exception(e)
            raise RuntimeError(f"Sandbox script execution error: {e}")

    else:
        # Dynamic execution
        try:
            buf_out = io.StringIO()
            buf_err = io.StringIO()
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                spec = importlib.util.spec_from_file_location("sandbox_module", script_path)
                sandbox_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(sandbox_module)

            stdout_val = buf_out.getvalue()
            stderr_val = buf_err.getvalue()
            if stdout_val.strip():
                log_info(f"[SANDBOX] stdout:\n{stdout_val}")
            if stderr_val.strip():
                log_warning(f"[SANDBOX] stderr:\n{stderr_val}")

            log_info(f"[SANDBOX] Script loaded dynamically: {script_path}")
            return stdout_val

        except Exception as e:
            log_exception(e)
            raise RuntimeError(f"Dynamic sandbox execution failed: {e}")


# -----------------------------------------------------------------------
# --- Real kernel-isolated execution (F2, reused from self_edit_manager) -
# -----------------------------------------------------------------------
# run_sandbox_script()'s use_subprocess=True path above has full host
# filesystem/network access despite the "sandbox" name — the actual
# production execution paths (autonomous-loop baselines, LLM-generated
# experiments) need this instead: the same sandbox-exec + echo_sandbox.sb
# Seatbelt profile + safe_exec_wrapper.py mechanism self_edit_manager.py
# already runs self-edit candidates through, with safe_exec_wrapper.py's
# --mode=script so a target script's own `if __name__ == "__main__":`
# guard fires correctly (unlike --mode=import, built for import-testing).
_SANDBOX_ROOT = os.path.dirname(os.path.abspath(__file__))
_SANDBOX_PROFILE = os.path.join(_SANDBOX_ROOT, "echo_sandbox.sb")
_SANDBOX_WRAPPER = os.path.join(_SANDBOX_ROOT, "safe_exec_wrapper.py")


def run_sandbox_script_isolated(script_path: str, timeout: int = DEFAULT_SANDBOX_TIMEOUT) -> dict:
    """Run script_path under real kernel-level isolation.

    Returns {"success": bool, "output": str, "error": str|None, "duration": float}
    — never raises; callers check "success" instead of catching an exception,
    matching the richer contract the now-removed sandbox/runner.py used to
    provide (that file duplicated this job with a weaker, incompatible
    contract and no input-mock handling — consolidated here instead of kept
    as a second implementation).
    """
    import tempfile
    import time as _time

    start = _time.time()
    if not os.path.exists(script_path):
        log_warning(f"Script not found: {script_path}")
        return {"success": False, "output": "", "error": f"Script not found: {script_path}", "duration": 0.0}

    log_info(f"[SANDBOX-ISOLATED] Executing script: {script_path}")

    try:
        with tempfile.TemporaryDirectory(prefix="echo_sandbox_run_") as scratch:
            scratch_real = os.path.realpath(scratch)

            # Input mock: write a mocked copy inside scratch (writes there are
            # explicitly allowed by echo_sandbox.sb) rather than passing
            # content via -c, since this path needs a real file for the
            # kernel profile + wrapper to load.
            mocked_content = _insert_input_mock(open(script_path).read())
            mocked_path = os.path.join(scratch_real, "_script.py")
            with open(mocked_path, "w") as f:
                f.write(mocked_content)

            result = subprocess.run(
                ["sandbox-exec", "-f", _SANDBOX_PROFILE, "-D", f"SCRATCH={scratch_real}",
                 sys.executable, _SANDBOX_WRAPPER, scratch_real, mocked_path, "--mode=script"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )

        duration = round(_time.time() - start, 2)
        if result.stdout.strip():
            log_info(f"[SANDBOX-ISOLATED] stdout:\n{result.stdout}")
        if result.stderr.strip():
            log_warning(f"[SANDBOX-ISOLATED] stderr:\n{result.stderr}")

        if result.returncode == 0 and "SANDBOX_OK" in result.stdout:
            log_info("[SANDBOX-ISOLATED] Script executed successfully")
            return {"success": True, "output": result.stdout.strip(), "error": None, "duration": duration}
        return {
            "success": False,
            "output": result.stdout.strip(),
            "error": (result.stderr.strip() or "sandbox exited non-zero")[:2000],
            "duration": duration,
        }

    except subprocess.TimeoutExpired:
        log_warning(f"[SANDBOX-ISOLATED] Script timed out after {timeout} seconds")
        return {"success": False, "output": "", "error": f"Timed out after {timeout}s", "duration": round(_time.time() - start, 2)}
    except FileNotFoundError as e:
        # sandbox-exec binary missing (non-macOS, or a stripped-down host) —
        # fail closed, matching self_edit_manager.py's documented behavior
        # for this exact same failure mode.
        log_exception(e)
        return {"success": False, "output": "", "error": f"sandbox-exec unavailable: {e}", "duration": round(_time.time() - start, 2)}
    except Exception as e:
        log_exception(e)
        return {"success": False, "output": "", "error": str(e), "duration": round(_time.time() - start, 2)}


# -----------------------------
# --- Standalone Execution ---
# -----------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run a Python script in the sandbox.")
    parser.add_argument("script", help="Path to Python script")
    parser.add_argument("--timeout", type=int, default=DEFAULT_SANDBOX_TIMEOUT, help="Max execution time in seconds")
    parser.add_argument("--dynamic", action="store_true", help="Load script dynamically instead of subprocess")
    args = parser.parse_args()
    run_sandbox_script(args.script, timeout=args.timeout, use_subprocess=not args.dynamic)
