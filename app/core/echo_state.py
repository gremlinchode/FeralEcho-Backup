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
# Dimensions:
#   [0] processing_novelty  — how surprising the environment is (0-1)
#   [1] coherence_tension   — internal disagreement across River task types (0-1)
#   [2] orientation_drift   — rate of change in Echo's quality profile (0-1)
#   [3] system_vitality     — inverse RAM pressure (1=healthy, 0=stressed) (0-1)
#   [4] curiosity_index     — recent surprise vs rolling baseline (0-1)
#   [5] friction_rate       — ClaudeShard friction rate last 50 (0-1)
#   [6] edit_momentum       — self-edit success rate (0-1)
#   [7] temporal_phase      — circadian sine signal (0=dawn, 1=dusk) (0-1)
#   [8] valence             — SIGNED [-1, 1]: recent trajectory of
#                             self-edit quality outcomes and independent
#                             (peer-model) council ratings — the only
#                             dimension here with a positive/negative
#                             polarity rather than a pure activity
#                             magnitude. Sourced entirely from signals this
#                             project already treats as externally-anchored
#                             (self_edit_outcomes.jsonl's pre/post deltas,
#                             council_rater.py's peer-model average, and —
#                             added 2026-07-21, closing the gap Finding 35
#                             flagged and never wired — echo_optuna.py's
#                             dry-run trial-vs-production quality deltas),
#                             not Echo's own self-referential quality_score.
#                             Fails closed to 0.0 (neutral) if none of the
#                             three sources is available yet.
#
#                             Why the third source: a live investigation
#                             (2026-07-21) found valence bit-identical
#                             across its entire 100-reading history buffer
#                             — not a bug, but a real consequence of its
#                             first two sources both being rare (a real,
#                             non-dry-run self-edit deploy lands roughly
#                             every 1-2 days; the council-rating average
#                             moves on a similar timescale). On the scale
#                             of a single conversation, valence was
#                             effectively a constant. Optuna's dry-run
#                             trials fire roughly 10x/hour and already
#                             publish a real trial-vs-production quality
#                             comparison to the Global Workspace
#                             (self_edit.dry_run_quality_delta, Phase 7.1)
#                             — reading that gives valence real temporal
#                             resolution on session timescales for the
#                             first time. Deliberately observational only,
#                             same posture as every other valence source:
#                             this dimension already feeds prompts and
#                             emergent_scheduler's pacing, nothing new is
#                             wired to consequence here.
# ============================================================

import json
import logging
import math
import time
from datetime import datetime
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

STATE_DIM = 9
STATE_LABELS = [
    "processing_novelty",
    "coherence_tension",
    "orientation_drift",
    "system_vitality",
    "curiosity_index",
    "friction_rate",
    "edit_momentum",
    "temporal_phase",
    "valence",
]

_STATE_PATH = Path("memory/echo_state.npy")
_HISTORY_PATH = Path("memory/echo_state_history.npy")
_HISTORY_SIZE = 100  # ring buffer — ~3.3h at 2-min cycles
_WORKSPACE_LOG_PATH = Path("memory/workspace_log.jsonl")
_DRY_RUN_QUALITY_RECENT_N = 10  # matches introspection's recent_quality_delta window size


def _recent_dry_run_quality_component() -> "float | None":
    """
    Third valence source (2026-07-21, closes Finding 35's never-wired gap).

    Reads the most recent `self_edit.dry_run_quality_delta` events straight
    from the Global Workspace log — the same real events echo_optuna.py has
    published on every dry-run trial since Phase 7.1, ~10x/hour, previously
    consumed nowhere except self_edit_outcome_tracker.py's per-outcome
    windowed aggregate (which is itself deliberately NOT wired into
    echo_state.py, per that module's own docstring — this reads the raw
    workspace events directly instead, a separate and much simpler path).

    Self-contained rather than importing introspection_channel.py's
    _tail_jsonl(): that module already imports FROM echo_state.py, so the
    reverse import would be circular.

    Each event's detail carries {trial_quality, current_quality}, both a
    0-4 AST-based code-quality score (current_quality is -1 when no
    production code exists yet to compare against — treated as unavailable,
    not as a real zero). delta = trial_quality - current_quality, normalized
    to roughly [-1, 1] by /4.0. Returns the mean of the most recent
    _DRY_RUN_QUALITY_RECENT_N valid deltas, or None if none are found —
    same fail-closed shape as the other two valence sources below.
    """
    try:
        with open(_WORKSPACE_LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            # Generous tail: dry-run events are interleaved with other
            # workspace event types (emergent_loop.salience fires every
            # cycle too), so scanning only the last _DRY_RUN_QUALITY_RECENT_N
            # raw lines would usually find zero. 400 is comfortably more
            # than the real event density observed (~10/hour dry-run vs.
            # several other per-cycle publishers) needs to find the last 10.
            raw_lines = f.readlines()[-400:]
    except Exception:
        return None

    deltas: list = []
    for line in reversed(raw_lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("type") != "self_edit.dry_run_quality_delta":
            continue
        detail = entry.get("detail") or {}
        trial_q = detail.get("trial_quality")
        current_q = detail.get("current_quality")
        if trial_q is None or current_q is None:
            continue
        try:
            trial_q = float(trial_q)
            current_q = float(current_q)
        except (TypeError, ValueError):
            continue
        if current_q < 0:  # -1 sentinel: no production code yet to compare against
            continue
        deltas.append(float(np.clip((trial_q - current_q) / 4.0, -1.0, 1.0)))
        if len(deltas) >= _DRY_RUN_QUALITY_RECENT_N:
            break

    return float(np.mean(deltas)) if deltas else None


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

    # [3] system_vitality — inverse RAM pressure. ram_pressure_pct can now
    # be an explicit None (introspection_channel.py's psutil-failure
    # sentinel, see system_guard.py) rather than merely absent — .get()'s
    # default only applies when the key is missing, so float(None) would
    # otherwise raise here uncaught. Treat unknown the same as the
    # pre-existing missing-key default (neutral 50% pressure).
    ram_pct_raw = sh.get("ram_pressure_pct", 50.0)
    ram_pct = 50.0 if ram_pct_raw is None else float(ram_pct_raw)
    vec[3] = 1.0 - min(ram_pct / 100.0, 1.0)

    # [4] curiosity_index — recent surprise vs rolling baseline
    s_last = float(pl.get("surprise_last", 0.0))
    s_r50 = float(pl.get("surprise_rolling_50", 0.01)) or 0.01
    vec[4] = min(s_last / (s_r50 * 2.0), 1.0)

    # [5] friction_rate — from ClaudeShard (already 0-1)
    vec[5] = min(float(cs.get("friction_rate", 0.0)), 1.0)

    # [6] edit_momentum — self_edit success rate
    vec[6] = min(float(se.get("success_rate", 0.0)), 1.0)

    # [7] temporal_phase — local-time circadian signal (0.0=midnight, 1.0=noon)
    # Phase-shifted by 6h so the peak lands at noon, not dawn.
    now_local = datetime.now()
    hour_frac = now_local.hour + now_local.minute / 60.0
    vec[7] = float((math.sin(2 * math.pi * (hour_frac - 6.0) / 24.0) + 1.0) / 2.0)

    # [8] valence — signed, fail-closed per component. Each source degrades
    # independently to "absent" rather than raising or defaulting to a
    # fake neutral-looking real value; combined score is the mean of
    # whichever sources are actually available, 0.0 if neither is.
    valence_components: list[float] = []
    se_delta = se.get("recent_quality_delta")
    if se_delta is not None:
        valence_components.append(float(np.clip(float(se_delta), -1.0, 1.0)))
    try:
        from app.core.council_rater import get_recent_council_average
        council_avg = get_recent_council_average()
        if council_avg is not None:
            # council_rating is 1-5; recenter on the scale midpoint (3) so
            # 5=+1 (best), 1=-1 (worst), 3=0 (neutral) — same recentering
            # shape used nowhere else in this file yet, first signed source.
            valence_components.append(float(np.clip((float(council_avg) - 3.0) / 2.0, -1.0, 1.0)))
    except Exception:
        pass
    try:
        dry_run_component = _recent_dry_run_quality_component()
        if dry_run_component is not None:
            valence_components.append(dry_run_component)
    except Exception:
        pass
    vec[8] = float(np.mean(valence_components)) if valence_components else 0.0

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
