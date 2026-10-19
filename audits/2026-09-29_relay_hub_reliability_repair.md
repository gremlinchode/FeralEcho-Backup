# Relay Reliability Repair — Consumer Isolation, Truthful Attribution, Durable Supervision & Zero-Dependency Guarantee

**Bounded implementation + adversarial verification.** Prior investigation
(`audits/2026-09-29_relay_hub_reliability_semantics_audit.md`) read in full before
any change. Not pushed — commits only, per the mission's explicit hard stop.

## 1. Executive Verdict

# REPAIR PASS WITH QUALIFICATIONS

All three bounded weaknesses the audit identified were repaired, verified by test,
and committed. The zero-dependency invariant was checked before repair (Phase 1)
and re-checked after, from an isolated worktree (Phase 15/16) — confirmed true both
times. Two real bugs were found and fixed *during* this repair that the audit did
not anticipate: a genuine concurrency race in `claude_relay`'s cursor-save logic
(reproduced 6/8 failing runs before the fix), and a test-infrastructure module-name
collision between the two new test files. "With qualifications" because: the new
LaunchAgents are deliberately **not yet activated** (Section 10 explains why), and
the attribution fix closes the *silent, automatic* false-claim case but cannot, by
itself, prevent a caller from *explicitly* lying about its own identity — a limit
stated honestly rather than glossed over.

## 2. Architectural Invariant

> **Claude/Codex relays are optional infrastructure and never required for core
> Echo operation.**

Checked before writing any code (Phase 1) and re-checked after, from a clean
worktree (Phase 13). Both times: **zero core dependency found.** This invariant is
not newly established by this repair — it was already true of the existing
architecture — but it is now the explicit, checked premise every change in this
report was made to preserve, not a background assumption.

## 3. Baseline

- `2026-09-29T15:27 UTC` / `08:27 PDT`. HEAD `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`,
  0 ahead/0 behind `origin/main`; 42 pre-existing dirty paths, untouched by this
  mission.
- Echo (`run.py`): PID 71538, running since `2026-09-28 19:15:54`; never
  restarted, stopped, or signaled at any point in this mission.
- Relay servers, re-verified current: `claude` identity PID 84828 (`127.0.0.1:8765`),
  `codex` identity PID 84838 (`127.0.0.1:8767`) — both the same manually-started
  processes from earlier today, never restarted by this repair (Section 10 explains
  why the new supervision wasn't activated on top of them).
- Hub health: all five channels `alive` before and after every change.

## 4. Pre-Repair Dependency Audit

Exhaustive `grep` across `app/` and `run.py` for every relay/hub-adjacent term
(`claude_relay`, `codex_relay`, `hub/check_hub`, `hub/notes`, `8765`, `8767`,
`CODEX_RELAY_SECRET`) found exactly two hits, both inspected directly:

| File | Line | Classification |
|---|---|---|
| `app/core/self_edit_manager.py:869` | a code comment citing `claude_relay/facts_m5.jsonl` as the historical source of a cross-check finding | **OBSERVABILITY / PROVENANCE CITATION** — no import, no call |
| `app/core/liveness_ledger.py:3872` | a code comment citing `claude_relay/facts_m5.jsonl` as the historical motivation for a specific check's design | **OBSERVABILITY / PROVENANCE CITATION** — no import, no call |

**No core dependency found. Gate cleared; proceeded per the mission's own
instruction.** (Every other hit outside `app/`/`run.py` — `codex_relay/relay.py`,
`claude_relay/relay.py`, `hub/notes.py`, `hub/check_hub.py` themselves, plus three
research-tooling files under `app/experiments/` — is the relay/hub code itself or
explicitly-separate research tooling, not core runtime.)

## 5. Cursor Repair

**Design**: an explicit, optional `--consumer <name>` on both relay scripts' `read`/
`status` commands. `None` (the default, omitted) reproduces the exact original
marker filename and behavior — every existing caller is byte-for-byte unaffected. A
named consumer gets its own independent marker file
(`.last_seen__<name>.json` / `.last_seen_from_<peer>__<name>.json`), so two
genuinely separate readers of the same inbox no longer share one "what's new"
position. Deliberately requires a **stable, caller-chosen** name — never an
auto-generated one per invocation, which the mission correctly flagged as worse
than the problem it would "solve" (a fresh identity every call would replay the
entire backlog forever). `claude_relay`'s existing, already-correct `read-hub`
mechanism (fixed independently by Air on 2026-09-16, per the audit's own Section 7
finding) was **not touched, not rewritten** — this adds a general mechanism
alongside it for any *future* independent consumer, per the mission's explicit
instruction not to redo already-working history.

**A real bug was found and fixed during this repair, not theorized in advance**:
writing the concurrent-access discrimination test (C6) for `claude_relay`'s cursor
reproducibly triggered `FileNotFoundError` 6 of 8 runs. Root cause: `_save_marker()`
used one fixed, shared `<marker_file>.tmp` name — two simultaneous writers racing
on it meant whichever called `os.replace()` second found its own tmp file already
moved away by the first. Fixed with a per-call-unique tmp filename
(`.{pid}.{thread_id}.tmp`) — the identical fix shape this project already proved
correct for the same race class elsewhere (CLAUDE.md Finding 41 B2,
`echo_core.py`'s `_persist_salience_state()`). Verified 5/5 clean runs after the
fix. `codex_relay`'s equivalent (`marker_path.write_text()`, a single syscall, no
tmp/rename step at all) was checked and did not reproduce the same failure in its
own C6 test — a narrower, already-benign write pattern for this specific race,
left unchanged.

## 6. Cursor Tests

22 tests total across both relay modules plus attribution (Section 7), all
passing, individually and together (the "together" run matters — see Section 5.1
below).

| Test | Module | Result |
|---|---|---|
| C1 — independent consumers don't steal each other's unread | both | pass |
| C2 — same consumer resumes correctly after exit | both | pass |
| C3 — different consumer IDs never collide on disk | both | pass |
| C4 — `notes.py`'s existing `read-hub` isolation stays intact | `claude_relay` | pass |
| C5 — legacy/default consumer is unchanged and deterministic | both | pass |
| C6 — concurrent access does not corrupt state | both | pass (found and fixed a real race first, Section 5) |

**A second real bug was found while running both new test files together, not
individually**: both used a bare `import relay` after a `sys.path` insert; since
`claude_relay/relay.py` and `codex_relay/relay.py` are two different files that
happen to share the literal module name `relay`, running both test suites in one
Python process let the second import silently reuse the first's cached
`sys.modules["relay"]` entry — testing the *wrong* module's code entirely. Fixed
by loading each under an explicit, unique module name via `importlib`
(`claude_relay_relay` / `codex_relay_relay`). Re-verified: 22/22 pass together and
individually, every time, including a direct before/after comparison (8 failures
→ 0, both real bugs fixed).

## 7. Attribution Repair

`hub/check_hub.py`'s unconditional `"checked_by": "claude-m5"` literal is removed.
New `resolve_checked_by(argv, env)` — pure, unit-tested, zero I/O beyond its two
inputs — resolves identity in priority order: an explicit `--checked-by <name>`
CLI argument, then the `HUB_CHECKED_BY` environment variable, then the honest,
non-attributing default `"unknown"`. **Never** falls back to `"claude-m5"` or any
other specific identity when none is supplied. Verified live: a real
`python3 hub/check_hub.py` run with neither flag nor env var set now correctly
writes `"checked_by": "unknown"` for every one of the five real channel checks —
confirmed by reading the actual new `hub/status.jsonl` entries back, not merely
by unit test.

Seven tests (`hub/test_check_hub.py`): A1 (explicit Claude identity is truthful),
A2 (explicit Codex identity is truthful), A3 (no identity → honest `"unknown"`),
A4 (governance-safety meta-test, Section 8), A5 (the literal historical bug —
default callers no longer silently become `"claude-m5"`), plus CLI-vs-env priority
and env-only resolution. All pass.

## 8. Governance Safety

Re-derived by grep, both before writing the fix and as a **permanent regression
test** (`test_a4_identity_field_grants_no_authority_anywhere`) that re-checks this
on every future test run rather than trusting a one-time audit finding forever:
`checked_by` has **zero consumers anywhere in the tracked codebase** outside
`hub/check_hub.py`'s own write site. It does not influence restore, dissent,
liveness, Protector scaffolding, self-edit approval, VSL promotion, deployment, or
rollback — none of those subsystems reference `hub/` at all (confirmed
independently by the same Section 4 dependency audit). **Currently, and after this
repair, purely informational.** The regression test exists specifically so a
future change that starts reading this field for something authoritative gets
caught by the test suite immediately, not discovered later the way the original
hardcoding was.

## 9. Supervision Design

Compared against every named alternative, using only what already exists in this
codebase (no new supervisor invented): `start_echo.sh`/Echo's watchdog were
rejected as the owner (would conflate two genuinely unrelated concerns and risks
the exact two-supervisor collision class CLAUDE.md's Finding 51 already documents
for a different pair of processes). launchd, modeled directly on the existing
`com.gremlin.echo.plist` precedent, is the best-fitting mechanism already proven
in this exact project. **Two separate LaunchAgents** (one per relay identity,
`com.gremlin.relay.claude` / `com.gremlin.relay.codex`), not one supervisor owning
both processes — this gives launchd genuine per-process crash detection and
independent restart, rather than only seeing one wrapper's own exit status.

`Echo lifecycle` and `Relay lifecycle` are fully independent by construction: the
new plists reference nothing in `run.py`/`start_echo.sh`, and the dependency audit
(Section 4) already confirms nothing in Echo's own runtime references the relay.

## 10. Supervision Implementation

- `codex_relay/start_local_relay_claude.sh` / `start_local_relay_codex.sh`: each
  reads `CODEX_RELAY_SECRET` from the existing, already-permission-protected
  `~/.claude-codex-relay/secret` file **at runtime**, runs its own crash-restart
  `while true` loop — the identical pattern `start_echo.sh` already uses for Echo
  — and logs to its own dedicated file. Neither script contains a secret value;
  both refuse to start cleanly (exit 1, logged) if the secret file is absent,
  rather than crash-looping against a `ValueError`.
- `codex_relay/com.gremlin.relay.claude.plist` / `com.gremlin.relay.codex.plist`:
  each points only at its own wrapper script, `RunAtLoad`, distinct stdout/stderr
  log paths under `~/.claude-codex-relay/`. **No secret value appears in either
  plist** — confirmed by direct inspection, not merely by design intent.
- Verified: `plutil -lint` passes on both plists; `zsh -n` passes on both scripts;
  `launchctl list | grep gremlin.relay` confirms **neither is loaded** right now.
- **Deliberately not activated in this pass.** Both relay identities are already
  running as manually-started processes from earlier today (PIDs 84828/84838,
  Section 3). Loading these LaunchAgents now would start a second, colliding pair
  fighting over the same two ports — the exact two-supervisor collision CLAUDE.md's
  own Finding 65 already documents and deliberately deferred for Echo's own plist,
  for the identical reason. Activation is a one-line follow-up
  (`cp codex_relay/com.gremlin.relay.*.plist ~/Library/LaunchAgents/ && launchctl
  load ...`) for whenever no manually-started instance is running — not performed
  here, per that same precedent.

## 11. Subscription / Availability Failure Semantics

Verified architecturally (Section 4's dependency audit already proves each row
below) and, for the "both unavailable" case, **by real, already-collected natural
evidence** rather than a new synthetic test:

| Scenario | Outcome |
|---|---|
| Claude unavailable | Codex relay (M5↔Air) and Echo both remain fully functional — no code path in either depends on Claude's presence. |
| Codex unavailable | Claude relay and Echo both remain fully functional — symmetric reasoning. |
| Both unavailable | **Echo remains functional — not just architecturally, but empirically demonstrated**: the local relay was completely down for the ~13 days the prior audit documented, and separately, this exact session's own earlier "Natural Learning Event Hunt" missions found Echo's `run.py` process (PID 71538, running continuously since well before this session restarted the local relay) generating real conversational responses, real self-edit attempts, and real RiverBrain adaptation throughout that same window — genuine zero-relay operation, already observed, not merely inferred. |
| Authentication expired | The relay's own `secret_from_env()` raises a clean `ValueError` at `send`/`serve` time — reported by the relay's own CLI, never propagates into or blocks anything Echo-side. |
| Relay server absent | `hub/check_hub.py` reports that one channel `unreachable`/`not_set_up`; the other four channels (including both Echo ones) are checked and reported completely independently (Section 12). |
| Subscription permanently cancelled | No code change required anywhere in `app/`/`run.py` — confirmed by the same zero-dependency finding. |

## 12. Hub Health Semantics

**Checked directly: no repair was needed here.** `hub/check_hub.py`'s `main()`
never computes or has ever computed a single combined "overall healthy" verdict
across its five channels — each of the five `check_*` functions calls
`append_status()` independently, and nothing anywhere aggregates them. The one
`all_passing` reference in the file (`check_echo_m5()`) is Echo's *own* internal
liveness-ledger value, reported as evidence text for the `echo_m5_liveness`
channel specifically — not a hub-wide rollup that could conflate "Claude relay is
down" with "FeralEcho is unhealthy." **CORE HEALTH (the two Echo channels) and
OPTIONAL CHANNEL HEALTH (the three relay channels) were already structurally
separate, by the simple fact that nothing combines them** — confirmed rather than
assumed, and left unchanged per the mission's own "do not redesign unless
necessary" instruction.

## 13. Zero-Relay Verification

From an isolated `git worktree --detach` at this repair's final commit, with a
stripped environment (`env -i`, no `CODEX_RELAY_SECRET`, no inherited shell
state): `run.py` parses cleanly; the same dependency-audit grep against `app/`
and `run.py` returns the identical two comment-only hits as Section 4, nothing
new. This confirms the repair itself introduced no new core dependency, on top of
Section 11's confirmation that none existed before.

## 14. Clean-Room Verification

Same isolated worktree, same stripped environment: all 22 tests
(`claude_relay.test_relay`, `codex_relay.test_relay`, `hub.test_check_hub`) pass —
**with no `CODEX_RELAY_SECRET` set at all**, confirming that merely *importing*
either relay module (as the tests must) never requires the secret; only the real
`send`/`serve` code paths do. No dirty local artifact (the pre-existing, unrelated
42 dirty paths noted in Section 3) was required for any test to pass — the
worktree's checkout was entirely clean of them.

## 15. Adversarial Results

| # | Question | Result |
|---|---|---|
| F1 | Can consumer A still steal consumer B's cursor? | **No, for named consumers** (C1/C3, verified). **Yes, still, for two callers that both omit `--consumer`** — this is the preserved legacy default, not a new defect; isolation is now available, not retroactively forced on backward-compatible callers. Stated precisely, not glossed over. |
| F2 | Can two consumers collide by default? | Same answer as F1 — by design, for Phase 4's own backward-compatibility requirement. |
| F3 | Can attribution still falsely claim Claude? | Only via an **explicit**, auditable `--checked-by claude-m5` claim from a caller that isn't actually Claude — a fundamentally different, visible risk than the old *automatic, silent* default. This fix closes the silent case; it cannot (without real authentication) prevent an explicit lie, and this report does not claim otherwise. |
| F4 | Can an arbitrary identity string gain authority? | No — confirmed via the A4 regression test; zero consumers exist anywhere. |
| F5 | Can relay startup failure prevent Echo startup? | No — confirmed architecturally (Section 4) and by design (Section 9's fully independent LaunchAgents). |
| F6 | Can relay death restart or damage Echo? | No — same reasoning. |
| F7 | Can Hub report core failure merely because subscriptions are unavailable? | No — confirmed, no aggregation exists (Section 12). |
| F8 | Can any governance path block indefinitely waiting for Claude/Codex? | No — confirmed, zero governance code references relay infrastructure (Section 4/8). |
| F9 | Do credentials appear in logs/plists/process arguments? | No — confirmed by direct `ps -ww` inspection of the real running processes' actual argv, and by inspecting both new plists/scripts directly. (One false-positive was caught and corrected during this check: a `grep -i "secret\|CODEX_RELAY"` incidentally matched the innocuous path substring `codex_relay` itself in the command line — the real argv was re-read directly and contains no credential value.) |
| F10 | Does a clean checkout require untracked relay state? | The secret file lives outside the repo entirely (`~/.claude-codex-relay/secret`, never tracked) and must be separately provisioned by the operator — this is the pre-existing, disclosed, intended secret-management design (per `codex_relay/README.md`'s own setup instructions), not a new requirement this repair introduced. |

**No F5–F9-class defect was found — no stop condition triggered.**

## 16. Remaining Limitations

- F1/F2's preserved default-collision case (stated above) — closing it fully would
  mean either breaking backward compatibility or picking an opinionated default
  consumer name for every caller, neither of which this mission's own scope asked
  for.
- F3's explicit-claim limitation — closing this would require real peer
  authentication for `hub/check_hub.py` callers, a materially larger change than a
  "reliability repair."
- The new LaunchAgents remain unactivated (Section 10) — a deliberate, disclosed
  deferral, not a completed task.
- No acknowledgement semantics, autonomous Claude↔Codex messaging, or Echo relay
  integration were added — explicitly out of scope per the mission's own "DO NOT
  IMPLEMENT" list, and not implemented.

## 17. Commits

All on branch `vsl-implementation`, none pushed:

- `ea22d75` — isolate relay consumer cursors (`claude_relay/relay.py`,
  `claude_relay/test_relay.py`, `codex_relay/relay.py`, `codex_relay/test_relay.py`;
  294 insertions, 19 deletions).
- `630287c` — make hub checker attribution truthful (`hub/check_hub.py`,
  `hub/test_check_hub.py`; 124 insertions, 1 deletion).
- `0a134d3` — add optional relay supervision, not yet activated
  (`codex_relay/com.gremlin.relay.claude.plist`,
  `codex_relay/com.gremlin.relay.codex.plist`,
  `codex_relay/start_local_relay_claude.sh`,
  `codex_relay/start_local_relay_codex.sh`; 136 insertions).

Each staged diff was inspected before committing (`git diff --cached`); each
contains only its own logically-scoped files; no credential material appears in
any commit (checked directly, not merely assumed); the full 22-test suite was run
and passed before every commit that touched test-relevant code.

## 18. Repository State

- HEAD: `0a134d3` (3 commits ahead of the `efeb565` baseline this mission started
  from), branch `vsl-implementation`. **Not pushed.**
- Working tree: only the same 42 pre-existing, unrelated dirty paths from Section 3
  remain (plus their ordinary runtime drift — `hub/status.jsonl`/`hub/notes.jsonl`
  continuing to accumulate real check/note activity, and `claude_relay`'s own
  mailbox/cursor files reflecting this session's genuine prior relay use) —
  nothing from this repair's own source changes is uncommitted.
- Echo (PID 71538) and both relay processes (PIDs 84828/84838) are exactly the
  same, uninterrupted processes as at Section 3's baseline.

## 19. What This Establishes

- The two specific, real reliability defects the prior audit found are repaired,
  tested, and committed: general cursor-consumer collision (beyond the
  already-fixed notes.py case) and hardcoded attribution.
- A durable, launchd-based supervision design exists, validated for syntax and
  non-interference, ready to activate when no manual instance conflicts.
- The zero-core-dependency invariant was true before this repair and remains true
  after it, checked twice, once from an isolated clean-room worktree.
- Two real bugs neither the audit nor the original mission brief anticipated were
  found and fixed during implementation: a genuine concurrency race in cursor
  persistence, and a test-infrastructure module-naming collision — both because
  this repair's own adversarial test-writing (C6, and running both new suites
  together) actually exercised conditions the original code had never been tested
  against.

## 20. What This Does NOT Establish

Explicitly, per the mission's own requirement:

- **Does not establish autonomous Claude↔Codex collaboration** — every use of
  these channels this session, before and during this repair, was human-directed
  session activity, not self-initiated agent behavior.
- **Does not establish Echo's use of the relay** — confirmed structurally
  uninvolved, unchanged by this repair.
- **Does not establish reliable external-agent availability** — Claude and Codex
  remain exactly as available or unavailable as their own underlying subscriptions
  make them; nothing here changes that.
- **Does not add acknowledgement semantics** — a sender still cannot distinguish
  "accepted" from "read" from "acted upon," unchanged from the audit's own finding.
- **Does not establish exactly-once delivery** — the existing at-least-once
  submission / effectively-at-most-once-per-named-consumer consumption model is
  unchanged in kind, only extended to support more than one named consumer safely.
- **Does not require, and specifically never assumes, any Claude/Codex
  subscription** — this is the repair's own central, twice-verified premise
  (Sections 4, 13), not an incidental property.
