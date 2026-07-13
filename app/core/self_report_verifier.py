"""
Self-report verifier — a second data point for the pattern
self_edit_outcome_tracker.py already proved out for self-edits.

Independently recomputes ground truth for claims Echo's own self_model.json
makes about itself, and logs a mismatch if reality disagrees. Log-only —
does NOT correct self_model.json, does NOT feed any decision path. Wiring
this into something consequential is a separate, explicit decision, same
principle self_edit_outcome_tracker.py's own docstring already states.

Motivating case: memory_health.journal_line_count in self_model.json was
found to be wrong (claimed 0, real count in the thousands) because
introspection_channel.py was reading the wrong journal file — now fixed
there directly. This module exists so a future instance of the same shape
of bug (a self-report claim silently drifting from reality) gets caught
on an ongoing basis instead of requiring another manual audit to find.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SELF_MODEL_PATH = Path("memory/self_model.json")
_VERIFICATION_LOG = Path("memory/self_report_verification.log")


def _load_self_model() -> dict:
    try:
        with open(_SELF_MODEL_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.debug(f"[SelfReportVerifier] failed to read self_model.json: {e}")
        return {}


def _real_faiss_vector_count() -> "int | None":
    try:
        from app.core.memory_bridge import vector_memory
        idx = getattr(vector_memory, "index", None)
        return int(idx.ntotal) if idx is not None else None
    except Exception as e:
        logger.debug(f"[SelfReportVerifier] failed to read live FAISS index: {e}")
        return None


def _real_journal_line_count() -> "int | None":
    try:
        from app.core import config
        journal_file = Path(config.MEMORY_JOURNAL_FILE)
    except Exception:
        journal_file = Path("memory/memory_journal.log")
    try:
        if not journal_file.exists():
            return None
        with open(journal_file, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except Exception as e:
        logger.debug(f"[SelfReportVerifier] failed to count {journal_file}: {e}")
        return None


def verify_memory_health(journal_tolerance: int = 5, faiss_tolerance_pct: float = 0.05) -> "dict | None":
    """
    Compare self_model.json's memory_health claim against a fresh,
    independent recomputation from source (not a re-read of the same
    cached introspection_state.json the original claim came from).

    faiss_vector_count and journal_line_count have very different natural
    growth rates (confirmed live: FAISS can grow by hundreds of vectors in
    the few minutes between self_model_updater refresh cycles, from the
    autonomous loops constantly writing memory, while journal growth tracks
    much slower real journaling activity) — a single flat tolerance fires
    constantly on FAISS's expected drift while being appropriately strict
    for the journal. faiss uses a relative (%) tolerance for this reason;
    journal keeps an absolute one, since any real gap there likely means a
    genuine bug (the original one being read here from a wrong file) rather
    than benign lag.

    Returns the mismatch dict and logs it if any field diverges beyond
    tolerance; returns None (no-op) if everything matches.
    """
    model = _load_self_model()
    claimed = model.get("memory_health", {})
    if not claimed:
        return None

    real_faiss = _real_faiss_vector_count()
    real_journal = _real_journal_line_count()

    mismatches = {}

    claimed_faiss = claimed.get("faiss_vector_count")
    if real_faiss is not None and isinstance(claimed_faiss, (int, float)):
        delta = real_faiss - int(claimed_faiss)
        threshold = max(50, abs(int(claimed_faiss)) * faiss_tolerance_pct)
        if abs(delta) > threshold:
            mismatches["faiss_vector_count"] = {
                "claimed": claimed_faiss, "actual": real_faiss, "delta": delta,
            }

    claimed_journal = claimed.get("journal_line_count")
    if real_journal is not None and isinstance(claimed_journal, (int, float)):
        delta = real_journal - int(claimed_journal)
        if abs(delta) > journal_tolerance:
            mismatches["journal_line_count"] = {
                "claimed": claimed_journal, "actual": real_journal, "delta": delta,
            }

    if not mismatches:
        return None

    entry = {
        "ts": model.get("last_updated"),
        "mismatches": mismatches,
    }
    try:
        _VERIFICATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_VERIFICATION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.debug(f"[SelfReportVerifier] failed to write verification log: {e}")

    logger.warning(f"[SelfReportVerifier] self_model.json memory_health mismatch: {mismatches}")
    return entry
