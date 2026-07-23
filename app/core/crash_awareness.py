"""
app/core/crash_awareness.py — "learned avoidance," not just resurrection.

Differential audit (2026-07-20/21, see audits/2026-07-20_differential_audit.md
and CLAUDE.md Finding 49) found 9 crash reports over ~71.5h sharing an
identical mlx::core::gpu::check_error -> libc++abi -> abort() signature.
Until now, Echo's only response to that crash was pure regeneration:
start_echo.sh's watchdog restarts the process, unchanged, and it can walk
straight back into the same failure on the very next MLX-selected council.
This module gives the process one cheap instinct instead: notice a recent
cluster of matching crashes and temporarily stop selecting mlx:* models,
the same way _RETIRED_MODELS permanently excludes vicuna:latest
(echo_model_orchestrator.py, Finding 39) — just temporary, and decided
fresh at every process start rather than hardcoded.
"""

import glob
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

_CRASH_REPORT_GLOB = os.path.expanduser(
    "~/Library/Logs/DiagnosticReports/python3.12-*.ips"
)
_MLX_SIGNATURE = "mlx::core::gpu::check_error"

_LOOKBACK_HOURS = 12
_TRIGGER_COUNT = 2
_COOLDOWN_HOURS = 4

# Found 2026-07-22: a real crash-rate escalation (12 SIGABRT exits in one
# day, vs. 21 total in the whole week before) went completely undetected by
# the check above, because it only ever reads real macOS .ips crash
# reports — and macOS throttles crash-report generation when the same
# process keeps crashing in a short window. Confirmed directly: only 1 of
# those 12 watchdog-logged exits had a corresponding .ips file. The
# watchdog's own log line ("Echo exited with code 134") is written on
# every single restart regardless of whether macOS bothered to write a
# report, making it a strictly more reliable evidence source for "is
# something crashing repeatedly" even though it can't confirm *which*
# signature caused any individual exit (unlike a confirmed .ips match).
# Deliberately a higher trigger count than the signature-confirmed path
# (3 vs 2) and OR'd with it, not a replacement — this is a coarser signal
# (any repeated SIGABRT, not confirmed-MLX specifically) used as a
# conservative fallback for exactly the case the .ips-only check is blind
# to, not a claim that every such exit is really MLX.
_WATCHDOG_TRIGGER_COUNT = 3
_WATCHDOG_LOG_PATH = os.path.join("memory", "echo_watchdog.log")

_STATE_PATH = Path("memory/mlx_crash_avoidance.json")


def _evaluate_crash_window(
    file_infos: "list[tuple[float, bool]]",
    now: float,
    lookback_hours: float = _LOOKBACK_HOURS,
    trigger_count: int = _TRIGGER_COUNT,
    cooldown_hours: float = _COOLDOWN_HOURS,
    watchdog_timestamps: "list[float] | None" = None,
    watchdog_trigger_count: int = _WATCHDOG_TRIGGER_COUNT,
) -> dict:
    """
    Pure, file-I/O-free evaluator — same pure/IO split as seam_engine.py's
    check_pair(). file_infos is a list of (mtime_epoch, has_mlx_signature)
    tuples for every crash report found, regardless of age; this function
    does the window/threshold logic so it's directly testable against
    synthetic input, real or fake, independent of the real filesystem.

    watchdog_timestamps (optional, default None/empty — fully backward
    compatible with every existing caller that doesn't pass it) is a
    second, independent evidence source: real watchdog-logged SIGABRT
    exit timestamps, which can't confirm the MLX signature specifically
    but can't be silently throttled away the way .ips files can be
    either. Either path triggering is enough to engage avoidance; when
    both do, the later avoid_until wins (more conservative, not less).
    """
    cutoff = now - (lookback_hours * 3600)
    matching = [mtime for mtime, has_sig in file_infos if has_sig and mtime >= cutoff]
    count = len(matching)

    watchdog_matching = [
        ts for ts in (watchdog_timestamps or []) if ts >= cutoff
    ]
    watchdog_count = len(watchdog_matching)

    avoid_until = None
    triggered_by = []
    if count >= trigger_count:
        avoid_until = max(matching) + (cooldown_hours * 3600)
        triggered_by.append("confirmed_signature")
    if watchdog_count >= watchdog_trigger_count:
        watchdog_avoid_until = max(watchdog_matching) + (cooldown_hours * 3600)
        if avoid_until is None or watchdog_avoid_until > avoid_until:
            avoid_until = watchdog_avoid_until
        triggered_by.append("watchdog_sigabrt_rate")

    return {
        "recent_crash_count": count,
        "recent_watchdog_sigabrt_count": watchdog_count,
        "avoid_until": avoid_until,
        "triggered_by": triggered_by,
        "lookback_hours": lookback_hours,
        "trigger_count": trigger_count,
        "watchdog_trigger_count": watchdog_trigger_count,
        "cooldown_hours": cooldown_hours,
    }


def _parse_ips_header_timestamp(text: str) -> "float | None":
    """
    Parse the authoritative crash timestamp from a .ips report's own JSON
    header (its first line), e.g. "2026-07-16 20:20:41.00 -0700".

    Found and fixed 2026-07-21: this function used to not exist —
    _gather_crash_file_info() trusted os.path.getmtime() instead, which
    turned out to be unreliable. Confirmed directly: two real crash
    reports (filenames dated 2026-07-15 and 2026-07-16) had mtimes
    matching the current day instead — 5-6 days after the actual crash,
    each landing within seconds of a real avoidance-check timestamp in
    memory/echo_watchdog.log. A plain Python read was directly tested
    against a copy of one of these files and confirmed NOT to change its
    mtime, ruling out this module's own file access as the cause — most
    likely macOS's own background crash-report processing (symbolication,
    Spotlight indexing, or similar) touches these files well after the
    real crash. This made an old crash look artificially fresh, risking a
    false or wrongly-extended avoidance trigger based on a stale report
    rather than a genuinely new one. Returns None (falls back to mtime,
    logged as a fallback rather than silently trusted as equally good)
    only if the header itself is ever unparseable.
    """
    try:
        first_line = text.split("\n", 1)[0]
        header = json.loads(first_line)
        ts_str = header.get("timestamp")
        if not ts_str:
            return None
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f %z")
        return dt.timestamp()
    except Exception:
        return None


def _gather_crash_file_info() -> "list[tuple[float, bool]]":
    """
    Real I/O: glob real macOS crash reports, check each for the MLX
    signature. Never raises — returns [] on any failure (directory
    missing, no permission, etc.), which _evaluate_crash_window()
    correctly treats as zero recent crashes, not an error state.
    """
    out = []
    try:
        for path in glob.glob(_CRASH_REPORT_GLOB):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                crash_time = _parse_ips_header_timestamp(text)
                if crash_time is None:
                    crash_time = os.path.getmtime(path)
                    logging.debug(
                        f"[MLX-AVOIDANCE] Falling back to mtime for {path} — "
                        "header timestamp unparseable"
                    )
                out.append((crash_time, _MLX_SIGNATURE in text))
            except Exception:
                continue
    except Exception as e:
        logging.debug(f"[MLX-AVOIDANCE] crash report scan failed: {e}")
    return out


_WATCHDOG_EXIT_RE = None  # compiled lazily, see _parse_watchdog_exit_line()


def _parse_watchdog_exit_line(line: str) -> "float | None":
    """
    Parses a real start_echo.sh watchdog line of the shape
    "[WATCHDOG] 2026-07-22T23:05:51Z Echo exited with code 134. Restarting
    in 10s..." into an epoch timestamp. Returns None for any non-matching
    line (including a watchdog restart line for a different exit code —
    only SIGABRT/134 is evidence of a real crash here) or an unparseable
    timestamp, never raises.
    """
    global _WATCHDOG_EXIT_RE
    if _WATCHDOG_EXIT_RE is None:
        import re
        _WATCHDOG_EXIT_RE = re.compile(
            r"\[WATCHDOG\]\s+(\S+)\s+Echo exited with code 134\."
        )
    m = _WATCHDOG_EXIT_RE.search(line)
    if not m:
        return None
    try:
        ts_str = m.group(1)
        # start_echo.sh logs UTC ISO-8601 with a trailing Z.
        dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
        from datetime import timezone
        return dt.replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return None


def _gather_watchdog_crash_timestamps() -> "list[float]":
    """
    Real I/O: scan the real watchdog log for genuine SIGABRT (code 134)
    exit lines. Never raises — returns [] on any failure (file missing,
    unreadable, etc.), which _evaluate_crash_window() correctly treats as
    "no additional evidence," not an error state.

    A line-count tail (the original design here) turned out not to work:
    checked directly against the real live log and found WATCHDOG lines
    are sparse relative to the volume of ordinary request/operational
    logging between them — the most recent real crash line sat 6,476
    lines before the end of a 216,352-line file, and even a 3,000-line
    tail window (already generous by this module's own usual standards)
    missed it entirely. A full-file scan is the reliable fix: this file
    is size-capped by Finding 51's log retention (tens of MB at most),
    and iterating line-by-line without materializing the whole file into
    a single readlines() list keeps memory bounded regardless of size.
    Only called once per process start, so the cost of a full scan here
    is a non-issue.
    """
    try:
        if not os.path.exists(_WATCHDOG_LOG_PATH):
            return []
        out = []
        with open(_WATCHDOG_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                ts = _parse_watchdog_exit_line(line)
                if ts is not None:
                    out.append(ts)
        return out
    except Exception as e:
        logging.debug(f"[MLX-AVOIDANCE] watchdog log scan failed: {e}")
        return []


def refresh_avoidance_state() -> dict:
    """
    Real scan + persist. Called once per process start (run.py's startup
    sequence) — the crash-report directory only changes if this exact
    process just crashed and got restarted, so a single startup-time
    computation is sufficient; no periodic re-scan thread needed.
    Fails safe to "no avoidance" on any error — never blocks startup.
    """
    try:
        file_infos = _gather_crash_file_info()
        watchdog_timestamps = _gather_watchdog_crash_timestamps()
        result = _evaluate_crash_window(file_infos, time.time(), watchdog_timestamps=watchdog_timestamps)
        result["computed_at"] = time.time()

        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(result))
        tmp.replace(_STATE_PATH)

        if result["avoid_until"]:
            matching_mtimes = [mtime for mtime, has_sig in file_infos if has_sig]
            most_recent_evidence = max(matching_mtimes + watchdog_timestamps) if (matching_mtimes or watchdog_timestamps) else time.time()
            hours_ago = (time.time() - most_recent_evidence) / 3600
            until_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result["avoid_until"]))
            triggered_by = result.get("triggered_by", [])
            # Honest about which evidence actually triggered this — a
            # watchdog-only trigger means "repeated SIGABRT, cause not
            # confirmed" (macOS may simply be throttling crash reports),
            # not a confirmed MLX diagnosis, and that distinction matters
            # for whoever reads this log.
            if "confirmed_signature" in triggered_by and "watchdog_sigabrt_rate" in triggered_by:
                basis = (f"{result['recent_crash_count']} confirmed MLX-signature crash(es) AND "
                         f"{result['recent_watchdog_sigabrt_count']} watchdog-logged SIGABRT exit(s)")
            elif "confirmed_signature" in triggered_by:
                basis = f"{result['recent_crash_count']} confirmed MLX-signature crash(es)"
            else:
                basis = (f"{result['recent_watchdog_sigabrt_count']} watchdog-logged SIGABRT exit(s) "
                         f"(cause not signature-confirmed — macOS may be throttling crash reports)")
            logging.warning(
                f"[MLX-AVOIDANCE] {basis} in the last {_LOOKBACK_HOURS}h (most recent ~{hours_ago:.1f}h ago) — "
                f"excluding mlx:* models from this session's council pool until {until_str}."
            )
            try:
                from app.core.echo_core import get_echo_core
                core = get_echo_core()
                if core:
                    core.publish_salience(
                        source="crash_awareness",
                        kind="mlx_avoidance.engaged",
                        summary=basis,
                        detail=result,
                        salience=0.7,
                    )
            except Exception:
                pass  # workspace publish is best-effort, never blocks the real decision above
        return result
    except Exception as e:
        logging.debug(f"[MLX-AVOIDANCE] refresh failed, defaulting to no avoidance: {e}")
        return {"recent_crash_count": 0, "avoid_until": None}


def is_mlx_avoidance_active() -> bool:
    """
    Cheap, frequent-call-safe check — reads the persisted state file only,
    no re-scan of the crash-report directory. Fails safe to False (normal
    operation, no exclusion) on any error, since this is a defensive
    nicety layered on top of normal council selection, not a hard safety
    gate that should ever block a real response.
    """
    try:
        state = json.loads(_STATE_PATH.read_text())
        avoid_until = state.get("avoid_until")
        return avoid_until is not None and time.time() < avoid_until
    except Exception:
        return False
