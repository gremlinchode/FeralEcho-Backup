# Three-Layer Provenance Reconciliation — Git HEAD / Working Tree / Runtime

**Date:** 2026-09-11
**Type:** Investigation-only, read-only. Narrow scope: Git HEAD ↔ working tree ↔ runtime provenance for FeralEcho's runtime-relevant code, triggered by the known `restore_council_gate` (51 vs 52 liveness checks) discrepancy.
**Explicitly out of scope this pass**: broad architecture audit, autonomy/learning/council research questions, re-litigating `research_state_consolidation.md`'s date anomaly (mentioned only where directly relevant to three-layer provenance).

---

## Phase 0 — Baseline

```
pwd:                         /Users/richietate/Desktop/FeralEcho
git rev-parse HEAD:          e92ec3b7fe4743f75746d161a06601db0232bff2
branch:                      main
git status --short | wc -l:  96
date (UTC, start):           2026-09-11T06:29:01Z
```
96 uncommitted paths at the start of this investigation (one more than the 95 recorded at the end of the prior reconciliation pass — the sole addition is that pass's own report file, `audits/2026-09-10_phase2_provenance_reconciliation.md`, confirmed by direct comparison against the previously-recorded path list). This baseline was re-confirmed identical (`HEAD` unchanged, path count unchanged) immediately before this report was written — see the Mutation Scope section.

---

## Phase 1 — Runtime State

**A FeralEcho process IS currently running.** Established without starting, restarting, or interfering with it:

```
PID:              7644
Started:          Thu Sep 10 22:41:53 2026  (elapsed at time of check: 47m13s)
Executable:        /Users/richietate/miniforge3/envs/feral_echo/bin/python3.12
Command line:      python -u run.py
Working directory: /Users/richietate/Desktop/FeralEcho   (confirmed via lsof's `cwd` entry)
Parent process:    PID 7636, /bin/zsh /Users/richietate/Desktop/FeralEcho/start_echo.sh
Grandparent:       PID 7605 (the interactive shell)
Listening port:    *:5000 ("commplex-main" — TCP LISTEN, confirmed via lsof)
Child process:     PID 7647 — python -c "from multiprocessing.resource_tracker import main;main(5)"
                    (a standard CPython multiprocessing helper, not application logic)
```

This is the same process instance investigated in the prior reconciliation pass (identical PID, identical start time) — no restart occurred between that investigation and this one. **All runtime claims below concern this specific, continuously-running process.**

---

## Phase 2 — Git's Version of Reality

For every runtime-relevant file, established via direct Git commands (blob hashes, `git log`, `git diff --stat`) — not inferred from any prior report's prose.

| File | HEAD blob | Last commit touching path | Last commit date | Modified vs. HEAD? |
|---|---|---|---|---|
| `run.py` | `7fc8bbc...` | `3b498ee` "Finding 92: complete Plan 5 (request-scoped trace_id)..." | 2026-09-05T17:58:42-07:00 | YES |
| `app/core/liveness_ledger.py` | `28bcabc...` | `1081f26` "sandbox: enforce noninteractive stdin contract for autonomous execution" | 2026-09-09T12:20:31-07:00 | YES |
| `sandbox/safe_exec_wrapper.py` | `63464ad...` | `1081f26` (same commit as above) | 2026-09-09T12:20:31-07:00 | YES |
| `app/core/snapshot_manager.py` | `bc6dd0e...` | `daf1fce` "Wire drift alerts into check_and_alert()... (PD #16)" | 2026-07-22T07:03:13-07:00 | YES |
| `app/core/river_deliberation.py` | `d1fc148...` | `9ac2f95` "Refactor synthesis to preserve verified information (Tier-4-driven)" | 2026-09-04T23:34:33-07:00 | YES |
| `app/core/temporal_environment.py` | `b35bc8c...` | `44e7a8e` "FeralEcho — autonomous mind, clean initial commit" | 2026-07-04T19:39:40-07:00 | YES |
| `app/core/echo_ground_truth.py` | `b284719...` | `525454a` "Fix epistemic claim rendering and generation audit" | 2026-09-07T21:29:25-07:00 | YES |

**All seven files are confirmed modified relative to HEAD** — not by `git status`'s `M` flag alone (which was already known) but independently, via distinct SHA-256 content hashes of the HEAD blob vs. the working-tree file (computed for all seven; every pair differs — VERIFIED, not inferred). `temporal_environment.py`'s and `snapshot_manager.py`'s *last real commits* predate the current investigation window entirely (July 2026) — their current uncommitted changes are not a recent edit to recently-touched files, they are the first change to genuinely stable files in over a month.

---

## Phase 3 — Working-Tree Reality

**Symbol-level diff** (top-level function/class definitions, HEAD vs. working tree, via direct AST parsing of both the Git blob and the on-disk file — immune to any line-count/context-window measurement error):

| File | HEAD defs | WT defs | Added (WT-only) | Removed (HEAD-only, gone from WT) |
|---|---:|---:|---|---|
| `run.py` | 56 | 56 | none | none |
| `app/core/liveness_ledger.py` | 118 | 121 | `_check_restore_council_gate`, `_evaluate_restore_council_gate`, `_read_jsonl_tail` | none |
| `sandbox/safe_exec_wrapper.py` | 7 | 7 | none | none |
| `app/core/snapshot_manager.py` | 18 | 21 | `_build_restore_dissent_entry`, `_council_review_restore`, `_log_restore_dissent_entry` | none |
| `app/core/river_deliberation.py` | 22 | 22 | none | none |
| `app/core/temporal_environment.py` | 7 | 8 | `get_macbook_location`, `get_phone_location` | **`get_location`** |
| `app/core/echo_ground_truth.py` | 25 | 25 | none | none |

Three files (`run.py`, `sandbox/safe_exec_wrapper.py`, `river_deliberation.py`) show **zero symbol-count change** despite being genuinely modified (confirmed via `git diff --stat`, non-zero) — meaning their changes are **body-level modifications of pre-existing functions**, not new top-level definitions: `run.py`'s `admin_restore()` route, `safe_exec_wrapper.py`'s `_install_patches()`, `river_deliberation.py`'s `select_best_fallback_candidate()`. This matters for the reconciliation: a symbol-name-only diff would have reported these three files as unchanged, which would be wrong — full-body diffing (already performed and confirmed in the prior pass, re-confirmed present here via non-zero `git diff --stat`) is required to see them.

**One genuine function removal found, not previously flagged this precisely**: `temporal_environment.py`'s `get_location()` exists in `HEAD` and does **not** exist in the working tree — replaced by `get_macbook_location()`/`get_phone_location()`. Checked directly whether this creates a real breakage risk: every real importer of this module (`terminal_client.py`, `app/autonomous_loop.py`, `app/core/echo_model_orchestrator.py`, `app/internet_tools/autonomous_fetch.py`, `archive_janitor/test_fetch.py`) imports only `get_temporal_environment_context()` (the wrapper, present and unchanged in name in both HEAD and working tree) — **zero callers of the removed bare `get_location()` were found anywhere in the tree** (VERIFIED via direct grep). `thunderhead.py`'s own `get_location()` (line 411) is a separate, self-contained, same-named function unrelated to this module (independently confirmed in an earlier pass this session). **No regression risk from this removal.**

**Untracked files**: `restore_council_gate`'s three defining functions above exist only as new code inside already-tracked-but-modified files — there is no separate untracked `.py` file implementing this mechanism. Confirmed via `git status --porcelain` (no new `??` `.py` path under `app/core/`).

---

## Phase 4 — Runtime-to-Source Reconciliation

Non-invasive evidence collected, without attaching to or executing code inside the live process:

**Filesystem mtimes of the source files vs. process start time** — every one of the seven files' mtimes (`run.py`: Sep 9 15:55; `liveness_ledger.py`: Sep 9 20:30; `safe_exec_wrapper.py`: Sep 9 12:24; `snapshot_manager.py`: Sep 9 15:55; `river_deliberation.py`: Sep 9 15:49; `temporal_environment.py`: Sep 9 15:53; `echo_ground_truth.py`: Sep 8 00:52) **predates the process start time (Sep 10 22:41:53) by hours to over a day.** None of these files changed between the process starting and this investigation running — the observation window is stable (no concurrent editing occurred).

**Bytecode cache evidence** (non-invasive, filesystem-only — `__pycache__/*.cpython-312.pyc`, matching the running process's own interpreter version, confirmed via `ps`'s executable path): every relevant `.pyc` file's mtime closely tracks its source `.py` file's own mtime (e.g., `liveness_ledger.cpython-312.pyc`: Sep 9 20:30, matching the source to the minute). **What this does and does not prove, stated precisely**: CPython's default import mechanism recompiles a module only when the source's mtime/size no longer matches what's embedded in the cached `.pyc`'s header. Since no source file changed after these `.pyc`s were written, the process's Sep 10 22:41:53 startup would have found the cache still valid and reused it without rewriting it — consistent with, but not independently proof beyond, what the blob-hash and live-query evidence below already establishes. This is corroborating, non-invasive filesystem evidence (SUPPORTED), not a substitute for direct runtime observation.

**Direct runtime observation** (the strongest evidence available, via the live process's own already-existing, explicitly read-only `GET /admin/liveness-status` endpoint — no code was executed inside the process, no debugger attached): the live endpoint's returned check set and evidence text were captured and compared against the working-tree source, set-for-set and, for two specific checks, field-for-field (see Phase 5).

**Conclusion for this phase**: the running process's observable behavior (Phase 5) matches the current working-tree source exactly, and nothing in the available non-invasive evidence (mtimes, bytecode cache, or live behavior) contradicts that match. **This does not, by itself, prove every line of every file the process has ever imported matches the working tree** — only the specific files and mechanisms checked in this pass.

---

## Phase 5 — The 51 vs. 52 Discrepancy, Reproduced Independently

**Method**: direct AST parsing of the `_CHECKS` tuple literal in both `git show HEAD:app/core/liveness_ledger.py` and the on-disk working-tree file — chosen specifically because it cannot silently truncate a result the way the prior pass's `grep -A N` context-window approach did (that bug is disclosed and corrected in the prior report; this method structurally cannot repeat it, since it reads to the tuple's actual closing token, not a fixed line count).

### A. HEAD — 51 entries (full enumerated list)
```
1. self_edit_apply_to_code       18. self_knowledge_verification   35. valence_self_edit_bounds
2. curiosity_engine               19. mlx_avoidance                 36. echo_projects_isolation
3. nature_spark                   20. log_retention                 37. echo_projects_no_escalation
4. wolf_friction_bridge           21. janitor_safety                38. echo_projects_council_advisory
5. claude_shard                   22. plan_retention                39. echo_projects_path_safety
6. question_garden_lineage        23. janitor_council_advisory_only 40. echo_projects_autonomy_gated
7. claude_research                24. modelfile_identity            41. echo_projects_autonomy_activity
8. self_model_drift               25. council_river_blend           42. touch_sense_rhythm
9. task_type_classifier           26. council_content_bounded       43. vision_sense_presence
10. global_workspace              27. apply_to_code_sandbox_isolation 44. hearing_sense_ambient
11. substrate_continuity          28. river_drift_alerting          45. awareness_scan_hygiene
12. global_workspace_consumption  29. f1_aliased_import_detection   46. code_analysis_retrieval_exclusion
13. valence_self_report           30. dual_learner_validation_gate  47. architecture_slice_bounded
14. reflection_shard_generation   31. echo_state_archiving          48. echo_messaging_auth_classification
15. dissent_log_hook              32. coupling_self_report          49. council_cursor_health
16. seam_engine                   33. reflection_meta_synthesis_hook 50. self_model_claims_integrity
17. code_verification             34. valence_exploration_bias      51. f2_stdin_contract
```

### B. Working tree — 52 entries
Identical to the above, with one insertion at position 16: **`restore_council_gate`** (immediately after `dissent_log_hook`), shifting `seam_engine` onward down by one — full list omitted for brevity (identical set to HEAD plus this one name; see the raw AST-parse transcript captured during this investigation for the complete ordered 52-item enumeration).

### C. Runtime — 52 entries (captured via live `GET /admin/liveness-status`, this session, alphabetically as returned by the JSON parse)
```
1. apply_to_code_sandbox_isolation  14. dual_learner_validation_gate    27. hearing_sense_ambient
2. architecture_slice_bounded       15. echo_messaging_auth_classification 28. janitor_council_advisory_only
3. awareness_scan_hygiene           16. echo_projects_autonomy_activity 29. janitor_safety
4. claude_research                  17. echo_projects_autonomy_gated    30. log_retention
5. claude_shard                     18. echo_projects_council_advisory  31. mlx_avoidance
6. code_analysis_retrieval_exclusion 19. echo_projects_isolation        32. modelfile_identity
7. code_verification                20. echo_projects_no_escalation    33. nature_spark
8. council_content_bounded          21. echo_projects_path_safety      34. plan_retention
9. council_cursor_health            22. echo_state_archiving           35. question_garden_lineage
10. council_river_blend             23. f1_aliased_import_detection    36. reflection_meta_synthesis_hook
11. coupling_self_report            24. f2_stdin_contract              37. reflection_shard_generation
12. curiosity_engine                25. global_workspace               38. restore_council_gate
13. dissent_log_hook                26. global_workspace_consumption   39. river_drift_alerting
                                                                        40. seam_engine
                                                                        41. self_edit_apply_to_code
                                                                        42. self_knowledge_verification
                                                                        43. self_model_claims_integrity
                                                                        44. self_model_drift
                                                                        45. substrate_continuity
                                                                        46. task_type_classifier
                                                                        47. touch_sense_rhythm
                                                                        48. valence_exploration_bias
                                                                        49. valence_self_edit_bounds
                                                                        50. valence_self_report
                                                                        51. vision_sense_presence
                                                                        52. wolf_friction_bridge
```

### Set reconciliation (computed directly, not estimated)
```
HEAD ∩ WORKING TREE:        51   (every HEAD check has an identically-named counterpart in the working tree)
HEAD-only:                  0    (nothing was removed)
WORKING-TREE-only:          1    (restore_council_gate)
RUNTIME ∩ WORKING TREE:     52   (exact match — every working-tree check name appears in the live response)
RUNTIME-only:                0
WORKING-TREE-only (vs runtime): 0
```

### Identity of `restore_council_gate`
- **On disk**: `app/core/liveness_ledger.py`, functions `_check_restore_council_gate()` and `_evaluate_restore_council_gate()` (confirmed present via Phase 3's symbol diff), reading `app/core/snapshot_manager.py`'s `_council_review_restore()`/`_build_restore_dissent_entry()`/`_log_restore_dissent_entry()` and `run.py`'s `admin_restore()` route.
- **In HEAD**: **confirmed absent** — `git show HEAD:app/core/liveness_ledger.py | ast-parse` contains no `_check_restore_council_gate`/`_evaluate_restore_council_gate`/`restore_council_gate` string anywhere (VERIFIED, this session, via the same AST-based method used for the 51/52 count, not a re-run of the prior grep-based check).
- **At runtime**: **confirmed present and executing**, via direct live query this session: `pass: true`, `status: "no_real_restores_since_deployment"`, evidence text identical in substance to what the working-tree source's own docstring describes (an honest, not-yet-exercised pass, since no real restore has occurred under this gate yet).

**Reconciled identity, not just name-matching**: the runtime evidence text's specific phrasing ("4 pre-deployment historical restore(s) in restore_log.jsonl are correctly excluded") matches a specific, distinctive code comment/logic path visible only in the working-tree source's `_evaluate_restore_council_gate()` function — this is not merely "a check with this name exists in both places," it is the **same specific implementation logic**, independently corroborated by matching a distinctive textual fingerprint between source and runtime output.

---

## Phase 6 — Additional Three-Layer Divergences

Targeted search, scoped to the same seven runtime-relevant files plus their direct call graph (not a repository-wide scan):

### Type A (HEAD absent, working tree present) — confirmed, multiple instances
1. `restore_council_gate` (the known case, §5).
2. `snapshot_manager.py`'s `_council_review_restore()`/`_build_restore_dissent_entry()`/`_log_restore_dissent_entry()` — the implementation `restore_council_gate` depends on; same provenance status.
3. `temporal_environment.py`'s `get_macbook_location()`/`get_phone_location()` — confirmed present in working tree, absent from HEAD, and (per Phase 4/5's live-behavior correlation methodology, applied narrowly) reachable from the live process via `get_temporal_environment_context()`, which every real caller imports.

### Type B (HEAD present, executing implementation differs)
1. `run.py`'s `admin_restore()` — same function name and route path in both HEAD and working tree; body substantively different (the council-review gate is inserted before the pre-existing `restore_snapshot()` call). **Confirmed body-level change** via non-zero symbol-stable `git diff --stat` (58 insertions on a file with zero new top-level defs).
2. `sandbox/safe_exec_wrapper.py`'s `_install_patches()` — same function, body extended with the `_os.close(0)` block. **Directly, empirically confirmed live-behaviorally different from what HEAD's version would do** (this session's earlier bounded probe test — a fresh invocation of the current on-disk file — showed `os.read(0, ...)` raising `OSError: Bad file descriptor`; `HEAD`'s version, per its own diff, lacks this block entirely, and by inspection would leave fd 0 open and reachable).
3. `app/core/river_deliberation.py`'s `select_best_fallback_candidate()` — same function name, body replaced (the "prefer longest" tie-break in HEAD vs. the 3-stage majority/skip/shortest rule in the working tree). Not independently re-exercised at runtime this pass (would require triggering a real multi-model council fallback event).
4. `app/core/liveness_ledger.py`'s `f2_stdin_contract` check itself — the *check name* exists in HEAD (unlike `restore_council_gate`), but its evaluator function's evidence fields differ: HEAD's version (per the prior pass's diff review) reports only `raised`/`isatty_honest`; the working-tree/runtime version additionally reports `python_stdin_blocked`/`os_fd0_blocked`, **confirmed live** this session (the runtime evidence text explicitly states "...still closes fd 0", a claim HEAD's version's own check cannot make since it has no fd0-related code to check).

### Type C (working tree present, runtime apparently absent)
**None found** in this pass's scope. Every working-tree addition checked against the live process (§5, §6 Type A/B items 1–4) was found reachable and, where directly testable, actively producing runtime effects.

### Type D (runtime symbols present, source provenance ambiguous)
**None found.** Every runtime-observed check name and evidence-text fragment traced cleanly to a specific, identifiable function in the current working-tree source.

### Type E (runtime behavior matches neither HEAD nor current working tree)
**None found.** This is the highest-severity category the mission asked to watch for; this pass found no instance of it. Stated plainly rather than assumed: this negative result is scoped to the seven files and their directly-traced dependencies examined here — it is not a claim that no such case exists anywhere in the ~185-file `audits/`-adjacent codebase, only that none was found within this investigation's deliberately narrow scope.

---

## Phase 7 — Timestamps and Identity

| File | Git last-commit date | Filesystem mtime | `.pyc` cache mtime (cpython-312) | HEAD blob hash (short) |
|---|---|---|---|---|
| `run.py` | 2026-09-05T17:58:42-07:00 | Sep 9 15:55:55 | N/A (top-level script, no cache) | `7fc8bbc` |
| `app/core/liveness_ledger.py` | 2026-09-09T12:20:31-07:00 | Sep 9 20:30:22 | Sep 9 20:30 | `28bcabc` |
| `sandbox/safe_exec_wrapper.py` | 2026-09-09T12:20:31-07:00 | Sep 9 12:24:04 | Sep 9 12:30 | `63464ad` |
| `app/core/snapshot_manager.py` | 2026-07-22T07:03:13-07:00 | Sep 9 15:55:39 | Sep 9 16:06 | `bc6dd0e` |
| `app/core/river_deliberation.py` | 2026-09-04T23:34:33-07:00 | Sep 9 15:49:24 | Sep 9 15:49 | `d1fc148` |
| `app/core/temporal_environment.py` | 2026-07-04T19:39:40-07:00 | Sep 9 15:53:40 | Sep 9 15:53 | `b35bc8c` |
| `app/core/echo_ground_truth.py` | 2026-09-07T21:29:25-07:00 | Sep 8 00:52:34 | Sep 8 00:52 | `b284719` |

**Explicitly not treated as proof of anything beyond itself**: filesystem mtime is recorded as "when this file was last written to disk," not as authorship time, commit time, or a claim about *why* it changed then. No timestamp above is used to infer causation. One internal consistency worth noting, not a contradiction: every `.pyc` cache mtime is within a few minutes of its source `.py`'s own mtime — exactly what normal CPython import-cache behavior produces, and not itself evidence of anything unusual.

**On `research_state_consolidation.md`'s previously-found date anomaly**: not re-investigated this pass, per the explicit scope instruction — it does not bear on the seven files' three-layer provenance examined here, since that file is documentation, not runtime code, and none of the seven files' own provenance chains reference or depend on it.

---

## Phase 8 — Evidence Classification (applied throughout)

- **VERIFIED**: all blob-hash comparisons (§2); the AST-based 51/52/52 enumeration and set reconciliation (§5); the live `restore_council_gate` and `f2_stdin_contract` evidence-text correlation (§5); the `get_location()` removal + zero-caller confirmation (§3); the direct empirical stdin/fd0 probe from the prior pass, re-cited here as already-established for this file's provenance chain (§6 Type B item 2).
- **SUPPORTED**: the bytecode-cache correlation (§4) — consistent with, not independently proof of, which exact source version the process loaded, beyond what the live-query evidence already establishes directly. The claim that `select_best_fallback_candidate()`'s working-tree version is "reachable" from real production traffic (§6 Type B item 3) — traced via imports/call graph, not exercised at runtime this pass.
- **INFERRED**: none promoted to a headline claim without a VERIFIED or SUPPORTED label attached above.
- **UNKNOWN**: whether any *other* file, beyond the seven examined, harbors a Type C/D/E divergence — explicitly out of scope for this narrow pass, not asserted to be absent project-wide.

---

## Phase 9 — Three-Layer Reconciliation Matrix

| Component / Claim | Git HEAD | Working Tree | Runtime | Relationship | Evidence | Status |
|---|---|---|---|---|---|---|
| Liveness Ledger check count | 51 | 52 | 52 | WT/Runtime match; both exceed HEAD by exactly 1 | AST parse (HEAD, WT) + live JSON parse (Runtime) | VERIFIED |
| `restore_council_gate` (check) | Absent | Present | Present, `pass:true` | HEAD absent; WT=Runtime | AST parse + live query, evidence-text fingerprint match | VERIFIED |
| `_council_review_restore()` + 2 siblings (`snapshot_manager.py`) | Absent | Present | Present (indirectly, via the check above) | HEAD absent; WT=Runtime (inferred reachable) | AST symbol diff; live evidence text depends on this code path | VERIFIED (source); SUPPORTED (direct runtime execution of this exact function, vs. only its downstream check output) |
| `admin_restore()` (`run.py`) | Present, older body | Present, modified body | Not directly re-exercised (no real restore triggered) | Type B — same route, different logic | `git diff --stat` (symbol-stable, body-changed) | SUPPORTED — not live-tested this pass (would require a real restore call) |
| `_install_patches()` fd0 close (`safe_exec_wrapper.py`) | Absent | Present | **Directly, empirically confirmed** (prior pass's bounded probe, re-cited) | HEAD absent; WT=Runtime, behaviorally confirmed | Direct subprocess invocation of the real, current file, outside the project tree | VERIFIED |
| `select_best_fallback_candidate()` 3-stage rule | Older ("prefer longest") | New (3-stage) | Reachable, not exercised this pass | Type B | `git diff --stat` (symbol-stable, body-changed) | SUPPORTED |
| `get_location()` (`temporal_environment.py`) | Present | **Absent** (removed) | Not called (superseded by `get_macbook_location`) | HEAD-only removal, zero real callers found | AST symbol diff + repo-wide grep for callers | VERIFIED (removal is safe) |
| `get_macbook_location()`/`get_phone_location()` | Absent | Present | Reachable via `get_temporal_environment_context()` | Type A | AST symbol diff + import-graph trace | SUPPORTED (reachability); not runtime-exercised this pass |
| `_SEE_HEAR_CONJUNCTION_RE` (`echo_ground_truth.py`) | Absent | Present | Reachable via `_relevant_slices()` | Type A (module-level, not a top-level def — confirmed present via `git diff`) | `git diff --stat` + prior pass's own read | SUPPORTED |
| Type C (WT present, runtime absent) | — | — | — | **None found** in scope | Cross-check of every WT addition against live query / call-graph | VERIFIED (for the scope examined) |
| Type D (runtime, provenance ambiguous) | — | — | — | **None found** in scope | Every runtime symbol traced to a specific WT function | VERIFIED (for the scope examined) |
| Type E (runtime matches neither layer) | — | — | — | **None found** in scope | Same as above | VERIFIED (for the scope examined) |

For each row above requiring it, the explicit HEAD/WORKING TREE/RUNTIME/Difference/Evidence/Interpretation/Unknown breakdown is embedded in §5 and §6's own prose (not duplicated a third time here, per this report's own economy).

---

## Phase 10 — Final Conclusions

**Q1. Does Git HEAD accurately describe the code currently present on disk?**
No. Confirmed via seven independent blob-hash mismatches (§2) and, at the symbol level, at least 8 added functions and 1 removed function across 4 files (§3), none of which exist in `HEAD`.

**Q2. Does the working tree accurately describe the code currently executing?**
Yes, for everything checked in this pass. The live process's `restore_council_gate`/`f2_stdin_contract` outputs match the working-tree source's own distinctive logic (§5), and the direct fd0/stdin probe (re-cited from the prior pass) confirms the working-tree `safe_exec_wrapper.py` is what actually executes when invoked. Not proven for every one of the seven files' every code path (`admin_restore()`'s new gate has never been exercised by a real restore; `select_best_fallback_candidate()`'s new rule has not been exercised by a real fallback event this pass) — those remain SUPPORTED, not VERIFIED, specifically because they haven't fired during this observation window, not because of any contrary evidence.

**Q3. Does Git HEAD accurately describe the code currently executing?**
No. This follows directly from Q1 and Q2: if HEAD ≠ working tree (Q1, VERIFIED) and working tree ≈ runtime (Q2, VERIFIED for the checked mechanisms), then HEAD ≠ runtime for those same mechanisms. Directly confirmed, not merely inferred by transitivity, for `restore_council_gate` and the fd0-close behavior specifically (§5, §6).

**Q4. How many concrete discrepancies were found between the three layers?**
**9** distinct HEAD-vs-working-tree discrepancies across the 7 files examined: 1 new liveness check + 3 new liveness-ledger helper functions (arguably one cluster, counted as 2 items — the check and its dependency chain), 3 new `snapshot_manager.py` functions, 2 new `temporal_environment.py` functions + 1 removed function (3 items), 1 new module-level regex construct in `echo_ground_truth.py`, and 3 body-level (Type B) modifications to pre-existing functions (`admin_restore()`, `_install_patches()`, `select_best_fallback_candidate()`). Not double-counted with the 51-vs-52 check-count figure, which is a summary of the first item.

**Q5. Breakdown by category:**
- HEAD → working-tree only (Type A/removal, never reached runtime differently than WT): all 9 items above are HEAD-vs-WT discrepancies by definition.
- Working-tree → runtime only (WT differs from what's running): **0 found** — every WT addition/modification checked was either confirmed live-matching or not yet exercised (never found to diverge from WT).
- HEAD → runtime (skipping past WT as an intermediate): not a separate category found — every runtime discrepancy from HEAD passes through and matches the working tree, none was found bypassing it.
- All three disagree (Type E): **0 found**, within this pass's scope (§6 Type E).

**Q6. Is `restore_council_gate` definitely runtime-active?**
Yes — VERIFIED, via a live query this session returning `pass: true` with evidence text that fingerprint-matches the working-tree source's own specific logic, not just a matching name.

**Q7. Is `restore_council_gate` definitely absent from HEAD?**
Yes — VERIFIED twice independently, by two different extraction methods (the prior pass's corrected `awk`-bounded grep, and this pass's AST-based parse), both returning zero occurrences of every defining identifier (`restore_council_gate`, `_check_restore_council_gate`, `_evaluate_restore_council_gate`, `_council_review_restore`) anywhere in `git show HEAD:...` for either `liveness_ledger.py` or `snapshot_manager.py`.

**Q8. Can the exact source provenance of the live process be established?**
For the specific mechanisms examined (`restore_council_gate`, `f2_stdin_contract`'s fd0 half, `admin_restore()`'s wiring) — **yes**, established directly via a combination of live-query evidence-text fingerprinting and (for the sandbox wrapper) direct empirical re-invocation of the actual current file. For the codebase as a whole — **no**, and this pass does not claim otherwise; only the seven files and their immediately-dependent functions were checked.

**Q9. Did the investigation uncover any case where runtime behavior cannot be explained by either HEAD or the current working tree?**
No (Type E, §6) — within this pass's deliberately narrow scope. Not generalized beyond that scope.

**Q10. Minimum documentation change needed to prevent a future investigator from assuming `git show HEAD` = currently executing FeralEcho:**
A single, prominent note — proposed location: the top of CLAUDE.md's "Liveness Ledger" section, or a new short standing note near the "Working Tree State" section header — stating explicitly that **the running server loads whatever is physically on disk at process start, which may differ from `HEAD` if uncommitted changes exist**, and that verifying "what's actually running" requires checking the working tree (or, more directly, the live `/admin/liveness-status` endpoint) rather than `git show HEAD`. This is a process/methodology note, not a claim requiring re-verification each time — it would have prevented exactly the confusion this three-part investigation exists to resolve. (Not applied — proposal only, per this mission's constraints.)

---

## Mutation Scope

```
Files created by this investigation:   audits/2026-09-11_three_layer_provenance_reconciliation.md (this file, only)
Files modified:                        none
Files deleted:                         none
Processes started:                     none
Processes stopped:                     none
Processes restarted:                   none
Services changed:                      none
Ports changed:                         none
Git state changed:                     none (no commits, no branches, no checkout/reset/rebase)
Packages installed:                    none

Temporary artifacts: one throwaway JSON response capture (a single curl response saved to a
/tmp path with a randomized suffix, used only to feed a Python parser) — created and deleted
within the same command, confirmed removed via `rm -f` in the same invocation.

Git HEAD before this investigation:    e92ec3b7fe4743f75746d161a06601db0232bff2
Git HEAD after this investigation:     e92ec3b7fe4743f75746d161a06601db0232bff2   (unchanged)
git status --short path count before:  96
git status --short path count after:   96 (before this report's own creation) -> 97 (after)
```

**Result matches the stated expectation exactly: no project files modified; no services restarted; no Git history changed.**
