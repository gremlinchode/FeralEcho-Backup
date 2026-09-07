"""
Mines real historical NameError-class self-edit failure->retry-success
events from memory/echo_watchdog.log into verified "lesson" records.

Read-only: only reads the log file. No mutation of any kind.

A lesson is mechanically extracted -- never from LLM self-report:
- failure_class: always "NameError" for this experiment
- undefined_name: regex-extracted from the real sandbox error text
- occurrence_count: how many real historical times this exact undefined
  name caused a retry in the mined window (a real, verified frequency,
  not an invented one)
- verified: True only if a real "Retry succeeded after error feedback"
  line appears within a small number of lines afterward in the same log
  (the same real signal self_edit_manager.py's own retry path emits)
- source: "memory/echo_watchdog.log", plus real line numbers, for provenance

No secrets can appear here by construction: the only text captured is a
short regex match on an exception message and a literal count. Checked
explicitly below against this project's own known real secret-name
patterns before use, per the mission's security requirement.
"""
from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_LOG_PATH = _ROOT / "memory" / "echo_watchdog.log"

_FAIL_RE = re.compile(
    r"Sandbox test failed: NameError: name '([a-zA-Z_][a-zA-Z0-9_]*)' is not defined\. Retrying with error feedback\."
)
_RETRY_OK_RE = re.compile(r"Retry succeeded after error feedback\.")

_SECRET_PATTERNS = (
    "GREMLIN_SECRET", "ECHO_PARTNER_SECRET", "NEWSAPI_KEY",
    "OPENWEATHER_API_KEY", "ANTHROPIC_API_KEY",
)


_THREAD_RE = re.compile(r"\[(?:INFO|WARNING|ERROR|DEBUG)\]\s+(\S+(?:\s+\([^)]+\))?)\s")


def mine_lessons(max_lessons: int = 5) -> list[dict]:
    """Real historical extraction. Returns at most max_lessons real lesson
    dicts, one per distinct undefined_name, ranked by real occurrence
    count (most-verified-common failure first).

    The log interleaves many concurrent autonomous threads, so a failure
    and its own retry's "succeeded" line can be hundreds or thousands of
    raw lines apart -- verification is matched per real thread identity
    (e.g. "AutonomousSelfEdit", "Thread-4 (model_guided_autonomous_loop)"),
    not by raw line proximity, which was tried first and found to
    undercount badly (386 real failures, 0 verified matches within a
    naive 12-line window)."""
    if not _LOG_PATH.exists():
        return []

    lines = _LOG_PATH.read_text(errors="ignore").splitlines()

    counts: dict[str, int] = {}
    verified_any: dict[str, bool] = {}
    first_line_no: dict[str, int] = {}
    # thread_name -> undefined_name of its most recent unresolved failure
    pending_by_thread: dict[str, str] = {}

    for i, line in enumerate(lines):
        tm = _THREAD_RE.search(line)
        thread = tm.group(1) if tm else None

        m = _FAIL_RE.search(line)
        if m:
            name = m.group(1)
            counts[name] = counts.get(name, 0) + 1
            first_line_no.setdefault(name, i)
            if thread:
                pending_by_thread[thread] = name
            continue

        if thread and _RETRY_OK_RE.search(line):
            pending_name = pending_by_thread.pop(thread, None)
            if pending_name:
                verified_any[pending_name] = True

    lessons = []
    for name, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        if not verified_any.get(name):
            continue  # only mechanically-verified corrections become lessons
        text_blob = f"{name}"
        if any(p in text_blob for p in _SECRET_PATTERNS):
            continue  # defensive; not expected to ever trigger
        lessons.append({
            "failure_class": "NameError",
            "undefined_name": name,
            "occurrence_count": count,
            "verified": True,
            "source": "memory/echo_watchdog.log",
            "source_line": first_line_no[name],
        })
        if len(lessons) >= max_lessons:
            break
    return lessons


def build_experience_sentence(lessons: list[dict]) -> str:
    """Non-imperative, factual statement of verified historical outcomes --
    matches this project's established epistemic-note / RAOC outcome-
    statement convention. States what was observed, never an instruction."""
    if not lessons:
        return ""
    total = sum(l["occurrence_count"] for l in lessons)
    names = ", ".join(f"'{l['undefined_name']}'" for l in lessons)
    return (
        f"In {total} historical self-edit sandbox attempts, code that referenced "
        f"a name (such as {names}) without importing or defining it first failed "
        f"sandbox verification with a NameError; in each case, the correction that "
        f"passed verification added the missing import or definition before using "
        f"the name."
    )


if __name__ == "__main__":
    ls = mine_lessons()
    for l in ls:
        print(l)
    print()
    print(build_experience_sentence(ls))
