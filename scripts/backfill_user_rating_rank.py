#!/usr/bin/env python3
"""Fold already-consumed human ratings into RiverBrain's ranking mean.

learn_from_rating() used to train the River classifier and leave
model_task_stats alone. score_model() reads that mean. Ratings at or
before memory/user_rating_cursor.json were already consumed and will
not be seen again, so this script applies only the ranking-mean update
for those rows. It never calls learn_from_rating(), so the classifier
is not trained a second time.

Default is a dry run: print model, task type, old mean, new mean, and
how many ratings moved that row. Nothing is written.

--commit writes memory/river_brain.pkl and memory/user_rating_rank_backfill.json
so a second run cannot apply the same ratings again. It refuses while
run.py or start_echo.sh is alive: the live RiverBrain writer would
overwrite the file from the in-memory brain, which does not have this
update until that process is restarted onto the new code.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import json
import os
import pickle
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.echo_model_orchestrator import (  # noqa: E402
    INTERACTION_LOG_PATH,
    RIVER_BRAIN_PATH,
    TASK_TYPE_MAP,
    _USER_RATING_CURSOR_PATH,
    _apply_user_rating_to_rank_stats,
    RiverBrain,
    load_interaction_log,
)

_MARKER_PATH = "memory/user_rating_rank_backfill.json"
# Class attribute only. RiverBrain() starts a writer thread, so this script
# must never construct one.
_WINDOW = RiverBrain._MEAN_EFFECTIVE_WINDOW


def _self_test() -> None:
    """The attribution rules below must match _apply_pending_user_ratings."""
    entries = [
        {"type": "note", "source": "autonomous", "timestamp": "2026-01-01T00:00:00",
         "model": "autonomous-model", "task_type": "coding"},
        {"type": "note", "source": "user_conversation", "timestamp": "2026-01-02T00:00:00",
         "model": "echo:latest", "task_type": "personal"},
        {"type": "user_rating", "timestamp": "2026-01-03T00:00:00", "rating": 5},
        {"type": "user_rating", "timestamp": "2026-01-04T00:00:00", "rating": 3},
        {"type": "user_rating", "timestamp": "2026-01-05T00:00:00", "rating": 1},
        {"type": "user_rating", "timestamp": "2026-01-01T12:00:00", "rating": 4},
    ]
    attributed, invalid, unattributed = _attribute_ratings(entries, "2026-01-04T00:00:00", "")
    got = [(row["timestamp"], row["rating"], row["model"], row["task_type"]) for row in attributed]
    assert got == [
        ("2026-01-03T00:00:00", 5, "echo:latest", "personal"),
        ("2026-01-04T00:00:00", 3, "echo:latest", "personal"),
    ], got
    assert invalid == 0 and unattributed == 1, (invalid, unattributed)
    again, _, _ = _attribute_ratings(entries, "2026-01-04T00:00:00", "2026-01-04T00:00:00")
    assert again == [], again
    unknown = _attribute_ratings(
        [{"type": "note", "source": "user_conversation", "timestamp": "t0",
          "model": "m", "task_type": "not-a-real-task"},
         {"type": "user_rating", "timestamp": "t1", "rating": 4}],
        "t1", "",
    )[0]
    assert unknown[0]["task_type"] == "general", unknown


def _attribute_ratings(entries, cursor_ts: str, already_through_ts: str):
    """Same prior-row rule as _apply_pending_user_ratings.

    A rating counts when already_through_ts < timestamp <= cursor_ts.
    The live applier only consumes timestamp > cursor, so this window is
    exactly the rows it will not see again. Rating 3 stays in the list;
    the rank helper writes nothing for it. Unknown task types remap to
    general, matching learn_from_rating().
    """
    interactions = [
        entry for entry in entries
        if entry.get("type") != "user_rating" and entry.get("source") == "user_conversation"
    ]
    ratings = [
        entry for entry in entries
        if entry.get("type") == "user_rating"
        and already_through_ts < entry.get("timestamp", "") <= cursor_ts
    ]
    attributed = []
    invalid = 0
    unattributed = 0
    for rating_entry in sorted(ratings, key=lambda entry: entry.get("timestamp", "")):
        user_rating = rating_entry.get("rating")
        rating_ts = rating_entry.get("timestamp", "")
        if not isinstance(user_rating, int) or isinstance(user_rating, bool) or user_rating not in range(1, 6):
            invalid += 1
            continue
        prior = [entry for entry in interactions if entry.get("timestamp", "") < rating_ts]
        if not prior:
            unattributed += 1
            continue
        ref = prior[-1]
        task_type = ref.get("task_type", "general")
        if task_type not in TASK_TYPE_MAP:
            task_type = "general"
        attributed.append({
            "timestamp": rating_ts,
            "rating": user_rating,
            "model": ref.get("model", "unknown"),
            "task_type": task_type,
        })
    return attributed, invalid, unattributed


def _load_cursor() -> str:
    if not os.path.exists(_USER_RATING_CURSOR_PATH):
        return ""
    with open(_USER_RATING_CURSOR_PATH, encoding="utf-8") as handle:
        return json.load(handle).get("last_processed_ts", "") or ""


def _load_marker() -> dict | None:
    if not os.path.exists(_MARKER_PATH):
        return None
    with open(_MARKER_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _apply_to_stats(stats: dict, attributed: list) -> tuple[dict, dict]:
    """Return (per-key report, counts). Mutates stats."""
    report = {}
    applied = 0
    neutral = 0
    for row in attributed:
        key = (row["model"], row["task_type"])
        bucket = stats.setdefault(row["model"], {}).setdefault(
            row["task_type"], {"count": 0, "mean": 0.5}
        )
        if key not in report:
            report[key] = {
                "old_mean": float(bucket.get("mean", 0.5)),
                "old_count": int(bucket.get("count", 0)),
                "old_user_rating_count": int(bucket.get("user_rating_count", 0)),
                "applied": 0,
                "neutral": 0,
            }
        if _apply_user_rating_to_rank_stats(bucket, row["rating"], _WINDOW):
            applied += 1
            report[key]["applied"] += 1
        else:
            neutral += 1
            report[key]["neutral"] += 1
        report[key]["new_mean"] = float(bucket.get("mean", 0.5))
        report[key]["new_count"] = int(bucket.get("count", 0))
        report[key]["new_user_rating_count"] = int(bucket.get("user_rating_count", 0))
    for item in report.values():
        item.setdefault("new_mean", item["old_mean"])
        item.setdefault("new_count", item["old_count"])
        item.setdefault("new_user_rating_count", item["old_user_rating_count"])
    return report, {"applied": applied, "neutral": neutral}


def _sanity(report: dict) -> list[str]:
    problems = []
    for (model, task), item in report.items():
        delta_count = item["new_count"] - item["old_count"]
        delta_ratings = item["new_user_rating_count"] - item["old_user_rating_count"]
        if delta_count != item["applied"] or delta_ratings != item["applied"]:
            problems.append(
                f"{model}/{task}: count moved by {delta_count}, user_rating_count by {delta_ratings}, "
                f"applied {item['applied']}"
            )
        if not 0.0 <= item["new_mean"] <= 1.0:
            problems.append(f"{model}/{task}: new mean {item['new_mean']} is outside [0, 1]")
    return problems


def _print_report(cursor_ts: str, attributed: list, invalid: int, unattributed: int, report: dict, counts: dict) -> None:
    print(f"cursor_ts={cursor_ts or '<none>'}")
    print(
        f"attributed={len(attributed)} mean_writes={counts['applied']} "
        f"neutral_or_unmapped={counts['neutral']} invalid={invalid} unattributed={unattributed}"
    )
    if not report:
        print("no model/task row was touched")
        return
    print(f"{'model':<28} {'task':<22} {'old_mean':>10} {'new_mean':>10} {'applied':>8} {'count':>12}")
    for (model, task) in sorted(report):
        item = report[(model, task)]
        print(
            f"{model:<28} {task:<22} {item['old_mean']:10.6f} {item['new_mean']:10.6f} "
            f"{item['applied']:8d} {item['old_count']:5d}->{item['new_count']:<5d}"
        )


def _listeners() -> list[str]:
    found = []
    for pattern in ("run.py", "start_echo.sh"):
        result = subprocess.run(
            ["pgrep", "-fl", pattern],
            capture_output=True, text=True, check=False,
        )
        for line in result.stdout.splitlines():
            if "pgrep" in line:
                continue
            found.append(line.strip())
    return found


def _commit(cursor_ts: str, attributed: list) -> int:
    listeners = _listeners()
    if listeners:
        print("refusing to write river_brain.pkl while a River writer can still be alive:")
        for line in listeners:
            print(f"  {line}")
        return 2
    if _load_marker() is not None:
        print(f"marker already exists at {_MARKER_PATH}; refusing to apply these ratings twice")
        return 2
    lock_path = RIVER_BRAIN_PATH + ".lock"
    os.makedirs(os.path.dirname(RIVER_BRAIN_PATH), exist_ok=True)
    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            if not os.path.exists(RIVER_BRAIN_PATH):
                print(f"missing {RIVER_BRAIN_PATH}")
                return 2
            with open(RIVER_BRAIN_PATH, "rb") as handle:
                data = pickle.load(handle)
            stats = data.get("model_task_stats")
            if not isinstance(stats, dict):
                print("river_brain.pkl has no model_task_stats dict")
                return 2
            report, counts = _apply_to_stats(stats, attributed)
            problems = _sanity(report)
            print("commit snapshot:")
            _print_report(cursor_ts, attributed, 0, 0, report, counts)
            if problems:
                print("refusing to write:")
                for problem in problems:
                    print(f"  {problem}")
                return 2
            tmp_path = RIVER_BRAIN_PATH + ".rating_backfill.tmp"
            with open(tmp_path, "wb") as handle:
                pickle.dump(data, handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, RIVER_BRAIN_PATH)
            marker = {
                "backfilled_through_ts": cursor_ts,
                "mean_writes": counts["applied"],
                "neutral_or_unmapped": counts["neutral"],
                "attributed": len(attributed),
            }
            tmp_marker = _MARKER_PATH + ".tmp"
            with open(tmp_marker, "w", encoding="utf-8") as handle:
                json.dump(marker, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_marker, _MARKER_PATH)
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
    print(f"wrote {RIVER_BRAIN_PATH}")
    print(f"wrote {_MARKER_PATH}")
    return 0


def main() -> int:
    _self_test()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="write river_brain.pkl and the one-shot marker after the dry-run math",
    )
    args = parser.parse_args()

    marker = _load_marker()
    cursor_ts = _load_cursor()
    if marker is not None:
        print(
            f"already backfilled through {marker.get('backfilled_through_ts')!r} "
            f"({marker.get('mean_writes')} mean writes). Nothing further to apply."
        )
        return 0

    entries = load_interaction_log()
    attributed, invalid, unattributed = _attribute_ratings(entries, cursor_ts, "")
    if not os.path.exists(RIVER_BRAIN_PATH):
        print(f"missing {RIVER_BRAIN_PATH}; attribution only, no means to update")
        _print_report(cursor_ts, attributed, invalid, unattributed, {}, {"applied": 0, "neutral": 0})
        return 2

    with open(RIVER_BRAIN_PATH, "rb") as handle:
        data = pickle.load(handle)
    stats = copy.deepcopy(data.get("model_task_stats") or {})
    report, counts = _apply_to_stats(stats, attributed)
    print("dry run (no file written):")
    _print_report(cursor_ts, attributed, invalid, unattributed, report, counts)
    problems = _sanity(report)
    if problems:
        print("dry-run math failed sanity:")
        for problem in problems:
            print(f"  {problem}")
        return 2
    if not args.commit:
        print("dry run only. Re-run with --commit after this printout looks right, and only while Echo is stopped.")
        return 0
    return _commit(cursor_ts, attributed)


if __name__ == "__main__":
    sys.exit(main())
