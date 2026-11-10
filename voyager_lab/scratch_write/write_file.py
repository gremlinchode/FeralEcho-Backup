"""Create a new regular file inside a caller-supplied scratch directory.

The only success result is status "verified" with audit_recorded True.
That status is set after the destination has been read back from disk and
an audit record has been appended inside the same scratch root.

This module does not register a production tool and does not choose a
default root. There is no command-line entry point.
"""

import errno
import os
import secrets
import stat

import confine


def _lock():
    return confine.OPERATION_LOCK


def _write_all(fd, data):
    """Write every byte to an already-open temp descriptor.

    Tests replace this function to simulate an interrupted write. Audit
    appends do not use it.
    """
    view = memoryview(data)
    while len(view):
        count = os.write(fd, view)
        if count <= 0:
            raise OSError(errno.EIO, "short write")
        view = view[count:]


def _unlink_temp(dir_fd, name):
    """Remove a temp name. Tests replace this to simulate cleanup failure."""
    os.unlink(name, dir_fd=dir_fd)


def _discard_temp(dir_fd, name):
    try:
        _unlink_temp(dir_fd, name)
    except OSError:
        return


def _result(operation, requested, status, reason, size, digest, verification, recorded, accepted):
    ok = (
        recorded
        and status == "verified"
        and verification == "match"
        and accepted
    )
    return {
        "accepted": bool(accepted) and ok,
        "audit_recorded": recorded,
        "ok": ok,
        "operation": operation,
        "path": confine.public_path(requested),
        "reason": reason,
        "sha256": digest,
        "size": size,
        "status": status,
        "verification": verification,
    }


def _finish(root, operation, requested, status, reason, size, digest, verification, accepted):
    """Append an audit record, then decide whether this call may report success."""
    record_accepted = bool(accepted) and status == "verified" and verification == "match"
    record = confine.build_record(
        operation,
        requested,
        record_accepted,
        reason if status != "verified" else "verified",
        size if status == "verified" else size,
        digest,
        verification,
    )
    recorded = False
    try:
        confine.append_audit(root.fd, record)
        recorded = True
    except Exception:
        recorded = False
    status_out = status
    reason_out = reason if status != "verified" else "verified"
    accepted_out = record_accepted
    if status == "verified" and not recorded:
        status_out = "audit_failed"
        reason_out = "audit_failed"
        accepted_out = False
    return _result(
        operation,
        requested,
        status_out,
        reason_out,
        size,
        digest,
        verification,
        recorded,
        accepted_out,
    )


def _reject(root, requested, exc, size=None, digest=None):
    return _finish(
        root,
        "write",
        requested,
        exc.status,
        exc.reason,
        size,
        digest,
        exc.verification,
        False,
    )


def _place_file(root_real, parent_fd, final, data):
    """Create `final` by linking a fully written temp inode. Never rename onto it."""
    confine.assert_fd_inside(parent_fd, root_real, status="write_failed")
    try:
        info = os.lstat(final, dir_fd=parent_fd)
    except FileNotFoundError:
        info = None
    except OSError as exc:
        raise confine.ConfineError("write_failed", status="write_failed") from exc
    if info is not None:
        confine.classify_existing(info)

    tmp_name = confine.TEMP_PREFIX + secrets.token_hex(16)
    flags = os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY | os.O_CLOEXEC
    fd = None
    linked = False
    try:
        try:
            fd = os.open(tmp_name, flags, confine.FILE_MODE, dir_fd=parent_fd)
        except OSError as exc:
            raise confine.ConfineError("write_failed", status="write_failed") from exc
        os.fchmod(fd, confine.FILE_MODE)
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != confine.FILE_MODE
            or info.st_nlink != 1
        ):
            raise confine.ConfineError("write_failed", status="write_failed")
        confine.assert_fd_inside(fd, root_real, status="write_failed")
        _write_all(fd, data)
        os.fsync(fd)
        confine.assert_fd_inside(fd, root_real, status="write_failed")
        os.close(fd)
        fd = None
        confine.assert_fd_inside(parent_fd, root_real, status="write_failed")
        try:
            os.link(
                tmp_name,
                final,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise confine.ConfineError("destination_exists") from exc
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise confine.ConfineError("destination_exists") from exc
            raise confine.ConfineError("link_failed", status="write_failed") from exc
        linked = True
        try:
            os.fsync(parent_fd)
        except OSError:
            pass
        try:
            _unlink_temp(parent_fd, tmp_name)
        except OSError as exc:
            raise confine.ConfineError(
                "temp_cleanup_failed",
                status="temp_cleanup_failed",
            ) from exc
    except confine.ConfineError:
        if fd is not None:
            os.close(fd)
            fd = None
        if not linked:
            _discard_temp(parent_fd, tmp_name)
        raise
    except OSError as exc:
        if fd is not None:
            os.close(fd)
            fd = None
        if not linked:
            _discard_temp(parent_fd, tmp_name)
        raise confine.ConfineError("write_failed", status="write_failed") from exc
    except Exception:
        if fd is not None:
            os.close(fd)
        if not linked:
            _discard_temp(parent_fd, tmp_name)
        raise

    actual = confine.read_regular(parent_fd, final, root_real, repair_mode=True)
    digest = confine.sha256_bytes(actual)
    if actual != data:
        raise confine.ConfineError(
            "verification_mismatch",
            status="verification_failed",
            verification="mismatch",
        )
    info = os.lstat(final, dir_fd=parent_fd)
    if not stat.S_ISREG(info.st_mode) or (stat.S_IMODE(info.st_mode) & 0o111):
        raise confine.ConfineError(
            "mode_unexpected",
            status="verification_failed",
            verification="mismatch",
        )
    return digest, len(actual)


def _write_locked(root, relative_path, content):
    try:
        opened = confine.open_root(root)
    except confine.ConfineError as exc:
        return _result(
            "write",
            relative_path,
            exc.status,
            exc.reason,
            None,
            None,
            exc.verification,
            False,
            False,
        )
    try:
        return _write_opened(opened, relative_path, content)
    finally:
        opened.close()


def _write_opened(opened, relative_path, content):
    try:
        data = confine.encode_content(content)
        parts = confine.split_relative(relative_path)
    except confine.ConfineError as exc:
        return _reject(opened, relative_path, exc)
    extra = []
    try:
        try:
            parent, final, extra = confine.walk_to_parent(opened, parts)
        except confine.ConfineError as exc:
            return _reject(opened, relative_path, exc)
        try:
            digest, size = _place_file(opened.real, parent, final, data)
        except confine.ConfineError as exc:
            if exc.status == "temp_cleanup_failed":
                return _after_temp_cleanup(opened, relative_path, parent, final, data)
            size = None
            digest = None
            if exc.verification == "mismatch":
                try:
                    actual = confine.read_regular(
                        parent, final, opened.real, repair_mode=False
                    )
                except confine.ConfineError:
                    actual = None
                if actual is not None:
                    size = len(actual)
                    digest = confine.sha256_bytes(actual)
            return _reject(opened, relative_path, exc, size=size, digest=digest)
        return _finish(
            opened,
            "write",
            relative_path,
            "verified",
            "verified",
            size,
            digest,
            "match",
            True,
        )
    finally:
        for fd in extra:
            os.close(fd)


def _after_temp_cleanup(opened, relative_path, parent, final, data):
    """The destination was linked and the temp name is still present."""
    try:
        actual = confine.read_regular(parent, final, opened.real, repair_mode=False)
    except confine.ConfineError as exc:
        return _reject(opened, relative_path, exc)
    digest = confine.sha256_bytes(actual)
    if actual != data:
        return _finish(
            opened,
            "write",
            relative_path,
            "verification_failed",
            "verification_mismatch",
            len(actual),
            digest,
            "mismatch",
            False,
        )
    return _finish(
        opened,
        "write",
        relative_path,
        "temp_cleanup_failed",
        "temp_cleanup_failed",
        len(actual),
        digest,
        "match",
        False,
    )


def write_file(root, relative_path, content):
    """Create a new file at `relative_path` inside `root`.

    root: absolute path of an existing real directory.
    relative_path: string relative path. Absolute paths are rejected.
    content: plain str, stored as UTF-8. It is not executed.

    Returns a dict. ok is True only when status is "verified" and the audit
    record was written. A return without an exception is not success.
    """
    with _lock():
        return _write_locked(root, relative_path, content)
