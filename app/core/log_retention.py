"""
app/core/log_retention.py — "a metabolism," not unbounded growth.

Confirmed live during the 2026-07-20/21 differential audit (see
audits/2026-07-20_differential_audit.md, CLAUDE.md Finding 41 D /
PENDING_DECISIONS.md #8): memory/*.log and memory/*.jsonl files have no
autonomous retention policy at all. echo_janitor.py (root) was built to
solve a different problem — stale/duplicate *scripts* in the project root
and files under logs/ — and never touches memory/, so it can't be "fixed
and wired in" to close this gap; it's the wrong tool. This module is a
small, purpose-built one instead.

Design constraint verified before writing this, not assumed: both
Python's open(path, "a") and the shell's `tee -a` (what start_echo.sh
pipes run.py's stdout/stderr into, for memory/echo_watchdog.log) are
O_APPEND writers — every write() syscall re-resolves to current
end-of-file at write time, not a cached offset. That means
compress-then-truncate is safe for every target file, including the one
whose writer isn't Python at all, without needing two different rotation
strategies. Residual, stated risk: a write landing in the narrow window
between "read for compression" and "truncate" could be lost — same class
of accepted risk as CLAUDE.md Finding 34's .tmp-rename race, worst case
one dropped log line, never corruption.
"""

import gzip
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def archive_if_due(sources: "list[tuple[str, str]]", dest_dir: "str | Path",
                    interval_hours: float, max_snapshots: int) -> bool:
    """Periodic-archive helper — added 2026-07-23 (CLAUDE.md Finding 75/
    physiology audit): confirmed no historical snapshot of
    memory/echo_state_history.npy exists anywhere, so a real correlation-
    structure shift found that session (temporal_phase<->valence:
    r=+0.83 on 2026-07-18 -> r=-0.93 measured fresh) couldn't be checked
    against real history — there was none, because the file is a fixed
    100-row ring buffer (~3.3h horizon) that silently overwrites. This
    doesn't fix that specific mystery retroactively (impossible); it
    prevents the same blind spot recurring for future questions like it.

    For each (src_path, glob_pattern) in sources: if the real src file
    exists and the newest existing archive matching glob_pattern in
    dest_dir is older than interval_hours (or none exists), copies a
    timestamped snapshot and prunes that pattern's archives down to
    max_snapshots. A failure on one source never blocks the others.
    Never raises. Returns True if anything was actually archived this call
    — parameterized (not hardcoded to the real echo-state paths/interval)
    specifically so a liveness check can exercise this real function
    against synthetic data, same reasoning as self_edit_manager.py's
    _prune_self_edit_plans() gaining optional params for the identical
    purpose (CLAUDE.md Finding 58).
    """
    archived_any = False
    dest_dir = Path(dest_dir)
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.warning(f"[ECHO-STATE-ARCHIVE] Could not create {dest_dir}: {e}")
        return False

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for src_path, glob_pattern in sources:
        try:
            src = Path(src_path)
            if not src.exists():
                continue
            existing = sorted(dest_dir.glob(glob_pattern))
            needs_archive = True
            if existing:
                age_hours = (
                    datetime.now(timezone.utc).timestamp() - existing[-1].stat().st_mtime
                ) / 3600
                needs_archive = age_hours >= interval_hours
            if not needs_archive:
                continue

            prefix = glob_pattern.split("*")[0]
            dest = dest_dir / f"{prefix}{stamp}{src.suffix}"
            shutil.copy2(src, dest)
            archived_any = True
            logging.info(f"[ECHO-STATE-ARCHIVE] Archived {src.name} -> {dest.name}")

            all_snaps = sorted(dest_dir.glob(glob_pattern))
            for old in all_snaps[:-max_snapshots]:
                try:
                    old.unlink()
                    logging.info(f"[ECHO-STATE-ARCHIVE] Pruned old snapshot {old.name}")
                except Exception:
                    pass
        except Exception as e:
            logging.warning(f"[ECHO-STATE-ARCHIVE] Archive failed for {src_path}: {e}")
            continue
    return archived_any


def rotate_if_oversized(path: "str | Path", max_bytes: int) -> bool:
    """
    No-op if the file doesn't exist or is under max_bytes. Otherwise:
    gzip the current content to <path>.1.gz (overwriting any prior
    generation — one generation of history kept, not an ever-growing
    archive directory that just recreates this same problem one level
    up), then truncate the live file to empty. Never raises; logs and
    returns False on any failure so a bad file never blocks the rest of
    a rotation pass.
    """
    path = Path(path)
    try:
        if not path.exists():
            return False
        size = path.stat().st_size
        if size <= max_bytes:
            return False

        data = path.read_bytes()
        archive_path = path.with_name(path.name + ".1.gz")
        with gzip.open(archive_path, "wb") as gz:
            gz.write(data)

        os.truncate(path, 0)
        logging.info(
            f"[LOG-RETENTION] Rotated {path} ({size} bytes -> {archive_path.name}, "
            f"live file truncated)"
        )
        return True
    except Exception as e:
        logging.warning(f"[LOG-RETENTION] Rotation failed for {path}: {e}")
        return False
