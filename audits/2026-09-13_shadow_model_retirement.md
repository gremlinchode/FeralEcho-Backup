# Shadow Model Retirement — Removal From All Live Consumers

**Date:** 2026-09-13
**Type:** Implementation mission, narrow scope (not a research arc)
**Status:** Complete. Retirement invariant established and verified. No commit made.

---

## 1. Executive conclusion

**Shadow has been successfully removed from all live consumers.** `shadow_model.propose()` — and every other function in `app/core/shadow_model.py` — is no longer reachable from any live production code path. This was verified at three independent layers (static full-repo grep, deterministic AST inspection, and a real runtime import), not asserted from the edit alone. The implementation file itself was preserved unmodified except for a new, explicit retirement header; no function body was changed, rewritten, or deleted.

Three live consumers were found and removed. One of them — `self_edit_manager.py`'s `perform_self_edit()` fallback — was a genuine, if last-resort, decision-influencing path: it could set `target_task_type` for a real self-edit generation cycle. The other two (`emergent_scheduler.py`'s reflection-triggered write into Shadow, `night_cycle.py`'s daily accuracy check) never influenced a decision, but were removed anyway because the mission's own required end state (Phase 5: "Live consumer: must be zero") and its explicit self_heal.py precedent ("not imported anywhere; has no live caller") set a bar stronger than "output not consumed for a decision" — leaving Shadow half-connected (still producing/logging, but consumed by nothing) would have reproduced exactly the "looks wired but isn't" ambiguity this project's own Liveness Ledger discipline exists to eliminate.

---

## 2. Starting state

| | |
|---|---|
| Starting Git HEAD | `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f` |
| Working-tree state at mission start | 114 changed lines in `git status --short` (all pre-existing, from prior sessions — none of the 5 files this mission touches were among them, confirmed directly before editing) |
| Implementation location | `app/core/shadow_model.py` (197 lines pre-edit): `propose(adjustments)`, `compare_to_actual()`, `log_accuracy()`, `check_and_correct(delta)`, `propose_from_reflection(reflection_text)` |
| Identified consumers (pre-edit) | 3 live production call sites (see §3) |

---

## 3. Consumer archaeology

Method: a comprehensive `grep -rn` across every `.py` file in the repository for `shadow_model`, `shadow_self_model`, `shadow_accuracy`, `shadow_corrections`, `propose_from_reflection`, `check_and_correct`, `compare_to_actual`, `log_accuracy` — followed by a direct read of every match's surrounding code (not textual inference), and a separate grep across every `.md` file for the same terms. A `.claude/worktrees/agent-abe6ecca0408fd0fb/` copy of `shadow_model.py` was found and excluded — it is a different agent's isolated git worktree, not part of this repository's live tree, and was not touched.

| Consumer | Classification | What it did | What happened |
|---|---|---|---|
| `app/emergent_scheduler.py:727-732` (inside the reflection-generation function) | **Live — write path, not decision path** | Called `propose_from_reflection(response)` on every real reflection cycle, which internally calls `propose()` to write `memory/shadow_self_model.json`. Self-contained `try/except: pass`; return value never used. | Removed. Replaced with a comment documenting the retirement and citing this report. |
| `app/maintenance/night_cycle.py:173-188` (inside the daily maintenance cycle) | **Live — read/log path, not decision path** | Called `log_accuracy()` (reads the shadow file, computes a delta) then `check_and_correct(delta)`. The returned `corrected` value was only ever passed to `logging.warning(...)` — never written anywhere, never passed to any decision function. This matches the module's own pre-existing inline comment: corrections here have been advisory-only/log-only since 2026-07-03 (`propose()` was deliberately left uncalled inside `check_and_correct()`). | Removed. Replaced with a comment documenting the retirement and citing this report. |
| `app/core/self_edit_manager.py:2905-2917`, inside `perform_self_edit()` | **Live — genuine decision path** | When the empirical signal (`SelfModelUpdater().get_weak_task_type()`) was unavailable (e.g. an import failure), read `memory/shadow_self_model.json` directly and used `targets.next_self_edit_focus` as `target_task_type` — which is passed straight into `_build_targeted_prompt(target_task_type, creativity)`, shaping what a real self-edit generation cycle actually targets. This is the one path that answers Phase 0's central question ("can `shadow_model.propose()` currently influence any live FeralEcho behavior?") with **yes**, via `propose_from_reflection()` (emergent_scheduler.py) → shadow file written → this fallback read → `target_task_type` set → real generation shaped. | Removed. The block now falls straight through from the empirical-signal check to the pre-existing `"coding"` default with no shadow read at all. Surrounding historical comment (documenting the 2026-09-05 priority-order fix and the 16.1% accuracy figure) was preserved and extended, not deleted, since it remains true and load-bearing context for *why* the empirical signal is checked first. |

**Test-only references:** none found. No test file (`test_*.py`, `*_test.py`, or any `scripts/verify_*.py`) references `shadow_model` or any of its functions.

**Documentation/historical references (left untouched, out of scope):** `CLAUDE.md`, `structure.md`, and a large number of `audits/*.md` research files (`2026-09-08_self_model_evidence_hierarchy.md`, `2026-09-08_persistent_self_model_DESIGN.md`, `2026-09-07_shadow_correction_validation_archaeology.md`, `2026-09-06_findings91_93_forensic_revalidation.md`, and roughly 45 others) mention Shadow narratively or as research subject matter. None of these were modified — they are historical/research artifacts describing Shadow's pre-retirement state and behavior, which remains accurate as history even after retirement, and per this mission's hard scope ("do not modify unrelated files," "do not perform broad cleanup") were left exactly as they were. `CLAUDE.md` in particular was deliberately not touched even though it hosts the project's actual documented precedent for `self_heal.py`'s retirement status — adding a matching entry there would be a reasonable follow-up but was not required to establish the retirement invariant itself, and is flagged in §8 as a candidate for a future, separately-scoped documentation pass rather than folded into this mission.

**Dead/ambiguous references:** none found.

---

## 4. Changes made

Four files, all in the repository's live tree (not the unrelated `.claude/worktrees/` copy):

1. **`app/core/shadow_model.py`** — module header only. Replaced the original short docstring with an explicit retirement notice (status, why, and revival conditions), preserving the original docstring text underneath for historical context. **No function body was changed, rewritten, or deleted.**
2. **`app/core/self_edit_manager.py`** — inside `perform_self_edit()`. Removed the shadow-file-read fallback block (the `if target_task_type is None: try: ... memory/shadow_self_model.json ...` block). Extended the pre-existing historical comment to document the retirement and why. The function now falls through directly from the empirical-signal check to the existing `"coding"` default.
3. **`app/maintenance/night_cycle.py`** — inside the nightly maintenance method. Removed the `try/except` block that called `log_accuracy()`/`check_and_correct()`. Replaced with a short comment documenting the retirement.
4. **`app/emergent_scheduler.py`** — inside the reflection-generation function. Removed the `try/except` block that called `propose_from_reflection()`. Replaced with a short comment documenting the retirement.

No other file was modified. No file was deleted. No test file was added (see §6 for why).

---

## 5. Retirement invariant

> **`shadow_model.propose()` is no longer consumed by any live production decision path.**

This claim is made only because verification in §6 actually establishes it — not asserted from the edit alone. More strongly than the minimum required claim: **no function in `shadow_model.py` is imported or called from any live production code path at all**, matching the mission's own Phase 5 requirement ("Live consumer: must be zero") and the self_heal.py precedent cited as the architectural model.

---

## 6. Verification

**Static verification (full-repo grep, run twice — once as initial archaeology, once post-edit to confirm the change):**
- Pre-edit: `grep -rn "shadow_model\|shadow_self_model\|shadow_accuracy\|shadow_corrections\|propose_from_reflection\|check_and_correct\|compare_to_actual\|log_accuracy" --include="*.py" .` found exactly 3 live call sites (§3) plus `shadow_model.py`'s own internal definitions.
- Post-edit: the identical grep shows every remaining match outside `shadow_model.py` is a plain comment (no `import`, no function call) in the three edited files; every match inside `shadow_model.py` is the module's own preserved implementation or the new retirement-notice comment block.
- A separate, targeted grep for `^\s*(import|from).*shadow_model` across every `.py` file in the repository returned zero matches outside `shadow_model.py` itself.
- A separate, targeted grep for the literal path strings `shadow_self_model.json` / `shadow_accuracy.jsonl` / `shadow_corrections.log` outside `shadow_model.py` returned only the two historical-comment mentions in `self_edit_manager.py` (both plain text inside a `#`-comment, not code).

**Deterministic AST verification** (stronger than textual grep — proves absence structurally, not just textually): a Python script parsed `app/core/self_edit_manager.py`, `app/maintenance/night_cycle.py`, and `app/emergent_scheduler.py` with `ast.parse()` and walked every `ast.Import`/`ast.ImportFrom` node in each file, filtering for any node naming `shadow_model`. Result for all three files: **`NONE`**.

**Runtime verification:**
- `app/core/shadow_model.py` was imported directly in the project's `feral_echo` conda environment. It imported cleanly, with all five functions (`propose`, `compare_to_actual`, `log_accuracy`, `check_and_correct`, `propose_from_reflection`) present and intact — confirming the preserved implementation still works as a standalone module.
- `app/core/self_edit_manager.py` was imported directly in the same environment (a real, heavy import — it triggered genuine FAISS/SentenceTransformer/tiktoken initialization, ~18.4s). It imported successfully with no error, and `"shadow_model" in dir(sem)` returned `False` — confirming no module-level binding to Shadow exists. (A substring check for `"shadow"` in `perform_self_edit`'s own source correctly returned `True` — this is the preserved historical/retirement *comment* text, not code; expected and not a regression, already established by the AST check above.)
- `night_cycle.py` and `emergent_scheduler.py` were **not** separately runtime-imported: the AST-level proof for these two files is already exhaustive and deterministic (it examines every import statement in the entire file, not just one execution path), and a second heavy runtime import — with its own real network calls and model loads — was judged unnecessary cost/risk for no additional evidentiary value. Documented here rather than silently skipped.

**Regression verification:** no pre-existing test file, `scripts/verify_*.py` script, or Liveness Ledger check references `shadow_model` (confirmed by grep — zero results). There was no existing narrow test suite to re-run. Per this mission's own scope discipline ("do not build the benchmark harness," "add tests only as necessary"), no new permanent test file was created; the static + AST + runtime checks above are the regression evidence for this change.

---

## 7. Preserved artifact

`app/core/shadow_model.py` remains in place, fully intact, at its original path. Every function body — `propose()`, `compare_to_actual()`, `log_accuracy()`, `check_and_correct()`, `propose_from_reflection()` — is byte-for-byte unchanged. Only the module's top-of-file header comment was extended with an explicit retirement notice; the original docstring content is preserved underneath it, not deleted. It is retained for two reasons: (1) it is the retained artifact a future dedicated investigation (§8) would need to actually re-run and inspect, and (2) deleting it would have destroyed the ability to answer the still-open question of *why* it performs below chance — which this mission was explicitly instructed not to investigate, but also not to foreclose.

`memory/shadow_self_model.json`, `memory/shadow_accuracy.jsonl`, and `memory/shadow_corrections.log` (the three data files Shadow read and wrote) were not touched, deleted, or modified by this mission — they remain on disk exactly as they were, real historical data available to whatever future investigation eventually runs.

---

## 8. Future investigation

**Open research question, deliberately not investigated in this mission:**

> Is Shadow's ~16.1% focus-match accuracy (2054 real entries; ~13.2% over the most recent 500) caused by a systematic/inversion/category-mapping defect that is diagnosable and fixable, or is it genuinely non-useful noise?

This mission did not attempt to answer this. Revival — re-wiring any live code to consume `shadow_model`'s output again — should require a new, dedicated, cheap investigation producing fresh evidence on this specific question, not a default action taken by momentum during an unrelated change. `app/core/shadow_model.py`'s own new header comment states this explicitly, so the constraint is visible to whoever next opens the file, not only recorded here.

**One adjacent, non-blocking observation, documented per this mission's own instruction to record rather than fix adjacent findings:** `CLAUDE.md`'s "Health Monitoring" section documents `self_heal.py`'s retirement status explicitly (the project's actual existing convention for this), but has no equivalent entry for `shadow_model.py`. Adding one would be a reasonable, low-risk follow-up — but doing so was judged unnecessary to establish this mission's required retirement invariant, and touching `CLAUDE.md` (a large, carefully-maintained institutional file, not itself part of the live decision paths this mission was scoped to) was left out of scope rather than done by momentum. Flagged here, not fixed.

---

## 9. Scope confirmation

This mission did **not**:
- redesign, refactor, or otherwise touch Council or candidate generation;
- implement deterministic verification/selection for anything;
- modify the evidence taxonomy work from earlier in this session;
- build the capability benchmark harness or any part of it;
- investigate *why* Shadow performs below chance;
- attempt to repair Shadow's accuracy;
- delete `app/core/shadow_model.py` or rewrite any of its function bodies;
- redesign self-model architecture (`self_model_updater.py`, `self_model_claims.py`, etc. — none were touched);
- change anything related to Q-001/Mechanism-B/the second-model cross-check idea;
- modify any production mechanism unrelated to Shadow's three consumer call sites;
- perform any broad cleanup beyond the four files directly required to establish the retirement invariant.

---

## Final response summary (per mission's required format)

1. **Report path:** `audits/2026-09-13_shadow_model_retirement.md`
2. **Starting Git HEAD:** `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f`
3. **Ending Git HEAD:** `e03f5984bb86d36ade51ed8f0753a3b8264c0f9f`
4. **Did Git HEAD change:** No.
5. **Number of files modified:** 4 — `app/core/shadow_model.py`, `app/core/self_edit_manager.py`, `app/maintenance/night_cycle.py`, `app/emergent_scheduler.py` (plus this one new report file).
6. **Were any unrelated files touched:** No. `git status --short` moved from 114 to 118 changed lines/files — exactly the 4 edits plus this 1 new report; every pre-existing entry in the working tree was confirmed untouched before editing began and again after.
7. **Complete list of live Shadow consumers found initially:** (a) `app/emergent_scheduler.py`'s reflection cycle, calling `propose_from_reflection()`; (b) `app/maintenance/night_cycle.py`'s daily maintenance cycle, calling `log_accuracy()`/`check_and_correct()`; (c) `app/core/self_edit_manager.py`'s `perform_self_edit()`, reading `memory/shadow_self_model.json` directly as a last-resort fallback for `target_task_type`. Only (c) influenced a real decision; all three were removed.
8. **Final verification result:** Zero live consumers remain, established at three independent layers — full-repo textual grep (post-edit), deterministic AST-level import inspection (all three former-consumer files, exhaustive per-file), and a real runtime import of both `shadow_model.py` and `self_edit_manager.py` in the production conda environment. All four edited files pass `ast.parse()` syntax checks.
9. **Unresolved ambiguity:** None regarding the retirement boundary itself — it is fully established. One open item outside this mission's scope is recorded in §8 (whether/when to add a matching `CLAUDE.md` retirement entry, deliberately not done here) and the pre-existing open research question (why Shadow performs below chance) remains exactly as open as it was before this mission, by design.
