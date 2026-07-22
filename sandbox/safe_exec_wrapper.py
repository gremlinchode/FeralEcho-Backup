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
"""

import builtins as _builtins
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
    if _mode not in ("import", "script", "apply_to_code"):
        print(f"Unknown --mode={_mode!r}, expected 'import', 'script', or 'apply_to_code'", file=sys.stderr)
        sys.exit(1)
    if _mode == "apply_to_code" and len(_extra_argv) < 2:
        print("--mode=apply_to_code requires -- <input_path> <output_path>", file=sys.stderr)
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
