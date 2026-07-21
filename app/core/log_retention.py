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
from pathlib import Path


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
