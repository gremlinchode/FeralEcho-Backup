"""
Prompt workspace — a shared, minimal utility for the disclaimed-system-note
pattern that fixed the directive-misattribution bug three separate times
tonight (bible_injection.py, echo_ground_truth.py, echo_tool_context.py),
each with its own independently hand-written header string.

Not a migration to role-separated messages — that's a much bigger, separate
decision (would touch river_deliberation.py/ollama_handler.py's core
transport). This stays on the existing flat-string prompt-concatenation
model; it just gives every injection point — existing and future — the
same safe, consistent framing from one place, instead of each one
reinventing (or forgetting to reinvent) the same wording.
"""


def system_note(tag: str, body: str, own_record: bool = False) -> str:
    """
    The one place this wording lives. Any block of text that's injected
    into a prompt but isn't part of the actual conversation (a system
    directive, a ground-truth fact dump, a tool result, an internal-state
    note) should be wrapped with this before being concatenated in, so the
    model has an explicit signal that it isn't something the conversation
    partner said.

    own_record: set True for content that IS genuinely the system's own
    first-person operational history (e.g. its own self-edit log, quality
    trajectory, a prior reflection it wrote) rather than external/ephemeral
    data (weather, tool lists, circadian state). Audit finding: both were
    previously wrapped in identical "not part of this conversation, and not
    said by whoever you're talking to" language — a fix for a real
    misattribution bug that also, as a side effect, told the model its own
    verified track record "wasn't said by" anyone, including implicitly
    itself. Default (False) is byte-identical to the original wording, so
    every existing caller is unaffected unless it explicitly opts in.
    """
    if own_record:
        return (
            f"[SYSTEM {tag} NOTE — this is your own verified record, not "
            f"something said by whoever you're talking to right now. {body}]"
        )
    return (
        f"[SYSTEM {tag} NOTE — not part of this conversation, and not said "
        f"by whoever you're talking to. {body}]"
    )


def assemble(base: str, *sections: str) -> str:
    """
    Consistent join order/separator for prepending labeled sections ahead
    of the base (user-facing) content. Replaces the ad-hoc, inconsistent
    concatenation previously done independently at each call site (e.g.
    terminal_client.py used "\\n" for one section and "\\n\\n" for another,
    in a different order than routes_echo_studio.py used for the same two).
    Empty/falsy sections are skipped; if none are present, returns base
    unchanged.
    """
    parts = [s for s in sections if s]
    if not parts:
        return base
    return "\n\n".join(parts) + "\n\n" + base
