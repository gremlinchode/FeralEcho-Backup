"""
Self-edit outcome tracker — Finding 8 closure.

Measures whether a self-edit actually improved behavior, using signals
independent of the F1/F2/F3 safety pipeline that gates the edit itself
(quality_score, council_rating, human terminal ratings — before vs. after
a fixed window around each successful deploy).

Log-only. Does NOT feed echo_state.py dim[6] (edit_momentum), self-edit
targeting, or River training. Wiring any of this into something
consequential is a separate, explicit decision — see GREMLIN_ROLE.md.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

_OUTCOMES_PATH = Path("memory/self_edit_outcomes.jsonl")
_INTERACTION_LOG = Path("memory/interaction_log.jsonl")
_COUNCIL_LOG = Path("memory/council_ratings.jsonl")

_EVAL_WINDOW_MINUTES = 90


def _parse_ts(s: str) -> "datetime | None":
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", ""))
    except Exception:
        return None


def _load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception as e:
        logging.debug(f"[SELF-EDIT-OUTCOME] load failed for {path}: {e}")
    return out


def record_pending_outcome(task_type: str, edit_timestamp: "str | None" = None) -> None:
    """Called once, right after a self-edit deploys successfully."""
    ts = edit_timestamp or datetime.utcnow().isoformat()
    entry = {
        "edit_id": ts,
        "task_type": task_type,
        "edit_timestamp": ts,
        "status": "pending",
    }
    try:
        _OUTCOMES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_OUTCOMES_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logging.debug(f"[SELF-EDIT-OUTCOME] record_pending_outcome failed: {e}")


def _mean_in_window(entries: list, start: datetime, end: datetime, task_type: str,
                     value_key: str, ts_key: str = "timestamp") -> "tuple[float | None, int]":
    vals = []
    for e in entries:
        if e.get("task_type") != task_type:
            continue
        v = e.get(value_key)
        if v is None:
            continue
        ts = _parse_ts(e.get(ts_key) or "")
        if ts is None or not (start <= ts < end):
            continue
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    return (round(mean(vals), 3) if vals else None), len(vals)


def _human_ratings_in_window(interaction_entries: list, start: datetime, end: datetime,
                              task_type: str) -> "tuple[float | None, int]":
    """Human ratings carry no task_type of their own — attribute each rating to the
    nearest preceding logged interaction, same approximation _apply_pending_user_ratings()
    already uses elsewhere (known-approximate; see audit Finding H-4)."""
    primary = sorted(
        (
            (_parse_ts(e.get("timestamp") or ""), e.get("task_type"))
            for e in interaction_entries
            if e.get("quality_score") is not None and e.get("task_type")
        ),
        key=lambda pair: pair[0] or datetime.min,
    )
    vals = []
    for e in interaction_entries:
        if e.get("type") != "user_rating":
            continue
        ts = _parse_ts(e.get("timestamp") or "")
        if ts is None or not (start <= ts < end):
            continue
        attributed_type = None
        for p_ts, p_task in primary:
            if p_ts is None or p_ts > ts:
                break
            attributed_type = p_task
        if attributed_type != task_type:
            continue
        r = e.get("rating")
        if r is None:
            continue
        try:
            vals.append(float(r))
        except (TypeError, ValueError):
            continue
    return (round(mean(vals), 3) if vals else None), len(vals)


def _delta(pre: "float | None", post: "float | None") -> "float | None":
    if pre is None or post is None:
        return None
    return round(post - pre, 3)


def evaluate_pending_outcomes(eval_window_minutes: int = _EVAL_WINDOW_MINUTES) -> int:
    """Finalize any pending outcome whose window has closed. Cheap no-op when nothing
    is ready — only reads interaction_log/council_ratings when there's work to do."""
    if not _OUTCOMES_PATH.exists():
        return 0

    try:
        lines = _OUTCOMES_PATH.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        logging.debug(f"[SELF-EDIT-OUTCOME] read failed: {e}")
        return 0

    now = datetime.utcnow()
    window = timedelta(minutes=eval_window_minutes)

    entries = []
    ready = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        entries.append(e)
        if e.get("status") == "pending":
            edit_ts = _parse_ts(e.get("edit_timestamp", ""))
            if edit_ts is not None and now - edit_ts >= window:
                ready.append(e)

    if not ready:
        return 0

    interaction_entries = _load_jsonl(_INTERACTION_LOG)
    council_entries = _load_jsonl(_COUNCIL_LOG)

    for e in ready:
        edit_ts = _parse_ts(e["edit_timestamp"])
        pre_start, pre_end = edit_ts - window, edit_ts
        post_start, post_end = edit_ts, edit_ts + window
        task_type = e.get("task_type")

        pre_q, pre_q_n = _mean_in_window(interaction_entries, pre_start, pre_end, task_type, "quality_score")
        post_q, post_q_n = _mean_in_window(interaction_entries, post_start, post_end, task_type, "quality_score")
        pre_c, pre_c_n = _mean_in_window(council_entries, pre_start, pre_end, task_type, "council_rating", ts_key="source_timestamp")
        post_c, post_c_n = _mean_in_window(council_entries, post_start, post_end, task_type, "council_rating", ts_key="source_timestamp")
        pre_h, pre_h_n = _human_ratings_in_window(interaction_entries, pre_start, pre_end, task_type)
        post_h, post_h_n = _human_ratings_in_window(interaction_entries, post_start, post_end, task_type)

        e["status"] = "evaluated"
        e["evaluated_at"] = now.isoformat()
        e["quality_score"] = {"pre": pre_q, "post": post_q, "pre_n": pre_q_n, "post_n": post_q_n, "delta": _delta(pre_q, post_q)}
        e["council_rating"] = {"pre": pre_c, "post": post_c, "pre_n": pre_c_n, "post_n": post_c_n, "delta": _delta(pre_c, post_c)}
        e["human_rating"] = {"pre": pre_h, "post": post_h, "pre_n": pre_h_n, "post_n": post_h_n, "delta": _delta(pre_h, post_h)}

    try:
        tmp = _OUTCOMES_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        tmp.replace(_OUTCOMES_PATH)
    except Exception as e:
        logging.warning(f"[SELF-EDIT-OUTCOME] write-back failed: {e}")
        return 0

    return len(ready)


def get_outcomes_summary(limit: int = 20) -> dict:
    entries = _load_jsonl(_OUTCOMES_PATH)
    pending = [e for e in entries if e.get("status") == "pending"]
    evaluated = [e for e in entries if e.get("status") == "evaluated"]
    recent = sorted(evaluated, key=lambda e: e.get("evaluated_at", ""), reverse=True)[:limit]
    return {
        "pending": len(pending),
        "evaluated": len(evaluated),
        "eval_window_minutes": _EVAL_WINDOW_MINUTES,
        "recent": recent,
    }
