# sandbox/run_script.py
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

def run_sandbox_script(script_path: str, timeout: int = DEFAULT_SANDBOX_TIMEOUT, use_subprocess=True):
    if not os.path.exists(script_path):
        log_warning(f"Script not found: {script_path}")
        raise FileNotFoundError(f"Script not found: {script_path}")

    log_info(f"[SANDBOX] Executing script: {script_path}")

    if use_subprocess:
        env = os.environ.copy()
        env["TOKENIZERS_PARALLELISM"] = "false"

        try:
            # CHANGE 2: Prepend input() mock so interactive scripts fail
            # immediately instead of hanging for the full timeout duration
            input_mock = (
                "import builtins; "
                "builtins.input = lambda *a, **kw: (_ for _ in ()).throw("
                "RuntimeError('input() is disabled in sandbox'))\n"
            )
            script_content = input_mock + open(script_path).read()

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
