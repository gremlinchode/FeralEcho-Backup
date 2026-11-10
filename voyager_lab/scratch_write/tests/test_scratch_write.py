"""Security suite for the scratch-only writer.

The suite creates temporary directories under the system temp area and
asserts filesystem state. It does not contact port 5000, import the
FeralEcho application, read production memory bodies, or hash the FAISS
index. Production paths are offered only as rejected roots, after
open_root has already refused them.

Escape attempts that use '..' or a symlink stop inside the temporary
parent. They are not aimed at the production tree: a broken check would
otherwise write there.
"""

import ast
import errno
import hashlib
import inspect
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path

TOOL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TOOL_DIR not in sys.path:
    sys.path.insert(0, TOOL_DIR)

PROD = "/Users/richietate/Desktop/FeralEcho"
VOY = "/Users/richietate/Desktop/FeralEcho-voyager"
VOY_LAB = os.path.join(VOY, "voyager_lab")
FAISS = os.path.join(PROD, "memory", "faiss.index")
PROBE = "scratch_write_probe_8f3c1d0e.txt"
SENTINEL = "SENTINEL_CONTENT_8f3c1d0e"
CANARY = b"CANARY-SAFE"

_FAISS_BEFORE_IMPORT = None


def _faiss_id():
    st = os.lstat(FAISS)
    return (st.st_ino, st.st_size, st.st_mtime_ns, st.st_mode)


_FAISS_BEFORE_IMPORT = _faiss_id()

import confine  # noqa: E402
import verify_file  # noqa: E402
import write_file  # noqa: E402

_FAISS_AFTER_IMPORT = _faiss_id()
if _FAISS_BEFORE_IMPORT[:2] != _FAISS_AFTER_IMPORT[:2]:
    raise RuntimeError("faiss inode or size changed while importing scratch_write")

WATCH_DIRS = (
    PROD,
    os.path.join(PROD, "memory"),
    os.path.join(PROD, "app"),
    os.path.join(PROD, "app", "core"),
    VOY,
    VOY_LAB,
    os.path.join(VOY_LAB, "voyager"),
    os.path.join(VOY_LAB, "results"),
    TOOL_DIR,
)
PROBE_WATCH = WATCH_DIRS + (
    "/tmp",
    "/private/tmp",
    "/Users/richietate/Desktop",
    "/dev",
)

FROZEN_FILES = (
    os.path.join(PROD, "echo_principles.json"),
    os.path.join(PROD, "Modelfile"),
    os.path.join(PROD, "run.py"),
    os.path.join(PROD, "app", "core", "echo_tool_dispatch.py"),
    os.path.join(VOY_LAB, "voyager", "__init__.py"),
    os.path.join(VOY_LAB, "voyager", "atomic.py"),
    os.path.join(VOY_LAB, "voyager", "baseline.py"),
    os.path.join(VOY_LAB, "voyager", "engine.py"),
    os.path.join(VOY_LAB, "voyager", "grader.py"),
    os.path.join(VOY_LAB, "voyager", "harness.py"),
    os.path.join(VOY_LAB, "voyager", "procedures.py"),
    os.path.join(VOY_LAB, "voyager", "rubric.py"),
    os.path.join(VOY_LAB, "voyager", "suite_spec.py"),
    os.path.join(VOY_LAB, "voyager", "worker.py"),
    os.path.join(VOY_LAB, "voyager", "world.py"),
    os.path.join(VOY_LAB, "self_check.py"),
    os.path.join(VOY_LAB, "freeze.py"),
    os.path.join(VOY_LAB, "run_experiment.py"),
    os.path.join(VOY_LAB, "RUBRIC_FREEZE.json"),
    os.path.join(VOY_LAB, "results", "summary.json"),
    os.path.join(VOY_LAB, "FIRST_LOCAL_SKILL_RESEARCH.md"),
    os.path.join(VOY_LAB, "CAB_ADVERSARIAL_REVIEW.md"),
    os.path.join(VOY_LAB, "ASSESSMENT.md"),
    os.path.join(VOY_LAB, "CAPABILITY_ACQUISITION.md"),
    os.path.join(VOY_LAB, "README.md"),
    os.path.join(TOOL_DIR, "confine.py"),
    os.path.join(TOOL_DIR, "write_file.py"),
    os.path.join(TOOL_DIR, "verify_file.py"),
)

LIVE_DIRS = {
    PROD,
    os.path.join(PROD, "memory"),
    os.path.join(PROD, "app"),
    os.path.join(PROD, "app", "core"),
}

FORBIDDEN_MODULES = {
    "app",
    "socket",
    "subprocess",
    "urllib",
    "faiss",
    "requests",
    "echo_tool_dispatch",
    "http",
    "ftplib",
    "smtplib",
    "ctypes",
    "importlib",
    "runpy",
    "shutil",
}

_NOTES = []
_BEFORE_FILES = None
_BEFORE_RESULTS = None
_BEFORE_VOYAGER = None
_BEFORE_FAISS = None
_VOYAGER_NAMES = None


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_id(path):
    st = os.lstat(path)
    if stat.S_ISLNK(st.st_mode):
        body = os.readlink(path).encode()
        kind = "symlink"
        digest = hashlib.sha256(body).hexdigest()
    elif stat.S_ISREG(st.st_mode):
        kind = "file"
        digest = _sha256_file(path)
    else:
        kind = "other"
        digest = None
    return (kind, st.st_mode, st.st_ino, st.st_size, st.st_mtime_ns, digest)


def _tree_manifest(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        filenames.sort()
        for name in dirnames:
            path = os.path.join(dirpath, name)
            st = os.lstat(path)
            rel = os.path.relpath(path, root)
            out[rel] = ("dir", st.st_mode, st.st_ino, st.st_size, st.st_mtime_ns, None)
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            out[rel] = _file_id(path)
    return out


def _names(path):
    return sorted(name for name in os.listdir(path) if name != "__pycache__")


def _preflight():
    if not os.path.isdir(PROD) or not os.path.isdir(VOY) or not os.path.isdir(VOY_LAB):
        raise RuntimeError("protected roots are missing")
    for path in FROZEN_FILES:
        if not os.path.isfile(path) or os.path.islink(path):
            raise RuntimeError("frozen file missing: " + path)
    if not os.path.isfile(FAISS) or os.path.islink(FAISS):
        raise RuntimeError("faiss index missing")
    if tuple(confine.PROTECTED_ROOTS) != (PROD, VOY):
        raise RuntimeError("denylist constants differ from this suite")
    if not confine.is_protected_path(PROD) or not confine.is_protected_path(VOY):
        raise RuntimeError("denylist preflight failed")
    if confine.is_within(VOY, PROD):
        raise RuntimeError("voyager treated as inside production")
    if not VOY.startswith(PROD):
        raise RuntimeError("the prefix trap this suite documents is absent")
    for directory in WATCH_DIRS:
        if not os.path.isdir(directory):
            raise RuntimeError("watch directory missing: " + directory)
        audit = os.path.join(directory, confine.AUDIT_NAME)
        if os.path.lexists(audit):
            raise RuntimeError("unexpected audit present: " + audit)
    for directory in PROBE_WATCH:
        probe = os.path.join(directory, PROBE)
        if os.path.lexists(probe):
            raise RuntimeError("unexpected probe present: " + probe)


_preflight()


def setUpModule():
    global _BEFORE_FILES, _BEFORE_RESULTS, _BEFORE_VOYAGER, _BEFORE_FAISS, _VOYAGER_NAMES
    _BEFORE_FILES = {path: _file_id(path) for path in FROZEN_FILES}
    _BEFORE_RESULTS = _tree_manifest(os.path.join(VOY_LAB, "results"))
    _BEFORE_VOYAGER = _tree_manifest(os.path.join(VOY_LAB, "voyager"))
    _VOYAGER_NAMES = _names(os.path.join(VOY_LAB, "voyager"))
    _BEFORE_FAISS = _faiss_id()


def tearDownModule():
    problems = []
    for path, before in _BEFORE_FILES.items():
        after = _file_id(path)
        if after != before:
            problems.append("frozen file changed: " + path)
    results = _tree_manifest(os.path.join(VOY_LAB, "results"))
    if results != _BEFORE_RESULTS:
        changed = sorted(set(results) ^ set(_BEFORE_RESULTS))
        changed += sorted(
            key for key in set(results) & set(_BEFORE_RESULTS) if results[key] != _BEFORE_RESULTS[key]
        )
        problems.append("results tree changed: " + ", ".join(changed[:20]))
    voyager = _tree_manifest(os.path.join(VOY_LAB, "voyager"))
    if voyager != _BEFORE_VOYAGER:
        problems.append("voyager tree changed")
    if _names(os.path.join(VOY_LAB, "voyager")) != _VOYAGER_NAMES:
        problems.append("voyager names changed")
    after_faiss = _faiss_id()
    if after_faiss[:2] != _BEFORE_FAISS[:2]:
        problems.append(
            "faiss inode or size changed: before=%s after=%s" % (_BEFORE_FAISS[:2], after_faiss[:2])
        )
    elif after_faiss[2] != _BEFORE_FAISS[2]:
        _NOTES.append(
            "faiss mtime changed during the suite; inode and size stayed %s %s"
            % (after_faiss[0], after_faiss[1])
        )
    for directory in WATCH_DIRS:
        audit = os.path.join(directory, confine.AUDIT_NAME)
        probe = os.path.join(directory, PROBE)
        if os.path.lexists(audit):
            problems.append("audit appeared: " + audit)
        if os.path.lexists(probe):
            problems.append("probe appeared: " + probe)
    if problems:
        raise AssertionError("\n".join(problems))
    if _NOTES:
        print("SCRATCH_WRITE_NOTES " + " | ".join(_NOTES))


def _read_nofollow(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise AssertionError("not a regular file: " + path)
        data = os.read(fd, st.st_size + 1)
        if len(data) != st.st_size:
            raise AssertionError("short read: " + path)
        return data, st
    finally:
        os.close(fd)


def _swtmp(directory):
    found = []
    for dirpath, dirnames, filenames in os.walk(directory, followlinks=False):
        for name in filenames:
            if name.startswith(confine.TEMP_PREFIX):
                found.append(os.path.join(dirpath, name))
    return found


def _audit_bytes(scratch):
    path = os.path.join(scratch, confine.AUDIT_NAME)
    if not os.path.isfile(path) or os.path.islink(path):
        return b""
    data, _st = _read_nofollow(path)
    return data


def _audit_records(scratch):
    raw = _audit_bytes(scratch)
    if not raw:
        return []
    return [json.loads(line) for line in raw.decode("ascii").splitlines()]


class ScratchWriteTests(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.TemporaryDirectory(prefix="scratch_write_test_")
        self.addCleanup(self.parent.cleanup)
        self.parent_path = self.parent.name
        self._require_temp(self.parent_path)
        self.scratch = os.path.join(self.parent_path, "scratch")
        os.mkdir(self.scratch, 0o755)
        self.canary = os.path.join(self.parent_path, "canary.txt")
        fd = os.open(self.canary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
        try:
            os.write(fd, CANARY)
        finally:
            os.close(fd)
        self.canary_id = os.lstat(self.canary)

    def _require_temp(self, path):
        real = os.path.realpath(path)
        prefixes = ("/private/var/folders/", "/var/folders/", "/private/tmp/", "/tmp/")
        if not real.startswith(prefixes):
            raise RuntimeError("refusing scratch outside system temp: " + real)
        if confine.is_protected_path(real) or confine.is_within(real, PROD) or confine.is_within(real, VOY):
            raise RuntimeError("scratch resolved into a protected tree: " + real)

    def _path(self, relative):
        return os.path.join(self.scratch, relative)

    def _assert_canary(self):
        data, st = _read_nofollow(self.canary)
        self.assertEqual(data, CANARY)
        self.assertEqual(st.st_ino, self.canary_id.st_ino)
        self.assertEqual(st.st_mtime_ns, self.canary_id.st_mtime_ns)
        self.assertEqual(stat.S_IMODE(st.st_mode), stat.S_IMODE(self.canary_id.st_mode))

    def _assert_rejected(self, result, reason):
        self.assertIsInstance(result, dict)
        self.assertFalse(result["ok"])
        self.assertFalse(result["accepted"])
        self.assertNotEqual(result["status"], "verified")
        self.assertEqual(result["reason"], reason)
        blob = json.dumps(result)
        self.assertNotIn(SENTINEL, blob)

    def _assert_absent(self, path):
        self.assertFalse(os.path.lexists(path))

    def _assert_created(self, relative, text):
        data, st = _read_nofollow(self._path(relative))
        self.assertEqual(data, text.encode("utf-8"))
        self.assertTrue(stat.S_ISREG(st.st_mode))
        self.assertFalse(stat.S_ISLNK(st.st_mode))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o644)
        self.assertEqual(st.st_nlink, 1)
        return data, st

    def test_a_normal_containment_uses_commonpath(self):
        self.assertTrue(VOY.startswith(PROD))
        self.assertFalse(confine.is_within(VOY, PROD))
        self.assertTrue(confine.is_protected_path(PROD))
        self.assertTrue(confine.is_protected_path(VOY))
        self.assertTrue(confine.is_protected_path(FAISS))
        self.assertTrue(confine.is_protected_path("/tmp"))
        self.assertTrue(confine.is_protected_path("/Users/richietate/Desktop"))
        self.assertFalse(confine.is_protected_path(self.scratch))
        self.assertFalse(confine.is_within(self.scratch, PROD))

    def test_a_normal_signatures_and_lock(self):
        write_sig = inspect.signature(write_file.write_file)
        verify_sig = inspect.signature(verify_file.verify_file)
        self.assertEqual(list(write_sig.parameters), ["root", "relative_path", "content"])
        self.assertEqual(list(verify_sig.parameters), ["root", "relative_path", "expected_content"])
        self.assertIs(write_file._lock(), confine.OPERATION_LOCK)
        self.assertIsInstance(confine.OPERATION_LOCK, type(threading.Lock()))

    def test_a_normal_source_isolation(self):
        for name in ("confine.py", "write_file.py", "verify_file.py"):
            path = os.path.join(TOOL_DIR, name)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            self.assertNotIn("5000", text)
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split(".")[0], FORBIDDEN_MODULES)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self.assertNotIn(node.module.split(".")[0], FORBIDDEN_MODULES)
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotEqual(node.func.id, "open")
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    owner = node.func.value
                    if isinstance(owner, ast.Name) and owner.id == "os":
                        self.assertNotIn(node.func.attr, ("system", "popen"))

    def test_a_normal_create_file(self):
        result = write_file.write_file(self.scratch, "note.txt", SENTINEL)
        self.assertTrue(result["ok"])
        self.assertTrue(result["accepted"])
        self.assertTrue(result["audit_recorded"])
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["verification"], "match")
        self.assertEqual(result["reason"], "verified")
        self.assertEqual(result["operation"], "write")
        self.assertEqual(result["path"], "note.txt")
        data, _st = self._assert_created("note.txt", SENTINEL)
        digest = hashlib.sha256(data).hexdigest()
        self.assertEqual(result["sha256"], digest)
        self.assertEqual(result["size"], len(data))
        self.assertNotIn(SENTINEL, json.dumps(result))
        raw = _audit_bytes(self.scratch)
        self.assertNotIn(SENTINEL.encode("utf-8"), raw)
        self.assertNotIn(b"\x00", raw)
        records = _audit_records(self.scratch)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["operation"], "write")
        self.assertEqual(records[0]["path"], "note.txt")
        self.assertTrue(records[0]["accepted"])
        self.assertEqual(records[0]["verification"], "match")
        self.assertEqual(records[0]["size"], len(data))
        self.assertEqual(records[0]["sha256"], digest)
        self.assertTrue(records[0]["timestamp"].endswith("Z"))
        audit = self._path(confine.AUDIT_NAME)
        _audit_data, audit_st = _read_nofollow(audit)
        self.assertEqual(stat.S_IMODE(audit_st.st_mode), 0o644)
        self.assertTrue(confine.is_within(audit, self.scratch))
        checked = verify_file.verify_file(self.scratch, "note.txt", SENTINEL)
        self.assertTrue(checked["ok"])
        self.assertEqual(checked["operation"], "verify")
        self.assertEqual(checked["sha256"], digest)
        again, _st2 = self._assert_created("note.txt", SENTINEL)
        self.assertEqual(again, data)

    def test_a_normal_subdirectory(self):
        os.mkdir(self._path("nested"), 0o755)
        text = "inside nested"
        result = write_file.write_file(self.scratch, "nested/inside.txt", text)
        self.assertTrue(result["ok"])
        self.assertEqual(result["path"], "nested/inside.txt")
        self._assert_created("nested/inside.txt", text)
        self.assertEqual(_swtmp(self.scratch), [])
        checked = verify_file.verify_file(self.scratch, "nested/inside.txt", text)
        self.assertTrue(checked["ok"])

    def test_a_normal_unicode(self):
        text = "café — 日本語\nsecond"
        result = write_file.write_file(self.scratch, "unicode.txt", text)
        self.assertTrue(result["ok"])
        data, _st = self._assert_created("unicode.txt", text)
        self.assertEqual(result["sha256"], hashlib.sha256(data).hexdigest())
        checked = verify_file.verify_file(self.scratch, "unicode.txt", text)
        self.assertTrue(checked["ok"])
        self.assertEqual(checked["sha256"], result["sha256"])

    def test_a_normal_multiline(self):
        text = "alpha\nbeta\r\ngamma\n"
        result = write_file.write_file(self.scratch, "lines.txt", text)
        self.assertTrue(result["ok"])
        data, _st = self._assert_created("lines.txt", text)
        self.assertEqual(data, b"alpha\nbeta\r\ngamma\n")
        checked = verify_file.verify_file(self.scratch, "lines.txt", text)
        self.assertTrue(checked["ok"])

    def test_a_normal_empty(self):
        result = write_file.write_file(self.scratch, "empty.txt", "")
        self.assertTrue(result["ok"])
        self.assertEqual(result["size"], 0)
        data, _st = self._assert_created("empty.txt", "")
        self.assertEqual(data, b"")
        self.assertEqual(result["sha256"], hashlib.sha256(b"").hexdigest())
        checked = verify_file.verify_file(self.scratch, "empty.txt", "")
        self.assertTrue(checked["ok"])

    def test_a_normal_max_size_accepted(self):
        text = "a" * confine.MAX_CONTENT_BYTES
        result = write_file.write_file(self.scratch, "max.txt", text)
        self.assertTrue(result["ok"])
        self.assertEqual(result["size"], confine.MAX_CONTENT_BYTES)
        data, _st = _read_nofollow(self._path("max.txt"))
        self.assertEqual(len(data), confine.MAX_CONTENT_BYTES)
        self.assertEqual(result["sha256"], hashlib.sha256(data).hexdigest())

    def test_a_normal_umask_exact_mode(self):
        previous = os.umask(0o077)
        self.addCleanup(os.umask, previous)
        result = write_file.write_file(self.scratch, "umask.txt", "mode")
        self.assertTrue(result["ok"])
        _data, st = self._assert_created("umask.txt", "mode")
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o644)

    def test_a_normal_content_is_not_executed(self):
        marker = os.path.join(self.parent_path, "executed.txt")
        text = "import pathlib\npathlib.Path(%r).write_text('pwned')\n" % marker
        result = write_file.write_file(self.scratch, "program.py", text)
        self.assertTrue(result["ok"])
        self._assert_created("program.py", text)
        self._assert_absent(marker)
        _data, st = _read_nofollow(self._path("program.py"))
        self.assertEqual(stat.S_IMODE(st.st_mode) & 0o111, 0)

    def test_a_normal_open_root_fd_path(self):
        opened = confine.open_root(self.scratch)
        try:
            self.assertEqual(confine.fd_path(opened.fd), os.path.realpath(self.scratch))
        finally:
            opened.close()

    def test_a_normal_nul_in_content_is_data(self):
        text = "a\x00b"
        result = write_file.write_file(self.scratch, "nul.txt", text)
        self.assertTrue(result["ok"])
        data, _st = self._assert_created("nul.txt", text)
        self.assertEqual(data, b"a\x00b")
        self.assertNotIn(b"\x00", _audit_bytes(self.scratch))

    def test_b_prohibit_dotdot(self):
        for relative in ("../canary.txt", "foo/../../canary.txt", "..", "foo/../bar.txt"):
            with self.subTest(relative=relative):
                result = write_file.write_file(self.scratch, relative, SENTINEL)
                self._assert_rejected(result, "path_dot_segment")
                self._assert_canary()
                self._assert_absent(self._path("foo"))
                self._assert_absent(self._path("bar.txt"))
                self.assertNotIn(SENTINEL.encode("utf-8"), _audit_bytes(self.scratch))

    def test_b_prohibit_dot_segment_and_empty_component(self):
        cases = {
            ".": "path_dot_segment",
            "./note.txt": "path_dot_segment",
            "foo/./bar.txt": "path_dot_segment",
            "foo//bar.txt": "path_empty_component",
            "foo/": "path_empty_component",
            "/": "path_absolute",
            "": "path_empty",
        }
        for relative, reason in cases.items():
            with self.subTest(relative=relative):
                result = write_file.write_file(self.scratch, relative, "x")
                self._assert_rejected(result, reason)
                self._assert_absent(self._path("note.txt"))
                self._assert_absent(self._path("bar.txt"))

    def test_b_prohibit_absolute_canary(self):
        result = write_file.write_file(self.scratch, self.canary, SENTINEL)
        self._assert_rejected(result, "path_absolute")
        self._assert_canary()
        outside_dir = os.path.join(self.parent_path, "outside")
        os.mkdir(outside_dir)
        absolute = os.path.join(outside_dir, "new.txt")
        result = write_file.write_file(self.scratch, absolute, SENTINEL)
        self._assert_rejected(result, "path_absolute")
        self._assert_absent(absolute)

    def test_b_prohibit_overwrite(self):
        first = write_file.write_file(self.scratch, "kept.txt", "ONE")
        self.assertTrue(first["ok"])
        before = os.lstat(self._path("kept.txt"))
        second = write_file.write_file(self.scratch, "kept.txt", "TWO")
        self._assert_rejected(second, "destination_exists")
        after_data, after = self._assert_created("kept.txt", "ONE")
        self.assertEqual(after_data, b"ONE")
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)

    def test_b_prohibit_overwrite_identical(self):
        first = write_file.write_file(self.scratch, "same.txt", "SAME")
        self.assertTrue(first["ok"])
        before = os.lstat(self._path("same.txt"))
        second = write_file.write_file(self.scratch, "same.txt", "SAME")
        self._assert_rejected(second, "destination_exists")
        after_data, after = _read_nofollow(self._path("same.txt"))
        self.assertEqual(after_data, b"SAME")
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)

    def test_b_prohibit_casefold(self):
        first = write_file.write_file(self.scratch, "Hello.txt", "ONE")
        self.assertTrue(first["ok"])
        second = write_file.write_file(self.scratch, "hello.txt", "TWO")
        self._assert_rejected(second, "destination_exists")
        data, _st = _read_nofollow(self._path("Hello.txt"))
        self.assertEqual(data, b"ONE")
        self.assertTrue(os.path.samefile(self._path("Hello.txt"), self._path("hello.txt")))

    def test_b_prohibit_unicode_normalization(self):
        nfc = "caf\u00e9.txt"
        nfd = "cafe\u0301.txt"
        first = write_file.write_file(self.scratch, nfc, "ONE")
        self.assertTrue(first["ok"])
        second = write_file.write_file(self.scratch, nfd, "TWO")
        self._assert_rejected(second, "destination_exists")
        data, _st = _read_nofollow(self._path(nfc))
        self.assertEqual(data, b"ONE")
        self.assertTrue(os.path.samefile(self._path(nfc), self._path(nfd)))

    def test_b_prohibit_symlink_destination(self):
        link = self._path("via")
        os.symlink(self.canary, link)
        before = os.lstat(self.canary)
        result = write_file.write_file(self.scratch, "via", SENTINEL)
        self._assert_rejected(result, "symlink_destination")
        self._assert_canary()
        after = os.lstat(self.canary)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertTrue(os.path.islink(link))
        self.assertEqual(os.readlink(link), self.canary)

    def test_b_prohibit_symlink_parent_escape(self):
        outside = os.path.join(self.parent_path, "outside")
        os.mkdir(outside)
        safe = os.path.join(outside, "safe.txt")
        fd = os.open(safe, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
        try:
            os.write(fd, b"SAFE")
        finally:
            os.close(fd)
        os.symlink(outside, self._path("escape"))
        os.symlink(safe, self._path("filelink"))
        before = os.lstat(safe)
        parent = write_file.write_file(self.scratch, "escape/new.txt", SENTINEL)
        nested = write_file.write_file(self.scratch, "filelink/new.txt", SENTINEL)
        self._assert_rejected(parent, "symlink_or_not_directory")
        self._assert_rejected(nested, "symlink_or_not_directory")
        self._assert_absent(os.path.join(outside, "new.txt"))
        data, after = _read_nofollow(safe)
        self.assertEqual(data, b"SAFE")
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertEqual(os.listdir(outside), ["safe.txt"])

    def test_b_prohibit_directory(self):
        os.mkdir(self._path("dirdest"), 0o755)
        result = write_file.write_file(self.scratch, "dirdest", SENTINEL)
        self._assert_rejected(result, "destination_directory")
        self.assertTrue(os.path.isdir(self._path("dirdest")))
        self.assertEqual(os.listdir(self._path("dirdest")), [])
        checked = verify_file.verify_file(self.scratch, "dirdest", SENTINEL)
        self._assert_rejected(checked, "destination_directory")
        self.assertEqual(os.listdir(self._path("dirdest")), [])

    def test_b_prohibit_socket(self):
        import socket

        path = self._path("sock")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(sock.close)
        sock.bind(path)
        before = os.lstat(path)
        result = write_file.write_file(self.scratch, "sock", SENTINEL)
        after = os.lstat(path)
        self._assert_rejected(result, "destination_not_regular")
        self.assertTrue(stat.S_ISSOCK(before.st_mode))
        self.assertEqual(before.st_mode, after.st_mode)
        self.assertEqual(before.st_ino, after.st_ino)
        checked = verify_file.verify_file(self.scratch, "sock", SENTINEL)
        self._assert_rejected(checked, "destination_not_regular")

    def test_b_prohibit_fifo(self):
        path = self._path("fifo")
        os.mkfifo(path, 0o644)
        before = os.lstat(path)
        result = write_file.write_file(self.scratch, "fifo", SENTINEL)
        after = os.lstat(path)
        self._assert_rejected(result, "destination_not_regular")
        self.assertTrue(stat.S_ISFIFO(before.st_mode))
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        checked = verify_file.verify_file(self.scratch, "fifo", SENTINEL)
        self._assert_rejected(checked, "destination_not_regular")

    def test_b_prohibit_dev_null_symlink_and_root(self):
        os.symlink("/dev/null", self._path("nulldev"))
        before = os.lstat("/dev/null")
        result = write_file.write_file(self.scratch, "nulldev", SENTINEL)
        after = os.lstat("/dev/null")
        self._assert_rejected(result, "symlink_destination")
        self.assertEqual(before.st_rdev, after.st_rdev)
        self.assertEqual(before.st_mode, after.st_mode)
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertTrue(os.path.islink(self._path("nulldev")))
        try:
            opened = confine.open_root("/dev/null")
        except confine.ConfineError as exc:
            self.assertEqual(exc.reason, "root_not_directory")
        else:
            opened.close()
            self.fail("open_root accepted /dev/null")
        rooted = write_file.write_file("/dev/null", PROBE, SENTINEL)
        self._assert_rejected(rooted, "root_not_directory")
        later = os.lstat("/dev/null")
        self.assertEqual(before.st_rdev, later.st_rdev)
        self.assertEqual(before.st_ino, later.st_ino)
        self._assert_absent("/dev/" + PROBE)

    def test_b_prohibit_executable_kwargs_and_mode(self):
        with self.assertRaises(TypeError):
            write_file.write_file(self.scratch, "exec.txt", "x", mode=0o755)
        self._assert_absent(self._path("exec.txt"))
        path = self._path("already.py")
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o755)
        try:
            os.write(fd, b"print(1)\n")
        finally:
            os.close(fd)
        before = os.lstat(path)
        result = write_file.write_file(self.scratch, "already.py", "print(2)\n")
        self._assert_rejected(result, "destination_exists")
        data, after = _read_nofollow(path)
        self.assertEqual(data, b"print(1)\n")
        self.assertEqual(stat.S_IMODE(before.st_mode), 0o755)
        self.assertEqual(stat.S_IMODE(after.st_mode), 0o755)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        checked = verify_file.verify_file(self.scratch, "already.py", "print(1)\n")
        self._assert_rejected(checked, "mode_unexpected")
        _data, final = _read_nofollow(path)
        self.assertEqual(stat.S_IMODE(final.st_mode), 0o755)

    def test_b_prohibit_shebang_not_executable(self):
        text = "#!/bin/sh\necho hi\n"
        result = write_file.write_file(self.scratch, "script.sh", text)
        self.assertTrue(result["ok"])
        _data, st = self._assert_created("script.sh", text)
        self.assertEqual(stat.S_IMODE(st.st_mode) & 0o111, 0)

    def test_b_prohibit_oversized_chars(self):
        text = "b" * (confine.MAX_CONTENT_BYTES + 1)
        result = write_file.write_file(self.scratch, "big.txt", text)
        self._assert_rejected(result, "content_too_large")
        self._assert_absent(self._path("big.txt"))
        self.assertEqual(_swtmp(self.scratch), [])
        raw = _audit_bytes(self.scratch)
        self.assertLess(len(raw), 4000)
        self.assertNotIn(b"bbb", raw)

    def test_b_prohibit_oversized_utf8(self):
        text = "😀" * 262145
        self.assertLess(len(text), confine.MAX_CONTENT_BYTES)
        self.assertGreater(len(text.encode("utf-8")), confine.MAX_CONTENT_BYTES)
        result = write_file.write_file(self.scratch, "emoji.txt", text)
        self._assert_rejected(result, "content_too_large")
        self._assert_absent(self._path("emoji.txt"))
        self.assertEqual(_swtmp(self.scratch), [])

    def test_b_prohibit_unsupported_types(self):
        class Sub(str):
            pass

        samples = (
            b"bytes",
            bytearray(b"ba"),
            None,
            1,
            1.5,
            ["list"],
            {"dict": 1},
            Sub("subclass"),
        )
        for sample in samples:
            with self.subTest(sample=type(sample).__name__):
                result = write_file.write_file(self.scratch, "bad.txt", sample)
                self._assert_rejected(result, "content_type")
                self._assert_absent(self._path("bad.txt"))
        rooted = write_file.write_file(Path(self.scratch), "bad.txt", "x")
        self._assert_rejected(rooted, "root_type")
        self._assert_absent(self._path("bad.txt"))
        self.assertFalse(rooted["audit_recorded"])

    def test_b_prohibit_encodings_and_controls(self):
        encoded = "%2e%2e/%2e%2e/canary.txt"
        result = write_file.write_file(self.scratch, encoded, SENTINEL)
        self._assert_rejected(result, "missing_parent")
        self._assert_canary()
        self._assert_absent(self._path("%2e%2e"))
        literal = write_file.write_file(self.scratch, "%2e%2e", "literal")
        self.assertTrue(literal["ok"])
        data, _st = self._assert_created("%2e%2e", "literal")
        self.assertEqual(data, b"literal")
        self._assert_canary()
        controls = {
            "a\\b.txt": "path_backslash",
            "a\nb.txt": "path_control_char",
            "a\x00b.txt": "path_nul",
            "a\x7fb.txt": "path_control_char",
        }
        for relative, reason in controls.items():
            with self.subTest(reason=reason):
                rejected = write_file.write_file(self.scratch, relative, SENTINEL)
                self._assert_rejected(rejected, reason)
        long_component = "c" * (confine.MAX_COMPONENT_BYTES + 1)
        rejected = write_file.write_file(self.scratch, long_component, "x")
        self._assert_rejected(rejected, "path_component_too_long")
        self._assert_absent(self._path(long_component))
        deep = "/".join(["d"] * (confine.MAX_DEPTH + 1))
        rejected = write_file.write_file(self.scratch, deep, "x")
        self._assert_rejected(rejected, "path_too_long")
        huge = "e" * (confine.MAX_PATH_CHARS + 1)
        rejected = write_file.write_file(self.scratch, huge, "x")
        self._assert_rejected(rejected, "path_too_long")
        self.assertIsNone(rejected["path"])

    def test_b_prohibit_reserved_names(self):
        first = write_file.write_file(self.scratch, "ok.txt", "fine")
        self.assertTrue(first["ok"])
        audit_before = _audit_bytes(self.scratch)
        reserved = write_file.write_file(self.scratch, confine.AUDIT_NAME, SENTINEL)
        self._assert_rejected(reserved, "path_reserved")
        temp_name = write_file.write_file(self.scratch, confine.TEMP_PREFIX + "manual", SENTINEL)
        self._assert_rejected(temp_name, "path_reserved_temp")
        os.mkdir(self._path("sub"))
        nested = write_file.write_file(self.scratch, "sub/" + confine.AUDIT_NAME, SENTINEL)
        self._assert_rejected(nested, "path_reserved")
        data, _st = self._assert_created("ok.txt", "fine")
        self.assertEqual(data, b"fine")
        raw = _audit_bytes(self.scratch)
        self.assertNotIn(SENTINEL.encode("utf-8"), raw)
        self.assertTrue(raw.startswith(audit_before))
        self.assertGreater(len(raw), len(audit_before))
        self._assert_absent(self._path(confine.TEMP_PREFIX + "manual"))

    def test_b_prohibit_missing_parent_not_created(self):
        result = write_file.write_file(self.scratch, "missing/file.txt", "x")
        self._assert_rejected(result, "missing_parent")
        self._assert_absent(self._path("missing"))
        self._assert_absent(self._path("file.txt"))

    def test_b_prohibit_fd_escape(self):
        fd = os.open(self.parent_path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            with self.assertRaises(confine.ConfineError) as caught:
                confine.assert_fd_inside(fd, os.path.realpath(self.scratch))
            self.assertEqual(caught.exception.reason, "escape")
        finally:
            os.close(fd)

    def test_b_prohibit_broad_tmp_and_desktop(self):
        self._assert_absent("/private/tmp/" + PROBE)
        try:
            opened = confine.open_root("/tmp")
        except confine.ConfineError as exc:
            self.assertEqual(exc.reason, "root_symlink")
        else:
            opened.close()
            self.fail("open_root accepted /tmp")
        result = write_file.write_file("/tmp", PROBE, SENTINEL)
        self._assert_rejected(result, "root_symlink")
        self._assert_absent("/private/tmp/" + PROBE)
        desktop = "/Users/richietate/Desktop"
        self._assert_absent(os.path.join(desktop, PROBE))
        try:
            opened = confine.open_root(desktop)
        except confine.ConfineError as exc:
            self.assertEqual(exc.reason, "root_protected")
        else:
            opened.close()
            self.fail("open_root accepted Desktop")
        result = write_file.write_file(desktop, PROBE, SENTINEL)
        self._assert_rejected(result, "root_protected")
        probe = os.path.join(desktop, PROBE)
        if os.path.lexists(probe):
            if os.path.isfile(probe) and not os.path.islink(probe):
                os.unlink(probe)
            self.fail("probe created on Desktop")

    def test_b_prohibit_relative_root_not_cwd(self):
        leak = os.path.join(TOOL_DIR, PROBE)
        self._assert_absent(leak)
        result = write_file.write_file("not-absolute", PROBE, SENTINEL)
        self._assert_rejected(result, "root_not_absolute")
        self.assertFalse(result["audit_recorded"])
        if os.path.lexists(leak):
            if os.path.isfile(leak) and not os.path.islink(leak):
                os.unlink(leak)
            self.fail("relative root wrote into the tool directory")

    def test_b_prohibit_root_symlink(self):
        link = os.path.join(self.parent_path, "rootlink")
        os.symlink(self.scratch, link)
        result = write_file.write_file(link, "a.txt", SENTINEL)
        self._assert_rejected(result, "root_symlink")
        self._assert_absent(self._path("a.txt"))
        self.assertFalse(result["audit_recorded"])

    def test_b_prohibit_nul_root(self):
        result = write_file.write_file(self.scratch + "\x00evil", "a.txt", SENTINEL)
        self._assert_rejected(result, "root_nul")
        self._assert_absent(self._path("a.txt"))
        self.assertFalse(result["audit_recorded"])

    def test_b_prohibit_audit_symlink(self):
        outside = os.path.join(self.parent_path, "audit_outside.txt")
        fd = os.open(outside, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
        try:
            os.write(fd, b"OUTSIDE-AUDIT")
        finally:
            os.close(fd)
        before = os.lstat(outside)
        os.symlink(outside, self._path(confine.AUDIT_NAME))
        result = write_file.write_file(self.scratch, "created.txt", "body")
        data, after = _read_nofollow(outside)
        self.assertEqual(data, b"OUTSIDE-AUDIT")
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertTrue(os.path.islink(self._path(confine.AUDIT_NAME)))
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "audit_failed")
        created, _st = self._assert_created("created.txt", "body")
        self.assertEqual(created, b"body")

    def test_b_prohibit_audit_hardlink(self):
        outside = os.path.join(self.parent_path, "audit_hard.txt")
        fd = os.open(outside, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
        try:
            os.write(fd, b"OUTSIDE-AUDIT")
        finally:
            os.close(fd)
        os.link(outside, self._path(confine.AUDIT_NAME))
        before = os.lstat(outside)
        self.assertGreaterEqual(before.st_nlink, 2)
        result = write_file.write_file(self.scratch, "created.txt", "body")
        data, after = _read_nofollow(outside)
        self.assertEqual(data, b"OUTSIDE-AUDIT")
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "audit_failed")
        created, _st = self._assert_created("created.txt", "body")
        self.assertEqual(created, b"body")

    def test_b_prohibit_hardlink_destination(self):
        os.link(self.canary, self._path("linked.txt"))
        before = os.lstat(self.canary)
        result = write_file.write_file(self.scratch, "linked.txt", SENTINEL)
        self._assert_rejected(result, "destination_exists")
        self._assert_canary()
        after = os.lstat(self.canary)
        self.assertEqual(before.st_ino, after.st_ino)
        linked, _st = _read_nofollow(self._path("linked.txt"))
        self.assertEqual(linked, CANARY)

    def test_c_failure_interrupted_write(self):
        keeper = write_file.write_file(self.scratch, "keeper.txt", "KEEP")
        self.assertTrue(keeper["ok"])

        def boom(fd, data):
            os.write(fd, b"PARTIAL")
            raise OSError(errno.EIO, "interrupted")

        original = write_file._write_all
        self.addCleanup(setattr, write_file, "_write_all", original)
        write_file._write_all = boom
        result = write_file.write_file(self.scratch, "gone.txt", "COMPLETE")
        write_file._write_all = original
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "write_failed")
        self._assert_absent(self._path("gone.txt"))
        self.assertEqual(_swtmp(self.scratch), [])
        self._assert_created("keeper.txt", "KEEP")
        raw = _audit_bytes(self.scratch)
        self.assertNotIn(b"PARTIAL", raw)
        self.assertNotIn(b"COMPLETE", raw)

    def test_c_failure_temp_open(self):
        real_open = os.open

        def guarded(path, flags, mode=0o777, *args, **kwargs):
            if isinstance(path, str) and path.startswith(confine.TEMP_PREFIX):
                raise OSError(errno.EIO, "simulated open failure")
            return real_open(path, flags, mode, *args, **kwargs)

        self.addCleanup(setattr, os, "open", real_open)
        os.open = guarded
        result = write_file.write_file(self.scratch, "nope.txt", "data")
        os.open = real_open
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "write_failed")
        self._assert_absent(self._path("nope.txt"))
        self.assertEqual(_swtmp(self.scratch), [])

    def test_c_failure_readonly_directory(self):
        sub = self._path("locked")
        os.mkdir(sub, 0o755)
        os.chmod(sub, 0o555)
        self.addCleanup(os.chmod, sub, 0o755)
        result = write_file.write_file(self.scratch, "locked/file.txt", "x")
        os.chmod(sub, 0o755)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "write_failed")
        self._assert_absent(os.path.join(sub, "file.txt"))
        self.assertEqual(os.listdir(sub), [])

    def test_c_failure_lied_readback(self):
        real_read = confine.read_regular

        def lie(dir_fd, name, root_real, repair_mode=False):
            data = real_read(dir_fd, name, root_real, repair_mode=False)
            return data + b"-LIE"

        self.addCleanup(setattr, confine, "read_regular", real_read)
        confine.read_regular = lie
        result = write_file.write_file(self.scratch, "lied.txt", "requested-body")
        confine.read_regular = real_read
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "verification_failed")
        self.assertEqual(result["verification"], "mismatch")
        data, _st = self._assert_created("lied.txt", "requested-body")
        self.assertEqual(data, b"requested-body")
        self.assertNotEqual(result["sha256"], hashlib.sha256(data).hexdigest())

    def test_c_failure_temp_cleanup(self):
        def no_unlink(dir_fd, name):
            raise OSError(errno.EPERM, "leave temp")

        original = write_file._unlink_temp
        self.addCleanup(setattr, write_file, "_unlink_temp", original)
        write_file._unlink_temp = no_unlink
        result = write_file.write_file(self.scratch, "kept.txt", "body")
        write_file._unlink_temp = original
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "temp_cleanup_failed")
        self.assertEqual(result["verification"], "match")
        self.assertTrue(result["audit_recorded"])
        data, dest = _read_nofollow(self._path("kept.txt"))
        self.assertEqual(data, b"body")
        self.assertTrue(stat.S_ISREG(dest.st_mode))
        self.assertFalse(stat.S_ISLNK(dest.st_mode))
        self.assertEqual(stat.S_IMODE(dest.st_mode), 0o644)
        temps = _swtmp(self.scratch)
        self.assertEqual(len(temps), 1)
        temp_st = os.lstat(temps[0])
        self.assertEqual(temp_st.st_ino, dest.st_ino)
        self.assertGreaterEqual(dest.st_nlink, 2)

    def test_c_failure_audit_append(self):
        def boom(root_fd, record):
            raise OSError(errno.EIO, "audit down")

        original = confine.append_audit
        self.addCleanup(setattr, confine, "append_audit", original)
        confine.append_audit = boom
        result = write_file.write_file(self.scratch, "audited.txt", "body")
        confine.append_audit = original
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "audit_failed")
        self.assertEqual(result["verification"], "match")
        self.assertFalse(result["audit_recorded"])
        data, _st = self._assert_created("audited.txt", "body")
        self.assertEqual(data, b"body")

    def test_c_failure_verify_mismatch_and_truncation(self):
        result = write_file.write_file(self.scratch, "check.txt", "hello world")
        self.assertTrue(result["ok"])
        path = self._path("check.txt")
        fd = os.open(path, os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            os.ftruncate(fd, 0)
            os.write(fd, b"hello")
        finally:
            os.close(fd)
        before = os.lstat(path)
        checked = verify_file.verify_file(self.scratch, "check.txt", "hello world")
        after = os.lstat(path)
        self.assertFalse(checked["ok"])
        self.assertEqual(checked["status"], "verification_failed")
        self.assertEqual(checked["verification"], "mismatch")
        self.assertEqual(checked["reason"], "verification_mismatch")
        data, _st = _read_nofollow(path)
        self.assertEqual(data, b"hello")
        self.assertEqual(checked["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(checked["size"], 5)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertEqual(before.st_ino, after.st_ino)

    def test_c_failure_verify_missing(self):
        result = verify_file.verify_file(self.scratch, "missing.txt", "x")
        self._assert_rejected(result, "missing")
        self.assertEqual(result["verification"], "missing")
        self.assertEqual(result["status"], "verification_failed")
        self._assert_absent(self._path("missing.txt"))

    def test_c_failure_verify_symlink_even_if_content_matches(self):
        os.symlink(self.canary, self._path("link"))
        before = os.lstat(self.canary)
        result = verify_file.verify_file(self.scratch, "link", CANARY.decode("ascii"))
        after = os.lstat(self.canary)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "symlink_destination")
        self.assertEqual(result["verification"], "unreadable")
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self._assert_canary()
        self.assertTrue(os.path.islink(self._path("link")))

    def test_c_failure_concurrent(self):
        results = []
        errors = []

        def run(text):
            try:
                results.append(write_file.write_file(self.scratch, "race.txt", text))
            except Exception as exc:
                errors.append(repr(exc))

        first = threading.Thread(target=run, args=("AAAA",))
        second = threading.Thread(target=run, args=("BBBB",))
        first.start()
        second.start()
        first.join()
        second.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        wins = [item for item in results if item["ok"]]
        self.assertEqual(len(wins), 1)
        data, st = _read_nofollow(self._path("race.txt"))
        self.assertIn(data, (b"AAAA", b"BBBB"))
        self.assertNotIn(b"AAAABBBB", data)
        self.assertNotIn(b"BBBBAAAA", data)
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o644)

    def _guard_then_write(self, path, reasons):
        is_dir = os.path.isdir(path) and not os.path.islink(path)
        probe = os.path.join(path, PROBE) if is_dir else None
        if probe is not None and os.path.lexists(probe):
            self.fail("probe already exists: " + probe)
        try:
            opened = confine.open_root(path)
        except confine.ConfineError as exc:
            self.assertIn(exc.reason, reasons)
        else:
            opened.close()
            self.fail("open_root accepted " + path)
        result = write_file.write_file(path, PROBE, SENTINEL)
        self.assertFalse(result["ok"])
        self.assertFalse(result["accepted"])
        self.assertIn(result["reason"], reasons)
        self.assertNotIn(SENTINEL, json.dumps(result))
        if probe is not None and os.path.lexists(probe):
            if os.path.isfile(probe) and not os.path.islink(probe):
                os.unlink(probe)
            self.fail("probe created: " + probe)
        return result

    def test_d_boundary_protected_directories(self):
        directories = (
            PROD,
            os.path.join(PROD, "memory"),
            os.path.join(PROD, "app"),
            os.path.join(PROD, "app", "core"),
            VOY,
            VOY_LAB,
            os.path.join(VOY_LAB, "voyager"),
            os.path.join(VOY_LAB, "results"),
        )
        for path in directories:
            with self.subTest(path=path):
                before = os.lstat(path)
                self._guard_then_write(path, ("root_protected",))
                after = os.lstat(path)
                self.assertEqual(before.st_ino, after.st_ino)
                if path not in LIVE_DIRS:
                    self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
                    self.assertEqual(before.st_size, after.st_size)
                self._assert_absent(os.path.join(path, PROBE))
                self._assert_absent(os.path.join(path, confine.AUDIT_NAME))

    def test_d_boundary_protected_files(self):
        for path in FROZEN_FILES:
            with self.subTest(path=path):
                before = _file_id(path)
                result = self._guard_then_write(path, ("root_not_directory", "root_protected"))
                self.assertEqual(result["reason"], "root_not_directory")
                after = _file_id(path)
                self.assertEqual(before, after)

    def test_d_boundary_faiss(self):
        before = _faiss_id()
        try:
            opened = confine.open_root(FAISS)
        except confine.ConfineError as exc:
            self.assertEqual(exc.reason, "root_not_directory")
        else:
            opened.close()
            self.fail("open_root accepted faiss")
        result = write_file.write_file(FAISS, PROBE, SENTINEL)
        after = _faiss_id()
        self._assert_rejected(result, "root_not_directory")
        self.assertEqual(before, after)
        memory = os.path.join(PROD, "memory")
        self._assert_absent(os.path.join(memory, PROBE))
        self._assert_absent(os.path.join(memory, confine.AUDIT_NAME))

    def test_d_boundary_outside_repository(self):
        outside = os.path.join(self.parent_path, "outside.txt")
        fd = os.open(outside, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o644)
        try:
            os.write(fd, b"OUTSIDE")
        finally:
            os.close(fd)
        before = os.lstat(outside)
        absolute = write_file.write_file(self.scratch, outside, SENTINEL)
        self._assert_rejected(absolute, "path_absolute")
        escaped = write_file.write_file(self.scratch, "../outside.txt", SENTINEL)
        self._assert_rejected(escaped, "path_dot_segment")
        as_root = write_file.write_file(outside, PROBE, SENTINEL)
        self._assert_rejected(as_root, "root_not_directory")
        data, after = _read_nofollow(outside)
        self.assertEqual(data, b"OUTSIDE")
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertFalse(confine.is_within(outside, PROD))
        self.assertFalse(confine.is_within(outside, VOY))


if __name__ == "__main__":
    unittest.main()
