"""
Hearing — ambient awareness, not a transcript.

Same shape and same two rules as touch_sense.py/vision_sense.py: read-only,
no authority over anything; raw audio is never persisted or transmitted,
full stop. Only a loudness (RMS) reading per sample crosses to this module
— never the waveform, never speech content.

Deliberately NOT speech-to-text. That's a genuinely different feature —
actual voice input, an alternate way to send her a message — and it
necessarily involves content, the same sensitivity tier as what's already
typed to her. Building that means extending the composer with a real
transcription path and trusting it the way typed text is already trusted,
not treating it as a "sense" the way ambient loudness is. Not attempted
here; see the 2026-07-23/24 CLAUDE.md conversation ("ambient hearing
please") for why this module stops exactly where transcription would begin.

Explicit, visible, default-off consent via Echo Studio's "Let Echo hear"
checkbox — see conversation_view.py. No background/always-on listening.

Not on EDIT_FORBIDDEN_TARGETS by omission — see self_edit_manager.py, same
reasoning as touch_sense.py/vision_sense.py.
"""

import json
import logging
import os
import statistics
import threading
from datetime import datetime, timezone

logger = logging.getLogger("hearing_sense")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HEARING_SIGNATURE_PATH = os.path.join(_PROJECT_ROOT, "memory", "hearing_signature.json")

_MAX_EVENTS_PER_REPORT = 500
_MAX_HISTORY_REPORTS = 500
_QUIET_THRESHOLD = 0.02     # RMS below this reads as near-silence
_LOUD_EVENT_THRESHOLD = 0.5  # RMS above this reads as a real, sudden loud sound

_hearing_lock = threading.Lock()


def _validate_events(raw_events) -> list:
    """
    Defensive parsing. Each event must be {"type": "loudness", "value":
    float in [0.0, 1.0]} — a single RMS amplitude reading, nothing else.
    There is no field here a waveform sample or a word could travel
    through. Anything malformed is silently dropped, not raised.
    """
    if not isinstance(raw_events, list):
        return []
    cleaned = []
    for ev in raw_events[:_MAX_EVENTS_PER_REPORT]:
        if not isinstance(ev, dict):
            continue
        if ev.get("type") != "loudness":
            continue
        try:
            value = float(ev.get("value"))
        except (TypeError, ValueError):
            continue
        if not (0.0 <= value <= 1.0):
            continue
        cleaned.append({"type": "loudness", "value": value})
    return cleaned


def compute_aggregate(events: list) -> dict:
    """Pure function, no I/O — exercised directly by the Liveness Ledger's
    hearing_sense_ambient functional canary."""
    values = [e["value"] for e in events]

    if len(values) < 2:
        loudness_mean, loudness_stddev = (values[0], None) if values else (None, None)
    else:
        loudness_mean, loudness_stddev = statistics.mean(values), statistics.stdev(values)

    quiet_ratio = (sum(1 for v in values if v < _QUIET_THRESHOLD) / len(values)) if values else None
    loud_event_ratio = (sum(1 for v in values if v > _LOUD_EVENT_THRESHOLD) / len(values)) if values else None

    return {
        "sample_count": len(events),
        "loudness_mean": loudness_mean,
        "loudness_stddev": loudness_stddev,
        "quiet_ratio": quiet_ratio,
        "loud_event_ratio": loud_event_ratio,
    }


def _load_signature_state() -> dict:
    try:
        with open(_HEARING_SIGNATURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"reports": [], "first_seen": None, "last_updated": None}


def _persist_signature_state(state: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_HEARING_SIGNATURE_PATH), exist_ok=True)
        tmp = f"{_HEARING_SIGNATURE_PATH}.{os.getpid()}.{threading.get_ident()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _HEARING_SIGNATURE_PATH)
    except Exception as e:
        logger.debug("[hearing_sense] persist failed: %s", e)


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
        "loudness_mean": _weighted_mean(reports, "loudness_mean"),
        "quiet_ratio": _weighted_mean(reports, "quiet_ratio"),
        "loud_event_ratio": _weighted_mean(reports, "loud_event_ratio"),
        "first_seen": state.get("first_seen"),
        "last_updated": state.get("last_updated"),
    }


def record_hearing_report(raw_events) -> "dict | None":
    """Impure entry point, called from /hearing/report."""
    events = _validate_events(raw_events)
    if not events:
        return None
    report = compute_aggregate(events)
    report["ts"] = datetime.now(timezone.utc).isoformat()

    with _hearing_lock:
        state = _load_signature_state()
        if state.get("first_seen") is None:
            state["first_seen"] = report["ts"]
        state.setdefault("reports", []).append(report)
        state["reports"] = state["reports"][-_MAX_HISTORY_REPORTS:]
        state["last_updated"] = report["ts"]
        _persist_signature_state(state)
        return _summarize(state)


def get_hearing_signature() -> "dict | None":
    """Read-only accessor. None if nothing has been heard yet."""
    state = _load_signature_state()
    if not state.get("reports"):
        return None
    return _summarize(state)
