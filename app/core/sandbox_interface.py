# app/core/sandbox_interface.py
from sandbox.run_script import run_sandbox_script
import os
import logging

SANDBOX_DIR = "sandbox/scripts"

def run_random_sandbox_script(timeout=10):
    """Pick a random script in the sandbox and run it."""
    scripts = [os.path.join(SANDBOX_DIR, f)
           for f in os.listdir(SANDBOX_DIR)
           if f.endswith(".py") and not f.startswith("temp_")]
    if not scripts:
        logging.warning("No scripts found in sandbox.")
        return None

    import random
    script = random.choice(scripts)
    logging.info(f"Echo is running sandbox script: {script}")
    output = run_sandbox_script(script, timeout=timeout)
    return output

