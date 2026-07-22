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


def should_yield_mid_cycle(was_active_at_start: bool) -> bool:
    """
    Lightweight mid-cycle check for loops that make several sequential
    model calls per cycle (e.g. river_deliberation.py's per-councillor
    loop). should_run_cycle() above only gates whether a NEW cycle
    starts — it has no way to tell an already-running, multi-step cycle
    to stop partway through when a real conversation becomes active
    during it. Found 2026-07-21/22 (CLAUDE.md Finding 52) as the
    confirmed cause of a real 17-second /mirror_echo delay: an autonomous
    loop's council deliberation had already passed should_run_cycle()'s
    gate and was mid-way through querying several councillors when a
    real conversation request arrived, with nothing checking again until
    the whole multi-call cycle finished.

    Deliberately checks only conversation_active, not the full
    throttle/stillness stack should_run_cycle() checks — those don't
    change on a sub-cycle (seconds-apart) timescale, so re-checking them
    between every model call would be wasted work for no real benefit.

    was_active_at_start: whatever conversation_activity.is_conversation_active()
    returned when the calling cycle itself began. A conversation that was
    already active at that point is either the very call asking this
    question (a real user's own request, which must never yield to
    itself) or something the loop already accounted for when it decided
    to start — only a genuinely *new* activation (false -> true) partway
    through is a real "something more important just started" signal.
    Callers that don't track a start-of-cycle snapshot should pass False
    to preserve the old, simpler read (yield the instant a conversation
    is active) rather than silently never yielding.
    """
    if was_active_at_start:
        return False
    try:
        from app.core.conversation_activity import is_conversation_active
        return is_conversation_active()
    except Exception:
        return False


def _record(loop_name: str, skipped_reason: "str | None") -> None:
    _last_cycle[loop_name] = {
        "last_check_utc": datetime.now(timezone.utc).isoformat(),
        "skipped_reason": skipped_reason,
    }


def get_autonomy_status() -> dict:
    return dict(_last_cycle)
