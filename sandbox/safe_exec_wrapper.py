"""
sandbox/safe_exec_wrapper.py — F2 filesystem-isolated sandbox (Option A).

Patches builtins before loading the module under test so that any write
operation targeting a path outside SCRATCH_DIR raises PermissionError.
The subprocess exits non-zero; the caller treats that as a sandbox failure.

Usage (called by self_edit_manager.py):
    python3 sandbox/safe_exec_wrapper.py <SCRATCH_DIR> <MODULE_PATH> [--mode=import|script]

--mode=import (default, unchanged): loads MODULE_PATH via spec_from_file_location
with a synthetic module name — used to *test whether code is importable*
without treating it as a runnable script. This is what self_edit_manager.py's
two call sites use and their behavior is untouched by this flag's addition.

--mode=script: loads MODULE_PATH with module name "__main__" instead, so a
target script's own `if __name__ == "__main__":` guard actually fires — used
by sandbox/run_script.py's run_sandbox_script_isolated() to run arbitrary
scripts (autonomous-loop baselines, LLM-generated experiments) the same way
`python script.py` would, but under this file's write-blocking patches plus
the kernel-level Seatbelt profile (echo_sandbox.sb) the caller wraps this
process in.

--mode=apply_to_code -- <input_path> <output_path>: PENDING_DECISIONS.md #7
(CLAUDE.md Finding 41 B3), added 2026-07-22. Loads MODULE_PATH (the real
deployed self_edit_generated.py) and calls its apply_to_code(code) with the
real candidate code read from <input_path>, writing the real string result
to <output_path> — both paths must live inside SCRATCH_DIR, same as every
other write this wrapper allows. Replaces self_edit_manager.py's prior
in-process ThreadPoolExecutor + soft 2s timeout, which could not actually
kill a hung/malicious hook (Python threads aren't forcibly killable) —
the abandoned thread kept running after the timeout fired, past the point
the in-process write-guard had already been torn down. Running this call
as its own subprocess under the real kernel Seatbelt profile means a
caller-side subprocess.run(timeout=...) genuinely SIGKILLs the whole
process on timeout, not just abandons a thread — closing the gap at its
root rather than hardening the same soft mechanism further. Also gives
the write-block itself real OS-level enforcement (the existing patches
below) instead of the temporary, additional in-process monkeypatch
self_edit_manager.py used to install and tear down around just this call.

--mode=functional_verify -- <output_path>: Phase 1 functional quality
signal (audits/2026-09-06_phase1_functional_quality_signal.md), added
2026-09-06. Deliberately not wired into any live call site — see that
report for scope and status. Loads MODULE_PATH (a self-edit-candidate-
shaped file, already staged by the caller) and, after it imports
successfully, enumerates every top-level function and class *defined in
this module* (obj.__module__ == the loaded module's own synthetic name —
excludes anything the candidate merely imports, e.g. Counter/defaultdict),
smoke-tests each with a minimal synthetic call (0 required params -> call
with none; exactly 1 required param -> call with the string "test",
matching the existing --mode=apply_to_code smoke-test convention already
established just above; 2+ required params -> recorded as
skipped_unsupported_signature rather than guessed, since guessing multiple
argument values has a high false-positive risk this mode is not designed
to absorb). Every call is individually wrapped in its own try/except, so a
raise is captured as structured data, never an uncaught subprocess crash —
SANDBOX_OK is still printed on harness success regardless of whether any
individual smoke-tested call raised. Writes a JSON summary
({"tested": [{"name", "kind", "outcome", "error"}], "any_tested": bool,
"any_raised": bool}) to <output_path>. This intentionally does NOT test
class methods individually, only module-level callables and bare class
construction — a stated scope limit, not an oversight (see the report's
"Environmental limitations" section). This also intentionally does not
attempt to verify semantic correctness against any external spec — no
such spec exists per self-edit family today, and inventing one was
explicitly out of scope for this phase. It answers exactly one question:
does this candidate's own top-level code raise when invoked with a
generic, non-adversarial input — the same question that would have
caught the real, already-diagnosed undefined-CodeGenerator-reference bug
in the currently-deployed self_edit_generated.py.

Patches applied before exec_module():
  builtins.open / io.open / _io.open   — all Python-level open() entry points
  io.FileIO / io.RawIOBase             — C file descriptor wrappers
  pathlib.Path.open                    — write_text / write_bytes path
  os.open                              — low-level fd open (O_WRONLY etc.)
  os.rename / os.replace / os.link / os.symlink / os.unlink
                                       — block two-step rename attacks
  os.fork                              — block child-process escape from patches
  os.system / os.popen / os.execv*    — unconditionally blocked
  subprocess.*                         — unconditionally blocked
  shutil copy/move/rmtree/copytree    — unconditionally blocked
  importlib.reload                     — blocks patch-undoing via reload
  ctypes.CDLL / ctypes.cdll / cffi    — blocks direct libc syscall access
  sys.stdin                            — replaced with _BlockedStdin (see below)

── stdin policy (audits/2026-09-09_f2_stdin_enforcement_boundary.md, Mission 27/28) ──
Autonomous sandboxed execution has no interactive stdin, established as
project-level practice at multiple prompt-construction sites (CLAUDE.md,
Mission 25) and enforced here at the one shared layer every real caller of
this wrapper already routes through (echo_projects.py's F2, self_edit_
manager.py's F2/apply_to_code, sandbox/run_script.py's two functions and
their five further downstream callers) — Mission 27 traced all of them and
found none legitimately needs real stdin. sys.stdin is replaced with
_BlockedStdin, a minimal io.TextIOBase subclass overriding only read(),
readline(), and readlines() to raise PermissionError with this file's own
existing "[SANDBOX] ..." convention (matching every other blocked
operation here, not run_script.py's separate RuntimeError-based
_insert_input_mock() precedent in a different file). readline()'s override
alone is sufficient to also cover next(sys.stdin)/iteration, since
io.IOBase's own inherited __next__ calls self.readline() internally —
verified directly, not assumed. input() is covered transparently too, with
no separate builtins.input patch: CPython's input() calls
sys.stdin.readline() whenever sys.stdin is not the interpreter's original
object, verified directly. isatty()/fileno()/readable()/seekable()/
writable()/encoding/errors/newlines/closed/flush()/close()/context-manager
support are all deliberately left at io.TextIOBase's own inherited
defaults (False/UnsupportedOperation/None/no-op as appropriate) rather
than reimplemented — each already produces an honest answer for a
non-functional stream with zero extra code, and overriding them further
would risk accidentally emulating a real terminal rather than truthfully
reporting there isn't one.

sandbox/run_script.py's _insert_input_mock() (a source-text insertion
mocking builtins.input only, covering two of run_script.py's own callers)
is intentionally left in place, unmodified, as harmless defense-in-depth —
it will simply never trigger once sys.stdin.readline() fails first.
Whether to simplify or remove it later is a separate, future decision, not
part of this change.
"""

import builtins as _builtins
import io
import os as _os
import sys


def _make_safe_open(scratch_abs: str, original_open):
    def _safe_open(file, mode="r", *args, **kwargs):
        mode_str = str(mode)
        if any(c in mode_str for c in "wax+"):
            abs_file = _os.path.abspath(str(file))
            if abs_file != scratch_abs and not abs_file.startswith(scratch_abs + _os.sep):
                raise PermissionError(
                    f"[SANDBOX] Write blocked outside scratch dir: {abs_file!r}"
                )
        return original_open(file, mode, *args, **kwargs)
    return _safe_open


def _make_safe_os_open(scratch_abs: str, original_os_open):
    _WRITE_FLAGS = _os.O_WRONLY | _os.O_RDWR | _os.O_CREAT | _os.O_TRUNC | _os.O_APPEND
    def _safe_os_open(path, flags, mode=0o777, *, dir_fd=None):
        if flags & _WRITE_FLAGS:
            if dir_fd is not None:
                raise PermissionError(
                    "[SANDBOX] os.open with dir_fd + write flags blocked"
                )
            abs_path = _os.path.abspath(str(path))
            if abs_path != scratch_abs and not abs_path.startswith(scratch_abs + _os.sep):
                raise PermissionError(
                    f"[SANDBOX] os.open write blocked outside scratch dir: {abs_path!r}"
                )
        if dir_fd is not None:
            return original_os_open(path, flags, mode, dir_fd=dir_fd)
        return original_os_open(path, flags, mode)
    return _safe_os_open


def _make_safe_path_open(scratch_abs: str, original_path_open):
    """
    Patch pathlib.Path.open — write_text / write_bytes call this method,
    which in CPython 3.10+ calls io.open directly rather than builtins.open.
    """
    def _safe_path_open(self, mode="r", *args, **kwargs):
        mode_str = str(mode)
        if any(c in mode_str for c in "wax+"):
            abs_f = _os.path.abspath(str(self))
            if abs_f != scratch_abs and not abs_f.startswith(scratch_abs + _os.sep):
                raise PermissionError(
                    f"[SANDBOX] pathlib write blocked outside scratch dir: {abs_f!r}"
                )
        return original_path_open(self, mode, *args, **kwargs)
    return _safe_path_open


def _make_safe_rename(scratch_abs: str, original_rename):
    """Block os.rename / os.replace to prevent write-to-temp-then-rename attacks."""
    def _safe_rename(src, dst, *args, **kwargs):
        abs_dst = _os.path.abspath(str(dst))
        if abs_dst != scratch_abs and not abs_dst.startswith(scratch_abs + _os.sep):
            raise PermissionError(
                f"[SANDBOX] rename/replace to outside scratch dir blocked: {abs_dst!r}"
            )
        return original_rename(src, dst, *args, **kwargs)
    return _safe_rename


def _blocked(*args, **kwargs):
    raise PermissionError("[SANDBOX] Call unconditionally blocked in sandbox")


class _BlockedStdin(io.TextIOBase):
    """Replaces sys.stdin inside the sandboxed subprocess. Only read()/
    readline()/readlines() are overridden — everything else (isatty(),
    fileno(), readable(), seekable(), writable(), encoding, errors,
    newlines, closed, flush(), close(), context-manager support) is left
    at io.TextIOBase's own inherited defaults, which are already honest
    for a non-functional stream (isatty()->False, fileno()->
    UnsupportedOperation, readable()/seekable()/writable()->False,
    flush()/close()->no-op) without any code here. readline()'s override
    alone also covers next(sys.stdin)/iteration and, transparently,
    input() itself — see the module docstring's stdin-policy section for
    why, verified directly rather than assumed."""

    def read(self, size=-1):
        raise PermissionError(
            "[SANDBOX] stdin.read() blocked — autonomous sandboxed execution has no interactive stdin"
        )

    def readline(self, size=-1):
        raise PermissionError(
            "[SANDBOX] stdin.readline() blocked — autonomous sandboxed execution has no interactive stdin"
        )

    def readlines(self, hint=-1):
        raise PermissionError(
            "[SANDBOX] stdin.readlines() blocked — autonomous sandboxed execution has no interactive stdin"
        )


def _install_patches(scratch: str) -> None:
    scratch_abs = _os.path.abspath(scratch)

    # ── GUI/display isolation (CLAUDE.md Finding 24, fixed 2026-07-15) ────────
    # Neither this wrapper nor echo_sandbox.sb previously scoped GUI/display
    # access — a real generated experiment (sandbox/experiments/exp_20260706_
    # 004311.py) called matplotlib.pyplot.show(), which opened a real
    # on-screen window (matplotlib here defaults to the interactive macosx
    # backend). echo_sandbox.sb's (allow mach-lookup) is required for normal
    # Python/objc runtime internals and is the same Mach IPC channel that
    # reaches the WindowServer, so it can't be narrowed without an unreliable
    # per-service allowlist — the reliable fix is at the Python layer, same
    # pattern as the network-module stubs below. MPLBACKEND is read by
    # matplotlib at import time, before any of its own code runs, so setting
    # it here (not matplotlib.use(), which only works if called before
    # matplotlib.pyplot is imported by the *candidate*, not guaranteed) covers
    # every import order. GUI toolkits are stubbed the same way _SAFETY_HEADER
    # already stubs network modules.
    _os.environ["MPLBACKEND"] = "Agg"
    for _gui_mod in ("tkinter", "_tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx"):
        sys.modules.setdefault(_gui_mod, None)

    # ── matplotlib config/cache directory (found 2026-09-05, echo_projects
    # capability-ceiling investigation) ─────────────────────────────────────
    # MPLBACKEND=Agg above correctly avoids a real GUI window (Finding 24's
    # own concern), but matplotlib.__init__._get_config_or_cache_dir() still
    # runs at import time REGARDLESS of backend, defaulting to a real
    # tempfile.mkdtemp() call outside this sandbox's writable scratch dir —
    # blocked, raising before the candidate's own code ever executes.
    # Confirmed as a real, currently-live failure, not theoretical: measured
    # directly against echo_projects's own historical record
    # (sandbox/echo_projects/*/_report.md) — every F2 failure whose traceback
    # bottoms out in matplotlib/__init__.py:_get_config_or_cache_dir is this
    # exact gap, and matplotlib is a common real import choice for that
    # pipeline's data-visualization-themed generated projects. Fixed the same
    # way MPLBACKEND already is: point MPLCONFIGDIR at a real, writable
    # subdirectory of this call's own scratch dir, so matplotlib's cache
    # init succeeds fully inside the sandbox's existing write boundary
    # instead of needing a new one.
    _mpl_config_dir = _os.path.join(scratch_abs, ".mplconfig")
    try:
        _os.makedirs(_mpl_config_dir, exist_ok=True)
        _os.environ["MPLCONFIGDIR"] = _mpl_config_dir
    except Exception:
        pass  # fail open -- matplotlib import will fail the same way it did before this fix, not worse

    # ── OpenMP / KMP duplicate-library guard (differential audit, 2026-07-20/21) ──
    # Mirrors run.py's own startup guard (CLAUDE.md's "OpenMP / KMP startup
    # guard" section). Not confirmed as the cause of the one KMP-signature crash
    # found in this session's audit — cheap, harmless insurance either way: these
    # vars only affect how numpy/faiss/MKL register their OpenMP runtime, and
    # this subprocess can load self-edit candidates that import any of them.
    _os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    _os.environ.setdefault("OMP_NUM_THREADS", "1")
    _os.environ.setdefault("MKL_NUM_THREADS", "1")

    # ── Phase 1: pre-import all stdlib modules we'll patch ────────────────────
    # Some modules run C-level initialization (ctypes builds pythonapi via
    # _ctypes.dlopen, shutil uses io.RawIOBase, etc.) that must complete
    # BEFORE we replace any C-level primitives.  Import first, patch after.
    import io          as _io
    import pathlib     as _pathlib
    import subprocess  as _sub
    import shutil      as _shutil
    import importlib   as _importlib

    try:
        import _io         as _c_io
    except ImportError:
        _c_io = None

    try:
        import posix       as _posix
    except ImportError:
        _posix = None

    try:
        import _posixsubprocess as _pss
    except ImportError:
        _pss = None

    # ctypes init calls _ctypes.dlopen(None) to build pythonapi — must complete
    # before we block dlopen.
    try:
        import ctypes  as _ctypes_mod
        import _ctypes as _c_ctypes
    except ImportError:
        _ctypes_mod = None
        _c_ctypes   = None

    try:
        import cffi    as _cffi
    except ImportError:
        _cffi = None

    # ── Phase 2: build helper objects ─────────────────────────────────────────
    safe_open      = _make_safe_open(scratch_abs, _builtins.open)
    safe_os_open   = _make_safe_os_open(scratch_abs, _os.open)
    safe_rename    = _make_safe_rename(scratch_abs, _os.rename)
    safe_replace   = _make_safe_rename(scratch_abs, _os.replace) if hasattr(_os, "replace") else _blocked

    # ── Phase 3: patch everything ──────────────────────────────────────────────

    # open() at every Python entry point
    _builtins.open = safe_open
    _io.open       = safe_open
    if _c_io:
        try: _c_io.open = safe_open
        except AttributeError: pass

    # io.FileIO — C class; subclass so stdlib can still inherit from the original
    try:
        _orig_FileIO = _io.FileIO
        class _SafeFileIO(_orig_FileIO):
            def __init__(self, file, mode="r", closefd=True, opener=None):
                if any(c in str(mode) for c in "wax+"):
                    abs_f = _os.path.abspath(str(file))
                    if abs_f != scratch_abs and not abs_f.startswith(scratch_abs + _os.sep):
                        raise PermissionError(
                            f"[SANDBOX] io.FileIO write blocked: {abs_f!r}"
                        )
                if opener is not None:
                    super().__init__(file, mode, closefd, opener)
                else:
                    super().__init__(file, mode, closefd)
        _io.FileIO = _SafeFileIO
        if _c_io:
            try: _c_io.FileIO = _SafeFileIO
            except AttributeError: pass
    except (AttributeError, TypeError):
        pass

    # pathlib.Path.open — write_text / write_bytes entry point
    _pathlib.Path.open = _make_safe_path_open(scratch_abs, _pathlib.Path.open)

    # os.* and posix.* (C backing) — patch both in parallel
    _os.open = safe_os_open
    if hasattr(_os, "rename"):  _os.rename  = safe_rename
    if hasattr(_os, "replace"): _os.replace = safe_replace
    for attr in ("fork", "system", "popen", "execv", "execve", "execvp", "execvpe",
                 "spawnl", "spawnle", "spawnlp", "spawnlpe", "link", "symlink"):
        if hasattr(_os, attr): setattr(_os, attr, _blocked)

    if _posix:
        try:
            safe_posix_open = _make_safe_os_open(scratch_abs, _posix.open)
            _posix.open = safe_posix_open
            if hasattr(_posix, "rename"):  _posix.rename  = _make_safe_rename(scratch_abs, _posix.rename)
            if hasattr(_posix, "replace"): _posix.replace = _make_safe_rename(scratch_abs, _posix.replace)
            for attr in ("fork", "system", "execv", "execve", "execvp", "execvpe",
                         "link", "symlink", "unlink"):
                if hasattr(_posix, attr): setattr(_posix, attr, _blocked)
        except AttributeError:
            pass

    # subprocess
    for attr in ("run", "call", "Popen", "check_call", "check_output",
                 "getoutput", "getstatusoutput"):
        setattr(_sub, attr, _blocked)

    # _posixsubprocess — C-level backing for subprocess.Popen
    if _pss:
        try:
            if hasattr(_pss, "fork_exec"): _pss.fork_exec = _blocked
        except AttributeError: pass

    # shutil
    for attr in ("copy", "copy2", "copyfile", "copyfileobj", "move", "rmtree", "copytree"):
        setattr(_shutil, attr, _blocked)

    # importlib.reload
    _importlib.reload = _blocked

    # ctypes / cffi — block AFTER ctypes is fully initialized (pythonapi already built)
    if _ctypes_mod:
        try:
            _ctypes_mod.CDLL          = _blocked
            _ctypes_mod.cdll          = _blocked
            _ctypes_mod.LibraryLoader = _blocked
        except AttributeError: pass
    if _c_ctypes:
        try:
            if hasattr(_c_ctypes, "dlopen"):       _c_ctypes.dlopen       = _blocked
            if hasattr(_c_ctypes, "LoadLibrary"):  _c_ctypes.LoadLibrary  = _blocked
        except AttributeError: pass
    if _cffi:
        try: _cffi.FFI = _blocked
        except AttributeError: pass

    # ── stdin policy (Mission 27/28, audits/2026-09-09_f2_stdin_enforcement_boundary.md) ──
    # Applied unconditionally, like every other patch above -- not gated on
    # --mode=, matching the fact that no real caller of this wrapper (traced
    # exhaustively in Mission 27) legitimately needs real stdin under any
    # mode. See the module docstring's stdin-policy section for the full
    # design rationale.
    sys.stdin = _BlockedStdin()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: safe_exec_wrapper.py <SCRATCH_DIR> <MODULE_PATH> [--mode=import|script]", file=sys.stderr)
        sys.exit(1)

    scratch_dir = sys.argv[1]
    module_path = sys.argv[2]

    # Optional --mode= flag anywhere after the two positional args, plus
    # everything after a bare "--" is passed through as the target script's
    # own sys.argv (only meaningful in --mode=script).
    _mode = "import"
    _extra_argv: list = []
    _rest = sys.argv[3:]
    if "--" in _rest:
        _split = _rest.index("--")
        _flags, _extra_argv = _rest[:_split], _rest[_split + 1:]
    else:
        _flags = _rest
    for _flag in _flags:
        if _flag.startswith("--mode="):
            _mode = _flag.split("=", 1)[1]
    if _mode not in ("import", "script", "apply_to_code", "functional_verify"):
        print(f"Unknown --mode={_mode!r}, expected 'import', 'script', 'apply_to_code', or 'functional_verify'", file=sys.stderr)
        sys.exit(1)
    if _mode == "apply_to_code" and len(_extra_argv) < 2:
        print("--mode=apply_to_code requires -- <input_path> <output_path>", file=sys.stderr)
        sys.exit(1)
    if _mode == "functional_verify" and len(_extra_argv) < 1:
        print("--mode=functional_verify requires -- <output_path>", file=sys.stderr)
        sys.exit(1)

    # This script is invoked directly (`sys.executable safe_exec_wrapper.py
    # ...`), not via `python -m`, so Python's default sys.path[0] is this
    # file's own directory (sandbox/), not the project root — any candidate
    # that imports a real project module (`import app.core.memory_bridge`,
    # `import app.mlx_handler`, etc., all legitimately allowed by
    # self_edit_manager.py's _ALLOWED_TOP_LEVEL) failed here with
    # ModuleNotFoundError: No module named 'app', regardless of whether the
    # code was otherwise correct. Adding the real project root fixes that.
    # Not a new safety gap: self_edit_manager.py's _validate_imports() (F1,
    # runs before this sandbox stage) already blocks the dangerous
    # self-referential imports (self_edit_manager, echo_optuna,
    # self_edit_generated) regardless of what's importable here, and the
    # write-blocking patches installed below are unaffected by sys.path.
    _project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

    # Gap-closure plan (2026-07-23): app/core/echo_projects.py's multi-file
    # pipeline needs flat sibling imports (`import helper`) to resolve when
    # main.py and helper.py are staged side-by-side in scratch_dir. Appended,
    # NOT inserted at position 0 -- inserting first would let a same-named
    # generated file (e.g. a generated requests.py) shadow a real,
    # not-yet-imported third-party package for the rest of this subprocess.
    # Already-patched stdlib modules (os/subprocess/shutil/etc.) are
    # pre-imported and cached in sys.modules by name before this point, so
    # they can't be shadowed either way regardless of position -- append-only
    # fallback resolution only matters for allowed-but-not-yet-imported
    # third-party names, which is exactly the case this needs to be safe for.
    if scratch_dir not in sys.path:
        sys.path.append(scratch_dir)

    _install_patches(scratch_dir)

    import importlib.util
    if _mode == "script":
        # Real module name "__main__" so `if __name__ == "__main__":` guards
        # in the target script fire, matching real `python script.py`
        # semantics (confirmed necessary: sandbox/scripts/hello_sandbox.py
        # gates its actual work behind exactly that guard).
        sys.argv = [module_path] + _extra_argv
        spec = importlib.util.spec_from_file_location("__main__", module_path)
    elif _mode == "apply_to_code":
        spec = importlib.util.spec_from_file_location("_sandbox_apply_to_code", module_path)
    elif _mode == "functional_verify":
        spec = importlib.util.spec_from_file_location("_sandbox_functional_verify", module_path)
    else:
        spec = importlib.util.spec_from_file_location("_sandbox_test", module_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    if _mode == "apply_to_code":
        # The caller (self_edit_manager.py's _run_apply_to_code_sandboxed())
        # already confirmed apply_to_code exists with a 1-arg signature
        # before ever spawning this subprocess — re-check here anyway since
        # this process re-imports the module fresh and must not trust the
        # caller's read as authoritative for what's actually in memory now.
        _in_path, _out_path = _extra_argv[0], _extra_argv[1]
        fn = getattr(m, "apply_to_code", None)
        if not callable(fn):
            print("APPLY_TO_CODE_NOT_CALLABLE", file=sys.stderr)
            sys.exit(1)
        import inspect as _inspect
        try:
            if len(_inspect.signature(fn).parameters) != 1:
                print("APPLY_TO_CODE_BAD_SIGNATURE", file=sys.stderr)
                sys.exit(1)
        except (TypeError, ValueError) as e:
            print(f"APPLY_TO_CODE_SIGNATURE_ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        with open(_in_path, "r", encoding="utf-8") as f:
            _candidate_code = f.read()
        _result = fn(_candidate_code)  # the one real risky call this mode exists to isolate
        if not isinstance(_result, str):
            print(f"APPLY_TO_CODE_BAD_RETURN_TYPE: {type(_result).__name__}", file=sys.stderr)
            sys.exit(1)
        with open(_out_path, "w", encoding="utf-8") as f:
            f.write(_result)
        print("SANDBOX_OK")
        sys.exit(0)

    if _mode == "functional_verify":
        import inspect as _inspect
        import json as _json

        _out_path = _extra_argv[0]
        _results: list = []
        for _name, _obj in vars(m).items():
            if _name.startswith("_"):
                continue
            _kind = None
            if _inspect.isfunction(_obj) and getattr(_obj, "__module__", None) == m.__name__:
                _kind = "function"
            elif _inspect.isclass(_obj) and getattr(_obj, "__module__", None) == m.__name__:
                _kind = "class"
            else:
                continue  # imported name, constant, or anything not a candidate-defined callable

            try:
                _target = _obj if _kind == "function" else _obj.__init__
                _params = [
                    p for p in _inspect.signature(_target).parameters.values()
                    if p.default is _inspect.Parameter.empty
                    and p.kind in (
                        _inspect.Parameter.POSITIONAL_ONLY,
                        _inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    )
                ]
                if _kind == "class" and _params and _params[0].name == "self":
                    _params = _params[1:]
            except (TypeError, ValueError) as _sig_err:
                _results.append({"name": _name, "kind": _kind, "outcome": "skipped_unsupported_signature", "error": str(_sig_err)})
                continue

            if len(_params) == 0:
                _args = ()
            elif len(_params) == 1:
                _args = ("test",)
            else:
                _results.append({"name": _name, "kind": _kind, "outcome": "skipped_unsupported_signature", "error": f"{len(_params)} required params"})
                continue

            try:
                _obj(*_args)
                _results.append({"name": _name, "kind": _kind, "outcome": "executed_ok", "error": None})
            except Exception as _call_err:
                _results.append({"name": _name, "kind": _kind, "outcome": "raised", "error": f"{type(_call_err).__name__}: {_call_err}"})

        _any_tested = any(r["outcome"] in ("executed_ok", "raised") for r in _results)
        _any_raised = any(r["outcome"] == "raised" for r in _results)
        with open(_out_path, "w", encoding="utf-8") as f:
            _json.dump({"tested": _results, "any_tested": _any_tested, "any_raised": _any_raised}, f)
        print("SANDBOX_OK")
        sys.exit(0)

    # Smoke-test apply_to_code() with real input, not just verify the module
    # imports (CLAUDE.md Finding 28): three successive broken versions of
    # this hook reached production because this test only checked import,
    # never invocation — a function that threw on every real call (missing
    # `import re`, then `regex_pattern`, then `is_prose` NameErrors) kept
    # passing. A raise here fails the test the same way an import failure
    # already does. Covers both call sites that use this wrapper in
    # --mode=import (F2's test_code_in_sandbox() and the staging import
    # test), since both load self_edit_generated.py-shaped candidates.
    if hasattr(m, "apply_to_code") and callable(m.apply_to_code):
        m.apply_to_code("def _sandbox_probe():\n    return 1\n")

    print("SANDBOX_OK")
