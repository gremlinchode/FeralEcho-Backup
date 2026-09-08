# Generation-Time Epistemic Revision — Implementation

## Implementation Rules gate: assessed and met for the fixes actually made

The mission's own gate requires implementation only if a "small, additive, rollback-able mechanism with a clear causal path and reproducible tests" was found. Two real bugs were found with exactly that shape (a content/rendering bug, and a detection regex gap); both were fixed. A third candidate mechanism (a stronger generation-time evidence gate) was tested in a minimal form and found insufficient — per the mission's own Phase 10 instruction, no larger version of that mechanism was built, since there was no evidence a bigger version of a technique that already failed would succeed (see `generation_epistemic_design.md`).

## Diff summary (not committed — left in the working tree for review, per this session's established practice for real code changes)

```
 app/core/echo_ground_truth.py           | 69 ++++++++++++++++++++++++++----
 app/core/self_knowledge_verification.py | 40 ++++++++++-----------
 app/core/self_model_claims.py           | 30 +++++++++++++
 3 files changed, 111 insertions(+), 28 deletions(-)
```

### `app/core/self_model_claims.py` (+30, purely additive)

New function `resolve_subject_truth(subject, self_model) -> bool | None` — the single shared implementation of "resolve a `KNOWN_SUBJECTS` dotted path against a real `self_model.json` dict," used by both `self_knowledge_verification.py`'s Check 5 and `echo_ground_truth.py`'s claims renderer. Deliberately extracted rather than reimplemented a second time, to avoid recreating the exact `CATEGORIES`/`TASK_TYPE_MAP` duplication-drift failure shape found twice earlier this session.

### `app/core/self_knowledge_verification.py` (net -0, real content changed)

1. Check 5's inline dotted-path-resolution logic (14 lines) replaced with a single call to the new shared `resolve_subject_truth()` — confirmed byte-for-byte identical detection behavior before/after via direct test.
2. `_DENIAL_RE` extended with two new alternative patterns, catching two real denial phrasings found via live testing that the original four patterns missed: "I do not have a [specific] X component" and "there's no evidence [...] that X is real." Verified against 6 direct test cases: the 2 new real misses now correctly caught, the original detection case still works, and 3 negative/regression cases (a genuinely-inactive component, an affirmative claim, an unrelated "don't have" sentence with no subject present, and hedged uncertainty) all still correctly *not* flagged.

### `app/core/echo_ground_truth.py` (+69/-28 net, `_build_self_model_claims()` rewritten)

1. Gained a `sm: dict | None = None` parameter, threaded from the two real call sites in `get_structural_self_facts()` (which already has `sm` loaded).
2. Rendering changed from a bare `"{subject}: VERIFIED TRUE/FALSE"` boolean label to a plainly-stated current fact (`"CURRENTLY VERIFIED REAL AND ACTIVE"` / `"CURRENTLY NOT VERIFIED as active"` / `"current status unavailable to re-check right now"`), resolved via the shared `resolve_subject_truth()`, with the ledger's historical verdict demoted to supporting context rather than the primary assertion.
3. One general, non-subject-specific evidence-priority instruction line appended when any claim history exists — tested and found insufficient alone (see validation doc), left in place because it did not make anything worse in the trials run and is a real, if incomplete, piece of the intended mechanism per the mission's Section 6 design sketch.

## What was NOT changed

- `self_model_claims.py`'s `record_claim()`/`get_recent_claims()`/`KNOWN_SUBJECTS`/the `proposed_by != verified_by` guard — untouched, all still exactly as the living-self-model commit left them.
- `routes_echo_studio.py` — untouched; the call site that invokes `verify_self_knowledge_claims()` and `record_claim()` is unchanged.
- The Liveness Ledger's `self_model_claims_integrity` check (19th, from the living-self-model commit) — untouched; still passes, since `resolve_subject_truth()`'s behavior on a drifted schema is unchanged (still fails closed to `False`, the same property that check tests).
- No `EDIT_FORBIDDEN_TARGETS` changes — no new production module was created this mission.

## Verification run before/after each change

- Syntax-checked every touched file after every edit (`ast.parse`).
- Check 5's refactor: identical detection results on both the real motivating case and a genuinely-inactive-component negative control, confirmed via direct function call, before touching the regex.
- `_DENIAL_RE` extension: 6-case direct test (2 new catches, 1 original-pattern regression check, 3 negative controls) — all pass.
- `resolve_subject_truth()`: 5-case direct test (real value, drifted/renamed field, missing self_model, `None` self_model, unknown subject) — all fail-closed correctly, matching the existing Liveness Ledger check's own expectations.
- Two real server restarts via the documented safe path (`kill $(lsof -ti :5000)`, since `start_echo.sh`'s watchdog was live and `safe_restart.sh` correctly refused direct restart both times), confirmed `serving` after each, before running any live-conversation test against the new code.
