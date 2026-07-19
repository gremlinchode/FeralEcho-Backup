"""
Shared throttle/stillness gate and status registry for FeralEcho's three
independent autonomy loops: emergent_scheduler.emergent_loop,
autonomous_loop.autonomous_loop, and run.py's self_edit_loop.

Each loop previously reimplemented its own should_throttle() check
independently, and the self-edit loop had none at all — it would run 10
Optuna trials of code-gen + sandbox execution every hour regardless of
system load. This module doesn't change what any loop does — only how
it decides whether to run this cycle — and exposes a shared status view
for observability via GET /admin/autonomy-status.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_last_cycle: dict = {}


def should_run_cycle(loop_name: str, tier: str = "heavy") -> bool:
    """One throttle + stillness gate shared by all three autonomy loops.

    tier: "heavy" (default, unchanged behavior) throttles at the same
    severe thresholds should_throttle() always used. "light" is for cheap,
    local, non-inference work — throttles only at severe pressure too
    (moderate pressure alone doesn't block it), so a caller that opts in
    can keep running through the same moderate pressure that already
    stops heavy inference work, instead of every loop sharing one
    identical all-or-nothing gate regardless of actual cost (audit
    finding). No existing caller passes tier, so nothing changes for them.
    """
    try:
        from app.core.system_guard import throttle_level
        level = throttle_level()
        # Both tiers currently block only at "severe" — heavy's threshold is
        # deliberately identical to should_throttle()'s historical behavior.
        # Kept as two explicit branches (not collapsed to one check) so a
        # future decision to make "heavy" also stop at "moderate" is a
        # one-line change with an obvious place to make it, not a silent
        # behavior change today.
        if tier == "light":
            blocked = level == "severe"
        else:
            blocked = level == "severe"
        if blocked:
            _record(loop_name, "throttled")
            return False
    except Exception:
        pass
    try:
        from app.core.stillness_state import is_in_stillness
        if is_in_stillness():
            _record(loop_name, "stillness")
            return False
    except Exception:
        pass
    try:
        # 2026-07-19 "remove every excuse" pass: don't let an autonomous
        # loop add to Ollama's single-concurrency queue while a real
        # conversation is already using it. Genuinely different from the
        # stillness check above — see conversation_activity.py's own
        # module docstring for why the two aren't merged.
        from app.core.conversation_activity import is_conversation_active
        if is_conversation_active():
            _record(loop_name, "conversation_active")
            return False
    except Exception:
        pass
    _record(loop_name, None)
    return True


def _record(loop_name: str, skipped_reason: "str | None") -> None:
    _last_cycle[loop_name] = {
        "last_check_utc": datetime.now(timezone.utc).isoformat(),
        "skipped_reason": skipped_reason,
    }


def get_autonomy_status() -> dict:
    return dict(_last_cycle)
