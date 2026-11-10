"""Host-owned directory pin and rootless scratch writer.

Laboratory only. This module is not an Echo tool and it is not registered
with any tool list. It does not modify confine.py, write_file.py, or
verify_file.py. Those functions still accept a caller-supplied root.

The operator passes one directory path to open_pinned_root. The host opens
that directory, duplicates the descriptor, and stores the descriptor
together with the device, inode, and F_GETPATH string from that moment.
ScratchWriter.write_file and ScratchWriter.verify_file take a relative
path and content only. They have no root parameter. Echo does not receive
the descriptor or a way to replace the pin.

A rename that is visible at a validation check fails the call. Descriptor
operations stay on the opened directory, so a replacement directory at the
old path is not the write target. If this call has already linked a name
and a later check sees the pinned directory move, the name is unlinked
through the pinned directory descriptor. Success is not returned unless
the file is still established at the pinned path. A success audit line is
not appended for a failed or relocated publication. If the directory inode
no longer matches, nothing is unlinked: the descriptor is no longer known
to be the original directory.

Residual limitation, stated precisely: this module does not close the
interval between a passing fstat/F_GETPATH check and a later os.write,
os.link, or audit append. Darwin provides no openat2/RESOLVE_BENEATH.
Userspace can sample the path and then lose the race. Bytes can land on
the moved inode inside that interval, and a process killed between link
and unlink is not cleaned up here. macOS Seatbelt is not used and is not
a substitute for the pin. sandbox(7) states that an already-open writable
descriptor may still be used after write restrictions are applied.
"""

import errno
import fcntl
import os
import secrets
import stat

import confine


class _PinLost(Exception):
    """The pinned directory failed a check. inode_ok means unlink is still safe."""

    def __init__(self, inode_ok):
        super().__init__("identity_mismatch")
        self.inode_ok = bool(inode_ok)


class PinnedRoot:
    """Directory descriptor retained by the host. Not an Echo-facing object."""

    __slots__ = ("fd", "path", "dev", "ino")

    def __init__(self, fd, path, dev, ino):
        self.fd = fd
        self.path = path
        self.dev = dev
        self.ino = ino


def _inspect_pin(pin):
    """Return (holds, inode_ok). Do not realpath the live F_GETPATH string."""
    try:
        info = os.fstat(pin.fd)
    except OSError:
        return False, False
    inode_ok = (
        stat.S_ISDIR(info.st_mode)
        and info.st_dev == pin.dev
        and info.st_ino == pin.ino
    )
    try:
        path = confine.fd_path(pin.fd)
    except confine.ConfineError:
        return False, inode_ok
    return inode_ok and path == pin.path, inode_ok


def _require_root_pin(pin):
    holds, inode_ok = _inspect_pin(pin)
    if not holds:
        raise _PinLost(inode_ok)


def _require_fd_path(fd, expected, pin):
    """The fd's F_GETPATH must equal `expected`, and the root pin must hold.

    A file inode is not compared with the directory inode. Those are
    different objects. `expected` is string concatenation of the pinned
    path and the relative name already accepted.
    """
    try:
        got = confine.fd_path(fd)
    except confine.ConfineError as exc:
        holds, inode_ok = _inspect_pin(pin)
        if not holds:
            raise _PinLost(inode_ok) from exc
        raise confine.ConfineError(
            "parent_unresolved",
            status="write_failed",
        ) from exc
    if got != expected:
        holds, inode_ok = _inspect_pin(pin)
        if not holds:
            raise _PinLost(inode_ok)
        raise confine.ConfineError("escape", status="write_failed")
    _require_root_pin(pin)


def _child_path(parent_path, name):
    return parent_path + "/" + name


def open_pinned_root(path):
    """Open one scratch directory and return a host-owned pin.

    Uses confine.open_root, so a protected path, a symlink, or a
    non-directory is refused before a ScratchWriter exists. The retained
    descriptor is a CLOEXEC duplicate. The original OpenRoot is closed.
    """
    if not hasattr(fcntl, "F_DUPFD_CLOEXEC"):
        raise confine.ConfineError("platform_unsupported")
    opened = confine.open_root(path)
    dup = None
    try:
        try:
            dup = fcntl.fcntl(opened.fd, fcntl.F_DUPFD_CLOEXEC, 0)
        except (OSError, TypeError, ValueError) as exc:
            raise confine.ConfineError("platform_unsupported") from exc
        if type(dup) is not int or dup < 0:
            raise confine.ConfineError("platform_unsupported")
        info = os.fstat(dup)
        if not stat.S_ISDIR(info.st_mode):
            raise confine.ConfineError("root_not_directory")
        got = confine.fd_path(dup)
        original = confine.fd_path(opened.fd)
        if got != opened.real or got != original:
            raise confine.ConfineError("root_mismatch")
        pin = PinnedRoot(dup, got, info.st_dev, info.st_ino)
        dup = None
        return pin
    finally:
        if dup is not None:
            os.close(dup)
        opened.close()


def _bare(operation, requested, status, reason, size, digest, verification):
    return {
        "accepted": False,
        "audit_recorded": False,
        "ok": False,
        "operation": operation,
        "path": confine.public_path(requested),
        "reason": reason,
        "sha256": digest,
        "size": size,
        "status": status,
        "verification": verification,
    }


def _unlink_ok(dir_fd, name):
    try:
        os.unlink(name, dir_fd=dir_fd)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


def _write_all(fd, data):
    view = memoryview(data)
    while len(view):
        count = os.write(fd, view)
        if count <= 0:
            raise OSError(errno.EIO, "short write")
        view = view[count:]


def _read_all(fd, size):
    if size == 0:
        return b""
    if size < 0 or size > confine.MAX_CONTENT_BYTES:
        raise confine.ConfineError(
            "readback_failed",
            status="verification_failed",
            verification="unreadable",
        )
    chunks = []
    remaining = size
    while remaining:
        block = os.read(fd, min(remaining, 1024 * 1024))
        if not block:
            raise confine.ConfineError(
                "readback_failed",
                status="verification_failed",
                verification="unreadable",
            )
        chunks.append(block)
        remaining -= len(block)
    return b"".join(chunks)


def _walk(pin, parts):
    """Open existing parents with O_NOFOLLOW. Do not create directories.

    Returns (parent_fd, final_name, parent_path, extra_fds). pin.fd is not
    in extra_fds and is not closed here.
    """
    _require_root_pin(pin)
    extra = []
    parent = pin.fd
    parent_path = pin.path
    try:
        for name in parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            try:
                fd = os.open(name, flags, dir_fd=parent)
            except OSError as exc:
                holds, inode_ok = _inspect_pin(pin)
                if not holds:
                    raise _PinLost(inode_ok) from exc
                if exc.errno == errno.ENOENT:
                    raise confine.ConfineError("missing_parent") from exc
                if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                    raise confine.ConfineError("symlink_or_not_directory") from exc
                raise confine.ConfineError(
                    "parent_unresolved",
                    status="write_failed",
                ) from exc
            extra.append(fd)
            child_path = _child_path(parent_path, name)
            _require_fd_path(fd, child_path, pin)
            parent = fd
            parent_path = child_path
        _require_fd_path(parent, parent_path, pin)
        return parent, parts[-1], parent_path, extra
    except Exception:
        for fd in extra:
            os.close(fd)
        raise


def _read_checked(pin, dir_fd, name, expected_path, repair_mode):
    """Read a regular file. Do not follow a symlink. Do not realpath."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(name, flags, dir_fd=dir_fd)
    except OSError as exc:
        holds, inode_ok = _inspect_pin(pin)
        if not holds:
            raise _PinLost(inode_ok) from exc
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise confine.ConfineError(
                "symlink_destination",
                status="verification_failed",
                verification="unreadable",
            ) from exc
        raise confine.ConfineError(
            "readback_failed",
            status="verification_failed",
            verification="unreadable",
        ) from exc
    try:
        _require_fd_path(fd, expected_path, pin)
        info = os.fstat(fd)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise confine.ConfineError(
                "destination_not_regular",
                status="verification_failed",
                verification="unreadable",
            )
        if info.st_size > confine.MAX_CONTENT_BYTES:
            raise confine.ConfineError(
                "content_too_large",
                status="verification_failed",
                verification="unreadable",
            )
        if stat.S_IMODE(info.st_mode) & 0o111:
            if not repair_mode:
                raise confine.ConfineError(
                    "mode_unexpected",
                    status="verification_failed",
                    verification="unreadable",
                )
            os.fchmod(fd, confine.FILE_MODE)
            info = os.fstat(fd)
            if stat.S_IMODE(info.st_mode) & 0o111:
                raise confine.ConfineError(
                    "mode_unexpected",
                    status="verification_failed",
                    verification="unreadable",
                )
        return _read_all(fd, info.st_size)
    finally:
        os.close(fd)


class ScratchWriter:
    """Rootless writer bound to one host-owned PinnedRoot.

    write_file(relative_path, content) and
    verify_file(relative_path, expected_content) are the only data
    operations. An extra root argument raises TypeError before this body
    runs. close() releases the host descriptor and is not a write tool.
    """

    def __init__(self, pin):
        if type(pin) is not PinnedRoot:
            raise TypeError("pin must be a PinnedRoot opened by the host")
        holds, _inode_ok = _inspect_pin(pin)
        if not holds:
            raise confine.ConfineError("root_mismatch")
        self._pin = pin
        self._closed = False

    def close(self):
        """Release the pinned directory descriptor. Host-side only."""
        with confine.OPERATION_LOCK:
            if self._closed:
                return
            self._closed = True
            os.close(self._pin.fd)

    def write_file(self, relative_path, content):
        """Create one new file inside the pinned directory."""
        with confine.OPERATION_LOCK:
            return self._write_locked(relative_path, content)

    def verify_file(self, relative_path, expected_content):
        """Compare one existing file inside the pinned directory."""
        with confine.OPERATION_LOCK:
            return self._verify_locked(relative_path, expected_content)

    def _identity(self, operation, requested):
        return _bare(
            operation,
            requested,
            "rejected",
            "identity_mismatch",
            None,
            None,
            "not_run",
        )

    def _on_pin_lost(self, parent, final, tmp_name, linked, lost, requested):
        """Undo a name this call published, or a temp it created, when that is safe.

        No audit line is appended. The descriptor is not used for unlink
        when the directory inode no longer matches the pin.
        """
        if not lost.inode_ok:
            return self._identity("write", requested)
        if linked:
            if not _unlink_ok(parent, final):
                if tmp_name is not None:
                    _unlink_ok(parent, tmp_name)
                return _bare(
                    "write",
                    requested,
                    "publish_cleanup_failed",
                    "publish_cleanup_failed",
                    None,
                    None,
                    "not_run",
                )
            if tmp_name is not None and not _unlink_ok(parent, tmp_name):
                return _bare(
                    "write",
                    requested,
                    "temp_cleanup_failed",
                    "temp_cleanup_failed",
                    None,
                    None,
                    "not_run",
                )
            return self._identity("write", requested)
        if tmp_name is not None and not _unlink_ok(parent, tmp_name):
            return _bare(
                "write",
                requested,
                "temp_cleanup_failed",
                "temp_cleanup_failed",
                None,
                None,
                "not_run",
            )
        return self._identity("write", requested)

    def _audit_or_identity(
        self,
        operation,
        requested,
        status,
        reason,
        size,
        digest,
        verification,
        accepted,
    ):
        """Append an audit line only while the pin still holds.

        The check immediately before append_audit still leaves a window
        until the append itself. A pin loss in that window raises _PinLost
        so the caller can drop a name this call published. ok is not
        reported true for that outcome.
        """
        holds, inode_ok = _inspect_pin(self._pin)
        if not holds:
            raise _PinLost(inode_ok)
        record_accepted = (
            bool(accepted) and status == "verified" and verification == "match"
        )
        record = confine.build_record(
            operation,
            requested,
            record_accepted,
            reason if status != "verified" else "verified",
            size,
            digest,
            verification,
        )
        recorded = False
        try:
            confine.append_audit(self._pin.fd, record)
            recorded = True
        except Exception:
            recorded = False
        holds_after, inode_after = _inspect_pin(self._pin)
        if not holds_after:
            raise _PinLost(inode_after)
        status_out = status
        reason_out = reason if status != "verified" else "verified"
        accepted_out = record_accepted
        if status == "verified" and not recorded:
            status_out = "audit_failed"
            reason_out = "audit_failed"
            accepted_out = False
        ok = (
            recorded
            and status_out == "verified"
            and verification == "match"
            and accepted_out
        )
        return {
            "accepted": bool(accepted_out) and ok,
            "audit_recorded": recorded,
            "ok": ok,
            "operation": operation,
            "path": confine.public_path(requested),
            "reason": reason_out,
            "sha256": digest,
            "size": size,
            "status": status_out,
            "verification": verification,
        }

    def _reject(self, parent, final, tmp_name, linked, requested, exc, size, digest):
        try:
            return self._audit_or_identity(
                "write",
                requested,
                exc.status,
                exc.reason,
                size,
                digest,
                exc.verification,
                False,
            )
        except _PinLost as lost:
            return self._on_pin_lost(parent, final, tmp_name, linked, lost, requested)

    def _write_locked(self, relative_path, content):
        if self._closed:
            return self._identity("write", relative_path)
        holds, _inode_ok = _inspect_pin(self._pin)
        if not holds:
            return self._identity("write", relative_path)
        try:
            data = confine.encode_content(content)
            parts = confine.split_relative(relative_path)
        except confine.ConfineError as exc:
            try:
                return self._audit_or_identity(
                    "write",
                    relative_path,
                    exc.status,
                    exc.reason,
                    None,
                    None,
                    exc.verification,
                    False,
                )
            except _PinLost:
                return self._identity("write", relative_path)
        extra = []
        try:
            try:
                parent, final, parent_path, extra = _walk(self._pin, parts)
            except _PinLost:
                return self._identity("write", relative_path)
            except confine.ConfineError as exc:
                try:
                    return self._audit_or_identity(
                        "write",
                        relative_path,
                        exc.status,
                        exc.reason,
                        None,
                        None,
                        exc.verification,
                        False,
                    )
                except _PinLost:
                    return self._identity("write", relative_path)
            return self._place(parent, final, parent_path, data, relative_path)
        finally:
            for fd in extra:
                os.close(fd)

    def _place(self, parent, final, parent_path, data, relative_path):
        fd = None
        tmp_name = None
        linked = False
        try:
            _require_fd_path(parent, parent_path, self._pin)
            try:
                info = os.lstat(final, dir_fd=parent)
            except FileNotFoundError:
                info = None
            except OSError as exc:
                _require_root_pin(self._pin)
                raise confine.ConfineError("write_failed", status="write_failed") from exc
            if info is not None:
                confine.classify_existing(info)

            tmp_name = confine.TEMP_PREFIX + secrets.token_hex(16)
            flags = (
                os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | os.O_WRONLY
                | os.O_CLOEXEC
            )
            try:
                fd = os.open(tmp_name, flags, confine.FILE_MODE, dir_fd=parent)
            except OSError as exc:
                tmp_name = None
                _require_root_pin(self._pin)
                raise confine.ConfineError("write_failed", status="write_failed") from exc
            os.fchmod(fd, confine.FILE_MODE)
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != confine.FILE_MODE
                or info.st_nlink != 1
            ):
                raise confine.ConfineError("write_failed", status="write_failed")
            expected_tmp = _child_path(parent_path, tmp_name)
            _require_fd_path(fd, expected_tmp, self._pin)
            _write_all(fd, data)
            os.fsync(fd)
            _require_fd_path(fd, expected_tmp, self._pin)
            os.close(fd)
            fd = None
            _require_fd_path(parent, parent_path, self._pin)
            try:
                os.link(
                    tmp_name,
                    final,
                    src_dir_fd=parent,
                    dst_dir_fd=parent,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise confine.ConfineError("destination_exists") from exc
            except OSError as exc:
                if exc.errno == errno.EEXIST:
                    raise confine.ConfineError("destination_exists") from exc
                raise confine.ConfineError("link_failed", status="write_failed") from exc
            linked = True
            _require_fd_path(parent, parent_path, self._pin)
            try:
                os.fsync(parent)
            except OSError:
                pass
            try:
                os.unlink(tmp_name, dir_fd=parent)
            except OSError as exc:
                raise confine.ConfineError(
                    "temp_cleanup_failed",
                    status="temp_cleanup_failed",
                ) from exc
            tmp_name = None
            expected_final = _child_path(parent_path, final)
            actual = _read_checked(
                self._pin,
                parent,
                final,
                expected_final,
                repair_mode=True,
            )
            digest = confine.sha256_bytes(actual)
            if actual != data:
                raise confine.ConfineError(
                    "verification_mismatch",
                    status="verification_failed",
                    verification="mismatch",
                )
            try:
                info = os.lstat(final, dir_fd=parent)
            except OSError as exc:
                _require_root_pin(self._pin)
                raise confine.ConfineError(
                    "readback_failed",
                    status="verification_failed",
                    verification="unreadable",
                ) from exc
            if not stat.S_ISREG(info.st_mode) or (stat.S_IMODE(info.st_mode) & 0o111):
                raise confine.ConfineError(
                    "mode_unexpected",
                    status="verification_failed",
                    verification="mismatch",
                )
            _require_root_pin(self._pin)
            return self._audit_or_identity(
                "write",
                relative_path,
                "verified",
                "verified",
                len(actual),
                digest,
                "match",
                True,
            )
        except _PinLost as lost:
            if fd is not None:
                os.close(fd)
                fd = None
            return self._on_pin_lost(
                parent, final, tmp_name, linked, lost, relative_path
            )
        except confine.ConfineError as exc:
            if fd is not None:
                os.close(fd)
                fd = None
            if exc.status == "temp_cleanup_failed":
                return self._after_temp_cleanup(
                    parent, final, tmp_name, parent_path, data, relative_path
                )
            size = None
            digest = None
            if exc.verification == "mismatch" and linked:
                try:
                    actual = _read_checked(
                        self._pin,
                        parent,
                        final,
                        _child_path(parent_path, final),
                        repair_mode=False,
                    )
                except _PinLost as lost:
                    return self._on_pin_lost(
                        parent, final, tmp_name, True, lost, relative_path
                    )
                except confine.ConfineError:
                    actual = None
                if actual is not None:
                    size = len(actual)
                    digest = confine.sha256_bytes(actual)
            if tmp_name is not None and not linked:
                _unlink_ok(parent, tmp_name)
                tmp_name = None
            return self._reject(
                parent, final, tmp_name, linked, relative_path, exc, size, digest
            )
        except OSError as exc:
            if fd is not None:
                os.close(fd)
                fd = None
            holds, inode_ok = _inspect_pin(self._pin)
            if not holds:
                return self._on_pin_lost(
                    parent,
                    final,
                    tmp_name,
                    linked,
                    _PinLost(inode_ok),
                    relative_path,
                )
            if tmp_name is not None and not linked:
                _unlink_ok(parent, tmp_name)
                tmp_name = None
            return self._reject(
                parent,
                final,
                tmp_name,
                linked,
                relative_path,
                confine.ConfineError("write_failed", status="write_failed"),
                None,
                None,
            )
        finally:
            if fd is not None:
                os.close(fd)

    def _after_temp_cleanup(
        self, parent, final, tmp_name, parent_path, data, relative_path
    ):
        """The final name was linked and the temp name is still present."""
        try:
            _require_root_pin(self._pin)
            actual = _read_checked(
                self._pin,
                parent,
                final,
                _child_path(parent_path, final),
                repair_mode=False,
            )
        except _PinLost as lost:
            return self._on_pin_lost(
                parent, final, tmp_name, True, lost, relative_path
            )
        except confine.ConfineError as exc:
            return self._reject(
                parent, final, tmp_name, True, relative_path, exc, None, None
            )
        digest = confine.sha256_bytes(actual) if actual is not None else None
        if actual != data:
            return self._reject(
                parent,
                final,
                tmp_name,
                True,
                relative_path,
                confine.ConfineError(
                    "verification_mismatch",
                    status="verification_failed",
                    verification="mismatch",
                ),
                None if actual is None else len(actual),
                digest,
            )
        try:
            return self._audit_or_identity(
                "write",
                relative_path,
                "temp_cleanup_failed",
                "temp_cleanup_failed",
                len(actual),
                digest,
                "match",
                False,
            )
        except _PinLost as lost:
            return self._on_pin_lost(
                parent, final, tmp_name, True, lost, relative_path
            )

    def _verify_locked(self, relative_path, expected_content):
        if self._closed:
            return self._identity("verify", relative_path)
        holds, _inode_ok = _inspect_pin(self._pin)
        if not holds:
            return self._identity("verify", relative_path)
        try:
            data = confine.encode_content(expected_content)
            parts = confine.split_relative(relative_path)
        except confine.ConfineError as exc:
            try:
                return self._audit_or_identity(
                    "verify",
                    relative_path,
                    exc.status,
                    exc.reason,
                    None,
                    None,
                    exc.verification,
                    False,
                )
            except _PinLost:
                return self._identity("verify", relative_path)
        extra = []
        try:
            try:
                parent, final, parent_path, extra = _walk(self._pin, parts)
            except _PinLost:
                return self._identity("verify", relative_path)
            except confine.ConfineError as exc:
                try:
                    return self._audit_or_identity(
                        "verify",
                        relative_path,
                        exc.status,
                        exc.reason,
                        None,
                        None,
                        exc.verification,
                        False,
                    )
                except _PinLost:
                    return self._identity("verify", relative_path)
            return self._verify_at(parent, final, parent_path, data, relative_path)
        finally:
            for fd in extra:
                os.close(fd)

    def _verify_reject(self, relative_path, exc, size=None, digest=None):
        try:
            return self._audit_or_identity(
                "verify",
                relative_path,
                exc.status,
                exc.reason,
                size,
                digest,
                exc.verification,
                False,
            )
        except _PinLost:
            return self._identity("verify", relative_path)

    def _verify_at(self, parent, final, parent_path, data, relative_path):
        """Read and compare. Do not create, chmod, or unlink an existing file."""
        try:
            _require_fd_path(parent, parent_path, self._pin)
            try:
                info = os.lstat(final, dir_fd=parent)
            except FileNotFoundError:
                return self._verify_reject(
                    relative_path,
                    confine.ConfineError(
                        "missing",
                        status="verification_failed",
                        verification="missing",
                    ),
                )
            except OSError as exc:
                _require_root_pin(self._pin)
                raise confine.ConfineError(
                    "readback_failed",
                    status="verification_failed",
                    verification="unreadable",
                ) from exc
            if stat.S_ISLNK(info.st_mode):
                return self._verify_finish_plain(
                    relative_path,
                    "verification_failed",
                    "symlink_destination",
                    None,
                    None,
                    "unreadable",
                )
            if stat.S_ISDIR(info.st_mode):
                return self._verify_finish_plain(
                    relative_path,
                    "verification_failed",
                    "destination_directory",
                    None,
                    None,
                    "unreadable",
                )
            if not stat.S_ISREG(info.st_mode):
                return self._verify_finish_plain(
                    relative_path,
                    "verification_failed",
                    "destination_not_regular",
                    None,
                    None,
                    "unreadable",
                )
            actual = _read_checked(
                self._pin,
                parent,
                final,
                _child_path(parent_path, final),
                repair_mode=False,
            )
            digest = confine.sha256_bytes(actual)
            if actual != data:
                return self._verify_finish_plain(
                    relative_path,
                    "verification_failed",
                    "verification_mismatch",
                    len(actual),
                    digest,
                    "mismatch",
                )
            _require_root_pin(self._pin)
            return self._audit_or_identity(
                "verify",
                relative_path,
                "verified",
                "verified",
                len(actual),
                digest,
                "match",
                True,
            )
        except _PinLost:
            return self._identity("verify", relative_path)
        except confine.ConfineError as exc:
            return self._verify_reject(relative_path, exc)

    def _verify_finish_plain(
        self, relative_path, status, reason, size, digest, verification
    ):
        try:
            return self._audit_or_identity(
                "verify",
                relative_path,
                status,
                reason,
                size,
                digest,
                verification,
                False,
            )
        except _PinLost:
            return self._identity("verify", relative_path)
