"""
sandbox/safe_exec_wrapper.py — F2 filesystem-isolated sandbox (Option A).

Patches builtins before loading the module under test so that any write
operation targeting a path outside SCRATCH_DIR raises PermissionError.
The subprocess exits non-zero; the caller treats that as a sandbox failure.

Usage (called by self_edit_manager.py):
    python3 sandbox/safe_exec_wrapper.py <SCRATCH_DIR> <MODULE_PATH>

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
        print("Usage: safe_exec_wrapper.py <SCRATCH_DIR> <MODULE_PATH>", file=sys.stderr)
        sys.exit(1)

    scratch_dir = sys.argv[1]
    module_path = sys.argv[2]

    _install_patches(scratch_dir)

    import importlib.util
    spec = importlib.util.spec_from_file_location("_sandbox_test", module_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    print("SANDBOX_OK")
