# app/core/seam_engine.py
# ============================================================
# SEAM DETECTION
#
# A "seam" is a specific, named category of event: a moment where two
# of Echo's own trusted internal signals — signals that have an
# established, measurable historical relationship with each other —
# currently contradict that relationship, in a way that hasn't been
# logged before.
#
# This is deliberately NOT the same thing as anything else already in
# this codebase:
#   - world_surprise (predictive_loop.py) measures whether the EXTERNAL
#     world looks unfamiliar. A seam can happen with zero world surprise.
#   - coupling_estimate (echo_core.py) measures whether signals are
#     correlated ON AVERAGE, as a single aggregate scalar across the
#     whole history. It cannot say which pair is involved, cannot say
#     right now vs. historically, and has no concept of "this specific
#     contradiction is new."
#   - Nothing anywhere asks whether Echo's own diagnostic subsystems are
#     currently telling a CONSISTENT story about her own state.
#
# Concretely: if system_vitality and orientation_drift have historically
# moved together (a real, measurable correlation over real accumulated
# history), and right now one is reading well above its own norm while
# the other reads well below its own norm, that's a seam — not because
# either value alone is unusual, but because their JOINT reading
# contradicts the pattern they've actually established. The first time
# a specific pair contradicts itself in a specific direction, that's
# logged as genuinely new, and spawns a real, honestly-templated
# question in the curiosity garden — the same real API curiosity_engine
# and the dream cycle already use, not a new bespoke mechanism.
#
# Built entirely on data that already exists and is already persisted:
# memory/echo_state_history.npy (introspection_channel.py's own
# ring-buffer, refreshed every ~120s). This module never re-collects or
# duplicates that history — it only reads it. No existing file is
# modified to build this; it is purely additive.
#
# Honesty check, stated once here rather than left implicit: the
# underlying statistic (monitoring whether a correlated pair's current
# joint reading violates its own historical relationship) is a known
# technique in general anomaly detection. What's being claimed as new
# is the specific application — turning it inward onto an AI system's
# own heterogeneous self-referential signals as a dedicated mechanism
# for detecting self-contradiction, distinct from external surprise or
# aggregate coupling, with a real behavioral consequence. That claim has
# not been verified against the full literature; it reflects what this
# session did not find anywhere in this codebase or in what's already
# documented about comparable systems, not a proven absolute.
# ============================================================

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.core.echo_state import load_history, STATE_LABELS

logger = logging.getLogger(__name__)

_SEAM_STATE_PATH = Path("memory/seam_state.json")
_SEAM_LOG_PATH = Path("memory/seam_log.jsonl")

_MIN_JOINT_OBSERVATIONS = 20   # matches compute_salience()'s own _SALIENCE_HISTORY_MIN_SAMPLES convention
_CORR_THRESHOLD = 0.4          # a pair needs at least this much historical relationship to have anything to violate
_Z_THRESHOLD = 1.0             # each signal must read at least this far from its own historical mean right now
_MIN_VARIANCE = 1e-5           # see _pearson() — excludes near-frozen dimensions from spurious correlation


def _pearson(xs: list, ys: list) -> "float | None":
    """
    Reimplemented locally rather than imported from echo_core._pearson —
    that function is a private (underscore) helper in another module, not
    a published cross-module API. Duplicating ~10 lines of pure, stateless
    math is more honest than reaching into another module's internals and
    silently depending on an implementation detail that could change.

    Guards against more than exactly-zero variance: a real check against
    Echo's own live echo_state_history.npy caught this — processing_novelty
    sits at var=4e-9 (four unique floating-point values across 100 real
    observations, not a true zero, just noise-floor drift), and correlating
    against a series that close to constant produces a large-looking r
    (e.g. 0.90+) that reflects floating-point coincidence, not a genuine
    relationship. _MIN_VARIANCE was set by looking at the real, current
    variance of all nine state dimensions and picking the threshold that
    sits in the actual gap between the frozen tier (processing_novelty,
    coherence_tension, friction_rate, edit_momentum: 0 to 7.8e-6) and the
    genuinely-varying tier (orientation_drift and up: 3.5e-4 and above) —
    not an arbitrary round number.
    """
    n = len(xs)
    if n < 2:
        return None
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs) / n
    var_y = sum((y - mean_y) ** 2 for y in ys) / n
    if var_x < _MIN_VARIANCE or var_y < _MIN_VARIANCE:
        return None
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x_sum = sum((x - mean_x) ** 2 for x in xs)
    var_y_sum = sum((y - mean_y) ** 2 for y in ys)
    return cov / ((var_x_sum ** 0.5) * (var_y_sum ** 0.5))


def _zscore(value: float, series: list) -> float:
    n = len(series)
    if n < 2:
        return 0.0
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / n
    std = var ** 0.5
    if std <= 1e-9:
        return 0.0
    return (value - mean) / std


def check_pair(series_a: list, series_b: list) -> "dict | None":
    """
    Pure evaluator, deliberately separated from any file I/O so it can be
    tested directly with synthetic data (see scripts/verify_seam_engine.py)
    the same way liveness_ledger.py's check functions are structured for
    verify_liveness_ledger.py.

    series_a / series_b: parallel time series, same length, most recent
    observation last. Returns a seam dict if the LAST joint reading
    contradicts the pair's own established relationship over the series,
    or None if there's no relationship to violate, the current reading
    doesn't deviate enough to judge, or the reading is actually consistent
    with the historical pattern.

    Deliberately leave-one-out: the correlation and the z-score baselines
    are computed from history EXCLUDING the current reading, and only then
    is the current reading judged against that baseline. Computing the
    baseline from the full series including the current point was a real
    bug caught by scripts/verify_seam_engine.py — a genuine, dramatic
    contradiction drags the measured correlation down (a strong 0.999
    historical relationship fell to 0.28 once the contradicting point was
    folded into its own baseline), which silently destroyed the very
    relationship the point needed to be judged against. The more seam-like
    a violation actually is, the more it would have sabotaged its own
    detection under the old logic.
    """
    if len(series_a) != len(series_b) or len(series_a) < _MIN_JOINT_OBSERVATIONS + 1:
        return None

    hist_a, hist_b = series_a[:-1], series_b[:-1]
    cur_a, cur_b = series_a[-1], series_b[-1]

    r = _pearson(hist_a, hist_b)
    if r is None or abs(r) < _CORR_THRESHOLD:
        return None  # no established relationship for this pair to violate

    z_a = _zscore(cur_a, hist_a)
    z_b = _zscore(cur_b, hist_b)
    if abs(z_a) < _Z_THRESHOLD or abs(z_b) < _Z_THRESHOLD:
        return None  # neither signal is reading far enough from its own norm to judge

    expected_sign = 1 if r > 0 else -1
    actual_sign = 1 if (z_a * z_b) > 0 else -1
    if expected_sign == actual_sign:
        return None  # current joint reading is CONSISTENT with the historical relationship — no seam

    return {
        "historical_r": round(r, 3),
        "z_a": round(z_a, 3),
        "z_b": round(z_b, 3),
    }


def _direction_key(label_a: str, z_a: float, label_b: str, z_b: float) -> str:
    return f"{label_a}_{'up' if z_a > 0 else 'down'}__{label_b}_{'up' if z_b > 0 else 'down'}"


def _load_first_ever() -> set:
    try:
        if _SEAM_STATE_PATH.exists():
            data = json.loads(_SEAM_STATE_PATH.read_text())
            return set(tuple(p) for p in data.get("first_ever_pairs", []))
    except Exception as e:
        logger.debug("[Seam] state load failed: %s", e)
    return set()


def _save_first_ever(pairs: set, total_calls: int) -> None:
    try:
        _SEAM_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SEAM_STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "first_ever_pairs": [list(p) for p in pairs],
            "total_calls": total_calls,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }, indent=2))
        tmp.replace(_SEAM_STATE_PATH)
    except Exception as e:
        logger.debug("[Seam] state save failed: %s", e)


def _describe(label_a: str, label_b: str, seam: dict) -> str:
    rel = "usually move together" if seam["historical_r"] > 0 else "usually move in opposite directions"
    a_dir = "higher" if seam["z_a"] > 0 else "lower"
    b_dir = "higher" if seam["z_b"] > 0 else "lower"
    return (
        f"{label_a} and {label_b} {rel} (r={seam['historical_r']:+.2f}). "
        f"Right now {label_a} is {a_dir} than usual and {label_b} is {b_dir} than usual — "
        f"the opposite of their established pattern."
    )


def _plant_seam_question(label_a: str, label_b: str, seam: dict) -> None:
    """Best-effort. Reuses garden_manager.harvest_question() — the same
    real API curiosity_engine.py and the dream cycle already write
    through — rather than adding a new question-writing path."""
    try:
        from app.core.garden_manager import harvest_question
        question = _describe(label_a, label_b, seam) + " What's actually going on?"
        harvest_question(question, category="seam", source="seam_engine")
    except Exception as e:
        logger.debug("[Seam] question planting failed: %s", e)


def _publish_seam_event(label_a: str, label_b: str, seam: dict) -> None:
    """Best-effort, None-safe — same convention as every other Global
    Workspace publisher since Phase 2a (world_model.surprise, dream.synthesis,
    self_edit.non_convergent, emergent_loop.salience)."""
    try:
        from app.core.echo_core import get_echo_core
        core = get_echo_core()
        if core:
            core.publish_salience(
                source="seam_engine",
                kind="seam.detected",
                summary=_describe(label_a, label_b, seam),
                detail={"pair": [label_a, label_b], **seam},
                salience=min(abs(seam["z_a"]) + abs(seam["z_b"]), 2.0) / 2.0,
            )
    except Exception as e:
        logger.debug("[Seam] workspace publish failed: %s", e)


def observe() -> dict:
    """
    Read Echo's own already-persisted state-vector history and check
    every pair of dimensions that have a real historical relationship for
    a seam. Fails closed to an honestly-labeled empty result if there
    isn't enough history yet — never fabricates a seam from insufficient
    data. Safe to call from anywhere; touches no existing file.
    """
    hist = load_history()
    if hist is None or len(hist) < _MIN_JOINT_OBSERVATIONS + 1:
        return {
            "status": "insufficient_history",
            "observations": 0 if hist is None else len(hist),
            "checked_pairs": 0,
            "seams": [],
        }

    n_dims = hist.shape[1]
    labels = STATE_LABELS[:n_dims]
    first_ever = _load_first_ever()
    seams = []
    checked = 0

    for i in range(n_dims):
        for j in range(i + 1, n_dims):
            series_a = hist[:, i].tolist()
            series_b = hist[:, j].tolist()
            result = check_pair(series_a, series_b)
            if result is None:
                if _pearson(series_a, series_b) is not None and abs(_pearson(series_a, series_b)) >= _CORR_THRESHOLD:
                    checked += 1
                continue
            checked += 1

            direction = _direction_key(labels[i], result["z_a"], labels[j], result["z_b"])
            pair_key = (labels[i], labels[j], direction)
            is_first = pair_key not in first_ever
            if is_first:
                first_ever.add(pair_key)

            seam_entry = {
                "pair": [labels[i], labels[j]],
                "direction": direction,
                "first_ever": is_first,
                **result,
            }
            seams.append(seam_entry)

            if is_first:
                _plant_seam_question(labels[i], labels[j], result)
                _publish_seam_event(labels[i], labels[j], result)

    _save_first_ever(first_ever, len(hist))

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "observations": len(hist),
        "checked_pairs": checked,
        "seams": seams,
    }
    try:
        _SEAM_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_SEAM_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.debug("[Seam] log write failed: %s", e)

    return {"status": "ok", "observations": len(hist), "checked_pairs": checked, "seams": seams}


if __name__ == "__main__":
    print(json.dumps(observe(), indent=2))
