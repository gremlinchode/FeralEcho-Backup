"""Read a scratch file back and compare it with expected text.

Verification does not create the destination and does not follow symlinks.
The bytes on disk are authoritative. A previous write_file return value is
not consulted.
"""

import os
import stat

import confine
import write_file


def _result(requested, status, reason, size, digest, verification, recorded, accepted):
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
        "operation": "verify",
        "path": confine.public_path(requested),
        "reason": reason,
        "sha256": digest,
        "size": size,
        "status": status,
        "verification": verification,
    }


def _finish(root, requested, status, reason, size, digest, verification, accepted):
    record_accepted = bool(accepted) and status == "verified" and verification == "match"
    record = confine.build_record(
        "verify",
        requested,
        record_accepted,
        reason if status != "verified" else "verified",
        size,
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
        requested,
        exc.status,
        exc.reason,
        size,
        digest,
        exc.verification,
        False,
    )


def _verify_opened(opened, relative_path, expected):
    try:
        data = confine.encode_content(expected)
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
            info = os.lstat(final, dir_fd=parent)
        except FileNotFoundError:
            return _finish(
                opened,
                relative_path,
                "verification_failed",
                "missing",
                None,
                None,
                "missing",
                False,
            )
        except OSError as exc:
            return _reject(
                opened,
                relative_path,
                confine.ConfineError(
                    "readback_failed",
                    status="verification_failed",
                    verification="unreadable",
                ),
            )
        if stat.S_ISLNK(info.st_mode):
            return _finish(
                opened,
                relative_path,
                "verification_failed",
                "symlink_destination",
                None,
                None,
                "unreadable",
                False,
            )
        if stat.S_ISDIR(info.st_mode):
            return _finish(
                opened,
                relative_path,
                "verification_failed",
                "destination_directory",
                None,
                None,
                "unreadable",
                False,
            )
        if not stat.S_ISREG(info.st_mode):
            return _finish(
                opened,
                relative_path,
                "verification_failed",
                "destination_not_regular",
                None,
                None,
                "unreadable",
                False,
            )
        try:
            actual = confine.read_regular(
                parent, final, opened.real, repair_mode=False
            )
        except confine.ConfineError as exc:
            return _reject(opened, relative_path, exc)
        digest = confine.sha256_bytes(actual)
        if actual != data:
            return _finish(
                opened,
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
            relative_path,
            "verified",
            "verified",
            len(actual),
            digest,
            "match",
            True,
        )
    finally:
        for fd in extra:
            os.close(fd)


def _verify_locked(root, relative_path, expected_content):
    try:
        opened = confine.open_root(root)
    except confine.ConfineError as exc:
        return _result(
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
        return _verify_opened(opened, relative_path, expected_content)
    finally:
        opened.close()


def verify_file(root, relative_path, expected_content):
    """Compare the file at `relative_path` with `expected_content`.

    Does not create or modify the destination. ok is True only when the
    bytes read from disk match and the verify audit record was written.
    """
    with write_file._lock():
        return _verify_locked(root, relative_path, expected_content)
