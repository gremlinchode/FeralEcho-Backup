# app/core/provenance_check.py
# ============================================================
# PROVENANCE — LEAF PRIMITIVE 1 OF 4: working_tree_file_identity()
# ============================================================
# (Leaf primitive 2 of 4, runtime_process_identity_and_self_report(),
# added 2026-09-13 -- see the second module-level docstring block below,
# just above its own definition, for its full contract. Summary: it
# provides externally-observed OS process facts (via psutil) about a
# given PID, plus the literal contents of two ALREADY-EXISTING runtime
# self-report artifacts this process itself writes (memory/echo_server.pid,
# memory/echo_sentinel.json) -- kept in two structurally separate
# sub-objects, never merged, per audits/2026-09-12_provenance_layer2_
# boundary_review.md's own required contract. It does NOT inspect
# sys.modules, does NOT prove module loading/import/execution, and does
# NOT introduce any verified/active/live-shaped boolean -- see that
# function's own docstring for the exact, narrow epistemic boundary.)
# ============================================================
# Implements ONLY the smallest safe slice identified by the completed
# provenance research arc's final design gate:
#   audits/2026-09-10_phase2_provenance_reconciliation.md
#   audits/2026-09-11_read_only_provenance_interface_design.md
#   audits/2026-09-11_provenance_leaf_primitives_validation.md
#   audits/2026-09-11_provenance_implementation_boundary_audit.md ("PROCEED
#     TO IMPLEMENTATION", Section 14: "Step 1 alone ... is the only one of
#     the four primitives with zero self-attestation exposure").
#
# This module does NOT implement runtime_process_identity(),
# runtime_self_reported_module_origin(), or reconcile(). Those are
# separate, later, separately-reviewed slices per the boundary audit's own
# Section 13 sequencing -- do not add them here.
#
# Design principle (from the boundary audit, Section 4/10), followed
# structurally, not just in prose:
#   evidence collection -> provenance/evidence record -> interpretation
# NEVER:
#   interpretation -> self-generated assertion presented as proof
#
# Concretely: this module is split into (1) pure evidence-gathering
# helpers that talk to the filesystem/git and can fail only into an
# explicit None/False, never an exception, and (2) one pure composition
# function, _compose_identity(), that assembles the final record from
# already-gathered evidence and computes the one derived field
# (`modified_vs_head`) -- it performs zero I/O, so its decision logic can
# be tested directly against synthetic evidence without touching the
# filesystem or git at all. This mirrors an existing, established pattern
# in this codebase (e.g. app/core/seam_engine.py's check_pair() being a
# pure evaluator separate from observe()'s I/O) -- not invented for this
# module specifically.
#
# Scope, exactly as bounded by the mission that authorized this file:
#   - Read-only. Never modifies files, git state, or runtime state.
#   - Objective. Every field is either a direct filesystem/git plumbing
#     fact, or explicitly None when that fact could not be established --
#     never a self-generated assertion.
#   - Deterministic. Same repo state + same path -> same result.
#   - Narrow. Says nothing about runtime liveness, process identity,
#     module import state, route reachability, or whether an
#     implementation is "alive" or "correct" -- those are separate,
#     unimplemented primitives (runtime_process_identity(),
#     runtime_self_reported_module_origin(), reconcile()).
#
# Field-name note, disclosed rather than silently resolved: the four
# predecessor documents use three slightly different names for the
# HEAD-blob-hash field across their history (an unlabeled second hash in
# read_only_provenance_interface_design.md's one-line summary; the
# empirically-validated `head_sha256` in provenance_leaf_primitives_
# validation.md's tested implementation; `head_blob_sha256_or_none` in
# provenance_implementation_boundary_audit.md's final, most-recent
# tightening, Section 6). This module uses the final document's literal
# field name, `head_blob_sha256_or_none`, since that document is
# explicitly the terminal word in the arc ("re-derives the boundary from
# first principles ... then attacks the evidence contract") and the
# mission that authorized this file says to follow existing vocabulary
# rather than invent a cleaner-looking alternative.
#
# Two fields NOT present in any predecessor document's return-shape
# listing are added here, disclosed rather than silently invented:
# `in_scope` and `error`. None of the four predecessor documents fully
# specify this primitive's behavior for a caller-supplied path that is
# malformed or resolves outside the project root (that discussion exists
# for runtime_self_reported_module_origin(), not this function) -- and
# the mission that authorized this file explicitly requires that such a
# case never be silently collapsed into a generic "doesn't exist" or
# "verified" result. `in_scope=False` + a short `error` code is the
# minimal, disclosed extension needed to satisfy that requirement without
# inventing any *interpretive* vocabulary beyond it.
# ============================================================

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional

import psutil  # already installed in this project's environment; confirmed
               # by audits/2026-09-11_provenance_leaf_primitives_validation.md
               # and re-confirmed live this session -- no new dependency added.

# ---------------------------------------------------------------------------
# Project-root resolution -- same walk-up-to-run.py algorithm already used
# by app/core/echo_tool_dispatch.py's _find_project_root(). Duplicated, not
# imported: this module is deliberately dependency-light (no `requests`,
# no tool-dispatch wiring), matching this codebase's existing convention of
# each module defining its own small root-resolution helper rather than a
# shared one (self_edit_manager.py and echo_tool_dispatch.py already use
# two different implementations of the same idea).
# ---------------------------------------------------------------------------

_GIT_TIMEOUT_SECONDS = 5


def _find_project_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isfile(os.path.join(here, "run.py")):
            return os.path.realpath(here)
        here = os.path.dirname(here)
    return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


_PROJECT_ROOT = _find_project_root()


# ---------------------------------------------------------------------------
# Path confinement -- TWO INDEPENDENT BRANCHES, deliberately never merged.
#
# Fixed 2026-09-13 (red-team finding, symlink path substitution): the
# original single-branch design used one realpath()-resolved path for
# EVERYTHING -- filesystem stat/read AND the relpath handed to git. For a
# symlink, realpath() follows the link to its target, which silently
# substitutes the TARGET's git identity (tracked status, HEAD blob) for
# the SYMLINK's own -- e.g. a tracked symlink whose git blob is literally
# the link-target text was reported with the target *file's* content hash,
# and a tracked symlink pointing at an untracked target was reported as
# untracked. Confirmed empirically in an isolated scratch repository; see
# the red-team report for full reproduction. Zero live impact against the
# real FeralEcho tree today (it contains no symlinks anywhere, tracked or
# not), but the contract must not depend on today's repository topology.
#
# Branch 1, _resolve_within_root() -- FILESYSTEM identity. UNCHANGED from
# before this fix: same enforcement shape as echo_tool_dispatch.py's
# _guard_read_path(), realpath()-resolved (so it correctly follows
# symlinks and collapses `..`, and correctly refuses a symlinked directory
# that resolves outside the root -- see the red-team's Case 4). Used ONLY
# for the root-confinement decision and for _stat_evidence() (exists,
# size, mtime, sha256) -- i.e. "what bytes do you get if you actually open
# this path." Must NEVER be used to build a git command.
#
# Branch 2, _lexical_git_relpath() -- GIT PATH identity. New in this fix.
# Normalizes the caller's literal path using ONLY string-level operations
# (os.path.normpath -- no filesystem access, no symlink resolution at
# all), so the path handed to `git ls-files`/`git show HEAD:` always names
# exactly what the caller asked about, never a symlink's resolved target.
# Also independently confined to the project root (lexically) -- not for
# a real escape risk (git's own `HEAD:<path>` syntax already refuses any
# path outside the repository with a hard "fatal: ... is outside
# repository", confirmed directly), but so `in_scope` stays an honest,
# cheap, up-front decision rather than depending on git's own error text.
#
# in_scope is True only when BOTH branches agree the path is confined --
# this can only ever make confinement equal-or-stricter than the original
# single-branch check, never weaker.
# ---------------------------------------------------------------------------

def _resolve_within_root(path: str) -> tuple[Optional[str], Optional[str]]:
    """FILESYSTEM branch only. Returns (resolved_absolute_path, None) if
    `path` is confined to the project root, or (None, error_code) if it is
    not. Follows symlinks (realpath). Never raises. Do not use this
    function's return value to build a git command -- see
    _lexical_git_relpath() for that."""
    try:
        if os.path.isabs(path):
            resolved = os.path.realpath(path)
        else:
            resolved = os.path.realpath(os.path.join(_PROJECT_ROOT, path))
    except (OSError, ValueError):
        return None, "path_resolution_failed"

    if resolved != _PROJECT_ROOT and not resolved.startswith(_PROJECT_ROOT + os.sep):
        return None, "path_outside_project_root"

    return resolved, None


def _lexical_git_relpath(path: str) -> tuple[Optional[str], Optional[str]]:
    """GIT PATH branch only. Returns (project_relative_path, None) if
    `path` is confined to the project root under PURE LEXICAL
    normalization (os.path.normpath -- never realpath, never touches the
    filesystem, never follows a symlink), or (None, error_code) if it is
    not. This is the path string handed to `git ls-files`/`git show
    HEAD:` -- it always names exactly what the caller literally supplied,
    so a symlink along the path can never cause git evidence to be
    silently reported for a different path than the one queried."""
    try:
        if os.path.isabs(path):
            candidate = os.path.normpath(path)
        else:
            candidate = os.path.normpath(os.path.join(_PROJECT_ROOT, path))
    except (OSError, ValueError):
        return None, "path_resolution_failed"

    if candidate != _PROJECT_ROOT and not candidate.startswith(_PROJECT_ROOT + os.sep):
        return None, "path_outside_project_root"

    return os.path.relpath(candidate, _PROJECT_ROOT), None


# ---------------------------------------------------------------------------
# Evidence gathering -- filesystem. Every failure mode maps to an explicit
# None/False, never an exception, and never a generic "doesn't exist" when
# the real evidence is "exists but unreadable."
# ---------------------------------------------------------------------------

def _stat_evidence(resolved_path: str) -> tuple[bool, Optional[int], Optional[str], Optional[str]]:
    """Returns (exists, size, mtime_iso8601, sha256) for a real, regular
    file. `exists` answers "is this a regular file" specifically (claim 1
    in the boundary audit's evidence matrix) -- a directory, a symlink to a
    missing target, or any non-regular-file path reports exists=False, not
    a distinct third state, matching this primitive's deliberately narrow
    "is this a file" scope."""
    if not os.path.isfile(resolved_path):
        return False, None, None, None

    try:
        st = os.stat(resolved_path)
        mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
        with open(resolved_path, "rb") as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        return True, st.st_size, mtime_iso, sha256
    except OSError:
        # Exists (confirmed above) but became unreadable between the isfile()
        # check and the read (permission change, race with a concurrent
        # delete, etc.) -- report the fact honestly rather than silently
        # reclassifying it as "doesn't exist."
        return True, None, None, None


# ---------------------------------------------------------------------------
# Evidence gathering -- git plumbing. Two fixed, read-only subcommands
# only. The path argument is the only variable part of either command line;
# both are invoked via subprocess.run() with an explicit argv list, never
# shell=True, so there is no command-injection surface and no way for a
# caller to substitute an arbitrary git subcommand.
# ---------------------------------------------------------------------------

def _git_tracked(relpath: str) -> Optional[bool]:
    """git ls-files --error-unmatch is git's own designed mechanism for
    this exact question. Exit 0 = tracked, exit 1 = not tracked -- both are
    well-defined, expected outcomes, not error conditions. Any other exit
    code (a genuinely broken/unavailable repo) or a failure to even launch
    git maps to None: not "False", because we have no evidence either way,
    and asserting False would misrepresent an unknown as a negative fact."""
    try:
        result = subprocess.run(
            ["git", "-C", _PROJECT_ROOT, "ls-files", "--error-unmatch", "--", relpath],
            capture_output=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def _git_head_blob_sha256(relpath: str) -> Optional[str]:
    """git show HEAD:<path> is independent of working-tree existence and
    independent of index/tracked state (claim 5 in the boundary audit's
    evidence matrix is deliberately its own, separately-checkable fact).
    A nonzero exit -- path not in HEAD, detached/missing HEAD, or any other
    git failure -- maps to None: "no HEAD blob evidence available", never
    a fabricated hash."""
    try:
        result = subprocess.run(
            ["git", "-C", _PROJECT_ROOT, "show", f"HEAD:{relpath}"],
            capture_output=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    return hashlib.sha256(result.stdout).hexdigest()


# ---------------------------------------------------------------------------
# Pure composition -- zero I/O. This is the ONLY place `modified_vs_head`
# is decided, and it is decided from already-gathered evidence alone, never
# by re-deriving anything from the filesystem or git itself. Kept separate
# specifically so its decision logic is directly unit-testable against
# synthetic evidence (see scripts/verify_provenance_check.py), including
# edge cases -- e.g. "tracked in HEAD but absent from disk" -- that would
# otherwise require actually mutating this repository's working tree to
# construct as a real fixture.
# ---------------------------------------------------------------------------

def _compose_identity(
    *,
    path: str,
    in_scope: bool,
    error: Optional[str],
    exists: Optional[bool],
    size: Optional[int],
    mtime: Optional[str],
    sha256: Optional[str],
    tracked: Optional[bool],
    head_blob_sha256: Optional[str],
) -> dict:
    if not in_scope:
        return {
            "path": path,
            "in_scope": False,
            "error": error,
            "exists": None,
            "tracked": None,
            "size": None,
            "mtime": None,
            "sha256": None,
            "head_blob_sha256_or_none": None,
            "modified_vs_head": None,
        }

    # `modified_vs_head` is only ever computed when BOTH sides of the
    # comparison are real, independently-gathered hashes. If the file does
    # not exist on disk, or HEAD has no blob for this path, this is
    # deliberately left None rather than inferring "modified" from one
    # side's absence -- collapsing "no working-tree hash to compare" into
    # an interpretive "yes, different" would be exactly the kind of
    # premature interpretation the design this module implements exists to
    # avoid. The caller can still see the full, disaggregated picture
    # (exists, tracked, head_blob_sha256_or_none) and draw that conclusion
    # itself, at whatever higher layer is responsible for interpretation.
    modified_vs_head: Optional[bool] = None
    if sha256 is not None and head_blob_sha256 is not None:
        modified_vs_head = sha256 != head_blob_sha256

    return {
        "path": path,
        "in_scope": True,
        "error": error,
        "exists": exists,
        "tracked": tracked,
        "size": size,
        "mtime": mtime,
        "sha256": sha256,
        "head_blob_sha256_or_none": head_blob_sha256,
        "modified_vs_head": modified_vs_head,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def working_tree_file_identity(path) -> dict:
    """
    Objective, read-only evidence about one file's identity in the current
    Git working tree. Never modifies anything; never raises.

    Args:
        path: a path, absolute or relative to the project root
              (e.g. "app/core/liveness_ledger.py"). Any type other than a
              non-empty string, or a path resolving outside the project
              root, is reported as `in_scope: False` with a machine-
              readable `error` code -- never silently coerced into a
              "file doesn't exist" result, and never executed as a path
              expression of any kind.

    Returns a dict with exactly these keys, always present:
        path                       -- the caller's own argument, echoed
                                       back verbatim (never the resolved
                                       absolute filesystem path -- this
                                       primitive does not disclose local
                                       filesystem layout).
        in_scope (bool)            -- False iff the argument was invalid or
                                       resolved outside the project root.
                                       All other fields are None in that case.
        error (str or None)        -- a short machine-readable reason when
                                       in_scope is False; otherwise None.
        exists (bool or None)      -- is this a regular file on disk, right
                                       now. None only when in_scope is False.
        tracked (bool or None)     -- is the caller's LITERAL path (lexically
                                       normalized only -- never symlink-
                                       resolved) in Git's index (`git
                                       ls-files --error-unmatch`), computed
                                       independently of `exists` -- a file
                                       can be tracked without existing on
                                       disk (deleted-but-not-`git rm`'d), or
                                       exist without being tracked
                                       (`git rm --cached`'d, or genuinely
                                       untracked). None if git could not be
                                       consulted at all (not "False"). If
                                       the queried path is a symlink, this
                                       is the symlink's OWN tracked status,
                                       never the status of whatever it
                                       points at.
        size (int or None)         -- byte size, only when exists is True
                                       and the file was readable.
        mtime (str or None)        -- ISO-8601 UTC modification time, only
                                       when exists is True and the file was
                                       readable.
        sha256 (str or None)       -- sha256 of the bytes obtained by
                                       reading the queried path, only when
                                       exists is True and the file was
                                       readable. For a symlink, this follows
                                       the link (ordinary POSIX open()
                                       semantics) and hashes the TARGET's
                                       content -- a deliberately different
                                       path interpretation than `tracked`/
                                       `head_blob_sha256_or_none` below, see
                                       those fields' own notes.
        head_blob_sha256_or_none (str or None)
                                    -- sha256 of the blob HEAD holds for the
                                       caller's LITERAL path (`git show
                                       HEAD:<literal-path>`, lexically
                                       normalized only -- never symlink-
                                       resolved), computed independently of
                                       `exists` and `tracked`. None if HEAD
                                       has no blob for this exact path, or
                                       git could not be consulted. If the
                                       queried path is a tracked symlink,
                                       this is the hash of the symlink's OWN
                                       blob (which Git stores as the link-
                                       target text, not the target file's
                                       content) -- never the resolved
                                       target's content hash. Because of
                                       this, `modified_vs_head` for a
                                       symlink compares two evidence sources
                                       with deliberately different meanings
                                       (dereferenced content vs. literal
                                       link-object identity) and will
                                       typically read True even when the
                                       symlink itself has not changed --
                                       this is disclosed, not fixed here;
                                       it follows from preserving `sha256`'s
                                       existing, unchanged semantics while
                                       correcting `tracked`/this field to
                                       stop misreporting the wrong Git
                                       object (see the module header for
                                       the full fix rationale).
        modified_vs_head (bool or None)
                                    -- sha256 != head_blob_sha256_or_none,
                                       computed ONLY when both are real
                                       hashes; None whenever either side is
                                       unavailable (never inferred from a
                                       one-sided absence).

    What this function CAN establish (per the boundary audit's evidence
    matrix, claims 1-5): whether a specific path is a regular file right
    now; whether Git's index tracks it; the sha256 of its current bytes;
    the sha256 of HEAD's blob for it, if any; and whether those two hashes
    differ. Each of these is independently, externally verifiable by
    anyone with filesystem and git access to this repository -- none of it
    depends on this process's own say-so.

    What this function explicitly CANNOT and does NOT establish: whether
    any running process has loaded this file, whether it is executing, or
    whether it is "responsible for" any observed behavior. Those are
    runtime claims requiring runtime_process_identity() and
    runtime_self_reported_module_origin() (unimplemented; a later, separate
    slice) plus explicit behavioral evidence -- never this function alone.
    A caller must not use a VERIFIED-sounding label for this function's
    output beyond exactly what it measured: file identity in the working
    tree and HEAD, nothing about runtime.
    """
    try:
        if not isinstance(path, str) or not path.strip():
            return _compose_identity(
                path=path if isinstance(path, str) else repr(path),
                in_scope=False,
                error="invalid_path_argument",
                exists=None, size=None, mtime=None, sha256=None,
                tracked=None, head_blob_sha256=None,
            )

        # Two independent branches (see the confinement block above) --
        # NEVER derive one from the other. fs_resolved_path (realpath,
        # symlink-following) feeds only filesystem stat/read. git_relpath
        # (lexical only, symlink-blind) feeds only git ls-files/show. This
        # is the exact fix for the red-team's confirmed symlink defect:
        # before, git_relpath was computed FROM fs_resolved_path, which
        # silently substituted a symlink's resolved target for the
        # symlink's own git identity.
        fs_resolved_path, fs_err = _resolve_within_root(path)
        git_relpath, git_err = _lexical_git_relpath(path)

        if fs_resolved_path is None or git_relpath is None:
            return _compose_identity(
                path=path, in_scope=False, error=(fs_err or git_err),
                exists=None, size=None, mtime=None, sha256=None,
                tracked=None, head_blob_sha256=None,
            )

        exists, size, mtime, sha256 = _stat_evidence(fs_resolved_path)
        tracked = _git_tracked(git_relpath)
        head_blob_sha256 = _git_head_blob_sha256(git_relpath)

        return _compose_identity(
            path=path, in_scope=True, error=None,
            exists=exists, size=size, mtime=mtime, sha256=sha256,
            tracked=tracked, head_blob_sha256=head_blob_sha256,
        )
    except Exception as exc:  # last-resort safety net -- this function must never raise
        return _compose_identity(
            path=path if isinstance(path, str) else repr(path),
            in_scope=False,
            error=f"internal_error:{type(exc).__name__}",
            exists=None, size=None, mtime=None, sha256=None,
            tracked=None, head_blob_sha256=None,
        )


# ============================================================
# PROVENANCE — LEAF PRIMITIVE 2 OF 4: runtime_process_identity_and_self_report()
# ============================================================
# Implements the primitive identified by
# audits/2026-09-12_provenance_layer2_boundary_review.md Section 6/7 as
# the smallest safe next step: Candidate A (externally-observed OS process
# facts) merged with Candidate C (reading two ALREADY-EXISTING runtime
# self-report artifacts) -- explicitly NOT Candidate B
# (runtime_self_reported_module_origin / sys.modules inspection), which
# that review found requires new in-process code this mission is not
# authorized to add (no new Flask route, no new echo_tool_dispatch.py
# tool, no restart of PID 7644).
#
# Self-report artifacts (NOT invented here -- both already exist, already
# written by run.py/app/core/dmn_guardian.py, confirmed by direct source
# read this session):
#   memory/echo_server.pid    -- plain text PID, written once at startup
#                                 (run.py `if __name__ == "__main__":`
#                                 block), unlinked only on a clean SIGTERM/
#                                 SIGINT shutdown (run.py's shutdown_handler)
#                                 -- a crash leaves it stale, a real,
#                                 disclosed possibility this module never
#                                 silently resolves.
#   memory/echo_sentinel.json -- JSON {stage, pid, start_utc,
#                                 last_heartbeat_utc, uptime_s}, written at
#                                 two fixed startup stages (run.py's
#                                 _write_sentinel()) and with its
#                                 last_heartbeat_utc field independently
#                                 refreshed every ~60s by
#                                 app/core/dmn_guardian.py's own guardian
#                                 cycle (confirmed live this session: two
#                                 reads two minutes apart showed the field
#                                 advance by exactly two minutes). Never
#                                 unlinked -- a crashed run's frozen
#                                 last-known state persists until the next
#                                 startup overwrites it.
#
# Same evidentiary discipline as Leaf Primitive 1: pure I/O-gathering
# helpers that can fail only into an explicit None/False -- never an
# exception -- feeding one pure composition function
# (_compose_process_report()) that performs zero I/O, so its decision
# logic (the `correlation` block) is directly unit-testable against
# synthetic evidence.
#
# THE CORE RULE THIS SECTION EXISTS TO ENFORCE, PER THE BOUNDARY REVIEW:
# `external_process` (genuinely independent OS observation) and
# `runtime_self_report` (content the target process wrote about itself)
# are two DIFFERENT evidence kinds and are NEVER merged into one
# undifferentiated object. `correlation` reports only whether the two
# AGREE on specific, named facts (a PID integer, a start-time delta) --
# agreement is evidence that two sources agree, nothing more. No field
# anywhere in this section is named or shaped like `verified`, `active`,
# `live`, `connected`, or `trusted`, and none may ever be added to this
# primitive's output -- that is a boundary, not a style preference.
# ============================================================

_SERVER_PID_FILE_RELPATH = "memory/echo_server.pid"
_SENTINEL_FILE_RELPATH = "memory/echo_sentinel.json"
_SENTINEL_EXPECTED_FIELDS = ("stage", "pid", "start_utc", "last_heartbeat_utc", "uptime_s")

# Tolerance for judging whether an externally-observed OS process creation
# time and the sentinel's self-reported start_utc "agree." Not an arbitrary
# round number: the one real, live gap measured this session between
# psutil's create_time() and run.py's _SENTINEL_START capture (which
# happens after several heavy imports -- faiss, sentence-transformers, etc.
# -- have already run) was ~4.4 seconds. 120s is deliberately generous
# beyond that single sample (covering a much slower cold boot -- CLAUDE.md
# Finding 40 records a real ~35s time-to-serving) while staying far
# tighter than any genuine PID-identity mismatch, which would differ by
# minutes/hours/days, not tens of seconds.
_START_TIME_MATCH_TOLERANCE_SECONDS = 120


# ---------------------------------------------------------------------------
# Evidence gathering -- external process observation. Every failure mode
# (nonexistent PID, access denied, the process vanishing mid-observation --
# a real race, not hypothetical) maps to an explicit None/False per field,
# never an exception.
# ---------------------------------------------------------------------------

def _external_process_observation(pid: int) -> dict:
    """Genuinely independent OS-level observation of `pid`, via psutil --
    zero cooperation required from the target process. Never raises."""
    result = {
        "exists": False,
        "create_time_utc": None,
        "cmdline": None,
        "executable": None,
        "cwd": None,
        "status": None,
        "access_denied": False,
        "error": None,
    }
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return result
    except Exception as exc:
        result["error"] = f"process_lookup_failed:{type(exc).__name__}"
        return result

    result["exists"] = True

    def _create_time_utc():
        return datetime.fromtimestamp(proc.create_time(), tz=timezone.utc).isoformat()

    for field, getter in (
        ("create_time_utc", _create_time_utc),
        ("cmdline", lambda: proc.cmdline() or None),
        ("executable", proc.exe),
        ("cwd", proc.cwd),
        ("status", proc.status),
    ):
        try:
            result[field] = getter()
        except psutil.NoSuchProcess:
            # Vanished mid-observation -- represented honestly: fields
            # already gathered above are kept, `exists` is corrected, and
            # nothing further is attempted.
            result["exists"] = False
            break
        except psutil.AccessDenied:
            result["access_denied"] = True
        except Exception as exc:
            result["error"] = f"{field}_failed:{type(exc).__name__}"

    return result


# ---------------------------------------------------------------------------
# Evidence gathering -- runtime self-report. Reads only the two artifacts
# this project's own live process already writes. Never modifies them,
# never triggers their writers. Only ever reads the fields the real writer
# code (run.py, app/core/dmn_guardian.py) actually produces -- never
# reinterprets an arbitrary extra key that might appear in the file.
# ---------------------------------------------------------------------------

def _read_server_pid_file() -> dict:
    result = {
        "path": _SERVER_PID_FILE_RELPATH,
        "exists": False,
        "readable": False,
        "malformed": False,
        "pid": None,
        "error": None,
    }
    full_path = os.path.join(_PROJECT_ROOT, _SERVER_PID_FILE_RELPATH)
    if not os.path.isfile(full_path):
        return result
    result["exists"] = True

    try:
        content = open(full_path, "r").read().strip()
        result["readable"] = True
    except OSError as exc:
        result["error"] = f"read_failed:{type(exc).__name__}"
        return result

    try:
        result["pid"] = int(content)
    except ValueError:
        result["malformed"] = True
        result["error"] = "non_integer_content"

    return result


def _read_sentinel_file() -> dict:
    result = {
        "path": _SENTINEL_FILE_RELPATH,
        "exists": False,
        "readable": False,
        "malformed": False,
        "stage": None,
        "pid": None,
        "start_utc": None,
        "last_heartbeat_utc": None,
        "uptime_s": None,
        "error": None,
    }
    full_path = os.path.join(_PROJECT_ROOT, _SENTINEL_FILE_RELPATH)
    if not os.path.isfile(full_path):
        return result
    result["exists"] = True

    try:
        raw = open(full_path, "r").read()
        result["readable"] = True
    except OSError as exc:
        result["error"] = f"read_failed:{type(exc).__name__}"
        return result

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        result["malformed"] = True
        result["error"] = "invalid_json"
        return result

    if not isinstance(data, dict):
        result["malformed"] = True
        result["error"] = "not_an_object"
        return result

    for field in _SENTINEL_EXPECTED_FIELDS:
        if field in data:
            result[field] = data[field]
        # else: stays None -- genuinely absent, never fabricated.

    return result


# ---------------------------------------------------------------------------
# Pure composition -- zero I/O. The ONLY place `correlation` is decided,
# from already-gathered evidence alone. A match reports only that two
# sources agree on one specific fact -- never a verdict about module
# loading, import, or execution (see the section-level docstring above).
# ---------------------------------------------------------------------------

def _compose_correlation(
    *,
    queried_pid: int,
    external_create_time_utc: Optional[str],
    server_file_pid: Optional[int],
    sentinel_pid: Optional[int],
    sentinel_start_utc: Optional[str],
) -> dict:
    def _pid_match(candidate: Optional[int]) -> Optional[bool]:
        if candidate is None:
            return None
        return candidate == queried_pid

    start_time_delta_seconds: Optional[float] = None
    start_time_match_sentinel: Optional[bool] = None
    if external_create_time_utc and sentinel_start_utc:
        try:
            t_external = datetime.fromisoformat(external_create_time_utc)
            t_self = datetime.fromisoformat(sentinel_start_utc.rstrip("Z"))
            if t_self.tzinfo is None:
                t_self = t_self.replace(tzinfo=timezone.utc)
            start_time_delta_seconds = abs((t_external - t_self).total_seconds())
            start_time_match_sentinel = start_time_delta_seconds <= _START_TIME_MATCH_TOLERANCE_SECONDS
        except (ValueError, TypeError):
            start_time_delta_seconds = None
            start_time_match_sentinel = None

    return {
        "pid_match_server_file": _pid_match(server_file_pid),
        "pid_match_sentinel": _pid_match(sentinel_pid),
        "start_time_match_sentinel": start_time_match_sentinel,
        "start_time_delta_seconds": start_time_delta_seconds,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def runtime_process_identity_and_self_report(pid) -> dict:
    """
    Two explicitly separate streams of evidence about a process identified
    by `pid`: what an independent OS-level observer can see about it, and
    what this project's own already-existing runtime self-report artifacts
    currently claim about it -- plus a small set of factual agreement
    comparisons between the two. Never modifies anything; never raises.

    Args:
        pid: a positive int. Any other type, or a non-positive value, is
             reported as `in_scope: False` with a machine-readable `error`
             code -- never silently coerced into "process doesn't exist."

    Returns a dict with exactly these top-level keys, always present:
        pid (int)                  -- the caller's own argument, echoed
                                       back verbatim.
        in_scope (bool)            -- False iff the argument was invalid.
                                       All evidence blocks are None in that
                                       case.
        error (str or None)        -- a short machine-readable reason when
                                       in_scope is False; otherwise None.
        external_process (dict or None)
                                    -- see below. None only when in_scope
                                       is False.
        runtime_self_report (dict or None)
                                    -- see below. None only when in_scope
                                       is False.
        correlation (dict or None) -- see below. None only when in_scope
                                       is False.

    `external_process` -- genuinely independent OS-level observation
    (psutil), zero cooperation required from the target process:
        exists (bool)               -- was a process with this PID found.
        create_time_utc (str/None)  -- OS-recorded process creation time.
        cmdline (list[str]/None)    -- OS-recorded argv.
        executable (str/None)       -- OS-recorded interpreter path.
        cwd (str/None)              -- OS-recorded working directory.
        status (str/None)           -- OS-recorded process status
                                        (e.g. "running", "sleeping").
        access_denied (bool)        -- True if one or more fields above
                                        could not be read due to OS
                                        permissions (same-user processes on
                                        this platform are not expected to
                                        hit this, but it is represented
                                        explicitly rather than assumed
                                        impossible).
        error (str/None)            -- a short machine-readable reason for
                                        an unexpected (non-AccessDenied,
                                        non-NoSuchProcess) failure, if any.

    `runtime_self_report` -- the LITERAL current contents of two
    already-existing files this project's own process writes about
    itself. Neither sub-object's content has any independent witness; it
    is exactly what the target process (or a now-dead prior instance of
    it) claimed, at whatever moment each file was last written:
        server_pid_file: {path, exists, readable, malformed, pid, error}
            -- memory/echo_server.pid's literal integer content, if any.
        sentinel_file: {path, exists, readable, malformed, stage, pid,
                          start_utc, last_heartbeat_utc, uptime_s, error}
            -- memory/echo_sentinel.json's literal field values, read only
               for the five keys its real writer code actually produces.
               A crashed prior run's frozen last-known state is
               indistinguishable, by this primitive alone, from a
               currently-live process's state -- see `correlation` and
               the module-level note on shutdown/crash asymmetry above.

    `correlation` -- factual agreement comparisons ONLY, never a verdict:
        pid_match_server_file (bool/None)   -- server_pid_file.pid == pid,
                                                or None if unavailable.
        pid_match_sentinel (bool/None)      -- sentinel_file.pid == pid,
                                                or None if unavailable.
        start_time_match_sentinel (bool/None)
                                             -- whether external_process's
                                                create_time_utc and
                                                sentinel_file's start_utc
                                                are within
                                                _START_TIME_MATCH_TOLERANCE_
                                                SECONDS of each other, or
                                                None if either side is
                                                unavailable or unparseable.
        start_time_delta_seconds (float/None)
                                             -- the raw, disclosed delta
                                                backing the field above.

    What this function CAN establish: whether an OS process with this PID
    currently exists and what the OS itself reports about it; what two
    specific, already-existing self-report files currently claim about a
    process; and whether those two evidence sources agree on a PID integer
    and, approximately, a start time.

    What this function explicitly CANNOT and does NOT establish, and must
    never be interpreted as establishing: whether that process has loaded
    any specific Python module (`sys.modules` inspection is architecturally
    unavailable to an external observer -- confirmed empirically in
    audits/2026-09-11_provenance_leaf_primitives_validation.md, not
    reopened here); whether any function anywhere has been called; or
    whether the process is "correct," "healthy," or "verified" in any
    sense. Agreement between `external_process` and `runtime_self_report`
    means only that two evidence sources currently agree on the specific,
    named fact being compared -- nothing about module loading, import, or
    execution follows from it. See audits/2026-09-12_provenance_layer2_
    boundary_review.md Section 6 for the full reasoning behind this
    boundary, and app/core/self_heal.py (tracked, clean, unmodified vs.
    HEAD, confirmed zero real importers) for why file/process identity
    evidence must never be read as runtime-use evidence.
    """
    try:
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            return {
                "pid": pid,
                "in_scope": False,
                "error": "invalid_pid_argument",
                "external_process": None,
                "runtime_self_report": None,
                "correlation": None,
            }

        external = _external_process_observation(pid)
        server_file = _read_server_pid_file()
        sentinel = _read_sentinel_file()

        correlation = _compose_correlation(
            queried_pid=pid,
            external_create_time_utc=external["create_time_utc"],
            server_file_pid=server_file["pid"],
            sentinel_pid=sentinel["pid"],
            sentinel_start_utc=sentinel["start_utc"],
        )

        return {
            "pid": pid,
            "in_scope": True,
            "error": None,
            "external_process": external,
            "runtime_self_report": {
                "server_pid_file": server_file,
                "sentinel_file": sentinel,
            },
            "correlation": correlation,
        }
    except Exception as exc:  # last-resort safety net -- this function must never raise
        return {
            "pid": pid,
            "in_scope": False,
            "error": f"internal_error:{type(exc).__name__}",
            "external_process": None,
            "runtime_self_report": None,
            "correlation": None,
        }
