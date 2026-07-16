# Risk Register

Investigation date: 2026-07-16, superseding the 2026-07-04 version in
place. Each finding rated Low / Medium / High / Critical with supporting
evidence, re-verified fresh this pass rather than copied from the prior
version. Ratings reflect risk to the owner's machine, data, and
credentials — not a judgment of the project's overall merit. Where an
original finding (R1-R11) is now resolved, that is stated plainly with
fresh evidence, not assumed from CLAUDE.md's own say-so.

## Status of the original Critical/High findings

### R1 (was CRITICAL) — Real API credentials committed to git — RESOLVED, re-confirmed fresh
`new_directory/app/core/env/environment.json` is confirmed **not tracked**
in the current repo (`git ls-files | grep new_directory` returns nothing).
`.gitignore` covers `new_directory/` explicitly (line 30). The original
audit already found the leaking commit was likely never pushed;
CLAUDE.md's Finding 7 documents the file being untracked via a clean
initial-commit rewrite on 2026-07-08. This pass independently re-confirms
the current state rather than trusting that account. **No further action
needed.**

### R2 (was HIGH) — Uncontrolled autonomous file/directory creation — ROOT CAUSE FIXED, residue is now historical
`self_edit_manager.py`'s path constants are confirmed, fresh, to be
anchored via `os.path.abspath(__file__)`, not relative/cwd-dependent
(re-verified directly against current source, not trusted from
CLAUDE.md). The 18 peripheral scaffold directories the original audit
found still exist on disk, but a fresh targeted secret-pattern grep across
all of them found zero new leaks. Two of the eighteen — `RebelCode/` and
`WhisperingWires/` — are corrected in this pass's dead_code.md: they are
live, tracked, genuinely-used subsystems, not scaffold clutter.
`RebelCode/territory_steward.py`'s `claim_new_ground()` (the second
original root cause) was not re-audited this pass. **Downgraded to
Low/informational** — the mechanism that produced the sprawl is fixed;
the existing sprawl is inert.

### R3 (was HIGH) — `/nuke` unauthenticated-adjacent kill switch — RESOLVED, re-confirmed fresh
`_secret_ok()` (`run.py`) now uses `hmac.compare_digest()` — genuinely
constant-time, confirmed by direct read this pass, not just cited from
CLAUDE.md. `GREMLIN_SECRET` is confirmed present in `.env` (key checked,
value not read). Fails closed if unset. **No further action needed** on
the auth mechanism itself; the underlying `0.0.0.0:5000` bind and
Tailscale-as-boundary assumption is unchanged — see R8 below.

### R4 (was HIGH) — Genuinely continuous, ungated autonomous self-modification — MITIGATED, not eliminated (by design)
The hourly self-edit loop is confirmed still firing (a real failure was
observed live during this very audit, 06:51:55 today, correctly rejected
with zero production impact — see runtime_observations.md). Since the
original audit: (1) a quality-score gate now rejects any candidate that
doesn't score at least as well as current production, directly targeting
the loop's own demonstrated non-convergence; (2) `apply_to_code()` hooks
are now smoke-tested inside the sandbox and write-blocked at call time
after a real incident where one smuggled unvalidated writes through an
approved import (CLAUDE.md Finding 31). The residual risk is unchanged in
kind from the original finding: a production process still self-modifies
its own live code on a fixed hourly timer with no external human approval
step. **This is confirmed to be a deliberate design decision, not an
oversight** — GREMLIN_ROLE.md explicitly excludes the F1/F2/F3 pipeline
itself from any roadmap aiming to change it. Rating held at **High**, with
the caveat that the gates around it are demonstrably more numerous and
more battle-tested than at the original audit.

## New finding — the single most important item this pass found

### R12 (HIGH, new) — `/mirror_echo`, the primary conversational entry point, has zero authentication
Confirmed by direct read, `run.py:485-520`. `/mirror_echo` — its own
in-code comment labels it the "MAIN ECHO ENTRY POINT" — accepts an
unauthenticated POST body, logs it (`logger.critical`), feeds it to
`dual_learner.log_event()` (permanent training-data ingestion used by
`/start_training`/`/download_model`) and to `echo_query()` (a real
conversational turn, which can itself write to FAISS memory via the
normal conversation path). No `_secret_ok()` call, no `hmac` check,
nothing — unlike every comparable POST endpoint (`/nuke`,
`/admin/restore`, `/admin/council-spotcheck`, `/inject_memory`,
`/force_nightcycle`, `/learning_event`, `/learning_batch`,
`/start_training`, `/memory/conversation`, `/sync/import`), all of which
were fixed with a shared `_secret_ok()` check in the 2026-07-08 pass this
audit's own predecessor recommended (CLAUDE.md Findings 14/15). This is
**not** the same as `/message/send`, which is deliberately unauthenticated
within the tailnet per the project owner's explicit, documented
confirmation (CLAUDE.md Finding 29) — no equivalent confirmation exists
anywhere for `/mirror_echo`. Anyone able to reach port 5000 could inject
arbitrary text that gets logged as a real interaction, fed into the
training-data pipeline, and answered by Echo as a genuine conversational
turn — the same risk class as the already-fixed `/inject_memory` gap
(poisoning long-lived state with attacker-controlled content), except
this path additionally feeds a model-training pipeline. **Recommend:**
flag to the project owner for an explicit decision (same posture as every
other auth-adjacent finding this project has handled — report, don't
silently fix) — either gate it with the existing `_secret_ok()` check
(same pattern as its siblings) or explicitly confirm it's meant to stay
open, the way `/message/send` was.

## Other current-state findings

### R5 (MEDIUM, unchanged) — ClaudeShard branding/implementation mismatch
Re-confirmed fresh this pass: no `anthropic` import, still
`random.random()` + keyword-marker gating. Unchanged from the original
audit in substance. **What's new**: this is no longer just documented —
`liveness_ledger.py`'s `claude_shard` check re-reads this exact source
every 120s and would fail loud the moment it stops being true. The risk
itself (a coin-flip signal branded as AI-derived) is unchanged; the
project's own ability to notice if that risk's premise silently changes
is substantially better than at the original audit.

### R6 (was MEDIUM, "wide-open admin/control surface") — RESOLVED for the originally-named endpoints, see R12 for the new instance
`/admin/restore`, `/admin/council-spotcheck`, `/inject_memory`,
`/force_nightcycle` are all confirmed gated by `_secret_ok()`, fresh this
pass. The general concern this finding raised (an unauthenticated
write-capable endpoint reachable at `0.0.0.0:5000`) recurred in a place
the original fix pass didn't cover — see R12.

### R7 (was MEDIUM, "dead subsystems create false confidence") — RESOLVED, upgraded from dead to honestly retired
Re-confirmed fresh: WOLF, SensoryHub, Bible art/interface, and the
continuity master are no longer silently dead — every code path now logs
or returns an honest "retired"/"disabled" status. `run.py`'s own header
comment states the real reason WOLF was retired (auto-approving raw
keystrokes as self-edit proposals against a hash-verified file) — a
genuinely more alarming original cause than "silent migration gap," now
transparently documented rather than hidden. **No further action needed.**

### R8 (MEDIUM, unchanged) — External network fetch surface run autonomously
Structurally unchanged: real, unattended HTTP requests to ~13 external
domains hourly, plus a real Anthropic API call path (now confirmed
successfully firing, where the original audit found it unconfirmed). This
remains by design; not re-scored.

### R9, R10 (were LOW) — Duplicate/backup files, 6,775-line orphaned file — RESOLVED, re-confirmed fresh
Both confirmed genuinely deleted this pass, not merely still-uncalled.
**No further action needed.**

### R11 (was LOW, "stale documentation") — RECURRING PATTERN, not a one-off
The original specific instance (CLAUDE.md's Finding 4, `cpu_tuning()`) is
itself now corrected in CLAUDE.md. A second, independent instance of the
identical failure mode was found this session (not this audit pass
specifically, but worth recording here): Phase 4 of the Emergence Roadmap
sat completely undocumented in CLAUDE.md for hours after being committed.
Two instances of the same pattern, in two different eras of the same
project's documentation, upgrades this from "one slip" to "a recurring
mode this project should watch for on an ongoing basis," even though the
project's overall documentation discipline (35 numbered, dated,
self-correcting Findings) is substantially more rigorous than at the
original audit. Rating held at **Low** — the pattern is annoying, not
dangerous, precisely because the project's own verification habits catch
it eventually.

### R13 (LOW-MEDIUM, new) — Self-edit non-convergence persists for `prose_stripping` specifically, despite a targeted fix attempt
`self_edit_convergence.json` shows the `prose_stripping` family at 94
cycles / 31 distinct function names — worse churn in raw terms than the
original audit's ~14-cycle sample. CLAUDE.md's Finding 32 (2026-07-15)
rewrote this family's prompt and explicitly flagged the result as
"hypothesis not proven." This pass observed a fresh real failure live
during its own runtime check (06:51:55 today), consistent with the issue
still being open. Not a safety risk (every failure here is caught by the
staging import test with zero production impact) — a code-quality/
resource-efficiency concern: hourly cycles are being spent on a family
that isn't converging.

### R14 (LOW, new) — Convergence-family classification bug
`self_edit_convergence.json`'s `unclassified` bucket holds 11 cycles with
30+ names that don't cleanly belong to any of the three named families.
This looks like a gap in the family-classification logic itself, not a
self-edit content problem. Not diagnosed further this pass — flagged for
a direct read of `self_edit_manager.py`'s `_CONVERGENCE_FAMILIES`
keyword-matching logic.

### R15 (LOW, informational) — Three odd tracked files from the original squashed commit
`./hello` (a trivial "Hello, world!" Mach-O binary), `./cd` (a real,
substantive Python script oddly named to shadow the shell builtin), and
`./moved` (literal "Hello, world!" text). All confirmed harmless this
pass — no risk, just repo clutter worth a cleanup pass someday.

## Reliability observations (not separately scored — informational)

- No crash loops or runaway resource consumption observed this pass.
- FAISS state is now healthy (47,607 real vectors, matching self-reported
  counts) — the original audit's single largest unresolved item is
  resolved.
- The council-rating and shadow-model calibration pipelines are both
  confirmed genuinely running but have not yet crossed their own internal
  trust/agreement thresholds — this is expected, ongoing accumulation, not
  a stall.

## Overall risk assessment

**Medium** (down from High at the original audit). Driven primarily by
R12 (`/mirror_echo`'s missing authentication — the one item this pass
recommends the project owner act on directly) and the accepted,
by-design residual risk of R4 (continuous autonomous self-modification,
now more heavily gated than before but still architecturally unsupervised
in the way GREMLIN_ROLE.md has deliberately chosen to keep it). Every
other Critical/High item from the original audit is confirmed resolved
with fresh evidence, not assumed. The project's own internal verification
tooling (the Liveness Ledger, 14 checks, 47 discrimination cases) is
itself a meaningful risk-reduction factor not present at the original
audit — it substantially lowers the odds that a regression in any of the
previously-fixed items would go unnoticed for long.
