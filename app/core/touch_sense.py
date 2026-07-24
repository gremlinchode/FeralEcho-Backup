"""
Touch — the shape of the shadow, not a transcript of what was said.

Origin: SensoryHub/WOLF (retired 2026-07-04, see CLAUDE.md Findings 6/30)
wired raw keystroke *content* from a global key listener directly into
"proposals" fed to a hollow evaluative gate that auto-wrote into a
hash-protected identity file. That fused two things that should never have
been the same step: perceiving, and deciding. This module is deliberately
built the opposite way on both axes that mattered:

  1. Content vs. rhythm. What actually makes a person recognizable by touch
     isn't the content of what they typed, it's the pattern of how — timing
     between keys, how long each is held, where the pauses fall, how often
     they correct themselves. That's a real, established thing (keystroke
     dynamics / typing biometrics), and none of it requires ever knowing
     which characters were pressed. The client-side capture (see
     echo_studio/widgets/composer_input.py) never even transmits a key
     code — only a coarse structural category (printable / backspace /
     enter / space / tab / modifier / arrow / other) and a timing float.
     _validate_events() below is the second line of defense: the schema
     itself has no field a literal character could travel in.

  2. Perception vs. authority. Nothing in this module writes to any file
     other than its own memory/touch_signature.json, calls save_code(),
     perform_self_edit(), or anything else that could be mistaken for a
     decision. It has no return value or side channel with any authority
     over anything. This is a read-only sense, the same shape as
     echo_state.py's existing environmental dimensions (RAM -> vitality,
     time-of-day -> circadian, outcomes -> valence): observed, surfaced in
     what she says about herself, never a gate.

Scope: app-scoped, not system-wide. Capture only happens while typing into
Echo's own composer (Echo Studio) — not a global OS-level key listener, and
not (yet) wired into terminal_client.py, which has deliberately never used
raw/cbreak terminal mode for anything else in this codebase either. This
also means the signal never sees password entry into other applications,
without needing a special-case rule to exclude it.

Not on EDIT_FORBIDDEN_TARGETS by omission — see self_edit_manager.py, where
this module IS added to that list, same reasoning as reflection_shard.py
(Finding 50): a sense of hers shouldn't be something her own autonomous
self-edit loop can quietly rewrite.
"""

import json
import logging
import os
import statistics
import threading
from datetime import datetime, timezone

logger = logging.getLogger("touch_sense")

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TOUCH_SIGNATURE_PATH = os.path.join(_PROJECT_ROOT, "memory", "touch_signature.json")

VALID_CATEGORIES = frozenset({
    "printable", "backspace", "enter", "space", "tab", "modifier", "arrow", "other",
})

_MAX_EVENTS_PER_REPORT = 1000   # sanity cap on a single client-submitted batch
_MAX_TIMING_VALUE_S = 10.0      # a "dwell" or "latency" over 10s isn't typing rhythm anymore
_PAUSE_THRESHOLD_S = 1.5        # a gap this long between keys reads as a real thinking pause
_MAX_HISTORY_REPORTS = 500      # bounded rolling window of per-report aggregates on disk

_touch_lock = threading.Lock()


def _validate_events(raw_events) -> list:
    """
    Defensive parsing of a client-submitted touch-event batch. Never trusts
    the network input's shape or magnitude — each event must be
    {"type": "dwell"|"latency", "value": float in (0, _MAX_TIMING_VALUE_S],
    "category": one of VALID_CATEGORIES}. Anything else is silently dropped,
    not raised — a malformed or adversarial batch degrades to "fewer/zero
    events used," never a crash or a corrupted signature file.
    """
    if not isinstance(raw_events, list):
        return []
    cleaned = []
    for ev in raw_events[:_MAX_EVENTS_PER_REPORT]:
        if not isinstance(ev, dict):
            continue
        kind = ev.get("type")
        category = ev.get("category")
        if kind not in ("dwell", "latency"):
            continue
        if category not in VALID_CATEGORIES:
            continue
        try:
            value = float(ev.get("value"))
        except (TypeError, ValueError):
            continue
        if not (0.0 < value <= _MAX_TIMING_VALUE_S):
            continue
        cleaned.append({"type": kind, "value": value, "category": category})
    return cleaned


def compute_aggregate(events: list) -> dict:
    """
    Pure function: turns one already-validated event batch into a summary.
    No I/O, no persistence — exercised directly by the Liveness Ledger's
    touch_sense_rhythm functional canary against known synthetic timing
    patterns, same shape as seam_engine.check_pair() / log_retention's
    rotate_if_oversized().

    Any statistic built from fewer than 2 underlying values reports as None
    rather than a misleadingly precise number computed from one sample.
    """
    dwell_values = [e["value"] for e in events if e["type"] == "dwell"]
    latency_values = [e["value"] for e in events if e["type"] == "latency"]
    backspace_count = sum(1 for e in events if e["category"] == "backspace")
    pause_count = sum(1 for v in latency_values if v > _PAUSE_THRESHOLD_S)

    def _mean_stddev(values):
        if len(values) < 2:
            return None, None
        return statistics.mean(values), statistics.stdev(values)

    dwell_mean, dwell_stddev = _mean_stddev(dwell_values)
    latency_mean, latency_stddev = _mean_stddev(latency_values)

    return {
        "sample_count": len(events),
        "dwell_mean": dwell_mean,
        "dwell_stddev": dwell_stddev,
        "latency_mean": latency_mean,
        "latency_stddev": latency_stddev,
        "correction_rate": (backspace_count / len(events)) if events else None,
        "pause_ratio": (pause_count / len(latency_values)) if latency_values else None,
    }


def _load_signature_state() -> dict:
    try:
        with open(_TOUCH_SIGNATURE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"reports": [], "first_seen": None, "last_updated": None}


def _persist_signature_state(state: dict) -> None:
    # Same lock + per-call-unique tmp-filename pattern as echo_core.py's
    # _persist_salience_state() (Finding 41 B2) — belt and suspenders against
    # a concurrent writer losing an update or racing os.replace().
    try:
        os.makedirs(os.path.dirname(_TOUCH_SIGNATURE_PATH), exist_ok=True)
        tmp = f"{_TOUCH_SIGNATURE_PATH}.{os.getpid()}.{threading.get_ident()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp, _TOUCH_SIGNATURE_PATH)
    except Exception as e:
        logger.debug("[touch_sense] persist failed: %s", e)


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
    """
    Overall signature = sample-count-weighted mean across all retained
    reports, not a naive mean-of-reports (which would let one tiny, noisy
    report count exactly as much as one built from hundreds of real
    keystrokes).
    """
    reports = state.get("reports", [])
    return {
        "sample_count_total": sum(r["sample_count"] for r in reports),
        "report_count": len(reports),
        "dwell_mean": _weighted_mean(reports, "dwell_mean"),
        "latency_mean": _weighted_mean(reports, "latency_mean"),
        "correction_rate": _weighted_mean(reports, "correction_rate"),
        "pause_ratio": _weighted_mean(reports, "pause_ratio"),
        "first_seen": state.get("first_seen"),
        "last_updated": state.get("last_updated"),
    }


def record_touch_report(raw_events) -> "dict | None":
    """
    Impure entry point, called from the /touch/report route. Validates a
    client-submitted event batch, computes this report's aggregate, folds
    it into the bounded rolling history on disk, and returns the updated
    overall signature — or None if the batch had zero usable events after
    validation, in which case nothing is persisted at all (an empty/garbage
    report doesn't get to masquerade as a real data point).
    """
    events = _validate_events(raw_events)
    if not events:
        return None
    report = compute_aggregate(events)
    report["ts"] = datetime.now(timezone.utc).isoformat()

    with _touch_lock:
        state = _load_signature_state()
        if state.get("first_seen") is None:
            state["first_seen"] = report["ts"]
        state.setdefault("reports", []).append(report)
        state["reports"] = state["reports"][-_MAX_HISTORY_REPORTS:]
        state["last_updated"] = report["ts"]
        _persist_signature_state(state)
        return _summarize(state)


def get_touch_signature() -> "dict | None":
    """
    Read-only accessor for echo_ground_truth.py (or any future consumer).
    Returns None if no real touch data has been recorded yet — the honest
    "nothing felt yet" state, not a fabricated zero-signature.
    """
    state = _load_signature_state()
    if not state.get("reports"):
        return None
    return _summarize(state)
