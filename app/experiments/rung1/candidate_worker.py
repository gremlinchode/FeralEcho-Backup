#!/usr/bin/env python3
"""
Rung-1 Stage E0/E0.1 -- untrusted candidate worker.

Runs INSIDE the sandboxed subprocess launched by trusted_evaluator.py, as
its own separate OS process. It never receives, and has no code path
capable of receiving, the expected output for any test case --
trusted_evaluator.py never writes the expected value anywhere this
process, its scratch directory, or its environment can reach; the
expected value lives only in a local Python variable inside
trusted_evaluator.run_case(), in a wholly separate process, and the
comparison happens there, after this process has already exited.

Invocation: argv = [candidate_path, function_name]. One line of JSON on
stdin: {"args": [<arg0>, <arg1>, ...]}.

Prints EXACTLY one line to the real stdout, and nothing else, after
candidate execution has completed:
    {"status": "ok", "value": <json-serializable return value>}
    {"status": "candidate_error", "stage": "exec"|"lookup"|"call", "error_type": "<ClassName>"}
    {"status": "malformed_result", "error_type": "<ClassName>"}

Real stderr is left connected -- the trusted controller captures it
separately as researcher-only diagnostic evidence and NEVER parses it for
the trusted PASS/FAIL/CORRECT/INCORRECT decision, which is computed
exclusively from the single stdout JSON line above.

Structural guarantee against a candidate faking its own success line or
smuggling a print()-based leak: the candidate's own code (both its
top-level statements during exec() and any call made to the requested
function) runs with the real OS-level file descriptor 1 (stdout)
temporarily dup2()'d to /dev/null. This is a file-descriptor-level
redirect, not a Python-object-level one (`sys.stdout = ...`) -- a
candidate that reassigns sys.stdout back to sys.__stdout__ during its own
top-level code still writes through a TextIOWrapper backed by fd 1, and
fd 1 itself is remapped to /dev/null for the whole duration of exec()/the
function call regardless of what the candidate does to the Python-level
sys.stdout object. This has been demonstrated against the specific
attacks in scripts/verify_rung1_e0_trusted_evaluator.py (a top-level
reassignment-and-print, and a direct write to a candidate-side duplicate
of the real fd) -- it is not a formal proof against every conceivable
descriptor-level or OS-level technique, and worker machinery and
candidate code still share one process and one address space; nothing
here creates a second in-process trust boundary. The real protection this
worker exists to support is that the trusted parent treats every field of
this file's stdout as an UNTRUSTED, parsed observation of the child's
computation, never as a self-authenticating verdict.

sys.stdout is explicitly flushed both immediately before the redirect
begins and immediately after candidate execution ends but before fd 1 is
restored -- without this, Python's own userspace output buffer could hold
candidate-authored bytes that get flushed later, after fd 1 has already
been restored to the real pipe, which would leak them regardless of the
fd-level redirect. This exact flush-before-restore requirement was
verified necessary during this file's own construction, not assumed.

(E0.1) Candidate top-level execution and the requested function call are
now wrapped in `except BaseException`, not `except Exception`. This is a
deliberate, narrow widening, scoped to exactly these two call sites: a
candidate calling `sys.exit(N)` (which raises SystemExit, a BaseException
subclass Exception does not catch) previously propagated out of this
worker entirely, causing the process to exit with a real nonzero status
that the trusted parent had no way to distinguish from a genuine sandbox-
launch failure -- independently reproduced and confirmed before this fix
(see the Stage E0.1 implementation report's "before/after" section).
SystemExit and KeyboardInterrupt raised by CANDIDATE code are now caught
here and reported through the same structured "candidate_error" envelope
every ordinary Exception already used -- closing the misclassification at
its root, in the untrusted process, rather than asking the trusted parent
to guess a cause from an exit code alone. This does not, and cannot,
catch every possible way a process can terminate: a candidate calling
os._exit() (which invokes the C-level _exit() syscall directly, bypassing
all Python exception machinery) or a genuine interpreter-level fault
still terminates this process with no chance to run any Python code at
all, including this except block -- those residual cases are handled
honestly, as an explicitly uncertain-cause outcome, on the trusted
parent's side (see trusted_evaluator.py's CHILD_TERMINATED_UNVERIFIED).

Exception messages and tracebacks are never printed anywhere by this file
-- only the exception's class NAME crosses back to the controller. A
candidate cannot leak anything through a crafted exception message,
because the message is never read by anything downstream of this file.
"""
import contextlib
import io
import json
import os
import sys


def _run_with_stdout_suppressed(fn, *args):
    """Run fn(*args) with the real fd 1 pointed at /dev/null for the
    duration of the call. Restores fd 1 unconditionally afterward, even on
    exception. See module docstring for why this must be fd-level, not
    sys.stdout-level, and why the explicit flushes are required."""
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    real_stdout_fd = os.dup(1)
    try:
        sys.stdout.flush()
        os.dup2(devnull_fd, 1)
        try:
            return fn(*args)
        finally:
            sys.stdout.flush()  # flush whatever the candidate wrote -- lands in devnull, not the real pipe
    finally:
        os.dup2(real_stdout_fd, 1)
        os.close(real_stdout_fd)
        os.close(devnull_fd)


def _emit(payload: dict) -> None:
    """The ONLY function in this file allowed to write to the real,
    restored stdout. Always called after _run_with_stdout_suppressed has
    already returned/raised and fd 1 has been restored."""
    print(json.dumps(payload), flush=True)


def main() -> int:
    if len(sys.argv) != 3:
        _emit({"status": "malformed_result", "error_type": "BadInvocation"})
        return 0
    candidate_path, fn_name = sys.argv[1], sys.argv[2]

    try:
        raw_line = sys.stdin.readline()
        call_args = json.loads(raw_line)["args"]
        if not isinstance(call_args, list):
            raise ValueError("args must be a list")
    except Exception:
        _emit({"status": "malformed_result", "error_type": "BadInputEncoding"})
        return 0

    try:
        with open(candidate_path, "r", encoding="utf-8") as f:
            candidate_source = f.read()
    except Exception:
        _emit({"status": "malformed_result", "error_type": "CandidateUnreadable"})
        return 0

    # Fresh, isolated namespace -- never shared with anything holding a
    # protected value (there is none in this process at all; this
    # isolation is defense-in-depth, not the primary guarantee here).
    ns: dict = {}

    def _do_exec():
        exec(compile(candidate_source, "<candidate>", "exec"), ns, ns)

    try:
        _run_with_stdout_suppressed(_do_exec)
    except BaseException as e:  # (E0.1) widened from Exception -- see module docstring
        _emit({"status": "candidate_error", "stage": "exec", "error_type": type(e).__name__})
        return 0

    fn = ns.get(fn_name)
    if not callable(fn):
        _emit({"status": "candidate_error", "stage": "lookup", "error_type": "FunctionNotFound"})
        return 0

    try:
        result = _run_with_stdout_suppressed(fn, *call_args)
    except BaseException as e:  # (E0.1) widened from Exception -- see module docstring
        _emit({"status": "candidate_error", "stage": "call", "error_type": type(e).__name__})
        return 0

    try:
        payload = json.dumps({"status": "ok", "value": result})
    except Exception:
        _emit({"status": "malformed_result", "error_type": "Unserializable"})
        return 0

    print(payload, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
