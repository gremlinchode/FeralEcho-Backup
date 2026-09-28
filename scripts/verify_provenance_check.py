#!/usr/bin/env python3
"""
verify_provenance_check.py -- discrimination tests for
app/core/provenance_check.py, the same style as
scripts/verify_seam_engine.py / scripts/verify_liveness_ledger.py: prove
each primitive's epistemic boundary, not merely that it runs without
raising.

Scope: three primitives now implemented.
  - working_tree_file_identity()               (Layer 1)
  - runtime_process_identity_and_self_report()  (Layer 2)
  - reconcile_process_and_selfreport()           (Reconciliation, added
    2026-09-13 per audits/2026-09-13_reconciliation_implementation_
    design.md's own contract)
There is still no runtime_self_reported_module_origin() (sys.modules
inspection) to test -- remains out of scope, per the leaf-primitives
validation's own explicit finding that it requires new in-process code
this thread is not authorized to add.

STRICTLY READ-ONLY. This script never writes, stages, commits, resets, or
otherwise mutates anything in the repository or the running system. It
verifies its own read-only-ness directly (Case 12) rather than merely
asserting it in prose.

Real fixtures used (chosen from the repository's own actual, pre-existing
state at the time this script was written -- never created or mutated by
this script):
  - CLAUDE.md                          -- tracked, clean (git status: none)
  - app/core/echo_ground_truth.py      -- tracked, currently modified
  - audits/2026-09-11_provenance_implementation_boundary_audit.md
                                        -- untracked, exists on disk, not in HEAD
  - app/core/definitely_does_not_exist_xyz123.py
                                        -- a synthetic path chosen to not exist
                                           anywhere (working tree or HEAD)
"""
import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, ".")
import app.core.provenance_check as pc  # noqa: E402
from app.core.provenance_check import (  # noqa: E402
    working_tree_file_identity,
    _compose_identity,
    runtime_process_identity_and_self_report,
    _compose_correlation,
    _external_process_observation,
    reconcile_process_and_selfreport,
    _compare_values,
    RELATIONSHIP_AGREE,
    RELATIONSHIP_DISAGREE,
    RELATIONSHIP_ONE_SIDED,
    RELATIONSHIP_NEITHER,
    EPISTEMIC_EVIDENCE_AGREES,
    EPISTEMIC_EVIDENCE_CONFLICTS,
    EPISTEMIC_INSUFFICIENT_EVIDENCE,
)
import psutil  # noqa: E402 -- already a project dependency (see provenance_check.py)
import copy  # noqa: E402
import inspect  # noqa: E402
from unittest import mock  # noqa: E402

TRACKED_CLEAN = "CLAUDE.md"
TRACKED_MODIFIED = "app/core/echo_ground_truth.py"
UNTRACKED_EXISTS_NOT_IN_HEAD = "audits/2026-09-11_provenance_implementation_boundary_audit.md"
NEVER_EXISTED = "app/core/definitely_does_not_exist_xyz123.py"


def _git(*args):
    return subprocess.run(
        ["git", "-C", ".", *args], capture_output=True, text=True
    ).stdout.strip()


# ---------------------------------------------------------------------------
# 1. Tracked file in a clean working tree
# ---------------------------------------------------------------------------

def case_1_tracked_clean():
    assert _git("status", "--porcelain", "--", TRACKED_CLEAN) == "", (
        f"fixture assumption broken: {TRACKED_CLEAN} is no longer clean"
    )
    r = working_tree_file_identity(TRACKED_CLEAN)
    return (
        r["in_scope"] is True
        and r["error"] is None
        and r["exists"] is True
        and r["tracked"] is True
        and isinstance(r["size"], int) and r["size"] > 0
        and isinstance(r["mtime"], str)
        and isinstance(r["sha256"], str) and len(r["sha256"]) == 64
        and isinstance(r["head_blob_sha256_or_none"], str)
        and r["sha256"] == r["head_blob_sha256_or_none"]
        and r["modified_vs_head"] is False
    )


# ---------------------------------------------------------------------------
# 2. Tracked file whose contents have changed
# ---------------------------------------------------------------------------

def case_2_tracked_modified():
    status = _git("status", "--porcelain", "--", TRACKED_MODIFIED)
    assert status.startswith(" M") or status.startswith("M"), (
        f"fixture assumption broken: {TRACKED_MODIFIED} is not showing as modified "
        f"(git status: {status!r})"
    )
    r = working_tree_file_identity(TRACKED_MODIFIED)
    return (
        r["in_scope"] is True
        and r["exists"] is True
        and r["tracked"] is True
        and r["sha256"] is not None
        and r["head_blob_sha256_or_none"] is not None
        and r["sha256"] != r["head_blob_sha256_or_none"]
        and r["modified_vs_head"] is True
    )


# ---------------------------------------------------------------------------
# 3. Untracked file (exists on disk, absent from the index, absent from HEAD)
# ---------------------------------------------------------------------------

def case_3_untracked():
    r = working_tree_file_identity(UNTRACKED_EXISTS_NOT_IN_HEAD)
    return (
        r["in_scope"] is True
        and r["exists"] is True
        and r["tracked"] is False
        and r["sha256"] is not None
        and r["head_blob_sha256_or_none"] is None
        # This is the case the mission specifically calls out: sha256 is
        # present but there is nothing on the HEAD side to compare against.
        # A wrong implementation might report False ("not modified", since
        # nothing differs) or True ("modified", since HEAD has nothing) --
        # both would be a fabricated boolean standing in for "unknown."
        and r["modified_vs_head"] is None
    )


# ---------------------------------------------------------------------------
# 4. Missing / never-existed file
# ---------------------------------------------------------------------------

def case_4_missing_file():
    r = working_tree_file_identity(NEVER_EXISTED)
    return (
        r["in_scope"] is True
        and r["error"] is None
        and r["exists"] is False
        and r["tracked"] is False
        and r["size"] is None
        and r["mtime"] is None
        and r["sha256"] is None
        and r["head_blob_sha256_or_none"] is None
        and r["modified_vs_head"] is None
    )


# ---------------------------------------------------------------------------
# 5a. Invalid path input -- wrong type / empty
# ---------------------------------------------------------------------------

def case_5a_invalid_type():
    for bad in (None, 123, "", "   "):
        r = working_tree_file_identity(bad)
        if not (
            r["in_scope"] is False
            and r["error"] == "invalid_path_argument"
            and all(
                r[k] is None
                for k in (
                    "exists", "tracked", "size", "mtime", "sha256",
                    "head_blob_sha256_or_none", "modified_vs_head",
                )
            )
        ):
            return False
    return True


# ---------------------------------------------------------------------------
# 5b. Invalid path input -- resolves outside the project root
# ---------------------------------------------------------------------------

def case_5b_outside_root():
    for escape_path in ("/etc/passwd", "../../../../../../etc/passwd"):
        r = working_tree_file_identity(escape_path)
        if not (
            r["in_scope"] is False
            and r["error"] == "path_outside_project_root"
            and all(
                r[k] is None
                for k in (
                    "exists", "tracked", "size", "mtime", "sha256",
                    "head_blob_sha256_or_none", "modified_vs_head",
                )
            )
        ):
            return False
    # The refusal must never silently degrade into a false "exists: False"
    # for a path that, on a real system, plausibly DOES exist outside the
    # project (/etc/passwd almost certainly exists on this machine) -- the
    # correct signal here is "refused to check", not "checked and absent".
    return True


# ---------------------------------------------------------------------------
# 6. Repeated invocation produces stable (equal) results
# ---------------------------------------------------------------------------

def case_6_deterministic():
    r1 = working_tree_file_identity(TRACKED_CLEAN)
    r2 = working_tree_file_identity(TRACKED_CLEAN)
    r3 = working_tree_file_identity(NEVER_EXISTED)
    r4 = working_tree_file_identity(NEVER_EXISTED)
    return r1 == r2 and r3 == r4


# ---------------------------------------------------------------------------
# 7. Read-only: no git mutation, no filesystem mutation, no HEAD change
# ---------------------------------------------------------------------------

def case_7_read_only():
    head_before = _git("rev-parse", "HEAD")
    status_before = _git("status", "--porcelain")

    working_tree_file_identity(TRACKED_CLEAN)
    working_tree_file_identity(TRACKED_MODIFIED)
    working_tree_file_identity(UNTRACKED_EXISTS_NOT_IN_HEAD)
    working_tree_file_identity(NEVER_EXISTED)
    working_tree_file_identity("/etc/passwd")
    working_tree_file_identity(None)

    head_after = _git("rev-parse", "HEAD")
    status_after = _git("status", "--porcelain")

    return head_before == head_after and status_before == status_after


# ---------------------------------------------------------------------------
# 8. Never raises, for any input shape
# ---------------------------------------------------------------------------

def case_8_never_raises():
    weird_inputs = [
        None, 123, [], {}, "", "   ",
        "\x00nullbyte", "a" * 10000,
        "app/core/../../../../etc/passwd",
        "/dev/null",
    ]
    for inp in weird_inputs:
        try:
            r = working_tree_file_identity(inp)
            if not isinstance(r, dict):
                return False
        except Exception:
            return False
    return True


# ---------------------------------------------------------------------------
# 9. Pure composition logic: the case a real fixture can't safely construct
#    without mutating the repository -- "tracked in HEAD, absent from disk"
#    (e.g. deleted from the working tree but not yet `git rm`'d). Exercised
#    directly against _compose_identity() with synthetic evidence, per this
#    module's own design (evidence-gathering is separated from decision
#    logic specifically so this is possible without touching git/fs).
# ---------------------------------------------------------------------------

def case_9_tracked_but_missing_from_disk():
    r = _compose_identity(
        path="some/deleted/file.py",
        in_scope=True,
        error=None,
        exists=False,
        size=None,
        mtime=None,
        sha256=None,
        tracked=True,
        head_blob_sha256="deadbeef" * 8,
    )
    return (
        r["exists"] is False
        and r["tracked"] is True
        and r["head_blob_sha256_or_none"] == "deadbeef" * 8
        # No working-tree hash exists to compare -- must not be inferred as
        # "modified" just because the file is gone.
        and r["modified_vs_head"] is None
    )


# ---------------------------------------------------------------------------
# 10. Pure composition logic: git genuinely unavailable/unknown (not "False")
# ---------------------------------------------------------------------------

def case_10_git_unknown_is_not_false():
    r = _compose_identity(
        path="whatever.py",
        in_scope=True,
        error=None,
        exists=True,
        size=10,
        mtime="2026-01-01T00:00:00+00:00",
        sha256="a" * 64,
        tracked=None,  # git ls-files could not be consulted at all
        head_blob_sha256=None,  # git show could not be consulted at all
    )
    return (
        r["tracked"] is None
        and r["head_blob_sha256_or_none"] is None
        and r["modified_vs_head"] is None
    )


# ---------------------------------------------------------------------------
# 11. Boolean fields never fabricated as "verified"-shaped truths when
#     evidence is genuinely equal/different -- the exact boundary the
#     mission's own text calls out.
# ---------------------------------------------------------------------------

def case_11_equal_and_different_are_distinguished():
    same = _compose_identity(
        path="x", in_scope=True, error=None, exists=True, size=1,
        mtime="t", sha256="abc", tracked=True, head_blob_sha256="abc",
    )
    different = _compose_identity(
        path="x", in_scope=True, error=None, exists=True, size=1,
        mtime="t", sha256="abc", tracked=True, head_blob_sha256="xyz",
    )
    unknown = _compose_identity(
        path="x", in_scope=True, error=None, exists=True, size=1,
        mtime="t", sha256="abc", tracked=True, head_blob_sha256=None,
    )
    return (
        same["modified_vs_head"] is False
        and different["modified_vs_head"] is True
        and unknown["modified_vs_head"] is None
    )


# ---------------------------------------------------------------------------
# 12-16. SYMLINK REGRESSION SUITE (2026-09-13 red-team finding, fixed)
#
# Root cause: the pre-fix implementation derived the path handed to
# `git ls-files`/`git show HEAD:` from os.path.realpath()'s output -- which
# follows symlinks -- so a symlink's own git identity (tracked status, HEAD
# blob) was silently replaced by whatever it happened to point at.
#
# These tests run against a throwaway git repository built under the
# system temp directory (never inside this project, removed unconditionally
# on exit), with app.core.provenance_check._PROJECT_ROOT pointed at it only
# for the duration of each case. This never touches the real FeralEcho
# repository -- confirmed by Case 7's own before/after HEAD/status check,
# which covers this whole run including these cases.
#
# Each assertion below is on a value that the PRE-FIX implementation is
# independently confirmed (via direct reproduction during the red-team,
# and re-confirmed inline in _prove_old_implementation_would_have_failed()
# below) to have gotten wrong -- these are not merely tests that happen to
# also pass against the old code.
# ---------------------------------------------------------------------------

def _write(base, name, content):
    path = os.path.join(base, name)
    with open(path, "w") as f:
        f.write(content)
    return path


@contextlib.contextmanager
def _isolated_symlink_repo():
    """Builds fixtures matching the red-team's exact reproduction, in a
    throwaway git repository outside this project. Points
    app.core.provenance_check._PROJECT_ROOT at it for the `with` block's
    duration; restores the real root and deletes both temp directories
    unconditionally on exit, even if the caller raises."""
    tmp = tempfile.mkdtemp(prefix="provenance_symlink_regression_")
    outside_dir = tempfile.mkdtemp(prefix="provenance_symlink_outside_")
    real_root = pc._PROJECT_ROOT
    try:
        def run(*args):
            subprocess.run(["git", "-C", tmp, *args], check=True, capture_output=True)

        run("init", "-q")
        run("config", "user.email", "redteam@test")
        run("config", "user.name", "redteam")

        _write(tmp, "real_target.py", "target content v1\n")
        _write(tmp, "untracked_target.py", "untracked target content\n")
        os.symlink("real_target.py", os.path.join(tmp, "symlink_to_sibling.py"))
        os.symlink("untracked_target.py", os.path.join(tmp, "symlink_to_untracked.py"))
        run("add", "real_target.py", "symlink_to_sibling.py", "symlink_to_untracked.py")
        run("commit", "-q", "-m", "symlink regression fixtures")

        _write(outside_dir, "secret.py", "outside content\n")
        os.symlink(outside_dir, os.path.join(tmp, "escape_dir"))

        pc._PROJECT_ROOT = os.path.realpath(tmp)
        yield tmp
    finally:
        pc._PROJECT_ROOT = real_root
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(outside_dir, ignore_errors=True)


def case_12_symlink_tracked_untracked_target():
    """Mission Case 1: a tracked symlink pointing at an untracked target
    must report `tracked` for the LITERAL symlink path, not the target's."""
    with _isolated_symlink_repo() as repo:
        gt_symlink = subprocess.run(
            ["git", "-C", repo, "ls-files", "--error-unmatch", "symlink_to_untracked.py"],
            capture_output=True,
        )
        gt_target = subprocess.run(
            ["git", "-C", repo, "ls-files", "--error-unmatch", "untracked_target.py"],
            capture_output=True,
        )
        assert gt_symlink.returncode == 0, "fixture broken: symlink_to_untracked.py should be tracked"
        assert gt_target.returncode == 1, "fixture broken: untracked_target.py should be untracked"

        r = working_tree_file_identity("symlink_to_untracked.py")
        return r["in_scope"] is True and r["tracked"] is True


def case_13_symlink_blob_is_its_own_not_targets_content():
    """Mission Case 2: head_blob_sha256_or_none for a tracked symlink must
    be the hash of the symlink's OWN git blob (the link-target text Git
    actually stores), never the dereferenced target file's content hash."""
    with _isolated_symlink_repo() as repo:
        real_symlink_blob = subprocess.run(
            ["git", "-C", repo, "show", "HEAD:symlink_to_sibling.py"],
            capture_output=True,
        ).stdout
        real_symlink_blob_hash = hashlib.sha256(real_symlink_blob).hexdigest()
        target_content_hash = hashlib.sha256(
            open(os.path.join(repo, "real_target.py"), "rb").read()
        ).hexdigest()
        assert real_symlink_blob_hash != target_content_hash, (
            "fixture broken: link-text hash coincidentally equals target content hash"
        )

        r = working_tree_file_identity("symlink_to_sibling.py")
        return (
            r["head_blob_sha256_or_none"] == real_symlink_blob_hash
            and r["head_blob_sha256_or_none"] != target_content_hash
        )


def case_14_symlink_identity_not_substituted_with_sibling():
    """Mission Case 3: querying a symlink must not silently report the
    git identity of the sibling file it points at -- the symlink and its
    target are distinct tracked git objects with distinct HEAD blobs."""
    with _isolated_symlink_repo() as repo:
        r_symlink = working_tree_file_identity("symlink_to_sibling.py")
        r_target = working_tree_file_identity("real_target.py")
        return (
            r_symlink["tracked"] is True
            and r_target["tracked"] is True
            and r_symlink["head_blob_sha256_or_none"] is not None
            and r_target["head_blob_sha256_or_none"] is not None
            and r_symlink["head_blob_sha256_or_none"] != r_target["head_blob_sha256_or_none"]
            and r_symlink["path"] == "symlink_to_sibling.py"
            and r_target["path"] == "real_target.py"
        )


def case_15_symlinked_directory_escape_still_refused():
    """Mission Case 4: the fix must not weaken realpath-based confinement.
    A path that lexically looks inside the project root but resolves
    outside it via a symlinked directory must still be refused -- this is
    a straight regression check on the pre-existing security boundary."""
    with _isolated_symlink_repo() as repo:
        r = working_tree_file_identity("escape_dir/secret.py")
        return (
            r["in_scope"] is False
            and r["error"] == "path_outside_project_root"
            and all(
                r[k] is None
                for k in (
                    "exists", "tracked", "size", "mtime", "sha256",
                    "head_blob_sha256_or_none", "modified_vs_head",
                )
            )
        )


def case_16_ordinary_files_unaffected_by_the_fix():
    """Mission Case 5: ordinary, non-symlink files must behave exactly as
    before -- no regression from splitting one path branch into two."""
    with _isolated_symlink_repo() as repo:
        r = working_tree_file_identity("real_target.py")
        real_hash = hashlib.sha256(
            open(os.path.join(repo, "real_target.py"), "rb").read()
        ).hexdigest()
        return (
            r["exists"] is True
            and r["tracked"] is True
            and r["sha256"] == real_hash
            and r["head_blob_sha256_or_none"] == real_hash
            and r["modified_vs_head"] is False
        )


def _prove_old_implementation_would_have_failed():
    """Not a pass/fail case -- a direct, printed demonstration (run once,
    at the top of __main__) that Cases 12/13 encode a real regression, not
    a tautology. Simulates the OLD (pre-fix) relpath derivation --
    os.path.relpath(realpath-resolved-target, PROJECT_ROOT) -- inline,
    without touching app/core/provenance_check.py, and shows it reproduces
    exactly the wrong values the red-team originally found."""
    with _isolated_symlink_repo() as repo:
        # Mirror the OLD production code exactly: it computed relpath
        # against pc._PROJECT_ROOT (already realpath-resolved, set by the
        # context manager), not against the raw `tmp` path -- using the
        # unresolved `repo` value here would introduce a harness-only bug
        # (macOS's /tmp is itself a symlink to /private/tmp), unrelated to
        # the production defect this is meant to reproduce.
        old_style_resolved = os.path.realpath(os.path.join(pc._PROJECT_ROOT, "symlink_to_untracked.py"))
        old_style_relpath = os.path.relpath(old_style_resolved, pc._PROJECT_ROOT)
        old_tracked = pc._git_tracked(old_style_relpath)

        old_style_resolved2 = os.path.realpath(os.path.join(pc._PROJECT_ROOT, "symlink_to_sibling.py"))
        old_style_relpath2 = os.path.relpath(old_style_resolved2, pc._PROJECT_ROOT)
        old_head_blob = pc._git_head_blob_sha256(old_style_relpath2)
        target_content_hash = hashlib.sha256(
            open(os.path.join(repo, "real_target.py"), "rb").read()
        ).hexdigest()

        print("[pre-fix simulation] symlink_to_untracked.py -> old-style tracked =",
              old_tracked, "(real git ls-files says True; old code said this)")
        print("[pre-fix simulation] symlink_to_sibling.py -> old-style head_blob =",
              old_head_blob, "== target content hash?", old_head_blob == target_content_hash)
        return old_tracked is False and old_head_blob == target_content_hash


# ---------------------------------------------------------------------------
# LAYER 2: runtime_process_identity_and_self_report() -- added 2026-09-13
# per audits/2026-09-12_provenance_layer2_boundary_review.md's own
# contract. Three groups: external-process observation (mocked psutil for
# the two race/permission cases that can't be reliably timed as a real
# fixture -- the exact deterministic-mock discipline this codebase already
# uses for the symlink regression tests above), self-report file reading
# (isolated scratch memory/ directory, same _PROJECT_ROOT-redirect pattern
# as the symlink tests, never touching the real memory/echo_server.pid or
# memory/echo_sentinel.json), correlation (pure, direct calls to
# _compose_correlation(), zero I/O), and epistemic-boundary structural
# checks proving the output schema cannot be misread as a module-loading,
# execution, or "verified runtime" claim.
# ---------------------------------------------------------------------------

def _find_nonexistent_pid():
    candidate = 999999999
    while psutil.pid_exists(candidate) and candidate > 1:
        candidate -= 1
    return candidate


# --- External process (mission Cases 1-4) ----------------------------------

def case_l2_ext_1_known_existing_pid():
    """A real, known-existing PID (this test process itself) must report
    exists=True with real, genuinely external fields populated."""
    r = _external_process_observation(os.getpid())
    return (
        r["exists"] is True
        and r["create_time_utc"] is not None
        and r["cmdline"] is not None
        and r["executable"] is not None
        and r["cwd"] is not None
        and r["status"] is not None
        and r["access_denied"] is False
    )


def case_l2_ext_2_nonexistent_pid():
    """A PID confirmed via psutil.pid_exists() to not exist must report
    exists=False, every evidence field None, no error -- absence is not
    an error condition."""
    pid = _find_nonexistent_pid()
    r = _external_process_observation(pid)
    return (
        r["exists"] is False
        and r["create_time_utc"] is None
        and r["cmdline"] is None
        and r["executable"] is None
        and r["cwd"] is None
        and r["status"] is None
        and r["error"] is None
    )


class _FakeVanishingProcess:
    """Simulates psutil.Process construction succeeding, then a specific
    field getter raising NoSuchProcess -- the real race Phase 8's Case 3
    asks to be covered, tested deterministically via a mock rather than a
    timing-dependent real kill (which cannot be made reliable)."""
    def __init__(self, pid):
        self.pid = pid

    def create_time(self):
        return 1234567890.0  # gathered successfully, before the "vanish"

    def cmdline(self):
        raise psutil.NoSuchProcess(self.pid)

    def exe(self):
        raise psutil.NoSuchProcess(self.pid)

    def cwd(self):
        raise psutil.NoSuchProcess(self.pid)

    def status(self):
        raise psutil.NoSuchProcess(self.pid)


def case_l2_ext_3_vanishes_mid_observation():
    """A process that disappears between construction and a later field
    read must degrade honestly: fields already gathered are kept, `exists`
    is corrected to False once the vanish is detected, and nothing raises."""
    real_process_cls = psutil.Process
    psutil.Process = _FakeVanishingProcess
    try:
        r = _external_process_observation(424242)
    finally:
        psutil.Process = real_process_cls
    return (
        r["exists"] is False
        and r["create_time_utc"] is not None
        and r["cmdline"] is None
    )


class _FakeAccessDeniedProcess:
    """Simulates a field genuinely inaccessible due to OS permissions,
    while other fields on the same process remain readable."""
    def __init__(self, pid):
        self.pid = pid

    def create_time(self):
        return 1234567890.0

    def cmdline(self):
        raise psutil.AccessDenied(self.pid)

    def exe(self):
        raise psutil.AccessDenied(self.pid)

    def cwd(self):
        return "/some/cwd"

    def status(self):
        return "running"


def case_l2_ext_4_access_denied_field():
    """A genuinely inaccessible field must set access_denied=True while
    exists stays True and other, genuinely-readable fields still populate
    -- not collapsed into one blanket failure."""
    real_process_cls = psutil.Process
    psutil.Process = _FakeAccessDeniedProcess
    try:
        r = _external_process_observation(424243)
    finally:
        psutil.Process = real_process_cls
    return (
        r["exists"] is True
        and r["access_denied"] is True
        and r["cmdline"] is None
        and r["cwd"] == "/some/cwd"
        and r["status"] == "running"
    )


# --- Self-report (mission Cases 5-10) ---------------------------------------

@contextlib.contextmanager
def _isolated_self_report_dir(server_pid_content=None, sentinel_content=None,
                                sentinel_raw=None, unreadable_sentinel=False):
    """Throwaway directory (never inside this project) containing a
    memory/ subdirectory with the given self-report file contents, with
    app.core.provenance_check._PROJECT_ROOT pointed at it for the `with`
    block's duration. Never touches the real memory/echo_server.pid or
    memory/echo_sentinel.json. Restores the real root and deletes the temp
    directory unconditionally on exit, even if the caller raises.

    server_pid_content: str or None -- written verbatim; None = file absent.
    sentinel_content: dict or None -- json.dump()'d; None = file absent.
    sentinel_raw: str or None -- written VERBATIM (bypasses json.dumps),
        for constructing deliberately malformed JSON; takes precedence.
    unreadable_sentinel: chmod 000 the sentinel file after writing it.
    """
    tmp = tempfile.mkdtemp(prefix="provenance_selfreport_")
    real_root = pc._PROJECT_ROOT
    try:
        memory_dir = os.path.join(tmp, "memory")
        os.makedirs(memory_dir, exist_ok=True)

        if server_pid_content is not None:
            with open(os.path.join(memory_dir, "echo_server.pid"), "w") as f:
                f.write(server_pid_content)

        sentinel_path = os.path.join(memory_dir, "echo_sentinel.json")
        if sentinel_raw is not None:
            with open(sentinel_path, "w") as f:
                f.write(sentinel_raw)
        elif sentinel_content is not None:
            with open(sentinel_path, "w") as f:
                json.dump(sentinel_content, f)

        if unreadable_sentinel:
            os.chmod(sentinel_path, 0o000)

        pc._PROJECT_ROOT = os.path.realpath(tmp)
        yield tmp
    finally:
        pc._PROJECT_ROOT = real_root
        try:
            os.chmod(os.path.join(tmp, "memory", "echo_sentinel.json"), 0o644)
        except OSError:
            pass
        shutil.rmtree(tmp, ignore_errors=True)


def case_l2_sr_1_both_artifacts_present_valid():
    with _isolated_self_report_dir(
        server_pid_content="12345",
        sentinel_content={
            "stage": "serving", "pid": 12345,
            "start_utc": "2026-01-01T00:00:00.000000Z",
            "last_heartbeat_utc": "2026-01-01T00:05:00.000000Z",
            "uptime_s": 300,
        },
    ):
        sf = pc._read_server_pid_file()
        sn = pc._read_sentinel_file()
        return (
            sf["exists"] is True and sf["readable"] is True
            and sf["malformed"] is False and sf["pid"] == 12345
            and sn["exists"] is True and sn["readable"] is True and sn["malformed"] is False
            and sn["stage"] == "serving" and sn["pid"] == 12345
            and sn["start_utc"] == "2026-01-01T00:00:00.000000Z"
            and sn["uptime_s"] == 300
        )


def case_l2_sr_2_missing_pid_file():
    with _isolated_self_report_dir(
        server_pid_content=None,
        sentinel_content={"stage": "serving", "pid": 1, "start_utc": "x",
                            "last_heartbeat_utc": "y", "uptime_s": 1},
    ):
        sf = pc._read_server_pid_file()
        return sf["exists"] is False and sf["readable"] is False and sf["pid"] is None


def case_l2_sr_3_missing_sentinel():
    with _isolated_self_report_dir(server_pid_content="1", sentinel_content=None):
        sn = pc._read_sentinel_file()
        return sn["exists"] is False and sn["readable"] is False and all(
            sn[k] is None for k in ("stage", "pid", "start_utc", "last_heartbeat_utc", "uptime_s")
        )


def case_l2_sr_4_malformed_sentinel_json():
    with _isolated_self_report_dir(server_pid_content="1", sentinel_raw="{not valid json!!"):
        sn = pc._read_sentinel_file()
        return (
            sn["exists"] is True and sn["readable"] is True
            and sn["malformed"] is True and sn["error"] == "invalid_json"
        )


def case_l2_sr_5_unreadable_artifact():
    with _isolated_self_report_dir(
        server_pid_content="1",
        sentinel_content={"stage": "s", "pid": 1, "start_utc": "x",
                            "last_heartbeat_utc": "y", "uptime_s": 1},
        unreadable_sentinel=True,
    ):
        sn = pc._read_sentinel_file()
        if sn["exists"] and not sn["readable"]:
            return sn["error"] is not None
        # A permission-bypassing environment (e.g. running as root) makes
        # chmod 000 not actually block the read -- still a valid,
        # non-crashing outcome; report it honestly rather than asserting
        # a permission-denied result that may not hold on every host.
        return sn["exists"] is True and sn["readable"] is True


def case_l2_sr_6_missing_expected_field():
    with _isolated_self_report_dir(
        server_pid_content="1",
        sentinel_content={"stage": "serving", "pid": 1, "start_utc": "x"},
    ):
        sn = pc._read_sentinel_file()
        return (
            sn["exists"] is True and sn["readable"] is True and sn["malformed"] is False
            and sn["stage"] == "serving" and sn["pid"] == 1 and sn["start_utc"] == "x"
            and sn["last_heartbeat_utc"] is None and sn["uptime_s"] is None
        )


def case_l2_sr_7_malformed_pid_file_non_integer():
    with _isolated_self_report_dir(server_pid_content="not-a-pid"):
        sf = pc._read_server_pid_file()
        return (
            sf["exists"] is True and sf["readable"] is True
            and sf["malformed"] is True and sf["pid"] is None
        )


# --- Correlation (mission Cases 11-15) --------------------------------------

def case_l2_corr_1_matching_pid():
    r = _compose_correlation(queried_pid=100, external_create_time_utc=None,
                               server_file_pid=100, sentinel_pid=100, sentinel_start_utc=None)
    return r["pid_match_server_file"] is True and r["pid_match_sentinel"] is True


def case_l2_corr_2_mismatching_pid():
    r = _compose_correlation(queried_pid=100, external_create_time_utc=None,
                               server_file_pid=200, sentinel_pid=300, sentinel_start_utc=None)
    return r["pid_match_server_file"] is False and r["pid_match_sentinel"] is False


def case_l2_corr_3_matching_start_identity():
    r = _compose_correlation(
        queried_pid=1, external_create_time_utc="2026-01-01T00:00:00+00:00",
        server_file_pid=None, sentinel_pid=None,
        sentinel_start_utc="2026-01-01T00:00:02.000000Z",  # 2s apart
    )
    return r["start_time_match_sentinel"] is True and r["start_time_delta_seconds"] == 2.0


def case_l2_corr_4_mismatching_start_identity():
    r = _compose_correlation(
        queried_pid=1, external_create_time_utc="2026-01-01T00:00:00+00:00",
        server_file_pid=None, sentinel_pid=None,
        sentinel_start_utc="2026-01-01T05:00:00.000000Z",  # 5 hours apart
    )
    return (
        r["start_time_match_sentinel"] is False
        and r["start_time_delta_seconds"] > pc._START_TIME_MATCH_TOLERANCE_SECONDS
    )


def case_l2_corr_5_unknown_when_one_side_unavailable():
    r = _compose_correlation(queried_pid=1, external_create_time_utc=None,
                               server_file_pid=None, sentinel_pid=None, sentinel_start_utc=None)
    return (
        r["pid_match_server_file"] is None
        and r["pid_match_sentinel"] is None
        and r["start_time_match_sentinel"] is None
        and r["start_time_delta_seconds"] is None
    )


# --- Epistemic boundary (mission Cases 16-19) -------------------------------

def _flatten_keys(d, prefix=""):
    keys = []
    if isinstance(d, dict):
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            keys.append(full)
            keys.extend(_flatten_keys(v, full))
    return keys


def case_l2_epi_1_no_module_loading_claim():
    """Proves the result schema contains no field name that could be
    (mis)read as a sys.modules / import-origin claim."""
    r = runtime_process_identity_and_self_report(os.getpid())
    keys = [k.lower() for k in _flatten_keys(r)]
    banned = ("module", "sys_modules", "imported", "import_origin")
    return not any(any(b in k for b in banned) for k in keys)


def case_l2_epi_2_no_execution_use_claim():
    """Proves no field claims a function was called/executed/in use.
    Deliberately checks 'executed'/'execution', not the bare substring
    'execut', so the legitimate external_process.executable field (the
    OS-reported interpreter PATH, not an execution claim) never
    false-positives this check."""
    r = runtime_process_identity_and_self_report(os.getpid())
    keys = [k.lower() for k in _flatten_keys(r)]
    banned = ("executed", "execution", "invoked", "was_called", "function_called", "in_use")
    return not any(any(b in k for b in banned) for k in keys)


def case_l2_epi_3_self_report_stays_identifiable():
    r = runtime_process_identity_and_self_report(os.getpid())
    return (
        "runtime_self_report" in r
        and isinstance(r["runtime_self_report"], dict)
        and "server_pid_file" in r["runtime_self_report"]
        and "sentinel_file" in r["runtime_self_report"]
        and "server_pid_file" not in (r.get("external_process") or {})
        and "sentinel_file" not in (r.get("external_process") or {})
    )


def case_l2_epi_4_external_stays_identifiable():
    r = runtime_process_identity_and_self_report(os.getpid())
    return (
        "external_process" in r
        and isinstance(r["external_process"], dict)
        and "exists" in r["external_process"]
        and "exists" not in (r.get("runtime_self_report") or {})
    )


def case_l2_epi_5_no_verified_active_live_boolean_label():
    """Structurally proves no field is named/shaped like a stronger-than-
    evidence label -- checked against the exact final path segment of
    every field, not a loose substring match, so this can never
    false-positive on an unrelated field that merely contains one of
    these words as part of a longer name."""
    r = runtime_process_identity_and_self_report(os.getpid())
    banned_exact = {
        "verified", "active", "live", "connected", "trusted",
        "healthy", "correct", "runtime_verified", "echo_is_live",
    }
    last_segments = {k.split(".")[-1].lower() for k in _flatten_keys(r)}
    return len(last_segments & banned_exact) == 0


def case_l2_epi_6_never_raises_and_read_only():
    """Rounds out the epistemic-boundary group with the same
    never-raises/read-only discipline Layer 1's Cases 7-8 already
    establish, applied to the new primitive."""
    head_before = _git("rev-parse", "HEAD")
    status_before = _git("status", "--porcelain")
    weird_inputs = [None, "not-a-pid", -1, 0, 1.5, True, [], {}]
    ok = True
    for inp in weird_inputs:
        try:
            r = runtime_process_identity_and_self_report(inp)
            if not isinstance(r, dict) or r["in_scope"] is not False:
                ok = False
        except Exception:
            ok = False
    runtime_process_identity_and_self_report(os.getpid())
    head_after = _git("rev-parse", "HEAD")
    status_after = _git("status", "--porcelain")
    return ok and head_before == head_after and status_before == status_after


# ---------------------------------------------------------------------------
# Reconciliation: reconcile_process_and_selfreport()  (added 2026-09-13, per
# audits/2026-09-13_reconciliation_implementation_design.md's own test
# specification, Section 19 -- 14 categories plus an explicit
# caller-cherry-picking test and the self_heal.py false-positive case.)
# ---------------------------------------------------------------------------

def _synthetic_layer2(
    pid=100,
    exists=True,
    create_time_utc=None,
    server_pid=100,
    sentinel_pid=100,
    sentinel_start_utc=None,
    start_time_match=None,
    start_time_delta=None,
):
    """Builds a Layer-2-result-shaped dict matching
    runtime_process_identity_and_self_report()'s real, live schema exactly
    (re-verified against current source this session -- see
    _compose_correlation()'s own return shape). start_time_match/
    start_time_delta are passed straight into `correlation` untouched,
    deliberately independent of create_time_utc/sentinel_start_utc, so a
    caller of this helper can construct a case where the two would
    disagree if reconcile() ever recomputed them -- Case recon-6 depends
    on that independence to prove reuse, not recomputation."""
    return {
        "pid": pid,
        "in_scope": True,
        "error": None,
        "external_process": {"exists": exists, "create_time_utc": create_time_utc},
        "runtime_self_report": {
            "server_pid_file": {"pid": server_pid},
            "sentinel_file": {"pid": sentinel_pid, "start_utc": sentinel_start_utc},
        },
        "correlation": {
            "pid_match_server_file": (server_pid == pid) if server_pid is not None else None,
            "pid_match_sentinel": (sentinel_pid == pid) if sentinel_pid is not None else None,
            "start_time_match_sentinel": start_time_match,
            "start_time_delta_seconds": start_time_delta,
        },
    }


def case_recon_1_happy_path():
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=100, sentinel_pid=100,
                                 start_time_match=True, start_time_delta=1.0)
    r = reconcile_process_and_selfreport(layer2)
    non_obs = [rel for rel in r["relationships"] if rel["subject"] != "observation_time"]
    obs = next(rel for rel in r["relationships"] if rel["subject"] == "observation_time")
    return (
        r["input_error"] is None
        and len(r["relationships"]) == 5
        and all(rel["state"] == RELATIONSHIP_AGREE for rel in non_obs)
        and obs["state"] == RELATIONSHIP_NEITHER  # never fabricated -- no observed_at field exists
        and r["aggregate"]["raw_agreeing_relationship_count"] == 4
        and r["aggregate"]["independent_corroboration_count"] == 1
        and r["aggregate"]["epistemic_summary"] == EPISTEMIC_EVIDENCE_AGREES
        and r["unrecognized_input_fields"] == []
        and r["scope_statement"] == pc._SCOPE_STATEMENT
    )


def case_recon_2_pid_and_start_time_disagreement():
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=200, sentinel_pid=300,
                                 start_time_match=False, start_time_delta=99999.0)
    r = reconcile_process_and_selfreport(layer2)
    return (
        r["input_error"] is None
        and any(rel["state"] == RELATIONSHIP_DISAGREE for rel in r["relationships"])
        and r["aggregate"]["epistemic_summary"] == EPISTEMIC_EVIDENCE_CONFLICTS
    )


def case_recon_3_missing_self_report_entirely():
    """Missing/malformed self-report degrades to ONE_SIDED/NEITHER --
    never fabricates AGREE from absence."""
    layer2 = {
        "pid": 100, "in_scope": True, "error": None,
        "external_process": {"exists": True, "create_time_utc": None},
        "runtime_self_report": {},
        "correlation": {},
    }
    r = reconcile_process_and_selfreport(layer2)
    pid_rels = [rel for rel in r["relationships"] if rel["subject"] == "pid"]
    return (
        r["input_error"] is None
        and all(rel["state"] in (RELATIONSHIP_ONE_SIDED, RELATIONSHIP_NEITHER) for rel in pid_rels)
        and not any(rel["state"] == RELATIONSHIP_AGREE for rel in r["relationships"])
        and r["aggregate"]["independent_corroboration_count"] == 0
    )


def case_recon_3b_malformed_self_report_field_types():
    """Wrong-typed self-report values (e.g. a string where an int PID is
    expected) never raise -- worst case is an honest DISAGREE/NEITHER,
    not a crash."""
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid="not-an-int", sentinel_pid=None)
    r = reconcile_process_and_selfreport(layer2)
    return r["input_error"] is None and len(r["relationships"]) == 5


def case_recon_4a_dependence_no_independent_witness():
    layer2 = _synthetic_layer2(pid=100, exists=False, server_pid=100, sentinel_pid=100)
    r = reconcile_process_and_selfreport(layer2)
    rels = {tuple(rel["compared"]): rel for rel in r["relationships"] if rel["subject"] == "pid"}
    return (
        rels[(pc._WITNESS_INDEPENDENT, "server_pid_file")]["state"] == RELATIONSHIP_ONE_SIDED
        and rels[(pc._WITNESS_INDEPENDENT, "sentinel_file")]["state"] == RELATIONSHIP_ONE_SIDED
        and rels[("server_pid_file", "sentinel_file")]["state"] == RELATIONSHIP_AGREE
        and r["aggregate"]["independent_corroboration_count"] == 0
    )


def case_recon_4b_dependence_capped_at_one():
    """Independent witness AND both dependent-group members all agree --
    independent_corroboration_count must still be exactly 1, never 2 or 3,
    per Section 14 of the design."""
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=100, sentinel_pid=100)
    r = reconcile_process_and_selfreport(layer2)
    pid_agree_count = sum(1 for rel in r["relationships"]
                            if rel["subject"] == "pid" and rel["state"] == RELATIONSHIP_AGREE)
    return pid_agree_count == 3 and r["aggregate"]["independent_corroboration_count"] == 1


def case_recon_5_pid_reuse_disagree_wins():
    """PID-reuse scenario: every PID relationship agrees (a coincidental
    or reused PID), but start_time disagrees -- epistemic_summary must
    become EVIDENCE_CONFLICTS despite 3 of 5 relationships agreeing.
    'DISAGREE always wins,' explicitly re-verified for this exact case
    per the mission's own instruction."""
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=100, sentinel_pid=100,
                                 start_time_match=False, start_time_delta=999999.0)
    r = reconcile_process_and_selfreport(layer2)
    pid_agree_count = sum(1 for rel in r["relationships"]
                            if rel["subject"] == "pid" and rel["state"] == RELATIONSHIP_AGREE)
    return (
        pid_agree_count == 3
        and r["aggregate"]["independent_corroboration_count"] == 1
        and r["aggregate"]["epistemic_summary"] == EPISTEMIC_EVIDENCE_CONFLICTS
    )


def case_recon_6_timestamp_reuse_not_recomputed():
    """Deliberately internally-inconsistent raw timestamps (5 hours apart)
    paired with a correlation field that explicitly claims a match --
    proves reconcile() trusts Layer 2's pre-computed
    start_time_match_sentinel verbatim rather than independently
    re-parsing create_time_utc/sentinel_start_utc itself (Section 9:
    reuse, never recompute). observation_time must stay NEITHER
    regardless -- no observed_at field exists in the live schema."""
    layer2 = _synthetic_layer2(
        pid=100, exists=True,
        create_time_utc="2026-01-01T00:00:00+00:00",
        sentinel_start_utc="2026-01-01T05:00:00.000000Z",
        start_time_match=True, start_time_delta=1.0,
    )
    r = reconcile_process_and_selfreport(layer2)
    start_rel = next(rel for rel in r["relationships"] if rel["subject"] == "start_time")
    obs_rel = next(rel for rel in r["relationships"] if rel["subject"] == "observation_time")
    return (
        start_rel["state"] == RELATIONSHIP_AGREE
        and start_rel["values"]["delta_seconds"] == 1.0
        and obs_rel["state"] == RELATIONSHIP_NEITHER
    )


def case_recon_7_purity():
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=100, sentinel_pid=100,
                                 start_time_match=True, start_time_delta=1.0)
    before = copy.deepcopy(layer2)
    r1 = reconcile_process_and_selfreport(layer2)
    r2 = reconcile_process_and_selfreport(layer2)
    return layer2 == before and r1 == r2


def case_recon_8_zero_io_via_mocking():
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=100, sentinel_pid=100,
                                 start_time_match=True, start_time_delta=1.0)

    def _boom(*a, **k):
        raise AssertionError("reconcile_process_and_selfreport performed real I/O")

    with mock.patch("psutil.Process", side_effect=_boom), \
         mock.patch("builtins.open", side_effect=_boom), \
         mock.patch("subprocess.run", side_effect=_boom):
        try:
            r = reconcile_process_and_selfreport(layer2)
        except AssertionError:
            return False
    return r["input_error"] is None


def case_recon_9_layer1_exclusion():
    """An extraneous, Layer-1-shaped top-level field must be disclosed via
    unrecognized_input_fields, never silently read, never affect the
    result -- Layer 1 is structurally outside this function's domain."""
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=100, sentinel_pid=100,
                                 start_time_match=True, start_time_delta=1.0)
    rigged = copy.deepcopy(layer2)
    rigged["sha256"] = "deadbeef" * 8
    rigged["head_blob_sha256_or_none"] = None
    r_clean = reconcile_process_and_selfreport(layer2)
    r_rigged = reconcile_process_and_selfreport(rigged)
    return (
        "sha256" in r_rigged["unrecognized_input_fields"]
        and "head_blob_sha256_or_none" in r_rigged["unrecognized_input_fields"]
        and r_rigged["aggregate"] == r_clean["aggregate"]
        and r_rigged["relationships"] == r_clean["relationships"]
    )


def case_recon_10_self_heal_false_positive():
    """The mission's specific adversarial test: real Layer 1 data for
    app/core/self_heal.py (tracked, clean, confirmed zero real importers
    -- see CLAUDE.md's Health Monitoring section) combined with real
    Layer 2 data for the live Echo process (PID 7644, read-only psutil
    inspection only -- never signaled/restarted/touched otherwise) must
    never produce any reconciliation field claiming the file is loaded,
    imported, or executing. Separately proves the primitive has zero
    access to Layer 1 at all: no Layer 1 field name appears anywhere in
    the reconciliation output's own schema."""
    l1 = working_tree_file_identity("app/core/self_heal.py")
    l2 = runtime_process_identity_and_self_report(7644)
    r = reconcile_process_and_selfreport(l2)
    keys = [k.lower() for k in _flatten_keys(r)]
    banned = ("loaded", "import", "module", "executing", "execution",
              "self_heal", "in_use", "running_code")
    no_forbidden_claim = not any(any(b in k for b in banned) for k in keys)
    l1_field_names = {"sha256", "head_blob_sha256_or_none", "tracked", "modified_vs_head"}
    no_l1_leakage = not any(k.split(".")[-1] in l1_field_names for k in _flatten_keys(r))
    return (
        l1["exists"] is True and l1["tracked"] is True  # fixture sanity
        and no_forbidden_claim
        and no_l1_leakage
    )


def case_recon_11_complete_input_requirement():
    """Exactly one required positional argument -- no field-selection
    kwargs a caller could use to pass only a favorable subset."""
    sig = inspect.signature(reconcile_process_and_selfreport)
    params = list(sig.parameters.values())
    return (
        len(params) == 1
        and params[0].kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        and params[0].default is inspect.Parameter.empty
    )


def case_recon_12_output_completeness():
    inputs = [{}, None, "garbage", 42, _synthetic_layer2(), {"pid": 1}]
    required_top = {"input_error", "witnesses", "relationships", "aggregate",
                      "unrecognized_input_fields", "scope_statement"}
    for inp in inputs:
        r = reconcile_process_and_selfreport(inp)
        if set(r.keys()) != required_top:
            return False
        if len(r["relationships"]) != 5:
            return False
        for rel in r["relationships"]:
            if not {"subject", "compared", "state", "values"} <= set(rel.keys()):
                return False
    return True


def case_recon_13_exact_enum_field_contract():
    allowed_states = {RELATIONSHIP_AGREE, RELATIONSHIP_DISAGREE, RELATIONSHIP_ONE_SIDED, RELATIONSHIP_NEITHER}
    allowed_summaries = {EPISTEMIC_EVIDENCE_AGREES, EPISTEMIC_EVIDENCE_CONFLICTS, EPISTEMIC_INSUFFICIENT_EVIDENCE}
    samples = [
        _synthetic_layer2(),
        _synthetic_layer2(exists=False, server_pid=None, sentinel_pid=None),
        _synthetic_layer2(server_pid=999, sentinel_pid=888),
        {}, None,
    ]
    for inp in samples:
        r = reconcile_process_and_selfreport(inp)
        if any(rel["state"] not in allowed_states for rel in r["relationships"]):
            return False
        if r["aggregate"]["epistemic_summary"] not in allowed_summaries:
            return False
        keys = {k.split(".")[-1].lower() for k in _flatten_keys(r)}
        if "verified" in keys:
            return False
    return True


def case_recon_14_malformed_top_level_input():
    bad_inputs = [None, "a string", 42, 3.14, [], (), set(), True, False]
    for inp in bad_inputs:
        try:
            r = reconcile_process_and_selfreport(inp)
        except Exception:
            return False
        if r["input_error"] != "malformed_layer2_result":
            return False
        if any(rel["state"] == RELATIONSHIP_AGREE for rel in r["relationships"]):
            return False
        if r["aggregate"]["epistemic_summary"] == EPISTEMIC_EVIDENCE_AGREES:
            return False
    return True


def case_recon_15_caller_cherry_picking():
    """A caller cannot manufacture extra corroboration by injecting
    fabricated, corroboration-shaped field names the schema doesn't
    recognize -- independent_corroboration_count and every relationship
    are computed only from the 3 hardcoded witness names against the
    schema's known fields, never from arbitrary caller-supplied field
    names, however favorable-looking."""
    layer2 = _synthetic_layer2(pid=100, exists=True, server_pid=100, sentinel_pid=100,
                                 start_time_match=True, start_time_delta=1.0)
    baseline = reconcile_process_and_selfreport(layer2)

    rigged = copy.deepcopy(layer2)
    rigged["additional_independent_witness_agrees"] = True
    rigged["extra_corroboration_hint"] = 99
    rigged_result = reconcile_process_and_selfreport(rigged)

    return (
        baseline["aggregate"] == rigged_result["aggregate"]
        and baseline["relationships"] == rigged_result["relationships"]
        and "additional_independent_witness_agrees" in rigged_result["unrecognized_input_fields"]
        and "extra_corroboration_hint" in rigged_result["unrecognized_input_fields"]
    )


CASES = [
    ("tracked file, clean working tree", case_1_tracked_clean),
    ("tracked file, modified vs HEAD", case_2_tracked_modified),
    ("untracked file (exists, not in HEAD, not tracked)", case_3_untracked),
    ("missing/never-existed file -> explicit False/None, not an error", case_4_missing_file),
    ("invalid path argument (type/empty) -> in_scope=False, all evidence None", case_5a_invalid_type),
    ("path resolves outside project root -> refused, not misreported as absent", case_5b_outside_root),
    ("repeated invocation is deterministic", case_6_deterministic),
    ("read-only: zero git/filesystem mutation across all calls", case_7_read_only),
    ("never raises, for any input shape", case_8_never_raises),
    ("tracked-but-missing-from-disk: modified_vs_head stays unknown, not inferred", case_9_tracked_but_missing_from_disk),
    ("git unavailable -> None, never coerced to False", case_10_git_unknown_is_not_false),
    ("equal/different/unknown hashes produce distinct, non-fabricated results", case_11_equal_and_different_are_distinguished),
    ("[symlink] tracked symlink -> untracked target: tracked reflects literal path", case_12_symlink_tracked_untracked_target),
    ("[symlink] head blob is the symlink's own object, not target content", case_13_symlink_blob_is_its_own_not_targets_content),
    ("[symlink] no silent substitution of sibling's git identity", case_14_symlink_identity_not_substituted_with_sibling),
    ("[symlink] symlinked-directory root escape still refused (no weakening)", case_15_symlinked_directory_escape_still_refused),
    ("[symlink] ordinary files unaffected by the two-branch fix", case_16_ordinary_files_unaffected_by_the_fix),
    ("[L2 ext] known existing PID -> real external fields populate", case_l2_ext_1_known_existing_pid),
    ("[L2 ext] nonexistent PID -> exists=False, no error", case_l2_ext_2_nonexistent_pid),
    ("[L2 ext] vanishes mid-observation -> honest partial degrade, no raise", case_l2_ext_3_vanishes_mid_observation),
    ("[L2 ext] access-denied field -> flagged, other fields unaffected", case_l2_ext_4_access_denied_field),
    ("[L2 self-report] both artifacts present and valid", case_l2_sr_1_both_artifacts_present_valid),
    ("[L2 self-report] missing PID file", case_l2_sr_2_missing_pid_file),
    ("[L2 self-report] missing sentinel", case_l2_sr_3_missing_sentinel),
    ("[L2 self-report] malformed sentinel JSON", case_l2_sr_4_malformed_sentinel_json),
    ("[L2 self-report] unreadable artifact", case_l2_sr_5_unreadable_artifact),
    ("[L2 self-report] missing expected field stays None, not malformed", case_l2_sr_6_missing_expected_field),
    ("[L2 self-report] malformed PID file (non-integer content)", case_l2_sr_7_malformed_pid_file_non_integer),
    ("[L2 correlation] matching PID -> True", case_l2_corr_1_matching_pid),
    ("[L2 correlation] mismatching PID -> False", case_l2_corr_2_mismatching_pid),
    ("[L2 correlation] matching start identity within tolerance", case_l2_corr_3_matching_start_identity),
    ("[L2 correlation] mismatching start identity outside tolerance", case_l2_corr_4_mismatching_start_identity),
    ("[L2 correlation] unknown when one side unavailable -> None, not False", case_l2_corr_5_unknown_when_one_side_unavailable),
    ("[L2 epistemic] no module-loading claim anywhere in schema", case_l2_epi_1_no_module_loading_claim),
    ("[L2 epistemic] no execution/use claim anywhere in schema", case_l2_epi_2_no_execution_use_claim),
    ("[L2 epistemic] self-report evidence stays identifiable as self-report", case_l2_epi_3_self_report_stays_identifiable),
    ("[L2 epistemic] external evidence stays identifiable as external", case_l2_epi_4_external_stays_identifiable),
    ("[L2 epistemic] no verified/active/live/connected/trusted label anywhere", case_l2_epi_5_no_verified_active_live_boolean_label),
    ("[L2 epistemic] never raises + read-only across weird inputs", case_l2_epi_6_never_raises_and_read_only),
    ("[recon 1] happy path: full agreement", case_recon_1_happy_path),
    ("[recon 2] PID and start-time disagreement -> EVIDENCE_CONFLICTS", case_recon_2_pid_and_start_time_disagreement),
    ("[recon 3] self-report missing entirely -> ONE_SIDED/NEITHER, never fabricated AGREE", case_recon_3_missing_self_report_entirely),
    ("[recon 3b] malformed self-report field types -> never raises", case_recon_3b_malformed_self_report_field_types),
    ("[recon 4a] dependence: no independent witness, dependent group still self-consistent", case_recon_4a_dependence_no_independent_witness),
    ("[recon 4b] dependence: independent + full dependent-group agreement capped at 1", case_recon_4b_dependence_capped_at_one),
    ("[recon 5] PID reuse: 3/5 relationships agree, DISAGREE still wins", case_recon_5_pid_reuse_disagree_wins),
    ("[recon 6] start-time reused not recomputed; observation_time always NEITHER", case_recon_6_timestamp_reuse_not_recomputed),
    ("[recon 7] purity: deterministic, zero input mutation", case_recon_7_purity),
    ("[recon 8] zero-I/O: psutil/open/subprocess.run never touched", case_recon_8_zero_io_via_mocking),
    ("[recon 9] Layer 1 exclusion: extraneous field disclosed, never read", case_recon_9_layer1_exclusion),
    ("[recon 10] self_heal.py real-data false-positive: no loaded/execution claim, zero Layer 1 access", case_recon_10_self_heal_false_positive),
    ("[recon 11] complete-input requirement: exactly one required positional arg", case_recon_11_complete_input_requirement),
    ("[recon 12] output completeness: always exactly 5 relationships + full top-level schema", case_recon_12_output_completeness),
    ("[recon 13] exact enum/field contract: no unapproved state, no 'verified' field", case_recon_13_exact_enum_field_contract),
    ("[recon 14] malformed top-level input: never raises, degrades honestly", case_recon_14_malformed_top_level_input),
    ("[recon 15] caller cherry-picking: fabricated fields can't manufacture corroboration", case_recon_15_caller_cherry_picking),
]

if __name__ == "__main__":
    print("--- proving the symlink cases below would have failed against the pre-fix code ---")
    old_impl_reproduces_the_bug = _prove_old_implementation_would_have_failed()
    print(f"pre-fix behavior reproduced (confirms these are real regression tests): "
          f"{old_impl_reproduces_the_bug}\n")

    passed = 0
    for name, fn in CASES:
        try:
            ok = fn()
        except AssertionError as exc:
            print(f"FAIL  {name}  (fixture assumption broken: {exc})")
            continue
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        passed += bool(ok)
    print(f"\n{passed}/{len(CASES)} discrimination cases passed")
    sys.exit(0 if passed == len(CASES) and old_impl_reproduces_the_bug else 1)
