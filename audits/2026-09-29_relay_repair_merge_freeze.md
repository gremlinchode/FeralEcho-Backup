# Relay Repair Merge Freeze — Post-Merge State Record

**Merge + verification mission.** Prior gate report
(`audits/2026-09-29_relay_repair_final_premerge_gate.md`, verdict MERGE WITH
QUALIFICATIONS) re-verified against live repository state before merging. Not
pushed. LaunchAgents not activated. Echo and manual relay processes untouched.

## Merge Verdict

# MERGED

## Phase 1 — Ground Truth Re-Established (not trusted from the prompt)

- Branch at mission start: `vsl-implementation`, HEAD `e5acbb09cece8d1791fa6d967fe57067137a8cff`.
- All four candidate commits confirmed as real ancestors of this HEAD via
  `git merge-base --is-ancestor` (not merely assumed from abbreviated hashes):
  `ea22d75356b3736b601f98400ff18cf36a35ec09`,
  `630287c44d45b7c7022acd45b436c8cbd4cb7a70`,
  `0a134d3ecbdd62b7b430637a3a31d45c9eb539ee`,
  `e5acbb09cece8d1791fa6d967fe57067137a8cff`.
- `origin/main` (cached, last fetched before this mission — a live `git fetch`
  attempt failed on `Permission denied (publickey)`, an expected, pre-existing
  credential limitation in this environment, not a new discrepancy) sits at
  `efeb565b3221eb6ff9d7a65a3c9f3232f16806d0`, strictly behind the candidate.
- **A real discrepancy was found and resolved before merging, not glossed
  over**: local `main` existed and pointed to `89a8c80973a691b63c539102b703453a9bb65491`
  — a commit *behind* both `origin/main` and the candidate (confirmed via
  `git merge-base --is-ancestor main HEAD`, true). This is not a genuine
  divergence with incompatible content — the reflog shows `main` was
  repeatedly, deliberately reset to earlier `vsl-implementation` checkpoints by
  prior sessions in this same project's own workflow, not organically diverged.
  Merging was therefore a clean, safe fast-forward, not a three-way merge.
- 44 dirty/untracked paths present, all pre-existing and unrelated (this
  session's own accumulated audit reports, conversation-state relay files,
  and other in-flight working-tree state) — none touched by this mission.
- The final gate report (`audits/2026-09-29_relay_repair_final_premerge_gate.md`)
  is preserved, untracked, unchanged.

## Phase 2 — Merge Performed

`main` was fast-forwarded to `e5acbb0` via `git branch -f main e5acbb0` —
deliberately a ref update rather than `git checkout main && git merge`, to avoid
disturbing the 44 pre-existing uncommitted changes sitting in the working tree
(a `checkout` risks conflicting with local modifications to tracked files; a
ref-only fast-forward touches nothing in the working tree or index). This
preserves every commit exactly as reviewed — no squash, no rebase, no rewrite.
`vsl-implementation` remained the active branch throughout; the working tree was
never switched.

**Distinction made explicit, per this mission's own requirement**: `main` now
*contains* the relay reliability repair. Nothing about the *running system* has
changed — no LaunchAgent was loaded, no relay process was restarted, Echo's own
`run.py` was never touched. **Repository integration and runtime activation are
two separate facts, and only the first happened.**

## Phase 3 — Post-Merge Verification (Isolated Worktree)

All checks run from a fresh `git worktree --detach` at `main`'s new HEAD — not
inferred from the pre-merge gate's own results, independently re-run:

- **26/26 tests pass** (`claude_relay.test_relay`, `codex_relay.test_relay`,
  `hub.test_check_hub`), relay env vars (`CODEX_RELAY_SECRET`, `HUB_CHECKED_BY`)
  explicitly unset.
- The path-traversal regression test (`test_c7_path_traversal_consumer_name_is_rejected`)
  re-run specifically and directly, both modules: pass.
- **Live functional check, not just unit test**: two independent named
  consumers (`consumerA`, `consumerB`) against a real seeded inbox — confirmed
  directly that consumer B's cursor file does not exist after consumer A reads,
  proving isolation holds in real use, not only in the mocked test harness.
- Legacy behavior (`--consumer` omitted) re-confirmed unchanged.
- **Genuine negative control, the strongest form available**: `claude_relay/`,
  `codex_relay/`, and `hub/` were physically removed (moved out, not deleted)
  from the isolated worktree entirely, and two real, substantial core Echo
  modules — `app.core.liveness_ledger` and `app.core.self_edit_manager` — were
  imported successfully with all relay/hub infrastructure completely absent
  from the filesystem, not merely absent from a grep. Both imported cleanly.
  Directories were restored afterward (worktree is disposable regardless).
- Credential re-scan against the merged history: clean, no matches beyond
  expected variable/flag *names*.
- Both plists re-validated (`plutil -lint`): OK.
- `launchctl list | grep gremlin.relay`: empty, confirmed not loaded, both
  before and after the merge.
- Echo (PID 71538) and both manual relay processes (PIDs 84828/84838):
  unchanged uptime, never restarted or signaled.

**No regression was introduced by the merge.** Nothing required repair in this
phase.

## Remaining Relay Qualifications

Preserved, not silently dropped:

- **Q1** — two callers that both omit `--consumer` still share one legacy
  cursor. Accepted, deliberate backward compatibility.
- **Q2** — an explicit `--checked-by` claim can still assert a false identity.
  Accepted, since `checked_by` has zero consumers (re-verified during the
  pre-merge gate, not re-derived again here to avoid redundant work already
  proven current).
- **New (from the pre-merge gate, now inherited by `main`)**: the path-traversal
  fix (`e5acbb0`) closes the specific demonstrated vector for `--consumer`; it
  is not a general filesystem-path-safety audit of either script beyond that
  one flag. The regression test protecting this boundary (`test_c7_*`) remains
  part of the permanent suite — no reason was found to remove it.

## Relay Engineering: CLOSED for this mission

Per the mission's own instruction, this branch of work stops here. LaunchAgent
activation remains a distinct, later, explicitly human-authorized step — the
"Future LaunchAgent Activation Procedure" already documented in the pre-merge
gate report is not executed and not superseded by this merge.
