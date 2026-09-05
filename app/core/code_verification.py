# app/core/code_verification.py
# ============================================================
# CORRECTNESS VERIFICATION FOR CONVERSATIONAL CODING ANSWERS
#
# 2026-07-19, Echo self-awareness forensic audit, Finding #1 — see
# audits/2026-07-18_echo_self_awareness_probe.md. Asked for the exact
# function her own self-edit loop had failed at 96+ times, cleanly and
# directly (none of the self-edit pipeline's own clutter), Echo's answer
# was confidently explained and completely non-functional — confirmed by
# actually running it. One raw councillor (echo:latest) went further and
# presented a specific "worked example" with a claimed output that is
# false when the code is actually run. Nothing in the ordinary chat path
# executes generated code before presenting it.
#
# Self-edit's own F2 gate (self_edit_manager.py's test_code_in_sandbox())
# deliberately does NOT execute candidate code either — but for a
# documented, different reason: self-edit candidates routinely reference
# functions in themselves that haven't been deployed yet, so execution
# was "architecturally broken" for that specific case and F2 moved to
# import-only verification. Conversational code snippets don't have that
# self-reference problem, so real execution is tractable here in a way it
# wasn't for self-edit.
#
# Scope, stated honestly: this does not attempt to prove arbitrary
# generated code is "correct" in general (undecidable without a spec). It
# catches two concrete, bounded things: (a) code that doesn't even parse,
# and (b) the specific failure mode caught tonight — a response that
# contains its own checkable claim (a print(...) call next to a claimed
# "# Output: ..." comment) that turns out to be false when actually run.
# That second part is narrow by design — it catches self-contradiction,
# not general incorrectness.
# ============================================================

import ast
import logging
import os
import re
import tempfile

logger = logging.getLogger(__name__)

# re.IGNORECASE added 2026-09-04 (Tier-4-confirmatory refactor, found
# during live validation of the synthesis-preservation fix, not
# hypothesized): a real echo:latest response used a "```Python" fence
# (capital P). Python's re module is case-sensitive by default, so
# (?:python)? never matched, the fence was found nowhere at all, and
# extract_python_blocks() silently returned zero blocks for a response
# that had real code in it -- confirmed directly via a full-response
# diagnostic capture, not inferred. This is a pre-existing gap in an
# already-shipped path (verify_response_code(), Finding 43/44's
# conversational code-verification caveat) that predates this refactor;
# fixing it here benefits that path too, not just the new synthesis
# checks that exposed it.
_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# A bare print(...) call — matched only against the code portion of a
# line (see find_claimed_example, which splits off any trailing comment
# first). A naive single regex spanning both the call and an optional
# trailing "# Output: ..." comment breaks as soon as the comment itself
# contains parentheses (e.g. "# Output: print('foo')") — greedy .+
# consumes through the LAST ')' on the line, which lands inside the
# comment, not the real call. Splitting on '#' first avoids that class of
# bug entirely rather than fighting it with regex lookahead tricks.
_PRINT_CALL_RE = re.compile(r"print\((?P<call>.+)\)\s*$")


def extract_python_blocks(text: str) -> list:
    """Pull every fenced code block out of response text. Deliberately
    returns blocks that fail to parse too — a syntax error is exactly one
    of the two things this module exists to catch, not something to
    silently filter out before the caller sees it."""
    return [m.group(1) for m in _FENCE_RE.finditer(text)]


def find_claimed_example(text: str) -> "tuple[str, str] | None":
    """Find a self-claimed worked example: a print(<call>) line followed
    by a claimed output, either as a trailing inline comment or on the
    very next '#'-prefixed line. Returns (call_expression, claimed_output),
    or None if the response makes no such checkable claim — most answers
    won't, and that's fine, there's nothing to verify in that case."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Split off any trailing comment BEFORE regex-matching the call —
        # doing it in one combined regex breaks when the comment itself
        # contains parentheses (see _PRINT_CALL_RE's comment).
        code_part, _, comment_part = stripped.partition("#")
        m = _PRINT_CALL_RE.search(code_part.strip())
        if not m:
            continue
        call = m.group("call").strip()
        inline = comment_part.strip()
        if inline.lower().startswith("output"):
            inline = inline.split(":", 1)[-1].strip() if ":" in inline else inline[6:].strip()
        if inline:
            return call, inline
        if i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt.startswith("#"):
                return call, nxt.lstrip("#").strip()
    return None


def verify_in_sandbox(script: str, timeout: int = 10) -> "tuple[bool, str]":
    """Actually run `script` under the real kernel-level sandbox — reuses
    sandbox.run_script.run_sandbox_script_isolated, the same isolated
    execution path self-edit's own experiment runner and autonomous
    sandbox cycles already use, rather than re-implementing the
    sandbox-exec invocation here. Returns (ran_ok, actual_stdout)."""
    from sandbox.run_script import run_sandbox_script_isolated

    fd, path = tempfile.mkstemp(suffix="_code_verify.py", prefix="claim_check_")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(script)
        result = run_sandbox_script_isolated(path, timeout=timeout)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if not result["success"]:
        return False, result.get("error") or "sandbox execution failed"

    # safe_exec_wrapper.py prints "SANDBOX_OK" as its own final line in
    # every mode, after any real output the script produced — strip it
    # before comparing against a claimed output.
    actual = "\n".join(
        ln for ln in result["output"].splitlines() if ln.strip() != "SANDBOX_OK"
    ).strip()
    return True, actual


def verify_response_code(response_text: str) -> "tuple[str | None, bool | None]":
    """Orchestrates verification for a full response. Returns
    (caveat, verified):
      - caveat: a short string to append if something checkable failed,
        else None.
      - verified: True if a self-made claim was checked and confirmed
        true, False if syntax failed or a checked claim was false, None
        if nothing was checkable at all (the common case — most coding
        answers make no verifiable claim, and that's fine, not evidence
        of anything either way).
    `verified` is deliberately a tri-state, not a bool: callers feeding
    this into a learning signal (see RiverBrain's learn_from_sandbox_outcome)
    need to distinguish "nothing to learn from" from "confirmed good" —
    collapsing that to a bool would either invent positive evidence for
    ordinary unclaimed answers or silently drop real negative evidence.
    Never raises — any internal failure fails open (no caveat, no signal)
    rather than blocking or corrupting a real response."""
    try:
        blocks = extract_python_blocks(response_text)
        if not blocks:
            return None, None

        for block in blocks:
            try:
                ast.parse(block)
            except SyntaxError as e:
                return (
                    f"\n\n⚠️ Note: the code above doesn't parse as valid Python "
                    f"({e.msg} on line {e.lineno}) — treat it as a draft, not a tested "
                    f"solution.",
                    False,
                )

        claim = find_claimed_example(response_text)
        if claim is None:
            return None, None
        _call_expression, claimed_output = claim

        # Run every extracted block concatenated in order, not one at a
        # time — the function definition and the usage example that
        # exercises it routinely live in separate fenced blocks (exactly
        # the real shape found tonight), so testing blocks in isolation
        # made the checkable claim look unverifiable and let it slip
        # through unflagged. Concatenating matches how a reader would
        # actually run the example.
        full_script = "\n\n".join(blocks)
        try:
            ran_ok, actual_output = verify_in_sandbox(full_script)
        except Exception as e:
            logger.debug(f"[CODE_VERIFY] sandbox call failed: {e}")
            return None, None
        if not ran_ok:
            return None, None  # couldn't execute at all — fail open, don't blame the claim

        actual_lines = {ln.strip() for ln in actual_output.splitlines()}
        if claimed_output.strip() not in actual_lines:
            return (
                f"\n\n⚠️ Note: I checked the worked example above by actually "
                f"running the code — the claimed output (`{claimed_output}`) doesn't "
                f"match what it actually prints. Treat the code as unverified.",
                False,
            )
        return None, True  # the claim checked out
    except Exception as e:
        logger.debug(f"[CODE_VERIFY] verify_response_code failed: {e}")
        return None, None
