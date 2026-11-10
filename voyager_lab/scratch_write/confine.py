"""Filesystem boundary for the scratch-only writer.

This module is laboratory code. It is not a production tool and it does
not import the FeralEcho application. Callers pass a scratch root that
must already exist. The root is rejected when it is a symlink, when it is
one of the broad directories listed below, or when its real path is inside
the production tree or the Voyager tree.

Containment uses openat, O_NOFOLLOW, and F_GETPATH. A string prefix is not
treated as proof, because the Voyager path shares a character prefix with
the production path.
"""

import errno
import fcntl
import hashlib
import json
import os
import stat
import threading
from datetime import datetime, timezone

MAX_CONTENT_BYTES = 1_048_576
MAX_PATH_CHARS = 1024
MAX_COMPONENT_BYTES = 255
MAX_DEPTH = 32
FILE_MODE = 0o644
AUDIT_NAME = ".scratch_write_audit.jsonl"
TEMP_PREFIX = ".swtmp_"
_GETPATH_BYTES = 1024

PROTECTED_ROOTS = (
    "/Users/richietate/Desktop/FeralEcho",
    "/Users/richietate/Desktop/FeralEcho-voyager",
)

# Exact real paths only. A private subdirectory of a temporary folder stays
# usable. The directory itself does not.
BROAD_ROOTS = (
    "/",
    "/tmp",
    "/private/tmp",
    "/var",
    "/private/var",
    "/private",
    "/Users",
    "/Users/richietate",
    "/Users/richietate/Desktop",
)

_BROAD_REAL = None

# Serializes write_file and verify_file in this process. A second process
# still relies on link() failing with EEXIST. This lock is not a sandbox.
OPERATION_LOCK = threading.Lock()


class ConfineError(Exception):
    """A confinement or verification failure. Never means the write succeeded."""

    def __init__(self, reason, status="rejected", verification="not_run"):
        super().__init__(reason)
        self.reason = reason
        self.status = status
        self.verification = verification


class OpenRoot:
    """An O_DIRECTORY file descriptor for a resolved scratch root."""

    def __init__(self, fd, real):
        self.fd = fd
        self.real = real
        self._closed = False

    def close(self):
        if not self._closed:
            os.close(self.fd)
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def _require_platform():
    missing = []
    if not hasattr(os, "O_NOFOLLOW"):
        missing.append("O_NOFOLLOW")
    if not hasattr(os, "O_DIRECTORY"):
        missing.append("O_DIRECTORY")
    if not hasattr(fcntl, "F_GETPATH"):
        missing.append("F_GETPATH")
    if missing:
        raise ConfineError("platform_unsupported")


def _broad_reals():
    global _BROAD_REAL
    if _BROAD_REAL is None:
        found = set()
        for item in BROAD_ROOTS:
            try:
                found.add(os.path.realpath(item))
            except OSError:
                found.add(item)
        _BROAD_REAL = frozenset(found)
    return _BROAD_REAL


def is_within(path, root):
    """Return True when the real path of `path` is `root` or a descendant.

    commonpath is used because a prefix test treats
    /Users/richietate/Desktop/FeralEcho-voyager as inside
    /Users/richietate/Desktop/FeralEcho.
    """
    try:
        path_real = os.path.realpath(path)
        root_real = os.path.realpath(root)
        return os.path.commonpath([path_real, root_real]) == root_real
    except (OSError, ValueError):
        return False


def is_protected_path(path):
    """Return True when `path` must not be used as a scratch root or target."""
    try:
        real = os.path.realpath(path)
    except OSError:
        return True
    if real in _broad_reals():
        return True
    for root in PROTECTED_ROOTS:
        if is_within(real, root):
            return True
    return False


def fd_path(fd):
    """Return the kernel path of an open descriptor, or raise ConfineError."""
    try:
        raw = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(_GETPATH_BYTES))
    except (OSError, ValueError) as exc:
        raise ConfineError("root_unresolved") from exc
    if not isinstance(raw, (bytes, bytearray)) or b"\0" not in raw:
        raise ConfineError("root_unresolved")
    try:
        text = bytes(raw).split(b"\0", 1)[0].decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ConfineError("root_unresolved") from exc
    if not text.startswith("/"):
        raise ConfineError("root_unresolved")
    return text


def assert_fd_inside(fd, root_real, status="write_failed"):
    """Raise unless this descriptor still names a path inside `root_real`."""
    path = fd_path(fd)
    verification = "unreadable" if status == "verification_failed" else "not_run"
    if is_protected_path(path) or not is_within(path, root_real):
        raise ConfineError("escape", status=status, verification=verification)
    return path


def public_path(path):
    """Return a loggable path. Oversized and non-str values are omitted."""
    if type(path) is not str or len(path) > MAX_PATH_CHARS:
        return None
    return path


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def encode_content(content):
    """Accept a plain str and return UTF-8 bytes. Do not interpret them."""
    if type(content) is not str:
        raise ConfineError("content_type")
    if len(content) > MAX_CONTENT_BYTES:
        raise ConfineError("content_too_large")
    try:
        data = content.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise ConfineError("content_unencodable") from exc
    if len(data) > MAX_CONTENT_BYTES:
        raise ConfineError("content_too_large")
    return data


def split_relative(path):
    """Split a relative path into components, or raise ConfineError.

    Components are not normalized. `..` is rejected rather than collapsed.
    Percent-encoded dots stay literal characters.
    """
    if type(path) is not str:
        raise ConfineError("path_type")
    if path == "":
        raise ConfineError("path_empty")
    if "\x00" in path:
        raise ConfineError("path_nul")
    if "\\" in path:
        raise ConfineError("path_backslash")
    if os.path.isabs(path):
        raise ConfineError("path_absolute")
    if len(path) > MAX_PATH_CHARS:
        raise ConfineError("path_too_long")
    for char in path:
        code = ord(char)
        if code < 32 or code == 127:
            raise ConfineError("path_control_char")
    parts = path.split("/")
    if any(part == "" for part in parts):
        raise ConfineError("path_empty_component")
    if len(parts) > MAX_DEPTH:
        raise ConfineError("path_too_long")
    for part in parts:
        if part in (".", ".."):
            raise ConfineError("path_dot_segment")
        try:
            encoded = part.encode("utf-8", "strict")
        except UnicodeEncodeError as exc:
            raise ConfineError("path_unencodable") from exc
        if len(encoded) > MAX_COMPONENT_BYTES:
            raise ConfineError("path_component_too_long")
        if part == AUDIT_NAME:
            raise ConfineError("path_reserved")
        if part.startswith(TEMP_PREFIX):
            raise ConfineError("path_reserved_temp")
    return parts


def open_root(root):
    """Open a real, non-symlink directory that is allowed to be a scratch."""
    if type(root) is not str:
        raise ConfineError("root_type")
    if "\x00" in root:
        raise ConfineError("root_nul")
    if not os.path.isabs(root):
        raise ConfineError("root_not_absolute")
    _require_platform()
    try:
        info = os.lstat(root)
    except FileNotFoundError as exc:
        raise ConfineError("root_missing") from exc
    except OSError as exc:
        raise ConfineError("root_open_failed") from exc
    if stat.S_ISLNK(info.st_mode):
        raise ConfineError("root_symlink")
    if not stat.S_ISDIR(info.st_mode):
        raise ConfineError("root_not_directory")
    real = os.path.realpath(root)
    if is_protected_path(real):
        raise ConfineError("root_protected")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(real, flags)
    except OSError as exc:
        raise ConfineError("root_open_failed") from exc
    try:
        got = fd_path(fd)
    except ConfineError:
        os.close(fd)
        raise
    if got != real:
        os.close(fd)
        raise ConfineError("root_mismatch")
    if is_protected_path(got):
        os.close(fd)
        raise ConfineError("root_protected")
    return OpenRoot(fd, real)


def walk_to_parent(root, parts):
    """Open each existing parent with O_NOFOLLOW. Do not create directories.

    Returns (parent_fd, final_name, extra_fds). extra_fds must be closed by
    the caller. root.fd is not included in extra_fds and is not closed here.
    """
    extra = []
    parent = root.fd
    try:
        for name in parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            try:
                fd = os.open(name, flags, dir_fd=parent)
            except OSError as exc:
                if exc.errno == errno.ENOENT:
                    raise ConfineError("missing_parent") from exc
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise ConfineError("symlink_or_not_directory") from exc
                raise ConfineError("parent_unresolved", status="write_failed") from exc
            extra.append(fd)
            assert_fd_inside(fd, root.real, status="write_failed")
            parent = fd
        return parent, parts[-1], extra
    except Exception:
        for fd in extra:
            os.close(fd)
        raise


def _audit_stat_ok(info):
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return False
    if stat.S_IMODE(info.st_mode) & 0o111:
        return False
    if info.st_nlink != 1:
        return False
    return True


def _open_audit_existing(root_fd):
    info = os.lstat(AUDIT_NAME, dir_fd=root_fd)
    if not _audit_stat_ok(info):
        raise ConfineError("audit_failed", status="audit_failed")
    flags = os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        return os.open(AUDIT_NAME, flags, dir_fd=root_fd)
    except OSError as exc:
        raise ConfineError("audit_failed", status="audit_failed") from exc


def _open_audit(root_fd):
    """Open the audit log inside the scratch root, or raise.

    A symlink, directory, socket, fifo, device, executable, or extra hard
    link is not opened. O_NOFOLLOW is not removed after a failed create.
    """
    create_flags = (
        os.O_CREAT | os.O_EXCL | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        info = os.lstat(AUDIT_NAME, dir_fd=root_fd)
    except FileNotFoundError:
        try:
            fd = os.open(AUDIT_NAME, create_flags, FILE_MODE, dir_fd=root_fd)
        except FileExistsError:
            return _open_audit_existing(root_fd)
        try:
            os.fchmod(fd, FILE_MODE)
            info = os.fstat(fd)
            if not _audit_stat_ok(info):
                raise ConfineError("audit_failed", status="audit_failed")
            return fd
        except Exception:
            os.close(fd)
            raise
    else:
        if not _audit_stat_ok(info):
            raise ConfineError("audit_failed", status="audit_failed")
        return _open_audit_existing(root_fd)


def _write_full(fd, payload):
    view = memoryview(payload)
    while len(view):
        count = os.write(fd, view)
        if count <= 0:
            raise OSError(errno.EIO, "short audit write")
        view = view[count:]


def append_audit(root_fd, record):
    """Append one JSON object to the scratch audit log."""
    line = json.dumps(
        record,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = (line + "\n").encode("ascii", "strict")
    fd = _open_audit(root_fd)
    try:
        _write_full(fd, payload)
        os.fsync(fd)
    except OSError as exc:
        raise ConfineError("audit_failed", status="audit_failed") from exc
    finally:
        os.close(fd)
    try:
        os.fsync(root_fd)
    except OSError:
        pass


def build_record(operation, path, accepted, reason, size, digest, verification):
    return {
        "accepted": bool(accepted),
        "operation": operation,
        "path": public_path(path),
        "reason": reason,
        "sha256": digest,
        "size": size,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "verification": verification,
    }


def read_regular(dir_fd, name, root_real, repair_mode=False):
    """Read a regular file through dir_fd. Do not follow a symlink."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(name, flags, dir_fd=dir_fd)
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise ConfineError(
                "symlink_destination",
                status="verification_failed",
                verification="unreadable",
            ) from exc
        raise ConfineError(
            "readback_failed",
            status="verification_failed",
            verification="unreadable",
        ) from exc
    try:
        assert_fd_inside(fd, root_real, status="verification_failed")
        info = os.fstat(fd)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise ConfineError(
                "destination_not_regular",
                status="verification_failed",
                verification="unreadable",
            )
        if info.st_size > MAX_CONTENT_BYTES:
            raise ConfineError(
                "content_too_large",
                status="verification_failed",
                verification="unreadable",
            )
        if stat.S_IMODE(info.st_mode) & 0o111:
            if not repair_mode:
                raise ConfineError(
                    "mode_unexpected",
                    status="verification_failed",
                    verification="unreadable",
                )
            os.fchmod(fd, FILE_MODE)
            info = os.fstat(fd)
            if stat.S_IMODE(info.st_mode) & 0o111:
                raise ConfineError(
                    "mode_unexpected",
                    status="verification_failed",
                    verification="unreadable",
                )
        return _read_full(fd, info.st_size)
    finally:
        os.close(fd)


def _read_full(fd, size):
    if size == 0:
        return b""
    if size < 0:
        raise ConfineError(
            "readback_failed",
            status="verification_failed",
            verification="unreadable",
        )
    chunks = []
    remaining = size
    while remaining:
        block = os.read(fd, min(remaining, 1024 * 1024))
        if not block:
            raise ConfineError(
                "readback_failed",
                status="verification_failed",
                verification="unreadable",
            )
        chunks.append(block)
        remaining -= len(block)
    return b"".join(chunks)


def classify_existing(info):
    """Raise the rejection that matches an existing final component."""
    if stat.S_ISLNK(info.st_mode):
        raise ConfineError("symlink_destination")
    if stat.S_ISDIR(info.st_mode):
        raise ConfineError("destination_directory")
    if not stat.S_ISREG(info.st_mode):
        raise ConfineError("destination_not_regular")
    raise ConfineError("destination_exists")
