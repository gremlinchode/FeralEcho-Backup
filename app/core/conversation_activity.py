# app/core/conversation_activity.py
"""
Shared "is a real conversation in flight right now" signal — 2026-07-19,
"remove every excuse" pass.

Deliberately separate from app/core/stillness_state.py, not a variant of
it: stillness is Echo's own deliberate, narrative rest state (entered and
exited by her own loops); this is a plain, mechanical fact about whether
a real HTTP request (mirror_echo, Echo Studio chat) is currently being
served. The two can disagree — Echo can be "in stillness" narratively
while a real request is in flight, or vice versa — and conflating them
would have been the same category of confabulation this whole pass exists
to remove.

Ollama's single-concurrency limit (-np 1) is external to this codebase —
FeralEcho can't reorder a request already queued inside Ollama. This
module exists so autonomous loops can at least avoid *adding* to that
queue while a real conversation is already using it, via
autonomy_coordinator.should_run_cycle()'s shared gate.

Import only from this module in tight loops — no heavy dependencies,
same convention as stillness_state.py.
"""
import threading

_active_count = 0
_lock = threading.Lock()


def mark_start() -> None:
    """Call at the start of a real conversational request. Always pair
    with mark_end() in a finally block — an unpaired mark_start() would
    leave autonomous loops deferring forever."""
    global _active_count
    with _lock:
        _active_count += 1


def mark_end() -> None:
    """Call when a real conversational request finishes, success or not."""
    global _active_count
    with _lock:
        _active_count = max(0, _active_count - 1)


def is_conversation_active() -> bool:
    """True while at least one real conversational request is in flight."""
    with _lock:
        return _active_count > 0
