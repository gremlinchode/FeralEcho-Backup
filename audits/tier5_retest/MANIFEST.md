# Tier-5 Retest — Reproducibility Manifest

Pointer index only. Does not duplicate raw evidence — every row below names the
authoritative artifact; read that artifact directly, not this summary, before
citing a number from it.

## Authoritative (clean) evidence

| Artifact | Path | Identity |
|---|---|---|
| Frozen task pool | `audits/tier5_retest/tier5_retest_task_pool_FROZEN.py` | SHA256 `595bb18abf1b8c6ca6c34e23687b909551c6dd610eb860961b3714b82bc7b8ac`, 20499 bytes. Live copy `scripts/tier5_retest_task_pool.py` re-verified byte-identical 2026-09-14. |
| Driver | `scripts/run_tier5_retest.py` | Paired treatment/control per task; treatment = real `river_deliberation.detect_full_agreement`/`find_missing_agreed_definitions`; control = same functions monkeypatched to permanent no-ops (reuses `scripts/verify_synthesis_refactor_control.py`'s pattern verbatim). No resume/skip logic — unconditional loop over all 20 tasks. |
| Raw results (clean) | `audits/tier5_retest/tier5_retest_results.jsonl` | 40 rows = 20 task_ids × 2 conditions, verified complete (2026-09-14: zero missing condition cells, max recorded `generation_time` 113.14s / min 24.13s — no sleep-artifact outliers). |
| Progress log (clean) | `audits/tier5_retest/tier5_retest_progress.txt` | Human-readable per-task pass/fail/gen_time, written as the run progressed. |
| Full stdout (clean) | `audits/tier5_retest/tier5_retest_stdout.log` | Source of the `[DELIBERATION]`/`[PROMPT GUARD]` log-line evidence cited in the retest report and adversarial audit. |
| Retest report | `audits/2026-09-13_tier5_council_correctness_retest.md` | Original analysis — self-reported headline numbers, since independently re-verified (see next row). |
| Adversarial audit | `audits/2026-09-14_tier5_retest_adversarial_audit.md` | **Authoritative validity assessment.** Independently re-verified every headline number by direct recomputation from `tier5_retest_results.jsonl`; found the aggregate statistic mathematically incapable of reaching p<.05 at 5 discordant pairs; found 2 additional mechanistic hits (3/20, not 1/20) via direct log inspection. Treat this report's conclusions as superseding the retest report's own interpretation wherever they differ. |

## Excluded (contaminated) evidence — preserved, not deleted, never pooled

| Artifact | Path | Why excluded |
|---|---|---|
| Contaminated results | `audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_results.jsonl` | Task `r-rf03` recorded generation_time=18024.08s (treatment) / 16439.91s (control) — a lid-close sleep spanning the measurement window. Task `r-dt04` (20th/20) has zero recorded result; the process was killed by a stream watchdog after 600s of silence. |
| Contaminated progress log | `audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_progress.txt` | Same run. |
| Contaminated stdout | `audits/tier5_retest/archive/SLEEP_INTERRUPTED_20260913_stdout.log` | Same run. |

Verified 2026-09-14: `scripts/run_tier5_retest.py` contains zero references to `archive`/`SLEEP_INTERRUPTED` — the clean driver has no code path that can read the contaminated files. The two result sets live in physically separate directories (`audits/tier5_retest/` vs `audits/tier5_retest/archive/`) with non-overlapping filenames.

## Prior comparison point (separate experiment, not part of this retest's evidence)

`audits/tier4_confirmatory_report.md` — n=84, `BASE_N` ≈79.8% vs `ARCH_COUNCIL` ≈67.9%, did not clear its own pre-registered significance bar (p=0.087 vs ≤0.048); 7 cases where every candidate was independently verified correct and synthesis still produced a wrong answer.

## Research ledger

`research/FINDINGS.md` R-011, `research/OPEN_QUESTIONS.md` Q-010 — the durable, cross-referenced record of this retest's conclusion and the precisely-scoped open question it leaves.

## Follow-up design (not executed)

`audits/2026-09-14_tier5_followup_experiment_design.md`
