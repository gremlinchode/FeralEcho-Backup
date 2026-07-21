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

_STATE_PATH = Path("memory/mlx_crash_avoidance.json")


def _evaluate_crash_window(
    file_infos: "list[tuple[float, bool]]",
    now: float,
    lookback_hours: float = _LOOKBACK_HOURS,
    trigger_count: int = _TRIGGER_COUNT,
    cooldown_hours: float = _COOLDOWN_HOURS,
) -> dict:
    """
    Pure, file-I/O-free evaluator — same pure/IO split as seam_engine.py's
    check_pair(). file_infos is a list of (mtime_epoch, has_mlx_signature)
    tuples for every crash report found, regardless of age; this function
    does the window/threshold logic so it's directly testable against
    synthetic input, real or fake, independent of the real filesystem.
    """
    cutoff = now - (lookback_hours * 3600)
    matching = [mtime for mtime, has_sig in file_infos if has_sig and mtime >= cutoff]
    count = len(matching)
    avoid_until = None
    if count >= trigger_count:
        avoid_until = max(matching) + (cooldown_hours * 3600)
    return {
        "recent_crash_count": count,
        "avoid_until": avoid_until,
        "lookback_hours": lookback_hours,
        "trigger_count": trigger_count,
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
        result = _evaluate_crash_window(file_infos, time.time())
        result["computed_at"] = time.time()

        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(result))
        tmp.replace(_STATE_PATH)

        if result["avoid_until"]:
            matching_mtimes = [mtime for mtime, has_sig in file_infos if has_sig]
            hours_ago = (time.time() - max(matching_mtimes)) / 3600 if matching_mtimes else 0.0
            until_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result["avoid_until"]))
            logging.warning(
                f"[MLX-AVOIDANCE] {result['recent_crash_count']} MLX-signature crash(es) "
                f"in the last {_LOOKBACK_HOURS}h (most recent ~{hours_ago:.1f}h ago) — "
                f"excluding mlx:* models from this session's council pool until {until_str}."
            )
            try:
                from app.core.echo_core import get_echo_core
                core = get_echo_core()
                if core:
                    core.publish_salience(
                        source="crash_awareness",
                        kind="mlx_avoidance.engaged",
                        summary=f"{result['recent_crash_count']} MLX crashes in {_LOOKBACK_HOURS}h",
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
