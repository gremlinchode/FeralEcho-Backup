# Self-Edit Candidate Evidence Preservation — Implementation

Implements exactly the change qualified in `audits/2026-09-22_self_edit_candidate_logging_qualification.md`. Instrumentation only — no VRM, no learning behavior, no retry/generation change, no new consumer of the preserved evidence.

## 1. Pre-change repository state

- Git HEAD before: `2fba42644c82b9f7096276f4dd338d615cf1bcce`.
- Working tree before: 210 porcelain entries — the same pre-existing dirty set carried through this whole session (27 pre-existing tracked-modified files, the rest untracked research/audit artifacts). **`app/core/self_edit_manager.py` was already modified before this implementation began** (part of that pre-existing 27); `app/core/self_edit_attempt_ledger.py` was **not** yet modified.
- Re-verified the qualification report's own source hashes before touching anything: `self_edit_manager.py` and `self_edit_attempt_ledger.py` were byte-identical to what the qualification report analyzed — confirmed via fresh sha256, matching the values recorded when the qualification was written. Nothing had drifted; proceeded per the mission's own instruction rather than stopping.

## 2. Exact implementation

Three edits to `app/core/self_edit_manager.py`, one to `app/core/self_edit_attempt_ledger.py`. Full diff in §13; summarized here:

1. **`_attempt` dict literal** (inside `execute_self_edit()`) gained three new keys — `initial_candidate_code`, `retry_candidate_code`, `parent_baseline_hash_at_generation` — plus an updated comment correcting the stale "never read by anything" claim (§7's correction from the qualification pass) and stating the artifact-vs-influence-provenance distinction inline, at the source, not just in this report.
2. **A new, independent hash computation**, placed immediately after the `_attempt` dict is constructed (before the prompt/plan/generation steps begin): reads `SELF_EDIT_FILE` in binary mode and computes `hashlib.sha256(...).hexdigest()`, wrapped in try/except that degrades to `None` (logged at debug level) on any failure — never able to block the real attempt.
3. **`_attempt["initial_candidate_code"] = code`**, inserted immediately after `test_code_in_sandbox(code)` returns and `initial_f2_outcome`/`initial_f2_error` are set — capturing the exact string that was just executed, before the retry logic below can reassign the `code` variable.
4. **`_attempt["retry_candidate_code"] = retry_code`**, inserted immediately after the retry's `test_code_in_sandbox(retry_code, ...)` returns and `retry_f2_outcome`/`retry_f2_error` are set, inside the same `if retry_code:` guard those fields already use — so a retry that never actually ran (empty generation) correctly leaves this `None`, exactly mirroring the existing fields' behavior.
5. **`read_recent_f2_error()`'s docstring** gained an explicit contract paragraph (qualification report §6/§14's recommended precision fix): stating plainly that it returns the whole row, that safety today depends on the one real caller extracting by name, and that any future caller must do the same.

**No other line in either file was touched by me.**

## 3. Files changed

- `app/core/self_edit_manager.py` — modified (3 of the edits above).
- `app/core/self_edit_attempt_ledger.py` — modified (the docstring edit).
- `scripts/verify_self_edit_candidate_preservation.py` — new test file.
- This report.

**Nothing else.** No production behavior file besides these two was touched.

## 4. Evidence fields and exact semantics

| Field | Semantics |
|---|---|
| `initial_candidate_code` | The exact candidate string passed to the *first* `test_code_in_sandbox()` call for this attempt (post-cleanup: fences stripped, self-call-stripped — i.e., exactly what was actually executed, not the model's raw un-cleaned output). `None` if generation itself failed before reaching that call. |
| `retry_candidate_code` | The exact candidate string passed to the *retry's* `test_code_in_sandbox()` call, same cleanup state. `None` if no retry occurred, or if the retry generated empty output (never reached execution) — mirroring `retry_f2_outcome`/`retry_f2_error`'s existing null-on-non-execution behavior exactly. |
| `parent_baseline_hash_at_generation` | sha256 of `app/core/self_edit_generated.py`'s raw bytes, read independently at the very start of this specific `execute_self_edit()` call — before the plan or either candidate is generated. Deliberately *not* reused from `generate_code_from_plan()`'s own internal read of the same file (see §6) and deliberately *not* the bare name `parent_baseline_hash` originally proposed, per the qualification report's own finding that the unqualified name was ambiguous between "at generation time" and "at fitness-judgment time," which can genuinely differ. |

## 5. Capture points (with the causal reasoning, not just the line numbers)

Exactly as specified in the qualification report and verified behaviorally by the new test suite (§9): each candidate field is set **immediately after** the sandbox call that consumed it returns, using the local variable that was *actually passed* to that call — never a variable that could have been reassigned since. This is what makes the initial-vs-retry separation real rather than incidental: `initial_candidate_code` is written before `code` is ever reassigned to `retry_code` on a successful retry (confirmed directly in the diff and by test 2b, §9), and `retry_candidate_code` is a distinct dict key entirely, so there is no shared slot for the two to collide in, unlike the pre-existing `reflection_entry["generated_code"]` field this whole investigation started from.

## 6. Parent/baseline provenance — what was actually done, and the one deliberate deviation from the qualification report's literal text

The qualification report's own §7 anchored the hash to `generate_code_from_plan()`'s internal read of `SELF_EDIT_FILE` (`current_contents`, at that function's line ~1808). Implementing it there would have required either changing `generate_code_from_plan()`'s return signature (breaking its other real callers: `wolf_friction_bridge.py`, `scripts/run_capability_pilot.py`, `scripts/run_tier3_apparatus.py`, and others — confirmed by a fresh repo-wide grep before deciding, not assumed) or reaching into that function's local variable from outside it (not possible in Python without a signature change). **Deviation, disclosed rather than silently made**: the hash is instead computed independently, reading `SELF_EDIT_FILE` a second time, at the very start of `execute_self_edit()` — strictly *before* `plan_code_logic()` and `generate_code_from_plan()` are even called, not merely before the latter's internal read. This is an earlier, not later, anchor point than the one originally specified, and is if anything more precise (no dependency on how long plan generation takes before the candidate-generating call begins) — not a weakening. The real, narrow risk this introduces: a concurrent self-edit deploy landing in the brief window between this read and `generate_code_from_plan()`'s own internal read of the same file would make the two reads disagree — an extremely narrow timing window (no LLM call happens in between), and no worse than the risk the qualification report itself already named for the originally-proposed anchor point. Reuses `hashlib.sha256` directly (stdlib), matching `snapshot_manager._sha256_file()`'s algorithm and bytes-only mode exactly, as recommended — not calling that function directly (it isn't exported for reuse and importing `snapshot_manager` into `self_edit_manager` for one hash call was judged a larger, less minimal change than one inline stdlib call).

## 7. Isolation from generation-facing consumers

**The one real consumer, `_attempt_ledger_evidence_section()`, was not modified at all** — confirmed by the diff (§13) touching nothing in that function. It continues to call `entry.get("initial_f2_error", "")` and nothing else. Verified **behaviorally**, not just by reading the source: test 6 in the new suite (§9) writes a synthetic ledger row containing real, distinctive marker strings in both new candidate-code fields, calls the real, unmodified `_attempt_ledger_evidence_section()` against it, and asserts the returned prompt-section text contains the real `initial_f2_error` text but neither marker string. The same test also confirms `read_recent_f2_error()` genuinely *does* return the full row including both markers — proving the isolation is enforced by the one caller's own narrow extraction, not by the data simply being absent, exactly the distinction the qualification report's §6 finding required be tested, not assumed.

The one honest, disclosed limitation carried forward unchanged from the qualification report: this safety is a property of how `_attempt_ledger_evidence_section()` happens to be written today, not a structural guarantee the ledger module itself enforces. The new explicit-contract docstring on `read_recent_f2_error()` (§2, item 5) is the mitigation qualified for this pass — it does not eliminate the possibility of a future careless caller, it makes the requirement impossible to miss by anyone reading the function they're about to call.

## 8. Backward compatibility

Verified directly (test 5, §9): a synthetic historical-shaped row containing none of the three new keys is read successfully by `read_recent_f2_error()` with no exception, and `.get()` access to any of the new keys on that old-shaped row returns `None` cleanly rather than raising. No historical row in the real, live `memory/self_edit_attempt_ledger.jsonl` was read, modified, or rewritten by this implementation or its tests — confirmed by hashing the real file before and after running the full test suite (§10) and finding it changed only by the live server's own ongoing, unrelated real activity (row count grew from 1,330 to 1,335 during this work, consistent with real production self-edit attempts continuing to run on the already-live server throughout).

## 9. Tests added

New file: `scripts/verify_self_edit_candidate_preservation.py`. Every test redirects `self_edit_attempt_ledger._LEDGER_PATH` and `self_edit_manager.SELF_EDIT_FILE` to scratch tempfiles and monkeypatches every real external dependency (`plan_code_logic`, `generate_code_from_plan`, `test_code_in_sandbox`, `choose_model`, `echo_query`, `get_river_brain`, `advise_before_edit`, `_validate_imports`, `scan_for_unsafe_operations`, `_stage_and_import_test`, `save_reflection`, `append_to_journal`, `detect_task_type`, `_prune_stale_staging_files`) so the **real** `execute_self_edit()` code path runs and is inspected, without ever calling Ollama, touching RiverBrain, running a real sandbox subprocess, or writing to any file under `memory/`. 28 checks total:

1. Initial candidate preservation, exact match, on a fail-then-fail attempt.
2. Retry preservation: initial and retry candidates both present and distinct.
3. Retry-succeeds case: **the specific historical overwrite bug** — confirms `initial_candidate_code` survives even when the retry succeeds and the outer `code` variable gets reassigned.
4. No-retry (immediate success) case: `retry_candidate_code`/`retry_f2_outcome`/`retry_f2_error` all correctly stay `None`, never implying a retry that didn't happen.
5. Empty-retry-generation case: `retry_candidate_code` stays `None` (nothing was actually executed), while `initial_candidate_code` is still correctly preserved.
6. Parent hash: matches an independently-computed sha256 of the real scratch parent file's bytes, and changes when that content changes.
7. Backward compatibility: a historical-shaped row without the new fields reads cleanly.
8. **Generation isolation, behavioral**: the critical test — confirms `_attempt_ledger_evidence_section()`'s real output never contains either candidate-code marker while still containing the real error text, and separately confirms the lower-level reader does carry the markers (proving isolation is enforced, not incidental).
9. Full regression: re-runs the pre-existing `scripts/verify_attempt_ledger_prompt_evidence.py` suite as a subprocess and requires it to still exit 0, unmodified.

## 10. Test results

```
28/28 checks passed
```
Ran twice (once during initial authoring, which caught two real test-authoring bugs — not implementation bugs, see §11 — and once clean after fixing them). Full output preserved in this session's own record. The pre-existing regression suite (item 9 above) passed as part of this same run. Both modified files pass `ast.parse()` syntax checks. Real production `memory/self_edit_attempt_ledger.jsonl` re-hashed before and after the entire test run and found to have changed only via the live server's own unrelated real activity (row count and hash both differ only in the direction of new, real rows being appended — never truncated, reordered, or corrupted).

## 11. Adversarial review

Attacked directly, per the mission's own list:

- **Could candidate source leak into generation?** Tested behaviorally and not found — §7/§9 item 8. The one real residual risk (a careless future caller of `read_recent_f2_error()`) is named, not hidden, and mitigated by the new explicit-contract docstring.
- **Could retry overwrite initial evidence?** Tested directly and not found — §9 items 2-3, including the specific historical-bug-shaped case (retry succeeds).
- **Could a candidate be associated with the wrong attempt?** Each `execute_self_edit()` call has its own local `_attempt` dict and local `code`/`retry_code` variables — no shared mutable state across calls; `trace_id` remains the unique per-attempt key, unchanged.
- **Does the parent hash have ambiguous semantics?** Addressed and named directly in §6 — the field name itself now states which of two possible moments it captures, and the deviation from the qualification report's literal anchor point is disclosed with reasoning, not silently made.
- **Do historical rows break?** Tested directly, §9 item 7 / §8 — no.
- **Does ledger consumer behavior change?** Tested behaviorally, §9 item 8 — no; the consumer function itself was not modified.
- **Does malformed candidate source break JSONL?** Not specifically fuzz-tested this pass, but reasoned through and judged low-risk: `json.dumps()` (the existing, unmodified write path) already escapes arbitrary Python strings; this is unchanged by adding two more string-typed fields.
- **Can concurrency cross-wire candidates?** No shared state introduced; reasoning in §5/§9's "wrong attempt" point applies identically.
- **Can a logging failure alter self-edit's real outcome?** No — the hash computation is wrapped in try/except degrading to `None`; the two candidate-code assignments are plain, non-raising dict writes to a dict that already existed; `_finish_attempt()`'s own existing best-effort, never-raise contract (`_record_attempt_ledger`) is unchanged and untouched.
- **Is storage/write behavior materially worse than predicted?** Not independently re-measured this pass beyond the qualification report's own estimate (~5-13MB/month) — the fields added are the same order of magnitude in size as predicted, no new finding here.

**One real, disclosed finding from this pass's own diff review, not previously named**: the working tree already contained an unrelated, pre-existing uncommitted change to `self_edit_manager.py` (a Shadow-model fallback retirement, near `perform_self_edit()`, dated 2026-09-13 in its own comments) from before this implementation began. `git diff` on the whole file necessarily shows it alongside my own three edits. **This hunk is not mine, was not touched, added to, or reverted by this work, and is called out explicitly here rather than silently left for someone else to puzzle over in a combined diff.**

## 12. Remaining limitations — artifact provenance vs. influence provenance, restated plainly

**This implementation improves artifact provenance only.** After this change, a future investigator can reconstruct exactly what code Echo generated on its first attempt, what it generated on a retry if one occurred, and what production file that generation was a modification of — none of which was reconstructable before.

**It does not, and cannot, establish influence provenance.** Nothing here tells a future investigator whether any later attempt actually used, consulted, or was affected by any earlier attempt's preserved evidence — because nothing today reads these two new fields at all (confirmed, §7), and even the one field that *is* already read (`initial_f2_error`) has its actual behavioral effect on generation quality explicitly unproven, per the 2026-09-07 validation report's own disclosed scope limit. A future, separately-designed and separately-authorized experiment that wants to test influence would need to build its own consumer and, critically, log what it fed into each specific prompt at the moment it did so — this implementation does not do that, and must not be described as if it does.

## 13. Diff summary

```
 app/core/self_edit_attempt_ledger.py | 18 +++++++-
 app/core/self_edit_manager.py        | 90 +++++++++++++++++++++++++++---------  (includes the pre-existing, unrelated Shadow-retirement hunk — see §11)
 2 files changed, 85 insertions(+), 23 deletions(-)
```
Of `self_edit_manager.py`'s reported changes, my own edits account for three additive hunks (the `_attempt` dict + hash computation, the `initial_candidate_code` capture, the `retry_candidate_code` capture) totaling well under half the reported diff; the remainder is the pre-existing Shadow-retirement hunk from before this work began (§11), left completely untouched.

**Git HEAD**: unchanged, `2fba42644c82b9f7096276f4dd338d615cf1bcce`, before and after. Nothing was committed, per the mission's own instruction not to commit unless explicitly required.

## 14. Final judgment

Behavioral-equivalence claim, checked rather than assumed: no new read, branch, or conditional was introduced anywhere in the generation/execution/fitness/deployment path — every new line either writes to the `_attempt` dict (already written unconditionally at the end of every attempt, unchanged) or computes a value from data already available at that point in the function. The one real, disclosed residual is the small extra file read for the hash and the marginally larger JSONL write — both bounded and reasoned through in §6/§9/§11, neither found to materially differ from the qualification report's prediction.

---

**CANDIDATE PRESERVATION:** VERIFIED

**INITIAL/RETRY SEPARATION:** VERIFIED

**PARENT PROVENANCE:** VERIFIED (with the disclosed, reasoned deviation in §6 from the qualification report's literal anchor point)

**GENERATION ISOLATION:** VERIFIED (behaviorally tested, not merely read from source; one residual, named risk carried forward — see §7)

**BACKWARD COMPATIBILITY:** VERIFIED

**OBSERVATIONAL INERTNESS:** SUPPORTED

**IMPLEMENTATION STATUS:** QUALIFIED

**What can future researchers know after this change that they could not know before it?** Exactly what source code Echo's self-edit loop generated on the first attempt of a given cycle, and separately what it generated on a retry if one happened, kept distinct even when the retry succeeds and would previously have overwritten the first attempt's record — plus a precise, unambiguous fingerprint of the production file that generation was attempting to modify, at the moment it started trying.

**What can they still NOT know?** Whether any later self-edit attempt actually looked at, was influenced by, or benefited from any earlier attempt's now-preserved evidence — nothing today reads these fields, and this change does not build, wire in, or even design a mechanism that would; that remains a separate, harder, entirely unaddressed question for a future, explicitly authorized experiment.
