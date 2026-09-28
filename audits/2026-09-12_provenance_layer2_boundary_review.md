# Provenance Layer 2 Boundary Review

**Date:** 2026-09-12/13
**Type:** Architecture/boundary review only. No application code modified. No Layer 2 primitive implemented. No commit. PID 7644 read-only-inspected only (`ps`, `psutil.Process()`, file reads — never signaled, restarted, or attached to).
**Predecessor artifacts reconciled against, not assumed correct:** `audits/2026-09-11_read_only_provenance_interface_design.md`, `audits/2026-09-11_provenance_leaf_primitives_validation.md`, `audits/2026-09-11_provenance_implementation_boundary_audit.md`, `audits/2026-09-10_phase2_provenance_reconciliation.md`, plus the now-committed `app/core/provenance_check.py` (commit `6e835bf`) and its own red-team/fix history from this session.

---

## 1. Executive conclusion

```
PROCEED WITH CONSTRAINTS
```

There is a real, narrowly-scoped, genuinely new Layer 2 primitive justified by evidence already sitting in this codebase — but it is **not** the `runtime_process_identity()`/`runtime_self_reported_module_origin()` pair as originally sketched by the predecessor design docs. Investigation this session found that most of the *process-identity* half of that pair (PID, start time) is **already self-reported today, continuously, by mechanisms that already exist and require zero new application code** (`memory/echo_server.pid`, `memory/echo_sentinel.json`) — the only new work is a small leaf function that reads those two files and cross-references them against one independent, external OS-level check. The *module-origin* half (`sys.modules` introspection) remains genuinely unbuildable without adding new in-process code, exactly as the leaf-primitives-validation report already established — this review does not reopen that finding, it re-confirms it (§4, §8).

The constraint: the recommended primitive must be built and documented as **process identity evidence only**, structurally incapable of answering anything about module loading, import, or execution — the exact boundary Phase 5's `self_heal.py` test exists to enforce.

---

## 2. Layer 1 capability boundary

`working_tree_file_identity(path)` (committed, `6e835bf`) gathers five facts about a file path, each independently externally re-derivable by anyone with filesystem/git access to this one repository: whether it is a regular file on disk now (`exists`); whether Git's index tracks the literal queried path (`tracked`); the sha256 of its current on-disk bytes (`sha256`); the sha256 of the blob HEAD holds for the literal queried path (`head_blob_sha256_or_none`); and whether those two hashes differ, when both are known (`modified_vs_head`).

**It can prove:** working-tree file state and Git object-store state for one path, at one point in time, as two structurally separated branches (filesystem-resolved vs. lexically-normalized-for-Git) since the 2026-09-13 symlink fix.

**It cannot prove, and its own docstring says so explicitly:** that any process has imported the file, that it is loaded into any running interpreter's `sys.modules`, that any function inside it has ever been called, or that the file is "responsible for" any observed system behavior. Nothing in its five output fields, or in `in_scope`/`error`, encodes or implies a runtime claim.

---

## 3. Evidence taxonomy

Six distinct evidence classes, kept explicitly unmerged for the rest of this document:

| Class | Example in this codebase | Independently observable? |
|---|---|---|
| **Working-tree evidence** | `os.stat()`, `hashlib.sha256(open(path,'rb').read())` | Yes — pure filesystem fact |
| **Git evidence** | `git ls-files --error-unmatch`, `git show HEAD:<path>` | Yes — pure object-store fact, external to any running process |
| **Process identity evidence** | `ps -p <pid>`, `psutil.Process(<pid>).create_time()/.cmdline()/.exe()/.cwd()` | Yes — the OS process table, read by a *separate* process, about a *target* process, with zero cooperation required from the target |
| **Runtime self-report evidence** | `memory/echo_server.pid`, `memory/echo_sentinel.json` (both written by the FeralEcho process about itself); `run.py`'s `/mirror_echo`/dashboard JSON payloads | Readable externally (they're plain files/HTTP responses), but the *content* originates entirely from the process being described — no independent witness to whether the content is accurate |
| **Runtime loading/import evidence** | `sys.modules`, `module.__file__` | **No** — confirmed this session (re-derivation, not reopening) that no mechanism anywhere in this codebase, and no OS-level tool (`lsof` was already checked in the leaf-primitives validation), exposes this to an external process; only obtainable from code executing inside the target interpreter |
| **Runtime execution/use evidence** | Whether a specific function was actually called | **No mechanism exists anywhere in this codebase today** — not even self-report; would require new instrumentation (a call counter, a trace log) inside the target module itself |

The predecessor design docs (`read_only_provenance_interface_design.md` line 59, `provenance_implementation_boundary_audit.md` §3 claims 6–10) already drew a version of this line between "process identity" (claims 6–7) and "module origin" (claims 8–9), correctly flagging the latter as self-report with no external witness. This review's contribution is confirming, empirically, that the *process identity* half no longer requires any new code to observe — see §5.

---

## 4. Self-heal falsification

**Direct test, run fresh this session, read-only:** `app/core/self_heal.py` exists on disk, `git status --porcelain -- app/core/self_heal.py` is empty (clean, matches HEAD), and a repo-wide grep for `self_heal` outside its own file finds exactly one real reference: `app/routes_echo_studio.py`'s dashboard handler, which does a **static text scan of `run.py`'s own source** for a non-comment `import app.core.self_heal` line — not a `sys.modules` check, not an execution check. That scan currently finds none, and the handler's own field is honestly labeled `"connected": false` — but the mechanism itself is a useful, concrete illustration of the exact failure mode this review is guarding against: a check that *looks* like a runtime-liveness signal but is actually repository/text evidence one layer removed from working-tree identity, not a layer closer to runtime truth.

**Would a naive provenance system conclude `self_heal.py` is "live"?** Yes, if it only asked Layer 1's questions: the file exists, is tracked, and (being unmodified) matches HEAD — every field `working_tree_file_identity()` can produce would read as "clean" for this file, identically to any genuinely-imported, actively-executing module. This is not a hypothetical — it is CLAUDE.md's own documented, standing example: *"FIXED, INTENTIONALLY DISCONNECTED. Not imported anywhere; has no live caller."*

**What would distinguish repository identity from runtime-loaded identity, if it were ever built?** Only genuine runtime self-report (`sys.modules.get("app.core.self_heal") is not None`, queried from code executing inside PID 7644) — nothing external can supply this (§3, §8). And even that would only establish loading, not use — a fifth, still-harder question (§ below).

**The five levels, kept explicitly distinct, per the mission's own instruction not to collapse them:**
1. **Repository presence** — the file exists somewhere in the tree. (`self_heal.py`: yes.)
2. **Repository identity** — Layer 1's own claims: tracked, hash-matched-to-HEAD. (`self_heal.py`: yes, clean.)
3. **Runtime loading** — `sys.modules` contains it. (`self_heal.py`: per CLAUDE.md's standing finding and the routes_echo_studio.py text-scan, almost certainly **no** — but this cannot be independently confirmed by anything built so far, including anything this review could build without new in-process code.)
4. **Runtime import origin** — if loaded, does `__file__` match this working-tree path (vs. a stale cached `.pyc`, a different install, etc.). (Inapplicable if level 3 fails.)
5. **Runtime execution/use** — a function inside it was actually called. (No mechanism exists anywhere in this codebase to establish this for *any* module, not just this one — a materially harder, unaddressed question, correctly out of scope for Layer 2.)

Level 2 says nothing about level 3, and level 3 (even if it existed) would say nothing about level 5. This is the load-bearing distinction the next primitive must respect.

---

## 5. Candidate Layer 2 primitives

### Candidate A — `runtime_process_identity()`

**Evidence gained:** externally-observable OS process-table facts about a specific PID (existence, start time, command line, executable path, cwd) via `psutil.Process(pid)` or `ps`, run from a *separate* process. **Empirically re-confirmed this session, live, against the real PID 7644**, with no restart and no interaction beyond `ps`/`psutil`:
```
ps:      PID 7644  STARTED Thu Sep 10 22:41:53 2026  COMMAND python -u run.py
psutil:  create_time = 2026-09-11T05:41:53.357916+00:00 (same instant, UTC)
         cmdline = ['python', '-u', 'run.py']
         exe = /Users/richietate/miniforge3/envs/feral_echo/bin/python3.12
         cwd = /Users/richietate/Desktop/FeralEcho
```
**Epistemic status:** genuine external observation — zero cooperation required from PID 7644, not self-report.
**Limitations:** proves a process with this PID exists and was started at this time running this command — says nothing about what modules it has loaded or what it is doing.
**Safety:** read-only, no signal, no attach; `psutil.Process(pid)` on the same-user process is a plain `/proc`-equivalent (macOS `libproc`/`sysctl`) read.
**Duplication risk:** none — Layer 1 has no process-facing fields at all.
**Recommendation: justified, cheap, and — per the discovery below — largely already free.**

### Candidate B — `runtime_self_reported_module_origin()`

**Evidence gained:** would answer "is module X in `sys.modules`, and what `__file__` does it report" — genuinely new evidence, not available any other way (§3, re-confirmed §8).
**Epistemic status:** pure self-report, with **no external corroboration path of any kind** — this was the leaf-primitives-validation report's central, empirically-proven finding (a scratch process's `sys.modules` is provably disjoint from PID 7644's; `lsof -p 7644` was already checked and shows zero `.py` sources among its open file descriptors). Nothing found this session contradicts it.
**Limitations:** even if built, only answers level 3 of §4's five-level ladder, never level 5.
**Safety:** cannot be implemented without adding a new capability to the **live** application — either a new Flask route or a new `echo_tool_dispatch.py` tool registration — both are changes to `run.py`/`app/core/echo_tool_dispatch.py`, both explicitly forbidden by this mission's Phase 9, and neither can be exercised against PID 7644 without either a restart (new code isn't running in the current process) or an already-existing reachable path (none exists today).
**Duplication risk:** none.
**Recommendation: real evidence value, but not buildable-or-testable within this mission's constraints. Correctly deferred, not abandoned — see §8.**

### Candidate C — an externally observable process/module relationship

This is where investigation this session found something the predecessor design docs did not have visibility into: **the process-identity half of "runtime self-report" already exists in this codebase, is already live, and requires zero new code.**

- `memory/echo_server.pid` — written once, at `run.py`'s own startup (`_SERVER_PID_FILE.write_text(str(os.getpid()))`), currently reads `7644` — matches the real PID exactly.
- `memory/echo_sentinel.json` — written at two fixed startup stages (`_write_sentinel("threads_starting")`, `_write_sentinel("serving")`) with `pid`/`start_utc`/`uptime_s`, **and its `last_heartbeat_utc` field is independently, continuously refreshed by `app/core/dmn_guardian.py`'s own already-documented 60-second guardian cycle** (confirmed directly, source at `dmn_guardian.py:164-172`; confirmed live by reading the file twice, two minutes apart, this session: `last_heartbeat_utc` advanced from `03:20:48Z` to `03:22:48Z`, matching wall-clock exactly).

**Cross-corroboration observed live, this session, between two structurally independent sources:**
```
External (psutil, OS process table):     create_time = 2026-09-11T05:41:53.357916 UTC
Self-report (echo_sentinel.json):        start_utc   = 2026-09-11T05:41:57.788028 UTC
                                          pid         = 7644  (matches ps/psutil exactly)
```
The ~4.4-second gap is exactly what's expected (the OS records process creation before Python reaches the line that calls `datetime.utcnow()` for `_SENTINEL_START`) — a small, explainable delta, not a discrepancy, and its very existence is what makes this a real corroboration between two *different* measurement methods rather than one value read twice.

**Evidence gained:** (a) real, external process-table facts (Candidate A's evidence, unchanged); (b) the *content* of two pre-existing self-report files, read as plain files — zero new application code required; (c) a factual comparison of whether (a) and (b) agree on PID and (approximately) on start time.
**Epistemic status:** (a) is external observation; (b) is self-report; (c) is a derived comparison of the two — all three must remain labeled as such, never merged into one "verified" field, per Phase 7's rule.
**Limitations:** identical to Candidate A's — process identity only, zero claim about modules, imports, or execution. `echo_server.pid` is also known to have a real gap worth disclosing: `_SERVER_PID_FILE.unlink(missing_ok=True)` exists somewhere in the shutdown path (found via grep, not traced further this session, out of scope) — meaning a clean shutdown removes the file, so its *absence* is not proof a process never ran, only that either it never started or it shut down cleanly since; this ambiguity must be represented explicitly, not resolved by assumption.
**Safety:** entirely read-only file reads plus one external `psutil`/`ps` call — no new code path inside `run.py`, no restart needed to test it, testable today against the real PID 7644.
**Duplication risk:** none against Layer 1 (disjoint evidence domain); does not duplicate Candidate A, it *is* Candidate A plus a genuinely free second, independent corroborating source.
**Recommendation: this is the smallest justified next primitive — see §6.**

### Candidate D — another primitive already proposed by the repository's provenance architecture

The only other primitive named anywhere in the predecessor design corpus is `reconcile()` — the composer that would eventually join Layer 1 and Layer 2 evidence into one `ProvenanceObservation`. Explicitly out of scope here: it has no evidence of its own to gather, it only has meaning once at least one real Layer 2 primitive exists to reconcile against, and `provenance_implementation_boundary_audit.md` §13 already sequences it *after* the leaf primitives, not before. No other undiscovered "Candidate D" was found in this repository's provenance-labeled documents.

---

## 6. Smallest safe next primitive

**One primitive, named to make its scope impossible to overstate by accident (mirroring `working_tree_file_identity()`'s own `runtime_self_reported_module_origin` naming precedent, which encodes the self-attestation caveat directly into the function name):**

```
runtime_process_identity_and_self_report(pid: int) -> dict
```

This is Candidate A + Candidate C, unified into one function, because they share one contract and neither is useful alone: Candidate A without the self-report cross-check is just `ps`; Candidate C's self-report half without Candidate A's external half would be exactly the self-attestation-with-no-witness problem this whole research program exists to avoid.

**It is explicitly NOT Candidate B.** No part of this primitive touches `sys.modules`, imports anything, or makes any claim about which code the process is running beyond its command line and executable path (both external, both already proven observable in §5).

---

## 7. Implementation boundary

*(Specification only — no code written, per this mission's Phase 9.)*

**Primitive name:** `runtime_process_identity_and_self_report(pid: int) -> dict`

**Input:** a single `int` PID. No path argument, no free-text argument, no shell/command argument of any kind — this closes off the exact "generic wrapper" risk Layer 1's own security review (Phase 6/12 of the prior missions) already flagged as the one pattern to avoid.

**Output contract, structured to keep the three evidence kinds visibly separate (per Phase 7's "evidence, not labels" rule) — sketch of the *shape*, not code:**
```
{
  "pid": <int, echoed back>,
  "external_observation": {
      "process_exists": <bool>,
      "create_time_utc": <ISO8601 or None>,
      "cmdline": <list[str] or None>,
      "executable": <str or None>,
      "cwd": <str or None>,
  },
  "self_report": {
      "server_pid_file": {"exists": <bool>, "pid": <int or None>},
      "sentinel_file":   {"exists": <bool>, "pid": <int or None>,
                            "stage": <str or None>,
                            "start_utc": <str or None>,
                            "last_heartbeat_utc": <str or None>,
                            "heartbeat_age_seconds": <float or None>},
  },
  "cross_check": {
      "pid_matches": <bool or None>,          # external.pid == self_report pid(s)
      "start_time_within_tolerance": <bool or None>,  # a small, explicitly-stated tolerance window
  }
}
```
No field named `verified`, `active`, `live`, `connected`, or `trusted` anywhere in this shape.

**Evidence it may collect:** OS-level process-table facts for the given PID (via `psutil`, matching what `ps` would show); the literal contents of `memory/echo_server.pid` and `memory/echo_sentinel.json`, read as plain files exactly as `working_tree_file_identity()` already reads working-tree files; and a factual, narrowly-defined comparison between the two (equality of PID; a stated, disclosed tolerance for start-time closeness — informed by the real ~4.4s gap observed in §5, not an arbitrary number).

**Evidence it must not claim:** anything about `sys.modules`, imports, loaded code, or function execution (Candidate B territory — structurally excluded by the input/output contract having no module-name argument at all); anything framed as "Echo is running correctly" or "this process is healthy" (a system-guard/liveness-ledger-shaped judgment, a different, already-existing subsystem with its own, separately-established evidentiary basis); and it must never treat `self_report.*` agreeing with `external_observation.*` as proof of anything beyond "these two sources currently agree" — matching Layer 1's `modified_vs_head` precedent of reporting a comparison result without upgrading it to a verified-sounding label.

**Tests required, mirroring `scripts/verify_provenance_check.py`'s own established shape:** (1) real, live case against PID 7644 — confirm external and self-report facts both populate and agree; (2) a nonexistent PID — `process_exists: False`, all other external fields `None`, self-report fields still populate independently (since they don't depend on the PID argument being alive) with `pid_matches` correctly reporting `False` or `None` rather than crashing; (3) missing/corrupted `echo_server.pid`/`echo_sentinel.json` — `exists: False`/parse failure maps to `None`, never fabricated; (4) read-only guarantee — no file written, no process signaled, `git status`/`ps` state identical before and after; (5) a case proving `cross_check` fields become `None` (not `False`) when one side is genuinely unavailable — the identical "unknown ≠ false" discipline `_compose_identity()` already established and must not regress here.

**Runtime safety constraints:** read-only `psutil.Process(pid)` calls and read-only file opens only; no write, no signal, no `kill()`, no environment mutation, no code injection; testable today against the live PID 7644 with zero restart required, since none of this reads anything that doesn't already exist.

---

## 8. Open uncertainty

Cannot currently be established without modifying or instrumenting the running process (PID 7644), and this review does not propose doing so:

1. **Whether `app/core/self_heal.py` (or any specific module) is actually present in PID 7644's live `sys.modules`.** No external mechanism exists; the only path is new in-process code (Candidate B), which itself would need either a restart to deploy or an already-reachable live code path that does not currently exist.
2. **Whether any function inside any loaded module has ever actually been called** (§4 level 5) — no mechanism, self-report or external, exists anywhere in this codebase for this today, for any module.
3. **Whether `__file__` for a hypothetically-loaded module matches the current working-tree path** — genuinely dependent on (1) existing first; recorded in the predecessor design docs as `provenance_implementation_boundary_audit.md` §4's claim 9, unchanged by this review.
4. **The exact shutdown-path behavior of `memory/echo_server.pid`** (confirmed to be `unlink`'d somewhere via grep, not traced to its exact call site this session) — a minor, disclosed gap in this review's own thoroughness, not a blocker, since Candidate C's design already treats the file's absence as `exists: False`, never as a stronger negative claim.
5. **Whether `psutil.Process(pid)` on this specific PID could ever raise `AccessDenied`** on a differently-permissioned deployment (not observed here, since this is a same-user process) — a portability note for the eventual implementation, not tested this session since it doesn't apply to the current environment.

---

## Integrity

```
HEAD before this review:  6e835bfb3ae4c3f761a74d4af19c5fe931ca32d4
HEAD after this review:   6e835bfb3ae4c3f761a74d4af19c5fe931ca32d4   (unchanged)
Files modified:           none
Files created:            audits/2026-09-12_provenance_layer2_boundary_review.md (this file)
Staged:                   nothing
Committed:                nothing
Pushed:                   nothing
PID 7644:                 unchanged throughout -- confirmed via ps/psutil (read-only) at multiple
                           points during this review; same start time (Thu Sep 10 22:41:53 2026 /
                           2026-09-11T05:41:53 UTC) observed at every check
```
