# app/core/sandbox_interface.py
from sandbox.run_script import run_sandbox_script_isolated
import os
import logging

SANDBOX_DIR = "sandbox/scripts"

def run_random_sandbox_script(timeout=10):
    """Pick a random script in the sandbox and run it.

    Runs under real kernel-level isolation (sandbox-exec + echo_sandbox.sb)
    instead of a bare subprocess with full host access — previously this
    was the one production call site actually flagged for the gap, though
    two other independent unisolated implementations (sandbox/runner.py,
    sandbox/experiment_runner.py) turned out to share it; all three now
    route through the same isolated helper.
    """
    scripts = [os.path.join(SANDBOX_DIR, f)
           for f in os.listdir(SANDBOX_DIR)
           if f.endswith(".py") and not f.startswith("temp_")]
    if not scripts:
        logging.warning("No scripts found in sandbox.")
        return None

    import random
    script = random.choice(scripts)
    logging.info(f"Echo is running sandbox script: {script}")
    result = run_sandbox_script_isolated(script, timeout=timeout)
    if not result["success"]:
        logging.warning(f"[SANDBOX] {script} failed: {result['error']}")
        return None
    return result["output"]

