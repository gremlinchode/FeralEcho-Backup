# app/core/shadow_model.py
# ============================================================
# SHADOW SELF-MODEL
# A lightweight experimental copy of self_model.json that Echo
# can freely overwrite with proposed targets without touching
# the production self-model.
#
# NightCycle reads shadow vs real and logs whether Echo's
# self-predictions were accurate. Over time this measures
# whether Echo's self-assessments are calibrated.
# ============================================================

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_SHADOW_PATH = Path("memory/shadow_self_model.json")
_REAL_PATH = Path("memory/self_model.json")
_ACCURACY_LOG = Path("memory/shadow_accuracy.jsonl")


def propose(adjustments: dict) -> None:
    """Write an experimental self_model proposal to the shadow file.

    adjustments: any self_model.json keys you want to override.
    Merged on top of the current real self_model as the baseline.
    Example:
        propose({"targets": {"next_self_edit_focus": "creative"}})
    """
    try:
        base = {}
        if _REAL_PATH.exists():
            with open(_REAL_PATH) as f:
                base = json.load(f)
        shadow = {
            **base,
            **adjustments,
            "shadow_proposed_at": datetime.now(timezone.utc).isoformat(),
        }
        _SHADOW_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW_PATH, "w") as f:
            json.dump(shadow, f, indent=2)
        logger.debug("[SHADOW] Proposal written: %s", list(adjustments.keys()))
    except Exception as e:
        logger.warning("[SHADOW] propose() failed: %s", e)


def compare_to_actual() -> dict:
    """Compare shadow targets and quality projections to real self_model.json.

    Returns a delta dict that can be logged to shadow_accuracy.jsonl.
    """
    try:
        if not _SHADOW_PATH.exists():
            return {"status": "no_shadow"}
        if not _REAL_PATH.exists():
            return {"status": "no_real_model"}

        with open(_SHADOW_PATH) as f:
            shadow = json.load(f)
        with open(_REAL_PATH) as f:
            real = json.load(f)

        shadow_targets = shadow.get("targets", {})
        real_targets = real.get("targets", {})

        shadow_perf = shadow.get("performance", {}).get("by_task_type", {})
        real_perf = real.get("performance", {}).get("by_task_type", {})

        quality_delta: dict = {}
        for task, s_data in shadow_perf.items():
            r_data = real_perf.get(task, {})
            s_q = s_data.get("avg_quality_score", 0.0)
            r_q = r_data.get("avg_quality_score", 0.0)
            quality_delta[task] = round(r_q - s_q, 4)

        return {
            "shadow_focus": shadow_targets.get("next_self_edit_focus", "?"),
            "real_focus": real_targets.get("next_self_edit_focus", "?"),
            "focus_matches": (
                shadow_targets.get("next_self_edit_focus")
                == real_targets.get("next_self_edit_focus")
            ),
            "quality_delta_from_shadow": quality_delta,
            "shadow_proposed_at": shadow.get("shadow_proposed_at", "unknown"),
            "real_updated_at": real.get("last_updated", "unknown"),
        }
    except Exception as e:
        logger.warning("[SHADOW] compare_to_actual() failed: %s", e)
        return {"status": "error", "reason": str(e)}


def log_accuracy() -> dict:
    """Compare shadow to real, append to shadow_accuracy.jsonl, return the delta."""
    delta = compare_to_actual()
    if "status" in delta:
        return delta
    try:
        entry = {"ts": datetime.now(timezone.utc).isoformat(), **delta}
        _ACCURACY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_ACCURACY_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(
            "[SHADOW] Accuracy logged | focus_matches=%s | shadow_focus=%s | real_focus=%s",
            delta.get("focus_matches"),
            delta.get("shadow_focus"),
            delta.get("real_focus"),
        )
    except Exception as e:
        logger.warning("[SHADOW] log_accuracy() failed: %s", e)
    return delta


_DRIFT_THRESHOLD = -0.15   # task quality delta worse than this triggers correction
_CORRECTION_LOG = Path("memory/shadow_corrections.log")


def check_and_correct(delta: dict) -> "str | None":
    """
    Inspect a delta from log_accuracy() and, when calibration has drifted
    significantly for any task type, propose a corrective focus and log it.

    Returns the corrected task type, or None if delta was within tolerance.
    """
    quality_deltas = delta.get("quality_delta_from_shadow", {})
    if not quality_deltas:
        return None

    worst_task = min(quality_deltas, key=lambda t: quality_deltas[t])
    worst_delta = quality_deltas[worst_task]
    if worst_delta >= _DRIFT_THRESHOLD:
        return None

    # propose() intentionally absent (2026-07-03):
    # Shadow corrections are advisory-only until the signal is externally validated.
    # Both sides of the shadow comparison trace to Echo's own outputs (reflection
    # keyword matching vs. quality_score on Echo responses) — no external anchor.
    # Corrections are logged below for future human review. See Finding 18.
    # Reconnect by restoring propose() here once shadow_corrections.log shows
    # consistent correlation with actual River accuracy improvement.

    try:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "corrected_task": worst_task,
            "delta": worst_delta,
            "all_deltas": quality_deltas,
            "shadow_focus": delta.get("shadow_focus"),
            "real_focus": delta.get("real_focus"),
        }
        _CORRECTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_CORRECTION_LOG, "a") as f:
            import json as _json
            f.write(_json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning("[SHADOW] check_and_correct log failed: %s", e)

    logger.warning(
        "[SHADOW] Calibration drift | task=%s delta=%.3f → proposed corrective focus",
        worst_task, worst_delta,
    )
    return worst_task


def propose_from_reflection(reflection_text: str) -> None:
    """Auto-propose a shadow target based on what Echo just reflected on.

    Lightweight heuristic: if the reflection mentions a task type, propose it
    as an experimental self_edit_focus. No LLM call — pure keyword matching.
    """
    _TASK_KEYWORDS = {
        "reasoning": ["reason", "logic", "pattern", "deduc", "infer", "analyz"],
        "coding": ["code", "program", "function", "debug", "implement", "script"],
        "creative": ["story", "poem", "imagine", "creat", "narrative", "express"],
        "personal": ["feel", "belief", "faith", "reflect", "meaning", "identity"],
    }
    text_lower = reflection_text.lower()
    best_task = None
    best_count = 0
    for task, keywords in _TASK_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_task = task

    if best_task and best_count >= 2:
        propose({
            "targets": {
                "next_self_edit_focus": best_task,
                "reason": f"shadow_proposed_from_reflection (score={best_count})",
            }
        })
        logger.debug("[SHADOW] Auto-proposed focus=%s from reflection (score=%d)", best_task, best_count)
