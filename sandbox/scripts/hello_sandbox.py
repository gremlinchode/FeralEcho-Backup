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
from app.core.awareness_tools_integration import discover_and_register_tools

# Mitigate Hugging Face tokenizers fork warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configurable sandbox timeout in seconds
SANDBOX_TIMEOUT = 600  # increased from 10s to 600s

def main():
    try:
        log_info("Hello Sandbox: script started.")
        print("Hello Sandbox: script started (printed output)")

        # Let Echo discover tools dynamically in the app/tools directory
        registered = discover_and_register_tools("app/core")
        log_info(f"Hello Sandbox: discovered and registered {registered} tools.")
        print(f"Discovered and registered {registered} tools in sandbox.")
        # Example of a small computation
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

