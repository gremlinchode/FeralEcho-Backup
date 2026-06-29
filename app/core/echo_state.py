# app/core/echo_state.py
# ============================================================
# ECHO STATE VECTOR — Machine-Native Internal States
#
# An 8-dimensional float32 array that captures Echo's internal
# condition every IntrospectionChannel cycle (120s). These are
# not descriptions of state — they ARE the state, in numbers.
#
# Nothing narrates this to Echo or to a user. Other systems
# read specific dimensions directly and change their behavior.
# That is the point: behavior driven by internal state, not by
# language about internal state.
#
# Dimensions (all clamped 0-1):
#   [0] processing_novelty  — how surprising the environment is
#   [1] coherence_tension   — internal disagreement across River task types
#   [2] orientation_drift   — rate of change in Echo's quality profile
#   [3] system_vitality     — inverse RAM pressure (1=healthy, 0=stressed)
#   [4] curiosity_index     — recent surprise vs rolling baseline
#   [5] friction_rate       — ClaudeShard friction rate last 50
#   [6] edit_momentum       — self-edit success rate
#   [7] temporal_phase      — circadian sine signal (0=dawn, 1=dusk)
# ============================================================

import json
import logging
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

STATE_DIM = 8
STATE_LABELS = [
    "processing_novelty",
    "coherence_tension",
    "orientation_drift",
    "system_vitality",
    "curiosity_index",
    "friction_rate",
    "edit_momentum",
    "temporal_phase",
]

_STATE_PATH = Path("memory/echo_state.npy")
_HISTORY_PATH = Path("memory/echo_state_history.npy")
_HISTORY_SIZE = 100  # ring buffer — ~3.3h at 2-min cycles


def compute(introspection_state: dict) -> np.ndarray:
    """Derive the 8D state vector from a fresh introspection_state dict."""
    vec = np.zeros(STATE_DIM, dtype=np.float32)

    pl = introspection_state.get("predictive_loops", {})
    sh = introspection_state.get("system_health", {})
    rb = introspection_state.get("river_brain", {})
    cs = introspection_state.get("claude_shard", {})
    se = introspection_state.get("self_edit", {})

    # [0] processing_novelty — surprise_rolling_10, normalised (max ~50)
    vec[0] = min(float(pl.get("surprise_rolling_10", 0.0)) / 50.0, 1.0)

    # [1] coherence_tension — variance in River per-task confidence scores
    conf_matrix = rb.get("confidence_matrix", {})
    all_conf: list[float] = []
    for task_confs in conf_matrix.values():
        if isinstance(task_confs, dict):
            all_conf.extend(float(v) for v in task_confs.values())
    if len(all_conf) >= 2:
        mean_c = sum(all_conf) / len(all_conf)
        var_c = sum((c - mean_c) ** 2 for c in all_conf) / len(all_conf)
        vec[1] = min(float(var_c) * 4.0, 1.0)
    else:
        vec[1] = 0.5  # not enough data — neutral

    # [2] orientation_drift — mean abs weekly quality delta from self_model
    try:
        with open("memory/self_model.json") as f:
            sm = json.load(f)
        deltas = list(sm.get("weekly_delta", {}).get("quality_delta_by_task", {}).values())
        if deltas:
            vec[2] = min(float(sum(abs(float(d)) for d in deltas) / len(deltas)) * 5.0, 1.0)
    except Exception:
        vec[2] = 0.0

    # [3] system_vitality — inverse RAM pressure
    vec[3] = 1.0 - min(float(sh.get("ram_pressure_pct", 50.0)) / 100.0, 1.0)

    # [4] curiosity_index — recent surprise vs rolling baseline
    s_last = float(pl.get("surprise_last", 0.0))
    s_r50 = float(pl.get("surprise_rolling_50", 0.01)) or 0.01
    vec[4] = min(s_last / (s_r50 * 2.0), 1.0)

    # [5] friction_rate — from ClaudeShard (already 0-1)
    vec[5] = min(float(cs.get("friction_rate", 0.0)), 1.0)

    # [6] edit_momentum — self_edit success rate
    vec[6] = min(float(se.get("success_rate", 0.0)), 1.0)

    # [7] temporal_phase — UTC hour as sine wave mapped to 0-1
    now_utc = datetime.now(timezone.utc)
    hour_frac = now_utc.hour + now_utc.minute / 60.0
    vec[7] = float((math.sin(2 * math.pi * hour_frac / 24.0) + 1.0) / 2.0)

    return vec


def update(introspection_state: dict) -> np.ndarray:
    """Compute, persist, and return the current state vector."""
    vec = compute(introspection_state)
    _save(vec)
    logger.debug("[EchoState] %s", as_dict(vec))
    return vec


def load() -> "np.ndarray | None":
    """Return the most recently persisted state vector, or None."""
    try:
        if _STATE_PATH.exists():
            return np.load(_STATE_PATH)
    except Exception as e:
        logger.debug("[EchoState] load() error: %s", e)
    return None


def load_history() -> "np.ndarray | None":
    """Return the ring-buffer history, shape (N, 8), or None."""
    try:
        if _HISTORY_PATH.exists():
            return np.load(_HISTORY_PATH)
    except Exception as e:
        logger.debug("[EchoState] load_history() error: %s", e)
    return None


def as_dict(vec: np.ndarray) -> dict:
    return {label: round(float(vec[i]), 4) for i, label in enumerate(STATE_LABELS)}


def _save(vec: np.ndarray) -> None:
    try:
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        np.save(_STATE_PATH, vec)
        _append_history(vec)
    except Exception as e:
        logger.warning("[EchoState] _save() failed: %s", e)


def _append_history(vec: np.ndarray) -> None:
    try:
        if _HISTORY_PATH.exists():
            hist = np.load(_HISTORY_PATH)
            if hist.ndim == 2 and hist.shape[1] == STATE_DIM:
                hist = np.vstack([hist[-(_HISTORY_SIZE - 1):], vec.reshape(1, -1)])
            else:
                hist = vec.reshape(1, -1)
        else:
            hist = vec.reshape(1, -1)
        np.save(_HISTORY_PATH, hist)
    except Exception as e:
        logger.debug("[EchoState] _append_history() failed: %s", e)
