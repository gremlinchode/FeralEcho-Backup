"""
app/core/self_edit_generated.py — Echo's own self-edit target file.

Reset 2026-07-21 to a clean, honestly-inert baseline (no `apply_to_code`
defined) after the deployed candidate (quality_scoring family, attempt 6,
a CodeQualityEvaluator class) was found to call two functions that don't
exist anywhere in the codebase and to use `re.search()` without `import re`
— safe only by accident, because `apply_to_code` had landed nested inside
the class rather than at module level, making it invisible to
`_apply_self_edit_output()`'s module-level lookup. Reset rather than
hand-patched, per this file's own established precedent (Finding 31):
it's self-edit's own output, not hand-authored code, so a reset is more
honest than debugging a broken generated candidate by hand.

`quality_scoring` is paused from the self-edit targeting rotation in the
same change (self_edit_manager.py's `_FOCUS_FAMILY_BY_CREATIVITY`) — same
non-convergence shape `prose_stripping` already showed before its own
2026-07-19 pause, so a bare reset alone would likely just be overwritten
by a near-identical attempt 7 on the next cycle.
"""
