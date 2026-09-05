"""
State-change instrumentation (Phase 7).

Per the mission's own explicit caution: a state change by itself is NOT
evidence of learning, and a memory write followed by behavior is not
automatically learning either. This module exists ONLY to make the real
state change (if any) directly observable and recorded in the evidence
ledger -- the causal question ("did experience cause a persistent state
change that subsequently caused behavior that would not otherwise have
occurred") is answered by the analysis layer (Phase 10/final report)
cross-referencing these hashes against the actual behavioral verdicts in
scoring.py, never by this module itself.

All functions here are read-only observers of REAL state -- they do not
create, fake, or simulate any state change themselves (Condition C/D's
own harness.py functions are what actually cause a real change, via the
real add_to_vector_memory()/retrieve_relevant_memories() calls).
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional


def hash_faiss_state() -> Optional[dict]:
    """A real, cheap fingerprint of the current on-disk FAISS state:
    file size + mtime of memory/memory_meta.json and memory/faiss.index,
    plus (if importable) the real live in-process vector count. Returns
    None if the files don't exist in this environment (e.g. a test
    sandbox) -- callers must handle None, not assume a value."""
    try:
        from app.core import config
        meta_path = os.path.join(config.MEMORY_DIR, "memory_meta.json")
        index_path = os.path.join(config.MEMORY_DIR, "faiss.index")
    except Exception:
        return None
    if not os.path.exists(meta_path):
        return None
    result = {
        "meta_size": os.path.getsize(meta_path),
        "meta_mtime": os.path.getmtime(meta_path),
    }
    if os.path.exists(index_path):
        result["index_size"] = os.path.getsize(index_path)
        result["index_mtime"] = os.path.getmtime(index_path)
    try:
        from app.core.memory_bridge import vector_memory
        result["live_ntotal"] = int(vector_memory.index.ntotal)
    except Exception:
        result["live_ntotal"] = None
    combined = f"{result.get('meta_size')}|{result.get('meta_mtime')}|{result.get('index_size')}|{result.get('live_ntotal')}"
    result["hash"] = hashlib.sha256(combined.encode()).hexdigest()[:16]
    return result


def hash_riverbrain_state() -> Optional[dict]:
    """A real, cheap fingerprint of memory/river_brain.pkl's on-disk
    state (size + mtime) -- deliberately does NOT unpickle the file for
    every trial (expensive, and this experiment's design, per the
    architecture audit, never uses a path that trains RiverBrain at
    all -- EchoDirectResponder is Design B, confirmed to bypass
    RiverBrain entirely). This hash exists as a NEGATIVE-CONTROL
    instrument: if it ever changes across a trial in this experiment,
    that would itself be a surprising, worth-investigating finding
    (evidence the responder path is not as clean as the architecture
    audit concluded), not an expected experimental variable."""
    try:
        from app.core import config
        path = os.path.join(config.MEMORY_DIR, "river_brain.pkl")
    except Exception:
        return None
    if not os.path.exists(path):
        return None
    result = {"size": os.path.getsize(path), "mtime": os.path.getmtime(path)}
    result["hash"] = hashlib.sha256(f"{result['size']}|{result['mtime']}".encode()).hexdigest()[:16]
    return result


def capture_state_snapshot() -> dict:
    """The one function callers should use: returns both hashes as a
    single dict, ready to drop into a LearningTrial's *_state_hash_before/
    after fields."""
    return {
        "memory_state": hash_faiss_state(),
        "riverbrain_state": hash_riverbrain_state(),
    }
