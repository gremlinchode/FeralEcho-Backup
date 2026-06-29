# app/core/system_guard.py
# ============================================================
# LOAD-AWARE THROTTLE GUARD (C2)
# Reads introspection_state.json and returns True when the
# system is under pressure so callers can skip inference.
# ============================================================

import json
import logging
import os
import time

try:
    import numpy as np
    _NUMPY_OK = True
except ImportError:
    _NUMPY_OK = False

logger = logging.getLogger(__name__)

_INTROSPECTION_PATH = os.path.join("memory", "introspection_state.json")
_CACHE_TTL = 60  # seconds between re-reads

_cache_ts: float = 0.0
_cache_val: bool = False


def should_throttle() -> bool:
    """Return True if system is under load and inference should be skipped.

    Thresholds:
      - RAM pressure > 92 %
      - Memory directory free space < 0.5 GB
      - 1-minute load average > 12.0
    Result is cached for 60 s to avoid disk reads every cycle.
    """
    global _cache_ts, _cache_val
    now = time.time()
    if now - _cache_ts < _CACHE_TTL:
        return _cache_val

    # Fast path: read system_vitality (dim [3]) from echo_state.npy.
    # vitality = 1 - ram_pct/100, so vitality < 0.08 means RAM > 92%.
    if _NUMPY_OK:
        try:
            _sv = os.path.join("memory", "echo_state.npy")
            if os.path.exists(_sv):
                _vec = np.load(_sv)
                if float(_vec[3]) < 0.08:
                    logger.warning("[THROTTLE] system_vitality=%.3f — RAM critical", float(_vec[3]))
                    _cache_val = True
                    _cache_ts = now
                    return _cache_val
        except Exception:
            pass

    try:
        with open(_INTROSPECTION_PATH, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        health = state.get("system_health", {})
        ram_pct = float(health.get("ram_pressure_pct", 0))
        free_gb = float(health.get("memory_dir_free_gb", 99))
        load_1m = float(health.get("load_avg_1m", 0))
        throttle = ram_pct > 92 or free_gb < 0.5 or load_1m > 12.0
        if throttle:
            logger.warning(
                "[THROTTLE] System under pressure: RAM=%.1f%% free=%.2fGB load=%.1f",
                ram_pct, free_gb, load_1m,
            )
        _cache_val = throttle
    except Exception as e:
        logger.debug("[THROTTLE] Could not read introspection state: %s", e)
        _cache_val = False

    _cache_ts = now
    return _cache_val
