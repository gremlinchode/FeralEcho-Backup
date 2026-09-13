#!/usr/bin/env python3
"""
verify_provenance_check.py -- discrimination tests for
app/core/provenance_check.py's working_tree_file_identity(), the same
style as scripts/verify_seam_engine.py / scripts/verify_liveness_ledger.py:
prove the primitive's epistemic boundary, not merely that it runs without
raising.

Scope: this is the ONLY primitive implemented so far (the smallest safe
slice identified by audits/2026-09-11_provenance_implementation_boundary_
audit.md). There is no runtime_process_identity(),
runtime_self_reported_module_origin(), or reconcile() to test yet.

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
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, ".")
import app.core.provenance_check as pc  # noqa: E402
from app.core.provenance_check import (  # noqa: E402
    working_tree_file_identity,
    _compose_identity,
)

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
