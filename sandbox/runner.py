"""
Sandbox Runner

Purpose:
- Safely execute scripts in the sandbox/scripts directory.
- Capture stdout/stderr output and send it to both console and sandbox logs.
- Enforce timeouts and return structured results.
"""

import subprocess
import sys
import os
import traceback
import time
from sandbox.logging_setup import log_info, log_warning, log_error, log_exception, close_handlers

# Path to sandbox scripts
SANDBOX_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")

def run_sandbox_script(script_name: str, timeout: int = 1200):
    """
    Execute a script inside the sandbox/scripts directory.
    Returns a dict containing:
        - success (bool)
        - output (str)
        - error (str or None)
        - duration (float)
    """
    start_time = time.time()
    script_path = os.path.join(SANDBOX_SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        log_error(f"Sandbox script not found: {script_path}")
        return {"success": False, "error": "Script not found", "output": "", "duration": 0.0}

    try:
        log_info(f"[SANDBOX] Starting script: {script_name}")

        # Run script in subprocess for isolation
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=SANDBOX_SCRIPTS_DIR,
            env={**os.environ, "TOKENIZERS_PARALLELISM": "false"},
        )

        stdout, stderr = process.communicate(timeout=timeout)
        duration = round(time.time() - start_time, 2)

        if process.returncode == 0:
            log_info(f"[SANDBOX] Script {script_name} completed successfully in {duration}s")
            if stdout.strip():
                log_info(f"[SANDBOX OUTPUT]\n{stdout.strip()}")
            return {"success": True, "output": stdout.strip(), "error": None, "duration": duration}
        else:
            log_warning(f"[SANDBOX] Script {script_name} exited with code {process.returncode}")
            if stderr.strip():
                log_warning(f"[SANDBOX STDERR]\n{stderr.strip()}")
            return {"success": False, "output": stdout.strip(), "error": stderr.strip(), "duration": duration}

    except subprocess.TimeoutExpired:
        log_warning(f"[SANDBOX] Script {script_name} timed out after {timeout}s")
        return {"success": False, "output": "", "error": "Timeout expired", "duration": timeout}

    except Exception as e:
        log_exception(e)
        traceback_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        return {"success": False, "output": "", "error": traceback_str, "duration": round(time.time() - start_time, 2)}

    finally:
        # Ensure log handlers are closed properly
        close_handlers()

# Optional standalone test
if __name__ == "__main__":
    result = run_sandbox_script("hello_sandbox.py")
    print("\nResult:", result)

