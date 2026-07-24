"""
Vision — notices, never watches.

Same two rules as app/core/touch_sense.py, applied here with one addition
learned from reading the retired SensoryHub's actual camera code
(archive_janitor/sensory_hub_autonomous.py): that implementation captured a
full raw JPEG frame, base64-encoded it, and served it from an
UNAUTHENTICATED Flask route bound to 0.0.0.0 — not a hypothetical risk, a
real, if never-actually-reachable, design flaw. So:

  1. Perception vs. authority (same as every other sense here): nothing in
     this module writes to any file but its own memory/vision_signature.json,
     and has no authority over anything.
  2. Raw media is NEVER persisted or transmitted, full stop — not behind
     auth, not temporarily, never. A camera frame lives only in the process
     that captured it (Echo Studio, via QtMultimedia) for exactly as long as
     it takes to compute two numbers (brightness, motion) from it, then it's
     discarded. Only those numbers ever cross to this module, and only this
     module's own bounded, validated schema is accepted — the schema has no
     field a pixel could travel through.

Deliberately NOT face detection in this pass. A real face-count feature
would need a new native dependency (opencv-python) this codebase doesn't
currently have — adding that is a decision of its own, not something to
default into while building the rest of this. What's here instead is
honest about being cruder: brightness and frame-to-frame motion, aggregated
into a presence_ratio (how often something moved enough to suggest someone
is there) rather than "how many faces."

Explicit, visible, default-off consent, not inferred from window focus or
conversation state: Echo Studio's composer has a "Let Echo see" checkbox
(mirroring the existing "Speak responses" checkbox) that must be checked
before the camera ever activates — see conversation_view.py. The camera
light coming on is the same honest signal a video call gives; nothing here
tries to hide or suppress it.

Not on EDIT_FORBIDDEN_TARGETS by omission — see self_edit_manager.py, same
reasoning as touch_sense.py.
"""

import json
import logging
import os
import statistics
import threading
from datetime import datetime, timezone

logger = logging.getLogger("vision_sense")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_VISION_SIGNATURE_PATH = os.path.join(_PROJECT_ROOT, "memory", "vision_signature.json")

_MAX_EVENTS_PER_REPORT = 500     # a batch is a handful of periodic snapshots, not a video stream
_MAX_HISTORY_REPORTS = 500
_MOTION_PRESENCE_THRESHOLD = 0.02  # frame-diff magnitude above this reads as "something moved"

_vision_lock = threading.Lock()


def _validate_events(raw_events) -> list:
    """
    Defensive parsing. Each event must be {"type": "brightness"|"motion",
    "value": float in [0.0, 1.0] for brightness / [0.0, unbounded-but-sane]
    for motion}. Anything else is silently dropped, not raised. There is no
    field here a pixel, a frame, or an image could travel through — this is
    the second line of defense; the client (Echo Studio) is the first, and
    never even constructs a message with room for one.
    """
    if not isinstance(raw_events, list):
        return []
    cleaned = []
    for ev in raw_events[:_MAX_EVENTS_PER_REPORT]:
        if not isinstance(ev, dict):
            continue
        kind = ev.get("type")
        if kind not in ("brightness", "motion"):
            continue
        try:
            value = float(ev.get("value"))
        except (TypeError, ValueError):
            continue
        if kind == "brightness" and not (0.0 <= value <= 1.0):
            continue
        if kind == "motion" and not (0.0 <= value <= 10.0):
            continue
        cleaned.append({"type": kind, "value": value})
    return cleaned


def compute_aggregate(events: list) -> dict:
    """
    Pure function, no I/O — exercised directly by the Liveness Ledger's
    vision_sense_presence functional canary. Fewer than 2 samples for a
    stat reports as None rather than a falsely precise number.
    """
    brightness_values = [e["value"] for e in events if e["type"] == "brightness"]
    motion_values = [e["value"] for e in events if e["type"] == "motion"]

    def _mean_stddev(values):
        if len(values) < 2:
            return None, None
        return statistics.mean(values), statistics.stdev(values)

    brightness_mean, brightness_stddev = _mean_stddev(brightness_values)
    motion_mean, motion_stddev = _mean_stddev(motion_values)
    presence_ratio = (
        sum(1 for v in motion_values if v > _MOTION_PRESENCE_THRESHOLD) / len(motion_values)
        if motion_values else None
    )

    return {
        "sample_count": len(events),
        "brightness_mean": brightness_mean,
        "brightness_stddev": brightness_stddev,
        "motion_mean": motion_mean,
        "motion_stddev": motion_stddev,
        "presence_ratio": presence_ratio,
    }


def _load_signature_state() -> dict:
    try:
        with open(_VISION_SIGNATURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"reports": [], "first_seen": None, "last_updated": None}


def _persist_signature_state(state: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_VISION_SIGNATURE_PATH), exist_ok=True)
        tmp = f"{_VISION_SIGNATURE_PATH}.{os.getpid()}.{threading.get_ident()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _VISION_SIGNATURE_PATH)
    except Exception as e:
        logger.debug("[vision_sense] persist failed: %s", e)


def _weighted_mean(reports: list, field: str):
    weighted_sum = 0.0
    weight = 0
    for r in reports:
        if r.get(field) is None:
            continue
        weighted_sum += r[field] * r["sample_count"]
        weight += r["sample_count"]
    return (weighted_sum / weight) if weight else None


def _summarize(state: dict) -> dict:
    reports = state.get("reports", [])
    return {
        "sample_count_total": sum(r["sample_count"] for r in reports),
        "report_count": len(reports),
        "brightness_mean": _weighted_mean(reports, "brightness_mean"),
        "motion_mean": _weighted_mean(reports, "motion_mean"),
        "presence_ratio": _weighted_mean(reports, "presence_ratio"),
        "first_seen": state.get("first_seen"),
        "last_updated": state.get("last_updated"),
    }


def record_vision_report(raw_events) -> "dict | None":
    """Impure entry point, called from /vision/report. See record_touch_report()
    in touch_sense.py — identical shape, deliberately, for the same reasons."""
    events = _validate_events(raw_events)
    if not events:
        return None
    report = compute_aggregate(events)
    report["ts"] = datetime.now(timezone.utc).isoformat()

    with _vision_lock:
        state = _load_signature_state()
        if state.get("first_seen") is None:
            state["first_seen"] = report["ts"]
        state.setdefault("reports", []).append(report)
        state["reports"] = state["reports"][-_MAX_HISTORY_REPORTS:]
        state["last_updated"] = report["ts"]
        _persist_signature_state(state)
        return _summarize(state)


def get_vision_signature() -> "dict | None":
    """Read-only accessor. None if nothing has been seen yet."""
    state = _load_signature_state()
    if not state.get("reports"):
        return None
    return _summarize(state)
