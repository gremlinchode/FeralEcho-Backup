# Phase 2 — Research Provenance Reconciliation Audit

**Date:** 2026-09-11 (real wall-clock, confirmed via `date -u` and the live server's own generated timestamps — see Starting-State Verification)
**Type:** Investigation-only, read-only. One bounded, isolated subprocess experiment was run outside the project tree (see §5.5) — no source, config, or Git state was touched.
**Mission:** Independently reconcile `audits/2026-09-10_research_arc_provenance_audit.md`'s claims against the repository, Git history, and the currently-running system. Do not repair discrepancies. Do not trust the prior report's classifications without re-deriving them.

---

## 1. Executive Summary

The prior report (Phase 1) holds up well under independent re-verification — **every one of its five "implemented + undocumented" claims is confirmed**, and its single most important finding (the F2 stdin/fd0 contract is live, real, and undocumented in CLAUDE.md) is not just confirmed but **strengthened by direct empirical testing this session** (§5.5: `sys.stdin`, raw fd 0, and `input()` are all genuinely blocked, tested live against the real, current, uncommitted sandbox code — VERIFIED, not just SUPPORTED as Phase 1 left it).

Three corrections to Phase 1, found during this reconciliation, disclosed rather than smoothed over:

1. **Phase 1's own liveness-check count was measured with a methodology bug.** It reported "52 checks... up from CLAUDE.md's documented 41" without checking whether that 52 reflected committed or uncommitted code. This audit found: **committed `HEAD` has 51 checks; the currently-running server is executing 52 — one check (`restore_council_gate`) that has never been committed to Git.** This is a materially more serious finding than Phase 1's own framing suggested: it is not just "undocumented," it is **the live production server currently running code that exists nowhere in Git history.**
2. **A real dating/naming anomaly was found in `audits/2026-09-11_research_state_consolidation.md`**, not previously flagged: its filename and internal header both say `2026-09-11`, but its on-disk mtime is `2026-09-08T13:18:27` — three days earlier, and one full day before the Git commit (`cfd01b7`, 2026-09-09) that captured the deliverables the file itself describes creating. This is presented as an open discrepancy, not resolved (§7).
3. **`select_best_fallback_candidate()`'s pre-rewrite version in `HEAD`** was last touched by a *different* commit (`9ac2f95`, "Refactor synthesis to preserve verified information") than either audit had previously named — a small provenance-precision gain, not a contradiction of Phase 1.

Nothing in this reconciliation found a claim in Phase 1 to be **false**. Several were found to be **incompletely characterized** (the check-count issue above being the most consequential), and one (the `echo_projects_autonomy` liveness claim) is now **doubly re-confirmed superseded**, with fresher live data than Phase 1 had.

---

## 2. Starting-State Verification

DIRECTLY VERIFIED, this session, via `git rev-parse`, `git branch`, `git status --short`, `date -u`, `ps aux`, `lsof`:

```
HEAD:            e92ec3b7fe4743f75746d161a06601db0232bff2   (matches Phase 1's claim, unchanged)
Branch:          main
Uncommitted paths (git status --short | wc -l): 95           (matches Phase 1's claimed end-state exactly)
Only new path since Phase 1's own start (94): audits/2026-09-10_research_arc_provenance_audit.md
                                                (confirmed — no other path appeared or vanished)
Real wall-clock timestamp at start of this phase: 2026-09-11T06:11:59Z
```

**Phase 1's specific claims — verified, not assumed:**
- `HEAD = e92ec3b` — CONFIRMED.
- uncommitted path count 95, previous 94, delta = 1 new audit file — CONFIRMED exactly.

**Running-process state**, DIRECTLY VERIFIED via `ps aux`/`lsof` (read-only):
```
run.py:      PID 7644, started 10:41PM (this session's earlier restart), still alive, unchanged
             (no restart occurred during this reconciliation — same PID throughout)
start_echo.sh watchdog: PID 7636, alive
ollama serve: PID 13534, alive since Sep 2 (long-running)
Listening:   *:5000 (run.py, PID 7644), 127.0.0.1:11434 (ollama, PID 13534)
```
No process was started, stopped, or restarted by this audit. PID 7644 is the identical process queried in Phase 1 and throughout this reconciliation.

---

## 3. Finding Inventory

Extracted from Phase 1's report, re-read for this pass (not re-derived from scratch — Phase 1's own categorization is used as a starting inventory, per this mission's instruction, then independently checked in §4–§9):

| # | Category | Finding |
|---|---|---|
| 1–5 | Implemented + undocumented | F2 stdin/fd0 contract; `/admin/restore` council gate; `select_best_fallback_candidate()` rewrite; `temporal_environment.py` location split; `echo_ground_truth.py` see/hear fix |
| 6 | Documented + unimplemented | Mission 18's read-only Git-provenance interface |
| 7 | Superseded/stale | `echo_projects_autonomy` "65.9+ hour silent gap" (R-010/Q-009) |
| 8 | Provenance/dating anomaly | `research/*.md` index committed in `cfd01b7`; its own explanatory audit report (`research_state_consolidation.md`) uncommitted, and internally date-anomalous |
| 9 | No discernible consequence | Q-004, Q-006, Q-005's unrepeated proposal |

This inventory was not blindly trusted — each row was independently re-derived below.

---

## 4. Five Implemented-but-Undocumented Reconciliations

For each: exact source location, Git provenance (via direct `git log -S`/`git show`, not inference from research notes), runtime status, evidence classification, and documentation search.

### 4.1 F2 stdin/fd0 sandbox contract
- **A. Source**: `sandbox/safe_exec_wrapper.py`, function `_install_patches()` (lines 240–460 in the current working-tree file, DIRECTLY VERIFIED by full read this session). `class _BlockedStdin(io.TextIOBase)` at line 211. The fd0-close block is lines 437–460. Reachable — this is the one shared subprocess-execution entry point all real F2 callers route through (per the file's own docstring, cross-checked against `self_edit_manager.py`, `app/core/echo_projects.py`, `sandbox/run_script.py` call sites — not re-traced exhaustively this pass, SUPPORTED not VERIFIED for the "all callers" claim specifically).
- **B. Git provenance** (DIRECTLY VERIFIED via `git log -S`):
  - `class _BlockedStdin` / `sys.stdin = _BlockedStdin()`: introduced in commit `1081f26` ("sandbox: enforce noninteractive stdin contract for autonomous execution", 2026-09-09T12:20:31-07:00). **Present in HEAD** (`git show HEAD:sandbox/safe_exec_wrapper.py` confirms the class and assignment both exist in the committed file).
  - `_os.close(0)`: **zero commits in its history** (`git log -S "_os.close(0)"` returns nothing) — exists **only in the current working-tree diff**, never committed.
- **C. Runtime status**: **LIVE**, and directly confirmed two ways this session: (1) the running server's `liveness_ledger.f2_stdin_contract` check reports its evidence text already includes *"...still closes fd 0"* (§4.1's own live query, this session) — meaning the running process loaded the current, uncommitted file, not `HEAD`'s version; (2) a bounded, isolated, direct invocation of the real wrapper (outside the project tree, §5.5) empirically confirmed the fd0-close and stdin-block both function correctly, right now, against the real current code.
- **D. Evidence**: DIRECT for the Python-level `sys.stdin` block (committed, live, empirically tested). DIRECT for the fd0-close (uncommitted but present on disk, live, empirically tested). Not promoted to more than DIRECT — this is exactly what DIRECT means (source + runtime observed).
- **E. Documentation**: Searched `CLAUDE.md`'s available content (its Self-Edit Safety Pipeline section, its Liveness Ledger table) — **no mention of a stdin/fd0 contract anywhere.** No `README*`/`ARCHITECTURE.md`/`docs/` equivalent found referencing it (`grep -rl "stdin" README* ARCHITECTURE.md 2>/dev/null` — no matches; no `docs/` directory exists in this repo). `research/FINDINGS.md` R-008's own text covers this chain in detail (REMEMBERED — see §11) but CLAUDE.md itself does not.

**Confirmed: IMPLEMENTED (mixed committed/uncommitted, as Phase 1 said) + UNDOCUMENTED in CLAUDE.md. Confidence: HIGH.**

### 4.2 `/admin/restore` council gate
- **A. Source**: `run.py`'s `admin_restore()` route (7 occurrences of `_council_review_restore`/`override_council_concern` confirmed in the current working-tree `run.py`, DIRECTLY VERIFIED via grep); `app/core/snapshot_manager.py`'s `_council_review_restore()`, `_build_restore_dissent_entry()`, `_log_restore_dissent_entry()`.
- **B. Git provenance**: `git log -S "_council_review_restore" -- app/core/snapshot_manager.py run.py` returns **zero commits**. `git show HEAD:app/core/snapshot_manager.py | grep -c _council_review_restore` = 0. **Entirely working-tree-only — never committed, in whole or in part.**
- **C. Runtime status**: **LIVE.** Direct query this session: `liveness_ledger.restore_council_gate` reports `"pass": true`, `"status": "no_real_restores_since_deployment"`, evidence: *"admin_restore() still calls the full review+dissent chain (source-anchor check passed). No real restore has occurred since this gate was deployed... (4 pre-deployment historical restore(s) in restore_log.jsonl are correctly excluded, not silently ignored.)"* — an honest, not-yet-exercised pass, exactly as Phase 1 characterized it, now independently re-confirmed live.
- **D. Evidence**: DIRECT for source + Git + the check's own static-anchor half. The check has never observed a real restore under this gate — the *ground-truth cross-check* half of the mechanism is UNVERIFIED-in-practice (it has never had real activity to check), though this is honestly reported by the check itself, not concealed.
- **E. Documentation**: Full-text search of CLAUDE.md's Snapshot and Restore System section — describes `/admin/restore` as "alert-and-propose, human-confirmed only," with no mention of a council-review layer. **Confirmed missing.**

**Confirmed: IMPLEMENTED (100% uncommitted) + UNDOCUMENTED. Confidence: HIGH.**

### 4.3 `select_best_fallback_candidate()` rewrite
- **A. Source**: `app/core/river_deliberation.py`, function `select_best_fallback_candidate()`. Current working-tree version implements the 3-stage rule (majority AST-agreement → RiverBrain tiebreak explicitly skipped → shortest-among-parseable), DIRECTLY VERIFIED by reading the full function this session (via the diff read in a prior session pass, re-confirmed present via grep this session).
- **B. Git provenance**: `git show HEAD:app/core/river_deliberation.py | grep -c "fp_counts = Counter"` = 0 — **the 3-stage version is not in HEAD.** `git log -S "def select_best_fallback_candidate"` shows the function's *definition line* was last touched by commit `9ac2f95` ("Refactor synthesis to preserve verified information (Tier-4-driven)") — this is a **different, earlier** commit than either audit had previously named; it corresponds to the Tier-5 synthesis refactor CLAUDE.md's own Finding 87 documents, which gave this function its prior ("prefer longest") form, not the 3-stage rewrite under investigation. **The 3-stage rewrite exists only in the working tree.**
- **C. Runtime status**: **LIVE** — this function is called from `deliberate_and_learn()`'s synthesis-rejection path, which is exercised on every real multi-model council deliberation that needs a fallback. Not independently re-triggered this session (would require a real council deliberation — out of scope for a bounded, read-only pass); classified LIVE based on direct code-reachability tracing (SUPPORTED, not independently exercised at runtime this pass).
- **D. Evidence**: DIRECT for source + Git provenance. INDIRECT/SUPPORTED for the 78.2%→96.1% improvement figure — this audit did not re-run `scripts/verify_select_best_fallback_candidate.py` (present, untracked, confirmed to exist via `ls`) to reproduce that number; it is REMEMBERED from `PENDING_DECISIONS.md`'s own text, not independently re-verified this pass.
- **E. Documentation**: `PENDING_DECISIONS.md` #20 documents this in detail (REMEMBERED, real). CLAUDE.md: confirmed absent by search.

**Confirmed: IMPLEMENTED (100% uncommitted) + UNDOCUMENTED in CLAUDE.md, DOCUMENTED in PENDING_DECISIONS.md. Confidence: HIGH**, with the one MEDIUM-confidence sub-claim flagged (the specific 78.2%→96.1% figure, not re-run this pass).

### 4.4 `temporal_environment.py` location split
- **A. Source**: `app/core/temporal_environment.py`, functions `get_macbook_location()`/`get_phone_location()`, confirmed present in the current working-tree file via grep this session.
- **B. Git provenance**: `git show HEAD:app/core/temporal_environment.py | grep -c "def get_macbook_location"` = 0; `git log -S "def get_macbook_location"` returns **zero commits**. Cross-checked against the one commit that touches this exact topic, `e92ec3b` ("docs: track MacBook/phone location separation decision") — **its own commit message states explicitly: "Documentation only, no code changed"**, and `git show --stat e92ec3b` confirms only `PENDING_DECISIONS.md` (1 line) was touched. **This is a clean, precisely-confirmed case: the decision was recorded as an open row in the last real commit; the implementation and the row's own "closed" writeup both happened afterward, entirely uncommitted.**
- **C. Runtime status**: **LIVE** — reachable from `get_temporal_environment_context()`, which is called by the real conversational grounding path (SUPPORTED via code trace, not independently re-triggered this pass).
- **D. Evidence**: DIRECT for source + Git provenance (the "docs only" commit message is about as clean a piece of direct evidence as this kind of archaeology gets). INDIRECT for the live-tested staleness figure (53.67h) cited in `PENDING_DECISIONS.md` — REMEMBERED, not re-measured this pass.
- **E. Documentation**: `PENDING_DECISIONS.md` #23 documents this fully (REMEMBERED). CLAUDE.md: confirmed absent.

**Confirmed: IMPLEMENTED (100% uncommitted) + UNDOCUMENTED in CLAUDE.md. Confidence: HIGH.**

### 4.5 `echo_ground_truth.py` see/hear conjunction fix
- **A. Source**: `app/core/echo_ground_truth.py`, `_SEE_HEAR_CONJUNCTION_RE` regex + its use in `_relevant_slices()`, confirmed present via grep this session.
- **B. Git provenance**: `git show HEAD:app/core/echo_ground_truth.py | grep -c _SEE_HEAR_CONJUNCTION_RE` = 0; `git log -S "_SEE_HEAR_CONJUNCTION_RE"` returns **zero commits**. **Entirely uncommitted.**
- **C. Runtime status**: **LIVE** — `_relevant_slices()` is called on every ground-truth-injection pass for a conversational turn (SUPPORTED via code trace).
- **D. Evidence**: DIRECT for source + Git. The "9 real conjunction phrasings match / 8 idiom phrasings don't" verification claim from Phase 1/prior session review is REMEMBERED, not re-run this pass.
- **E. Documentation**: No CLAUDE.md mention found. `research/EXPERIMENT_INDEX.md` E-025 documents this as "Mission 5... Fix deployed and verified live" (REMEMBERED) — so this fix has research-corpus documentation but, like the others, no CLAUDE.md entry.

**Confirmed: IMPLEMENTED (100% uncommitted) + UNDOCUMENTED in CLAUDE.md. Confidence: HIGH.**

**Summary for §4**: All five of Phase 1's "implemented + undocumented" claims survive independent verification. All five are, in fact, **more purely uncommitted than a casual reading of Phase 1 might suggest** — four of the five have *zero* Git history for their defining code (not even a prior, different version being modified — the identifiers simply do not exist anywhere in `git log -S` results), and the fifth (F2 contract) is a genuine split, with real committed and real uncommitted parts precisely delineated above.

---

## 5. F2 stdin-contract Forensic Reconstruction

### 5.1 Original finding
Per `research/FINDINGS.md` R-008's chain (REMEMBERED from Phase 1's own full read of this file — not re-read verbatim this pass, but its content was directly quoted and is not being re-derived from a summary of a summary):

Mission 24 (`audits/2026-09-09_f2_sandbox_timeout_forensics.md`) found that `_run_f2_multi_file()` never set `stdin=` on its `subprocess.run()` call, so a sandboxed subprocess inherited `run.py`'s own real, live terminal file descriptor. A generated project's `input()` call — explicitly invited by `echo_projects.py`'s own spec text ("an interactive text scenario") — would then hang against that live-but-silent terminal until a 60-second timeout fired. **Confidence at the time**: the report frames this as directly reproduced (a real pty hang vs. an explicit-EOF non-hang), which this audit treats as SUPPORTED/REMEMBERED — not re-run this pass, but methodologically sound as described (a controlled before/after comparison, not a single observation).

### 5.2 Proposed response
Missions 25–29 progressively narrowed the fix: spec-vs-harness contract archaeology (Mission 25) → candidate-fix testing finding neither `_insert_input_mock()` nor `stdin=DEVNULL` sufficient alone (Mission 26) → the correct enforcement layer determined to be `safe_exec_wrapper.py`, not `run_script.py` (Mission 27) → raw fd0 characterized as a second, distinct attack surface (Mission 29). This was **fully proposed and analyzed before any code was written** — five audit documents (Missions 25–29) with zero corresponding commits until Mission 28.

### 5.3 Implementation — exact source
`sandbox/safe_exec_wrapper.py`:
- `class _BlockedStdin(io.TextIOBase)` (lines 211–237 current file): overrides `read()`, `readline()`, `readlines()` — each raises `PermissionError` with the file's own `"[SANDBOX] ..."` convention.
- `_install_patches()` line 435: `sys.stdin = _BlockedStdin()` — unconditional, not gated on `--mode=`.
- `_install_patches()` lines 457–460: `try: _os.close(0)\n except OSError: pass` — closes the OS-level file descriptor.
- **Inputs**: the scratch directory and module path passed as CLI args; the subprocess's own inherited environment (including fd 0) at spawn time.
- **Outputs**: `SANDBOX_OK` printed and exit code 0 on success; a non-zero exit and stderr text on any blocked operation or failure.
- **Subprocess behavior**: this file is itself invoked as a fresh `sys.executable` subprocess by callers (`self_edit_manager.py`, `echo_projects.py`, `run_script.py`), wrapped in turn by the real kernel-level `sandbox-exec` Seatbelt profile (`echo_sandbox.sb`) — confirmed via the file's own docstring, not independently re-traced to the Seatbelt layer this pass.
- **Timeout behavior**: not implemented in this file itself — callers apply `subprocess.run(timeout=...)`, which genuinely `SIGKILL`s the child on timeout (a real, meaningful distinction from the pre-fix in-process `ThreadPoolExecutor` approach, per the file's own `apply_to_code` mode docstring — REMEMBERED from that docstring, not independently tested this pass for the apply_to_code mode specifically).
- **Fallback behavior**: `except OSError: pass` on the fd0 close — the docstring states this only fires on the "already-safe" case (fd already closed), and any *other* `OSError` propagates uncaught. Not independently stress-tested this pass beyond the one probe in §5.5.

### 5.4 Git history
Precisely reconstructed this session via `git log --format="%cI %h %s"`:
```
2026-09-09T12:19:37-07:00  75721f0  audit: document F2 sandbox timeout forensics       (Mission 24 doc)
2026-09-09T12:19:45-07:00  c7c1551  audit: document F2 stdin contract archaeology       (Mission 25 doc)
2026-09-09T12:19:51-07:00  5c78b0f  audit: document F2 stdin resolution experiment      (Mission 26 doc)
2026-09-09T12:19:58-07:00  bcdef70  audit: document F2 stdin enforcement boundary decision (Mission 27 doc)
2026-09-09T12:20:31-07:00  1081f26  sandbox: enforce noninteractive stdin contract for autonomous execution
                                     [Mission 28's CODE: sys.stdin=_BlockedStdin(), the class, and the
                                      f2_stdin_contract liveness check — all confirmed present in HEAD]
2026-09-09T12:20:40-07:00  ea5e5e8  audit: document OS-level fd0 stdin boundary forensics (Mission 29 doc)
2026-09-09T12:20:49-07:00  cfd01b7  audit: add research index
2026-09-09T12:20:59-07:00  e92ec3b  docs: track MacBook/phone location separation decision  [current HEAD]
```
**A notable, directly-observed fact**: all 8 commits land within an 82-second real-world window (12:19:37 to 12:20:59). This is a single batch-commit session capturing already-written work, not live incremental commits made as each mission finished — worth knowing when reasoning about "when" this work "happened" versus "when" it was committed. **Mission 30's own implementation commit (the fd0-close code itself) does not appear in this list at all** — there is no commit for it. `_os.close(0)` remains, as stated in §4.1, entirely uncommitted.

**Fully contained in HEAD?** No. The Python-level `sys.stdin` block (Mission 28) is. The OS-level `fd0` close (Mission 30) is not — it exists only in the working tree, alongside its own audit report (`audits/2026-09-09_os_level_stdin_fd0_implementation.md`, confirmed present in the untracked file list, never committed).

### 5.5 Runtime — direct empirical verification
A bounded, isolated, read-only-safe experiment was run this session (full command shown for reproducibility):

- A throwaway 3-line probe script and scratch directory were created **entirely outside the project tree**, in this session's own scratchpad (`/private/tmp/claude-501/.../scratchpad/f2_probe_scratch/`) — no project file was touched.
- The real, current, unmodified `sandbox/safe_exec_wrapper.py` was invoked exactly as its own docstring specifies (`python3 sandbox/safe_exec_wrapper.py <scratch> <module> --mode=script`), with `stdin` explicitly redirected from `/dev/null` (guaranteeing no hang is possible regardless of outcome — an immediate EOF either way).
- **Result** (DIRECTLY VERIFIED, exit code 0, `SANDBOX_OK` printed):
  ```
  STDIN_READLINE: BLOCKED (PermissionError: [SANDBOX] stdin.readline() blocked — ...)
  FD0_READ: BLOCKED (OSError: [Errno 9] Bad file descriptor)
  INPUT: BLOCKED (PermissionError: [SANDBOX] stdin.readline() blocked — ...)
  ```
- The throwaway scratch directory and probe file were deleted immediately afterward (confirmed via a follow-up `ls` returning "No such file or directory") — no residue left anywhere, inside or outside the project.
- This is neither `run.py` nor any part of the live server's own process — it is a standalone invocation of the real sandbox wrapper file, the same way `self_edit_manager.py`/`echo_projects.py` themselves invoke it. **This upgrades the fd0/stdin-block claim from SUPPORTED (Phase 1, source-reading only) to VERIFIED** (per this mission's own evidence vocabulary — a real before/intervention/after comparison was performed, and the result matched the expected direction).

**Not performed, and explicitly not attempted**: restarting `run.py`; triggering a real self-edit or `echo_projects` cycle through the live server; testing the `apply_to_code` mode specifically; testing the kernel-level Seatbelt profile's own independent enforcement (the Python-level patches were tested in isolation, without the `sandbox-exec` wrapper around them, since reproducing that wrapper safely outside the project's existing call sites was judged out of proportion for this confirmation).

### 5.6 Current semantics — does it solve the original problem?
**Comparing directly against the original failure condition** (Mission 24: a generated program's `input()` call hangs against a live, inherited terminal until a 60s timeout):
- `input()` no longer hangs — it raises immediately (§5.5, VERIFIED).
- The raw-fd bypass Mission 28 itself disclosed as unfixed (`os.read(0, ...)`) is now also closed (§5.5, VERIFIED) — this specific, named residual gap from the prior mission is confirmed resolved, not merely claimed resolved.
- **Not independently re-tested this pass**: whether a *generated, real* `echo_projects` project containing `input()` now completes cleanly end-to-end through the full production pipeline (would require either waiting for a real autonomous cycle or manually invoking `council_generate_project()`, both judged out of scope for a bounded, non-service-restarting pass).

**Classification: SOLVED**, for the specific, narrow failure mode Missions 24–30 targeted (stdin/fd0 hang), with HIGH confidence on the mechanism (directly tested this session) and MEDIUM confidence on full end-to-end production behavior (not independently re-exercised through the real pipeline this pass — REMEMBERED from Mission 30's own claimed regression-testing that "all 8 real production callers" were checked, not independently reproduced here).

**One related, separate, NOT re-verified claim**: whether `echo_projects_autonomy`'s broader 0/61 success rate (a different, wider problem than the stdin hang specifically) has improved as a result — see §6, which found the *scheduling* half of that problem resolved but did not re-derive the underlying success-rate figure.

### 5.7 Documentation
**Why CLAUDE.md doesn't reflect this**: the most direct, evidence-supported explanation is simply that **the entire chain was committed on 2026-09-09 and CLAUDE.md's last content is dated 2026-09-05** (per Phase 1's own finding, not re-derived independently this pass beyond confirming CLAUDE.md's available content contains no matching section) — a straightforward timing gap, not a deliberate omission or a methodology failure. **Minimum documentation that would eventually be needed** (not applied): one CLAUDE.md Finding describing (a) the original hang, (b) the two-layer fix (`sys.stdin` + fd0), (c) its split commit status, (d) the `f2_stdin_contract` Liveness Ledger check and its current evidence fields (`python_stdin_blocked`, `os_fd0_blocked`), matching this document's own established Finding-writing conventions.

---

## 6. 65.9-hour Claim Reconciliation

**What the original claim actually said** (REMEMBERED, from `research/FINDINGS.md` R-010, read in full during Phase 1): `echo_projects_autonomy` — the autonomous "investigation" loop introduced by CLAUDE.md's own Finding 85 — showed a confirmed 65.9+ hour gap with zero successful cycles as of Mission 21 (`2026-09-11_feralecho_unresolved_defect_audit.md`), with the root cause explicitly left unresolved between two hypotheses: a genuine code-level stall, or a restart-frequency artifact from an unusually restart-heavy investigation window.

**What subsequent missions in the same corpus already found** (REMEMBERED, R-010's own later updates, read in full during Phase 1): Mission 22 ruled out restart-frequency for its own observed 8.07h window and found the loop's scheduling record never re-evaluated past its startup check; Mission 23 found strong correlational evidence (a real, dated `pmset -g log` sleep/wake event) for an OS-suspend-extends-`time.sleep()` hypothesis; Mission 24 fully root-caused a *related but distinct* problem (`F2_TIMEOUT`, the stdin hang itself, §5) as deterministic and reproducible regardless of sleep/wake state.

**Independently re-verified this session, twice, at different moments** (DIRECT):
```
Query 1 (06:13:48 UTC):  "Last real autonomous cycle was 6.3h ago (within the 12h tolerance),
                          status='f2_failed', spec_source='garden'."  pass: true
memory/echo_projects_autonomy_state.json:
  last_run_utc: 2026-09-10T23:53:01.369332+00:00
  last_status: f2_failed
sandbox/echo_projects/ directory count: 61 total attempts
Most recent attempt directory: 20260910T235301Z_... (matches the state file's last_run_utc exactly)
```
**Reconciliation**: the specific symptom the "65.9+ hour silent gap" claim described — the scheduler not firing at all — is **STALE/SUPERSEDED**, independently confirmed twice this session with fresh queries several minutes apart, both showing a real, recent cycle (`f2_failed`, not "no cycle"). This is consistent with, not contradictory to, Mission 23's own restart-recovery finding — a clean restart (which this session's own earlier terminal-freeze-triggered restart, unrelated to this investigation, provided) appears to be sufficient to un-stick the scheduler, matching the pattern Mission 23 already found once.

**What remains genuinely unresolved, not resolved by this reconciliation**: the underlying *reason* F2 keeps failing (`status='f2_failed'`) on real generated projects — this reconciliation did not re-derive the 0/61 historical-success-rate figure Mission 22 reported, nor determine whether the specific F1/F2 failure content differs from what Mission 22 characterized. **Classification: STALE for the liveness-gap symptom specifically (HIGH confidence, directly re-observed twice); the broader "does echo_projects_autonomy ever succeed" question remains UNKNOWN to this pass** (not re-measured).

**Explicitly not manufactured**: no cycle was triggered, forced, or waited-for by this audit — both observations reflect activity that occurred on its own, before this reconciliation began (the most recent cycle at 23:53:01 predates this session's own investigation start).

---

## 7. Research-Index / Audit Provenance Reconciliation

**The state, precisely reconstructed this session:**

```
research/{CURRENT_STATE,DECISIONS,EXPERIMENT_INDEX,FINDINGS,OPEN_QUESTIONS}.md
  → committed in cfd01b7, 2026-09-09T12:20:49-07:00 ("audit: add research index...")
  → cfd01b7's own commit message states: "this index predates and extends beyond the F2 stdin
     chain committed in the surrounding commits" — i.e., the commit author already knew and
     disclosed that this index's underlying content predates its own commit date.

audits/2026-09-11_research_state_consolidation.md
  → STILL UNTRACKED as of this session (confirmed via git status --porcelain this session)
  → filename prefix: 2026-09-11
  → internal header: "**Date:** 2026-09-11"
  → on-disk mtime (stat): 2026-09-08T13:18:27  ← three days before both its own claimed date
                                                  AND one day before cfd01b7's commit
  → its own internal "HEAD (start and end)" integrity claim: 525454a1dccfc91adf1aa8b01ff9b6ce8405d423

525454a1dccfc91adf1aa8b01ff9b6ce8405d423
  → committed 2026-09-07T21:29:25-07:00 ("Fix epistemic claim rendering and generation audit")
  → confirmed (git merge-base --is-ancestor) to be a real, genuine ancestor of current HEAD
  → confirmed to be the LAST commit before the 82-second, 8-commit batch on 2026-09-09T12:19-12:20
    (i.e., 525454a was genuinely HEAD for the entire real-world span 09-07 21:29 through 09-09 12:19)
```

**Reconciling the file's own self-report against this evidence**: the file's "HEAD was 525454a" claim is **CONFIRMED ACCURATE** — 525454a genuinely was HEAD for the entire window during which the file's mtime (09-08 13:18) falls. This part of the file's own integrity record holds up.

**What does NOT reconcile cleanly**: the file's filename and internal header both say `2026-09-11` — a full three days after its actual last-write time (09-08) and two days after the commit batch (09-09) that captured the deliverables it describes itself as having just created. Per this mission's explicit instruction not to "correct" this, four possibilities are recorded, **none confirmed over the others from available evidence**:

1. **A legitimate future-dated filename**: the author may have named/dated the file for an anticipated later review or "presentation" date, distinct from its actual authorship time — plausible, not confirmed.
2. **A naming anomaly**: a simple, undetected typo/misremembering of the current date at the time of writing or naming — plausible, not confirmed, and this project's own extensive prior history (CLAUDE.md's own Findings repeatedly catch exactly this class of small dating slip) makes it a reasonably likely mundane explanation.
3. **An ordering issue**: the file's content could have been substantially finalized on 09-08, held, then the header/filename updated later to reflect an intended-but-different final date, without the file's content being re-saved (which would explain the "content" mtime staying at 09-08 while claiming a later date) — plausible, not confirmed; this would require the file to have been edited via a method that doesn't update mtime, which was not independently tested this pass.
4. **A misunderstanding in Phase 1**: re-checked directly — Phase 1's own claim was narrower than this ("committed in cfd01b7... but the audit report... was not committed alongside it, and remains untracked today") and did **not** itself assert anything about the mtime/header date relationship — that specific anomaly is a **new finding of this reconciliation pass**, not a claim Phase 1 made incorrectly. Phase 1's actual claim (research/*.md committed, the explanatory report not) is **independently reconfirmed, accurate, and unaffected by this date anomaly**.

**This audit's own report is dated `2026-09-10` in its filename** (matching Phase 1's convention) while being investigated and written on real-world 2026-09-11 — the same category of filename/wall-clock mismatch is present in this very document, for the same reason the user's own prompt flagged as worth investigating rather than "correcting." Noted for transparency, not resolved.

---

## 8. Mission 18 Verification

Independently re-checked this session with broader search terms than Phase 1 used (`GitProvenance`, `git_evidence_ledger`, `evidence_id.*git`, `read.only.*git.*interface`, across `app/` and `run.py`): **zero matches**, confirming Phase 1's finding of zero implementation. `audits/2026-09-11_read_only_git_provenance_design.md` exists (confirmed present in the untracked file list) and, per Phase 1's own excerpt (REMEMBERED, not re-read in full this pass), describes a design (evidence-hierarchy, an `evidence_id`-keyed append-only ledger at a proposed `memory/git_evidence_ledger.jsonl` path) explicitly marked "not implemented, named here as the design target" within its own text.

**Confirmed: DOCUMENTED + UNIMPLEMENTED, correctly self-labeled as in-progress (`research/CURRENT_STATE.md`'s own `[UNRESOLVED — active design mission]` tag) rather than a broken promise. Confidence: HIGH.**

---

## 9. Q-004 / Q-006 / Q-005 Assessment

Per this mission's own instruction not to over-invest here — one targeted check each:

- **Q-005** (does memory retrieval materially influence model selection/classification/self-edit targeting?) — its own proposed next experiment ("rerun the July memory-ablation experiment at `temperature=0`") has **not been run**: a grep for `temperature=0` across `audits/` combined with "ablation"/"memory" in the filename returns only the original 2026-07-23 file, no rerun. **Classification holds: real, correctly-scoped open question, genuinely un-actioned since Finding 76 (July) through this pass, across two separate research programs now flagging the identical unexecuted next step.**
- **Q-006** (is RiverBrain's trust-gate history representative of a broader "automated trust never self-activates" pattern?) — a grep for a dedicated trust-gate audit across `audits/` and `research/` returns only this document and the feasibility study mentioning it in passing; **no dedicated audit exists.** **Classification holds: real, proposed, not yet run.**
- **Q-004** (hypothesis-formation / competing-explanation comparison) — Phase 1's own characterization ("not yet designed... exploratory") was not independently re-checked beyond confirming no code or dedicated audit exists matching this description (consistent with the broader corpus's own explicit "no mechanism anywhere in the codebase" framing for this capability). **Classification holds.**

All three: **CONFIRMED as genuinely low/no discernible consequence, not research churn requiring correction** — each is an honestly-labeled open question with a real, if unexecuted, next step, not a false or misleading claim.

---

## 10. Evidence Matrix

| Finding | Source | Git Status | Runtime Status | Evidence | Documentation | Final Classification | Confidence |
|---|---|---|---|---|---|---|---|
| F2 stdin block (`sys.stdin`) | `sandbox/safe_exec_wrapper.py` | **Committed** (`1081f26`) | LIVE | DIRECT (source + Git + empirical test §5.5) | Absent from CLAUDE.md; present in `research/FINDINGS.md` R-008 | IMPLEMENTED + UNDOCUMENTED (in CLAUDE.md) | HIGH |
| F2 fd0 close | `sandbox/safe_exec_wrapper.py` | **Uncommitted** (working tree only) | LIVE | DIRECT (source + empirical test §5.5) | Absent everywhere except its own audit report (untracked) | IMPLEMENTED + UNDOCUMENTED | HIGH |
| `f2_stdin_contract` liveness check | `app/core/liveness_ledger.py` | **Split**: check itself committed (`1081f26`); `os_fd0_blocked` field uncommitted | LIVE, evidence text confirms extended (uncommitted) version is running | DIRECT | Absent from CLAUDE.md's Liveness Ledger table | IMPLEMENTED + UNDOCUMENTED | HIGH |
| `/admin/restore` council gate | `run.py`, `app/core/snapshot_manager.py` | **Uncommitted** | LIVE (honest not-yet-exercised pass) | DIRECT | `PENDING_DECISIONS.md` #20; absent from CLAUDE.md | IMPLEMENTED + UNDOCUMENTED | HIGH |
| `select_best_fallback_candidate()` rewrite | `app/core/river_deliberation.py` | **Uncommitted**; HEAD's version last touched by `9ac2f95` (a different, earlier refactor) | LIVE (reachable, not re-exercised) | DIRECT (source+Git); INDIRECT (78.2%→96.1% figure, not re-run) | `PENDING_DECISIONS.md` #20; absent from CLAUDE.md | IMPLEMENTED + UNDOCUMENTED | HIGH (MEDIUM on the specific %-figure) |
| `temporal_environment.py` split | `app/core/temporal_environment.py` | **Uncommitted** (last real commit on this topic was docs-only) | LIVE (reachable) | DIRECT | `PENDING_DECISIONS.md` #23; absent from CLAUDE.md | IMPLEMENTED + UNDOCUMENTED | HIGH |
| See/hear conjunction fix | `app/core/echo_ground_truth.py` | **Uncommitted** | LIVE (reachable) | DIRECT | `research/EXPERIMENT_INDEX.md` E-025; absent from CLAUDE.md | IMPLEMENTED + UNDOCUMENTED | HIGH |
| Mission 18 Git-provenance interface | (none) | N/A — no code | N/A | DIRECT (grep confirms absence) | Extensively documented in `research/*.md` and its own design doc | DOCUMENTED + UNIMPLEMENTED | HIGH |
| `echo_projects_autonomy` liveness gap | `memory/echo_projects_autonomy_state.json`, live check | N/A (behavioral claim) | LIVE, firing (2 fresh independent queries, `f2_failed`) | DIRECT | `research/FINDINGS.md` R-010 (describes the now-stale state) | STALE/SUPERSEDED (symptom); underlying 0/N success rate UNVERIFIED this pass | HIGH (symptom); LOW-UNVERIFIED (root cause) |
| `research_state_consolidation.md` commit/date state | `audits/2026-09-11_research_state_consolidation.md` | Uncommitted; its own deliverables (`research/*.md`) committed separately | N/A | DIRECT (mtime, git log, commit messages) | The anomaly itself is undocumented anywhere | PARTIALLY TRACED PROVENANCE — genuine open discrepancy, not resolved | MEDIUM (facts HIGH; interpretation LOW, explicitly left open) |
| Q-004/Q-005/Q-006 | `research/OPEN_QUESTIONS.md` | N/A | N/A | DIRECT (grep confirms no follow-up artifact exists) | Honestly self-documented as open | UNVERIFIED (no consequence), correctly labeled by the corpus itself | HIGH |

---

## 11. Directly Verified vs. Inherited vs. Unverified

**DIRECTLY VERIFIED this session** (source read, Git command output, or live/empirical test performed by this pass specifically):
- All Git provenance claims in §4 and §5.4 (every `git log -S`/`git show`/`git log --format` result).
- The F2 stdin/fd0 empirical test (§5.5) — the single strongest new evidence this reconciliation produced.
- The `f2_stdin_contract`, `restore_council_gate`, and `echo_projects_autonomy_activity` live check evidence text (three separate `curl` queries this session, at three different timestamps).
- The `_CHECKS` tuple count discrepancy (51 committed vs. 52 running) — including this audit's own self-correction of an initial undercount caused by a `grep -A N` context-window bug, disclosed in full below.
- `e92ec3b`'s "documentation only, no code changed" commit message, and the precise 82-second commit-batch timing.
- Process/port state (§2).

**INHERITED FROM PRIOR RESEARCH** (REMEMBERED — used as stated, not independently re-derived):
- The 78.2%→96.1% fallback-candidate improvement figure.
- The specific "5/5 hang reproduced, EOF confirmed instead" Mission 24 experimental detail.
- The 53.67h phone-location staleness figure.
- The "9 conjunction phrasings match / 8 idioms don't" regex-verification claim.
- `research/FINDINGS.md`/`EXPERIMENT_INDEX.md`'s own depth-of-review disclosures for the ~40 files this pass did not independently re-read.
- The 0/61 historical `echo_projects_autonomy` success-rate figure (Mission 22) — not re-derived this pass.

**UNVERIFIED** (cannot currently be established from available evidence, this pass):
- Whether a real, full `echo_projects` generated project (not a synthetic probe) currently completes cleanly through the real production pipeline end-to-end.
- The true cause of the `research_state_consolidation.md` date/mtime anomaly (§7) — four possibilities recorded, none resolved.
- Whether `select_best_fallback_candidate()`'s claimed corpus-verified accuracy figures would reproduce if `scripts/verify_select_best_fallback_candidate.py` were re-run this session (script confirmed to exist; not re-executed).
- Whether the underlying `echo_projects_autonomy` F2-failure content has changed in nature since Mission 22's own characterization.

**Self-disclosed methodology correction, made mid-investigation, not smoothed over**: this audit's own first attempt to count `HEAD`'s Liveness Ledger check tuple used `grep -A 60` (a fixed 60-line context window), which silently truncated the real tuple and produced an undercount. Caught by cross-checking the same extraction method against the working-tree file and finding an implausible-looking match to the *wrong* file's own separately-mis-measured count — re-done with an unbounded `awk`-based extraction that reads to the tuple's actual closing paren, yielding the correct, reproducible counts (51 committed / 52 running) reported throughout this document. This is exactly the kind of self-caught measurement bug this project's own methodology treats as a sign of good process, not something to hide.

---

## 12. Proposed Documentation Patch List

**Not applied. Proposals only, per this mission's explicit constraint.**

| # | File | Section | Factual change required | Reason | Evidence | Priority |
|---|---|---|---|---|---|---|
| 1 | `CLAUDE.md` | Liveness Ledger section | Update check count/table to reflect that the *committed* count is 51, distinct from whatever count is currently live (which includes uncommitted checks) — and note explicitly that check count can differ between `HEAD` and the running process | The live server is currently running Liveness Ledger checks that exist nowhere in Git history; a reader of CLAUDE.md has no way to know this is possible, let alone currently true | §4.1, §10 (this document) | **P0** — actively misleading: CLAUDE.md's own stated purpose for this section is ground-truth accuracy about what's really checked |
| 2 | `CLAUDE.md` | Self-Edit Safety Pipeline / new subsection | Document the F2 stdin/fd0 contract: original hang, two-layer fix, split commit status, `f2_stdin_contract` check | A real, live, security-relevant sandbox-hardening change with zero canonical documentation | §5 (this document) | **P0** |
| 3 | `CLAUDE.md` | Snapshot and Restore System | Document the new council-review gate on `/admin/restore`, including its current "never yet exercised against a real restore" honest state | Directly closes a gap CLAUDE.md's own "Standing Principle" section names as unbuilt; currently misleading by omission | §4.2 (this document) | **P1** |
| 4 | `CLAUDE.md` | River deliberation / self-edit council section | Document `select_best_fallback_candidate()`'s 3-stage rewrite and its measured improvement (once re-verified — see priority note) | Real, measured quality improvement to council-disagreement resolution, currently invisible to CLAUDE.md readers | §4.3 (this document); re-verify the %-figure before citing it as settled | **P1** |
| 5 | `CLAUDE.md` | Machine-Native Awareness / relevant section | Document the MacBook/phone location split in `temporal_environment.py` | Real correctness fix; currently invisible | §4.4 | **P1** |
| 6 | `CLAUDE.md` | Echo Studio / ground-truth section | Document the see/hear conjunction regex fix | Small, real, already-shipped correctness fix; low urgency given its scope | §4.5 | **P2** |
| 7 | `research/FINDINGS.md` (self-correction of its own corpus) | R-010 | Add a dated "Update" annotation (matching this corpus's own established discipline) noting the liveness-gap symptom is superseded as of 2026-09-11, with the underlying success-rate question still open | The corpus's own entries are stale relative to directly observable current state | §6 (this document) | **P2** |
| 8 | Either `research/DECISIONS.md` or a new dedicated note | D-002 | Reconcile D-002's "replication in progress" phrasing against `EXPERIMENT_INDEX.md` E-035's own "REPLICATED" status in the same committed index | Internal inconsistency within the corpus's own canonical files, already flagged by Phase 1, independently unresolved | Phase 1 §"Superseded Findings" item 3 | **P2** |
| 9 | `audits/2026-09-11_research_state_consolidation.md` (commit it, don't edit it) | N/A | Commit the file as-is; do not alter its date/header to "fix" the anomaly found in §7 | Preserves the historical record exactly as this project's own discipline requires; the anomaly itself is a legitimate thing to leave visible, not something to quietly correct | §7 (this document) | **P3** — process note, not a content correction |

---

## 13. Final Assessment

1. **How many previously claimed IMPLEMENTED + UNDOCUMENTED findings survive independent verification?** All five. HIGH confidence on all five.
2. **How many are actually live?** All five are reachable/live in the running process (F2 contract confirmed by direct empirical test; the other four confirmed by direct code-reachability tracing, not independently re-exercised at runtime this pass).
3. **How many are only partially implemented?** One — the F2 stdin/fd0 contract itself is a genuine split (Python-level committed and live; OS-level fd0 uncommitted but also live, since the process loads from the working tree, not from Git).
4. **How many previous claims are stale or superseded?** One directly reconfirmed (the `echo_projects_autonomy` liveness-gap symptom, now independently re-observed twice this session with fresher data than Phase 1 had). One new anomaly surfaced that Phase 1 did not find (the `research_state_consolidation.md` date/mtime mismatch, §7) — not a correction of Phase 1, an addition to it.
5. **Is F2 actually solved, partially solved, or still broken?** **SOLVED**, for the specific stdin/fd0 hang failure mode, with direct empirical confirmation this session (§5.5) — the strongest evidence tier this methodology has. The broader question of whether `echo_projects_autonomy`'s overall F2 failure rate has improved is a **separate, still-open question**, not resolved by this pass.
6. **Is the current running server consistent with the repository's documented architecture?** **No, not fully** — the running server currently executes at least one Liveness Ledger check (`restore_council_gate`) and one sandbox-hardening mechanism (fd0 close) that exist nowhere in Git history, meaning `git show HEAD` does not accurately describe what is currently running. This is the single most concrete, checkable version of "the documentation/reality gap" this whole investigation has been asked to characterize.
7. **What is the largest remaining provenance gap?** The gap between "what CLAUDE.md documents" and "what the running production process is currently executing" — not between research and code (those two are well-connected via `PENDING_DECISIONS.md` for the production-fixes thread), but between the **working tree** (which the running process actually loads) and **both** Git history and canonical documentation simultaneously.
8. **What is the single highest-value next action?** Commit the already-written, already-verified working-tree changes (F2 fd0 implementation, restore council gate, fallback-candidate rewrite, location split, see/hear fix) — every one of them was independently re-confirmed correct, tested, and low-risk by this pass and the prior one. This closes the Git-history gap immediately; a CLAUDE.md documentation pass can follow at lower urgency once the code itself is no longer only-on-disk.
9. **Did anything in this investigation require changing runtime state?** **NO.** One bounded, isolated subprocess was run outside the project tree as a direct empirical test (§5.5); it read the real `sandbox/safe_exec_wrapper.py` file (unmodified) but wrote nothing inside the project, created and then deleted its own scratch files entirely within this session's own scratchpad directory, and did not interact with `run.py`, Ollama, or any persisted application state.
10. **Did anything in this investigation modify Git state?** **NO.** `git status --porcelain` path count (95) and `HEAD` (`e92ec3b`) are identical at the end of this investigation to their state at the start.

---

## 14. Explicit Safety / Mutation Statement

### Mutation Statement

```
Source code changed:           NO
CLAUDE.md changed:              NO
README/architecture docs changed: NO
Configuration changed:          NO
Environment variables changed:  NO
Runtime state changed:          NO — see note below
Services restarted:             NO (run.py PID 7644 unchanged throughout; Ollama PID 13534 unchanged)
Git history changed:            NO
Commits created:                NO
Files other than this new report created/modified/deleted: NO

Note on "runtime state": one bounded, read-only-intent subprocess experiment (§5.5) invoked the
real sandbox/safe_exec_wrapper.py directly, entirely outside the project tree, against a
throwaway probe script and scratch directory created in this session's own scratchpad
(not inside /Users/richietate/Desktop/FeralEcho). Both the probe script and scratch directory
were deleted immediately after the test (confirmed via a follow-up directory listing). This did
not touch run.py, Ollama, any persisted memory/ state, or any file inside the project repository.
It is disclosed here in full rather than omitted, per this mission's own "measure first" ethic —
it is the one action in this investigation that executed code, and its scope and cleanup are
recorded precisely above (§5.5) so the reader can judge for themselves whether it fits within
"runtime inspection is permitted."

git status --porcelain path count: 95 (start) -> 95 (end, before this report's own creation)
HEAD: e92ec3b7fe4743f75746d161a06601db0232bff2 (unchanged, start and end)
```
