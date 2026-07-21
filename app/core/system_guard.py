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
_cache_level: str = "none"


# "severe" thresholds — unchanged from should_throttle()'s original values,
# still what should_throttle() itself (and every existing caller of it)
# uses. "moderate" is a new, more permissive tier: a caller doing cheap,
# local, non-inference work (audit finding: "one RAM spike silences the
# entire autonomy stack simultaneously... network-heavy council
# deliberation and cheap local journal trims alike") can opt into
# throttle_level()/should_run_cycle(tier="light") to keep running through
# moderate pressure that already stops heavy inference work, instead of
# every loop sharing one identical threshold regardless of cost.
_SEVERE_RAM_PCT = 92.0
_SEVERE_FREE_GB = 0.5
_SEVERE_LOAD_1M = 12.0
_MODERATE_RAM_PCT = 80.0
_MODERATE_FREE_GB = 1.5
_MODERATE_LOAD_1M = 8.0


def throttle_level() -> str:
    """Returns "none", "moderate", or "severe" — see threshold constants
    above. Cached for 60s alongside should_throttle(), same read."""
    global _cache_ts, _cache_val, _cache_level
    now = time.time()
    if now - _cache_ts < _CACHE_TTL:
        return _cache_level

    if _NUMPY_OK:
        try:
            _sv = os.path.join("memory", "echo_state.npy")
            if os.path.exists(_sv):
                _vec = np.load(_sv)
                if float(_vec[3]) < 0.08:
                    logger.warning("[THROTTLE] system_vitality=%.3f — RAM critical", float(_vec[3]))
                    _cache_val, _cache_level, _cache_ts = True, "severe", now
                    return _cache_level
        except Exception:
            pass

    try:
        with open(_INTROSPECTION_PATH, "r", encoding="utf-8") as fh:
            state = json.load(fh)
        health = state.get("system_health", {})
        ram_pct_raw = health.get("ram_pressure_pct", 0)
        if ram_pct_raw is None:
            # introspection_channel.py writes an explicit None here only
            # when its psutil collection failed outright — a genuinely
            # unknown reading, not a healthy 0%. Fail closed rather than
            # silently treating "unknown" the same as "idle."
            logger.warning("[THROTTLE] system_health RAM reading unknown — failing closed")
            _cache_val, _cache_level, _cache_ts = True, "severe", now
            return _cache_level
        ram_pct = float(ram_pct_raw)
        free_gb = float(health.get("memory_dir_free_gb", 99))
        load_1m = float(health.get("load_avg_1m", 0))

        if ram_pct > _SEVERE_RAM_PCT or free_gb < _SEVERE_FREE_GB or load_1m > _SEVERE_LOAD_1M:
            level = "severe"
        elif ram_pct > _MODERATE_RAM_PCT or free_gb < _MODERATE_FREE_GB or load_1m > _MODERATE_LOAD_1M:
            level = "moderate"
        else:
            level = "none"

        if level != "none":
            # Found 2026-07-21: this line used to print all three raw
            # readings unlabeled ("RAM=84.1% free=781.60GB load=1.9") with
            # no indication of which metric(s) actually crossed a
            # threshold — free_gb is disk free space for memory/
            # (memory_dir_free_gb), not RAM, but sitting right next to a
            # RAM percentage it reads like 781GB of free RAM, and a reader
            # has to know the threshold constants by heart to tell which
            # reading(s) triggered the alert. Now names the metric that
            # actually crossed a threshold explicitly, and clarifies
            # free_gb's real meaning in the full-readings tail.
            ram_thresh = _SEVERE_RAM_PCT if level == "severe" else _MODERATE_RAM_PCT
            free_thresh = _SEVERE_FREE_GB if level == "severe" else _MODERATE_FREE_GB
            load_thresh = _SEVERE_LOAD_1M if level == "severe" else _MODERATE_LOAD_1M
            triggers = []
            if ram_pct > ram_thresh:
                triggers.append(f"RAM={ram_pct:.1f}% (>{ram_thresh:.0f}%)")
            if free_gb < free_thresh:
                triggers.append(f"disk_free={free_gb:.2f}GB (<{free_thresh:.1f}GB)")
            if load_1m > load_thresh:
                triggers.append(f"load={load_1m:.1f} (>{load_thresh:.1f})")
            logger.warning(
                "[THROTTLE] System under %s pressure: %s "
                "(full readings: RAM=%.1f%% disk_free=%.2fGB load=%.1f)",
                level, ", ".join(triggers) or "unknown metric", ram_pct, free_gb, load_1m,
            )
        _cache_val = level == "severe"
        _cache_level = level
    except Exception as e:
        logger.debug("[THROTTLE] Could not read introspection state: %s", e)
        _cache_val, _cache_level = False, "none"

    _cache_ts = now
    return _cache_level


def should_throttle() -> bool:
    """Return True if system is under severe load and inference should be
    skipped. Unchanged thresholds/behavior from before throttle_level()
    existed — this is now a thin wrapper so existing callers (and their
    exact pass/fail thresholds) are completely unaffected.

    Thresholds:
      - RAM pressure > 92 %
      - Memory directory free space < 0.5 GB
      - 1-minute load average > 12.0
    Result is cached for 60 s to avoid disk reads every cycle.
    """
    return throttle_level() == "severe"
