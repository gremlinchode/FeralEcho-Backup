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

# No sandbox.logging_setup import here on purpose: that module writes to
# sandbox/logs/sandbox_execution.log, which sits outside this script's
# scratch directory once it runs under the real Seatbelt-isolated path
# (run_sandbox_script_isolated()) — a sandboxed child process writing its
# own log file is exactly the kind of write-outside-scratch the isolation
# exists to block, so it correctly fails closed with PermissionError there.
# stdout (every line below) is captured and logged by the *caller*, running
# outside the sandbox boundary, the same way self_edit_manager.py's sandbox
# calls already work — this script only needs print().

# Mitigate Hugging Face tokenizers fork warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configurable sandbox timeout in seconds
SANDBOX_TIMEOUT = 600

def main():
    try:
        print("Hello Sandbox: script started (printed output)")

        # Smoke test: verify basic computation works in subprocess environment.
        # Tool discovery was removed — registrations in a subprocess die with
        # the process and accomplish nothing that persists in production.
        result = sum(i * i for i in range(10))
        print(f"Hello Sandbox: Computation result = {result}")

        time.sleep(1)

        print("Hello Sandbox: script finished successfully (printed output)")

        return f"Computation result = {result}"

    except Exception as e:
        print(f"Hello Sandbox encountered an exception: {e}", file=sys.stderr)
        return f"Error: {e}"

if __name__ == "__main__":
    try:
        output = main()
        print("Sandbox returned:\n", output)
    except Exception as e:
        print(f"Sandbox returned an exception: {e}", file=sys.stderr)

