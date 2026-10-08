"""Exclusive-create evidence storage under an explicitly supplied local root."""
import os
from pathlib import Path
import re

from .contracts import canonical, digest_bytes


def write_event(root: Path, event_id: str, event: dict) -> str:
    """Root must be a new, caller-approved research directory; not a sandbox.

    O_NOFOLLOW protects the event leaf. OS confinement of future callers remains
    a separate requirement. Never infer permission from a path supplied by a
    candidate/proposer. Existing bytes are never overwritten.
    """
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", event_id):
        raise ValueError("invalid event id")
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("expected existing non-symlink research root")
    payload = canonical(event) + b"\n"
    if len(payload) > 262144:
        raise ValueError("event exceeds journal bound")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(root / (event_id + ".json"), flags, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    return digest_bytes(payload)
