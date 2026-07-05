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


def should_run_cycle(loop_name: str) -> bool:
    """One throttle + stillness gate shared by all three autonomy loops."""
    try:
        from app.core.system_guard import should_throttle
        if should_throttle():
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
    _record(loop_name, None)
    return True


def _record(loop_name: str, skipped_reason: "str | None") -> None:
    _last_cycle[loop_name] = {
        "last_check_utc": datetime.now(timezone.utc).isoformat(),
        "skipped_reason": skipped_reason,
    }


def get_autonomy_status() -> dict:
    return dict(_last_cycle)
