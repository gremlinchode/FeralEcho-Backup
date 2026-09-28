# VSL Reproducibility Repair — Final Report

## 1. Original broken `main` commit

`607c6d0024c7bc0810dcb0d446cd9c664551a1b2` (the final adversarial-gate commit, pushed to
`origin/main` before this mission began).

## 2. Exact root cause

`app/experiments/skill_ledger/common.py` (committed as part of the original VSL
implementation, before the integration-readiness pass) imports
`canon`/`sha256_obj`/`sha256_text` from `app.experiments.accumulation_probe.common` —
a package that was never committed to git by anyone, at any point, despite existing on
disk and being used throughout the entire multi-week VSL research and integration arc.
`app/core/skill_ledger/store.py` (written during the integration-readiness pass)
re-exported `sha256_text` from that same module rather than duplicating it, extending the
transitive dependency from the experimental package into the production core. Neither
choice was unreasonable in isolation; the combination created a real production
dependency on an uncommitted package. Full forensic account:
`audits/2026-09-28_vsl_clean_checkout_reproducibility_failure.md`.

## 3. Production dependency closure discovered

- **Strict minimum for the production import chain**: `accumulation_probe/common.py`
  alone (confirmed self-contained: `hashlib`/`json`/`os`/`pathlib` only).
- **Full scientific reference implementation** (`harness.py`, `prospective_transfer.py`,
  `accumulation.py`): additionally needs `accumulation_probe`'s `oracle_runner`/
  `ollama_client`/`worlds`/`tasks`/`tasks_v2`, and `persistent_routing.strategies.build_prompt`.
- Both packages, checked directly file-by-file, depend only on each other and stdlib —
  no further cascading dependency on any other uncommitted package.
- `accumulation_probe` is also a real dependency of at least 6 other currently-uncommitted
  experiment packages (`belief_revision_probe`, `g3_micro_probe`, `persistent_routing`,
  `strategy_characterization`, `rung1`, and others) — confirming it is a genuinely shared,
  foundational research utility, not a VSL-specific accident.

## 4. `accumulation_probe`: committed intact, not extracted

**Decision: commit the full 47-file package unmodified**, not a narrower extraction of
just the 3 needed symbols. Reasoning, weighed explicitly per the mission's Phase 2:
zero code changes to the already twice-adversarially-gated VSL production core (lower
risk than touching gated code for a marginal dependency-footprint reduction); correctly
and completely restores this project's own standing "the scientific reference
implementation must remain runnable" commitment, not just the narrower production claim;
avoids an arbitrary, misleading partial commit of an otherwise-cohesive package that six
other research threads also depend on; independently confirmed clean (zero secrets, zero
syntax errors).

## 5. Status of `persistent_routing`

Committed intact (15 files) for the same reasoning as above. Confirmed **not** part of
the strict production dependency closure (no file under `app/core/` imports anything from
it, directly or transitively) — it is needed only to import/run
`app/experiments/skill_ledger/harness.py`, an already-committed file this project has
explicitly committed to keeping runnable.

## 6. Repair commit hash

`e022b76` — adds exactly the 41 real source/doc files across both packages (the other 21
files in the real, on-disk directories are `__pycache__/*.pyc`, correctly excluded by
`.gitignore`, verified by diffing the real file list against what was staged). No code
was modified. No Skill A artifact was touched.

A second, separate commit, `593a717`, adds the Phase 5 permanent regression guard (item
10 below) — kept isolated from the dependency repair per the mission's explicit
instruction.

Both were fast-forwarded onto `main` and pushed to `origin/main`
(`607c6d0..593a717`), matching the same merge/push mechanism used for the original VSL
merge.

## 7. Clean-checkout verification results

Performed at three independent levels of rigor, each stronger than the last:

1. **Local `git worktree` of the exact pre-repair commit** (`607c6d0`): reproduced the
   exact original failure, full traceback captured (see item 2 above / the forensic
   note).
2. **Local `git worktree` of the repaired commit** (`e022b76`, then re-verified at
   `593a717`): confirmed clean (`git status --porcelain` empty in the worktree — no
   untracked files present). `app.core.skill_ledger` (all 5 submodules) and
   `app.core.echo_projects` both import cleanly. `app/experiments/skill_ledger/verify_diff_extract.py`
   → 15/15. The full scientific reference implementation
   (`harness.py`/`prospective_transfer.py`/`accumulation.py`) imports cleanly.
   Confirmed no path back to the real dev tree exists (`PYTHONPATH` empty, default
   `sys.path` contains only stdlib/site-packages — the clean-room tests could not have
   silently succeeded by reaching outside the checkout).
3. **A genuinely fresh `git clone` directly from `origin`** (the strongest possible
   check, bypassing even local git object reuse): `git clone --depth 1
   git@github.com:gremlinchode/FeralEcho-Backup.git`, confirmed `HEAD=593a717`, confirmed
   `git status --porcelain` empty, confirmed `app.core.echo_projects` imports cleanly,
   confirmed `verify_diff_extract.py` → 15/15.

**Explicit, precise finding, not glossed over**: `scripts/verify_skill_ledger_integration.py`'s
checks #3/#4 (real Skill A/B content-hash checks) correctly **fail** with
`FileNotFoundError` — not `ModuleNotFoundError` — from both the local worktree and the
fresh remote clone, because `memory/experiments/skill_ledger/skills/*.json` is
deliberately, correctly excluded by the blanket `memory/` gitignore rule (confirmed via
`git log --all`: these specific files were never tracked, ever, by design — the same
category as `river_brain.pkl` or the FAISS index). **This is not a regression and not
something this repair should "fix" by committing real skill data** — Skill A is local
learned state, not source code, and treating it as git-trackable would be a different,
separate architectural decision this report does not make unilaterally. The permanent
regression guard (item 10) was deliberately scoped to test only the code-reproducibility
question this distinction separates out cleanly.

## 8. VSL suite results from the clean checkout

- `app/experiments/skill_ledger/verify_diff_extract.py`: **15/15**, from all three
  verification levels above.
- `scripts/verify_skill_ledger_integration.py`: the new check #1 (clean-checkout
  reproducibility guard) passes; checks #3/#4 fail for the correct, expected reason
  above when run against a bare checkout with no local `memory/` state — this suite was
  always designed to run in a populated development environment (as it does in the real
  dev tree, where it passes **35/35**), not a bare clone with zero runtime state.

## 9. Skill A before/after identity evidence

Recorded at the start of this mission, before any repair work: `version=4`,
`effective_lifecycle=ACTIVE`, `content_hash=95de89e132a81e2fc856fee453393b680c832f5a4c951cebbd97288cd68e7627`,
plus file-level SHA-256 of all four real `memory/skill_ledger/skills/*.json` files.
Re-checked identically after both the repair commit and the guard commit, in the real
dev environment: **every value matches exactly, byte-for-byte** — Skill A was untouched
by this entire repair mission.

## 10. Permanent regression guard added

`scripts/verify_skill_ledger_integration.py` gained a new check, run first,
unconditionally: `_check_clean_checkout_reproducibility()`. It extracts **only** the
current `HEAD` commit's tracked files via `git archive HEAD` (never the working tree,
never untracked files) into a scratch directory, then attempts the real production
import chain (`app.core.echo_projects`, all 5 `app.core.skill_ledger` submodules) from a
genuinely separate subprocess with no inherited `PYTHONPATH` and a `cwd` confined to the
extraction. **Verified as a genuine negative control, not just re-run**: the identical
check logic, run against the pre-repair commit `607c6d0`, correctly **fails** with the
exact original `ModuleNotFoundError`; run against the repaired `HEAD`, it correctly
**passes**. This proves the guard discriminates a real reproducibility failure rather
than passing trivially — the same standard this project's other regression suites
(`verify_diff_extract.py`, `verify_liveness_ledger.py`) already hold themselves to.

This directly answers Phase 5's question ("can tooling detect imports satisfied only by
untracked files"): yes, and it now does, automatically, every time this suite runs.

## 11. Does the bounded VSL claim survive?

**Yes — but only after this repair, and the distinction matters.** Restated precisely,
per the mission's own required separation:

- **Local implementation worked** — true throughout, never in question.
- **Scientific evidence survived adversarial testing** — true throughout, confirmed
  independently twice, unaffected by this mission.
- **Repository was reproducible from committed state** — **false at the time of the
  `MERGE` verdict** (never tested), **true now**, independently confirmed via a fresh
  clone directly from `origin`, the strongest evidence this specific question admits.

The previous gate established the first two rigorously. It did not establish the third,
and stating that plainly — rather than assuming it followed from the first two — is the
entire point of this mission.

## 12. Proposed batching plan for remaining uncommitted research

**272 paths remain** (30 modified tracked files, ~240 untracked paths across ~14 distinct
research threads spanning 2026-09-07 through 2026-09-27), **not touched by this repair**,
per the mission's explicit scope boundary. Grouped below by actual research lineage
(filename/content/date correlation), not arbitrary file count. **Nothing in this section
has been committed — this is a proposal for your review and ordering, not an action
taken.**

| # | Batch | Date range | Representative contents | Code + evidence together? |
|---|---|---|---|---|
| 1 | **Provenance / observation-time / runtime-identity** | 09-07 → 09-20 | `app/core/provenance_check.py` (mod), `scripts/verify_provenance_check.py` (mod), ~25 audit docs (`authority_boundary_deliberateness` → `reconciliation_primitive_architecture`), `feralecho_runtime_identity_*`, `real_trace_f2_provenance/_scratch/` | Yes — code and its audit trail are the same thread |
| 2 | **Epistemic self-model / self-transparency arbitration** | 09-07 → 09-09 | ~35 audit docs (`echo_blind_self_model`, `epistemic_arbitration_*` ×6, `self_model_*` ×5, `self_transparency_audit_*`, `mechanism_c/d_*`), `echo_self_model_claims.json` | Docs only — no corresponding tracked code changes identified |
| 3 | **Task-type classifier causal audit** | 09-09, 09-14 → 09-17 | `app/experiments/task_type_ground_truth/`, `scripts/task_type_behavioral_experiment*.py` ×3, ~12 audit docs (`mission32`-`mission35`, `task_type_*`) | Yes |
| 4 | **Codex/OS-level autonomy investigation** | 09-09 | `codex_headless_subscription_independence_proof`, `openai_codex_local_agent_architecture_investigation`, `os_level_stdin_fd0_implementation`, `open_ended_learning_discovery`, `autonomous_investigation_liveness_recovery_forensics`, `autonomous_scheduler_restart_temporal_lifecycle_forensics` | Docs only |
| 5 | **E5-mini / capability-ceiling** | 09-16 → 09-17 | `app/experiments/e5_mini/`, `audits/python_learning_capability_gap/`, `audits/recursive_learning_ground_truth/`, `scripts/verify_qual_ident.py`, ~13 audit docs | Yes |
| 6 | **Persistent-competence / AP-0 / Rung1** | 09-19 → 09-23 | `app/experiments/rung1/`, `historical_difficulty_calibration/`, `minimal_procedure_transfer/`, `scripts/verify_rung1_e0_trusted_evaluator.py`, ~13 audit docs + 2 JSON evidence ledgers | Yes |
| 7 | **Backup/vault/Seagate infrastructure** | 09-20 → 09-21 | `feralecho_backup_manifest_schema.json`, `feralecho_cross_backup_relay_schema.json`, `feralecho_m5_intel_cross_backup_relay_plan`, `feralecho_verified_backup_and_recovery_plan`, `seagate_2tb_echo_vault_preflight`, `seagate_apfs_encrypted_format_preflight`, `seagate_post_f1_guard_diagnostic` | Docs only (ops/infra, not code) |
| 8 | **Claude/Codex reconciliation + research-direction strategy** | 09-22 | ~11 audit docs (`claude_codex_reconciliation_and_oct1_roadmap`, `codex_adversarial_attack_on_reconciled_roadmap`, `feralecho_research_direction_reassessment`, `vrm_retrospective_feasibility_investigation`, etc.) | Docs only |
| 9 | **Self-edit candidate logging / evidence preservation** | 09-22 → 09-23 | `app/core/self_edit_attempt_ledger.py` (mod), `self_edit_convergence.json` (mod), `self_edit_generated.py` (mod), `self_edit_manager.py` (mod), `staging/self_edit_candidate.py` (mod), `sandbox/scripts/temp_self_edit.py` (mod), `sandbox/safe_exec_wrapper.py` (mod), `app/experiments/validated_experience_competence_transfer/`, `scripts/verify_self_edit_candidate_preservation.py`, `verify_select_best_fallback_candidate.py`, ~10 audit docs | Yes — this is the largest code+evidence-paired batch |
| 10 | **Tier3/Tier5 reisolated reruns** | 09-09, 09-13 → 09-14 | `audits/tier3_apparatus/`, `audits/tier5_retest/`, `scripts/run_tier3_reisolated_rerun.py`, `run_tier5_retest.py`, `tier5_retest_task_pool.py`, `audits/2026-09-14_tier5_followup_experiment_design.md` (mod), `app/core/river_deliberation.py` (mod), `app/core/echo_model_orchestrator.py` (mod) — **note**: these two modified core files may also carry contributions from other batches, see caveat below | Yes |
| 11 | **VSL research not already committed** | 09-27 | `app/experiments/strategy_characterization/`, `restart_persistence_transfer/`, `g3_micro_probe/`, `belief_revision_probe/`, ~11 audit docs (`strategy_characterization_protocol_*` ×5, `ark_checkin_protocol_design`, `autonomous_acquisition_counterfactual_experience_protocol`, `diagnostic_correction_learning_feasibility`, `learning_investigation_synthesis`, `restart_persistence_of_acquired_competence`) | Yes — this is the direct scientific prehistory of the VSL work already merged |
| 12 | **Breakfast Club (autonomous GPT reachability)** | 09-24 | `app/experiments/breakfast_club_reachability/`, ~13 audit docs (`breakfast_club_*` ×6, `operation_breakfast_club_*` ×7), `feralecho_two_node_relay_stalemate_forensic`, `codex_validated_experience_transfer_self_falsification` | Yes |
| 13 | **Claude relay / hub / codex relay tooling** | ongoing | `claude_relay/relay.py` (mod), `README.md` (mod), `.last_seen_from_air.json` (mod), `from_m5.md` (mod, 1110 lines — large), `.last_seen_from_air_hub.json`, `facts_m5.jsonl`, `hub/`, `codex_relay/` | Yes, tooling + its own state |
| 14 | **Research strategy/brainstorm docs** | scattered | `research/OPEN_QUESTIONS.md` (mod), `CLOUD_CHAMBER_SEALED_GPT_BASELINE.*`, `COLLABORATOR_SUBSTITUTION_CODEX_PILOT`, `FRONTIER_COLLABORATOR_REGULATORY_DEPENDENCY`, `MACOS_AUTHORIZATION_EVIDENCE_ARCHEOLOGY`, `MEMORY_PRESERVATION_*` ×2, `OPOSSUM_MODE_BRAINSTORM`, `STRATEGIC_FRONTIER_RESILIENCE`, `TWO_NODE_IDENTITY_PRESERVATION_RELAY_ARCHAEOLOGY` | Docs only, overlaps thematically with batches 4/12 |

**Files whose provenance remains ambiguous, flagged rather than forced into a batch**:
`CLAUDE.md`, `PENDING_DECISIONS.md`, `app/core/echo_ground_truth.py`,
`app/core/echo_model_orchestrator.py`, `app/core/liveness_ledger.py` (275-line diff —
almost certainly contains additive checks from *several* of the batches above, since
every research thread in this project's history tends to add its own Liveness Ledger
check), `app/core/shadow_model.py`, `app/core/snapshot_manager.py`,
`app/core/temporal_environment.py`, `app/emergent_scheduler.py`,
`app/lib/vector_memory.py`, `app/maintenance/night_cycle.py`, `run.py`,
`scripts/verify_liveness_ledger.py`, `logs/janitor_report.json`. These are large,
cross-cutting files this whole project's own convention keeps editing across many
missions (per CLAUDE.md's own extensive Findings history) — splitting them cleanly by
hunk to match the batches above would require line-level archaeology beyond what this
report attempts unprompted. **Recommendation**: commit these together, last, as their own
explicitly-labeled "cumulative platform changes, spanning the above batches" commit,
rather than forcing an artificial per-batch split that risks being wrong.

**Recommended commit order**: 11 → 9 → 1 → 3 → 5 → 6 → 12 → 10 → 2 → 4 → 8 → 14 → 13 → 7,
then the ambiguous cross-cutting files last. Reasoning: batch 11 is the direct scientific
prehistory of the already-merged VSL work and is the most valuable to land immediately
after this repair; batch 9 (self-edit evidence preservation) and batch 1 (provenance) are
the next-most load-bearing infrastructure; documentation-only batches (2, 4, 8, 14) can
safely land whenever convenient since they carry no code risk; ops/infra (7) is lowest
urgency.

**Nothing above has been committed.** This is a proposal awaiting your review — I can
execute any subset of it, in any order, on your instruction.

## 13. What remains uncertain

- Exactly which hunks of `liveness_ledger.py`/`provenance_check.py`/other large modified
  files belong to which batch — not resolved here, flagged as needing either your
  judgment or a dedicated line-level archaeology pass if a clean split is wanted.
- Whether `data/`-style skill artifacts (Skill A/B's real `memory/skill_ledger/`
  content) should ever be treated as git-trackable reference data rather than pure local
  runtime state — explicitly not decided here; flagged as a separate architectural
  question, not defaulted into either direction.
- Whether the tooling-debris worktree (`.claude/worktrees/agent-abe6ecca0408fd0fb/`,
  confirmed once more this session to be 100% safe to discard — its sole commit `a23b940`
  remains fully contained in `main`'s current history) should be cleaned up now or left
  for a separate pass — **not touched in this mission**, per its own explicit "do not mix
  into the scientific repair commit" instruction. Recommended command, to run whenever
  convenient: `git worktree remove .claude/worktrees/agent-abe6ecca0408fd0fb --force`.
