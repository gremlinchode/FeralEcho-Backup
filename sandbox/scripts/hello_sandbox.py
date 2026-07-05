"""
Hello Sandbox Script for Echo

Purpose:
- Demonstrates a safe, self-contained script Echo can run autonomously.
- Logs output to the sandbox logger.
- Captures all prints and errors.
- Configured for extended sandbox timeout.
- Integrates tool discovery for autonomous testing.
"""

import time
import os
import sys
from sandbox.logging_setup import log_info, log_warning

# Mitigate Hugging Face tokenizers fork warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configurable sandbox timeout in seconds
SANDBOX_TIMEOUT = 600

def main():
    try:
        log_info("Hello Sandbox: script started.")
        print("Hello Sandbox: script started (printed output)")

        # Smoke test: verify basic computation works in subprocess environment.
        # Tool discovery was removed — registrations in a subprocess die with
        # the process and accomplish nothing that persists in production.
        result = sum(i * i for i in range(10))
        log_info(f"Hello Sandbox: Computation result = {result}")
        print(f"Hello Sandbox: Computation result = {result}")

        time.sleep(1)

        log_info("Hello Sandbox: script finished successfully.")
        print("Hello Sandbox: script finished successfully (printed output)")

        return f"Computation result = {result}"

    except Exception as e:
        log_warning(f"Hello Sandbox: script encountered an error: {e}")
        print(f"Hello Sandbox encountered an exception: {e}", file=sys.stderr)
        return f"Error: {e}"

if __name__ == "__main__":
    try:
        output = main()
        print("Sandbox returned:\n", output)
    except Exception as e:
        print(f"Sandbox returned an exception: {e}", file=sys.stderr)

