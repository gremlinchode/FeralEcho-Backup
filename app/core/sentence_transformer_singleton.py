# app/core/sentence_transformer_singleton.py
# ============================================================
# Shared SentenceTransformer singleton.
# Previously, memory_bridge.py, reflection_shard.py, and
# dual_learning.py each called SentenceTransformer() independently
# at import time — each load makes ~15 HTTP calls and takes 15-30s.
# All three now share this one instance, cutting startup from ~90s.
# ============================================================
from threading import Lock
import logging

_lock = Lock()
_model = None

logger = logging.getLogger(__name__)


def get_sentence_transformer(model_name: str = "all-MiniLM-L6-v2"):
    """Return (and lazily initialize) the shared SentenceTransformer instance."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                logger.info("[ST_SINGLETON] Loading SentenceTransformer('%s') …", model_name)
                _model = SentenceTransformer(model_name)
                logger.info("[ST_SINGLETON] Model ready.")
    return _model
