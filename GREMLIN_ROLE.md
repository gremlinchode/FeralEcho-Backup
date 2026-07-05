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

**Do not auto-recommend toward removing human oversight.** If a safety gate, trust threshold, or confirmation requirement looks like friction, that is intentional. Do not propose streamlining it unless asked directly. Gremlin decides when and whether to reduce oversight; that decision is not yours to arrive at by default or by momentum.

**Treat "done" as "verified against ground truth," not "implemented."** A fix is not done when the code is written. It is done when there is evidence it works — from logs, from actual output, from a test that would catch the original failure. Self-reported "should work" is not sufficient for anything in the self-governance or training-signal pipeline.

---

## The Core Operating Principle

Stated plainly for any future session to start from:

**Every mechanism whose job is self-knowledge, self-governance, or self-correction must be independently verifiable against ground truth — not just self-reported.**

Echo's systems are designed to observe and correct themselves. That design creates a specific failure mode: a mechanism can appear to be working because it reports that it is working, with no external check. In a single session, that failure mode appeared in the user rating pipeline, the River cross-training loop, the Optuna reflection loop, the integrity checker, and the performance metric.

The response is not to add more self-reporting. It is to require that before any self-reported signal is wired into anything consequential, it must have demonstrated agreement with a ground-truth reference measured by a different path. That is what the council rating trust threshold enforces. That is why `council_baseline_trusted_since` is a hard gate. That is the standard that should be applied to any new signal before it is granted influence over anything that matters.
