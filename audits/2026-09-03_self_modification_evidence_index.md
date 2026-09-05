# Evidence Index — Echo Self-Modification Investigation Thread

Standalone reference companion to `audits/2026-09-03_self_modification_causal_chain.md`,
`audits/2026-09-03_self_edit_forensic_verification.md`, and
`audits/2026-09-03_apply_to_code_forensic_reconstruction.md`. Every row
is either a direct source-code citation (checked against current
working-tree content or a specific git blob) or a directly-reproduced
execution result from this investigation thread. No row is asserted from
memory or inference alone. **No production code was modified to produce
any evidence below.**

| ID | Claim | Evidence type | Exact location | Confidence | Notes |
|---|---|---|---|---|---|
| E01 | `apply_to_code` is the only automatically-invoked function from `self_edit_generated.py` | Exhaustive source grep | `self_edit_manager.py` (`_apply_self_edit_output`, `line 1701`); `liveness_ledger.py` (health-check read only) | High | Zero other call sites found anywhere in `app/` |
| E02 | 3,196 real `apply_to_code` invocations recorded | Direct file parse | `memory/apply_to_code_invocations.jsonl` | High | Schema uniform across all lines: `{ts, changed, before_len, after_len, error}` — no code content ever stored |
| E03 | 5 backup-recoverable implementations, all directly executed | Direct extraction + execution | `app/core/self_edit_backups/self_edit_20260813120335.py`, `self_edit_20260813175936.py`, `self_edit_20260823031936.py`, `self_edit_20260825011254.py`, `self_edit_20260826121324.py` | High | Live windows reconstructed from consecutive backup filenames |
| E04 | V1's `apply_to_code` produces `SyntaxError` on realistic input | Direct execution, `compile()` result | `self_edit_20260813120335.py:36-46`; test run this thread | High | Whole-line replacement (`'refactor_shorten_code_generation_v10'`/`'log_call'` matches → placeholder token) orphans indentation |
| E05 | V3's `apply_to_code` silently deletes every `import`/`from` line | Direct execution, output inspected | `self_edit_20260823031936.py:4-29` | High | Parses cleanly; guarantees `NameError` at first use of a stripped import |
| E06 | V4 (`apply_to_code = refactor_shorten_code_generation_v15`) is a decorator bound to the wrong contract | Direct execution + real log cross-check | `self_edit_20260825011254.py:17,29`; 322/322 real invocations logged `APPLY_TO_CODE_BAD_RETURN_TYPE` | High | Found via alias, not `def` — corrects the prior report's first-pass search method |
| E07 | V2/V5 timeouts occur during module import, not transformation logic | Direct timing, reproduced live | V2 logic: 1.57e-5s; V5 logic: 9.5e-7s; `import app.emergent_scheduler`: 7.08s (measured live, this session) | High | 2.0s sandbox budget vs. 7.08s real cold-import cost |
| E08 | Fitness-gate rejection condition is strict `<` (ties pass) | Direct source read | `app/core/self_edit_manager.py:2082` | High | `if candidate_quality < current_quality:` |
| E09 | Coding-task "quality" = raw AST structural-node count | Direct source read | `echo_quality_scorer.py:296-313` (`_ast_complexity`), `374-393` (dispatch) | High | Counts `If/For/While/ListComp/DictComp/SetComp/GeneratorExp/Try/With/AsyncFor/AsyncWith/IfExp/BoolOp` |
| E10 | All 25 currently-retained real deploys score a perfect 4/4 | Direct execution of the real scorer against each real file | `app/core/self_edit_backups/*.py` (25 files) | High | Complexity range 3-8, all ≥ the "4" threshold |
| E11 | Real self-edit success rate is 426/463 (92%), not 0/37 | Corrected grep methodology, direct recount | `memory/SELF_EDIT.log` | High | Prior audit's error: success-branch log line never records quality scores, only the rejection branch does |
| E12 | `non_convergent_streak` measures per-cycle name-count delta, not historical failure-to-converge | Direct source read + reproduced synthetic trace | `self_edit_manager.py:1045-1113`, esp. `1073-1074` | High | 10-cycle synthetic test: 9 tracked cycles, 9 distinct names, streak=0 every cycle |
| E13 | `self_edit_generated.py` is git-tracked with real history | Direct `git log` | 7 commits, `44e7a8e` (2026-06-28) → `65cdff5` (2026-07-21) | High | Extends recoverable history well beyond the 25-file backup rotation cap |
| E14 | Two historical implementations were structurally never invocable | Direct git blob read | commit `dd7849f` (`autonomous_self_edit`, wrong name); commit `6f337d6` (class-nested, wrong scope) | High | `getattr(module, "apply_to_code", None)` would return `None` for both |
| E15 | Commit messages independently corroborate this thread's re-derived failure patterns | Direct `git show` | commit `3ea69b3` ("253 of its last 254 invocations" NameError, one 2173→47-char corruption); commit `092186f` (class-nested hook calling nonexistent functions) | High | Written by earlier sessions with no knowledge of this investigation |
| E16 | Current live file contains a real, untriggered filesystem-write attempt | Direct content read | commit `65cdff5` = current `app/core/self_edit_generated.py:22-24` (`with open('temp_code.txt', 'w') ...`) | High | Not reachable — the containing function (not named `apply_to_code`) is never called |
| E17 | Flask's dev reloader is explicitly disabled | Direct source read | `run.py:1522` (`use_reloader=False`) | High | Rules out reload-on-file-change as a mechanism |
| E18 | Project-wide dynamic tool discovery scans `app/core` directly, live, on a recurring cadence | Direct source read | `run.py:1285` (startup, once); `app/autonomous_awareness.py:45,443` (`TOOLS_PATH = ".../app/core"`, every awareness cycle) | High | Confirmed via real call sites, not just the function's own definition |
| E19 | The discovery scan's skip-list does not exclude `app/core` or `self_edit_generated.py` | Direct source read | `app/core/awareness_tools_integration.py:42-51` | High | `SKIP_DIRS` only excludes `self_edit_backups`, `sandbox`, VCS/venv/build dirs |
| E20 | `ToolManager` is a genuine process-wide singleton | Direct source read | `app/core/tool_manager.py:10-17` (`__new__` override) | High | Confirms `awareness_tools_integration.py`'s `tm` and `echo_model_orchestrator.py`'s `_tm` are the same object |
| E21 | The only real consumer of the shared registry reads tool *names* only, never invokes a tool | Direct source read | `echo_model_orchestrator.py:1511-1515`; `tool_manager.py:23-24` (`list_tools` returns `list(self.tools.keys())`) | High | Feeds a plain-text "TOOL-LIST" system note, nothing else |
| E22 | No code anywhere calls `.get_tool(name).func(...)` for a dynamically-registered tool | Exhaustive project-wide grep | (confirmed absence) | High | Checked across all of `app/` and `run.py`, excluding plan-text files |
| E23 | The real conversational tool-dispatch path uses a separate, small, hardcoded tool set | Direct source read | `app/core/echo_tool_dispatch.py:302-350` (`_execute_tool`, if/elif on a fixed name set) | High | Structurally disconnected from `ToolManager`'s dynamic registry |
| E24 | References to `__import__`/`eval`/tool-registration wiring for self-edit are proposed plans, not executed code | File-type and content inspection | `app/core/self_edit_plans/*.txt` (dozens of files) | High | Natural-language/pseudocode planning output, not `.py` source; inconsistent function names across attempts consistent with per-cycle hallucination, not a stable design |
| E25 | `self_edit_convergence.json` feeds `compute_salience()` — a real but numeric-only bridge | Direct source read | `app/core/echo_core.py:561` (`_SALIENCE_CONVERGENCE_PATH`) | Medium | Real, pre-existing (Emergence-roadmap) mechanism; carries a streak *count*, not self-edit's generated code, to `emergent_scheduler.py`'s prompt-weighting |
| E26 | No crontab or filesystem watcher targets `self_edit_generated.py` | Direct commands run this session | `crontab -l` → empty; `start_echo.sh` read directly (crash-restart only, no file-change trigger) | High | |
| E27 | ~1,471 of 3,196 real invocations (pre-2026-07-14) are permanently unrecoverable | Timestamp comparison | `memory/apply_to_code_invocations.jsonl` earliest entry (2026-07-14 18:33:33) vs. earliest recoverable code (git commit `44e7a8e`, 2026-06-28, defines no hook at all) | High | States a genuine boundary of recoverable evidence, not a claim about what happened in that window |
| E28 | `_recent_outcome_note()` is a real, working feedback mechanism, built on the already-proven-broken quality metric | Direct source read | `self_edit_manager.py:2636-2667` | High | Reads `self_edit_outcome_tracker.get_outcomes_summary()`, folds a delta-based note into the next prompt's Focus-text |

---

**Coverage note**: this index does not repeat every minor observation
from the three underlying reports verbatim — it captures every claim
load-bearing enough to affect this thread's executive conclusions. For
narrative context behind any row, follow the "Exact location" column
back into the relevant report.
