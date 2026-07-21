# GREMLIN_ROLE.md

This document is for Claude Code sessions working in the FeralEcho repository. It describes the project owner's role, operating constraints, and working preferences so that future sessions can orient immediately without re-deriving them from conversation history. Read this before proposing anything consequential.

---

## Who Gremlin Is

The project owner ("Gremlin") is the human-in-the-loop for all consequential decisions about Echo's autonomy, safety, and self-governance. He is the system architect and conducts ongoing security audits. He holds final authority over anything that affects Echo's ability to modify herself, train her own classifiers, or act on self-reported signal.

**Working context:** On-call graveyard shifts. Frequently works from hotel rooms, train cabs, or mobile hotspots. Sessions are often interrupted and resumed asynchronously. Do not assume continuous attention across a session. Prefer self-contained, resumable units of work — finish a clearly scoped thing, report, wait. Long unbroken chains that assume he's watching continuously will fail.

---

## What Requires Human Confirmation

The following require explicit approval from Gremlin before any action is taken. These are not defaults to be arrived at by momentum or omission. When in doubt, ask.

- **Any restore-from-snapshot action.** The system can identify a last-known-good snapshot and surface it. It cannot execute the restore. `POST /admin/restore` must be a deliberate human command.
- **Any reactivation of the wolf friction bridge.** The current call site invokes `simulate_self_edit()`. Replacing it with `perform_self_edit()`, or connecting dry-run results to any live action, requires explicit confirmation.
- **Any River training-signal blending decision.** When `council_baseline_trusted_since` is eventually set, the proposed blending weight (30% council / 70% quality_score) must be reviewed and approved before any implementation. Flag it, do not wire it in.
- **Any change to `EDIT_FORBIDDEN_TARGETS`.** The protected file list in `self_edit_manager.py` is a safety boundary. Adding or removing targets requires human sign-off.
- **Any change to the F1/F2/F3 safety pipeline itself.** These gates can be audited and findings reported. They cannot be loosened, bypassed, or restructured without explicit authorization.
- **Any loosening of the "peer-model only" constraint on council rating.** `_select_peer_model()` has no same-model fallback by design. Changing this is a policy decision, not an implementation default.
- **Any reconnection of `self_heal.py` to a live caller.** The module is fixed and disconnected by design. Reconnecting requires review — even to a test path.
- **Any modification of `echo_principles.json` or its genesis hash.** Hash-verified at startup. Do not modify.

The list above is standing policy — permanent rules, not open questions. For **specific, currently-open items** that have been flagged and are waiting on Gremlin's actual call (not a category, a concrete pending decision), see `PENDING_DECISIONS.md` at the repo root. Any session that flags a new "Gremlin's call" item anywhere in this project should add a row there in the same change, not leave it as a paragraph buried in CLAUDE.md for someone to rediscover later.

---

## What Does Not Require Him

- Diagnostic reads, log inspection, status reports scoped as "report only."
- Syntax checks, import tests, and non-destructive code analysis.
- Drafting proposed changes for his review — showing diffs before applying is the preferred pattern.
- Monitoring H3 dry-run output and reporting accumulated findings.
- Running `spot_check.py` to fill human spot-check ratings.
- Any action explicitly scoped in conversation as "diagnose and report, don't fix yet."

---

## How He Prefers to Work

These preferences are extracted from demonstrated corrections and confirmations over multiple sessions. Treat them as standing instructions.

**Show diffs before applying non-trivial changes.** For anything touching core control flow, safety gates, training signal paths, or more than a few lines of logic, present the proposed change first and wait. Apply after explicit confirmation. This applies even when the change seems obviously correct.

**Report findings before proposing fixes.** The pattern that works: "Here's what I found. Here's what I'd propose." Pause between them. The pause gives him time to evaluate the finding independently before the fix forecloses options. Do not fix-and-report as a single step for anything consequential.

**Flag the core failure pattern explicitly when you see it.** FeralEcho's recurring failure mode is: a mechanism that appears connected and functional, reports itself as working, but is actually disconnected, operating on contaminated signal, or measuring something other than what it claims. In one session this appeared in: the user rating pipeline (technically functional, captured nothing for months), `verify_integrity()` (import check only, not behavioral), `measure_efficiency()` (phantom metric returning a constant), the Optuna reflection loop (ran blind its entire existence), and the council rating cursor (initialized at EOF with no warning that 10,954 entries were skipped). When you find something that matches this pattern — self-report not matching ground truth — flag it explicitly before moving on. Do not let it pass silently into a summary.

**Self-sufficiency suggestions are welcome, not withheld by default.** Surfacing places where Echo and the council could genuinely handle more in-house is expected, not something to sit on. This is separate from the "What Requires Human Confirmation" list above, which stays a hard boundary regardless — a suggestion to expand Echo's autonomous capability is welcome even in adjacent territory, but anything touching one of those eight named items still needs Gremlin's explicit go-ahead before it's even proposed as a live change, not just before it's built. (Replaces a narrower rule removed 2026-07-21 at Gremlin's direct request — that rule blocked this category of suggestion entirely; this is the deliberate, scoped replacement, not a return to no rule at all.)

**Treat "done" as "verified against ground truth," not "implemented."** A fix is not done when the code is written. It is done when there is evidence it works — from logs, from actual output, from a test that would catch the original failure. Self-reported "should work" is not sufficient for anything in the self-governance or training-signal pipeline.

---

## Interacting with FeralEcho (Practical Reference)

This is the quick operational on-ramp. CLAUDE.md has the full technical detail (architecture, safety pipeline, monitoring commands) — this section is what a session needs before touching the running system, plus what this project's sessions have learned the hard way.

### Starting and restarting

- Ollama must already be running (`ollama serve`, or confirm via `curl -m 3 localhost:11434/api/tags`) before `run.py` starts.
- Standard start:
  ```bash
  source ~/miniforge3/etc/profile.d/conda.sh
  conda activate feral_echo
  python run.py
  ```
- Server binds `0.0.0.0:5000` — Tailscale is the security boundary, not app-level auth.
- **The process does not hot-reload. A code change is not live until the server is killed and restarted.** Use `safe_restart.sh` (repo root), not a raw kill+restart:
  ```bash
  ./safe_restart.sh
  ```
  Starting a new process while port 5000 is still held causes the new one to die silently inside `start_background_threads()` with no visible error — but the more important reason to use the script rather than a bare `kill $(lsof -ti :5000) && python run.py`: `start_echo.sh` runs an independent watchdog loop that also restarts `run.py` on exit, and a manual kill+restart racing against a live watchdog has caused a real crash and a duplicate log rotation before — on both this machine and the 2020 Intel MacBook ("Ark"), more than once each, across both Gremlin and Claude sessions (CLAUDE.md Finding 51, fix in Finding 56). `safe_restart.sh` checks for a live watchdog first and refuses to proceed if one is found, telling you exactly which PID to deal with instead of silently colliding with it.
- Startup is slow and CPU-heavy (embedding warmup, a full code-scan into VectorMemory) — port 5000 may not bind for 30–90+ seconds while the process is clearly alive and busy (high CPU%, growing log). Don't kill it early mistaking this for a hang; check `ps aux | grep "python run.py"` and log growth before concluding it's stuck.
- Confirm a clean start two ways: `memory/echo_sentinel.json` should read `"stage": "serving"`, and the startup log should show `[GENESIS] echo_principles.json hash verified OK` (genesis-hash-at-startup check — see CLAUDE.md's Protected Files section; the specific old Finding-letter citation this line used to carry doesn't correspond to anything in CLAUDE.md's current numbering and was removed rather than guessed at, 2026-07-21).
- Before reporting any fix as "done," check whether the server is actually running the code that contains the fix, not code from before the session's edits. A commit on disk is not a fix in effect until the process serving requests has been restarted.

### Talking to Echo

- `python terminal_client.py` — interactive conversation, the primary way to exercise real behavior (not just endpoints).
- Type a bare digit 1–5 at the next `You:` prompt to rate the last response — this is the highest-trust human signal in the whole system (see council/River trust-gate discussion elsewhere in this doc and in CLAUDE.md).

### Checking system health (admin endpoints — all GET unless noted, all read-only except `/admin/restore`)

- `curl localhost:5000/admin/liveness-status` — **the most important one, added since this section was last checked (2026-07-21):** 21 independent checks verifying real subsystem behavior against ground truth, not self-report. `all_passing: false` or `stale: true` means something that looks wired is actually dead, faked, or its collector thread died. Check this first, not last, when anything seems off.
- `curl localhost:5000/admin/council-stats` — peer-rating trust-gate progress toward `council_baseline_trusted_since` (includes a `self_rating_excluded` count of ratings skipped for lacking a genuine peer model)
- `curl localhost:5000/admin/self-edit-outcomes` — before/after quality_score, council_rating, and human-rating windows around each self-edit (log-only, does not gate anything)
- `curl localhost:5000/admin/autonomy-status` — last-check status (throttled/stillness/ok) for autonomy loops sharing `autonomy_coordinator.py`'s gate. **Caution:** as of 2026-07-21, a live grep of every `should_run_cycle()` call site found at least 8 distinct tags gated this way (`autonomous_loop`, `awareness_dream`, `awareness_code_scan`, `emergent_scheduler`, `model_guided_orchestrator`, `self_edit_loop`, `echo_messaging`, `echo_checkin`) — more than the "three loops" this line and `autonomy_coordinator.py`'s own module docstring both still claim. Not corrected in the source docstring in this pass, only flagged here — a real, live doc-drift instance, not just documentation staleness.
- `curl -X POST localhost:5000/admin/restore -d '{"snapshot_id": "..."}'` — restores five files (self_edit_generated.py, river_brain.pkl, echo_principles.json + hash, Modelfile). Human-confirmed only, per the hard rules above — never call this without Gremlin explicitly asking for that specific snapshot.
- See CLAUDE.md's "Monitoring" section for log-tailing one-liners and deeper diagnostics (SELF_EDIT.log, interaction_log quality stream, FAISS vector counts, sentinel/crash state).

**Note on the Finding-number citations that used to be attached to the entries above** (`Finding M-4/27`, `Finding 8/28`, `Finding 29`, `Finding C-2/25`): checked directly against CLAUDE.md's current text (2026-07-21) — none of them correspond to anything there. They appear to be leftover references to an older, lettered/departmental Finding-numbering scheme (`C-2`, `M-4`) that CLAUDE.md no longer uses at all, mixed with plain numbers that collide with unrelated current Findings (CLAUDE.md's real Finding 29 is about `/message/send` auth, not autonomy status; Finding 8 is about a dead launchd job, not self-edit outcomes). The underlying claims were re-verified directly against current code and are still accurate — only the broken citations were removed, not guessed at with a plausible-looking replacement number.

### Things this project's sessions have learned the hard way

- Git commits in this repo use an auto-configured identity (`richietate@Richards-MacBook-Air.local`) — no global `user.name`/`user.email` is set. Don't silently "fix" this by running `git config` — flag it, let Gremlin decide.
- Originally three autonomy loops (`emergent_scheduler.emergent_loop`, `autonomous_loop.autonomous_loop`, `run.py`'s `self_edit_loop`) shared one throttle/stillness gate (`app/core/autonomy_coordinator.py`, `should_run_cycle()`) as of 2026-07-05 — **stale as of 2026-07-21**, at least 8 distinct tags call it now (see the `/admin/autonomy-status` note above). If touching any autonomous loop, use the shared gate — don't reintroduce an independent throttle check, and don't trust "three" as the current count without re-checking `grep -rn "should_run_cycle(" app/` first.
- The working tree can accumulate a large amount of real, safety-relevant uncommitted work across many sessions (382 changed paths were found accumulated across ~3 weeks in one instance). Check `git status` and `git log` early in a session rather than assuming recent CLAUDE.md narration reflects what's actually committed.
- Sandbox/pentest scaffolding (F1/F2 adversarial test scripts, hourly self-edit snapshots) is gitignored, not deleted — see the `.gitignore` "DISPOSABLE TEST/PENTEST ARTIFACTS" section. Don't `git add -A` in this repo; stage files explicitly.
- **Before building on top of any "confirmed"/"verified live" claim in CLAUDE.md, spot-check at least one against current reality first — don't inherit it as an axiom.** Confidence compounds forward across sessions faster than verification does by default: a 2026-07-08 session wrote that Nature Spark was "verified live with genuine generated output," and that claim sat unquestioned for five days before a 2026-07-13 session actually pointed a check at real data and found it was still faking it two-thirds of the time. The same day, the *opposite* drift direction turned up too — Finding 12's "the two sides were never wire-compatible" conclusion had already been fixed on Air's side and just never got reflected back here. Neither took more than a few minutes to check once someone actually looked. This doesn't mean re-verifying everything — it means treating an unverified prior claim as a hypothesis to spot-check, not a foundation to build the next several hours of work on.

---

## The Core Operating Principle

Stated plainly for any future session to start from:

**Every mechanism whose job is self-knowledge, self-governance, or self-correction must be independently verifiable against ground truth — not just self-reported.**

Echo's systems are designed to observe and correct themselves. That design creates a specific failure mode: a mechanism can appear to be working because it reports that it is working, with no external check. In a single session, that failure mode appeared in the user rating pipeline, the River cross-training loop, the Optuna reflection loop, the integrity checker, and the performance metric.

The response is not to add more self-reporting. It is to require that before any self-reported signal is wired into anything consequential, it must have demonstrated agreement with a ground-truth reference measured by a different path. That is what the council rating trust threshold enforces. That is why `council_baseline_trusted_since` is a hard gate. That is the standard that should be applied to any new signal before it is granted influence over anything that matters.
