"""Kernel jail for arm-generation processes (sandbox-exec). An arm process can read+write only its own root; it cannot read
the oracle, the frozen worlds, the hidden tests, or any other arm's root, and cannot write anywhere else. Network stays open (Ollama on localhost)."""
import os, subprocess
from .common import PYTHON

def profile(arm_root, exp_root):
    arm = os.path.realpath(arm_root); exp = os.path.realpath(exp_root)
    return ("(version 1)(allow default)(deny file-write*)"
            f'(allow file-write* (subpath "{arm}") (literal "/dev/null") (literal "/dev/dtracehelper"))'
            f'(deny file-read* (subpath "{exp}"))(allow file-read* (subpath "{arm}"))')

def run_jailed(argv, arm_root, exp_root, timeout, extra_env=None):
    env = {**os.environ, **(extra_env or {})}
    return subprocess.run(["sandbox-exec", "-p", profile(arm_root, exp_root), PYTHON, "-I", "-B"] + list(argv),
                          capture_output=True, text=True, timeout=timeout, env=env)
