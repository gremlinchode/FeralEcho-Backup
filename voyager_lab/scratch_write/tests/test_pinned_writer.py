"""T1, T8, and T2 for the rootless pinned writer.

Laboratory only. These tests do not contact port 5000, import the
FeralEcho application, read production memory bodies, or hash the FAISS
index. Protected paths are measured with lstat. A guard refuses os.open
on those paths so a regression cannot write them.
"""

import errno
import hashlib
import inspect
import json
import os
import shutil
import stat
import sys
import tempfile
import threading
import traceback
import unittest

TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_DIR not in sys.path:
    sys.path.insert(0, TOOL_DIR)

import confine  # noqa: E402
import pinned_writer  # noqa: E402

PROD = "/Users/richietate/Desktop/FeralEcho"
VOY = "/Users/richietate/Desktop/FeralEcho-voyager"
SENTINEL = "PINNED_SENTINEL_8f3c1d0e"
ESCAPE_BODY = "ESCAPE_BODY_8f3c1d0e"
PROBE_NAME = "pinned_probe_8f3c1d0e.txt"
T2_NAME = "published.txt"
MAX_TRIALS = 40

PROTECTED = (
    ("production_root", os.path.join(PROD), "dir"),
    ("production_memory", os.path.join(PROD, "memory"), "dir"),
    ("production_app_core", os.path.join(PROD, "app", "core"), "dir"),
    ("voyager_worktree", VOY, "dir"),
    ("voyager_package", os.path.join(VOY, "voyager_lab", "voyager"), "dir"),
    ("voyager_results", os.path.join(VOY, "voyager_lab", "results"), "dir"),
    ("faiss_index", os.path.join(PROD, "memory", "faiss.index"), "file"),
    ("memory_meta", os.path.join(PROD, "memory", "memory_meta.json"), "file"),
    (
        "voyager_summary",
        os.path.join(VOY, "voyager_lab", "results", "summary.json"),
        "file",
    ),
    (
        "absent_probe",
        os.path.join(PROD, "memory", PROBE_NAME),
        "missing",
    ),
)


def _dump(tag, payload):
    path = "/tmp/scratch_writer_%s.json" % tag
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    payload["evidence_path"] = path
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def _probe_name_present(path, ident):
    """True only when the synthetic probe name is present.

    A protected file that already exists, such as faiss.index, is not
    the probe. Identity changes for those files are recorded separately.
    """
    if ident.get("kind") == "dir":
        try:
            return PROBE_NAME in os.listdir(path)
        except OSError as exc:
            return "error:%s" % exc.errno
    if os.path.basename(path) == PROBE_NAME:
        return ident.get("exists") is True
    return False


def _ident(path):
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return {"exists": False, "path": path}
    except OSError as exc:
        return {"exists": None, "path": path, "error": exc.errno}
    return {
        "exists": True,
        "path": path,
        "dev": info.st_dev,
        "ino": info.st_ino,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "mode": stat.S_IMODE(info.st_mode),
        "nlink": info.st_nlink,
        "kind": (
            "dir" if stat.S_ISDIR(info.st_mode)
            else "file" if stat.S_ISREG(info.st_mode)
            else "symlink" if stat.S_ISLNK(info.st_mode)
            else "other"
        ),
    }


def _listing(path):
    try:
        names = sorted(os.listdir(path))
    except FileNotFoundError:
        return {"exists": False, "names": None}
    except OSError as exc:
        return {"exists": None, "error": exc.errno}
    entries = []
    for name in names:
        full = path + "/" + name
        try:
            info = os.lstat(full)
        except OSError as exc:
            entries.append({"name": name, "error": exc.errno})
            continue
        entries.append({
            "name": name,
            "dev": info.st_dev,
            "ino": info.st_ino,
            "size": info.st_size,
            "mtime_ns": info.st_mtime_ns,
            "mode": stat.S_IMODE(info.st_mode),
            "nlink": info.st_nlink,
            "kind": (
                "dir" if stat.S_ISDIR(info.st_mode)
                else "file" if stat.S_ISREG(info.st_mode)
                else "symlink" if stat.S_ISLNK(info.st_mode)
                else "other"
            ),
        })
    return {"exists": True, "names": names, "entries": entries}


def _read_nofollow(dir_path, name):
    """Read one directory entry without following a symlink."""
    dir_fd = os.open(
        dir_path,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        fd = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=dir_fd,
        )
        try:
            info = os.fstat(fd)
            chunks = []
            remaining = info.st_size
            while remaining:
                block = os.read(fd, min(remaining, 1024 * 1024))
                if not block:
                    break
                chunks.append(block)
                remaining -= len(block)
            data = b"".join(chunks)
            return {
                "ok": True,
                "size": info.st_size,
                "read_size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "mode": stat.S_IMODE(info.st_mode),
                "ino": info.st_ino,
                "dev": info.st_dev,
                "nlink": info.st_nlink,
                "text": data.decode("utf-8", "replace") if len(data) <= 256 else None,
            }
        finally:
            os.close(fd)
    except OSError as exc:
        return {"ok": False, "errno": exc.errno}
    finally:
        os.close(dir_fd)


def _audit_text(dir_path):
    listed = _listing(dir_path)
    names = listed.get("names") or []
    if confine.AUDIT_NAME not in names:
        return {"present": False, "text": None, "records": []}
    read = _read_nofollow(dir_path, confine.AUDIT_NAME)
    text = None
    records = []
    if read.get("ok") and read.get("text") is not None:
        text = read["text"]
    elif read.get("ok"):
        # Larger than the preview cap. Re-read is unnecessary: audit lines
        # for these tests are small. Record the hash only.
        text = None
    if read.get("ok"):
        dir_fd = os.open(
            dir_path,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        try:
            fd = os.open(
                confine.AUDIT_NAME,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=dir_fd,
            )
            try:
                raw = b""
                while True:
                    block = os.read(fd, 65536)
                    if not block:
                        break
                    raw += block
            finally:
                os.close(fd)
        finally:
            os.close(dir_fd)
        text = raw.decode("ascii", "replace")
        for line in text.splitlines():
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append({"unparsed": line})
    return {
        "present": True,
        "text": text,
        "records": records,
        "read": {k: v for k, v in read.items() if k != "text"},
    }


def _success_records(records):
    found = []
    for record in records:
        if (
            record.get("accepted") is True
            and record.get("verification") == "match"
            and record.get("reason") == "verified"
        ):
            found.append(record)
    return found


def _under_protected(path):
    if isinstance(path, bytes):
        try:
            text = os.fsdecode(path)
        except Exception:
            return False
    elif isinstance(path, str):
        text = path
    else:
        return False
    if not text.startswith("/"):
        return False
    try:
        real = os.path.realpath(text)
    except OSError:
        real = text
    for root in (PROD, VOY):
        try:
            if os.path.commonpath([real, root]) == root:
                return True
        except ValueError:
            continue
    return False


def _thread_in_pinned_writer(ident):
    frame = sys._current_frames().get(ident)
    while frame is not None:
        if frame.f_code.co_filename.endswith("pinned_writer.py"):
            return True
        frame = frame.f_back
    return False


class PinnedWriterCampaign(unittest.TestCase):
    def test_t1_root_substitution(self):
        base = tempfile.mkdtemp(prefix="swpin_t1_")
        pin_requested = base + "/pin"
        outside = base + "/outside"
        os.mkdir(pin_requested, 0o700)
        os.mkdir(outside, 0o700)
        canary_path = outside + "/canary.txt"
        with open(canary_path, "wb") as handle:
            handle.write(b"CANARY-SAFE-T1")
        abs_target = base + "/abs_target.txt"
        escape_target = base + "/escaped.txt"
        evidence = {
            "test": "T1",
            "setup": {
                "base": base,
                "pin_requested": pin_requested,
                "outside": outside,
                "canary": canary_path,
            },
            "limitations": [
                "The laboratory write_file(root, ...) API was not called. "
                "The existing 56 tests already cover that API. This test "
                "does not create a file outside the pinned directory.",
            ],
        }
        writer = None
        try:
            canary_before = _ident(canary_path)
            outside_before = _listing(outside)
            base_before = _listing(base)
            pin = pinned_writer.open_pinned_root(pin_requested)
            evidence["pin"] = {
                "path": pin.path,
                "dev": pin.dev,
                "ino": pin.ino,
                "fd": pin.fd,
            }
            writer = pinned_writer.ScratchWriter(pin)
            write_sig = inspect.signature(pinned_writer.ScratchWriter.write_file)
            verify_sig = inspect.signature(pinned_writer.ScratchWriter.verify_file)
            evidence["signatures"] = {
                "write_file": [name for name in write_sig.parameters],
                "verify_file": [name for name in verify_sig.parameters],
            }
            legal = writer.write_file("legal.txt", SENTINEL)
            legal_read = _read_nofollow(pin.path, "legal.txt")
            verified = writer.verify_file("legal.txt", SENTINEL)
            root_errors = []
            for label, call in (
                (
                    "write_keyword",
                    lambda: writer.write_file("x.txt", "no", root=outside),
                ),
                (
                    "write_positional",
                    lambda: writer.write_file("x.txt", "no", outside),
                ),
                (
                    "verify_keyword",
                    lambda: writer.verify_file("legal.txt", SENTINEL, root=outside),
                ),
            ):
                try:
                    value = call()
                    root_errors.append({
                        "label": label,
                        "raised": False,
                        "value": value,
                    })
                except TypeError as exc:
                    root_errors.append({
                        "label": label,
                        "raised": True,
                        "type": "TypeError",
                        "message": str(exc),
                    })
            escape = writer.write_file("../escaped.txt", ESCAPE_BODY)
            absolute = writer.write_file(abs_target, ESCAPE_BODY)
            audit = _audit_text(pin.path)
            audit_text = audit.get("text") or ""
            evidence.update({
                "operations": {
                    "legal_write": legal,
                    "legal_independent_read": legal_read,
                    "legal_verify": verified,
                    "root_substitution": root_errors,
                    "escape_write": escape,
                    "absolute_write": absolute,
                },
                "after": {
                    "pin_listing": _listing(pin.path),
                    "outside_listing": _listing(outside),
                    "base_listing": _listing(base),
                    "canary": _ident(canary_path),
                    "escape_target": _ident(escape_target),
                    "abs_target": _ident(abs_target),
                    "pin_fd": {
                        "dev": os.fstat(pin.fd).st_dev,
                        "ino": os.fstat(pin.fd).st_ino,
                        "path": confine.fd_path(pin.fd),
                    },
                },
                "audit": audit,
                "canary_before": canary_before,
                "outside_before": outside_before,
                "base_before": base_before,
            })
            checks = {
                "signature_has_no_root": (
                    "root" not in write_sig.parameters
                    and "root" not in verify_sig.parameters
                    and list(write_sig.parameters) == [
                        "self", "relative_path", "content",
                    ]
                    and list(verify_sig.parameters) == [
                        "self", "relative_path", "expected_content",
                    ]
                ),
                "legal_ok": legal.get("ok") is True and legal.get("status") == "verified",
                "legal_bytes": (
                    legal_read.get("text") == SENTINEL
                    and legal_read.get("mode") == 0o644
                ),
                "verify_ok": (
                    verified.get("ok") is True
                    and verified.get("verification") == "match"
                ),
                "sentinel_absent_from_audit": SENTINEL not in audit_text,
                "escape_body_absent_from_audit": ESCAPE_BODY not in audit_text,
                "root_calls_typeerror": all(
                    item.get("raised") is True and item.get("type") == "TypeError"
                    for item in root_errors
                ) and len(root_errors) == 3,
                "escape_rejected": escape.get("ok") is False,
                "absolute_rejected": absolute.get("ok") is False,
                "escape_absent": evidence["after"]["escape_target"]["exists"] is False,
                "abs_absent": evidence["after"]["abs_target"]["exists"] is False,
                "canary_inode": (
                    evidence["after"]["canary"].get("ino") == canary_before.get("ino")
                    and evidence["after"]["canary"].get("size") == canary_before.get("size")
                    and evidence["after"]["canary"].get("mtime_ns")
                    == canary_before.get("mtime_ns")
                ),
                "outside_names_unchanged": (
                    evidence["after"]["outside_listing"].get("names")
                    == outside_before.get("names")
                ),
                "pin_fd_identity": (
                    evidence["after"]["pin_fd"]["ino"] == pin.ino
                    and evidence["after"]["pin_fd"]["path"] == pin.path
                ),
                "no_file_outside_pin_names": (
                    "escaped.txt" not in (evidence["after"]["base_listing"].get("names") or [])
                    and "abs_target.txt" not in (evidence["after"]["base_listing"].get("names") or [])
                    and "x.txt" not in (evidence["after"]["pin_listing"].get("names") or [])
                ),
            }
            evidence["checks"] = checks
            evidence["verdict"] = "PASS" if all(checks.values()) else "FAIL"
        except Exception as exc:
            evidence["exception"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "trace": traceback.format_exc(),
            }
            evidence["verdict"] = "FAIL"
        finally:
            if writer is not None:
                writer.close()
            path = _dump("t1", evidence)
            if evidence.get("verdict") == "PASS":
                shutil.rmtree(base)
            else:
                evidence["preserved_directory"] = base
                _dump("t1", evidence)
        self.assertEqual(
            evidence.get("verdict"),
            "PASS",
            "T1 failed; evidence %s checks %s"
            % (path, evidence.get("checks")),
        )

    def test_t8_protected_paths(self):
        evidence = {
            "test": "T8",
            "setup": "open_pinned_root on protected paths; os.open guard records and refuses those paths",
            "limitations": [
                "Identity is lstat only. FAISS and memory bodies were not read or hashed.",
                "A live server may change memory or FAISS size or mtime during the samples. An inode change is a failure. A size or mtime change with no os.open of that path is recorded as UNKNOWN and is not attributed to this writer.",
                "Full production directory listings are not copied into the evidence file. Probe-name absence and directory identity are recorded.",
            ],
        }
        before = {name: _ident(path) for name, path, _kind in PROTECTED}
        probe_before = {
            name: _probe_name_present(path, before[name])
            for name, path, _kind in PROTECTED
        }
        opened = []
        real_open = os.open

        def guarded_open(path, flags, *args, **kwargs):
            if "dir_fd" not in kwargs and _under_protected(path):
                opened.append({
                    "path": path.decode("utf-8", "replace") if isinstance(path, bytes) else path,
                    "flags": flags,
                    "stack": [
                        "%s:%s:%s" % (frame.filename, frame.lineno, frame.name)
                        for frame in traceback.extract_stack(limit=12)[:-1]
                    ],
                })
                raise OSError(errno.EPERM, "T8 guard refused a protected open")
            return real_open(path, flags, *args, **kwargs)

        attempts = []
        os.open = guarded_open
        try:
            for name, path, kind in PROTECTED:
                try:
                    pin = pinned_writer.open_pinned_root(path)
                except confine.ConfineError as exc:
                    attempts.append({
                        "name": name,
                        "path": path,
                        "expected_kind": kind,
                        "raised": exc.reason,
                        "pin_returned": False,
                    })
                    continue
                pin_fd = getattr(pin, "fd", None)
                attempts.append({
                    "name": name,
                    "path": path,
                    "expected_kind": kind,
                    "raised": None,
                    "pin_returned": True,
                    "pin_path": getattr(pin, "path", None),
                    "pin_ino": getattr(pin, "ino", None),
                })
                if pin_fd is not None:
                    os.close(pin_fd)
        finally:
            os.open = real_open
        after = {name: _ident(path) for name, path, _kind in PROTECTED}
        probe_after = {
            name: _probe_name_present(path, after[name])
            for name, path, _kind in PROTECTED
        }
        deltas = {}
        for name, _path, _kind in PROTECTED:
            left = before[name]
            right = after[name]
            deltas[name] = {
                "inode_changed": left.get("ino") != right.get("ino"),
                "size_changed": left.get("size") != right.get("size"),
                "mtime_changed": left.get("mtime_ns") != right.get("mtime_ns"),
                "exists_before": left.get("exists"),
                "exists_after": right.get("exists"),
                "kind_before": left.get("kind"),
                "kind_after": right.get("kind"),
            }
        expected_reason = {
            "dir": "root_protected",
            "file": "root_not_directory",
            "missing": "root_missing",
        }
        reason_ok = True
        for item in attempts:
            observed = before[item["name"]]
            if observed.get("exists") is False:
                want = "root_missing"
            elif observed.get("kind") == "dir":
                want = expected_reason["dir"]
            elif observed.get("kind") == "file":
                want = expected_reason["file"]
            elif observed.get("kind") == "symlink":
                want = "root_symlink"
            else:
                want = expected_reason[item["expected_kind"]]
            item["want"] = want
            item["reason_ok"] = item["raised"] == want and item["pin_returned"] is False
            if not item["reason_ok"]:
                reason_ok = False
        inode_stable = all(not item["inode_changed"] for item in deltas.values())
        content_flutter = {
            name: item for name, item in deltas.items()
            if item["size_changed"] or item["mtime_changed"]
        }
        probes_absent = all(value is False for value in probe_after.values())
        files_remain = all(
            item["exists_before"] == item["exists_after"] for item in deltas.values()
        )
        checks = {
            "every_open_refused": reason_ok and len(attempts) == len(PROTECTED),
            "no_pin_returned": all(item["pin_returned"] is False for item in attempts),
            "os_open_not_called_on_protected": opened == [],
            "inodes_stable": inode_stable,
            "protected_paths_still_present": files_remain,
            "probe_names_absent": probes_absent,
        }
        if content_flutter and opened == [] and inode_stable:
            flutter_note = "UNKNOWN"
        elif content_flutter:
            flutter_note = "FAIL"
        else:
            flutter_note = "PASS"
        evidence.update({
            "before": before,
            "after": after,
            "deltas": deltas,
            "probe_before": probe_before,
            "probe_after": probe_after,
            "attempts": attempts,
            "protected_open_attempts": opened,
            "content_identity": flutter_note,
            "checks": checks,
        })
        mandatory = all(checks.values())
        evidence["verdict"] = "PASS" if mandatory else "FAIL"
        if content_flutter and evidence["verdict"] == "PASS":
            evidence["content_identity_detail"] = (
                "Size or mtime changed and this process did not os.open those "
                "paths. Cause is UNKNOWN. Inodes were stable. Not converted "
                "into a failure and not attributed to ScratchWriter."
            )
        path = _dump("t8", evidence)
        self.assertEqual(
            evidence["verdict"],
            "PASS",
            "T8 failed; evidence %s checks %s opens %s"
            % (path, checks, opened),
        )

    def test_t2_live_rename(self):
        evidence = {
            "test": "T2",
            "setup": (
                "A racing thread lists the pinned directory and, while "
                "write_file is still on the pinned_writer stack and the "
                "temp name is visible, renames that directory aside and "
                "mkdirs a replacement at the pinned path. Payload is "
                "1_048_576 'Z' characters. No sleep was added to the writer."
            ),
            "trials": [],
            "limitations": [
                "Seeing the temp name proves the rename overlapped the temp's lifetime, which includes the write. It does not prove the rename fell in the interval between a passing check and os.link.",
                "A rename that the poller refused because write_file had already returned is not scored.",
                "Cross-process audit interleaving was not tested.",
            ],
        }
        payload = "Z" * confine.MAX_CONTENT_BYTES
        payload_sha = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        evidence["payload_bytes"] = len(payload.encode("utf-8"))
        evidence["payload_sha256"] = payload_sha
        winner = None
        preserved = None
        try:
            for trial in range(1, MAX_TRIALS + 1):
                outcome = _one_rename_trial(trial, payload)
                summary = {
                    "trial": trial,
                    "saw_temp": outcome.get("saw_temp"),
                    "renamed_during_call": outcome.get("renamed_during_call"),
                    "refused_post_return": outcome.get("refused_post_return"),
                    "ok": (outcome.get("result") or {}).get("ok"),
                    "status": (outcome.get("result") or {}).get("status"),
                    "reason": (outcome.get("result") or {}).get("reason"),
                    "audit_recorded": (outcome.get("result") or {}).get("audit_recorded"),
                    "replacement_names": (
                        (outcome.get("replacement_listing") or {}).get("names")
                    ),
                    "moved_names": (outcome.get("moved_listing") or {}).get("names"),
                    "poller_error": outcome.get("poller_error"),
                    "writer_error": outcome.get("writer_error"),
                }
                evidence["trials"].append(summary)
                if outcome.get("fatal"):
                    winner = outcome
                    preserved = outcome.get("base")
                    evidence["fatal_trial"] = _public_trial(outcome)
                    evidence["verdict"] = "FAIL"
                    break
                if outcome.get("renamed_during_call"):
                    winner = outcome
                    scored = _score_rename_trial(outcome)
                    evidence["scored"] = scored
                    evidence["observed"] = _public_trial(outcome)
                    if scored["pass"]:
                        evidence["verdict"] = "PASS"
                        _close_and_remove(outcome)
                    else:
                        evidence["verdict"] = "FAIL"
                        preserved = outcome.get("base")
                        _close_only(outcome)
                    break
                _close_and_remove(outcome)
            else:
                evidence["verdict"] = "UNKNOWN"
                evidence["unknown_reason"] = (
                    "No trial observed a rename while write_file was still "
                    "inside pinned_writer.py and a .swtmp_ name was listed. "
                    "Trial count %s. This is not a pass." % MAX_TRIALS
                )
        except Exception as exc:
            evidence["exception"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "trace": traceback.format_exc(),
            }
            evidence["verdict"] = "FAIL"
            if winner is not None:
                preserved = winner.get("base")
                _close_only(winner)
        if preserved is not None:
            evidence["preserved_directory"] = preserved
        path = _dump("t2", evidence)
        self.assertEqual(
            evidence.get("verdict"),
            "PASS",
            "T2 %s; evidence %s" % (evidence.get("verdict"), path),
        )


def _public_trial(outcome):
    """Drop the live writer object before JSON serialization."""
    skip = {"writer", "pin"}
    public = {}
    for key, value in outcome.items():
        if key in skip:
            continue
        public[key] = value
    return public


def _close_only(outcome):
    writer = outcome.get("writer")
    if writer is not None:
        try:
            writer.close()
        except OSError:
            pass
        outcome["writer"] = None


def _close_and_remove(outcome):
    _close_only(outcome)
    base = outcome.get("base")
    if base and os.path.isdir(base):
        shutil.rmtree(base)


def _score_rename_trial(outcome):
    result = outcome.get("result") or {}
    replacement_names = (outcome.get("replacement_listing") or {}).get("names")
    moved_names = (outcome.get("moved_listing") or {}).get("names") or []
    records = (outcome.get("moved_audit") or {}).get("records") or []
    success = _success_records(records)
    audit_present = (outcome.get("moved_audit") or {}).get("present") is True
    published_present = T2_NAME in moved_names
    temp_present = any(name.startswith(confine.TEMP_PREFIX) for name in moved_names)
    status = result.get("status")
    reason = result.get("reason")
    cleanup_ok = False
    # A cleaned publication is status "rejected" and reason
    # "identity_mismatch". publish_cleanup_failed and temp_cleanup_failed
    # use that same string for both status and reason, and the leftover
    # name must still be listed.
    if (
        status == "rejected"
        and reason == "identity_mismatch"
        and not published_present
        and not temp_present
    ):
        cleanup_ok = True
    elif (
        status == "publish_cleanup_failed"
        and reason == "publish_cleanup_failed"
        and published_present
    ):
        cleanup_ok = True
    elif (
        status == "temp_cleanup_failed"
        and reason == "temp_cleanup_failed"
        and temp_present
        and not published_present
    ):
        cleanup_ok = True
    pin_ino = outcome.get("pin_ino")
    moved_ino = (outcome.get("moved_ident") or {}).get("ino")
    replacement_ino = (outcome.get("replacement_ident") or {}).get("ino")
    fd_ino = (outcome.get("fd_after") or {}).get("ino")
    checks = {
        "renamed_during_call": outcome.get("renamed_during_call") is True,
        "ok_false": result.get("ok") is False,
        "accepted_false": result.get("accepted") is False,
        "audit_recorded_false": result.get("audit_recorded") is False,
        "replacement_empty": replacement_names == [],
        "replacement_inode_differs": (
            replacement_ino is not None and replacement_ino != pin_ino
        ),
        "moved_inode_is_pin": moved_ino == pin_ino and fd_ino == pin_ino,
        "no_success_audit": success == [] and not audit_present,
        "cleanup_matches_listing": cleanup_ok,
        "file_not_reported_verified": result.get("status") != "verified",
    }
    return {"pass": all(checks.values()), "checks": checks, "success_audit": success}


def _one_rename_trial(trial, payload):
    base = tempfile.mkdtemp(prefix="swpin_t2_%02d_" % trial)
    requested = base + "/pin"
    os.mkdir(requested, 0o700)
    pin = pinned_writer.open_pinned_root(requested)
    writer = pinned_writer.ScratchWriter(pin)
    parent = pin.path.rsplit("/", 1)[0]
    moved = parent + "/moved"
    state = {
        "renamed_during_call": False,
        "saw_temp": False,
        "temp_name": None,
        "refused_post_return": False,
        "finished_ns": 0,
        "poller_error": None,
        "writer_error": None,
        "result": None,
        "fatal": False,
    }
    decision = threading.Lock()
    writer_started = threading.Event()

    def poller():
        try:
            while state["finished_ns"] == 0:
                try:
                    names = os.listdir(pin.path)
                except FileNotFoundError:
                    continue
                temps = [name for name in names if name.startswith(confine.TEMP_PREFIX)]
                if not temps:
                    continue
                state["saw_temp"] = True
                state["temp_name"] = temps[0]
                with decision:
                    if state["finished_ns"] != 0 or not _thread_in_pinned_writer(
                        writer_thread.ident
                    ):
                        state["refused_post_return"] = True
                        return
                    os.rename(pin.path, moved)
                    os.mkdir(pin.path, 0o700)
                    state["renamed_during_call"] = True
                    return
        except Exception as exc:
            state["poller_error"] = "%s: %s" % (type(exc).__name__, exc)
            state["fatal"] = True

    def runner():
        writer_started.set()
        try:
            state["result"] = writer.write_file(T2_NAME, payload)
        except Exception as exc:
            state["writer_error"] = "%s: %s" % (type(exc).__name__, exc)
            state["fatal"] = True
        finally:
            with decision:
                state["finished_ns"] = 1

    writer_thread = threading.Thread(target=runner)
    poller_thread = threading.Thread(target=poller)
    poller_thread.start()
    writer_thread.start()
    writer_started.wait(5)
    writer_thread.join(120)
    if writer_thread.is_alive():
        state["writer_error"] = "writer thread still alive after 120s"
        state["fatal"] = True
        with decision:
            state["finished_ns"] = 1
    poller_thread.join(10)
    outcome = {
        "trial": trial,
        "base": os.path.dirname(pin.path),
        "pin_path": pin.path,
        "pin_dev": pin.dev,
        "pin_ino": pin.ino,
        "moved_path": moved,
        "writer": writer,
        "pin": pin,
        "saw_temp": state["saw_temp"],
        "temp_name": state["temp_name"],
        "renamed_during_call": state["renamed_during_call"],
        "refused_post_return": state["refused_post_return"],
        "poller_error": state["poller_error"],
        "writer_error": state["writer_error"],
        "result": state["result"],
        "fatal": state["fatal"],
    }
    if state["renamed_during_call"] or state["fatal"]:
        outcome["fd_after"] = _fd_identity(pin.fd)
        outcome["moved_ident"] = _ident(moved)
        outcome["replacement_ident"] = _ident(pin.path)
        outcome["moved_listing"] = _listing(moved)
        outcome["replacement_listing"] = _listing(pin.path)
        outcome["moved_audit"] = (
            _audit_text(moved) if os.path.isdir(moved) else {"present": False, "records": []}
        )
        outcome["replacement_audit"] = (
            _audit_text(pin.path) if os.path.isdir(pin.path) else {"present": False, "records": []}
        )
        if os.path.isdir(moved) and T2_NAME in (outcome["moved_listing"].get("names") or []):
            read = _read_nofollow(moved, T2_NAME)
            read.pop("text", None)
            outcome["moved_published_read"] = read
        if os.path.isdir(pin.path) and T2_NAME in (
            outcome["replacement_listing"].get("names") or []
        ):
            read = _read_nofollow(pin.path, T2_NAME)
            read.pop("text", None)
            outcome["replacement_published_read"] = read
            outcome["fatal"] = True
        replacement_names = outcome["replacement_listing"].get("names") or []
        if replacement_names:
            outcome["fatal"] = True
        if state["result"] is not None and state["result"].get("ok") is True:
            outcome["fatal"] = True
    return outcome


def _fd_identity(fd):
    try:
        info = os.fstat(fd)
        path = confine.fd_path(fd)
    except OSError as exc:
        return {"error": exc.errno}
    except confine.ConfineError as exc:
        return {"error": exc.reason}
    return {"dev": info.st_dev, "ino": info.st_ino, "path": path}


if __name__ == "__main__":
    unittest.main()
