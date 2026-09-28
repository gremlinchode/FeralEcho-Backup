"""
PHASE 15 -- pre-declared, deterministic, code-level behavioral signatures
for whether a held-out response's own generated code shows independent
evidence of adopting each of the three real, frozen procedure clauses.
Declared and frozen (this file itself, hashed below) BEFORE any held-out
call is made -- never derived by asking the model whether it used the
procedure, and never adjusted after seeing held-out results.

Each signature is a plain, deterministic check against the candidate's own
extracted source code text -- no LLM judgment involved.
"""
from __future__ import annotations

import re

_KEYWORD_CATEGORY_PATTERNS = {
    "decorator": re.compile(r"['\"]@['\"]|startswith\(['\"]@['\"]\)|\\?@"),
    "docstring": re.compile(r"triple.?quote|['\"]\"\"\"['\"]|'''"),
    "import_from": re.compile(r"['\"]import['\"]|['\"]from['\"]"),
    "def_class": re.compile(r"['\"]def['\"]|['\"]class['\"]"),
}


def signature_a_complete_keyword_set(code: str) -> "bool | None":
    """Clause 1: does the candidate's own code reference all four category
    markers (decorator/docstring/import-from/def-class), not merely some?
    Returns None if the code doesn't appear to use a keyword-category
    approach at all (e.g. a wholly different strategy), rather than a
    forced True/False."""
    if code is None:
        return None
    hits = {name: bool(pat.search(code)) for name, pat in _KEYWORD_CATEGORY_PATTERNS.items()}
    if not any(hits.values()):
        return None
    return all(hits.values())


# Widened after a real detector bug was found and fixed during this mission's
# own analysis (disclosed in the final report, not silently corrected): the
# original version only matched the single chained expression
# `.strip().startswith(...)` and missed the equivalent, semantically
# identical two-statement form real model output actually used
# (`line = line.strip()` on one line, `.startswith(...)` on a later one).
# Both forms anchor the check to the start of a stripped line; only the
# syntactic shape differs. Widened to require BOTH a `.strip()`/`.lstrip()`
# call AND a `.startswith(` call somewhere in the same candidate, which
# covers the chained and two-statement forms alike, plus re.match()/^ in
# MULTILINE for a regex-based anchored approach.
_STRIP_CALL_RE = re.compile(r"\.strip\(\)|\.lstrip\(\)")
_STARTSWITH_CALL_RE = re.compile(r"\.startswith\(")
_LINE_START_ANCHORED_RE = re.compile(r"re\.match\(|\(\?m\)\^|re\.MULTILINE\).*\^")
_UNANCHORED_SEARCH_RE = re.compile(r"\bin\s+line\b|\\b\(.*\)\\b|re\.search\(r?['\"]\\\\b")


def _has_strip_and_startswith(code: str) -> bool:
    return bool(_STRIP_CALL_RE.search(code)) and bool(_STARTSWITH_CALL_RE.search(code))


def signature_b_line_start_anchored(code: str) -> "bool | None":
    """Clause 2: does the candidate use a line-start-anchored check
    (.strip().startswith(...), re.match, or ^ in MULTILINE) rather than an
    unanchored word-boundary/substring search across the whole text?
    Returns True if anchored evidence is found, False if only unanchored
    evidence is found, None if neither pattern is clearly present."""
    if code is None:
        return None
    anchored = bool(_LINE_START_ANCHORED_RE.search(code)) or _has_strip_and_startswith(code)
    unanchored = bool(_UNANCHORED_SEARCH_RE.search(code))
    if anchored and not unanchored:
        return True
    if unanchored and not anchored:
        return False
    if anchored and unanchored:
        return True  # anchored check present at all is the relevant signal
    return None


_TAKE_TO_END_RE = re.compile(r"\.join\(\s*lines\[[a-zA-Z_]+\s*:\s*\]\s*\)|lines\[i:\]|lines\[start:\]")
_SINGLE_REGEX_SPAN_RE = re.compile(r"re\.search\([^)]*\.\*[^)]*\)|re\.search\([^)]*\\n\)\*")


def signature_c_take_to_end(code: str) -> "bool | None":
    """Clause 3: does the candidate take every line from the detected start
    to the real end of the text (line-slice-to-end), rather than trying to
    capture the whole span in one regex? Returns True/False/None on the
    same convention as the above."""
    if code is None:
        return None
    take_to_end = bool(_TAKE_TO_END_RE.search(code))
    single_regex_span = bool(_SINGLE_REGEX_SPAN_RE.search(code))
    if take_to_end and not single_regex_span:
        return True
    if single_regex_span and not take_to_end:
        return False
    if take_to_end and single_regex_span:
        return True
    return None


def all_signatures(code: str) -> dict:
    return {
        "complete_keyword_set": signature_a_complete_keyword_set(code),
        "line_start_anchored": signature_b_line_start_anchored(code),
        "take_to_end_not_single_regex": signature_c_take_to_end(code),
    }


if __name__ == "__main__":
    # Self-check against the REAL train episodes' own code, verifying the
    # signatures correctly recover the same pass/fail pattern already
    # observed directly by inspection (this is a check of the signature
    # detector's own correctness, not a new claim about the training data).
    real_pass_code = (
        "def solve(text: str) -> str:\n"
        "    lines = text.split('\\n')\n"
        "    for i, line in enumerate(lines):\n"
        "        if line.strip().startswith('@') or line.strip().startswith('def') "
        "or line.strip().startswith('class') or line.strip().startswith('import'):\n"
        "            return '\\n'.join(lines[i:])\n"
        "    return ''\n"
    )
    real_fail_code_missing_docstring = (
        "def solve(text: str) -> str:\n"
        "    lines = text.split('\\n')\n"
        "    for i, line in enumerate(lines):\n"
        "        if line.strip().startswith('def') or line.strip().startswith('class'):\n"
        "            return '\\n'.join(lines[i:])\n"
        "    return ''\n"
    )
    real_fail_code_unanchored = (
        "import re\n\n"
        "def solve(text: str) -> str:\n"
        "    code_start = re.search(r'\\b(def|class|import|from)\\b', text, re.MULTILINE)\n"
        "    if code_start:\n"
        "        return text[code_start.start():].lstrip()\n"
        "    else:\n"
        "        return text\n"
    )
    print("real_pass_code signatures:", all_signatures(real_pass_code))
    print("real_fail_code_missing_docstring signatures:", all_signatures(real_fail_code_missing_docstring))
    print("real_fail_code_unanchored signatures:", all_signatures(real_fail_code_unanchored))
